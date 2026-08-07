"""Unit tests for the inventory parser and cluster.json generator."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "deploy"))

import inventory  # noqa: E402
import gen_fleet_config  # noqa: E402

EXAMPLE = os.path.join(ROOT, "examples", "fleet_inventory.csv")


def _write(text):
    fh = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
    fh.write(text)
    fh.close()
    return fh.name


class TestInventory(unittest.TestCase):
    def test_example_loads(self):
        consoles = inventory.load_inventory(EXAMPLE)
        self.assertEqual(len(consoles), 4)
        self.assertEqual(consoles[0].node_id, "ps3-L003-E0000")
        self.assertEqual(consoles[0].port, 9000)
        self.assertEqual(consoles[3].cech, "CECHP")

    def test_comment_lines_skipped(self):
        path = _write("# a comment\nlayer,expert,host,port\n"
                      "# another\n3,0,10.0.0.1,9000\n")
        self.addCleanup(os.unlink, path)
        self.assertEqual(len(inventory.load_inventory(path)), 1)

    def test_missing_required_column(self):
        path = _write("layer,expert,host\n3,0,10.0.0.1\n")
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ValueError):
            inventory.load_inventory(path)

    def test_noninteger_port(self):
        path = _write("layer,expert,host,port\n3,0,10.0.0.1,x\n")
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ValueError):
            inventory.load_inventory(path)

    def test_duplicate_placement_rejected(self):
        path = _write("layer,expert,host,port\n"
                      "3,0,10.0.0.1,9000\n3,0,10.0.0.2,9000\n")
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ValueError):
            inventory.load_inventory(path)

    def test_one_layer_guard(self):
        path = _write("layer,expert,host,port\n"
                      "3,0,10.0.0.1,9000\n4,0,10.0.0.2,9000\n")
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ValueError):
            inventory.one_layer(inventory.load_inventory(path))


class TestGenConfig(unittest.TestCase):
    def _gen(self, **kw):
        consoles = inventory.load_inventory(EXAMPLE)
        return gen_fleet_config.build_config(
            consoles, size=kw.get("size", 2),
            head_host=kw.get("head_host", "10.0.1.1"),
            head_port_base=kw.get("head_port_base", 8100),
            head_standby=kw.get("head_standby", 0),
            head_standby_host=kw.get("head_standby_host"),
            regions=kw.get("regions", 0),
            region_host=kw.get("region_host", "10.0.2.1"),
            region_port_base=kw.get("region_port_base", 8200),
            region_standby=kw.get("region_standby", 0),
            region_standby_host=kw.get("region_standby_host"))

    def test_subcluster_grouping(self):
        cfg = self._gen(size=2)
        self.assertEqual(cfg["subcluster_size"], 2)
        self.assertEqual(len(cfg["subclusters"]), 2)
        self.assertEqual([m["node"] for m in cfg["subclusters"][0]["members"]],
                         ["ps3-L003-E0000", "ps3-L003-E0001"])
        self.assertEqual(cfg["subclusters"][0]["port"], 8100)
        self.assertEqual(cfg["subclusters"][1]["port"], 8101)

    def test_members_carry_real_host_port(self):
        cfg = self._gen(size=4)
        member = cfg["subclusters"][0]["members"][3]
        self.assertEqual(member["host"], "10.0.0.13")
        self.assertEqual(member["port"], 9000)

    def test_regions_deal_contiguously(self):
        cfg = self._gen(size=1, regions=2)
        self.assertEqual(len(cfg["subclusters"]), 4)
        self.assertEqual(len(cfg["regions"]), 2)
        first = cfg["regions"][0]["subclusters"]
        second = cfg["regions"][1]["subclusters"]
        self.assertEqual(first, ["sc-0000", "sc-0001"])
        self.assertEqual(second, ["sc-0002", "sc-0003"])

    def test_standby_addresses(self):
        cfg = self._gen(size=2, head_standby=1, regions=1, region_standby=1)
        self.assertIn("standby", cfg["subclusters"][0])
        self.assertEqual(len(cfg["subclusters"][0]["standby"]), 1)
        self.assertIn("standby", cfg["regions"][0])

    def test_regions_exceed_subclusters(self):
        with self.assertRaises(ValueError):
            self._gen(size=2, regions=5)

    def test_output_is_json(self):
        cfg = self._gen(size=2)
        # round-trips as JSON (what ClusterConfig.load consumes)
        self.assertEqual(json.loads(json.dumps(cfg))["subcluster_size"], 2)


if __name__ == "__main__":
    unittest.main()
