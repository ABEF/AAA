// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {BudgetAdversarialVenue} from "./MigrationBudgetAdversarial.t.sol";
import {RebalanceBudgetPolicy} from "./RebalanceBudget.t.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";

/// @dev TEST ONLY exact-transfer runtime substitute. Its authenticated mock
/// authority tries to widen future policy during the real Vault's asset pull.
contract LossPolicyCallbackToken is MockToken {
    ZZZMigrationBudget private budget;
    address private watched;
    bool private armed;
    constructor() MockToken(0) {}
    function configure(ZZZMigrationBudget target,address recipient) external { budget=target;watched=recipient;armed=true; }
    function _update(address from,address to,uint256 amount) internal override {
        super._update(from,to,amount);
        if (armed && to==watched && amount!=0) { armed=false;budget.setLossLimits(1000,300); }
    }
}

/// @dev TEST ONLY burned execution loss, with backed retained principal. The
/// shared position can grow without treating undeployed idle as an actual loss.
contract GovernedGrowthLossVenue is BudgetAdversarialVenue {
    MockToken private immutable first;
    MockToken private immutable second;
    constructor(address a,address b) BudgetAdversarialVenue(a,b) {first=MockToken(a);second=MockToken(b);}
    function increase(bytes32,uint256 id,uint256 a,uint256 b,uint128,uint256)
        external returns(uint256 used0,uint256 used1) {
        used0=a;used1=b;
        require(first.transferFrom(msg.sender,address(this),a));require(second.transferFrom(msg.sender,address(this),b));
        amount0[id]+=a-mintLoss0;amount1[id]+=b-mintLoss1;
        first.burn(mintLoss0);second.burn(mintLoss1);
    }
}

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
    function testDefaultsHardMaximumZeroAndGovernanceEvents() public {
        ZZZMigrationBudget b=_budget();assertEq(b.MAX_LOSS_BPS(),1000);
        assertEq(b.contributionLossBps(),200);assertEq(b.maintenanceLossBps(),300);
        vm.expectEmit(false,false,false,true,address(b));emit ContributionLossLimitChanged(200,1000);
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
        _budget().setLossLimits(100,300);
        GovernedGrowthLossVenue lossy=new GovernedGrowthLossVenue(address(t0),address(t1));
        ac.bind(Ids.LIQUIDITY,address(lossy));lossy.losses(0,0,20,0);
        _venueLimit(1000);uint256 id=_mint(alice);
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,1000,0);
        _budget().setLossLimits(200,300);_activate(alice,id,1000,0);
        assertEq(lossy.amount0(vault.group(_bucket()).lpTokenId),980);
        assertEq(vault.sharesOf(id),980e18);
        assertEq(vault.group(_bucket()).idle0,0);
        uint256 shares=vault.sharesOf(id);uint256 before=t0.balanceOf(alice);
        // A real 2% modeled execution loss satisfies the governed 2% floor,
        // but not the venue's stricter 1% net-value guard. No idle masks loss.
        _venueLimit(100);
        vm.prank(alice);vm.expectRevert(ZZZModule.Slippage.selector);vault.increase(id,1000,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(id),shares);assertEq(t0.balanceOf(alice),before);
    }
    function testLaterContributionsUseSamePolicyWithoutBorrowingIncumbentIdle() public {
        _budget().setLossLimits(100,300);
        uint256 id=activatedPosition();_venueLimit(1000);venue.setSpendBps(9800);
        vm.prank(alice);vm.expectRevert(ZZZModule.Slippage.selector);vault.increase(id,1000,0,1,block.timestamp+100);
        _budget().setLossLimits(200,300);vm.prank(alice);vault.increase(id,1000,0,1,block.timestamp+100);
        assertEq(vault.contributionUSD(id),3000e18);assertEq(vault.sharesOf(id),3000e18);
        assertEq(vault.group(_bucket()).idle0,20);
    }
    function testPackedContributionCapStaysFixedDespiteLaterGovernanceChange() public {
        _budget().setLossLimits(100,300);
        _venueLimit(1000);uint256 id=_mint(alice);venue.setSpendBps(9800);
        LossPolicyCallbackToken implementation=new LossPolicyCallbackToken();
        vm.etch(address(t0),address(implementation).code);
        LossPolicyCallbackToken(address(t0)).configure(_budget(),address(vault));
        vm.mockCall(address(ac),abi.encodeCall(ac.canConfigure,(address(t0))),abi.encode(true));
        uint256 before=t0.balanceOf(alice);
        // Callback successfully invokes governance, but the operation captured
        // 1% before this pull. A later 10% policy cannot make 98% LP acceptable.
        vm.prank(alice);vm.expectRevert(ZZZModule.Slippage.selector);vault.activate(id,poolId,1000,0,1,block.timestamp+100);
        assertEq(_budget().contributionLossBps(),100);assertEq(t0.balanceOf(alice),before);
        assertEq(vault.sharesOf(id),0);assertFalse(membership.eligible(id));
        // An independently governed future policy is used by the next operation.
        _budget().setLossLimits(1000,300);_activate(alice,id,1000,0);
        assertEq(_budget().contributionLossBps(),1000);assertEq(vault.sharesOf(id),1000e18);
        assertEq(venue.a0(vault.group(_bucket()).lpTokenId),980);
    }
    function testRetainedValueRoundsUpAndCannotExceedHardMaximum() public {
        MockFeed first=new MockFeed(18,1);MockFeed second=new MockFeed(18,1);
        oracle.setDualFeed(address(t0),
            ZZZOracle.SourcePolicy(address(first),address(first).codehash,keccak256("rounding-first"),3600,18),
            ZZZOracle.SourcePolicy(address(second),address(second).codehash,keccak256("rounding-second"),3600,18),
            0,REVIEW);
        BudgetAdversarialVenue exact=new BudgetAdversarialVenue(address(t0),address(t1));
        ac.bind(Ids.LIQUIDITY,address(exact));_venueLimit(1000);
        // Zero-decimal token at 1 wei USD per raw unit: the real activation is
        // $100 + 1 wei USD. Venue burns execution loss; idle cannot hide it.
        uint256 input=100e18+1;uint256 loss=10e18;uint256 floor=90e18+1;
        t0.mint(alice,input);uint256 id=_mint(alice);uint256 before=t0.balanceOf(alice);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);_budget().setLossLimits(1001,300);
        _budget().setLossLimits(0,300);exact.losses(0,0,1,0);
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,input,0);
        _budget().setLossLimits(1000,300);exact.losses(0,0,loss+1,0);
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,input,0);
        assertEq(t0.balanceOf(alice),before);assertEq(vault.sharesOf(id),0);
        exact.losses(0,0,loss,0);_activate(alice,id,input,0);
        assertEq(vault.sharesOf(id),floor);assertEq(vault.contributionUSD(id),input);
        assertEq(exact.amount0(vault.group(_bucket()).lpTokenId),floor);
        assertEq(vault.group(_bucket()).idle0,0);
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
}
