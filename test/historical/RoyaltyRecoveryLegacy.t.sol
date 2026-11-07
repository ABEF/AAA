// Historical conversion/recovery1 fixture; not the fresh settlement2 ledger.
// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {RoyaltyConversionTest, ConversionNFT, ConversionToken, ConversionVenue, ConversionAccess}
    from "../RoyaltyConversion.t.sol";
import {ZZZRoyaltyRewards} from "./ZZZRoyaltyRewards.sol";
import {ZZZRewardConverter} from "./ZZZRewardConverterLegacy.sol";
import {Ids} from "../../src/libraries/ZZZTypes.sol";
import {DualOracleFixture} from "../helpers/DualOracleFixture.sol";
import {ZZZOracle} from "../../src/ZZZOracle.sol";
using DualOracleFixture for ZZZOracle;

contract RecoveryNFT is ConversionNFT {
    constructor(address controller) ConversionNFT(controller) {}
    function royaltyRewards() external view returns(address) { return address(royalties); }
}
contract RecoveryHandoff {
    address public immutable destinationController;
    constructor(address controller) { destinationController = controller; }
}

/// @dev Real royalty/converter code; synthetic venue, currency, prices and access.
/// The separate TypedV4Rewards suite exercises actual local v4 core execution.
contract RoyaltyRecoveryTest is RoyaltyConversionTest {
    bytes32 private constant REVIEW = keccak256("reviewed unallocated-only recovery");

    function _unknown(bool priced) private returns(ConversionToken unknown, ConversionVenue market, bytes32 route) {
        unknown = new ConversionToken(); market = new ConversionVenue(address(unknown),w);
        route = c.addRoute(ZZZRewardConverter.RoutePolicy(address(unknown),address(market),address(market),
            address(market),500,address(unknown).codehash,address(market).codehash,address(market).codehash,
            address(market).codehash,REVIEW));
        if(priced) oracle.setTestFeed(address(unknown),address(sf),3600);
    }
    function _recover(address asset,uint256 amount,bytes32 route) private returns(uint256) {
        return r.recoverUnallocated(asset,amount,route,1,block.timestamp+60,REVIEW);
    }
    function _empty() private returns(ConversionNFT fresh,ZZZRoyaltyRewards ledger) {
        fresh = new ConversionNFT(address(a)); ledger=fresh.royalties(); a.bind(Ids.NFT,address(fresh));
    }

    function testRecoveryUnsupportedTokenDoesNotNeedPermanentAdmissionAndUsesCurrentWeights() public {
        (ConversionToken unknown,,bytes32 route) = _unknown(true);
        unknown.mint(address(r),600e6); nft.activate(3);
        uint256 count=r.assetCount(); assertEq(_recover(address(unknown),600e6,route),0.3 ether);
        assertFalse(r.isAsset(address(unknown))); assertEq(r.assetCount(),count);
        assertEq(r.claimable(1,address(0)),0.05 ether); assertEq(r.claimable(2,address(0)),0.1 ether);
        assertEq(r.claimable(3,address(0)),0.15 ether); assertEq(unknown.balanceOf(address(r)),0);
        assertEq(unknown.allowance(address(r),address(c)),0);
        vm.prank(alice); assertEq(r.claim(1,address(0)),0.05 ether);
        assertEq(r.liabilities(address(0)),0.25 ether);
    }

    function testRecoveryAdmittedOrphansExcludeEveryEarnedAndPendingEntitlement() public {
        (ConversionToken unknown,,bytes32 route) = _unknown(true);
        unknown.mint(address(r),600e6); nft.add(address(unknown));
        unknown.mint(address(r),300e6);
        uint256 aliceBefore=r.claimable(1,address(unknown)); uint256 bobBefore=r.claimable(2,address(unknown));
        assertEq(_recover(address(unknown),600e6,route),0.3 ether);
        assertEq(r.orphaned(address(unknown)),0); assertEq(unknown.balanceOf(address(r)),300e6);
        assertEq(r.accounted(address(unknown)),300e6); assertEq(r.liabilities(address(unknown)),300e6);
        assertEq(r.claimable(1,address(unknown)),aliceBefore); assertEq(r.claimable(2,address(unknown)),bobBefore);
        vm.expectRevert(); _recover(address(unknown),1,route);
        vm.prank(alice); assertEq(r.claim(1,address(unknown)),100e6);
        vm.prank(bob); assertEq(r.claim(2,address(unknown)),200e6);
    }

    function testRecoveryCannotTakeDeferredCohortFundsEvenWhenNewcomerNowActive() public {
        t.mint(address(r),600e6); t.setFault(1); nft.activate(3); t.setFault(0);
        vm.expectRevert(); _recover(address(t),1,routeId);
        assertEq(r.claimable(1,address(t)),200e6); assertEq(r.claimable(2,address(t)),400e6);
        assertEq(r.claimable(3,address(t)),0); r.sync(address(t));
        assertEq(r.claimable(3,address(t)),0); assertTrue(r.eligibleFor(3,address(t)));
    }

    function testRecoveryNativeEmptyCohortFundsNeedActivationButNoConverterOrSwap() public {
        (ConversionNFT fresh,ZZZRoyaltyRewards ledger)=_empty();
        (bool ok,)=address(ledger).call{value:3 ether}(""); assertTrue(ok); ledger.sync(address(0));
        vm.expectRevert(); ledger.recoverUnallocated(address(0),3 ether,0,3 ether,block.timestamp+60,REVIEW);
        fresh.mint(alice,9,0); fresh.activate(9); fresh.mint(bob,10,1); fresh.activate(10);
        assertEq(ledger.recoverUnallocated(address(0),3 ether,0,3 ether,block.timestamp+60,REVIEW),3 ether);
        assertEq(ledger.orphaned(address(0)),0); assertEq(ledger.accounted(address(0)),3 ether);
        assertEq(ledger.liabilities(address(0)),3 ether); assertEq(ledger.claimable(9,address(0)),1 ether);
        assertEq(ledger.claimable(10,address(0)),2 ether); assertEq(address(ledger).balance,3 ether);
    }

    function testRecoveryKeeperCannotActAsGovernanceAndLifecycleLocksRollback() public {
        (ConversionToken unknown,,bytes32 route) = _unknown(true); unknown.mint(address(r),600e6);
        a.setKeeper(bob,true); vm.prank(bob); vm.expectRevert(); _recover(address(unknown),600e6,route);
        a.setPaused(true); vm.expectRevert(); _recover(address(unknown),600e6,route); a.setPaused(false);
        a.setPreparation(true); vm.expectRevert(); _recover(address(unknown),600e6,route); a.setPreparation(false);
        a.state(1); vm.expectRevert(); _recover(address(unknown),600e6,route); a.state(0);
        a.bind(Ids.NFT,address(1)); vm.expectRevert(); _recover(address(unknown),600e6,route);
        a.bind(Ids.NFT,address(nft)); assertEq(unknown.balanceOf(address(r)),600e6);
        assertEq(_recover(address(unknown),600e6,route),0.3 ether);
    }

    function testRecoveryUnknownWithoutPricesOrSellableRouteRetainsAllFundsAndETHClaims() public {
        (ConversionToken unknown,,bytes32 route) = _unknown(false); unknown.mint(address(r),600e6);
        vm.expectRevert(); _recover(address(unknown),600e6,route);
        assertEq(unknown.balanceOf(address(r)),600e6); pay(3 ether);
        vm.prank(alice); assertEq(r.claim(1,address(0)),1 ether);
        assertEq(unknown.allowance(address(r),address(c)),0);
    }

    function testRecoveryLossCapStrongerMinimumAndLyingOutputAreAtomic() public {
        (ConversionToken unknown,ConversionVenue market,bytes32 route)=_unknown(true);
        unknown.mint(address(r),600e6); market.settings(9800,false);
        vm.expectRevert(); _recover(address(unknown),600e6,route);
        market.settings(10000,true); vm.expectRevert(); _recover(address(unknown),600e6,route);
        market.settings(10000,false); vm.expectRevert();
        r.recoverUnallocated(address(unknown),600e6,route,0.31 ether,block.timestamp+60,REVIEW);
        assertEq(unknown.balanceOf(address(r)),600e6); assertEq(r.liabilities(address(0)),0);
        assertEq(_recover(address(unknown),600e6,route),0.3 ether);
    }

    function testRecoveryExactInputsZeroReviewExpiredAmountAndDisabledRouteReject() public {
        (ConversionToken unknown,,bytes32 route)=_unknown(true); unknown.mint(address(r),600e6);
        vm.expectRevert(); r.recoverUnallocated(address(unknown),0,route,1,block.timestamp+60,REVIEW);
        vm.expectRevert(); r.recoverUnallocated(address(unknown),1,route,0,block.timestamp+60,REVIEW);
        vm.expectRevert(); r.recoverUnallocated(address(unknown),1,route,1,block.timestamp+60,0);
        vm.expectRevert(); r.recoverUnallocated(address(unknown),1,route,1,block.timestamp-1,REVIEW);
        vm.expectRevert(); r.recoverUnallocated(address(unknown),1,route,1,block.timestamp+601,REVIEW);
        vm.expectRevert(); _recover(address(unknown),600e6+1,route);
        c.setRouteEnabled(route,false); vm.expectRevert(); _recover(address(unknown),600e6,route);
        assertEq(unknown.balanceOf(address(r)),600e6); assertEq(r.accounted(address(0)),0);
    }

    function testRecoveryCallbackPauseRollsBackAndTransferCarriesRecoveredRights() public {
        (ConversionToken unknown,ConversionVenue market,bytes32 route)=_unknown(true);
        unknown.mint(address(r),600e6); market.setCallback(address(a),abi.encodeCall(a.setPaused,(true)));
        vm.expectRevert(); _recover(address(unknown),600e6,route);
        assertFalse(a.paused()); assertEq(unknown.balanceOf(address(r)),600e6);
        market.setCallback(address(0),bytes("")); _recover(address(unknown),600e6,route);
        vm.prank(alice); nft.transferFrom(alice,carol,1);
        vm.prank(alice); vm.expectRevert(); r.claim(1,address(0));
        vm.prank(carol); assertEq(r.claim(1,address(0)),0.1 ether);
    }

    function testRecoveryTerminalLPExitDoesNotEndRoyaltyRecovery() public {
        (ConversionToken unknown,,bytes32 route)=_unknown(true); unknown.mint(address(r),600e6);
        a.bind(Ids.VAULT,address(this)); a.setPaused(true); a.startLPExit(); a.setPaused(false);
        assertEq(_recover(address(unknown),600e6,route),0.3 ether); assertTrue(a.lpExitStarted());
    }

    function testRecoveryFuzzPreservesOldRewardsAndConservesEveryRecoveredWei(uint96 raw) public {
        uint256 amount=bound(uint256(raw),6,1e12);
        (ConversionToken unknown,,bytes32 route)=_unknown(true);
        pay(3 ether); nft.activate(3); unknown.mint(address(r),amount);
        uint256 output=_recover(address(unknown),amount,route);
        uint256 one=r.claimable(1,address(0)); uint256 two=r.claimable(2,address(0));
        uint256 three=r.claimable(3,address(0));
        assertGe(one,1 ether); assertGe(two,2 ether);
        assertLe(one+two+three,3 ether+output); assertLe(3 ether+output-one-two-three,3);
        vm.prank(alice); assertEq(r.claim(1,address(0)),one);
        vm.prank(bob); assertEq(r.claim(2,address(0)),two);
        vm.prank(carol); assertEq(r.claim(3,address(0)),three);
        assertEq(address(r).balance,3 ether+output-one-two-three);
        assertEq(r.liabilities(address(0)),address(r).balance);
        assertEq(unknown.balanceOf(address(r)),0);
    }

    function testRecoveryThousandNFTsUseOneWeightedAllocationWithoutDormantDilution() public {
        (ConversionNFT fresh,ZZZRoyaltyRewards ledger)=_empty();
        uint256 total=1998 ether; vm.deal(address(this),total);
        (bool ok,)=address(ledger).call{value:total}(""); assertTrue(ok); ledger.sync(address(0));
        for(uint256 i;i<999;++i){fresh.mint(alice,i+10,uint8(i%3));fresh.activate(i+10);}
        fresh.mint(bob,5000,2); assertEq(fresh.mintedCount(),1000); assertEq(ledger.totalWeight(),1998);
        assertEq(ledger.recoverUnallocated(address(0),total,0,total,block.timestamp+60,REVIEW),total);
        uint256 sum;
        for(uint256 i;i<999;++i){uint256 value=ledger.claimable(i+10,address(0));
            assertEq(value,(i%3+1)*1 ether);sum+=value;}
        assertEq(sum,total);assertEq(ledger.claimable(5000,address(0)),0);
        vm.prank(alice);fresh.transferFrom(alice,bob,10);
        vm.prank(bob);assertEq(ledger.claim(10,address(0)),1 ether);
        assertEq(ledger.liabilities(address(0)),total-1 ether);
        assertEq(ledger.claimable(11,address(0)),2 ether);
    }

    function testRecoveryRetiredReceiverForwardsUnsupportedTokenOnlyToAuthenticatedSuccessor() public {
        (ConversionToken unknown,,)=_unknown(true); unknown.mint(address(r),600e6);
        vm.expectRevert(); r.forwardLate(address(unknown));
        ConversionAccess destination=new ConversionAccess(); RecoveryNFT successor=new RecoveryNFT(address(destination));
        destination.bind(Ids.NFT,address(successor)); RecoveryHandoff handoff=new RecoveryHandoff(address(destination));
        a.bind(Ids.CANONICAL,address(handoff)); a.state(3);
        vm.prank(bob); assertEq(r.forwardLate(address(unknown)),600e6);
        assertEq(unknown.balanceOf(address(r)),0); assertEq(unknown.balanceOf(address(successor.royalties())),600e6);
        assertFalse(successor.royalties().isAsset(address(unknown))); assertEq(unknown.balanceOf(bob),0);
    }
}
