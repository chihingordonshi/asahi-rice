"""Validate native iwd/Waybar configuration without changing live networking."""

import configparser
import json
from pathlib import Path
import re
import shlex
import unittest

ROOT = Path(__file__).resolve().parents[1]


def waybar_network():
    text = (ROOT / '.config/waybar/config.jsonc').read_text()
    return json.loads(re.sub(r',\s*([}\]])', r'\1', text))['network']


class IwdSetupTest(unittest.TestCase):
    def test_iwd_provides_ip_and_dns_without_disabling_roaming_or_reconnection(self):
        config = configparser.ConfigParser()
        config.read(ROOT / 'setup/iwd-main.conf')
        self.assertTrue(config.getboolean('General', 'EnableNetworkConfiguration'))
        self.assertEqual(config['General']['AddressRandomization'], 'network')
        self.assertEqual(config['Network']['NameResolvingService'], 'systemd')
        self.assertTrue(config.getboolean('Network', 'EnableIPv6'))
        self.assertFalse(config.getboolean('Scan', 'DisablePeriodicScan', fallback=False))
        self.assertFalse(config.getboolean('Scan', 'DisableRoamingScan', fallback=False))
        self.assertEqual(config.getint('Scan', 'InitialPeriodicScanInterval'), 30)
        self.assertEqual(config.getint('Scan', 'MaximumPeriodicScanInterval'), 300)
        self.assertEqual(config['DriverQuirks']['DefaultInterface'], 'brcmfmac')

    def test_resolver_preserves_local_mdns_without_responding_or_llmnr(self):
        config = configparser.ConfigParser()
        config.read(ROOT / 'setup/resolved-low-power.conf')
        self.assertFalse(config.getboolean('Resolve', 'LLMNR'))
        self.assertEqual(config['Resolve']['MulticastDNS'], 'resolve')
        self.assertTrue(config.getboolean('Resolve', 'Cache'))
        self.assertNotIn('DNS', config['Resolve'])
        self.assertNotIn('Domains', config['Resolve'])
        self.assertNotIn('DNSStubListener', config['Resolve'])

    def test_waybar_uses_upstream_impala_and_iwctl(self):
        network = waybar_network()
        self.assertEqual(shlex.split(network['on-click'])[-1], '/home/chihin/.local/bin/impala')
        self.assertEqual(shlex.split(network['on-click-right'])[-1], 'iwctl')
        self.assertNotIn('on-click-middle', network)
        self.assertIn('{essid}', network['format-wifi'])
        self.assertIn('hidden SSIDs', network['tooltip-format'])
        self.assertNotIn('wifi-menu', str(network))
        self.assertNotIn('nmtui', str(network))

    def test_no_legacy_nm_applet_autostart(self):
        self.assertNotIn('nm-applet', (ROOT / '.config/hypr/autostart.lua').read_text())
        config = configparser.ConfigParser()
        config.read(ROOT / '.config/autostart/nm-applet.desktop')
        self.assertTrue(config.getboolean('Desktop Entry', 'Hidden'))
        manifest = (ROOT / 'setup/home-files.txt').read_text().splitlines()
        self.assertIn('.config/autostart/nm-applet.desktop', manifest)
        self.assertNotIn('.local/bin/wifi-menu', manifest)


if __name__ == '__main__':
    unittest.main()
