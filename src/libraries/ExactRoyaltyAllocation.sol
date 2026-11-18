// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Exact royalty allocation with bounded enrollment cohorts.
/// @dev Lifetime rounds/gross/paid debt are coefficients modulo2^256. Actual
/// receipts and payouts retain checked same-currency liabilities. Fresh round
/// books are not compatible with historical raw tree storage; canonical rows
/// flatten funded per-NFT rights and restore the cursor as an initial offset.
library ExactRoyaltyAllocation {
    // Low16bits: current cursor; next16: initial cursor. Highbit tags a full
    // uint256 round spill; other223 coefficient bits share the common word.
    // No initialized bit is needed: an all-zero book has zero gross exactly.
    struct Book { uint256 packed; uint256 wideRounds; }
    struct Cohorts { mapping(uint256=>uint256) roundsAt; uint16[] ends; }
    error InvalidAllocation();

    function credit(Book storage book,uint256 amount,uint256 weight,uint256 cursor,uint256 globalBefore)
        internal returns(uint256 nextCursor,uint256 globalAfter) {
        _validate(weight,cursor);
        globalAfter=globalBefore+amount;
        uint256 turns;
        (nextCursor,turns)=_step(amount,weight,cursor);
        // Coefficients are intentionally modulo2^256. Monetary liability above
        // remains checked. Book.slot+1 is the exact full-width overflow spill.
        assembly ("memory-safe") {
            let packed:=sload(book.slot)
            let position:=and(packed,0xffffffff)
            if iszero(packed){position:=shl(16,cursor)}
            let round:=shr(32,packed)
            if shr(255,packed){round:=sload(add(book.slot,1))}
            round:=add(round,turns)
            if shr(223,round){sstore(add(book.slot,1),round) round:=shl(223,1)}
            sstore(book.slot,or(shl(32,round),or(and(position,0xffff0000),nextCursor)))
        }
    }

    function rounds(Book storage book) internal view returns(uint256){return _bookRound(book,book.packed);}
    function _bookRound(Book storage book,uint256 packed) private view returns(uint256){
        uint256 result;
        assembly ("memory-safe") {
            result:=shr(32,packed)
            if shr(255,packed){result:=sload(add(book.slot,1))}
        }
        return result;
    }
    /// @notice Gross coefficient, before birth and paid-debt subtraction.
    function gross(Book storage book,uint256 first,uint256 last) internal view returns(uint256 value){
        _interval(first,last);
        uint256 packed=book.packed;uint256 position=uint32(packed);
        unchecked {
            value=_bookRound(book,packed)*(last-first+1)+_prefix(first,last,position&type(uint16).max)
                -_prefix(first,last,(position>>16)&type(uint16).max);
        }
    }

    /// @notice Append one immutable eligibility boundary, at most1000 total.
    function enroll(Cohorts storage cohort,uint256 end,uint256 rounds) internal {
        if(end==0)return;
        if(end>1000)revert InvalidAllocation();
        uint256 length=cohort.ends.length;
        if(length!=0){
            uint256 last;unchecked{last=cohort.ends[length-1];}
            if(end==last)return;
            if(end<last)revert InvalidAllocation();
        }
        enrollValidated(cohort,end,rounds);
    }
    /// @dev The sole production caller proves end strictly increases in1..1000.
    function enrollValidated(Cohorts storage cohort,uint256 end,uint256 rounds) internal {
        // _enrollTo proves count increases strictly within1..1000. The latest
        // stored end equals that asset's eligibleCount; there is no other caller.
        cohort.roundsAt[end]=rounds;
        cohort.ends.push(uint16(end));
    }
    /// @notice First enrollment boundary at or after the NFT ordinal.
    /// Search is bounded by the1000-NFT cap, never by payment history.
    function birth(Cohorts storage cohort,uint256 ordinal) internal view returns(uint256 end,uint256 rounds){
        if(ordinal==0)revert InvalidAllocation();
        return birthActivated(cohort,ordinal);
    }
    /// @dev The sole production caller has returned for activationOrdinal==0.
    function birthActivated(Cohorts storage cohort,uint256 ordinal) internal view returns(uint256 end,uint256 rounds){
        uint256 low;uint256 length=cohort.ends.length;uint256 high=length;
        unchecked {
            while(low<high){
                uint256 middle=(low+high)>>1;
                if(cohort.ends[middle]<ordinal)low=middle+1;else high=middle;
            }
        }
        if(low==length)revert InvalidAllocation();
        end=cohort.ends[low];rounds=cohort.roundsAt[end];
    }
    /// @notice Preview exactly the old raw-unit cyclic allocation.
    /// Validation and clipped future intervals are unchanged. The round identity
    /// may wrap in its intermediates; its mathematical result is within amount.
    function previewShare(uint256 amount,uint256 weight,uint256 cursor,
        uint256 firstTicket,uint256 lastTicket) internal pure returns(uint256 value) {
        _validate(weight,cursor);_interval(firstTicket,lastTicket);
        if(firstTicket>weight)return 0;
        if(lastTicket>weight)lastTicket=weight;
        (uint256 next,uint256 turns)=_step(amount,weight,cursor);
        unchecked {
            value=turns*(lastTicket-firstTicket+1)+_prefix(firstTicket,lastTicket,next)
                -_prefix(firstTicket,lastTicket,cursor);
        }
    }
    function _step(uint256 amount,uint256 weight,uint256 cursor)
        private pure returns(uint256 next,uint256 turns) {
        unchecked {
            next=cursor+amount%weight;turns=amount/weight;
            if(next>=weight){next-=weight;++turns;}
        }
    }
    function _prefix(uint256 first,uint256 last,uint256 cursor) private pure returns(uint256){
        if(first>cursor)return 0;
        unchecked{return (last<cursor?last:cursor)-first+1;}
    }
    function _validate(uint256 weight,uint256 cursor) private pure {
        if(weight>3000||cursor>=weight)revert InvalidAllocation();
    }
    function _interval(uint256 first,uint256 last) private pure {
        if(first==0||first>last||last>3000)revert InvalidAllocation();
    }
}
