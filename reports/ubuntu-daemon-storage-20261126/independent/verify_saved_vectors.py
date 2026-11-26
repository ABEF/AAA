"""Offline independent c811 vector verification; no app imports or network.

Prepared before execution. Reads bounded saved public vectors and the exact
reviewed input archive. It never imports helper/production code or signs.
"""
from pathlib import Path
import argparse
import copy
import datetime as dt
import hashlib
import io
import json
import math
import re
import tarfile

HEAD = 'c07d5b153149f7c072ee5ff785c1cabac60197f6'
MONITOR = '90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'
LAB = '/opt/popl-ubuntu-daemon-storage-20261126-c811'
KEEPER = Path(LAB).name + '-keeper.service'
MODEL = Path(LAB).name + '-model.service'
RESOLVE = Path(LAB).name + '-resolve.service'
FROZEN = {
    'keeper_runtime.py': 'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4',
    'keeper_jobs.py': '363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4',
    'job_cases.py': '7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7',
}
REVIEWED_HELPERS = {
    'model_service.py': 'a02747cd750363b04280d0f01438338bfbbc4df73065d1d5a74b6825a1924eb4',
    'storage_control.py': '04943410dbb51c5f019ba6f8bd3c4d752653d7987631f02ec9865e90ee83f1bb',
    'native_base.py': 'fe476c1f95d1c72a9f604889c500f501d3e7fe951714edd7806e2ae406d72765',
}


def need(value, label):
    if not value:
        raise ValueError(label)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result, 'duplicate JSON field')
        result[key] = value
    return result


def decode(raw):
    def constant(_):
        raise ValueError('nonfinite JSON constant')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    need(type(value) is dict, 'JSON object required')
    return value


def read(path, maximum=2 * 1024 * 1024):
    need(path.is_file() and not path.is_symlink(), 'regular evidence file required')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    need(0 < len(raw) <= maximum, 'bounded evidence read exceeded')
    return raw


def quantity(value):
    need(type(value) is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})', value),
         'noncanonical RPC quantity')
    return int(value, 16)


def txhash(value):
    need(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{64}', value) and int(value, 16),
         'nonzero hash required')
    return value.lower()


def stamp(value):
    result = dt.datetime.fromisoformat(value).timestamp()
    need(math.isfinite(result), 'finite timestamp required')
    return result


def snapshot(record):
    need(type(record) is dict and type(record.get('raw_utf8')) is str, 'exact raw journal required')
    raw = record['raw_utf8'].encode('utf8')
    need(len(raw) <= 2 * 1024 * 1024 and sha(raw) == record['sha256'], 'journal byte digest differs')
    value = decode(raw)
    need(value == record['state'], 'raw journal interpretation differs')
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--campaign-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists(), 'new exclusive review output required')
    artifacts, checks = {}, []

    def load(name):
        candidates = [args.campaign_dir / name, args.campaign_dir / 'artifacts' / name]
        candidates += list(args.campaign_dir.glob('fetch-*/' + name))
        candidates = [path for path in candidates if path.is_file()]
        need(bool(candidates), 'missing public evidence: ' + name)
        values = [read(path) for path in candidates]
        need(len({sha(raw) for raw in values}) == 1, 'conflicting duplicate evidence: ' + name)
        artifacts[name] = {'bytes': len(values[0]), 'sha256': sha(values[0])}
        return decode(values[0])

    def passed(name):
        checks.append({'check': name, 'passed': True})

    build_raw = read(args.build_dir / 'BUILD_RECEIPT.json')
    build = decode(build_raw)
    source_raw = read(args.build_dir / 'SOURCE_MANIFEST.json')
    source = decode(source_raw)
    need(build['source_base'] == source['source_head'] == HEAD and
         build['source_manifest_sha256'] == sha(source_raw) and
         source['approved_worktree_overrides'] == [] and
         source['byte_equal_to_base_HEAD'] is True and
         source['unrelated_dirty_worktree_files_excluded'] is True and
         source['frozen_F6_Solidity_modified'] is False and len(source['members']) == 191,
         'exact current source identity differs')
    need(source['members']['keeper/monitor.py']['sha256'] == MONITOR,
         'current monitor source differs')
    archive_raw = read(args.build_dir / 'c811.inputs.tar.gz', 96 * 1024 * 1024)
    need(build['bundle'] == {'bytes': len(archive_raw), 'sha256': sha(archive_raw)}, 'archive pin differs')
    with tarfile.open(fileobj=io.BytesIO(archive_raw), mode='r:gz') as archive:
        members = archive.getmembers()
        need(len({member.name for member in members}) == len(members) and
             all(member.isfile() and 0 <= member.size <= 128 * 1024 * 1024 for member in members) and
             sum(member.size for member in members) <= 128 * 1024 * 1024,
             'archive members or expanded bound differ')
        manifest = decode(archive.extractfile('MANIFEST.json').read())
        need(manifest['source_head'] == HEAD and manifest['source_manifest_sha256'] == sha(source_raw),
             'archive source manifest binding differs')
        need(set(manifest['members']) == {member.name for member in members} - {'MANIFEST.json'},
             'archive inventory differs')
        need({member.name.removeprefix('source/contracts/') for member in members
              if member.name.startswith('source/contracts/')} == set(source['members']),
             'complete production archive source inventory differs')
        for member in members:
            if member.name == 'MANIFEST.json':
                continue
            raw = archive.extractfile(member).read()
            need(manifest['members'][member.name] == {'bytes': len(raw), 'sha256': sha(raw)},
                 'archive member pin differs')
            if member.name.startswith('source/contracts/'):
                need(source['members'][member.name.removeprefix('source/contracts/')] ==
                     {'bytes': len(raw), 'sha256': sha(raw)}, 'production member source differs')
            if member.name.startswith('source/helpers/'):
                name = member.name.removeprefix('source/helpers/')
                need(build['helpers'][name] == {'bytes': len(raw), 'sha256': sha(raw)}, 'helper pin differs')
                need(read(args.build_dir / name) == raw if (args.build_dir / name).exists() else name in FROZEN,
                     'prepared helper changed after packaging')
                if name in FROZEN:
                    need(sha(raw) == FROZEN[name], 'frozen setup helper differs')
                else:
                    need(name in REVIEWED_HELPERS and sha(raw) == REVIEWED_HELPERS[name],
                         'independently reviewed new helper differs')
    for name, key in (('remote_capsule.py', 'controller'), ('host_control.py', 'host_wrapper')):
        raw = read(args.build_dir / name)
        need(build[key] == {'bytes': len(raw), 'sha256': sha(raw)}, 'closed controller pin differs')
    passed('current_HEAD_191_production_members_frozen_helpers_and_closed_controller_pins')

    orchestration = load('ORCHESTRATION_RESULT.json')
    need(orchestration['success'] is True and orchestration['completed'] is True and
         orchestration['cleanup'] is True and orchestration['failure'] is None and
         orchestration['old_test_bodies_run'] == orchestration['new_test_bodies_run'] == 0 and
         orchestration['new_composed_scenarios'] == 1 and orchestration['public_transactions'] ==
         orchestration['new_seals'] == 0 and orchestration['elapsed_seconds'] <= 840,
         'bounded isolated orchestration did not complete')
    actions = orchestration['actions']
    expected = ['upload', 'install', 'start', 'startkeeper', 'prove', 'repair', 'resolve', 'resume']
    ordered = [row['action'] for row in actions if row.get('action') in expected]
    need(ordered == expected and all(row.get('exit_code') == 0 and row.get('reason') is None
         for row in actions if row.get('action') != 'cleanup_observation'), 'closed operation ordering differs')
    result = load('model-RESULT.json')
    need(result['success'] is True and result['source_head'] == HEAD and
         result['raw_attempts'] == result['raw_forwarded'] == 1 and
         0 < result['shared_RPC_requests'] <= 6000 and result['old_feature_journeys_or_tests_run'] ==
         result['public_transactions'] == result['new_seals'] == 0, 'actual scenario counter/source differs')
    passed('one_new_scenario_no_prior_test_bodies_one_original_submission_bounded_6000_RPC_840s')

    ready = load('model-READY.json')
    initial_record = load('case-INITIAL_JOURNAL.json')
    initial = snapshot(initial_record)
    accepted = load('case-HASH_SAVE_FAULT_ARMED.json')
    blocked = load('case-HASHLESS_RESTART_BLOCKED.json')
    accepted_state = snapshot({'sha256': accepted['journal_sha256'],
                               'raw_utf8': accepted['journal_raw_utf8'], 'state': accepted['state']})
    blocked_state = snapshot({'sha256': blocked['journal_sha256'],
                              'raw_utf8': blocked['raw_utf8'], 'state': blocked['state']})
    h = txhash(accepted['accepted_hash'])
    intent = accepted['intent']
    need(initial['pending'] is None and initial['next_nonce'] == 0 and initial['spent'] == {} and
         ready['original_journal_sha256'] == initial_record['sha256'] and
         accepted_state['pending'] == intent and intent['hash'] is None and intent['nonce'] == 0 and
         accepted_state['next_nonce'] == 0 and accepted_state['spent'] == {} and
         accepted_state == blocked_state and accepted['journal_sha256'] == blocked['journal_sha256'] and
         blocked['accepted_hash'] == h and blocked['no_resend'] is True,
         'original durable hashless intent was not preserved')
    need(accepted['actor_path'] == LAB + '/runtime/run-001/model/supervisor/actor' and
         accepted['mode_before'] == '0700' and accepted['mode_fault'] == '0500' and
         accepted['configuration_sha256'] == ready['configuration_sha256'] and
         blocked['health']['status'] == 'recovery_required' and blocked['health']['pending'] is True and
         blocked['health']['pending_action'] == intent['key'] and
         stamp(blocked['health']['time']) >= accepted['utc'], 'repaired actual hashless restart proof differs')
    need(accepted['semantic_configuration_sha256'] == ready['semantic_configuration_sha256'] ==
         blocked['health']['configuration_sha256'], 'semantic configuration identity differs')
    passed('actual_acceptance_fault_then_exact_hashless_same_journal_restart_block')

    proof = load('native-FAULT_PROOF.json')
    repair = load('native-REPAIR.json')
    need(proof['accepted_hash'] == h and proof['journal_sha256'] == accepted['journal_sha256'] and
         repair['accepted_hash'] == h and repair['journal_sha256'] == proof['journal_sha256'] and
         repair['lock_identity'] == proof['lock_identity'] and
         repair['repair'] == 'ONLY_actor_directory_0500_to_0700', 'native repair identity differs')
    errors, halts = proof['cycle_errors'], proof['halts']
    need(errors and halts and all(row['os_errno'] == 'EACCES' for row in errors + halts) and
         stamp(errors[0]['time']) <= stamp(halts[0]['time']), 'original EACCES diagnostic order differs')
    events = proof['stock_log_events']
    reconciliation = [row for row in events if row.get('event') == 'submission_requires_reconciliation']
    need(len(reconciliation) == 1 and reconciliation[0]['reported_transaction'] == h and
         reconciliation[0]['os_errno'] == 'EACCES' and
         events.index(reconciliation[0]) < events.index(errors[0]) < events.index(halts[0]),
         'original strict candidate diagnostic/order differs')
    failed_native = proof['native_snapshot']
    failed_keeper = failed_native['units'][KEEPER]
    need(failed_keeper['properties'].get('MainPID', '0') == '0' and not failed_keeper['cgroup']['pids'],
         'original writer not fenced at repair')
    exits = [row for row in failed_keeper.get('manager_journal', [])
             if row.get('MESSAGE_ID') == '98e322203f7a4ed290d09fe03c09fe15' and
             row.get('EXIT_CODE') == 'exited' and str(row.get('EXIT_STATUS')) == '1']
    need(bool(exits), 'actual manager exit1 evidence absent')
    passed('genuine_EACCES_natural_daemon_exit_empty_group_and_only_directory_repair')

    resolution = load('native-RESOLUTION_RECEIPT.json')
    marker = load('native-RESOLUTION_COMPLETE.json')
    resolution_ready = load('case-RESOLUTION_READY.json')
    adopted = snapshot(resolution_ready['resolved_journal'])
    expected_adopted = copy.deepcopy(accepted_state)
    expected_adopted['pending']['hash'] = h
    need(adopted == expected_adopted and marker == resolution_ready['root_marker'] and
         marker['accepted_hash'] == resolution['accepted_hash'] == h and
         marker['state_sha256'] == resolution['state_sha256'] == resolution_ready['resolved_journal']['sha256'] and
         marker['signing_enabled'] is False and marker['manager_wait_completion'] is True,
         'explicit resolver changed more than original hash')
    command = resolution['result']['direct_exec_argv']
    need(command == ['/usr/bin/python3', '-m', 'keeper.monitor', '--config',
                     LAB + '/runtime/run-001/model/supervisor/actor/config.json', '--resolve-pending', h] and
         resolution['result']['manager_wait_completion'] is True and
         resolution['result']['manager_wait_returncode'] == 0, 'resolver was not exact successful nonsigning CLI')
    need(quantity(resolution_ready['head']['number']) - quantity(resolution_ready['receipt']['blockNumber']) + 1 == 12,
         'twelve actual confirmations absent after hash-only resolution')
    passed('fenced_exact_no_live_resolver_hash_only_adoption_then_twelve_confirmations')

    recovered_record = load('case-RECOVERED_JOURNAL.json')
    recovered = snapshot(recovered_record['journal'])
    tx, receipt, header, head = (recovered_record[key] for key in
                                ('transaction_without_signature', 'receipt', 'receipt_block', 'head'))
    accepted_tx = accepted['transaction_without_signature']
    need(not {'r', 's', 'v', 'yParity'} & set(tx) and not {'r', 's', 'v', 'yParity'} & set(accepted_tx),
         'signature components unexpectedly exported')
    fee = intent['fee_review']
    for transaction in (tx, accepted_tx):
        need(txhash(transaction['hash']) == h and transaction['from'].lower() == ready['sender'] ==
             accepted_state['sender'] and transaction['to'].lower() == intent['to'] and
             transaction['input'].lower() == intent['data'].lower() and quantity(transaction['nonce']) == 0 and
             quantity(transaction['value']) == intent['value'] == 0 and quantity(transaction['chainId']) == 4663 and
             quantity(transaction['gas']) == fee['gas_limit'], 'original signed transaction identity differs')
        kind = quantity(transaction.get('type') or '0x0')
        cap = quantity(transaction['maxFeePerGas'] if kind == 2 else transaction['gasPrice'])
        need(kind in (0, 1, 2) and cap == fee['max_fee_per_gas'], 'signed fee cap differs')
    kind = quantity(tx.get('type') or '0x0')
    cap = fee['max_fee_per_gas']
    if kind == 2:
        base, priority = quantity(header['baseFeePerGas']), quantity(tx['maxPriorityFeePerGas'])
        need(priority <= cap and base <= cap, 'invalid canonical dynamic fee inputs')
        price = min(cap, base + priority)
    else:
        price = cap
        need(quantity(receipt['effectiveGasPrice']) == price, 'legacy receipt contradicts signed gas price')
    used, l1 = quantity(receipt['gasUsed']), quantity(receipt.get('l1Fee', '0x0'))
    paid = used * price + l1
    need(fee['schema'] == 1 and 0 < used <= fee['gas_limit'] <= 24000000 and
         0 < price <= cap <= 5000000000 and l1 == fee['l1_fee_allowance_wei'] == 0 and
         fee['receipt_fee_policy'] == 'included' and
         fee['maximum_cost_wei'] == fee['gas_limit'] * cap <= 10**16 and
         paid == recovered_record['paid_wei'] <= fee['maximum_cost_wei'], 'canonical fee calculation/bounds differ')
    number, timestamp = quantity(header['number']), quantity(header['timestamp'])
    need(receipt['status'] == '0x1' and txhash(receipt['transactionHash']) == h and
         receipt['from'].lower() == ready['sender'] and receipt['to'].lower() == intent['to'] and
         receipt['blockHash'] == tx['blockHash'] == header['hash'] and
         receipt['blockNumber'] == tx['blockNumber'] == header['number'] and
         receipt['transactionIndex'] == tx['transactionIndex'] and
         quantity(head['number']) - number + 1 >= 12 and timestamp <= quantity(head['timestamp']),
         'canonical transaction receipt inclusion/depth differs')
    day = dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).date().isoformat()
    observation = {'transaction': h, 'reported_price_wei': quantity(receipt['effectiveGasPrice']),
                   'execution_price_wei': price, 'gas_used': used, 'l1_fee_wei': l1,
                   'receipt_fee_policy': 'included', 'cost_wei': paid}
    need(recovered['pending'] is None and recovered['next_nonce'] == 1 and recovered['spent'] == {day: paid} and
         recovered['receipt_anchor'] == {'number': number, 'hash': header['hash'], 'timestamp': timestamp, 'nonce': 0} and
         recovered['last_fee_observation'] == observation and recovered['last'][intent['key']] == timestamp,
         'exact once-only canonical accounting differs')
    passed('independent_signed_cap_plus_canonical_header_fee_exact_day_nonce_anchor_and_harvest_clock')

    healthy = load('case-HEALTHY_NORMAL_CYCLE.json')
    refresh = load('case-RECOVERY_REFRESH_HEALTH.json')
    timing = load('case-HEALTHY_TIMING.json')
    healthy_state = snapshot(load('case-HEALTHY_JOURNAL.json'))
    final = snapshot(load('case-FINAL_JOURNAL.json'))
    need(healthy['status'] == 'healthy_v2' and healthy['live'] is True and healthy['pending'] is False and
         healthy['pending_action'] is None and healthy['chain_id'] == 4663 and healthy['sender'] == ready['sender'],
         'fresh normal healthy view differs')
    need(refresh['status'] == 'degraded' and refresh['pending'] is False and
         refresh['rebalance_confirmation_health']['policy']['state'] == 'pending_recovery',
         'distinct degraded receipt-recovery cycle absent')
    elapsed = stamp(healthy['time']) - stamp(refresh['time'])
    need(healthy['configuration_sha256'] == blocked['health']['configuration_sha256'] ==
         accepted['semantic_configuration_sha256'] and
         timing['configured_interval_seconds'] == 240 and timing['configured_confirmations'] == 12 and
         timing['poll_delay_or_configuration_changed'] is False and
         timing['minimum_observation_allowance_seconds'] == 239 and
         timing['recovery_health_utc'] == stamp(refresh['time']) and
         timing['healthy_health_utc'] == stamp(healthy['time']) and
         abs(timing['health_elapsed_seconds'] - elapsed) < 0.00001 and elapsed >= 239 and
         timing['monotonic_elapsed_seconds'] >= 239 and
         timing['recovery_observed_utc'] == recovered_record['recovery_observed_utc'],
         'fresh normal cycle timing/source-preserved interval differs')
    for state in (healthy_state, final):
        for key in ('pending', 'next_nonce', 'spent', 'receipt_anchor', 'last_fee_observation'):
            need(state[key] == recovered[key], 'settled accounting changed after recovery')
        need(state['last'][intent['key']] == timestamp, 'harvest clock repeated or lost')
    need(healthy_state == final, 'final journal changed after healthy capture')
    need(load('case-FINANCIAL_BEFORE.json') == load('case-FINANCIAL_AFTER.json'),
         'NFT rights LP custody or classified backing changed')
    passed('fresh240second_normal_cycle_no_second_charge_and_exact_rights_backing_preserved')

    stopped = load('native-FINAL_STOP.json')
    final_native = orchestration['final_status']['native']
    for unit in (KEEPER, MODEL, RESOLVE):
        row = final_native['units'][unit]
        need(row['properties'].get('MainPID', '0') == '0' and not row['cgroup']['pids'] and
             row['properties'].get('ActiveState') in ('inactive', 'failed', None), 'owned group remains live')
    need(stopped['phase'] == 'stopped', 'native final stop receipt absent')
    passed('owned_keeper_resolver_model_groups_empty_after_final_journal_capture')

    output = {'schema': 1, 'success': True, 'source_head': HEAD, 'checks': checks,
              'actual_paid_keeper_transactions': 1, 'keeper_raw_resends': 0, 'paid_wei': paid,
              'canonical_execution_price_wei': price, 'gas_used': used,
              'RPC_requests': result['shared_RPC_requests'], 'elapsed_seconds': orchestration['elapsed_seconds'],
              'artifacts': artifacts,
              'build_receipt_sha256': sha(build_raw), 'source_manifest_sha256': sha(source_raw),
              'verifier_sha256': sha(Path(__file__).read_bytes()),
              'scope': 'finite_same_host_two_NFT_single_main_zero_fee_daemon_EACCES_restart_recovery',
              'production_approved': False, 'unchanged_tests_rerun': 0,
              'external_host_preservation_review_required': True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(output, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'success': True, 'checks': len(checks), 'paid_wei': paid}, sort_keys=True))


if __name__ == '__main__':
    main()
