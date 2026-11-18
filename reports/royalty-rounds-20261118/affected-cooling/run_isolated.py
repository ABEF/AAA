"""Two affected cooling cases; exact byte-sliced harness and production closure, no root edits."""
from pathlib import Path
import gzip,hashlib,json,os,re,shutil,subprocess,sys,time,tomllib
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
D=V/'royalty-rounds-20261118/affected-cooling/isolated01';D.mkdir(exist_ok=False);W=D/'workspace';W.mkdir()
TARGET='test/RoyaltyAudit20261105.t.sol'
FUNCTIONS=['_ledger','setUp','_worstPrefix','_coolLedger','_coolRecordedContracts',
 'testGasWorstRotatedColdFullSyncFitsGovernedOptionalBudget',
 'testHealthyOptionalCurrencyIsNotDeferredByExactAllocatorDefaultBudget']
PROTECTED=['reports/source-checks.json','scripts/run-fork-checks.py','tests_python/test_fork_runner.py','tests_python/test_frontend_history.py']

def function_slice(text,name):
 begin=text.index('    function '+name+'(');opening=text.index('{',begin);i=opening;depth=0;state='normal';quote=''
 while i<len(text):
  ch=text[i];nxt=text[i+1:i+2]
  if state=='line':
   if ch=='\n':state='normal'
  elif state=='block':
   if ch=='*'and nxt=='/':state='normal';i+=1
  elif state=='string':
   if ch=='\\':i+=1
   elif ch==quote:state='normal'
  elif ch=='/'and nxt=='/':state='line';i+=1
  elif ch=='/'and nxt=='*':state='block';i+=1
  elif ch in('\"',"'"):state='string';quote=ch
  elif ch=='{':depth+=1
  elif ch=='}':
   depth-=1
   if depth==0:return text[begin:i+1]
  i+=1
 raise ValueError('Unterminated selected function')

def sha(b):return hashlib.sha256(b).hexdigest()
config=(R/'foundry.toml').read_bytes()
normal=json.loads((R/'reports/royalty-rounds-20261118/build/current/START.json').read_bytes())
assert sha(config)==normal['build_input_sha256']['foundry.toml'],'Root normal configuration is not restored'
assert sha((V/'toolchain-0.8.26/solc.exe').read_bytes())=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
profile=json.loads((R/'reports/royalty-rounds-20261118/build/current/EFFECTIVE_NORMAL_PROFILE.json').read_bytes())
assert sha((V/'foundry-v1.4.4/forge.exe').read_bytes())==profile['forge_file_sha256']
cfg=tomllib.loads(config.decode())['profile']['default']
remaps=[tuple(s.split('=',1))for s in cfg['remappings']]
original=(R/TARGET).read_bytes();text=original.decode();start=text.index('contract RoyaltyAudit20261105Test is Test {');fields_end=text.index('    function _ledger(',start)
projection='''// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
// TEST ONLY exact selected-method projection; source bodies authenticated below.
import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {InKindNFT} from "./RoyaltyRecovery.t.sol";
import {MockAccess,MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
'''+text[start:fields_end]+'\n\n'.join(function_slice(text,n)for n in FUNCTIONS)+'\n}\n'
function_proof={n:sha(function_slice(text,n).encode())for n in FUNCTIONS}
assert function_proof=={n:sha(function_slice(projection,n).encode())for n in FUNCTIONS}
protected_before={n:sha((R/n).read_bytes())for n in PROTECTED}
texts={};root_before={};todo=[TARGET]
while todo:
 name=todo.pop()
 if name in texts:continue
 original_raw=(R/name).read_bytes();root_before[name]=sha(original_raw);raw=projection.encode()if name==TARGET else original_raw;texts[name]=raw
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
 '--match-path',TARGET,'--match-contract','RoyaltyAudit20261105Test','--match-test','testGasWorstRotatedColdFullSyncFitsGovernedOptionalBudget|testHealthyOptionalCurrencyIsNotDeferredByExactAllocatorDefaultBudget',
 '--out',str(D/'out'),'--cache-path',str(D/'cache'),'--code-size-limit','1000000','-vvv','--json']
env={k:v for k,v in os.environ.items()if k.upper()in('SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT')}
env['PATH']=str(V/'toolchain-0.8.26')+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32');env['RAYON_NUM_THREADS']='2'
start={'schema':1,'scope':'only2affectedcoolingmethods; exactmethods/helpers in projectedharness, actualledger/dependencybytes; notfullgraph/profile/marketsapproval',
 'command':cmd,'source_before_sha256':before,'root_foundry_sha256':sha(config),'copied_foundry_byte_identical':True,
 'source_copy_closed_files':len(texts),'source_copy_nopatches':False,'only_projected_source':TARGET,
 'original_target_sha256':sha(original),'projected_target_sha256':sha(projection.encode()),'root_source_before_sha256':root_before,
 'exact_function_body_sha256':function_proof,'protected_before_sha256':protected_before,
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
artifact=D/'out'/'RoyaltyAudit20261105.t.sol'/'RoyaltyAudit20261105Test.json'
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
 'copy_source_before_after_equal':before==copy_after,'root_selected_source_before_after_equal':root_before==root_after,'root_config_unchanged':sha((R/'foundry.toml').read_bytes())==sha(config),
 'compiled_source_identity_verified':proof,'raw_sha256':sha((D/'raw.json').read_bytes()),'stderr_sha256':sha((D/'stderr.log').read_bytes()),'existing_affected_methods':2,'unrelated_old_methods_run':0,'protected_unchanged':protected_before=={n:sha((R/n).read_bytes())for n in PROTECTED},'production_approved':False}
result['pass']=code==0 and len(methods)==2 and all(m['status']=='Success'for m in methods)and before==copy_after and bool(proof)and root_before==root_after and result['protected_unchanged']and result['root_config_unchanged']
(D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in('exit_code','elapsed_seconds','selected_methods','methods','copy_source_before_after_equal','root_selected_source_before_after_equal','pass')}),flush=True)
if not methods:print((D/'raw.json').read_text(errors='replace')[-4000:]);print((D/'stderr.log').read_text(errors='replace')[-4000:])
sys.exit(0 if result['pass']else 1)
