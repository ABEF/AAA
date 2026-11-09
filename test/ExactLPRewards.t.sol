// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";

import {Vm} from "forge-std/Vm.sol";
import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {MockAccess,MockToken,MockPools} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {Ids,Position,PositionStatus,PoolKey,PoolConfig} from "../src/libraries/ZZZTypes.sol";

/// @dev TEST ONLY fixed-pair bootstrap identity, not a venue admission proof.
contract ExactLPFixedIdentity {address public immutable zzz;constructor(address token){zzz=token;}}

/// @dev TEST ONLY canonical share writer. No liquidity/valuation/pricing is
/// simulated here. Actual Rewards authenticates this fixed module, the real
/// NFT's immutable ordinals, aggregate writes and real Membership hooks.
contract ExactLPShareFixture {
    uint256 public constant ACCOUNTING_VERSION=7;
    uint256 public constant MAX_BUCKETS=4;
    ZZZRewards public immutable rewards;ZZZMembership public immutable members;
    ZZZNFT public immutable nft;ZZZFeeController public immutable fees;MockToken public immutable zzz;
    mapping(uint256=>uint256)public nftBucket;mapping(uint256=>uint256)public sharesOf;
    mapping(uint256=>uint256)public bucketTotalShares;mapping(uint256=>Position)private records;
    bool public failAfterSync;
    constructor(ZZZRewards r,ZZZMembership m,ZZZNFT n,ZZZFeeController f,MockToken token){rewards=r;members=m;nft=n;fees=f;zzz=token;}
    receive()external payable{}
    function mintProceedsRecipient()external pure returns(address payable){return payable(address(0x7EA5));}
    function migrationBudget()external view returns(address){return address(this);}
    function compositionEpoch(uint256)external pure returns(uint64){return 0;}
    function bucketCount()external pure returns(uint256){return 4;}
    function bucketAt(uint256 i)external pure returns(uint256){require(i<4);return i+1;}
    function setRecord(uint256 bucket,bytes32 pool)external{require(bucket>0&&bucket<=4);records[bucket].poolId=pool;records[bucket].status=PositionStatus.Active;}
    function group(uint256 bucket)external view returns(Position memory){return records[bucket];}
    function mint(address owner,uint256 id)external{nft.mint(owner,id);}
    function setFailAfterSync(bool value)external{failAfterSync=value;}
    function join(uint256 id,uint256 bucket,uint256 delta)external{
        require(bucket>0&&bucket<=4&&delta!=0&&(nftBucket[id]==0||nftBucket[id]==bucket));
        members.settleDust();nftBucket[id]=bucket;sharesOf[id]+=delta;bucketTotalShares[bucket]+=delta;
        rewards.syncShares(id);
        if(!members.eligible(id))members.activate(id);
        require(!failAfterSync,"TEST ONLY after-sync fault");nft.notifyContribution(id);
    }
    function malformed(uint256 id,uint256 bucket,uint256 weight,uint256 total)external{
        nftBucket[id]=bucket;sharesOf[id]=weight;bucketTotalShares[bucket]=total;rewards.syncShares(id);
    }
    function allocateETH(uint256 bucket)external payable{fees.allocate{value:msg.value}(bucket,address(0),msg.value);}
    function allocateZZZ(uint256 bucket,uint256 amount)external{zzz.approve(address(fees),amount);fees.allocate(bucket,address(zzz),amount);zzz.approve(address(fees),0);}
}

/// @dev TEST ONLY conversion accounting seam. It is NOT route/oracle/Uniswap
/// qualification. Actual converter execution is covered in LPRewardConversion
/// and TypedV4Rewards. Exact transfer deltas/callback rollback use real tokens.
contract ExactLPConverterFixture {
    address public immutable ledger;MockAccess public immutable access;MockToken public immutable token;
    uint8 public fault;
    constructor(address r,MockAccess a,MockToken t){ledger=r;access=a;token=t;}
    receive()external payable{}
    function setFault(uint8 value)external{fault=value;}
    function convert(address asset,uint256 amount,bytes32,uint256 minimum,uint256 deadline)external returns(uint256 output){
        require(msg.sender==ledger&&asset==address(token)&&deadline>=block.timestamp&&fault!=1);
        require(token.transferFrom(msg.sender,address(this),amount));output=amount;require(output>=minimum);
        if(fault==2)access.setPaused(true);
        (bool ok,)=payable(ledger).call{value:output}("");require(ok);
        if(fault==3)++output;
    }
}

contract ExactLPRejectingHolder is IERC721Receiver {
    bool public reject;ZZZNFT public immutable nft;ZZZRewards public immutable rewards;
    constructor(ZZZNFT n,ZZZRewards r){nft=n;rewards=r;}
    receive()external payable{require(!reject,"TEST ONLY rejecting owner");}
    function setReject(bool value)external{reject=value;}
    function claim(uint256 id,address asset)external returns(uint256){return rewards.claim(id,asset);}
    function transfer(address to,uint256 id)external{nft.transferFrom(address(this),to,id);}
    function onERC721Received(address,address,uint256,bytes calldata)external pure returns(bytes4){return IERC721Receiver.onERC721Received.selector;}
}

contract ExactLPRewardsTest is Test {
    MockAccess private access;MockToken private token;MockPools private pools;MockVRF private vrf;
    ZZZRewards private rewards;ZZZNFT private nft;ZZZMembership private members;ZZZFeeController private fees;
    ExactLPShareFixture private shares;ExactLPConverterFixture private converter;
    address private constant ALICE=address(0xA11CE);address private constant BOB=address(0xB0B);
    uint256 private nextId=10001;
    event ExactLPColdRouterSubset(uint256 activeNFTs,uint256 positiveNFTs,uint256 operations,uint256 rawGas,uint256 serviceBudget,bool withinServiceBudget);
    event ExactLPColdRouter32(uint256 activeNFTs,uint256 positiveNFTs,uint256 operations,uint256 rawGas,uint256 serviceBudget,bool withinServiceBudget);
    event ExactLPWire(uint8 indexed stage,bytes logs,bytes snapshot);
    struct WireSnapshot {
        address nft;address vault;address membership;address rewards;address fees;address zzz;
        uint256 id;uint256 bucket;uint256 shares;uint256 eligible;address owner;uint256 ordinal;
        uint256 individualETH;uint256 collectiveETH;uint256 individualZZZ;uint256 collectiveZZZ;
        uint256 bucketWeight;uint256 bucketETH;uint256 bucketZZZ;
        uint256 globalWeight;uint256 globalETH;uint256 globalZZZ;
        uint256 directETH;uint256 directZZZ;uint256 liabilityETH;uint256 liabilityZZZ;
    }
    event ExactLPColdGas(uint256 activeNFTs,uint256 nativeClaim,uint256 growth);
    function setUp()public{
        vm.warp(1_000_000);vm.deal(address(this),1_000_000 ether);access=new MockAccess();ProtocolPolicyFixture.bind(address(access));
        token=new MockToken(18);pools=new MockPools();pools.setActivationAssets(address(new ExactLPFixedIdentity(address(token))));
        nft=new ZZZNFT(address(access),"ipfs://TEST-ONLY/", address(new ZZZNFTMetadata(address(access))));nft.setMintEnd(uint64(block.timestamp+3650 days));
        members=new ZZZMembership(address(access));rewards=new ZZZRewards(address(access));fees=new ZZZFeeController(address(access));
        shares=new ExactLPShareFixture(rewards,members,nft,fees,token);
        access.bind(Ids.VAULT,address(shares));access.bind(Ids.NFT,address(nft));access.bind(Ids.MEMBERSHIP,address(members));
        access.bind(Ids.REWARDS,address(rewards));access.bind(Ids.FEES,address(fees));access.bind(Ids.POOLS,address(pools));access.bind(Ids.BUYBACK,address(this));
        access.setKeeper(address(this),true);rewards.addAsset(address(token));
        converter=new ExactLPConverterFixture(address(rewards),access,token);rewards.bindConverter(address(converter));vm.deal(address(converter),1000 ether);
        vrf=new MockVRF();ProtocolPolicyFixture.randomness(address(access),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        for(uint256 bucket=1;bucket<=4;++bucket){PoolConfig memory c;c.key=PoolKey(address(0),address(token),uint24(3000+bucket),60,address(0));bytes32 pool=keccak256(abi.encode(c.key));pools.set(pool,c);shares.setRecord(bucket,pool);}
        access.seal();
    }
    function _mint(address owner,uint256 bucket,uint256 weight)private returns(uint256 id){
        id=nextId;nextId+=7;shares.mint(owner,id);vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
        if(weight!=0)shares.join(id,bucket,weight);
    }
    function _fund(uint256 bucket,uint256 eth,uint256 zzz)private{
        if(eth!=0)shares.allocateETH{value:eth}(bucket);
        if(zzz!=0){token.mint(address(shares),zzz);shares.allocateZZZ(bucket,zzz);}
    }
    function _components(uint256 id,address asset)private view returns(uint256,uint256){return rewards.claimableComponents(id,asset);}
    function _assertBacking()private view{
        for(uint256 a;a<2;++a){address asset=a==0?address(0):address(token);uint256 sum=rewards.directLiabilities(asset);
            (,uint256 ge,uint256 gz)=rewards.allocationTree(0);sum+=a==0?ge:gz;
            for(uint256 b=1;b<=4;++b){(uint256 weight,uint256 e,uint256 z)=rewards.allocationTree(b);assertEq(weight,shares.bucketTotalShares(b));sum+=a==0?e:z;}
            assertEq(sum,rewards.liabilities(asset));assertEq(a==0?address(rewards).balance:token.balanceOf(address(rewards)),sum+rewards.orphaned(asset));
            uint256 classified=fees.buybackBalance(asset);for(uint256 b=1;b<=4;++b)classified+=fees.compoundBalance(b,asset)+fees.dust(b,asset);
            assertEq(classified,fees.accounted(asset));assertEq(a==0?address(fees).balance:token.balanceOf(address(fees)),classified);
        }
        (uint256 active,,)=rewards.allocationTree(0);assertEq(active,members.totalEligible());
    }
    function _claim(address owner,uint256 id,address asset)private returns(uint256 amount){
        amount=rewards.claimable(id,asset);uint256 before=asset==address(0)?owner.balance:token.balanceOf(owner);
        vm.prank(owner);assertEq(rewards.claim(id,asset),amount);assertEq((asset==address(0)?owner.balance:token.balanceOf(owner))-before,amount);
    }
    function testExactRewardsFinalReceiptPaysEveryAllocatedRawUnitBothCurrencies()public{
        uint256 id=_mint(ALICE,1,101e18+1);_fund(1,20,20);
        for(uint256 a;a<2;++a){address asset=a==0?address(0):address(token);(uint256 personal,uint256 shared)=_components(id,asset);
            assertEq(personal,16);assertEq(shared,2);assertEq(_claim(ALICE,id,asset),18);assertEq(rewards.liabilities(asset),0);
            assertEq(fees.compoundBalance(1,asset),1);assertEq(fees.buybackBalance(asset),1);assertEq(_claim(ALICE,id,asset),0);
        }_assertBacking();
    }
    function testExactRewardsNewActivationAndGrowthNeverAcquireEarlierRights()public{
        uint256 alice=_mint(ALICE,1,7e18);_fund(1,101,143);uint256 oldETH=rewards.claimable(alice,address(0));uint256 oldZZZ=rewards.claimable(alice,address(token));
        uint256 bob=_mint(BOB,1,11e18);assertEq(rewards.claimable(bob,address(0)),0);assertEq(rewards.claimable(bob,address(token)),0);
        assertGe(rewards.claimable(alice,address(0)),oldETH);assertGe(rewards.claimable(alice,address(token)),oldZZZ);
        uint256 beforeA=rewards.claimable(alice,address(0));uint256 beforeB=rewards.claimable(bob,address(0));shares.join(bob,1,100e18);
        assertEq(rewards.claimable(alice,address(0)),beforeA);assertEq(rewards.claimable(bob,address(0)),beforeB);
        _fund(1,400,600);assertGt(rewards.claimable(bob,address(0)),beforeB);_assertBacking();
        for(uint256 a;a<2;++a){address asset=a==0?address(0):address(token);_claim(ALICE,alice,asset);_claim(BOB,bob,asset);assertEq(rewards.liabilities(asset),0);}_assertBacking();
    }
    function testExactRewardsFailedPostWriteHookRestoresAllWeightsAndRights()public{
        uint256 alice=_mint(ALICE,1,101e18);uint256 bob=_mint(BOB,0,0);_fund(1,100,120);
        uint256 beforeA=rewards.claimable(alice,address(token));uint256 supply=shares.bucketTotalShares(1);shares.setFailAfterSync(true);
        vm.expectRevert();shares.join(bob,1,9e18);assertEq(shares.sharesOf(bob),0);assertEq(shares.nftBucket(bob),0);assertEq(shares.bucketTotalShares(1),supply);
        assertFalse(members.eligible(bob));assertEq(members.totalEligible(),1);assertEq(rewards.rewardBucket(bob),0);assertEq(rewards.claimable(alice,address(token)),beforeA);_assertBacking();
    }
    function testExactRewardsHookAuthorizationTotalsOrdinalsAndImmutableBuckets()public{
        uint256 id=_mint(ALICE,1,100e18);_fund(1,100,100);uint256 before=rewards.claimable(id,address(token));
        vm.expectRevert();rewards.syncShares(id);vm.expectRevert();rewards.syncMembership(id);
        vm.expectRevert();shares.malformed(id,2,100e18,100e18);vm.expectRevert();shares.malformed(id,1,99e18,99e18);
        vm.expectRevert();shares.malformed(id,1,101e18,102e18);vm.expectRevert();shares.malformed(999999,1,1,100e18+1);
        assertEq(shares.nftBucket(id),1);assertEq(shares.sharesOf(id),100e18);assertEq(rewards.claimable(id,address(token)),before);_assertBacking();
    }
    function testExactRewardsCanonicalParentWritesAndSendsRejectUnrelatedCaller()public{
        uint256 id=_mint(ALICE,1,100e18);_fund(1,20,20);uint256 owed=rewards.claimable(id,address(token));
        vm.expectRevert();rewards.canonicalWrite(2,bytes(""));
        vm.expectRevert();rewards.canonicalSend(address(token),ALICE,1);
        vm.expectRevert();rewards.canonicalSeed(1);
        assertEq(rewards.claimable(id,address(token)),owed);assertEq(token.balanceOf(ALICE),0);_assertBacking();
    }
    function testExactRewardsTransferClaimsAndRouterPreserveCurrentOwner()public{
        uint256 id=_mint(ALICE,1,100e18);_fund(1,100,200);uint256 eth=rewards.claimable(id,address(0));uint256 zzz=rewards.claimable(id,address(token));
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,id);vm.prank(ALICE);vm.expectRevert();rewards.claim(id,address(0));
        ZZZClaimRouter.Claim[] memory list=new ZZZClaimRouter.Claim[](2);list[0]=ZZZClaimRouter.Claim(id,address(0),false);list[1]=ZZZClaimRouter.Claim(id,address(token),false);
        ZZZClaimRouter router=nft.claimRouter();vm.prank(BOB);uint256[] memory paid=router.claimBatch(list);assertEq(paid[0],eth);assertEq(paid[1],zzz);assertEq(rewards.liabilities(address(0)),0);assertEq(rewards.liabilities(address(token)),0);_assertBacking();
    }
    function testExactRewardsRejectingOwnerFailureKeepsWholeMoneyAndRetry()public{
        ExactLPRejectingHolder holder=new ExactLPRejectingHolder(nft,rewards);uint256 id=_mint(address(holder),1,100e18);_fund(1,20,20);
        holder.setReject(true);vm.expectRevert();holder.claim(id,address(0));assertEq(rewards.claimable(id,address(0)),18);assertEq(rewards.liabilities(address(0)),18);
        holder.transfer(ALICE,id);assertEq(_claim(ALICE,id,address(0)),18);assertEq(_claim(ALICE,id,address(token)),18);_assertBacking();
    }
    function testExactRewardsConversionKeepsSameNFTComponentsAndNativeBacking()public{
        uint256 a=_mint(ALICE,1,1e18);uint256 b=_mint(BOB,1,3e18);_fund(1,400,800);
        (uint256 ap,uint256 ac)=_components(a,address(token));(uint256 bp,uint256 bc)=_components(b,address(token));
        (uint256 oldAP,uint256 oldAC)=_components(a,address(0));(uint256 oldBP,uint256 oldBC)=_components(b,address(0));
        uint256 newcomer=_mint(ALICE,1,99e18);uint256[] memory ids=new uint256[](2);ids[0]=a;ids[1]=b;
        assertEq(rewards.convertBatch(address(token),ids,bytes32(uint256(1)),ap+ac+bp+bc,block.timestamp+100),ap+ac+bp+bc);
        (uint256 afterP,uint256 afterC)=_components(a,address(0));assertEq(afterP,oldAP+ap);assertEq(afterC,oldAC+ac);
        (afterP,afterC)=_components(b,address(0));assertEq(afterP,oldBP+bp);assertEq(afterC,oldBC+bc);assertEq(rewards.claimable(newcomer,address(0)),0);
        assertEq(rewards.claimable(a,address(token)),0);assertEq(rewards.claimable(b,address(token)),0);assertEq(token.allowance(address(rewards),address(converter)),0);
        _assertBacking();_claim(ALICE,a,address(0));_claim(BOB,b,address(0));_assertBacking();
    }
    function testExactRewardsConversionFaultOrPauseRollsBackBooksAndReserves()public{
        uint256 id=_mint(ALICE,1,100e18);_fund(1,100,100);uint256[] memory ids=new uint256[](1);ids[0]=id;
        uint256 prior=rewards.claimable(id,address(token));uint256 compound=fees.compoundBalance(1,address(token));uint256 burn=fees.buybackBalance(address(token));
        for(uint8 fault=1;fault<=3;++fault){converter.setFault(fault);vm.expectRevert();rewards.convertBatch(address(token),ids,bytes32(uint256(1)),1,block.timestamp+100);
            assertEq(rewards.claimable(id,address(token)),prior);assertFalse(access.paused());assertEq(rewards.directLiabilities(address(0)),0);assertEq(fees.compoundBalance(1,address(token)),compound);assertEq(fees.buybackBalance(address(token)),burn);_assertBacking();
        }converter.setFault(0);assertEq(rewards.convertBatch(address(token),ids,bytes32(uint256(1)),1,block.timestamp+100),prior);_assertBacking();
    }
    function testExactRewardsClaimsStayAvailableWhenPaused()public{
        uint256 id=_mint(ALICE,1,100e18);_fund(1,20,20);access.setPaused(true);assertEq(_claim(ALICE,id,address(0)),18);assertEq(_claim(ALICE,id,address(token)),18);_assertBacking();
    }
    function _thousand()private returns(uint256[] memory ids){
        ids=new uint256[](1000);for(uint256 i;i<1000;++i){address owner=address(uint160(0x100000+i%37));ids[i]=_mint(owner,i%4+1,i%10==0?0:(i%101+1)*1e18);}
        assertEq(nft.mintedCount(),1000);assertEq(members.totalEligible(),900);for(uint256 b=1;b<=4;++b)_fund(b,20*(b+17),20*(b+23));
    }
    function testExactRewards1000MintedMixedWalletDormancyAndAllUnitsClaimed()public{
        // Functional multi-transaction aggregation only. Metering is paused for
        // this test's1000separate-owner calls; no1000claim productionTx exists.
        vm.pauseGasMetering();uint256[] memory ids=_thousand();_assertBacking();uint256 expectedETH=rewards.liabilities(address(0));uint256 expectedZZZ=rewards.liabilities(address(token));uint256 eth;uint256 zzz;
        for(uint256 i;i<1000;++i){address owner=nft.ownerOf(ids[i]);if(i%10==0){assertEq(rewards.claimable(ids[i],address(0)),0);assertEq(rewards.claimable(ids[i],address(token)),0);}eth+=_claim(owner,ids[i],address(0));zzz+=_claim(owner,ids[i],address(token));}
        assertEq(eth,expectedETH);assertEq(zzz,expectedZZZ);assertEq(rewards.liabilities(address(0)),0);assertEq(rewards.liabilities(address(token)),0);_assertBacking();vm.resumeGasMetering();
    }
    function testExactRewardsColdMaximumCohortClaimAndGrowthGas()public{
        vm.pauseGasMetering();uint256[] memory ids=_thousand();uint256 id=ids[1];address owner=nft.ownerOf(id);_fund(2,1e12,1e12);vm.resumeGasMetering();
        vm.cool(address(rewards));vm.cool(address(nft));vm.cool(address(shares));vm.cool(address(members));vm.cool(address(access));
        uint256 start=gasleft();vm.prank(owner);uint256 paid=rewards.claim(id,address(0));uint256 claimGas=start-gasleft();assertGt(paid,0);
        _fund(2,100,100);vm.cool(address(rewards));vm.cool(address(nft));vm.cool(address(shares));vm.cool(address(members));vm.cool(address(access));vm.cool(address(fees));
        start=gasleft();shares.join(id,2,5e18);uint256 growthGas=start-gasleft();emit ExactLPColdGas(900,claimGas,growthGas);_assertBacking();
    }
    function _wireSnapshot(uint256 id)private view returns(bytes memory){
        WireSnapshot memory w;w.nft=address(nft);w.vault=address(shares);w.membership=address(members);
        w.rewards=address(rewards);w.fees=address(fees);w.zzz=address(token);w.id=id;w.bucket=shares.nftBucket(id);w.shares=shares.sharesOf(id);w.eligible=members.totalEligible();w.owner=nft.ownerOf(id);w.ordinal=nft.mintOrdinalOf(id);
        (w.individualETH,w.collectiveETH)=rewards.claimableComponents(id,address(0));(w.individualZZZ,w.collectiveZZZ)=rewards.claimableComponents(id,address(token));
        (w.bucketWeight,w.bucketETH,w.bucketZZZ)=rewards.allocationTree(1);(w.globalWeight,w.globalETH,w.globalZZZ)=rewards.allocationTree(0);
        w.directETH=rewards.directLiabilities(address(0));w.directZZZ=rewards.directLiabilities(address(token));w.liabilityETH=rewards.liabilities(address(0));w.liabilityZZZ=rewards.liabilities(address(token));return abi.encode(w);
    }
    function testExactRewardsActualWireProducerBothBooks()public{
        vm.recordLogs();uint256 id=_mint(ALICE,1,101);Vm.Log[] memory records=vm.getRecordedLogs();emit ExactLPWire(0,abi.encode(records),_wireSnapshot(id));
        vm.recordLogs();_fund(1,20,20);records=vm.getRecordedLogs();emit ExactLPWire(1,abi.encode(records),_wireSnapshot(id));
        (uint256 personal,uint256 shared)=rewards.claimableComponents(id,address(0));assertEq(personal,16);assertEq(shared,2);
        vm.recordLogs();assertEq(_claim(ALICE,id,address(0)),18);assertEq(_claim(ALICE,id,address(token)),18);records=vm.getRecordedLogs();emit ExactLPWire(2,abi.encode(records),_wireSnapshot(id));_assertBacking();
    }

    function testExactRewardsDeficitBlocksOnlyAffectedBookAndPreservesWholeRights()public{
        uint256 a=_mint(ALICE,1,1e18);uint256 b=_mint(BOB,1,3e18);_fund(1,400,800);
        uint256 aETH=rewards.claimable(a,address(0));uint256 bETH=rewards.claimable(b,address(0));uint256 ethLiability=rewards.liabilities(address(0));
        vm.deal(address(rewards),ethLiability-1);vm.prank(ALICE);vm.expectRevert();rewards.claim(a,address(0));
        assertEq(rewards.claimable(a,address(0)),aETH);assertEq(rewards.claimable(b,address(0)),bETH);assertEq(rewards.liabilities(address(0)),ethLiability);
        assertGt(_claim(ALICE,a,address(token)),0);assertGt(_claim(BOB,b,address(token)),0);
        vm.deal(address(rewards),ethLiability);assertEq(_claim(ALICE,a,address(0)),aETH);assertEq(_claim(BOB,b,address(0)),bETH);_assertBacking();
        _fund(1,400,800);uint256 aZZZ=rewards.claimable(a,address(token));uint256 bZZZ=rewards.claimable(b,address(token));uint256 zzzLiability=rewards.liabilities(address(token));
        vm.prank(address(rewards));token.burn(1);vm.prank(BOB);vm.expectRevert();rewards.claim(b,address(token));
        assertEq(rewards.claimable(a,address(token)),aZZZ);assertEq(rewards.claimable(b,address(token)),bZZZ);assertEq(rewards.liabilities(address(token)),zzzLiability);
        assertGt(_claim(ALICE,a,address(0)),0);assertGt(_claim(BOB,b,address(0)),0);
        token.mint(address(rewards),1);assertEq(_claim(ALICE,a,address(token)),aZZZ);assertEq(_claim(BOB,b,address(token)),bZZZ);_assertBacking();
    }

    function testExactRewardsColdRouter32FundedEntriesAtMaximumMintedCohort()public{
        vm.pauseGasMetering();uint256[] memory ids=_thousand();
        for(uint256 bucket=1;bucket<=4;++bucket)_fund(bucket,1e15,1e15);
        address owner=address(0x100001);ZZZClaimRouter router=nft.claimRouter();
        ZZZClaimRouter.Claim[] memory entries=new ZZZClaimRouter.Claim[](32);uint256 count;uint256 expectedETH;uint256 expectedZZZ;
        for(uint256 i;i<1000&&count<16;++i)if(nft.ownerOf(ids[i])==owner&&members.eligible(ids[i])){
            uint256 eth=rewards.claimable(ids[i],address(0));uint256 zzz=rewards.claimable(ids[i],address(token));assertGt(eth,0);assertGt(zzz,0);
            entries[2*count]=ZZZClaimRouter.Claim(ids[i],address(0),false);entries[2*count+1]=ZZZClaimRouter.Claim(ids[i],address(token),false);expectedETH+=eth;expectedZZZ+=zzz;++count;
        }
        assertEq(count,16);uint256 beforeETH=owner.balance;uint256 beforeZZZ=token.balanceOf(owner);
        vm.cool(address(router));vm.cool(address(rewards));vm.cool(address(nft));vm.cool(address(access));vm.cool(address(token));vm.cool(owner);
        vm.resumeGasMetering();vm.prank(owner);uint256 start=gasleft();uint256[] memory paid=router.claimBatch(entries);uint256 used=start-gasleft();
        uint256 actualETH;uint256 actualZZZ;for(uint256 i;i<paid.length;++i){assertGt(paid[i],0);if(i%2==0)actualETH+=paid[i];else actualZZZ+=paid[i];}
        assertEq(actualETH,expectedETH);assertEq(actualZZZ,expectedZZZ);assertEq(owner.balance-beforeETH,expectedETH);assertEq(token.balanceOf(owner)-beforeZZZ,expectedZZZ);
        emit ExactLPColdRouter32(900,16,32,used,12_000_000,used<=12_000_000);_assertBacking();
    }

    function testExactRewardsColdRouterEightFundedEntriesAtMaximumMintedCohort()public{
        vm.pauseGasMetering();uint256[] memory ids=_thousand();
        for(uint256 bucket=1;bucket<=4;++bucket)_fund(bucket,1e15,1e15);
        address owner=address(0x100001);ZZZClaimRouter router=nft.claimRouter();
        ZZZClaimRouter.Claim[] memory entries=new ZZZClaimRouter.Claim[](8);uint256 count;uint256 expectedETH;uint256 expectedZZZ;uint256 bucketsSeen;
        for(uint256 i;i<1000&&count<4;++i)if(nft.ownerOf(ids[i])==owner&&members.eligible(ids[i])){
            uint256 eth=rewards.claimable(ids[i],address(0));uint256 zzz=rewards.claimable(ids[i],address(token));assertGt(eth,0);assertGt(zzz,0);bucketsSeen|=1<<shares.nftBucket(ids[i]);
            entries[2*count]=ZZZClaimRouter.Claim(ids[i],address(0),false);entries[2*count+1]=ZZZClaimRouter.Claim(ids[i],address(token),false);expectedETH+=eth;expectedZZZ+=zzz;++count;
        }
        assertEq(count,4);assertEq(bucketsSeen,30);uint256 beforeETH=owner.balance;uint256 beforeZZZ=token.balanceOf(owner);
        vm.cool(address(router));vm.cool(address(rewards));vm.cool(address(nft));vm.cool(address(access));vm.cool(address(token));vm.cool(owner);
        vm.resumeGasMetering();vm.prank(owner);uint256 start=gasleft();uint256[] memory paid=router.claimBatch(entries);uint256 used=start-gasleft();
        uint256 actualETH;uint256 actualZZZ;for(uint256 i;i<paid.length;++i){assertGt(paid[i],0);if(i%2==0)actualETH+=paid[i];else actualZZZ+=paid[i];}
        assertEq(actualETH,expectedETH);assertEq(actualZZZ,expectedZZZ);assertEq(owner.balance-beforeETH,expectedETH);assertEq(token.balanceOf(owner)-beforeZZZ,expectedZZZ);
        emit ExactLPColdRouterSubset(900,4,8,used,12_000_000,used<=12_000_000);_assertBacking();
    }

}
