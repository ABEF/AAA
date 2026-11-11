from pathlib import Path
import contextlib,datetime,hashlib,importlib,json,sys,time,unittest
R=Path.cwd();E=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
from scripts.run_python_tests import select_tests,Results
modules=['test_abi','test_indexer_startup_atomicity','test_frontend_transactions',
 'test_frontend_activation','test_indexer','test_indexer_config_integrity']
tests,classes=select_tests(modules)
specific=(('test_earnings_checkpoints','CheckpointAPITests',
 'test_hash_mismatch_missing_partial_duplicate_json_and_source_drift_reject'),
 ('test_earnings_checkpoint_v2','Checkpoint2APITests',
 'test_truncation_source_drift_and_checkpoint_hash_mismatch_never_fall_back'))
for module,name,method in specific:
    item=getattr(importlib.import_module('tests_python.'+module),name)(method)
    assert item.id() not in tests;tests[item.id()]=item
assert len(tests)==117
paths=sorted({p for directory in ('frontend_api','zzz_ops','indexer') for p in (R/directory).glob('*.py')})
paths+=sorted({R/(identifier.replace('.','/')+'.py') for identifier in []})
paths+=sorted({R/'tests_python'/(module+'.py') for module in modules+[x[0] for x in specific]})
def pins():return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=pins();started=time.monotonic()
with (E/'final-backend-117.log').open('x',encoding='utf-8') as log:
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Results).run(unittest.TestSuite(tests.values()))
after=pins();record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'modules':modules,
 'specific_checkpoint_methods':[x.id() for x in list(tests.values())[-2:]],
 'selected_methods':list(tests),'executed_methods':result.methods,'tests_run':result.testsRun,
 'failures':[(x.id(),s) for x,s in result.failures],'errors':[(x.id(),s) for x,s in result.errors],
 'skips':[(x.id(),reason) for x,reason in result.skipped],
 'successful':result.wasSuccessful() and before==after and result.methods==list(tests),
 'seconds':round(time.monotonic()-started,3),'source_sha256_before':before,'source_sha256_after':after,
 'scope':'One deduplicated final-source117-method backend scope, including full static codec21/startup13/affectedconsumers81/checkpoint-source-drift2. No live providers, Solidity execution, signer, service or environment change.'}
with (E/'final-backend-117.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({key:record[key] if key not in ('failures','errors','skips') else len(record[key]) for key in ('tests_run','failures','errors','skips','successful','seconds')}))
raise SystemExit(0 if record['successful'] else 1)
