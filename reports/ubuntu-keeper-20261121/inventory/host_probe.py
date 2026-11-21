"""Read-only Ubuntu/tool/service inventory; no keys, configs, journals or writes."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys


def command(argv, timeout=8):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                            env={"PATH": "/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
    assert len(result.stdout) <= 1024 * 1024 and len(result.stderr) <= 64 * 1024
    return {"argv": argv, "exit_code": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr}


def main():
    release = {}
    for line in Path("/etc/os-release").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key in ("NAME", "VERSION", "ID", "VERSION_ID", "PRETTY_NAME"):
                release[key] = value.strip('"')
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            memory[key] = value.strip()
    disks = {}
    for target in ("/opt", "/run", "/tmp"):
        info = shutil.disk_usage(target)
        disks[target] = {"total": info.total, "used": info.used, "free": info.free}

    tools = {}
    roots = [Path(p) for p in ("/usr/local/bin", "/usr/bin", "/root/.foundry/bin",
                              "/opt/zzz-keeper-staging/bin", "/opt/zzz-keeper-staging/.foundry/bin",
                              "/opt/foundry-v1.4.4", "/opt/popl-rehearsal-tools")]
    for name in ("python3", "anvil", "cast", "forge", "solc", "docker", "podman"):
        candidates = {str(root / name) for root in roots if (root / name).is_file()}
        found = shutil.which(name)
        if found:
            candidates.add(found)
        rows = []
        for target in sorted(candidates):
            path = Path(target)
            if not os.access(path, os.X_OK):
                continue
            version = command([target, "--version"])
            row = {"path": target, "resolved": str(path.resolve()), "bytes": path.stat().st_size,
                   "version": version}
            if name in ("anvil", "cast", "forge") and path.stat().st_size <= 128 * 1024 * 1024:
                row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(row)
        tools[name] = rows

    units = []
    selected = command(["systemctl", "list-units", "--all", "--type=service,timer", "--output=json", "--no-pager"])
    if selected["exit_code"] == 0:
        rows = json.loads(selected["stdout"])
        names = sorted(row["unit"] for row in rows if re.search(r"(?:zzz|popl|nginx|caddy)", row["unit"], re.I))
        assert len(names) <= 60
        fields = ("Id", "LoadState", "ActiveState", "SubState", "MainPID", "NRestarts", "InvocationID")
        for name in names:
            result = command(["systemctl", "show", name, "--no-pager", *[v for key in fields for v in ("-p", key)]])
            units.append({"unit": name, "properties": dict(line.split("=", 1) for line in result["stdout"].splitlines() if "=" in line),
                          "exit_code": result["exit_code"]})
    result = {"schema": 1, "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "read_only_host_and_tool_inventory_no_service_or_configuration_changes",
              "os_release": release, "kernel": platform.release(), "machine": platform.machine(),
              "python": sys.version, "transport_effective_uid": os.geteuid(), "cpu_count": os.cpu_count(),
              "memory": memory, "disk_bytes": disks, "tools": tools,
              "systemd_version": command(["systemctl", "--version"]),
              "mounts": {p: command(["findmnt", "--noheadings", "--target", p, "--output", "TARGET,FSTYPE,OPTIONS"]) for p in ("/opt", "/run", "/tmp")},
              "selected_unit_inventory_exit_code": selected["exit_code"], "selected_units": units,
              "listening_tcp": command(["ss", "-H", "-ltnp"]),
              "production_approved": False}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
