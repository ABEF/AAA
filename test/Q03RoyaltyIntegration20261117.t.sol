// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {InKindNFT} from "./RoyaltyRecovery.t.sol";
import {MockAccess,MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @dev TEST ONLY: exhaust the ledger's existing forwarded optional allowance.
contract Q03RoyaltyGasFault is MockToken {
    bool public failed;
    constructor() MockToken(6) {}
    function setFailed(bool value) external { failed=value; }
    function balanceOf(address who) public view override returns(uint256) {
        if(failed) assembly("memory-safe"){invalid()}
        return super.balanceOf(who);
    }
}

/// @notice COMPONENT integration: actual royalty4/allocator/router and typed
/// InKindNFT/MockAccess setup. No physical LP, full Entry gas, real mint2 sale,
/// whole-coordinator handoff or external-token acceptance is claimed here.
contract Q03RoyaltyIntegration20261117Test is Test {
    uint64 private constant END=1200;
    uint256 private constant OPEN=4800;
    address private constant ALICE=address(0xA11CE);
    address private constant BOB=address(0xB0B);
    address private constant CAROL=address(0xCA701);
    address private constant DAN=address(0xDA1);
    address private constant EVE=address(0xE1E);
    address private constant FRED=address(0xF1ED);

    MockAccess private control;
    InKindNFT private nft;
    ZZZRoyaltyRewards private ledger;
    MockToken private token;
    uint256 private active;
    uint256 private total;
    uint256[7] private weights;
    uint256[7] private first;
    mapping(address=>uint256) private cursor;
    mapping(address=>mapping(uint256=>uint256)) private expected;

    function _setup() private {
        vm.warp(1000);vm.deal(address(this),1 ether);
        control=new MockAccess();nft=new InKindNFT(address(control));ledger=nft.royalties();
        control.bind(Ids.NFT,address(nft));control.seal();
        token=new MockToken(6);nft.add(address(token));
        vm.prank(address(nft));ledger.setMintEnd(END);
        assertEq(ZZZProtocolPolicy(control.protocolPolicy()).royaltySyncGas(),1_000_000);
    }
    function _mint(uint256 id,uint8 rarity,address owner) private {
        nft.mint(owner,id,rarity);weights[id]=uint256(rarity)+1;
    }
    function _join(uint256 id) private {
        assertEq(id,active+1);nft.activate(id);
        first[id]=total+1;total+=weights[id];++active;
        assertEq(ledger.activationCount(),active);assertEq(ledger.totalWeight(),total);
        assertEq(ledger.ticketStart(id),first[id]);assertEq(ledger.weightOf(id),weights[id]);
    }
    function _fund(ZZZRoyaltyRewards target,address asset,uint256 amount) private {
        if(asset==address(0)) {
            (bool ok,)=address(target).call{value:amount}("");assertTrue(ok);
        } else MockToken(asset).mint(address(target),amount);
    }
    // Independent individual-unit walk. The known fixture cohort's gcd unit is
    // an explicit argument; no ledger preview or allocator/tree is its oracle.
    function _model(address asset,uint256 amount,uint256 count,uint256 unit) private {
        uint256 weight;
        for(uint256 id=1;id<=count;++id)weight+=weights[id];
        assertGt(weight,0);assertEq(weight%unit,0);assertEq(cursor[asset]%unit,0);
        uint256 slots=weight/unit;uint256 next=cursor[asset]/unit;
        for(uint256 n;n<amount;++n) {
            bool assigned;
            for(uint256 id=1;id<=count;++id) {
                uint256 start=(first[id]-1)/unit;
                if(next>=start && next<start+weights[id]/unit) {
                    ++expected[asset][id];assigned=true;break;
                }
            }
            assertTrue(assigned);next=(next+1)%slots;
        }
        cursor[asset]=next*unit;
    }
    function _fundSync(ZZZRoyaltyRewards target,address asset,uint256 amount,uint256 unit) private {
        _fund(target,asset,amount);_model(asset,amount,active,unit);target.sync(asset);
        assertEq(target.allocationCursor(asset),cursor[asset]);
    }
    function _assertClaims(ZZZRoyaltyRewards target,address asset) private view {
        uint256 sum;
        for(uint256 id=1;id<=active;++id) {
            assertEq(target.claimable(id,asset),expected[asset][id]);sum+=expected[asset][id];
        }
        assertEq(target.liabilities(asset),sum);assertEq(target.accounted(asset),sum);
        assertEq(target.orphaned(asset),0);assertEq(target.openingPool(asset),0);
        assertEq(target.pending(asset),0);
        uint256 backing=asset==address(0)?address(target).balance:MockToken(asset).balanceOf(address(target));
        assertEq(backing,sum);
    }
    function _claim(InKindNFT ownerBook,ZZZRoyaltyRewards target,uint256 id,address asset) private returns(uint256 paid) {
        address owner=ownerBook.ownerOf(id);
        uint256 beforeBalance=asset==address(0)?owner.balance:MockToken(asset).balanceOf(owner);
        uint256 units=expected[asset][id];
        vm.prank(owner);paid=target.claim(id,asset);assertEq(paid,units);
        expected[asset][id]=0;
        uint256 afterBalance=asset==address(0)?owner.balance:MockToken(asset).balanceOf(owner);
        assertEq(afterBalance-beforeBalance,units);
    }
    function _drain(InKindNFT ownerBook,ZZZRoyaltyRewards target,address asset) private returns(uint256 paid) {
        for(uint256 id=active;id!=0;--id)paid+=_claim(ownerBook,target,id,asset);
        _assertClaims(target,asset);
        for(uint256 id=1;id<=active;++id)assertEq(_claim(ownerBook,target,id,asset),0);
    }

    function testQ03RareCompressedOutstandingCrossesCommunThenLegendaryWithoutOlderRights() public {
        _setup();_mint(1,1,ALICE);_mint(2,1,BOB);_mint(3,1,CAROL);
        _mint(4,0,DAN);_mint(5,2,EVE);
        _join(1);_join(2);_join(3);vm.warp(OPEN);ledger.syncAll();
        // Width3/amount11 takes the complementary branch in the candidate.
        _fundSync(ledger,address(token),11,2);assertEq(_claim(nft,ledger,2,address(token)),4);
        _fund(ledger,address(token),5);_model(address(token),5,3,2);_join(4);
        assertEq(ledger.claimable(4,address(token)),0);_assertClaims(ledger,address(token));
        // Old unit2 credits remain outstanding while all future credit is unit1.
        _fundSync(ledger,address(token),19,1);
        _fund(ledger,address(token),13);_model(address(token),13,4,1);_join(5);
        assertEq(ledger.claimable(5,address(token)),0);_assertClaims(ledger,address(token));
        _fundSync(ledger,address(token),31,1);
        vm.prank(ALICE);nft.transferFrom(ALICE,FRED,1);
        vm.prank(ALICE);vm.expectRevert(ZZZRoyaltyRewards.Unauthorized.selector);ledger.claim(1,address(token));
        _assertClaims(ledger,address(token));assertEq(_drain(nft,ledger,address(token)),75);
        assertEq(token.balanceOf(BOB)+token.balanceOf(CAROL)+token.balanceOf(DAN)+token.balanceOf(EVE)+token.balanceOf(FRED),79);
    }

    function testQ03OpeningGasFaultIncludesGraceCohortButNotCutoffEntrantAfterTransfer() public {
        _setup();Q03RoyaltyGasFault fault=new Q03RoyaltyGasFault();nft.add(address(fault));
        assertEq(ledger.assets(2),address(fault));
        _mint(1,0,ALICE);_mint(2,1,BOB);_mint(3,2,CAROL);_mint(4,0,DAN);_join(1);
        _fund(ledger,address(0),7);_fund(ledger,address(token),13);_fund(ledger,address(fault),17);
        ledger.syncAll();assertEq(ledger.openingPool(address(fault)),17);
        fault.setFailed(true);vm.warp(OPEN-1);_join(2);
        assertEq(ledger.eligibleCount(address(fault)),1);
        _fund(ledger,address(0),5);_fund(ledger,address(token),11);_fund(ledger,address(fault),19);
        _model(address(0),12,2,1);_model(address(token),24,2,1);_model(address(fault),36,2,1);
        vm.warp(OPEN);_join(3);
        assertEq(ledger.eligibleCount(address(fault)),1);
        assertEq(ledger.effectiveEligibleCount(address(fault)),2);
        assertTrue(ledger.eligibleFor(1,address(fault)));assertTrue(ledger.eligibleFor(2,address(fault)));
        assertFalse(ledger.eligibleFor(3,address(fault)));
        assertEq(ledger.claimable(3,address(0)),0);assertEq(ledger.claimable(3,address(token)),0);
        vm.prank(BOB);nft.transferFrom(BOB,EVE,2);
        fault.setFailed(false);ledger.sync(address(fault));
        assertEq(ledger.eligibleCount(address(fault)),3);assertEq(ledger.claimable(3,address(fault)),0);
        _assertClaims(ledger,address(0));_assertClaims(ledger,address(token));_assertClaims(ledger,address(fault));
        vm.prank(BOB);vm.expectRevert(ZZZRoyaltyRewards.Unauthorized.selector);ledger.claim(2,address(fault));
        _fundSync(ledger,address(0),5,1);_fundSync(ledger,address(token),7,1);_fundSync(ledger,address(fault),11,1);
        _join(4);assertEq(ledger.claimable(4,address(fault)),0);
        _fundSync(ledger,address(0),7,1);_fundSync(ledger,address(token),13,1);_fundSync(ledger,address(fault),17,1);
        assertEq(_drain(nft,ledger,address(0)),24);assertEq(_drain(nft,ledger,address(token)),44);
        assertEq(_drain(nft,ledger,address(fault)),64);
    }

    function _seedCanonical() private {
        _setup();_mint(1,0,ALICE);_mint(2,0,BOB);_mint(3,0,CAROL);_mint(4,0,DAN);_mint(5,0,EVE);
        for(uint256 id=1;id<=5;++id)_join(id);
        vm.warp(OPEN);ledger.syncAll();
        // Two >half-prefix receipts with a partial claim in between exercise
        // cancellation-tag redistribution; assertions depend only on units.
        _fundSync(ledger,address(token),9,1);assertEq(_claim(nft,ledger,2,address(token)),2);
        _fundSync(ledger,address(token),4,1);
        _fundSync(ledger,address(0),9,1);assertEq(_claim(nft,ledger,4,address(0)),2);
        _fundSync(ledger,address(0),4,1);
        vm.prank(ALICE);nft.transferFrom(ALICE,FRED,1);
        _assertClaims(ledger,address(token));_assertClaims(ledger,address(0));
    }
    function _importCanonical() private returns(MockAccess destination,InKindNFT nextNFT,ZZZRoyaltyRewards next) {
        destination=new MockAccess();nextNFT=new InKindNFT(address(destination));next=nextNFT.royalties();
        destination.bind(Ids.NFT,address(nextNFT));destination.bind(Ids.CANONICAL,address(this));destination.seal();
        for(uint256 id=1;id<=5;++id)nextNFT.mint(nft.ownerOf(id),id,0);
        control.bind(Ids.CANONICAL,address(this));control.setCanonicalState(1);destination.setCanonicalState(2);
        ledger.canonicalCapture();ledger.canonicalSettle();
        uint256 rows=ledger.canonicalCount();assertEq(rows,18);
        for(uint256 row;row<rows;++row) {
            bytes memory record=ledger.canonicalExport(row);
            if(row>=3) {
                uint256 id=(row-3)/3+1;uint256 subrow=(row-3)%3;
                if(subrow==0) {
                    (uint256 tokenId,uint256 weight,uint256 ordinal,uint256 start)=abi.decode(record,(uint256,uint256,uint256,uint256));
                    assertEq(tokenId,id);assertEq(weight,1);assertEq(ordinal,id);assertEq(start,id);
                } else {
                    (uint256 tokenId,address asset,uint256 amount)=abi.decode(record,(uint256,address,uint256));
                    assertEq(tokenId,id);assertEq(asset,subrow==1?address(0):address(token));
                    assertEq(amount,expected[asset][id]);
                }
            }
            next.canonicalImport(row,record);
        }
        vm.expectRevert();next.canonicalValidate(); // Imported rows alone are not backing.
        for(uint256 index;index<2;++index) {
            (address asset,uint256 backing)=ledger.canonicalBacking(index);
            assertEq(asset,index==0?address(0):address(token));assertEq(backing,11);
            ledger.canonicalRelease(index,address(next));next.canonicalAccept(index,address(ledger));
        }
        next.canonicalValidate();
        _assertClaims(next,address(0));_assertClaims(next,address(token));
    }
    function testQ03FlattenedImportClaimsAccruedAndNewBookUnitsWithoutOldTreeCounter() public {
        _seedCanonical();(MockAccess destination,InKindNFT nextNFT,ZZZRoyaltyRewards next)=_importCanonical();
        // Imported claims are accrued, not reconstructed raw trees/counters.
        next.canonicalActivate();control.setCanonicalState(3);destination.setCanonicalState(0);
        _fundSync(next,address(token),16,1);_fundSync(next,address(0),6,1);
        _assertClaims(next,address(token));_assertClaims(next,address(0));
        assertEq(_drain(nextNFT,next,address(token)),27);assertEq(_drain(nextNFT,next,address(0)),17);
        assertEq(address(ledger).balance,0);assertEq(token.balanceOf(address(ledger)),0);
        vm.prank(FRED);vm.expectRevert();ledger.claim(1,address(token));
    }
    function testQ03FundedAbortRestoresSourceComplementaryCreditsAndFutureClaims() public {
        _seedCanonical();(MockAccess destination,,ZZZRoyaltyRewards next)=_importCanonical();
        for(uint256 index;index<2;++index) {
            next.canonicalRelease(index,address(ledger));ledger.canonicalRestore(index,address(next));
        }
        ledger.canonicalValidate();
        destination.setCanonicalState(4);control.setCanonicalState(0);
        assertEq(address(next).balance,0);assertEq(token.balanceOf(address(next)),0);
        _assertClaims(ledger,address(0));_assertClaims(ledger,address(token));
        _fundSync(ledger,address(token),16,1);_fundSync(ledger,address(0),6,1);
        assertEq(_drain(nft,ledger,address(token)),27);assertEq(_drain(nft,ledger,address(0)),17);
        vm.prank(FRED);vm.expectRevert();next.claim(1,address(token));
    }

    function testQ03ProductionLedgerUintMaxComplementaryDrainAndReturnThreeCycles() public {
        _setup();_mint(1,0,ALICE);_mint(2,2,CAROL);_join(1);_join(2);
        vm.warp(OPEN);ledger.syncAll();
        uint256 maximum=type(uint256).max;token.mint(address(ledger),maximum);
        for(uint256 cycle;cycle<3;++cycle) {
            // Four independent ticket values, not a UINT_MAX-iteration loop.
            // Every cycle uses the same real token supply, not a fresh mint.
            uint256 start=cursor[address(token)];uint256 common;uint256 legendary;
            for(uint256 ticket;ticket<4;++ticket) {
                uint256 units=maximum/4;
                if((ticket+4-start)%4<maximum%4)++units;
                if(ticket==0)common=units;else legendary+=units;
            }
            assertEq(common+legendary,maximum);
            expected[address(token)][1]=common;expected[address(token)][2]=legendary;
            cursor[address(token)]=(start+maximum%4)%4;
            assertEq(ledger.pending(address(token)),maximum);
            // Old cancellation tags must contribute zero to pending previews.
            assertEq(ledger.claimable(1,address(token)),common);
            assertEq(ledger.claimable(2,address(token)),legendary);
            ledger.sync(address(token));assertEq(ledger.allocationCursor(address(token)),cursor[address(token)]);
            _assertClaims(ledger,address(token));
            uint256 paidCommon;uint256 paidLegendary;
            if(cycle%2==0) {
                paidLegendary=_claim(nft,ledger,2,address(token));paidCommon=_claim(nft,ledger,1,address(token));
            } else {
                paidCommon=_claim(nft,ledger,1,address(token));paidLegendary=_claim(nft,ledger,2,address(token));
            }
            assertEq(paidCommon+paidLegendary,maximum);_assertClaims(ledger,address(token));
            assertEq(_claim(nft,ledger,1,address(token)),0);assertEq(_claim(nft,ledger,2,address(token)),0);
            assertEq(token.totalSupply(),maximum);
            if(cycle<2) {
                vm.prank(ALICE);assertTrue(token.transfer(address(ledger),paidCommon));
                vm.prank(CAROL);assertTrue(token.transfer(address(ledger),paidLegendary));
                assertEq(token.balanceOf(ALICE),0);assertEq(token.balanceOf(CAROL),0);
                assertEq(token.balanceOf(address(ledger)),maximum);
            }
        }
    }
}
