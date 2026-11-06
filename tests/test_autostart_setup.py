"""Keep XDG autostart limited to intentional system-entry suppression."""

import configparser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "blueman.desktop",
    "imsettings-start.desktop",
    "org.kde.xwaylandvideobridge.desktop",
    "sealertauto.desktop",
}


class AutostartSetupTest(unittest.TestCase):
    def test_only_required_suppression_entries_remain(self):
        entries = {path.name for path in (ROOT / ".config/autostart").iterdir()}
        self.assertEqual(entries, EXPECTED)
        for name in entries:
            with self.subTest(entry=name):
                config = configparser.ConfigParser()
                config.read(ROOT / ".config/autostart" / name)
                entry = config["Desktop Entry"]
                self.assertEqual(entry["Type"], "Application")
                self.assertTrue(entry.getboolean("Hidden"))
                self.assertNotIn("Exec", entry)

    def test_manifest_matches_remaining_entries(self):
        manifest = (ROOT / "setup/home-files.txt").read_text().splitlines()
        entries = {line.removeprefix(".config/autostart/") for line in manifest
                   if line.startswith(".config/autostart/")}
        self.assertEqual(entries, EXPECTED)

    def test_ibus_is_started_by_hyprland_instead(self):
        startup = (ROOT / ".config/hypr/autostart.lua").read_text()
        self.assertIn('ibus-daemon --daemonize --replace --xim', startup)
        self.assertIn("--enable-wayland-im", startup)
        self.assertIn("--emoji-extension=disable", startup)
        self.assertNotIn('hl.exec_cmd("fcitx5 ', startup)
        self.assertFalse((ROOT / ".config/autostart/org.fcitx.Fcitx5.desktop").exists())


if __name__ == "__main__":
    unittest.main()
