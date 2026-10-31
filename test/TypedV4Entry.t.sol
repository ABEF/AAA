// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZProtocolPolicy} from "../src/interfaces/IZZZProtocolPolicy.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {BalanceDelta, BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZV4RouteExecutor} from "../src/ZZZV4RouteExecutor.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {FakePermit2, FakeState} from "./LiquidityEncoding.t.sol";
import {BoundaryWETH, BoundaryCore, BoundaryPositions, BoundaryForce} from "./NativeLiquidity.t.sol";
import {NativeFlowToken, NativeFlowRegistry} from "./NativeVaultFlows.t.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

/// @notice Actual v4 conversion and real Entry/Vault/Strategy/share accounting.
/// LP settlement/admission, prices and VRF remain explicit local substitutes;
/// this is not Robinhood market or external provider qualification.
contract TypedV4EntryTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    MockAccess private access;
    MockToken private source;
    NativeFlowToken private zzz;
    BoundaryWETH private brokenWrapper;
    BoundaryPositions private positions;
    NativeFlowRegistry private registry;
    ZZZActivationEntry private entry;
    ZZZVault private vault;
    ZZZNFT private nft;
    ZZZMembership private membership;
    MockVRF private vrf;
    PoolManager private conversionCore;
    StateView private conversionState;
    PoolKey private sourceETH;
    PoolKey private sourceZZZ;
    PoolKey private nativeZZZ;
    bytes32 private lpPool;
    bytes32 private toETH;
    bytes32 private toZZZ;
    bytes32 private nativeToZZZ;
    address private constant ALICE = address(0xA11CE);
    receive() external payable {}
    function activePlan(uint256) external pure returns (bytes32) { return bytes32(0); }

    function setUp() public {
        vm.warp(1_000_000); vm.deal(address(this), 10000000 ether); vm.deal(ALICE, 1000 ether);
        access = new MockAccess(); ProtocolPolicyFixture.bind(address(access)); source = new MockToken(18); zzz = new NativeFlowToken();
        brokenWrapper = new BoundaryWETH(); brokenWrapper.failures(true, true);
        ZZZOracle oracle = new ZZZOracle(address(access), address(0)); MockFeed feed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(0), address(feed), 1 hours); oracle.setTestFeed(address(zzz), address(feed), 1 hours);
        oracle.setTestFeed(address(source), address(feed), 1 hours); access.bind(Ids.ORACLE, address(oracle));
        registry = new NativeFlowRegistry(address(access), oracle, address(zzz)); entry = registry.activationEntry();
        // The generic local source stands for the fixed reviewed fixture ZZZ;
        // it is not a third user input. The LP pair remains a local substitute.
        registry.activationAssets().configureZZZ(address(source),address(source).codehash,
            keccak256("explicit reviewed fixture ZZZ identity, not stablecoin support"));
        BoundaryCore lpCore = new BoundaryCore(); FakePermit2 permit = new FakePermit2();
        positions = new BoundaryPositions(address(lpCore), address(permit), address(brokenWrapper)); lpCore.setPositions(address(positions));
        FakeState lpState = new FakeState(address(lpCore));
        ZZZLiquidityManager manager = new ZZZLiquidityManager(address(access), address(positions), address(lpState), address(lpCore), address(permit), address(new ZZZLPBalancer(address(access), address(lpCore), address(lpState))));
        vault = new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        nft = new ZZZNFT(address(access), "ipfs://typed-v4-entry-fixture/"); membership = new ZZZMembership(address(access));
        ZZZRewards rewards = new ZZZRewards(address(access)); ZZZFeeController fees = new ZZZFeeController(address(access));
        access.bind(Ids.VAULT, address(vault)); access.bind(Ids.NFT, address(nft)); access.bind(Ids.MEMBERSHIP, address(membership));
        access.bind(Ids.REWARDS, address(rewards)); access.bind(Ids.FEES, address(fees)); access.bind(Ids.POOLS, address(registry));
        access.bind(Ids.LIQUIDITY, address(manager)); access.bind(Ids.STRATEGY, address(new ZZZStrategy(address(access), address(new ZZZPortfolioPolicy(address(access))), address(new ZZZRebalanceConfirmation(address(access))))));
        access.bind(Ids.MIGRATION, address(this)); rewards.addAsset(address(zzz));
        vrf = new MockVRF(); ProtocolPolicyFixture.randomness(address(nft.access()),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        CanonicalFixture.bind(address(access)); access.seal();
        PoolConfig memory lp = registry.get(bytes32(0)); lpPool = keccak256(abi.encode(lp.key));
        vm.mockCall(address(lpState), abi.encodeWithSignature("getSlot0(bytes32)", lpPool),
            abi.encode(uint160(1 << 96), int24(0), uint24(0), uint24(10020)));
        vm.deal(address(lpCore), 10000 ether); zzz.mint(address(lpCore), 10000 ether); source.mint(ALICE, 1000 ether);
        conversionCore = new PoolManager(address(this)); conversionState = new StateView(IPoolManager(address(conversionCore)));
        source.mint(address(this), 10000000 ether); zzz.mint(address(this), 10000000 ether);
        sourceETH = PoolKey(address(0), address(source), 500, 10, address(0));
        nativeZZZ = PoolKey(address(0), address(zzz), 500, 10, address(0));
        sourceZZZ = address(source) < address(zzz)
            ? PoolKey(address(source), address(zzz), 500, 10, address(0))
            : PoolKey(address(zzz), address(source), 500, 10, address(0));
        _seed(sourceETH); _seed(sourceZZZ); _seed(nativeZZZ);
        toETH = entry.addV4Route(_policy(sourceETH, address(source), address(0)));
        toZZZ = entry.addV4Route(_policy(sourceZZZ, address(source), address(zzz)));
        nativeToZZZ = entry.addV4Route(_policy(nativeZZZ, address(0), address(zzz)));
    }
    function _coreKey(PoolKey memory key) private pure returns (CoreKey memory) {
        return CoreKey(Currency.wrap(key.currency0), Currency.wrap(key.currency1), key.fee, key.tickSpacing, IHooks(key.hooks));
    }
    function _seed(PoolKey memory key) private {
        conversionCore.initialize(_coreKey(key), uint160(1 << 96)); conversionCore.unlock(abi.encode(key));
    }
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == address(conversionCore)); PoolKey memory key = abi.decode(data, (PoolKey));
        (BalanceDelta delta,) = conversionCore.modifyLiquidity(_coreKey(key),
            ModifyLiquidityParams(-60000, 60000, 1000000 ether, bytes32(0)), "");
        _pay(key.currency0, delta.amount0()); _pay(key.currency1, delta.amount1()); return "";
    }
    function _pay(address asset, int128 delta) private {
        if (delta == 0) return; require(delta < 0); uint256 amount = uint256(-int256(delta));
        conversionCore.sync(Currency.wrap(asset));
        if (asset == address(0)) assertEq(conversionCore.settle{value: amount}(), amount);
        else { require(IERC20(asset).transfer(address(conversionCore), amount)); assertEq(conversionCore.settle(), amount); }
    }
    function _policy(PoolKey memory key, address input, address output) private view returns (ZZZV4RouteExecutor.Policy memory p) {
        p.source = input; p.output = output; p.key = key; p.poolManager = address(conversionCore); p.stateView = address(conversionState);
        p.sourceCodeHash = input == address(0) ? entry.v4Executor().NATIVE_ASSET_CODE_HASH() : input.codehash;
        p.outputCodeHash = output == address(0) ? entry.v4Executor().NATIVE_ASSET_CODE_HASH() : output.codehash;
        p.poolManagerCodeHash = address(conversionCore).codehash; p.stateViewCodeHash = address(conversionState).codehash;
        p.reviewHash = keccak256("actual local core, not production route qualification");
    }
    function _mint() private returns (uint256 id) {
        bytes32 reviewedPolicy1 = vault.mintPolicyFingerprint(); vm.prank(ALICE); id = vault.mintDormant{value: 0.05 ether}(reviewedPolicy1);
        vrf.fulfill(nft.requestOf(id), 0, 0); nft.finalizeTraits(id);
    }
    function _request(uint256 id, address input, uint256 amount, bytes32 route, bool increase)
        private view returns (ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id, lpPool, input, amount, route, amount * 99 / 100, 1, block.timestamp + 100, increase);
    }
    function _assertClean() private view {
        assertEq(address(entry).balance, 0); assertEq(address(entry.v4Executor()).balance, 0);
        assertEq(source.balanceOf(address(entry)), 0); assertEq(source.balanceOf(address(entry.v4Executor())), 0);
        assertEq(zzz.balanceOf(address(entry)), 0); assertEq(zzz.balanceOf(address(entry.v4Executor())), 0);
        assertEq(source.allowance(address(entry), address(entry.v4Executor())), 0);
        assertEq(zzz.allowance(address(entry), address(vault)), 0); assertEq(brokenWrapper.totalSupply(), 0);
    }

    function testActualV4SourceToNativeActivationAndSourceToZZZGrowthReachRealVault() public {
        uint256 id = _mint(); vm.prank(ALICE); source.approve(address(entry), 105 ether);
        bytes32 reviewedPolicy2 = IZZZProtocolPolicy(address(entry.access().protocolPolicy())).entryFingerprint(); vm.prank(ALICE); entry.executeReviewed(_request(id, address(source), 100 ether, toETH, false), 200,reviewedPolicy2);
        uint256 shares = vault.sharesOf(id); assertGt(shares, 0); assertTrue(membership.eligible(id));
        assertEq(vault.contributionUSD(id), 100 ether); assertEq(nft.ownerOf(id), ALICE);
        (bool available, uint256 value) = nft.currentLPValue(id); assertTrue(available); assertGe(value, 99 ether); _assertClean();
        bytes32 reviewedPolicy3 = IZZZProtocolPolicy(address(entry.access().protocolPolicy())).entryFingerprint(); vm.prank(ALICE); entry.executeReviewed(_request(id, address(source), 5 ether, toZZZ, true), 200,reviewedPolicy3);
        assertGt(vault.sharesOf(id), shares); assertEq(vault.contributionUSD(id), 105 ether);
        assertEq(vault.bucketCount(), 1); assertEq(source.allowance(ALICE, address(entry)), 0);
        (available, value) = nft.currentLPValue(id); assertTrue(available); assertGe(value, 103.95 ether); _assertClean();
    }
    function testRealVaultFailureAndConversionMinimumFailureRevertActualSwapAndUserFunds() public {
        uint256 id = _mint(); vm.prank(ALICE); source.approve(address(entry), 100 ether);
        ZZZActivationEntry.Request memory r = _request(id, address(source), 100 ether, toETH, false);
        uint256 beforeSource = source.balanceOf(ALICE); uint256 beforeETH = ALICE.balance;
        positions.retain(true); bytes32 reviewedPolicy4 = IZZZProtocolPolicy(address(entry.access().protocolPolicy())).entryFingerprint(); vm.prank(ALICE); vm.expectRevert(); entry.executeReviewed(r, 200,reviewedPolicy4);
        assertEq(source.balanceOf(ALICE), beforeSource); assertEq(ALICE.balance, beforeETH); assertEq(vault.sharesOf(id), 0);
        assertFalse(membership.eligible(id)); assertTrue(nft.traitsReady(id)); assertEq(nft.ownerOf(id), ALICE);
        assertEq(source.allowance(ALICE, address(entry)), 100 ether); _assertClean();
        (uint160 price,,,) = conversionState.getSlot0(PoolId.wrap(keccak256(abi.encode(sourceETH))));
        assertEq(price, uint160(1 << 96));
        positions.retain(false); r.minimumOut = 100 ether;
        bytes32 reviewedPolicy5 = IZZZProtocolPolicy(address(entry.access().protocolPolicy())).entryFingerprint(); vm.prank(ALICE); vm.expectRevert(); entry.executeReviewed(r, 200,reviewedPolicy5);
        assertEq(source.balanceOf(ALICE), beforeSource); assertEq(vault.sharesOf(id), 0); _assertClean();
        (price,,,) = conversionState.getSlot0(PoolId.wrap(keccak256(abi.encode(sourceETH)))); assertEq(price, uint160(1 << 96));
    }
    function testActualV4NativeInputToZZZUsesExactValueAndOriginalValueBudget() public {
        uint256 id = _mint(); uint256 beforeETH = ALICE.balance;
        ZZZActivationEntry.Request memory r = _request(id, address(0), 100 ether, nativeToZZZ, false);
        bytes32 reviewedPolicy6 = IZZZProtocolPolicy(address(entry.access().protocolPolicy())).entryFingerprint(); vm.prank(ALICE); entry.executeReviewed{value: 100 ether}(r, 200,reviewedPolicy6);
        assertEq(ALICE.balance, beforeETH - 100 ether); assertEq(vault.contributionUSD(id), 100 ether);
        assertGt(vault.sharesOf(id), 0); assertTrue(membership.eligible(id));
        (bool available, uint256 value) = nft.currentLPValue(id); assertTrue(available); assertGe(value, 99 ether); _assertClean();
    }
    function testNativeReviewedCapRejectsBeforeConversionAndReturnsValueAtomically() public {
        uint256 id=_mint();uint256 beforeETH=ALICE.balance;
        ZZZActivationEntry.Request memory request=_request(id,address(0),100 ether,nativeToZZZ,false);
        assertEq(vault.migrationBudget().contributionLossBps(),200);
        bytes32 reviewedPolicy7 = IZZZProtocolPolicy(address(entry.access().protocolPolicy())).entryFingerprint(); vm.prank(ALICE);vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        entry.executeReviewed{value:100 ether}(request,100,reviewedPolicy7);
        assertEq(ALICE.balance,beforeETH);assertEq(vault.sharesOf(id),0);
        assertFalse(membership.eligible(id));_assertClean();
        (uint160 price,,,)=conversionState.getSlot0(PoolId.wrap(keccak256(abi.encode(nativeZZZ))));
        assertEq(price,uint160(1<<96));
        vault.migrationBudget().setLossLimits(100,300);
        bytes32 reviewedPolicy8 = IZZZProtocolPolicy(address(entry.access().protocolPolicy())).entryFingerprint(); vm.prank(ALICE);entry.executeReviewed{value:100 ether}(request,100,reviewedPolicy8);
        assertEq(ALICE.balance,beforeETH-100 ether);assertGt(vault.sharesOf(id),0);_assertClean();
    }
}
