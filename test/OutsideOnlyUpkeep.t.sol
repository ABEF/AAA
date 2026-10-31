// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";

import {Test} from "forge-std/Test.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IStateViewMinimal} from "../src/interfaces/IZZZ.sol";
import {Ids,PoolKey,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockPools,MockToken,MockFeed} from "./mocks/Mocks.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
using DualOracleFixture for ZZZOracle;

/// Current maintenance3 threshold observations. The historical filename is kept
/// for navigation; these tests do not assert the removed outside-only trigger.
/// Controlled source/physical observations, not live-market qualification.
contract UpkeepObservation {
    Position private record;
    int24 public lower; int24 public upper;
    uint160 private price = uint160(1<<96);
    int24 private tick;
    uint24 private protocol; uint24 private fee=3000;
    function setPosition(Position memory p) external {record=p;}
    function group(uint256) external view returns(Position memory) {return record;}
    function setTicks(int24 lo,int24 hi) external {lower=lo;upper=hi;}
    function ticks(uint256) external view returns(int24,int24) {return(lower,upper);}
    function setMarket(uint160 root,int24 storedTick) external {price=root;tick=storedTick;}
    function setFees(uint24 p,uint24 f) external {protocol=p;fee=f;}
    function stateView() external view returns(IStateViewMinimal) {return IStateViewMinimal(address(this));}
    function spot(bytes32) external view returns(uint160) {return price;}
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24) {return(price,tick,protocol,fee);}
}

contract ThresholdUpkeepTest is Test {
    MockAccess private access;
    MockPools private pools;
    ZZZStrategy private strategy;
    ZZZOracle private oracle;
    MockToken private t1;
    MockFeed private f0; MockFeed private f1;
    UpkeepObservation private observed;
    PoolConfig private config; Position private position; bytes32 private pool;
    uint256 private constant BUCKET=44;
    uint256 private constant INTERVAL=12 hours;

    function setUp() public {
        vm.warp(1_000_000);
        access=new MockAccess(); ProtocolPolicyFixture.bind(address(access));pools=new MockPools();oracle=new ZZZOracle(address(access),address(0));
        strategy=new ZZZStrategy(address(access), address(new ZZZPortfolioPolicy(address(access))), address(new ZZZRebalanceConfirmation(address(access))));observed=new UpkeepObservation();
        t1=new MockToken(18);f0=new MockFeed(8,1e8);f1=new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(f0),1 days);oracle.setTestFeed(address(t1),address(f1),1 days);
        access.bind(Ids.POOLS,address(pools));access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.VAULT,address(observed));access.bind(Ids.LIQUIDITY,address(observed));
        access.bind(Ids.STRATEGY,address(strategy));access.seal();
        config=PoolConfig(PoolKey(address(0),address(t1),3000,60,address(0)),
            true,true,2500,100,100,100,uint32(INTERVAL),100e18,1e24);
        pool=keccak256(abi.encode(config.key));pools.set(pool,config);
        strategy.setRangeOrientation(pool,1);
        (int24 lo,int24 hi,uint160 center)=strategy.target(pool);
        observed.setTicks(lo,hi);
        position=Position(pool,1,0,0,100e18,center,uint64(block.timestamp),PositionStatus.Active);
        observed.setPosition(position);
    }
    function _market(int24 storedTick,bool downward) private {
        uint160 root=TickMath.getSqrtPriceAtTick(downward?storedTick+1:storedTick);
        observed.setMarket(root,storedTick);
        uint256 usd=Math.mulDiv(Math.mulDiv(root,root,uint256(1)<<96),1e8,uint256(1)<<96);
        f0.set(int256(usd),block.timestamp,block.timestamp);f1.set(1e8,block.timestamp,block.timestamp);
    }
    function _afterCooldown() private {vm.warp(uint256(position.lastRebalance)+INTERVAL);}

    function testVersionAndOnePercentMoveInsideWideRangeDoNotAuthorizeReplacement() public {
        assertEq(strategy.MAINTENANCE_POLICY_VERSION(),3);
        _afterCooldown();_market(100,false); // About one percent, still well inside.
        assertFalse(strategy.rangeUpdatePending(BUCKET));assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testActualExitBeforeTwelveHoursWaitsUntilExactBoundary() public {
        _market(observed.upper(),false);
        vm.warp(uint256(position.lastRebalance)+1 hours);assertFalse(strategy.needsRebalance(BUCKET));
        vm.warp(uint256(position.lastRebalance)+INTERVAL-1);assertFalse(strategy.needsRebalance(BUCKET));
        _afterCooldown();_market(observed.upper(),false);assertTrue(strategy.needsRebalance(BUCKET));
    }
    function testThresholdIsAlreadyMetAtBothPhysicalRangeEdges() public {
        _afterCooldown();
        _market(observed.lower(),false);assertTrue(strategy.needsRebalance(BUCKET));
        _market(observed.upper()-1,false);assertTrue(strategy.needsRebalance(BUCKET));
        _market(observed.upper(),false);assertTrue(strategy.needsRebalance(BUCKET));
        _market(observed.lower()-1,false);assertTrue(strategy.needsRebalance(BUCKET));
    }
    function testExactDownwardCrossingRetainsActualStoredTick() public {
        _afterCooldown();
        _market(observed.lower()-1,true);assertTrue(strategy.needsRebalance(BUCKET));
        // The stored tick may still be inside at an exact downward crossing,
        // but85%price distance is already exceeded. Do not restore outside-only.
        _market(observed.upper()-1,true);assertTrue(strategy.needsRebalance(BUCKET));
    }
    function testDeliberateWidthChangeAppliesInsideOnlyAfterCooldown() public {
        config.rangeBps=5000;pools.set(pool,config);
        assertTrue(strategy.rangeUpdatePending(BUCKET));assertFalse(strategy.needsRebalance(BUCKET));
        _afterCooldown();assertTrue(strategy.needsRebalance(BUCKET));
        config.rangeBps=2500;pools.set(pool,config);assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testReturnInsideThresholdCancelsOrdinaryEligibility() public {
        _afterCooldown();_market(observed.upper(),false);assertTrue(strategy.needsRebalance(BUCKET));
        _market(0,false);assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testGovernedCooldownChangeUsesOriginalPhysicalClock() public {
        _market(observed.upper(),false);vm.warp(uint256(position.lastRebalance)+6 hours);
        assertFalse(strategy.needsRebalance(BUCKET));
        config.minRebalanceInterval=6 hours;pools.set(pool,config);
        _market(observed.upper(),false);assertTrue(strategy.needsRebalance(BUCKET));
        assertEq(observed.group(BUCKET).lastRebalance,position.lastRebalance);
    }
    function testInconsistentTickSqrtAndMalformedFeesRejectEligibility() public {
        _afterCooldown();observed.setMarket(uint160(1<<96),1);
        vm.expectRevert(ZZZModule.InvalidState.selector);strategy.needsRebalance(BUCKET);
        observed.setMarket(uint160(1<<96),0);observed.setFees(1001,3000);
        vm.expectRevert(ZZZModule.InvalidState.selector);strategy.needsRebalance(BUCKET);
        observed.setFees(0,500);
        vm.expectRevert(ZZZModule.InvalidState.selector);strategy.needsRebalance(BUCKET);
    }
    function testFreshnessAndExecutionReferenceAreNotReplacedByPoolSpot() public {
        _afterCooldown();_market(observed.upper(),false);
        f0.set(1e8,block.timestamp-2 days,block.timestamp-2 days);
        vm.expectRevert();strategy.needsRebalance(BUCKET);
        f0.set(1e8,block.timestamp,block.timestamp);
        vm.expectRevert(ZZZModule.Slippage.selector);strategy.needsRebalance(BUCKET);
    }
    function testInactiveDisabledAndMalformedPhysicalRangesCannotAuthorizeWork() public {
        _afterCooldown();config.operationsEnabled=false;pools.set(pool,config);
        assertFalse(strategy.needsRebalance(BUCKET));
        config.operationsEnabled=true;pools.set(pool,config);observed.setTicks(0,0);
        vm.expectRevert(ZZZModule.InvalidState.selector);strategy.needsRebalance(BUCKET);
        position.status=PositionStatus.Parked;observed.setPosition(position);
        assertFalse(strategy.needsRebalance(BUCKET));
    }
}
