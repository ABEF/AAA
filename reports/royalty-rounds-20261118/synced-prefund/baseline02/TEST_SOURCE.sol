// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {InKindNFT} from "./RoyaltyRecovery.t.sol";
import {MockAccess,MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZCanonicalLedger} from "../src/base/ZZZCanonicalLedger.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @notice NEW actual-ledger canonical control. Typed InKindNFT/MockAccess are
/// seams; actual whole-coordinator authentication remains separately qualified.
contract RoyaltySyncedPrefundImport20261118Test is Test {
    address private constant A=address(0xA11CE);
    address private constant B=address(0xB0B);
    address private constant C=address(0xCA701);
    receive() external payable {}
    function _pay(ZZZRoyaltyRewards target,uint256 amount)private{
        (bool ok,)=address(target).call{value:amount}("");assertTrue(ok);
    }
    function _claim(ZZZRoyaltyRewards ledger,address owner,uint256 id,address asset,uint256 amount)private{
        uint256 beforeBalance=asset==address(0)?owner.balance:MockToken(asset).balanceOf(owner);
        vm.prank(owner);assertEq(ledger.claim(id,asset),amount);
        assertEq(asset==address(0)?owner.balance-beforeBalance:MockToken(asset).balanceOf(owner)-beforeBalance,amount);
    }
    function _assertReserve(ZZZRoyaltyRewards ledger,MockToken token,uint256 eth,uint256 zzz)private view{
        assertEq(ledger.openingPool(address(0)),0);assertEq(ledger.openingPool(address(token)),0);
        assertEq(ledger.liabilities(address(0)),0);assertEq(ledger.liabilities(address(token)),0);
        assertEq(ledger.orphaned(address(0)),eth);assertEq(ledger.orphaned(address(token)),zzz);
        assertEq(ledger.accounted(address(0)),eth);assertEq(ledger.accounted(address(token)),zzz);
        assertEq(address(ledger).balance,eth);assertEq(token.balanceOf(address(ledger)),zzz);
        assertEq(ledger.pending(address(0)),0);assertEq(ledger.pending(address(token)),0);
    }
    function _overflowAndRetry()private{
        MockAccess control=new MockAccess();InKindNFT nft=new InKindNFT(address(control));ZZZRoyaltyRewards target=nft.royalties();
        control.bind(Ids.NFT,address(nft));control.bind(Ids.CANONICAL,address(this));nft.mint(A,1,0);
        // Boundary fixture only: no operation-time balance mutation occurs.
        vm.deal(address(target),type(uint256).max);target.sync(address(0));
        assertEq(target.openingPool(address(0)),type(uint256).max);
        control.setCanonicalState(2);
        target.canonicalImport(0,abi.encode(uint256(1),uint256(1),uint256(1),uint64(1200),uint8(16)));
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",uint256(0x11)));
        target.canonicalImport(1,abi.encode(address(0),uint256(0),uint256(1),uint256(1),uint256(0),uint256(1)));
        assertEq(target.canonicalAssetCount(),0);
        assertEq(target.liabilities(address(0)),0);assertEq(target.orphaned(address(0)),0);
        assertEq(target.openingPool(address(0)),type(uint256).max);
        // Corrected authenticated row fits the SAME actual prefund. A rejected
        // row must not consume its index or leave a duplicate backing entry.
        target.canonicalImport(1,abi.encode(address(0),uint256(0),uint256(0),uint256(0),uint256(0),uint256(0)));
        assertEq(target.canonicalAssetCount(),1);
        assertEq(target.openingPool(address(0)),0);assertEq(target.orphaned(address(0)),type(uint256).max);
        assertEq(target.accounted(address(0)),type(uint256).max);
    }
    function testSyncedTargetPrefundsImportOncePreserveSourceRightsAndFutureRoyalties()public{
        vm.warp(1000);vm.deal(address(this),1 ether);
        MockAccess sourceControl=new MockAccess();InKindNFT sourceNFT=new InKindNFT(address(sourceControl));
        ZZZRoyaltyRewards source=sourceNFT.royalties();MockToken token=new MockToken(6);
        sourceControl.bind(Ids.NFT,address(sourceNFT));sourceControl.bind(Ids.CANONICAL,address(this));sourceControl.seal();
        sourceNFT.add(address(token));vm.prank(address(sourceNFT));source.setMintEnd(1200);
        sourceNFT.mint(A,1,0);sourceNFT.mint(B,2,2);sourceNFT.activate(1);sourceNFT.activate(2);
        vm.warp(4800);source.syncAll();_pay(source,5);token.mint(address(source),7);source.syncAll();
        _claim(source,A,1,address(0),2);_claim(source,A,1,address(token),2);
        assertEq(source.liabilities(address(0)),3);assertEq(source.liabilities(address(token)),5);
        MockAccess targetControl=new MockAccess();InKindNFT targetNFT=new InKindNFT(address(targetControl));
        ZZZRoyaltyRewards target=targetNFT.royalties();targetControl.bind(Ids.NFT,address(targetNFT));
        targetControl.bind(Ids.CANONICAL,address(this));targetNFT.add(address(token));
        targetNFT.mint(A,1,0);targetNFT.mint(B,2,2);
        assertFalse(targetControl.isSealed());assertEq(targetControl.canonicalState(),0);
        _pay(target,1);token.mint(address(target),2);target.syncAll();
        assertEq(target.openingPool(address(0)),1);assertEq(target.openingPool(address(token)),2);
        assertEq(target.activationCount(),0);assertEq(target.totalWeight(),0);
        sourceControl.setCanonicalState(1);targetControl.setCanonicalState(2);targetControl.seal();
        source.canonicalCapture();source.canonicalSettle();
        for(uint256 row;row<source.canonicalCount();++row)target.canonicalImport(row,source.canonicalExport(row));
        assertEq(target.openingPool(address(0)),0);assertEq(target.openingPool(address(token)),0);
        assertEq(target.orphaned(address(0)),1);assertEq(target.orphaned(address(token)),2);
        assertEq(target.accounted(address(0)),4);assertEq(target.accounted(address(token)),7);
        vm.expectRevert(ZZZCanonicalLedger.CanonicalState.selector);target.canonicalValidate();
        for(uint256 i;i<2;++i){source.canonicalRelease(i,address(target));target.canonicalAccept(i,address(source));}
        // Additional unsynchronized inert receipts must also stay separate.
        _pay(target,4);token.mint(address(target),3);target.canonicalValidate();target.canonicalActivate();
        sourceControl.setCanonicalState(3);targetControl.setCanonicalState(0);
        vm.prank(B);targetNFT.transferFrom(B,C,2);
        _claim(target,A,1,address(0),0);_claim(target,A,1,address(token),0);
        _claim(target,C,2,address(0),3);_claim(target,C,2,address(token),5);_assertReserve(target,token,5,5);
        _pay(target,4);token.mint(address(target),4);target.syncAll();
        _claim(target,A,1,address(0),1);_claim(target,C,2,address(0),3);
        _claim(target,A,1,address(token),1);_claim(target,C,2,address(token),3);_assertReserve(target,token,5,5);
        target.allocateAllUnallocated(address(0),keccak256("reviewed native target-prefund allocation"));
        target.allocateAllUnallocated(address(token),keccak256("reviewed token target-prefund allocation"));
        _claim(target,A,1,address(0),1);_claim(target,C,2,address(0),4);
        _claim(target,A,1,address(token),1);_claim(target,C,2,address(token),4);_assertReserve(target,token,0,0);
        _overflowAndRetry();
    }
}
