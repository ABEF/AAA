// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZLPBalanceMath} from "./ZZZLPBalanceMath.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZPriceMath} from "./libraries/ZZZPriceMath.sol";
import {Ids, PoolKey, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZPools, IZZZOracle, IZZZStrategy, IZZZLiquidity, IPositionManagerMinimal, IStateViewMinimal, IPoolManagerMinimal} from "./interfaces/IZZZ.sol";

interface IPortfolioRoutePolicy { function controlFingerprint(bytes32) external view returns(bytes32); }
interface ILPRegistryRevision { function configurationRevision() external view returns (uint64); }

/// @notice Bounded, typed ETH/ZZZ balancing. Quotes revert all core changes and
/// compare useful target LP value at one independent price vector, not raw L.
/// This is a bounded search of reviewed venues, not a global optimum promise.
contract ZZZLPBalancer is ZZZModule {
    uint256 public constant LP_ROUTING_VERSION = 2;
    uint256 public constant EXECUTION_QUALITY_VERSION = 1;
    uint256 public constant MAX_ADDITIONAL_LOSS_BPS = 1000;
    uint256 public constant MAX_EXECUTION_POOLS = 4;
    ZZZLPBalanceMath public immutable balanceMath;
    IPoolManagerMinimal public immutable poolManager;
    IStateViewMinimal public immutable stateView;
    bytes32[] private venues;
    uint64 public executionRevision;
    uint8 public searchIterations = 8;
    uint32 public quoteGasLimit = 200000;
    bytes32 private pendingQuoteHash;

    struct Plan { bytes32 poolId; bool zeroForOne; uint256 amountIn; uint256 amountOut; uint256 minimumOut; uint160 sqrtAfter; uint160 targetSqrtAfter; uint64 revision; bytes32 fingerprint; }
    error QuoteResult(uint256 output, uint160 sqrtAfter);
    event ExecutionPoolsConfigured(uint64 indexed revision, bytes32[] pools, bytes32 indexed reviewHash);
    event SolverConfigured(uint64 indexed revision, uint8 iterations, uint32 gasLimit, bytes32 indexed reviewHash);
    /// @dev This is a selected quote, not income. The manager verifies exact
    /// actual output/price; any failed outer operation rolls this log back.
    event BalancePlanned(bytes32 indexed targetPool, bytes32 indexed executionPool, bool zeroForOne,
        uint256 amountIn, uint256 expectedOutput, uint64 revision);

    constructor(address controller, address core, address state) ZZZModule(controller) {
        balanceMath = new ZZZLPBalanceMath();
        poolManager = IPoolManagerMinimal(core);
        stateView = IStateViewMinimal(state);
    }
    /// @notice The sealed controller fixes the sole parent. Standalone creation
    /// avoids embedding this router in Manager initcode; no mutable parent setter.
    function liquidityManager() public view returns(address) { return access.module(Ids.LIQUIDITY); }
    function executionPoolCount() external view returns (uint256) { return venues.length; }
    function executionPoolAt(uint256 index) external view returns (bytes32) { return venues[index]; }
    /// @notice Shared exact v4 math avoids embedding a second copy in Manager.
    /// Pure calculation, no custody or authorization; Manager verifies raw spends.
    function deploymentAmounts(uint160 current,int24 lower,int24 upper,uint256 amount0,uint256 amount1)
        external view returns(uint128 liquidity,uint256 nativeDebt) {
        return balanceMath.deploymentAmounts(current,lower,upper,amount0,amount1);
    }
    function principalAmounts(uint256 id) external view returns(uint256 amount0,uint256 amount1) {
        return balanceMath.principalAmounts(IZZZLiquidity(liquidityManager()).positionManager(),address(stateView),id);
    }
    /// @notice Policy belongs to the fixed Strategy; never a keeper input.
    function additionalLossBps() public view returns(uint16) {
        return IZZZStrategy(access.module(Ids.STRATEGY)).additionalLossBps();
    }
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
            address(oracle),access.module(Ids.STRATEGY),
            IZZZStrategy(access.module(Ids.STRATEGY)).executionQualityRevision(),
            IPortfolioRoutePolicy(IZZZStrategy(access.module(Ids.STRATEGY)).portfolioPolicy()).controlFingerprint(target),
            lower,upper,referencePrice,first,second));
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
    function _fee(PoolConfig memory c, bool direction, uint24 protocol, uint24 fee) private pure returns (uint256) {
        if (fee != c.key.fee || (protocol & 0xfff) > 1000 || protocol >> 12 > 1000) revert InvalidState();
        uint256 selected = direction ? protocol & 0xfff : protocol >> 12;
        return selected + fee - Math.mulDiv(selected,fee,1_000_000);
    }
    function _pool(bytes32 id) private view returns (PoolConfig memory c) {
        c = IZZZPools(access.module(Ids.POOLS)).accounting(id);
        if (!c.operationsEnabled || c.key.currency0 != address(0) || c.key.currency1 == address(0) ||
            c.key.hooks != address(0) || c.key.fee > 100000 || c.maxSlippageBps > 1000 ||
            keccak256(abi.encode(c.key)) != id) revert InvalidConfiguration();
    }
    function _prices(address token) private view returns (ZZZLPBalanceMath.Prices memory p) {
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        (p.lower0,p.upper0,) = oracle.priceBounds(address(0));
        (p.lower1,p.upper1,) = oracle.priceBounds(token);
        uint8 d1 = oracle.tokenDecimals(token);
        p.scale1 = 10 ** d1;
        p.referenceX96 = ZZZPriceMath.referenceX96(p.lower0,p.lower1,18,d1,address(0));
        p.extraLoss = additionalLossBps();
    }
    function _validSpot(uint160 price, uint160 referencePrice, uint16 deviation) private pure returns (bool) {
        if (price < TickMath.MIN_SQRT_PRICE || price >= TickMath.MAX_SQRT_PRICE) return false;
        uint256 root = Math.mulDiv(price,1e18,referencePrice);
        uint256 ratio = Math.mulDiv(root,root,1e18);
        return (ratio > 1e18 ? ratio-1e18 : 1e18-ratio) <= uint256(deviation)*1e14;
    }
    function _evaluate(ZZZLPBalanceMath.Context memory x,uint160 price,uint256 a0,uint256 a1)
        private view returns(ZZZLPBalanceMath.Evaluation memory) {
        return balanceMath.evaluate(x,price,a0,a1);
    }
    function _quoted(ZZZLPBalanceMath.Prices memory p, bool direction, uint256 amount) private pure returns (uint256) {
        uint256 value = Math.mulDiv(amount,direction ? p.upper0 : p.upper1,direction ? 1e18 : p.scale1);
        return Math.mulDiv(value,direction ? p.scale1 : 1e18,direction ? p.lower1 : p.lower0);
    }
    function _minimum(ZZZLPBalanceMath.Prices memory p, bool direction, uint256 amount, uint16 loss, uint256 fee) private pure returns (uint256) {
        uint256 gross = Math.mulDiv(_quoted(p,direction,amount),10000-loss,10000);
        uint256 netInput = Math.mulDiv(amount,1_000_000-fee,1_000_000);
        return Math.max(gross,Math.mulDiv(_quoted(p,direction,netInput),10000-p.extraLoss,10000,Math.Rounding.Ceil));
    }
    /// @dev Fee-aware seed usually gives one quote for deep, small trades.
    function _seed(ZZZLPBalanceMath.Context memory x,bool direction,uint256 fee)
        private view returns(uint256 input,uint256 residual) {
        // routePlan passes a calldata copy. Seed a needed partial trade with
        // the same rounding headroom as its later qualification, without making
        // a naturally sufficient main require another swap.
        if(x.mainFloor<9999)++x.mainFloor;
        return balanceMath.seed(x,direction,fee);
    }
    function plan(bytes32 target,int24 lower,int24 upper,uint256 amount0,uint256 amount1)
        external returns(Plan memory) { uint256[4] memory marks; return _plan(target,lower,upper,amount0,amount1,10000,marks); }
    /// @notice Fresh replacement only: minimum qualifying main allocation, not
    /// maximum-main turnover. Manager captures permission from its fixed Budget.
    function planPartial(bytes32 target,int24 lower,int24 upper,uint256 amount0,uint256 amount1,uint16 mainFloor,uint256[4] calldata marks)
        external returns(Plan memory) {
        if(mainFloor<6000 || mainFloor>=10000)revert InvalidConfiguration();
        return _plan(target,lower,upper,amount0,amount1,mainFloor,marks);
    }
    function _plan(bytes32 target,int24 lower,int24 upper,uint256 amount0,uint256 amount1,uint16 mainFloor,uint256[4] memory marks)
        private returns(Plan memory best) {
        if (msg.sender != liquidityManager() || access.module(Ids.LIQUIDITY) != msg.sender || !access.isSealed()) revert Unauthorized();
        if (amount0 > type(uint128).max || amount1 > type(uint128).max || lower >= upper) revert InvalidAmount();
        PoolConfig memory destination = _pool(target);
        ZZZLPBalanceMath.Context memory x = ZZZLPBalanceMath.Context(target,IZZZStrategy(access.module(Ids.STRATEGY)).validatePrice(target),
            TickMath.getSqrtPriceAtTick(lower),TickMath.getSqrtPriceAtTick(upper),amount0,amount1,_prices(destination.key.currency1),mainFloor,marks);
        ZZZLPBalanceMath.Evaluation memory baseline = _evaluate(x,x.spot,amount0,amount1);
        best.revision = executionRevision;
        best.targetSqrtAfter = x.spot;
        bytes32 original = policyFingerprint(target,bytes32(0));
        best.fingerprint = original;
        uint256 bestValue = baseline.deployed;
        // A balanced budget needs no swap just to chase rounding dust.
        // A naturally sufficient main already satisfies the policy. The extra
        // 1bp sizing headroom is only for a needed trade, not a hidden reason
        // to swap an otherwise sufficient portfolio or require a live venue.
        if (baseline.retained == 0 || baseline.deployed >= Math.mulDiv(baseline.retained,mainFloor==10000?9990:mainFloor,10000,Math.Rounding.Ceil)) {
            emit BalancePlanned(target,bytes32(0),false,0,0,best.revision);
            return best;
        }
        for (uint256 i; i < venues.length; ++i) {
            // An independently disabled venue must not freeze healthy candidates.
            try this.routePlan(x,venues[i],baseline.excess0) returns (Plan memory candidate,uint256 deployed) {
                if (mainFloor==10000 ? deployed>bestValue : candidate.amountIn!=0 &&
                    (best.amountIn==0 || candidate.amountIn<best.amountIn ||
                        (candidate.amountIn==best.amountIn && candidate.amountOut>best.amountOut))) {
                    best=candidate;bestValue=deployed;
                }
            } catch {}
        }
        if (mainFloor<10000 && best.amountIn==0) revert Slippage();
        if (executionRevision != best.revision || policyFingerprint(target,bytes32(0)) != original) revert InvalidState();
        emit BalancePlanned(target,best.poolId,best.zeroForOne,best.amountIn,best.amountOut,best.revision);
    }
    function routePlan(ZZZLPBalanceMath.Context calldata x, bytes32 id, bool direction) external returns (Plan memory best,uint256 bestValue) {
        if (msg.sender != address(this)) revert Unauthorized();
        PoolConfig memory c = _pool(id);
        PoolConfig memory target = _pool(x.target);
        if (c.key.currency1 != target.key.currency1) revert InvalidConfiguration();
        (uint160 beforePrice,,uint24 protocol,uint24 fee) = stateView.getSlot0(id);
        uint256 swapFee = _fee(c,direction,protocol,fee);
        if (!_validSpot(beforePrice,x.prices.referenceX96,c.maxSpotDeviationBps)) revert InvalidState();
        uint256 lo; uint256 hi = direction ? x.amount0 : x.amount1;
        if (hi > uint256(uint128(type(int128).max))) hi = uint256(uint128(type(int128).max));
        (uint256 input,uint256 initialResidual) = _seed(x,direction,swapFee);
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
                    c.maxSlippageBps < target.maxSlippageBps ? c.maxSlippageBps : target.maxSlippageBps,swapFee);
                if (minimum == 0) lo = input+1;
                // Feasibility comes before the target-ratio bracket. Increasing
                // an already excessive trade cannot repair impact/spot limits.
                else if (output < minimum || !_validSpot(afterPrice,x.prices.referenceX96,c.maxSpotDeviationBps)) hi = input;
                else {
                    uint256 a0 = direction ? x.amount0-input : x.amount0+output;
                    uint256 a1 = direction ? x.amount1+output : x.amount1-input;
                    ZZZLPBalanceMath.Evaluation memory e = _evaluate(x,id == x.target ? afterPrice : x.spot,a0,a1);
                    // Keep one basis point of search headroom for rounded mint
                    // debts. A9999floor may be unavailable if full deployment
                    // cannot be represented; governance can choose a lower one.
                    bool meets=x.mainFloor<10000 && e.deployed>=Math.mulDiv(e.retained,x.mainFloor+1,10000,Math.Rounding.Ceil);
                    if(x.mainFloor<10000) {
                        if(meets) {
                            if(best.amountIn==0 || input<best.amountIn) {
                                bestValue=e.deployed;
                                best=Plan(id,direction,input,output,minimum,afterPrice,id==x.target?afterPrice:x.spot,
                                    executionRevision,policyFingerprint(x.target,id));
                            }
                            hi=input;
                        } else if(e.excess0==direction)lo=input+1;
                        else hi=input;
                    } else {
                        if(e.deployed>bestValue) {
                            bestValue=e.deployed;
                            best=Plan(id,direction,input,output,minimum,afterPrice,id==x.target?afterPrice:x.spot,
                                executionRevision,policyFingerprint(x.target,id));
                            if(e.deployed>=Math.mulDiv(e.retained,9990,10000))break;
                        }
                        if(e.excess0==direction)lo=input+1;
                        else hi=input;
                    }
                    // Safeguarded secant from the original zero-input residual:
                    // smooth v4 curves converge faster than midpoint-only
                    // search, without another real swap or an unbounded loop.
                    if (x.mainFloor==10000 && initialResidual != 0) {
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
