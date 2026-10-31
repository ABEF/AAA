// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {Test} from "forge-std/Test.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {Ids,PoolKey,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockPools,MockToken,MockFeed} from "./mocks/Mocks.sol";
import {DynamicRangeVectors as Vectors} from "./helpers/DynamicRangeVectors.sol";

// Read-only synthetic venue state; real manager/strategy/oracle/metadata math.
// This is not Uniswap settlement or production feed qualification.
contract RangeDependency {}
contract RangeState {
    address public poolManager; uint160 public price;
    constructor(address manager) {poolManager=manager;}
    function set(uint160 value) external {price=value;}
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24){return(price,0,0,3000);}
}
contract RangePositionManager {
    address public poolManager; address public permit2;
    PoolKey private key; int24 private lower; int24 private upper;
    uint256 public currentId=1;
    constructor(address m,address p){poolManager=m;permit2=p;}
    function set(PoolKey memory k,int24 l,int24 u) external {key=k;lower=l;upper=u;}
    function getPoolAndPositionInfo(uint256 id) external view returns(PoolKey memory,uint256){
        require(id==currentId);return(key,(uint256(uint24(lower))<<8)|(uint256(uint24(upper))<<32));
    }
    function getPositionLiquidity(uint256 id) external view returns(uint128){require(id==currentId);return 1e18;}
}
contract RangeLedger {
    function migrationBudget() external view returns(address){return address(this);}
    function historicalCompoundValue(uint256) external pure returns(uint256){return 0;}
    Position private record;
    function set(Position memory p) external {record=p;}
    function group(uint256) external view returns(Position memory){return record;}
    function nftBucket(uint256) external pure returns(uint256){return 1;}
    function sharesOf(uint256) external pure returns(uint256){return 5;}
    function bucketTotalShares(uint256) external pure returns(uint256){return 100;}
    function compoundBalance(uint256,address) external pure returns(uint256){return 0;}
}
contract DynamicRangeTest is Test {
    MockAccess ac; MockPools pools; ZZZOracle oracle; ZZZStrategy strategy;
    ZZZLiquidityManager manager; ZZZNFTMetadata metadata;
    RangeState state; RangePositionManager posm; RangeLedger ledger;
    MockFeed feed0; MockFeed feed1; PoolConfig config; bytes32 pool;
    address constant T0=address(0x1000); address constant T1=address(0x2000);
    function setUp() public {
        vm.warp(1000000); ac=new MockAccess(); ProtocolPolicyFixture.bind(address(ac));pools=new MockPools();ledger=new RangeLedger();
        address core=address(new RangeDependency());address permit=address(new RangeDependency());
        state=new RangeState(core);posm=new RangePositionManager(core,permit);
        manager=new ZZZLiquidityManager(address(ac),address(posm),address(state),core,permit, address(new ZZZLPBalancer(address(ac), core, address(state))));
        oracle=new ZZZOracle(address(ac),address(0));strategy=new ZZZStrategy(address(ac), address(new ZZZPortfolioPolicy(address(ac))), address(new ZZZRebalanceConfirmation(address(ac))));
        metadata=new ZZZNFTMetadata(address(ac));feed0=new MockFeed(8,1e8);feed1=new MockFeed(8,1e8);
        ac.bind(Ids.POOLS,address(pools));ac.bind(Ids.ORACLE,address(oracle));ac.bind(Ids.STRATEGY,address(strategy));
        ac.bind(Ids.LIQUIDITY,address(manager));ac.bind(Ids.VAULT,address(ledger));ac.bind(Ids.FEES,address(ledger));ac.seal();
        config.key=PoolKey(T0,T1,3000,60,address(0));config.operationsEnabled=true;
        config.rangeBps=5000;config.triggerBps=1000;config.maxSpotDeviationBps=100;config.maxSlippageBps=100;
        pool=keccak256(abi.encode(config.key));
    }
    function _load(uint256 n) private returns(Vectors.V memory v) {
        v=Vectors.get(n);vm.etch(T0,address(new MockToken(v.d0)).code);vm.etch(T1,address(new MockToken(v.d1)).code);
        feed0.set(v.reverse?int256(1e8):int256(v.priceE8),block.timestamp,block.timestamp);
        feed1.set(v.reverse?int256(v.priceE8):int256(1e8),block.timestamp,block.timestamp);
        oracle.setTestFeed(T0,address(feed0),3600);oracle.setTestFeed(T1,address(feed1),3600);
        pools.set(pool,config);posm.set(config.key,v.lower,v.upper);state.set(v.spot);
        Position memory p;p.poolId=pool;p.lpTokenId=1;p.status=PositionStatus.Active;
        p.centerX96=uint160(1<<96);ledger.set(p);
    }
    function _assertNetDeployment(Vectors.V memory v,bool direction,uint256 input,uint256 swap) private view {
        // Value the real post-fee pair using the independent Decimal position
        // vector. No strategy weight or target helper supplies this expectation.
        uint256 output=oracle.quote(direction?T0:T1,direction?T1:T0,swap)*997000/1_000_000;
        uint256 a0=direction?input-swap:output;
        uint256 a1=direction?output:input-swap;
        uint256 unit0=oracle.value(T0,v.a0);uint256 unit1=oracle.value(T1,v.a1);
        uint256 value0=oracle.value(T0,a0);uint256 value1=oracle.value(T1,a1);
        assertApproxEqAbs(Math.mulDiv(value0,1_000_000,value0+value1),v.weight0,2);
        uint256 scale=v.a0==0?Math.mulDiv(a1,1e18,v.a1):v.a1==0?Math.mulDiv(a0,1e18,v.a0):
            Math.min(Math.mulDiv(a0,1e18,v.a0),Math.mulDiv(a1,1e18,v.a1));
        uint256 deployed=Math.mulDiv(scale,unit0+unit1,1e18);
        assertGe(deployed,oracle.value(direction?T0:T1,input)*99/100);
    }
    function testIndependentAmountsAndExistingRangePlanAcrossPricesAndDecimals() public {
        for(uint256 i;i<36;++i){
            Vectors.V memory v=_load(i);(uint256 x,uint256 y)=manager.amounts(1);
            // Independent Decimal sqrt encodings differ by at most insignificant
            // raw-unit rounding; 1e-20 relative + 2 raw units is the stated bound.
            assertApproxEqAbs(x,v.a0,v.a0/1e20+2);assertApproxEqAbs(y,v.a1,v.a1/1e20+2);
            for(uint256 size=100;size<=10000;size*=100){
                uint256 amount0=size*1e18*10**v.d0/oracle.price(T0);
                uint256 amount1=size*1e18*10**v.d1/oracle.price(T1);
                (bool direction,uint256 swap,)=strategy.compoundPlan(1,amount0,0);
                // Solve the independently derived target ratio after the actual
                // 3000-pip LP charge, rather than treating the swap as free.
                if(swap>0)assertTrue(direction);
                uint256 unit0=oracle.value(T0,v.a0);uint256 unit1=oracle.value(T1,v.a1);
                uint256 expected=Math.mulDiv(amount0,unit1*1_000_000,(unit0+unit1)*1_000_000-unit0*3000);
                assertApproxEqAbs(swap,expected,amount0/1_000_000+2);
                _assertNetDeployment(v,true,amount0,swap);
                (direction,swap,)=strategy.compoundPlan(1,0,amount1);
                if(swap>0)assertFalse(direction);
                expected=Math.mulDiv(amount1,unit0*1_000_000,(unit0+unit1)*1_000_000-unit1*3000);
                assertApproxEqAbs(swap,expected,amount1/1_000_000+2);
                _assertNetDeployment(v,false,amount1,swap);
                // A proportional dual-token entry requires at most rounding dust.
                (direction,swap,)=strategy.compoundPlan(1,amount0*v.weight0/1_000_000,amount1*(1_000_000-v.weight0)/1_000_000);
                assertLe(oracle.value(direction?T0:T1,swap),size*1e18/100000+2e12);
            }
            uint256 nav=oracle.value(T0,x)+oracle.value(T1,y);
            assertEq(metadata.currentValue(444),nav*5/100);
        }
    }
    function testInitialRangeRecentersButExistingEntryUsesOldRange() public {
        Vectors.V memory v=_load(5); // $1.40 in the original approximately .50-1.50 range
        (int24 lower,int24 upper,)=strategy.target(pool);
        assertGt(lower,v.lower);assertGt(upper,v.upper);
        (bool d,uint256 oldSwap,)=strategy.compoundPlan(1,100e18,0);
        (bool n,uint256 newSwap,)=strategy.swapPlan(pool,100e18,0);
        assertTrue(d&&n);assertGt(oldSwap,newSwap);
    }
    function testMetadataRejectsManipulatedSpotEvenWithFreshUsdFeeds() public {
        _load(3);state.set(uint160(2<<96));
        vm.expectRevert();strategy.validateExitPrice(pool);
        vm.expectRevert();metadata.currentValue(444);
    }
    function testDisabledOperationsStillPermitHonestValuation() public {
        _load(3);config.operationsEnabled=false;pools.set(pool,config);
        assertGt(metadata.currentValue(444),0);
        vm.expectRevert();strategy.compoundPlan(1,100e18,0);
    }
    function testStaleOracleAndFailedVenueCannotBecomeVerifiedZero() public {
        _load(3);feed0.set(1e8,block.timestamp-4000,block.timestamp-4000);
        vm.expectRevert();metadata.currentValue(444);
        _load(3);vm.etch(address(posm),hex"00");vm.expectRevert();metadata.currentValue(444);
    }
}
