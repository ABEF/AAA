// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZNFT, IZZZVRFCoordinator} from "../src/ZZZNFT.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess} from "./mocks/Mocks.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";

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
    function acceptGovernance(ZZZAccessController controller) external {controller.acceptGovernance();}
    function resetSequenceForTest(uint256 value) external {sequence=value;}
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
contract UpgradedRecordedRequestCoordinator is RecordedRequestCoordinator {
    function runtimeMarker() external pure returns(uint256){return 2;}
}

/// @dev TEST ONLY. No LP, rewards or external custody is simulated here.
contract RequestSettingsBound {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
    // TEST ONLY identity for seal; this VRF fixture has no LP/source admission.
    function activationAssets() external view returns(address) { return address(this); }
    function zzz() external pure returns(address) { return address(0x7A7A); }
    function currentZZZ() external pure returns(address) { return address(0x7A7A); }
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
    address public incomingSource;
    address public destinationController;
    constructor(address controller) RequestSettingsBound(controller) {}
    function setPeers(address source,address destination) external {incomingSource=source;destinationController=destination;}
    function transition(uint8 state) external { ZZZAccessController(payable(address(access))).canonicalTransition(state, false, true); }
    function capture(ZZZNFTCanonical codec) external {codec.canonicalCapture();}
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
        ZZZProtocolPolicy policy;
    }
    System private current;
    address private constant ALICE = address(0xA11CE);
    address private constant GOVERNANCE = address(0xA0A0);
    address private constant GUARDIAN = address(0x600D);
    bytes32 private constant REVIEW=keccak256("request settings fixture review");
    event RandomnessSettingsConfigured(uint16 confirmations,uint32 callbackGasLimit,uint64 revision,bytes32 reviewHash);

    function setUp() public { vm.warp(1_000_000); current = _deploy(3, 500000, true); }

    function _deploy(uint16 confirmations, uint32 gasLimit, bool sealNow) private returns (System memory s) {
        s.access = new ZZZAccessController(GOVERNANCE, address(this), GUARDIAN);
        s.policy = new ZZZProtocolPolicy(address(s.access),address(0x7EA5));
        s.access.bindProtocolPolicy(address(s.policy));
        s.nft = new ZZZNFT(address(s.access), "ipfs://request-settings-fixture/");
        s.coordinator = new RecordedRequestCoordinator();
        s.policy.configureRandomness(address(s.coordinator),address(s.coordinator).codehash,keccak256("fixed gas lane"),17,confirmations,gasLimit,true,REVIEW);
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
    function _govern(System memory s, address target, bytes memory data) private {
        vm.prank(s.access.governance());
        (bool ok, bytes memory result) = target.call(data);
        if (!ok) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
    }
    function _tune(System memory s, uint16 confirmations, uint32 gasLimit) private {
        _govern(s,address(s.policy),abi.encodeCall(s.policy.setRandomnessRequestSettings,(confirmations,gasLimit,REVIEW)));
    }
    function _expectTuneRevert(System memory s, uint16 confirmations, uint32 gasLimit, bytes4 selector) private {
        vm.prank(s.access.governance()); vm.expectRevert(selector);
        s.policy.setRandomnessRequestSettings(confirmations,gasLimit,REVIEW);
    }
    function _rotate(System memory s,RecordedRequestCoordinator next) private {
        _govern(s,address(s.policy),abi.encodeCall(s.policy.rotateRandomness,
            (address(next),address(next).codehash,keccak256("rotated lane"),42,4,600000,false,REVIEW)));
    }
    function _expectRotationRevert(System memory s,RecordedRequestCoordinator next,bytes4 selector) private {
        vm.prank(s.access.governance());vm.expectRevert(selector);
        s.policy.rotateRandomness(address(next),address(next).codehash,keccak256("rotated lane"),42,4,600000,false,REVIEW);
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
        vm.expectEmit(false,false,false,true,address(current.policy));
        emit RandomnessSettingsConfigured(200,10000000,2,REVIEW);
        vm.prank(current.access.governance());current.policy.setRandomnessRequestSettings(200,10000000,REVIEW);
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
        vm.expectRevert(ZZZModule.Unauthorized.selector);current.policy.setRandomnessRequestSettings(4,600000,REVIEW);
        vm.prank(ALICE);vm.expectRevert(ZZZModule.Unauthorized.selector);current.policy.setRandomnessRequestSettings(4,600000,REVIEW);
        vm.prank(GUARDIAN);vm.expectRevert(ZZZModule.Unauthorized.selector);current.policy.setRandomnessRequestSettings(4,600000,REVIEW);
        assertEq(current.nft.requestConfirmations(), 3); assertEq(current.nft.callbackGasLimit(), 500000);
        _assertFixedDependencies(current);
        _tune(current, 3, 200000); current.vault.mint(ALICE, 444); _assertRequest(current, 1, 3, 200000);
    }

    function testTuningRequiresConfigurationAndWorksBeforeSealWithoutProviderReplacement() public {
        MockAccess unconfiguredAccess = new MockAccess(); ZZZNFT unconfigured = new ZZZNFT(address(unconfiguredAccess), "");
        ZZZProtocolPolicy unconfiguredPolicy=new ZZZProtocolPolicy(address(unconfiguredAccess),address(0x7EA5));
        unconfiguredAccess.setProtocolPolicy(address(unconfiguredPolicy));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);unconfiguredPolicy.setRandomnessRequestSettings(3,500000,REVIEW);
        unconfiguredAccess.seal();
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);unconfiguredPolicy.setRandomnessRequestSettings(3,500000,REVIEW);
        assertFalse(unconfigured.randomnessConfigured());
        System memory bootstrap = _deploy(5, 600000, false);
        bootstrap.policy.setRandomnessRequestSettings(6,700000,REVIEW);
        bootstrap.access.seal(); bootstrap.vault.mint(ALICE, 444); _assertRequest(bootstrap, 1, 6, 700000);
        vm.prank(bootstrap.access.governance()); vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        bootstrap.policy.configureRandomness(address(current.coordinator),address(current.coordinator).codehash,bytes32(uint256(2)),18,3,500000,false,REVIEW);
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
        importing.policy.setRandomnessRequestSettings(6,700000,REVIEW);
        assertEq(importing.nft.requestConfirmations(), 5); assertEq(importing.nft.callbackGasLimit(), 600000);
        _assertFixedDependencies(importing);
    }

    function testPreparationAndAllCanonicalLocksRejectTuningWhileRevealMayDrain() public {
        current.vault.mint(ALICE, 444);
        ZZZAccessController.PreparationNotice memory notice = ZZZAccessController.PreparationNotice(
            block.chainid, address(0xCA11), keccak256("reviewed deployment"), keccak256("review material"));
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

    function testUnprivilegedCoordinatorCallbackCannotChangeGovernanceSettingsDuringMint() public {
        current.coordinator.setCallback(address(current.policy),
            abi.encodeCall(current.policy.setRandomnessRequestSettings,(20,2000000,REVIEW)));
        current.vault.mint(ALICE, 444);
        assertFalse(current.coordinator.callbackSucceeded());
        assertEq(current.coordinator.callbackResult(), abi.encodeWithSelector(ZZZModule.Unauthorized.selector));
        assertEq(current.nft.requestConfirmations(), 3); assertEq(current.nft.callbackGasLimit(), 500000);
        assertEq(current.coordinator.sequence(), 1); _assertRequest(current, 1, 3, 500000);
        current.coordinator.setCallback(address(0), "");
        _tune(current, 20, 2000000);
        current.vault.mint(ALICE, 445); _assertRequest(current, 2, 20, 2000000);
    }

    function testSuccessorKeepsOwnFutureSettingsAndImportedHistoricalRequestEpoch() public {
        current.vault.mint(ALICE, 444); current.coordinator.fulfill(1, 900, 4); current.nft.finalizeTraits(444);
        _tune(current, 7, 700000);
        // Same values with a different local revision must remain compatible.
        _govern(current,address(current.policy),abi.encodeCall(current.policy.setEvolutionThresholds,
            (uint128(1000e18),uint128(10000e18),REVIEW)));
        System memory successor = _deploy(9, 900000, true);
        current.handoff.setPeers(address(0),address(successor.access));
        successor.handoff.setPeers(address(current.access),address(0));
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

    function testRotationWaitsForFulfilledANDMintOrderedFinalizedDraws() public {
        RecordedRequestCoordinator next=new RecordedRequestCoordinator();
        current.vault.mint(ALICE,444);
        _expectRotationRevert(current,next,ZZZModule.InvalidState.selector);
        current.coordinator.fulfill(1,0,0);
        _expectRotationRevert(current,next,ZZZModule.InvalidState.selector);
        current.nft.finalizeTraits(444);
        bytes32 previous=_traitStateHash(current.nft,444);
        _rotate(current,next);
        assertEq(current.nft.randomnessEpoch(),1);assertEq(current.nft.randomnessCoordinator(),address(next));
        assertEq(_traitStateHash(current.nft,444),previous);assertEq(current.nft.requestEpochOf(444),0);
        current.vault.mint(ALICE,445);
        assertEq(current.nft.requestOf(445),1);assertEq(current.nft.requestEpochOf(445),1);
        vm.expectRevert(ZZZModule.Unauthorized.selector);current.coordinator.fulfill(1,999,999);
        next.fulfill(1,0,0);current.nft.finalizeTraits(445);
        assertEq(_traitStateHash(current.nft,444),previous);assertTrue(current.nft.traitsReady(445));
    }

    function testSameProviderCannotRecycleAnOldRequestIDAfterRotation() public {
        current.vault.mint(ALICE,444);current.coordinator.fulfill(1,0,0);current.nft.finalizeTraits(444);
        bytes32 previous=_traitStateHash(current.nft,444);
        _rotate(current,current.coordinator);
        current.coordinator.resetSequenceForTest(0);
        vm.expectRevert(ZZZModule.InvalidState.selector);current.vault.mint(ALICE,445);
        assertEq(current.nft.mintedCount(),1);assertEq(current.nft.requestOf(445),0);
        assertEq(_traitStateHash(current.nft,444),previous);
    }

    function testProviderRuntimeChangeBlocksNewMintButOriginalCallbackCanDrain() public {
        current.vault.mint(ALICE,444);
        UpgradedRecordedRequestCoordinator implementation=new UpgradedRecordedRequestCoordinator();
        vm.etch(address(current.coordinator),address(implementation).code);
        vm.expectRevert(ZZZModule.NotReady.selector);current.vault.mint(ALICE,445);
        current.coordinator.fulfill(1,0,0);current.nft.finalizeTraits(444);
        _rotate(current,current.coordinator);
        current.vault.mint(ALICE,445);
        assertEq(current.nft.requestOf(445),2);assertEq(current.nft.requestEpochOf(445),1);
    }

    function testAuthorizedProviderCallbackCannotChangeRequestSettingsMidMint() public {
        _govern(current,address(current.access),abi.encodeCall(current.access.proposeGovernance,(address(current.coordinator))));
        current.coordinator.acceptGovernance(current.access);
        current.coordinator.setCallback(address(current.policy),
            abi.encodeCall(current.policy.setRandomnessRequestSettings,(20,2000000,REVIEW)));
        vm.expectRevert(ZZZModule.InvalidState.selector);current.vault.mint(ALICE,444);
        assertEq(current.nft.mintedCount(),0);assertEq(current.coordinator.sequence(),0);
        assertEq(current.policy.vrfRevision(),1);assertEq(current.nft.callbackGasLimit(),500000);
    }

    function testCosmeticProviderCallbackDoesNotInvalidateTheVrfRevision() public {
        _govern(current,address(current.access),abi.encodeCall(current.access.proposeGovernance,(address(current.coordinator))));
        current.coordinator.acceptGovernance(current.access);
        current.coordinator.setCallback(address(current.policy),
            abi.encodeCall(current.policy.setEvolutionThresholds,(uint128(2000e18),uint128(20000e18),REVIEW)));
        current.vault.mint(ALICE,444);
        assertTrue(current.coordinator.callbackSucceeded());assertEq(current.nft.mintedCount(),1);
        assertEq(current.policy.vrfRevision(),1);assertEq(current.nft.callbackGasLimit(),500000);
        assertEq(current.policy.metadataPolicy().enhancedUSD,2000e18);
    }

    function testRotationRequiresExplicitMatchingRuntimeAndReview() public {
        RecordedRequestCoordinator next=new RecordedRequestCoordinator();
        vm.prank(ALICE);vm.expectRevert(ZZZModule.Unauthorized.selector);
        current.policy.rotateRandomness(address(next),address(next).codehash,keccak256("lane"),1,3,500000,false,REVIEW);
        vm.prank(GOVERNANCE);vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        current.policy.rotateRandomness(address(next),bytes32(uint256(1)),keccak256("lane"),1,3,500000,false,REVIEW);
        vm.prank(GOVERNANCE);vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        current.policy.rotateRandomness(address(next),address(next).codehash,keccak256("lane"),1,3,500000,false,bytes32(0));
        assertEq(current.nft.randomnessCoordinator(),address(current.coordinator));assertEq(current.nft.randomnessEpoch(),0);
    }

    function testCanonicalHandoffRejectsMismatchedVisualThresholdsBeforeImport() public {
        System memory successor=_deploy(9,900000,true);
        _govern(successor,address(successor.policy),abi.encodeCall(successor.policy.setEvolutionThresholds,
            (uint128(2000e18),uint128(20000e18),REVIEW)));
        current.handoff.setPeers(address(0),address(successor.access));
        successor.handoff.setPeers(address(current.access),address(0));
        current.handoff.transition(1);successor.handoff.transition(2);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);current.handoff.capture(current.codec);
        bytes memory header=current.codec.canonicalExport(0);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        successor.handoff.importRecord(successor.codec,0,header);
        assertEq(successor.nft.mintedCount(),0);assertEq(successor.nft.nextToFinalize(),1);
    }

    function testRetiredHeaderRemainsReadableAfterSuccessorChangesCosmetics() public {
        System memory successor=_deploy(9,900000,true);
        current.handoff.setPeers(address(0),address(successor.access));
        current.handoff.transition(3);
        _govern(successor,address(successor.policy),abi.encodeCall(successor.policy.setEvolutionThresholds,
            (uint128(2000e18),uint128(20000e18),REVIEW)));
        bytes memory header=current.codec.canonicalExport(0);
        assertGt(header.length,0);current.codec.canonicalValidate();
    }
}
