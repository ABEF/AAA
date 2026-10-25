"""Capture focused offline current-profile preparation regressions; no RPC or signing."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import io
import json
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
phase = sys.argv[1]
if phase not in ('before', 'after'):
    raise SystemExit('Use before or after')
names = [
    'test_current_dormant_activation_new_pool_and_active_growth_prepare',
    'test_current_zzz_requires_only_exact_approval_before_fresh_review',
    'test_current_native_policy_getter_is_typed_and_other_zero_uses_stay_rejected',
    'test_explicit_historical_profile_keeps_old_dormant_value_and_native_preparation',
    'test_dormant_codes_cannot_be_mixed_between_profiles_and_nonactive_growth_is_rejected',
]
files = ['frontend_api/activation.py', 'frontend_api/service.py',
         'tests_python/test_current_activation_profile.py']
hashes = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in files}
suite = unittest.defaultTestLoader.loadTestsFromNames([
    'tests_python.test_current_activation_profile.CurrentActivationProfileTests.' + n for n in names])
stream = io.StringIO()
start = time.monotonic()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'phase': phase,
    'scope': 'Five new offline current/historical profile composition methods; synthetic byte-level traces, no live service or Solidity execution.',
    'selected_methods': names, 'tests_run': result.testsRun,
    'failures': [{'test': str(t), 'trace': trace} for t, trace in result.failures],
    'errors': [{'test': str(t), 'trace': trace} for t, trace in result.errors],
    'skips': result.skipped, 'successful': result.wasSuccessful(),
    'elapsed_seconds': round(time.monotonic() - start, 3),
    'source_sha256': hashes,
    'sources_unchanged': all(hashlib.sha256((ROOT / n).read_bytes()).hexdigest() == h for n, h in hashes.items())}
folder = ROOT / 'reports/full-audit-20261025'
(folder / f'activation-profile-{phase}.log').write_text(stream.getvalue(), encoding='utf-8', newline='\n')
(folder / f'activation-profile-{phase}.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({k: v for k, v in report.items() if k not in ('failures', 'errors')} | {
    'failure_count': len(result.failures), 'error_count': len(result.errors)}))
raise SystemExit(not result.wasSuccessful())
