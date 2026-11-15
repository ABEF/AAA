"""Prepare an offline source-pinned deployment review; never deploy or seal."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from zzz_ops.deployment_plan import main
if __name__=='__main__':raise SystemExit(main())
