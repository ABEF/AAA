"""Fixed c818 preparation/control; only new isolated scheduling units exist here."""
from pathlib import Path, PurePosixPath
import argparse
import base64
import hashlib
import gzip
import io
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import tarfile
import time

LAB = Path('/opt/popl-keeper-scheduling-20261126-c818')
PREFIX = 'popl-keeper-scheduling-20261126-c818'
UNIT = PREFIX + '.service'
JOBS = ('init', 'backup', 'observe', 'hold', 'checks', 'rebind')
SERVICES = (UNIT, *(PREFIX + '-' + name + '.service' for name in JOBS))
TIMERS = (PREFIX + '-backup.timer', PREFIX + '-observe.timer')
EXPECTED = __MEMBERS__
BUNDLE_SHA = __BUNDLE_SHA__
SOURCE_MANIFEST_SHA = __SOURCE_MANIFEST_SHA__
MAX_ARCHIVE = 2*1024*1024
ARTIFACTS = ('RESULT.json', 'FINAL.json', 'PROGRESS.json', 'FOCUSED_RESULT.json',
    'FOCUSED_PROGRESS.json', 'WORKER_LOGS.json', 'MANAGER_TRACE.json', 'NATIVE_PROPERTIES.json')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(value):
    if not value:
        raise ValueError('Fixed isolated scheduling control refused')


def run(argv, timeout=15):
    mask = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM}
    child = owned = None
    output = [bytearray(), bytearray()]
    size = 0
    end = time.monotonic()+timeout
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'},
            start_new_session=True, close_fds=True)
        owned = child
        with selectors.DefaultSelector() as selector:
            for index, pipe in enumerate((child.stdout, child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, index)
            while selector.get_map():
                need(time.monotonic() < end)
                for key, _ in selector.select(min(.1, max(.001, end-time.monotonic()))):
                    raw = os.read(key.fd, min(16384, 65537-size))
                    if not raw:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(raw)
                    need(size <= 65536)
                    output[key.data].extend(raw)
        while True:
            need(time.monotonic() < end)
            previous = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
            try:
                try:
                    code = child.wait(timeout=min(.05, max(.001, end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    continue
                owned = None
                return code, bytes(output[0]), bytes(output[1])
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous)
    finally:
        if owned is not None:
            previous = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
            try:
                if owned.returncode is None:
                    try:
                        os.killpg(owned.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                owned.wait(timeout=2)
                owned = None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        if child is not None:
            child.stdout.close()
            child.stderr.close()


def properties(unit=UNIT):
    need(unit in (*SERVICES, *TIMERS))
    names = ('Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,'
        'ExecStart,User,Group,PrivateNetwork,NoNewPrivileges,ProtectSystem,ProtectHome,Restart,NRestarts,'
        'KillMode,TimeoutStartUSec,TimeoutStopUSec,MemoryMax,MemorySwapMax,TasksMax,WorkingDirectory,ReadWritePaths,'
        'StartLimitIntervalUSec,StartLimitBurst,References,PropagatesStopTo,CapabilityBoundingSet')
    code, out, err = run(['/usr/bin/systemctl', 'show', unit, '--no-pager', '--property=' + names])
    value = dict(line.split('=', 1) for line in out.decode('utf8', 'strict').splitlines() if '=' in line)
    need(code == 0 or code == 1 and value.get('LoadState') == 'not-found')
    return value


def read(path, maximum, owner=0):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_uid == owner and
        before.st_nlink == 1 and not before.st_mode & 0o022 and 0 <= before.st_size <= maximum)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        data = bytearray()
        while True:
            part = os.read(fd, min(65536, maximum+1-len(data)))
            if not part:
                break
            data.extend(part)
            need(len(data) <= maximum)
        final = os.fstat(fd)
        named = path.lstat()
        key = lambda st: (st.st_dev, st.st_ino, st.st_uid, st.st_mode, st.st_nlink, st.st_size, st.st_mtime_ns)
        need(key(before) == key(opened) == key(final) == key(named) and len(data) == before.st_size)
        return bytes(data)
    finally:
        os.close(fd)


def owned():
    need(os.getuid() == 0)
    for path in (Path('/opt'), LAB):
        st = path.lstat()
        need(stat.S_ISDIR(st.st_mode) and st.st_uid == 0 and not st.st_mode & 0o022)
    need(json.loads(read(LAB/'LAB_ID.json', 16384)) == {'schema': 1, 'unit': UNIT, 'lab': str(LAB),
        'controller_sha256': ACTIVE_CONTROLLER_SHA, 'bundle_sha256': BUNDLE_SHA,
        'source_manifest_sha256': SOURCE_MANIFEST_SHA})
    mask_identity()


def mask_identity():
    parent = (LAB/'masks').lstat()
    need(stat.S_ISDIR(parent.st_mode) and parent.st_uid == 0 and stat.S_IMODE(parent.st_mode) == 0o555)
    result = {}
    for name in ('key.empty', 'password.empty'):
        path = LAB/'masks'/name
        item = path.lstat()
        need(stat.S_ISREG(item.st_mode) and not path.is_symlink() and item.st_uid == 0 and
            stat.S_IMODE(item.st_mode) == 0 and item.st_nlink == 1 and item.st_size == 0)
        result[name] = {'device': item.st_dev, 'inode': item.st_ino, 'uid': item.st_uid,
            'mode': stat.S_IMODE(item.st_mode), 'links': item.st_nlink, 'bytes': item.st_size}
    need(len({(v['device'], v['inode']) for v in result.values()}) == 2)
    return result


def source_identity():
    result = {}
    for name, pin in EXPECTED.items():
        raw = read(LAB/name, 1024*1024)
        need(pin == {'bytes': len(raw), 'sha256': sha(raw)} and not (LAB/name).stat().st_mode & 0o222)
        result[name] = sha(raw)
    return result


def write_root(name, value):
    need(name in ('LAB_ID.json', 'INSTALL.json', 'START.json', 'FINAL.json'))
    raw = (json.dumps(value, sort_keys=True, allow_nan=False)+'\n').encode()
    need(len(raw) <= 32768)
    fd = os.open(LAB/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def install(a):
    need(os.getuid() == 0 and not os.path.lexists(LAB))
    need(all(properties(unit).get('LoadState') == 'not-found' for unit in (*SERVICES, *TIMERS)))
    raw = sys.stdin.buffer.read(MAX_ARCHIVE+1)
    need(0 < len(raw) <= MAX_ARCHIVE and sha(raw) == BUNDLE_SHA)
    data = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r|gz') as archive:
        for item in archive:
            need(len(data) < len(EXPECTED) and item.name in EXPECTED and item.name not in data and item.isfile()
                and item.name == str(PurePosixPath(item.name)) and not item.name.startswith('/')
                and '..' not in PurePosixPath(item.name).parts and '\\' not in item.name and ':' not in item.name
                and 0 <= item.size <= 1024*1024)
            total += item.size
            need(total <= 8*1024*1024)
            value = archive.extractfile(item).read(1024*1024+1)
            need(EXPECTED[item.name] == {'bytes': len(value), 'sha256': sha(value)})
            data[item.name] = value
    need(set(data) == set(EXPECTED) and sha(data['SOURCE_MANIFEST.json']) == SOURCE_MANIFEST_SHA)
    LAB.mkdir(mode=0o755)
    for name, value in sorted(data.items()):
        path = LAB/name
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
        os.fchmod(fd, 0o444)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    masks = LAB/'masks'
    masks.mkdir(mode=0o755)
    for name in ('key.empty', 'password.empty'):
        fd = os.open(masks/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0)
        os.fchmod(fd, 0)
        os.close(fd)
    os.chmod(masks, 0o555)
    runtime = LAB/'runtime'
    runtime.mkdir(mode=0o700)
    os.chown(runtime, 65534, 65534)
    for name in ('tmp', 'home'):
        path = runtime/name
        path.mkdir(mode=0o700)
        os.chown(path, 65534, 65534)
    for job in ('driver', *JOBS):
        for channel in ('stdout', 'stderr'):
            fd = os.open(runtime/(job+'.'+channel), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            if job != 'driver':
                os.fchown(fd, 65534, 65534)
            os.close(fd)
    write_root('INSTALL.json', {'schema': 1, 'source_before': source_identity(), 'mask_before': mask_identity()})
    write_root('LAB_ID.json', {'schema': 1, 'unit': UNIT, 'lab': str(LAB), 'controller_sha256': a.controller_sha256,
        'bundle_sha256': BUNDLE_SHA, 'source_manifest_sha256': SOURCE_MANIFEST_SHA})
    return {'phase': 'installed', 'source': source_identity(), 'existing_units_changed': False}


def start(a):
    owned()
    need(not (LAB/'START.json').exists() and properties().get('LoadState') == 'not-found')
    runtime = LAB/'runtime'
    policy = {'Type': 'oneshot', 'User': 'root', 'Group': 'root', 'PrivateNetwork': 'yes', 'PrivateTmp': 'yes',
        'PrivateDevices': 'yes', 'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'NoNewPrivileges': 'yes',
        'ProtectKernelTunables': 'yes', 'ProtectKernelModules': 'yes', 'ProtectControlGroups': 'yes',
        'RestrictSUIDSGID': 'yes', 'LockPersonality': 'yes',
        'CapabilityBoundingSet': 'CAP_CHOWN CAP_DAC_OVERRIDE CAP_FOWNER', 'AmbientCapabilities': '',
        'RestrictAddressFamilies': 'AF_UNIX AF_INET', 'ReadWritePaths': str(runtime), 'UMask': '0077',
        'Restart': 'no', 'RemainAfterExit': 'yes', 'TimeoutStartSec': '180', 'TimeoutStopSec': '2',
        'KillMode': 'control-group', 'SendSIGKILL': 'yes', 'FinalKillSignal': 'SIGKILL',
        'MemoryMax': '512M', 'MemorySwapMax': '0', 'TasksMax': '64', 'CPUQuota': '100%',
        'LimitCORE': '0', 'LimitFSIZE': '65536', 'WorkingDirectory': str(LAB/'source'),
        'StandardOutput': 'append:'+str(runtime/'driver.stdout'), 'StandardError': 'append:'+str(runtime/'driver.stderr'),
        'PropagatesStopTo': ' '.join((*TIMERS, *(unit for unit in SERVICES if unit != UNIT)))}
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONPATH': str(LAB/'source'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'PYTHONUNBUFFERED': '1',
        'TMPDIR': str(runtime/'tmp'), 'HOME': str(runtime/'home'),
        'POPL_LAB_HOST_NETWORK_NAMESPACE': os.readlink('/proc/self/ns/net')}
    command = ['/usr/bin/systemd-run', '--quiet', '--no-block', '--unit='+UNIT]
    command += ['--property='+key+'='+value for key, value in policy.items()]
    command += ['--setenv='+key+'='+value for key, value in env.items()]
    argv = ['/usr/bin/python3', '-B', str(LAB/'source/lab_driver.py')]
    code, _, _ = run([*command, '--', *argv])
    need(code == 0)
    write_root('START.json', {'schema': 1, 'source_before': source_identity(), 'policy': policy,
        'environment': env, 'argv': argv, 'public_transactions': 0, 'only_fixed_new_units': True})
    return {'phase': 'started', 'unit': UNIT, 'properties': properties()}


def empty_group(p):
    if p.get('MainPID', '0') != '0':
        return False
    group = p.get('ControlGroup', '')
    if not group:
        return True
    need(group in ('/system.slice/'+unit for unit in SERVICES))
    path = Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs'
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return True
    need(len(raw) <= 4096)
    return not raw.strip()


def status(a):
    owned()
    p = properties()
    sizes = {name: (LAB/'runtime'/name).stat().st_size for name in ('driver.stdout', 'driver.stderr')}
    overflow = sum(sizes.values()) > 65536
    return {'phase': 'status', 'properties': p, 'driver_group_empty': empty_group(p),
        'terminal': empty_group(p) and p.get('SubState') in ('dead', 'failed', 'exited'),
        'combined_driver_output_bytes': sum(sizes.values()), 'output_limit_exceeded': overflow,
        'result_present': (LAB/'runtime/RESULT.json').exists()}


def stop(a):
    owned()
    before = {unit: properties(unit) for unit in (*TIMERS, *SERVICES)}
    for unit in (*TIMERS, *(u for u in SERVICES if u != UNIT), UNIT):
        if properties(unit).get('LoadState') != 'not-found':
            code, _, _ = run(['/usr/bin/systemctl', 'stop', unit], timeout=10)
            need(code == 0)
    after = {unit: properties(unit) for unit in (*TIMERS, *SERVICES)}
    need(all(empty_group(after[unit]) for unit in SERVICES))
    need(all(after[unit].get('ActiveState') in ('inactive', 'failed', None) for unit in TIMERS))
    if not (LAB/'FINAL.json').exists():
        installed = json.loads(read(LAB/'INSTALL.json', 32768))
        initial = installed['source_before']
        final = source_identity()
        property_raw = (json.dumps({'before_stop': before, 'after_stop': after}, sort_keys=True,
            separators=(',', ':'), allow_nan=False)+'\n').encode()
        need(len(property_raw) <= 256*1024)
        write_root('FINAL.json', {'schema': 1, 'source_before': initial, 'source_after': final,
            'source_unchanged': initial == final, 'all_owned_group_empty': True,
            'mask_before': installed['mask_before'], 'mask_after': mask_identity(),
            'mask_sources_unchanged': installed['mask_before'] == mask_identity(),
            'unit_properties': {'decoded_bytes': len(property_raw), 'decoded_sha256': sha(property_raw),
                'gzip_base64': base64.b64encode(gzip.compress(property_raw, mtime=0)).decode('ascii')}})
    return {'phase': 'stopped', 'all_owned_group_empty': True, 'owned_unit_count': len(SERVICES)+len(TIMERS)}


def fetch(a):
    owned()
    need(a.artifact in ARTIFACTS)
    path = LAB/'FINAL.json' if a.artifact == 'FINAL.json' else LAB/'runtime'/a.artifact
    raw = read(path, 32768, owner=65534 if a.artifact in ('FOCUSED_RESULT.json', 'FOCUSED_PROGRESS.json') else 0)
    return {'phase': 'saved_artifact', 'name': a.artifact, 'bytes': len(raw), 'sha256': sha(raw),
        'base64': base64.b64encode(raw).decode('ascii')}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=('install', 'start', 'status', 'stop', 'fetch'))
    p.add_argument('--controller-sha256', required=True)
    p.add_argument('--artifact')
    a = p.parse_args()
    need(re.fullmatch('[0-9a-f]{64}', a.controller_sha256) is not None)
    globals()['ACTIVE_CONTROLLER_SHA'] = a.controller_sha256
    value = globals()[a.action](a)
    print(json.dumps(value, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'refused': True, 'error_type': type(exc).__name__, 'scope': 'new_fixed_c818_scheduling'}))
        raise SystemExit(1) from None
