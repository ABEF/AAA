// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IZZZAccess, IZZZVault} from "./interfaces/IZZZ.sol";
import {IZZZCanonicalModule} from "./interfaces/IZZZCanonical.sol";
import {Ids} from "./libraries/ZZZTypes.sol";

interface ICanonicalController is IZZZAccess {
    function bootstrap() external view returns (address);
    function preparationHash() external view returns (bytes32);
    function preparationReadyDestination() external view returns (bool);
    function preparationNotice() external view returns (uint256,address,bytes32,bytes32);
    function canonicalTransition(uint8 state, bool settling, bool clearPreparation) external;
}
interface ICanonicalHelpers {
    function canonicalModule() external view returns (address);
    function royaltyRewards() external view returns (address);
    function canonicalRetire() external;
}

/// @notice Fixed, bounded handoff coordinator. This first transport is direct
/// same-chain custody with atomic retirement/activation. It cannot attest remote
/// consensus or move assets through an unqualified cross-chain provider.
/// Governance cannot supply accounting rows or use a generic withdrawal target.
contract ZZZCanonicalHandoff is ReentrancyGuard {
    uint256 public constant SLOTS = 6;
    uint256 public constant MAX_ROWS = 8;
    bytes32 public constant SCHEMA = keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4");
    ICanonicalController public immutable access;
    // 0 idle, 1 frozen/exporting, 2 imported, 3 retired, 4 importing,
    // 5 active replacement, 6 aborting, 7 cancelled replacement, 8 captured/settling.
    uint8 public phase;
    uint8 public settlementCursor;
    address public incomingSource;
    address public destinationController;
    bytes32 public handoffId;
    bytes32 public stateRoot;
    bool public importComplete;
    uint256[6] public recordCount;
    uint256[6] public assetCount;
    uint256[6] public exportCursor;
    uint256[6] public importCursor;
    bytes32[6] public exportRoot;
    bytes32[6] public importRoot;
    mapping(uint8 => mapping(uint256 => bool)) public funded;
    mapping(uint8 => mapping(uint256 => bool)) public incomingFunded;
    mapping(uint8 => mapping(uint256 => bool)) public returned;
    bytes32 private destinationDeployment;
    error Unauthorized();
    error InvalidState();
    error InvalidRecord();
    error InvalidBacking();
    error UnsupportedTransport();
    event ImportPrepared(address indexed sourceController);
    event Frozen(bytes32 indexed handoff, address indexed destination);
    event DomainSettled(bytes32 indexed handoff, uint8 indexed slot);
    event RecordExported(bytes32 indexed handoff, uint8 indexed slot, uint256 indexed row, bytes record);
    event SnapshotCommitted(bytes32 indexed handoff, bytes32 stateRoot);
    event RecordImported(bytes32 indexed handoff, uint8 indexed slot, uint256 indexed row);
    event BackingTransferred(bytes32 indexed handoff, uint8 indexed slot, uint256 indexed index, address asset, uint256 amount);
    event Retired(bytes32 indexed handoff, address indexed successor, bytes32 stateRoot);
    event Activated(bytes32 indexed handoff, address indexed source, bytes32 stateRoot);
    event AbortStarted(bytes32 indexed handoff);
    event BackingReturned(bytes32 indexed handoff, uint8 indexed slot, uint256 indexed index);
    event Aborted(bytes32 indexed handoff);

    constructor(address controller) { access = ICanonicalController(controller); }
    modifier governance() {
        if (msg.sender != access.governance() || !access.isSealed()) revert Unauthorized();
        _;
    }
    function moduleAt(uint8 slot) public view returns (address) {
        if (slot == 0) return access.module(Ids.NFT_CANONICAL);
        if (slot == 1) return ICanonicalHelpers(access.module(Ids.VAULT)).canonicalModule();
        if (slot == 2) return access.module(Ids.MEMBERSHIP);
        if (slot == 3) return access.module(Ids.REWARDS);
        if (slot == 4) return ICanonicalHelpers(access.module(Ids.NFT)).royaltyRewards();
        if (slot == 5) return access.module(Ids.FEES_CANONICAL);
        revert InvalidState();
    }
    function _module(uint8 slot) private view returns (IZZZCanonicalModule) {
        return IZZZCanonicalModule(moduleAt(slot));
    }
    function _peer(address controller) private view returns (ZZZCanonicalHandoff) {
        return ZZZCanonicalHandoff(IZZZAccess(controller).canonicalHandoff());
    }
    /// @notice Review commitment to the exact destination controller, code,
    /// bound modules and immutable helpers. Review still has to establish that
    /// the selected implementation is safe; a code hash is not a security proof.
    function deploymentCommitment() public view returns (bytes32 result) {
        if (!access.isSealed()) revert InvalidState();
        result = keccak256(abi.encode(SCHEMA, block.chainid, address(access), address(this),
            address(access).codehash, address(this).codehash, incomingSource));
        bytes32[16] memory ids = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP,
            Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION,
            Ids.ORACLE, Ids.POOLS, Ids.CANONICAL,
            Ids.NFT_CANONICAL, Ids.VAULT_CANONICAL, Ids.FEES_CANONICAL];
        for (uint256 i; i < ids.length; ++i) {
            address target = access.module(ids[i]);
            if (target.code.length == 0) revert InvalidState();
            result = keccak256(abi.encode(result, ids[i], target, target.codehash));
        }
        for (uint8 slot; slot < SLOTS; ++slot) {
            address target = moduleAt(slot);
            result = keccak256(abi.encode(result, slot, target, target.codehash));
        }
    }
    /// @notice Only an unused, unsealed deployment can become an inert importer.
    /// Its ordinary economic entrypoints remain unavailable until activation.
    function prepareImport(address sourceController) external nonReentrant {
        if (access.isSealed() || msg.sender != access.bootstrap() || phase != 0 ||
            sourceController == address(access) || sourceController.code.length == 0 ||
            !IZZZAccess(sourceController).isSealed()) revert Unauthorized();
        if (IZZZVault(access.module(Ids.VAULT)).canonicalChainId() != block.chainid) revert UnsupportedTransport();
        if (_peer(sourceController).SCHEMA() != SCHEMA) revert UnsupportedTransport();
        incomingSource = sourceController;
        phase = 4;
        access.canonicalTransition(2, false, false);
        emit ImportPrepared(sourceController);
    }
    function freeze() external governance nonReentrant {
        if ((phase != 0 && phase != 5) || !access.preparationActive() || access.canonicalState() != 0 ||
            !access.preparationReadyDestination())
            revert InvalidState();
        (uint256 chain, address destination, bytes32 deployment,) = access.preparationNotice();
        if (chain != block.chainid) revert UnsupportedTransport();
        ZZZCanonicalHandoff peer = _peer(destination);
        if (!IZZZAccess(destination).isSealed() || peer.SCHEMA() != SCHEMA || peer.phase() != 4 ||
            peer.incomingSource() != address(access) || peer.deploymentCommitment() != deployment)
            revert InvalidState();
        if (IZZZVault(IZZZAccess(destination).module(Ids.VAULT)).canonicalChainId() != block.chainid)
            revert UnsupportedTransport();
        // Every bucket must be parked and have no active custody handoff.
        // Capture enforces that boundary; no retired v3 channel is admitted.
        destinationController = destination;
        destinationDeployment = deployment;
        handoffId = keccak256(abi.encode(SCHEMA, block.chainid, address(access), address(this),
            destination, address(peer), access.preparationHash(), deployment));
        phase = 8;
        settlementCursor = 0;
        stateRoot = bytes32(0);
        // Establish the guard BEFORE any external balance observation. Capture
        // every module first, then process only those immutable cutoffs.
        access.canonicalTransition(1, false, false);
        for (uint8 slot; slot < SLOTS; ++slot) _module(slot).canonicalCapture();
        for (uint8 slot; slot < SLOTS; ++slot) {
            recordCount[slot] = _module(slot).canonicalCount();
            assetCount[slot] = _module(slot).canonicalAssetCount();
            if (recordCount[slot] == 0 || assetCount[slot] > 256)
                revert InvalidState();
            exportCursor[slot] = 0;
            exportRoot[slot] = bytes32(0);
            for (uint256 index; index < assetCount[slot]; ++index) {
                funded[slot][index] = false;
                returned[slot][index] = false;
            }
        }
        peer.bindFrozen(handoffId);
        emit Frozen(handoffId, destination);
    }
    /// @notice Process each captured domain exactly once in fixed order. No
    /// export, funding or activation is possible until all six have settled.
    /// Cutoffs were captured atomically at freeze; later receipts stay outside
    /// this snapshot even if the operator stops between settlement calls.
    function settle(uint8 slot) external nonReentrant {
        if (phase != 8 || slot != settlementCursor || slot >= SLOTS) revert InvalidState();
        access.canonicalTransition(1, true, false);
        _module(slot).canonicalSettle();
        access.canonicalTransition(1, false, false);
        settlementCursor = slot + 1;
        if (settlementCursor == SLOTS) phase = 1;
        emit DomainSettled(handoffId, slot);
    }
    function bindFrozen(bytes32 id) external {
        if (phase != 4 || msg.sender != address(_peer(incomingSource)) || handoffId != bytes32(0))
            revert Unauthorized();
        handoffId = id;
        ZZZCanonicalHandoff source = ZZZCanonicalHandoff(msg.sender);
        if (source.handoffId() != id || source.destinationController() != address(access)) revert InvalidState();
        for (uint8 slot; slot < SLOTS; ++slot) {
            recordCount[slot] = source.recordCount(slot);
            assetCount[slot] = source.assetCount(slot);
        }
    }
    function _next(bytes32 previous, uint8 slot, uint256 row, bytes memory record) private view returns (bytes32) {
        return keccak256(abi.encode(handoffId, slot, row, previous, keccak256(record)));
    }
    function exportRows(uint8 slot, uint256 count) external nonReentrant {
        if (phase != 1 || slot >= SLOTS || count == 0 || count > MAX_ROWS ||
            exportCursor[slot] + count > recordCount[slot]) revert InvalidState();
        uint256 end = exportCursor[slot] + count;
        for (uint256 row = exportCursor[slot]; row < end; ++row) {
            bytes memory record = _module(slot).canonicalExport(row);
            exportRoot[slot] = _next(exportRoot[slot], slot, row, record);
            emit RecordExported(handoffId, slot, row, record);
        }
        exportCursor[slot] = end;
        bool complete = true;
        for (uint8 i; i < SLOTS; ++i) if (exportCursor[i] != recordCount[i]) complete = false;
        if (complete) {
            stateRoot = keccak256(abi.encode(handoffId, recordCount, assetCount, exportRoot));
            emit SnapshotCommitted(handoffId, stateRoot);
        }
    }
    function importRows(uint8 slot, bytes[] calldata records) external nonReentrant {
        if (phase != 4 || slot >= SLOTS || records.length == 0 || records.length > MAX_ROWS ||
            importCursor[slot] + records.length > recordCount[slot]) revert InvalidState();
        ZZZCanonicalHandoff source = _peer(incomingSource);
        if (source.phase() != 1 || source.stateRoot() == bytes32(0) || source.handoffId() != handoffId)
            revert InvalidState();
        IZZZCanonicalModule sourceModule = IZZZCanonicalModule(source.moduleAt(slot));
        for (uint256 i; i < records.length; ++i) {
            uint256 row = importCursor[slot]++;
            if (keccak256(records[i]) != keccak256(sourceModule.canonicalExport(row))) revert InvalidRecord();
            _module(slot).canonicalImport(row, records[i]);
            importRoot[slot] = _next(importRoot[slot], slot, row, records[i]);
            emit RecordImported(handoffId, slot, row);
        }
    }
    function completeImport() external nonReentrant {
        if (phase != 4) revert InvalidState();
        ZZZCanonicalHandoff source = _peer(incomingSource);
        for (uint8 slot; slot < SLOTS; ++slot) {
            if (importCursor[slot] != recordCount[slot] || importRoot[slot] != source.exportRoot(slot) ||
                _module(slot).canonicalCount() != recordCount[slot] ||
                _module(slot).canonicalAssetCount() != assetCount[slot]) revert InvalidRecord();
        }
        stateRoot = keccak256(abi.encode(handoffId, recordCount, assetCount, importRoot));
        if (source.phase() != 1 || stateRoot == bytes32(0) || stateRoot != source.stateRoot()) revert InvalidRecord();
        importComplete = true;
        phase = 2;
    }
    function _balance(address asset, address owner) private view returns (uint256) {
        return asset == address(0) ? owner.balance : IERC20(asset).balanceOf(owner);
    }
    function fund(uint8 slot, uint256 index) external nonReentrant {
        if (phase != 1 || slot >= SLOTS || index >= assetCount[slot] || funded[slot][index]) revert InvalidState();
        ZZZCanonicalHandoff peer = _peer(destinationController);
        if (peer.phase() != 2 || peer.stateRoot() != stateRoot || stateRoot == bytes32(0)) revert InvalidState();
        (address asset, uint256 amount) = _module(slot).canonicalBacking(index);
        IZZZCanonicalModule destination = IZZZCanonicalModule(peer.moduleAt(slot));
        (address otherAsset, uint256 otherAmount) = destination.canonicalBacking(index);
        if (otherAsset != asset || otherAmount != amount) revert InvalidBacking();
        funded[slot][index] = true;
        uint256 beforeBalance = _balance(asset, address(destination));
        _module(slot).canonicalRelease(index, address(destination));
        if (_balance(asset, address(destination)) != beforeBalance + amount) revert InvalidBacking();
        peer.acceptFunding(slot, index);
        emit BackingTransferred(handoffId, slot, index, asset, amount);
    }
    function acceptFunding(uint8 slot, uint256 index) external nonReentrant {
        ZZZCanonicalHandoff source = _peer(incomingSource);
        if (msg.sender != address(source) || phase != 2 || slot >= SLOTS || index >= assetCount[slot] ||
            incomingFunded[slot][index] || !source.funded(slot,index)) revert Unauthorized();
        incomingFunded[slot][index] = true;
        _module(slot).canonicalAccept(index, source.moduleAt(slot));
    }
    function _allFunded() private view {
        for (uint8 slot; slot < SLOTS; ++slot) {
            for (uint256 index; index < assetCount[slot]; ++index)
                if (!funded[slot][index]) revert InvalidBacking();
        }
    }
    function commit() external governance nonReentrant {
        if (phase != 1 || stateRoot == bytes32(0)) revert InvalidState();
        ZZZCanonicalHandoff peer = _peer(destinationController);
        if (peer.phase() != 2 || peer.stateRoot() != stateRoot ||
            peer.deploymentCommitment() != destinationDeployment) revert InvalidState();
        _allFunded();
        // Both transitions are atomic on this chain. A failed readiness or
        // backing check rolls retirement back; no competing successor is added.
        phase = 3;
        access.canonicalTransition(3, false, false);
        ICanonicalHelpers(access.module(Ids.NFT)).canonicalRetire();
        peer.activate();
        emit Retired(handoffId, destinationController, stateRoot);
    }
    function activate() external nonReentrant {
        ZZZCanonicalHandoff source = _peer(incomingSource);
        if (msg.sender != address(source) || phase != 2 || source.phase() != 3 ||
            source.destinationController() != address(access) || source.stateRoot() != stateRoot)
            revert Unauthorized();
        for (uint8 slot; slot < SLOTS; ++slot) {
            for (uint256 index; index < assetCount[slot]; ++index)
                if (!incomingFunded[slot][index]) revert InvalidBacking();
            _module(slot).canonicalValidate();
        }
        for (uint8 slot; slot < SLOTS; ++slot) _module(slot).canonicalActivate();
        phase = 5;
        access.canonicalTransition(0, false, true);
        emit Activated(handoffId, incomingSource, stateRoot);
    }
    function abort() external governance nonReentrant {
        if (phase != 1 && phase != 8) revert InvalidState();
        phase = 6;
        _peer(destinationController).cancelImport();
        emit AbortStarted(handoffId);
    }
    function cancelImport() external nonReentrant {
        ZZZCanonicalHandoff source = _peer(incomingSource);
        if (msg.sender != address(source) || source.phase() != 6 || (phase != 4 && phase != 2))
            revert Unauthorized();
        phase = 7;
        access.canonicalTransition(4, false, false);
    }
    function returnFunds(uint8 slot, uint256 index) external nonReentrant {
        if (phase != 6 || slot >= SLOTS || index >= assetCount[slot] ||
            !funded[slot][index] || returned[slot][index]) revert InvalidState();
        ZZZCanonicalHandoff peer = _peer(destinationController);
        if (peer.phase() != 7) revert InvalidState();
        (address asset, uint256 amount) = _module(slot).canonicalBacking(index);
        returned[slot][index] = true;
        uint256 beforeBalance = _balance(asset, moduleAt(slot));
        peer.returnFunding(slot, index);
        if (_balance(asset, moduleAt(slot)) != beforeBalance + amount) revert InvalidBacking();
        _module(slot).canonicalRestore(index, peer.moduleAt(slot));
        emit BackingReturned(handoffId, slot, index);
    }
    function returnFunding(uint8 slot, uint256 index) external nonReentrant {
        ZZZCanonicalHandoff source = _peer(incomingSource);
        if (msg.sender != address(source) || phase != 7 || source.phase() != 6 ||
            !incomingFunded[slot][index] || !source.returned(slot,index)) revert Unauthorized();
        incomingFunded[slot][index] = false;
        _module(slot).canonicalRelease(index, source.moduleAt(slot));
    }
    function finishAbort() external governance nonReentrant {
        if (phase != 6 || _peer(destinationController).phase() != 7) revert InvalidState();
        for (uint8 slot; slot < SLOTS; ++slot) {
            for (uint256 index; index < assetCount[slot]; ++index)
                if (funded[slot][index] && !returned[slot][index]) revert InvalidBacking();
            _module(slot).canonicalValidate();
        }
        phase = incomingSource == address(0) ? 0 : 5;
        access.canonicalTransition(0, false, true);
        emit Aborted(handoffId);
    }
}
