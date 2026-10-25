"""Capture offline Rpc-to-history-audit composition before/after a narrow fix."""
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
    'test_actual_rpc_checked_integer_chain_id_can_complete_read_only_audit',
    'test_canonical_wire_quantity_injected_adapter_remains_supported',
    'test_boolean_float_wrong_or_noncanonical_chain_ids_fail_without_database_changes',
    'test_actual_transport_wrong_network_stays_fail_closed_before_history',
]
files = ['frontend_api/history_audit.py', 'zzz_ops/rpc.py', 'tests_python/test_history_audit_transport.py']
hashes = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in files}
suite = unittest.defaultTestLoader.loadTestsFromNames([
    'tests_python.test_history_audit_transport.HistoryAuditTransportTests.' + n for n in names])
stream = io.StringIO()
start = time.monotonic()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'phase': phase,
    'scope': 'Four new offline transport/SQLite history-audit methods, using real Rpc.call with HTTP replaced by a fixture. No public RPC, signing or existing database writes.',
    'selected_methods': names, 'tests_run': result.testsRun,
    'failures': [{'test': str(t), 'trace': trace} for t, trace in result.failures],
    'errors': [{'test': str(t), 'trace': trace} for t, trace in result.errors],
    'skips': result.skipped, 'successful': result.wasSuccessful(),
    'elapsed_seconds': round(time.monotonic() - start, 3), 'source_sha256': hashes,
    'sources_unchanged': all(hashlib.sha256((ROOT / n).read_bytes()).hexdigest() == h for n, h in hashes.items())}
folder = ROOT / 'reports/full-audit-20261025'
(folder / f'history-transport-{phase}.log').write_text(stream.getvalue(), encoding='utf-8', newline='\n')
(folder / f'history-transport-{phase}.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({k: v for k, v in report.items() if k not in ('failures', 'errors')} | {
    'failure_count': len(result.failures), 'error_count': len(result.errors)}))
raise SystemExit(not result.wasSuccessful())
