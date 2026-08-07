# Recased PS3 rack sled — hardware spec

Engineering design for running PS3 expert nodes 24/7 in a rack, rather than as
stock consoles on a shelf. **Nothing here is validated on hardware.** Treat the
electrical and thermal sections as a specification to review with a qualified
electrical/mechanical engineer and to *measure*, not as a wiring guide. Mains
voltages and multi-hundred-amp DC buses are dangerous.

## Design stance

- The **stock internal PSU is not treated as 24/7-safe** at fleet scale, and the
  original in-case cluster layout (consoles in plastic shells on shelving) is a
  hack, not a production design.
- Keep the parts Sony got right: the lower shield/frame, X-clamp, IHS, heatsink,
  **Syscon** thermal protection, and the stock blower's tach/PWM. Discard the
  plastic shell, optical mechanics, and the consumer PSU.
- **One motherboard revision per chassis.** Baseline: CECHL/P/Q-class fat boards
  (65 nm Cell + 65 nm RSX, original OtherOS support, ~130 W nominal vs
  ~170–200 W for early 90 nm units). Mixing revisions turns power, fan, and
  mechanical interfaces into a maintenance problem.

## Power budget (measure before trusting)

Published figures for 65 nm fat units are ~130 W nominal / 280 W max PSU rating.
Plan against a conservative **180 W/node design load** until measured under the
actual SPE/RSX expert kernel, which is not a game workload.

| Scope | Nodes | Design load @180 W |
|-------|------:|-------------------:|
| 4-node sled | 4 | ~720 W |
| 22-node subcluster | 22 | ~4.0 kW |

At 12 V, 22 nodes ≈ **330 A** — which is exactly why a single rack-wide 12 V bus
is the wrong answer.

### Prototype power (per sled)

- Shelf-local redundant CRPS / server PSUs: `2 × 1.2 kW` 80+ Platinum in 1+1,
  ideal-diode ORed, feeding a protected branch per board.
- Per-board branch: current-limited eFuse + fuse + telemetry, connector rated
  ≥ `20 A @ 12 V`.

### Fleet power (per rack)

- Redundant **48 V DC** rack distribution with a per-sled 48→12 V converter, so
  the high-current 12 V path is short local copper only.
- Dual mains feeds (e.g. 208/240 V), each able to carry the whole rack load.

### The PS3 power-on handshake (do not shortcut)

The PS3 PSU exposes a small control connector. Syscon asserts a ~3.3 V
`ACDC_STBY` enable to switch on the main 12 V rail, and reads `ACIN_DET` /
`5VSB` standby. In a recased sled you must:

- generate the board's 5/5.5 V standby locally;
- interface `ACDC_STBY` through proper logic / optocoupling or a MOSFET
  controller — **never** wire it directly to ATX `PS_ON`, and **never** use
  soldered hooks on the board's power posts;
- stagger per-board starts to bound inrush.

## Cooling budget

Budget **180 W/node** of heat until measured. At a 10 °C rack air rise, 22 nodes
need on the order of **~700 CFM** delivered through the heatsinks; design for
**35–45 CFM/node** after duct and heatsink impedance, with **N+1 fans** and tach
monitoring.

- Sealed cold-aisle intake, rear exhaust; no board may ingest another's plume.
- Retain Syscon thermal protection as a hard requirement — it is the last line
  if a fan or duct fails.
- Replace external thermal paste during refurb; **do not** delid Cell at fleet
  scale (high scrap rate for little gain).

## One-rack subcluster (maps to the 22-node group)

| U | Contents |
|---|----------|
| 6 × 4U | four-node compute sleds = 24 slots (22 active + 2 cold spares) |
| 3–4U | redundant power shelves (or 48 V shelf + per-sled converters) |
| 1U | 48-port 1GbE switch, dual 10/25GbE uplinks |
| 1U | subcluster/region head server |
| 1U | management / console server + shelf power controller |
| rest | duct transitions, service loops, spare power capacity |

At 150–180 W/node that rack is ~**3.5–4.2 kW IT**, suited to dual 208/240 V 30 A
feeds where each feed can carry the whole rack. Two subclusters per rack halves
the rack count but pushes cooling/power toward ~7–8 kW.

## Networking & management

- PS3 wired **Gigabit** NIC at MTU 1500 (no jumbo frames). Aggregate leaf
  traffic upstream via the head's 10/25GbE uplink. Compute and out-of-band
  management on separate VLANs.
- Out-of-band per-node control (independent of the OS): soft-button, hard rail
  cycling, current sensing, fan telemetry, inlet/exhaust temperature. WoL is a
  convenience, not the recovery path (a hung console won't answer it).

## Scale reality

One 22-node subcluster per rack ≈ one quarter of a K3 layer's experts is *not*
true — a K3 layer has ~896 experts, so a full layer is ~41 subclusters ≈ 41
racks. The whole 82,432-expert model is on the order of **~3,700 racks** and
**~11–15 MW** of PS3 compute before cooling and coordinators. The point of this
spec is to make the *per-rack* engineering sound so that number is at least
honest; the construction path is `4-node sled → 22-node rack → full layer →
multi-layer farm`, measuring watts, thermals, and failure rates at each gate.

## Sources

- CECHL hardware / OtherOS / power: https://www.psdevwiki.com/ps3/CECHLxx
- PS3 PSU rails, revision caveats: https://www.psdevwiki.com/ps3/Power_Supply
- PSU control connector (`ACDC_STBY`/`ACIN_DET`/`5VSB`):
  https://www.psdevwiki.com/ps3/Template:PS3_PSU_Control_connector_4_pins
- Syscon thermal control: https://www.psdevwiki.com/ps3/Thermal
- OtherOS Wake-on-LAN: https://lists.ozlabs.org/pipermail/linuxppc-dev/2008-March/053536.html
- Condor 22-PS3 grouping (IEEE HPEC 2012):
  https://ieee-hpec.org/2012/index_htm_files/Barnell.pdf
