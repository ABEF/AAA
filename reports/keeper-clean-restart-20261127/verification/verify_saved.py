"""Independent fixed-case audit of saved bytes. No helper/application/RPC execution.

The private saved kit and witness packet are required; they must remain private.
This verifier does not reinterpret present-day freshness or rerun the rehearsal.
"""
from pathlib import Path
import ast
import base64
import copy
import datetime
import hashlib
import json
import math
import os
import stat
import subprocess
import zlib

REPO = Path(__file__).resolve().parents[3]
WORK = REPO / 'cache-keeper-clean-restart-20261127'
PRIVATE = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-clean-restart-20261127/private')
CASE = PRIVATE / 'campaign-003'
HOST = PRIVATE.parents[1] / 'history-export-20261124/host-preservation'
OUTPUT = Path(__file__).with_name('SAVED_RECONCILIATION.json')
HEAD = 'd6e8a909fd2b2a12eb1bee15173e92d526178cdb'
SOURCE_PIN = 'c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
CONTROLLER = '22d459431d168fa5822ea8917544a2de166f2e1a820b1d9f6de39516a1d31a91'
CONTINUATION = 'c6ef1c1ed2b1f10c9c393e6d9c5438fb81e913f6eccce53b491b70b1bf8f9e8d'
RUNTIME = '3025d86be5de48fd1643ddd53819fe3ef1d9268dca689749827ad399247abdb6'
HASH = '0xbc4f7151d43ef650ad69027e1b81bdbc95de780f382221ff59c0f6b6c77046e1'
inputs = {}
checks = []
sha = lambda raw: hashlib.sha256(raw).hexdigest()
enc = lambda value: (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()

def need(value, label):
    if not value:
        raise ValueError(label)

def decode(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('nonfinite_JSON')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    def finite(item):
        if type(item) is float:
            need(math.isfinite(item), 'nonfinite_JSON')
        elif type(item) is dict:
            for child in item.values(): finite(child)
        elif type(item) is list:
            for child in item: finite(child)
    finite(value)
    return value

def label(path):
    path = path.resolve()
    if path.is_relative_to(PRIVATE): return 'private/' + path.relative_to(PRIVATE).as_posix()
    if path.is_relative_to(HOST): return 'private-host-preservation/' + path.relative_to(HOST).as_posix()
    return path.relative_to(REPO).as_posix()

def read(path, maximum=1048576):
    path = Path(path)
    before = path.lstat()
    key = lambda row: (row.st_dev, row.st_ino, row.st_mode, row.st_nlink, row.st_size, row.st_mtime_ns)
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_ino != 0
         and 0 <= before.st_size <= maximum and not getattr(before, 'st_file_attributes', 0) & 0x400, 'saved_file_metadata')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as stream:
        need(key(os.fstat(stream.fileno())) == key(before), 'saved_file_open_identity')
        raw = stream.read(maximum + 1)
        need(len(raw) == before.st_size and key(os.fstat(stream.fileno())) == key(before) == key(path.lstat()), 'saved_file_stable_read')
    inputs[label(path)] = {'bytes': len(raw), 'sha256': sha(raw)}
    return raw

def load(path, maximum=1048576):
    return decode(read(path, maximum))

def check(name, condition=True):
    need(condition, name)
    checks.append(name)

def stopped(properties):
    return properties['MainPID'] == '0' and properties['ActiveState'] in ('inactive', 'failed') and not properties['ControlGroup']

def main():
    proof_raw = read(CASE / 'desktop-kit/KIT_PROOF.json', 16384)
    proof = decode(proof_raw)
    expected = proof['files']
    check('private_kit_proof_unsigned_exact45', proof['ok'] is True and proof['unsigned'] is True
          and proof['kind'] == 'c828-desktop-recovery-kit' and len(expected) == 45
          and proof['review_max_age_seconds'] == 900 and proof['signer_material_included'] is False
          and proof['readiness_approved'] is proof['production_approved'] is False)
    kit = CASE / 'desktop-kit/kit'
    dirs = {p.as_posix() for name in expected for p in Path(name).parents if p != Path('.')}
    actual, contents = set(), {}
    pending = [(kit, 0)]
    while pending:
        parent, depth = pending.pop()
        need(depth <= 5, 'kit_directory_depth')
        with os.scandir(parent) as rows:
            for row in rows:
                path = Path(row.path)
                name = path.relative_to(kit).as_posix()
                info = path.lstat()  # Path.lstat is required on Windows; DirEntry.stat may report nlink0.
                need(name not in actual and name in set(expected) | dirs and len(actual) < 64
                     and not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'closed_kit_tree')
                actual.add(name)
                if stat.S_ISDIR(info.st_mode):
                    need(name in dirs, 'kit_directory_name')
                    pending.append((path, depth + 1))
                else:
                    raw = read(path)
                    need({'bytes': len(raw), 'sha256': sha(raw)} == expected[name], 'kit_file_pin')
                    contents[name] = raw
    check('private_kit45_stable_singlelink_rehash', actual == set(expected) | dirs and len(contents) == 45
          and sum(map(len, contents.values())) == proof['total_raw_bytes'] == 808416)
    manifest = decode(contents['SOURCE_MANIFEST.json'])
    source_rows = manifest['source_files']
    check('original_source_manifest_and41members', sha(contents['SOURCE_MANIFEST.json']) == SOURCE_PIN
          and len(source_rows) == 41 and set(contents) == {'SOURCE_MANIFEST.json', 'CONFIG.json', 'bundle/manifest.json', 'bundle/journal.json', *('source/' + n for n in source_rows)})
    source_names = list(source_rows)
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    git = subprocess.run(['git', 'cat-file', '--batch'], cwd=REPO, env=env,
        input=('\n'.join(HEAD + ':' + name for name in source_names) + '\n').encode(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    need(len(git.stdout) <= 2097152 and len(git.stderr) <= 4096, 'Git_blob_output_bound')
    cursor = 0
    for name in source_names:
        end = git.stdout.index(b'\n', cursor)
        header = git.stdout[cursor:end].split()
        need(len(header) == 3 and header[1] == b'blob', 'Git_blob_header')
        size = int(header[2]); cursor = end + 1
        blob = git.stdout[cursor:cursor + size]; cursor += size
        need(git.stdout[cursor:cursor + 1] == b'\n', 'Git_blob_terminator'); cursor += 1
        need(blob == contents['source/' + name] and len(blob) == source_rows[name]['bytes']
             and sha(blob) == source_rows[name]['sha256'], 'Git_source_byte_identity')
    check('current_release41_exact_trusted_Git_blobs', cursor == len(git.stdout))
    source13 = {name: source_rows[name]['sha256'] for name in manifest['dynamic_source_groups']['keeper/health.py:SOURCE_FILES']}
    check('source13_identity', len(source13) == 13)

    included = load(CASE / 'fetch-included/INCLUDED.json')
    canonical = load(CASE / 'fetch-canonical/CANONICAL.json')
    config = decode(contents['CONFIG.json']); original = decode(contents['bundle/journal.json'])
    native_manifest = decode(contents['bundle/manifest.json'])
    for name, field in [('CONFIG.json', 'configuration_sha256'), ('bundle/manifest.json', 'backup_manifest_sha256'), ('bundle/journal.json', 'pending_journal_sha256')]:
        need(sha(contents[name]) == included[field], 'independent_capture_pin')
    check('capture_is_original_once_only_included_pending', included['accepted_hash'] == HASH == proof['accepted_hash']
          and included['raw_attempts'] == included['raw_forwarded'] == 1 and included['actual_node_pending_before_inclusion'] is True
          and included['source_journal_unchanged'] is True and included['confirmations'] == 12
          and included['clock_overrides'] == 0 and included['native_backup_returncode'] == 0
          and original['pending']['hash'] == HASH and original['next_nonce'] == original['pending']['nonce'] == 0)
    check('original_policy_and_operating_limits_unchanged', config['chain_id'] == 4663 and config['confirmations'] == 12
          and config['interval_seconds'] == 240 and config['max_gas_limit'] == 24000000
          and config['max_gas_price_wei'] == '5000000000' and config['max_transaction_cost_wei'] == '10000000000000000'
          and config['max_daily_cost_wei'] == '50000000000000000' and config['maintenance']['harvest_interval_seconds'] == 3600
          and config.get('submission_fee_profile', 1) == 1 and proof['original_created_at'] == native_manifest['created_at'])
    receipt, tx, block, head = (canonical[key] for key in ('receipt', 'transaction_without_signature', 'receipt_block', 'head'))
    q = lambda value: int(value, 16)
    check('independent_canonical_transaction_receipt_header', HASH == canonical['hash'] == receipt['transactionHash'] == tx['hash']
          and receipt['status'] == '0x1' and tx['from'].lower() == config['sender']
          and tx['to'].lower() == original['pending']['to'] and tx['input'].lower() == original['pending']['data'].lower()
          and q(tx['nonce']) == 0 and q(tx['value']) == original['pending']['value'] == 0 and q(tx['chainId']) == 4663
          and receipt['blockHash'] == tx['blockHash'] == block['hash'] and receipt['blockNumber'] == tx['blockNumber'] == block['number']
          and receipt['transactionIndex'] == tx['transactionIndex'] and q(head['number']) - q(block['number']) + 1 >= 12)
    need(type(original['pending']['fee_review']['gas_limit']) is int, 'fee_integer')
    envelope = original['pending']['fee_review']
    cap = q(tx['maxFeePerGas']) if q(tx['type']) == 2 else q(tx['gasPrice'])
    price = min(cap, q(block['baseFeePerGas']) + q(tx['maxPriorityFeePerGas'])) if q(tx['type']) == 2 else cap
    gas = q(receipt['gasUsed']); l1 = q(receipt.get('l1Fee', '0x0')); cost = gas * q(receipt['effectiveGasPrice']) + l1
    stamp = q(block['timestamp']); day = datetime.datetime.fromtimestamp(stamp, datetime.timezone.utc).date().isoformat()
    check('actual_fee_envelope_cost_and_inclusion_deadline', q(receipt['effectiveGasPrice']) == price
          and cap == envelope['max_fee_per_gas'] and q(tx['gas']) == envelope['gas_limit']
          and 0 < gas <= envelope['gas_limit'] and envelope['receipt_fee_policy'] == 'included'
          and l1 == envelope['l1_fee_allowance_wei'] == 0 and cost <= envelope['maximum_cost_wei']
          and included['actual_inclusion_timestamp'] == stamp <= included['harvest_deadline'])

    compressed = read(CASE / 'private2/TARGET2_PRIVATE.zlib', 32768)
    inflater = zlib.decompressobj(); raw_packet = inflater.decompress(compressed, 131073)
    need(len(raw_packet) <= 131072 and inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail, 'private_packet_bound')
    packet = decode(raw_packet)
    wanted = {'CONFIG.json', 'STATE-BEFORE.json', 'STATE-SETTLED.json', 'STATE-DRY.json', 'HEALTH-RECOVERY.json', 'HEALTH-DRY.json', 'RESTORE_PLAN.json', 'TARGET_IDENTITY.json'}
    check('fixed_private_eight_records_complete_success', set(packet['files']) == wanted and packet['missing'] == []
          and packet['target_success'] is True and packet['raw_records_must_remain_private'] is True
          and packet['target_unit_status']['ExecMainCode'] == '1' and packet['target_unit_status']['ExecMainStatus'] == '0')
    raw_records = {}
    for name, row in packet['files'].items():
        raw = base64.b64decode(row['raw_base64'], validate=True)
        need(len(raw) == row['bytes'] <= 32768 and sha(raw) == row['sha256'], 'private_record_pin')
        raw_records[name] = raw
    records = {name: decode(raw) for name, raw in raw_records.items()}
    before, settled, dry = (records['STATE-' + name + '.json'] for name in ('BEFORE', 'SETTLED', 'DRY'))
    health, dry_health, identity, plan = (records[name] for name in ('HEALTH-RECOVERY.json', 'HEALTH-DRY.json', 'TARGET_IDENTITY.json', 'RESTORE_PLAN.json'))
    result = load(CASE / 'result2/TARGET2_RESULT.json', 32768)
    check('same_raw_config_and_pending_reconstructed', raw_records['CONFIG.json'] == contents['CONFIG.json']
          and raw_records['STATE-BEFORE.json'] == contents['bundle/journal.json'] and identity['accepted_hash'] == HASH
          and identity['source_manifest_sha256'] == SOURCE_PIN and identity['configuration_sha256'] == sha(contents['CONFIG.json'])
          and identity['pending_journal_sha256'] == sha(contents['bundle/journal.json'])
          and identity['desktop_proof_sha256'] == sha(proof_raw) and identity['review_max_age_seconds'] == 900)
    spent = copy.deepcopy(before['spent']); spent[day] = spent.get(day, 0) + cost
    anchor = {'number': q(block['number']), 'hash': block['hash'], 'timestamp': stamp, 'nonce': 0}
    observation = {'transaction': HASH, 'reported_price_wei': price, 'execution_price_wei': price,
                   'gas_used': gas, 'l1_fee_wei': 0, 'receipt_fee_policy': 'included', 'cost_wei': cost}
    check('independent_once_only_exact_paid_accounting', settled['pending'] is None and settled['next_nonce'] == 1
          and settled['spent'] == spent and settled['receipt_anchor'] == anchor and settled['last_fee_observation'] == observation
          and settled['last'] == {**before['last'], before['pending']['key']: stamp})
    financial = ('pending', 'next_nonce', 'spent', 'receipt_anchor', 'last_fee_observation', 'last')
    changed = sorted(k for k in set(settled) | set(dry) if settled.get(k) != dry.get(k))
    check('second_process_dry_financial_state_unchanged', all(dry.get(k) == settled.get(k) for k in financial)
          and set(changed) <= {'conversion_turn', 'bucket_cursor'} and changed == result['changed_dry_scheduler_keys']
          and dry['conversion_turn'] == (settled.get('conversion_turn', 0) + 1) % 3)
    semantic = sha(json.dumps(config, sort_keys=True, separators=(',', ':')).encode())
    check('recovery_health_truthful_metadata_degraded', health['status'] == 'degraded' and health['live'] is health['pending'] is False
          and health['skipped_buckets'] == health['blocked_actions'] == 0 and health['configuration_sha256'] == semantic
          and health['lp_execution_health']['state'] == health['rebalance_confirmation_health']['policy']['state'] == 'pending_recovery')
    check('fresh_dry_health_and_current_source_identity', dry_health['status'] == 'dry_run_v2' and dry_health['live'] is dry_health['pending'] is False
          and dry_health['skipped_buckets'] == dry_health['blocked_actions'] == 0 and dry_health['configuration_sha256'] == semantic
          and dry_health['lp_execution_health']['state'] == dry_health['rebalance_confirmation_health']['policy']['state'] == 'observed_this_cycle'
          and all(item['configuration_sha256'] == semantic and item['source_files_sha256'] == source13 for item in
                  (dry_health['lp_execution_health']['last_confirmed'], dry_health['rebalance_confirmation_health']['policy']['last_observed'])))
    check('native_restore_plan_keeps_all_adoption_flags_false', plan['unsigned'] is True
          and all(plan[k] is False for k in ('live_ready', 'canonical_state_verified', 'old_keeper_fenced', 'signer_material_included', 'configuration_installed', 'service_restarted'))
          and plan['manifest_sha256'] == sha(contents['bundle/manifest.json']) and sha(raw_records['RESTORE_PLAN.json']) == result['native_restore_plan_sha256']
          and plan['configuration_raw_sha256'] == sha(contents['CONFIG.json']) and plan['configuration_sha256'] == semantic)
    calls = result['calls']
    check('two_native_and_two_fresh_stock_process_results', [row['returncode'] for row in calls] == [0, 0, 1, 0]
          and all(row['stderr']['bytes'] == 0 and row['stderr']['sha256'] == sha(b'') for row in calls)
          and calls[2]['argv'] == calls[3]['argv'] and calls[2]['argv'][-1] == '--once'
          and '-m' in calls[2]['argv'] and 'keeper.monitor' in calls[2]['argv']
          and all('--live' not in row['argv'] and '--initialize-state' not in row['argv'] for row in calls)
          and all(row['argv'][row['argv'].index('--max-age-seconds') + 1] == '900' for row in calls[:2]))
    for key, name in [('before', 'STATE-BEFORE.json'), ('settled', 'STATE-SETTLED.json'), ('dry', 'STATE-DRY.json'), ('recovery_health', 'HEALTH-RECOVERY.json'), ('dry_health', 'HEALTH-DRY.json')]:
        need(result['files'][key] == {'bytes': len(raw_records[name]), 'sha256': sha(raw_records[name])}, 'result_raw_witness_binding')
    check('result_and_unsigned_false_approval_scope', result['success'] is result['unsigned'] is result['signer_and_cast_absent'] is True
          and result['readiness_approved'] is result['production_approved'] is result['canonical_state_verified'] is False
          and result['old_test_bodies_run'] == 0 and result['recovery_transaction_attempt_delta'] == 0
          and result['node_nonces'] == {'latest': 1, 'pending': 1} and result['source13_sha256'] == source13)
    for counters in (result['gateway_counters_before'], result['gateway_counters_after']):
        need(all(counters[key] == 1 for key in ('raw_attempts', 'raw_forwarded', 'transaction_method_attempts')), 'zero_target_transaction_attempt_delta')
    check('independent_actual_root_inodes_runtime_and_lock', result['actual_isolation']['actual_root_inode_pair'] == identity['target_root_inode_pair']
          and result['actual_isolation']['actual_input_inode_pairs'] == identity['target_input_inode_pairs']
          and len(identity['target_input_inode_pairs']) == 4
          and all(pair != identity['original_input_inode_pairs'][key] for key, pair in identity['target_input_inode_pairs'].items())
          and identity['target_host_root'].endswith('/target2-root')
          and result['actual_isolation']['effective_capabilities'] == 0
          and result['actual_isolation']['uid'] == result['actual_isolation']['gid'] == 65534
          and result['actual_isolation']['external_runtime_mounts_verified'] == 18
          and result['actual_isolation']['external_runtime_review_sha256'] == RUNTIME
          and result['actual_isolation']['OS_runtime_is_external'] is True
          and result['actual_isolation']['separate_node_cgroup'] is True and result['actual_isolation']['host_network_access'] is False
          and result['actual_isolation']['physical_second_host'] is result['actual_isolation']['chain_history_archive_restored'] is False
          and result['target_lock']['mode'] == 0o600 and result['target_lock']['uid'] == 65534
          and result['target_lock']['links'] == 1 and result['target_lock']['bytes'] == 0)
    recovery_time = datetime.datetime.fromisoformat(health['time'].replace('Z', '+00:00'))
    need(recovery_time.utcoffset() == datetime.timedelta(0), 'recovery_time_UTC')
    capture_age = recovery_time.timestamp() - native_manifest['created_at']
    check('actual_saved_recovery_age_within_unchanged900', type(native_manifest['created_at']) is int and 0 <= capture_age <= 900)

    vectors = {name: load(CASE / ('fetch-financial_' + name) / ('FINANCIAL_' + name.upper() + '.json')) for name in ('initial', 'included', 'final')}
    check('final_independent_physical_vectors_before_node_stop', vectors['included'] == vectors['final']
          and vectors['initial']['rights'] == vectors['final']['rights'] and vectors['initial']['position'] == vectors['final']['position'])
    final = load(CASE / 'fetch-final_chain/FINAL_CHAIN.json')
    status = load(CASE / 'status-final/SANITIZED_RESULT.json')
    source_status = load(CASE / 'status-source/SANITIZED_RESULT.json')['units']['source']
    fenced_status = load(CASE / 'status-capture/SANITIZED_RESULT.json')['units']['source']
    check('source_once_completed_then_group_stopped_without_restart', source_status['group_empty'] is True
          and source_status['properties']['ExecMainCode'] == '1' and source_status['properties']['ExecMainStatus'] == '0'
          and fenced_status['group_empty'] is True and stopped(fenced_status['properties']) and fenced_status['properties']['Restart'] == 'no')
    check('one_source_forward_zero_recovery_send_final_nonces', final['accepted_hash'] == HASH and final['receipt_unchanged'] is True
          and final['post_inclusion_financial_unchanged'] is True and final['source_journal_sha256'] == included['pending_journal_sha256']
          and final['node_nonce_latest'] == final['node_nonce_pending'] == 1 and final['public_transactions'] == final['clock_overrides'] == 0
          and final['production_approved'] is False and all(final['budget'][key] == status['budget'][key] == 1 for key in ('raw_attempts', 'raw_forwarded', 'transaction_method_attempts'))
          and status['budget']['RPC_requests'] == final['budget']['RPC_requests'] + 2 == 2119 <= 6000)
    for number in ('001', '002', '003'):
        stop = load(PRIVATE / ('campaign-' + number) / 'fetch-stop/FINAL_STOP.json')
        need(stop['all_new_groups_empty'] is stop['old_immutable_fixture_unchanged'] is True
             and len(stop['units']) == 9 and all(stopped(p) for p in stop['units'].values()), 'old_nine_groups_stopped')
        need(stop['final_physical_capture_present'] is (number == '003'), 'no_failure_relabel')
    stop2 = load(CASE / 'stop2/SANITIZED_RESULT.json')
    check('all_three_cases_and_both_continuation_units_stopped', stop2['target2_group_empty'] is True
          and set(stop2['units']) == {'target2', 'fresh2'} and all(stopped(p) for p in stop2['units'].values()))
    failed = load(PRIVATE / 'campaign-001/status-failed/SANITIZED_RESULT.json')
    bootstrap_failure = load(PRIVATE / 'campaign-002/status-bootstrap/SANITIZED_RESULT.json')
    diagnosis = load(PRIVATE / 'target-diagnostic-001/RESULT.json')
    check('earlier_source_and_preexec_failures_retained', failed['capture_complete'] is failed['target_result_present'] is False
          and all(failed['budget'][key] == bootstrap_failure['budget'][key] == 0 for key in ('raw_attempts', 'raw_forwarded', 'transaction_method_attempts'))
          and diagnosis['target']['ExecMainCode'] == '1' and diagnosis['target']['ExecMainStatus'] == '226' and diagnosis['target']['MainPID'] == '0'
          and diagnosis['source_pending_unchanged'] is diagnosis['target_pending_unchanged'] is True
          and any('mount namespacing' in row['MESSAGE'] and '/actor: No such file or directory' in row['MESSAGE'] for row in diagnosis['messages']))

    original_controller = read(WORK / 'c828/remote_capsule.py', 65536)
    continuation = read(WORK / 'c828/continuation/target2_continuation.py', 65536)
    tail = read(WORK / 'c828/continuation/target2_tail.py', 16384)
    check('continuation_preserves_original_code_and_identity', sha(original_controller) == CONTROLLER and sha(continuation) == CONTINUATION
          and continuation == b"__name__='_preserved_c828_controller'\n" + original_controller + b'\n' + tail)
    pins = load(WORK / 'c828/PARENT_REVIEW_PINS.json')
    for name, digest in pins['files'].items():
        need(sha(read(WORK / 'c828' / name, 65536)) == digest, 'frozen_c828_source_pin')
    check('frozen_reviewed_sources_unchanged', len(pins['files']) == 9)
    protected = load(WORK / 'root/ARCHIVE.json')['protected']
    check('four_unrelated_dirty_files_preserved', len(protected) == 4 and all(sha(read(REPO / name, 16777216)) == digest for name, digest in protected.items()))
    host_before_raw = read(HOST / 'before-020/HOST_SNAPSHOT.json', 32768)
    host_mid_raw = read(HOST / 'final-020/HOST_SNAPSHOT.json', 32768)
    host_final_raw = read(HOST / 'final-021/HOST_SNAPSHOT.json', 32768)
    host_before, host_mid, host_final = map(decode, (host_before_raw, host_mid_raw, host_final_raw))
    need(sha(host_before_raw) == 'e2ec3c9cbfada3aa31f4474fe91ae41f8fdcec8ccc3aaa3edd52e90a9e268114'
         and sha(host_final_raw) == 'd5ed0f7528d803295ff802107a47d39d9e65e0bc7d70c1cd919fdc99aeb99708', 'actual_host_snapshot_pin')
    def host_differences(after):
        old = {row['unit']: row['properties'] for row in host_before['existing_units']}
        new = {row['unit']: row['properties'] for row in after['existing_units']}
        need(old.keys() == new.keys() and len(old) == 5, 'host_five_unit_identity')
        differences, ambient = [], []
        for unit in old:
            for key in old[unit].keys() | new[unit].keys():
                if old[unit].get(key) == new[unit].get(key): continue
                if unit == 'zzz-stage-observer.service' and key == 'InvocationID': ambient.append(key)
                else: differences.append((unit, key))
        return differences, ambient
    mid_diff, mid_ambient = host_differences(host_mid)
    final_diff, final_ambient = host_differences(host_final)
    comparison = load(HOST / 'compare-021-corrected/PRESERVATION_REVIEW.json', 32768)
    nonpass = load(HOST / 'compare-020/PRESERVATION_REVIEW.json', 32768)
    check('settled_five_existing_host_states_exact', final_diff == [] and len(final_ambient) == 1
          and comparison['success'] is True and comparison['non_ambient_difference_count'] == 0
          and comparison['existing_units_checked'] == 5 and comparison['ignored_observer_invocation_count'] == 1
          and comparison['before_snapshot_sha256'] == sha(host_before_raw) and comparison['final_snapshot_sha256'] == sha(host_final_raw))
    check('mid_observer_snapshot_NONPASS_and_local_path_typo_retained', len(mid_diff) == 5 and len(mid_ambient) == 1
          and all(unit in {'zzz-stage-observer.service', 'zzz-stage-observer.timer'} for unit, key in mid_diff)
          and nonpass['success'] is False and nonpass['non_ambient_difference_count'] == 5
          and nonpass['final_snapshot_sha256'] == sha(host_mid_raw) and list((HOST / 'compare-021').iterdir()) == [])
    check('saved_host_readonly_and_old_owned_groups_stopped', all(
        snapshot['read_only'] is True and snapshot['service_actions'] == 0
        and snapshot['production_approved'] is snapshot['public_signing'] is False
        and snapshot['all_seven_owned_labs_stopped'] is snapshot['original_HOST_BEFORE_preserved'] is True
        and snapshot['c7e4_unexecuted_footprint_absent'] is True
        and all(row['stopped'] is True for row in snapshot['owned_units'])
        for snapshot in (host_before, host_final)))
    report = {'schema': 1, 'kind': 'independent_saved_clean_root_stock_recovery_verification', 'ok': True,
        'source_commit': HEAD, 'accepted_hash': HASH, 'private_kit_files': 45, 'private_kit_raw_bytes': 808416,
        'private_eight_record_packet_rehashed': True, 'cost_wei': cost, 'inclusion_UTC_day': day,
        'actual_total_RPC': 2119, 'actual_capture_age_at_recovery_seconds': capture_age,
        'original_signed_keeper_transactions': 1, 'fixture_setup_governance_transactions_in_successful_case': 5,
        'target_transaction_attempt_delta': 0, 'checks': checks, 'inputs': dict(sorted(inputs.items())),
        'native_stdout_evidence_boundary': 'Native stdout bytes remain on the stopped private root; saved pinned worker checked their exact manifest/plan lines. Independent desktop review verifies raw restore plan and four captured process receipts, not a newly fetched stdout body.',
        'earlier_verifier_metadata_failure_retained': {'stage': 'saved_recovery_age', 'error_type': 'TypeError', 'cause': 'ISO health time was initially subtracted from integer manifest time; corrected only timestamp parsing after prior saved data checks passed.', 'application_or_native_rerun': False},
        'host_preservation': {'before020_sha256': sha(host_before_raw), 'settled_final021_sha256': sha(host_final_raw), 'existing_states': 5, 'nonambient_differences': 0, 'observer_invocation_differences': 1, 'earlier_mid_observer_NONPASS_differences': 5, 'local_compare_path_typo_retained': True, 'raw_host_details_published': False},
        'scope': 'Same-host clean application root reconstructed from exact private desktop kit, against a continuously retained isolated disposable chain.',
        'not_proved': ['physical second host', 'complete OS restoration', 'chain image restore', 'public-chain canonical truth', 'cross-host signing fencing', 'physical durability', 'sustained operation', 'production approval'],
        'readiness_approved': False, 'production_approved': False, 'actual_second_host': False,
        'review_activity': {'application_imports': 0, 'reviewed_application_or_helper_bodies_executed': 0, 'native_commands': 0, 'test_bodies': 0, 'server_calls': 0, 'network_requests': 0, 'own_saved_data_AST_hash_and_readonly_Git_blobs_only': True}}
    OUTPUT.write_bytes(enc(report))
    print(json.dumps({'ok': True, 'checks': len(checks), 'private_files': 45, 'cost_wei': cost, 'output_sha256': sha(OUTPUT.read_bytes())}))

if __name__ == '__main__':
    main()
