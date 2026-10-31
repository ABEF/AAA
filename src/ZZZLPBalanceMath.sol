// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {LiquidityAmounts} from "@uniswap/v4-periphery/src/libraries/LiquidityAmounts.sol";
import {PoolKey} from "./libraries/ZZZTypes.sol";
import {IPositionManagerMinimal,IStateViewMinimal} from "./interfaces/IZZZ.sol";

/// @notice Fixed noncustodial arithmetic child. No approvals, storage writes,
/// callback, execution or recipient authority. Separates ordinary code-size gates.
contract ZZZLPBalanceMath {
    uint256 public constant LP_BALANCE_MATH_VERSION = 1;
    address public immutable balancer;
    struct Prices { uint256 lower0; uint256 upper0; uint256 lower1; uint256 upper1; uint256 scale1; uint160 referenceX96; uint16 extraLoss; }
    struct Context { bytes32 target; uint160 spot; uint160 lower; uint160 upper; uint256 amount0; uint256 amount1; Prices prices; uint16 mainFloor; uint256[4] marks; }
    struct Evaluation { uint256 deployed; uint256 retained; uint256 imbalance; bool excess0; }
    error InvalidAmount();
    constructor() { balancer = msg.sender; }

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
