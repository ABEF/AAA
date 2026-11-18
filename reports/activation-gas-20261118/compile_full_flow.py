"""Compile only the new final workload into its existing owned Forge cache.

No test execution, export permission, root configuration change or environment
adoption. Build and the subsequent test use the same compiler/output/cache.
"""
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,re,subprocess,sys,time

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rounds_full_runner',P/'run_full_flow.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
V=runner.V;OWN=runner.OWN
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
 assert len(sys.argv)==2 and re.fullmatch(r'full[0-9]{2}-compile[0-9]{2}',sys.argv[1]),'Use one new owned compile-only stage'
 D=OWN/sys.argv[1]
 D.mkdir(exist_ok=False)
 config=(R/'foundry.toml').read_bytes();fixture='test/'+runner.TARGET+'.t.sol'
 assert sha((R/fixture).read_bytes())==runner.FIXTURE_SHA256
 sources=runner.closure(fixture,config)
 before={name:sha(raw)for name,raw in sources.items()}
 freeze_raw=(OWN/'SOURCE_FREEZE.json').read_bytes();freeze=json.loads(freeze_raw)
 root_sources={p.relative_to(R).as_posix():sha(p.read_bytes())for p in(R/'src').rglob('*.sol')}
 assert freeze['schema']==1 and freeze['source_sha256']==root_sources and freeze['fixture_sha256']==runner.FIXTURE_SHA256
 assert freeze['foundry_toml_sha256']==sha(config)
 assert all(sha((R/name).read_bytes())==pin for name,pin in freeze['protected_sha256'].items())
 (D/'SOURCE_POOL.json.gz').write_bytes(gzip.compress(json.dumps({'sources':{name:{'content':raw.replace(b'\r\n',b'\n').decode()}for name,raw in sources.items()}},separators=(',',':')).encode(),mtime=0))
 retained={Path(name).name for name in sources}
 skipped=sorted({p.name for p in(R/'test').rglob('*.sol')if p.name not in retained})
 forge=V/'foundry-v1.4.4/forge.exe';solc=V/'toolchain-0.8.26/solc.exe'
 assert sha(forge.read_bytes())=='8500da38f541a1ebd5b97a34c8c5b9b057eba5ad160c657a5224b4e1c8f8e101'
 assert sha(solc.read_bytes())=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
 cmd=[str(forge),'build','--offline','--use',str(solc),'--root',str(R),'--out',str(OWN/'full-out'),'--cache-path',str(OWN/'full-cache')]
 for name in skipped:cmd+=['--skip',name]
 env={k:v for k,v in os.environ.items()if k.upper()in('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT')}
 env.update(PATH=str(solc.parent)+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32'),RAYON_NUM_THREADS='2')
 start={'schema':1,'source_freeze_sha256':sha(freeze_raw),'scope':'Compile only;0test executions, root configuration byte-identical, no exports/network/signing','command':cmd,'source_before':before,'config_sha256':sha(config),'tools':{str(p):sha(p.read_bytes())for p in(forge,solc)},'source_pool_sha256':sha((D/'SOURCE_POOL.json.gz').read_bytes())}
 (D/'START.json').write_text(json.dumps(start,indent=2)+'\n',encoding='utf-8');then=time.monotonic()
 with(D/'stdout.log').open('xb')as out,(D/'stderr.log').open('xb')as err:
  proc=subprocess.Popen(cmd,cwd=R,env=env,stdout=out,stderr=err);(D/'PID.json').write_text(json.dumps({'pid':proc.pid,'command':cmd})+'\n',encoding='utf-8')
  try:code=proc.wait(timeout=2400)
  except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=15);raise RuntimeError('Owned compile-only process exceeded2400s; no test execution')
 after={name:sha((R/name).read_bytes())for name in sources}
 artifact=OWN/'full-out'/(runner.TARGET+'.t.sol')/(runner.TARGET+'Test.json')
 metadata_ok=False
 if code==0 and artifact.exists():
  obj=json.loads(artifact.read_bytes());metadata=obj['metadata'];assert set(metadata['sources'])==set(sources)
  sys.path.insert(0,str(R));from zzz_ops.abi import keccak256
  for name,row in metadata['sources'].items():assert row['keccak256']=='0x'+keccak256(sources[name].replace(b'\r\n',b'\n')).hex(),name
  metadata_ok=True
  (D/'producer-artifact.json.gz').write_bytes(gzip.compress(artifact.read_bytes(),mtime=0))
 protected_after={name:sha((R/name).read_bytes())for name in freeze['protected_sha256']}
 result={'protected_four_unchanged':protected_after==freeze['protected_sha256'],'exit_code':code,'elapsed_seconds':time.monotonic()-then,'source_bracket_stable':before==after,'base_config_byte_identical':(R/'foundry.toml').read_bytes()==config,'compiled_metadata_source_identities_verified':metadata_ok,'test_executions':0,'production_approved':False}
 result['pass']=code==0 and before==after and result['base_config_byte_identical']and metadata_ok and result['protected_four_unchanged']
 (D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
 return 0 if result['pass']else 1
if __name__=='__main__':raise SystemExit(main())
