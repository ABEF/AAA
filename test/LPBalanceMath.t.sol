// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZLPBalanceMath} from "../src/ZZZLPBalanceMath.sol";

/// @dev Arithmetic verification only. These are not actual-core swap quotes,
/// route selection, deployment-size gates or production service qualification.
contract LPBalanceMathTest is Test {
    uint160 private constant Q96 = uint160(1 << 96);
    ZZZLPBalanceMath private calculation;

    function setUp() public { calculation = new ZZZLPBalanceMath(); }
    function _context(uint256 first,uint256 second,uint16 mainFloor)
        private pure returns(ZZZLPBalanceMath.Context memory x) {
        x.target = keccak256("test-only arithmetic pair");
        x.spot=Q96; x.lower=Q96/2; x.upper=Q96*2;
        x.amount0=first; x.amount1=second; x.mainFloor=mainFloor;
        x.prices=ZZZLPBalanceMath.Prices(1 ether,1 ether,1 ether,1 ether,1 ether,Q96,100);
        if(mainFloor!=10000)x.marks=[uint256(1 ether),1 ether,1 ether,1 ether];
    }
    function testMathChildHasNoMutableParentChoice() public view {
        assertEq(calculation.LP_BALANCE_MATH_VERSION(),1); assertEq(calculation.balancer(),address(this));
    }
    function testFullSeedRetainsOriginalFloorRoundingExactly() public view {
        ZZZLPBalanceMath.Context memory x = _context(80 ether,20 ether,10000);
        // Independent exact integer vectors for30/(1-fee/2). The fractional
        // result is truncated as in the original full-balance implementation.
        uint256[4] memory fees=[uint256(0),3000,11010,100000];
        uint256[4] memory expected=[uint256(30000000000000000000),30045067601402103154,
            30166064183329227396,31578947368421052631];
        for(uint256 i;i<fees.length;++i) {
            (uint256 input,uint256 residual)=calculation.seed(x,true,fees[i]);
            assertEq(input,expected[i]); assertEq(residual,30 ether);
        }
        x=_context(20 ether,80 ether,10000);
        (uint256 reverse,uint256 excess)=calculation.seed(x,false,11010);
        assertEq(reverse,expected[2]); assertEq(excess,30 ether);
    }
    function testPartialSeedTargetsPostCostFloorRatherThanPreCostSixty() public view {
        ZZZLPBalanceMath.Context memory x = _context(80 ether,20 ether,6000);
        // Scarce side needs10of100before costs. With1%known fee, solve
        // 20+.99x >= .3*(100-.01x), hence x >=10/.993.
        (uint256 input,uint256 deficit)=calculation.seed(x,true,10000);
        assertEq(input,10070493454179254784); assertEq(deficit,10 ether);
        uint256 output=Math.mulDiv(input,990000,1_000_000);
        ZZZLPBalanceMath.Evaluation memory e=calculation.evaluate(x,Q96,x.amount0-input,x.amount1+output);
        uint256 required=Math.mulDiv(e.retained,6000,10000,Math.Rounding.Ceil);
        // Predicted principal rounds down; the execution layer must still
        // validate actual mints. The seed is a starting candidate, not proof.
        assertApproxEqAbs(e.deployed,required,4);
        assertLt(e.deployed,60 ether); assertLt(input,11 ether);
        (uint256 full,)=calculation.seed(_context(80 ether,20 ether,10000),true,10000);
        assertLt(input,full);
    }
    function testPartialSeedOppositeDirectionAndFeeVectors() public view {
        ZZZLPBalanceMath.Context memory x=_context(20 ether,80 ether,6000);
        uint256[4] memory fees=[uint256(0),3000,11010,100000];
        uint256[4] memory expected=[uint256(10000000000000000000),10021044192804890270,
            10077668591837289994,10752688172043010753];
        for(uint256 i;i<fees.length;++i) {
            (uint256 input,uint256 residual)=calculation.seed(x,false,fees[i]);
            assertEq(input,expected[i]); assertEq(residual,10 ether);
        }
    }
    function testAlreadySufficientPassiveMainDoesNotNeedRepairSwap() public view {
        ZZZLPBalanceMath.Context memory x=_context(65 ether,35 ether,6000);
        (uint256 input,uint256 residual)=calculation.seed(x,true,11010);
        assertEq(input,0); assertEq(residual,0);
        ZZZLPBalanceMath.Evaluation memory e=calculation.evaluate(x,Q96,x.amount0,x.amount1);
        assertEq(e.retained,100 ether); assertApproxEqAbs(e.deployed,70 ether,2);
    }
    function testFullyOneSidedInventoryNeedsOnlyMainFloorRepairNotFullBalance() public view {
        ZZZLPBalanceMath.Context memory x=_context(100 ether,0,6000);
        (uint256 partialInput,)=calculation.seed(x,true,11010);
        (uint256 full,)=calculation.seed(_context(100 ether,0,10000),true,11010);
        assertGt(partialInput,30 ether); assertLt(partialInput,31 ether);
        assertGt(full,50 ether); assertLt(partialInput,full);
    }
    function testEvaluateUsesDeployableValueNotRawLiquidityOrIdle() public view {
        ZZZLPBalanceMath.Context memory x=_context(80 ether,20 ether,6000);
        ZZZLPBalanceMath.Evaluation memory e=calculation.evaluate(x,Q96,x.amount0,x.amount1);
        assertEq(e.retained,100 ether); assertApproxEqAbs(e.deployed,40 ether,2);
        assertEq(e.imbalance,30 ether); assertTrue(e.excess0);
        e=calculation.evaluate(x,Q96/2,x.amount0,x.amount1);
        assertApproxEqAbs(e.deployed,80 ether,2);
        e=calculation.evaluate(x,Q96*2,x.amount0,x.amount1);
        assertApproxEqAbs(e.deployed,20 ether,2);
    }
    function testRoundedDebtNeverUsesUnprovidedAssetAndBoundsPrincipal() public view {
        int24 lower=-4080; int24 upper=6960;
        uint256 amount0=13 ether; uint256 amount1=9 ether;
        (uint128 liquidity,uint256 nativeDebt)=calculation.deploymentAmounts(Q96,lower,upper,amount0,amount1);
        (uint256 debt0,uint256 debt1)=calculation.deploymentDebts(Q96,lower,upper,liquidity);
        assertEq(nativeDebt,debt0); assertLe(debt0,amount0); assertLe(debt1,amount1);
        uint256 principal0=SqrtPriceMath.getAmount0Delta(Q96,TickMath.getSqrtPriceAtTick(upper),liquidity,false);
        uint256 principal1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),Q96,liquidity,false);
        assertGe(debt0,principal0); assertLe(debt0-principal0,1);
        assertGe(debt1,principal1); assertLe(debt1-principal1,1);
    }
    function testOneSidedDeploymentDebtsAtBothRangeBoundaries() public view {
        int24 lower=-600; int24 upper=600;
        uint160 a=TickMath.getSqrtPriceAtTick(lower); uint160 b=TickMath.getSqrtPriceAtTick(upper);
        (uint256 first,uint256 second)=calculation.deploymentDebts(a,lower,upper,1 ether);
        assertGt(first,0); assertEq(second,0);
        (first,second)=calculation.deploymentDebts(b,lower,upper,1 ether);
        assertEq(first,0); assertGt(second,0);
    }
    function testFuzzFullSeedMatchesOriginalClosedForm(uint96 surplus,uint96 scarce,uint24 fee) public view {
        surplus=uint96(bound(surplus,1,1e25)); scarce=uint96(bound(scarce,0,surplus));
        fee=uint24(bound(fee,0,100000));
        ZZZLPBalanceMath.Context memory x=_context(surplus,scarce,10000);
        uint256 desired=(uint256(surplus)+scarce)/2;
        uint256 excess=uint256(surplus)-desired;
        uint256 original=excess*1e18/(1e18-(uint256(5e17)*fee/1_000_000));
        (uint256 input,uint256 residual)=calculation.seed(x,true,fee);
        assertEq(input,original); assertEq(residual,excess);
    }
}
