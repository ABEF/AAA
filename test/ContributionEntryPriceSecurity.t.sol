// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DirectEntryFixture} from "./AtomicActivationIntegration.t.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";
import {PoolConfig} from "../src/libraries/ZZZTypes.sol";

/// @dev Hostile source-token callback, replacing the removed route callback.
/// Phase1=pull,2=Vault approval,3=approval reset; ordinary EOA approval is inert.
contract DirectEntryCallbackToken is MockToken {
    address public entry;address public target;bytes public data;uint8 public phase;bool private running;
    constructor()MockToken(18){}
    function configure(address e,address t,bytes calldata d,uint8 p)external {entry=e;target=t;data=d;phase=p;}
    function _callback(uint8 p)private {
        if(msg.sender!=entry || running || phase!=p)return;
        running=true;(bool ok,bytes memory reason)=target.call(data);
        if(!ok)assembly("memory-safe"){revert(add(reason,32),mload(reason))}
        running=false;
    }
    function transferFrom(address from,address to,uint256 amount)public override returns(bool){
        bool ok=super.transferFrom(from,to,amount);_callback(1);return ok;
    }
    function approve(address spender,uint256 amount)public override returns(bool){
        bool ok=super.approve(spender,amount);_callback(amount==0?3:2);return ok;
    }
}

contract ContributionEntryPriceSecurityTest is DirectEntryFixture {
    function _armed(address target,bytes memory data,uint8 phase)private returns(DirectEntryCallbackToken token){
        token=new DirectEntryCallbackToken();vm.etch(address(t1),address(token).code);
        token=DirectEntryCallbackToken(address(t1));
        assets.setAsset(address(t1),true,address(t1).codehash,REVIEW);
        token.configure(address(entry),target,data,phase);
    }
    function _assertPriceRollback(uint256 id,uint8 phase)private {
        address source=oracle.policy(oracle.activePolicy(address(t1))).primary.source;
        int256 original=MockFeed(source).answer();uint256 before=t1.balanceOf(alice);
        _armed(source,abi.encodeCall(MockFeed.set,(original+1,block.timestamp,block.timestamp)),phase);
        _reject(alice,_request(id,false));assertEq(MockFeed(source).answer(),original);_unspent(id,before);
    }
    function testDirectPriceCaptureSurvivesPullCallback()public realIntegration {_assertPriceRollback(_mint(alice),1);}
    function testDirectPriceCaptureSurvivesVaultApprovalCallback()public realIntegration {_assertPriceRollback(_mint(alice),2);}
    function testDirectPriceCaptureSurvivesFinalResetCallback()public realIntegration {_assertPriceRollback(_mint(alice),3);}
    function testDirectWiderAndTighterLossMutationRollback()public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        for(uint16 next=0;next<=200;next+=200){
            _armed(address(vault.migrationBudget()),abi.encodeWithSignature("setLossLimits(uint16,uint16)",next,uint16(300)),1);
            vm.mockCall(address(ac),abi.encodeCall(ac.canConfigure,(address(t1))),abi.encode(true));
            _reject(alice,_request(id,false));assertEq(vault.migrationBudget().contributionLossBps(),100);_unspent(id,before);
        }
    }
    function testDirectPoolControlMutationRollback()public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);PoolConfig memory c=registry.get(poolId);c.maxSlippageBps=200;
        _armed(address(registry),abi.encodeCall(registry.configure,(c)),2);
        vm.mockCall(address(ac),abi.encodeCall(ac.canConfigure,(address(t1))),abi.encode(true));
        _reject(alice,_request(id,false));assertEq(registry.get(poolId).maxSlippageBps,100);_unspent(id,before);
    }
    function testDirectOwnerTransferDuringPullRollsBackNFTAndFunds()public realIntegration {
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        _armed(address(nft),abi.encodeCall(nft.transferFrom,(alice,bob,id)),1);
        vm.prank(alice);nft.approve(address(t1),id);_reject(alice,_request(id,false));_unspent(id,before);
    }
}
