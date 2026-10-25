// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {Test} from "forge-std/Test.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationAssetsFactory} from "../src/ZZZActivationAssetsFactory.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {FakePermit2, FakeState, FakePolicy} from "./LiquidityEncoding.t.sol";
import {BoundaryWETH, BoundaryCore, BoundaryPositions, BoundaryForce, BoundaryOracle} from "./NativeLiquidity.t.sol";

/// @dev Real currency identity; settlement implementation below is the existing
/// deterministic fake, not evidence of a live Uniswap or Robinhood provider.
contract GenuineNativePools {
    PoolConfig private config;
    constructor(PoolConfig memory c) { config = c; }
    function get(bytes32 id) external view returns (PoolConfig memory) {
        require(id == keccak256(abi.encode(config.key))); return config;
    }
    function accounting(bytes32) external view returns (PoolConfig memory) { return config; }
    function isNativePool(bytes32 id) external view returns (bool) {
        require(id == keccak256(abi.encode(config.key))); return config.key.currency0 == address(0);
    }
    function disable() external { config.operationsEnabled = false; config.depositsEnabled = false; }
}

contract NativeCallbackToken is MockToken {
    address private forceTarget;
    constructor() MockToken(18) {}
    function forceDuringPull(address target) external { forceTarget = target; }
    function _update(address from, address to, uint256 amount) internal override {
        super._update(from, to, amount);
        if (from != address(0) && to == forceTarget) new BoundaryForce{value: 1}(payable(to));
    }
}

contract NativeAssetFoundationTest is Test {
    MockAccess private access;
    BoundaryWETH private brokenWrapper;
    NativeCallbackToken private token;
    FakePermit2 private permit;
    BoundaryCore private core;
    BoundaryPositions private positions;
    GenuineNativePools private pools;
    ZZZLiquidityManager private manager;
    bytes32 private poolId;
    bool private rejectETH;
    bool private tryReenter;

    receive() external payable {
        require(!rejectETH, "reject ETH");
        if (tryReenter) {
            (bool ok,) = address(manager).call(abi.encodeWithSignature("collect(bytes32,uint256,uint256)", poolId, 1, block.timestamp));
            require(!ok, "reentry succeeded");
        }
    }
    function setUp() public {
        vm.warp(10 days);
        access = new MockAccess(); brokenWrapper = new BoundaryWETH(); token = new NativeCallbackToken();
        brokenWrapper.failures(true, true);
        permit = new FakePermit2(); core = new BoundaryCore();
        positions = new BoundaryPositions(address(core), address(permit), address(brokenWrapper)); core.setPositions(address(positions));
        FakeState state = new FakeState(address(core));
        manager = new ZZZLiquidityManager(address(access), address(positions), address(state), address(core), address(permit));
        PoolConfig memory c; c.key = PoolKey(address(0), address(token), 10020, 60, address(0));
        c.operationsEnabled = true; c.maxSlippageBps = 200; poolId = keccak256(abi.encode(c.key));
        vm.mockCall(address(state), abi.encodeWithSignature("getSlot0(bytes32)", poolId),
            abi.encode(uint160(1 << 96), int24(0), uint24(0), uint24(10020)));
        pools = new GenuineNativePools(c);
        access.bind(Ids.VAULT, address(this)); access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.LIQUIDITY, address(manager)); access.bind(Ids.STRATEGY, address(new FakePolicy()));
        access.bind(Ids.ORACLE, address(new BoundaryOracle())); access.seal();
        vm.deal(address(this), 100 ether); vm.deal(address(core), 100 ether);
        token.mint(address(core), 100 ether); token.mint(address(this), 50 ether);
        token.approve(address(manager), type(uint256).max);
    }
    function _mint() private returns (uint256 id) {
        (id,,) = manager.mint{value: 10 ether}(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        positions.approve(address(manager), id);
    }
    function testNativeMintAndIncreaseReturnUnusedETHWithoutCallingBrokenWrapper() public {
        new BoundaryForce{value: 123}(payable(address(manager)));
        new BoundaryForce{value: 456}(payable(address(positions)));
        token.mint(address(manager), 789);
        uint256 beforeETH = address(this).balance;
        (uint256 id, uint256 spent0, uint256 spent1) = manager.mint{value: 10 ether}(
            poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH - spent0); assertGt(spent1, 0);
        positions.approve(address(manager), id);
        uint128 original = positions.getPositionLiquidity(id);
        (uint256 added0,) = manager.increase{value: 3 ether}(poolId, id, 3 ether, 3 ether, 1, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH - spent0 - added0);
        assertGt(positions.getPositionLiquidity(id), original);
        assertEq(address(manager).balance, 123); assertEq(address(positions).balance, 456);
        assertEq(token.balanceOf(address(manager)), 789);
        assertEq(token.allowance(address(manager), address(permit)), 0);
        assertEq(brokenWrapper.balanceOf(address(this)), 0); assertEq(brokenWrapper.balanceOf(address(manager)), 0);
    }
    function testNativeMissingOrExtraValueCannotUseForcedPrefund() public {
        new BoundaryForce{value: 20 ether}(payable(address(manager)));
        vm.expectRevert(); manager.mint(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        vm.expectRevert(); manager.mint{value: 10 ether + 1}(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(address(manager).balance, 20 ether); assertEq(positions.nextTokenId(), 1);
    }
    function testNativeERC20PullCannotInjectETHToReduceReportedNativeSpend() public {
        vm.deal(address(token), 1);
        token.forceDuringPull(address(manager));
        uint256 beforeETH = address(this).balance;
        vm.expectRevert(); manager.mint{value: 10 ether}(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH); assertEq(address(token).balance, 1);
        assertEq(address(manager).balance, 0); assertEq(positions.nextTokenId(), 1);
    }
    function testNativeCollectAndDisabledClosePayETHWithFailedWrapper() public {
        uint256 id = _mint(); positions.fees(id, 17, 29);
        new BoundaryForce{value: 123}(payable(address(manager))); token.mint(address(manager), 40);
        uint256 beforeETH = address(this).balance; uint256 beforeToken = token.balanceOf(address(this));
        manager.collect(poolId, id, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH + 17); assertEq(token.balanceOf(address(this)), beforeToken + 29);
        (uint256 principal0, uint256 principal1) = manager.amounts(id); pools.disable();
        manager.close(poolId, id, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH + 17 + principal0);
        assertEq(token.balanceOf(address(this)), beforeToken + 29 + principal1);
        assertEq(address(manager).balance, 123); assertEq(token.balanceOf(address(manager)), 40);
        assertEq(brokenWrapper.totalSupply(), 0);
    }
    function testNativeInputAndOutputSwapHaveExactBudgetsAndRetainPrefunds() public {
        new BoundaryForce{value: 123}(payable(address(manager)));
        uint256 beforeETH = address(this).balance; uint256 beforeToken = token.balanceOf(address(this));
        uint256 output = manager.swap{value: 1 ether}(poolId, true, 1 ether, 0.99 ether, block.timestamp + 100);
        assertEq(output, 0.99 ether); assertEq(token.balanceOf(address(this)), beforeToken + output);
        assertEq(address(this).balance, beforeETH - 1 ether);
        output = manager.swap(poolId, false, 1 ether, 0.99 ether, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH - 0.01 ether); assertEq(address(manager).balance, 123);
        vm.expectRevert(); manager.swap(poolId, true, 1 ether, 0.99 ether, block.timestamp + 100);
        vm.expectRevert(); manager.swap{value: 1}(poolId, false, 1 ether, 0.99 ether, block.timestamp + 100);
        assertEq(brokenWrapper.totalSupply(), 0);
    }
    function testNativePartialSettlementAndUnexpectedETHRevertAtomically() public {
        core.setPartial(true);
        uint256 beforeETH = address(this).balance;
        vm.expectRevert(); manager.swap{value: 1 ether}(poolId, true, 1 ether, 0.98 ether, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH);
        core.setPartial(false); core.forceTake(true);
        uint256 beforeToken = token.balanceOf(address(this));
        vm.expectRevert(); manager.swap(poolId, false, 1 ether, 0.98 ether, block.timestamp + 100);
        assertEq(token.balanceOf(address(this)), beforeToken); assertEq(address(this).balance, beforeETH);
    }
    function testNativeRejectedRecipientRollsBackAndReentryCannotCollectTwice() public {
        uint256 id = _mint(); positions.fees(id, 17, 29);
        rejectETH = true; vm.expectRevert(); manager.collect(poolId, id, block.timestamp + 100);
        assertEq(positions.nativeFees(id), 17); assertEq(positions.tokenFees(id), 29);
        rejectETH = false; tryReenter = true;
        uint256 beforeETH = address(this).balance; manager.collect(poolId, id, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH + 17); assertEq(positions.nativeFees(id), 0);
    }
    function testNativeRetainedPositionValueRevertsInsteadOfSubsidizingLaterLP() public {
        positions.retain(true);
        uint256 beforeETH = address(this).balance; uint256 beforeToken = token.balanceOf(address(this));
        vm.expectRevert(); manager.mint{value: 10 ether}(poolId, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(address(this).balance, beforeETH); assertEq(token.balanceOf(address(this)), beforeToken);
        assertEq(positions.nextTokenId(), 1);
    }
    function testNativeETHOracleAndSourceAdmissionAreDistinctFromWETH() public {
        ZZZOracle oracle = new ZZZOracle(address(access), address(0));
        access.bind(Ids.ORACLE, address(oracle));
        vm.expectRevert(); oracle.value(address(0), 1 ether);
        MockFeed nativeFeed = new MockFeed(8, 2000e8); MockFeed wrappedFeed = new MockFeed(8, 999e8);
        oracle.setTestFeed(address(0), address(nativeFeed), 1 hours);
        oracle.setTestFeed(address(brokenWrapper), address(wrappedFeed), 1 hours);
        assertEq(oracle.tokenDecimals(address(0)), 18); assertEq(oracle.value(address(0), 1 ether), 2000 ether);
        assertEq(oracle.value(address(brokenWrapper), 1 ether), 999 ether);
        ZZZActivationAssets assets = ZZZActivationAssets(ZZZActivationAssetsFactory(access.activationAssetsFactory()).create());
        vm.expectRevert(); assets.setAsset(address(0), true, bytes32(0), keccak256("review"));
        assets.setAsset(address(0), true, assets.NATIVE_ASSET_CODE_HASH(), keccak256("review"));
        assertEq(assets.value(address(0), 0.05 ether), 100 ether);
        assets.setAsset(address(0), false, bytes32(0), keccak256("disable"));
        vm.expectRevert(); assets.value(address(0), 1 ether);
        assertEq(assets.value(address(0), 0), 0);
        // A broken/expired native feed cannot be replaced by a wrapped-token price.
        nativeFeed.set(2000e8, block.timestamp, block.timestamp - 1 hours - 1);
        vm.expectRevert(); oracle.value(address(0), 1 ether);
    }
}
