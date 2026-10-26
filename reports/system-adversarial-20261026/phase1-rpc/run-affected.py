"""Defined-class, deduplicated actual RPC / budget / history adapter fixtures.

No real provider, signer, installed Anvil or operating service is contacted.
Reuses the maintained runner's source pinning, not its keeper test selection.
"""
from pathlib import Path
from datetime import datetime, timezone
import importlib, importlib.util, inspect, io, json, sys, time, unittest

ROOT = Path(__file__).resolve().parents[2]
TARGET = Path(__file__).parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('pin_helpers', ROOT / 'scripts/run-keeper-tests.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
MODULES = ('test_rpc_integrity', 'test_rpc', 'test_request_limits', 'test_history_audit_transport')


def pins():
    return {**base.inputs(), Path(__file__).relative_to(ROOT).as_posix(): base.sha(Path(__file__))}


def main():
    tests = {}; classes = []
    for name in MODULES:
        module = importlib.import_module('tests_python.' + name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if not issubclass(cls, unittest.TestCase) or cls.__module__ != module.__name__: continue
            classes.append(cls.__module__ + '.' + cls.__name__)
            for method in unittest.defaultTestLoader.getTestCaseNames(cls):
                item = cls(method); assert item.id() not in tests
                tests[item.id()] = item
    before = pins(); started = time.monotonic(); stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=base.Results).run(unittest.TestSuite(tests.values()))
    after = pins(); changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Actual read RPC integrity, retry/budget and history-adapter fixtures; not provider or operating qualification.',
        'modules': list(MODULES), 'classes': classes, 'selected_methods': list(tests),
        'executed_methods': result.methods, 'tests_run': result.testsRun,
        'failures': [(case.id(), detail) for case, detail in result.failures],
        'errors': [(case.id(), detail) for case, detail in result.errors],
        'skips': [(case.id(), reason) for case, reason in result.skipped],
        'source_sha256_before': before, 'source_sha256_after': after, 'source_changes_during_run': changed,
        'elapsed_seconds': round(time.monotonic() - started, 3), 'production_approved': False,
        'successful': result.wasSuccessful() and not changed and result.testsRun == len(tests)}
    (TARGET / 'affected-suite.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    (TARGET / 'affected-suite.log').write_text(stream.getvalue(), encoding='utf-8', newline='\n')
    print(json.dumps({name: report[name] for name in ('tests_run', 'successful', 'elapsed_seconds', 'source_changes_during_run')}))
    print(json.dumps({'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped)}))
    raise SystemExit(0 if report['successful'] else 1)


if __name__ == '__main__': main()
