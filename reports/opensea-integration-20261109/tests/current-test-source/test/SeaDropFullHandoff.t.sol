// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZSeaDropMint} from "../src/ZZZSeaDropMint.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZCanonicalHandoff} from "../src/ZZZCanonicalHandoff.sol";
import {IZZZCanonicalModule} from "../src/interfaces/IZZZCanonical.sol";
import {IZZZSeaDrop,AllowListData} from "../src/interfaces/IZZZSeaDrop.sol";
import {Ids,PoolConfig,PoolKey,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {CanonicalNativeVenue} from "./helpers/CanonicalNativeVenue.sol";
import {PreparationPools,PreparationPolicy} from "./helpers/CanonicalPreparationFixtures.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {PortfolioFixture} from "./helpers/PortfolioFixture.sol";
import {VerifiedSeaDropV1} from "./fixtures/VerifiedSeaDropV1.sol";

/// @notice Two NEW whole-graph composition cases, not inherited historical tests.
/// All six accounting domains, Access and handoff coordinators are actual code;
/// SeaDrop is the exact verified runtime. Venue, token, correlated USD feeds and
/// VRF are explicit fixtures, not market/provider/OpenSea/operating acceptance.
contract SeaDropFullHandoffTest is Test {
    using DualOracleFixture for ZZZOracle;
    struct System {
        ZZZAccessController access;
        ZZZProtocolPolicy policy;
        ZZZVault vault;
        ZZZNFT nft;
        ZZZSeaDropMint mint;
        ZZZRoyaltyRewards royalties;
        ZZZRewards rewards;
        ZZZMembership members;
        ZZZFeeController fees;
        ZZZMigration migration;
        PreparationPools pools;
        CanonicalNativeVenue venue;
        ZZZOracle oracle;
        MockVRF vrf;
        ZZZCanonicalHandoff handoff;
    }
    struct Rights {
        uint256 first;
        uint256 second;
        uint256 dormant;
        uint256 firstLP;
        uint256 secondLP;
        uint256 firstRoyalty;
        uint256 secondRoyalty;
        uint256 firstTokenRoyalty;
        uint256 secondTokenRoyalty;
    }
    System private source;
    System private destination;
    Rights private expectedRights;
    MockToken private token;
    MockFeed private feed;
    IZZZSeaDrop private seaDrop;
    ZZZSeaDropMint.MintConfig private mintConfig;
    bytes32 private pool;
    uint256 private peakStepGas;
    uint256 private constant STEP_BUDGET=12_000_000;
    uint256 private constant PRICE=0.05 ether;
    address private constant ALICE=address(0xA11CE);
    address private constant BOB=address(0xB0B);
    address private constant KEEPER=address(0xBEEF);
    address private constant GUARDIAN=address(0x600D);
    address private constant CREATOR=address(0xCAFE);
    address private constant PLATFORM=address(0xFEE);
    bytes32 private constant REVIEW=keccak256("TEST ONLY whole V10 SeaDrop handoff");

    function setUp() public {
        vm.chainId(4663);vm.warp(1_000_000);
        seaDrop=IZZZSeaDrop(VerifiedSeaDropV1.install(vm));
        token=new MockToken(0);feed=new MockFeed(8,1e8);
        // Public-only is an explicit supported configuration. Other phase
        // quotas/proofs are exercised by the separate actual issuance suites.
        mintConfig.publicWalletLimit=10;mintConfig.feeBps=1000;mintConfig.maxBatch=10;
        mintConfig.teamStart=uint48(block.timestamp-4);mintConfig.teamEnd=uint48(block.timestamp-3);
        mintConfig.allowlistStart=uint48(block.timestamp-2);mintConfig.allowlistEnd=uint48(block.timestamp-1);
        mintConfig.publicStart=uint48(block.timestamp);mintConfig.publicEnd=uint48(block.timestamp+100);
        mintConfig.feeRecipient=PLATFORM;
        mintConfig.allowedPayersHash=keccak256(abi.encode(new address[](0)));
        source=_deploy(true);destination=_deploy(false);
        destination.handoff.prepareImport(address(source.access));destination.access.seal();
        vm.deal(ALICE,10 ether);vm.deal(BOB,10 ether);vm.deal(address(this),10 ether);
        token.mint(ALICE,1_000_000);
        vm.prank(ALICE);token.approve(address(source.vault),10_000);
    }

    function _deploy(bool sealNow) private returns(System memory s) {
        s.access=new ZZZAccessController(address(this),KEEPER,GUARDIAN);
        s.policy=ProtocolPolicyFixture.bind(address(s.access),CREATOR);
        s.pools=new PreparationPools(address(s.access));
        s.venue=new CanonicalNativeVenue(address(s.access),address(token));
        vm.deal(address(s.venue),1 ether);
        s.vault=new ZZZVault(address(s.access),block.chainid,address(new ZZZMigrationBudget(address(s.access))));
        s.nft=new ZZZNFT(address(s.access),"ipfs://TEST-ONLY-FULL-HANDOFF/",
            address(new ZZZNFTMetadata(address(s.access))));
        s.royalties=s.nft.royaltyRewards();
        s.rewards=new ZZZRewards(address(s.access));s.members=new ZZZMembership(address(s.access));
        s.fees=new ZZZFeeController(address(s.access));s.migration=new ZZZMigration(address(s.access));
        s.oracle=new ZZZOracle(address(s.access),address(0));
        s.access.bind(Ids.VAULT,address(s.vault));s.access.bind(Ids.NFT,address(s.nft));
        s.access.bind(Ids.LIQUIDITY,address(s.venue));s.access.bind(Ids.REWARDS,address(s.rewards));
        s.access.bind(Ids.MEMBERSHIP,address(s.members));s.access.bind(Ids.FEES,address(s.fees));
        s.access.bind(Ids.STRATEGY,address(new PreparationPolicy(address(s.access))));
        s.access.bind(Ids.COMPOUNDER,address(new ZZZCompounder(address(s.access))));
        s.access.bind(Ids.BUYBACK,address(new ZZZBuyback(address(s.access),address(token),1e30)));
        s.access.bind(Ids.MIGRATION,address(s.migration));s.access.bind(Ids.ORACLE,address(s.oracle));
        s.access.bind(Ids.POOLS,address(s.pools));
        s.oracle.setTestFeed(address(0),address(feed),3600);
        s.oracle.setTestFeed(address(token),address(feed),3600);
        s.pools.setTestZZZIdentity(address(token));s.rewards.addAsset(address(token));
        s.migration.configureZZZ(address(token),address(token).codehash,REVIEW);
        s.nft.addRoyaltyAsset(address(token));
        s.vrf=new MockVRF();
        ProtocolPolicyFixture.randomness(address(s.access),address(s.vrf),bytes32(uint256(1)),1,3,500000,false);
        PoolConfig memory c;c.key=PoolKey(address(0),address(token),3000,60,address(0));
        c.operationsEnabled=true;c.depositsEnabled=true;c.minDepositUSD=1e18;
        c.maxPositionUSD=1e30;c.maxSlippageBps=100;
        pool=keccak256(abi.encode(c.key));s.pools.set(pool,c);
        s.mint=new ZZZSeaDropMint(address(s.access),address(s.nft),address(seaDrop),address(seaDrop).codehash);
        s.nft.setSeaDropMint(address(s.mint));s.mint.configure(mintConfig,uint128(PRICE),REVIEW);
        s.nft.setMintEnd(mintConfig.publicEnd);
        s.nft.updatePublicDrop(address(seaDrop),s.mint.expectedPublicDrop());
        s.nft.updateAllowList(address(seaDrop),AllowListData(bytes32(0),new string[](0),"ipfs://TEST-ONLY-PUBLIC/"));
        s.nft.updateCreatorPayoutAddress(address(seaDrop),CREATOR);
        s.nft.updateAllowedFeeRecipient(address(seaDrop),PLATFORM,true);
        CanonicalFixture.bind(address(s.access));
        s.handoff=ZZZCanonicalHandoff(s.access.canonicalHandoff());
        assertEq(s.handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10"));
        if(sealNow)s.access.seal();
    }

    function _fresh() private {feed.set(1e8,block.timestamp,block.timestamp);}
    function _cool(System memory s) private {
        bytes32[16] memory ids=[Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,
            Ids.STRATEGY,Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.ORACLE,Ids.POOLS,
            Ids.CANONICAL,Ids.NFT_CANONICAL,Ids.VAULT_CANONICAL,Ids.FEES_CANONICAL];
        address royalties=address(s.royalties);address mint=address(s.mint);
        address rewardCanonical=s.rewards.canonicalModule();
        for(uint256 i;i<ids.length;++i)vm.cool(s.access.module(ids[i]));
        vm.cool(royalties);vm.cool(mint);vm.cool(rewardCanonical);
        vm.cool(address(s.policy));vm.cool(address(s.access));vm.cool(address(token));vm.cool(address(feed));
    }
    function _measure(uint256 started) private {
        uint256 used=started-gasleft();assertLt(used,STEP_BUDGET,"step exceeds unchanged 12M local budget");
        if(used>peakStepGas)peakStepGas=used;
    }
    function _govern(address target,bytes memory data) private {
        _fresh();_cool(source);_cool(destination);
        uint256 started=gasleft();(bool ok,bytes memory result)=target.call(data);
        if(!ok)assembly("memory-safe"){revert(add(result,32),mload(result))}
        _measure(started);
    }

    function _seed() private {
        Rights storage r=expectedRights;
        assertEq(address(source.nft.seaDropMint()),address(source.mint));
        assertEq(address(destination.nft.seaDropMint()),address(destination.mint));
        vm.prank(ALICE);seaDrop.mintPublic{value:3*PRICE}(address(source.nft),PLATFORM,address(0),3);
        r.first=source.nft.tokenAtOrdinal(1);r.second=source.nft.tokenAtOrdinal(2);
        r.dormant=source.nft.tokenAtOrdinal(3);
        for(uint256 ordinal=1;ordinal<=3;++ordinal) {
            uint256 id=source.nft.tokenAtOrdinal(ordinal);
            uint256 rarity=ordinal==2?source.nft.remainingToReveal()-1:0;
            source.vrf.fulfill(source.nft.requestOf(id),rarity,ordinal*19);source.nft.finalizeTraits(id);
        }
        assertEq(source.nft.rarityOf(r.first),0);assertEq(source.nft.rarityOf(r.second),2);
        _fresh();vm.prank(ALICE);source.vault.activate{value:1000}(r.first,pool,1000,1000,1,block.timestamp+100);
        _fresh();vm.prank(ALICE);source.vault.activate{value:500}(r.second,pool,500,500,1,block.timestamp+100);
        source.venue.setFees(2000,0);
        uint256 bucket=source.vault.nftBucket(r.first);
        vm.prank(KEEPER);source.vault.collectFees(bucket,block.timestamp+100);
        token.mint(address(source.royalties),101);
        (bool funded,)=address(source.royalties).call{value:1 ether+3}("");assertTrue(funded);
        // The sale actually expires; no helper/NFT deadline is silently changed.
        vm.warp(uint256(mintConfig.publicEnd)+3601);source.royalties.syncAll();_fresh();
        assertTrue(source.royalties.royaltiesOpen());assertEq(source.royalties.totalWeight(),4);
        vm.prank(ALICE);source.nft.transferFrom(ALICE,BOB,r.second);
        r.firstLP=source.rewards.claimable(r.first,address(0));r.secondLP=source.rewards.claimable(r.second,address(0));
        r.firstRoyalty=source.royalties.claimable(r.first,address(0));
        r.secondRoyalty=source.royalties.claimable(r.second,address(0));
        r.firstTokenRoyalty=source.royalties.claimable(r.first,address(token));
        r.secondTokenRoyalty=source.royalties.claimable(r.second,address(token));
        assertGt(r.firstLP,0);assertGt(r.secondLP,0);assertEq(r.firstLP+r.secondLP,1800);
        assertGt(r.firstRoyalty,0);assertGt(r.secondRoyalty,0);
        assertEq(r.firstRoyalty+r.secondRoyalty,1 ether+3);
        assertEq(r.firstTokenRoyalty+r.secondTokenRoyalty,101);
        assertEq(source.rewards.claimable(r.dormant,address(0)),0);
        assertEq(source.royalties.claimable(r.dormant,address(0)),0);
        assertEq(source.royalties.weightOf(r.dormant),0);
        assertEq(source.mint.lifetimeMinted(ALICE),3);assertEq(source.mint.lifetimeMinted(BOB),0);
    }

    function _freezeAndSettle(Rights memory r) private {
        ZZZAccessController.PreparationNotice memory notice=ZZZAccessController.PreparationNotice(
            block.chainid,address(destination.access),destination.handoff.deploymentCommitment(),REVIEW);
        _govern(address(source.access),abi.encodeCall(source.access.startPreparation,(notice)));
        vm.prank(GUARDIAN);source.access.setPaused(true);
        uint256 bucket=source.vault.nftBucket(r.first);Position memory p=source.vault.group(bucket);
        ZZZMigration.ParkingRequest memory request=ZZZMigration.ParkingRequest(bucket,p.poolId,p.lpTokenId,
            source.vault.bucketTotalShares(bucket),p.depositUSD,source.migration.custodyEpoch(bucket),
            source.migration.parkingNonce(bucket),address(0),address(token),1,1,block.timestamp+100,REVIEW,
            PortfolioFixture.executionHash(address(source.venue),p.lpTokenId));
        _govern(address(source.migration),abi.encodeCall(source.migration.park,(request)));
        assertEq(uint8(source.vault.group(bucket).status),uint8(PositionStatus.Parked));
        _govern(address(source.handoff),abi.encodeCall(source.handoff.freeze,()));
        for(uint8 slot;slot<6;++slot) {
            _cool(source);_cool(destination);uint256 started=gasleft();source.handoff.settle(slot);_measure(started);
        }
        assertEq(source.access.canonicalState(),1);assertEq(destination.access.canonicalState(),2);
    }

    function _exportImportFund() private {
        for(uint8 slot;slot<6;++slot) {
            uint256 count=source.handoff.recordCount(slot);
            for(uint256 offset;offset<count;offset+=8) {
                vm.resetGasMetering();
                this.exportOneBatch(slot,count-offset>8?8:count-offset);
            }
        }
        assertNotEq(source.handoff.stateRoot(),bytes32(0));
        for(uint8 slot;slot<6;++slot) {
            uint256 count=source.handoff.recordCount(slot);
            for(uint256 offset;offset<count;offset+=8) {
                vm.resetGasMetering();
                this.importOneBatch(slot,offset,count-offset>8?8:count-offset);
            }
        }
        _cool(source);_cool(destination);uint256 completion=gasleft();destination.handoff.completeImport();_measure(completion);
        for(uint8 slot;slot<6;++slot)for(uint256 index;index<source.handoff.assetCount(slot);++index) {
            _cool(source);_cool(destination);uint256 started=gasleft();source.handoff.fund(slot,index);_measure(started);
        }
        assertTrue(source.handoff.funded(3,0));
        assertEq(address(source.rewards).balance,0);assertGt(address(destination.rewards).balance,0);
        assertGt(address(destination.royalties).balance,0);
    }

    /// @dev TEST ONLY transaction-frame boundaries. Retaining every ABI buffer
    /// for thousands of rows in one caller frame exhausts the harness memory,
    /// whereas real batches run as separate transactions. Reset metering only
    /// between operations; each real call still has its unchanged 12M check.
    function exportOneBatch(uint8 slot,uint256 count) external {
        require(msg.sender==address(this));
        _cool(source);_cool(destination);uint256 started=gasleft();
        source.handoff.exportRows(slot,count);_measure(started);
    }
    function importOneBatch(uint8 slot,uint256 offset,uint256 length) external {
        require(msg.sender==address(this));
        IZZZCanonicalModule module=IZZZCanonicalModule(source.handoff.moduleAt(slot));
        bytes[] memory rows=new bytes[](length);
        for(uint256 i;i<length;++i)rows[i]=module.canonicalExport(offset+i);
        _cool(source);_cool(destination);uint256 started=gasleft();
        destination.handoff.importRows(slot,rows);_measure(started);
    }

    function _assertMintContinuity(System memory s,Rights memory r) private view {
        assertEq(s.nft.mintedCount(),3);assertEq(s.mint.totalMinted(),3);
        assertEq(s.mint.lifetimeMinted(ALICE),3);assertEq(s.mint.lifetimeMinted(BOB),0);
        assertEq(s.mint.phaseMinted(3),3);assertEq(s.mint.phaseMinted(1),0);assertEq(s.mint.phaseMinted(2),0);
        assertEq(s.nft.originalMintRecipient(r.second),ALICE);assertEq(s.nft.ownerOf(r.second),BOB);
        assertEq(s.nft.mintStageOf(r.first),3);assertEq(s.nft.mintStageOf(r.second),3);assertEq(s.nft.mintStageOf(r.dormant),3);
        assertEq(s.nft.ownerOf(r.dormant),ALICE);assertEq(s.royalties.weightOf(r.dormant),0);
        assertEq(s.rewards.claimable(r.dormant,address(0)),0);
    }

    function testBoundSeaDropWholeV10CommitCarriesActualLPAndRoyaltyClaimsToCurrentOwner() public {
        // Preserve the expected baseline across the separate transaction-frame
        // driver, rather than retaining a caller-memory pointer through it.
        _seed();assertGt(expectedRights.second,0);
        _freezeAndSettle(expectedRights);_exportImportFund();
        _govern(address(source.handoff),abi.encodeCall(source.handoff.commit,()));
        Rights storage r=expectedRights;
        assertEq(source.access.canonicalState(),3);assertEq(destination.access.canonicalState(),0);
        _assertMintContinuity(destination,r);
        assertEq(destination.vault.sharesOf(r.first),source.vault.sharesOf(r.first));
        assertEq(destination.vault.sharesOf(r.second),source.vault.sharesOf(r.second));
        assertEq(destination.rewards.claimable(r.first,address(0)),r.firstLP);
        assertEq(destination.rewards.claimable(r.second,address(0)),r.secondLP);
        assertEq(destination.royalties.claimable(r.second,address(0)),r.secondRoyalty);
        assertEq(destination.royalties.claimable(r.second,address(token)),r.secondTokenRoyalty);
        vm.prank(ALICE);vm.expectRevert();destination.rewards.claim(r.second,address(0));
        vm.prank(ALICE);vm.expectRevert();destination.royalties.claim(r.second,address(0));
        uint256 beforeETH=BOB.balance;uint256 beforeToken=token.balanceOf(BOB);
        vm.prank(BOB);assertEq(destination.rewards.claim(r.second,address(0)),r.secondLP);
        vm.prank(BOB);assertEq(destination.royalties.claim(r.second,address(0)),r.secondRoyalty);
        vm.prank(BOB);assertEq(destination.royalties.claim(r.second,address(token)),r.secondTokenRoyalty);
        assertEq(BOB.balance,beforeETH+r.secondLP+r.secondRoyalty);
        assertEq(token.balanceOf(BOB),beforeToken+r.secondTokenRoyalty);
        vm.prank(BOB);vm.expectRevert();source.rewards.claim(r.second,address(0));
        vm.prank(BOB);vm.expectRevert();source.royalties.claim(r.second,address(0));
        emit log_named_uint("whole V10 commit peak bounded step gas",peakStepGas);
    }

    function testBoundSeaDropFundedV10AbortReturnsBackingAndPreservesOriginalMintBooks() public {
        _seed();assertGt(expectedRights.second,0);
        _freezeAndSettle(expectedRights);_exportImportFund();
        _govern(address(source.handoff),abi.encodeCall(source.handoff.abort,()));
        vm.expectRevert();source.handoff.finishAbort();
        for(uint8 slot;slot<6;++slot)for(uint256 index;index<source.handoff.assetCount(slot);++index) {
            _cool(source);_cool(destination);uint256 started=gasleft();source.handoff.returnFunds(slot,index);_measure(started);
        }
        _govern(address(source.handoff),abi.encodeCall(source.handoff.finishAbort,()));
        Rights storage r=expectedRights;
        assertEq(source.access.canonicalState(),0);assertEq(destination.access.canonicalState(),4);
        _assertMintContinuity(source,r);
        assertEq(source.rewards.claimable(r.second,address(0)),r.secondLP);
        assertEq(source.royalties.claimable(r.second,address(0)),r.secondRoyalty);
        assertEq(source.royalties.claimable(r.second,address(token)),r.secondTokenRoyalty);
        uint256 beforeETH=BOB.balance;vm.prank(BOB);assertEq(source.rewards.claim(r.second,address(0)),r.secondLP);
        vm.prank(BOB);assertEq(source.royalties.claim(r.second,address(0)),r.secondRoyalty);
        assertEq(BOB.balance,beforeETH+r.secondLP+r.secondRoyalty);
        vm.prank(BOB);vm.expectRevert();destination.rewards.claim(r.second,address(0));
        vm.prank(BOB);vm.expectRevert();destination.royalties.claim(r.second,address(0));
        vm.expectRevert();destination.handoff.completeImport();
        assertEq(destination.mint.totalMinted(),3);assertEq(destination.mint.lifetimeMinted(ALICE),3);
        emit log_named_uint("whole V10 funded abort peak bounded step gas",peakStepGas);
    }
}
