# Console qualification & burn-in checklist

Every donor PS3 passes this before it joins a production rack. The goal is to
catch marginal boards *before* they cause silent wrong answers or thermal events
in a 22-node subcluster. **Untested procedure** — adjust thresholds to what you
actually measure on your hardware.

## 1. Intake & inventory

- [ ] Record CECH model and mainboard revision (e.g. CECHL / VER-001).
- [ ] Record NIC MAC, assigned rack/slot, PDU + outlet.
- [ ] Add the console as one row in `examples/fleet_inventory.csv`
      (layer, expert, host, port, mac, rack, slot, pdu, pdu_outlet, cech).
- [ ] Confirm it is the chassis's standardized revision; quarantine odd ones.

## 2. Refurbishment

- [ ] Clean; replace external thermal paste (do **not** delid Cell).
- [ ] Verify heatsink/X-clamp seating and fan spins freely.
- [ ] Decide BD strategy: keep paired BD logic board, or qualify a noBD image
      (see `bringup/OTHEROS_CFW_NOTES.md`) — record which.

## 3. Electrical (recased sleds only)

- [ ] Confirm per-board eFuse/fuse and connector rating (≥ 20 A @ 12 V).
- [ ] Confirm local 5/5.5 V standby present.
- [ ] Confirm `ACDC_STBY` is driven through proper logic/optocoupling/MOSFET,
      **not** hardwired to ATX `PS_ON`.
- [ ] Confirm staggered start; measure inrush.

## 4. Boot & network

- [ ] Boots the standard OS image (local or NFS root) unattended.
- [ ] `ps3-expert@<layer>-<expert>` service comes up and listens.
- [ ] From a head server, `run_subcluster.py --check-members` PINGs this node OK.
- [ ] Wired GigE link up at MTU 1500; record negotiated speed.
- [ ] WoL wakes it from standby (`power/wol.py --dry-run` first, then live).
- [ ] OOB power cycle recovers it (`power/power_cycle.py`, narrowed to this node).

## 5. Compute correctness

- [ ] Serve this node's real packed `.exp` (not `--identity`).
- [ ] Run tokens through it and compare against the `ram-coffers` flat
      dispatcher / reference worker (`np.array_equal` in exact mode). A board
      that computes *different* bits is a reject, not a warning.

## 6. Burn-in (48–72 h)

Run the actual SPE/RSX expert kernel continuously and log:

- [ ] Cell/RSX temperatures and fan RPM (Syscon/thermal sensors).
- [ ] Rail current per board.
- [ ] Corrected/uncorrected network errors.
- [ ] Crash/restart count (systemd `Restart=on-failure` events).
- [ ] Any exact-mode output mismatch (must be zero).

## 7. Disposition

- [ ] Pass → mark ready, assign to a subcluster. Place expert **replicas in a
      different chassis/power domain** than their primary.
- [ ] Marginal → quarantine; do not repair inside a production rack.
- [ ] Keep ≥ 10% spare capacity per rack.
