"""Exclusive verification outputs, reserved before any imported/check execution.

The durable nonpass marker survives incomplete producers. Owned file handles
prevent finalization from following a replaced path. This is evidence integrity,
not authentication against an account able to replace all local files.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import stat


class Evidence:
    def __init__(self, path, *, with_log=False, kind='verification'):
        self.path = Path(path)
        self.log_path = self.path.with_suffix('.log') if with_log else None
        if self.log_path is not None and self.path.resolve() == self.log_path.resolve():
            raise ValueError('JSON and log evidence paths must be distinct')
        self.kind = kind
        self.json = self.log = None
        self.finished = False

    @staticmethod
    def _open(path):
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            return os.fdopen(fd, 'w+', encoding='utf-8', newline='\n')
        except BaseException:
            os.close(fd)
            raise

    @staticmethod
    def _owned(path, handle):
        current, original = path.lstat(), os.fstat(handle.fileno())
        if (not stat.S_ISREG(current.st_mode) or
                (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino)):
            raise ValueError('Reserved evidence path changed; preserve and inspect the outputs')

    def _sync_directory(self):
        if hasattr(os, 'O_DIRECTORY'):
            fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    def _write_json(self, payload):
        # Validate before truncating even our own earlier nonpass marker.
        text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        self._owned(self.path, self.json)
        self.json.seek(0)
        self.json.truncate()
        self.json.write(text)
        self.json.flush()
        os.fsync(self.json.fileno())
        self._sync_directory()

    def _marker(self, state, error_type=None):
        return {'kind': self.kind, 'evidence_status': state, 'successful': False,
                'completion_recorded': False, 'production_approved': False,
                'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                'error_type': error_type,
                'notice': 'Incomplete verification evidence; do not infer that no work executed or retry it automatically.'}

    def _sync_log(self):
        if self.log is not None:
            self._owned(self.log_path, self.log)
            self.log.flush()
            os.fsync(self.log.fileno())

    def _failed(self, exc):
        # Best effort only when storage itself failed; never replace the cause,
        # delete reserved evidence or write through another owner's pathname.
        try:
            self._sync_log()
        except (OSError, ValueError):
            pass
        if self.json is not None:
            try:
                self._write_json(self._marker('interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit))
                                             else 'failed', type(exc).__name__))
            except (OSError, ValueError):
                pass

    def __enter__(self):
        paths = [self.path] + ([self.log_path] if self.log_path is not None else [])
        # Friendly preflight, followed by exclusive creation to close the race.
        if any(path.exists() or path.is_symlink() for path in paths):
            raise FileExistsError('Verification evidence output already exists')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.json = self._open(self.path)
            self._write_json(self._marker('in_progress'))
            if self.log_path is not None:
                self.log = self._open(self.log_path)
                self._sync_log()
                self._sync_directory()
            return self
        except BaseException as exc:
            self._failed(exc)
            self._close()
            raise

    def read_log(self):
        if self.log is None:
            return ''
        self._owned(self.log_path, self.log)
        self.log.flush()
        position = self.log.tell()
        self.log.seek(0)
        text = self.log.read()
        self.log.seek(position)
        return text

    def finish(self, report):
        if self.finished or not isinstance(report, dict):
            raise ValueError('Evidence requires one final object report')
        self._sync_log()
        self._write_json({**report, 'evidence_status': 'complete', 'completion_recorded': True})
        self.finished = True

    def _close(self):
        try:
            if self.log is not None:
                self.log.close()
        finally:
            if self.json is not None:
                self.json.close()

    def __exit__(self, typ, exc, traceback):
        incomplete = not self.finished and (exc is None or isinstance(exc, SystemExit) and exc.code in (None, 0))
        try:
            if exc is not None:
                self._failed(exc)
            elif not self.finished:
                self._failed(RuntimeError('Producer ended without a final report'))
        finally:
            self._close()
        if incomplete:
            raise RuntimeError('Verification producer exited without a final report')
        return False
