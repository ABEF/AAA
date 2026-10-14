// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

library Ids {
    bytes32 internal constant VAULT = keccak256("ZZZVault");
    bytes32 internal constant NFT = keccak256("ZZZNFT");
    bytes32 internal constant LIQUIDITY = keccak256("ZZZLiquidityManager");
    bytes32 internal constant REWARDS = keccak256("ZZZRewards");
    bytes32 internal constant POWER = keccak256("ZZZPower");
    bytes32 internal constant FEES = keccak256("ZZZFeeController");
    bytes32 internal constant STRATEGY = keccak256("ZZZStrategy");
    bytes32 internal constant COMPOUNDER = keccak256("ZZZCompounder");
    bytes32 internal constant BUYBACK = keccak256("ZZZBuyback");
    bytes32 internal constant MIGRATION = keccak256("ZZZMigration");
    bytes32 internal constant BRIDGE = keccak256("ZZZBridgeAdapter");
    bytes32 internal constant RECEIVER = keccak256("ZZZMigrationReceiver");
    bytes32 internal constant ORACLE = keccak256("ZZZOracle");
    bytes32 internal constant POOLS = keccak256("ZZZPoolRegistry");
    bytes32 internal constant ROUTES = keccak256("ZZZMigrationRegistry");
}

// ABI-compatible with the canonical Uniswap v4 PoolKey. ERC20 currencies only.
struct PoolKey {
    address currency0;
    address currency1;
    uint24 fee;
    int24 tickSpacing;
    address hooks;
}

struct PoolConfig {
    PoolKey key;
    bool depositsEnabled;
    bool operationsEnabled;
    uint16 rangeBps;
    uint16 triggerBps;
    uint16 maxSpotDeviationBps;
    uint16 maxSlippageBps;
    uint32 minRebalanceInterval;
    uint256 minDepositUSD;
    uint256 maxPositionUSD;
}

enum PositionStatus { None, Active, Outbound, Remote, Inbound }
struct Position {
    bytes32 poolId;
    uint256 lpTokenId;
    uint256 idle0;
    uint256 idle1;
    uint256 depositUSD;
    uint160 centerX96;
    uint64 lastRebalance;
    PositionStatus status;
    uint256 homeChain;
    address homeVault;
    address homeReceiver;
    address homeToken0;
    address homeToken1;
    uint256 locationChain;
    address locationVault;
}

// Each route is append-only. Only enabled can subsequently be changed.
// source/destination tokens must represent the same asset at identical decimals.
struct Route {
    uint256 sourceChain;
    address sourceAdapter;
    address sourceVault;
    address sourceReceiver;
    uint256 destinationChain;
    address destinationAdapter;
    address destinationVault;
    address destinationReceiver;
    bytes32 destinationPool;
    address sourceToken0;
    address sourceToken1;
    address destinationToken0;
    address destinationToken1;
    uint8 token0Decimals;
    uint8 token1Decimals;
}

enum MessageKind { Principal, Reward, Acknowledgement }
struct BridgeMessage {
    uint8 version;
    MessageKind kind;
    bytes32 routeId;
    uint256 nonce;
    uint256 nftId;
    bytes32 migrationId;
    uint256 homeChain;
    address homeVault;
    address homeReceiver;
    uint256 depositUSD;
    uint256 amount0;
    uint256 amount1;
    // Reward messages use amount0 only. Split must sum to amount0.
    uint256 individual;
    uint256 collective;
}
