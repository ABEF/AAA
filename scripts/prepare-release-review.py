"""Export or verify a frozen, read-only review package. No tests or approvals."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zzz_ops.review_bundle import main

if __name__ == '__main__':
    sys.exit(main())
