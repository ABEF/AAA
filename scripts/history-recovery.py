"""Offline history backup, verification and exclusive restore; never installs."""
import argparse
from pathlib import Path
import re
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from frontend_api.history_recovery import backup, verify, restore, load_config, DEFAULT_BYTES, MAX_PACKAGE_BYTES
from frontend_api.earnings_checkpoint_build import BuildBudget
from zzz_ops.rpc import RpcError
from zzz_ops.work_budget import request_scope


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default message includes rejected values. A misplaced
        # credentialed URL or token must not become a terminal/log disclosure.
        self.print_usage(sys.stderr)
        self.exit(2,'Invalid history-recovery arguments. Use --help.\n')


def main(argv=None):
    parser=SafeArgumentParser(prog='history-recovery',description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    for name in ('backup','verify','restore'):
        command=commands.add_parser(name)
        if name=='backup':
            command.add_argument('--config',type=Path,required=True)
            command.add_argument('--review',type=Path)
            command.add_argument('--review-sha256')
        else:
            command.add_argument('--bundle',type=Path,required=True)
            command.add_argument('--manifest-sha256',required=True)
        if name!='verify':command.add_argument('--output',type=Path,required=True)
        command.add_argument('--max-seconds',type=int,default=60)
        command.add_argument('--max-bytes',type=int,default=DEFAULT_BYTES)
    args=parser.parse_args(argv)
    try:
        budget=BuildBudget(args.max_seconds)
        if not 1<=args.max_bytes<=MAX_PACKAGE_BYTES:raise ValueError('Invalid recovery byte bound')
        if args.action=='backup':
            if (args.review is None)!=(args.review_sha256 is None):raise ValueError('Review inputs must be paired')
            if args.review_sha256 is not None and not re.fullmatch('[0-9a-f]{64}',args.review_sha256):raise ValueError('Invalid review digest')
        elif not re.fullmatch('[0-9a-f]{64}',args.manifest_sha256):raise ValueError('Invalid manifest digest')
        with request_scope(budget) as active:
            options=dict(budget=active,max_bytes=args.max_bytes)
            if args.action=='backup':
                reviewed=None if args.review is None else {'path':str(args.review),'sha256':args.review_sha256}
                _,digest=backup(load_config(args.config),args.output,review=reviewed,**options)
            elif args.action=='verify':
                verify(args.bundle,args.manifest_sha256,**options);digest=args.manifest_sha256
            else:
                _,digest=restore(args.bundle,args.manifest_sha256,args.output,**options)
    except (OSError,ValueError,RpcError,sqlite3.Error,KeyError,TypeError,RecursionError):
        print('History recovery failed. Preserve the original databases, WAL, checkpoint and reviewed configuration. '
              'Inspect the requested output directory: partial unapproved files may exist; use a new path for another attempt. '
              'No configuration was installed or service restarted.',file=sys.stderr)
        return 1
    print(('Restore receipt SHA-256: ' if args.action=='restore' else 'Manifest SHA-256: ')+digest)
    print('Offline verification only. Not approved or installed. Preserve all raw history and the full24-hour window; '
          'review private path mappings and canonical coverage separately before any service adoption.')
    return 0


if __name__=='__main__':raise SystemExit(main())
