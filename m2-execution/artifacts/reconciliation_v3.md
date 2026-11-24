# Reconciliation report

Inventory: 796 IDs (796 distinct, 796 distinct JUnit keys)

| Metric | v3-1 | v3-2 | v3-3 |
|---|---|---|---|
| JUnit testcase elements | 796 | 796 | 796 |
| JUnit suite `tests` attribute | 857 | 857 | 857 |
| Subtests derived (suite tests attribute minus testcase elements) | 61 | 61 | 61 |
| Subtests reported in pytest_stdout.log | {"passed": 61} | {"passed": 61} | {"passed": 61} |
| Mapped elements | 796 | 796 | 796 |
| Mapped unique inventory IDs | 796 | 796 | 796 |
| Duplicate IDs in JUnit | 0 | 0 | 0 |
| Extra elements from duplicates | 0 | 0 | 0 |
| Unmatched JUnit cases | 0 | 0 | 0 |
| ...subtest-like (name extends an inventory test) | 0 | 0 | 0 |
| ...belonging to how many parent tests | 0 | 0 | 0 |
| ...unclassified | 0 | 0 | 0 |
| Inventory IDs with no JUnit case | 0 | 0 | 0 |
| Attempt records | 796 | 796 | 796 |
| Unique record IDs | 796 | 796 | 796 |
| Duplicate record IDs | 0 | 0 | 0 |
| Inventory IDs without a record | 0 | 0 | 0 |
| Records not in inventory | 0 | 0 | 0 |
| Record outcomes | {"passed": 793, "skipped": 3} | {"passed": 793, "skipped": 3} | {"passed": 793, "skipped": 3} |

All runs have the same record ID set: **True**

Subtests are recorded here as counts only. They are not additional pytest node IDs, and the attempt records stay at one record per test function.

## Samples of unmatched JUnit cases: v3-1 (0 total)
- none

## Samples of unmatched JUnit cases: v3-2 (0 total)
- none

## Samples of unmatched JUnit cases: v3-3 (0 total)
- none

