// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

library Ids {
    bytes32 internal constant VAULT = keccak256("ZZZVault");
    bytes32 internal constant NFT = keccak256("ZZZNFT");
    bytes32 internal constant LIQUIDITY = keccak256("ZZZLiquidityManager");
    bytes32 internal constant REWARDS = keccak256("ZZZRewards");
    bytes32 internal constant MEMBERSHIP = keccak256("ZZZMembership");
    bytes32 internal constant FEES = keccak256("ZZZFeeController");
    bytes32 internal constant STRATEGY = keccak256("ZZZStrategy");
    bytes32 internal constant COMPOUNDER = keccak256("ZZZCompounder");
    bytes32 internal constant BUYBACK = keccak256("ZZZBuyback");
    bytes32 internal constant MIGRATION = keccak256("ZZZMigration");
    bytes32 internal constant ORACLE = keccak256("ZZZOracle");
    bytes32 internal constant POOLS = keccak256("ZZZPoolRegistry");
    bytes32 internal constant CANONICAL = keccak256("ZZZCanonicalHandoff");
    bytes32 internal constant NFT_CANONICAL = keccak256("ZZZNFTCanonical");
    bytes32 internal constant VAULT_CANONICAL = keccak256("ZZZVaultCanonical");
    bytes32 internal constant FEES_CANONICAL = keccak256("ZZZFeesCanonical");
}

// ABI-compatible with Uniswap v4. Native ETH is address(0), distinct from WETH.
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

// Accounting V3 is local custody only. Historical V2 decoders retain their own
// fifteen-word Position and status meanings; never reinterpret them as this ABI.
enum PositionStatus { None, Active, Outbound, Dormant, Parked }
struct Position {
    bytes32 poolId;
    uint256 lpTokenId;
    uint256 idle0;
    uint256 idle1;
    uint256 depositUSD;
    uint160 centerX96;
    uint64 lastRebalance;
    PositionStatus status;
}

