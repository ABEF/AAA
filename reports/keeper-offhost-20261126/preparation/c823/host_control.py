"""Fixed c823 action wrapper; reviewed sources only, opaque pinned SSH transport."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,os,shlex,stat,subprocess,threading,time

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
TRANSPORT=ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py'
TRANSPORT_SHA='a7f7f91863833bca9081b0ad6af833a1cf5147e65f1c2cfe7e058449f1bddc45'
MAX_CAPTURE=65536
BOOTSTRAP="""import sys,hashlib
n=int.from_bytes(sys.stdin.buffer.read(4),'big');assert 0<n<=65536
code=sys.stdin.buffer.read(n);assert len(code)==n
expected=sys.argv[sys.argv.index('--controller-sha256')+1]
assert hashlib.sha256(code).hexdigest()==expected
exec(compile(code,'<fixed_c823_capsule>','exec'),{'__name__':'__main__','__file__':'<fixed_c823_capsule>'})
"""
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def capture(command,data,output):
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    lock=threading.Lock();overflow=threading.Event();counts=[0,0];errors=[]
    def drain(pipe,name,index):
        try:
            with(output/name).open('xb')as f:
                while True:
                    chunk=pipe.read(16384)
                    if not chunk:break
                    with lock:
                        room=MAX_CAPTURE-sum(counts)
                        if len(chunk)>room:
                            if room>0:f.write(chunk[:room]);counts[index]+=room
                            overflow.set();break
                        f.write(chunk);counts[index]+=len(chunk)
        except BaseException:errors.append('capture_failed');overflow.set()
        finally:pipe.close()
    def send():
        try:process.stdin.write(data);process.stdin.flush()
        except(BrokenPipeError,OSError):errors.append('input_closed')
        finally:
            try:process.stdin.close()
            except OSError:pass
    threads=[threading.Thread(target=drain,args=(process.stdout,'stdout.raw',0),daemon=True),
        threading.Thread(target=drain,args=(process.stderr,'stderr.raw',1),daemon=True),threading.Thread(target=send,daemon=True)]
    for thread in threads:thread.start()
    deadline=time.monotonic()+45;reason=None
    while process.poll()is None:
        if overflow.is_set():reason='combined_output_limit';process.kill();break
        if time.monotonic()>=deadline:reason='action_timeout';process.kill();break
        time.sleep(.05)
    try:process.wait(timeout=2)
    except subprocess.TimeoutExpired:reason='cleanup_timeout';process.kill()
    for thread in threads:thread.join(2)
    if any(thread.is_alive()for thread in threads):reason='pipe_cleanup_timeout'
    return process.returncode,reason,counts,errors

PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-offhost-20261126/private')
NAMES=('manifest.json','selection.json','alert-state.json','selected/manifest.json','selected/journal.json')
OUTER='a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'


def private_path(path):
    original=path.absolute();root=PRIVATE.absolute();assert original.is_relative_to(root)
    for item in (*reversed(original.parents),original):
        if not item.is_relative_to(root):continue
        try:info=item.lstat()
        except FileNotFoundError:continue
        assert not stat.S_ISLNK(info.st_mode)and not getattr(info,'st_file_attributes',0)&0x400
    value=original.resolve();assert value.is_relative_to(PRIVATE.resolve());return value


def bounded(path,maximum=65536):
    path=private_path(path);before=path.lstat()
    assert stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_size<=maximum
    flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(path,flags)
    key=lambda item:(item.st_dev,item.st_ino,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns)
    with os.fdopen(fd,'rb')as stream:
        assert key(os.fstat(stream.fileno()))==key(before)
        raw=stream.read(maximum+1);named=private_path(path).lstat()
        assert key(os.fstat(stream.fileno()))==key(before)==key(named)and len(raw)==before.st_size<=maximum
    return raw


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('export','install','start','status','stop','fetch'))
    p.add_argument('--artifact',choices=('RESULT.json','PROGRESS.json','FINAL.json','INSTALL.json'))
    p.add_argument('--package',type=Path);p.add_argument('--desktop-proof',type=Path);p.add_argument('--proof-sha256')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    approval=json.loads((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    for name in ('remote_capsule.py','worker.py','host_control.py'):assert sha((BASE/name).read_bytes())==approval[name]
    assert sha(TRANSPORT.read_bytes())==TRANSPORT_SHA and PRIVATE.is_dir()
    output=private_path(a.output);assert not output.exists();output.mkdir(parents=True,**({}if os.name=='nt'else{'mode':0o700}))
    controller=(BASE/'remote_capsule.py').read_bytes();assert 0<len(controller)<=65536
    args=['python3','-c',BOOTSTRAP,a.action,'--controller-sha256',sha(controller)]
    data=len(controller).to_bytes(4,'big')+controller;wire_bytes=0
    if a.action=='fetch':assert a.artifact is not None;args+=['--artifact',a.artifact]
    if a.action=='install':
        assert a.package is not None and a.desktop_proof is not None and a.proof_sha256 is not None
        package=private_path(a.package);proof=bounded(private_path(a.desktop_proof),8192)
        assert sha(proof)==a.proof_sha256
        files={}
        for name in NAMES:
            raw=bounded(package/name);files[name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
        assert files['manifest.json']['sha256']==OUTER
        wire=json.dumps({'schema':1,'kind':'popl-keeper-offhost-import','files':files,
            'desktop_proof_base64':base64.b64encode(proof).decode('ascii')},sort_keys=True,separators=(',',':')).encode()
        assert 0<len(wire)<=65536;wire_bytes=len(wire);data+=wire
        args+=['--desktop-proof-sha256',a.proof_sha256]
    transport=module(TRANSPORT,'fixed_c823_opaque_transport');started=time.monotonic()
    code,reason,counts,errors=capture(transport.ssh()+[' '.join(map(shlex.quote,args))],data,output)
    receipt={'schema':1,'action':a.action,'exit_code':code,'capture_reason':reason,'capture_errors':errors,
        'controller_sha256':sha(controller),'transport_sha256':TRANSPORT_SHA,'combined_output_limit':65536,
        'stdout_bytes':counts[0],'stderr_bytes':counts[1],'input_wire_bytes':wire_bytes,
        'elapsed_seconds':time.monotonic()-started,'opaque_SSH_transport':True,
        'host_wrapper_signer_files_accessed':False,'production_signer_material_read_or_exported':False,
        'raw_transport_kept_private':True,'only_fixed_c823_unit_control':True}
    for name in ('stdout.raw','stderr.raw'):receipt[name+'_sha256']=sha((output/name).read_bytes())
    if code==0 and reason is None and not errors:
        response=json.loads((output/'stdout.raw').read_bytes())
        if a.action=='export':
            assert response['kind']=='popl-keeper-offhost-export'and set(response['files'])==set(NAMES)
            exported=output/'package';exported.mkdir(**({}if os.name=='nt'else{'mode':0o700}));(exported/'selected').mkdir(**({}if os.name=='nt'else{'mode':0o700}))
            filepins={}
            for name in NAMES:
                row=response['files'][name];raw=base64.b64decode(row['raw_base64'],validate=True)
                assert len(raw)==row['bytes']and sha(raw)==row['sha256']and len(raw)<=65536
                with(exported/name).open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
                filepins[name]={'bytes':len(raw),'sha256':sha(raw)}
            assert filepins['manifest.json']['sha256']==OUTER
            # Explicit metadata allowlist. Never label the raw response PUBLIC.
            metadata={'schema':1,'files':filepins,'response_bytes':counts[0],
                'response_sha256':receipt['stdout.raw_sha256'],
                'original_fenced_before_and_after':response['original_fenced_before_and_after'],
                'original_reference_snapshot_sha256':response['original_reference_snapshot_sha256'],
                'source_trust_report_sha256':response['source_trust_report_sha256'],
                'original_files_unchanged':response['original_files_unchanged'],
                'policy_configuration_and_signer_material_exported':response['policy_configuration_and_signer_material_exported'],
                'raw_files_stay_private':True}
            with(output/'EXPORT_METADATA.json').open('x',encoding='utf8')as stream:json.dump(metadata,stream,indent=2,sort_keys=True);stream.write('\n')
        elif a.action=='fetch':
            raw=base64.b64decode(response['base64'],validate=True)
            assert response['name']==a.artifact and len(raw)==response['bytes']and sha(raw)==response['sha256']
            with(output/a.artifact).open('xb')as stream:stream.write(raw)
        else:
            with(output/'SANITIZED_RESULT.json').open('x',encoding='utf8')as stream:json.dump(response,stream,indent=2,sort_keys=True);stream.write('\n')
    with(output/'EXECUTION.json').open('x',encoding='utf8')as stream:json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(receipt,sort_keys=True));return 0 if code==0 and reason is None and not errors else 1


if __name__=='__main__':raise SystemExit(main())
