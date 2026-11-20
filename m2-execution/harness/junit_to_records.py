#!/usr/bin/env python3
"""Convert one run's JUnit XML into attempt records (schema 1.0.0, JSON Lines).
Usage: junit_to_records.py <run_dir> <repeat_index> [--expected FILE]
Needs <run_dir>/junit.xml and <run_dir>/meta.json. Writes <run_dir>/attempt_records.jsonl
"""
import argparse, json, sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
OUTCOMES = {"passed", "failed", "skipped", "error", "missing"}
RANK = {"skipped": 0, "passed": 1, "failed": 2, "error": 3}
CONFIG = {"xdist_workers": 0, "coverage": False, "coverage_core": None,
          "extra_flags": ["-p no:cacheprovider"]}


def nodeid_to_key(nodeid):
    """tests/test_x.py::Cls::test_a[p] -> ('tests.test_x.Cls', 'test_a[p]')"""
    path, _, rest = nodeid.partition(".py::")
    base, br, params = rest.partition("[")
    parts = base.split("::")
    return ".".join([path.replace("/", ".")] + parts[:-1]), parts[-1] + br + params


def classify(tc):
    for tag, outcome in (("error", "error"), ("failure", "failed"), ("skipped", "skipped")):
        el = tc.find(tag)
        if el is not None:
            return outcome, el
    return "passed", None


def signature(el):
    msg = (el.get("message") or "").strip() or (el.text or "").strip()
    first = msg.splitlines()[0] if msg else "unknown"
    typ = el.get("type") or ""
    sig = f"{typ}: {first}" if typ and not first.startswith(typ) else first
    return sig[:300] or "unknown"


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate(rec):
    errs = []
    if len(rec["commit_sha"]) != 40: errs.append("commit_sha not 40 chars")
    if not rec["image_id"].startswith("sha256:"): errs.append("image_id format")
    if rec["outcome"] not in OUTCOMES: errs.append("bad outcome")
    if (rec["duration_s"] is None) != (rec["outcome"] == "missing"):
        errs.append("duration_s null only for missing")
    if rec["outcome"] in ("failed", "error") and not rec["error_signature"]:
        errs.append("empty error_signature")
    if rec["outcome"] in ("passed", "skipped", "missing") and rec["error_signature"]:
        errs.append("error_signature must be empty")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("repeat_index", type=int)
    ap.add_argument("--expected", default="artifacts/inventory/expected_tests.txt")
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    meta = json.loads((run_dir / "meta.json").read_text())
    root = ET.parse(run_dir / "junit.xml").getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")

    start = datetime.fromisoformat(suite.get("timestamp"))
    if start.tzinfo is None:                      # container clock is UTC
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(seconds=float(suite.get("time", 0)))

    expected = [l.strip() for l in Path(a.expected).read_text().splitlines() if "::" in l]
    key_to_id = {nodeid_to_key(n): n for n in expected}

    base = {"schema_version": SCHEMA_VERSION, "run_id": meta["run_id"],
            "repeat_index": a.repeat_index, "commit_sha": meta["commit_sha"],
            "image_id": meta["image_id"]}
    found, unmatched, dups = {}, [], 0
    for tc in suite.iter("testcase"):
        key = (tc.get("classname", ""), tc.get("name", ""))
        nodeid = key_to_id.get(key)
        if nodeid is None:
            unmatched.append(key)
            continue
        outcome, el = classify(tc)
        dur = float(tc.get("time", 0))
        if nodeid in found:                       # keep the worst outcome, sum time
            dups += 1
            old = found[nodeid]
            dur += old["duration_s"]
            if RANK[old["outcome"]] >= RANK[outcome]:
                old["duration_s"] = dur
                continue
        rec = dict(base, test_id=nodeid, outcome=outcome, duration_s=dur,
                   error_signature=signature(el) if outcome in ("failed", "error") else "",
                   started_at=iso(start), finished_at=iso(end), config=CONFIG)
        if outcome == "skipped":
            rec["skip_reason"] = (el.get("message") or "").strip()
        found[nodeid] = rec

    records = []
    for n in expected:                            # expected order, missing filled in
        records.append(found.get(n) or dict(
            base, test_id=n, outcome="missing", duration_s=None, error_signature="",
            started_at=iso(start), finished_at=iso(end), config=CONFIG))

    bad = [(r["test_id"], e) for r in records if (e := validate(r))]
    out = run_dir / "attempt_records.jsonl"
    out.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    counts = {}
    for r in records:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    print(f"{meta['run_id']}: {len(records)} records -> {out}")
    print("outcomes:", counts, "| duplicates merged:", dups)
    if unmatched:
        print(f"WARNING: {len(unmatched)} JUnit testcases not in expected list:")
        for k in unmatched[:10]: print("  ", k)
    if bad:
        print("WARNING: schema violations:", bad[:10])
    sys.exit(2 if (unmatched or bad) else 0)


if __name__ == "__main__":
    main()
