from pathlib import Path
import hashlib,json,os,re,subprocess,time
r=Path.cwd();e=Path(__file__).parent;v=e.parents[1]
stage=e/'evm-initial';stage.mkdir(exist_ok=False);build=e/'build';build.mkdir(exist_ok=False)
forge=v/'foundry-v1.4.4/forge.exe';solc=v/'toolchain-0.8.26/solc.exe'
normal=v/'exact-lp-solidity-20261106/physical-d7f78dc7d6/normal-final-c5967be9f9/START.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(path):return {p.relative_to(r).as_posix():sha(p) for p in (r/path).rglob('*.sol')}
sources=pins('src');tests=pins('test');cfg=sha(r/'foundry.toml');tool={'forge':sha(forge),'solc':sha(solc)}
accepted=json.loads(normal.read_text());normal_pins=accepted.get('source_sha256',accepted.get('sources_before',{}))
assert normal_pins and all(normal_pins.get(k)==h for k,h in sources.items())
closed={k:sha(r/k) for k in json.loads((e/'abi-corrected/status.json').read_text())['source_after']}
new='test/ExactLPAllocation.t.sol';expected=set(re.findall(r'function (test\w+)\(', (r/new).read_text()));assert len(expected)==14
command=[str(forge),'test','--root',str(r),'--use',str(solc),'--offline','--match-contract','^ExactLPAllocationTest$',
 '--match-path',new,'--match-test','^(testExactLP|testFuzzExactLP)','--fuzz-runs','1000','--threads','1','--json','-vv',
 '--out',str(build/'out'),'--cache-path',str(build/'cache')]
keep=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','HOMEDRIVE','HOMEPATH')
env={k:os.environ[k] for k in keep if k in os.environ};env.update(FOUNDRY_CODE_SIZE_LIMIT='1000000',FOUNDRY_OFFLINE='true',FOUNDRY_FFI='false',PYTHONDONTWRITEBYTECODE='1')
env['PATH']=str(forge.parent)+os.pathsep+str(solc.parent)+os.pathsep+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32')
(stage/'START.json').write_text(json.dumps({'command':command,'normal_source_basis':str(normal),'production_before':sources,'tests_before':tests,
 'closed_before':closed,'toolchain_sha256':tool,'config_sha256':cfg,'credentials_inherited':False,'fixture_code_size_limit':1000000,
 'expected_methods':sorted(expected),'fuzz_runs_per_property':1000,'fresh_isolated_cache':True},indent=2)+'\n')
start=time.monotonic()
with (stage/'stdout.json').open('wb') as so,(stage/'stderr.log').open('wb') as se:
 p=subprocess.Popen(command,cwd=r,env=env,stdout=so,stderr=se);(stage/'process.json').write_text(json.dumps({'pid':p.pid,'owned_test_process':True})+'\n')
 try:code=p.wait(timeout=1200)
 except subprocess.TimeoutExpired:p.kill();p.wait();(stage/'TIMEOUT.json').write_text('{"timeout_seconds":1200,"terminated":true}\n');raise
methods={};error=None
try:
 data=json.loads((stage/'stdout.json').read_text())
 for suite,body in data.items():
  if isinstance(body,dict):
   for name,item in body.get('test_results',{}).items():methods[suite+'::'+name]={'status':item['status'],'reason':item.get('reason'),'kind':item.get('kind'),'counterexample':item.get('counterexample')}
except ValueError:error='Missing or invalid Forge JSON; raw streams retained.'
after=pins('src');ta=pins('test');ca={k:sha(r/k) for k in closed};seen={k.split('::')[-1].split('(')[0] for k in methods}
status={'exit_code':code,'elapsed_seconds':time.monotonic()-start,'methods':methods,'expected_methods':sorted(expected),'exact_method_set':seen==expected,
 'parse_error':error,'source_before':sources,'source_after':after,'source_unchanged':sources==after,'test_before':tests,'test_after':ta,'tests_unchanged':tests==ta,
 'closed_before':closed,'closed_after':ca,'closed_unchanged':closed==ca,'config_unchanged':cfg==sha(r/'foundry.toml'),
 'toolchain_unchanged':tool=={'forge':sha(forge),'solc':sha(solc)},'fixture_code_size_limit':1000000,
 'scope':'Only new internal engine/harness;14methods including2fuzz properties*1000runs. Real current Rewards/Vault/canonical/services/sites/chains/journals/signers are NOT integrated or changed. Fixed2logical books have no tokens or funding/owner checks. Full-node walks exist only in test oracle/invariant/digest. Cold gas is external harness+engine, not host/transfer/router/intrinsic or operating qualification.'}
status['successful']=code==0 and seen==expected and all(x['status']=='Success' for x in methods.values()) and all(status[k] for k in ('source_unchanged','tests_unchanged','closed_unchanged','config_unchanged','toolchain_unchanged'))
(stage/'status.json').write_text(json.dumps(status,indent=2)+'\n')
print(json.dumps({'successful':status['successful'],'exit_code':code,'methods':methods,'elapsed_seconds':status['elapsed_seconds'],'parse_error':error},indent=2),flush=True)
raise SystemExit(not status['successful'])
