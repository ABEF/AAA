"""Only two existing controls affected by current activation/ABI-reader fixes."""
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
names = [
    'tests_python.test_entry_review_policy.EntryReviewPolicyTests.test_explicit_legacy_profile_keeps_its_original_selector_and_response_shape',
    'tests_python.test_native_backend_boundary.NativeBackendBoundaryTests.test_zero_is_a_typed_currency_never_a_contract_target_or_owner',
]
files = ['frontend_api/activation.py', 'frontend_api/service.py',
         'tests_python/test_entry_review_policy.py', 'tests_python/test_native_backend_boundary.py']
hashes = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in files}
stream = io.StringIO()
start = time.monotonic()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromNames(names))
report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Two existing directly affected historical-profile and zero-address ABI controls, rerun because activation.py/service.py changed. Synthetic offline RPC only.',
    'selected_methods': names, 'tests_run': result.testsRun,
    'failures': [{'test': str(t), 'trace': trace} for t, trace in result.failures],
    'errors': [{'test': str(t), 'trace': trace} for t, trace in result.errors],
    'successful': result.wasSuccessful(), 'elapsed_seconds': round(time.monotonic() - start, 3),
    'source_sha256': hashes,
    'sources_unchanged': all(hashlib.sha256((ROOT / n).read_bytes()).hexdigest() == h for n, h in hashes.items())}
folder = ROOT / 'reports/full-audit-20261025'
(folder / 'services-compatibility.log').write_text(stream.getvalue(), encoding='utf-8', newline='\n')
(folder / 'services-compatibility.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({k: v for k, v in report.items() if k not in ('failures', 'errors')}))
raise SystemExit(not result.wasSuccessful())
