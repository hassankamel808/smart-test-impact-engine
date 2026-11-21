#!/usr/bin/env bash
# Usage: harness/run_suite.sh <run_id>
# Runs the suite through security/run_restricted.sh.
# Exit code = pytest's exit code, after the metadata is saved.
# Pre-flight failure codes (outside pytest's 1-5): 71 no digest file, 72 image mismatch,
# 73 run folder exists, 74 invalid run_id.
set -euo pipefail
cd "$(dirname "$0")/.."
RUN_ID="${1:?usage: run_suite.sh <run_id>}"
if ! [[ "$RUN_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || [[ "$RUN_ID" == *..* ]]; then
  echo "run_id must use only letters, digits, '.', '_' or '-' and start with a letter or digit" >&2; exit 74
fi
IMAGE_TAG="black-ref:0aa7ce6"
COMMIT_SHA="0aa7ce6926f097d06e348edf89937d3f770b37f1"
OUT="runs/${RUN_ID}"

[ -s docker/IMAGE_DIGEST.txt ] || { echo "missing docker/IMAGE_DIGEST.txt" >&2; exit 71; }
EXPECTED_ID=$(tr -d '\r\n ' < docker/IMAGE_DIGEST.txt)
ACTUAL_ID=$(docker image inspect --format='{{.Id}}' "$IMAGE_TAG" 2>/dev/null || true)
if [ "$ACTUAL_ID" != "$EXPECTED_ID" ]; then
  echo "IMAGE MISMATCH: expected '$EXPECTED_ID' but $IMAGE_TAG is '$ACTUAL_ID'. Not running." >&2
  exit 72
fi
if [ -e "$OUT" ]; then
  echo "Run folder $OUT already exists. Refusing to overwrite; use a new run id." >&2
  exit 73
fi
mkdir -p "$OUT"

DOCKER_CLIENT=$(docker version --format '{{.Client.Version}}' 2>/dev/null || echo unknown)
DOCKER_SERVER=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo unknown)
DOCKER_PLATFORM=$(docker info --format '{{.OperatingSystem}} {{.OSType}}/{{.Architecture}}' 2>/dev/null || echo unknown)
HOST_PLATFORM="$(uname -srm) | OS=${OS:-n/a}"
RESTRICTIONS="uid 10001, cap-drop ALL, no-new-privileges, network none, memory 2g, cpus 2, pids 512, read-only root, tmpfs /tmp 256m, pull never"

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
set +e
security/run_restricted.sh "$OUT" \
  pytest -p no:cacheprovider --junitxml=/out/junit.xml -q \
  > "$OUT/pytest_stdout.log" 2>&1
EXIT=$?
set -e
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)

PY=$(command -v python || command -v python3)
export RUN_ID COMMIT_SHA IMAGE_TAG ACTUAL_ID EXPECTED_ID START END EXIT \
       DOCKER_CLIENT DOCKER_SERVER DOCKER_PLATFORM HOST_PLATFORM RESTRICTIONS
"$PY" - <<'PYEOF' > "$OUT/meta.json"
import json, os
e = os.environ
print(json.dumps({
    "meta_version": 3,
    "run_id": e["RUN_ID"],
    "commit_sha": e["COMMIT_SHA"],
    "image_tag": e["IMAGE_TAG"],
    "image_id": e["ACTUAL_ID"],
    "expected_image_id": e["EXPECTED_ID"],
    "started_at": e["START"],
    "finished_at": e["END"],
    "pytest_exit_code": int(e["EXIT"]),
    "pytest_command": "pytest -p no:cacheprovider --junitxml=/out/junit.xml -q",
    "execution_mode": "restricted",
    "runner": "security/run_restricted.sh",
    "restrictions": e["RESTRICTIONS"],
    "docker_client_version": e["DOCKER_CLIENT"],
    "docker_server_version": e["DOCKER_SERVER"],
    "docker_server_platform": e["DOCKER_PLATFORM"],
    "host_platform": e["HOST_PLATFORM"],
}, indent=1))
PYEOF

echo "${RUN_ID}: pytest exit=${EXIT} (log: $OUT/pytest_stdout.log)"
exit "$EXIT"