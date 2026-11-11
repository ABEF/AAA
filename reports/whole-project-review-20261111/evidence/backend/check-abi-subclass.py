from pathlib import Path
import contextlib,datetime,hashlib,json,sys,time,unittest
R=Path.cwd();E=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
from scripts.run_python_tests import select_tests,Results
stage=sys.argv[1];tests,classes=select_tests(['test_abi'])
if stage=='abi-subclass-negative':
    tests={k:v for k,v in tests.items() if k.endswith('.test_uint_input_never_truncates_or_coerces_nonintegers')}
paths=[R/'zzz_ops/abi.py',R/'tests_python/test_abi.py']
def pins():return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=pins();started=time.monotonic()
with (E/(stage+'.log')).open('x',encoding='utf-8') as log:
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Results).run(unittest.TestSuite(tests.values()))
after=pins();record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'selected_methods':list(tests),'executed_methods':result.methods,'tests_run':result.testsRun,
 'failures':[(x.id(),s) for x,s in result.failures],'errors':[(x.id(),s) for x,s in result.errors],
 'skips':[(x.id(),reason) for x,reason in result.skipped],
 'source_sha256_before':before,'source_sha256_after':after,
 'successful':before==after and result.wasSuccessful() and result.methods==list(tests),
 'seconds':round(time.monotonic()-started,3),
 'scope':'Exact-type input validation; hostile Python str subclass, not an external JSON exploit. Ordinary ints/decimal strings, leading zeros, precision and static ABI vectors remain checked. No economic/profile/deployment change. Checkpoint rebuild/review before future adoption remains required.'}
with (E/(stage+'.json')).open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({key:record[key] if key not in ('failures','errors','skips') else len(record[key]) for key in ('tests_run','failures','errors','skips','successful','seconds','source_sha256_after')}))
raise SystemExit(0 if record['successful'] else 1)
