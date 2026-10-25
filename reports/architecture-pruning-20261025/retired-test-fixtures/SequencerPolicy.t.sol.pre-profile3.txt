// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {Test} from "forge-std/Test.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockFeed, MockToken, BoundDummy} from "./mocks/Mocks.sol";

contract RecoverableUptimeFeed {
    uint8 public constant decimals = 0;
    bool public fail;
    uint256 public started;
    constructor(uint256 start) { started = start; }
    function setFail(bool state) external { fail = state; }
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        require(!fail, "retired uptime source");
        return (1, 0, started, started, 1);
    }
}

contract SequencerPolicyTest is Test {
    MockAccess access;
    MockToken token;
    MockFeed usd;
    MockFeed sequencer;
    ZZZOracle oracle;
    bytes32 constant REVIEW = keccak256("reviewed deployment and uptime semantics");

    function setUp() public {
        vm.warp(1_000_000);
        access = new MockAccess();
        token = new MockToken(18);
        usd = new MockFeed(8, 2e8);
        sequencer = new MockFeed(0, 0);
        sequencer.set(0, block.timestamp - 2 hours, block.timestamp - 2 hours);
        oracle = new ZZZOracle(address(access), address(sequencer));
        oracle.setTestFeed(address(token), address(usd), 1 days);
    }

    function _replace(MockFeed source) private returns (bytes32) {
        return oracle.setSequencerFeed(address(source), address(source).codehash, REVIEW);
    }
    function _healthy() private returns (MockFeed source) {
        source = new MockFeed(0, 0);
        source.set(0, block.timestamp - 2 hours, block.timestamp - 2 hours);
    }
    function testOptionalConstructorZeroHasNoPolicyUntilConfigured() public {
        ZZZOracle noSource = new ZZZOracle(address(access), address(0));
        noSource.setTestFeed(address(token), address(usd), 1 days);
        assertEq(noSource.sequencerFeed(), address(0));
        assertEq(noSource.sequencerPolicyCount(), 0);
        assertEq(noSource.price(address(token)), 2e18);
        noSource.setSequencerFeed(address(sequencer), address(sequencer).codehash, REVIEW);
        vm.expectRevert();
        noSource.setSequencerFeed(address(0), bytes32(0), REVIEW);
        assertEq(noSource.sequencerFeed(), address(sequencer));
    }
    function testConstructorAdmissionRetainsExplicitProvenance() public view {
        bytes32 id = oracle.sequencerPolicyAt(0);
        assertEq(id, oracle.activeSequencerPolicy());
        (address source, bytes32 pin, bytes32 review, bool bootstrap) = oracle.sequencerPolicies(id);
        assertEq(source, address(sequencer));
        assertEq(pin, address(sequencer).codehash);
        assertTrue(review != bytes32(0));
        assertTrue(bootstrap);
    }
    function testUnauthorizedReplacementRejected() public {
        MockFeed next = _healthy();
        vm.prank(address(0xBAD));
        vm.expectRevert();
        oracle.setSequencerFeed(address(next), address(next).codehash, REVIEW);
        assertEq(oracle.sequencerFeed(), address(sequencer));
    }
    function testZeroSourceReviewAndCodePinsRejected() public {
        vm.expectRevert(); oracle.setSequencerFeed(address(0), bytes32(0), REVIEW);
        vm.expectRevert(); oracle.setSequencerFeed(address(sequencer), address(sequencer).codehash, bytes32(0));
        vm.expectRevert(); oracle.setSequencerFeed(address(sequencer), bytes32(0), REVIEW);
        vm.expectRevert(); oracle.setSequencerFeed(address(sequencer), keccak256("wrong runtime"), REVIEW);
        vm.expectRevert(); oracle.setSequencerFeed(address(0xABC), address(0xABC).codehash, REVIEW);
        assertEq(oracle.sequencerPolicyCount(), 1);
    }
    function testPoliciesAppendEvenWhenParametersRepeat() public {
        bytes32 original = oracle.activeSequencerPolicy();
        bytes32 second = _replace(sequencer);
        bytes32 third = _replace(sequencer);
        assertTrue(second != third);
        assertEq(oracle.sequencerPolicyCount(), 3);
        assertEq(oracle.sequencerPolicyAt(0), original);
        assertEq(oracle.sequencerPolicyAt(1), second);
        assertEq(oracle.sequencerPolicyAt(2), third);
        (address source, bytes32 pin, bytes32 review, bool bootstrap) = oracle.sequencerPolicies(second);
        assertEq(source, address(sequencer)); assertEq(pin, address(sequencer).codehash);
        assertEq(review, REVIEW); assertFalse(bootstrap);
    }
    function testDownReplacementDoesNotBypassUptimeGuard() public {
        MockFeed next = new MockFeed(0, 1);
        _replace(next);
        vm.expectRevert(); oracle.price(address(token));
        next.set(0, block.timestamp, block.timestamp);
        vm.expectRevert(); oracle.price(address(token));
        vm.warp(block.timestamp + 1 hours);
        vm.expectRevert(); oracle.price(address(token));
        vm.warp(block.timestamp + 1);
        assertEq(oracle.price(address(token)), 2e18);
    }
    function testFutureOrZeroStartedAndMalformedRoundsRejected() public {
        sequencer.set(0, block.timestamp + 1, block.timestamp + 1);
        vm.expectRevert(); oracle.price(address(token));
        vm.expectRevert(); _replace(sequencer);
        sequencer.set(0, 0, block.timestamp);
        vm.expectRevert(); _replace(sequencer);
        sequencer.set(0, block.timestamp - 2 hours, block.timestamp - 2 hours);
        sequencer.rounds(0, 0);
        vm.expectRevert(); _replace(sequencer);
        sequencer.rounds(2, 1);
        vm.expectRevert(); oracle.price(address(token));
    }
    function testNonbinaryStatusBadTimestampsAndDecimalsRejected() public {
        sequencer.set(2, block.timestamp - 2 hours, block.timestamp - 2 hours);
        vm.expectRevert(); _replace(sequencer);
        sequencer.set(0, block.timestamp - 2 hours, block.timestamp - 3 hours);
        vm.expectRevert(); _replace(sequencer);
        sequencer.set(0, block.timestamp - 2 hours, block.timestamp + 1);
        vm.expectRevert(); _replace(sequencer);
        MockFeed priceFeed = new MockFeed(8, 0);
        vm.expectRevert(); _replace(priceFeed);
        vm.expectRevert(); new ZZZOracle(address(access), address(priceFeed));
    }
    function testHealthyUnchangingUptimeDoesNotBecomeStale() public {
        vm.warp(block.timestamp + 365 days);
        usd.set(2e8, block.timestamp, block.timestamp);
        assertEq(oracle.price(address(token)), 2e18);
    }
    function testRuntimeMutationFailsClosedAndReviewedReplacementRecovers() public {
        vm.etch(address(sequencer), hex"00");
        vm.expectRevert(); oracle.price(address(token));
        MockFeed next = _healthy();
        _replace(next);
        assertEq(oracle.price(address(token)), 2e18);
    }
    function testRevertingOldDependencyDoesNotBlockRecovery() public {
        RecoverableUptimeFeed oldSource = new RecoverableUptimeFeed(block.timestamp - 2 hours);
        oracle.setSequencerFeed(address(oldSource), address(oldSource).codehash, REVIEW);
        oldSource.setFail(true);
        vm.expectRevert(); oracle.price(address(token));
        _replace(_healthy());
        assertEq(oracle.price(address(token)), 2e18);
    }
    function testActualSealedTimelockControlsReplacementAndCannotDisable() public {
        address[] memory actors = new address[](1); actors[0] = address(this);
        ZZZAccessController controller = new ZZZAccessController(0, actors, actors, address(0x111), address(0x222));
        RecoverableUptimeFeed oldSource = new RecoverableUptimeFeed(block.timestamp - 2 hours);
        ZZZOracle governed = new ZZZOracle(address(controller), address(oldSource));
        governed.setTestFeed(address(token), address(usd), 1 days);
        // Retired transport slots cannot be rebound in the custody-handoff
        // layout. CanonicalFixture supplies the four required companions.
        bytes32[12] memory ids = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP,
            Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION,
            Ids.ORACLE, Ids.POOLS];
        for (uint256 i; i < ids.length; ++i) {
            controller.bind(ids[i], ids[i] == Ids.ORACLE ? address(governed) : address(new BoundDummy(address(controller))));
        }
        CanonicalFixture.bind(address(controller));
        controller.seal();
        oldSource.setFail(true);
        MockFeed next = _healthy();
        vm.expectRevert(); governed.setSequencerFeed(address(next), address(next).codehash, REVIEW);
        bytes memory data = abi.encodeCall(governed.setSequencerFeed, (address(next), address(next).codehash, REVIEW));
        bytes32 salt = keccak256("replace retired sequencer");
        controller.schedule(address(governed), 0, data, bytes32(0), salt, 0);
        controller.execute(address(governed), 0, data, bytes32(0), salt);
        usd.set(2e8, block.timestamp, block.timestamp);
        assertEq(governed.price(address(token)), 2e18);
        assertEq(governed.sequencerFeed(), address(next));
        data = abi.encodeCall(governed.setSequencerFeed, (address(0), bytes32(0), REVIEW));
        salt = keccak256("cannot disable safety");
        controller.schedule(address(governed), 0, data, bytes32(0), salt, 0);
        vm.warp(block.timestamp + 1 days);
        vm.expectRevert(); controller.execute(address(governed), 0, data, bytes32(0), salt);
        assertEq(governed.sequencerFeed(), address(next));
    }
}
