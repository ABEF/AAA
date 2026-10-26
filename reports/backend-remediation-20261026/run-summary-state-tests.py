"""Capture current inactive-state and both LP/ETH integrity boundaries only."""
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
TARGET = Path(__file__).parent


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    phase = sys.argv[1]
    if phase not in ('before', 'after'):
        raise ValueError('Explicit evidence phase required')
    prefix = TARGET / ('summary-state-' + phase)
    if prefix.with_suffix('.json').exists() or prefix.with_suffix('.log').exists():
        raise ValueError('Evidence already exists; preserve it and use a new attempt')
    paths = ('frontend_api/portfolio.py', 'tests_python/test_wallet_summary_integrity.py',
             'tests_python/test_wallet_summary.py')
    hashes = {name: digest(name) for name in paths}
    names = ['tests_python.test_wallet_summary_integrity.WalletSummaryIntegrityTests']
    if phase == 'after':
        names.append('tests_python.test_wallet_summary.WalletSummaryTests')
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    output = io.StringIO()
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    assert hashes == {name: digest(name) for name in hashes}, 'Source changed during capture'
    report = dict(observed_at_utc=datetime.now(timezone.utc).isoformat(), phase=phase,
                  scope='Eleven new summary integrity/state methods; final run adds twelve existing controls because their shared fixture now models the current profile and one extra weight getter.',
                  command=[sys.executable, '-X', 'utf8', str(Path(__file__).relative_to(ROOT)), phase],
                  selection=names, tests_run=result.testsRun,
                  failures=[(str(t), error) for t, error in result.failures],
                  errors=[(str(t), error) for t, error in result.errors], successful=result.wasSuccessful(),
                  elapsed_seconds=round(time.monotonic() - started, 3), source_sha256=hashes,
                  sources_unchanged=True,
                  repeated_initial_five_methods_not_additional_coverage=True)
    prefix.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    prefix.with_suffix('.log').write_text(output.getvalue(), encoding='utf-8', newline='\n')
    print(json.dumps({key: report[key] for key in ('phase', 'tests_run', 'successful', 'elapsed_seconds')}))


if __name__ == '__main__':
    main()
