"""Fixed c817 action wrapper; reviewed sources only, opaque pinned SSH transport."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,shlex,subprocess,threading,time

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
exec(compile(code,'<fixed_c817_capsule>','exec'),{'__name__':'__main__','__file__':'<fixed_c817_capsule>'})
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

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('install','start','status','stop','fetch'))
    p.add_argument('--artifact',choices=('RESULT.json','FINAL.json','PROGRESS.json'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    approval=json.loads((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    for name in ('c817.inputs.tar.gz','remote_capsule.py','host_control.py'):
        assert sha((BASE/name).read_bytes())==approval[name]
    assert sha(TRANSPORT.read_bytes())==TRANSPORT_SHA
    output=a.output.resolve();assert output.is_relative_to(BASE)and not output.exists();output.mkdir(parents=True,mode=0o755)
    controller=(BASE/'remote_capsule.py').read_bytes();assert 0<len(controller)<=65536
    args=['python3','-c',BOOTSTRAP,a.action,'--controller-sha256',sha(controller)]
    if a.action=='fetch':assert a.artifact is not None;args+=['--artifact',a.artifact]
    packet=len(controller).to_bytes(4,'big')+controller
    if a.action=='install':
        bundle=(BASE/'c817.inputs.tar.gz').read_bytes();assert 0<len(bundle)<=2*1024*1024;packet+=bundle
    transport=module(TRANSPORT,'fixed_c817_opaque_transport');started=time.monotonic()
    code,reason,counts,errors=capture(transport.ssh()+[' '.join(map(shlex.quote,args))],packet,output)
    receipt={'schema':1,'action':a.action,'exit_code':code,'capture_reason':reason,'capture_errors':errors,
        'controller_sha256':sha(controller),'transport_sha256':TRANSPORT_SHA,'combined_output_limit':65536,
        'stdout_bytes':counts[0],'stderr_bytes':counts[1],'elapsed_seconds':time.monotonic()-started,
        'opaque_SSH_transport':True,'Ethereum_signer_files_read_or_copied':False,'only_fixed_c817_unit':True}
    for name in ('stdout.raw','stderr.raw'):receipt[name+'_sha256']=sha((output/name).read_bytes())
    if code==0 and reason is None and not errors:
        response=json.loads((output/'stdout.raw').read_bytes())
        if a.action=='fetch':
            raw=base64.b64decode(response['base64'],validate=True)
            assert response['name']==a.artifact and len(raw)==response['bytes']and sha(raw)==response['sha256']
            with(output/a.artifact).open('xb')as f:f.write(raw)
        else:
            with(output/'PUBLIC_RESULT.json').open('x',encoding='utf8')as f:json.dump(response,f,indent=2,sort_keys=True);f.write('\n')
    with(output/'EXECUTION.json').open('x',encoding='utf8')as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(receipt,sort_keys=True));return 0 if code==0 and reason is None and not errors else 1

if __name__=='__main__':raise SystemExit(main())
