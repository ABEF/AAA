"""Fixed c821 unsigned reconstruction-kit preflight; no application imports.

This report helper checks a closed saved inventory against independently retained
pins. It does not define a new backup format, reconstruct signer material, run a
keeper, map a live filesystem or approve canonical state, fencing or adoption.
Raw configuration, policy and package remain in the private store outside Git.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time

PRIVATE = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/'
    '01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-reconstruction-20261127/private')
SOURCE_MANIFEST = 'c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
CONFIG = '1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
POLICY = '7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
OUTER = 'a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED = '911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
CREATED = 1795723324
MAX_AGE, OPERATING_AGE = 86400, 900
MAX_FILE, MAX_TOTAL, MAX_PROOF = 1024 * 1024, 2 * 1024 * 1024, 16384
PACKAGE = ('manifest.json', 'selection.json', 'alert-state.json',
    'selected/manifest.json', 'selected/journal.json')
DAEMON = ('keeper/monitor.py', 'keeper/ops.py', 'keeper/health.py',
    'keeper/rebalance_confirmation.py', 'keeper/compound_policy.py',
    'keeper/cast_process.py', 'zzz_ops/protocol_policy.py', 'zzz_ops/lp_execution.py',
    'zzz_ops/execution_price.py', 'zzz_ops/rebalance_confirmation.py',
    'zzz_ops/abi.py', 'zzz_ops/rpc.py', 'zzz_ops/state.py')
SCHEDULE = (*DAEMON, 'keeper/alerts.py', 'scripts/keeper-alerts.py',
    'keeper/recovery_bundle.py', 'scripts/keeper-recovery.py',
    'keeper/scheduling.py', 'scripts/keeper-schedule.py')
FLAGS = {'unsigned': True, 'readiness_approved': False, 'production_approved': False,
    'canonical_state_verified': False, 'old_keeper_fenced': False,
    'signer_material_included': False, 'configuration_installed': False,
    'services_restarted': False, 'operating_freshness_approved': False}


def need(condition):
    if not condition:
        raise ValueError('Unsigned reconstruction kit refused.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False) + '\n').encode('utf8')


def decode(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value)
            value[key] = item
        return value
    def reject(_):
        raise ValueError('Unsigned reconstruction kit refused.')
    value = json.loads(raw.decode('utf8'), object_pairs_hook=pairs,
        parse_float=reject, parse_constant=reject)
    need(type(value) is dict)
    stack, count = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        count += 1
        need(depth <= 32 and count <= 100000)
        if type(item) is dict:
            stack.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            stack.extend((child, depth + 1) for child in item)
    return value


def key(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
        info.st_size, info.st_mtime_ns)


def clean(path, *, new=False):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and '\x00' not in str(path))
    need(path.is_relative_to(PRIVATE) and not str(path).startswith(('\\\\', '//')))
    if os.name == 'nt':
        need(all(':' not in part and not part.endswith(('.', ' '))
            for part in path.parts[1:]))
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


def read(path, end, maximum=MAX_FILE):
    need(time.monotonic() <= end)
    path = clean(path)
    parent, before = path.parent.lstat(), path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
        and before.st_ino != 0 and 0 < before.st_size <= maximum)
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    flags |= getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_CLOEXEC', 0)
    fd = os.open(path, flags)
    try:
        need(key(os.fstat(fd)) == key(before))
        chunks, size = [], 0
        while True:
            need(time.monotonic() <= end)
            chunk = os.read(fd, min(65536, maximum + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            need(size <= maximum)
            chunks.append(chunk)
        need(key(os.fstat(fd)) == key(before) == key(clean(path).lstat()))
    finally:
        os.close(fd)
    after_parent = clean(path.parent).lstat()
    need((parent.st_dev, parent.st_ino) == (after_parent.st_dev, after_parent.st_ino)
        and size == before.st_size)
    return b''.join(chunks)


def inventory(folder, names, end):
    """Visit only the finite expected tree, rejecting extras before descent."""
    expected_dirs = {''}
    for name in names:
        expected_dirs.update(str(parent) for parent in PurePosixPath(name).parents
            if str(parent) != '.')
    expected = set(names) | expected_dirs - {''}
    pending, found, snapshots = [''], set(), {}
    while pending:
        need(time.monotonic() <= end)
        relative = pending.pop()
        directory = clean(folder / relative)
        before = directory.lstat()
        need(stat.S_ISDIR(before.st_mode))
        snapshots[relative] = key(before)
        with os.scandir(directory) as entries:
            for entry in entries:
                need(len(found) < len(expected) and time.monotonic() <= end)
                name = str(PurePosixPath(relative) / entry.name)
                need(name in expected and name not in found)
                found.add(name)
                info = Path(entry.path).lstat()
                need(not stat.S_ISLNK(info.st_mode) and not getattr(info,
                    'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
                if name in expected_dirs:
                    need(stat.S_ISDIR(info.st_mode))
                    pending.append(name)
                else:
                    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                        and 0 < info.st_size <= MAX_FILE)
        need(key(clean(directory).lstat()) == key(before))
    need(found == expected)
    return snapshots


def verify(folder):
    end = time.monotonic() + 60
    folder = clean(folder)
    manifest_raw = read(folder / 'SOURCE_MANIFEST.json', end)
    need(sha(manifest_raw) == SOURCE_MANIFEST)
    manifest = decode(manifest_raw)
    sources = manifest['source_files']
    need(type(sources) is dict and len(sources) == 41)
    for name, row in sources.items():
        need(type(name) is str and re.fullmatch(r'(keeper|zzz_ops|scripts|tests_python)/[A-Za-z0-9_-]+\.py', name)
            and type(row) is dict and set(row) == {'bytes', 'sha256', 'stage'}
            and type(row['bytes']) is int and 0 < row['bytes'] <= MAX_FILE
            and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']))
    names = tuple(sorted(('SOURCE_MANIFEST.json', 'references/keeper-config.json',
        'references/policy.json', *('source/' + name for name in sources),
        *('package/' + name for name in PACKAGE))))
    need(len(names) == 49)
    before = inventory(folder, names, end)
    raw, files, total = {}, {}, 0
    for name in names:
        value = read(folder / name, end)
        total += len(value)
        need(total <= MAX_TOTAL)
        raw[name] = value
        files[name] = {'bytes': len(value), 'sha256': sha(value)}
    need(raw['SOURCE_MANIFEST.json'] == manifest_raw)
    for name, row in sources.items():
        need(files['source/' + name] == {field: row[field] for field in ('bytes', 'sha256')})
    for name, digest in (('references/keeper-config.json', CONFIG),
            ('references/policy.json', POLICY), ('package/manifest.json', OUTER),
            ('package/selected/manifest.json', NESTED)):
        need(files[name]['sha256'] == digest)
    # The authenticated raw config is deliberately not decoded or printed.
    policy = decode(raw['references/policy.json'])
    outer = decode(raw['package/manifest.json'])
    nested = decode(raw['package/selected/manifest.json'])
    source13 = {name: sources[name]['sha256'] for name in DAEMON}
    source19 = {name: sources[name]['sha256'] for name in SCHEDULE}
    need(nested['source_files_sha256'] == source13
        and policy['source_files_sha256'] == source19 == outer['source_files_sha256'])
    need(policy['configuration_sha256'] == CONFIG == nested['configuration_raw_sha256']
        == outer['configuration_raw_sha256'] and outer['policy_sha256'] == POLICY)
    need(outer['created_at'] == CREATED == nested['created_at']
        and policy['max_backup_age_seconds'] == OPERATING_AGE)
    for row in outer['files']:
        name = row['path']
        need(name in PACKAGE[1:] and files['package/' + name]
            == {field: row[field] for field in ('bytes', 'sha256')})
    need(len(outer['files']) == 4 and {row['path'] for row in outer['files']} == set(PACKAGE[1:]))
    need(nested['files'] == [{'path': 'journal.json', **files['package/selected/journal.json']}])
    for name in names:
        need(read(folder / name, end) == raw[name])
    need(inventory(folder, names, end) == before)
    current = int(time.time())
    need(CREATED <= current and current - CREATED <= MAX_AGE)
    return {'schema': 1, 'kind': 'popl-unsigned-recovery-kit-review', 'ok': True,
        **FLAGS, 'source_manifest_sha256': SOURCE_MANIFEST, 'policy_sha256': POLICY,
        'configuration_sha256': CONFIG, 'outer_manifest_sha256': OUTER,
        'nested_manifest_sha256': NESTED, 'source_file_count': 41, 'file_count': 49,
        'total_bytes': total, 'files': files, 'source13_sha256': source13,
        'source19_sha256': source19, 'capture_created_at': CREATED,
        'actual_verified_at': current, 'actual_capture_age_seconds': current - CREATED,
        'review_max_age_seconds': MAX_AGE, 'original_operating_max_age_seconds': OPERATING_AGE,
        'actual_operating_age_exceeded': current - CREATED > OPERATING_AGE}


def write_proof(path, raw):
    need(len(raw) <= MAX_PROOF)
    path = clean(path, new=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(raw) == len(raw))
        stream.flush()
        os.fsync(stream.fileno())
    need(read(path, time.monotonic() + 5, MAX_PROOF) == raw)


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, 'Invalid unsigned reconstruction kit arguments.\n')
    parser = SafeParser(description=__doc__)
    parser.add_argument('action', choices=('verify',))
    parser.add_argument('--kit', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    args = parser.parse_args()
    stage = 'input_paths'
    try:
        folder, output = clean(args.kit), clean(args.proof, new=True)
        need(not output.is_relative_to(folder) and not folder.is_relative_to(output))
        stage = 'kit_verification'
        proof = verify(folder)
        stage = 'proof_encoding'
        encoded = encode(proof)
        stage = 'proof_publication'
        write_proof(output, encoded)
        print(json.dumps({'schema': 1, 'ok': True, 'unsigned': True,
            'readiness_approved': False, 'file_count': 49, 'total_bytes': proof['total_bytes'],
            'proof_bytes': len(encoded), 'proof_sha256': sha(encoded)}, sort_keys=True))
        return 0
    except Exception as exc:
        error_type = type(exc).__name__
        if error_type not in ('ValueError', 'TypeError', 'KeyError', 'OSError',
                'FileNotFoundError', 'FileExistsError', 'PermissionError',
                'NotADirectoryError', 'IsADirectoryError', 'UnicodeDecodeError',
                'JSONDecodeError', 'RecursionError', 'OverflowError', 'MemoryError'):
            error_type = 'UnexpectedError'
        print(json.dumps({'schema': 1, 'ok': False, 'unsigned': True,
            'readiness_approved': False, 'refusal_code': 'kit_preflight',
            'error_type': error_type, 'refusal_stage': stage}, sort_keys=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
