// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockFeed} from "./mocks/Mocks.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {Vm} from "forge-std/Vm.sol";

/// @notice Exercise real contribution accounting and emitted basis bytes. Venue,
/// access, feeds and VRF are test substitutes, not public service qualification.
contract ContributionMarkPackingTest is PooledVaultFixture {
    struct WideMark { uint256 lower; uint256 upper; uint256 scale; bytes32 fingerprint; }
    function _exercise(uint256 usdPrice) private {
        MockFeed a = new MockFeed(18,int256(usdPrice));
        MockFeed b = new MockFeed(18,int256(usdPrice));
        oracle.setDualFeed(address(t0),
            ZZZOracle.SourcePolicy(address(a),address(a).codehash,bytes32(uint256(1)),3600,18),
            ZZZOracle.SourcePolicy(address(b),address(b).codehash,bytes32(uint256(2)),3600,18),
            0,keccak256("maximum price offline fixture"));
        PoolConfig memory c = pools.accounting(poolId); c.maxPositionUSD = 1e40; pools.set(poolId,c);
        uint256 id = _mint(alice);
        (uint256 low0,uint256 high0,bytes32 fp0) = oracle.priceBounds(address(t0));
        (uint256 low1,uint256 high1,bytes32 fp1) = oracle.priceBounds(address(t1));
        // The old wide tuple encoding is the externally verified basis format.
        // Storage packing must not change this event or its field values.
        bytes32 expected = keccak256(abi.encode(poolId,id,usdPrice,usdPrice));
        expected = keccak256(abi.encode(expected,address(t0),WideMark(low0,high0,1,fp0)));
        expected = keccak256(abi.encode(expected,address(t1),WideMark(low1,high1,1,fp1)));
        vm.recordLogs(); _activate(alice,id,1,0);
        Vm.Log[] memory logs = vm.getRecordedLogs(); bool found;
        bytes32 signature = keccak256("ContributionVerified(uint256,uint256,uint256,uint256,uint256,uint256,uint160,bytes32)");
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].emitter != address(oracle.contributionPricing()) || logs[i].topics[0] != signature) continue;
            (uint256 inputLow,uint256 inputHigh,uint256 deployed,uint256 net,,bytes32 actual) =
                abi.decode(logs[i].data,(uint256,uint256,uint256,uint256,uint160,bytes32));
            assertEq(inputLow,usdPrice); assertEq(inputHigh,usdPrice);
            assertEq(deployed,usdPrice); assertEq(net,usdPrice); assertEq(actual,expected);
            found = true;
        }
        assertTrue(found); assertEq(vault.sharesOf(id),usdPrice);
        assertFalse(oracle.contributionPricing().active());
    }
    function testMaximumNormalizedPriceRetainsExactSharesAndBasisHash() public { _exercise(1e36); }
    function testFuzzPackedPricePreservesContributionAccounting(uint128 raw) public {
        _exercise(bound(uint256(raw),100e18,1e36));
    }
}
