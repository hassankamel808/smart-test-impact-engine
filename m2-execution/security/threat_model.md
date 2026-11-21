# Container threat model (Member 2)

Scope: running the test suite of a team-pinned repository (psf/black @ 0aa7ce6926f097d06e348edf89937d3f770b37f1) in Docker.
Not in scope: arbitrary public pull requests. Containers are not a complete sandbox for hostile code.

Image: `black-ref:0aa7ce6`, ID `sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef`
Restricted runner: `security/run_restricted.sh`. Probe: `security/hostile/probe.py`.
Evidence: `security/evidence/hostile_restricted.json`, `security/evidence/hostile_open.json`.

## Assets
Host files, host environment variables, credentials, network access, the output folder, CI infrastructure.

## Threats and controls
| Threat | Control | Status |
|---|---|---|
| Read host env variables / secrets | No `-e`, no `--env-file`; no secrets in the image | Probe: `USERPROFILE` not visible in either run |
| Network exfiltration / downloads | `--network none` | Probe: DNS, TCP 443 and HTTP GET all blocked; the open run allowed DNS |
| Escalate privileges | uid 10001, `--cap-drop ALL`, `no-new-privileges`, no sudo installed | Probe: all capability sets zero, `sudo` not found |
| Tamper with source or system files | `--read-only` root, tmpfs only for `/tmp` | Probe: writes to `/app` and `/etc` blocked |
| Read protected files | non-root user | Probe: `/etc/shadow` blocked |
| Control the Docker daemon | socket never mounted | Probe: `/var/run/docker.sock` absent |
| Resource exhaustion (memory, CPU, process count) | `--memory 2g --memory-swap 2g`, `--cpus 2`, `--pids-limit 512` are configured | **PENDING: limits are set but have not been stress-tested. Exhaustion is not claimed to be mitigated.** |
| Hostile writes to the output mount | per-run mount only; converter parses XML/JSON and never executes it | **Residual risk** (see below) |

## Checklist
- [x] non-root user
- [x] no secrets passed to the container
- [x] no Docker socket
- [x] capabilities dropped (`--cap-drop ALL`), `no-new-privileges`
- [x] network policy `--network none`
- [x] read-only root filesystem
- [x] resource limits configured (memory, CPU, PIDs)
- [x] full suite passes under all restrictions (restricted-01: 793 passed, 3 skipped)
- [ ] **resource-limit stress test (memory hog, fork bomb): PENDING**

## Blocked vs not blocked
Blocked: network (DNS, TCP, HTTP), writes outside `/tmp` and `/out`, host environment variables, `/etc/shadow`, `sudo`, Docker socket.
Not blocked: writes to `/tmp` and `/out`; reading environment variables baked into the image.

## Finding: `GPG_KEY` environment variable
- The probe flagged `GPG_KEY` because its name filter matches "KEY". It reports names only.
- Source: the official `python:3.12-slim` base image sets it in its own image configuration. It appears in the base image's `Config.Env` (checked by `docker image inspect` on the base image pinned by digest) and was not added by this project.
- It is not host-provided: our scripts pass no `-e` or `--env-file` (checked with `grep`), and host variables such as `USERPROFILE` are not visible in the container.
- Consequence: the probe can see image-level variables, so no real secret may ever be put in the image. Host-provided credentials were not found.

## Residual risk: writable `/out` mount
`/out` is a host folder mounted read-write, because pytest must write its JUnit file there. A hostile test could therefore:
- fill the folder (disk exhaustion on the host or VM),
- plant files or forge a `junit.xml` that the harness later reads (result poisoning),
- not escape the folder: the probe saw only `/out` as a host mount.

Mitigations in place: one folder per run, no other host mount, output treated as untrusted data and parsed, never executed. Not yet in place: a size quota on the folder, and cross-checking the JUnit file against the pytest exit code and the stdout summary. Accepted for team-owned code only.

## Limitations
- Docker Desktop on Windows runs containers in a Linux VM, so these controls protect the VM, not directly the Windows host.
- The container shares the VM's kernel; no custom seccomp profile was applied.
- The hostile test is a probe that reports what is allowed, not an exploit attempt.
- Only team-owned code is run. This model does not make arbitrary public pull requests safe.
- `artifacts/run-001..006` were executed without the restriction set (same image ID, same
  commands otherwise). Only `restricted-01` and, from `run-007` on, the default harness run
  under `security/run_restricted.sh`. The restricted and unrestricted runs gave identical outcomes.
- The runner checks the image ID against `docker/IMAGE_DIGEST.txt`, never pulls (`--pull=never`),
  and accepts only `runs/<name>` as output dir (no traversal, no symlinks). `/out` stays a
  writable per-run mount (residual risk above).
## Review
Reviewers: Member 1 and the leader. Open items go to `decisions/technology-log.md`.