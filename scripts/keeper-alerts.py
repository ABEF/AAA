"""Unsigned one-shot keeper alert check; loopback test delivery only.

No scheduler, production notification channel, signer, service or keeper state
is installed or changed. Keep the alert directory separate from keeper files.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from keeper.alerts import run_once,AlertRefusal,REFUSAL_CODES

class SafeArgumentParser(argparse.ArgumentParser):
    def error(self,message):
        self.print_usage(sys.stderr)
        self.exit(2,'Invalid keeper-alerts arguments. Use --help.\n')

def main(argv=None):
    p=SafeArgumentParser(prog='keeper-alerts',description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--working-directory',type=Path,required=True)
    p.add_argument('--backup-bundle',type=Path,required=True)
    p.add_argument('--backup-manifest-sha256',required=True)
    p.add_argument('--backup-config',type=Path,required=True)
    p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--max-health-age-seconds',type=int,required=True)
    p.add_argument('--max-backup-age-seconds',type=int,required=True)
    p.add_argument('--pending-max-age-seconds',type=int,required=True,
        help='Grace since first sidecar observation; not transaction age.')
    p.add_argument('--receiver',help='Optional http://127.0.0.1:PORT/alerts test receiver.')
    p.add_argument('--allow-dry-run',action='store_true')
    p.add_argument('--max-seconds',type=int,default=60)
    p.add_argument('--max-bytes',type=int,default=16*1024*1024)
    a=p.parse_args(argv)
    try:
        result=run_once(a.config,working_directory=a.working_directory,
            backup_bundle=a.backup_bundle,backup_manifest_sha256=a.backup_manifest_sha256,
            backup_config_path=a.backup_config,directory=a.directory,
            max_health_age_seconds=a.max_health_age_seconds,max_backup_age_seconds=a.max_backup_age_seconds,
            pending_max_age_seconds=a.pending_max_age_seconds,receiver=a.receiver,
            allow_dry_run=a.allow_dry_run,max_seconds=a.max_seconds,max_bytes=a.max_bytes)
    except Exception as exc:
        code=exc.code if type(exc)is AlertRefusal and exc.code in REFUSAL_CODES else 'invalid_input'
        print(json.dumps({'schema':1,'unsigned':True,'readiness_approved':False,'ok':False,'refusal_code':code},sort_keys=True))
        return 1
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    return 0 if result['ok']else 1

if __name__=='__main__':raise SystemExit(main())
