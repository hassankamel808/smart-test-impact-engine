# M2 Execution (Member 2)

Pinned, reproducible execution of the psf/black test suite, with per-test attempt records.

Target: psf/black @ `0aa7ce6926f097d06e348edf89937d3f770b37f1`, Python 3.12, pytest 9.2.0, serial, black's own config.
Image: `black-ref:0aa7ce6`, ID `sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef` (recorded in `docker/IMAGE_DIGEST.txt`).
Base image: `python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`.

## Layout

| Path | Content |
|---|---|
| `docker/` | Dockerfile, hash-locked dependency files, build script, image ID |
| `harness/` | run, repeat, JUnit-to-records converter, reconciliation, comparison, duration export |
| `security/` | restricted runner, hostile probe, threat model, `evidence/` (probe results) |
| `artifacts/inventory/expected_tests.txt` | the 796 collected test IDs |
| `artifacts/run-NNN/` | one run each: `attempt_records.jsonl` (schema 1.0.0), `meta.json`, `junit.xml`, and `pytest_stdout.log` where stored |
| `artifacts/reconciliation_*.md/.json` | JUnit vs inventory vs records, per run set |
| `artifacts/repeated_runs_log*.md` | cross-run comparison and validation, per run set |
| `artifacts/duration_trace.csv` | per-test durations of run-001..003, mean and max |

## Runs

| Folders | Run ids | Execution | Metadata |
|---|---|---|---|
| `run-001..003` | `rep-1..3` | **unrestricted** docker run (baseline, never edited) | basic |
| `run-004..006` | `v2-1..3` | **unrestricted**, image ID check, Docker and host metadata | `meta_version` 2 |
| `run-007..009` | `v3-1..3` | **restricted** (`security/run_restricted.sh`) | `meta_version` 3 |

All runs: 793 passed, 3 skipped (1 Windows-only, 2 `no_jupyter`), 0 failed, 0 missing, 796 records, identical outcomes across runs.
The JUnit suite attribute says 857 tests: 796 `<testcase>` elements plus 61 subtests. Subtests have no testcase element, are recorded only as counts in the reconciliation reports, and are not extra node IDs.

## Reproduce (from `m2-execution/`)

Use a new run prefix and new report file names. Never reuse an existing run folder or overwrite the baseline reports.

```bash
mkdir -p upstream && git clone https://github.com/psf/black.git upstream/black
git -C upstream/black checkout 0aa7ce6926f097d06e348edf89937d3f770b37f1
./docker/build.sh                       # refuses a wrong or dirty checkout, never overwrites the recorded image ID
harness/repeat_runs.sh rerun            # restricted runs into runs/rerun-1..3 (git-ignored)
for i in 1 2 3; do python harness/junit_to_records.py runs/rerun-$i $i; done
python harness/reconcile_run.py artifacts/inventory/expected_tests.txt artifacts/reconciliation_rerun.md runs/rerun-1 runs/rerun-2 runs/rerun-3
python harness/compare_runs.py artifacts/repeated_runs_log_rerun.md runs/rerun-1 runs/rerun-2 runs/rerun-3
python harness/export_durations.py artifacts/duration_trace_rerun.csv runs/rerun-1 runs/rerun-2 runs/rerun-3
```

A rebuild on another machine uses the same pinned inputs but may produce a different image ID. `build.sh` then exits with 77 and keeps the recorded ID; treat that as a new environment.

## Exit codes

| Code | Meaning |
|---|---|
| 0 to 5 | pytest's own exit code, saved in `meta.json` and then returned |
| 71 | `docker/IMAGE_DIGEST.txt` missing |
| 72 | image tag does not match the recorded image ID |
| 73 | run folder already exists (never overwritten) |
| 74 | invalid run id |
| 75 | unsafe output directory (restricted runner) |
| 76, 77 | `build.sh`: wrong checkout, or rebuilt image ID differs |

## Security

Restricted runs use uid 10001, `--cap-drop ALL`, `no-new-privileges`, `--network none`, memory 2 GB, 2 CPUs, 512 PIDs, read-only root, 256 MB `/tmp`, `--pull=never`. See `security/threat_model.md`.
The resource-limit stress test is **PENDING**. The writable `/out` mount is a documented residual risk.

## Limitations

- Three repeats cannot detect rare flakiness.
- Docker Desktop runs containers in a Linux VM, so the controls protect the VM, not directly the Windows host.
- Serial execution only; no coverage data (Member 4).
- This harness measures reliability only. It makes no claim about test selection performance.