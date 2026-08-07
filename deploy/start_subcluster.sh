#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Start one subcluster (head) server on this deployment host.
#
# Thin wrapper around ram-coffers' tools/run_subcluster.py so a farm's head
# servers all launch identically from the same cluster.json. Set RAM_COFFERS to
# a checkout of ram-coffers/ps3-cluster.
#
#   RAM_COFFERS=/opt/ram-coffers/ps3-cluster \
#     deploy/start_subcluster.sh cluster.json sc-0000 [extra run_subcluster args]
set -euo pipefail

: "${RAM_COFFERS:?set RAM_COFFERS to a ram-coffers/ps3-cluster checkout}"
CONFIG="${1:?usage: start_subcluster.sh cluster.json sc-id [args...]}"
SUBCLUSTER="${2:?usage: start_subcluster.sh cluster.json sc-id [args...]}"
shift 2

exec python3 "$RAM_COFFERS/tools/run_subcluster.py" \
    --config "$CONFIG" --subcluster "$SUBCLUSTER" "$@"
