// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice TEST-ONLY global-liability-bound modular allocation experiment.
/// @dev The caller must authenticate the same currency's complete liability.
/// The original mapping-only layout remains; no duplicate outstanding ledger.
library Q03GlobalBoundAllocation {
    uint256 private constant MAX_TICKETS=3000;
    uint256 private constant FIRST_LEAF=4096;
    struct Book {mapping(uint256=>uint256) pending;}
    error InvalidAllocation();

    function credit(Book storage book,uint256 amount,uint256 weight,uint256 cursor,uint256 globalBefore)
        internal returns(uint256 nextCursor,uint256 globalAfter) {
        _validate(weight,cursor);
        // This returned value is used by the authenticating host. It is an
        // economic addition, not an unchecked modular coefficient operation.
        globalAfter=globalBefore+amount;
        unchecked {
            uint256 quotient=amount/weight;
            uint256 remainder=amount%weight;
            nextCursor=addmod(cursor,remainder,weight);
            uint256 delta=1;
            if(remainder>weight/2){
                ++quotient;remainder=weight-remainder;cursor=nextCursor;
                delta=type(uint256).max;
            }
            if(quotient!=0)_add(book,1,weight,quotient);
            uint256 first=remainder<weight-cursor?remainder:weight-cursor;
            if(first!=0)_add(book,cursor+1,cursor+first,delta);
            uint256 wrapped=remainder-first;
            if(wrapped!=0)_add(book,1,wrapped,delta);
        }
    }

    function addRange(Book storage book,uint256 low,uint256 high,uint256 delta,uint256 globalBefore)
        internal returns(uint256 globalAfter) {
        _interval(low,high);
        uint256 count;unchecked{count=high-low+1;}
        globalAfter=globalBefore+delta*count;
        if(delta!=0)_add(book,low,high,delta);
    }
    function _add(Book storage book,uint256 low,uint256 high,uint256 delta) private {
        unchecked{
            uint256 left=FIRST_LEAF-1+low;uint256 right=FIRST_LEAF-1+high;
            while(left<=right){
                if((left&1)!=0)book.pending[left++]+=delta;
                if((right&1)==0)book.pending[right--]+=delta;
                left>>=1;right>>=1;
            }
        }
    }
    function viewTicket(Book storage book,uint256 ticket) internal view returns(uint256 amount){
        _interval(ticket,ticket);
        unchecked{
            uint256 node=FIRST_LEAF-1+ticket;
            while(node!=0){amount+=book.pending[node];node>>=1;}
        }
    }
    function takeTicket(Book storage book,uint256 ticket,uint256 available) internal returns(uint256 amount){
        _interval(ticket,ticket);
        unchecked{
            uint256 node=1;uint256 path=ticket-1;uint256 carry;
            for(uint256 mask=FIRST_LEAF>>1;mask!=0;mask>>=1){
                uint256 tag=book.pending[node];
                if(tag!=0){carry+=tag;delete book.pending[node];}
                if((path&mask)==0){if(carry!=0)book.pending[(node<<1)|1]+=carry;node<<=1;}
                else{if(carry!=0)book.pending[node<<1]+=carry;node=(node<<1)|1;}
            }
            amount=book.pending[node]+carry;delete book.pending[node];
        }
        if(amount>available)revert InvalidAllocation();
    }
    function _validate(uint256 weight,uint256 cursor) private pure{
        // This also rejects every unsigned cursor when weight is zero.
        if(weight>MAX_TICKETS||cursor>=weight)revert InvalidAllocation();
    }
    function _interval(uint256 low,uint256 high) private pure{
        if(low==0||low>high||high>MAX_TICKETS)revert InvalidAllocation();
    }
}
