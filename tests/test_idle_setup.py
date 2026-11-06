"""Regression checks for low-fork desktop configuration; no live changes."""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def config():
    text = (ROOT / '.config/waybar/config.jsonc').read_text()
    return json.loads(re.sub(r',\s*([}\]])', r'\1', text))


class IdleSetupTest(unittest.TestCase):
    def test_networkmanager_is_not_reinstalled_by_package_manifest(self):
        packages = (ROOT / 'setup/dnf-packages.txt').read_text().splitlines()
        self.assertIn('iwd', packages)
        self.assertFalse(any(p.startswith('NetworkManager') for p in packages))
        self.assertNotIn('network-manager-applet', packages)
        self.assertNotIn('nm-connection-editor', packages)

    def test_cpu_and_memory_use_native_waybar_modules(self):
        c = config()
        enabled = c['modules-left'] + c['modules-center'] + c['modules-right']
        for name in ('cpu', 'memory'):
            self.assertEqual(enabled.count(name), 1)
            self.assertNotIn('custom/' + name, enabled)
            self.assertNotIn('exec', c[name])
        self.assertEqual(c['cpu']['interval'], 5)
        self.assertEqual(c['memory']['interval'], 15)
        self.assertIn('{usage7}', c['cpu']['tooltip-format'])
        self.assertIn('btop', c['memory']['on-click'])
        css = (ROOT / '.config/waybar/style.css').read_text()
        self.assertIn('#cpu, #memory,', css)

    def test_controls_keep_signalled_refresh_and_existing_actions(self):
        c = config()
        for name, interval, signal in (('brightness', 10, 11), ('volume', 5, 10)):
            module = c['custom/' + name]
            self.assertEqual(module['interval'], interval)
            self.assertEqual(module['signal'], signal)
            self.assertIn('waybar-level', module['exec'])
            self.assertIn('waybar-level', module['on-scroll-up'])
            self.assertIn('waybar-level', module['on-scroll-down'])
        self.assertIn('toggle', c['custom/volume']['on-click-right'])
        self.assertEqual(c['custom/volume']['on-click'], 'pavucontrol')

    def test_less_frequent_polling_does_not_disable_profile_click_refresh(self):
        c = config()
        self.assertEqual(c['clock']['interval'], 60)
        self.assertNotIn('%S', c['clock']['tooltip-format'])
        self.assertEqual(c['custom/ibus']['interval'], 3)
        self.assertEqual(c['custom/power-profile']['interval'], 30)
        self.assertTrue(c['custom/power-profile'].get('exec-on-event', True))
        self.assertIn('waybar-power-profile-cycle.sh', c['custom/power-profile']['on-click'])


if __name__ == '__main__':
    unittest.main()
