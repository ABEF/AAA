"""NEW finite c818 native-timer composition; public fixtures, no financial work.

The root driver may manage only its fixed c818 units. Actual scheduler CLIs run
as nobody in the driver's private network namespace. Lab frequencies are not
production defaults. No old test body is selected or executed; fixture-module
and setup imports are explicit in the focused runner.
"""
from pathlib import Path
import base64
import configparser
import copy
import datetime as dt
import hashlib
import gzip
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import selectors
import signal
from socketserver import TCPServer
import stat
import subprocess
import sys
import threading
import time

LAB = Path('/opt/popl-keeper-scheduling-20261126-c818')
SOURCE = LAB / 'source'
RUNTIME = LAB / 'runtime'
PREFIX = 'popl-keeper-scheduling-20261126-c818'
ANCHOR = PREFIX + '.service'
JOBS = ('init', 'backup', 'observe', 'hold', 'checks', 'rebind')
UNITS = tuple(PREFIX + '-' + name + '.service' for name in JOBS)
TIMERS = (PREFIX + '-backup.timer', PREFIX + '-observe.timer')
PROPERTIES = ('Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,'
    'ExecMainStatus,ExecStart,User,Group,PrivateNetwork,JoinsNamespaceOf,Restart,KillMode,'
    'TimeoutStartUSec,TimeoutStopUSec,RemainAfterExit,MemoryMax,MemorySwapMax,TasksMax,'
    'ProtectSystem,ReadWritePaths,FragmentPath,TriggeredBy,Triggers,TimersMonotonic,'
    'AccuracyUSec,RandomizedDelayUSec,NextElapseUSecMonotonic,LastTriggerUSecMonotonic,'
    'BindReadOnlyPaths,IPAddressDeny,IPAddressAllow,StartLimitIntervalUSec,StartLimitBurst,References,PropagatesStopTo')
STARTED = []
PASSED = []
DETAILS = {}
COMMANDS = []
PROPERTIES_CAPTURE = {}
END = time.monotonic() + 165


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def compressed(value, maximum=256*1024):
    raw = encoded(value)
    need(len(raw) <= maximum, 'decoded_evidence_bound')
    return {'decoded_bytes': len(raw), 'decoded_sha256': sha(raw),
        'gzip_base64': base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii')}


def need(value, code='native_schedule_assertion'):
    if not value:
        raise ValueError(code)


def publish(name, value):
    need(name in ('PROGRESS.json', 'RESULT.json', 'WORKER_LOGS.json', 'MANAGER_TRACE.json', 'NATIVE_PROPERTIES.json'))
    raw = encoded(value)
    need(len(raw) <= 32768, 'evidence_bound')
    temp = RUNTIME / (name + '.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, RUNTIME / name)
    directory = os.open(RUNTIME, os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def progress(name, detail=None):
    need(name not in STARTED, 'scenario_repeated')
    STARTED.append(name)
    publish('PROGRESS.json', {'schema': 1, 'started': STARTED, 'passed': PASSED,
        'current': name, 'detail': detail, 'old_test_bodies_run': 0, 'production_approved': False})


def passed(name, detail):
    need(name == STARTED[-1] and name not in PASSED)
    PASSED.append(name)
    DETAILS[name] = detail
    publish('PROGRESS.json', {'schema': 1, 'started': STARTED, 'passed': PASSED,
        'current': None, 'old_test_bodies_run': 0, 'production_approved': False})


def run(argv, timeout=12):
    """Bound fixed manager/CLI process capture with correct child ownership."""
    need(time.monotonic() < END)
    need(argv[0] in ('/usr/bin/systemctl', '/usr/bin/systemd-run'))
    mask = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM}
    child = owned = None
    output = [bytearray(), bytearray()]
    size = 0
    end = min(END, time.monotonic() + timeout)
    try:
        # The receiver thread may be alive: never execute Python preexec_fn in
        # its forked child. Spawn unmasked; the fixed unit supervises descendants.
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'},
            start_new_session=True, close_fds=True)
        owned = child
        with selectors.DefaultSelector() as selector:
            for index, pipe in enumerate((child.stdout, child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, index)
            while selector.get_map():
                need(time.monotonic() < end, 'manager_deadline')
                for key, _ in selector.select(min(.1, max(.001, end-time.monotonic()))):
                    raw = os.read(key.fd, min(16384, 65537-size))
                    if not raw:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(raw)
                    need(size <= 65536, 'manager_output_bound')
                    output[key.data].extend(raw)
        while True:
            need(time.monotonic() < end, 'manager_deadline')
            prior = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
            try:
                try:
                    code = child.wait(timeout=min(.05, max(.001, end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    continue
                owned = None
                break
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, prior)
        COMMANDS.append({'program': Path(argv[0]).name, 'verb': argv[1],
            'owned_units': [arg for arg in argv if arg.startswith(PREFIX)], 'code': code,
            'argv_sha256': sha(encoded(argv)),
            'stdout_sha256': sha(output[0]), 'stderr_sha256': sha(output[1])})
        need(len(COMMANDS) <= 300, 'manager_call_bound')
        return code, bytes(output[0]), bytes(output[1])
    finally:
        if owned is not None:
            prior = signal.pthread_sigmask(signal.SIG_BLOCK, mask)
            try:
                if owned.returncode is None:
                    try:
                        os.killpg(owned.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                owned.wait(timeout=2)
                owned = None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, prior)
        if child is not None:
            child.stdout.close()
            child.stderr.close()


def manager(verb, *units, checked=True):
    need(verb in ('start', 'stop', 'reset-failed'))
    need(bool(units) and set(units) <= set((*UNITS, *TIMERS)))
    code, out, err = run(['/usr/bin/systemctl', verb, *units])
    if checked:
        need(code == 0, 'manager_action_refused')
    return code


def props(unit):
    need(unit in (*UNITS, *TIMERS, ANCHOR))
    code, out, err = run(['/usr/bin/systemctl', 'show', unit, '--no-pager', '--property=' + PROPERTIES])
    value = dict(line.split('=', 1) for line in out.decode('utf8', 'strict').splitlines() if '=' in line)
    need(code == 0 or code == 1 and value.get('LoadState') == 'not-found')
    entry = PROPERTIES_CAPTURE.setdefault(unit, {})
    if value.get('LoadState') != 'not-found' and 'first_existing' not in entry:
        entry['first_existing'] = value
    entry['last'] = value
    return value


def short_props(value):
    keep = ('Id', 'LoadState', 'ActiveState', 'SubState', 'MainPID', 'ControlGroup', 'Result',
        'ExecMainStatus', 'User', 'Group', 'PrivateNetwork', 'JoinsNamespaceOf', 'KillMode',
        'TimeoutStartUSec', 'TimeoutStopUSec', 'Restart', 'RemainAfterExit', 'TimersMonotonic',
        'AccuracyUSec', 'RandomizedDelayUSec', 'StartLimitIntervalUSec', 'StartLimitBurst')
    return {key: value[key] for key in keep if key in value and value[key] != ''}


def wait_for(predicate, seconds=15, label='wait_refused'):
    end = min(END, time.monotonic() + seconds)
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(.15)
    raise ValueError(label)


def empty_group(properties):
    if properties.get('MainPID', '0') != '0':
        return False
    group = properties.get('ControlGroup', '')
    if not group:
        return True
    need(group in ('/system.slice/' + unit for unit in (*UNITS, ANCHOR)))
    path = Path('/sys/fs/cgroup') / group.lstrip('/') / 'cgroup.procs'
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return True
    need(len(raw) <= 4096)
    return not raw.strip()


def idle_job(job):
    p = props(PREFIX + '-' + job + '.service')
    return p if empty_group(p) and p.get('SubState') in ('dead', 'failed', 'exited') else None


def stop_timers():
    for timer in TIMERS:
        if props(timer).get('LoadState') != 'not-found':
            manager('stop', timer)
    for job in ('backup', 'observe'):
        wait_for(lambda job=job: idle_job(job), label='job_not_idle')


def job_policy(job):
    value = {'Type': 'oneshot', 'User': 'nobody', 'Group': 'nogroup', 'PrivateNetwork': 'yes',
        'JoinsNamespaceOf': ANCHOR, 'After': ANCHOR, 'PrivateTmp': 'yes', 'PrivateDevices': 'yes',
        'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'NoNewPrivileges': 'yes',
        'ProtectKernelTunables': 'yes', 'ProtectKernelModules': 'yes', 'ProtectControlGroups': 'yes',
        'RestrictSUIDSGID': 'yes', 'LockPersonality': 'yes', 'CapabilityBoundingSet': '',
        'AmbientCapabilities': '', 'RestrictAddressFamilies': 'AF_UNIX AF_INET',
        'ReadWritePaths': str(RUNTIME), 'UMask': '0077', 'Restart': 'no',
        'RemainAfterExit': 'yes' if job in ('init', 'checks', 'rebind') else 'no',
        'TimeoutStartSec': '8' if job == 'hold' else '180', 'TimeoutStopSec': '2',
        'StartLimitIntervalSec': '0',
        'KillMode': 'control-group', 'SendSIGKILL': 'yes', 'FinalKillSignal': 'SIGKILL',
        'MemoryMax': '256M', 'MemorySwapMax': '0', 'TasksMax': '32', 'LimitCORE': '0',
        'LimitFSIZE': '65536', 'WorkingDirectory': str(SOURCE),
        'BindReadOnlyPaths': str(LAB / 'masks/key.empty') + ':' + str(RUNTIME / 'working/keystore.secret') + ' ' +
            str(LAB / 'masks/password.empty') + ':' + str(RUNTIME / 'working/password.secret'),
        'StandardOutput': 'append:' + str(RUNTIME / (job + '.stdout')),
        'StandardError': 'append:' + str(RUNTIME / (job + '.stderr'))}
    if job == 'observe':
        value.update(IPAddressDeny='any', IPAddressAllow='127.0.0.1/32')
    return value


def start_job(job, *, timer=None):
    need(job in JOBS)
    unit = PREFIX + '-' + job + '.service'
    need(props(unit).get('LoadState') == 'not-found', 'owned_unit_exists')
    argv = ['/usr/bin/systemd-run', '--quiet', '--no-block', '--unit=' + unit]
    if timer is not None:
        need(job in ('backup', 'observe') and timer in (3, 6))
        argv += ['--on-active=1s', '--on-unit-inactive=' + str(timer) + 's',
            '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0']
    for key, value in job_policy(job).items():
        argv.append('--property=' + key + '=' + value)
    for key, value in {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONPATH': str(SOURCE),
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'PYTHONUNBUFFERED': '1',
            'HOME': str(RUNTIME / 'home'), 'TMPDIR': str(RUNTIME / 'tmp')}.items():
        argv.append('--setenv=' + key + '=' + value)
    if job == 'hold':
        command = ['/usr/bin/python3', '-B', str(SOURCE / 'hold_lock.py')]
    elif job == 'checks':
        command = ['/usr/bin/python3', '-B', str(SOURCE / 'run_focused.py')]
    elif job == 'rebind':
        command = ['/usr/bin/python3', '-B', str(SOURCE / 'scripts/keeper-schedule.py'), job,
            '--policy', str(RUNTIME / 'policy-new.json'), '--policy-sha256', NEW_POLICY_PIN,
            '--previous-policy', str(RUNTIME / 'policy.json'), '--previous-policy-sha256', POLICY_PIN]
    else:
        command = ['/usr/bin/python3', '-B', str(SOURCE / 'scripts/keeper-schedule.py'), job,
            '--policy', str(RUNTIME / 'policy.json'), '--policy-sha256', POLICY_PIN]
    code, _, _ = run([*argv, '--', *command])
    need(code == 0, 'native_start_refused')
    p = props(unit)
    need(p.get('TimeoutStartUSec') == ('8s' if job == 'hold' else '3min'), 'effective_timeout')
    need(p.get('StartLimitIntervalUSec') in ('0', '0s'), 'effective_start_limit')
    need(p.get('User') == 'nobody' and p.get('Group') == 'nogroup' and
        p.get('PrivateNetwork') == 'yes' and p.get('JoinsNamespaceOf') == ANCHOR and
        p.get('KillMode') == 'control-group' and p.get('Restart') == 'no' and
        p.get('RemainAfterExit') == ('yes' if job in ('init', 'checks', 'rebind') else 'no'), 'effective_unit_policy')
    return short_props(p)


def call_job(job):
    unit = PREFIX + '-' + job + '.service'
    need(idle_job(job))
    manager('reset-failed', unit, checked=False)
    code = manager('start', unit, checked=False)
    p = wait_for(lambda: idle_job(job), label='manual_job_deadline')
    return code, p


def private_json(path, value, uid=65534, mode=0o600):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    need(len(raw) <= 65536)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(path, mode)
    os.chown(path, uid, uid)


def read_json(path):
    raw = path.read_bytes()
    need(len(raw) <= 65536)
    return json.loads(raw)


def source_health():
    from keeper.health import source_hashes
    return source_hashes()


def observations():
    return [HEALTH['lp_execution_health']['last_confirmed'],
        HEALTH['rebalance_confirmation_health']['policy']['last_observed']]


def health(*, pending=False, bad=False):
    now = int(time.time())
    stamp = dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat()
    HEALTH.update(time=stamp, last_success_at=stamp, chain_id=CONFIG['chain_id'],
        sender=CONFIG['sender'], status='awaiting_receipt' if pending else 'dry_run_v2',
        live=False, pending=pending,
        pending_action=STATE['pending']['key'] if pending else None,
        pending_day=STATE['pending']['day'] if pending else None,
        configuration_sha256=sha(encoded(CONFIG).rstrip(b'\n')), strategy_paused=False,
        canonical_state=0, preparation_active=False, consecutive_failures=int(bad),
        skipped_buckets=0, blocked_actions=0, confirmed_reverts=0,
        active_revert_cooldowns=0, next_revert_retry_after=None)
    for observation in observations():
        observation.update(configuration_sha256=HEALTH['configuration_sha256'],
            source_files_sha256=source_health(), block_timestamp=now-2, observed_at_unix=now-1)
    private_json(Path(CONFIG['health_path']), HEALTH)


def fixture(receiver):
    global CONFIG, HEALTH, STATE, ORIGINAL_JOURNAL, POLICY_PIN, PENDING_VECTOR
    from keeper import scheduling
    work = RUNTIME / 'working'
    work.mkdir(mode=0o700)
    os.chown(work, 65534, 65534)
    runtime = work / 'runtime'
    runtime.mkdir(mode=0o700)
    os.chown(runtime, 65534, 65534)
    journal_vector = read_json(SOURCE / 'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json')
    PENDING_VECTOR = json.loads(journal_vector['journal_raw_utf8'])
    STATE = copy.deepcopy(PENDING_VECTOR)
    STATE.update(sender='0x' + '35'*20, pending=None, next_nonce=0, receipt_anchor=None, spent={})
    CONFIG = {'chain_id': 4663, 'accounting_model': 'shared-pools-v2', 'sender': STATE['sender'],
        'contracts': copy.deepcopy(STATE['contracts']), 'accounting_version': 7, 'custody_version': 5,
        'fee_intake_version': 1, 'royalty_settlement_version': 4, 'portfolio_version': 2,
        'maintenance_policy_version': 3, 'rebalance_confirmation_version': 3,
        'execution_quality_version': 1, 'protocol_policy_version': 1, 'lp_routing_version': 3,
        'execution_price_version': 1, 'rpc_urls': ['https://offline.invalid/no-network'],
        'state_path': str(runtime / 'journal.json'), 'health_path': str(runtime / 'health.json'),
        'lock_path': str(runtime / 'keeper.lock'), 'keystore': str(work / 'keystore.secret'),
        'password_file': str(work / 'password.secret'), 'reviewed_for_live_use': False,
        'interval_seconds': 240, 'confirmations': 12, 'max_gas_limit': 24000000,
        'max_gas_price_wei': '5000000000', 'max_transaction_cost_wei': '10000000000000000',
        'max_daily_cost_wei': '50000000000000000', 'l1_fee_allowance_wei': '0',
        'receipt_fee_policy': 'included',
        'idle_compounding_budget': '0x596b344ab09a470bc468753e7bd3dc0a9fc5ebc1',
        'maintenance': {'compound': False, 'compound_idle': False, 'harvest': True,
            'minimum_liquidity': 1, 'harvest_interval_seconds': 3600},
        'metadata_refresh': {'enabled': False}, 'royalty_conversion': {'enabled': False},
        'lp_conversion': {'enabled': False}, 'principal_distribution': {'enabled': False},
        'adaptive_range': {'enabled': False}, 'bucket_overrides': {}, 'buybacks': []}
    HEALTH = copy.deepcopy(read_json(SOURCE / 'reports/ubuntu-backup-recovery-20261126/evidence/c814/model-DRY.json')['health'])
    CONFIG['code_hashes'] = {name: '0x' + '11'*32 for name in STATE['contracts']}
    for row in observations():
        CONFIG['code_hashes'].update(row['runtime_code_hashes'])
    private_json(RUNTIME / 'keeper-config.json', CONFIG)
    private_json(Path(CONFIG['state_path']), STATE)
    ORIGINAL_JOURNAL = Path(CONFIG['state_path']).read_bytes()
    for name in ('keystore.secret', 'password.secret'):
        path = work / name
        path.write_bytes(b'DISPOSABLE-NOT-A-SIGNER-SECRET\n')
        os.chmod(path, 0)
    health()
    policy = {'schema': 1, 'kind': 'popl-keeper-schedule',
        'configuration': str(RUNTIME / 'keeper-config.json'),
        'configuration_sha256': sha((RUNTIME / 'keeper-config.json').read_bytes()),
        'working_directory': str(work), 'scheduler_directory': str(RUNTIME / 'schedule'),
        'backup_directory': str(RUNTIME / 'backups'), 'alert_directory': str(RUNTIME / 'alerts'),
        'source_files_sha256': {name: sha((SOURCE / name).read_bytes()) for name in scheduling.SOURCE_FILES},
        'max_backups': 32, 'max_health_age_seconds': 120, 'max_backup_age_seconds': 8,
        'pending_max_age_seconds': 120, 'receiver': receiver, 'allow_dry_run': True,
        'max_bytes': 16777216, 'max_seconds': 60}
    private_json(RUNTIME / 'policy.json', policy, uid=0, mode=0o444)
    POLICY_PIN = sha((RUNTIME / 'policy.json').read_bytes())


def template_bindings():
    rows = {}
    fixed = {'Type': 'oneshot', 'Restart': 'no', 'RemainAfterExit': 'no',
        'TimeoutStartSec': '180s', 'TimeoutStopSec': '2s', 'KillMode': 'control-group',
        'SendSIGKILL': 'yes', 'FinalKillSignal': 'SIGKILL', 'LimitCORE': '0',
        'UMask': '0077', 'NoNewPrivileges': 'yes', 'PrivateTmp': 'yes',
        'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'PrivateDevices': 'yes',
        'ProtectKernelTunables': 'yes', 'ProtectKernelModules': 'yes',
        'ProtectControlGroups': 'yes', 'RestrictSUIDSGID': 'yes',
        'LockPersonality': 'yes', 'CapabilityBoundingSet': ''}
    for job, name in (('backup', 'backup'), ('observe', 'observer')):
        source = SOURCE / ('keeper/zzz-keeper-' + name + '.service')
        parser = configparser.ConfigParser(interpolation=None, strict=True)
        parser.optionxform = str
        parser.read_string(source.read_text())
        need(parser['Unit']['StartLimitIntervalSec'] == '0', 'template_retry_policy')
        need(all(parser['Service'][k] == v for k, v in fixed.items()), 'template_shared_policy')
        need('keeper-schedule.py ' + job + ' --policy ' in parser['Service']['ExecStart'])
        rows[job] = {'source': str(source.relative_to(SOURCE)), 'source_sha256': sha(source.read_bytes()),
            'preserved_template_values': fixed,
            'lab_overrides': ['User/Group=nobody/nogroup', 'fixed lab paths/private writable root',
                'literal policy/pin arguments instead of EnvironmentFile', 'private shared namespace',
                'bounded append logs instead of journal', 'extra resource/file limits'],
            'lab_native_policy': job_policy(job)}
    return rows


class Receiver(HTTPServer):
    allow_reuse_address = True

    def server_bind(self):
        TCPServer.server_bind(self)
        self.server_name, self.server_port = '127.0.0.1', self.server_address[1]


RECEIVED = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        need(self.path == '/alerts')
        size = int(self.headers['Content-Length'])
        need(0 < size <= 2048)
        body = json.loads(self.rfile.read(size))
        need(body['unsigned'] is True and body['readiness_approved'] is False)
        RECEIVED.append(body)
        need(len(RECEIVED) <= 64)
        raw = encoded({'event_id': body['event_id'], 'accepted': True})
        self.send_response(200)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def receiver(port=0):
    server = Receiver(('127.0.0.1', port), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
    thread.start()
    return server, thread


def close_receiver(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
    need(not thread.is_alive())


def selected():
    return (RUNTIME / 'schedule/selected.json').read_bytes()


def alert_state():
    return read_json(RUNTIME / 'alerts/state.json')


def successful_runs(job):
    path = RUNTIME / (job + '.stdout')
    records = []
    for line in path.read_bytes().splitlines():
        need(len(line) <= 16384)
        value = json.loads(line)
        if value.get('ok') is True:
            records.append(value)
    return records


def last_cli(job):
    lines = (RUNTIME / (job + '.stdout')).read_bytes().splitlines()
    need(bool(lines), 'missing_cli_record')
    value = json.loads(lines[-1])
    need(type(value) is dict)
    return value


def main():
    global END, NEW_POLICY_PIN
    need(os.getuid() == 0 and os.readlink('/proc/self/ns/net') != os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'])
    need(not (RUNTIME / 'RESULT.json').exists(), 'no_replay')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SOURCE))
    started = time.monotonic()
    original_before = None
    server = thread = None
    cleanup = False
    result = {'schema': 1, 'success': False, 'old_test_bodies_run': 0,
        'public_transactions': 0, 'signer_contents_read': False, 'production_approved': False}
    try:
        server, thread = receiver()
        port = server.server_port
        fixture('http://127.0.0.1:' + str(port) + '/alerts')
        original_before = sha(ORIGINAL_JOURNAL)
        progress('new_focused_scheduler_methods')
        checks_props = start_job('checks')
        wait_for(lambda: idle_job('checks'), seconds=25, label='focused_selection_deadline')
        checks = read_json(RUNTIME / 'FOCUSED_RESULT.json')
        need(checks.get('success') is True and checks['old_test_bodies_run'] == 0, 'focused_selection_failed')
        passed('new_focused_scheduler_methods', {'properties': checks_props,
            'selected_methods': checks['selected_methods'], 'passes': checks['tests_run']})

        progress('explicit_bootstrap')
        bindings = template_bindings()
        init_props = start_job('init')
        wait_for(lambda: idle_job('init'))
        need(props(PREFIX + '-init.service').get('ExecMainStatus') == '0', 'init_cli_failed')
        need(read_json(RUNTIME / 'alerts/state.json')['outbox'] == [])
        first = selected()
        passed('explicit_bootstrap', {'init_properties': init_props, 'selected_sha256': sha(first),
            'maintained_template_bindings': bindings})

        progress('native_repeating_timers')
        backup_props = start_job('backup', timer=6)
        observe_props = start_job('observe', timer=3)
        wait_for(lambda: len(successful_runs('backup')) >= 2 and len(successful_runs('observe')) >= 2,
            seconds=22, label='native_repetition_missing')
        stop_timers()
        need(selected() != first, 'no_rotation')
        need(len(list((RUNTIME / 'backups').iterdir())) >= 3)
        need(alert_state()['outbox'] == [] and alert_state()['active'] == {})
        passed('native_repeating_timers', {'backup_properties': backup_props,
            'observe_properties': observe_props, 'backup_timer': short_props(props(TIMERS[0])),
            'observe_timer': short_props(props(TIMERS[1])), 'backup_successes': len(successful_runs('backup')),
            'observe_successes': len(successful_runs('observe'))})

        progress('shared_lock_and_hard_timeout')
        prior = selected()
        hold_props = start_job('hold')
        ready = wait_for(lambda: (RUNTIME / 'HOLD_READY.json').exists())
        holder = read_json(RUNTIME / 'HOLD_READY.json')
        busy_records = {}
        for job in ('backup', 'observe'):
            need(call_job(job)[0] != 0, 'overlap_accepted')
            busy_records[job] = last_cli(job)
            need(busy_records[job].get('refusal_code') == 'scheduler_lock', 'wrong_overlap_refusal')
            need(props(PREFIX + '-hold.service').get('MainPID') == str(holder['parent_pid']), 'holder_expired_early')
        need(selected() == prior, 'busy_selection_changed')
        stopped = wait_for(lambda: idle_job('hold'), seconds=12, label='hard_timeout_missing')
        need(stopped.get('Result') == 'timeout' and empty_group(stopped), 'timeout_not_empty')
        wait_for(lambda: all(not Path('/proc/' + str(holder[k])).exists() for k in ('parent_pid', 'child_pid')),
            seconds=3, label='timeout_descendant_survived')
        need(call_job('backup')[0] == 0, 'lock_not_released_for_backup')
        code, _ = call_job('observe')
        need(code == 0, 'lock_not_released')
        passed('shared_lock_and_hard_timeout', {'effective': hold_props,
            'timed_out': short_props(stopped), 'inert_pids': holder,
            'busy_refusals': busy_records, 'selection_unchanged': True})

        progress('failed_backup_retains_selected')
        prior = selected()
        journal = Path(CONFIG['state_path'])
        original = journal.read_bytes()
        journal.write_bytes(b'{"not_a_supported_journal":true}\n')
        try:
            code, failure = call_job('backup')
            need(code != 0 and selected() == prior, 'failed_rotation_promoted')
            refusal = last_cli('backup')
            need(refusal.get('refusal_code') == 'backup_capture' and
                refusal.get('cause_code') == 'journal_envelope', 'wrong_backup_failure')
        finally:
            journal.write_bytes(original)
        passed('failed_backup_retains_selected', {'failure': short_props(failure),
            'refusal': refusal, 'selection_sha256': sha(prior)})

        progress('missed_backup_stale_then_recovery')
        health()
        # Backup timer stays stopped; observer timer alone must detect staleness.
        manager('start', TIMERS[1])
        wait_for(lambda: 'backup_stale' in alert_state()['active'], seconds=17, label='stale_backup_not_observed')
        stop_timers()
        stale_id = alert_state()['active']['backup_stale']
        need(any(e['event_id'] == stale_id and e['type'] == 'incident' for e in RECEIVED))
        health()
        need(call_job('backup')[0] == 0, 'fresh_backup_failed')
        need(call_job('observe')[0] == 0, 'fresh_recovery_failed')
        need(alert_state()['active'] == {} and alert_state()['outbox'] == [])
        need(any(e['reason_code'] == 'backup_stale' and e['type'] == 'recovery' for e in RECEIVED))
        passed('missed_backup_stale_then_recovery', {'stale_event_id': stale_id,
            'actual_receiver_recovery': True, 'stopped_backup_timer': short_props(props(TIMERS[0]))})

        progress('receiver_outage_restart_and_pending_age')
        close_receiver(server, thread)
        server = thread = None
        STATE['pending'] = copy.deepcopy(PENDING_VECTOR['pending'])
        STATE['pending']['hash'] = '0x' + '29'*32
        STATE['next_nonce'] = STATE['pending']['nonce']
        private_json(Path(CONFIG['state_path']), STATE)
        health(pending=True, bad=True)
        need(call_job('backup')[0] == 0)
        need(call_job('observe')[0] != 0)
        failed = alert_state()
        first_seen = failed['pending']['first_seen']
        queued = [e['event_id'] for e in failed['outbox']]
        need(bool(queued), 'receiver_outage_not_queued')
        manager('start', TIMERS[1])
        wait_for(lambda: alert_state()['last_observed_at'] > failed['last_observed_at'], seconds=7)
        stop_timers()
        after = alert_state()
        need(after['pending']['first_seen'] == first_seen and
            [e['event_id'] for e in after['outbox']][:len(queued)] == queued, 'restart_lost_pending_or_ids')
        server, thread = receiver(port)
        seen_before = len(RECEIVED)
        need(call_job('observe')[0] != 0)
        after = alert_state()
        need(after['pending']['first_seen'] == first_seen and after['outbox'] == [])
        need(set(queued) <= {e['event_id'] for e in RECEIVED[seen_before:]}, 'queued_ids_not_redelivered')
        STATE['pending'] = None
        STATE['next_nonce'] = 0
        private_json(Path(CONFIG['state_path']), STATE)
        health()
        need(call_job('backup')[0] == 0 and call_job('observe')[0] == 0)
        need(alert_state()['pending'] is None and alert_state()['active'] == {} and alert_state()['outbox'] == [])
        passed('receiver_outage_restart_and_pending_age', {'preserved_first_seen': first_seen,
            'queued_ids_redelivered': queued, 'clear_requires_explicit_valid_no_pending': True})

        progress('explicit_policy_rebind_preserves_pending_state')
        old_selected = read_json(RUNTIME / 'schedule/selected.json')
        old_alert = (RUNTIME / 'alerts/state.json').read_bytes()
        new_policy = read_json(RUNTIME / 'policy.json')
        new_policy['max_health_age_seconds'] = 121
        private_json(RUNTIME / 'policy-new.json', new_policy, uid=0, mode=0o444)
        NEW_POLICY_PIN = sha((RUNTIME / 'policy-new.json').read_bytes())
        rebind_props = start_job('rebind')
        wait_for(lambda: idle_job('rebind'), label='rebind_cli_deadline')
        need(props(PREFIX + '-rebind.service').get('ExecMainStatus') == '0', 'rebind_cli_failed')
        rebound = read_json(RUNTIME / 'schedule/selected.json')
        need(rebound == {**old_selected, 'policy_sha256': NEW_POLICY_PIN}, 'rebind_changed_backup_identity')
        need((RUNTIME / 'alerts/state.json').read_bytes() == old_alert, 'rebind_changed_alert_state')
        passed('explicit_policy_rebind_preserves_pending_state', {'properties': rebind_props,
            'previous_policy_pin': POLICY_PIN, 'new_policy_pin': NEW_POLICY_PIN,
            'only_selection_policy_pin_changed': True})

        progress('final_stop_and_preservation')
        stop_timers()
        need(Path(CONFIG['state_path']).read_bytes() == ORIGINAL_JOURNAL, 'fixture_journal_not_restored')
        need(sha((RUNTIME / 'keeper-config.json').read_bytes()) == read_json(RUNTIME / 'policy.json')['configuration_sha256'])
        for name in ('keystore.secret', 'password.secret'):
            st = (RUNTIME / 'working' / name).stat()
            need(st.st_uid == 0 and stat.S_IMODE(st.st_mode) == 0)
        states = {unit: props(unit) for unit in (*UNITS, *TIMERS)}
        need(all(empty_group(states[unit]) for unit in UNITS))
        need(all(states[timer].get('ActiveState') == 'inactive' for timer in TIMERS))
        passed('final_stop_and_preservation', {'final_unit_properties': {k: short_props(v) for k, v in states.items()},
            'fixture_journal_sha256': sha(ORIGINAL_JOURNAL), 'signer_placeholders_inaccessible': True})
        cleanup = True
        result['success'] = True
    except BaseException as exc:
        result['error_type'] = type(exc).__name__
        result['error_code'] = str(exc) if isinstance(exc, ValueError) and str(exc).replace('_', '').isalnum() else 'scoped_failure'
    finally:
        # Preserve results before the outer controller stops the namespace.
        try:
            for timer in TIMERS:
                if props(timer).get('LoadState') != 'not-found':
                    manager('stop', timer, checked=False)
            for unit in UNITS:
                if props(unit).get('LoadState') != 'not-found':
                    manager('stop', unit, checked=False)
            cleanup = all(empty_group(props(unit)) for unit in UNITS)
        except BaseException as exc:
            result['cleanup_error_type'] = type(exc).__name__
        if server is not None:
            try:
                close_receiver(server, thread)
            except BaseException as exc:
                result['receiver_cleanup_error_type'] = type(exc).__name__
                cleanup = False
        final_journal = None
        if 'CONFIG' in globals():
            try:
                final_journal = sha(Path(CONFIG['state_path']).read_bytes())
            except BaseException as exc:
                result['final_journal_capture_error_type'] = type(exc).__name__
        result.update(started_scenarios=STARTED, passed_scenarios=PASSED, scenario_details=DETAILS,
            cleanup=cleanup, elapsed_seconds=time.monotonic()-started,
            receiver_event_count=len(RECEIVED), receiver_events=compressed(RECEIVED), manager_command_count=len(COMMANDS),
            manager_commands_sha256=sha(encoded(COMMANDS)), initial_fixture_journal_sha256=original_before,
            final_fixture_journal_sha256=final_journal,
            explicit_fixture_seam='public historical JSON with fresh wall-clock and current source identities; no chain',
            lab_intervals_seconds={'backup': 6, 'observe': 3, 'backup_age': 8},
            actual_provider_or_offhost_qualified=False)
        publish('RESULT.json', result)
        logs = {}
        for job in JOBS:
            for channel in ('stdout', 'stderr'):
                path = RUNTIME / (job + '.' + channel)
                if not path.exists():
                    logs[job + '.' + channel] = {'capture_state': 'not_created'}
                    continue
                raw = path.read_bytes()
                need(len(raw) <= 65536)
                raw.decode('utf8', 'strict')
                logs[job + '.' + channel] = {'bytes': len(raw), 'sha256': sha(raw),
                    'gzip_base64': base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii')}
        publish('WORKER_LOGS.json', {'schema': 1, 'logs': logs, 'credential_values_included': False})
        command_raw = encoded(COMMANDS)
        need(len(command_raw) <= 256*1024, 'decoded_trace_bound')
        publish('MANAGER_TRACE.json', {'schema': 1, 'command_count': len(COMMANDS),
            'decoded_bytes': len(command_raw), 'decoded_sha256': sha(command_raw),
            'gzip_base64': base64.b64encode(gzip.compress(command_raw, mtime=0)).decode('ascii'),
            'only_fixed_c818_manager_actions': True, 'public_transactions': 0})
        publish('NATIVE_PROPERTIES.json', {'schema': 1, 'units': compressed(PROPERTIES_CAPTURE),
            'first_existing_and_last_captured': True})
    print(json.dumps({'c818_success': result['success'], 'new_scenarios_passed': len(PASSED), 'cleanup': cleanup}))
    return 0 if result['success'] and cleanup else 1


if __name__ == '__main__':
    raise SystemExit(main())
