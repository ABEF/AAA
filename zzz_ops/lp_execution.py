"""Bounded LP-router capability observations; never choose or sign a swap."""
from zzz_ops.abi import address


def observe(read, *, liquidity, router, pool_manager, state_view, access, pools):
    """``read`` must use one canonical block for every address/ABI result."""
    def number(target, method, *args):
        values = read(target, method, *args)
        if not isinstance(values, list) or len(values) != 1:
            raise ValueError('Malformed LP execution capability result')
        return int(values[0], 16)
    def binding(target, method, expected):
        if number(target, method) != int(address(expected), 16):
            raise ValueError('LP execution immutable binding differs')
    for target in (liquidity, router):
        if number(target, 'LP_ROUTING_VERSION()') != 1:
            raise ValueError('Unsupported LP execution capability')
        binding(target, 'access()', access)
    for target, method, expected in ((liquidity, 'balancingRouter()', router),
            (liquidity, 'poolManager()', pool_manager), (liquidity, 'stateView()', state_view),
            (router, 'liquidityManager()', liquidity), (router, 'poolManager()', pool_manager),
            (router, 'stateView()', state_view)):
        binding(target, method, expected)
    revision = number(router, 'executionRevision()')
    registry_revision = number(pools, 'configurationRevision()')
    iterations = number(router, 'searchIterations()')
    quote_gas = number(router, 'quoteGasLimit()')
    count = number(router, 'executionPoolCount()')
    if (not 0 <= revision < 2**64 or not 0 <= registry_revision < 2**64 or
            not 4 <= iterations <= 12 or not 100_000 <= quote_gas <= 300_000 or
            number(router, 'MAX_EXECUTION_POOLS()') != 4 or not 0 <= count <= 4):
        raise ValueError('LP execution metadata exceeds reviewed bounds')
    catalog = []
    for index in range(count):
        value = number(router, 'executionPoolAt(uint256)', index)
        if not 0 < value < 2**256 or value in catalog:
            raise ValueError('Malformed or duplicate LP execution pool')
        catalog.append(value)
    return {'version': 1, 'router': router, 'execution_revision': revision,
            'registry_configuration_revision': registry_revision,
            'search_iterations': iterations, 'quote_gas_limit': quote_gas,
            'execution_pools': ['0x' + f'{value:064x}' for value in catalog],
            'swaps_enabled': bool(catalog), 'catalog_frozen_by_wallet_review': False}
