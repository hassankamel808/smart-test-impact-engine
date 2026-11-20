#!/usr/bin/env bash
# Usage: harness/run_suite.sh <run_id>
set -euo pipefail
cd "$(dirname "$0")/.."
RUN_ID="${1:?usage: run_suite.sh <run_id>}"
OUT="runs/${RUN_ID}"
mkdir -p "$OUT"
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
set +e
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$PWD/$OUT:/out" \
  black-ref:0aa7ce6 \
  pytest -p no:cacheprovider --junitxml=/out/junit.xml -q \
  > "$OUT/pytest_stdout.log" 2>&1
EXIT=$?
set -e
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
IMAGE_ID=$(docker image inspect --format='{{.Id}}' black-ref:0aa7ce6)
cat > "$OUT/meta.json" <<JSON
{"run_id":"${RUN_ID}","commit_sha":"0aa7ce6926f097d06e348edf89937d3f770b37f1",
 "image_id":"${IMAGE_ID}","started_at":"${START}","finished_at":"${END}",
 "pytest_exit_code":${EXIT}}
JSON
echo "${RUN_ID}: exit=${EXIT} (log: $OUT/pytest_stdout.log)"
