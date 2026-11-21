"""Sequential reviewed actions; stop on the first nonzero result."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
V = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-keeper-20261121")

if sys.argv[1] == "prepare":
    tasks = [("stop-preflight", "stop-preflight-01"),
             ("upload", "cache-upload-01", "--cache", str(V / "run2/prefetch-01/cache.json"), "--sha256", "558ef8edaae0428a313cf2a235854231c0d9a884e0a379655fadf46aa2fd780c"),
             ("freeze", "freeze-01", "--sha256", "558ef8edaae0428a313cf2a235854231c0d9a884e0a379655fadf46aa2fd780c"),
             ("start-final", "start-final-01"), ("bootstrap", "bootstrap-final-01"),
             ("preflight", "preflight-final-01"), ("initialize", "initialize-01")]
elif sys.argv[1] == "recover":
    tasks = [("hold-mining", "hold-mining-01"), ("live", "live-01"), ("await-pending", "pending-01"),
             ("lock-contender", "lock-contender-01"), ("kill-keeper", "kill-01"), ("resume-mining", "resume-mining-01")]
else:
    raise SystemExit("Unknown reviewed phase")
for task in tasks:
    result = subprocess.run([sys.executable, str(HERE / "drive.py"), *task])
    # The stock lock contender is expected to return1 because the main owns flock.
    expected = 1 if task[0] == "lock-contender" else 0
    if result.returncode != expected:
        raise SystemExit(result.returncode or 2)
