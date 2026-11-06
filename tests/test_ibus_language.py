"""Exercise the shared IBus switch without sending keys or changing live settings."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".local/bin/ibus-language"
CONFIGURE = ROOT / "setup/configure-ibus.sh"

MOCK = r'''
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
with open(os.environ["MOCK_CALLS"], "a") as log:
    log.write(json.dumps([Path(sys.argv[0]).name, *args]) + "\n")
if Path(sys.argv[0]).name == "gsettings":
    sys.exit(0)
state_path = Path(os.environ["MOCK_STATE"])
state = json.loads(state_path.read_text())
if not state.get("available", True):
    print("Can't connect to IBus.", file=sys.stderr)
    sys.exit(1)
if args == ["engine"]:
    print(state["engine"])
elif len(args) == 2 and args[0] == "engine":
    if state.get("fail_set"):
        sys.exit(1)
    state["engine"] = args[1]
    state_path.write_text(json.dumps(state))
else:
    sys.exit(2)
'''


class IBusLanguageTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="ibus-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / "state.json"
        self.calls = self.directory / "calls.jsonl"
        self.calls.write_text("")
        self.state.write_text(json.dumps({"engine": "xkb:us::eng"}))
        bin_dir = self.directory / "bin"
        bin_dir.mkdir()
        for name in ("ibus", "gsettings"):
            path = bin_dir / name
            path.write_text(f"#!{sys.executable}\n{MOCK}")
            path.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "XDG_RUNTIME_DIR": str(self.directory),
            "MOCK_STATE": str(self.state),
            "MOCK_CALLS": str(self.calls),
        }

    def run_helper(self, action, engine="xkb:us::eng", **options):
        self.state.write_text(json.dumps({"engine": engine, **options}))
        return subprocess.run([str(HELPER), action], env=self.env, text=True,
                              capture_output=True, timeout=5)

    def test_status_is_json_and_does_not_change_engine(self):
        for engine, text in (("xkb:us::eng", "EN"), ("rime", "CN"), ('other"engine', 'other"engine')):
            with self.subTest(engine=engine):
                result = self.run_helper("status", engine)
                self.assertEqual(result.returncode, 0, result.stderr)
                status = json.loads(result.stdout)
                self.assertEqual(status["text"], text)
                self.assertIn("Super+R", status["tooltip"])
                self.assertIn("global", status["tooltip"])
                self.assertEqual(json.loads(self.state.read_text())["engine"], engine)

    def test_toggle_uses_only_english_and_rime(self):
        for engine, expected in (("xkb:us::eng", "rime"), ("rime", "xkb:us::eng"), ("other", "rime")):
            with self.subTest(engine=engine):
                result = self.run_helper("toggle", engine)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(self.state.read_text())["engine"], expected)

    def test_missing_daemon_keeps_status_visible_but_does_not_toggle(self):
        result = self.run_helper("status", available=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["class"], "unavailable")
        self.assertEqual(result.stderr, "")
        result = self.run_helper("toggle", available=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("IBus is not running", result.stderr)
        self.assertEqual(json.loads(self.state.read_text())["engine"], "xkb:us::eng")

    def test_failed_switch_is_reported(self):
        result = self.run_helper("toggle", fail_set=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(self.state.read_text())["engine"], "xkb:us::eng")

    def test_rapid_switches_are_serialized(self):
        children = [subprocess.Popen([str(HELPER), "toggle"], env=self.env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    for _ in range(4)]
        try:
            for child in children:
                _, error = child.communicate(timeout=5)
                self.assertEqual(child.returncode, 0, error)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.communicate()
        self.assertEqual(json.loads(self.state.read_text())["engine"], "xkb:us::eng")

    def test_invalid_action_does_not_contact_ibus(self):
        result = self.run_helper("invalid")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls.read_text(), "")

    def test_minimal_global_profile_and_no_competing_shortcuts(self):
        result = subprocess.run([str(CONFIGURE)], env=self.env, text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
        settings = {(call[2], call[3]): call[4] for call in calls}
        general = "org.freedesktop.ibus.general"
        panel = "org.freedesktop.ibus.panel"
        self.assertEqual(settings[general, "preload-engines"], "['xkb:us::eng', 'rime']")
        self.assertEqual(settings[general, "use-global-engine"], "true")
        self.assertEqual(settings[panel, "show-icon-on-systray"], "false")
        self.assertEqual(settings[panel, "show"], "0")
        for (schema, key), value in settings.items():
            if schema.endswith(".hotkey") or key in ("hotkey", "unicode-hotkey"):
                self.assertEqual(value, "[]", (schema, key))

    def test_hyprland_and_waybar_share_the_same_switch(self):
        bindings = (ROOT / ".config/hypr/keybindings.lua").read_text()
        self.assertIn('mainMod .. " + R"', bindings)
        self.assertIn("/.local/bin/ibus-language toggle", bindings)
        config = (ROOT / ".config/waybar/config.jsonc").read_text()
        self.assertIn('"on-click": "~/.local/bin/ibus-language toggle"', config)
        self.assertIn('"exec": "~/.local/bin/ibus-language status"', config)
        self.assertNotIn("fcitx5-remote", config + bindings)
        environment = (ROOT / ".config/hypr/environment.lua").read_text()
        self.assertIn('hl.env("XMODIFIERS", "@im=ibus")', environment)
        self.assertNotIn('hl.env("QT_IM_MODULE"', environment)
        self.assertNotIn('hl.env("GTK_IM_MODULE"', environment)


if __name__ == "__main__":
    unittest.main()
