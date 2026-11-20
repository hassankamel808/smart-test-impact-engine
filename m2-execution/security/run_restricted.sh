#!/usr/bin/env bash
# Usage: security/run_restricted.sh <out_dir> <command...>
# Runs the pinned image with the restriction set from the threat model.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:?usage: run_restricted.sh <out_dir> <command...>}"; shift
mkdir -p "$OUT"
MSYS_NO_PATHCONV=1 docker run --rm \
  --user 10001:10001 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --network none \
  --memory 2g --memory-swap 2g \
  --cpus 2 \
  --pids-limit 512 \
  --read-only \
  --tmpfs /tmp:rw,size=256m \
  -v "$PWD/$OUT:/out" \
  black-ref:0aa7ce6 "$@"
