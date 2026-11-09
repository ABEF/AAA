from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
R=Path.cwd();E=Path(__file__).resolve().parent;D=R/'reports/contribution-loss3-20261109'
logdir=E/'default-check';logdir.mkdir(exist_ok=False)
py=Path('C:/Users/Ali/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
report=E/'static-417c118f1d/detectors-only.json'
cmd=[str(py),'-B','-X','utf8',str(R/'scripts/check-slither-review.py'),str(report)]
before={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'src').rglob('*.sol')}
original=(E/'check-slither-review-before.py').read_bytes();current=(R/'scripts/check-slither-review.py').read_bytes()
assert original.replace(b'reports/opensea-integration-20261109/static-review.json',b'reports/contribution-loss3-20261109/static-review.json',1)==current
keep=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','HOMEDRIVE','HOMEPATH')
env={k:os.environ[k]for k in keep if k in os.environ};env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(R)
result=subprocess.run(cmd,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
with (logdir/'default-check.log').open('xb')as f:f.write(result.stdout)
after={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'src').rglob('*.sol')}
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exit_code':result.returncode,'source_before':before,'source_after':after,'source_unchanged':before==after,'checker_only_default_path_changed':True,'existing_comparison_rules_unchanged':True,'log_sha256':hashlib.sha256(result.stdout).hexdigest(),'credentials_inherited':False,'no_recompile':True,'no_new_analyzer_run':True}
with (logdir/'verification.json').open('x',encoding='utf-8',newline='\n')as f:json.dump(record,f,indent=2);f.write('\n')
assert result.returncode==0 and before==after,result.stdout.decode('utf-8')
print(result.stdout.decode('utf-8'))
manifest=json.loads((D/'contract-static-manifest.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    raw=(D/row['path']).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps({'manifest_entries':len(manifest['files']),'mismatches':0,'comparison_rules_changed':False}))
