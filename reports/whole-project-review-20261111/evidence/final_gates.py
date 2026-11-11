from pathlib import Path
import hashlib,json,shutil,subprocess,sys
R=Path.cwd();E=Path(__file__).resolve().parent;D=R/'reports/whole-project-review-20261111'
commands=[['scripts/generate-function-reference.py','--check'],['scripts/generate-operator-reference.py','--check'],['scripts/sync-project-todo.py','--check'],['scripts/check-slither-review.py',str(E/'static/static-d96917a2cb/slither.json')],[str(E/'final_integrity.py')]]
results=[]
for args in commands:
 p=subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=R,capture_output=True,text=True)
 results.append({'args':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 print(json.dumps({'gate':Path(args[0]).name,'exit_code':p.returncode,'output':p.stdout.strip()[:1200]}))
 assert p.returncode==0,results[-1]
(E/'final-gates.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
manifest_path=D/'evidence/manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
for name in ('final-gates.json','final-integrity.json','final_gates.py','final_integrity.py'):
 target=D/'evidence'/name;shutil.copyfile(E/name,target)
 h=hashlib.sha256(target.read_bytes()).hexdigest()
 manifest['files'].append({'original_evidence':name,'published':'evidence/'+name,'bytes':target.stat().st_size,'sha256':h,'stored_sha256':h})
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Final gate evidence retained; no code suites repeated for documentation changes.')
