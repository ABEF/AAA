// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ExactLPAllocation} from "../src/libraries/ExactLPAllocation.sol";
contract CurrentNativeAdapterCompileProbe is ZZZRewards {constructor(address a)ZZZRewards(a){}
    function rawTreeDigest(uint256 bucket) external view returns(bytes32 hash) {
        for(uint256 t;t<2;++t) {
            ExactLPAllocation.Tree storage tree=t==0?ownerBooks[bucket]:collectiveBook;
            hash=keccak256(abi.encode(hash,tree.books[0].outstanding,tree.books[1].outstanding));
            for(uint256 node=1;node<=2023;++node) {
                (uint128 high0,uint256 low0)=ExactLPAllocation.readCarry(tree.books[0].carry[node]);
                (uint128 high1,uint256 low1)=ExactLPAllocation.readCarry(tree.books[1].carry[node]);
                hash=keccak256(abi.encode(hash,tree.weights[node],tree.books[0].pending[node],
                    high0,low0,tree.books[1].pending[node],high1,low1));
            }
        }
    }
}
contract ExactLPAllocationHarness {
    using ExactLPAllocation for ExactLPAllocation.Tree;
    ExactLPAllocation.Tree private tree;
    function setWeight(uint256 ordinal,uint256 weight) external returns(uint256){return tree.setWeight(ordinal,weight);}
    function credit(uint8 asset,uint256 amount)external{tree.credit(_asset(asset),amount);}
    function take(uint8 asset,uint256 ordinal)external returns(uint256){return tree.take(_asset(asset),ordinal);}
    function claimable(uint8 asset,uint256 ordinal)external view returns(uint256){return tree.claimable(_asset(asset),ordinal);}
    function outstanding(uint8 asset)external view returns(uint256){return tree.outstanding(_asset(asset));}
    function totalWeight()external view returns(uint256){return tree.totalWeight();}
    function weightOf(uint256 ordinal)external view returns(uint256){return tree.weightOf(ordinal);}
    function split(uint256 amount,uint256 left,uint256 total,uint128 high,uint256 low)
        external pure returns(uint256,uint256,uint128,uint256){return ExactLPAllocation.split(amount,left,total,high,low);}
    function node(uint8 asset,uint256 index)external view returns(uint256 weight,uint256 pending,uint128 high,uint256 low){
        require(index!=0&&index<2048);ExactLPAllocation.Book storage b=tree.books[uint256(_asset(asset))];
        (high,low)=ExactLPAllocation.readCarry(b.carry[index]);
        return(tree.weights[index],b.pending[index],high,low);
    }
    // Complete bounded state digest is test-only. No production operation walks
    // every NFT/node to credit fees, claim one leaf or change one weight.
    function digest()external view returns(bytes32 value){
        value=keccak256(abi.encode(tree.books[0].outstanding,tree.books[1].outstanding));
        for(uint256 i=1;i<2048;++i){
            (uint128 high0,uint256 low0)=ExactLPAllocation.readCarry(tree.books[0].carry[i]);
            (uint128 high1,uint256 low1)=ExactLPAllocation.readCarry(tree.books[1].carry[i]);
            value=keccak256(abi.encode(value,tree.weights[i],tree.books[0].pending[i],high0,low0,
                tree.books[1].pending[i],high1,low1));
        }
    }
    function _asset(uint8 asset)private pure returns(ExactLPAllocation.Asset){require(asset<2,"TEST ONLY unknown asset");return ExactLPAllocation.Asset(asset);}
}

