"""Finite c827 unsigned target witness; private raw outputs, sanitized result."""
import sys
sys.dont_write_bytecode = True
import copy, datetime as dt, http.client, json, os, re, stat, time
from pathlib import Path
import shared as S
import runtime_support as R

ROOT = S.ROOT
WORK = ROOT / 'witness'
CONFIG = S.ACTOR / 'config.json'
STATE = S.ACTOR / 'state.json'
BUNDLE = ROOT / 'bundle'
MANIFEST_SHA = 'c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
FIELDS = ('pending', 'next_nonce', 'spent', 'receipt_anchor', 'last_fee_observation', 'last')
END = 0
RPC_ID = 0
STAGE = 'preflight'


def remaining(maximum=75):
    value = END - time.monotonic()
    S.need(value >= 1, 'target_deadline')
    return min(maximum, value)


def raw_save(name, raw):
    S.need(re.fullmatch(r'[A-Z][A-Z0-9_-]*\.(json|bin)', name) and len(raw) <= 2097152, 'witness_name_bound')
    path = WORK / name
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        S.need(stream.write(raw) == len(raw), 'witness_write')
        stream.flush(); os.fsync(stream.fileno())
    S.need(S.read(path) == raw, 'witness_readback')
    return {'bytes': len(raw), 'sha256': S.sha(raw)}


def rpc(method, params):
    global RPC_ID
    S.need(method in {'eth_chainId', 'eth_getTransactionReceipt', 'eth_getTransactionByHash',
        'eth_getBlockByNumber', 'eth_getTransactionCount'}, 'witness_read_method')
    RPC_ID += 1
    connection = http.client.HTTPConnection('127.0.0.1', 19627, timeout=remaining(15))
    try:
        connection.request('POST', '/', S.enc({'jsonrpc': '2.0', 'id': RPC_ID,
            'method': method, 'params': params}), {'Content-Type': 'application/json'})
        response = connection.getresponse(); S.need(response.status == 200, 'witness_RPC_HTTP')
        raw = response.read(2097153); S.need(len(raw) <= 2097152, 'witness_RPC_bound')
        value = S.decode(raw)
        S.need(type(value) is dict and value.get('jsonrpc') == '2.0' and type(value.get('id')) is int
            and value['id'] == RPC_ID and 'result' in value and 'error' not in value, 'witness_RPC_identity')
        return value['result']
    finally:
        connection.close()


def unsigned_files_absent():
    S.need(all(not os.path.lexists(path) for path in (S.ACTOR / 'secrets/keeper',
        S.ACTOR / 'secrets/password', ROOT / 'tools/cast')), 'target_signer_or_cast_present')


def sources():
    raw = S.read(ROOT / 'SOURCE_MANIFEST.json', 1048576)
    S.need(S.sha(raw) == MANIFEST_SHA, 'source_manifest_pin')
    manifest = S.decode(raw); rows = manifest['source_files']
    S.need(type(rows) is dict and len(rows) == 41, 'source_inventory')
    for name, row in rows.items():
        S.need(re.fullmatch(r'(keeper|zzz_ops|scripts|tests_python)/[A-Za-z0-9_-]+\.py', name)
            and S.sha(S.read(S.SOURCE / name, 1048576)) == row['sha256']
            and (S.SOURCE / name).lstat().st_size == row['bytes'], 'source_file_pin')
    names = manifest['dynamic_source_groups']['keeper/health.py:SOURCE_FILES']
    S.need(len(names) == 13, 'source13_count')
    return {name: rows[name]['sha256'] for name in names}


def isolation(identity):
    proof = S.namespace_guard()
    def proc(name):
        with Path('/proc/self', name).open('rb') as stream:
            raw = stream.read(65537)
        S.need(len(raw) <= 65536, 'target_proc_bound')
        return raw
    status = proc('status').decode('ascii')
    caps = re.search(r'^CapEff:\s*([0-9a-fA-F]+)$', status, re.M)
    S.need(caps and int(caps[1], 16) == 0, 'target_empty_capabilities')
    root = Path('/').stat()
    S.need([root.st_dev, root.st_ino] == identity['target_root_inode_pair'], 'actual_target_root')
    actual = {}
    for name, expected in identity['target_input_inode_pairs'].items():
        S.need(name in {'SOURCE_MANIFEST.json', 'source/keeper/monitor.py', 'actor/config.json', 'actor/state.json'}, 'isolation_input_name')
        item = (ROOT / name).lstat(); pair = [item.st_dev, item.st_ino]
        S.need(pair == expected and pair != identity['original_input_inode_pairs'][name], 'actual_copied_input_inode')
        actual[name] = pair
    S.need(len(actual) == 4, 'isolation_input_count')
    old = '/opt/popl-keeper-clean-restart-20261127-c827'
    S.need(identity['target_host_root'] == old + '/target-root', 'fixed_target_host_root')
    unavailable = [old + '/source', old + '/actor/config.json', old + '/actor/secrets',
        '/opt/popl-ubuntu-backup-recovery-20261126-c814',
        '/opt/popl-keeper-sidecar-recovery-20261126-c821',
        '/opt/popl-keeper-offhost-20261126-c823', '/opt/popl-keeper-reconstruction-20261127-c825']
    S.need(all(not os.path.lexists(name) for name in unavailable), 'old_application_paths_unavailable')
    raw = S.read(ROOT / 'RUNTIME_REVIEW.json', 65536)
    S.need(S.sha(raw) == identity['runtime_review_sha256'], 'external_runtime_review_pin')
    runtime = S.decode(raw)
    for name, row in runtime['files'].items():
        data = R.read(Path(name), 16777216)
        S.need(len(data) == row['bytes'] and S.sha(data) == row['sha256'], 'actual_runtime_file')
    tree = R.runtime_tree(Path(runtime['stdlib']))
    S.need(tree == runtime['stdlib_tree'], 'actual_runtime_stdlib')
    mount_raw = proc('mountinfo'); mounts = {}
    for line in mount_raw.decode('utf8', 'strict').splitlines():
        fields = line.split(); S.need(len(fields) >= 10, 'mountinfo_shape')
        point, mount_root = fields[4], fields[3]
        options = fields[5].split(',')
        broad = point in {'/opt', '/home', '/etc', '/usr', '/lib', '/usr/lib/x86_64-linux-gnu'}
        masked = mount_root.startswith('/run/systemd/inaccessible/')
        own = mount_root == identity['target_host_root'] + point
        S.need(not broad or 'ro' in options and (masked or own), 'broad_host_mount')
        S.need(not any(mount_root == name or mount_root.startswith(name + '/') for name in unavailable), 'old_application_bind')
        mounts[point] = options
    S.need(len(runtime['mounts']) == 18 and all('ro' in mounts.get(row['target'], [])
        for row in runtime['mounts']), 'actual_runtime_mounts_readonly')
    return {**proof, 'uid': os.getuid(), 'gid': os.getgid(), 'effective_capabilities': 0,
        'actual_root_inode_pair': [root.st_dev, root.st_ino], 'actual_input_inode_pairs': actual,
        'old_application_paths_unavailable': unavailable, 'mountinfo_sha256': S.sha(mount_raw),
        'mount_count': len(mounts), 'external_runtime_review_sha256': S.sha(raw),
        'external_runtime_mounts_verified': 18, 'stdlib_tree': tree, 'OS_runtime_is_external': True,
        'physical_second_host': False, 'chain_history_archive_restored': False}


def counters(identity):
    value = S.value(S.SHARED / 'BUDGET.json', 65536)
    names = ('raw_attempts', 'raw_forwarded', 'transaction_method_attempts')
    S.need(all(value[name] == 1 for name in names) and value['accepted_hash'] == identity['accepted_hash']
        and value['accepted_transaction_verified'] is True, 'zero_target_send_counters')
    return {name: value[name] for name in (*names, 'RPC_requests')}


def run(argv, label, allowed=(0,)):
    code, out, err = S.command(argv, cwd=S.SOURCE, env=S.environment(),
        seconds=remaining(75), allowed_codes=tuple(range(-128, 256)))
    record = {'argv': list(map(str, argv)), 'returncode': code,
        'stdout': raw_save(label + '-STDOUT.bin', out),
        'stderr': raw_save(label + '-STDERR.bin', err)}
    S.save(label + '-CALL.json', record, folder=WORK)
    S.need(not err and code in allowed, 'target_command_outcome')
    return record


def canonical(config, before, identity):
    pending = before['pending']; digest = pending['hash']; fee = pending['fee_review']
    S.need(rpc('eth_chainId', []) == hex(config['chain_id']) == hex(4663), 'target_chain')
    receipt = rpc('eth_getTransactionReceipt', [digest]); tx = rpc('eth_getTransactionByHash', [digest])
    block = rpc('eth_getBlockByNumber', [receipt['blockNumber'], False])
    head = rpc('eth_getBlockByNumber', ['latest', False])
    q = lambda value: int(value, 16)
    S.need(digest == identity['accepted_hash'] == receipt['transactionHash'] == tx['hash']
        and receipt['status'] == '0x1' and tx['from'].lower() == config['sender']
        and tx['to'].lower() == pending['to'] and tx['input'].lower() == pending['data'].lower()
        and q(tx['nonce']) == pending['nonce'] and q(tx['value']) == pending['value'] == 0
        and q(tx['chainId']) == config['chain_id'] and q(tx['gas']) == fee['gas_limit']
        and receipt['blockHash'] == tx['blockHash'] == block['hash']
        and receipt['blockNumber'] == tx['blockNumber'] == block['number']
        and receipt['transactionIndex'] == tx['transactionIndex'], 'target_canonical_identity')
    S.need(abs(time.time() - q(head['timestamp'])) <= 600
        and q(head['number']) - q(block['number']) + 1 >= config['confirmations'] == 12,
        'target_fresh_confirmed_head')
    kind = q(tx.get('type', '0x0'))
    cap = q(tx['maxFeePerGas'] if kind == 2 else tx['gasPrice'])
    if kind == 2:
        tip, base = q(tx['maxPriorityFeePerGas']), q(block['baseFeePerGas'])
        S.need(0 <= tip <= cap and base <= cap, 'target_dynamic_fee')
        price = min(cap, base + tip)
    else:
        S.need(kind in (0, 1), 'target_transaction_type'); price = cap
    gas, l1 = q(receipt['gasUsed']), q(receipt.get('l1Fee', '0x0'))
    cost = gas * price + l1
    S.need(cap == fee['max_fee_per_gas'] and 0 < gas <= fee['gas_limit']
        and fee['receipt_fee_policy'] == 'included' and l1 == fee['l1_fee_allowance_wei'] == 0
        and q(receipt['effectiveGasPrice']) == price and cost <= fee['maximum_cost_wei'], 'target_original_fee_envelope')
    if fee['schema'] == 2:
        S.need(kind == 2 and tip == 0 and fee['execution_fee_model'] == 'eip1559_zero_tip', 'target_zero_tip')
    stamp = q(block['timestamp'])
    return {'number': q(block['number']), 'hash': block['hash'], 'timestamp': stamp,
        'nonce': pending['nonce'], 'day': dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date().isoformat(),
        'gas_used': gas, 'execution_price_wei': price, 'reported_price_wei': q(receipt['effectiveGasPrice']),
        'l1_fee_wei': l1, 'cost_wei': cost, 'receipt_fee_policy': fee['receipt_fee_policy']}


def main():
    global END, STAGE
    END = time.monotonic() + 165
    S.need(os.getuid() == os.getgid() == 65534, 'target_uid')
    unsigned_files_absent()
    identity_path = ROOT / 'TARGET_IDENTITY.json'
    S.need(identity_path.lstat().st_uid == 0, 'target_external_identity_owner')
    identity = S.value(identity_path, 65536)
    S.need(identity['schema'] == 1 and identity['kind'] == 'popl-clean-restart-target-identity'
        and identity['source_manifest_sha256'] == MANIFEST_SHA
        and identity['review_max_age_seconds'] == 900, 'target_identity')
    actual_isolation = isolation(identity)
    before_counters = counters(identity)
    source13 = sources(); config_raw = S.read(CONFIG, 1048576); before_raw = S.read(STATE, 1048576)
    S.need(S.sha(config_raw) == identity['configuration_sha256']
        and S.sha(before_raw) == identity['pending_journal_sha256'], 'target_input_pins')
    config, before = S.decode(config_raw), S.decode(before_raw)
    semantic = S.sha(json.dumps(config, sort_keys=True, separators=(',', ':')).encode())
    S.need(config['rpc_urls'] == ['http://127.0.0.1:19627'] and config['state_path'] == str(STATE)
        and config['health_path'] == str(S.ACTOR / 'health.json')
        and config['lock_path'] == str(S.ACTOR / 'keeper.lock'), 'target_exact_runtime_paths')
    S.need(type(before['pending']) is dict and before['pending']['hash'] == identity['accepted_hash']
        and before['pending']['nonce'] == before['next_nonce'] == identity['next_nonce'] == 0,
        'target_present_known_pending')
    S.need(not os.path.lexists(S.ACTOR / 'health.json') and not os.path.lexists(S.ACTOR / 'keeper.lock'), 'fresh_target_health_lock')
    files = {'before': raw_save('STATE-BEFORE.json', before_raw)}
    arguments = ['--config', str(CONFIG), '--bundle', str(BUNDLE), '--manifest-sha256',
        identity['journal_manifest_sha256'], '--max-age-seconds', '900',
        '--minimum-created-at', str(identity['created_at']), '--minimum-next-nonce', '0']
    prefix = ['/usr/bin/python3', '-S', '-B', str(S.SOURCE / 'scripts/keeper-recovery.py')]
    STAGE = 'native_verify_restore'
    calls = [run([*prefix, 'verify', *arguments], 'NATIVE-VERIFY'),
        run([*prefix, 'restore', *arguments, '--output', str(WORK / 'native-restored')], 'NATIVE-RESTORE')]
    S.need(S.read(WORK / 'native-restored/keeper-state.json') == before_raw == S.read(STATE), 'native_state_equivalence')
    plan_raw = S.read(WORK / 'native-restored/RESTORE_PLAN.json'); plan = S.decode(plan_raw)
    verified = re.findall(rb'^Manifest SHA-256: ([0-9a-f]{64})$', S.read(WORK / 'NATIVE-VERIFY-STDOUT.bin'), re.M)
    restored = re.findall(rb'^Restore plan SHA-256: ([0-9a-f]{64})$', S.read(WORK / 'NATIVE-RESTORE-STDOUT.bin'), re.M)
    S.need(verified == [identity['journal_manifest_sha256'].encode()]
        and restored == [S.sha(plan_raw).encode()], 'native_stdout_plan_binding')
    S.need(plan['unsigned'] is True and all(plan[key] is False for key in ('live_ready',
        'canonical_state_verified', 'old_keeper_fenced', 'signer_material_included',
        'configuration_installed', 'service_restarted')), 'native_false_adoption_flags')
    STAGE = 'canonical_review'
    expected = canonical(config, before, identity)
    argv = ['/usr/bin/python3', '-S', '-B', '-m', 'keeper.monitor', '--config', str(CONFIG), '--once']
    STAGE = 'stock_recovery'
    calls.append(run(argv, 'RECOVERY', (1,)))
    settled_raw, first_health_raw = S.read(STATE), S.read(S.ACTOR / 'health.json')
    settled, health = S.decode(settled_raw), S.decode(first_health_raw)
    spent = copy.deepcopy(before['spent']); spent[expected['day']] = spent.get(expected['day'], 0) + expected['cost_wei']
    anchor = {key: expected[key] for key in ('number', 'hash', 'timestamp', 'nonce')}
    fee = {key: expected[key] for key in ('reported_price_wei', 'execution_price_wei', 'gas_used', 'l1_fee_wei', 'receipt_fee_policy', 'cost_wei')}
    fee['transaction'] = identity['accepted_hash']
    S.need(settled['pending'] is None and settled['next_nonce'] == 1 and settled['spent'] == spent
        and settled['receipt_anchor'] == anchor and settled['last_fee_observation'] == fee
        and settled['last'] == {**before['last'], before['pending']['key']: expected['timestamp']}, 'once_only_paid_accounting')
    S.need(health['status'] == 'degraded' and health['live'] is False and health['pending'] is False
        and health['skipped_buckets'] == health['blocked_actions'] == 0
        and health['configuration_sha256'] == semantic
        and health['lp_execution_health']['state'] == 'pending_recovery'
        and health['rebalance_confirmation_health']['policy']['state'] == 'pending_recovery', 'recovery_metadata_degraded')
    files.update(settled=raw_save('STATE-SETTLED.json', settled_raw), recovery_health=raw_save('HEALTH-RECOVERY.json', first_health_raw))
    lock = (S.ACTOR / 'keeper.lock').lstat()
    S.need(stat.S_ISREG(lock.st_mode) and lock.st_nlink == 1 and lock.st_uid == 65534
        and stat.S_IMODE(lock.st_mode) == 0o600 and lock.st_size == 0, 'target_lock_metadata')
    STAGE = 'stock_dry'
    calls.append(run(argv, 'DRY', (0,)))
    dry_raw, dry_health_raw = S.read(STATE), S.read(S.ACTOR / 'health.json')
    dry, dry_health = S.decode(dry_raw), S.decode(dry_health_raw)
    changed = sorted(key for key in set(settled) | set(dry) if settled.get(key) != dry.get(key))
    S.need(all(dry.get(key) == settled.get(key) for key in FIELDS)
        and set(changed) <= {'conversion_turn', 'bucket_cursor'}
        and dry['conversion_turn'] == (settled.get('conversion_turn', 0) + 1) % 3, 'dry_financial_fields_unchanged')
    S.need(dry_health['status'] == 'dry_run_v2' and dry_health['live'] is False
        and dry_health['configuration_sha256'] == semantic
        and dry_health['pending'] is False and dry_health['skipped_buckets'] == dry_health['blocked_actions'] == 0,
        'fresh_dry_health')
    S.need(dry_health['lp_execution_health']['state'] == 'observed_this_cycle'
        and dry_health['rebalance_confirmation_health']['policy']['state'] == 'observed_this_cycle', 'fresh_dry_metadata')
    for observed in (dry_health['lp_execution_health']['last_confirmed'],
            dry_health['rebalance_confirmation_health']['policy']['last_observed']):
        S.need(observed['configuration_sha256'] == semantic and observed['source_files_sha256'] == source13,
            'fresh_metadata_identity')
    files.update(dry=raw_save('STATE-DRY.json', dry_raw), dry_health=raw_save('HEALTH-DRY.json', dry_health_raw))
    nonces = {tag: int(rpc('eth_getTransactionCount', [config['sender'], tag]), 16) for tag in ('latest', 'pending')}
    S.need(nonces == {'latest': 1, 'pending': 1} and S.read(CONFIG) == config_raw and sources() == source13, 'target_final_identity')
    final_lock = (S.ACTOR / 'keeper.lock').lstat()
    S.need((final_lock.st_dev, final_lock.st_ino, final_lock.st_mode, final_lock.st_nlink, final_lock.st_size)
        == (lock.st_dev, lock.st_ino, lock.st_mode, lock.st_nlink, lock.st_size), 'target_lock_preserved')
    unsigned_files_absent()
    after_counters = counters(identity)
    STAGE = 'result_publication'
    S.save('RESULT.json', {'schema': 1, 'success': True, 'unsigned': True,
        'readiness_approved': False, 'production_approved': False, 'canonical_state_verified': False,
        'scope': 'clean_application_root_against_retained_isolated_chain', 'calls': calls,
        'files': files, 'native_restore_plan_sha256': S.sha(plan_raw), 'source13_sha256': source13,
        'accepted_hash': identity['accepted_hash'], 'canonical_accounting': expected,
        'node_nonces': nonces, 'changed_dry_scheduler_keys': changed,
        'configuration_raw_sha256': S.sha(config_raw), 'configuration_semantic_sha256': semantic,
        'desktop_proof_sha256': identity['desktop_proof_sha256'], 'signer_and_cast_absent': True,
        'actual_isolation': actual_isolation, 'gateway_counters_before': before_counters,
        'gateway_counters_after': after_counters, 'recovery_transaction_attempt_delta': 0,
        'target_lock': {'device': lock.st_dev, 'inode': lock.st_ino, 'mode': stat.S_IMODE(lock.st_mode),
            'uid': lock.st_uid, 'links': lock.st_nlink, 'bytes': lock.st_size},
        'stock_recovery_exit': 1, 'stock_dry_exit': 0, 'old_test_bodies_run': 0}, folder=WORK)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        error = type(exc).__name__
        if error not in ('ValueError', 'KeyError', 'TypeError', 'OSError', 'FileNotFoundError',
                'PermissionError', 'FileExistsError', 'TimeoutError', 'TimeoutExpired'):
            error = 'UnexpectedError'
        print(json.dumps({'schema': 1, 'success': False, 'refusal_code': 'target_witness',
            'readiness_approved': False, 'refusal_stage': STAGE, 'error_type': error}))
        raise SystemExit(1) from None
