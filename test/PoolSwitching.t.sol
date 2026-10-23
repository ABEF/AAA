// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {MockToken, MockRoutes, MockReadyRouter} from "./mocks/Mocks.sol";
import {Ids, PoolConfig, Position, PositionStatus, Route} from "../src/libraries/ZZZTypes.sol";

/// @notice Actual Vault/Migration/Fees/Rewards/NFT integration. Pool registry,
/// authority, feeds and LP execution are fixtures; no arbitrary venue is tested.
contract PoolSwitchingTest is PooledVaultFixture {
    function _migration() private returns (ZZZMigration migration) {
        migration = new ZZZMigration(address(ac)); ac.bind(Ids.MIGRATION, address(migration));
    }

    function _poolAt(uint256 index) private returns (bytes32 target) {
        PoolConfig memory c = pools.get(poolId); c.key.fee = uint24(500 + index);
        target = keccak256(abi.encode(c.key)); pools.set(target, c);
    }

    function _assertIdentity(uint256 id, uint256 shares, uint256 supply, Position memory home) private view {
        uint256 bucket = vault.nftBucket(id); Position memory current = vault.group(bucket);
        assertEq(bucket, _bucket()); assertEq(vault.homePoolId(bucket), poolId);
        assertEq(vault.sharesOf(id), shares); assertEq(vault.bucketTotalShares(bucket), supply);
        assertEq(current.homeChain, home.homeChain); assertEq(current.homeVault, home.homeVault);
        assertEq(current.homeReceiver, home.homeReceiver); assertEq(current.homeToken0, home.homeToken0);
        assertEq(current.homeToken1, home.homeToken1); assertEq(current.depositUSD, home.depositUSD);
        assertEq(current.locationChain, block.chainid); assertEq(current.locationVault, address(vault));
        assertEq(uint256(current.status), uint256(PositionStatus.Active));
        assertTrue(membership.eligible(id));
    }

    function testSamePairSwitchKeepsTwoNFTSharesFundedRewardsAndHomeIdentity() public {
        uint256 first = activatedPosition(); uint256 second = _mint(bob); _activate(bob, second, 1000, 1000);
        uint256 bucket = _bucket(); uint256 shares = vault.sharesOf(first); uint256 supply = vault.bucketTotalShares(bucket);
        Position memory beforePosition = vault.group(bucket); uint256 secondShares = vault.sharesOf(second);
        venue.setFees(100, 100); vault.collectFees(bucket, block.timestamp + 100);
        assertEq(rewards.claimable(first, address(t0)), 45); assertEq(rewards.claimable(second, address(t0)), 45);
        t0.mint(address(vault), 777); t1.mint(address(vault), 888);

        bytes32 target = _poolAt(1); _migration().movePool(bucket, target, 1, block.timestamp + 100);
        Position memory afterPosition = vault.group(bucket);
        _assertIdentity(first, shares, supply, beforePosition);
        assertEq(vault.sharesOf(second), secondShares); assertEq(nft.ownerOf(first), alice); assertEq(nft.ownerOf(second), bob);
        assertEq(afterPosition.poolId, target); assertTrue(afterPosition.lpTokenId != beforePosition.lpTokenId);
        assertEq(venue.ownerOf(afterPosition.lpTokenId), address(vault));
        vm.expectRevert(); venue.ownerOf(beforePosition.lpTokenId);
        assertEq(venue.a0(afterPosition.lpTokenId), 2005); assertEq(venue.a1(afterPosition.lpTokenId), 2005);
        assertEq(afterPosition.idle0, 0); assertEq(afterPosition.idle1, 0);
        assertEq(vault.totalIdle(address(t0)), 0); assertEq(vault.totalIdle(address(t1)), 0);
        assertEq(t0.balanceOf(address(vault)), 777); assertEq(t1.balanceOf(address(vault)), 888);
        assertEq(fees.compoundBalance(bucket, address(t0)), 0); assertEq(fees.buybackBalance(address(t0)), 5);
        assertEq(rewards.claimable(first, address(t0)), 45); assertEq(rewards.claimable(second, address(t0)), 45);
        assertEq(vault.bucketCount(), 1); assertEq(vault.poolBucket(poolId), bucket); assertEq(vault.poolBucket(target), bucket);
        assertEq(t0.allowance(address(vault), address(venue)), 0); assertEq(t1.allowance(address(vault), address(venue)), 0);
        assertEq(membership.totalEligible(), 2);
        vm.prank(alice); nft.transferFrom(alice, bob, first);
        vm.prank(bob); assertEq(rewards.claim(first, address(t0)), 45);
        assertEq(venue.a0(afterPosition.lpTokenId), 2005); assertEq(fees.buybackBalance(address(t0)), 5);
    }

    function testFullCapacitySwitchAndReturnReuseTheExistingBucketSlot() public {
        uint256 id = activatedPosition(); uint256 bucket = _bucket();
        uint256 shares = vault.sharesOf(id); Position memory home = vault.group(bucket);
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) vault.reservePool(_poolAt(i), 10000 + i);
        bytes32 target = _poolAt(10); ZZZMigration migration = _migration();
        migration.movePool(bucket, target, 1, block.timestamp + 100);
        uint256 middle = vault.group(bucket).lpTokenId;
        assertEq(vault.bucketCount(), 4); assertEq(vault.poolBucket(target), bucket);
        migration.movePool(bucket, poolId, 1, block.timestamp + 100);
        _assertIdentity(id, shares, shares, home);
        assertEq(vault.bucketCount(), 4); assertEq(vault.group(bucket).poolId, poolId);
        assertTrue(vault.group(bucket).lpTokenId != middle); vm.expectRevert(); venue.ownerOf(middle);
        for (uint256 i = 1; i < vault.MAX_BUCKETS(); ++i) assertEq(vault.bucketAt(i), 10000 + i);
    }

    function testChangedPairReversedOrderAndDisabledPoolRemainRejectedAtomically() public {
        uint256 id = activatedPosition(); Position memory beforePosition = vault.group(_bucket());
        ZZZMigration migration = _migration(); MockToken other = new MockToken(0);
        for (uint256 i; i < 3; ++i) {
            PoolConfig memory c = pools.get(poolId); c.key.fee = uint24(700 + i);
            if (i == 0) c.key.currency1 = address(other);
            else if (i == 1) { c.key.currency0 = address(t1); c.key.currency1 = address(t0); }
            else c.operationsEnabled = false;
            bytes32 target = keccak256(abi.encode(c.key)); pools.set(target, c);
            vm.expectRevert(bytes4(keccak256("InvalidConfiguration()")));
            migration.movePool(_bucket(), target, 1, block.timestamp + 100);
            assertEq(vault.poolBucket(target), 0); assertEq(vault.bucketCount(), 1);
            assertEq(vault.group(_bucket()).poolId, poolId); assertEq(vault.group(_bucket()).lpTokenId, beforePosition.lpTokenId);
            assertEq(venue.ownerOf(beforePosition.lpTokenId), address(vault)); assertEq(vault.sharesOf(id), 2000e18);
        }
    }

    function testVenueFailureRollsBackCloseFeesCompoundAndNewPoolReservation() public {
        uint256 id = activatedPosition(); Position memory beforePosition = vault.group(_bucket());
        uint256 shares = vault.sharesOf(id); venue.setFees(100, 100); venue.setFail(true);
        bytes32 target = _poolAt(1); ZZZMigration migration = _migration();
        vm.expectRevert(); migration.movePool(_bucket(), target, 1, block.timestamp + 100);
        _assertIdentity(id, shares, shares, beforePosition);
        assertEq(vault.group(_bucket()).lpTokenId, beforePosition.lpTokenId); assertEq(vault.group(_bucket()).poolId, poolId);
        assertEq(venue.ownerOf(beforePosition.lpTokenId), address(vault)); assertEq(venue.a0(beforePosition.lpTokenId), 1000);
        assertEq(venue.fee0(), 100); assertEq(venue.fee1(), 100);
        assertEq(fees.compoundBalance(_bucket(), address(t0)), 0); assertEq(fees.buybackBalance(address(t0)), 0);
        assertEq(rewards.claimable(id, address(t0)), 0); assertEq(rewards.liabilities(address(t0)), 0);
        assertEq(vault.poolBucket(target), 0); assertEq(vault.bucketCount(), 1);
        assertEq(t0.balanceOf(address(vault)), 0); assertEq(t1.balanceOf(address(vault)), 0);
        assertEq(t0.allowance(address(vault), address(venue)), 0); assertEq(t1.allowance(address(vault), address(venue)), 0);
    }

    function testPoolAlreadyAssignedToAnotherBucketCannotBeTakenBySwitch() public {
        uint256 first = activatedPosition(); bytes32 target = _poolAt(1);
        uint256 second = _mint(bob); vm.prank(bob); vault.activate(second, target, 1000, 1000, 1, block.timestamp + 100);
        uint256 firstBucket = vault.nftBucket(first); uint256 secondBucket = vault.nftBucket(second);
        uint256 firstLP = vault.group(firstBucket).lpTokenId; uint256 secondLP = vault.group(secondBucket).lpTokenId;
        ZZZMigration migration = _migration(); vm.expectRevert(bytes4(keccak256("InvalidState()")));
        migration.movePool(firstBucket, target, 1, block.timestamp + 100);
        assertEq(vault.poolBucket(target), secondBucket); assertEq(vault.poolBucket(poolId), firstBucket);
        assertEq(vault.group(firstBucket).lpTokenId, firstLP); assertEq(vault.group(secondBucket).lpTokenId, secondLP);
        assertEq(venue.ownerOf(firstLP), address(vault)); assertEq(venue.ownerOf(secondLP), address(vault));
        assertEq(vault.bucketCount(), 2); assertEq(membership.totalEligible(), 2);
    }

    function testRolePauseDeadlineMinimumAndSamePoolGuardsPreserveCustody() public {
        uint256 id = activatedPosition(); Position memory home = vault.group(_bucket());
        uint256 shares = vault.sharesOf(id); bytes32 target = _poolAt(1); ZZZMigration migration = _migration();
        vm.prank(alice); vm.expectRevert(); migration.movePool(_bucket(), target, 1, block.timestamp + 100);
        vm.prank(alice); vm.expectRevert(); vault.movePool(_bucket(), target, 1, block.timestamp + 100);
        vm.expectRevert(); migration.movePool(_bucket(), target, 0, block.timestamp + 100);
        vm.expectRevert(); migration.movePool(_bucket(), target, 1, block.timestamp - 1);
        vm.expectRevert(); migration.movePool(_bucket(), target, 1, block.timestamp + 601);
        vm.expectRevert(); migration.movePool(_bucket(), poolId, 1, block.timestamp + 100);
        ac.setPaused(true); vm.expectRevert(); migration.movePool(_bucket(), target, 1, block.timestamp + 100);
        _assertIdentity(id, shares, shares, home);
        assertEq(vault.group(_bucket()).lpTokenId, home.lpTokenId); assertEq(vault.bucketCount(), 1);
        assertEq(vault.poolBucket(target), 0); assertEq(venue.ownerOf(home.lpTokenId), address(vault));
    }


}
