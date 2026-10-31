// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZPythPriceFeed} from "../src/ZZZPythPriceFeed.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {MockAccess, MockFeed} from "./mocks/Mocks.sol";

/// @dev Offline ABI/failure fixture; it does not verify a real Pyth proof,
/// provider, publisher set, proxy policy or update-service availability.
contract PythCoreReadFixture {
    bytes32 public immutable id;
    int64 public price;
    uint64 public confidence;
    int32 public exponent;
    uint256 public published;
    bool public exhaust;
    constructor(bytes32 feed) { id = feed; }
    function set(int64 value, uint64 conf, int32 expo, uint256 timestamp) external {
        price = value; confidence = conf; exponent = expo; published = timestamp;
    }
    function setExhaust(bool enabled) external { exhaust = enabled; }
    function getPriceUnsafe(bytes32 feed) external view returns (int64, uint64, int32, uint256) {
        require(feed == id, "unknown feed fixture");
        while (exhaust) {}
        return (price, confidence, exponent, published);
    }
}

contract PythPriceFeedTest is Test {
    bytes32 private constant FEED = keccak256("offline ETH/USD fixture, not a real source ID");
    bytes32 private constant REVIEW = keccak256("explicit offline reader policy, not independent approval");
    PythCoreReadFixture private core;
    ZZZPythPriceFeed private reader;

    function setUp() public {
        vm.warp(1_000_000);
        core = new PythCoreReadFixture(FEED);
        core.set(2000e8, 1e8, -8, block.timestamp - 10);
        reader = _deploy(address(core), address(core).codehash, FEED, -8, 60, 100, REVIEW);
    }
    function _deploy(address source, bytes32 code, bytes32 id, int32 expo, uint32 age, uint16 conf, bytes32 review)
        private returns (ZZZPythPriceFeed) {
        return new ZZZPythPriceFeed(source, code, id, expo, age, conf, review);
    }
    function _reject() private {
        vm.expectRevert(ZZZPythPriceFeed.InvalidObservation.selector);
        reader.latestRoundData();
    }
    function _mock(uint256 price, uint256 conf, uint256 expo, uint256 published) private {
        vm.mockCall(address(core), abi.encodeCall(core.getPriceUnsafe, (FEED)), abi.encode(price, conf, expo, published));
    }
    function testPreservesExactPriceOriginalTimestampAndSyntheticRoundIdentity() public view {
        (uint80 round, int256 answer, uint256 started, uint256 updated, uint80 answered) = reader.latestRoundData();
        assertEq(answer, 2000e8); assertEq(started, block.timestamp - 10); assertEq(updated, started);
        assertEq(uint256(round), updated); assertEq(answered, round); assertEq(reader.decimals(), 8);
        assertEq(reader.core(), address(core)); assertEq(reader.feedId(), FEED); assertEq(reader.reviewHash(), REVIEW);
    }
    function testConstructorRejectsMissingIdentityUnreviewedRuntimeAndInvalidPolicy() public {
        bytes32 code = address(core).codehash;
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(0), code, FEED, -8, 60, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(99), code, FEED, -8, 60, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), bytes32(0), FEED, -8, 60, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), bytes32(uint256(1)), FEED, -8, 60, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), code, bytes32(0), -8, 60, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), code, FEED, -8, 60, 100, bytes32(0));
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), code, FEED, -19, 60, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), code, FEED, 1, 60, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), code, FEED, -8, 0, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), code, FEED, -8, 86401, 100, REVIEW);
        vm.expectRevert(ZZZPythPriceFeed.InvalidConfiguration.selector); _deploy(address(core), code, FEED, -8, 60, 301, REVIEW);
    }
    function testFreshnessBoundaryIsExactAndCannotBeRenewedByReading() public {
        core.set(2000e8, 0, -8, block.timestamp - 60);
        reader.latestRoundData(); vm.warp(block.timestamp + 1); _reject();
    }
    function testZeroFutureAndOversizedPublishTimesReject() public {
        core.set(2000e8, 0, -8, 0); _reject();
        core.set(2000e8, 0, -8, block.timestamp + 1); _reject();
        vm.warp(uint256(type(uint80).max) + 10);
        core.set(2000e8, 0, -8, block.timestamp); _reject();
    }
    function testZeroNegativeAndNoncanonicalWidePricesReject() public {
        core.set(0, 0, -8, block.timestamp); _reject();
        core.set(-1, 0, -8, block.timestamp); _reject();
        _mock(uint256(uint64(type(int64).max)) + 1, 0, uint256(int256(-8)), block.timestamp); _reject();
    }
    function testExponentChangesAndMalformedSignExtensionReject() public {
        core.set(2000e8, 0, -7, block.timestamp); _reject();
        // uint32(-8), without the ABI's required sign extension, is not int32(-8).
        _mock(2000e8, 0, uint32(type(uint32).max) - 7, block.timestamp); _reject();
    }
    function testNoncanonicalConfidenceCannotTruncateToSafeValue() public {
        _mock(2000e8, uint256(type(uint64).max) + 1, uint256(int256(-8)), block.timestamp); _reject();
    }
    function testConfidenceBoundaryAndOneRawUnitAboveAreExact() public {
        core.set(2000e8, 20e8, -8, block.timestamp); reader.latestRoundData();
        core.set(2000e8, 20e8 + 1, -8, block.timestamp); _reject();
        core.set(1, 1, -8, block.timestamp); _reject();
    }
    function testZeroConfidencePolicyRequiresActualZeroConfidence() public {
        reader = _deploy(address(core), address(core).codehash, FEED, -8, 60, 0, REVIEW);
        _reject(); core.set(2000e8, 0, -8, block.timestamp); reader.latestRoundData();
    }
    function testChangedCoreRuntimeFailsDespitePreviouslyValidPrice() public {
        vm.etch(address(core), hex"60006000fd"); _reject();
    }
    function testShortOversizedAndRevertingDataHaveBoundedDomainErrors() public {
        bytes memory input = abi.encodeCall(core.getPriceUnsafe, (FEED));
        vm.mockCall(address(core), input, hex"01"); _reject();
        vm.mockCall(address(core), input, new bytes(65536)); _reject();
        vm.clearMockedCalls(); vm.mockCallRevert(address(core), input, new bytes(65536)); _reject();
    }
    function testGasExhaustionCannotConsumeEntireCallerBudget() public {
        core.setExhaust(true);
        uint256 before = gasleft();
        (bool ok, bytes memory data) = address(reader).staticcall{gas:1_000_000}(abi.encodeCall(reader.latestRoundData, ()));
        assertFalse(ok); assertEq(data, abi.encodeWithSelector(ZZZPythPriceFeed.InvalidObservation.selector));
        assertLt(before - gasleft(), 350_000);
    }
    function testNoNativeValueOrArbitraryUpdateSurface() public {
        vm.deal(address(this), 1 ether);
        (bool ok,) = address(reader).call{value:1} (abi.encodeCall(reader.latestRoundData, ())); assertFalse(ok);
        (ok,) = address(reader).call{value:1}(""); assertFalse(ok);
        (ok,) = address(reader).call(abi.encodeWithSignature("updatePriceFeeds(bytes[])", new bytes[](0))); assertFalse(ok);
        assertEq(address(reader).balance, 0);
    }
    function testExponentEndpointsRetainExactUnitsWithoutRescaling() public {
        ZZZPythPriceFeed zero = _deploy(address(core), address(core).codehash, FEED, 0, 86400, 300, REVIEW);
        core.set(123, 0, 0, block.timestamp); (,int256 answer,,,) = zero.latestRoundData();
        assertEq(answer, 123); assertEq(zero.decimals(), 0);
        ZZZPythPriceFeed eighteen = _deploy(address(core), address(core).codehash, FEED, -18, 86400, 300, REVIEW);
        core.set(type(int64).max, 0, -18, block.timestamp); (,answer,,,) = eighteen.latestRoundData();
        assertEq(answer, type(int64).max); assertEq(eighteen.decimals(), 18);
    }
    function testFuzzConfidenceCheckMatchesExactRationalBoundary(uint64 rawPrice, uint64 rawConfidence, uint16 rawLimit) public {
        uint64 price = uint64(bound(rawPrice, 1, uint64(type(int64).max)));
        uint16 limit = uint16(bound(rawLimit, 0, 300));
        reader = _deploy(address(core), address(core).codehash, FEED, -8, 60, limit, REVIEW);
        core.set(int64(price), rawConfidence, -8, block.timestamp);
        bool expected = uint256(rawConfidence) * 10_000 <= uint256(price) * limit;
        (bool ok,) = address(reader).staticcall(abi.encodeCall(reader.latestRoundData, ()));
        assertEq(ok, expected);
    }
    function _oracle() private returns (ZZZOracle oracle, MockFeed first) {
        MockAccess access = new MockAccess(); ProtocolPolicyFixture.bind(address(access));
        first = new MockFeed(8, 2000e8);
        oracle = new ZZZOracle(address(access), address(0));
        oracle.setDualFeed(address(0),
            ZZZOracle.SourcePolicy(address(first), address(first).codehash, keccak256("offline Chainlink fixture"), 60, 8),
            ZZZOracle.SourcePolicy(address(reader), address(reader).codehash, keccak256("offline Pyth fixture"), 60, 8), 300, REVIEW);
    }
    function testNativeOracleIntegrationPreservesDualBoundsAndChangingRoundFingerprint() public {
        (ZZZOracle oracle,) = _oracle();
        (uint256 low, uint256 high, bytes32 fingerprint) = oracle.priceBounds(address(0));
        assertEq(low, 2000e18); assertEq(high, low); assertTrue(fingerprint != bytes32(0));
        core.set(2020e8, 1e8, -8, block.timestamp);
        bytes32 next;
        (low, high, next) = oracle.priceBounds(address(0));
        assertEq(low, 2000e18); assertEq(high, 2020e18); assertTrue(next != fingerprint);
        assertEq(oracle.tokenDecimals(address(0)), 18); assertEq(oracle.value(address(0), 0.05 ether), 100e18);
    }
    function testNativeOracleIntegrationHasNoSingleSourceFallbackForOutageOrDisagreement() public {
        (ZZZOracle oracle,) = _oracle();
        core.set(2000e8, 0, -8, block.timestamp - 61); vm.expectRevert(); oracle.priceBounds(address(0));
        core.set(2000e8, 21e8, -8, block.timestamp); vm.expectRevert(); oracle.priceBounds(address(0));
        core.set(2060e8, 0, -8, block.timestamp); oracle.priceBounds(address(0));
        core.set(2060e8 + 1, 0, -8, block.timestamp); vm.expectRevert(); oracle.priceBounds(address(0));
        vm.etch(address(core), hex"60006000fd"); vm.expectRevert(); oracle.priceBounds(address(0));
    }
}
