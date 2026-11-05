// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ExactRoyaltyAllocation as Allocation} from "../src/libraries/ExactRoyaltyAllocation.sol";

contract ExactRoyaltyAllocationHarness {
    using Allocation for Allocation.Book;
    Allocation.Book private book;
    function credit(uint256 amount,uint256 weight,uint256 cursor) external returns(uint256) {
        return book.credit(amount,weight,cursor);
    }
    function range(uint256 low,uint256 high,uint256 delta) external { book.addRange(low,high,delta); }
    function viewTicket(uint256 ticket) external view returns(uint256) { return book.viewTicket(ticket); }
    function takeTicket(uint256 ticket) external returns(uint256) { return book.takeTicket(ticket); }
    function preview(uint256 amount,uint256 weight,uint256 cursor,uint256 first,uint256 last)
        external pure returns(uint256) { return Allocation.previewShare(amount,weight,cursor,first,last); }
    function nodeValue(uint256 node) external view returns(uint256) { return book.pending[node]; }
}

/// @dev Prior recursive representation retained ONLY as an independent layout
/// comparison. Production uses the bounded iterative implementation.
contract RecursiveAllocationReference {
    mapping(uint256 => uint256) public pending;
    function range(uint256 low,uint256 high,uint256 delta) public { _add(1,1,4096,low,high,delta); }
    function _add(uint256 node,uint256 left,uint256 right,uint256 low,uint256 high,uint256 delta) private {
        if(low<=left && right<=high) { pending[node]+=delta;return; }
        uint256 middle=(left+right)/2;
        if(low<=middle) _add(node*2,left,middle,low,high,delta);
        if(high>middle) _add(node*2+1,middle+1,right,low,high,delta);
    }
    function take(uint256 ticket) external returns(uint256 amount) {
        uint256 node=1;uint256 left=1;uint256 right=4096;uint256 carry;
        while(left!=right) {
            uint256 tag=pending[node];
            if(tag!=0) { carry+=tag;delete pending[node]; }
            uint256 middle=(left+right)/2;
            if(ticket<=middle) {
                if(carry!=0) pending[node*2+1]+=carry;
                node*=2;right=middle;
            } else {
                if(carry!=0) pending[node*2]+=carry;
                node=node*2+1;left=middle+1;
            }
        }
        amount=pending[node]+carry;
        delete pending[node];
    }
}

contract ExactRoyaltyAllocationTest is Test {
    ExactRoyaltyAllocationHarness private allocator;
    function setUp() public { allocator = new ExactRoyaltyAllocationHarness(); }

    function testEveryUnitIsAssignedAndRepeatedClaimsCannotTakeItTwice() public {
        uint256 cursor = allocator.credit(1,6,0);
        assertEq(cursor,1);
        assertEq(allocator.viewTicket(1),1);
        for(uint256 i=2;i<=6;++i) assertEq(allocator.viewTicket(i),0);
        cursor = allocator.credit(5,6,cursor);
        assertEq(cursor,0);
        // One Commun, one Rare and one Legendary occupy1,2,3tickets. Claims
        // occur in reverse NFT order, not the allocation order.
        assertEq(allocator.takeTicket(4)+allocator.takeTicket(5)+allocator.takeTicket(6),3);
        assertEq(allocator.takeTicket(2)+allocator.takeTicket(3),2);
        assertEq(allocator.takeTicket(1),1);
        for(uint256 i=1;i<=6;++i) {
            assertEq(allocator.viewTicket(i),0);
            assertEq(allocator.takeTicket(i),0);
        }
    }

    function testRemainderWrapPreservesAllOtherTicketRights() public {
        assertEq(allocator.credit(4,6,4),2);
        for(uint256 i=1;i<=6;++i) assertEq(allocator.viewTicket(i),i<=2||i>=5 ? 1 : 0);
        assertEq(allocator.takeTicket(6),1);
        assertEq(allocator.takeTicket(1),1);
        assertEq(allocator.viewTicket(2),1);
        assertEq(allocator.viewTicket(5),1);
        assertEq(allocator.takeTicket(5),1);
        assertEq(allocator.takeTicket(2),1);
    }

    function testBatchedAndCombinedReceiptsMatchAtFixedEligibleWeight() public {
        ExactRoyaltyAllocationHarness combined = new ExactRoyaltyAllocationHarness();
        uint256 cursor=4;
        uint256[7] memory amounts=[uint256(0),1,2,11,17,37,1009];
        uint256 total;
        for(uint256 i;i<amounts.length;++i) {
            total+=amounts[i];
            cursor=allocator.credit(amounts[i],17,cursor);
        }
        assertEq(cursor,combined.credit(total,17,4));
        uint256 received;
        for(uint256 i=1;i<=17;++i) {
            assertEq(allocator.viewTicket(i),combined.viewTicket(i));
            uint256 before=allocator.viewTicket(i);
            assertEq(allocator.takeTicket(i),before);
            assertEq(combined.takeTicket(i),before);
            received+=before;
        }
        assertEq(received,total);
    }

    function testNewPrefixTicketsNeverReceivePastIncome() public {
        uint256 cursor=allocator.credit(100,1,0);
        assertEq(cursor,0);
        assertEq(allocator.viewTicket(2),0);
        assertEq(allocator.viewTicket(3),0);
        cursor=allocator.credit(3,3,cursor);
        assertEq(cursor,0);
        assertEq(allocator.takeTicket(1),101);
        assertEq(allocator.takeTicket(2),1);
        assertEq(allocator.takeTicket(3),1);
        assertEq(allocator.preview(100,1,0,2,3),0);
        assertEq(allocator.preview(100,1,0,1,3),100);
    }

    function testMaximumAmountCanBeDrainedThenCreditedAgainWithoutLifetimeOverflow() public {
        for(uint256 weight=1;weight<=3;++weight) {
            uint256 cursor;
            for(uint256 epoch;epoch<3;++epoch) {
                cursor=allocator.credit(type(uint256).max,weight,cursor);
                uint256 paid;
                for(uint256 i=weight;i!=0;--i) paid+=allocator.takeTicket(i);
                assertEq(paid,type(uint256).max);
                for(uint256 i=1;i<=weight;++i) assertEq(allocator.viewTicket(i),0);
            }
        }
    }

    function testMaximumTicketBoundaryDrainsEveryUnitAndLeavesNoFutureCredit() public {
        uint256 amount=100003;
        uint256 next=allocator.credit(amount,3000,2999);
        assertEq(next,(2999+amount%3000)%3000);
        uint256 total;
        // The future-ticket boundary is enforced by the public harness too.
        for(uint256 i=3000;i!=0;--i) {
            total+=allocator.takeTicket(i);
            assertEq(allocator.viewTicket(i),0);
        }
        assertEq(total,amount);
    }

    function testPreviewMatchesActualWithoutMutatingExistingAmounts() public {
        for(uint256 weight=1;weight<=17;++weight) {
            ExactRoyaltyAllocationHarness fresh=new ExactRoyaltyAllocationHarness();
            uint256 cursor=weight-1;
            uint256 amount=weight*3+weight/2;
            fresh.credit(amount,weight,cursor);
            uint256 sum;
            for(uint256 i=1;i<=weight;++i) {
                uint256 expected=fresh.preview(amount,weight,cursor,i,i);
                assertEq(fresh.viewTicket(i),expected);
                assertEq(fresh.takeTicket(i),expected);
                sum+=expected;
            }
            assertEq(sum,amount);
            assertEq(fresh.preview(type(uint256).max,weight,cursor,1,3000),type(uint256).max);
        }
    }

    function testRangeAddsAndClaimingOneTicketDoNotResurrectClearedCredit() public {
        allocator.range(1,2048,7);
        allocator.range(2,3000,11);
        assertEq(allocator.viewTicket(1),7);
        assertEq(allocator.takeTicket(2),18);
        assertEq(allocator.viewTicket(1),7);
        assertEq(allocator.viewTicket(3),18);
        allocator.range(1,3000,2);
        assertEq(allocator.takeTicket(2),2);
        assertEq(allocator.takeTicket(2),0);
        assertEq(allocator.viewTicket(3),20);
        assertEq(allocator.viewTicket(2049),13);
        assertEq(allocator.viewTicket(3000),13);
    }

    function testIterativeAndRecursiveTreesHaveIdenticalOutstandingNodeRepresentation() public {
        RecursiveAllocationReference old=new RecursiveAllocationReference();
        uint256[5] memory low=[uint256(1),2,1025,1,2999];
        uint256[5] memory high=[uint256(3000),2048,2559,1023,3000];
        for(uint256 i;i<low.length;++i) {
            allocator.range(low[i],high[i],11+i);
            old.range(low[i],high[i],11+i);
        }
        for(uint256 node=1;node<8192;++node) assertEq(allocator.nodeValue(node),old.pending(node));
        uint256[6] memory selected=[uint256(1),1499,1500,1501,2999,3000];
        for(uint256 i;i<selected.length;++i) assertEq(allocator.takeTicket(selected[i]),old.take(selected[i]));
        for(uint256 node=1;node<8192;++node) assertEq(allocator.nodeValue(node),old.pending(node));
    }

    function testBoundsRejectEvenForZeroAmountWithoutChangingValidBalances() public {
        allocator.credit(17,3,0);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.credit(0,0,0);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.credit(0,3001,0);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.credit(0,3,3);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.range(0,1,0);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.range(2,1,0);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.range(1,3001,0);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.viewTicket(0);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.takeTicket(3001);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.preview(0,0,0,1,1);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.preview(0,3,3,1,1);
        vm.expectRevert(Allocation.InvalidAllocation.selector);allocator.preview(0,3,0,0,1);
        assertEq(allocator.takeTicket(1)+allocator.takeTicket(2)+allocator.takeTicket(3),17);
    }

    function testFuzzCreditTakeAndGrowingPrefixAgainstAnIndependentPerUnitModel(uint256 seed) public {
        uint256[65] memory model;
        uint256 weight=1;
        uint256 cursor;
        uint256 received;
        uint256 paid;
        for(uint256 step;step<64;++step) {
            seed=uint256(keccak256(abi.encode(seed,step)));
            uint256 operation=seed%4;
            if(operation<2) {
                uint256 amount=(seed>>32)%128;
                uint256 expectedCursor=cursor;
                // Model actual indivisible units directly, without the
                // library's quotient/range decomposition or tree.
                for(uint256 unit;unit<amount;++unit) {
                    ++model[expectedCursor+1];
                    ++expectedCursor;
                    if(expectedCursor==weight) expectedCursor=0;
                }
                uint256 next=allocator.credit(amount,weight,cursor);
                assertEq(next,expectedCursor);
                cursor=next;
                received+=amount;
            } else if(operation==2) {
                uint256 ticket=(seed>>64)%weight+1;
                assertEq(allocator.viewTicket(ticket),model[ticket]);
                uint256 taken=allocator.takeTicket(ticket);
                assertEq(taken,model[ticket]);
                paid+=taken;
                model[ticket]=0;
            } else if(weight<62) {
                uint256 nextWeight=weight+1+(seed>>96)%3;
                for(uint256 ticket=weight+1;ticket<=nextWeight;++ticket) {
                    assertEq(allocator.viewTicket(ticket),0);
                }
                weight=nextWeight;
            }
        }
        uint256 offset=seed%weight;
        for(uint256 i;i<weight;++i) {
            uint256 ticket=(offset+i)%weight+1;
            assertEq(allocator.viewTicket(ticket),model[ticket]);
            paid+=allocator.takeTicket(ticket);
            assertEq(allocator.takeTicket(ticket),0);
        }
        assertEq(paid,received);
    }

    function testGasColdAndWarmNonPowerOfTwoAllocationAndThreeTicketClaim() public {
        uint256 before=gasleft();
        allocator.credit(100003,3000,2911);
        emit log_named_uint("allocator cold credit gas",before-gasleft());
        before=gasleft();
        allocator.credit(100003,3000,2911);
        emit log_named_uint("allocator warm credit gas",before-gasleft());
        before=gasleft();
        uint256 received=allocator.takeTicket(1499)+allocator.takeTicket(1500)+allocator.takeTicket(1501);
        emit log_named_uint("allocator three-ticket take gas",before-gasleft());
        assertGt(received,0);
    }
}
