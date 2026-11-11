// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {LiquidityAmounts} from "@uniswap/v4-periphery/src/libraries/LiquidityAmounts.sol";
import {PoolKey,PoolConfig,Position,PositionStatus,Ids} from "./libraries/ZZZTypes.sol";
import {IPositionManagerMinimal,IStateViewMinimal,IZZZAccess,IZZZPools,IZZZOracle,IZZZLiquidity,IZZZVault,IZZZStrategy} from "./interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {IZZZExecutionOracle,MarketState} from "./interfaces/IZZZExecutionOracle.sol";
import {ZZZPriceMath} from "./libraries/ZZZPriceMath.sol";

interface IExecutionMathParent {function access()external view returns(IZZZAccess);}
interface IExecutionMathStrategy {
    function portfolioPolicy()external view returns(address);
    function rangeOrientation(bytes32)external view returns(uint8);
    function additionalLossBps()external view returns(uint16);
    function executionQualityRevision()external view returns(uint64);
}
interface IExecutionMathPortfolio {function range(PoolConfig calldata,uint160,uint8)external view returns(int24,int24);}
interface IExecutionMathState {function stateView()external view returns(IStateViewMinimal);}
interface IExecutionMathRegistry {function configurationRevision()external view returns(uint64);}
interface IExecutionMathControls {function controlFingerprint(bytes32)external view returns(bytes32);}
interface IExecutionMathMainFloor {function minimumMainBps(bytes32)external view returns(uint16);}
interface IExecutionMathNativePools {function isNativePool(bytes32)external view returns(bool);}
interface IExecutionMathAssets {function activationAssets()external view returns(address);}
interface IExecutionMathZZZ {function zzz()external view returns(address);}
interface IExecutionMathCompoundBudget {
    function lastCompound(uint256)external view returns(uint64);
    function compoundInterval(bytes32)external view returns(uint32);
}

/// @notice Fixed noncustodial arithmetic child. No approvals, storage writes,
/// callback, execution or recipient authority. Separates ordinary code-size gates.
contract ZZZLPBalanceMath {
    uint256 public constant LP_BALANCE_MATH_VERSION = 1;
    uint256 public constant EXECUTION_PRICE_VERSION = 1;
    address public immutable balancer;
    struct Prices { uint256 lower0; uint256 upper0; uint256 lower1; uint256 upper1; uint256 scale1; uint160 referenceX96; uint16 extraLoss; }
    struct Context { bytes32 target; uint160 spot; uint160 lower; uint160 upper; uint256 amount0; uint256 amount1; Prices prices; uint16 mainFloor; uint256[4] marks; }
    struct Evaluation { uint256 deployed; uint256 retained; uint256 imbalance; bool excess0; }
    error InvalidAmount();
    error InvalidState();
    error InvalidConfiguration();
    error Slippage();
    constructor() { balancer = msg.sender; }

    function _access()private view returns(IZZZAccess){return IExecutionMathParent(balancer).access();}
    /// @notice Fixed deployment token binding, never a caller-selected asset.
    function fixedZZZ()external view returns(address zzz){
        address registry=_access().module(Ids.POOLS);
        if(registry.code.length==0)revert InvalidConfiguration();
        address assets=IExecutionMathAssets(registry).activationAssets();
        if(assets.code.length==0)revert InvalidConfiguration();
        zzz=IExecutionMathZZZ(assets).zzz();
        if(zzz==address(0) || zzz.code.length==0)revert InvalidConfiguration();
    }
    /// @notice Identical native admission checks for the fixed Manager. This
    /// read cannot admit a pool, move funds or waive its parent's force mask.
    function nativeConfig(bytes32 pool,bool requireOperations)external view returns(PoolConfig memory c){
        address pools=_access().module(Ids.POOLS);c=IZZZPools(pools).get(pool);
        if((requireOperations && !c.operationsEnabled) || keccak256(abi.encode(c.key))!=pool ||
            c.key.currency0!=address(0) || c.key.currency1==address(0) || c.key.fee>100000 ||
            c.key.hooks!=address(0) || !IExecutionMathNativePools(pools).isNativePool(pool))revert InvalidState();
    }
    /// @notice Read-only execution geometry against the captured initial vector.
    /// The fixed parent supplies Access; no caller-selected controller or price.
    function executionTarget(bytes32 pool)public view returns(int24 lower,int24 upper,uint160 referenceX96){
        IZZZAccess a=_access();PoolConfig memory c=IZZZPools(a.module(Ids.POOLS)).accounting(pool);
        if(!c.operationsEnabled)revert InvalidState();
        referenceX96=IZZZExecutionOracle(a.module(Ids.ORACLE)).executionReferenceX96(c.key.currency0,c.key.currency1);
        IExecutionMathStrategy s=IExecutionMathStrategy(a.module(Ids.STRATEGY));
        (lower,upper)=_executionRange(c,referenceX96,s,pool);
    }
    function _executionRange(PoolConfig memory c,uint160 ref,IExecutionMathStrategy strategy,bytes32 pool)
        private view returns(int24,int24){
        return IExecutionMathPortfolio(strategy.portfolioPolicy()).range(c,ref,strategy.rangeOrientation(pool));
    }
    /// @notice Preserve the router's exact policy commitment while its market
    /// observations advance only through the Oracle's verified own-swap proof.
    function policyFingerprint(bytes32 target,bytes32 venue)external view returns(bytes32){
        IZZZAccess a=_access();address registry=a.module(Ids.POOLS);
        PoolConfig memory t=IZZZPools(registry).accounting(target);
        if(!t.operationsEnabled || t.key.currency0!=address(0) || t.key.currency1==address(0))revert InvalidState();
        IZZZExecutionOracle o=IZZZExecutionOracle(a.module(Ids.ORACLE));
        (uint256 lower0,,bytes32 first)=o.executionBounds(address(0));
        (uint256 lower1,,bytes32 second)=o.executionBounds(t.key.currency1);
        bytes32 route=venue==bytes32(0)?bytes32(0):keccak256(abi.encode(IZZZPools(registry).accounting(venue)));
        IExecutionMathStrategy s=IExecutionMathStrategy(a.module(Ids.STRATEGY));
        // The same STATICCALL chain already has both validated bounds/config.
        // Derive identical geometry/hash without rereading the whole graph.
        uint160 ref=ZZZPriceMath.referenceX96(lower0,lower1,18,IZZZOracle(address(o)).tokenDecimals(t.key.currency1),address(0));
        (int24 lower,int24 upper)=_executionRange(t,ref,s,target);
        return keccak256(abi.encode(registry,IExecutionMathRegistry(registry).configurationRevision(),t,route,
            address(o),address(s),s.executionQualityRevision(),
            IExecutionMathControls(s.portfolioPolicy()).controlFingerprint(target),lower,upper,ref,first,second));
    }
    function executionValidatePrice(bytes32 pool)external view returns(uint160 spot){
        IZZZAccess a=_access();PoolConfig memory c=IZZZPools(a.module(Ids.POOLS)).accounting(pool);
        if(!c.operationsEnabled)revert InvalidState();
        uint160 ref=IZZZExecutionOracle(a.module(Ids.ORACLE)).executionReferenceX96(c.key.currency0,c.key.currency1);
        spot=IZZZLiquidity(a.module(Ids.LIQUIDITY)).spot(pool);
        if(spot==0)revert InvalidState();
        if(!validSpot(spot,ref,c.maxSpotDeviationBps))revert Slippage();
    }
    function executionPrices(address token)public view returns(Prices memory p){
        IZZZAccess a=_access();IZZZOracle o=IZZZOracle(a.module(Ids.ORACLE));
        (p.lower0,p.upper0,)=IZZZExecutionOracle(address(o)).executionBounds(address(0));
        (p.lower1,p.upper1,)=IZZZExecutionOracle(address(o)).executionBounds(token);
        uint8 decimals=o.tokenDecimals(token);p.scale1=10**decimals;
        p.referenceX96=ZZZPriceMath.referenceX96(p.lower0,p.lower1,18,decimals,address(0));
        p.extraLoss=IExecutionMathStrategy(a.module(Ids.STRATEGY)).additionalLossBps();
    }
    function executionMinimumOutput(bytes32 pool,bool direction,uint256 amount)external view returns(uint256){
        if(amount==0 || amount>type(uint128).max)revert InvalidAmount();
        IZZZAccess a=_access();PoolConfig memory c=IZZZPools(a.module(Ids.POOLS)).accounting(pool);
        if(!c.operationsEnabled)revert InvalidState();
        (,,uint24 protocol,uint24 fee)=IExecutionMathState(a.module(Ids.LIQUIDITY)).stateView().getSlot0(pool);
        if(c.key.hooks!=address(0) || fee!=c.key.fee || fee>100000 || (protocol & 0xfff)>1000 || protocol>>12>1000)revert InvalidState();
        uint256 selected=direction?protocol & 0xfff:protocol>>12;
        return minimumOutput(executionPrices(c.key.currency1),direction,amount,c.maxSlippageBps,selected+fee-Math.mulDiv(selected,fee,1_000_000));
    }
    function validSpot(uint160 price,uint160 referencePrice,uint16 deviation)public pure returns(bool){
        if(price<TickMath.MIN_SQRT_PRICE || price>=TickMath.MAX_SQRT_PRICE)return false;
        uint256 root=Math.mulDiv(price,1e18,referencePrice);
        uint256 ratio=Math.mulDiv(root,root,1e18);
        return (ratio>1e18?ratio-1e18:1e18-ratio)<=uint256(deviation)*1e14;
    }
    function _quoted(Prices memory p,bool direction,uint256 amount)private pure returns(uint256){
        uint256 usd=Math.mulDiv(amount,direction?p.upper0:p.upper1,direction?1e18:p.scale1);
        return Math.mulDiv(usd,direction?p.scale1:1e18,direction?p.lower1:p.lower0);
    }
    function minimumOutput(Prices memory p,bool direction,uint256 amount,uint16 loss,uint256 fee)public pure returns(uint256){
        uint256 gross=Math.mulDiv(_quoted(p,direction,amount),10000-loss,10000);
        uint256 net=Math.mulDiv(amount,1_000_000-fee,1_000_000);
        return Math.max(gross,Math.mulDiv(_quoted(p,direction,net),10000-p.extraLoss,10000,Math.Rounding.Ceil));
    }
    /// @notice Actual physical portfolio and attributed idle at a caller's
    /// captured vector. Read-only math grants no execution or withdrawal right.
    function maintenanceValues(uint256 bucket,uint256 price0,uint256 price1,uint256 scale0,uint256 scale1)
        public view returns(uint256 deployed,uint256 idle){
        IZZZAccess a=_access();Position memory p=IZZZVault(a.module(Ids.VAULT)).group(bucket);
        if(p.lpTokenId!=0){
            (uint256 a0,uint256 a1)=IZZZLiquidity(a.module(Ids.LIQUIDITY)).portfolioAmounts(p.lpTokenId);
            deployed=Math.mulDiv(a0,price0,scale0)+Math.mulDiv(a1,price1,scale1);
        }
        idle=Math.mulDiv(p.idle0,price0,scale0)+Math.mulDiv(p.idle1,price1,scale1);
    }
    function checkMaintenance(uint256 bucket,uint256 beforeValue,uint256 price0,uint256 price1,
        uint256 scale0,uint256 scale1,uint16 lossBps,uint16 maxIdleBps,bytes32 expectedPolicy)
        external view returns(uint256 deployed,uint256 idle,bytes32 poolId){
        IZZZAccess a=_access();
        if(beforeValue==0 || lossBps>1000 || maxIdleBps>4000 ||
            IZZZProtocolPolicy(a.protocolPolicy()).maintenanceFingerprint()!=expectedPolicy)revert InvalidState();
        poolId=IZZZVault(a.module(Ids.VAULT)).group(bucket).poolId;
        (deployed,idle)=maintenanceValues(bucket,price0,price1,scale0,scale1);
        uint256 retained=deployed+idle;
        if(retained<beforeValue-Math.mulDiv(beforeValue,lossBps,10000) || deployed==0 ||
            idle>Math.mulDiv(retained,maxIdleBps,10000))revert Slippage();
    }
    function assertPortfolioUtilization(uint256 bucket,uint256 price0,uint256 price1,uint256 scale0,uint256 scale1)
        external view {
        IZZZAccess a=_access();Position memory p=IZZZVault(a.module(Ids.VAULT)).group(bucket);
        IZZZLiquidity manager=IZZZLiquidity(a.module(Ids.LIQUIDITY));
        (uint256 a0,uint256 a1)=manager.amounts(p.lpTokenId);
        uint256 main=Math.mulDiv(a0,price0,scale0)+Math.mulDiv(a1,price1,scale1);
        uint256 secondary=manager.secondaryId(p.lpTokenId);uint256 residual;
        if(secondary!=0){
            (a0,a1)=manager.amounts(secondary);
            residual=Math.mulDiv(a0,price0,scale0)+Math.mulDiv(a1,price1,scale1);
        }
        uint256 retained=main+residual+Math.mulDiv(p.idle0,price0,scale0)+Math.mulDiv(p.idle1,price1,scale1);
        uint16 floor=IExecutionMathMainFloor(IExecutionMathStrategy(a.module(Ids.STRATEGY)).portfolioPolicy()).minimumMainBps(p.poolId);
        if(main<Math.mulDiv(retained,floor,10000,Math.Rounding.Ceil) || residual>Math.mulDiv(retained,10000-floor,10000))revert Slippage();
    }
    function validateResidualClose(uint256 bucket,bool busy)external view {
        IZZZAccess a=_access();Position memory p=IZZZVault(a.module(Ids.VAULT)).group(bucket);
        if(!a.isSealed() || !a.paused() || a.lpExitStarted() || busy || p.status!=PositionStatus.Active ||
            p.lpTokenId==0 || IZZZLiquidity(a.module(Ids.LIQUIDITY)).secondaryId(p.lpTokenId)==0)revert InvalidState();
    }
    function validateRebalance(uint256 bucket,uint128 minimumLiquidity,bool emergency,uint8 checks)external view {
        IZZZStrategy strategy=IZZZStrategy(_access().module(Ids.STRATEGY));
        if(emergency){
            if((checks & 1)!=0 && !strategy.needsRebalance(bucket))revert InvalidState();
        }else if(minimumLiquidity==0 || !strategy.rebalanceReady(bucket))revert InvalidState();
    }
    function compoundReady(uint256 bucket,address budget)external view returns(bool){
        IZZZAccess a=_access();Position memory p=IZZZVault(a.module(Ids.VAULT)).group(bucket);
        if(p.status!=PositionStatus.Active || p.lpTokenId==0)return false;
        PoolConfig memory c=IZZZPools(a.module(Ids.POOLS)).accounting(p.poolId);
        if(!c.operationsEnabled)return false;
        uint256 previous=IExecutionMathCompoundBudget(budget).lastCompound(bucket);
        if(p.lastRebalance>previous)previous=p.lastRebalance;
        if(block.timestamp<previous+IExecutionMathCompoundBudget(budget).compoundInterval(p.poolId))return false;
        IZZZStrategy strategy=IZZZStrategy(a.module(Ids.STRATEGY));
        return !strategy.needsRebalance(bucket) && strategy.keeperRangeTarget(p.poolId)==0;
    }

    function deploymentAmounts(uint160 current,int24 lower,int24 upper,uint256 amount0,uint256 amount1)
        external pure returns(uint128 liquidity,uint256 nativeDebt) {
        uint160 a=TickMath.getSqrtPriceAtTick(lower);uint160 b=TickMath.getSqrtPriceAtTick(upper);
        liquidity=LiquidityAmounts.getLiquidityForAmounts(current,a,b,amount0,amount1);
        if(current<b) nativeDebt=SqrtPriceMath.getAmount0Delta(current<=a?a:current,b,liquidity,true);
    }
    /// @notice Exact rounded-up principal debts for a fixed liquidity amount.
    function deploymentDebts(uint160 current,int24 lower,int24 upper,uint128 liquidity)
        external pure returns(uint256 amount0,uint256 amount1) {
        uint160 a=TickMath.getSqrtPriceAtTick(lower);uint160 b=TickMath.getSqrtPriceAtTick(upper);
        if(current<b)amount0=SqrtPriceMath.getAmount0Delta(current<=a?a:current,b,liquidity,true);
        if(current>a)amount1=SqrtPriceMath.getAmount1Delta(a,current>=b?b:current,liquidity,true);
    }
    function principalAmounts(address positionManager,address state,uint256 id)
        external view returns(uint256 amount0,uint256 amount1) {
        IPositionManagerMinimal posm=IPositionManagerMinimal(positionManager);
        (PoolKey memory key,uint256 info)=posm.getPoolAndPositionInfo(id);
        uint160 a=TickMath.getSqrtPriceAtTick(int24(uint24(info>>8)));
        uint160 b=TickMath.getSqrtPriceAtTick(int24(uint24(info>>32)));
        (uint160 current,,,)=IStateViewMinimal(state).getSlot0(keccak256(abi.encode(key)));
        uint128 liquidity=posm.getPositionLiquidity(id);
        if(current<=a) amount0=SqrtPriceMath.getAmount0Delta(a,b,liquidity,false);
        else if(current>=b) amount1=SqrtPriceMath.getAmount1Delta(a,b,liquidity,false);
        else {amount0=SqrtPriceMath.getAmount0Delta(current,b,liquidity,false);amount1=SqrtPriceMath.getAmount1Delta(a,current,liquidity,false);}
    }
    function _values(Prices memory p,uint256 a0,uint256 a1) private pure returns(uint256,uint256) {
        return(Math.mulDiv(a0,p.lower0,1e18),Math.mulDiv(a1,p.lower1,p.scale1));
    }
    function _allocationValues(Context memory x,uint256 a0,uint256 a1) private pure returns(uint256,uint256) {
        if(x.mainFloor==10000)return _values(x.prices,a0,a1);
        if(x.marks[0]==0 || x.marks[1]==0 || x.marks[2]==0 || x.marks[3]==0)revert InvalidAmount();
        return(Math.mulDiv(a0,x.marks[0],x.marks[2]),Math.mulDiv(a1,x.marks[1],x.marks[3]));
    }
    function _units(Context memory x,uint160 price) private pure returns(uint256 u0,uint256 u1) {
        if(price<=x.lower)u0=SqrtPriceMath.getAmount0Delta(x.lower,x.upper,1e18,false);
        else if(price>=x.upper)u1=SqrtPriceMath.getAmount1Delta(x.lower,x.upper,1e18,false);
        else {u0=SqrtPriceMath.getAmount0Delta(price,x.upper,1e18,false);u1=SqrtPriceMath.getAmount1Delta(x.lower,price,1e18,false);}
        return _allocationValues(x,u0,u1);
    }
    function evaluate(Context memory x,uint160 price,uint256 a0,uint256 a1) external pure returns(Evaluation memory e) {
        (uint256 v0,uint256 v1)=_allocationValues(x,a0,a1);e.retained=v0+v1;
        (uint256 u0,uint256 u1)=_units(x,price);if(u0+u1==0)revert InvalidAmount();
        uint256 desired0=Math.mulDiv(e.retained,u0,u0+u1);e.excess0=v0>desired0;
        e.imbalance=e.excess0?v0-desired0:desired0-v0;
        uint128 liq=LiquidityAmounts.getLiquidityForAmounts(price,x.lower,x.upper,a0,a1);
        uint256 used0;uint256 used1;
        if(price<=x.lower)used0=SqrtPriceMath.getAmount0Delta(x.lower,x.upper,liq,false);
        else if(price>=x.upper)used1=SqrtPriceMath.getAmount1Delta(x.lower,x.upper,liq,false);
        else {used0=SqrtPriceMath.getAmount0Delta(price,x.upper,liq,false);used1=SqrtPriceMath.getAmount1Delta(x.lower,price,liq,false);}
        (used0,used1)=_allocationValues(x,used0,used1);e.deployed=used0+used1;
    }
    /// @notice Preserve the existing full-balance seed; partial mode targets the
    /// scarce asset needed for its post-cost main floor instead of a full reset.
    function seed(Context memory x,bool direction,uint256 fee) external pure returns(uint256 input,uint256 residual) {
        (uint256 u0,uint256 u1)=_units(x,x.spot);if(u0+u1==0)revert InvalidAmount();
        (uint256 v0,uint256 v1)=_allocationValues(x,x.amount0,x.amount1);
        uint256 excess;
        if(x.mainFloor==10000) {
            uint256 desired=Math.mulDiv(v0+v1,u0,u0+u1);
            excess=direction?v0-desired:desired-v0;residual=excess;
            uint256 weight=Math.mulDiv(direction?u0:u1,1e18,u0+u1);
            excess=Math.mulDiv(excess,1e18,1e18-Math.mulDiv(weight,fee,1_000_000));
        } else {
            uint256 weight=Math.mulDiv(direction?u1:u0,1e18,u0+u1);
            uint256 fraction=Math.mulDiv(weight,x.mainFloor,10000);
            uint256 needed=Math.mulDiv(v0+v1,fraction,1e18,Math.Rounding.Ceil);
            uint256 scarce=direction?v1:v0;
            if(needed<=scarce)return(0,0);
            residual=needed-scarce;
            excess=Math.mulDiv(residual,1e18,1e18-Math.mulDiv(1e18-fraction,fee,1_000_000),Math.Rounding.Ceil);
        }
        uint256 scale=x.mainFloor==10000?(direction?1e18:x.prices.scale1):(direction?x.marks[2]:x.marks[3]);
        uint256 mark=x.mainFloor==10000?(direction?x.prices.lower0:x.prices.lower1):(direction?x.marks[0]:x.marks[1]);
        input=Math.mulDiv(excess,scale,mark,
            x.mainFloor==10000?Math.Rounding.Floor:Math.Rounding.Ceil);
    }
}
