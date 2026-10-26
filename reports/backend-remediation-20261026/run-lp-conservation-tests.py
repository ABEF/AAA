"""Scoped offline regression capture; never signs, connects RPC or starts services."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PHASE = sys.argv[1]
assert PHASE in ('before', 'after')
SELECTION = ['tests_python.test_lp_fee_conservation.CurrentFeeConservationAPITests']
if PHASE == 'after':
    SELECTION.append('tests_python.test_lp_fee_conservation.StrictFeeReplayTests')
paths = ['frontend_api/earnings.py', 'frontend_api/earnings_replay.py', 'frontend_api/wallet_earnings.py',
         'tests_python/test_lp_fee_conservation.py']
hashes = {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths}
loader = unittest.TestLoader()
suite = unittest.TestSuite(loader.loadTestsFromName(n) for n in SELECTION)
out = io.StringIO(); start = time.monotonic()
result = unittest.TextTestRunner(stream=out, verbosity=2).run(suite)
report = dict(observed_at_utc=datetime.now(timezone.utc).isoformat(), phase=PHASE,
    scope='Current3/fee1 actual SQLite and Projection earnings composition plus explicitly versioned event conservation. Synthetic offline RPC only.',
    selection=SELECTION, tests_run=result.testsRun,
    failures=[dict(test=str(test), traceback=error) for test,error in result.failures],
    errors=[dict(test=str(test), traceback=error) for test,error in result.errors],
    successful=result.wasSuccessful(), elapsed_seconds=round(time.monotonic()-start,3),
    source_sha256=hashes, source_unchanged=hashes=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})
target=ROOT/'reports/backend-remediation-20261026'
(target/('lp-conservation-'+PHASE+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(target/('lp-conservation-'+PHASE+'.log')).write_text(out.getvalue(),encoding='utf-8')
print(json.dumps({k:report[k] for k in ('phase','tests_run','successful','elapsed_seconds')}))
sys.exit(0 if result.wasSuccessful() else 1)
