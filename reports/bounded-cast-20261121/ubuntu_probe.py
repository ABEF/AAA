"""Run only the frozen Cast-capture helper tests as nobody; no services/RPC."""
from pathlib import Path
import base64
import ctypes
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time

EXPECTED = {
    "keeper/cast_process.py": "b6203067b022625bce2bfb415bb6ed85620dc8c7002b51f2d3d4c9296c5ac3e1",
    "test_cast_process.py": "875628819dae4d09ebc5a214dba634788d798182d2b3e882eefa22d7f2c2a9a2",
}

assert os.geteuid() == 0 and sys.platform.startswith("linux")
payload = json.loads(sys.stdin.buffer.read(131073))
assert set(payload) == set(EXPECTED)
sources = {name: base64.b64decode(payload[name], validate=True) for name in EXPECTED}
assert all(len(raw) < 32768 and hashlib.sha256(raw).hexdigest() == EXPECTED[name]
           for name, raw in sources.items())
# Adopt only this probe's orphaned test descendants, including the fork case.
# This is a per-process setting, not a service/host configuration change.
assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
os.setgroups([])
os.setgid(65534)
os.setuid(65534)
assert os.getuid() == os.geteuid() == 65534

with tempfile.TemporaryDirectory(prefix="popl-cast-check-", dir="/tmp") as directory:
    root = Path(directory).resolve()
    assert root.parent == Path("/tmp") and root.name.startswith("popl-cast-check-")
    assert root.stat().st_uid == 65534
    (root / "keeper").mkdir(mode=0o700)
    (root / "keeper/__init__.py").write_bytes(b"")
    (root / "tmp").mkdir(mode=0o700)
    for name, raw in sources.items():
        (root / name).write_bytes(raw)
    command = [sys.executable, "-m", "unittest", "-v", "test_cast_process"]
    child = subprocess.Popen(command, cwd=root, env={
        "PATH": "/usr/bin:/bin", "PYTHONPATH": str(root), "TMPDIR": str(root / "tmp"),
        "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C.UTF-8"},
        start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    expired = False
    try:
        stdout, stderr = child.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        expired = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate(timeout=2)
    # Every test emits only bounded unittest diagnostics, never captured child data.
    assert len(stdout) + len(stderr) < 262144
    seen = set()
    killed = 0
    until = time.monotonic() + 2
    children_file = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children")
    while children_file.read_text().split():
        assert time.monotonic() < until, "Test descendant cleanup deadline"
        for value in children_file.read_text().split():
            pid = int(value)
            fields = Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1].split()
            assert int(fields[1]) == os.getpid() and pid != child.pid
            first = pid not in seen
            seen.add(pid)
            if first and fields[0] not in ("Z", "X"):
                os.kill(pid, signal.SIGKILL)
                killed += 1
            os.waitpid(pid, os.WNOHANG)
        time.sleep(.01)
    result = {"schema": 1, "scope": "eight_new_Cast_capture_helper_methods_only",
              "uid": os.getuid(), "source_sha256": EXPECTED,
              "exit_code": child.returncode, "outer_timeout": expired,
              "stdout": stdout.decode(), "stderr": stderr.decode(),
              "orphaned_test_descendants_reaped": len(seen),
              "unexpected_live_descendants_killed": killed,
              "all_children_reaped": not children_file.read_text().split(),
              "services_chain_signer_or_RPC_used": False,
              "temporary_directory": str(root)}
assert not root.exists()
result["temporary_directory_removed"] = True
result["successful"] = child.returncode == 0 and not expired and killed == 0
print(json.dumps(result, indent=2))
