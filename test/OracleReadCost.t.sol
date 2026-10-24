// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {IPriceFeed} from "../src/interfaces/IZZZ.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";

/// @dev A pinned dependency can still fail behind an unchanged runtime/proxy.
/// These modes model failures, not an approved production uptime service.
contract FaultyUptimeRead {
    uint256 public mode;
    uint256 private immutable start;
    constructor(uint256 started) { start = started; }
    function setMode(uint256 next) external { mode = next; }
    function decimals() external view returns (uint8) {
        while (mode == 1) {}
        if (mode == 3) assembly ("memory-safe") { mstore(0, 0) mstore(32, 0) return(0, 64) }
        return 0;
    }
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        while (mode == 2) {}
        if (mode == 5) assembly ("memory-safe") { revert(0, 65536) }
        uint256 started = start;
        if (mode == 4 || mode == 6) {
            uint256 round = mode == 6 ? uint256(type(uint80).max) + 1 : 1;
            uint256 length = mode == 4 ? 192 : 160;
            assembly ("memory-safe") {
                let ptr := mload(0x40)
                mstore(ptr, round) mstore(add(ptr,32), 0)
                mstore(add(ptr,64), started) mstore(add(ptr,96), started)
                mstore(add(ptr,128), round) mstore(add(ptr,160), 0)
                return(ptr, length)
            }
        }
        return (1, 0, started, started, 1);
    }
}

contract OracleReadCostTest is Test {
    ZZZOracle private oracle;
    MockAccess private access;
    MockToken private token;
    MockFeed private first;
    MockFeed private second;
    FaultyUptimeRead private uptime;
    bytes32 private constant REVIEW = keccak256("offline source boundary fixture");

    function _source(MockFeed feed, uint256 independence) private view returns (ZZZOracle.SourcePolicy memory) {
        return ZZZOracle.SourcePolicy(address(feed),address(feed).codehash,bytes32(independence),3600,8);
    }
    function setUp() public {
        vm.warp(1_000_000);
        access = new MockAccess(); token = new MockToken(18);
        first = new MockFeed(8, 1e8); second = new MockFeed(8, 1e8);
        uptime = new FaultyUptimeRead(block.timestamp - 2 hours);
        oracle = new ZZZOracle(address(access),address(uptime));
        oracle.setDualFeed(address(token),_source(first,1),_source(second,2),300,REVIEW);
    }
    function _reject(uint256 mode) private {
        uptime.setMode(mode);
        uint256 before = gasleft();
        (bool ok,bytes memory result) = address(oracle).staticcall{gas:2_000_000}(
            abi.encodeCall(oracle.price,(address(token))));
        uint256 spent = before - gasleft();
        assertFalse(ok,"unusable dependency must not yield a price");
        assertEq(result,abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,address(uptime)),
            "failure must be a bounded Oracle domain error");
        assertLt(spent,650_000,"one failed dependency must not consume the caller gas budget");
    }
    function testUptimeDecimalsGasBombIsBounded() public { _reject(1); }
    function testUptimeRoundGasBombIsBounded() public { _reject(2); }
    function testUptimeOversizedDecimalsRejected() public { _reject(3); }
    function testUptimeOversizedRoundRejected() public { _reject(4); }
    function testUptimeRevertDataIsNotBubbled() public { _reject(5); }
    function testUptimeNoncanonicalRoundHasDomainError() public { _reject(6); }
    function testAdmissionReadsEachPriceSourceOnce() public {
        vm.expectCall(address(first),abi.encodeCall(IPriceFeed.decimals,()),uint64(1));
        vm.expectCall(address(second),abi.encodeCall(IPriceFeed.decimals,()),uint64(1));
        vm.expectCall(address(first),abi.encodeCall(IPriceFeed.latestRoundData,()),uint64(1));
        vm.expectCall(address(second),abi.encodeCall(IPriceFeed.latestRoundData,()),uint64(1));
        oracle.setDualFeed(address(token),_source(first,1),_source(second,2),300,REVIEW);
    }
    function testIdenticalCurrencyQuoteStillValidatesOneSourcePair() public {
        vm.expectCall(address(first),abi.encodeCall(IPriceFeed.latestRoundData,()),uint64(1));
        vm.expectCall(address(second),abi.encodeCall(IPriceFeed.latestRoundData,()),uint64(1));
        assertEq(oracle.quote(address(token),address(token),12345),12345);
    }
    function testIdenticalCurrencyQuoteDoesNotBypassFaultySource() public {
        second.set(0,block.timestamp,block.timestamp);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,address(token)));
        oracle.quote(address(token),address(token),12345);
    }
    function testFaultyOldUptimeDoesNotPreventGovernedReplacement() public {
        uptime.setMode(2);
        FaultyUptimeRead next = new FaultyUptimeRead(block.timestamp - 2 hours);
        access.seal();
        oracle.setSequencerFeed(address(next),address(next).codehash,REVIEW);
        assertEq(oracle.price(address(token)),1e18);
    }
}
