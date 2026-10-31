// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken} from "./mocks/Mocks.sol";

contract ReserveVenueOracleFixture {
    bool private broken;
    function setBroken() external { broken = true; }
    function tokenDecimals(address) external pure returns (uint8) { return 18; }
    function price(address) external view returns (uint256) {
        if (broken) revert("unavailable fixture price");
        return 1e18;
    }
}
contract ReserveVenueRewardsFixture {
    bool public healthy = true;
    function setUnhealthy() external { healthy = false; }
    function isAsset(address) external view returns (bool) { return healthy; }
}
contract ReserveVenueExitFixture {
    uint8 public exitPhase;
    function setPhase(uint8 phase) external { exitPhase = phase; }
}

/// @dev TEST ONLY: override the hardcoded chain/runtime/wiring predicate. All
/// actual configureNative identity, phase, price, asset and configuration logic
/// remains inherited. Success here does not qualify Robinhood dependencies.
contract ReserveVenueRegistryFixture is ZZZPoolRegistry {
    constructor(address controller) ZZZPoolRegistry(controller) {}
    function _nativeBindings() internal pure override {}
}

contract PostExitReserveVenueTest is Test {
    address private constant ZZZ = 0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    address private constant STATE = 0xF3334192D15450CdD385c8B70e03f9A6bD9E673b;
    MockAccess private control;
    ReserveVenueRegistryFixture private registry;
    ReserveVenueOracleFixture private oracle;
    ReserveVenueRewardsFixture private rewards;
    ReserveVenueExitFixture private exit;
    PoolConfig private initial;
    bytes32 private pool;

    function setUp() public {
        control = new MockAccess(); ProtocolPolicyFixture.bind(address(control));
        registry = new ReserveVenueRegistryFixture(address(control));
        oracle = new ReserveVenueOracleFixture();
        rewards = new ReserveVenueRewardsFixture();
        exit = new ReserveVenueExitFixture();
        control.bind(Ids.POOLS, address(registry));
        control.bind(Ids.ORACLE, address(oracle));
        control.bind(Ids.REWARDS, address(rewards));
        control.bind(Ids.MIGRATION, address(exit));
        control.bind(Ids.VAULT, address(this));
        MockToken template = new MockToken(18);
        vm.etch(ZZZ, address(template).code);
        registry.activationAssets().configureZZZ(ZZZ, ZZZ.codehash, keccak256("synthetic reserve venue fixture"));
        initial.key = PoolKey(address(0), ZZZ, 500, 10, address(0));
        initial.depositsEnabled = true;
        initial.operationsEnabled = true;
        initial.rangeBps = 5000;
        initial.triggerBps = 100;
        initial.maxSpotDeviationBps = 300;
        initial.maxSlippageBps = 200;
        initial.minRebalanceInterval = 12 hours;
        initial.minDepositUSD = 100e18;
        initial.maxPositionUSD = 1_000_000e18;
        _slot(initial);
        pool = registry.configureNative(initial);
        control.seal();
    }
    function _slot(PoolConfig memory c) private {
        vm.mockCall(STATE, abi.encodeWithSignature("getSlot0(bytes32)", keccak256(abi.encode(c.key))),
            abi.encode(uint160(1 << 96), int24(0), uint24(0), c.key.fee));
    }
    function _start(uint8 phase) private {
        control.setPaused(true);
        control.startLPExit();
        exit.setPhase(phase);
    }
    function _reserve() private view returns (PoolConfig memory c) {
        c = initial;
        c.depositsEnabled = false;
    }
    function testOperatingAdmissionStillAllowsContributionPool() public view {
        assertEq(registry.contributionPool(), pool);
        assertTrue(registry.get(pool).depositsEnabled);
    }
    function testReadyCanRestoreDisabledReserveVenueWithoutReopeningContributions() public {
        _start(3);
        registry.disablePool(pool, true, true);
        uint64 beforeRevision = registry.configurationRevision();
        registry.configureNative(_reserve());
        assertTrue(registry.get(pool).operationsEnabled);
        assertFalse(registry.get(pool).depositsEnabled);
        assertEq(registry.contributionPool(), bytes32(0));
        assertEq(registry.configurationRevision(), beforeRevision + 1);
        assertTrue(control.lpExitStarted());
    }
    function testReadyCanAdmitDifferentFeeTierForRemainingReserve() public {
        _start(3);
        registry.disablePool(pool, true, true);
        PoolConfig memory c = _reserve();
        c.key.fee = 3000;
        c.key.tickSpacing = 60;
        _slot(c);
        bytes32 replacement = registry.configureNative(c);
        assertTrue(registry.exists(replacement));
        assertTrue(registry.get(replacement).operationsEnabled);
        assertFalse(registry.get(replacement).depositsEnabled);
        assertFalse(registry.get(pool).operationsEnabled);
        assertEq(registry.contributionPool(), bytes32(0));
        assertTrue(control.lpExitStarted());
    }
    function testClosingCannotConfigureEvenDepositsDisabled() public {
        _start(1);
        vm.expectRevert(ZZZModule.LPExitLocked.selector);
        registry.configureNative(_reserve());
    }
    function testAllocatingCannotConfigureEvenDepositsDisabled() public {
        _start(2);
        vm.expectRevert(ZZZModule.LPExitLocked.selector);
        registry.configureNative(_reserve());
    }
    function testReadyCannotEnableDeposits() public {
        _start(3);
        registry.disablePool(pool, true, true);
        vm.expectRevert(ZZZModule.LPExitLocked.selector);
        registry.configureNative(initial);
        assertFalse(registry.get(pool).depositsEnabled);
        assertFalse(registry.get(pool).operationsEnabled);
    }
    function testUnknownMigrationCannotAuthorizeTerminalConfiguration() public {
        _start(3);
        control.bind(Ids.MIGRATION, address(0x1234)); // MockAccess only; real bindings are sealed.
        vm.expectRevert();
        registry.configureNative(_reserve());
    }
    function testReadyConfigurationStillRequiresGovernance() public {
        _start(3);
        vm.prank(address(0xBEEF));
        vm.expectRevert(ZZZModule.Unauthorized.selector);
        registry.configureNative(_reserve());
    }
    function testPreparationStillBlocksGovernance() public {
        control.setPreparation(true);
        vm.expectRevert(ZZZModule.Unauthorized.selector);
        registry.configureNative(_reserve());
    }
    function testReadyStillRequiresFreshPricesAndRewardAssetAdmission() public {
        _start(3);
        oracle.setBroken();
        vm.expectRevert();
        registry.configureNative(_reserve());
        assertTrue(registry.get(pool).depositsEnabled); // Rejected writes are atomic.
    }
    function testReadyStillRequiresRewardAssetAdmission() public {
        _start(3);
        rewards.setUnhealthy();
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        registry.configureNative(_reserve());
    }
    function testReadyPreservesDisabledSourcePolicy() public {
        _start(3);
        ZZZActivationAssets assets = registry.activationAssets();
        bytes32 disabled = assets.setAsset(ZZZ, false, ZZZ.codehash, keccak256("disabled synthetic source"));
        registry.configureNative(_reserve());
        assertEq(assets.activePolicy(ZZZ), disabled);
        (address token, bool enabled,,,,) = assets.policies(disabled);
        assertEq(token, ZZZ);
        assertFalse(enabled);
    }
    function testFinalPhaseReadRollsBackConfigurationWhenNoLongerReady() public {
        _start(3);
        bytes[] memory phases = new bytes[](2);
        phases[0] = abi.encode(uint8(3));
        phases[1] = abi.encode(uint8(2));
        vm.mockCalls(address(exit), abi.encodeWithSignature("exitPhase()"), phases);
        uint64 beforeRevision = registry.configurationRevision();
        vm.expectRevert(ZZZModule.LPExitLocked.selector);
        registry.configureNative(_reserve());
        assertEq(registry.configurationRevision(), beforeRevision);
        assertTrue(registry.get(pool).depositsEnabled);
    }
    function testFinalTerminalReadRejectsExitStartingDuringAdmission() public {
        exit.setPhase(1);
        bytes[] memory flags = new bytes[](2);
        flags[0] = abi.encode(false);
        flags[1] = abi.encode(true);
        vm.mockCalls(address(control), abi.encodeWithSignature("lpExitStarted()"), flags);
        uint64 beforeRevision = registry.configurationRevision();
        vm.expectRevert(ZZZModule.LPExitLocked.selector);
        registry.configureNative(_reserve());
        assertEq(registry.configurationRevision(), beforeRevision);
    }
    function testFinalGovernanceReadStillRejectsLostAuthority() public {
        _start(3);
        bytes[] memory permitted = new bytes[](2);
        permitted[0] = abi.encode(true);
        permitted[1] = abi.encode(false);
        vm.mockCalls(address(control), abi.encodeWithSignature("canConfigure(address)", address(this)), permitted);
        uint64 beforeRevision = registry.configurationRevision();
        vm.expectRevert(ZZZModule.Unauthorized.selector);
        registry.configureNative(_reserve());
        assertEq(registry.configurationRevision(), beforeRevision);
    }
    function testConcreteProductionRegistryStillRejectsUnpinnedDependenciesAfterReady() public {
        ZZZPoolRegistry concrete = new ZZZPoolRegistry(address(control));
        control.beginBootstrap(); // Fixture setup only; production controller cannot unseal.
        concrete.activationAssets().configureZZZ(ZZZ, ZZZ.codehash, keccak256("fake token is not native qualification"));
        control.seal();
        _start(3);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        concrete.configureNative(_reserve());
        assertFalse(concrete.exists(pool));
    }
}
