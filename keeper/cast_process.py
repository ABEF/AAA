"""Bounded noninteractive Unix Cast capture; never signs or retries on its own.

The raw stdout/stderr budget is shared. Pipe reads and exit wait use one deadline;
host/cgroup supervision still bounds kernel stalls and escaped descendants.
"""
from __future__ import annotations

import math
import os
import selectors
import signal
import subprocess
import time

MAX_OUTPUT_BYTES = 64 * 1024
READ_CHUNK_BYTES = 4096
CLEANUP_TIMEOUT_SECONDS = 2
WAIT_SLICE_SECONDS = .05


class CastCaptureError(RuntimeError):
    """Fixed diagnostics only; never contains command, environment or output."""


def _terminate(process):
    # The unreaped leader anchors this newly created process-group identity.
    # Do not poll/reap it before killing descendants holding inherited pipes.
    # A waiter may already have reaped while propagating an interruption.
    # Its numeric group is no longer an owned identity and must not be killed.
    if process.returncode is not None:
        return
    failed = False
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        failed = True
    wait_failed = False
    try:
        process.wait(timeout=CLEANUP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        wait_failed = True
    if wait_failed:
        raise CastCaptureError('Cast process cleanup did not complete')
    if failed:
        raise CastCaptureError('Cast process-group cleanup failed') from None


def run_cast(command, *, env, timeout):
    """Return complete bounded text, or fail without returning a partial result.

    Callers must publish uncertain send intent before invocation. An exception
    does not establish whether a transaction was broadcast. No shell, prompt,
    output logging, watchdog pulse, temporary output file or retry is used.
    """
    if os.name != 'posix':
        raise CastCaptureError('Cast capture requires supported Unix pipes')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Invalid Cast capture timeout')
    deadline = time.monotonic() + timeout

    def remaining():
        seconds = deadline - time.monotonic()
        if seconds <= 0:
            raise subprocess.TimeoutExpired('Cast', timeout)
        return seconds

    with selectors.DefaultSelector() as ready:
        process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
            close_fds=True, start_new_session=True)
        reaped = False
        timed_out = False
        try:
            buffers = [bytearray(), bytearray()]
            total = 0
            for index, pipe in enumerate((process.stdout, process.stderr)):
                os.set_blocking(pipe.fileno(), False)
                ready.register(pipe, selectors.EVENT_READ, index)
            while ready.get_map():
                events = ready.select(remaining())
                remaining()
                for key, _mask in events:
                    try:
                        data = os.read(key.fd, min(READ_CHUNK_BYTES, MAX_OUTPUT_BYTES - total + 1))
                    except BlockingIOError:
                        continue
                    if not data:
                        ready.unregister(key.fileobj)
                        continue
                    if len(data) > MAX_OUTPUT_BYTES - total:
                        raise CastCaptureError('Cast output exceeded its byte limit')
                    buffers[key.data].extend(data)
                    total += len(data)
            # Decode before reaping: failure cleanup must retain the anchored
            # process-group identity. Both streams keep old text=True semantics.
            output = None
            try:
                output = tuple(bytes(value).decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
                               for value in buffers)
            except UnicodeError:
                pass
            if output is None:
                raise CastCaptureError('Cast output was not valid UTF-8')
            stdout, stderr = output
            # Preserve ownership across reaping and bookkeeping. SIGINT can
            # otherwise make Popen.wait reap internally before it re-raises.
            # Short slices keep interruption responsive within the same deadline.
            signals = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM}
            while True:
                wait_seconds = min(WAIT_SLICE_SECONDS, remaining())
                previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
                try:
                    signal.pthread_sigmask(signal.SIG_BLOCK, signals)
                    try:
                        returncode = process.wait(timeout=wait_seconds)
                    except subprocess.TimeoutExpired:
                        continue
                    reaped = True
                    break
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            remaining()
            return subprocess.CompletedProcess(command, returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            # Do not attach argv, partial output or provider/credential paths.
            timed_out = True
        finally:
            try:
                if not reaped:
                    _terminate(process)
            finally:
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
        if timed_out:
            raise subprocess.TimeoutExpired('Cast', timeout)
