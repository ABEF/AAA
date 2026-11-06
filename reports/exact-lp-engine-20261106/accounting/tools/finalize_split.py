from pathlib import Path
import hashlib,json,re
r=Path.cwd();e=Path(__file__).parent;p='test/ExactLPAllocation.t.sol'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
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
def norm(s):return re.sub(r'\s+',' ',s).strip()
def inner(s):return s[s.index('{')+1:-1]
old=(e/'test-combined16-before-split.sol').read_text();new=(r/p).read_text()
of=functions(body(old,'ExactLPAllocationTest'));nf=functions(body(new,'ExactLPAllocationTest'))
combined='testExactLPOptimizedMatchesFrozenBaselineCompleteStorageAfterEveryAction'
ordinary='testExactLPOptimizedMatchesFrozenBaselineOrdinaryLifecycleCompleteStorage'
wide='testExactLPOptimizedMatchesFrozenBaselineFullWidthCompleteStorage'
assert set(of)-set(nf)=={combined} and set(nf)-set(of)=={ordinary,wide}
assert all(nf[n]==v for n,v in of.items() if n!=combined)
for name in ('ExactLPAllocationHarness','ExactLPBaselineHarness'):assert body(old,name)==body(new,name)
before,after=inner(of[combined]).split('// A second fresh pair covers',1)
assert norm(inner(nf[ordinary]))==norm(before)
expected='// A second fresh pair covers'+after
expected=expected.replace('baseline=new ExactLPBaselineHarness();','ExactLPBaselineHarness baseline=new ExactLPBaselineHarness();',1)
assert norm(inner(nf[wide]))==norm(expected)
prior=json.loads((e/'evm-optimized/status.json').read_text());split=json.loads((e/'evm-split-default/status.json').read_text());assert split['successful']
passed={k:v for k,v in prior['methods'].items() if v['status']=='Success'};assert len(passed)==15 and len(split['methods'])==2
deps={k:h for k,h in prior['closed_after'].items() if k!=p}
assert all(split['closed_after'].get(k)==h==sha(r/k) for k,h in deps.items())
assert prior['source_after']==split['source_after'] and all(sha(r/k)==h for k,h in split['source_after'].items())
start=json.loads((e/'evm-split-default/START.json').read_text());assert '--gas-limit' not in start['command']
assert prior['config_unchanged'] and split['config_unchanged'] and prior['toolchain_unchanged'] and split['toolchain_unchanged']
proof={'scope':'Current17methods: exact15unchanged-success dependency reuse plus2new split default-budget passes.',
 'old_combined_source_sha256':sha(e/'test-combined16-before-split.sol'),'final17_source_sha256':sha(r/p),
 'reused15_test_bodies_setup_and_all_existing_helpers_unchanged':True,
 'common_function_sha256_normalized_lf':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in of.items() if n!=combined},
 'optimized_harness_entire_body_unchanged':True,'frozen_baseline_harness_entire_body_unchanged':True,
 'both_split_bodies_preserve_exact_original_action_assertion_sequences':True,
 'only_second_sequence_change':'Declare baseline local in the second standalone method; original second fresh-pair construction retained.',
 'all24_other_compiler_dependencies_unchanged':deps,'all85_current_sources_frozen':True,
 'removed_combined_method':combined,'new_default_methods':[ordinary,wide],
 'default_gas_limit':1073741824,'gas_override_present':False,
 'default_split_actual_gas':{k:v['kind']['Unit']['gas'] for k,v in split['methods'].items()}}
assert all(g<1073741824 for g in proof['default_split_actual_gas'].values())
(e/'DEFAULT_SPLIT_REUSE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n')
(e/'test-final17.sol').write_bytes((r/p).read_bytes())
record=json.loads((e/'FINAL_TEST_REVIEW.combined16.json').read_text());record['historical_combined16_record']='FINAL_TEST_REVIEW.combined16.json'
record['test_sha256']=sha(r/p);record['closed_test_source25']=split['closed_after']
record['final_distinct_successful_methods']=17;record['methods']=passed|split['methods']
record['final_current_stages']={'reused15unchanged':{'status':'evm-optimized/status.json','success':15,'default_gas_limit':1073741824,'proof':'DEFAULT_SPLIT_REUSE_PROOF.json'},
 'split2default':{'status':'evm-split-default/status.json','success':2,'default_gas_limit':1073741824,'gas_override':False}}
record['historical_combined_stages']=record.pop('final_evm_stages',{})
record['final_evm_status']=['evm-optimized/status.json','evm-split-default/status.json']
record['default_ci_test_compatibility']='Both full-state scanners now pass separately below default2^30 gas. No foundry.toml or production/operating budget change. Entire repository suite/CI not rerun.'
record['failure_explanation']='Historical combined scanner exceeded default2^30 test envelope and passed diagnostic10b. It was then split at its existing second fresh-pair boundary so BOTH current scanner methods pass the DEFAULT limit; all actions/assertions retained. Combined failure/diagnostic source stages are historical, not current default acceptance.'
record['counts_not_summed']='Current17distinct methods=15unchanged exact-source successes+2default split successes. Old combined16, diagnostic1, baseline15 overlap and are not added. Two preserved fuzzproperties each1000inputs.'
record['full_state_differential']='Current ordinary/fullwidth split tests compare ALL2047node weights/pending/high/low and both outstanding books after every action/preview; exact original sequences retained.'
record['default_split_reuse_proof']='DEFAULT_SPLIT_REUSE_PROOF.json';record['source_test_preservation_original']='SOURCE_TEST_PRESERVATION.json';record['source_test_preservation']='DEFAULT_SPLIT_REUSE_PROOF.json'
(e/'FINAL_TEST_REVIEW.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'current_methods':17,'default_actual_gas':proof['default_split_actual_gas'],'final_test_sha256':sha(r/p),'reused15_dependencies_unchanged':True,'library_sha256':sha(r/'src/libraries/ExactLPAllocation.sol'),'record':str(e/'FINAL_TEST_REVIEW.json')},indent=2))
