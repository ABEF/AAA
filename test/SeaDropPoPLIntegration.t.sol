// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZSeaDropMint} from "../src/ZZZSeaDropMint.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZSeaDrop,PublicDrop,AllowListData,MintParams,TokenGatedDropStage,SignedMintValidationParams}
    from "../src/interfaces/IZZZSeaDrop.sol";
import {Ids,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {VerifiedSeaDropV1} from "./fixtures/VerifiedSeaDropV1.sol";

interface ISeaDropTestCallback {function duringReceiver() external;}
interface ISeaDropPayoutTestCallback {function afterPayment() external;}
contract PoPLSeaDropPayoutMutationFixture {
    address public immutable observer;
    constructor(address testObserver){observer=testObserver;}
    receive() external payable {ISeaDropPayoutTestCallback(observer).afterPayment();}
}
contract PoPLSeaDropReceiverFixture is IERC721Receiver {
    address public immutable collection;
    address public immutable observer;
    bool public reject;
    address public forwardTo;
    constructor(address nft,address testObserver){collection=nft;observer=testObserver;}
    function setReject(bool value) external {reject=value;}
    function setForwardTo(address recipient) external {forwardTo=recipient;}
    function onERC721Received(address,address,uint256 id,bytes calldata) external returns(bytes4) {
        require(msg.sender==collection,"wrong collection");
        ISeaDropTestCallback(observer).duringReceiver();
        if(forwardTo!=address(0))ZZZNFT(collection).transferFrom(address(this),forwardTo,id);
        require(!reject,"reject NFT");
        return IERC721Receiver.onERC721Received.selector;
    }
}
contract PoPLSeaDropRejectsPaymentFixture {receive() external payable {revert("reject payment");}}

/// @notice Real PoPL NFT, Vault, immutable Vault companion, mint helper, policy
/// and royalty factory execute against the EXACT deployed SeaDrop V1 runtime.
/// Authority and asynchronous VRF are explicit local mocks. There is no LP
/// venue, provider acceptance, full canonical handoff or live OpenSea enrollment.
abstract contract SeaDropPoPLFixture is Test {
    MockAccess internal access;
    MockVRF internal vrf;
    ZZZProtocolPolicy internal policy;
    ZZZNFT internal nft;
    ZZZVault internal vault;
    ZZZSeaDropMint internal helper;
    IZZZSeaDrop internal seaDrop;
    ZZZSeaDropMint.MintConfig internal config;
    MintParams internal teamTerms;
    MintParams internal allowlistTerms;
    bytes32 internal teamLeaf;
    bytes32 internal aliceLeaf;
    bytes32 internal bobLeaf;
    bytes32 internal allowlistBranch;
    address internal constant TEAM=address(0x7EA0);
    address internal constant ALICE=address(0xA11CE);
    address internal constant BOB=address(0xB0B);
    address internal constant CAROL=address(0xCA701);
    address internal constant FEE=address(0xFEE);
    address internal constant CREATOR=address(0xCAFE);
    bytes32 internal constant REVIEW=keccak256("TEST ONLY SeaDrop mint terms review");
    uint256 internal constant PRICE=0.05 ether;
    uint8 internal callbackMode;
    address internal paymentObserver;

    function setUp() public virtual {
        vm.chainId(4663);vm.warp(1_000_000);
        seaDrop=IZZZSeaDrop(VerifiedSeaDropV1.install(vm));
        access=new MockAccess();
        policy=new ZZZProtocolPolicy(address(access),CREATOR);access.setProtocolPolicy(address(policy));
        vault=new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        nft=new ZZZNFT(address(access),"ipfs://TEST-ONLY/",address(new ZZZNFTMetadata(address(access))));
        access.bind(Ids.VAULT,address(vault));access.bind(Ids.NFT,address(nft));
        access.bind(Ids.VAULT_CANONICAL,address(new ZZZVaultCanonical(address(access),address(vault),block.chainid)));
        helper=new ZZZSeaDropMint(address(access),address(nft),address(seaDrop),address(seaDrop).codehash);
        nft.setSeaDropMint(address(helper));
        vrf=new MockVRF();
        policy.configureRandomness(address(vrf),address(vrf).codehash,bytes32(uint256(1)),1,3,500000,false,REVIEW);
        config.teamAllocation=20;config.allowlistAllocation=500;config.publicWalletLimit=10;
        config.feeBps=1000;config.maxBatch=10;
        config.teamStart=uint48(block.timestamp);config.teamEnd=config.teamStart+100;
        config.allowlistStart=config.teamEnd+1;config.allowlistEnd=config.allowlistStart+100;
        config.publicStart=config.allowlistEnd+1;config.publicEnd=config.publicStart+100;
        config.feeRecipient=FEE;config.allowedPayersHash=keccak256(abi.encode(new address[](0)));
        // Stage limits in upstream Merkle leaves are lifetime supply and wallet
        // limits. PoPL's separate stage books impose the reviewed phase quotas.
        teamTerms=MintParams(0,20,config.teamStart,config.teamEnd,1,20,0,true);
        // The deliberately wider upstream wallet ceiling proves that PoPL's
        // independent one-per-allowlist book enforces its own restriction.
        allowlistTerms=MintParams(PRICE,1000,config.allowlistStart,config.allowlistEnd,2,520,1000,true);
        teamLeaf=keccak256(abi.encode(TEAM,teamTerms));
        aliceLeaf=keccak256(abi.encode(ALICE,allowlistTerms));
        bobLeaf=keccak256(abi.encode(BOB,allowlistTerms));
        allowlistBranch=_pair(aliceLeaf,bobLeaf);config.merkleRoot=_pair(teamLeaf,allowlistBranch);
        helper.configure(config,uint128(PRICE),REVIEW);nft.setMintEnd(config.publicEnd);
        _syncDrop();access.seal();
        vm.deal(TEAM,10 ether);vm.deal(ALICE,10 ether);vm.deal(BOB,10 ether);vm.deal(CAROL,10 ether);
    }
    function _pair(bytes32 a,bytes32 b) internal pure returns(bytes32) {
        return a<b?keccak256(abi.encodePacked(a,b)):keccak256(abi.encodePacked(b,a));
    }
    function _syncDrop() internal {
        nft.updatePublicDrop(address(seaDrop),helper.expectedPublicDrop());
        nft.updateAllowList(address(seaDrop),AllowListData(config.merkleRoot,new string[](0),"ipfs://TEST-ONLY-MANIFEST/"));
        nft.updateCreatorPayoutAddress(address(seaDrop),policy.salePolicy().recipient);
        if(!seaDrop.getFeeRecipientIsAllowed(address(nft),config.feeRecipient))
            nft.updateAllowedFeeRecipient(address(seaDrop),config.feeRecipient,true);
    }
    function _public(address buyer,uint256 quantity) internal {
        vm.prank(buyer);seaDrop.mintPublic{value:PRICE*quantity}(address(nft),config.feeRecipient,address(0),quantity);
    }
    function _allowlist(address buyer) internal {
        bytes32[] memory proof=new bytes32[](2);
        proof[0]=buyer==ALICE?bobLeaf:aliceLeaf;proof[1]=teamLeaf;
        vm.prank(buyer);seaDrop.mintAllowList{value:PRICE}(address(nft),config.feeRecipient,address(0),1,allowlistTerms,proof);
    }
    function _team(uint256 quantity) internal {
        bytes32[] memory proof=new bytes32[](1);proof[0]=allowlistBranch;
        vm.prank(TEAM);seaDrop.mintAllowList(address(nft),config.feeRecipient,address(0),quantity,teamTerms,proof);
    }
    function _assertEmpty() internal view {
        assertEq(nft.mintedCount(),0);assertEq(helper.totalMinted(),0);assertEq(vault.sequence(),0);
        assertEq(vrf.sequence(),0);assertFalse(helper.minting());assertEq(helper.activeRecipient(),address(0));
        assertEq(helper.phaseMinted(1),0);assertEq(helper.phaseMinted(2),0);assertEq(helper.phaseMinted(3),0);
        assertEq(nft.royaltyRewards().totalWeight(),0);assertEq(address(vault).balance,0);
        uint256 id=_firstId();assertEq(nft.requestOf(id),0);assertEq(nft.mintOrdinalOf(id),0);
        assertEq(helper.originalMintRecipient(1),address(0));assertEq(helper.mintStage(1),0);
        assertEq(uint8(vault.nftStatus(id)),uint8(PositionStatus.None));
    }
    function _firstId() internal view returns(uint256) {
        return uint256(keccak256(abi.encode(block.chainid,address(vault),uint256(1))));
    }
    function duringReceiver() external {
        require(msg.sender.code.length!=0,"fixture callback");
        if(callbackMode==1)policy.setMintPrice(uint128(2*PRICE),REVIEW);
        else if(callbackMode==2)nft.setMintEnd(uint64(config.publicEnd)+10);
        else if(callbackMode==3)access.setPaused(true);
        else if(callbackMode==4)nft.setMintPaused(true);
    }
    function afterPayment() external {
        require(msg.sender==paymentObserver&&nft.mintedCount()!=0,"fixture payment callback");
        assertFalse(helper.minting());
        policy.setMintPrice(uint128(2*PRICE),REVIEW);
    }

}

contract SeaDropPoPLIntegrationTest is SeaDropPoPLFixture {
    function testActualPublicMintBindsCanonicalIdentityBuyerAndDormantVRF() public {
        vm.warp(config.publicStart);_public(ALICE,2);
        uint256 id=_firstId();assertEq(nft.tokenAtOrdinal(1),id);assertEq(nft.ownerOf(id),ALICE);
        assertEq(nft.originalMintRecipient(id),ALICE);assertEq(helper.originalMintRecipient(1),ALICE);
        assertEq(nft.mintOrdinalOf(id),1);assertEq(nft.mintStageOf(id),3);
        assertEq(nft.mintedCount(),2);assertEq(vault.sequence(),2);assertEq(helper.totalMinted(),2);
        assertEq(helper.lifetimeMinted(ALICE),2);assertEq(vrf.sequence(),2);assertEq(nft.requestOf(id),1);
        assertFalse(nft.traitsReady(id));assertEq(vault.sharesOf(id),0);assertEq(vault.nftBucket(id),0);
        assertEq(uint8(vault.nftStatus(id)),uint8(PositionStatus.Dormant));
        assertEq(nft.royaltyRewards().weightOf(id),0);assertEq(nft.royaltyRewards().totalWeight(),0);
        assertEq(FEE.balance,0.01 ether);assertEq(CREATOR.balance,0.09 ether);
        assertEq(address(vault).balance,0);assertEq(address(nft.royaltyRewards()).balance,0);
        vrf.fulfill(1,0,0);nft.finalizeTraits(id);assertTrue(nft.traitsReady(id));assertEq(nft.royaltyRewards().weightOf(id),0);
    }
    function testTeamAllowlistAndPublicUseSeparateQuotaBooksAndSharedSupply() public {
        _team(2);assertEq(TEAM.balance,10 ether);assertEq(FEE.balance,0);assertEq(CREATOR.balance,0);
        vm.warp(config.allowlistStart);_allowlist(ALICE);
        vm.warp(config.publicStart);_public(BOB,3);
        assertEq(helper.phaseMinted(1),2);assertEq(helper.phaseMinted(2),1);assertEq(helper.phaseMinted(3),3);
        assertEq(helper.totalMinted(),6);assertEq(nft.mintedCount(),6);assertEq(vault.sequence(),6);assertEq(vrf.sequence(),6);
        assertEq(helper.mintStage(1),1);assertEq(helper.mintStage(3),2);assertEq(helper.mintStage(4),3);
        assertEq(CREATOR.balance,0.18 ether);assertEq(FEE.balance,0.02 ether);
    }
    function testAllowlistOnePerWalletCannotBeResetByTransferringNFT() public {
        vm.warp(config.allowlistStart);_allowlist(ALICE);
        vm.prank(ALICE);nft.transferFrom(ALICE,CAROL,_firstId());
        vm.expectRevert();_allowlist(ALICE);
        assertEq(helper.allowlistMinted(ALICE),1);assertEq(helper.lifetimeMinted(ALICE),1);
        assertEq(nft.ownerOf(_firstId()),CAROL);assertEq(vrf.sequence(),1);assertEq(vault.sequence(),1);
    }
    function testImmediateReceiverTransferPreservesOriginalMintQuotaAndCurrentOwner() public {
        PoPLSeaDropReceiverFixture receiver=new PoPLSeaDropReceiverFixture(address(nft),address(this));
        receiver.setForwardTo(CAROL);vm.deal(address(receiver),PRICE);vm.warp(config.publicStart);
        vm.prank(address(receiver));seaDrop.mintPublic{value:PRICE}(address(nft),FEE,address(0),1);
        uint256 id=_firstId();assertEq(nft.ownerOf(id),CAROL);
        assertEq(nft.originalMintRecipient(id),address(receiver));assertEq(helper.originalMintRecipient(1),address(receiver));
        assertEq(helper.lifetimeMinted(address(receiver)),1);assertEq(helper.lifetimeMinted(CAROL),0);
        assertEq(nft.requestOf(id),1);assertEq(nft.royaltyRewards().weightOf(id),0);
    }
    function testBatchCapRejectsWholeOperationWithoutMintOrDraw() public {
        config.maxBatch=1;helper.configure(config,uint128(PRICE),REVIEW);
        vm.expectRevert();_team(2);_assertEmpty();
        vm.warp(config.publicStart);vm.expectRevert();_public(ALICE,11);_assertEmpty();
    }
    function testWrongAllowlistProofAndModifiedPriceLeafAreRejected() public {
        vm.warp(config.allowlistStart);MintParams memory wrong=allowlistTerms;wrong.mintPrice=0;
        bytes32[] memory proof=new bytes32[](2);proof[0]=bobLeaf;proof[1]=teamLeaf;
        vm.prank(ALICE);vm.expectRevert();seaDrop.mintAllowList(address(nft),FEE,address(0),1,wrong,proof);
        proof[0]=aliceLeaf;vm.prank(ALICE);vm.expectRevert();
        seaDrop.mintAllowList{value:PRICE}(address(nft),FEE,address(0),1,allowlistTerms,proof);
        _assertEmpty();
    }
    function testChangedPolicyPriceRequiresNewReviewedTermsInsteadOfUsingOldRoot() public {
        policy.setMintPrice(uint128(2*PRICE),REVIEW);
        // A stale explicit expected price fails even before root admission.
        vm.expectRevert();helper.configure(config,uint128(PRICE),REVIEW);
        // The current positive allowlist root also cannot acquire new prices.
        vm.expectRevert();helper.configure(config,uint128(2*PRICE),REVIEW);
        vm.warp(config.allowlistStart);
        vm.expectRevert();_allowlist(ALICE);_assertEmpty();
    }
    function testFreeTeamOnlyRootSurvivesReviewedFuturePublicPriceChange() public {
        config.allowlistAllocation=0;config.merkleRoot=teamLeaf;
        helper.configure(config,uint128(PRICE),REVIEW);
        nft.updateAllowList(address(seaDrop),AllowListData(teamLeaf,new string[](0),"ipfs://TEST-ONLY-TEAM/"));
        policy.setMintPrice(uint128(2*PRICE),REVIEW);
        helper.configure(config,uint128(2*PRICE),REVIEW);
        nft.updatePublicDrop(address(seaDrop),helper.expectedPublicDrop());
        bytes32[] memory proof=new bytes32[](0);vm.prank(TEAM);
        seaDrop.mintAllowList(address(nft),FEE,address(0),1,teamTerms,proof);
        assertEq(helper.phaseMinted(1),1);assertEq(TEAM.balance,10 ether);
        vm.warp(config.publicStart);vm.prank(ALICE);
        seaDrop.mintPublic{value:2*PRICE}(address(nft),FEE,address(0),1);
        assertEq(helper.phaseMinted(3),1);assertEq(nft.mintedCount(),2);
        assertEq(FEE.balance,0.01 ether);assertEq(CREATOR.balance,0.09 ether);
    }
    function testGlobalPauseMintPausePreparationAndWrongCallerPreventIssuance() public {
        vm.warp(config.publicStart);access.setPaused(true);vm.expectRevert();_public(ALICE,1);access.setPaused(false);
        nft.setMintPaused(true);vm.expectRevert();_public(ALICE,1);nft.setMintPaused(false);
        access.setPreparation(true);vm.expectRevert();_public(ALICE,1);access.setPreparation(false);
        vm.prank(ALICE);vm.expectRevert();nft.mintSeaDrop(ALICE,1);
        vm.prank(ALICE);vm.expectRevert();helper.beginMint(address(seaDrop),ALICE,1);
        _assertEmpty();
    }
    function testDirectMintCannotBypassSeaDropAfterHelperBinding() public {
        vm.warp(config.publicStart);bytes32 review=vault.mintPolicyFingerprint();
        vm.prank(ALICE);vm.expectRevert();vault.mintDormant{value:PRICE}(review);_assertEmpty();
    }
    function testUnavailableVRFRefundsBuyerAndLeavesNoReservedBatchOrCanonicalID() public {
        vrf.setFailRequests(true);vm.warp(config.publicStart);
        vm.expectRevert();_public(ALICE,2);_assertEmpty();
        assertEq(ALICE.balance,10 ether);assertEq(FEE.balance,0);assertEq(CREATOR.balance,0);
    }
    function testRejectingPayeeRefundsFeeAndRevertsRealVRFAndAllQuotaBooks() public {
        PoPLSeaDropRejectsPaymentFixture bad=new PoPLSeaDropRejectsPaymentFixture();
        policy.proposeMintRecipient(address(bad),REVIEW);vm.prank(address(bad));policy.acceptMintRecipient();
        nft.updateCreatorPayoutAddress(address(seaDrop),address(bad));
        vm.warp(config.publicStart);vm.expectRevert();_public(ALICE,2);
        _assertEmpty();assertEq(ALICE.balance,10 ether);assertEq(FEE.balance,0);assertEq(address(bad).balance,0);
    }
    function testAuthorizedPostNFTPayeeMutationKeepsCurrentGrossNetAndChangesFutureOnly() public {
        PoPLSeaDropPayoutMutationFixture recipient=new PoPLSeaDropPayoutMutationFixture(address(this));
        paymentObserver=address(recipient);policy.proposeMintRecipient(address(recipient),REVIEW);
        vm.prank(address(recipient));policy.acceptMintRecipient();
        nft.updateCreatorPayoutAddress(address(seaDrop),address(recipient));
        vm.warp(config.publicStart);_public(ALICE,1);
        assertEq(nft.ownerOf(_firstId()),ALICE);assertEq(helper.totalMinted(),1);assertEq(vrf.sequence(),1);
        assertEq(FEE.balance,0.005 ether);assertEq(address(recipient).balance,0.045 ether);
        assertEq(ALICE.balance,10 ether-PRICE);assertEq(policy.salePolicy().mintPrice,2*PRICE);
        // New reviews must reconcile the changed price/root. The current mint
        // remains atomic and paid at its captured old terms; it is not rerolled.
        vm.expectRevert();_public(BOB,1);assertEq(helper.totalMinted(),1);
    }
    function testRejectingFeeRecipientRevertsRealNFTVaultAndVRF() public {
        PoPLSeaDropRejectsPaymentFixture bad=new PoPLSeaDropRejectsPaymentFixture();
        nft.updateAllowedFeeRecipient(address(seaDrop),FEE,false);
        config.feeRecipient=address(bad);helper.configure(config,uint128(PRICE),REVIEW);
        nft.updateAllowedFeeRecipient(address(seaDrop),address(bad),true);
        vm.warp(config.publicStart);vm.expectRevert();_public(ALICE,2);
        _assertEmpty();assertEq(ALICE.balance,10 ether);assertEq(CREATOR.balance,0);assertEq(address(bad).balance,0);
    }
    function testRejectingReceiverRollsBackCanonicalIDsRequestsAndHelperReservation() public {
        PoPLSeaDropReceiverFixture receiver=new PoPLSeaDropReceiverFixture(address(nft),address(this));
        receiver.setReject(true);vm.deal(address(receiver),PRICE);vm.warp(config.publicStart);
        vm.prank(address(receiver));vm.expectRevert();seaDrop.mintPublic{value:PRICE}(address(nft),FEE,address(0),1);
        _assertEmpty();assertEq(address(receiver).balance,PRICE);assertEq(FEE.balance,0);assertEq(CREATOR.balance,0);
    }
    function testReceiverCannotChangeCurrentPriceEndOrPauseWithoutRollingBackMint() public {
        PoPLSeaDropReceiverFixture receiver=new PoPLSeaDropReceiverFixture(address(nft),address(this));
        vm.deal(address(receiver),4*PRICE);vm.warp(config.publicStart);
        for(uint8 mode=1;mode<=4;++mode){
            callbackMode=mode;vm.prank(address(receiver));vm.expectRevert();
            seaDrop.mintPublic{value:PRICE}(address(nft),FEE,address(0),1);
            _assertEmpty();assertEq(policy.salePolicy().mintPrice,PRICE);assertEq(nft.royaltyRewards().mintEnd(),config.publicEnd);
            assertFalse(access.paused());assertFalse(nft.mintPaused());
        }
    }
    function testTypedSettersRejectWrongImplementationUnauthorizedAndUnsupportedFamilies() public {
        vm.prank(ALICE);vm.expectRevert();nft.updateCreatorPayoutAddress(address(seaDrop),CREATOR);
        vm.expectRevert();nft.updateCreatorPayoutAddress(address(0xBAD),CREATOR);
        vm.expectRevert();nft.updateCreatorPayoutAddress(address(seaDrop),ALICE);
        TokenGatedDropStage memory gate;SignedMintValidationParams memory signer;
        vm.expectRevert();nft.updateTokenGatedDrop(address(seaDrop),ALICE,gate);
        vm.expectRevert();nft.updateSignedMintValidationParams(address(seaDrop),ALICE,signer);
        address[] memory singleton=new address[](1);singleton[0]=address(seaDrop);
        vm.expectRevert();nft.updateAllowedSeaDrop(singleton);
        assertEq(seaDrop.getSigners(address(nft)).length,0);assertEq(seaDrop.getTokenGatedAllowedTokens(address(nft)).length,0);
    }
    function testBindingCannotBeReplacedAfterSealAndQuotasCannotShrinkBelowIssued() public {
        vm.expectRevert();nft.setSeaDropMint(address(helper));
        _team(2);config.teamAllocation=1;vm.expectRevert();helper.configure(config,uint128(PRICE),REVIEW);
        assertEq(helper.phaseMinted(1),2);assertEq(nft.mintedCount(),2);assertEq(helper.totalMinted(),2);
    }
}
