from pathlib import Path
import hashlib,json,subprocess,sys
E=Path(__file__).resolve().parent;W=Path('C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website')
stage=sys.argv[1];assert stage in ['before','after']
node='C:/Program Files/nodejs/node.exe';rows=[]
commands=[[node,'--test','tests/deployment-bundle.test.mjs']]
if stage=='after':commands.extend([[node,'--check',f] for f in ['build.mjs','server.mjs','tests/deployment-bundle.test.mjs']])
for i,cmd in enumerate(commands):
 p=subprocess.run(cmd,cwd=W,capture_output=True,text=True)
 log=E/f'{stage}-{i}.log'
 with log.open('x',encoding='utf-8') as f:f.write(p.stdout);f.write(p.stderr)
 rows.append({'command':cmd,'exit_code':p.returncode,'log':log.name,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
with (E/f'{stage}.json').open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2);f.write('\n')
print(json.dumps(rows))
if stage=='before':assert rows[0]['exit_code']!=0
else:assert all(row['exit_code']==0 for row in rows)
