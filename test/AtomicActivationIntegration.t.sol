// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC721} from "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {IV3RouteRouter} from "../src/interfaces/IZZZV3Route.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed} from "./mocks/Mocks.sol";
import {PooledVaultFixture, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {EntryFactoryFixture, EntryPoolFixture} from "./helpers/ActivationRouteFixture.sol";

/// @dev TEST ONLY: a typed SwapRouter02 boundary with deterministic 6-to-18
/// decimal output and optional transfer callback. This is not live routing,
/// executable market pricing or evidence of actual Robinhood liquidity.
contract AtomicIntegrationRouter is IV3RouteRouter {
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
/// production uses immutable sealed modules and the actual governance controller.
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
    modifier realIntegration() { _integrationFixture(false); _; }
    modifier directIntegration() { _integrationFixture(true); _; }
    function _integrationFixture(bool directSource) private {
        // This controller is intentionally a rebindable TEST mock. Assemble
        // these additional dependencies before its tested sealed phase; the
        // production AccessController has no unseal/bootstrap-reset function.
        ac.beginBootstrap();
        // This historical boundary suite deliberately exercises a stricter 1%
        // contribution policy; the production default is independently tested at 2%.
        vault.migrationBudget().setLossLimits(100,300);
        // Replace only fixture dependencies; the Vault, NFT, Membership,
        // Oracle, Rewards and FeeController remain their real implementations.
        // Keep actual constructor-created tokens sorted while the reviewed ZZZ
        // uses six decimals and the conversion output uses eighteen. The fixed
        // ZZZ is also a target-pair currency, never an unrelated source asset.
        uint256 nonce = vm.getNonce(address(this));
        bool outputFirst = vm.computeCreateAddress(address(this), nonce) <
            vm.computeCreateAddress(address(this), nonce + 1);
        if (outputFirst) { t0 = new MockToken(18); stable = new MockToken(6); }
        else { stable = new MockToken(6); t0 = new MockToken(18); }
        t1 = stable;
        require(address(t0) < address(t1), "fixture token order");
        venue = new VaultLiquidityMock(address(t0), address(t1));
        ac.bind(Ids.LIQUIDITY, address(venue));
        MockFeed pairFeed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(t0), address(pairFeed), 3600);
        oracle.setTestFeed(address(t1), address(pairFeed), 3600);
        rewards.addAsset(address(t0)); rewards.addAsset(address(t1));
        registry = new ZZZPoolRegistry(address(ac)); ac.bind(Ids.POOLS, address(registry));
        assets = registry.activationAssets(); entry = registry.activationEntry();
        // Historical variable name only: stable is this fixture's fixed ZZZ,
        // not a stablecoin accepted by the production source policy.
        stableFeed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(stable), address(stableFeed), 3600);
        MockToken reviewed = directSource ? t0 : stable;
        assets.configureZZZ(address(reviewed), address(reviewed).codehash, REVIEW);
        PoolConfig memory config = PoolConfig(PoolKey(address(t0), address(t1), 3000, 60, address(0)),
            true, true, 1000, 300, 100, 100, 600, 1e18, 1e30);
        poolId = registry.configure(config);
        assertEq(assets.policyCount(), 2);
        assertEq(entry.registry(), address(registry)); assertEq(address(entry.activationAssets()), address(assets));
        factory = new EntryFactoryFixture(); router = new AtomicIntegrationRouter(address(factory));
        conversionPool = new EntryPoolFixture(address(factory), address(stable), address(t0)); factory.set(address(conversionPool));
        if (!directSource) routeId = entry.addRoute(ZZZActivationEntry.RoutePolicy(address(stable), address(t0), address(router),
            address(factory), address(conversionPool), 500, address(router).codehash, address(factory).codehash,
            address(conversionPool).codehash, address(stable).codehash, address(t0).codehash, REVIEW));
        t0.mint(address(router), 100000e18);
        _fundIntegrationOwner(alice); _fundIntegrationOwner(bob);
        ac.seal();
    }
    function _fundIntegrationOwner(address owner) private {
        stable.mint(owner, 10000e6); t0.mint(owner, 10000e18);
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
        vm.prank(owner); entry.executeReviewed(request, 100);
    }
    function _cleanEntry() private {
        assertEq(stable.balanceOf(address(entry)), 0); assertEq(t0.balanceOf(address(entry)), 0);
        assertEq(t1.balanceOf(address(entry)), 0);
        assertEq(stable.allowance(address(entry), address(router)), 0);
        assertEq(t0.allowance(address(entry), address(vault)), 0);
        assertEq(t1.allowance(address(entry), address(vault)), 0);
        vm.prank(address(registry)); assertEq(entry.sourceValue(poolId, 99e18, 0), 0);
    }
    function _cleanContextAndApprovals() private {
        _cleanEntry();
        (,bool enabled,,,,)=assets.policies(assets.activePolicy(address(t0)));
        if (assets.isContributionAsset(address(t0)) && enabled) {
            vm.prank(address(vault)); assertEq(registry.contributionValue(poolId,99e18,0),99e18);
        } else {
            // Once the Entry context is disarmed, a target-pair currency is
            // not a permitted original source merely because it is accounted.
            vm.prank(address(vault));vm.expectRevert();registry.contributionValue(poolId,99e18,0);
        }
    }
    function _assertDormantAndUnspent(uint256 id) private {
        assertEq(stable.balanceOf(alice), 10000e6); assertEq(stable.balanceOf(address(router)), 0);
        assertEq(vault.nftBucket(id), 0); assertEq(vault.sharesOf(id), 0); assertEq(vault.contributionUSD(id), 0);
        assertEq(uint256(vault.nftStatus(id)), uint256(PositionStatus.Dormant));
        assertFalse(membership.eligible(id)); assertEq(nft.royaltyRewards().weightOf(id), 0);
        assertEq(vault.bucketCount(), 0); assertEq(venue.next(), 1);
        assertEq(nft.ownerOf(id), alice); _cleanContextAndApprovals();
    }

    function testFiveDollarConvertedTopUpRetainsNinetyNinePercentFloor() public realIntegration {
        uint256 id = _mint(alice); _execute(alice, _request(id, false));
        uint256 bucket = vault.nftBucket(id); uint256 lp = vault.group(bucket).lpTokenId;
        uint256 shares = vault.sharesOf(id); uint256 deployed = venue.a0(lp);
        ZZZActivationEntry.Request memory r = _request(id, true);
        r.amountIn = 5e6; r.minimumOut = 1;
        _execute(alice, r);
        assertEq(vault.contributionUSD(id), 105e18);
        assertEq(venue.a0(lp) - deployed, 4.95e18);
        assertGt(vault.sharesOf(id), shares); _cleanEntry();
        shares = vault.sharesOf(id); deployed = venue.a0(lp);
        uint256 balance = stable.balanceOf(alice);
        router.setOutputBps(9899);
        vm.prank(alice); vm.expectRevert(); entry.executeReviewed(r, 100);
        assertEq(vault.sharesOf(id), shares); assertEq(venue.a0(lp), deployed);
        assertEq(stable.balanceOf(alice), balance); assertEq(vault.contributionUSD(id), 105e18);
    }

    function testTopUpFloorUsesSourceUSDNotTokenCountOrStablePeg() public realIntegration {
        uint256 id = _mint(alice); _execute(alice, _request(id, false));
        ZZZActivationEntry.Request memory r = _request(id, true);
        r.minimumOut = 1; r.amountIn = 5e6 - 1;
        uint256 balance = stable.balanceOf(alice); uint256 shares = vault.sharesOf(id);
        vm.prank(alice); vm.expectRevert(); entry.executeReviewed(r, 100);
        assertEq(stable.balanceOf(alice), balance); assertEq(vault.sharesOf(id), shares);
        stableFeed.set(5e7, block.timestamp, block.timestamp);
        r.amountIn = 5e6;
        vm.prank(alice); vm.expectRevert(); entry.executeReviewed(r, 100);
        r.amountIn = 10e6; router.setOutputBps(4950);
        _execute(alice, r);
        assertEq(vault.contributionUSD(id), 105e18); _cleanEntry();
    }

    function testDirectVaultTopUpCannotBypassFiveDollarMinimum() public directIntegration {
        uint256 id = _mint(alice);
        vm.prank(alice);vault.activate(id,poolId,100e18,0,1,block.timestamp+100);
        uint256 balance = t0.balanceOf(alice); uint256 shares = vault.sharesOf(id);
        vm.prank(alice); vm.expectRevert(); vault.increase(id, 5e18 - 1, 0, 1, block.timestamp + 100);
        assertEq(t0.balanceOf(alice), balance); assertEq(vault.sharesOf(id), shares);
        vm.prank(alice); vault.increase(id, 5e18, 0, 1, block.timestamp + 100);
        assertEq(vault.contributionUSD(id), 105e18); assertGt(vault.sharesOf(id), shares);
    }

    function testGovernedPoolFloorCanTightenButCannotRelaxTopUpFloor() public realIntegration {
        uint256 id = _mint(alice); _execute(alice, _request(id, false));
        PoolConfig memory c = registry.get(poolId); c.minDepositUSD = 6e18; registry.configure(c);
        ZZZActivationEntry.Request memory r = _request(id, true); r.amountIn = 5e6; r.minimumOut = 1;
        vm.prank(alice); vm.expectRevert(); entry.executeReviewed(r, 100);
        c.minDepositUSD = 1; registry.configure(c);
        r.amountIn = 5e6 - 1;
        vm.prank(alice); vm.expectRevert(); entry.executeReviewed(r, 100);
        r.amountIn = 5e6; _execute(alice, r);
        uint256 dormant = _mint(alice); r.nftId = dormant; r.increase = false;
        vm.prank(alice); vm.expectRevert(); entry.executeReviewed(r, 100);
        assertEq(vault.nftBucket(dormant), 0); assertEq(vault.contributionUSD(id), 105e18);
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
    function testDirectPairPathKeepsItsOwnHundredGrossAndNinetyNinePercentFloor() public directIntegration {
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
        vm.prank(address(vault));vm.expectRevert();registry.contributionValue(poolId,1e18,0);
        _assertDormantAndUnspent(id);
    }
    function testOriginalZZZValueUsesRealOracleFeedInsteadOfAssumingOneDollar() public realIntegration {
        uint256 id = _mint(alice); stableFeed.set(98e6, block.timestamp, block.timestamp);
        assertEq(oracle.value(address(stable), 100e6), 98e18);
        vm.expectRevert(); _execute(alice, _request(id, false));
        _assertDormantAndUnspent(id);
    }
    function testDisabledOriginalSourceRejectsActivationAndTopUpWithoutChangingExistingPosition() public realIntegration {
        uint256 active = _mint(alice); _execute(alice, _request(active, false));
        uint256 dormant = _mint(alice); uint256 bucket = vault.nftBucket(active);
        uint256 lp = vault.group(bucket).lpTokenId;
        uint256 stableBefore = stable.balanceOf(alice); uint256 routeBefore = t0.balanceOf(address(router));
        bytes32 disabled = assets.setAsset(address(stable), false, bytes32(0), REVIEW);
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); _execute(alice, _request(dormant, false));
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); _execute(alice, _request(active, true));
        assertEq(stable.balanceOf(alice), stableBefore); assertEq(t0.balanceOf(address(router)), routeBefore);
        assertEq(vault.sharesOf(active), 99e18); assertEq(vault.contributionUSD(active), 100e18);
        assertEq(vault.group(bucket).lpTokenId, lp); assertEq(venue.a0(lp), 99e18);
        assertEq(vault.nftBucket(dormant), 0); assertEq(vault.sharesOf(dormant), 0);
        assertFalse(membership.eligible(dormant)); assertEq(nft.royaltyRewards().weightOf(dormant), 0);
        assertEq(membership.totalEligible(), 1); assertEq(vault.bucketCount(), 1); _cleanContextAndApprovals();

        // Same-token re-admission is permitted after sealing; token identity
        // itself is fixed and no replacement asset is introduced by this test.
        bytes32 enabled = assets.setAsset(address(stable),true,address(stable).codehash,REVIEW);
        assertTrue(enabled != disabled); (, bool oldEnabled,,,,) = assets.policies(disabled); assertFalse(oldEnabled);
        _execute(alice, _request(dormant, false));
        assertEq(vault.nftBucket(dormant), bucket); assertEq(vault.group(bucket).lpTokenId, lp);
        assertEq(vault.contributionUSD(dormant), 100e18); assertEq(membership.totalEligible(), 2);
        _cleanContextAndApprovals();
    }
    function testDisabledIntermediateRejectsDirectInputButPreservesAdmittedSourceRouteAndPolicyHistory() public realIntegration {
        bytes32 disabled = assets.setAsset(address(t0), false, bytes32(0), REVIEW);
        uint256 count = assets.policyCount();
        registry.configure(registry.get(poolId));
        assertEq(assets.activePolicy(address(t0)), disabled); assertEq(assets.policyCount(), count);
        (, bool enabled,,,,) = assets.policies(disabled); assertFalse(enabled);

        uint256 active = _mint(alice); _execute(alice, _request(active, false));
        _execute(alice, _request(active, true));
        uint256 bucket = vault.nftBucket(active); uint256 lp = vault.group(bucket).lpTokenId;
        assertEq(venue.a0(lp), 198e18); assertEq(vault.contributionUSD(active), 200e18);
        uint256 dormant = _mint(alice); uint256 before = t0.balanceOf(alice);
        vm.prank(alice); t0.approve(address(entry), 100e18);
        ZZZActivationEntry.Request memory direct = _request(dormant, false);
        direct.sourceAsset = address(t0); direct.amountIn = 100e18; direct.routeId = 0; direct.minimumOut = 0;
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); _execute(alice, direct);
        direct.nftId = active; direct.increase = true;
        vm.expectRevert(bytes4(keccak256("InvalidConfiguration()"))); _execute(alice, direct);
        vm.prank(alice); vm.expectRevert(bytes4(keccak256("InvalidConfiguration()")));
        vault.activate(dormant, poolId, 100e18, 0, 1, block.timestamp + 100);
        vm.prank(address(vault)); vm.expectRevert(bytes4(keccak256("InvalidConfiguration()")));
        registry.contributionValue(poolId, 100e18, 0);
        assertEq(t0.balanceOf(alice), before); assertEq(t0.allowance(alice, address(entry)), 100e18);
        assertEq(vault.nftBucket(dormant), 0); assertFalse(membership.eligible(dormant));
        assertEq(vault.sharesOf(active), 198e18); assertEq(venue.a0(lp), 198e18);
        assertEq(membership.totalEligible(), 1); assertEq(vault.bucketCount(), 1); _cleanEntry();
    }
    function testDisablingAllInputsAndRoutePreservesFundedLPAndRoyaltyRightsForNewOwner() public realIntegration {
        uint256 id = _mint(alice); _execute(alice, _request(id, false));
        ZZZRoyaltyRewards royalties = nft.royaltyRewards();
        uint256 bucket = vault.nftBucket(id); uint256 lp = vault.group(bucket).lpTokenId;
        venue.setFees(100e18, 0); vault.collectFees(bucket, block.timestamp + 100);
        uint256 owed = rewards.claimable(id, address(t0)); assertEq(owed, 90e18 - 1);
        (bool paid,) = address(royalties).call{value: 1 ether}(""); assertTrue(paid);
        uint256 royalty = royalties.claimable(id, address(0)); assertEq(royalty, 1 ether);
        uint256 weight = royalties.weightOf(id);

        assets.setAsset(address(stable), false, bytes32(0), REVIEW);
        assets.setAsset(address(0),false,assets.NATIVE_ASSET_CODE_HASH(),REVIEW);
        assets.setAsset(address(t0), false, bytes32(0), REVIEW);
        entry.setRouteEnabled(routeId, false);
        vm.prank(alice); nft.transferFrom(alice, bob, id);
        assertTrue(membership.eligible(id)); assertEq(membership.totalEligible(), 1);
        assertEq(royalties.weightOf(id), weight); assertEq(vault.sharesOf(id), 99e18);
        assertEq(vault.group(bucket).lpTokenId, lp); assertEq(venue.ownerOf(lp), address(vault));
        vm.prank(alice); vm.expectRevert(); rewards.claim(id, address(t0));
        vm.prank(alice); vm.expectRevert(); royalties.claim(id, address(0));
        uint256 tokenBefore = t0.balanceOf(bob); uint256 nativeBefore = bob.balance;
        vm.prank(bob); assertEq(rewards.claim(id, address(t0)), owed);
        vm.prank(bob); assertEq(royalties.claim(id, address(0)), royalty);
        assertEq(t0.balanceOf(bob), tokenBefore + owed); assertEq(bob.balance, nativeBefore + royalty);
        assertEq(rewards.claimable(id, address(t0)), 0); assertEq(royalties.claimable(id, address(0)), 0);
        assertEq(rewards.liabilities(address(t0)), 1); assertEq(t0.balanceOf(address(rewards)), 1);
        assertEq(royalties.liabilities(address(0)), 0);
        assertEq(vault.contributionUSD(id), 100e18); assertEq(venue.a0(lp), 99e18); _cleanEntry();
    }
}
