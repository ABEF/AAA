"""Compile one frozen100-source normal graph, then admit it without recompiling.

No source writes, test execution, signing, deployment, sealing or environment
adoption. Unknown private layouts and public name changes need separate exact
review pins; size success alone is never a trusted-build pass.
"""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,os,re,subprocess,sys,time
from datetime import datetime,timezone

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R))
from zzz_ops.function_reference import BUILD_INPUTS,import_compiler
from zzz_ops.abi import keccak256
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OWN=V/'activation-final-six-20261118'
BASE=V/'activation-gas-20261118/build/final01'
PUB=R/'reports/activation-final-six-20261118/build/final'
BUILD_ID='activation-final-six-20261118'
SOLC=V/'toolchain-0.8.26/solc.exe';FORGE=V/'foundry-v1.4.4/forge.exe'
COMPILER='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
ALLOWED_SOURCE_CHANGES={
 'src/libraries/ExactLPAllocation.sol','src/ZZZRoyaltyRewards.sol',
 'src/libraries/ExactRoyaltyAllocation.sol','src/ZZZContributionPricing.sol',
 'src/ZZZOracle.sol','src/ZZZV4SpotPriceFeed.sol'}
PROTECTED={
 'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
sha=lambda b:hashlib.sha256(b).hexdigest()
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()

def save(path,value,*,new=True):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x'if new else'w',encoding='utf-8',newline='\n')as f:json.dump(value,f,indent=2);f.write('\n')

def semantic_type(layout,key,seen=()):
 row=layout['types'][key];r={k:row[k]for k in('encoding','label','numberOfBytes')}
 if key in seen:return {**r,'recursive':True}
 for k in('key','value','base'):
  if k in row:r[k]=semantic_type(layout,row[k],(*seen,key))
 if 'members'in row:r['members']=[{'label':x['label'],'slot':x['slot'],'offset':x['offset'],
  'type':semantic_type(layout,x['type'],(*seen,key))}for x in row['members']]
 return r

def semantic_storage(layout):
 return[{'contract':x['contract'],'label':x['label'],'slot':x['slot'],'offset':x['offset'],
  'type':semantic_type(layout,x['type'])}for x in layout['storage']]

def abi_arg(arg):
 # Names/internalType are cosmetic, but are reported independently below.
 assert set(arg)<= {'name','type','internalType','components','indexed'},arg
 row={k:arg[k]for k in('type','indexed')if k in arg}
 if 'components'in arg:row['components']=[abi_arg(x)for x in arg['components']]
 return row

def abi_row(row):
 assert set(row)<= {'type','name','inputs','outputs','stateMutability','anonymous'},row
 result={k:row[k]for k in('type','name','stateMutability','anonymous')if k in row}
 for key in('inputs','outputs'):
  if key in row:result[key]=[abi_arg(arg)for arg in row[key]]
 return result

def abi_model(abi):return sorted((abi_row(row)for row in abi),key=lambda row:canonical(row))

def abi_names(before,after):
 assert abi_model(before)==abi_model(after),'Public ABI type/signature/mutability changed'
 # Solidity can emit identical error signatures from two imported libraries.
 # Preserve their multiplicities; do not collapse rows or reject a valid ABI.
 by_before={};by_after={}
 for row in before:by_before.setdefault(canonical(abi_row(row)),[]).append(row)
 for row in after:by_after.setdefault(canonical(abi_row(row)),[]).append(row)
 changes=[]
 def args(a,b,path):
  for i,(x,y)in enumerate(zip(a,b)):
   here=path+'/'+str(i)
   for field in('name','internalType'):
    if x.get(field)!=y.get(field):changes.append({'field':here+'/'+field,'baseline':x.get(field),'final':y.get(field)})
   if 'components'in x:args(x['components'],y['components'],here+'/components')
 for key in sorted(by_before):
  aa,bb=by_before[key],by_after[key];assert len(aa)==len(bb)
  assert len(aa)==1 or aa[0]['type']=='error','Duplicate callable ABI signature'
  for occurrence,(a,b)in enumerate(zip(sorted(aa,key=canonical),sorted(bb,key=canonical))):
   label=key.decode('ascii')+('/occurrence/'+str(occurrence)if len(aa)>1 else'')
   for field in('inputs','outputs'):
    if field in a:args(a[field],b[field],label+'/'+field)
 return changes

def freeze():
 raw=(OWN/'SOURCE_FREEZE.json').read_bytes();f=json.loads(raw);assert f['schema']==1
 expected={p.relative_to(R).as_posix():sha(p.read_bytes())for p in(R/'src').rglob('*.sol')}
 assert len(expected)==61 and f['source_sha256']==expected,'Current sources differ from explicit freeze'
 assert f['protected_sha256']==PROTECTED and all(sha((R/n).read_bytes())==h for n,h in PROTECTED.items())
 assert f['foundry_toml_sha256']==sha((R/'foundry.toml').read_bytes())
 review=f['normal_build'];assert review['build_id']==BUILD_ID
 assert review['baseline_input_sha256']==sha((BASE/'compiler-input.json').read_bytes())
 assert review['baseline_output_sha256']==sha((BASE/'compiler-output.json').read_bytes())
 return raw,f

def compare(data,old,compiled,prior):
 gates=[];abis=[];layouts=[];details={}
 for g in prior['gates']:
  obj=compiled['contracts'][g['path']][g['name']];before=old['contracts'][g['path']][g['name']]
  rt=len(obj['evm']['deployedBytecode']['object'])//2;cr=len(obj['evm']['bytecode']['object'])//2
  gates.append({**g,'runtime':rt,'creation':cr,'runtime_margin':24576-rt,'maximum_total_argument_bytes':49152-cr,
   'runtime_delta':rt-len(before['evm']['deployedBytecode']['object'])//2,'creation_delta':cr-len(before['evm']['bytecode']['object'])//2,
   'runtime_ok':rt<=24576,'creation_ok':cr+g['minimum_args']<=49152})
  a=semantic_storage(before['storageLayout']);b=semantic_storage(obj['storageLayout']);identity=g['path']+':'+g['name']
  layouts.append({'path':g['path'],'name':g['name'],'identity':identity,'identical':a==b,'baseline_semantic_sha256':sha(canonical(a)),'final_semantic_sha256':sha(canonical(b))})
  if a!=b:details[identity]={'baseline':a,'final':b}
  if g['name']=='ZZZRewards':
   def carries(value):
    found=[]
    def walk(x):
     if isinstance(x,dict):
      if x.get('label')=='struct ExactLPAllocation.Carry':found.append(x)
      for v in x.values():walk(v)
     elif isinstance(x,list):
      for v in x:walk(v)
    walk(value);return found
   oldcarry=carries(a);newcarry=carries(b);assert oldcarry and newcarry and oldcarry==newcarry,'LP carry physical footprint changed'
   for c in newcarry:assert c['numberOfBytes']=='64'and[(m['label'],m['slot'],m['offset'],m['type']['label'])for m in c['members']]==[('packed','0',0,'uint256'),('wide','1',0,'uint256')]
 # Check all emitted ABI objects, including interfaces not represented by size gates.
 for path,contracts in old['contracts'].items():
  assert set(contracts)==set(compiled['contracts'][path]),('Contract inventory changed',path)
  for name,before in contracts.items():
   after=compiled['contracts'][path][name];same_types=abi_model(before['abi'])==abi_model(after['abi'])
   changes=abi_names(before['abi'],after['abi'])if same_types else[]
   abis.append({'path':path,'name':name,'identity':path+':'+name,'strictly_identical':before['abi']==after['abi'],
    'canonical_signatures_tuple_types_mutability_identical':same_types,'parameter_output_name_or_internalType_changes':changes})
 return gates,abis,layouts,details

def compile_stage(dest):
 freeze_raw,f=freeze();assert sha(SOLC.read_bytes())==COMPILER
 data=json.loads((BASE/'compiler-input.json').read_bytes());old=json.loads((BASE/'compiler-output.json').read_bytes());prior=json.loads((BASE/'RESULT.json').read_bytes())
 assert prior['pass']and len(data['sources'])==100 and len(prior['gates'])==48
 actual={n:sha((R/n).read_bytes())for n in data['sources']};changed=set()
 for n,row in data['sources'].items():
  text=(R/n).read_bytes().decode('utf-8');assert not text.startswith('\ufeff'),'Unexpected BOM'
  if row['content']!=text:changed.add(n)
  row['content']=text
 assert changed<=ALLOWED_SOURCE_CHANGES,('Unapproved source family',changed-ALLOWED_SOURCE_CHANGES)
 assert {n:actual[n]for n in changed}==f['normal_build']['approved_changed_source_sha256'],'Exact approved source changes differ'
 assert {n for n in actual if n.startswith('src/')}==set(f['source_sha256'])
 assert data['settings']==json.loads((BASE/'compiler-input.json').read_bytes())['settings']
 build={n:sha((R/n).read_bytes())for n in BUILD_INPUTS if(R/n).is_file()};assert len(build)==4
 assert actual=={n:sha(row['content'].encode('utf-8'))for n,row in data['sources'].items()}
 dest.mkdir(parents=True,exist_ok=False)
 payload=json.dumps(data,separators=(',',':'),ensure_ascii=True).encode();(dest/'compiler-input.json').write_bytes(payload)
 keep={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA'}
 env={k:v for k,v in os.environ.items()if k.upper()in keep};env['PATH']=str(SOLC.parent)+os.pathsep+'C:/Windows/System32'
 spec=importlib.util.spec_from_file_location('_final_six_normal_profile',R/'scripts/verify-normal-profile.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 save(dest/'EFFECTIVE_NORMAL_PROFILE.json',module.inspect_profile(str(FORGE),environment=env))
 start={'kind':'actual_closed_normal_build','candidate_build_id':BUILD_ID,'started_utc':datetime.now(timezone.utc).isoformat(),
  'command':[str(SOLC),'--standard-json'],'settings':data['settings'],'compiler_sha256':COMPILER,'source_freeze_sha256':sha(freeze_raw),
  'source_sha256':{n:h for n,h in actual.items()if n.startswith('src/')},'dependency_source_sha256':{n:h for n,h in actual.items()if not n.startswith('src/')},
  'compiler_content_sha256':actual,'build_input_sha256':build,'input_sha256':sha(payload),'actual_filesystem_matches_compiler_input':True,
  'unchanged_before_build':True,'source_adopted':True,'production_sources_written_by_this_compilation':False,'production_approved':False,
  'changed_from_activation_gas':sorted(changed),'codegen_and_output_settings_exactly_unchanged':True,
  'baseline_input_sha256':sha((BASE/'compiler-input.json').read_bytes()),'baseline_output_sha256':sha((BASE/'compiler-output.json').read_bytes()),
  'old_test_methods_executed':0,'phase':'compiled_awaiting_explicit_admission'}
 save(dest/'START.json',start);save(dest/'PREFLIGHT_RESULT.json',{'scope':'Source/build preflight, not a compilation pass','closed_sources':100,'project_sources':61,'not_a_build_pass':True})
 then=time.monotonic()
 with(dest/'compiler-input.json').open('rb')as inp,(dest/'compiler-output.json').open('xb')as out,(dest/'stderr.txt').open('xb')as err:
  proc=subprocess.Popen(start['command'],stdin=inp,stdout=out,stderr=err,cwd=dest,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));save(dest/'PID.json',{'owned_pid':proc.pid})
  try:rc=proc.wait(timeout=900)
  except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=15);raise RuntimeError('Owned normal compiler exceeded900seconds')
 save(dest/'COMPILER_EXIT.json',{'solc_exit_code':rc,'seconds':time.monotonic()-then,
  'compiler_output_sha256':sha((dest/'compiler-output.json').read_bytes()),
  'stderr_sha256':sha((dest/'stderr.txt').read_bytes())})
 raw=(dest/'compiler-output.json').read_bytes();compiled=json.loads(raw);errors=[x for x in compiled.get('errors',[])if x['severity']=='error']
 gates=[];abis=[];layouts=[];details={}
 if not errors:gates,abis,layouts,details=compare(data,old,compiled,prior)
 after={n:sha((R/n).read_bytes())for n in actual};build_after={n:sha((R/n).read_bytes())for n in build}
 sizepass=rc==0 and not errors and len(gates)==48 and all(g['runtime_ok']and g['creation_ok']for g in gates)
 result={**start,'completed_utc':datetime.now(timezone.utc).isoformat(),'solc_exit_code':rc,'exit_code':rc,'seconds':time.monotonic()-then,
  'errors':errors,'gates':gates,'all_pass':sizepass,'source_count':100,'compiled_source_count':len(compiled.get('sources',{})),
  'closed_input_inventory':set(compiled.get('sources',{}))==set(actual),'unexpected_implicit_sources':sorted(set(compiled.get('sources',{}))-set(actual)),
  'missing_compiled_sources':sorted(set(actual)-set(compiled.get('sources',{}))),'normal_limits':{'runtime_bytes':24576,'initcode_bytes':49152},
  'unchanged_during_build':actual==after and build==build_after,'actual_source_files_unchanged_during_build':actual==after,
  'build_inputs_unchanged_during_build':build==build_after,'source_sha256_after':after,'build_input_sha256_after':build_after,
  'solc_executable_sha256':sha(SOLC.read_bytes()),'solc_executable_unchanged':sha(SOLC.read_bytes())==COMPILER,
  'compiler_input_sha256':sha(payload),'compiler_output_sha256':sha(raw),
  'canonical_abi_types_identical':bool(abis)and all(x['canonical_signatures_tuple_types_mutability_identical']for x in abis),
  'abi_strictly_identical':bool(abis)and all(x['strictly_identical']for x in abis),
  'semantic_storage_differences':[x for x in layouts if not x['identical']],
  'abi_name_differences':[x for x in abis if x['parameter_output_name_or_internalType_changes']],
  'protected_four_unchanged':all(sha((R/n).read_bytes())==h for n,h in PROTECTED.items()),'pass':False,
  'admission_required':True,'not_trusted_until_admission':True}
 if not errors:
  code=bytes.fromhex(compiled['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object']);parts=[code[:24573],code[24573:]]
  carrier={'payload_length':len(code),'creation_code_hash':'0x'+keccak256(code).hex(),'parts':[{'index':i,'payload_bytes':len(x),'runtime_bytes':len(x)+3,'runtime_code_hash':'0x'+keccak256(b'\x5f\x5f\xfd'+x).hex(),'runtime_ok':len(x)+3<=24576}for i,x in enumerate(parts)],'source_adopted':True,'production_approved':False}
  carrier['all_pass']=len(code)+32<=49152 and len(code)<=2*24573 and all(x['runtime_ok']for x in carrier['parts']);save(dest/'ROYALTY_CARRIER_EVIDENCE.json',carrier);result['carrier_checks_pass']=carrier['all_pass']
 save(dest/'ABI_STORAGE_COMPARISON.json',{'abi':abis,'storage':layouts});save(dest/'PRIVATE_LAYOUT_DIFFS.json',details)
 save(dest/'COMPILED_RESULT.json',result);save(dest/'normal-size-evidence.json',result)
 print(json.dumps({'phase':result['phase'],'size_pass':sizepass,'canonical_abi_types_identical':result['canonical_abi_types_identical'],'private_layout_changes':len(result['semantic_storage_differences']),'abi_name_changes':len(result['abi_name_differences']),'trusted_pass':False,'next':'Review exact layout/name deltas, then rerun this stage with--admit; no recompile'},indent=2))
 return 0 if sizepass and result['closed_input_inventory']and result['unchanged_during_build']and result['canonical_abi_types_identical']else 1

def admit(dest):
 freeze_raw,f=freeze();result=json.loads((dest/'COMPILED_RESULT.json').read_bytes())
 assert result['phase']=='compiled_awaiting_explicit_admission'and not(result['pass'])
 assert result['source_freeze_sha256']==sha(freeze_raw)and result['candidate_build_id']==BUILD_ID
 assert result['compiler_input_sha256']==sha((dest/'compiler-input.json').read_bytes())
 assert result['compiler_output_sha256']==sha((dest/'compiler-output.json').read_bytes())
 assert result['source_sha256_after']=={n:sha((R/n).read_bytes())for n in result['compiler_content_sha256']}
 assert result['build_input_sha256_after']=={n:sha((R/n).read_bytes())for n in result['build_input_sha256']}
 data=json.loads((dest/'compiler-input.json').read_bytes());compiled=json.loads((dest/'compiler-output.json').read_bytes())
 old=json.loads((BASE/'compiler-output.json').read_bytes());prior=json.loads((BASE/'RESULT.json').read_bytes())
 assert data['settings']==json.loads((BASE/'compiler-input.json').read_bytes())['settings']
 assert {n:sha(row['content'].encode('utf-8'))for n,row in data['sources'].items()}==result['compiler_content_sha256']
 assert len(data['sources'])==len(compiled['sources'])==100 and set(data['sources'])==set(compiled['sources'])
 gates,abis,layouts,details=compare(data,old,compiled,prior)
 assert gates==result['gates'],'Cached size claims differ from actual outputs'
 assert [x for x in layouts if not x['identical']]==result['semantic_storage_differences'],'Cached private layout differences differ'
 assert [x for x in abis if x['parameter_output_name_or_internalType_changes']]==result['abi_name_differences'],'Cached public name changes differ'
 assert all(x['canonical_signatures_tuple_types_mutability_identical']for x in abis),'Actual public ABI types changed'
 required={x['identity']:{'baseline_semantic_sha256':x['baseline_semantic_sha256'],'final_semantic_sha256':x['final_semantic_sha256']}for x in result['semantic_storage_differences']}
 name_required={x['identity']:x['parameter_output_name_or_internalType_changes']for x in result['abi_name_differences']}
 acceptance_path=OWN/'LAYOUT_ACCEPTANCE.json';acceptance_raw=acceptance_path.read_bytes()if acceptance_path.exists()else None
 if required or name_required:
  assert acceptance_raw is not None,'Exact private layout/public name acceptance is required'
  acceptance=json.loads(acceptance_raw)
  assert acceptance['schema']==1 and acceptance['build_id']==BUILD_ID and acceptance['reviewed']is True
  assert acceptance['source_freeze_sha256']==sha(freeze_raw)
  assert acceptance['compiler_input_sha256']==result['compiler_input_sha256']and acceptance['compiler_output_sha256']==result['compiler_output_sha256']
  assert acceptance['accepted_semantic_storage_deltas']==required,'Unknown or excess accepted private layout'
  assert acceptance['accepted_abi_name_changes']==name_required,'Unknown or excess public name/internalType changes'
 result.update(phase='admitted_without_recompilation',admission_required=False,not_trusted_until_admission=False,
  abi_changes_as_expected=result['canonical_abi_types_identical'],storage_changes_as_expected=True,
  layout_acceptance_sha256=sha(acceptance_raw)if acceptance_raw else None,
  admission_utc=datetime.now(timezone.utc).isoformat(),additional_compiler_runs=0)
 result['pass']=all(result.get(k)for k in('all_pass','closed_input_inventory','unchanged_during_build','solc_executable_unchanged','abi_changes_as_expected','storage_changes_as_expected','protected_four_unchanged','carrier_checks_pass'))
 assert result['pass'],'Compilation does not meet all normal admission conditions'
 save(dest/'normal-size-evidence.json',result,new=False)
 snapshot=import_compiler(R,dest/'compiler-input.json',dest/'compiler-output.json',dest/'normal-size-evidence.json')
 admission={'strict_import_pass':True,'actual_build_not_preflight':True,'additional_compiler_runs':0,'source_objects':len(snapshot['abi_snapshot']),
  'closed_sources':len(snapshot['source_snapshot']['compiler_source_names']),'size_evidence_sha256':sha((dest/'normal-size-evidence.json').read_bytes()),'production_approved':False}
 save(dest/'ADMISSION_RESULT.json',admission);save(dest/'RESULT.json',result)
 PUB.mkdir(parents=True,exist_ok=False)
 names=['START.json','COMPILER_EXIT.json','COMPILED_RESULT.json','RESULT.json','normal-size-evidence.json','PREFLIGHT_RESULT.json','EFFECTIVE_NORMAL_PROFILE.json','ABI_STORAGE_COMPARISON.json','PRIVATE_LAYOUT_DIFFS.json','ROYALTY_CARRIER_EVIDENCE.json','ADMISSION_RESULT.json','stderr.txt']
 for name in('compiler-input.json','compiler-output.json'):
  (dest/(name+'.gz')).write_bytes(gzip.compress((dest/name).read_bytes(),mtime=0));names.append(name+'.gz')
 for name in names:(PUB/name).write_bytes((dest/name).read_bytes())
 if acceptance_raw:(PUB/'LAYOUT_ACCEPTANCE.json').write_bytes(acceptance_raw);names.append('LAYOUT_ACCEPTANCE.json')
 save(PUB/'ARTIFACTS.json',{'external_uncompressed_directory':str(dest),'files':{n:sha((PUB/n).read_bytes())for n in names},'historical_activation_gas_unchanged':True,'production_approved':False})
 print(json.dumps({'pass':True,'all48_size_pass':True,'additional_compiler_runs':0,'strict_import':admission},indent=2));return 0

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage');parser.add_argument('--admit',action='store_true');args=parser.parse_args()
 assert re.fullmatch(r'final[0-9]{2}',args.stage),'Use a new owned finalNN stage'
 dest=OWN/'build'/args.stage
 return admit(dest)if args.admit else compile_stage(dest)

if __name__=='__main__':raise SystemExit(main())
