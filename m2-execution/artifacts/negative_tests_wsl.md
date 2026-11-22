# Negative-path tests (wsl)

- Date (UTC): 2026-11-22T13:55:25Z
- Host: Linux 6.18.58.1-microsoft-standard-WSL2 x86_64 (WSL distro: Ubuntu)
- Docker server: 29.9.3
- Git: git version 2.53.0
- Real symlinks available: yes
- Sandbox copy of the scripts was used and deleted afterwards; real runs/, artifacts/run-*, docker/IMAGE_DIGEST.txt untouched.

| Case | Result | Detail |
|---|---|---|
| reconcile: unmodified run (control) | PASS | exit 0 |
| reconcile: JUnit case missing | PASS | exit 1 |
| reconcile: duplicate JUnit test ID | PASS | exit 1 |
| reconcile: unmatched JUnit case | PASS | exit 1 |
| run_suite: run_id with traversal (../escape) | PASS | exit 74 |
| run_restricted: output dir with traversal (../../escape) | PASS | exit 75 |
| run_restricted: absolute output dir (/tmp/x) | PASS | exit 75 |
| nothing created outside the sandbox | PASS | no escape directory |
| run_suite: runs/ is a symlink | PASS | exit 75 |
| run_restricted: runs/ is a symlink | PASS | exit 75 |
| symlink target untouched (runs/) | PASS | nothing created behind the link |
| run_restricted: output dir is a symlink | PASS | exit 75 |
| symlink target untouched (output dir) | PASS | nothing created behind the link |
| build.sh: upstream/black missing | PASS | exit 76 |
| build.sh: wrong commit, dirty (2 cases), control | SKIP | no Black clone at the pinned commit (set BLACK_SRC or clone upstream/black) |
| build.sh missing-checkout case never reached docker build | PASS | no docker build/run was attempted |
| run_restricted: image digest mismatch | PASS | exit 72 |
| run_suite: image digest mismatch | PASS | exit 72 |
| run_suite: existing run folder | PASS | exit 73 |
| digest and existing-folder cases never started a container | PASS | no docker build/run was attempted |
| control: matching digest starts the restricted container (runs 'true') | PASS | exit 0 |
| image ID unchanged by the tests | PASS | sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef |

Summary: 21 passed, 0 failed, 1 skipped
