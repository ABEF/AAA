"""Bounded bytes from a fixed, read-only utility; no shell or output logging.

This is not a signer transport. The direct process is reaped on failure; Unix
also kills its new group. Windows descendant containment remains a host duty.
The fixed monitor caller is single-threaded. Process creation and kernel stalls
still require host supervision; the elapsed work deadline cannot preempt them.
"""
from __future__ import annotations

import math
import os
import signal
import subprocess
import time

MAX_OUTPUT_BYTES = 1024 * 1024
READ_BYTES = 4096
CLEANUP_SECONDS = 2
WAIT_SLICE_SECONDS = .05


class ReadProcessError(RuntimeError):
    """Fixed diagnostics; argv, environment and captured bytes are excluded."""


def _windows_available(pipe):
    # Anonymous Popen pipes support PeekNamedPipe. Peek before each small read,
    # avoiding a blocking reader thread that an inherited pipe could strand.
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    peek = kernel.PeekNamedPipe
    peek.argtypes = (wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                     wintypes.LPVOID, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID)
    peek.restype = wintypes.BOOL
    available = wintypes.DWORD()
    if not peek(msvcrt.get_osfhandle(pipe.fileno()), None, 0, None,
                ctypes.byref(available), None):
        if ctypes.get_last_error() in (109, 232):
            return None
        raise ReadProcessError('Read-only process pipe failed') from None
    return available.value


def _cleanup(process):
    # Popen.wait may reap the child while handling KeyboardInterrupt and then
    # re-raise it before our caller records reaped=True. Never signal that old
    # numeric group: its leader is no longer an owned, unreaped identity.
    if os.name == 'posix' and process.returncode is not None:
        return
    failed = False
    try:
        if os.name == 'posix':
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass
    except OSError:
        failed = True
    try:
        process.wait(timeout=CLEANUP_SECONDS)
    except subprocess.TimeoutExpired:
        raise ReadProcessError('Read-only process cleanup did not complete') from None
    if failed:
        raise ReadProcessError('Read-only process cleanup failed') from None


def run_read_process(command, *, timeout):
    """Return complete bytes within one deadline and aggregate 1MiB budget.

    Intended for the forced-command SSH monitor only. No retries, stdin, shell,
    partial result, temporary output file or startup of monitoring is provided.
    """
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Invalid read-only process timeout')
    if os.name not in ('nt', 'posix'):
        raise ReadProcessError('Unsupported read-only process platform')
    deadline = time.monotonic() + timeout
    process = None
    success = False
    reaped = False
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
            close_fds=True, start_new_session=os.name == 'posix')
        pipes = [process.stdout, process.stderr]
        buffers = [bytearray(), bytearray()]
        if os.name == 'posix':
            for pipe in pipes:
                os.set_blocking(pipe.fileno(), False)
        active = {0, 1}
        total = 0
        while active:
            if time.monotonic() >= deadline:
                raise ReadProcessError('Read-only process deadline exceeded')
            progressed = False
            for index in tuple(active):
                pipe = pipes[index]
                size = min(READ_BYTES, MAX_OUTPUT_BYTES - total + 1)
                if os.name == 'nt':
                    available = _windows_available(pipe)
                    if available is None:
                        active.remove(index)
                        continue
                    if not available:
                        continue
                    size = min(size, available)
                try:
                    data = os.read(pipe.fileno(), size)
                except BlockingIOError:
                    continue
                if not data:
                    active.remove(index)
                    continue
                progressed = True
                if len(data) > MAX_OUTPUT_BYTES - total:
                    raise ReadProcessError('Read-only process output exceeded byte limit')
                buffers[index].extend(data)
                total += len(data)
            if not progressed and active:
                time.sleep(min(.01, max(0, deadline - time.monotonic())))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ReadProcessError('Read-only process deadline exceeded')
        if os.name == 'posix':
            # Mask only short wait/reaped bookkeeping slices. The child was
            # already started unmasked; no inherited signal policy is changed.
            signals = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM}
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ReadProcessError('Read-only process deadline exceeded')
                previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
                try:
                    signal.pthread_sigmask(signal.SIG_BLOCK, signals)
                    try:
                        returncode = process.wait(timeout=min(WAIT_SLICE_SECONDS, remaining))
                    except subprocess.TimeoutExpired:
                        continue
                    reaped = True
                    break
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        else:
            try:
                returncode = process.wait(timeout=remaining)
                reaped = True
            except subprocess.TimeoutExpired:
                raise ReadProcessError('Read-only process deadline exceeded') from None
        if time.monotonic() >= deadline:
            raise ReadProcessError('Read-only process deadline exceeded')
        result = subprocess.CompletedProcess('read-only process', returncode,
                                           bytes(buffers[0]), bytes(buffers[1]))
        success = True
        return result
    except ReadProcessError:
        raise
    except (OSError, ValueError):
        raise ReadProcessError('Read-only process unavailable') from None
    finally:
        if process is not None:
            try:
                if not success and not reaped:
                    _cleanup(process)
            finally:
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
