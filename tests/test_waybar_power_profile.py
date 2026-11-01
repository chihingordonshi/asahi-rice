"""Exercise the power-profile buttons without changing live power or wallpaper settings."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / ".local/bin/waybar-power-profile.sh"
CYCLE = ROOT / ".local/bin/waybar-power-profile-cycle.sh"

MOCK = r'''
import json
import os
from pathlib import Path
import sys

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["MOCK_CALLS"], "a") as log:
    log.write(json.dumps([name, *args]) + "\n")
if name == "waypaper-set-backend.sh":
    sys.exit(0)

path = Path(os.environ["MOCK_STATE"])
state = json.loads(path.read_text())
if not state.get("available", True):
    print("The name is not activatable", file=sys.stderr)
    sys.exit(1)
if args[1] == "get-property":
    print("s " + json.dumps(state["profile"]))
elif args[1] == "set-property":
    if state.get("fail_set"):
        sys.exit(1)
    state["profile"] = args[-1]
    path.write_text(json.dumps(state))
else:
    sys.exit(2)
'''


class WaybarPowerProfileTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="waybar-power-profile-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / "state.json"
        self.log = self.directory / "calls.jsonl"
        bin_dir = self.directory / "bin"
        bin_dir.mkdir()
        home = self.directory / "home"
        wallpaper = home / ".local/bin/waypaper-set-backend.sh"
        wallpaper.parent.mkdir(parents=True)
        for path in (bin_dir / "busctl", wallpaper):
            path.write_text(f"#!{sys.executable}\n{MOCK}")
            path.chmod(0o755)
        self.env = {
            **os.environ,
            "HOME": str(home),
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "MOCK_STATE": str(self.state),
            "MOCK_CALLS": str(self.log),
        }

    def run_script(self, script, profile="balanced", **options):
        self.state.write_text(json.dumps({"profile": profile, **options}))
        self.log.write_text("")
        result = subprocess.run(
            [str(script)], env=self.env, text=True, capture_output=True, timeout=5
        )
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return result, json.loads(self.state.read_text()), calls

    def test_status_icons(self):
        for profile, icon in (
            ("performance", "󰑣"),
            ("balanced", "󰗑"),
            ("power-saver", "󰌪"),
            ("unknown", "󰐥"),
        ):
            with self.subTest(profile=profile):
                result, state, calls = self.run_script(STATUS, profile)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["text"], icon)
                self.assertIn(f"Power profile: {profile}", payload["tooltip"])
                self.assertEqual(result.stderr, "")
                self.assertEqual(state["profile"], profile)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][:3], ["busctl", "--system", "get-property"])

    def test_missing_service_keeps_button_visible(self):
        result, _, calls = self.run_script(STATUS, available=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["text"], "󰐥")
        self.assertEqual(payload["class"], "unavailable")
        self.assertIn("unavailable", payload["tooltip"])
        self.assertNotIn("Click to cycle", payload["tooltip"])
        self.assertEqual(result.stderr, "")
        self.assertEqual(len(calls), 1)

    def test_cycle_and_power_saver_wallpaper(self):
        for current, expected in (
            ("performance", "balanced"),
            ("balanced", "power-saver"),
            ("power-saver", "performance"),
            ("unknown", "balanced"),
        ):
            with self.subTest(profile=current):
                result, state, calls = self.run_script(CYCLE, current)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(state["profile"], expected)
                self.assertEqual(calls[1][:3], ["busctl", "--system", "set-property"])
                self.assertEqual(calls[1][-2:], ["s", expected])
                wallpaper_calls = [call for call in calls if call[0] == "waypaper-set-backend.sh"]
                self.assertEqual(
                    wallpaper_calls,
                    [["waypaper-set-backend.sh", "sway"]] if expected == "power-saver" else [],
                )

    def test_cycle_without_service_does_not_write(self):
        result, state, calls = self.run_script(CYCLE, available=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Power profiles unavailable", result.stderr)
        self.assertNotIn("not activatable", result.stderr)
        self.assertEqual(state["profile"], "balanced")
        self.assertEqual(len(calls), 1)

    def test_failed_profile_change_does_not_switch_wallpaper(self):
        result, state, calls = self.run_script(CYCLE, fail_set=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(state["profile"], "balanced")
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[0] == "busctl" for call in calls))


if __name__ == "__main__":
    unittest.main()
