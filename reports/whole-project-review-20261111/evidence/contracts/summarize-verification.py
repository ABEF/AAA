"""Count unique accepted methods and prove exact source-closure reuse, retaining failures."""
from pathlib import Path
import hashlib,json,posixpath,re,sys
R=Path.cwd();B=Path(__file__).resolve().parent;INITIAL=B/'focused-6cdccb71d2';FINAL=Path(sys.argv[1])
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
initial=load(INITIAL/'SELECTED_VERIFICATION.json');final=load(FINAL/'VERIFICATION.json')
assert final['exit_code']==0 and final['source_unchanged']and final['snapshot_exact']
keep={'NativeCanonicalFundingTest','NativeMigrationBudgetTest','GlobalMembershipDustTest','NFTMetadataTest'}
reused=[c for c in initial['tests']if c['suite'].split(':')[-1]in keep]
assert len(reused)==22 and all(c['status']=='Success'for c in reused)
remaps={'@openzeppelin/contracts/':'node_modules/@openzeppelin/contracts/','@uniswap/v4-core/':'node_modules/@uniswap/v4-core/','@uniswap/v4-periphery/':'node_modules/@uniswap/v4-periphery/','v4-core/':'node_modules/@uniswap/v4-core/','permit2/':'node_modules/@uniswap/v4-periphery/lib/permit2/','solmate/':'node_modules/@uniswap/v4-core/lib/solmate/','forge-std/':'lib/forge-std/src/'}
pattern=re.compile(r'''\bimport\s+(?:\{[^}]*\}\s*from\s*|(?:\*\s*as\s+\w+|\w+)\s*from\s*)?["']([^"']+)["']\s*;''',re.S)
def closure(name,seen):
 if name in seen:return
 seen.add(name)
 for imported in pattern.findall((R/name).read_text(encoding='utf-8-sig')):
  if imported.startswith('.'):child=posixpath.normpath(posixpath.join(posixpath.dirname(name),imported))
  else:
   prefix=next(p for p in sorted(remaps,key=len,reverse=True)if imported.startswith(p));child=remaps[prefix]+imported[len(prefix):]
  closure(child,seen)
bindings=[]
for name in sorted({c['suite'].split(':')[0]for c in reused}):
 files=set();closure(name,files)
 hashes={f:sha(R/f)for f in sorted(files)}
 assert all(initial['sources'].get(f)==h for f,h in hashes.items())
 bindings.append({'test_source':name,'exact_current_import_closure_sha256':hashes,'reused_source_closure_identical':True})
assert len(final['tests'])==30 and all(c['status']=='Success'for c in final['tests'])
keys=[(c['suite'],c['test'])for c in reused+final['tests']];assert len(keys)==len(set(keys))==52
normal=B/'normal-final-ea7e55d22b';normalg=load(normal/'production-size-gates.json')
assert normalg['all_pass']and all(sha(R/name)==digest for name,digest in normalg['source_sha256'].items())
result={'unique_accepted_EVM_methods':52,'fresh_affected_after_fixture_fixes':30,'unchanged_exact_source_closure_reuse':22,
 'normal_compile':str(normal),'normal_size_gates':len(normalg['gates']),'all_normal_source_bindings_current':True,
 'normal_comparison':str(B/'normal-comparison-final.json'),'initial38':str(INITIAL/'SELECTED_VERIFICATION.json'),
 'final30':str(FINAL/'VERIFICATION.json'),'original7failures_and_traces_retained':str(INITIAL/'original-seven-failure-traces.json'),
 'original_schema_failure':str(B/'focused-fb8c0ee384/VERIFICATION.json'),'reused_test_closures':bindings,
 'accepted_methods':reused+final['tests'],'scope':'Synthetic/component EVM evidence and closed normal compile. No live market, target-chain gas, provider, operating, public wallet or deployment qualification.'}
(B/'VERIFICATION-SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k]for k in('unique_accepted_EVM_methods','fresh_affected_after_fixture_fixes','unchanged_exact_source_closure_reuse','normal_size_gates','all_normal_source_bindings_current')}))
