// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {MockAccess, MockToken, MockPools, MockFeed} from "./mocks/Mocks.sol";
import {Ids, PoolConfig, Position} from "../src/libraries/ZZZTypes.sol";

contract MigrationExecutionBudgetTest is PooledVaultFixture {
    event MigrationValueChecked(uint256 indexed bucketId, uint256 beforeUSD, uint256 deployedUSD, uint256 idleUSD);

    function _target() private returns (bytes32 target) {
        PoolConfig memory c = pools.get(poolId);
        c.key.fee = 500;
        target = keccak256(abi.encode(c.key));
        pools.set(target, c);
    }
    function _migration() private returns (ZZZMigration migration) {
        migration = new ZZZMigration(address(ac));
        ac.bind(Ids.MIGRATION, address(migration));
    }
    function testReceiptIncludesOldAndNewDesignatedCompoundWithoutCountingRewardsBuybackOrDonations() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        venue.setFees(200, 400);
        vault.collectFees(bucket, block.timestamp + 100);
        assertEq(fees.compoundBalance(bucket, address(t0)), 10);
        assertEq(fees.compoundBalance(bucket, address(t1)), 20);
        t0.mint(address(vault), 777);
        t1.mint(address(vault), 888);
        venue.setFees(100, 200);
        bytes32 target = _target();
        ZZZMigration migration = _migration();
        vm.expectEmit(true, false, false, true, address(vault.migrationBudget()));
        emit MigrationValueChecked(bucket, 2045e18, 2045e18, 0);
        migration.movePool(bucket, target, 1, block.timestamp + 100);
        Position memory p = vault.group(bucket);
        assertEq(venue.a0(p.lpTokenId), 1015);
        assertEq(venue.a1(p.lpTokenId), 1030);
        assertEq(rewards.claimable(id, address(t0)), 270);
        assertEq(rewards.claimable(id, address(t1)), 540);
        assertEq(fees.buybackBalance(address(t0)), 15);
        assertEq(fees.buybackBalance(address(t1)), 30);
        assertEq(t0.balanceOf(address(vault)), 777);
        assertEq(t1.balanceOf(address(vault)), 888);
        assertEq(vault.sharesOf(id), 2000e18);
    }
    function testRepeatedMovesStartFreshSnapshotsIncludingAttributedIdle() public {
        activatedPosition();
        uint256 bucket = _bucket();
        bytes32 target = _target();
        ZZZMigration migration = _migration();
        venue.setSpendBps(9500);
        vm.expectEmit(true, false, false, true, address(vault.migrationBudget()));
        emit MigrationValueChecked(bucket, 2000e18, 1900e18, 100e18);
        migration.movePool(bucket, target, 1, block.timestamp + 100);
        assertEq(vault.group(bucket).idle0, 50);
        assertEq(vault.group(bucket).idle1, 50);
        venue.setSpendBps(10000);
        vm.expectEmit(true, false, false, true, address(vault.migrationBudget()));
        emit MigrationValueChecked(bucket, 2000e18, 2000e18, 0);
        migration.movePool(bucket, poolId, 1, block.timestamp + 100);
        assertEq(vault.group(bucket).idle0, 0);
        assertEq(vault.group(bucket).idle1, 0);
    }
    function testStaleBaselineFeedRejectsBeforeHarvestAndPreservesCustody() public {
        uint256 id = activatedPosition();
        uint256 bucket = _bucket();
        Position memory beforePosition = vault.group(bucket);
        venue.setFees(100, 200);
        bytes32 target = _target();
        ZZZMigration migration = _migration();
        vm.warp(block.timestamp + 3601);
        vm.expectRevert();
        migration.movePool(bucket, target, 1, block.timestamp + 100);
        assertEq(venue.fee0(), 100);
        assertEq(venue.fee1(), 200);
        assertEq(vault.group(bucket).lpTokenId, beforePosition.lpTokenId);
        assertEq(venue.ownerOf(beforePosition.lpTokenId), address(vault));
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(vault.poolBucket(target), 0);
    }
}

/// @dev Only the helper valuation math is isolated here. Integration tests above
/// and the adversarial suite use the actual Vault, fees, ownership and shares.
contract MigrationBudgetScaleHarness {
    ZZZMigrationBudget public immutable budget;
    Position private position;
    uint256 private amount0;
    uint256 private amount1;
    constructor(address access) { budget = new ZZZMigrationBudget(access); }
    function setAmounts(uint256 a0, uint256 a1) external {
        position.poolId = bytes32(uint256(1));
        position.lpTokenId = 1;
        amount0 = a0;
        amount1 = a1;
    }
    function group(uint256) external view returns (Position memory) { return position; }
    function amounts(uint256) external view returns (uint256, uint256) { return (amount0, amount1); }
    function begin() external { budget.checkpoint(1, 0); budget.checkpoint(1, 1); }
    function finish() external { budget.checkpoint(1, 2); }
}

contract MigrationBudgetScaleTest is Test {
    MigrationBudgetScaleHarness private harness;
    MockFeed private stableFeed;
    MockFeed private nativeFeed;
    function setUp() public {
        vm.warp(1_000_000);
        MockAccess ac = new MockAccess();
        MockPools pools = new MockPools();
        MockToken stable = new MockToken(6);
        MockToken native = new MockToken(18);
        stableFeed = new MockFeed(8, 1e8);
        nativeFeed = new MockFeed(8, 2000e8);
        ZZZOracle oracle = new ZZZOracle(address(ac), address(0));
        oracle.setFeed(address(stable), address(stableFeed), 3600);
        oracle.setFeed(address(native), address(nativeFeed), 3600);
        PoolConfig memory c;
        c.key.currency0 = address(stable);
        c.key.currency1 = address(native);
        pools.set(bytes32(uint256(1)), c);
        harness = new MigrationBudgetScaleHarness(address(ac));
        ac.bind(Ids.ORACLE, address(oracle));
        ac.bind(Ids.POOLS, address(pools));
        ac.bind(Ids.LIQUIDITY, address(harness));
    }
    function testMixedDecimalsAndUnequalPricesAcceptExactlyThreePercentAggregateLoss() public {
        harness.setAmounts(1000e6, 1 ether); // $3,000 principal.
        harness.begin();
        harness.setAmounts(910e6, 1 ether); // $2,910, exactly 97%.
        harness.finish();
    }
    function testMixedDecimalsRejectOneStableBaseUnitPastFloorDespiteHigherLiveFeed() public {
        harness.setAmounts(1000e6, 1 ether);
        harness.begin();
        nativeFeed.set(4000e8, block.timestamp, block.timestamp);
        harness.setAmounts(910e6 - 1, 1 ether);
        vm.expectRevert(ZZZMigrationBudget.Slippage.selector);
        harness.finish();
    }
}
