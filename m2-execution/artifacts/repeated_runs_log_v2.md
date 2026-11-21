# Repeated-run comparison

Runs: v2-1, v2-2, v2-3
Inventory: 796 IDs (artifacts/inventory/expected_tests.txt)

## 1. Inventory

| Run | records | unique IDs | duplicates | inventory IDs missing | not in inventory | outcome=missing |
|---|---|---|---|---|---|---|
| v2-1 | 796 | 796 | 0 | 0 | 0 | 0 |
| v2-2 | 796 | 796 | 0 | 0 | 0 | 0 |
| v2-3 | 796 | 796 | 0 | 0 | 0 | 0 |

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
| v2-1 | 0 | 29.9.3 | Docker Desktop linux/x86_64 | MINGW64_NT-10.0-26200 3.6.5-22c95533.x86_64 x86_64 | OS=Windows_NT |
| v2-2 | 0 | 29.9.3 | Docker Desktop linux/x86_64 | MINGW64_NT-10.0-26200 3.6.5-22c95533.x86_64 x86_64 | OS=Windows_NT |
| v2-3 | 0 | 29.9.3 | Docker Desktop linux/x86_64 | MINGW64_NT-10.0-26200 3.6.5-22c95533.x86_64 x86_64 | OS=Windows_NT |

## 4. Outcome differences

Tests with differing outcome: 0


## 5. Duration spread (informational, top 10)

| Test | min s | max s | ratio |
|---|---|---|---|
| `tests/test_format.py::test_simple_format[module_docstring_3]` | 0.011 | 0.612 | 55.6 |
| `tests/test_format.py::test_simple_format[line_ranges_outside_source]` | 0.001 | 0.006 | 6.0 |
| `tests/test_black.py::BlackTestCase::test_parse_pyproject_toml_project_metadata` | 0.001 | 0.004 | 4.0 |
| `tests/test_docs.py::test_feature_lists_are_up_to_date` | 0.002 | 0.007 | 3.5 |
| `tests/test_black.py::BlackTestCase::test_line_ranges_in_pyproject_toml` | 0.002 | 0.007 | 3.5 |
| `tests/test_ipynb.py::test_ipynb_and_pyi_flags` | 0.001 | 0.003 | 3.0 |
| `tests/test_black.py::BlackTestCase::test_report_write_github_outputs` | 0.001 | 0.003 | 3.0 |
| `tests/test_black.py::BlackTestCase::test_report_verbose` | 0.001 | 0.003 | 3.0 |
| `tests/test_black.py::TestCaching::test_filter_cached_hash` | 0.002 | 0.005 | 2.5 |
| `tests/test_black.py::TestCaching::test_filter_cached` | 0.002 | 0.005 | 2.5 |

## Validation

**PASS**

Unstable rule (team decision): unstable if the outcome differs in any run.
Limitation: a few runs cannot detect rare flakiness (for example 1 failure in 20).
