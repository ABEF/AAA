// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";

import {Test} from "forge-std/Test.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {IStateViewMinimal} from "../src/interfaces/IZZZ.sol";
import {MockAccess} from "./mocks/Mocks.sol";
import {SinglePositionFixture} from "./helpers/PortfolioFixture.sol";

/// @dev TEST ONLY source/admission/venue fixtures. Real Strategy and Budget
/// enforce current confirmation3/600-second persistence and maintenance3. The
/// explicit single-leg fixture does not qualify real feeds/custody/keeper rollout.
contract ConfirmationOracleFixture {
    ZZZContributionPricing public immutable contributionPricing;
    constructor(address controller) { contributionPricing = new ZZZContributionPricing(controller,address(this)); }
    mapping(address => bytes32) public activePolicy;
    bytes32 public activeSequencerPolicy = keccak256("test sequencer policy");
    uint160 public referencePrice = uint160(1 << 96);
    bool public failed;
    function setPolicy(address token,bytes32 id) external { activePolicy[token] = id; }
    function setReference(uint160 price) external { referencePrice = price; }
    function setFailed(bool value) external { failed = value; }
    function referenceX96(address,address) external view returns(uint160) { require(!failed,"test price fault"); return referencePrice; }
    function price(address) external view returns(uint256) { require(!failed,"test price fault"); return 1e18; }
    function tokenDecimals(address) external pure returns(uint8) { return 18; }
}
contract ConfirmationPoolsFixture {
    PoolConfig private config;
    uint64 public configurationRevision;
    function set(PoolConfig memory next) external { config = next; ++configurationRevision; }
    function get(bytes32) external view returns(PoolConfig memory) { return config; }
    function accounting(bytes32) external view returns(PoolConfig memory) { return config; }
}
contract ConfirmationVenueFixture is SinglePositionFixture {
    int24 public lower; int24 public upper; int24 public tick;
    function setRange(int24 lo,int24 hi) external { lower=lo; upper=hi; }
    function setTick(int24 next) external { tick=next; }
    function ticks(uint256) external view returns(int24,int24) { return(lower,upper); }
    function spot(bytes32) external view returns(uint160) { return TickMath.getSqrtPriceAtTick(tick); }
    function stateView() external view returns(IStateViewMinimal) { return IStateViewMinimal(address(this)); }
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24) {
        return(TickMath.getSqrtPriceAtTick(tick),tick,0,3000);
    }
    function amounts(uint256) external pure returns(uint256,uint256) { return(10 ether,10 ether); }
}

contract RebalanceConfirmationTest is Test {
    uint256 private constant BUCKET = 1;
    uint64 private constant COOLDOWN = 12 hours;
    address private constant ZZZ = address(0xABCD);
    MockAccess private access;
    ConfirmationOracleFixture private oracle;
    ConfirmationPoolsFixture private pools;
    ConfirmationVenueFixture private venue;
    ZZZStrategy private strategy;
    ZZZRebalanceConfirmation private confirmation;
    ZZZMigrationBudget private budget;
    Position private position;
    bytes32 private pool;

    function setUp() public {
        vm.warp(1_000_000);
        access = new MockAccess(); ProtocolPolicyFixture.bind(address(access)); oracle = new ConfirmationOracleFixture(address(access));
        pools = new ConfirmationPoolsFixture(); venue = new ConfirmationVenueFixture();
        strategy = new ZZZStrategy(address(access), address(new ZZZPortfolioPolicy(address(access))), address(new ZZZRebalanceConfirmation(address(access)))); confirmation = strategy.rebalanceConfirmation();
        budget = new ZZZMigrationBudget(address(access));
        access.bind(Ids.VAULT,address(this)); access.bind(Ids.POOLS,address(pools));
        access.bind(Ids.LIQUIDITY,address(venue)); access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.STRATEGY,address(strategy)); access.setKeeper(address(this),true);
        PoolKey memory key = PoolKey(address(0),ZZZ,3000,60,address(0));
        pool = keccak256(abi.encode(key));
        pools.set(PoolConfig(key,true,true,2500,100,500,200,uint32(COOLDOWN),100 ether,1_000_000 ether));
        oracle.setPolicy(address(0),keccak256("test ETH two-source policy"));
        oracle.setPolicy(ZZZ,keccak256("test ZZZ two-source policy"));
        (int24 lower,int24 upper,) = strategy.target(pool);
        venue.setRange(lower,upper);
        position = Position(pool,1,0,0,100 ether,uint160(1<<96),uint64(block.timestamp)-COOLDOWN,PositionStatus.Active);
        access.seal();
        _below();
    }
    function group(uint256) external view returns(Position memory) { return position; }
    function migrationBudget() external view returns(address) { return address(budget); }
    function _below() private { _tick(venue.lower()-1); }
    function _above() private { _tick(venue.upper()); }
    function _inside() private { _tick(0); }
    function _tick(int24 tick) private {
        venue.setTick(tick); oracle.setReference(TickMath.getSqrtPriceAtTick(tick));
    }
    function _configure() private { confirmation.configure(600,300,keccak256("test-only cadence and latency review")); }
    /// @dev Find the last nontriggered tick adjacent to the lower85%threshold.
    /// This keeps physical/reference disagreement inside the price-deviation
    /// guard, rather than accidentally testing a completely different failure.
    function _insideLowerThreshold() private view returns(int24 high) {
        int24 low=venue.lower();high=0;
        while(high-low>1) {
            int24 middle=low+(high-low)/2;
            if(strategy.portfolioPolicy().thresholdSide(position.centerX96,venue.lower(),venue.upper(),
                TickMath.getSqrtPriceAtTick(middle))==1) low=middle;
            else high=middle;
        }
    }
    function _first() private view returns(uint64 value) { (,value,,) = confirmation.observations(BUCKET); }
    function _last() private view returns(uint64 value) { (,,value,) = confirmation.observations(BUCKET); }
    function _observeAfter(uint256 secondsLater) private returns(bool) { vm.warp(block.timestamp+secondsLater); return confirmation.observe(BUCKET); }

    function testFreshDefaultIsExplicitlyUnconfiguredAndCannotRebalance() public {
        assertEq(confirmation.duration(),600); assertEq(confirmation.maxObservationGap(),0);
        assertEq(confirmation.strategy(),address(strategy)); assertEq(address(confirmation.access()),address(access));
        assertEq(strategy.REBALANCE_CONFIRMATION_VERSION(),3); assertEq(budget.REBALANCE_CONFIRMATION_VERSION(),3);
        assertEq(confirmation.REBALANCE_CONFIRMATION_VERSION(),3); assertTrue(confirmation.requireReferenceExit());
        assertTrue(strategy.needsRebalance(BUCKET)); assertFalse(strategy.rebalanceReady(BUCKET));
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector); budget.validateRebalance(BUCKET,1);
    }
    function testExactTenMinuteBoundaryWithFiveMinuteObservations() public {
        _configure(); uint256 first=block.timestamp;
        assertFalse(confirmation.observe(BUCKET)); assertFalse(_observeAfter(300));
        vm.warp(first+599); assertFalse(strategy.rebalanceReady(BUCKET));
        vm.warp(first+600); assertTrue(strategy.rebalanceReady(BUCKET));
        assertTrue(confirmation.observe(BUCKET)); budget.validateRebalance(BUCKET,1);
        assertEq(_first(),first); assertEq(_last(),first+600);
    }
    function testTargetOnlyExitCannotStartOrKeepConfirmation() public {
        _configure(); confirmation.observe(BUCKET); uint64 first = _first();
        vm.warp(block.timestamp+240);
        oracle.setReference(TickMath.getSqrtPriceAtTick(_insideLowerThreshold()));
        (uint8 side,bytes32 identity,bool manual) = confirmation.condition(BUCKET);
        assertEq(side,0); assertEq(identity,bytes32(0)); assertFalse(manual);
        assertTrue(strategy.needsRebalance(BUCKET)); assertFalse(strategy.rebalanceReady(BUCKET));
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
        _below(); vm.warp(block.timestamp+1); confirmation.observe(BUCKET);
        assertGt(_first(),first);
    }
    function testReferenceOnlyExitCannotStartConfirmation() public {
        _configure(); venue.setTick(_insideLowerThreshold());
        oracle.setReference(TickMath.getSqrtPriceAtTick(venue.lower()-1));
        assertFalse(strategy.needsRebalance(BUCKET));
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
    }
    function testOppositeSideExitsCannotConfirmEvenWithinSpotTolerance() public {
        _configure(); PoolConfig memory c = pools.get(pool);
        c.rangeBps=100; c.triggerBps=50; pools.set(c);
        oracle.setReference(uint160(1<<96));
        (int24 lower,int24 upper,) = strategy.target(pool); venue.setRange(lower,upper);
        venue.setTick(lower-1); oracle.setReference(TickMath.getSqrtPriceAtTick(upper+1));
        assertTrue(strategy.needsRebalance(BUCKET));
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
    }
    function testReferenceMustStillAgreeAtExecutionRead() public {
        _configure(); confirmation.observe(BUCKET);
        _observeAfter(300); _observeAfter(300); assertTrue(_observeAfter(300));
        oracle.setReference(TickMath.getSqrtPriceAtTick(_insideLowerThreshold()));
        assertFalse(strategy.rebalanceReady(BUCKET));
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector); budget.validateRebalance(BUCKET,1);
    }
    function testGovernedRelaxationAndRestoreCannotReusePriorWindow() public {
        _configure(); confirmation.observe(BUCKET);
        _observeAfter(300); _observeAfter(300); assertTrue(_observeAfter(300));
        uint64 revision=confirmation.policyRevision();
        confirmation.setRequireReferenceExit(false,keccak256("reviewed recovery policy"));
        assertEq(confirmation.policyRevision(),revision+1); assertFalse(strategy.rebalanceReady(BUCKET));
        oracle.setReference(TickMath.getSqrtPriceAtTick(_insideLowerThreshold()));
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),block.timestamp);
        _observeAfter(300); _observeAfter(300); assertTrue(_observeAfter(300));
        confirmation.setRequireReferenceExit(true,keccak256("restored independent trigger"));
        assertFalse(strategy.rebalanceReady(BUCKET));
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
    }
    function testReferencePolicyRejectsUnreviewedAndUnauthorizedUpdates() public {
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        confirmation.setRequireReferenceExit(false,bytes32(0));
        access.setKeeper(address(0xBEEF),true); vm.prank(address(0xBEEF));
        vm.expectRevert(ZZZModule.Unauthorized.selector);
        confirmation.setRequireReferenceExit(false,keccak256("keeper cannot loosen policy"));
    }
    function testMaximumGapIsInclusiveAndOneSecondMoreRestarts() public {
        _configure(); confirmation.observe(BUCKET); uint256 original=block.timestamp;
        assertFalse(_observeAfter(300)); assertEq(_first(),original);
        assertFalse(_observeAfter(301)); assertEq(_first(),block.timestamp);
        assertFalse(strategy.rebalanceReady(BUCKET));
    }
    function testSingleOldSampleAndLateEndpointCannotQualify() public {
        confirmation.configure(600,300,keccak256("test maximum gap review"));
        confirmation.observe(BUCKET); uint256 first=block.timestamp;
        vm.warp(first+600); assertFalse(strategy.rebalanceReady(BUCKET));
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),first+600);
    }
    function testSameBlockRepeatsDoNotAdvanceTime() public {
        _configure(); confirmation.observe(BUCKET); uint64 first=_first();
        assertFalse(confirmation.observe(BUCKET)); assertFalse(confirmation.observe(BUCKET));
        assertEq(_first(),first); assertEq(_last(),first); assertFalse(strategy.rebalanceReady(BUCKET));
    }
    function testInsideObservationClearsAndLaterExitStartsFresh() public {
        _configure(); confirmation.observe(BUCKET); vm.warp(block.timestamp+300); _inside();
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
        _below(); vm.warp(block.timestamp+1); confirmation.observe(BUCKET);
        assertEq(_first(),block.timestamp); assertFalse(strategy.rebalanceReady(BUCKET));
    }
    function testOppositeExitSideRestarts() public {
        _configure(); confirmation.observe(BUCKET); vm.warp(block.timestamp+300); _above();
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),block.timestamp);
        (,,,uint8 side)=confirmation.observations(BUCKET); assertEq(side,2);
    }
    function testReplacementLPIdentityRestarts() public {
        _configure(); confirmation.observe(BUCKET); vm.warp(block.timestamp+300); ++position.lpTokenId;
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),block.timestamp);
    }
    function testContributionBalancesDoNotResetTheSamePhysicalWindow() public {
        _configure(); confirmation.observe(BUCKET); uint64 first=_first();
        position.depositUSD += 100 ether; position.idle0 += 2 ether; position.idle1 += 3 ether;
        vm.warp(block.timestamp+300); confirmation.observe(BUCKET);
        assertEq(_first(),first); assertEq(_last(),block.timestamp);
    }
    function testChangedAndRestoredRegistryPolicyRestarts() public {
        _configure(); confirmation.observe(BUCKET); vm.warp(block.timestamp+300);
        PoolConfig memory c=pools.get(pool); uint16 previous=c.maxSlippageBps;
        c.maxSlippageBps=300; pools.set(c); c.maxSlippageBps=previous; pools.set(c);
        confirmation.observe(BUCKET); assertEq(_first(),block.timestamp);
    }
    function testHealthyReferenceUpdatesDoNotResetStablePolicyWindow() public {
        _configure(); confirmation.observe(BUCKET); uint64 first=_first();
        vm.warp(block.timestamp+300); _tick(venue.lower()-2);
        confirmation.observe(BUCKET); assertEq(_first(),first); assertEq(_last(),block.timestamp);
    }
    function testNewOraclePolicyRestartsWithoutNormalRoundFingerprinting() public {
        _configure(); confirmation.observe(BUCKET); vm.warp(block.timestamp+300);
        oracle.setPolicy(ZZZ,keccak256("new reviewed policy"));
        confirmation.observe(BUCKET); assertEq(_first(),block.timestamp);
    }
    function testOrientationChangeAndRestoreInvalidatesPriorEvidence() public {
        _configure(); confirmation.observe(BUCKET); uint64 revision=confirmation.policyRevision();
        strategy.setRangeOrientation(pool,1); strategy.setRangeOrientation(pool,0);
        assertEq(confirmation.policyRevision(),revision+2);
        vm.warp(block.timestamp+300); confirmation.observe(BUCKET); assertEq(_first(),block.timestamp);
    }
    function testObservedPriceFailureClearsInSuccessfulTransaction() public {
        _configure(); confirmation.observe(BUCKET); oracle.setFailed(true);
        vm.expectRevert(); strategy.rebalanceReady(BUCKET);
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0); assertEq(_last(),0);
        oracle.setFailed(false); vm.warp(block.timestamp+1); confirmation.observe(BUCKET);
        assertEq(_first(),block.timestamp);
    }
    function test_FailedObservationTransactionDoesNotPretendItCleared() public {
        _configure(); confirmation.observe(BUCKET); uint64 first=_first();
        (bool success,)=address(confirmation).call{gas:1000}(abi.encodeCall(confirmation.observe,(BUCKET)));
        assertFalse(success); assertEq(_first(),first); assertEq(_last(),first);
    }
    function testUnauthorizedObserverCannotExtendOrClearEvidence() public {
        _configure(); confirmation.observe(BUCKET); uint64 first=_first();
        vm.prank(address(0xBAD)); vm.expectRevert(ZZZModule.Unauthorized.selector); confirmation.observe(BUCKET);
        vm.prank(address(0xBAD)); vm.expectRevert(ZZZModule.Unauthorized.selector); confirmation.resetObservation(BUCKET);
        vm.prank(address(0xBAD)); vm.expectRevert(ZZZModule.Unauthorized.selector);
        confirmation.configure(600,300,keccak256("unapproved caller"));
        vm.expectRevert(ZZZModule.Unauthorized.selector); confirmation.invalidatePolicy();
        assertEq(_first(),first);
    }
    function testKeeperCanClearDuringOrdinaryPauseWithoutExtending() public {
        _configure(); confirmation.observe(BUCKET); access.setPaused(true);
        assertFalse(strategy.rebalanceReady(BUCKET));
        confirmation.resetObservation(BUCKET); assertEq(_first(),0);
        vm.expectRevert(ZZZModule.Paused.selector); confirmation.observe(BUCKET);
    }
    function testPreparationAndCanonicalLocksFailClosed() public {
        _configure(); confirmation.observe(BUCKET); uint64 first=_first();
        access.setPreparation(true); assertFalse(strategy.rebalanceReady(BUCKET));
        vm.expectRevert(ZZZModule.Preparing.selector); confirmation.resetObservation(BUCKET);
        assertEq(_first(),first); access.setPreparation(false);
        access.setCanonicalState(2); assertFalse(strategy.rebalanceReady(BUCKET));
    }
    function testCollectiveExitPermanentlyBlocksObservationAndConfigurationMutation() public {
        _configure(); confirmation.observe(BUCKET); access.setPaused(true); access.startLPExit();
        assertFalse(strategy.rebalanceReady(BUCKET));
        vm.expectRevert(ZZZModule.LPExitLocked.selector); confirmation.resetObservation(BUCKET);
        vm.expectRevert(ZZZModule.LPExitLocked.selector);
        confirmation.configure(600,300,keccak256("cannot reopen retired LP"));
    }
    function testPostExitGovernanceOrientationCanChangeWithoutReopeningPrincipal() public {
        _configure(); confirmation.observe(BUCKET); access.setPaused(true); access.startLPExit();
        uint64 previous=confirmation.policyRevision();
        strategy.setRangeOrientation(pool,1);
        assertEq(strategy.rangeOrientation(pool),1); assertEq(confirmation.policyRevision(),previous+1);
        assertFalse(strategy.rebalanceReady(BUCKET));
        vm.expectRevert(ZZZModule.LPExitLocked.selector); confirmation.resetObservation(BUCKET);
        vm.expectRevert(ZZZModule.LPExitLocked.selector);
        confirmation.configure(600,300,keccak256("still cannot reopen retired LP"));
    }
    function testSamplesBeginDuringCooldownButCannotAuthorizeEarlyExecution() public {
        _configure(); position.lastRebalance=uint64(block.timestamp)-COOLDOWN+1;
        uint64 first=uint64(block.timestamp);
        assertFalse(strategy.needsRebalance(BUCKET)); assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),first);
        vm.warp(block.timestamp+1); assertTrue(strategy.needsRebalance(BUCKET));
        confirmation.observe(BUCKET); assertEq(_first(),first); assertFalse(strategy.rebalanceReady(BUCKET));
    }
    function testManualWidthExceptionPreservesRawCooldownAndPriceGuards() public {
        _inside(); PoolConfig memory c=pools.get(pool); c.rangeBps=5000; pools.set(c);
        position.lastRebalance=uint64(block.timestamp)-COOLDOWN+1;
        assertFalse(strategy.rebalanceReady(BUCKET)); vm.warp(block.timestamp+1);
        assertTrue(strategy.rebalanceReady(BUCKET)); budget.validateRebalance(BUCKET,1);
        oracle.setFailed(true); vm.expectRevert(); strategy.rebalanceReady(BUCKET);
    }
    function testPendingConfirmationDoesNotAllowCompoundToBypassRawPriority() public {
        _configure(); confirmation.observe(BUCKET);
        assertTrue(strategy.needsRebalance(BUCKET)); assertFalse(strategy.rebalanceReady(BUCKET));
        assertFalse(budget.compoundReady(BUCKET));
    }
    function testConfigurationBoundsAndExplicitStop() public {
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); confirmation.configure(59,0,keccak256("review"));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); confirmation.configure(604801,0,keccak256("review"));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); confirmation.configure(600,301,keccak256("review"));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); confirmation.configure(600,300,bytes32(0));
        _configure(); confirmation.observe(BUCKET);
        confirmation.configure(600,0,keccak256("explicit governed ordinary-rebalance stop"));
        assertFalse(strategy.rebalanceReady(BUCKET)); assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
    }
    function testBudgetSnapshotRejectsChangedAndRestoredConfirmationPolicy() public {
        _configure(); budget.checkpoint(BUCKET,0); budget.checkpoint(BUCKET,1);
        confirmation.configure(600,240,keccak256("reviewed temporary gap"));
        _configure();
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); budget.checkpoint(BUCKET,2);
    }
    function testBudgetSnapshotRejectsChangedAndRestoredRegistryControls() public {
        _configure(); budget.checkpoint(BUCKET,0); budget.checkpoint(BUCKET,1);
        PoolConfig memory c=pools.get(pool); uint16 previous=c.maxSlippageBps;
        c.maxSlippageBps=300; pools.set(c); c.maxSlippageBps=previous; pools.set(c);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); budget.checkpoint(BUCKET,2);
    }
    function testBudgetSnapshotRejectsChangedAndRestoredQualityControls() public {
        _configure(); budget.checkpoint(BUCKET,0); budget.checkpoint(BUCKET,1);
        strategy.setAdditionalLossBps(200,keccak256("temporary quality policy"));
        strategy.setAdditionalLossBps(100,keccak256("restored quality policy"));
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); budget.checkpoint(BUCKET,2);
    }
    function testBudgetSnapshotRejectsResetEvidenceAfterReadiness() public {
        _configure(); confirmation.observe(BUCKET);
        _observeAfter(300); _observeAfter(300); assertTrue(_observeAfter(300));
        budget.validateRebalance(BUCKET,1);
        budget.checkpoint(BUCKET,0); budget.checkpoint(BUCKET,1);
        confirmation.resetObservation(BUCKET);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector); budget.checkpoint(BUCKET,2);
    }
}
