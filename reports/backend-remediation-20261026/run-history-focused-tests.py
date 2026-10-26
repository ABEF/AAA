"""One scoped offline evidence capture; no external state or live RPC."""
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
SELECTION = {
    'semantic': ['tests_python.test_lp_fee_conservation.StrictFeeReplayTests.test_strict_nft_math_keeps_lp_share_collective_and_royalty_rarity_independent'],
    'canonical': ['tests_python.test_lp_fee_conservation.StrictFeeReplayTests.test_strict_canonical_epoch_skips_imports_and_resets_only_observed_fee_keys'],
    'dust-before': ['tests_python.test_lp_fee_conservation.CurrentFeeDustAPITests'],
    'dust-after': ['tests_python.test_lp_fee_conservation.CurrentFeeDustAPITests',
                   'tests_python.test_lp_fee_conservation.CurrentFeeConservationAPITests'],
}[PHASE]
paths = ['frontend_api/earnings.py', 'frontend_api/earnings_replay.py', 'frontend_api/wallet_earnings.py',
         'frontend_api/service.py', 'tests_python/test_lp_fee_conservation.py']
hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}
out = io.StringIO(); start = time.monotonic()
result = unittest.TextTestRunner(stream=out, verbosity=2).run(unittest.TestSuite(
    unittest.defaultTestLoader.loadTestsFromName(name) for name in SELECTION))
report = dict(observed_at_utc=datetime.now(timezone.utc).isoformat(), phase=PHASE,
    scope='Synthetic offline RPC, actual byte-ABI Projection and disposable SQLite only. No network or signing.',
    selection=SELECTION, tests_run=result.testsRun,
    failures=[dict(test=str(test), traceback=error) for test,error in result.failures],
    errors=[dict(test=str(test), traceback=error) for test,error in result.errors],
    successful=result.wasSuccessful(), elapsed_seconds=round(time.monotonic()-start, 3),
    source_sha256=hashes, source_unchanged=hashes == {
        name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})
destination = ROOT/'reports/backend-remediation-20261026'
(destination/('history-'+PHASE+'.json')).write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
(destination/('history-'+PHASE+'.log')).write_text(out.getvalue(), encoding='utf-8')
print(json.dumps({key: report[key] for key in ('phase', 'tests_run', 'successful', 'elapsed_seconds')}))
sys.exit(0 if result.wasSuccessful() else 1)
