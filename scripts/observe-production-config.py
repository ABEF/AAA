#!/usr/bin/env python3
"""Read one canonical production-inventory snapshot without signing or approval.

The explicitly named environment variable contains only a read RPC endpoint.
Its contents and provider exceptions are never included in output or logs.
"""
import argparse
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zzz_ops.production_observer import observe, read_manifest, write_observation
from zzz_ops.rpc import Rpc


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # Argparse normally echoes unrecognized values. A mistakenly supplied
        # endpoint must not disclose an RPC credential in diagnostics.
        raise ValueError('Invalid observer arguments')


def main(argv=None):
    parser = _Parser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--rpc-env', required=True, help='Name of a read-only RPC URL environment variable')
    parser.add_argument('--block-number', type=int, help='Optional cross-check of the inventory block; never a latest fallback')
    parser.add_argument('--expected-block-hash', help='Required with --block-number; must match the reviewed inventory anchor')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--historical-consistency',action='store_true',
        help='Inspect an explicitly historical inventory; never qualify the fresh portfolio release')
    try:
        args = parser.parse_args(argv)
        if not re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', args.rpc_env) or any(
                word in args.rpc_env for word in ('PRIVATE', 'SECRET', 'PASSWORD', 'MNEMONIC', 'SIGNER', 'KEY')):
            raise ValueError('Use an explicitly named read RPC URL variable')
        config = read_manifest(args.config)
        if args.config.resolve() == args.output.resolve():
            raise ValueError('Keep observations separate from the reviewed input inventory')
        if (args.block_number is None) != (args.expected_block_hash is None):
            raise ValueError('Supply both optional anchor cross-checks')
        if args.block_number is not None:
            anchor = config['chains'][0]['observed_block']
            if (type(anchor['number']) is not int or args.block_number != anchor['number'] or
                    not re.fullmatch(r'0x[0-9a-fA-F]{64}', args.expected_block_hash) or
                    args.expected_block_hash.lower() != anchor['hash'].lower()):
                raise ValueError('Explicit anchor differs from the reviewed inventory')
        chain_id = config['chains'][0]['chain_id']
        endpoint = os.environ[args.rpc_env]
        rpc = Rpc([endpoint], chain_id, timeout=10, retries=2)
        version=config.get('schema_version')
        if type(version) is int and version==8 and not args.historical_consistency:
            from zzz_ops.production_observer_v6 import observe as observe_current
            result=observe_current(config,rpc)
        elif type(version) is int and version==7 and args.historical_consistency:
            from zzz_ops.production_observer_v5 import observe as observe_current
            result=observe_current(config,rpc)
        elif type(version) is int and version==6 and args.historical_consistency:
            from zzz_ops.production_observer_v4 import observe as observe_current
            result = observe_current(config,rpc)
        elif args.historical_consistency:
            result = observe(config, rpc)
        else:
            raise ValueError('Historical inventory needs explicit inspection; no relabeling')
        write_observation(args.output, result)
    except Exception:
        print('Inventory observation failed; previous output preserved. Check public configuration, canonical anchor and read RPC availability.', file=sys.stderr)
        return 1
    complete = result['chains'][0]['observation']['complete']
    print('Read-only inventory observation saved. '+('Reads complete.' if complete else 'Some observations are unavailable or mismatched.')+
          ' Independent reviews and complete inventory history remain separate; this is not release approval.')
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
