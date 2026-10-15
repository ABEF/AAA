// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {PoolConfig, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Gross-input UX and actual marginal LP protection, with a fake venue.
/// Native/real venue and stable-input conversion are separate integration tests.
contract EntryExecutionBudgetTest is PooledVaultFixture {
    function testHundredGrossWithNinetyNineLPActivates() public {
        venue.setSpendBps(9900);
        uint256 id = _mint(alice);
        _activate(alice, id, 100, 0);
        uint256 bucket = vault.nftBucket(id);
        assertEq(venue.a0(vault.group(bucket).lpTokenId), 99);
        assertEq(vault.group(bucket).idle0, 1);
        assertEq(vault.contributionUSD(id), 100e18);
        assertTrue(membership.eligible(id));
    }
    function testRoundingCannotDeployLessThanNinetyNinePercent() public {
        venue.setSpendBps(9900);
        uint256 id = _mint(alice);
        // Both zero-decimal tokens round 49.5 down to 49: only $98 is LP.
        vm.expectRevert(); _activate(alice, id, 50, 50);
        assertEq(uint256(vault.nftStatus(id)), uint256(PositionStatus.Dormant));
        assertEq(vault.sharesOf(id), 0); assertEq(vault.bucketCount(), 0);
    }
    function testLoosePoolSlippageCannotOverrideGlobalOnePercentLimit() public {
        PoolConfig memory c = pools.get(poolId); c.maxSlippageBps = 200; pools.set(poolId, c);
        uint256 id = _mint(alice); venue.setSpendBps(9800);
        t0.mint(address(vault), 1000); // Unattributed donations cannot pay the shortfall.
        vm.expectRevert(); _activate(alice, id, 1000, 0);
        assertEq(vault.sharesOf(id), 0); assertEq(t0.balanceOf(address(vault)), 1000);
        assertEq(t0.balanceOf(alice), 100000);
    }
    function testIncumbentIdleCannotSubsidizeNewNFTsExecutionBudget() public {
        venue.setSpendBps(9900);
        uint256 incumbent = activatedPosition(); uint256 bucket = vault.nftBucket(incumbent);
        uint256 originalShares = vault.sharesOf(incumbent);
        uint256 id = _mint(bob);
        vm.expectRevert(); _activate(bob, id, 100, 0);
        assertEq(vault.sharesOf(incumbent), originalShares);
        assertEq(vault.group(bucket).idle0 + vault.group(bucket).idle1, 20);
        assertEq(vault.sharesOf(id), 0); assertEq(membership.totalEligible(), 1);
    }
    function testLaterContributionsAlsoRequireNinetyNinePercentDeployed() public {
        venue.setSpendBps(10000); uint256 id = activatedPosition();
        venue.setSpendBps(9900);
        vm.prank(alice); vault.increase(id, 1000, 0, 1, block.timestamp + 100);
        assertEq(vault.contributionUSD(id), 3000e18);
        venue.setSpendBps(9800);
        vm.prank(alice); vm.expectRevert(); vault.increase(id, 1000, 0, 1, block.timestamp + 100);
        assertEq(vault.contributionUSD(id), 3000e18);
    }
}
