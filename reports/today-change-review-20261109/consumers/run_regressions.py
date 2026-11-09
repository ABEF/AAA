from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
R=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=Path(__file__).resolve().parent/'regression-01'
stage=sys.argv[1]
assert stage in ('red','green')
D=E/stage;D.mkdir(exist_ok=False)
methods=['test_phase_matches_every_inclusive_stage_boundary','test_phase_zero_is_valid_between_stages',
 'test_in_range_phase_code_cannot_contradict_the_pinned_timestamp','test_phase_requires_an_exact_pinned_timestamp',
 'test_disabled_mint_family_counts_reject_boolean_zero_aliases']
targets=['tests_python.test_production_v15.MintInventoryTests.'+name for name in methods] if stage=='red' else ['tests_python.test_production_v15.MintInventoryTests']
paths=['zzz_ops/production_v15.py','tests_python/test_production_v15.py','config/production.example.json']
def pins():return {p:hashlib.sha256((R/p).read_bytes()).hexdigest()for p in paths}
before=pins()
if stage=='red':assert (R/paths[0]).read_bytes()==(E/'production_v15-before.py').read_bytes()
py='C:/Users/Ali/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
cmd=[py,'-B','-X','utf8','-m','unittest','-v',*targets]
keep=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','HOMEDRIVE','HOMEPATH')
env={k:os.environ[k]for k in keep if k in os.environ};env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(R)
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(cmd,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
with (D/'unittest.log').open('xb')as f:f.write(p.stdout)
after=pins()
record={'stage':stage,'command':cmd,'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'exit_code':p.returncode,'source_before':before,'source_after':after,'source_unchanged':before==after,
 'credentials_inherited':False,'no_network_or_chain_requested':True,'scope':'New consumer preflight regressions only against unpatched code'if stage=='red'else'Affected MintInventoryTests class including5new methods; no unchanged wire/browser/Solidity suites rerun',
 'raw_log_sha256':hashlib.sha256(p.stdout).hexdigest()}
with (D/'verification.json').open('x',encoding='utf-8',newline='\n')as f:json.dump(record,f,indent=2);f.write('\n')
print(p.stdout.decode('utf-8'))
assert before==after
if stage=='red':assert p.returncode!=0
else:assert p.returncode==0
