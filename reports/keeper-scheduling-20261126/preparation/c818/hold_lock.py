"""Inert new lock holder; native TimeoutStartSec must kill both sleepers."""
from pathlib import Path
import fcntl
import json
import os
import signal
import time

RUNTIME = Path('/opt/popl-keeper-scheduling-20261126-c818/runtime')
assert os.getuid() == os.getgid() == 65534
fd = os.open(RUNTIME / 'schedule/schedule.lock', os.O_RDWR | os.O_NOFOLLOW)
fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
child = os.fork()
if child == 0:
    time.sleep(60)
    os._exit(0)
raw = (json.dumps({'parent_pid': os.getpid(), 'child_pid': child}, sort_keys=True) + '\n').encode()
out = os.open(RUNTIME / 'HOLD_READY.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
with os.fdopen(out, 'wb') as stream:
    stream.write(raw)
    stream.flush()
    os.fsync(stream.fileno())
time.sleep(60)
