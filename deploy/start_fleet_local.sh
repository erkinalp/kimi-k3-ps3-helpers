#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Bring a whole farm up on ONE host, for testing without hardware.
#
# Starts a reference (numpy) expert worker per console, one head server per
# subcluster, and one coordinator per region, all from cluster.json. This is the
# loopback rehearsal of what the bringup/ service + start_subcluster.sh /
# start_region.sh do across real consoles and head servers.
#
#   RAM_COFFERS=/opt/ram-coffers/ps3-cluster \
#     deploy/start_fleet_local.sh cluster.json [--identity]
#
# --identity serves trivial identity experts (no .exp files needed), enough to
# exercise the hierarchy and PING/PONG. For real expert math, drop packed .exp
# files next to each console and remove --identity (see comments below).
#
# Ctrl-C tears the whole farm down.
set -euo pipefail

: "${RAM_COFFERS:?set RAM_COFFERS to a ram-coffers/ps3-cluster checkout}"
CONFIG="${1:?usage: start_fleet_local.sh cluster.json [--identity]}"
IDENTITY="${2:-}"

PIDS=()
cleanup() {
    echo "stopping fleet..." >&2
    for pid in "${PIDS[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Consoles, then heads, then regions. Readiness is the caller's concern: use
# run_layer.py --ping (or run_subcluster.py --check-members) before dispatching.
mapfile -t SPEC < <(python3 - "$CONFIG" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
for sc in cfg["subclusters"]:
    for m in sc["members"]:
        print("expert", m["host"], m["port"], m["layer"], m["expert"])
    print("head", sc["id"])
for rg in cfg.get("regions", []):
    print("region", rg["id"])
PY
)

for line in "${SPEC[@]}"; do
    # shellcheck disable=SC2086
    set -- $line
    case "$1" in
    expert)
        host="$2"; port="$3"; layer="$4"; expert="$5"
        if [[ "$IDENTITY" == "--identity" ]]; then
            python3 "$RAM_COFFERS/tools/run_expert.py" --identity \
                --layer "$layer" --expert "$expert" \
                --host "$host" --port "$port" &
        else
            # Expects an .exp file named L<layer>-E<expert>.exp in $PWD;
            # generate with $RAM_COFFERS/tools/pack_expert.py.
            python3 "$RAM_COFFERS/tools/run_expert.py" \
                "L${layer}-E${expert}.exp" --host "$host" --port "$port" &
        fi
        PIDS+=("$!") ;;
    head)
        RAM_COFFERS="$RAM_COFFERS" "$(dirname "$0")/start_subcluster.sh" \
            "$CONFIG" "$2" &
        PIDS+=("$!") ;;
    region)
        RAM_COFFERS="$RAM_COFFERS" "$(dirname "$0")/start_region.sh" \
            "$CONFIG" "$2" &
        PIDS+=("$!") ;;
    esac
done

echo "fleet up (${#PIDS[@]} processes). Ctrl-C to stop." >&2
echo "check readiness: python3 $RAM_COFFERS/tools/run_layer.py --config $CONFIG --ping" >&2
wait
