"""Exact NEW scheduling methods in an isolated nobody-owned process."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import resource
import signal
import stat
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parent
RUNTIME = Path('/opt/popl-keeper-sidecar-recovery-20261126-c821/runtime')
METHODS = __METHODS__


def publish(name, value):
    assert name in ('FOCUSED_PROGRESS.json', 'FOCUSED_RESULT.json')
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    assert len(raw) <= 32768
    temporary = RUNTIME / (name + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, RUNTIME / name)
    directory = os.open(RUNTIME, os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class BoundedStream:
    def __init__(self):
        self.raw = bytearray()

    def write(self, value):
        raw = value.encode()
        assert len(self.raw) + len(raw) <= 16384
        self.raw.extend(raw)

    def flush(self):
        pass


class TrackedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []
        self.finished = []
        self.outcomes = {}

    def progress(self):
        publish('FOCUSED_PROGRESS.json', {'schema': 1, 'selected_methods': list(METHODS),
            'started': self.started, 'finished': self.finished, 'outcomes': self.outcomes,
            'old_test_bodies_run': 0})

    def startTest(self, case):
        name = case._testMethodName
        assert name in METHODS and name not in self.started
        self.started.append(name)
        self.outcomes[name] = 'entered'
        self.progress()
        super().startTest(case)

    def stopTest(self, case):
        self.finished.append(case._testMethodName)
        self.progress()
        super().stopTest(case)

    def addSuccess(self, case):
        self.outcomes[case._testMethodName] = 'passed'
        super().addSuccess(case)

    def addFailure(self, case, err):
        self.outcomes[case._testMethodName] = 'failed'
        super().addFailure(case, err)

    def addError(self, case, err):
        self.outcomes[case._testMethodName] = 'error'
        super().addError(case, err)

    def addSubTest(self, case, subtest, err):
        if err is not None:
            self.outcomes[case._testMethodName] = 'failed_subtest'
        super().addSubTest(case, subtest, err)


def main():
    assert os.getuid() == os.getgid() == 65534 and set(os.getgroups()) <= {65534}
    assert resource.getrlimit(resource.RLIMIT_FSIZE) == (65536, 65536)
    mask_stats = [(RUNTIME/'working'/name).lstat() for name in ('keystore.secret', 'password.secret')]
    assert all(stat.S_ISREG(st.st_mode) and st.st_uid == 0 and stat.S_IMODE(st.st_mode) == 0 and
        st.st_size == 0 and st.st_nlink == 1 for st in mask_stats)
    assert len({(st.st_dev, st.st_ino) for st in mask_stats}) == 2
    denied = 0
    for name in ('keystore.secret', 'password.secret'):
        try:
            fd = os.open(RUNTIME/'working'/name, os.O_RDONLY | os.O_NOFOLLOW)
        except PermissionError:
            denied += 1
        else:
            os.close(fd)
            raise AssertionError('Masked disposable signer path was readable')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location('c821_new_scheduling', ROOT / 'tests_python/test_keeper_sidecar_recovery.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = module.KeeperSidecarRecoveryTests
    assert set(METHODS) == {name for name, member in cls.__dict__.items() if name.startswith('test_') and callable(member)}
    selected = [cls(name) for name in METHODS]
    stream = BoundedStream()
    started = time.monotonic()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2,
            resultclass=TrackedResult).run(unittest.TestSuite(selected))
    failed = {}
    locations = {}
    for case, detail in result.errors + result.failures:
        owner = getattr(case, 'test_case', case)
        name = owner._testMethodName
        failed[name] = hashlib.sha256(detail.encode()).hexdigest()
        # Test diagnostics contain synthetic configuration markers, so expose
        # only digests and the terminal fixed traceback line, never raw text.
        locations[name] = detail.splitlines()[-1].split(':', 1)[0][:80]
    success = result.wasSuccessful() and result.testsRun == len(METHODS) and not result.skipped and (
        result.started == list(METHODS) and result.finished == list(METHODS) and
        all(result.outcomes.get(name) == 'passed' for name in METHODS))
    value = {'schema': 1, 'success': bool(success), 'selected_methods': list(METHODS),
        'tests_run': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures),
        'skipped': len(result.skipped), 'error_digests': failed, 'error_types': locations,
        'diagnostic_bytes': len(stream.raw), 'diagnostic_sha256': hashlib.sha256(stream.raw).hexdigest(),
        'elapsed_seconds': time.monotonic()-started, 'uid': os.getuid(), 'gid': os.getgid(),
        'old_test_bodies_run': 0, 'fixture_helper_setup_only': True,
        'actual_masked_regular_paths': 2, 'actual_unreadable_distinct_empty_root_masks': denied == 2,
        'masked_dev_inode_pairs': [[st.st_dev, st.st_ino] for st in mask_stats],
        'public_transactions': 0, 'production_approved': False}
    value.update(method_outcomes=result.outcomes, started=result.started, finished=result.finished)
    publish('FOCUSED_RESULT.json', value)
    print(json.dumps({'new_focused_methods': result.testsRun, 'success': bool(success)}))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
