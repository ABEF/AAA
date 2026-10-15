// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Local real-module regression; the LP venue, feeds and transport
/// authority are fixture mocks. This is not a production chain gas measurement.
contract BucketCapacityTest is PooledVaultFixture {
    function _poolAt(uint256 index) private returns (bytes32 other) {
        if (index == 0) return poolId;
        PoolConfig memory config = pools.get(poolId);
        config.key.fee = uint24(500 + index);
        other = keccak256(abi.encode(config.key));
        pools.set(other, config);
    }

    function _canonicalBuckets(uint256 count) private returns (uint256[] memory ids) {
        ids = new uint256[](count);
        for (uint256 i; i < count; ++i) {
            _fundUser(alice); ids[i] = _mint(alice); bytes32 pool = _poolAt(i);
            vm.prank(alice); vault.activate(ids[i], pool, 1000, 1000, 1, block.timestamp + 100);
        }
    }

    function testSixteenHistoricalCanonicalBucketsRejectNewPoolButAllowExistingPoolNFT() public {
        uint256[] memory ids = _canonicalBuckets(16);
        assertEq(vault.MAX_BUCKETS(), 16); assertEq(vault.bucketCount(), 16);
        uint256 entrant = _mint(bob); bytes32 extra = _poolAt(16);
        vm.prank(bob); vm.expectRevert(); vault.activate(entrant, extra, 1000, 1000, 1, block.timestamp + 100);
        assertEq(vault.bucketCount(), 16); assertEq(vault.poolBucket(extra), 0); assertEq(vault.nftBucket(entrant), 0);
        assertFalse(membership.eligible(entrant));
        _activate(bob, entrant, 1000, 1000);
        assertEq(vault.bucketCount(), 16); assertEq(vault.nftBucket(entrant), vault.nftBucket(ids[0]));
        assertEq(membership.totalEligible(), 17);
        vm.prank(alice); vault.increase(ids[0], 100, 100, 1, block.timestamp + 100);
        assertEq(vault.bucketCount(), 16); assertEq(membership.totalEligible(), 17);
    }

    function testHistoricalCapStillAllowsCanonicalCustodyReturnAndRepeatedDeparture() public {
        uint256[] memory ids = _canonicalBuckets(16); uint256 bucket = vault.nftBucket(ids[0]);
        Position memory original = vault.group(bucket); uint256 shares = vault.bucketTotalShares(bucket);
        for (uint256 i; i < 2; ++i) {
            vault.releaseForMigration(bucket, bytes32(i + 1), block.timestamp + 100);
            vault.confirmMigration(bucket, block.chainid + 1, address(0xF001));
            address receiver = ac.module(Ids.RECEIVER); t0.mint(receiver, 1000); t1.mint(receiver, 1000);
            vm.startPrank(receiver);
            t0.approve(address(vault), 1000); t1.approve(address(vault), 1000);
            vault.importPending(bucket, poolId, original, shares, poolId, 1000, 1000);
            vault.finalizeImport(bucket, 1, block.timestamp + 100); vm.stopPrank();
            assertEq(vault.bucketCount(), 16); assertEq(vault.bucketTotalShares(bucket), shares);
            assertEq(uint256(vault.group(bucket).status), uint256(PositionStatus.Active));
        }
        assertTrue(membership.eligible(ids[0])); assertEq(membership.totalEligible(), 16);
        uint256 entrant = _mint(bob); bytes32 extra = _poolAt(16);
        vm.prank(bob); vm.expectRevert(); vault.activate(entrant, extra, 1000, 1000, 1, block.timestamp + 100);
    }

    function _remoteOrigin(uint256 index) private view returns (uint256 bucket, Position memory origin) {
        origin.homeChain = vault.canonicalChainId(); origin.homeVault = address(uint160(0x10000 + index));
        origin.homeReceiver = address(0xABCD); origin.homeToken0 = address(t0); origin.homeToken1 = address(t1);
        origin.depositUSD = 2000e18;
        bucket = uint256(keccak256(abi.encode(origin.homeChain, origin.homeVault, poolId)));
    }

    function _importRemote(uint256 index) private returns (uint256 bucket) {
        Position memory origin; (bucket, origin) = _remoteOrigin(index); bytes32 destination = _poolAt(index);
        vault.reservePool(destination, bucket);
        address receiver = ac.module(Ids.RECEIVER); t0.mint(receiver, 1000); t1.mint(receiver, 1000);
        vm.startPrank(receiver); t0.approve(address(vault), 1000); t1.approve(address(vault), 1000);
        vault.importPending(bucket, destination, origin, 2000e18, poolId, 1000, 1000); vm.stopPrank();
    }

    function testSatelliteImportHistoryHasTheSameSixteenBucketLimit() public {
        vm.chainId(block.chainid + 1);
        for (uint256 i; i < 16; ++i) _importRemote(i);
        assertEq(vault.bucketCount(), 16); assertEq(vault.totalIdle(address(t0)), 16000);
        uint256 bucket; Position memory origin; (bucket, origin) = _remoteOrigin(16);
        bytes32 destination = _poolAt(16); vault.reservePool(destination, bucket);
        vm.prank(ac.module(Ids.RECEIVER)); vm.expectRevert();
        vault.importPending(bucket, destination, origin, 2000e18, poolId, 1000, 1000);
        assertEq(vault.bucketCount(), 16); assertEq(vault.totalIdle(address(t0)), 16000);
        assertEq(uint256(vault.group(bucket).status), uint256(PositionStatus.None));
    }

    function testMaximumFundedSixteenBucketEntryWorkload() public {
        uint256[] memory ids = _canonicalBuckets(16);
        for (uint256 i; i < 16; ++i) {
            venue.setFees(19, 19); vault.collectFees(vault.nftBucket(ids[i]), block.timestamp + 100);
        }
        assertEq(fees.accounted(address(t0)), 16 * 19); assertEq(rewards.liabilities(address(t0)), 0);
        uint256 entrant = _mint(bob);
        vm.cool(address(vault)); vm.cool(address(fees)); vm.cool(address(membership)); vm.cool(address(rewards));
        vm.cool(address(t0)); vm.cool(address(t1)); vm.cool(address(venue)); vm.cool(address(pools));
        vm.cool(address(oracle)); vm.cool(address(policy)); vm.cool(address(nft)); vm.cool(address(nft.royaltyRewards()));
        uint256 start = gasleft(); vm.prank(bob);
        vault.activate(entrant, poolId, 1000, 1000, 1, block.timestamp + 100);
        uint256 used = start - gasleft(); emit log_named_uint("membership.16-distinct-funded-buckets.activation", used);
        assertLt(used, 12_000_000, "16-bucket entry exceeds local reviewed workload budget");
        assertEq(vault.bucketCount(), 16); assertEq(membership.totalEligible(), 17);
        assertEq(rewards.claimable(entrant, address(t0)), 0); assertEq(rewards.claimable(entrant, address(t1)), 0);
        assertEq(rewards.liabilities(address(t0)), 16 * 19); assertEq(fees.accounted(address(t0)), 0);
        for (uint256 i; i < 16; ++i) {
            assertEq(fees.dust(vault.nftBucket(ids[i]), address(t0)), 0);
            assertEq(rewards.claimable(ids[i], address(t0)), 19); assertEq(rewards.claimable(ids[i], address(t1)), 19);
        }
    }
}
