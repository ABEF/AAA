// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {SeaDropPoPLFixture} from "./SeaDropPoPLIntegration.t.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";
import {ZZZSeaDropMint} from "../src/ZZZSeaDropMint.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZCanonicalHandoff} from "../src/ZZZCanonicalHandoff.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {CanonicalNFTRecord} from "../src/interfaces/IZZZNFTCanonical.sol";
import {AllowListData} from "../src/interfaces/IZZZSeaDrop.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess} from "./mocks/Mocks.sol";

/// @dev TEST ONLY coordinator getters for the isolated actual NFT codec.
/// Lifecycle transitions are explicit mock controls, not a full handoff proof.
contract SeaDropCanonicalPeerFixture {
    address public incomingSource;
    address public destinationController;
    bytes32 public SCHEMA=keccak256("ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10");
    function connect(address source,address destination) external {
        incomingSource=source;destinationController=destination;
    }
    function setSchema(bytes32 schema) external {SCHEMA=schema;}
}

contract SeaDropCanonicalBootstrapAccessFixture is MockAccess {
    function bootstrap() external view returns(address){return governor;}
}

/// @notice Actual SeaDrop runtime and PoPL issuance produce authenticated source
/// records. Actual NFT/V10 codec/helper import all records and artwork inventory.
/// This is NFT-domain continuity only: authorities, lifecycle and VRF are mocks;
/// no LP/reward backing, full coordinator cutover, provider or gas acceptance.
contract SeaDropCanonicalTest is SeaDropPoPLFixture {
    struct Destination {
        MockAccess access;
        ZZZProtocolPolicy policy;
        ZZZNFT nft;
        ZZZSeaDropMint helper;
        ZZZNFTCanonical codec;
        SeaDropCanonicalPeerFixture peer;
    }
    ZZZNFTCanonical private sourceCodec;
    SeaDropCanonicalPeerFixture private sourcePeer;
    Destination private destination;

    function setUp() public override {
        super.setUp();
        access.beginBootstrap();
        sourceCodec=new ZZZNFTCanonical(address(access),address(nft));
        sourcePeer=new SeaDropCanonicalPeerFixture();
        access.bind(Ids.NFT_CANONICAL,address(sourceCodec));
        access.bind(Ids.CANONICAL,address(sourcePeer));
        access.seal();
        destination=_destination(true,uint128(PRICE),address(seaDrop));
        sourcePeer.connect(address(0),address(destination.access));
        destination.peer.connect(address(access),address(0));
    }

    function _destination(bool bindHelper,uint128 mintPrice,address drop)
        private returns(Destination memory s) {
        s.access=new MockAccess();
        s.policy=new ZZZProtocolPolicy(address(s.access),CREATOR);
        s.access.setProtocolPolicy(address(s.policy));
        s.nft=new ZZZNFT(address(s.access),"ipfs://TEST-ONLY/",
            address(new ZZZNFTMetadata(address(s.access))));
        s.access.bind(Ids.NFT,address(s.nft));
        if(mintPrice!=PRICE)s.policy.setMintPrice(mintPrice,REVIEW);
        if(bindHelper) {
            s.helper=new ZZZSeaDropMint(address(s.access),address(s.nft),drop,drop.codehash);
            s.nft.setSeaDropMint(address(s.helper));
            s.helper.configure(config,mintPrice,REVIEW);
        }
        s.nft.setMintEnd(config.publicEnd);
        s.codec=new ZZZNFTCanonical(address(s.access),address(s.nft));
        s.peer=new SeaDropCanonicalPeerFixture();
        s.access.bind(Ids.NFT_CANONICAL,address(s.codec));
        s.access.bind(Ids.CANONICAL,address(s.peer));
        s.peer.connect(address(access),address(0));
        s.access.seal();
    }

    function _mintAllStages() private {
        _team(2);
        vm.warp(config.allowlistStart);_allowlist(ALICE);
        vm.warp(config.publicStart);_public(BOB,2);
        assertEq(nft.mintedCount(),5);
        for(uint256 ordinal=1;ordinal<=5;++ordinal) {
            uint256 id=nft.tokenAtOrdinal(ordinal);
            vrf.fulfill(nft.requestOf(id),ordinal*173,ordinal*37);
            nft.finalizeTraits(id);
        }
        uint256 aliceId=nft.tokenAtOrdinal(3);uint256 bobId=nft.tokenAtOrdinal(4);
        vm.prank(ALICE);nft.transferFrom(ALICE,CAROL,aliceId);
        vm.prank(BOB);nft.transferFrom(BOB,CAROL,bobId);
    }

    function _freezeAndCapture() private {
        access.setCanonicalState(1);destination.access.setCanonicalState(2);
        vm.prank(address(sourcePeer));sourceCodec.canonicalCapture();
    }

    function _importRow(uint256 row) private {
        bytes memory data=sourceCodec.canonicalExport(row);
        vm.prank(address(destination.peer));destination.codec.canonicalImport(row,data);
    }

    function _assertBook(address recipient,uint256 lifetime,uint256 allowlist) private view {
        assertEq(destination.helper.lifetimeMinted(recipient),lifetime);
        assertEq(destination.helper.allowlistMinted(recipient),allowlist);
        (uint256 actualLifetime,uint256 supply,uint256 ceiling)=destination.helper.mintStats(recipient);
        assertEq(actualLifetime,lifetime);assertEq(supply,5);assertEq(ceiling,1000);
    }

    function testActualThreeStageIssuanceAndTransfersExportOriginalRecipients() public {
        _mintAllStages();_freezeAndCapture();
        for(uint256 ordinal=1;ordinal<=5;++ordinal) {
            CanonicalNFTRecord memory row=abi.decode(sourceCodec.canonicalExport(ordinal),(CanonicalNFTRecord));
            address original=ordinal<=2?TEAM:ordinal==3?ALICE:BOB;
            uint8 stage=ordinal<=2?1:ordinal==3?2:3;
            assertEq(row.originalRecipient,original);assertEq(row.mintStage,stage);
            assertEq(row.originalRecipient,nft.originalMintRecipient(row.id));
            assertEq(helper.originalMintRecipient(ordinal),original);
            assertEq(helper.mintStage(ordinal),stage);
            assertEq(row.owner,ordinal==3||ordinal==4?CAROL:original);
            assertTrue(nft.traitsReady(row.id));
        }
        assertEq(helper.lifetimeMinted(CAROL),0);assertEq(helper.allowlistMinted(CAROL),0);
    }

    function testCompleteNFTCodecImportPreservesOwnersDrawsQuotasAndAllArtworkRows() public {
        _mintAllStages();_freezeAndCapture();
        uint256 count=sourceCodec.canonicalCount();assertEq(count,1006);
        for(uint256 row;row<count;++row)_importRow(row);
        destination.codec.canonicalValidate();
        vm.prank(address(destination.peer));destination.codec.canonicalActivate();
        assertEq(destination.nft.mintedCount(),5);assertEq(destination.helper.totalMinted(),5);
        assertEq(destination.helper.phaseMinted(1),2);assertEq(destination.helper.phaseMinted(2),1);
        assertEq(destination.helper.phaseMinted(3),2);assertEq(destination.nft.remainingToReveal(),995);
        assertEq(destination.nft.nextToFinalize(),6);
        assertEq(destination.nft.randomnessEpoch(),nft.randomnessEpoch()+1);
        _assertBook(TEAM,2,0);_assertBook(ALICE,1,1);_assertBook(BOB,2,0);_assertBook(CAROL,0,0);
        for(uint256 ordinal=1;ordinal<=5;++ordinal) {
            uint256 id=nft.tokenAtOrdinal(ordinal);
            assertEq(destination.nft.tokenAtOrdinal(ordinal),id);
            assertEq(destination.nft.ownerOf(id),nft.ownerOf(id));
            assertEq(destination.nft.originalMintRecipient(id),nft.originalMintRecipient(id));
            assertEq(destination.nft.mintStageOf(id),nft.mintStageOf(id));
            assertEq(destination.nft.requestOf(id),nft.requestOf(id));
            assertEq(destination.nft.requestEpochOf(id),nft.requestEpochOf(id));
            assertEq(destination.nft.rarityOf(id),nft.rarityOf(id));
            assertEq(destination.nft.paletteOf(id),nft.paletteOf(id));
            assertEq(destination.nft.patternOf(id),nft.patternOf(id));
            assertTrue(destination.nft.traitsReady(id));
        }
        for(uint8 rarity;rarity<3;++rarity) {
            assertEq(destination.nft.rarityRemaining(rarity),nft.rarityRemaining(rarity));
            uint256 limit=rarity==0?600:rarity==1?300:100;
            for(uint256 item;item<limit;++item)
                assertEq(destination.nft.canonicalArtwork(rarity,item),nft.canonicalArtwork(rarity,item));
        }
    }

    function testIncompleteImportCannotActivateOrValidateUnrestoredMintCounts() public {
        _mintAllStages();_freezeAndCapture();_importRow(0);
        assertEq(destination.nft.mintedCount(),5);assertEq(destination.helper.totalMinted(),0);
        vm.expectRevert();destination.helper.assertCanonicalCount();
        vm.expectRevert();destination.codec.canonicalValidate();
        vm.prank(address(destination.peer));vm.expectRevert();destination.codec.canonicalActivate();
        _importRow(1);assertEq(destination.helper.totalMinted(),1);
        vm.expectRevert();destination.helper.assertCanonicalCount();
    }

    function testLegacyTenWordNFTRecordRejectsAndDoesNotAdvanceImportCursor() public {
        _mintAllStages();_freezeAndCapture();_importRow(0);
        CanonicalNFTRecord memory row=abi.decode(sourceCodec.canonicalExport(1),(CanonicalNFTRecord));
        bytes memory legacy=abi.encode(row.id,row.owner,row.rarity,row.color,row.palette,row.pattern,
            row.requestId,row.requestEpoch,row.rarityWord,row.colorWord);
        assertEq(legacy.length,320);
        vm.prank(address(destination.peer));vm.expectRevert();destination.codec.canonicalImport(1,legacy);
        assertEq(destination.helper.totalMinted(),0);
        _importRow(1);assertEq(destination.helper.totalMinted(),1);
    }

    function testInvalidStageAndZeroOriginalRecipientRollbackWithoutConsumingRow() public {
        _mintAllStages();_freezeAndCapture();_importRow(0);
        CanonicalNFTRecord memory row=abi.decode(sourceCodec.canonicalExport(1),(CanonicalNFTRecord));
        row.mintStage=0;
        vm.prank(address(destination.peer));vm.expectRevert();destination.codec.canonicalImport(1,abi.encode(row));
        row.mintStage=4;
        vm.prank(address(destination.peer));vm.expectRevert();destination.codec.canonicalImport(1,abi.encode(row));
        row.mintStage=1;row.originalRecipient=address(0);
        vm.prank(address(destination.peer));vm.expectRevert();destination.codec.canonicalImport(1,abi.encode(row));
        assertEq(destination.helper.totalMinted(),0);_importRow(1);
        assertEq(destination.helper.totalMinted(),1);
    }

    function testDuplicateAllowlistRecipientCannotBeRestoredAsAnotherMint() public {
        _mintAllStages();_freezeAndCapture();
        for(uint256 row;row<4;++row)_importRow(row);
        CanonicalNFTRecord memory forged=abi.decode(sourceCodec.canonicalExport(4),(CanonicalNFTRecord));
        forged.originalRecipient=ALICE;forged.mintStage=2;
        vm.prank(address(destination.peer));vm.expectRevert();destination.codec.canonicalImport(4,abi.encode(forged));
        assertEq(destination.helper.totalMinted(),3);assertEq(destination.helper.allowlistMinted(ALICE),1);
        _importRow(4);assertEq(destination.helper.totalMinted(),4);
    }

    function testPendingOriginalRandomnessBlocksSourceCaptureWithoutChangingQuotaBooks() public {
        vm.warp(config.publicStart);_public(ALICE,1);
        access.setCanonicalState(1);destination.access.setCanonicalState(2);
        vm.prank(address(sourcePeer));vm.expectRevert();sourceCodec.canonicalCapture();
        assertEq(helper.totalMinted(),1);assertEq(helper.lifetimeMinted(ALICE),1);
        assertEq(helper.phaseMinted(3),1);assertEq(vrf.sequence(),1);
        assertFalse(nft.traitsReady(_firstId()));assertEq(nft.requestOf(_firstId()),1);
    }

    function testHalfBoundAndDifferentPlanOrPriceAreRejectedBeforeHeaderImport() public {
        _mintAllStages();
        Destination memory half=_destination(false,uint128(PRICE),address(seaDrop));
        sourcePeer.connect(address(0),address(half.access));access.setCanonicalState(1);
        vm.prank(address(sourcePeer));vm.expectRevert();sourceCodec.canonicalCapture();
        sourcePeer.connect(address(0),address(destination.access));
        ZZZSeaDropMint.MintConfig memory changed=config;changed.publicWalletLimit=9;
        destination.helper.configure(changed,uint128(PRICE),REVIEW);
        vm.prank(address(sourcePeer));vm.expectRevert();sourceCodec.canonicalCapture();
        Destination memory priced=_destination(true,uint128(2*PRICE),address(seaDrop));
        sourcePeer.connect(address(0),address(priced.access));
        vm.prank(address(sourcePeer));vm.expectRevert();sourceCodec.canonicalCapture();
        assertEq(nft.mintedCount(),5);assertEq(helper.totalMinted(),5);
    }

    function testDifferentPinnedSeaDropRuntimeRejectsCanonicalPeer() public {
        _mintAllStages();
        address altered=address(0xD1FF);
        vm.etch(altered,bytes.concat(address(seaDrop).code,hex"00"));
        Destination memory wrong=_destination(true,uint128(PRICE),altered);
        assertNotEq(wrong.helper.seaDropCodeHash(),helper.seaDropCodeHash());
        sourcePeer.connect(address(0),address(wrong.access));access.setCanonicalState(1);
        vm.prank(address(sourcePeer));vm.expectRevert();sourceCodec.canonicalCapture();
    }

    function testSourceBooksSurviveMockCancelledPartialNFTImport() public {
        _mintAllStages();_freezeAndCapture();_importRow(0);_importRow(1);
        // Mock only the coordinator's cancellation boundary. Actual abort and
        // classified backing restoration require the separate full-graph suite.
        destination.access.setCanonicalState(4);access.setCanonicalState(0);
        assertEq(helper.totalMinted(),5);assertEq(helper.phaseMinted(1),2);
        assertEq(helper.phaseMinted(2),1);assertEq(helper.phaseMinted(3),2);
        assertEq(helper.lifetimeMinted(ALICE),1);assertEq(helper.allowlistMinted(ALICE),1);
        assertEq(nft.ownerOf(nft.tokenAtOrdinal(3)),CAROL);
        vm.prank(address(destination.peer));vm.expectRevert();destination.codec.canonicalActivate();
        uint256 importedId=destination.nft.tokenAtOrdinal(1);
        vm.expectRevert();destination.nft.transferFrom(TEAM,BOB,importedId);
        vm.warp(config.allowlistStart);vm.expectRevert();_allowlist(ALICE);
        assertEq(helper.totalMinted(),5);
    }

    function testActualCoordinatorRejectsV9SchemaBeforePreparingAnImporter() public {
        sourcePeer.setSchema(keccak256("ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9"));
        SeaDropCanonicalBootstrapAccessFixture target=new SeaDropCanonicalBootstrapAccessFixture();
        target.setProtocolPolicy(address(new ZZZProtocolPolicy(address(target),CREATOR)));
        ZZZVault targetVault=new ZZZVault(address(target),block.chainid,address(new ZZZMigrationBudget(address(target))));
        target.bind(Ids.VAULT,address(targetVault));
        ZZZCanonicalHandoff handoff=new ZZZCanonicalHandoff(address(target));
        target.bind(Ids.CANONICAL,address(handoff));
        vm.expectRevert(ZZZCanonicalHandoff.UnsupportedTransport.selector);handoff.prepareImport(address(access));
        assertEq(handoff.phase(),0);assertEq(target.canonicalState(),0);
        assertEq(handoff.incomingSource(),address(0));
    }
}
