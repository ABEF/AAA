// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZRewardReceiver} from "../src/ZZZRewardReceiver.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBridgeAdapter} from "../src/ZZZBridgeAdapter.sol";
import {IZZZCanonicalModule} from "../src/interfaces/IZZZCanonical.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus, Route, BridgeMessage, MessageKind}
    from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {PreparationPools, PreparationPolicy, PreparationVenue, PreparationRoutes, PreparationTransport,
    PreparationReceiver} from "./CanonicalPreparation.t.sol";

interface ICanonicalHandoffTest {
    function prepareImport(address sourceController) external;
    function deploymentCommitment() external view returns (bytes32);
    function freeze() external;
    function settle(uint8 slot) external;
    function settlementCursor() external view returns (uint8);
    function phase() external view returns (uint8);
    function moduleAt(uint8 slot) external view returns (address);
    function recordCount(uint256 slot) external view returns (uint256);
    function assetCount(uint256 slot) external view returns (uint256);
    function exportRows(uint8 slot, uint256 count) external;
    function importRows(uint8 slot, bytes[] calldata records) external;
    function completeImport() external;
    function fund(uint8 slot, uint256 index) external;
    function commit() external;
    function abort() external;
    function returnFunds(uint8 slot, uint256 index) external;
    function finishAbort() external;
    function stateRoot() external view returns (bytes32);
    function funded(uint8 slot, uint256 index) external view returns (bool);
}

/// @dev TEST ONLY: exact-transfer token with an armed external callback. This
/// exercises cross-module lifecycle reentry, not an approved production asset.
contract HandoffTransitionToken is MockToken {
    ZZZAccessController private callbackController;
    address private callbackTarget;
    address private triggerFrom;
    address private triggerTo;
    bytes private callbackData;
    bytes32 private callbackSalt;
    bool private armed;
    constructor() MockToken(0) {}
    function arm(ZZZAccessController controller, address target, bytes calldata data, bytes32 salt,
        address from, address to) external {
        callbackController = controller; callbackTarget = target; callbackData = data;
        callbackSalt = salt; triggerFrom = from; triggerTo = to; armed = true;
    }
    function _update(address from, address to, uint256 amount) internal override {
        super._update(from, to, amount);
        if (armed && from == triggerFrom && to == triggerTo) {
            armed = false;
            callbackController.execute(callbackTarget, 0, callbackData, bytes32(0), callbackSalt);
        }
    }
}

/// @dev TEST ONLY: exact native wrapper for frozen creator-payment settlement.
contract HandoffNativeWrapper is MockToken {
    constructor() MockToken(18) {}
    function deposit() external payable { _mint(msg.sender, msg.value); }
}

/// @notice Two independent real controller/economic systems on one local chain.
/// Venue, asset, oracle, transport and VRF fixtures are deliberately mocked.
/// These tests do not qualify a cross-chain finality verifier or real transport.
contract CanonicalHandoffTest is Test {
    struct System {
        ZZZAccessController ac;
        ZZZVault vault;
        ZZZNFT nft;
        ZZZRoyaltyRewards royalties;
        ZZZRewards rewards;
        ZZZMembership membership;
        ZZZFeeController fees;
        ZZZMigration migration;
        ZZZBridgeAdapter bridge;
        PreparationPools pools;
        PreparationVenue venue;
        MockVRF vrf;
        ICanonicalHandoffTest handoff;
    }
    System private source;
    System private destination;
    MockToken private token0;
    MockToken private token1;
    MockFeed private feed;
    bytes32 private poolId;
    uint256 private governanceNonce;
    uint256 private constant HANDOFF_CALL_GAS_BUDGET = 12_000_000;
    uint256 private peakExportGas;
    uint256 private peakSettlementGas;
    bool private segmentScaleGas;
    uint256 private peakImportGas;
    uint256 private peakFundingGas;
    uint256 private peakFreezeGas;
    uint256 private peakCommitGas;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address private constant OPERATOR = address(0x0F3A);
    address private constant GUARDIAN = address(0x600D);
    address payable private constant TREASURY = payable(address(0x7EA5));

    function setUp() public {
        vm.warp(1_000_000);
        token0 = new HandoffTransitionToken(); token1 = new MockToken(0); feed = new MockFeed(8, 1e8);
        source = _deploySystem(true);
        destination = _deploySystem(false);
        destination.handoff.prepareImport(address(source.ac));
        destination.ac.seal();
        vm.deal(ALICE, 100 ether); vm.deal(BOB, 100 ether); vm.deal(address(this), 100 ether);
        token0.mint(ALICE, 10000000); token1.mint(ALICE, 10000000);
        _approve(source); _approve(destination);
    }

    function _deploySystem(bool sealNow) private returns (System memory s) {
        return _deploySystemWithAssets(sealNow, true);
    }
    function _deploySystemWithAssets(bool sealNow, bool admitAssets) private returns (System memory s) {
        return _deploySystemWithChain(sealNow, admitAssets, block.chainid);
    }
    function _deploySystemWithChain(bool sealNow, bool admitAssets, uint256 homeChain) private returns (System memory s) {
        address[] memory proposers = new address[](1); proposers[0] = address(this);
        address[] memory executors = new address[](1); executors[0] = address(0);
        s.ac = new ZZZAccessController(1 days, proposers, executors, address(this), GUARDIAN);
        s.pools = new PreparationPools(address(s.ac));
        s.venue = new PreparationVenue(address(s.ac), address(token0), address(token1));
        s.vault = new ZZZVault(address(s.ac), homeChain, TREASURY);
        s.nft = new ZZZNFT(address(s.ac), "ipfs://canonical-handoff-fixture/");
        s.royalties = s.nft.royaltyRewards();
        s.rewards = new ZZZRewards(address(s.ac)); s.membership = new ZZZMembership(address(s.ac));
        s.fees = new ZZZFeeController(address(s.ac)); s.migration = new ZZZMigration(address(s.ac));
        ZZZOracle oracle = new ZZZOracle(address(s.ac), address(0));
        PreparationTransport transport = new PreparationTransport(address(s.ac));
        PreparationReceiver receiver = new PreparationReceiver(address(s.ac));
        receiver.configure(address(token0), false);
        s.bridge = new ZZZBridgeAdapter(address(s.ac), address(transport));
        s.ac.bind(Ids.VAULT, address(s.vault)); s.ac.bind(Ids.NFT, address(s.nft));
        s.ac.bind(Ids.LIQUIDITY, address(s.venue)); s.ac.bind(Ids.REWARDS, address(s.rewards));
        s.ac.bind(Ids.MEMBERSHIP, address(s.membership)); s.ac.bind(Ids.FEES, address(s.fees));
        s.ac.bind(Ids.STRATEGY, address(new PreparationPolicy(address(s.ac))));
        s.ac.bind(Ids.COMPOUNDER, address(new ZZZCompounder(address(s.ac))));
        s.ac.bind(Ids.BUYBACK, address(new ZZZBuyback(address(s.ac), address(token0), 1e30)));
        s.ac.bind(Ids.MIGRATION, address(s.migration)); s.ac.bind(Ids.BRIDGE, address(s.bridge));
        s.ac.bind(Ids.RECEIVER, address(receiver)); s.ac.bind(Ids.ORACLE, address(oracle));
        s.ac.bind(Ids.POOLS, address(s.pools));
        s.ac.bind(Ids.ROUTES, address(new PreparationRoutes(address(s.ac))));
        s.ac.bind(Ids.TRANSPORT, address(transport));
        oracle.setFeed(address(token0), address(feed), 3600); oracle.setFeed(address(token1), address(feed), 3600);
        if (admitAssets) {
            s.rewards.addAsset(address(token0)); s.rewards.addAsset(address(token1));
            s.nft.addRoyaltyAsset(address(token0));
        }
        s.vrf = new MockVRF();
        s.nft.configureRandomness(address(s.vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        PoolConfig memory config;
        config.key = PoolKey(address(token0), address(token1), 3000, 60, address(0));
        config.operationsEnabled = true; config.depositsEnabled = true;
        config.minDepositUSD = 1e18; config.maxPositionUSD = 1e30; config.maxSlippageBps = 100;
        poolId = keccak256(abi.encode(config.key)); s.pools.set(poolId, config);
        CanonicalFixture.bind(address(s.ac));
        s.handoff = ICanonicalHandoffTest(address(s.ac.canonicalHandoff()));
        if (sealNow) s.ac.seal();
    }

    function _approve(System memory s) private {
        vm.startPrank(ALICE);
        token0.approve(address(s.vault), type(uint256).max);
        token1.approve(address(s.vault), type(uint256).max);
        vm.stopPrank();
    }
    function _govern(System memory s, address target, bytes memory data) private {
        bytes32 salt = bytes32(++governanceNonce);
        s.ac.schedule(target, 0, data, bytes32(0), salt, 1 days);
        vm.warp(block.timestamp + 1 days);
        _fresh();
        uint256 beforeGas = gasleft();
        s.ac.execute(target, 0, data, bytes32(0), salt);
        uint256 used = beforeGas - gasleft();
        if (target == address(s.handoff)) {
            assertLt(used, HANDOFF_CALL_GAS_BUDGET, "Canonical governance operation exceeds local per-call budget");
            if (bytes4(data) == ICanonicalHandoffTest.freeze.selector && used > peakFreezeGas) peakFreezeGas = used;
            if (bytes4(data) == ICanonicalHandoffTest.commit.selector && used > peakCommitGas) peakCommitGas = used;
        }
    }
    function _governReject(System memory s, address target, bytes memory data) private {
        bytes32 salt = bytes32(++governanceNonce);
        s.ac.schedule(target, 0, data, bytes32(0), salt, 1 days);
        vm.warp(block.timestamp + 1 days);
        vm.expectRevert(); s.ac.execute(target, 0, data, bytes32(0), salt);
    }
    function _fresh() private { feed.set(1e8, block.timestamp, block.timestamp); }
    function _mint(System memory s, uint256 rarityWord, uint256 artworkWord) private returns (uint256 id) {
        vm.prank(ALICE); id = s.vault.mintDormant{value: 0.05 ether}();
        s.vrf.fulfill(s.nft.requestOf(id), rarityWord, artworkWord); s.nft.finalizeTraits(id);
    }
    function _activate(System memory s, uint256 id, uint256 amount) private {
        _fresh(); vm.prank(ALICE); s.vault.activate(id, poolId, amount, amount, 1, block.timestamp + 100);
    }
    function _seed() private returns (uint256 first, uint256 second, uint256 dormant) {
        first = _mint(source, 0, 27); _activate(source, first, 1000);
        second = _mint(source, source.nft.remainingToReveal() - 1, 45); _activate(source, second, 500);
        dormant = _mint(source, 0, 61);
        source.venue.setFees(103, 107); source.vault.collectFees(source.vault.nftBucket(first), block.timestamp + 100);
        token0.mint(address(source.royalties), 101);
        (bool ok,) = address(source.royalties).call{value: 1 ether + 3}(""); assertTrue(ok);
    }
    function _prepare() private {
        ZZZAccessController.PreparationNotice memory notice = ZZZAccessController.PreparationNotice(
            block.chainid, address(destination.ac), destination.handoff.deploymentCommitment(), keccak256("handoff fixture review"));
        _govern(source, address(source.ac), abi.encodeCall(source.ac.startPreparation, (notice)));
    }
    function _park(uint256 bucket) private {
        vm.prank(GUARDIAN); source.ac.setPaused(true);
        Position memory p = source.vault.group(bucket);
        ZZZMigration.ParkingRequest memory request = ZZZMigration.ParkingRequest(bucket, p.poolId, p.lpTokenId,
            source.vault.bucketTotalShares(bucket), p.depositUSD, source.migration.custodyEpoch(bucket),
            source.migration.parkingNonce(bucket), address(token0), address(token1), 1, 1,
            block.timestamp + 1 days + 100, keccak256("handoff parking fixture"));
        _govern(source, address(source.migration), abi.encodeCall(source.migration.park, (request)));
    }
    function _freeze(uint256 activeId) private {
        _prepare();
        if (activeId != 0 && source.vault.group(source.vault.nftBucket(activeId)).status == PositionStatus.Active) {
            _park(source.vault.nftBucket(activeId));
        }
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        _settleAll();
    }
    function _settleAll() private {
        for (uint8 slot = source.handoff.settlementCursor(); slot < 6; ++slot) {
            _coolSystem(source);
            uint256 beforeGas = gasleft();
            source.handoff.settle(slot);
            uint256 used = beforeGas - gasleft();
            assertLt(used, HANDOFF_CALL_GAS_BUDGET, "Cold settlement exceeds unchanged 12M budget");
            if (used > peakSettlementGas) peakSettlementGas = used;
        }
    }
    function _exportAll() private {
        for (uint8 slot; slot < 6; ++slot) {
            uint256 count = source.handoff.recordCount(slot);
            for (uint256 offset; offset < count; offset += 8) {
                // Each batch is a separate transaction in operation. Reset only
                // between calls; the unchanged per-call budget remains metered.
                if (segmentScaleGas) vm.resetGasMetering();
                uint256 beforeGas = gasleft();
                source.handoff.exportRows(slot, count - offset > 8 ? 8 : count - offset);
                uint256 used = beforeGas - gasleft();
                assertLt(used, HANDOFF_CALL_GAS_BUDGET, "Export batch exceeds local per-call budget");
                if (used > peakExportGas) peakExportGas = used;
            }
        }
        assertNotEq(source.handoff.stateRoot(), bytes32(0));
    }
    function _importAll() private {
        for (uint8 slot; slot < 6; ++slot) {
            IZZZCanonicalModule module = IZZZCanonicalModule(source.handoff.moduleAt(slot));
            uint256 count = source.handoff.recordCount(slot);
            for (uint256 offset; offset < count; offset += 8) {
                if (segmentScaleGas) vm.resetGasMetering();
                uint256 length = count - offset > 8 ? 8 : count - offset;
                bytes[] memory records = new bytes[](length);
                for (uint256 i; i < length; ++i) records[i] = module.canonicalExport(offset + i);
                uint256 beforeGas = gasleft();
                destination.handoff.importRows(slot, records);
                uint256 used = beforeGas - gasleft();
                assertLt(used, HANDOFF_CALL_GAS_BUDGET, "Import batch exceeds local per-call budget");
                if (used > peakImportGas) peakImportGas = used;
            }
        }
        uint256 beforeGas = gasleft();
        destination.handoff.completeImport();
        assertLt(beforeGas - gasleft(), HANDOFF_CALL_GAS_BUDGET, "Import completion exceeds local per-call budget");
    }
    function _fundAll() private {
        for (uint8 slot; slot < 6; ++slot) {
            for (uint256 i; i < source.handoff.assetCount(slot); ++i) {
                uint256 beforeGas = gasleft(); source.handoff.fund(slot, i);
                uint256 used = beforeGas - gasleft();
                assertLt(used, HANDOFF_CALL_GAS_BUDGET, "Funding transfer exceeds local per-call budget");
                if (used > peakFundingGas) peakFundingGas = used;
            }
        }
    }
    function _commit() private {
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.commit, ()));
        assertEq(source.ac.canonicalState(), 3); assertEq(destination.ac.canonicalState(), 0);
    }
    function _migrate(uint256 activeId) private { _freeze(activeId); _exportAll(); _importAll(); _fundAll(); _commit(); }
    function _logGasPeaks() private {
        emit log_named_uint("handoff.freeze.peak", peakFreezeGas);
        emit log_named_uint("handoff.settle-one-domain.cold.peak", peakSettlementGas);
        emit log_named_uint("handoff.export-8-rows.peak", peakExportGas);
        emit log_named_uint("handoff.import-8-rows.peak", peakImportGas);
        emit log_named_uint("handoff.fund-one-asset.peak", peakFundingGas);
        emit log_named_uint("handoff.commit-and-activate.peak", peakCommitGas);
    }
    function _coolSystem(System memory s) private {
        bytes32[20] memory ids = [Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,
            Ids.STRATEGY,Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.BRIDGE,Ids.RECEIVER,Ids.ORACLE,
            Ids.POOLS,Ids.ROUTES,Ids.TRANSPORT,Ids.CANONICAL,Ids.NFT_CANONICAL,Ids.VAULT_CANONICAL,Ids.FEES_CANONICAL];
        for (uint256 i; i < s.rewards.assetCount(); ++i) vm.cool(s.rewards.assets(i));
        for (uint256 i; i < s.fees.rewardReceiverCount(); ++i) vm.cool(s.fees.rewardReceivers(i));
        vm.cool(address(s.royalties));
        for (uint256 i; i < ids.length; ++i) vm.cool(s.ac.module(ids[i]));
        vm.cool(address(s.ac));
    }
    function _governColdHandoff(bytes memory data) private returns (uint256 used) {
        bytes32 salt = bytes32(++governanceNonce);
        source.ac.schedule(address(source.handoff), 0, data, bytes32(0), salt, 1 days);
        vm.warp(block.timestamp + 1 days); feed.set(1e8, block.timestamp, block.timestamp);
        _coolSystem(source); _coolSystem(destination);
        uint256 beforeGas = gasleft();
        source.ac.execute(address(source.handoff), 0, data, bytes32(0), salt);
        used = beforeGas - gasleft();
        assertLt(used, HANDOFF_CALL_GAS_BUDGET, "Cold canonical governance call exceeds unchanged 12M budget");
    }
    function _rewardRowHash(ZZZRewards ledger, uint256 id, address asset) private view returns (bytes32) {
        return keccak256(abi.encode(ledger.individual(id, asset), ledger.collective(id, asset),
            ledger.paidIndex(id, asset), ledger.fraction(id, asset), ledger.paidOwnerIndex(id, asset),
            ledger.ownerFraction(id, asset)));
    }
    function _royaltyRowHash(ZZZRoyaltyRewards ledger, uint256 id, address asset) private view returns (bytes32) {
        return keccak256(abi.encode(ledger.weightOf(id), ledger.accrued(id, asset),
            ledger.paidIndex(id, asset), ledger.fraction(id, asset)));
    }

    function testImportingDestinationCannotMintOrAllocateRights() public {
        assertEq(destination.ac.canonicalState(), 2);
        vm.prank(ALICE); vm.expectRevert(); destination.vault.mintDormant{value: 0.05 ether}();
        assertEq(destination.nft.mintedCount(), 0); assertEq(destination.membership.totalEligible(), 0);
        assertEq(source.ac.canonicalState(), 0);
    }

    function testFreezeRequiresTimelockAndFullyRevealedMintInventory() public {
        vm.prank(ALICE); source.vault.mintDormant{value: 0.05 ether}(); _prepare();
        vm.expectRevert(); source.handoff.freeze();
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        assertEq(source.ac.canonicalState(), 0);
        assertEq(source.nft.mintedCount(), 1); assertEq(source.nft.nextToFinalize(), 1);
    }

    function testFreezeRejectsLiveLiquidityAndPreservesItsCustody() public {
        uint256 id = _mint(source, 0, 0); _activate(source, id, 1000); _prepare();
        uint256 bucket = source.vault.nftBucket(id); uint256 lp = source.vault.group(bucket).lpTokenId;
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        assertEq(source.ac.canonicalState(), 0); assertEq(source.venue.ownerOf(lp), address(source.vault));
    }

    function testFrozenSourceBlocksTransfersClaimsAndOrdinarySync() public {
        (uint256 first,,) = _seed(); _freeze(first);
        assertEq(source.ac.canonicalState(), 1);
        vm.prank(ALICE); vm.expectRevert(); source.nft.transferFrom(ALICE, BOB, first);
        vm.prank(ALICE); vm.expectRevert(); source.rewards.claim(first, address(token0));
        vm.prank(ALICE); vm.expectRevert(); source.royalties.claim(first, address(0));
        vm.expectRevert(); source.royalties.sync(address(0));
        assertEq(source.nft.ownerOf(first), ALICE);
    }

    function testCompleteHandoffPreservesOwnersSharesTraitsAndBothRewardLedgers() public {
        (uint256 first, uint256 second, uint256 dormant) = _seed();
        vm.prank(ALICE); source.nft.transferFrom(ALICE, BOB, second);
        _freeze(first); _exportAll(); _importAll();
        uint256 lpFirst = source.rewards.claimable(first, address(token0));
        uint256 lpSecond = source.rewards.claimable(second, address(token0));
        uint256 royaltyFirst = source.royalties.claimable(first, address(0));
        uint256 royaltySecond = source.royalties.claimable(second, address(0));
        _fundAll(); _commit();
        assertEq(destination.nft.ownerOf(first), ALICE); assertEq(destination.nft.ownerOf(second), BOB);
        assertEq(destination.nft.ownerOf(dormant), ALICE); assertEq(destination.nft.mintedCount(), 3);
        assertEq(destination.nft.rarityOf(first), source.nft.rarityOf(first));
        assertEq(destination.nft.rarityOf(second), source.nft.rarityOf(second));
        assertEq(destination.nft.paletteOf(second), source.nft.paletteOf(second));
        assertEq(destination.nft.patternOf(second), source.nft.patternOf(second));
        assertEq(destination.vault.sharesOf(first), source.vault.sharesOf(first));
        assertEq(destination.vault.sharesOf(second), source.vault.sharesOf(second));
        assertEq(destination.vault.nftBucket(first), source.vault.nftBucket(first));
        assertEq(destination.membership.totalEligible(), 2);
        assertEq(destination.royalties.totalWeight(), 4);
        assertEq(destination.rewards.claimable(first, address(token0)), lpFirst);
        assertEq(destination.rewards.claimable(second, address(token0)), lpSecond);
        assertEq(destination.royalties.claimable(first, address(0)), royaltyFirst);
        assertEq(destination.royalties.claimable(second, address(0)), royaltySecond);
        assertEq(_rewardRowHash(destination.rewards, first, address(token0)),
            _rewardRowHash(source.rewards, first, address(token0)));
        assertEq(_rewardRowHash(destination.rewards, second, address(token0)),
            _rewardRowHash(source.rewards, second, address(token0)));
        assertEq(_royaltyRowHash(destination.royalties, first, address(0)),
            _royaltyRowHash(source.royalties, first, address(0)));
        assertEq(destination.rewards.index(address(token0)), source.rewards.index(address(token0)));
        assertEq(destination.rewards.ownerIndex(destination.vault.nftBucket(first), address(token0)),
            source.rewards.ownerIndex(source.vault.nftBucket(first), address(token0)));
        vm.prank(BOB); assertEq(destination.rewards.claim(second, address(token0)), lpSecond);
        vm.prank(BOB); assertEq(destination.royalties.claim(second, address(0)), royaltySecond);
        vm.prank(ALICE); vm.expectRevert(); source.rewards.claim(first, address(token0));
        vm.prank(BOB); vm.expectRevert(); source.royalties.claim(second, address(0));
    }

    function testDestinationNeverCopiesOldOperatorApprovalsAndRightsFollowNewOwner() public {
        (uint256 first,,) = _seed();
        vm.startPrank(ALICE); source.nft.approve(OPERATOR, first); source.nft.setApprovalForAll(OPERATOR, true); vm.stopPrank();
        _migrate(first);
        assertEq(destination.nft.getApproved(first), address(0)); assertFalse(destination.nft.isApprovedForAll(ALICE, OPERATOR));
        vm.prank(OPERATOR); vm.expectRevert(); destination.nft.transferFrom(ALICE, OPERATOR, first);
        vm.prank(ALICE); destination.nft.transferFrom(ALICE, BOB, first);
        uint256 amount = destination.rewards.claimable(first, address(token0)); assertGt(amount, 0);
        vm.prank(ALICE); vm.expectRevert(); destination.rewards.claim(first, address(token0));
        vm.prank(BOB); assertEq(destination.rewards.claim(first, address(token0)), amount);
    }

    function testMalformedRecordAndIncompleteImportCannotActivate() public {
        (uint256 first,,) = _seed(); _freeze(first); _exportAll();
        bytes[] memory wrong = new bytes[](1); wrong[0] = hex"123456";
        vm.expectRevert(); destination.handoff.importRows(0, wrong);
        vm.expectRevert(); destination.handoff.completeImport();
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.commit, ()));
        assertEq(source.ac.canonicalState(), 1); assertEq(destination.ac.canonicalState(), 2);
    }

    function testPartialFundingCannotActivateAndFundingCannotReplay() public {
        (uint256 first,,) = _seed(); _freeze(first); _exportAll(); _importAll();
        source.handoff.fund(3, 0); // One LP reward asset; principal and royalty backing are absent.
        vm.expectRevert(); source.handoff.fund(3, 0);
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.commit, ()));
        assertEq(source.ac.canonicalState(), 1); assertEq(destination.ac.canonicalState(), 2);
    }

    function testAbortBeforeFundingRestoresOnlySourceAndPermanentlyCancelsDestination() public {
        (uint256 first,,) = _seed(); _freeze(first); _exportAll(); _importAll();
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.abort, ()));
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        assertEq(source.ac.canonicalState(), 0); assertEq(destination.ac.canonicalState(), 4);
        vm.prank(ALICE); source.nft.transferFrom(ALICE, BOB, first);
        vm.prank(BOB); assertGt(source.rewards.claim(first, address(token0)), 0);
        vm.expectRevert(); destination.handoff.completeImport();
    }

    function testAbortAfterFundingRequiresExactReturnedBacking() public {
        (uint256 first,,) = _seed(); _freeze(first); _exportAll(); _importAll(); _fundAll();
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.abort, ()));
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        for (uint8 slot; slot < 6; ++slot) {
            for (uint256 i; i < source.handoff.assetCount(slot); ++i) source.handoff.returnFunds(slot, i);
        }
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        assertEq(source.ac.canonicalState(), 0); assertEq(destination.ac.canonicalState(), 4);
        vm.prank(ALICE); assertGt(source.rewards.claim(first, address(token0)), 0);
        vm.prank(ALICE); assertGt(source.royalties.claim(first, address(0)), 0);
    }

    function testRetiredSourceCannotAbortRecommitOrReopenThroughUnpause() public {
        (uint256 first,,) = _seed(); _migrate(first);
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.abort, ()));
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.commit, ()));
        // Governance may keep incident pause tooling, but cannot regain ownership authority.
        bytes memory unpause = abi.encodeCall(source.ac.setPaused, (false));
        bytes32 salt = bytes32(++governanceNonce);
        source.ac.schedule(address(source.ac), 0, unpause, bytes32(0), salt, 1 days); vm.warp(block.timestamp + 1 days);
        try source.ac.execute(address(source.ac), 0, unpause, bytes32(0), salt) {} catch {}
        assertEq(source.ac.canonicalState(), 3);
        vm.prank(ALICE); vm.expectRevert(); source.nft.transferFrom(ALICE, BOB, first);
        vm.prank(ALICE); vm.expectRevert(); source.vault.mintDormant{value: 0.05 ether}();
    }

    function testRemainingRarityAndArtworkInventoryContinueAfterMigration() public {
        _mint(source, 0, 311); _mint(source, 600, 211); _mint(source, 999, 91);
        uint256 saved = vm.snapshotState();
        uint256[6] memory expectedIds; uint8[6] memory rarity; uint8[6] memory palette; uint8[6] memory pattern;
        for (uint256 i; i < 6; ++i) {
            uint256 id = _mint(source, i * 157, i * 139 + 72); expectedIds[i] = id;
            rarity[i] = source.nft.rarityOf(id); palette[i] = source.nft.paletteOf(id); pattern[i] = source.nft.patternOf(id);
        }
        assertTrue(vm.revertToState(saved)); _migrate(0);
        for (uint256 i; i < 6; ++i) {
            uint256 id = _mint(destination, i * 157, i * 139 + 72);
            assertEq(id, expectedIds[i]); assertEq(destination.nft.rarityOf(id), rarity[i]);
            assertEq(destination.nft.paletteOf(id), palette[i]); assertEq(destination.nft.patternOf(id), pattern[i]);
        }
        assertEq(destination.nft.mintedCount(), 9); assertEq(destination.nft.remainingToReveal(), 991);
    }

    function testDestinationRoyaltyPrefundsCannotSubstituteForHandoffFundingOrRewardUsers() public {
        (uint256 first,,) = _seed();
        token0.mint(address(destination.royalties), 555);
        (bool ok,) = address(destination.royalties).call{value: 7 ether}(""); assertTrue(ok);
        _freeze(first); _exportAll(); _importAll();
        uint256 expectedNative = source.royalties.claimable(first, address(0));
        uint256 expectedToken = source.royalties.claimable(first, address(token0));
        // Sufficient unsolicited balances still cannot satisfy authenticated funding flags.
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.commit, ()));
        _fundAll(); _commit();
        assertEq(destination.royalties.claimable(first, address(0)), expectedNative);
        assertEq(destination.royalties.claimable(first, address(token0)), expectedToken);
        destination.royalties.syncAll();
        assertEq(destination.royalties.claimable(first, address(0)), expectedNative);
        assertEq(destination.royalties.claimable(first, address(token0)), expectedToken);
    }

    function testPostFreezeSourceDonationDoesNotAlterStateCommitmentOrBaseBacking() public {
        (uint256 first,,) = _seed(); _freeze(first);
        IZZZCanonicalModule royaltyModule = IZZZCanonicalModule(source.handoff.moduleAt(4));
        uint256 count = royaltyModule.canonicalCount(); bytes32 beforeRows;
        for (uint256 row; row < count; ++row) beforeRows = keccak256(abi.encode(beforeRows, royaltyModule.canonicalExport(row)));
        (address asset, uint256 backing) = royaltyModule.canonicalBacking(0); assertEq(asset, address(0));
        (bool ok,) = address(source.royalties).call{value: 3 ether}(""); assertTrue(ok);
        token0.mint(address(source.royalties), 777);
        bytes32 afterRows;
        for (uint256 row; row < count; ++row) afterRows = keccak256(abi.encode(afterRows, royaltyModule.canonicalExport(row)));
        assertEq(afterRows, beforeRows);
        (, uint256 afterBacking) = royaltyModule.canonicalBacking(0); assertEq(afterBacking, backing);
        _exportAll(); _importAll(); _fundAll(); _commit();
        assertEq(address(source.royalties).balance, 3 ether);
        assertEq(token0.balanceOf(address(source.royalties)), 777);
    }

    function testInterruptedSettlementKeepsCutoffsAndBlocksEarlyImportFundingAndClaims() public {
        (uint256 first,,) = _seed(); uint256 bucket = source.vault.nftBucket(first);
        _govern(source, address(source.fees), abi.encodeCall(source.fees.createRewardReceiver, (bucket, address(0))));
        address inbox = source.fees.rewardReceiver(bucket);
        token0.mint(inbox, 100);
        _prepare(); _park(bucket);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        assertEq(source.handoff.phase(), 8);
        vm.expectRevert(); source.handoff.settle(1);
        source.handoff.settle(0);
        vm.expectRevert(); source.handoff.settle(0);
        vm.expectRevert(); source.handoff.exportRows(0, 1);
        vm.expectRevert(); source.handoff.fund(3, 0);
        vm.expectRevert(); destination.handoff.completeImport();
        vm.prank(ALICE); vm.expectRevert(); source.rewards.claim(first, address(token0));
        vm.prank(ALICE); vm.expectRevert(); source.nft.transferFrom(ALICE, BOB, first);
        token0.mint(inbox, 777);
        token0.mint(address(source.royalties), 333);
        vm.warp(block.timestamp + 7 days);
        _settleAll();
        assertEq(source.handoff.phase(), 1);
        assertFalse(source.ac.canonicalSettling());
        assertEq(token0.balanceOf(inbox), 777);
        vm.expectRevert(); source.handoff.settle(5);
        _exportAll(); _importAll(); _fundAll(); _commit();
        assertEq(token0.balanceOf(address(source.royalties)), 333);
        assertEq(token0.balanceOf(inbox), 777);
        assertGt(destination.rewards.claimable(first, address(token0)), 0);
    }

    function testAbortBeforeSettlementReopensSourceWithoutLosingPendingReceipts() public {
        _abortDuringSettlement(0);
    }
    function testAbortAfterRoyaltySettlementReopensWithoutDoubleCrediting() public {
        _abortDuringSettlement(5);
    }
    function _abortDuringSettlement(uint8 settled) private {
        (uint256 first,,) = _seed(); uint256 bucket = source.vault.nftBucket(first);
        _govern(source, address(source.fees), abi.encodeCall(source.fees.createRewardReceiver, (bucket, address(0))));
        address inbox = source.fees.rewardReceiver(bucket);
        token0.mint(inbox, 100);
        _prepare(); _park(bucket);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        for (uint8 slot; slot < settled; ++slot) source.handoff.settle(slot);
        token0.mint(inbox, 77); token0.mint(address(source.royalties), 99);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.abort, ()));
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        assertEq(source.ac.canonicalState(), 0); assertEq(destination.ac.canonicalState(), 4);
        vm.expectRevert(); source.handoff.settle(settled);
        source.fees.syncExternal(bucket);
        assertEq(token0.balanceOf(inbox), 0);
        source.royalties.syncAll();
        uint256 royaltyBefore = source.royalties.claimable(first, address(token0));
        assertEq(royaltyBefore, 50); // 101 captured + 99 late, Commun weight 1 of 4.
        vm.prank(ALICE); uint256 royalty = source.royalties.claim(first, address(token0));
        assertEq(royalty, royaltyBefore);
        vm.prank(ALICE); assertEq(source.royalties.claim(first, address(token0)), 0);
        vm.prank(ALICE); assertGt(source.rewards.claim(first, address(token0)), 0);
        vm.prank(ALICE); source.nft.transferFrom(ALICE, BOB, first);
    }

    function testFullThousandNFTInventoryImportsExactlyOnceWithCompleteDenominators() public {
        // Minting 1,000 fixtures represents separate transactions. Exclude only
        // that setup from the test's aggregate gas cap; every handoff call below
        // remains metered with its normal per-call limits and bounded row size.
        vm.pauseGasMetering();
        (uint256 first, uint256 second,) = _seed();
        uint256 last;
        for (uint256 i = 3; i < 1000; ++i) last = _mint(source, i * 157, i * 139 + 72);
        assertEq(source.nft.remainingToReveal(), 0);
        assertEq(source.nft.rarityRemaining(0), 0); assertEq(source.nft.rarityRemaining(1), 0);
        assertEq(source.nft.rarityRemaining(2), 0);
        vm.resumeGasMetering();
        segmentScaleGas = true;
        _migrate(first);
        segmentScaleGas = false;
        assertEq(destination.nft.mintedCount(), 1000); assertEq(destination.nft.balanceOf(ALICE), 1000);
        assertEq(destination.nft.tokenAtOrdinal(1000), last); assertEq(destination.nft.ownerOf(last), ALICE);
        assertEq(destination.nft.remainingToReveal(), 0);
        assertEq(destination.membership.totalEligible(), 2); assertEq(destination.royalties.totalWeight(), 4);
        assertTrue(destination.membership.eligible(first)); assertTrue(destination.membership.eligible(second));
        assertFalse(destination.membership.eligible(last));
        assertGt(destination.rewards.claimable(first, address(token0)), 0);
        assertEq(destination.rewards.claimable(last, address(token0)), 0);
        vm.prank(ALICE); vm.expectRevert(); destination.vault.mintDormant{value: 0.05 ether}();
        bytes[] memory duplicate = new bytes[](1); duplicate[0] = hex"00";
        vm.expectRevert(); destination.handoff.importRows(0, duplicate);
        _logGasPeaks();
    }

    function testDormantImportedNFTCanActivateIntoExistingSharedBucket() public {
        (uint256 first,, uint256 dormant) = _seed(); _migrate(first);
        uint256 bucket = destination.vault.nftBucket(first);
        _govern(destination, address(destination.migration), abi.encodeCall(destination.migration.resume,
            (bucket, poolId, 1, block.timestamp + 1 days + 100)));
        _activate(destination, dormant, 100);
        assertEq(destination.vault.nftBucket(dormant), bucket); assertEq(destination.vault.bucketCount(), 1);
        assertEq(destination.membership.totalEligible(), 3); assertGt(destination.vault.sharesOf(dormant), 0);
    }

    function testActivatedSuccessorCanLaterMigrateAgainAfterNewMintsAndContributions() public {
        (uint256 first,,) = _seed(); _migrate(first);
        uint256 bucket = destination.vault.nftBucket(first);
        _govern(destination, address(destination.migration), abi.encodeCall(destination.migration.resume,
            (bucket, poolId, 1, block.timestamp + 1 days + 100)));
        uint256 newId = _mint(destination, 27, 87); _activate(destination, newId, 100);
        vm.prank(ALICE); destination.vault.increase(first, 50, 50, 1, block.timestamp + 100);
        uint256 expectedShares = destination.vault.sharesOf(first);
        source = destination; destination = _deploySystem(false);
        destination.handoff.prepareImport(address(source.ac)); destination.ac.seal(); _approve(destination);
        _migrate(first);
        assertEq(destination.nft.mintedCount(), 4); assertEq(destination.nft.ownerOf(newId), ALICE);
        assertEq(destination.vault.sharesOf(first), expectedShares);
        assertEq(destination.vault.nftBucket(newId), bucket); assertEq(destination.membership.totalEligible(), 3);
        assertEq(destination.nft.mintOrdinalOf(newId), 4);
    }

    function testFreezeInsideLegacyFundingCallbackCannotCountOnePaymentTwice() public {
        (uint256 first,,) = _seed(); uint256 bucket = source.vault.nftBucket(first);
        _govern(source, address(source.fees), abi.encodeCall(source.fees.createRewardReceiver, (bucket, address(0))));
        _migrate(first); System memory retired = source;
        address legacyInbox = retired.fees.rewardReceiver(bucket);
        token0.mint(legacyInbox, 100); retired.fees.syncExternal(bucket);
        assertEq(retired.fees.lateGross(bucket, address(token0)), 100);
        source = destination; destination = _deploySystem(false);
        destination.handoff.prepareImport(address(source.ac)); destination.ac.seal();
        _prepare();
        bytes memory data = abi.encodeCall(source.handoff.freeze, ()); bytes32 salt = bytes32(++governanceNonce);
        source.ac.schedule(address(source.handoff), 0, data, bytes32(0), salt, 1 days);
        vm.warp(block.timestamp + 1 days);
        HandoffTransitionToken(address(token0)).arm(source.ac, address(source.handoff), data, salt,
            address(retired.fees), address(source.fees));
        vm.expectRevert(); retired.fees.forwardLate(bucket, address(token0));
        assertEq(source.ac.canonicalState(), 0);
        assertEq(retired.fees.lateGross(bucket, address(token0)), 100);
        assertEq(source.fees.lateGross(bucket, address(token0)), 0);
        assertEq(destination.ac.canonicalState(), 2);
    }

    function testCrossChainNoticeDoesNotAuthorizeUnverifiedFreezeOrExport() public {
        _mint(source, 0, 0);
        ZZZAccessController.PreparationNotice memory notice = ZZZAccessController.PreparationNotice(
            block.chainid + 1, address(0xCA11), keccak256("unqualified remote deployment"), keccak256("notice only"));
        _govern(source, address(source.ac), abi.encodeCall(source.ac.startPreparation, (notice)));
        _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        assertEq(source.ac.canonicalState(), 0); assertEq(source.handoff.stateRoot(), bytes32(0));
        vm.expectRevert(); source.handoff.exportRows(0, 1);
    }

    function testAnyHistoricalBridgeUseRequiresSeparateAuthenticatedDrainDesign() public {
        uint256 id = _mint(source, 0, 0);
        bytes32 routeId = keccak256("fixture historical acknowledgement"); Route memory route;
        route.sourceChain = block.chainid; route.sourceAdapter = address(source.bridge);
        route.sourceVault = address(source.vault); route.sourceReceiver = source.ac.module(Ids.RECEIVER);
        route.destinationChain = block.chainid + 1; route.destinationAdapter = address(0x5150);
        route.destinationVault = address(0x5151); route.destinationReceiver = address(0x5152);
        PreparationRoutes(source.ac.module(Ids.ROUTES)).set(routeId, route);
        BridgeMessage memory message; message.version = 3; message.kind = MessageKind.Acknowledgement;
        message.routeId = routeId; message.migrationId = keccak256("test-only old channel");
        // Mock receiver authentication only: this creates real adapter history,
        // not evidence of a real remote provider or completed channel shutdown.
        vm.prank(source.ac.module(Ids.RECEIVER)); source.bridge.send(message);
        assertEq(source.bridge.nonce(), 1);
        _prepare(); _governReject(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        assertEq(source.ac.canonicalState(), 0); assertEq(source.nft.ownerOf(id), ALICE);
        assertEq(source.vault.bucketCount(), 0);
    }

    function testUnsealedSameChainDestinationCannotBeAnnouncedAsExecutableHandoff() public {
        System memory unsealed = _deploySystem(false); unsealed.handoff.prepareImport(address(source.ac));
        ZZZAccessController.PreparationNotice memory notice = ZZZAccessController.PreparationNotice(
            block.chainid, address(unsealed.ac), keccak256("unsealed configuration can still change"), keccak256("review"));
        _governReject(source, address(source.ac), abi.encodeCall(source.ac.startPreparation, (notice)));
        assertFalse(source.ac.preparationActive()); assertEq(source.ac.canonicalState(), 0);
    }

    function testAbortedSourceCanUseFreshDestinationWithoutReusingOldRootsOrFundingFlags() public {
        (uint256 first,,) = _seed(); _freeze(first); _exportAll(); _importAll();
        bytes32 oldRoot = source.handoff.stateRoot(); System memory cancelled = destination;
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.abort, ()));
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        vm.prank(ALICE); source.nft.transferFrom(ALICE, BOB, first);
        destination = _deploySystem(false); destination.handoff.prepareImport(address(source.ac)); destination.ac.seal();
        _migrate(first);
        assertNotEq(source.handoff.stateRoot(), oldRoot); assertEq(destination.nft.ownerOf(first), BOB);
        assertEq(cancelled.ac.canonicalState(), 4); assertEq(destination.ac.canonicalState(), 0);
        vm.expectRevert(); cancelled.handoff.completeImport();
    }

    function testEmptyCollectionAndZeroLPAssetsCanMigrateWithoutInventingBacking() public {
        source = _deploySystemWithAssets(true, false);
        destination = _deploySystemWithAssets(false, false);
        destination.handoff.prepareImport(address(source.ac)); destination.ac.seal();
        _migrate(0);
        assertEq(destination.nft.mintedCount(), 0);
        assertEq(destination.nft.remainingToReveal(), 1000);
        assertEq(destination.rewards.assetCount(), 0);
        assertEq(destination.membership.totalEligible(), 0);
        assertEq(destination.royalties.totalWeight(), 0);
        assertEq(destination.handoff.assetCount(1), 0);
        assertEq(destination.handoff.assetCount(3), 0);
        assertEq(destination.handoff.assetCount(4), 1); // Native royalty slot, zero backing.
        uint256 id = _mint(destination, 0, 0);
        assertEq(destination.nft.ownerOf(id), ALICE); assertEq(destination.nft.mintedCount(), 1);
    }

    function testSatelliteConfiguredDestinationCannotPrepareCanonicalImport() public {
        destination = _deploySystemWithChain(false, true, block.chainid + 1);
        vm.expectRevert(); destination.handoff.prepareImport(address(source.ac));
        assertEq(destination.ac.canonicalState(), 0);
        assertEq(source.ac.canonicalState(), 0);
        uint256 id = _mint(source, 0, 0); assertEq(source.nft.ownerOf(id), ALICE);
    }

    function testPartialFundingAbortReturnsOnlyTransferredBacking() public {
        (uint256 first,,) = _seed(); _freeze(first); _exportAll(); _importAll();
        uint256 principal = token0.balanceOf(address(source.vault));
        uint256 rewards = token0.balanceOf(address(source.rewards));
        source.handoff.fund(1, 0);
        assertEq(token0.balanceOf(address(source.vault)), 0);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.abort, ()));
        source.handoff.returnFunds(1, 0);
        vm.expectRevert(); source.handoff.returnFunds(3, 0);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        assertEq(token0.balanceOf(address(source.vault)), principal);
        assertEq(token0.balanceOf(address(source.rewards)), rewards);
        assertEq(source.ac.canonicalState(), 0); assertEq(destination.ac.canonicalState(), 4);
    }

    function testFundingCallbackCannotAbortHalfwayThroughExactPrincipalTransfer() public {
        (uint256 first,,) = _seed(); _freeze(first); _exportAll(); _importAll();
        bytes memory data = abi.encodeCall(source.handoff.abort, ()); bytes32 salt = bytes32(++governanceNonce);
        source.ac.schedule(address(source.handoff), 0, data, bytes32(0), salt, 1 days);
        vm.warp(block.timestamp + 1 days);
        uint256 principal = token0.balanceOf(address(source.vault));
        HandoffTransitionToken(address(token0)).arm(source.ac, address(source.handoff), data, salt,
            address(source.vault), destination.handoff.moduleAt(1));
        vm.expectRevert(); source.handoff.fund(1, 0);
        assertFalse(source.handoff.funded(1, 0));
        assertEq(token0.balanceOf(address(source.vault)), principal);
        assertEq(token0.balanceOf(address(destination.vault)), 0);
        assertEq(source.ac.canonicalState(), 1); assertEq(destination.ac.canonicalState(), 2);
        source.ac.execute(address(source.handoff), 0, data, bytes32(0), salt);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        assertEq(source.ac.canonicalState(), 0); assertEq(destination.ac.canonicalState(), 4);
    }

    function testProtectedInboxTokensNativeAndSuccessorPrefundsStayQuarantined() public {
        (uint256 first,,) = _seed(); uint256 bucket = source.vault.nftBucket(first);
        address factory = address(source.fees.receiverFactory());
        address predicted = vm.computeCreateAddress(factory, vm.getNonce(factory));
        token0.mint(predicted, 11); token1.mint(predicted, 13); vm.deal(predicted, 17);
        _govern(source, address(source.fees), abi.encodeCall(source.fees.createRewardReceiver, (bucket, address(0))));
        assertEq(source.fees.rewardReceiver(bucket), predicted);
        token0.mint(predicted, 100); token1.mint(predicted, 120);
        factory = address(destination.fees.receiverFactory());
        address successorInbox = vm.computeCreateAddress(factory, vm.getNonce(factory));
        token0.mint(successorInbox, 19); token1.mint(successorInbox, 23); vm.deal(successorInbox, 29);
        _freeze(first);
        assertEq(source.fees.totalExternalFunded(bucket, address(token0)), 100);
        assertEq(source.fees.totalExternalFunded(bucket, address(token1)), 120);
        token0.mint(predicted, 40); // Arrives after the frozen cutoff.
        _exportAll(); _importAll(); _fundAll(); _commit();
        assertEq(destination.fees.rewardReceiver(bucket), successorInbox);
        ZZZRewardReceiver inbox = ZZZRewardReceiver(payable(successorInbox));
        assertEq(inbox.protected0(), 30); assertEq(inbox.protected1(), 36); assertEq(inbox.protectedNative(), 46);
        assertEq(token0.balanceOf(successorInbox), 30); assertEq(token1.balanceOf(successorInbox), 36);
        assertEq(successorInbox.balance, 46);
        (uint256 pending0, uint256 pending1) = inbox.pending(); assertEq(pending0, 0); assertEq(pending1, 0);
        assertEq(token0.balanceOf(predicted), 40); assertEq(predicted.balance, 0);
        source.fees.syncExternal(bucket); assertEq(source.fees.lateGross(bucket, address(token0)), 40);
        source.fees.forwardLate(bucket, address(token0));
        assertEq(destination.fees.totalExternalFunded(bucket, address(token0)), 140);
        assertEq(source.fees.lateGross(bucket, address(token0)), 0);
        vm.expectRevert(); source.fees.forwardLate(bucket, address(token0));
        assertEq(inbox.protected0(), 30); assertEq(inbox.protectedNative(), 46);
    }

    function testRetiredRoyaltyInboxForwardsOnlyRemainingReceiptsWithoutDuplicatingClaims() public {
        (uint256 first,,) = _seed(); _freeze(first);
        uint256 expectedNative = source.royalties.claimable(first, address(0));
        uint256 expectedToken = source.royalties.claimable(first, address(token0));
        _exportAll(); _importAll(); _fundAll(); _commit();
        (bool ok,) = address(source.royalties).call{value: 400}(""); assertTrue(ok);
        token0.mint(address(source.royalties), 400);
        source.royalties.forwardLate(address(0)); source.royalties.forwardLate(address(token0));
        assertEq(address(source.royalties).balance, 0); assertEq(token0.balanceOf(address(source.royalties)), 0);
        assertEq(destination.royalties.claimable(first, address(0)), expectedNative + 100);
        assertEq(destination.royalties.claimable(first, address(token0)), expectedToken + 100);
        assertEq(source.royalties.forwardLate(address(0)), 0);
        vm.prank(ALICE); assertEq(destination.royalties.claim(first, address(0)), expectedNative + 100);
        vm.prank(ALICE); assertEq(destination.royalties.claim(first, address(token0)), expectedToken + 100);
        assertEq(destination.royalties.claimable(first, address(0)), 0);
        assertEq(destination.royalties.claimable(first, address(token0)), 0);
    }

    function testMaximumLocalAssetAndBucketDomainsPreserveEveryImportedLedger() public {
        (uint256 first,,) = _seed();
        destination = _deploySystem(false);
        MockToken[30] memory extra;
        for (uint256 i; i < extra.length; ++i) {
            extra[i] = new MockToken(0);
            _govern(source, address(source.rewards), abi.encodeCall(source.rewards.addAsset, (address(extra[i]))));
            destination.rewards.addAsset(address(extra[i]));
            extra[i].mint(address(source.vault), i + 1);
            extra[i].mint(address(source.rewards), i + 2);
            extra[i].mint(address(source.fees), i + 3);
            if (i < 15) {
                _govern(source, address(source.nft), abi.encodeCall(source.nft.addRoyaltyAsset, (address(extra[i]))));
                destination.nft.addRoyaltyAsset(address(extra[i]));
                extra[i].mint(address(source.royalties), 40 * (i + 1));
            }
        }
        bytes32 initialPool = poolId;
        PoolConfig memory config = source.pools.get(poolId);
        for (uint256 i = 1; i < 4; ++i) {
            config.key.fee = uint24(3000 + i);
            poolId = keccak256(abi.encode(config.key)); source.pools.set(poolId, config); destination.pools.set(poolId, config);
            uint256 id = _mint(source, i * 79, i * 133); _activate(source, id, 100);
        }
        poolId = initialPool;
        for (uint256 i; i < source.vault.bucketCount(); ++i) {
            uint256 bucket = source.vault.bucketAt(i);
            _govern(source, address(source.fees), abi.encodeCall(source.fees.createRewardReceiver, (bucket, address(0))));
            token0.mint(source.fees.rewardReceiver(bucket), 100 + i);
            token1.mint(source.fees.rewardReceiver(bucket), 120 + i);
        }
        destination.handoff.prepareImport(address(source.ac)); destination.ac.seal();
        _prepare();
        for (uint256 i; i < source.vault.bucketCount(); ++i) _park(source.vault.bucketAt(i));
        uint256 freezeGas = _governColdHandoff(abi.encodeCall(source.handoff.freeze, ()));
        emit log_named_uint("handoff.4-buckets.32-assets.4-inboxes.17-royalties.freeze.cold", freezeGas);
        _settleAll();
        uint256 expectedRoyalty = source.royalties.claimable(first, address(extra[14]));
        _exportAll(); _importAll(); _fundAll();
        uint256 commitGas = _governColdHandoff(abi.encodeCall(source.handoff.commit, ()));
        emit log_named_uint("handoff.4-buckets.32-assets.4-inboxes.17-royalties.commit.cold", commitGas);
        assertEq(source.ac.canonicalState(), 3); assertEq(destination.ac.canonicalState(), 0);
        assertEq(destination.vault.bucketCount(), 4); assertEq(destination.rewards.assetCount(), 32);
        assertEq(destination.royalties.assetCount(), 17);
        assertEq(destination.membership.totalEligible(), 5);
        for (uint256 i; i < extra.length; ++i) {
            assertEq(extra[i].balanceOf(address(destination.vault)), i + 1);
            assertEq(extra[i].balanceOf(address(destination.rewards)), i + 2);
            assertEq(extra[i].balanceOf(address(destination.fees)), i + 3);
            assertEq(destination.rewards.claimable(first, address(extra[i])), 0);
        }
        assertEq(destination.royalties.claimable(first, address(extra[14])), expectedRoyalty);
        _logGasPeaks();
    }

    function testLegacyReceiptsQueuedWhileSuccessorFrozenRemainBackedAcrossNextHandoff() public {
        (uint256 first,,) = _seed(); uint256 bucket = source.vault.nftBucket(first);
        _govern(source, address(source.fees), abi.encodeCall(source.fees.createRewardReceiver, (bucket, address(0))));
        _migrate(first); System memory ancestor = source;
        source = destination; destination = _deploySystem(false);
        destination.handoff.prepareImport(address(source.ac)); destination.ac.seal();
        _freeze(first); _exportAll(); bytes32 rootBeforeLate = source.handoff.stateRoot();
        token0.mint(ancestor.fees.rewardReceiver(bucket), 100);
        ancestor.fees.syncExternal(bucket); ancestor.fees.forwardLate(bucket, address(token0));
        assertEq(source.fees.lateGross(bucket, address(token0)), 100);
        (bool ok,) = address(ancestor.royalties).call{value: 400}(""); assertTrue(ok);
        ancestor.royalties.forwardLate(address(0));
        uint256 royaltyBeforeLate = source.royalties.claimable(first, address(0));
        _importAll(); _fundAll(); _commit();
        assertEq(source.handoff.stateRoot(), rootBeforeLate);
        assertEq(token0.balanceOf(address(source.fees)), 100);
        assertEq(address(source.royalties).balance, 400);
        source.fees.forwardLate(bucket, address(token0)); source.royalties.forwardLate(address(0));
        assertEq(destination.fees.totalExternalFunded(bucket, address(token0)), 100);
        assertEq(destination.royalties.claimable(first, address(0)), royaltyBeforeLate + 100);
        assertEq(token0.balanceOf(address(source.fees)), 0); assertEq(address(source.royalties).balance, 0);
        vm.expectRevert(); source.fees.forwardLate(bucket, address(token0));
    }

    function testPendingNativeCreatorPaymentIsWrappedAndAllocatedOnceAtFreeze() public {
        token0 = new HandoffNativeWrapper();
        source = _deploySystem(true); destination = _deploySystem(false);
        destination.handoff.prepareImport(address(source.ac)); destination.ac.seal();
        token0.mint(ALICE, 10000000); _approve(source); _approve(destination);
        (uint256 first,,) = _seed(); uint256 bucket = source.vault.nftBucket(first);
        _govern(source, address(source.fees), abi.encodeCall(source.fees.createRewardReceiver, (bucket, address(token0))));
        address inbox = source.fees.rewardReceiver(bucket);
        (bool ok,) = inbox.call{value: 1 ether + 7}(""); assertTrue(ok);
        _freeze(first);
        assertEq(inbox.balance, 0); assertEq(token0.balanceOf(inbox), 0);
        assertEq(address(token0).balance, 1 ether + 7);
        assertEq(source.fees.totalExternalFunded(bucket, address(token0)), 1 ether + 7);
        uint256 expected = source.rewards.claimable(first, address(token0));
        _exportAll(); _importAll(); _fundAll(); _commit();
        assertEq(destination.rewards.claimable(first, address(token0)), expected);
        assertEq(destination.fees.totalExternalFunded(bucket, address(token0)), 1 ether + 7);
        destination.fees.syncExternal(bucket);
        assertEq(destination.fees.totalExternalFunded(bucket, address(token0)), 1 ether + 7);
        vm.prank(ALICE); assertEq(destination.rewards.claim(first, address(token0)), expected);
        assertEq(destination.rewards.claimable(first, address(token0)), 0);
    }
}
