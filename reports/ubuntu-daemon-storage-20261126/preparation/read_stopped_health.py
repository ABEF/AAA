"""Read only the stopped c811 health/journal and public configuration digests.

No application/tool imports on the server, signing, service mutation or retries.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import time

BASE=Path(__file__).resolve().parent
V=BASE.parent
ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
REMOTE=r'''
from pathlib import Path
import hashlib,json,os,stat,subprocess,time
LAB=Path('/opt/popl-ubuntu-daemon-storage-20261126-c811')
ACTOR=LAB/'runtime/run-001/model/supervisor/actor'
end=time.monotonic()+20
def need(value):
 if not value:raise ValueError('Stopped owned-lab evidence refused')
def read(path):
 need(path in (ACTOR/'health.json',ACTOR/'state.json',ACTOR/'config.json'))
 opened=[]
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);opened.append(fd)
  for part in path.parts[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);opened.append(fd)
   st=os.fstat(fd);need(st.st_uid in (0,65534)and not st.st_mode&0o022)
  fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd);opened.append(fd)
  st=os.fstat(fd);need(stat.S_ISREG(st.st_mode)and st.st_uid==65534 and st.st_nlink==1 and st.st_size<=2097152 and not st.st_mode&0o077)
  raw=os.read(fd,2097153);need(0<len(raw)<=2097152 and len(raw)==st.st_size)
  value=json.loads(raw);need(type(value)is dict)
  return raw,value
 finally:
  for fd in reversed(opened):os.close(fd)
def stopped():
 rows={}
 for kind in ('keeper','resolve','model'):
  name=LAB.name+'-'+kind+'.service'
  c=subprocess.run(['/usr/bin/systemctl','show',name,'--no-pager','--property=ActiveState,MainPID,LoadState'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)
  need(c.returncode in (0,4)and len(c.stdout)+len(c.stderr)<=65536)
  p=dict(line.split('=',1)for line in c.stdout.decode('utf8','strict').splitlines())
  need(p.get('MainPID','0')=='0'and p.get('ActiveState')in ('inactive','failed'))
  rows[name]=p
 return rows
before=stopped();health_raw,health=read(ACTOR/'health.json');journal_raw,journal=read(ACTOR/'state.json');config_raw,config=read(ACTOR/'config.json')
need(config['rpc_urls']==['http://127.0.0.1:19592']and config['interval_seconds']==240 and config['confirmations']==12 and config['max_gas_limit']==24000000)
after=stopped();need(time.monotonic()<end)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
print(json.dumps({'schema':1,'read_only':True,'service_actions':0,'application_code_executed':False,'secrets_exported':False,
 'lab':str(LAB),'observed_utc_epoch':time.time(),'before_units':before,'after_units':after,
 'health':{'sha256':sha(health_raw),'raw_utf8':health_raw.decode('utf8'),'state':health},
 'journal':{'sha256':sha(journal_raw),'raw_utf8':journal_raw.decode('utf8'),'state':journal},
 'configuration_raw_sha256':sha(config_raw),'configuration_semantic_sha256':sha(json.dumps(config,sort_keys=True,separators=(',',':')).encode()),
 'configured_interval_seconds':240,'configured_confirmations':12,'configured_max_gas_limit':24000000},sort_keys=True))
'''


def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(BASE)and not out.exists()
    out.mkdir(mode=0o700);sys.dont_write_bytecode=True
    t=mod(ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py','existing_opaque_transport')
    runner=mod(V/'ubuntu-storage-20261125/c808/host_control.py','bounded_read_capture')
    runner.MAX_CAPTURE=3*1024*1024
    start=time.monotonic()
    code,reason,counts,errors=runner.captured(t.ssh()+['python3 -'],REMOTE.encode(),out,30)
    result={'exit_code':code,'capture_reason':reason,'capture_errors':errors,
        'elapsed_seconds':time.monotonic()-start,'read_only':True,'service_actions':0,
        'remote_source_sha256':hashlib.sha256(REMOTE.encode()).hexdigest(),
        'stdout_sha256':hashlib.sha256((out/'stdout.raw').read_bytes()).hexdigest(),
        'stderr_sha256':hashlib.sha256((out/'stderr.raw').read_bytes()).hexdigest()}
    if code==0 and reason is None:
        value=json.loads((out/'stdout.raw').read_bytes())
        with (out/'STOPPED_HEALTH.json').open('x',encoding='utf8')as f:
            json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    with (out/'EXECUTION.json').open('x',encoding='utf8')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(result));return code or bool(reason)


if __name__=='__main__':raise SystemExit(main())
