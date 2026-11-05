// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Exact raw-unit allocation to permanent rarity-weight tickets.
/// @dev Internal code only: no deployed helper or external authority. Tags hold
/// outstanding units, not lifetime accrual, so paid units leave the tree.
library ExactRoyaltyAllocation {
    uint256 internal constant MAX_TICKETS = 3000;
    uint256 private constant FIRST_LEAF = 4096;
    struct Book { mapping(uint256 => uint256) pending; }
    error InvalidAllocation();

    /// @notice Allocate every unit to the captured eligible prefix, rotating
    /// indivisible remainders. Fixed-prefix batching preserves final allocation.
    function credit(Book storage book,uint256 amount,uint256 weight,uint256 cursor)
        internal returns(uint256 nextCursor) {
        _validate(weight,cursor);
        uint256 quotient = amount / weight;
        uint256 remainder = amount % weight;
        if(quotient != 0) _add(book,1,weight,quotient);
        uint256 first = remainder < weight-cursor ? remainder : weight-cursor;
        if(first != 0) _add(book,cursor+1,cursor+first,1);
        uint256 wrapped = remainder-first;
        if(wrapped != 0) _add(book,1,wrapped,1);
        // Both terms are<weight<=3000; never add amount to cursor.
        nextCursor = cursor+remainder;
        if(nextCursor >= weight) nextCursor -= weight;
    }

    /// @notice Add units per ticket to one bounded inclusive interval.
    function addRange(Book storage book,uint256 low,uint256 high,uint256 delta) internal {
        _interval(low,high);
        if(delta != 0) _add(book,low,high,delta);
    }

    function _add(Book storage book,uint256 low,uint256 high,uint256 delta) private {
        uint256 left = FIRST_LEAF-1+low;
        uint256 right = FIRST_LEAF-1+high;
        // Standard inclusive dyadic cover. Only endpoints advance, so each
        // level uses at most two tags and at most13levels are visited.
        while(left <= right) {
            if((left & 1) != 0) book.pending[left++] += delta;
            if((right & 1) == 0) book.pending[right--] += delta;
            left >>= 1;
            right >>= 1;
        }
    }

    /// @notice Read a ticket without changing any tag or recipient entitlement.
    function viewTicket(Book storage book,uint256 ticket) internal view returns(uint256 amount) {
        _interval(ticket,ticket);
        uint256 node = FIRST_LEAF-1+ticket;
        while(node != 0) {
            amount += book.pending[node];
            node >>= 1;
        }
    }

    /// @notice Remove exactly one ticket's outstanding units. Carry selected
    /// tags in memory and materialize only the sibling's share; no external
    /// call can observe the temporary path. Other tickets retain all rights.
    function takeTicket(Book storage book,uint256 ticket) internal returns(uint256 amount) {
        _interval(ticket,ticket);
        uint256 node = 1;
        uint256 path = ticket-1;
        uint256 carry;
        for(uint256 mask=FIRST_LEAF>>1;mask != 0;mask >>= 1) {
            uint256 tag = book.pending[node];
            if(tag != 0) {
                carry += tag;
                delete book.pending[node];
            }
            if((path & mask) == 0) {
                if(carry != 0) book.pending[(node<<1)|1] += carry;
                node <<= 1;
            } else {
                if(carry != 0) book.pending[node<<1] += carry;
                node = (node<<1)|1;
            }
        }
        uint256 leaf = book.pending[node];
        amount = leaf + carry;
        if(leaf != 0) delete book.pending[node];
    }

    /// @notice Preview a pending allocation's exact units for an NFT interval.
    /// Future tickets beyond the captured eligible prefix receive zero.
    function previewShare(uint256 amount,uint256 weight,uint256 cursor,
        uint256 firstTicket,uint256 lastTicket) internal pure returns(uint256 value) {
        _validate(weight,cursor);
        _interval(firstTicket,lastTicket);
        uint256 count = _overlap(firstTicket,lastTicket,1,weight);
        value = (amount/weight)*count;
        uint256 remainder = amount%weight;
        uint256 first = remainder < weight-cursor ? remainder : weight-cursor;
        uint256 wrapped = remainder-first;
        if(first != 0) value += _overlap(firstTicket,lastTicket,cursor+1,cursor+first);
        if(wrapped != 0) value += _overlap(firstTicket,lastTicket,1,wrapped);
    }

    function _overlap(uint256 low,uint256 high,uint256 first,uint256 last)
        private pure returns(uint256) {
        if(low > last || high < first) return 0;
        uint256 start = low > first ? low : first;
        uint256 end = high < last ? high : last;
        return end-start+1;
    }
    function _validate(uint256 weight,uint256 cursor) private pure {
        if(weight == 0 || weight > MAX_TICKETS || cursor >= weight) revert InvalidAllocation();
    }
    function _interval(uint256 low,uint256 high) private pure {
        if(low == 0 || low > high || high > MAX_TICKETS) revert InvalidAllocation();
    }
}
