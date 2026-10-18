"""Observe expired-preparation work using synthetic RPC; no network or wallet."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-root', required=True, type=Path,
                    help='Isolated git archive of 485a089; avoid mixed local drafts')
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
root = args.source_root.resolve()
scope = json.loads(Path(__file__).with_name('scope.json').read_text(encoding='utf-8'))
for name, expected in scope['files'].items():
    if name.endswith('.py'):
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
sys.path.insert(0, str(root))
from tests_python.test_frontend_activation import ActivationRPC, configuration, Projection, ActivationTransactions
from frontend_api.service import ProjectionError

rpc = ActivationRPC()
now = [1000]
projection = Projection(configuration(), rpc, clock=lambda: now[0])
service = ActivationTransactions(projection, rpc.config)
original = rpc.call
after = []
expired = [False]

def call(method, params):
    if expired[0]:
        after.append(method)
    value = original(method, params)
    if method == 'eth_getCode' and not expired[0]:
        now[0] = 2000
        expired[0] = True
    return value

rpc.call = call
try:
    service.prepare(rpc.request)
except ProjectionError as exc:
    assert 'stale' in str(exc).lower() or 'expired' in str(exc).lower(), str(exc)
    assert len(after) == 134 and rpc.trace_count == 2, (len(after), rpc.trace_count)
    result = {
        'published_head': scope['head'],
        'scenario': 'Synthetic clock expires after first pinned code read; published preparer with synthetic RPC fixture',
        'returned_unsigned_transaction': False,
        'final_error': str(exc),
        'rpc_calls_after_expiry': len(after),
        'methods_after_expiry': dict(Counter(after)),
        'trace_calls': rpc.trace_count,
        'limitations': 'No network delay, HTTP load test or public service exercised. Demonstrates late detection and continued work after expiry only.',
    }
else:
    raise AssertionError('Expired snapshot unexpectedly returned a draft')

bindings = {}
for module in list(sys.modules.values()):
    path = getattr(module, '__file__', None)
    if path:
        path = Path(path).resolve()
        if path.is_relative_to(root) and path.is_file():
            bindings[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
result['loaded_repository_modules'] = dict(sorted(bindings.items()))
result['reproducer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'loaded_repository_modules'}))
