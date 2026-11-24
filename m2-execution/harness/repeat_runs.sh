#!/usr/bin/env bash
# Usage: harness/repeat_runs.sh [prefix]  -> runs <prefix>-1..3, keeps every attempt.
set -uo pipefail
cd "$(dirname "$0")/.."
PREFIX="${1:-rep}"
WORST=0
for i in 1 2 3; do
  harness/run_suite.sh "${PREFIX}-${i}"
  CODE=$?
  if [ "$CODE" -gt "$WORST" ]; then WORST=$CODE; fi
done
exit "$WORST"