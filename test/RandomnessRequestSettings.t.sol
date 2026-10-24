// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZNFT, IZZZVRFCoordinator} from "../src/ZZZNFT.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess} from "./mocks/Mocks.sol";

/// @dev TEST ONLY. Retains each submitted tuple; performs no VRF verification.
contract RecordedRequestCoordinator is IZZZVRFCoordinator {
    struct SubmittedRequest {
        address consumer;
        bytes32 keyHash;
        uint256 subscriptionId;
        uint16 confirmations;
        uint32 callbackGasLimit;
        uint32 numWords;
        bytes extraArgs;
    }
    mapping(uint256 => SubmittedRequest) private submitted;
    uint256 public sequence;
    address private callbackTarget;
    bytes private callbackData;
    bool public callbackSucceeded;
    bytes public callbackResult;

    function request(uint256 id) external view returns (SubmittedRequest memory) { return submitted[id]; }
    function setCallback(address target, bytes calldata data) external { callbackTarget = target; callbackData = data; }
    function requestRandomWords(RandomWordsRequest calldata value) external returns (uint256 id) {
        id = ++sequence;
        submitted[id] = SubmittedRequest(msg.sender, value.keyHash, value.subId, value.requestConfirmations,
            value.callbackGasLimit, value.numWords, value.extraArgs);
        if (callbackTarget != address(0)) (callbackSucceeded, callbackResult) = callbackTarget.call(callbackData);
    }
    function fulfill(uint256 id, uint256 rarityWord, uint256 artworkWord) external {
        uint256[] memory words = new uint256[](2); words[0] = rarityWord; words[1] = artworkWord;
        ZZZNFT(submitted[id].consumer).rawFulfillRandomWords(id, words);
    }
}

/// @dev TEST ONLY. No LP, rewards or external custody is simulated here.
contract RequestSettingsBound {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}
contract RequestSettingsVault is RequestSettingsBound {
    ZZZNFT private immutable nft;
    address payable public constant mintProceedsRecipient = payable(address(0x7EA5));
    constructor(address controller, ZZZNFT collection) RequestSettingsBound(controller) { nft = collection; }
    function canonicalChainId() external view returns (uint256) { return block.chainid; }
    function mint(address owner, uint256 id) external { nft.mint(owner, id); }
}
contract RequestSettingsCompanion is RequestSettingsBound {
    address public immutable vault;
    address public immutable fees;
    constructor(address controller, address owner) RequestSettingsBound(controller) { vault = owner; fees = owner; }
}
/// @dev TEST ONLY lifecycle driver. The real controller still enforces all
/// configuration gates; this is not a funded whole-protocol migration fixture.
contract RequestSettingsHandoff is RequestSettingsBound {
    constructor(address controller) RequestSettingsBound(controller) {}
    function transition(uint8 state) external { ZZZAccessController(payable(address(access))).canonicalTransition(state, false, true); }
    function importRecord(ZZZNFTCanonical codec, uint256 row, bytes calldata record) external { codec.canonicalImport(row, record); }
    function validate(ZZZNFTCanonical codec) external view { codec.canonicalValidate(); }
    function activate(ZZZNFTCanonical codec) external { codec.canonicalActivate(); }
}

contract RandomnessRequestSettingsTest is Test {
    struct System {
        ZZZAccessController access;
        ZZZNFT nft;
        RecordedRequestCoordinator coordinator;
        RequestSettingsVault vault;
        RequestSettingsHandoff handoff;
        ZZZNFTCanonical codec;
    }
    System private current;
    uint256 private governanceNonce;
    address private constant ALICE = address(0xA11CE);
    address private constant GUARDIAN = address(0x600D);
    event RandomnessRequestSettingsChanged(uint16 previousConfirmations, uint32 previousCallbackGasLimit,
        uint16 confirmations, uint32 callbackGasLimit);

    function setUp() public { vm.warp(1_000_000); current = _deploy(3, 500000, true); }

    function _deploy(uint16 confirmations, uint32 gasLimit, bool sealNow) private returns (System memory s) {
        address[] memory proposers = new address[](1); proposers[0] = address(this);
        address[] memory executors = new address[](1); executors[0] = address(0);
        s.access = new ZZZAccessController(0, proposers, executors, address(this), GUARDIAN);
        s.nft = new ZZZNFT(address(s.access), "ipfs://request-settings-fixture/");
        s.coordinator = new RecordedRequestCoordinator();
        s.nft.configureRandomness(address(s.coordinator), keccak256("fixed gas lane"), 17, confirmations, gasLimit, true);
        s.vault = new RequestSettingsVault(address(s.access), s.nft);
        s.handoff = new RequestSettingsHandoff(address(s.access));
        s.codec = new ZZZNFTCanonical(address(s.access), address(s.nft));
        s.access.bind(Ids.NFT, address(s.nft)); s.access.bind(Ids.VAULT, address(s.vault));
        s.access.bind(Ids.CANONICAL, address(s.handoff)); s.access.bind(Ids.NFT_CANONICAL, address(s.codec));
        bytes32[10] memory ordinary = [Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP, Ids.FEES,
            Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION, Ids.ORACLE, Ids.POOLS];
        for (uint256 i; i < ordinary.length; ++i)
            s.access.bind(ordinary[i], address(new RequestSettingsBound(address(s.access))));
        s.access.bind(Ids.VAULT_CANONICAL, address(new RequestSettingsCompanion(address(s.access), address(s.vault))));
        s.access.bind(Ids.FEES_CANONICAL,
            address(new RequestSettingsCompanion(address(s.access), s.access.module(Ids.FEES))));
        if (sealNow) s.access.seal();
    }
    function _schedule(System memory s, address target, bytes memory data) private returns (bytes32 salt) {
        salt = bytes32(++governanceNonce); s.access.schedule(target, 0, data, bytes32(0), salt, 0);
    }
    function _govern(System memory s, address target, bytes memory data) private {
        bytes32 salt = _schedule(s, target, data);
        s.access.execute(target, 0, data, bytes32(0), salt);
    }
    function _tune(System memory s, uint16 confirmations, uint32 gasLimit) private {
        _govern(s, address(s.nft), abi.encodeCall(s.nft.setRandomnessRequestSettings, (confirmations, gasLimit)));
    }
    function _expectTuneRevert(System memory s, uint16 confirmations, uint32 gasLimit, bytes4 selector) private {
        bytes memory data = abi.encodeCall(s.nft.setRandomnessRequestSettings, (confirmations, gasLimit));
        bytes32 salt = _schedule(s, address(s.nft), data); vm.expectRevert(selector);
        s.access.execute(address(s.nft), 0, data, bytes32(0), salt);
    }
    function _assertFixedDependencies(System memory s) private view {
        assertEq(s.nft.randomnessCoordinator(), address(s.coordinator)); assertEq(s.nft.keyHash(), keccak256("fixed gas lane"));
        assertEq(s.nft.subscriptionId(), 17); assertTrue(s.nft.nativePayment()); assertTrue(s.nft.randomnessConfigured());
    }
    function _assertRequest(System memory s, uint256 id, uint16 confirmations, uint32 gasLimit) private view {
        RecordedRequestCoordinator.SubmittedRequest memory record = s.coordinator.request(id);
        assertEq(record.consumer, address(s.nft)); assertEq(record.confirmations, confirmations);
        assertEq(record.callbackGasLimit, gasLimit); assertEq(record.keyHash, keccak256("fixed gas lane"));
        assertEq(record.subscriptionId, 17); assertEq(record.numWords, 2);
        assertEq(record.extraArgs, abi.encodeWithSelector(bytes4(keccak256("VRF ExtraArgsV1")), true));
    }
    function _traitStateHash(ZZZNFT collection, uint256 id) private view returns (bytes32) {
        (uint256 recordedId, uint256 rarityWord, uint256 artworkWord, bool requested, bool fulfilled) = collection.canonicalRandomness(id);
        return keccak256(abi.encode(collection.rarityOf(id), collection.paletteOf(id), collection.patternOf(id),
            collection.colorOf(id), recordedId, rarityWord, artworkWord, requested, fulfilled));
    }

    function testImmediateGovernanceChangesOnlyFutureRequestArgumentsAndEmitsExactEvent() public {
        current.vault.mint(ALICE, 444); bytes32 oldRequest = keccak256(abi.encode(current.coordinator.request(1)));
        uint256 timestamp = block.timestamp;
        bytes memory data = abi.encodeCall(current.nft.setRandomnessRequestSettings, (200, 10000000));
        bytes32 salt = _schedule(current, address(current.nft), data);
        vm.expectEmit(false, false, false, true, address(current.nft));
        emit RandomnessRequestSettingsChanged(3, 500000, 200, 10000000);
        current.access.execute(address(current.nft), 0, data, bytes32(0), salt);
        assertEq(block.timestamp, timestamp); assertEq(current.nft.requestConfirmations(), 200);
        assertEq(current.nft.callbackGasLimit(), 10000000); _assertFixedDependencies(current);
        assertEq(keccak256(abi.encode(current.coordinator.request(1))), oldRequest);
        current.vault.mint(ALICE, 445); _assertRequest(current, 1, 3, 500000); _assertRequest(current, 2, 200, 10000000);
        assertEq(current.nft.requestOf(444), 1); assertEq(current.nft.requestOf(445), 2);
        assertEq(current.nft.mintOrdinalOf(444), 1); assertEq(current.nft.mintOrdinalOf(445), 2);
    }

    function testPendingAuthenticationOrderedRevealAndFinalTraitsSurviveTuning() public {
        current.vault.mint(ALICE, 444); _tune(current, 8, 800000); current.vault.mint(ALICE, 445);
        current.coordinator.fulfill(2, 599, 5); vm.expectRevert(ZZZModule.NotReady.selector); current.nft.finalizeTraits(445);
        uint256[] memory words = new uint256[](2);
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Unauthorized.selector); current.nft.rawFulfillRandomWords(1, words);
        _tune(current, 3, 200000); current.coordinator.fulfill(1, 0, 0);
        current.nft.finalizeTraits(444); current.nft.finalizeTraits(445);
        assertEq(current.nft.rarityOf(444), 0); assertEq(current.nft.rarityOf(445), 1);
        assertEq(current.nft.rarityRemaining(0), 599); assertEq(current.nft.rarityRemaining(1), 299);
        assertEq(current.nft.remainingToReveal(), 998); assertEq(current.nft.nextToFinalize(), 3);
        bytes32 traits = _traitStateHash(current.nft, 444);
        _tune(current, 199, 9999999);
        assertEq(_traitStateHash(current.nft, 444), traits);
        vm.expectRevert(ZZZModule.InvalidState.selector); current.coordinator.fulfill(1, 999, 999);
        vm.expectRevert(ZZZModule.NotReady.selector); current.nft.finalizeTraits(444);
        assertEq(current.coordinator.sequence(), 2); assertEq(current.nft.mintedCount(), 2);
        _assertRequest(current, 1, 3, 500000); _assertRequest(current, 2, 8, 800000);
    }

    function testInvalidBoundsAndNonGovernanceCannotChangeSettings() public {
        _expectTuneRevert(current, 2, 500000, ZZZModule.InvalidConfiguration.selector);
        _expectTuneRevert(current, 201, 500000, ZZZModule.InvalidConfiguration.selector);
        _expectTuneRevert(current, 3, 199999, ZZZModule.InvalidConfiguration.selector);
        _expectTuneRevert(current, 3, 10000001, ZZZModule.InvalidConfiguration.selector);
        vm.expectRevert(ZZZModule.Unauthorized.selector); current.nft.setRandomnessRequestSettings(4, 600000);
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Unauthorized.selector); current.nft.setRandomnessRequestSettings(4, 600000);
        vm.prank(GUARDIAN); vm.expectRevert(ZZZModule.Unauthorized.selector); current.nft.setRandomnessRequestSettings(4, 600000);
        assertEq(current.nft.requestConfirmations(), 3); assertEq(current.nft.callbackGasLimit(), 500000);
        _assertFixedDependencies(current);
        _tune(current, 3, 200000); current.vault.mint(ALICE, 444); _assertRequest(current, 1, 3, 200000);
    }

    function testTuningRequiresConfigurationAndWorksBeforeSealWithoutProviderReplacement() public {
        MockAccess unconfiguredAccess = new MockAccess(); ZZZNFT unconfigured = new ZZZNFT(address(unconfiguredAccess), "");
        vm.expectRevert(ZZZModule.NotReady.selector); unconfigured.setRandomnessRequestSettings(3, 500000);
        unconfiguredAccess.seal();
        vm.expectRevert(ZZZModule.NotReady.selector); unconfigured.setRandomnessRequestSettings(3, 500000);
        System memory bootstrap = _deploy(5, 600000, false);
        bootstrap.nft.setRandomnessRequestSettings(6, 700000);
        bootstrap.access.seal(); bootstrap.vault.mint(ALICE, 444); _assertRequest(bootstrap, 1, 6, 700000);
        bytes memory replacement = abi.encodeCall(bootstrap.nft.configureRandomness,
            (address(current.coordinator), bytes32(uint256(2)), 18, 3, 500000, false));
        bytes32 salt = _schedule(bootstrap, address(bootstrap.nft), replacement);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        bootstrap.access.execute(address(bootstrap.nft), 0, replacement, bytes32(0), salt);
        _assertFixedDependencies(bootstrap);
    }

    function testPauseDoesNotPreventGovernanceRepairOrChangePauseState() public {
        vm.prank(GUARDIAN); current.access.setPaused(true);
        _govern(current, address(current.nft), abi.encodeCall(current.nft.setMintPaused, (true)));
        _tune(current, 12, 1200000);
        assertTrue(current.access.paused()); assertTrue(current.nft.mintPaused());
        assertEq(current.nft.requestConfirmations(), 12); assertEq(current.nft.callbackGasLimit(), 1200000);
        _govern(current, address(current.access), abi.encodeCall(current.access.setPaused, (false)));
        _govern(current, address(current.nft), abi.encodeCall(current.nft.setMintPaused, (false)));
        current.vault.mint(ALICE, 444); _assertRequest(current, 1, 12, 1200000);
    }

    function testUnsealedImporterBootstrapCannotBypassCanonicalOperatingLock() public {
        System memory importing = _deploy(5, 600000, false);
        importing.handoff.transition(2);
        // Bootstrap is deliberately still recognized before seal; operating is
        // an independent fail-closed boundary for the inert importer.
        assertTrue(importing.access.canConfigure(address(this))); assertFalse(importing.access.isSealed());
        vm.expectRevert(ZZZModule.CanonicalLocked.selector);
        importing.nft.setRandomnessRequestSettings(6, 700000);
        assertEq(importing.nft.requestConfirmations(), 5); assertEq(importing.nft.callbackGasLimit(), 600000);
        _assertFixedDependencies(importing);
    }

    function testPreparationAndAllCanonicalLocksRejectTuningWhileRevealMayDrain() public {
        current.vault.mint(ALICE, 444);
        ZZZAccessController.PreparationNotice memory notice = ZZZAccessController.PreparationNotice(
            block.chainid + 1, address(0xCA11), keccak256("reviewed deployment"), keccak256("review material"));
        _govern(current, address(current.access), abi.encodeCall(current.access.startPreparation, (notice)));
        _expectTuneRevert(current, 4, 600000, ZZZModule.Unauthorized.selector);
        current.coordinator.fulfill(1, 0, 0); current.nft.finalizeTraits(444); assertTrue(current.nft.traitsReady(444));
        _govern(current, address(current.access), abi.encodeCall(current.access.cancelPreparation, (current.access.preparationHash())));
        for (uint8 state = 1; state <= 4; ++state) {
            uint256 snapshot = vm.snapshotState(); current.handoff.transition(state);
            _expectTuneRevert(current, 4, 600000, ZZZModule.Unauthorized.selector);
            assertTrue(vm.revertToState(snapshot));
        }
        _tune(current, 4, 600000); assertEq(current.nft.requestConfirmations(), 4);
    }

    function testRequestCallbackCannotExecuteReadyGovernanceChangeDuringMint() public {
        bytes memory data = abi.encodeCall(current.nft.setRandomnessRequestSettings, (20, 2000000));
        bytes32 salt = _schedule(current, address(current.nft), data);
        current.coordinator.setCallback(address(current.access), abi.encodeCall(current.access.execute,
            (address(current.nft), 0, data, bytes32(0), salt)));
        current.vault.mint(ALICE, 444);
        assertFalse(current.coordinator.callbackSucceeded());
        assertEq(current.coordinator.callbackResult(), abi.encodeWithSelector(ReentrancyGuard.ReentrancyGuardReentrantCall.selector));
        assertEq(current.nft.requestConfirmations(), 3); assertEq(current.nft.callbackGasLimit(), 500000);
        assertEq(current.coordinator.sequence(), 1); _assertRequest(current, 1, 3, 500000);
        current.coordinator.setCallback(address(0), "");
        current.access.execute(address(current.nft), 0, data, bytes32(0), salt);
        current.vault.mint(ALICE, 445); _assertRequest(current, 2, 20, 2000000);
    }

    function testSuccessorKeepsOwnFutureSettingsAndImportedHistoricalRequestEpoch() public {
        current.vault.mint(ALICE, 444); current.coordinator.fulfill(1, 900, 4); current.nft.finalizeTraits(444);
        _tune(current, 7, 700000);
        System memory successor = _deploy(9, 900000, true);
        current.handoff.transition(1); successor.handoff.transition(2);
        _expectTuneRevert(successor, 11, 1100000, ZZZModule.Unauthorized.selector);
        uint256 count = current.codec.canonicalCount();
        for (uint256 row; row < count; ++row)
            successor.handoff.importRecord(successor.codec, row, current.codec.canonicalExport(row));
        successor.handoff.validate(successor.codec); successor.handoff.activate(successor.codec);
        current.handoff.transition(3); successor.handoff.transition(0);
        assertEq(successor.nft.requestConfirmations(), 9); assertEq(successor.nft.callbackGasLimit(), 900000);
        assertEq(successor.nft.ownerOf(444), ALICE); assertEq(successor.nft.rarityOf(444), current.nft.rarityOf(444));
        assertEq(successor.nft.paletteOf(444), current.nft.paletteOf(444)); assertEq(successor.nft.patternOf(444), current.nft.patternOf(444));
        assertEq(successor.nft.requestEpochOf(444), 0); assertEq(successor.nft.randomnessEpoch(), 1);
        assertEq(successor.nft.requestOf(444), 1);
        _tune(successor, 11, 1100000); successor.vault.mint(ALICE, 445);
        assertEq(successor.nft.requestOf(445), 1); assertEq(successor.nft.requestEpochOf(445), 1);
        _assertRequest(successor, 1, 11, 1100000);
        successor.coordinator.fulfill(1, 0, 0); successor.nft.finalizeTraits(445);
        assertTrue(successor.nft.traitsReady(444)); assertTrue(successor.nft.traitsReady(445));
        assertEq(successor.nft.mintedCount(), 2); assertEq(successor.nft.nextToFinalize(), 3);
        _assertFixedDependencies(successor);
    }
}
