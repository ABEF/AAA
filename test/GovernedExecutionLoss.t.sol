// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {HandoffVenue} from "./CustodyHandoff.t.sol";
import {BudgetAdversarialVenue} from "./MigrationBudgetAdversarial.t.sol";
import {RebalanceBudgetPolicy} from "./RebalanceBudget.t.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Real Vault, policy, custody and reward ledgers; deterministic venue,
/// price and authority fixtures. Not a qualification of actual market execution.
contract GovernedExecutionLossTest is PooledVaultFixture {
    bytes32 private constant REVIEW=keccak256("governed loss policy local fixture");
    ZZZMigrationBudget private budget;
    event ContributionLossLimitChanged(uint16 previous,uint16 current);
    event MaintenanceLossLimitChanged(uint16 previous,uint16 current);

    function setUp() public override {super.setUp();budget=vault.migrationBudget();}
    function _budget() private view returns(ZZZMigrationBudget){return budget;}
    function _venueLimit(uint16 limit) private {
        PoolConfig memory c=pools.get(poolId);c.maxSlippageBps=limit;pools.set(poolId,c);
    }
    function _target() private returns(bytes32 target){
        PoolConfig memory c=pools.get(poolId);c.key.fee=500;target=keccak256(abi.encode(c.key));pools.set(target,c);
    }
    function _migration() private returns(ZZZMigration m){m=new ZZZMigration(address(ac));ac.bind(Ids.MIGRATION,address(m));}
    function _rebalance() private {vault.rebalance(_bucket(),1,block.timestamp+100);}
    function _capture(uint256 id) private returns(uint32 limits){
        ZZZMigrationBudget b=_budget();uint256 bucket=_bucket();
        vm.prank(address(vault));(,,limits)=b.validateContribution(id,bucket,1000e18,1000,1,false);
    }
    function _math(uint256 input,uint256 deployed,uint32 limits) private view returns(uint256 issued,uint256 net){
        return _budget().contributionResult(_bucket(),input,0,0,0,deployed,0,limits);
    }
    function _custody() private returns(ZZZMigration m){
        ac.bind(Ids.LIQUIDITY,address(new HandoffVenue(pools)));m=_migration();
        m.configureZZZ(address(t1),address(t1).codehash,REVIEW);activatedPosition();
    }
    function _request(ZZZMigration m,bool raw,uint256 minimum) private view returns(ZZZMigration.Request memory r){
        r.bucket=_bucket();r.sourceSnapshot=m.sourceSnapshot(r.bucket);r.recipient=bob;r.recipientCodeHash=bob.codehash;
        r.destinationChain=block.chainid;r.destinationCustody=address(vault);r.destinationPool=poolId;
        r.output0=address(t0);r.output1=address(t1);r.minimum0=1;r.minimum1=1;r.minimumZZZ=minimum;
        r.rawExit=raw;r.exitMinimum0=1000;r.exitMinimum1=1000;r.deadline=block.timestamp+100;r.reviewHash=REVIEW;
    }
    function _return(ZZZMigration m,bytes32 id,uint256 x,uint256 y) private {
        t0.mint(address(this),x);t1.mint(address(this),y);t0.approve(address(m),x);t1.approve(address(m),y);
        m.completeLocal(id,x,y,1,block.timestamp+100);
    }

    function testDefaultsHardMaximumZeroAndGovernanceEvents() public {
        ZZZMigrationBudget b=_budget();assertEq(b.MAX_LOSS_BPS(),1000);
        assertEq(b.contributionLossBps(),100);assertEq(b.maintenanceLossBps(),300);
        vm.expectEmit(false,false,false,true,address(b));emit ContributionLossLimitChanged(100,1000);
        b.setLossLimits(1000,300);
        vm.expectEmit(false,false,false,true,address(b));emit ContributionLossLimitChanged(1000,1000);
        vm.expectEmit(false,false,false,true,address(b));emit MaintenanceLossLimitChanged(300,0);
        b.setLossLimits(1000,0);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);b.setLossLimits(1001,0);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);b.setLossLimits(1000,1001);
        b.setLossLimits(0,0);b.setLossLimits(0,1000);
        assertEq(b.contributionLossBps(),0);assertEq(b.maintenanceLossBps(),1000);
    }
    function testOnlyGovernanceAndOperatingLifecycleCanChangeLimits() public {
        ZZZMigrationBudget b=_budget();vm.prank(alice);vm.expectRevert(ZZZModule.Unauthorized.selector);b.setLossLimits(200,300);
        ZZZVaultCanonical companion=vault.canonicalModule();
        vm.expectRevert(ZZZModule.Unauthorized.selector);companion.validateOwner(1,alice,true,false);
        vm.expectRevert(ZZZModule.Unauthorized.selector);companion.validateContribution(1,1,100e18,100,1,true);
        ac.setKeeper(alice,true);vm.prank(alice);vm.expectRevert(ZZZModule.Unauthorized.selector);b.setLossLimits(100,500);
        ac.setPreparation(true);vm.expectRevert();b.setLossLimits(200,300);ac.setPreparation(false);
        for(uint8 state=1;state<5;++state){
            ac.setCanonicalState(state);vm.expectRevert(ZZZModule.CanonicalLocked.selector);b.setLossLimits(100,500);
        }
        ac.setCanonicalState(0);ac.setPaused(true);b.setLossLimits(100,500);b.setLossLimits(200,500);
        assertEq(b.maintenanceLossBps(),500);assertEq(b.contributionLossBps(),200);
    }
    function testActivationAndGrowthUseGovernedContributionLimitWithVenueFloorRetained() public {
        _venueLimit(1000);uint256 id=_mint(alice);venue.setSpendBps(9800);
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,1000,0);
        _budget().setLossLimits(200,300);_activate(alice,id,1000,0);
        assertEq(venue.a0(vault.group(_bucket()).lpTokenId),980);assertEq(vault.group(_bucket()).idle0,20);
        assertEq(vault.sharesOf(id),1000e18);
        // Stricter per-venue guard remains effective when global policy is looser.
        _venueLimit(100);uint32 limits=_capture(id);
        vm.expectRevert(ZZZModule.Slippage.selector);_math(1000e18,980e18,limits);
    }
    function testLaterContributionsUseSamePolicyWithoutBorrowingIncumbentIdle() public {
        uint256 id=activatedPosition();_venueLimit(1000);venue.setSpendBps(9800);
        vm.prank(alice);vm.expectRevert(ZZZModule.Slippage.selector);vault.increase(id,1000,0,1,block.timestamp+100);
        _budget().setLossLimits(200,300);vm.prank(alice);vault.increase(id,1000,0,1,block.timestamp+100);
        assertEq(vault.contributionUSD(id),3000e18);assertEq(vault.sharesOf(id),3000e18);
        assertEq(vault.group(_bucket()).idle0,20);
    }
    function testPackedContributionCapStaysFixedDespiteLaterGovernanceChange() public {
        uint256 id=activatedPosition();_venueLimit(1000);uint32 captured=_capture(id);
        assertEq(uint16(captured),1000);assertEq(uint16(captured>>16),100);
        _budget().setLossLimits(1000,300);
        vm.expectRevert(ZZZModule.Slippage.selector);_math(1000e18,980e18,captured);
        uint32 future=_capture(id);(uint256 issued,uint256 net)=_math(1000e18,980e18,future);
        assertEq(issued,980e18);assertEq(net,980e18);
    }
    function testRetainedValueRoundsUpAndCannotExceedHardMaximum() public {
        uint32 limits=uint32(1000)|(uint32(1000)<<16);
        (uint256 issued,)=_math(1001,901,limits);assertEq(issued,901);
        vm.expectRevert(ZZZModule.Slippage.selector);_math(1001,900,limits);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);_math(1001,1001,uint32(1000)|(uint32(1001)<<16));
        vm.expectRevert(ZZZModule.Slippage.selector);_math(1001,1000,uint32(1000));
    }
    function testRebalanceUsesCurrentBoundedPolicyAndPreservesShares() public {
        uint256 id=activatedPosition();venue.setCloseLossBps(1000);uint256 previous=vault.group(_bucket()).lpTokenId;
        vm.expectRevert(ZZZModule.Slippage.selector);_rebalance();assertEq(vault.group(_bucket()).lpTokenId,previous);
        _budget().setLossLimits(100,1000);_rebalance();assertEq(vault.sharesOf(id),2000e18);
        (bool available,uint256 value)=nft.currentLPValue(id);assertTrue(available);assertEq(value,1800e18);
    }
    function testAtomicMoveUsesSamePolicyAndPreservesStrongPoolChecks() public {
        uint256 id=activatedPosition();ZZZMigration m=_migration();bytes32 target=_target();venue.setCloseLossBps(1000);
        vm.expectRevert(ZZZModule.Slippage.selector);m.moveFunds(_bucket(),target,1,block.timestamp+100);
        assertEq(vault.group(_bucket()).poolId,poolId);_budget().setLossLimits(100,1000);
        m.moveFunds(_bucket(),target,1,block.timestamp+100);assertEq(vault.group(_bucket()).poolId,target);
        assertEq(vault.sharesOf(id),2000e18);assertEq(t0.allowance(address(vault),address(venue)),0);
    }
    function testGovernanceCallbackCannotWidenActiveMaintenanceSnapshot() public {
        BudgetAdversarialVenue adverse=new BudgetAdversarialVenue(address(t0),address(t1));
        ac.bind(Ids.LIQUIDITY,address(adverse));ac.bind(Ids.STRATEGY,address(new RebalanceBudgetPolicy()));activatedPosition();
        ZZZMigrationBudget b=_budget();
        vm.mockCall(address(ac),abi.encodeCall(ac.canConfigure,(address(adverse))),abi.encode(true));
        adverse.reenter(address(b),abi.encodeCall(b.setLossLimits,(100,1000)));_rebalance();
        assertTrue(adverse.reentryAttempted());assertFalse(adverse.reentrySucceeded());
        assertEq(adverse.reentryError(),ZZZModule.InvalidConfiguration.selector);assertEq(b.maintenanceLossBps(),300);
    }
    function testNormalCustodyApprovalCannotBeWeakenedAfterPolicyIncrease() public {
        ZZZMigration m=_custody();bytes32 id=m.approve(_request(m,false,1940));
        assertEq(m.minimumRetainedUSD(id),1940e18);ac.setPaused(true);m.exit(id);
        bytes32 commitment=m.proofCommitment(id,1);_budget().setLossLimits(100,1000);
        assertEq(m.proofCommitment(id,1),commitment);ac.setPaused(false);
        t0.mint(address(this),900);t1.mint(address(this),900);t0.approve(address(m),900);t1.approve(address(m),900);
        vm.expectRevert(ZZZModule.Slippage.selector);m.completeLocal(id,900,900,1,block.timestamp+100);
        assertEq(uint256(vault.group(_bucket()).status),uint256(PositionStatus.Outbound));
        _return(m,id,970,970);assertEq(m.outstandingCount(),0);
    }
    function testLoweringPolicyDoesNotRewriteAnApprovedCustodyBudget() public {
        ZZZMigration m=_custody();_budget().setLossLimits(100,500);
        bytes32 id=m.approve(_request(m,false,1900));assertEq(m.minimumRetainedUSD(id),1900e18);
        _budget().setLossLimits(100,0);ac.setPaused(true);m.exit(id);ac.setPaused(false);
        _return(m,id,950,950);assertEq(m.outstandingCount(),0);
    }
    function testRawEmergencyRetainsExplicitMinimaAndNoUSDBudget() public {
        ZZZMigration m=_custody();_budget().setLossLimits(100,0);vm.warp(block.timestamp+4000);
        bytes32 id=m.approve(_request(m,true,0));assertEq(m.minimumRetainedUSD(id),0);
        ac.setPaused(true);m.exit(id);assertEq(t0.balanceOf(bob),101000);assertEq(t1.balanceOf(bob),101000);
    }
}
