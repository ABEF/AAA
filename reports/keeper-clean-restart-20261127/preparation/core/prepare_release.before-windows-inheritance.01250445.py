"""Fixed desktop preparation of the exact current public-source release only.

No application imports, tests, network calls, config, journal or signer inputs.
Partial output is retained on refusal; never overwrite, repair or auto-delete it.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
HEAD = 'd6e8a909fd2b2a12eb1bee15173e92d526178cdb'
MANIFEST_PATH = 'reports/keeper-sidecar-recovery-20261126/preparation/c821/SOURCE_MANIFEST.json'
MANIFEST_SHA = 'c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
PRIVATE = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/'
    '01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-clean-restart-20261127/private')
RELEASE = PRIVATE / 'release-001'
RECEIPT = BASE / 'RELEASE_PREPARATION.json'
MAX_FILE, MAX_TOTAL, MAX_STDERR = 1048576, 2097152, 4096


def need(condition):
    if not condition:
        raise ValueError('Exact release preparation refused.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf8')


def decode(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value)
            value[key] = item
        return value
    def reject(_):
        raise ValueError('Exact release preparation refused.')
    return json.loads(raw.decode('utf8'), object_pairs_hook=pairs,
        parse_constant=reject, parse_float=reject)


def key(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
        info.st_size, info.st_mtime_ns)


def clean(path, *, new=False, receipt=False):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and '\x00' not in str(path))
    need((path == RECEIPT if receipt else path.is_relative_to(PRIVATE))
        and not str(path).startswith(('\\\\', '//')))
    if os.name == 'nt':
        need(all(':' not in part and not part.endswith(('.', ' ')) for part in path.parts[1:]))
    for item in (*reversed(path.parents), path):
        if new and item == path:
            need(not os.path.lexists(path))
            break
        info = item.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info,
            'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
        if item != path:
            need(stat.S_ISDIR(info.st_mode))
    return path


def git(args, end, *, data=b'', maximum=MAX_TOTAL):
    """Bound bytes while draining both local Git pipes, before accumulation."""
    need(time.monotonic() < end and len(data) <= 16384)
    process = subprocess.Popen(['git', *args], cwd=ROOT, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    failed = threading.Event()
    output, errors = [], []
    def drain(pipe, result, limit):
        size = 0
        try:
            while True:
                chunk = pipe.read(16384)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit:
                    failed.set()
                    break
                result.append(chunk)
        except Exception:
            failed.set()
        finally:
            pipe.close()
    def send():
        try:
            process.stdin.write(data)
            process.stdin.flush()
        except Exception:
            failed.set()
        finally:
            process.stdin.close()
    threads = [threading.Thread(target=drain, args=(process.stdout, output, maximum), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, errors, MAX_STDERR), daemon=True),
        threading.Thread(target=send, daemon=True)]
    for thread in threads:
        thread.start()
    while process.poll() is None:
        if failed.is_set() or time.monotonic() >= end:
            process.kill()
            break
        time.sleep(.01)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        failed.set()
    for thread in threads:
        thread.join(2)
    need(not failed.is_set() and not any(thread.is_alive() for thread in threads)
        and process.returncode == 0 and time.monotonic() <= end)
    return b''.join(output)


def write(path, raw, end, *, receipt=False):
    need(time.monotonic() <= end and 0 < len(raw) <= MAX_FILE)
    path = clean(path, new=True, receipt=receipt)
    parent = path.parent.lstat()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
        getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(raw) == len(raw))
        stream.flush()
        os.fsync(stream.fileno())
        opened = os.fstat(stream.fileno())
    named = clean(path, receipt=receipt).lstat()
    need(key(opened) == key(named) and stat.S_ISREG(named.st_mode) and named.st_nlink == 1)
    after = path.parent.lstat()
    need((parent.st_dev, parent.st_ino) == (after.st_dev, after.st_ino))


def read(path, end):
    need(time.monotonic() <= end)
    path = clean(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_ino != 0
        and 0 < before.st_size <= MAX_FILE)
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0) |
        getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as stream:
        need(key(os.fstat(stream.fileno())) == key(before))
        raw = stream.read(MAX_FILE + 1)
        need(key(os.fstat(stream.fileno())) == key(before) == key(clean(path).lstat())
            and len(raw) == before.st_size)
    need(time.monotonic() <= end)
    return raw


def inventory(names, end):
    directories = {'source', 'source/keeper', 'source/zzz_ops', 'source/scripts', 'source/tests_python'}
    expected = set(names) | directories
    pending, found, snapshots = [''], set(), {}
    while pending:
        need(time.monotonic() <= end)
        relative = pending.pop()
        directory = clean(RELEASE / relative)
        before = directory.lstat()
        need(stat.S_ISDIR(before.st_mode))
        snapshots[relative] = key(before)
        with os.scandir(directory) as entries:
            for entry in entries:
                need(len(found) < len(expected))
                name = str(PurePosixPath(relative) / entry.name)
                need(name in expected and name not in found)
                found.add(name)
                info = Path(entry.path).lstat()
                need(not stat.S_ISLNK(info.st_mode) and not getattr(info,
                    'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
                if name in directories:
                    need(stat.S_ISDIR(info.st_mode))
                    pending.append(name)
                else:
                    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= MAX_FILE)
        need(key(clean(directory).lstat()) == key(before))
    need(found == expected)
    return snapshots


def main():
    stage = 'trust'
    try:
        end = time.monotonic() + 60
        need(git(['rev-parse', 'HEAD'], end, maximum=128).decode().strip() == HEAD)
        need(git(['branch', '--show-current'], end, maximum=128).decode().strip() == 'main')
        clean(RELEASE, new=True)
        clean(RECEIPT, new=True, receipt=True)
        manifest_raw = git(['cat-file', 'blob', HEAD + ':' + MANIFEST_PATH], end, maximum=MAX_FILE)
        need(len(manifest_raw) == 24910 and sha(manifest_raw) == MANIFEST_SHA)
        sources = decode(manifest_raw)['source_files']
        need(type(sources) is dict and len(sources) == 41)
        for name, row in sources.items():
            need(type(name) is str and re.fullmatch(r'(keeper|zzz_ops|scripts|tests_python)/[A-Za-z0-9_-]+\.py', name)
                and type(row) is dict and set(row) == {'bytes', 'sha256', 'stage'}
                and type(row['bytes']) is int and 0 < row['bytes'] <= MAX_FILE
                and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']))
        stage = 'git_blobs'
        names = sorted(sources)
        batch = git(['cat-file', '--batch'], end,
            data=''.join(HEAD + ':' + name + '\n' for name in names).encode(), maximum=MAX_TOTAL)
        raw_files, at = {'SOURCE_MANIFEST.json': manifest_raw}, 0
        for name in names:
            stop = batch.index(b'\n', at)
            header = batch[at:stop].split()
            need(len(header) == 3 and re.fullmatch(b'[0-9a-f]{40,64}', header[0]) and header[1] == b'blob')
            size = int(header[2]); at = stop + 1
            need(size == sources[name]['bytes'] and size <= MAX_FILE)
            raw = batch[at:at + size]; at += size + 1
            need(batch[at - 1:at] == b'\n' and len(raw) == size and sha(raw) == sources[name]['sha256'])
            raw_files['source/' + name] = raw
        need(at == len(batch) and len(raw_files) == 42 and sum(map(len, raw_files.values())) <= MAX_TOTAL)
        stage = 'publication'
        os.mkdir(clean(RELEASE, new=True), 0o700)
        for name in ('source', 'source/keeper', 'source/zzz_ops', 'source/scripts', 'source/tests_python'):
            os.mkdir(clean(RELEASE / name, new=True), 0o700)
        for name, raw in raw_files.items():
            write(RELEASE / name, raw, end)
        stage = 'saved_readback'
        initial = inventory(raw_files, end)
        for name, raw in raw_files.items():
            need(read(RELEASE / name, end) == raw)
        need(inventory(raw_files, end) == initial)
        for name, raw in raw_files.items():
            need(read(RELEASE / name, end) == raw)
        need(inventory(raw_files, end) == initial)
        receipt = {'schema': 1, 'kind': 'fixed_current_release_preparation', 'ok': True,
            'source_commit': HEAD, 'source_manifest_sha256': MANIFEST_SHA,
            'release_files': 41, 'total_members': 42, 'source_raw_bytes': sum(row['bytes'] for row in sources.values()),
            'total_raw_bytes': sum(map(len, raw_files.values())),
            'files': {name: {'bytes': len(raw), 'sha256': sha(raw)} for name, raw in sorted(raw_files.items())},
            'configuration_or_native_capture_included': False, 'signer_material_included': False,
            'raw_source_outside_checkout': True, 'readiness_approved': False,
            'application_imports': 0, 'test_bodies_run': 0, 'network_calls': 0, 'server_actions': 0}
        stage = 'receipt'
        write(RECEIPT, encode(receipt), end, receipt=True)
        print(json.dumps({'schema': 1, 'ok': True, 'release_files': 41, 'total_members': 42,
            'total_raw_bytes': receipt['total_raw_bytes'], 'receipt_sha256': sha(encode(receipt))}, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({'schema': 1, 'ok': False, 'refusal_stage': stage,
            'readiness_approved': False, 'refusal_code': 'release_preparation'}, sort_keys=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
