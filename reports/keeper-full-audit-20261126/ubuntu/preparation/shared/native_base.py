"""DRAFT root-native helpers for one fixed, isolated c804 rehearsal.

No import-time action, CLI, generic service name, arbitrary executable, remote
transport, installer, signing command or journal edit is provided. The parent
capsule must authenticate this file and its complete installed source manifest
before calling these functions. All commands affect only MODEL_UNIT/KEEPER_UNIT.

Integration: native_start_model(pins), poll model READY, native_start_keeper(),
then RestartWitness(native_status()).capture() from the parent's bounded poll
loop. finish() requires an observed empty old cgroup before the new invocation.
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


LAB = Path('/opt/popl-ubuntu-supervisor-20261125-c804')
MODEL_UNIT = 'popl-ubuntu-supervisor-20261125-c804-model.service'
KEEPER_UNIT = 'popl-ubuntu-supervisor-20261125-c804-keeper.service'
UNITS = (MODEL_UNIT, KEEPER_UNIT)
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
    need(unit in UNITS, 'Only the two fixed native units are admitted')
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


def _logs(kind):
    need(kind in ('model', 'keeper'), 'Native log kind differs')
    result = []
    for stream in ('stdout', 'stderr'):
        path = RUN / ('native-' + kind + '.' + stream + '.log')
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600)
        os.fchown(fd, UID, GID)
        os.close(fd)
        result.append('append:' + str(path))
    return result


def _common_policy(kind):
    stdout, stderr = _logs(kind)
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
            # Additional fixture containment only, divided between two units:
            # model+keeper total <=2GiB /150% CPU /128 tasks, not a new profile.
            'RuntimeMaxSec': '900',
            'MemoryMax': '1536M' if kind == 'model' else '512M',
            'MemorySwapMax': '0', 'TasksMax': '64',
            'CPUQuota': '100%' if kind == 'model' else '50%', 'CPUWeight': '10',
            'IOWeight': '10', 'Nice': '10', 'WorkingDirectory': str(SOURCE),
            'StandardOutput': stdout, 'StandardError': stderr,
            'UnsetEnvironment': 'HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY '
                                'http_proxy https_proxy all_proxy no_proxy PYTHONHOME '
                                'PYTHONSTARTUP PYTHONUSERBASE PYTHONINSPECT'}


def _start(unit, argv, policy, environment):
    need(_properties(unit).get('LoadState') == 'not-found',
         'Fixed native unit name already exists')
    command = ['/usr/bin/systemd-run', '--quiet', '--unit=' + _unit(unit)]
    for key, value in policy.items():
        command.append('--property=' + key + '=' + value)
    for key, value in environment.items():
        command.append('--setenv=' + key + '=' + value)
    command += ['--', *argv]
    result = _run(command, timeout=20)
    need(result['returncode'] == 0, 'Fixed native transient start failed')
    return {'unit': unit, 'requested_policy': policy,
            'properties': _properties(unit), 'direct_exec_argv': argv,
            'controller_output_sha256': digest(result['stdout'] + result['stderr'])}


def native_start_model(pins):
    """Start the independently supervised private namespace/model peer."""
    _ownership()
    expected = {'source_manifest_sha256', 'base_sha256', 'jobs_sha256',
                'cases_sha256', 'model_sha256'}
    need(type(pins) is dict and set(pins) == expected and
         all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)
             for value in pins.values()), 'Native source pin set differs')
    for path, key in ((LAB / 'inputs/SOURCE_MANIFEST.json', 'source_manifest_sha256'),
                      (HELPERS / 'keeper_runtime.py', 'base_sha256'),
                      (HELPERS / 'keeper_jobs.py', 'jobs_sha256'),
                      (HELPERS / 'job_cases.py', 'cases_sha256'),
                      (HELPERS / 'model_service.py', 'model_sha256')):
        _read(path, 2 * 1024 * 1024, expected=pins[key])
    for name, pin in (('cast', CAST_SHA), ('anvil', ANVIL_SHA)):
        _read(LAB / 'tools' / name, 128 * 1024 * 1024, expected=pin)
    need(_properties(MODEL_UNIT).get('LoadState') == 'not-found' and
         _properties(KEEPER_UNIT).get('LoadState') == 'not-found',
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
    for key in ('source_manifest_sha256', 'base_sha256', 'jobs_sha256', 'cases_sha256'):
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
             'cast_binary': str(LAB / 'tools/cast'), 'keystore': str(LIVE / 'secrets/keeper'), 'password_file': str(LIVE / 'secrets/password'), 'state_path': str(LIVE / 'state.json'),
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
    policy = _common_policy('keeper')
    policy.update(WatchdogSec='120s', TimeoutStopSec='120s', Restart='on-failure',
                  RestartSec='30s', NotifyAccess='main', WatchdogSignal='SIGKILL',
                  StartLimitIntervalSec='600s', StartLimitBurst='5',
                  JoinsNamespaceOf=MODEL_UNIT, Requires=MODEL_UNIT, After=MODEL_UNIT)
    environment = {'PATH': str(LAB / 'tools') + ':/usr/bin:/bin', 'LANG': 'C.UTF-8',
                   'PYTHONPATH': str(SOURCE), 'PYTHONDONTWRITEBYTECODE': '1',
                   'PYTHONUNBUFFERED': '1', 'PYTHONNOUSERSITE': '1',
                   'TMPDIR': str(MODEL / 'tmp'), 'HOME': str(LIVE / 'secrets')}
    argv = ['/usr/bin/python3', '-m', 'keeper.monitor', '--config', str(CONFIG), '--live']
    need(ready.get('monitor_argv') == argv and
         ready.get('monitor_working_directory') == str(SOURCE),
         'Native stock ExecStart differs from ready record')
    result = _start(KEEPER_UNIT, argv, policy, environment)
    _keeper_policy_checks(result['properties'])
    result['configuration_sha256'] = digest(raw)
    return result


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
    def __init__(self, baseline):
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
        need(any(row.get('UNIT_RESULT') == 'watchdog' or
                 re.search(r"failed with result ['\"]watchdog['\"]", 
                           row.get('MESSAGE', '').lower()) is not None
                 for row in keeper['manager_journal']),
             'Native manager watchdog outcome is absent')
        return {'schema': 1, 'old_invocation_id': self.old_invocation,
                'old_main_pid': self.old_main, 'old_processes': self.old_processes,
                'observed_empty_monotonic': self.empty_before_restart,
                'new_invocation': self.new_invocation, 'baseline': self.baseline,
                'samples': self.samples, 'final': final,
                'scope': 'sampled native cgroup cleanup and one stock keeper watchdog restart',
                'no_universal_fencing_or_total_elapsed_bound_claimed': True}
