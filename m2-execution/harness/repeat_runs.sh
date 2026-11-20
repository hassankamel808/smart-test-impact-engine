#!/usr/bin/env bash
# Usage: harness/repeat_runs.sh [prefix]   -> runs rep-1, rep-2, rep-3
set -euo pipefail
cd "$(dirname "$0")/.."
PREFIX="${1:-rep}"
for i in 1 2 3; do
  harness/run_suite.sh "${PREFIX}-${i}"
done
