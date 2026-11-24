#!/usr/bin/env bash
# Builds the image from the pinned, clean Black checkout.
# Exit 76 = wrong or dirty checkout. Exit 77 = rebuilt image differs from the recorded one.
# The tag black-ref:0aa7ce6 is moved only if the new ID equals the recorded ID (or none is recorded yet).
set -euo pipefail
cd "$(dirname "$0")/.."
PIN=0aa7ce6926f097d06e348edf89937d3f770b37f1
[ "$(git -C upstream/black rev-parse --verify HEAD)" = "$PIN" ] || { echo "upstream/black is not at $PIN" >&2; exit 76; }
[ -z "$(git -C upstream/black status --porcelain)" ] || { echo "upstream/black has local changes" >&2; exit 76; }
docker build -f docker/Dockerfile -t black-ref:candidate .
NEW=$(docker inspect --format='{{.Id}}' black-ref:candidate)
if [ -s docker/IMAGE_DIGEST.txt ]; then
  OLD=$(tr -d '\r\n ' < docker/IMAGE_DIGEST.txt)
  if [ "$NEW" != "$OLD" ]; then
    echo "$NEW" > docker/IMAGE_DIGEST.new
    echo "WARNING: rebuilt image ID $NEW differs from the recorded $OLD." >&2
    echo "The tag black-ref:0aa7ce6 was NOT moved. Treat the rebuild as a new environment, or load the archive (docker/IMAGE_ARCHIVE.md)." >&2
    exit 77
  fi
else
  echo "$NEW" > docker/IMAGE_DIGEST.txt
fi
docker tag black-ref:candidate black-ref:0aa7ce6
echo "$NEW"