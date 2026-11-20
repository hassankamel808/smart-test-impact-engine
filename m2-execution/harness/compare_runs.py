#!/usr/bin/env python3
"""Usage: compare_runs.py OUT.md run_dir1 run_dir2 [run_dir3 ...]
Lists every test whose outcome differs between runs (Gate 0 repeated-run log)."""
import json, sys
from pathlib import Path


def load(run_dir):
    p = Path(run_dir) / "attempt_records.jsonl"
    return {r["test_id"]: r for r in (json.loads(l) for l in p.read_text().splitlines() if l.strip())}


out, dirs = sys.argv[1], sys.argv[2:]
runs = [load(d) for d in dirs]
names = [Path(d).name for d in dirs]
tests = sorted(set().union(*[set(r) for r in runs]))

diff = [t for t in tests if len({r.get(t, {}).get("outcome", "missing") for r in runs}) > 1]
spread = []
for t in tests:
    ds = [r[t]["duration_s"] for r in runs if t in r and r[t]["duration_s"] is not None]
    if len(ds) > 1 and min(ds) > 0:
        spread.append((max(ds) / min(ds), t, min(ds), max(ds)))
spread.sort(reverse=True)

L = [f"# Repeated-run log", "", f"Runs compared: {', '.join(names)}",
     f"Tests compared: {len(tests)}", f"Tests with differing outcome: {len(diff)}", ""]
if diff:
    L += ["| Test | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for t in diff:
        L.append(f"| `{t}` | " + " | ".join(r.get(t, {}).get("outcome", "missing") for r in runs) + " |")
else:
    L.append("No test changed outcome across these runs.")
L += ["", "## Duration spread (informational, top 10 by max/min ratio)", "",
      "| Test | min s | max s | ratio |", "|---|---|---|---|"]
for ratio, t, lo, hi in spread[:10]:
    L.append(f"| `{t}` | {lo:.3f} | {hi:.3f} | {ratio:.1f} |")
L += ["", "Unstable rule (team decision): a test is unstable if its outcome differs in any run.",
      "Limitation: three runs cannot detect rare flakiness (for example 1 failure in 20)."]
Path(out).write_text("\n".join(L) + "\n")
print(f"{len(diff)} tests differ; written to {out}")
