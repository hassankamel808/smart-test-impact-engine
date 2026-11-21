#!/usr/bin/env python3
"""Usage: compare_runs.py OUT.md run_dir1 run_dir2 [...] [--expected FILE]
Validates inventory, provenance, pytest exit codes (from meta.json), duration values
and outcomes. Exit 0 only if every validation passes."""
import argparse, json, math
from collections import Counter
from datetime import datetime
from pathlib import Path


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--expected", default="artifacts/inventory/expected_tests.txt")
    a = ap.parse_args()
    names = [Path(d).name for d in a.run_dirs]
    expected = [l.strip() for l in Path(a.expected).read_text().splitlines() if "::" in l]
    exp_set = set(expected)
    recs = [[json.loads(l) for l in (Path(d) / "attempt_records.jsonl").read_text().splitlines() if l.strip()]
            for d in a.run_dirs]
    metas = [json.loads((Path(d) / "meta.json").read_text()) if (Path(d) / "meta.json").exists() else {}
             for d in a.run_dirs]
    problems = []

    # 1. Inventory
    L = ["# Repeated-run comparison", "", f"Runs: {', '.join(names)}",
         f"Inventory: {len(expected)} IDs ({a.expected})", "", "## 1. Inventory", "",
         "| Run | records | unique IDs | duplicates | inventory IDs missing | not in inventory | outcome=missing |",
         "|---|---|---|---|---|---|---|"]
    idsets = []
    for n, rs in zip(names, recs):
        ids = [r["test_id"] for r in rs]
        c = Counter(ids)
        dups = [i for i, k in c.items() if k > 1]
        miss, extra = exp_set - set(ids), set(ids) - exp_set
        om = sum(1 for r in rs if r["outcome"] == "missing")
        L.append(f"| {n} | {len(ids)} | {len(c)} | {len(dups)} | {len(miss)} | {len(extra)} | {om} |")
        if dups or miss or extra or len(ids) != len(expected):
            problems.append(f"{n}: records do not match the inventory")
        if om:
            problems.append(f"{n}: {om} tests have outcome=missing")
        idsets.append(set(ids))
    same = all(s == idsets[0] for s in idsets)
    L.append(f"\nSame test ID set in every run: **{same}**")
    if not same:
        problems.append("runs do not contain the same test IDs")

    # 2. Provenance
    L += ["", "## 2. Provenance", "", "| Field | Distinct values across all records |", "|---|---|"]
    for f in ("commit_sha", "image_id", "schema_version"):
        vals = {r[f] for rs in recs for r in rs}
        L.append(f"| {f} | {', '.join(sorted(vals))} |")
        if len(vals) != 1:
            problems.append(f"{f} differs across records")
    cfgs = {json.dumps(r.get("config"), sort_keys=True) for rs in recs for r in rs}
    L.append(f"| config | {len(cfgs)} distinct |")
    if len(cfgs) != 1:
        problems.append("config differs across records")
    if any(len(r["commit_sha"]) != 40 for rs in recs for r in rs):
        problems.append("commit_sha is not 40 characters")
    for n, rs, m in zip(names, recs, metas):
        if m.get("commit_sha") and m["commit_sha"] != rs[0]["commit_sha"]:
            problems.append(f"{n}: meta commit_sha differs from records")
        if m.get("image_id") and m["image_id"] != rs[0]["image_id"]:
            problems.append(f"{n}: meta image_id differs from records")

    # 3. Pytest exit codes from metadata
    L += ["", "## 3. Pytest exit codes (from meta.json)", "",
          "| Run | pytest exit | failed+error records | Docker server | platform | host |", "|---|---|---|---|---|---|"]
    for n, rs, m in zip(names, recs, metas):
        code = m.get("pytest_exit_code")
        bad = sum(1 for r in rs if r["outcome"] in ("failed", "error"))
        L.append(f"| {n} | {code if code is not None else 'MISSING'} | {bad} | "
                 f"{m.get('docker_server_version', 'n/a (baseline)')} | "
                 f"{m.get('docker_server_platform', 'n/a (baseline)')} | {m.get('host_platform', 'n/a (baseline)')} |")
        if isinstance(code, bool) or not isinstance(code, int):
            problems.append(f"{n}: meta.json has no integer pytest_exit_code")
            continue
        if code != 0:
            problems.append(f"{n}: pytest exit code is {code}, not 0")
        if code == 0 and bad:
            problems.append(f"{n}: exit code 0 but {bad} failed/error records")
        if code == 1 and not bad:
            problems.append(f"{n}: exit code 1 (tests failed) but no failed/error records")

    # 4. Duration validation
    L += ["", "## 4. Duration validation", "",
          "| Run | valid durations | invalid | sum of test time s | suite time s | max s |", "|---|---|---|---|---|---|"]
    for n, rs in zip(names, recs):
        invalid, valid = [], []
        for r in rs:
            d = r["duration_s"]
            if r["outcome"] == "missing":
                if d is not None:
                    invalid.append(r["test_id"])
            elif isinstance(d, bool) or not isinstance(d, (int, float)) or not math.isfinite(d) or d < 0:
                invalid.append(r["test_id"])
            else:
                valid.append(d)
        suite = (ts(rs[0]["finished_at"]) - ts(rs[0]["started_at"])).total_seconds()
        total = sum(valid)
        L.append(f"| {n} | {len(valid)} | {len(invalid)} | {total:.2f} | {suite:.0f} | {max(valid, default=0):.3f} |")
        if invalid:
            problems.append(f"{n}: {len(invalid)} records have an invalid duration (e.g. {invalid[0]})")
        if total > suite + 2:
            problems.append(f"{n}: sum of test durations ({total:.1f}s) exceeds suite time ({suite:.0f}s)")
    L.append("\nRules: a non-missing record needs a finite number >= 0; missing needs null; "
             "summed test time must not exceed the suite time (serial run, 2 s tolerance).")

    # 5. Outcome differences
    by = [{r["test_id"]: r["outcome"] for r in rs} for rs in recs]
    diff = [t for t in sorted(exp_set) if len({b.get(t, "missing") for b in by}) > 1]
    L += ["", "## 5. Outcome differences", "", f"Tests with differing outcome: {len(diff)}", ""]
    if diff:
        L += ["| Test | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
        L += [f"| `{t}` | " + " | ".join(b.get(t, "missing") for b in by) + " |" for t in diff]

    dur = [{r["test_id"]: r["duration_s"] for r in rs} for rs in recs]
    spread = []
    for t in sorted(exp_set):
        ds = [d[t] for d in dur if isinstance(d.get(t), (int, float)) and not isinstance(d.get(t), bool)]
        if len(ds) > 1 and min(ds) > 0:
            spread.append((max(ds) / min(ds), t, min(ds), max(ds)))
    spread.sort(reverse=True)
    L += ["", "## 6. Duration spread (informational, top 10)", "",
          "| Test | min s | max s | ratio |", "|---|---|---|---|"]
    L += [f"| `{t}` | {lo:.3f} | {hi:.3f} | {ra:.1f} |" for ra, t, lo, hi in spread[:10]]

    L += ["", "## Validation", "", "**PASS**" if not problems else "**FAIL**"]
    L += [f"- {p}" for p in problems]
    L += ["", "Unstable rule (team decision): unstable if the outcome differs in any run.",
          "Limitation: a few runs cannot detect rare flakiness (for example 1 failure in 20)."]
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"validation: {'PASS' if not problems else 'FAIL'}; {len(diff)} tests differ; written to {a.out}")
    for p in problems:
        print("  -", p)
    raise SystemExit(1 if problems else 0)


main()