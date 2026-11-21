"""Read-only final unit/cgroup inventory for the two explicitly owned Ubuntu labs."""
from pathlib import Path
import json
import os
import subprocess

LABS = ("popl-ubuntu-20261121-c8876a3a", "popl-ubuntu-20261121-8a629f43")
rows = []
assert os.geteuid() == 0
for stem in LABS:
    for role in ("keeper", "proxy", "anvil", "cache"):
        unit = stem + "-" + role + ".service"
        command = subprocess.run(["systemctl", "show", unit, "--no-pager", "-p", "Id", "-p", "LoadState",
                                  "-p", "ActiveState", "-p", "SubState", "-p", "MainPID", "-p", "ControlGroup"],
                                 capture_output=True, timeout=5)
        fields = dict(line.split("=", 1) for line in command.stdout.decode().splitlines() if "=" in line)
        assert command.returncode == 0 or fields.get("LoadState") == "not-found"
        group = Path("/sys/fs/cgroup/system.slice") / unit
        process_files = list(group.rglob("cgroup.procs")) if group.exists() else []
        assert len(process_files) <= 64
        pids = sorted({int(value) for file in process_files for value in file.read_text().splitlines()})
        rows.append({"unit": unit, "properties": fields, "cgroup": str(group),
                     "cgroup_exists": group.exists(), "cgroup_pids": pids,
                     "stopped": fields.get("MainPID", "0") == "0" and fields.get("ActiveState") in ("inactive", "failed") and not pids})
print(json.dumps({"schema": 1, "scope": "read_only_owned_units_cgroups_after_stop", "units": rows,
                  "all_owned_stopped": all(row["stopped"] for row in rows), "service_writes": False}, indent=2))
