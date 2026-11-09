"""Prepare/check offline source-bound PoPL SeaDrop manifests; never RPC/sign/submit."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zzz_ops.opensea_drop import main

if __name__ == '__main__':
    sys.exit(main())
