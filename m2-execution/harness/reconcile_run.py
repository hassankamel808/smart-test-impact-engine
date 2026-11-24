#!/usr/bin/env python3
"""Reconcile JUnit testcases and attempt records against the expected inventory.
Usage: reconcile_run.py EXPECTED.txt OUT.md run_dir [run_dir ...]
Never modifies run folders. Writes OUT.md and OUT.json.
Exit 0 if every run's records are exactly the inventory; 1 if not;
2 if records are fine but some unmatched JUnit cases could not be explained."""
import json, re, sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from junit_to_records import nodeid_to_key


def parent_of(cls, name, by_cls):
    best = None
    for exp_name, nodeid in by_cls.get(cls, []):
        if (name.startswith(exp_name) and len(name) > len(exp_name)
                and name[len(exp_name)] in " (["):
            if best is None or len(exp_name) > len(best[0]):
                best = (exp_name, nodeid)
    return best[1] if best else None

def subtests_from_log(d):
    """Parse 'N subtests passed' from the last non-empty line of pytest_stdout.log, if stored."""
    log = Path(d) / "pytest_stdout.log"
    if not log.exists():
        return None
    lines = [l for l in log.read_text(errors="replace").splitlines() if l.strip()]
    found = re.findall(r"(\d+) subtests? (passed|failed|skipped)", lines[-1]) if lines else []
    return {status: int(n) for n, status in found}

def reconcile(run_dir, expected, key_to_id, by_cls):
    d = Path(run_dir)
    root = ET.parse(d / "junit.xml").getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    cases = list(suite.iter("testcase"))
    seen, unmatched = Counter(), []
    for tc in cases:
        key = (tc.get("classname", ""), tc.get("name", ""))
        nid = key_to_id.get(key)
        if nid is None:
            unmatched.append(key)
        else:
            seen[nid] += 1
    parents, unclassified, samples = Counter(), [], []
    for cls, name in unmatched:
        p = parent_of(cls, name, by_cls)
        label = f"{cls}::{name}"
        if p:
            parents[p] += 1
            label += f"  -> probable subtest of {p}"
        else:
            unclassified.append(label)
        if len(samples) < 8:
            samples.append(label)
    recs = [json.loads(l) for l in (d / "attempt_records.jsonl").read_text().splitlines() if l.strip()]
    ids = [x["test_id"] for x in recs]
    c = Counter(ids)
    r = {
        "run": d.name,
        "junit_testcase_elements": len(cases),
        "junit_suite_tests_attribute": suite.get("tests"),
        "subtests_derived_from_suite_attribute":
            (int(suite.get("tests")) - len(cases)) if (suite.get("tests") or "").isdigit() else None,
        "subtests_reported_by_pytest": subtests_from_log(d),
        "subtests_note": "Subtests are counted in the suite 'tests' attribute only. "
                         "They have no <testcase> element and are not extra pytest node IDs.",
        "mapped_elements": sum(seen.values()),
        "mapped_unique_ids": len(seen),
        "duplicate_ids_in_junit": sorted(i for i, k in seen.items() if k > 1),
        "extra_elements_from_duplicates": sum(k - 1 for k in seen.values() if k > 1),
        "unmatched_total": len(unmatched),
        "unmatched_subtest_like": sum(parents.values()),
        "unmatched_parent_tests": len(parents),
        "unmatched_unclassified": unclassified,
        "unmatched_samples": samples,
        "inventory_ids_not_in_junit": sorted(set(expected) - set(seen)),
        "records": len(ids),
        "record_unique_ids": len(c),
        "record_duplicate_ids": sorted(i for i, k in c.items() if k > 1),
        "inventory_ids_without_record": sorted(set(expected) - set(ids)),
        "records_not_in_inventory": sorted(set(ids) - set(expected)),
        "record_outcomes": dict(Counter(x["outcome"] for x in recs)),
    }
    return r, set(ids)


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    exp_file, out, dirs = sys.argv[1], sys.argv[2], sys.argv[3:]
    expected = [l.strip() for l in Path(exp_file).read_text().splitlines() if "::" in l]
    key_to_id = {nodeid_to_key(n): n for n in expected}
    by_cls = defaultdict(list)
    for (cls, name), nid in key_to_id.items():
        by_cls[cls].append((name, nid))
    results, idsets = [], []
    for d in dirs:
        r, s = reconcile(d, expected, key_to_id, by_cls)
        results.append(r)
        idsets.append(s)

    n = len(expected)
    same_ids = all(s == idsets[0] for s in idsets)
    rows = [
        ("JUnit testcase elements", lambda r: r["junit_testcase_elements"]),
        ("JUnit suite `tests` attribute", lambda r: r["junit_suite_tests_attribute"]),
        ("Subtests derived (suite tests attribute minus testcase elements)",
         lambda r: r["subtests_derived_from_suite_attribute"]),
        ("Subtests reported in pytest_stdout.log",
         lambda r: json.dumps(r["subtests_reported_by_pytest"]) if r["subtests_reported_by_pytest"] is not None
         else "n/a (log not stored)"),
        ("Mapped elements", lambda r: r["mapped_elements"]),
        ("Mapped unique inventory IDs", lambda r: r["mapped_unique_ids"]),
        ("Duplicate IDs in JUnit", lambda r: len(r["duplicate_ids_in_junit"])),
        ("Extra elements from duplicates", lambda r: r["extra_elements_from_duplicates"]),
        ("Unmatched JUnit cases", lambda r: r["unmatched_total"]),
        ("...subtest-like (name extends an inventory test)", lambda r: r["unmatched_subtest_like"]),
        ("...belonging to how many parent tests", lambda r: r["unmatched_parent_tests"]),
        ("...unclassified", lambda r: len(r["unmatched_unclassified"])),
        ("Inventory IDs with no JUnit case", lambda r: len(r["inventory_ids_not_in_junit"])),
        ("Attempt records", lambda r: r["records"]),
        ("Unique record IDs", lambda r: r["record_unique_ids"]),
        ("Duplicate record IDs", lambda r: len(r["record_duplicate_ids"])),
        ("Inventory IDs without a record", lambda r: len(r["inventory_ids_without_record"])),
        ("Records not in inventory", lambda r: len(r["records_not_in_inventory"])),
        ("Record outcomes", lambda r: json.dumps(r["record_outcomes"])),
    ]
    L = ["# Reconciliation report", "",
         f"Inventory: {n} IDs ({len(set(expected))} distinct, {len(key_to_id)} distinct JUnit keys)", "",
         "| Metric | " + " | ".join(r["run"] for r in results) + " |",
         "|---|" + "---|" * len(results)]
    for label, fn in rows:
        L.append(f"| {label} | " + " | ".join(str(fn(r)) for r in results) + " |")
    L += ["", f"All runs have the same record ID set: **{same_ids}**", ""]
    L += ["Subtests are recorded here as counts only. They are not additional pytest node IDs, "
          "and the attempt records stay at one record per test function.", ""]
    for r in results:
        L.append(f"## Samples of unmatched JUnit cases: {r['run']} ({r['unmatched_total']} total)")
        L += [f"- `{s}`" for s in r["unmatched_samples"]] or ["- none"]
        L.append("")
    Path(out).write_text("\n".join(L) + "\n")
    Path(out).with_suffix(".json").write_text(json.dumps(results, indent=1))

    def problems(r):
        p = []
        if r["records"] != n or r["record_unique_ids"] != n:
            p.append("record count differs from inventory")
        if r["record_duplicate_ids"]:
            p.append("duplicate record IDs")
        if r["inventory_ids_without_record"]:
            p.append("inventory IDs without a record")
        if r["records_not_in_inventory"]:
            p.append("records not in inventory")
        if r["inventory_ids_not_in_junit"]:
            p.append("inventory IDs with no JUnit case")
        if r["duplicate_ids_in_junit"]:
            p.append("duplicate JUnit test IDs")
        if r["unmatched_total"]:
            p.append("unmatched JUnit cases")
        return p

    failed = {r["run"]: problems(r) for r in results if problems(r)}
    clean = same_ids and not failed
    print("\n".join(L[:4 + len(rows) + 2]))
    print(f"\nrecords exactly match inventory in every run: {clean}  -> {out}")
    verdict = ["", "## Verdict", "", "**CLEAN**" if clean else "**NOT CLEAN**"]
    if not same_ids:
        verdict.append("- runs do not have the same record ID set")
    for run, ps in failed.items():
        verdict += [f"- {run}: {p}" for p in ps]
    Path(out).write_text("\n".join(L + verdict) + "\n")
    for line in verdict[4:]:
        print(line)
    if not clean:
        sys.exit(1)


main()