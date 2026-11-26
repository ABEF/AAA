"""Unsigned one-shot backup/observer coordination for supervised Ubuntu timers.

The pinned policy authorizes local automatic selection of newly verified backup
generations. That local producer pin is not independent/off-host authentication,
canonical freshness, signer fencing, loaded-code attestation or live readiness.
Only explicit init creates state. Nothing installs or starts a service.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import time

from keeper import alerts, recovery_bundle as recovery
from zzz_ops.state import atomic_json, process_lock

SOURCE_FILES = tuple(dict.fromkeys((*recovery.SOURCE_FILES, *alerts.OBSERVER_SOURCE_FILES,
    'keeper/scheduling.py', 'scripts/keeper-schedule.py')))
POLICY_FIELDS = frozenset(('schema', 'kind', 'configuration', 'configuration_sha256',
    'working_directory', 'scheduler_directory', 'backup_directory', 'alert_directory',
    'source_files_sha256', 'max_backups', 'max_health_age_seconds',
    'max_backup_age_seconds', 'pending_max_age_seconds', 'receiver', 'allow_dry_run',
    'max_bytes', 'max_seconds'))
SELECTION_FIELDS = frozenset(('schema', 'kind', 'policy_sha256', 'configuration_sha256',
    'generation', 'manifest_sha256', 'created_at', 'identity'))
REFUSAL_CODES = frozenset(('invalid_input', 'policy_pin', 'policy_input',
    'source_identity', 'configuration_identity', 'path_identity', 'scheduler_state',
    'scheduler_lock', 'capacity', 'backup_capture', 'backup_verification',
    'selection_publication', 'observer_state', 'observation', 'resource_budget'))
MAX_SELECTION_BYTES = 65536
SELECTION_NAME = 'selected.json'
LOCK_NAME = 'schedule.lock'


class ScheduleRefusal(ValueError):
    """Fixed diagnostics only; never paths, configuration or signer output."""
    def __init__(self, code, cause_code=None):
        self.code = code if type(code) is str and code in REFUSAL_CODES else 'invalid_input'
        known = recovery.REFUSAL_CODES | alerts.REFUSAL_CODES
        self.cause_code = cause_code if type(cause_code) is str and cause_code in known else None
        super().__init__('Keeper schedule operation refused [' + self.code + '].')


def _need(condition, code='policy_input'):
    if not condition:
        raise ScheduleRefusal(code)


def _hash(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None and int(value, 16) != 0


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _integer(value, low, high):
    _need(type(value) is int and low <= value <= high)
    return value


def _absolute(value, kind='reference'):
    _need(type(value) is str and bool(value) and Path(value).is_absolute()
        and not value.startswith('//') and '\x00' not in value and '..' not in Path(value).parts,
        'path_identity')
    return recovery._path(value, kind=kind)


def _separate(left, right):
    _need(left != right and not left.is_relative_to(right) and not right.is_relative_to(left),
        'path_identity')


def _remaining(context):
    seconds = int(context['budget'].end - time.monotonic())
    _need(seconds >= 1, 'resource_budget')
    return min(seconds, 120)


def _private_directory(path):
    recovery._path(path, kind='dir')
    item = path.lstat()
    _need(stat.S_ISDIR(item.st_mode) and item.st_uid == os.getuid()
        and stat.S_IMODE(item.st_mode) == 0o700, 'path_identity')
    recovery._protected(path.parent)
    return item.st_dev, item.st_ino


def _private_inventory(path, names, *, required=()):
    identity = _private_directory(path)
    found = set()
    with os.scandir(path) as entries:
        for entry in entries:
            _need(entry.name in names and entry.name not in found, 'scheduler_state')
            item = entry.stat(follow_symlinks=False)
            _need(stat.S_ISREG(item.st_mode) and item.st_nlink == 1
                and item.st_uid == os.getuid() and not item.st_mode & 0o077,
                'scheduler_state')
            found.add(entry.name)
    _need(set(required) <= found, 'scheduler_state')
    _need(_private_directory(path) == identity, 'path_identity')
    return identity


def _load(policy_path, policy_sha256, *, shared_budget=None):
    _need(os.name == 'posix', 'invalid_input')
    _need(_hash(policy_sha256), 'policy_pin')
    start = time.monotonic()
    budget = recovery._Budget(60, recovery.DEFAULT_BYTES) if shared_budget is None else shared_budget
    budget.check()
    path = _absolute(str(policy_path), 'file')
    raw = recovery._read(path, recovery.MAX_CONFIG_BYTES, budget)
    _need(_sha(raw) == policy_sha256, 'policy_pin')
    policy = recovery._decode(raw)
    _need(set(policy) == POLICY_FIELDS and type(policy['schema']) is int
        and policy['schema'] == 1 and policy['kind'] == 'popl-keeper-schedule')
    _integer(policy['max_seconds'], 1, 120)
    _integer(policy['max_bytes'], 1, recovery.MAX_BYTES)
    _integer(policy['max_backups'], 1, 1024)
    for key in ('max_health_age_seconds', 'max_backup_age_seconds', 'pending_max_age_seconds'):
        _integer(policy[key], 1, 31536000)
    _need(type(policy['allow_dry_run']) is bool)
    alerts._receiver(policy['receiver'])
    _need(_hash(policy['configuration_sha256']))
    expected = policy['source_files_sha256']
    _need(type(expected) is dict and set(expected) == set(SOURCE_FILES)
        and all(_hash(digest) for digest in expected.values()))
    if shared_budget is None:
        budget.end = start + policy['max_seconds']
        budget.maximum = policy['max_bytes']
    budget.check()
    working = _absolute(policy['working_directory'], 'dir')
    configuration = _absolute(policy['configuration'], 'file')
    config_path, config_raw, config, identity = recovery._configuration(configuration, budget)
    _need(_sha(config_raw) == policy['configuration_sha256'], 'configuration_identity')
    journal = recovery._path(config.get('state_path', 'var/keeper.json'), base=working)
    # Metadata only: missing or malformed journal/health bytes must reach the
    # observer, rather than making a backup prerequisite for incident delivery.
    refs = recovery._references(config, working, config_path, journal)
    directories = {key: _absolute(policy[key]) for key in
        ('scheduler_directory', 'backup_directory', 'alert_directory')}
    protected = [path, config_path, journal, journal.parent, *refs]
    for output in directories.values():
        recovery._protected(output.parent)
        for original in protected:
            _separate(output, original)
    values = list(directories.values())
    for index, output in enumerate(values):
        for other in values[index + 1:]:
            _separate(output, other)
    _need(recovery._sources(SOURCE_FILES, budget) == expected, 'source_identity')
    return {'policy': policy, 'policy_path': path, 'policy_raw': raw,
        'policy_sha256': policy_sha256, 'configuration': config_path,
        'configuration_raw': config_raw, 'working': working, 'identity': identity,
        'directories': directories, 'budget': budget}


def _stable(context):
    budget = context['budget']; policy = context['policy']
    _need(recovery._read(context['policy_path'], recovery.MAX_CONFIG_BYTES, budget)
        == context['policy_raw'], 'policy_pin')
    _need(recovery._read(context['configuration'], recovery.MAX_CONFIG_BYTES, budget)
        == context['configuration_raw'], 'configuration_identity')
    _need(recovery._sources(SOURCE_FILES, budget) == policy['source_files_sha256'],
        'source_identity')


def _selection(context):
    directory = context['directories']['scheduler_directory']
    _private_inventory(directory, {LOCK_NAME, SELECTION_NAME}, required=(LOCK_NAME, SELECTION_NAME))
    value = recovery._decode(recovery._read(directory / SELECTION_NAME, MAX_SELECTION_BYTES,
        context['budget']))
    _need(set(value) == SELECTION_FIELDS and type(value['schema']) is int and value['schema'] == 1
        and value['kind'] == 'popl-keeper-selected-backup'
        and value['policy_sha256'] == context['policy_sha256']
        and value['configuration_sha256'] == context['policy']['configuration_sha256']
        and value['identity'] == context['identity']
        and type(value['generation']) is str
        and re.fullmatch('snapshot-[0-9a-f]{32}', value['generation']) is not None
        and _hash(value['manifest_sha256'])
        and type(value['created_at']) is int and 0 <= value['created_at'] < 1 << 63,
        'scheduler_state')
    return value


def _observer_state(context):
    directory = context['directories']['alert_directory']
    _private_inventory(directory, {'alert.lock', 'state.json'}, required=('alert.lock', 'state.json'))
    try:
        alerts._load_state(directory / 'state.json', context['budget'])
    except Exception:
        raise ScheduleRefusal('observer_state') from None


def _generation_count(context):
    directory = context['directories']['backup_directory']
    before = _private_directory(directory)
    count = 0
    with os.scandir(directory) as entries:
        for entry in entries:
            context['budget'].check()
            count += 1
            _need(count <= context['policy']['max_backups'], 'capacity')
            _need(re.fullmatch('snapshot-[0-9a-f]{32}', entry.name) is not None,
                'scheduler_state')
            item = entry.stat(follow_symlinks=False)
            _need(stat.S_ISDIR(item.st_mode) and item.st_uid == os.getuid()
                and stat.S_IMODE(item.st_mode) == 0o700, 'scheduler_state')
    _need(before == _private_directory(directory), 'path_identity')
    return count


def _publish(context, value, *, previous_context=None):
    directory = context['directories']['scheduler_directory']
    before = _private_inventory(directory, {LOCK_NAME, SELECTION_NAME}, required=(LOCK_NAME,))
    _need(len(recovery._json(value)) <= MAX_SELECTION_BYTES, 'resource_budget')
    _stable(context)
    if previous_context is not None:
        _stable(previous_context)
    try:
        atomic_json(directory / SELECTION_NAME, value)
    except Exception:
        # A rename may have succeeded before a directory-fsync failure. Keep
        # whichever complete record exists; do not guess or roll it back.
        raise ScheduleRefusal('selection_publication') from None
    _need(before == _private_directory(directory), 'path_identity')
    _need(_selection(context) == value, 'selection_publication')


def _backup(context, now, previous=None):
    count = _generation_count(context)
    _need(count < context['policy']['max_backups'], 'capacity')
    _need(previous is None or now >= previous['created_at'], 'scheduler_state')
    generation = 'snapshot-' + os.urandom(16).hex()
    output = context['directories']['backup_directory'] / generation
    try:
        manifest, pin = recovery.backup(context['configuration'], output,
            working_directory=context['working'], max_bytes=context['policy']['max_bytes'],
            max_seconds=_remaining(context), now=now)
    except recovery.RecoveryRefusal as exc:
        raise ScheduleRefusal('backup_capture', exc.code) from None
    try:
        verified = recovery.verify(output, pin, context['configuration'],
            max_age_seconds=context['policy']['max_backup_age_seconds'],
            max_bytes=context['policy']['max_bytes'], max_seconds=_remaining(context), now=now)
        _need(verified == manifest, 'backup_verification')
    except recovery.RecoveryRefusal as exc:
        raise ScheduleRefusal('backup_verification', exc.code) from None
    value = {'schema': 1, 'kind': 'popl-keeper-selected-backup',
        'policy_sha256': context['policy_sha256'],
        'configuration_sha256': context['policy']['configuration_sha256'],
        'generation': generation, 'manifest_sha256': pin, 'created_at': manifest['created_at'],
        'identity': manifest['identity']}
    _publish(context, value)
    return value, count + 1


def _observe(context, selected, now):
    policy = context['policy']
    try:
        result = alerts.run_once(context['configuration'], working_directory=context['working'],
            backup_bundle=context['directories']['backup_directory'] / selected['generation'],
            backup_manifest_sha256=selected['manifest_sha256'],
            backup_config_path=context['configuration'],
            directory=context['directories']['alert_directory'],
            max_health_age_seconds=policy['max_health_age_seconds'],
            max_backup_age_seconds=policy['max_backup_age_seconds'],
            pending_max_age_seconds=policy['pending_max_age_seconds'],
            receiver=policy['receiver'], allow_dry_run=policy['allow_dry_run'],
            max_seconds=_remaining(context), max_bytes=policy['max_bytes'], now=now)
    except alerts.AlertRefusal as exc:
        raise ScheduleRefusal('observation', exc.code) from None
    context['budget'].check()
    return result


def run_once(action, policy_path, policy_sha256, *, now=None,
        previous_policy_path=None, previous_policy_sha256=None):
    """Perform one unsigned timer job; never install/start/retry another job.

    Init is exclusive, including partial attempts. Capture/verify failures leave
    the prior selection unchanged; publication errors can have an uncertain
    old/new commit and require review. Observe never recaptures or picks a folder.
    """
    _need(action in ('init', 'backup', 'observe', 'rebind'), 'invalid_input')
    _need((previous_policy_path is not None and previous_policy_sha256 is not None)
        if action == 'rebind' else previous_policy_path is None and previous_policy_sha256 is None,
        'invalid_input')
    try:
        context = _load(policy_path, policy_sha256)
        previous_context = None
        if action == 'rebind':
            previous_context = _load(previous_policy_path, previous_policy_sha256,
                shared_budget=context['budget'])
            # Only scheduling/observation settings may change. A source,
            # deployment or path migration needs a different reviewed procedure.
            fixed = ('schema', 'kind', 'configuration', 'configuration_sha256',
                'working_directory', 'scheduler_directory', 'backup_directory',
                'alert_directory', 'source_files_sha256')
            _need(all(context['policy'][key] == previous_context['policy'][key]
                for key in fixed), 'policy_input')
        current = recovery._time(now)
        directories = context['directories']
        if action == 'init':
            _need(all(not os.path.lexists(path) for path in directories.values()), 'scheduler_state')
            _stable(context)
            for path in directories.values():
                recovery._reserve(path)
        else:
            needed = ('scheduler_directory', 'backup_directory') if action == 'backup' else (
                ('scheduler_directory', 'alert_directory') if action == 'observe' else
                ('scheduler_directory',))
            for name in needed:
                _private_directory(directories[name])
            _private_inventory(directories['scheduler_directory'], {LOCK_NAME, SELECTION_NAME},
                required=(LOCK_NAME, SELECTION_NAME))
        try:
            guard = process_lock(directories['scheduler_directory'] / LOCK_NAME)
            guard.__enter__()
        except Exception:
            raise ScheduleRefusal('scheduler_lock') from None
        try:
            _private_inventory(directories['scheduler_directory'], {LOCK_NAME, SELECTION_NAME},
                required=(LOCK_NAME,))
            if action == 'rebind':
                selected = _selection(previous_context)
                selected = {**selected, 'policy_sha256': context['policy_sha256']}
                _publish(context, selected, previous_context=previous_context)
            elif action != 'init':
                selected = _selection(context)
                if action == 'observe':
                    _observer_state(context)
            if action in ('init', 'backup'):
                selected, count = _backup(context, current,
                    previous=selected if action == 'backup' else None)
            else:
                # Unrelated generations and capacity do not gate checking the
                # last explicitly selected bundle. No newest-folder fallback.
                count = None
            observation = None
            if action in ('init', 'observe'):
                _stable(context)
                observation = _observe(context, selected, current)
                _observer_state(context)
                # A late policy/source change can follow an outbox commit.
                # Refuse success, preserving that committed state for review.
                _stable(context)
            context['budget'].check()
            return {'schema': 1, 'unsigned': True, 'readiness_approved': False,
                'action': action, 'ok': observation is None or observation['ok'] is True,
                'generation': selected['generation'], 'manifest_sha256': selected['manifest_sha256'],
                'created_at': selected['created_at'], 'retained_generations': count,
                'observation': observation, 'automatic_local_selection': True,
                'independent_offhost_authentication': False, 'scheduler_initialized': True,
                'policy_rebound': action == 'rebind'}
        finally:
            guard.__exit__(None, None, None)
    except ScheduleRefusal:
        raise
    except recovery.RecoveryRefusal as exc:
        code = 'resource_budget' if exc.code == 'resource_budget' else 'path_identity'
        raise ScheduleRefusal(code, exc.code) from None
    except Exception:
        raise ScheduleRefusal('invalid_input') from None
