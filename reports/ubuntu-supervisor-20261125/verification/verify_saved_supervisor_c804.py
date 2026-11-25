"""NEW independent stdlib-only review of frozen c804 saved public vectors.

DRAFT: written before evidence closure; no execution or passing result implied.
Read-only: no project imports, RPC, subprocess, signing, file writes or repair.
Artifacts may be flat or below fetch directories; conflicting duplicate names
refuse. Native cleanup and transaction recovery are separate required checks.
An optional final journal is read only after the parent has stopped both units.
"""
from pathlib import Path, PurePosixPath
import argparse
import datetime
import hashlib
import io
import json
import math
import re
import stat
import tarfile

HEAD = '7f862557df8e8cbaf8494c7b1c12f18e07be436d'
LAB = '/opt/popl-ubuntu-supervisor-20261125-c804'
KEEPER = 'popl-ubuntu-supervisor-20261125-c804-keeper.service'
MODEL = 'popl-ubuntu-supervisor-20261125-c804-model.service'
BUCKET = 47181787163762592248710325652087236475813397965818762058663276509558631703230
GOVERNANCE = '0x000000000000000000000000000000000000a0a0'
KEEPER_CHANGED = '0x4e4109d520c9526f0541c4732fe75bfe81842ffcba4a1a829277abfaeba117da'
SET_KEEPER = '0xd1b9e853'
MAX_JSON = 2 * 1024 * 1024


class Refused(ValueError):
    pass


class Missing(Refused):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'Duplicate JSON field')
            result[key] = value
        return result

    def constant(_):
        raise Refused('Nonfinite JSON constant')

    def real(value):
        result = float(value)
        need(math.isfinite(result), 'Overflowing/nonfinite JSON number')
        return result

    return json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
                      parse_constant=constant, parse_float=real)


def uint(value):
    if type(value) is str:
        need(re.fullmatch(r'0|[1-9][0-9]{0,77}', value) is not None,
             'Invalid canonical decimal quantity')
        value = int(value)
    need(type(value) is int and 0 <= value < 1 << 256, 'Invalid unsigned quantity')
    return value


def q(value):
    need(type(value) is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})', value)
         is not None, 'Invalid RPC hexadecimal quantity')
    return int(value, 16)


def address(value):
    need(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{40}', value) is not None,
         'Invalid address')
    return value.lower()


def hash32(value):
    need(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{64}', value) is not None
         and int(value, 16) > 0, 'Invalid nonzero public hash')
    return value.lower()


def number(value):
    need(type(value) in (int, float) and math.isfinite(value) and value >= 0,
         'Invalid monotonic time')
    return value


def bounded(path, maximum=MAX_JSON):
    path = Path(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and not path.is_symlink() and
         before.st_nlink == 1 and 0 <= before.st_size <= maximum,
         'Input is not a bounded single-link regular file')
    raw = path.read_bytes()
    after = path.lstat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns)
    need(key(before) == key(after) and len(raw) == before.st_size,
         'Input changed during read')
    return raw


class Inputs:
    def __init__(self, root):
        self.root = Path(root)
        self.used = {}

    def raw(self, name, optional=False, maximum=MAX_JSON):
        matches = sorted(self.root.rglob(name))
        need(len(matches) <= 32, 'Artifact duplicate count exceeded')
        if not matches:
            if optional:
                return None
            raise Missing('Required artifact missing: ' + name)
        values = [bounded(path, maximum) for path in matches]
        need(all(value == values[0] for value in values),
             'Conflicting duplicate artifact: ' + name)
        self.used[name] = {'bytes': len(values[0]), 'sha256': sha(values[0]),
                           'identical_copies': len(matches)}
        return values[0]

    def get(self, name, optional=False):
        raw = self.raw(name, optional)
        return None if raw is None else strict_json(raw)


def journal(row, raw_key='raw_utf8', hash_key='sha256'):
    need(type(row) is dict and type(row.get(raw_key)) is str,
         'Raw journal bytes not supplied')
    raw = row[raw_key].encode('utf-8', 'strict')
    need(len(raw) <= MAX_JSON and sha(raw) == row[hash_key], 'Journal byte digest differs')
    state = strict_json(raw)
    need(type(state) is dict, 'Journal is not an object')
    if 'state' in row:
        need(state == row['state'], 'Raw journal and decoded state differ')
    return state, raw


def critical(state):
    keys = ('chain_id', 'sender', 'contracts', 'accounting_model', 'accounting_version',
            'fee_intake_version', 'pending', 'next_nonce', 'receipt_anchor', 'spent',
            'last_fee_observation', 'last')
    result = {key: state.get(key) for key in keys}
    for key in ('last_harvest', 'harvested_at'):
        if key in state:
            result[key] = state[key]
    return result


def source_review(build):
    receipt_raw = bounded(build / 'BUILD_RECEIPT.json')
    receipt = strict_json(receipt_raw)
    need(receipt['lab'] == LAB and receipt['feature'] == 'body' and
         receipt['current_production_members_byte_identical'] == 190 and
         receipt['production_sources_changed'] is False, 'Unexpected build stage')
    archive_raw = bounded(build / 'c804.inputs.tar.gz', 96 * 1024 * 1024)
    need({'bytes': len(archive_raw), 'sha256': sha(archive_raw)} == receipt['bundle'],
         'Frozen archive differs from build receipt')
    members, total = {}, 0
    with tarfile.open(fileobj=io.BytesIO(archive_raw), mode='r|gz') as archive:
        for item in archive:
            path = PurePosixPath(item.name)
            need(len(members) < 2048 and item.isfile() and not path.is_absolute() and
                 '..' not in path.parts and str(path) == item.name and
                 '\\' not in item.name and item.name not in members and
                 0 <= item.size <= 32 * 1024 * 1024, 'Unsafe frozen archive member')
            total += item.size
            need(total <= 256 * 1024 * 1024, 'Expanded archive bound exceeded')
            raw = archive.extractfile(item).read(item.size + 1)
            need(len(raw) == item.size, 'Archive member length differs')
            members[item.name] = raw
    manifest = strict_json(members['MANIFEST.json'])
    need({'bytes': len(members['MANIFEST.json']), 'sha256': sha(members['MANIFEST.json'])}
         == receipt['manifest'], 'Manifest digest differs')
    need(set(members) == set(manifest['members']) | {'MANIFEST.json'},
         'Archive inventory differs')
    for name, pin in manifest['members'].items():
        need({'bytes': len(members[name]), 'sha256': sha(members[name])} == pin,
             'Frozen archive member pin differs')
    source_raw = members['inputs/SOURCE_MANIFEST.json']
    source = strict_json(source_raw)
    need(sha(source_raw) == receipt['source_manifest_sha256'] and
         source['source_head'] == HEAD and len(source['members']) == 190 and
         source['frozen_F6_Solidity_modified'] is False and
         source['unrelated_dirty_worktree_files_excluded'] is True,
         'Frozen production-source identity differs')
    for name, pin in source['members'].items():
        raw = members['source/contracts/' + name]
        need({'bytes': len(raw), 'sha256': sha(raw)} == pin,
             'Production source member differs')
    for name, pin in receipt['helpers'].items():
        raw = bounded(build / name)
        need({'bytes': len(raw), 'sha256': sha(raw)} == pin and
             raw == members['source/helpers/' + name], 'Executed helper source differs')
    for name, key in (('remote_capsule.py', 'controller'), ('host_control.py', 'host_wrapper')):
        raw = bounded(build / name)
        need({'bytes': len(raw), 'sha256': sha(raw)} == receipt[key],
             'Controller/wrapper pin differs')
    return {'source_head': HEAD, 'production_members': 190,
            'bundle_sha256': sha(archive_raw), 'build_receipt_sha256': sha(receipt_raw),
            'helper_pins': receipt['helpers'],
            'scope': 'saved local archive/source identity; remote adoption needs native receipts'}


def saved_hash_review(inputs):
    initial, _ = journal(inputs.get('case-INITIAL_JOURNAL.json'))
    pending_row = inputs.get('case-DURABLE_PENDING.json')
    pending_state, pending_raw = journal(pending_row)
    baseline = inputs.get('native-BASELINE.json')
    baseline_state, baseline_raw = journal(baseline, 'journal_raw_utf8', 'journal_sha256')
    trigger = inputs.get('case-FAULT_TRIGGER.json')
    trigger_state, trigger_raw = journal(trigger, 'journal_raw_utf8', 'journal_sha256')
    restart = inputs.get('native-JOURNAL_DURING_RESTART.json')
    restart_state, restart_raw = journal(restart)
    need(pending_raw == baseline_raw == trigger_raw == restart_raw and
         pending_state == baseline_state == trigger_state == restart_state,
         'Saved hash journal changed before native recovery')
    p = pending_state['pending']
    need(initial['pending'] is None and initial['next_nonce'] == 0 and initial['spent'] == {} and
         initial['receipt_anchor'] is None and p['nonce'] == pending_state['next_nonce'] == 0,
         'Fresh initial/pending nonce or spending differs')
    need(pending_state['sender'] == initial['sender'] and pending_state['chain_id'] ==
         initial['chain_id'] == 4663 and pending_state['spent'] == initial['spent'],
         'Pending publication altered sender/chain/paid spending')
    need(hash32(p['hash']) == hash32(trigger['pending_hash']) and p == trigger['intent'] and
         p['key'] == 'harvest:' + str(BUCKET) and uint(p['value']) == 0 and
         address(p['to']) == address(pending_state['contracts']['vault']),
         'Saved harvest identity differs')
    need(trigger['method'] == 'eth_getTransactionReceipt' and
         trigger['fault'] == 'chunk_size_without_CRLF' and
         trigger['trickle_interval_seconds'] == 1 and trigger['maximum_trickle_seconds'] == 160 and
         trigger['completed_http_reply'] is False, 'Wrong/no saved-hash body-framing fault')
    raw_reviews = inputs.get('case-RAW_REVIEWS.json')
    need(type(raw_reviews) is list and len(raw_reviews) == 1,
         'Expected one captured pre-signing review')
    review_intent = dict(raw_reviews[0]['intent'])
    need(review_intent.get('hash') is None and raw_reviews[0]['raw_signature_retained'] is False,
         'Raw signing review was not originally hashless/public-only')
    review_intent['hash'] = p['hash']
    need(review_intent == p, 'Original signing review changed during broadcast/recovery')
    return {'transaction_hash': p['hash'], 'saved_journal_sha256': sha(pending_raw),
            'four_raw_snapshots_identical': True, 'saved_intent': p}


def transaction_review(inputs):
    original = inputs.get('case-DURABLE_PENDING.json')['state']
    p = original['pending']
    row = inputs.get('case-RECOVERED_JOURNAL.json')
    state, tx, receipt, block, head = (row[key] for key in
        ('state', 'transaction_without_signature', 'receipt', 'receipt_block', 'head'))
    need(hash32(tx['hash']) == hash32(receipt['transactionHash']) == hash32(p['hash']) and
         hash32(tx['blockHash']) == hash32(receipt['blockHash']) == hash32(block['hash']) and
         q(tx['blockNumber']) == q(receipt['blockNumber']) == q(block['number']),
         'Saved transaction canonical inclusion differs')
    index = q(receipt['transactionIndex'])
    need(q(tx['transactionIndex']) == index and type(block['transactions']) is list and
         index < len(block['transactions']) and hash32(block['transactions'][index]) == hash32(p['hash']),
         'Header transaction index differs')
    need(address(tx['from']) == address(state['sender']) == address(original['sender']) ==
         address(receipt['from']) and address(tx['to']) == address(p['to']) ==
         address(receipt['to']) and tx['input'].lower() == p['data'].lower() and
         q(tx['nonce']) == uint(p['nonce']) == 0 and q(tx['value']) == uint(p['value']) == 0 and
         q(tx['chainId']) == state['chain_id'] == 4663 and q(receipt['status']) == 1,
         'Transaction sender/target/calldata/nonce/value/chain/status differs')
    need(q(head['number']) - q(block['number']) + 1 >= 12 and
         q(head['timestamp']) >= q(block['timestamp']), 'Twelve canonical confirmations absent')
    f, kind, gas, used = p['fee_review'], q(tx.get('type', '0x0')), q(tx['gas']), q(receipt['gasUsed'])
    need(type(f.get('schema')) is int and f['schema'] == 1 and
         0 < used <= gas == uint(f['gas_limit']) <= 24000000 and
         f['receipt_fee_policy'] == 'included' and uint(f['l1_fee_allowance_wei']) == 0 and
         q(receipt.get('l1Fee', '0x0')) == 0, 'Captured gas/profile/fee semantics differ')
    if kind == 2:
        cap, tip, base = q(tx['maxFeePerGas']), q(tx['maxPriorityFeePerGas']), q(block['baseFeePerGas'])
        need(tip <= cap and base <= cap, 'Invalid canonical EIP1559 envelope')
        price = min(cap, base + tip)
    elif kind in (0, 1):
        cap = price = q(tx['gasPrice'])
        need(q(receipt['effectiveGasPrice']) == price, 'Legacy reported/canonical price differs')
    else:
        raise Refused('Unsupported signed transaction fee type')
    need(0 < cap == uint(f['max_fee_per_gas']) <= 5000000000 and
         gas * cap == uint(f['maximum_cost_wei']) <= 10**16, 'Signed maximum exceeds original limits')
    paid = used * price
    need(0 < paid <= gas * cap and uint(row['paid_wei']) == paid and
         uint(row['canonical_execution_price_wei']) == price and
         uint(row['reported_effective_gas_price_wei']) == q(receipt['effectiveGasPrice']),
         'Independent canonical execution cost differs')
    day = datetime.datetime.fromtimestamp(q(block['timestamp']), datetime.timezone.utc).date().isoformat()
    expected_spent = {key: uint(value) for key, value in original['spent'].items()}
    expected_spent[day] = expected_spent.get(day, 0) + paid
    need({key: uint(value) for key, value in state['spent'].items()} == expected_spent and
         sum(expected_spent.values()) <= 5 * 10**16 and state['pending'] is None and
         state['next_nonce'] == p['nonce'] + 1 and state['receipt_anchor'] == {
             'number': q(block['number']), 'hash': block['hash'],
             'timestamp': q(block['timestamp']), 'nonce': p['nonce']} and
         state['last'][p['key']] == q(block['timestamp']), 'Nonce/anchor/day/harvest cost not settled once')
    need(state['last_fee_observation'] == {
        'transaction': p['hash'], 'reported_price_wei': q(receipt['effectiveGasPrice']),
        'execution_price_wei': price, 'gas_used': used, 'l1_fee_wei': 0,
        'receipt_fee_policy': 'included', 'cost_wei': paid}, 'Exact fee observation differs')
    records = inputs.get('case-RECEIPTS.json')
    need(len(records) == 1 and records[0]['hash'] == p['hash'] and records[0]['intent'] == p and
         records[0]['receipt'] == receipt, 'Final saved receipt inventory differs')
    for name in ('model-COMPLETE.json', 'model-RESULT.json'):
        result = inputs.get(name)
        need(result['success'] is True and result['raw_attempts'] == result['raw_forwarded'] == 1 and
             result['saved_hash_recovered'] is True and result['fresh_stock_healthy_cycle'] is True and
             0 < result['shared_RPC_requests'] <= 6000 and result['public_transactions'] == 0 and
             result['new_seals'] == 0 and result['old_feature_journeys_or_tests_run'] == 0,
             'Campaign counters/outcome do not support exactly one finite recovery')
    case = inputs.get('case-RESULT.json')
    need(case['raw_attempts'] == case['raw_forwarded'] == 1 and case['stock_transactions'] == 1 and
         case['gateway_refusals'] == [] and case['status'] == 'passed',
         'Gateway/case records contain another send/refusal/incomplete outcome')
    health = inputs.get('case-HEALTHY_NORMAL_CYCLE.json')
    need(health['status'] == 'healthy_v2', 'Fresh normal healthy cycle absent')
    return {'transaction_hash': p['hash'], 'gas_used': used, 'canonical_price_wei': price,
            'reported_price_wei': q(receipt['effectiveGasPrice']), 'paid_wei': paid,
            'original_maximum_cost_wei': gas * cap, 'nonce_before': 0, 'nonce_after': 1,
            'one_source_bound_raw_attempt': True,
            'recovered_digest': 'reported SHA only; RECOVERED_JOURNAL has no raw_utf8',
            'fee_profile': 'original schema1, not profile2 adoption'}


def financial_review(inputs):
    before, after = inputs.get('case-FINANCIAL_BEFORE.json'), inputs.get('case-FINANCIAL_AFTER.json')
    need(before['rights'] == after['rights'] and len(before['rights']) == 2 and
         before['physical'] == after['physical'], 'NFT rights or LP principal changed')
    physical = before['physical']
    need(len(physical['group']) == 8 and physical['group'][7] == 1 and
         uint(physical['main']) > 0 and uint(physical['secondary']) == 0 and
         uint(physical['liquidity']) > 0, 'Wrong/missing original one-main active LP projection')
    for row in before['rights']:
        uint(row['id'])
        uint(row['shares'])
        uint(row['eligible'])
        uint(row['royalty_weight'])
        need(type(row['owner']) is str and re.fullmatch(r'0x[0-9a-fA-F]{64}', row['owner'])
             is not None and int(row['owner'], 16) > 0, 'Missing owner result')
    return {'two_NFT_owner_share_membership_royalty_projections_equal': True,
            'main_LP_identity_liquidity_ticks_custody_projection_equal': True,
            'money_projection_equal': before['money'] == after['money'],
            'money_projection_differences': [key for key in sorted(set(before['money']) | set(after['money']))
                if before['money'].get(key) != after['money'].get(key)],
            'scope': 'saved getter projections; no new allocation/LP-flow requalification'}


def authority_review(inputs):
    sender = address(inputs.get('case-INITIAL_JOURNAL.json')['state']['sender'])
    access = address(inputs.get('case-INITIAL_JOURNAL.json')['state']['contracts']['access'])
    rows = [row for row in inputs.get('case-SETUP.json') if row.get('label') == 'enable_new_keeper']
    need(len(rows) == 1, 'Exactly one saved local keeper grant is required')
    row, data = rows[0], SET_KEEPER + f'{int(sender, 16):064x}' + f'{1:064x}'
    envelope, receipt = row['envelope'], row['receipt']
    need(address(envelope['from']) == GOVERNANCE and address(envelope['to']) == access and
         envelope['data'].lower() == data and q(envelope['value']) == 0 and
         hash32(row['hash']) == hash32(receipt['transactionHash']) and q(receipt['status']) == 1 and
         address(receipt['from']) == GOVERNANCE and address(receipt['to']) == access,
         'Saved grant envelope/receipt projection differs')
    events = [event for event in receipt['logs'] if address(event['address']) == access and
              event.get('topics') and event['topics'][0].lower() == KEEPER_CHANGED]
    need(len(events) == 1 and len(events[0]['topics']) == 2 and
         int(events[0]['topics'][1], 16) == int(sender, 16) and
         events[0]['data'].lower() == '0x' + f'{1:064x}', 'KeeperChanged grant event differs')
    return {'saved_grant_envelope_and_event_consistent': True,
            'before_after_role_getters': 'not supplied; no authority equality inferred',
            'setup_canonical_header': 'not supplied for this grant; receipt projection/source bound',
            'permissionless_harvest_is_authorization_proof': False,
            'governance_or_guardian_authority_added': 'not inferred'}


def policy(values):
    expected = {'WatchdogUSec': '2min', 'TimeoutStopUSec': '2min', 'RestartUSec': '30s',
                'Restart': 'on-failure', 'NotifyAccess': 'main', 'WatchdogSignal': '9',
                'KillMode': 'control-group', 'SendSIGKILL': 'yes', 'FinalKillSignal': '9',
                'LimitCORE': '0', 'StartLimitIntervalUSec': '10min', 'StartLimitBurst': '5',
                'User': 'nobody', 'Group': 'nogroup', 'PrivateNetwork': 'yes',
                'NoNewPrivileges': 'yes', 'ProtectSystem': 'strict', 'ProtectHome': 'yes',
                'ProtectControlGroups': 'yes', 'PrivateDevices': 'yes',
                'WorkingDirectory': LAB + '/source/contracts'}
    need(all(values.get(key) == value for key, value in expected.items()),
         'Loaded native keeper supervisor policy differs')
    need(MODEL in values.get('JoinsNamespaceOf', '').split() and
         '/usr/bin/python3 -m keeper.monitor --config ' + LAB +
         '/runtime/run-001/model/supervisor/actor/config.json --live' in values['ExecStart'],
         'Direct stock main/namespace dependency differs')


def old_dead(snapshot, old):
    expected = {(row['pid'], row['start_ticks']) for row in old}
    rows = snapshot['old_processes']
    need({(row['pid'], row['start_ticks']) for row in rows} == expected,
         'Old-generation process observation set differs')
    all_dead = True
    for row in rows:
        current = row['current']
        same = current is not None and current['start_ticks'] == row['start_ticks']
        live = same and current['state'] not in ('Z', 'X')
        need(row['same_generation'] == same and row['same_generation_live'] == live,
             'Old-generation liveness flags contradict raw process identity')
        all_dead = all_dead and not live
    return all_dead


def native_review(inputs):
    base = inputs.get('native-BASELINE.json')['snapshot']
    proof = inputs.get('native-NATIVE_RESTART_PROOF.json')
    need(proof['baseline'] == base and base['lab'] == LAB, 'Native baseline identity differs')
    old_unit = base['units'][KEEPER]
    policy(old_unit['properties'])
    old = [row for row in old_unit['cgroup']['processes'] if row is not None]
    need(old == proof['old_processes'] and proof['old_main_pid'] == int(old_unit['properties']['MainPID'])
         and proof['old_invocation_id'] == old_unit['properties']['InvocationID'] and
         int(old_unit['properties']['WatchdogTimestampMonotonic']) > 0,
         'Old native main/generation/accepted notification differs')
    samples = proof['samples']
    need(type(samples) is list and 2 <= len(samples) <= 1200, 'Missing bounded native restart samples')
    empty, new = [], []
    prior = -1
    for sample in samples:
        end = number(sample['finished_monotonic'])
        need(number(sample['started_monotonic']) <= end and end >= prior and sample['lab'] == LAB,
             'Native sample monotonic/lab identity differs')
        prior = end
        unit = sample['units'][KEEPER]
        p = unit['properties']
        need(unit['cgroup']['path'] == '/system.slice/' + KEEPER, 'Recursive cgroup path differs')
        dead = old_dead(sample, old)
        if int(p['MainPID']) == 0 and unit['cgroup']['pids'] == [] and dead:
            empty.append(end)
        if int(p['MainPID']) > 1 and p.get('InvocationID') != proof['old_invocation_id']:
            need(dead, 'Old process generation overlaps replacement main')
            new.append((end, p))
    need(empty and new and min(empty) < new[0][0] and
         proof['observed_empty_monotonic'] == min(empty), 'Empty cgroup before restart not witnessed')
    observed, new_properties = new[0]
    need(min(empty) < int(new_properties['ExecMainStartTimestampMonotonic']) / 10**6 <= observed,
         'Sampled empty group does not precede actual new main start')
    ni = proof['new_invocation']
    need(ni['invocation_id'] == new_properties['InvocationID'] and
         ni['pid'] == int(new_properties['MainPID']) and
         ni['observed_monotonic'] == observed and ni['all_old_generations_dead'] is True and
         ni['observed_empty_before_restart'] == min(empty), 'New invocation summary contradicts samples')
    final = proof['final']
    need(old_dead(final, old), 'Old process generations survive final observation')
    unit = final['units'][KEEPER]
    policy(unit['properties'])
    need(int(unit['properties']['NRestarts']) == int(old_unit['properties']['NRestarts']) + 1 and
         unit['properties']['InvocationID'] == ni['invocation_id'], 'Native restart count/identity differs')
    main = next(row for row in unit['cgroup']['processes'] if row and row['pid'] == ni['pid'])
    model = final['units'][MODEL]
    mp = next(row for row in model['cgroup']['processes'] if row and
              row['pid'] == int(model['properties']['MainPID']))
    need(main['uid'] == mp['uid'] == 65534 and main['network_namespace'] == mp['network_namespace']
         != final['host_network_namespace'], 'Native unprivileged/private namespace identity differs')
    events = unit['manager_journal']
    for event in events:
        need(str(event['_PID']) == '1' and event['UNIT'] == KEEPER, 'Manager journal attribution differs')
    watchdog = [event for event in events if event.get('UNIT_RESULT') == 'watchdog' or
                re.search(r"failed with result ['\"]watchdog['\"]", event.get('MESSAGE', '').lower())]
    need(watchdog, 'Native watchdog outcome absent; manual main kill is a different partition')
    fault, closed = inputs.get('case-FAULT_TRIGGER.json'), inputs.get('case-FAULT_CLOSED.json')
    need(closed['completed_http_reply'] is False and closed['peer_disconnected'] is True and
         100 <= number(closed['elapsed_seconds']) <= 162 and
         100 <= uint(closed['fragments']) <= closed['elapsed_seconds'] + 2 and
         number(fault['monotonic']) < number(closed['monotonic']),
         'Continuously incomplete HTTP framing not independently supported')
    before, after = proof['lock_before'], proof['lock_after']
    middle = inputs.get('native-JOURNAL_DURING_RESTART.json')['lock']
    need((before['dev'], before['ino'], before['uid']) ==
         (after['dev'], after['ino'], after['uid']) ==
         (middle['dev'], middle['ino'], middle['uid']) and before['uid'] == 65534 and
         middle['exclusive_probe_when_empty'] is True, 'Persistent lock/release evidence differs')
    warnings = [event.get('MESSAGE', '') for event in events if
                re.search(r'failed to kill|invalid argument|warning', event.get('MESSAGE', ''), re.I)]
    return {'native_watchdog_restarts': 1, 'observed_old_cgroup_processes': len(old),
            'old_cgroup_had_processes_beyond_main': len(old) > 1,
            'empty_before_actual_new_main_start': True, 'same_persistent_lock_inode': True,
            'sampled_empty_to_new_observation_seconds': observed - min(empty),
            'fault': 'incomplete chunk-size framing with completed headers',
            'manager_warning_messages': warnings,
            'active_Cast_cleanup_experiment': 'not this case; verify separate manual-main-kill lab',
            'DNS_header_soak_offhost_fencing': 'not newly tested by these c804 vectors'}


def final_journal_review(inputs):
    raw = inputs.raw('FINAL_JOURNAL.raw', optional=True)
    if raw is None:
        raise Missing('Optional final raw journal not supplied; recovered digest remains unrecomputed')
    state = strict_json(raw)
    expected_raw = inputs.raw('FINAL_JOURNAL.sha256', optional=True, maximum=256)
    if expected_raw is not None:
        expected = expected_raw.decode('ascii', 'strict').strip()
        need(re.fullmatch('[0-9a-f]{64}', expected) is not None and sha(raw) == expected,
             'Final raw journal SHA sidecar differs')
    recovered = inputs.get('case-RECOVERED_JOURNAL.json')
    need(critical(state) == critical(recovered['state']), 'Final settled critical journal fields changed')
    differences = sorted(key for key in set(state) | set(recovered['state'])
                         if state.get(key) != recovered['state'].get(key))
    return {'final_sha256': sha(raw), 'sidecar_supplied': expected_raw is not None,
            'equals_reported_recovered_digest': sha(raw) == recovered['sha256'],
            'all_settled_critical_fields_equal': True,
            'other_top_level_fields_changed_after_normal_cycle': differences,
            'capture_after_stop': 'requires separate final native-stop vector'}


def cleanup_review(path):
    if path is None:
        raise Missing('Final native-stop vector not supplied')
    value = strict_json(bounded(path))
    need(value.get('phase') == 'stopped' and value.get('all_owned_units_stopped') is True,
         'Native stop request alone does not prove cleanup')
    snapshot = value['native_status']
    for name in (KEEPER, MODEL):
        unit = snapshot['units'][name]
        need(unit['properties'].get('ActiveState') in ('inactive', 'failed', None) and
             int(unit['properties'].get('MainPID', '0')) == 0 and
             unit['cgroup']['pids'] == [] and unit['cgroup']['processes'] == [],
             'Final owned native cgroup is not empty')
    return {'both_owned_native_units_finally_empty': True,
            'scope': 'final recursive process census; existing-service preservation is separate'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--native-stop', type=Path)
    args = parser.parse_args()
    inputs, checks = Inputs(args.evidence), {}
    tasks = [('frozen_sources', lambda: source_review(args.build_dir)),
             ('saved_hash_bytes', lambda: saved_hash_review(inputs)),
             ('canonical_paid_recovery_once', lambda: transaction_review(inputs)),
             ('NFT_LP_rights', lambda: financial_review(inputs)),
             ('authority_projection_only', lambda: authority_review(inputs)),
             ('native_watchdog_and_group_restart', lambda: native_review(inputs)),
             ('optional_final_raw_journal', lambda: final_journal_review(inputs)),
             ('final_native_cleanup', lambda: cleanup_review(args.native_stop))]
    for name, run in tasks:
        try:
            checks[name] = {'status': 'passed', 'proof': run()}
        except Missing as exc:
            checks[name] = {'status': 'missing', 'reason': str(exc)}
        except (Refused, KeyError, IndexError, StopIteration, TypeError, ValueError, OSError,
                tarfile.TarError) as exc:
            checks[name] = {'status': 'failed', 'reason': str(exc), 'error_class': type(exc).__name__}
    required = [row['status'] for name, row in checks.items() if name != 'optional_final_raw_journal']
    status = 'failed' if 'failed' in required else 'incomplete' if 'missing' in required else 'passed'
    print(json.dumps({'schema': 1, 'stage': 'c804_saved_vectors_independent_review', 'status': status,
        'checks': checks, 'input_files': inputs.used, 'runtime_actions': 0, 'network_calls': 0,
        'old_test_bodies_run': 0, 'production_approved': False,
        'limits': [
            'Only supplied frozen vectors are checked; input hashes provide identity, not hostile-host authentication.',
            'Incomplete chunk-size framing is a body-framing watchdog experiment; DNS is not newly tested.',
            'Saved-hash watchdog recovery does not prove active Cast watchdog/timeout cleanup.',
            'A separate actual-Cast manual main SIGKILL must retain its signal outcome, hashless intent and no-resend scope.',
            'Role getter equality is not supplied; permissionless harvest cannot prove keeper authorization.',
            'Money projections are compared but full nonzero fee allocation is not newly requalified.',
            'Off-host fencing/restore, storage/fsync/permission faults, restart storms, alerts, soak and provider fees stay open.',
            'Existing-service/heartbeat preservation requires its separate before/after host review.']},
        sort_keys=True, indent=2, allow_nan=False))
    return 1 if status == 'failed' else 2 if status == 'incomplete' else 0


if __name__ == '__main__':
    raise SystemExit(main())
