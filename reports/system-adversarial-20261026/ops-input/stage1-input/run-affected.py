"""Affected holder inventory fixtures, selected by defined class exactly once."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib, inspect, io, json, sys, time, unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
TARGET = Path(__file__).parent
MODULES = ('tests_python.test_holder_preflight', 'tests_python.test_holder_inventory_input')
FILES = ('scripts/inventory-nft-holders.py', 'tests_python/test_holder_inventory_input.py',
         'tests_python/test_holder_preflight.py', 'zzz_ops/holder_preflight.py',
         'zzz_ops/abi.py', 'zzz_ops/work_budget.py', 'zzz_ops/errors.py', 'zzz_ops/rpc.py')


def pins():
    paths = [ROOT / name for name in FILES] + [Path(__file__)]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    tests = {}
    for name in MODULES:
        module = importlib.import_module(name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if not issubclass(cls, unittest.TestCase) or cls.__module__ != module.__name__:
                continue
            for method in unittest.defaultTestLoader.getTestCaseNames(cls):
                item = cls(method)
                assert item.id() not in tests
                tests[item.id()] = item
    before = pins(); stream = io.StringIO(); start = time.monotonic()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite(tests.values()))
    after = pins()
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Affected holder-inventory unit/temp-file/CLI fixtures only; no wallet, actual RPC, service or installed state.',
        'selected_methods': list(tests), 'tests_run': result.testsRun,
        'failures': [(c.id(), d) for c, d in result.failures],
        'errors': [(c.id(), d) for c, d in result.errors],
        'skips': [(c.id(), d) for c, d in result.skipped],
        'source_sha256_before': before, 'source_sha256_after': after,
        'source_changes_during_run': changed,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        'successful': result.wasSuccessful() and not changed and result.testsRun == len(tests),
        'new_methods_in_scope': 8, 'new_tests_unchanged_since_negative_control':
            before['tests_python/test_holder_inventory_input.py'] == json.loads((TARGET / 'before.json').read_text())['source_sha256']['tests_python/test_holder_inventory_input.py'],
        'production_approved': False}
    (TARGET / 'after.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    (TARGET / 'after.log').write_text(stream.getvalue(), encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ('tests_run', 'successful', 'elapsed_seconds', 'source_changes_during_run', 'new_tests_unchanged_since_negative_control')}))
    raise SystemExit(0 if report['successful'] and report['new_tests_unchanged_since_negative_control'] else 1)


if __name__ == '__main__':
    main()
