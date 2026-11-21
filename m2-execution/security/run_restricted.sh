#!/usr/bin/env bash
# Usage: security/run_restricted.sh runs/<name> <command...>
# Exit codes (outside pytest's 1-5): 71 no digest file, 72 image mismatch, 75 unsafe output dir.
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE_TAG="black-ref:0aa7ce6"
OUT="${1:?usage: run_restricted.sh runs/<name> <command...>}"; shift

# Output dir: exactly runs/<name>, no traversal, no symlinks, resolved path must be directly under runs/
if ! [[ "$OUT" =~ ^runs/[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || [[ "$OUT" == *..* ]]; then
  echo "output dir must be runs/<name> (letters, digits, '.', '_', '-')" >&2; exit 75
fi
mkdir -p runs
[ ! -L runs ] || { echo "runs/ must not be a symlink" >&2; exit 75; }
mkdir -p "$OUT"
[ ! -L "$OUT" ] || { echo "$OUT must not be a symlink" >&2; exit 75; }
ROOT=$(cd runs && pwd -P); REAL=$(cd "$OUT" && pwd -P)
[ "$(dirname "$REAL")" = "$ROOT" ] || { echo "$OUT resolves outside runs/" >&2; exit 75; }

# Image: the tag must still point at the recorded image ID, and Docker must never pull
[ -s docker/IMAGE_DIGEST.txt ] || { echo "missing docker/IMAGE_DIGEST.txt" >&2; exit 71; }
EXPECTED_ID=$(tr -d '\r\n ' < docker/IMAGE_DIGEST.txt)
ACTUAL_ID=$(docker image inspect --format='{{.Id}}' "$IMAGE_TAG" 2>/dev/null || true)
if [ "$ACTUAL_ID" != "$EXPECTED_ID" ]; then
  echo "IMAGE MISMATCH: expected '$EXPECTED_ID' but $IMAGE_TAG is '$ACTUAL_ID'. Not running." >&2
  exit 72
fi

MSYS_NO_PATHCONV=1 docker run --rm --pull=never \
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
  "$IMAGE_TAG" "$@"