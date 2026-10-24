// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {RewardsAndFeesTest} from "./RewardsAndFees.t.sol";
import {MockToken} from "./mocks/Mocks.sol";
import {IZZZVault, IZZZMembership} from "../src/interfaces/IZZZ.sol";

/// @notice Focused maximum-asset checkpoint tests. Real reward/membership/NFT
/// contracts use the explicitly isolated Vault share fixture from the base suite.
contract RewardsCheckpointCachingTest is RewardsAndFeesTest {
    function _allAssets() private {
        while (rewards.assetCount() < 33) rewards.addAsset(address(new MockToken(18)));
    }

    function _creditAsset(address asset, uint256 personal, uint256 shared) private {
        uint256 amount = personal + shared;
        if (asset == address(0)) {
            vm.deal(address(fees), amount);
            vm.prank(address(fees));
            rewards.creditPool{value: amount}(BUCKET, asset, personal, shared);
        } else {
            MockToken(asset).mint(address(fees), amount);
            vm.startPrank(address(fees));
            MockToken(asset).approve(address(rewards), amount);
            rewards.creditPool(BUCKET, asset, personal, shared);
            vm.stopPrank();
        }
    }

    function testCheckpointCachePreservesAll33CurrenciesBeforeTopUp() public {
        _allAssets();
        vault.join(2, BUCKET, 200); _activate(2);
        uint256[] memory beforeAmounts = new uint256[](33);
        for (uint256 i; i < 33; ++i) {
            address asset = rewards.assets(i);
            _creditAsset(asset, 7, 5);
            beforeAmounts[i] = rewards.claimable(1, asset);
        }
        vault.join(1, BUCKET, 100);
        vm.prank(address(membership)); rewards.checkpointAll(1);
        for (uint256 i; i < 33; ++i) {
            address asset = rewards.assets(i);
            assertEq(rewards.claimable(1, asset), beforeAmounts[i]);
            assertEq(rewards.paidOwnerIndex(1, asset), rewards.ownerIndex(BUCKET, asset));
            assertEq(rewards.paidIndex(1, asset), rewards.index(asset));
            assertGt(rewards.ownerFraction(1, asset), 0);
            assertGt(rewards.fraction(1, asset), 0);
        }
    }

    function testCheckpointCacheDormantExcludesAll33PastCurrencies() public {
        _allAssets();
        for (uint256 i; i < 33; ++i) _creditAsset(rewards.assets(i), 7, 5);
        vault.join(2, BUCKET, 100); _activate(2);
        for (uint256 i; i < 33; ++i) {
            address asset = rewards.assets(i);
            assertEq(rewards.claimable(2, asset), 0);
            assertEq(rewards.paidOwnerIndex(2, asset), rewards.ownerIndex(BUCKET, asset));
            assertEq(rewards.paidIndex(2, asset), rewards.index(asset));
        }
    }

    function testCheckpointCacheReadsOwnerStateOnceAt33Assets() public {
        _allAssets();
        vm.expectCall(address(vault), abi.encodeCall(IZZZVault.nftBucket, (1)), uint64(1));
        vm.expectCall(address(vault), abi.encodeCall(IZZZVault.sharesOf, (1)), uint64(1));
        vm.prank(address(vault)); rewards.checkpointOwner(1);
    }

    function testCheckpointCacheReadsMembershipOnceAt33Assets() public {
        _allAssets();
        vm.expectCall(address(membership), abi.encodeCall(IZZZMembership.eligible, (1)), uint64(1));
        vm.prank(address(membership)); rewards.checkpointAll(1);
    }

    function testCheckpointCacheBenchmarkOwner33() public {
        _allAssets();
        for (uint256 i; i < 33; ++i) _creditAsset(rewards.assets(i), 7, 5);
        vm.prank(address(vault));
        uint256 beforeGas = gasleft();
        rewards.checkpointOwner(1);
        emit log_named_uint("owner_checkpoint_33_gas", beforeGas - gasleft());
    }

    function testCheckpointCacheBenchmarkCollective33() public {
        _allAssets();
        for (uint256 i; i < 33; ++i) _creditAsset(rewards.assets(i), 7, 5);
        vm.prank(address(membership));
        uint256 beforeGas = gasleft();
        rewards.checkpointAll(1);
        emit log_named_uint("collective_checkpoint_33_gas", beforeGas - gasleft());
    }
}
