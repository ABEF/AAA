"""NEW targeted Bash guard proof only: preserved legacy FIFO baseline+5 new cases.
No tar/help rerun, installer/observer execution, network, signing or sealing.
"""
from pathlib import Path
import hashlib,importlib.util,json,os,stat,time
LAB=Path('/opt/popl-installer-guards-20261124-c7f5')
OUT=LAB/'runtime/run-001'
NEW_INSTALLER_SHA='b66878fee51f54ac36656646d41f57e70955b9b43c5aff228b5ecd02b3e258b3'
LEGACY=Path('/opt/popl-ubuntu-install-proof-20261124-c7ef/runtime/run-001/future-staging-install.sh')
LEGACY_SHA='6304b5735a33f4a5ac79efc89ea6916c2e3d3a656f2d9219aaa32baf6f10b347'
CAST_HELPER=Path('/opt/popl-ubuntu-features-20261124-c7ed/source/contracts/keeper/cast_process.py')
CAST_SHA='b6203067b022625bce2bfb415bb6ed85620dc8c7002b51f2d3d4c9296c5ac3e1'
class ProofRefusal(ValueError):pass
def need(ok,message):
 if not ok:raise ProofRefusal(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):
 raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();need(len(raw)<=1024*1024,'Receipt bound')
 with path.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def read_root(path,maximum,expected):
 opened=[]
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);opened.append(fd)
  for part in path.parts[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);opened.append(fd);x=os.fstat(fd);need(stat.S_ISDIR(x.st_mode)and x.st_uid==0 and not x.st_mode&0o022,'Root directory identity')
  parent=fd;fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);opened.append(fd);a=os.fstat(fd);need(stat.S_ISREG(a.st_mode)and a.st_uid==0 and a.st_nlink==1 and not a.st_mode&0o022 and a.st_size<=maximum,'Root file identity or bound')
  raw=os.read(fd,maximum+1);b=os.fstat(fd);c=os.stat(path.name,dir_fd=parent,follow_symlinks=False);key=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_uid,x.st_nlink,x.st_size,x.st_mtime_ns)
  need(key(a)==key(b)==key(c)and len(raw)==a.st_size and sha(raw)==expected,'Root input changed');return raw
 finally:
  for fd in reversed(opened):os.close(fd)
def fragment(raw):
 text=raw.decode('utf-8').replace('\r\n','\n');start='for binary in "$base/bin/"{cast,anvil,forge}; do\n';need(text.count(start)==1,'Unique real installer loop required');body=text.split(start,1)[1].split('\ndone\n',1)[0];need(0<len(body)<1024,'Guard fragment bound');return body

def main():
 need(os.name=='posix'and os.geteuid()==os.getegid()==0,'Root-owned special fixture proof required')
 need(Path(__file__).resolve()==LAB/'source/guard_proof.py','Fixed helper path')
 need(os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Private network required')
 need(not os.path.lexists(OUT),'New owned output required');OUT.mkdir(mode=0o700);tmp=OUT/'tmp';tmp.mkdir(mode=0o700)
 result={'schema':1,'success':False,'scope':'NEW actual Bash FIFO baseline and5 negative/positive guard cases using exact extracted installer fragments and sentinel chmod only','new_installer_sha256':NEW_INSTALLER_SHA,'legacy_installer_sha256':LEGACY_SHA,'tar_commands_repeated':0,'help_commands_repeated':0,'full_installer_or_observer_executed':False,'actual_chmod_executed':False,'public_transactions':0,'new_sealing':False,'old_test_bodies':0,'production_approved':False,'commands':[]};stage='source_proof'
 try:
  new_script=read_root(LAB/'source/staging-install.sh',16384,NEW_INSTALLER_SHA);legacy_script=read_root(LEGACY,16384,LEGACY_SHA);read_root(CAST_HELPER,16384,CAST_SHA)
  before=fragment(legacy_script);after=fragment(new_script);need(before.replace('  test -f "$binary" && test ! -L "$binary"','  test -f "$binary"\n  test ! -L "$binary"')==after,'Only standalone type guards may differ in fragment')
  need('  test -f "$binary"\n  test ! -L "$binary"'in after,'New standalone type guards missing');result['fragment_sha256']={'legacy':sha(before.encode()),'new':sha(after.encode())}
  spec=importlib.util.spec_from_file_location('pinned_cast_capture',CAST_HELPER);capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
  fixture=OUT/'fixtures';fixture.mkdir(mode=0o700);sentinels=OUT/'sentinels';sentinels.mkdir(mode=0o700)
  for name in('valid.txt','hardlink-source.txt'):(fixture/name).write_text('NEW controlled nonexecuted guard fixture.\n',encoding='utf-8');(fixture/name).chmod(0o644)
  os.mkfifo(fixture/'fifo',0o600);(fixture/'directory').mkdir(mode=0o700);os.symlink('valid.txt',fixture/'symlink');os.link(fixture/'hardlink-source.txt',fixture/'hardlink')
  def identities():
   rows={}
   for path in sorted(fixture.iterdir()):
    x=path.lstat();row={'device':x.st_dev,'inode':x.st_ino,'uid':x.st_uid,'gid':x.st_gid,'mode':x.st_mode,'links':x.st_nlink,'bytes':x.st_size}
    if stat.S_ISREG(x.st_mode):row['content_sha256']=sha(path.read_bytes())
    if stat.S_ISLNK(x.st_mode):row['target']=os.readlink(path)
    rows[path.name]=row
   return rows
  originals=identities();result['fixtures_before']=originals
  preamble='set -euo pipefail\nbinary=$1\nsentinel=$2\nchmod() { test "$#" = 2; test "$1" = 0755; test "$2" = "$binary"; printf "%s\\n" reached > "$sentinel"; }\n'
  for name,body in(('legacy-fragment.sh',before),('new-fragment.sh',after)):(OUT/name).write_text(preamble+body+'\n',encoding='utf-8');(OUT/name).chmod(0o444)
  env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(tmp),'PYTHONDONTWRITEBYTECODE':'1'};until=time.monotonic()+30
  cases=[('legacy-fifo','legacy-fragment.sh','fifo',0,True),('new-fifo','new-fragment.sh','fifo',1,False),('new-directory','new-fragment.sh','directory',1,False),('new-symlink','new-fragment.sh','symlink',1,False),('new-hardlink','new-fragment.sh','hardlink',1,False),('new-valid-regular','new-fragment.sh','valid.txt',0,True)]
  stage='actual_bash_guard_cases'
  for label,script,target,expected_code,expected_sentinel in cases:
   result['active_command']=label;need(time.monotonic()<until,'Aggregate proof deadline');sentinel=sentinels/label;start=time.monotonic();child=capture.run_cast(['/bin/bash','--noprofile','--norc',str(OUT/script),str(fixture/target),str(sentinel)],env=env,timeout=min(5,until-time.monotonic()))
   for suffix,text in(('stdout',child.stdout),('stderr',child.stderr)):
    with(OUT/(label+'.'+suffix)).open('x',encoding='utf-8')as f:f.write(text)
   row={'name':label,'exit_code':child.returncode,'expected_exit_code':expected_code,'chmod_sentinel':sentinel.is_file(),'expected_chmod_sentinel':expected_sentinel,'elapsed_seconds':time.monotonic()-start,'stdout_bytes':len(child.stdout.encode()),'stderr_bytes':len(child.stderr.encode())};result['commands'].append(row)
   need(child.returncode==expected_code and sentinel.is_file()==expected_sentinel,'Extracted guard case differs');need(identities()==originals,'Fixture identity or content changed')
  read_root(LEGACY,16384,LEGACY_SHA);read_root(CAST_HELPER,16384,CAST_SHA);read_root(LAB/'source/staging-install.sh',16384,NEW_INSTALLER_SHA)
  result.update(success=True,active_command=None,new_guard_cases=5,legacy_fifo_baseline_reproduced=True,negative_types_refuse_before_chmod=True,valid_regular_reaches_chmod_sentinel=True,fixture_bytes_modes_and_inodes_preserved=True,old_inputs_preserved=True)
 except Exception as exc:result.update(failure_stage=stage,error_class=type(exc).__name__,fixed_guard=str(exc)if type(exc)is ProofRefusal else None)
 finally:save(OUT/'RESULT.json',result)
 print(json.dumps({'success':result['success'],'commands':len(result['commands']),'active_command':result.get('active_command')}));return 0 if result['success']else 1
if __name__=='__main__':raise SystemExit(main())
