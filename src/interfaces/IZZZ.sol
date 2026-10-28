// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PoolKey, PoolConfig, Position, PositionStatus} from "../libraries/ZZZTypes.sol";

interface IZZZAccess {
    function governance() external view returns (address);
    function module(bytes32 key) external view returns (address);
    function isSealed() external view returns (bool);
    function paused() external view returns (bool);
    function lpExitStarted() external view returns (bool);
    function startLPExit() external;
    function preparationActive() external view returns (bool);
    function canonicalHandoff() external view returns (address);
    function royaltyFactory() external view returns (address);
    function activationAssetsFactory() external view returns (address);
    function canonicalState() external view returns (uint8);
    function canonicalSettling() external view returns (bool);
    function keepers(address who) external view returns (bool);
    function moduleAuthorized(bytes32 id, address caller) external view returns (bool);
    function keeperAuthorized(address caller) external view returns (bool);
    function canConfigure(address who) external view returns (bool);
}
interface IZZZBound { function access() external view returns (IZZZAccess); }
interface IZZZNFT {
    function ownerOf(uint256 id) external view returns (address);
    function claimRouter() external view returns (address);
    function mint(address to, uint256 id) external;
    function traitsReady(uint256 id) external view returns (bool);
    function randomnessConfigured() external view returns (bool);
    function notifyContribution(uint256 id) external;
}
interface IZZZMembership {
    function eligible(uint256 id) external view returns (bool);
    function totalEligible() external view returns (uint256);
    function activate(uint256 id) external;
    function settleDust() external;
}
interface IZZZRewards {
    function isAsset(address token) external view returns (bool);
    function checkpointAll(uint256 id) external;
    function checkpointOwner(uint256 id) external;
    function creditPool(uint256 bucketId, address token, uint256 individual, uint256 collective) external payable;
}
interface IZZZFees {
    function allocate(uint256 id, address token, uint256 amount) external payable;
    function compoundBalance(uint256 id, address token) external view returns (uint256);
    function releaseCompound(uint256 id, address token) external returns (uint256);
    function flushDust(uint256 id, address token) external;
    function releaseBuyback(address token, uint256 amount) external;

}
interface IZZZPools {
    function activationEntry() external view returns (address);
    function get(bytes32 poolId) external view returns (PoolConfig memory);
    /// @notice Actual accounting assets in venue slot order. Zero is admitted
    /// native ETH, distinct from any wrapped ERC20 and from an unset pool.
    function accounting(bytes32 poolId) external view returns (PoolConfig memory);
    function contributionValue(bytes32 poolId, uint256 amount0, uint256 amount1) external view returns (uint256);
}
interface IZZZActivationEntry {
    function validateOwner(uint256 id, bytes32 vaultCallHash) external view;
    function sourceValue(bytes32 poolId, uint256 amount0, uint256 amount1) external view returns (uint256);
}
interface IZZZOracle {
    function contributionPricing() external view returns (address);
    function priceBounds(address token) external view returns (uint256 lower, uint256 upper, bytes32 fingerprint);
    function price(address token) external view returns (uint256);
    function tokenDecimals(address token) external view returns (uint8);
    function value(address token, uint256 amount) external view returns (uint256);
    function quote(address input, address output, uint256 amount) external view returns (uint256);
    function referenceX96(address token0, address token1) external view returns (uint160);
}
interface IZZZStrategy {
    function validateExitPrice(bytes32 poolId) external view returns (uint160);
    function target(bytes32 poolId) external view returns (int24 lower, int24 upper, uint160 referenceX96);
    function validatePrice(bytes32 poolId) external view returns (uint160 spotX96);
    function needsRebalance(uint256 id) external view returns (bool);
    function keeperRangeTarget(bytes32 poolId) external view returns (uint16);
    function compoundPlan(uint256 id, uint256 amount0, uint256 amount1) external view returns (bool, uint256, uint256);
    function swapPlan(bytes32 poolId, uint256 amount0, uint256 amount1)
        external view returns (bool zeroForOne, uint256 amountIn, uint256 minimumOut);
}
interface IZZZLiquidity {
    function balanceContext(bytes32 poolId) external view returns (bytes32);
    /// @notice Balance only the supplied attributed budget against the current
    /// target position, selecting one admitted execution venue atomically.
    function balance(bytes32 poolId, uint256 tokenId, uint256 amount0, uint256 amount1, uint256 deadline)
        external payable returns (uint256 balanced0, uint256 balanced1);
    function mint(bytes32 poolId, int24 lower, int24 upper, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline) external payable returns (uint256 tokenId, uint256 spent0, uint256 spent1);
    function increase(bytes32 poolId, uint256 tokenId, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline) external payable returns (uint256 spent0, uint256 spent1);
    function collect(bytes32 poolId, uint256 tokenId, uint256 deadline) external;
    function close(bytes32 poolId, uint256 tokenId, uint256 deadline) external;
    function swap(bytes32 poolId, bool zeroForOne, uint256 amountIn, uint256 minimumOut, uint256 deadline)
        external payable returns (uint256 amountOut);
    function amounts(uint256 tokenId) external view returns (uint256 amount0, uint256 amount1);
    function ticks(uint256 tokenId) external view returns (int24 lower, int24 upper);
    function spot(bytes32 poolId) external view returns (uint160);
    function positionManager() external view returns (address);
}
interface IZZZVault {
    function canonicalChainId() external view returns (uint256);
    function mintProceedsRecipient() external view returns (address payable);
    function nftStatus(uint256 id) external view returns (PositionStatus);
    function group(uint256 bucketId) external view returns (Position memory);
    function nftBucket(uint256 id) external view returns (uint256);
    function sharesOf(uint256 id) external view returns (uint256);
    function bucketTotalShares(uint256 bucketId) external view returns (uint256);
    function homePoolId(uint256 bucketId) external view returns (bytes32);
    function poolBucket(bytes32 poolId) external view returns (uint256);
    function bucketCount() external view returns (uint256);
    function MAX_BUCKETS() external view returns (uint256);
    function bucketAt(uint256 index) external view returns (uint256);
    function mintDormant() external payable returns (uint256 id);
    function activate(uint256 id, bytes32 poolId, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline) external payable;
    function increase(uint256 id, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline) external payable;
    function park(uint256 id, uint256 deadline) external;
    function resume(uint256 id, bytes32 poolId, uint128 minimumLiquidity, uint256 deadline) external;
    function compound(uint256 id, uint128 minimumLiquidity, uint256 deadline) external;
    function beginLPExit() external;
    function exitBucketToHolders(uint256 id, uint256 minimumETH, uint256 minimumZZZ, uint256 deadline)
        external returns (uint256 amountETH, uint256 amountZZZ);
    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline) external;
}
interface IZZZMigration {
    function currentZZZ() external view returns (address);
    function activePlan(uint256 bucketId) external view returns (bytes32);
    function custodyEpoch(uint256 id) external view returns (uint64);
}

/// @dev Minimal external ABIs, checked against the official Uniswap v4 sources.
interface IPositionManagerMinimal {
    function modifyLiquidities(bytes calldata unlockData, uint256 deadline) external payable;
    function nextTokenId() external view returns (uint256);
    function getPositionLiquidity(uint256 id) external view returns (uint128);
    function getPoolAndPositionInfo(uint256 id) external view returns (PoolKey memory, uint256);
    function ownerOf(uint256 id) external view returns (address);
    function approve(address spender, uint256 id) external;
    function poolManager() external view returns (address);
    function permit2() external view returns (address);
}
interface IStateViewMinimal {
    function getSlot0(bytes32 poolId) external view returns (uint160, int24, uint24, uint24);
    function poolManager() external view returns (address);
}
interface IPermit2Minimal {
    function approve(address token, address spender, uint160 amount, uint48 expiration) external;
}
interface IPoolManagerMinimal {
    struct SwapParams { bool zeroForOne; int256 amountSpecified; uint160 sqrtPriceLimitX96; }
    function unlock(bytes calldata data) external returns (bytes memory);
    function swap(PoolKey calldata key, SwapParams calldata params, bytes calldata hookData) external returns (int256 delta);
    function sync(address currency) external;
    function settle() external payable returns (uint256 paid);
    function take(address currency, address to, uint256 amount) external;
}
interface IPriceFeed {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
    function decimals() external view returns (uint8);
}
interface IBurnable {
    function burn(uint256 amount) external;
    function totalSupply() external view returns (uint256);
}
