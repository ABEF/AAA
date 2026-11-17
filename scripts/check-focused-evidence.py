#!/usr/bin/env python3
"""Check fixed historical evidence; no compilation, network or execution."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from zzz_ops.focused_evidence import EvidenceError,check
if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(json.dumps({"integrity_admitted":False,"reason":"no_arguments_supported"}));raise SystemExit(2)
    try:
        result=check()
    except (EvidenceError,OSError,KeyError,TypeError,ValueError):
        print(json.dumps({"integrity_admitted":False,"reason":"focused_evidence_refused"}));raise SystemExit(2)
    print(json.dumps(result,indent=2))
