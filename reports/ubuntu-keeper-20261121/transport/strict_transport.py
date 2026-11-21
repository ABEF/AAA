"""Strict pinned SSH for reviewed public capsules; no credential export or shell input."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import re
import shlex
import subprocess
import tarfile

V = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
SSH = 'C:/Windows/System32/OpenSSH/ssh.exe'
MAX = 32 * 1024 * 1024
CONTROLLER = 'source/reports/ubuntu-keeper-20261121/run/capsule.py'
ACTIONS = ('install', 'key', 'start-preflight', 'bootstrap', 'preflight', 'stop-preflight',
           'start-final', 'initialize', 'live', 'sample', 'lock-contender', 'kill-keeper',
           'stop-keeper', 'fault', 'freeze', 'cache-events', 'stop',
           'hold-mining', 'resume-mining', 'await-pending', 'proof')
TIMEOUTS = {'preflight': 230, 'initialize': 180, 'bootstrap': 180,
            'stop': 160, 'stop-preflight': 160, 'stop-keeper': 160,
            'await-pending': 70, 'start-preflight': 90, 'start-final': 90,
            'key': 90, 'live': 90, 'proof': 60}
UPLOAD = '''import sys,os,re,hashlib,json
path,expected,length=sys.argv[1:];length=int(length)
assert os.geteuid()==0 and re.fullmatch(r'/tmp/popl-ubuntu-20261121-[0-9a-f]{8}\\.(inputs\\.tar\\.gz|cache\\.json)',path)
assert re.fullmatch('[0-9a-f]{64}',expected) and 0<length<=33554432
data=sys.stdin.buffer.read(33554433)
assert len(data)==length and hashlib.sha256(data).hexdigest()==expected
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
print(json.dumps({'uploaded':path,'sha256':expected,'bytes':length,'only_new_file':True}))
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ssh():
    key = V/'poplint-ops-credentials/id_ed25519'
    known = V/'website-todo-20261016/staging-monitor/known_hosts'
    assert key.is_file() and known.is_file()
    return [SSH, '-F', 'NUL', '-T', '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
            '-o', 'IdentityAgent=none', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
            '-o', 'GlobalKnownHostsFile=NUL', '-o', 'UserKnownHostsFile='+str(known),
            '-o', 'ConnectTimeout=10', '-o', 'ConnectionAttempts=1', '-o', 'ServerAliveInterval=5',
            '-o', 'ServerAliveCountMax=1', '-o', 'ClearAllForwardings=yes', '-i', str(key), 'root@46.225.185.212']


def bundle(path):
    assert path.is_file() and not path.is_symlink() and 0<path.stat().st_size<=MAX
    raw=path.read_bytes(); receipt=json.loads(path.with_name('BUNDLE.json').read_bytes())
    assert sha(raw)==receipt['archive_sha256'] and len(raw)==receipt['archive_bytes']
    assert receipt['private_data_included'] is False
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        entries=archive.getmembers(); names=[e.name for e in entries]
        assert len(names)==len(set(names))<=1000 and sum(e.size for e in entries)<=64*1024*1024
        for e in entries:
            assert e.isfile() and e.name==str(PurePosixPath(e.name))
            assert not e.name.startswith('/') and '..'not in PurePosixPath(e.name).parts and '\\'not in e.name and ':'not in e.name
        manifest=json.loads(archive.extractfile('INPUT_MANIFEST.json').read())
        assert manifest==receipt['manifest'] and manifest['credential_members']==0
        assert set(names)==set(manifest['members'])|{'INPUT_MANIFEST.json'}
        for name,pin in manifest['members'].items():
            data=archive.extractfile(name).read();assert len(data)==pin['bytes'] and sha(data)==pin['sha256']
        controller=archive.extractfile(CONTROLLER).read()
        assert sha(controller)==manifest['members'][CONTROLLER]['sha256']
    return raw,receipt,controller


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True,type=Path)
    p.add_argument('--lab',required=True);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--action',required=True,choices=('upload',*ACTIONS))
    p.add_argument('--cache',type=Path);p.add_argument('--sha256')
    p.add_argument('--primary',choices=('healthy','outage','body_trickle'),default='healthy')
    p.add_argument('--secondary',choices=('healthy','outage','body_trickle'),default='healthy')
    a=p.parse_args();assert re.fullmatch('/opt/popl-ubuntu-20261121-[0-9a-f]{8}',a.lab)
    assert a.output.resolve().is_relative_to(V/'ubuntu-keeper-20261121')
    a.output.mkdir(parents=True,exist_ok=False)
    raw,receipt,controller=bundle(a.bundle)
    stem='/tmp/'+a.lab.rsplit('/',1)[1]; remote_file=stem+'.inputs.tar.gz'
    if a.action=='upload':
        data=raw
        if a.cache:
            assert a.cache.is_file() and 0<a.cache.stat().st_size<=MAX
            data=a.cache.read_bytes();assert sha(data)==a.sha256
            cache=json.loads(data);assert cache['anchor_number']==119107223 and cache['anchor_hash']=='0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335'
            assert isinstance(cache['entries'],dict);remote_file=stem+'.cache.json'
        remote='python3 -c '+shlex.quote(UPLOAD)+' '+shlex.quote(remote_file)+' '+sha(data)+' '+str(len(data))
    else:
        argv=['python3','-','--lab',a.lab,a.action]
        if a.action=='install':argv+=['--bundle',remote_file,'--sha256',receipt['archive_sha256']]
        if a.action=='freeze':
            assert re.fullmatch('[0-9a-f]{64}',a.sha256 or'')
            argv+=['--bundle',stem+'.cache.json','--sha256',a.sha256]
        if a.action=='fault':argv+=['--primary',a.primary,'--secondary',a.secondary]
        remote=' '.join(shlex.quote(x)for x in argv);data=controller
    timeout=TIMEOUTS.get(a.action,30)
    result=subprocess.run([*ssh(),remote],input=data,capture_output=True,timeout=timeout)
    assert len(result.stdout)<=8*1024*1024 and len(result.stderr)<=1024*1024
    if a.action=='key':
        # Only this fixed public result schema may leave the key-generation controller.
        public=json.loads(result.stdout) if result.returncode==0 else {'exit_code':result.returncode,'key_output_discarded':True}
        if result.returncode==0:assert set(public)=={'phase','sender','secret_exported','mode','uid','rpc_urls_fixed'}and public['secret_exported']is False
        (a.output/'stdout.json').write_bytes((json.dumps(public,indent=2)+'\n').encode())
    else:
        (a.output/'stdout.raw').write_bytes(result.stdout);(a.output/'stderr.raw').write_bytes(result.stderr)
    record={'schema':1,'action':a.action,'lab':a.lab,'exit_code':result.returncode,
            'bundle_sha256':receipt['archive_sha256'],'controller_sha256':sha(controller),
            'transport_source_sha256':sha(Path(__file__).read_bytes()),'timeout_seconds':timeout,
            'output_sha256':sha(result.stdout),'output_bytes':len(result.stdout),
            'private_key_contents_exported':False,'strict_pinned_host':True,'only_owned_paths':True}
    (a.output/'EXECUTION.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
    print(json.dumps(record));return result.returncode


if __name__=='__main__':raise SystemExit(main())
