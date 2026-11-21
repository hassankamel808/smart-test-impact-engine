#!/usr/bin/env bash
# Builds black-ref:0aa7ce6 only from the pinned, clean checkout. Exit 76 = wrong checkout, 77 = image ID changed.
set -euo pipefail
cd "$(dirname "$0")/.."
PIN=0aa7ce6926f097d06e348edf89937d3f770b37f1
[ "$(git -C upstream/black rev-parse --verify HEAD)" = "$PIN" ] || { echo "upstream/black is not at $PIN" >&2; exit 76; }
[ -z "$(git -C upstream/black status --porcelain)" ] || { echo "upstream/black has local changes" >&2; exit 76; }
docker build -f docker/Dockerfile -t black-ref:0aa7ce6 .
NEW=$(docker inspect --format='{{.Id}}' black-ref:0aa7ce6)
if [ -s docker/IMAGE_DIGEST.txt ] && [ "$(tr -d '\r\n ' < docker/IMAGE_DIGEST.txt)" != "$NEW" ]; then
  echo "$NEW" > docker/IMAGE_DIGEST.new
  echo "WARNING: rebuilt image ID differs from the recorded one. Recorded ID kept; new ID saved in docker/IMAGE_DIGEST.new. Treat it as a new environment." >&2
  exit 77
fi
echo "$NEW" | tee docker/IMAGE_DIGEST.txt