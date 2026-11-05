"""Keep WeChat input aligned without forcing its subwindows to tile."""

import configparser
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WeChatSetupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lua = shutil.which("lua") or shutil.which("luajit")
        if not lua:
            raise unittest.SkipTest("Lua interpreter unavailable")
        script = '''
            hl = { window_rule = function(rule)
                if rule.name:match("^wechat") then
                    print(table.concat({rule.name, rule.match.class or "",
                        rule.match.title or "", tostring(rule.tile),
                        tostring(rule.float), tostring(rule.no_max_size)}, "\\t"))
                end
            end }
            dofile(%s)
        ''' % json.dumps(str(ROOT / ".config/hypr/window-rules.lua"))
        result = subprocess.run([lua, "-"], input=script, text=True,
                                capture_output=True, timeout=5, check=True)
        cls.rules = [dict(zip(("name", "class", "title", "tile", "float", "no_max_size"),
                             line.split("\t")))
                     for line in result.stdout.splitlines()]

    def matching_rules(self, app_class, title):
        return [rule for rule in self.rules
                if re.fullmatch(rule["class"], app_class)
                and (not rule["title"] or re.fullmatch(rule["title"], title))]

    def test_only_main_window_ignores_maximum_size_hints(self):
        for app_class in ("wechat", "WeChat", "Wechat", "weChat"):
            for title in ("Weixin", "WeChat", "微信"):
                with self.subTest(app_class=app_class, title=title):
                    rules = self.matching_rules(app_class, title)
                    self.assertTrue(rules)
                    self.assertTrue(any(rule["no_max_size"] == "true" for rule in rules))

    def test_no_wechat_rule_forces_tiling_or_floating(self):
        for rule in self.rules:
            with self.subTest(rule=rule["name"]):
                self.assertEqual(rule["tile"], "nil")
                self.assertEqual(rule["float"], "nil")

    def test_subwindows_keep_their_own_size_and_floating_hints(self):
        for title in ("Open", "表情", "Meme", "Settings", "Image", ""):
            with self.subTest(title=title):
                self.assertEqual(self.matching_rules("wechat", title), [])

    def test_unrelated_applications_keep_their_size_hints(self):
        for app_class in ("terminal", "brave-browser", "wechat-helper", "not-wechat"):
            with self.subTest(app_class=app_class):
                self.assertEqual(self.matching_rules(app_class, "Open"), [])

    def desktop_entry(self, name):
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / ".local/share/applications" / name)
        return config["Desktop Entry"]

    def test_rpm_launcher_uses_xwayland_to_keep_input_and_rendering_in_sync(self):
        entry = self.desktop_entry("wechat.desktop")
        self.assertEqual(shlex.split(entry["Exec"]), [
            "env", "QT_QPA_PLATFORM=xcb", "/usr/bin/wechat", "%U",
        ])
        self.assertEqual(entry["TryExec"], "/usr/bin/wechat")
        self.assertEqual(entry["StartupWMClass"], "wechat")
        self.assertFalse(entry.getboolean("Terminal"))

    def test_stale_flatpak_launcher_is_hidden_and_not_reinstalled(self):
        entry = self.desktop_entry("com.tencent.WeChat.desktop")
        self.assertTrue(entry.getboolean("Hidden"))
        self.assertNotIn("Exec", entry)
        apps = (ROOT / "setup/flatpak-apps.txt").read_text().splitlines()
        self.assertFalse(any("com.tencent.WeChat" in line for line in apps))

    def test_both_launcher_overrides_are_deployed(self):
        manifest = (ROOT / "setup/home-files.txt").read_text().splitlines()
        for name in ("wechat.desktop", "com.tencent.WeChat.desktop"):
            with self.subTest(name=name):
                self.assertIn(f".local/share/applications/{name}", manifest)


if __name__ == "__main__":
    unittest.main()
