"""Fixed read-only observer lifecycle metadata; no service control or app code."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,time
BASE=Path(__file__).resolve().parent
V=BASE.parent
ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
REMOTE=r'''
import json,subprocess,time
def run(args):
 p=subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
 if p.returncode!=0 or len(p.stdout)+len(p.stderr)>32768:raise ValueError('Fixed lifecycle read refused')
 return p.stdout.decode('utf8','strict')
start=time.monotonic()
props={}
for unit,names in [('zzz-stage-observer.service','Type,ActiveState,SubState,MainPID,Result,ExecMainCode,ExecMainStatus,InvocationID'),('zzz-stage-observer.timer','ActiveState,SubState,LastTriggerUSec,NextElapseUSecRealtime,NextElapseUSecMonotonic,Triggers')]:
 text=run(['/usr/bin/systemctl','show',unit,'--no-pager','--property='+names])
 props[unit]=dict(line.split('=',1)for line in text.splitlines())
fields='__REALTIME_TIMESTAMP,_PID,MESSAGE_ID,UNIT,EXIT_CODE,EXIT_STATUS'
raw=run(['/usr/bin/journalctl','--unit=zzz-stage-observer.service','--since=2026-11-26 13:36:20 UTC','--until=2026-11-26 13:47:40 UTC','--no-pager','--output=json','--output-fields='+fields,'--lines=40'])
events=[]
for line in raw.splitlines():
 row=json.loads(line)
 if str(row.get('_PID'))=='1':events.append({k:v for k,v in row.items()if k in fields.split(',')})
if time.monotonic()-start>20:raise ValueError('Fixed lifecycle deadline')
print(json.dumps({'schema':1,'read_only':True,'service_actions':0,'application_code_executed':False,'secrets_exported':False,'properties':props,'manager_events':events,'interval_UTC':['2026-11-26 13:36:20','2026-11-26 13:47:40'],'message_text_exported':False},sort_keys=True))
'''


def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(BASE)and not out.exists();out.mkdir(mode=0o700)
    sys.dont_write_bytecode=True
    t=mod(ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py','opaque_existing_transport')
    c=mod(V/'ubuntu-storage-20261125/c808/host_control.py','bounded_read_capture');c.MAX_CAPTURE=65536
    before=time.monotonic();code,reason,counts,errors=c.captured(t.ssh()+['python3 -'],REMOTE.encode(),out,30)
    receipt={'exit_code':code,'capture_reason':reason,'capture_errors':errors,'read_only':True,'service_actions':0,
        'remote_source_sha256':hashlib.sha256(REMOTE.encode()).hexdigest(),'elapsed_seconds':time.monotonic()-before,
        'stdout_sha256':hashlib.sha256((out/'stdout.raw').read_bytes()).hexdigest(),
        'stderr_sha256':hashlib.sha256((out/'stderr.raw').read_bytes()).hexdigest()}
    if code==0 and reason is None:
        with(out/'RESULT.json').open('x',encoding='utf8')as f:json.dump(json.loads((out/'stdout.raw').read_bytes()),f,indent=2,sort_keys=True);f.write('\n')
    with(out/'EXECUTION.json').open('x',encoding='utf8')as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(receipt));return code or bool(reason)


if __name__=='__main__':raise SystemExit(main())
