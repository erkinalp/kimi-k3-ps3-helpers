# kimi-k3-ps3-helpers

Hardware bring-up, deployment, and rack-engineering helpers for running the
[`ram-coffers`](https://github.com/erkinalp/ram-coffers) Kimi-K3 PlayStation 3
expert cluster on **real consoles and real racks**.

This repo is deliberately the *PS3-specific* half of the project. `ram-coffers`
holds the portable core — the P3XC protocol, the coordinators (subcluster /
region / layer), the dispatcher, dedup, topology/config, and the numpy
reference worker — all of which build anywhere with a C compiler and CPython and
retarget to newer servers of the same hardware lineage at build time. Everything
that only makes sense on a PS3 (or on a physical farm of them) lives here:

- console **bring-up** (a deployable expert-worker service + OtherOS/CFW notes),
- **deployment** helpers (inventory-driven `cluster.json`, start scripts,
  diskless/NFS root image recipe),
- **power** helpers (Wake-on-LAN and out-of-band power control keyed off the
  fleet inventory),
- **rack/hardware** engineering (the recased-sled power, cooling, and layout
  spec, plus a burn-in/qualification checklist).

> **Status.** None of this has been validated on physical PS3 hardware, SPE, or
> RSX in the environment that produced it. The Python/shell helpers are tested
> against the `ram-coffers` reference worker over loopback TCP; the hardware,
> firmware, power, and rack material is an engineering design to be verified on
> real consoles before any load is applied. Treat the electrical and thermal
> sections as a spec to review with a qualified engineer, not a wiring guide.

## Relationship to ram-coffers

```
ram-coffers  (portable core, retargetable at build time)
  ps3_cluster/            protocol, coordinators, dispatch, dedup, hierarchy
  tools/run_expert.py     numpy reference console worker  (P3XC over TCP)
  ppu|spu|rsx/            the one hardware-bound piece: the expert GEMV kernel
        │
        │  P3XC contract (see docs/P3XC_CONTRACT.md)
        ▼
kimi-k3-ps3-helpers  (this repo, PS3-specific)
  bringup/    turn a console into a P3XC expert worker (service + notes)
  deploy/     inventory → cluster.json, start scripts, diskless image
  power/      WoL + out-of-band power control from the inventory
  rack/       recased-sled hardware spec + burn-in checklist
```

The **only** coupling is the P3XC wire contract and the `cluster.json` schema,
both of which are owned by `ram-coffers` and mirrored (not forked) in
[`docs/P3XC_CONTRACT.md`](docs/P3XC_CONTRACT.md). If those change upstream, this
repo follows.

## Quick start (loopback, no hardware)

Point `RAM_COFFERS` at a checkout of the core repo, then bring a small farm up
entirely on one host — this is exactly what the deploy helpers automate on real
consoles, minus the hardware:

```bash
export RAM_COFFERS=/path/to/ram-coffers/ps3-cluster

# 1. describe a fleet (one row per console) and generate cluster.json
python3 deploy/gen_fleet_config.py \
    --inventory examples/fleet_inventory.csv \
    --layer 3 --size 22 --regions 1 \
    -o /tmp/cluster.json

# 2. bring the whole thing up (workers, heads, region) as local processes
deploy/start_fleet_local.sh /tmp/cluster.json

# 3. run one token through it and check it against the flat dispatcher
python3 "$RAM_COFFERS/tools/run_layer.py" --config /tmp/cluster.json --ping
```

On real consoles, step 2 is replaced by the `bringup/` service on each PS3 plus
`deploy/start_subcluster.sh` / `start_region.sh` on the head servers; the config
in step 1 comes from your real inventory instead of the example CSV.

## Layout

| Path | What |
|------|------|
| `docs/P3XC_CONTRACT.md` | The wire/config contract this repo targets (mirror of ram-coffers). |
| `bringup/` | `ps3-expert@.service`, `install_console.sh`, OtherOS/CFW/noBD notes. |
| `deploy/` | `gen_fleet_config.py`, start scripts, `DISKLESS_NFS_IMAGE.md`. |
| `power/` | `wol.py`, `power_cycle.py` (pluggable OOB backends), fleet helpers. |
| `rack/` | `RACK_HARDWARE_SPEC.md`, `BURN_IN_CHECKLIST.md`. |
| `examples/` | `fleet_inventory.csv` sample. |
| `tests/` | loopback tests for the deploy/power helpers. |

See [`AGENTS.md`](AGENTS.md) for how the pieces fit and what is and isn't safe to
assume.

## License

GNU Affero General Public License v3.0 (AGPL-3.0), the same license as
[`ram-coffers`](https://github.com/erkinalp/ram-coffers). See [`LICENSE`](LICENSE).
Because AGPL's network-use clause applies, anyone operating a farm built from
this tooling and offering it over a network must offer the corresponding source.
