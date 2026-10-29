from __future__ import annotations
import contextlib
import json
import math
import os
from pathlib import Path
import re
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
    return json.loads(path.read_text(encoding=encoding), object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant, parse_float=_finite_float) if path.exists() else default

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
    """Linux/Unix advisory lock, automatically released on process death."""
    import fcntl
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+') as handle:
        try: fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc: raise RuntimeError('Another instance holds the process lock') from exc
        try: yield
        finally: fcntl.flock(handle,fcntl.LOCK_UN)
