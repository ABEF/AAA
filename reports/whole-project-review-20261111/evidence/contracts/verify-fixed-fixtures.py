"""Recheck only the test contracts affected by two justified native-fixture fixes."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,uuid
R=Path.cwd();B=Path(__file__).resolve().parent;V=B.parents[1];OLD=B/'focused-6cdccb71d2'
P=B/('focused-final-'+uuid.uuid4().hex[:10]);P.mkdir()
for name in ('src','test','node_modules','lib','empty','out','cache'):
 if(OLD/name).is_dir():shutil.copytree(OLD/name,P/name)
shutil.copy2(OLD/'foundry.toml',P/'foundry.toml')
changed=['test/AtomicActivationIntegration.t.sol','test/ContributionPriceSecurity.t.sol','test/EntryReviewPolicy.t.sol']
for name in changed:shutil.copy2(R/name,P/name)
original=json.loads((OLD/'START.json').read_bytes())
watched=sorted(set(original['sources'])|set(changed))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
before={name:sha(R/name)for name in watched}
assert before=={name:sha(P/name)for name in watched}
for name in original['sources']:
 if name.startswith('src/'):assert before[name]==original['sources'][name]
command=[str(V/'foundry-v1.4.4/forge.exe'),'test','--root',str(P),'--use',str(V/'toolchain-0.8.26/solc.exe'),'--offline','--match-contract','^(ContributionEntryPriceSecurityTest|ContributionPriceSecurityTest|AtomicActivationIntegrationTest|EntryReviewPolicyTest)$','--json']
(P/'START.json').write_text(json.dumps({'command':command,'sources':before,'scope':'Native ledger fixture and funded-claim test correction; actual production source unchanged from closed normal compiler; no RPC/deployment/signing/Anvil'},indent=2)+'\n')
env=os.environ.copy();env['RAYON_NUM_THREADS']='2';start=time.monotonic()
with(P/'forge.json').open('xb')as out,(P/'forge.stderr.log').open('xb')as err:
 proc=subprocess.run(command,cwd=P,env=env,stdout=out,stderr=err,timeout=1200)
output=json.loads((P/'forge.json').read_bytes())
cases=[{'suite':suite,'test':name,'status':value.get('status'),'reason':value.get('reason'),'kind':value.get('kind')}for suite,body in output.items()for name,value in body.get('test_results',{}).items()]
after={name:sha(R/name)for name in watched}
report={'exit_code':proc.returncode,'seconds':round(time.monotonic()-start,2),'tests':cases,'source_unchanged':before==after,'snapshot_exact':before=={name:sha(P/name)for name in watched},'sources':before,'command':command,'solidity_src_identical_to_initial_post_cleanup_snapshot':True,'scope':'30 affected synthetic fixture tests; unchanged22 Native/Membership/metadata methods remain separately source-bound to initial run, not rerun or summed twice'}
(P/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(str(P),flush=True);print(json.dumps({k:report[k]for k in('exit_code','seconds','tests','source_unchanged','snapshot_exact')}),flush=True)
assert proc.returncode==0 and len(cases)==30 and all(c['status']=='Success'for c in cases)and report['source_unchanged']and report['snapshot_exact']
