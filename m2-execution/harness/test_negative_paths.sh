#!/usr/bin/env bash
# Negative-path tests for the M2 harness.
# Usage: harness/test_negative_paths.sh <label> [report.md]     label: wsl | linux | gitbash
# Env:   SB_PARENT  where to create the sandbox (Git Bash: use "$PWD" so Docker can mount it)
#        BLACK_SRC  existing Black clone at the pinned commit (default: upstream/black)
# Runs against a throw-away COPY of the scripts. Real runs/, artifacts/run-*, docker/IMAGE_DIGEST.txt
# and upstream/ are never modified. Docker is shimmed; only the control at the end starts a container.
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
LABEL="${1:?usage: test_negative_paths.sh <label: wsl|linux|gitbash> [report.md]}"
REPORT="${2:-artifacts/negative_tests_${LABEL}.md}"
if [ -e "$REPORT" ]; then echo "$REPORT already exists; not overwriting" >&2; exit 1; fi
PIN=0aa7ce6926f097d06e348edf89937d3f770b37f1
IMAGE_TAG="black-ref:0aa7ce6"

PY=""
for p in python3 python; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import sys" >/dev/null 2>&1; then PY=$(command -v "$p"); break; fi
done
REAL_DOCKER=$(command -v docker || true)

SB=$(mktemp -d -p "${SB_PARENT:-${TMPDIR:-/tmp}}" negtest.XXXXXX) || exit 1
trap 'rm -rf "$SB" 2>/dev/null || true' EXIT
mkdir -p "$SB"/harness "$SB"/security "$SB"/docker "$SB"/bin "$SB"/elsewhere "$SB"/rc "$SB"/artifacts/inventory
{ cp harness/run_suite.sh harness/reconcile_run.py harness/junit_to_records.py "$SB/harness/" \
  && cp security/run_restricted.sh "$SB/security/" \
  && cp docker/build.sh docker/IMAGE_DIGEST.txt "$SB/docker/" \
  && cp artifacts/inventory/expected_tests.txt "$SB/artifacts/inventory/"; } \
  || { echo "sandbox setup failed" >&2; exit 1; }
sed -i 's/\r$//' "$SB"/harness/* "$SB"/security/* "$SB"/docker/build.sh "$SB"/docker/IMAGE_DIGEST.txt
chmod +x "$SB"/harness/*.sh "$SB"/security/*.sh "$SB"/docker/build.sh

export REAL_DOCKER SHIM_LOG="$SB/shim.log"
: > "$SHIM_LOG"
cat > "$SB/bin/docker" <<'SHIM'
#!/usr/bin/env bash
case "${1:-}" in
  image|version|info)
    if [ -n "${REAL_DOCKER:-}" ]; then exec "$REAL_DOCKER" "$@"; fi
    exit 127 ;;
  *)
    echo "BLOCKED: docker $*" >> "$SHIM_LOG"
    exit 99 ;;
esac
SHIM
chmod +x "$SB/bin/docker"

PASS=0; FAIL=0; SKIP=0; ROWS=""
record() {
  local d; d=$(printf '%s' "$3" | tr '|' '/')
  ROWS="${ROWS}| $1 | $2 | $d |"$'\n'
  case "$2" in PASS) PASS=$((PASS+1));; FAIL) FAIL=$((FAIL+1));; *) SKIP=$((SKIP+1));; esac
  printf '%-5s %s: %s\n' "$2" "$1" "$d"
}
in_sb()      { ( cd "$SB" && PATH="$SB/bin:$PATH" "$@" ); }
in_sb_real() { ( cd "$SB" && "$@" ); }
expect_exit() {
  local name="$1" want="$2" out code
  shift 2
  out=$("$@" 2>&1); code=$?
  if [ "$code" = "$want" ]; then record "$name" PASS "exit $code"
  else record "$name" FAIL "exit $code, expected $want: $(printf '%s' "$out" | tail -n 1)"; fi
}
check_shim() {
  if grep -q BLOCKED "$SHIM_LOG" 2>/dev/null; then record "$1" FAIL "$(head -n 1 "$SHIM_LOG")"
  else record "$1" PASS "no docker build/run was attempted"; fi
  : > "$SHIM_LOG"
}

# ---------- A: reconcile_run.py ----------
mutate() {
  "$PY" - "$1" "$2" <<'PYEOF'
import re, sys, pathlib
mode, d = sys.argv[1], sys.argv[2]
p = pathlib.Path(d) / "junit.xml"
s = p.read_text(encoding="utf-8")
m = re.search(r'<testcase [^>]*?(/>|>.*?</testcase>)', s, flags=re.S)
if mode == "truncate":
    s = s[:m.start()] + s[m.end():]
elif mode == "duplicate":
    s = s[:m.end()] + m.group(0) + s[m.end():]
elif mode == "unmatched":
    s = s.replace("</testsuite>", '<testcase classname="tests.fake" name="test_fake" time="0.001"/></testsuite>', 1)
p.write_text(s, encoding="utf-8")
PYEOF
}
if [ -n "$PY" ] && [ -f artifacts/run-004/junit.xml ]; then
  for c in ok truncate duplicate unmatched; do cp -r artifacts/run-004 "$SB/rc/$c"; done
  mutate truncate "$SB/rc/truncate"; mutate duplicate "$SB/rc/duplicate"; mutate unmatched "$SB/rc/unmatched"
  rec() { in_sb "$PY" harness/reconcile_run.py artifacts/inventory/expected_tests.txt "rc/$1.md" "rc/$1"; }
  expect_exit "reconcile: unmodified run (control)" 0 rec ok
  expect_exit "reconcile: JUnit case missing" 1 rec truncate
  expect_exit "reconcile: duplicate JUnit test ID" 1 rec duplicate
  expect_exit "reconcile: unmatched JUnit case" 1 rec unmatched
else
  record "reconcile cases (4)" SKIP "python or artifacts/run-004 not available"
fi

# ---------- B: path validation ----------
expect_exit "run_suite: run_id with traversal (../escape)" 74 in_sb harness/run_suite.sh ../escape
expect_exit "run_restricted: output dir with traversal (../../escape)" 75 in_sb security/run_restricted.sh ../../escape true
expect_exit "run_restricted: absolute output dir (/tmp/x)" 75 in_sb security/run_restricted.sh /tmp/x true
if [ -e "$(dirname "$SB")/escape" ]; then record "nothing created outside the sandbox" FAIL "escape exists"
else record "nothing created outside the sandbox" PASS "no escape directory"; fi

# ---------- C: symlinks ----------
ln -s "$SB/elsewhere" "$SB/_symtest" 2>/dev/null
if [ -L "$SB/_symtest" ]; then CAN_SYM=1; else CAN_SYM=0; fi
rm -rf "$SB/_symtest"
if [ "$CAN_SYM" = 1 ]; then
  rm -rf "$SB/runs"; ln -s "$SB/elsewhere" "$SB/runs"
  expect_exit "run_suite: runs/ is a symlink" 75 in_sb harness/run_suite.sh sym-1
  expect_exit "run_restricted: runs/ is a symlink" 75 in_sb security/run_restricted.sh runs/sym-1 true
  if [ -z "$(ls -A "$SB/elsewhere")" ]; then record "symlink target untouched (runs/)" PASS "nothing created behind the link"
  else record "symlink target untouched (runs/)" FAIL "$(ls -A "$SB/elsewhere" | head -n 1)"; fi
  rm -rf "$SB/runs"; mkdir -p "$SB/runs"; ln -s "$SB/elsewhere" "$SB/runs/linkdir"
  expect_exit "run_restricted: output dir is a symlink" 75 in_sb security/run_restricted.sh runs/linkdir true
  if [ -z "$(ls -A "$SB/elsewhere")" ]; then record "symlink target untouched (output dir)" PASS "nothing created behind the link"
  else record "symlink target untouched (output dir)" FAIL "$(ls -A "$SB/elsewhere" | head -n 1)"; fi
  rm -rf "$SB/runs"
else
  record "symlinked runs/ and output dir (5 checks)" SKIP "this shell cannot create real symlinks; run in Linux/WSL"
fi

# ---------- D: build.sh ----------
expect_exit "build.sh: upstream/black missing" 76 in_sb docker/build.sh
BLACK_SRC="${BLACK_SRC:-$ROOT/upstream/black}"
CLONE_OK=0
if [ -e "$BLACK_SRC/.git" ] && [ "$(git -C "$BLACK_SRC" rev-parse HEAD 2>/dev/null)" = "$PIN" ]; then
  mkdir -p "$SB/upstream"
  if git clone -q --no-hardlinks "$BLACK_SRC" "$SB/upstream/black" 2>/dev/null \
     && git -C "$SB/upstream/black" checkout -q --detach "$PIN" 2>/dev/null; then CLONE_OK=1; fi
fi
if [ "$CLONE_OK" = 1 ]; then
  B="$SB/upstream/black"
  if git -C "$B" checkout -q --detach "${PIN}~1" 2>/dev/null; then
    expect_exit "build.sh: wrong Black commit (parent of the pin)" 76 in_sb docker/build.sh
  else
    record "build.sh: wrong Black commit" SKIP "could not check out the parent commit"
  fi
  git -C "$B" checkout -q --detach "$PIN"
  echo "dirty" >> "$B/README.md"
  expect_exit "build.sh: dirty checkout (modified tracked file)" 76 in_sb docker/build.sh
  git -C "$B" checkout -q -- README.md
  : > "$B/_untracked_test_file"
  expect_exit "build.sh: dirty checkout (untracked file)" 76 in_sb docker/build.sh
  rm -f "$B/_untracked_test_file"
  check_shim "build.sh negative cases never reached docker build"
  expect_exit "build.sh: clean pinned checkout reaches docker build (control; shim blocks the build)" 99 in_sb docker/build.sh
  : > "$SHIM_LOG"
else
  record "build.sh: wrong commit, dirty (2 cases), control" SKIP "no Black clone at the pinned commit (set BLACK_SRC or clone upstream/black)"
  check_shim "build.sh missing-checkout case never reached docker build"
fi

# ---------- E: image digest, existing run folder, positive control ----------
HAVE_IMAGE=0; ID_NOW=""
if [ -n "$REAL_DOCKER" ]; then
  ID_NOW=$("$REAL_DOCKER" image inspect --format='{{.Id}}' "$IMAGE_TAG" 2>/dev/null || true)
  REC_ID=$(tr -d '\r\n ' < docker/IMAGE_DIGEST.txt 2>/dev/null || true)
  if [ -n "$ID_NOW" ] && [ "$ID_NOW" = "$REC_ID" ]; then HAVE_IMAGE=1; fi
fi
if [ "$HAVE_IMAGE" = 1 ]; then
  rm -rf "$SB/runs"; mkdir -p "$SB/runs"
  cp "$SB/docker/IMAGE_DIGEST.txt" "$SB/good_digest"
  echo "sha256:0000000000000000000000000000000000000000000000000000000000000000" > "$SB/docker/IMAGE_DIGEST.txt"
  expect_exit "run_restricted: image digest mismatch" 72 in_sb security/run_restricted.sh runs/mm-1 true
  expect_exit "run_suite: image digest mismatch" 72 in_sb harness/run_suite.sh mm-2
  cp "$SB/good_digest" "$SB/docker/IMAGE_DIGEST.txt"
  mkdir -p "$SB/runs/exists-1"
  expect_exit "run_suite: existing run folder" 73 in_sb harness/run_suite.sh exists-1
  check_shim "digest and existing-folder cases never started a container"
  expect_exit "control: matching digest starts the restricted container (runs 'true')" 0 in_sb_real security/run_restricted.sh runs/ctl-1 true
  ID_AFTER=$("$REAL_DOCKER" image inspect --format='{{.Id}}' "$IMAGE_TAG" 2>/dev/null || true)
  if [ "$ID_AFTER" = "$ID_NOW" ]; then record "image ID unchanged by the tests" PASS "$ID_NOW"
  else record "image ID unchanged by the tests" FAIL "before $ID_NOW, after $ID_AFTER"; fi
else
  record "digest mismatch (2), existing run folder, control" SKIP "docker or the recorded image ID is not available in this shell"
fi

{
  echo "# Negative-path tests ($LABEL)"
  echo
  echo "- Date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- Host: $(uname -srm) (WSL distro: ${WSL_DISTRO_NAME:-none})"
  echo "- Docker server: $( [ -n "$REAL_DOCKER" ] && "$REAL_DOCKER" version --format '{{.Server.Version}}' 2>/dev/null || echo n/a )"
  echo "- Git: $(git --version)"
  echo "- Real symlinks available: $( [ "$CAN_SYM" = 1 ] && echo yes || echo no )"
  echo "- Sandbox copy of the scripts was used and deleted afterwards; real runs/, artifacts/run-*, docker/IMAGE_DIGEST.txt untouched."
  echo
  echo "| Case | Result | Detail |"
  echo "|---|---|---|"
  printf '%s' "$ROWS"
  echo
  echo "Summary: $PASS passed, $FAIL failed, $SKIP skipped"
} > "$REPORT"
echo
echo "Summary: $PASS passed, $FAIL failed, $SKIP skipped  (report: $REPORT)"
exit $(( FAIL > 0 ? 1 : 0 ))