// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {IStateViewMinimal} from "../src/interfaces/IZZZ.sol";
import {MockAccess} from "./mocks/Mocks.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

/// @dev TEST ONLY independent-price and venue adapters. No real feed, market,
/// routing, custody operation or operating qualification is claimed here.
contract PortfolioOracleFixture {
    uint160 public referencePrice = uint160(1 << 96);
    mapping(address => bytes32) public activePolicy;
    bytes32 public activeSequencerPolicy = keccak256("test sequencer");
    bool public failed;
    function setPolicy(address token,bytes32 value) external { activePolicy[token] = value; }
    function setReference(uint160 value) external { referencePrice = value; }
    function setFailed(bool value) external { failed = value; }
    function referenceX96(address,address) external view returns(uint160) { require(!failed,"test feed fault"); return referencePrice; }
}
contract PortfolioPoolsFixture {
    PoolConfig private config;
    uint64 public configurationRevision;
    bool public failed;
    function set(PoolConfig memory value) external { config = value; ++configurationRevision; }
    function setFailed(bool value) external { failed = value; }
    function get(bytes32) external view returns(PoolConfig memory) { return config; }
    function accounting(bytes32) external view returns(PoolConfig memory) { require(!failed,"test venue binding fault"); return config; }
}
contract PortfolioVenueFixture {
    PoolKey private key;
    int24 public lower;
    int24 public upper;
    uint160 public current = uint160(1 << 96);
    uint256 public auxiliary;
    uint128 public mainLiquidity = 1 ether;
    address public owner;
    bool public fingerprintFault;
    function initialize(PoolKey memory k,address recipient,int24 lo,int24 hi) external { key=k;owner=recipient;lower=lo;upper=hi; }
    function setCurrent(uint160 value) external { current = value; }
    function setAuxiliary(uint256 value) external { auxiliary = value; }
    function setLiquidity(uint128 value) external { mainLiquidity = value; }
    function setOwner(address value) external { owner = value; }
    function setFingerprintFault(bool value) external { fingerprintFault = value; }
    function ticks(uint256 id) external view returns(int24,int24) {
        return id == 1 ? (lower,upper) : (upper,upper+key.tickSpacing);
    }
    function spot(bytes32) external view returns(uint160) { return current; }
    function stateView() external view returns(IStateViewMinimal) { return IStateViewMinimal(address(this)); }
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24) {
        return(current,TickMath.getTickAtSqrtPrice(current),0,key.fee);
    }
    function positionManager() external view returns(address) { return address(this); }
    function secondaryId(uint256) external view returns(uint256) { return auxiliary; }
    function portfolioFingerprint(uint256 main) external view returns(bytes32) {
        require(!fingerprintFault,"test physical fault");
        // Actual production Manager authenticates both owners/keys/ranges here;
        // mutable liquidity is deliberately excluded from confirmation identity.
        return keccak256(abi.encode(main,auxiliary,lower,upper,owner));
    }
    function ownerOf(uint256) external view returns(address) { return owner; }
    function getPositionLiquidity(uint256 id) external view returns(uint128) { return id == 1 ? mainLiquidity : 1 ether; }
    function getPoolAndPositionInfo(uint256 id) external view returns(PoolKey memory,uint256) {
        int24 lo = id == 1 ? lower : upper;
        int24 hi = id == 1 ? upper : upper+key.tickSpacing;
        return(key,uint256(uint24(lo)) << 8 | uint256(uint24(hi)) << 32);
    }
    function record(ZZZPortfolioPolicy policy,uint256 main,bytes32 pool) external { policy.recordApplied(main,pool); }
}

contract PortfolioPolicyTest is Test {
    address private constant ZZZ = address(0xABCD);
    uint256 private constant BUCKET = 1;
    uint64 private constant COOLDOWN = 12 hours;
    uint160 private constant Q96 = uint160(1 << 96);
    MockAccess private access;
    PortfolioOracleFixture private oracle;
    PortfolioPoolsFixture private pools;
    PortfolioVenueFixture private venue;
    ZZZStrategy private strategy;
    ZZZPortfolioPolicy private policy;
    ZZZProtocolPolicy private protocol;
    ZZZRebalanceConfirmation private confirmation;
    Position private position;
    bytes32 private pool;

    function setUp() public {
        vm.warp(1_000_000);
        access = new MockAccess();protocol=ProtocolPolicyFixture.bind(address(access));oracle = new PortfolioOracleFixture();
        pools = new PortfolioPoolsFixture(); venue = new PortfolioVenueFixture();
        policy = new ZZZPortfolioPolicy(address(access)); confirmation = new ZZZRebalanceConfirmation(address(access));
        strategy = new ZZZStrategy(address(access),address(policy),address(confirmation));
        access.bind(Ids.VAULT,address(this)); access.bind(Ids.POOLS,address(pools));
        access.bind(Ids.LIQUIDITY,address(venue)); access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.STRATEGY,address(strategy)); access.setKeeper(address(this),true);
        PoolKey memory key = PoolKey(address(0),ZZZ,3000,60,address(0));
        pool = keccak256(abi.encode(key));
        pools.set(PoolConfig(key,true,true,5000,100,500,200,uint32(COOLDOWN),100 ether,1_000_000 ether));
        oracle.setPolicy(address(0),keccak256("test ETH")); oracle.setPolicy(ZZZ,keccak256("test ZZZ"));
        strategy.setRangeOrientation(pool,1);
        (int24 lower,int24 upper,) = strategy.target(pool);
        venue.initialize(key,address(this),lower,upper);
        position = Position(pool,1,0,0,100 ether,Q96,uint64(block.timestamp),PositionStatus.Active);
        access.seal(); venue.record(policy,1,pool);
    }
    function group(uint256) external view returns(Position memory) { return position; }
    function _price(uint256 numerator,uint256 denominator) private pure returns(uint160) {
        return uint160(Math.sqrt(Math.mulDiv(uint256(Q96)*Q96,denominator,numerator)));
    }
    function _market(uint256 numerator,uint256 denominator) private {
        uint160 price = _price(numerator,denominator);
        venue.setCurrent(price); oracle.setReference(price);
    }
    function _due() private { position.lastRebalance = uint64(block.timestamp)-COOLDOWN; }
    function _configure() private { confirmation.configure(600,300,keccak256("test cadence review")); }
    function _enable() private {
        policy.setMode(pool,true,keccak256("test two leg review"));
    }
    function _first() private view returns(uint64 first) { (,first,,) = confirmation.observations(BUCKET); }

    function testFreshVersionsDefaultsAndUnconfiguredConfirmation() public view {
        assertEq(strategy.MAINTENANCE_POLICY_VERSION(),3);
        assertEq(strategy.REBALANCE_CONFIRMATION_VERSION(),3);
        assertEq(confirmation.REBALANCE_CONFIRMATION_VERSION(),3);
        assertEq(policy.PORTFOLIO_VERSION(),2); assertEq(policy.strategy(),address(strategy));
        assertEq(policy.thresholdBps(),8500); assertEq(policy.minimumMainBps(pool),6000); assertEq(policy.maximumResidualBps(pool),4000);
        assertEq(policy.residualGapSpacings(pool),1);
        assertFalse(policy.enabled(pool)); assertEq(policy.residualSideBps(pool),5000);
        assertEq(policy.DEFAULT_RESIDUAL_SIDE_BPS(),5000);
        assertEq(confirmation.duration(),600); assertEq(confirmation.maxObservationGap(),0);
    }
    function testEightyFivePercentPriceDistanceTriggersInsideBothPhysicalEdges() public {
        _market(140,100); (uint8 side,bool manual) = strategy.rebalanceCondition(BUCKET);
        assertEq(side,0); assertFalse(manual);
        _market(144,100); (side,manual) = strategy.rebalanceCondition(BUCKET);
        assertEq(side,1); assertFalse(manual);
        uint160 price = venue.current();
        assertGt(price,TickMath.getSqrtPriceAtTick(venue.lower()));
        _market(60,100); (side,) = strategy.rebalanceCondition(BUCKET); assertEq(side,0);
        _market(56,100); (side,) = strategy.rebalanceCondition(BUCKET); assertEq(side,2);
        assertLt(venue.current(),TickMath.getSqrtPriceAtTick(venue.upper()));
    }
    function testActualRoundedBoundsAndInversePriceDoNotUseTickPercentage() public view {
        int24 lower = venue.lower(); int24 upper = venue.upper();
        // At the actual bounds both sides always qualify; the centre never does.
        assertEq(policy.thresholdSide(Q96,lower,upper,TickMath.getSqrtPriceAtTick(lower)),1);
        assertEq(policy.thresholdSide(Q96,lower,upper,TickMath.getSqrtPriceAtTick(upper)),2);
        assertEq(policy.thresholdSide(Q96,lower,upper,Q96),0);
        //85%of sqrt/tick distance is materially different: a41%price move is
        // below the requested85%of the approximately50%actual price boundary.
        assertEq(policy.thresholdSide(Q96,lower,upper,_price(141,100)),0);
    }
    function testIndependentDecimalThresholdFixturesOnBothSides() public view {
        // Independently generated at100decimal digits from1.0001^tick, not the
        // Solidity fixed-point implementation. For[-4080,6960], actual ZZZ/ETH
        // bounds are[.498592972568...,1.503776485861...]. The85%thresholds are
        // .573804026682...and1.428210012982...; samples differ by1e-10 in price.
        assertEq(policy.thresholdSide(Q96,-4080,6960,66295423154005916862571018134),0);
        assertEq(policy.thresholdSide(Q96,-4080,6960,66295423149364062895083722748),1);
        assertEq(policy.thresholdSide(Q96,-4080,6960,104591836303361924396657038834),0);
        assertEq(policy.thresholdSide(Q96,-4080,6960,104591836321589721945779390678),2);
    }
    function testThresholdGeometryScalesNearBothTickExtremes() public view {
        int24 lowCenter = TickMath.MIN_TICK+10000;
        int24 highCenter = TickMath.MAX_TICK-10000;
        uint160 low = TickMath.getSqrtPriceAtTick(lowCenter);
        uint160 high = TickMath.getSqrtPriceAtTick(highCenter);
        assertEq(policy.thresholdSide(low,lowCenter-1000,lowCenter+1000,low),0);
        assertEq(policy.thresholdSide(high,highCenter-1000,highCenter+1000,high),0);
        assertEq(policy.thresholdSide(low,lowCenter-1000,lowCenter+1000,TickMath.getSqrtPriceAtTick(lowCenter-999)),1);
        assertEq(policy.thresholdSide(high,highCenter-1000,highCenter+1000,TickMath.getSqrtPriceAtTick(highCenter+999)),2);
    }
    function testSamplesAccumulateDuringCooldownWithoutGrantingReadiness() public {
        _configure(); _market(144,100);
        (uint8 side,,bool manual) = confirmation.condition(BUCKET);
        assertEq(side,1); assertFalse(manual); assertFalse(strategy.needsRebalance(BUCKET));
        uint256 first = block.timestamp;
        assertFalse(confirmation.observe(BUCKET)); vm.warp(first+240); assertFalse(confirmation.observe(BUCKET));
        vm.warp(first+480); assertFalse(confirmation.observe(BUCKET));
        vm.warp(first+600); assertFalse(confirmation.observe(BUCKET));
        assertEq(_first(),first); assertFalse(strategy.rebalanceReady(BUCKET));
    }
    function testTenMinuteMaturityAndCooldownMustBothHold() public {
        _configure(); _market(144,100); position.lastRebalance = uint64(block.timestamp)-COOLDOWN+600;
        uint256 first = block.timestamp;
        confirmation.observe(BUCKET); vm.warp(first+240); confirmation.observe(BUCKET);
        vm.warp(first+480); confirmation.observe(BUCKET);
        vm.warp(first+599); assertFalse(strategy.rebalanceReady(BUCKET));
        vm.warp(first+600); assertTrue(strategy.rebalanceReady(BUCKET)); assertTrue(confirmation.observe(BUCKET));
    }
    function testModePendingIsVisibleDuringCooldownButCannotExecute() public {
        _enable();
        assertTrue(policy.configurationPending(BUCKET));
        (uint8 side,,bool manual) = confirmation.condition(BUCKET);
        assertEq(side,0); assertTrue(manual); assertFalse(strategy.rebalanceReady(BUCKET));
        assertFalse(confirmation.observe(BUCKET)); _due(); assertTrue(strategy.rebalanceReady(BUCKET));
    }
    function testTriggerChangeInvalidatesSamplesWithoutManualModeException() public {
        _configure(); _due(); _market(144,100); confirmation.observe(BUCKET);
        (,bytes32 beforeIdentity,) = confirmation.condition(BUCKET);
        policy.setTriggerBps(8400,keccak256("test trigger review"));
        (,bytes32 afterIdentity,bool manual) = confirmation.condition(BUCKET);
        assertTrue(beforeIdentity != afterIdentity); assertFalse(manual); assertFalse(policy.configurationPending(BUCKET));
        assertFalse(strategy.rebalanceReady(BUCKET));
        vm.warp(block.timestamp+1); confirmation.observe(BUCKET); assertEq(_first(),block.timestamp);
    }
    function testReferenceMustCrossTheSameInsideRangeThreshold() public {
        _configure(); _due(); _market(144,100); confirmation.observe(BUCKET);
        oracle.setReference(_price(140,100));
        (uint8 side,,bool manual) = confirmation.condition(BUCKET);
        assertEq(side,0); assertFalse(manual); assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
        _market(140,100); oracle.setReference(_price(144,100));
        (side,,) = confirmation.condition(BUCKET); assertEq(side,0);
    }
    function testGapStrictlyGreaterThanFiveMinutesRestartsWindow() public {
        _configure(); _due(); _market(144,100); confirmation.observe(BUCKET);
        uint64 old = _first(); vm.warp(block.timestamp+301); confirmation.observe(BUCKET);
        assertGt(_first(),old); assertEq(_first(),block.timestamp);
    }
    function testReturningInsideAndChangingSidesRestartEvidence() public {
        _configure(); _due(); _market(144,100); confirmation.observe(BUCKET);
        uint64 first = _first(); vm.warp(block.timestamp+240); _market(140,100);
        assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
        vm.warp(block.timestamp+1); _market(144,100); confirmation.observe(BUCKET);
        assertGt(_first(),first); first = _first();
        vm.warp(block.timestamp+240); _market(56,100); confirmation.observe(BUCKET);
        assertGt(_first(),first); (,,,uint8 side) = confirmation.observations(BUCKET); assertEq(side,2);
    }
    function testChangingAndRestoringPolicyCannotRestoreOldSamples() public {
        _configure(); _due(); _market(144,100); confirmation.observe(BUCKET);
        uint64 first = _first();
        policy.setTriggerBps(8400,keccak256("test changed"));
        policy.setTriggerBps(8500,keccak256("test restored"));
        vm.warp(block.timestamp+1); confirmation.observe(BUCKET); assertGt(_first(),first);
    }
    function testAuxiliaryIdentityResetsButNormalLiquidityIncreaseDoesNot() public {
        _configure(); _due(); _market(144,100); confirmation.observe(BUCKET);
        uint64 first = _first(); vm.warp(block.timestamp+240);
        venue.setLiquidity(2 ether); confirmation.observe(BUCKET); assertEq(_first(),first);
        venue.setAuxiliary(2); vm.warp(block.timestamp+1); confirmation.observe(BUCKET);
        assertEq(_first(),block.timestamp); assertGt(_first(),first);
    }
    function testPhysicalReadFaultClearsEvidenceWithoutReverting() public {
        _configure(); _due(); _market(144,100); confirmation.observe(BUCKET);
        venue.setFingerprintFault(true); assertFalse(confirmation.observe(BUCKET)); assertEq(_first(),0);
    }
    function testRecordedGeometryValidatesActualVaultOwnershipAndDistinctLegs() public {
        _enable(); venue.setAuxiliary(2); venue.record(policy,1,pool);
        assertEq(policy.appliedRevision(1),policy.geometryRevision(pool)); assertFalse(policy.configurationPending(BUCKET));
        venue.setAuxiliary(1); vm.expectRevert(ZZZModule.InvalidState.selector); venue.record(policy,1,pool);
        venue.setAuxiliary(2); venue.setOwner(address(0xBAD));
        vm.expectRevert(ZZZModule.InvalidState.selector); venue.record(policy,1,pool);
    }
    function testOnlyCurrentSealedManagerCanRecordAppliedGeometry() public {
        vm.expectRevert(ZZZModule.Unauthorized.selector); policy.recordApplied(1,pool);
        access.beginBootstrap(); vm.expectRevert(ZZZModule.Unauthorized.selector); venue.record(policy,1,pool);
    }
    function testDisablingRecordsPendingMergeAndCannotDiscardAuxiliary() public {
        _enable(); venue.setAuxiliary(2); venue.record(policy,1,pool);
        policy.setMode(pool,false,keccak256("test disable")); assertTrue(policy.configurationPending(BUCKET));
        vm.expectRevert(ZZZModule.InvalidState.selector); venue.record(policy,1,pool);
        //TEST ONLY emulate the Manager's later atomic all-leg close/single mint.
        venue.setAuxiliary(0); venue.record(policy,1,pool); assertFalse(policy.configurationPending(BUCKET));
    }
    function testDisablingDesiredModeDoesNotRequireHealthyVenueDependencies() public {
        _enable(); venue.record(policy,1,pool); pools.setFailed(true);
        policy.setMode(pool,false,keccak256("test emergency desired disable"));
        assertFalse(policy.enabled(pool)); assertTrue(policy.configurationPending(BUCKET));
    }
    function testTriggerBoundsAuthorizationAndTerminalLock() public {
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); policy.setTriggerBps(0,keccak256("test"));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); policy.setTriggerBps(10001,keccak256("test"));
        vm.prank(address(0xBAD)); vm.expectRevert(ZZZModule.Unauthorized.selector); policy.setTriggerBps(9000,keccak256("test"));
        access.setPaused(true); access.startLPExit();
        vm.expectRevert(ZZZModule.LPExitLocked.selector); policy.setMode(pool,true,keccak256("test"));
    }
    function testInvalidCentreFailsThresholdButDeliberateRepairRetainsGuards() public {
        int24 lower=venue.lower();int24 upper=venue.upper();
        uint160 invalidCenter=TickMath.getSqrtPriceAtTick(lower);
        vm.expectRevert(ZZZModule.InvalidState.selector);
        policy.thresholdSide(invalidCenter,lower,upper,Q96);
        position.centerX96 = TickMath.getSqrtPriceAtTick(upper); _due();
        (uint8 side,bool manual) = strategy.rebalanceCondition(BUCKET);
        assertEq(side,0); assertTrue(manual); assertTrue(strategy.needsRebalance(BUCKET));
    }
    function testModeCanEnableWithApprovedHalfSideDefaultAndRejectsInvalidGeometry() public {
        policy.setMode(pool,true,keccak256("test reviewed enable using approved default"));
        assertTrue(policy.enabled(pool)); assertEq(policy.residualSideBps(pool),5000);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); policy.configureResidualSide(pool,0,keccak256("test"));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); policy.configureResidualSide(pool,10001,keccak256("test"));
    }
    function testConfiguringUnusedResidualGeometryDoesNotForceSinglePositionTrade() public {
        policy.configureResidualSide(pool,5000,keccak256("test future geometry"));
        assertGt(policy.revision(),0); assertEq(policy.geometryRevision(pool),0);
        assertFalse(policy.configurationPending(BUCKET));
        (uint8 side,bool manual) = strategy.rebalanceCondition(BUCKET);
        assertEq(side,0); assertFalse(manual);
    }
    function testFullResidualUsesCorrectSideWithinMainAndLeavesFullTickGap() public {
        policy.configureResidualSide(pool,10000,keccak256("test explicit full-side override"));
        _enable();
        (int24 lower0,int24 upper0) = policy.residualRange(pool,Q96,venue.lower(),venue.upper(),true);
        (int24 lower1,int24 upper1) = policy.residualRange(pool,Q96,venue.lower(),venue.upper(),false);
        assertEq(lower0,120); assertEq(upper0,venue.upper());
        assertEq(lower1,venue.lower()); assertEq(upper1,-60);
        assertGt(TickMath.getSqrtPriceAtTick(lower0),Q96);
        assertLt(TickMath.getSqrtPriceAtTick(upper1),Q96);
        // At a nonaligned current tick59, nearest token0 edge120 is still at
        // least61ticks beyond spot, rather than the1tick gap to aligned60.
        uint160 nonaligned = TickMath.getSqrtPriceAtTick(59);
        (lower0,) = policy.residualRange(pool,nonaligned,venue.lower(),venue.upper(),true);
        (,upper1) = policy.residualRange(pool,nonaligned,venue.lower(),venue.upper(),false);
        assertEq(lower0,120); assertEq(upper1,-60);
    }
    function testHalfSideMeansHalfPriceExtentNotHalfTicksOrFullWidth() public {
        _enable(); policy.configureResidualSide(pool,5000,keccak256("test half-side review"));
        (int24 lower0,int24 upper0) = policy.residualRange(pool,Q96,venue.lower(),venue.upper(),true);
        (int24 lower1,int24 upper1) = policy.residualRange(pool,Q96,venue.lower(),venue.upper(),false);
        assertEq(lower0,120); assertEq(upper1,-60);
        // Lower ZZZ-price boundary~.4986: half-side target~.7493(raw sqrt up).
        // Upper boundary~1.5038: half-side target~1.2519(raw sqrt down).
        assertGt(upper0,2000); assertLt(upper0,4000);
        assertGt(lower1,-3000); assertLt(lower1,-1000);
        assertGt(lower1,venue.lower()); assertLt(upper0,venue.upper());
        assertTrue(policy.configurationPending(BUCKET));
    }
    function testResidualFailsRatherThanCrossSpotOrInventWidth() public {
        _enable();
        int24 lower=venue.lower();int24 upper=venue.upper();
        uint160 nearUpper=TickMath.getSqrtPriceAtTick(upper-1);
        vm.expectRevert(ZZZModule.InvalidState.selector);
        policy.residualRange(pool,nearUpper,lower,upper,true);
        policy.configureResidualSide(pool,1,keccak256("test unrepresentable narrow extent"));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        policy.residualRange(pool,Q96,lower,upper,false);
    }
    function testGovernedAllocationPreservesEnvelopeAndPendingGeometrySemantics() public {
        policy.configureMainAllocation(pool,7500,keccak256("test higher main floor"));
        assertEq(policy.minimumMainBps(pool),7500);assertEq(policy.maximumResidualBps(pool),2500);
        assertFalse(policy.configurationPending(BUCKET));_enable();venue.record(policy,1,pool);
        policy.configureMainAllocation(pool,8000,keccak256("test80/20"));assertTrue(policy.configurationPending(BUCKET));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.configureMainAllocation(pool,5999,keccak256("test"));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.configureMainAllocation(pool,10000,keccak256("test"));
        policy.configureMainAllocation(pool,9999,keccak256("test strict operator policy"));
        assertEq(policy.maximumResidualBps(pool),1);
    }
    function testLargerGapKeepsBothResidualSidesOneSidedAndInsideMain() public {
        _enable();policy.configureResidualGap(pool,3,keccak256("test larger tick spacing gap"));
        (int24 lower0,int24 upper0)=policy.residualRange(pool,Q96,venue.lower(),venue.upper(),true);
        (int24 lower1,int24 upper1)=policy.residualRange(pool,Q96,venue.lower(),venue.upper(),false);
        assertEq(lower0,240);assertEq(upper1,-180);
        assertLt(TickMath.getSqrtPriceAtTick(upper1),Q96);assertGt(TickMath.getSqrtPriceAtTick(lower0),Q96);
        assertGe(lower1,venue.lower());assertLe(upper0,venue.upper());assertTrue(policy.configurationPending(BUCKET));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.configureResidualGap(pool,0,keccak256("test"));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.configureResidualGap(pool,30000,keccak256("test"));
        policy.configureResidualGap(pool,1000,keccak256("test valid domain but too wide for current main"));
        int24 mainLower=venue.lower();int24 mainUpper=venue.upper();
        vm.expectRevert(ZZZModule.InvalidState.selector);policy.residualRange(pool,Q96,mainLower,mainUpper,true);
    }
    function testScopedPolicyChangesResetOnlyRelevantSamplesAndNeverCreateCosmeticTrade() public {
        _configure();_due();_market(144,100);confirmation.observe(BUCKET);
        (,bytes32 beforeIdentity,)=confirmation.condition(BUCKET);uint64 first=_first();
        protocol.setMintPrice(uint128(0.04 ether),keccak256("test sale only"));
        protocol.setEvolutionThresholds(2000e18,20000e18,keccak256("test cosmetics only"));
        protocol.setGasPolicy(200000,600000,300000,keccak256("test gas only"));
        protocol.setEntryPolicy(150e18,5e18,1000,keccak256("test entrant only"));
        (,bytes32 unchanged,bool manual)=confirmation.condition(BUCKET);assertEq(unchanged,beforeIdentity);assertFalse(manual);
        vm.warp(block.timestamp+240);confirmation.observe(BUCKET);assertEq(_first(),first);
        protocol.setMaintenancePolicy(1000,keccak256("test maintenance financial change"));
        (,bytes32 changed,)=confirmation.condition(BUCKET);assertTrue(changed!=beforeIdentity);assertFalse(policy.configurationPending(BUCKET));
        vm.warp(block.timestamp+1);confirmation.observe(BUCKET);assertEq(_first(),block.timestamp);
    }
    function testUnrelatedPoolGeometryKeepsOtherPoolControlFingerprintStable() public {
        _configure();_due();_market(144,100);confirmation.observe(BUCKET);
        (,bytes32 beforeIdentity,)=confirmation.condition(BUCKET);PoolConfig memory original=pools.get(pool);
        PoolConfig memory other=abi.decode(abi.encode(original),(PoolConfig));other.key.fee=5000;bytes32 otherId=keccak256(abi.encode(other.key));
        pools.set(other);policy.configureMainAllocation(otherId,7000,keccak256("test unrelated pool"));
        pools.set(original);
        // The fixture's registry global revision changed in this setup; direct
        // policy scope, not that deliberately global registry identity, is checked.
        bytes32 first=policy.controlFingerprint(pool);
        pools.set(other);policy.configureResidualGap(otherId,2,keccak256("test other gap"));pools.set(original);
        assertEq(policy.controlFingerprint(pool),first);assertTrue(beforeIdentity!=bytes32(0));
    }
    function testBroaderManualRangeUsesStrictlyPositivePriceBoundsAndTickMathLimits() public view {
        PoolConfig memory c=pools.get(pool);c.rangeBps=9999;
        (int24 lower,int24 upper)=policy.range(c,Q96,1);
        assertLt(lower,0);assertGt(upper,0);assertGe(lower,TickMath.MIN_TICK);assertLe(upper,TickMath.MAX_TICK);
    }
}
