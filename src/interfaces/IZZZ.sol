// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PoolKey, PoolConfig, Position, Route, BridgeMessage} from "../libraries/ZZZTypes.sol";

interface IZZZAccess {
    function module(bytes32 key) external view returns (address);
    function isSealed() external view returns (bool);
    function paused() external view returns (bool);
    function keepers(address who) external view returns (bool);
    function canConfigure(address who) external view returns (bool);
}
interface IZZZBound { function access() external view returns (IZZZAccess); }
interface IZZZNFT {
    function ownerOf(uint256 id) external view returns (address);
    function mint(address to, uint256 id) external;
}
interface IZZZPower {
    function powerOf(uint256 id) external view returns (uint256);
    function totalPower() external view returns (uint256);
    function add(uint256 id, uint256 amount) external;
}
interface IZZZRewards {
    function isAsset(address token) external view returns (bool);
    function checkpointAll(uint256 id) external;
    function credit(uint256 id, address token, uint256 individual, uint256 collective) external;
}
interface IZZZFees {
    function allocate(uint256 id, address token, uint256 amount) external;
    function compoundBalance(uint256 id, address token) external view returns (uint256);
    function releaseCompound(uint256 id, address token) external returns (uint256);
    function flushDust(uint256 id, address token) external;
    function releaseBuyback(address token, uint256 amount) external;
    function creditRemote(uint256 id, address token, uint256 individual, uint256 collective) external;
}
interface IZZZPools {
    function get(bytes32 poolId) external view returns (PoolConfig memory);
}
interface IZZZOracle {
    function price(address token) external view returns (uint256);
    function tokenDecimals(address token) external view returns (uint8);
    function value(address token, uint256 amount) external view returns (uint256);
    function quote(address input, address output, uint256 amount) external view returns (uint256);
    function referenceX96(address token0, address token1) external view returns (uint160);
}
interface IZZZStrategy {
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
    function position(uint256 id) external view returns (Position memory);
    function compound(uint256 id, uint128 minimumLiquidity, uint256 deadline) external;
    function releaseForMigration(uint256 id, bytes32 migrationId, uint256 deadline)
        external returns (uint256 amount0, uint256 amount1);
    function importPending(uint256 id, bytes32 poolId, Position calldata origin, uint256 amount0, uint256 amount1) external;
    function finalizeImport(uint256 id, uint128 minimumLiquidity, uint256 deadline) external;
    function confirmMigration(uint256 id, uint256 destinationChain, address destinationVault) external;
    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline) external;
}
interface IZZZRoutes {
    function get(bytes32 id) external view returns (Route memory route, bool enabled);
}
interface IZZZBridge {
    function send(BridgeMessage calldata message) external payable returns (bytes32 transportId);
}
interface IZZZMigration {
    function authorizedRemote(uint256 id, uint256 chainId, address vault) external view returns (bool);
    function confirm(bytes32 migrationId, uint256 id, uint256 chainId, address vault) external;
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
