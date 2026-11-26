"""Separate offline c811 reconciliation; original campaign remains NONPASS.

Uses saved actual transaction/journals, the original structured stock log and a
separately authorized read of the already stopped lab. No replay, application
imports, network, signing, journal edit or assertion override is performed.
"""
from pathlib import Path
import argparse
import copy
import datetime as dt
import importlib.util
import io
import json
import tarfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('prepared_vector_primitives', HERE / 'verify_saved_vectors.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
need, sha, read, decode = P.need, P.sha, P.read, P.decode
q, snapshot, stamp, txhash = P.quantity, P.snapshot, P.stamp, P.txhash
LOG_SHA = 'ba1cdabfd46ea8fe7a2a7b517fee0b3f2e7ff31536f44941931c89c123af2d42'
POSTRUN_REMOTE_SHA = '03ea8998a319fa260a2b94807088ab70f5fd36bb1faca01965da4e3b0dd5fb76'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--campaign-dir', type=Path, required=True)
    parser.add_argument('--postrun-dir', type=Path, required=True)
    parser.add_argument('--stock-log', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists(), 'exclusive separate reconciliation output required')
    artifacts, checks = {}, []

    def remember(name, raw):
        artifacts[name] = {'bytes': len(raw), 'sha256': sha(raw)}

    def load(name):
        candidates = [args.campaign_dir / name, args.campaign_dir / 'artifacts' / name]
        candidates += list(args.campaign_dir.glob('fetch-*/' + name))
        candidates = [path for path in candidates if path.is_file()]
        need(bool(candidates), 'missing original public vector: ' + name)
        values = [read(path) for path in candidates]
        need(len({sha(raw) for raw in values}) == 1, 'conflicting original vector: ' + name)
        remember(name, values[0])
        return decode(values[0])

    def passed(name):
        checks.append({'check': name, 'passed': True})

    build_raw, source_raw = (read(args.build_dir / name) for name in
                             ('BUILD_RECEIPT.json', 'SOURCE_MANIFEST.json'))
    build, source = decode(build_raw), decode(source_raw)
    need(build['source_base'] == source['source_head'] == P.HEAD and
         source['byte_equal_to_base_HEAD'] is True and source['approved_worktree_overrides'] == [] and
         source['frozen_F6_Solidity_modified'] is False and len(source['members']) == 191 and
         build['source_manifest_sha256'] == sha(source_raw) and
         source['members']['keeper/monitor.py']['sha256'] == P.MONITOR,
         'current exact production source binding differs')
    archive_raw = read(args.build_dir / 'c811.inputs.tar.gz', 96 * 1024 * 1024)
    need(build['bundle'] == {'bytes': len(archive_raw), 'sha256': sha(archive_raw)}, 'original archive pin differs')
    with tarfile.open(fileobj=io.BytesIO(archive_raw), mode='r:gz') as archive:
        members = archive.getmembers()
        need(all(member.isfile() for member in members) and
             len({member.name for member in members}) == len(members) and
             sum(member.size for member in members) <= 128 * 1024 * 1024, 'archive scope/bound differs')
        manifest = decode(archive.extractfile('MANIFEST.json').read())
        need(manifest['source_head'] == P.HEAD and manifest['source_manifest_sha256'] == sha(source_raw) and
             set(manifest['members']) == {member.name for member in members} - {'MANIFEST.json'},
             'archive member inventory differs')
        production = set()
        for member in members:
            raw = archive.extractfile(member).read()
            if member.name == 'MANIFEST.json':
                continue
            pin = {'bytes': len(raw), 'sha256': sha(raw)}
            need(manifest['members'][member.name] == pin, 'original archived member differs')
            if member.name.startswith('source/contracts/'):
                name = member.name.removeprefix('source/contracts/')
                production.add(name)
                need(source['members'][name] == pin, 'archived production source pin differs')
            elif member.name.startswith('source/helpers/'):
                name = member.name.removeprefix('source/helpers/')
                expected = {**P.FROZEN, **P.REVIEWED_HELPERS}
                need(name in expected and sha(raw) == expected[name] and build['helpers'][name] == pin,
                     'executed helper differs from independent pre-execution review')
        need(production == set(source['members']), 'full191 production source scope differs')
        monitor = archive.extractfile('source/contracts/keeper/monitor.py').read().decode('utf8')
    need(monitor.index('if self.rebalance_confirmation.version in (1,2,3) and known and not self._cycle_error:') <
         monitor.index("if getattr(self,'_recovery_refresh_due',False) and not self._cycle_error:") and
         'delay = min(delay,remaining)' in monitor and 'return max(1,delay)' in monitor,
         'known confirmation deadline priority source differs')
    for name, key in (('remote_capsule.py', 'controller'), ('host_control.py', 'host_wrapper')):
        raw = read(args.build_dir / name)
        need(build[key] == {'bytes': len(raw), 'sha256': sha(raw)}, 'closed controller source differs')
    remember('BUILD_RECEIPT.json', build_raw)
    remember('SOURCE_MANIFEST.json', source_raw)
    passed('exact191_HEAD_sources_frozen_F6_helpers_and_preserved_deadline_priority')

    campaign, result = load('ORCHESTRATION_RESULT.json'), load('model-RESULT.json')
    need(campaign['success'] is False and campaign['completed'] is False and campaign['cleanup'] is True and
         campaign['failure']['fixed_reason'] == 'Private model exited before model-COMPLETE.json' and
         result['success'] is False and result['error_class'] == 'HarnessRefusal' and
         result['fixed_guard'] == 'Fresh healthy cycle did not retain the normal240second wait' and
         result['failure_stage'] == 'await_next_normal_240second_cycle' and
         result['raw_attempts'] == result['raw_forwarded'] == 1 and
         result['shared_RPC_requests'] <= 6000 and campaign['elapsed_seconds'] <= 840 and
         campaign['old_test_bodies_run'] == campaign['new_test_bodies_run'] == 0 and
         campaign['new_composed_scenarios'] == 1 and result['public_transactions'] == result['new_seals'] == 0,
         'original NONPASS or its specific harness-only refusal was altered')
    passed('original_campaign_and_model_NONPASS_preserved_exactly_no_financial_replay')

    ready, initial = load('model-READY.json'), snapshot(load('case-INITIAL_JOURNAL.json'))
    accepted, blocked = load('case-HASH_SAVE_FAULT_ARMED.json'), load('case-HASHLESS_RESTART_BLOCKED.json')
    accepted_state = snapshot({'sha256': accepted['journal_sha256'],
                               'raw_utf8': accepted['journal_raw_utf8'], 'state': accepted['state']})
    blocked_state = snapshot({'sha256': blocked['journal_sha256'],
                              'raw_utf8': blocked['raw_utf8'], 'state': blocked['state']})
    h, intent = txhash(accepted['accepted_hash']), accepted['intent']
    need(initial['pending'] is None and initial['next_nonce'] == 0 and initial['spent'] == {} and
         accepted_state == blocked_state and accepted_state['pending'] == intent and intent['hash'] is None and
         intent['nonce'] == accepted_state['next_nonce'] == 0 and accepted_state['spent'] == {} and
         accepted['mode_before'] == '0700' and accepted['mode_fault'] == '0500' and
         accepted['actor_path'] == P.LAB + '/runtime/run-001/model/supervisor/actor' and
         blocked['accepted_hash'] == h and blocked['health']['status'] == 'recovery_required' and
         blocked['health']['pending'] is True and blocked['health']['pending_action'] == intent['key'] and
         stamp(blocked['health']['time']) >= accepted['utc'], 'actual hashless journal/restart differs')
    proof, repair = load('native-FAULT_PROOF.json'), load('native-REPAIR.json')
    events = proof['stock_log_events']
    submissions = [row for row in events if row.get('event') == 'submission_requires_reconciliation']
    errors = [row for row in events if row.get('event') == 'cycle_failed' and row.get('os_errno') == 'EACCES']
    halts = [row for row in events if row.get('event') == 'keeper_halted' and row.get('os_errno') == 'EACCES']
    need(len(submissions) == 1 and submissions[0]['reported_transaction'] == h and
         submissions[0]['os_errno'] == 'EACCES' and errors and halts and
         events.index(submissions[0]) < events.index(errors[0]) < events.index(halts[0]) and
         proof['accepted_hash'] == repair['accepted_hash'] == h and
         proof['journal_sha256'] == repair['journal_sha256'] == accepted['journal_sha256'] and
         repair['repair'] == 'ONLY_actor_directory_0500_to_0700' and
         proof['lock_identity'] == repair['lock_identity'], 'genuine failure/only-directory repair differs')
    failed_keeper = proof['native_snapshot']['units'][P.KEEPER]
    need(failed_keeper['properties'].get('MainPID', '0') == '0' and not failed_keeper['cgroup']['pids'] and
         any(row.get('MESSAGE_ID') == '98e322203f7a4ed290d09fe03c09fe15' and
             row.get('EXIT_CODE') == 'exited' and str(row.get('EXIT_STATUS')) == '1'
             for row in failed_keeper['manager_journal']), 'natural exit1/empty first writer not proved')
    passed('real_accepted_hash_EACCES_original_diagnostics_natural_exit_and_hashless_restart_no_resend')

    resolver, marker, resolution_ready = (load(name) for name in
        ('native-RESOLUTION_RECEIPT.json', 'native-RESOLUTION_COMPLETE.json', 'case-RESOLUTION_READY.json'))
    adopted = snapshot(resolution_ready['resolved_journal'])
    expected = copy.deepcopy(accepted_state)
    expected['pending']['hash'] = h
    need(adopted == expected and marker == resolution_ready['root_marker'] and
         marker['accepted_hash'] == resolver['accepted_hash'] == h and
         marker['state_sha256'] == resolver['state_sha256'] == resolution_ready['resolved_journal']['sha256'] and
         resolver['result']['direct_exec_argv'] == ['/usr/bin/python3', '-m', 'keeper.monitor', '--config',
           P.LAB + '/runtime/run-001/model/supervisor/actor/config.json', '--resolve-pending', h] and
         resolver['result']['manager_wait_completion'] is True and resolver['result']['manager_wait_returncode'] == 0 and
         marker['signing_enabled'] is False and
         q(resolution_ready['head']['number']) - q(resolution_ready['receipt']['blockNumber']) + 1 == 12,
         'exact no-live hash-only resolution or twelve confirmations differs')
    passed('explicit_no_live_hash_only_resolution_before_twelve_actual_confirmations')

    recovered_record, final_record = load('case-RECOVERED_JOURNAL.json'), load('case-FINAL_JOURNAL.json')
    recovered, final = snapshot(recovered_record['journal']), snapshot(final_record)
    tx, receipt, header, head = (recovered_record[key] for key in
        ('transaction_without_signature', 'receipt', 'receipt_block', 'head'))
    fee = intent['fee_review']
    for transaction in (accepted['transaction_without_signature'], tx):
        need(not {'r', 's', 'v', 'yParity'} & set(transaction) and txhash(transaction['hash']) == h and
             transaction['from'].lower() == ready['sender'] == accepted_state['sender'] and
             transaction['to'].lower() == intent['to'] and transaction['input'].lower() == intent['data'].lower() and
             q(transaction['nonce']) == 0 and q(transaction['value']) == intent['value'] == 0 and
             q(transaction['chainId']) == 4663 and q(transaction['gas']) == fee['gas_limit'],
             'original signed public identity differs')
        kind = q(transaction.get('type') or '0x0')
        cap = q(transaction['maxFeePerGas'] if kind == 2 else transaction['gasPrice'])
        need(kind in (0, 1, 2) and cap == fee['max_fee_per_gas'], 'original captured signed cap differs')
    kind, cap = q(tx.get('type') or '0x0'), fee['max_fee_per_gas']
    if kind == 2:
        base, priority = q(header['baseFeePerGas']), q(tx['maxPriorityFeePerGas'])
        need(base <= cap and priority <= cap, 'canonical signed fee inputs invalid')
        price = min(cap, base + priority)
    else:
        price = cap
        need(q(receipt['effectiveGasPrice']) == price, 'legacy execution price differs')
    used, l1 = q(receipt['gasUsed']), q(receipt.get('l1Fee', '0x0'))
    paid = used * price + l1
    need(fee['schema'] == 1 and 0 < used <= fee['gas_limit'] <= 24000000 and
         0 < price <= cap <= 5000000000 and l1 == fee['l1_fee_allowance_wei'] == 0 and
         fee['receipt_fee_policy'] == 'included' and fee['maximum_cost_wei'] == fee['gas_limit'] * cap <= 10**16 and
         paid == recovered_record['paid_wei'] <= fee['maximum_cost_wei'], 'independent canonical fee calculation differs')
    number, timestamp = q(header['number']), q(header['timestamp'])
    need(receipt['status'] == '0x1' and receipt['transactionHash'] == tx['hash'] == h and
         receipt['from'].lower() == ready['sender'] and receipt['to'].lower() == intent['to'] and
         receipt['blockHash'] == tx['blockHash'] == header['hash'] and
         receipt['blockNumber'] == tx['blockNumber'] == header['number'] and
         receipt['transactionIndex'] == tx['transactionIndex'] and
         q(head['number']) - number + 1 >= 12 and timestamp <= q(head['timestamp']),
         'canonical original inclusion differs')
    day = dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).date().isoformat()
    observation = {'transaction': h, 'reported_price_wei': q(receipt['effectiveGasPrice']),
        'execution_price_wei': price, 'gas_used': used, 'l1_fee_wei': l1,
        'receipt_fee_policy': 'included', 'cost_wei': paid}
    need(recovered['pending'] is None and recovered['next_nonce'] == 1 and recovered['spent'] == {day: paid} and
         recovered['receipt_anchor'] == {'number': number, 'hash': header['hash'], 'timestamp': timestamp, 'nonce': 0} and
         recovered['last_fee_observation'] == observation and recovered['last'][intent['key']] == timestamp,
         'once-only canonical receipt accounting differs')
    for key in ('pending', 'next_nonce', 'spent', 'receipt_anchor', 'last_fee_observation', 'last'):
        need(final[key] == recovered[key], 'settled accounting changed after actual recovery')
    passed('independent_canonical_fees_day_nonce_anchor_and_harvest_clock_booked_once')

    post_raw, post_exec_raw = (read(args.postrun_dir / name) for name in ('STOPPED_HEALTH.json', 'EXECUTION.json'))
    post, post_exec = decode(post_raw), decode(post_exec_raw)
    post_stdout = read(args.postrun_dir / 'stdout.raw', 3 * 1024 * 1024)
    need(post_exec['remote_source_sha256'] == POSTRUN_REMOTE_SHA and
         post_exec['stdout_sha256'] == sha(post_stdout) and decode(post_stdout) == post,
         'reviewed read-only source/transport capture binding differs')
    remember('STOPPED_HEALTH.json', post_raw)
    remember('STOPPED_HEALTH_EXECUTION.json', post_exec_raw)
    need(post_exec['exit_code'] == 0 and post_exec['capture_reason'] is None and post['read_only'] is True and
         post['service_actions'] == 0 and post['application_code_executed'] is False and post['secrets_exported'] is False and
         post['lab'] == P.LAB and post['configured_interval_seconds'] == 240 and
         post['configured_confirmations'] == 12 and post['configured_max_gas_limit'] == 24000000,
         'separate stopped-lab read is not authentic bounded read-only evidence')
    health = snapshot(post['health'])
    need(snapshot(post['journal']) == final and post['journal']['sha256'] == final_record['sha256'] and
         post['configuration_raw_sha256'] == ready['configuration_sha256'] == accepted['configuration_sha256'] and
         post['configuration_semantic_sha256'] == health['configuration_sha256'] ==
         ready['semantic_configuration_sha256'] == accepted['semantic_configuration_sha256'],
         'post-stop exact journal/configuration identities differ')
    need(health['status'] == 'healthy_v2' and health['live'] is True and health['pending'] is False and
         health['pending_action'] is None and health['chain_id'] == 4663 and health['sender'] == ready['sender'] and
         health['rebalance_confirmation_health']['policy']['state'] == 'observed_this_cycle',
         'actual fresh normal healthy cycle not retained')
    log_raw = read(args.stock_log, 512 * 1024)
    need(sha(log_raw) == LOG_SHA, 'original stock structured log digest differs')
    log = [decode(line) for line in log_raw.splitlines()]
    remember('native-keeper.stdout.log', log_raw)
    confirmed = [row for row in log if row.get('event') == 'confirmed']
    degraded = [row for row in log if row.get('event') == 'cycle_completed' and row.get('status') == 'degraded']
    healthy = [row for row in log if row.get('event') == 'cycle_completed' and row.get('status') == 'healthy_v2']
    need(len(confirmed) == len(degraded) == len(healthy) == 1 and confirmed[0]['transaction'] == h and
         int(confirmed[0]['cost_wei']) == paid and log.index(confirmed[0]) < log.index(degraded[0]) < log.index(healthy[0]) and
         healthy[0]['pending'] is False and healthy[0]['skipped_buckets'] == 0 and
         abs(stamp(healthy[0]['time']) - stamp(health['time'])) < 1,
         'original actual confirmed/degraded/healthy process records differ')
    elapsed = stamp(healthy[0]['time']) - stamp(degraded[0]['time'])
    need(0 < elapsed < 239, 'original timing refusal was not reproduced from actual log')
    old_schedules, new_schedules = recovered['observed_adjustment_v3'], final['observed_adjustment_v3']
    need(len(old_schedules) == len(new_schedules) == 1 and set(old_schedules) == set(new_schedules),
         'retained known confirmation schedule absent')
    key = next(iter(old_schedules))
    old, new = old_schedules[key], new_schedules[key]
    need(old == accepted_state['observed_adjustment_v3'][key] and old['execute_after'] == new['execute_after'] == 0 and
         old['identity'] == new['identity'] and old['next_check_at'] - old['last_checked_at'] == 240 and
         new['last_checked_at'] >= old['next_check_at'] and
         new['next_check_at'] - new['last_checked_at'] == 240,
         'earlier persisted deadline/actual next sample relation differs')
    changed = {name for name in set(recovered) | set(final) if recovered.get(name) != final.get(name)}
    need(changed <= {'conversion_turn', 'observed_adjustment_v3'}, 'unexpected settled journal behavior changed')
    passed('actual_fresh_healthy_cycle_preserves240_config_earlier_known_deadline_is_not_minimum_wait')

    native = campaign['final_status']['native']
    for unit in (P.KEEPER, P.MODEL, P.RESOLVE):
        row = native['units'][unit]
        need(row['properties'].get('MainPID', '0') == '0' and not row['cgroup']['pids'], 'original owned group not empty')
        for phase in ('before_units', 'after_units'):
            need(post[phase][unit].get('MainPID', '0') == '0' and
                 post[phase][unit].get('ActiveState') in ('inactive', 'failed'), 'post-read owned unit not stopped')
    need(load('native-FINAL_STOP.json')['phase'] == 'stopped', 'original owned stop receipt absent')
    need(not list(args.campaign_dir.glob('fetch-*/case-FINANCIAL_AFTER.json')),
         'unexpected financial-after vector requires scope review')
    passed('original_recursive_groups_empty_and_post_read_units_stopped_missing_after_vectors_explicit')

    output = {'schema': 1, 'core_recovery_verified': True, 'actual_healthy_cycle_verified': True,
        'original_campaign_success': False, 'original_model_success': False,
        'original_timing_assertion_passed': False, 'full_planned_scenario_pass': False,
        'financial_after_vectors_available': False, 'source_head': P.HEAD,
        'checks': checks, 'artifacts': artifacts, 'actual_paid_keeper_transactions': 1,
        'keeper_raw_resends': 0, 'paid_wei': paid, 'gas_used': used, 'canonical_execution_price_wei': price,
        'shared_RPC_requests': result['shared_RPC_requests'], 'original_elapsed_seconds': campaign['elapsed_seconds'],
        'actual_degraded_to_healthy_seconds': elapsed,
        'timing_correction': '240 is outer polling interval; preserved known confirmation deadline can wake earlier',
        'unchanged_test_bodies_rerun': 0, 'financial_scenarios_replayed': 0,
        'production_approved': False, 'external_host_preservation_review_required': True,
        'missing_scope': ['new physical/rights/backing after-state vectors were not captured before harness refusal',
                         'no physical power-loss, off-host fencing, sustained operation or actual-provider qualification'],
        'verifier_sha256': sha(Path(__file__).read_bytes()),
        'primitives_source_sha256': sha((HERE / 'verify_saved_vectors.py').read_bytes())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(output, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'core_recovery_verified': True, 'original_campaign_success': False,
        'checks': len(checks), 'paid_wei': paid, 'actual_degraded_to_healthy_seconds': elapsed}, sort_keys=True))


if __name__ == '__main__':
    main()
