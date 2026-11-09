from pathlib import Path
import gzip,hashlib,json,os,subprocess,sys
R=Path.cwd();E=Path(__file__).parent;D=E/'final-gates';D.mkdir(exist_ok=False)
raw=gzip.decompress((R/'reports/contribution-loss3-20261109/static/detectors-only.json.gz').read_bytes());(D/'detectors.json').write_bytes(raw)
keep=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','HOMEDRIVE','HOMEPATH')
env={k:os.environ[k]for k in keep if k in os.environ}
checks=[('functions',['scripts/generate-function-reference.py','--check'],0),('operator',['scripts/generate-operator-reference.py','--check'],0),('todo',['scripts/sync-project-todo.py','--check'],0),('static-coverage',['scripts/check-slither-review.py',str(D/'detectors.json')],0),('default-preflight',['scripts/validate-production-config.py','config/production.example.json'],1)]
rows=[]
for name,args,expected in checks:
 run=subprocess.run([sys.executable,'-B','-X','utf8',*args],capture_output=True,env=env,timeout=60)
 (D/(name+'.stdout')).write_bytes(run.stdout);(D/(name+'.stderr')).write_bytes(run.stderr)
 ok=run.returncode==expected
 row={'name':name,'arguments':args,'exit_code':run.returncode,'expected_exit':expected,'passed':ok,'stdout_sha256':hashlib.sha256(run.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(run.stderr).hexdigest()}
 if name=='default-preflight':
  data=json.loads(run.stdout);row['default_remains_blocked']=data.get('production_approved')is False or data.get('passed')is False or bool(data.get('errors'))or bool(data.get('blockers'))
  row['result_keys']=sorted(data.keys());assert row['default_remains_blocked'],data.keys()
 rows.append(row);print(json.dumps({k:v for k,v in row.items()if k not in ('arguments','stdout_sha256','stderr_sha256')}))
 if not ok:raise SystemExit('Unexpected gate outcome: '+name)
record={'baseline':'d81185684d768b0afccfed4801a443ed4ccca60d','credentials_inherited':False,'checks':rows,'no_tests_or_analyzer_rerun':True}
(D/'verification.json').write_text(json.dumps(record,indent=2)+'\n')
target=R/'reports/today-change-review-20261109/final-gates';target.mkdir()
for p in D.iterdir():
 if p.name!='detectors.json':(target/p.name).write_bytes(p.read_bytes())
