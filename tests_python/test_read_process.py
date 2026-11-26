"""NEW portable utility-boundary cases; disposable Python children only.

No SSH, monitoring activation, key, chain, signer or old test method runs.
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

from zzz_ops import read_process as capture


class ReadProcessTests(unittest.TestCase):
    marker = 'PRIVATE-ARGV-DO-NOT-LOG'

    def invoke(self, code, timeout=3):
        return capture.run_read_process([sys.executable, '-c', code, self.marker], timeout=timeout)

    def refuse(self, code, timeout=3):
        with self.assertRaises(capture.ReadProcessError) as caught:
            self.invoke(code, timeout)
        error = caught.exception
        for marker in (self.marker, 'PRIVATE-CHILD-OUTPUT'):
            self.assertNotIn(marker, str(error))
            self.assertNotIn(marker, repr(error.args))
        for name in ('cmd', 'stdout', 'stderr', 'output'):
            self.assertFalse(hasattr(error, name), name)
        return error

    def test_complete_bytes_nonzero_exit_and_closed_stdin(self):
        result = self.invoke("import os,sys;assert sys.stdin.buffer.read()==b'';os.write(1,b'raw\\xff\\r\\n');os.write(2,b'warn');raise SystemExit(7)")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (7, b'raw\xff\r\n', b'warn'))
        self.assertEqual(result.args, 'read-only process')

    def test_exact_combined_mebibyte_is_retained(self):
        half = capture.MAX_OUTPUT_BYTES // 2
        result = self.invoke(f"import os;os.write(1,b'a'*{half});os.write(2,b'b'*{half})")
        self.assertEqual(capture.MAX_OUTPUT_BYTES, 1048576)
        self.assertEqual((len(result.stdout), len(result.stderr)), (half, half))

    def test_each_stream_and_combined_overflow_refuse_without_partial_result(self):
        maximum = capture.MAX_OUTPUT_BYTES
        for stdout, stderr in ((maximum + 1, 0), (0, maximum + 1),
                               (maximum // 2, maximum // 2 + 1)):
            with self.subTest(stdout=stdout, stderr=stderr):
                self.refuse(f"import os;os.write(1,b'a'*{stdout});os.write(2,b'b'*{stderr});os.write(1,b'PRIVATE-CHILD-OUTPUT')")

    def test_one_deadline_bounds_idle_active_and_closed_pipes(self):
        codes = ("import time;time.sleep(30)",
                 "import os,time\nwhile True:os.write(1,b'x');time.sleep(.005)",
                 "import os,time;os.close(1);os.close(2);time.sleep(30)")
        for code in codes:
            with self.subTest(code=code):
                started = time.monotonic()
                self.refuse(code, timeout=.3)
                self.assertLess(time.monotonic() - started, 3)

    def test_failure_reaps_child_closes_pipes_and_never_uses_shell(self):
        original = subprocess.Popen
        children = []
        def spawn(*args, **kwargs):
            self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
            self.assertNotIn('shell', kwargs)
            self.assertTrue(kwargs['close_fds'])
            child = original(*args, **kwargs)
            children.append(child)
            return child
        with patch.object(capture.subprocess, 'Popen', side_effect=spawn):
            self.refuse("import os,time;os.write(2,b'z'*1048577);time.sleep(30)")
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].returncode)
        self.assertTrue(children[0].stdout.closed)
        self.assertTrue(children[0].stderr.closed)

    def test_invalid_deadlines_and_startup_error_do_not_disclose_arguments(self):
        for timeout in (True, 0, -1, float('nan'), float('inf'), '30'):
            with self.subTest(timeout=timeout), patch.object(capture.subprocess, 'Popen') as spawn:
                with self.assertRaises(ValueError):
                    capture.run_read_process([self.marker], timeout=timeout)
                spawn.assert_not_called()
        with patch.object(capture.subprocess, 'Popen', side_effect=OSError(self.marker)):
            self.refuse('unused')

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux inherited-pipe lifecycle proof')
    def test_exited_parent_cannot_strand_a_unix_inherited_pipe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'child.pid'
            code = ("import os,sys,time\nfrom pathlib import Path\npid=os.fork()\n"
                    "if pid==0:time.sleep(30);os._exit(0)\n"
                    "Path(sys.argv[1]).write_text(str(pid));os._exit(0)")
            def alive(pid):
                try:
                    state = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()[0]
                except FileNotFoundError:
                    return False
                return state not in ('Z', 'X')
            pid = None
            try:
                started = time.monotonic()
                with self.assertRaises(capture.ReadProcessError):
                    capture.run_read_process([sys.executable, '-c', code, str(path)], timeout=.5)
                self.assertLess(time.monotonic() - started, 3)
                pid = int(path.read_text())
                deadline = time.monotonic() + 2
                while alive(pid) and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertFalse(alive(pid), 'Inherited-pipe child survived failed capture')
            finally:
                if pid is None and path.exists():
                    pid = int(path.read_text())
                if pid is not None and alive(pid):
                    os.kill(pid, signal.SIGKILL)

