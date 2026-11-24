"""Action-only wrapper for a fixed owned Ubuntu lab; credentials stay opaque.

This file never prints transport arguments, key/password bytes or configured
credential contents. Import only strict_transport.ssh(), not its older main().
Upload/start require separate explicit invocation; inspecting this file does none.
"""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,os,shlex,subprocess,threading,time

ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-hybrid-20261124/hybrid')
TRANSPORT=ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py'
CAPSULE=BASE/'remote_capsule.py'
MAX_CAPTURE=16*1024*1024
UPLOAD_SOURCE=r"""import sys,os,hashlib,json,re
path='/tmp/popl-ubuntu-hybrid-20261124-c7ff.inputs.tar.gz'
expected,length=sys.argv[1:];length=int(length)
assert os.geteuid()==0 and re.fullmatch('[0-9a-f]{64}',expected) and 0<length<=96*1024*1024
data=sys.stdin.buffer.read(96*1024*1024+1)
assert len(data)==length and hashlib.sha256(data).hexdigest()==expected
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
print(json.dumps({'phase':'uploaded','path':path,'bytes':length,'sha256':expected,'exclusive_new_file':True,'existing_services_changed':False}))
"""

def sha(data):return hashlib.sha256(data).hexdigest()

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def captured(command,data,output,timeout):
    # Both pipes are drained under one byte ceiling; no unbounded communicate().
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    lock=threading.Lock();limit=threading.Event();counts=[0,0];errors=[]
    def drain(pipe,name,index):
        try:
            with (output/name).open('xb')as stream:
                while True:
                    chunk=pipe.read(16384)
                    if not chunk:break
                    with lock:
                        room=MAX_CAPTURE-sum(counts)
                        if len(chunk)>room:
                            if room>0:stream.write(chunk[:room]);counts[index]+=room
                            limit.set();break
                        stream.write(chunk);counts[index]+=len(chunk)
        except BaseException:errors.append('capture_failed');limit.set()
        finally:pipe.close()
    def send():
        try:process.stdin.write(data);process.stdin.flush()
        except (BrokenPipeError,OSError):errors.append('input_closed')
        finally:
            try:process.stdin.close()
            except OSError:pass
    readers=[threading.Thread(target=drain,args=(process.stdout,'stdout.raw',0),daemon=True),threading.Thread(target=drain,args=(process.stderr,'stderr.raw',1),daemon=True)]
    writer=threading.Thread(target=send,daemon=True)
    for thread in readers+[writer]:thread.start()
    deadline=time.monotonic()+timeout;reason=None
    while process.poll()is None:
        if limit.is_set():reason='output_limit';process.kill();break
        if time.monotonic()>=deadline:reason='timeout';process.kill();break
        time.sleep(.05)
    try:process.wait(timeout=2)
    except subprocess.TimeoutExpired:reason='cleanup_timeout';process.kill()
    for thread in readers+[writer]:thread.join(2)
    if any(thread.is_alive()for thread in readers+[writer]):reason='pipe_cleanup_timeout'
    return process.returncode,reason,counts,errors

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('validate-bundle','upload','install','start','status','stop','fetch'))
    parser.add_argument('--bundle',type=Path);parser.add_argument('--bundle-sha256')
    parser.add_argument('--attempt',type=int,default=1);parser.add_argument('--artifact');parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    output=a.output.resolve();assert output.is_relative_to(BASE) and not output.exists()and a.attempt==1
    output.mkdir(parents=True,exist_ok=False)
    controller=CAPSULE.read_bytes();controller_hash=sha(controller)
    receipt={'schema':1,'action':a.action,'controller_sha256':controller_hash,'transport_source_sha256':sha(TRANSPORT.read_bytes()),'strict_pinned_host':True,'credentials_read_or_exported':False,'only_fixed_owned_lab':True}
    capsule=module(CAPSULE,'owned_wallet_capsule')
    if a.action in ('validate-bundle','upload'):
        assert a.bundle is not None and a.bundle.is_file() and not a.bundle.is_symlink() and 0<a.bundle.stat().st_size<=capsule.MAX_ARCHIVE
        data=a.bundle.read_bytes();manifest,members=capsule.manifest_entries(data);receipt.update(bundle_sha256=sha(data),bundle_bytes=len(data),members=len(members),no_signer_or_credentials=manifest['no_signer_or_credentials'],sealing_forbidden=manifest['sealing_forbidden'])
        if a.action=='validate-bundle':
            receipt.update(exit_code=0,network_used=False);(output/'EXECUTION.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt));return 0
        remote='python3 -c '+shlex.quote(UPLOAD_SOURCE)+' '+sha(data)+' '+str(len(data));timeout=120
    else:
        args=['python3','-',a.action,'--controller-sha256',controller_hash,'--attempt',str(a.attempt)]
        if a.action=='install':
            assert a.bundle_sha256 is not None and len(a.bundle_sha256)==64
            args+=['--bundle-sha256',a.bundle_sha256]
        if a.action=='fetch':assert a.artifact in capsule.PUBLIC;args+=['--artifact',a.artifact]
        remote=' '.join(map(shlex.quote,args));data=controller;timeout=120 if a.action=='install'else 45
    transport=module(TRANSPORT,'opaque_fixed_transport');started=time.monotonic()
    code,reason,counts,errors=captured(transport.ssh()+[remote],data,output,timeout)
    receipt.update(exit_code=code,failed_capture_reason=reason,elapsed_seconds=time.monotonic()-started,timeout_seconds=timeout,stdout_bytes=counts[0],stderr_bytes=counts[1],capture_status=errors)
    for name in ('stdout.raw','stderr.raw'):receipt[name+'_sha256']=sha((output/name).read_bytes())
    if code==0 and reason is None:
        response=json.loads((output/'stdout.raw').read_bytes())
        if a.action=='fetch':
            assert response['phase']=='public_artifact' and response['artifact']==a.artifact and response['attempt']==a.attempt
            public=base64.b64decode(response['base64'],validate=True);assert len(public)==response['bytes']and sha(public)==response['sha256']
            (output/a.artifact).write_bytes(public);receipt['artifact_sha256']=sha(public)
        else:
            (output/'PUBLIC_RESULT.json').write_text(json.dumps(response,indent=2)+'\n',encoding='utf-8')
    (output/'EXECUTION.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt));return code if reason is None else 1
if __name__=='__main__':raise SystemExit(main())
