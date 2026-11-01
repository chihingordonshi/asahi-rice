"""Validate the click-to-kill widget without activating the live window picker."""

import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WaybarKillTest(unittest.TestCase):
    def setUp(self):
        text = (ROOT / ".config/waybar/config.jsonc").read_text()
        self.config = json.loads(re.sub(r",\s*([}\]])", r"\1", text))
        self.module = self.config["custom/kill"]

    def test_button_is_enabled_once_beside_suspend(self):
        left = self.config["modules-left"]
        self.assertEqual(left[left.index("custom/suspend") + 1], "custom/kill")
        modules = sum((self.config[f"modules-{side}"] for side in ("left", "center", "right")), [])
        self.assertEqual(modules.count("custom/kill"), 1)
        self.assertEqual(self.module["format"], "󰅖")
        self.assertIn("Esc: cancel", self.module["tooltip-format"])
        self.assertIn("Unsaved work may be lost", self.module["tooltip-format"])

    def test_release_starts_picker_not_press_or_immediate_window_kill(self):
        # Press starts the picker too early: the initiating release cancels it.
        self.assertNotIn("on-click", self.module)
        action = self.module["on-click-release"]
        self.assertEqual(shlex.split(action), ["hyprctl", "kill"])
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="waybar-kill-", dir=artifacts) as temporary:
            directory = Path(temporary)
            log = directory / "args.json"
            mock = directory / "hyprctl"
            mock.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "Path(os.environ['MOCK_CALLS']).write_text(json.dumps(sys.argv[1:]))\n"
            )
            mock.chmod(0o755)
            result = subprocess.run(
                ["/bin/sh", "-c", action],
                env={**os.environ, "PATH": str(directory), "MOCK_CALLS": str(log)},
                text=True, capture_output=True, timeout=5,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(log.read_text()), ["kill"])

    def test_icon_uses_neutral_nerd_font(self):
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
        label = Gtk.Label(label=self.module["format"])
        label.set_name("custom-kill")
        context = label.get_style_context()
        context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.assertEqual(
            context.get_property("font-family", Gtk.StateFlags.NORMAL)[0],
            "JetBrainsMono Nerd Font",
        )
        color = context.get_color(Gtk.StateFlags.NORMAL)
        for actual, expected in zip(
            (color.red, color.green, color.blue, color.alpha),
            (0xE5 / 255, 0xE1 / 255, 0xE7 / 255, 1),
        ):
            self.assertAlmostEqual(actual, expected, places=5)
        layout = label.create_pango_layout(self.module["format"])
        self.assertEqual(layout.get_unknown_glyphs_count(), 0)


if __name__ == "__main__":
    unittest.main()
