"""DRAFT root-native helpers for the separate fixed c806 Cast interruption.

No import-time action, CLI, generic service name, arbitrary executable, remote
transport, installer, signing command or journal edit is provided. The parent
capsule must authenticate this file and its complete installed source manifest
before calling these functions. Only MODEL_UNIT/KEEPER_UNIT/RESOLVE_UNIT are used.

Integration: native_start_model(pins), poll model READY, native_start_keeper(),
then native_kill_keeper_main() only after the model holds an actual Cast reply.
Use RestartWitness(receipt).capture() from the parent's bounded poll loop.
This is a deliberate main SIGKILL, never described as a watchdog experiment.
After the stock hashless block, stop keeper, native_resolve_saved_hash(), await
the one-shot resolver success and native_resume_keeper() with the same journal.
Call native_stop_owned() repeatedly: keeper is stopped before model is requested.
This file has not been executed against a host or used to run a test.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import time


LAB = Path('/opt/popl-ubuntu-supervisor-20261125-c806')
MODEL_UNIT = 'popl-ubuntu-supervisor-20261125-c806-model.service'
KEEPER_UNIT = 'popl-ubuntu-supervisor-20261125-c806-keeper.service'
RESOLVE_UNIT = 'popl-ubuntu-supervisor-20261125-c806-resolve.service'
UNITS = (MODEL_UNIT, KEEPER_UNIT, RESOLVE_UNIT)
SOURCE = LAB / 'source/contracts'
HELPERS = LAB / 'source/helpers'
RUN = LAB / 'runtime/run-001'
MODEL = RUN / 'model'
LIVE = MODEL / 'supervisor/actor'
CONFIG = LIVE / 'config.json'
READY = MODEL / 'READY.json'
UID = GID = 65534
CAST_SHA = 'd55f540256f0dd8b940a125d435919948a5e8c140262e9923067cbfa95ef2970'
ANVIL_SHA = '05ee0cf1758024ea5e23dae562d92955ace205ab299091a43d2fa5bdeb6933bd'
MAX_OUTPUT = 512 * 1024
MAX_PIDS = 256
MAX_GROUPS = 64
HELD = MODEL / 'supervisor/CAST_REPLY_HELD.json'
BLOCKED = MODEL / 'supervisor/HASHLESS_RESTART_BLOCKED.json'
PROPERTIES = (
    'Id', 'LoadState', 'ActiveState', 'SubState', 'MainPID', 'ControlGroup',
    'InvocationID', 'NRestarts', 'Result', 'ExecMainCode', 'ExecMainStatus',
    'ExecMainStartTimestampMonotonic', 'ExecMainExitTimestampMonotonic',
    'ActiveEnterTimestampMonotonic', 'InactiveEnterTimestampMonotonic',
    'WatchdogUSec', 'WatchdogSignal', 'WatchdogTimestampMonotonic',
    'TimeoutStopUSec', 'RestartUSec', 'Restart', 'NotifyAccess', 'KillMode',
    'SendSIGKILL', 'FinalKillSignal', 'LimitCORE', 'StartLimitIntervalUSec',
    'StartLimitBurst', 'User', 'Group', 'PrivateNetwork', 'JoinsNamespaceOf',
    'NoNewPrivileges', 'ProtectSystem', 'ProtectHome', 'ProtectControlGroups',
    'PrivateDevices', 'RestrictAddressFamilies', 'ReadWritePaths',
    'WorkingDirectory', 'ExecStart', 'RuntimeMaxUSec', 'MemoryMax',
    'MemorySwapMax', 'TasksMax', 'CPUQuotaPerSecUSec',
)


class NativeRefusal(ValueError):
    """Only reviewed fixed diagnostic literals may be exposed by the capsule."""


def need(value, message):
    if not value:
        raise NativeRefusal(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _read(path, maximum, owners=(0,), expected=None):
    """Pinned no-follow bounded read; never called for a credential file."""
    need(path.is_absolute(), 'Absolute fixed input path required')
    opened = []
    try:
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        opened.append(fd)
        for part in path.parts[1:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW |
                         os.O_CLOEXEC, dir_fd=fd)
            opened.append(fd)
            st = os.fstat(fd)
            need(stat.S_ISDIR(st.st_mode) and st.st_uid in owners and
                 not st.st_mode & 0o022, 'Unsafe fixed input parent')
        parent = fd
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                     dir_fd=parent)
        opened.append(fd)
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid in owners and
             before.st_nlink == 1 and not before.st_mode & 0o022 and
             0 <= before.st_size <= maximum, 'Unsafe fixed input file')
        parts, total = [], 0
        while True:
            part = os.read(fd, min(65536, maximum + 1 - total))
            if not part:
                break
            total += len(part)
            need(total <= maximum, 'Fixed input read bound exceeded')
            parts.append(part)
        after = os.fstat(fd)
        current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        key = lambda item: (item.st_dev, item.st_ino, item.st_uid, item.st_mode,
                            item.st_nlink, item.st_size, item.st_mtime_ns)
        need(key(before) == key(after) == key(current) and total == before.st_size,
             'Fixed input changed during read')
        raw = b''.join(parts)
        if expected is not None:
            need(digest(raw) == expected, 'Fixed input source pin differs')
        return raw
    finally:
        for fd in reversed(opened):
            os.close(fd)


def _ownership():
    need(os.name == 'posix' and os.geteuid() == 0, 'Native root control required')
    st = LAB.lstat()
    need(stat.S_ISDIR(st.st_mode) and st.st_uid == 0 and
         not st.st_mode & 0o022, 'Fixed lab ownership differs')
    marker = json.loads(_read(LAB / 'LAB_ID.json', 16384))
    need(marker.get('lab') == str(LAB), 'Fixed lab marker differs')
    return marker


def _unit(unit):
    need(unit in UNITS, 'Only the three fixed c806 native units are admitted')
    return unit


def _run(argv, timeout=15):
    """Bound bytes while reading, including failure cleanup; never print argv."""
    need(0 < timeout <= 30 and isinstance(argv, list) and argv,
         'Native command bound differs')
    env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'}
    child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env, close_fds=True,
                             start_new_session=True, bufsize=0)
    streams = [bytearray(), bytearray()]
    deadline = time.monotonic() + timeout
    reaped = False
    try:
        with selectors.DefaultSelector() as select:
            for index, pipe in enumerate((child.stdout, child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                select.register(pipe, selectors.EVENT_READ, index)
            total = 0
            while select.get_map():
                remaining = deadline - time.monotonic()
                need(remaining > 0, 'Native command deadline exceeded')
                for key, _ in select.select(remaining):
                    try:
                        raw = os.read(key.fd, min(4096, MAX_OUTPUT - total + 1))
                    except BlockingIOError:
                        continue
                    if not raw:
                        select.unregister(key.fileobj)
                        continue
                    total += len(raw)
                    need(total <= MAX_OUTPUT, 'Native command output bound exceeded')
                    streams[key.data].extend(raw)
            remaining = deadline - time.monotonic()
            need(remaining > 0, 'Native command deadline exceeded')
            code = child.wait(timeout=remaining)
            reaped = True
            return {'returncode': code, 'stdout': bytes(streams[0]),
                    'stderr': bytes(streams[1])}
    finally:
        try:
            if not reaped:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=2)
        finally:
            child.stdout.close()
            child.stderr.close()


def _properties(unit):
    result = _run(['/usr/bin/systemctl', 'show', _unit(unit), '--no-pager',
                   '--property=' + ','.join(PROPERTIES)])
    values = dict(line.split('=', 1) for line in
                  result['stdout'].decode('utf-8', 'strict').splitlines()
                  if '=' in line)
    need(result['returncode'] == 0 or values.get('LoadState') == 'not-found',
         'Native property inspection failed')
    need(values.get('Id', unit) == unit, 'Native unit identity differs')
    return values


def _proc(pid):
    need(type(pid) is int and pid > 1, 'Native process identity differs')
    base = Path('/proc') / str(pid)
    try:
        raw = (base / 'stat').read_bytes()
        need(len(raw) <= 8192, 'Native process stat bound exceeded')
        text = raw.decode('utf-8', 'replace')
        fields = text[text.rindex(')') + 2:].split()
        need(len(fields) >= 20, 'Native process stat shape differs')
        group = (base / 'cgroup').read_bytes()
        need(len(group) <= 8192, 'Native process cgroup bound exceeded')
        # No command line, environment, credential bytes or socket URL is read.
        return {'pid': pid, 'state': fields[0], 'ppid': int(fields[1]),
                'pgrp': int(fields[2]), 'session': int(fields[3]),
                'start_ticks': int(fields[19]),
                'cgroup': group.decode('utf-8', 'strict').splitlines(),
                'uid': base.stat().st_uid,
                'network_namespace': os.readlink(base / 'ns/net')}
    except (FileNotFoundError, ProcessLookupError):
        return None


def _census(unit, properties):
    expected = '/system.slice/' + _unit(unit)
    group = properties.get('ControlGroup', '')
    need(not group or group == expected, 'Native cgroup path differs')
    # Inspect the fixed cgroup even after ControlGroup becomes blank on exit.
    root = Path('/sys/fs/cgroup') / expected.lstrip('/')
    pending, groups, pids = [root], [], set()
    while pending:
        path = pending.pop()
        try:
            st = path.lstat()
        except FileNotFoundError:
            continue
        need(stat.S_ISDIR(st.st_mode) and not path.is_symlink() and
             path.is_relative_to(root), 'Native cgroup directory differs')
        groups.append(str(path.relative_to(root)) or '.')
        need(len(groups) <= MAX_GROUPS, 'Native cgroup count exceeded')
        try:
            raw = (path / 'cgroup.procs').read_bytes()
            need(len(raw) <= 16384, 'Native cgroup process bytes exceeded')
            pids.update(int(line) for line in raw.splitlines())
            need(len(pids) <= MAX_PIDS, 'Native cgroup process count exceeded')
            for entry in path.iterdir():
                identity = entry.lstat()
                if stat.S_ISDIR(identity.st_mode):
                    pending.append(entry)
        except FileNotFoundError:
            pass
    return {'path': expected, 'exists': root.exists(), 'groups': sorted(groups),
            'pids': sorted(pids), 'processes': [_proc(pid) for pid in sorted(pids)]}


def _manager_journal(unit):
    # UNIT+PID1 selects manager lifecycle messages; worker stdout is excluded.
    result = _run(['/usr/bin/journalctl', '--quiet', '--no-pager', '--output=json',
                   '--lines=160', '_PID=1', 'UNIT=' + _unit(unit)])
    need(result['returncode'] == 0, 'Native manager journal read failed')
    rows = []
    keys = ('__CURSOR', '__REALTIME_TIMESTAMP', '__MONOTONIC_TIMESTAMP',
            '_SOURCE_MONOTONIC_TIMESTAMP', '_BOOT_ID', '_PID', 'UNIT',
            'INVOCATION_ID', 'MESSAGE_ID', 'UNIT_RESULT', 'JOB_RESULT',
            'EXIT_CODE', 'EXIT_STATUS', 'SIGNALNAME', 'SYSLOG_IDENTIFIER', 'MESSAGE')
    for line in result['stdout'].splitlines():
        row = json.loads(line)
        need(str(row.get('_PID')) == '1' and row.get('UNIT') == unit,
             'Native manager journal identity differs')
        message = row.get('MESSAGE', '')
        need(isinstance(message, str) and len(message.encode()) <= 8192,
             'Native manager message bound exceeded')
        rows.append({key: row[key] for key in keys if key in row})
    need(len(rows) <= 160, 'Native manager row count exceeded')
    return rows


def native_status(old_processes=(), include_journal=True):
    """Read native state; no filesystem state or services are mutated."""
    _ownership()
    need(len(old_processes) <= MAX_PIDS, 'Old process census bound exceeded')
    started = time.monotonic()
    units = {}
    for unit in UNITS:
        values = _properties(unit)
        units[unit] = {'properties': values, 'cgroup': _census(unit, values)}
        if include_journal:
            units[unit]['manager_journal'] = _manager_journal(unit)
    old = []
    for item in old_processes:
        need(type(item) is dict and type(item.get('pid')) is int and
             type(item.get('start_ticks')) is int, 'Old generation shape differs')
        current = _proc(item['pid'])
        same = current is not None and current['start_ticks'] == item['start_ticks']
        old.append({'pid': item['pid'], 'start_ticks': item['start_ticks'],
                    'same_generation': same,
                    'same_generation_live': same and current['state'] not in ('Z', 'X'),
                    'current': current})
    return {'schema': 1, 'lab': str(LAB), 'started_monotonic': started,
            'finished_monotonic': time.monotonic(), 'utc': time.time(),
            'host_network_namespace': os.readlink('/proc/self/ns/net'),
            'units': units, 'old_processes': old}


def _runtime_directory(path):
    need(path in (LAB / 'runtime', RUN, RUN / 'native-tmp'),
         'Native runtime directory path differs')
    try:
        path.mkdir(mode=0o700)
        os.chown(path, UID, GID)
    except FileExistsError:
        pass
    st = path.lstat()
    need(stat.S_ISDIR(st.st_mode) and st.st_uid == UID and st.st_gid == GID and
         stat.S_IMODE(st.st_mode) == 0o700, 'Native runtime directory differs')


def _logs(kind, reuse=False):
    need(kind in ('model', 'keeper', 'resolve'), 'Native log kind differs')
    result = []
    for stream in ('stdout', 'stderr'):
        path = RUN / ('native-' + kind + '.' + stream + '.log')
        if reuse:
            identity = path.lstat()
            need(kind == 'keeper' and stat.S_ISREG(identity.st_mode) and
                 identity.st_uid == UID and identity.st_nlink == 1 and
                 stat.S_IMODE(identity.st_mode) == 0o600,
                 'Reviewed existing append log identity differs')
            result.append('append:' + str(path))
            continue
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600)
        os.fchown(fd, UID, GID)
        os.close(fd)
        result.append('append:' + str(path))
    return result


def _common_policy(kind, reuse_logs=False):
    stdout, stderr = _logs(kind, reuse=reuse_logs)
    return {'Type': 'simple', 'User': 'nobody', 'Group': 'nogroup',
            'NoNewPrivileges': 'yes', 'PrivateNetwork': 'yes', 'PrivateTmp': 'yes',
            'PrivateDevices': 'yes', 'ProtectSystem': 'strict', 'ProtectHome': 'yes',
            'ProtectKernelTunables': 'yes', 'ProtectKernelModules': 'yes',
            'ProtectControlGroups': 'yes', 'RestrictSUIDSGID': 'yes',
            'LockPersonality': 'yes', 'CapabilityBoundingSet': '',
            'AmbientCapabilities': '', 'RestrictAddressFamilies': 'AF_UNIX AF_INET AF_INET6',
            'ReadWritePaths': str(LAB / 'runtime'), 'UMask': '0077',
            'KillMode': 'control-group', 'SendSIGKILL': 'yes',
            'FinalKillSignal': 'SIGKILL', 'LimitCORE': '0',
            # Fixture model plus either keeper OR one-shot resolver remains
            # <=2GiB /150% CPU /128 tasks. Resolver requires keeper empty.
            'RuntimeMaxSec': '900',
            'MemoryMax': '1536M' if kind == 'model' else '512M',
            'MemorySwapMax': '0', 'TasksMax': '64',
            'CPUQuota': '100%' if kind == 'model' else '50%', 'CPUWeight': '10',
            'IOWeight': '10', 'Nice': '10', 'WorkingDirectory': str(SOURCE),
            'StandardOutput': stdout, 'StandardError': stderr,
            'UnsetEnvironment': 'HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY '
                                'http_proxy https_proxy all_proxy no_proxy PYTHONHOME '
                                'PYTHONSTARTUP PYTHONUSERBASE PYTHONINSPECT'}


def _start(unit, argv, policy, environment, wait=False):
    need(_properties(unit).get('LoadState') == 'not-found',
         'Fixed native unit name already exists')
    command = ['/usr/bin/systemd-run', '--quiet', '--unit=' + _unit(unit)]
    if wait:
        need(unit == RESOLVE_UNIT, 'Only exact stock resolver may use manager wait')
        command.append('--wait')
    for key, value in policy.items():
        command.append('--property=' + key + '=' + value)
    for key, value in environment.items():
        command.append('--setenv=' + key + '=' + value)
    command += ['--', *argv]
    result = _run(command, timeout=30 if wait else 20)
    need(result['returncode'] == 0, 'Fixed native transient start failed')
    return {'unit': unit, 'requested_policy': policy,
            'properties': _properties(unit), 'direct_exec_argv': argv,
            'manager_wait_completion': wait, 'manager_wait_returncode': result['returncode'],
            'manager_wait_completed_monotonic': time.monotonic() if wait else None,
            'controller_output_sha256': digest(result['stdout'] + result['stderr'])}


def native_start_model(pins):
    """Start the independently supervised private namespace/model peer."""
    _ownership()
    expected = {'source_manifest_sha256', 'base_sha256', 'jobs_sha256',
                'cases_sha256', 'model_sha256', 'base_model_sha256'}
    need(type(pins) is dict and set(pins) == expected and
         all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)
             for value in pins.values()), 'Native source pin set differs')
    for path, key in ((LAB / 'inputs/SOURCE_MANIFEST.json', 'source_manifest_sha256'),
                      (HELPERS / 'keeper_runtime.py', 'base_sha256'),
                      (HELPERS / 'keeper_jobs.py', 'jobs_sha256'),
                      (HELPERS / 'job_cases.py', 'cases_sha256'),
                      (HELPERS / 'model_service.py', 'model_sha256'),
                      (HELPERS / 'model_service_base.py', 'base_model_sha256')):
        _read(path, 2 * 1024 * 1024, expected=pins[key])
    for name, pin in (('cast', CAST_SHA), ('anvil', ANVIL_SHA)):
        _read(LAB / 'tools' / name, 128 * 1024 * 1024, expected=pin)
    need(all(_properties(unit).get('LoadState') == 'not-found' for unit in UNITS),
         'Native unit names must both be unused')
    for path in (LAB / 'runtime', RUN, RUN / 'native-tmp'):
        _runtime_directory(path)
    need(not os.path.lexists(MODEL), 'New native model output already exists')
    policy = _common_policy('model')
    policy.update(Restart='no', TimeoutStopSec='120')
    environment = {'PATH': str(LAB / 'tools') + ':/usr/bin:/bin', 'LANG': 'C.UTF-8',
                   'PYTHONPATH': str(HELPERS), 'PYTHONDONTWRITEBYTECODE': '1',
                   'PYTHONUNBUFFERED': '1', 'PYTHONNOUSERSITE': '1',
                   'POPL_LAB_HOST_NETWORK_NAMESPACE': os.readlink('/proc/self/ns/net'),
                   'TMPDIR': str(RUN / 'native-tmp')}
    argv = ['/usr/bin/python3', '-B', str(HELPERS / 'model_service.py')]
    for key in ('source_manifest_sha256', 'base_sha256', 'jobs_sha256',
                'cases_sha256', 'base_model_sha256'):
        argv += ['--' + key.replace('_', '-'), pins[key]]
    return _start(MODEL_UNIT, argv, policy, environment)


def _keeper_policy_checks(values):
    expected = {'WatchdogUSec': '2min', 'TimeoutStopUSec': '2min',
                'RestartUSec': '30s', 'Restart': 'on-failure',
                'NotifyAccess': 'main', 'WatchdogSignal': '9',
                'KillMode': 'control-group', 'SendSIGKILL': 'yes',
                'FinalKillSignal': '9', 'LimitCORE': '0',
                'User': 'nobody', 'Group': 'nogroup', 'PrivateNetwork': 'yes',
                'NoNewPrivileges': 'yes', 'ProtectSystem': 'strict',
                'ProtectHome': 'yes', 'ProtectControlGroups': 'yes',
                'PrivateDevices': 'yes', 'WorkingDirectory': str(SOURCE)}
    need(all(values.get(key) == value for key, value in expected.items()),
         'Loaded native keeper safeguards differ')
    need(MODEL_UNIT in values.get('JoinsNamespaceOf', '').split(),
         'Loaded native keeper namespace dependency differs')


def _keeper_launch_parts(reuse_logs=False):
    policy = _common_policy('keeper', reuse_logs=reuse_logs)
    policy.update(WatchdogSec='120s', TimeoutStopSec='120s', Restart='on-failure',
                  RestartSec='30s', NotifyAccess='main', WatchdogSignal='SIGKILL',
                  StartLimitIntervalSec='600s', StartLimitBurst='5',
                  JoinsNamespaceOf=MODEL_UNIT, Requires=MODEL_UNIT, After=MODEL_UNIT)
    environment = {'PATH': str(LAB / 'tools') + ':/usr/bin:/bin', 'LANG': 'C.UTF-8',
                   'PYTHONPATH': str(SOURCE), 'PYTHONDONTWRITEBYTECODE': '1',
                   'PYTHONUNBUFFERED': '1', 'PYTHONNOUSERSITE': '1',
                   'TMPDIR': str(MODEL / 'tmp'), 'HOME': str(LIVE / 'secrets')}
    argv = ['/usr/bin/python3', '-m', 'keeper.monitor', '--config', str(CONFIG), '--live']
    return argv, policy, environment


def native_start_keeper():
    """Direct stock main, exact existing config, one native keeper cgroup."""
    _ownership()
    model = _properties(MODEL_UNIT)
    need(model.get('ActiveState') == 'active' and int(model.get('MainPID', '0')) > 1,
         'Native model must be active before keeper')
    ready = json.loads(_read(READY, 65536, owners=(0, UID)))
    raw = _read(CONFIG, 256 * 1024, owners=(0, UID))
    need(ready.get('configuration_path') == str(CONFIG) and
         ready.get('configuration_sha256') == digest(raw),
         'Native model ready configuration differs')
    config = json.loads(raw)
    exact = {'chain_id': 4663, 'rpc_urls': ['http://127.0.0.1:19593'],
             'cast_binary': str(LAB / 'tools/cast'),
             'keystore': str(LIVE / 'secrets/keeper'),
             'password_file': str(LIVE / 'secrets/password'),
             'state_path': str(LIVE / 'state.json'),
             'health_path': str(LIVE / 'health.json'), 'lock_path': str(LIVE / 'keeper.lock'),
             'interval_seconds': 240, 'confirmations': 12, 'max_gas_limit': 24000000,
             'max_gas_price_wei': '5000000000',
             'max_transaction_cost_wei': '10000000000000000',
             'max_daily_cost_wei': '50000000000000000',
             'l1_fee_allowance_wei': '0', 'receipt_fee_policy': 'included'}
    need(all(config.get(key) == value for key, value in exact.items()),
         'Native keeper configuration or guard differs')
    need(config.get('maintenance') == {'compound': False, 'compound_idle': False,
         'harvest': True, 'minimum_liquidity': 1, 'harvest_interval_seconds': 3600},
         'Native keeper maintenance partition differs')
    _read(LAB / 'tools/cast', 128 * 1024 * 1024, expected=CAST_SHA)
    model_proc = _proc(int(model['MainPID']))
    need(model_proc is not None and model_proc['uid'] == UID and
         model_proc['network_namespace'] != os.readlink('/proc/self/ns/net') and
         ready.get('namespace') == model_proc['network_namespace'],
         'Native model private namespace differs')
    argv, policy, environment = _keeper_launch_parts()
    need(ready.get('monitor_argv') == argv and
         ready.get('monitor_working_directory') == str(SOURCE),
         'Native stock ExecStart differs from ready record')
    result = _start(KEEPER_UNIT, argv, policy, environment)
    _keeper_policy_checks(result['properties'])
    result['configuration_sha256'] = digest(raw)
    return result


def _held_record():
    raw = _read(HELD, 2 * 1024 * 1024, owners=(0, UID))
    record = json.loads(raw)
    accepted = record.get('accepted_hash')
    need(isinstance(accepted, str) and re.fullmatch(r'0x[0-9a-fA-F]{64}', accepted)
         and int(accepted, 16) != 0, 'Known accepted transaction hash differs')
    need(type(record.get('intent')) is dict and record['intent'].get('hash') is None
         and record['intent'].get('nonce') == 0 and
         record.get('maximum_hold_seconds') == 75,
         'Held actual Cast hashless intent differs')
    return raw, record


def native_kill_keeper_main():
    """Deliberate main kill only after native capture of the actual Cast child.

    Does not signal Cast directly and does not claim transactional cancellation.
    The manager's own group cleanup must remove the separately sessioned Cast.
    """
    _ownership()
    held_raw, held = _held_record()
    need(type(held.get('monotonic')) in (int, float) and
         0 <= time.monotonic() - held['monotonic'] <= 20,
         'Prompt actual Cast interruption window expired')
    journal = _read(LIVE / 'state.json', 2 * 1024 * 1024, owners=(0, UID))
    state = json.loads(journal)
    need(held.get('journal_sha256') == digest(journal) and
         held.get('journal_raw_utf8') == journal.decode('utf-8') and
         state.get('pending') == held['intent'] and state.get('next_nonce') == 0,
         'Original hashless journal changed before main kill')
    baseline = native_status()
    keeper = baseline['units'][KEEPER_UNIT]
    values = keeper['properties']
    _keeper_policy_checks(values)
    main = int(values.get('MainPID', '0'))
    need(values.get('ActiveState') == 'active' and main > 1 and
         int(values.get('WatchdogTimestampMonotonic', '0')) > 0,
         'Active notified native main required for deliberate kill')
    _read(LAB / 'tools/cast', 128 * 1024 * 1024, expected=CAST_SHA)
    matches = []
    for proc in keeper['cgroup']['processes']:
        if proc is None or proc['pid'] == main or proc['ppid'] != main:
            continue
        if proc['uid'] != UID or proc['session'] != proc['pid'] or proc['pgrp'] != proc['pid']:
            continue
        try:
            actual = os.readlink('/proc/' + str(proc['pid']) + '/exe')
            argv_raw = Path('/proc/' + str(proc['pid']) + '/cmdline').read_bytes()
        except (FileNotFoundError, ProcessLookupError):
            continue
        need(len(argv_raw) <= 65536, 'Actual Cast argument bound exceeded')
        argv = argv_raw.rstrip(b'\0').split(b'\0')
        if actual != str(LAB / 'tools/cast') or len(argv) < 4 or argv[1] != b'send':
            continue
        # Inspect only fixed command identities. Never return or log raw argv.
        need(argv[0] == os.fsencode(LAB / 'tools/cast') and
             b'--nonce' in argv and argv[argv.index(b'--nonce') + 1] == b'0' and
             b'--async' in argv and b'--json' in argv,
             'Actual Cast invocation identity differs')
        current = _proc(proc['pid'])
        if current is not None and current['start_ticks'] == proc['start_ticks'] and current['state'] not in ('Z', 'X'):
            matches.append(current)
    need(len(matches) == 1, 'Exactly one live actual Cast child must be captured')
    again = _properties(KEEPER_UNIT)
    need(again.get('InvocationID') == values.get('InvocationID') and
         int(again.get('MainPID', '0')) == main,
         'Native main changed before deliberate kill')
    need(0 <= time.monotonic() - held['monotonic'] <= 30,
         'Actual Cast hold margin exhausted before kill')
    requested = time.monotonic()
    result = _run(['/usr/bin/systemctl', 'kill', '--kill-whom=main',
                   '--signal=SIGKILL', KEEPER_UNIT])
    need(result['returncode'] == 0, 'Deliberate owned main kill request failed')
    return {'schema': 1, 'experiment': 'deliberate_SIGKILL_main_while_actual_Cast_reply_held',
            'watchdog_experiment': False, 'before': baseline,
            'actual_cast_before_main_kill': matches[0],
            'known_accepted_hash': held['accepted_hash'].lower(),
            'held_record_sha256': digest(held_raw), 'hashless_journal_sha256': digest(journal),
            'main_pid': main, 'invocation_id': values['InvocationID'],
            'kill_request_monotonic': requested, 'kill_return_monotonic': time.monotonic(),
            'no_transactional_cancellation_claimed': True}


def _inactive_empty(unit):
    values = _properties(unit)
    census = _census(unit, values)
    need(values.get('ActiveState') in ('inactive', 'failed', None) and
         int(values.get('MainPID', '0')) == 0 and not census['pids'],
         'Required native unit is not inactive with empty cgroup')
    return values


def native_resolve_saved_hash():
    """Adopt only the model's actual accepted hash using the stock one-shot CLI."""
    _ownership()
    _inactive_empty(KEEPER_UNIT)
    held_raw, held = _held_record()
    blocked = json.loads(_read(BLOCKED, 2 * 1024 * 1024, owners=(0, UID)))
    journal = _read(LIVE / 'state.json', 2 * 1024 * 1024, owners=(0, UID))
    state = json.loads(journal)
    need(blocked.get('accepted_hash') == held['accepted_hash'] and
         blocked.get('no_resend') is True and blocked.get('journal_sha256') == digest(journal) ==
         held.get('journal_sha256') and state.get('pending') == held['intent'] and
         state.get('next_nonce') == 0,
         'Stock hashless restart block or original journal differs')
    model = _properties(MODEL_UNIT)
    need(model.get('ActiveState') == 'active', 'Model must remain available for exact resolution')
    ready = json.loads(_read(READY, 65536, owners=(0, UID)))
    config = _read(CONFIG, 256 * 1024, owners=(0, UID))
    need(ready.get('configuration_sha256') == digest(config),
         'Original configuration changed before hash resolution')
    policy = _common_policy('resolve')
    policy.update(Restart='no', TimeoutStopSec='120s',
                  JoinsNamespaceOf=MODEL_UNIT, Requires=MODEL_UNIT, After=MODEL_UNIT)
    environment = {'PATH': str(LAB / 'tools') + ':/usr/bin:/bin', 'LANG': 'C.UTF-8',
                   'PYTHONPATH': str(SOURCE), 'PYTHONDONTWRITEBYTECODE': '1',
                   'PYTHONUNBUFFERED': '1', 'PYTHONNOUSERSITE': '1',
                   'TMPDIR': str(MODEL / 'tmp'), 'HOME': str(LIVE / 'secrets')}
    argv = ['/usr/bin/python3', '-m', 'keeper.monitor', '--config', str(CONFIG),
            '--resolve-pending', held['accepted_hash'].lower()]
    result = _start(RESOLVE_UNIT, argv, policy, environment, wait=True)
    after_raw = _read(LIVE / 'state.json', 2 * 1024 * 1024, owners=(0, UID))
    after = json.loads(after_raw)
    need(after.get('pending') is None and after.get('next_nonce') == 1,
         'Successful stock resolver did not reconcile original transaction')
    _inactive_empty(RESOLVE_UNIT)
    result.update(known_accepted_hash=held['accepted_hash'].lower(),
                  original_hashless_journal_sha256=digest(journal),
                  resolved_journal_sha256=digest(after_raw),
                  configuration_sha256=digest(config),
                  held_record_sha256=digest(held_raw),
                  signing_enabled=False, explicit_stock_hash_resolution=True)
    return result


def native_resume_keeper(resolution_receipt):
    """Resume or recreate only the reviewed fixed unit after manager-wait success."""
    _ownership()
    values = _inactive_empty(KEEPER_UNIT)
    resolved = _inactive_empty(RESOLVE_UNIT)
    _, held = _held_record()
    expected_argv = ['/usr/bin/python3', '-m', 'keeper.monitor', '--config', str(CONFIG),
                     '--resolve-pending', held['accepted_hash'].lower()]
    need(type(resolution_receipt) is dict and resolution_receipt.get('unit') == RESOLVE_UNIT and
         resolution_receipt.get('manager_wait_completion') is True and
         resolution_receipt.get('manager_wait_returncode') == 0 and
         resolution_receipt.get('direct_exec_argv') == expected_argv and
         resolution_receipt.get('known_accepted_hash') == held['accepted_hash'].lower(),
         'Recorded exact stock resolver completion differs')
    ready = json.loads(_read(READY, 65536, owners=(0, UID)))
    config = _read(CONFIG, 256 * 1024, owners=(0, UID))
    need(ready.get('configuration_sha256') == digest(config) ==
         resolution_receipt.get('configuration_sha256'),
         'Original configuration changed before normal resume')
    journal_raw = _read(LIVE / 'state.json', 2 * 1024 * 1024, owners=(0, UID))
    journal = json.loads(journal_raw)
    need(journal.get('pending') is None and journal.get('next_nonce') == 1,
         'Exact original transaction has not been reconciled')
    need(digest(journal_raw) == resolution_receipt.get('resolved_journal_sha256'),
         'Resolved original journal changed before normal resume')
    need(_properties(MODEL_UNIT).get('ActiveState') == 'active',
         'Native model unavailable for normal resume')
    collected = values.get('LoadState') == 'not-found'
    if collected:
        argv, policy, environment = _keeper_launch_parts(reuse_logs=True)
        launch = _start(KEEPER_UNIT, argv, policy, environment)
        _keeper_policy_checks(launch['properties'])
    else:
        _keeper_policy_checks(values)
        result = _run(['/usr/bin/systemctl', 'start', '--no-block', KEEPER_UNIT])
        need(result['returncode'] == 0, 'Reviewed native keeper resume request failed')
        launch = {'properties': _properties(KEEPER_UNIT)}
    return {'phase': 'normal_resume_requested', 'unit': KEEPER_UNIT,
            'same_configuration_sha256': digest(config),
            'same_original_journal_preserved': True,
            'journal_before_resume_sha256': digest(journal_raw),
            'unit_recreated_after_gc': collected, 'same_existing_logs_appended': True,
            'before': values, 'resolver_exit_or_collected': resolved,
            'recorded_resolver_completion': resolution_receipt,
            'launch': launch, 'after': _properties(KEEPER_UNIT)}


def native_request_stop(unit):
    """Nonblocking stop of one exact owned unit; model must be stopped last."""
    _ownership()
    _unit(unit)
    if unit == MODEL_UNIT:
        keeper = _properties(KEEPER_UNIT)
        census = _census(KEEPER_UNIT, keeper)
        need(keeper.get('ActiveState') in ('inactive', 'failed', None) and
             int(keeper.get('MainPID', '0')) == 0 and not census['pids'],
             'Keeper must be fully stopped before model')
        _inactive_empty(RESOLVE_UNIT)
    before = _properties(unit)
    if before.get('LoadState') != 'not-found':
        result = _run(['/usr/bin/systemctl', 'stop', '--no-block', unit])
        need(result['returncode'] == 0, 'Fixed native stop request failed')
    return {'unit': unit, 'stop_requested': True, 'before': before,
            'after': _properties(unit), 'stopped_is_not_inferred_from_request': True}


def native_stop_owned():
    """Call repeatedly; no stop request is made for any other service name."""
    _ownership()
    keeper = _properties(KEEPER_UNIT)
    census = _census(KEEPER_UNIT, keeper)
    keeper_done = (keeper.get('ActiveState') in ('inactive', 'failed', None) and
                   int(keeper.get('MainPID', '0')) == 0 and not census['pids'])
    if not keeper_done:
        return {'phase': 'stopping_keeper', 'request': native_request_stop(KEEPER_UNIT)}
    resolver = _properties(RESOLVE_UNIT)
    resolver_census = _census(RESOLVE_UNIT, resolver)
    resolver_done = (resolver.get('ActiveState') in ('inactive', 'failed', None) and
                     int(resolver.get('MainPID', '0')) == 0 and not resolver_census['pids'])
    if not resolver_done:
        return {'phase': 'stopping_resolver', 'request': native_request_stop(RESOLVE_UNIT)}
    model = _properties(MODEL_UNIT)
    model_census = _census(MODEL_UNIT, model)
    model_done = (model.get('ActiveState') in ('inactive', 'failed', None) and
                  int(model.get('MainPID', '0')) == 0 and not model_census['pids'])
    if not model_done:
        return {'phase': 'stopping_model', 'request': native_request_stop(MODEL_UNIT)}
    return {'phase': 'stopped', 'all_owned_units_stopped': True,
            'only_fixed_native_units_controlled': True,
            'native_status': native_status()}


class RestartWitness:
    """Parent-driven samples; never sleeps, spawns, signs, edits or restarts.

    Poll capture() sufficiently often throughout the unchanged30s restart gap.
    A final new-PID snapshot alone cannot satisfy the empty-before-restart gate.
    """
    def __init__(self, kill_receipt):
        need(kill_receipt.get('watchdog_experiment') is False and
             kill_receipt.get('experiment') == 'deliberate_SIGKILL_main_while_actual_Cast_reply_held',
             'Deliberate actual Cast main-kill receipt required')
        baseline = kill_receipt['before']
        keeper = baseline['units'][KEEPER_UNIT]
        self.old_invocation = keeper['properties'].get('InvocationID')
        self.old_main = int(keeper['properties'].get('MainPID', '0'))
        self.old_processes = [row for row in keeper['cgroup']['processes']
                              if row is not None]
        need(self.old_invocation and self.old_main > 1 and self.old_processes and
             any(row['pid'] == self.old_main for row in self.old_processes),
             'Restart witness requires a running native keeper baseline')
        need(int(keeper['properties'].get('WatchdogTimestampMonotonic', '0')) > 0,
             'Native main notification has not been accepted')
        self.baseline = baseline
        self.kill_receipt = kill_receipt
        need(any(row['pid'] == kill_receipt['actual_cast_before_main_kill']['pid'] and
                 row['start_ticks'] == kill_receipt['actual_cast_before_main_kill']['start_ticks']
                 for row in self.old_processes),
             'Actual Cast generation absent from native baseline')
        self.samples = []
        self.empty_before_restart = None
        self.new_invocation = None

    def capture(self):
        need(len(self.samples) < 1200, 'Native restart witness sample bound exceeded')
        snapshot = native_status(self.old_processes, include_journal=False)
        keeper = snapshot['units'][KEEPER_UNIT]
        properties = keeper['properties']
        pid = int(properties.get('MainPID', '0'))
        invocation = properties.get('InvocationID')
        all_old_dead = all(not row['same_generation_live'] for row in snapshot['old_processes'])
        empty = pid == 0 and not keeper['cgroup']['pids'] and all_old_dead
        if empty and self.new_invocation is None and self.empty_before_restart is None:
            self.empty_before_restart = snapshot['finished_monotonic']
        is_new = pid > 1 and invocation and invocation != self.old_invocation
        if is_new and self.new_invocation is None:
            self.new_invocation = {'invocation_id': invocation, 'pid': pid,
                                   'observed_monotonic': snapshot['finished_monotonic'],
                                   'all_old_generations_dead': all_old_dead,
                                   'observed_empty_before_restart': self.empty_before_restart}
        self.samples.append(snapshot)
        return snapshot

    def finish(self):
        need(self.empty_before_restart is not None and self.new_invocation is not None,
             'Native empty cgroup before restart was not observed')
        need(self.new_invocation['all_old_generations_dead'] and
             self.empty_before_restart < self.new_invocation['observed_monotonic'],
             'Old native process generations survived restart')
        final = native_status(self.old_processes)
        keeper = final['units'][KEEPER_UNIT]
        _keeper_policy_checks(keeper['properties'])
        need(keeper['properties'].get('InvocationID') == self.new_invocation['invocation_id'] and
             int(keeper['properties'].get('NRestarts', '0')) ==
             int(self.baseline['units'][KEEPER_UNIT]['properties'].get('NRestarts', '0')) + 1,
             'Expected exactly one native restart')
        need(all(not row['same_generation_live'] for row in final['old_processes']),
             'Old native generation remains live')
        pid = int(keeper['properties'].get('MainPID', '0'))
        current = next((row for row in keeper['cgroup']['processes']
                        if row is not None and row['pid'] == pid), None)
        model = final['units'][MODEL_UNIT]
        model_pid = int(model['properties'].get('MainPID', '0'))
        model_proc = next((row for row in model['cgroup']['processes']
                           if row is not None and row['pid'] == model_pid), None)
        need(current is not None and model_proc is not None and current['uid'] == UID and
             current['network_namespace'] == model_proc['network_namespace'] !=
             final['host_network_namespace'], 'Restarted native namespace identity differs')
        need(any(row.get('UNIT_RESULT') == 'signal' or
                 re.search(r"failed with result ['\"]signal['\"]",
                           row.get('MESSAGE', '').lower()) is not None
                 for row in keeper['manager_journal']),
             'Native manager signal-failure outcome is absent')
        return {'schema': 1, 'old_invocation_id': self.old_invocation,
                'old_main_pid': self.old_main, 'old_processes': self.old_processes,
                'observed_empty_monotonic': self.empty_before_restart,
                'new_invocation': self.new_invocation, 'baseline': self.baseline,
                'samples': self.samples, 'final': final,
                'deliberate_main_kill_receipt': self.kill_receipt,
                'scope': 'actual Cast child cleanup after deliberate main SIGKILL and one stock restart',
                'watchdog_experiment': False,
                'no_universal_fencing_or_total_elapsed_bound_claimed': True}
