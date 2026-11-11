from pathlib import Path
import hashlib,json,subprocess
E=Path(__file__).resolve().parent;W=Path('C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website')
node='C:/Program Files/nodejs/node.exe'
commands=[[node,'--test','--test-reporter=tap','tests/current-demo-policy.test.mjs','tests/domain.test.mjs','tests/ui-state.test.mjs','tests/contribution-flow.test.mjs','tests/reward-display-audit.test.mjs']]
commands.extend([[node,'--check',f] for f in ['domain.js','app.js','preview-store.js','tests/current-demo-policy.test.mjs','tests/contribution-flow.test.mjs']])
rows=[]
for i,cmd in enumerate(commands):
 p=subprocess.run(cmd,cwd=W,capture_output=True,text=True)
 log=E/f'demo-after-{i}.log'
 with log.open('x',encoding='utf-8') as f:f.write(p.stdout);f.write(p.stderr)
 rows.append({'command':cmd,'exit_code':p.returncode,'log':log.name,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
with (E/'demo-after.json').open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2);f.write('\n')
print(json.dumps(rows));print((E/'demo-after-0.log').read_text()[-1300:])
assert all(row['exit_code']==0 for row in rows)
