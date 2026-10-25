from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=Path(__file__).parent;B=E/'solidity';X=E.parent
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((B/'selected/focused-transformation.json').read_text());profile=Path(manifest['profile']).resolve()
assert profile.is_relative_to((B/'selected').resolve())
path='test/GlobalMembershipDust.t.sol';before=(R/path).read_bytes()
assert (profile/path).read_bytes()==before
old=b'vm.expectRevert(failure);pools.accounting(poolId);'
new=b'''(bool ok,bytes memory returned)=address(pools).staticcall(
            abi.encodeWithSignature("accounting(bytes32)",poolId));
        assertFalse(ok);assertEq(returned,failure);'''
assert before.count(old)==1;after=before.replace(old,new)
assert before==after.replace(new,old)
(B/'selected/global-before-control-repair.sol.txt').write_bytes(before)
(R/path).write_bytes(after);(profile/path).write_bytes(after)
sizes=json.loads((B/'source-size-gates.json').read_text())
for n,h in sizes['source_sha256'].items():assert sha((R/n).read_bytes())==h,n
record={'scope':'Repair only the failure-injection assertion: inspect exact low-level staticcall success/revert bytes rather than Foundry expectRevert on its same-depth mocked call. Financial assertions and production unchanged.','file':path,'before_sha256':sha(before),'after_sha256':sha(after),'exact_single_control_replacement':True,'profile':str(profile),'production_source_sha256':sizes['source_sha256']}
(B/'selected/control-repair.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
methods={'testBrokenHistoricalVenueStillSettlesFundedDustOnlyToIncumbents','testBrokenHistoricalVenueWithNoDustDoesNotBlockHealthyNewEntry','testHistoricalDustPaymentFailureRejectsEntryWithoutLosingOldRights'}
env=os.environ.copy();env['RAYON_NUM_THREADS']='2'
command=[str(X/'foundry-v1.4.4/forge.exe'),'test','--root',str(profile),'--use',str(X/'toolchain-0.8.26/solc.exe'),'--match-contract','^GlobalMembershipDustTest$','--match-test','('+'|'.join(sorted(methods))+')','--json']
start=time.monotonic();p=subprocess.run(command,capture_output=True,env=env,timeout=1200)
(B/'selected/control-repair-results.json').write_bytes(p.stdout);(B/'selected/control-repair-stderr.log').write_bytes(p.stderr)
d=json.loads(p.stdout);cases=[{'suite':s,'method':n,'status':v.get('status'),'reason':v.get('reason'),'kind':v.get('kind')} for s,c in d.items() for n,v in c.get('test_results',{}).items()]
actual={v['method'].split('(')[0] for v in cases};complete=actual==methods and len(cases)==3
result={'command':command,'elapsed_seconds':round(time.monotonic()-start,3),'exit_code':p.returncode,'cases':cases,'complete':complete,'successful':complete and p.returncode==0 and all(v['status']=='Success' for v in cases),'repair_manifest_sha256':sha((B/'selected/control-repair.json').read_bytes())}
(B/'selected/control-repair-summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:result[k] for k in ('exit_code','elapsed_seconds','complete','successful')}))
raise SystemExit(0 if result['successful'] else 1)
