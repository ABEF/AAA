// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {RangePolicyRecord, RangeRewardAdmission} from "./RangePolicy.t.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
using DualOracleFixture for ZZZOracle;

contract KeeperRangeVault is RangePolicyRecord {
    bytes32 private pool;
    constructor(address controller) RangePolicyRecord(controller) {}
    function bindPool(bytes32 id) external { pool = id; }
    function poolBucket(bytes32 id) external view returns(uint256) { return id == pool ? 44 : 0; }
}
contract KeeperRangeAccess is MockAccess {
    function setSeal(bool value) external { isSealed = value; }
}

/// The real Registry/Strategy/dual-source Oracle execute against controlled
/// position observations. This does not claim actual venue settlement or VRF.
contract KeeperRangePolicyTest is Test {
    KeeperRangeAccess controller;
    ZZZPoolRegistry registry;
    ZZZStrategy strategy;
    ZZZOracle oracle;
    KeeperRangeVault vault;
    RangePolicyRecord venue;
    MockToken t0; MockToken t1; MockFeed f0; MockFeed f1;
    PoolConfig config; Position position; bytes32 pool;
    address constant KEEPER = address(0x4444);
    bytes32 constant REVIEW = keccak256("explicit inverse-price rule review");

    function setUp() public {
        vm.warp(1_000_000);
        controller = new KeeperRangeAccess();
        registry = new ZZZPoolRegistry(address(controller));
        strategy = new ZZZStrategy(address(controller));
        oracle = new ZZZOracle(address(controller),address(0));
        vault = new KeeperRangeVault(address(controller));
        venue = new RangePolicyRecord(address(controller));
        controller.bind(Ids.POOLS,address(registry)); controller.bind(Ids.STRATEGY,address(strategy));
        controller.bind(Ids.ORACLE,address(oracle)); controller.bind(Ids.VAULT,address(vault));
        controller.bind(Ids.LIQUIDITY,address(venue));
        controller.bind(Ids.REWARDS,address(new RangeRewardAdmission(address(controller))));
        MockToken a = new MockToken(18); MockToken b = new MockToken(18);
        (t0,t1) = address(a) < address(b) ? (a,b) : (b,a);
        f0 = new MockFeed(8,1e8); f1 = new MockFeed(8,1e8);
        oracle.setTestFeed(address(t0),address(f0),1 days);
        oracle.setTestFeed(address(t1),address(f1),1 days);
        config = PoolConfig(PoolKey(address(t0),address(t1),3000,200,address(0)),
            true,true,5000,500,100,100,600,100e18,1e30);
        pool = registry.configure(config); vault.bindPool(pool);
        position.poolId=pool; position.status=PositionStatus.Active;
        controller.setKeeper(KEEPER,true); controller.seal();
        _replace();
    }
    function _price(int256 rawToken1PerToken0) private {
        f0.set(rawToken1PerToken0,block.timestamp,block.timestamp);
        f1.set(1e8,block.timestamp,block.timestamp);
    }
    function _replace() private {
        (int24 lower,int24 upper,uint160 center) = strategy.target(pool);
        ++position.lpTokenId; position.centerX96=center; position.lastRebalance=uint64(block.timestamp);
        venue.setTicks(position.lpTokenId,lower,upper); vault.set(position);
    }
    function _approve() private {
        strategy.setRangeOrientation(pool,1); _replace();
        strategy.setKeeperRangePolicy(pool,true,100,1000,600,REVIEW);
    }
    function testExplicitOrientationPreservesLegacyUntilApprovedAndInvertsOutwardTicks() public {
        (int24 rawLower,int24 rawUpper,) = strategy.target(pool);
        assertEq(strategy.rangeOrientation(pool),0);
        strategy.setRangeOrientation(pool,1);
        (int24 lower,int24 upper,uint160 ref) = strategy.target(pool);
        assertTrue(lower != rawLower || upper != rawUpper);
        // Desired inverse price Q=1/P is [0.5Q,1.5Q], hence raw P is
        // [2P/3,2P]. Test the physical ticks bracket those endpoints.
        uint160 low = TickMath.getSqrtPriceAtTick(lower);
        uint160 high = TickMath.getSqrtPriceAtTick(upper);
        assertLe(Math.mulDiv(low,low,ref), Math.mulDiv(ref,2,3));
        assertGe(Math.mulDiv(high,high,ref), uint256(ref)*2);
        assertTrue(strategy.rangeUpdatePending(44));
        _replace(); assertFalse(strategy.rangeUpdatePending(44));
    }
    function _endpoints(bytes32 selected,uint16 width,uint160 ref) private {
        vm.mockCall(address(oracle),abi.encodeCall(oracle.referenceX96,(address(t0),address(t1))),abi.encode(ref));
        (int24 lower,int24 upper,) = strategy.target(selected);
        uint256 a = TickMath.getSqrtPriceAtTick(lower);
        uint256 b = TickMath.getSqrtPriceAtTick(upper);
        uint256 referenceSquared = uint256(ref)*ref;
        // Independent integer inequalities on actual Uniswap ticks. At these
        // bounded references all products fit uint256 without truncation.
        assertLe(a*a*(10000+uint256(width)),referenceSquared*10000);
        assertGe(b*b*(10000-uint256(width)),referenceSquared*10000);
    }
    function testFuzzInverseEndpointsBracketExactTickNeighbors(int24 tick,bool fine,bool wide) public {
        tick = int24(bound(int256(tick),-20000,20000));
        config.key.tickSpacing = fine ? int24(1) : int24(200);
        config.depositsEnabled = false; config.rangeBps = wide ? uint16(5000) : uint16(2500);
        bytes32 selected = registry.configure(config);
        strategy.setRangeOrientation(selected,1);
        uint160 ref = TickMath.getSqrtPriceAtTick(tick);
        _endpoints(selected,config.rangeBps,ref-1);
        _endpoints(selected,config.rangeBps,ref);
        _endpoints(selected,config.rangeBps,ref+1);
    }
    function testInverseTriggerTreatsUpAndDownMovesInTheChosenPriceDirection() public {
        strategy.setRangeOrientation(pool,1); _replace();
        config.triggerBps=1000; registry.configure(config);
        vm.warp(block.timestamp+600);
        _price(111000000); assertFalse(strategy.needsRebalance(44)); // inverse decline <10%
        _price(112000000); assertTrue(strategy.needsRebalance(44));
        _price(91000000); assertFalse(strategy.needsRebalance(44)); // inverse rise <10%
        _price(90000000); assertTrue(strategy.needsRebalance(44));
    }
    function testPolicyIsDisabledByDefaultAndCannotChooseUnapprovedWidths() public {
        assertEq(strategy.keeperRangeTarget(pool),0);
        vm.prank(KEEPER); vm.expectRevert(); strategy.applyKeeperRange(pool);
        vm.prank(KEEPER); vm.expectRevert(); registry.applyKeeperRange(pool,2500);
        vm.prank(address(strategy)); vm.expectRevert(); registry.applyKeeperRange(pool,3000);
        vm.prank(KEEPER); vm.expectRevert(); strategy.setRangeOrientation(pool,1);
        vm.prank(KEEPER); vm.expectRevert(); strategy.setKeeperRangePolicy(pool,true,100,1000,600,REVIEW);
    }
    function testRegistryCallbackPreservesEveryControllerLifecycleAndStopGuard() public {
        controller.setSeal(false);
        vm.prank(address(strategy)); vm.expectRevert(); registry.applyKeeperRange(pool,2500);
        controller.setSeal(true);
        for (uint8 state=1;state<=4;++state) {
            controller.setCanonicalState(state);
            vm.prank(address(strategy)); vm.expectRevert(); registry.applyKeeperRange(pool,2500);
        }
        controller.setCanonicalState(0); controller.setPreparation(true);
        vm.prank(address(strategy)); vm.expectRevert(); registry.applyKeeperRange(pool,2500);
        controller.setPreparation(false); controller.setPaused(true);
        vm.prank(address(strategy)); vm.expectRevert(); registry.applyKeeperRange(pool,2500);
        controller.setPaused(false); config.operationsEnabled=false; registry.configure(config);
        vm.prank(address(strategy)); vm.expectRevert(); registry.applyKeeperRange(pool,2500);
        assertEq(registry.get(pool).rangeBps,5000);
    }
    function testNarrowWidenHysteresisAndPhysicalApplicationRequireSeparateCheckpoints() public {
        _approve();
        assertEq(strategy.keeperRangeTarget(pool),0);
        vm.warp(block.timestamp+600); _price(1e8);
        assertEq(strategy.keeperRangeTarget(pool),2500);
        bytes32 beforeKey=keccak256(abi.encode(registry.get(pool).key));
        vm.prank(KEEPER); strategy.applyKeeperRange(pool);
        PoolConfig memory current=registry.get(pool);
        assertEq(current.rangeBps,2500); assertEq(keccak256(abi.encode(current.key)),beforeKey);
        assertEq(current.triggerBps,config.triggerBps); assertEq(current.maxSlippageBps,config.maxSlippageBps);
        vm.warp(block.timestamp+600); _price(80000000);
        assertEq(strategy.keeperRangeTarget(pool),0); // Prior width is not physically applied.
        _replace();
        vm.warp(block.timestamp+600); _price(64000000); // Inverse price rises25% from new center.
        assertEq(strategy.keeperRangeTarget(pool),5000);
        vm.prank(KEEPER); strategy.applyKeeperRange(pool);
        assertEq(registry.get(pool).rangeBps,5000);
    }
    function testChangedConfigurationDisablesEligibilityUntilGovernanceReviewsAgain() public {
        _approve(); vm.warp(block.timestamp+600);
        config.maxPositionUSD+=1; registry.configure(config);
        assertEq(strategy.keeperRangeTarget(pool),0);
        strategy.setKeeperRangePolicy(pool,true,100,1000,600,keccak256("new review"));
        vm.warp(block.timestamp+600); assertEq(strategy.keeperRangeTarget(pool),2500);
    }
    function testStopsLocksAndBadPriceCannotEnableRangeSelection() public {
        _approve(); vm.warp(block.timestamp+600);
        controller.setPaused(true); assertEq(strategy.keeperRangeTarget(pool),0);
        vm.prank(KEEPER); vm.expectRevert(); strategy.applyKeeperRange(pool);
        controller.setPaused(false); controller.setPreparation(true); assertEq(strategy.keeperRangeTarget(pool),0);
        controller.setPreparation(false); controller.setCanonicalState(1); assertEq(strategy.keeperRangeTarget(pool),0);
        controller.setCanonicalState(0);
        f0.set(1e8,block.timestamp-2 days,block.timestamp-2 days);
        vm.expectRevert(); strategy.keeperRangeTarget(pool);
        // Disabling requires no healthy Oracle or venue read.
        strategy.setKeeperRangePolicy(pool,false,0,0,0,bytes32(0));
        assertEq(strategy.keeperRangeTarget(pool),0);
    }
    function testThresholdBoundsOrientationAndCooldownAreGoverned() public {
        vm.expectRevert(); strategy.setRangeOrientation(pool,2);
        vm.expectRevert(); strategy.setKeeperRangePolicy(pool,true,100,1000,600,REVIEW); // raw mode
        strategy.setRangeOrientation(pool,1); _replace();
        vm.expectRevert(); strategy.setKeeperRangePolicy(pool,true,1000,1000,600,REVIEW);
        vm.expectRevert(); strategy.setKeeperRangePolicy(pool,true,0,2500,600,REVIEW);
        vm.expectRevert(); strategy.setKeeperRangePolicy(pool,true,100,1000,599,REVIEW);
        vm.expectRevert(); strategy.setKeeperRangePolicy(pool,true,100,1000,600,bytes32(0));
        strategy.setKeeperRangePolicy(pool,true,100,1000,600,REVIEW);
        strategy.setRangeOrientation(pool,0);
        vm.warp(block.timestamp+600); assertEq(strategy.keeperRangeTarget(pool),0);
    }
}
