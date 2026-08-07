#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build a ram-coffers ``cluster.json`` from the fleet inventory CSV.

This is the inventory-driven counterpart to ram-coffers'
``tools/gen_cluster_config.py``: instead of numbering consoles off a port base on
one host, it reads real ``(host, port)`` per console from the inventory, groups
them into Condor-sized subclusters, and optionally deals the heads into regions.

The emitted file is the schema documented in ``docs/P3XC_CONTRACT.md`` and is
meant to load unchanged with ram-coffers' ``ClusterConfig.load()``.

    python3 deploy/gen_fleet_config.py \
        --inventory examples/fleet_inventory.csv \
        --layer 3 --size 22 --regions 1 \
        --head-host 10.0.1.1 --region-host 10.0.2.1 \
        -o cluster.json

``--head-host``/``--region-host`` place the coordinators; ``--head-standby`` /
``--region-standby`` add extra (independent) coordinator addresses that failover
walks. Standby ports follow the primaries; edit the emitted hosts so a standby
does not share a machine with the primary it covers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inventory import Console, load_inventory, one_layer  # noqa: E402


def _standby(host, base_port, index, count):
    return [{"host": host, "port": base_port + index * 1000 + n + 1}
            for n in range(count)]


def build_config(consoles, size, head_host, head_port_base,
                 head_standby, head_standby_host,
                 regions, region_host, region_port_base,
                 region_standby, region_standby_host):
    consoles = sorted(consoles, key=lambda c: c.expert)
    subclusters = []
    for index, start in enumerate(range(0, len(consoles), size)):
        chunk = consoles[start:start + size]
        entry = {
            "id": f"sc-{index:04d}",
            "host": head_host,
            "port": head_port_base + index,
            "members": [{"layer": c.layer, "expert": c.expert,
                         "node": c.node_id, "host": c.host, "port": c.port}
                        for c in chunk],
        }
        if head_standby:
            sh = head_standby_host or head_host
            entry["standby"] = _standby(sh, head_port_base + index, 0,
                                        head_standby)
        subclusters.append(entry)

    config = {"subcluster_size": size, "subclusters": subclusters}

    if regions:
        if regions > len(subclusters):
            raise ValueError(f"--regions {regions} exceeds "
                             f"{len(subclusters)} subclusters")
        region_list = []
        # Deal heads out contiguously so a token's top-k lands in few regions.
        per = -(-len(subclusters) // regions)  # ceil
        for rindex, start in enumerate(range(0, len(subclusters), per)):
            members = [sc["id"] for sc in subclusters[start:start + per]]
            entry = {
                "id": f"rg-{rindex:04d}",
                "host": region_host,
                "port": region_port_base + rindex,
                "subclusters": members,
            }
            if region_standby:
                rh = region_standby_host or region_host
                entry["standby"] = _standby(rh, region_port_base + rindex, 0,
                                            region_standby)
            region_list.append(entry)
        config["regions"] = region_list
    return config


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", required=True, help="fleet CSV")
    ap.add_argument("--layer", type=int,
                    help="serve only this layer (required if CSV spans layers)")
    ap.add_argument("--size", type=int, default=22,
                    help="consoles per subcluster (Condor used 22)")
    ap.add_argument("--head-host", default="0.0.0.0")
    ap.add_argument("--head-port-base", type=int, default=8100)
    ap.add_argument("--head-standby", type=int, default=0)
    ap.add_argument("--head-standby-host")
    ap.add_argument("--regions", type=int, default=0)
    ap.add_argument("--region-host", default="0.0.0.0")
    ap.add_argument("--region-port-base", type=int, default=8200)
    ap.add_argument("--region-standby", type=int, default=0)
    ap.add_argument("--region-standby-host")
    ap.add_argument("-o", "--output", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    consoles = load_inventory(args.inventory)
    if args.layer is not None:
        consoles = [c for c in consoles if c.layer == args.layer]
        if not consoles:
            ap.error(f"no consoles for layer {args.layer} in {args.inventory}")
    else:
        one_layer(consoles)  # raise a clear error if the CSV spans layers

    if args.region_standby and not args.regions:
        ap.error("--region-standby needs --regions")

    config = build_config(
        consoles, size=args.size,
        head_host=args.head_host, head_port_base=args.head_port_base,
        head_standby=args.head_standby, head_standby_host=args.head_standby_host,
        regions=args.regions, region_host=args.region_host,
        region_port_base=args.region_port_base,
        region_standby=args.region_standby,
        region_standby_host=args.region_standby_host)

    text = json.dumps(config, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"wrote {args.output}: {len(config.get('regions', []))} regions, "
              f"{len(config['subclusters'])} subclusters, "
              f"{sum(len(s['members']) for s in config['subclusters'])} "
              f"consoles")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
