"""Run only the two reviewed lock-source files as nobody, without services/RPC."""
from pathlib import Path
import base64
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile

EXPECTED = {
    "zzz_ops/state.py": "78985688f9fc0cebf4aa5912b1401a338ac1e9ce21d8c787393e0e2d421976cf",
    "test_process_lock_safety.py": "3d983cb79896c326eec5e68494c752385ca9bdb39779608d4e882ee085f022e2",
}
payload = json.load(sys.stdin)
assert set(payload) == set(EXPECTED) and os.geteuid() == 0
sources = {name: base64.b64decode(payload[name], validate=True) for name in EXPECTED}
assert all(len(raw) < 32 * 1024 and hashlib.sha256(raw).hexdigest() == EXPECTED[name] for name, raw in sources.items())
os.setgroups([])
os.setgid(65534)
os.setuid(65534)
assert os.getuid() == os.geteuid() == 65534
with tempfile.TemporaryDirectory(prefix="popl-lock-check-", dir="/tmp") as directory:
    root = Path(directory).resolve()
    assert root.parent == Path("/tmp") and root.name.startswith("popl-lock-check-") and root.stat().st_uid == 65534
    (root / "zzz_ops").mkdir(mode=0o700)
    (root / "zzz_ops/__init__.py").write_bytes(b"")
    for name, raw in sources.items():
        (root / name).write_bytes(raw)
    command = [sys.executable, "-m", "unittest", "-v", "test_process_lock_safety"]
    child = subprocess.Popen(command, cwd=root, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(root),
                                                   "PYTHONDONTWRITEBYTECODE": "1"},
                             start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    expired = False
    try:
        stdout, stderr = child.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        expired = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate(timeout=5)
    assert len(stdout) + len(stderr) < 64 * 1024
    result = {"schema": 1, "scope": "only_new_process_lock_tests_unprivileged_Ubuntu",
              "uid": os.getuid(), "source_sha256": EXPECTED, "exit_code": child.returncode,
              "timeout": expired, "stdout": stdout.decode(), "stderr": stderr.decode(),
              "services_or_chain_or_signer_started": False, "temporary_directory": str(root)}
assert not root.exists()
result["temporary_directory_removed"] = True
print(json.dumps(result, indent=2))
