// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZPriceMath} from "./libraries/ZZZPriceMath.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "./libraries/ZZZTypes.sol";
import {IZZZPools, IZZZOracle, IZZZLiquidity, IZZZVault, IStateViewMinimal} from "./interfaces/IZZZ.sol";

interface IV4FeeState { function stateView() external view returns (IStateViewMinimal); }

/// @notice Stateless policy. Only the vault can commit position state changes.
contract ZZZStrategy is ZZZModule {
    struct AssetPrice { uint256 lower; uint256 upper; uint256 scale; }
    struct PairPrices { AssetPrice first; AssetPrice second; uint160 referenceX96; }
    constructor(address controller) ZZZModule(controller) {}
    function _floor(int24 tick, int24 spacing) private pure returns (int24) {
        int24 quotient = tick / spacing;
        if (tick < 0 && tick % spacing != 0) --quotient;
        return quotient * spacing;
    }
    function target(bytes32 poolId) public view returns (int24 lower, int24 upper, uint160 referenceX96) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        if (!c.operationsEnabled) revert InvalidState();
        referenceX96 = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0, c.key.currency1);
        (lower, upper) = _range(c, referenceX96);
    }
    function _range(PoolConfig memory c, uint160 referenceX96) private pure returns (int24 lower, int24 upper) {
        uint256 lowerRoot = Math.mulDiv(referenceX96, Math.sqrt(uint256(10000 - c.rangeBps) * 1e28), 1e16);
        uint256 upperRoot = Math.mulDiv(referenceX96, Math.sqrt(uint256(10000 + c.rangeBps) * 1e28), 1e16);
        if (lowerRoot <= TickMath.MIN_SQRT_PRICE || upperRoot >= TickMath.MAX_SQRT_PRICE) revert InvalidConfiguration();
        lower = _floor(TickMath.getTickAtSqrtPrice(uint160(lowerRoot)), c.key.tickSpacing);
        // Always round the upper limit outward, including an exact tick boundary.
        upper = _floor(TickMath.getTickAtSqrtPrice(uint160(upperRoot)), c.key.tickSpacing) + c.key.tickSpacing;
        if (lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper) revert InvalidConfiguration();
    }
    function validatePrice(bytes32 poolId) public view returns (uint160 spotX96) {
        return _validatePrice(poolId, true);
    }
    /// @notice A disabled source pool can still exit through governed custody paths.
    /// Oracle freshness and spot-deviation checks remain mandatory.
    function validateExitPrice(bytes32 poolId) public view returns (uint160 spotX96) {
        return _validatePrice(poolId, false);
    }
    function _validatePrice(bytes32 poolId, bool requireOperations) private view returns (uint160 spotX96) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        if (requireOperations && !c.operationsEnabled) revert InvalidState();
        uint160 referenceX96 = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0, c.key.currency1);
        return _checkedSpot(poolId, c, referenceX96);
    }
    function _checkedSpot(bytes32 poolId, PoolConfig memory c, uint160 referenceX96) private view returns (uint160 spotX96) {
        spotX96 = IZZZLiquidity(access.module(Ids.LIQUIDITY)).spot(poolId);
        if (spotX96 == 0) revert InvalidState();
        uint256 relativeRoot = Math.mulDiv(spotX96, 1e18, referenceX96);
        uint256 relativePrice = Math.mulDiv(relativeRoot, relativeRoot, 1e18);
        uint256 difference = relativePrice > 1e18 ? relativePrice - 1e18 : 1e18 - relativePrice;
        if (difference > uint256(c.maxSpotDeviationBps) * 1e14) revert Slippage();
    }
    function needsRebalance(uint256 id) external view returns (bool) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(id);
        if (p.status != PositionStatus.Active || p.centerX96 == 0 || p.lpTokenId == 0) return false;
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if (!c.operationsEnabled || block.timestamp < p.lastRebalance + c.minRebalanceInterval) return false;
        uint160 ref = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0, c.key.currency1);
        uint256 rootRatio = Math.mulDiv(ref, 1e18, p.centerX96);
        uint256 priceRatio = Math.mulDiv(rootRatio, rootRatio, 1e18);
        uint256 delta = priceRatio > 1e18 ? priceRatio - 1e18 : 1e18 - priceRatio;
        return delta >= uint256(c.triggerBps) * 1e14 || _rangeUpdatePending(p, c);
    }
    /// @notice A timelocked width change can require replacement even at a flat price.
    /// Pending is not execution eligibility: cooldown, operations and all Vault
    /// guards still apply. Comparing at the recorded center avoids price-drift churn.
    function rangeUpdatePending(uint256 id) external view returns (bool) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(id);
        if (p.status != PositionStatus.Active || p.centerX96 == 0 || p.lpTokenId == 0) return false;
        return _rangeUpdatePending(p, IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId));
    }
    function _rangeUpdatePending(Position memory p, PoolConfig memory c) private view returns (bool) {
        (int24 expectedLower, int24 expectedUpper) = _range(c, p.centerX96);
        (int24 lower, int24 upper) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).ticks(p.lpTokenId);
        if (lower >= upper) revert InvalidState();
        return lower != expectedLower || upper != expectedUpper;
    }
    function swapPlan(bytes32 poolId, uint256 amount0, uint256 amount1)
        external view returns (bool zeroForOne, uint256 amountIn, uint256 minimumOut) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        if (!c.operationsEnabled) revert InvalidState();
        PairPrices memory prices = _pairPrices(c);
        (int24 lower, int24 upper) = _range(c, prices.referenceX96);
        return _plan(poolId, c, prices, lower, upper, amount0, amount1);
    }
    function compoundPlan(uint256 id, uint256 amount0, uint256 amount1)
        external view returns (bool, uint256, uint256) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(id);
        (int24 lower, int24 upper) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).ticks(p.lpTokenId);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if (!c.operationsEnabled) revert InvalidState();
        return _plan(p.poolId, c, _pairPrices(c), lower, upper, amount0, amount1);
    }
    /// @dev One read-only plan uses one fully validated pair vector. This is
    /// memory-only: execution and final contribution checks still read afresh.
    function _pairPrices(PoolConfig memory c) private view returns (PairPrices memory p) {
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        (p.first.lower,p.first.upper,) = oracle.priceBounds(c.key.currency0);
        (p.second.lower,p.second.upper,) = oracle.priceBounds(c.key.currency1);
        uint8 d0 = oracle.tokenDecimals(c.key.currency0);
        uint8 d1 = oracle.tokenDecimals(c.key.currency1);
        p.first.scale = 10 ** d0; p.second.scale = 10 ** d1;
        p.referenceX96 = ZZZPriceMath.referenceX96(p.first.lower,p.second.lower,d0,d1,c.key.currency0);
    }
    function _value(AssetPrice memory p, uint256 amount) private pure returns (uint256) {
        return Math.mulDiv(amount,p.lower,p.scale);
    }
    function _plan(bytes32 poolId, PoolConfig memory c, PairPrices memory prices,
        int24 lower, int24 upper, uint256 amount0, uint256 amount1)
        private view returns (bool zeroForOne, uint256 amountIn, uint256 minimumOut) {
        uint160 spotX96 = _checkedSpot(poolId,c,prices.referenceX96);
        uint160 a = TickMath.getSqrtPriceAtTick(lower);
        uint160 b = TickMath.getSqrtPriceAtTick(upper);
        uint256 unit0;
        uint256 unit1;
        if (spotX96 <= a) unit0 = SqrtPriceMath.getAmount0Delta(a, b, uint128(1e18), false);
        else if (spotX96 >= b) unit1 = SqrtPriceMath.getAmount1Delta(a, b, uint128(1e18), false);
        else {
            unit0 = SqrtPriceMath.getAmount0Delta(spotX96, b, uint128(1e18), false);
            unit1 = SqrtPriceMath.getAmount1Delta(a, spotX96, uint128(1e18), false);
        }
        uint256 v0 = _value(prices.first, amount0);
        uint256 v1 = _value(prices.second, amount1);
        uint256 u0 = _value(prices.first, unit0);
        uint256 u1 = _value(prices.second, unit1);
        if (u0 + u1 == 0) revert InvalidAmount();
        uint256 desired0 = Math.mulDiv(v0 + v1, u0, u0 + u1);
        zeroForOne = v0 > desired0;
        AssetPrice memory input = zeroForOne ? prices.first : prices.second;
        AssetPrice memory output = zeroForOne ? prices.second : prices.first;
        uint256 excess = zeroForOne ? v0 - desired0 : desired0 - v0;
        {
            // Every admitted v4 pool is static and hookless. Size the net pair
            // after its actual directional protocol + LP fee, including ERC20
            // destinations reached by a native-to-WETH pool move.
            (,, uint24 protocol, uint24 lpFee) = IV4FeeState(access.module(Ids.LIQUIDITY)).stateView().getSlot0(poolId);
            uint256 pf = zeroForOne ? protocol & 0xfff : protocol >> 12;
            if (c.key.hooks != address(0) || lpFee != c.key.fee || pf > 1000) revert InvalidConfiguration();
            uint256 fee = pf + uint256(lpFee) - Math.mulDiv(pf, lpFee, 1_000_000);
            uint256 inputWeight = Math.mulDiv(zeroForOne ? u0 : u1, 1e18, u0 + u1);
            excess = Math.mulDiv(excess, 1e18, 1e18 - Math.mulDiv(inputWeight, fee, 1_000_000));
        }
        amountIn = Math.mulDiv(excess, input.scale, input.lower);
        if (amountIn > (zeroForOne ? amount0 : amount1)) revert InvalidState();
        // Preserve Oracle.quote's two floor operations exactly: upper-valued
        // source USD first, then lower-valued output raw units.
        uint256 quoted = Math.mulDiv(Math.mulDiv(amountIn,input.upper,input.scale),output.scale,output.lower);
        minimumOut = Math.mulDiv(quoted, 10000 - c.maxSlippageBps, 10000);
        if (minimumOut == 0) amountIn = 0;
    }
}
