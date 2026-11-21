# Repeated-run comparison

Runs: v3-1, v3-2, v3-3
Inventory: 796 IDs (artifacts/inventory/expected_tests.txt)

## 1. Inventory

| Run | records | unique IDs | duplicates | inventory IDs missing | not in inventory | outcome=missing |
|---|---|---|---|---|---|---|
| v3-1 | 796 | 796 | 0 | 0 | 0 | 0 |
| v3-2 | 796 | 796 | 0 | 0 | 0 | 0 |
| v3-3 | 796 | 796 | 0 | 0 | 0 | 0 |

Same test ID set in every run: **True**

## 2. Provenance

| Field | Distinct values across all records |
|---|---|
| commit_sha | 0aa7ce6926f097d06e348edf89937d3f770b37f1 |
| image_id | sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef |
| schema_version | 1.0.0 |
| config | 1 distinct |

## 3. Pytest exit codes (from meta.json)

| Run | pytest exit | failed+error records | Docker server | platform | host |
|---|---|---|---|---|---|
| v3-1 | 0 | 0 | 29.9.3 | Docker Desktop linux/x86_64 | MINGW64_NT-10.0-26200 3.6.5-22c95533.x86_64 x86_64 | OS=Windows_NT |
| v3-2 | 0 | 0 | 29.9.3 | Docker Desktop linux/x86_64 | MINGW64_NT-10.0-26200 3.6.5-22c95533.x86_64 x86_64 | OS=Windows_NT |
| v3-3 | 0 | 0 | 29.9.3 | Docker Desktop linux/x86_64 | MINGW64_NT-10.0-26200 3.6.5-22c95533.x86_64 x86_64 | OS=Windows_NT |

## 4. Duration validation

| Run | valid durations | invalid | sum of test time s | suite time s | max s |
|---|---|---|---|---|---|
| v3-1 | 796 | 0 | 80.18 | 84 | 2.727 |
| v3-2 | 796 | 0 | 77.05 | 79 | 2.702 |
| v3-3 | 796 | 0 | 77.37 | 79 | 2.824 |

Rules: a non-missing record needs a finite number >= 0; missing needs null; summed test time must not exceed the suite time (serial run, 2 s tolerance).

## 5. Outcome differences

Tests with differing outcome: 0


## 6. Duration spread (informational, top 10)

| Test | min s | max s | ratio |
|---|---|---|---|
| `tests/test_black.py::BlackTestCase::test_parse_pyproject_toml_project_metadata` | 0.001 | 0.011 | 11.0 |
| `tests/test_docs.py::test_feature_lists_are_up_to_date` | 0.001 | 0.009 | 9.0 |
| `tests/test_format.py::test_simple_format[line_ranges_outside_source]` | 0.001 | 0.007 | 7.0 |
| `tests/test_ipynb.py::test_unparseable_notebook` | 0.001 | 0.006 | 6.0 |
| `tests/test_black.py::TestFileCollection::test_get_sources_with_stdin_filename` | 0.001 | 0.006 | 6.0 |
| `tests/test_black.py::BlackTestCase::test_parse_pyproject_toml` | 0.001 | 0.006 | 6.0 |
| `tests/test_ipynb.py::test_entire_notebook_without_changes` | 0.002 | 0.008 | 4.0 |
| `tests/test_format.py::test_patma_invalid` | 0.002 | 0.008 | 4.0 |
| `tests/test_format.py::test_simple_format[whitespace]` | 0.002 | 0.007 | 3.5 |
| `tests/test_black.py::TestFileCollection::test_invalid_nested_gitignore` | 0.004 | 0.014 | 3.5 |

## Validation

**PASS**

Unstable rule (team decision): unstable if the outcome differs in any run.
Limitation: a few runs cannot detect rare flakiness (for example 1 failure in 20).
