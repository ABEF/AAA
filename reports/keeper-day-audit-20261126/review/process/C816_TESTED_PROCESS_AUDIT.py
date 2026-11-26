"""NEW process-ownership regressions; no process, signal or old test is run.

CPython Popen.wait may reap while handling KeyboardInterrupt, before re-raising.
These full capture-path compositions model that boundary, deferred signal
delivery after successful reaping, and bounded retry slices for both utilities.
"""
from contextlib import ExitStack
import os
import signal
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from keeper import cast_process
from zzz_ops import read_process


class InertPipe:
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.closed = False

    def fileno(self):
        return self.descriptor

    def close(self):
        self.closed = True


class InertSelector:
    def __init__(self):
        self.mapping = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def register(self, pipe, _event, data):
        self.mapping[pipe.fileno()] = SimpleNamespace(fd=pipe.fileno(), fileobj=pipe, data=data)

    def unregister(self, pipe):
        del self.mapping[pipe.fileno()]

    def get_map(self):
        return self.mapping

    def select(self, _timeout):
        return [(key, None) for key in self.mapping.values()]


class InterruptedChild:
    def __init__(self, mode):
        self.pid = 700001
        self.returncode = None
        self.stdout, self.stderr = InertPipe(10001), InertPipe(10002)
        self.mode, self.waits, self.killed = mode, [], False

    def wait(self, *, timeout):
        self.waits.append(timeout)
        if len(self.waits) == 1 and self.mode in ('reaped_interrupt', 'unreaped_interrupt'):
            if self.mode == 'reaped_interrupt':
                self.returncode = 0
            raise KeyboardInterrupt()
        if self.mode == 'retry_success' and len(self.waits) <= 2:
            raise subprocess.TimeoutExpired('inert process', timeout)
        if self.mode == 'deadline_timeout' and not self.killed:
            raise subprocess.TimeoutExpired('inert process', timeout)
        self.returncode = -signal.SIGKILL if self.killed else 0
        return self.returncode


class KeeperProcessAuditTests(unittest.TestCase):
    def compose(self, kind, mode):
        subject = cast_process if kind == 'cast' else read_process
        cleanup_name = '_terminate' if kind == 'cast' else '_cleanup'
        cleanup_function = getattr(subject, cleanup_name)
        child = InterruptedChild(mode)
        masks, order = [], []
        restored = False
        clock_ticks = []

        def clock():
            self.assertLess(len(clock_ticks), 64, 'An original deadline must not restart on each wait slice')
            clock_ticks.append((len(clock_ticks) + 1) * .02)
            return clock_ticks[-1]

        def killed(_pid, _signal):
            child.killed = True

        def mask(how, values):
            nonlocal restored
            order.append('mask')
            masks.append((how, values))
            if how == subject.signal.SIG_SETMASK and mode == 'restore_interrupt' and not restored:
                restored = True
                raise KeyboardInterrupt()
            return frozenset({signal.SIGTERM})

        def spawn(*_args, **kwargs):
            self.assertEqual([], masks, 'A newly spawned child must not inherit our wait mask')
            self.assertTrue(kwargs['start_new_session'])
            order.append('spawn')
            return child

        with ExitStack() as stack:
            stack.enter_context(patch.object(subject.os, 'name', 'posix'))
            # Constants are supplied only for portable inert modeling on Windows;
            # this does not claim an actual Windows pthread-mask implementation.
            for name, fallback in (('SIGALRM', 14), ('SIGHUP', 1), ('SIG_BLOCK', 0), ('SIG_SETMASK', 2)):
                stack.enter_context(patch.object(subject.signal, name, getattr(signal, name, fallback), create=True))
            stack.enter_context(patch.object(subject.signal, 'pthread_sigmask', side_effect=mask, create=True))
            stack.enter_context(patch.object(subject.subprocess, 'Popen', side_effect=spawn))
            stack.enter_context(patch.object(subject.os, 'set_blocking'))
            stack.enter_context(patch.object(subject.os, 'read', return_value=b''))
            kill = stack.enter_context(patch.object(subject.os, 'killpg', side_effect=killed, create=True))
            cleanup = stack.enter_context(patch.object(subject, cleanup_name, wraps=cleanup_function))
            if mode == 'deadline_timeout':
                stack.enter_context(patch.object(subject.time, 'monotonic', side_effect=clock))
            if kind == 'cast':
                stack.enter_context(patch.object(subject.selectors, 'DefaultSelector', return_value=InertSelector()))

            def invoke():
                command = ['inert-private-utility']
                timeout = .3 if mode == 'deadline_timeout' else 3
                if kind == 'cast':
                    return subject.run_cast(command, env={}, timeout=timeout)
                return subject.run_read_process(command, timeout=timeout)

            if mode == 'retry_success':
                result = invoke()
                self.assertEqual((0, '', '') if kind == 'cast' else (0, b'', b''),
                                 (result.returncode, result.stdout, result.stderr))
            elif mode == 'deadline_timeout':
                error = subprocess.TimeoutExpired if kind == 'cast' else read_process.ReadProcessError
                with self.assertRaises(error):
                    invoke()
                self.assertLessEqual(clock_ticks[-1], .4)
            else:
                with self.assertRaises(KeyboardInterrupt):
                    invoke()
        self.assertEqual('spawn', order[0])
        self.assertTrue(child.stdout.closed)
        self.assertTrue(child.stderr.closed)
        return child, kill, cleanup, masks

    def test_read_capture_never_signals_a_reaped_group_and_still_cleans_owned_interrupts(self):
        for mode in ('reaped_interrupt', 'unreaped_interrupt'):
            with self.subTest(mode=mode):
                child, kill, cleanup, _ = self.compose('read', mode)
                cleanup.assert_called_once()
                if mode == 'reaped_interrupt':
                    kill.assert_not_called()
                    self.assertEqual(1, len(child.waits))
                else:
                    kill.assert_called_once_with(child.pid, signal.SIGKILL)
                    self.assertEqual(read_process.CLEANUP_SECONDS, child.waits[-1])

    def test_cast_capture_never_signals_a_reaped_group_and_still_cleans_owned_interrupts(self):
        for mode in ('reaped_interrupt', 'unreaped_interrupt'):
            with self.subTest(mode=mode):
                child, kill, cleanup, _ = self.compose('cast', mode)
                cleanup.assert_called_once()
                if mode == 'reaped_interrupt':
                    kill.assert_not_called()
                    self.assertEqual(1, len(child.waits))
                else:
                    kill.assert_called_once_with(child.pid, signal.SIGKILL)
                    self.assertEqual(cast_process.CLEANUP_TIMEOUT_SECONDS, child.waits[-1])

    def test_reaped_flag_is_published_before_deferred_signal_delivery(self):
        for kind in ('read', 'cast'):
            with self.subTest(kind=kind):
                child, kill, cleanup, masks = self.compose(kind, 'restore_interrupt')
                self.assertEqual(0, child.returncode)
                cleanup.assert_not_called()
                kill.assert_not_called()
                self.assertEqual(3, len(masks))
                self.assertEqual(frozenset({signal.SIGTERM}), masks[-1][1])

    def test_wait_retry_slices_preserve_mask_and_original_absolute_budget(self):
        for kind in ('read', 'cast'):
            with self.subTest(kind=kind):
                subject = cast_process if kind == 'cast' else read_process
                child, kill, cleanup, masks = self.compose(kind, 'retry_success')
                cleanup.assert_not_called()
                kill.assert_not_called()
                self.assertEqual(3, len(child.waits))
                self.assertTrue(all(0 < seconds <= .05 for seconds in child.waits))
                self.assertEqual(.05, subject.WAIT_SLICE_SECONDS)
                self.assertEqual(9, len(masks))
                for index in (2, 5, 8):
                    self.assertEqual(frozenset({signal.SIGTERM}), masks[index][1])

    def test_repeated_wait_timeouts_expire_original_deadline_and_keep_cleanup_budget(self):
        for kind in ('read', 'cast'):
            with self.subTest(kind=kind):
                child, kill, cleanup, masks = self.compose(kind, 'deadline_timeout')
                cleanup.assert_called_once()
                kill.assert_called_once_with(child.pid, signal.SIGKILL)
                self.assertGreater(len(child.waits), 2)
                self.assertTrue(all(0 < seconds <= .05 for seconds in child.waits[:-1]))
                self.assertEqual(2, child.waits[-1])
                self.assertEqual(0, len(masks) % 3)

    @unittest.skipUnless(os.name == 'posix' and hasattr(signal, 'pthread_sigmask'),
                         'Actual POSIX signal-mask ownership proof')
    def test_actual_sigint_is_delivered_only_after_reaped_ownership_is_recorded(self):
        # Only this isolated test process signals itself. Popen, pipes and
        # killpg stay inert, so no child or unrelated process can be affected.
        for kind in ('read', 'cast'):
            with self.subTest(kind=kind):
                subject = cast_process if kind == 'cast' else read_process
                cleanup_name = '_terminate' if kind == 'cast' else '_cleanup'
                child = InterruptedChild('actual_signal')
                original_handler = signal.getsignal(signal.SIGINT)
                original_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
                self.assertNotIn(signal.SIGINT, signal.sigpending(), 'Unexpected preexisting test signal')
                received = []

                def handler(signum, _frame):
                    received.append(signum)
                    raise KeyboardInterrupt()

                def wait(*, timeout):
                    child.waits.append(timeout)
                    os.kill(os.getpid(), signal.SIGINT)
                    self.assertEqual([], received)
                    self.assertIn(signal.SIGINT, signal.sigpending())
                    child.returncode = 0
                    return 0

                try:
                    signal.signal(signal.SIGINT, handler)
                    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT})
                    with ExitStack() as stack:
                        stack.enter_context(patch.object(subject.subprocess, 'Popen', return_value=child))
                        stack.enter_context(patch.object(child, 'wait', side_effect=wait))
                        stack.enter_context(patch.object(subject.os, 'set_blocking'))
                        stack.enter_context(patch.object(subject.os, 'read', return_value=b''))
                        kill = stack.enter_context(patch.object(subject.os, 'killpg'))
                        cleanup = stack.enter_context(patch.object(subject, cleanup_name))
                        if kind == 'cast':
                            stack.enter_context(patch.object(subject.selectors, 'DefaultSelector',
                                                             return_value=InertSelector()))
                        with self.assertRaises(KeyboardInterrupt):
                            if kind == 'cast':
                                subject.run_cast(['inert-private-utility'], env={}, timeout=3)
                            else:
                                subject.run_read_process(['inert-private-utility'], timeout=3)
                        self.assertEqual([signal.SIGINT], received)
                        cleanup.assert_not_called()
                        kill.assert_not_called()
                        self.assertEqual(0, child.returncode)
                        self.assertTrue(child.stdout.closed and child.stderr.closed)
                finally:
                    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
                    if signal.SIGINT in signal.sigpending():
                        signal.sigwait({signal.SIGINT})
                    signal.signal(signal.SIGINT, original_handler)
                    signal.pthread_sigmask(signal.SIG_SETMASK, original_mask)
