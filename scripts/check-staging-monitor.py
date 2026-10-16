"""Off-host, forced-command SSH check; copies only test recovery snapshots.

Private transport key and pinned known_hosts must remain outside the repository.
The remote account has no signing, service-control, shell or forwarding access.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from keeper.monitor import error_context
from keeper.ops import digest,timestamp


def validate_export(data,now=None):
    now=time.time() if now is None else now
    if data.get('staging_only') is not True or data.get('chain_id')!=31337:raise ValueError('Not a staging export')
    age=now-timestamp(data.get('created_at'))
    reasons=[]
    if age < -30 or age > 900:reasons.append('export_stale_or_future')
    if data.get('health',{}).get('ok') is not True:reasons.append('keeper_unhealthy')
    backup=data.get('backup',{})
    if backup.get('ok') is not True:reasons.append('backup_failed')
    snapshot=backup.get('snapshot')
    if snapshot is not None:
        if snapshot.get('sha256')!=digest(snapshot['payload']) or snapshot['payload']['state']['chain_id']!=31337:
            raise ValueError('Snapshot integrity or chain mismatch')
        backup_age=now-timestamp(snapshot['payload']['created_at'])
        if backup_age < -30 or backup_age > 900:reasons.append('backup_stale_or_future')
    else:reasons.append('snapshot_missing')
    return {'ok':not reasons,'reasons':reasons,'export_age_seconds':round(age,2),'staging_only':True},snapshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key',required=True);parser.add_argument('--known-hosts',required=True)
    parser.add_argument('--backup-directory',required=True);parser.add_argument('--ssh',default='ssh')
    args=parser.parse_args()
    try:
        result=subprocess.run([args.ssh,'-T','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',
            '-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=1',
            '-o','UserKnownHostsFile='+str(Path(args.known_hosts).resolve()),'-i',str(Path(args.key).resolve()),
            'zzz-stage-monitor@46.225.185.212','status'],capture_output=True,timeout=30)
        if result.returncode or len(result.stdout)>1048576:raise ValueError('Monitor connection/output failed')
        report,snapshot=validate_export(json.loads(result.stdout))
        if snapshot is not None:
            folder=Path(args.backup_directory);folder.mkdir(parents=True,exist_ok=True)
            target=folder/(snapshot['sha256']+'.json')
            raw=(json.dumps(snapshot,sort_keys=True,indent=2)+'\n').encode()
            if target.exists():
                if target.read_bytes()!=raw:raise ValueError('Existing off-host snapshot differs')
            else:
                fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
            report['offhost_snapshot_sha256']=hashlib.sha256(raw).hexdigest()
    except Exception as exc:report={'ok':False,'reasons':['monitor_unavailable'],**error_context(exc)}
    print(json.dumps(report,sort_keys=True));return 0 if report['ok'] else 1


if __name__=='__main__':sys.exit(main())
