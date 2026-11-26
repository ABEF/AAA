"""c823 desktop-only proof of the pinned c821 package; no product imports.

This does not establish POSIX permissions, current canonical state, freshness,
single-writer fencing or permission to adopt a restored keeper/observer.
Original policy/configuration/signers are intentionally not input payloads.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

CAP = 16 * 1024 * 1024
SECONDS = 60
PROOF_CAP = 8192
V_ROOT = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/'
    '01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-offhost-20261126')
PRIVATE_ROOT, TRUST_ROOT = V_ROOT / 'private', V_ROOT / 'trust'
TRUST_SHA = '9bec125bedd73b6f80cb3f316a7822aa09aeb9198927ca8d901c476f3798c371'
OUTER = 'a9dea475a22014c7eb5fcf965896eb691a2ba5c8de352e0c23d6fd1611dbb05b'
NESTED = '911d98ef86b1cd229378ae15ac685e8ce67285c0035c8cf670dfca3cccc5d0d1'
POLICY = '7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'
CONFIG = '1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'
NAMES = ('manifest.json', 'selection.json', 'alert-state.json',
    'selected/manifest.json', 'selected/journal.json')
PAYLOADS = NAMES[1:]
OUTER_FLAGS = {'unsigned': True, 'readiness_approved': False,
    'old_sidecars_fenced': False, 'canonical_state_verified': False,
    'signer_material_included': False, 'policy_or_configuration_installed': False,
    'services_restarted': False, 'runtime_paths_mapped': False,
    'lock_ownership_restored': False, 'selected_generation_freshness_approved': False}
NESTED_FLAGS = {'unsigned': True, 'live_ready': False,
    'canonical_state_verified': False, 'old_keeper_fenced': False,
    'signer_material_included': False, 'configuration_installed': False,
    'service_restarted': False}
DAEMON = ('keeper/monitor.py', 'keeper/ops.py', 'keeper/health.py',
    'keeper/rebalance_confirmation.py', 'keeper/compound_policy.py',
    'keeper/cast_process.py', 'zzz_ops/protocol_policy.py', 'zzz_ops/lp_execution.py',
    'zzz_ops/execution_price.py', 'zzz_ops/rebalance_confirmation.py',
    'zzz_ops/abi.py', 'zzz_ops/rpc.py', 'zzz_ops/state.py')
NESTED_PRODUCER = ('keeper/recovery_bundle.py', 'scripts/keeper-recovery.py')
OUTER_PRODUCER = ('keeper/sidecar_recovery.py', 'scripts/keeper-sidecar-recovery.py')
SCHEDULE = (*DAEMON, 'keeper/alerts.py', 'scripts/keeper-alerts.py',
    *NESTED_PRODUCER, 'keeper/scheduling.py', 'scripts/keeper-schedule.py')
OUTER_FIELDS = {'schema', 'kind', 'created_at', 'policy_sha256',
    'configuration_raw_sha256', 'identity', 'source_files_sha256',
    'producer_files_sha256', 'original_paths', 'files', 'observer_summary',
    'scope', *OUTER_FLAGS}
NESTED_FIELDS = {'schema', 'kind', 'created_at', 'configuration_raw_sha256',
    'configuration_sha256', 'identity', 'source_files_sha256',
    'producer_files_sha256', 'files', 'pending_summary', 'scope', *NESTED_FLAGS}
SELECTION_FIELDS = {'schema', 'kind', 'policy_sha256', 'configuration_sha256',
    'generation', 'manifest_sha256', 'created_at', 'identity'}
OBSERVER_FIELDS = {'schema', 'scope_sha256', 'sequence', 'last_observed_at',
    'active', 'pending', 'outbox'}
EVENT_FIELDS = {'schema', 'event_id', 'type', 'reason_code', 'sequence',
    'observed_at', 'scope_sha256', 'unsigned', 'readiness_approved'}


def need(value):
    if not value:
        raise ValueError('Desktop package verification refused.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def decode(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value)
            value[key] = item
        return value
    def reject(_):
        raise ValueError('Desktop package verification refused.')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
        parse_float=reject, parse_constant=reject)
    need(type(value) is dict)
    stack, count = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        count += 1
        need(depth <= 32 and count <= 100000)
        if type(item) is dict:
            stack.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            stack.extend((child, depth + 1) for child in item)
    return value


def clean_path(value, *, new=False):
    path = Path(value)
    need(path.is_absolute() and '..' not in path.parts and '\x00' not in str(path))
    need(not str(path).startswith(('\\\\', '//')))
    if os.name == 'nt':
        need(all(':' not in part and not part.endswith(('.', ' '))
            for part in path.parts[1:]))
    for item in (*reversed(path.parents), path):
        if new and item == path:
            need(not os.path.lexists(path))
            break
        record = item.lstat()
        need(not stat.S_ISLNK(record.st_mode) and not getattr(record,
            'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
        if item != path:
            need(stat.S_ISDIR(record.st_mode))
    return path


def identity(record):
    return (record.st_dev, record.st_ino, record.st_size, record.st_mtime_ns,
        record.st_mode, record.st_nlink)


def read(path, maximum, end):
    need(time.monotonic() <= end)
    clean_path(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
        before.st_ino != 0 and 0 < before.st_size <= maximum)
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    flags |= getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_CLOEXEC', 0)
    fd = os.open(path, flags)
    try:
        need(identity(os.fstat(fd)) == identity(before))
        pieces, size = [], 0
        while True:
            need(time.monotonic() <= end)
            part = os.read(fd, min(65536, maximum + 1 - size))
            if not part:
                break
            size += len(part)
            need(size <= maximum)
            pieces.append(part)
        need(identity(os.fstat(fd)) == identity(before) == identity(path.lstat())
            and size == before.st_size)
    finally:
        os.close(fd)
    clean_path(path)
    return b''.join(pieces)


def inventory(folder, end):
    clean_path(folder)
    need(stat.S_ISDIR(folder.lstat().st_mode))
    nested = clean_path(folder / 'selected')
    need(stat.S_ISDIR(nested.lstat().st_mode))
    for directory, names in ((folder,
            {'manifest.json', 'selection.json', 'alert-state.json', 'selected'}),
            (nested, {'manifest.json', 'journal.json'})):
        found = set()
        with os.scandir(directory) as entries:
            for row in entries:
                need(time.monotonic() <= end and row.name in names and
                    row.name not in found and len(found) < len(names))
                found.add(row.name)
        need(found == names and time.monotonic() <= end)


def hashes(value, names):
    need(type(value) is dict and set(value) == set(names))
    need(all(type(item) is str and re.fullmatch('[0-9a-f]{64}', item)
        and int(item, 16) != 0 for item in value.values()))


def verify(package, trust_path, end):
    package, trust_path = clean_path(package), clean_path(trust_path)
    need(not trust_path.is_relative_to(package))
    trust_raw = read(trust_path, 65536, end)
    need(sha(trust_raw) == TRUST_SHA)
    trust = decode(trust_raw)
    need(trust['success'] is True and trust['bundle_manifest_pin'] == OUTER and
        trust['policy_pin'] == POLICY and trust['config_pin']['sha256'] == CONFIG)
    selected_trust = trust['selected']
    generation = selected_trust['generation']
    expected = {'selection.json': trust['source_files']['scheduler/selected.json'],
        'alert-state.json': trust['source_files']['alerts/state.json'],
        'selected/manifest.json': trust['source_files']['backups/' + generation + '/manifest.json'],
        'selected/journal.json': trust['source_files']['backups/' + generation + '/journal.json']}
    inventory(package, end)
    records = [clean_path(package / name).lstat() for name in NAMES]
    need(sum(row.st_size for row in records) + len(trust_raw) <= CAP and
        len({(row.st_dev, row.st_ino) for row in records}) == 5)
    raw = {name: read(package / name, 65536 if name == 'manifest.json'
        else expected[name]['bytes'], end) for name in NAMES}
    need(sha(raw['manifest.json']) == OUTER and sha(raw['selected/manifest.json']) == NESTED)
    for name, row in expected.items():
        need(len(raw[name]) == row['bytes'] and sha(raw[name]) == row['sha256'])
    outer, selection, observer, nested, journal = [decode(raw[name]) for name in NAMES]
    need(set(outer) == OUTER_FIELDS and set(nested) == NESTED_FIELDS and
        set(selection) == SELECTION_FIELDS and set(observer) == OBSERVER_FIELDS)
    for value, kind in ((outer, 'popl-keeper-sidecar-recovery'),
            (selection, 'popl-keeper-selected-backup'), (nested, 'popl-keeper-recovery')):
        need(type(value['schema']) is int and value['schema'] == 1 and value['kind'] == kind)
    need(type(observer['schema']) is int and observer['schema'] == 1)
    need(all(outer.get(key) is value for key, value in OUTER_FLAGS.items()) and
        all(nested.get(key) is value for key, value in NESTED_FLAGS.items()))
    need(outer['scope'] == 'exact_stable_sidecar_state_not_host_fencing_or_canonical_truth'
        and nested['scope'] == 'stable_point_in_time_bytes_not_latest_chain_state_or_runtime_attestation')
    need(outer['original_paths'] == trust['restore_plan']['original_paths'])
    need(selection == selected_trust and outer['identity'] == nested['identity'] == selection['identity'])
    need(outer['policy_sha256'] == selection['policy_sha256'] == POLICY and
        outer['configuration_raw_sha256'] == nested['configuration_raw_sha256'] ==
        selection['configuration_sha256'] == CONFIG)
    need(selection['manifest_sha256'] == NESTED and
        nested['created_at'] == selection['created_at'] == 1795723324)
    now = int(time.time())
    need(type(outer['created_at']) is int and nested['created_at'] <= outer['created_at'] <= now
        and now - outer['created_at'] <= 86400)
    hashes(outer['source_files_sha256'], SCHEDULE)
    hashes(nested['source_files_sha256'], DAEMON)
    hashes(outer['producer_files_sha256'], OUTER_PRODUCER)
    hashes(nested['producer_files_sha256'], NESTED_PRODUCER)
    need(all(outer['source_files_sha256'][name] == item for name, item in
        {**nested['source_files_sha256'], **nested['producer_files_sha256']}.items()))
    need(outer['files'] == [{'path': name, 'bytes': len(raw[name]), 'sha256': sha(raw[name])}
        for name in PAYLOADS] and nested['files'] == [{'path': 'journal.json',
            'bytes': len(raw['selected/journal.json']), 'sha256': sha(raw['selected/journal.json'])}])
    need(observer == trust['observer_before'])
    summary = {'sequence': observer['sequence'], 'last_observed_at': observer['last_observed_at'],
        'outbox_count': len(observer['outbox']), 'pending': observer['pending']}
    need(outer['observer_summary'] == summary)
    for event in observer['outbox']:
        need(set(event) == EVENT_FIELDS and event['unsigned'] is True and
            event['readiness_approved'] is False and event['event_id'] == sha(encoded(
                [1, event['scope_sha256'], event['sequence'], event['type'], event['reason_code']])))
    economic = outer['identity']
    need(all(journal.get(key) == economic[key] for key in ('chain_id', 'sender',
        'contracts', 'accounting_model', 'accounting_version', 'fee_intake_version', 'execution_price_version')))
    need(type(journal['next_nonce']) is int and journal['next_nonce'] >= 0 and
        type(journal['spent']) is dict)
    for day, amount in journal['spent'].items():
        need(dt.date.fromisoformat(day).isoformat() == day and type(amount) is int and amount >= 0)
    pending = journal['pending']
    need(nested['pending_summary'] == {'present': pending is not None,
        'hash_present': pending is not None and pending.get('hash') is not None,
        'fee_review_present': pending is not None and pending.get('fee_review') is not None,
        'manual_fee_review_required': pending is not None and 'fee_review' not in pending,
        'next_nonce': journal['next_nonce']})
    inventory(package, end)
    for name in NAMES:
        need(read(package / name, len(raw[name]), end) == raw[name])
    need(read(trust_path, len(trust_raw), end) == trust_raw)
    need(time.monotonic() <= end)
    return {'schema': 1, 'kind': 'popl-keeper-offhost-desktop-proof', 'ok': True,
        'unsigned': True, 'readiness_approved': False, 'production_approved': False,
        'outer_manifest_sha256': OUTER, 'nested_manifest_sha256': NESTED,
        'policy_sha256': POLICY, 'configuration_sha256': CONFIG,
        'outer_created_at': outer['created_at'], 'nested_created_at': nested['created_at'],
        'verified_at_unix': now, 'posix_core_verified': False,
        'canonical_state_verified': False, 'current_operating_freshness_approved': False,
        'operating_max_age_seconds': 900, 'recovery_review_max_age_seconds': 86400,
        'source_trust_report_sha256': TRUST_SHA,
        'files': {name: {'bytes': len(raw[name]), 'sha256': sha(raw[name])} for name in NAMES},
        'preserved_state': {'economic_identity_sha256': sha(encoded(economic)),
            'next_nonce': journal['next_nonce'], 'spent_sha256': sha(encoded(journal['spent'])),
            'pending_sha256': sha(encoded(pending)),
            'receipt_anchor_sha256': sha(encoded(journal['receipt_anchor'])),
            'observer_sequence': observer['sequence'],
            'pending_first_seen': observer['pending']['first_seen'] if observer['pending'] else None,
            'pending_intent_sha256': observer['pending']['intent_sha256'] if observer['pending'] else None,
            'event_ids': [event['event_id'] for event in observer['outbox']]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--trust', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        end = time.monotonic() + SECONDS
        need(os.name == 'nt')
        package, trust = clean_path(args.package), clean_path(args.trust)
        output = clean_path(args.output, new=True)
        need(package.is_relative_to(PRIVATE_ROOT) and package != PRIVATE_ROOT and
            trust.is_relative_to(TRUST_ROOT) and output.is_relative_to(PRIVATE_ROOT))
        need(not output.parent.is_relative_to(package) and
            not package.is_relative_to(output.parent) and output != trust)
        result = verify(package, trust, end)
        raw = json.dumps(result, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
        need(len(raw) <= PROOF_CAP)
        clean_path(output, new=True)
        parent_identity = identity(output.parent.lstat())
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
        flags |= getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(output, flags, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        clean_path(output)
        need(identity(output.parent.lstat())[:2] == parent_identity[:2] and
            output.lstat().st_nlink == 1)
        need(read(output, len(raw), end) == raw and time.monotonic() <= end)
        print(json.dumps({'schema': 1, 'ok': True, 'unsigned': True,
            'readiness_approved': False, 'proof_sha256': sha(raw)}, sort_keys=True))
        return 0
    except (Exception, KeyboardInterrupt):
        print('{"ok":false,"readiness_approved":false,"schema":1,"unsigned":true}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
