// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZPriceMath} from "./libraries/ZZZPriceMath.sol";
import {ZZZRebalanceConfirmation} from "./ZZZRebalanceConfirmation.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "./libraries/ZZZTypes.sol";
import {IZZZPools, IZZZOracle, IZZZLiquidity, IZZZVault, IStateViewMinimal} from "./interfaces/IZZZ.sol";

interface IV4FeeState { function stateView() external view returns (IStateViewMinimal); }
interface IRangeRegistry { function applyKeeperRange(bytes32 poolId,uint16 rangeBps) external; }

/// @notice Bounded strategy policy. Only the vault commits physical LP changes.
contract ZZZStrategy is ZZZModule {
    uint256 public constant RANGE_POLICY_VERSION = 1;
    /// @notice Physical outside-range upkeep, with a governed range-change exception.
    uint256 public constant MAINTENANCE_POLICY_VERSION = 2;
    uint256 public constant REBALANCE_CONFIRMATION_VERSION = 2;
    ZZZRebalanceConfirmation public immutable rebalanceConfirmation;
    uint256 public constant EXECUTION_QUALITY_VERSION = 1;
    uint256 public constant MAX_ADDITIONAL_LOSS_BPS = 1000;
    uint16 public additionalLossBps = 100;
    uint64 public executionQualityRevision;
    /// 0 preserves historical token1/token0; 1 expresses token0/token1.
    mapping(bytes32 => uint8) public rangeOrientation;
    struct KeeperRangePolicy {
        bool enabled;
        uint16 narrowTriggerBps;
        uint16 widenTriggerBps;
        uint32 minInterval;
        uint64 lastChange;
        bytes32 configurationHash;
        bytes32 reviewHash;
    }
    mapping(bytes32 => KeeperRangePolicy) public keeperRangePolicy;
    uint256 public activeKeeperRangePolicies;
    event RangeOrientationChanged(bytes32 indexed poolId,uint8 previous,uint8 current);
    event KeeperRangePolicyChanged(bytes32 indexed poolId,bool enabled,bytes32 configurationHash,bytes32 reviewHash);
    event KeeperRangeSelected(bytes32 indexed poolId,uint16 previous,uint16 current,bytes32 reviewHash);
    event AdditionalLossLimitChanged(uint16 previous,uint16 current,uint64 revision,bytes32 indexed reviewHash);
    struct AssetPrice { uint256 lower; uint256 upper; uint256 scale; }
    struct PairPrices { AssetPrice first; AssetPrice second; uint160 referenceX96; }
    constructor(address controller) ZZZModule(controller) {
        rebalanceConfirmation = new ZZZRebalanceConfirmation(controller);
    }
    /// @notice Separate from raw needsRebalance so pending upkeep blocks compound.
    function rebalanceReady(uint256 id) external view returns(bool) { return rebalanceConfirmation.ready(id); }
    function rebalanceObservation(uint256 id) external view returns(uint8 side,bytes32 identity,bool manual) {
        return rebalanceConfirmation.condition(id);
    }
    /// @notice Extra oracle-relative loss after actual directional trading fees;
    /// gross/caller/operation floors remain independent. Available for post-exit
    /// buybacks and ordinary pause, but not preparation/canonical lifecycle locks.
    function setAdditionalLossBps(uint16 limit,bytes32 reviewHash) external onlyGovernance operating {
        if (limit > MAX_ADDITIONAL_LOSS_BPS || reviewHash == bytes32(0)) revert InvalidConfiguration();
        uint16 previous = additionalLossBps;
        additionalLossBps = limit;
        ++executionQualityRevision;
        emit AdditionalLossLimitChanged(previous,limit,executionQualityRevision,reviewHash);
    }
    /// @notice Inclusion-time minimum, not a keeper-selected price or swap quote.
    /// Known fees are removed from raw input; rounding/impact/reference spread
    /// still consumes the additional limit. Never exempts fees from gross caps.
    function minimumOutput(bytes32 poolId,bool direction,uint256 amount) external view returns(uint256) {
        return _minimumOutput(poolId,direction,amount,true);
    }
    /// @notice Same financial floor without operations-enabled admission, for a
    /// separately authorized paused emergency which deliberately bypasses it.
    function minimumOutputForExit(bytes32 poolId,bool direction,uint256 amount) external view returns(uint256) {
        return _minimumOutput(poolId,direction,amount,false);
    }
    function _minimumOutput(bytes32 poolId,bool direction,uint256 amount,bool requireOperations) private view returns(uint256) {
        if (amount == 0 || amount > type(uint128).max) revert InvalidAmount();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        if (requireOperations && !c.operationsEnabled) revert InvalidState();
        PairPrices memory prices = _pairPrices(c);
        return _minimum(prices,direction,amount,c.maxSlippageBps,_swapFee(poolId,c,direction));
    }
    function _swapFee(bytes32 poolId,PoolConfig memory c,bool direction) private view returns(uint256) {
        (,,uint24 protocol,uint24 fee) = IV4FeeState(access.module(Ids.LIQUIDITY)).stateView().getSlot0(poolId);
        if (c.key.hooks != address(0) || fee != c.key.fee || fee > 100000 ||
            (protocol & 0xfff) > 1000 || protocol >> 12 > 1000) revert InvalidConfiguration();
        uint256 selected = direction ? protocol & 0xfff : protocol >> 12;
        return selected+fee-Math.mulDiv(selected,fee,1_000_000);
    }
    function _quoted(PairPrices memory prices,bool direction,uint256 amount) private pure returns(uint256) {
        AssetPrice memory input = direction ? prices.first : prices.second;
        AssetPrice memory output = direction ? prices.second : prices.first;
        return Math.mulDiv(Math.mulDiv(amount,input.upper,input.scale),output.scale,output.lower);
    }
    function _minimum(PairPrices memory prices,bool direction,uint256 amount,uint16 grossLoss,uint256 fee)
        private view returns(uint256) {
        uint256 gross = Math.mulDiv(_quoted(prices,direction,amount),10000-grossLoss,10000);
        uint256 net = Math.mulDiv(amount,1_000_000-fee,1_000_000);
        return Math.max(gross,Math.mulDiv(_quoted(prices,direction,net),10000-additionalLossBps,10000,Math.Rounding.Ceil));
    }
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
    function _range(PoolConfig memory c, uint160 referenceX96) private view returns (int24 lower, int24 upper) {
        uint256 below = Math.sqrt(uint256(10000 - c.rangeBps) * 1e28);
        uint256 above = Math.sqrt(uint256(10000 + c.rangeBps) * 1e28);
        bool inverse = rangeOrientation[keccak256(abi.encode(c.key))] == 1;
        uint256 lowerRoot = inverse ? Math.mulDiv(referenceX96,1e16,
            Math.sqrt(uint256(10000+c.rangeBps)*1e28,Math.Rounding.Ceil)) : Math.mulDiv(referenceX96,below,1e16);
        uint256 upperRoot = inverse ? Math.mulDiv(referenceX96,1e16,below,Math.Rounding.Ceil) : Math.mulDiv(referenceX96,above,1e16);
        if (lowerRoot <= TickMath.MIN_SQRT_PRICE || upperRoot >= TickMath.MAX_SQRT_PRICE) revert InvalidConfiguration();
        lower = _floor(TickMath.getTickAtSqrtPrice(uint160(lowerRoot)), c.key.tickSpacing);
        // Always round the upper limit outward, including an exact tick boundary.
        upper = _floor(TickMath.getTickAtSqrtPrice(uint160(upperRoot)), c.key.tickSpacing) + c.key.tickSpacing;
        if (lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper) revert InvalidConfiguration();
    }
    /// @notice Explicit opt-in; existing physical ticks are not reinterpreted.
    function setRangeOrientation(bytes32 poolId,uint8 orientation) external onlyGovernance operating {
        uint8 previous = rangeOrientation[poolId];
        if (orientation > 1 || previous == orientation) revert InvalidConfiguration();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        rangeOrientation[poolId] = orientation;
        _range(c,IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0,c.key.currency1));
        KeeperRangePolicy storage policy = keeperRangePolicy[poolId];
        if (policy.enabled) {
            policy.enabled = false;
            --activeKeeperRangePolicies;
            emit KeeperRangePolicyChanged(poolId,false,policy.configurationHash,policy.reviewHash);
        }
        rebalanceConfirmation.invalidatePolicy();
        emit RangeOrientationChanged(poolId,previous,orientation);
    }
    /// @notice Review actual price-displacement rules, not an inferred volatility model.
    /// Disabling never needs healthy Oracle/venue data. Existing audit fields persist.
    function setKeeperRangePolicy(bytes32 poolId,bool enabled,uint16 narrowTriggerBps,uint16 widenTriggerBps,
        uint32 minInterval,bytes32 reviewHash) external onlyGovernance operating {
        if (poolId == bytes32(0)) revert InvalidConfiguration();
        KeeperRangePolicy storage policy = keeperRangePolicy[poolId];
        if (!enabled) {
            if(policy.enabled) --activeKeeperRangePolicies;
            policy.enabled = false;
            emit KeeperRangePolicyChanged(poolId,false,policy.configurationHash,policy.reviewHash);
            return;
        }
        // A keeper-selected width would otherwise use the deliberate-width
        // exception. It cannot silently bypass same-side reference protection.
        if(rebalanceConfirmation.requireReferenceExit()) revert InvalidConfiguration();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        if (rangeOrientation[poolId] != 1 || (c.rangeBps != 2500 && c.rangeBps != 5000) ||
            c.triggerBps >= 2500 || c.maxSpotDeviationBps >= 2500 || narrowTriggerBps >= widenTriggerBps ||
            widenTriggerBps >= 2500 || minInterval < 600 || minInterval < c.minRebalanceInterval ||
            minInterval > 7 days || reviewHash == bytes32(0)) revert InvalidConfiguration();
        _range(c,IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0,c.key.currency1));
        bytes32 fingerprint = _rangeConfiguration(c);
        if(!policy.enabled) ++activeKeeperRangePolicies;
        keeperRangePolicy[poolId] = KeeperRangePolicy(true,narrowTriggerBps,widenTriggerBps,minInterval,
            uint64(block.timestamp),fingerprint,reviewHash);
        emit KeeperRangePolicyChanged(poolId,true,fingerprint,reviewHash);
    }
    function _rangeConfiguration(PoolConfig memory c) private view returns(bytes32 fingerprint) {
        uint16 width = c.rangeBps;
        c.rangeBps = 0;
        fingerprint = keccak256(abi.encode(c,rangeOrientation[keccak256(abi.encode(c.key))]));
        c.rangeBps = width;
    }
    function _displacement(bytes32 poolId,uint160 center,uint160 referenceX96) private view returns(uint256) {
        uint256 root = rangeOrientation[poolId] == 1 ? Math.mulDiv(center,1e18,referenceX96) :
            Math.mulDiv(referenceX96,1e18,center);
        uint256 ratio = Math.mulDiv(root,root,1e18);
        return ratio > 1e18 ? ratio-1e18 : 1e18-ratio;
    }
    function keeperRangeTarget(bytes32 poolId) public view returns(uint16 next) {
        KeeperRangePolicy memory policy = keeperRangePolicy[poolId];
        if (!policy.enabled || !access.isSealed() || access.paused() || access.preparationActive() ||
            access.canonicalState() != 0 || rangeOrientation[poolId] != 1 ||
            block.timestamp < uint256(policy.lastChange)+policy.minInterval) return 0;
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
        if (!c.operationsEnabled || _rangeConfiguration(c) != policy.configurationHash ||
            (c.rangeBps != 2500 && c.rangeBps != 5000)) return 0;
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        uint256 bucket = vault.poolBucket(poolId);
        if (bucket == 0) return 0;
        Position memory p = vault.group(bucket);
        if (p.poolId != poolId || p.status != PositionStatus.Active || p.lpTokenId == 0 || p.centerX96 == 0 ||
            block.timestamp < uint256(p.lastRebalance)+c.minRebalanceInterval || _rangeUpdatePending(p,c)) return 0;
        uint160 ref = IZZZOracle(access.module(Ids.ORACLE)).referenceX96(c.key.currency0,c.key.currency1);
        uint256 movement = _displacement(poolId,p.centerX96,ref);
        if (c.rangeBps == 2500 && movement >= uint256(policy.widenTriggerBps)*1e14) next = 5000;
        else if (c.rangeBps == 5000 && movement <= uint256(policy.narrowTriggerBps)*1e14) next = 2500;
        if (next != 0) { c.rangeBps = next; _range(c,ref); }
    }
    /// @notice Keeper supplies a pool only; the reviewed on-chain rule chooses width.
    function applyKeeperRange(bytes32 poolId) external onlyKeeper live operating principalOperating returns(uint16 next) {
        next = keeperRangeTarget(poolId);
        if (next == 0) revert InvalidState();
        uint16 previous = IZZZPools(access.module(Ids.POOLS)).get(poolId).rangeBps;
        keeperRangePolicy[poolId].lastChange = uint64(block.timestamp);
        IRangeRegistry(access.module(Ids.POOLS)).applyKeeperRange(poolId,next);
        emit KeeperRangeSelected(poolId,previous,next,keeperRangePolicy[poolId].reviewHash);
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
        _checkedSpot(p.poolId,c,ref);
        (int24 lower,int24 upper) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).ticks(p.lpTokenId);
        if (lower < TickMath.MIN_TICK || upper > TickMath.MAX_TICK || lower >= upper) revert InvalidState();
        int24 tick = _checkedPoolTick(p.poolId,c);
        // A true range exit cannot bypass the governed minimum interval. A
        // deliberate width/orientation change may still apply while in range.
        return tick < lower || tick >= upper || _rangeUpdatePending(p,c);
    }
    /// @dev Preserve v4's exact downward-crossing tick, which may be one below
    /// getTickAtSqrtPrice. Using a recomputed tick would misclassify that edge.
    function _checkedPoolTick(bytes32 poolId,PoolConfig memory c) private view returns(int24 tick) {
        uint160 price; uint24 protocol; uint24 fee;
        (price,tick,protocol,fee) = IV4FeeState(access.module(Ids.LIQUIDITY)).stateView().getSlot0(poolId);
        if (price < TickMath.MIN_SQRT_PRICE || price >= TickMath.MAX_SQRT_PRICE ||
            tick < TickMath.MIN_TICK || tick >= TickMath.MAX_TICK || fee != c.key.fee ||
            (protocol & 0xfff) > 1000 || protocol >> 12 > 1000) revert InvalidState();
        if (price < TickMath.getSqrtPriceAtTick(tick) || price > TickMath.getSqrtPriceAtTick(tick+1)) revert InvalidState();
    }
    /// @notice A governed width/orientation change can require replacement at a flat price.
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
        uint256 excess = zeroForOne ? v0 - desired0 : desired0 - v0;
        uint256 fee = _swapFee(poolId,c,zeroForOne);
        {
            // Every admitted v4 pool is static, hookless and native ETH/fixed ZZZ.
            // Size the net pair after its actual directional protocol + LP fee.
            uint256 inputWeight = Math.mulDiv(zeroForOne ? u0 : u1, 1e18, u0 + u1);
            excess = Math.mulDiv(excess, 1e18, 1e18 - Math.mulDiv(inputWeight, fee, 1_000_000));
        }
        amountIn = Math.mulDiv(excess, input.scale, input.lower);
        if (amountIn > (zeroForOne ? amount0 : amount1)) revert InvalidState();
        // Preserve Oracle.quote's two floor operations exactly: upper-valued
        // source USD first, then lower-valued output raw units.
        minimumOut = _minimum(prices,zeroForOne,amountIn,c.maxSlippageBps,fee);
        if (minimumOut == 0) amountIn = 0;
    }
}
