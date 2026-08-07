# Test report — kimi-k3-ps3-helpers scaffold

## Unit tests (no hardware, no ram-coffers needed)

```
python3 -m unittest discover -s tests
Ran 22 tests ... OK
```

Covers: inventory CSV parsing (comments, missing columns, non-integer fields,
duplicate-placement rejection, one-layer guard), `cluster.json` generation
(subcluster grouping, real host/port from inventory, contiguous region dealing,
standby addresses, over-provisioned-regions error, JSON round-trip), Wake-on-LAN
magic-packet construction (length, format tolerance, invalid-MAC rejection), and
the power-cycle helper (dry-run, command backend, missing-PDU error,
whole-fleet destructive refusal).

## End-to-end against ram-coffers (loopback, no hardware)

With `RAM_COFFERS` pointing at a `ram-coffers/ps3-cluster` checkout
(commit `0ee3158`):

```
RAM_COFFERS=.../ps3-cluster python3 -m unittest discover -s tests
Ran 25 tests ... OK
```

The extra 3 tests generate a `cluster.json` from the example inventory and load
it with ram-coffers' own `ClusterConfig.load()` (two-tier, three-tier, and
standby), proving the emitted schema is accepted unchanged.

Manual full-fleet rehearsal on one host:

```
gen_fleet_config.py  → 2 subclusters, 1 region, 4 consoles
start_fleet_local.sh --identity → 7 processes up
run_layer.py --ping → rg-0000  up
run_layer.py --layer 3 --experts 0 2 --gates 0.5 0.5 (activation = ones)
    → output = ones   (0.5*I(x) + 0.5*I(x) through region→subcluster→expert)
```

## Not covered (by design)

No physical PS3, SPE, or RSX execution. The bring-up service, diskless image
recipe, power/rack docs, and burn-in checklist are engineering designs to be
validated on real consoles; they are not exercised here.
