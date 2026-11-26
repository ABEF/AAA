"""NEW c822 model for real daemon plus unsigned sidecar composition.

PREPARATION ONLY until parent review. Reuses frozen copied-state/setup helpers,
never an old scenario body. Only fresh isolated signer material is generated.
No host/service control lives here; the root coordinator owns those decisions.
"""
from pathlib import Path
import argparse
import base64
import copy
import datetime as dt
import gzip
import json
import os
import re
import signal
import stat
import sys
import threading
import time

import keeper_runtime as B
import keeper_jobs as J
import job_cases as C

LAB = Path('/opt/popl-keeper-composition-20261126-c822')
SOURCE = LAB / 'source/contracts'
OUT = LAB / 'runtime/model'
CONTROL = LAB / 'runtime/control'
HEAD = '7436933c153246f57eaa01cf42c5f3ec90363dad'
for module in (B, J, C):
    module.LAB, module.SOURCE, module.OUT = LAB, SOURCE, OUT
need, sha = B.need, B.sha
TX_FIELDS = ('hash', 'from', 'to', 'input', 'nonce', 'value', 'gas',
    'gasPrice', 'type', 'chainId', 'maxFeePerGas', 'maxPriorityFeePerGas',
    'blockHash', 'blockNumber', 'transactionIndex')
BOOKED = ('pending', 'next_nonce', 'spent', 'receipt_anchor',
    'last_fee_observation', 'last')
LIVE_READ_RACES = {'before': 0, 'during': 0}


def save(path, value):
    """Publish new lab evidence fully written and exclusive, never overwrite."""
    raw = json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    need(len(raw) <= 2 * 1024 * 1024, 'Diagnostic artifact exceeds bound')
    path = Path(path)
    temporary = path.parent / ('.' + path.name + '.' + os.urandom(16).hex() + '.part')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    # No-clobber link exposes only complete bytes. Marker-only readers accept
    # nlink2 during this tiny window; journal/health readers remain strict1.
    os.link(temporary, path, follow_symlinks=False)
    os.unlink(temporary)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def raw_file(path):
    """Bounded stable private evidence read; no signer contents are read here."""
    path = Path(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
        not path.is_symlink() and 0 < before.st_size <= 2 * 1024 * 1024,
        'Model record identity differs')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        key = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
        need(key(opened) == key(before), 'Model record changed before read')
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536, 2 * 1024 * 1024 + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            need(size <= 2 * 1024 * 1024, 'Model record exceeds bound')
            chunks.append(chunk)
        need(key(os.fstat(fd)) == key(before) == key(path.lstat()) and
            size == before.st_size, 'Model record changed during read')
        return b''.join(chunks)
    finally:
        os.close(fd)


def private_copy(path, raw):
    need(len(raw) <= 2 * 1024 * 1024, 'Private evidence exceeds bound')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def live_file(path):
    """Skip only a known atomic-rename race in this bounded polling iteration."""
    try:
        return raw_file(path)
    except B.HarnessRefusal as exc:
        labels = {'Model record changed before read': 'before',
            'Model record changed during read': 'during'}
        if type(exc) is not B.HarnessRefusal or str(exc) not in labels:
            raise
        LIVE_READ_RACES[labels[str(exc)]] += 1
        return None


def root_marker(name):
    need(name in ('INCLUDE', 'CAPTURE_FINAL'), 'Closed root control name')
    path = CONTROL / (name + '.json')
    try:
        item = path.lstat()
    except FileNotFoundError:
        return False
    # The coordinator publishes root controls by rename, so they retain the
    # strict single-link rule even while model reporting uses exclusive links.
    need(stat.S_ISREG(item.st_mode) and item.st_uid == 0 and item.st_nlink == 1
        and stat.S_IMODE(item.st_mode) == 0o444 and item.st_size <= 65536,
        'Root control record differs')
    value = B.json_file(path, 65536)
    need(value == {'schema': 1, 'name': name}, 'Root control intent differs')
    return True


class Model(J.Model):
    def start(self, env):
        need(sha(self.binary.read_bytes()) == B.ANVIL_SHA, 'Anvil differs')
        self.controlled_genesis_timestamp = int(time.time())
        self.child = B.Child([self.binary, '--host', '127.0.0.1', '--port', '19591',
            '--accounts', '0', '--silent', '--chain-id', '4663', '--hardfork',
            'cancun', '--gas-limit', '32000000', '--gas-price', '1000000000',
            '--block-base-fee-per-gas', '1', '--timestamp',
            str(self.controlled_genesis_timestamp), '--load-state',
            LAB / 'inputs/restore-state.json'], self.folder, env, self.folder / 'anvil')
        end = time.monotonic() + 20
        while True:
            need(self.child.process.poll() is None and not self.child.overflow,
                'Owned model stopped during startup')
            if B.owns(self.child.process.pid, 19591):
                try:
                    if self.rpc('eth_chainId', []) == '0x1237':
                        break
                except (ConnectionError, OSError):
                    pass
            need(time.monotonic() < end, 'Owned model startup deadline')
            time.sleep(.1)
        header = self.rpc('eth_getBlockByNumber', ['latest', False])
        need(header['hash'].lower() == B.IMPORTED_HASH and
            int(header['gasLimit'], 16) == 32000000, 'Copied F6 anchor differs')
        return header

    def guard(self):
        need(self.raw_send_count == self.work.raw_attempts == 1 and
            self.raw_forwarded == 0, 'Only one fresh harvest is admitted')
        super().guard()
        need(self.work.raw == 1, 'Exactly one guarded harvest is admitted')


C.Model = Model


def financial(case):
    """Actual integer-unit ownership, physical LP and reserve readback."""
    return {'rights': case.rights(), 'physical': case.physical(),
        'money': case.money(), 'vault_balances': {
            J.ZERO: int(case.model.rpc('eth_getBalance', [case.a['vault'], 'latest']), 16),
            J.ZZZ: case.uint(J.ZZZ, 'balanceOf(address)', case.a['vault'])}}


def canonical(case, transaction_hash):
    from zzz_ops.ethereum_fees import execution_price
    receipt = case.model.rpc('eth_getTransactionReceipt', [transaction_hash])
    need(type(receipt) is dict and receipt['status'] == '0x1',
        'Genuine harvest did not succeed')
    header = case.model.rpc('eth_getBlockByHash', [receipt['blockHash'], False])
    tx = case.model.rpc('eth_getTransactionByHash', [transaction_hash])
    head = case.model.rpc('eth_getBlockByNumber', ['latest', False])
    block = int(receipt['blockNumber'], 16)
    need(header['hash'] == receipt['blockHash'] and int(header['number'], 16) == block
        and int(head['number'], 16) - block + 1 >= 12, 'Canonical depth differs')
    fee = execution_price(tx, header, receipt)
    paid = int(receipt['gasUsed'], 16) * fee
    return {'schema': 1, 'accepted_hash': transaction_hash, 'receipt': receipt,
        'receipt_block': header, 'head': head,
        'transaction_without_signature': {key: tx.get(key) for key in TX_FIELDS},
        'execution_price_wei': fee, 'paid_wei': paid,
        'confirmations': int(head['number'], 16) - block + 1}


def validate_booking(case, state, intent, proof):
    from zzz_ops.abi import keccak256
    from zzz_ops.ethereum_fees import fee_cap, transaction_chain_id
    header, receipt, paid = proof['receipt_block'], proof['receipt'], proof['paid_wei']
    tx = proof['transaction_without_signature']
    need(tx['hash'] == receipt['transactionHash'] == proof['accepted_hash'] and
        tx['from'].lower() == receipt['from'].lower() == case.sender and
        tx['to'].lower() == receipt['to'].lower() == intent['to'] and
        tx['input'] == intent['data'] and int(tx['nonce'], 16) == intent['nonce'] == 0
        and int(tx['value'], 16) == intent['value'] == 0 and
        transaction_chain_id(tx) == 4663 and
        int(tx['gas'], 16) == intent['fee_review']['gas_limit'] and
        fee_cap(tx) == intent['fee_review']['max_fee_per_gas'],
        'Canonical signed transaction differs from the saved intent')
    topic = '0x' + keccak256(b'FeesCollected(uint256,uint256,uint256)').hex()
    harvests = [row for row in receipt['logs'] if
        row.get('address', '').lower() == case.a['vault'] and
        row.get('topics', [])[:1] == [topic]]
    need(len(harvests) == 1 and harvests[0]['topics'] == [topic, '0x' + f'{J.BUCKET:064x}']
        and len(case.decode(harvests[0]['data'])) == 2 and
        harvests[0]['transactionHash'] == proof['accepted_hash'] and
        harvests[0]['blockHash'] == header['hash'] and
        harvests[0].get('removed', False) is False,
        'Canonical exact bucket harvest event differs')
    stamp = int(header['timestamp'], 16)
    day = dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date().isoformat()
    need(state['pending'] is None and state['next_nonce'] == 1 and
        state['spent'] == {day: paid} and state['last'][intent['key']] == stamp and
        state['receipt_anchor'] == {'number': int(receipt['blockNumber'], 16),
            'hash': header['hash'], 'timestamp': stamp, 'nonce': 0},
        'Once-only canonical receipt booking differs')
    fee = state.get('last_fee_observation')
    need(type(fee) is dict and fee['transaction'] == proof['accepted_hash'] and
        fee['execution_price_wei'] == proof['execution_price_wei'] and
        fee['gas_used'] == int(receipt['gasUsed'], 16) and fee['l1_fee_wei'] == 0 and
        fee['receipt_fee_policy'] == 'included' and fee['cost_wei'] == paid,
        'Captured complete execution cost differs')
    need(case.model.raw_send_count == case.model.raw_forwarded ==
        case.model.work.raw_attempts == case.model.work.raw == 1,
        'Duplicate signing or forwarding detected')


def current_health(case, health):
    """Do not accept a status string instead of actual source-bound checks."""
    from keeper.ops import health_check
    now = time.time()
    checked = health_check(case.cfg, max_age=300, allow_dry_run=False,
        now=now, snapshot=health)
    need(checked['ok'] is True and not checked['reasons'] and
        health.get('status') == 'healthy_v2' and health.get('pending') is False and
        health.get('live') is True, 'Actual current keeper health is not accepted')
    anchors = {}
    for name, observation in (
            ('execution', health['lp_execution_health']['last_confirmed']),
            ('confirmation', health['rebalance_confirmation_health']['policy']['last_observed'])):
        number, stamp = observation['block_number'], observation['block_timestamp']
        header = case.model.rpc('eth_getBlockByNumber', [hex(number), False])
        need(type(header) is dict and int(header['number'], 16) == number and
            header['hash'] == observation['block_hash'] and
            int(header['timestamp'], 16) == stamp and -30 <= now - stamp <= 300,
            'Fresh observation canonical anchor differs')
        anchors[name] = {'number': number, 'hash': header['hash'],
            'timestamp': stamp, 'wall_age_seconds': now - stamp}
    return {'checker': checked, 'canonical_observation_anchors': anchors,
        'read_wall_unix': now, 'read_monotonic': time.monotonic()}


def export_evidence(case, source, result):
    """Export only named nonsecret existing records; no RPC or configuration."""
    files = {}
    for name in ('INITIAL_JOURNAL.json', 'PENDING_JOURNAL.json',
            'SETTLED_JOURNAL.json', 'HEALTHY_JOURNAL.json', 'FINAL_JOURNAL.json',
            'FINANCIAL_INITIAL.json', 'FINANCIAL_INCLUDED.json',
            'FINANCIAL_FINAL.json', 'CANONICAL_FINAL.json'):
        raw = raw_file(case.folder / name)
        files[name] = {'bytes': len(raw), 'sha256': sha(raw),
            'raw_base64': base64.b64encode(raw).decode('ascii')}
    payload = {'schema': 1, 'kind': 'popl-isolated-keeper-composition-evidence',
        'unsigned': True, 'readiness_approved': False, 'source_head': HEAD,
        'source_pins': source['members'], 'files': files,
        'exact_counters': {key: result[key] for key in
            ('shared_RPC_requests', 'raw_attempts', 'raw_forwarded', 'raw_guarded',
                'node_nonces', 'configuration_raw_sha256', 'final_journal_sha256',
                'live_read_races')},
        'raw_configuration_included': False, 'signer_material_included': False,
        'raw_signed_envelope_included': False,
        'scope': 'saved_actual_vectors_not_new_execution_or_public_qualification'}
    decoded = B.enc(payload)
    need(len(decoded) <= 256 * 1024, 'Saved model evidence decoded bound')
    envelope = {'decoded_bytes': len(decoded), 'decoded_sha256': sha(decoded),
        'gzip_base64': base64.b64encode(gzip.compress(decoded, mtime=0)).decode('ascii')}
    encoded = json.dumps(envelope, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    need(len(encoded) <= 32768, 'Saved model evidence encoded bound')
    save(OUT / 'MODEL_EVIDENCE.json', envelope)


def main():
    parser = argparse.ArgumentParser()
    for key in ('source-manifest', 'base', 'jobs', 'cases'):
        parser.add_argument('--' + key + '-sha256', required=True)
    args = parser.parse_args()
    need(os.geteuid() == 65534 and os.readlink('/proc/self/ns/net') !=
        os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'], 'New isolated nobody worker required')
    for module, pin in ((B, args.base_sha256), (J, args.jobs_sha256), (C, args.cases_sha256)):
        need(sha(Path(module.__file__).read_bytes()) == pin, 'Frozen setup helper differs')
    OUT.mkdir(mode=0o700, exist_ok=False)
    source = B.validate_source(args.source_manifest_sha256)
    need(source['source_head'] == HEAD, 'Exact current source required')
    for name, (size, pin) in B.INPUTS.items():
        raw = (LAB / 'inputs' / name).read_bytes()
        need(len(raw) == size and sha(raw) == pin, 'Copied F6 input differs')
    need(sha((LAB / 'tools/cast').read_bytes()) == B.CAST_SHA, 'Cast differs')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SOURCE))
    rows = B.json_file(LAB / 'inputs/instances.json')
    addresses = {row['role']: row['address'].lower() for row in rows}
    pins = {row['role']: row['runtime_keccak256'].lower() for row in rows}
    need(len(rows) == len(addresses) == len(set(addresses.values())) == 39,
        'Exact copied F6 graph required')
    temporary = OUT / 'tmp'
    temporary.mkdir(mode=0o700)
    env = {'TMPDIR': str(temporary), 'PATH': str(LAB / 'tools') + ':/usr/bin:/bin',
        'LANG': 'C.UTF-8', 'HOME': str(OUT / 'unadopted-home'),
        'PYTHONPATH': str(SOURCE), 'PYTHONDONTWRITEBYTECODE': '1'}
    os.environ.update(env)
    work, events = J.Work(), J.Events()
    case = C.Case('composition', work, env, addresses, pins, rows,
        B.json_file(LAB / 'inputs/bindings.json'), events)
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    result = {'schema': 1, 'source_head': HEAD, 'success': False,
        'scope': 'actual_local_stock_daemon_and_unsigned_sidecar_composition',
        'old_test_bodies_run': 0, 'public_transactions': 0, 'new_seals': 0,
        'production_approved': False, 'same_host_synthetic_fixture': True,
        'keeper_interval_seconds': 240, 'confirmations': 12, 'hourly_harvest': 3600,
        'gas_ceiling': 24000000, 'padding_percent': 25}
    phases = set()
    intent = proof = included = settled_state = None
    accepted = original_config = None
    last_heartbeat = 0.0
    ready_clock = None
    try:
        case.start()
        case.configure(maintenance={'compound': False, 'compound_idle': False,
            'harvest': True, 'minimum_liquidity': 1, 'harvest_interval_seconds': 3600})
        case.model.review['allowed'] = [('harvest', 'vault', 'collectFees(uint256,uint256)')]
        case.lock_guard.__exit__(None, None, None)
        case.lock_guard, case.k = None, None
        original_config = raw_file(case.config_path)
        journal = Path(case.cfg['state_path'])
        initial_state = json.loads(raw_file(journal))
        need(initial_state['pending'] is None and initial_state['next_nonce'] == 0 and
            not initial_state['spent'], 'Fresh unused journal required')
        need(case.uint('strategy', 'needsRebalance(uint256)', J.BUCKET) == 0 and
            case.uint('strategy', 'rangeUpdatePending(uint256)', J.BUCKET) == 0,
            'Only the selected harvest may be due')
        initial = financial(case)
        save(case.folder / 'FINANCIAL_INITIAL.json', initial)
        private_copy(case.folder / 'ORIGINAL_CONFIG.json', original_config)
        private_copy(case.folder / 'INITIAL_JOURNAL.json', raw_file(journal))
        for _ in range(12):
            case.advance()
        ready_clock = time.monotonic()
        save(OUT / 'READY.json', {'schema': 1, 'source_head': HEAD,
            'namespace': os.readlink('/proc/self/ns/net'), 'sender': case.sender,
            'configuration_path': str(case.config_path),
            'configuration_sha256': sha(original_config),
            'semantic_configuration_sha256': sha(B.enc(case.cfg)),
            'state_path': str(journal), 'health_path': case.cfg['health_path'],
            'lock_path': case.cfg['lock_path'], 'keystore_path': case.cfg['keystore'],
            'password_path': case.cfg['password_file'],
            'monitor_argv': ['/usr/bin/python3', '-B', '-m', 'keeper.monitor',
                '--config', str(case.config_path), '--live'],
            'monitor_working_directory': str(SOURCE), 'monotonic': ready_clock,
            'initial_health_present': Path(case.cfg['health_path']).exists(),
            'limits_unchanged': True})
        case.stage = 'await_actual_daemon_pending'
        while not stopped.wait(.25):
            need(time.monotonic() < work.deadline, 'Shared900second bound exceeded')
            need(case.model.raw_send_count <= 1 and work.raw_attempts <= 1 and
                case.model.raw_forwarded <= 1 and work.raw <= 1, 'Unexpected second send')
            need(raw_file(case.config_path) == original_config, 'Original config changed')
            state_raw = live_file(journal)
            if state_raw is None:
                continue
            state = json.loads(state_raw)
            if 'pending' not in phases:
                pending = state.get('pending')
                if type(pending) is not dict or type(pending.get('hash')) is not str:
                    continue
                accepted, intent = pending['hash'], copy.deepcopy(pending)
                need(re.fullmatch('0x[0-9a-f]{64}', accepted) and int(accepted, 16) > 0
                    and pending['nonce'] == state['next_nonce'] == 0 and
                    pending['key'] == 'harvest:' + str(J.BUCKET),
                    'Actual pending identity differs')
                tx = case.model.rpc('eth_getTransactionByHash', [accepted])
                from zzz_ops.ethereum_fees import fee_cap, transaction_chain_id
                need(tx['from'].lower() == case.sender and tx['to'].lower() == pending['to']
                    and tx['input'] == pending['data'] and int(tx['nonce'], 16) == 0 and
                    int(tx['value'], 16) == 0 and transaction_chain_id(tx) == 4663 and
                    int(tx['gas'], 16) == pending['fee_review']['gas_limit'] and
                    fee_cap(tx) == pending['fee_review']['max_fee_per_gas'] and
                    tx.get('blockNumber') is None and
                    case.model.rpc('eth_getTransactionReceipt', [accepted]) is None,
                    'Actual unmined signed transaction differs')
                private_copy(case.folder / 'PENDING_JOURNAL.json', state_raw)
                save(OUT / 'PENDING.json', {'schema': 1, 'accepted_hash': accepted,
                    'journal_sha256': sha(state_raw), 'monotonic': time.monotonic(),
                    'canonical_transaction': {key: tx.get(key) for key in TX_FIELDS},
                    'fee_review': pending['fee_review'], 'unmined': True})
                phases.add('pending')
                case.stage = 'await_root_include_after_sidecar_race'
            if 'included' not in phases:
                if not root_marker('INCLUDE'):
                    continue
                # Synthetic local mining is disclosed. Do not change keeper sleep,
                # confirmation count, feed limits or signed transaction deadline.
                need(case.now() <= int(intent['data'][-64:], 16),
                    'Signed harvest deadline expired before local inclusion')
                for _ in range(12):
                    case.advance()
                proof = canonical(case, accepted)
                need(proof['confirmations'] == 12, 'Initial inclusion must have12confirmations')
                save(case.folder / 'CANONICAL_INCLUDED.json', proof)
                included = financial(case)
                save(case.folder / 'FINANCIAL_INCLUDED.json', included)
                save(OUT / 'INCLUDED.json', {'schema': 1, 'accepted_hash': accepted,
                    'confirmations': 12, 'monotonic': time.monotonic(),
                    'paid_wei': proof['paid_wei'], 'receipt_block': proof['receipt_block'],
                    'head': proof['head'], 'local_mining_only': True})
                phases.add('included')
                case.stage = 'await_ordinary_daemon_receipt_wake'
            # Only the isolated controller mines. A fresh empty block follows the
            # wall clock approximately every5s; block/clock cadence is synthetic.
            clock = time.monotonic()
            if clock - last_heartbeat >= 5:
                wall = int(time.time())
                if wall > case.now():
                    case.advance(wall)
                last_heartbeat = clock
            if 'settled' not in phases and state.get('pending') is None and state.get('next_nonce') == 1:
                proof = canonical(case, accepted)
                validate_booking(case, state, intent, proof)
                health_raw = live_file(Path(case.cfg['health_path']))
                if health_raw is None:
                    continue
                health = json.loads(health_raw)
                # Journal commit precedes health publication. A transient running
                # snapshot is not the final receipt-cycle result: wait for it.
                if health.get('status') == 'running' or health.get('pending') is not False:
                    continue
                need(health.get('status') == 'degraded' and health.get('live') is True
                    and health.get('rebalance_confirmation_health', {}).get('policy', {}).get('state') == 'pending_recovery',
                    'First cleared-receipt cycle must retain truthful metadata degradation')
                private_copy(case.folder / 'SETTLED_JOURNAL.json', state_raw)
                private_copy(case.folder / 'SETTLED_HEALTH.json', health_raw)
                settled_state = copy.deepcopy(state)
                save(OUT / 'SETTLED.json', {'schema': 1, 'accepted_hash': accepted,
                    'journal_sha256': sha(state_raw), 'monotonic': time.monotonic(),
                    'recovery_fields': {key: state.get(key) for key in BOOKED},
                    'health': health, 'paid_wei': proof['paid_wei'],
                    'ready_elapsed_seconds': time.monotonic() - ready_clock})
                phases.add('settled')
                case.stage = 'await_following_normal240second_metadata_wake'
            if 'settled' in phases and 'healthy' not in phases:
                health_raw = live_file(Path(case.cfg['health_path']))
                if health_raw is None:
                    continue
                health = json.loads(health_raw)
                if health.get('status') != 'healthy_v2':
                    continue
                check = current_health(case, health)
                state_raw = live_file(journal)
                if state_raw is None:
                    continue
                state = json.loads(state_raw)
                proof = canonical(case, accepted)
                validate_booking(case, state, intent, proof)
                need(all(B.enc(state.get(key)) == B.enc(settled_state.get(key)) for key in BOOKED),
                    'Metadata refresh changed booked financial recovery')
                private_copy(case.folder / 'HEALTHY_JOURNAL.json', state_raw)
                private_copy(case.folder / 'HEALTHY_HEALTH.json', health_raw)
                save(OUT / 'HEALTHY.json', {'schema': 1, 'accepted_hash': accepted,
                    'journal_sha256': sha(state_raw), 'health': health, 'acceptance': check,
                    'monotonic': time.monotonic(), 'ready_elapsed_seconds': time.monotonic() - ready_clock,
                    'normal_loop_only': True, 'forced_refresh': False})
                phases.add('healthy')
                case.stage = 'await_root_keeper_and_sidecar_fence_before_final_capture'
            if 'healthy' not in phases or not root_marker('CAPTURE_FINAL'):
                continue
            final_raw = raw_file(journal)
            final_state = json.loads(final_raw)
            proof = canonical(case, accepted)
            validate_booking(case, final_state, intent, proof)
            need(all(B.enc(final_state.get(key)) == B.enc(settled_state.get(key)) for key in BOOKED),
                'Final canonical booking changed')
            final = financial(case)
            need(final == included, 'Post-inclusion financial vectors changed')
            need(final['rights'] == initial['rights'] and final['physical'] == initial['physical'],
                'NFT rights or physical principal changed during unsigned composition')
            nonces = {tag: int(case.model.rpc('eth_getTransactionCount', [case.sender, tag]), 16)
                for tag in ('latest', 'pending')}
            need(nonces == {'latest': 1, 'pending': 1}, 'Final signer nonce differs')
            need(raw_file(journal) == final_raw and raw_file(case.config_path) == original_config,
                'Final source records changed during capture')
            B.validate_source(args.source_manifest_sha256)
            save(case.folder / 'FINANCIAL_FINAL.json', final)
            save(case.folder / 'CANONICAL_FINAL.json', proof)
            private_copy(case.folder / 'FINAL_JOURNAL.json', final_raw)
            result.update(success=True, accepted_hash=accepted, phases=sorted(phases),
                shared_RPC_requests=work.count, raw_attempts=work.raw_attempts,
                raw_forwarded=case.model.raw_forwarded, raw_guarded=work.raw,
                node_nonces=nonces, final_financial_capture_complete=True,
                post_inclusion_financial_unchanged=True, initial_NFT_rights_and_principal_unchanged=True,
                canonical_receipt_booked_once=True, actual_following_normal_health_accepted=True,
                configuration_raw_sha256=sha(original_config), final_journal_sha256=sha(final_raw),
                ready_elapsed_seconds=time.monotonic() - ready_clock,
                signer_contents_exported=False, cleanup_still_required=True,
                live_read_races=dict(LIVE_READ_RACES))
            export_evidence(case, source, result)
            save(OUT / 'MODEL_RESULT.json', result)
            save(OUT / 'COMPLETE.json', result)
            case.stage = 'await_root_model_stop_after_final_capture'
            break
        need(result['success'], 'Complete composition was not observed')
        while not stopped.wait(.25):
            need(time.monotonic() < work.deadline, 'Root cleanup exceeded900seconds')
    except Exception as exc:
        result.update(success=False, failure_stage=case.stage, **B.safe_error(exc))
    finally:
        # Final physical evidence MUST precede COMPLETE/model-cgroup shutdown.
        # Never repeat a body or manufacture missing after-state following stop.
        try:
            B.validate_source(args.source_manifest_sha256)
            if original_config is not None:
                need(raw_file(case.config_path) == original_config, 'Original config changed at stop')
            for name, (size, pin) in B.INPUTS.items():
                raw = (LAB / 'inputs' / name).read_bytes()
                need(len(raw) == size and sha(raw) == pin, 'Original copied input changed')
            result['final_source_and_inputs_unchanged'] = True
        except Exception as exc:
            result.update(success=False, final_source_error=B.safe_error(exc))
        try:
            case.outcome.update(status='passed' if result['success'] else 'failed')
            result['cleanup'] = case.close()
        except Exception as exc:
            result.update(success=False, cleanup_error=B.safe_error(exc))
        result.update(shared_RPC_requests=work.count, raw_attempts=work.raw_attempts,
            raw_forwarded=case.model.raw_forwarded, raw_guarded=work.raw,
            live_read_races=dict(LIVE_READ_RACES),
            signer_material='Only new private disposable signer; no signer bytes exported')
        try:
            save(OUT / 'EVENTS.json', {'fixture_setup_events': ''.join(events.parts)})
            if not (OUT / 'MODEL_RESULT.json').exists():
                save(OUT / 'MODEL_RESULT.json', result)
            save(OUT / 'MODEL_STOP.json', result)
        except Exception:
            return 1
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
