// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZOracle, IZZZRewards} from "./interfaces/IZZZ.sol";

/// @notice Append-only pool identities; bounded strategy parameters are timelocked.
/// No hooks, native ETH, rebasing, or transfer-tax token support in this version.
contract ZZZPoolRegistry is ZZZModule {
    mapping(bytes32 => PoolConfig) private pools;
    mapping(bytes32 => bool) public exists;
    event PoolConfigured(bytes32 indexed poolId, address indexed token0, address indexed token1);
    constructor(address controller) ZZZModule(controller) {}
    function configure(PoolConfig calldata config) external onlyGovernance returns (bytes32 poolId) {
        PoolKey memory k = config.key;
        if (k.currency0 >= k.currency1 || k.currency0.code.length == 0 || k.currency1.code.length == 0 ||
            k.hooks != address(0) || k.tickSpacing <= 0 || k.tickSpacing > 32767 || k.fee > 100000 ||
            config.rangeBps < 100 || config.rangeBps > 5000 || config.triggerBps < 100 ||
            config.triggerBps >= config.rangeBps || config.maxSpotDeviationBps == 0 ||
            config.maxSpotDeviationBps > 500 || config.maxSpotDeviationBps >= config.rangeBps || config.maxSlippageBps == 0 || config.maxSlippageBps > 200 || k.fee >= uint24(config.maxSlippageBps) * 100 ||
            config.minRebalanceInterval < 600 || config.minRebalanceInterval > 7 days ||
            config.minDepositUSD == 0 || config.maxPositionUSD < config.minDepositUSD) revert InvalidConfiguration();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        oracle.price(k.currency0);
        oracle.price(k.currency1);
        IZZZRewards rewards = IZZZRewards(access.module(Ids.REWARDS));
        if (!rewards.isAsset(k.currency0) || !rewards.isAsset(k.currency1)) revert InvalidConfiguration();
        poolId = keccak256(abi.encode(k));
        pools[poolId] = config;
        exists[poolId] = true;
        emit PoolConfigured(poolId, k.currency0, k.currency1);
    }
    function get(bytes32 poolId) external view returns (PoolConfig memory) {
        if (!exists[poolId]) revert InvalidConfiguration();
        return pools[poolId];
    }
}
