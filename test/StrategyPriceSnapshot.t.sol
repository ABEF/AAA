// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {IZZZOracle,IPriceFeed,IStateViewMinimal} from "../src/interfaces/IZZZ.sol";
import {Ids,PoolKey,PoolConfig,Position} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockPools,MockToken,MockFeed} from "./mocks/Mocks.sol";

/// @dev Venue reads are synthetic. The Oracle and its two separately controlled
/// source mocks per asset are real code; this does not qualify actual providers.
contract SnapshotVenue {
    uint160 public current;
    int24 private lower; int24 private upper;
    uint24 public protocolFee;
    uint24 public lpFee;
    function set(uint160 price,int24 lo,int24 hi,uint24 protocol,uint24 lp) external {
        current=price;lower=lo;upper=hi;protocolFee=protocol;lpFee=lp;
    }
    function stateView() external view returns(IStateViewMinimal) { return IStateViewMinimal(address(this)); }
    function spot(bytes32) external view returns(uint160) { return current; }
    function ticks(uint256) external view returns(int24,int24) { return(lower,upper); }
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24) { return(current,0,protocolFee,lpFee); }
}
contract SnapshotVault {
    bytes32 private pool;
    function set(bytes32 id) external { pool=id; }
    function group(uint256) external view returns(Position memory p) { p.poolId=pool;p.lpTokenId=1; }
}

contract StrategyPriceSnapshotTest is Test {
    MockAccess private access;
    MockPools private pools;
    ZZZOracle private oracle;
    ZZZStrategy private strategy;
    SnapshotVenue private venue;
    SnapshotVault private ledger;
    MockFeed[4] private feeds;
    PoolConfig private config;
    bytes32 private poolId;
    address private token0;
    address private constant TOKEN1=address(0x2000);

    function setUp() public {
        vm.warp(1_000_000);access=new MockAccess();pools=new MockPools();
        oracle=new ZZZOracle(address(access),address(0));strategy=new ZZZStrategy(address(access));
        venue=new SnapshotVenue();ledger=new SnapshotVault();
        access.bind(Ids.POOLS,address(pools));access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.LIQUIDITY,address(venue));access.bind(Ids.VAULT,address(ledger));
        _load(false,18,18);
    }
    function _admit(address token,int256 answer,uint256 index) private {
        MockFeed a=new MockFeed(8,answer);MockFeed b=new MockFeed(8,answer*1005/1000);
        feeds[index]=a;feeds[index+1]=b;
        oracle.setDualFeed(token,
            ZZZOracle.SourcePolicy(address(a),address(a).codehash,keccak256(abi.encode("mock A",token)),3600,8),
            ZZZOracle.SourcePolicy(address(b),address(b).codehash,keccak256(abi.encode("mock B",token)),3600,8),
            300,keccak256("TEST_ONLY_NOT_PROVIDER_QUALIFICATION"));
    }
    function _load(bool native,uint8 decimals0,uint8 decimals1) private {
        token0=native?address(0):address(0x1000);
        if (!native) vm.etch(token0,address(new MockToken(decimals0)).code);
        vm.etch(TOKEN1,address(new MockToken(decimals1)).code);
        _admit(token0,2000e8,0);_admit(TOKEN1,125e6,2);
        config.key=PoolKey(token0,TOKEN1,10020,200,address(0));
        config.operationsEnabled=true;config.rangeBps=5000;
        config.maxSpotDeviationBps=100;config.maxSlippageBps=200;
        poolId=keccak256(abi.encode(config.key));pools.set(poolId,config);ledger.set(poolId);
        (int24 lo,int24 hi,uint160 ref)=strategy.target(poolId);
        venue.set(ref,lo,hi,uint24(700|(1000<<12)),10020);
    }

    /// @dev Unchanged pre-optimization formula, intentionally retaining all
    /// repeated Oracle calls as a rounding/output parity oracle and gas control.
    function _legacy(bool existing,uint256 amount0,uint256 amount1)
        private view returns(bool zeroForOne,uint256 amountIn,uint256 minimumOut) {
        int24 lower;int24 upper;
        if(existing) (lower,upper)=venue.ticks(1);else (lower,upper,)=strategy.target(poolId);
        uint160 spot=strategy.validatePrice(poolId);
        uint160 a=TickMath.getSqrtPriceAtTick(lower);uint160 b=TickMath.getSqrtPriceAtTick(upper);
        uint256 unit0;uint256 unit1;
        if(spot<=a)unit0=SqrtPriceMath.getAmount0Delta(a,b,1e18,false);
        else if(spot>=b)unit1=SqrtPriceMath.getAmount1Delta(a,b,1e18,false);
        else {unit0=SqrtPriceMath.getAmount0Delta(spot,b,1e18,false);unit1=SqrtPriceMath.getAmount1Delta(a,spot,1e18,false);}
        uint256 v0=oracle.value(token0,amount0);uint256 v1=oracle.value(TOKEN1,amount1);
        uint256 u0=oracle.value(token0,unit0);uint256 u1=oracle.value(TOKEN1,unit1);
        require(u0+u1!=0);
        uint256 desired0=Math.mulDiv(v0+v1,u0,u0+u1);zeroForOne=v0>desired0;
        address input=zeroForOne?token0:TOKEN1;address output=zeroForOne?TOKEN1:token0;
        uint256 excess=zeroForOne?v0-desired0:desired0-v0;
        (,,uint24 protocol,uint24 lpFee)=venue.getSlot0(poolId);
        uint256 pf=zeroForOne?protocol&0xfff:protocol>>12;
        uint256 fee=pf+uint256(lpFee)-Math.mulDiv(pf,lpFee,1_000_000);
        uint256 weight=Math.mulDiv(zeroForOne?u0:u1,1e18,u0+u1);
        excess=Math.mulDiv(excess,1e18,1e18-Math.mulDiv(weight,fee,1_000_000));
        amountIn=Math.mulDiv(excess,10**oracle.tokenDecimals(input),oracle.price(input));
        require(amountIn<=(zeroForOne?amount0:amount1));
        minimumOut=Math.mulDiv(oracle.quote(input,output,amountIn),10000-config.maxSlippageBps,10000);
        if(minimumOut==0)amountIn=0;
    }
    function _parity(uint256 amount0,uint256 amount1) private view {
        (bool oldDirection,uint256 oldInput,uint256 oldMinimum)=_legacy(false,amount0,amount1);
        (bool direction,uint256 input,uint256 minimum)=strategy.swapPlan(poolId,amount0,amount1);
        assertEq(direction,oldDirection);assertEq(input,oldInput);assertEq(minimum,oldMinimum);
        (oldDirection,oldInput,oldMinimum)=_legacy(true,amount0,amount1);
        (direction,input,minimum)=strategy.compoundPlan(1,amount0,amount1);
        assertEq(direction,oldDirection);assertEq(input,oldInput);assertEq(minimum,oldMinimum);
    }
    function testExactPlannerParityAcrossNativeMixedDecimalsBothDirectionsAndDualSpread() public {
        for(uint256 i;i<4;++i) {
            _load(i<2,i%2==0?18:6,i%2==0?6:18);
            uint256 a0=100e18*(10**oracle.tokenDecimals(token0))/oracle.price(token0);
            uint256 a1=100e18*(10**oracle.tokenDecimals(TOKEN1))/oracle.price(TOKEN1);
            _parity(a0,0);_parity(0,a1);_parity(a0,a1);_parity(a0/17,a1/31);
        }
    }
    function testParityWithReversedAssetPricesAndSecondaryAsLowerSource() public {
        for(uint256 i;i<2;++i) {
            _load(i==0,18,6);
            // Source address/order does not identify the upper or lower bound.
            // Also reverse the asset USD-price ordering from the main vectors.
            feeds[0].set(125625000,block.timestamp,block.timestamp);
            feeds[1].set(125000000,block.timestamp,block.timestamp);
            feeds[2].set(2010e8,block.timestamp,block.timestamp);
            feeds[3].set(2000e8,block.timestamp,block.timestamp);
            (int24 lo,int24 hi,uint160 ref)=strategy.target(poolId);
            venue.set(ref,lo,hi,uint24(1000|(700<<12)),10020);
            uint256 a0=100e18*(10**oracle.tokenDecimals(token0))/oracle.price(token0);
            uint256 a1=100e18*(10**oracle.tokenDecimals(TOKEN1))/oracle.price(TOKEN1);
            _parity(a0,0);_parity(0,a1);_parity(a0/17,a1/31);
        }
    }
    function testExistingRangeParityWhenSpotIsOutsideEitherBoundary() public {
        uint160 ref=oracle.referenceX96(token0,TOKEN1);
        int24 spotTick=TickMath.getTickAtSqrtPrice(ref);
        int24 near=spotTick/200*200;
        venue.set(ref,near+400,near+2000,uint24(700|(1000<<12)),10020);
        _parity(0.05 ether,0);_parity(0,80 ether);
        venue.set(ref,near-2000,near-400,uint24(700|(1000<<12)),10020);
        _parity(0.05 ether,0);_parity(0,80 ether);
    }
    function _expectSinglePairRead() private {
        vm.expectCall(address(oracle),abi.encodeCall(IZZZOracle.priceBounds,(token0)),1);
        vm.expectCall(address(oracle),abi.encodeCall(IZZZOracle.priceBounds,(TOKEN1)),1);
        for(uint256 i;i<4;++i) vm.expectCall(address(feeds[i]),abi.encodeCall(IPriceFeed.latestRoundData,()),1);
    }
    function testSwapPlanReadsEachValidatedPairSourceExactlyOnce() public {
        _expectSinglePairRead();strategy.swapPlan(poolId,1 ether,0);
    }
    function testCompoundPlanReadsEachValidatedPairSourceExactlyOnce() public {
        _expectSinglePairRead();strategy.compoundPlan(1,0,100e18);
    }
    function testSecondSourceStalenessAndInvalidPriceCannotUseSnapshotFallback() public {
        feeds[1].set(2000e8,block.timestamp-3601,block.timestamp-3601);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,token0));
        strategy.swapPlan(poolId,1 ether,0);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,token0));
        strategy.compoundPlan(1,0,100e18);
        feeds[1].set(2000e8,block.timestamp,block.timestamp);
        feeds[3].set(0,block.timestamp,block.timestamp);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,TOKEN1));
        strategy.swapPlan(poolId,1 ether,0);
    }
    function testSnapshotIsNotReusedAcrossCallsAndDivergenceFailsClosed() public {
        strategy.swapPlan(poolId,1 ether,0);
        feeds[1].set(2100e8,block.timestamp,block.timestamp);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,token0));
        strategy.swapPlan(poolId,1 ether,0);
    }
    function testManipulatedSpotAndDisabledOperationsStillFailClosed() public {
        (int24 lo,int24 hi,)=strategy.target(poolId);uint160 ref=oracle.referenceX96(token0,TOKEN1);
        venue.set(uint160(uint256(ref)*110/100),lo,hi,0,10020);
        vm.expectRevert();strategy.swapPlan(poolId,1 ether,0);
        config.operationsEnabled=false;pools.set(poolId,config);
        vm.expectRevert();strategy.swapPlan(poolId,1 ether,0);
        vm.expectRevert();strategy.compoundPlan(1,0,100e18);
    }
    function testMemorySnapshotGasControlRetainsExactOutput() public {
        uint256 beforeGas=gasleft();(bool d,uint256 input,uint256 minimum)=_legacy(false,1 ether,0);
        uint256 legacyGas=beforeGas-gasleft();beforeGas=gasleft();
        (bool d2,uint256 input2,uint256 minimum2)=strategy.swapPlan(poolId,1 ether,0);
        uint256 snapshotGas=beforeGas-gasleft();assertEq(d,d2);assertEq(input,input2);assertEq(minimum,minimum2);
        emit log_named_uint("Repeated-read formula gas (warm fixture)",legacyGas);
        emit log_named_uint("Pair snapshot gas (warm fixture)",snapshotGas);
        // Fixed mocks characterize this planner only, not real provider gas.
        assertLt(snapshotGas,legacyGas);
    }
}
