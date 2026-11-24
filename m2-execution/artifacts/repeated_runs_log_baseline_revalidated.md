# Repeated-run comparison

Runs: run-001, run-002, run-003
Inventory: 796 IDs (artifacts/inventory/expected_tests.txt)

## 1. Inventory

| Run | records | unique IDs | duplicates | inventory IDs missing | not in inventory | outcome=missing |
|---|---|---|---|---|---|---|
| run-001 | 796 | 796 | 0 | 0 | 0 | 0 |
| run-002 | 796 | 796 | 0 | 0 | 0 | 0 |
| run-003 | 796 | 796 | 0 | 0 | 0 | 0 |

Same test ID set in every run: **True**

## 2. Provenance

| Field | Distinct values across all records |
|---|---|
| commit_sha | 0aa7ce6926f097d06e348edf89937d3f770b37f1 |
| image_id | sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef |
| schema_version | 1.0.0 |
| config | 1 distinct |

## 3. Run metadata

| Run | pytest exit | Docker server | platform | host |
|---|---|---|---|---|
| run-001 | 0 | n/a (baseline) | n/a (baseline) | n/a (baseline) |
| run-002 | 0 | n/a (baseline) | n/a (baseline) | n/a (baseline) |
| run-003 | 0 | n/a (baseline) | n/a (baseline) | n/a (baseline) |

## 4. Outcome differences

Tests with differing outcome: 0


## 5. Duration spread (informational, top 10)

| Test | min s | max s | ratio |
|---|---|---|---|
| `tests/test_black.py::TestFileCollection::test_get_sources_with_stdin_symlink_outside_root` | 0.002 | 0.012 | 6.0 |
| `tests/test_black.py::BlackTestCase::test_get_features_used_for_future_flags` | 0.002 | 0.010 | 5.0 |
| `tests/test_format.py::test_simple_format[whitespace]` | 0.001 | 0.002 | 2.0 |
| `tests/test_format.py::test_simple_format[line_ranges_outside_source]` | 0.001 | 0.002 | 2.0 |
| `tests/test_format.py::test_empty` | 0.001 | 0.002 | 2.0 |
| `tests/test_docs.py::test_feature_lists_are_up_to_date` | 0.001 | 0.002 | 2.0 |
| `tests/test_black.py::BlackTestCase::test_report_write_github_outputs` | 0.001 | 0.002 | 2.0 |
| `tests/test_black.py::BlackTestCase::test_reformat_one_with_stdin_filename_pyi` | 0.001 | 0.002 | 2.0 |
| `tests/test_black.py::BlackTestCase::test_reformat_one_with_stdin_and_existing_path` | 0.001 | 0.002 | 2.0 |
| `tests/test_black.py::BlackTestCase::test_is_filesystem_root` | 0.001 | 0.002 | 2.0 |

## Validation

**PASS**

Unstable rule (team decision): unstable if the outcome differs in any run.
Limitation: a few runs cannot detect rare flakiness (for example 1 failure in 20).
