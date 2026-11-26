"""Unsigned, offline keeper-journal backup and exclusive restore preparation.

Only the exact journal is packaged. Reviewed configuration and signer material
stay separate. Integrity/freshness-of-capture is not chain reconciliation,
single-writer fencing, live admission or permission to adopt restored state.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

DEFAULT_BYTES = 16 * 1024 * 1024
MAX_BYTES = 64 * 1024 * 1024
MAX_CONFIG_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = ('keeper/monitor.py', 'keeper/ops.py', 'keeper/health.py',
    'keeper/rebalance_confirmation.py', 'keeper/compound_policy.py', 'keeper/cast_process.py',
    'zzz_ops/protocol_policy.py', 'zzz_ops/lp_execution.py', 'zzz_ops/execution_price.py',
    'zzz_ops/rebalance_confirmation.py', 'zzz_ops/abi.py', 'zzz_ops/rpc.py', 'zzz_ops/state.py')
PRODUCER_FILES = ('keeper/recovery_bundle.py', 'scripts/keeper-recovery.py')
ROOT_FIELDS = frozenset(('chain_id', 'sender', 'contracts', 'accounting_model',
    'accounting_version', 'fee_intake_version', 'execution_price_version', 'bucket_cursor',
    'last', 'spent', 'retry_after', 'pending', 'next_nonce', 'receipt_anchor',
    'last_fee_observation', 'outside_rebalance_v2', 'observed_rebalance_v1',
    'observed_adjustment_v3', 'confirmation_reset_v1', 'confirmation_clear_v1',
    'adjustment_jitter_last_v3', 'conversion_turn', 'buyback_priority', 'buyback_cursor',
    'metadata_refresh', 'lp_conversion', 'royalty_conversion',
    'principal_distribution_first', 'principal_distribution_cursor'))
FLAGS = {'unsigned': True, 'live_ready': False, 'canonical_state_verified': False,
    'old_keeper_fenced': False, 'signer_material_included': False,
    'configuration_installed': False, 'service_restarted': False}
MANIFEST_FIELDS = frozenset(('schema', 'kind', 'created_at', 'configuration_raw_sha256',
    'configuration_sha256', 'identity', 'source_files_sha256', 'producer_files_sha256',
    'files', 'pending_summary', 'scope', *FLAGS))
SAFE_FAILURE = 'Keeper recovery operation refused; preserve original state and configuration.'
REFUSAL_CODES = frozenset(('invalid_input', 'trusted_pin', 'config_identity', 'release_identity',
    'backup_age_or_floor', 'source_snapshot_changed', 'output_publication', 'resource_budget',
    'journal_envelope', 'package_inventory'))


class RecoveryRefusal(ValueError):
    """Only fixed operator diagnostics; never input values or exception text."""
    def __init__(self, code):
        self.code = code if type(code) is str and code in REFUSAL_CODES else 'invalid_input'
        super().__init__(SAFE_FAILURE + ' [' + self.code + ']')


def _need(value, code='invalid_input'):
    if not value:
        raise RecoveryRefusal(code)


def _uint(value, maximum=(1 << 256) - 1):
    _need(type(value) is int and 0 <= value <= maximum)
    return value


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _hash(value, *, prefixed=False, zero=False):
    _need(type(value) is str and re.fullmatch(('0x' if prefixed else '') + '[0-9a-fA-F]{64}', value))
    _need(zero or int(value[-64:], 16) != 0)
    return value.lower()


def _address(value, *, zero=False):
    _need(type(value) is str and re.fullmatch('0x[0-9a-fA-F]{40}', value))
    _need(zero or int(value[2:], 16) != 0)
    return value.lower()


def _json(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf8')


def _pairs(items):
    result = {}
    for key, value in items:
        _need(key not in result)
        result[key] = value
    return result


def _constant(_):
    raise ValueError(SAFE_FAILURE)


def _decode(raw):
    value = json.loads(raw.decode('utf8'), object_pairs_hook=_pairs, parse_constant=_constant)
    _need(type(value) is dict)
    # Bound nested object work independently of Python's JSON recursion limit.
    pending = [(value, 0)]; nodes = 0
    while pending:
        node, depth = pending.pop(); nodes += 1
        _need(depth <= 64 and nodes <= 1000000)
        if isinstance(node, dict):
            pending.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            pending.extend((child, depth + 1) for child in node)
        elif isinstance(node, float):
            _need(node == node and abs(node) != float('inf'))
    return value


class _Budget:
    def __init__(self, seconds, maximum):
        _need(type(seconds) is int and 1 <= seconds <= 300, 'resource_budget')
        _need(type(maximum) is int and 1 <= maximum <= MAX_BYTES, 'resource_budget')
        self.end = time.monotonic() + seconds
        self.maximum = maximum

    def check(self):
        _need(time.monotonic() <= self.end, 'resource_budget')


def _path(value, *, base=None, kind='reference'):
    _need(isinstance(value, (str, Path)) and bool(str(value)) and '\x00' not in str(value))
    p = Path(value).expanduser()
    _need('..' not in p.parts)
    if os.name == 'nt':
        _need(not p.drive or p.is_absolute())
    if not p.is_absolute():
        p = (Path.cwd() if base is None else base) / p
    p = p.absolute()
    if os.name == 'nt':
        _need(not str(p).startswith(('\\\\', '//')) and len(p.drive) == 2 and p.drive[1] == ':')
        _need(all(':' not in part for part in p.parts[1:]))
    missing = False
    for item in (*reversed(p.parents), p):
        if missing:
            _need(kind == 'reference')
            continue
        try:
            st = item.lstat()
        except FileNotFoundError:
            _need(kind == 'reference' or item == p and kind == 'new')
            missing = True
            continue
        _need(not stat.S_ISLNK(st.st_mode) and not getattr(st, 'st_file_attributes', 0) &
              getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
        if item != p:
            _need(stat.S_ISDIR(st.st_mode))
    if kind == 'file':
        st = p.lstat(); _need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1)
    elif kind == 'dir':
        _need(stat.S_ISDIR(p.lstat().st_mode))
    elif kind == 'new':
        _need(not os.path.lexists(p) and p.parent.is_dir(), 'output_publication')
    return p


def _stat_identity(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def _directory_identity(st):
    return (st.st_dev, st.st_ino)


def _protected(path):
    path = _path(path, kind='dir'); st = path.lstat()
    if os.name != 'nt':
        _need(st.st_uid in (0, os.getuid()) and not st.st_mode & 0o022)
    return st


def _read(path, maximum, budget):
    path = _path(path, kind='file'); parent = _protected(path.parent); before = path.lstat()
    if os.name != 'nt':
        _need(before.st_uid in (0, os.getuid()) and not before.st_mode & 0o022)
    _need(before.st_size <= maximum, 'resource_budget')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0))
    try:
        opened = os.fstat(fd)
        _need(_stat_identity(opened) == _stat_identity(before) and stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1,
            'source_snapshot_changed')
        chunks = []; size = 0
        while True:
            budget.check(); raw = os.read(fd, min(65536, maximum + 1 - size))
            if not raw:
                break
            size += len(raw); _need(size <= maximum, 'resource_budget'); chunks.append(raw)
        _need(_stat_identity(os.fstat(fd)) == _stat_identity(before), 'source_snapshot_changed')
    finally:
        os.close(fd)
    _need(_directory_identity(_protected(path.parent)) == _directory_identity(parent) and
        _stat_identity(_path(path, kind='file').lstat()) == _stat_identity(before) and size == before.st_size,
        'source_snapshot_changed')
    budget.check()
    return b''.join(chunks)


def _sources(names, budget):
    return {name: _sha(_read(ROOT / name, MAX_CONFIG_BYTES, budget)) for name in names}


def source_hashes(budget=None):
    """Existing thirteen-file local identity; not loaded-code attestation."""
    return _sources(SOURCE_FILES, _Budget(60, DEFAULT_BYTES) if budget is None else budget)


def _semantic(config):
    # Exactly the Keeper's configuration digest: no newline and default ASCII.
    return _sha(json.dumps(config, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def _configuration(path, budget):
    p = _path(path, kind='file'); raw = _read(p, MAX_CONFIG_BYTES, budget); config = _decode(raw)
    required = {'accounting_version': 7, 'custody_version': 5, 'fee_intake_version': 1,
        'portfolio_version': 2, 'maintenance_policy_version': 3, 'rebalance_confirmation_version': 3,
        'execution_quality_version': 1, 'protocol_policy_version': 1}
    _need(all(type(config.get(k)) is int and config[k] == v for k, v in required.items()), 'config_identity')
    execution = config.get('execution_price_version', 0)
    _need(type(execution) is int and execution in (0, 1) and
          type(config.get('lp_routing_version')) is int and config['lp_routing_version'] == (3 if execution else 2), 'config_identity')
    royalty = config.get('royalty_settlement_version', 0)
    _need(type(royalty) is int and royalty in (0, 2, 3, 4), 'config_identity')
    _need(config.get('accounting_model', 'shared-pools-v2') == 'shared-pools-v2', 'config_identity')
    chain = _uint(config.get('chain_id')); _need(chain > 0)
    sender = _address(config.get('sender'))
    contracts = config.get('contracts'); _need(type(contracts) is dict and bool(contracts))
    _need(all(type(key) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,63}', key) for key in contracts))
    contracts = {key: _address(value) for key, value in contracts.items()}
    _need({'access', 'vault', 'strategy', 'fees', 'compounder', 'buyback', 'pools', 'rewards',
        'principal_exit', 'liquidity', 'balancing_router', 'pool_manager', 'state_view',
        'portfolio_policy', 'lp_balance_math', 'lp_position_executor', 'protocol_policy',
        'rebalance_confirmation'} <= set(contracts))
    identity = {'chain_id': chain, 'sender': sender, 'contracts': contracts,
        'accounting_model': 'shared-pools-v2', **required,
        'execution_price_version': execution, 'lp_routing_version': config['lp_routing_version'],
        'royalty_settlement_version': royalty}
    return p, raw, config, identity


def _references(config, working, config_path, journal):
    # Resolve with the daemon's WorkingDirectory, never the config directory.
    _need(working.is_absolute())
    values = {'health_path': str(journal.with_suffix('.health.json')), 'lock_path': 'var/keeper.lock'}
    values.update({key: config[key] for key in ('health_path', 'lock_path', 'keystore', 'password_file') if config.get(key)})
    refs = [_path(value, base=working) for value in values.values()]
    _need(len(set([config_path, journal, *refs])) == len([config_path, journal, *refs]))
    entries = []
    for p in [config_path, journal, *refs]:
        try:
            st = p.lstat()
        except FileNotFoundError:
            continue
        _need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1)
        entries.append((st.st_dev, st.st_ino))
    _need(len(entries) == len(set(entries)))
    return refs


def _no_sensitive_fields(value):
    banned = {'privatekey', 'secretkey', 'mnemonic', 'seedphrase', 'password', 'keystore',
        'rawtransaction', 'rawsignedtransaction', 'signedtransaction', 'signedenvelope', 'rpcurls'}
    todo = [value]
    while todo:
        item = todo.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                _need(re.sub('[^a-z0-9]', '', key.lower()) not in banned)
                todo.append(child)
        elif isinstance(item, list):
            todo.extend(item)
        elif isinstance(item, str):
            _need(not re.search(r'https?://', item, re.I))


def _fee(pending):
    if 'fee_review' not in pending:
        return
    fee = pending['fee_review']
    fields = {'schema', 'gas_limit', 'max_fee_per_gas', 'l1_fee_allowance_wei',
        'maximum_cost_wei', 'receipt_fee_policy'}
    _need(type(fee) is dict and type(fee.get('schema')) is int and fee['schema'] in (1, 2))
    if fee['schema'] == 2:
        fields.add('execution_fee_model')
    _need(set(fee) == fields)
    for key in ('gas_limit', 'max_fee_per_gas', 'l1_fee_allowance_wei', 'maximum_cost_wei'):
        _uint(fee[key])
    _need(fee['gas_limit'] > 0 and fee['maximum_cost_wei'] ==
        fee['gas_limit'] * fee['max_fee_per_gas'] + fee['l1_fee_allowance_wei'] + pending['value'])
    _need(fee['receipt_fee_policy'] in ('included', 'separate_l1_fee'))
    if fee['schema'] == 2:
        _need(fee['execution_fee_model'] == 'eip1559_zero_tip' and fee['receipt_fee_policy'] == 'included'
            and fee['l1_fee_allowance_wei'] == 0 and fee['max_fee_per_gas'] > 0)


def _bucket(value):
    _need(type(value) is str and re.fullmatch('[1-9][0-9]{0,77}', value) and int(value) < 1 << 256)


def _action(value):
    _need(type(value) is str and re.fullmatch(
        r'(?:(?:harvest|rebalance|compound|external_rewards|range_policy|rebalance_reset|rebalance_observation|principal_allocate|principal_distribute):[1-9][0-9]{0,77}'
        r'|(?:buyback|royalty_sync):0x[0-9a-fA-F]{40}'
        r'|(?:lp_conversion|royalty_conversion):0x[0-9a-fA-F]{40}:[1-9][0-9]{0,3}:[1-9][0-9]{0,3}'
        r'|metadata:[1-9][0-9]{0,3}:[1-9][0-9]{0,3})', value))


def _record(record, *, stored):
    fields = {'ordinal', 'token_id', 'traits_ready', 'available', 'stage'}
    if stored:
        fields |= {'observed_number', 'observed_hash', 'notification_number', 'notification_hash'}
    _need(type(record) is dict and set(record) in (fields, fields | {'lifecycle_fingerprint'}))
    _need(1 <= _uint(record['ordinal'], 1000) <= 1000 and type(record['token_id']) is str and
        re.fullmatch('0|[1-9][0-9]{0,77}', record['token_id']) and int(record['token_id']) < 1 << 256)
    _need(type(record['traits_ready']) is bool and type(record['available']) is bool)
    _uint(record['stage'], 4)
    _need((record['available'] or record['stage'] == 1) and
        (record['traits_ready'] or record['stage'] == 0 and record['available']))
    if 'lifecycle_fingerprint' in record:
        _hash(record['lifecycle_fingerprint'], prefixed=True, zero=True)
    if stored:
        for key in ('observed_number', 'notification_number'):
            _uint(record[key])
        for key in ('observed_hash', 'notification_hash'):
            _hash(record[key], prefixed=True)


def _metadata_identity(value):
    fields = {'chain_id', 'controller', 'nft'}
    _need(type(value) is dict and set(value) in (fields, fields | {'metadata_lifecycle_version', 'renderer', 'renderer_code_hash'}))
    _need(_uint(value['chain_id']) > 0)
    _address(value['controller']); _address(value['nft'])
    if 'metadata_lifecycle_version' in value:
        _need(type(value['metadata_lifecycle_version']) is int and value['metadata_lifecycle_version'] == 2)
        _address(value['renderer']); _hash(value['renderer_code_hash'], prefixed=True)


def _metadata_payload(payload, state):
    _need(type(payload) is dict and set(payload) == {'identity', 'observed_number', 'observed_hash',
        'first_ordinal', 'last_ordinal', 'maximum_age', 'records'})
    _metadata_identity(payload['identity'])
    _need(type(state.get('metadata_refresh')) is dict and payload['identity'] == state['metadata_refresh']['identity'])
    _uint(payload['observed_number']); _hash(payload['observed_hash'], prefixed=True)
    first = _uint(payload['first_ordinal'], 1000); last = _uint(payload['last_ordinal'], 1000)
    _need(1 <= first <= last and last - first < 50 and 1 <= _uint(payload['maximum_age'], 10000) <= 10000)
    _need(type(payload['records']) is list and len(payload['records']) == last - first + 1)
    for ordinal, record in zip(range(first, last + 1), payload['records']):
        _record(record, stored=False); _need(record['ordinal'] == ordinal)
        _need((payload['identity'].get('metadata_lifecycle_version') == 2) == ('lifecycle_fingerprint' in record))
    _need(len({record['token_id'] for record in payload['records']}) == len(payload['records']))


def _optional_state(value):
    for name in ('outside_rebalance_v2', 'observed_rebalance_v1', 'observed_adjustment_v3'):
        rows = value.get(name, {}); _need(type(rows) is dict and len(rows) <= 10000)
        for bucket, record in rows.items():
            _bucket(bucket)
            fields = {'identity', 'observed_at', 'next_check_at', 'execute_after'}
            if name != 'outside_rebalance_v2':
                fields.add('last_checked_at')
            _need(type(record) is dict and set(record) == fields)
            _hash(record['identity'], prefixed=True)
            for key in fields - {'identity'}:
                _uint(record[key], (1 << 64) - 1)
            observed, check, execute = (record[k] for k in ('observed_at', 'next_check_at', 'execute_after'))
            if name == 'outside_rebalance_v2':
                valid = execute == 0 and check == observed + 3600 or check == 0 and 60 <= execute - observed <= 600
            else:
                last = record['last_checked_at']
                cadence = 1 <= check - last <= 240 if name == 'observed_adjustment_v3' else check - last in (240, 300)
                valid = last >= observed and cadence and (execute == 0 or
                    60 <= execute - observed <= (300 if name == 'observed_adjustment_v3' else 600))
            _need(valid)
    resets = value.get('confirmation_reset_v1', {}); _need(type(resets) is dict and len(resets) <= 10000)
    for bucket, needed in resets.items():
        _bucket(bucket); _need(needed is True)
    clears = value.get('confirmation_clear_v1', {}); _need(type(clears) is dict and len(clears) <= 10000)
    for bucket, record in clears.items():
        _bucket(bucket)
        _need(type(record) is dict and set(record) == {'number', 'hash', 'timestamp', 'nonce', 'awaiting_healthy_read'})
        _hash(record['hash'], prefixed=True); _need(type(record['awaiting_healthy_read']) is bool)
        for key in ('number', 'timestamp', 'nonce'):
            _uint(record[key])
    jitter = value.get('adjustment_jitter_last_v3', {}); _need(type(jitter) is dict and len(jitter) <= 10000)
    for bucket, seconds in jitter.items():
        _bucket(bucket); _need(60 <= _uint(seconds, 300) <= 300)
    for name in ('conversion_turn', 'buyback_cursor', 'principal_distribution_cursor'):
        if name in value:
            _uint(value[name], {'conversion_turn': 2, 'buyback_cursor': 32, 'principal_distribution_cursor': 1001}[name])
            _need(name != 'principal_distribution_cursor' or value[name] >= 1)
    for name in ('buyback_priority', 'principal_distribution_first'):
        if name in value:
            _need(type(value[name]) is bool)
    observation = value.get('last_fee_observation')
    if observation is not None:
        _need(type(observation) is dict and set(observation) == {'transaction', 'reported_price_wei',
            'execution_price_wei', 'gas_used', 'l1_fee_wei', 'receipt_fee_policy', 'cost_wei'})
        _hash(observation['transaction'], prefixed=True)
        _need(observation['receipt_fee_policy'] in ('included', 'separate_l1_fee'))
        for key in ('reported_price_wei', 'execution_price_wei', 'gas_used', 'l1_fee_wei', 'cost_wei'):
            _uint(observation[key])
    for name in ('lp_conversion', 'royalty_conversion'):
        if name not in value:
            continue
        row = value[name]
        _need(type(row) is dict and set(row) == {'identity', 'asset', 'ordinal', 'next_first'})
        identity = row['identity']; fields = {'ledger', 'nft', 'assets'}
        _need(type(identity) is dict and set(identity) in (fields, fields | {'profile'}, fields | {'profile', 'executor'}))
        _address(identity['ledger']); _address(identity['nft'])
        _need(type(identity['assets']) is list and 1 <= len(identity['assets']) <= 16)
        for asset in identity['assets']:
            _address(asset)
        if 'profile' in identity:
            _need(identity['profile'] in ('v3_wrapper_configurable', 'v4_native'))
        if 'executor' in identity:
            _address(identity['executor'])
        _need(_uint(row['asset']) < len(identity['assets']) and 1 <= _uint(row['ordinal'], 1000) <= 1000
            and type(row['next_first']) is bool)
    if 'metadata_refresh' in value:
        row = value['metadata_refresh']
        _need(type(row) is dict and set(row) == {'identity', 'cursor', 'next_first', 'notified'})
        _metadata_identity(row['identity']); _need(1 <= _uint(row['cursor'], 1000) <= 1000 and type(row['next_first']) is bool)
        _need(type(row['notified']) is dict and len(row['notified']) <= 1000)
        for ordinal, record in row['notified'].items():
            _record(record, stored=True); _need(ordinal == str(record['ordinal']))
            _need(record['notification_number'] >= record['observed_number'] and
                (row['identity'].get('metadata_lifecycle_version') == 2) == ('lifecycle_fingerprint' in record))


def _state(raw, identity):
    value = _decode(raw); _need(set(value) <= ROOT_FIELDS, 'journal_envelope')
    _need({'chain_id', 'sender', 'contracts', 'accounting_model', 'accounting_version',
        'fee_intake_version', 'bucket_cursor', 'last', 'spent', 'pending', 'next_nonce', 'receipt_anchor'} <= set(value), 'journal_envelope')
    _no_sensitive_fields(value)
    _need(value.get('chain_id') == identity['chain_id'] and type(value.get('chain_id')) is int and
          value.get('sender') == identity['sender'] and value.get('contracts') == identity['contracts'] and
          value.get('accounting_model') == 'shared-pools-v2')
    for key in ('accounting_version', 'fee_intake_version'):
        _need(type(value.get(key)) is int and value[key] == identity[key])
    _need(type(value.get('execution_price_version', 0)) is int and
          value.get('execution_price_version', 0) == identity['execution_price_version'])
    _uint(value.get('bucket_cursor'))
    for key in ('last', 'spent', 'retry_after'):
        counters = value.get(key, {}) if key == 'retry_after' else value.get(key)
        _need(type(counters) is dict)
        for name, amount in counters.items():
            _need(type(name) is str and bool(name) and len(name) <= 256); _uint(amount)
            if key == 'spent':
                _need(dt.date.fromisoformat(name).isoformat() == name)
            else:
                _action(name)
    nonce = value.get('next_nonce')
    if nonce is not None:
        _uint(nonce)
    anchor = value.get('receipt_anchor')
    if anchor is not None:
        _need(type(anchor) is dict and set(anchor) == {'number', 'hash', 'timestamp', 'nonce'})
        for key in ('number', 'timestamp', 'nonce'):
            _uint(anchor[key])
        _hash(anchor['hash'], prefixed=True); _need(nonce == anchor['nonce'] + 1)
    pending = value.get('pending')
    if pending is not None:
        _need(type(pending) is dict and {'key', 'nonce', 'to', 'data', 'value', 'day', 'hash'} <= set(pending)
            and set(pending) <= {'key', 'nonce', 'to', 'data', 'value', 'day', 'hash', 'fee_review', 'metadata_observation'})
        _action(pending['key'])
        _uint(pending['nonce']); _uint(pending['value']); _address(pending['to'])
        _need(nonce is None or nonce == pending['nonce'])
        _need(type(pending['data']) is str and re.fullmatch(r'0x(?:[0-9a-fA-F]{2}){4,}', pending['data']))
        _need(dt.date.fromisoformat(pending['day']).isoformat() == pending['day'])
        if pending['hash'] is not None:
            _hash(pending['hash'], prefixed=True)
        _fee(pending)
        if 'metadata_observation' in pending:
            _metadata_payload(pending['metadata_observation'], value)
    _optional_state(value)
    return value


def _summary(state):
    pending = state.get('pending')
    return {'present': pending is not None, 'hash_present': pending is not None and pending.get('hash') is not None,
        'fee_review_present': pending is not None and pending.get('fee_review') is not None,
        'manual_fee_review_required': pending is not None and 'fee_review' not in pending,
        'next_nonce': state.get('next_nonce')}


def _time(now):
    return _uint(int(time.time()) if now is None else now, (1 << 63) - 1)


def _sync(path):
    if os.name != 'nt':
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _reserve(path):
    path = _path(path, kind='new'); parent = _protected(path.parent)
    if os.name != 'nt':
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            _need(_directory_identity(os.fstat(fd)) == _directory_identity(parent))
            os.mkdir(path.name, 0o700, dir_fd=fd)
        finally:
            os.close(fd)
    else:
        path.mkdir(mode=0o700)
    own = _protected(path)
    _need(_directory_identity(_protected(path.parent)) == _directory_identity(parent))
    _sync(path.parent)
    return path, (_directory_identity(parent), _directory_identity(own))


def _output_identity(path, reservation):
    parent, own = reservation
    _need(_directory_identity(_protected(path.parent)) == parent and
        _directory_identity(_protected(path)) == own, 'output_publication')


def _write(path, raw, budget, reservation):
    budget.check()
    _output_identity(path.parent, reservation)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    if os.name != 'nt':
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            _need(_directory_identity(os.fstat(directory)) == reservation[1])
            fd = os.open(path.name, flags, 0o600, dir_fd=directory)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.fsync(directory)
        finally:
            os.close(directory)
    else:
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    _output_identity(path.parent, reservation); budget.check()


def _overlap(output, inputs):
    _need(all(output != p and not p.is_relative_to(output) for p in inputs), 'output_publication')


def _capture(config_path, working_directory, budget):
    working = _path(working_directory, kind='dir')
    config_path, config_raw, config, identity = _configuration(config_path, budget)
    journal = _path(config.get('state_path', 'var/keeper.json'), base=working, kind='file')
    refs = _references(config, working, config_path, journal)
    raw = _read(journal, budget.maximum, budget); state = _state(raw, identity)
    sources = source_hashes(budget)
    return config_path, config_raw, config, identity, journal, refs, raw, state, sources


def _check_capture(capture, budget, producer):
    config_path, config_raw, config, identity, journal, refs, raw, state, sources = capture
    _need(_read(config_path, MAX_CONFIG_BYTES, budget) == config_raw and
          _read(journal, budget.maximum, budget) == raw and source_hashes(budget) == sources and
          _sources(PRODUCER_FILES, budget) == producer, 'source_snapshot_changed')


def backup(config_path, output, *, working_directory, max_bytes=DEFAULT_BYTES, max_seconds=60, now=None):
    """Point-in-time stable snapshot; neither stop/fence nor claim latest state."""
    stage = 'invalid_input'
    try:
        budget = _Budget(max_seconds, max_bytes)
        capture = _capture(config_path, working_directory, budget)
        cfg_path, cfg_raw, config, identity, journal, refs, raw, state, sources = capture
        output = _path(output, kind='new'); _overlap(output, [cfg_path, journal, *refs])
        _need(not output.is_relative_to(journal.parent), 'output_publication')
        manifest = {'schema': 1, 'kind': 'popl-keeper-recovery', 'created_at': _time(now),
            'configuration_raw_sha256': _sha(cfg_raw), 'configuration_sha256': _semantic(config),
            'identity': identity, 'source_files_sha256': sources,
            'producer_files_sha256': _sources(PRODUCER_FILES, budget),
            'files': [{'path': 'journal.json', 'bytes': len(raw), 'sha256': _sha(raw)}],
            'pending_summary': _summary(state), **FLAGS,
            'scope': 'stable_point_in_time_bytes_not_latest_chain_state_or_runtime_attestation'}
        encoded = _json(manifest); _need(len(encoded) <= MAX_MANIFEST_BYTES and len(raw) + len(encoded) <= max_bytes, 'resource_budget')
        _check_capture(capture, budget, manifest['producer_files_sha256'])
        stage = 'output_publication'
        output, reservation = _reserve(output); _write(output / 'journal.json', raw, budget, reservation)
        _check_capture(capture, budget, manifest['producer_files_sha256'])
        _write(output / 'manifest.json', encoded, budget, reservation)
        return manifest, _sha(encoded)
    except RecoveryRefusal:
        raise
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError, UnicodeError):
        raise RecoveryRefusal(stage) from None


def _inventory(folder, budget):
    expected = {'manifest.json', 'journal.json'}; names = set()
    with os.scandir(folder) as entries:
        for entry in entries:
            budget.check(); _need(entry.name in expected and entry.name not in names, 'package_inventory')
            names.add(entry.name)
    _need(names == expected, 'package_inventory')


def _verified(bundle, manifest_sha256, config_path, *, max_age_seconds, minimum_created_at,
        minimum_next_nonce, budget, now):
    _need(type(manifest_sha256) is str and re.fullmatch('[0-9a-f]{64}', manifest_sha256)
        and int(manifest_sha256, 16) != 0, 'trusted_pin')
    folder = _path(bundle, kind='dir')
    _inventory(folder, budget)
    cfg_path, cfg_raw, config, identity = _configuration(config_path, budget)
    raw = _read(folder / 'manifest.json', MAX_MANIFEST_BYTES, budget)
    _need(_sha(raw) == manifest_sha256, 'trusted_pin')
    manifest = _decode(raw)
    _need(set(manifest) == MANIFEST_FIELDS and type(manifest['schema']) is int and manifest['schema'] == 1
        and manifest['kind'] == 'popl-keeper-recovery' and all(manifest.get(k) is v for k, v in FLAGS.items())
        and manifest['scope'] == 'stable_point_in_time_bytes_not_latest_chain_state_or_runtime_attestation')
    _need(manifest['configuration_raw_sha256'] == _sha(cfg_raw) and
          manifest['configuration_sha256'] == _semantic(config) and _json(manifest['identity']) == _json(identity), 'config_identity')
    _need(manifest['source_files_sha256'] == source_hashes(budget), 'release_identity')
    producer = manifest['producer_files_sha256']
    _need(type(producer) is dict and set(producer) == set(PRODUCER_FILES))
    for digest in producer.values():
        _hash(digest)
    created = _uint(manifest['created_at'], (1 << 63) - 1); current = _time(now)
    _uint(max_age_seconds, (1 << 63) - 1); _need(max_age_seconds > 0)
    _uint(minimum_created_at, (1 << 63) - 1)
    _need(minimum_created_at <= created <= current and current - created <= max_age_seconds, 'backup_age_or_floor')
    rows = manifest['files']
    _need(type(rows) is list and len(rows) == 1 and type(rows[0]) is dict and
          set(rows[0]) == {'path', 'bytes', 'sha256'} and rows[0]['path'] == 'journal.json')
    row = rows[0]; _uint(row['bytes'], max_bytes := budget.maximum); _hash(row['sha256'])
    _need(row['bytes'] > 0 and row['bytes'] + len(raw) <= max_bytes, 'resource_budget')
    journal_raw = _read(folder / 'journal.json', max_bytes, budget)
    _need(len(journal_raw) == row['bytes'] and _sha(journal_raw) == row['sha256'], 'package_inventory')
    state = _state(journal_raw, identity); _need(_json(manifest['pending_summary']) == _json(_summary(state)))
    if minimum_next_nonce is not None:
        _uint(minimum_next_nonce); _need(state.get('next_nonce') is not None and state['next_nonce'] >= minimum_next_nonce, 'backup_age_or_floor')
    _need(_read(cfg_path, MAX_CONFIG_BYTES, budget) == cfg_raw and
        _read(folder / 'manifest.json', MAX_MANIFEST_BYTES, budget) == raw and
        _read(folder / 'journal.json', max_bytes, budget) == journal_raw and
        manifest['source_files_sha256'] == source_hashes(budget), 'source_snapshot_changed')
    _inventory(folder, budget)
    return manifest, journal_raw, cfg_path


def verify(bundle, manifest_sha256, config_path, *, max_age_seconds, minimum_created_at=0,
        minimum_next_nonce=None, max_bytes=DEFAULT_BYTES, max_seconds=60, now=None):
    """Authenticate selected bytes/config/source and capture age, never chain truth."""
    stage = 'package_inventory'
    try:
        budget = _Budget(max_seconds, max_bytes)
        manifest, _, _ = _verified(bundle, manifest_sha256, config_path, max_age_seconds=max_age_seconds,
            minimum_created_at=minimum_created_at, minimum_next_nonce=minimum_next_nonce, budget=budget, now=now)
        return manifest
    except RecoveryRefusal:
        raise
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError, UnicodeError):
        raise RecoveryRefusal(stage) from None


def restore(bundle, manifest_sha256, config_path, output, *, max_age_seconds, minimum_created_at=0,
        minimum_next_nonce=None, max_bytes=DEFAULT_BYTES, max_seconds=60, now=None):
    """Write exact state and unsigned plan into a fresh folder; never installs."""
    stage = 'package_inventory'
    try:
        budget = _Budget(max_seconds, max_bytes)
        options = {'max_age_seconds': max_age_seconds, 'minimum_created_at': minimum_created_at,
            'minimum_next_nonce': minimum_next_nonce, 'budget': budget, 'now': now}
        manifest, journal_raw, cfg_path = _verified(bundle, manifest_sha256, config_path, **options)
        source = _path(bundle, kind='dir'); output = _path(output, kind='new')
        _need(not output.is_relative_to(source), 'output_publication'); _overlap(output, [source, cfg_path])
        plan = {'schema': 1, 'kind': 'popl-keeper-restore-plan', 'manifest_sha256': manifest_sha256,
            'journal': {'path': 'keeper-state.json', 'bytes': len(journal_raw), 'sha256': _sha(journal_raw)},
            'configuration_raw_sha256': manifest['configuration_raw_sha256'],
            'configuration_sha256': manifest['configuration_sha256'], 'identity': manifest['identity'],
            'pending_summary': manifest['pending_summary'], **FLAGS,
            'required_operator_review': ['fence old keeper and signer descendants including restart paths',
                'preserve and reconcile original pending transaction; never resend ambiguous intent',
                'review actual canonical nonce receipt anchor and original captured fee accounting',
                'supply separately secured reviewed configuration and signer material',
                'review new runtime path mapping and provider before adoption',
                'use matching release and dry-run recovery before separately authorized live operation']}
        encoded = _json(plan)
        _need(len(journal_raw) + len(encoded) <= max_bytes and len(encoded) <= MAX_MANIFEST_BYTES, 'resource_budget')
        stage = 'output_publication'
        output, reservation = _reserve(output); _write(output / 'keeper-state.json', journal_raw, budget, reservation)
        current, current_raw, _ = _verified(bundle, manifest_sha256, config_path, **options)
        _need(current == manifest and current_raw == journal_raw, 'source_snapshot_changed')
        _write(output / 'RESTORE_PLAN.json', encoded, budget, reservation)
        return plan, _sha(encoded)
    except RecoveryRefusal:
        raise
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError, UnicodeError):
        raise RecoveryRefusal(stage) from None
