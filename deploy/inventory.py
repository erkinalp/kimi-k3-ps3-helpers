#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read and validate the fleet inventory CSV.

The inventory is the single source of truth: cluster.json, Wake-on-LAN lists,
and out-of-band power maps are all derived from it. This module is stdlib-only
so it runs on a stock OtherOS Python as well as on a deployment host.

Each row is one console (one expert x one layer). See
``examples/fleet_inventory.csv`` for the column contract.
"""
from __future__ import annotations

import csv
import dataclasses
from typing import Dict, Iterable, List, Optional

REQUIRED = ("layer", "expert", "host", "port")
OPTIONAL = ("mac", "rack", "slot", "pdu", "pdu_outlet", "cech")


@dataclasses.dataclass(frozen=True)
class Console:
    layer: int
    expert: int
    host: str
    port: int
    mac: Optional[str] = None
    rack: Optional[str] = None
    slot: Optional[str] = None
    pdu: Optional[str] = None
    pdu_outlet: Optional[str] = None
    cech: Optional[str] = None

    @property
    def node_id(self) -> str:
        """Canonical placement id, matching ram-coffers gen_cluster_config."""
        return f"ps3-L{self.layer:03d}-E{self.expert:04d}"


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def load_inventory(path: str) -> List[Console]:
    """Parse ``path`` into ``Console`` rows, skipping ``#`` comment lines.

    Raises ``ValueError`` on a missing required column, a non-integer
    layer/expert/port, or a duplicate ``(layer, expert)`` placement.
    """
    consoles: List[Console] = []
    seen: Dict[tuple, int] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [line for line in fh if not line.lstrip().startswith("#")]
    reader = csv.DictReader(rows)
    if reader.fieldnames is None:
        raise ValueError(f"{path}: no header row")
    missing = [c for c in REQUIRED if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"{path}: missing required column(s): "
                         f"{', '.join(missing)}")
    for lineno, row in enumerate(reader, start=2):
        try:
            layer = int(row["layer"])
            expert = int(row["expert"])
            port = int(row["port"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path}:{lineno}: layer/expert/port must be "
                             f"integers ({exc})") from exc
        host = _clean(row.get("host"))
        if not host:
            raise ValueError(f"{path}:{lineno}: host is required")
        key = (layer, expert)
        if key in seen:
            raise ValueError(f"{path}:{lineno}: duplicate placement "
                             f"L{layer} E{expert} (also line {seen[key]})")
        seen[key] = lineno
        consoles.append(Console(
            layer=layer, expert=expert, host=host, port=port,
            mac=_clean(row.get("mac")), rack=_clean(row.get("rack")),
            slot=_clean(row.get("slot")), pdu=_clean(row.get("pdu")),
            pdu_outlet=_clean(row.get("pdu_outlet")),
            cech=_clean(row.get("cech"))))
    if not consoles:
        raise ValueError(f"{path}: no console rows")
    return consoles


def one_layer(consoles: Iterable[Console]) -> int:
    """Return the single layer id shared by ``consoles`` or raise.

    The generator produces a config for one layer at a time, matching the core
    repo's per-layer ``cluster.json``.
    """
    layers = sorted({c.layer for c in consoles})
    if len(layers) != 1:
        raise ValueError(f"inventory spans multiple layers {layers}; "
                         f"filter to one with --layer")
    return layers[0]
