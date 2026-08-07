#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Install the expert-worker service on one console.
#
# Run on the PS3 (OtherOS / exploited Linux with systemd) after copying this
# repo and the worker binary to it. Idempotent: safe to re-run.
#
#   sudo bringup/install_console.sh 3 0      # this console serves L3 E0
#
# It installs the systemd template, writes /etc/ps3-expert.env from the example
# if absent, and enables the instance. It does NOT fabricate an .exp file or a
# binary; those come from your build/pack pipeline.
set -euo pipefail

LAYER="${1:?usage: install_console.sh <layer> <expert>}"
EXPERT="${2:?usage: install_console.sh <layer> <expert>}"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [[ $EUID -ne 0 ]]; then
    echo "run as root (systemd unit + /etc install)" >&2
    exit 1
fi

install -m 0644 "$HERE/ps3-expert@.service" \
    /etc/systemd/system/ps3-expert@.service

if [[ ! -f /etc/ps3-expert.env ]]; then
    install -m 0644 "$HERE/ps3-expert.env.example" /etc/ps3-expert.env
    echo "wrote /etc/ps3-expert.env from example -- EDIT IT before starting" >&2
fi

systemctl daemon-reload
systemctl enable "ps3-expert@${LAYER}-${EXPERT}.service"
echo "installed ps3-expert@${LAYER}-${EXPERT}.service" >&2
echo "edit /etc/ps3-expert.env, then: systemctl start ps3-expert@${LAYER}-${EXPERT}.service" >&2
