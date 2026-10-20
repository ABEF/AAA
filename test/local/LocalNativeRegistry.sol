// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZModule} from "../../src/base/ZZZModule.sol";
import {ZZZActivationAssets} from "../../src/ZZZActivationAssets.sol";
import {ZZZActivationEntry} from "../../src/ZZZActivationEntry.sol";
import {Ids, PoolConfig} from "../../src/libraries/ZZZTypes.sol";

/// @dev LOCAL ONLY: substitutes native venue admission, never production pins.
/// Entry, Vault, budgets and ledgers are unmodified. The mock venue accounts in
/// WETH/ZZZ while Entry receives ETH and wraps atomically within the same call.
contract LocalNativeRegistry is ZZZModule {
    address public immutable wrapper;
    address public immutable token;
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    bytes32 public contributionPool;
    PoolConfig private config;
    mapping(bytes32 => bool) public exists;

    constructor(address controller, address weth, address zzz) ZZZModule(controller) {
        require(block.chainid == 31337 && weth.code.length > 0 && zzz.code.length > 0 && weth != zzz, "local fixture only");
        wrapper=weth; token=zzz;
        activationAssets=new ZZZActivationAssets(controller,address(this));
        activationEntry=new ZZZActivationEntry(controller,address(this),address(activationAssets));
    }
    function configureNative(PoolConfig calldata next) external onlyGovernance returns(bytes32 id) {
        require(next.key.currency0==address(0) && next.key.currency1==token && next.key.hooks==address(0),"fixture pair");
        require(next.key.tickSpacing==60 && next.key.fee==3000 && next.rangeBps>=100 && next.rangeBps<=5000 && next.triggerBps<next.rangeBps,"fixture strategy");
        id=keccak256(abi.encode(next.key));
        require(contributionPool==bytes32(0)||contributionPool==id,"one fixture pool");
        activationAssets.admitPoolAsset(wrapper);activationAssets.admitPoolAsset(token);
        config=next;contributionPool=id;exists[id]=true;
    }
    function get(bytes32 id) external view returns(PoolConfig memory) {require(exists[id],"unknown pool");return config;}
    function accounting(bytes32 id) public view returns(PoolConfig memory c) {require(exists[id],"unknown pool");c=config;c.key.currency0=wrapper;}
    function nativeAsset(bytes32 id) external view returns(address) {require(exists[id],"unknown pool");return wrapper;}
    function contributionValue(bytes32 id,uint256 a0,uint256 a1) external view returns(uint256) {
        require(exists[id],"unknown pool");
        if(msg.sender==access.module(Ids.VAULT)) {
            uint256 original=activationEntry.sourceValue(id,a0,a1);
            if(original!=0)return original;
        }
        return activationAssets.value(wrapper,a0)+activationAssets.value(token,a1);
    }
}
