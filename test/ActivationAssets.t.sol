// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed, BoundDummy, TaxToken} from "./mocks/Mocks.sol";
import {ExactToken} from "../src/libraries/ExactToken.sol";

/// @dev TEST ONLY: immutable helper factory. Real Registry configuration adds
/// its own governance/pool validation before invoking admitPoolAsset.
contract ActivationRegistryFixture {
    IZZZAccess public immutable access;
    ZZZActivationAssets public immutable assets;
    constructor(address controller) {
        access = IZZZAccess(controller);
        assets = new ZZZActivationAssets(controller, address(this));
    }
    function admit(address token) external returns (bytes32) { return assets.admitPoolAsset(token); }
}

contract ActivationMetadataToken is ERC20 {
    uint8 private digits = 18;
    bool private fail;
    constructor() ERC20("Admission fixture", "AF") {}
    function configure(uint8 value, bool reject) external { digits = value; fail = reject; }
    function decimals() public view override returns (uint8) { require(!fail, "metadata unavailable"); return digits; }
}

/// @dev Admission does not replace the existing exact-transfer execution guard.
contract ActivationPullFixture {
    function pull(address token, uint256 amount) external { ExactToken.pull(token, msg.sender, amount); }
}

contract ActivationAssetsTest is Test {
    ZZZAccessController private access;
    ZZZOracle private oracle;
    ActivationRegistryFixture private registry;
    ZZZActivationAssets private assets;
    MockToken private token;
    MockFeed private feed;
    address private constant ATTACKER = address(0xBAD);
    address private constant GUARDIAN = address(0x600D);
    bytes32 private constant REVIEW = keccak256("internal governance review fixture; not external audit");

    function setUp() public {
        vm.warp(1000000);
        address[] memory auth = new address[](1); auth[0] = address(this);
        access = new ZZZAccessController(0, auth, auth, address(0xBEEF), GUARDIAN);
        oracle = new ZZZOracle(address(access), address(0));
        registry = new ActivationRegistryFixture(address(access)); assets = registry.assets();
        access.bind(Ids.ORACLE, address(oracle)); access.bind(Ids.POOLS, address(registry));
        token = new MockToken(6); feed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(token), address(feed), 1 days);
    }

    function _seal() private {
        bytes32[16] memory ids = [Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,
            Ids.STRATEGY,Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.BRIDGE,Ids.RECEIVER,Ids.ORACLE,
            Ids.POOLS,Ids.ROUTES,Ids.TRANSPORT];
        for (uint256 i; i < ids.length; ++i) {
            if (access.module(ids[i]) == address(0)) access.bind(ids[i], address(new BoundDummy(address(access))));
        }
        CanonicalFixture.bind(address(access));
        access.seal();
    }

    function _execute(bytes memory payload, bytes32 salt) private {
        access.schedule(address(assets), 0, payload, bytes32(0), salt, 0);
        feed.set(1e8, block.timestamp, block.timestamp);
        access.execute(address(assets), 0, payload, bytes32(0), salt);
    }

    function testImmutableRegistryAndInitialReviewedAdmission() public {
        assertEq(assets.registry(), address(registry)); assertEq(address(assets.access()), address(access));
        bytes32 id = assets.setAsset(address(token), true, address(token).codehash, REVIEW);
        assertEq(assets.activePolicy(address(token)), id); assertEq(assets.policyCount(), 1);
        assertEq(assets.policyAt(0), id); assertEq(assets.value(address(token), 100e6), 100e18);
        (address asset, bool enabled, bytes32 codeHash, bytes32 reviewHash, uint8 decimals, bool poolAdmission) = assets.policies(id);
        assertEq(asset, address(token)); assertTrue(enabled); assertEq(codeHash, address(token).codehash);
        assertEq(reviewHash, REVIEW); assertEq(decimals, 6); assertFalse(poolAdmission);
    }

    function testOnlyImmutableRegistryCanBootstrapPoolAssets() public {
        vm.prank(ATTACKER); vm.expectRevert(); assets.admitPoolAsset(address(token));
        vm.prank(address(this)); vm.expectRevert(); assets.admitPoolAsset(address(token));
        bytes32 id = registry.admit(address(token));
        (,,,,,bool poolAdmission) = assets.policies(id); assertTrue(poolAdmission);
        assertEq(assets.value(address(token), 1e6), 1e18);
        assertEq(registry.admit(address(token)), id); assertEq(assets.policyCount(), 1);
    }

    function testPoolReconfigurationNeverReenablesDisabledPolicyOrUpdatesOldPin() public {
        bytes32 first = registry.admit(address(token));
        bytes32 disabled = assets.setAsset(address(token), false, address(token).codehash, REVIEW);
        vm.etch(address(token), hex"fe");
        assertEq(registry.admit(address(token)), disabled); assertEq(assets.policyCount(), 2);
        assertEq(assets.policyAt(0), first); assertEq(assets.policyAt(1), disabled);
        vm.expectRevert(); assets.value(address(token), 1);
    }

    function testUnknownDisabledPolicyBlocksAutomaticPoolAdmissionWithoutDependencyReads() public {
        address futureToken = address(0xF0777);
        bytes32 id = assets.setAsset(futureToken, false, bytes32(0), REVIEW);
        assertEq(registry.admit(futureToken), id); assertEq(assets.policyCount(), 1);
        vm.expectRevert(); assets.value(futureToken, 1);
        assertEq(assets.value(futureToken, 0), 0);
    }

    function testDisabledBadTokenAndFailingPriceCanAlwaysBeRecorded() public {
        bytes32 pin = address(token).codehash; registry.admit(address(token));
        vm.mockCallRevert(address(feed), abi.encodeWithSignature("latestRoundData()"), hex"bad0");
        vm.etch(address(token), hex"fe");
        bytes32 id = assets.setAsset(address(token), false, pin, REVIEW);
        (,bool enabled,,,,) = assets.policies(id); assertFalse(enabled);
        assertEq(assets.value(address(token), 0), 0);
    }

    function testZeroInputSkipsAllAssetAndOracleDependencies() public {
        assertEq(assets.value(address(0), 0), 0); assertEq(assets.value(ATTACKER, 0), 0);
        registry.admit(address(token)); assets.setAsset(address(token), false, bytes32(0), REVIEW);
        vm.etch(address(oracle), hex"fe"); vm.etch(address(token), hex"fe");
        assertEq(assets.value(address(token), 0), 0);
    }

    function testDisableOneAssetLeavesAnotherSourceUsableAndDoesNotChangeOracleValuation() public {
        MockToken other = new MockToken(18); MockFeed secondFeed = new MockFeed(8, 2e8);
        oracle.setTestFeed(address(other), address(secondFeed), 1 days);
        registry.admit(address(token)); registry.admit(address(other));
        assets.setAsset(address(token), false, address(token).codehash, REVIEW);
        assertEq(assets.value(address(other), 5e18), 10e18);
        assertEq(oracle.value(address(token), 100e6), 100e18);
        vm.expectRevert(); assets.value(address(token), 100e6);
    }

    function testZeroAddressUnreviewedOrIncorrectPinCannotEnable() public {
        vm.expectRevert(); assets.setAsset(address(0), true, bytes32(uint256(1)), REVIEW);
        vm.expectRevert(); assets.setAsset(address(token), true, address(token).codehash, bytes32(0));
        vm.expectRevert(); assets.setAsset(address(token), true, bytes32(0), REVIEW);
        vm.expectRevert(); assets.setAsset(address(token), true, bytes32(uint256(1)), REVIEW);
        vm.expectRevert(); assets.setAsset(ATTACKER, true, ATTACKER.codehash, REVIEW);
        vm.expectRevert(); registry.admit(address(0)); assertEq(assets.policyCount(), 0);
    }

    function testMissingStaleOrZeroFeedCannotEnableOrAdmitNewSource() public {
        MockToken unknown = new MockToken(18);
        vm.expectRevert(); registry.admit(address(unknown));
        vm.warp(block.timestamp + 1 days + 1);
        vm.expectRevert(); assets.setAsset(address(token), true, address(token).codehash, REVIEW);
        feed.set(0, block.timestamp, block.timestamp);
        vm.expectRevert(); registry.admit(address(token)); assertEq(assets.policyCount(), 0);
    }

    function testBadMetadataAndOracleDecimalMismatchRejectNewSource() public {
        ActivationMetadataToken changed = new ActivationMetadataToken();
        oracle.setTestFeed(address(changed), address(feed), 1 days);
        changed.configure(19, false); vm.expectRevert(); registry.admit(address(changed));
        changed.configure(6, false); vm.expectRevert(); registry.admit(address(changed));
        changed.configure(18, true); vm.expectRevert(); registry.admit(address(changed));
        assertEq(assets.policyCount(), 0);
    }

    function testHistoryNeverOverwritesEvenWhenReturningToSameParameters() public {
        bytes32 pin = address(token).codehash;
        bytes32 first = assets.setAsset(address(token), true, pin, REVIEW);
        bytes32 second = assets.setAsset(address(token), false, pin, REVIEW);
        bytes32 third = assets.setAsset(address(token), true, pin, REVIEW);
        assertTrue(first != second && first != third && second != third); assertEq(assets.policyCount(), 3);
        (,bool oldEnabled,bytes32 oldPin,bytes32 oldReview,uint8 oldDecimals,) = assets.policies(first);
        assertTrue(oldEnabled); assertEq(oldPin, pin); assertEq(oldReview, REVIEW); assertEq(oldDecimals, 6);
        assertEq(assets.activePolicy(address(token)), third);
    }

    function testChangedRuntimeRequiresNewExplicitGovernanceReviewBeforeContributing() public {
        bytes32 first = registry.admit(address(token));
        MockToken replacement = new MockToken(18); vm.etch(address(token), address(replacement).code);
        vm.expectRevert(); assets.value(address(token), 100e6);
        assertEq(registry.admit(address(token)), first);
        vm.expectRevert(); assets.setAsset(address(token), true, address(replacement).codehash, REVIEW);
        // Reconfigure the feed to the reviewed changed token's current decimals.
        oracle.setTestFeed(address(token), address(feed), 1 days);
        bytes32 updated = assets.setAsset(address(token), true, address(replacement).codehash, keccak256("new internal review"));
        assertTrue(updated != first); assertEq(assets.value(address(token), 1e18), 1e18);
    }

    function testOracleDecimalReconfigurationInvalidatesOldAdmissionUntilReviewedAgain() public {
        ActivationMetadataToken changed = new ActivationMetadataToken();
        oracle.setTestFeed(address(changed), address(feed), 1 days); registry.admit(address(changed));
        changed.configure(6, false); oracle.setTestFeed(address(changed), address(feed), 1 days);
        vm.expectRevert(); assets.value(address(changed), 1e6);
        assets.setAsset(address(changed), true, address(changed).codehash, REVIEW);
        assertEq(assets.value(address(changed), 1e6), 1e18);
    }

    function testImmediateGovernanceStillRequiresControllerAfterSeal() public {
        registry.admit(address(token)); _seal();
        bytes memory payload = abi.encodeCall(assets.setAsset, (address(token), false, address(token).codehash, REVIEW));
        vm.expectRevert(); assets.setAsset(address(token), false, address(token).codehash, REVIEW);
        vm.prank(ATTACKER); vm.expectRevert(); assets.setAsset(address(token), false, address(token).codehash, REVIEW);
        vm.prank(GUARDIAN); vm.expectRevert(); assets.setAsset(address(token), false, address(token).codehash, REVIEW);
        _execute(payload, keccak256("disable token"));
        vm.expectRevert(); assets.value(address(token), 1e6);
    }

    function testGovernanceEnableRequiresFreshFeedAndCorrectRuntimeAtExecution() public {
        _seal(); bytes memory payload = abi.encodeCall(assets.setAsset, (address(token), true, address(token).codehash, REVIEW));
        bytes32 salt = keccak256("enable token");
        access.schedule(address(assets), 0, payload, bytes32(0), salt, 0);
        vm.warp(block.timestamp + 2 days);
        vm.expectRevert(); access.execute(address(assets), 0, payload, bytes32(0), salt);
        assertEq(assets.policyCount(), 0); feed.set(1e8, block.timestamp, block.timestamp);
        access.execute(address(assets), 0, payload, bytes32(0), salt);
        assertEq(assets.value(address(token), 100e6), 100e18);
    }

    function testGovernanceDisableSucceedsDespiteTokenAndOracleOutage() public {
        bytes32 pin = address(token).codehash; registry.admit(address(token)); _seal();
        vm.etch(address(token), hex"fe"); vm.etch(address(oracle), hex"fe");
        _execute(abi.encodeCall(assets.setAsset, (address(token), false, pin, REVIEW)), keccak256("outage disable"));
        (,bool enabled,,,,) = assets.policies(assets.activePolicy(address(token))); assertFalse(enabled);
    }

    function testGuardianPauseDoesNotGrantAssetConfigurationAuthority() public {
        registry.admit(address(token)); _seal(); vm.prank(GUARDIAN); access.setPaused(true);
        assertEq(assets.value(address(token), 1e6), 1e18);
        _execute(abi.encodeCall(assets.setAsset, (address(token), false, address(token).codehash, REVIEW)), keccak256("paused disable"));
        vm.expectRevert(); assets.value(address(token), 1e6);
    }

    function testAdmissionNeverHoldsOrMovesFundsAndCannotSweepForcedAssets() public {
        token.mint(address(assets), 123); vm.deal(address(assets), 1 ether);
        registry.admit(address(token)); assets.setAsset(address(token), false, address(token).codehash, REVIEW);
        assertEq(token.balanceOf(address(assets)), 123); assertEq(address(assets).balance, 1 ether);
        (bool success,) = address(assets).call(abi.encodeWithSignature("withdraw(address)",address(token))); assertFalse(success);
        (success,) = address(assets).call(abi.encodeWithSignature("sweep(address,address)",address(token),ATTACKER)); assertFalse(success);
        assertEq(token.balanceOf(ATTACKER), 0);
    }

    function testAdmissionDoesNotBypassExistingExactTransferExecutionGuard() public {
        TaxToken taxed = new TaxToken(); oracle.setTestFeed(address(taxed), address(feed), 1 days);
        // Governance's review attestation is not proof of transfer semantics.
        registry.admit(address(taxed)); assertEq(assets.value(address(taxed), 100), 100);
        ActivationPullFixture puller = new ActivationPullFixture(); taxed.mint(address(this), 100);
        taxed.approve(address(puller), 100); vm.expectRevert(); puller.pull(address(taxed), 100);
        assertEq(taxed.balanceOf(address(this)), 100); assertEq(taxed.balanceOf(address(puller)), 0);
    }
}
