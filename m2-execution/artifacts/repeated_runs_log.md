# Repeated-run log

Runs compared: rep-1, rep-2, rep-3
Tests compared: 796
Tests with differing outcome: 0

No test changed outcome across these runs.

## Duration spread (informational, top 10 by max/min ratio)

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

Unstable rule (team decision): a test is unstable if its outcome differs in any run.
Limitation: three runs cannot detect rare flakiness (for example 1 failure in 20).
