"""Read-only keeper readiness/health checks and secret-free recovery snapshots.

These commands never sign, repair state, replace transactions or authorize a
second signer. Snapshot hashes detect corruption, not malicious replacement.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from keeper.monitor import Keeper, error_context, positive, rpc_quantity
from keeper.health import execution_reasons, observe_confirmation_health, summary as health_summary
from zzz_ops.state import read_json


def _read_required_json(path):
    # Preserve missing-file behavior while sharing the journal's strict parser.
    # Ambiguous diagnostics/backups must not pass by selecting a final duplicate.
    missing = object()
    value = read_json(path,missing)
    if value is missing: raise FileNotFoundError('Required keeper JSON input is missing')
    if not isinstance(value,dict): raise ValueError('Keeper JSON input must be an object')
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def timestamp(value):
    if not isinstance(value,str): raise ValueError('Missing timestamp')
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ValueError('Timestamp must be UTC')
    return parsed.timestamp()


def health_check(config, *, max_age=1800, allow_dry_run=False, now=None):
    positive(max_age,'max_age')
    path = Path(config.get('health_path',str(Path(config.get('state_path','var/keeper.json')).with_suffix('.health.json'))))
    data = _read_required_json(path)
    now = time.time() if now is None else now
    age = now-timestamp(data.get('time'))
    reasons = []
    if age < -30 or age > max_age: reasons.append('heartbeat_stale_or_future')
    if data.get('chain_id') != config['chain_id'] or data.get('sender') != config['sender'].lower():
        reasons.append('deployment_identity_mismatch')
    if data.get('configuration_sha256') != digest(config):
        reasons.append('configuration_mismatch')
    reasons.extend(execution_reasons(data,config,now=now,max_age=max_age))
    expected = 'dry_run' if allow_dry_run else 'healthy'
    if config.get('execution_quality_version',0) == 1 or config.get('rebalance_confirmation_version',0) in (1,2):expected += '_v2'
    if data.get('status') != expected or data.get('live') is not (not allow_dry_run): reasons.append('maintenance_not_healthy')
    for field in ('pending','strategy_paused'):
        if data.get(field) is not False: reasons.append(field)
    # Preparation is an intentional restriction, not a failed keeper. Unknown
    # legacy health records still cannot assert compatibility with this source.
    lifecycle = data.get('canonical_state')
    if type(lifecycle) is not int or lifecycle not in range(5): reasons.append('canonical_state_unknown')
    elif lifecycle != 0: reasons.append('canonical_lifecycle_locked')
    if lifecycle == 0 and type(data.get('preparation_active')) is not bool: reasons.append('preparation_state_unknown')
    for field in ('skipped_buckets','blocked_actions','consecutive_failures','confirmed_reverts'):
        if type(data.get(field)) is not int or data[field] != 0: reasons.append(field)
    cooldowns = data.get('active_revert_cooldowns')
    retry_after = data.get('next_revert_retry_after')
    if (type(cooldowns) is not int or cooldowns < 0 or 'next_revert_retry_after' not in data or
            (cooldowns == 0 and retry_after is not None) or
            (cooldowns > 0 and (type(retry_after) is not int or retry_after <= 0))):
        reasons.append('revert_cooldown_state_unknown')
    elif cooldowns:
        reasons.append('reverted_actions_in_cooldown')
    if data.get('last_success_at') is None:
        reasons.append('no_successful_cycle_yet')
    else:
        success_age = now-timestamp(data['last_success_at'])
        if success_age < -30 or success_age > max_age: reasons.append('last_success_stale_or_future')
    return {'ok':not reasons,'reasons':reasons,'heartbeat_age_seconds':round(age,3),
            'preparation_active':data.get('preparation_active'),
            'canonical_state':lifecycle,
            'active_revert_cooldowns':cooldowns,'next_revert_retry_after':retry_after,
            'health_schema':data.get('health_schema') if type(data.get('health_schema')) is int else None,
            **health_summary(data),
            'scope':'health_file_only; use an off-host scheduler and alert receiver'}


def preflight(config, *, rpc=None):
    """Check restored state against current chain without changing it or signing."""
    if not Path(config.get('state_path','var/keeper.json')).is_file(): raise ValueError('Recovery state is missing')
    keeper = Keeper(config,rpc=rpc)
    reasons = []
    if config.get('reviewed_for_live_use') is not True: reasons.append('configuration_not_reviewed')
    if keeper.fee_policy == 'unverified': reasons.append('fee_policy_unverified')
    if keeper.fee_policy == 'separate_l1_fee': positive(config.get('l1_fee_allowance_wei'),'l1_fee_allowance_wei')
    if keeper.state.get('next_nonce') is None: reasons.append('nonce_checkpoint_missing')
    if keeper.state.get('next_nonce') not in (None,0) and keeper.state.get('receipt_anchor') is None:
        reasons.append('receipt_checkpoint_missing')
    keeper._validate_code_hashes()
    keeper._validate_accounting_version()
    head,_ = keeper._head()
    keeper._validate_checkpoint()
    if keeper.view('access','isSealed()') != 1: reasons.append('protocol_not_sealed')
    if keeper.view('access','keepers(address)',keeper.sender) != 1: reasons.append('keeper_not_authorized')
    if keeper.view('access','paused()') != 0: reasons.append('protocol_paused')
    preparing = keeper.preparation_active()
    if preparing: reasons.append('canonical_preparation_active')
    lifecycle = keeper.canonical_state()
    if lifecycle != 0: reasons.append('canonical_lifecycle_locked')
    expected = keeper.state.get('next_nonce')
    latest = rpc_quantity(keeper.rpc.call('eth_getTransactionCount',[keeper.sender,'latest']),'latest nonce')
    pending = rpc_quantity(keeper.rpc.call('eth_getTransactionCount',[keeper.sender,'pending']),'pending nonce')
    if keeper.state.get('pending') is not None: reasons.append('pending_intent_requires_reconciliation')
    if expected != latest or expected != pending: reasons.append('nonce_reconciliation_required')
    balance = rpc_quantity(keeper.rpc.call('eth_getBalance',[keeper.sender,'latest']),'balance')
    if balance < positive(config['max_transaction_cost_wei'],'max_transaction_cost_wei'):
        reasons.append('balance_below_transaction_budget')
    confirmation = None
    if keeper.rebalance_confirmation.version in (1,2):
        # Pending recovery must not acquire a dependency on a new policy read.
        # Otherwise validate the gate even before any bucket leaves cooldown.
        if keeper.state.get('pending') is not None:
            confirmation = {'schema':1,'state':'pending_recovery','last_observed':None,'last_error':None}
        else:
            confirmation = observe_confirmation_health(keeper)
            if confirmation['state']=='stopped': reasons.append('rebalance_confirmation_stopped')
            elif confirmation['state']=='incompatible_cadence': reasons.append('rebalance_confirmation_cadence_incompatible')
            elif confirmation['state']!='observed_this_cycle': reasons.append('rebalance_confirmation_unavailable')
    # Recheck the existing anchor after the RPC calls; this is still a point-in-time observation.
    keeper._validate_checkpoint()
    return {'ok':not reasons,'reasons':reasons,'chain_id':keeper.chain,'head':head,'preparation_active':preparing,'canonical_state':lifecycle,
            'expected_nonce':expected,'latest_nonce':latest,'pending_nonce':pending,
            'rebalance_confirmation_policy':confirmation,
            'scope':'read_only_point_in_time; not production approval or multi-host fencing'}


def create_snapshot(config, output):
    if not Path(config.get('state_path','var/keeper.json')).is_file(): raise ValueError('Recovery state is missing')
    keeper = Keeper(config)  # Parse/validate one atomic state version; no RPC or signer calls.
    if keeper.state.get('next_nonce') is None: raise ValueError('Snapshot requires initialized state')
    # Only keeper state is copied. Never copy RPC URLs, password, keystore or config.
    payload = {'schema':1,'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
               'config_sha256':digest(config),'state':keeper.state}
    envelope = {'payload':payload,'sha256':digest(payload)}
    path = Path(output)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name = tempfile.mkstemp(prefix='.keeper-snapshot-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:
            json.dump(envelope,handle,sort_keys=True,indent=2)
            handle.write('\n');handle.flush();os.fsync(handle.fileno())
        # Exclusive, atomic publication. Never overwrite a state/config/old backup.
        os.link(name,path)
        if hasattr(os,'O_DIRECTORY'):
            directory = os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try: os.fsync(directory)
            finally: os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)
    return {'ok':True,'sha256':envelope['sha256'],'pending':bool(keeper.state.get('pending')),
            'scope':'local_snapshot; copy off-host and validate freshness before restoration'}


def verify_snapshot(config, path, *, max_age=3600, now=None):
    positive(max_age,'max_age')
    data = _read_required_json(path)
    payload = data['payload']
    if payload.get('schema') != 1 or digest(payload) != data.get('sha256'): raise ValueError('Snapshot integrity mismatch')
    state = payload['state']
    if state['chain_id'] != config['chain_id'] or state['sender'] != config['sender'].lower() or \
            state['contracts'] != {k:v.lower() for k,v in config['contracts'].items()}:
        raise ValueError('Snapshot belongs to another deployment')
    age = (time.time() if now is None else now)-timestamp(payload['created_at'])
    reasons = []
    if age < -30 or age > max_age: reasons.append('snapshot_stale_or_future')
    if payload.get('config_sha256') != digest(config): reasons.append('configuration_changed_requires_review')
    return {'ok':not reasons,'reasons':reasons,'sha256':data['sha256'],'age_seconds':round(age,3),
            'scope':'integrity_and_age_only; not authenticated, not proof of chain freshness'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    sub = parser.add_subparsers(dest='command',required=True)
    health = sub.add_parser('health');health.add_argument('--max-age',type=int,default=1800)
    health.add_argument('--allow-dry-run',action='store_true')
    sub.add_parser('preflight')
    snapshot = sub.add_parser('snapshot');snapshot.add_argument('--output',required=True)
    verify = sub.add_parser('verify-snapshot');verify.add_argument('--input',required=True)
    verify.add_argument('--max-age',type=int,default=3600)
    args = parser.parse_args()
    try:
        config = _read_required_json(args.config)
        if args.command == 'health': report = health_check(config,max_age=args.max_age,allow_dry_run=args.allow_dry_run)
        elif args.command == 'preflight': report = preflight(config)
        elif args.command == 'snapshot': report = create_snapshot(config,args.output)
        else: report = verify_snapshot(config,args.input,max_age=args.max_age)
    except Exception as exc:
        report = {'ok':False,'reasons':['check_unavailable'],**error_context(exc)}
    print(json.dumps(report,sort_keys=True))
    return 0 if report['ok'] else 1


if __name__ == '__main__': sys.exit(main())
