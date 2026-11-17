// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockAccess,MockToken,MockPools} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ExactLPFixedIdentity,ExactLPShareFixture} from "./ExactLPRewards.t.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {Ids,PoolKey,PoolConfig} from "../src/libraries/ZZZTypes.sol";

/// @dev Test-only conventional ERC20 with an explicit recipient delivery fault.
/// Reads/enrollment remain healthy; this isolates a late claim-transfer failure.
contract LaunchClaimToken20261117 is MockToken {
    address private rejectingRecipient;
    error RecipientRejected();
    constructor()MockToken(18){}
    function reject(address recipient)external{rejectingRecipient=recipient;}
    function _update(address from,address to,uint256 amount)internal override{
        if(amount!=0 && to==rejectingRecipient)revert RecipientRejected();
        super._update(from,to,amount);
    }
}

/// @notice Real NFT/VRF trait finalization, Membership, FeeController, exact LP,
/// original-currency royalty4 and immutable claim router. The typed share writer
/// is a declared accounting seam: it does not create/price physical liquidity.
/// Direct mint is the explicit zero-SeaDrop test profile, not OpenSea acceptance.
/// ALL funding/enrollment occurs in setUp, before the measured test transaction.
abstract contract LaunchClaimFixture20261117 is Test {
    uint256 internal constant CLAIM_GAS=12_000_000;
    address internal constant ALICE=address(0xA11CE);
    address internal constant BOB=address(0xB0B);
    MockAccess internal access;
    MockPools internal pools;
    MockVRF internal vrf;
    ZZZNFT internal nft;
    ZZZRewards internal rewards;
    ZZZMembership internal membership;
    ZZZFeeController internal fees;
    ZZZRoyaltyRewards internal royalties;
    ZZZClaimRouter internal router;
    ExactLPShareFixture internal shares;
    LaunchClaimToken20261117[16] internal currencies;
    uint256[1000] internal ids;
    address[] private coldTargets;
    struct Cash {uint256 eth;uint256[16] tokens;}
    event LaunchClaimEnvelope(bytes32 indexed scenario,uint256 entries,uint256 gasLimit,uint256 bodyGas,bool success);
    event LaunchClaimColdFootprint(uint256 accounts,uint256 recordedSlotResets);

    function _storeRoyalties()internal pure virtual returns(bool){return true;}
    function setUp()public virtual{
        vm.pauseGasMetering();vm.warp(1_000_000);vm.deal(address(this),1_000_000 ether);
        access=new MockAccess();ProtocolPolicyFixture.bind(address(access));pools=new MockPools();
        for(uint256 a;a<16;++a)currencies[a]=new LaunchClaimToken20261117();
        pools.setActivationAssets(address(new ExactLPFixedIdentity(address(currencies[0]))));
        nft=new ZZZNFT(address(access),"ipfs://TEST-ONLY-launch-claims/",address(new ZZZNFTMetadata(address(access))));
        nft.setMintEnd(uint64(block.timestamp+3650 days));
        membership=new ZZZMembership(address(access));rewards=new ZZZRewards(address(access));fees=new ZZZFeeController(address(access));
        shares=new ExactLPShareFixture(rewards,membership,nft,fees,currencies[0]);
        access.bind(Ids.VAULT,address(shares));access.bind(Ids.NFT,address(nft));access.bind(Ids.MEMBERSHIP,address(membership));
        access.bind(Ids.REWARDS,address(rewards));access.bind(Ids.FEES,address(fees));access.bind(Ids.POOLS,address(pools));
        rewards.addAsset(address(currencies[0]));
        for(uint256 a;a<16;++a)nft.addRoyaltyAsset(address(currencies[a]));
        vrf=new MockVRF();ProtocolPolicyFixture.randomness(address(access),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        for(uint256 b=1;b<=4;++b){
            PoolConfig memory c;c.key=PoolKey(address(0),address(currencies[0]),uint24(3000+b),60,address(0));
            bytes32 pool=keccak256(abi.encode(c.key));pools.set(pool,c);shares.setRecord(b,pool);
        }
        access.seal();royalties=nft.royaltyRewards();router=nft.claimRouter();
        for(uint256 i;i<1000;++i){
            uint256 id=10001+i*7;ids[i]=id;shares.mint(ALICE,id);
            vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
            shares.join(id,i%4+1,(i%101+1)*1e18);
        }
        // Word zero exhausts Common600, then Rare300, then Legendary100.
        assertEq(nft.rarityOf(ids[599]),0);assertEq(nft.rarityOf(ids[600]),1);
        assertEq(nft.rarityOf(ids[899]),1);assertEq(nft.rarityOf(ids[900]),2);
        assertEq(nft.mintedCount(),1000);assertEq(membership.totalEligible(),1000);
        assertEq(royalties.activationCount(),1000);assertEq(royalties.totalWeight(),1500);
        assertEq(royalties.assetCount(),17);assertEq(royalties.assetCapacity(),16);
        for(uint256 i;i<16;++i){vm.prank(ALICE);nft.transferFrom(ALICE,BOB,ids[900+i*6]);}
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,ids[999]);
        nft.setMintEnd(uint64(block.timestamp+1));vm.warp(block.timestamp+3601);royalties.syncAll();
        for(uint256 b=1;b<=4;++b){
            shares.allocateETH{value:10_000_003+b*20}(b);
            currencies[0].mint(address(shares),20_000_007+b*20);
            shares.allocateZZZ(b,20_000_007+b*20);
        }
        (bool sent,)=address(royalties).call{value:2_000_017}("");require(sent);
        for(uint256 a;a<16;++a)currencies[a].mint(address(royalties),1_000_003+a*10);
        if(_storeRoyalties())royalties.syncAll();
        assertEq(royalties.pending(address(0)),_storeRoyalties()?0:2_000_017);
        _target(address(access));_target(address(pools));_target(address(nft));_target(address(router));
        _target(address(rewards));_target(address(royalties));_target(address(membership));_target(address(shares));
        _target(address(fees));_target(access.protocolPolicy());_target(rewards.canonicalModule());
        for(uint256 a;a<16;++a)_target(address(currencies[a]));
        vm.resumeGasMetering();
    }
    function _target(address target)private{
        coldTargets.push(target);
    }
    function _cold()internal{
        uint256 reset;
        for(uint256 a;a<coldTargets.length;++a){
            address target=coldTargets[a];
            (bytes32[] memory r,bytes32[] memory w)=vm.accesses(target);
            // setUp completed in the preceding setup execution. Record only
            // reads/writes warmed inside THIS test transaction before the call;
            // unaccessed setup slots start cold without copying the setup log.
            for(uint256 i;i<r.length;++i){vm.coolSlot(target,r[i]);++reset;}
            for(uint256 i;i<w.length;++i){vm.coolSlot(target,w[i]);++reset;}
            vm.cool(target);
        }
        vm.cool(BOB);assertGt(reset,0,"Cold storage footprint must be material");
        emit LaunchClaimColdFootprint(coldTargets.length+1,reset);
    }
    function _nineteen()internal view returns(ZZZClaimRouter.Claim[] memory list){
        list=new ZZZClaimRouter.Claim[](19);uint256 id=ids[999];
        list[0]=ZZZClaimRouter.Claim(id,address(0),false);
        list[1]=ZZZClaimRouter.Claim(id,address(currencies[0]),false);
        list[2]=ZZZClaimRouter.Claim(id,address(0),true);
        for(uint256 a;a<16;++a)list[a+3]=ZZZClaimRouter.Claim(id,address(currencies[a]),true);
    }
    function _thirtyTwo()internal view returns(ZZZClaimRouter.Claim[] memory list){
        list=new ZZZClaimRouter.Claim[](32);
        for(uint256 i;i<16;++i){uint256 id=ids[900+i*5];
            list[2*i]=ZZZClaimRouter.Claim(id,address(0),false);
            list[2*i+1]=ZZZClaimRouter.Claim(id,address(currencies[0]),false);
        }
    }
    function _slice(ZZZClaimRouter.Claim[] memory list,uint256 first,uint256 count)
        internal pure returns(ZZZClaimRouter.Claim[] memory result){
        result=new ZZZClaimRouter.Claim[](count);for(uint256 i;i<count;++i)result[i]=list[first+i];
    }
    function _expected(ZZZClaimRouter.Claim[] memory list)internal view returns(uint256[] memory amounts){
        amounts=new uint256[](list.length);
        for(uint256 i;i<list.length;++i){ZZZClaimRouter.Claim memory e=list[i];
            assertEq(nft.ownerOf(e.nftId),BOB);
            amounts[i]=e.royalty?royalties.claimable(e.nftId,e.asset):rewards.claimable(e.nftId,e.asset);
            assertGt(amounts[i],0,"Each selected claim must be genuinely funded");
        }
    }
    function _cash()internal view returns(Cash memory c){c.eth=BOB.balance;for(uint256 a;a<16;++a)c.tokens[a]=currencies[a].balanceOf(BOB);}
    function _paid(ZZZClaimRouter.Claim[] memory list,uint256[] memory expected,uint256[] memory actual,Cash memory beforeCash)internal view{
        assertEq(actual.length,list.length);uint256 eth;uint256[16] memory token;
        for(uint256 i;i<list.length;++i){assertEq(actual[i],expected[i]);
            if(list[i].asset==address(0))eth+=actual[i];else{
                bool found;for(uint256 a;a<16;++a)if(list[i].asset==address(currencies[a])){token[a]+=actual[i];found=true;break;}assertTrue(found);
            }
            assertEq(list[i].royalty?royalties.claimable(list[i].nftId,list[i].asset):rewards.claimable(list[i].nftId,list[i].asset),0);
        }
        assertEq(BOB.balance-beforeCash.eth,eth);
        for(uint256 a;a<16;++a)assertEq(currencies[a].balanceOf(BOB)-beforeCash.tokens[a],token[a]);
    }
    function _digest()internal view returns(bytes32 h){
        h=keccak256(abi.encode(_cash(),rewards.liabilities(address(0)),rewards.liabilities(address(currencies[0])),
            address(rewards).balance,currencies[0].balanceOf(address(rewards)),membership.totalEligible(),royalties.totalWeight()));
        for(uint256 b;b<=4;++b){
            (uint256 weight,uint256 eth,uint256 zzz)=rewards.allocationTree(b);
            h=keccak256(abi.encode(h,b,weight,eth,zzz));
        }
        for(uint256 i;i<16;++i)h=_lpRightDigest(h,ids[900+i*6]);
        h=_lpRightDigest(h,ids[999]);h=_lpRightDigest(h,ids[0]);
        h=keccak256(abi.encode(h,address(fees).balance,currencies[0].balanceOf(address(fees)),
            fees.accounted(address(0)),fees.accounted(address(currencies[0])),
            fees.buybackBalance(address(0)),fees.buybackBalance(address(currencies[0]))));
        for(uint256 b=1;b<=4;++b)h=keccak256(abi.encode(h,b,
            fees.compoundBalance(b,address(0)),fees.compoundBalance(b,address(currencies[0])),
            fees.dust(b,address(0)),fees.dust(b,address(currencies[0]))));
        for(uint256 a;a<17;++a){address asset=a==0?address(0):address(currencies[a-1]);
            uint256 backing=a==0?address(royalties).balance:currencies[a-1].balanceOf(address(royalties));
            h=keccak256(abi.encode(h,asset,backing,royalties.accounted(asset),royalties.liabilities(asset),royalties.orphaned(asset)));
            h=keccak256(abi.encode(h,royalties.openingPool(asset),royalties.allocationCursor(asset),royalties.eligibleCount(asset),royalties.eligibleWeight(asset),
                royalties.claimable(ids[999],asset),royalties.claimable(ids[0],asset)));
        }
    }
    function _lpRightDigest(bytes32 h,uint256 id)private view returns(bytes32){
        (uint256 personalETH,uint256 collectiveETH)=rewards.claimableComponents(id,address(0));
        (uint256 personalZZZ,uint256 collectiveZZZ)=rewards.claimableComponents(id,address(currencies[0]));
        return keccak256(abi.encode(h,id,nft.ownerOf(id),shares.sharesOf(id),shares.nftBucket(id),
            personalETH,collectiveETH,personalZZZ,collectiveZZZ));
    }
    function _trial(ZZZClaimRouter.Claim[] memory list,bytes32 scenario)internal returns(bool ok,bytes memory result){
        bytes memory payload=abi.encodeCall(ZZZClaimRouter.claimBatch,(list));_cold();
        vm.prank(BOB);uint256 start=gasleft();(ok,result)=address(router).call{gas:CLAIM_GAS}(payload);
        uint256 used=start-gasleft();emit LaunchClaimEnvelope(scenario,list.length,CLAIM_GAS,used,ok);
    }
    /// @dev The first trial is a cold funded-state12M witness. Later successful
    /// chunks prove bounded functional recovery in this test, not separate cold
    /// transactions: EIP-2200 original-value state can differ across real txs.
    function _boundedOrSplit(ZZZClaimRouter.Claim[] memory list,bytes32 scenario)internal{
        uint256[] memory expected=_expected(list);Cash memory beforeCash=_cash();bytes32 beforeState=_digest();
        (bool ok,bytes memory result)=_trial(list,scenario);
        if(ok){_paid(list,expected,abi.decode(result,(uint256[])),beforeCash);return;}
        assertEq(_digest(),beforeState,"A refused envelope must preserve every observed right/backing field");
        for(uint256 first;first<list.length;first+=8){
            uint256 count=list.length-first;if(count>8)count=8;
            ZZZClaimRouter.Claim[] memory part=_slice(list,first,count);
            uint256[] memory partExpected=_expected(part);Cash memory partCash=_cash();
            (ok,result)=_trial(part,keccak256(abi.encode(scenario,first)));
            assertTrue(ok,"Prepare a smaller reviewed claim batch; never raise12M automatically");
            _paid(part,partExpected,abi.decode(result,(uint256[])),partCash);
        }
    }
}

contract LaunchClaimCapacityPending20261117Test is LaunchClaimFixture20261117 {
    function _storeRoyalties()internal pure override returns(bool){return false;}
    function testLaunchNineteenPendingMixedLedgerClaimsAtTwelveMillionWithSafeRecovery()public{
        vm.record();assertGt(royalties.pending(address(currencies[15])),0);
        vm.prank(ALICE);vm.expectRevert(ZZZClaimRouter.Unauthorized.selector);router.claimBatch(_nineteen());
        _boundedOrSplit(_nineteen(),keccak256("pending17royalty+2LP:1000active:claim12M"));
        assertEq(nft.ownerOf(ids[999]),BOB);assertEq(membership.totalEligible(),1000);
    }
}

contract LaunchClaimCapacityStored20261117Test is LaunchClaimFixture20261117 {
    function testLaunchThirtyTwoStoredLPClaimsAtTwelveMillionAndExactCountLimit()public{
        vm.record();ZZZClaimRouter.Claim[] memory list=_thirtyTwo();
        uint256 bucketsSeen;
        for(uint256 i;i<16;++i){
            uint256 id=list[2*i].nftId;address owner=nft.ownerOf(id);
            if(owner!=BOB){vm.prank(owner);nft.transferFrom(owner,BOB,id);}
            bucketsSeen|=uint256(1)<<shares.nftBucket(id);
        }
        assertEq(bucketsSeen,30,"Measured selection must actually span all four LP books");
        ZZZClaimRouter.Claim[] memory tooMany=new ZZZClaimRouter.Claim[](33);
        for(uint256 i;i<32;++i)tooMany[i]=list[i];tooMany[32]=list[0];
        bytes32 beforeState=_digest();vm.prank(BOB);vm.expectRevert(ZZZClaimRouter.InvalidBatch.selector);router.claimBatch(tooMany);
        assertEq(_digest(),beforeState);
        _boundedOrSplit(list,keccak256("32storedLP:16currentownerNFT:4buckets:claim12M"));
    }
    function testLaunchLastRoyaltyFaultRollsBackMixedClaimsThenHealthySubsetAndRecoveryPayExactly()public{
        vm.record();ZZZClaimRouter.Claim[] memory list=_nineteen();uint256[] memory expected=_expected(list);
        uint256 snapshot=vm.snapshotState();
        _boundedOrSplit(list,keccak256("stored17royalty+2LP:1000active:claim12M"));
        assertTrue(vm.revertToState(snapshot));
        currencies[15].reject(BOB);bytes32 beforeState=_digest();
        vm.expectCall(address(currencies[15]),abi.encodeWithSignature("transfer(address,uint256)",BOB,expected[18]));
        vm.prank(BOB);vm.expectRevert(LaunchClaimToken20261117.RecipientRejected.selector);router.claimBatch(list);
        assertEq(_digest(),beforeState,"Late selected-currency failure must roll back earlier LP/royalty payments");
        _boundedOrSplit(_slice(list,0,18),keccak256("healthy18withoutfailedcurrency:claim12M"));
        assertEq(royalties.claimable(ids[999],address(currencies[15])),expected[18]);
        assertGe(currencies[15].balanceOf(address(royalties)),royalties.liabilities(address(currencies[15])));
        currencies[15].reject(address(0));_boundedOrSplit(_slice(list,18,1),keccak256("recovered1originalcurrency:claim12M"));
        Cash memory beforeCash=_cash();vm.prank(BOB);uint256[] memory repeat=router.claimBatch(_slice(list,18,1));
        assertEq(repeat[0],0);assertEq(keccak256(abi.encode(_cash())),keccak256(abi.encode(beforeCash)));
        assertEq(nft.ownerOf(ids[999]),BOB);assertEq(membership.totalEligible(),1000);
    }
}
