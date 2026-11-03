"""Exercise wallpaper selection and rotation without a display or user systemd."""

import configparser
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / ".local/bin/random-wallpaper"
LAUNCHER = ROOT / ".local/bin/random-wallpaper.sh"
REMOVED_HELPERS = (
    ".config/waypaper/config.ini",
    ".local/bin/waypaper-set-backend.sh",
    ".local/bin/waybar-wallpaper-backend.sh",
    ".local/bin/waybar-wallpaper-backend-cycle.sh",
    ".local/bin/wallpaper-auto-downscale",
)

MOCK = r'''
import json
import os
from pathlib import Path
import sys
import time

name = Path(sys.argv[0]).name
with open(os.environ["MOCK_CALLS"], "a") as log:
    log.write(json.dumps([name, *sys.argv[1:]]) + "\n")
if name == "systemctl":
    release = os.environ.get("MOCK_SYSTEMCTL_RELEASE_FILE")
    if release:
        deadline = time.monotonic() + 4
        while not Path(release).exists():
            if time.monotonic() >= deadline:
                print("mock systemctl timed out waiting for release", file=sys.stderr)
                sys.exit(98)
            time.sleep(0.01)
    if os.environ.get("MOCK_SYSTEMCTL_ERROR"):
        print(os.environ["MOCK_SYSTEMCTL_ERROR"], file=sys.stderr)
    sys.exit(int(os.environ.get("MOCK_SYSTEMCTL_EXIT", "0")))
if name == "swaybg":
    Path(os.environ["MOCK_PID_FILE"]).write_text(str(os.getpid()))
    sys.exit(int(os.environ.get("MOCK_SWAYBG_EXIT", "0")))
print("unexpected wallpaper helper: " + name, file=sys.stderr)
sys.exit(99)
'''


class RandomWallpaperTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="random-wallpaper-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.home = self.directory / "home"
        self.runtime = self.directory / "runtime"
        self.cache = self.directory / "cache"
        self.wallpapers = self.home / "Pictures/Wallpapers"
        self.log = self.directory / "calls.jsonl"
        self.pid_file = self.directory / "swaybg.pid"
        self.log.write_text("")
        self.home.mkdir()
        self.runtime.mkdir()
        bin_dir = self.directory / "bin"
        bin_dir.mkdir()
        # Also intercept obsolete helpers, so a regression cannot touch live
        # wallpaper processes through PATH while these tests are running.
        for name in ("systemctl", "swaybg", "waypaper", "mpvpaper", "pkill", "killall"):
            path = bin_dir / name
            path.write_text(f"#!{sys.executable}\n{MOCK}")
            path.chmod(0o755)
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "XDG_RUNTIME_DIR": str(self.runtime),
            "XDG_CACHE_HOME": str(self.cache),
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "MOCK_CALLS": str(self.log),
            "MOCK_PID_FILE": str(self.pid_file),
        }

    def image(self, name, root=None):
        path = (root if root is not None else self.wallpapers) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image contents are not decoded by the mock swaybg\n")
        return path

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def run_script(self, script, env=None):
        return subprocess.run(
            [str(script)],
            env=self.env if env is None else env,
            text=True,
            capture_output=True,
            timeout=5,
        )

    def assert_pick(self, result, path):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [["swaybg", "-i", str(path), "-m", "fill"]])
        self.assertEqual(result.stdout, "")

    def test_supported_image_formats_case_insensitively(self):
        for extension in ("jpg", "jpeg", "png", "webp", "bmp", "gif", "tif", "tiff"):
            for spelling in (extension, extension.upper()):
                with self.subTest(extension=spelling):
                    path = self.image(f"nested library/image.{spelling}")
                    self.log.write_text("")
                    self.assert_pick(self.run_script(LAUNCHER), path)
                    path.unlink()

    def test_recurses_and_ignores_non_images_and_directories(self):
        for name in ("video.mp4", "video.mkv", "video.webm", "video.mov", "notes.txt",
                     "vector.svg", "book.pdf", "README", "image.png.tmp", "photo.jpg.mp4"):
            self.image(name)
        (self.wallpapers / "not-a-file.PNG").mkdir()
        path = self.image("collection/deeper/pick.WeBp")
        self.assert_pick(self.run_script(LAUNCHER), path)

    def test_preserves_whitespace_unicode_and_newlines(self):
        path = self.image("collection with spaces\nand tabs\t/雪 'quoted'\nimage.PNG")
        self.assert_pick(self.run_script(LAUNCHER), path)
        self.assertEqual(
            (self.runtime / "swaybg-wallpaper.current").read_bytes(),
            os.fsencode(path) + b"\0",
        )

    def test_symlinked_wallpaper_root(self):
        target = self.directory / "external collection"
        selected = self.image("nested/image.jpeg", root=target)
        self.wallpapers.parent.mkdir(parents=True)
        self.wallpapers.symlink_to(target, target_is_directory=True)
        self.assert_pick(self.run_script(LAUNCHER), self.wallpapers / selected.relative_to(target))

    def test_two_images_never_immediately_repeat(self):
        images = {
            str(self.image("first image\n.PNG")),
            str(self.image("nested/second\nimage.jpg")),
        }
        previous = None
        for _ in range(6):
            self.log.write_text("")
            result = self.run_script(LAUNCHER)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = self.calls()
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0:2], ["swaybg", "-i"])
            self.assertEqual(calls[0][3:], ["-m", "fill"])
            selected = calls[0][2]
            self.assertIn(selected, images)
            self.assertNotEqual(selected, previous)
            self.assertEqual(
                (self.runtime / "swaybg-wallpaper.current").read_bytes(),
                os.fsencode(selected) + b"\0",
            )
            previous = selected

    def test_single_image_can_be_selected_repeatedly(self):
        path = self.image("only image.png")
        for _ in range(3):
            self.log.write_text("")
            self.assert_pick(self.run_script(LAUNCHER), path)

    def test_stale_current_image_does_not_exclude_the_library(self):
        (self.runtime / "swaybg-wallpaper.current").write_bytes(b"/removed/image.png\0")
        path = self.image("available image.gif")
        self.assert_pick(self.run_script(LAUNCHER), path)

    def test_missing_directory_fails_clearly_without_launching(self):
        result = self.run_script(LAUNCHER)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr.lower(), r"wallpaper|director")
        self.assertEqual(self.calls(), [])

    def test_empty_or_non_image_library_fails_without_launching(self):
        self.wallpapers.mkdir(parents=True)
        for non_image in (None, "video.mp4"):
            with self.subTest(non_image=non_image):
                if non_image:
                    self.image(non_image)
                result = self.run_script(LAUNCHER)
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(result.stderr.lower(), r"no.*(image|wallpaper)|(image|wallpaper).*empty")
                self.assertEqual(self.calls(), [])

    def test_launcher_execs_swaybg_as_the_foreground_process(self):
        path = self.image("foreground.png")
        with subprocess.Popen(
            [str(LAUNCHER)], env=self.env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ) as child:
            output, error = child.communicate(timeout=5)
            self.assertEqual(child.returncode, 0, error)
            self.assertEqual(output, "")
            self.assertEqual(int(self.pid_file.read_text()), child.pid)
        self.assertEqual(self.calls(), [["swaybg", "-i", str(path), "-m", "fill"]])

    def test_launcher_propagates_swaybg_exit_status(self):
        self.image("image.png")
        result = self.run_script(LAUNCHER, {**self.env, "MOCK_SWAYBG_EXIT": "23"})
        self.assertEqual(result.returncode, 23)
        self.assertEqual(len(self.calls()), 1)

    def test_launcher_uses_cache_fallback_without_runtime_directory(self):
        path = self.image("cached image.png")
        for use_xdg_cache in (True, False):
            with self.subTest(use_xdg_cache=use_xdg_cache):
                env = dict(self.env)
                env.pop("XDG_RUNTIME_DIR")
                if not use_xdg_cache:
                    env.pop("XDG_CACHE_HOME")
                cache = self.cache if use_xdg_cache else self.home / ".cache"
                self.log.write_text("")
                self.assert_pick(self.run_script(LAUNCHER, env), path)
                current_files = list(cache.rglob("swaybg-wallpaper.current"))
                self.assertEqual(len(current_files), 1)
                self.assertEqual(current_files[0].read_bytes(), os.fsencode(path) + b"\0")

    def test_wrapper_restarts_only_the_supervised_wallpaper_service(self):
        result = self.run_script(WRAPPER)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls(), [["systemctl", "--user", "restart", "swaybg-wallpaper.service"]]
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_wrapper_coalesces_requests_until_cooldown_expires(self):
        for _ in range(3):
            result = self.run_script(WRAPPER)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        time.sleep(1.6)
        result = self.run_script(WRAPPER)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 2)

    def test_overlapping_wrapper_requests_coalesce(self):
        release = self.directory / "release-systemctl"
        env = {**self.env, "MOCK_SYSTEMCTL_RELEASE_FILE": str(release)}
        children = []
        try:
            children.append(subprocess.Popen(
                [str(WRAPPER)], env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ))
            deadline = time.monotonic() + 3
            while not self.calls() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(len(self.calls()), 1, "first request never reached systemctl")
            for _ in range(5):
                children.append(subprocess.Popen(
                    [str(WRAPPER)], env=env, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                ))
            release.touch()
            for child in children:
                _, error = child.communicate(timeout=5)
                self.assertEqual(child.returncode, 0, error)
            self.assertEqual(len(self.calls()), 1)
        finally:
            release.touch()
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.communicate()

    def test_failed_restart_propagates_error_and_does_not_start_cooldown(self):
        result = self.run_script(WRAPPER, {
            **self.env, "MOCK_SYSTEMCTL_EXIT": "19", "MOCK_SYSTEMCTL_ERROR": "restart failed",
        })
        self.assertEqual(result.returncode, 19)
        self.assertIn("restart failed", result.stderr)
        retry = self.run_script(WRAPPER)
        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual(len(self.calls()), 2)
        suppressed = self.run_script(WRAPPER)
        self.assertEqual(suppressed.returncode, 0, suppressed.stderr)
        self.assertEqual(len(self.calls()), 2)

    def test_wrapper_uses_cache_fallback_without_runtime_directory(self):
        for use_xdg_cache in (True, False):
            with self.subTest(use_xdg_cache=use_xdg_cache):
                env = dict(self.env)
                env.pop("XDG_RUNTIME_DIR")
                if not use_xdg_cache:
                    env.pop("XDG_CACHE_HOME")
                self.log.write_text("")
                for _ in range(2):
                    result = self.run_script(WRAPPER, env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    self.calls(), [["systemctl", "--user", "restart", "swaybg-wallpaper.service"]]
                )
                cache = self.cache if use_xdg_cache else self.home / ".cache"
                self.assertTrue(cache.is_dir())


class WallpaperWiringTest(unittest.TestCase):
    def unit(self, name):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ROOT / ".config/systemd/user" / name)
        return parser

    def test_rotation_oneshot_delegates_to_wrapper_with_default_kill_mode(self):
        service = self.unit("random-wallpaper.service")["Service"]
        self.assertEqual(service["Type"], "oneshot")
        self.assertEqual(shlex.split(service["ExecStart"]), ["%h/.local/bin/random-wallpaper"])
        self.assertEqual(service.get("KillMode", "control-group"), "control-group")

    def test_foreground_wallpaper_service_is_supervised_with_session(self):
        unit = self.unit("swaybg-wallpaper.service")
        self.assertIn("graphical-session.target", unit["Unit"]["PartOf"].split())
        self.assertEqual(unit["Service"]["Restart"], "always")
        self.assertEqual(
            shlex.split(unit["Service"]["ExecStart"]), ["%h/.local/bin/random-wallpaper.sh"]
        )

    def test_startup_starts_swaybg_service_without_obsolete_helpers(self):
        startup = (ROOT / ".config/hypr/autostart.lua").read_text()
        self.assertIn("systemctl --user start swaybg-wallpaper.service", startup)
        for obsolete in ("waypaper", "mpvpaper", "wallpaper-auto-downscale"):
            self.assertNotIn(obsolete, startup)

    def test_setup_tracks_both_entry_points_and_removes_old_helpers(self):
        manifest = {
            line.strip()
            for line in (ROOT / "setup/home-files.txt").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for entry in (".local/bin/random-wallpaper", ".local/bin/random-wallpaper.sh"):
            self.assertIn(entry, manifest)
        for obsolete in REMOVED_HELPERS:
            self.assertNotIn(obsolete, manifest)
            self.assertFalse((ROOT / obsolete).exists(), obsolete)
            self.assertFalse((ROOT / obsolete).is_symlink(), obsolete)


if __name__ == "__main__":
    unittest.main()
