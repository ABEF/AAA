// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZNFTMetadata,NFTMetadataInput} from "../src/ZZZNFTMetadata.sol";
import {Ids,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {IZZZProtocolPolicy} from "../src/interfaces/IZZZProtocolPolicy.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";

// TEST ONLY: deterministic lifecycle/settlement snapshots, without protocol
// authority, real liquidity, price-source, marketplace or operating claims.
contract LifecycleAccessMock {
    mapping(bytes32=>address) public module;
    uint8 public canonicalState;
    bool public lpExitStarted;
    bool public preparationActive;
    address public protocolPolicy;
    function setModule(bytes32 key,address value) external {module[key]=value;}
    function setPolicy(address value) external {protocolPolicy=value;}
    function setCanonical(uint8 value) external {canonicalState=value;}
    function startExit() external {lpExitStarted=true;}
    function setPreparation(bool value) external {preparationActive=value;}
}
contract LifecyclePolicyMock {
    function metadataPolicy() external pure returns(IZZZProtocolPolicy.MetadataPolicy memory){
        return IZZZProtocolPolicy.MetadataPolicy(1000e18,10000e18,0);
    }
}
contract LifecycleWeightMock {
    mapping(uint256=>uint256) public weightOf;
    function set(uint256 id,uint256 weight) external {weightOf[id]=weight;}
}
contract LifecycleCollectionMock {
    address public access;
    address public royaltyRewards;
    bool public revealed=true;
    mapping(uint256=>address) private owners;
    address private successorController;
    address private successorNFT;
    constructor(address controller,address receiver){access=controller;royaltyRewards=receiver;owners[1]=address(0xA11CE);}
    function ownerOf(uint256 id) external view returns(address){require(owners[id]!=address(0));return owners[id];}
    function transfer(uint256 id,address owner) external {owners[id]=owner;}
    function rarityOf(uint256) external pure returns(uint8){return 2;}
    function paletteOf(uint256) external pure returns(uint8){return 0;}
    function patternOf(uint256) external pure returns(uint8){return 3;}
    function traitsReady(uint256) external view returns(bool){return revealed;}
    function setRevealed(bool value) external {revealed=value;}
    function artworkBaseURI() external pure returns(string memory){return "ipfs://reviewed-root/";}
    function setSuccessor(address controller,address nft) external {successorController=controller;successorNFT=nft;}
    function canonicalSuccessor() external view returns(address,address){return(successorController,successorNFT);}
}
contract LifecycleVaultMock {
    mapping(uint256=>uint256) public sharesOf;
    PositionStatus public status=PositionStatus.Active;
    function setShares(uint256 id,uint256 shares) external {sharesOf[id]=shares;}
    function setStatus(PositionStatus value) external {status=value;}
    function nftStatus(uint256 id) external view returns(PositionStatus){return sharesOf[id]==0?PositionStatus.Dormant:status;}
    function nftBucket(uint256 id) external view returns(uint256){return sharesOf[id]==0?0:1;}
    function bucketTotalShares(uint256) external pure returns(uint256){return 1;}
    function group(uint256) external view returns(Position memory value){value.status=status;value.lpTokenId=status==PositionStatus.Active?1:0;}
}
contract LifecycleSettlementMock {
    uint8 private phase;
    bool private failure;
    address public currentZZZ=address(0x1111);
    struct Principal {uint256 ethAmount;uint256 zzzAmount;bool allocated;bool paid;}
    mapping(uint256=>Principal) public principalOf;
    function setPhase(uint8 value) external {phase=value;}
    function setFailure(bool value) external {failure=value;}
    function exitPhase() external view returns(uint8){require(!failure);return phase;}
    function setPrincipal(uint256 id,uint256 ethAmount,uint256 zzzAmount,bool allocated,bool paid) external {
        principalOf[id]=Principal(ethAmount,zzzAmount,allocated,paid);
    }
}

contract MetadataLifecycleSnapshotsTest is Test {
    LifecycleAccessMock private access;
    LifecycleCollectionMock private nft;
    LifecycleVaultMock private vault;
    LifecycleSettlementMock private settlement;
    LifecycleWeightMock private weights;
    ZZZNFTMetadata private renderer;

    function setUp() public {
        vm.warp(1000000);vm.roll(100);
        access=new LifecycleAccessMock();weights=new LifecycleWeightMock();
        nft=new LifecycleCollectionMock(address(access),address(weights));vault=new LifecycleVaultMock();
        settlement=new LifecycleSettlementMock();renderer=new ZZZNFTMetadata(address(access));
        access.setPolicy(address(new LifecyclePolicyMock()));
        access.setModule(Ids.NFT,address(nft));access.setModule(Ids.VAULT,address(vault));
        access.setModule(Ids.MIGRATION,address(settlement));
        access.setModule(Ids.NFT_CANONICAL,address(new ZZZNFTCanonical(address(access),address(nft))));
    }
    function _exit(bool funded,bool closed) private {
        if(funded){weights.set(1,3);vault.setShares(1,1);}
        if(closed)vault.setStatus(PositionStatus.Exited);
        settlement.setPhase(1);access.startExit();
    }

    function testDormantTerminalClosurePreservesDormantArtWithoutPromisingActivationOrRoyalties() public {
        _exit(false,false);
        string memory json=_json(1);
        assertEq(vm.parseJsonUint(json,".metadata_schema"),2);
        assertTrue(vm.parseJsonBool(json,".activation_closed"));
        assertFalse(vm.parseJsonBool(json,".lp_exited"));
        assertFalse(vm.parseJsonBool(json,".royalty_activated"));
        assertEq(vm.parseJsonString(json,".principal_return_status"),"not_applicable");
        assertEq(vm.parseJsonString(json,".image"),"ipfs://reviewed-root/cyan-ribs-legendary-dormant.svg");
        assertTrue(_contains(vm.parseJsonString(json,".description"),"never activated"));
        assertTrue(_contains(json,'"value":"Activation closed"'));
    }
    function testUnrevealedTerminalNFTKeepsPlaceholderAndHonestPendingReveal() public {
        nft.setRevealed(false);_exit(false,false);
        string memory json=_json(1);
        assertTrue(_contains(vm.parseJsonString(json,".image"),"data:image/svg+xml;base64,"));
        assertTrue(_contains(vm.parseJsonString(json,".description"),"reveal remains pending"));
        assertTrue(_contains(json,'"value":"Unrevealed"'));
        assertFalse(vm.parseJsonBool(json,".principal_paid"));
    }
    function testStartedExitDoesNotPretendBucketAlreadyClosedOrPrincipalPaid() public {
        _exit(true,false);string memory json=_json(1);
        assertFalse(vm.parseJsonBool(json,".lp_exited"));
        assertFalse(vm.parseJsonBool(json,".principal_allocated"));
        assertFalse(vm.parseJsonBool(json,".principal_paid"));
        assertEq(vm.parseJsonString(json,".principal_return_status"),"awaiting_allocation");
        assertTrue(_contains(vm.parseJsonString(json,".description"),"has not closed"));
    }
    function testClosedUnallocatedExitIsOracleIndependentButNotZeroPaymentOrDormant() public {
        _exit(true,true);string memory json=_json(1);
        assertTrue(vm.parseJsonBool(json,".valuation_available"));
        assertTrue(vm.parseJsonBool(json,".lp_exited"));
        assertTrue(vm.parseJsonBool(json,".royalty_activated"));
        assertEq(vm.parseJsonString(json,".lp_value_usd_18"),"0");
        assertEq(vm.parseJsonString(json,".principal_return_status"),"awaiting_allocation");
        assertFalse(vm.parseJsonBool(json,".principal_allocated"));
        assertEq(vm.parseJsonString(json,".image"),"ipfs://reviewed-root/cyan-ribs-legendary-activated.svg");
    }
    function testAllocatedReadyAndPaidAreDistinctWithoutCountingPaidPrincipalAgain() public {
        _exit(true,true);settlement.setPhase(2);settlement.setPrincipal(1,7,11,true,false);
        string memory pending=_json(1);bytes32 prior=renderer.metadataLifecycleFingerprint(1);
        assertEq(vm.parseJsonString(pending,".principal_return_status"),"allocated_pending_readiness");
        assertTrue(vm.parseJsonBool(pending,".principal_allocated"));
        settlement.setPhase(3);string memory ready=_json(1);
        assertEq(vm.parseJsonString(ready,".principal_return_status"),"payable");
        assertTrue(renderer.metadataLifecycleFingerprint(1)!=prior);
        prior=renderer.metadataLifecycleFingerprint(1);
        settlement.setPrincipal(1,7,11,true,true);string memory paid=_json(1);
        assertTrue(vm.parseJsonBool(paid,".principal_paid"));
        assertEq(vm.parseJsonString(paid,".principal_return_status"),"paid");
        assertFalse(_contains(paid,'"remaining_principal_eth_wei":'));
        assertTrue(_contains(vm.parseJsonString(paid,".description"),"already been paid"));
        assertTrue(renderer.metadataLifecycleFingerprint(1)!=prior);
        nft.transfer(1,address(0xB0B));
        assertEq(vm.parseJsonString(_json(1),".principal_return_status"),"paid");
        assertEq(vm.parseJsonString(paid,".image"),vm.parseJsonString(ready,".image"));
    }
    function testZeroEntitlementIsNotMisreportedAsPaidOrAwaitingMoney() public {
        _exit(true,true);settlement.setPhase(3);settlement.setPrincipal(1,0,0,true,false);
        string memory json=_json(1);
        assertEq(vm.parseJsonString(json,".principal_return_status"),"zero_entitlement");
        assertFalse(vm.parseJsonBool(json,".principal_paid"));
        assertTrue(vm.parseJsonBool(json,".principal_allocated"));
        assertTrue(_contains(vm.parseJsonString(json,".description"),"assigns no principal"));
    }
    function testReplacementFrozenImportingCancelledCannotAdvertiseLiveRights() public {
        for(uint8 state=1;state<=4;++state){
            if(state==3)continue;
            access.setCanonical(state);string memory json=_json(1);
            assertEq(vm.parseJsonUint(json,".canonical_state"),state);
            assertTrue(vm.parseJsonUint(json,".canonical_state")!=0);
            assertTrue(_contains(json,'"successor_nft":null'));
        }
    }
    function testRetiredCollectionNamesSuccessorAndCannotPromiseRightsOnOldNFT() public {
        access.setCanonical(3);nft.setSuccessor(address(0x2222),address(0x3333));
        string memory json=_json(1);
        assertEq(vm.parseJsonUint(json,".canonical_state"),3);
        assertEq(vm.parseJsonAddress(json,".successor_controller"),address(0x2222));
        assertEq(vm.parseJsonAddress(json,".successor_nft"),address(0x3333));
        assertTrue(_contains(vm.parseJsonString(json,".description"),"retired NFT cannot exercise"));
        assertEq(renderer.METADATA_LIFECYCLE_VERSION(),2);
    }
    function testSnapshotContextChangesDoNotCreateLifecycleFingerprintChurn() public {
        bytes32 fingerprint=renderer.metadataLifecycleFingerprint(1);string memory beforeURI=renderer.tokenMetadata(1);
        vm.roll(123);vm.warp(1000123);string memory json=_json(1);
        assertEq(vm.parseJsonUint(json,".metadata_snapshot_block"),123);
        assertEq(vm.parseJsonUint(json,".metadata_snapshot_timestamp"),1000123);
        assertTrue(keccak256(bytes(beforeURI))!=keccak256(bytes(renderer.tokenMetadata(1))));
        assertEq(renderer.metadataLifecycleFingerprint(1),fingerprint);
    }
    function testPreparationAndCancellationAreVisibleWithoutPretendingPermanentClosure() public {
        bytes32 beforeKey=renderer.metadataLifecycleFingerprint(1);access.setPreparation(true);
        string memory json=_json(1);
        assertEq(vm.parseJsonUint(json,".canonical_state"),0);
        assertTrue(vm.parseJsonBool(json,".replacement_preparing"));
        assertFalse(vm.parseJsonBool(json,".activation_closed"));
        assertTrue(_contains(json,'"value":"Replacement preparing"'));
        assertTrue(_contains(vm.parseJsonString(json,".description"),"earned claims retain their separate rules"));
        assertTrue(renderer.metadataLifecycleFingerprint(1)!=beforeKey);
        access.setPreparation(false);
        assertEq(renderer.metadataLifecycleFingerprint(1),beforeKey);
        assertFalse(vm.parseJsonBool(_json(1),".replacement_preparing"));
    }
    function testLifecycleFingerprintNeedsNoOracleAndDistinguishesParkedCustody() public {
        weights.set(1,3);vault.setShares(1,1);
        assertFalse(vm.parseJsonBool(_json(1),".valuation_available"));
        bytes32 active=renderer.metadataLifecycleFingerprint(1);
        vault.setStatus(PositionStatus.Parked);
        assertTrue(renderer.metadataLifecycleFingerprint(1)!=active);
        assertTrue(_contains(_json(1),'"value":"LP parked"'));
    }
    function testLifecycleDependencyFailureCannotBecomeFakeOperatingOrPaidSnapshot() public {
        _exit(true,true);settlement.setFailure(true);
        vm.expectRevert();renderer.tokenMetadata(1);
        vm.expectRevert();renderer.metadataLifecycleFingerprint(1);
    }
    function testInvalidPaymentPhaseOrUnallocatedPaidFlagFailsClosed() public {
        _exit(true,true);settlement.setPhase(4);
        vm.expectRevert();renderer.tokenMetadata(1);
        settlement.setPhase(3);settlement.setPrincipal(1,1,2,false,true);
        vm.expectRevert();renderer.tokenMetadata(1);
    }
    function testInvalidCanonicalStateOrMissingRetiredSuccessorFailsClosed() public {
        access.setCanonical(5);vm.expectRevert();renderer.tokenMetadata(1);
        access.setCanonical(3);vm.expectRevert();renderer.tokenMetadata(1);
        vm.expectRevert();renderer.metadataLifecycleFingerprint(1);
    }
    function testNonexistentTokenCannotObtainCanonicalMetadataOrFingerprint() public {
        vm.expectRevert();renderer.tokenMetadata(999);
        vm.expectRevert();renderer.metadataLifecycleFingerprint(999);
    }
    function testCompanionBindingRejectsWrongControllerAndWrongCollection() public {
        LifecycleAccessMock foreignAccess=new LifecycleAccessMock();
        LifecycleCollectionMock foreignNFT=new LifecycleCollectionMock(address(foreignAccess),address(weights));
        ZZZNFTCanonical wrongController=new ZZZNFTCanonical(address(foreignAccess),address(foreignNFT));
        access.setModule(Ids.NFT_CANONICAL,address(wrongController));
        vm.expectRevert();renderer.tokenMetadata(1);
        vm.expectRevert();renderer.metadataLifecycleFingerprint(1);
        LifecycleCollectionMock otherNFT=new LifecycleCollectionMock(address(access),address(weights));
        ZZZNFTCanonical wrongCollection=new ZZZNFTCanonical(address(access),address(otherNFT));
        access.setModule(Ids.NFT_CANONICAL,address(wrongCollection));
        vm.expectRevert();renderer.tokenMetadata(1);
        vm.expectRevert();renderer.metadataLifecycleFingerprint(1);
    }
    function testCompanionFiveWordsMatchPackedFlagsAndOpaqueFingerprint() public {
        _exit(true,true);settlement.setPhase(3);settlement.setPrincipal(1,7,11,true,true);
        ZZZNFTCanonical lens=ZZZNFTCanonical(access.module(Ids.NFT_CANONICAL));
        (uint256 flags,uint256 ethAmount,uint256 zzzAmount,address controller,address successor)=lens.metadataLifecycleState(1);
        uint256 expected=2|(uint256(3)<<16)|(uint256(PositionStatus.Exited)<<24)|
            (uint256(1)<<33)|(uint256(1)<<34)|(uint256(1)<<35)|(uint256(1)<<36);
        assertEq(flags,expected);assertEq(ethAmount,7);assertEq(zzzAmount,11);
        assertEq(controller,address(0));assertEq(successor,address(0));
        bytes32 beforeKey=renderer.metadataLifecycleFingerprint(1);
        assertEq(beforeKey,keccak256(abi.encode(flags,ethAmount,zzzAmount,controller,successor)));
        settlement.setPrincipal(1,8,11,true,true);
        assertTrue(renderer.metadataLifecycleFingerprint(1)!=beforeKey);
        vm.expectRevert();lens.metadataLifecycleState(999);
    }
    function testStatelessRenderPreviewRetainsInputABIWithoutInventingPaidStatus() public {
        NFTMetadataInput memory input=NFTMetadataInput(1,2,0,3,4,true,true,0,3,"ipfs://reviewed-root/");
        string memory json=_decode(renderer.render(input));
        assertTrue(_contains(vm.parseJsonString(json,".description"),"remaining unpaid principal"));
        assertFalse(_contains(json,'"principal_paid":'));
        assertEq(vm.parseJsonString(json,".image"),"ipfs://reviewed-root/cyan-ribs-legendary-activated.svg");
    }
    function _json(uint256 id) private view returns(string memory){return _decode(renderer.tokenMetadata(id));}
    function _decode(string memory uri) private pure returns(string memory){
        bytes memory data=bytes(uri);uint256 prefix=29;
        bytes memory decoded=new bytes((data.length-prefix)/4*3);uint256 count;
        for(uint256 i=prefix;i<data.length;i+=4){
            uint256 word=(_digit(data[i])<<18)|(_digit(data[i+1])<<12)|(_digit(data[i+2])<<6)|_digit(data[i+3]);
            decoded[count++]=bytes1(uint8(word>>16));
            if(data[i+2]!="=")decoded[count++]=bytes1(uint8(word>>8));
            if(data[i+3]!="=")decoded[count++]=bytes1(uint8(word));
        }
        bytes memory result=new bytes(count);for(uint256 i;i<count;++i)result[i]=decoded[i];return string(result);
    }
    function _digit(bytes1 character) private pure returns(uint256){
        uint8 value=uint8(character);if(value>=65&&value<=90)return value-65;
        if(value>=97&&value<=122)return value-71;if(value>=48&&value<=57)return value+4;
        if(value==43)return 62;if(value==47)return 63;return 0;
    }
    function _contains(string memory haystack,string memory needle) private pure returns(bool){
        bytes memory a=bytes(haystack);bytes memory b=bytes(needle);
        if(b.length>a.length)return false;
        for(uint256 i;i<=a.length-b.length;++i){bool same=true;for(uint256 j;j<b.length;++j){if(a[i+j]!=b[j]){same=false;break;}}if(same)return true;}
        return false;
    }
}
