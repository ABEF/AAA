// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {PoolConfig, PoolKey, Position} from "../src/libraries/ZZZTypes.sol";

/// @notice Current Budget4 cadence and accounting composition. The venue and
/// need flag are explicit synthetic fixtures; real Strategy3/Confirmation3
/// trigger sampling is verified separately in RebalanceConfirmation/PortfolioPolicy.
/// No native venue, market/MEV or installed-keeper qualification is implied.
contract MaintenanceCadenceTest is PooledVaultFixture {
    uint256 private constant INTERVAL = 600;

    function setUp() public override {
        super.setUp();
        PoolConfig memory c = pools.get(poolId);
        c.minRebalanceInterval = uint32(INTERVAL);
        pools.set(poolId, c);
        vault.migrationBudget().setCompoundInterval(poolId,uint32(INTERVAL));
        policy.setNeed(false);
    }

    function _compound(uint256 bucket) private {
        compounder.compound(bucket, 1, block.timestamp + 100);
    }

    function _ready(uint256 bucket) private view returns (bool) {
        return vault.migrationBudget().compoundReady(bucket);
    }

    function testFirstCompoundWaitsAfterCreationAtExactBoundary() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        uint256 created = vault.group(bucket).lastRebalance;
        assertEq(vault.migrationBudget().IDLE_COMPOUNDING_VERSION(), 4);
        venue.setFees(100, 100);
        vm.warp(created + INTERVAL - 1);
        assertFalse(_ready(bucket));
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector);
        _compound(bucket);
        assertEq(venue.fee0(), 100);
        assertEq(vault.migrationBudget().lastCompound(bucket), 0);
        vm.warp(created + INTERVAL);
        assertTrue(_ready(bucket));
        _compound(bucket);
        assertEq(vault.migrationBudget().lastCompound(bucket), block.timestamp);
        assertEq(vault.group(bucket).lastRebalance, created);
        assertEq(rewards.claimable(id, address(t0)), 90);
    }

    function testCompoundThenCompoundUsesOwnExactBoundary() public {
        activatedPosition();
        uint256 bucket = _bucket();
        vm.warp(block.timestamp + INTERVAL);
        venue.setFees(100, 100);
        _compound(bucket);
        uint256 previous = block.timestamp;
        venue.setFees(100, 100); // A successful retry needs actual new backing.
        vm.warp(previous + INTERVAL - 1);
        assertFalse(_ready(bucket));
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector);
        _compound(bucket);
        assertEq(venue.fee0(), 100);
        vm.warp(previous + INTERVAL);
        assertTrue(_ready(bucket));
        _compound(bucket);
    }

    function testRebalanceThenCompoundWaitsWithoutBlockingHarvestOrClaim() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        vm.warp(block.timestamp + INTERVAL);
        policy.setNeed(true);
        vault.rebalance(bucket, 1, block.timestamp + 100);
        policy.setNeed(false);
        uint256 replacement = vault.group(bucket).lastRebalance;
        venue.setFees(100, 100);
        vault.collectFees(bucket, block.timestamp + 100);
        vm.prank(alice);
        assertEq(rewards.claim(id, address(t0)), 90);
        assertEq(fees.compoundBalance(bucket, address(t0)), 5);
        assertFalse(_ready(bucket));
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector);
        _compound(bucket);
        vm.warp(replacement + INTERVAL);
        _compound(bucket);
    }

    function testRecentCompoundCannotPostponeAnEligibleRebalance() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        vm.warp(block.timestamp + INTERVAL);
        venue.setFees(100, 100);
        _compound(bucket);
        uint256 shares = vault.sharesOf(id);
        uint256 oldLP = vault.group(bucket).lpTokenId;
        uint256 compounded = block.timestamp;
        // The original rebalance interval has elapsed. A newly eligible trigger
        // must not be vetoed by the compound which completed in this block.
        policy.setNeed(true);
        vault.rebalance(bucket, 1, block.timestamp + 100);
        assertGt(vault.group(bucket).lpTokenId, oldLP);
        assertEq(vault.group(bucket).lastRebalance, compounded);
        assertEq(vault.migrationBudget().lastCompound(bucket), compounded);
        assertEq(vault.sharesOf(id), shares);
    }

    function testEligibleRebalanceRejectsCompoundBeforeFeeOrClockMutation() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        vm.warp(block.timestamp + INTERVAL);
        venue.setFees(100, 100);
        policy.setNeed(true);
        assertFalse(_ready(bucket));
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector);
        _compound(bucket);
        assertEq(venue.fee0(), 100);
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(vault.migrationBudget().lastCompound(bucket), 0);
        vault.rebalance(bucket, 1, block.timestamp + 100);
        assertEq(rewards.claimable(id, address(t0)), 90);
    }

    function testLateCompoundFailureRollsBackBackingAndCooldownForRetry() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        vm.warp(block.timestamp + INTERVAL);
        Position memory beforePosition = vault.group(bucket);
        uint256 shares = vault.sharesOf(id);
        venue.setFees(10000, 10000);
        venue.setSpendBps(0); // Late deployment leaves more than 5% idle.
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector);
        _compound(bucket);
        assertEq(vault.migrationBudget().lastCompound(bucket), 0);
        assertEq(venue.fee0(), 10000);
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(fees.compoundBalance(bucket, address(t0)), 0);
        assertEq(fees.buybackBalance(address(t0)), 0);
        assertEq(vault.group(bucket).lpTokenId, beforePosition.lpTokenId);
        assertEq(vault.group(bucket).idle0, beforePosition.idle0);
        assertEq(vault.sharesOf(id), shares);
        venue.setSpendBps(10000);
        _compound(bucket);
        assertEq(vault.migrationBudget().lastCompound(bucket), block.timestamp);
        assertEq(rewards.claimable(id, address(t0)), 9000);
    }

    function testAvailablePreapprovedRangeSelectionTakesPriorityBeforeItIsApplied() public {
        activatedPosition();
        uint256 bucket = _bucket();
        vm.warp(block.timestamp + INTERVAL);
        assertTrue(_ready(bucket));
        policy.setRangeTarget(2500);
        assertFalse(_ready(bucket));
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector);
        _compound(bucket);
        assertEq(vault.migrationBudget().lastCompound(bucket), 0);
        policy.setRangeTarget(0);
        assertTrue(_ready(bucket));
    }

    function testGovernedIntervalChangeAndOperationsDisableAreRespected() public {
        activatedPosition();
        uint256 bucket = _bucket();
        vm.warp(block.timestamp + INTERVAL);
        PoolConfig memory c = pools.get(poolId);
        vault.migrationBudget().setCompoundInterval(poolId,1200);
        assertFalse(_ready(bucket));
        vault.migrationBudget().setCompoundInterval(poolId,uint32(INTERVAL));
        assertTrue(_ready(bucket));
        c.operationsEnabled = false;
        pools.set(poolId, c);
        assertFalse(_ready(bucket));
    }

    function testTopUpDoesNotResetCadenceOrSuppressHarvest() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        uint256 created = vault.group(bucket).lastRebalance;
        vm.warp(created + INTERVAL - 1);
        venue.setFees(100, 100);
        vm.prank(alice);
        vault.increase(id, 100, 100, 1, block.timestamp + 100);
        assertEq(vault.group(bucket).lastRebalance, created);
        assertEq(vault.migrationBudget().lastCompound(bucket), 0);
        assertEq(rewards.claimable(id, address(t0)), 90);
        vm.warp(created + INTERVAL);
        assertTrue(_ready(bucket));
    }

    function testBucketClocksAreIndependent() public {
        activatedPosition();
        uint256 first = _bucket();
        PoolConfig memory c = pools.get(poolId);
        c.key = PoolKey(address(t0), address(t1), 500, 60, address(0));
        bytes32 secondPool = keccak256(abi.encode(c.key));
        pools.set(secondPool, c); // Explicit mock admission of historical buckets.
        vault.migrationBudget().setCompoundInterval(secondPool,uint32(INTERVAL));
        uint256 secondNFT = _mint(bob);
        vm.prank(bob);
        vault.activate(secondNFT, secondPool, 1000, 1000, 1, block.timestamp + 100);
        uint256 second = vault.nftBucket(secondNFT);
        vm.warp(block.timestamp + INTERVAL);
        venue.setFees(100, 100);
        _compound(first);
        assertFalse(_ready(first));
        assertTrue(_ready(second));
        venue.setFees(100, 100);
        _compound(second);
        assertEq(vault.migrationBudget().lastCompound(second), block.timestamp);
    }

    function testMissingAndDormantBucketsCannotCompound() public {
        assertFalse(_ready(0));
        _mint(alice);
        assertFalse(_ready(_bucket()));
    }
}
