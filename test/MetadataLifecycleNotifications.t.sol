// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {BoundDummy} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {HolderCollectiveExitTest, RejectHolderETH} from "./HolderCollectiveExit.t.sol";

library LifecycleEventChecks {
    bytes32 private constant BATCH=keccak256("BatchMetadataUpdate(uint256,uint256)");
    bytes32 private constant TOKEN=keccak256("MetadataUpdate(uint256)");
    function batches(Vm.Log[] memory logs,address collection) internal pure returns(uint256 count) {
        for(uint256 i;i<logs.length;++i)if(logs[i].emitter==collection && logs[i].topics.length==1 && logs[i].topics[0]==BATCH) {
            (uint256 first,uint256 last)=abi.decode(logs[i].data,(uint256,uint256));
            require(first==0 && last==type(uint256).max,"wrong collection invalidation bounds");++count;
        }
    }
    function tokens(Vm.Log[] memory logs,address collection,uint256 id) internal pure returns(uint256 count) {
        for(uint256 i;i<logs.length;++i)if(logs[i].emitter==collection && logs[i].topics.length==1 &&
            logs[i].topics[0]==TOKEN && abi.decode(logs[i].data,(uint256))==id)++count;
    }
}

interface IMetadataFixtureExecutionPolicy {
    function target(bytes32 pool)external view returns(int24,int24,uint160);
    function validatePrice(bytes32 pool)external view returns(uint160);
}

/// @dev TEST ONLY read-only adapter for the inherited mocked 1:1 venue. The
/// current Oracle requires the fixed token identity and captured execution
/// geometry. Preserve that fixture's explicit price/target seam; do not mock
/// Oracle, ContributionPricing, custody, actual fee allocation or settlement.
contract MetadataLifecycleExecutionFixture {
    address public immutable fixedZZZ;
    IMetadataFixtureExecutionPolicy private immutable policy;
    constructor(address token,address strategy){fixedZZZ=token;policy=IMetadataFixtureExecutionPolicy(strategy);}
    function executionTarget(bytes32 pool)external view returns(int24,int24,uint160){return policy.target(pool);}
    function executionValidatePrice(bytes32 pool)external view returns(uint160){return policy.validatePrice(pool);}
}

/// @dev TEST ONLY malformed fixed-NFT binding; proves atomic lifecycle rollback.
contract RejectLifecycleMetadata {
    address public immutable access;
    constructor(address controller){access=controller;}
    function policyMetadataChanged()external pure{revert("fixture rejects metadata hook");}
}

/// @notice Real controller and NFT notification authority/state writes. Other
/// modules are explicit identity stubs; not a complete economic handoff rehearsal.
contract MetadataLifecycleControllerNotificationsTest is Test {
    ZZZAccessController private controller;
    ZZZNFT private collection;
    address private guardian=address(0x123);
    bytes32 private constant REVIEW=keccak256("TEST ONLY metadata lifecycle review");
    function setUp()public{
        vm.warp(1_000_000);
        controller=new ZZZAccessController(address(this),address(0x456),guardian);
        ProtocolPolicyFixture.bind(address(controller));
        collection=new ZZZNFT(address(controller),"ipfs://lifecycle/",address(new ZZZNFTMetadata(address(controller))));
        controller.bind(Ids.NFT,address(collection));
        bytes32[11] memory ids=[Ids.VAULT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,Ids.STRATEGY,
            Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.ORACLE,Ids.POOLS];
        for(uint256 i;i<ids.length;++i)controller.bind(ids[i],address(new BoundDummy(address(controller))));
        MockVRF vrf=new MockVRF();
        ProtocolPolicyFixture.randomness(address(controller),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        CanonicalFixture.bind(address(controller));controller.seal();
    }
    function _notice()private view returns(ZZZAccessController.PreparationNotice memory){
        return ZZZAccessController.PreparationNotice(block.chainid,address(0xD057),REVIEW,REVIEW);
    }
    function testMetadataLifecycleFixedHookRejectsEveryUnrelatedCaller()public{
        address[5] memory outsiders=[address(this),guardian,address(0x456),controller.module(Ids.VAULT),controller.canonicalHandoff()];
        for(uint256 i;i<outsiders.length;++i){
            vm.prank(outsiders[i]);vm.expectRevert(bytes4(keccak256("Unauthorized()")));collection.policyMetadataChanged();
        }
        address[3] memory allowed=[address(controller),controller.protocolPolicy(),controller.module(Ids.MIGRATION)];
        vm.recordLogs();
        for(uint256 i;i<allowed.length;++i){vm.prank(allowed[i]);collection.policyMetadataChanged();}
        assertEq(LifecycleEventChecks.batches(vm.getRecordedLogs(),address(collection)),3);
        assertEq(collection.mintedCount(),0);assertTrue(controller.isSealed());
    }
    function testMetadataLifecyclePreparationAndCancellationNotifyAfterWrites()public{
        vm.recordLogs();controller.startPreparation(_notice());
        assertTrue(controller.preparationActive());
        assertEq(LifecycleEventChecks.batches(vm.getRecordedLogs(),address(collection)),1);
        bytes32 notice=controller.preparationHash();
        vm.recordLogs();controller.cancelPreparation(notice);
        assertFalse(controller.preparationActive());
        assertEq(LifecycleEventChecks.batches(vm.getRecordedLogs(),address(collection)),1);
        assertEq(collection.mintedCount(),0);
    }
    function testMetadataLifecycleCanonicalStateChangesNotifyIncludingActivationAndCancel()public{
        address handoff=controller.canonicalHandoff();
        uint8[5] memory states=[uint8(2),uint8(0),uint8(1),uint8(0),uint8(4)];
        for(uint256 i;i<states.length;++i){
            vm.recordLogs();vm.prank(handoff);controller.canonicalTransition(states[i],false,true);
            assertEq(controller.canonicalState(),states[i]);
            assertEq(LifecycleEventChecks.batches(vm.getRecordedLogs(),address(collection)),1);
        }
        vm.prank(handoff);vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        controller.canonicalTransition(0,false,true);
        assertEq(controller.canonicalState(),4);
    }
    function testMetadataLifecycleTerminalStartNotifiesDormantCollectionWithoutPrices()public{
        vm.prank(guardian);controller.setPaused(true);
        vm.recordLogs();vm.prank(controller.module(Ids.VAULT));controller.startLPExit();
        assertTrue(controller.lpExitStarted());
        assertEq(LifecycleEventChecks.batches(vm.getRecordedLogs(),address(collection)),1);
        // Bound price/Vault stubs intentionally implement no valuation method.
        assertEq(collection.mintedCount(),0);assertEq(collection.royaltyRewards().totalWeight(),0);
    }
    function testMetadataLifecycleUnboundBootstrapSkipsHookAndWrongHookRollsBackState()public{
        ZZZAccessController empty=new ZZZAccessController(address(this),address(1),address(2));
        address handoff=address(new BoundDummy(address(empty)));empty.bind(Ids.CANONICAL,handoff);
        vm.recordLogs();vm.prank(handoff);empty.canonicalTransition(2,false,false);
        assertEq(empty.canonicalState(),2);assertEq(vm.getRecordedLogs().length,0);
        ZZZAccessController wrong=new ZZZAccessController(address(this),address(1),address(2));
        handoff=address(new BoundDummy(address(wrong)));wrong.bind(Ids.CANONICAL,handoff);
        wrong.bind(Ids.NFT,address(new RejectLifecycleMetadata(address(wrong))));
        vm.prank(handoff);vm.expectRevert(abi.encodeWithSignature("Error(string)","fixture rejects metadata hook"));
        wrong.canonicalTransition(2,false,false);
        assertEq(wrong.canonicalState(),0);assertFalse(wrong.canonicalSettling());
    }
}

/// @notice Reuse the existing real Vault/NFT/settlement fixture, not its test
/// methods. The parent uses mocked venue/prices/VRF; select only the new
/// testMetadataLifecycle* methods rather than rerunning unchanged inherited tests.
contract MetadataLifecycleExitNotificationsTest is HolderCollectiveExitTest {
    bool private metadataExecutionFixtureBound;
    // TEST ONLY decoder for the actual canonical NFT tokenURI, copied from the
    // existing metadata fixture rather than substituting a renderer snapshot.
    function _metadataJSON(uint256 id)private view returns(string memory){
        bytes memory data=bytes(nft.tokenURI(id));uint256 prefix=29;
        bytes memory decoded=new bytes((data.length-prefix)/4*3);uint256 count;
        for(uint256 i=prefix;i<data.length;i+=4){
            uint256 word=(_metadataDigit(data[i])<<18)|(_metadataDigit(data[i+1])<<12)|
                (_metadataDigit(data[i+2])<<6)|_metadataDigit(data[i+3]);
            decoded[count++]=bytes1(uint8(word>>16));
            if(data[i+2]!="=")decoded[count++]=bytes1(uint8(word>>8));
            if(data[i+3]!="=")decoded[count++]=bytes1(uint8(word));
        }
        bytes memory result=new bytes(count);for(uint256 i;i<count;++i)result[i]=decoded[i];
        return string(result);
    }
    function _metadataDigit(bytes1 character)private pure returns(uint256){
        uint8 value=uint8(character);
        if(value>=65 && value<=90)return value-65;
        if(value>=97 && value<=122)return value-71;
        if(value>=48 && value<=57)return value+4;
        if(value==43)return 62;if(value==47)return 63;return 0;
    }
    function _metadataEvolution(string memory json)private pure returns(string memory){
        for(uint256 i;i<12;++i){
            string memory path=string.concat(".attributes[",vm.toString(i),"]");
            if(keccak256(bytes(vm.parseJsonString(json,string.concat(path,".trait_type"))))==keccak256("Evolution"))
                return vm.parseJsonString(json,string.concat(path,".value"));
        }
        revert("missing Evolution attribute");
    }
    function _metadataMint(address owner)private returns(uint256 id){
        bytes32 fingerprint=vault.mintPolicyFingerprint();
        vm.prank(owner);id=vault.mintDormant{value:0.05 ether}(fingerprint);
        vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
    }
    function _metadataActivate(address owner)private returns(uint256 id){
        if(!metadataExecutionFixtureBound){
            MetadataLifecycleExecutionFixture fixture=new MetadataLifecycleExecutionFixture(address(token),ac.module(Ids.STRATEGY));
            vm.mockCall(address(venue),abi.encodeWithSignature("executionStrategy()"),abi.encode(address(fixture)));
            metadataExecutionFixtureBound=true;
        }
        id=_metadataMint(owner);vm.prank(owner);
        vault.activate{value:100 ether}(id,poolId,100 ether,100 ether,1,block.timestamp+100);
    }
    function _metadataBegin()private{ac.setPaused(true);migration.beginCollectiveExit(review);}
    function _metadataReady(uint256 active)private{
        _metadataBegin();migration.closeBucket(vault.nftBucket(active),0,0,block.timestamp+100);migration.allocatePrincipal(32);
    }
    function _metadataIDs(uint256 a,uint256 b)private pure returns(uint256[] memory ids){
        ids=new uint256[](2);ids[0]=a;ids[1]=b;
    }
    function testMetadataLifecycleBucketCloseNotifiesBeforeAnyAllocation()public{
        uint256 active=_metadataActivate(alice);uint256 dormant=_metadataMint(bob);_metadataBegin();
        vm.recordLogs();migration.closeBucket(vault.nftBucket(active),0,0,block.timestamp+100);
        assertEq(LifecycleEventChecks.batches(vm.getRecordedLogs(),address(nft)),1);
        assertEq(uint256(migration.exitPhase()),2);assertEq(migration.allocationCursor(),1);
        (,uint8 stage)=nft.evolution(active);assertEq(stage,4);
        (,stage)=nft.evolution(dormant);assertEq(stage,0);
        assertEq(nft.royaltyRewards().weightOf(active),1);assertEq(nft.royaltyRewards().weightOf(dormant),0);
    }
    function testMetadataLifecycleReadyNotifiesEarlierAllocationsWhenFinalOrdinalDormant()public{
        uint256 a=_metadataActivate(alice);uint256 b=_metadataActivate(bob);uint256 dormant=_metadataMint(alice);
        _metadataBegin();migration.closeBucket(vault.nftBucket(a),0,0,block.timestamp+100);
        vm.recordLogs();migration.allocatePrincipal(1);Vm.Log[] memory logs=vm.getRecordedLogs();
        assertEq(LifecycleEventChecks.tokens(logs,address(nft),a),1);assertEq(LifecycleEventChecks.batches(logs,address(nft)),0);
        vm.recordLogs();migration.allocatePrincipal(1);logs=vm.getRecordedLogs();
        assertEq(LifecycleEventChecks.tokens(logs,address(nft),b),1);assertEq(LifecycleEventChecks.batches(logs,address(nft)),0);
        vm.recordLogs();migration.allocatePrincipal(1);logs=vm.getRecordedLogs();
        assertEq(uint256(migration.exitPhase()),3);assertEq(LifecycleEventChecks.batches(logs,address(nft)),1);
        assertEq(LifecycleEventChecks.tokens(logs,address(nft),dormant),0);
        (uint256 ethAmount,uint256 zzzAmount)=migration.claimablePrincipal(a);assertEq(ethAmount,100 ether);assertEq(zzzAmount,100 ether);
    }
    function testMetadataLifecyclePayoutNotifiesOnlySuccessAndNeverRepaidNFT()public{
        uint256 a=_metadataActivate(alice);uint256 b=_metadataActivate(bob);RejectHolderETH receiver=new RejectHolderETH();
        vm.prank(alice);nft.transferFrom(alice,address(receiver),a);_metadataReady(a);
        uint256 beforeBob=bob.balance;uint256 beforeZZZ=token.balanceOf(bob);
        vm.recordLogs();assertEq(migration.distributePrincipal(_metadataIDs(a,b)),1);Vm.Log[] memory logs=vm.getRecordedLogs();
        assertEq(LifecycleEventChecks.tokens(logs,address(nft),a),0);assertEq(LifecycleEventChecks.tokens(logs,address(nft),b),1);
        (,,,bool paid)=migration.principalOf(a);assertFalse(paid);(,,,paid)=migration.principalOf(b);assertTrue(paid);
        assertEq(bob.balance,beforeBob+100 ether);assertEq(token.balanceOf(bob),beforeZZZ+100 ether);
        assertEq(migration.remainingETH(),100 ether);assertEq(migration.remainingZZZ(),100 ether);
        vm.recordLogs();assertEq(migration.distributePrincipal(_metadataIDs(a,b)),0);logs=vm.getRecordedLogs();
        assertEq(LifecycleEventChecks.tokens(logs,address(nft),a),0);assertEq(LifecycleEventChecks.tokens(logs,address(nft),b),0);
        vm.recordLogs();receiver.recover(migration,a,alice);
        assertEq(LifecycleEventChecks.tokens(vm.getRecordedLogs(),address(nft),a),1);
        assertEq(migration.remainingETH(),0);assertEq(migration.remainingZZZ(),0);
    }
    function testMetadataLifecycleTransferredUnpaidPrincipalNotifiesNewOwnerPayment()public{
        uint256 a=_metadataActivate(alice);_metadataReady(a);
        vm.prank(alice);nft.transferFrom(alice,bob,a);uint256 beforeETH=bob.balance;uint256 beforeZZZ=token.balanceOf(bob);
        uint256[] memory ids=new uint256[](1);ids[0]=a;
        vm.recordLogs();assertEq(migration.distributePrincipal(ids),1);
        assertEq(LifecycleEventChecks.tokens(vm.getRecordedLogs(),address(nft),a),1);
        assertEq(bob.balance,beforeETH+100 ether);assertEq(token.balanceOf(bob),beforeZZZ+100 ether);
        (,,,bool paid)=migration.principalOf(a);assertTrue(paid);assertEq(nft.royaltyRewards().weightOf(a),1);
    }
    function testMetadataLifecycleActualTokenURITracksExitAllocationTransferAndPaidPrincipal()public{
        uint256 active=_metadataActivate(alice);string memory json=_metadataJSON(active);
        assertEq(vm.parseJsonUint(json,".metadata_schema"),2);
        assertEq(vm.parseJsonString(json,".principal_return_status"),"not_started");
        assertFalse(vm.parseJsonBool(json,".lp_exited"));
        string memory activeImage=vm.parseJsonString(json,".image");
        _metadataBegin();json=_metadataJSON(active);
        assertTrue(vm.parseJsonBool(json,".collection_lp_exit_started"));
        assertEq(vm.parseJsonUint(json,".collection_exit_phase"),1);
        assertEq(vm.parseJsonString(json,".principal_return_status"),"awaiting_allocation");
        assertFalse(vm.parseJsonBool(json,".lp_exited"));
        migration.closeBucket(vault.nftBucket(active),0,0,block.timestamp+100);json=_metadataJSON(active);
        assertEq(vm.parseJsonUint(json,".collection_exit_phase"),2);
        assertTrue(vm.parseJsonBool(json,".lp_exited"));
        assertEq(vm.parseJsonString(json,".lp_value_usd_18"),"0");
        assertEq(_metadataEvolution(json),"LP exited");
        assertEq(vm.parseJsonString(json,".image"),activeImage);
        assertEq(vm.parseJsonString(json,".principal_return_status"),"awaiting_allocation");
        migration.allocatePrincipal(32);json=_metadataJSON(active);
        assertEq(vm.parseJsonUint(json,".collection_exit_phase"),3);
        assertEq(vm.parseJsonString(json,".principal_return_status"),"payable");
        assertTrue(vm.parseJsonBool(json,".principal_allocated"));assertFalse(vm.parseJsonBool(json,".principal_paid"));
        vm.prank(alice);nft.transferFrom(alice,bob,active);assertEq(nft.ownerOf(active),bob);
        json=_metadataJSON(active);assertEq(vm.parseJsonString(json,".principal_return_status"),"payable");
        uint256 beforeETH=bob.balance;uint256 beforeZZZ=token.balanceOf(bob);
        uint256[] memory ids=new uint256[](1);ids[0]=active;assertEq(migration.distributePrincipal(ids),1);
        assertEq(bob.balance,beforeETH+100 ether);assertEq(token.balanceOf(bob),beforeZZZ+100 ether);
        uint256 beforeRead=gasleft();string memory paidURI=nft.tokenURI(active);
        emit log_named_uint("metadata2_paid_tokenURI_local_call_gas",beforeRead-gasleft());
        assertGt(bytes(paidURI).length,29);json=_metadataJSON(active);
        assertEq(vm.parseJsonString(json,".principal_return_status"),"paid");
        assertTrue(vm.parseJsonBool(json,".principal_paid"));assertTrue(vm.parseJsonBool(json,".lp_exited"));
        assertTrue(vm.parseJsonBool(json,".royalty_activated"));assertEq(nft.royaltyRewards().weightOf(active),1);
        assertEq(_metadataEvolution(json),"LP exited");assertEq(vm.parseJsonString(json,".image"),activeImage);
    }
}
