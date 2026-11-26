"""Public vectors, fresh wallclock and deliberate pending incident; not chain proof."""
from pathlib import Path
import copy,datetime as dt,json,os,time
from lab_common import SOURCE,RUNTIME,sha,enc as encoded,read_json,need

def private_json(path, value, uid=65534, mode=0o600):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    need(len(raw) <= 65536)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(path, mode)
    os.chown(path, uid, uid)


def read_json(path):
    raw = path.read_bytes()
    need(len(raw) <= 65536)
    return json.loads(raw)


def source_health():
    from keeper.health import source_hashes
    return source_hashes()


def observations():
    return [HEALTH['lp_execution_health']['last_confirmed'],
        HEALTH['rebalance_confirmation_health']['policy']['last_observed']]


def health(*, pending=False, bad=False):
    now = int(time.time())
    stamp = dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat()
    HEALTH.update(time=stamp, last_success_at=stamp, chain_id=CONFIG['chain_id'],
        sender=CONFIG['sender'], status='awaiting_receipt' if pending else 'dry_run_v2',
        live=False, pending=pending,
        pending_action=STATE['pending']['key'] if pending else None,
        pending_day=STATE['pending']['day'] if pending else None,
        configuration_sha256=sha(encoded(CONFIG).rstrip(b'\n')), strategy_paused=False,
        canonical_state=0, preparation_active=False, consecutive_failures=int(bad),
        skipped_buckets=0, blocked_actions=0, confirmed_reverts=0,
        active_revert_cooldowns=0, next_revert_retry_after=None)
    for observation in observations():
        observation.update(configuration_sha256=HEALTH['configuration_sha256'],
            source_files_sha256=source_health(), block_timestamp=now-2, observed_at_unix=now-1)
    private_json(Path(CONFIG['health_path']), HEALTH)


def fixture(receiver):
    global CONFIG, HEALTH, STATE, ORIGINAL_JOURNAL, POLICY_PIN, PENDING_VECTOR
    from keeper import scheduling
    work = RUNTIME / 'working'
    work.mkdir(mode=0o700)
    os.chown(work, 65534, 65534)
    runtime = work / 'runtime'
    runtime.mkdir(mode=0o700)
    os.chown(runtime, 65534, 65534)
    journal_vector = read_json(SOURCE / 'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json')
    PENDING_VECTOR = json.loads(journal_vector['journal_raw_utf8'])
    STATE = copy.deepcopy(PENDING_VECTOR)
    STATE.update(sender='0x' + '35'*20, pending=copy.deepcopy(PENDING_VECTOR['pending']), next_nonce=PENDING_VECTOR['pending']['nonce'], receipt_anchor=None, spent={})
    STATE['pending']['hash'] = '0x' + '29'*32
    CONFIG = {'chain_id': 4663, 'accounting_model': 'shared-pools-v2', 'sender': STATE['sender'],
        'contracts': copy.deepcopy(STATE['contracts']), 'accounting_version': 7, 'custody_version': 5,
        'fee_intake_version': 1, 'royalty_settlement_version': 4, 'portfolio_version': 2,
        'maintenance_policy_version': 3, 'rebalance_confirmation_version': 3,
        'execution_quality_version': 1, 'protocol_policy_version': 1, 'lp_routing_version': 3,
        'execution_price_version': 1, 'rpc_urls': ['https://offline.invalid/no-network'],
        'state_path': str(runtime / 'journal.json'), 'health_path': str(runtime / 'health.json'),
        'lock_path': str(runtime / 'keeper.lock'), 'keystore': str(work / 'keystore.secret'),
        'password_file': str(work / 'password.secret'), 'reviewed_for_live_use': False,
        'interval_seconds': 240, 'confirmations': 12, 'max_gas_limit': 24000000,
        'max_gas_price_wei': '5000000000', 'max_transaction_cost_wei': '10000000000000000',
        'max_daily_cost_wei': '50000000000000000', 'l1_fee_allowance_wei': '0',
        'receipt_fee_policy': 'included',
        'idle_compounding_budget': '0x596b344ab09a470bc468753e7bd3dc0a9fc5ebc1',
        'maintenance': {'compound': False, 'compound_idle': False, 'harvest': True,
            'minimum_liquidity': 1, 'harvest_interval_seconds': 3600},
        'metadata_refresh': {'enabled': False}, 'royalty_conversion': {'enabled': False},
        'lp_conversion': {'enabled': False}, 'principal_distribution': {'enabled': False},
        'adaptive_range': {'enabled': False}, 'bucket_overrides': {}, 'buybacks': []}
    HEALTH = copy.deepcopy(read_json(SOURCE / 'reports/ubuntu-backup-recovery-20261126/evidence/c814/model-DRY.json')['health'])
    CONFIG['code_hashes'] = {name: '0x' + '11'*32 for name in STATE['contracts']}
    for row in observations():
        CONFIG['code_hashes'].update(row['runtime_code_hashes'])
    private_json(RUNTIME / 'keeper-config.json', CONFIG)
    private_json(Path(CONFIG['state_path']), STATE)
    ORIGINAL_JOURNAL = Path(CONFIG['state_path']).read_bytes()
    for name in ('keystore.secret', 'password.secret'):
        path = work / name
        path.write_bytes(b'DISPOSABLE-NOT-A-SIGNER-SECRET\n')
        os.chmod(path, 0)
    health(pending=True, bad=True)
    policy = {'schema': 1, 'kind': 'popl-keeper-schedule',
        'configuration': str(RUNTIME / 'keeper-config.json'),
        'configuration_sha256': sha((RUNTIME / 'keeper-config.json').read_bytes()),
        'working_directory': str(work), 'scheduler_directory': str(RUNTIME / 'schedule'),
        'backup_directory': str(RUNTIME / 'backups'), 'alert_directory': str(RUNTIME / 'alerts'),
        'source_files_sha256': {name: sha((SOURCE / name).read_bytes()) for name in scheduling.SOURCE_FILES},
        'max_backups': 32, 'max_health_age_seconds': 120, 'max_backup_age_seconds': 900,
        'pending_max_age_seconds': 3600, 'receiver': receiver, 'allow_dry_run': True,
        'max_bytes': 16777216, 'max_seconds': 60}
    private_json(RUNTIME / 'policy.json', policy, uid=0, mode=0o444)
    POLICY_PIN = sha((RUNTIME / 'policy.json').read_bytes())


