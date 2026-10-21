"""Exercise volume controls without touching the live audio session or OSD."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".local/bin/waybar-level"

MOCK = r'''
import json
import os
from pathlib import Path
import sys

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["MOCK_CALLS"], "a") as log:
    log.write(json.dumps([name, *args]) + "\n")
if name != "wpctl":
    sys.exit(0)

path = Path(os.environ["MOCK_STATE"])
state = json.loads(path.read_text())
if args[0] == "get-volume":
    if state.get("fail_get"):
        sys.exit(1)
    suffix = " [MUTED]" if state["muted"] else ""
    print(f'Volume: {state["volume"]:.2f}{suffix}')
elif args[0] == "set-volume":
    if state.get("fail_set"):
        sys.exit(1)
    delta = 0.05 if args[-1] == "5%+" else -0.05
    state["volume"] = max(0, state["volume"] + delta)
    if "-l" in args:
        state["volume"] = min(1, state["volume"])
    path.write_text(json.dumps(state))
elif args[0] == "set-mute":
    state["muted"] = not state["muted"]
    path.write_text(json.dumps(state))
else:
    sys.exit(2)
'''


class WaybarLevelTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="waybar-level-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / "state.json"
        self.log = self.directory / "calls.jsonl"
        bin_dir = self.directory / "bin"
        bin_dir.mkdir()
        for name in ("wpctl", "pkill", "makoctl", "notify-send", "brightnessctl"):
            path = bin_dir / name
            path.write_text(f"#!{sys.executable}\n{MOCK}")
            path.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "XDG_RUNTIME_DIR": str(self.directory),
            "MOCK_STATE": str(self.state),
            "MOCK_CALLS": str(self.log),
        }

    def run_volume(self, volume, action, muted=False, **state):
        initial = {"volume": volume, "muted": muted, **state}
        self.state.write_text(json.dumps(initial))
        self.log.write_text("")
        result = subprocess.run(
            [str(SCRIPT), "volume", action],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=5,
        )
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return result, json.loads(self.state.read_text()), calls

    def test_outward_keys_at_limits_do_nothing(self):
        for volume, action in ((0, "down"), (1, "up"), (1.2, "up")):
            for muted in (False, True):
                with self.subTest(volume=volume, action=action, muted=muted):
                    result, state, calls = self.run_volume(volume, action, muted)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(state, {"volume": volume, "muted": muted})
                    self.assertEqual(calls, [["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]])
                    self.assertEqual(result.stdout, "")

    def test_normal_steps_and_near_limits(self):
        cases = (
            (0, "up", 0.05),
            (1, "down", 0.95),
            (0.6, "up", 0.65),
            (0.6, "down", 0.55),
            (0.98, "up", 1),
            (0.02, "down", 0),
        )
        for volume, action, expected in cases:
            with self.subTest(volume=volume, action=action):
                result, state, calls = self.run_volume(volume, action)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertAlmostEqual(state["volume"], expected)
                writes = [call for call in calls if call[:2] == ["wpctl", "set-volume"]]
                args = ["-l", "1"] if action == "up" else []
                step = "5%+" if action == "up" else "5%-"
                self.assertEqual(writes, [["wpctl", "set-volume", *args, "@DEFAULT_AUDIO_SINK@", step]])
                self.assertEqual(sum(call[0] == "notify-send" for call in calls), 1)
                self.assertIn(["pkill", "-RTMIN+10", "-x", "waybar"], calls)

    def test_mute_toggle_still_works_at_limits(self):
        for volume in (0, 1):
            result, state, calls = self.run_volume(volume, "toggle")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(state, {"volume": volume, "muted": True})
            self.assertIn(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], calls)
            self.assertTrue(any(call[0] == "notify-send" for call in calls))

    def test_status_is_read_only(self):
        result, _, calls = self.run_volume(0.6, "status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["percentage"], 60)
        self.assertEqual(calls, [["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]])

    def test_audio_errors_do_not_send_notifications(self):
        for failure in ("fail_get", "fail_set"):
            with self.subTest(failure=failure):
                result, state, calls = self.run_volume(0.6, "up", **{failure: True})
                self.assertEqual(result.returncode, 1)
                self.assertEqual(state["volume"], 0.6)
                self.assertTrue(all(call[0] == "wpctl" for call in calls))


if __name__ == "__main__":
    unittest.main()
