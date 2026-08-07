"""Unit tests for the Wake-on-LAN magic packet builder."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "power"))

import wol  # noqa: E402


class TestMagicPacket(unittest.TestCase):
    def test_length_is_102(self):
        self.assertEqual(len(wol.magic_packet("00:1f:a7:00:00:10")), 102)

    def test_starts_with_six_ff(self):
        self.assertEqual(wol.magic_packet("001fa7000010")[:6], b"\xff" * 6)

    def test_mac_repeated_16_times(self):
        packet = wol.magic_packet("00-1f-a7-00-00-10")
        mac = bytes.fromhex("001fa7000010")
        self.assertEqual(packet[6:], mac * 16)

    def test_accepts_multiple_formats(self):
        a = wol.magic_packet("00:1f:a7:00:00:10")
        b = wol.magic_packet("001f.a700.0010")
        self.assertEqual(a, b)

    def test_invalid_mac_rejected(self):
        with self.assertRaises(ValueError):
            wol.magic_packet("not-a-mac")


if __name__ == "__main__":
    unittest.main()
