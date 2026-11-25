"""NEW read-only saved-vector reviewer for the separate c806 actual-Cast case.

DRAFT, not executed. Uses only the adjacent c804 verifier's pure readers/math/
comparison helpers; no keeper/project imports, subprocess, RPC, file writes,
repair, signing or old test bodies. Its sibling verifier must be retained/pinned.
The c804 body-watchdog conclusion is never imported as c806 evidence.
"""
from pathlib import Path
import argparse
import datetime
import importlib.util
import io
import json
import re
import sys
import tarfile

sys.dont_write_bytecode = True
COMPANION = Path(__file__).with_name('verify_saved_supervisor_c804.py')
spec = importlib.util.spec_from_file_location('saved_supervisor_readers', COMPANION)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
need, uint, q, address, hash32 = S.need, S.uint, S.q, S.address, S.hash32
sha, bounded, strict_json, journal, number = S.sha, S.bounded, S.strict_json, S.journal, S.number
LAB = '/opt/popl-ubuntu-supervisor-20261125-c806'
KEEPER = 'popl-ubuntu-supervisor-20261125-c806-keeper.service'
MODEL = 'popl-ubuntu-supervisor-20261125-c806-model.service'
RESOLVE = 'popl-ubuntu-supervisor-20261125-c806-resolve.service'
S.LAB, S.KEEPER, S.MODEL = LAB, KEEPER, MODEL
CONFIG = LAB + '/runtime/run-001/model/supervisor/actor/config.json'


def source_review(build):
    receipt_raw = bounded(build / 'BUILD_RECEIPT.json')
    receipt = strict_json(receipt_raw)
    need(receipt['lab'] == LAB and receipt['feature'] == 'signer' and
         receipt['current_production_members_byte_identical'] == 190 and
         receipt['production_sources_changed'] is False and
         receipt['manual_main_kill_not_watchdog'] is True, 'Unexpected signer source stage')
    raw = bounded(build / 'c806.inputs.tar.gz', 96 * 1024 * 1024)
    need({'bytes': len(raw), 'sha256': sha(raw)} == receipt['bundle'], 'Frozen c806 archive differs')
    members, total = {}, 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r|gz') as archive:
        for item in archive:
            path = S.PurePosixPath(item.name)
            need(len(members) < 2048 and item.isfile() and not path.is_absolute() and
                 '..' not in path.parts and str(path) == item.name and '\\' not in item.name and
                 item.name not in members and 0 <= item.size <= 32 * 1024 * 1024,
                 'Unsafe frozen c806 archive member')
            total += item.size
            need(total <= 256 * 1024 * 1024, 'Expanded c806 archive exceeds bound')
            value = archive.extractfile(item).read(item.size + 1)
            need(len(value) == item.size, 'c806 archive member length differs')
            members[item.name] = value
    manifest = strict_json(members['MANIFEST.json'])
    need({'bytes': len(members['MANIFEST.json']), 'sha256': sha(members['MANIFEST.json'])}
         == receipt['manifest'] and set(members) == set(manifest['members']) | {'MANIFEST.json'},
         'Frozen c806 manifest/inventory differs')
    for name, pin in manifest['members'].items():
        need({'bytes': len(members[name]), 'sha256': sha(members[name])} == pin,
             'Frozen c806 member pin differs')
    source_raw = members['inputs/SOURCE_MANIFEST.json']
    source = strict_json(source_raw)
    need(sha(source_raw) == receipt['source_manifest_sha256'] and
         source['source_head'] == S.HEAD and len(source['members']) == 190 and
         source['frozen_F6_Solidity_modified'] is False and
         source['unrelated_dirty_worktree_files_excluded'] is True,
         'Frozen c806 production identity differs')
    for name, pin in source['members'].items():
        value = members['source/contracts/' + name]
        need({'bytes': len(value), 'sha256': sha(value)} == pin, 'Frozen production member differs')
    for name, pin in receipt['helpers'].items():
        value = bounded(build / name)
        need({'bytes': len(value), 'sha256': sha(value)} == pin and
             members['source/helpers/' + name] == value, 'Frozen c806 helper differs')
    for name, key in (('remote_capsule.py', 'controller'), ('host_control.py', 'host_wrapper')):
        value = bounded(build / name)
        need({'bytes': len(value), 'sha256': sha(value)} == receipt[key], 'Frozen c806 controller differs')
    return {'source_head': S.HEAD, 'production_members': 190,
            'build_receipt_sha256': sha(receipt_raw), 'bundle_sha256': sha(raw),
            'companion_verifier_sha256': sha(bounded(COMPANION)),
            'helper_pins': receipt['helpers']}


def hashless_review(inputs):
    initial, _ = journal(inputs.get('case-INITIAL_JOURNAL.json'))
    held = inputs.get('case-CAST_REPLY_HELD.json')
    state, raw = journal(held, 'journal_raw_utf8', 'journal_sha256')
    baseline = inputs.get('native-BASELINE.json')
    baseline_state, baseline_raw = journal(baseline, 'journal_raw_utf8', 'journal_sha256')
    blocked = inputs.get('case-HASHLESS_RESTART_BLOCKED.json')
    blocked_state, blocked_raw = journal(blocked, 'raw_utf8', 'journal_sha256')
    middle = inputs.get('native-JOURNAL_DURING_RESTART.json')
    middle_state, middle_raw = journal(middle)
    need(raw == baseline_raw == blocked_raw == middle_raw and
         state == baseline_state == blocked_state == middle_state,
         'Original ambiguous hashless journal changed across cleanup/restart')
    p = state['pending']
    need(initial['pending'] is None and initial['next_nonce'] == 0 and initial['spent'] == {} and
         initial['receipt_anchor'] is None and p == held['intent'] and p.get('hash') is None and
         p['nonce'] == state['next_nonce'] == 0 and p['value'] == 0 and
         p['key'] == 'harvest:' + str(S.BUCKET) and
         address(p['to']) == address(state['contracts']['vault']) and
         state['sender'] == initial['sender'] and state['chain_id'] == initial['chain_id'] == 4663,
         'Fresh/hashless pending transaction identity differs')
    tx, h = held['transaction_without_signature'], hash32(held['accepted_hash'])
    need(hash32(tx['hash']) == h and address(tx['from']) == address(state['sender']) and
         address(tx['to']) == address(p['to']) and tx['input'].lower() == p['data'].lower() and
         q(tx['nonce']) == p['nonce'] == 0 and q(tx['value']) == p['value'] == 0 and
         q(tx['chainId']) == 4663 and held['maximum_hold_seconds'] == 75 and
         held['actual_node_accepted_before_withholding'] is True and
         held['no_raw_signature_or_request_params_retained'] is True,
         'Original accepted node hash/withheld reply projection differs')
    closed = inputs.get('case-CAST_CLIENT_CLOSED.json')
    need(hash32(closed['accepted_hash']) == h and closed['client_disconnected_before_reply'] is True and
         closed['reply_returned'] is False and 0 <= number(closed['elapsed_seconds']) < 75 and
         number(closed['monotonic']) > number(held['monotonic']),
         'Actual client did not disconnect before held reply returned')
    need(inputs.raw('case-HELD_REPLY_RETURNED.json', optional=True) is None,
         'Original Cast reply returned; do not claim interrupted reply')
    need(blocked['accepted_hash'] == held['accepted_hash'] and blocked['no_resend'] is True and
         blocked['explicit_stock_resolver_required'] is True and
         blocked['health']['status'] == 'recovery_required' and
         blocked['health']['pending'] is True and blocked['health']['pending_action'] == p['key'] and
         datetime.datetime.fromisoformat(blocked['health']['time']).timestamp() >= closed['utc'],
         'Fresh ordinary restart did not retain/block the same hashless intent')
    reviews = inputs.get('case-RAW_REVIEWS.json')
    need(len(reviews) == 1 and reviews[0]['intent'] == p and
         reviews[0]['raw_signature_retained'] is False, 'Original hashless fee review changed')
    return {'accepted_hash': h, 'hashless_journal_sha256': sha(raw),
            'four_raw_journal_snapshots_equal': True, 'stock_restart_blocked_new_signing': True,
            'reply_was_not_returned': True,
            'scope': 'accepted original transaction remains valid; no transactional cancellation'}


def native_review(inputs):
    kill = inputs.get('native-SIGNER_KILL.json')
    proof = inputs.get('native-NATIVE_RESTART_PROOF.json')
    need(kill['experiment'] == 'deliberate_SIGKILL_main_while_actual_Cast_reply_held' and
         kill['watchdog_experiment'] is False and proof['watchdog_experiment'] is False and
         proof['deliberate_main_kill_receipt'] == kill and proof['baseline'] == kill['before'],
         'This partition must remain an explicit manual-main-kill experiment')
    held_raw = inputs.raw('case-CAST_REPLY_HELD.json')
    held = strict_json(held_raw)
    need(kill['known_accepted_hash'] == held['accepted_hash'] and
         kill['held_record_sha256'] == sha(held_raw) and
         kill['hashless_journal_sha256'] == held['journal_sha256'] and
         0 <= number(kill['kill_request_monotonic']) - number(held['monotonic']) <= 30 and
         number(kill['kill_request_monotonic']) <= number(kill['kill_return_monotonic']),
         'Native main-kill identity/prompt hold margin differs')
    baseline = kill['before']
    need(inputs.get('native-BASELINE.json')['snapshot'] == baseline,
         'Root-owned signer baseline contradicts actual main-kill snapshot')
    unit = baseline['units'][KEEPER]
    S.policy(unit['properties'])
    main = int(unit['properties']['MainPID'])
    old = [row for row in unit['cgroup']['processes'] if row is not None]
    cast = kill['actual_cast_before_main_kill']
    need(main == kill['main_pid'] == proof['old_main_pid'] and main > 1 and
         kill['invocation_id'] == unit['properties']['InvocationID'] == proof['old_invocation_id'] and
         old == proof['old_processes'] and cast in old and cast['pid'] != main and
         cast['ppid'] == main and cast['session'] == cast['pgrp'] == cast['pid'] and
         cast['uid'] == 65534 and cast['state'] not in ('Z', 'X') and
         int(unit['properties']['WatchdogTimestampMonotonic']) > 0,
         'Actual separately sessioned live Cast child absent at main kill')
    samples, empty, new, previous = proof['samples'], [], [], -1
    need(2 <= len(samples) <= 1200, 'Bounded native signer restart samples missing')
    for snapshot in samples:
        end = number(snapshot['finished_monotonic'])
        need(snapshot['lab'] == LAB and number(snapshot['started_monotonic']) <= end and end >= previous,
             'Native signer sample identity/time differs')
        previous = end
        current = snapshot['units'][KEEPER]
        properties = current['properties']
        need(current['cgroup']['path'] == '/system.slice/' + KEEPER, 'Recursive signer cgroup differs')
        dead = S.old_dead(snapshot, old)
        if int(properties['MainPID']) == 0 and current['cgroup']['pids'] == [] and dead:
            empty.append(end)
        if int(properties['MainPID']) > 1 and properties.get('InvocationID') != proof['old_invocation_id']:
            need(dead, 'Old actual Cast/main generation overlaps replacement keeper')
            new.append((end, properties))
    need(empty and new and proof['observed_empty_monotonic'] == min(empty) < new[0][0] and
         min(empty) < int(new[0][1]['ExecMainStartTimestampMonotonic']) / 10**6 <= new[0][0],
         'Old main/Cast cgroup not empty before actual replacement main start')
    ni = proof['new_invocation']
    need(ni['invocation_id'] == new[0][1]['InvocationID'] and ni['pid'] == int(new[0][1]['MainPID']) and
         ni['observed_monotonic'] == new[0][0] and ni['all_old_generations_dead'] is True and
         ni['observed_empty_before_restart'] == min(empty), 'Signer new-invocation summary differs')
    final = proof['final']
    need(S.old_dead(final, old), 'Old actual Cast process generation still live')
    final_unit = final['units'][KEEPER]
    S.policy(final_unit['properties'])
    need(int(final_unit['properties']['NRestarts']) == int(unit['properties']['NRestarts']) + 1 and
         final_unit['properties']['InvocationID'] == ni['invocation_id'],
         'Expected one automatic restart after deliberate main kill')
    events = final_unit['manager_journal']
    for event in events:
        need(str(event['_PID']) == '1' and event['UNIT'] == KEEPER,
             'Signer native manager attribution differs')
    need(any(event.get('UNIT_RESULT') == 'signal' or
             re.search(r"failed with result ['\"]signal['\"]", event.get('MESSAGE', '').lower())
             for event in events), 'Actual native signal-failure outcome absent')
    before, after = proof['lock_before'], proof['lock_after']
    middle = inputs.get('native-JOURNAL_DURING_RESTART.json')['lock']
    need((before['dev'], before['ino'], before['uid']) ==
         (after['dev'], after['ino'], after['uid']) ==
         (middle['dev'], middle['ino'], middle['uid']) and before['uid'] == 65534 and
         middle['exclusive_probe_when_empty'] is True, 'Hashless signer lock release/inode differs')
    main_now = next(row for row in final_unit['cgroup']['processes'] if row and row['pid'] == ni['pid'])
    model = final['units'][MODEL]
    model_now = next(row for row in model['cgroup']['processes'] if row and
                     row['pid'] == int(model['properties']['MainPID']))
    need(main_now['uid'] == model_now['uid'] == 65534 and
         main_now['network_namespace'] == model_now['network_namespace'] != final['host_network_namespace'],
         'Restarted signer native namespace/uid differs')
    return {'manual_main_SIGKILL': True, 'watchdog_experiment': False,
            'actual_Cast_generation_captured_alive': True, 'observed_old_processes': len(old),
            'separately_sessioned_Cast_dead_before_new_main': True,
            'same_lock_inode_and_exclusive_empty_probe': True, 'automatic_restarts': 1,
            'universal_fencing_or_transaction_cancellation': False,
            'manager_warning_messages': [event.get('MESSAGE', '') for event in events if
                re.search(r'failed to kill|invalid argument|warning', event.get('MESSAGE', ''), re.I)]}


def transaction_review(inputs):
    held = inputs.get('case-CAST_REPLY_HELD.json')
    original, p, h = held['state'], held['intent'], hash32(held['accepted_hash'])
    row = inputs.get('case-RECOVERED_JOURNAL.json')
    state, tx, receipt, block, head = (row[key] for key in
        ('state', 'transaction_without_signature', 'receipt', 'receipt_block', 'head'))
    need(hash32(row['accepted_hash']) == hash32(tx['hash']) == hash32(receipt['transactionHash']) == h and
         hash32(tx['blockHash']) == hash32(receipt['blockHash']) == hash32(block['hash']) and
         q(tx['blockNumber']) == q(receipt['blockNumber']) == q(block['number']),
         'Original accepted hash canonical inclusion differs')
    index = q(receipt['transactionIndex'])
    need(q(tx['transactionIndex']) == index and index < len(block['transactions']) and
         hash32(block['transactions'][index]) == h and
         address(tx['from']) == address(receipt['from']) == address(original['sender']) ==
         address(state['sender']) and address(tx['to']) == address(receipt['to']) == address(p['to']) and
         tx['input'].lower() == p['data'].lower() and q(tx['nonce']) == uint(p['nonce']) == 0 and
         q(tx['value']) == uint(p['value']) == 0 and q(tx['chainId']) == 4663 and
         q(receipt['status']) == 1, 'Original accepted transaction identity/index/status differs')
    need(q(head['number']) - q(block['number']) + 1 >= 12 and
         q(head['timestamp']) >= q(block['timestamp']), 'Twelve actual confirmations absent')
    f, gas, used, kind = p['fee_review'], q(tx['gas']), q(receipt['gasUsed']), q(tx.get('type', '0x0'))
    need(type(f.get('schema')) is int and f['schema'] == 1 and
         0 < used <= gas == uint(f['gas_limit']) <= 24000000 and
         f['receipt_fee_policy'] == 'included' and uint(f['l1_fee_allowance_wei']) == 0 and
         q(receipt.get('l1Fee', '0x0')) == 0, 'Original gas/profile/fee semantics differ')
    if kind == 2:
        cap, tip, base = q(tx['maxFeePerGas']), q(tx['maxPriorityFeePerGas']), q(block['baseFeePerGas'])
        need(tip <= cap and base <= cap, 'Invalid canonical EIP1559 envelope')
        price = min(cap, base + tip)
    elif kind in (0, 1):
        cap = price = q(tx['gasPrice'])
        need(price == q(receipt['effectiveGasPrice']), 'Legacy fee price differs')
    else:
        raise S.Refused('Unsupported original transaction fee type')
    paid = used * price
    need(0 < cap == uint(f['max_fee_per_gas']) <= 5000000000 and
         0 < paid <= gas * cap == uint(f['maximum_cost_wei']) <= 10**16 and
         uint(row['paid_wei']) == paid and uint(row['canonical_execution_price_wei']) == price and
         uint(row['reported_effective_gas_price_wei']) == q(receipt['effectiveGasPrice']),
         'Canonical accepted transaction cost differs from retained original fee review')
    day = datetime.datetime.fromtimestamp(q(block['timestamp']), datetime.timezone.utc).date().isoformat()
    spent = {key: uint(value) for key, value in original['spent'].items()}
    spent[day] = spent.get(day, 0) + paid
    need(state['pending'] is None and state['next_nonce'] == p['nonce'] + 1 == 1 and
         {key: uint(value) for key, value in state['spent'].items()} == spent and
         sum(spent.values()) <= 5 * 10**16 and state['receipt_anchor'] == {
             'number': q(block['number']), 'hash': block['hash'],
             'timestamp': q(block['timestamp']), 'nonce': 0} and
         state['last'][p['key']] == q(block['timestamp']) and state['last_fee_observation'] == {
             'transaction': held['accepted_hash'], 'reported_price_wei': q(receipt['effectiveGasPrice']),
             'execution_price_wei': price, 'gas_used': used, 'l1_fee_wei': 0,
             'receipt_fee_policy': 'included', 'cost_wei': paid}, 'Nonce/receipt/day cost not settled once')
    records = inputs.get('case-RECEIPTS.json')
    need(len(records) == 1 and hash32(records[0]['hash']) == h and records[0]['intent'] == p and
         records[0]['receipt'] == receipt and records[0]['explicit_hash_resolution'] is True,
         'Exactly one original explicitly resolved receipt is required')
    complete, result, case = (inputs.get(name) for name in
        ('model-COMPLETE.json', 'model-RESULT.json', 'case-RESULT.json'))
    for value in (complete, result):
        need(value['success'] is True and hash32(value['accepted_hash']) == h and
             value['hashless_restart_blocked'] is True and value['explicit_resolution_recovered'] is True and
             value['fresh_native_healthy_cycle'] is True and
             value['manual_SIGKILL_main_case_not_watchdog_case'] is True and
             value['public_transactions'] == 0 and value['new_seals'] == 0 and
             value['old_feature_journeys_or_tests_run'] == 0, 'Incomplete signer campaign outcome')
    need(result['raw_attempts'] == result['raw_forwarded'] == case['raw_attempts'] ==
         case['raw_forwarded'] == case['stock_transactions'] == 1 and
         0 < result['shared_RPC_requests'] <= 6000 and case['gateway_refusals'] == [] and
         case['status'] == 'passed', 'Another signer submission/refusal or incomplete result exists')
    health = inputs.get('case-HEALTHY_NORMAL_CYCLE.json')
    need(health['status'] == 'healthy_v2', 'Fresh normal post-resolution healthy cycle absent')
    return {'accepted_hash': h, 'gas_used': used, 'canonical_price_wei': price,
            'reported_price_wei': q(receipt['effectiveGasPrice']), 'paid_wei': paid,
            'original_maximum_cost_wei': gas * cap, 'nonce_before': 0, 'nonce_after': 1,
            'one_original_source_bound_raw_send_only': True,
            'recovered_digest': 'reported journal_sha256 only until final raw journal supplied'}


def resolver_review(inputs):
    request_raw = inputs.raw('native-RESOLUTION_REQUEST.json')
    completion_raw = inputs.raw('native-RESOLUTION_COMPLETE.json')
    completion = strict_json(completion_raw)
    need(request_raw == completion_raw,
         'Root resolver request/completion projections differ; manager-wait result must be identical')
    held_raw = inputs.raw('case-CAST_REPLY_HELD.json')
    held = strict_json(held_raw)
    h = hash32(held['accepted_hash'])
    ready = inputs.get('model-READY.json')
    stop = inputs.get('native-STOP_KEEPER.json')
    need(stop['unit'] == KEEPER and stop['stop_requested'] is True and
         stop['stopped_is_not_inferred_from_request'] is True,
         'Intentional keeper-stop ordering record absent')
    argv = ['/usr/bin/python3', '-m', 'keeper.monitor', '--config', CONFIG,
            '--resolve-pending', h]
    need(completion['unit'] == RESOLVE and completion['direct_exec_argv'] == argv and
         '--live' not in completion['direct_exec_argv'] and
         completion['manager_wait_completion'] is True and
         type(completion['manager_wait_returncode']) is int and
         completion['manager_wait_returncode'] == 0 and
         completion['signing_enabled'] is False and completion['explicit_stock_hash_resolution'] is True and
         hash32(completion['known_accepted_hash']) == h and
         completion['original_hashless_journal_sha256'] == held['journal_sha256'] and
         completion['held_record_sha256'] == sha(held_raw) and
         completion['configuration_sha256'] == ready['configuration_sha256'],
         'Root-owned exact stock resolver manager-wait completion is missing/inconsistent')
    resolved_at = number(completion['manager_wait_completed_monotonic'])
    closed = inputs.get('case-CAST_CLIENT_CLOSED.json')
    proof = inputs.get('native-NATIVE_RESTART_PROOF.json')
    need(resolved_at > number(closed['monotonic']) and
         resolved_at > number(proof['new_invocation']['observed_monotonic']),
         'Explicit resolver completion predates client close/ordinary hashless restart')
    policy = completion['requested_policy']
    expected = {'Restart': 'no', 'TimeoutStopSec': '120s', 'User': 'nobody',
                'Group': 'nogroup', 'PrivateNetwork': 'yes', 'NotifyAccess': None,
                'KillMode': 'control-group', 'SendSIGKILL': 'yes', 'FinalKillSignal': 'SIGKILL',
                'JoinsNamespaceOf': MODEL, 'Requires': MODEL, 'After': MODEL,
                'WorkingDirectory': LAB + '/source/contracts'}
    need(all(policy.get(key) == value for key, value in expected.items()),
         'Exact nonsigning resolver service policy differs')
    resume = inputs.get('native-NORMAL_RESUME.json')
    recovered = inputs.get('case-RECOVERED_JOURNAL.json')
    need(resume['phase'] == 'normal_resume_requested' and resume['unit'] == KEEPER and
         resume['recorded_resolver_completion'] == completion and
         resume['same_configuration_sha256'] == completion['configuration_sha256'] and
         resume['same_original_journal_preserved'] is True and
         resume['journal_before_resume_sha256'] == completion['resolved_journal_sha256'] ==
         recovered['journal_sha256'] and resume['same_existing_logs_appended'] is True,
         'Normal resume changed the completed original journal/configuration or completion identity')
    before = resume['before']
    need(before.get('ActiveState') in ('inactive', 'failed', None) and
         int(before.get('MainPID', '0')) == 0,
         'Normal keeper resumed while previous native keeper was active')
    collected = before.get('LoadState') == 'not-found'
    need(type(resume['unit_recreated_after_gc']) is bool and
         resume['unit_recreated_after_gc'] == collected,
         'Collected transient-unit recreation flag contradicts loaded state')
    launched = resume['launch']
    S.policy(launched['properties'])
    need(int(launched['properties']['ExecMainStartTimestampMonotonic']) / 10**6 > resolved_at,
         'Normal keeper start predates successful nonsigning resolver completion')
    if collected:
        need(launched['unit'] == KEEPER and launched['direct_exec_argv'] ==
             ['/usr/bin/python3', '-m', 'keeper.monitor', '--config', CONFIG, '--live'],
             'Collected keeper was not recreated with the exact original stock main')
        policy = launched['requested_policy']
        need(policy['StandardOutput'] == 'append:' + LAB + '/runtime/run-001/native-keeper.stdout.log' and
             policy['StandardError'] == 'append:' + LAB + '/runtime/run-001/native-keeper.stderr.log' and
             policy['WatchdogSec'] == policy['TimeoutStopSec'] == '120s' and
             policy['RestartSec'] == '30s' and policy['NotifyAccess'] == 'main' and
             policy['KillMode'] == 'control-group',
             'Recreated keeper did not request the same existing append log paths/supervisor policy')
    else:
        S.policy(before)
    return {'stock_resolver_exact_accepted_hash': h, 'nonsigning_argv_verified': True,
            'root_owned_manager_wait_completed_returncode': 0,
            'resolver_property_load_state_after_completion': completion['properties'].get('LoadState'),
            'resolved_journal_sha256': completion['resolved_journal_sha256'],
            'normal_keeper_recreated_after_transient_GC': collected,
            'same_existing_append_log_paths_source_and_policy_bound': True,
            'independent_log_prefix_bytes_unchanged': 'not supplied; append policy is not a byte-prefix comparison',
            'restart_count_scope': 'one automatic signal restart before intentional stop; recreated unit may reset NRestarts',
            'request_is_completion': 'systemd-run --wait returned success; not merely an asynchronous start request'}


def final_journal_review(inputs):
    raw = inputs.raw('FINAL_JOURNAL.raw', optional=True)
    if raw is None:
        raise S.Missing('Optional stopped final raw journal not supplied')
    state = strict_json(raw)
    sidecar = inputs.raw('FINAL_JOURNAL.sha256', optional=True, maximum=256)
    if sidecar is not None:
        expected = sidecar.decode('ascii', 'strict').strip()
        need(re.fullmatch('[0-9a-f]{64}', expected) is not None and expected == sha(raw),
             'Stopped final raw journal SHA sidecar differs')
    recovered = inputs.get('case-RECOVERED_JOURNAL.json')
    need(S.critical(state) == S.critical(recovered['state']), 'Stopped final settled critical fields changed')
    return {'final_sha256': sha(raw), 'sidecar_supplied': sidecar is not None,
            'equals_reported_recovered_digest': sha(raw) == recovered['journal_sha256'],
            'all_settled_critical_fields_equal': True,
            'other_top_level_fields_changed_after_normal_cycle': sorted(key for key in
                set(state) | set(recovered['state']) if state.get(key) != recovered['state'].get(key)),
            'capture_after_stop': 'requires separate final native-stop vector'}


def cleanup_review(path):
    if path is None:
        raise S.Missing('Final signer native-stop vector not supplied')
    value = strict_json(bounded(path))
    need(value.get('phase') == 'stopped' and value.get('all_owned_units_stopped') is True,
         'Stop request alone is not final signer cleanup')
    for name in (KEEPER, RESOLVE, MODEL):
        unit = value['native_status']['units'][name]
        need(unit['properties'].get('ActiveState') in ('inactive', 'failed', None) and
             int(unit['properties'].get('MainPID', '0')) == 0 and unit['cgroup']['pids'] == [] and
             unit['cgroup']['processes'] == [], 'Final signer native unit still has processes')
    return {'all_three_fixed_native_cgroups_finally_empty': True,
            'collected_unit_not_found': 'acceptable only with empty fixed recursive cgroup census'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--native-stop', type=Path)
    args = parser.parse_args()
    inputs, checks = S.Inputs(args.evidence), {}
    tasks = [('frozen_sources', lambda: source_review(args.build_dir)),
             ('accepted_hashless_restart_block', lambda: hashless_review(inputs)),
             ('actual_Cast_manual_main_kill_cleanup', lambda: native_review(inputs)),
             ('explicit_stock_resolver_and_normal_resume', lambda: resolver_review(inputs)),
             ('canonical_paid_recovery_once', lambda: transaction_review(inputs)),
             ('NFT_LP_rights', lambda: S.financial_review(inputs)),
             ('authority_projection_only', lambda: S.authority_review(inputs)),
             ('optional_final_raw_journal', lambda: final_journal_review(inputs)),
             ('final_native_cleanup', lambda: cleanup_review(args.native_stop))]
    for name, run in tasks:
        try:
            checks[name] = {'status': 'passed', 'proof': run()}
        except S.Missing as exc:
            checks[name] = {'status': 'missing', 'reason': str(exc)}
        except (S.Refused, KeyError, IndexError, StopIteration, TypeError, ValueError, OSError,
                tarfile.TarError) as exc:
            checks[name] = {'status': 'failed', 'reason': str(exc), 'error_class': type(exc).__name__}
    required = [value['status'] for name, value in checks.items() if name != 'optional_final_raw_journal']
    status = 'failed' if 'failed' in required else 'incomplete' if 'missing' in required else 'passed'
    print(json.dumps({'schema': 1, 'stage': 'c806_saved_vectors_independent_review', 'status': status,
        'checks': checks, 'input_files': inputs.used, 'runtime_actions': 0, 'network_calls': 0,
        'old_test_bodies_run': 0, 'production_approved': False,
        'limits': [
            'Manual main SIGKILL while actual Cast awaits its withheld accepted reply; not a watchdog/90s Cast-timeout experiment.',
            'Original accepted transaction remains valid; a disconnected signer does not cancel EVM work.',
            'Hashless intent blocks ordinary restart until explicit stock resolution of that exact independently captured hash.',
            'Collected transient-unit recreation requires its own root-owned completion and append-only log evidence.',
            'Saved role grant is a projection; no absent role-getter equality or authorization is inferred from permissionless harvest.',
            'Source-bound counters establish one finite send; no global mempool/provider/host guarantee is claimed.',
            'Off-host fencing, storage faults, restart storms, alerts, soak, provider fees and release approval remain open.',
            'Existing-service/heartbeat preservation requires a separate host before/after comparison.']},
        sort_keys=True, indent=2, allow_nan=False))
    return 1 if status == 'failed' else 2 if status == 'incomplete' else 0


if __name__ == '__main__':
    raise SystemExit(main())
