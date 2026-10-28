// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
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
import {ZZZLPBalancer} from "./ZZZLPBalancer.sol";
import {IZZZPools, IZZZStrategy, IPositionManagerMinimal, IStateViewMinimal,
    IPermit2Minimal, IPoolManagerMinimal} from "./interfaces/IZZZ.sol";

interface INativePoolAssets {
    function isNativePool(bytes32 poolId) external view returns (bool);
}

/// @notice Typed v4 operations only. No arbitrary call/action/recipient entrypoint.
/// Vault owns every LP NFT. Per-NFT approvals authorize this immutable module.
contract ZZZLiquidityManager is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    uint256 public constant LP_ROUTING_VERSION = 1;
    uint256 public constant EXECUTION_QUALITY_VERSION = 1;
    ZZZLPBalancer public immutable balancingRouter;
    IPositionManagerMinimal private immutable posm;
    IStateViewMinimal public immutable stateView;
    IPoolManagerMinimal public immutable poolManager;
    IPermit2Minimal public immutable permit2;
    bytes32 private pendingSwapHash;
    // A native credit is accepted only during an expected core call.
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
        balancingRouter = new ZZZLPBalancer(controller,poolManager_,stateView_);
    }
    receive() external payable {
        if (msg.sender != nativeSender || nativeSender == address(0)) revert Unauthorized();
        nativeReceived += msg.value;
    }
    function positionManager() external view returns (address) { return address(posm); }
    /// @notice Pins balancing policy across Vault approval/reset callbacks too.
    function balanceContext(bytes32 targetPool) external view returns (bytes32) {
        return _balanceContext(targetPool);
    }
    function _balanceContext(bytes32 targetPool) private view returns (bytes32) {
        return keccak256(abi.encode(address(balancingRouter),balancingRouter.executionRevision(),
            balancingRouter.policyFingerprint(targetPool,bytes32(0))));
    }
    function spot(bytes32 poolId) public view returns (uint160 priceX96) {
        (priceX96,,,) = stateView.getSlot0(poolId);
    }
    function _config(bytes32 poolId, bool requireOperations) private view returns (PoolConfig memory c) {
        c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        if ((requireOperations && !c.operationsEnabled) || keccak256(abi.encode(c.key)) != poolId) revert InvalidState();
        if (c.key.currency0 == address(0)) {
            // Native identity is the real zero currency, validated without a wrapper.
            if (!INativePoolAssets(access.module(Ids.POOLS)).isNativePool(poolId) || c.key.fee > 100000 ||
                c.key.hooks != address(0)) revert InvalidState();
        } else if (c.key.hooks != address(0)) revert InvalidState();
    }
    function _balance(address token, address owner) private view returns (uint256) {
        return token == address(0) ? owner.balance : IERC20(token).balanceOf(owner);
    }
    function _sendNative(address recipient, uint256 amount) private {
        if (amount == 0) return;
        uint256 beforeNative = address(this).balance;
        (bool ok,) = recipient.call{value: amount}("");
        if (!ok || address(this).balance + amount != beforeNative) revert InvalidState();
    }
    function _finishNativeCredit(uint256 beforeNative, address recipient) private {
        nativeSender = address(0);
        uint256 amount = nativeReceived;
        nativeReceived = 0;
        if (address(this).balance != beforeNative + amount) revert InvalidState();
        _sendNative(recipient, amount);
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
        address t0 = c.key.currency0;
        address t1 = c.key.currency1;
        bool nativePool = t0 == address(0);
        if (msg.value != (nativePool ? amount0 : 0)) revert InvalidAmount();
        uint256 before0 = _balance(t0, address(this)) - msg.value;
        uint256 before1 = IERC20(t1).balanceOf(address(this));
        if (!nativePool) ExactToken.pull(t0, msg.sender, amount0);
        ExactToken.pull(t1, msg.sender, amount1);
        uint256 nativeValue;
        uint256 beforeNative = address(this).balance;
        if (nativePool && beforeNative != before0 + msg.value) revert InvalidState();
        uint256 beforePosmNative;
        if (nativePool) {
            // No SWEEP: pay exactly rounded-up principal debt. Prior PosM donations
            // cannot fund this operation and any unconsumed value makes it revert.
            nativeValue = _nativeDebt(current, lower, upper, liquidity);
            if (nativeValue > amount0) revert Slippage();
            beforePosmNative = address(posm).balance;
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
            if (address(posm).balance != beforePosmNative || address(this).balance + nativeValue != beforeNative) revert InvalidState();
        } else _reset(t0);
        _reset(t1);
        uint256 unused0 = _balance(t0, address(this)) - before0;
        uint256 unused1 = IERC20(t1).balanceOf(address(this)) - before1;
        if (unused0 > amount0 || unused1 > amount1) revert InvalidState();
        spent0 = amount0 - unused0;
        spent1 = amount1 - unused1;
        if (nativePool) _sendNative(msg.sender, unused0);
        else ExactToken.push(t0, msg.sender, unused0);
        ExactToken.push(t1, msg.sender, unused1);
        // A static hookless mint/increase does not move the pool price. Token
        // approvals, pulls, settlement and refunds can nevertheless call external
        // code. Check the final mark and physical LP only after ALL those calls,
        // so incumbent repricing or a late LP mutation cannot masquerade as new LP.
        if (IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(poolId) != current) revert Slippage();
        (int24 actualLower, int24 actualUpper) = _checkPosition(poolId, tokenId);
        if (actualLower != lower || actualUpper != upper ||
            uint256(posm.getPositionLiquidity(tokenId)) != uint256(previousLiquidity) + liquidity) revert InvalidState();
    }
    function mint(bytes32 poolId, int24 lower, int24 upper, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline)
        external payable onlyModule(Ids.VAULT) nonReentrant returns (uint256 tokenId, uint256 spent0, uint256 spent1) {
        return _mintOrIncrease(poolId, 0, lower, upper, amount0, amount1, minimumLiquidity, deadline);
    }
    function increase(bytes32 poolId, uint256 id, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline)
        external payable onlyModule(Ids.VAULT) nonReentrant returns (uint256 spent0, uint256 spent1) {
        (int24 lower, int24 upper) = _checkPosition(poolId, id);
        (, spent0, spent1) = _mintOrIncrease(poolId, id, lower, upper, amount0, amount1, minimumLiquidity, deadline);
    }
    function collect(bytes32 poolId, uint256 id, uint256 deadline) external onlyModule(Ids.VAULT) nonReentrant {
        _deadline(deadline);
        PoolConfig memory c = _config(poolId, false);
        _checkPosition(poolId, id);
        bytes[] memory parameters = new bytes[](2);
        parameters[0] = abi.encode(id, uint256(0), uint128(0), uint128(0), bytes(""));
        _settleTakePair(c.key, DECREASE, parameters, deadline);
    }
    /// @dev Only collect/close supply fixed typed actions. Keep recipient reads
    /// after their original callbacks; native and ERC20 prefunds stay untouched.
    function _settleTakePair(PoolKey memory key, uint8 action, bytes[] memory parameters, uint256 deadline) private {
        bool nativePool = key.currency0 == address(0);
        uint256 beforeNative = address(this).balance;
        if (nativePool) { nativeSender = address(poolManager); nativeReceived = 0; }
        parameters[1] = abi.encode(key.currency0, key.currency1, nativePool ? address(this) : access.module(Ids.VAULT));
        uint256 beforeToken1 = nativePool ? IERC20(key.currency1).balanceOf(address(this)) : 0;
        posm.modifyLiquidities(abi.encode(abi.encodePacked(action, TAKE_PAIR), parameters), deadline);
        if (nativePool) {
            _finishNativeCredit(beforeNative, access.module(Ids.VAULT));
            ExactToken.push(key.currency1, access.module(Ids.VAULT), IERC20(key.currency1).balanceOf(address(this)) - beforeToken1);
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
        _settleTakePair(c.key, BURN, parameters, deadline);
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
        external payable nonReentrant returns (uint256 amountOut) {
        if (!access.isSealed() || (msg.sender != access.module(Ids.VAULT) && msg.sender != access.module(Ids.BUYBACK))) revert Unauthorized();
        _deadline(deadline);
        if (amountIn == 0 || amountIn > type(uint128).max) revert InvalidAmount();
        PoolConfig memory c = _config(poolId,true);
        address input = zeroForOne ? c.key.currency0 : c.key.currency1;
        if (msg.value != (input == address(0) ? amountIn : 0)) revert InvalidAmount();
        bytes32 context = _balanceContext(poolId);
        if (input != address(0)) ExactToken.pull(input, msg.sender, amountIn);
        uint256 beforeNative = address(this).balance - msg.value;
        amountOut = _swapExact(poolId,c,zeroForOne,amountIn,minimumOut,msg.sender);
        if (address(this).balance != beforeNative || _balanceContext(poolId) != context) revert InvalidState();
    }
    function _swapExact(bytes32 poolId, PoolConfig memory c, bool zeroForOne, uint256 amountIn, uint256 minimumOut,
        address recipient) private returns (uint256 amountOut) {
        IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(poolId);
        address output = zeroForOne ? c.key.currency1 : c.key.currency0;
        if (minimumOut == 0) revert Slippage();
        minimumOut = Math.max(minimumOut,IZZZStrategy(access.module(Ids.STRATEGY)).minimumOutput(poolId,zeroForOne,amountIn));
        uint256 beforeOutput = _balance(output,recipient);
        bytes memory payload = abi.encode(c.key, zeroForOne, amountIn, minimumOut, recipient);
        pendingSwapHash = keccak256(payload);
        amountOut = abi.decode(poolManager.unlock(payload), (uint256));
        if (pendingSwapHash != bytes32(0) || amountOut < minimumOut ||
            _balance(output,recipient) != beforeOutput+amountOut) revert InvalidState();
        IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(poolId);
    }
    /// @notice Balance only the supplied budget, executing one selected swap.
    /// The LP destination/ticks stay fixed; catalog routes never receive custody.
    function balance(bytes32 targetPool,uint256 existingLpId,uint256 amount0,uint256 amount1,uint256 deadline)
        external payable onlyModule(Ids.VAULT) nonReentrant returns (uint256 balanced0,uint256 balanced1) {
        _deadline(deadline);
        if (amount0 > type(uint128).max || amount1 > type(uint128).max || msg.value != amount0) revert InvalidAmount();
        PoolConfig memory target = _config(targetPool,true);
        if (target.key.currency0 != address(0)) revert InvalidConfiguration();
        bytes32 context = _balanceContext(targetPool);
        uint256 nativePrefund = address(this).balance-msg.value;
        uint256 tokenPrefund = IERC20(target.key.currency1).balanceOf(address(this));
        int24 lower; int24 upper; uint128 priorLiquidity;
        if (existingLpId != 0) {
            (lower,upper) = _checkPosition(targetPool,existingLpId);
            priorLiquidity = posm.getPositionLiquidity(existingLpId);
        } else (lower,upper,) = IZZZStrategy(access.module(Ids.STRATEGY)).target(targetPool);
        // Pull before quoting: even a token callback cannot intervene between
        // the simulated route and the actual swap. Refund only this budget.
        ExactToken.pull(target.key.currency1,msg.sender,amount1);
        if (_balanceContext(targetPool) != context) revert InvalidState();
        ZZZLPBalancer.Plan memory p = balancingRouter.plan(targetPool,lower,upper,amount0,amount1);
        balanced0 = amount0; balanced1 = amount1;
        uint256 refund0 = amount0; uint256 refund1 = amount1;
        if (p.amountIn != 0) {
            PoolConfig memory venue = _config(p.poolId,true);
            if (venue.key.currency0 != address(0) || venue.key.currency1 != target.key.currency1 ||
                p.amountIn > (p.zeroForOne ? amount0 : amount1)) revert InvalidState();
            uint256 output = _swapExact(p.poolId,venue,p.zeroForOne,p.amountIn,p.minimumOut,msg.sender);
            if (output != p.amountOut || spot(p.poolId) != p.sqrtAfter) revert Slippage();
            if (p.zeroForOne) { balanced0 -= p.amountIn; balanced1 += output; refund0 -= p.amountIn; }
            else { balanced1 -= p.amountIn; balanced0 += output; refund1 -= p.amountIn; }
        }
        _sendNative(msg.sender,refund0);
        ExactToken.push(target.key.currency1,msg.sender,refund1);
        if (existingLpId != 0) {
            (int24 finalLower,int24 finalUpper) = _checkPosition(targetPool,existingLpId);
            if (lower != finalLower || upper != finalUpper || posm.getPositionLiquidity(existingLpId) != priorLiquidity) revert InvalidState();
        }
        if (address(this).balance != nativePrefund || IERC20(target.key.currency1).balanceOf(address(this)) != tokenPrefund ||
            balancingRouter.executionRevision() != p.revision ||
            balancingRouter.policyFingerprint(targetPool,p.poolId) != p.fingerprint ||
            IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(targetPool) != p.targetSqrtAfter) revert InvalidState();
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
            _finishNativeCredit(beforeNative, recipient);
        } else poolManager.take(output, recipient, amountOut);
        return abi.encode(amountOut);
    }
}
