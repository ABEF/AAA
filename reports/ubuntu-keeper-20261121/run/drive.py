"""Public action-only convenience wrapper; never reads a private lab artifact."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
V = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-keeper-20261121")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action")
    p.add_argument("label")
    p.add_argument("--cache")
    p.add_argument("--sha256")
    p.add_argument("--primary")
    p.add_argument("--secondary")
    a = p.parse_args()
    meta = json.loads((V / "transport/LAB2.json").read_bytes())
    cmd = [sys.executable, str(ROOT / "reports/ubuntu-keeper-20261121/transport/strict_transport.py"),
           "--bundle", meta["bundle"], "--lab", meta["lab"], "--action", a.action,
           "--output", str(V / "run2" / a.label)]
    for key in ("cache", "sha256", "primary", "secondary"):
        value = getattr(a, key)
        if value is not None:
            cmd += ["--" + key, value]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
