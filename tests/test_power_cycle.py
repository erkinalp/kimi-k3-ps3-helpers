"""Unit tests for the out-of-band power-cycle helper (dry-run + command)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "power"))
sys.path.insert(0, os.path.join(ROOT, "deploy"))

import power_cycle  # noqa: E402
from inventory import Console  # noqa: E402

EXAMPLE = os.path.join(ROOT, "examples", "fleet_inventory.csv")


class TestPowerCycle(unittest.TestCase):
    def _console(self, **kw):
        base = dict(layer=3, expert=0, host="10.0.0.10", port=9000,
                    pdu="pdu-r01-a", pdu_outlet="1")
        base.update(kw)
        return Console(**base)

    def test_dry_run_on(self):
        # Should not raise and should not require pdu backend.
        power_cycle.apply_action(self._console(), "on", "dry-run", "", 0.0)

    def test_command_backend_missing_pdu_raises(self):
        console = self._console(pdu=None, pdu_outlet=None)
        with self.assertRaises(ValueError):
            power_cycle.apply_action(console, "on", "command",
                                     "true {pdu} {outlet}", 0.0)

    def test_command_backend_runs_template(self):
        # `true` accepts any args and exits 0; proves formatting/splitting work.
        power_cycle.apply_action(self._console(), "on", "command",
                                 "true {pdu} {outlet} {action}", 0.0)

    def test_cli_refuses_whole_fleet_destructive(self):
        # argparse .error() raises SystemExit(2) rather than returning.
        with self.assertRaises(SystemExit):
            power_cycle.main([
                "--inventory", EXAMPLE, "--action", "off",
                "--backend", "command", "--cmd", "true {pdu} {outlet}"])

    def test_cli_dry_run_whole_fleet_allowed(self):
        rc = power_cycle.main([
            "--inventory", EXAMPLE, "--action", "cycle",
            "--backend", "dry-run", "--settle", "0"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    # main() uses argparse .error() which raises SystemExit; wrap for the
    # refusal test so it reports a nonzero "return" instead of aborting.
    unittest.main()
