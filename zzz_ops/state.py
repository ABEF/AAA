from __future__ import annotations
import contextlib
import json
import os
from pathlib import Path
from typing import Any, Iterator

def read_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else default

def atomic_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    fd = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    try:
        with os.fdopen(fd,'w') as handle:
            json.dump(data,handle,indent=2,sort_keys=True)
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
