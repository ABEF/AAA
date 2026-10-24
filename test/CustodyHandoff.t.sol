// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockToken,MockFeed,MockPools} from "./mocks/Mocks.sol";
import {ZZZMigration,ICustodyFinality} from "../src/ZZZMigration.sol";
import {ZZZCustodyValidation} from "../src/ZZZCustodyValidation.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {ZZZRewardReceiver} from "../src/ZZZRewardReceiver.sol";
import {Ids,Position,PositionStatus,PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
/// TEST ONLY: deterministic token math; not a real Uniswap/router/price/finality implementation.
contract HandoffVenue is ERC721 {
    MockPools pools; uint256 next=1; uint256 public loss; bool public failSwap;
    mapping(uint256=>uint256) public a0; mapping(uint256=>uint256) public a1;
    constructor(MockPools p) ERC721("Fixture","FIX") {pools=p;}
    function configure(uint256 l,bool f) external {loss=l;failSwap=f;}
    function positionManager() external view returns(address){return address(this);}
    function amounts(uint256 id) external view returns(uint256,uint256){return(a0[id],a1[id]);}
    function _fund(bytes32 pool,uint256 id,uint256 x,uint256 y) private {
        PoolConfig memory c=pools.accounting(pool);MockToken(c.key.currency0).transferFrom(msg.sender,address(this),x);
        MockToken(c.key.currency1).transferFrom(msg.sender,address(this),y);a0[id]+=x;a1[id]+=y;
    }
    function mint(bytes32 pool,int24,int24,uint256 x,uint256 y,uint128,uint256) external returns(uint256 id,uint256,uint256){
        id=next++;_mint(msg.sender,id);_fund(pool,id,x,y);return(id,x,y);
    }
    function increase(bytes32 pool,uint256 id,uint256 x,uint256 y,uint128,uint256) external returns(uint256,uint256){_fund(pool,id,x,y);return(x,y);}
    function collect(bytes32,uint256,uint256) external {}
    function close(bytes32 pool,uint256 id,uint256) external {
        PoolConfig memory c=pools.accounting(pool);uint256 x=a0[id];uint256 y=a1[id];delete a0[id];delete a1[id];_burn(id);
        MockToken(c.key.currency0).transfer(msg.sender,x);MockToken(c.key.currency1).transfer(msg.sender,y);
    }
    function swap(bytes32 pool,bool direction,uint256 amount,uint256 minimum,uint256) external returns(uint256 out){
        require(!failSwap,"swap unavailable");PoolConfig memory c=pools.accounting(pool);
        address input=direction?c.key.currency0:c.key.currency1;address output=direction?c.key.currency1:c.key.currency0;
        MockToken(input).transferFrom(msg.sender,address(this),amount);out=amount*(10000-loss)/10000;require(out>=minimum,"minimum");
        MockToken(output).mint(msg.sender,out);
    }
}
contract CustodyProofFixture is ICustodyFinality {
    bytes32 public accepted;
    function accept(bytes32 value) external {accepted=value;}
    function verifyCustody(bytes32 digest,bytes calldata proof) external view returns(bool){return digest==accepted && keccak256(proof)==keccak256(hex"01");}
}
contract CustodyHandoffTest is PooledVaultFixture {
    ZZZMigration migration; HandoffVenue handoffVenue; bytes32 review=keccak256("reviewed fixture only");
    function setUp() public override {
        super.setUp();handoffVenue=new HandoffVenue(pools);ac.bind(Ids.LIQUIDITY,address(handoffVenue));
        migration=new ZZZMigration(address(ac));ac.bind(Ids.MIGRATION,address(migration));
        migration.configureZZZ(address(t1),address(t1).codehash,review);
    }
    function _r(bool raw) private view returns(ZZZMigration.Request memory r) {
        r.bucket=_bucket();r.sourceSnapshot=migration.sourceSnapshot(r.bucket);r.recipient=bob;r.recipientCodeHash=bob.codehash;
        r.destinationChain=block.chainid;r.destinationCustody=address(vault);r.destinationPool=poolId;
        r.output0=address(t0);r.output1=address(t1);r.minimum0=970;r.minimum1=970;
        r.minimumZZZ=1940;r.rawExit=raw;r.exitMinimum0=1000;r.exitMinimum1=1000;
        r.deadline=block.timestamp+100;r.reviewHash=review;
    }
    function _send(bool raw) private returns(bytes32 id) {
        id=migration.approve(_r(raw));ac.setPaused(true);migration.exit(id);
    }
    function _return(bytes32 id,uint256 x,uint256 y) private {
        t0.mint(address(this),x);t1.mint(address(this),y);t0.approve(address(migration),x);t1.approve(address(migration),y);
        migration.completeLocal(id,x,y,1,block.timestamp+100);
    }
    function testExitAlwaysSendsOnlyZZZAndPreservesDonationsSharesAndRoyalties() public {
        uint256 nftId=activatedPosition();uint256 shares=vault.sharesOf(nftId);
        t0.mint(address(vault),777);t1.mint(address(migration),555);
        uint256 beforeBalance=t1.balanceOf(bob);bytes32 id=_send(false);
        assertEq(t1.balanceOf(bob)-beforeBalance,2000);assertEq(t0.balanceOf(address(vault)),777);
        assertEq(t1.balanceOf(address(migration)),555);assertEq(vault.sharesOf(nftId),shares);
        assertEq(uint256(vault.group(_bucket()).status),uint256(PositionStatus.Outbound));
        assertEq(t0.allowance(address(vault),address(handoffVenue)),0);assertEq(migration.activePlan(_bucket()),id);
        (bool available,)=nft.currentLPValue(nftId);assertFalse(available);assertEq(nft.royaltyRewards().weightOf(nftId),1);
    }
    function testCompleteRequiresActualLPAndPreservesNFTAndLedgers() public {
        uint256 nftId=activatedPosition();uint256 shares=vault.sharesOf(nftId);bytes32 id=_send(false);ac.setPaused(false);
        _return(id,1000,1000);Position memory p=vault.group(_bucket());assertEq(uint256(p.status),uint256(PositionStatus.Active));
        assertEq(handoffVenue.ownerOf(p.lpTokenId),address(vault));assertEq(vault.sharesOf(nftId),shares);
        assertEq(migration.activePlan(_bucket()),bytes32(0));assertEq(migration.outstandingCount(),0);
        assertEq(t0.allowance(address(migration),address(vault)),0);assertEq(t1.allowance(address(migration),address(vault)),0);
        assertEq(vault.migrationBudget().compositionEpoch(_bucket()),1);
    }
    function testSwapFailureRevertsWholeExitWithoutAutomaticRawFallback() public {
        activatedPosition();bytes32 id=migration.approve(_r(false));uint256 lp=vault.group(_bucket()).lpTokenId;
        handoffVenue.configure(0,true);ac.setPaused(true);vm.expectRevert();migration.exit(id);
        assertEq(handoffVenue.ownerOf(lp),address(vault));assertEq(migration.custodyEpoch(_bucket()),0);
        (ZZZMigration.Status status,,,,)=migration.state(id);assertEq(uint256(status),uint256(ZZZMigration.Status.Approved));
    }
    function testEmergencyRawExitWorksWithFailedSwapAndStalePrices() public {
        activatedPosition();vm.warp(block.timestamp+4000);handoffVenue.configure(9000,true);
        bytes32 id=_send(true);assertGt(t0.balanceOf(bob),0);assertGt(t1.balanceOf(bob),0);
        (,,,uint256 usd,)=migration.state(id);assertEq(usd,0);
    }
    function testRawExitMinimumProtectsCloseAndRollsBack() public {
        activatedPosition();ZZZMigration.Request memory r=_r(true);r.exitMinimum0=1001;bytes32 id=migration.approve(r);
        uint256 lp=vault.group(_bucket()).lpTokenId;ac.setPaused(true);vm.expectRevert();migration.exit(id);assertEq(handoffVenue.ownerOf(lp),address(vault));
    }
    function testEmergencyCanMoveToCustodyBeforeChoosingAnyNewPoolWithStoppedSourceAndStaleFeed() public {
        activatedPosition();PoolConfig memory c=pools.get(poolId);c.operationsEnabled=false;c.depositsEnabled=false;pools.set(poolId,c);
        vm.warp(block.timestamp+4000);handoffVenue.configure(9999,true);ZZZMigration.Request memory r=_r(true);
        r.destinationPool=bytes32(0);r.destinationCustody=bob;r.minimum0=0;r.minimum1=0;
        bytes32 id=migration.approve(r);ac.setPaused(true);migration.exit(id);
        (ZZZMigration.Status status,uint256 sent0,uint256 sent1,,)=migration.state(id);
        assertEq(uint256(status),uint256(ZZZMigration.Status.Sent));assertEq(sent0,1000);assertEq(sent1,1000);
    }
    function testHoldingCanBindNewDestinationExactlyOnceWithoutChangingSourceBudget() public {
        activatedPosition();ZZZMigration.Request memory r=_r(false);r.destinationPool=bytes32(0);r.destinationCustody=bob;r.minimum0=0;r.minimum1=0;
        bytes32 id=migration.approve(r);ac.setPaused(true);migration.exit(id);
        vm.prank(alice);vm.expectRevert();migration.bindLocalDestination(id,poolId,1,1,review);
        migration.bindLocalDestination(id,poolId,1,1,review);
        vm.expectRevert();migration.bindLocalDestination(id,poolId,1,1,review);
        ac.setPaused(false);t0.mint(address(this),970);t1.mint(address(this),969);t0.approve(address(migration),970);t1.approve(address(migration),969);
        vm.expectRevert();migration.completeLocal(id,970,969,1,block.timestamp+100);
        _return(id,1000,1000);assertEq(migration.outstandingCount(),0);
    }
    function testValidationCompanionCannotBeCalledByUnprivilegedAccounts() public {
        activatedPosition();bytes memory encoded=abi.encode(_r(false));ZZZCustodyValidation validator=migration.validation();
        vm.expectRevert();validator.validateRequest(encoded);
        vm.expectRevert();validator.validateDestination(encoded);
        vm.expectRevert();validator.validateParking(encoded);
    }
    function testApprovalRejectsInvalidSnapshotAndCompanionAsRecipient() public {
        activatedPosition();ZZZMigration.Request memory r=_r(false);r.sourceSnapshot=bytes32(uint256(1));
        vm.expectRevert();migration.approve(r);
        r=_r(false);r.recipient=address(migration.validation());r.recipientCodeHash=r.recipient.codehash;
        vm.expectRevert();migration.approve(r);
    }
    function testDestinationValidationRejectsUnreservedPoolAndWrongCustody() public {
        activatedPosition();ZZZMigration.Request memory r=_r(false);r.destinationCustody=bob;
        vm.expectRevert();migration.approve(r);
        PoolConfig memory c=pools.get(poolId);c.key.fee=500;bytes32 target=keccak256(abi.encode(c.key));pools.set(target,c);
        r=_r(false);r.destinationPool=target;vm.expectRevert();migration.approve(r);
        vault.reservePool(target,_bucket());bytes32 id=migration.approve(r);assertEq(migration.activePlan(_bucket()),id);
    }
    function testNormalModeRejectsAnUnpricedOrUnswappableExit() public {
        activatedPosition();vm.warp(block.timestamp+4000);ZZZMigration.Request memory r=_r(false);
        vm.expectRevert();migration.approve(r);
    }
    function testThreePercentBudgetCannotBeRelaxedByRequest() public {
        activatedPosition();ZZZMigration.Request memory r=_r(false);r.minimumZZZ=1939;
        vm.expectRevert();migration.approve(r);
    }
    function testLocalEndToEndBudgetIncludesExitAndRedeployment() public {
        activatedPosition();handoffVenue.configure(100,false);ZZZMigration.Request memory r=_r(false);
        r.minimum0=1;r.minimum1=1;bytes32 id=migration.approve(r);ac.setPaused(true);migration.exit(id);ac.setPaused(false);
        t0.mint(address(this),970);t1.mint(address(this),969);t0.approve(address(migration),970);t1.approve(address(migration),969);
        vm.expectRevert();migration.completeLocal(id,970,969,1,block.timestamp+100); // raw minima pass; original USD budget fails.
        _return(id,970,970);
    }
    function testOneToTenReplacementWithDifferentDecimalsPreservesSharesAndValue() public {
        uint256 nftId=activatedPosition();MockToken nextZZZ=new MockToken(6);MockFeed feed=new MockFeed(8,1e7);
        oracle.setTestFeed(address(nextZZZ),address(feed),3600);rewards.addAsset(address(nextZZZ));
        PoolConfig memory c=pools.get(poolId);c.key.currency1=address(nextZZZ);bytes32 target=keccak256(abi.encode(c.key));pools.set(target,c);vault.reservePool(target,_bucket());
        ZZZMigration.Request memory r=_r(false);r.destinationPool=target;r.output1=address(nextZZZ);r.minimum1=9700e6;
        bytes32 id=migration.approve(r);ac.setPaused(true);migration.exit(id);ac.setPaused(false);
        t0.mint(address(this),1000);nextZZZ.mint(address(this),10000e6);t0.approve(address(migration),1000);nextZZZ.approve(address(migration),10000e6);
        migration.completeLocal(id,1000,10000e6,1,block.timestamp+100);
        assertEq(vault.sharesOf(nftId),2000e18);(bool available,uint256 value)=nft.currentLPValue(nftId);assertTrue(available);assertEq(value,2000e18);
        migration.configureZZZ(address(nextZZZ),address(nextZZZ).codehash,review);assertEq(migration.currentZZZ(),address(nextZZZ));
    }
    function testFuzzExitSwapLossLimit(uint16 loss) public {
        loss=uint16(bound(loss,0,10000));activatedPosition();bytes32 id=migration.approve(_r(false));
        handoffVenue.configure(loss,false);ac.setPaused(true);
        // This fixture's per-leg limit is 1%, stricter than the overall 3%.
        if(loss>100){vm.expectRevert();migration.exit(id);}else migration.exit(id);
    }
    function testLateCreatorRewardsAndUnclaimedRightsFollowNFTDuringCustody() public {
        uint256 nftId=activatedPosition();address inbox=fees.createRewardReceiver(_bucket(),address(0));_send(false);
        t1.mint(inbox,100);ZZZRewardReceiver(payable(inbox)).sync();assertEq(rewards.claimable(nftId,address(t1)),90);
        vm.prank(alice);nft.transferFrom(alice,bob,nftId);vm.prank(bob);assertEq(rewards.claim(nftId,address(t1)),90);
        assertEq(fees.compoundBalance(_bucket(),address(t1)),5);assertEq(fees.buybackBalance(address(t1)),5);
    }
    function testRecoveredCustodyNeedsFullActualSentZZZAndCanRemainPaused() public {
        uint256 nftId=activatedPosition();bytes32 id=_send(false);
        vm.prank(bob);t1.approve(address(migration),2000);vm.prank(bob);migration.recover(id,block.timestamp+100,"");
        Position memory p=vault.group(_bucket());assertEq(uint256(p.status),uint256(PositionStatus.Parked));assertEq(p.idle0,0);assertEq(p.idle1,2000);
        assertEq(vault.totalIdle(address(t1)),2000);assertEq(vault.sharesOf(nftId),2000e18);
    }
    function testNoTimeoutCancellationAfterSending() public {
        activatedPosition();bytes32 id=_send(false);vm.warp(block.timestamp+100 days);
        vm.expectRevert();migration.cancel(id);assertEq(migration.activePlan(_bucket()),id);
    }
    function testApprovalCanBeCancelledWithoutMovingFunds() public {
        activatedPosition();bytes32 id=migration.approve(_r(false));migration.cancel(id);
        assertEq(migration.outstandingCount(),0);assertEq(uint256(vault.group(_bucket()).status),uint256(PositionStatus.Active));
    }
    function testStateDriftAndDuplicateApprovalsFailClosed() public {
        activatedPosition();ZZZMigration.Request memory r=_r(false);bytes32 id=migration.approve(r);
        vm.expectRevert();migration.approve(r);handoffVenue.configure(0,false);
        uint256 next=_mint(bob);vm.prank(bob);vm.expectRevert();vault.activate(next,poolId,100,100,1,block.timestamp+100);
        vm.warp(block.timestamp+101);
        ac.setPaused(true);vm.expectRevert();migration.exit(id);
    }
    function testUnauthorizedExitAndConfigurationAreRejected() public {
        activatedPosition();ZZZMigration.Request memory r=_r(false);vm.prank(alice);vm.expectRevert();migration.approve(r);
        vm.prank(alice);vm.expectRevert();migration.configureZZZ(address(t0),address(t0).codehash,review);
    }
    function testRemoteCannotBeApprovedWithoutVerifier() public {
        activatedPosition();ZZZMigration.Request memory r=_r(false);r.destinationChain=block.chainid+1;
        vm.expectRevert();migration.approve(r);
    }
    function testRemoteProofCannotBeReplacedByGovernanceAndRecoveryRequiresClosure() public {
        activatedPosition();CustodyProofFixture verifier=new CustodyProofFixture();ZZZMigration.Request memory r=_r(false);
        r.destinationChain=block.chainid+1;r.destinationCustody=address(0x1234);r.verifier=address(verifier);r.verifierCodeHash=address(verifier).codehash;
        bytes32 id=migration.approve(r);ac.setPaused(true);migration.exit(id);
        vm.expectRevert();migration.verifyRemote(id,hex"01");verifier.accept(migration.proofCommitment(id,1));migration.verifyRemote(id,hex"01");
        vm.prank(bob);t1.approve(address(migration),2000);vm.prank(bob);vm.expectRevert();migration.recover(id,block.timestamp+100,hex"01");
        verifier.accept(migration.proofCommitment(id,2));vm.prank(bob);migration.recover(id,block.timestamp+100,hex"01");
        assertEq(migration.outstandingCount(),0);
    }
    function testSentCustodyCannotChangeZZZOrAcceptInventedCompletion() public {
        activatedPosition();bytes32 id=_send(false);vm.expectRevert();migration.configureZZZ(address(t0),address(t0).codehash,review);
        ac.setPaused(false);vm.expectRevert();migration.completeLocal(id,1000,1000,1,block.timestamp+100);
    }
}
