from pathlib import Path
import hashlib,json,re,sys
r=Path.cwd();e=Path(__file__).parent;sys.path.insert(0,str(r))
from zzz_ops.abi import keccak256
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
stage=e/'evm-optimized';result=json.loads((stage/'status.json').read_text())
budget=json.loads((e/'evm-differential-budget/status.json').read_text());assert budget['successful'] and len(budget['methods'])==1
passed={k:v for k,v in result['methods'].items() if v['status']=='Success'}
assert len(passed)==15 and result['source_after']==budget['source_after'] and result['test_after']==budget['test_after'] and result['closed_after']==budget['closed_after']
final_methods=passed|budget['methods'];assert len(final_methods)==16 and all(x['status']=='Success' for x in final_methods.values())
lib='src/libraries/ExactLPAllocation.sol';test='test/ExactLPAllocation.t.sol';helper='test/helpers/ExactLPAllocationBaseline.sol'
def body(s,name):
 at=s.index('{',s.index('contract '+name));end=at+1;depth=1
 while depth:
  if s[end]=='{':depth+=1
  elif s[end]=='}':depth-=1
  end+=1
 return s[at:end]
def functions(s):
 out={}
 for m in re.finditer(r'\bfunction\s+(\w+)\s*\([^)]*\)[^{;]*\{',s):
  at=m.end();depth=1
  while depth:
   if s[at]=='{':depth+=1
   elif s[at]=='}':depth-=1
   at+=1
  out[m.group(1)]=s[m.start():at]
 return out
old=(e/'test-baseline15.sol').read_text();now=(r/test).read_text();of=functions(body(old,'ExactLPAllocationTest'));nf=functions(body(now,'ExactLPAllocationTest'))
assert all(nf[n]==value for n,value in of.items());assert body(old,'ExactLPAllocationHarness')==body(now,'ExactLPAllocationHarness')
expected=(e/'library-baseline.sol').read_text().replace('library ExactLPAllocation {','library ExactLPAllocationBaseline {',1).replace('pragma solidity 0.8.26;','pragma solidity 0.8.26;\n// TEST ONLY: frozen pre-optimization engine, intentionally not current production code.',1)
assert (r/helper).read_text()==expected
initial=json.loads((e/'evm-initial/status.json').read_text())
assert all(sha(r/k)==h for k,h in initial['source_before'].items() if k!=lib)
assert all(sha(r/k)==h for k,h in initial['test_before'].items() if k!=test)
protected={'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
assert all(sha(r/k)==h for k,h in protected.items())
proof={'original_harness_body_preserved':True,'all_baseline15_test_and_helper_bodies_preserved':True,
 'old_method_helper_normalized_sha256':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in of.items()},
 'only_added_test_helpers':sorted(set(nf)-set(of)),'test_only_baseline_copy_exact_after_name_comment_substitution':True,
 'baseline_library_sha256':sha(e/'library-baseline.sol'),'test_only_baseline_helper_sha256':sha(r/helper),
 'prior84_source_files_unchanged':True,'all_preexisting_test_files_unchanged':True,'protected4_sha256':protected}
(e/'SOURCE_TEST_PRESERVATION.json').write_text(json.dumps(proof,indent=2)+'\n')
data=json.loads((stage/'stdout.json').read_text());topic='0x'+keccak256(b'ColdEngineGas(uint256,uint256,uint256,uint256,uint256)').hex();events=[]
for suite,b in data.items():
 if isinstance(b,dict):
  for method,item in b.get('test_results',{}).items():
   for x in item.get('logs',[]):
    if x.get('topics') and x['topics'][0]==topic:events.append({'method':method,'raw':x['data'],'values':[int(x['data'][2:][i:i+64],16) for i in range(0,len(x['data'])-2,64)]})
assert len(events)==1
baseline=json.loads((e/'COLD_GAS_INITIAL.json').read_text())[0]['values'];optimized=events[0]['values'];assert baseline[0]==optimized[0]==1000
names=['root_credit','one_book_take','two_book_weight_change','batch32_engine_entries']
gas={name:{'baseline_raw':a,'optimized_raw':b,'raw_saved':a-b,'percent_raw_saved':(a-b)*100/a} for name,a,b in zip(names,baseline[1:],optimized[1:])}
measurement={'baseline_event':'COLD_GAS_INITIAL.json','optimized_event':events,'comparison':gas,
 'cooling':'vm.cool(h) marks account and ALL storage slots cold before each measurement.',
 'scope':'RAW external harness call plus internal engine. Refunds/intrinsic gas/real host ownership,funding,second reward component,token transfers and ClaimRouter are excluded. Batch32=16ordinals*2logical books, not32full holder claims. Not target-chain/economic/12Mqualification.'}
(e/'COLD_GAS_COMPARISON.json').write_text(json.dumps(measurement,indent=2)+'\n')
(e/'library-final.sol').write_bytes((r/lib).read_bytes());(e/'test-final16.sol').write_bytes((r/test).read_bytes())
fuzz={k:v['kind']['Fuzz']['runs'] for k,v in final_methods.items() if isinstance(v.get('kind'),dict) and 'Fuzz' in v['kind']};assert len(fuzz)==2 and set(fuzz.values())=={1000}
record={'scope':'Standalone INTERNAL exact-unit LP engine milestone; current Rewards/Vault/canonical/profile6 NOT integrated.',
 'library_sha256':sha(r/lib),'test_sha256':sha(r/test),'baseline_helper_sha256':sha(r/helper),
 'current_source85':result['source_after'],'closed_test_source25':result['closed_after'],
 'final_distinct_successful_methods':16,'fuzz_properties_and_runs':fuzz,'methods':final_methods,
 'final_evm_stages':{'evm-optimized':{'success':15,'failure':1,'default_test_gas_limit':1073741824},'evm-differential-budget':{'success':1,'selected_only':True,'explicit_test_gas_limit':10000000000}},
 'final_evm_status':['evm-optimized/status.json','evm-differential-budget/status.json'],'retained_preoptimization15':'BASELINE15_REVIEW.json',
 'counts_not_summed':'Baseline15 overlaps final16. Report16current methods, not31; each fuzz property1000inputs, not additional named methods.',
 'evm_failures_retained':1,'failure_explanation':'Complete-state scanner Revert at1073667604gas near default1073741824test envelope. The same source/config/tools pass selected-only with10bTESTenvelope; no assertion, source or operating-budget change. Scanner repeatedly visits2047nodes and is not anO10engine operation. Passed15methods notrerun.',
 'retained_parser_failure':'abi-initial/status.json: test-only reserved identifier after, renamed before EVM; no library correction.',
 'gas_comparison':'COLD_GAS_COMPARISON.json','source_test_preservation':'SOURCE_TEST_PRESERVATION.json',
 'full_state_differential':'Frozen original afd5 engine versus optimized346a engine; checks both outstanding and ALL2047nodes weights/pending/high/low after every selected operation and preview. Not only final balances.',
 'functional_scope':['whole final unit both books','full-width split and safe carry','fixed-weight batching/claim order','independent eager mixed sequence','both old-asset paths before activation/growth','no-op state preservation','growth starvation phase improvement','integer-boundary unit-delay limitation','zero-weight old rights and phase','MAXoutstanding repeated lifetimes','overflow/invalid rollback','1000ordinals/no padding','actual512bit nonzero-low rebase'],
 'current_behavior_changed':False,'new_internal_component_only':True,
 'remaining':['Real Rewards/Vault/Membership share synchronization','liabilities,funding,owner checks,conversions and separate compound/buyback/royalty barriers','fresh accounting/canonical/consumer identities and import/export','full-host runtime/initcode/static/gas integration','target-chain qualifications and independent audit'],
 'normal_final_basis':json.loads((stage/'START.json').read_text())['normal_source_basis']}
(e/'FINAL_TEST_REVIEW.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'final_methods':16,'fuzz_runs':fuzz,'library_sha256':record['library_sha256'],'test_sha256':record['test_sha256'],'gas':gas,'record':str(e/'FINAL_TEST_REVIEW.json')},indent=2))
