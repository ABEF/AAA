from pathlib import Path
import subprocess,json,sys,hashlib,time
R=Path.cwd();E=Path(__file__).parent;D=E/'release-checks';D.mkdir(exist_ok=False)
modules=['tests_python.test_slither_review','tests_python.test_function_reference','tests_python.test_operator_reference',
 'tests_python.test_exact_lp_inventory','tests_python.test_exact_lp_profile7','tests_python.test_production_preflight_cli',
 'tests_python.test_frontend_policy_v6','tests_python.test_frontend_lifecycle']
t=time.monotonic();r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','-v',*modules],capture_output=True,cwd=R,timeout=120)
(D/'stdout.txt').write_bytes(r.stdout);(D/'stderr.txt').write_bytes(r.stderr)
record={'exit_code':r.returncode,'modules':modules,'elapsed':time.monotonic()-t,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()};(D/'status.json').write_text(json.dumps(record,indent=2)+'\n')
print(r.stderr.decode()[-4500:]);print(json.dumps(record));sys.exit(r.returncode)
