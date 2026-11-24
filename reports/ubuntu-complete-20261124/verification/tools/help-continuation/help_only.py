"""Continue ONLY16 uncompleted CLI --help commands as an already-nobody unit.
Preserve c7ef aggregatefalse and10 completed root syntax/ownership commands.
No installer, observer, tar/bash repetition, RPC, signing or financial feature.
"""
from pathlib import Path
import hashlib,json,os,re,stat,sys,time
LAB=Path('/opt/popl-ubuntu-help-20261124-c7f1')
OUT=LAB/'runtime/run-001'
SOURCE=Path('/opt/popl-ubuntu-features-20261124-c7ed/source/contracts')
SOURCE_MANIFEST=Path('/opt/popl-ubuntu-features-20261124-c7ed/inputs/SOURCE_MANIFEST.json')
SOURCE_SHA='c8b2c3f25572a9c64f1b701dde1aba5601261f805707bb460726537f44532f23'
PRIOR_HELPER=Path('/opt/popl-ubuntu-install-proof-20261124-c7ef/source/installer_boundary.py')
PRIOR_HELPER_SHA='d4a787ef82c56b9792e8fffa2b8f358b74ef315cb120d328189c82db65b8ddf6'
PRIOR_RESULT_SHA='cae14bf32cba08c6cfddd668cd26bfc8a1eed0635db871ffb20915fb5c01bfbc'
MODULES=('keeper.monitor','keeper.ops','keeper.probe','indexer.monitor','frontend_api.server','frontend_api.activation_server')
SCRIPTS=('prepare-manual-lp.py','prepare-operator-management.py','prepare-operator-review.py','prepare-deployment.py','prepare-deployment-sequence.py','prepare-preseal.py','prepare-opensea-drop.py','history-recovery.py','import-earnings-checkpoint.py','build-earnings-checkpoint.py')
class ProofRefusal(ValueError):pass
def need(value,message):
 if not value:raise ProofRefusal(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):
 raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();need(len(raw)<=1024*1024,'Receipt bound')
 with path.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def read_root(path,maximum,expected):
 opened=[]
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);opened.append(fd)
  for part in path.parts[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);opened.append(fd);entry=os.fstat(fd);need(entry.st_uid==0 and stat.S_ISDIR(entry.st_mode)and not entry.st_mode&0o022,'Root source directory identity')
  parent=fd;fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);opened.append(fd);before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and before.st_uid==0 and before.st_nlink==1 and not before.st_mode&0o022 and before.st_size<=maximum,'Root file identity or bound')
  data=[];total=0
  while True:
   raw=os.read(fd,min(65536,maximum+1-total))
   if not raw:break
   total+=len(raw);need(total<=maximum,'Read byte bound');data.append(raw)
  after=os.fstat(fd);current=os.stat(path.name,dir_fd=parent,follow_symlinks=False);key=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_nlink,s.st_size,s.st_mtime_ns)
  raw=b''.join(data);need(key(before)==key(after)==key(current)and total==before.st_size and sha(raw)==expected,'Pinned source changed');return raw
 finally:
  for fd in reversed(opened):os.close(fd)

def main():
 need(os.name=='posix'and os.geteuid()==os.getegid()==65534 and all(g==65534 for g in os.getgroups()),'Already unprivileged UID/GID/groups required')
 need(Path(__file__).resolve()==LAB/'source/help_only.py','Fixed helper path')
 need(os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Private network required')
 need(not os.path.lexists(OUT),'New owned output only');OUT.mkdir(mode=0o700);tmp=OUT/'tmp';tmp.mkdir(mode=0o700)
 result={'schema':1,'success':False,'scope':'ONLY16 previously uncompleted Ubuntu unprivileged CLI --help parsers; no financial feature approval','root_commands_repeated':0,'uid':os.geteuid(),'gid':os.getegid(),'supplementary_groups':os.getgroups(),'old_test_bodies':0,'public_transactions':0,'new_sealing':False,'signing':False,'source_changes':False,'production_approved':False,'commands':[],'prior_aggregate_success':False,'prior_failure_cause':'PermissionError at first attempted unprivileged help spawn; exact OS cause not established'}
 stage='source_and_prior_proof'
 try:
  read_root(PRIOR_HELPER,128*1024,PRIOR_HELPER_SHA)
  prior=json.loads(read_root(LAB/'inputs/prior-result.json',2*1024*1024,PRIOR_RESULT_SHA));need(prior['success']is False and prior['failure_stage']=='unprivileged_help_only'and prior['error_class']=='PermissionError'and len(prior['commands'])==10 and all(r['returncode']==0 and r['uid']==0 for r in prior['commands']),'Prior completed scope differs')
  result['prior_result_sha256']=PRIOR_RESULT_SHA;result['prior_completed_root_commands']=10
  source=json.loads(read_root(SOURCE_MANIFEST,2*1024*1024,SOURCE_SHA))
  for name,pin in source['members'].items():read_root(SOURCE/name,pin['bytes'],pin['sha256'])
  result['source_files_verified']=len(source['members']);result['source_manifest_sha256']=SOURCE_SHA;sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE))
  from keeper.cast_process import run_cast
  environment={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONPATH':str(SOURCE),'TMPDIR':str(tmp),'HOME':str(tmp)};until=time.monotonic()+120
  commands=[('help-'+m.replace('.','-'),['/usr/bin/python3','-B','-m',m,'--help'])for m in MODULES]+[('help-'+n[:-3],['/usr/bin/python3','-B',str(SOURCE/'scripts'/n),'--help'])for n in SCRIPTS]
  stage='unprivileged_help_only'
  for label,argv in commands:
   need(time.monotonic()<until,'Aggregate command deadline');result['active_command']=label;start=time.monotonic();child=run_cast(argv,env=environment,timeout=min(15,until-time.monotonic()))
   for suffix,text in(('stdout',child.stdout),('stderr',child.stderr)):
    with(OUT/(label+'.'+suffix)).open('x',encoding='utf-8')as stream:stream.write(text)
   row={'name':label,'returncode':child.returncode,'uid':65534,'gid':65534,'elapsed_seconds':time.monotonic()-start,'stdout_bytes':len(child.stdout.encode()),'stderr_bytes':len(child.stderr.encode())};result['commands'].append(row)
   need(child.returncode==0 and'usage:'in child.stdout.lower(),'Fixed help command refused')
  result['active_command']=None
  for name,pin in source['members'].items():read_root(SOURCE/name,pin['bytes'],pin['sha256'])
  result.update(success=True,help_only_commands=16,source_files_preserved=True,prior_helper_preserved=True,financial_features_executed=False,root_drop_attempted=False)
 except Exception as exc:result.update(failure_stage=stage,error_class=type(exc).__name__,fixed_guard=str(exc)if type(exc)is ProofRefusal else None)
 finally:save(OUT/'RESULT.json',result)
 print(json.dumps({'success':result['success'],'commands':len(result['commands']),'active_command':result.get('active_command'),'failure_stage':result.get('failure_stage')}));return 0 if result['success']else 1
if __name__=='__main__':raise SystemExit(main())
