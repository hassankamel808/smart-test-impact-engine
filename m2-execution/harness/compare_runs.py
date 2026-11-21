#!/usr/bin/env python3
"""Usage: compare_runs.py OUT.md run_dir1 run_dir2 [...] [--expected FILE]
Validates inventory, provenance (commit SHA, image ID, schema, config) and outcomes.
Exit 0 only if every validation passes."""
import argparse, json
from collections import Counter
from pathlib import Path


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
    shas = {r["commit_sha"] for rs in recs for r in rs}
    if any(len(s) != 40 for s in shas):
        problems.append("commit_sha is not 40 characters")

    L += ["", "## 3. Run metadata", "", "| Run | pytest exit | Docker server | platform | host |", "|---|---|---|---|---|"]
    for n, m in zip(names, metas):
        L.append(f"| {n} | {m.get('pytest_exit_code', 'n/a')} | {m.get('docker_server_version', 'n/a (baseline)')} "
                 f"| {m.get('docker_server_platform', 'n/a (baseline)')} | {m.get('host_platform', 'n/a (baseline)')} |")

    by = [{r["test_id"]: r["outcome"] for r in rs} for rs in recs]
    diff = [t for t in sorted(exp_set) if len({b.get(t, "missing") for b in by}) > 1]
    L += ["", "## 4. Outcome differences", "", f"Tests with differing outcome: {len(diff)}", ""]
    if diff:
        L += ["| Test | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
        L += [f"| `{t}` | " + " | ".join(b.get(t, "missing") for b in by) + " |" for t in diff]

    spread = []
    for t in sorted(exp_set):
        ds = [r["duration_s"] for rs in recs for r in rs if r["test_id"] == t and r["duration_s"] is not None] if False else []
    dur = [{r["test_id"]: r["duration_s"] for r in rs} for rs in recs]
    for t in sorted(exp_set):
        ds = [d[t] for d in dur if d.get(t) is not None]
        if len(ds) > 1 and min(ds) > 0:
            spread.append((max(ds) / min(ds), t, min(ds), max(ds)))
    spread.sort(reverse=True)
    L += ["", "## 5. Duration spread (informational, top 10)", "", "| Test | min s | max s | ratio |", "|---|---|---|---|"]
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