"""Prepare/check offline public-data review records. Never RPC/sign/submit."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from zzz_ops.operator_review import main

if __name__=='__main__':sys.exit(main())
