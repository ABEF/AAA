"""Two strict-format regressions, before/after; no compiler, EVM or network."""
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
if sys.argv[1:] not in (['initial'],['final']):raise ValueError('Select initial or final scope')
phase=sys.argv[1]
HERE=Path(__file__).resolve().parent
destination=HERE/('format-tests-'+phase+'.json')
if destination.exists():raise ValueError('Preserve prior evidence')
methods=['tests_python.test_function_reference.FunctionReferenceTests.'+name for name in (
    'test_outer_schema_one_requires_an_integer_for_snapshots_notes_and_merges',
    'test_fixed_point_abi_width_precision_and_aliases_are_canonical')]
if phase=='final':methods.append('tests_python.test_function_reference.FunctionReferenceTests.test_canonical_nested_tuple_arrays_and_overloads_are_exact')
paths=('zzz_ops/function_reference.py','tests_python/test_function_reference.py')
hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}
start=time.monotonic()
with (HERE/('format-tests-'+phase+'.log')).open('w',encoding='utf-8') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(methods))
unchanged=hashes=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}
report={'scope':'Only strict outer schema and fixed-point ABI formats; final scope includes one affected existing canonical-type control.',
    'phase':phase,'command':[sys.executable,'-X','utf8',str(Path(__file__).relative_to(ROOT)),phase],
    'methods':methods,'tests_run':result.testsRun,'source_sha256':hashes,'unchanged':unchanged,
    'elapsed_seconds':round(time.monotonic()-start,4),
    'failures':[{'case':case.id(),'traceback':detail} for case,detail in result.failures],
    'errors':[{'case':case.id(),'traceback':detail} for case,detail in result.errors],
    'successful':result.wasSuccessful() and unchanged}
destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:report[key] for key in ('phase','tests_run','elapsed_seconds','unchanged','successful')},indent=2))
print(json.dumps({'failed_subcases':len(report['failures']),'errors':len(report['errors'])}))
sys.exit(0 if report['successful'] else 1)
