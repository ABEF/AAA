// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {TimelockController} from "@openzeppelin/contracts/governance/TimelockController.sol";
import {IZZZBound, IZZZAccess, IZZZBridgeEndpoint, IZZZVault, IZZZNFT} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {ZZZCanonicalHandoff} from "./ZZZCanonicalHandoff.sol";
import {ZZZRoyaltyFactory} from "./ZZZRoyaltyFactory.sol";

interface ICanonicalOwnerBinding {
    function nft() external view returns (address);
    function vault() external view returns (address);
    function fees() external view returns (address);
}

/// @notice Immediate role-authorized governance; module bindings are fixed at seal().
/// OpenZeppelin's operation hashes, roles, replay and predecessor checks remain,
/// but scheduling has no waiting period. This controller cannot act as the Vault.
contract ZZZAccessController is TimelockController {
    mapping(bytes32 => address) public module;
    mapping(address => bool) public keepers;
    mapping(address => bool) public guardians;
    address public bootstrap;
    bool public isSealed;
    bool public paused;
    bool public preparationActive;
    address public immutable royaltyFactory;
    uint8 public canonicalState;
    bool public canonicalSettling;
    bool public preparationReadyDestination;
    uint256 public preparationNonce;
    bytes32 public preparationHash;
    uint256 public preparationStartedAt;
    /// @dev Public notice only. These commitments do not authenticate a remote
    /// deployment, approve a successor, freeze rights or authorize any export.
    struct PreparationNotice {
        uint256 destinationChain;
        address successorController;
        bytes32 deploymentCommitment;
        bytes32 reviewHash;
    }
    PreparationNotice public preparationNotice;
    event ModuleBound(bytes32 indexed id, address indexed implementation);
    event SystemSealed();
    event PauseChanged(bool paused);
    event KeeperChanged(address indexed account, bool enabled);
    event PreparationStarted(bytes32 indexed noticeHash, uint256 indexed nonce,
        uint256 indexed destinationChain, address successorController, bytes32 deploymentCommitment, bytes32 reviewHash);
    event PreparationCancelled(bytes32 indexed noticeHash);
    error Unauthorized();
    error InvalidConfiguration();

    constructor(uint256 delay, address[] memory proposers, address[] memory executors, address initialKeeper,
        address initialGuardian) TimelockController(delay, proposers, executors, address(0)) {
        if (delay != 0 || proposers.length == 0 || executors.length == 0 ||
            initialKeeper == address(0) || initialGuardian == address(0)) revert InvalidConfiguration();
        for (uint256 i; i < proposers.length; ++i) {
            if (proposers[i] == address(0)) revert InvalidConfiguration();
        }
        bootstrap = msg.sender;
        royaltyFactory = address(new ZZZRoyaltyFactory());
        keepers[initialKeeper] = true;
        guardians[initialGuardian] = true;
    }
    /// @notice Exact authorized operations are ready immediately. Retain the
    /// audited scheduling/execution primitives without permitting delayed calls.
    function schedule(address target, uint256 value, bytes calldata data,
        bytes32 predecessor, bytes32 salt, uint256 delay) public override {
        // OZ reserves timestamp 1 for completed operations, and 0 for unset.
        if (delay != 0 || block.timestamp <= 1) revert InvalidConfiguration();
        super.schedule(target, value, data, predecessor, salt, 0);
    }
    function scheduleBatch(address[] calldata targets, uint256[] calldata values,
        bytes[] calldata payloads, bytes32 predecessor, bytes32 salt, uint256 delay) public override {
        if (delay != 0 || block.timestamp <= 1) revert InvalidConfiguration();
        super.scheduleBatch(targets, values, payloads, predecessor, salt, 0);
    }
    function canConfigure(address account) public view returns (bool) {
        return !preparationActive && ((canonicalState == 0 && account == address(this)) ||
            (!isSealed && account == bootstrap));
    }
    function canonicalHandoff() public view returns (address) { return module[Ids.CANONICAL]; }
    /// @dev One fail-closed authorization read keeps the immutable modules small.
    function moduleAuthorized(bytes32 id, address caller) external view returns (bool) {
        return isSealed && canonicalState == 0 && caller == module[id];
    }
    function keeperAuthorized(address caller) external view returns (bool) {
        return isSealed && canonicalState == 0 && keepers[caller];
    }
    /// @dev Only the immutable coordinator may change canonical authority.
    /// Pause/unpause and ordinary governance never bypass terminal retirement.
    function canonicalTransition(uint8 state, bool settling, bool clearPreparation) external {
        if (msg.sender != canonicalHandoff() || msg.sender == address(0) || state > 4 || (settling && state != 1)) revert Unauthorized();
        if (canonicalState == 3 || canonicalState == 4) revert InvalidConfiguration();
        canonicalState = state;
        canonicalSettling = settling;
        if (clearPreparation) preparationActive = false;
    }
    /// @notice Announce a cancellable preparation window through the existing
    /// controller, without a waiting period. The source remains the sole canonical authority.
    function startPreparation(PreparationNotice calldata notice) external {
        if (msg.sender != address(this) || !isSealed || preparationActive || canonicalState != 0) revert Unauthorized();
        if (IZZZVault(module[Ids.VAULT]).canonicalChainId() != block.chainid ||
            notice.destinationChain == 0 || notice.successorController == address(0) ||
            (notice.destinationChain == block.chainid && notice.successorController == address(this)) ||
            notice.deploymentCommitment == bytes32(0) || notice.reviewHash == bytes32(0)) revert InvalidConfiguration();
        preparationReadyDestination = false;
        if (notice.destinationChain == block.chainid && notice.successorController.code.length != 0) {
            IZZZAccess destination = IZZZAccess(notice.successorController);
            // Freeze cannot authenticate a configuration that bootstrap changed
            // after the notice was reviewed. A usable local importer is already
            // sealed, inert and bound to this source when announcement executes.
            if (!destination.isSealed() || destination.canonicalState() != 2) revert InvalidConfiguration();
            ZZZCanonicalHandoff handoff = ZZZCanonicalHandoff(destination.canonicalHandoff());
            if (handoff.incomingSource() != address(this) ||
                handoff.deploymentCommitment() != notice.deploymentCommitment) revert InvalidConfiguration();
            preparationReadyDestination = true;
        }
        uint256 nonce = ++preparationNonce;
        bytes32 noticeHash = keccak256(abi.encode("ZZZ_CANONICAL_PREPARATION_V1", block.chainid, address(this),
            module[Ids.VAULT], module[Ids.NFT], nonce, notice));
        preparationNotice = notice;
        preparationHash = noticeHash;
        preparationStartedAt = block.timestamp;
        preparationActive = true;
        emit PreparationStarted(noticeHash, nonce, notice.destinationChain, notice.successorController,
            notice.deploymentCommitment, notice.reviewHash);
    }
    /// @notice No custody or rights leave during preparation, so cancellation
    /// needs no remote proof. Exact notice binding prevents cancelling a later notice.
    function cancelPreparation(bytes32 noticeHash) external {
        if (msg.sender != address(this) || !preparationActive || canonicalState != 0) revert Unauthorized();
        if (noticeHash != preparationHash) revert InvalidConfiguration();
        preparationActive = false;
        emit PreparationCancelled(noticeHash);
    }
    function bind(bytes32 id, address implementation) external {
        if (msg.sender != bootstrap || isSealed) revert Unauthorized();
        if (implementation.code.length == 0 || module[id] != address(0) ||
            address(IZZZBound(implementation).access()) != address(this)) revert InvalidConfiguration();
        module[id] = implementation;
        emit ModuleBound(id, implementation);
    }
    function seal() external {
        if (msg.sender != bootstrap || isSealed) revert Unauthorized();
        bytes32[20] memory required = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP,
            Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION, Ids.BRIDGE,
            Ids.RECEIVER, Ids.ORACLE, Ids.POOLS, Ids.ROUTES, Ids.TRANSPORT, Ids.CANONICAL,
            Ids.NFT_CANONICAL, Ids.VAULT_CANONICAL, Ids.FEES_CANONICAL];
        for (uint256 i; i < required.length; ++i) {
            if (module[required[i]].code.length == 0) revert InvalidConfiguration();
            for (uint256 j; j < i; ++j) {
                if (module[required[i]] == module[required[j]]) revert InvalidConfiguration();
            }
        }
        if (ICanonicalOwnerBinding(module[Ids.NFT_CANONICAL]).nft() != module[Ids.NFT] ||
            ICanonicalOwnerBinding(module[Ids.VAULT_CANONICAL]).vault() != module[Ids.VAULT] ||
            ICanonicalOwnerBinding(module[Ids.FEES_CANONICAL]).fees() != module[Ids.FEES]) revert InvalidConfiguration();
        if (IZZZBridgeEndpoint(module[Ids.BRIDGE]).transport() != module[Ids.TRANSPORT]) revert InvalidConfiguration();
        // NFT randomness is configured only before sealing. Do not irreversibly
        // lock the canonical collection while its mint configuration is absent.
        if (IZZZVault(module[Ids.VAULT]).canonicalChainId() == block.chainid &&
            !IZZZNFT(module[Ids.NFT]).randomnessConfigured()) revert InvalidConfiguration();
        isSealed = true;
        bootstrap = address(0);
        emit SystemSealed();
    }
    function setKeeper(address who, bool enabled) external {
        if (!canConfigure(msg.sender) || who == address(0)) revert Unauthorized();
        keepers[who] = enabled;
        emit KeeperChanged(who, enabled);
    }
    function setGuardian(address who, bool enabled) external {
        if (!canConfigure(msg.sender) || who == address(0)) revert Unauthorized();
        guardians[who] = enabled;
    }
    function setPaused(bool state) external {
        // Pause control remains available to drain incoming custody and park it.
        // Unpausing never bypasses the separate preparation guards.
        if (msg.sender != address(this) && !(!isSealed && msg.sender == bootstrap) &&
            !(state && guardians[msg.sender])) revert Unauthorized();
        paused = state;
        emit PauseChanged(state);
    }
    /// @notice Zero governance delay is fixed for this deployment's lifetime.
    function updateDelay(uint256) external pure override {
        revert InvalidConfiguration();
    }
}
