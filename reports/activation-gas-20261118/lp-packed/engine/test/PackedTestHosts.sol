// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {BaselineHost,PackedHost} from "../src/LPHeadlineHosts.sol";
import {ExactLPAllocation} from "../src/ExactLPAllocationOriginal.sol";
import {ExactLPAllocationPacked} from "../src/ExactLPAllocationPacked.sol";
contract TestBaselineHost is BaselineHost {
 function seedPhase(uint8 a,uint256 n,uint128 h,uint256 l)external{tree.books[a].carry[n]=ExactLPAllocation.Carry(h,l);}
}
contract TestPackedHost is PackedHost {
 function seedPhase(uint8 a,uint256 n,uint128 h,uint256 l)external{ExactLPAllocationPacked.writeCarry(tree.books[a].carry[n],h,l);}
 function physicalCarry(uint8 a,uint256 n)external view returns(uint256,uint256){ExactLPAllocationPacked.Carry storage c=tree.books[a].carry[n];return(c.packed,c.wide);}
}
