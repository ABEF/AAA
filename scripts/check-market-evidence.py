#!/usr/bin/env python3
"""Check the dated 16-November market bundle offline; never approve live use."""
from pathlib import Path
import argparse
import json
import sys

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
from zzz_ops.market_evidence import verify


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,
        default=REPO/'reports/real-market-refresh-20261116/evidence.zip')
    args=parser.parse_args(argv)
    try:
        report=verify(args.evidence)
    except (ValueError,OSError) as exc:
        print(json.dumps({'status':'FAIL','production_approved':False,
            'error':str(exc),'network_calls':0}))
        return 1
    print(json.dumps(report,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
