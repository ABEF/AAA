from pathlib import Path
import hashlib,json,os,re,subprocess,time,shutil
r=Path.cwd();e=Path(__file__).parent;v=e.parents[1];stage=e/'evm-priority-native-core';stage.mkdir(exist_ok=False);build=e/'build';
assert build.is_dir()
forge=v/'foundry-v1.4.4/forge.exe';solc=v/'toolchain-0.8.26/solc.exe';normal=v/'exact-lp-integration-20261106-64f9/normal-final-5994e91eed/START.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(path):return {p.relative_to(r).as_posix():sha(p) for p in (r/path).rglob('*.sol')}
sources=pins('src');cfg=sha(r/'foundry.toml');tool={'forge':sha(forge),'solc':sha(solc)};normal_pins=json.loads(normal.read_text())['source_sha256'];assert all(normal_pins.get(k)==h for k,h in sources.items())
closed={k:sha(r/k) for k in json.loads((e/'abi-priority-native-core/status.json').read_text())['source_after']};test='test/VaultAccounting.t.sol';expected={'testUnsealedSystemCannotMint', 'testHarvestAuditBothLegEntryCheckpointsAndSecondLegFailureRollback', 'testActualV4EntrantSwapFeesBelongOnlyToIncumbentBeforeSharesIssue', 'testOldDepositSelectorCannotBypassPaidMint'}
command=[str(forge),'test','--root',str(r),'--use',str(solc),'--offline','--match-contract','^(VaultAccountingTest|IntegratedEconomicConservationTest|HarvestAuditActualV4Test)$','--match-test','^(testOldDepositSelectorCannotBypassPaidMint|testUnsealedSystemCannotMint|testActualV4EntrantSwapFeesBelongOnlyToIncumbentBeforeSharesIssue|testHarvestAuditBothLegEntryCheckpointsAndSecondLegFailureRollback)\(','--fuzz-runs','1000','--threads','1','--json','-vv','--out',str(build/'out'),'--cache-path',str(build/'cache')]
command+=sum((['--skip',p.relative_to(r).as_posix()] for p in list((r/'test').rglob('*.t.sol'))+list((r/'script').rglob('*.sol')) if p.relative_to(r).as_posix() not in closed),[])
keep=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','HOMEDRIVE','HOMEPATH');env={k:os.environ[k] for k in keep if k in os.environ};env.update(FOUNDRY_CODE_SIZE_LIMIT='1000000',FOUNDRY_OFFLINE='true',FOUNDRY_FFI='false',PYTHONDONTWRITEBYTECODE='1');env['PATH']=str(forge.parent)+os.pathsep+str(solc.parent)+os.pathsep+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32')
(stage/'START.json').write_text(json.dumps({'command':command,'normal_source_basis':str(normal),'production_before':sources,'closed_before':closed,'toolchain_sha256':tool,'config_sha256':cfg,'credentials_inherited':False,'fixture_code_size_limit':1000000,'expected_methods':sorted(expected)},indent=2)+'\n');snapshot=stage/'test-sources';snapshot.mkdir();
for path in closed:
 if path.startswith('test/'):
  dest=snapshot/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/path,dest)
start=time.monotonic()
with (stage/'stdout.json').open('wb')as so,(stage/'stderr.log').open('wb')as se:
 p=subprocess.Popen(command,cwd=r,env=env,stdout=so,stderr=se);(stage/'process.json').write_text(json.dumps({'pid':p.pid,'owned_test_process':True}));print('Started ONLY4 priority corrected-native/actual-core controls',p.pid,flush=True)
 try:code=p.wait(timeout=1800)
 except subprocess.TimeoutExpired:p.kill();p.wait();(stage/'TIMEOUT.json').write_text('{"timeout_seconds":1800,"terminated":true}');raise
methods={};error=None
try:
 data=json.loads((stage/'stdout.json').read_text())
 for suite,body in data.items():
  if isinstance(body,dict):
   for name,item in body.get('test_results',{}).items():methods[suite+'::'+name]={'status':item['status'],'reason':item.get('reason'),'gas':item.get('kind'),'counterexample':item.get('counterexample')}
except ValueError:error='Missing/invalidForgeJSON;raw retained'
after=pins('src');ca={k:sha(r/k) for k in closed};seen={k.split('::')[-1].split('(')[0]for k in methods};status={'exit_code':code,'elapsed_seconds':time.monotonic()-start,'methods':methods,'expected_methods':sorted(expected),'exact_method_set':seen==expected,'parse_error':error,'source_before':sources,'source_after':after,'source_unchanged':sources==after,'closed_before':closed,'closed_after':ca,'closed_unchanged':closed==ca,'config_unchanged':cfg==sha(r/'foundry.toml'),'toolchain_unchanged':tool=={'forge':sha(forge),'solc':sha(solc)},'fixture_code_size_limit':1000000,'scope':'FOUR bounded priority correctednative+actualPoolManager/PositionManager controls ONLY, defaultgasbudget,realNFT/Fees/Rewards/Membership; authenticated synthetic shares+conversion seam,noactual-v4 route qualification,1000 functional calls aggregated with meteringpaused notone1000Tx;separatecoldgasmeasured.'};status['successful']=code==0 and seen==expected and all(x['status']=='Success'for x in methods.values())and all(status[k]for k in ('source_unchanged','closed_unchanged','config_unchanged','toolchain_unchanged'));(stage/'status.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps({'exit_code':code,'elapsed_seconds':status['elapsed_seconds'],'count':len(methods),'failures':{k:x['reason']for k,x in methods.items()if x['status']!='Success'},'successful':status['successful']},indent=2))
