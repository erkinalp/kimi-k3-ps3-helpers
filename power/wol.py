#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wake consoles from the fleet inventory with Wake-on-LAN magic packets.

OtherOS supports WoL from firmware 2.20; enable it on each console before
shutdown (``ethtool -s eth0 wol g``). This sends the magic packet(s) using only
the standard library, so it runs from any deployment host without ether-wake
installed.

    python3 power/wol.py --inventory examples/fleet_inventory.csv          # all
    python3 power/wol.py --inventory examples/fleet_inventory.csv --rack r01
    python3 power/wol.py --inventory examples/fleet_inventory.csv \
        --layer 3 --expert 0

WoL is best-effort: a hung or powered-off-at-the-PDU console will not answer.
For guaranteed state changes use ``power/power_cycle.py`` against the PDU.
"""
from __future__ import annotations

import argparse
import os
import socket
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "deploy"))

from inventory import load_inventory  # noqa: E402


def magic_packet(mac: str) -> bytes:
    """Build the 102-byte WoL magic packet for ``mac`` (any common format)."""
    hexdigits = mac.replace(":", "").replace("-", "").replace(".", "")
    if len(hexdigits) != 12:
        raise ValueError(f"invalid MAC: {mac!r}")
    payload = bytes.fromhex(hexdigits)
    return b"\xff" * 6 + payload * 16


def wake(mac: str, broadcast: str = "255.255.255.255", port: int = 9) -> None:
    packet = magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast, port))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--rack", help="only consoles in this rack")
    ap.add_argument("--layer", type=int, help="only this layer")
    ap.add_argument("--expert", type=int, help="only this expert (with --layer)")
    ap.add_argument("--broadcast", default="255.255.255.255",
                    help="broadcast address for the compute subnet")
    ap.add_argument("--port", type=int, default=9)
    ap.add_argument("--dry-run", action="store_true",
                    help="print who would be woken, send nothing")
    args = ap.parse_args(argv)

    consoles = load_inventory(args.inventory)
    if args.rack:
        consoles = [c for c in consoles if c.rack == args.rack]
    if args.layer is not None:
        consoles = [c for c in consoles if c.layer == args.layer]
    if args.expert is not None:
        consoles = [c for c in consoles if c.expert == args.expert]
    if not consoles:
        ap.error("no consoles matched the filters")

    woken = 0
    for console in consoles:
        if not console.mac:
            print(f"skip {console.node_id}: no MAC in inventory",
                  file=sys.stderr)
            continue
        if args.dry_run:
            print(f"would wake {console.node_id} ({console.mac})")
        else:
            wake(console.mac, args.broadcast, args.port)
            print(f"woke {console.node_id} ({console.mac})")
        woken += 1
    if not woken:
        print("nothing sent (no MACs?)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
