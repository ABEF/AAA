"""Report-only reconciliation of saved c820/c821 evidence; no application imports.

This reads the curated report and the NEW test source as AST data. It never runs
test bodies, application modules, processes, network calls or server actions.
Physical remote payload bytes were not fetched: their recorded hashes/lengths
are reconciled with the fixed native harness's successful equality assertions.
"""
from pathlib import Path
import argparse
import ast
import base64
import hashlib
import json
import re
import stat
import zlib


MAX_JSON = 65536
MAX_PACKED = 262144
EMPTY = hashlib.sha256(b'').hexdigest()
INPUTS = {}
FLAGS = ('readiness_approved', 'old_sidecars_fenced', 'canonical_state_verified',
    'signer_material_included', 'policy_or_configuration_installed',
    'services_restarted', 'runtime_paths_mapped', 'lock_ownership_restored',
    'selected_generation_freshness_approved')
STAGES = ['new_focused_recovery_methods', 'actual_unsigned_capture_verify_restore',
    'mapped_target_resumes_same_outbox_and_pending_clock', 'final_fenced_preservation']


def need(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value, *, pretty=False, newline=True):
    options = {'indent': 2} if pretty else {'separators': (',', ':')}
    return (json.dumps(value, sort_keys=True, allow_nan=False, **options) +
        ('\n' if newline else '')).encode('utf8')


def pairs(rows):
    value = {}
    for key, item in rows:
        need(key not in value, 'duplicate_json_key')
        value[key] = item
    return value


def decoded(raw):
    return json.loads(raw.decode('utf8', 'strict'), object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('json_constant')))


def read(path, limit=MAX_JSON):
    item = path.lstat()
    need(stat.S_ISREG(item.st_mode) and item.st_nlink == 1 and item.st_size <= limit,
        'saved_file_kind_or_size')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) == item.st_size and len(raw) <= limit, 'saved_file_size_changed')
    INPUTS[str(path)] = {'bytes': len(raw), 'sha256': sha(raw)}
    return raw


def load(path):
    return decoded(read(path))


def packed(value, *, fields=('decoded_bytes', 'decoded_sha256', 'gzip_base64'), maximum=MAX_PACKED):
    count, pin, encoded = (value[key] for key in fields)
    need(type(count) is int and 0 <= count <= maximum and type(encoded) is str and
        len(encoded) <= MAX_JSON and re.fullmatch('[0-9a-f]{64}', pin), 'packed_descriptor')
    compressed = base64.b64decode(encoded, validate=True)
    need(len(compressed) <= MAX_JSON, 'compressed_bound')
    reader = zlib.decompressobj(31)
    raw = reader.decompress(compressed, maximum + 1)
    need(len(raw) <= maximum and reader.eof and not reader.unused_data and
        not reader.unconsumed_tail and len(raw) == count and sha(raw) == pin,
        'packed_integrity')
    return raw


def fetched(report, campaign, number, name, controller):
    directory = report / 'evidence' / campaign / ('fetch-' + str(number))
    raw = read(directory / name, 32768)
    receipt = load(directory / 'EXECUTION.json')
    need(receipt['action'] == 'fetch' and receipt['exit_code'] == 0 and
        receipt['capture_reason'] is None and receipt['capture_errors'] == [] and
        receipt['combined_output_limit'] == MAX_JSON and receipt['stderr_bytes'] == 0 and
        receipt['stderr.raw_sha256'] == EMPTY and receipt['controller_sha256'] == controller and
        receipt['Ethereum_signer_files_read_or_copied'] is False and
        receipt['only_fixed_' + campaign + '_unit'] is True, 'fetch_receipt')
    # Reconstruct the exact pinned capsule's JSON/base64 fetch envelope. The
    # original wrapper is not republished, but its captured SHA and length are.
    wrapper = (json.dumps({'phase': 'saved_artifact', 'name': name, 'bytes': len(raw),
        'sha256': sha(raw), 'base64': base64.b64encode(raw).decode('ascii')},
        sort_keys=True) + '\n').encode()
    need(len(wrapper) == receipt['stdout_bytes'] and sha(wrapper) == receipt['stdout.raw_sha256']
        and len(wrapper) <= MAX_JSON, 'fetch_envelope_pin')
    return decoded(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    report = options.report.resolve()
    repo = report.parents[1]
    prep = report / 'preparation' / 'c821'
    manifest = load(prep / 'SOURCE_MANIFEST.json')
    build = load(prep / 'BUILD_RECEIPT.json')
    controller = sha(read(prep / 'remote_capsule.py'))
    need(controller == build['controller']['sha256'] and
        sha(read(prep / 'SOURCE_MANIFEST.json')) == build['source_manifest']['sha256'] and
        len(manifest['source_files']) == 41 and build['archive_members'] == 49,
        'preparation_identity')
    old_manifest = load(report / 'preparation/c820/SOURCE_MANIFEST.json')
    need(set(manifest['source_files']) - set(old_manifest['source_files']) ==
        {'scripts/keeper-schedule.py'} and all(manifest['source_files'][key] == value
        for key, value in old_manifest['source_files'].items()), 'closure_change_scope')
    methods = manifest['new_methods']
    need(len(methods) == len(set(methods)) == 8 and
        manifest['new_method_AST_sha256'] == old_manifest['new_method_AST_sha256'], 'new_method_scope')
    test_path = repo / 'tests_python/test_keeper_sidecar_recovery.py'
    test_raw = read(test_path)
    need(sha(test_raw) == manifest['source_files'][str(test_path.relative_to(repo)).replace('\\', '/')]['sha256'],
        'frozen_test_file')
    test_ast = ast.parse(test_raw)
    cls = next(node for node in test_ast.body if isinstance(node, ast.ClassDef) and
        node.name == 'KeeperSidecarRecoveryTests')
    actual = {node.name: sha(ast.dump(node, include_attributes=False).encode()) for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}
    need(actual == manifest['new_method_AST_sha256'], 'method_ast_pins')

    names = ['RESULT.json', 'FINAL.json', 'PROGRESS.json', 'FOCUSED_RESULT.json',
        'FOCUSED_PROGRESS.json', 'SOURCE_RESULT.json', 'TARGET_RESULT.json',
        'WORKER_LOGS.json', 'MANAGER_TRACE.json', 'NATIVE_PROPERTIES.json']
    values = {name: fetched(report, 'c821', index, name, controller)
        for index, name in enumerate(names, 1)}
    result, final, progress, focus, focused_progress, source, target, logs, trace, native = (
        values[name] for name in names)
    need(result['success'] is True and result['cleanup'] is True and
        result['started_scenarios'] == result['passed_scenarios'] == STAGES and
        result['old_test_bodies_run'] == 0 and result['public_transactions'] == 0 and
        result['signer_contents_read'] is False and result['production_approved'] is False and
        0 < result['elapsed_seconds'] <= 165, 'campaign_scope')
    need(progress == {'schema': 1, 'current': None, 'started': STAGES, 'passed': STAGES,
        'old_test_bodies_run': 0}, 'scenario_progress')
    need(focus['success'] is True and focus['tests_run'] == 8 and focus['uid'] == focus['gid'] == 65534 and
        all(focus[key] == 0 for key in ('errors', 'failures', 'skipped', 'old_test_bodies_run',
        'public_transactions')) and focus['selected_methods'] == focus['started'] == focus['finished'] == methods and
        focus['method_outcomes'] == {name: 'passed' for name in methods} and
        focus['error_digests'] == focus['error_types'] == {} and focus['fixture_helper_setup_only'] is True and
        focus['actual_masked_regular_paths'] == 2 and focus['actual_unreadable_distinct_empty_root_masks'] is True,
        'focused_outcomes')
    need(focused_progress == {'schema': 1, 'selected_methods': methods, 'started': methods,
        'finished': methods, 'outcomes': focus['method_outcomes'], 'old_test_bodies_run': 0},
        'focused_progress')

    plan = source['restore_plan']
    need(source['success'] is source['unsigned'] is True and target['success'] is target['unsigned'] is True and
        source['signer_contents_read'] is target['signer_contents_read'] is False and
        source['public_transactions'] == target['public_transactions'] == 0 and
        source['source_state_unchanged'] is source['policy_and_configuration_unchanged'] is True and
        source['raw_records_rewritten'] is False and source['restore_does_not_adopt'] is True and
        source['source_files'] == source['restored_files'], 'actual_restore_scope')
    need(plan['unsigned'] is True and all(plan[key] is False for key in FLAGS) and
        sha(digest(plan)) == source['restore_plan_pin']['sha256'] and
        len(digest(plan)) == source['restore_plan_pin']['bytes'] and
        plan['manifest_sha256'] == source['bundle_manifest_pin'] == source['verified']['manifest_sha256'] and
        source['verified']['ok'] is True and source['verified']['unsigned'] is True and
        source['verified']['readiness_approved'] is False, 'unsigned_plan_pin')
    rows = {row['path']: {'bytes': row['bytes'], 'sha256': row['sha256']} for row in plan['files']}
    generation = source['selected']['generation']
    need(set(rows) == {'scheduler/selected.json', 'alerts/state.json',
        'backups/' + generation + '/manifest.json', 'backups/' + generation + '/journal.json'} and
        rows == source['source_files'] and len(rows) == 4 and
        source['selected']['manifest_sha256'] == rows['backups/' + generation + '/manifest.json']['sha256'] and
        source['selected']['policy_sha256'] == source['policy_pin'] == plan['policy_sha256'] and
        source['selected']['configuration_sha256'] == source['config_pin']['sha256'] ==
        plan['configuration_raw_sha256'] and source['selected']['identity'] == plan['identity'],
        'four_exact_recorded_payload_mappings')
    # These are deterministic encodings of saved objects, not independent reads
    # of the remote raw files. They strengthen the recorded SHA mapping.
    for obj, name in ((source['selected'], 'scheduler/selected.json'),
            (source['observer_before'], 'alerts/state.json')):
        raw = digest(obj, pretty=True)
        need(rows[name] == {'bytes': len(raw), 'sha256': sha(raw)}, 'saved_object_encoding')
    need(plan['restored_directories'] == {'scheduler_directory': 'scheduler',
        'alert_directory': 'alerts', 'backup_directory': 'backups'} and
        plan['new_empty_lock_files'] == ['scheduler/schedule.lock', 'alerts/alert.lock'], 'restore_mapping')
    need(set(source['source_locks']) == set(source['fresh_restore_locks']) == {'schedule', 'alert'} and
        len({tuple(pair) for pair in source['fresh_restore_locks'].values()}) == 2 and
        all(source['fresh_restore_locks'][key] != source['source_locks'][key] for key in source['source_locks']),
        'new_coordination_inodes')

    before, after = target['observer_before'], target['observer_after']
    need(before == source['observer_before'] and before['pending'] is not None and before['outbox'] and
        after['pending'] == before['pending'] and after['sequence'] == before['sequence'] and
        after['scope_sha256'] == before['scope_sha256'] and after['active'] == before['active'] and
        after['outbox'] == [] and after['last_observed_at'] >= before['last_observed_at'] and
        target['pending_first_seen_preserved'] == before['pending']['first_seen'], 'observer_continuity')
    queued = [event['event_id'] for event in before['outbox']]
    for event in before['outbox']:
        need(event['event_id'] == sha(digest([1, event['scope_sha256'], event['sequence'],
            event['type'], event['reason_code']], newline=False)) and
            event['unsigned'] is True and event['readiness_approved'] is False, 'event_identity')
    received = decoded(packed(result['receiver_events']))
    need(received == before['outbox'] and queued == target['same_queued_ids'] and
        target['fresh_target_namespace'] is target['logical_paths_and_raw_policy_unchanged'] is True and
        target['delivery_is_at_least_once'] is True, 'receiver_exact_ids')
    observation = target['observation']['observation']
    need(observation['delivery'] == {'acknowledged': len(queued), 'attempted': len(queued),
        'state': 'acknowledged'} and observation['event_ids'] == [] and
        observation['outbox_count'] == 0 and observation['ok'] is False and
        observation['observation']['reason_codes'] == ['health_not_healthy'] and
        observation['observation']['backup_ok'] is True, 'ack_with_expected_ongoing_incident')
    transition = result['scenario_details'][STAGES[2]]
    need(transition['source_before'] == transition['source_after'] and
        transition['queued_ids'] == transition['actual_received_ids'] == queued and
        transition['source_before']['journal'] == result['scenario_details'][STAGES[3]]['original_journal'],
        'source_retained_after_target')
    need(result['scenario_details'][STAGES[1]]['source_job_empty_before_target'] is True and
        result['scenario_details'][STAGES[1]]['source_files'] == rows and
        result['scenario_details'][STAGES[1]]['restored_files'] == rows, 'native_raw_equality_assertions')

    expected_sources = {name: pin['sha256'] for name, pin in manifest['members'].items()}
    expected_sources['SOURCE_MANIFEST.json'] = sha(read(prep / 'SOURCE_MANIFEST.json'))
    need(final['source_before'] == final['source_after'] == expected_sources and
        final['source_unchanged'] is final['mask_sources_unchanged'] is final['all_owned_group_empty'] is True,
        'final_source_and_groups')
    need(final['mask_before'] == final['mask_after'] and len(final['mask_before']) == 2 and
        len({(row['device'], row['inode']) for row in final['mask_before'].values()}) == 2 and
        all(row['uid'] == row['mode'] == row['bytes'] == 0 and row['links'] == 1
        for row in final['mask_before'].values()), 'final_unreadable_masks')
    need({tuple(pair) for pair in focus['masked_dev_inode_pairs']} ==
        {(row['device'], row['inode']) for row in final['mask_before'].values()} ==
        set(map(tuple, source['mask_inode_pairs'])) == set(map(tuple, target['mask_inode_pairs'])),
        'same_mask_identities')
    properties = decoded(packed(native['units']))
    final_properties = decoded(packed(final['unit_properties']))
    prefix = 'popl-keeper-sidecar-recovery-20261126-c821'
    owned = {prefix + '.service', *(prefix + '-' + role + '.service' for role in ('checks', 'source', 'target'))}
    need(set(final_properties['after_stop']) == owned and
        all(row['MainPID'] == '0' and row['ControlGroup'] == '' and row['ActiveState'] == 'inactive'
        for row in final_properties['after_stop'].values()), 'actual_final_four_groups')
    for role, stage in (('checks', STAGES[0]), ('source', STAGES[1]), ('target', STAGES[2])):
        key = prefix + '-' + role + '.service'
        completed = result['scenario_details'][stage]['properties']['completed']
        need(completed['Id'] == key and completed['Type'] == 'oneshot' and completed['User'] == 'nobody' and
            completed['Group'] == 'nogroup' and completed['PrivateNetwork'] == 'yes' and
            completed['CapabilityBoundingSet'] == '' and completed['Restart'] == 'no' and
            completed['KillMode'] == 'control-group' and completed['ExecMainCode'] == '1' and
            completed['ExecMainStatus'] == completed['MainPID'] == '0' and completed['ControlGroup'] == '' and
            int(completed['ExecMainStartTimestampMonotonic']) > 0 and
            properties[key]['first_existing']['InvocationID'] == completed['InvocationID'], 'actual_native_worker')
        need(('runtime/restored/scheduler:' in completed['BindPaths']) == (role == 'target'), 'namespace_mapping')
    commands = decoded(packed(trace['commands']))
    need(len(commands) == trace['count'] <= 150 and
        all(row['program'] in ('systemctl', 'systemd-run') and set(row['owned_units']) <= owned
        for row in commands) and sum(row['program'] == 'systemd-run' for row in commands) == 3,
        'bounded_owned_manager_trace')
    need(set(logs['logs']) == {role + '.' + channel for role in ('checks', 'source', 'target')
        for channel in ('stdout', 'stderr')}, 'worker_log_inventory')
    for name, row in logs['logs'].items():
        raw = packed(row, fields=('bytes', 'sha256', 'gzip_base64'), maximum=MAX_JSON)
        if name.endswith('stderr'):
            need(raw == b'', 'worker_stderr')
        else:
            need(decoded(raw)['success'] is True, 'worker_stdout')

    old_prep = report / 'preparation/c820'
    old_controller = sha(read(old_prep / 'remote_capsule.py'))
    old = fetched(report, 'c820', 1, 'RESULT.json', old_controller)
    old_final = fetched(report, 'c820', 2, 'FINAL.json', old_controller)
    need(old['success'] is False and old['started_scenarios'] == old['passed_scenarios'] == [] and
        old['old_test_bodies_run'] == 0 and old['error_type'] == 'FileNotFoundError' and
        old['frames'][1] == {'file': 'fixture.py', 'function': 'fixture', 'line': 102} and
        old_final['all_owned_group_empty'] is old_final['source_unchanged'] is old_final['mask_sources_unchanged'] is True,
        'original_failure_scope')

    preservation = load(report / 'verification/HOST_PRESERVATION.json')
    host_before = load(report / 'verification/before-016-CAPTURE.json')
    host_after = load(report / 'verification/final-016-CAPTURE.json')
    need(preservation['success'] is True and preservation['non_ambient_difference_count'] == 0 and
        preservation['ignored_observer_invocation_count'] == 1 and preservation['existing_units_checked'] == 5 and
        preservation['owned_labs_checked'] == 7 and preservation['raw_host_details_published'] is False and
        all(value is True for value in preservation['checks'].values()) and
        preservation['before_snapshot_sha256'] == host_before['snapshot_sha256'] and
        preservation['final_snapshot_sha256'] == host_after['snapshot_sha256'], 'sanitized_host_comparison')
    need(all(row['success'] is row['read_only'] is row['snapshot_complete'] is True and
        row['all_seven_owned_labs_stopped'] is True and row['credentials_read_or_exported'] is False and
        row['exit_code'] == row['service_actions'] == 0 and row['stderr_bytes'] == 0
        for row in (host_before, host_after)), 'host_capture_boundaries')

    output = options.output or report / 'verification/UBUNTU_VERIFICATION.json'
    output = output.resolve()
    need(output.parent == (report / 'verification').resolve() and not output.is_symlink(), 'report_output_only')
    summary = {'schema': 1, 'kind': 'saved_keeper_sidecar_Ubuntu_evidence_verification', 'success': True,
        'campaign': 'c821', 'original_c820': {'result': 'NONPASS', 'new_test_bodies_run': 0,
        'old_test_bodies_run': 0, 'cause': 'missing_dynamic_schedule_CLI_before_fixture_completed'},
        'new_methods_passed': 8, 'errors': 0, 'failures': 0, 'skips': 0,
        'new_method_seconds': focus['elapsed_seconds'], 'campaign_seconds': result['elapsed_seconds'],
        'stages_passed': STAGES, 'source_members': 41, 'archive_members': 49,
        'four_recorded_raw_payload_hash_length_mappings_equal': True,
        'native_actual_raw_equality_and_metadata_assertions': True,
        'physical_remote_payload_bytes_independently_rehashed': False,
        'deterministic_saved_selection_state_and_plan_encodings_match_recorded_pins': True,
        'new_lock_inodes_distinct_and_original_lock_ownership_not_restored': True,
        'queued_event_ids_and_pending_first_seen_preserved': True,
        'acknowledged_event_count': len(queued), 'at_least_once_delivery_not_exactly_once': True,
        'selected_backup_freshness_not_approved': True, 'source_policy_config_journal_unchanged': True,
        'all_four_owned_groups_stopped': True, 'masks_unchanged': True,
        'existing_host_units_checked': 5, 'existing_host_nonambient_differences': 0,
        'disclosed_observer_invocations': 1, 'sanitized_comparison_only_not_raw_host_recomputation': True,
        'verification_application_imports': 0, 'verification_test_bodies_run': 0,
        'verification_network_requests': 0, 'verification_server_actions': 0,
        'scope_limits': ['same-host isolated namespace and public synthetic vectors; no RPC or chain',
            'recorded raw payload pins reconcile successful native byte/readback assertions; raw remote payloads not fetched',
            'new empty locks and empty source job group do not prove independent host fencing or host-loss recovery',
            'local manifest pins do not establish off-host authenticity or canonical freshness',
            'sanitized host comparison is preserved and cross-bound to capture pins; private host raw details not republished',
            'no production channel, physical durability, sustained-operation or independent release approval'],
        'production_approved': False, 'input_pins': {str(Path(path).relative_to(repo)).replace('\\', '/'): value
            for path, value in sorted(INPUTS.items())}, 'verifier_sha256': sha(Path(__file__).read_bytes())}
    raw = digest(summary, pretty=True)
    output.write_bytes(raw)
    print(json.dumps({'success': True, 'new_methods_passed': 8, 'stages_passed': 4,
        'output_sha256': sha(raw), 'output_bytes': len(raw), 'test_bodies_executed_by_verifier': 0}))


if __name__ == '__main__':
    main()
