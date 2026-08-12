# P3XC contract (mirror)

This is a **read-only mirror** of the contract owned by
[`ram-coffers`](https://github.com/erkinalp/ram-coffers), pinned to the merged
coordination core on the `kimi-k3-playstation3` branch (PR #1, merge commit
`eb71e56`). It exists so the helpers in this repo can be understood standalone.
The authoritative source is
`ram-coffers/ps3-cluster/ps3_cluster/protocol.py`,
`ps3_cluster/batch.py`, and `ps3_cluster/deployment.py`. **If this file
disagrees with those, they win.**

## What a console must do

A console is an **expert worker**. It listens on TCP and answers P3XC frames for
exactly one `(layer, expert)`. The deployable worker is the C binary
`build/expert_node_host <expert.exp> [port]`; its portable stand-in is
`ram-coffers/tools/run_expert.py`. Both implement the same protocol and
lifecycle, so a head server cannot tell them apart.

Lifecycle a console must honour:

- bind and `accept()`, one connection per coordinator, connections are
  **persistent** (many frames per connection);
- answer `PING` with `PONG` for liveness checks;
- answer `REQ` (an input activation for its `(layer, expert)`) with `RSP` (the
  expert's output activation);
- leave the accept loop cleanly on `SIGTERM`/`SIGINT` so an init system or farm
  script can stop it.

Consoles never see the batched frames (`BREQ`/`BRSP`/`BERR`); those are spoken
only between a layer coordinator and a subcluster/region coordinator.

## Wire format (network byte order, big-endian, length-prefixed)

```
magic     : 4 bytes  b"P3XC"
version   : uint8     (currently 1)
msg_type  : uint8     REQ=1 RSP=2 ERR=3 PING=4 PONG=5  (BREQ=6 BRSP=7 BERR=8)
layer     : uint16
expert    : uint16
token_id  : uint32
dtype     : uint8     F32=1 F16=2 BF16=3 U8(packed MXFP4)=4
ndim      : uint8
shape     : ndim * uint32
payload   : product(shape) * itemsize, big-endian elements
trailer   : optional, batch frames only
```

Cell is natively big-endian, so on a PS3 the byte order is free; a little-endian
head server pays the swap. A frame larger than `1<<26` bytes (64 MiB) is refused
so a bad length prefix cannot exhaust a console's 256 MB of XDR RAM.

## cluster.json schema (what deploy/gen_fleet_config.py must emit)

```json
{
  "subcluster_size": 22,
  "subclusters": [
    {
      "id": "sc-0000",
      "host": "10.0.1.1", "port": 8100,
      "standby": [{"host": "10.0.1.2", "port": 8100}],
      "members": [
        {"layer": 3, "expert": 0,
         "node": "ps3-L003-E0000", "host": "10.0.0.10", "port": 9000}
      ]
    }
  ],
  "regions": [
    {"id": "rg-0000", "host": "10.0.2.1", "port": 8200,
     "standby": [{"host": "10.0.2.2", "port": 8200}],
     "subclusters": ["sc-0000", "sc-0001"]}
  ]
}
```

Rules:

- Node ids are canonical `ps3-L<layer:03d>-E<expert:04d>`; one expert per node.
- `regions` is optional; omit it for a two-tier (layer → head → console) farm.
- `standby` is an ordered list of extra coordinator addresses that failover
  walks; a standby is an **independent process** on another address with its own
  bounded dedup cache, not shared state with the primary.
- The generated file must load unchanged with
  `ram-coffers` `ClusterConfig.load()`.

## Deployment commands owned by the core

The head/region/layer processes are core tooling; this repo only wraps them:

```bash
python3 $RAM_COFFERS/tools/run_expert.py     expert.exp --host 0.0.0.0 --port 9000
python3 $RAM_COFFERS/tools/run_subcluster.py --config cluster.json --subcluster sc-0000
python3 $RAM_COFFERS/tools/run_region.py     --config cluster.json --region rg-0000
python3 $RAM_COFFERS/tools/run_layer.py      --config cluster.json --ping
```
