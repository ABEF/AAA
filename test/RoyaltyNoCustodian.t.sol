// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";

/// @dev External royalty custody has been removed. These regressions verify
/// that its old selectors cannot drain funds, while holder rights stay live.
contract RoyaltyNoCustodianTest is PooledVaultFixture {
    ZZZRoyaltyRewards ledger;
    uint256 nftId;

    function setUp() public override {
        super.setUp();
        ledger = nft.royaltyRewards();
        nft.addRoyaltyAsset(address(t1));
        nftId = activatedPosition();
        nft.setMintEnd(uint64(block.timestamp+1));vm.warp(block.timestamp+3601);ledger.syncAll();
        t1.mint(address(ledger), 100);
        ledger.sync(address(t1));
    }

    function testGovernanceCannotSendRoyaltyBackingToExternalCustodian() public {
        ac.setPaused(true);
        uint256 beforeReceiver = t1.balanceOf(bob);
        uint256 beforeWeight = ledger.weightOf(nftId);
        (bool ok,) = address(ledger).call(abi.encodeWithSignature(
            "exitCustody(address,address,uint256,uint256,bytes32,bytes32)",
            address(t1), bob, 100, 0, bob.codehash, keccak256("removed custody")
        ));
        assertFalse(ok);
        assertEq(t1.balanceOf(address(ledger)), 100);
        assertEq(t1.balanceOf(bob), beforeReceiver);
        assertEq(ledger.weightOf(nftId), beforeWeight);
        vm.prank(alice);
        assertEq(ledger.claim(nftId, address(t1)), 100);
    }

    function testRemovedReturnSelectorCannotAcceptFundsOrAlterAccounting() public {
        uint256 beforeNative = address(ledger).balance;
        (bool ok,) = address(ledger).call{value: 1 ether}(abi.encodeWithSignature(
            "returnCustody(address,bytes32)", address(0), bytes32(uint256(1))
        ));
        assertFalse(ok);
        assertEq(address(ledger).balance, beforeNative);
        assertEq(ledger.claimable(nftId, address(t1)), 100);
        assertEq(ledger.liabilities(address(t1)), 100);
    }

    function testRemovedCustodyGettersAreNotPhantomCompatibilityBindings() public {
        (bool amount,) = address(ledger).staticcall(abi.encodeWithSignature("custodyAmount(address)", address(t1)));
        (bool nonce,) = address(ledger).staticcall(abi.encodeWithSignature("custodyNonce(address)", address(t1)));
        (bool id,) = address(ledger).staticcall(abi.encodeWithSignature("custodyId(address)", address(t1)));
        (bool count,) = address(ledger).staticcall(abi.encodeWithSignature("custodyCount()"));
        assertFalse(amount);
        assertFalse(nonce);
        assertFalse(id);
        assertFalse(count);
    }

    function testExistingAndFutureRoyaltiesFollowNFTDuringPausedOperations() public {
        ac.setPaused(true);
        uint256 weight = ledger.weightOf(nftId);
        uint256 ordinal = ledger.activationOrdinal(nftId);
        vm.prank(alice);
        nft.transferFrom(alice, bob, nftId);
        t1.mint(address(ledger), 50);
        (bool funded,) = address(ledger).call{value: 1 ether}("");
        assertTrue(funded);
        assertEq(ledger.weightOf(nftId), weight);
        assertEq(ledger.activationOrdinal(nftId), ordinal);
        assertTrue(ledger.eligibleFor(nftId, address(0)));
        assertTrue(ledger.eligibleFor(nftId, address(t1)));
        vm.prank(alice);
        vm.expectRevert(ZZZRoyaltyRewards.Unauthorized.selector);
        ledger.claim(nftId, address(t1));
        vm.prank(bob);
        assertEq(ledger.claim(nftId, address(t1)), 150);
        vm.prank(bob);
        assertEq(ledger.claim(nftId, address(0)), 1 ether);
        assertEq(ledger.claimable(nftId, address(t1)), 0);
        assertEq(ledger.claimable(nftId, address(0)), 0);
    }
}
