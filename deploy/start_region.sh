#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Start one regional (head-of-heads) coordinator on this deployment host.
#
# Thin wrapper around ram-coffers' tools/run_region.py. Set RAM_COFFERS to a
# checkout of ram-coffers/ps3-cluster.
#
#   RAM_COFFERS=/opt/ram-coffers/ps3-cluster \
#     deploy/start_region.sh cluster.json rg-0000 [extra run_region args]
set -euo pipefail

: "${RAM_COFFERS:?set RAM_COFFERS to a ram-coffers/ps3-cluster checkout}"
CONFIG="${1:?usage: start_region.sh cluster.json rg-id [args...]}"
REGION="${2:?usage: start_region.sh cluster.json rg-id [args...]}"
shift 2

exec python3 "$RAM_COFFERS/tools/run_region.py" \
    --config "$CONFIG" --region "$REGION" "$@"
