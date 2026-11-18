from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
D=V/'q03-activation-gas-20261117/validation-reuse'/sys.argv[1];D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=list(R.glob('src/**/*.sol'))+list(R.glob('test/**/*.sol'))+[R/'foundry.toml']
def pins():return {p.relative_to(R).as_posix():sha(p)for p in paths}
before=pins();target='Q03ValidationReuse20261117'
selector=sys.argv[2]if len(sys.argv)>2 else'^testQ03'
cmd=[str(V/'foundry-v1.4.4/forge.exe'),'test','--offline','--use',str(V/'toolchain-0.8.26/solc.exe'),
 '--root',str(R),'--match-path','test/'+target+'.t.sol','--match-contract',target+'Test',
 '--match-test',selector,'--out',str(D.parent/'out'),'--cache-path',str(D.parent/'cache'),
 '--skip','Q03ActivationCapacity20261117.t.sol','--skip','Q03ComplementAllocation20261117.t.sol',
 '--skip','Q03EnvelopeAllocation20261117.t.sol',
 '--code-size-limit','1000000','-vvv','--json']
env={k:v for k,v in os.environ.items()if k in('SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT')}
env['PATH']=str(V/'toolchain-0.8.26')+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32')
env['RAYON_NUM_THREADS']='2'
(D/'SOURCE_TEST.sol.txt').write_bytes((R/'test'/f'{target}.t.sol').read_bytes())
(D/'START.json').write_text(json.dumps({'command':cmd,'source_before':before,'environment':'allowlisted OS only; no RPC/private/export variables','tools':{str(p):sha(p)for p in(V/'foundry-v1.4.4/forge.exe',V/'toolchain-0.8.26/solc.exe')}},indent=2)+'\n')
start=time.monotonic()
with(D/'raw.json').open('xb')as out,(D/'stderr.log').open('xb')as err:
 p=subprocess.Popen(cmd,cwd=R,env=env,stdout=out,stderr=err)
 (D/'PID.json').write_text(json.dumps({'pid':p.pid})+'\n')
 code=p.wait(timeout=1800)
after=pins();methods=[]
try:
 raw=json.loads((D/'raw.json').read_bytes())
 for host,body in raw.items():
  for name,res in body.get('test_results',{}).items():methods.append({'id':host+'.'+name,'status':res.get('status'),'reason':res.get('reason'),'gas':res.get('gas'),'logs':res.get('decoded_logs')})
except(ValueError,AttributeError):pass
artifact=D.parent/'out'/f'{target}.t.sol'/f'{target}Test.json'
if artifact.exists():shutil.copy2(artifact,D/'producer-artifact.json')
record={'exit_code':code,'elapsed_seconds':time.monotonic()-start,'methods':methods,'source_bracket_stable':before==after,'source_before':before,'source_after':after,'raw_sha256':sha(D/'raw.json'),'stderr_sha256':sha(D/'stderr.log'),'artifact_sha256':sha(D/'producer-artifact.json')if(D/'producer-artifact.json').exists()else None,'unchanged_test_methods_executed':0,'runtime_limit_override':'test aggregate only; separate normal48 limits unchanged','production_approved':False}
(D/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k]for k in('exit_code','elapsed_seconds','source_bracket_stable','methods')}),flush=True)
if not methods:print((D/'stderr.log').read_text(errors='replace')[-4000:])
sys.exit(0 if code==0 and methods and all(m['status']=='Success'for m in methods)and before==after else 1)
