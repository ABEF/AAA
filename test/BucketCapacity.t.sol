// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Ids, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Local real-module regression; the LP venue, feeds and authority
/// are fixture mocks. This is not a production chain gas measurement.
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

    function testFourHistoricalCanonicalBucketsRejectNewPoolButAllowExistingPoolNFT() public {
        uint256[] memory ids = _canonicalBuckets(4);
        assertEq(vault.MAX_BUCKETS(), 4); assertEq(vault.bucketCount(), 4);
        uint256 entrant = _mint(bob); bytes32 extra = _poolAt(4);
        vm.prank(bob); vm.expectRevert(); vault.activate(entrant, extra, 1000, 1000, 1, block.timestamp + 100);
        assertEq(vault.bucketCount(), 4); assertEq(vault.poolBucket(extra), 0); assertEq(vault.nftBucket(entrant), 0);
        assertFalse(membership.eligible(entrant));
        _activate(bob, entrant, 1000, 1000);
        assertEq(vault.bucketCount(), 4); assertEq(vault.nftBucket(entrant), vault.nftBucket(ids[0]));
        assertEq(membership.totalEligible(), 5);
        vm.prank(alice); vault.increase(ids[0], 100, 100, 1, block.timestamp + 100);
        assertEq(vault.bucketCount(), 4); assertEq(membership.totalEligible(), 5);
    }




    function testMaximumFundedFourBucketEntryWorkload() public {
        uint256[] memory ids = _canonicalBuckets(4);
        for (uint256 i; i < 4; ++i) {
            venue.setFees(19, 19); vault.collectFees(vault.nftBucket(ids[i]), block.timestamp + 100);
        }
        assertEq(fees.accounted(address(t0)), 4 * 19); assertEq(rewards.liabilities(address(t0)), 0);
        uint256 entrant = _mint(bob);
        vm.cool(address(vault)); vm.cool(address(fees)); vm.cool(address(membership)); vm.cool(address(rewards));
        vm.cool(address(t0)); vm.cool(address(t1)); vm.cool(address(venue)); vm.cool(address(pools));
        vm.cool(address(oracle)); vm.cool(address(policy)); vm.cool(address(nft.royaltyRewards()));
        // The royalty-ledger getter touches the NFT; cool it after that read.
        vm.cool(address(nft));
        uint256 start = gasleft(); vm.prank(bob);
        vault.activate(entrant, poolId, 1000, 1000, 1, block.timestamp + 100);
        uint256 used = start - gasleft(); emit log_named_uint("membership.4-distinct-funded-buckets.activation", used);
        assertLt(used, 12_000_000, "4-bucket entry exceeds local reviewed workload budget");
        assertEq(vault.bucketCount(), 4); assertEq(membership.totalEligible(), 5);
        assertEq(rewards.claimable(entrant, address(t0)), 0); assertEq(rewards.claimable(entrant, address(t1)), 0);
        assertEq(rewards.liabilities(address(t0)), 4 * 19); assertEq(fees.accounted(address(t0)), 0);
        for (uint256 i; i < 4; ++i) {
            assertEq(fees.dust(vault.nftBucket(ids[i]), address(t0)), 0);
            assertEq(rewards.claimable(ids[i], address(t0)), 19); assertEq(rewards.claimable(ids[i], address(t1)), 19);
        }
    }
}
