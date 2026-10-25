// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {BoundDummy, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

using DualOracleFixture for ZZZOracle;

/// @notice Actual Access/Registry/Assets/Oracle/Rewards/Migration/Buyback and
/// canonical companions. Unused economic core roles are explicit BoundDummy
/// fixtures. Configuration is exercised through Buyback's actual policy setter.
/// Governance is an immediate trusted wallet, not a delay or generic executor;
/// changing it does not automatically rotate guardian, keeper or mint recipient.
contract DirectGovernanceTest is Test {
    ZZZAccessController private access;
    ZZZPoolRegistry private pools;
    ZZZOracle private oracle;
    ZZZRewards private rewards;
    ZZZMigration private migration;
    ZZZBuyback private buyback;
    MockToken private zzz;
    address private constant GOVERNANCE = address(0x6007);
    address private constant KEEPER = address(0xBEEF);
    address private constant GUARDIAN = address(0x600D);
    address private constant STRANGER = address(0xBAD);
    address private constant NEXT = address(0x6008);
    bytes32 private constant REVIEW = keccak256("direct governance fixed ZZZ fixture");

    function setUp() public {
        vm.warp(1_000_000);
        access = new ZZZAccessController(GOVERNANCE, KEEPER, GUARDIAN);
        zzz = new MockToken(18);
        pools = new ZZZPoolRegistry(address(access));
        oracle = new ZZZOracle(address(access), address(0));
        rewards = new ZZZRewards(address(access));
        migration = new ZZZMigration(address(access));
        buyback = new ZZZBuyback(address(access), address(zzz), 1e30);
        access.bind(Ids.POOLS, address(pools)); access.bind(Ids.ORACLE, address(oracle));
        access.bind(Ids.REWARDS, address(rewards)); access.bind(Ids.MIGRATION, address(migration));
        access.bind(Ids.BUYBACK, address(buyback));
        MockFeed feed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(zzz), address(feed), 3600);
        rewards.addAsset(address(zzz));
        pools.activationAssets().configureZZZ(address(zzz), address(zzz).codehash, REVIEW);
        migration.configureZZZ(address(zzz), address(zzz).codehash, REVIEW);
        bytes32[7] memory unused = [Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.MEMBERSHIP,
            Ids.FEES,Ids.STRATEGY,Ids.COMPOUNDER];
        for (uint256 i; i < unused.length; ++i) access.bind(unused[i], address(new BoundDummy(address(access))));
        CanonicalFixture.bind(address(access));
    }

    function _seal() private { access.seal(); }
    function _setLimit(address caller, uint256 limit) private {
        vm.prank(caller); buyback.setOperatingTradeUSD(limit);
    }
    function _notice() private view returns (ZZZAccessController.PreparationNotice memory) {
        return ZZZAccessController.PreparationNotice(block.chainid, address(0xCA11),
            keccak256("non-executable local review notice"), REVIEW);
    }

    function testSelectedGovernanceConfiguresImmediatelyAfterSealAndBootstrapLosesAuthority() public {
        _setLimit(address(this), 4e18);
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(3e18);
        _seal();
        assertEq(access.GOVERNANCE_VERSION(), 2); assertEq(access.bootstrap(), address(0));
        uint256 at = block.timestamp;
        _setLimit(GOVERNANCE, 2e18);
        assertEq(buyback.operatingTradeUSD(), 2e18); assertEq(block.timestamp, at);
        vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(1e18);
        vm.prank(STRANGER); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(1e18);
        vm.prank(address(0)); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(1e18);
        assertEq(buyback.operatingTradeUSD(), 2e18);
    }

    function testGuardianMayPauseButCannotUnpauseConfigureOrReplaceGovernance() public {
        _seal();
        vm.prank(GUARDIAN); access.setPaused(true); assertTrue(access.paused());
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.setPaused(false);
        vm.prank(KEEPER); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.setPaused(true);
        vm.prank(GUARDIAN); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(0);
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.proposeGovernance(NEXT);
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.setKeeper(STRANGER, true);
        _setLimit(GOVERNANCE, 0); assertEq(buyback.operatingTradeUSD(), 0);
        vm.prank(GOVERNANCE); access.setPaused(false); assertFalse(access.paused());
        assertEq(access.governance(), GOVERNANCE); assertFalse(access.keepers(STRANGER));
    }

    function testTwoStepGovernancePreservesCurrentAuthoritySupportsCancellationAndRejectsWrongAcceptors() public {
        _seal();
        vm.prank(STRANGER); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.proposeGovernance(NEXT);
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); access.proposeGovernance(address(access));
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); access.proposeGovernance(GOVERNANCE);
        vm.prank(GOVERNANCE); access.proposeGovernance(NEXT);
        assertEq(access.governance(), GOVERNANCE); assertEq(access.pendingGovernance(), NEXT);
        _setLimit(GOVERNANCE, 5e18);
        vm.prank(STRANGER); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.acceptGovernance();
        vm.prank(GOVERNANCE); access.proposeGovernance(address(0));
        vm.prank(NEXT); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.acceptGovernance();
        vm.prank(address(0)); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.acceptGovernance();
        vm.prank(GOVERNANCE); access.proposeGovernance(NEXT);
        vm.prank(NEXT); access.acceptGovernance();
        assertEq(access.governance(), NEXT); assertEq(access.pendingGovernance(), address(0));
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(1e18);
        _setLimit(NEXT, 1e18); assertEq(buyback.operatingTradeUSD(), 1e18);
        assertTrue(access.keepers(KEEPER)); assertTrue(access.guardians(GUARDIAN));
    }

    function testZeroRolesAndControllerSelfGovernanceCannotCreateADeployment() public {
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        new ZZZAccessController(address(0), KEEPER, GUARDIAN);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        new ZZZAccessController(GOVERNANCE, address(0), GUARDIAN);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        new ZZZAccessController(GOVERNANCE, KEEPER, address(0));
        address predicted = vm.computeCreateAddress(address(this), vm.getNonce(address(this)));
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        new ZZZAccessController(predicted, KEEPER, GUARDIAN);
        assertEq(access.governance(), GOVERNANCE); assertFalse(access.isSealed());
    }

    function testRetiredTimelockSelectorsCannotExecuteScheduleOrGrantAuthority() public {
        _seal();
        bytes memory operation = abi.encodeCall(buyback.setOperatingTradeUSD, (0));
        bytes[] memory removed = new bytes[](4);
        removed[0] = abi.encodeWithSignature("schedule(address,uint256,bytes,bytes32,bytes32,uint256)",
            address(buyback), 0, operation, bytes32(0), bytes32(0), 0);
        removed[1] = abi.encodeWithSignature("execute(address,uint256,bytes,bytes32,bytes32)",
            address(buyback), 0, operation, bytes32(0), bytes32(0));
        removed[2] = abi.encodeWithSignature("grantRole(bytes32,address)", bytes32(0), STRANGER);
        removed[3] = abi.encodeWithSignature("updateDelay(uint256)", 0);
        for (uint256 i; i < removed.length; ++i) {
            vm.prank(GOVERNANCE); (bool ok,) = address(access).call(removed[i]);
            assertFalse(ok, "Removed executor selector remained callable");
        }
        assertEq(buyback.operatingTradeUSD(), 1e30);
        assertEq(access.governance(), GOVERNANCE); assertFalse(access.canConfigure(STRANGER));
        _setLimit(GOVERNANCE, 3e18); assertEq(buyback.operatingTradeUSD(), 3e18);
    }

    function testPreparationAndFrozenLifecycleBlockPendingGovernanceHandover() public {
        _seal();
        vm.prank(GOVERNANCE); access.proposeGovernance(NEXT);
        vm.prank(GOVERNANCE); access.startPreparation(_notice());
        vm.prank(NEXT); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.acceptGovernance();
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.proposeGovernance(address(0));
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(0);
        bytes32 noticeHash = access.preparationHash();
        vm.prank(GOVERNANCE); access.cancelPreparation(noticeHash);
        address handoff = access.canonicalHandoff();
        // Controller transition authorization is isolated here; the full
        // financial handoff suite exercises actual freeze and backing transfer.
        vm.prank(handoff); access.canonicalTransition(1, false, false);
        vm.prank(NEXT); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.acceptGovernance();
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.proposeGovernance(STRANGER);
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(0);
        assertEq(access.governance(), GOVERNANCE); assertEq(access.pendingGovernance(), NEXT);
        assertEq(buyback.operatingTradeUSD(), 1e30);
    }

    function testUnknownBindingsZeroModuleCallersAndTerminalRetirementCannotReopenConfiguration() public {
        address substitute = address(new BoundDummy(address(access)));
        bytes32 obsoleteBridge = keccak256("ZZZBridgeAdapter");
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); access.bind(obsoleteBridge, substitute);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); access.bind(bytes32(0), substitute);
        assertFalse(access.moduleAuthorized(obsoleteBridge, address(0)));
        _seal();
        address original = access.module(Ids.BUYBACK);
        vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.bind(Ids.BUYBACK, substitute);
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.bind(Ids.BUYBACK, substitute);
        assertEq(access.module(Ids.BUYBACK), original);
        assertFalse(access.moduleAuthorized(obsoleteBridge, address(0)));
        assertFalse(access.moduleAuthorized(Ids.BUYBACK, address(0)));
        address handoff = access.canonicalHandoff();
        vm.prank(STRANGER); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.canonicalTransition(3, false, true);
        vm.prank(handoff); access.canonicalTransition(3, false, true);
        vm.prank(GOVERNANCE); access.setPaused(false);
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZModule.Unauthorized.selector); buyback.setOperatingTradeUSD(0);
        vm.prank(GOVERNANCE); vm.expectRevert(ZZZAccessController.Unauthorized.selector); access.setKeeper(STRANGER, true);
        vm.prank(handoff); vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); access.canonicalTransition(0, false, true);
        assertEq(access.canonicalState(), 3); assertFalse(access.canConfigure(GOVERNANCE));
        assertFalse(access.moduleAuthorized(Ids.BUYBACK, original)); assertFalse(access.keeperAuthorized(KEEPER));
        assertEq(buyback.operatingTradeUSD(), 1e30);
    }
}
