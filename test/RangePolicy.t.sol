// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {Test} from "forge-std/Test.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {IStateViewMinimal} from "../src/interfaces/IZZZ.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
// TEST ONLY ERC20 admission; production permits only native ETH/ZZZ LP.
import {SyntheticPoolRegistry as ZZZPoolRegistry} from "./helpers/SyntheticPoolRegistry.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockFeed, BoundDummy} from "./mocks/Mocks.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

interface IRangeBinder { function bind(bytes32 id, address target) external; }
// Controlled position observations only. Real settlement/rights are covered by
// the selected-pool fork; this fixture does not pretend to execute Uniswap.
contract RangePolicyRecord is BoundDummy {
    Position private record;
    mapping(uint256 => int24[2]) private ranges;
    mapping(uint256 => bool) private known;
    uint160 private marketPrice = uint160(1<<96);
    int24 private marketTick;
    constructor(address controller) BoundDummy(controller) {}
    function set(Position memory p) external { record = p; }
    function group(uint256) external view returns (Position memory) { return record; }
    function setTicks(uint256 id, int24 lower, int24 upper) external { ranges[id] = [lower, upper]; known[id] = true; }
    function ticks(uint256 id) external view returns (int24, int24) {
        require(known[id], "missing position"); return (ranges[id][0], ranges[id][1]);
    }
    function setMarket(uint160 price,int24 tick) external { marketPrice=price;marketTick=tick; }
    function stateView() external view returns(IStateViewMinimal) { return IStateViewMinimal(address(this)); }
    function spot(bytes32) external view returns(uint160) { return marketPrice; }
    function getSlot0(bytes32) external view returns(uint160,int24,uint24,uint24) {
        return(marketPrice,marketTick,0,3000);
    }
}
contract RangeRewardAdmission is BoundDummy {
    constructor(address controller) BoundDummy(controller) {}
    function isAsset(address) external pure returns (bool) { return true; }
}
contract RangePolicyTest is Test {
    address controller;
    ZZZPoolRegistry registry;
    ZZZStrategy strategy;
    ZZZOracle oracle;
    RangePolicyRecord vault;
    RangePolicyRecord venue;
    MockToken t0; MockToken t1; MockFeed f0; MockFeed f1;
    PoolConfig config; Position position; bytes32 pool;
    uint256 constant BUCKET = 44;

    function setUp() public {
        vm.warp(1_000_000); MockAccess mock = new MockAccess(); ProtocolPolicyFixture.bind(address(mock));
        _system(address(mock)); mock.seal();
    }
    function _system(address access) private {
        controller = access; IRangeBinder binder = IRangeBinder(access);
        registry = new ZZZPoolRegistry(access); strategy = new ZZZStrategy(access, address(new ZZZPortfolioPolicy(access)), address(new ZZZRebalanceConfirmation(access)));
        oracle = new ZZZOracle(access, address(0)); vault = new RangePolicyRecord(access); venue = new RangePolicyRecord(access);
        binder.bind(Ids.POOLS, address(registry)); binder.bind(Ids.STRATEGY, address(strategy));
        binder.bind(Ids.ORACLE, address(oracle)); binder.bind(Ids.VAULT, address(vault));
        binder.bind(Ids.LIQUIDITY, address(venue)); binder.bind(Ids.REWARDS, address(new RangeRewardAdmission(access)));
        MockToken a = new MockToken(18); MockToken b = new MockToken(18);
        (t0, t1) = address(a) < address(b) ? (a, b) : (b, a);
        f0 = new MockFeed(8, 1e8); f1 = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(t0), address(f0), 1 days); oracle.setTestFeed(address(t1), address(f1), 1 days);
        config = PoolConfig(PoolKey(address(t0), address(t1), 3000, 200, address(0)),
            true, true, 5000, 500, 100, 100, 600, 100e18, 1e30);
        registry.activationAssets().configureZZZ(address(t1),address(t1).codehash,keccak256("range policy fixture ZZZ"));
        pool = registry.configure(config);
        position.poolId = pool; position.lpTokenId = 1; position.status = PositionStatus.Active;
        _replace();
    }
    function _replace() private {
        (int24 lower, int24 upper, uint160 center) = strategy.target(pool);
        ++position.lpTokenId; position.centerX96 = center; position.lastRebalance = uint64(block.timestamp);
        venue.setTicks(position.lpTokenId, lower, upper); vault.set(position);
    }
    function _width(uint16 width) private {
        config.rangeBps = width; config.triggerBps = width > 500 ? 500 : width - 1;
        config.maxSpotDeviationBps = width > 100 ? 100 : width - 1;
        registry.configure(config);
    }
    function _price(int256 price) private {
        f0.set(price, block.timestamp, block.timestamp); f1.set(1e8, block.timestamp, block.timestamp);
        uint160 root = oracle.referenceX96(address(t0),address(t1));
        venue.setMarket(root,TickMath.getTickAtSqrtPrice(root));
    }
    function testNarrowingWaitsForCooldownThenAppliesOnce() public {
        assertFalse(strategy.rangeUpdatePending(BUCKET)); _width(1000);
        assertTrue(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
        vm.warp(block.timestamp + 599); assertFalse(strategy.needsRebalance(BUCKET));
        vm.warp(block.timestamp + 1); assertTrue(strategy.needsRebalance(BUCKET));
        _replace(); assertFalse(strategy.rangeUpdatePending(BUCKET));
        vm.warp(block.timestamp + 600); assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testWideningAndReturningToDeployedPolicy() public {
        _width(1000); _replace(); vm.warp(block.timestamp + 600);
        _width(5000); assertTrue(strategy.rangeUpdatePending(BUCKET)); assertTrue(strategy.needsRebalance(BUCKET));
        _width(1000); assertFalse(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testMarketMoveInsidePhysicalRangeDoesNotCreateChurn() public {
        vm.warp(block.timestamp + 600); _price(101000000);
        assertFalse(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
        _price(110000000); assertFalse(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
        _price(160000000); assertTrue(strategy.needsRebalance(BUCKET));
        _replace(); vm.warp(block.timestamp + 600); assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testRoundedIdenticalTicksAndUnrelatedConfigurationDoNotRebalance() public {
        _width(1000); _replace(); vm.warp(block.timestamp + 600);
        _width(1001); assertFalse(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
        config.maxSlippageBps = 150; config.maxPositionUSD *= 2; registry.configure(config);
        assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testDisabledOperationsAndStaleOracleCannotBypassNormalEligibility() public {
        _width(1000); vm.warp(block.timestamp + 600);
        config.operationsEnabled = false; registry.configure(config);
        assertTrue(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
        config.operationsEnabled = true; registry.configure(config);
        f0.set(1e8, block.timestamp - 2 days, block.timestamp - 2 days);
        vm.expectRevert(); strategy.needsRebalance(BUCKET);
    }
    function testInactiveAndMissingIdentityCannotAuthorizeRebalance() public {
        _width(1000); vm.warp(block.timestamp + 600);
        for (uint8 i; i <= uint8(PositionStatus.Parked); ++i) {
            if (i == uint8(PositionStatus.Active)) continue;
            position.status = PositionStatus(i); vault.set(position);
            assertFalse(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
        }
        position.status = PositionStatus.Active; position.lpTokenId = 0; vault.set(position);
        assertFalse(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
        position.lpTokenId = 2; position.centerX96 = 0; vault.set(position);
        assertFalse(strategy.rangeUpdatePending(BUCKET)); assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testCurrentPhysicalPositionIsReadAndMalformedTicksFailClosed() public {
        _width(1000); vm.warp(block.timestamp + 600); assertTrue(strategy.needsRebalance(BUCKET));
        _replace(); vm.warp(block.timestamp + 600);
        venue.setTicks(position.lpTokenId - 1, 0, 0); assertFalse(strategy.needsRebalance(BUCKET));
        venue.setTicks(position.lpTokenId, 0, 0); vm.expectRevert(); strategy.rangeUpdatePending(BUCKET);
        vm.expectRevert(); strategy.needsRebalance(BUCKET);
    }
    function testFuzzAppliedWidthHasNoPersistentMismatch(uint16 requested) public {
        _width(uint16(bound(uint256(requested), 101, 5000))); _replace();
        assertFalse(strategy.rangeUpdatePending(BUCKET)); vm.warp(block.timestamp + 600);
        assertFalse(strategy.needsRebalance(BUCKET));
    }
    function testRealSealedGovernanceCanImmediatelyApproveRangeChange() public {
        ZZZAccessController access = new ZZZAccessController(address(0xA0A0), address(0x20), address(0x21)); ProtocolPolicyFixture.bind(address(access));
        _system(address(access));
        // The removed LP bridge/transport identities are intentionally unbindable.
        bytes32[6] memory rest = [Ids.NFT, Ids.MEMBERSHIP, Ids.FEES, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION];
        for (uint256 i; i < rest.length; ++i) access.bind(rest[i], address(new BoundDummy(address(access))));
        CanonicalFixture.bind(address(access)); access.seal();
        config.rangeBps = 1000;
        vm.expectRevert(); registry.configure(config); // Bootstrap has been revoked.
        vm.prank(address(0x20)); vm.expectRevert(); registry.configure(config); // Keeper has no configuration power.
        assertFalse(strategy.rangeUpdatePending(BUCKET));
        _price(1e8);
        vm.prank(access.governance()); registry.configure(config);
        assertTrue(strategy.rangeUpdatePending(BUCKET));
        // Immediate governance does not bypass the unchanged maintenance cooldown.
        assertFalse(strategy.needsRebalance(BUCKET));
        vm.warp(block.timestamp + 600); _price(1e8); assertTrue(strategy.needsRebalance(BUCKET));
        _replace(); vm.warp(block.timestamp + 600); assertFalse(strategy.needsRebalance(BUCKET));
    }
}
