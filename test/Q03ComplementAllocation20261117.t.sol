// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Q03PositiveAllocationBaseline as Positive, Q03ComplementAllocation as Complement}
    from "./fixtures/Q03ComplementAllocation.sol";

/// @dev EXPERIMENT ONLY. The existing positive engine is a differential control;
/// the separate direct per-ticket arithmetic below is the entitlement oracle.
contract Q03PositiveHarness {
    using Positive for Positive.Book;
    Positive.Book private book;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256) {return book.credit(a,w,c);}
    function range(uint256 l,uint256 h,uint256 d) external {book.addRange(l,h,d);}
    function take(uint256 t) external returns(uint256) {return book.takeTicket(t);}
    function ticket(uint256 t) external view returns(uint256) {return book.viewTicket(t);}
    function tags() external view returns(uint256 n) {for(uint256 i=1;i<8192;++i)if(book.pending[i]!=0)++n;}
}

contract Q03ComplementHarness {
    using Complement for Complement.Book;
    Complement.Book private book;
    function credit(uint256 a,uint256 w,uint256 c) external returns(uint256) {return book.credit(a,w,c);}
    function range(uint256 l,uint256 h,uint256 d) external {book.addRange(l,h,d);}
    function take(uint256 t) external returns(uint256) {return book.takeTicket(t);}
    function ticket(uint256 t) external view returns(uint256) {return book.viewTicket(t);}
    function outstanding() external view returns(uint256) {return book.outstanding;}
    function tags() external view returns(uint256 n) {for(uint256 i=1;i<8192;++i)if(book.pending[i]!=0)++n;}
}

/// @notice Bounded differential experiments, not a production integration or
/// storage/canonical compatibility approval. No unchanged old method executes.
contract Q03ComplementAllocation20261117Test is Test {
    Q03PositiveHarness private old;
    Q03ComplementHarness private candidate;
    uint256[3001] private model;
    uint256 private total;
    event Q03Gas(uint256 weight,uint256 positiveGas,uint256 complementGas,uint256 saved,
        uint256 positiveTags,uint256 complementTags);

    function _fresh() private {
        old=new Q03PositiveHarness();candidate=new Q03ComplementHarness();
        delete model;total=0;
    }
    function _credit(uint256 amount,uint256 weight,uint256 cursor) private returns(uint256 next) {
        next=(cursor+amount%weight)%weight;
        assertEq(old.credit(amount,weight,cursor),next);
        assertEq(candidate.credit(amount,weight,cursor),next);
        total+=amount;
        uint256 q=amount/weight;uint256 r=amount%weight;
        for(uint256 t=1;t<=weight;++t){
            uint256 distance=(t-1+weight-cursor)%weight;
            model[t]+=q+(distance<r?1:0);
        }
        assertEq(candidate.outstanding(),total);
    }
    function _assert(uint256 end) private view {
        uint256 sum;
        for(uint256 t=1;t<=end;++t){
            assertEq(old.ticket(t),model[t]);assertEq(candidate.ticket(t),model[t]);sum+=model[t];
        }
        assertEq(sum,total);assertEq(candidate.outstanding(),total);
    }
    function _take(uint256 ticket) private returns(uint256 amount) {
        amount=model[ticket];assertEq(old.take(ticket),amount);assertEq(candidate.take(ticket),amount);
        model[ticket]=0;total-=amount;assertEq(candidate.outstanding(),total);
        assertEq(old.ticket(ticket),0);assertEq(candidate.ticket(ticket),0);
    }

    function testQ03ComplementColdRotatedCreditsReduceStorageAndPreserveEveryTicket() public {
        vm.pauseGasMetering();
        uint256[3] memory weights=[uint256(1023),1499,3000];
        for(uint256 i;i<weights.length;++i){
            uint256 w=weights[i];uint256 a=2*w-2;uint256 c=513;
            _fresh();vm.cool(address(old));vm.cool(address(candidate));
            vm.resumeGasMetering();uint256 start=gasleft();uint256 beforeCursor=old.credit(a,w,c);
            uint256 oldGas=start-gasleft();start=gasleft();uint256 afterCursor=candidate.credit(a,w,c);
            uint256 newGas=start-gasleft();vm.pauseGasMetering();
            assertEq(beforeCursor,afterCursor);assertEq(afterCursor,(c+a%w)%w);
            assertLt(newGas,oldGas);assertGt(oldGas-newGas,100_000);
            uint256 oldTags=old.tags();uint256 newTags=candidate.tags();assertLt(newTags,oldTags);
            emit Q03Gas(w,oldGas,newGas,oldGas-newGas,oldTags,newTags);
            emit log_named_uint("experimental weight",w);
            emit log_named_uint("positive cold credit gas",oldGas);
            emit log_named_uint("complement cold credit gas",newGas);
            emit log_named_uint("cold credit gas saved",oldGas-newGas);
            emit log_named_uint("positive nonzero tags",oldTags);
            emit log_named_uint("complement nonzero tags",newTags);
            uint256 paid;
            for(uint256 t=1;t<=w;++t){
                uint256 expected=a/w+((t-1+w-c)%w<a%w?1:0);
                assertEq(old.ticket(t),expected);assertEq(candidate.ticket(t),expected);
            }
            if(w<3000){assertEq(candidate.ticket(w+1),0);assertEq(old.ticket(w+1),0);}
            for(uint256 t=w;t!=0;--t){uint256 aOld=old.take(t);assertEq(candidate.take(t),aOld);paid+=aOld;}
            assertEq(paid,a);assertEq(candidate.outstanding(),0);assertEq(candidate.take(1),0);
        }
        vm.resumeGasMetering();
    }

    function testQ03ComplementGrowingPrefixesPartialClaimsAndRecreditMatchIndependentUnits() public {
        vm.pauseGasMetering();_fresh();
        uint256[10] memory weights=[uint256(1),2,3,17,250,811,1023,1499,1500,3000];
        uint256 cursor;
        for(uint256 i;i<weights.length;++i){
            uint256 w=weights[i];cursor%=w;
            cursor=_credit(3*w+(w>1?w-1:0),w,cursor);
            _assert(w);
            if(w<3000){assertEq(candidate.ticket(w+1),0);assertEq(old.ticket(w+1),0);}
            _take(w);_take(1);if(w>3)_take(w/2);
            _assert(w);
            cursor=_credit(w+1,w,cursor);_assert(w);
        }
        for(uint256 t=3000;t!=0;--t)_take(t);
        _assert(3000);assertEq(total,0);
        // Reuse the same books after all prior claims. Neither residual modular
        // coefficients nor future ticket growth may resurrect any old income.
        cursor=_credit(2999,3000,cursor);_assert(3000);
        for(uint256 t=1;t<=3000;++t)_take(t);
        assertEq(total,0);vm.resumeGasMetering();
    }

    function testQ03ComplementUintMaximumCheckedTotalsAndRepeatedDrainingStayExact() public {
        vm.pauseGasMetering();
        uint256[4] memory weights=[uint256(1),4,250,3000];
        for(uint256 j;j<weights.length;++j){
            _fresh();uint256 w=weights[j];uint256 cursor=w-1;
            uint256 epochs=w==250?3:1;
            for(uint256 epoch;epoch<epochs;++epoch){
                cursor=_credit(type(uint256).max,w,cursor);_assert(w);
                // UINTMAX/4 has remainder3: the temporary complementary prefix
                // totals UINTMAX+1, yet actual assigned credit remains UINTMAX.
                vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));
                candidate.credit(1,w,cursor);_assert(w);
                for(uint256 t=w;t!=0;--t)_take(t);
                assertEq(total,0);assertEq(candidate.outstanding(),0);
                assertEq(candidate.take(w),0);
            }
        }
        vm.resumeGasMetering();
    }

    function testQ03ComplementRangeBudgetAndInvalidInputsCannotCorruptBacking() public {
        vm.pauseGasMetering();_fresh();
        uint256 delta=type(uint256).max/250;
        old.range(1,250,delta);candidate.range(1,250,delta);
        total=delta*250;for(uint256 t=1;t<=250;++t)model[t]=delta;
        _assert(250);
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));candidate.range(1,250,type(uint256).max);
        _assert(250);
        _credit(type(uint256).max-total,250,249);_assert(250);
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)",0x11));candidate.range(1,1,1);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.credit(0,0,0);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.credit(0,3001,0);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.credit(0,250,250);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.range(0,1,0);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.range(2,1,0);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.range(1,3001,0);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.take(0);
        vm.expectRevert(Complement.InvalidAllocation.selector);candidate.ticket(3001);
        _assert(250);assertEq(candidate.ticket(251),0);
        for(uint256 t=1;t<=250;++t)_take(t);
        assertEq(candidate.outstanding(),0);assertEq(total,0);
        vm.resumeGasMetering();
    }
}
