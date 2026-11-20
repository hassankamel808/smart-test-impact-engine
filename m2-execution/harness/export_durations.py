#!/usr/bin/env python3
"""Per-test duration trace from attempt records.
Usage: export_durations.py OUT.csv run_dir1 [run_dir2 ...]
Reads <run_dir>/attempt_records.jsonl. Writes one CSV row per test and prints a summary.
"""
import csv, json, statistics, sys
from pathlib import Path


def load(run_dir):
    p = Path(run_dir) / "attempt_records.jsonl"
    return {r["test_id"]: r for r in (json.loads(l) for l in p.read_text().splitlines() if l.strip())}


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    if not dirs:
        sys.exit(__doc__)
    names = [Path(d).name for d in dirs]
    runs = [load(d) for d in dirs]
    tests = sorted(set().union(*[set(r) for r in runs]))

    rows = []
    for t in tests:
        per_run, outcomes = [], []
        for r in runs:
            rec = r.get(t)
            outcomes.append(rec["outcome"] if rec else "missing")
            per_run.append(rec["duration_s"] if rec else None)
        vals = [d for d in per_run if d is not None]
        rows.append({
            "test_id": t,
            **{f"duration_{n}": ("" if d is None else f"{d:.6f}") for n, d in zip(names, per_run)},
            "mean_s": f"{statistics.mean(vals):.6f}" if vals else "",
            "max_s": f"{max(vals):.6f}" if vals else "",
            "outcomes": "|".join(sorted(set(outcomes))),
        })

    rows.sort(key=lambda r: float(r["max_s"] or 0), reverse=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    means = [float(r["mean_s"]) for r in rows if r["mean_s"]]
    total = sum(means)
    print(f"{len(rows)} tests, {len(dirs)} runs -> {out}")
    print(f"sum of mean durations: {total:.2f} s (sum of test times, not wall clock)")
    print("top 5 slowest by max:")
    for r in rows[:5]:
        print(f"  {float(r['max_s']):8.3f} s  {r['test_id']}")
    top10 = sum(float(r["mean_s"]) for r in rows[:10] if r["mean_s"])
    print(f"top 10 tests = {100 * top10 / total:.1f}% of total test time")
    no_dur = [r["test_id"] for r in rows if not r["mean_s"]]
    if no_dur:
        print(f"WARNING: {len(no_dur)} tests have no duration (missing): {no_dur[:5]}")


main()