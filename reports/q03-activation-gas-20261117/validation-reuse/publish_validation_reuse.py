"""Publish the bounded actual stages; does not run or reclassify tests."""
from pathlib import Path
import gzip,hashlib,json,shutil,sys
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
S=V/'q03-activation-gas-20261117/validation-reuse';D=R/'reports/q03-activation-gas-20261117/validation-reuse'
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
normal=json.loads((S/'normal/compiler-input.json').read_bytes())['sources']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def body(text,name):
 start=text.index('function '+name+'(');opening=text.index('{',start);depth=0
 for i in range(opening,len(text)):
  if text[i]=='{':depth+=1
  if text[i]=='}':
   depth-=1
   if not depth:return text[start:i+1]
 raise ValueError(name)
nameprefix='test/Q03ValidationReuse20261117.t.sol:Q03ValidationReuse20261117Test.'
reused=['testQ03EntryFinalApprovalResetStillRejectsFreshSameValueRoundAndAllAccountingRollsBack','testQ03NonzeroPullStillRejectsSmallForeignMarketMutationAndRollsBack']
latest=['testQ03PrivateProofReuseAllowsBothActualSwapDirectionsAndPublicRefundProofs','testQ03RefundSourceDisableRestoreStillInvalidatesFinalProofAndEveryTransfer','testQ03StandaloneSwapStillRejectsPullRoundMutationThenProvesBothOwnTransitions']
records=[]
closures={}
for stage,names in [('boundary02',reused),('boundary03',latest)]:
 data=json.loads((S/stage/'EXECUTION.json').read_text());raw=json.loads((S/stage/'raw.json').read_bytes())
 assert sha(S/stage/'raw.json')==data['raw_sha256']
 selected={m['id']:m for m in data['methods']}
 art=json.loads((S/stage/'producer-artifact.json').read_bytes());methodids=art['methodIdentifiers']
 metadata=art['metadata'];compiled_sources={};source_rows={}
 for source,identity in metadata['sources'].items():
  if source=='test/Q03ValidationReuse20261117.t.sol':rawsource=(S/stage/'SOURCE_TEST.sol.txt').read_bytes()
  elif source in normal:rawsource=normal[source]['content'].encode()
  else:rawsource=(R/source).read_bytes()
  # Forge normalizes CRLF before passing source text to standard-json Solc.
  # Authenticate both actual filesystem bytes and the observed compiler text.
  digest=hashlib.sha256(rawsource).hexdigest();compilertext=rawsource.replace(b'\r\n',b'\n')
  keccak='0x'+keccak256(compilertext).hex()
  assert keccak==identity['keccak256'],source
  if source in data['source_before']:assert digest==data['source_before'][source],source
  compiled_sources[source]={'content':compilertext.decode()}
  source_rows[source]={'filesystem_sha256':digest,'compiler_text_sha256':hashlib.sha256(compilertext).hexdigest(),'compiler_keccak256':keccak,'filesystem_crlf_to_compiler_lf':rawsource!=compilertext}
 scope={'sources':compiled_sources,'compiler':metadata['compiler'],'settings':metadata['settings']}
 sourcepool=gzip.compress(json.dumps(scope,ensure_ascii=True,separators=(',',':')).encode(),mtime=0)
 stageout=D/stage;stageout.mkdir(parents=True,exist_ok=True)
 (stageout/'COMPILED_SOURCE_POOL.json.gz').write_bytes(sourcepool)
 closures[stage]={'source_count':len(source_rows),'sources':source_rows,'all_compiled_keccak_and_before_sha_match':True,'source_pool_sha256':sha(stageout/'COMPILED_SOURCE_POOL.json.gz'),'source_after_differences':[source for source in data['source_before']if data['source_before'][source]!=data['source_after'].get(source)]}
 for name in names:
  ident=nameprefix+name+'()';m=selected[ident];assert m['status']=='Success',m
  assert name+'()'in methodids
  earlier=(S/stage/'SOURCE_TEST.sol.txt').read_text();current=(R/'test/Q03ValidationReuse20261117.t.sol').read_text()
  a=body(earlier,name);b=body(current,name);assert a==b
  records.append({'id':ident,'stage':stage,'status':m['status'],'exact_method_text_unchanged':True,'method_text_sha256':hashlib.sha256(a.encode()).hexdigest(),'selector':methodids[name+'()'],'raw_sha256':data['raw_sha256'],'producer_artifact_sha256':data['artifact_sha256']})
 for path in ['src/ZZZLiquidityManager.sol','src/ZZZContributionPricing.sol']:
  assert data['source_before'][path]==sha(R/path),path
 for p in (S/stage).iterdir():
  if p.is_file():
   target=D/stage/p.name;target.parent.mkdir(parents=True,exist_ok=True)
   if p.suffix=='.json'and p.stat().st_size>500_000:target=target.with_suffix('.json.gz');target.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
   else:shutil.copy2(p,target)
for p in(S/'boundary01').iterdir():
 if p.is_file():target=D/'boundary01'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
result={'schema':1,'methods':records,'distinct_successful_new_methods':len(records),'unchanged_prior_suite_methods_rerun':0,
 'compiled_closures':closures,
 'stages':{stage:{k:json.loads((S/stage/'EXECUTION.json').read_text()).get(k)for k in ['exit_code','elapsed_seconds','source_bracket_stable']}for stage in ['boundary01','boundary02','boundary03']},
 'stage_limits':['boundary01 parser failure in unrelated in-progress experimental fixture:0methods.','boundary02:2passes+2fixturefailures; first2successful method texts reused exactly, not rerun.','boundary03:only2corrected fixtures+1newstandalonecaller selected; actual source before/after differences retained.','Results are exact recorded compiler source stages, not proof all future source changes preserve behavior.'],
 'compiler_scope':'Normal100source/48gates from approved two-source stage; later Royalty source port requires independent normal admission.',
 'gas_qualification':False,'production_approved':False}
assert len(records)==5
(D/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
for name in ['run_validation_boundary.py','prove_validation_reuse.py','compile_validation_reuse.py','publish_validation_reuse.py']:shutil.copy2(V/'q03-activation-gas-20261117'/name,D/name)
print(json.dumps({'distinct_new_successful_methods':len(records),'stages':result['stages']}))
