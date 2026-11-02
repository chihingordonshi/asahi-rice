"""Check the client-only mDNS policy without changing the live firewall."""

import configparser
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MdnsFilterTest(unittest.TestCase):
    def test_filter_is_scoped_to_wifi_multicast_queries_only(self):
        text = (ROOT / 'setup/mdns-client-only.nft').read_text()
        rules = [line.strip() for line in text.splitlines() if 'counter drop' in line]
        self.assertEqual(len(rules), 2)
        for rule, destination in zip(rules, ('ip daddr 224.0.0.251', 'ip6 daddr ff02::fb')):
            self.assertIn('iifname "wld0"', rule)
            self.assertIn(destination, rule)
            self.assertIn('udp dport 5353 udp length >= 20', rule)
            self.assertIn('@th,80,16 & 0x8000 == 0 counter drop', rule)
        self.assertIn('policy accept;', text)
        self.assertNotIn('hook output', text)
        self.assertNotIn('flush ruleset', text)
        self.assertNotIn('ct state', text)
        self.assertNotIn('chsrv', text)
        self.assertIn('destroy table inet mdns_client_only', text)

    def test_qr_offset_distinguishes_questions_from_answers(self):
        for flags, is_question in ((0, True), (0x0100, True), (0x8000, False), (0x8400, False)):
            with self.subTest(flags=flags):
                dns = struct.pack('!6H', 0, flags, 1, 0, 0, 0)
                udp = struct.pack('!4H', 5353, 5353, 8 + len(dns), 0) + dns
                self.assertEqual(len(udp), 20)
                flag_field = int.from_bytes(udp[80 // 8:80 // 8 + 2], 'big')
                self.assertEqual(flag_field & 0x8000 == 0, is_question)

    def test_service_loads_once_and_only_removes_its_own_table(self):
        c = configparser.ConfigParser(interpolation=None)
        c.read(ROOT / 'setup/mdns-client-only.service')
        self.assertEqual(c['Service']['Type'], 'oneshot')
        self.assertTrue(c.getboolean('Service', 'RemainAfterExit'))
        self.assertEqual(c['Unit']['After'], 'firewalld.service')
        self.assertEqual(c['Service']['ExecStart'], '/usr/sbin/nft --file /etc/nftables/mdns-client-only.nft')
        self.assertEqual(c['Service']['ExecReload'], c['Service']['ExecStart'])
        self.assertEqual(c['Service']['ExecStop'], '-/usr/sbin/nft delete table inet mdns_client_only')
        self.assertEqual(c['Install']['WantedBy'], 'multi-user.target')
        self.assertNotIn('Restart', c['Service'])


if __name__ == '__main__':
    unittest.main()
