"""Run the current portable keeper scope, recording exact hashes and exclusions."""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
FOUNDRY = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/foundry-v1.4.4')
os.environ['PATH'] = str(FOUNDRY)+os.pathsep+os.environ.get('PATH','')
MODULES = ['tests_python.test_keeper_preparation','tests_python.test_keeper','tests_python.test_keeper_ops',
           'tests_python.test_keeper_recovery','tests_python.test_metadata_keeper','tests_python.test_keeper_reservations']
EXCLUDED = {'tests_python.test_keeper_recovery.RecoveryTests.test_runtime_permissions_and_symlinks_fail_closed':
            'Requires POSIX ownership, permissions and symlink semantics; current host is Windows.'}
SOURCES = ['keeper/__init__.py','keeper/monitor.py','keeper/ops.py','keeper/rehearsal/KeeperVenue.sol',
           'zzz_ops/abi.py','zzz_ops/rpc.py','zzz_ops/state.py',
           *[module.replace('.','/')+'.py' for module in MODULES],
           str(Path(__file__).resolve().relative_to(ROOT)).replace('\\','/')]

def hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}

def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite): yield from flatten(item)
        else: yield item

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
before = hashes()
cast = shutil.which('cast')
if not cast: raise RuntimeError('Pinned cast must be available inside Python before importing tests')
inventory = list(flatten(unittest.defaultTestLoader.loadTestsFromNames(MODULES)))
ids = {test.id() for test in inventory}
if not set(EXCLUDED).issubset(ids): raise RuntimeError('Expected POSIX exclusion absent from inventory')
tests = [test for test in inventory if test.id() not in EXCLUDED]
stream = io.StringIO()
timer = time.monotonic()
result = unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(tests))
after = hashes()
passed = result.wasSuccessful() and not result.skipped and before == after
report = {'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'duration_seconds':round(time.monotonic()-timer,3),'python':platform.python_version(),
          'platform':platform.platform(),'cast':cast,'cast_sha256':hashlib.sha256(Path(cast).read_bytes()).hexdigest(),
          'inventory_count':len(inventory),'tests_run':result.testsRun,'failures':len(result.failures),
          'errors':len(result.errors),'runtime_skips':len(result.skipped),'successful':passed,
          'excluded':[{'test':name,'reason':reason} for name,reason in EXCLUDED.items()],
          'test_ids':[test.id() for test in tests],'source_sha256_before':before,'source_sha256_after':after,
          'source_unchanged':before == after,
          'scope':'Portable keeper unit/integration mocks and actual cast CLI parser; no signer keys, public RPC, '
                  'public transactions, deployed staging changes or fresh real-process rehearsal. '
                  'KeeperVenue.sol is hash-bound only; this Python run does not compile or execute it.'}
(OUT/'tests.log').write_text(stream.getvalue(),encoding='utf-8')
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:report[key] for key in ('tests_run','failures','errors','runtime_skips','successful',
                                           'source_unchanged','inventory_count','excluded')},indent=2))
sys.exit(0 if passed else 1)
