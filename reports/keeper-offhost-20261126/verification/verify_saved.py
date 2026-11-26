"""Reconcile c823 saved evidence only; no product imports, subprocesses or network.

Optional --private-campaign rehashes only the exact five synthetic package files,
desktop proof and fixed transport captures. It never writes private data into the
report. Server restore bytes are supported by the source-pinned native witness
and its readback records, not a new independent remote filesystem inspection.
"""
import argparse
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import time

CAP = 16 * 1024 * 1024
DEADLINE_SECONDS = 60
OUTER = 'a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED = '911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
TRUST = '9bec125bedd73b6f80cb3f316a7822aa09aeb9198927ca8d901c476f3798c371'
POLICY = '7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
CONFIG = '1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
SOURCE = 'c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
PROOF = '75d2189e6e5ecc177d6836a8dc01fb3b598a3a60f187f3a727bdbad751d2b878'
CONTROLLER = 'd6e37f02c1e35ba8d61dce2debd4cc0bd917a26c5d95f9480b6a8a5486d24d35'
WORKER = '5ec39493c3f79e22ca8b42eb67833b35556fab68612172434ed9d5e01b93fa9e'
HOST = '281d9ded160451bf733e79c14b94c93a0ce0e18329bebf587fa316031c5a7774'
DESKTOP = '6186169eb96941b81eea71b608a0101490f003015b48faebe7852de1e6037f14'
TRANSPORT = 'a7f7f91863833bca9081b0ad6af833a1cf5147e65f1c2cfe7e058449f1bddc45'
CREATED = 1795723324
GENERATION = 'snapshot-a28822b4f4201a59add47c277572290e'
NAMES = ('manifest.json', 'selection.json', 'alert-state.json',
         'selected/manifest.json', 'selected/journal.json')
OLD = '/opt/popl-keeper-sidecar-recovery-20261126-c821'
NEW = '/opt/popl-keeper-offhost-20261126-c823'
UNIT = 'popl-keeper-offhost-20261126-c823.service'
OLD_UNITS = {'popl-keeper-sidecar-recovery-20261126-c821' + suffix + '.service'
             for suffix in ('', '-checks', '-source', '-target')}


def need(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def decode(raw):
    def pairs(rows):
        out = {}
        for key, value in rows:
            need(key not in out, 'duplicate_key')
            out[key] = value
        return out
    def reject(_):
        raise ValueError('nonfinite_constant')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    need(type(value) is dict, 'object_required')
    return value


class Reader:
    def __init__(self):
        self.end = time.monotonic() + DEADLINE_SECONDS
        self.total = 0
        self.pins = {}

    def read(self, path, label, cap=65536, pin=None):
        need(time.monotonic() < self.end, 'saved_review_deadline')
        before = path.lstat()
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
             0 <= before.st_size <= cap and not path.is_symlink() and
             not getattr(before, 'st_file_attributes', 0) & 0x400, 'saved_file_metadata')
        for parent in path.parents:
            record = parent.lstat()
            need(not stat.S_ISLNK(record.st_mode) and
                 not getattr(record, 'st_file_attributes', 0) & 0x400, 'parent_alias')
        flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags)
        key = lambda row: (row.st_dev, row.st_ino, row.st_mode, row.st_nlink,
                           row.st_size, row.st_mtime_ns)
        with os.fdopen(fd, 'rb') as stream:
            raw = stream.read(cap + 1)
            need(key(before) == key(os.fstat(stream.fileno())) == key(path.lstat())
                 and len(raw) == before.st_size <= cap, 'saved_file_changed')
        self.total += len(raw)
        need(self.total <= CAP and time.monotonic() < self.end, 'saved_resource_bound')
        actual = sha(raw)
        need(pin is None or pin == actual, 'saved_pin_mismatch:' + label)
        self.pins[label] = {'bytes': len(raw), 'sha256': actual}
        return raw

    def obj(self, path, label, **kwargs):
        return decode(self.read(path, label, **kwargs))


def inventory(folder, expected, end):
    found = set()
    with os.scandir(folder) as entries:
        for entry in entries:
            need(time.monotonic() < end and len(found) < len(expected) and
                 entry.name in expected and entry.name not in found, 'desktop_exact_inventory')
            found.add(entry.name)
    need(found == expected, 'desktop_exact_inventory')


def verify(repo, report, private):
    r = Reader()
    obj = lambda relative: r.obj(report / relative, relative)
    preparation = report / 'preparation'
    for path, pin in (('c823/worker.py', WORKER), ('c823/remote_capsule.py', CONTROLLER),
                      ('c823/host_control.py', HOST), ('desktop/desktop_verify.py', DESKTOP)):
        raw = r.read(preparation / path, 'preparation/' + path, pin=pin)
        ast.parse(raw)
    original = repo / 'reports/keeper-sidecar-recovery-20261126'
    trust = r.obj(original / 'evidence/c821/fetch-6/SOURCE_RESULT.json',
                  'published_c821_trust', pin=TRUST)
    source = r.obj(original / 'preparation/c821/SOURCE_MANIFEST.json',
                   'published_c821_source_manifest', pin=SOURCE)
    proof = obj('evidence/desktop/DESKTOP_PROOF.json')
    need(r.pins['evidence/desktop/DESKTOP_PROOF.json']['sha256'] == PROOF, 'desktop_proof_pin')
    need(trust['success'] is True and trust['bundle_manifest_pin'] == OUTER and
         trust['policy_pin'] == POLICY and trust['config_pin']['sha256'] == CONFIG,
         'original_trust_identity')
    provenance = obj('verification/TRUST_PROVENANCE.json')
    need(provenance['sha256'] == TRUST and provenance['derived_from_incoming_packet'] is False
         and provenance['source_commit'] == 'a1b1a5ab4f3f334305b34a4761952d5c215a3a96',
         'independent_trust_provenance')
    expected = {'manifest.json': {'bytes': 5261, 'sha256': OUTER}}
    original_paths = {'selection.json': 'scheduler/selected.json',
        'alert-state.json': 'alerts/state.json',
        'selected/manifest.json': 'backups/' + GENERATION + '/manifest.json',
        'selected/journal.json': 'backups/' + GENERATION + '/journal.json'}
    expected.update({name: trust['source_files'][path] for name, path in original_paths.items()})
    need(set(expected) == set(NAMES) and expected['selected/manifest.json']['sha256'] == NESTED,
         'expected_five')
    metadata = obj('evidence/c823/export-003/EXPORT_METADATA.json')
    installed = obj('evidence/c823/install/SANITIZED_RESULT.json')
    install = obj('evidence/c823/fetch-install/INSTALL.json')
    result = obj('evidence/c823/fetch-result/RESULT.json')
    final = obj('evidence/c823/fetch-final/FINAL.json')
    status = obj('evidence/c823/status/SANITIZED_RESULT.json')
    for files in (metadata['files'], proof['files'], installed['input_files'], install['input_files']):
        need(files == expected, 'transport_file_map')
    need(metadata['original_fenced_before_and_after'] is True and
         metadata['original_files_unchanged'] is True and
         metadata['policy_configuration_and_signer_material_exported'] is False and
         metadata['source_trust_report_sha256'] == TRUST, 'export_scope')
    need(installed['desktop_proof_sha256'] == install['desktop_proof_sha256'] == PROOF and
         installed['same_desktop_bytes_imported'] is True, 'desktop_return_binding')
    for key in ('unsigned', 'ok'):
        need(proof[key] is True, 'desktop_success')
    for key in ('readiness_approved', 'production_approved', 'posix_core_verified',
                'canonical_state_verified', 'current_operating_freshness_approved'):
        need(proof[key] is False, 'desktop_nonadoption')
    need(proof['policy_sha256'] == POLICY and proof['configuration_sha256'] == CONFIG
         and proof['outer_manifest_sha256'] == OUTER and proof['nested_manifest_sha256'] == NESTED
         and proof['operating_max_age_seconds'] == 900 and
         proof['recovery_review_max_age_seconds'] == 86400, 'age_policy_not_rewritten')
    need(result['success'] is True and result['unsigned'] is True and
         result['all_adoption_flags_false'] is True and result['restores_are_review_only'] is True,
         'native_success_scope')
    for key in ('readiness_approved', 'production_approved', 'asof_clock_override',
                'old_policy_changed', 'operational_freshness_approved',
                'source_services_started', 'raw_records_rewritten'):
        need(result[key] is False, 'native_nonadoption:' + key)
    need(all(result[key] == 0 for key in ('RPC_calls', 'public_transactions', 'test_bodies_run')),
         'zero_actions')
    need(result['new_review_max_age_seconds'] == 86400 and
         result['operating_policy_max_backup_age_seconds'] == 900 and
         result['original_capture_times'] == {'outer': CREATED, 'nested': CREATED}
         and all(900 < age <= 86400 for age in result['capture_ages_seconds'].values())
         and result['outside_original_operating_age'] is True, 'historical_actual_wall_age')
    need(result['pending_summary'] == trust['observer_before']['pending'] and
         result['sequence'] == trust['observer_before']['sequence'] and
         result['outbox_ids'] == [e['event_id'] for e in trust['observer_before']['outbox']],
         'observer_continuity')
    need(proof['preserved_state']['pending_first_seen'] == result['pending_summary']['first_seen']
         and proof['preserved_state']['pending_intent_sha256'] == result['pending_summary']['intent_sha256']
         and proof['preserved_state']['event_ids'] == result['outbox_ids'], 'desktop_observer_continuity')
    restored_expected = {'keeper-state.json': expected['selected/journal.json'],
        'scheduler/selected.json': expected['selection.json'], 'alerts/state.json': expected['alert-state.json'],
        'selected/manifest.json': expected['selected/manifest.json'],
        'selected/journal.json': expected['selected/journal.json']}
    need(result['restored_files'] == restored_expected, 'native_readback_map')
    calls = result['calls']
    task_names = [('keeper-recovery.py', 'verify'), ('keeper-recovery.py', 'restore'),
                  ('keeper-sidecar-recovery.py', 'verify'), ('keeper-sidecar-recovery.py', 'restore')]
    need(len(calls) == 4, 'four_existing_calls')
    for call, (script, action) in zip(calls, task_names):
        args = call['argv']
        pin = NESTED if script == 'keeper-recovery.py' else OUTER
        need(call['script'] == script and call['action'] == action and call['returncode'] == 0 and
             args[:4] == ['/usr/bin/python3', '-B', OLD + '/source/scripts/' + script, action]
             and args[args.index('--max-age-seconds') + 1] == '86400'
             and args[args.index('--minimum-created-at') + 1] == str(CREATED)
             and args[args.index('--manifest-sha256') + 1] == pin
             and 0 < call['stdout_bytes'] <= 65536 and 0 <= call['elapsed_seconds'] < 75,
             'native_call_inputs')
        expected_flags = ['--config', OLD + '/runtime/keeper-config.json'] if script == 'keeper-recovery.py' else [
            '--policy', OLD + '/runtime/policy.json', '--policy-sha256', POLICY]
        expected_flags += ['--bundle', NEW + '/runtime/imported' + ('/selected' if script == 'keeper-recovery.py' else ''),
            '--manifest-sha256', pin, '--max-age-seconds', '86400', '--minimum-created-at', str(CREATED)]
        if action == 'restore':
            expected_flags += ['--output', NEW + '/runtime/' + ('keeper-review' if script == 'keeper-recovery.py' else 'sidecar-review')]
        need(args[4:] == expected_flags, 'exact_original_cli_argv')
    need(calls[0]['parsed']['manifest_or_plan_sha256'] == NESTED and
         calls[1]['parsed']['manifest_or_plan_sha256'] == result['native_restore_plan_sha256'] and
         calls[2]['parsed']['manifest_sha256'] == calls[3]['parsed']['manifest_sha256'] == OUTER and
         calls[3]['parsed']['restore_plan_sha256'] == result['sidecar_restore_plan_sha256'] ==
         trust['restore_plan_pin']['sha256'], 'four_output_pin_bindings')
    oldlocks = result['original_lock_metadata_unchanged']
    newlocks = result['new_empty_lock_inode_pairs']
    need(len(oldlocks) == len(newlocks) == 2 and len({tuple(v) for v in newlocks}) == 2 and
         {tuple(v) for v in newlocks}.isdisjoint({tuple(v[:2]) for v in oldlocks}) and
         {tuple(v[:2]) for v in oldlocks} == {tuple(v) for v in trust['source_locks'].values()}
         and all(v[2:6] == [stat.S_IFREG | 0o600, 65534, 1, 0] for v in oldlocks)
         and result['new_locks_disjoint_from_originals'] is True, 'old_new_lock_separation')
    need(len(result['signer_masks_distinct_unreadable']) == 2 and len({tuple(v)
         for v in result['signer_masks_distinct_unreadable']}) == 2, 'distinct_masks')
    snapshots = [install['original_before'], install['original_after'], final['original_after']]
    need(snapshots[0] == snapshots[1] == snapshots[2], 'source_references_package_and_fence_unchanged')
    snapshot = snapshots[0]
    need(snapshot['package_files'] == expected and snapshot['source_manifest_sha256'] == SOURCE,
         'original_package_source')
    need(sha(canonical(snapshot) + b'\n') == metadata['original_reference_snapshot_sha256'],
         'export_original_snapshot_binding')
    need(set(snapshot['fenced_units']) == OLD_UNITS and all(p['MainPID'] == '0' and
         p['ControlGroup'] == '' and p['ActiveState'] == 'inactive'
         for p in snapshot['fenced_units'].values()), 'four_original_groups_empty')
    refs = snapshot['protected_reference_hashes']
    need(refs == {'policy.json': POLICY, 'keeper-config.json': CONFIG,
        'working/runtime/journal.json': expected['selected/journal.json']['sha256'],
        'schedule/selected.json': expected['selection.json']['sha256'],
        'alerts/state.json': expected['alert-state.json']['sha256']}, 'original_reference_identity')
    need(len(source['source_files']) == len(snapshot['source_files_sha256']) == 41,
         'source_closure_41')
    for name, row in source['source_files'].items():
        need(snapshot['source_files_sha256'][name] == row['sha256'], 'source_map_readback')
        raw = r.read(repo / name, 'source/' + name, cap=1024 * 1024, pin=row['sha256'])
        need(len(raw) == row['bytes'], 'source_length')
    status_props = status['properties']
    need(status['actual_execution_started'] is True and status['result_present'] is True
         and status_props['Id'] == UNIT and status_props['Result'] == 'success'
         and status_props['ExecMainStatus'] == '0' and status_props['User'] == 'nobody'
         and status_props['PrivateNetwork'] == 'yes' and status_props['RestrictAddressFamilies'] == 'AF_UNIX'
         and status_props['Restart'] == 'no' and status_props['KillMode'] == 'control-group'
         and status_props['TimeoutStartUSec'] == '3min' and status_props['TimeoutStopUSec'] == '2s',
         'actual_unit_bounds')
    need(final['new_group_empty'] is True and final['old_four_groups_fenced'] is True
         and final['original_unchanged'] is True and final['after_stop']['MainPID'] == '0'
         and final['after_stop']['ControlGroup'] == '' and
         final['after_stop']['ActiveState'] == 'inactive', 'owned_stop')
    actions = ('export-003', 'install', 'start', 'status', 'stop', 'fetch-result', 'fetch-final', 'fetch-install')
    receipts = {}
    for name in actions:
        receipt = obj('evidence/c823/' + name + '/EXECUTION.json')
        need(receipt['exit_code'] == 0 and receipt['capture_reason'] is None and receipt['capture_errors'] == []
             and receipt['controller_sha256'] == CONTROLLER and receipt['transport_sha256'] == TRANSPORT
             and receipt['combined_output_limit'] == 65536 and receipt['stderr_bytes'] == 0
             and receipt['stdout_bytes'] <= 65536 and receipt['production_signer_material_read_or_exported'] is False,
             'bounded_transport_receipt')
        receipts[name] = receipt
    attempts = obj('review/ORIGINAL_ATTEMPTS.json')
    failed = obj('evidence/c823/export/EXECUTION.json')
    need(failed['exit_code'] == 255 and failed['stdout_bytes'] == 0 and
         len(attempts['attempts']) == 3 and attempts['test_bodies_run'] == 0 and
         attempts['attempts'][2]['proof_published'] is False, 'original_failures_retained')
    host = obj('verification/HOST_PRESERVATION.json')
    first_host = obj('verification/ORIGINAL_HOST_COMPARISON_NONPASS.json')
    before = obj('verification/before-018-CAPTURE.json')
    first_final = obj('verification/final-018-CAPTURE.json')
    settled = obj('verification/final-018-settled-CAPTURE.json')
    need(host['success'] is True and host['non_ambient_difference_count'] == 0
         and host['ignored_observer_invocation_count'] == 1 and host['existing_units_checked'] == 5
         and host['before_snapshot_sha256'] == before['snapshot_sha256']
         and host['final_snapshot_sha256'] == settled['snapshot_sha256']
         and first_host['success'] is False and first_host['non_ambient_difference_count'] == 5
         and first_host['final_snapshot_sha256'] == first_final['snapshot_sha256']
         and settled['snapshot_sha256'] != first_final['snapshot_sha256']
         and all(v['service_actions'] == 0 and v['read_only'] is True and v['snapshot_complete'] is True
                 for v in (before, first_final, settled)), 'separate_host_comparisons')
    private_summary = {'performed': False}
    if private is not None:
        package = private / 'export-003/package'
        inventory(package, {'manifest.json', 'selection.json', 'alert-state.json', 'selected'}, r.end)
        inventory(package / 'selected', {'manifest.json', 'journal.json'}, r.end)
        raw = {name: r.read(package / name, 'private/package/' + name, pin=expected[name]['sha256']) for name in NAMES}
        need({k: {'bytes': len(v), 'sha256': sha(v)} for k, v in raw.items()} == expected, 'private_five_hashes')
        need(r.read(private / 'proof/DESKTOP_PROOF-002.json', 'private/desktop-proof', pin=PROOF) ==
             r.read(report / 'evidence/desktop/DESKTOP_PROOF.json', 'proof_duplicate'), 'private_proof_bytes')
        records = {name: decode(data) for name, data in raw.items()}
        outer, selected, observer, nested, journal = [records[name] for name in NAMES]
        need(selected == trust['selected'] and observer == trust['observer_before'] and
             nested['created_at'] == selected['created_at'] == outer['created_at'] == CREATED,
             'raw_original_state')
        need(len(outer['source_files_sha256']) == 19 and len(nested['source_files_sha256']) == 13,
             'source19_daemon13')
        for mapping in (outer['source_files_sha256'], outer['producer_files_sha256'],
                        nested['source_files_sha256'], nested['producer_files_sha256']):
            need(all(snapshot['source_files_sha256'][k] == v for k, v in mapping.items()), 'raw_source_identity')
        need(proof['preserved_state'] == {'economic_identity_sha256': sha(canonical(outer['identity'])),
            'next_nonce': journal['next_nonce'], 'spent_sha256': sha(canonical(journal['spent'])),
            'pending_sha256': sha(canonical(journal['pending'])),
            'receipt_anchor_sha256': sha(canonical(journal['receipt_anchor'])),
            'observer_sequence': observer['sequence'], 'pending_first_seen': observer['pending']['first_seen'],
            'pending_intent_sha256': observer['pending']['intent_sha256'],
            'event_ids': [v['event_id'] for v in observer['outbox']]}, 'independent_raw_nonce_cost_pending_clock_digest')
        for event in observer['outbox']:
            need(event['event_id'] == sha(canonical([1, event['scope_sha256'], event['sequence'],
                 event['type'], event['reason_code']])), 'event_id_formula')
        for name in actions:
            receipt = receipts[name]
            stdout = r.read(private / name / 'stdout.raw', 'private/' + name + '/stdout', pin=receipt['stdout.raw_sha256'])
            stderr = r.read(private / name / 'stderr.raw', 'private/' + name + '/stderr', pin=receipt['stderr.raw_sha256'])
            need(len(stdout) == receipt['stdout_bytes'] and stderr == b'', 'actual_transport_bounds')
            response = decode(stdout)
            if name == 'export-003':
                need(response['kind'] == 'popl-keeper-offhost-export' and set(response['files']) == set(NAMES), 'raw_export_shape')
                for member in NAMES:
                    need(base64.b64decode(response['files'][member]['raw_base64'], validate=True) == raw[member],
                         'actual_desktop_export_bytes')
            elif name.startswith('fetch-'):
                target = {'fetch-result': 'RESULT.json', 'fetch-final': 'FINAL.json', 'fetch-install': 'INSTALL.json'}[name]
                fetched = base64.b64decode(response['base64'], validate=True)
                public = r.read(report / 'evidence/c823' / name / target, 'decoded/' + target)
                need(response['name'] == target and len(fetched) == response['bytes'] <= 32768
                     and sha(fetched) == response['sha256'] and fetched == public, 'actual_fetch_payload')
            else:
                need(response == obj('evidence/c823/' + name + '/SANITIZED_RESULT.json'), 'actual_transport_sanitized_result')
        private_summary = {'performed': True, 'file_count': 5, 'package_total_bytes': sum(map(len, raw.values())),
            'proof_rehashed': True, 'all_eight_transport_captures_rehashed': True,
            'nonce_cost_pending_anchor_digests_recomputed': True, 'event_ids_recomputed': True,
            'raw_data_written_to_report': False}
    return {'schema': 1, 'kind': 'independent-saved-c823-reconciliation', 'success': True,
        'scope': 'historical-synthetic-c821-offhost-possession-return-and-native-review-only-restore',
        'full_offhost_failover_qualified': False, 'release_approved': False, 'production_approved': False,
        'application_imports': 0, 'test_bodies': 0, 'server_calls': 0, 'network_calls': 0,
        'verification_input_bytes': r.total, 'input_pins': r.pins, 'native_original_CLI_calls': 4,
        'worker_elapsed_seconds': result['elapsed_seconds'], 'source_files_read_back': 41,
        'daemon_source_count': 13, 'scheduler_source_count': 19,
        'caller_review_age_seconds': 86400, 'unchanged_operating_age_seconds': 900,
        'actual_native_capture_ages_seconds': result['capture_ages_seconds'],
        'private_reconciliation': private_summary,
        'preserved_state': proof['preserved_state'], 'all_restore_adoption_flags_remain_false': True,
        'new_empty_lock_inodes_differ_from_originals': True,
        'existing_host_state': {'final_non_ambient_differences': 0, 'disclosed_observer_invocations': 1,
            'original_mid_observer_NONPASS_differences': 5, 'original_comparison_retained': True,
            'raw_host_vectors_redecoded_by_this_verifier': False},
        'limitations': ['Existing synthetic package, no new capture, signing, chain query or transaction',
            'Server restore byte equality/new empty lock metadata come from the pinned native witness and its saved readbacks',
            'Raw desktop five files and saved SSH frames can be independently rehashed only when private evidence is supplied',
            'Host preservation reconciles sanitized original and settled comparisons; it does not re-inspect a live host',
            'No second Linux host, host-loss rehearsal, writer/key fencing restoration, physical durability or adoption',
            'Historical caller recovery age is not an operating backup freshness-policy increase']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--report', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--private-campaign', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.repo.resolve(), args.report.resolve(), args.private_campaign)
    output = args.output or args.report / 'verification/OFFHOST_VERIFICATION.json'
    output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf8')
    print(json.dumps({'success': True, 'native_CLI_calls': 4,
        'private_reconciliation': result['private_reconciliation']['performed'],
        'output_sha256': sha(output.read_bytes())}, sort_keys=True))


if __name__ == '__main__':
    main()
