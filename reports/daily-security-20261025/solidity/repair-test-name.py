from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=Path(__file__).parent;B=E/'solidity';X=E.parent
def sha(b):return hashlib.sha256(b).hexdigest()
summary=json.loads((B/'selected/focused-summary.json').read_text())
manifest=json.loads((B/'selected/focused-transformation.json').read_text())
profile=Path(manifest['profile']).resolve()
assert profile.is_relative_to((B/'selected').resolve())
name='test/GlobalMembershipDust.t.sol';root_file=R/name;test_file=profile/name
before=root_file.read_bytes()
assert sha(before)==manifest['sources'][name]['original_sha256']
assert test_file.read_bytes()==before,'All GlobalMembershipDust methods were selected; no file transformation expected'
old=b'testFailedHistoricalDustPaymentStillRejectsEntryWithoutLosingOldRights'
new=b'testHistoricalDustPaymentFailureRejectsEntryWithoutLosingOldRights'
assert before.count(old)==1
after=before.replace(old,new)
assert before==after.replace(new,old)
(B/'selected/global-before-name-repair.sol.txt').write_bytes(before)
root_file.write_bytes(after);test_file.write_bytes(after)
sizes=json.loads((B/'source-size-gates.json').read_text())
for path,h in sizes['source_sha256'].items():assert sha((R/path).read_bytes())==h,path
record={'scope':'Repair only a test function identifier reserved by Foundry; production and assertions/helpers unchanged.','file':name,'before_sha256':sha(before),'after_sha256':sha(after),'old_identifier':old.decode(),'new_identifier':new.decode(),'exact_single_identifier_replacement':True,'profile':str(profile),'production_source_sha256':sizes['source_sha256']}
(B/'selected/test-name-repair.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
env=os.environ.copy();env['RAYON_NUM_THREADS']='2'
command=[str(X/'foundry-v1.4.4/forge.exe'),'test','--root',str(profile),'--use',str(X/'toolchain-0.8.26/solc.exe'),'--match-contract','^GlobalMembershipDustTest$','--json']
start=time.monotonic();result=subprocess.run(command,capture_output=True,env=env,timeout=1200)
(B/'selected/dust-repair-results.json').write_bytes(result.stdout);(B/'selected/dust-repair-stderr.log').write_bytes(result.stderr)
data=json.loads(result.stdout);cases=[{'suite':suite,'method':m,'status':v.get('status'),'reason':v.get('reason'),'kind':v.get('kind')} for suite,d in data.items() for m,v in d.get('test_results',{}).items()]
expected={m if m!=old.decode() else new.decode() for m in manifest['selection']['GlobalMembershipDustTest']['methods']}
actual={v['method'].split('(')[0] for v in cases}
final={'elapsed_seconds':round(time.monotonic()-start,3),'command':command,'exit_code':result.returncode,'expected':sorted(expected),'cases':cases,'complete':expected==actual and len(cases)==8,'successful':result.returncode==0 and expected==actual and len(cases)==8 and all(v['status']=='Success' for v in cases),'repair_manifest_sha256':sha((B/'selected/test-name-repair.json').read_bytes())}
(B/'selected/dust-repair-summary.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:final[k] for k in ('exit_code','elapsed_seconds','complete','successful')}))
raise SystemExit(0 if final['successful'] else 1)
