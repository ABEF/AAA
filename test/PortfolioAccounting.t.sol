// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZCustodyValidation} from "../src/ZZZCustodyValidation.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "../src/libraries/ZZZTypes.sol";

contract PortfolioAccountingAccess {
    mapping(bytes32 => address) public module;
    uint8 public canonicalState;
    bool public paused;
    bool public lpExitStarted;
    function set(bytes32 id,address target) external { module[id] = target; }
    function setState(uint8 state) external { canonicalState = state; }
    function setPaused(bool value) external { paused = value; }
    function isSealed() external pure returns(bool) { return true; }
    function preparationActive() external pure returns(bool) { return false; }
    function governance() external view returns(address) { return module[Ids.MIGRATION]; }
    function canonicalHandoff() external view returns(address) { return module[Ids.CANONICAL]; }
}

contract PortfolioAccountingVault {
    Position private position;
    address public migrationBudget;
    uint256 public constant ACCOUNTING_VERSION = 6;
    function set(Position memory p,address budget) external { position = p; migrationBudget = budget; }
    function group(uint256) external view returns(Position memory) { return position; }
    function checkpoint(uint256 bucket,uint8 phase) external { ZZZMigrationBudget(migrationBudget).checkpoint(bucket,phase); }
    function assertIdle(uint256 bucket) external view { ZZZMigrationBudget(migrationBudget).assertIdle(bucket); }
    function nativeSender(address sender) external view returns(bool) {
        return ZZZMigrationBudget(migrationBudget).validateNativeSender(sender);
    }
    function bucketTotalShares(uint256) external pure returns(uint256) { return 1; }
    function canonicalChainId() external view returns(uint256) { return block.chainid; }
    function canonicalBarrier() external pure {}
    function sequence() external pure returns(uint256) { return 0; }
    function bucketCount() external pure returns(uint256) { return 0; }
}

contract PortfolioAccountingLiquidity {
    mapping(uint256 => uint256[2]) private principal;
    mapping(uint256 => uint256) public secondaryId;
    uint256 public activeSecondaryCount;
    address public positionOperator;
    uint256 public constant PORTFOLIO_VERSION = 2;
    function set(uint256 id,uint256 a0,uint256 a1) external { principal[id] = [a0,a1]; }
    function link(uint256 main,uint256 secondary) external {
        secondaryId[main] = secondary;
        activeSecondaryCount = secondary == 0 ? 0 : 1;
    }
    function setOperator(address operator) external { positionOperator = operator; }
    function amounts(uint256 id) external view returns(uint256,uint256) {
        return (principal[id][0],principal[id][1]);
    }
    function portfolioAmounts(uint256 id) external view returns(uint256,uint256) {
        uint256 second = secondaryId[id];
        return (principal[id][0]+principal[second][0],principal[id][1]+principal[second][1]);
    }
    function portfolioFingerprint(uint256 main) external view returns(bytes32) {
        return keccak256(abi.encode(main,secondaryId[main]));
    }
    function executionPortfolioFingerprint(uint256 main) external view returns(bytes32) {
        uint256 secondary = secondaryId[main];
        return keccak256(abi.encode(main,secondary,principal[main],principal[secondary]));
    }
}

contract PortfolioAccountingPools {
    PoolConfig private configuration;
    function set(PoolConfig memory c) external { configuration = c; }
    function accounting(bytes32) external view returns(PoolConfig memory) { return configuration; }
    function get(bytes32) external view returns(PoolConfig memory) { return configuration; }
}

contract PortfolioAccountingOracle {
    ZZZContributionPricing public contributionPricing;
    constructor(address access) { contributionPricing = new ZZZContributionPricing(access,address(this)); }
    function value(address,uint256 amount) external pure returns(uint256) { return amount; }
    function price(address) external pure returns(uint256) { return 1e18; }
    function tokenDecimals(address) external pure returns(uint8) { return 18; }
}

contract PortfolioAccountingPolicy {
    uint64 public revision = 1;
    bool private hybrid;
    function set(bool value) external { hybrid = value; ++revision; }
    // The real helper is per-pool. This fixture isolates the Budget's captured
    // revision and replacement/compound capability, not execution geometry.
    function enabled(bytes32) external view returns(bool) { return hybrid; }
}

contract PortfolioAccountingConfirmation {
    bool private poolSpecific;
    function usePoolSpecificHashes() external { poolSpecific = true; }
    function observationFingerprint(uint256,bytes32 pool) external view returns(bytes32) {
        return poolSpecific ? keccak256(abi.encode(pool)) : bytes32(uint256(7));
    }
}

contract PortfolioAccountingStrategy {
    address public portfolioPolicy;
    address public rebalanceConfirmation;
    constructor(address policy,address confirmation) { portfolioPolicy = policy; rebalanceConfirmation = confirmation; }
    function needsRebalance(uint256) external pure returns(bool) { return false; }
    function keeperRangeTarget(bytes32) external pure returns(uint16) { return 0; }
}

contract PortfolioAccountingRewards {
    function assetCount() external pure returns(uint256) { return 0; }
}

/// @notice Actual Pricing/Budget/Canonical bodies with typed bounded fixtures.
/// These tests prove ledger and lifecycle checks, not pool execution or providers.
contract PortfolioAccountingTest is Test {
    PortfolioAccountingAccess private access;
    PortfolioAccountingVault private vault;
    PortfolioAccountingLiquidity private liquidity;
    PortfolioAccountingPools private pools;
    PortfolioAccountingOracle private oracle;
    PortfolioAccountingPolicy private policy;
    ZZZContributionPricing private pricing;
    bytes32 private POOL;

    function setUp() public {
        access = new PortfolioAccountingAccess();
        vault = new PortfolioAccountingVault();
        liquidity = new PortfolioAccountingLiquidity();
        pools = new PortfolioAccountingPools();
        oracle = new PortfolioAccountingOracle(address(access));
        policy = new PortfolioAccountingPolicy();
        pricing = oracle.contributionPricing();
        PortfolioAccountingConfirmation confirmation = new PortfolioAccountingConfirmation();
        access.set(Ids.VAULT,address(vault)); access.set(Ids.LIQUIDITY,address(liquidity));
        access.set(Ids.POOLS,address(pools)); access.set(Ids.ORACLE,address(oracle));
        access.set(Ids.STRATEGY,address(new PortfolioAccountingStrategy(address(policy),address(confirmation))));
        access.set(Ids.MIGRATION,address(this)); access.set(Ids.CANONICAL,address(this));
        access.set(Ids.REWARDS,address(new PortfolioAccountingRewards()));
        PoolConfig memory c; c.operationsEnabled = true; c.key.currency1 = address(1);
        c.key.tickSpacing = 60; c.key.fee = 3000; pools.set(c); POOL = keccak256(abi.encode(c.key));
        _position(0,0,address(this));
    }

    function _position(uint256 idle0,uint256 idle1,address budget) private {
        vault.set(Position(POOL,1,idle0,idle1,100,1,0,PositionStatus.Active),budget);
    }
    function _legs(uint256 main,uint256 residual) private {
        liquidity.set(1,main,0); liquidity.set(2,0,residual); liquidity.link(1,residual == 0 ? 0 : 2);
    }
    function testAggregateNAVIncludesResidualButPhysicalAmountsRemainSeparate() public {
        _legs(60,40); _position(3,2,address(this));
        (uint256 deployed,uint256 idle) = pricing.nav(11);
        assertEq(deployed,100); assertEq(idle,5);
        (uint256 physical0,uint256 physical1) = liquidity.amounts(1);
        assertEq(physical0,60); assertEq(physical1,0);
    }
    function testMainFloorAcceptsExactSixtyWithoutForcingResidual() public {
        _legs(60,40); pricing.assertPortfolioUtilization(11,1e18,1e18,1e18,1e18);
        _legs(100,0); pricing.assertPortfolioUtilization(11,1e18,1e18,1e18,1e18);
    }
    function testMainFloorRejectsBelowSixtyAndCountsAttributedIdle() public {
        _legs(59,41);
        vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        pricing.assertPortfolioUtilization(11,1e18,1e18,1e18,1e18);
        _legs(60,40); _position(1,0,address(this));
        vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        pricing.assertPortfolioUtilization(11,1e18,1e18,1e18,1e18);
    }
    function testMainFloorRoundsRequiredValueUp() public {
        _legs(60002,40003);
        vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        pricing.assertPortfolioUtilization(11,1e18,1e18,1e18,1e18);
        _legs(60003,40002); pricing.assertPortfolioUtilization(11,1e18,1e18,1e18,1e18);
    }
    function testMaintenanceCapabilityExcludesCompoundingAndEmergency() public {
        _legs(60,40);
        ZZZMigrationBudget replacement = new ZZZMigrationBudget(address(access));
        _position(0,0,address(replacement));
        assertEq(replacement.maintenanceBucket(),0);
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector); replacement.maintenancePrices();
        vault.checkpoint(11,0); assertEq(replacement.maintenanceBucket(),11);
        (uint256 price0,uint256 price1,uint256 scale0,uint256 scale1) = replacement.maintenancePrices();
        assertEq(price0,1e18); assertEq(price1,1e18); assertEq(scale0,1e18); assertEq(scale1,1e18);

        ZZZMigrationBudget compound = new ZZZMigrationBudget(address(access));
        _position(0,0,address(compound)); vm.warp(2 hours);
        vault.checkpoint(11,3); assertEq(compound.maintenanceBucket(),0);
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector); compound.maintenancePrices();

        ZZZMigrationBudget emergency = new ZZZMigrationBudget(address(access));
        _position(0,0,address(emergency)); access.setPaused(true);
        emergency.beginEmergency(11,4); vault.checkpoint(11,0);
        assertEq(emergency.maintenanceBucket(),0);
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector); emergency.maintenancePrices();
    }
    function testCapturedPolicyChangeAbortsMaintenance() public {
        _legs(60,40);
        ZZZMigrationBudget budget = new ZZZMigrationBudget(address(access));
        _position(0,0,address(budget)); vault.checkpoint(11,0); vault.checkpoint(11,1);
        policy.set(true);
        vm.expectRevert(ZZZMigrationBudget.InvalidState.selector); vault.checkpoint(11,2);
    }
    function testSamePairPoolMoveKeepsOriginalObservationControl() public {
        _legs(60,40);
        PortfolioAccountingStrategy strategy = PortfolioAccountingStrategy(access.module(Ids.STRATEGY));
        PortfolioAccountingConfirmation(strategy.rebalanceConfirmation()).usePoolSpecificHashes();
        ZZZMigrationBudget budget = new ZZZMigrationBudget(address(access));
        _position(0,0,address(budget)); vault.checkpoint(11,0); vault.checkpoint(11,1);
        // Same actual currencies and retained principal; changing only the
        // admitted pool must not compare the old sample to a foreign pool hash.
        vault.set(Position(bytes32(uint256(456)),1,0,0,100,1,0,PositionStatus.Active),address(budget));
        vault.checkpoint(11,2); assertEq(budget.maintenanceBucket(),0);
    }
    function testStandaloneBudgetAuthorizesControllerVaultNotItsDeployer() public {
        _legs(60,40);
        ZZZMigrationBudget budget = new ZZZMigrationBudget(address(access));
        _position(0,0,address(budget));
        vm.expectRevert(ZZZMigrationBudget.Unauthorized.selector); budget.checkpoint(11,0);
        vault.checkpoint(11,0); assertEq(budget.maintenanceBucket(),11);
    }
    function testIdleAmountBoundRemainsAtomicBudgetRequirement() public {
        ZZZMigrationBudget budget = new ZZZMigrationBudget(address(access));
        _position(uint256(type(uint128).max)+1,0,address(budget));
        vm.expectRevert(ZZZMigrationBudget.InvalidAmount.selector); vault.assertIdle(11);
    }
    function testNativePrincipalCreditAcceptsOnlyFixedManagerAndOperator() public {
        ZZZMigrationBudget budget = new ZZZMigrationBudget(address(access));
        _position(0,0,address(budget)); liquidity.setOperator(address(0xABCD));
        assertTrue(vault.nativeSender(address(liquidity))); assertTrue(vault.nativeSender(address(0xABCD)));
        access.set(Ids.FEES,address(0xFEE)); assertFalse(vault.nativeSender(address(0xFEE)));
        vm.expectRevert(ZZZMigrationBudget.Unauthorized.selector); vault.nativeSender(address(0xBAD));
    }
    function testReplacementEnforcesUtilizationAfterUnchangedRetainedNAV() public {
        policy.set(true); _legs(59,41);
        ZZZMigrationBudget budget = new ZZZMigrationBudget(address(access));
        _position(0,0,address(budget)); vault.checkpoint(11,0); vault.checkpoint(11,1);
        vm.expectRevert(ZZZContributionPricing.Slippage.selector); vault.checkpoint(11,2);
        _legs(60,40); vault.checkpoint(11,2);
        assertEq(budget.maintenanceBucket(),0);
    }
    function testStandaloneCompoundDoesNotEnforceReplacementOnlyMainFloor() public {
        policy.set(true); _legs(20,80);
        ZZZMigrationBudget budget = new ZZZMigrationBudget(address(access));
        _position(0,0,address(budget)); vm.warp(2 hours);
        vault.checkpoint(11,3); vault.checkpoint(11,1); vault.checkpoint(11,2);
        assertEq(budget.maintenanceBucket(),0);
    }
    function testCanonicalV5RejectsLiveResidualEvenWithoutListedBuckets() public {
        ZZZVaultCanonical canonical = new ZZZVaultCanonical(address(access),address(vault),block.chainid);
        access.setState(1); _legs(60,40);
        vm.expectRevert(ZZZVaultCanonical.InvalidState.selector); canonical.canonicalCapture();
        liquidity.link(1,0); canonical.canonicalCapture();
    }
    function testCanonicalActivationRejectsLiveResidual() public {
        ZZZVaultCanonical canonical = new ZZZVaultCanonical(address(access),address(vault),block.chainid);
        access.setState(2); _legs(60,40);
        vm.expectRevert(ZZZVaultCanonical.InvalidState.selector); canonical.canonicalActivate();
        liquidity.link(1,0); canonical.canonicalActivate();
    }
    function parkingNonce(uint256) external pure returns(uint64) { return 0; }
    function custodyEpoch(uint256) external pure returns(uint64) { return 0; }
    function testParkingReviewBindsBothPhysicalIdentities() public {
        ZZZCustodyValidation validation = new ZZZCustodyValidation(address(access));
        _legs(60,40); access.setPaused(true);
        ZZZCustodyValidation.Parking memory request;
        request.bucketId = 11; request.poolId = POOL; request.lpTokenId = 1;
        request.totalShares = 1; request.depositUSD = 100; request.minimum0 = 1;
        request.token1 = address(1);
        request.deadline = block.timestamp+1; request.reviewHash = bytes32(uint256(1));
        request.portfolioHash = liquidity.executionPortfolioFingerprint(1);
        validation.validateParking(abi.encode(request));
        liquidity.link(1,3);
        vm.expectRevert(ZZZCustodyValidation.InvalidState.selector);
        validation.validateParking(abi.encode(request));
    }
}
