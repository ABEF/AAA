// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken} from "./mocks/Mocks.sol";

/// @dev Local source-admission substitutes only. These are not independent feeds
/// or qualification of Robinhood's live token, markets or venue dependencies.
contract NativeIdentityOracleFixture {
    function tokenDecimals(address) external pure returns (uint8) { return 18; }
    function price(address) external pure returns (uint256) { return 1e18; }
}
contract NativeIdentityRewardsFixture {
    function isAsset(address) external pure returns (bool) { return true; }
}

/// @notice Real Registry/Assets enforce the fixed source identity before native
/// runtime admission. Matching identity is insufficient to bypass venue pins;
/// this negative campaign never fabricates successful native qualification.
contract NativeSourceIdentityTest is Test {
    address private constant ZZZ = 0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    bytes32 private constant REVIEW = keccak256("local identity guard, not live token approval");
    MockAccess private access;
    ZZZPoolRegistry private registry;
    ZZZActivationAssets private assets;
    error IdentityReadReached();

    function setUp() public {
        vm.chainId(4663);
        access = new MockAccess();
        registry = new ZZZPoolRegistry(address(access));
        assets = registry.activationAssets();
        access.bind(Ids.POOLS, address(registry));
        access.bind(Ids.ORACLE, address(new NativeIdentityOracleFixture()));
        access.bind(Ids.REWARDS, address(new NativeIdentityRewardsFixture()));
    }
    function _config() private pure returns (PoolConfig memory c) {
        c.key = PoolKey(address(0), ZZZ, 10020, 200, address(0));
        c.depositsEnabled = true; c.operationsEnabled = true;
        c.rangeBps = 5000; c.triggerBps = 500;
        c.maxSpotDeviationBps = 100; c.maxSlippageBps = 200;
        c.minRebalanceInterval = 600;
        c.minDepositUSD = 100e18; c.maxPositionUSD = 1e30;
    }
    function _unchanged(PoolConfig memory c, uint256 policies) private view {
        assertFalse(registry.exists(keccak256(abi.encode(c.key))));
        assertEq(registry.contributionPool(), bytes32(0));
        assertEq(assets.policyCount(), policies);
    }
    function testUnsetSourceIdentityCannotAdmitNativePool() public {
        PoolConfig memory c = _config();
        assertEq(assets.zzz(), address(0));
        vm.expectCall(address(assets), abi.encodeWithSignature("zzz()"), uint64(1));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        registry.configureNative(c);
        _unchanged(c, 0);
    }
    function testWrongFixedSourceCannotAdmitNativePool() public {
        MockToken other = new MockToken(18);
        assets.configureZZZ(address(other), address(other).codehash, REVIEW);
        PoolConfig memory c = _config();
        assertEq(assets.zzz(), address(other));
        vm.expectCall(address(assets), abi.encodeWithSignature("zzz()"), uint64(1));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        registry.configureNative(c);
        _unchanged(c, 1);
    }
    function testSourceIdentityReadPrecedesNativeChainAndRuntimeChecks() public {
        // An early chain/runtime rejection would mask this distinct sentinel.
        // The actual source getter is otherwise unmocked in the other cases.
        vm.chainId(31337);
        vm.mockCallRevert(address(assets), abi.encodeWithSignature("zzz()"),
            abi.encodeWithSelector(IdentityReadReached.selector));
        vm.expectRevert(IdentityReadReached.selector);
        registry.configureNative(_config());
        _unchanged(_config(), 0);
    }
    function testMatchingSourceStillCannotBypassNativeRuntimePins() public {
        MockToken template = new MockToken(18);
        vm.etch(ZZZ, address(template).code);
        assets.configureZZZ(ZZZ, ZZZ.codehash, REVIEW);
        PoolConfig memory c = _config();
        assertEq(assets.zzz(), ZZZ);
        vm.expectCall(address(assets), abi.encodeWithSignature("zzz()"), uint64(1));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        registry.configureNative(c);
        // This fake token is intentionally not the pinned production runtime.
        _unchanged(c, 1);
    }
    function testGenericERC20AdmissionRejectsUnsetOrUnrelatedFixedZZZ() public {
        MockToken a = new MockToken(18); MockToken b = new MockToken(18);
        PoolConfig memory c = _config();
        (address first, address second) = address(a) < address(b)
            ? (address(a), address(b)) : (address(b), address(a));
        c.key = PoolKey(first, second, 10020, 200, address(0));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); registry.configure(c);
        _unchanged(c, 0);
        MockToken unrelated = new MockToken(18);
        assets.configureZZZ(address(unrelated), address(unrelated).codehash, REVIEW);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); registry.configure(c);
        _unchanged(c, 1);
    }
    function testGenericERC20AdmissionAllowsFixedZZZPairWithoutAddingThirdSource() public {
        MockToken a = new MockToken(18); MockToken b = new MockToken(18);
        assets.configureZZZ(address(a), address(a).codehash, REVIEW);
        PoolConfig memory c = _config();
        (address first, address second) = address(a) < address(b)
            ? (address(a), address(b)) : (address(b), address(a));
        c.key = PoolKey(first, second, 10020, 200, address(0));
        bytes32 id = registry.configure(c);
        assertTrue(registry.exists(id)); assertEq(registry.contributionPool(), id);
        assertEq(assets.zzz(), address(a));
        assertTrue(assets.isContributionAsset(address(a)));
        assertFalse(assets.isContributionAsset(address(b)));
    }
}
