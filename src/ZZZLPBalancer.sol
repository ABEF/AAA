// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {LiquidityAmounts} from "@uniswap/v4-periphery/src/libraries/LiquidityAmounts.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZPriceMath} from "./libraries/ZZZPriceMath.sol";
import {Ids, PoolKey, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZPools, IZZZOracle, IZZZStrategy, IStateViewMinimal, IPoolManagerMinimal} from "./interfaces/IZZZ.sol";

interface ILPRegistryRevision { function configurationRevision() external view returns (uint64); }

/// @notice Bounded, typed ETH/ZZZ balancing. Quotes revert all core changes and
/// compare useful target LP value at one independent price vector, not raw L.
/// This is a bounded search of reviewed venues, not a global optimum promise.
contract ZZZLPBalancer is ZZZModule {
    uint256 public constant LP_ROUTING_VERSION = 1;
    uint256 public constant MAX_EXECUTION_POOLS = 4;
    address public immutable liquidityManager;
    IPoolManagerMinimal public immutable poolManager;
    IStateViewMinimal public immutable stateView;
    bytes32[] private venues;
    uint64 public executionRevision;
    uint8 public searchIterations = 8;
    uint32 public quoteGasLimit = 200000;
    bytes32 private pendingQuoteHash;

    struct Prices { uint256 lower0; uint256 upper0; uint256 lower1; uint256 upper1; uint256 scale1; uint160 referenceX96; }
    struct Context { bytes32 target; uint160 spot; uint160 lower; uint160 upper; uint256 amount0; uint256 amount1; Prices prices; }
    struct Plan { bytes32 poolId; bool zeroForOne; uint256 amountIn; uint256 amountOut; uint256 minimumOut; uint160 sqrtAfter; uint160 targetSqrtAfter; uint64 revision; bytes32 fingerprint; }
    struct Evaluation { uint256 deployed; uint256 retained; uint256 imbalance; bool excess0; }
    error QuoteResult(uint256 output, uint160 sqrtAfter);
    event ExecutionPoolsConfigured(uint64 indexed revision, bytes32[] pools, bytes32 indexed reviewHash);
    event SolverConfigured(uint64 indexed revision, uint8 iterations, uint32 gasLimit, bytes32 indexed reviewHash);
    /// @dev This is a selected quote, not income. The manager verifies exact
    /// actual output/price; any failed outer operation rolls this log back.
    event BalancePlanned(bytes32 indexed targetPool, bytes32 indexed executionPool, bool zeroForOne,
        uint256 amountIn, uint256 expectedOutput, uint64 revision);

    constructor(address controller, address core, address state) ZZZModule(controller) {
        // Created by the manager while its runtime does not yet exist.
        liquidityManager = msg.sender;
        poolManager = IPoolManagerMinimal(core);
        stateView = IStateViewMinimal(state);
    }
    function executionPoolCount() external view returns (uint256) { return venues.length; }
    function executionPoolAt(uint256 index) external view returns (bytes32) { return venues[index]; }
    /// @notice Captures target/venue controls, monotonic registry changes and
    /// both independently validated source rounds. Recheck after token callbacks.
    function policyFingerprint(bytes32 target, bytes32 venue) public view returns (bytes32) {
        address registry = access.module(Ids.POOLS);
        PoolConfig memory t = IZZZPools(registry).accounting(target);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        (,,bytes32 first) = oracle.priceBounds(address(0));
        (,,bytes32 second) = oracle.priceBounds(t.key.currency1);
        bytes32 route = venue == bytes32(0) ? bytes32(0) : keccak256(abi.encode(IZZZPools(registry).accounting(venue)));
        (int24 lower,int24 upper,uint160 referencePrice) = IZZZStrategy(access.module(Ids.STRATEGY)).target(target);
        return keccak256(abi.encode(registry,ILPRegistryRevision(registry).configurationRevision(),t,route,
            address(oracle),access.module(Ids.STRATEGY),lower,upper,referencePrice,first,second));
    }

    /// @notice Empty removes all swap venues without consulting prices or core.
    /// Pool admission remains separate; this grants no token/recipient authority.
    function configureExecutionPools(bytes32[] calldata pools, bytes32 reviewHash)
        external onlyGovernance operating principalOperating {
        if (pools.length > MAX_EXECUTION_POOLS || reviewHash == bytes32(0)) revert InvalidConfiguration();
        for (uint256 i; i < pools.length; ++i) {
            PoolConfig memory c = _pool(pools[i]);
            IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(pools[i]);
            (,,,uint24 fee) = stateView.getSlot0(pools[i]);
            if (fee != c.key.fee) revert InvalidConfiguration();
            for (uint256 j; j < i; ++j) if (pools[j] == pools[i]) revert InvalidConfiguration();
        }
        venues = pools;
        ++executionRevision;
        emit ExecutionPoolsConfigured(executionRevision, pools, reviewHash);
    }
    /// @notice Work limits are explicit and governed; no unbounded quote loop.
    function configureSolver(uint8 iterations, uint32 gasLimit, bytes32 reviewHash)
        external onlyGovernance operating principalOperating {
        if (iterations < 4 || iterations > 12 || gasLimit < 100000 || gasLimit > 300000 || reviewHash == bytes32(0))
            revert InvalidConfiguration();
        searchIterations = iterations; quoteGasLimit = gasLimit; ++executionRevision;
        emit SolverConfigured(executionRevision, iterations, gasLimit, reviewHash);
    }
    function _pool(bytes32 id) private view returns (PoolConfig memory c) {
        c = IZZZPools(access.module(Ids.POOLS)).accounting(id);
        if (!c.operationsEnabled || c.key.currency0 != address(0) || c.key.currency1 == address(0) ||
            c.key.hooks != address(0) || c.key.fee > 100000 || c.maxSlippageBps > 1000 ||
            keccak256(abi.encode(c.key)) != id) revert InvalidConfiguration();
    }
    function _prices(address token) private view returns (Prices memory p) {
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        (p.lower0,p.upper0,) = oracle.priceBounds(address(0));
        (p.lower1,p.upper1,) = oracle.priceBounds(token);
        uint8 d1 = oracle.tokenDecimals(token);
        p.scale1 = 10 ** d1;
        p.referenceX96 = ZZZPriceMath.referenceX96(p.lower0,p.lower1,18,d1,address(0));
    }
    function _validSpot(uint160 price, uint160 referencePrice, uint16 deviation) private pure returns (bool) {
        if (price < TickMath.MIN_SQRT_PRICE || price >= TickMath.MAX_SQRT_PRICE) return false;
        uint256 root = Math.mulDiv(price,1e18,referencePrice);
        uint256 ratio = Math.mulDiv(root,root,1e18);
        return (ratio > 1e18 ? ratio-1e18 : 1e18-ratio) <= uint256(deviation)*1e14;
    }
    function _values(Prices memory p, uint256 amount0, uint256 amount1) private pure returns (uint256 v0, uint256 v1) {
        return (Math.mulDiv(amount0,p.lower0,1e18),Math.mulDiv(amount1,p.lower1,p.scale1));
    }
    function _evaluate(Context memory x, uint160 price, uint256 a0, uint256 a1) private pure returns (Evaluation memory e) {
        (uint256 v0,uint256 v1) = _values(x.prices,a0,a1);
        e.retained = v0+v1;
        uint256 u0; uint256 u1;
        if (price <= x.lower) u0 = SqrtPriceMath.getAmount0Delta(x.lower,x.upper,1e18,false);
        else if (price >= x.upper) u1 = SqrtPriceMath.getAmount1Delta(x.lower,x.upper,1e18,false);
        else {
            u0 = SqrtPriceMath.getAmount0Delta(price,x.upper,1e18,false);
            u1 = SqrtPriceMath.getAmount1Delta(x.lower,price,1e18,false);
        }
        (u0,u1) = _values(x.prices,u0,u1);
        if (u0+u1 == 0) revert InvalidAmount();
        uint256 desired0 = Math.mulDiv(e.retained,u0,u0+u1);
        e.excess0 = v0 > desired0;
        e.imbalance = e.excess0 ? v0-desired0 : desired0-v0;
        uint128 liquidity = LiquidityAmounts.getLiquidityForAmounts(price,x.lower,x.upper,a0,a1);
        uint256 used0; uint256 used1;
        if (price <= x.lower) used0 = SqrtPriceMath.getAmount0Delta(x.lower,x.upper,liquidity,false);
        else if (price >= x.upper) used1 = SqrtPriceMath.getAmount1Delta(x.lower,x.upper,liquidity,false);
        else {
            used0 = SqrtPriceMath.getAmount0Delta(price,x.upper,liquidity,false);
            used1 = SqrtPriceMath.getAmount1Delta(x.lower,price,liquidity,false);
        }
        (used0,used1) = _values(x.prices,used0,used1);
        e.deployed = used0+used1;
    }
    function _minimum(Prices memory p, bool direction, uint256 amount, uint16 loss) private pure returns (uint256) {
        uint256 value = Math.mulDiv(amount,direction ? p.upper0 : p.upper1,direction ? 1e18 : p.scale1);
        uint256 output = Math.mulDiv(value,direction ? p.scale1 : 1e18,direction ? p.lower1 : p.lower0);
        return Math.mulDiv(output,10000-loss,10000);
    }
    /// @dev Fee-aware seed usually gives one quote for deep, small trades.
    function _seed(Context memory x, bool direction, uint256 fee) private pure returns (uint256 input,uint256 residual) {
        uint256 unit0; uint256 unit1;
        if (x.spot <= x.lower) unit0 = SqrtPriceMath.getAmount0Delta(x.lower,x.upper,1e18,false);
        else if (x.spot >= x.upper) unit1 = SqrtPriceMath.getAmount1Delta(x.lower,x.upper,1e18,false);
        else {
            unit0 = SqrtPriceMath.getAmount0Delta(x.spot,x.upper,1e18,false);
            unit1 = SqrtPriceMath.getAmount1Delta(x.lower,x.spot,1e18,false);
        }
        (unit0,unit1) = _values(x.prices,unit0,unit1);
        (uint256 v0,uint256 v1) = _values(x.prices,x.amount0,x.amount1);
        uint256 desired = Math.mulDiv(v0+v1,unit0,unit0+unit1);
        uint256 excess = direction ? v0-desired : desired-v0;
        residual = excess;
        uint256 weight = Math.mulDiv(direction ? unit0 : unit1,1e18,unit0+unit1);
        excess = Math.mulDiv(excess,1e18,1e18-Math.mulDiv(weight,fee,1_000_000));
        input = Math.mulDiv(excess,direction ? 1e18 : x.prices.scale1,direction ? x.prices.lower0 : x.prices.lower1);
    }
    function plan(bytes32 target, int24 lower, int24 upper, uint256 amount0, uint256 amount1)
        external returns (Plan memory best) {
        if (msg.sender != liquidityManager || access.module(Ids.LIQUIDITY) != msg.sender || !access.isSealed()) revert Unauthorized();
        if (amount0 > type(uint128).max || amount1 > type(uint128).max || lower >= upper) revert InvalidAmount();
        PoolConfig memory destination = _pool(target);
        Context memory x = Context(target,IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(target),
            TickMath.getSqrtPriceAtTick(lower),TickMath.getSqrtPriceAtTick(upper),amount0,amount1,_prices(destination.key.currency1));
        Evaluation memory baseline = _evaluate(x,x.spot,amount0,amount1);
        best.revision = executionRevision;
        best.targetSqrtAfter = x.spot;
        bytes32 original = policyFingerprint(target,bytes32(0));
        best.fingerprint = original;
        uint256 bestValue = baseline.deployed;
        // A balanced budget needs no swap just to chase rounding dust.
        if (baseline.retained == 0 || baseline.deployed >= Math.mulDiv(baseline.retained,9990,10000)) {
            emit BalancePlanned(target,bytes32(0),false,0,0,best.revision);
            return best;
        }
        for (uint256 i; i < venues.length; ++i) {
            // An independently disabled venue must not freeze healthy candidates.
            try this.routePlan(x,venues[i],baseline.excess0) returns (Plan memory candidate,uint256 deployed) {
                if (deployed > bestValue) { best = candidate; bestValue = deployed; }
            } catch {}
        }
        if (executionRevision != best.revision || policyFingerprint(target,bytes32(0)) != original) revert InvalidState();
        emit BalancePlanned(target,best.poolId,best.zeroForOne,best.amountIn,best.amountOut,best.revision);
    }
    function routePlan(Context calldata x, bytes32 id, bool direction) external returns (Plan memory best,uint256 bestValue) {
        if (msg.sender != address(this)) revert Unauthorized();
        PoolConfig memory c = _pool(id);
        PoolConfig memory target = _pool(x.target);
        if (c.key.currency1 != target.key.currency1) revert InvalidConfiguration();
        (uint160 beforePrice,,uint24 protocol,uint24 fee) = stateView.getSlot0(id);
        uint256 protocolFee = direction ? protocol & 0xfff : protocol >> 12;
        if (fee != c.key.fee || protocolFee > 1000 || !_validSpot(beforePrice,x.prices.referenceX96,c.maxSpotDeviationBps)) revert InvalidState();
        uint256 lo; uint256 hi = direction ? x.amount0 : x.amount1;
        if (hi > uint256(uint128(type(int128).max))) hi = uint256(uint128(type(int128).max));
        (uint256 input,uint256 initialResidual) = _seed(x,direction,protocolFee+fee-Math.mulDiv(protocolFee,fee,1_000_000));
        if (input == 0) return (best,0);
        if (input > hi) input = hi;
        best.revision = executionRevision;
        for (uint256 pass; pass < searchIterations && lo < hi; ++pass) {
            uint256 interpolated;
            bool quoted; uint256 output; uint160 afterPrice;
            try this.quoteCandidate{gas:quoteGasLimit}(c.key,direction,input) returns (uint256 out,uint160 price) {
                quoted = true; output = out; afterPrice = price;
            } catch {}
            if (!quoted) hi = input;
            else {
                uint256 minimum = _minimum(x.prices,direction,input,
                    c.maxSlippageBps < target.maxSlippageBps ? c.maxSlippageBps : target.maxSlippageBps);
                if (minimum == 0) lo = input+1;
                // Feasibility comes before the target-ratio bracket. Increasing
                // an already excessive trade cannot repair impact/spot limits.
                else if (output < minimum || !_validSpot(afterPrice,x.prices.referenceX96,c.maxSpotDeviationBps)) hi = input;
                else {
                    uint256 a0 = direction ? x.amount0-input : x.amount0+output;
                    uint256 a1 = direction ? x.amount1+output : x.amount1-input;
                    Evaluation memory e = _evaluate(x,id == x.target ? afterPrice : x.spot,a0,a1);
                    if (e.deployed > bestValue) {
                        bestValue = e.deployed;
                        best = Plan(id,direction,input,output,minimum,afterPrice,id == x.target ? afterPrice : x.spot,
                            executionRevision,policyFingerprint(x.target,id));
                        if (e.deployed >= Math.mulDiv(e.retained,9990,10000)) break;
                    }
                    if (e.excess0 == direction) lo = input+1;
                    else hi = input;
                    // Safeguarded secant from the original zero-input residual:
                    // smooth v4 curves converge faster than midpoint-only
                    // search, without another real swap or an unbounded loop.
                    if (initialResidual != 0) {
                        if (e.excess0 == direction && e.imbalance < initialResidual) {
                            uint256 denominator = initialResidual-e.imbalance;
                            // Prove the quotient is bounded before mulDiv;
                            // a nearly flat residual must not overflow or jump
                            // outside the already established feasible bracket.
                            if (input < Math.mulDiv(hi,denominator,initialResidual))
                                interpolated = Math.mulDiv(input,initialResidual,denominator);
                        } else if (e.excess0 != direction && e.imbalance <= type(uint256).max-initialResidual) {
                            interpolated = Math.mulDiv(input,initialResidual,initialResidual+e.imbalance);
                        }
                    }
                }
            }
            if (lo >= hi) break;
            input = interpolated != 0 && interpolated >= lo && interpolated < hi ? interpolated : lo+(hi-lo)/2;
        }
    }
    /// @dev Only our bounded search may quote. No funds settle; the custom
    /// revert rolls back every tick, price, fee and transient core delta.
    function quoteCandidate(PoolKey calldata key, bool direction, uint256 amount) external returns (uint256 output,uint160 afterPrice) {
        if (msg.sender != address(this) || amount == 0 || amount > uint256(uint128(type(int128).max))) revert Unauthorized();
        bytes memory payload = abi.encode(key,direction,amount);
        pendingQuoteHash = keccak256(payload);
        try poolManager.unlock(payload) returns (bytes memory) { revert InvalidState(); }
        catch (bytes memory reason) {
            pendingQuoteHash = bytes32(0);
            bytes4 selector;
            if (reason.length == 68) assembly ("memory-safe") { selector := mload(add(reason,32)) }
            if (selector != QuoteResult.selector) revert InvalidState();
            assembly ("memory-safe") { output := mload(add(reason,36)) afterPrice := mload(add(reason,68)) }
            if (output == 0 || afterPrice == 0) revert InvalidState();
        }
    }
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        if (msg.sender != address(poolManager) || pendingQuoteHash == bytes32(0) || keccak256(data) != pendingQuoteHash) revert Unauthorized();
        (PoolKey memory key,bool direction,uint256 amount) = abi.decode(data,(PoolKey,bool,uint256));
        int256 delta = poolManager.swap(key,IPoolManagerMinimal.SwapParams(direction,-int256(amount),
            direction ? TickMath.MIN_SQRT_PRICE+1 : TickMath.MAX_SQRT_PRICE-1),"");
        int128 d0 = int128(delta >> 128); int128 d1 = int128(uint128(uint256(delta)));
        int128 spent = direction ? d0 : d1; int128 received = direction ? d1 : d0;
        if (spent >= 0 || received <= 0 || uint256(-int256(spent)) != amount) revert Slippage();
        (uint160 afterPrice,,,) = stateView.getSlot0(keccak256(abi.encode(key)));
        revert QuoteResult(uint256(int256(received)),afterPrice);
    }
}
