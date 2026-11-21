from __future__ import annotations
import contextlib
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any, Iterator

def integer(value: Any, field: str, *, minimum: int = 0) -> int:
    """Accept integer JSON values/decimal strings without truncating floats or bools."""
    if isinstance(value, bool) or not isinstance(value, (int, str)) or \
        isinstance(value, str) and not re.fullmatch(r'[0-9]+', value):
        raise ValueError(f'{field} must be an integer')
    number = int(value)
    if number < minimum:
        raise ValueError(f'{field} must be at least {minimum}')
    return number

def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON state field')
        result[key] = value
    return result

def _reject_constant(_value):
    raise ValueError('Nonfinite JSON state number')

def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Nonfinite JSON state number')
    return number

def read_json(path: str | Path, default: Any = None, *, encoding: str | None = None) -> Any:
    """Missing files use the explicit default; present malformed truth never does."""
    path = Path(path)
    # exists() follows links and can classify a dangling entry or access failure
    # as absence. Only a missing directory entry may create fresh defaults.
    try:
        path.lstat()
    except FileNotFoundError:
        return default
    return json.loads(path.read_text(encoding=encoding), object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant, parse_float=_finite_float)

def atomic_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive random creation never follows/clobbers a pre-existing .tmp link.
    # mkstemp creates a private 0600 file, regardless of stale file permissions.
    fd, name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd,'w') as handle:
            json.dump(data,handle,indent=2,sort_keys=True,allow_nan=False)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary,path)
        # Ensure the directory entry is durable before a transaction is submitted.
        if hasattr(os,'O_DIRECTORY'):
            directory = os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try: os.fsync(directory)
            finally: os.close(directory)
    finally:
        if temporary.exists(): temporary.unlink()

@contextlib.contextmanager
def process_lock(path: str | Path) -> Iterator[None]:
    """Private Unix advisory lock, released on death; never replace its inode.

    The direct parent is pinned and must be a real, protected directory. Its
    ancestors and the current user remain trusted host configuration; this is
    not multi-host fencing or protection from a hostile process with our UID.
    """
    import fcntl
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    parent = os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        directory = os.fstat(parent)
        if directory.st_uid not in (0,os.getuid()) or directory.st_mode & 0o022:
            raise ValueError('Process-lock directory must be protected and owned by keeper or root')
        descriptor = os.open(path.name,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,
                             0o600,dir_fd=parent)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_uid != os.getuid() or opened.st_mode & 0o022:
                raise ValueError('Process lock must be a protected regular file owned by this user')
            try: fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as exc: raise RuntimeError('Another instance holds the process lock') from exc
            try:
                named = os.stat(path.name,dir_fd=parent,follow_symlinks=False)
                current = path.lstat()
                identity = (opened.st_dev,opened.st_ino)
                if (named.st_dev,named.st_ino) != identity or (current.st_dev,current.st_ino) != identity:
                    raise RuntimeError('Process-lock path changed during acquisition')
                yield
            finally: fcntl.flock(descriptor,fcntl.LOCK_UN)
        finally: os.close(descriptor)
    finally: os.close(parent)
