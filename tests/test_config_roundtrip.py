"""End-to-end: generated cluster.json must load in ram-coffers unchanged.

The whole point of gen_fleet_config.py is to emit a file the core repo consumes,
so the strongest test loads it with ram-coffers' own ClusterConfig. Needs
RAM_COFFERS pointing at a ram-coffers/ps3-cluster checkout; skips cleanly if
unset so the unit tests still run standalone.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "deploy"))

import gen_fleet_config  # noqa: E402

EXAMPLE = os.path.join(ROOT, "examples", "fleet_inventory.csv")
RAM_COFFERS = os.environ.get("RAM_COFFERS")


@unittest.skipUnless(RAM_COFFERS and os.path.isdir(RAM_COFFERS),
                     "set RAM_COFFERS to a ram-coffers/ps3-cluster checkout")
class TestConfigRoundtrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, RAM_COFFERS)
        from ps3_cluster.deployment import ClusterConfig  # noqa: E402
        cls.ClusterConfig = ClusterConfig

    def _emit(self, argv):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        self.addCleanup(os.unlink, path)
        gen_fleet_config.main(["--inventory", EXAMPLE, "-o", path] + argv)
        return path

    def test_two_tier_loads(self):
        path = self._emit(["--size", "2", "--head-host", "10.0.1.1"])
        cfg = self.ClusterConfig.load(path)
        self.assertEqual(len(cfg.subclusters), 2)
        # every canonical placement is present
        nodes = {m.node_id for sc in cfg.subclusters for m in sc.members}
        self.assertIn("ps3-L003-E0000", nodes)

    def test_three_tier_loads(self):
        path = self._emit(["--size", "1", "--regions", "2",
                           "--head-host", "10.0.1.1",
                           "--region-host", "10.0.2.1"])
        cfg = self.ClusterConfig.load(path)
        self.assertEqual(len(cfg.regions), 2)
        self.assertEqual(len(cfg.subclusters), 4)

    def test_standby_loads(self):
        path = self._emit(["--size", "2", "--head-host", "10.0.1.1",
                           "--head-standby", "1",
                           "--head-standby-host", "10.0.1.2"])
        cfg = self.ClusterConfig.load(path)
        # the file at least round-trips through the core loader with standby set
        with open(path) as fh:
            raw = json.load(fh)
        self.assertIn("standby", raw["subclusters"][0])
        self.assertTrue(cfg.subclusters)


if __name__ == "__main__":
    unittest.main()
