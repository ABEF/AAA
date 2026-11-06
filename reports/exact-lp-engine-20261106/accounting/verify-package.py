from pathlib import Path
import gzip,hashlib,json,re

root=Path(__file__).parent
def digest(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((root/'COPY_MANIFEST_ACCOUNTING.json').read_text())
for item in manifest['files']:
 p=(root/item['copy_relative']).resolve();assert p.is_relative_to(root.resolve())
 data=p.read_bytes();assert digest(data)==item['copy_sha256']
 raw=gzip.decompress(data) if item['transform']=='gzip_mtime0' else data
 assert digest(raw)==item['original_sha256'] and len(raw)==item['original_bytes']
def load(n):return json.loads((root/n).read_text())
prior=load('evm-optimized/status.json');split=load('evm-split-default/status.json');current=load('FINAL_TEST_REVIEW.json')
assert split['successful'] and len(split['methods'])==2
passed={k:v for k,v in prior['methods'].items() if v['status']=='Success'};assert len(passed)==15
assert current['methods']==passed|split['methods'] and current['final_distinct_successful_methods']==17
for stage in ('evm-optimized','evm-split-default'):
 start=load(stage+'/START.json');assert '--gas-limit' not in start['command']
 assert start['config_sha256']==load('evm-split-default/START.json')['config_sha256']
 status=load(stage+'/status.json');assert status['source_unchanged'] and status['tests_unchanged'] and status['closed_unchanged'] and status['config_unchanged'] and status['toolchain_unchanged']
 raw=json.loads(gzip.decompress((root/stage/'stdout.json.gz').read_bytes()))
 observed={suite+'::'+name:{'status':row['status'],'reason':row.get('reason'),'kind':row.get('kind'),'counterexample':row.get('counterexample')} for suite,b in raw.items() if isinstance(b,dict) for name,row in b.get('test_results',{}).items()}
 assert observed==status['methods']
assert all(v['kind']['Unit']['gas']<1073741824 for v in split['methods'].values())
proof=load('DEFAULT_SPLIT_REUSE_PROOF.json')
old=(root/'sources/test-combined16-before-split.sol').read_text();new=(root/'sources/test-final17.sol').read_text()
assert digest((root/'sources/test-final17.sol').read_bytes())==current['test_sha256']==proof['final17_source_sha256']
assert digest((root/'sources/library-final.sol').read_bytes())==current['library_sha256']
def body(s,name):
 at=s.index('{',s.index('contract '+name));end=at+1;level=1
 while level:
  if s[end]=='{':level+=1
  elif s[end]=='}':level-=1
  end+=1
 return s[at:end]
def functions(s):
 result={}
 for m in re.finditer(r'\bfunction\s+(\w+)\s*\([^)]*\)[^{;]*\{',s):
  end=m.end();level=1
  while level:
   if s[end]=='{':level+=1
   elif s[end]=='}':level-=1
   end+=1
  result[m.group(1)]=s[m.start():end]
 return result
of=functions(body(old,'ExactLPAllocationTest'));nf=functions(body(new,'ExactLPAllocationTest'))
removed=proof['removed_combined_method'];added=proof['new_default_methods']
assert set(of)-set(nf)=={removed} and set(nf)-set(of)==set(added)
assert all(nf[n]==value for n,value in of.items() if n!=removed)
for name in ('ExactLPAllocationHarness','ExactLPBaselineHarness'):assert body(old,name)==body(new,name)
def norm(s):return re.sub(r'\s+',' ',s).strip()
def inside(s):return s[s.index('{')+1:-1]
left,right=inside(of[removed]).split('// A second fresh pair covers',1)
assert norm(inside(nf[added[0]]))==norm(left)
right=('// A second fresh pair covers'+right).replace('baseline=new ExactLPBaselineHarness();','ExactLPBaselineHarness baseline=new ExactLPBaselineHarness();',1)
assert norm(inside(nf[added[1]]))==norm(right)
assert prior['source_after']==split['source_after']
assert all(prior['closed_after'][k]==h==split['closed_after'][k] for k,h in proof['all24_other_compiler_dependencies_unchanged'].items())
compiler=json.loads(gzip.decompress((root/'abi-optimized/input.json.gz').read_bytes()))
for k,h in proof['all24_other_compiler_dependencies_unchanged'].items():
 text=compiler['sources'][k]['content'];options=(text.encode(),text.replace('\n','\r\n').encode())
 assert h in {digest(x) for b in options for x in (b,b'\xef\xbb\xbf'+b)},k
fuzz=[x['kind']['Fuzz']['runs'] for x in passed.values() if 'Fuzz' in x.get('kind',{})];assert sorted(fuzz)==[1000,1000]
print(json.dumps({'package_verified':True,'copied_entries':len(manifest['files']),'current_distinct_methods':17,'reused_unchanged_successes':15,'new_default_split_passes':2,'default_gas_limit':1073741824,'source_closure_proof':True,'fuzz_runs_each':fuzz,'scope':'Recorded isolated evidence only; no builds/EVM/tests/services/signing executed by this verifier.'},indent=2))
