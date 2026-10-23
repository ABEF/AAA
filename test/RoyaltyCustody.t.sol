// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
contract RoyaltyCustodyTest is PooledVaultFixture {
    ZZZRoyaltyRewards ledger;uint256 nftId;bytes32 review=keccak256("fixture custody review");
    function setUp() public override {
        super.setUp();ledger=nft.royaltyRewards();nft.addRoyaltyAsset(address(t0));nftId=activatedPosition();
        t0.mint(address(ledger),100);ledger.sync(address(t0));
    }
    function _exit() private returns(bytes32) {
        ac.setPaused(true);return ledger.exitCustody(address(t0),bob,100,ledger.custodyNonce(address(t0)),bob.codehash,review);
    }
    function testFullRoyaltyCurrencyMovesWithoutChangingRightsOrLP() public {
        uint256 shares=vault.sharesOf(nftId);uint256 liabilities=ledger.liabilities(address(t0));bytes32 id=_exit();
        assertEq(ledger.custodyId(address(t0)),id);assertEq(ledger.custodyAmount(address(t0)),100);
        assertEq(ledger.liabilities(address(t0)),liabilities);assertEq(vault.sharesOf(nftId),shares);
        vm.expectRevert(ZZZRoyaltyRewards.CustodyInTransit.selector);ledger.claimable(nftId,address(t0));
        vm.prank(alice);vm.expectRevert(ZZZRoyaltyRewards.CustodyInTransit.selector);ledger.claim(nftId,address(t0));
    }
    function testFullReturnIsNotNewIncomeAndRightsFollowTransfer() public {
        bytes32 id=_exit();vm.prank(alice);nft.transferFrom(alice,bob,nftId);
        vm.prank(bob);t0.approve(address(ledger),100);vm.prank(bob);ledger.returnCustody(address(t0),id);
        assertEq(ledger.custodyCount(),0);assertEq(ledger.claimable(nftId,address(t0)),100);
        vm.prank(bob);assertEq(ledger.claim(nftId,address(t0)),100);assertEq(ledger.liabilities(address(t0)),0);
    }
    function testLateReceiptsNotDoubleCountedOnReturn() public {
        bytes32 id=_exit();t0.mint(address(ledger),50);
        vm.prank(bob);t0.approve(address(ledger),100);vm.prank(bob);ledger.returnCustody(address(t0),id);
        assertEq(ledger.claimable(nftId,address(t0)),150);ledger.sync(address(t0));assertEq(ledger.liabilities(address(t0)),150);
    }
    function testHealthyNativeRoyaltiesRemainClaimableDuringTokenCustody() public {
        _exit();vm.deal(address(this),1 ether);(bool ok,)=address(ledger).call{value:1 ether}("");assertTrue(ok);
        vm.prank(alice);assertEq(ledger.claim(nftId,address(0)),1 ether);
    }
    function testNativeExitAndExactReturn() public {
        vm.deal(address(this),2 ether);(bool ok,)=address(ledger).call{value:1 ether}("");assertTrue(ok);ac.setPaused(true);
        bytes32 id=ledger.exitCustody(address(0),bob,1 ether,0,bob.codehash,review);
        vm.expectRevert();ledger.returnCustody{value:1 ether-1}(address(0),id);
        ledger.returnCustody{value:1 ether}(address(0),id);assertEq(ledger.claimable(nftId,address(0)),1 ether);
    }
    function testRoyaltyExitRequiresPausedGovernanceExactAmountAndNonce() public {
        vm.expectRevert();ledger.exitCustody(address(t0),bob,100,0,bob.codehash,review);
        ac.setPaused(true);vm.prank(alice);vm.expectRevert();ledger.exitCustody(address(t0),bob,100,0,bob.codehash,review);
        vm.expectRevert();ledger.exitCustody(address(t0),bob,99,0,bob.codehash,review);
        vm.expectRevert();ledger.exitCustody(address(t0),bob,100,1,bob.codehash,review);
    }
    function testCustodyReturnCannotUseDonationAsReplacementOrBeReplayed() public {
        bytes32 id=_exit();t0.mint(address(ledger),100);
        vm.expectRevert();ledger.returnCustody(address(t0),id); // caller must actually fund the complete return.
        vm.prank(bob);t0.approve(address(ledger),100);vm.prank(bob);ledger.returnCustody(address(t0),id);
        vm.expectRevert();ledger.returnCustody(address(t0),id);
    }
    function testWholeCollectionCannotSnapshotExternalRoyaltyBacking() public {
        _exit();ac.setCanonicalState(1);vm.prank(ac.module(Ids.CANONICAL));
        vm.expectRevert(ZZZRoyaltyRewards.CustodyInTransit.selector);ledger.canonicalCapture();
    }
    function testNativeCustodyDefersOnlyNewNativeEligibilityWithoutRetroactiveFees() public {
        vm.deal(address(this),3 ether);(bool ok,)=address(ledger).call{value:1 ether}("");assertTrue(ok);ac.setPaused(true);
        bytes32 id=ledger.exitCustody(address(0),bob,1 ether,0,bob.codehash,review);
        ac.setPaused(false);uint256 next=_mint(bob);_activate(bob,next,1000,1000);
        assertFalse(ledger.eligibleFor(next,address(0)));
        (ok,)=address(ledger).call{value:0.5 ether}("");assertTrue(ok);
        ledger.returnCustody{value:1 ether}(address(0),id);ledger.sync(address(0));
        assertTrue(ledger.eligibleFor(next,address(0)));assertEq(ledger.claimable(next,address(0)),0);
        assertEq(ledger.claimable(nftId,address(0)),1.5 ether);
    }
}
