# M2 Execution


## Reference runs (Member 2)

Target: psf/black @ `0aa7ce6926f097d06e348edf89937d3f770b37f1`, Python 3.12, pytest 9.2.0, serial, black's own config.
Image ID used: `sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef`.

| Path | Content |
|---|---|
| `docker/` | Dockerfile, hash-locked dependency files, build script |
| `harness/` | run, repeat, JUnit-to-records converter, run comparison, duration export |
| `security/` | restricted runner, hostile probe, threat model, `evidence/` (probe results) |
| `artifacts/inventory/expected_tests.txt` | the 796 collected test IDs |
| `artifacts/run-001..003/` | three repeats (rep-1..3): `attempt_records.jsonl` (schema 1.0.0), `meta.json`, `junit.xml` |
| `artifacts/repeated_runs_log.md` | 0 tests changed outcome across 3 runs |
| `artifacts/duration_trace.csv` | per-test durations, mean and max |

Result per run: 793 passed, 3 skipped (1 Windows-only, 2 `no_jupyter`), 0 failed, 0 missing. The `run_id` inside the records is `rep-N`; folder `run-00N` is the same run.

Reproduce (from `m2-execution/`):

```bash
mkdir -p upstream && git clone https://github.com/psf/black.git upstream/black
git -C upstream/black checkout 0aa7ce6926f097d06e348edf89937d3f770b37f1
./docker/build.sh
harness/repeat_runs.sh rep        # raw output goes to runs/ (git-ignored)
for i in 1 2 3; do python harness/junit_to_records.py runs/rep-$i $i; done
python harness/compare_runs.py artifacts/repeated_runs_log.md runs/rep-1 runs/rep-2 runs/rep-3
python harness/export_durations.py artifacts/duration_trace.csv runs/rep-1 runs/rep-2 runs/rep-3
```

Limitations: three repeats cannot detect rare flakiness; Docker Desktop runs containers in a Linux VM; resource limits are not stress-tested; this harness measures reliability only, not selection performance.