"""Record only the reserved-None keeper regression and its exact source scope."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
SOURCES = (
    'keeper/__init__.py', 'keeper/monitor.py', 'zzz_ops/__init__.py',
    'zzz_ops/abi.py', 'zzz_ops/rpc.py', 'zzz_ops/state.py',
    'tests_python/__init__.py', 'tests_python/test_keeper.py',
    'tests_python/test_keeper_reservations.py',
    'reports/architecture-evolution/keeper/run_targeted.py',
)


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


if __name__ == '__main__':
    before = hashes()
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.loadTestsFromName('tests_python.test_keeper_reservations')
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    after = hashes()
    log = stream.getvalue()
    (OUTPUT / 'tests.log').write_text(log, encoding='utf-8', newline='\n')
    receipt = {
        'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'command': ['python', 'reports/architecture-evolution/keeper/run_targeted.py'],
        'python': platform.python_version(),
        'scope': 'Targeted static-ABI mock RPC reserved-None discovery; not an on-chain or live operating rehearsal.',
        'tests_run': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skipped': len(result.skipped),
        'successful': result.wasSuccessful() and before == after,
        'source_hash_normalization': 'Raw local bytes; before/after equality is exact.',
        'source_sha256_before': before, 'source_sha256_after': after,
        'source_unchanged': before == after,
        'log_sha256': hashlib.sha256((OUTPUT / 'tests.log').read_bytes()).hexdigest(),
        'keeper_source_changed': False, 'live_signing': False,
        'public_transactions': False, 'production_approved': False,
        'limitations': [
            'Reserved state is a 15-word zero-valued Position ABI fixture; no contract deployment is executed.',
            'Keeper view/group decoding, cursor persistence and health output are real; transaction submission is mocked.',
            'Unix advisory locking, real venues, production services and full keeper suites are outside this run.',
        ],
    }
    (OUTPUT / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(log, end='')
    print(json.dumps({key: receipt[key] for key in ('tests_run', 'failures', 'errors', 'skipped', 'source_unchanged', 'successful')}))
    sys.exit(not receipt['successful'])
