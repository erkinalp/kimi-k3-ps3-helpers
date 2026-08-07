# Diskless / NFS-root image recipe

Design for booting a fleet of consoles from one immutable OS image so you manage
**one** root, not N disks. **Untested on hardware here** — validate on one
console before rolling out.

## Why

- One kernel + userland to patch, not one per console.
- A console is cattle: reimage by rebooting, not by servicing a disk.
- Per-console state (its `(layer, expert)`, its `.exp` file) is tiny and comes
  from the inventory, so the root can be read-only and shared.

## Shape

```
head/boot server
  ├─ read-only NFS export:  /srv/ps3root         (shared OS image)
  ├─ per-console overlay:   /srv/nodes/<node>/   (writable: /etc/ps3-expert.env)
  └─ expert files:          /srv/experts/L###-E####.exp
consoles (OtherOS/Linux)
  petitboot/kboot → kernel + initramfs → mount NFS root → tmpfs/overlay for /var
```

Because OtherOS RSX is cold and XDR is only 256 MB, keep the image lean: no
desktop, no optical stack, just kernel, libc, Python 3 (for the reference
worker) or the `expert_node_host` binary, and the `bringup/` service.

## Steps (outline)

1. **Build the shared root** on the boot server for the PPC target (Yellow Dog /
   Debian PPC lineage), install Python 3 or drop in the built worker binary, and
   install `bringup/ps3-expert@.service`.
2. **Export it read-only** over NFS to the compute VLAN only.
3. **Per-console identity from the inventory.** For each row, render a tiny
   overlay containing `/etc/ps3-expert.env` (its `EXPERT_PORT` and the layer/
   expert its instance name encodes) and symlink its `.exp` file. Generate these
   straight from `examples/fleet_inventory.csv` so the NFS layout and
   `cluster.json` never disagree.
4. **Point each console's bootloader** at the shared kernel + its overlay
   (petitboot config or kboot `root=/dev/nfs nfsroot=...`).
5. **Enable the instance** (`ps3-expert@<layer>-<expert>`) in the image so a
   booted console comes up already serving.

## Keep it consistent with the config

The same inventory drives `deploy/gen_fleet_config.py` (→ `cluster.json`) and the
per-node overlays here. If you change a console's host/port/placement, regenerate
both. A mismatch shows up as a head server whose `--check-members` PING fails for
that node.

## Networking

Compute NFS + P3XC traffic stays on a private VLAN at MTU 1500 (no jumbo
frames). Management/boot (DHCP/TFTP/NFS) and out-of-band power live on separate
VLANs. The P3XC worker does not authenticate, so network isolation is the
control — never expose a console port to an untrusted network.
