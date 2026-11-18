// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {IZZZProtocolPolicy as P} from "../src/interfaces/IZZZProtocolPolicy.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";

/// @dev TEST ONLY authority context: mirrors Access's bootstrap/governance and
/// canonical/preparation answers; it does not qualify a full sealed deployment.
contract RoyaltyReadPolicyAccess {
    address private immutable bootstrap=msg.sender;
    address private immutable governance=msg.sender;
    bool public isSealed;
    bool public preparationActive;
    uint8 public canonicalState;
    function canConfigure(address account) external view returns(bool){
        return !preparationActive && ((isSealed && canonicalState==0 && account==governance) ||
            (!isSealed && account==bootstrap));
    }
    function setState(bool sealed_,bool preparation,uint8 canonical) external {
        require(msg.sender==bootstrap);isSealed=sealed_;preparationActive=preparation;canonicalState=canonical;
    }
}

contract RoyaltyBalancePolicy20261118Test is Test {
    RoyaltyReadPolicyAccess private access;
    ZZZProtocolPolicy private policy;
    address private constant RECIPIENT=address(0xCAFE);
    bytes32 private constant REVIEW=keccak256("TEST ONLY isolated royalty read policy");
    event RoyaltyBalanceGasConfigured(uint32 balanceGas,uint64 revision,bytes32 reviewHash);

    function setUp()public {
        access=new RoyaltyReadPolicyAccess();policy=new ZZZProtocolPolicy(address(access),RECIPIENT);
    }
    function _state()private view returns(bytes32){
        return keccak256(abi.encode(policy.royaltyBalanceGas(),policy.gasPolicy(),policy.configurationRevision(),policy.configurationHash()));
    }

    function testRoyaltyReadPolicyDefaultCommitsFiftyKAndRetainsExactGasTupleAndFingerprint()public view {
        assertEq(policy.royaltyBalanceGas(),50000);
        P.GasPolicy memory gas=policy.gasPolicy();
        assertEq(gas.payoutGas,180000);assertEq(gas.sourceCallGas,500000);assertEq(gas.royaltySyncGas,1000000);assertEq(gas.revision,1);
        assertEq(policy.royaltySyncGas(),1000000);
        (bool ok,bytes memory output)=address(policy).staticcall(abi.encodeCall(ZZZProtocolPolicy.gasPolicy,()));
        assertTrue(ok);assertEq(output.length,128,"historical four-word gas tuple is unchanged");
        assertEq(output,abi.encode(gas));
        assertEq(policy.gasFingerprint(),keccak256(abi.encode(address(policy),gas)),"historical gas fingerprint encoding is unchanged");
        assertEq(policy.configurationHash(),keccak256(abi.encode("ZZZ_PROTOCOL_POLICY_V1",block.chainid,address(policy),address(access),
            policy.entryPolicy(),policy.maintenancePolicy(),gas,uint32(50000),policy.salePolicy(),policy.metadataPolicy())));
    }

    function testRoyaltyReadPolicyBoundsRevisionReviewAndExistingSetterRemainIndependent()public {
        bytes32 entry=policy.entryFingerprint();bytes32 maintenance=policy.maintenanceFingerprint();bytes32 mint=policy.mintFingerprint();
        bytes32 oldGas=policy.gasFingerprint();bytes32 oldConfig=policy.configurationHash();
        vm.expectEmit(false,false,false,true,address(policy));emit RoyaltyBalanceGasConfigured(10000,2,REVIEW);
        policy.setRoyaltyBalanceGas(10000,REVIEW);
        assertEq(policy.royaltyBalanceGas(),10000);assertEq(policy.gasPolicy().revision,2);assertEq(policy.configurationRevision(),1);
        assertTrue(policy.gasFingerprint()!=oldGas);assertTrue(policy.configurationHash()!=oldConfig);
        policy.setRoyaltyBalanceGas(1000000,REVIEW);
        assertEq(policy.royaltyBalanceGas(),1000000);assertEq(policy.royaltySyncGas(),1000000);
        policy.setGasPolicy(200000,600000,300000,REVIEW);
        assertEq(policy.royaltyBalanceGas(),1000000,"existing setter cannot silently replace the read budget");
        assertEq(policy.gasPolicy().revision,4);assertEq(policy.royaltySyncGas(),300000);
        policy.setRoyaltyBalanceGas(50000,REVIEW);
        assertEq(policy.gasPolicy().revision,5);assertEq(policy.configurationRevision(),4);
        assertTrue(policy.gasFingerprint()!=oldGas,"restoring a value cannot revive an old reviewed revision");
        assertEq(policy.gasFingerprint(),keccak256(abi.encode(address(policy),policy.gasPolicy())));
        assertEq(policy.entryFingerprint(),entry);assertEq(policy.maintenanceFingerprint(),maintenance);assertEq(policy.mintFingerprint(),mint);
    }

    function testRoyaltyReadPolicyRejectsBadBoundsMissingReviewAndUnauthorizedOrFrozenWritesAtomically()public {
        bytes32 beforeState=_state();
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setRoyaltyBalanceGas(9999,REVIEW);assertEq(_state(),beforeState);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setRoyaltyBalanceGas(1000001,REVIEW);assertEq(_state(),beforeState);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);policy.setRoyaltyBalanceGas(50000,bytes32(0));assertEq(_state(),beforeState);
        vm.prank(address(0xBAD));vm.expectRevert(ZZZModule.Unauthorized.selector);policy.setRoyaltyBalanceGas(60000,REVIEW);assertEq(_state(),beforeState);
        access.setState(false,false,2);
        vm.expectRevert(ZZZModule.CanonicalLocked.selector);policy.setRoyaltyBalanceGas(60000,REVIEW);assertEq(_state(),beforeState);
        access.setState(false,true,0);
        vm.expectRevert(ZZZModule.Unauthorized.selector);policy.setRoyaltyBalanceGas(60000,REVIEW);assertEq(_state(),beforeState);
        access.setState(true,false,0);
        vm.prank(address(0xBAD));vm.expectRevert(ZZZModule.Unauthorized.selector);policy.setRoyaltyBalanceGas(60000,REVIEW);assertEq(_state(),beforeState);
        policy.setRoyaltyBalanceGas(60000,REVIEW);assertEq(policy.royaltyBalanceGas(),60000);
        assertEq(policy.gasPolicy().revision,2);assertEq(policy.royaltySyncGas(),1000000);
    }
}
