"""One frozen affected-backend sweep, excluding imported TestCase duplicates.

No live RPC, signing, services, or local-chain state. The originally dirty
frontend-history module supplies imported fixtures only, never selected tests.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
TARGET = Path(__file__).parent
sys.path.insert(0, str(ROOT))

MODULES = (
    'test_frontend_api', 'test_royalty_reporting',
    'test_native_royalty_custody_reporting', 'test_earnings',
    'test_wallet_earnings', 'test_collection', 'test_wallet_summary',
    'test_current_fee_integrity', 'test_wallet_summary_integrity',
    'test_lp_fee_conservation',
)
CHANGED_BACKEND = (
    'frontend_api/earnings.py', 'frontend_api/earnings_replay.py',
    'frontend_api/portfolio.py', 'frontend_api/service.py',
    'frontend_api/wallet_earnings.py',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


class Results(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.methods = []
        self.active = None

    def startTest(self, test):
        super().startTest(test)
        self.active = {'id': test.id(), 'status': 'running', 'subtests': []}
        self.started = time.monotonic()

    def stopTest(self, test):
        self.active['elapsed_seconds'] = round(time.monotonic() - self.started, 6)
        if self.active['status'] == 'running':
            self.active['status'] = 'passed'
        self.methods.append(self.active)
        super().stopTest(test)

    def addSuccess(self, test):
        self.active['status'] = 'passed'
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.active['status'] = 'failed'
        self.active['detail'] = self._exc_info_to_string(err, test)
        super().addFailure(test, err)

    def addError(self, test, err):
        self.active['status'] = 'error'
        self.active['detail'] = self._exc_info_to_string(err, test)
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.active['status'] = 'skipped'
        self.active['reason'] = reason
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.active['status'] = 'expected_failure'
        self.active['detail'] = self._exc_info_to_string(err, test)
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.active['status'] = 'unexpected_success'
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        item = {'id': subtest.id(), 'status': 'passed' if err is None else 'failed'}
        if err is not None:
            item['detail'] = self._exc_info_to_string(err, subtest)
            self.active['status'] = 'failed'
        self.active['subtests'].append(item)
        super().addSubTest(test, subtest, err)


def main():
    report_path = TARGET / 'affected-suite.json'
    log_path = TARGET / 'affected-suite.log'
    if report_path.exists() or log_path.exists():
        raise RuntimeError('Preserve the recorded attempt; do not overwrite affected-suite evidence')
    classes = []
    methods = {}
    for name in MODULES:
        module = importlib.import_module('tests_python.' + name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__ or not issubclass(cls, unittest.TestCase):
                continue
            classes.append(cls.__module__ + '.' + cls.__qualname__)
            for case in flatten(unittest.defaultTestLoader.loadTestsFromTestCase(cls)):
                if case.id() in methods:
                    raise RuntimeError('Duplicate selected method: ' + case.id())
                methods[case.id()] = case
    if not methods or any(i.startswith('tests_python.test_frontend_history.') for i in methods):
        raise RuntimeError('Incorrect affected-method selection')

    # Capture the full read-only implementation closure, and the actual loaded
    # fixture files, before execution. Dynamic implementation imports cannot
    # evade the before/after binding by loading later during a selected test.
    paths = {str(p.relative_to(ROOT)).replace('\\', '/')
             for folder in ('frontend_api', 'zzz_ops') for p in (ROOT / folder).rglob('*.py')}
    imported_fixtures = set()
    for name, module in list(sys.modules.items()):
        if name.startswith('tests_python.') and getattr(module, '__file__', None):
            path = Path(module.__file__).resolve()
            if path.suffix == '.py' and path.is_relative_to(ROOT):
                imported_fixtures.add(path.relative_to(ROOT).as_posix())
    paths |= imported_fixtures | set(CHANGED_BACKEND)
    paths.add(Path(__file__).relative_to(ROOT).as_posix())
    paths = sorted(paths)
    before = {path: digest(ROOT / path) for path in paths}
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    with log_path.open('x', encoding='utf-8', newline='\n') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Results).run(
            unittest.TestSuite(methods[i] for i in sorted(methods)))
    after = {path: digest(ROOT / path) for path in paths}
    changed = [path for path in paths if before[path] != after[path]]
    report = {
        'schema': 1,
        'observed_at_utc': started_at,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'One final affected Python sweep for five changed backend modules; no Solidity or whole-Python regression, live RPC, signing, services or local-chain actions.',
        'selection': {'modules': ['tests_python.' + name for name in MODULES],
                      'defined_test_classes_only': True, 'classes': sorted(classes),
                      'deduplicated_method_ids': sorted(methods),
                      'original_dirty_frontend_history_tests_excluded': True,
                      'imported_fixture_paths': sorted(imported_fixtures)},
        'source_sha256_before': before,
        'source_sha256_after': after,
        'source_changes_during_run': changed,
        'sources_unchanged': not changed,
        'tests_run': result.testsRun,
        'methods': result.methods,
        'failures': [{'id': test.id(), 'detail': detail} for test, detail in result.failures],
        'errors': [{'id': test.id(), 'detail': detail} for test, detail in result.errors],
        'skips': [{'id': test.id(), 'reason': reason} for test, reason in result.skipped],
        'successful': result.wasSuccessful() and not changed,
        'elapsed_seconds': round(time.monotonic() - start, 3),
    }
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: report[key] for key in
                     ('tests_run', 'successful', 'sources_unchanged', 'elapsed_seconds')}))
    if not report['successful']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
