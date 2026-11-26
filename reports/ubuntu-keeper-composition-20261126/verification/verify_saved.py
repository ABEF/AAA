"""Independent report-only c822 reconciliation; no application imports or RPC.

Run only after the complete fixed evidence set and final host comparison exist.
This checks saved raw bytes and integer accounting. It does not execute tests,
restart processes, query a chain, attest loaded code, or approve production.
"""
from pathlib import Path
import argparse
import ast
import base64
import datetime as dt
import hashlib
import io
import json
import math
import re
import stat
import tarfile
import zlib


HEAD = '7436933c153246f57eaa01cf42c5f3ec90363dad'
CONTROLLER = '69b3cee016793ab0cf18c6e1c2f40e41bf4bf8220053a079a52bd10209788a3f'
BUNDLE = '7d1aa75502b81eb67eb23c073d366395a0715edb3398198754511108c4d108a5'
MANIFEST = '4f318d8f2d8d94ac629e9e1771872536f1a2400ea244b86c4912fcb770aeadd0'
MODEL = 'c829059ff6ec73c13037b82995e267397ab59073de5fc48eaf8a9f436e9e82e5'
PREFIX = 'popl-keeper-composition-20261126-c822'
EMPTY = hashlib.sha256(b'').hexdigest()
FEES_TOPIC = '0xa54e6c2fc0861aa9c991b26891d71059d517983b9e84b91020f42609c452eb9d'
MAX_WIRE = 65536
MAX_ARTIFACT = 32768
MAX_PACKED = 262144
BOOKED = ('pending', 'next_nonce', 'spent', 'receipt_anchor', 'last_fee_observation', 'last')
ARTIFACTS = ('RESULT.json', 'FINAL.json', 'PROGRESS.json', 'SIDECAR_RESULT.json',
    'WORKER_LOGS.json', 'MANAGER_TRACE.json', 'NATIVE_PROPERTIES.json',
    'READY.json', 'PENDING.json', 'INCLUDED.json', 'SETTLED.json', 'HEALTHY.json',
    'COMPLETE.json', 'MODEL_RESULT.json', 'MODEL_STOP.json', 'MODEL_EVIDENCE.json',
    'RACE_READY.json', 'RACE_RESULT.json', 'HOLD_READY.json', 'HOLD_RESULT.json')
STAGES = ('current_copied_state_and_normal_daemon',
    'actual_timer_contention_and_same_pending_history',
    'ordinary_pending_recovery_and_required_fresh_observations', 'fenced_final_physical_capture')
RAW_NAMES = ('INITIAL_JOURNAL.json', 'PENDING_JOURNAL.json', 'SETTLED_JOURNAL.json',
    'HEALTHY_JOURNAL.json', 'FINAL_JOURNAL.json', 'FINANCIAL_INITIAL.json',
    'FINANCIAL_INCLUDED.json', 'FINANCIAL_FINAL.json', 'CANONICAL_FINAL.json')
TX_FIELDS = ('hash', 'from', 'to', 'input', 'nonce', 'value', 'gas', 'gasPrice',
    'type', 'chainId', 'maxFeePerGas', 'maxPriorityFeePerGas', 'blockHash',
    'blockNumber', 'transactionIndex')
INPUT_PINS = {}


def need(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def uint(value):
    need(type(value) is int and 0 <= value < 1 << 256, 'unsigned_integer')
    return value


def quantity(value):
    need(type(value) is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', value),
        'rpc_quantity')
    return int(value, 16)


def number(value):
    need(type(value) in (int, float) and math.isfinite(value), 'finite_clock')
    return value


def address(value):
    need(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{40}', value), 'address')
    return value.lower()


def hash32(value, prefix=True):
    need(type(value) is str and re.fullmatch(('0x' if prefix else '') + '[0-9a-fA-F]{64}', value),
        'hash32')
    return value.lower()


def enc(value, newline=False):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) +
        ('\n' if newline else '')).encode('utf8')


def pairs(rows):
    value = {}
    for key, item in rows:
        need(key not in value, 'duplicate_json_key')
        value[key] = item
    return value


def finite(text):
    value = float(text)
    need(math.isfinite(value), 'nonfinite_json')
    return value


def obj(raw):
    return json.loads(raw.decode('utf8', 'strict'), object_pairs_hook=pairs,
        parse_float=finite, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('json_constant')))


def read(path, limit, label):
    item = path.lstat()
    need(stat.S_ISREG(item.st_mode) and item.st_nlink == 1 and item.st_size <= limit,
        'saved_file_kind_or_size')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) == item.st_size and len(raw) <= limit, 'saved_file_size_changed')
    INPUT_PINS[label] = {'bytes': len(raw), 'sha256': sha(raw)}
    return raw


def json_file(path, limit, label):
    return obj(read(path, limit, label))


def packed(value):
    need(set(value) == {'decoded_bytes', 'decoded_sha256', 'gzip_base64'}, 'packed_shape')
    size = uint(value['decoded_bytes'])
    need(size <= MAX_PACKED and type(value['gzip_base64']) is str and
        len(value['gzip_base64']) <= MAX_WIRE, 'packed_bound')
    compressed = base64.b64decode(value['gzip_base64'], validate=True)
    need(len(compressed) <= MAX_WIRE, 'compressed_bound')
    decoder = zlib.decompressobj(31)
    raw = decoder.decompress(compressed, MAX_PACKED + 1)
    need(len(raw) == size and len(raw) <= MAX_PACKED and decoder.eof and
        not decoder.unused_data and not decoder.unconsumed_tail and
        sha(raw) == hash32(value['decoded_sha256'], False), 'packed_integrity')
    return raw


def fetch(evidence, name):
    # Immutable early captures remain their original evidence. Only progress is
    # mutable, so explicitly select its final fetch rather than an early view.
    candidates = ([path / name for path in evidence.glob('fetch-*') if (path / name).is_file()]
        if name == 'PROGRESS.json' else list(evidence.rglob(name)))
    need(len(candidates) == 1, 'one_explicit_complete_fetch_per_artifact')
    path = candidates[0]
    directory = path.parent
    raw = read(path, MAX_ARTIFACT, 'evidence/' + str(path.relative_to(evidence)).replace('\\', '/'))
    receipt = json_file(directory / 'EXECUTION.json', MAX_WIRE,
        'evidence/' + directory.name + '/EXECUTION.json')
    need(receipt['action'] == 'fetch' and receipt['exit_code'] == 0 and
        receipt['capture_reason'] is None and receipt['capture_errors'] == [] and
        receipt['controller_sha256'] == CONTROLLER and receipt['combined_output_limit'] == MAX_WIRE and
        receipt['stderr_bytes'] == 0 and receipt['stderr.raw_sha256'] == EMPTY and
        receipt['host_wrapper_signer_files_accessed'] is False and
        receipt['production_signer_material_read_or_exported'] is False and
        receipt['fresh_disposable_lab_signer_used'] is True and receipt['only_fixed_c822_units'] is True,
        'fetch_receipt')
    wire = (json.dumps({'phase': 'saved_artifact', 'name': name, 'bytes': len(raw),
        'sha256': sha(raw), 'base64': base64.b64encode(raw).decode('ascii')},
        sort_keys=True) + '\n').encode()
    need(len(wire) == receipt['stdout_bytes'] and len(wire) <= MAX_WIRE and
        sha(wire) == receipt['stdout.raw_sha256'], 'exact_fetch_wire_pin')
    return obj(raw)


def preparation(folder):
    manifest_raw = read(folder / 'SOURCE_MANIFEST.json', MAX_WIRE, 'preparation/SOURCE_MANIFEST.json')
    need(sha(manifest_raw) == MANIFEST, 'frozen_manifest')
    manifest = obj(manifest_raw)
    build = json_file(folder / 'BUILD_RECEIPT.json', MAX_WIRE, 'preparation/BUILD_RECEIPT.json')
    need(manifest['source_head'] == build['source_head'] == HEAD and
        len(manifest['source_files']) == build['source_members'] == 36 and
        build['archive_members'] == 45 and not manifest['source_overrides'] and
        not build['production_source_overrides'] and build['tests_run'] == 0,
        'preparation_scope')
    controller_raw = read(folder / 'remote_capsule.py', MAX_WIRE, 'preparation/remote_capsule.py')
    need(sha(controller_raw) == CONTROLLER == build['controller']['sha256'], 'controller_pin')
    source_raw = read(folder / 'PRODUCTION_SOURCE_MANIFEST.json', MAX_WIRE,
        'preparation/PRODUCTION_SOURCE_MANIFEST.json')
    source = obj(source_raw)
    need(source['members'] == manifest['source_files'] and source['source_head'] == HEAD and
        sha(source_raw) == manifest['production_source_manifest_sha256'] and
        'indexer/event_schema.json' in source['members'] and
        len(manifest['dynamic_source_groups']['scheduling19']) == 19 and
        len(manifest['dynamic_source_groups']['health13']) == 13,
        'current_source_manifest')
    for group in manifest['dynamic_source_groups'].values():
        need(set(group) <= set(source['members']), 'declared_source_closure')
    expected = {name: pin['sha256'] for name, pin in manifest['members'].items()}
    expected['SOURCE_MANIFEST.json'] = MANIFEST
    # Only literal data declarations are inspected. Nothing in the capsule runs.
    syntax = ast.parse(controller_raw)
    constants = {target.id: node.value for node in syntax.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)}
    need(ast.literal_eval(constants['BUNDLE_SHA']) == BUNDLE and
        ast.literal_eval(constants['SOURCE_MANIFEST_SHA']) == MANIFEST,
        'embedded_packet_pins')
    embedded = ast.literal_eval(constants['EXPECTED'])
    need(len(embedded) == 45 and set(embedded) == set(expected) and
        all(pin['sha256'] == expected[name] for name, pin in embedded.items()), 'embedded_member_pins')
    for name, row in ast.literal_eval(constants['COPIED_INPUTS']).items():
        expected['inputs/' + name] = row[1]
    for name, pin in ast.literal_eval(constants['TOOLS']).items():
        expected['tools/' + name] = pin
    need(len(expected) == 51 and sha(read(folder / 'model_service.py', MAX_WIRE,
        'preparation/model_service.py')) == MODEL == build['model']['sha256'], 'full_source51_and_model')
    # A publication may omit the binary archive; its exact member/production
    # identities remain bound by the executed capsule and final source maps.
    packet_path = folder / 'c822.inputs.tar.gz'
    archive_checked = False
    if packet_path.exists():
        raw = read(packet_path, 2 * 1024 * 1024, 'preparation/c822.inputs.tar.gz')
        need(sha(raw) == BUNDLE == build['bundle']['sha256'], 'archive_pin')
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as packet:
            rows = packet.getmembers()
            need(len(rows) == len({row.name for row in rows}) == 45, 'archive_count')
            for row in rows:
                need(row.isfile() and row.uid == row.gid == 0 and row.mode == 0o444 and
                    row.name in embedded and row.size <= 1024 * 1024, 'archive_metadata')
                data = packet.extractfile(row).read()
                need(embedded[row.name] == {'bytes': len(data), 'sha256': sha(data)}, 'archive_member')
        archive_checked = True
    return manifest, source, expected, archive_checked


def raw_vectors(envelope, source):
    value = obj(packed(envelope))
    need(value['schema'] == 1 and value['kind'] == 'popl-isolated-keeper-composition-evidence' and
        value['unsigned'] is True and value['readiness_approved'] is False and
        value['source_head'] == HEAD and value['source_pins'] == source['members'] and
        value['raw_configuration_included'] is value['signer_material_included'] is
        value['raw_signed_envelope_included'] is False and set(value['files']) == set(RAW_NAMES),
        'model_export_scope')
    raw, parsed = {}, {}
    for name, row in value['files'].items():
        need(set(row) == {'bytes', 'sha256', 'raw_base64'} and uint(row['bytes']) <= MAX_PACKED and
            type(row['raw_base64']) is str and len(row['raw_base64']) <= MAX_PACKED, 'raw_vector_descriptor')
        data = base64.b64decode(row['raw_base64'], validate=True)
        need(len(data) == row['bytes'] and sha(data) == hash32(row['sha256'], False), 'raw_vector_integrity')
        raw[name], parsed[name] = data, obj(data)
    need(sum(map(len, raw.values())) <= MAX_PACKED, 'raw_vector_aggregate')
    return value, raw, parsed


def fee_and_booking(values, raw, vectors):
    initial, pending, settled, healthy, final = (vectors[name] for name in RAW_NAMES[:5])
    intent = pending['pending']
    need(initial['pending'] is None and initial['next_nonce'] == 0 and initial['spent'] == {} and
        type(intent) is dict and intent['nonce'] == pending['next_nonce'] == 0 and
        pending['sender'] == initial['sender'] and hash32(intent['hash']) ==
        values['PENDING.json']['accepted_hash'], 'initial_and_pending')
    identity = ('chain_id', 'sender', 'contracts', 'accounting_model', 'accounting_version',
        'fee_intake_version', 'execution_price_version')
    need(initial['chain_id'] == 4663 and initial['accounting_model'] == 'shared-pools-v2' and
        initial['accounting_version'] == 7 and initial['fee_intake_version'] ==
        initial['execution_price_version'] == 1 and all(all(state[key] == initial[key] for key in identity)
        for state in (pending, settled, healthy, final)), 'exact_journal_identity')
    proof = vectors['CANONICAL_FINAL.json']
    tx, receipt, block, head = (proof[key] for key in
        ('transaction_without_signature', 'receipt', 'receipt_block', 'head'))
    need(set(tx) == set(TX_FIELDS), 'signature_free_tx_whitelist')
    transaction_hash = hash32(intent['hash'])
    need(hash32(tx['hash']) == hash32(receipt['transactionHash']) ==
        hash32(proof['accepted_hash']) == transaction_hash and quantity(receipt['status']) == 1 and
        address(tx['from']) == address(receipt['from']) == address(initial['sender']) and
        address(tx['to']) == address(receipt['to']) == address(intent['to']) ==
        address(initial['contracts']['vault']) and quantity(tx['nonce']) == intent['nonce'] == 0 and
        quantity(tx['value']) == intent['value'] == 0 and quantity(tx['chainId']) == 4663 and
        tx['input'] == intent['data'], 'exact_canonical_transaction')
    block_number, stamp = quantity(receipt['blockNumber']), quantity(block['timestamp'])
    need(hash32(block['hash']) == hash32(receipt['blockHash']) == hash32(tx['blockHash']) and
        quantity(block['number']) == quantity(tx['blockNumber']) == block_number and
        quantity(tx['transactionIndex']) == quantity(receipt['transactionIndex']) and
        quantity(head['number']) - block_number + 1 == proof['confirmations'] >= 12,
        'canonical_inclusion_and_depth')
    raw_data = intent['data']
    need(type(raw_data) is str and re.fullmatch(r'0x[0-9a-f]{136}', raw_data) and
        intent['key'] == 'harvest:' + str(int(raw_data[10:74], 16)) and
        stamp <= int(raw_data[-64:], 16), 'harvest_calldata_and_deadline')
    bucket = int(raw_data[10:74], 16)
    budget = intent['fee_review']
    gas_limit, fee_cap = uint(budget['gas_limit']), uint(budget['max_fee_per_gas'])
    need(budget['schema'] == 1 and budget['receipt_fee_policy'] == 'included' and
        budget['l1_fee_allowance_wei'] == 0 and 0 < gas_limit <= 24000000 and
        0 < fee_cap <= 5000000000 and quantity(tx['gas']) == gas_limit and
        budget['maximum_cost_wei'] == gas_limit * fee_cap <= 10**16, 'unchanged_fee_bounds')
    tx_type = quantity(tx['type'])
    if tx_type == 2:
        # Independent canonical EIP-1559 arithmetic; no project fee helpers.
        maximum = quantity(tx['maxFeePerGas'])
        priority = quantity(tx['maxPriorityFeePerGas'])
        base = quantity(block['baseFeePerGas'])
        need(0 <= priority <= maximum and maximum == fee_cap and maximum >= base, 'type2_fee_parameters')
        effective = min(maximum, base + priority)
    else:
        need(tx_type in (0, 1), 'unsupported_transaction_type')
        effective = quantity(tx['gasPrice'])
        need(effective == fee_cap, 'legacy_fee_cap')
    gas_used = quantity(receipt['gasUsed'])
    paid = gas_used * effective
    need(0 < gas_used <= gas_limit and quantity(receipt['effectiveGasPrice']) == effective and
        proof['execution_price_wei'] == effective and proof['paid_wei'] == paid and
        paid <= budget['maximum_cost_wei'], 'independent_actual_fee')
    day = dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date().isoformat()
    expected_last = {**initial['last'], intent['key']: stamp}
    for state in (settled, healthy, final):
        need(state['pending'] is None and state['next_nonce'] == 1 and state['spent'] == {day: paid} and
            state['last'] == expected_last and state['receipt_anchor'] == {'number': block_number,
            'hash': block['hash'], 'timestamp': stamp, 'nonce': 0}, 'once_only_receipt_booking')
        fee = state['last_fee_observation']
        need(fee['transaction'] == transaction_hash and fee['execution_price_wei'] == effective and
            fee['gas_used'] == gas_used and fee['l1_fee_wei'] == 0 and fee['receipt_fee_policy'] == 'included'
            and fee['cost_wei'] == paid, 'once_only_complete_fee_observation')
    need(all(all(state[key] == settled[key] for key in BOOKED) for state in (healthy, final)),
        'unchanged_booked_fields_across_later_wake')
    harvests = [row for row in receipt['logs'] if address(row['address']) == address(intent['to']) and
        row['topics'][:1] == [FEES_TOPIC]]
    need(len(harvests) == 1, 'one_actual_bucket_harvest_event')
    event = harvests[0]
    need(event['topics'] == [FEES_TOPIC, '0x' + format(bucket, '064x')] and
        re.fullmatch(r'0x[0-9a-fA-F]{128}', event['data']) and event.get('removed', False) is False and
        event['transactionHash'] == transaction_hash and event['blockHash'] == block['hash'] and
        quantity(event['blockNumber']) == block_number and
        quantity(event['transactionIndex']) == quantity(receipt['transactionIndex']), 'actual_harvest_inclusion')
    for artifact, journal in (('PENDING.json', 'PENDING_JOURNAL.json'),
            ('SETTLED.json', 'SETTLED_JOURNAL.json'), ('HEALTHY.json', 'HEALTHY_JOURNAL.json')):
        need(values[artifact]['journal_sha256'] == sha(raw[journal]) and
            values[artifact]['accepted_hash'] == transaction_hash, 'phase_raw_journal_binding')
    return {'hash': transaction_hash, 'type': tx_type, 'gas_used': gas_used,
        'gas_limit': gas_limit, 'effective_gas_price_wei': effective, 'paid_wei': paid,
        'UTC_fee_day': day, 'bucket': str(bucket), 'confirmations_final': proof['confirmations'],
        'harvest_amount0': int(event['data'][2:66], 16), 'harvest_amount1': int(event['data'][66:], 16)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--host-comparison', type=Path, required=True)
    parser.add_argument('--host-before', type=Path, required=True)
    parser.add_argument('--host-after', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest, source, expected_sources, archive_checked = preparation(args.preparation)
    values = {name: fetch(args.evidence, name) for name in ARTIFACTS}
    result, final, progress = (values[key] for key in ('RESULT.json', 'FINAL.json', 'PROGRESS.json'))
    need(result['success'] is result['cleanup'] is True and result['started_scenarios'] ==
        result['passed_scenarios'] == list(STAGES) and result['old_test_bodies_run'] == 0 and
        result['zero_component_test_bodies_run'] is True and result['public_transactions'] == result['new_seals'] == 0
        and result['production_approved'] is False and 0 < number(result['elapsed_seconds']) <= 900,
        'complete_finite_campaign')
    need(progress == {'schema': 1, 'started': list(STAGES), 'passed': list(STAGES),
        'current': None, 'old_test_bodies_run': 0}, 'complete_scenario_progress')
    details = obj(packed(result['scenario_details']))
    need(set(details) == set(STAGES), 'all_stage_details')
    export, raw, vectors = raw_vectors(values['MODEL_EVIDENCE.json'], source)
    accounting = fee_and_booking(values, raw, vectors)
    model, stopped, complete = (values[key] for key in ('MODEL_RESULT.json', 'MODEL_STOP.json', 'COMPLETE.json'))
    need(model == complete and model['success'] is True and stopped['success'] is True and
        stopped['final_source_and_inputs_unchanged'] is True and stopped['cleanup']['stopped'] is True and
        stopped == result['model_stop'], 'successful_final_model_stop')
    for record in (model, stopped, export['exact_counters']):
        need(record['raw_attempts'] == record['raw_forwarded'] == record['raw_guarded'] == 1 and
            record['node_nonces'] == {'latest': 1, 'pending': 1} and
            record['configuration_raw_sha256'] == model['configuration_raw_sha256'] and
            record['final_journal_sha256'] == sha(raw['FINAL_JOURNAL.json']) and
            0 < record['shared_RPC_requests'] <= 6000, 'single_send_current_counters')
    need(all(model[key] == value for key, value in export['exact_counters'].items()),
        'exact_export_model_counter_binding')
    need(model['source_head'] == HEAD and model['keeper_interval_seconds'] == 240 and
        model['confirmations'] == 12 and model['hourly_harvest'] == 3600 and
        model['gas_ceiling'] == 24000000 and model['padding_percent'] == 25 and
        all(model[key] is True for key in ('final_financial_capture_complete',
        'post_inclusion_financial_unchanged', 'initial_NFT_rights_and_principal_unchanged',
        'canonical_receipt_booked_once', 'actual_following_normal_health_accepted')) and
        model['public_transactions'] == model['new_seals'] == model['old_test_bodies_run'] == 0,
        'unchanged_execution_profile')
    before, included, after = (vectors[name] for name in RAW_NAMES[5:8])
    need(included == after and before['rights'] == after['rights'] and
        before['physical'] == after['physical'], 'exact_physical_rights_money_vectors')
    need(after['physical']['main'] == after['physical']['group'][1] and
        after['physical']['group'][7] == 1 and after['physical']['liquidity'] > 0,
        'active_preserved_physical_principal')

    ready, pending, included_phase, settled, healthy = (values[key] for key in
        ('READY.json', 'PENDING.json', 'INCLUDED.json', 'SETTLED.json', 'HEALTHY.json'))
    need(settled['health']['status'] == 'degraded' and settled['health']['pending'] is False and
        settled['health']['rebalance_confirmation_health']['policy']['state'] == 'pending_recovery' and
        healthy['normal_loop_only'] is True and healthy['forced_refresh'] is False and
        healthy['health']['status'] == 'healthy_v2' and healthy['health']['live'] is True and
        healthy['health']['pending'] is False and healthy['acceptance']['checker']['ok'] is True and
        healthy['acceptance']['checker']['reasons'] == [], 'degraded_then_actual_healthy_wake')
    for name, anchor in healthy['acceptance']['canonical_observation_anchors'].items():
        observation = (healthy['health']['lp_execution_health']['last_confirmed'] if name == 'execution' else
            healthy['health']['rebalance_confirmation_health']['policy']['last_observed'])
        need(anchor['number'] == observation['block_number'] and anchor['hash'] == observation['block_hash'] and
            anchor['timestamp'] == observation['block_timestamp'] and
            -30 <= number(anchor['wall_age_seconds']) <= 300 and
            abs(healthy['acceptance']['read_wall_unix'] - anchor['timestamp'] - anchor['wall_age_seconds']) < .001,
            'fresh_observation_anchor')
    need(included_phase['confirmations'] == 12 and included_phase['local_mining_only'] is True and
        included_phase['accepted_hash'] == accounting['hash'] and
        quantity(included_phase['head']['number']) - quantity(included_phase['receipt_block']['number']) + 1 == 12,
        'directed_local_confirmation_depth')

    race_ready, race, hold, held = (values[key] for key in
        ('RACE_READY.json', 'RACE_RESULT.json', 'HOLD_READY.json', 'HOLD_RESULT.json'))
    need(race['success'] is True and race['refusal_code'] == 'backup_capture' and
        race['cause_code'] == 'source_snapshot_changed' and race['instrumented_read_barrier'] is True and
        race['production_sources_changed'] is False and
        race['captured_journal_sha256'] == race_ready['captured_journal_sha256'] and
        race['captured_journal_sha256'] != race['actual_journal_sha256'] and
        race['selection_before'] == race['selection_after_under_lock'] == race_ready['selection_before'],
        'instrumented_safe_capture_refusal')
    need(held['success'] is True and held['files_before'] == held['files_after'] == hold['files'] and
        held['pending'] == hold['pending'] and held['queued_ids'] == hold['queued_ids'] and
        hold['pending']['first_seen'] <= number(healthy['acceptance']['read_wall_unix']), 'held_history_exact')
    timeline = [ready['monotonic'], race_ready['monotonic'], pending['monotonic'], race['monotonic'],
        hold['monotonic'], held['monotonic'], included_phase['monotonic'], settled['monotonic'], healthy['monotonic']]
    need(all(number(item) > 0 for item in timeline) and timeline == sorted(timeline), 'actual_process_timeline')
    # Report observed deltas; do not invent a239s minimum after receipt recovery.
    timing = {'ready_to_pending': pending['monotonic'] - ready['monotonic'],
        'include_to_settled': settled['monotonic'] - included_phase['monotonic'],
        'settled_to_healthy': healthy['monotonic'] - settled['monotonic'],
        'explicit_hold_seconds': held['monotonic'] - hold['monotonic']}
    sidecars = values['SIDECAR_RESULT.json']
    records = obj(packed(sidecars['records']))
    received = obj(packed(sidecars['receiver_events']))
    need(len(records) == sidecars['invocations'] <= 128 and sidecars['max_backups'] == 32 and
        sidecars['lab_backup_seconds'] == 45 and sidecars['lab_observer_seconds'] == 10 and
        sidecars['complete_output_not_truncated'] is True and records, 'bounded_native_sidecar_records')
    def busy(row, lower, upper):
        return (row['action'] in ('backup', 'observe') and row['started_monotonic'] >= lower and
            row['ended_monotonic'] <= upper and row.get('value', {}).get('refusal_code') == 'scheduler_lock')
    need({row['action'] for row in records if busy(row, hold['monotonic'], held['monotonic'])} ==
        {'backup', 'observe'}, 'both_actual_timer_lock_refusals')
    need(any(row['action'] == 'backup' and row.get('returncode') == 0 and
        row.get('value', {}).get('ok') is True and row['started_monotonic'] >= settled['monotonic']
        for row in records) and any(row['action'] == 'observe' and row.get('returncode') == 0 and
        row.get('value', {}).get('ok') is True and row['started_monotonic'] >= healthy['monotonic']
        for row in records), 'eventual_ordinary_timer_success')
    held_detail = details[STAGES[1]]
    ack = held_detail['after_ack']
    need(ack['pending'] == hold['pending'] == held_detail['queued_before_hold']['pending'] and
        ack['outbox'] == [] and ack['sequence'] == hold['sequence'] and
        set(hold['queued_ids']) <= {event['event_id'] for event in received}, 'same_pending_and_outbox_ack')
    event_ids = {}
    for event in received:
        need(event['unsigned'] is True and event['readiness_approved'] is False and
            event['event_id'] == sha(enc([1, event['scope_sha256'], event['sequence'],
            event['type'], event['reason_code']])), 'received_event_identity')
        if event['event_id'] in event_ids:
            need(event_ids[event['event_id']] == event, 'same_id_different_payload')
        event_ids[event['event_id']] = event

    need(final['source_before'] == final['source_after'] == expected_sources and
        final['source_unchanged'] is final['all_owned_group_empty'] is
        final['mask_sources_unchanged'] is True and final['mask_before'] == final['mask_after'], 'final_source51')
    masks = final['mask_before']
    mask_ids = {(row['device'], row['inode']) for row in masks.values()}
    need(len(masks) == len(mask_ids) == 2 and all(row['uid'] == row['mode'] == row['bytes'] == 0
        and row['links'] == 1 for row in masks.values()), 'unchanged_unreadable_masks')
    for row in records:
        need(set(map(tuple, row['mask_inode_pairs'])) == mask_ids and
            row['action'] in ('init', 'backup', 'observe', 'barrier') and
            number(row['ended_monotonic']) >= number(row['started_monotonic']) and
            'error_type' not in row, 'native_sidecar_secret_exclusion')
        need(row['value']['unsigned'] is True and row['value']['readiness_approved'] is False,
            'all_sidecar_invocations_unsigned')
    properties = obj(packed(values['NATIVE_PROPERTIES.json']['units']))
    final_properties = obj(packed(final['unit_properties']))
    services = {PREFIX + '.service', *(PREFIX + '-' + role + '.service' for role in
        ('model', 'keeper', 'backup', 'observe', 'init', 'barrier'))}
    timers = {PREFIX + '-backup.timer', PREFIX + '-observe.timer'}
    need(set(final_properties['after_stop']) == services | timers and all(
        row.get('MainPID', '0') == '0' and row.get('ControlGroup', '') == ''
        for name, row in final_properties['after_stop'].items() if name in services), 'final_owned_groups')
    need(all(final_properties['after_stop'][name]['ActiveState'] in ('inactive', 'failed') for name in timers),
        'final_owned_timers_stopped')
    keeper = properties[PREFIX + '-keeper.service']
    need(bool(keeper['first_existing']['InvocationID']) and
        keeper['first_existing']['Type'] == 'exec' and keeper['first_existing']['User'] == 'nobody' and
        keeper['first_existing']['CapabilityBoundingSet'] == '' and
        keeper['first_existing']['Restart'] == 'no' and
        'keeper.monitor' in keeper['first_existing']['ExecStart'] and
        '--live' in keeper['first_existing']['ExecStart'] and '--once' not in keeper['first_existing']['ExecStart'],
        'one_continuous_stock_daemon_invocation')
    if keeper['last'].get('InvocationID'):
        need(keeper['last']['InvocationID'] == keeper['first_existing']['InvocationID'], 'same_observed_keeper_invocation')
    else:
        need(keeper['last']['LoadState'] == 'not-found' and keeper['last']['MainPID'] == '0',
            'transient_keeper_unloaded_after_stop')
    for name, role in ((PREFIX + '-backup.service', 'backup'), (PREFIX + '-observe.service', 'observe')):
        row = properties[name]['first_existing']
        need(row['Type'] == 'oneshot' and row['User'] == 'nobody' and row['PrivateNetwork'] == 'yes' and
            row['CapabilityBoundingSet'] == '' and row['Restart'] == 'no' and row['KillMode'] == 'control-group' and
            'masks/key.empty' in row['BindReadOnlyPaths'] and 'masks/password.empty' in row['BindReadOnlyPaths'],
            'actual_unsigned_native_unit')
    commands = obj(packed(values['MANAGER_TRACE.json']['commands']))
    need(len(commands) == values['MANAGER_TRACE.json']['count'] <= 300 and
        all(row['program'] in ('systemctl', 'systemd-run') and set(row['owned_units']) <= services | timers
        for row in commands), 'bounded_owned_manager_trace')
    for name, row in values['WORKER_LOGS.json']['logs'].items():
        need(uint(row['bytes']) <= MAX_WIRE, 'worker_log_bound')
        descriptor = {'decoded_bytes': row['bytes'], 'decoded_sha256': row['sha256'], 'gzip_base64': row['gzip_base64']}
        need(len(packed(descriptor)) == row['bytes'], 'worker_log_exact_bytes')

    preservation = json_file(args.host_comparison, MAX_WIRE, 'host/HOST_PRESERVATION.json')
    host_before = json_file(args.host_before, MAX_WIRE, 'host/before-CAPTURE.json')
    host_after = json_file(args.host_after, MAX_WIRE, 'host/final-CAPTURE.json')
    need(preservation['success'] is True and preservation['non_ambient_difference_count'] == 0 and
        preservation['existing_units_checked'] == 5 and preservation['raw_host_details_published'] is False and
        all(value is True for value in preservation['checks'].values()) and
        preservation['before_snapshot_sha256'] == host_before['snapshot_sha256'] and
        preservation['final_snapshot_sha256'] == host_after['snapshot_sha256'] and
        all(row['success'] is row['read_only'] is row['snapshot_complete'] is True and
        row['credentials_read_or_exported'] is False and row['service_actions'] == row['exit_code'] == 0
        for row in (host_before, host_after)), 'sanitized_host_preservation')
    observer_invocations = uint(preservation['ignored_observer_invocation_count'])
    summary = {'schema': 1, 'kind': 'independent_saved_c822_composition_reconciliation', 'success': True,
        'source_head': HEAD, 'production_source_members': 36, 'archive_members': 45,
        'archive_bytes_reverified': archive_checked, 'source51_and_inputs_unchanged': True,
        'actual_raw_vector_files_rehashed': len(raw), 'stages_passed': list(STAGES),
        'component_test_bodies_executed': 0, 'new_keeper_transactions': 1, 'accounting': accounting,
        'journal_booked_fields_equal_settled_healthy_final': True,
        'included_final_financial_vectors_equal': True, 'initial_final_rights_and_principal_equal': True,
        'actual_genuine_healthy_later_wake': True, 'observed_monotonic_deltas_seconds': timing,
        'ordinary_sidecar_invocations': len(records), 'acknowledged_original_queued_ids': hold['queued_ids'],
        'notification_delivery_is_at_least_once': True, 'receiver_events': len(received),
        'unique_receiver_event_ids': len(event_ids), 'shared_RPC_requests': stopped['shared_RPC_requests'],
        'all_seven_services_and_two_timers_stopped': True, 'five_existing_units_preserved': True,
        'non_ambient_host_differences': 0, 'disclosed_observer_invocations': observer_invocations,
        'verification_application_imports': 0, 'verification_test_bodies_run': 0,
        'verification_network_requests': 0, 'verification_server_actions': 0, 'production_approved': False,
        'scope_limits': ['same-host isolated copied F6 state and mock references; no actual market/provider qualification',
            'instrumented RACE overlaps actual signing; explicit HOLD precedes inclusion; later recovery uses ordinary timers',
            'observed timing and current300s anchor checks do not promise zero lag, exact periodic execution or multi-day soak',
            'local canonical hash/receipt/header relationships are reconciled; not an independent consensus or RLP reconstruction',
            'fee-empty or controlled fixture does not newly qualify dynamic funded80/10/5/5 allocation or Robinhood complete fees',
            'no off-host possession/fencing, real notification relay, physical durability or independent release approval',
            'sanitized host comparison is cross-bound to capture pins; private raw host details are not republished'],
        'input_pins': INPUT_PINS, 'verifier_sha256': sha(Path(__file__).read_bytes())}
    output = args.output.resolve()
    need(output.parent.is_dir() and not output.exists(), 'exclusive_verification_output')
    encoded = (json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    need(len(encoded) <= MAX_ARTIFACT, 'verification_result_bound')
    with output.open('xb') as stream:
        stream.write(encoded)
    print(json.dumps({'success': True, 'raw_vectors_rehashed': len(raw), 'new_transactions': 1,
        'output_bytes': len(encoded), 'output_sha256': sha(encoded), 'test_bodies_run_by_verifier': 0}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        code = str(exc) if type(exc) is ValueError and re.fullmatch('[a-z0-9_]+', str(exc)) else 'invalid_saved_evidence'
        print(json.dumps({'success': False, 'failure_code': code, 'error_type': type(exc).__name__,
            'application_imports': 0, 'test_bodies_run': 0, 'network_requests': 0, 'server_actions': 0}))
        raise SystemExit(1) from None
