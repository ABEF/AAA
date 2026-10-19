// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZArtwork} from "../src/libraries/ZZZArtwork.sol";
import {ZZZNFTMetadata, NFTMetadataInput} from "../src/ZZZNFTMetadata.sol";
import {Ids, Position, PositionStatus, PoolConfig, PoolKey} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockFeed, MockPools} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

/// @dev TEST ONLY. Marks synthetic LP shares/NAV without real LP custody.
contract MetadataVaultMock {
    ZZZNFT public nft;
    address payable public mintProceedsRecipient = payable(address(0x7EA5));
    mapping(uint256 => uint256) public nftBucket;
    mapping(uint256 => uint256) public sharesOf;
    mapping(uint256 => uint256) public bucketTotalShares;
    Position private position;
    function setNFT(ZZZNFT candidate) external { nft = candidate; }
    function setMintRecipient(address recipient) external { mintProceedsRecipient = payable(recipient); }
    function mint(address owner, uint256 id) external { nft.mint(owner, id); }
    function setPosition(Position memory candidate) external { position = candidate; }
    function group(uint256) external view returns (Position memory) { return position; }
    function contribute(uint256 id, uint256 shares, uint256 supply) external {
        nftBucket[id] = 1; sharesOf[id] = shares; bucketTotalShares[1] = supply;
        nft.notifyContribution(id);
    }
}

contract MetadataVenueMock {
    uint256 private a0; uint256 private a1; bool private failing;
    function set(uint256 x, uint256 y) external { a0 = x; a1 = y; }
    function setFail(bool fail) external { failing = fail; }
    function amounts(uint256) external view returns (uint256, uint256) { require(!failing); return (a0, a1); }
}

contract MetadataFeesMock {
    mapping(uint256 => mapping(address => uint256)) public compoundBalance;
    function set(address token, uint256 amount) external { compoundBalance[1][token] = amount; }
}

// Price-policy plumbing only. DynamicRange.t.sol exercises the real guard.
contract MetadataPricePolicyMock {
    bool public fail;
    function setFail(bool value) external {fail=value;}
    function validateExitPrice(bytes32) external view returns(uint160) {require(!fail);return uint160(1<<96);}
}

/// @notice NFT trait/reveal/valuation security with explicitly mocked coordinator
/// and LP custody. These tests do not establish deployed VRF or venue support.
contract NFTMetadataTest is Test {
    MockAccess private access;
    ZZZNFT private nft;
    MockVRF private vrf;
    MetadataVaultMock private vault;
    MetadataVenueMock private venue;
    MetadataFeesMock private fees;
    MetadataPricePolicyMock private pricePolicy;
    MockPools private pools;
    ZZZOracle private oracle;
    MockToken private token0; MockToken private token1;
    MockFeed private feed0; MockFeed private feed1;
    Position private home;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);

    function setUp() public {
        vm.warp(1000000);
        access = new MockAccess(); vault = new MetadataVaultMock(); vrf = new MockVRF();
        nft = new ZZZNFT(address(access), "ipfs://example/"); vault.setNFT(nft);
        nft.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        venue = new MetadataVenueMock(); fees = new MetadataFeesMock(); pools = new MockPools();
        token0 = new MockToken(0); token1 = new MockToken(0);
        oracle = new ZZZOracle(address(access), address(0)); feed0 = new MockFeed(8, 1e8); feed1 = new MockFeed(8, 1e8);
        oracle.setFeed(address(token0), address(feed0), 3600); oracle.setFeed(address(token1), address(feed1), 3600);
        access.bind(Ids.NFT, address(nft)); access.bind(Ids.VAULT, address(vault));
        access.bind(Ids.LIQUIDITY, address(venue)); access.bind(Ids.FEES, address(fees));
        access.bind(Ids.POOLS, address(pools)); access.bind(Ids.ORACLE, address(oracle));
        pricePolicy = new MetadataPricePolicyMock(); access.bind(Ids.STRATEGY, address(pricePolicy));
        PoolConfig memory config; config.key = PoolKey(address(token0), address(token1), 3000, 60, address(0));
        home.poolId = keccak256(abi.encode(config.key)); home.lpTokenId = 1; home.status = PositionStatus.Active;
        home.homeChain = block.chainid; home.homeVault = address(vault);
        home.locationChain = block.chainid; home.locationVault = address(vault);
        pools.set(home.poolId, config); vault.setPosition(home); venue.set(1000, 1000);
        access.seal(); vm.deal(ALICE, 10 ether);
    }

    function _reveal(uint256 id, uint256 rarityWord, uint256 colorWord) private {
        vault.mint(ALICE, id); vrf.fulfill(nft.requestOf(id), rarityWord, colorWord);
        vm.prank(BOB); nft.finalizeTraits(id);
    }
    function _active(uint256 id, uint256 rarityWord, uint256 colorWord) private {
        _reveal(id, rarityWord, colorWord); vault.contribute(id, 100, 100);
    }
    function _stage(uint256 id, uint8 expected) private view {
        (bool available, uint8 actual) = nft.evolution(id); assertTrue(available); assertEq(actual, expected);
    }

    function testPriceGuardFailureReportsUnavailableAndPreservesOwnershipAndRoyaltyEligibility() public {
        _active(444, 0, 0); uint256 weight=nft.royaltyRewards().weightOf(444);
        pricePolicy.setFail(true);
        (bool available,uint256 value)=nft.currentLPValue(444);
        assertFalse(available);assertEq(value,0);assertEq(nft.ownerOf(444),ALICE);
        assertEq(nft.royaltyRewards().weightOf(444),weight);
        assertGt(bytes(nft.tokenURI(444)).length,0);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,444);assertEq(nft.ownerOf(444),BOB);
        pricePolicy.setFail(false);(available,value)=nft.currentLPValue(444);
        assertTrue(available);assertEq(value,2000e18);
    }

    function testMintRequiresFixedVRFAndRollbackLeavesNoRequest() public {
        MockAccess otherAccess = new MockAccess(); ZZZNFT other = new ZZZNFT(address(otherAccess), "");
        otherAccess.bind(Ids.VAULT, address(this)); otherAccess.seal();
        vm.expectRevert(); other.mint(ALICE, 1);
        assertEq(other.mintedCount(), 0); assertEq(other.requestOf(1), 0);
        vrf.setFailRequests(true); vm.expectRevert(); vault.mint(ALICE, 1);
        assertEq(nft.mintedCount(), 0); assertEq(vrf.sequence(), 0);
    }

    function testVRFConfigurationAndRequestTupleAreFixed() public {
        vm.expectRevert(); nft.configureRandomness(address(vrf), bytes32(uint256(2)), 2, 3, 500000, false);
        vault.mint(ALICE, 1);
        assertEq(nft.randomnessCoordinator(), address(vrf)); assertEq(nft.subscriptionId(), 1);
        assertEq(vrf.lastKeyHash(), bytes32(uint256(1))); assertEq(vrf.lastSubscriptionId(), 1);
        assertEq(vrf.lastConfirmations(), 3); assertEq(vrf.lastGasLimit(), 500000); assertEq(vrf.lastNumWords(), 2);
        assertEq(vrf.lastExtraArgs(), abi.encodeWithSelector(bytes4(keccak256("VRF ExtraArgsV1")), false));
        assertEq(nft.mintOrdinalOf(1), 1); assertEq(nft.tokenAtOrdinal(1), 1);
        vm.prank(BOB); vm.expectRevert(); nft.mint(BOB, 2);
    }

    function testMintRecipientCannotDivertMintProceedsIntoRoyaltyLedgerOrNFT() public {
        vault.setMintRecipient(address(nft.royaltyRewards()));
        vm.expectRevert(); vault.mint(ALICE, 1);
        assertEq(nft.mintedCount(), 0); assertEq(vrf.sequence(), 0); assertEq(nft.requestOf(1), 0);
        assertEq(nft.royaltyRewards().totalWeight(), 0);
        vault.setMintRecipient(address(nft)); vm.expectRevert(); vault.mint(ALICE, 1);
        assertEq(nft.mintedCount(), 0); assertEq(vrf.sequence(), 0);
    }

    function testUnsealedConfigurationRejectsUnauthorizedInvalidAndSecondConfiguration() public {
        MockAccess otherAccess = new MockAccess(); ZZZNFT other = new ZZZNFT(address(otherAccess), "");
        vm.prank(BOB); vm.expectRevert(); other.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        vm.expectRevert(); other.configureRandomness(address(0), bytes32(uint256(1)), 1, 3, 500000, false);
        vm.expectRevert(); other.configureRandomness(address(vrf), bytes32(0), 1, 3, 500000, false);
        vm.expectRevert(); other.configureRandomness(address(vrf), bytes32(uint256(1)), 0, 3, 500000, false);
        vm.expectRevert(); other.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 2, 500000, false);
        vm.expectRevert(); other.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 100000, false);
        other.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, true);
        vm.expectRevert(); other.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, true);
        assertTrue(other.nativePayment());
    }

    function testOnlyCoordinatorMayFulfillKnownRequestOnceWithTwoWords() public {
        vault.mint(ALICE, 17); uint256 request = nft.requestOf(17); uint256[] memory words = new uint256[](2);
        vm.prank(BOB); vm.expectRevert(); nft.rawFulfillRandomWords(request, words);
        vm.prank(address(vrf)); vm.expectRevert(); nft.rawFulfillRandomWords(request + 1, words);
        vm.expectRevert(); vrf.fulfillMalformed(request, 1);
        vm.expectRevert(); vrf.fulfillMalformed(request, 3);
        vm.expectRevert(); nft.finalizeTraits(17);
        vrf.fulfill(request, 900, 5); assertFalse(nft.traitsReady(17));
        vm.expectRevert(); vrf.fulfill(request, 0, 0);
        vm.prank(BOB); nft.finalizeTraits(17);
        assertEq(nft.rarityOf(17), 2); assertEq(nft.colorOf(17), 5);
        vm.expectRevert(); nft.finalizeTraits(17);
        assertEq(nft.requestOf(17), request); assertEq(vrf.sequence(), 1);
    }

    function testPendingTraitsCannotActivateAndTransferCannotReroll() public {
        vault.mint(ALICE, 1);
        vm.expectRevert(); vault.contribute(1, 100, 100);
        assertEq(vault.sharesOf(1), 0); assertEq(nft.royaltyRewards().weightOf(1), 0);
        vm.prank(ALICE); nft.transferFrom(ALICE, BOB, 1);
        vrf.fulfill(nft.requestOf(1), 999, 4); nft.finalizeTraits(1);
        assertEq(nft.ownerOf(1), BOB); assertEq(nft.rarityOf(1), 2); assertEq(nft.colorOf(1), 2);
        assertEq(nft.paletteOf(1), 45); assertEq(nft.patternOf(1), 2);
        assertEq(vrf.sequence(), 1); assertEq(nft.mintedCount(), 1);
    }

    function testOutOfOrderCallbackCannotReorderQuotaConsumption() public {
        vault.mint(ALICE, 1); vault.mint(ALICE, 2);
        vrf.fulfill(nft.requestOf(2), 599, 5);
        vm.expectRevert(); nft.finalizeTraits(2);
        assertEq(nft.remainingToReveal(), 1000); assertEq(nft.rarityRemaining(0), 600);
        vrf.fulfill(nft.requestOf(1), 0, 0); nft.finalizeTraits(1); nft.finalizeTraits(2);
        assertEq(nft.rarityOf(1), 0); assertEq(nft.rarityOf(2), 1);
        assertEq(nft.rarityRemaining(0), 599); assertEq(nft.rarityRemaining(1), 299);
        assertEq(nft.nextToFinalize(), 3);
    }

    function testFuzzInitialRarityOddsAndIndependentArtwork(uint256 rarityWord, uint256 colorWord) public {
        _reveal(1, rarityWord, colorWord); uint256 roll = rarityWord % 1000;
        uint8 rarity = roll < 600 ? 0 : roll < 900 ? 1 : 2;
        assertEq(nft.rarityOf(1), rarity);
        (uint8 palette, uint8 pattern) = ZZZArtwork.item(rarity, colorWord % (rarity == 0 ? 600 : rarity == 1 ? 300 : 100));
        assertEq(nft.paletteOf(1), palette); assertEq(nft.patternOf(1), pattern);
        assertEq(nft.colorOf(1), ZZZArtwork.primaryColor(palette));
    }

    function testInitialRarityBoundaries() public {
        uint256[6] memory words = [uint256(0), 599, 600, 899, 900, 999];
        uint256[6] memory expected = [uint256(0), 0, 1, 1, 2, 2];
        for (uint256 i; i < words.length; ++i) {
            uint256 snapshot = vm.snapshotState(); _reveal(1, words[i], i);
            assertEq(nft.rarityOf(1), expected[i]);
            assertTrue(vm.revertToState(snapshot));
        }
    }

    function testFullSupplyConsumesExactQuotasAndCannotRequestMint1001() public {
        uint256[3] memory counts; uint256[9] memory styleRarity; uint256[696] memory artworkCopies;
        for (uint256 i = 1; i <= 1000; ++i) {
            _reveal(i, uint256(keccak256(abi.encode(i, "rarity"))), uint256(keccak256(abi.encode(i, "color"))));
            uint8 rarity = nft.rarityOf(i); uint8 palette = nft.paletteOf(i); uint8 pattern = nft.patternOf(i);
            assertLt(palette, 58); assertLt(pattern, 4);
            ++counts[rarity]; ++styleRarity[(palette < 8 ? 0 : palette < 30 ? 1 : 2) * 3 + rarity];
            uint256 copies = ++artworkCopies[uint256(rarity) * 232 + uint256(palette) * 4 + pattern];
            assertLe(copies, rarity == 2 ? 1 : 4);
        }
        assertEq(counts[0], 600); assertEq(counts[1], 300); assertEq(counts[2], 100);
        uint256[9] memory expected = [uint256(120), 60, 20, 300, 150, 50, 180, 90, 30];
        for (uint256 i; i < expected.length; ++i) assertEq(styleRarity[i], expected[i]);
        assertEq(nft.mintedCount(), 1000); assertEq(nft.remainingToReveal(), 0); assertEq(nft.nextToFinalize(), 1001);
        for (uint256 i; i < 3; ++i) assertEq(nft.rarityRemaining(i), 0);
        vm.expectRevert(); vault.mint(ALICE, 1001);
        assertEq(nft.mintedCount(), 1000); assertEq(vrf.sequence(), 1000); assertEq(nft.requestOf(1001), 0);
    }

    function testTraitsStayFixedThroughActivationTopUpAndTransfer() public {
        _reveal(1, 950, 5); assertEq(nft.royaltyRewards().weightOf(1), 0); _stage(1, 0);
        assertEq(nft.paletteOf(1), 5); assertEq(nft.patternOf(1), 1);
        vault.contribute(1, 100, 100); assertEq(nft.royaltyRewards().weightOf(1), 3);
        vault.contribute(1, 200, 200); assertEq(nft.royaltyRewards().totalWeight(), 3);
        vm.prank(ALICE); nft.transferFrom(ALICE, BOB, 1);
        assertEq(nft.rarityOf(1), 2); assertEq(nft.colorOf(1), 5); assertEq(nft.royaltyRewards().weightOf(1), 3);
        assertEq(nft.paletteOf(1), 5); assertEq(nft.patternOf(1), 1);
        assertEq(vrf.sequence(), 1); assertEq(nft.mintedCount(), 1);
    }

    function testLiveEvolutionThresholdsAndDownwardMarketMovesDoNotRemoveRights() public {
        _active(1, 0, 0);
        venue.set(100, 0); _stage(1, 1);
        venue.set(999, 0); _stage(1, 1);
        venue.set(1000, 0); _stage(1, 2);
        venue.set(9999, 0); _stage(1, 2);
        venue.set(10000, 0); _stage(1, 3);
        feed0.set(1e7, block.timestamp, block.timestamp); _stage(1, 2);
        feed0.set(9990000, block.timestamp, block.timestamp); _stage(1, 1);
        venue.set(0, 0); _stage(1, 1);
        assertEq(nft.royaltyRewards().weightOf(1), 1); assertEq(nft.royaltyRewards().totalWeight(), 1);
    }

    function testCurrentNAVIncludesIdleAndCompoundAndAttributesOnlyNFTShares() public {
        _active(1, 0, 0); vault.contribute(1, 25, 100);
        home.idle0 = 100; home.idle1 = 200; vault.setPosition(home);
        fees.set(address(token0), 300); fees.set(address(token1), 400);
        (bool available, uint256 value) = nft.currentLPValue(1);
        assertTrue(available); assertEq(value, 750e18);
    }

    function testStaleOracleDoesNotBreakURIOrRoyaltyClaimsOrFabricateDormantState() public {
        _active(1, 950, 5); vm.warp(block.timestamp + 3601);
        (bool available, uint256 value) = nft.currentLPValue(1); assertFalse(available); assertEq(value, 0);
        uint8 state; (available, state) = nft.evolution(1); assertFalse(available); assertEq(state, 1);
        string memory json = _json(1);
        assertFalse(vm.parseJsonBool(json, ".valuation_available"));
        assertEq(_stringAttribute(json, "Evolution"), "Valuation unavailable");
        assertEq(vm.parseJsonString(json, ".image"), "ipfs://example/crimson-panels-legendary-activated.svg");
        assertEq(_uintAttribute(json, "NFT-sale royalty weight"), 3);
        ZZZRoyaltyRewards royaltyReceiver = nft.royaltyRewards();
        vm.deal(address(royaltyReceiver), 1 ether);
        vm.prank(ALICE); assertEq(royaltyReceiver.claim(1, address(0)), 1 ether - 1);
    }

    function testMigrationStatesAndUnavailableVenueKeepRightsAndReadableMetadata() public {
        _active(1, 0, 0);
        PositionStatus[3] memory states = [PositionStatus.Outbound, PositionStatus.Remote, PositionStatus.Inbound];
        for (uint256 i; i < states.length; ++i) {
            home.status = states[i]; vault.setPosition(home);
            (bool available,) = nft.currentLPValue(1); assertFalse(available);
            assertFalse(vm.parseJsonBool(_json(1), ".valuation_available"));
            assertEq(nft.royaltyRewards().weightOf(1), 1);
        }
        home.status = PositionStatus.Active; home.locationChain = block.chainid + 1; vault.setPosition(home);
        (bool available,) = nft.currentLPValue(1); assertFalse(available);
        home.locationChain = block.chainid; vault.setPosition(home); venue.setFail(true);
        (available,) = nft.currentLPValue(1); assertFalse(available);
        assertGt(bytes(nft.tokenURI(1)).length, 0);
    }

    function testERC2981UsesFivePercentSingleImmutableReceiverAndERC4906IsSupported() public {
        (address receiver, uint256 amount) = nft.royaltyInfo(999, 1 ether);
        assertEq(receiver, address(nft.royaltyRewards())); assertEq(amount, 0.05 ether);
        (receiver, amount) = nft.royaltyInfo(0, type(uint256).max); assertEq(amount, type(uint256).max / 20);
        assertEq(nft.royaltyRewards().nft(), address(nft));
        assertEq(address(nft.metadataRenderer().access()), address(access));
        assertTrue(nft.supportsInterface(0x2a55205a)); assertTrue(nft.supportsInterface(0x49064906));
        assertTrue(nft.supportsInterface(0x80ac58cd)); assertFalse(nft.supportsInterface(0xffffffff));
        _reveal(1, 0, 0); vm.recordLogs(); vm.prank(BOB); nft.refreshMetadata(1);
        Vm.Log[] memory logs = vm.getRecordedLogs(); assertEq(logs.length, 1);
        assertEq(logs[0].topics.length, 1); assertEq(logs[0].topics[0], keccak256("MetadataUpdate(uint256)"));
        assertEq(abi.decode(logs[0].data, (uint256)), 1);
    }

    function testBaseURICannotChangeAfterSealOrOverwriteConstructorCommitment() public {
        vm.expectRevert(); nft.setBaseURI("ipfs://replacement/");
        MockAccess otherAccess = new MockAccess(); ZZZNFT other = new ZZZNFT(address(otherAccess), "");
        vm.prank(BOB); vm.expectRevert(); other.setBaseURI("ipfs://unauthorized/");
        vm.expectRevert(); other.setBaseURI("https://mutable.example/");
        vm.expectRevert(); new ZZZNFT(address(otherAccess), "https://mutable.example/");
        other.setBaseURI("ipfs://fixed/"); vm.expectRevert(); other.setBaseURI("ipfs://replacement/");
        otherAccess.seal(); vm.expectRevert(); other.setBaseURI("ipfs://later/");
    }

    function _hashedId(uint256 ordinal) private view returns (uint256) {
        return uint256(keccak256(abi.encode(block.chainid, address(vault), ordinal)));
    }

    function _mintHashed(uint256 count) private {
        for (uint256 ordinal = 1; ordinal <= count; ++ordinal) vault.mint(ALICE, _hashedId(ordinal));
    }

    function _assertRefreshLogs(uint256 firstOrdinal, uint256 lastOrdinal) private {
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, lastOrdinal - firstOrdinal + 1);
        for (uint256 i; i < logs.length; ++i) {
            assertEq(logs[i].emitter, address(nft));
            assertEq(logs[i].topics.length, 1);
            assertEq(logs[i].topics[0], keccak256("MetadataUpdate(uint256)"));
            assertEq(abi.decode(logs[i].data, (uint256)), _hashedId(firstOrdinal + i));
        }
    }

    function _rejectRefreshRange(uint256 firstOrdinal, uint256 lastOrdinal) private {
        vm.recordLogs();
        vm.expectRevert(bytes4(keccak256("InvalidAmount()")));
        nft.refreshMetadataRange(firstOrdinal, lastOrdinal);
        assertEq(vm.getRecordedLogs().length, 0);
    }

    function testRefreshMetadataRangeEmitsActualHashedIDsInMintOrder() public {
        _mintHashed(4);
        assertTrue(_hashedId(2) != 2); assertTrue(_hashedId(3) != 3);
        vm.recordLogs(); vm.prank(BOB); nft.refreshMetadataRange(2, 3);
        _assertRefreshLogs(2, 3);
        assertEq(nft.mintedCount(), 4); assertEq(nft.nextToFinalize(), 1);
        assertFalse(nft.traitsReady(_hashedId(2)));
    }

    function testRefreshMetadataRangeAcceptsOneAndMaximumFifty() public {
        _mintHashed(51); assertEq(nft.MAX_METADATA_REFRESH_BATCH(), 50);
        vm.recordLogs(); vm.prank(BOB); nft.refreshMetadataRange(51, 51);
        _assertRefreshLogs(51, 51);
        // Mint setup warmed storage; cool it to measure a fresh operator call.
        vm.recordLogs(); vm.cool(address(nft)); vm.prank(BOB);
        uint256 beforeGas = gasleft(); nft.refreshMetadataRange(2, 51);
        uint256 usedGas = beforeGas - gasleft();
        _assertRefreshLogs(2, 51);
        emit log_named_uint("50-NFT metadata refresh gas (cold storage)", usedGas);
        assertLt(usedGas, 500000, "bounded metadata notification exceeds operator budget");
    }

    function testRefreshMetadataRangeRejectsEmptyZeroReversedAndUnmintedBoundsAtomically() public {
        _rejectRefreshRange(1, 1);
        _mintHashed(2);
        _rejectRefreshRange(0, 0); _rejectRefreshRange(0, 1); _rejectRefreshRange(2, 1);
        _rejectRefreshRange(1, 3); _rejectRefreshRange(3, 3);
        _rejectRefreshRange(type(uint256).max, type(uint256).max);
    }

    function testRefreshMetadataRangeRejectsFiftyOneBeforeAnyNotification() public {
        _mintHashed(51); _rejectRefreshRange(1, 51);
    }

    function testRefreshMetadataRangeIgnoresPauseTransferAndUnavailableValuation() public {
        uint256 id = _hashedId(1); _active(id, 950, 5);
        vm.prank(ALICE); nft.transferFrom(ALICE, BOB, id);
        access.setPaused(true); venue.setFail(true); vm.warp(block.timestamp + 3601);
        (bool available,) = nft.currentLPValue(id); assertFalse(available);
        vm.recordLogs(); vm.prank(address(0xC0FFEE)); nft.refreshMetadataRange(1, 1);
        _assertRefreshLogs(1, 1);
        assertEq(nft.ownerOf(id), BOB); assertTrue(nft.traitsReady(id));
        assertEq(nft.royaltyRewards().weightOf(id), 3); assertEq(vault.sharesOf(id), 100);
        (available,) = nft.currentLPValue(id); assertFalse(available);
    }

    function testRefreshMetadataRangeDoesNotCacheOrChangePriceDrivenEvolution() public {
        uint256 id = _hashedId(1); _active(id, 0, 0);
        venue.set(1000, 0); _stage(id, 2);
        feed0.set(1e7, block.timestamp, block.timestamp); _stage(id, 1);
        string memory beforeURI = nft.tokenURI(id);
        vm.prank(BOB); nft.refreshMetadataRange(1, 1);
        assertEq(nft.tokenURI(id), beforeURI); _stage(id, 1);
        venue.set(100000, 0); _stage(id, 3);
        beforeURI = nft.tokenURI(id); nft.refreshMetadataRange(1, 1);
        assertEq(nft.tokenURI(id), beforeURI); _stage(id, 3);
        assertEq(nft.royaltyRewards().weightOf(id), 1); assertEq(vault.sharesOf(id), 100);
    }

    function testPendingAndRevealedTokenURIsAreValidJSONAndNonexistentIDsRevert() public {
        vault.mint(ALICE, 1); string memory json = _json(1);
        assertEq(vm.parseJsonString(json, ".attributes[0].value"), "Unrevealed");
        assertEq(_stringAttribute(json, "Evolution"), "Dormant");
        assertEq(_uintAttribute(json, "NFT-sale royalty weight"), 0);
        vrf.fulfill(nft.requestOf(1), 0, 54); nft.finalizeTraits(1); json = _json(1);
        assertEq(vm.parseJsonString(json, ".image"), "ipfs://example/cyan-orbits-commun-dormant.svg");
        assertEq(_stringAttribute(json, "Color style"), "Monochrome");
        assertEq(_stringAttribute(json, "Palette"), "Cyan");
        assertEq(_stringAttribute(json, "Color 1"), "Cyan");
        assertEq(_stringAttribute(json, "Circuit pattern"), "Orbital rings");
        assertEq(vm.parseJsonString(json, ".lp_value_usd_18"), "0");
        vm.expectRevert(); nft.tokenURI(2); vm.expectRevert(); nft.evolution(2);
    }

    function testZeroWordsConsumeTheFullInventoryWithoutArtworkRerollsOrQuotaLoss() public {
        uint256[696] memory copies;
        for (uint256 id = 1; id <= 1000; ++id) {
            _reveal(id, 0, 0);
            uint8 rarity = nft.rarityOf(id); uint8 palette = nft.paletteOf(id); uint8 pattern = nft.patternOf(id);
            uint256 count = ++copies[uint256(rarity) * 232 + uint256(palette) * 4 + pattern];
            assertLe(count, rarity == 2 ? 1 : 4);
        }
        assertEq(nft.remainingToReveal(), 0);
        assertEq(nft.rarityOf(600), 0); assertEq(nft.rarityOf(601), 1);
        assertEq(nft.rarityOf(900), 1); assertEq(nft.rarityOf(901), 2);
    }

    function testIvoryOnyxBicolorAndTricolorMetadataNeverAffectRarityRoyaltyWeight() public {
        _reveal(1, 0, 3); // Onyx / Orbital rings, Commun.
        string memory json = _json(1);
        assertEq(_stringAttribute(json, "Palette"), "Onyx");
        assertEq(_stringAttribute(json, "Color style"), "Monochrome");
        _reveal(2, 0, 5); // Violet / Crimson / Ivory, Commun.
        json = _json(2);
        assertEq(_stringAttribute(json, "Color style"), "Tricolor");
        assertEq(_stringAttribute(json, "Palette"), "Violet / Crimson / Ivory");
        assertEq(_stringAttribute(json, "Color 1"), "Violet");
        assertEq(_stringAttribute(json, "Color 2"), "Crimson");
        assertEq(_stringAttribute(json, "Color 3"), "Ivory");
        assertEq(vm.parseJsonString(json, ".image"), "ipfs://example/violet-crimson-ivory-ribs-commun-dormant.svg");
        assertEq(_stringAttribute(json, "Circuit pattern"), "Twin circuit routes");
        vault.contribute(1, 100, 200); vault.contribute(2, 100, 200);
        assertEq(nft.royaltyRewards().weightOf(1), 1); assertEq(nft.royaltyRewards().weightOf(2), 1);
        assertEq(nft.royaltyRewards().totalWeight(), 2);
    }

    function _attributeIndex(string memory json, string memory trait) private pure returns (string memory) {
        for (uint256 i; i < 9; ++i) {
            string memory prefix = string.concat(".attributes[", vm.toString(i), "]");
            if (keccak256(bytes(vm.parseJsonString(json, string.concat(prefix, ".trait_type")))) == keccak256(bytes(trait))) {
                return string.concat(prefix, ".value");
            }
        }
        revert("Attribute missing");
    }
    function _stringAttribute(string memory json, string memory trait) private pure returns (string memory) {
        return vm.parseJsonString(json, _attributeIndex(json, trait));
    }
    function _uintAttribute(string memory json, string memory trait) private pure returns (uint256) {
        return vm.parseJsonUint(json, _attributeIndex(json, trait));
    }

    function _json(uint256 id) private view returns (string memory) {
        bytes memory data = bytes(nft.tokenURI(id)); uint256 prefix = 29;
        bytes memory decoded = new bytes((data.length - prefix) / 4 * 3); uint256 count;
        for (uint256 i = prefix; i < data.length; i += 4) {
            uint256 word = (_digit(data[i]) << 18) | (_digit(data[i + 1]) << 12) |
                (_digit(data[i + 2]) << 6) | _digit(data[i + 3]);
            decoded[count++] = bytes1(uint8(word >> 16));
            if (data[i + 2] != "=") decoded[count++] = bytes1(uint8(word >> 8));
            if (data[i + 3] != "=") decoded[count++] = bytes1(uint8(word));
        }
        bytes memory result = new bytes(count); for (uint256 i; i < count; ++i) result[i] = decoded[i];
        return string(result);
    }
    function _digit(bytes1 character) private pure returns (uint256) {
        uint8 value = uint8(character);
        if (value >= 65 && value <= 90) return value - 65;
        if (value >= 97 && value <= 122) return value - 71;
        if (value >= 48 && value <= 57) return value + 4;
        if (value == 43) return 62;
        if (value == 47) return 63;
        return 0;
    }
}
