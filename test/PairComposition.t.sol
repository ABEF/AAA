// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZPairMigration} from "../src/ZZZPairMigration.sol";
import {ZZZRewardReceiver} from "../src/ZZZRewardReceiver.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {Ids,PoolConfig,Position} from "../src/libraries/ZZZTypes.sol";
import {MockToken,MockPools,MockFeed,MockAccess} from "./mocks/Mocks.sol";

/// TEST ONLY: deterministic token quantities, not real Uniswap execution/prices.
contract PairVenue is ERC721 {
    MockPools public pools;
    uint256 public next = 1;
    uint256 public closeLoss; uint256 public swapLoss; uint256 public spendBps = 10000;
    uint256 public fee0; uint256 public fee1;
    bool public fail;
    MockFeed public callbackFeed;
    mapping(uint256=>bytes32) public poolOf;
    mapping(uint256=>uint256) public a0; mapping(uint256=>uint256) public a1;
    constructor(MockPools p) ERC721("Pair fixture","PF") { pools=p; }
    function positionManager() external view returns(address) { return address(this); }
    function configure(uint256 c,uint256 s,uint256 b,bool f) external { closeLoss=c;swapLoss=s;spendBps=b;fail=f; }
    function setFees(uint256 x,uint256 y) external { fee0=x;fee1=y; }
    function reprice(MockFeed f) external { callbackFeed=f; }
    function amounts(uint256 id) external view returns(uint256,uint256) { return(a0[id],a1[id]); }
    function _tokens(bytes32 pool) private view returns(MockToken,MockToken) {
        PoolConfig memory c=pools.accounting(pool); return(MockToken(c.key.currency0),MockToken(c.key.currency1));
    }
    function _fund(bytes32 pool,uint256 id,uint256 x,uint256 y) private returns(uint256 s0,uint256 s1) {
        require(!fail,"fixture failure"); (MockToken t0,MockToken t1)=_tokens(pool);
        s0=x*spendBps/10000;s1=y*spendBps/10000;
        t0.transferFrom(msg.sender,address(this),s0);t1.transferFrom(msg.sender,address(this),s1);
        a0[id]+=s0;a1[id]+=s1;
    }
    function mint(bytes32 pool,int24,int24,uint256 x,uint256 y,uint128,uint256) external returns(uint256 id,uint256 s0,uint256 s1) {
        id=next++;poolOf[id]=pool;_mint(msg.sender,id);(s0,s1)=_fund(pool,id,x,y);
    }
    function increase(bytes32 pool,uint256 id,uint256 x,uint256 y,uint128,uint256) external returns(uint256,uint256) {
        require(poolOf[id]==pool);return _fund(pool,id,x,y);
    }
    function collect(bytes32 pool,uint256,uint256) external {
        (MockToken t0,MockToken t1)=_tokens(pool);t0.mint(msg.sender,fee0);t1.mint(msg.sender,fee1);fee0=0;fee1=0;
    }
    function close(bytes32 pool,uint256 id,uint256) external {
        require(poolOf[id]==pool);(MockToken t0,MockToken t1)=_tokens(pool);
        uint256 x=a0[id]*(10000-closeLoss)/10000;uint256 y=a1[id]*(10000-closeLoss)/10000;
        delete a0[id];delete a1[id];_burn(id);t0.transfer(msg.sender,x);t1.transfer(msg.sender,y);
    }
    function swap(bytes32 pool,bool direction,uint256 amount,uint256 minimum,uint256) external returns(uint256 out) {
        (MockToken t0,MockToken t1)=_tokens(pool);(MockToken input,MockToken output)=direction?(t0,t1):(t1,t0);
        input.transferFrom(msg.sender,address(this),amount);out=amount*(10000-swapLoss)/10000;require(out>=minimum);
        output.mint(msg.sender,out);
        if(address(callbackFeed)!=address(0))callbackFeed.set(100e8,block.timestamp,block.timestamp);
    }
}

contract PairCompositionTest is PooledVaultFixture {
    PairVenue pairVenue; MockToken t2; MockFeed feed2;
    ZZZMigration migration; ZZZPairMigration composer;
    bytes32 target; bytes32 route;
    function setUp() public override {
        super.setUp();
        pairVenue=new PairVenue(pools);ac.bind(Ids.LIQUIDITY,address(pairVenue));
        migration=new ZZZMigration(address(ac));ac.bind(Ids.MIGRATION,address(migration));composer=migration.pairMigration();
        t2=new MockToken(0);feed2=new MockFeed(8,1e8);oracle.setFeed(address(t2),address(feed2),3600);rewards.addAsset(address(t2));
        PoolConfig memory c=pools.get(poolId);c.key.currency1=address(t2);target=keccak256(abi.encode(c.key));pools.set(target,c);
        c.key.currency0=address(t1);route=keccak256(abi.encode(c.key));pools.set(route,c);
    }
    function _request(uint256 amount,uint256 minimum) private view returns(ZZZPairMigration.Request memory r) {
        uint256 b=_bucket();Position memory p=vault.group(b);
        r.bucket=b;r.sourcePool=p.poolId;r.sourceLP=p.lpTokenId;r.totalShares=vault.bucketTotalShares(b);
        r.epoch=vault.migrationBudget().compositionEpoch(b);r.destinationPool=target;r.minimumLiquidity=1;
        r.deadline=block.timestamp+100;r.reviewHash=keccak256("reviewed test plan");r.steps=new ZZZPairMigration.Step[](1);
        r.steps[0]=ZZZPairMigration.Step(route,true,uint128(amount),uint128(minimum));
    }
    function _assertUnchanged(uint256 id,uint256 lp,uint256 shares) private view {
        assertEq(vault.group(_bucket()).poolId,poolId);assertEq(vault.group(_bucket()).lpTokenId,lp);
        assertEq(vault.sharesOf(id),shares);assertEq(pairVenue.ownerOf(lp),address(vault));
        assertEq(vault.migrationBudget().compositionEpoch(_bucket()),0);assertEq(composer.activeBucket(),0);
        assertEq(vault.poolBucket(target),0);assertEq(vault.migrationBudget().pairExecutor(),address(0));
    }
    function testMovePreservesSharesOldRewardsInboxAndDonationIsolation() public {
        uint256 id=activatedPosition();uint256 b=_bucket();uint256 shares=vault.sharesOf(id);
        address inbox=fees.createRewardReceiver(b,address(0));
        pairVenue.setFees(100,100);t0.mint(address(vault),777);t1.mint(address(composer),888);
        composer.execute(_request(1005,1005));Position memory p=vault.group(b);
        assertEq(p.poolId,target);assertEq(p.homeToken0,address(t0));assertEq(p.homeToken1,address(t1));
        assertEq(p.idle0,0);assertEq(p.idle1,0);assertEq(vault.sharesOf(id),shares);assertEq(vault.bucketTotalShares(b),shares);
        assertEq(pairVenue.a0(p.lpTokenId),1005);assertEq(pairVenue.a1(p.lpTokenId),1005);
        assertEq(t0.balanceOf(address(vault)),777);assertEq(t1.balanceOf(address(composer)),888);
        assertEq(rewards.claimable(id,address(t0)),90);assertEq(rewards.claimable(id,address(t1)),90);
        assertEq(fees.rewardReceiver(b),inbox);assertEq(fees.buybackBalance(address(t1)),5);
        assertEq(vault.migrationBudget().compositionEpoch(b),1);assertEq(vault.totalIdle(address(t1)),0);
        assertEq(t1.allowance(address(composer),address(pairVenue)),0);
        t1.mint(inbox,100);ZZZRewardReceiver(payable(inbox)).sync();
        assertEq(rewards.claimable(id,address(t1)),180);assertEq(fees.compoundBalance(b,address(t1)),5);
        assertEq(vault.migrationBudget().historicalCompoundValue(b),5e18);
        vm.prank(alice);nft.transferFrom(alice,bob,id);vm.prank(bob);assertEq(rewards.claim(id,address(t1)),180);
    }
    function testLateCompoundCannotDiluteIncumbentsOrBecomeNewContribution() public {
        uint256 id=activatedPosition();uint256 b=_bucket();address inbox=fees.createRewardReceiver(b,address(0));
        composer.execute(_request(1000,1000));
        t1.mint(inbox,100);ZZZRewardReceiver(payable(inbox)).sync();
        uint256 newcomer=_mint(bob);t2.mint(bob,100);vm.prank(bob);t2.approve(address(vault),100);
        vm.prank(bob);vault.activate(newcomer,target,100,100,1,block.timestamp+100);
        assertEq(vault.sharesOf(newcomer),uint256(2000e18)*200/2005);
        assertEq(rewards.claimable(newcomer,address(t1)),0);assertEq(rewards.claimable(id,address(t1)),90);
        assertEq(fees.compoundBalance(b,address(t1)),5);assertEq(vault.contributionUSD(newcomer),200e18);
        (bool available,uint256 value)=nft.currentLPValue(id);assertTrue(available);assertApproxEqAbs(value,2005e18,1);
    }
    function testThreePercentAggregateCapIncludesCloseAndConversion() public {
        activatedPosition();pairVenue.configure(100,400,10000,false);
        composer.execute(_request(990,950));
        Position memory p=vault.group(_bucket());assertEq(pairVenue.a0(p.lpTokenId)+pairVenue.a1(p.lpTokenId),1940);
    }
    function testOneUnitBeyondAggregateCapRollsBackAllCustodyAndApprovals() public {
        uint256 id=activatedPosition();uint256 lp=vault.group(_bucket()).lpTokenId;uint256 shares=vault.sharesOf(id);
        pairVenue.configure(100,410,10000,false);t2.mint(address(composer),999999);
        ZZZPairMigration.Request memory r=_request(990,949);
        vm.expectRevert();composer.execute(r);_assertUnchanged(id,lp,shares);
        assertEq(t2.balanceOf(address(composer)),999999);assertEq(t1.allowance(address(composer),address(pairVenue)),0);
    }
    function testFreshOracleRepricingCannotHideConversionLoss() public {
        uint256 id=activatedPosition();uint256 lp=vault.group(_bucket()).lpTokenId;
        pairVenue.configure(0,1000,10000,false);pairVenue.reprice(feed2);
        ZZZPairMigration.Request memory r=_request(1000,900);
        vm.expectRevert();composer.execute(r);_assertUnchanged(id,lp,vault.sharesOf(id));
        assertEq(oracle.price(address(t2)),1e18);
    }
    function testIncompleteConversionAndVenueFailureRevert() public {
        uint256 id=activatedPosition();uint256 lp=vault.group(_bucket()).lpTokenId;
        ZZZPairMigration.Request memory r=_request(999,999);
        vm.expectRevert();composer.execute(r);_assertUnchanged(id,lp,vault.sharesOf(id));
        pairVenue.configure(0,0,10000,true);r=_request(1000,1000);vm.expectRevert();composer.execute(r);
        _assertUnchanged(id,lp,vault.sharesOf(id));
    }
    function testReviewIdentityEpochDeadlineRolesAndOrdinaryPairGuard() public {
        uint256 id=activatedPosition();ZZZPairMigration.Request memory r=_request(1000,1000);
        vm.prank(alice);vm.expectRevert();composer.execute(r);
        r.sourceLP++;vm.expectRevert();composer.execute(r);r.sourceLP--;
        r.totalShares++;vm.expectRevert();composer.execute(r);r.totalShares--;
        r.epoch++;vm.expectRevert();composer.execute(r);r.epoch--;
        r.deadline=block.timestamp+601;vm.expectRevert();composer.execute(r);r.deadline=block.timestamp+100;
        vm.expectRevert();migration.movePool(_bucket(),target,1,block.timestamp+100);
        vm.expectRevert();composer.convert(_bucket(),1000,1000);
        vm.expectRevert();fees.releaseCompound(_bucket(),address(t1));
        _assertUnchanged(id,r.sourceLP,r.totalShares);
        composer.execute(r);vm.expectRevert();composer.execute(r);
        vm.expectRevert();migration.propose(_bucket(),bytes32(uint256(123)));
    }
    function testSecondMoveIncludesHistoricalCompoundingAndRetainsBothRewardCurrencies() public {
        uint256 id=activatedPosition();address inbox=fees.createRewardReceiver(_bucket(),address(0));
        composer.execute(_request(1000,1000));t1.mint(inbox,100);ZZZRewardReceiver(payable(inbox)).sync();
        ZZZPairMigration.Request memory r=_request(1000,1000);r.destinationPool=poolId;r.steps[0].zeroForOne=false;
        composer.execute(r);Position memory p=vault.group(_bucket());
        assertEq(p.poolId,poolId);assertEq(pairVenue.a0(p.lpTokenId),1000);assertEq(pairVenue.a1(p.lpTokenId),1005);
        assertEq(fees.compoundBalance(_bucket(),address(t1)),0);assertEq(rewards.claimable(id,address(t1)),90);
        assertEq(vault.migrationBudget().compositionEpoch(_bucket()),2);
    }
    function testConsolidateOldCompoundWithoutChangingCurrentPool() public {
        activatedPosition();address inbox=fees.createRewardReceiver(_bucket(),address(0));
        composer.execute(_request(1000,1000));t1.mint(inbox,100);ZZZRewardReceiver(payable(inbox)).sync();
        ZZZPairMigration.Request memory r=_request(5,5);composer.execute(r);
        Position memory p=vault.group(_bucket());assertEq(p.poolId,target);
        assertEq(pairVenue.a0(p.lpTokenId),1000);assertEq(pairVenue.a1(p.lpTokenId),1005);
        assertEq(fees.compoundBalance(_bucket(),address(t1)),0);assertEq(vault.migrationBudget().compositionEpoch(_bucket()),2);
    }
    function testFuzzLossBudgetUsesWholeMove(uint16 rawClose,uint16 rawSwap) public {
        uint256 id=activatedPosition();uint256 lp=vault.group(_bucket()).lpTokenId;
        uint256 closeBps=bound(rawClose,0,300);uint256 swapBps=bound(rawSwap,0,600);
        pairVenue.configure(closeBps,swapBps,10000,false);
        uint256 input=1000*(10000-closeBps)/10000;uint256 output=input*(10000-swapBps)/10000;
        ZZZPairMigration.Request memory r=_request(input,output);
        if(input+output<1940){vm.expectRevert();composer.execute(r);_assertUnchanged(id,lp,vault.sharesOf(id));}
        else {composer.execute(r);assertEq(vault.group(_bucket()).poolId,target);}
    }
    function testComposedParkedRecordsCarryEpochAndCorrectCurrencyBacking() public {
        uint256 id=activatedPosition();composer.execute(_request(1000,1000));uint256 b=_bucket();
        ac.setPaused(true);vm.prank(address(migration));vault.park(b,block.timestamp+100);
        ac.setCanonicalState(1);
        ZZZVaultCanonical source=vault.canonicalModule();
        vm.prank(ac.canonicalHandoff());source.canonicalCapture();
        MockAccess nextAccess=new MockAccess();ZZZVault nextVault=new ZZZVault(address(nextAccess),block.chainid,treasury);
        nextAccess.bind(Ids.VAULT,address(nextVault));nextAccess.bind(Ids.POOLS,address(pools));
        nextAccess.bind(Ids.REWARDS,address(rewards));nextAccess.bind(Ids.RECEIVER,address(0x7788));
        nextAccess.bind(Ids.CANONICAL,address(this));
        ZZZVaultCanonical dest=new ZZZVaultCanonical(address(nextAccess),address(nextVault),block.chainid);
        nextAccess.bind(Ids.VAULT_CANONICAL,address(dest));nextAccess.setCanonicalState(2);
        for(uint256 i;i<source.canonicalCount();++i)dest.canonicalImport(i,source.canonicalExport(i));
        assertEq(nextVault.migrationBudget().compositionEpoch(b),1);
        assertEq(nextVault.totalIdle(address(t0)),1000);assertEq(nextVault.totalIdle(address(t1)),0);
        assertEq(nextVault.totalIdle(address(t2)),1000);assertEq(nextVault.group(b).homeToken1,address(t1));
        assertEq(nextVault.sharesOf(id),vault.sharesOf(id));assertEq(nextVault.bucketTotalShares(b),vault.bucketTotalShares(b));
        t0.mint(address(nextVault),1000);t2.mint(address(nextVault),1000);dest.canonicalValidate();
        ZZZMigrationBudget nextBudget=nextVault.migrationBudget();
        vm.expectRevert();nextBudget.importComposition(b,0);
    }
    function testUnselectedHistoricalReserveAndFailedFeedDoNotTrapCurrentLP() public {
        uint256 id=activatedPosition();address inbox=fees.createRewardReceiver(_bucket(),address(0));
        composer.execute(_request(1000,1000));t1.mint(inbox,100);ZZZRewardReceiver(payable(inbox)).sync();
        MockFeed failed=new MockFeed(8,0);oracle.setFeed(address(t1),address(failed),3600);
        ZZZPairMigration.Request memory r=_request(0,0);r.steps=new ZZZPairMigration.Step[](0);
        composer.execute(r);
        assertEq(fees.compoundBalance(_bucket(),address(t1)),5);assertEq(rewards.claimable(id,address(t1)),90);
        Position memory p=vault.group(_bucket());assertEq(pairVenue.a0(p.lpTokenId)+pairVenue.a1(p.lpTokenId),2000);
        assertEq(vault.sharesOf(id),2000e18);assertEq(vault.migrationBudget().compositionEpoch(_bucket()),2);
    }
    function testHistoricalVenueDustCannotLeakToNewMembership() public {
        uint256 id=activatedPosition();composer.execute(_request(1000,1000));
        pairVenue.setFees(0,19);vault.collectFees(_bucket(),block.timestamp+100);
        assertEq(fees.dust(_bucket(),address(t2)),19);
        ZZZPairMigration.Request memory r=_request(1000,1000);r.destinationPool=poolId;r.steps[0].zeroForOne=false;
        composer.execute(r);uint256 newcomer=_mint(bob);_activate(bob,newcomer,100,100);
        assertEq(rewards.claimable(id,address(t2)),19);assertEq(rewards.claimable(newcomer,address(t2)),0);
        assertEq(fees.dust(_bucket(),address(t2)),0);
    }
    function testPausedMoveFailsAndParkedResumeRetainsAtomicBudget() public {
        activatedPosition();ac.setPaused(true);uint256 b=_bucket();
        vm.prank(address(migration));vault.park(b,block.timestamp+100);
        ZZZPairMigration.Request memory r=_request(1000,1000);
        vm.expectRevert();composer.execute(r);
        ac.setPaused(false);composer.execute(r);assertEq(vault.group(b).poolId,target);
        assertEq(vault.migrationBudget().compositionEpoch(b),1);
    }
}
