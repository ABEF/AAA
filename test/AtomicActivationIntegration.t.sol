// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC721} from "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationEntry, IActivationV3Router} from "../src/ZZZActivationEntry.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed} from "./mocks/Mocks.sol";
import {PooledVaultFixture, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {EntryFactoryFixture, EntryPoolFixture} from "./ActivationEntry.t.sol";

/// @dev TEST ONLY: a typed SwapRouter02 boundary with deterministic 6-to-18
/// decimal output and optional transfer callback. This is not live routing,
/// executable market pricing or evidence of actual Robinhood liquidity.
contract AtomicIntegrationRouter is IActivationV3Router {
    address public immutable factory;
    uint256 public outputBps = 9900;
    IERC721 public callbackNFT;
    uint256 public callbackId;
    address public callbackFrom;
    address public callbackTo;
    constructor(address selectedFactory) { factory = selectedFactory; }
    function setOutputBps(uint256 bps) external { outputBps = bps; }
    function transferNFTDuringSwap(IERC721 nft, uint256 id, address from, address to) external {
        callbackNFT = nft; callbackId = id; callbackFrom = from; callbackTo = to;
    }
    function exactInputSingle(ExactInputSingleParams calldata p) external payable returns (uint256 out) {
        require(msg.value == 0 && p.sqrtPriceLimitX96 == 0 && p.fee == 500, "unexpected typed route");
        require(IERC20(p.tokenIn).transferFrom(msg.sender, address(this), p.amountIn));
        out = p.amountIn * 1e12 * outputBps / 10000;
        require(out >= p.amountOutMinimum, "insufficient conversion output");
        require(IERC20(p.tokenOut).transfer(p.recipient, out));
        if (address(callbackNFT) != address(0)) callbackNFT.transferFrom(callbackFrom, callbackTo, callbackId);
    }
}

/// @notice Real Vault/Registry-created Entry/Assets/Oracle/reward ownership
/// integration. LP custody/math and V3 execution are deliberately mocked.
/// The fixture MockAccess permits post-seal rebinding ONLY for test assembly;
/// production uses immutable sealed modules and the actual governance timelock.
contract AtomicActivationIntegrationTest is PooledVaultFixture {
    ZZZPoolRegistry registry;
    ZZZActivationAssets assets;
    ZZZActivationEntry entry;
    MockToken stable;
    MockFeed stableFeed;
    EntryFactoryFixture factory;
    EntryPoolFixture conversionPool;
    AtomicIntegrationRouter router;
    bytes32 routeId;
    bytes32 constant REVIEW = keccak256("internal atomic integration fixture, not independent approval");
    event Activated(uint256 indexed nftId, address indexed owner, bytes32 indexed poolId, uint256 amount0, uint256 amount1);

    // Foundry first runs the inherited, non-virtual PooledVaultFixture.setUp.
    // This modifier then assembles the real Registry/Entry integration for each
    // test without changing the shared fixture or its authority semantics.
    modifier realIntegration() { _integrationFixture(); _; }
    function _integrationFixture() private {
        // Replace only fixture dependencies; the Vault, NFT, Membership,
        // Oracle, Rewards and FeeController remain their real implementations.
        MockToken first = new MockToken(18); MockToken second = new MockToken(18);
        t0 = address(first) < address(second) ? first : second;
        t1 = address(first) < address(second) ? second : first;
        venue = new VaultLiquidityMock(address(t0), address(t1));
        ac.bind(Ids.LIQUIDITY, address(venue));
        MockFeed pairFeed = new MockFeed(8, 1e8);
        oracle.setFeed(address(t0), address(pairFeed), 3600);
        oracle.setFeed(address(t1), address(pairFeed), 3600);
        rewards.addAsset(address(t0)); rewards.addAsset(address(t1));
        registry = new ZZZPoolRegistry(address(ac)); ac.bind(Ids.POOLS, address(registry));
        assets = registry.activationAssets(); entry = registry.activationEntry();
        PoolConfig memory config = PoolConfig(PoolKey(address(t0), address(t1), 3000, 60, address(0)),
            true, true, 1000, 300, 100, 100, 600, 1e18, 1e30);
        poolId = registry.configure(config);
        assertEq(assets.policyCount(), 2);
        assertEq(entry.registry(), address(registry)); assertEq(address(entry.activationAssets()), address(assets));
        stable = new MockToken(6); stableFeed = new MockFeed(8, 1e8);
        oracle.setFeed(address(stable), address(stableFeed), 3600);
        assets.setAsset(address(stable), true, address(stable).codehash, REVIEW);
        factory = new EntryFactoryFixture(); router = new AtomicIntegrationRouter(address(factory));
        conversionPool = new EntryPoolFixture(address(factory), address(stable), address(t0)); factory.set(address(conversionPool));
        routeId = entry.addRoute(ZZZActivationEntry.RoutePolicy(address(stable), address(t0), address(router),
            address(factory), address(conversionPool), 500, address(router).codehash, address(factory).codehash,
            address(conversionPool).codehash, address(stable).codehash, address(t0).codehash, REVIEW));
        t0.mint(address(router), 100000e18);
        _fundIntegrationOwner(alice); _fundIntegrationOwner(bob);
    }
    function _fundIntegrationOwner(address owner) private {
        stable.mint(owner, 10000e6); t0.mint(owner, 10000e18); t1.mint(owner, 10000e18);
        vm.startPrank(owner);
        stable.approve(address(entry), type(uint256).max);
        t0.approve(address(vault), type(uint256).max); t1.approve(address(vault), type(uint256).max);
        vm.stopPrank();
    }
    function _request(uint256 id, bool increase) private view returns (ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id, poolId, address(stable), 100e6, routeId, 99e18, 1,
            block.timestamp + 100, increase);
    }
    function _execute(address owner, ZZZActivationEntry.Request memory request) private {
        vm.prank(owner); entry.execute(request);
    }
    function _cleanContextAndApprovals() private {
        assertEq(stable.balanceOf(address(entry)), 0); assertEq(t0.balanceOf(address(entry)), 0);
        assertEq(stable.allowance(address(entry), address(router)), 0);
        assertEq(t0.allowance(address(entry), address(vault)), 0);
        vm.prank(address(registry)); assertEq(entry.sourceValue(poolId, 99e18, 0), 0);
        vm.prank(address(vault)); assertEq(registry.contributionValue(poolId, 99e18, 0), 99e18);
    }
    function _assertDormantAndUnspent(uint256 id) private {
        assertEq(stable.balanceOf(alice), 10000e6); assertEq(stable.balanceOf(address(router)), 0);
        assertEq(vault.nftBucket(id), 0); assertEq(vault.sharesOf(id), 0); assertEq(vault.contributionUSD(id), 0);
        assertEq(uint256(vault.nftStatus(id)), uint256(PositionStatus.Dormant));
        assertFalse(membership.eligible(id)); assertEq(nft.royaltyRewards().weightOf(id), 0);
        assertEq(vault.bucketCount(), 0); assertEq(venue.next(), 1);
        assertEq(nft.ownerOf(id), alice); _cleanContextAndApprovals();
    }

    function testRealVaultActivationBindsHundredGrossToNinetyNineActualLPAndOwnerEvent() public realIntegration {
        uint256 id = _mint(alice);
        vm.expectEmit(true, true, true, true, address(vault)); emit Activated(id, alice, poolId, 99e18, 0);
        _execute(alice, _request(id, false));
        Position memory p = vault.group(vault.nftBucket(id));
        assertEq(venue.a0(p.lpTokenId), 99e18); assertEq(venue.a1(p.lpTokenId), 0);
        assertEq(vault.sharesOf(id), 99e18); assertEq(vault.contributionUSD(id), 100e18);
        assertEq(p.depositUSD, 100e18); assertEq(venue.ownerOf(p.lpTokenId), address(vault));
        assertEq(nft.ownerOf(id), alice); assertEq(nft.getApproved(id), address(0));
        assertFalse(nft.isApprovedForAll(alice, address(entry)));
        assertTrue(membership.eligible(id)); assertEq(membership.totalEligible(), 1);
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(stable.balanceOf(alice), 9900e6); _cleanContextAndApprovals();
    }
    function testOnePercentConversionPlusOnePercentDeploymentExceedsSharedBudgetAndRollsBack() public realIntegration {
        uint256 id = _mint(alice); venue.setSpendBps(9900);
        uint256 routeOutputBefore = t0.balanceOf(address(router));
        // Conversion alone delivers 99%; LP alone can deploy 99% (separate
        // direct-pair test). Together they would deploy only 98.01 USD.
        vm.expectRevert(); _execute(alice, _request(id, false));
        _assertDormantAndUnspent(id);
        assertEq(t0.balanceOf(address(router)), routeOutputBefore);
        assertEq(t0.balanceOf(address(venue)), 0); assertEq(t0.balanceOf(address(vault)), 0);
    }
    function testDirectPairPathKeepsItsOwnHundredGrossAndNinetyNinePercentFloor() public realIntegration {
        uint256 id = _mint(alice); uint256 original = t0.balanceOf(alice);
        vm.prank(alice); vm.expectRevert(); vault.activate(id, poolId, 99e18, 0, 1, block.timestamp + 100);
        assertEq(t0.balanceOf(alice), original); assertEq(vault.sharesOf(id), 0);
        venue.setSpendBps(9899);
        vm.prank(alice); vm.expectRevert(); vault.activate(id, poolId, 100e18, 0, 1, block.timestamp + 100);
        assertEq(t0.balanceOf(alice), original); assertEq(vault.sharesOf(id), 0);
        venue.setSpendBps(9900);
        vm.prank(alice); vault.activate(id, poolId, 100e18, 0, 1, block.timestamp + 100);
        Position memory p = vault.group(vault.nftBucket(id));
        assertEq(venue.a0(p.lpTokenId), 99e18); assertEq(p.idle0, 1e18);
        assertEq(vault.contributionUSD(id), 100e18); assertEq(p.depositUSD, 100e18);
        _cleanContextAndApprovals();
    }
    function testTopUpsUseOriginalSourceBudgetAndPreserveSingleLPAndMembership() public realIntegration {
        uint256 id = _mint(alice); _execute(alice, _request(id, false));
        uint256 bucket = vault.nftBucket(id); uint256 lp = vault.group(bucket).lpTokenId;
        _execute(alice, _request(id, true));
        assertEq(vault.group(bucket).lpTokenId, lp); assertEq(venue.a0(lp), 198e18);
        assertEq(vault.contributionUSD(id), 200e18); assertEq(vault.sharesOf(id), 198e18);
        assertEq(membership.totalEligible(), 1); assertEq(vault.bucketCount(), 1); assertEq(venue.next(), 2);
        uint256 stableBefore = stable.balanceOf(alice); uint256 venueBefore = t0.balanceOf(address(venue));
        venue.setSpendBps(9900);
        vm.expectRevert(); _execute(alice, _request(id, true));
        assertEq(stable.balanceOf(alice), stableBefore); assertEq(t0.balanceOf(address(venue)), venueBefore);
        assertEq(venue.a0(lp), 198e18); assertEq(vault.sharesOf(id), 198e18);
        assertEq(vault.contributionUSD(id), 200e18); _cleanContextAndApprovals();
    }
    function testActualRewardsAndSourceContributionRightsFollowCurrentNFTOwner() public realIntegration {
        uint256 id = _mint(alice); _execute(alice, _request(id, false));
        uint256 bucket = vault.nftBucket(id); venue.setFees(100e18, 0);
        vault.collectFees(bucket, block.timestamp + 100);
        // Personal index floors 80e18 * 1e36 / 99e18. Applying the
        // 99e18 shares yields 80e18 - 1 raw unit; collective 10e18 is exact.
        // The remaining unit stays backed in the ledger with fractional rights.
        uint256 expected = 90e18 - 1;
        assertEq(rewards.claimable(id, address(t0)), expected);
        vm.prank(alice); nft.transferFrom(alice, bob, id);
        vm.prank(alice); vm.expectRevert(); rewards.claim(id, address(t0));
        vm.expectRevert(); _execute(alice, _request(id, true));
        uint256 before = t0.balanceOf(bob); vm.prank(bob); assertEq(rewards.claim(id, address(t0)), expected);
        assertEq(t0.balanceOf(bob), before + expected);
        assertEq(rewards.liabilities(address(t0)), 1); assertEq(t0.balanceOf(address(rewards)), 1);
        _execute(bob, _request(id, true));
        assertEq(nft.ownerOf(id), bob); assertEq(nft.getApproved(id), address(0));
        assertEq(vault.contributionUSD(id), 200e18); assertEq(membership.totalEligible(), 1);
        _cleanContextAndApprovals();
    }
    function testNFTApprovalAndOperatorAuthorityCannotFundAnotherOwnersPosition() public realIntegration {
        uint256 id = _mint(alice);
        vm.startPrank(alice); nft.approve(bob, id); nft.setApprovalForAll(bob, true); vm.stopPrank();
        vm.expectRevert(); _execute(bob, _request(id, false));
        vm.prank(bob); vm.expectRevert(); vault.activate(id, poolId, 100e18, 0, 1, block.timestamp + 100);
        _assertDormantAndUnspent(id); assertEq(stable.balanceOf(bob), 10000e6);
    }
    function testConversionOwnershipChangeRollsBackSourceTokensAndNFTTransfer() public realIntegration {
        uint256 id = _mint(alice); vm.prank(alice); nft.approve(address(router), id);
        router.transferNFTDuringSwap(IERC721(address(nft)), id, alice, bob);
        vm.expectRevert(); _execute(alice, _request(id, false));
        _assertDormantAndUnspent(id); assertEq(nft.getApproved(id), address(router));
    }
    function testInactiveContextCannotAuthorizeSpoofedVaultCallerOrForgeGrossInput() public realIntegration {
        uint256 id = _mint(alice);
        vm.expectRevert(); entry.validateOwner(id, bytes32(0));
        vm.expectRevert(); entry.sourceValue(poolId, 100e18, 0);
        vm.prank(address(entry)); vm.expectRevert(); vault.activate(id, poolId, 100e18, 0, 1, block.timestamp + 100);
        vm.prank(address(vault)); vm.expectRevert(); entry.validateOwner(id, bytes32(0));
        vm.prank(address(vault)); assertEq(registry.contributionValue(poolId, 1e18, 0), 1e18);
        _assertDormantAndUnspent(id);
    }
    function testOriginalStableValueUsesRealOracleFeedInsteadOfAssumingOneDollar() public realIntegration {
        uint256 id = _mint(alice); stableFeed.set(98e6, block.timestamp, block.timestamp);
        assertEq(oracle.value(address(stable), 100e6), 98e18);
        vm.expectRevert(); _execute(alice, _request(id, false));
        _assertDormantAndUnspent(id);
    }
}
