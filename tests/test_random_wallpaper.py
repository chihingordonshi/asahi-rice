"""Exercise native wallpaper IPC without changing the desktop or starting renderers."""

import configparser
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".local/bin/random-wallpaper"
COMPAT = ROOT / ".local/bin/random-wallpaper.sh"
LEGACY_DEPLOYMENTS = (
    ".config/hypr/scripts/waybar-autohide",
    ".config/hypr/waybar.lua",
    ".config/pavucontrol.ini",
    ".config/systemd/user/random-wallpaper.timer",
    ".config/systemd/user/swaybg-wallpaper.service",
    ".config/systemd/user/timers.target.wants/random-wallpaper.timer",
    ".config/systemd/user/waybar.service.d/restart.conf",
    ".config/waybar/config.jsonc",
    ".config/waybar/style.css",
    ".local/bin/waybar-bluetooth.sh",
    ".local/bin/waybar-cpu.sh",
    ".local/bin/waybar-fcitx5.sh",
    ".local/bin/waybar-memory.sh",
    ".local/bin/waybar-kitty-art.sh",
    ".local/bin/waybar-power-profile-cycle.sh",
    ".local/bin/waybar-power-profile.sh",
)

MOCK = r'''
import json
import os
from pathlib import Path
import sys

name = Path(sys.argv[0]).name
with open(os.environ["MOCK_CALLS"], "a") as log:
    log.write(json.dumps([name, *sys.argv[1:]]) + "\n")
if name != "noctalia":
    print("unexpected legacy wallpaper helper: " + name, file=sys.stderr)
    sys.exit(99)
print(os.environ.get("MOCK_STDOUT", ""), end="")
print(os.environ.get("MOCK_STDERR", ""), end="", file=sys.stderr)
sys.exit(int(os.environ.get("MOCK_EXIT", "0")))
'''


class RandomWallpaperTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="random-wallpaper-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.home = self.directory / "home"
        self.log = self.directory / "calls.jsonl"
        self.log.write_text("")
        self.home.mkdir()
        bin_dir = self.home / ".local/bin"
        bin_dir.mkdir(parents=True)
        # Intercept Noctalia too: tests must never send IPC to the live shell.
        for name in ("noctalia", "systemctl", "swaybg", "waypaper", "mpvpaper", "pkill", "killall"):
            path = bin_dir / name
            path.write_text(f"#!{sys.executable}\n{MOCK}")
            path.chmod(0o755)
        (bin_dir / "random-wallpaper").symlink_to(HELPER)
        (bin_dir / "random-wallpaper.sh").symlink_to(COMPAT)
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "MOCK_CALLS": str(self.log),
        }

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def run_helper(self, script, *args, **overrides):
        return subprocess.run(
            [str(script), *args], env={**self.env, **overrides},
            text=True, capture_output=True, timeout=5,
        )

    def test_both_entry_points_delegate_only_to_native_random_selection(self):
        for entry in (HELPER, COMPAT, self.home / ".local/bin/random-wallpaper.sh"):
            with self.subTest(entry=entry):
                self.log.write_text("")
                result = self.run_helper(entry)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls(), [["noctalia", "msg", "wallpaper-random"]])
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test_optional_connector_is_forwarded_without_shell_expansion(self):
        for entry in (HELPER, COMPAT):
            with self.subTest(entry=entry):
                connector = "output with spaces;'$HOME\n雪"
                self.log.write_text("")
                result = self.run_helper(entry, connector)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls(), [["noctalia", "msg", "wallpaper-random", connector]])

    def test_native_failure_and_output_are_preserved(self):
        for entry in (HELPER, COMPAT):
            with self.subTest(entry=entry):
                self.log.write_text("")
                result = self.run_helper(
                    entry, MOCK_EXIT="23", MOCK_STDERR="Noctalia unavailable\n",
                    MOCK_STDOUT="native response\n",
                )
                self.assertEqual(result.returncode, 23)
                self.assertEqual(result.stderr, "Noctalia unavailable\n")
                self.assertEqual(result.stdout, "native response\n")
                self.assertEqual(len(self.calls()), 1)

    def test_repeated_requests_do_not_start_a_service_or_local_cooldown(self):
        for _ in range(3):
            result = self.run_helper(HELPER)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [["noctalia", "msg", "wallpaper-random"]] * 3)

    @unittest.skipUnless(shutil.which("zsh"), "zsh is required for the shell helper test")
    def test_zsh_wallpaper_function_uses_the_same_native_helper(self):
        result = subprocess.run(
            ["zsh", "-f", "-c", 'source "$1"; wallpaper "$2"', "wallpaper-test",
             str(ROOT / ".zsh_functions"), "eDP-1"],
            env=self.env, text=True, capture_output=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [["noctalia", "msg", "wallpaper-random", "eDP-1"]])


class WallpaperWiringTest(unittest.TestCase):
    def test_manual_oneshot_uses_native_helper(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ROOT / ".config/systemd/user/random-wallpaper.service")
        service = parser["Service"]
        self.assertEqual(service["Type"], "oneshot")
        self.assertEqual(shlex.split(service["ExecStart"]), ["%h/.local/bin/random-wallpaper"])

    def test_startup_and_manifests_do_not_restore_legacy_owners(self):
        startup = (ROOT / ".config/hypr/autostart.lua").read_text()
        services = (ROOT / "setup/user-services.txt").read_text().splitlines()
        files = (ROOT / "setup/home-files.txt").read_text().splitlines()
        for disabled in ("swaybg-wallpaper.service", "random-wallpaper.timer", "waybar.service"):
            self.assertNotIn(disabled, startup)
            self.assertNotIn(disabled, services)
        for entry in LEGACY_DEPLOYMENTS:
            self.assertNotIn(entry, files, entry)
        for entry in (".local/bin/random-wallpaper", ".local/bin/random-wallpaper.sh", ".local/bin/waybar-level"):
            self.assertIn(entry, files)

    def test_setup_keeps_native_shell_and_backends_not_replaced_frontends(self):
        packages = (ROOT / "setup/dnf-packages.txt").read_text().splitlines()
        for obsolete in ("waybar", "ironbar", "swaybg", "waypaper", "impala", "bluetuith", "blueman", "pavucontrol", "wiremix", "wofi"):
            self.assertNotIn(obsolete, packages)
        for retained in ("noctalia", "iwd", "mako", "rofi", "hypridle", "hyprlock", "tuned-ppd"):
            self.assertIn(retained, packages)


if __name__ == "__main__":
    unittest.main()
