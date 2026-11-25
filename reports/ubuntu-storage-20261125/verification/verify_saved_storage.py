"""Independent saved-vector checks only; no imports of keeper or lab code."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import re
import tarfile

MAX_FILE = 2 * 1024 * 1024
MONITOR_SHA = '5ab6bbb20eea21e301d81d2e829a827594079561e2f10770336ec8585b234631'
BASE_HEAD = '352ebe0aa479a10f2220857edadbf049720616c5'


class Refused(ValueError):
    pass


class Missing(Refused):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(values):
    result = {}
    for key, value in values:
        need(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def bad_number(value):
    raise Refused('Nonfinite JSON value')


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_number)


class Inputs:
    def __init__(self, root):
        self.root = root.resolve()
        self.used = {}

    def raw(self, name):
        found = [p for p in self.root.rglob(name) if p.is_file() and not p.is_symlink()]
        if not found:
            raise Missing('Missing saved artifact: ' + name)
        values = []
        for path in found:
            need(path.stat().st_size <= MAX_FILE, 'Saved artifact exceeds bound')
            values.append(path.read_bytes())
        need(all(raw == values[0] for raw in values), 'Conflicting duplicate artifact: ' + name)
        self.used[name] = {'bytes': len(values[0]), 'sha256': sha(values[0])}
        return values[0]

    def json(self, name):
        return decode(self.raw(name))


def quantity(value):
    need(type(value) is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})', value),
         'Noncanonical EVM quantity')
    return int(value, 16)


def snapshot(record):
    need(type(record) is dict and type(record['raw_utf8']) is str, 'Raw journal snapshot absent')
    raw = record['raw_utf8'].encode('utf8')
    need(0 < len(raw) <= MAX_FILE and sha(raw) == record['sha256'], 'Journal raw/hash mismatch')
    state = decode(raw)
    need(state == record['state'], 'Journal parsed state differs from exact bytes')
    need(state['chain_id'] == 4663 and state['accounting_version'] == 7,
         'Journal identity/profile differs')
    return state


def source_review(inputs, build_dir):
    build = decode((build_dir / 'BUILD_RECEIPT.json').read_bytes())
    archive_path = build_dir / (Path(build['lab']).name.rsplit('-', 1)[-1] + '.inputs.tar.gz')
    if not archive_path.is_file():
        raise Missing('Original preserved input archive is required for source replay')
    need(archive_path.stat().st_size <= 96 * 1024 * 1024, 'Original archive exceeds bound')
    raw = archive_path.read_bytes()
    need(len(raw) == build['bundle']['bytes'] and sha(raw) == build['bundle']['sha256'],
         'Original source bundle differs')
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = archive.getmembers()
        need(len({m.name for m in members}) == len(members) and all(m.isfile() for m in members),
             'Archive entries differ')
        manifest_raw = archive.extractfile('MANIFEST.json').read(MAX_FILE + 1)
        need(len(manifest_raw) <= MAX_FILE and sha(manifest_raw) == build['manifest']['sha256'],
             'Original manifest differs')
        manifest = decode(manifest_raw)
        source_raw = archive.extractfile('inputs/SOURCE_MANIFEST.json').read(MAX_FILE + 1)
        need(len(source_raw) <= MAX_FILE and sha(source_raw) == build['source_manifest_sha256'],
             'Production source manifest differs')
        source = decode(source_raw)
        need(inputs.json('SOURCE.json') == source and source['source_head'] == BASE_HEAD,
             'Worker source identity differs')
        need(len(source['members']) == build['current_production_members'] == 190,
             'Production source inventory differs')
        need(source['members']['keeper/monitor.py']['sha256'] == MONITOR_SHA,
             'Reviewed production monitor differs')
        need({row['path'] for row in source['approved_worktree_overrides']} ==
             {'keeper/monitor.py', 'scripts/verify.sh'}, 'Unreviewed production override')
        for name, pin in build['helpers'].items():
            data = archive.extractfile('source/helpers/' + name).read(MAX_FILE + 1)
            need(len(data) == pin['bytes'] and sha(data) == pin['sha256'], 'Frozen lab helper differs')
        monitor = archive.extractfile('source/contracts/keeper/monitor.py').read(MAX_FILE + 1)
        need(sha(monitor) == MONITOR_SHA, 'Archived monitor bytes differ')
    limits = build['limits']
    expected = {'RPC_requests': 6000, 'worker_seconds': 900, 'maintenance_gas': 24000000,
                'padding_percent': 25, 'confirmations': 12, 'gas_price_wei': 5000000000,
                'single_maximum_cost_wei': str(10**16), 'daily_maximum_cost_wei': str(5 * 10**16),
                'namespace_private_tmpfs_bytes': 1048576}
    need(all(limits.get(key) == value for key, value in expected.items()), 'Unchanged lab/financial limits differ')
    return {'source_head': BASE_HEAD, 'production_members': 190, 'monitor_sha256': MONITOR_SHA,
            'source_manifest_sha256': build['source_manifest_sha256'], 'bundle_sha256': sha(raw)}


def filesystem_review(inputs):
    fs = inputs.json('FILESYSTEM.json')
    need(fs['fstype'] == 'tmpfs' and fs['bytes'] == 1048576 and fs['uid'] == 65534
         and fs['mode'] == '0o700', 'Bounded unprivileged tmpfs identity differs')
    need(fs['mount'].startswith('/opt/popl-ubuntu-storage-20261125-')
         and fs['mount'].endswith('/runtime/storage'), 'Unexpected storage target')
    need(fs['host_physical_filesystem_never_filled'] is True
         and fs['power_loss_or_ext4_durability_qualified'] is False, 'Storage evidence scope differs')
    return {'tmpfs_bytes': fs['bytes'], 'uid': fs['uid'], 'mount_namespace': fs['mount_namespace'],
            'physical_power_loss_qualified': False}


def branch_review(inputs):
    rows = inputs.json('BRANCHES.json')
    expected = [('intent_EACCES', 'EACCES', 0, 0), ('intent_ENOSPC', 'ENOSPC', 0, 0),
                ('accepted_hash_EACCES', 'EACCES', 0, 1), ('receipt_ENOSPC', 'ENOSPC', 1, 1),
                ('accepted_hash_ENOSPC', 'ENOSPC', 1, 2), ('receipt_EACCES', 'EACCES', 2, 2)]
    need(len(rows) == len(expected), 'Expected six distinct storage failures')
    for row, (stage, mode, before_count, after_count) in zip(rows, expected):
        need(row['stage'] == stage and row['mode'] == mode, 'Storage branch identity differs')
        need(row['actual_errno'] == (13 if mode == 'EACCES' else 28)
             and row['actual_errno_name'] == mode, 'Actual Ubuntu errno differs')
        before, after = snapshot(row['before']), snapshot(row['after'])
        checkpoint = row['expected_unchanged_checkpoint']
        snapshot(checkpoint)
        need(row['after']['raw_utf8'] == checkpoint['raw_utf8'], 'Failure changed retained checkpoint')
        need(row['raw_sends_before'] == before_count and row['raw_sends_after'] == after_count,
             'Failure sent/resubmitted unexpectedly')
        if stage.startswith('accepted_hash_'):
            known = row['accepted_boundary']
            need(known['durable_hashless']['raw_utf8'] == checkpoint['raw_utf8']
                 and after['pending']['hash'] is None
                 and row['memory_after']['pending']['hash'] == known['hash'],
                 'Accepted boundary did not retain exact durable hashless intent')
            fault = known['fault']
        else:
            need(row['before']['raw_utf8'] == checkpoint['raw_utf8'], 'Preexisting checkpoint changed')
            fault = row['fault']
        need(fault['mode'] == mode, 'OS fault type differs')
        if mode == 'EACCES':
            need(fault['parent_mode'] == '0o500', 'Permission fault did not affect parent directory')
        else:
            need(fault['filler_errno'] == 28 and fault['filler_errno_name'] == 'ENOSPC'
                 and 0 < fault['filler_bytes'] <= 1048576 and fault['free_after'] == 0,
                 'Bounded actual tmpfs-full evidence differs')
        if stage.startswith('receipt_'):
            need(row['memory_after'] == before and before == after,
                 'Receipt failure did not retain old disk and restore old memory')
        if stage.startswith('intent_'):
            need(before['pending'] is None and after['pending'] is None,
                 'Never-broadcast intent changed durable checkpoint')
    return {'branches': len(rows), 'errno_EACCES_count': 3, 'errno_ENOSPC_count': 3,
            'unchanged_checkpoints': True, 'unexpected_resends': 0}


def transaction_review(inputs):
    rows = inputs.json('TRANSACTIONS.json')
    need(len(rows) == 2, 'Expected two distinct paid transactions')
    previous = snapshot(inputs.json('INITIAL_JOURNAL.json'))
    need(previous['pending'] is None and previous['next_nonce'] == 0, 'Initial sender checkpoint differs')
    totals = dict(previous['spent'])
    hashes, costs = [], []
    for nonce, row in enumerate(rows):
        accepted = inputs.json('ACCEPTED_' + str(nonce) + '.json')
        known = row['known_at_acceptance']
        need(accepted['hash'] == known['hash'] == row['accepted_hash'], 'Accepted hash evidence differs')
        snapshot(accepted['durable_hashless'])
        need(accepted['durable_hashless']['raw_utf8'] == known['durable_hashless']['raw_utf8'],
             'Accepted durable boundary differs')
        original = row['original_pending']
        published = snapshot(row['published_hash'])
        recovered = snapshot(row['recovered'])
        need(published['pending'] == original and original['hash'] == row['accepted_hash']
             and original['nonce'] == nonce and original['value'] == 0, 'Published original intent differs')
        tx, receipt, header, head = (row[key] for key in
                                    ('transaction_without_signature', 'receipt', 'receipt_header', 'confirmed_head'))
        need(not set(tx) & {'r', 's', 'v', 'yParity'}, 'Raw signature must not be exported')
        need(tx['hash'].lower() == receipt['transactionHash'].lower() == row['accepted_hash'],
             'Transaction/receipt hash differs')
        need(tx['from'].lower() == receipt['from'].lower() == previous['sender']
             and tx['to'].lower() == receipt['to'].lower() == original['to']
             and tx['input'].lower() == original['data'].lower(), 'Signed sender/target/call differs')
        need(quantity(tx['chainId']) == 4663 and quantity(tx['nonce']) == nonce
             and quantity(tx['value']) == 0 and quantity(receipt['status']) == 1, 'Chain/nonce/value/status differs')
        block, stamp = quantity(receipt['blockNumber']), quantity(header['timestamp'])
        need(quantity(tx['blockNumber']) == quantity(header['number']) == block
             and tx['blockHash'].lower() == receipt['blockHash'].lower() == header['hash'].lower()
             and quantity(tx['transactionIndex']) == quantity(receipt['transactionIndex']),
             'Canonical inclusion identity differs')
        need(quantity(head['number']) - block + 1 >= 12
             and quantity(head['timestamp']) >= stamp and row['accepted_hash'] in header['transactions'],
             'Canonical confirmation depth differs')
        review = original['fee_review']
        need(review['schema'] == 1 and review['receipt_fee_policy'] == 'included'
             and review['l1_fee_allowance_wei'] == 0, 'Original captured fee policy differs')
        tx_type = quantity(tx.get('type', '0x0'))
        if tx_type == 2:
            cap, tip, base = quantity(tx['maxFeePerGas']), quantity(tx['maxPriorityFeePerGas']), quantity(header['baseFeePerGas'])
            need(cap >= base and cap >= tip, 'Invalid signed type2 fee envelope')
            price = min(cap, base + tip)
        else:
            need(tx_type in (0, 1), 'Unsupported signed transaction type')
            price = cap = quantity(tx['gasPrice'])
        gas, allowance = quantity(receipt['gasUsed']), quantity(tx['gas'])
        need(0 < gas <= allowance == review['gas_limit'] <= 24000000
             and cap <= review['max_fee_per_gas'] <= 5000000000,
             'Captured gas/fee bounds differ')
        need(review['maximum_cost_wei'] == review['gas_limit'] * review['max_fee_per_gas'] <= 10**16,
             'Captured maximum cost differs')
        paid = gas * price
        need(row['paid_wei'] == paid and row['canonical_execution_price_wei'] == price
             and paid <= review['maximum_cost_wei'], 'Canonical paid cost differs')
        day = dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date().isoformat()
        totals[day] = totals.get(day, 0) + paid
        need(recovered['spent'] == totals and recovered['pending'] is None
             and recovered['next_nonce'] == nonce + 1 and row['raw_sends'] == nonce + 1,
             'Recovery duplicated cost, lost nonce or resent')
        need(recovered['receipt_anchor'] == {'number': block, 'hash': header['hash'], 'timestamp': stamp, 'nonce': nonce},
             'Canonical recovered anchor differs')
        observation = recovered['last_fee_observation']
        need(observation['transaction'] == row['accepted_hash'] and observation['cost_wei'] == paid
             and observation['gas_used'] == gas and observation['execution_price_wei'] == price,
             'Recovered fee observation differs')
        for key in ('chain_id', 'sender', 'contracts', 'accounting_model', 'accounting_version'):
            need(recovered[key] == previous[key], 'Recovery relabelled identity')
        hashes.append(row['accepted_hash']); costs.append(paid); previous = recovered
    need(len(set(hashes)) == 2, 'Original transaction hashes are not distinct')
    final = inputs.json('FINAL_JOURNAL.json')
    stop = inputs.json('JOURNAL_AT_STOP.json')
    need(snapshot(final) == previous and snapshot(stop) == previous
         and final['raw_utf8'] == stop['raw_utf8'] == rows[-1]['recovered']['raw_utf8'],
         'Final exact raw checkpoint differs from settled recovery')
    return {'actual_paid_transactions': 2, 'hashes': hashes, 'paid_costs_wei': costs,
            'final_next_nonce': 2, 'daily_costs_wei': totals, 'raw_resends': 0,
            'onchain_final_nonce_getters': 'source assertions only; separate read vectors not supplied'}


def rights_and_result_review(inputs):
    before, after = inputs.json('BEFORE.json'), inputs.json('AFTER.json')
    need(before == after and len(before['rights']) == 2, 'Captured NFT/LP/reserve projections changed')
    result = inputs.json('RESULT.json')
    need(result['success'] is True and result['failures'] == 6
         and result['actual_paid_transactions'] == 2 and result['raw_resends'] == 0,
         'Worker aggregate differs')
    need(result['raw_attempts'] == result['raw_forwarded'] == 2
         and 0 < result['shared_RPC_requests'] <= 6000 and result['real_seconds_remaining'] > 0,
         'Bounded worker submission/resource counts differ')
    need(result['direct_stock_calls_not_normal_daemon'] is True
         and result['new_seals'] == result['public_transactions'] == 0
         and result['old_passed_tests_or_worker_journeys_run'] == 0, 'Execution scope differs')
    need(result['cleanup']['stopped'] is True and result['cleanup']['overflow'] is False,
         'Owned model cleanup differs')
    return {'projection_equality': True, 'NFT_count': 2, 'RPC_requests': result['shared_RPC_requests'],
            'direct_stock_calls_not_normal_daemon': True, 'financial_allocation_requalified': False}


def reported_hash_review(inputs):
    parts = inputs.json('EVENTS.json')
    need(type(parts) is list and all(type(part) is str for part in parts), 'Stock event capture shape differs')
    raw = ''.join(parts)
    need(len(raw.encode('utf8')) <= 65536, 'Combined stock event capture exceeds bound')
    events = [decode(line) for line in raw.splitlines() if line]
    reported = [event for event in events if event.get('event') == 'submission_requires_reconciliation']
    transactions = inputs.json('TRANSACTIONS.json')
    need(len(reported) == len(transactions) == 2, 'Expected two hash-persistence failure diagnostics')
    for index, (event, tx) in enumerate(zip(reported, transactions)):
        need(event['reported_transaction'] == tx['accepted_hash']
             and event['os_errno'] == ('EACCES' if index == 0 else 'ENOSPC'),
             'Reported candidate or fixed OS errno differs from actual boundary')
        need(event['error_type'] == ('PermissionError' if index == 0 else 'OSError')
             and type(event['error_site']) is str and 'transaction' not in event,
             'Failure diagnostic classification differs')
        need(not any(row.get('event') == 'submitted' and row.get('transaction') == tx['accepted_hash']
                     for row in events), 'Failed hash persistence was labelled submitted')
        confirmed = [row for row in events if row.get('event') == 'confirmed'
                     and row.get('transaction') == tx['accepted_hash']]
        need(len(confirmed) == 1 and int(confirmed[0]['cost_wei']) == tx['paid_wei'],
             'Stock recovery log repeated or changed canonical cost')
    return {'validated_reported_candidates': 2, 'raw_signer_output_exported': False,
            'candidate_log_is_acceptance_guarantee': False, 'confirmed_once_per_original_hash': True}


def native_review(path, stopped):
    if path is None:
        raise Missing('Native ' + ('stop' if stopped else 'start') + ' record not supplied')
    need(path.stat().st_size <= MAX_FILE, 'Native readback exceeds bound')
    record = decode(path.read_bytes())
    if stopped:
        values = record['after']['properties']
        need(values['ActiveState'] in ('inactive', 'failed') and int(values['MainPID']) == 0
             and record['after']['owned_cgroup_pids'] == []
             and record['only_owned_unit_stopped'] is True, 'Final owned cgroup is not stopped')
        return {'native_stopped': True, 'empty_owned_cgroup': True}
    values = record['properties']
    need(values['PrivateMounts'] == values['PrivateNetwork'] == 'yes'
         and values['User'] == 'nobody' and values['Group'] == 'nogroup'
         and values['NoNewPrivileges'] == 'yes', 'Loaded isolated unprivileged service differs')
    need('/runtime/storage' in values['TemporaryFileSystem'], 'Loaded bounded tmpfs absent')
    return {'loaded_private_mounts': True, 'loaded_private_network': True, 'native_user': 'nobody'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--build-dir', required=True, type=Path)
    parser.add_argument('--start', type=Path)
    parser.add_argument('--stop', type=Path)
    args = parser.parse_args()
    inputs, checks = Inputs(args.evidence), {}
    tasks = [('frozen_source_and_limits', lambda: source_review(inputs, args.build_dir)),
             ('actual_bounded_tmpfs', lambda: filesystem_review(inputs)),
             ('six_actual_OS_failure_boundaries', lambda: branch_review(inputs)),
             ('canonical_paid_recovery_once', lambda: transaction_review(inputs)),
             ('reported_hash_storage_failure_diagnostics', lambda: reported_hash_review(inputs)),
             ('captured_NFT_LP_projections_and_scope', lambda: rights_and_result_review(inputs)),
             ('loaded_private_native_unit', lambda: native_review(args.start, False)),
             ('final_native_cleanup', lambda: native_review(args.stop, True))]
    for name, run in tasks:
        try:
            checks[name] = {'status': 'passed', 'proof': run()}
        except Missing as exc:
            checks[name] = {'status': 'missing', 'reason': str(exc)}
        except (Refused, ValueError, TypeError, KeyError, OSError, tarfile.TarError) as exc:
            checks[name] = {'status': 'failed', 'reason': str(exc), 'error_class': type(exc).__name__}
    values = [row['status'] for row in checks.values()]
    status = 'failed' if 'failed' in values else 'incomplete' if 'missing' in values else 'passed'
    print(json.dumps({'schema': 1, 'stage': 'storage_saved_vectors_independent_review',
        'status': status, 'checks': checks, 'input_files': inputs.used,
        'runtime_actions': 0, 'network_calls': 0, 'old_test_bodies_run': 0,
        'production_approved': False, 'limitations': [
            'Saved vectors/source pins do not authenticate a hostile host or provider.',
            'Genuine tmpfs ENOSPC and Unix directory EACCES do not prove physical-power-loss, ext4 or directory-fsync-failure durability.',
            'These direct stock submit/resolve/poll calls are not a new normal-daemon/supervisor proof.',
            'Zero-fee harvests compare selected NFT/LP/reserve projections; economic allocation and arbitrary faults are not requalified.',
            'Final on-chain nonce values are executed-source assertions, without separate getter vectors.',
            'Restart storms, additional transports/storage failures, off-host fencing/restore, alerts and soak remain open.',
            'Original service and heartbeat preservation needs its separate host comparison.']}, indent=2, sort_keys=True))
    return 1 if status == 'failed' else 2 if status == 'incomplete' else 0


if __name__ == '__main__':
    raise SystemExit(main())
