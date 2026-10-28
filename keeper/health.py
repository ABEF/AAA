"""Versioned, secret-free keeper observations; never attest a running binary."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

HEALTH_SCHEMA = 2
OBSERVATION_SCHEMA = 1
SOURCE_FILES = ('keeper/monitor.py', 'keeper/ops.py', 'keeper/health.py', 'keeper/rebalance_confirmation.py',
    'zzz_ops/lp_execution.py', 'zzz_ops/abi.py', 'zzz_ops/rpc.py', 'zzz_ops/state.py')
RUNTIME_ROLES = ('access', 'pools', 'liquidity', 'balancing_router', 'pool_manager', 'state_view', 'strategy')


def source_hashes():
    """Local source-file identity only, not proof of loaded code or safe custody."""
    root = Path(__file__).resolve().parent.parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in SOURCE_FILES}


def digest(value):
    import json
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _uint(value, maximum=2**256-1):
    return type(value) is int and 0 <= value <= maximum


def _hash(value, *, prefix=True):
    return (isinstance(value, str) and re.fullmatch(('0x' if prefix else '')+'[0-9a-f]{64}', value) is not None
        and int(value[-64:],16) != 0)


def execution_reasons(data, config, *, now, max_age):
    """Check the new profile's local receipt; historical profiles stay historical."""
    version = data.get('health_schema')
    if version is not None and (type(version) is not int or version != HEALTH_SCHEMA):
        return ['unsupported_health_schema']
    quality_version=config.get('execution_quality_version',0)
    if type(quality_version) is not int or quality_version not in (0,1):
        return ['execution_health_profile_invalid']
    confirmation_version=config.get('rebalance_confirmation_version',0)
    if type(confirmation_version) is not int or confirmation_version not in (0,1):
        return ['execution_health_profile_invalid']
    if confirmation_version==1 and version!=HEALTH_SCHEMA:
        return ['execution_health_schema_required']
    if quality_version != 1:
        return []
    if type(config.get('lp_routing_version')) is not int or config['lp_routing_version'] != 1:
        return ['execution_health_profile_invalid']
    if version != HEALTH_SCHEMA:
        return ['execution_health_schema_required']
    report = data.get('lp_execution_health')
    if (not isinstance(report, dict) or type(report.get('schema')) is not int or
            report['schema'] != OBSERVATION_SCHEMA):
        return ['execution_observation_unknown']
    reasons = []
    if report.get('state') != 'observed_this_cycle':
        reasons.append('execution_observation_not_current')
    observation = report.get('last_confirmed')
    if not isinstance(observation, dict):
        return reasons+['execution_observation_unavailable']
    number, stamp, head = (observation.get(k) for k in ('block_number', 'block_timestamp', 'head_number'))
    confirmations = config.get('confirmations', 12)
    if (not _uint(number) or not _uint(head) or not _uint(stamp) or stamp == 0 or
            type(confirmations) is not int or confirmations < 1 or head-number+1 < confirmations or
            not _hash(observation.get('block_hash'))):
        reasons.append('execution_observation_anchor_invalid')
    elif now-stamp < -30 or now-stamp > min(max_age, 600):
        reasons.append('execution_observation_stale_or_future')
    observed = observation.get('observed_at_unix')
    if not _uint(observed) or now-observed < -30 or now-observed > max_age:
        reasons.append('execution_observation_read_stale_or_future')
    if observation.get('configuration_sha256') != digest(config):
        reasons.append('execution_observation_configuration_mismatch')
    if observation.get('source_files_sha256') != source_hashes():
        reasons.append('execution_observation_source_mismatch')
    if observation.get('source_identity_scope') != 'local_files_at_keeper_start_not_runtime_attestation':
        reasons.append('execution_observation_source_scope_unknown')
    runtimes = observation.get('runtime_code_hashes')
    expected = config.get('code_hashes', {})
    if (not isinstance(runtimes, dict) or set(runtimes) != set(RUNTIME_ROLES) or
            any(not _hash(runtimes.get(role)) or runtimes.get(role) != str(expected.get(role, '')).lower()
                for role in RUNTIME_ROLES)):
        reasons.append('execution_observation_runtime_mismatch')
    policy = observation.get('metadata')
    quality = policy.get('execution_quality') if isinstance(policy, dict) else None
    catalog=policy.get('execution_pools') if isinstance(policy,dict) else None
    if (not isinstance(policy, dict) or type(policy.get('version')) is not int or policy['version'] != 1 or
            policy.get('router') != config.get('contracts', {}).get('balancing_router', '').lower() or
            not _uint(policy.get('execution_revision'),2**64-1) or
            not _uint(policy.get('registry_configuration_revision'),2**64-1) or
            not _uint(policy.get('search_iterations'),12) or policy['search_iterations']<4 or
            not _uint(policy.get('quote_gas_limit'),300000) or policy['quote_gas_limit']<100000 or
            not isinstance(catalog,list) or len(catalog)>4 or any(not _hash(value) for value in catalog) or
            len(set(catalog))!=len(catalog) or policy.get('swaps_enabled') is not bool(catalog) or
            policy.get('catalog_frozen_by_wallet_review') is not False or
            not isinstance(quality, dict) or type(quality.get('version')) is not int or quality['version'] != 1 or
            quality.get('policy_owner') != config.get('contracts', {}).get('strategy', '').lower() or
            not _uint(quality.get('quality_policy_revision'), 2**64-1) or
            not _uint(quality.get('additional_loss_bps'), 1000) or
            type(quality.get('maximum_additional_loss_bps')) is not int or
            quality['maximum_additional_loss_bps'] != 1000 or
            quality.get('known_pool_fees_excluded_from_additional_limit') is not True or
            quality.get('policy_frozen_by_wallet_review') is not False):
        reasons.append('execution_observation_policy_invalid')
    return reasons


def summary(data):
    """Allowlisted public diagnostics; malformed health files cannot echo secrets."""
    report = data.get('lp_execution_health')
    state = report.get('state') if isinstance(report, dict) else None
    states = ('not_observed', 'pending_recovery', 'not_observed_this_cycle',
        'not_configured', 'observed_this_cycle', 'unavailable')
    result = {'execution_observation_state': state if state in states else 'unknown'}
    gas = data.get('gas_review')
    review = gas.get('last_review') if isinstance(gas, dict) else None
    if isinstance(review, dict):
        result['gas_review'] = {key: review.get(key) if _uint(review.get(key)) else None for key in
            ('head_number', 'estimated_gas', 'padded_gas_required', 'gas_limit_cap', 'gas_price_wei',
             'gas_price_cap_wei', 'maximum_cost_wei', 'transaction_cost_cap_wei', 'daily_cost_cap_wei')}
        reason = review.get('reason')
        result['gas_review']['reason'] = reason if reason in (None, 'estimate_or_price_unavailable',
            'gas_limit_cap', 'gas_price_cap', 'conversion_uneconomic', 'cost_cap') else 'unknown'
    return result
