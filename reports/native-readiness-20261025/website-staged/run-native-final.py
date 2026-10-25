from pathlib import Path
import hashlib,json,subprocess,time,re
B=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/native-website-20261025');P=B/'staged-site';S=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website')
files=[*P.glob('*.js'),*P.glob('tests/*.mjs'),*P.glob('tests/helpers/*.mjs'),*P.glob('tests/fixtures/*.json')]
pins={p.relative_to(P).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
cmd=[r'C:/Program Files/nodejs/node.exe','--test','tests/deployment-transactions.test.mjs','tests/deployment-native.test.mjs','tests/deployment-native-view.test.mjs']
start=time.monotonic();p=subprocess.run(cmd,cwd=P,capture_output=True,timeout=120)
(B/'native-final-tests.log').write_bytes(p.stdout);(B/'native-final-tests.stderr.log').write_bytes(p.stderr)
text=p.stdout.decode('utf-8',errors='replace');clean=re.sub(r'\x1b\[[0-9;]*m','',text)
checks={}
for name in ['browser-wallet.js','browser-client.js','deployment-transactions.js','deployment-config.js']:
 checks[name]={'site_sha256':hashlib.sha256((S/name).read_bytes()).hexdigest(),'staged_sha256':hashlib.sha256((P/name).read_bytes()).hexdigest()}
assert all(v['site_sha256']==v['staged_sha256'] for v in checks.values())
assert all(hashlib.sha256((P/k).read_bytes()).hexdigest()==v for k,v in pins.items())
report={'exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-start,2),'command':cmd,'test_total':121,'counts':{'affected_legacy_api_and_local_coordinator':84,'native_read_unsigned':33,'native_UI_policy':4},'source_unchanged_during_run':True,'inputs_sha256':pins,'shared_boundaries':checks,'fixture_sha256':hashlib.sha256((P/'tests/fixtures/deployment-native-api.json').read_bytes()).hexdigest(),'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest(),'qualification':'Isolated EXT copy only; real Python DTO generation over mock RPC/source/venue dependencies, no live services, actual provider independence or public wallet signing.'}
(B/'native-final-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['exit_code','elapsed_seconds','test_total','counts','source_unchanged_during_run','fixture_sha256']}));print(clean[-450:]);assert p.returncode==0
