from pathlib import Path
import subprocess,json,sys,hashlib,time
E=Path(__file__).parent;R=Path.cwd();D=E/'api-attempt1';D.mkdir(exist_ok=False)
modules=['tests_python.test_transaction_gas_policy_v2','tests_python.test_frontend_transactions','tests_python.test_claim_planner']
paths=['frontend_api/transaction_gas.py','frontend_api/transactions.py','frontend_api/claim_planner.py','tests_python/test_transaction_gas_policy_v2.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={p:sha(R/p)for p in paths};start=time.monotonic()
r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','-v',*modules],capture_output=True,cwd=R,timeout=120)
(D/'stdout.txt').write_bytes(r.stdout);(D/'stderr.txt').write_bytes(r.stderr)
x={'exit_code':r.returncode,'modules':modules,'elapsed':time.monotonic()-start,'before':before,'after':{p:sha(R/p)for p in paths}};(D/'status.json').write_text(json.dumps(x,indent=2)+'\n')
print(r.stderr.decode()[-7000:]);print(json.dumps(x));sys.exit(r.returncode)
