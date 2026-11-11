"""Exercise the real Bash player with mocked mpv/services and a fake DRM tree."""

import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".local/bin/touchbar"
MOCK = r'''
import json
import os
from pathlib import Path
import sys
import time

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["MOCK_CALLS"], "a") as log:
    log.write(json.dumps([name, *args]) + "\n")
if name == "sudo":
    assert args[0] == "-n"
    os.execv(args[1], args[1:])
if name == "systemctl":
    sys.exit(0)
if "--version" in args:
    code = int(os.environ.get("MOCK_VERSION_EXIT", "0"))
    if code:
        print("libavcodec.so.62: cannot open shared object file", file=sys.stderr)
    sys.exit(code)
Path(os.environ["MOCK_PLAYER_PID"]).write_text(str(os.getpid()))
time.sleep(float(os.environ.get("MOCK_PLAYER_SECONDS", "0.25")))
sys.exit(int(os.environ.get("MOCK_PLAYER_EXIT", "0")))
'''


class TouchbarTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="touchbar-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.home = self.root / "home"
        self.assets = self.home / ".local/share/touchbar-animations"
        self.assets.mkdir(parents=True)
        self.log = self.root / "calls.jsonl"
        self.log.touch()
        self.pid = self.root / "player.pid"
        self.started = self.root / "started"
        self.sysfs = self.root / "sysfs"
        self.devices = self.root / "dri"
        self.devices.mkdir()
        self.panel("card0-DSI-1", "connected", "1920x1200")
        self.panel("card1-DSI-1", "disconnected", "60x2008")
        self.panel("card7-DSI-2", "connected", "60x2008")
        self.device = self.devices / "card7"
        self.device.touch()
        self.mpv = self.repo / ".build/touchbar-mpv/mpv"
        self.mock(self.mpv)
        # Preserve production's absolute privileged-command paths. Only this
        # sandbox copy substitutes them; no live sudo/systemctl is ever invoked.
        script = SCRIPT.read_text()
        for name in ("sudo", "systemctl"):
            mock = self.root / "bin" / name
            self.mock(mock)
            script = script.replace(f"/usr/bin/{name}", shlex.quote(str(mock)))
        helper = self.repo / ".local/bin/touchbar"
        helper.parent.mkdir(parents=True)
        helper.write_text(script)
        helper.chmod(0o755)
        self.command = self.home / ".local/bin/touchbar"
        self.command.parent.mkdir(parents=True)
        self.command.symlink_to(helper)
        self.asset = self.assets / "stickman.mkv"
        self.asset.touch()
        self.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith("TOUCHBAR_")
        }
        self.env.update({
            "HOME": str(self.home),
            "TOUCHBAR_DRM_SYSFS_ROOT": str(self.sysfs),
            "TOUCHBAR_DRM_DEVICE_ROOT": str(self.devices),
            "TOUCHBAR_STARTED_FILE": str(self.started),
            "MOCK_CALLS": str(self.log),
            "MOCK_PLAYER_PID": str(self.pid),
        })

    def mock(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"#!{sys.executable}\n{MOCK}")
        path.chmod(0o755)

    def panel(self, name, status, mode):
        path = self.sysfs / name
        path.mkdir(parents=True)
        (path / "status").write_text(status + "\n")
        (path / "modes").write_text(mode + "\n")

    def calls(self, name=None):
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return calls if name is None else [call[1:] for call in calls if call[0] == name]

    def run_player(self, *args):
        return subprocess.run(
            [str(self.command), "play", *args], env=self.env, cwd=self.root,
            text=True, capture_output=True, timeout=5,
        )

    def assert_no_handoff(self):
        self.assertEqual(self.calls("sudo"), [])
        self.assertEqual(self.calls("systemctl"), [])
        self.assertFalse(self.started.exists())

    def test_symlink_selects_rebuilt_player_and_discovers_panel(self):
        result = self.run_player("stickman")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls("mpv"), [
            ["--no-config", "--version"],
            ["--no-config", "--vo=drm", f"--drm-device={self.device}",
             "--drm-connector=DSI-2", "--video-rotate=90", "--loop-file=no",
             "--input-terminal=no", "--really-quiet", "--no-audio", "--", str(self.asset)],
        ])
        self.assertEqual(self.calls("systemctl"), [["stop", "tiny-dfr"], ["start", "tiny-dfr"]])
        self.assertTrue(self.started.exists())

    def test_legacy_patched_player_remains_available(self):
        self.mpv.unlink()
        self.mock(self.home / ".local/src/mpv-touchbar/build/mpv")
        result = self.run_player("stickman")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls("mpv")), 2)

    def test_literal_paths_and_explicit_player_override(self):
        alternate = self.root / "patched mpv's build"
        self.mock(alternate)
        self.env["TOUCHBAR_MPV_BIN"] = str(alternate)
        asset = self.root / "clip 'quoted' $(touch PWNED); 雪\n.mkv"
        asset.touch()
        result = self.run_player(str(asset), "--audio", "--loop", "--rotate", "270")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = self.calls(alternate.name)[1]
        self.assertEqual(args[-2:], ["--", str(asset)])
        self.assertIn("--loop-file=inf", args)
        self.assertIn("--video-rotate=270", args)
        self.assertNotIn("--no-audio", args)
        self.assertFalse((self.root / "PWNED").exists())

    def test_missing_ffmpeg_library_fails_before_service_changes(self):
        self.env["MOCK_VERSION_EXIT"] = "127"
        (self.assets / "linux-showcase.mkv").touch()
        result = self.run_player("linux-showcase", "--loop")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("libavcodec.so.62", result.stderr)
        self.assertIn("build-touchbar-mpv.sh", result.stderr)
        self.assert_no_handoff()

    def test_missing_executable_fails_before_service_changes(self):
        self.env["TOUCHBAR_MPV_BIN"] = str(self.root / "missing-mpv")
        result = self.run_player("stickman")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("build-touchbar-mpv.sh", result.stderr)
        self.assert_no_handoff()

    def test_missing_panel_fails_before_service_changes(self):
        (self.sysfs / "card7-DSI-2/status").write_text("disconnected\n")
        result = self.run_player("stickman")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no connected", result.stderr)
        self.assert_no_handoff()

    def test_inaccessible_device_fails_before_service_changes(self):
        self.device.chmod(0)
        result = self.run_player("stickman")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot access", result.stderr)
        self.assert_no_handoff()

    def test_invalid_rotation_fails_before_preflight(self):
        for args in (("--rotate",), ("--rotate", "90; touch PWNED")):
            with self.subTest(args=args):
                result = self.run_player("stickman", *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("--rotate requires", result.stderr)
                self.assertEqual(self.calls(), [])

    def test_missing_registered_asset_fails_before_preflight(self):
        self.asset.unlink()
        result = self.run_player("stickman")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no such file", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_player_failure_restores_normal_controls(self):
        self.env["MOCK_PLAYER_EXIT"] = "9"
        result = self.run_player("stickman")
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertEqual(self.calls("systemctl"), [["stop", "tiny-dfr"], ["start", "tiny-dfr"]])

    def test_termination_reaps_player_and_restores_both_services(self):
        self.check_signal_cleanup(signal.SIGTERM, 143)

    def test_interrupt_reaps_player_and_restores_both_services(self):
        self.check_signal_cleanup(signal.SIGINT, 130)

    def check_signal_cleanup(self, signum, expected_status):
        (self.assets / "linux-showcase.mkv").touch()
        self.env["MOCK_PLAYER_SECONDS"] = "30"
        process = subprocess.Popen(
            [str(self.command), "play", "linux-showcase", "--loop"],
            env=self.env, cwd=self.root, start_new_session=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

        def cleanup():
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=3)
        self.addCleanup(cleanup)
        deadline = time.monotonic() + 3
        while not self.started.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(self.started.exists())
        player_pid = int(self.pid.read_text())
        process.send_signal(signum)
        _, stderr = process.communicate(timeout=3)
        self.assertEqual(process.returncode, expected_status, stderr)
        with self.assertRaises(ProcessLookupError):
            os.kill(player_pid, 0)
        self.assertEqual(self.calls("systemctl"), [
            ["--user", "is-active", "--quiet", "codex-touchbar.service"],
            ["--user", "stop", "codex-touchbar.service"],
            ["stop", "tiny-dfr"], ["start", "tiny-dfr"],
            ["--user", "start", "codex-touchbar.service"],
        ])


if __name__ == "__main__":
    unittest.main()
