"""Fixed c824 wrapper; opaque pinned transport, 2MiB compressed input/64KiB output."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,os,shlex,stat,subprocess,threading,time,zlib

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-reconstruction-20261127/private')
TRANSPORT=ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py'
TRANSPORT_SHA='a7f7f91863833bca9081b0ad6af833a1cf5147e65f1c2cfe7e058449f1bddc45'
MAX_CAPTURE=65536
BOOTSTRAP="""import sys,hashlib
sys.dont_write_bytecode=True
n=int.from_bytes(sys.stdin.buffer.read(4),'big');assert 0<n<=65536
code=sys.stdin.buffer.read(n);assert len(code)==n
expected=sys.argv[sys.argv.index('--controller-sha256')+1]
assert hashlib.sha256(code).hexdigest()==expected
exec(compile(code,'<fixed_c824_capsule>','exec'),{'__name__':'__main__','__file__':'<fixed_c824_capsule>'})
"""
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def private_path(path):
    original=path.absolute();root=PRIVATE.absolute();assert original.is_relative_to(root)
    for item in(*reversed(original.parents),original):
        if not item.is_relative_to(root):continue
        try:info=item.lstat()
        except FileNotFoundError:continue
        assert not stat.S_ISLNK(info.st_mode)and not getattr(info,'st_file_attributes',0)&0x400
    value=original.resolve();assert value.is_relative_to(PRIVATE.resolve());return value


def bounded(path,maximum=1048576):
    path=private_path(path);before=path.lstat()
    assert stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_size<=maximum
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    key=lambda item:(item.st_dev,item.st_ino,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns)
    with os.fdopen(fd,'rb')as stream:
        assert key(os.fstat(stream.fileno()))==key(before)
        raw=stream.read(maximum+1);named=private_path(path).lstat()
        assert key(os.fstat(stream.fileno()))==key(before)==key(named)and len(raw)==before.st_size<=maximum
    return raw


def write(path,raw):
    path=private_path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def capture(command,data,output):
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    lock=threading.Lock();overflow=threading.Event();counts=[0,0];errors=[]
    def drain(pipe,name,index):
        try:
            with(output/name).open('xb')as stream:
                while True:
                    chunk=pipe.read(16384)
                    if not chunk:break
                    with lock:
                        room=MAX_CAPTURE-sum(counts)
                        if len(chunk)>room:
                            if room>0:stream.write(chunk[:room]);counts[index]+=room
                            overflow.set();break
                        stream.write(chunk);counts[index]+=len(chunk)
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


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('export','install','start','status','stop','fetch'))
    p.add_argument('--mode',choices=('negative','complete'))
    p.add_argument('--artifact',choices=('RESULT-negative.json','RESULT-complete.json','INSTALL.json','FINAL.json'))
    p.add_argument('--kit',type=Path);p.add_argument('--desktop-proof',type=Path);p.add_argument('--proof-sha256')
    p.add_argument('--runtime-review',type=Path);p.add_argument('--runtime-review-sha256')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    approval=json.loads((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    for name in('remote_capsule.py','worker.py','host_control.py'):assert sha((BASE/name).read_bytes())==approval[name]
    assert sha(TRANSPORT.read_bytes())==TRANSPORT_SHA and PRIVATE.is_dir()
    output=private_path(a.output);assert not output.exists();output.mkdir(parents=True)
    controller=(BASE/'remote_capsule.py').read_bytes();assert 0<len(controller)<=65536
    args=['python3','-I','-S','-B','-c',BOOTSTRAP,a.action,'--controller-sha256',sha(controller)]
    data=len(controller).to_bytes(4,'big')+controller;wire_bytes=expanded_bytes=0
    if a.action=='start':assert a.mode is not None;args+=['--mode',a.mode]
    if a.action=='fetch':assert a.artifact is not None;args+=['--artifact',a.artifact]
    if a.action=='install':
        assert all(value is not None for value in(a.kit,a.desktop_proof,a.proof_sha256,a.runtime_review,a.runtime_review_sha256))
        proof=bounded(a.desktop_proof,16384);assert sha(proof)==a.proof_sha256;verified=json.loads(proof)
        assert verified['kind']=='popl-unsigned-recovery-kit-review'and verified['ok']is True and len(verified['files'])==49
        runtime=bounded(a.runtime_review,16384);assert sha(runtime)==a.runtime_review_sha256
        files={}
        for name,row in verified['files'].items():
            raw=bounded(private_path(a.kit)/name)
            assert len(raw)==row['bytes']and sha(raw)==row['sha256']
            files[name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
        packet=enc({'schema':1,'kind':'popl-keeper-reconstruction-import','files':files,
            'desktop_proof_base64':base64.b64encode(proof).decode('ascii')})
        assert 0<len(packet)<=2097152;wire=zlib.compress(packet,9);assert 0<len(wire)<=2097152
        expanded_bytes=len(packet);wire_bytes=len(wire);data+=wire
        args+=['--desktop-proof-sha256',a.proof_sha256,'--runtime-review-sha256',a.runtime_review_sha256]
    transport=module(TRANSPORT,'fixed_c824_opaque_transport');started=time.monotonic()
    code,reason,counts,errors=capture(transport.ssh()+[' '.join(map(shlex.quote,args))],data,output)
    receipt={'schema':1,'action':a.action,'mode':a.mode,'exit_code':code,'capture_reason':reason,'capture_errors':errors,
        'controller_sha256':sha(controller),'transport_sha256':TRANSPORT_SHA,'combined_output_limit':65536,
        'compressed_input_limit':2097152,'expanded_input_limit':2097152,'compressed_input_bytes':wire_bytes,'expanded_input_bytes':expanded_bytes,
        'stdout_bytes':counts[0],'stderr_bytes':counts[1],'elapsed_seconds':time.monotonic()-started,
        'opaque_SSH_transport':True,'signer_files_accessed':False,'raw_transport_kept_private':True,'only_fixed_c824_unit_control':True}
    for name in('stdout.raw','stderr.raw'):receipt[name+'_sha256']=sha((output/name).read_bytes())
    if code==0 and reason is None and not errors:
        response=json.loads((output/'stdout.raw').read_bytes())
        if a.action=='export':
            assert response['kind']=='popl-keeper-reconstruction-reference-export'
            assert set(response['files'])=={'references/keeper-config.json','references/policy.json'}
            metadata={}
            for name,row in response['files'].items():
                raw=base64.b64decode(row['raw_base64'],validate=True)
                assert len(raw)==row['bytes']and sha(raw)==row['sha256']and len(raw)<=65536
                write(output/name,raw);metadata[name]={'bytes':len(raw),'sha256':sha(raw)}
            runtime=enc(response['runtime_review']);assert len(runtime)<=16384 and sha(runtime)==response['runtime_review_sha256']
            write(output/'RUNTIME_REVIEW.json',runtime)
            write(output/'EXPORT_METADATA.json',enc({'schema':1,'references':metadata,
                'runtime_review_sha256':response['runtime_review_sha256'],'original_unchanged':response['original_unchanged'],
                'source_manifest_sha256':response['source_manifest_sha256'],'source_files_count':response['source_files_count'],
                'source_bodies_exported':False,'working_journal_exported':False,'signer_material_exported':False}))
        elif a.action=='fetch':
            raw=base64.b64decode(response['base64'],validate=True)
            assert response['name']==a.artifact and len(raw)==response['bytes']and sha(raw)==response['sha256'];write(output/a.artifact,raw)
        else:write(output/'SANITIZED_RESULT.json',enc(response))
    write(output/'EXECUTION.json',enc(receipt));print(json.dumps(receipt,sort_keys=True))
    return 0 if code==0 and reason is None and not errors else 1


if __name__=='__main__':raise SystemExit(main())
