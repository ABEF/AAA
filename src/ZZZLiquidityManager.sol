// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
interface IPairSwapCompanion { function pairMigration() external view returns (address); }
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {LiquidityAmounts} from "@uniswap/v4-periphery/src/libraries/LiquidityAmounts.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZPools, IZZZOracle, IZZZStrategy, IPositionManagerMinimal, IStateViewMinimal,
    IPermit2Minimal, IPoolManagerMinimal} from "./interfaces/IZZZ.sol";

interface INativePoolAssets {
    function nativeAsset(bytes32 poolId) external view returns (address);
}
interface ICanonicalWrapper {
    function WETH9() external view returns (address);
    function deposit() external payable;
    function withdraw(uint256 amount) external;
}

/// @notice Typed v4 operations only. No arbitrary call/action/recipient entrypoint.
/// Vault owns every LP NFT. Per-NFT approvals authorize this immutable module.
contract ZZZLiquidityManager is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    IPositionManagerMinimal private immutable posm;
    IStateViewMinimal public immutable stateView;
    IPoolManagerMinimal public immutable poolManager;
    IPermit2Minimal public immutable permit2;
    bytes32 private pendingSwapHash;
    // A native credit is accepted only during an expected wrapper/core call.
    // Forced ETH is preserved and never counted as contribution or revenue.
    address private nativeSender;
    uint256 private nativeReceived;
    uint8 private constant INCREASE = 0x00;
    uint8 private constant DECREASE = 0x01;
    uint8 private constant MINT = 0x02;
    uint8 private constant BURN = 0x03;
    uint8 private constant SETTLE_PAIR = 0x0d;
    uint8 private constant TAKE_PAIR = 0x11;

    constructor(address controller, address positionManager_, address stateView_, address poolManager_, address permit2_)
        ZZZModule(controller) {
        if (positionManager_.code.length == 0 || stateView_.code.length == 0 || poolManager_.code.length == 0 ||
            permit2_.code.length == 0) revert InvalidConfiguration();
        posm = IPositionManagerMinimal(positionManager_);
        stateView = IStateViewMinimal(stateView_);
        poolManager = IPoolManagerMinimal(poolManager_);
        permit2 = IPermit2Minimal(permit2_);
        if (posm.poolManager() != poolManager_ || posm.permit2() != permit2_ ||
            stateView.poolManager() != poolManager_) revert InvalidConfiguration();
    }
    receive() external payable {
        if (msg.sender != nativeSender || nativeSender == address(0)) revert Unauthorized();
        nativeReceived += msg.value;
    }
    function positionManager() external view returns (address) { return address(posm); }
    function spot(bytes32 poolId) public view returns (uint160 priceX96) {
        (priceX96,,,) = stateView.getSlot0(poolId);
    }
    function _config(bytes32 poolId, bool requireOperations) private view returns (PoolConfig memory c) {
        c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        if ((requireOperations && !c.operationsEnabled) || keccak256(abi.encode(c.key)) != poolId) revert InvalidState();
        if (c.key.currency0 == address(0)) {
            // Only the registry's separately reviewed native policy can normalize this key.
            if (_nativeAsset(poolId) == address(0) || c.key.fee != 0 ||
                uint160(c.key.hooks) & 0x3fff != 0x2044) revert InvalidState();
        } else if (c.key.hooks != address(0)) revert InvalidState();
    }
    function _nativeAsset(bytes32 poolId) private view returns (address wrapper) {
        wrapper = INativePoolAssets(access.module(Ids.POOLS)).nativeAsset(poolId);
        if (wrapper.code.length == 0 || ICanonicalWrapper(address(posm)).WETH9() != wrapper) revert InvalidConfiguration();
    }
    function _assets(bytes32 poolId, PoolConfig memory c) private view returns (address token0, address token1) {
        token0 = c.key.currency0 == address(0) ? _nativeAsset(poolId) : c.key.currency0;
        token1 = c.key.currency1;
    }
    function _unwrap(address wrapper, uint256 amount) private {
        if (amount == 0) return;
        uint256 beforeNative = address(this).balance;
        uint256 beforeWrapped = IERC20(wrapper).balanceOf(address(this));
        nativeSender = wrapper;
        nativeReceived = 0;
        ICanonicalWrapper(wrapper).withdraw(amount);
        nativeSender = address(0);
        if (nativeReceived != amount || address(this).balance != beforeNative + amount ||
            IERC20(wrapper).balanceOf(address(this)) + amount != beforeWrapped) revert InvalidState();
        nativeReceived = 0;
    }
    function _wrap(address wrapper, uint256 amount) private {
        if (amount == 0) return;
        uint256 beforeNative = address(this).balance;
        uint256 beforeWrapped = IERC20(wrapper).balanceOf(address(this));
        ICanonicalWrapper(wrapper).deposit{value: amount}();
        if (address(this).balance + amount != beforeNative ||
            IERC20(wrapper).balanceOf(address(this)) != beforeWrapped + amount) revert InvalidState();
    }
    function _finishNativeCredit(address wrapper, uint256 beforeNative, address recipient) private {
        nativeSender = address(0);
        uint256 amount = nativeReceived;
        nativeReceived = 0;
        if (address(this).balance != beforeNative + amount) revert InvalidState();
        _wrap(wrapper, amount);
        ExactToken.push(wrapper, recipient, amount);
    }
    function _nativeDebt(uint160 current, int24 lower, int24 upper, uint128 liquidity) private pure returns (uint256) {
        uint160 a = TickMath.getSqrtPriceAtTick(lower);
        uint160 b = TickMath.getSqrtPriceAtTick(upper);
        if (current >= b) return 0;
        return SqrtPriceMath.getAmount0Delta(current <= a ? a : current, b, liquidity, true);
    }
    function _checkPosition(bytes32 poolId, uint256 id) private view returns (int24 lower, int24 upper) {
        if (posm.ownerOf(id) != access.module(Ids.VAULT)) revert InvalidState();
        (PoolKey memory key, uint256 info) = posm.getPoolAndPositionInfo(id);
        if (keccak256(abi.encode(key)) != poolId) revert InvalidState();
        lower = int24(uint24(info >> 8));
        upper = int24(uint24(info >> 32));
    }
    function _approve(address token, uint256 amount, uint256 deadline) private {
        if (amount > type(uint128).max) revert InvalidAmount();
        IERC20(token).forceApprove(address(permit2), amount);
        permit2.approve(token, address(posm), uint160(amount), uint48(deadline));
    }
    function _reset(address token) private {
        permit2.approve(token, address(posm), 0, 0);
        IERC20(token).forceApprove(address(permit2), 0);
    }
    function _mintOrIncrease(bytes32 poolId, uint256 id, int24 lower, int24 upper, uint256 amount0,
        uint256 amount1, uint128 minimumLiquidity, uint256 deadline)
        private returns (uint256 tokenId, uint256 spent0, uint256 spent1) {
        _deadline(deadline);
        if (amount0 > type(uint128).max || amount1 > type(uint128).max) revert InvalidAmount();
        PoolConfig memory c = _config(poolId, true);
        uint160 current = IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(poolId);
        if (lower % c.key.tickSpacing != 0 || upper % c.key.tickSpacing != 0 || lower >= upper) revert InvalidConfiguration();
        uint128 previousLiquidity = id == 0 ? 0 : posm.getPositionLiquidity(id);
        uint128 liquidity = LiquidityAmounts.getLiquidityForAmounts(current, TickMath.getSqrtPriceAtTick(lower),
            TickMath.getSqrtPriceAtTick(upper), amount0, amount1);
        if (liquidity == 0 || liquidity < minimumLiquidity) revert Slippage();
        (address t0, address t1) = _assets(poolId, c);
        uint256 before0 = IERC20(t0).balanceOf(address(this));
        uint256 before1 = IERC20(t1).balanceOf(address(this));
        ExactToken.pull(t0, msg.sender, amount0);
        ExactToken.pull(t1, msg.sender, amount1);
        bool nativePool = c.key.currency0 == address(0);
        uint256 nativeValue;
        uint256 beforeNative = address(this).balance;
        uint256 beforePosmNative;
        if (nativePool) {
            // No SWEEP: pay exactly rounded-up principal debt. Prior PosM donations
            // cannot fund this operation and any unconsumed value makes it revert.
            nativeValue = _nativeDebt(current, lower, upper, liquidity);
            if (nativeValue > amount0) revert Slippage();
            beforePosmNative = address(posm).balance;
            _unwrap(t0, nativeValue);
        } else _approve(t0, amount0, deadline);
        _approve(t1, amount1, deadline);
        bytes[] memory parameters = new bytes[](2);
        tokenId = id;
        if (id == 0) {
            tokenId = posm.nextTokenId();
            parameters[0] = abi.encode(c.key, lower, upper, uint256(liquidity), uint128(amount0), uint128(amount1),
                access.module(Ids.VAULT), bytes(""));
        } else {
            parameters[0] = abi.encode(id, uint256(liquidity), uint128(amount0), uint128(amount1), bytes(""));
        }
        parameters[1] = abi.encode(c.key.currency0, c.key.currency1);
        posm.modifyLiquidities{value: nativeValue}(
            abi.encode(abi.encodePacked(id == 0 ? MINT : INCREASE, SETTLE_PAIR), parameters), deadline);
        if (nativePool) {
            if (address(posm).balance != beforePosmNative || address(this).balance != beforeNative) revert InvalidState();
        } else _reset(t0);
        _reset(t1);
        (int24 actualLower, int24 actualUpper) = _checkPosition(poolId, tokenId);
        if (actualLower != lower || actualUpper != upper ||
            uint256(posm.getPositionLiquidity(tokenId)) != uint256(previousLiquidity) + liquidity) revert InvalidState();
        uint256 unused0 = IERC20(t0).balanceOf(address(this)) - before0;
        uint256 unused1 = IERC20(t1).balanceOf(address(this)) - before1;
        if (unused0 > amount0 || unused1 > amount1) revert InvalidState();
        spent0 = amount0 - unused0;
        spent1 = amount1 - unused1;
        ExactToken.push(t0, msg.sender, unused0);
        ExactToken.push(t1, msg.sender, unused1);
    }
    function mint(bytes32 poolId, int24 lower, int24 upper, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.VAULT) nonReentrant returns (uint256 tokenId, uint256 spent0, uint256 spent1) {
        return _mintOrIncrease(poolId, 0, lower, upper, amount0, amount1, minimumLiquidity, deadline);
    }
    function increase(bytes32 poolId, uint256 id, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.VAULT) nonReentrant returns (uint256 spent0, uint256 spent1) {
        (int24 lower, int24 upper) = _checkPosition(poolId, id);
        (, spent0, spent1) = _mintOrIncrease(poolId, id, lower, upper, amount0, amount1, minimumLiquidity, deadline);
    }
    function collect(bytes32 poolId, uint256 id, uint256 deadline) external onlyModule(Ids.VAULT) nonReentrant {
        _deadline(deadline);
        PoolConfig memory c = _config(poolId, false);
        _checkPosition(poolId, id);
        bytes[] memory parameters = new bytes[](2);
        parameters[0] = abi.encode(id, uint256(0), uint128(0), uint128(0), bytes(""));
        bool nativePool = c.key.currency0 == address(0);
        uint256 beforeNative = address(this).balance;
        if (nativePool) { nativeSender = address(poolManager); nativeReceived = 0; }
        parameters[1] = abi.encode(c.key.currency0, c.key.currency1, nativePool ? address(this) : access.module(Ids.VAULT));
        uint256 beforeToken1 = nativePool ? IERC20(c.key.currency1).balanceOf(address(this)) : 0;
        posm.modifyLiquidities(abi.encode(abi.encodePacked(DECREASE, TAKE_PAIR), parameters), deadline);
        if (nativePool) {
            _finishNativeCredit(_nativeAsset(poolId), beforeNative, access.module(Ids.VAULT));
            ExactToken.push(c.key.currency1, access.module(Ids.VAULT), IERC20(c.key.currency1).balanceOf(address(this)) - beforeToken1);
        }
    }
    function close(bytes32 poolId, uint256 id, uint256 deadline) external onlyModule(Ids.VAULT) nonReentrant {
        _deadline(deadline);
        PoolConfig memory c = _config(poolId, false);
        _checkPosition(poolId, id);
        (uint256 expected0, uint256 expected1) = amounts(id);
        uint256 min0 = Math.mulDiv(expected0, 10000 - c.maxSlippageBps, 10000);
        uint256 min1 = Math.mulDiv(expected1, 10000 - c.maxSlippageBps, 10000);
        if (min0 > type(uint128).max || min1 > type(uint128).max) revert InvalidAmount();
        bytes[] memory parameters = new bytes[](2);
        parameters[0] = abi.encode(id, uint128(min0), uint128(min1), bytes(""));
        bool nativePool = c.key.currency0 == address(0);
        uint256 beforeNative = address(this).balance;
        if (nativePool) { nativeSender = address(poolManager); nativeReceived = 0; }
        parameters[1] = abi.encode(c.key.currency0, c.key.currency1, nativePool ? address(this) : access.module(Ids.VAULT));
        uint256 beforeToken1 = nativePool ? IERC20(c.key.currency1).balanceOf(address(this)) : 0;
        posm.modifyLiquidities(abi.encode(abi.encodePacked(BURN, TAKE_PAIR), parameters), deadline);
        if (nativePool) {
            _finishNativeCredit(_nativeAsset(poolId), beforeNative, access.module(Ids.VAULT));
            ExactToken.push(c.key.currency1, access.module(Ids.VAULT), IERC20(c.key.currency1).balanceOf(address(this)) - beforeToken1);
        }
    }
    function ticks(uint256 id) external view returns (int24 lower, int24 upper) {
        (, uint256 info) = posm.getPoolAndPositionInfo(id);
        return (int24(uint24(info >> 8)), int24(uint24(info >> 32)));
    }
    function amounts(uint256 id) public view returns (uint256 amount0, uint256 amount1) {
        (PoolKey memory key, uint256 info) = posm.getPoolAndPositionInfo(id);
        int24 lower = int24(uint24(info >> 8));
        int24 upper = int24(uint24(info >> 32));
        uint160 priceX96 = spot(keccak256(abi.encode(key)));
        uint160 a = TickMath.getSqrtPriceAtTick(lower);
        uint160 b = TickMath.getSqrtPriceAtTick(upper);
        uint128 liquidity = posm.getPositionLiquidity(id);
        if (priceX96 <= a) amount0 = SqrtPriceMath.getAmount0Delta(a, b, liquidity, false);
        else if (priceX96 >= b) amount1 = SqrtPriceMath.getAmount1Delta(a, b, liquidity, false);
        else {
            amount0 = SqrtPriceMath.getAmount0Delta(priceX96, b, liquidity, false);
            amount1 = SqrtPriceMath.getAmount1Delta(a, priceX96, liquidity, false);
        }
    }
    function swap(bytes32 poolId, bool zeroForOne, uint256 amountIn, uint256 minimumOut, uint256 deadline)
        external nonReentrant returns (uint256 amountOut) {
        if (!access.isSealed() || (msg.sender != access.module(Ids.VAULT) && msg.sender != access.module(Ids.BUYBACK) &&
            msg.sender != IPairSwapCompanion(access.module(Ids.MIGRATION)).pairMigration())) revert Unauthorized();
        _deadline(deadline);
        if (amountIn == 0 || amountIn > type(uint128).max) revert InvalidAmount();
        PoolConfig memory c = _config(poolId, true);
        IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(poolId);
        (address token0, address token1) = _assets(poolId, c);
        address input = zeroForOne ? token0 : token1;
        address output = zeroForOne ? token1 : token0;
        uint256 protocolMinimum = Math.mulDiv(IZZZOracle(access.module(Ids.ORACLE)).quote(input, output, amountIn),
            10000 - c.maxSlippageBps, 10000);
        if (minimumOut < protocolMinimum || minimumOut == 0) revert Slippage();
        ExactToken.pull(input, msg.sender, amountIn);
        uint256 beforeNative = address(this).balance;
        if (c.key.currency0 == address(0) && zeroForOne) _unwrap(token0, amountIn);
        uint256 beforeOutput = IERC20(output).balanceOf(msg.sender);
        bytes memory payload = abi.encode(c.key, zeroForOne, amountIn, minimumOut, msg.sender);
        pendingSwapHash = keccak256(payload);
        amountOut = abi.decode(poolManager.unlock(payload), (uint256));
        if (pendingSwapHash != bytes32(0) || amountOut < minimumOut ||
            IERC20(output).balanceOf(msg.sender) != beforeOutput + amountOut ||
            address(this).balance != beforeNative) revert InvalidState();
        IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(poolId);
    }
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        if (msg.sender != address(poolManager) || pendingSwapHash == bytes32(0) ||
            pendingSwapHash != keccak256(data)) revert Unauthorized();
        pendingSwapHash = bytes32(0);
        (PoolKey memory key, bool zeroForOne, uint256 amountIn, uint256 minOut, address recipient) =
            abi.decode(data, (PoolKey, bool, uint256, uint256, address));
        int256 delta = poolManager.swap(key, IPoolManagerMinimal.SwapParams(zeroForOne, -int256(amountIn),
            zeroForOne ? TickMath.MIN_SQRT_PRICE + 1 : TickMath.MAX_SQRT_PRICE - 1), bytes(""));
        int128 delta0 = int128(delta >> 128);
        int128 delta1 = int128(uint128(uint256(delta)));
        int128 inputDelta = zeroForOne ? delta0 : delta1;
        int128 outputDelta = zeroForOne ? delta1 : delta0;
        if (inputDelta >= 0 || outputDelta <= 0 || uint256(-int256(inputDelta)) != amountIn ||
            uint256(int256(outputDelta)) < minOut) revert Slippage();
        address input = zeroForOne ? key.currency0 : key.currency1;
        address output = zeroForOne ? key.currency1 : key.currency0;
        poolManager.sync(input);
        if (input == address(0)) {
            if (poolManager.settle{value: amountIn}() != amountIn) revert InvalidState();
        } else {
            ExactToken.push(input, address(poolManager), amountIn);
            if (poolManager.settle() != amountIn) revert InvalidState();
        }
        uint256 amountOut = uint256(int256(outputDelta));
        if (output == address(0)) {
            uint256 beforeNative = address(this).balance;
            nativeSender = address(poolManager);
            nativeReceived = 0;
            poolManager.take(output, address(this), amountOut);
            if (nativeReceived != amountOut) revert InvalidState();
            _finishNativeCredit(_nativeAsset(keccak256(abi.encode(key))), beforeNative, recipient);
        } else poolManager.take(output, recipient, amountOut);
        return abi.encode(amountOut);
    }
}
