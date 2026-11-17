// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {InKindNFT} from "./RoyaltyRecovery.t.sol";
import {MockAccess,MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @dev TEST ONLY: conventional token except a deliberate optional balance read
/// can exhaust the ledger's existing isolated1M subcall. No LP asset is faulted.
contract LaunchTailFaultCurrency is MockToken {
    bool public burnReads;
    constructor() MockToken(6) {}
    function setBurnReads(bool value) external {burnReads=value;}
    function balanceOf(address owner) public view override returns(uint256){
        if(burnReads){while(true){assembly("memory-safe"){pop(gas())}}}
        return super.balanceOf(owner);
    }
}

/// @notice Royalty4 COMPONENT stress only. Actual exact-unit ledger/router code,
/// explicit InKindNFT writer, MockAccess and16 controlled optional currencies.
/// No1000 LP contributions, real mint2 issuance, physical-v4 execution, full
/// activation budget, RPC cold-call estimate or target-chain gas is claimed.
/// Setup/assertion metering is paused; logs measure only the typed component call.
contract LaunchRoyaltyTail20261117Test is Test {
    address private constant ALICE=address(0xA11CE);
    address private constant BOB=address(0xB0B);
    uint64 private constant END=1200;
    uint256 private constant OPEN=4800;
    uint256 private constant CURRENCIES=16;
    MockAccess private control;
    InKindNFT private nft;
    ZZZRoyaltyRewards private royalties;
    MockToken[16] private currencies;
    uint256[1001] private firstTicket;
    uint256[1001] private expectedWeight;
    uint256 private incumbentCount;
    uint256 private incumbentWeight;
    uint256 private nextId;
    LaunchTailFaultCurrency private fault;

    function _populate(bool maximum,bool faulty) private {
        vm.warp(1000);
        control=new MockAccess();nft=new InKindNFT(address(control));royalties=nft.royalties();
        control.bind(Ids.NFT,address(nft));control.seal();
        vm.prank(address(nft));royalties.setMintEnd(END);
        assertEq(royalties.ROYALTY_SETTLEMENT_VERSION(),4);
        assertEq(royalties.assetCapacity(),16);
        assertEq(ZZZProtocolPolicy(control.protocolPolicy()).royaltySyncGas(),1_000_000);
        incumbentCount=maximum?999:811;nextId=incumbentCount+1;
        for(uint256 id=1;id<=nextId;++id){
            // Both populations fit the actual600/300/100 rarity inventory.
            uint8 rarity=maximum?(id<=599?0:id<=899?1:id<=999?2:0):
                (id<=600?0:id<=810?1:id==811?2:1);
            nft.mint(id==nextId?BOB:ALICE,id,rarity);
            expectedWeight[id]=uint256(rarity)+1;
            if(id<=incumbentCount){
                firstTicket[id]=incumbentWeight+1;incumbentWeight+=expectedWeight[id];
                nft.activate(id);
            }
        }
        assertEq(incumbentWeight,maximum?1499:1023);
        assertEq(royalties.activationCount(),incumbentCount);
        assertEq(royalties.totalWeight(),incumbentWeight);
        assertEq(royalties.weightOf(nextId),0);
        for(uint256 i;i<CURRENCIES;++i){
            if(faulty && i==CURRENCIES-1){fault=new LaunchTailFaultCurrency();currencies[i]=fault;}
            else currencies[i]=new MockToken(6);
            nft.add(address(currencies[i]));
            assertEq(royalties.orphaned(address(currencies[i])),0);
        }
        assertEq(royalties.assetCount(),17);assertEq(nft.mintedCount(),nextId);
    }

    function _rotated(bool maximum,bool faulty) private returns(uint256 receipt){
        _populate(maximum,faulty);vm.warp(OPEN);royalties.syncAll();
        // First513unit tickets all belong to distinct Commun NFTs. Drain those
        // exact claims so the later quotient/wrap encounters empty cold tags.
        for(uint256 i;i<CURRENCIES;++i){
            MockToken asset=currencies[i];asset.mint(address(royalties),513);royalties.sync(address(asset));
            uint256 beforeBalance=asset.balanceOf(ALICE);vm.startPrank(ALICE);
            for(uint256 id=1;id<=513;++id)assertEq(royalties.claim(id,address(asset)),1);
            vm.stopPrank();assertEq(asset.balanceOf(ALICE)-beforeBalance,513);
            assertEq(royalties.liabilities(address(asset)),0);assertEq(royalties.accounted(address(asset)),0);
            assertEq(asset.balanceOf(address(royalties)),0);assertEq(royalties.allocationCursor(address(asset)),513);
        }
        receipt=2*incumbentWeight-2;
        for(uint256 i;i<CURRENCIES;++i)currencies[i].mint(address(royalties),receipt);
    }

    function _measureActivation(string memory label) private returns(uint256 used){
        address policy=control.protocolPolicy();
        // Installed Vm.cool resets account and accessed-storage warmth. Final
        // full-call/RPC qualification must separately use naturally cold calls.
        vm.cool(address(nft));vm.cool(address(royalties));vm.cool(address(control));vm.cool(policy);
        for(uint256 i;i<CURRENCIES;++i)vm.cool(address(currencies[i]));
        vm.resumeGasMetering();uint256 beforeGas=gasleft();nft.activate(nextId);used=beforeGas-gasleft();vm.pauseGasMetering();
        emit log_named_uint(label,used);
        assertEq(royalties.activationCount(),incumbentCount+1);
        assertEq(royalties.totalWeight(),incumbentWeight+expectedWeight[nextId]);
        assertEq(royalties.weightOf(nextId),expectedWeight[nextId]);
    }

    // Independent quotient/remainder arithmetic over permanent one-based
    // tickets. No allocator preview or ledger claimable value is its oracle.
    function _expected(uint256 id,uint256 amount,uint256 cursor) private view returns(uint256 value){
        uint256 weight=expectedWeight[id];value=(amount/incumbentWeight)*weight;
        uint256 remainder=amount%incumbentWeight;
        for(uint256 t=firstTicket[id];t<firstTicket[id]+weight;++t){
            uint256 distance=(t-1+incumbentWeight-cursor)%incumbentWeight;
            if(distance<remainder)++value;
        }
    }
    function _checkIncumbents(address asset,uint256 amount,uint256 cursor) private view {
        uint256 sum;
        for(uint256 id=1;id<=incumbentCount;++id){
            uint256 expected=_expected(id,amount,cursor);
            assertEq(royalties.claimable(id,asset),expected);sum+=expected;
        }
        assertEq(sum,amount);assertEq(royalties.claimable(nextId,asset),0);
    }
    function _checkAllRecorded(uint256 amount,uint256 cursor) private view {
        for(uint256 i;i<CURRENCIES;++i){
            address asset=address(currencies[i]);_checkIncumbents(asset,amount,cursor);
            assertEq(royalties.pending(asset),0);assertEq(royalties.openingPool(asset),0);
            assertEq(royalties.orphaned(asset),0);assertEq(royalties.liabilities(asset),amount);
            assertEq(royalties.accounted(asset),amount);assertEq(currencies[i].balanceOf(address(royalties)),amount);
            assertEq(royalties.eligibleCount(asset),incumbentCount+1);
            assertTrue(royalties.eligibleFor(nextId,asset));
        }
    }

    function testLaunchRoyaltyTail811RotatedSixteenHealthyColdActivation() public {
        vm.pauseGasMetering();uint256 receipt=_rotated(false,false);
        _measureActivation("COMPONENT16 healthy811/weight1023 rotated cold activation gas");
        _checkAllRecorded(receipt,513);vm.resumeGasMetering();
    }
    function testLaunchRoyaltyTail999MixedStockSixteenHealthyColdActivation() public {
        vm.pauseGasMetering();uint256 receipt=_rotated(true,false);
        _measureActivation("COMPONENT16 healthy999/weight1499 rotated cold activation gas");
        _checkAllRecorded(receipt,513);vm.resumeGasMetering();
    }
    function testLaunchRoyaltyTailSixteenFirstOpeningAllocationExcludesCutoffEntrant() public {
        vm.pauseGasMetering();_populate(false,false);
        // Both a pre-opening pool and not-yet-synchronized receipt must be
        // assigned to the old cutoff cohort, not the late activation.
        for(uint256 i;i<CURRENCIES;++i){
            currencies[i].mint(address(royalties),513);royalties.sync(address(currencies[i]));
            assertEq(royalties.openingPool(address(currencies[i])),513);
            currencies[i].mint(address(royalties),1531);
        }
        vm.warp(OPEN);
        _measureActivation("COMPONENT16 first-opening811/weight1023 cold activation gas");
        _checkAllRecorded(2044,0);vm.resumeGasMetering();
    }
    function testLaunchRoyaltyTailLastGasFaultDefersOnlyCurrencyThenRecoversOldCohort() public {
        vm.pauseGasMetering();uint256 receipt=_rotated(false,true);
        fault.setBurnReads(true);
        _measureActivation("COMPONENT16 last1Mfault/15healthy rotated cold activation gas");
        assertFalse(royalties.eligibleFor(nextId,address(fault)));
        assertEq(royalties.eligibleCount(address(fault)),incumbentCount);
        // Fault removal is an explicit external-token recovery, not mutation
        // of the royalty ledger or an assertion that every real token recovers.
        fault.setBurnReads(false);
        assertEq(royalties.pending(address(fault)),receipt);
        assertEq(royalties.liabilities(address(fault)),0);
        _checkIncumbents(address(fault),receipt,513);
        royalties.sync(address(fault));_checkAllRecorded(receipt,513);
        uint256 future=incumbentWeight+expectedWeight[nextId];fault.mint(address(royalties),future);royalties.sync(address(fault));
        uint256 beforeBob=fault.balanceOf(BOB);vm.prank(BOB);
        assertEq(royalties.claim(nextId,address(fault)),expectedWeight[nextId]);
        assertEq(fault.balanceOf(BOB)-beforeBob,expectedWeight[nextId]);
        uint256 beforeAlice=fault.balanceOf(ALICE);uint256 paid;
        vm.startPrank(ALICE);
        for(uint256 id=1;id<=incumbentCount;++id){
            uint256 expected=_expected(id,receipt,513)+expectedWeight[id];
            uint256 amount=royalties.claim(id,address(fault));assertEq(amount,expected);paid+=amount;
        }
        vm.stopPrank();assertEq(paid,receipt+incumbentWeight);assertEq(fault.balanceOf(ALICE)-beforeAlice,paid);
        assertEq(royalties.liabilities(address(fault)),0);assertEq(royalties.accounted(address(fault)),0);
        assertEq(fault.balanceOf(address(royalties)),0);assertEq(royalties.pending(address(fault)),0);
        vm.prank(BOB);assertEq(royalties.claim(nextId,address(fault)),0);
        vm.resumeGasMetering();
    }
}
