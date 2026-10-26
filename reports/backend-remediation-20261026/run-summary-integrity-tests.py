"""Capture only five new wallet-summary integrity methods; no live services."""
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
    source = 'frontend_api/portfolio.py'
    test = 'tests_python/test_wallet_summary_integrity.py'
    hashes = {name: digest(name) for name in (source, test, 'tests_python/test_wallet_summary.py')}
    label = 'tests_python.test_wallet_summary_integrity.WalletSummaryIntegrityTests'
    suite = unittest.defaultTestLoader.loadTestsFromName(label)
    output = io.StringIO()
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    assert hashes == {name: digest(name) for name in hashes}, 'Source changed during capture'
    report = dict(observed_at_utc=datetime.now(timezone.utc).isoformat(), phase=phase,
                  scope='Five new wallet-summary integrity methods only; deterministic snapshot/ABI fixture, no network or service.',
                  command=[sys.executable, '-X', 'utf8', str(Path(__file__).relative_to(ROOT)), phase],
                  tests_run=result.testsRun, failures=[(str(t), error) for t, error in result.failures],
                  errors=[(str(t), error) for t, error in result.errors],
                  successful=result.wasSuccessful(), elapsed_seconds=round(time.monotonic() - started, 3),
                  source_sha256=hashes, sources_unchanged=True)
    prefix = TARGET / ('summary-integrity-' + phase)
    prefix.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    prefix.with_suffix('.log').write_text(output.getvalue(), encoding='utf-8', newline='\n')
    print(json.dumps({key: report[key] for key in ('phase', 'tests_run', 'successful', 'elapsed_seconds')},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
