# AGENTS.md

Orientation for anyone (human or agent) working in this repo.

## What this repo is

The **PS3-specific** deployment/hardware half of the Kimi-K3-on-PlayStation-3
project. The portable core lives in
[`ram-coffers`](https://github.com/erkinalp/ram-coffers). This repo never
reimplements the protocol, coordinators, or dispatcher — it only helps get real
consoles and racks to the point where they can speak the core's P3XC protocol.

## Hard rules

1. **Do not fork the protocol.** The P3XC frame format and `cluster.json` schema
   are owned by `ram-coffers`. `docs/P3XC_CONTRACT.md` is a *mirror* for
   reference; if it disagrees with the core repo, the core repo wins. Anything
   that generates `cluster.json` here must produce a file the core's
   `ClusterConfig.load()` accepts unchanged.
2. **Never claim hardware validation that did not happen.** No physical PS3, SPE,
   or RSX execution has been performed here. Say "designed / untested on
   hardware" and mean it. The electrical and thermal material is a spec to be
   reviewed and measured, not a guarantee.
3. **Keep placement canonical.** One expert × one layer per node
   (`ps3-L<layer>-E<expert>`). RSX capacity does not silently pack experts; any
   packing is opt-in and belongs to the core's planner, not to deploy scripts.
4. **Safety first in the hardware docs.** Stock PS3 PSUs are not treated as
   24/7-safe; the original in-case cluster layout is treated as a hack, not the
   production design. Never document wiring the PS3 `ACDC_STBY` enable directly
   to ATX `PS_ON`, and never recommend soldered hooks on the board power posts.

## Dependencies

- Python 3 standard library only for the helpers (`csv`, `json`, `argparse`,
  `socket`, `struct`, `subprocess`). No third-party packages required to run the
  deploy/power tooling.
- `numpy` is only needed transitively when you actually invoke the `ram-coffers`
  reference worker; the helpers themselves don't import it.
- Shell scripts target `bash` and POSIX `ip`/`ping`/`ether-wake` where noted.

## Running the tests

```bash
export RAM_COFFERS=/path/to/ram-coffers/ps3-cluster   # for loopback e2e tests
python3 -m unittest discover -s tests -v
```

Tests that need the core repo skip cleanly (not fail) when `RAM_COFFERS` is
unset, so the unit-level tests still run standalone.

## Conventions

- Every console is one row in the fleet inventory CSV (see
  `examples/fleet_inventory.csv`). The inventory is the single source of truth;
  `cluster.json`, WoL lists, and power maps are all derived from it.
- Keep scripts idempotent and safe to re-run.
- Prefer failing loudly (nonzero exit, clear message) over partial fleet state.
