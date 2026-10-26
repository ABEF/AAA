"""Offline conversion-reader regression evidence; no RPC, signer or services."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
phase = sys.argv[1]
assert phase in ('before', 'after')
paths = ['keeper/royalties.py', 'keeper/monitor.py', 'tests_python/test_keeper_conversion_integrity.py',
         'tests_python/test_royalty_keeper.py', 'tests_python/test_typed_v4_conversion_keeper.py']
hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
output = io.StringIO(); start = time.monotonic()
selection = 'tests_python.test_keeper_conversion_integrity.ConversionBooleanIntegrityTests'
result = unittest.TextTestRunner(stream=output, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromName(selection))
report = dict(observed_at_utc=datetime.now(timezone.utc).isoformat(), phase=phase,
    scope='Actual Keeper/RoyaltyAutomation, disposable state files and injected byte RPC. Three explicit profiles and both ledgers. No network/signing/service.',
    selection=selection, tests_run=result.testsRun,
    failures=[dict(test=str(t), traceback=reason) for t, reason in result.failures],
    errors=[dict(test=str(t), traceback=reason) for t, reason in result.errors],
    successful=result.wasSuccessful(), elapsed_seconds=round(time.monotonic()-start,3),
    source_sha256=hashes, source_unchanged=hashes == {
        p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
target=Path(__file__).resolve().parent
(target/(phase+'.json')).write_bytes((json.dumps(report,indent=2)+'\n').encode())
(target/(phase+'.log')).write_bytes(output.getvalue().encode())
print(json.dumps({key:report[key] for key in ('phase','tests_run','successful','elapsed_seconds','source_unchanged')}))
sys.exit(0 if result.wasSuccessful() else 1)
