// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

// Copied into an isolated test directory by prepare-dollar-rehearsal.py.
// Never run or deploy as production source. Venue, prices, VRF and authority
// are fixture dependencies; these tests do not qualify the live Pons route.
import {AtomicActivationIntegrationTest} from "./AtomicActivationIntegration.t.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {PoolConfig} from "../src/libraries/ZZZTypes.sol";

contract DollarActivationRehearsalTest is AtomicActivationIntegrationTest {
    function _dollarRequest(uint256 id, uint256 amount, bool increase)
        private view returns (ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id, poolId, address(stable), amount, routeId,
            amount * 1e12 * 9900 / 10000, 1,
            block.timestamp + 100, increase);
    }
    function _dollarExecute(uint256 id, uint256 amount, bool increase) private {
        ZZZActivationEntry.Request memory request = _dollarRequest(id, amount, increase);
        vm.prank(alice); entry.execute(request);
    }
    function _dollarClean() private view {
        assertEq(stable.balanceOf(address(entry)), 0);
        assertEq(t0.balanceOf(address(entry)), 0);
        assertEq(stable.allowance(address(entry), address(router)), 0);
        assertEq(t0.allowance(address(entry), address(vault)), 0);
    }
    function testDollarActivationDeploysNinetyNineCentsAndSetsEligibility() public realIntegration {
        uint256 id = _mint(alice);
        _dollarExecute(id, 1e6, false);
        uint256 lp = vault.group(vault.nftBucket(id)).lpTokenId;
        assertEq(venue.a0(lp), 99e16);
        assertEq(vault.contributionUSD(id), 1e18);
        assertEq(vault.sharesOf(id), 99e16);
        assertEq(venue.ownerOf(lp), address(vault));
        assertTrue(membership.eligible(id));
        assertGt(nft.royaltyRewards().weightOf(id), 0);
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(vault.MINT_PRICE(), 0.05 ether);
        _dollarClean();
    }
    function testDollarBelowMinimumEntryRollsBack() public realIntegration {
        uint256 id = _mint(alice); uint256 before = stable.balanceOf(alice);
        vm.expectRevert(bytes4(keccak256("InvalidAmount()"))); _dollarExecute(id, 999999, false);
        assertEq(stable.balanceOf(alice), before); assertEq(vault.sharesOf(id), 0);
        assertEq(vault.bucketCount(), 0); assertFalse(membership.eligible(id));
        _dollarClean();
    }
    function testDollarDirectFloorSurvivesLowerPoolMinimum() public realIntegration {
        PoolConfig memory c = registry.get(poolId); c.minDepositUSD = 1; registry.configure(c);
        uint256 id = _mint(alice);
        vm.prank(alice); vm.expectRevert(bytes4(keccak256("InvalidAmount()")));
        vault.activate(id, poolId, 1e18 - 1, 0, 1, block.timestamp + 100);
        assertEq(vault.sharesOf(id), 0);
        venue.setSpendBps(9900);
        vm.prank(alice); vault.activate(id, poolId, 1e18, 0, 1, block.timestamp + 100);
        assertEq(venue.a0(vault.group(vault.nftBucket(id)).lpTokenId), 99e16);
    }
    function testDollarCombinedConversionAndDeploymentCannotExceedOnePercent() public realIntegration {
        uint256 id = _mint(alice); uint256 before = stable.balanceOf(alice);
        venue.setSpendBps(9900); // .99 conversion * .99 deployment = .9801 LP, rejected.
        vm.expectRevert(bytes4(keccak256("Slippage()"))); _dollarExecute(id, 1e6, false);
        assertEq(stable.balanceOf(alice), before); assertEq(vault.sharesOf(id), 0);
        assertEq(vault.bucketCount(), 0); _dollarClean();
    }
    function testDollarStableValueUsesOracleAndCeilingRawAmount() public realIntegration {
        uint256 id = _mint(alice);
        stableFeed.set(99999000, block.timestamp, block.timestamp);
        vm.expectRevert(bytes4(keccak256("InvalidAmount()"))); _dollarExecute(id, 1e6, false);
        uint256 amount = (1e18 * 1e6 + oracle.price(address(stable)) - 1) / oracle.price(address(stable));
        assertEq(amount, 1000011);
        _dollarExecute(id, amount, false);
        assertGe(vault.contributionUSD(id), 1e18); _dollarClean();
    }
    function testDollarTopUpKeepsSameSharedLPAndDoesNotAddMembership() public realIntegration {
        uint256 id = _mint(alice); _dollarExecute(id, 1e6, false);
        uint256 bucket = vault.nftBucket(id); uint256 lp = vault.group(bucket).lpTokenId;
        _dollarExecute(id, 1e6, true);
        assertEq(vault.group(bucket).lpTokenId, lp); assertEq(vault.bucketCount(), 1);
        assertEq(vault.contributionUSD(id), 2e18); assertEq(venue.a0(lp), 198e16);
        assertEq(membership.totalEligible(), 1); _dollarClean();
    }
    function testDollarTransferPreservesAccruedLPAndRoyaltyRights() public realIntegration {
        uint256 id = _mint(alice); _dollarExecute(id, 1e6, false);
        venue.setFees(1e18, 0); vault.collectFees(vault.nftBucket(id), block.timestamp + 100);
        uint256 owed = rewards.claimable(id, address(t0)); assertGt(owed, 0);
        ZZZRoyaltyRewards royalty = nft.royaltyRewards();
        uint256 weight = royalty.weightOf(id);
        (bool funded,) = payable(address(royalty)).call{value: 0.001 ether}(""); assertTrue(funded);
        assertEq(royalty.claimable(id, address(0)), 0.001 ether);
        vm.prank(alice); nft.transferFrom(alice, bob, id);
        assertEq(rewards.claimable(id, address(t0)), owed);
        assertEq(royalty.weightOf(id), weight);
        vm.prank(alice); vm.expectRevert(bytes4(keccak256("Unauthorized()"))); rewards.claim(id, address(t0));
        vm.prank(alice); vm.expectRevert(bytes4(keccak256("Unauthorized()"))); royalty.claim(id, address(0));
        vm.prank(bob); assertEq(rewards.claim(id, address(t0)), owed);
        uint256 before = bob.balance;
        vm.prank(bob); assertEq(royalty.claim(id, address(0)), 0.001 ether);
        assertEq(bob.balance, before + 0.001 ether);
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(royalty.claimable(id, address(0)), 0);
    }
    function testDollarWrongOwnerAndPauseStillReject() public realIntegration {
        uint256 id = _mint(alice);
        ZZZActivationEntry.Request memory r = _dollarRequest(id, 1e6, false);
        vm.prank(bob); vm.expectRevert(bytes4(keccak256("Unauthorized()"))); entry.execute(r);
        ac.setPaused(true);
        vm.expectRevert(bytes4(keccak256("Paused()"))); _dollarExecute(id, 1e6, false);
        assertEq(vault.sharesOf(id), 0); _dollarClean();
    }
    function testDollarConversionStillRequiresNonzeroMinimumOutput() public realIntegration {
        uint256 id = _mint(alice); ZZZActivationEntry.Request memory r = _dollarRequest(id, 1e6, false);
        r.minimumOut = 0;
        vm.prank(alice); vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); entry.execute(r);
        assertEq(vault.sharesOf(id), 0); _dollarClean();
    }
    function testDollarConstructorGuardRejectsRobinhoodMainnet() public realIntegration {
        vm.chainId(4663);
        vm.expectRevert(bytes("LOCAL_REHEARSAL_ONLY")); new ZZZMigrationBudget(address(ac));
        vm.expectRevert(bytes("LOCAL_REHEARSAL_ONLY"));
        new ZZZActivationEntry(address(ac), address(registry), address(assets));
    }
}
