"""NEW root-only GNU tar ownership boundary and unprivileged CLI-syntax proof.
No installer/observer, public endpoint, signing, sealing or old state mutation.
"""
from pathlib import Path
import ast,base64,gzip,hashlib,io,json,os,re,signal,stat,subprocess,threading,time,tarfile
LAB=Path('/opt/popl-ubuntu-install-proof-20261124-c7ef')
SOURCE=Path('/opt/popl-ubuntu-features-20261124-c7ed/source/contracts')
SOURCE_MANIFEST=Path('/opt/popl-ubuntu-features-20261124-c7ed/inputs/SOURCE_MANIFEST.json')
SOURCE_SHA='c8b2c3f25572a9c64f1b701dde1aba5601261f805707bb460726537f44532f23'
INSTALLER_SHA='6304b5735a33f4a5ac79efc89ea6916c2e3d3a656f2d9219aaa32baf6f10b347'
INSTALLER_BASE64='IyEvdXNyL2Jpbi9lbnYgYmFzaAojIEV4cGxpY2l0IG9wZXJhdG9yIGluc3RhbGxhdGlvbiBvbiBhbiBhdXRob3JpemVkIGhvc3QuIE5vIHByb2R1Y3Rpb24gY2hhaW4uCnNldCAtZXVvIHBpcGVmYWlsCnRlc3QgIiQoaWQgLXUpIiA9IDAKdGVzdCAiJCh1bmFtZSAtbSkiID0geDg2XzY0CmJhc2U9L29wdC96enota2VlcGVyLXN0YWdpbmcKc3RhdGU9L3Zhci9saWIvenp6LWtlZXBlci1zdGFnaW5nCnRlc3QgLWYgIiRiYXNlL2tlZXBlci9tb25pdG9yLnB5Igp0ZXN0ICEgLWUgIiRzdGF0ZSIKaWYgZ2V0ZW50IHBhc3N3ZCB6enotc3RhZ2UgPi9kZXYvbnVsbDsgdGhlbiBlY2hvICdTdGFnaW5nIGFjY291bnQgYWxyZWFkeSBleGlzdHM7IHN0b3AgZm9yIHJldmlldy4nID4mMjsgZXhpdCAxOyBmaQppZiBzcyAtbG50SCAnKCBzcG9ydCA9IDoxODU0NSApJyB8IGdyZXAgLXEgLjsgdGhlbiBlY2hvICdTdGFnaW5nIHBvcnQgYWxyZWFkeSBvY2N1cGllZC4nID4mMjsgZXhpdCAxOyBmaQp1c2VyYWRkIC0tc3lzdGVtIC0tdXNlci1ncm91cCAtLWhvbWUtZGlyICIkc3RhdGUiIC0tc2hlbGwgL3Vzci9zYmluL25vbG9naW4genp6LXN0YWdlCmluc3RhbGwgLWQgLW0gMDcwMCAtbyB6enotc3RhZ2UgLWcgenp6LXN0YWdlICIkc3RhdGUiICIkc3RhdGUvY2hhaW4iICIkc3RhdGUva2VlcGVyIiAiJHN0YXRlL2tleXMiICIkc3RhdGUvYmFja3VwcyIgIiRzdGF0ZS9idWlsZCIgIiRzdGF0ZS9idWlsZC9zcmMiCmluc3RhbGwgLWQgLW0gMDc1NSAiJGJhc2UvYmluIgpjdXJsIC0tZmFpbCAtLWxvY2F0aW9uIC0tc2lsZW50IC0tc2hvdy1lcnJvciAtLW1heC10aW1lIDEyMCBcCiAgaHR0cHM6Ly9naXRodWIuY29tL2ZvdW5kcnktcnMvZm91bmRyeS9yZWxlYXNlcy9kb3dubG9hZC92MS40LjQvZm91bmRyeV92MS40LjRfbGludXhfYW1kNjQudGFyLmd6IFwKICAtLW91dHB1dCAiJGJhc2UvZm91bmRyeS50YXIuZ3oiCnByaW50ZiAnJXMgICVzXG4nIDIyYmExMTBhNDBlNGRlNzc5MWIwMDdiMDgyODRlN2IwMzhjNmJkNGNlMTQxYjdhYzM0YjVhY2NlYzA0ZjcxYTQgIiRiYXNlL2ZvdW5kcnkudGFyLmd6IiB8IHNoYTI1NnN1bSAtLWNoZWNrIC0tc3RhdHVzCnRhciAtLW5vLXNhbWUtb3duZXIgLXh6ZiAiJGJhc2UvZm91bmRyeS50YXIuZ3oiIC1DICIkYmFzZS9iaW4iIGNhc3QgYW52aWwgZm9yZ2UKIyBBIHJlbGVhc2UgYXJjaGl2ZSBtYXkgcmVjb3JkIGl0cyBidWlsZGVyJ3MgVUlEL0dJRC4gS2VlcCBleGVjdXRhYmxlIG93bmVyc2hpcAojIHdpdGggdGhpcyByb290IGluc3RhbGxlciBhbmQgcmVmdXNlIGxpbmtzIG9yIHByZS1leGlzdGluZyBmb3JlaWduIG93bmVyc2hpcC4KZm9yIGJpbmFyeSBpbiAiJGJhc2UvYmluLyJ7Y2FzdCxhbnZpbCxmb3JnZX07IGRvCiAgdGVzdCAtZiAiJGJpbmFyeSIgJiYgdGVzdCAhIC1MICIkYmluYXJ5IgogIHRlc3QgIiQoc3RhdCAtYyAnJXU6JWc6JWgnICIkYmluYXJ5IikiID0gJzA6MDoxJwogIGNobW9kIDA3NTUgIiRiaW5hcnkiCmRvbmUKaW5zdGFsbCAtbSAwNjAwIC1vIHp6ei1zdGFnZSAtZyB6enotc3RhZ2UgIiRiYXNlL2tlZXBlci9yZWhlYXJzYWwvS2VlcGVyVmVudWUuc29sIiAiJHN0YXRlL2J1aWxkL3NyYy9LZWVwZXJWZW51ZS5zb2wiCnByaW50ZiAnW3Byb2ZpbGUuZGVmYXVsdF1cbnNvbGNfdmVyc2lvbj0iMC44LjI2IlxuZXZtX3ZlcnNpb249ImNhbmN1biJcbicgPiAiJHN0YXRlL2J1aWxkL2ZvdW5kcnkudG9tbCIKY2hvd24genp6LXN0YWdlOnp6ei1zdGFnZSAiJHN0YXRlL2J1aWxkL2ZvdW5kcnkudG9tbCIKcnVudXNlciAtdSB6enotc3RhZ2UgLS0gZW52IEhPTUU9IiRzdGF0ZSIgIiRiYXNlL2Jpbi9mb3JnZSIgYnVpbGQgLS1yb290ICIkc3RhdGUvYnVpbGQiCgpjYXQgPiAvZXRjL3N5c3RlbWQvc3lzdGVtL3p6ei1zdGFnZS1hbnZpbC5zZXJ2aWNlIDw8J1VOSVQnCltVbml0XQpEZXNjcmlwdGlvbj1Qb1BMIGlzb2xhdGVkIHN0YWdpbmcgY2hhaW4gKHRlc3QgRVRIIG9ubHkpCkFmdGVyPW5ldHdvcmsudGFyZ2V0ClN0YXJ0TGltaXRJbnRlcnZhbFNlYz02MDAKU3RhcnRMaW1pdEJ1cnN0PTUKW1NlcnZpY2VdClVzZXI9enp6LXN0YWdlCkdyb3VwPXp6ei1zdGFnZQpXb3JraW5nRGlyZWN0b3J5PS9vcHQvenp6LWtlZXBlci1zdGFnaW5nCkV4ZWNTdGFydD0vb3B0L3p6ei1rZWVwZXItc3RhZ2luZy9iaW4vYW52aWwgLS1ob3N0IDEyNy4wLjAuMSAtLXBvcnQgMTg1NDUgLS1jaGFpbi1pZCAzMTMzNyAtLWJsb2NrLXRpbWUgNSAtLXN0YXRlIC92YXIvbGliL3p6ei1rZWVwZXItc3RhZ2luZy9jaGFpbi9zdGF0ZS5qc29uIC0tcHJlc2VydmUtaGlzdG9yaWNhbC1zdGF0ZXMgLS1zdGF0ZS1pbnRlcnZhbCAzMCAtLXNpbGVudApSZXN0YXJ0PW9uLWZhaWx1cmUKUmVzdGFydFNlYz0xNQpUaW1lb3V0U3RvcFNlYz02MApLaWxsTW9kZT1jb250cm9sLWdyb3VwCk5vTmV3UHJpdmlsZWdlcz10cnVlClByaXZhdGVUbXA9dHJ1ZQpQcml2YXRlRGV2aWNlcz10cnVlClByb3RlY3RTeXN0ZW09c3RyaWN0ClByb3RlY3RIb21lPXRydWUKUHJvdGVjdEtlcm5lbFR1bmFibGVzPXRydWUKUHJvdGVjdEtlcm5lbE1vZHVsZXM9dHJ1ZQpQcm90ZWN0Q29udHJvbEdyb3Vwcz10cnVlClJlc3RyaWN0U1VJRFNHSUQ9dHJ1ZQpMb2NrUGVyc29uYWxpdHk9dHJ1ZQpDYXBhYmlsaXR5Qm91bmRpbmdTZXQ9ClJlc3RyaWN0QWRkcmVzc0ZhbWlsaWVzPUFGX1VOSVggQUZfSU5FVCBBRl9JTkVUNgpJUEFkZHJlc3NEZW55PWFueQpJUEFkZHJlc3NBbGxvdz1sb2NhbGhvc3QKUmVhZFdyaXRlUGF0aHM9L3Zhci9saWIvenp6LWtlZXBlci1zdGFnaW5nL2NoYWluCkNQVVF1b3RhPTIwJQpNZW1vcnlNYXg9NTEyTQpUYXNrc01heD02NApVTWFzaz0wMDc3CltJbnN0YWxsXQpXYW50ZWRCeT1tdWx0aS11c2VyLnRhcmdldApVTklUCmNhdCA+IC9ldGMvc3lzdGVtZC9zeXN0ZW0venp6LXN0YWdlLWtlZXBlci5zZXJ2aWNlIDw8J1VOSVQnCltVbml0XQpEZXNjcmlwdGlvbj1Qb1BMIGtlZXBlciBzdGFnaW5nIChpc29sYXRlZCB0ZXN0IGNoYWluIG9ubHkpClJlcXVpcmVzPXp6ei1zdGFnZS1hbnZpbC5zZXJ2aWNlCkFmdGVyPXp6ei1zdGFnZS1hbnZpbC5zZXJ2aWNlClN0YXJ0TGltaXRJbnRlcnZhbFNlYz02MDAKU3RhcnRMaW1pdEJ1cnN0PTUKW1NlcnZpY2VdClVzZXI9enp6LXN0YWdlCkdyb3VwPXp6ei1zdGFnZQpXb3JraW5nRGlyZWN0b3J5PS9vcHQvenp6LWtlZXBlci1zdGFnaW5nCkV4ZWNTdGFydD0vdXNyL2Jpbi9weXRob24zIC1tIGtlZXBlci5tb25pdG9yIC0tY29uZmlnIC92YXIvbGliL3p6ei1rZWVwZXItc3RhZ2luZy9rZWVwZXIvY29uZmlnLmpzb24gLS1saXZlCkVudmlyb25tZW50PVBZVEhPTkRPTlRXUklURUJZVEVDT0RFPTEKUmVzdGFydD1vbi1mYWlsdXJlClJlc3RhcnRTZWM9MzAKS2lsbE1vZGU9Y29udHJvbC1ncm91cApUaW1lb3V0U3RvcFNlYz0xMjAKTm9OZXdQcml2aWxlZ2VzPXRydWUKUHJpdmF0ZVRtcD10cnVlClByaXZhdGVEZXZpY2VzPXRydWUKUHJvdGVjdFN5c3RlbT1zdHJpY3QKUHJvdGVjdEhvbWU9dHJ1ZQpQcm90ZWN0S2VybmVsVHVuYWJsZXM9dHJ1ZQpQcm90ZWN0S2VybmVsTW9kdWxlcz10cnVlClByb3RlY3RDb250cm9sR3JvdXBzPXRydWUKUmVzdHJpY3RTVUlEU0dJRD10cnVlCkxvY2tQZXJzb25hbGl0eT10cnVlCkNhcGFiaWxpdHlCb3VuZGluZ1NldD0KUmVzdHJpY3RBZGRyZXNzRmFtaWxpZXM9QUZfVU5JWCBBRl9JTkVUIEFGX0lORVQ2CklQQWRkcmVzc0Rlbnk9YW55CklQQWRkcmVzc0FsbG93PWxvY2FsaG9zdApSZWFkV3JpdGVQYXRocz0vdmFyL2xpYi96enota2VlcGVyLXN0YWdpbmcva2VlcGVyClJlYWRPbmx5UGF0aHM9L3Zhci9saWIvenp6LWtlZXBlci1zdGFnaW5nL2tleXMKSW5hY2Nlc3NpYmxlUGF0aHM9L3Zhci9saWIvenp6LWtlZXBlci1zdGFnaW5nL2NoYWluIC92YXIvbGliL3p6ei1rZWVwZXItc3RhZ2luZy9iYWNrdXBzCkNQVVF1b3RhPTIwJQpNZW1vcnlNYXg9MjU2TQpUYXNrc01heD02NApVTWFzaz0wMDc3CltJbnN0YWxsXQpXYW50ZWRCeT1tdWx0aS11c2VyLnRhcmdldApVTklUCnN5c3RlbWQtYW5hbHl6ZSB2ZXJpZnkgL2V0Yy9zeXN0ZW1kL3N5c3RlbS96enotc3RhZ2UtYW52aWwuc2VydmljZSAvZXRjL3N5c3RlbWQvc3lzdGVtL3p6ei1zdGFnZS1rZWVwZXIuc2VydmljZQpzeXN0ZW1jdGwgZGFlbW9uLXJlbG9hZApzeXN0ZW1jdGwgc3RhcnQgenp6LXN0YWdlLWFudmlsLnNlcnZpY2UKZm9yIGF0dGVtcHQgaW4gezEuLjIwfTsgZG8KICBpZiBjdXJsIC0tZmFpbCAtLXNpbGVudCAtLW1heC10aW1lIDIgLUggJ0NvbnRlbnQtVHlwZTogYXBwbGljYXRpb24vanNvbicgLWQgJ3sianNvbnJwYyI6IjIuMCIsImlkIjoxLCJtZXRob2QiOiJldGhfY2hhaW5JZCIsInBhcmFtcyI6W119JyBodHRwOi8vMTI3LjAuMC4xOjE4NTQ1LyB8IGdyZXAgLXEgJzB4N2E2OSc7IHRoZW4gYnJlYWs7IGZpCiAgc2xlZXAgMQpkb25lCmNkICIkYmFzZSIKcnVudXNlciAtdSB6enotc3RhZ2UgLS0gZW52IEhPTUU9IiRzdGF0ZSIgUFlUSE9ORE9OVFdSSVRFQllURUNPREU9MSAvdXNyL2Jpbi9weXRob24zIC1tIGtlZXBlci5zdGFnaW5nCnN5c3RlbWN0bCBlbmFibGUgLS1ub3cgenp6LXN0YWdlLWFudmlsLnNlcnZpY2Ugenp6LXN0YWdlLWtlZXBlci5zZXJ2aWNlCnN5c3RlbWN0bCBpcy1hY3RpdmUgenp6LXN0YWdlLWFudmlsLnNlcnZpY2Ugenp6LXN0YWdlLWtlZXBlci5zZXJ2aWNlCg=='
OUT=LAB/'runtime/run-001'
MAX_OUTPUT=65536
MODULES=('keeper.monitor','keeper.ops','keeper.probe','indexer.monitor','frontend_api.server','frontend_api.activation_server')
SCRIPTS=('prepare-manual-lp.py','prepare-operator-management.py','prepare-operator-review.py','prepare-deployment.py','prepare-deployment-sequence.py','prepare-preseal.py','prepare-opensea-drop.py','history-recovery.py','import-earnings-checkpoint.py','build-earnings-checkpoint.py')

def need(ok,reason):
 if not ok:raise RuntimeError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):
 raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();need(len(raw)<=2*1024*1024,'Receipt bound')
 with path.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def read_root(path,maximum,expected):
 opened=[]
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);opened.append(fd)
  for part in path.parts[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);opened.append(fd);s=os.fstat(fd);need(s.st_uid==0 and stat.S_ISDIR(s.st_mode)and not s.st_mode&0o022,'Root source directory identity')
  parent=fd;fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);opened.append(fd);s=os.fstat(fd);need(s.st_uid==0 and stat.S_ISREG(s.st_mode)and s.st_nlink==1 and not s.st_mode&0o022 and s.st_size<=maximum,'Root source file identity')
  raw=os.read(fd,maximum+1);now=os.fstat(fd);need(len(raw)==s.st_size and len(raw)<=maximum and(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(now.st_dev,now.st_ino,now.st_size,now.st_mtime_ns)and sha(raw)==expected,'Root source pin differs');return raw
 finally:
  for fd in reversed(opened):os.close(fd)

def main():
 need(os.name=='posix'and os.geteuid()==os.getegid()==0,'Root-only GNU tar ownership proof')
 need(Path(__file__).resolve()==LAB/'source/installer_boundary.py','Fixed helper path')
 need(os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Private network required')
 runtime=LAB/'runtime';identity=runtime.lstat();need(stat.S_ISDIR(identity.st_mode)and identity.st_uid==0 and not identity.st_mode&0o022,'Owned root runtime directory required');runtime.chmod(0o755)
 need(not os.path.lexists(OUT),'New owned run directory required');OUT.mkdir(mode=0o755);OUT.chmod(0o755)
 tmp=OUT/'cli-tmp';tmp.mkdir(mode=0o700);os.chown(tmp,65534,65534)
 env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(SOURCE),'TMPDIR':str(tmp),'HOME':str(tmp)}
 until=time.monotonic()+120;results=[];stage='verify_sources';result={'schema':1,'success':False,'scope':'NEW synthetic GNUtar ownership boundary, parser-only shell and unprivileged --help only','financial_features_executed':False,'old_test_bodies':0,'public_transactions':0,'new_sealing':False,'old_installation_changed':False,'production_approved':False,'commands':results}
 def command(label,argv,*,nobody=False):
  need(time.monotonic()<until,'Aggregate proof deadline');need(re.fullmatch('[a-z0-9-]{1,64}',label)is not None,'Output label')
  p=subprocess.Popen(argv,cwd=SOURCE,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,user=65534 if nobody else 0,group=65534 if nobody else 0,extra_groups=())
  chunks=[[],[]];total=[0];lock=threading.Lock();overflow=threading.Event()
  def drain(pipe,index):
   try:
    while True:
     part=pipe.read(4096)
     if not part:break
     with lock:
      room=max(0,MAX_OUTPUT-total[0]);chunks[index].append(part[:room]);total[0]+=min(room,len(part))
      if len(part)>room:overflow.set()
   finally:pipe.close()
  readers=[threading.Thread(target=drain,args=(p.stdout,0),daemon=True),threading.Thread(target=drain,args=(p.stderr,1),daemon=True)]
  for t in readers:t.start()
  deadline=min(until,time.monotonic()+15);timed_out=False
  try:
   while p.poll()is None:
    if overflow.is_set()or time.monotonic()>=deadline:timed_out=True;os.killpg(p.pid,signal.SIGKILL);break
    time.sleep(.02)
   p.wait(timeout=2)
  finally:
   if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=2)
   for t in readers:t.join(2)
  need(not any(t.is_alive()for t in readers),'Child pipe cleanup incomplete')
  bodies=[b''.join(x)for x in chunks]
  for suffix,raw in zip(('stdout','stderr'),bodies):
   with(OUT/(label+'.'+suffix)).open('xb')as f:f.write(raw)
  record={'name':label,'returncode':p.returncode,'uid':65534 if nobody else 0,'gid':65534 if nobody else 0,'timed_out_or_overflow':timed_out or overflow.is_set(),'captured_total_bytes':total[0],'argv_kind':'fixed_help_only'if nobody else'fixed_tar_or_parser_only'};results.append(record)
  need(not record['timed_out_or_overflow']and p.returncode==0,'Fixed proof command refused');return bodies
 try:
  raw=read_root(SOURCE_MANIFEST,2*1024*1024,SOURCE_SHA);source=json.loads(raw)
  for name,pin in source['members'].items():read_root(SOURCE/name,pin['bytes'],pin['sha256'])
  result['source_manifest_sha256']=SOURCE_SHA;result['source_stage']=source['source_stage'];result['source_files_verified']=len(source['members'])
  installer=base64.b64decode(INSTALLER_BASE64,validate=True);need(sha(installer)==INSTALLER_SHA,'Future installer pin differs');inputpath=OUT/'future-staging-install.sh';inputpath.write_bytes(installer);inputpath.chmod(0o444)
  stage='gnu_tar_ownership_boundary';version=command('gnu-tar-version',['/usr/bin/tar','--version'])[0];need(b'GNU tar'in version,'GNU tar implementation required')
  content=b'PoPL NEW synthetic non-executable builder-owned archive member.\n';buffer=io.BytesIO()
  with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0,filename='')as gz:
   with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT)as archive:
    member=tarfile.TarInfo('builder-owned.txt');member.size=len(content);member.uid=member.gid=1001;member.uname=member.gname='';member.mode=0o644;member.mtime=0;archive.addfile(member,io.BytesIO(content))
  packed=buffer.getvalue();need(len(packed)<4096,'Synthetic archive bound');archive_path=OUT/'synthetic-builder-owned.tar.gz';archive_path.write_bytes(packed);archive_path.chmod(0o444)
  for label,flags,expected_uid in [('original',[],1001),('fixed',['--no-same-owner'],0)]:
   destination=OUT/label;destination.mkdir(mode=0o755)
   command('tar-'+label,['/usr/bin/tar',*flags,'-xzf',str(archive_path),'-C',str(destination),'builder-owned.txt'])
   path=destination/'builder-owned.txt';s=path.lstat();need(stat.S_ISREG(s.st_mode)and not s.st_mode&0o111 and s.st_nlink==1 and(s.st_uid,s.st_gid)==(expected_uid,expected_uid)and path.read_bytes()==content,'Synthetic extraction ownership or content differs')
   result[label]={'uid':s.st_uid,'gid':s.st_gid,'archive_extraction_mode':oct(s.st_mode&0o777),'links':s.st_nlink,'bytes':s.st_size,'content_sha256':sha(content),'nonexecutable_at_extraction':True,'file_never_executed':True}
   ownership_guard=(s.st_uid,s.st_gid,s.st_nlink)==(0,0,1)and stat.S_ISREG(s.st_mode)and not path.is_symlink();result[label]['installer_ownership_guard_passed']=ownership_guard
   if label=='original':need(not ownership_guard,'Original ownership fault was not reproduced')
   else:
    need(ownership_guard,'Refuse chmod before exact regular/root ownership proof');path.chmod(0o755);after=path.lstat();need((after.st_uid,after.st_gid,after.st_nlink,after.st_mode&0o777)==(0,0,1,0o755),'Reviewed post-guard mode differs');result[label]['post_guard_mode']='0o755'

  result['archive']={'uid':1001,'gid':1001,'bytes':len(packed),'sha256':sha(packed),'member_count':1,'regular_member_only':True}
  original_stat=command('original-stat-proof',['/usr/bin/stat','-c','%u:%g:%h:%a',str(OUT/'original/builder-owned.txt')])[0].strip();need(original_stat==b'1001:1001:1:644','Original GNUstat fields differ')
  fixed_stat=command('fixed-stat-proof',['/usr/bin/stat','-c','%u:%g:%h:%a',str(OUT/'fixed/builder-owned.txt')])[0].strip();need(fixed_stat==b'0:0:1:755','Fixed GNUstat fields differ')
  stage='bash_parse_only';command('updated-installer-bash-n',['/bin/bash','--noprofile','--norc','-n',str(inputpath)])
  for name in('keeper/staging-monitor-install.sh','scripts/install-deps.sh','scripts/verify-slither.sh','scripts/verify.sh'):
   command('bash-n-'+Path(name).stem.replace('_','-'),['/bin/bash','--noprofile','--norc','-n',str(SOURCE/name)])
  result['future_installer_sha256']=INSTALLER_SHA
  stage='unprivileged_help_only'
  for name in MODULES:
   body=command('help-'+name.replace('.','-'),['/usr/bin/python3','-B','-m',name,'--help'],nobody=True)[0];need(b'usage:'in body.lower(),'CLI help missing')
  for name in SCRIPTS:
   body=command('help-'+name[:-3],['/usr/bin/python3','-B',str(SOURCE/'scripts'/name),'--help'],nobody=True)[0];need(b'usage:'in body.lower(),'Script help missing')
  for name,pin in source['members'].items():read_root(SOURCE/name,pin['bytes'],pin['sha256'])
  result.update(success=True,source_files_preserved=True,help_only_commands=len(MODULES)+len(SCRIPTS),staging_installers_executed=False,fixed_observer_executed=False)
 except Exception as exc:
  result.update(failure_stage=stage,error_class=type(exc).__name__,fixed_guard=str(exc)if type(exc)is RuntimeError else None)
 finally:save(OUT/'RESULT.json',result)
 print(json.dumps({'success':result['success'],'failure_stage':result.get('failure_stage'),'commands':len(results)}));return 0 if result['success']else 1
if __name__=='__main__':raise SystemExit(main())
