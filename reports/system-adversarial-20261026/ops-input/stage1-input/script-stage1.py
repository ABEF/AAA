"""Bounded read-only inventory and offline summary; no wallet or signer."""
import argparse
import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zzz_ops.holder_preflight import scan_page, summarize
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.errors import WorkLimit


def read_json(path):
    # Bound the read itself, not merely the bytes already allocated in memory.
    with Path(path).open('rb') as source:
        raw = source.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Inventory input exceeds bound')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate inventory JSON key')
            result[key] = value
        return result
    def reject_constant(_value):
        raise ValueError('Nonfinite inventory JSON number')
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Nonfinite inventory JSON number')
        return number
    try:
        return json.loads(raw, object_pairs_hook=unique,
                          parse_constant=reject_constant, parse_float=finite_float)
    except RecursionError:
        raise ValueError('Inventory JSON parser exceeded its nesting limit') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    scan = sub.add_parser('scan')
    scan.add_argument('--config', required=True)
    scan.add_argument('--rpc-env', default='POPL_READ_RPC_URL')
    scan.add_argument('--first', type=int, default=1)
    scan.add_argument('--limit', type=int, default=50)
    scan.add_argument('--output', required=True)
    merge = sub.add_parser('summarize')
    merge.add_argument('pages', nargs='+')
    merge.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.mode == 'scan':
            cfg = read_json(args.config)
            rpc = Rpc([os.environ[args.rpc_env]], cfg['chain_id'], retries=2)
            report = scan_page(rpc, cfg, first=args.first, limit=args.limit)
            status = 0
        else:
            if len(args.pages) > 1000:
                raise ValueError('Too many pages')
            report = summarize([read_json(p) for p in args.pages])
            status = 0 if report['complete'] and not report['unresolved_contract_holders'] else 2
        # Never overwrite an older successful observation after a failed retry.
        with Path(args.output).open('x', encoding='utf-8', newline='\n') as out:
            out.write(json.dumps(report, indent=2) + '\n')
        print('Inventory saved. This is read-only evidence, not migration approval.')
        return status
    except (ValueError, KeyError, TypeError, OSError, RpcError, WorkLimit):
        # Provider URLs can contain credentials: do not expose exception details.
        print('Inventory failed; no new successful report. Check configuration, permissions, canonical block and RPC availability.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
