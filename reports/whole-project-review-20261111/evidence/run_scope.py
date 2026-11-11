from pathlib import Path
import datetime,hashlib,json,subprocess,sys,time
R=Path.cwd();E=Path(__file__).resolve().parent
label=sys.argv[1]; selectors=sys.argv[2:]
assert label and selectors and all(s.startswith('tests_python.') for s in selectors)
D=E/'keeper';D.mkdir(exist_ok=True)
source_names=['keeper/monitor.py','tests_python/test_keeper_late_job_budget.py','zzz_ops/abi.py']
def pins():return {n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in source_names}
before=pins();start=time.monotonic()
command=[sys.executable,'-B','-X','utf8','-m','unittest',*selectors]
with (D/(label+'.log')).open('xb') as log:
 result=subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT)
record={'command':command,'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-start,
 'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_before':before,'source_after':pins(),
 'fixture_scope':'inert RPC, temp journal, mocked signer; no actual submission/service/chain',
 'no_service_or_chain_change':True}
with (D/(label+'.json')).open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record));print((D/(label+'.log')).read_text()[-3600:])
raise SystemExit(result.returncode)
