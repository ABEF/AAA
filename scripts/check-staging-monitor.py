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
import re
import stat
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from keeper.monitor import error_context
from keeper.ops import digest,timestamp
from zzz_ops.read_process import run_read_process

MAX_SNAPSHOT_BYTES=1048576
MAX_ARCHIVE_FILES=10000


def archive_snapshot(snapshot,folder):
    if (type(snapshot)is not dict or type(snapshot.get('sha256'))is not str
            or re.fullmatch('[0-9a-f]{64}',snapshot['sha256'])is None
            or type(snapshot.get('payload'))is not dict or snapshot['sha256']!=digest(snapshot['payload'])):
        raise ValueError('Invalid off-host snapshot digest')
    raw=(json.dumps(snapshot,sort_keys=True,indent=2)+'\n').encode()
    if len(raw)>MAX_SNAPSHOT_BYTES:raise ValueError('Off-host snapshot exceeds storage bound')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    directory=folder.lstat()
    if (not stat.S_ISDIR(directory.st_mode) or stat.S_ISLNK(directory.st_mode)
            or getattr(directory,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)):
        raise ValueError('Invalid off-host archive directory')
    target=folder/(snapshot['sha256']+'.json')
    try:before=target.lstat()
    except FileNotFoundError:before=None
    if before is not None:
        identity=lambda item:(item.st_dev,item.st_ino,item.st_mode,item.st_nlink,
            item.st_size,item.st_mtime_ns)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size!=len(raw)
                or getattr(before,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)):
            raise ValueError('Invalid existing off-host snapshot')
        flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
        fd=os.open(target,flags)
        with os.fdopen(fd,'rb')as handle:
            opened=os.fstat(handle.fileno())
            if identity(opened)!=identity(before):raise ValueError('Off-host snapshot changed')
            saved=handle.read(len(raw)+1)
            after_fd=os.fstat(handle.fileno());after_path=target.lstat()
            # Windows path/fd ctime semantics differ; compare each API to itself.
            if (identity(after_fd)!=identity(before) or identity(after_path)!=identity(before)
                    or after_fd.st_ctime_ns!=opened.st_ctime_ns or after_path.st_ctime_ns!=before.st_ctime_ns
                    or saved!=raw):raise ValueError('Existing off-host snapshot differs or changed')
    else:
        count=0
        with os.scandir(folder)as entries:
            for _ in entries:
                count+=1
                if count>=MAX_ARCHIVE_FILES:raise ValueError('Off-host retention budget requires operator review')
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb')as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
    return hashlib.sha256(raw).hexdigest()


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
        result=run_read_process([args.ssh,'-T','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',
            '-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=1',
            '-o','UserKnownHostsFile='+str(Path(args.known_hosts).resolve()),'-i',str(Path(args.key).resolve()),
            'zzz-stage-monitor@46.225.185.212','status'],timeout=30)
        if result.returncode or len(result.stdout)>1048576:raise ValueError('Monitor connection/output failed')
        report,snapshot=validate_export(json.loads(result.stdout))
        if snapshot is not None:
            report['offhost_snapshot_sha256']=archive_snapshot(snapshot,args.backup_directory)
    except Exception as exc:report={'ok':False,'reasons':['monitor_unavailable'],**error_context(exc)}
    print(json.dumps(report,sort_keys=True));return 0 if report['ok'] else 1


if __name__=='__main__':sys.exit(main())
