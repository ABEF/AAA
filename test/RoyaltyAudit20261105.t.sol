// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {InKindNFT, InKindFaultToken} from "./RoyaltyRecovery.t.sol";
import {MockAccess, MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {ZZZRoyaltyFactory} from "../src/ZZZRoyaltyFactory.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @notice Exact-unit regressions derived from archived royalty3 reproductions.
/// These tests verify supported currencies and the approved rotating-ticket rule;
/// pathological tokens and real marketplace/service qualification remain separate.
contract RoyaltyAudit20261105Test is Test {
    uint64 private constant END = 1200;
    uint256 private constant OPEN = 4800;
    bytes32 private constant REVIEW = keccak256("audited current-weight allocation");
    address private constant ALICE = address(0xa11ce);
    address private constant BOB = address(0xb0b);
    address private constant CAROL = address(0xca701);
    uint256 private transcriptSequence;

    function _ledger() private returns (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) {
        MockAccess control = new MockAccess();
        nft = new InKindNFT(address(control));
        r = nft.royalties();
        control.bind(Ids.NFT, address(nft));
        control.seal();
        token = new MockToken(0);
        nft.add(address(token));
        vm.prank(address(nft));
        r.setMintEnd(END);
    }

    function setUp() public { vm.warp(1000); }

    function testFiniteEndingWholeLegendaryEntitlementsAreFullyClaimable() public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        nft.mint(ALICE, 1, 2); nft.mint(BOB, 2, 2); nft.mint(CAROL, 3, 2);
        nft.activate(1); nft.activate(2); nft.activate(3);
        token.mint(address(r), 3);
        vm.warp(OPEN);
        // The independent rational allocation is exactly one whole unit each.
        assertEq(3 * uint256(3) / uint256(9), 1);
        vm.prank(ALICE); assertEq(r.claim(1, address(token)), 1);
        vm.prank(BOB); assertEq(r.claim(2, address(token)), 1);
        vm.prank(CAROL); assertEq(r.claim(3, address(token)), 1);
        assertEq(r.orphaned(address(token)), 0);
        assertEq(r.openingPool(address(token)), 0);
        assertEq(r.liabilities(address(token)), 0);
        assertEq(r.accounted(address(token)), 0);
        assertEq(token.balanceOf(address(r)), 0);
        // Repeating claims, transferring ownership and allocate-all cannot
        // resurrect any already paid unit.
        vm.prank(ALICE); nft.transferFrom(ALICE, BOB, 1);
        vm.prank(BOB); assertEq(r.claim(1, address(token)), 0);
        assertEq(r.allocateAllUnallocated(address(token), REVIEW), 0);
        assertEq(r.liabilities(address(token)), 0);
    }

    function testSyncSegmentationPreservesExactFiniteFinalPayout() public {
        (InKindNFT splitNFT, ZZZRoyaltyRewards split, MockToken splitToken) = _ledger();
        (InKindNFT batchNFT, ZZZRoyaltyRewards batch, MockToken batchToken) = _ledger();
        splitNFT.mint(ALICE,1,0); splitNFT.mint(BOB,2,1);
        batchNFT.mint(ALICE,1,0); batchNFT.mint(BOB,2,1);
        splitNFT.activate(1); splitNFT.activate(2);
        batchNFT.activate(1); batchNFT.activate(2);
        vm.warp(OPEN); split.sync(address(splitToken)); batch.sync(address(batchToken));
        for (uint256 i; i<6; ++i) { splitToken.mint(address(split),1); split.sync(address(splitToken)); }
        batchToken.mint(address(batch),6); batch.sync(address(batchToken));
        vm.prank(ALICE); uint256 splitA = split.claim(1,address(splitToken));
        vm.prank(BOB); uint256 splitB = split.claim(2,address(splitToken));
        vm.prank(ALICE); uint256 batchA = batch.claim(1,address(batchToken));
        vm.prank(BOB); uint256 batchB = batch.claim(2,address(batchToken));
        assertEq(splitA,batchA); assertEq(splitB,batchB);
        assertEq(splitA+splitB,6); assertEq(batchA+batchB,6);
        assertEq(split.liabilities(address(splitToken)),0);
        assertEq(batch.liabilities(address(batchToken)),0);
        assertEq(splitToken.balanceOf(address(split)),0);
    }

    function testHundredLegendaryWholeUnitPoolIsEntirelyPaid() public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        for (uint256 id=1; id<=100; ++id) {
            nft.mint(address(uint160(0x10000+id)),id,2); nft.activate(id);
        }
        token.mint(address(r),100); vm.warp(OPEN);
        uint256 paid;
        for (uint256 id=1; id<=100; ++id) {
            vm.prank(nft.ownerOf(id)); uint256 claimed=r.claim(id,address(token));
            assertEq(claimed,1); paid+=claimed;
        }
        assertEq(paid,100); assertEq(r.totalWeight(),300);
        assertEq(r.liabilities(address(token)),0);
        assertEq(token.balanceOf(address(r)),0);
        assertEq(r.orphaned(address(token)),0);
    }

    function testDelayedFirstObservationProtectsFrozenCohortButNotReceiptTimestamps() public {
        (InKindNFT nft, ZZZRoyaltyRewards r,) = _ledger();
        InKindFaultToken fault = new InKindFaultToken(); nft.add(address(fault));
        nft.mint(ALICE,1,0); nft.mint(BOB,2,1); nft.activate(1);
        fault.mint(address(r),100); fault.setFailed(true);
        vm.warp(OPEN+1); nft.activate(2);
        // These receipts arrive after Bob's activation but while its currency
        // remains unreadable. The earlier cohort conservatively retains them.
        fault.mint(address(r),200); fault.setFailed(false); r.sync(address(fault));
        assertEq(r.claimable(1,address(fault)),300);
        assertEq(r.claimable(2,address(fault)),0);
        fault.mint(address(r),300);
        assertEq(r.claimable(1,address(fault)),400);
        assertEq(r.claimable(2,address(fault)),200);
    }

    function testAdmissionAfterOpeningRequiresExplicitCurrentWeightAllocation() public {
        (InKindNFT nft, ZZZRoyaltyRewards r,) = _ledger();
        MockToken unknown = new MockToken(0);
        nft.mint(ALICE,1,0); nft.mint(BOB,2,1); nft.activate(1);
        unknown.mint(address(r),300);
        vm.warp(OPEN); nft.activate(2); nft.add(address(unknown));
        assertEq(r.orphaned(address(unknown)),300);
        assertEq(r.claimable(1,address(unknown)),0);
        assertEq(r.claimable(2,address(unknown)),0);
        assertEq(r.allocateAllUnallocated(address(unknown),REVIEW),300);
        vm.prank(ALICE); assertEq(r.claim(1,address(unknown)),100);
        vm.prank(BOB); assertEq(r.claim(2,address(unknown)),200);
        assertEq(unknown.balanceOf(address(r)),0);
    }

    function testNoCutoffParticipantLeavesNoPayableBeneficiaryUntilGovernanceDecision() public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        nft.mint(ALICE,1,0); token.mint(address(r),7); vm.warp(OPEN); r.sync(address(token));
        assertEq(r.orphaned(address(token)),7);
        vm.expectRevert(); r.allocateAllUnallocated(address(token),REVIEW);
        nft.activate(1); assertEq(r.claimable(1,address(token)),0);
        assertEq(r.allocateAllUnallocated(address(token),REVIEW),7);
        vm.prank(ALICE); assertEq(r.claim(1,address(token)),7);
        assertEq(r.accounted(address(token)),0);
    }

    function testSelectedFaultedCurrencyRollsBackBatchButHealthyCurrencyRemainsClaimable() public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        InKindFaultToken fault = new InKindFaultToken(); nft.add(address(fault));
        nft.mint(ALICE,1,0); nft.activate(1);
        token.mint(address(r),7); fault.mint(address(r),9); vm.warp(OPEN);
        fault.setFailed(true);
        ZZZClaimRouter.Claim[] memory entries = new ZZZClaimRouter.Claim[](2);
        entries[0]=ZZZClaimRouter.Claim(1,address(token),true);
        entries[1]=ZZZClaimRouter.Claim(1,address(fault),true);
        ZZZClaimRouter router=nft.claimRouter();
        vm.prank(ALICE); vm.expectRevert(); router.claimBatch(entries);
        assertEq(token.balanceOf(ALICE),0); assertEq(token.balanceOf(address(r)),7);
        vm.prank(ALICE); assertEq(r.claim(1,address(token)),7);
        assertEq(token.balanceOf(ALICE),7);
    }

    function testFuzzEveryFinalUnitIsExactlyPayableWithIndependentTicketModel(uint96 raw) public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        nft.mint(ALICE,1,0); nft.mint(BOB,2,1); nft.mint(CAROL,3,2);
        nft.activate(1); nft.activate(2); nft.activate(3);
        uint256 received=uint256(raw)+1; token.mint(address(r),received); vm.warp(OPEN);
        vm.prank(ALICE); uint256 x=r.claim(1,address(token));
        vm.prank(BOB); uint256 y=r.claim(2,address(token));
        vm.prank(CAROL); uint256 z=r.claim(3,address(token));
        uint256 remaining=received-x-y-z;
        assertEq(remaining,0);
        assertEq(token.balanceOf(address(r)),remaining);
        assertEq(r.liabilities(address(token)),remaining);
        assertEq(r.accounted(address(token)),remaining);
        assertEq(r.orphaned(address(token)),0);
        assertEq(r.openingPool(address(token)),0);
        vm.prank(ALICE); assertEq(r.claim(1,address(token)),0);
        vm.prank(BOB); assertEq(r.claim(2,address(token)),0);
        vm.prank(CAROL); assertEq(r.claim(3,address(token)),0);
        // Independent per-ticket allocation: no tree, global index or fractions.
        uint256[6] memory tickets;
        uint256 q=received/6;
        for (uint256 i; i<6; ++i) tickets[i]=q;
        for (uint256 i; i<received%6; ++i) ++tickets[i];
        assertEq(x,tickets[0]);
        assertEq(y,tickets[1]+tickets[2]);
        assertEq(z,tickets[3]+tickets[4]+tickets[5]);
    }

    function testPaidMaxUintUnitsCanBeReceivedAgainWithoutLifetimeAccumulatorOverflow() public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        nft.mint(ALICE,1,2); nft.activate(1); vm.warp(OPEN);
        token.mint(address(r),type(uint256).max);
        vm.prank(ALICE); assertEq(r.claim(1,address(token)),type(uint256).max);
        assertEq(r.liabilities(address(token)),0);
        vm.prank(ALICE); token.transfer(address(r),type(uint256).max);
        vm.prank(ALICE); assertEq(r.claim(1,address(token)),type(uint256).max);
        assertEq(r.liabilities(address(token)),0);
        assertEq(token.balanceOf(address(r)),0);
    }

    function testThousandMixedNFTsAndOddFinalAmountLeaveNoRemainder() public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        for (uint256 id=1; id<=1000; ++id) {
            uint8 rarity=id<=600 ? 0 : id<=900 ? 1 : 2;
            nft.mint(address(uint160(0x10000+id%37)),id,rarity); nft.activate(id);
        }
        assertEq(r.totalWeight(),1500);
        token.mint(address(r),1507); vm.warp(OPEN);
        uint256 paid;
        // Reverse claim order cannot affect the preassigned ticket recipients.
        for (uint256 id=1000; id!=0; --id) {
            uint256 expected=uint256(nft.rarityOf(id))+1+(id<=7 ? 1 : 0);
            address owner=nft.ownerOf(id); uint256 before=token.balanceOf(owner);
            vm.prank(owner); assertEq(r.claim(id,address(token)),expected);
            assertEq(token.balanceOf(owner)-before,expected); paid+=expected;
        }
        assertEq(paid,1507); assertEq(r.liabilities(address(token)),0);
        assertEq(r.accounted(address(token)),0); assertEq(token.balanceOf(address(r)),0);
    }

    function testGasColdSyncLegendaryClaimAndThirtyTwoEntryRouterBatch() public {
        (InKindNFT nft, ZZZRoyaltyRewards r, MockToken token) = _ledger();
        for (uint256 id=1; id<=1000; ++id) {
            uint8 rarity=id<=600 ? 0 : id<=900 ? 1 : 2;
            nft.mint(ALICE,id,rarity); nft.activate(id);
        }
        token.mint(address(r),100003); vm.warp(OPEN);
        uint256 before=gasleft(); r.sync(address(token));
        emit log_named_uint("full royalty cold initial sync gas",before-gasleft());
        before=gasleft(); vm.prank(ALICE); r.claim(950,address(token));
        emit log_named_uint("full royalty three-ticket claim gas",before-gasleft());
        ZZZClaimRouter.Claim[] memory claims=new ZZZClaimRouter.Claim[](32);
        for (uint256 i; i<32; ++i) claims[i]=ZZZClaimRouter.Claim(951+i,address(token),true);
        ZZZClaimRouter router=nft.claimRouter();
        before=gasleft(); vm.prank(ALICE); router.claimBatch(claims);
        emit log_named_uint("full royalty thirty-two-entry batch gas",before-gasleft());
        token.mint(address(r),100003);
        before=gasleft(); r.sync(address(token));
        emit log_named_uint("full royalty warm rotated sync gas",before-gasleft());
    }

    function _worstPrefix() private returns(InKindNFT nft,ZZZRoyaltyRewards r,MockToken token) {
        (nft,r,token)=_ledger();
        // This prefix fits the actual600/300/100rarity inventory, unlike a
        // hypothetical1000Legendary stress population.
        for(uint256 id=1;id<=811;++id) {
            uint8 rarity=id<=600 ? 0 : id<=810 ? 1 : 2;
            nft.mint(ALICE,id,rarity); nft.activate(id);
        }
        nft.mint(BOB,812,1);
        assertEq(r.totalWeight(),1023);
        token.mint(address(r),513); vm.warp(OPEN); r.sync(address(token));
        for(uint256 id=1;id<=811;++id) { vm.prank(ALICE); r.claim(id,address(token)); }
        assertEq(r.liabilities(address(token)),0);
        assertEq(r.allocationCursor(address(token)),513);
        token.mint(address(r),2044);
    }
    function _coolLedger(ZZZRoyaltyRewards r,address asset) private {
        // allocationBooks slot8 is source/compiler-bound and checked in the
        // corresponding normal0.8.26storage layout before recording evidence.
        bytes32 books=keccak256(abi.encode(asset,uint256(8)));
        bytes32 book=keccak256(abi.encode(uint256(1),books));
        for(uint256 node=1;node<8192;++node)
            vm.coolSlot(address(r),keccak256(abi.encode(node,book)));
        for(uint256 slot;slot<64;++slot) {
            vm.coolSlot(address(r),bytes32(slot));
            vm.coolSlot(address(r),keccak256(abi.encode(asset,slot)));
        }
        vm.cool(address(r)); vm.cool(asset);
    }
    function _coolRecordedContracts(InKindNFT nft,ZZZRoyaltyRewards r,address asset) private {
        // Resolve addresses before cooling any recorded slots. record/accesses
        // captures setup's reads AND writes, including token, NFT and policy
        // storage. The installed Vm.cool also resets the account's storage;
        // explicit slot cooling keeps this measured footprint visible.
        address control=r.canonicalController();
        address policy=MockAccess(control).protocolPolicy();
        address[5] memory targets=[address(nft),address(r),asset,control,policy];
        for(uint256 i;i<targets.length;++i) {
            (bytes32[] memory reads,bytes32[] memory writes)=vm.accesses(targets[i]);
            for(uint256 j;j<reads.length;++j) vm.coolSlot(targets[i],reads[j]);
            for(uint256 j;j<writes.length;++j) vm.coolSlot(targets[i],writes[j]);
            vm.cool(targets[i]);
        }
        _coolLedger(r,asset);
    }
    function testGasWorstRotatedColdFullSyncFitsGovernedOptionalBudget() public {
        vm.record();
        (InKindNFT nft,ZZZRoyaltyRewards r,MockToken token)=_worstPrefix();
        _coolRecordedContracts(nft,r,address(token));
        uint256 before=gasleft(); r.sync(address(token));
        uint256 used=before-gasleft();
        emit log_named_uint("full royalty cooled worst rotated sync gas",used);
        assertLt(used,1000000);
        assertEq(r.liabilities(address(token)),2044);
    }
    function testHealthyOptionalCurrencyIsNotDeferredByExactAllocatorDefaultBudget() public {
        vm.record();
        (InKindNFT nft,ZZZRoyaltyRewards r,MockToken token)=_worstPrefix();
        _coolRecordedContracts(nft,r,address(token));
        uint256 before=gasleft(); nft.activate(812);
        emit log_named_uint("full activation including cooled worst optional sync gas",before-gasleft());
        assertEq(r.eligibleCount(address(token)),812);
        assertEq(r.pending(address(token)),0);
        assertEq(r.claimable(812,address(token)),0);
        token.mint(address(r),1025);
        vm.prank(BOB); assertEq(r.claim(812,address(token)),2);
    }

    function _frozen() private returns (InKindNFT nft,ZZZRoyaltyRewards source,MockToken token) {
        (nft,source,token)=_ledger();
        nft.mint(ALICE,1,1); nft.mint(BOB,2,0); nft.mint(CAROL,3,2);
        // Activation order differs from mint order and must survive V8 import.
        nft.activate(3); nft.activate(1); token.mint(address(source),7);
        vm.warp(OPEN); source.syncAll();
        MockAccess control=MockAccess(source.canonicalController());
        control.bind(Ids.CANONICAL,address(this)); control.setCanonicalState(1);
        source.canonicalCapture(); source.canonicalSettle();
    }

    function _destination(InKindNFT sourceNFT) private returns (MockAccess control,InKindNFT nft,ZZZRoyaltyRewards target) {
        control=new MockAccess(); nft=new InKindNFT(address(control)); target=nft.royalties();
        control.bind(Ids.NFT,address(nft)); control.bind(Ids.CANONICAL,address(this));
        for (uint256 id=1; id<=3; ++id) nft.mint(sourceNFT.ownerOf(id),id,sourceNFT.rarityOf(id));
        control.setCanonicalState(2);
    }
    function _rows(ZZZRoyaltyRewards source,ZZZRoyaltyRewards target,uint256 first,uint256 end) private {
        for (uint256 row=first; row<end; ++row) target.canonicalImport(row,source.canonicalExport(row));
    }
    function _back(ZZZRoyaltyRewards source,ZZZRoyaltyRewards target) private {
        for (uint256 i; i<source.canonicalAssetCount(); ++i) {
            source.canonicalRelease(i,address(target)); target.canonicalAccept(i,address(source));
        }
    }

    function testCanonicalV8ViewFlattenPreservesTicketOrderAndExactBacking() public {
        (InKindNFT sourceNFT,ZZZRoyaltyRewards source,MockToken token)=_frozen();
        (MockAccess control,,ZZZRoyaltyRewards target)=_destination(sourceNFT);
        _rows(source,target,0,source.canonicalCount()); _back(source,target);
        target.canonicalValidate(); target.canonicalActivate(); control.setCanonicalState(0);
        assertEq(target.activationOrdinal(3),1); assertEq(target.ticketStart(3),1);
        assertEq(target.activationOrdinal(1),2); assertEq(target.ticketStart(1),4);
        assertEq(target.allocationCursor(address(token)),2);
        vm.prank(ALICE); assertEq(target.claim(1,address(token)),2);
        vm.prank(CAROL); assertEq(target.claim(3,address(token)),5);
        assertEq(target.liabilities(address(token)),0);
        // Cursor and original ticket mapping determine the NEXT indivisible
        // receipt too; importing in mint order must not change its recipient.
        token.mint(address(target),1);
        assertEq(target.claimable(3,address(token)),1);
        assertEq(target.claimable(1,address(token)),0);
    }

    function testCanonicalAbortWithoutFundingKeepsSourceTreeAndExcludesLateReceiptsFromExport() public {
        (,ZZZRoyaltyRewards source,MockToken token)=_frozen();
        token.mint(address(source),2);
        (,,uint256 exported)=abi.decode(source.canonicalExport(11),(uint256,address,uint256));
        assertEq(exported,5);
        assertEq(source.claimable(3,address(token)),5);
        // No release occurred: the full coordinator's restoration is vacuous.
        // Restoring operating state exposes the intact original tree + late funds.
        MockAccess(source.canonicalController()).setCanonicalState(0);
        vm.prank(ALICE); uint256 a=source.claim(1,address(token));
        vm.prank(CAROL); uint256 c=source.claim(3,address(token));
        assertEq(a+c,9); assertEq(source.liabilities(address(token)),0);
    }

    function testCanonicalRejectsMalformedAssetRowAndOutOfRangeCursor() public {
        (InKindNFT nft,ZZZRoyaltyRewards source,)=_frozen();
        (,,ZZZRoyaltyRewards target)=_destination(nft);
        _rows(source,target,0,2);
        bytes memory valid=source.canonicalExport(2);
        vm.expectRevert(); target.canonicalImport(2,bytes.concat(valid,bytes32(uint256(1))));
        (address asset,,uint256 acc,uint256 liability,uint256 orphan,uint256 backing)=abi.decode(valid,(address,uint256,uint256,uint256,uint256,uint256));
        vm.expectRevert(); target.canonicalImport(2,abi.encode(asset,5,acc,liability,orphan,backing));
        target.canonicalImport(2,valid);
    }

    function testCanonicalRejectsDuplicateOrdinalsAndOverlappingTickets() public {
        (InKindNFT nft,ZZZRoyaltyRewards source,)=_frozen();
        (,,ZZZRoyaltyRewards duplicate)=_destination(nft); _rows(source,duplicate,0,9);
        vm.expectRevert(); duplicate.canonicalImport(9,abi.encode(uint256(3),uint256(3),uint256(2),uint256(1)));
        // Failed row is retryable with the exact authenticated record.
        duplicate.canonicalImport(9,source.canonicalExport(9));
        (,,ZZZRoyaltyRewards overlap)=_destination(nft); _rows(source,overlap,0,3);
        overlap.canonicalImport(3,abi.encode(uint256(1),uint256(2),uint256(2),uint256(2)));
        _rows(source,overlap,4,9);
        bytes memory nextRecord=source.canonicalExport(9);
        vm.expectRevert(); overlap.canonicalImport(9,nextRecord);
    }

    function testCanonicalRejectsOrdinalHoleAfterAllRowsAndFullBacking() public {
        (InKindNFT nft,ZZZRoyaltyRewards source,)=_frozen();
        (,,ZZZRoyaltyRewards target)=_destination(nft); _rows(source,target,0,9);
        target.canonicalImport(9,abi.encode(uint256(3),uint256(3),uint256(3),uint256(1)));
        _rows(source,target,10,source.canonicalCount()); _back(source,target);
        vm.expectRevert(); target.canonicalValidate();
    }

    function testCanonicalRejectsClaimLiabilityMismatchAfterAllRowsAndFullBacking() public {
        (InKindNFT nft,ZZZRoyaltyRewards source,)=_frozen();
        (,,ZZZRoyaltyRewards target)=_destination(nft); _rows(source,target,0,11);
        target.canonicalImport(11,abi.encode(uint256(3),address(source.assets(1)),uint256(4)));
        _back(source,target);
        vm.expectRevert(); target.canonicalValidate();
    }

    function testEqualRareCohortGetsEveryExactlyProportionalWholeUnit() public {
        (InKindNFT nft,ZZZRoyaltyRewards r,MockToken token)=_ledger();
        nft.mint(ALICE,1,1); nft.mint(BOB,2,1); nft.mint(CAROL,3,1);
        nft.activate(1); nft.activate(2); nft.activate(3);
        token.mint(address(r),3); vm.warp(OPEN);
        vm.prank(CAROL); assertEq(r.claim(3,address(token)),1);
        vm.prank(ALICE); assertEq(r.claim(1,address(token)),1);
        vm.prank(BOB); assertEq(r.claim(2,address(token)),1);
        assertEq(r.liabilities(address(token)),0);
    }

    function testGCDChangePreservesOldBookAndExcludesNewUnalignedLegendaryTickets() public {
        (InKindNFT nft,ZZZRoyaltyRewards r,MockToken token)=_ledger();
        nft.mint(ALICE,1,1); nft.mint(CAROL,3,2); nft.mint(BOB,4,2);
        nft.activate(3); token.mint(address(r),3); vm.warp(OPEN); r.sync(address(token));
        assertEq(r.claimable(3,address(token)),3);
        nft.activate(1); nft.activate(4);
        assertEq(r.ticketStart(4),6); // not aligned to the old g=3book.
        assertEq(r.claimable(4,address(token)),0);
        assertEq(r.claimable(1,address(token)),0);
        token.mint(address(r),8);
        vm.prank(BOB); assertEq(r.claim(4,address(token)),3);
        vm.prank(ALICE); assertEq(r.claim(1,address(token)),2);
        vm.prank(CAROL); assertEq(r.claim(3,address(token)),6);
        assertEq(r.liabilities(address(token)),0); assertEq(token.balanceOf(address(r)),0);
    }

    function testGCDChangePreservesOldRareBookAndExcludesNewUnalignedRareTickets() public {
        (InKindNFT nft,ZZZRoyaltyRewards r,MockToken token)=_ledger();
        for(uint256 id=1;id<=3;++id) { nft.mint(ALICE,id,1); nft.activate(id); }
        nft.mint(BOB,4,0); nft.mint(CAROL,5,1);
        token.mint(address(r),3); vm.warp(OPEN); r.sync(address(token));
        nft.activate(4); nft.activate(5); assertEq(r.ticketStart(5),8);
        assertEq(r.claimable(5,address(token)),0);
        token.mint(address(r),9);
        uint256 total;
        for(uint256 id=1;id<=3;++id) { vm.prank(ALICE); total+=r.claim(id,address(token)); }
        assertEq(total,9);
        vm.prank(BOB); assertEq(r.claim(4,address(token)),1);
        vm.prank(CAROL); assertEq(r.claim(5,address(token)),2);
        assertEq(r.liabilities(address(token)),0); assertEq(token.balanceOf(address(r)),0);
    }

    function testCanonicalRejectsCursorNotDivisibleByImportedCohortGCD() public {
        (InKindNFT nft,ZZZRoyaltyRewards source,MockToken token)=_ledger();
        nft.mint(ALICE,1,2); nft.mint(BOB,2,2); nft.mint(CAROL,3,2);
        nft.activate(1); nft.activate(2); nft.activate(3); token.mint(address(source),1);
        vm.warp(OPEN); source.syncAll();
        MockAccess control=MockAccess(source.canonicalController());
        control.bind(Ids.CANONICAL,address(this)); control.setCanonicalState(1);
        source.canonicalCapture(); source.canonicalSettle();
        (,,ZZZRoyaltyRewards target)=_destination(nft); _rows(source,target,0,2);
        (address asset,,uint256 acc,uint256 liability,uint256 orphan,uint256 backing)=
            abi.decode(source.canonicalExport(2),(address,uint256,uint256,uint256,uint256,uint256));
        target.canonicalImport(2,abi.encode(asset,uint256(1),acc,liability,orphan,backing));
        _rows(source,target,3,source.canonicalCount()); _back(source,target);
        vm.expectRevert(); target.canonicalValidate();
    }

    function _transcriptMetadata(string memory name,InKindNFT nft,ZZZRoyaltyRewards r,MockToken token) private {
        string memory key=string.concat("metadata-",name);
        vm.serializeString(key,"case",name);
        vm.serializeString(key,"environment","isolated_foundry_evm");
        vm.serializeBool(key,"real_royalty_ledger",true);
        vm.serializeBool(key,"synthetic_nft_access_token",true);
        vm.serializeBool(key,"public_chain",false);
        vm.serializeAddress(key,"nft",address(nft));
        vm.serializeAddress(key,"ledger",address(r));
        vm.serializeAddress(key,"controller",r.canonicalController());
        vm.serializeAddress(key,"asset",address(token));
        vm.serializeBytes32(key,"ledger_runtime_code_hash",address(r).codehash);
        vm.serializeString(key,"settlement_version",vm.toString(r.ROYALTY_SETTLEMENT_VERSION()));
        vm.serializeString(key,"mint_end",vm.toString(r.mintEnd()));
        vm.serializeString(key,"mint_end_revision",vm.toString(r.mintEndRevision()));
        emit log_named_string("POPL_ROYALTY_METADATA",vm.serializeString(key,"claims_open_at",vm.toString(r.royaltiesOpenAt())));
    }
    function _transcriptEvents(string memory name,string memory phase,ZZZRoyaltyRewards r) private {
        Vm.Log[] memory entries=vm.getRecordedLogs();
        for(uint256 i;i<entries.length;++i) if(entries[i].emitter==address(r)) {
            string memory key=string.concat("event-",name,"-",vm.toString(transcriptSequence++));
            vm.serializeString(key,"case",name); vm.serializeString(key,"phase",phase);
            vm.serializeAddress(key,"emitter",entries[i].emitter);
            vm.serializeBytes32(key,"topics",entries[i].topics);
            vm.serializeString(key,"block_number",vm.toString(block.number));
            vm.serializeString(key,"timestamp",vm.toString(block.timestamp));
            emit log_named_string("POPL_ROYALTY_EVENT",vm.serializeBytes(key,"data",entries[i].data));
        }
    }
    function _transcriptSnapshot(string memory name,string memory phase,InKindNFT nft,
        ZZZRoyaltyRewards r,MockToken token,uint256[] memory ids) private {
        string memory key=string.concat("snapshot-",name,"-",phase);
        string[] memory idValues=new string[](ids.length);
        string[] memory weights=new string[](ids.length);
        string[] memory starts=new string[](ids.length);
        string[] memory ordinals=new string[](ids.length);
        string[] memory claimable=new string[](ids.length);
        address[] memory owners=new address[](ids.length);
        for(uint256 i;i<ids.length;++i) {
            idValues[i]=vm.toString(ids[i]); weights[i]=vm.toString(r.weightOf(ids[i]));
            starts[i]=vm.toString(r.ticketStart(ids[i])); ordinals[i]=vm.toString(r.activationOrdinal(ids[i]));
            claimable[i]=vm.toString(r.claimable(ids[i],address(token))); owners[i]=nft.ownerOf(ids[i]);
        }
        vm.serializeString(key,"case",name); vm.serializeString(key,"phase",phase);
        vm.serializeString(key,"token_ids",idValues); vm.serializeString(key,"weights",weights);
        vm.serializeString(key,"ticket_starts",starts); vm.serializeString(key,"activation_ordinals",ordinals);
        vm.serializeAddress(key,"owners",owners); vm.serializeString(key,"claimable_units",claimable);
        vm.serializeString(key,"activation_count",vm.toString(r.activationCount()));
        vm.serializeString(key,"total_weight",vm.toString(r.totalWeight()));
        vm.serializeString(key,"eligible_count",vm.toString(r.eligibleCount(address(token))));
        vm.serializeString(key,"eligible_weight",vm.toString(r.eligibleWeight(address(token))));
        vm.serializeString(key,"allocation_cursor",vm.toString(r.allocationCursor(address(token))));
        vm.serializeString(key,"raw_balance",vm.toString(token.balanceOf(address(r))));
        vm.serializeString(key,"accounted",vm.toString(r.accounted(address(token))));
        vm.serializeString(key,"liabilities",vm.toString(r.liabilities(address(token))));
        vm.serializeString(key,"orphaned",vm.toString(r.orphaned(address(token))));
        emit log_named_string("POPL_ROYALTY_SNAPSHOT",vm.serializeString(key,"opening_pool",vm.toString(r.openingPool(address(token)))));
    }

    function testEmitActualLedgerTranscriptForBackendOneBasedWireAndV8Rows() public {
        string memory name="mixed-nonmint-order";
        vm.recordLogs();
        (InKindNFT nft,ZZZRoyaltyRewards r,MockToken token)=_ledger();
        _transcriptMetadata(name,nft,r,token); _transcriptEvents(name,"configured",r);
        nft.mint(ALICE,10,1); nft.mint(BOB,20,0); nft.mint(CAROL,30,2);
        vm.recordLogs(); nft.activate(30); nft.activate(10); nft.activate(20);
        _transcriptEvents(name,"activated",r);
        uint256[] memory ids=new uint256[](3);ids[0]=30;ids[1]=10;ids[2]=20;
        token.mint(address(r),7); vm.warp(OPEN); vm.roll(block.number+1);
        vm.recordLogs(); r.syncAll(); _transcriptEvents(name,"initial-seven",r);
        _transcriptSnapshot(name,"initial-seven",nft,r,token,ids);
        token.mint(address(r),5); vm.roll(block.number+1);
        vm.recordLogs(); r.sync(address(token)); _transcriptEvents(name,"later-five",r);
        _transcriptSnapshot(name,"later-five",nft,r,token,ids);
        MockAccess control=MockAccess(r.canonicalController());
        control.bind(Ids.CANONICAL,address(this)); control.setCanonicalState(1);
        vm.recordLogs(); r.canonicalCapture(); r.canonicalSettle(); _transcriptEvents(name,"frozen-settled",r);
        for(uint256 row;row<r.canonicalCount();++row) {
            string memory key=string.concat("wire-",vm.toString(row));
            vm.serializeString(key,"case",name); vm.serializeString(key,"row",vm.toString(row));
            emit log_named_string("POPL_ROYALTY_V8_ROW",vm.serializeBytes(key,"record",r.canonicalExport(row)));
        }
        control.setCanonicalState(0); vm.recordLogs();
        vm.prank(BOB); assertEq(r.claim(20,address(token)),2);
        vm.prank(CAROL); assertEq(r.claim(30,address(token)),6);
        vm.prank(ALICE); assertEq(r.claim(10,address(token)),4);
        _transcriptEvents(name,"claimed-all",r);
        _transcriptSnapshot(name,"claimed-all",nft,r,token,ids);
        assertEq(r.liabilities(address(token)),0); assertEq(token.balanceOf(address(r)),0);
    }

    function testEmitActualLedgerTranscriptForPrefixGCDChange() public {
        string memory name="gcd-three-to-one";
        vm.recordLogs();
        (InKindNFT nft,ZZZRoyaltyRewards r,MockToken token)=_ledger();
        _transcriptMetadata(name,nft,r,token); _transcriptEvents(name,"configured",r);
        nft.mint(ALICE,11,2); nft.mint(BOB,22,2); nft.mint(CAROL,33,1);
        vm.recordLogs(); nft.activate(11); nft.activate(22); _transcriptEvents(name,"early-activated",r);
        uint256[] memory ids=new uint256[](3);ids[0]=11;ids[1]=22;ids[2]=33;
        token.mint(address(r),1); vm.warp(OPEN); vm.roll(block.number+1);
        vm.recordLogs(); r.syncAll(); _transcriptEvents(name,"initial-one",r);
        _transcriptSnapshot(name,"initial-one",nft,r,token,ids);
        vm.roll(block.number+1); vm.recordLogs(); nft.activate(33); _transcriptEvents(name,"late-rare-activated",r);
        token.mint(address(r),7); vm.roll(block.number+1);
        vm.recordLogs(); r.sync(address(token)); _transcriptEvents(name,"later-seven",r);
        _transcriptSnapshot(name,"later-seven",nft,r,token,ids);
        vm.recordLogs();
        vm.prank(CAROL); assertEq(r.claim(33,address(token)),2);
        vm.prank(BOB); assertEq(r.claim(22,address(token)),3);
        vm.prank(ALICE); assertEq(r.claim(11,address(token)),3);
        _transcriptEvents(name,"claimed-all",r);
        _transcriptSnapshot(name,"claimed-all",nft,r,token,ids);
        assertEq(r.liabilities(address(token)),0); assertEq(token.balanceOf(address(r)),0);
    }
}

contract RoyaltyFactoryAuditCaller {
    function create(ZZZRoyaltyFactory factory) external returns(ZZZRoyaltyRewards) { return factory.create(); }
}

contract RoyaltyFactoryAudit20261105Test is Test {
    function testFactoryBindsOnlyFixedCodeTypedNFTAndController() public {
        ZZZRoyaltyFactory factory=new ZZZRoyaltyFactory();
        bytes32 expected=keccak256(type(ZZZRoyaltyRewards).creationCode);
        assertEq(factory.royaltyCodeHash(),expected);
        assertEq(factory.controller(),address(this));
        ZZZRoyaltyRewards first=factory.create();
        assertEq(first.nft(),address(this)); assertEq(first.canonicalController(),address(this));
        RoyaltyFactoryAuditCaller caller=new RoyaltyFactoryAuditCaller();
        ZZZRoyaltyRewards second=caller.create(factory);
        assertEq(second.nft(),address(caller)); assertEq(second.canonicalController(),address(this));
        assertTrue(address(first)!=address(second));
        assertEq(factory.royaltyCodeHash(),expected);
        (bool arbitrary,)=address(factory).call(abi.encodeWithSignature("create(bytes)",hex"60006000f3"));
        assertFalse(arbitrary);
    }

    function testFactoryFailsClosedIfItsAuthenticatedCodePayloadChanges() public {
        ZZZRoyaltyFactory factory=new ZZZRoyaltyFactory(); bytes32 expected=factory.royaltyCodeHash();
        // Test-only code replacement; neither factory nor carrier exposes a mutator.
        bytes memory altered=factory.part0().code;altered[3]^=bytes1(uint8(1));
        vm.etch(factory.part0(),altered);
        assertEq(factory.royaltyCodeHash(),expected);
        vm.expectRevert(ZZZRoyaltyFactory.InvalidCreationCode.selector); factory.create();
    }

    function testGasActualControllerAndNFTConstructorWithImmutableCodeData() public {
        uint256 before=gasleft();
        ZZZAccessController control=new ZZZAccessController(address(0xa11ce),address(0xb0b),address(0xca701));
        emit log_named_uint("actual controller constructor gas including immutable code data",before-gasleft());
        ZZZProtocolPolicy policy=new ZZZProtocolPolicy(address(control),address(0x7ea5));
        control.bindProtocolPolicy(address(policy));
        before=gasleft(); ZZZNFT nft=new ZZZNFT(address(control),"ipfs://exact-audit/");
        emit log_named_uint("actual NFT constructor gas including code-backed exact royalty ledger",before-gasleft());
        assertEq(nft.royaltyRewards().nft(),address(nft));
        assertEq(nft.royaltyRewards().canonicalController(),address(control));
        assertEq(ZZZRoyaltyFactory(control.royaltyFactory()).royaltyCodeHash(),keccak256(type(ZZZRoyaltyRewards).creationCode));
    }
}

/// @dev Actual mint bodies and companion; only authority/provider are mocks.
contract MintSaleEndReviewAudit20261105Test is Test {
    MockAccess private access;
    ZZZNFT private collection;
    ZZZVault private vault;
    MockVRF private provider;
    bool private mutateDeadline;
    address private constant ALICE=address(0xa11ce);
    function setUp() public {
        vm.warp(1000); access=new MockAccess();
        ProtocolPolicyFixture.bind(address(access),address(this));
        vault=new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        collection=new ZZZNFT(address(access),"");
        access.bind(Ids.VAULT,address(vault)); access.bind(Ids.NFT,address(collection));
        access.bind(Ids.VAULT_CANONICAL,address(new ZZZVaultCanonical(address(access),address(vault),block.chainid)));
        provider=new MockVRF();
        ProtocolPolicyFixture.randomness(address(access),address(provider),bytes32(uint256(1)),1,3,500000,false);
        collection.setMintEnd(1200); access.seal();
        vm.deal(ALICE,1 ether); vm.deal(address(this),0);
    }
    receive() external payable { if(mutateDeadline) collection.setMintEnd(1300); }

    function testProceedsCallbackCannotChangeEndAfterNFTGuardAndRollsBackAllMintState() public {
        bytes32 reviewed=vault.mintPolicyFingerprint(); mutateDeadline=true;
        vm.prank(ALICE); vm.expectRevert(ZZZModule.InvalidState.selector);
        vault.mintDormant{value:0.05 ether}(reviewed);
        assertEq(collection.mintedCount(),0); assertEq(vault.sequence(),0);
        assertEq(collection.royaltyRewards().mintEnd(),1200);
        assertEq(collection.royaltyRewards().mintEndRevision(),1);
        assertEq(provider.sequence(),0); assertEq(address(this).balance,0);
        assertEq(ALICE.balance,1 ether);
    }
    function testEndChangeInvalidatesPreparedReviewAndNewReviewStillMints() public {
        bytes32 reviewed=vault.mintPolicyFingerprint(); collection.setMintEnd(1300);
        assertTrue(vault.mintPolicyFingerprint()!=reviewed);
        vm.prank(ALICE); vm.expectRevert(ZZZVaultCanonical.InvalidAmount.selector);
        vault.mintDormant{value:0.05 ether}(reviewed);
        assertEq(collection.mintedCount(),0); assertEq(provider.sequence(),0);
        bytes32 current=vault.mintPolicyFingerprint();
        vm.prank(ALICE); uint256 id=vault.mintDormant{value:0.05 ether}(current);
        assertEq(collection.ownerOf(id),ALICE); assertEq(collection.mintedCount(),1);
        assertEq(collection.royaltyRewards().mintEndRevision(),2);
    }
    function testRestoringEndCannotReviveAnOlderPreparedReview() public {
        bytes32 reviewed=vault.mintPolicyFingerprint();
        collection.setMintEnd(1300); collection.setMintEnd(1200);
        assertEq(collection.royaltyRewards().mintEnd(),1200);
        assertEq(collection.royaltyRewards().mintEndRevision(),3);
        assertTrue(vault.mintPolicyFingerprint()!=reviewed);
        vm.prank(ALICE); vm.expectRevert(ZZZVaultCanonical.InvalidAmount.selector);
        vault.mintDormant{value:0.05 ether}(reviewed);
        assertEq(collection.mintedCount(),0); assertEq(provider.sequence(),0);
    }
    function testSameValueScheduleWriteInvalidatesAnOlderPreparedReview() public {
        bytes32 reviewed=vault.mintPolicyFingerprint(); collection.setMintEnd(1200);
        assertEq(collection.royaltyRewards().mintEndRevision(),2);
        assertTrue(vault.mintPolicyFingerprint()!=reviewed);
        vm.prank(ALICE); vm.expectRevert(ZZZVaultCanonical.InvalidAmount.selector);
        vault.mintDormant{value:0.05 ether}(reviewed);
    }
    function testCompositeFingerprintMatchesIndependentSixWordEncoding() public view {
        ZZZRoyaltyRewards ledger=collection.royaltyRewards();
        bytes32 expected=keccak256(abi.encode(keccak256("ZZZ_MINT_POLICY_WITH_ROYALTY_END_V2"),
            ZZZProtocolPolicy(access.protocolPolicy()).mintFingerprint(),address(collection),address(ledger),
            ledger.mintEnd(),ledger.mintEndRevision()));
        assertEq(vault.mintPolicyFingerprint(),expected);
    }
}
