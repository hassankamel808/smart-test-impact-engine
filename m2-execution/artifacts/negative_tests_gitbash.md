# Negative-path tests (gitbash)

- Date (UTC): 2026-11-22T13:53:30Z
- Host: MINGW64_NT-10.0-26200 3.6.5-22c95533.x86_64 x86_64 (WSL distro: none)
- Docker server: 29.9.3
- Git: git version 2.52.0.windows.1
- Real symlinks available: no
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
| symlinked runs/ and output dir (5 checks) | SKIP | this shell cannot create real symlinks; run in Linux/WSL |
| build.sh: upstream/black missing | PASS | exit 76 |
| build.sh: wrong Black commit (parent of the pin) | PASS | exit 76 |
| build.sh: dirty checkout (modified tracked file) | PASS | exit 76 |
| build.sh: dirty checkout (untracked file) | PASS | exit 76 |
| build.sh negative cases never reached docker build | PASS | no docker build/run was attempted |
| build.sh: clean pinned checkout reaches docker build (control; shim blocks the build) | PASS | exit 99 |
| run_restricted: image digest mismatch | PASS | exit 72 |
| run_suite: image digest mismatch | PASS | exit 72 |
| run_suite: existing run folder | PASS | exit 73 |
| digest and existing-folder cases never started a container | PASS | no docker build/run was attempted |
| control: matching digest starts the restricted container (runs 'true') | PASS | exit 0 |
| image ID unchanged by the tests | PASS | sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef |

Summary: 20 passed, 0 failed, 1 skipped
