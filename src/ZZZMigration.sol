// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig, Route, BridgeMessage, MessageKind, AckPurpose} from "./libraries/ZZZTypes.sol";
import {IZZZVault, IZZZPools, IZZZRoutes, IZZZBridge, IZZZBridgeRouter, IZZZFees} from "./interfaces/IZZZ.sol";

/// @notice Repeated, timelocked custody moves. NFT shares and Power remain canonical; custody moves whole buckets without NFT loops.
contract ZZZMigration is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    enum Status { None, Scheduled, Cancelled, Bridged, Completed }
    struct Plan { uint256 bucketId; bytes32 routeId; uint64 earliest; Status status; uint64 epoch; bytes32 poolId; bytes32 snapshot; }
    struct Location { uint64 epoch; uint256 chainId; address vault; }
    mapping(bytes32 => Plan) public plans;
    mapping(uint256 => bytes32) public activePlan;
    mapping(uint256 => uint64) public custodyEpoch;
    mapping(uint256 => Location) public locations;
    mapping(uint256 => mapping(uint64 => bytes32)) public locationSnapshots;
    mapping(bytes32 => BridgeMessage) private departures;
    mapping(bytes32 => bool) private remotes;
    mapping(bytes32 => bool) private rewardPaths;
    uint256 public sequence;
    uint256 public constant MIGRATION_DELAY = 2 days;
    event Scheduled(bytes32 indexed migrationId, uint256 indexed bucketId, bytes32 indexed routeId, uint64 earliest);
    event Cancelled(bytes32 indexed migrationId);
    event Bridged(bytes32 indexed migrationId, bytes32 transportId);
    event Completed(bytes32 indexed migrationId, uint256 indexed bucketId);
    event LocationRecorded(uint256 indexed bucketId, uint64 indexed epoch, uint256 chainId, address vault);
    constructor(address controller) ZZZModule(controller) {}

    function _snapshot(BridgeMessage memory m) private pure returns (bytes32) {
        // ACK transport routes/nonces/purpose differ; the immutable custody move does not.
        bytes32 identity = keccak256(abi.encode(m.bucketId, m.homeChain, m.homeVault,
            m.homeReceiver, m.homePoolId, m.depositUSD, m.totalShares));
        bytes32 custody = keccak256(abi.encode(m.migrationId, m.migrationEpoch, m.principalRouteId,
            m.previousChain, m.previousVault, m.previousReceiver));
        bytes32 accounting = keccak256(abi.encode(m.canonicalToken0, m.canonicalToken1,
            m.allocatedIndividual0, m.allocatedCollective0, m.allocatedIndividual1, m.allocatedCollective1));
        return keccak256(abi.encode(identity, custody, accounting));
    }
    function _principal(uint256 id, bytes32 routeId, uint64 epoch, bytes32 migrationId, Position memory p)
        private view returns (BridgeMessage memory m) {
        m.version = 3;
        m.kind = MessageKind.Principal;
        m.routeId = routeId;
        m.principalRouteId = routeId;
        m.bucketId = id;
        m.migrationId = migrationId;
        m.migrationEpoch = epoch;
        m.previousChain = block.chainid;
        m.previousVault = access.module(Ids.VAULT);
        m.previousReceiver = access.module(Ids.RECEIVER);
        m.homeChain = p.homeChain;
        m.homeVault = p.homeVault;
        m.homeReceiver = p.homeReceiver;
        m.depositUSD = p.depositUSD;
        m.canonicalToken0 = p.homeToken0;
        m.canonicalToken1 = p.homeToken1;
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        m.homePoolId = vault.homePoolId(id);
        m.totalShares = vault.bucketTotalShares(id);
    }
    function propose(uint256 id, bytes32 routeId) external onlyGovernance returns (bytes32 migrationId) {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(id);
        (Route memory r, bool active) = IZZZRoutes(access.module(Ids.ROUTES)).get(routeId);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(p.poolId);
        if (!active || !IZZZBridgeRouter(access.module(Ids.TRANSPORT)).canSend(routeId) ||
            p.status != PositionStatus.Active || p.homeChain != vault.canonicalChainId() ||
            p.homeVault == address(0) || p.homeReceiver == address(0) || p.depositUSD == 0 ||
            p.homeToken0 == address(0) || p.homeToken1 == address(0) || vault.bucketTotalShares(id) == 0 ||
            vault.homePoolId(id) == bytes32(0) ||
            id != uint256(keccak256(abi.encode(p.homeChain, p.homeVault, vault.homePoolId(id)))) ||
            r.sourceChain != block.chainid || r.sourceVault != address(vault) || r.sourceReceiver != access.module(Ids.RECEIVER) ||
            r.sourceToken0 != c.key.currency0 || r.sourceToken1 != c.key.currency1 || activePlan[id] != bytes32(0)) revert InvalidConfiguration();
        uint64 epoch = custodyEpoch[id] + 1;
        migrationId = keccak256(abi.encode(block.chainid, address(this), ++sequence, id, epoch, routeId));
        uint64 earliest = uint64(block.timestamp + MIGRATION_DELAY);
        BridgeMessage memory m = _principal(id, routeId, epoch, migrationId, p);
        plans[migrationId] = Plan(id, routeId, earliest, Status.Scheduled, epoch, p.poolId, _snapshot(m));
        departures[migrationId] = m;
        activePlan[id] = migrationId;
        emit Scheduled(migrationId, id, routeId, earliest);
    }
    function cancel(bytes32 migrationId) external onlyGovernance {
        Plan storage plan = plans[migrationId];
        if (plan.status != Status.Scheduled) revert InvalidState();
        plan.status = Status.Cancelled;
        delete activePlan[plan.bucketId];
        emit Cancelled(migrationId);
    }
    function execute(bytes32 migrationId, uint256 deadline) external payable onlyKeeper live nonReentrant {
        _deadline(deadline);
        Plan storage plan = plans[migrationId];
        if (plan.status != Status.Scheduled || block.timestamp < plan.earliest) revert InvalidState();
        (Route memory r, bool active) = IZZZRoutes(access.module(Ids.ROUTES)).get(plan.routeId);
        if (!active || !IZZZBridgeRouter(access.module(Ids.TRANSPORT)).canSend(plan.routeId)) revert InvalidConfiguration();
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(plan.bucketId);
        if (p.status != PositionStatus.Active || p.poolId != plan.poolId || custodyEpoch[plan.bucketId] + 1 != plan.epoch ||
            _snapshot(_principal(plan.bucketId, plan.routeId, plan.epoch, migrationId, p)) != plan.snapshot) revert InvalidState();
        uint256 before0 = IERC20(r.sourceToken0).balanceOf(address(this));
        uint256 before1 = IERC20(r.sourceToken1).balanceOf(address(this));
        custodyEpoch[plan.bucketId] = plan.epoch;
        (uint256 amount0, uint256 amount1) = vault.releaseForMigration(plan.bucketId, migrationId, deadline);
        if (IERC20(r.sourceToken0).balanceOf(address(this)) != before0 + amount0 ||
            IERC20(r.sourceToken1).balanceOf(address(this)) != before1 + amount1) revert InvalidState();
        plan.status = Status.Bridged;
        BridgeMessage memory m = departures[migrationId];
        m.amount0 = amount0;
        m.amount1 = amount1;
        // Harvest during release can increase fee allocations. Freeze the actual
        // departure accounting only after release, while the proposal's cohort
        // snapshot has already been checked above.
        IZZZFees fees = IZZZFees(access.module(Ids.FEES));
        (m.allocatedIndividual0, m.allocatedCollective0) = fees.allocated(plan.bucketId, m.canonicalToken0);
        (m.allocatedIndividual1, m.allocatedCollective1) = fees.allocated(plan.bucketId, m.canonicalToken1);
        plan.snapshot = _snapshot(m);
        departures[migrationId] = m;
        address adapter = access.module(Ids.BRIDGE);
        IERC20(r.sourceToken0).forceApprove(adapter, amount0);
        IERC20(r.sourceToken1).forceApprove(adapter, amount1);
        bytes32 receipt = IZZZBridge(adapter).send{value: msg.value}(m);
        IERC20(r.sourceToken0).forceApprove(adapter, 0);
        IERC20(r.sourceToken1).forceApprove(adapter, 0);
        if (IERC20(r.sourceToken0).balanceOf(address(this)) != before0 ||
            IERC20(r.sourceToken1).balanceOf(address(this)) != before1) revert InvalidState();
        emit Bridged(migrationId, receipt);
    }
    function authorizedRemote(uint256 id, uint256 chainId, address vault) external view returns (bool) {
        return remotes[keccak256(abi.encode(id, chainId, vault))];
    }
    function authorizedReward(uint256 id, uint256 chainId, address vault, address remoteToken, address homeToken)
        external view returns (bool) {
        return rewardPaths[keccak256(abi.encode(id, chainId, vault, remoteToken, homeToken))];
    }
    function _identity(BridgeMessage memory m, Route memory r) private pure {
        if (m.version != 3 || m.totalShares == 0 || m.homePoolId == bytes32(0) ||
            m.bucketId != uint256(keccak256(abi.encode(m.homeChain, m.homeVault, m.homePoolId))) || m.migrationId == bytes32(0) || m.migrationEpoch == 0 || m.depositUSD == 0 ||
            m.homeChain == 0 || m.homeVault == address(0) || m.homeReceiver == address(0) ||
            m.canonicalToken0 == address(0) || m.canonicalToken1 == address(0) || m.canonicalToken0 == m.canonicalToken1 ||
            r.sourceToken0 == address(0) || r.sourceToken1 == address(0) ||
            m.previousChain != r.sourceChain || m.previousVault != r.sourceVault || m.previousReceiver != r.sourceReceiver) revert InvalidConfiguration();
    }
    function registerImport(BridgeMessage calldata message) external onlyModule(Ids.RECEIVER) {
        BridgeMessage memory m = message;
        (Route memory r,) = IZZZRoutes(access.module(Ids.ROUTES)).get(m.principalRouteId);
        _identity(m, r);
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(m.bucketId);
        if (m.kind != MessageKind.Principal || m.routeId != m.principalRouteId ||
            r.destinationChain != block.chainid || r.destinationVault != address(vault) ||
            r.destinationReceiver != access.module(Ids.RECEIVER) || m.homeChain != vault.canonicalChainId() ||
            m.migrationEpoch <= custodyEpoch[m.bucketId] || (p.status != PositionStatus.None && p.status != PositionStatus.Remote) ||
            p.lpTokenId != 0 || p.idle0 != 0 || p.idle1 != 0) revert InvalidState();
        if (p.status == PositionStatus.Remote && (p.homeChain != m.homeChain || p.homeVault != m.homeVault ||
            p.homeReceiver != m.homeReceiver || vault.homePoolId(m.bucketId) != m.homePoolId ||
            p.depositUSD > m.depositUSD || vault.bucketTotalShares(m.bucketId) > m.totalShares)) revert InvalidState();
        if (m.homeChain == block.chainid) {
            if (m.homeVault != address(vault) || p.status != PositionStatus.Remote ||
                p.depositUSD != m.depositUSD || vault.bucketTotalShares(m.bucketId) != m.totalShares ||
                r.destinationToken0 != m.canonicalToken0 || r.destinationToken1 != m.canonicalToken1) revert InvalidState();
            _recordCanonical(m, r.destinationChain, r.destinationVault, false);
        } else if (r.sourceChain == m.homeChain && r.sourceVault == m.homeVault &&
            (r.sourceToken0 != m.canonicalToken0 || r.sourceToken1 != m.canonicalToken1)) revert InvalidConfiguration();
        custodyEpoch[m.bucketId] = m.migrationEpoch;
    }
    function _recordCanonical(BridgeMessage memory m, uint256 destinationChain, address destinationVault, bool updateVault)
        private {
        bytes32 hash = _snapshot(m);
        bytes32 existing = locationSnapshots[m.bucketId][m.migrationEpoch];
        if (existing != bytes32(0)) {
            if (existing != hash) revert InvalidState();
            return; // An exact historical retry cannot regress the current location.
        }
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(m.bucketId);
        if (m.homeChain != block.chainid || m.homeVault != address(vault) || m.homeReceiver != access.module(Ids.RECEIVER) ||
            p.homeChain != m.homeChain || p.homeVault != m.homeVault || p.homeReceiver != m.homeReceiver ||
            p.depositUSD != m.depositUSD || vault.homePoolId(m.bucketId) != m.homePoolId ||
            vault.bucketTotalShares(m.bucketId) != m.totalShares || (p.status != PositionStatus.Outbound && p.status != PositionStatus.Remote)) revert InvalidState();
        Location memory old = locations[m.bucketId];
        if (old.epoch == 0) { old.chainId = p.homeChain; old.vault = p.homeVault; }
        if (m.migrationEpoch != old.epoch + 1 || m.previousChain != old.chainId || m.previousVault != old.vault) revert InvalidState();
        (Route memory r,) = IZZZRoutes(access.module(Ids.ROUTES)).get(m.principalRouteId);
        _identity(m, r);
        if (r.destinationChain != destinationChain || r.destinationVault != destinationVault) revert InvalidState();
        if (r.sourceChain == m.homeChain && r.sourceVault == m.homeVault) {
            Plan memory origin = plans[m.migrationId];
            if (origin.status != Status.Bridged || origin.snapshot != hash ||
                r.sourceToken0 != m.canonicalToken0 || r.sourceToken1 != m.canonicalToken1) revert Unauthorized();
        } else if (!rewardPaths[keccak256(abi.encode(m.bucketId, r.sourceChain, r.sourceVault, r.sourceToken0, m.canonicalToken0))] ||
            !rewardPaths[keccak256(abi.encode(m.bucketId, r.sourceChain, r.sourceVault, r.sourceToken1, m.canonicalToken1))]) revert Unauthorized();
        locationSnapshots[m.bucketId][m.migrationEpoch] = hash;
        locations[m.bucketId] = Location(m.migrationEpoch, destinationChain, destinationVault);
        if (m.migrationEpoch > custodyEpoch[m.bucketId]) custodyEpoch[m.bucketId] = m.migrationEpoch;
        remotes[keccak256(abi.encode(m.bucketId, destinationChain, destinationVault))] = true;
        rewardPaths[keccak256(abi.encode(m.bucketId, destinationChain, destinationVault, r.destinationToken0, m.canonicalToken0))] = true;
        rewardPaths[keccak256(abi.encode(m.bucketId, destinationChain, destinationVault, r.destinationToken1, m.canonicalToken1))] = true;
        if (updateVault) vault.confirmMigration(m.bucketId, destinationChain, destinationVault);
        emit LocationRecorded(m.bucketId, m.migrationEpoch, destinationChain, destinationVault);
    }
    function confirm(BridgeMessage calldata message, uint256 chainId, address destinationVault) external onlyModule(Ids.RECEIVER) {
        BridgeMessage memory m = message;
        (Route memory r,) = IZZZRoutes(access.module(Ids.ROUTES)).get(m.principalRouteId);
        _identity(m, r);
        if (m.kind != MessageKind.Acknowledgement || m.amount0 != 0 || m.amount1 != 0 ||
            m.individual != 0 || m.collective != 0 || chainId != r.destinationChain || destinationVault != r.destinationVault) revert InvalidState();
        if (m.acknowledgement == AckPurpose.SourceCompletion) {
            Plan storage plan = plans[m.migrationId];
            if (plan.bucketId != m.bucketId || plan.routeId != m.principalRouteId || plan.epoch != m.migrationEpoch ||
                plan.snapshot != _snapshot(m)) revert InvalidState();
            if (plan.status == Status.Completed) return;
            if (plan.status != Status.Bridged) revert InvalidState();
            if (m.homeChain == block.chainid && m.homeVault == access.module(Ids.VAULT)) {
                _recordCanonical(m, chainId, destinationVault, true);
            } else {
                Position memory p = IZZZVault(access.module(Ids.VAULT)).group(m.bucketId);
                if (p.status != PositionStatus.Outbound || custodyEpoch[m.bucketId] != plan.epoch) revert InvalidState();
                IZZZVault(access.module(Ids.VAULT)).confirmMigration(m.bucketId, chainId, destinationVault);
            }
            plan.status = Status.Completed;
            delete activePlan[plan.bucketId];
            emit Completed(m.migrationId, m.bucketId);
        } else {
            _recordCanonical(m, chainId, destinationVault, true);
        }
    }
    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline) external onlyGovernance live {
        IZZZVault(access.module(Ids.VAULT)).movePool(id, newPool, minimumLiquidity, deadline);
    }
    // No per-NFT calls or timeout-based principal release. A timeout is NOT proof of bridge cancellation.
}
