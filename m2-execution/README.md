# M2 Execution (Member 2)

Pinned, reproducible execution of the psf/black test suite, with per-test attempt records.

Target: psf/black @ `0aa7ce6926f097d06e348edf89937d3f770b37f1`, Python 3.12, pytest 9.2.0, serial, black's own config.
Image: `black-ref:0aa7ce6`, ID `sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef` (recorded in `docker/IMAGE_DIGEST.txt`).
Base image: `python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`.

**Other members: do not rebuild the image.** An independent rebuild gives a different image ID. Load the exact image from the archive instead; see [`docker/IMAGE_ARCHIVE.md`](docker/IMAGE_ARCHIVE.md) (SHA-256 checksum, layer fingerprint, load and verify commands).

## Layout

| Path | Content |
|---|---|
| `docker/` | Dockerfile, hash-locked dependency files, build script, image ID, `IMAGE_ARCHIVE.md`, archive checksum |
| `harness/` | run, repeat, JUnit-to-records converter, reconciliation, comparison, duration export, negative-path tests |
| `security/` | restricted runner, hostile probe, threat model, `evidence/` (probe results) |
| `artifacts/inventory/expected_tests.txt` | the 796 collected test IDs |
| `artifacts/run-NNN/` | one run each: `attempt_records.jsonl` (schema 1.0.0), `meta.json`, `junit.xml`, and `pytest_stdout.log` where stored |
| `artifacts/reconciliation_*.md/.json` | JUnit vs inventory vs records, per run set |
| `artifacts/repeated_runs_log*.md` | cross-run comparison and validation, per run set |
| `artifacts/negative_tests_*.md` | results of the negative-path tests (WSL and Git Bash) |
| `artifacts/duration_trace.csv` | per-test durations of run-001..003, mean and max |

## Runs

| Folders | Run ids | Execution | Metadata |
|---|---|---|---|
| `run-001..003` | `rep-1..3` | **unrestricted** docker run (baseline, never edited) | basic |
| `run-004..006` | `v2-1..3` | **unrestricted**, image ID check, Docker and host metadata | `meta_version` 2 |
| `run-007..009` | `v3-1..3` | **restricted** (`security/run_restricted.sh`) | `meta_version` 3 |

All nine runs: 793 passed, 3 skipped (1 Windows-only, 2 `no_jupyter`), 0 failed, 0 missing, 796 records, identical outcomes, 0 tests differing. `artifacts/reconciliation_all_runs_strict.md` reconciles all nine runs against the inventory (CLEAN).
The JUnit suite attribute says 857 tests: 796 `<testcase>` elements plus 61 subtests. Subtests have no testcase element, are recorded only as counts in the reconciliation reports, and are not extra node IDs.

## Reproduce (from `m2-execution/`, in WSL or Linux; Git Bash also works but cannot test symlinks)

Use a new run prefix and new report file names. Never reuse an existing run folder or overwrite the baseline reports.

```bash
# 1. Get the exact image: load the archive (preferred) ...
sha256sum -c docker/black-ref-0aa7ce6.tar.gz.sha256      # run next to the downloaded archive
docker load -i black-ref-0aa7ce6.tar.gz
docker image inspect black-ref:0aa7ce6 --format '{{.Id}}'     # must equal docker/IMAGE_DIGEST.txt

# ... or rebuild (only to audit the Dockerfile; the image ID will probably differ)
mkdir -p upstream && git clone https://github.com/psf/black.git upstream/black
git -C upstream/black checkout 0aa7ce6926f097d06e348edf89937d3f770b37f1
./docker/build.sh

# 2. Three restricted runs, records, checks
harness/repeat_runs.sh rerun                      # runs/rerun-1..3 (git-ignored)
for i in 1 2 3; do python3 harness/junit_to_records.py runs/rerun-$i $i; done
python3 harness/reconcile_run.py artifacts/inventory/expected_tests.txt artifacts/reconciliation_rerun.md runs/rerun-1 runs/rerun-2 runs/rerun-3
python3 harness/compare_runs.py artifacts/repeated_runs_log_rerun.md runs/rerun-1 runs/rerun-2 runs/rerun-3
python3 harness/export_durations.py artifacts/duration_trace_rerun.csv runs/rerun-1 runs/rerun-2 runs/rerun-3

# 3. Negative-path tests (use a new report name; needs a Black clone at the pinned commit)
BLACK_SRC=upstream/black bash harness/test_negative_paths.sh wsl artifacts/negative_tests_rerun.md
```

`build.sh` builds under a temporary tag and moves `black-ref:0aa7ce6` only if the new image ID equals the recorded one. Otherwise it exits with 77, keeps the recorded ID, and writes the new ID to `docker/IMAGE_DIGEST.new`. Treat that as a new environment.

## Exit codes

| Script | Code | Meaning |
|---|---|---|
| `run_suite.sh` | 0 to 5 | pytest's own exit code, saved in `meta.json` and then returned |
| `run_suite.sh`, `run_restricted.sh` | 71 | `docker/IMAGE_DIGEST.txt` missing |
| | 72 | image tag does not match the recorded image ID |
| `run_suite.sh` | 73 | run folder already exists (never overwritten) |
| `run_suite.sh` | 74 | invalid run id |
| `run_suite.sh`, `run_restricted.sh` | 75 | unsafe output directory, or `runs/` is a symlink |
| `build.sh` | 76 | wrong or dirty Black checkout |
| `build.sh` | 77 | rebuilt image ID differs from the recorded one |
| `reconcile_run.py` | 0 | clean: records exactly match the inventory, same IDs in every run |
| | 1 | not clean: missing, duplicate or unmatched JUnit cases, or record problems |
| `compare_runs.py` | 0 | all validations pass |
| | 1 | at least one validation failed |
| `test_negative_paths.sh` | 0 / 1 | no case failed / at least one case failed (skipped cases are listed) |

## Security

Restricted runs use uid 10001, `--cap-drop ALL`, `no-new-privileges`, `--network none`, memory 2 GB, 2 CPUs, 512 PIDs, read-only root, 256 MB `/tmp`, `--pull=never`. The runner checks the image ID before starting and accepts only `runs/<name>` as output directory. See `security/threat_model.md`.
The resource-limit stress test is **PENDING**. The writable `/out` mount is a documented residual risk.

## Limitations

- Three repeats cannot detect rare flakiness.
- Docker Desktop runs containers in a Linux VM, so the controls protect the VM, not directly the Windows host.
- `run-001..006` ran without the restriction set; only `run-007..009` ran under it. The outcomes were identical.
- The image archive was load-tested on the machine that built it. A teammate's load is the independent check. A Docker setup with a different image store may report another image ID for identical layers; compare the layer fingerprint in `docker/IMAGE_ARCHIVE.md`.
- Negative-path tests: the symlink cases need Linux or WSL (Git Bash cannot create real symlinks). The `build.sh` rebuild path that ends in exit 77 was not exercised.
- Serial execution only; no coverage data (Member 4).
- This harness measures reliability only. It makes no claim about test selection performance.