"""Exercise serialized visibility IPC using a fake Noctalia, never the desktop."""

import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".local/bin/noctalia-bar-apply"
LUAJIT = shutil.which("luajit")
MOCK = r'''
import json, os, sys
from pathlib import Path
root = Path(os.environ["XDG_RUNTIME_DIR"])
args = sys.argv[1:]
with (root / "calls").open("a") as log:
    log.write(json.dumps(args) + "\n")
assert args[0] == "msg"
if args[1] == "config-get":
    assert args[2:] == ["bar.default.reserve_space"]
    print((root / "reserved").read_text())
elif args[1] == "config-set":
    assert args[2] == "bar.default.reserve_space"
    if os.environ.get("MOCK_SET_FAIL"):
        sys.exit(17)
    (root / "reserved").write_text(args[3])
    (root / "visible").write_text("true")  # Simulate a bar configuration reload.
    # Model the reported blank-widget case; this does not prove UI recovery.
    (root / "workspaces-ready").write_text("false")
elif args[1] == "bar-auto-hide-set":
    assert args[2:] == ["off", "default"]
    if os.environ.get("MOCK_AUTO_HIDE_FAIL"):
        sys.exit(18)
    (root / "mode").write_text(args[2])
elif args[1] in ("bar-show", "bar-hide"):
    assert args[2:] == ["default"]
    if args[1] == "bar-show" and os.environ.get("MOCK_SHOW_FAIL"):
        sys.exit(20)
    assert (root / "mode").read_text() == "off", "edge reveal must be disabled first"
    (root / "visible").write_text(str(args[1] == "bar-show").lower())
else:
    raise AssertionError(args)
'''


MOCK_HYPRCTL = r'''
import json, os, sys
from pathlib import Path
root = Path(os.environ["XDG_RUNTIME_DIR"])
args = sys.argv[1:]
with (root / "calls").open("a") as log:
    log.write(json.dumps(args) + "\n")
assert len(args) == 2 and args[0] == "eval"
assert (root / "visible").read_text() == "true", "refresh must follow successful show"
if os.environ.get("MOCK_REFRESH_FAIL"):
    sys.exit(19)
if os.environ.get("MOCK_REFRESH_ERROR_REPLY"):
    print("Lua error: refresh failed")
    sys.exit(0)
(root / "workspaces-ready").write_text("true")
print("ok")
'''


class NoctaliaBarApplyTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="noctalia-apply-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.runtime = Path(temporary.name)
        bin_dir = self.runtime / "bin"
        bin_dir.mkdir()
        mock = bin_dir / "noctalia"
        mock.write_text(f"#!{sys.executable}\n{MOCK}")
        mock.chmod(0o755)
        hyprctl = bin_dir / "hyprctl"
        hyprctl.write_text(f"#!{sys.executable}\n{MOCK_HYPRCTL}")
        hyprctl.chmod(0o755)
        (self.runtime / "workspaces-ready").write_text("true")
        (self.runtime / "reserved").write_text("false")
        (self.runtime / "mode").write_text("on")  # Upgrade from edge-reveal mode.
        (self.runtime / "calls").write_text("")
        self.env = {**os.environ, "XDG_RUNTIME_DIR": str(self.runtime),
                    "PATH": f"{bin_dir}:{os.environ['PATH']}"}

    def desired(self, reserve, visibility):
        temporary = self.runtime / "desired.tmp"
        temporary.write_text(f"{reserve} {visibility}\n")
        temporary.replace(self.runtime / "noctalia-bar.desired")

    def calls(self):
        return [json.loads(line) for line in (self.runtime / "calls").read_text().splitlines()]

    def run_helper(self):
        return subprocess.run(["bash", str(HELPER)], env=self.env, text=True,
                              capture_output=True, timeout=5)

    def test_pin_sets_gap_shows_then_refreshes_workspace_snapshot(self):
        self.desired("true", "show")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[:-1], [
            ["msg", "config-get", "bar.default.reserve_space"],
            ["msg", "config-set", "bar.default.reserve_space", "true"],
            ["msg", "bar-auto-hide-set", "off", "default"],
            ["msg", "bar-show", "default"],
        ])
        self.assertEqual(self.calls()[-1][0], "eval")
        self.assertEqual((self.runtime / "reserved").read_text(), "true")
        self.assertEqual((self.runtime / "visible").read_text(), "true")
        self.assertEqual((self.runtime / "workspaces-ready").read_text(), "true")

    def test_show_refreshes_workspace_snapshot_without_settings_reload(self):
        (self.runtime / "workspaces-ready").write_text("false")
        self.desired("false", "show")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[:-1], [
            ["msg", "config-get", "bar.default.reserve_space"],
            ["msg", "bar-auto-hide-set", "off", "default"],
            ["msg", "bar-show", "default"],
        ])
        self.assertEqual(self.calls()[-1][0], "eval")
        self.assertEqual((self.runtime / "workspaces-ready").read_text(), "true")

    @unittest.skipUnless(LUAJIT, "luajit is required to validate the refresh code")
    def test_workspace_refresh_lua_preserves_exact_name_and_skips_missing_workspace(self):
        self.desired("false", "show")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1][0], "eval")
        code = self.calls()[-1][1]
        scenario = r'''
            local current = nil
            local calls = 0
            hl = {
                get_active_workspace = function() return current end,
                dsp = {workspace = {rename = function(options) return options end}},
                dispatch = function(options)
                    assert(options.workspace == current)
                    assert(options.name == current.name)
                    calls = calls + 1
                end,
            }
            local refresh = assert(loadstring(arg[1]))
            refresh(); assert(calls == 0)
            current = {}; refresh(); assert(calls == 0)
            current = {name = ""}; refresh(); assert(calls == 0)
            current = {name = 'named "quotes" \\ newline\n中文'}
            local name = current.name
            refresh(); assert(calls == 1 and current.name == name)
        '''
        result = subprocess.run([LUAJIT, "-", code], input=scenario,
                                text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unpin_releases_gap_then_hides_without_edge_reveal(self):
        (self.runtime / "reserved").write_text("true")
        self.desired("false", "hide")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [
            ["msg", "config-get", "bar.default.reserve_space"],
            ["msg", "config-set", "bar.default.reserve_space", "false"],
            ["msg", "bar-auto-hide-set", "off", "default"],
            ["msg", "bar-hide", "default"],
        ])
        self.assertEqual((self.runtime / "reserved").read_text(), "false")
        self.assertEqual((self.runtime / "visible").read_text(), "false")

    def test_unchanged_reservation_avoids_settings_reload(self):
        self.desired("false", "hide")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 3)
        self.assertFalse(any(call[1] == "config-set" for call in self.calls()))
        self.assertEqual((self.runtime / "visible").read_text(), "false")

    def test_queued_jobs_read_latest_state_after_taking_lock(self):
        lock_path = self.runtime / "noctalia-bar.lock"
        with lock_path.open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.desired("true", "show")
            first = subprocess.Popen(["bash", str(HELPER)], env=self.env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.desired("false", "hide")
            second = subprocess.Popen(["bash", str(HELPER)], env=self.env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fcntl.flock(lock, fcntl.LOCK_UN)
        for process in (first, second):
            output, error = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, error.decode())
        self.assertEqual((self.runtime / "reserved").read_text(), "false")
        self.assertEqual((self.runtime / "visible").read_text(), "false")
        self.assertFalse(any(call[1] in ("config-set", "bar-show") for call in self.calls()))
        self.assertEqual([call for call in self.calls() if call[1] == "bar-hide"],
                         [["msg", "bar-hide", "default"]] * 2)

    def test_queued_shows_refresh_after_the_last_rebuild(self):
        with (self.runtime / "noctalia-bar.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.desired("false", "hide")
            first = subprocess.Popen(["bash", str(HELPER)], env=self.env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.desired("true", "show")
            second = subprocess.Popen(["bash", str(HELPER)], env=self.env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fcntl.flock(lock, fcntl.LOCK_UN)
        for process in (first, second):
            output, error = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, error.decode())
        calls = self.calls()
        self.assertEqual(sum(call[:2] == ["msg", "config-set"] for call in calls), 1)
        self.assertEqual(sum(call[0] == "eval" for call in calls), 2)
        self.assertEqual(calls[-1][0], "eval")
        self.assertEqual((self.runtime / "visible").read_text(), "true")
        self.assertEqual((self.runtime / "workspaces-ready").read_text(), "true")

    def test_failed_show_does_not_request_snapshot_refresh(self):
        self.desired("true", "show")
        self.env["MOCK_SHOW_FAIL"] = "1"
        result = self.run_helper()
        self.assertEqual(result.returncode, 20)
        self.assertEqual(self.calls()[-1], ["msg", "bar-show", "default"])
        self.assertFalse(any(call[0] == "eval" for call in self.calls()))
        self.assertEqual((self.runtime / "workspaces-ready").read_text(), "false")

    def test_failed_refresh_preserves_successful_show_and_reports_failure(self):
        self.desired("true", "show")
        self.env["MOCK_REFRESH_FAIL"] = "1"
        result = self.run_helper()
        self.assertEqual(result.returncode, 19)
        self.assertEqual((self.runtime / "reserved").read_text(), "true")
        self.assertEqual((self.runtime / "visible").read_text(), "true")
        self.assertEqual((self.runtime / "workspaces-ready").read_text(), "false")

    def test_lua_error_reply_is_not_treated_as_success(self):
        self.desired("true", "show")
        self.env["MOCK_REFRESH_ERROR_REPLY"] = "1"
        result = self.run_helper()
        self.assertEqual(result.returncode, 1)
        self.assertIn("workspace refresh failed", result.stderr)
        self.assertEqual((self.runtime / "visible").read_text(), "true")

    def test_failed_setting_write_does_not_run_visibility_commands(self):
        self.desired("true", "show")
        self.env["MOCK_SET_FAIL"] = "1"
        result = self.run_helper()
        self.assertEqual(result.returncode, 17)
        self.assertEqual([call[1] for call in self.calls()], ["config-get", "config-set"])

    def test_failed_auto_hide_disable_does_not_hide_with_edge_reveal_enabled(self):
        self.desired("false", "hide")
        self.env["MOCK_AUTO_HIDE_FAIL"] = "1"
        result = self.run_helper()
        self.assertEqual(result.returncode, 18)
        self.assertEqual([call[1] for call in self.calls()], ["config-get", "bar-auto-hide-set"])

    def test_invalid_state_never_reaches_noctalia(self):
        for reserve, visibility in (("invalid", "show"), ("false", "invalid"),
                                    ("false", "on"), ("false", "off")):
            with self.subTest(reserve=reserve, visibility=visibility):
                self.desired(reserve, visibility)
                self.assertEqual(self.run_helper().returncode, 2)
                self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
