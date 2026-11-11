"""Explicit execution-price capability; public dual-source observations stay live.

This authenticates existing pinned contracts only. It does not select feeds,
register composite sources, relax prices or prepare/sign an operation.
"""
from zzz_ops.abi import uint_result

VERSION = 1
ROLES = ('oracle', 'contribution_pricing', 'liquidity', 'balancing_router', 'lp_position_executor', 'strategy')
INVENTORY_ROLES = (('modules', 'oracle'), ('helpers', 'contribution_pricing'),
                   ('modules', 'liquidity'), ('helpers', 'balancing_router'),
                   ('helpers', 'lp_position_executor'), ('modules', 'strategy'))


def version(value):
    if type(value) is not int or value not in (0, VERSION):
        raise ValueError('Unsupported explicit execution-price profile')
    return value


def observe(read, pins):
    """Caller authenticates exact runtime pins and one canonical block first."""
    for role in ROLES:
        if role not in pins:
            raise ValueError('Missing pinned execution-price contract')
        values = read(pins[role], 'EXECUTION_PRICE_VERSION()', count=1)
        if len(values) != 1 or uint_result('0x' + values[0]) != VERSION:
            raise ValueError('Execution-price capability differs from the explicit profile')
    helper = read(pins['liquidity'], 'executionStrategy()', count=1)
    if (len(helper) != 1 or uint_result('0x' + helper[0]) != int(pins['lp_balance_math'], 16) or
            read(pins['lp_balance_math'], 'EXECUTION_PRICE_VERSION()', count=1) != [f'{1:064x}']):
        raise ValueError('Execution-price Strategy helper differs from the fixed math child')
    active = read(pins['oracle'], 'executionActive()', count=1)
    if len(active) != 1 or uint_result('0x' + active[0]) != 0:
        raise ValueError('Execution-price context must be inactive before preparation')
    revision = read(pins['oracle'], 'executionSourceRevision()', count=1)
    if len(revision) != 1 or uint_result('0x' + revision[0]) >= 1 << 64:
        raise ValueError('Invalid execution-source revision')
    return {'version': VERSION, 'contracts': {role: pins[role] for role in ROLES},
            'execution_strategy': pins['lp_balance_math'],
            'source_revision': int(revision[0], 16), 'context_active': False}
