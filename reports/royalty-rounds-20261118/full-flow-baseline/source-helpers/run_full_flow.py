"""Run one NEW frozen rounds2 near-capacity method and its ten exports only.

Only an owned export filesystem permission is temporarily added and restored.
The aggregate test's resources do not change production or actual RPC budgets.
"""
from pathlib import Path
import gzip,hashlib,json,os,re,shutil,subprocess,sys,time,tomllib

ROOT=Path(__file__).resolve().parents[2]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OWN=V/'royalty-rounds-20261118'
TARGET='RoyaltyRoundsCapacity20261118'
METHOD='testRoundsFull1000DenseCurrenciesOpeningRotationsAllFaultsAndGrowth()'
FIXTURE_SHA256='123492acdbf7e2696f8a8bdca6580a6ccde7267f7cba863e851d211f251e0fdf'
EXPECTED_CASES=['rounds-999-opening-eth','rounds-999-opening-zzz-allfault','rounds-999-rotated-zzz',
 'rounds-999-rotated-eth-onefault','rounds-999-rotated-eth-allfault','rounds-999-rotated-zzz-allfault',
 'rounds-999-rotated-zzz-allslow','rounds-999-rotated-eth','rounds-1000-grow-eth','rounds-1000-grow-zzz-allfault']
PROTECTED=['reports/source-checks.json','scripts/run-fork-checks.py','tests_python/test_fork_runner.py','tests_python/test_frontend_history.py']
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def closure(start,config):
 remaps=[tuple(row.split('=',1))for row in tomllib.loads(config.decode())['profile']['default']['remappings']]
 found={};todo=[start]
 while todo:
  name=todo.pop()
  if name in found:continue
  raw=(ROOT/name).read_bytes();found[name]=raw
  text=re.sub(r'/\*.*?\*/','',raw.decode(),flags=re.S)
  for imp in re.findall(r'^\s*import\s+[^;]*?[\"\']([^\"\']+)[\"\']\s*;',text,flags=re.M):
   if imp.startswith('.'):name2=os.path.normpath(str(Path(name).parent/imp)).replace('\\','/')
   else:
    name2=imp
    for prefix,replacement in remaps:
     if imp.startswith(prefix):name2=replacement+imp[len(prefix):];break
   assert not name2.startswith('../')and(ROOT/name2).is_file(),(name,imp,name2)
   todo.append(name2)
 return found

def main():
 assert len(sys.argv)in(1,2)
 stage=sys.argv[1]if len(sys.argv)==2 else'full01';assert re.fullmatch(r'full[0-9]{2}',stage)
 d=OWN/stage;d.mkdir(parents=True,exist_ok=False);exports=d/'exports';exports.mkdir()
 original=(ROOT/'foundry.toml').read_bytes();assert original.count(b'fs_permissions = [')==1
 fixture=ROOT/'test'/(TARGET+'.t.sol');assert sha(fixture.read_bytes())==FIXTURE_SHA256
 scope=json.loads((ROOT/'reports/royalty-rounds-20261118/FULL_FLOW_SCOPE.json').read_bytes())
 assert scope['new_fixture_sha256']==FIXTURE_SHA256 and scope['new_export_cases']==10 and scope['budget']==20_000_000 and scope['padding_bps']==2000
 sources=closure('test/'+TARGET+'.t.sol',original)
 source_paths={p.relative_to(ROOT).as_posix()for p in(ROOT/'src').rglob('*.sol')}|set(sources)|set(PROTECTED)|{'foundry.toml'}
 before={name:sha((ROOT/name).read_bytes())for name in sorted(source_paths)}
 (d/'SOURCE_TEST.sol.txt').write_bytes(fixture.read_bytes())
 (d/'COMPILED_INPUT_SOURCE_POOL.json.gz').write_bytes(gzip.compress(json.dumps({'sources':{name:{'content':raw.replace(b'\r\n',b'\n').decode()}for name,raw in sources.items()}},separators=(',',':')).encode(),mtime=0))
 temporary=original.replace(b'fs_permissions = [',('fs_permissions = [{ access = "read-write", path = "'+exports.as_posix()+'" }, ').encode())
 (d/'foundry.toml').write_bytes(temporary);(d/'ORIGINAL_foundry.toml').write_bytes(original)
 forge=V/'foundry-v1.4.4/forge.exe';solc=V/'toolchain-0.8.26/solc.exe'
 assert sha(forge.read_bytes())=='8500da38f541a1ebd5b97a34c8c5b9b057eba5ad160c657a5224b4e1c8f8e101'
 assert sha(solc.read_bytes())=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
 cmd=[str(forge),'test','--offline','--use',str(solc),'--root',str(ROOT),
  '--match-path','test/'+TARGET+'.t.sol','--match-contract',TARGET+'Test',
  '--match-test','^'+METHOD[:-2],'--out',str(OWN/'full-out'),'--cache-path',str(OWN/'full-cache'),
  '--code-size-limit','1000000','-vv','--json']
 retained={Path(name).name for name in sources}
 skipped=sorted({p.name for p in(ROOT/'test').rglob('*.sol')if p.name not in retained})
 for name in skipped:cmd+=['--skip',name]
 env={k:v for k,v in os.environ.items()if k.upper()in('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT')}
 env.update(PATH=str(solc.parent)+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32'),RAYON_NUM_THREADS='2',
  POPL_REFERENCE_EXPORT_PATH=str(exports/'setup'),POPL_GAS_PROFILE_EXPORT_ROOT=str(exports),
  FOUNDRY_GAS_LIMIT='10000000000',FOUNDRY_MEMORY_LIMIT='536870912')
 start={'schema':1,'command':cmd,'source_before':before,'compiled_closure_files':len(sources),
  'compiled_input_pool_sha256':sha((d/'COMPILED_INPUT_SOURCE_POOL.json.gz').read_bytes()),
  'config_sha256':sha(temporary),'base_config_sha256':sha(original),'runner_sha256':sha(Path(__file__).read_bytes()),
  'tools':{str(p):sha(p.read_bytes())for p in(forge,solc)},'skipped_unrelated_test_roots':skipped,
  'environment':'Allowlisted OS variables and owned export paths only; no RPC/private/signer variables',
  'started_unix':time.time(),'harness_only_resources':{'gas_limit':10_000_000_000,'memory_limit':536_870_912,
   'code_size_limit':1_000_000,'actual_entry_cap':20_000_000,'diagnostic_only_cap':32_000_000,
   'normal_limits_and_production_defaults_changed':False}}
 (d/'START.json').write_text(json.dumps(start,indent=2)+'\n')
 begin=time.monotonic();code=None;error=None;restored=False
 try:
  assert (ROOT/'foundry.toml').read_bytes()==original
  (ROOT/'foundry.toml').write_bytes(temporary)
  probe=subprocess.run([str(forge),'config','--json','--root',str(ROOT)],cwd=ROOT,env=env,capture_output=True,timeout=30)
  assert probe.returncode==0;values=json.loads(probe.stdout)
  selected={k:values.get(k)for k in('gas_limit','memory_limit','solc','evm_version','optimizer','optimizer_runs','via_ir','optimizer_details','fs_permissions')}
  assert selected['gas_limit']==10_000_000_000 and selected['memory_limit']==536_870_912
  (d/'HARNESS_RESOURCES.json').write_text(json.dumps(selected,indent=2)+'\n')
  with(d/'raw.json').open('xb')as out,(d/'stderr.log').open('xb')as err:
   proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=out,stderr=err)
   (d/'PID.json').write_text(json.dumps({'pid':proc.pid,'command':cmd})+'\n')
   try:code=proc.wait(timeout=2400)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=15);error='Owned full test process timeout; not a pass'
 except Exception as exc:error=type(exc).__name__+': '+str(exc)
 finally:
  current=(ROOT/'foundry.toml').read_bytes()
  if current==temporary:(ROOT/'foundry.toml').write_bytes(original);restored=True
  elif current==original:restored=True
  else:(d/'UNEXPECTED_foundry.toml').write_bytes(current);error=(error or'')+' Concurrent config change; preserved without overwriting it'
 after={name:sha((ROOT/name).read_bytes())for name in sorted(source_paths)}
 methods=[]
 try:
  for host,body in json.loads((d/'raw.json').read_bytes()).items():
   for name,res in body.get('test_results',{}).items():methods.append({'id':host+':'+name,'status':res.get('status'),'reason':res.get('reason'),'logs':res.get('decoded_logs')})
 except(ValueError,AttributeError,FileNotFoundError):pass
 artifact=OWN/'full-out'/(TARGET+'.t.sol')/(TARGET+'Test.json');metadata_verified=False
 if artifact.exists():
  shutil.copy2(artifact,d/'producer-artifact.json');obj=json.loads(artifact.read_bytes());meta=obj['metadata']
  sys.path.insert(0,str(ROOT));from zzz_ops.abi import keccak256
  assert set(meta['sources'])==set(sources)
  for name,row in meta['sources'].items():assert row['keccak256']=='0x'+keccak256(sources[name].replace(b'\r\n',b'\n')).hex(),name
  metadata_verified=True
 expected_id='test/'+TARGET+'.t.sol:'+TARGET+'Test:'+METHOD
 result={'schema':1,'exit_code':code,'error':error,'elapsed_seconds':time.monotonic()-begin,'methods':methods,
  'source_before':before,'source_after':after,'source_bracket_stable':before==after,'base_config_unchanged':restored,
  'compiled_source_metadata_verified':metadata_verified,'unchanged_old_tests_executed':0,'public_RPC_or_transactions':False,
  'producer_artifact_sha256':sha((d/'producer-artifact.json').read_bytes())if(d/'producer-artifact.json').exists()else None,
  'raw_sha256':sha((d/'raw.json').read_bytes())if(d/'raw.json').exists()else None,
  'stderr_sha256':sha((d/'stderr.log').read_bytes())if(d/'stderr.log').exists()else None,'production_approved':False}
 result['pass']=code==0 and error is None and len(methods)==1 and methods[0]['id']==expected_id and methods[0]['status']=='Success'and before==after and restored and metadata_verified
 (d/'EXECUTION.json').write_text(json.dumps(result,indent=2)+'\n')
 if result['pass']:
  (d/'PRODUCER.json').write_text(json.dumps({'schema':1,'method_ids':[expected_id],'case_labels':EXPECTED_CASES,
   'raw_sha256':result['raw_sha256'],'start_sha256':sha((d/'START.json').read_bytes()),'artifact_sha256':result['producer_artifact_sha256']},indent=2)+'\n')
 print(json.dumps({k:result[k]for k in('exit_code','error','elapsed_seconds','pass','source_bracket_stable','base_config_unchanged','compiled_source_metadata_verified')}),flush=True)
 for method in methods:print(json.dumps({k:v for k,v in method.items()if k!='logs'}),flush=True)
 if not methods and(d/'raw.json').exists():print((d/'raw.json').read_text(errors='replace')[-3500:])
 return 0 if result['pass']else 1

if __name__=='__main__':raise SystemExit(main())
