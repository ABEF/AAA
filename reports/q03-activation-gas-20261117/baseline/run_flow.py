"""Run only NEW Q03 fixture methods, with owned exports/caches and pinned tools.

Only an owned export permission is temporarily added and exactly restored.
No existing node, public RPC, signer or default adoption.
The higher code-size limit belongs only to the aggregate test harness; normal
production object limits must pass in a separate exact-source build.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OWN=V/'q03-activation-gas-20261117'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
stage=sys.argv[1];assert re.fullmatch(r'[a-z0-9-]+',stage)
target=sys.argv[2]if len(sys.argv)>2 else'Q03ActivationCapacity20261117'
assert target in('Q03ActivationCapacity20261117','Q03ComplementAllocation20261117')
selector=sys.argv[3]if len(sys.argv)>3 else'^testQ03'
assert selector.startswith('^testQ03')
d=OWN/stage;d.mkdir(parents=True,exist_ok=False);exports=d/'exports';exports.mkdir()
source=(ROOT/'foundry.toml').read_bytes();assert source.count(b'fs_permissions = [')==1
config=source.replace(b'fs_permissions = [',('fs_permissions = [{ access = "read-write", path = "'+exports.as_posix()+'" }, ').encode())
(d/'foundry.toml').write_bytes(config)
(d/'ORIGINAL_foundry.toml').write_bytes(source)
cmd=[str(V/'foundry-v1.4.4/forge.exe'),'test','--offline','--use',str(V/'toolchain-0.8.26/solc.exe'),
 '--root',str(ROOT),'--match-path','test/'+target+'.t.sol',
 '--match-contract',target+'.*Test','--match-test',selector,'--out',str(OWN/'out'),
 '--cache-path',str(OWN/'cache'),'--code-size-limit','1000000','-vv','--json']
if target=='Q03ActivationCapacity20261117':cmd+=['--skip','Q03ComplementAllocation20261117.t.sol']
else:cmd+=['--skip','Q03ActivationCapacity20261117.t.sol']
env={k:v for k,v in os.environ.items()if k in('SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT')}
env.update(PATH=str(V/'toolchain-0.8.26')+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32'),
 RAYON_NUM_THREADS='2',POPL_REFERENCE_EXPORT_PATH=str(exports/'setup'),POPL_GAS_PROFILE_EXPORT_ROOT=str(exports))
if target=='Q03ActivationCapacity20261117':
 # Large vm.dumpState/readFile buffers and unmetered historical setup belong
 # only to this aggregate harness. Every actual measured entry remains20M,
 # a32M diagnostic is never approved, and owned RPC qualification stays32M.
 env.update(FOUNDRY_GAS_LIMIT='10000000000',FOUNDRY_MEMORY_LIMIT='536870912')
paths=list(ROOT.glob('src/**/*.sol'))+list(ROOT.glob('test/**/*.sol'))+[ROOT/'foundry.toml']
before={p.relative_to(ROOT).as_posix():sha(p)for p in paths}
(d/'SOURCE_TEST.sol.txt').write_bytes((ROOT/'test'/(target+'.t.sol')).read_bytes())
started={'command':cmd,'source_before':before,'config_sha256':sha(d/'foundry.toml'),
 'base_config_sha256':hashlib.sha256(source).hexdigest(),'runner_sha256':sha(__file__),
 'tools':{str(p):sha(p)for p in(V/'foundry-v1.4.4/forge.exe',V/'toolchain-0.8.26/solc.exe')},
 'environment':'Allowlisted OS variables and owned export paths only','started_unix':time.time()}
started['harness_only_resources']={'gas_limit':env.get('FOUNDRY_GAS_LIMIT'),
 'memory_limit':env.get('FOUNDRY_MEMORY_LIMIT'),'actual_entry_cap':20_000_000,
 'diagnostic_only_cap':32_000_000,'normal_limits_and_production_defaults_changed':False}
(d/'START.json').write_text(json.dumps(started,indent=2)+'\n',encoding='utf-8')
start=time.monotonic();code=None;error=None
try:
 (ROOT/'foundry.toml').write_bytes(config)
 probe=subprocess.run([str(V/'foundry-v1.4.4/forge.exe'),'config','--json','--root',str(ROOT)],
   cwd=ROOT,env=env,capture_output=True,timeout=30)
 if probe.returncode:raise RuntimeError('Owned effective harness configuration unavailable')
 observed=json.loads(probe.stdout)
 selected={k:observed.get(k)for k in('gas_limit','memory_limit','solc','evm_version','optimizer','optimizer_runs','via_ir')}
 if target=='Q03ActivationCapacity20261117':
  assert selected['gas_limit']==10_000_000_000 and selected['memory_limit']==536_870_912
 (d/'HARNESS_RESOURCES.json').write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8')
 with(d/'raw.json').open('xb')as out,(d/'stderr.log').open('xb')as err:
  code=subprocess.run(cmd,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=2400).returncode
except subprocess.TimeoutExpired:error='Owned test process timeout; no result is a pass'
finally:
 assert (ROOT/'foundry.toml').read_bytes()==config,'Concurrent config change; preserve both for review'
 (ROOT/'foundry.toml').write_bytes(source)
after={p.relative_to(ROOT).as_posix():sha(p)for p in paths}
artifact=OWN/'out'/(target+'.t.sol')/(target+'Test.json')
artifact_hash=None
if artifact.exists():
 shutil.copy2(artifact,d/'producer-artifact.json');artifact_hash=sha(d/'producer-artifact.json')
methods=[]
try:
 raw=json.loads((d/'raw.json').read_bytes())
 for host,body in raw.items():
  for name,result in body.get('test_results',{}).items():
   methods.append({'id':host+'.'+name,'status':result.get('status'),'reason':result.get('reason'),
     'logs':result.get('decoded_logs'),'gas':result.get('gas')})
except(ValueError,AttributeError):pass
result={'exit_code':code,'error':error,'elapsed_seconds':time.monotonic()-start,'methods':methods,
 'source_before':before,'source_after':after,'source_bracket_stable':before==after,
 'base_config_unchanged':(ROOT/'foundry.toml').read_bytes()==source,'raw_sha256':sha(d/'raw.json'),
 'stderr_sha256':sha(d/'stderr.log'),'old_test_methods_executed':0,'public_RPC_or_transactions':False,
 'producer_artifact_sha256':artifact_hash,'producer_source_snapshot_sha256':sha(d/'SOURCE_TEST.sol.txt'),
 'runtime_limit_override':'Test aggregate harness ONLY; not production size admission'}
(d/'EXECUTION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k]for k in('exit_code','error','elapsed_seconds','methods','source_bracket_stable','base_config_unchanged')}),flush=True)
if not methods:print(json.dumps((d/'stderr.log').read_text(encoding='utf-8',errors='replace')[-3000:],ensure_ascii=True))
if code or error or not methods or any(m['status']!='Success'for m in methods):sys.exit(1)
