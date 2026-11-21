"""New Unix lock-admission checks; no keeper, signing, RPC, service or old suite."""
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

if os.name == 'posix':
    import fcntl

from zzz_ops import state


@unittest.skipUnless(os.name == 'posix', 'Unix advisory locking requires Unix')
class ProcessLockSafetyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='popl-lock-case-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / 'keeper.lock'

    def test_new_private_and_legacy_locks_keep_their_inode_and_bytes(self):
        with state.process_lock(self.path):
            self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
            inode = self.path.stat().st_ino
        self.assertEqual(self.path.stat().st_ino, inode)
        self.path.write_text('existing-lock-marker')
        self.path.chmod(0o644)
        with state.process_lock(self.path):
            self.assertEqual(self.path.read_text(), 'existing-lock-marker')
            self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o644)
            self.assertEqual(self.path.stat().st_ino, inode)
        self.assertEqual(self.path.read_text(), 'existing-lock-marker')

    def test_symlink_fifo_and_symlink_parent_are_refused_without_waiting(self):
        target = self.root / 'marker'
        target.write_text('unchanged')
        self.path.symlink_to(target)
        with self.assertRaises(OSError):
            with state.process_lock(self.path): self.fail('symlink admitted')
        self.assertEqual(target.read_text(), 'unchanged')
        self.assertTrue(self.path.is_symlink())
        self.path.unlink()
        os.mkfifo(self.path, 0o600)
        before = time.monotonic()
        with self.assertRaises(ValueError):
            with state.process_lock(self.path): self.fail('FIFO admitted')
        self.assertLess(time.monotonic() - before, 1)
        self.assertTrue(stat.S_ISFIFO(self.path.stat().st_mode))
        linked = self.root / 'linked-parent'
        real = self.root / 'real-parent'
        real.mkdir(mode=0o700)
        linked.symlink_to(real, target_is_directory=True)
        with self.assertRaises(OSError):
            with state.process_lock(linked / 'keeper.lock'): self.fail('parent symlink admitted')
        self.assertFalse((real / 'keeper.lock').exists())

    def test_unsafe_parent_or_lock_permissions_are_refused_without_repair(self):
        for mode in (0o770, 0o777):
            with self.subTest(parent_mode=mode):
                self.root.chmod(mode)
                with self.assertRaises(ValueError):
                    with state.process_lock(self.path): self.fail('unsafe parent admitted')
                self.assertFalse(self.path.exists())
        self.root.chmod(0o700)
        self.path.write_text('preserve')
        for mode in (0o620, 0o602):
            with self.subTest(file_mode=mode):
                self.path.chmod(mode)
                with self.assertRaises(ValueError):
                    with state.process_lock(self.path): self.fail('unsafe lock admitted')
                self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), mode)
                self.assertEqual(self.path.read_text(), 'preserve')

    def test_parent_and_lock_owner_checks_are_independent(self):
        original = os.fstat
        for wrong_type in ('directory', 'file'):
            def observed(descriptor, kind=wrong_type):
                result = original(descriptor)
                matches = stat.S_ISDIR(result.st_mode) if kind == 'directory' else stat.S_ISREG(result.st_mode)
                if not matches: return result
                values = {name: getattr(result, name) for name in ('st_mode', 'st_uid', 'st_dev', 'st_ino')}
                values['st_uid'] = os.getuid() + 10000
                return types.SimpleNamespace(**values)
            with self.subTest(owner=wrong_type), patch.object(state.os, 'fstat', side_effect=observed):
                with self.assertRaises(ValueError):
                    with state.process_lock(self.path): self.fail('unreviewed owner admitted')

    def test_changed_named_inode_is_refused_and_never_unlinked(self):
        original = fcntl.flock
        changed = []
        def acquire(descriptor, operation):
            if operation & fcntl.LOCK_EX and not changed:
                changed.append(True)
                self.path.unlink()
                self.path.write_text('replacement')
            return original(descriptor, operation)
        with patch.object(fcntl, 'flock', side_effect=acquire):
            with self.assertRaisesRegex(RuntimeError, 'path changed'):
                with state.process_lock(self.path): self.fail('replacement admitted')
        self.assertEqual(self.path.read_text(), 'replacement')
        with state.process_lock(self.path):
            self.assertEqual(self.path.read_text(), 'replacement')

    def test_descriptor_is_nonblocking_and_not_inherited_on_exec(self):
        original = fcntl.flock
        seen = []
        def acquire(descriptor, operation):
            if operation & fcntl.LOCK_EX:
                seen.append(descriptor)
                self.assertTrue(fcntl.fcntl(descriptor, fcntl.F_GETFD) & fcntl.FD_CLOEXEC)
                self.assertTrue(fcntl.fcntl(descriptor, fcntl.F_GETFL) & os.O_NONBLOCK)
            return original(descriptor, operation)
        with patch.object(fcntl, 'flock', side_effect=acquire), state.process_lock(self.path):
            self.assertEqual(len(seen), 1)

    def child_environment(self):
        environment = {'PATH': os.environ.get('PATH', ''), 'PYTHONPATH': str(Path(state.__file__).resolve().parents[1]),
                       'PYTHONDONTWRITEBYTECODE': '1'}
        return environment

    def test_separate_process_contender_cannot_enter_the_same_inode(self):
        script = ('import sys;from zzz_ops.state import process_lock\n'
                  'try:\n with process_lock(sys.argv[1]): print("incorrectly-entered")\n'
                  'except RuntimeError: print("contended")\n')
        with state.process_lock(self.path):
            inode = self.path.stat().st_ino
            result = subprocess.run([sys.executable, '-c', script, str(self.path)], env=self.child_environment(),
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'contended')
            self.assertEqual(self.path.stat().st_ino, inode)

    def test_process_death_releases_the_same_persistent_inode(self):
        script = ('import sys;from zzz_ops.state import process_lock\n'
                  'with process_lock(sys.argv[1]):\n print("held",flush=True);sys.stdin.readline()\n')
        child = subprocess.Popen([sys.executable, '-c', script, str(self.path)], env=self.child_environment(),
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            with selectors.DefaultSelector() as poller:
                poller.register(child.stdout, selectors.EVENT_READ)
                self.assertTrue(poller.select(5), 'lock holder did not start')
            self.assertEqual(child.stdout.readline().strip(), 'held')
            inode = self.path.stat().st_ino
            child.kill()
            child.wait(timeout=5)
            with state.process_lock(self.path):
                self.assertEqual(self.path.stat().st_ino, inode)
        finally:
            if child.poll() is None: child.kill()
            child.communicate(timeout=5)


if __name__ == '__main__':
    unittest.main()
