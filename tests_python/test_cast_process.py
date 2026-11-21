"""New Unix capture-boundary checks using disposable Python children only.

No Cast binary, wallet, key, chain, RPC, service or unchanged test method runs.
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from keeper import cast_process as capture


@unittest.skipUnless(os.name == 'posix', 'Live Cast capture requires Unix pipes')
class CastProcessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='popl-capture-case-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.marker = 'DO-NOT-LOG-CAST-ARGUMENT'
        self.environment = {'PATH': os.defpath, 'LANG': 'C.UTF-8',
                            'PYTHONIOENCODING': 'utf-8',
                            'CAPTURE_CANARY': 'DO-NOT-LOG-CAST-ENVIRONMENT'}

    def command(self, code, *args):
        return [sys.executable, '-c', code, *map(str, args), self.marker]

    def invoke(self, code, *, timeout=2, args=()):
        return capture.run_cast(self.command(code, *args), env=self.environment,
                                timeout=timeout)

    def refused(self, code, *, timeout=2, args=()):
        with self.assertRaises(RuntimeError) as error:
            self.invoke(code, timeout=timeout, args=args)
        message = str(error.exception)
        for value in (self.marker, self.environment['CAPTURE_CANARY'],
                      'DO-NOT-LOG-CHILD-OUTPUT'):
            self.assertNotIn(value, message)
            self.assertNotIn(value, repr(error.exception.args))
        for name in ('cmd', 'stdout', 'stderr', 'output'):
            self.assertFalse(hasattr(error.exception, name), name)
        return error.exception

    def expired(self, code, *, timeout, args=()):
        with self.assertRaises(subprocess.TimeoutExpired) as error:
            self.invoke(code, timeout=timeout, args=args)
        self.assertEqual(error.exception.cmd, 'Cast')
        self.assertEqual(error.exception.timeout, timeout)
        self.assertIsNone(error.exception.output)
        self.assertIsNone(error.exception.stderr)
        for marker in (self.marker, self.environment['CAPTURE_CANARY']):
            self.assertNotIn(marker, str(error.exception))
            self.assertNotIn(marker, repr(error.exception.args))
        return error.exception

    def test_successful_text_and_nonzero_exit_are_preserved(self):
        result = self.invoke("import os;os.write(1,b'address\\r\\n');os.write(2,b'warning\\r');raise SystemExit(7)")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout, 'address\n')
        self.assertEqual(result.stderr, 'warning\n')

    def test_exact_aggregate_byte_budget_is_admitted(self):
        self.assertEqual(capture.MAX_OUTPUT_BYTES, 65536)
        half = capture.MAX_OUTPUT_BYTES // 2
        result = self.invoke(f"import os;os.write(1,b'a'*{half});os.write(2,b'b'*{half})")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'a' * half)
        self.assertEqual(result.stderr, 'b' * half)

    def test_stdout_stderr_and_split_overflow_are_refused_without_disclosure(self):
        limit = capture.MAX_OUTPUT_BYTES
        for stdout, stderr in ((limit + 1, 0), (0, limit + 1), (limit // 2, limit // 2 + 1)):
            with self.subTest(stdout=stdout, stderr=stderr):
                code = (f"import os;os.write(1,b'x'*{stdout});os.write(2,b'y'*{stderr});"
                        "os.write(2,b'DO-NOT-LOG-CHILD-OUTPUT')")
                self.refused(code)
        # A plausible successful hash is not publishable when stderr overruns.
        self.refused("import os;os.write(1,b'0x'+b'b'*64);os.write(2,b'y'*65536)")

    def test_invalid_utf8_cannot_return_a_partial_valid_hash(self):
        self.refused("import os;os.write(1,b'0x'+b'b'*64+b'\\xff')")
        self.refused("import os;os.write(1,b'0x'+b'b'*64);os.write(2,b'\\xff')")

    def test_deadline_covers_idle_active_and_closed_pipes(self):
        cases = (
            "import time;time.sleep(30)",
            "import os,time\nwhile True:os.write(1,b'x');time.sleep(.005)",
            "import os,time;os.close(1);os.close(2);time.sleep(30)",
        )
        for code in cases:
            with self.subTest(code=code):
                started = time.monotonic()
                self.expired(code, timeout=0.3)
                self.assertLess(time.monotonic() - started, 4)

    @staticmethod
    def alive(pid):
        try:
            fields = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()
        except FileNotFoundError:
            return False
        return fields[0] not in ('Z', 'X')

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux proc/fork child lifecycle proof')
    def test_exited_parent_cannot_leave_inherited_pipe_descendant_running(self):
        pid_file = self.root / 'descendant.pid'
        code = ("import os,sys,time\nfrom pathlib import Path\npid=os.fork()\n"
                "if pid==0:time.sleep(30);os._exit(0)\n"
                "Path(sys.argv[1]).write_text(str(pid));os._exit(0)")
        child = None
        try:
            started = time.monotonic()
            self.expired(code, timeout=0.5, args=(pid_file,))
            self.assertLess(time.monotonic() - started, 4)
            child = int(pid_file.read_text())
            self.assertGreater(child, 1)
            deadline = time.monotonic() + 2
            while self.alive(child) and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertFalse(self.alive(child), 'Inherited-pipe descendant survived failed capture')
        finally:
            if child is None and pid_file.exists():
                child = int(pid_file.read_text())
            if child is not None and self.alive(child):
                os.kill(child, signal.SIGKILL)

    def test_failure_reaps_direct_child_and_closes_both_pipes(self):
        original = subprocess.Popen
        children = []
        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            children.append(child)
            return child
        with patch.object(capture.subprocess, 'Popen', side_effect=spawn):
            self.refused("import os,time;os.write(1,b'x'*70000);time.sleep(30)")
        self.assertEqual(len(children), 1)
        child = children[0]
        self.assertIsNotNone(child.returncode)
        self.assertTrue(child.stdout.closed)
        self.assertTrue(child.stderr.closed)
        with self.assertRaises(ChildProcessError):
            os.waitpid(child.pid, os.WNOHANG)

    def test_interrupted_pipe_wait_reaps_child_and_preserves_interrupt(self):
        original = subprocess.Popen
        children = []
        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            children.append(child)
            return child
        with patch.object(capture.subprocess, 'Popen', side_effect=spawn), \
                patch.object(capture.selectors.DefaultSelector, 'select', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.invoke("import time;time.sleep(30)")
        self.assertEqual(len(children), 1)
        child = children[0]
        self.assertIsNotNone(child.returncode)
        self.assertTrue(child.stdout.closed)
        self.assertTrue(child.stderr.closed)


if __name__ == '__main__':
    unittest.main()
