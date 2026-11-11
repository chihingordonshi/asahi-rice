"""Keep the historical curve disabled; validate its data without input-device access."""

import ctypes
import ctypes.util
import math
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / ".config/hypr/mouse-acceleration.lua"
INPUT = ROOT / ".config/hypr/input.lua"

CAPTURE = r'''
local devices = {}
hl = {
    device = function(config) devices[#devices + 1] = config end,
    config = function() error("mouse module must not change global input") end,
}
dofile(arg[1])
assert(#devices == 1, "expected exactly one device override")
local device = devices[1]
local count = 0
for key in pairs(device) do
    assert(key == "name" or key == "accel_profile", "unexpected device setting")
    count = count + 1
end
assert(count == 2)
print(device.name)
print(device.accel_profile)
'''

INTEGRATION = r'''
package.path = arg[2] .. "/?.lua;" .. package.path
hl = {
    config = function() end,
    device = function() end,
    gesture = function() end,
    on = function() end,
    get_active_window = function() return nil end,
}
dofile(arg[1])
assert(package.loaded["mouse-acceleration"] == nil,
    "the historical curve must not load by default")
'''


class MouseAccelerationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lua = shutil.which("lua")
        if cls.lua is None:
            raise unittest.SkipTest("Lua is not installed")
        result = cls.run_lua(CAPTURE, MODULE)
        cls.device, profile = result.stdout.strip().splitlines()
        kind, step, *points = profile.split()
        if kind != "custom":
            raise AssertionError(profile)
        cls.step = float(step)
        cls.points = [float(point) for point in points]

    @staticmethod
    def run_lua(script, path, executable=None):
        result = subprocess.run(
            [executable or shutil.which("lua"), "-", str(path), str(MODULE.parent)],
            input=script, text=True, capture_output=True, timeout=5,
        )
        if result.returncode:
            raise AssertionError(result.stderr or result.stdout)
        return result

    def test_historical_experiment_only_targets_the_external_mouse(self):
        self.assertEqual(self.device, "usb-gaming-mouse-1")

    def test_historical_experiment_is_not_loaded_by_default(self):
        self.run_lua(INTEGRATION, INPUT)

    def test_deployment_manifest_includes_the_required_module(self):
        manifest = (ROOT / "setup/home-files.txt").read_text().splitlines()
        self.assertIn(".config/hypr/mouse-acceleration.lua", manifest)

    def test_samples_are_valid_output_speeds(self):
        self.assertAlmostEqual(self.step, (127 / 62) * 1000 / 400 / 8, places=9)
        self.assertEqual(len(self.points), 64)  # 63 resampled positions + tail
        self.assertEqual(self.points[0], 0)
        self.assertTrue(all(math.isfinite(p) and p >= 0 for p in self.points))
        self.assertTrue(all(a < b for a, b in zip(self.points, self.points[1:])))

    def test_reference_samples_use_physical_velocity_conversion(self):
        source_ppi = 1728 * 25.4 / 344.245
        target_ppi = (2560 / 1.6) * 25.4 / 286
        output_scale = target_ppi / source_ppi / 8
        # Independent source anchors bracketing selected resampling positions.
        reference = {1: (2, 0.464648, 0.885612),
                     2: (4, 1.65208, 2.41855),
                     15: (30, 26.1395, 27.9305),
                     31: (63, 83.7539, 85.5117),
                     62: (127, 139.898, 139.898)}
        for index, (lower, left, right) in reference.items():
            with self.subTest(index=index):
                source_index = index * 127 / 62
                pixels = left + (right - left) * (source_index - lower)
                self.assertAlmostEqual(self.points[index], pixels * output_scale,
                                       delta=5.1e-10)
                self.assertAlmostEqual(index * self.step,
                                       source_index * 1000 / 400 / 8, places=7)

    def test_gain_matches_the_measured_shape_not_an_unbounded_polynomial(self):
        gains = [output / (index * self.step)
                 for index, output in enumerate(self.points) if index]
        self.assertTrue(0.10 < gains[0] < 0.11)
        self.assertTrue(0.61 < max(gains) < 0.62)
        self.assertAlmostEqual(gains[-1], 0.491072516, places=8)
        # The source has declining gain at high speeds; do not "fix" that away.
        self.assertLess(gains[-1], max(gains))

    def test_resampling_error_at_the_low_speed_corner_is_explicit(self):
        output_scale = ((2560 / 1.6) / 286) / (1728 / 344.245) / 8
        position = 3 * 62 / 127
        lower = math.floor(position)
        output = self.points[lower] + (self.points[lower + 1] - self.points[lower]) \
            * (position - lower)
        relative_error = output / (0.885612 * output_scale) - 1
        self.assertAlmostEqual(relative_error, 0.198781, places=6)

    def test_extrapolation_has_constant_final_gain(self):
        slope = (self.points[-1] - self.points[-2]) / self.step
        last_speed = (len(self.points) - 1) * self.step
        last_gain = self.points[-1] / last_speed
        self.assertAlmostEqual(slope, last_gain, places=8)
        for speed in (last_speed * 2, last_speed * 100):
            output = self.points[-1] + (speed - last_speed) * slope
            self.assertAlmostEqual(output / speed, last_gain, places=8)

    def test_luajit_produces_the_same_profile(self):
        luajit = shutil.which("luajit")
        if luajit is None:
            self.skipTest("LuaJIT is not installed")
        self.assertEqual(self.run_lua(CAPTURE, MODULE, luajit).stdout,
                         self.run_lua(CAPTURE, MODULE).stdout)

    def test_installed_libinput_accepts_the_motion_curve_without_device_access(self):
        library = ctypes.util.find_library("input")
        if library is None:
            self.skipTest("libinput is not installed")
        libinput = ctypes.CDLL(library)
        if not hasattr(libinput, "libinput_config_accel_create"):
            self.skipTest("libinput predates custom profiles (1.23)")
        libinput.libinput_config_accel_create.argtypes = [ctypes.c_int]
        libinput.libinput_config_accel_create.restype = ctypes.c_void_p
        libinput.libinput_config_accel_set_points.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_double, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
        ]
        libinput.libinput_config_accel_set_points.restype = ctypes.c_int
        libinput.libinput_config_accel_destroy.argtypes = [ctypes.c_void_p]
        libinput.libinput_config_accel_destroy.restype = None

        config = libinput.libinput_config_accel_create(1 << 2)  # CUSTOM
        self.assertTrue(config)
        try:
            points = (ctypes.c_double * len(self.points))(*self.points)
            status = libinput.libinput_config_accel_set_points(
                config, 1, self.step, len(points), points,  # MOTION
            )
            self.assertEqual(status, 0)  # LIBINPUT_CONFIG_STATUS_SUCCESS
        finally:
            libinput.libinput_config_accel_destroy(config)


if __name__ == "__main__":
    unittest.main()
