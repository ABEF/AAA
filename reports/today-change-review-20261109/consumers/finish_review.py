from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
D=Path(__file__).resolve().parent;E=D/'regression-01'
for name in ('REVIEW.md','REVIEW.json','manifest.json'):shutil.copyfile(D/name,E/(name+'.before-fix'))
for path,name in [('zzz_ops/production_v15.py','production_v15-after.py'),('tests_python/test_production_v15.py','test_production_v15-after.py')]:shutil.copyfile(R/path,E/name)
diff=subprocess.check_output(['git','-C',str(R),'diff','--','zzz_ops/production_v15.py','tests_python/test_production_v15.py'],stderr=subprocess.DEVNULL)
with (E/'implemented.diff').open('xb')as f:f.write(diff)
red=json.loads((E/'red/verification.json').read_text(encoding='utf-8'));green=json.loads((E/'green/verification.json').read_text(encoding='utf-8'))
assert red['exit_code']!=0 and green['exit_code']==0 and red['source_unchanged'] and green['source_unchanged']
review=json.loads((D/'REVIEW.json').read_text(encoding='utf-8'))
for finding in review['findings']:finding['resolution']='fixed locally after the pinned read-only review; see fix_verification'
review['fix_verification']={'changed_files':['zzz_ops/production_v15.py','tests_python/test_production_v15.py'],
 'behavior':'Offline preflight now reconciles current phase against the pinned exact timestamp using the helper inclusive stage order and accepts valid phase0 gaps/pre/post-sale. Disabled-family counts require exact int0. No contract behavior or authority changes.',
 'red':{'raw_log':'regression-01/red/unittest.log','verification':'regression-01/red/verification.json','methods':5,'outcome':'Expected failure against unchanged validator:16 failing subcases across3methods;2valid-boundary/gap methods already pass.'},
 'green':{'raw_log':'regression-01/green/unittest.log','verification':'regression-01/green/verification.json','methods':13,'outcome':'All13 affected inventory methods pass, including5new focused methods. Unchanged3 observer-wire methods and browser/Solidity suites were not rerun.'},
 'final_source_sha256':green['source_after'],'no_rpc_or_deployment':True,'comparison_rules_or_financial_limits_changed':False,'unrelated_work_preserved':True}
(D/'REVIEW.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
text=(D/'REVIEW.md').read_text(encoding='utf-8')
text=text.replace('No tests, network probes, signing, deployment or source changes were performed.','The initial inspection performed no tests, network probes, signing, deployment or source changes. Two resulting preflight fixes were then explicitly authorized and verified as described below.')
text=text.replace('Two narrow consistency findings remain in the pinned source:','Two narrow consistency findings were found in the pinned source and are now corrected locally:')
text+='''
The only implementation edits are `zzz_ops/production_v15.py` and `tests_python/test_production_v15.py`. The synthetic fixture now explicitly observes timestamp300, the inclusive start of its public stage. Five new methods first ran against the unchanged validator:16 mismatching/invalid subcases failed as expected, while valid boundaries and interstage gaps already passed. After the two fixes, all13 methods in the affected inventory class passed once. Raw red/green logs and before/after source hashes are retained under `regression-01/`; unchanged observer-wire, browser and Solidity suites were not rerun. No RPC, deployment, financial-limit, contract, signer, website, service or journal change occurred.
'''
(D/'REVIEW.md').write_text(text,encoding='utf-8',newline='\n')
records=[]
for path in sorted(D.rglob('*')):
    if path.is_file() and path!=D/'manifest.json' and '__pycache__'not in path.parts:
        raw=path.read_bytes();records.append({'path':path.relative_to(D).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(D/'manifest.json').write_text(json.dumps({'files':records},indent=2)+'\n',encoding='utf-8',newline='\n')
for row in records:assert hashlib.sha256((D/row['path']).read_bytes()).hexdigest()==row['sha256']
print(json.dumps({'files':len(records),'bytes':sum(x['bytes']for x in records),'manifest_sha256':hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),'red':'5methods/16expected failing subcases','green':'13affected methods pass','source_stable_during_each':True}))
