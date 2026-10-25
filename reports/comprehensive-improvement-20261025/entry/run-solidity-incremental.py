from pathlib import Path
import os,json,hashlib,shutil,subprocess,time,sys
R=Path.cwd();E=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9');B=E/'review-policy-20261025';P=B/'entry-review-profile';tag='entry-review-final'
shutil.copytree(R/'src',P/'src',dirs_exist_ok=True)
for name in ('EntryReviewPolicy.t.sol','TypedV4Entry.t.sol'):shutil.copy2(R/'test'/name,P/'test'/name)
pins={p.relative_to(P).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src','test') for p in (P/folder).rglob('*.sol')}
(B/(tag+'-inputs.json')).write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8',newline='\n')
cmd=[str(E/'foundry-v1.4.4/forge.exe'),'test','--root',str(P),'--use',str(E/'toolchain-0.8.26/solc.exe'),'--match-contract','EntryReviewPolicyTest|TypedV4EntryTest','--match-test','testMaximumAboveTenPercentAndLegacySelectorsFailClosed|testMalformedMaximumABI|testNativeReviewedCap','--json']
env=os.environ.copy();env['RAYON_NUM_THREADS']='2';t=time.monotonic();p=subprocess.run(cmd,capture_output=True,env=env,timeout=1500)
(B/(tag+'.json')).write_bytes(p.stdout);(B/(tag+'.stderr.log')).write_bytes(p.stderr)
try:
 x=json.loads(p.stdout);cases=[{'suite':suite,'test':name,'status':v.get('status'),'reason':v.get('reason')} for suite,z in x.items() for name,v in z.get('test_results',{}).items()]
except Exception:cases=[]
report={'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-t,'command':cmd,'cases':cases,'diagnostic':p.stdout.decode(errors='replace')[:4000] if not cases else None,'notice':'Incremental same production compiler profile; reruns one repaired test plus two later-added cases only. No unchanged suite repetition.'}
(B/(tag+'-summary.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report,indent=2));sys.exit(p.returncode)
