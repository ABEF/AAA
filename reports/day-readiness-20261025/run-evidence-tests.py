"""Run only affected evidence-generator tests; no Solidity compiler or EVM."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent
names=sys.argv[1:]
stem='evidence-tests' if not names else 'evidence-failed-recheck'
destination=HERE/(stem+'.json')
if destination.exists():raise ValueError('Preserve earlier test evidence')
watched=('zzz_ops/function_reference.py','tests_python/test_function_reference.py','scripts/generate-function-reference.py')
hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in watched}
suite=unittest.defaultTestLoader.loadTestsFromNames(names or ['tests_python.test_function_reference'])
def ids(value):
    return [name for item in value for name in (ids(item) if isinstance(item,unittest.TestSuite) else [item.id()])]
selected=ids(suite)
start=time.monotonic()
with (HERE/(stem+'.log')).open('w',encoding='utf-8') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
elapsed=round(time.monotonic()-start,3)
failures={case.id():detail for case,detail in result.failures}
errors={case.id():detail for case,detail in result.errors}
skips={case.id():detail for case,detail in result.skipped}
unchanged=hashes=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in watched}
report={'scope':'Focused evidence importer/generator/CLI checks only; no compiler, EVM, network, signing or services.',
    'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'command':[sys.executable,'-X','utf8',str(Path(__file__).relative_to(ROOT)),*names],
    'source_sha256':hashes,'sources_unchanged':unchanged,'elapsed_seconds':elapsed,'tests_run':result.testsRun,
    'selected_methods':selected,'failures':failures,'errors':errors,'skips':skips,
    'successful':result.wasSuccessful() and unchanged}
destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:report[key] for key in ('tests_run','elapsed_seconds','sources_unchanged','successful')},indent=2))
if failures or errors:print(json.dumps({'failures':failures,'errors':errors},indent=2))
sys.exit(0 if report['successful'] else 1)
