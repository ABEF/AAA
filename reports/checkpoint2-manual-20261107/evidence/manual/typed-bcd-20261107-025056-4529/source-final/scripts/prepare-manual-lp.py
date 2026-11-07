"""Prepare one read-only, typed, unsigned Active-state manual LP operation."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from zzz_ops.manual_lp_review import main

if __name__=='__main__':sys.exit(main())
