"""Validate on-demand Bluetooth controls without changing adapter/device state."""

import configparser
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def waybar():
    text = (ROOT / ".config/waybar/config.jsonc").read_text()
    return json.loads(re.sub(r",\s*([}\]])", r"\1", text))


class BluetoothSetupTest(unittest.TestCase):
    def test_native_bluetooth_module_is_enabled_once_beside_network(self):
        config = waybar()
        modules = sum((config.get(key, []) for key in
                       ("modules-left", "modules-center", "modules-right")), [])
        self.assertEqual(modules.count("bluetooth"), 1)
        self.assertNotIn("custom/bluetooth", modules)
        right = config["modules-right"]
        self.assertEqual(right[right.index("bluetooth") + 1], "network")
        module = config["bluetooth"]
        self.assertNotIn("exec", module)
        self.assertNotIn("interval", module)
        self.assertIn("{status}", module["tooltip-format"])
        self.assertIn("{num_connections}", module["tooltip-format"])

    def test_buttons_match_the_wifi_terminal_workflow(self):
        module = waybar()["bluetooth"]
        for button, title, executable in (
            ("on-click", "bluetooth-select", "/home/chihin/.local/bin/bluetuith"),
            ("on-click-right", "bluetooth-console", "bluetoothctl"),
        ):
            with self.subTest(button=button):
                self.assertEqual(shlex.split(module[button]), [
                    "kitty", "--class", "bluetooth-select", "--title", title,
                    "-o", "close_on_child_death=yes", executable,
                ])
        self.assertNotIn("on-click-middle", module)
        self.assertIn("Left: bluetuith", module["tooltip-format"])
        self.assertIn("Right: advanced bluetoothctl console", module["tooltip-format"])

    def test_blueman_autostart_is_suppressed_without_a_replacement_daemon(self):
        config = configparser.ConfigParser()
        config.read(ROOT / ".config/autostart/blueman.desktop")
        self.assertTrue(config.getboolean("Desktop Entry", "Hidden"))
        self.assertEqual(config["Desktop Entry"]["Type"], "Application")
        self.assertNotIn("Exec", config["Desktop Entry"])
        manifest = (ROOT / "setup/home-files.txt").read_text().splitlines()
        self.assertIn(".config/autostart/blueman.desktop", manifest)
        startup = (ROOT / ".config/hypr/autostart.lua").read_text()
        for name in ("blueman-applet", "bluetui", "bluetuith"):
            self.assertNotIn(name, startup)

    def test_bluetooth_terminal_floats_like_wifi(self):
        lua = shutil.which("lua")
        if not lua:
            self.skipTest("Lua interpreter unavailable")
        script = '''
            hl = { window_rule = function(rule)
                if rule.name == "wifi-select" or rule.name == "bluetooth-select" then
                    print(table.concat({rule.name, rule.match.class,
                        tostring(rule.float), rule.size[1], rule.size[2],
                        tostring(rule.opaque)}, "\\t"))
                end
            end }
            dofile(%s)
        ''' % json.dumps(str(ROOT / ".config/hypr/window-rules.lua"))
        result = subprocess.run([lua, "-"], input=script, text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        rules = dict((fields[0], fields[1:]) for fields in
                     (line.split("\t") for line in result.stdout.splitlines()))
        self.assertEqual(rules["bluetooth-select"],
                         ["^bluetooth-select$", "true", "800", "500", "true"])
        self.assertEqual(rules["bluetooth-select"][1:], rules["wifi-select"][1:])

    def test_status_icons_use_nerd_font_and_network_color(self):
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
        except (ImportError, ValueError):
            self.skipTest("GTK/PyGObject unavailable; run with /usr/bin/python3")
        if not Gtk.init_check()[0]:
            self.skipTest("GTK rendering requires a display")
        provider = Gtk.CssProvider()
        provider.load_from_path(str(ROOT / ".config/waybar/style.css"))
        module = waybar()["bluetooth"]
        for key in ("format", "format-off", "format-disabled", "format-no-controller"):
            with self.subTest(state=key):
                icon = module[key]
                self.assertEqual(len(icon), 1)
                label = Gtk.Label(label=icon)
                label.set_name("bluetooth")
                context = label.get_style_context()
                context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                self.assertEqual(context.get_property("font-family", Gtk.StateFlags.NORMAL)[0],
                                 "JetBrainsMono Nerd Font")
                color = context.get_color(Gtk.StateFlags.NORMAL)
                for actual, expected in zip((color.red, color.green, color.blue),
                                            (0xB7 / 255, 0xC5 / 255, 1)):
                    self.assertAlmostEqual(actual, expected, places=5)
                self.assertEqual(label.create_pango_layout(icon).get_unknown_glyphs_count(), 0)


if __name__ == "__main__":
    unittest.main()
