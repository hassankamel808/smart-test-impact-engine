#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker build -f docker/Dockerfile -t black-ref:0aa7ce6 .
docker inspect --format='{{.Id}}' black-ref:0aa7ce6 | tee docker/IMAGE_DIGEST.txt
