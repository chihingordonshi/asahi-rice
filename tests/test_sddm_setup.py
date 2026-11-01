"""Check the standalone SDDM theme/deployment contract without touching a session."""

import configparser
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "setup/sddm/themes/macos"


class SddmSetupTest(unittest.TestCase):
    def test_wayland_greeter_does_not_require_plasma(self):
        config = configparser.ConfigParser()
        config.read(ROOT / "setup/sddm/10-macos.conf")
        self.assertEqual(config["General"]["DisplayServer"], "wayland")
        self.assertEqual(config["General"]["InputMethod"], "")
        self.assertEqual(config["Theme"]["Current"], "macos")
        self.assertEqual(config["Theme"]["ThemeDir"], "/usr/local/share/sddm/themes")
        self.assertEqual(config["Wayland"]["CompositorCommand"],
                         "/usr/bin/weston --shell=kiosk --config=/etc/sddm/weston.ini")
        self.assertFalse(config.has_section("Autologin"))
        weston = configparser.ConfigParser()
        weston.read(ROOT / "setup/sddm/weston.ini")
        self.assertEqual(weston["output"]["name"], "eDP-1")
        self.assertEqual(weston["output"]["scale"], "2")

    def test_greeter_enables_pointer_and_touchpad_clicking(self):
        config = configparser.ConfigParser()
        config.read(ROOT / "setup/sddm/10-macos.conf")
        self.assertEqual(config["Theme"]["CursorTheme"], "Bibata-Original-Classic")
        self.assertEqual(config["Theme"].getint("CursorSize"), 24)
        weston = configparser.ConfigParser()
        weston.read(ROOT / "setup/sddm/weston.ini")
        self.assertFalse(weston["libinput"].getboolean("disable-input"))
        self.assertTrue(weston["libinput"].getboolean("enable-tap"))
        self.assertTrue(weston["libinput"].getboolean("tap-and-drag"))
        installer = (ROOT / "setup/install-sddm.sh").read_text()
        self.assertIn("test -r /usr/share/icons/Bibata-Original-Classic/cursors/left_ptr", installer)

    def test_theme_pins_uwsm_managed_hyprland(self):
        config = configparser.ConfigParser()
        config.read(THEME / "theme.conf")
        self.assertEqual(config["General"]["sessionFile"],
                         "/usr/share/wayland-sessions/hyprland-uwsm.desktop")

    def test_qt6_theme_metadata(self):
        metadata = configparser.ConfigParser()
        metadata.read(THEME / "metadata.desktop")
        self.assertEqual(metadata["SddmGreeterTheme"]["QtVersion"], "6")
        self.assertTrue((THEME / metadata["SddmGreeterTheme"]["MainScript"]).is_file())

    def test_self_contained_assets(self):
        assets = list(THEME.rglob("*.svg"))
        self.assertGreaterEqual(len(assets), 2)
        for asset in assets:
            tree = ET.parse(asset)
            self.assertEqual(tree.getroot().tag, "{http://www.w3.org/2000/svg}svg")
            for element in tree.iter():
                for attribute, value in element.attrib.items():
                    if attribute.endswith("href"):
                        self.assertTrue(value.startswith("#"), f"External SVG asset: {asset}")
        for qml in THEME.rglob("*.qml"):
            source = qml.read_text()
            self.assertNotRegex(source, r"import\s+org\.kde\.")
            for reference in re.findall(r'\bsource:\s*"([^"\n]+\.(?:svg|png|jpg))"', source):
                self.assertTrue((qml.parent / reference).is_file(), reference)

    def test_migration_preserves_the_live_session_and_authentication(self):
        installer = (ROOT / "setup/install-sddm.sh").read_text()
        self.assertIn("systemctl enable --force sddm.service", installer)
        self.assertIn("systemctl disable plasmalogin.service", installer)
        self.assertNotIn("--now", installer)
        self.assertNotRegex(installer, r"systemctl\s+(?:stop|restart|reboot)")
        self.assertNotIn("/etc/pam.d", installer)
        self.assertIn("if ! sudo test -e /var/lib/sddm/state.conf; then", installer)
        self.assertIn("Session=/usr/share/wayland-sessions/hyprland-uwsm.desktop", installer)
        self.assertIn("-o sddm -g sddm -m 0600", installer)

    def test_package_manifest_uses_sddm_not_kde_identity(self):
        packages = set((ROOT / "setup/dnf-packages.txt").read_text().splitlines())
        self.assertTrue({"sddm", "sddm-wayland-generic", "hyprland-uwsm",
                         "fedora-asahi-remix-release-identity-basic"} <= packages)
        self.assertNotIn("fedora-asahi-remix-release-identity-kde-desktop", packages)
        self.assertNotIn("fedora-asahi-remix-release-kde-desktop", packages)


if __name__ == "__main__":
    unittest.main()
