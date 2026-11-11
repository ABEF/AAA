from pathlib import Path
import contextlib,datetime,hashlib,importlib,json,sys,time,unittest
R=Path.cwd();E=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
from scripts.run_python_tests import select_tests,Results
modules=['test_frontend_transactions','test_frontend_activation','test_indexer','test_indexer_config_integrity']
paths=[R/n for n in ('zzz_ops/abi.py','indexer/monitor.py','tests_python/test_abi.py','tests_python/test_indexer_startup_atomicity.py')]
paths+=sorted((R/'frontend_api').glob('*.py'))+sorted((R/'zzz_ops').glob('*.py'))+sorted((R/'indexer').glob('*.py'))
def pins():return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=pins();tests,classes=select_tests(modules);started=time.monotonic()
with (E/'consumer-tests.log').open('x',encoding='utf-8') as log:
 with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
  result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Results).run(unittest.TestSuite(tests.values()))
after=pins();record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'modules':modules,
 'selected_methods':list(tests),'executed_methods':result.methods,'tests_run':result.testsRun,
 'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
 'successful':result.wasSuccessful() and before==after and result.methods==list(tests),
 'seconds':round(time.monotonic()-started,3),'source_sha256_before':before,'source_sha256_after':after,
 'scope':'Affected ordinary unsigned transaction/activation and actual disposable SQLite consumers; no live services/RPC or Solidity execution.'}
with (E/'consumer-tests.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:record[k] for k in ('tests_run','failures','errors','skips','successful','seconds')}))
raise SystemExit(0 if record['successful'] else 1)
