"""Bounded LP-router capability observations; never choose or sign a swap."""
from zzz_ops.abi import address, keccak256


def observe(read, *, liquidity, router, pool_manager, state_view, access, pools, quality_version=0, strategy=None,
            routing_version=1, math_helper=None, position_executor=None,portfolio_version=1):
    """``read`` must use one canonical block for every address/ABI result."""
    if type(quality_version) is not int or quality_version not in (0,1):
        raise ValueError('Unsupported explicit execution-quality capability')
    if type(routing_version) is not int or routing_version not in (1,2):
        raise ValueError('Unsupported explicit LP-routing capability')
    if type(portfolio_version) is not int or portfolio_version not in (1,2):raise ValueError('Unsupported explicit portfolio capability')
    if routing_version==2 and (math_helper is None or position_executor is None):
        raise ValueError('Portfolio routing requires reviewed arithmetic and position helpers')
    def number(target, method, *args):
        values = read(target, method, *args)
        if not isinstance(values, list) or len(values) != 1:
            raise ValueError('Malformed LP execution capability result')
        return int(values[0], 16)
    def binding(target, method, expected):
        if number(target, method) != int(address(expected), 16):
            raise ValueError('LP execution immutable binding differs')
    for target in (liquidity, router):
        if number(target, 'LP_ROUTING_VERSION()') != routing_version:
            raise ValueError('Unsupported LP execution capability')
        binding(target, 'access()', access)
        if quality_version == 1 and number(target, 'EXECUTION_QUALITY_VERSION()') != 1:
            raise ValueError('Unsupported execution-quality capability')
    for target, method, expected in ((liquidity, 'balancingRouter()', router),
            (liquidity, 'poolManager()', pool_manager), (liquidity, 'stateView()', state_view),
            (router, 'liquidityManager()', liquidity), (router, 'poolManager()', pool_manager),
            (router, 'stateView()', state_view)):
        binding(target, method, expected)
    if routing_version==2:
        if number(liquidity,'PORTFOLIO_VERSION()')!=portfolio_version:
            raise ValueError('Unsupported explicit portfolio capability')
        binding(router,'balanceMath()',math_helper)
        binding(math_helper,'balancer()',router)
        if number(math_helper,'LP_BALANCE_MATH_VERSION()')!=1:
            raise ValueError('Unsupported LP arithmetic capability')
        binding(liquidity,'positionOperator()',position_executor)
        binding(position_executor,'liquidityManager()',liquidity)
        binding(position_executor,'access()',access)
        binding(position_executor,'poolManager()',pool_manager)
        binding(position_executor,'stateView()',state_view)
        binding(position_executor,'balancingRouter()',router)
        binding(position_executor,'positionManager()', '0x'+f'{number(liquidity,"positionManager()"):040x}')
        binding(position_executor,'permit2()', '0x'+f'{number(liquidity,"permit2()"):040x}')
        if number(position_executor,'LP_POSITION_EXECUTOR_VERSION()')!=1:
            raise ValueError('Unsupported typed position executor capability')
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
    quality = {}
    if quality_version == 1:
        owner = address('0x'+f'{number(access,"module(bytes32)","0x"+keccak256(b"ZZZStrategy").hex()):040x}')
        if strategy is not None and owner != address(strategy):
            raise ValueError('Execution-quality owner differs from the reviewed Strategy')
        binding(owner, 'access()', access)
        if number(owner, 'EXECUTION_QUALITY_VERSION()') != 1:
            raise ValueError('Unsupported Strategy execution-quality capability')
        maximum = number(router, 'MAX_ADDITIONAL_LOSS_BPS()')
        additional = number(router, 'additionalLossBps()')
        policy_revision = number(owner, 'executionQualityRevision()')
        if (maximum != 1000 or not 0 <= additional <= maximum or not 0 <= policy_revision < 2**64 or
                number(owner, 'MAX_ADDITIONAL_LOSS_BPS()') != maximum or
                number(owner, 'additionalLossBps()') != additional):
            raise ValueError('Execution-quality policy exceeds reviewed bounds')
        quality = {'execution_quality': {'version': 1, 'additional_loss_bps': additional,
            'maximum_additional_loss_bps': maximum,
            'policy_owner': owner, 'quality_policy_revision': policy_revision,
            'known_pool_fees_excluded_from_additional_limit': True,
            'policy_frozen_by_wallet_review': False}}
    return {'version': routing_version, 'router': router, 'execution_revision': revision,
            'registry_configuration_revision': registry_revision,
            'search_iterations': iterations, 'quote_gas_limit': quote_gas,
            'execution_pools': ['0x' + f'{value:064x}' for value in catalog],
            'swaps_enabled': bool(catalog), 'catalog_frozen_by_wallet_review': False,
            **({'math_helper':math_helper,'position_executor':position_executor,'portfolio_version':portfolio_version} if routing_version==2 else {}), **quality}
