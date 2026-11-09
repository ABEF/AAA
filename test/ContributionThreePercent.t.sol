// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture,VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {BudgetAdversarialVenue} from "./MigrationBudgetAdversarial.t.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {IZZZProtocolPolicy} from "../src/interfaces/IZZZProtocolPolicy.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @dev TEST ONLY native admission; all Registry accounting/source logic stays
/// real. The deterministic venue below does not qualify pinned Robinhood v4.
contract ContributionNativeRegistry is ZZZPoolRegistry {
    constructor(address controller) ZZZPoolRegistry(controller) {}
    function configureFixture(PoolConfig calldata config) external onlyGovernance principalOperating returns(bytes32) {
        if(config.key.currency0!=address(0) || config.key.currency1!=activationAssets.zzz() ||
            config.key.hooks!=address(0))revert InvalidConfiguration();
        return _configure(config,address(0),config.key.currency1);
    }
    function _nativeBindings() internal pure override {}
}

/// @notice Actual Vault/Pricing/Rewards accounting with a deterministic venue.
/// Native fixture units are normalized to $1 each, not real market/gas evidence.
/// This changes only the contribution budget; stricter venue guards remain.
contract ContributionThreePercentDefaultTest is PooledVaultFixture {
    function _assertPolicy() private view {
        assertEq(vault.migrationBudget().contributionLossBps(),300);
        assertEq(vault.migrationBudget().maintenanceLossBps(),300);
        assertEq(vault.migrationBudget().MAX_LOSS_BPS(),1000);
        assertEq(pools.get(poolId).maxSlippageBps,100,"fixture venue floor unchanged");
    }

    function testFreshDefaultChangesOnlyContributionBudget() public view {
        _assertPolicy();
    }

    function testActivationAcceptsExact97PercentDeployedWithFullyBackedIdle() public {
        _assertPolicy();venue.setSpendBps(9700);
        uint256 id=_mint(alice);uint256 before=alice.balance;
        _activate(alice,id,10000,0);
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        (uint256 deployed,uint256 idle)=vault.migrationBudget().nav(bucket);
        assertEq(venue.a0(p.lpTokenId),9700);assertEq(p.idle0,300);
        assertEq(deployed,9700e18);assertEq(idle,300e18);
        assertEq(deployed+idle,10000e18,"unused tokens remain principal, not loss");
        assertEq(vault.sharesOf(id),10000e18);assertEq(vault.contributionUSD(id),10000e18);
        assertEq(venue.ownerOf(p.lpTokenId),address(vault));
        assertEq(alice.balance,before-10000);assertTrue(membership.eligible(id));
        assertEq(membership.totalEligible(),1);assertGt(nft.royaltyRewards().weightOf(id),0);
        assertFalse(oracle.contributionPricing().active());_assertPolicy();
    }

    function testActivationBelow97PercentCannotBorrowDonationsAndRollsBackAllRights() public {
        _assertPolicy();venue.setSpendBps(9699);
        _giftNative(address(vault),1000);
        uint256 id=_mint(alice);uint256 before=alice.balance;
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,10000,0);
        assertEq(alice.balance,before);assertEq(address(vault).balance,1000);
        assertEq(vault.bucketCount(),0);assertEq(vault.nftBucket(id),0);
        assertEq(vault.sharesOf(id),0);assertEq(vault.contributionUSD(id),0);
        assertEq(uint256(vault.nftStatus(id)),uint256(PositionStatus.Dormant));
        assertFalse(membership.eligible(id));assertEq(membership.totalEligible(),0);
        assertEq(nft.royaltyRewards().weightOf(id),0);
        assertFalse(oracle.contributionPricing().active());_assertPolicy();
    }

    function testGrowthUsesMarginal97PercentWithoutRecentringOrBorrowingIncumbentIdle() public {
        _assertPolicy();uint256 id=_mint(alice);_activate(alice,id,10000,0);
        uint256 bucket=vault.nftBucket(id);Position memory original=vault.group(bucket);
        venue.setSpendBps(9700);
        vm.prank(alice);vault.increase{value:10000}(id,10000,0,1,block.timestamp+100);
        Position memory afterGrowth=vault.group(bucket);
        assertEq(afterGrowth.lpTokenId,original.lpTokenId);
        assertEq(afterGrowth.centerX96,original.centerX96);
        assertEq(afterGrowth.lastRebalance,original.lastRebalance);
        assertEq(venue.a0(afterGrowth.lpTokenId),19700);assertEq(afterGrowth.idle0,300);
        assertEq(vault.sharesOf(id),20000e18);assertEq(vault.contributionUSD(id),20000e18);
        // The incumbent's $300 idle cannot cover one missing entrant LP unit.
        venue.setSpendBps(9699);uint256 before=alice.balance;
        vm.prank(alice);vm.expectRevert(ZZZModule.Slippage.selector);
        vault.increase{value:10000}(id,10000,0,1,block.timestamp+100);
        Position memory rejected=vault.group(bucket);
        assertEq(alice.balance,before);assertEq(venue.a0(rejected.lpTokenId),19700);
        assertEq(rejected.idle0,300);assertEq(vault.totalIdle(address(0)),300);
        assertEq(vault.sharesOf(id),20000e18);assertEq(vault.contributionUSD(id),20000e18);
        assertEq(rejected.centerX96,original.centerX96);
        assertEq(rejected.lastRebalance,original.lastRebalance);
        assertEq(membership.totalEligible(),1);assertFalse(oracle.contributionPricing().active());
    }

    function testIndivisibleUnitRoundsUpRatherThanAcceptingLessThan97Percent() public {
        uint256 id=_mint(alice);uint256 before=alice.balance;
        // 97% of101 is97.97:97 whole fixture units is below the USD floor.
        venue.setSpendBps(9700);
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,101,0);
        assertEq(alice.balance,before);assertEq(vault.sharesOf(id),0);
        venue.setSpendBps(9703);_activate(alice,id,101,0);
        Position memory p=vault.group(vault.nftBucket(id));
        assertEq(venue.a0(p.lpTokenId),98);assertEq(p.idle0,3);
        assertEq(vault.sharesOf(id),101e18);assertEq(vault.contributionUSD(id),101e18);
    }

    function testExplicitGovernedTwoPercentRemainsStricterThanNewDefault() public {
        _assertPolicy();vault.migrationBudget().setLossLimits(200,300);
        uint256 id=_mint(alice);venue.setSpendBps(9700);
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,10000,0);
        assertEq(vault.nftBucket(id),0);assertFalse(membership.eligible(id));
        venue.setSpendBps(9800);_activate(alice,id,10000,0);
        Position memory p=vault.group(vault.nftBucket(id));
        assertEq(venue.a0(p.lpTokenId),9800);assertEq(p.idle0,200);
        assertEq(vault.migrationBudget().contributionLossBps(),200);
        assertEq(vault.migrationBudget().maintenanceLossBps(),300);
    }

    function testThreePercentBudgetDoesNotWidenExistingOnePercentVenueGuard() public {
        _assertPolicy();
        BudgetAdversarialVenue lossy=new BudgetAdversarialVenue(address(t0),address(t1));
        ac.bind(Ids.LIQUIDITY,address(lossy));lossy.losses(0,0,30,0);
        uint256 id=_mint(alice);uint256 before=alice.balance;
        // Actual97% retained LP would satisfy the contribution floor, but the
        // unchanged1% venue NAV floor requires99%; no idle conceals the loss.
        vm.expectRevert(ZZZModule.Slippage.selector);_activate(alice,id,1000,0);
        assertEq(alice.balance,before);assertEq(vault.sharesOf(id),0);
        assertEq(vault.bucketCount(),0);assertFalse(membership.eligible(id));_assertPolicy();
    }
}

/// @notice Direct Entry3 uses real source/policy/allowance checks with a fake LP
/// and explicit test-only native admission. No external fixture policy changes.
contract ContributionThreePercentEntryTest is PooledVaultFixture {
    using DualOracleFixture for ZZZOracle;
    ContributionNativeRegistry private registry;
    ZZZActivationEntry private entry;
    modifier entryFixture() {
        ac.beginBootstrap();
        t1=new MockToken(18);
        venue=new VaultLiquidityMock(address(0),address(t1));ac.bind(Ids.LIQUIDITY,address(venue));
        MockFeed feed=new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(feed),3600);oracle.setTestFeed(address(t1),address(feed),3600);
        t1.mint(alice,10000e18);
        registry=new ContributionNativeRegistry(address(ac));ac.bind(Ids.POOLS,address(registry));
        ZZZActivationAssets assets=registry.activationAssets();entry=registry.activationEntry();
        assets.configureZZZ(address(t1),address(t1).codehash,keccak256("TEST_ONLY_THREE_PERCENT_FIXED_ZZZ"));
        rewards=new ZZZRewards(address(ac));ac.bind(Ids.REWARDS,address(rewards));rewards.addAsset(address(t1));
        PoolConfig memory config=PoolConfig(PoolKey(address(0),address(t1),3000,60,address(0)),
            true,true,1000,300,100,100,600,1e18,1e30);
        poolId=registry.configureFixture(config);ac.seal();_;
    }
    function _request(uint256 id,bool grow) private view returns(ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id,poolId,address(t1),grow?5e18:100e18,1,block.timestamp+100,grow);
    }
    function _clean() private view {
        assertEq(address(entry).balance,0);assertEq(t1.balanceOf(address(entry)),0);
        assertEq(t1.allowance(address(entry),address(vault)),0);assertFalse(oracle.contributionPricing().active());
    }
    function _unspent(uint256 id,uint256 balance) private view {
        assertEq(t1.balanceOf(alice),balance);assertEq(vault.nftBucket(id),0);
        assertEq(vault.sharesOf(id),0);assertEq(vault.contributionUSD(id),0);
        assertFalse(membership.eligible(id));assertEq(nft.royaltyRewards().weightOf(id),0);
        assertEq(nft.ownerOf(id),alice);_clean();
    }
    function _submit(uint256 id,bool grow,uint16 maximum,bool reject) private {
        ZZZActivationEntry.Request memory request=_request(id,grow);
        bytes32 policyHash=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
        vm.startPrank(alice);t1.approve(address(entry),request.amountIn);
        if(reject)vm.expectRevert(ZZZModule.Slippage.selector);
        entry.executeReviewed(request,maximum,policyHash);vm.stopPrank();
    }

    function testSavedTwoPercentCallerMaximumRejectsBeforeTokenPull() public entryFixture {
        assertEq(vault.migrationBudget().contributionLossBps(),300);
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        _submit(id,false,200,true);_unspent(id,before);
        assertEq(t1.allowance(alice,address(entry)),100e18,"confirmed approval remains unused");
        assertEq(vault.bucketCount(),0);assertEq(registry.get(poolId).maxSlippageBps,100);
    }

    function testReviewedThreePercentAppliesToActivationAndFiveDollarGrowth() public entryFixture {
        assertEq(vault.migrationBudget().contributionLossBps(),300);
        uint256 id=_mint(alice);uint256 before=t1.balanceOf(alice);
        venue.setSpendBps(9699);_submit(id,false,300,true);_unspent(id,before);
        assertEq(t1.allowance(alice,address(entry)),100e18);
        venue.setSpendBps(9700);_submit(id,false,300,false);
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        assertEq(venue.a1(p.lpTokenId),97e18);assertEq(p.idle1,3e18);
        assertEq(vault.sharesOf(id),100e18);assertEq(vault.contributionUSD(id),100e18);_clean();
        uint256 beforeGrow=t1.balanceOf(alice);
        venue.setSpendBps(9699);_submit(id,true,300,true);
        assertEq(t1.balanceOf(alice),beforeGrow);assertEq(t1.allowance(alice,address(entry)),5e18);
        assertEq(vault.sharesOf(id),100e18);assertEq(vault.contributionUSD(id),100e18);
        assertEq(venue.a1(p.lpTokenId),97e18);assertEq(vault.group(bucket).idle1,3e18);_clean();
        venue.setSpendBps(9700);_submit(id,true,300,false);
        Position memory grown=vault.group(bucket);
        assertEq(venue.a1(p.lpTokenId),101.85e18);assertEq(grown.idle1,3.15e18);
        assertEq(vault.sharesOf(id),105e18);assertEq(vault.contributionUSD(id),105e18);
        assertEq(grown.lpTokenId,p.lpTokenId);assertEq(grown.centerX96,p.centerX96);
        assertEq(grown.lastRebalance,p.lastRebalance);assertEq(membership.totalEligible(),1);
        assertEq(vault.migrationBudget().maintenanceLossBps(),300);
        assertEq(registry.get(poolId).maxSlippageBps,100);_clean();
    }
}
