"""Prepare a typed unsigned custody or collective-exit governance operation."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from zzz_ops.management_review import main

if __name__=='__main__':sys.exit(main())
