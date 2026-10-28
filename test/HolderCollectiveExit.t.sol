// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {Ids,PoolKey,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {ExactAsset} from "../src/libraries/ExactAsset.sol";
import {MockAccess,MockToken,MockPools,MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
using DualOracleFixture for ZZZOracle;

/// @dev Deliberately fake venue quantities; real Vault, NFT, fee/reward and
/// settlement modules compose below. Not target-chain market qualification.
contract HolderExitVenue is ERC721 {
    MockToken public immutable token;
    uint256 public next=1;
    uint256 public fee0;
    uint256 public fee1;
    bool public rejectClose;
    mapping(uint256=>uint256) public a0;
    mapping(uint256=>uint256) public a1;
    constructor(MockToken t) ERC721("Exit fixture LP","EXITLP") { token=t; }
    receive() external payable {}
    function positionManager() external view returns(address) {return address(this);}
    function balanceContext(bytes32) external pure returns(bytes32){return bytes32(0);}
    function balance(bytes32,uint256,uint256 x,uint256 y,uint256) external payable returns(uint256,uint256) {
        require(msg.value==x);
        ExactAsset.push(address(0),msg.sender,x);
        return(x,y); // Exit accounting fixture, not a market sizing substitute.
    }
    function amounts(uint256 id) external view returns(uint256,uint256) {return(a0[id],a1[id]);}
    function ticks(uint256) external pure returns(int24,int24) {return(-600,600);}
    function spot(bytes32) external pure returns(uint160) {return uint160(1<<96);}
    function setFees(uint256 x,uint256 y) external {fee0=x;fee1=y;}
    function setReject(bool value) external {rejectClose=value;}
    function mint(bytes32,int24,int24,uint256 x,uint256 y,uint128,uint256)
        external payable returns(uint256 id,uint256,uint256) {
        require(msg.value==x);id=next++;_mint(msg.sender,id);require(token.transferFrom(msg.sender,address(this),y));
        a0[id]=x;a1[id]=y;return(id,x,y);
    }
    function increase(bytes32,uint256 id,uint256 x,uint256 y,uint128,uint256)
        external payable returns(uint256,uint256) {
        require(msg.value==x);require(token.transferFrom(msg.sender,address(this),y));a0[id]+=x;a1[id]+=y;return(x,y);
    }
    function collect(bytes32,uint256,uint256) external {
        uint256 x=fee0;uint256 y=fee1;fee0=0;fee1=0;
        ExactAsset.push(address(0),msg.sender,x);token.mint(msg.sender,y);
    }
    function close(bytes32,uint256 id,uint256) external {
        require(!rejectClose);uint256 x=a0[id];uint256 y=a1[id];delete a0[id];delete a1[id];_burn(id);
        ExactAsset.push(address(0),msg.sender,x);ExactAsset.push(address(token),msg.sender,y);
    }
}
contract HolderExitPolicy {
    function needsRebalance(uint256) external pure returns(bool) {return true;}
    function target(bytes32) external pure returns(int24,int24,uint160) {return(-600,600,uint160(1<<96));}
    function validatePrice(bytes32) external pure returns(uint160) {return uint160(1<<96);}
    function validateExitPrice(bytes32) external pure returns(uint160) {return uint160(1<<96);}
    function compoundPlan(uint256,uint256,uint256) external pure returns(bool,uint256,uint256) {return(false,0,0);}
    function swapPlan(bytes32,uint256,uint256) external pure returns(bool,uint256,uint256) {return(false,0,0);}
}
interface IHolderExitCallback {function tryExitDuringTransfer() external;}
contract HolderExitCallbackToken is MockToken {
    address public callback;address public triggerFrom;
    constructor() MockToken(18) {}
    function arm(address target,address from) external {callback=target;triggerFrom=from;}
    function _update(address from,address to,uint256 amount) internal override {
        super._update(from,to,amount);
        if(callback!=address(0)&&from==triggerFrom&&amount!=0)IHolderExitCallback(callback).tryExitDuringTransfer();
    }
}
contract HolderExitIdentity {address public immutable zzz;constructor(address t){zzz=t;}}
contract RejectHolderETH {
    receive() external payable {revert("cannot receive ETH");}
    function recover(ZZZMigration migration,uint256 id,address recipient) external {migration.claimPrincipal(id,recipient);}
}
contract ReenterHolderETH {
    ZZZMigration public migration;uint256 public id;bool public reentered;
    function configure(ZZZMigration m,uint256 i) external {migration=m;id=i;}
    receive() external payable {
        (reentered,)=address(migration).call(abi.encodeCall(ZZZMigration.claimPrincipal,(id,address(this))));
    }
}
contract GasConsumingHolderETH {receive() external payable {while(true){assembly{pop(gas())}}}}

contract HolderCollectiveExitTest is Test {
    event MetadataUpdate(uint256 tokenId);
    MockAccess ac;HolderExitCallbackToken token;MockPools pools;HolderExitVenue venue;ZZZVault vault;ZZZNFT nft;
    ZZZMigration migration;ZZZMembership membership;ZZZRewards rewards;ZZZFeeController fees;ZZZOracle oracle;MockVRF vrf;
    bytes32 poolId;bytes32 review=keccak256("reviewed holder exit fixture");
    address alice=address(0xA11CE);address bob=address(0xB0B);address payable treasury=payable(address(0x7EA5));
    receive() external payable {}
    function setUp() public {
        vm.warp(1_000_000);ac=new MockAccess();token=new HolderExitCallbackToken();pools=new MockPools();venue=new HolderExitVenue(token);
        oracle=new ZZZOracle(address(ac),address(0));MockFeed feed=new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(feed),1 hours);oracle.setTestFeed(address(token),address(feed),1 hours);
        vault=new ZZZVault(address(ac),block.chainid,treasury);nft=new ZZZNFT(address(ac),"ipfs://exit/");
        membership=new ZZZMembership(address(ac));rewards=new ZZZRewards(address(ac));fees=new ZZZFeeController(address(ac));
        migration=new ZZZMigration(address(ac));
        ac.bind(Ids.VAULT,address(vault));ac.bind(Ids.NFT,address(nft));ac.bind(Ids.MEMBERSHIP,address(membership));
        ac.bind(Ids.REWARDS,address(rewards));ac.bind(Ids.FEES,address(fees));ac.bind(Ids.ORACLE,address(oracle));
        ac.bind(Ids.POOLS,address(pools));ac.bind(Ids.LIQUIDITY,address(venue));ac.bind(Ids.STRATEGY,address(new HolderExitPolicy()));
        ac.bind(Ids.MIGRATION,address(migration));ac.bind(Ids.BUYBACK,address(new ZZZBuyback(address(ac),address(token),1e30)));
        ac.setKeeper(address(this),true);rewards.addAsset(address(token));
        pools.setActivationAssets(address(new HolderExitIdentity(address(token))));
        migration.configureZZZ(address(token),address(token).codehash,review);
        PoolConfig memory c;c.key=PoolKey(address(0),address(token),10020,60,address(0));c.operationsEnabled=true;c.depositsEnabled=true;
        c.rangeBps=1000;c.triggerBps=100;c.maxSpotDeviationBps=100;c.maxSlippageBps=200;c.minRebalanceInterval=600;
        c.minDepositUSD=5e18;c.maxPositionUSD=1e30;poolId=keccak256(abi.encode(c.key));pools.set(poolId,c);
        vrf=new MockVRF();nft.configureRandomness(address(vrf),bytes32(uint256(1)),1,3,500000,false);
        CanonicalFixture.bind(address(ac));ac.seal();
        vm.deal(alice,10000 ether);vm.deal(bob,10000 ether);vm.deal(address(this),10000 ether);vm.deal(address(venue),10000 ether);
        token.mint(alice,10000 ether);token.mint(bob,10000 ether);
        vm.prank(alice);token.approve(address(vault),type(uint256).max);vm.prank(bob);token.approve(address(vault),type(uint256).max);
    }
    function _mint(address who) private returns(uint256 id) {
        vm.prank(who);id=vault.mintDormant{value:0.05 ether}();vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
    }
    function _activate(address who,uint256 amount) private returns(uint256 id) {
        id=_mint(who);vm.prank(who);vault.activate{value:amount}(id,poolId,amount,amount,1,block.timestamp+100);
    }
    function _start() private {ac.setPaused(true);migration.beginCollectiveExit(review);}
    function _ready(uint256 bucket) private {_start();migration.closeBucket(bucket,0,0,block.timestamp+100);migration.allocatePrincipal(32);}
    function _ids(uint256 first,uint256 second) private pure returns(uint256[] memory ids) {ids=new uint256[](2);ids[0]=first;ids[1]=second;}
    function testPrincipalIsProportionalNotEqualAndExactAfterAutomaticPayout() public {
        uint256 a=_activate(alice,100 ether);uint256 b=_activate(bob,300 ether);uint256 bucket=vault.nftBucket(a);
        uint256 aShares=vault.sharesOf(a);uint256 bShares=vault.sharesOf(b);assertEq(bShares,3*aShares);
        _ready(bucket);(uint256 x,uint256 y)=migration.claimablePrincipal(a);assertEq(x,100 ether);assertEq(y,100 ether);
        uint256 beforeA=alice.balance;uint256 beforeB=bob.balance;uint256 tokenA=token.balanceOf(alice);uint256 tokenB=token.balanceOf(bob);
        vm.prank(address(0xCA11));assertEq(migration.distributePrincipal(_ids(a,b)),2);
        assertEq(alice.balance-beforeA,100 ether);assertEq(bob.balance-beforeB,300 ether);
        assertEq(token.balanceOf(alice)-tokenA,100 ether);assertEq(token.balanceOf(bob)-tokenB,300 ether);
        assertEq(migration.remainingETH(),0);assertEq(migration.remainingZZZ(),0);
        assertEq(vault.sharesOf(a),aShares);assertEq(vault.sharesOf(b),bShares);assertTrue(membership.eligible(a));
    }
    function testFinalHarvestAndPendingCompoundPreserveEarnedClaimsAndBuyback() public {
        uint256 a=_activate(alice,100 ether);uint256 bucket=vault.nftBucket(a);
        venue.setFees(20 ether,40 ether);vault.collectFees(bucket,block.timestamp+100);
        assertEq(rewards.claimable(a,address(0)),18 ether);assertEq(fees.compoundBalance(bucket,address(0)),1 ether);
        venue.setFees(20 ether,20 ether);_ready(bucket);
        (uint256 x,uint256 y)=migration.claimablePrincipal(a);assertEq(x,102 ether);assertEq(y,103 ether);
        assertEq(rewards.claimable(a,address(0)),36 ether);assertEq(rewards.claimable(a,address(token)),54 ether);
        assertEq(fees.buybackBalance(address(0)),2 ether);assertEq(fees.buybackBalance(address(token)),3 ether);
        assertEq(fees.compoundBalance(bucket,address(0)),0);assertEq(fees.compoundBalance(bucket,address(token)),0);
        vm.prank(alice);assertEq(rewards.claim(a,address(0)),36 ether);
        assertEq(rewards.claimable(a,address(token)),54 ether);
    }
    function testUnpaidPrincipalAndPastRewardsFollowTransferAndFutureRoyaltiesContinue() public {
        uint256 a=_activate(alice,100 ether);uint256 bucket=vault.nftBucket(a);venue.setFees(20 ether,0);_ready(bucket);
        vm.prank(alice);nft.transferFrom(alice,bob,a);uint256 before=bob.balance;
        vm.prank(alice);vm.expectRevert();migration.claimPrincipal(a,alice);
        vm.prank(bob);migration.claimPrincipal(a,bob);assertEq(bob.balance-before,101 ether);
        vm.prank(bob);assertEq(rewards.claim(a,address(0)),18 ether);
        (bool sent,)=address(nft.royaltyRewards()).call{value:5 ether}("");assertTrue(sent);
        ZZZRoyaltyRewards royalty=nft.royaltyRewards();
        vm.prank(bob);assertEq(royalty.claim(a,address(0)),5 ether);
        assertEq(nft.royaltyRewards().weightOf(a),1);(bool available,uint256 value)=nft.currentLPValue(a);assertTrue(available);assertEq(value,0);
    }
    function testRejectingRecipientDoesNotBlockOthersAndCanChooseFallback() public {
        uint256 a=_activate(alice,100 ether);uint256 b=_activate(bob,100 ether);RejectHolderETH rejector=new RejectHolderETH();
        vm.prank(alice);nft.transferFrom(alice,address(rejector),a);_ready(vault.nftBucket(a));
        uint256 before=token.balanceOf(address(rejector));assertEq(migration.distributePrincipal(_ids(a,b)),1);
        assertEq(token.balanceOf(address(rejector)),before);(,,,bool paid)=migration.principalOf(a);assertFalse(paid);
        assertEq(migration.remainingETH(),100 ether);assertEq(migration.remainingZZZ(),100 ether);
        rejector.recover(migration,a,alice);(,,,paid)=migration.principalOf(a);assertTrue(paid);
    }
    function testGasConsumingRecipientIsIsolatedAndLaterRecipientPaid() public {
        uint256 a=_activate(alice,100 ether);uint256 b=_activate(bob,100 ether);GasConsumingHolderETH rejector=new GasConsumingHolderETH();
        vm.prank(alice);nft.transferFrom(alice,address(rejector),a);_ready(vault.nftBucket(a));
        assertEq(migration.distributePrincipal(_ids(a,b)),1);(,,,bool paid)=migration.principalOf(a);assertFalse(paid);
        (,,,paid)=migration.principalOf(b);assertTrue(paid);
    }
    function testDoubleClaimsDuplicateBatchAndReentrancyCannotPayTwice() public {
        uint256 a=_activate(alice,100 ether);ReenterHolderETH receiver=new ReenterHolderETH();receiver.configure(migration,a);
        vm.prank(alice);nft.transferFrom(alice,address(receiver),a);_ready(vault.nftBucket(a));
        assertEq(migration.distributePrincipal(_ids(a,a)),1);assertFalse(receiver.reentered());
        assertEq(address(receiver).balance,100 ether);assertEq(token.balanceOf(address(receiver)),100 ether);
        assertEq(migration.remainingETH(),0);assertEq(migration.distributePrincipal(_ids(a,a)),0);
    }
    function testPrefundsNeverJoinPrincipalAndRemainAfterCompletePayout() public {
        uint256 a=_activate(alice,100 ether);vm.deal(address(migration),7 ether);token.mint(address(migration),9 ether);
        vm.deal(address(vault),address(vault).balance+11 ether);token.mint(address(vault),13 ether);
        _ready(vault.nftBucket(a));uint256[] memory ids=new uint256[](1);ids[0]=a;migration.distributePrincipal(ids);
        assertEq(address(migration).balance,7 ether);assertEq(token.balanceOf(address(migration)),9 ether);
        assertEq(address(vault).balance,11 ether);assertEq(token.balanceOf(address(vault)),13 ether);
    }
    function testExitWithoutHealthyPricesOrEnabledPoolAndRawMinimumRollback() public {
        uint256 a=_activate(alice,100 ether);uint256 bucket=vault.nftBucket(a);PoolConfig memory c=pools.get(poolId);
        c.operationsEnabled=false;c.depositsEnabled=false;pools.set(poolId,c);vm.warp(block.timestamp+4000);_start();
        uint256 lp=vault.group(bucket).lpTokenId;vm.expectRevert();migration.closeBucket(bucket,101 ether,0,block.timestamp+100);
        assertEq(venue.ownerOf(lp),address(vault));assertEq(migration.remainingBuckets(),1);
        migration.closeBucket(bucket,100 ether,100 ether,block.timestamp+100);migration.allocatePrincipal(32);
        assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Exited));
    }
    function testOnlyGovernanceStartsAndCannotReopenOrStartTwice() public {
        uint256 a=_activate(alice,100 ether);uint256 dormant=_mint(alice);uint256 bucket=vault.nftBucket(a);ac.setPaused(true);
        vm.prank(alice);vm.expectRevert();migration.beginCollectiveExit(review);migration.beginCollectiveExit(review);
        vm.expectRevert();migration.beginCollectiveExit(review);ac.setPaused(false);
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}();
        vm.prank(alice);vm.expectRevert();vault.increase{value:5 ether}(a,5 ether,5 ether,1,block.timestamp+100);
        vm.prank(alice);vm.expectRevert();vault.activate{value:100 ether}(dormant,poolId,100 ether,100 ether,1,block.timestamp+100);
        vm.expectRevert();vault.rebalance(bucket,1,block.timestamp+100);
        vm.expectRevert();migration.resume(bucket,poolId,1,block.timestamp+100);
        vm.expectRevert();migration.moveFunds(bucket,poolId,1,block.timestamp+100);
        ZZZMigration.ParkingRequest memory r;vm.expectRevert();migration.park(r);
    }
    function testDormantHasNoPrincipalAndAllocationBoundsAreEnforced() public {
        uint256 dormant=_mint(alice);uint256 active=_activate(alice,100 ether);uint256 bucket=vault.nftBucket(active);_start();
        vm.expectRevert();migration.allocatePrincipal(1);migration.closeBucket(bucket,0,0,block.timestamp+100);
        vm.expectRevert();migration.allocatePrincipal(0);vm.expectRevert();migration.allocatePrincipal(33);
        migration.allocatePrincipal(1);assertEq(uint256(migration.exitPhase()),uint256(ZZZMigration.ExitPhase.Allocating));
        vm.expectRevert();migration.claimablePrincipal(active);
        vm.expectEmit(false,false,false,true,address(nft));emit MetadataUpdate(active);migration.allocatePrincipal(1);
        (uint256 x,uint256 y)=migration.claimablePrincipal(dormant);assertEq(x,0);assertEq(y,0);
        (x,y)=migration.claimablePrincipal(active);assertEq(x,100 ether);assertEq(y,100 ether);
    }
    bool public exitCallbackSucceeded;
    bool public exitCallbackAttempted;
    function tryExitDuringTransfer() external {
        require(msg.sender==address(token));exitCallbackAttempted=true;ac.setPaused(true);
        (exitCallbackSucceeded,)=address(migration).call(abi.encodeCall(ZZZMigration.beginCollectiveExit,(review)));
        ac.setPaused(false);
    }
    function testExitCannotStartInsideAnInFlightContributionCallback() public {
        uint256 a=_activate(alice,100 ether);token.arm(address(this),alice);
        vm.prank(alice);vault.increase{value:5 ether}(a,5 ether,5 ether,1,block.timestamp+100);
        assertTrue(exitCallbackAttempted);assertFalse(exitCallbackSucceeded);assertFalse(ac.lpExitStarted());
        assertEq(uint256(migration.exitPhase()),uint256(ZZZMigration.ExitPhase.Operating));
    }
    function testObsoleteExternalCustodySelectorsAreAbsent() public {
        bytes4[4] memory selectors=[bytes4(keccak256("exit(bytes32)")),bytes4(keccak256("recover(bytes32,uint256)")),
            bytes4(keccak256("completeLocal(bytes32,uint256,uint256,uint128,uint256)")),bytes4(keccak256("bindLocalDestination(bytes32,bytes32,uint256,uint256,bytes32)"))];
        for(uint256 i;i<selectors.length;++i){(bool ok,)=address(migration).call(abi.encodeWithSelector(selectors[i]));assertFalse(ok);}
    }
    function testFuzzCumulativeAllocationConservesEveryRawUnit(uint96 first,uint96 second,uint96 fee) public {
        uint256 a0=bound(first,50 ether,500 ether);uint256 a1=bound(second,50 ether,500 ether);uint256 f=bound(fee,0,100 ether);
        uint256 a=_activate(alice,a0);uint256 b=_activate(bob,a1);uint256 bucket=vault.nftBucket(a);venue.setFees(f,f);
        _ready(bucket);(uint256 x,uint256 y)=migration.claimablePrincipal(a);(uint256 bx,uint256 by)=migration.claimablePrincipal(b);
        assertEq(x+bx,migration.remainingETH());assertEq(y+by,migration.remainingZZZ());
        migration.distributePrincipal(_ids(a,b));assertEq(migration.remainingETH(),0);assertEq(migration.remainingZZZ(),0);
    }
}

/// @dev Model only for maximum-supply enumeration and multiple historical bucket
/// bookkeeping. Real Vault economic composition is tested above.
contract ExitScaleNFT {
    uint256 public constant mintedCount=1000;
    mapping(uint256=>address) public owners;
    constructor(address owner){for(uint256 i=1;i<=1000;++i)owners[i]=owner;}
    function tokenAtOrdinal(uint256 ordinal) external pure returns(uint256){require(ordinal>=1&&ordinal<=1000);return ordinal;}
    function ownerOf(uint256 id) external view returns(address){require(owners[id]!=address(0));return owners[id];}
    function transfer(uint256 id,address owner) external {owners[id]=owner;}
    function refreshMetadata(uint256 id) external view {require(owners[id]!=address(0));}
}
contract ExitScaleVault {
    MockAccess public immutable access;MockToken public immutable token;
    uint256 public constant MAX_BUCKETS=4;uint256 public constant bucketCount=4;
    mapping(uint256=>Position) private p;
    mapping(uint256=>uint256) public sharesOf;
    mapping(uint256=>uint256) public nftBucket;
    mapping(uint256=>uint256) public bucketTotalShares;
    constructor(MockAccess a,MockToken t,MockPools pools,bool zeroFourth){
        access=a;token=t;
        for(uint256 i=1;i<=4;++i){
            PoolConfig memory c;c.key=PoolKey(address(0),address(t),uint24(10020+i),60,address(0));
            bytes32 pool=keccak256(abi.encode(c.key));pools.set(pool,c);
            p[i].poolId=pool;p[i].status=PositionStatus.Parked;
            p[i].idle0=uint128(zeroFourth&&i==4?0:i*1000+777);p[i].idle1=uint128(zeroFourth&&i==4?0:i*2000+333);
        }
        // NFT1 stays dormant; the other999share four historical custody buckets.
        for(uint256 i=2;i<=1000;++i){uint256 bucket=(i-2)%4+1;uint256 shares=i%7+1;
            sharesOf[i]=shares;nftBucket[i]=bucket;bucketTotalShares[bucket]+=shares;}
    }
    receive() external payable {}
    function bucketAt(uint256 index) external pure returns(uint256){require(index<4);return index+1;}
    function group(uint256 id) external view returns(Position memory){return p[id];}
    function beginLPExit() external {require(msg.sender==access.module(Ids.MIGRATION));access.startLPExit();}
    function exitBucketToHolders(uint256 id,uint256 x,uint256 y,uint256) external returns(uint256 a,uint256 b){
        require(msg.sender==access.module(Ids.MIGRATION)&&access.lpExitStarted());Position storage pos=p[id];
        require(pos.status==PositionStatus.Parked);a=pos.idle0;b=pos.idle1;require(a>=x&&b>=y);
        pos.idle0=0;pos.idle1=0;pos.status=PositionStatus.Exited;
        ExactAsset.push(address(0),msg.sender,a);ExactAsset.push(address(token),msg.sender,b);
    }
    function corruptShares(uint256 id,uint256 shares) external {sharesOf[id]=shares;}
    function corruptCurrency(MockPools pools,uint256 id,address wrong) external {
        PoolConfig memory c=pools.accounting(p[id].poolId);c.key.currency1=wrong;pools.set(p[id].poolId,c);
    }
}
contract ExitScaleAssets {function isAsset(address) external pure returns(bool){return true;}}
contract HolderExitScaleTest is Test {
    MockAccess ac;MockToken token;MockPools pools;ExitScaleVault vault;ExitScaleNFT nft;ZZZMigration migration;
    bytes32 review=keccak256("scale model only");address owner=address(0xA11CE);
    function _setup(bool zeroFourth) private {
        vm.warp(1_000_000);ac=new MockAccess();token=new MockToken(18);pools=new MockPools();
        vault=new ExitScaleVault(ac,token,pools,zeroFourth);nft=new ExitScaleNFT(owner);migration=new ZZZMigration(address(ac));
        ac.bind(Ids.VAULT,address(vault));ac.bind(Ids.NFT,address(nft));ac.bind(Ids.POOLS,address(pools));
        ac.bind(Ids.MIGRATION,address(migration));ac.bind(Ids.REWARDS,address(new ExitScaleAssets()));
        address identity=address(new HolderExitIdentity(address(token)));pools.setActivationAssets(identity);ac.bind(Ids.BUYBACK,identity);
        migration.configureZZZ(address(token),address(token).codehash,review);ac.seal();ac.setPaused(true);
        uint256 x;uint256 y;for(uint256 i=1;i<=4;++i){Position memory p=vault.group(i);x+=p.idle0;y+=p.idle1;}
        vm.deal(address(vault),x);token.mint(address(vault),y);
    }
    function testAll1000OrdinalsFourBucketsAndZeroOutputConserveExactPrincipal() public {
        _setup(true);migration.beginCollectiveExit(review);
        migration.closeBucket(1,0,0,block.timestamp+100);nft.transfer(2,address(0xB0B));
        vm.expectRevert();migration.allocatePrincipal(32);
        for(uint256 i=2;i<=4;++i)migration.closeBucket(i,0,0,block.timestamp+100);
        uint256 totalETH=migration.remainingETH();uint256 totalZZZ=migration.remainingZZZ();
        while(uint256(migration.exitPhase())==uint256(ZZZMigration.ExitPhase.Allocating))migration.allocatePrincipal(32);
        uint256 allocatedETH;uint256 allocatedZZZ;
        for(uint256 i=1;i<=1000;++i){(uint256 x,uint256 y,bool allocated,)=migration.principalOf(i);
            assertTrue(allocated);allocatedETH+=x;allocatedZZZ+=y;}
        assertEq(allocatedETH,totalETH);assertEq(allocatedZZZ,totalZZZ);assertEq(migration.allocationCursor(),1001);
        uint256[] memory ids=new uint256[](1);ids[0]=2;uint256 before=address(0xB0B).balance;
        migration.distributePrincipal(ids);assertGt(address(0xB0B).balance,before);
        // Every real allocation is paid once; zero-output and dormant entries
        // need no transaction and cannot absorb unrelated prefunds.
        for(uint256 first=1;first<=1000;first+=32){uint256 end=first+32>1001?1001:first+32;
            ids=new uint256[](end-first);for(uint256 j=first;j<end;++j)ids[j-first]=j;migration.distributePrincipal(ids);}
        assertEq(migration.remainingETH(),0);assertEq(migration.remainingZZZ(),0);
    }
    function testAllBucketsValidatedBeforeIrreversibleStart() public {
        _setup(false);vault.corruptCurrency(pools,4,address(0xBAD));vm.expectRevert();migration.beginCollectiveExit(review);
        assertFalse(ac.lpExitStarted());assertEq(uint256(migration.exitPhase()),0);assertEq(migration.settlementBucketCount(),0);
    }
    function testMissingOrInconsistentShareInventoryFailsClosedBeforeAnyPayout() public {
        _setup(false);migration.beginCollectiveExit(review);for(uint256 i=1;i<=4;++i)migration.closeBucket(i,0,0,block.timestamp+100);
        vault.corruptShares(1000,vault.sharesOf(1000)-1);
        while(migration.allocationCursor()+32<=1000)migration.allocatePrincipal(32);
        vm.expectRevert();migration.allocatePrincipal(32);assertEq(uint256(migration.exitPhase()),uint256(ZZZMigration.ExitPhase.Allocating));
        vm.expectRevert();migration.claimablePrincipal(2);
    }
}
