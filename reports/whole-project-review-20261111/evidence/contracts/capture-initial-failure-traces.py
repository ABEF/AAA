from pathlib import Path
import hashlib,json,subprocess
B=Path(__file__).resolve().parent;V=B.parents[1];P=B/'focused-6cdccb71d2'
start=json.loads((P/'START.json').read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert start['sources']=={name:sha(P/name)for name in start['sources']}
command=[str(V/'foundry-v1.4.4/forge.exe'),'test','--root',str(P),'--use',str(V/'toolchain-0.8.26/solc.exe'),'--offline','--match-contract','ContributionEntryPriceSecurityTest|ContributionPriceSecurityTest','--match-test','testFundedClaimsRemainAvailableWhenPricingFails|testDirectPriceCaptureSurvives|testDirectWider|testDirectPool|testDirectOwner','-vvvv']
with(P/'original-seven-failure-traces.txt').open('xb')as out,(P/'original-seven-failure-traces.stderr.txt').open('xb')as err:
 result=subprocess.run(command,cwd=P,stdout=out,stderr=err,timeout=300)
trace=(P/'original-seven-failure-traces.txt').read_text()
assert result.returncode==1 and '7 failing tests' in trace
record={'exit_code':result.returncode,'command':command,'snapshot_still_exact':start['sources']=={name:sha(P/name)for name in start['sources']},'trace_sha256':sha(P/'original-seven-failure-traces.txt'),'scope':'Diagnostic execution of original immutable test snapshot only; retains seven original failures, not new accepted verification.'}
(P/'original-seven-failure-traces.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
