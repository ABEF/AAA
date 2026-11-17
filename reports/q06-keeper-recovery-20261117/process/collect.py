"""Read only the four owned Q06 labs; emit a bounded public-evidence archive.

No credential/keystore or installed application journal is read. The existing
observer is inspected only through PID1's bounded service lifecycle messages.
"""
import base64,gzip,hashlib,io,json,os,pathlib,re,subprocess,sys,tarfile,time

BASES=(
 '/run/popl-q06-20261117-65e71e7447bf',
 '/run/popl-q06-20261117-fbdc081eb8c0',
 '/run/popl-q06-20261117-91076f0abfde',
 '/opt/popl-q06-20261117-7b5ec836608b',
)
files={};total=0
def add(name,body):
 global total
 assert name not in files and not name.startswith('/') and '..'not in pathlib.PurePosixPath(name).parts
 total+=len(body);assert total<=32*1024*1024
 files[name]=body
def js(name,value):add(name,(json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=20,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'})
 assert len(p.stdout)<4*1024*1024
 return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr[:2048]}
def manager_journal(unit,start,end):
 r=run(['journalctl','--no-pager','--output=json','-n','200','--since','@'+str(int(start)),
        '--until','@'+str(int(end)+2),'_PID=1','UNIT='+unit])
 rows=[]
 for line in r['stdout'].splitlines():
  row=json.loads(line)
  rows.append({k:row[k]for k in('MESSAGE','UNIT','UNIT_RESULT','RESULT','JOB_TYPE','JOB_RESULT',
       '__REALTIME_TIMESTAMP','__MONOTONIC_TIMESTAMP','INVOCATION_ID','_PID','_COMM')if k in row})
 return {'returncode':r['returncode'],'stderr':r['stderr'],'rows':rows,'limit':200}
for text in BASES:
 base=pathlib.Path(text)
 assert re.fullmatch(r'/(?:run|opt)/popl-q06-20261117-[0-9a-f]{12}',text)and base.is_dir()and not base.is_symlink()
 label=base.name;manifest=json.loads((base/'source-manifest.json').read_text());after={};mismatches=[]
 for name,expected in manifest.items():
  assert not name.startswith('/')and'..'not in pathlib.PurePosixPath(name).parts
  p=base/'source'/name;assert p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(base/'source')
  actual=hashlib.sha256(p.read_bytes()).hexdigest();after[name]=actual
  if actual!=expected:mismatches.append(name)
 js(label+'/SOURCE_AFTER.json',{'checked_files':len(after),'sha256':after,'mismatches':mismatches})
 for p in sorted(base.rglob('*')):
  if p.is_dir()or p.is_symlink()or p.is_relative_to(base/'source'):continue
  if p.name in('inert-keystore.json','inert-password','inert-cast'):continue
  assert p.is_file()and p.resolve().is_relative_to(base)
  add(label+'/'+p.relative_to(base).as_posix(),p.read_bytes())
 timeline=json.loads((base/'timeline.json').read_text());start=min(r['utc']for r in timeline)-60;end=max(r['utc']for r in timeline)+60
 summary=json.loads((base/'SUMMARY.json').read_text())
 unit_state={}
 for unit in summary['units']:
  assert unit.startswith(label+'-')and re.fullmatch(r'[a-z0-9-]+\.service',unit)
  js(label+'/manager-journal/'+unit+'.json',manager_journal(unit,start,end))
  unit_state[unit]=run(['systemctl','show',unit,'--no-pager','-p','ActiveState','-p','MainPID','-p','ControlGroup'])
 js(label+'/OWNED_UNITS_AFTER.json',unit_state)
 if label.endswith('7b5ec836608b'):
  js(label+'/observer-manager-journal.json',manager_journal('zzz-stage-observer.service',start,end))
  js(label+'/observer-timer.json',run(['systemctl','show','zzz-stage-observer.timer','--no-pager',
    '-p','ActiveState','-p','SubState','-p','Triggers','-p','LastTriggerUSec','-p','NextElapseUSecRealtime',
    '-p','NextElapseUSecMonotonic','-p','TimersMonotonic','-p','TimersCalendar']))
js('HOST.json',{'collected_utc':time.time(),'python':sys.version,'kernel':os.uname().release,
 'systemd':run(['systemd','--version'])['stdout'].splitlines()[0],
 'transport_uid':os.getuid(),'scope':'Read-only own lab collection; no installed app output/credential read'})
js('ARCHIVE_MANIFEST.json',{'sha256':{n:hashlib.sha256(b).hexdigest()for n,b in sorted(files.items())},
 'files':len(files),'expanded_bytes':total,'omitted':'Entire supplied source pool (hashed separately); inert credential placeholders and executable'})
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w:gz')as out:
 for name,body in sorted(files.items()):
  item=tarfile.TarInfo(name);item.size=len(body);item.mode=0o600;out.addfile(item,io.BytesIO(body))
print(base64.b64encode(buffer.getvalue()).decode())
