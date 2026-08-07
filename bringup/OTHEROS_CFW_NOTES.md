# OtherOS / CFW / noBD bring-up notes

Engineering notes for getting Linux onto a fleet of PS3s so each can run the
expert worker. **Untested in the environment that produced this file** — verify
on one console before touching a fleet. Nothing here bypasses copy protection or
runs unauthorized software; it is about booting Linux on hardware you own.

## Boot paths

Two routes reach a Linux userland that can run the P3XC worker:

1. **OtherOS (hypervisor).** The sanctioned route on early fat models. RSX is
   restricted (see the RSX notes in `ram-coffers`), 6 SPEs are usable, and the
   NIC, disk, and USB are available. Requires a fat PS3 kept on firmware that
   still has the OtherOS installer (≤ 3.15; **removed in 3.21**), and an
   `otheros.bld` payload on a FAT-formatted USB key under `/PS3/otheros/`.
2. **Exploited GameOS/Linux.** Later route giving full RSX and (with the right
   entry) a 7th SPE. Model/firmware dependent; out of scope to script here, but
   the worker and service files are identical once you have a shell.

Pick **one** motherboard revision per chassis so the power, fan, and firmware
interfaces are uniform. The recommended baseline is CECHL/P/Q-class fat boards:
65 nm Cell + 65 nm RSX, original OtherOS support, ~130 W nominal.

## Firmware and the Blu-ray logic board (noBD)

The console's paired **Blu-ray logic board** is a firmware dependency, not just
an optical drive. Stock retail firmware — and ordinary CFW built from it —
expects that board present and responsive. If it is missing or faulty, the
console may still reach a menu but updates can fail or loop (commonly
`8002F14E`) and apps can black-screen. Special **noBD** firmware variants patch
around that.

For a rack build, the conservative options are:

- **Keep the small paired BD logic board** (discard only the optical mechanics),
  so ordinary firmware is happy; or
- **Qualify one exact noBD firmware image** on the chosen motherboard revision
  *before* removing the board, and standardize that image fleet-wide.

Do **not** install ordinary OFW/HFW on a board already converted to a noBD
configuration — that can strand it in an update failure. Assume official
old-OtherOS firmware is BD-dependent unless you have tested it with the paired
controller absent.

## What the worker needs from the OS

- Wired Gigabit NIC up at MTU 1500 (do not depend on jumbo frames; the PS3 Linux
  driver historically capped frame size well below 9000).
- A Python 3 (for the reference worker) or the built `expert_node_host` binary.
- The systemd template in this directory, or an equivalent init script.
- A copy of this console's packed `L<layer>-E<expert>.exp` file, or a read-only
  NFS mount that provides it (see `deploy/DISKLESS_NFS_IMAGE.md`).

## Remote power

OtherOS gained **Wake-on-LAN** in firmware 2.20 (`ethtool -s eth0 wol g` before
shutdown; wake with an etherwake magic packet). Treat it as a convenience only;
a shelf controller must independently provide hard power cycling because a hung
console will not answer WoL. See `power/`.
