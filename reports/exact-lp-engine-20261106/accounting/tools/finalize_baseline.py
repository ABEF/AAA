from pathlib import Path
import hashlib,json,re
r=Path.cwd();e=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lib=r/'src/libraries/ExactLPAllocation.sol';test=r/'test/ExactLPAllocation.t.sol'
initial=json.loads((e/'evm-initial/status.json').read_text());wide=json.loads((e/'evm-wide-rebase/status.json').read_text())
assert initial['successful'] and wide['successful'] and len(initial['methods'])==14 and len(wide['methods'])==1
def functions(s):
 d={}
 for m in re.finditer(r'\bfunction\s+(\w+)\s*\([^)]*\)[^{;]*\{',s):
  at=m.end();depth=1
  while depth:
   if s[at]=='{':depth+=1
   elif s[at]=='}':depth-=1
   at+=1
  d[m.group(1)]=s[m.start():at]
 return d
old=functions((e/'test-initial14.sol').read_text());new=functions(test.read_text())
assert all(new[n]==s for n,s in old.items());assert set(new)-set(old)=={'testExactLPWideRebasePreservesBothBookRightsAndHighPhase'}
(e/'library-baseline.sol').write_bytes(lib.read_bytes());(e/'test-baseline15.sol').write_bytes(test.read_bytes())
data={'scope':'UNINTEGRATED internal engine baseline before selected-path optimization','library_sha256':sha(lib),'test15_sha256':sha(test),
 'distinct_successful_methods':15,'stages':{'initial14':str(e/'evm-initial/status.json'),'wide_only1':str(e/'evm-wide-rebase/status.json')},
 'all14method_and_helper_bodies_preserved_for15th_addition':True,'initial14_body_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in old.items()},
 'gas_samples':json.loads((e/'COLD_GAS_INITIAL.json').read_text()),'positive_pending_both_books':True,'cool_account_and_all_slots':True,
 'gas_scope':'RAW external harness+internal engine only. No refunds/intrinsic/host/owner/funding/token/router/second-component qualification.',
 'fuzz_properties':2,'fuzz_runs_each':1000,'evm_failures':0,'retained_abi_parser_failure':'abi-initial/status.json',
 'source85':wide['source_after'],'tests_after':wide['test_after'],'closed24':wide['closed_after']}
(e/'BASELINE15_REVIEW.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'baseline15_preserved':True,'library_sha256':sha(lib),'test_sha256':sha(test),'record':str(e/'BASELINE15_REVIEW.json')},indent=2))
