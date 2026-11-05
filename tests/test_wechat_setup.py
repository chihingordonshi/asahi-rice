"""Keep WeChat tiled despite its client-provided maximum-size hint."""

import json
from pathlib import Path
import re
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

    def test_main_window_and_dialogs_tile_without_maximum_size_limits(self):
        for app_class in ("wechat", "WeChat", "Wechat", "weChat"):
            for title in ("Weixin", "WeChat", "Open", ""):
                with self.subTest(app_class=app_class, title=title):
                    rules = self.matching_rules(app_class, title)
                    self.assertTrue(rules)
                    self.assertTrue(any(rule["tile"] == "true" for rule in rules))
                    self.assertTrue(any(rule["no_max_size"] == "true" for rule in rules))
                    # Even float=false is not a substitute for an explicit tile
                    # effect; keep dialog-specific float rules out of the way.
                    self.assertTrue(all(rule["float"] == "nil" for rule in rules))

    def test_unrelated_applications_keep_their_size_hints(self):
        for app_class in ("terminal", "brave-browser", "wechat-helper", "not-wechat"):
            with self.subTest(app_class=app_class):
                self.assertEqual(self.matching_rules(app_class, "Open"), [])


if __name__ == "__main__":
    unittest.main()
