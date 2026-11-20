#!/usr/bin/env python3
"""Hostile probe: reports what the container allows. Writes /out/hostile_result.json"""
import json, os, socket, subprocess, urllib.request

R = {}


def probe(name, fn):
    try:
        R[name] = {"result": "ALLOWED", "detail": str(fn())[:200]}
    except Exception as e:
        R[name] = {"result": "BLOCKED", "detail": f"{type(e).__name__}: {e}"[:200]}


def caps():
    return [l.strip() for l in open("/proc/self/status") if l.startswith("Cap")]


def mounts():
    return [l.split()[1] for l in open("/proc/mounts") if "/out" in l or "docker" in l][:5]


SECRET_HINTS = ("TOKEN", "SECRET", "KEY", "PASSWORD", "USERPROFILE", "COMPUTERNAME")
probe("read_env_secrets", lambda: [k for k in os.environ if any(h in k.upper() for h in SECRET_HINTS)]
      or "no secret-like variable names visible")
probe("read_host_windows_env", lambda: os.environ["USERPROFILE"])
probe("network_dns", lambda: socket.gethostbyname("example.com"))
probe("network_tcp_443", lambda: socket.create_connection(("1.1.1.1", 443), timeout=3))
probe("http_get", lambda: urllib.request.urlopen("http://example.com", timeout=3).status)
probe("docker_socket", lambda: os.stat("/var/run/docker.sock"))
probe("write_app_dir", lambda: open("/app/hostile.txt", "w").write("x"))
probe("write_root_etc", lambda: open("/etc/hostile.txt", "w").write("x"))
probe("write_tmp", lambda: open("/tmp/hostile.txt", "w").write("x"))
probe("write_out_mount", lambda: open("/out/hostile_write.txt", "w").write("x"))
probe("read_etc_shadow", lambda: open("/etc/shadow").read(50))
probe("run_as_user", lambda: f"uid={os.getuid()} gid={os.getgid()}")
probe("sudo", lambda: subprocess.run(["sudo", "id"], capture_output=True, timeout=3).stdout)
probe("capabilities", caps)
probe("mounts_of_interest", mounts)

try:
    with open("/out/hostile_result.json", "w") as f:
        json.dump(R, f, indent=2)
except Exception as e:
    print("could not write result file:", e)

for k, v in R.items():
    print(f"{v['result']:8} {k}: {v['detail']}")