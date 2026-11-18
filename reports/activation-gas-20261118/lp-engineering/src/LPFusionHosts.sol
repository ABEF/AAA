// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ExactLPAllocation} from "./ExactLPAllocationOriginal.sol";
import {ExactLPAllocationFused} from "./ExactLPAllocationFused.sol";
contract BaselineHost {
    using ExactLPAllocation for ExactLPAllocation.Tree;
    ExactLPAllocation.Tree internal tree;
    function setWeight(uint256 o,uint256 w)external returns(uint256){return tree.setWeight(o,w);}
    function credit(uint8 a,uint256 n)external{tree.credit(ExactLPAllocation.Asset(a),n);}
    function take(uint8 a,uint256 o)external returns(uint256){return tree.take(ExactLPAllocation.Asset(a),o);}
    function claimable(uint8 a,uint256 o)external view returns(uint256){return tree.claimable(ExactLPAllocation.Asset(a),o);}
    function outstanding(uint8 a)external view returns(uint256){return tree.outstanding(ExactLPAllocation.Asset(a));}
    function totalWeight()external view returns(uint256){return tree.totalWeight();}
    function weightOf(uint256 o)external view returns(uint256){return tree.weightOf(o);}
    function node(uint8 a,uint256 n)external view returns(uint256,uint256,uint128,uint256){ExactLPAllocation.Book storage b=tree.books[a];return(tree.weights[n],b.pending[n],b.carry[n].high,b.carry[n].low);}
    function digest()external view returns(bytes32 v){v=keccak256(abi.encode(tree.books[0].outstanding,tree.books[1].outstanding));for(uint256 n=1;n<2048;++n)v=keccak256(abi.encode(v,tree.weights[n],tree.books[0].pending[n],tree.books[0].carry[n].high,tree.books[0].carry[n].low,tree.books[1].pending[n],tree.books[1].carry[n].high,tree.books[1].carry[n].low));}
}
contract FusedHost {
    using ExactLPAllocationFused for ExactLPAllocationFused.Tree;
    ExactLPAllocationFused.Tree internal tree;
    function setWeight(uint256 o,uint256 w)external returns(uint256){return tree.setWeight(o,w);}
    function credit(uint8 a,uint256 n)external{tree.credit(ExactLPAllocationFused.Asset(a),n);}
    function take(uint8 a,uint256 o)external returns(uint256){return tree.take(ExactLPAllocationFused.Asset(a),o);}
    function claimable(uint8 a,uint256 o)external view returns(uint256){return tree.claimable(ExactLPAllocationFused.Asset(a),o);}
    function outstanding(uint8 a)external view returns(uint256){return tree.outstanding(ExactLPAllocationFused.Asset(a));}
    function totalWeight()external view returns(uint256){return tree.totalWeight();}
    function weightOf(uint256 o)external view returns(uint256){return tree.weightOf(o);}
    function node(uint8 a,uint256 n)external view returns(uint256,uint256,uint128,uint256){ExactLPAllocationFused.Book storage b=tree.books[a];return(tree.weights[n],b.pending[n],b.carry[n].high,b.carry[n].low);}
    function digest()external view returns(bytes32 v){v=keccak256(abi.encode(tree.books[0].outstanding,tree.books[1].outstanding));for(uint256 n=1;n<2048;++n)v=keccak256(abi.encode(v,tree.weights[n],tree.books[0].pending[n],tree.books[0].carry[n].high,tree.books[0].carry[n].low,tree.books[1].pending[n],tree.books[1].carry[n].high,tree.books[1].carry[n].low));}
}
