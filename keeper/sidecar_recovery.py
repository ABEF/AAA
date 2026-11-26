"""Unsigned exact-state backup and review-only restoration for keeper sidecars.

The selected journal is a historical backup, not the current keeper journal.
Policy/configuration and signer material stay separate. Neither file hashes nor
new coordination files establish fencing, canonical freshness or adoption.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
import time

from keeper import alerts, recovery_bundle as recovery, scheduling

DEFAULT_BYTES = recovery.DEFAULT_BYTES
MAX_BYTES = recovery.MAX_BYTES
PRODUCER_FILES = ('keeper/sidecar_recovery.py', 'scripts/keeper-sidecar-recovery.py')
PAYLOADS = ('selection.json', 'alert-state.json', 'selected/manifest.json', 'selected/journal.json')
FLAGS = {'unsigned': True, 'readiness_approved': False, 'old_sidecars_fenced': False,
    'canonical_state_verified': False, 'signer_material_included': False,
    'policy_or_configuration_installed': False, 'services_restarted': False,
    'runtime_paths_mapped': False, 'lock_ownership_restored': False,
    'selected_generation_freshness_approved': False}
SCOPE = 'exact_stable_sidecar_state_not_host_fencing_or_canonical_truth'
MANIFEST_FIELDS = frozenset(('schema', 'kind', 'created_at', 'policy_sha256',
    'configuration_raw_sha256', 'identity', 'source_files_sha256',
    'producer_files_sha256', 'original_paths', 'files', 'observer_summary',
    'scope', *FLAGS))
REFUSAL_CODES = frozenset(('invalid_input', 'trusted_pin', 'policy_identity',
    'source_identity', 'source_lock', 'source_state', 'source_snapshot_changed',
    'package_inventory', 'package_age', 'output_publication', 'resource_budget'))


class SidecarRefusal(ValueError):
    """Fixed sanitized diagnostics; no input paths, credentials or exception text."""
    def __init__(self, code):
        self.code = code if type(code) is str and code in REFUSAL_CODES else 'invalid_input'
        super().__init__('Keeper sidecar recovery refused [' + self.code + '].')


def _need(value, code='source_state'):
    if not value:
        raise SidecarRefusal(code)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _budget(seconds, maximum):
    _need(type(seconds) is int and 1 <= seconds <= 120, 'resource_budget')
    _need(type(maximum) is int and 1 <= maximum <= MAX_BYTES, 'resource_budget')
    return recovery._Budget(seconds, maximum)


def _context(policy_path, policy_sha256, budget):
    start = time.monotonic()
    context = scheduling._load(policy_path, policy_sha256, shared_budget=budget)
    budget.end = min(budget.end, start + context['policy']['max_seconds'])
    budget.maximum = min(budget.maximum, context['policy']['max_bytes'])
    budget.check()
    return context


def _key(item):
    return item.st_dev, item.st_ino, item.st_mode, item.st_uid, item.st_nlink, item.st_size, item.st_mtime_ns


def _held_lock(token):
    path, descriptor, identity = token
    _need(_key(path.lstat()) == _key(os.fstat(descriptor)) == identity, 'source_lock')


@contextmanager
def _existing_lock(path):
    """Never O_CREAT: missing source locks cannot silently become new locks."""
    import fcntl
    scheduling._private_directory(path.parent)
    recovery._path(path, kind='file')
    before = path.lstat()
    _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
        before.st_uid == os.getuid() and stat.S_IMODE(before.st_mode) == 0o600, 'source_lock')
    descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    locked = False
    try:
        _need(_key(os.fstat(descriptor)) == _key(before), 'source_lock')
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SidecarRefusal('source_lock') from None
        locked = True
        token = path, descriptor, _key(before)
        _held_lock(token)
        yield token
        _held_lock(token)
    finally:
        try:
            if locked:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _selection(raw, context):
    value = recovery._decode(raw)
    _need(set(value) == scheduling.SELECTION_FIELDS and type(value['schema']) is int and
        value['schema'] == 1 and value['kind'] == 'popl-keeper-selected-backup' and
        value['policy_sha256'] == context['policy_sha256'] and
        value['configuration_sha256'] == context['policy']['configuration_sha256'] and
        value['identity'] == context['identity'] and
        type(value['generation']) is str and len(value['generation']) == 41 and
        value['generation'].startswith('snapshot-') and
        all(ch in '0123456789abcdef' for ch in value['generation'][9:]) and
        scheduling._hash(value['manifest_sha256']) and type(value['created_at']) is int and
        0 <= value['created_at'] < 1 << 63)
    return value


def _observer(raw):
    """Validate existing schema1 bytes, without the observer's missing-file default."""
    value = alerts._decode(raw)
    _need(set(value) == {'schema', 'scope_sha256', 'sequence', 'last_observed_at', 'active', 'pending', 'outbox'}
        and type(value['schema']) is int and value['schema'] == 1 and
        (value['scope_sha256'] is None or alerts._hex(value['scope_sha256'])))
    alerts._uint(value['sequence']); alerts._uint(value['last_observed_at'])
    _need(type(value['active']) is dict and set(value['active']) <= alerts.REASONS and
        all(alerts._hex(item) for item in value['active'].values()))
    pending = value['pending']
    _need(pending is None or type(pending) is dict and set(pending) == {'intent_sha256', 'first_seen'} and
        alerts._hex(pending['intent_sha256']) and type(pending['first_seen']) is int and
        0 <= pending['first_seen'] <= value['last_observed_at'])
    _need(type(value['outbox']) is list and len(value['outbox']) <= alerts.MAX_OUTBOX)
    sequence = 0; identifiers = set()
    for event in value['outbox']:
        alerts._event_valid(event)
        _need(sequence < event['sequence'] <= value['sequence'] and event['event_id'] not in identifiers)
        sequence = event['sequence']; identifiers.add(event['event_id'])
    return value


def _summary(observer):
    return {'sequence': observer['sequence'], 'last_observed_at': observer['last_observed_at'],
        'outbox_count': len(observer['outbox']), 'pending': observer['pending']}


def _paths(context):
    return {name: str(path) for name, path in context['directories'].items()}


def _selected(folder, selected, context, current):
    # Validate historical integrity at its own recorded time, not operational
    # freshness at today's time. The normal restored observer still ages it.
    _need(selected['created_at'] <= current, 'source_state')
    manifest, journal, _ = recovery._verified(folder, selected['manifest_sha256'],
        context['configuration'], max_age_seconds=1, minimum_created_at=0,
        minimum_next_nonce=None, budget=context['budget'], now=selected['created_at'])
    _need(manifest['created_at'] == selected['created_at'] and manifest['identity'] == selected['identity'])
    return manifest, journal


def _separate_output(output, context, extra=()):
    output = recovery._path(output, kind='new')
    config = recovery._decode(context['configuration_raw'])
    journal = recovery._path(config.get('state_path', 'var/keeper.json'), base=context['working'])
    references = recovery._references(config, context['working'], context['configuration'], journal)
    for original in (context['policy_path'], context['configuration'], journal, journal.parent,
            *references, *context['directories'].values(), *extra):
        scheduling._separate(output, original)
    return output


def _source_files(context, current):
    dirs = context['directories']; budget = context['budget']
    scheduling._private_inventory(dirs['scheduler_directory'],
        {scheduling.SELECTION_NAME, scheduling.LOCK_NAME}, required=(scheduling.SELECTION_NAME, scheduling.LOCK_NAME))
    scheduling._private_inventory(dirs['alert_directory'], {'state.json', 'alert.lock'},
        required=('state.json', 'alert.lock'))
    selection_raw = recovery._read(dirs['scheduler_directory'] / scheduling.SELECTION_NAME,
        scheduling.MAX_SELECTION_BYTES, budget)
    alert_raw = recovery._read(dirs['alert_directory'] / 'state.json', alerts.MAX_STATE_BYTES, budget)
    selected = _selection(selection_raw, context); observer = _observer(alert_raw)
    folder = dirs['backup_directory'] / selected['generation']
    _need(len(selection_raw) + len(alert_raw) + (folder / 'manifest.json').lstat().st_size +
        (folder / 'journal.json').lstat().st_size <= budget.maximum, 'resource_budget')
    manifest, journal_raw = _selected(folder, selected, context, current)
    manifest_raw = recovery._read(folder / 'manifest.json', recovery.MAX_MANIFEST_BYTES, budget)
    _need(_sha(manifest_raw) == selected['manifest_sha256'])
    _need(recovery._decode(manifest_raw) == manifest)
    raw = {'selection.json': selection_raw, 'alert-state.json': alert_raw,
        'selected/manifest.json': manifest_raw, 'selected/journal.json': journal_raw}
    return selected, observer, raw


def _plan(manifest, pin, selected):
    mapping = {'selection.json': 'scheduler/selected.json', 'alert-state.json': 'alerts/state.json',
        'selected/manifest.json': 'backups/' + selected['generation'] + '/manifest.json',
        'selected/journal.json': 'backups/' + selected['generation'] + '/journal.json'}
    return {'schema': 1, 'kind': 'popl-keeper-sidecar-restore-plan', 'manifest_sha256': pin,
        'policy_sha256': manifest['policy_sha256'],
        'configuration_raw_sha256': manifest['configuration_raw_sha256'], 'identity': manifest['identity'],
        'original_paths': manifest['original_paths'],
        'restored_directories': {'scheduler_directory': 'scheduler', 'alert_directory': 'alerts', 'backup_directory': 'backups'},
        'files': [{**row, 'path': mapping[row['path']]} for row in manifest['files']],
        'new_empty_lock_files': ['scheduler/schedule.lock', 'alerts/alert.lock'],
        'observer_summary': manifest['observer_summary'], **FLAGS,
        'required_operator_review': ['fence old sidecar writers and automatic restart paths',
            'retain original policy configuration source release and independent manifest pin',
            'review exact original logical paths versus proposed restore directory mapping',
            'new empty locks are coordination inodes not restored lock ownership',
            'selected journal is an old backup not the current keeper journal or canonical state',
            'resume observation without resetting event IDs sequence or pending first_seen',
            'review actual current health backup age and delivery before any separate adoption']}


def _fits(raw, manifest, selected, maximum):
    total = sum(len(value) for value in raw.values())
    encoded = recovery._json(manifest)
    plan = recovery._json(_plan(manifest, '0' * 64, selected))
    _need(len(encoded) <= recovery.MAX_MANIFEST_BYTES and len(plan) <= recovery.MAX_MANIFEST_BYTES and
        total + max(len(encoded), len(plan)) <= maximum, 'resource_budget')
    return encoded


def _same_capture(context, selected, observer, raw, producer, current):
    scheduling._stable(context)
    again_selected, again_observer, again_raw = _source_files(context, current)
    _need(again_selected == selected and again_observer == observer and again_raw == raw,
        'source_snapshot_changed')
    _need(recovery._sources(PRODUCER_FILES, context['budget']) == producer, 'source_snapshot_changed')


def _package_inventory(folder, budget):
    recovery._protected(folder)
    found = set()
    with os.scandir(folder) as entries:
        for entry in entries:
            budget.check()
            _need(entry.name in ('manifest.json', 'selection.json', 'alert-state.json', 'selected') and
                entry.name not in found, 'package_inventory')
            item = entry.stat(follow_symlinks=False)
            _need(stat.S_ISDIR(item.st_mode) if entry.name == 'selected' else
                stat.S_ISREG(item.st_mode) and item.st_nlink == 1, 'package_inventory')
            found.add(entry.name)
    _need(found == {'manifest.json', 'selection.json', 'alert-state.json', 'selected'}, 'package_inventory')
    recovery._inventory(folder / 'selected', budget)


def _verified(bundle, pin, context, *, max_age_seconds, minimum_created_at, current):
    budget = context['budget']; _need(scheduling._hash(pin), 'trusted_pin')
    _need(type(max_age_seconds) is int and 1 <= max_age_seconds < 1 << 63 and
        type(minimum_created_at) is int and 0 <= minimum_created_at < 1 << 63, 'invalid_input')
    folder = recovery._path(bundle, kind='dir'); _package_inventory(folder, budget)
    encoded = recovery._read(folder / 'manifest.json', recovery.MAX_MANIFEST_BYTES, budget)
    _need(_sha(encoded) == pin, 'trusted_pin'); manifest = recovery._decode(encoded)
    _need(set(manifest) == MANIFEST_FIELDS and type(manifest['schema']) is int and manifest['schema'] == 1 and
        manifest['kind'] == 'popl-keeper-sidecar-recovery' and manifest['scope'] == SCOPE and
        all(manifest.get(key) is value for key, value in FLAGS.items()), 'package_inventory')
    _need(manifest['policy_sha256'] == context['policy_sha256'] and
        manifest['configuration_raw_sha256'] == context['policy']['configuration_sha256'] and
        manifest['identity'] == context['identity'] and manifest['original_paths'] == _paths(context), 'policy_identity')
    _need(manifest['source_files_sha256'] == context['policy']['source_files_sha256'], 'source_identity')
    producer = manifest['producer_files_sha256']
    _need(type(producer) is dict and set(producer) == set(PRODUCER_FILES) and
        all(scheduling._hash(value) for value in producer.values()), 'package_inventory')
    created = manifest['created_at']
    _need(type(created) is int and minimum_created_at <= created <= current and
        current - created <= max_age_seconds, 'package_age')
    rows = manifest['files']
    _need(type(rows) is list and len(rows) == len(PAYLOADS), 'package_inventory')
    for name, row in zip(PAYLOADS, rows):
        _need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'} and row['path'] == name and
            type(row['bytes']) is int and 0 < row['bytes'] <= budget.maximum and scheduling._hash(row['sha256']),
            'package_inventory')
    _need(sum(row['bytes'] for row in rows) + len(encoded) <= budget.maximum, 'resource_budget')
    raw = {}
    for name, row in zip(PAYLOADS, rows):
        maximum = scheduling.MAX_SELECTION_BYTES if name == 'selection.json' else (
            alerts.MAX_STATE_BYTES if name == 'alert-state.json' else
            recovery.MAX_MANIFEST_BYTES if name == 'selected/manifest.json' else budget.maximum)
        value = recovery._read(folder / name, min(row['bytes'], maximum), budget)
        _need(len(value) == row['bytes'] and _sha(value) == row['sha256'], 'package_inventory')
        raw[name] = value
    selected = _selection(raw['selection.json'], context); observer = _observer(raw['alert-state.json'])
    _need(manifest['observer_summary'] == _summary(observer), 'package_inventory')
    nested, nested_raw = _selected(folder / 'selected', selected, context, created)
    _need(nested_raw == raw['selected/journal.json'] and
        recovery._decode(raw['selected/manifest.json']) == nested, 'package_inventory')
    _fits(raw, manifest, selected, budget.maximum)
    scheduling._stable(context)
    _need(recovery._read(folder / 'manifest.json', recovery.MAX_MANIFEST_BYTES, budget) == encoded,
        'source_snapshot_changed')
    for name, value in raw.items():
        _need(recovery._read(folder / name, len(value), budget) == value, 'source_snapshot_changed')
    _package_inventory(folder, budget)
    return manifest, selected, raw, folder


def _refusal(exc, stage):
    if type(exc) is SidecarRefusal:
        return exc
    if isinstance(exc, (recovery.RecoveryRefusal, scheduling.ScheduleRefusal)) and exc.code == 'resource_budget':
        return SidecarRefusal('resource_budget')
    if type(exc) is scheduling.ScheduleRefusal and exc.code == 'source_identity':
        return SidecarRefusal('source_identity')
    return SidecarRefusal(stage)


def backup(policy_path, policy_sha256, output, *, max_bytes=DEFAULT_BYTES, max_seconds=60, now=None):
    """Capture existing state under both old locks; never creates a source lock."""
    stage = 'policy_identity'
    try:
        context = _context(policy_path, policy_sha256, _budget(max_seconds, max_bytes))
        budget = context['budget']; current = recovery._time(now); dirs = context['directories']
        output = _separate_output(output, context)
        stage = 'source_lock'
        with _existing_lock(dirs['scheduler_directory'] / scheduling.LOCK_NAME) as scheduler_lock:
            with _existing_lock(dirs['alert_directory'] / 'alert.lock') as observer_lock:
                stage = 'source_state'
                selected, observer, raw = _source_files(context, current)
                producer = recovery._sources(PRODUCER_FILES, budget)
                manifest = {'schema': 1, 'kind': 'popl-keeper-sidecar-recovery', 'created_at': current,
                    'policy_sha256': context['policy_sha256'],
                    'configuration_raw_sha256': context['policy']['configuration_sha256'],
                    'identity': context['identity'], 'source_files_sha256': context['policy']['source_files_sha256'],
                    'producer_files_sha256': producer, 'original_paths': _paths(context),
                    'files': [{'path': name, 'bytes': len(raw[name]), 'sha256': _sha(raw[name])} for name in PAYLOADS],
                    'observer_summary': _summary(observer), 'scope': SCOPE, **FLAGS}
                encoded = _fits(raw, manifest, selected, budget.maximum)
                _same_capture(context, selected, observer, raw, producer, current)
                _held_lock(scheduler_lock); _held_lock(observer_lock)
                stage = 'output_publication'
                output, reservation = recovery._reserve(output)
                nested, nested_reservation = recovery._reserve(output / 'selected')
                for name in PAYLOADS:
                    recovery._write(output / name, raw[name], budget,
                        nested_reservation if name.startswith('selected/') else reservation)
                _same_capture(context, selected, observer, raw, producer, current)
                _held_lock(scheduler_lock); _held_lock(observer_lock)
                for name, value in raw.items():
                    _need(recovery._read(output / name, len(value), budget) == value, 'output_publication')
                recovery._output_identity(output, reservation)
                recovery._write(output / 'manifest.json', encoded, budget, reservation)
                return manifest, _sha(encoded)
    except Exception as exc:
        raise _refusal(exc, stage) from None


def verify(bundle, manifest_sha256, policy_path, policy_sha256, *, max_age_seconds,
        minimum_created_at=0, max_bytes=DEFAULT_BYTES, max_seconds=60, now=None):
    """Verify a complete package's exact bytes and capture age; never adopts it."""
    try:
        context = _context(policy_path, policy_sha256, _budget(max_seconds, max_bytes))
        manifest, _, _, _ = _verified(bundle, manifest_sha256, context,
            max_age_seconds=max_age_seconds, minimum_created_at=minimum_created_at, current=recovery._time(now))
        return manifest
    except Exception as exc:
        raise _refusal(exc, 'package_inventory') from None


def restore(bundle, manifest_sha256, policy_path, policy_sha256, output, *, max_age_seconds,
        minimum_created_at=0, max_bytes=DEFAULT_BYTES, max_seconds=60, now=None):
    """Fresh private output and unsigned mapping plan; lock ownership is not data."""
    stage = 'package_inventory'
    try:
        context = _context(policy_path, policy_sha256, _budget(max_seconds, max_bytes))
        current = recovery._time(now); budget = context['budget']
        options = {'max_age_seconds': max_age_seconds, 'minimum_created_at': minimum_created_at, 'current': current}
        manifest, selected, raw, source = _verified(bundle, manifest_sha256, context, **options)
        output = _separate_output(output, context, (source,))
        plan = _plan(manifest, manifest_sha256, selected); encoded = recovery._json(plan)
        _need(sum(map(len, raw.values())) + len(encoded) <= budget.maximum, 'resource_budget')
        stage = 'output_publication'; output, reservation = recovery._reserve(output)
        reservations = {}
        for name in ('scheduler', 'alerts', 'backups', 'backups/' + selected['generation']):
            _, reservations[name] = recovery._reserve(output / name)
        mapping = {'selection.json': 'scheduler/selected.json', 'alert-state.json': 'alerts/state.json',
            'selected/manifest.json': 'backups/' + selected['generation'] + '/manifest.json',
            'selected/journal.json': 'backups/' + selected['generation'] + '/journal.json'}
        for old, name in mapping.items():
            recovery._write(output / name, raw[old], budget, reservations[str(Path(name).parent)])
        for name in ('scheduler/schedule.lock', 'alerts/alert.lock'):
            recovery._write(output / name, b'', budget, reservations[str(Path(name).parent)])
        again, again_selected, again_raw, _ = _verified(bundle, manifest_sha256, context, **options)
        _need(again == manifest and again_selected == selected and again_raw == raw, 'source_snapshot_changed')
        for old, name in mapping.items():
            _need(recovery._read(output / name, len(raw[old]), budget) == raw[old], 'output_publication')
        lock_identities = set()
        for name in ('scheduler/schedule.lock', 'alerts/alert.lock'):
            path = output / name; item = path.lstat()
            _need(stat.S_ISREG(item.st_mode) and item.st_uid == os.getuid() and
                stat.S_IMODE(item.st_mode) == 0o600 and item.st_nlink == 1 and item.st_size == 0 and
                recovery._read(path, 0, budget) == b'', 'output_publication')
            lock_identities.add((item.st_dev, item.st_ino))
        _need(len(lock_identities) == 2, 'output_publication')
        recovery._output_identity(output, reservation)
        recovery._write(output / 'RESTORE_PLAN.json', encoded, budget, reservation)
        return plan, _sha(encoded)
    except Exception as exc:
        raise _refusal(exc, stage) from None
