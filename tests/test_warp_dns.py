"""Validate fail-closed WARP DNS and narrow, daemon-free profile actions."""

import configparser
from pathlib import Path
import shlex
import unittest

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "setup"
UNITS = [
    "systemd-resolved.service",
    "systemd-resolved-varlink.socket",
    "systemd-resolved-monitor.socket",
]


class WarpDnsTest(unittest.TestCase):
    def test_no_lan_or_public_dns_fallback(self):
        lines = (SETUP / "warp-resolv.conf").read_text().splitlines()
        self.assertEqual(
            [line.split()[1] for line in lines if line.startswith("nameserver ")],
            ["127.0.2.2", "127.0.2.3"],
        )
        config = configparser.ConfigParser()
        config.read(SETUP / "resolved-warp-dns.conf")
        self.assertEqual(config["Resolve"]["DNS"].split(), ["127.0.2.2", "127.0.2.3"])
        self.assertEqual(config["Resolve"]["FallbackDNS"], "")
        self.assertEqual(config["Resolve"]["Domains"], "~.")

    def test_power_saver_blocks_service_and_socket_reactivation(self):
        text = (SETUP / "resolved-power-saver.service").read_text()
        config = configparser.ConfigParser()
        config.read_string(text)
        self.assertEqual(config["Service"]["Type"], "oneshot")
        self.assertNotIn("RemainAfterExit", config["Service"])
        self.assertEqual(
            shlex.split(config["Service"]["ExecStartPre"]),
            ["/usr/bin/grep", "-Fxq", "nameserver 127.0.2.2", "/etc/resolv.conf"],
        )
        self.assertEqual(
            shlex.split(config["Service"]["ExecStart"]),
            ["/usr/bin/systemctl", "mask", "--runtime", "--now", *UNITS],
        )

    def test_performance_only_removes_runtime_masks_then_starts_resolved(self):
        lines = (SETUP / "resolved-performance.service").read_text().splitlines()
        self.assertIn("Type=oneshot", lines)
        self.assertEqual(
            [shlex.split(line.partition("=")[2]) for line in lines if line.startswith("ExecStart=")],
            [
                ["/usr/bin/systemctl", "unmask", "--runtime", *UNITS],
                ["/usr/bin/systemctl", "start", "systemd-resolved.service"],
            ],
        )
        self.assertFalse(any(line.startswith("RemainAfterExit=") for line in lines))

    def test_boot_oneshot_only_applies_power_saver_after_profile_service(self):
        config = configparser.ConfigParser()
        config.read(SETUP / "resolved-power-saver-at-boot.service")
        self.assertEqual(config["Unit"]["Wants"], "tuned-ppd.service")
        self.assertEqual(config["Unit"]["After"], "tuned-ppd.service")
        self.assertEqual(config["Service"]["Type"], "oneshot")
        self.assertEqual(config["Service"]["ExecStart"],
                         "/usr/bin/systemctl start resolved-power-saver.service")
        self.assertIn("/usr/bin/grep -Fq power-saver", config["Service"]["ExecCondition"])
        self.assertIn("-o pipefail", config["Service"]["ExecCondition"])
        self.assertEqual(config["Install"]["WantedBy"], "multi-user.target")

    def test_sudo_grant_allows_only_the_two_root_owned_actions(self):
        lines = (SETUP / "power-profile-resolver.sudoers").read_text().splitlines()
        grants = [line for line in lines if line and not line.startswith("#")]
        self.assertEqual(grants, [
            "chihin ALL=(root) NOPASSWD: /usr/bin/systemctl start resolved-power-saver.service, "
            "/usr/bin/systemctl start resolved-performance.service"
        ])


if __name__ == "__main__":
    unittest.main()
