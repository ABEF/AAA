// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "./libraries/ZZZTypes.sol";
import {IZZZPools, IZZZOracle, IZZZLiquidity, IZZZVault} from "./interfaces/IZZZ.sol";

/// @notice Stateless policy. Only the vault can commit position state changes.
contract ZZZStrategy is ZZZModule {
    constructor(address controller) ZZZModule(controller) {}
    function _floor(int24 tick, int24 spacing) private pure returns (int24) {
        int24 quotient = tick / spacing;
        if (tick < 0 && tick % spacing != 0) --quotient;
        return quotient * spacing;
    }
    function target(bytes32 poolId) public view returns (int24 lower, int24 upper, uint160 referenceX96) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        if (!c.operationsEnabled) revert InvalidState();
        referenceX96 = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0, c.key.currency1);
        uint256 lowerRoot = Math.mulDiv(referenceX96, Math.sqrt(uint256(10000 - c.rangeBps) * 1e28), 1e16);
        uint256 upperRoot = Math.mulDiv(referenceX96, Math.sqrt(uint256(10000 + c.rangeBps) * 1e28), 1e16);
        if (lowerRoot <= TickMath.MIN_SQRT_PRICE || upperRoot >= TickMath.MAX_SQRT_PRICE) revert InvalidConfiguration();
        lower = _floor(TickMath.getTickAtSqrtPrice(uint160(lowerRoot)), c.key.tickSpacing);
        // Always round the upper limit outward, including an exact tick boundary.
        upper = _floor(TickMath.getTickAtSqrtPrice(uint160(upperRoot)), c.key.tickSpacing) + c.key.tickSpacing;
        if (lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper) revert InvalidConfiguration();
    }
    function validatePrice(bytes32 poolId) public view returns (uint160 spotX96) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        if (!c.operationsEnabled) revert InvalidState();
        uint160 referenceX96 = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0, c.key.currency1);
        spotX96 = IZZZLiquidity(access.module(Ids.LIQUIDITY)).spot(poolId);
        if (spotX96 == 0) revert InvalidState();
        uint256 relativeRoot = Math.mulDiv(spotX96, 1e18, referenceX96);
        uint256 relativePrice = Math.mulDiv(relativeRoot, relativeRoot, 1e18);
        uint256 difference = relativePrice > 1e18 ? relativePrice - 1e18 : 1e18 - relativePrice;
        if (difference > uint256(c.maxSpotDeviationBps) * 1e14) revert Slippage();
    }
    function needsRebalance(uint256 id) external view returns (bool) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).position(id);
        if (p.status != PositionStatus.Active || p.centerX96 == 0) return false;
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(p.poolId);
        if (!c.operationsEnabled || block.timestamp < p.lastRebalance + c.minRebalanceInterval) return false;
        uint160 ref = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0, c.key.currency1);
        uint256 rootRatio = Math.mulDiv(ref, 1e18, p.centerX96);
        uint256 priceRatio = Math.mulDiv(rootRatio, rootRatio, 1e18);
        uint256 delta = priceRatio > 1e18 ? priceRatio - 1e18 : 1e18 - priceRatio;
        return delta >= uint256(c.triggerBps) * 1e14;
    }
    function swapPlan(bytes32 poolId, uint256 amount0, uint256 amount1)
        external view returns (bool zeroForOne, uint256 amountIn, uint256 minimumOut) {
        (int24 lower, int24 upper,) = target(poolId);
        return _plan(poolId, lower, upper, amount0, amount1);
    }
    function compoundPlan(uint256 id, uint256 amount0, uint256 amount1)
        external view returns (bool, uint256, uint256) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).position(id);
        (int24 lower, int24 upper) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).ticks(p.lpTokenId);
        return _plan(p.poolId, lower, upper, amount0, amount1);
    }
    function _plan(bytes32 poolId, int24 lower, int24 upper, uint256 amount0, uint256 amount1)
        private view returns (bool zeroForOne, uint256 amountIn, uint256 minimumOut) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
        uint160 spotX96 = validatePrice(poolId);
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
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        uint256 v0 = oracle.value(c.key.currency0, amount0);
        uint256 v1 = oracle.value(c.key.currency1, amount1);
        uint256 u0 = oracle.value(c.key.currency0, unit0);
        uint256 u1 = oracle.value(c.key.currency1, unit1);
        if (u0 + u1 == 0) revert InvalidAmount();
        uint256 desired0 = Math.mulDiv(v0 + v1, u0, u0 + u1);
        zeroForOne = v0 > desired0;
        address input = zeroForOne ? c.key.currency0 : c.key.currency1;
        address output = zeroForOne ? c.key.currency1 : c.key.currency0;
        uint256 excess = zeroForOne ? v0 - desired0 : desired0 - v0;
        amountIn = Math.mulDiv(excess, 10 ** oracle.tokenDecimals(input), oracle.price(input));
        if (amountIn > (zeroForOne ? amount0 : amount1)) revert InvalidState();
        minimumOut = Math.mulDiv(oracle.quote(input, output, amountIn), 10000 - c.maxSlippageBps, 10000);
        if (minimumOut == 0) amountIn = 0;
    }
}
