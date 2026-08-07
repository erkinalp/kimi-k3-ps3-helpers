#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Out-of-band power control for consoles, keyed off the fleet inventory.

Wake-on-LAN cannot recover a hung console; only cutting and restoring its outlet
can. This maps ``(pdu, pdu_outlet)`` from the inventory to a pluggable backend
that drives your actual power controller. No backend is bundled that talks to
real hardware by default: the shipped backends are ``dry-run`` (print only) and
``command`` (run a templated shell command per outlet), so you wire it to your
own PDU/relay tooling without this repo assuming a vendor.

    # see what would happen
    python3 power/power_cycle.py --inventory examples/fleet_inventory.csv \
        --rack r01 --action cycle --backend dry-run

    # drive a real controller via your own CLI (no secrets in this repo; read
    # credentials from the environment your command template consumes)
    python3 power/power_cycle.py --inventory examples/fleet_inventory.csv \
        --layer 3 --expert 0 --action off \
        --backend command \
        --cmd 'mypdu --host {pdu} --outlet {outlet} --{action}'

Actions: ``on``, ``off``, ``cycle`` (off, wait ``--settle`` seconds, on).
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "deploy"))

from inventory import Console, load_inventory  # noqa: E402


def _select(consoles, rack, layer, expert):
    if rack:
        consoles = [c for c in consoles if c.rack == rack]
    if layer is not None:
        consoles = [c for c in consoles if c.layer == layer]
    if expert is not None:
        consoles = [c for c in consoles if c.expert == expert]
    return consoles


def _run_command(template: str, console: Console, action: str) -> None:
    if not console.pdu or not console.pdu_outlet:
        raise ValueError(f"{console.node_id}: no pdu/pdu_outlet in inventory")
    cmd = template.format(pdu=console.pdu, outlet=console.pdu_outlet,
                          action=action, node=console.node_id,
                          host=console.host)
    subprocess.run(shlex.split(cmd), check=True)


def apply_action(console: Console, action: str, backend: str, cmd: str,
                 settle: float) -> None:
    steps = ["off", "on"] if action == "cycle" else [action]
    for index, step in enumerate(steps):
        if backend == "dry-run":
            print(f"[dry-run] {console.node_id}: {step} "
                  f"(pdu={console.pdu} outlet={console.pdu_outlet})")
        elif backend == "command":
            _run_command(cmd, console, step)
            print(f"{console.node_id}: {step}")
        else:
            raise ValueError(f"unknown backend {backend!r}")
        if action == "cycle" and index == 0:
            time.sleep(settle)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--rack")
    ap.add_argument("--layer", type=int)
    ap.add_argument("--expert", type=int)
    ap.add_argument("--action", required=True, choices=("on", "off", "cycle"))
    ap.add_argument("--backend", default="dry-run",
                    choices=("dry-run", "command"))
    ap.add_argument("--cmd", default="",
                    help="command template for --backend command; fields: "
                         "{pdu} {outlet} {action} {node} {host}")
    ap.add_argument("--settle", type=float, default=5.0,
                    help="seconds between off and on for --action cycle")
    args = ap.parse_args(argv)

    if args.backend == "command" and not args.cmd:
        ap.error("--backend command requires --cmd")

    consoles = _select(load_inventory(args.inventory), args.rack, args.layer,
                       args.expert)
    if not consoles:
        ap.error("no consoles matched the filters")

    # A whole-fleet destructive action deserves an explicit confirmation.
    if args.backend != "dry-run" and args.action in ("off", "cycle") \
            and not (args.rack or args.layer is not None):
        ap.error("refusing to power off the entire inventory; narrow with "
                 "--rack/--layer or use --backend dry-run")

    for console in consoles:
        apply_action(console, args.action, args.backend, args.cmd, args.settle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
