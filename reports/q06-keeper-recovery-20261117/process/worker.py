"""Isolated Linux process evidence, CURRENT Keeper7 and INERT HTTP/Cast.

This is a test-only process harness, never a keeper deployment or real signer.
It imports fixture constructors, not unittest cases. Production Keeper guards,
JSON transport, lock, durable writes, fee review and receipt recovery are real.
All contracts, prices, receipts and runtime pins are synthetic wire responses.
The executable called Cast cannot sign or submit: it returns a fixed address/hash
or stalls so a separately owned systemd supervisor can exercise containment.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import threading
import time

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from keeper.monitor import Keeper, FEES_COLLECTED_TOPIC
from keeper.watchdog import ProgressRPC, ProgressWatchdog
from tests_python.test_keeper_maintenance_clock import CurrentCycleRPC
from zzz_ops.abi import calldata
from zzz_ops.execution_price import ROLES
from zzz_ops.rpc import Rpc
from zzz_ops.state import atomic_json, process_lock, read_json

HASH = '0x' + 'ac' * 32
BLOCK_HASH = '0x' + 'ab' * 32
SCOPE = ('current Keeper7 process/HTTP/durability with inert synthetic contracts '
         'and no signing, broadcast, Anvil, target-chain or economic assurance')


def source_pool():
    paths = {Path(__file__).resolve()}
    for directory in ('scripts', 'keeper', 'zzz_ops', 'tests_python', 'frontend_api', 'indexer'):
        paths.update(p for p in (REPO / directory).rglob('*.py') if '__pycache__' not in p.parts)
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def private_write(path, value, *, executable=False):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700 if executable else 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())


def marker(root, name, **values):
    atomic_json(root / (name + '.json'), {'pid': os.getpid(), 'time': time.time(), **values})


def runtime_metadata(watchdog):
    return {'python_version': platform.python_version(), 'python_executable': sys.executable,
            'os_name': os.name, 'kernel': platform.release(), 'uid': os.getuid(),
            'pid': os.getpid(), 'watchdog_enabled': watchdog.enabled,
            'watchdog_seconds': watchdog.seconds, 'watchdog_cadence_seconds': watchdog.cadence,
            'transport_attempt_complete_registered': watchdog.enabled,
            'syscall_scope': 'real HTTP sockets/flock/fsync/Unix datagrams/processes; synthetic contract/signing data'}


def log_line(path, value):
    # Only synthetic loopback payloads enter this new owned transcript.
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n'
    if len(raw) > 256_000:
        raise ValueError('Harness transcript row exceeds bound')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def inert_cast(argv):
    """Executable child; deliberately knows no private key or signing library."""
    if '--keystore' not in argv:
        raise ValueError('Inert Cast requires its owned placeholder path')
    root = Path(argv[argv.index('--keystore') + 1]).resolve().parent
    cfg = read_json(root / 'config.json')
    if argv[:2] == ['wallet', 'address']:
        log_line(root / 'cast-calls.jsonl', {'kind': 'wallet_address', 'pid': os.getpid()})
        print(cfg['sender'], flush=True)
        return 0
    if not argv or argv[0] != 'send':
        raise ValueError('Inert Cast implements no other operation')
    allowed = {'--from', '--keystore', '--password-file', '--chain', '--nonce', '--gas-limit',
               '--gas-price', '--value', '--async', '--json', '--priority-gas-price'}
    # Reject accidental broadening beyond the production send envelope used here.
    if any(arg.startswith('--') and arg not in allowed for arg in argv):
        raise ValueError('Unexpected inert Cast argument')
    state = read_json(root / 'state.json')
    pending = state.get('pending')
    if not pending or pending['hash'] is not None or pending['fee_review']['schema'] != 2:
        raise ValueError('Signer reached without durable schema2 hashless intent')
    log_line(root / 'cast-calls.jsonl', {'kind': 'send_inert', 'pid': os.getpid(),
             'nonce': pending['nonce'], 'durable_pending_sha256': hashlib.sha256((root / 'state.json').read_bytes()).hexdigest()})
    marker(root, 'signer_ready', parent=os.getppid(), pending_hashless=True)
    if (root / 'signer_stall.flag').exists():
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        grandchild = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
            '--grandchild', str(root)], start_new_session=True, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        marker(root, 'signer_descendants', signer=os.getpid(), grandchild=grandchild.pid)
        while True:
            time.sleep(1)
    until = time.monotonic() + 240
    while not (root / 'allow_hash.flag').exists():
        if time.monotonic() >= until:
            raise TimeoutError('Inert hash-release barrier timed out')
        time.sleep(0.05)
    print(json.dumps({'transactionHash': HASH}), flush=True)
    return 0


class Wire(CurrentCycleRPC):
    """Current fixture graph behind REAL production HTTP decoding and RPC pins."""
    def __init__(self, root):
        super().__init__(root / 'state.json')
        self.root = root
        self.now = read_json(root / 'clock.json')['timestamp']
        self.position[6] = self.now - 50_000
        self.physical_side = self.reference = 0
        self.price = 10
        self.cfg.update(chain_id=4663, custody_version=5, royalty_settlement_version=4,
            execution_price_version=1, lp_routing_version=3, submission_fee_profile=2,
            receipt_fee_policy='included', l1_fee_allowance_wei=0,
            reviewed_for_live_use=True, principal_distribution={'enabled': False},
            royalty_conversion={'enabled': False}, lp_conversion={'enabled': False},
            max_gas_limit=100_000, max_gas_price_wei=100,
            max_transaction_cost_wei=1_000_000, max_daily_cost_wei=10_000_000,
            confirmations=2, interval_seconds=240,
            keystore=str(root / 'inert-keystore.json'), password_file=str(root / 'inert-password'),
            cast_binary=str(root / 'inert-cast'), health_path=str(root / 'health.json'),
            lock_path=str(root / 'keeper.lock'))
        self.cfg['maintenance'].update(compound=False, compound_idle=False, harvest=True,
                                      harvest_interval_seconds=3600)
        for role, index in (('oracle', 15501), ('contribution_pricing', 15502)):
            self.contracts[role] = '0x' + f'{index:040x}'
            self.cfg['code_hashes'][role] = self.pin
        self.replies = {}
        def add(role, signature, value):
            self.replies[self.contracts[role], calldata(signature)] = '0x' + f'{value:064x}'
        for role in ROLES + ('lp_balance_math',):
            add(role, 'EXECUTION_PRICE_VERSION()', 1)
        for role in ('liquidity', 'balancing_router'):
            add(role, 'LP_ROUTING_VERSION()', 3)
        add('liquidity', 'executionStrategy()', int(self.contracts['lp_balance_math'], 16))
        for role in ('oracle', 'contribution_pricing'):
            add(role, 'access()', int(self.contracts['access'], 16))
        add('oracle', 'contributionPricing()', int(self.contracts['contribution_pricing'], 16))
        add('contribution_pricing', 'oracle()', int(self.contracts['oracle'], 16))
        add('oracle', 'executionActive()', 0)
        add('oracle', 'executionSourceRevision()', 3)

    def call(self, method, params):
        if method == 'eth_chainId':
            return hex(4663)
        if method == 'eth_getTransactionCount':
            return hex(1 if (self.root / 'included.flag').exists() else 0)
        if method == 'eth_getBlockByNumber':
            return {'number': '0x64' if params[0] == 'latest' else params[0],
                    'hash': BLOCK_HASH, 'timestamp': hex(self.now), 'baseFeePerGas': '0x3',
                    'gasLimit': hex(32_000_000)}
        if method in ('eth_getTransactionReceipt', 'eth_getTransactionByHash'):
            if params != [HASH] or not (self.root / 'included.flag').exists():
                return None
            pending = read_json(self.root / 'receipt-pending.json')
            common = {'transactionHash': HASH, 'blockNumber': '0x63', 'blockHash': BLOCK_HASH,
                'transactionIndex': '0x0', 'from': self.cfg['sender'], 'to': self.contracts['vault']}
            if method == 'eth_getTransactionByHash':
                return {key: value for key, value in common.items() if key != 'transactionHash'} | {
                    'hash': HASH, 'nonce': hex(pending['nonce']), 'input': pending['data'],
                    'value': hex(pending['value']), 'gas': hex(pending['fee_review']['gas_limit']),
                    'type': '0x2', 'chainId': hex(4663),
                    'maxFeePerGas': hex(pending['fee_review']['max_fee_per_gas']),
                    'maxPriorityFeePerGas': '0x0'}
            event = {**common, 'address': self.contracts['vault'], 'logIndex': '0x0',
                'removed': False, 'topics': [FEES_COLLECTED_TOPIC, '0x' + f'{7:064x}'],
                'data': '0x' + f'{80:064x}{20:064x}'}
            return {**common, 'status': '0x1', 'gasUsed': '0x64',
                    'effectiveGasPrice': '0x3', 'logs': [event]}
        if method == 'eth_call' and 'from' not in params[0]:
            key = (params[0]['to'], params[0]['data'])
            if key in self.replies:
                return self.replies[key]
        return super().call(method, params)


class Server:
    def __init__(self, root, wire):
        self.root, self.wire = root, wire
        self.stall = False
        self.sequence = 0
        self.mutex = threading.Lock()
        outer = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass
            def do_POST(self):
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 128_000:
                    self.send_error(413)
                    return
                request = json.loads(self.rfile.read(length))
                with outer.mutex:
                    outer.sequence += 1
                    seq = outer.sequence
                log_line(root / 'rpc.jsonl', {'sequence': seq, 'request': request})
                if outer.stall:
                    # Deliberately incomplete header: each byte arrives within
                    # socket inactivity timeout, but HTTP header parsing never
                    # completes. The actual client's transport-completion hook
                    # cannot pulse during this blocked opener.read boundary.
                    self.connection.sendall(b'HTTP/1.1 200 OK\r\nX-Inert-Stall: ')
                    marker(root, 'rpc_stalled', method=request['method'], sequence=seq,
                           stall_kind='incomplete_header_one_byte_each_second',
                           ordinary_socket_timeout_seconds=60, maximum_stall_seconds=600)
                    until = time.monotonic() + 600
                    try:
                        while time.monotonic() < until:
                            time.sleep(1)
                            self.connection.sendall(b'.')
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    return
                try:
                    result = wire.call(request['method'], request.get('params', []))
                    response = {'jsonrpc': '2.0', 'id': request['id'], 'result': result}
                except Exception as error:
                    # Fixture gaps remain explicit failures, never successful zeroes.
                    marker(root, 'wire_error', method=request.get('method'), error_type=type(error).__name__)
                    response = {'jsonrpc': '2.0', 'id': request.get('id'),
                        'error': {'code': -32000, 'message': 'Inert fixture has no valid reply'}}
                log_line(root / 'rpc.jsonl', {'sequence': seq, 'response': response})
                raw = json.dumps(response, separators=(',', ':')).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--mode', required=True, choices=('prepare', 'submit', 'recover',
        'hashless', 'rpc-stall', 'signer-stall', 'stop-intent', 'lock-hold', 'lock-contend', 'serve', 'describe'))
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.mode == 'describe':
        print(json.dumps({'scope': SCOPE, 'modes': parser._option_string_actions['--mode'].choices}))
        return 0
    if os.name != 'posix' or os.getuid() == 0:
        raise ValueError('Run only as an unprivileged Linux user')
    if not root.is_dir() or root.is_symlink() or root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise ValueError('Root must be a new owned mode0700 directory')
    before = source_pool()
    if args.mode == 'prepare':
        if (root / 'clock.json').exists():
            raise ValueError('Preparation never overwrites an existing scenario')
        atomic_json(root / 'clock.json', {'timestamp': int(time.time())})
        private_write(root / 'inert-keystore.json', 'INERT PLACEHOLDER - NOT AN ENCRYPTED WALLET\n')
        private_write(root / 'inert-password', 'INERT PLACEHOLDER - NO CREDENTIAL\n')
        launch = '#!' + sys.executable + '\nimport runpy,sys\nsys.argv=[' + repr(str(Path(__file__).resolve())) + ", '--inert-cast']+sys.argv[1:]\nrunpy.run_path(" + repr(str(Path(__file__).resolve())) + ",run_name='__main__')\n"
        private_write(root / 'inert-cast', launch, executable=True)
    wire = Wire(root)
    server = Server(root, wire)
    wire.cfg['rpc_urls'] = [server.url]
    atomic_json(root / 'config.json', wire.cfg)
    watchdog = ProgressWatchdog.from_environment()
    watchdog.pulse(force=True)
    runtime = runtime_metadata(watchdog)
    try:
        if args.mode == 'prepare':
            # Production initialization checks actual HTTP pins/getters/nonces.
            keeper = Keeper(wire.cfg, rpc=ProgressRPC(Rpc([server.url], 4663,
                transport_attempt_complete=watchdog.pulse if watchdog.enabled else None), watchdog))
            keeper.initialize_state()
            marker(root, 'prepared', sender=keeper.sender, scope=SCOPE,
                   configuration_sha256=keeper.configuration_sha256, runtime=runtime)
        elif args.mode in ('lock-hold', 'lock-contend'):
            with process_lock(wire.cfg['lock_path']):
                marker(root, 'lock_acquired', mode=args.mode)
                if args.mode == 'lock-hold':
                    while True:
                        watchdog.pulse()
                        time.sleep(0.2)
        else:
            with process_lock(wire.cfg['lock_path']):
                transport = Rpc([server.url], 4663, timeout=60, retries=1,
                    transport_attempt_complete=watchdog.pulse if watchdog.enabled else None)
                keeper = Keeper(wire.cfg, live=True, rpc=ProgressRPC(transport, watchdog))
                watchdog.pulse(force=True)
                marker(root, 'live_ready', scope=SCOPE, accounting_version=keeper.accounting_version,
                       custody_version=keeper.custody_version, execution_price_version=keeper.execution_price_version,
                       runtime=runtime)
                if args.mode == 'rpc-stall':
                    server.stall = True
                    keeper.run_cycle()
                    raise AssertionError('Stalled RPC unexpectedly completed')
                elif args.mode == 'stop-intent':
                    # Fault injection is ONLY a barrier after the original real
                    # durable save. No signer/validation/guard is replaced.
                    stop = False
                    def halt(*_args):
                        nonlocal stop
                        stop = True
                    signal.signal(signal.SIGTERM, halt)
                    signal.signal(signal.SIGINT, halt)
                    keeper.stop_requested = lambda: stop
                    original_save = keeper.save
                    initial_nonce = keeper.state['next_nonce']
                    initial_spent = copy.deepcopy(keeper.state['spent'])
                    saved = None
                    def save_then_wait():
                        nonlocal saved
                        original_save()
                        if keeper.state.get('pending') is None:
                            return
                        if saved is not None:
                            raise AssertionError('Unexpected second pending publication')
                        saved = keeper.path.read_bytes()
                        marker(root, 'intent_saved',
                               state_sha256=hashlib.sha256(saved).hexdigest(),
                               nonce=keeper.state['next_nonce'], spent=keeper.state['spent'],
                               barrier_scope='after_original_save_fsync_before_signer')
                        until = time.monotonic() + 30
                        while not stop:
                            if time.monotonic() >= until:
                                raise TimeoutError('Supervisor did not signal the saved-intent barrier')
                            time.sleep(0.02)
                    keeper.save = save_then_wait
                    try:
                        submitted = keeper.submit('vault', 'collectFees(uint256,uint256)',
                                                  (7, wire.now + 180), 'harvest:7')
                    finally:
                        keeper.save = original_save
                    calls = root / 'cast-calls.jsonl'
                    send_count = sum(json.loads(line).get('kind') == 'send_inert'
                                     for line in calls.read_text().splitlines()) if calls.exists() else 0
                    pending = keeper.state.get('pending')
                    if (not stop or submitted or saved is None or keeper.path.read_bytes() != saved
                            or pending is None or pending['hash'] is not None or send_count != 0
                            or keeper.state['next_nonce'] != initial_nonce
                            or keeper.state['spent'] != initial_spent):
                        raise AssertionError('Shutdown did not preserve exactly the unsent durable intent')
                    marker(root, 'stop_intent_prevented', send_inert_calls=0,
                           nonce=keeper.state['next_nonce'], spent=keeper.state['spent'],
                           pending_hashless=True, state_sha256=hashlib.sha256(saved).hexdigest())
                elif args.mode in ('submit', 'signer-stall'):
                    if args.mode == 'signer-stall':
                        private_write(root / 'signer_stall.flag', 'inert child containment test\n')
                    if not keeper.submit('vault', 'collectFees(uint256,uint256)',
                                         (7, wire.now + 180), 'harvest:7'):
                        raise AssertionError('Actual keeper refused the synthetic reviewed harvest')
                    marker(root, 'submitted', pending=keeper.state['pending'])
                elif args.mode == 'hashless':
                    original = keeper.path.read_bytes()
                    if not keeper.state.get('pending') or keeper.state['pending']['hash'] is not None:
                        raise AssertionError('Hashless recovery requires the retained real submit intent')
                    if not keeper.poll_pending() or keeper.path.read_bytes() != original:
                        raise AssertionError('Hashless recovery mutated or failed to block')
                    marker(root, 'hashless_blocked', state_sha256=hashlib.sha256(original).hexdigest())
                elif args.mode == 'recover':
                    pending = copy.deepcopy(keeper.state.get('pending'))
                    if not pending or pending['hash'] != HASH or pending['fee_review']['schema'] != 2:
                        raise AssertionError('Recovery requires the previously saved hash/schema2 intent')
                    atomic_json(root / 'receipt-pending.json', pending)
                    private_write(root / 'included.flag', 'inert authenticated inclusion transcript\n')
                    if keeper.poll_pending():
                        raise AssertionError('Canonical included synthetic receipt did not settle')
                    final = keeper.path.read_bytes()
                    day = dt.datetime.fromtimestamp(wire.now, dt.timezone.utc).date().isoformat()
                    if (keeper.state['pending'] is not None or keeper.state['next_nonce'] != pending['nonce'] + 1
                            or keeper.state['spent'] != {day: 300}
                            or keeper.state['last'].get('harvest:7') != wire.now
                            or keeper.state['last_fee_observation']['execution_price_wei'] != 3):
                        raise AssertionError('Receipt nonce/cost/harvest reconciliation differs')
                    if keeper.poll_pending() or keeper.path.read_bytes() != final:
                        raise AssertionError('Repeated recovery changed paid accounting')
                    marker(root, 'recovered', nonce=keeper.state['next_nonce'], cost_wei=300,
                           gas_used=100, price_wei=3, state_sha256=hashlib.sha256(final).hexdigest())
                elif args.mode == 'serve':
                    # Explicit containment/restart actor: only actual saved-intent
                    # recovery/checkpoint reads, never scheduling new operations.
                    marker(root, 'serving', pending=bool(keeper.state.get('pending')),
                           runtime=runtime, mode_scope='recovery_only_no_new_job_scheduling')
                    while True:
                        keeper.poll_pending()
                        watchdog.pulse()
                        time.sleep(0.2)
        after = source_pool()
        if before != after:
            raise AssertionError('Harness sources changed during execution')
        atomic_json(root / (args.mode + '-source.json'), {'scope': SCOPE,
            'source_sha256_before': before, 'source_sha256_after': after,
            'runtime': runtime,
            'production_approved': False, 'real_signing': False, 'public_transactions': 0})
        return 0
    finally:
        server.close()


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == '--inert-cast':
        raise SystemExit(inert_cast(sys.argv[2:]))
    if len(sys.argv) == 3 and sys.argv[1] == '--grandchild':
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        marker(Path(sys.argv[2]), 'grandchild_ready', parent=os.getppid())
        while True:
            time.sleep(1)
    raise SystemExit(main())
