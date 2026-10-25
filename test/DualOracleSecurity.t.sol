// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {IPriceFeed} from "../src/interfaces/IZZZ.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";

contract GasExhaustingDualSource {
    uint8 public constant decimals = 8;
    bool public exhausted;
    function setExhausted() external { exhausted = true; }
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        while (exhausted) {}
        return (1, 1e8, block.timestamp, block.timestamp, 1);
    }
}

/// @dev These source mocks prove checks and accounting semantics only. Their
/// independence labels are fixtures, not qualification of real price providers.
contract DualOracleSecurityTest is Test {
    MockAccess access;
    MockToken token;
    MockFeed first;
    MockFeed second;
    ZZZOracle oracle;
    bytes32 constant REVIEW = keccak256("explicit reviewed dual source policy fixture");
    bytes32 constant SOURCE_A = keccak256("independent upstream A fixture");
    bytes32 constant SOURCE_B = keccak256("independent upstream B fixture");

    function setUp() public {
        vm.warp(1_000_000);
        access = new MockAccess();
        token = new MockToken(6);
        first = new MockFeed(8, 1e8);
        second = new MockFeed(8, 1e8);
        oracle = new ZZZOracle(address(access), address(0));
        _set(address(token), first, second, 100);
    }
    function _source(MockFeed feed, bytes32 independence) private view returns (ZZZOracle.SourcePolicy memory) {
        return ZZZOracle.SourcePolicy(address(feed), address(feed).codehash, independence, 3600, feed.decimals());
    }
    function _set(address asset, MockFeed a, MockFeed b, uint16 deviation) private returns (bytes32) {
        return oracle.setDualFeed(asset, _source(a, SOURCE_A), _source(b, SOURCE_B), deviation, REVIEW);
    }
    function _rejectPrice() private {
        vm.expectRevert(); oracle.price(address(token));
    }
    function _mockRound(address source, uint256 round, int256 answer, uint256 started,
        uint256 updated, uint256 answered) private {
        vm.mockCall(source, abi.encodeCall(IPriceFeed.latestRoundData, ()),
            abi.encode(round, answer, started, updated, answered));
    }
    function testDualBoundsUseLowerForThresholdAndUpperForConversionQuote() public {
        second.set(101e6, block.timestamp, block.timestamp);
        (uint256 lower, uint256 upper, bytes32 fingerprint) = oracle.priceBounds(address(token));
        assertEq(lower, 1e18); assertEq(upper, 1.01e18); assertTrue(fingerprint != bytes32(0));
        assertEq(oracle.price(address(token)), lower);
        assertEq(oracle.value(address(token), 100e6), 100e18);
        MockFeed ethA = new MockFeed(8, 2000e8);
        MockFeed ethB = new MockFeed(8, 2020e8);
        _set(address(0), ethA, ethB, 100);
        assertEq(oracle.quote(address(token), address(0), 100e6), 0.0505 ether);
        assertEq(oracle.quote(address(0), address(token), 1 ether), 2020e6);
        assertEq(oracle.quote(address(token), address(token), 12345), 12345);
    }
    function testMixedDecimalsNormalizedAndNativeIdentityExplicit() public {
        MockFeed nativeA = new MockFeed(8, 2000e8);
        MockFeed nativeB = new MockFeed(18, 2000e18);
        _set(address(0), nativeA, nativeB, 0);
        assertEq(oracle.PRICING_VERSION(), 2);
        assertEq(oracle.tokenDecimals(address(0)), 18);
        assertEq(oracle.value(address(0), 0.05 ether), 100e18);
        assertGt(oracle.referenceX96(address(0), address(token)), 0);
    }
    function testStableDepegUsesBothActualPricesNotOneDollar() public {
        first.set(90e6, block.timestamp, block.timestamp);
        second.set(90e6, block.timestamp, block.timestamp);
        assertEq(oracle.value(address(token), 100e6), 90e18);
        assertEq(oracle.price(address(token)), 0.9e18);
    }
    function testSpreadExactBoundaryAndOneRawUnitAbove() public {
        second.set(101e6, block.timestamp, block.timestamp);
        assertEq(oracle.price(address(token)), 1e18);
        second.set(101e6 + 1, block.timestamp, block.timestamp);
        _rejectPrice();
    }
    function testZeroSpreadRequiresExactNormalizedAgreement() public {
        _set(address(token), first, second, 0);
        second.set(1e8 + 1, block.timestamp, block.timestamp);
        _rejectPrice();
    }
    function testStaleEitherSourceCannotFallBackToHealthySource() public {
        vm.warp(block.timestamp + 3601);
        first.set(1e8, block.timestamp, block.timestamp);
        _rejectPrice();
        second.set(1e8, block.timestamp, block.timestamp);
        assertEq(oracle.price(address(token)), 1e18);
        first.set(1e8, block.timestamp - 3601, block.timestamp - 3601);
        _rejectPrice();
    }
    function testExactFreshnessBoundaryAccepted() public {
        vm.warp(block.timestamp + 3600);
        assertEq(oracle.price(address(token)), 1e18);
    }
    function testZeroAndNegativeAnswersRejectedWithoutFallback() public {
        first.set(0, block.timestamp, block.timestamp); _rejectPrice();
        first.set(-1, block.timestamp, block.timestamp); _rejectPrice();
        first.set(1e8, block.timestamp, block.timestamp);
        second.set(-1, block.timestamp, block.timestamp); _rejectPrice();
    }
    function testFutureZeroAndReversedTimestampsRejected() public {
        first.set(1e8, block.timestamp, block.timestamp + 1); _rejectPrice();
        first.set(1e8, 0, block.timestamp); _rejectPrice();
        first.set(1e8, 0, 0); _rejectPrice();
        first.set(1e8, block.timestamp, block.timestamp - 1); _rejectPrice();
    }
    function testIncompleteZeroAndNoncanonicalRoundsRejected() public {
        first.rounds(10, 9); _rejectPrice();
        first.rounds(0, 0); _rejectPrice();
        _mockRound(address(first), uint256(type(uint80).max) + 1, 1e8, block.timestamp, block.timestamp, type(uint256).max);
        _rejectPrice();
    }
    function testNormalizedOverflowRejectedWithDomainError() public {
        first.set(type(int256).max, block.timestamp, block.timestamp);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(token)));
        oracle.price(address(token));
    }
    function testMaximumNormalizedPriceAndOneUnitAbove() public {
        MockFeed a = new MockFeed(18, 1e36);
        MockFeed b = new MockFeed(18, 1e36);
        _set(address(token), a, b, 0);
        assertEq(oracle.price(address(token)), 1e36);
        a.set(1e36 + 1, block.timestamp, block.timestamp); _rejectPrice();
    }
    function testRuntimeChangeFailsEvenWithSameAnswer() public {
        vm.etch(address(second), hex"60006000fd");
        _rejectPrice();
    }
    function testSourceDecimalsChangeFailsEvenWithSameRuntime() public {
        vm.mockCall(address(second), abi.encodeCall(IPriceFeed.decimals, ()), abi.encode(uint256(18)));
        _rejectPrice();
    }
    function testAssetDecimalsChangeFails() public {
        vm.mockCall(address(token), abi.encodeCall(IPriceFeed.decimals, ()), abi.encode(uint256(18)));
        _rejectPrice();
    }
    function testMalformedShortAndOversizedSourceResponsesRejected() public {
        vm.mockCall(address(second), abi.encodeCall(IPriceFeed.latestRoundData, ()), hex"01"); _rejectPrice();
        vm.mockCall(address(second), abi.encodeCall(IPriceFeed.latestRoundData, ()), new bytes(16_384)); _rejectPrice();
        vm.clearMockedCalls();
        vm.mockCall(address(second), abi.encodeCall(IPriceFeed.decimals, ()), new bytes(64)); _rejectPrice();
    }
    function testRevertingSourceDoesNotSelectTheOther() public {
        vm.mockCallRevert(address(first), abi.encodeCall(IPriceFeed.latestRoundData, ()), hex"deadbeef");
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(token)));
        oracle.price(address(token));
    }
    function testGasExhaustingSourceIsBoundedAndFailsClosed() public {
        GasExhaustingDualSource bomb = new GasExhaustingDualSource();
        ZZZOracle.SourcePolicy memory a = _source(first, SOURCE_A);
        ZZZOracle.SourcePolicy memory b = ZZZOracle.SourcePolicy(address(bomb), address(bomb).codehash, SOURCE_B, 3600, 8);
        oracle.setDualFeed(address(token), a, b, 0, REVIEW);
        bomb.setExhausted();
        uint256 startingGas = gasleft();
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(token)));
        oracle.price(address(token));
        assertLt(startingGas - gasleft(), 650_000);
    }
    function testUnknownAssetAndLegacySingleFeedAreExplicitlyRejected() public {
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector, address(77)));
        oracle.price(address(77));
        // Retired single-source calldata stays unsupported without keeping a
        // callable compatibility shim in the production ABI.
        (bool accepted,) = address(oracle).call(abi.encodeWithSignature(
            "setFeed(address,address,uint32)",address(token),address(first),uint32(3600)));
        assertFalse(accepted);
        assertEq(oracle.policyCount(), 1);
    }
    function testPolicyRejectsSameAddressOrSameIndependenceIdentity() public {
        ZZZOracle.SourcePolicy memory a = _source(first, SOURCE_A);
        ZZZOracle.SourcePolicy memory b = _source(first, SOURCE_B);
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
        b = _source(second, SOURCE_A);
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
        a.independenceId = bytes32(0); b.independenceId = SOURCE_B;
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
    }
    function testPolicyRejectsZeroReviewWrongRuntimeBadAgeAndExcessiveSpread() public {
        ZZZOracle.SourcePolicy memory a = _source(first, SOURCE_A);
        ZZZOracle.SourcePolicy memory b = _source(second, SOURCE_B);
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, bytes32(0));
        a.expectedCodeHash = keccak256("wrong");
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
        a = _source(first, SOURCE_A); a.maxAge = 0;
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
        a.maxAge = 86401;
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
        a = _source(first, SOURCE_A);
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 501, REVIEW);
    }
    function testPolicyAdmissionRejectsCurrentlyDivergentOrInvalidSource() public {
        ZZZOracle.SourcePolicy memory a = _source(first, SOURCE_A);
        ZZZOracle.SourcePolicy memory b = _source(second, SOURCE_B);
        second.set(2e8, block.timestamp, block.timestamp);
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
        second.set(0, block.timestamp, block.timestamp);
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 100, REVIEW);
        assertEq(oracle.policyCount(), 1);
    }
    function testPolicyHistoryAppendOnlyEvenWhenReturningToSameParameters() public {
        bytes32 old = oracle.activePolicy(address(token));
        ZZZOracle.DualPolicy memory beforePolicy = oracle.policy(old);
        bytes32 next = _set(address(token), first, second, 100);
        assertTrue(old != next); assertEq(oracle.policyCount(), 2);
        assertEq(oracle.policyAt(0), old); assertEq(oracle.policyAt(1), next);
        assertEq(abi.encode(oracle.policy(old)), abi.encode(beforePolicy));
        assertEq(next, keccak256(abi.encode(address(oracle), uint256(1), oracle.policy(next))));
        (address primary, uint32 age, uint8 fd, uint8 td) = oracle.feeds(address(token));
        assertEq(primary, address(first)); assertEq(age, 3600); assertEq(fd, 8); assertEq(td, 6);
    }
    function testFingerprintBindsCompleteRoundsPolicyAndOracleDomain() public {
        (,, bytes32 original) = oracle.priceBounds(address(token));
        ZZZOracle.Round memory r = ZZZOracle.Round(1, 1e8, block.timestamp, block.timestamp, 1);
        bytes32 expected = keccak256(abi.encode(oracle.FINGERPRINT_DOMAIN(), block.chainid, address(oracle),
            oracle.activePolicy(address(token)), bytes32(0), r, r));
        assertEq(original, expected);
        second.rounds(2, 2);
        (,, bytes32 changed) = oracle.priceBounds(address(token));
        assertTrue(original != changed);
        _set(address(token), first, second, 100);
        (,, bytes32 reconfigured) = oracle.priceBounds(address(token));
        assertTrue(changed != reconfigured);
    }
    function testImmediateGovernanceAfterSealAndUnauthorizedReconfigurationBlocked() public {
        access.seal();
        bytes32 previous = oracle.activePolicy(address(token));
        bytes32 next = _set(address(token), first, second, 50);
        assertTrue(previous != next);
        ZZZOracle.SourcePolicy memory a = _source(first, SOURCE_A);
        ZZZOracle.SourcePolicy memory b = _source(second, SOURCE_B);
        vm.prank(address(99)); vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 50, REVIEW);
        access.setPreparation(true);
        vm.expectRevert(); oracle.setDualFeed(address(token), a, b, 50, REVIEW);
        assertEq(oracle.activePolicy(address(token)), next);
    }
    function testSequencerDownGraceAndRecoveryStillGateDualPrices() public {
        MockFeed sequencer = new MockFeed(0, 0);
        oracle = new ZZZOracle(address(access), address(sequencer));
        _set(address(token), first, second, 100);
        _rejectPrice();
        vm.warp(block.timestamp + 3601);
        first.set(1e8, block.timestamp, block.timestamp);
        second.set(1e8, block.timestamp, block.timestamp);
        assertEq(oracle.price(address(token)), 1e18);
        sequencer.set(1, block.timestamp, block.timestamp); _rejectPrice();
    }
    function testFuzzBoundsAndSpreadNeverFavorSingleSource(uint96 raw, uint16 spread) public {
        uint256 low = bound(uint256(raw), 1, 1e25);
        uint256 delta = bound(uint256(spread), 0, 500);
        MockFeed a = new MockFeed(18, int256(low));
        MockFeed b = new MockFeed(18, int256(low + low * delta / 10000));
        _set(address(token), a, b, uint16(delta));
        (uint256 lower, uint256 upper,) = oracle.priceBounds(address(token));
        assertEq(lower, low); assertEq(upper, low + low * delta / 10000);
        assertLe(upper - lower, lower * delta / 10000);
    }
}
