"""Fixed c804/c805/c806 stopped-journal capture. Import is inert; root runs explicitly.

Only the pinned opaque strict_transport.ssh() supplies transport arguments.
No key/password/configuration or other journal is read or exported.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import threading
import time

V = Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE = V / 'ubuntu-supervisor-20261125'
CAMPAIGN = BASE / 'campaign'
ROOT = Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
TRANSPORT = ROOT / 'reports/ubuntu-keeper-20261121/transport/strict_transport.py'
MAX_CAPTURE = 16 * 1024 * 1024
MAX_JOURNAL = 2 * 1024 * 1024

REMOTE = r'''
from pathlib import Path, PurePosixPath
import base64,hashlib,json,os,re,selectors,signal,stat,subprocess,sys,time
deadline=time.monotonic()+35
def need(value,message):
 if not value:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def checkpoint():need(time.monotonic()<deadline,'Final read-only work deadline')
pins=json.loads(base64.b64decode(sys.argv[1],validate=True))
variant=pins['variant'];need(variant in('body','signer'),'Fixed final variant required')
allowed={'body':('/opt/popl-ubuntu-supervisor-20261125-c804',),
 'signer':('/opt/popl-ubuntu-supervisor-20261125-c805','/opt/popl-ubuntu-supervisor-20261125-c806')}
need(pins['lab']in allowed[variant],'Closed final lab set differs')
LAB=Path(pins['lab'])
UNITS=tuple(LAB.name+'-'+name+'.service'for name in('model','keeper','resolve'))
STOP_UNITS=tuple('popl-ubuntu-supervisor-20261125-'+tag+'-'+name+'.service'
 for tag in('c804','c805','c806')for name in('model','keeper','resolve'))
LIVE=LAB/'runtime/run-001/model/supervisor/actor/state.json'
need(os.name=='posix'and os.geteuid()==0,'Root final read required')
need(pins['lab']==str(LAB),'Fixed final lab differs')
for key in('controller_sha256','manifest_sha256','bundle_sha256','source_manifest_sha256','native_sha256'):
 need(type(pins[key])is str and re.fullmatch('[0-9a-f]{64}',pins[key]),'Final source pin differs')
def read(path,maximum,owners=(0,),mode=None,expected=None):
 checkpoint();need(path.is_absolute(),'Absolute final path required');opened=[]
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);opened.append(fd)
  for part in path.parts[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);opened.append(fd)
   item=os.fstat(fd);need(stat.S_ISDIR(item.st_mode)and item.st_uid in owners and not item.st_mode&0o022,'Unsafe final parent')
  parent=fd;fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);opened.append(fd)
  before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and before.st_uid in owners and before.st_nlink==1 and not before.st_mode&0o022 and 0<=before.st_size<=maximum,'Unsafe final file')
  if mode is not None:need(stat.S_IMODE(before.st_mode)==mode,'Final file mode differs')
  parts=[];size=0
  while True:
   checkpoint();part=os.read(fd,min(65536,maximum+1-size))
   if not part:break
   size+=len(part);need(size<=maximum,'Final read byte bound');parts.append(part)
  after=os.fstat(fd);current=os.stat(path.name,dir_fd=parent,follow_symlinks=False)
  identity=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(identity(before)==identity(after)==identity(current)and size==before.st_size,'Final file changed during read')
  raw=b''.join(parts)
  if expected is not None:need(sha(raw)==expected,'Final file source pin differs')
  return raw,{'uid':before.st_uid,'mode':oct(stat.S_IMODE(before.st_mode)),'dev':before.st_dev,'ino':before.st_ino,'bytes':size,'sha256':sha(raw)}
 finally:
  for fd in reversed(opened):os.close(fd)
def run(argv):
 checkpoint();end=min(deadline,time.monotonic()+4)
 child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'})
 chunks=[bytearray(),bytearray()];size=0;finished=False
 try:
  with selectors.DefaultSelector()as poll:
   for n,pipe in enumerate((child.stdout,child.stderr)):os.set_blocking(pipe.fileno(),False);poll.register(pipe,selectors.EVENT_READ,n)
   while poll.get_map():
    need(time.monotonic()<end,'Final process read deadline')
    for key,_ in poll.select(max(.001,end-time.monotonic())):
     part=os.read(key.fd,min(8192,131073-size))
     if not part:poll.unregister(key.fileobj);continue
     size+=len(part);need(size<=131072,'Final process output bound');chunks[key.data].extend(part)
  need(time.monotonic()<end,'Final process completion deadline');code=child.wait(timeout=max(.001,end-time.monotonic()));finished=True
  return code,bytes(chunks[0]),bytes(chunks[1])
 finally:
  if not finished:
   try:os.killpg(child.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   child.wait(timeout=2)
  child.stdout.close();child.stderr.close()
def census(unit):
 root=Path('/sys/fs/cgroup/system.slice')/unit;pending=[root];groups=[];pids=set()
 while pending:
  checkpoint();path=pending.pop()
  try:item=path.lstat()
  except FileNotFoundError:continue
  need(stat.S_ISDIR(item.st_mode)and not path.is_symlink()and path.is_relative_to(root),'Final cgroup identity differs')
  groups.append(str(path.relative_to(root)));need(len(groups)<=64,'Final cgroup count bound')
  try:
   raw=(path/'cgroup.procs').read_bytes();need(len(raw)<=16384,'Final cgroup process byte bound')
   pids.update(int(n)for n in raw.splitlines());need(len(pids)<=256,'Final cgroup PID count bound')
   for entry in path.iterdir():
    if stat.S_ISDIR(entry.lstat().st_mode):pending.append(entry)
  except FileNotFoundError:pass
 return {'fixed_path':'/system.slice/'+unit,'exists':root.exists(),'groups':groups,'pids':sorted(pids)}
def stopped():
 result={}
 for unit in STOP_UNITS:
  code,out,_=run(['/usr/bin/systemctl','show',unit,'--no-pager','--property=Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainStatus,InvocationID,NRestarts'])
  values=dict(line.split('=',1)for line in out.decode('utf-8','strict').splitlines()if'='in line)
  need(code==0 or values.get('LoadState')=='not-found','Final unit inspection refused')
  need(values.get('Id',unit)==unit and values.get('ActiveState')in('inactive','failed',None)and int(values.get('MainPID','0'))==0,'Final owned unit is not stopped')
  need(not values.get('ControlGroup')or values['ControlGroup']=='/system.slice/'+unit,'Final owned cgroup differs')
  group=census(unit);need(not group['pids'],'Final owned cgroup is not empty')
  result[unit]={'properties':values,'cgroup':group}
 return result
labstat=LAB.lstat();need(stat.S_ISDIR(labstat.st_mode)and labstat.st_uid==0 and not labstat.st_mode&0o022,'Final lab root ownership differs')
markerraw,_=read(LAB/'LAB_ID.json',16384);marker=json.loads(markerraw)
need(marker.get('lab')==str(LAB)and marker.get('unit')==UNITS[0]and
 marker.get('controller_sha256')==pins['controller_sha256']and marker.get('bundle_sha256')==pins['bundle_sha256']and
 marker.get('source_manifest_sha256')==pins['manifest_sha256']and marker.get('source_identity_manifest_sha256')==pins['source_manifest_sha256'],
 'Final root lab marker/source identity differs')
manifest_raw,_=read(LAB/'MANIFEST.json',2*1024*1024,expected=pins['manifest_sha256']);manifest=json.loads(manifest_raw)
source_raw,_=read(LAB/'inputs/SOURCE_MANIFEST.json',2*1024*1024,expected=pins['source_manifest_sha256']);source=json.loads(source_raw)
need(source.get('source_head')=='7f862557df8e8cbaf8494c7b1c12f18e07be436d'and len(source.get('members',{}))==190,'Final production source scope differs')
native_pin=manifest['members']['source/helpers/native_control.py']
need(native_pin['sha256']==pins['native_sha256'],'Final native manifest pin differs')
read(LAB/'source/helpers/native_control.py',2*1024*1024,expected=pins['native_sha256'])
before=stopped()
raw,identity=read(LIVE,2*1024*1024,owners=(0,65534),mode=0o600)
need(identity['uid']==65534,'Final journal owner differs')
state=json.loads(raw);need(type(state)is dict and state.get('chain_id')==4663 and state.get('accounting_version')==7 and
 type(state.get('sender'))is str and re.fullmatch('0x[0-9a-f]{40}',state['sender'])and
 type(state.get('contracts'))is dict and type(state.get('spent'))is dict and
 type(state.get('next_nonce'))is int and 'pending'in state,'Final journal shape differs')
def no_secrets(value):
 if type(value)is dict:
  need(not(set(value)&{'private_key','privateKey','password','password_file','keystore','mnemonic','rpc_urls','rpc_url','secret'}),'Final journal contains prohibited material')
  for child in value.values():no_secrets(child)
 elif type(value)is list:
  for child in value:no_secrets(child)
no_secrets(state)
after=stopped();again,again_identity=read(LIVE,2*1024*1024,owners=(0,65534),mode=0o600)
need(raw==again and identity==again_identity,'Final stopped journal changed')
print(json.dumps({'schema':1,'phase':'final_stopped_journal','variant':variant,'lab':str(LAB),
 'journal_path':str(LIVE),'journal':identity,'journal_base64':base64.b64encode(raw).decode('ascii'),
 'units_before':before,'units_after':after,'all_fixed_owned_units_stopped':True,'all_fixed_owned_cgroups_empty':True,
 'pins':pins,'root_marker_sha256':sha(markerraw),'read_only':True,'only_exact_public_journal_exported':True},sort_keys=True))
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bounded_capture(argv, stdin, output):
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, close_fds=True)
    lock, overflow = threading.Lock(), threading.Event()
    counts, errors = [0, 0], []

    def drain(pipe, name, index):
        try:
            with (output / name).open('xb') as stream:
                while True:
                    part = pipe.read(16384)
                    if not part:
                        break
                    with lock:
                        room = MAX_CAPTURE - sum(counts)
                        if len(part) > room:
                            if room > 0:
                                stream.write(part[:room])
                                counts[index] += room
                            overflow.set()
                            break
                        stream.write(part)
                        counts[index] += len(part)
        except BaseException:
            errors.append('bounded_capture_failed')
            overflow.set()
        finally:
            pipe.close()

    def send():
        try:
            child.stdin.write(stdin)
            child.stdin.flush()
        except (BrokenPipeError, OSError):
            errors.append('input_closed')
        finally:
            try:
                child.stdin.close()
            except OSError:
                pass

    threads = [threading.Thread(target=drain, args=(child.stdout, 'stdout.raw', 0), daemon=True),
               threading.Thread(target=drain, args=(child.stderr, 'stderr.raw', 1), daemon=True),
               threading.Thread(target=send, daemon=True)]
    for thread in threads:
        thread.start()
    end, reason = time.monotonic() + 45, None
    while child.poll() is None:
        if overflow.is_set():
            reason = 'combined_output_limit'
            child.kill()
            break
        if time.monotonic() >= end:
            reason = '45second_transport_deadline'
            child.kill()
            break
        time.sleep(.05)
    try:
        child.wait(timeout=2)
    except subprocess.TimeoutExpired:
        reason = 'bounded_cleanup_failed'
        child.kill()
    cleanup_end = time.monotonic() + 2
    for thread in threads:
        thread.join(max(0, cleanup_end - time.monotonic()))
    if any(thread.is_alive() for thread in threads):
        reason = 'bounded_pipe_cleanup_failed'
    return child.returncode, reason, counts, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('body', 'signer'), required=True)
    parser.add_argument('--build-sha256', required=True)
    parser.add_argument('--transport-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for value in (args.build_sha256, args.transport_sha256):
        assert re.fullmatch('[0-9a-f]{64}', value)
    output = args.output.resolve()
    assert output.is_relative_to(CAMPAIGN.resolve()) and output != CAMPAIGN.resolve()
    assert not output.exists() and not output.is_symlink()
    source = BASE / args.variant
    build_raw = (source / 'BUILD_RECEIPT.json').read_bytes()
    assert len(build_raw) <= 2 * 1024 * 1024 and sha(build_raw) == args.build_sha256
    build = json.loads(build_raw)
    controller = (source / 'remote_capsule.py').read_bytes()
    assert len(controller) == build['controller']['bytes'] and sha(controller) == build['controller']['sha256']
    transport_raw = TRANSPORT.read_bytes()
    assert len(transport_raw) <= 128 * 1024 and sha(transport_raw) == args.transport_sha256
    allowed = {'body': ('/opt/popl-ubuntu-supervisor-20261125-c804',),
               'signer': ('/opt/popl-ubuntu-supervisor-20261125-c805',
                          '/opt/popl-ubuntu-supervisor-20261125-c806')}
    lab = build['lab']
    assert lab in allowed[args.variant]
    pins = {'variant': args.variant, 'lab': lab,
            'controller_sha256': build['controller']['sha256'],
            'manifest_sha256': build['manifest']['sha256'],
            'bundle_sha256': build['bundle']['sha256'],
            'source_manifest_sha256': build['source_manifest_sha256'],
            'native_sha256': build['helpers']['native_control.py']['sha256']}
    spec = importlib.util.spec_from_file_location('opaque_pinned_final_transport', TRANSPORT)
    transport = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(transport)
    encoded = base64.b64encode(json.dumps(pins, sort_keys=True).encode()).decode('ascii')
    argv = transport.ssh() + ['python3 - ' + shlex.quote(encoded)]
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    code, reason, counts, errors = bounded_capture(argv, REMOTE.encode('utf-8'), output)
    receipt = {'schema': 1, 'variant': args.variant, 'exit_code': code,
               'capture_failure': reason, 'capture_errors': errors,
               'elapsed_seconds': time.monotonic() - started,
               'deadline_seconds': 45, 'maximum_combined_output_bytes': MAX_CAPTURE,
               'stdout_bytes': counts[0], 'stderr_bytes': counts[1],
               'build_receipt_sha256': args.build_sha256,
               'transport_source_sha256': args.transport_sha256,
               'remote_readonly_source_sha256': sha(REMOTE.encode('utf-8')),
               'only_fixed_public_journal_requested': True, 'pins': pins}
    for name in ('stdout.raw', 'stderr.raw'):
        receipt[name + '_sha256'] = sha((output / name).read_bytes())
    if code == 0 and reason is None:
        response = json.loads((output / 'stdout.raw').read_bytes())
        assert response['phase'] == 'final_stopped_journal' and response['pins'] == pins
        assert response['all_fixed_owned_units_stopped'] is True and response['all_fixed_owned_cgroups_empty'] is True
        raw = base64.b64decode(response.pop('journal_base64'), validate=True)
        assert 0 < len(raw) <= MAX_JOURNAL and len(raw) == response['journal']['bytes']
        assert sha(raw) == response['journal']['sha256']
        with (output / 'FINAL_JOURNAL.raw').open('xb') as stream:
            stream.write(raw)
        with (output / 'PUBLIC_RESULT.json').open('x', encoding='utf-8') as stream:
            json.dump(response, stream, indent=2, sort_keys=True)
            stream.write('\n')
        receipt['journal_sha256'] = sha(raw)
        receipt['journal_bytes'] = len(raw)
    with (output / 'EXECUTION.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(receipt, sort_keys=True))
    return code if reason is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
