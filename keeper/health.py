"""Versioned, secret-free keeper observations; never attest a running binary."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import time
from keeper.rebalance_confirmation import CHECK_SECONDS

HEALTH_SCHEMA = 2
OBSERVATION_SCHEMA = 1
SOURCE_FILES = ('keeper/monitor.py', 'keeper/ops.py', 'keeper/health.py', 'keeper/rebalance_confirmation.py',
    'keeper/compound_policy.py',
    'zzz_ops/protocol_policy.py', 'zzz_ops/lp_execution.py', 'zzz_ops/rebalance_confirmation.py', 'zzz_ops/abi.py', 'zzz_ops/rpc.py', 'zzz_ops/state.py')
RUNTIME_ROLES = ('access', 'pools', 'liquidity', 'balancing_router', 'pool_manager', 'state_view', 'strategy')
CONFIRMATION_RUNTIME_ROLES = ('access', 'strategy', 'vault', 'rebalance_confirmation', 'idle_compounding_budget')
CONFIRMATION_SCOPE = 'latest_canonical_policy_only_not_continuous_evidence'


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


def _confirmation_bindings(config):
    from zzz_ops.abi import address
    contracts = config.get('contracts', {})
    access, strategy, vault, helper = (address(contracts.get(role)) for role in
        ('access', 'strategy', 'vault', 'rebalance_confirmation'))
    budget = address(config.get('idle_compounding_budget'))
    result={'strategy_access':access, 'strategy_helper':helper, 'helper_strategy':strategy,
        'helper_access':access, 'vault_budget':budget, 'budget_vault':vault, 'budget_access':access,
        'access_strategy':strategy, 'access_vault':vault}
    if config.get('rebalance_confirmation_version')==3:
        policy=address(contracts.get('portfolio_policy'))
        result.update(strategy_portfolio_policy=policy,portfolio_policy_strategy=strategy,portfolio_policy_access=access)
    return result


def _confirmation_roles(config):
    return CONFIRMATION_RUNTIME_ROLES+(('portfolio_policy',) if config.get('rebalance_confirmation_version')==3 else ())+(
        ('protocol_policy',) if config.get('accounting_version')==6 else ())


def _confirmation_capabilities(config):
    result={role:config['rebalance_confirmation_version'] for role in
        ('strategy','rebalance_confirmation','idle_compounding_budget')}
    if config.get('rebalance_confirmation_version')==3:
        result.update(portfolio_policy=2 if config.get('accounting_version')==6 else 1,budget_compounding=4)
    if config.get('accounting_version')==6:result['protocol_policy']=1
    return result


def observe_confirmation_health(keeper, previous=None):
    """Fresh policy-only latest reads; diagnostic metadata never authorizes work.

    The caller must skip this dependency while recovering a saved intent. Gap0
    is an intentional maintenance stop, not a reason to block independent fees.
    """
    from keeper.monitor import error_context, rpc_hash, rpc_quantity
    from zzz_ops.rpc import RpcError
    report = {'schema':OBSERVATION_SCHEMA, 'state':'not_configured',
        'last_observed':previous.get('last_observed') if isinstance(previous,dict) else None, 'last_error':None}
    if keeper.rebalance_confirmation.version not in (1,2,3):
        return report
    try:
        identity = digest(keeper.config)
        if identity != keeper.configuration_sha256:
            raise RpcError('Loaded confirmation configuration changed')
        # validate() checks actual runtime pins, fixed Strategy/helper/Budget
        # bindings and capabilities without condition(), prices or bucket reads.
        policy = keeper.rebalance_confirmation.validate()
        header = keeper.rpc.call('eth_getBlockByNumber',[hex(policy['block_number']),False])
        if (not isinstance(header,dict) or
                rpc_quantity(header.get('number'),'confirmation observation number') != policy['block_number'] or
                rpc_hash(header.get('hash'),'confirmation observation hash') != policy['block_hash'] or
                rpc_quantity(header.get('timestamp'),'confirmation observation timestamp',minimum=1) != policy['block_timestamp']):
            raise RpcError('Confirmation observation anchor changed')
        if digest(keeper.config) != identity:
            raise RpcError('Confirmation configuration changed during observation')
        observed_at = int(time.time())
        if observed_at-policy['block_timestamp'] < -30 or observed_at-policy['block_timestamp'] > 600:
            raise RpcError('Confirmation observation is stale or in the future')
        observed = {**policy, 'observed_at_unix':observed_at, 'anchor_scope':CONFIRMATION_SCOPE,
            'configuration_sha256':identity, 'source_files_sha256':keeper.source_files_sha256,
            'source_identity_scope':'local_files_at_keeper_start_not_runtime_attestation',
            'runtime_code_hashes':{role:keeper.config['code_hashes'][role].lower()
                for role in _confirmation_roles(keeper.config)},
            'validated_bindings':_confirmation_bindings(keeper.config),
            'validated_capabilities':_confirmation_capabilities(keeper.config)}
        gap = policy['maximum_gap_seconds']
        report.update(state='stopped' if gap==0 else 'incompatible_cadence' if gap<CHECK_SECONDS else 'observed_this_cycle',
            last_observed=observed)
    except (RpcError,ValueError,TypeError,KeyError) as exc:
        report.update(state='unavailable',last_error=error_context(exc))
    return report


def confirmation_reasons(data, config, *, now, max_age):
    """Require fresh confirmation evidence independently of execution quality."""
    if config.get('rebalance_confirmation_version',0) not in (1,2,3):
        return []
    interval = config.get('interval_seconds')
    fresh=config['rebalance_confirmation_version']==3
    if (type(config.get('accounting_version')) is not int or config['accounting_version'] not in ((5,6) if fresh else (4,)) or
            config.get('accounting_version')==6 and (type(config.get('protocol_policy_version')) is not int or config['protocol_policy_version']!=1) or
            type(config.get('maintenance_policy_version')) is not int or config['maintenance_policy_version'] != (3 if fresh else 2) or
            fresh and (type(config.get('portfolio_version')) is not int or config['portfolio_version']!=(2 if config.get('accounting_version')==6 else 1) or
                type(config.get('lp_routing_version')) is not int or config['lp_routing_version']!=2) or
            type(interval) is not int or not 60 <= interval <= CHECK_SECONDS):
        return ['confirmation_health_profile_invalid']
    outer = data.get('rebalance_confirmation_health')
    report = outer.get('policy') if isinstance(outer,dict) else None
    if (not isinstance(report,dict) or type(report.get('schema')) is not int or report['schema'] != OBSERVATION_SCHEMA):
        return ['confirmation_observation_unknown']
    reasons = []
    expected_version=config['rebalance_confirmation_version']
    if (type(outer.get('version')) is not int or outer['version'] != expected_version or
            type(outer.get('check_interval_seconds')) is not int or outer['check_interval_seconds'] != CHECK_SECONDS):
        reasons.append('confirmation_service_cadence_mismatch')
    state = report.get('state')
    if state not in ('observed_this_cycle','stopped','incompatible_cadence'):
        reasons.append('confirmation_observation_not_current')
    observation = report.get('last_observed')
    if not isinstance(observation,dict):
        return reasons+['confirmation_observation_unavailable']
    number, stamp = observation.get('block_number'), observation.get('block_timestamp')
    if not _uint(number) or not _uint(stamp) or stamp == 0 or not _hash(observation.get('block_hash')):
        reasons.append('confirmation_observation_anchor_invalid')
    elif now-stamp < -30 or now-stamp > min(max_age,600):
        reasons.append('confirmation_observation_stale_or_future')
    observed = observation.get('observed_at_unix')
    if not _uint(observed) or now-observed < -30 or now-observed > min(max_age,600):
        reasons.append('confirmation_observation_read_stale_or_future')
    if observation.get('anchor_scope') != CONFIRMATION_SCOPE:
        reasons.append('confirmation_observation_scope_unknown')
    if observation.get('configuration_sha256') != digest(config):
        reasons.append('confirmation_observation_configuration_mismatch')
    if observation.get('source_files_sha256') != source_hashes():
        reasons.append('confirmation_observation_source_mismatch')
    if observation.get('source_identity_scope') != 'local_files_at_keeper_start_not_runtime_attestation':
        reasons.append('confirmation_observation_source_scope_unknown')
    runtimes, expected = observation.get('runtime_code_hashes'), config.get('code_hashes',{})
    roles=_confirmation_roles(config)
    if (not isinstance(runtimes,dict) or set(runtimes) != set(roles) or
            any(not _hash(runtimes.get(role)) or runtimes.get(role) != str(expected.get(role,'')).lower()
                for role in roles)):
        reasons.append('confirmation_observation_runtime_mismatch')
    try:
        bindings = _confirmation_bindings(config)
    except (ValueError,TypeError,KeyError):
        bindings = None
    capabilities = observation.get('validated_capabilities')
    wanted=_confirmation_capabilities(config)
    if (bindings is None or observation.get('validated_bindings') != bindings or
            not isinstance(capabilities,dict) or set(capabilities)!=set(wanted) or
            any(type(value) is not int or value!=wanted[role] for role,value in capabilities.items())):
        reasons.append('confirmation_observation_bindings_invalid')
    duration, gap = observation.get('duration_seconds'), observation.get('maximum_gap_seconds')
    review = observation.get('review_hash')
    valid_policy = (type(observation.get('version')) is int and observation['version']==expected_version and
        _uint(duration,604800) and duration>=60 and _uint(gap) and gap<=duration//2 and
        _uint(observation.get('policy_revision'),2**64-1) and isinstance(review,str) and
        re.fullmatch(r'0x[0-9a-f]{64}',review) is not None and (gap==0 or _hash(review)))
    if expected_version in (2,3):
        reference_review=observation.get('reference_review_hash')
        valid_policy = (valid_policy and type(observation.get('reference_exit_required')) is bool and
            isinstance(reference_review,str) and re.fullmatch(r'0x[0-9a-f]{64}',reference_review) is not None and
            (observation['reference_exit_required'] or _hash(reference_review)))
    if fresh:
        valid_policy=(valid_policy and type(observation.get('portfolio_version')) is int and observation['portfolio_version']==(2 if config.get('accounting_version')==6 else 1) and
            observation.get('portfolio_policy')==str(config.get('contracts',{}).get('portfolio_policy','')).lower() and
            _uint(observation.get('portfolio_policy_revision'),2**64-1) and
            _uint(observation.get('threshold_bps'),10000) and observation['threshold_bps']>0 and
            observation.get('threshold_basis')=='ZZZ_in_ETH_actual_centre_to_physical_boundary' and
            ((observation.get('minimum_main_bps') is None and observation.get('maximum_residual_bps') is None) if config.get('accounting_version')==6 else
             type(observation.get('minimum_main_bps')) is int and observation['minimum_main_bps']==6000 and
             type(observation.get('maximum_residual_bps')) is int and observation['maximum_residual_bps']==4000))
    if not valid_policy:
        reasons.append('confirmation_observation_policy_invalid')
    elif gap==0 and data.get('lp_exit_started') is not True:
        reasons.append('rebalance_confirmation_stopped')
    elif 0<gap<CHECK_SECONDS and data.get('lp_exit_started') is not True:
        reasons.append('rebalance_confirmation_cadence_incompatible')
    if (state=='stopped') != (valid_policy and gap==0):
        reasons.append('confirmation_observation_state_invalid')
    if (state=='incompatible_cadence') != (valid_policy and 0<gap<CHECK_SECONDS):
        reasons.append('confirmation_observation_state_invalid')
    return reasons


def execution_reasons(data, config, *, now, max_age):
    """Check the new profile's local receipt; historical profiles stay historical."""
    version = data.get('health_schema')
    if version is not None and (type(version) is not int or version != HEALTH_SCHEMA):
        return ['unsupported_health_schema']
    quality_version=config.get('execution_quality_version',0)
    if type(quality_version) is not int or quality_version not in (0,1):
        return ['execution_health_profile_invalid']
    confirmation_version=config.get('rebalance_confirmation_version',0)
    if type(confirmation_version) is not int or confirmation_version not in (0,1,2,3):
        return ['execution_health_profile_invalid']
    if confirmation_version in (1,2,3) and version!=HEALTH_SCHEMA:
        return ['execution_health_schema_required']
    confirmation = confirmation_reasons(data,config,now=now,max_age=max_age)
    if quality_version != 1:
        return confirmation
    if type(config.get('lp_routing_version')) is not int or config['lp_routing_version'] != (2 if config.get('accounting_version') in (5,6) else 1):
        return ['execution_health_profile_invalid']
    if version != HEALTH_SCHEMA:
        return ['execution_health_schema_required']
    report = data.get('lp_execution_health')
    if (not isinstance(report, dict) or type(report.get('schema')) is not int or
            report['schema'] != OBSERVATION_SCHEMA):
        return ['execution_observation_unknown']
    reasons = confirmation
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
    roles=RUNTIME_ROLES+(('lp_balance_math','lp_position_executor') if config['lp_routing_version']==2 else ())
    if (not isinstance(runtimes, dict) or set(runtimes) != set(roles) or
            any(not _hash(runtimes.get(role)) or runtimes.get(role) != str(expected.get(role, '')).lower()
                for role in roles)):
        reasons.append('execution_observation_runtime_mismatch')
    policy = observation.get('metadata')
    quality = policy.get('execution_quality') if isinstance(policy, dict) else None
    catalog=policy.get('execution_pools') if isinstance(policy,dict) else None
    if (not isinstance(policy, dict) or type(policy.get('version')) is not int or policy['version'] != config['lp_routing_version'] or
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
    if config['lp_routing_version']==2 and (not isinstance(policy,dict) or
            type(policy.get('portfolio_version')) is not int or policy['portfolio_version']!=(2 if config.get('accounting_version')==6 else 1) or
            policy.get('math_helper')!=str(config.get('contracts',{}).get('lp_balance_math','')).lower() or
            policy.get('position_executor')!=str(config.get('contracts',{}).get('lp_position_executor','')).lower()):
        reasons.append('execution_portfolio_helper_invalid')
    return reasons


def summary(data):
    """Allowlisted public diagnostics; malformed health files cannot echo secrets."""
    report = data.get('lp_execution_health')
    state = report.get('state') if isinstance(report, dict) else None
    states = ('not_observed', 'pending_recovery', 'not_observed_this_cycle',
        'not_configured', 'observed_this_cycle', 'unavailable')
    result = {'execution_observation_state': state if state in states else 'unknown'}
    confirmation = data.get('rebalance_confirmation_health')
    policy = confirmation.get('policy') if isinstance(confirmation,dict) else None
    policy_state = policy.get('state') if isinstance(policy,dict) else None
    result['confirmation_policy_state'] = policy_state if policy_state in (*states,'stopped','incompatible_cadence') else 'unknown'
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
