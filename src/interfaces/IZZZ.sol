// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PoolKey, PoolConfig, Position, PositionStatus, Route, BridgeMessage, TransportPolicy} from "../libraries/ZZZTypes.sol";

interface IZZZAccess {
    function module(bytes32 key) external view returns (address);
    function isSealed() external view returns (bool);
    function paused() external view returns (bool);
    function preparationActive() external view returns (bool);
    function keepers(address who) external view returns (bool);
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
    function creditPool(uint256 bucketId, address token, uint256 individual, uint256 collective) external;
}
interface IZZZFees {
    function allocate(uint256 id, address token, uint256 amount) external;
    function syncExternal(uint256 bucketId) external;
    function syncAllExternal() external;
    function hasPendingExternal() external view returns (bool);
    function compoundBalance(uint256 id, address token) external view returns (uint256);
    function releaseCompound(uint256 id, address token) external returns (uint256);
    function flushDust(uint256 id, address token) external;
    function releaseBuyback(address token, uint256 amount) external;
    function creditRemote(uint256 id, address token, uint256 individual, uint256 collective) external;
    function bindRemoteAsset(uint256 id, address token, address canonicalToken) external;
    function allocated(uint256 bucketId, address canonicalToken) external view returns (uint256, uint256);
    function importAccounting(BridgeMessage calldata message) external;
    function remoteSettled(uint256 bucketId) external view returns (bool);
}
interface IZZZPools {
    function activationEntry() external view returns (address);
    function get(bytes32 poolId) external view returns (PoolConfig memory);
    /// @notice Canonical ERC20 accounting assets in the actual venue's slot order.
    /// Native venue currency is normalized only by the reviewed liquidity adapter.
    function accounting(bytes32 poolId) external view returns (PoolConfig memory);
    function contributionValue(bytes32 poolId, uint256 amount0, uint256 amount1) external view returns (uint256);
}
interface IZZZActivationEntry {
    function validateOwner(uint256 id, bytes32 vaultCallHash) external view;
    function sourceValue(bytes32 poolId, uint256 amount0, uint256 amount1) external view returns (uint256);
}
interface IZZZOracle {
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
    function compoundPlan(uint256 id, uint256 amount0, uint256 amount1) external view returns (bool, uint256, uint256);
    function swapPlan(bytes32 poolId, uint256 amount0, uint256 amount1)
        external view returns (bool zeroForOne, uint256 amountIn, uint256 minimumOut);
}
interface IZZZLiquidity {
    function mint(bytes32 poolId, int24 lower, int24 upper, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline) external returns (uint256 tokenId, uint256 spent0, uint256 spent1);
    function increase(bytes32 poolId, uint256 tokenId, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline) external returns (uint256 spent0, uint256 spent1);
    function collect(bytes32 poolId, uint256 tokenId, uint256 deadline) external;
    function close(bytes32 poolId, uint256 tokenId, uint256 deadline) external;
    function swap(bytes32 poolId, bool zeroForOne, uint256 amountIn, uint256 minimumOut, uint256 deadline)
        external returns (uint256 amountOut);
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
    function activate(uint256 id, bytes32 poolId, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline) external;
    function increase(uint256 id, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline) external;
    function park(uint256 id, uint256 deadline) external;
    function resume(uint256 id, bytes32 poolId, uint128 minimumLiquidity, uint256 deadline) external;
    function compound(uint256 id, uint128 minimumLiquidity, uint256 deadline) external;
    function releaseForMigration(uint256 id, bytes32 migrationId, uint256 deadline)
        external returns (uint256 amount0, uint256 amount1);
    function importPending(uint256 id, bytes32 poolId, Position calldata origin, uint256 shares, bytes32 homePool,
        uint256 amount0, uint256 amount1) external;
    function finalizeImport(uint256 id, uint128 minimumLiquidity, uint256 deadline) external;
    function confirmMigration(uint256 id, uint256 destinationChain, address destinationVault) external;
    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline) external;
}
interface IZZZRoutes {
    function get(bytes32 id) external view returns (Route memory route, bool enabled);
    function transportPolicyId(bytes32 id) external view returns (bytes32);
}
interface IZZZBridge {
    function send(BridgeMessage calldata message) external payable returns (bytes32 transportId);
}
interface IZZZMigration {
    function activePlan(uint256 bucketId) external view returns (bytes32);
    function authorizedRemote(uint256 id, uint256 chainId, address vault) external view returns (bool);
    function custodyEpoch(uint256 id) external view returns (uint64);
    function registerImport(BridgeMessage calldata message) external;
    function confirm(BridgeMessage calldata message, uint256 chainId, address vault) external;
    function authorizedReward(uint256 id, uint256 chainId, address vault, address remoteToken, address homeToken) external view returns (bool);
}
interface IZZZReceiver {
    function receiveMessage(uint256 sourceChain, address sourceAdapter, BridgeMessage calldata message) external;
}

/// @notice Transport implementers MUST authenticate the origin chain and sender,
/// enforce finality, and atomically deliver EXACT token amounts to the adapter.
/// No particular production bridge is implied by this interface.
interface IZZZTransport {
    function send(uint256 destinationChain, address destinationAdapter, address[] calldata tokens,
        uint256[] calldata amounts, bytes calldata payload) external payable returns (bytes32);
}
interface IZZZTransportReceiver {
    function onMessage(uint256 sourceChain, address sourceAdapter, bytes calldata payload) external;
}

interface IZZZBridgeEndpoint { function transport() external view returns (address); }
interface IZZZBridgeRouter {
    function registerPolicy(TransportPolicy calldata policy) external returns (bytes32);
    function matchesRoute(bytes32 policyId, Route calldata route) external view returns (bool);
    function canSend(bytes32 routeId) external view returns (bool);
}
/// @notice A separately reviewed, router-bound SDK wrapper. The wrapper MUST
/// authenticate the physical source router/chain, finality and exact backed
/// destination assets before calling onProviderMessage. configurationHash must
/// commit to all channel security/asset settings; a getter alone proves nothing.
interface IZZZTransportProvider {
    function router() external view returns (address);
    function configurationHash(bytes32 channelId) external view returns (bytes32);
    function send(bytes32 policyId, uint256 destinationChain, address destinationProvider,
        address destinationRouter, address[] calldata tokens, uint256[] calldata amounts,
        bytes calldata envelope) external payable returns (bytes32);
}
interface IZZZBridgeRouterReceiver {
    function onProviderMessage(uint256 authenticatedSourceChain, address authenticatedSourceRouter,
        address[] calldata actualDestinationTokens, uint256[] calldata actualAmounts,
        bytes calldata envelope) external;
}

/// @dev Minimal external ABIs, checked against the official Uniswap v4 sources.
interface IPositionManagerMinimal {
    function modifyLiquidities(bytes calldata unlockData, uint256 deadline) external payable;
    function nextTokenId() external view returns (uint256);
    function getPositionLiquidity(uint256 id) external view returns (uint128);
    function getPoolAndPositionInfo(uint256 id) external view returns (PoolKey memory, uint256);
    function ownerOf(uint256 id) external view returns (address);
    function approve(address spender, uint256 id) external;
    function getApproved(uint256 id) external view returns (address);
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
