"""Three NEW policy cases in an exact minimal dependency copy, no root edits."""
from pathlib import Path
import gzip,hashlib,json,os,re,shutil,subprocess,sys,time,tomllib
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
D=V/'royalty-rounds-20261118/policy/isolated01';D.mkdir(exist_ok=False);W=D/'workspace';W.mkdir()
TARGET='test/RoyaltyBalancePolicy20261118.t.sol'
def sha(b):return hashlib.sha256(b).hexdigest()
config=(R/'foundry.toml').read_bytes();cfg=tomllib.loads(config.decode())['profile']['default']
remaps=[tuple(s.split('=',1))for s in cfg['remappings']]
texts={};todo=[TARGET]
while todo:
 name=todo.pop()
 if name in texts:continue
 raw=(R/name).read_bytes();texts[name]=raw
 stripped=re.sub(r'/\*.*?\*/','',raw.decode(),flags=re.S)
 for imp in re.findall(r'^\s*import\s+[^;]*?[\"\']([^\"\']+)[\"\']\s*;',stripped,flags=re.M):
  if imp.startswith('.'):dep=os.path.normpath(str(Path(name).parent/imp)).replace('\\','/')
  else:
   dep=imp
   for prefix,replacement in remaps:
    if imp.startswith(prefix):dep=replacement+imp[len(prefix):];break
  assert not dep.startswith('../')and(R/dep).is_file(),(name,imp,dep)
  todo.append(dep)
for name,raw in texts.items():
 p=W/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
(W/'foundry.toml').write_bytes(config)
before={n:sha(b)for n,b in texts.items()}
cmd=[str(V/'foundry-v1.4.4/forge.exe'),'test','--offline','--root',str(W),'--use',str(V/'toolchain-0.8.26/solc.exe'),
 '--match-path',TARGET,'--match-contract','RoyaltyBalancePolicy20261118Test','--match-test','^testRoyaltyReadPolicy',
 '--out',str(D/'out'),'--cache-path',str(D/'cache'),'--code-size-limit','1000000','-vvv','--json']
env={k:v for k,v in os.environ.items()if k.upper()in('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT')}
env['PATH']=str(V/'toolchain-0.8.26')+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32');env['RAYON_NUM_THREADS']='2'
start={'schema':1,'scope':'only3newrealPolicytests; exact minimaldependencycopy, controlledAccessanswers; notfullgraph/markets/qualification',
 'command':cmd,'source_before_sha256':before,'root_foundry_sha256':sha(config),'copied_foundry_byte_identical':True,
 'source_copy_closed_files':len(texts),'source_copy_nopatches':True,
 'tools':{str(p):sha(p.read_bytes())for p in(V/'foundry-v1.4.4/forge.exe',V/'toolchain-0.8.26/solc.exe')},
 'environment':'allowlistedOSonly; nosigner/RPC/private variables','runtime_override':'aggregateTESTONLY; no production size/gas/budget change'}
(D/'START.json').write_text(json.dumps(start,indent=2)+'\n')
then=time.monotonic()
with(D/'raw.json').open('xb')as out,(D/'stderr.log').open('xb')as err:
 p=subprocess.Popen(cmd,cwd=W,env=env,stdout=out,stderr=err);(D/'PID.json').write_text(json.dumps({'pid':p.pid})+'\n');code=p.wait(timeout=1200)
methods=[]
try:
 for host,body in json.loads((D/'raw.json').read_bytes()).items():
  for name,result in body.get('test_results',{}).items():methods.append({'id':host+'.'+name,'status':result.get('status'),'reason':result.get('reason')})
except(ValueError,AttributeError):pass
artifact=D/'out'/'RoyaltyBalancePolicy20261118.t.sol'/'RoyaltyBalancePolicy20261118Test.json'
proof={}
if artifact.exists():
 shutil.copy2(artifact,D/'producer-artifact.json');obj=json.loads(artifact.read_bytes());meta=obj['metadata'];sys.path.insert(0,str(R));from zzz_ops.abi import keccak256
 assert set(meta['sources'])==set(texts)
 for name,row in meta['sources'].items():
  compilertext=texts[name].replace(b'\r\n',b'\n');digest='0x'+keccak256(compilertext).hex();assert digest==row['keccak256'],name
  proof[name]={'filesystem_sha256':before[name],'compiler_keccak256':digest,'crlf_normalized':compilertext!=texts[name]}
 (D/'COMPILED_SOURCE_POOL.json.gz').write_bytes(gzip.compress(json.dumps({'sources':{n:{'content':b.replace(b'\r\n',b'\n').decode()}for n,b in texts.items()},'compiler':meta['compiler'],'settings':meta['settings']},separators=(',',':')).encode(),mtime=0))
copy_after={n:sha((W/n).read_bytes())for n in texts};root_after={n:sha((R/n).read_bytes())for n in texts}
result={'schema':1,'exit_code':code,'elapsed_seconds':time.monotonic()-then,'methods':methods,'selected_methods':len(methods),
 'copy_source_before_after_equal':before==copy_after,'root_selected_source_before_after_equal':before==root_after,'root_config_unchanged':sha((R/'foundry.toml').read_bytes())==sha(config),
 'compiled_source_identity_verified':proof,'raw_sha256':sha((D/'raw.json').read_bytes()),'stderr_sha256':sha((D/'stderr.log').read_bytes()),'unchanged_prior_methods_rerun':0,'production_approved':False}
result['pass']=code==0 and len(methods)==3 and all(m['status']=='Success'for m in methods)and before==copy_after and bool(proof)
(D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in('exit_code','elapsed_seconds','selected_methods','methods','copy_source_before_after_equal','root_selected_source_before_after_equal','pass')}),flush=True)
if not methods:print((D/'raw.json').read_text(errors='replace')[-4000:]);print((D/'stderr.log').read_text(errors='replace')[-4000:])
sys.exit(0 if result['pass']else 1)
