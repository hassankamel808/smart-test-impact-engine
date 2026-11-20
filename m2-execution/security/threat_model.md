# Container threat model (Member 2)

Scope: running the test suite of a team-pinned repository (psf/black @ 0aa7ce6926f097d06e348edf89937d3f770b37f1) in Docker.
Not in scope: arbitrary public pull requests. Containers are not a complete sandbox for hostile code.

Image: `black-ref:0aa7ce6`, ID `sha256:97ad1d4c33ba11fc921bb6f0e5b6b1144459cbd07c31adf41ff5f1d6563274ef`
Restricted runner: `security/run_restricted.sh`
Probe: `security/hostile/probe.py`
Evidence: `security/evidence/hostile_restricted.json`, `security/evidence/hostile_open.json`

## Assets
Host files, host environment variables, credentials, network access, the output folder, CI infrastructure.

## Threats and controls
| Threat | Control | Evidence |
|---|---|---|
| Read host env variables / secrets | No `-e`, no `--env-file`; no secrets in image | probe: `USERPROFILE` not visible (BLOCKED) in both runs |
| Network exfiltration / downloads | `--network none` | probe: DNS (name resolution failed), TCP 443 (network unreachable), HTTP GET: all BLOCKED; open run allowed DNS |
| Escalate privileges | non-root uid 10001, `--cap-drop ALL`, `no-new-privileges`, no sudo installed | probe: uid=10001, all capability sets zero, `sudo` not found |
| Tamper with source or system files | `--read-only` root filesystem, tmpfs only for `/tmp` | probe: writes to `/app` and `/etc` BLOCKED (open run allowed `/app`) |
| Read protected files | non-root user | probe: `/etc/shadow` BLOCKED |
| Control the Docker daemon | socket never mounted | probe: `/var/run/docker.sock` absent |
| Exhaust resources | `--memory 2g --memory-swap 2g`, `--cpus 2`, `--pids-limit 512` | configured; not stress-tested |
| Poison results via output folder | per-run mount only; converter parses XML/JSON data and never executes it | residual risk |

## Checklist
- [x] non-root user
- [x] no secrets passed to the container
- [x] no Docker socket
- [x] capabilities dropped (`--cap-drop ALL`)
- [x] `no-new-privileges`
- [x] network policy: `--network none`
- [x] read-only root filesystem
- [x] resource limits set (memory, CPU, PIDs)
- [x] full suite passes under all restrictions (restricted-01: 793 passed, 3 skipped)
- [ ] resource limits stress-tested (memory hog, fork bomb)

## Blocked vs not blocked
Blocked: network (DNS, TCP, HTTP), writes outside `/tmp` and `/out`, host environment variables, `/etc/shadow`, `sudo`, Docker socket.
Not blocked: writes to `/tmp` and `/out`; reading image-level environment variables.

Findings:
- `GPG_KEY` is visible in the environment. It is a public key ID set by the official python base image, not a host secret.
- `/out` is writable by design. Hostile code can fill it or plant files, so its contents are treated as untrusted data.
- In the unrestricted comparison run, DNS worked but TCP 443 and HTTP timed out (likely Docker Desktop or firewall), so that run does not show what a hostile test could reach on other networks.

## Limitations
- Docker Desktop on Windows runs containers in a Linux VM, so these controls protect the VM, not directly the Windows host.
- The container shares the VM's kernel; no custom seccomp profile was applied.
- Resource limits (memory, CPU, PIDs) were configured but not stress-tested.
- The hostile test was a probe that reports what is allowed, not an exploit attempt.
- Only team-owned code is run. This model does not make arbitrary public pull requests safe.

## Review
Reviewers: Member 1 and the leader. Open items go to `decisions/technology-log.md`.