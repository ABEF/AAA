"""Fixed c819 preparation/control; only new isolated scheduling units exist here."""
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

LAB = Path('/opt/popl-keeper-scheduling-20261126-c819')
PREFIX = 'popl-keeper-scheduling-20261126-c819'
UNIT = PREFIX + '.service'
JOBS = ('init', 'backup', 'observe', 'hold', 'checks', 'rebind')
SERVICES = (UNIT, *(PREFIX + '-' + name + '.service' for name in JOBS))
TIMERS = (PREFIX + '-backup.timer', PREFIX + '-observe.timer')
EXPECTED = {'source/keeper/scheduling.py': {'bytes': 17800, 'sha256': 'd79be28db6bac2978f7c8efdfb641e037ce6d2024faa4e60e02f6f7c62049f4a'}, 'source/scripts/keeper-schedule.py': {'bytes': 2140, 'sha256': '5c07ec965eba5c5a2d94895ba050f17d49b9689923cf67a05f20f2d0bf29c0b4'}, 'source/tests_python/test_keeper_scheduling.py': {'bytes': 15979, 'sha256': '15a4f2bf088fc1853437838c3925f2eb5be9295305880dbaa052ef390bedae72'}, 'source/keeper/monitor.py': {'bytes': 194496, 'sha256': '90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'}, 'source/keeper/ops.py': {'bytes': 14444, 'sha256': 'da396ec9c65295fe540f9dc812a0612d8ed27f1ab677fd388b479e2f2372ad89'}, 'source/keeper/health.py': {'bytes': 24415, 'sha256': 'dd25d2151295d09dcdebc4b0331b82c8d2b384a5501b49d0bfeb483d396b5c04'}, 'source/keeper/rebalance_confirmation.py': {'bytes': 11926, 'sha256': '6cc29d78aaf4c3804379e9b15d0ff177ff537da1158e66a3111ae2c85d6d317d'}, 'source/keeper/compound_policy.py': {'bytes': 17260, 'sha256': '129d330417c37747e16456fd18c892550cf870bdad31847e328b42a5c7270e29'}, 'source/keeper/cast_process.py': {'bytes': 5694, 'sha256': '5856fec6fb15e1abb66750394c2fb7a24314686e964eca0e9363b5007aa5ba3a'}, 'source/zzz_ops/protocol_policy.py': {'bytes': 5907, 'sha256': '4d73e7a3f6d6b98c91f083e2c557a48259ac9bcc0dbe2fb7752f74c4335bb5c3'}, 'source/zzz_ops/lp_execution.py': {'bytes': 6860, 'sha256': '90c985622387a4de8d52dd075856a4cf25e8c2e5bc62f4a3490978fc8cf746b0'}, 'source/zzz_ops/execution_price.py': {'bytes': 2280, 'sha256': '1d0ff892d43ec450438e7d2a1c2f783e6d9f9aec66f1fe98e3c35f5b09de47e2'}, 'source/zzz_ops/rebalance_confirmation.py': {'bytes': 17194, 'sha256': '77a41f2520be5d5c6768505e7bfe75f68db79d37f611062750ecd02f58185331'}, 'source/zzz_ops/abi.py': {'bytes': 4797, 'sha256': 'c4c755f1a9bf8db70b1ecb81e2b4e6765581961289f6f550502983e375293d91'}, 'source/zzz_ops/rpc.py': {'bytes': 9709, 'sha256': '6b76610b1bc042196198657e069b30ef1009aff3237d71979e8d21495fb6380f'}, 'source/zzz_ops/state.py': {'bytes': 4644, 'sha256': '78985688f9fc0cebf4aa5912b1401a338ac1e9ce21d8c787393e0e2d421976cf'}, 'source/keeper/alerts.py': {'bytes': 23149, 'sha256': '053ac2a70f38801b77afde8ba107c78e322a11630cb04620e1aa35a3f811fe13'}, 'source/scripts/keeper-alerts.py': {'bytes': 2629, 'sha256': '4f3b6b3efa9401c4039b9dcdc1fa9bf0c4136c2342f02c7286c895bc0ef027c5'}, 'source/keeper/recovery_bundle.py': {'bytes': 36532, 'sha256': '022cd3b9a3692f9b5576fded8fb15d4aca2797f4ad3bd449561a4d57173de550'}, 'source/scripts/keeper-recovery.py': {'bytes': 3423, 'sha256': '450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'}, 'source/keeper/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'source/tests_python/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'source/tests_python/test_keeper_alerts.py': {'bytes': 32525, 'sha256': 'f960f5a50dd1469b3d1f9c1bfb1002e68e1c83982586bc59eec390db83915b6d'}, 'source/keeper/principal.py': {'bytes': 9171, 'sha256': 'b602340db5c7a52ad281c6b60885e2f74cc2708b731595fac5eeb9e026da6874'}, 'source/keeper/royalties.py': {'bytes': 17321, 'sha256': '02e04783068eed60db827673c9c27d3a37175edd7dccfa5ddefb8b54c055904c'}, 'source/keeper/watchdog.py': {'bytes': 5707, 'sha256': '59b4bb7783453a8f271fd5ab265fd5d2857d55096479be34f10ffe56c8408372'}, 'source/zzz_ops/errors.py': {'bytes': 992, 'sha256': '1dcc2855b45af8f806835f70f7f75200aa5b93ef84ddcf862e1e0f067aba5305'}, 'source/zzz_ops/ethereum_fees.py': {'bytes': 2464, 'sha256': '8c832b5e28beb7d7d5c8d90d6df102bb084a680cf251ded850a2f00fe0cb2ffe'}, 'source/zzz_ops/position.py': {'bytes': 2437, 'sha256': '54075cb2329e6e1defb4942683378d6a3995a74a6ea5e1f239a8fcf611e30d4d'}, 'source/zzz_ops/range_policy.py': {'bytes': 5859, 'sha256': '4d4d8c1772b45417d98e2aa336e100f59674c7bbbe7f4a35efa8d07f87d90171'}, 'source/keeper/operation_review.py': {'bytes': 43774, 'sha256': '75f6fc17399ae28791f81d97d5afea2f98a3061662cbb6e9f072b562d6f72f48'}, 'source/zzz_ops/physical_portfolio.py': {'bytes': 2125, 'sha256': 'f119b665860cb4aaa9fbebe81aa1f2564906dff8466d1febf96ea4eef46e719b'}, 'source/zzz_ops/production_v4.py': {'bytes': 65998, 'sha256': 'ffa0e95b06ca1c166e7e56debcba8829764a204a3f7b7e377fa2310499073d5c'}, 'source/zzz_ops/tick_math.py': {'bytes': 4949, 'sha256': '5224a360f3fecbc9c1d42094863e74771cee8036a60d8b81647d9e6d45e0c70a'}, 'source/zzz_ops/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'source/zzz_ops/work_budget.py': {'bytes': 3633, 'sha256': 'd60de944ee02fc8be02cdbdde0210c84fff02dea8bb63b386cc73688061a535b'}, 'source/zzz_ops/production_v2.py': {'bytes': 102622, 'sha256': '109531b48b9c8a85166c9585351dc40b4b534ec5eea14c5b81d895c1b2209889'}, 'source/zzz_ops/price_policy.py': {'bytes': 7148, 'sha256': '2f5e41da367c04fd811ac14a09bf0662abf8fe46f7a7619a17efa58295ce2958'}, 'source/keeper/zzz-keeper-backup.service': {'bytes': 1314, 'sha256': 'cfce8b4a2a06264ae07550f03dca5c6770b684780a55a670df5b6ab16236f4a9'}, 'source/keeper/zzz-keeper-backup.timer': {'bytes': 327, 'sha256': 'c9f3e856d2459da8e3a0ade1cf3ab6ff9b713c5eab6b0b01b515e9dc638a4c7c'}, 'source/keeper/zzz-keeper-observer.service': {'bytes': 1397, 'sha256': '1d8212f673e84dbdef42e2b8e67c7fc64a61640f12278f710d3a4204c423951b'}, 'source/keeper/zzz-keeper-observer.timer': {'bytes': 339, 'sha256': 'f78e1f409f5caa96668b5cfaa86962d3315bb81f7035fe05f61e50ce4ad44d90'}, 'source/reports/ubuntu-backup-recovery-20261126/evidence/c814/model-DRY.json': {'bytes': 11810, 'sha256': 'ad430c2dfbb5909f7925196d575965b91dff0f6c8397f9f54133749c2ac36d13'}, 'source/reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json': {'bytes': 7965, 'sha256': '70b4e6081c561092d7c7cadf173da48180b912839818ee262c2cf830b83e463f'}, 'source/lab_driver.py': {'bytes': 37494, 'sha256': 'aeae03ab9491d4a8cab4a07b86c1324ef22c379f182a6f3c187877217d34c205'}, 'source/hold_lock.py': {'bytes': 793, 'sha256': '54d32cfc41b0cd8782ffb3a3e55899ce362933c72ad78bf45c0723706503bc5c'}, 'source/run_focused.py': {'bytes': 6978, 'sha256': 'baad46b48b4609c3cdd0c76f55840a6f32756d4664ce189d8f5a8314dbec8817'}, 'SOURCE_MANIFEST.json': {'bytes': 21938, 'sha256': 'd48dcba9211ebbbbf20384081f6f71455e412d96bfbfab555ead57e4fc68f461'}}
BUNDLE_SHA = '82b3e12a19e0d247a67fce909ac08c8f305c321fe1bfa0383fd3a10a4ea253e9'
SOURCE_MANIFEST_SHA = 'd48dcba9211ebbbbf20384081f6f71455e412d96bfbfab555ead57e4fc68f461'
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
        'StartLimitIntervalUSec,StartLimitBurst,References,PropagatesStopTo,CapabilityBoundingSet,Type,RuntimeMaxUSec,'
        'ExecMainStartTimestampMonotonic,InvocationID')
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
    # The anchor must finish its start job before ordered namespace-sharing
    # workers can execute. Only this lab coordinator is Type=exec; real jobs
    # remain oneshot and keep their own TimeoutStartSec bounds.
    policy = {'Type': 'exec', 'User': 'root', 'Group': 'root', 'PrivateNetwork': 'yes', 'PrivateTmp': 'yes',
        'PrivateDevices': 'yes', 'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'NoNewPrivileges': 'yes',
        'ProtectKernelTunables': 'yes', 'ProtectKernelModules': 'yes', 'ProtectControlGroups': 'yes',
        'RestrictSUIDSGID': 'yes', 'LockPersonality': 'yes',
        'CapabilityBoundingSet': 'CAP_CHOWN CAP_DAC_OVERRIDE CAP_FOWNER', 'AmbientCapabilities': '',
        'RestrictAddressFamilies': 'AF_UNIX AF_INET', 'ReadWritePaths': str(runtime), 'UMask': '0077',
        'Restart': 'no', 'RemainAfterExit': 'yes', 'RuntimeMaxSec': '180',
        'TimeoutStartSec': '180', 'TimeoutStopSec': '2',
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
        print(json.dumps({'refused': True, 'error_type': type(exc).__name__, 'scope': 'new_fixed_c819_scheduling'}))
        raise SystemExit(1) from None
