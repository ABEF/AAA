"""Unsigned keeper journal backup, verification and exclusive review-only restore."""
import argparse
from pathlib import Path
import sys

# Reading a protected installed release must not create bytecode beside it.
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from keeper.recovery_bundle import backup,verify,restore,DEFAULT_BYTES,RecoveryRefusal,REFUSAL_CODES


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self,message):
        # Rejected values may be a misplaced credential or endpoint.
        self.print_usage(sys.stderr)
        self.exit(2,'Invalid keeper-recovery arguments. Use --help.\n')


def main(argv=None):
    parser=SafeArgumentParser(prog='keeper-recovery',description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    for name in ('backup','verify','restore'):
        command=commands.add_parser(name)
        command.add_argument('--config',type=Path,required=True)
        command.add_argument('--max-bytes',type=int,default=DEFAULT_BYTES)
        command.add_argument('--max-seconds',type=int,default=60)
        if name=='backup':
            command.add_argument('--working-directory',type=Path,required=True)
        else:
            command.add_argument('--bundle',type=Path,required=True)
            command.add_argument('--manifest-sha256',required=True)
            command.add_argument('--max-age-seconds',type=int,required=True)
            command.add_argument('--minimum-created-at',type=int,default=0)
            command.add_argument('--minimum-next-nonce',type=int)
        if name!='verify':command.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        options={'max_bytes':args.max_bytes,'max_seconds':args.max_seconds}
        if args.action=='backup':
            _,digest=backup(args.config,args.output,working_directory=args.working_directory,**options)
        else:
            options.update(max_age_seconds=args.max_age_seconds,minimum_created_at=args.minimum_created_at,
                minimum_next_nonce=args.minimum_next_nonce)
            if args.action=='verify':
                verify(args.bundle,args.manifest_sha256,args.config,**options)
                digest=args.manifest_sha256
            else:
                _,digest=restore(args.bundle,args.manifest_sha256,args.config,args.output,**options)
    except Exception as exc:
        # Even unexpected ordinary failures must not echo a credential-bearing
        # config value, path or exception message. Interrupts still propagate.
        code=exc.code if type(exc)is RecoveryRefusal and exc.code in REFUSAL_CODES else 'invalid_input'
        print('Keeper recovery refused ('+code+'). Preserve the original journal and separately secured configuration. '
            'An incomplete output may remain; use a new path. Nothing was signed, installed or started.',file=sys.stderr)
        return 1
    label='Restore plan SHA-256'if args.action=='restore'else'Manifest SHA-256'
    print(label+': '+digest)
    print('Offline integrity review only. Configuration and signer secrets are not bundled. '
        'Before adoption, fence the old signer, review runtime paths, reconcile canonical transactions and '
        'run the reviewed stock recovery. No service was started or state installed.')
    return 0


if __name__=='__main__':raise SystemExit(main())
