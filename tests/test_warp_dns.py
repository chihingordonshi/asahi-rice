"""Keep network/VPN DNS automatic, without static pins or power-profile hooks."""

import configparser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "setup"
RETIRED_UNITS = (
    "resolved-power-saver.service",
    "resolved-performance.service",
    "resolved-power-saver-at-boot.service",
)


class AutomaticDnsTest(unittest.TestCase):
    def test_iwd_publishes_network_dns(self):
        config = configparser.ConfigParser()
        config.read(SETUP / "iwd-main.conf")
        self.assertEqual(config["Network"]["NameResolvingService"], "systemd")
        self.assertTrue(config.getboolean("General", "EnableNetworkConfiguration"))

    def test_no_static_dns_or_domain_pins(self):
        for name in ("resolved-low-power.conf", "resolved-warp-dns.conf"):
            with self.subTest(file=name):
                config = configparser.ConfigParser()
                config.read(SETUP / name)
                for option in ("DNS", "FallbackDNS", "Domains"):
                    self.assertNotIn(option, config["Resolve"])
        lines = (SETUP / "warp-resolv.conf").read_text().splitlines()
        self.assertTrue(all(not line.strip() or line.lstrip().startswith("#") for line in lines))
        self.assertIn("RETIRED", lines[0])

    def test_retired_units_cannot_stop_or_mask_resolved(self):
        for unit in RETIRED_UNITS:
            with self.subTest(unit=unit):
                config = configparser.ConfigParser()
                config.read(SETUP / unit)
                self.assertTrue(config.getboolean("Unit", "RefuseManualStart"))
                self.assertEqual(dict(config["Service"]),
                                 {"type": "oneshot", "execstart": "/usr/bin/true"})
                self.assertNotIn("Install", config)

    def test_profile_changes_have_no_dns_or_wallpaper_side_effect(self):
        script = (ROOT / ".local/bin/waybar-power-profile-cycle.sh").read_text()
        self.assertNotIn("sudo", script)
        self.assertNotIn("systemctl", script)
        self.assertNotIn("resolvectl", script)
        self.assertNotIn("waypaper", script)
        lines = (SETUP / "power-profile-resolver.sudoers").read_text().splitlines()
        self.assertTrue(all(not line.strip() or line.lstrip().startswith("#") for line in lines))

    def test_bootstrap_does_not_reinstall_the_retired_dns_policy(self):
        script = (SETUP / "install.sh").read_text()
        for name in (*RETIRED_UNITS, "resolved-warp-dns.conf", "warp-resolv.conf",
                     "power-profile-resolver.sudoers"):
            self.assertNotIn(name, script)


if __name__ == "__main__":
    unittest.main()
