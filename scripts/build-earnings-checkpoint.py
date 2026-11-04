"""Prepare a read-only candidate; review/pin separately. Never signs or installs."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from frontend_api.service import Projection
from frontend_api.earnings_checkpoint_build import BuildBudget,build,publish_candidate
from zzz_ops.state import read_json
from zzz_ops.rpc import RpcError


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--block',required=True,type=int)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--max-seconds',type=int,default=60)
    parser.add_argument('--max-calls',type=int,default=4096)
    parser.add_argument('--max-posts',type=int,default=8192)
    args=parser.parse_args(argv)
    try:
        budget=BuildBudget(args.max_seconds,args.max_calls,args.max_posts)
        p=Projection(read_json(args.config,encoding='utf-8'))
        if p.earnings_history is None:raise ValueError('Missing earnings profile')
        raw=build(p.earnings_history,args.block,budget=budget)
        digest=publish_candidate(args.output,raw)
    except (OSError,ValueError,RpcError,KeyError,TypeError,RecursionError):
        print('Checkpoint construction failed; preserve the reviewed config, raw database and prior checkpoint. No checkpoint was approved or service changed.',file=sys.stderr)
        return 1
    print('Candidate SHA-256: '+digest)
    print('Not approved or installed. Independently review before pinning; the served checkpoint must precede the full24-hour window.')
    return 0


if __name__=='__main__':raise SystemExit(main())
