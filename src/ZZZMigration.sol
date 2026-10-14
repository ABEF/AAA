// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig, Route, BridgeMessage, MessageKind} from "./libraries/ZZZTypes.sol";
import {IZZZVault, IZZZPools, IZZZRoutes, IZZZBridge} from "./interfaces/IZZZ.sol";

contract ZZZMigration is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    enum Status { None, Scheduled, Cancelled, Bridged, Completed }
    struct Plan { uint256 nftId; bytes32 routeId; uint64 earliest; Status status; }
    mapping(bytes32 => Plan) public plans;
    mapping(uint256 => bytes32) public activePlan;
    mapping(bytes32 => bool) private remotes;
    mapping(bytes32 => bool) private rewardPaths;
    uint256 public sequence;
    uint256 public constant MIGRATION_DELAY = 2 days;
    event Scheduled(bytes32 indexed migrationId, uint256 indexed nftId, bytes32 indexed routeId, uint64 earliest);
    event Cancelled(bytes32 indexed migrationId);
    event Bridged(bytes32 indexed migrationId, bytes32 transportId);
    event Completed(bytes32 indexed migrationId, uint256 indexed nftId);
    constructor(address controller) ZZZModule(controller) {}
    function propose(uint256 id, bytes32 routeId) external onlyGovernance returns (bytes32 migrationId) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).position(id);
        (Route memory r, bool active) = IZZZRoutes(access.module(Ids.ROUTES)).get(routeId);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(p.poolId);
        if (!active || p.status != PositionStatus.Active || p.homeChain != block.chainid || p.homeVault != access.module(Ids.VAULT) ||
            r.sourceChain != block.chainid || r.sourceVault != p.homeVault || r.sourceReceiver != p.homeReceiver ||
            r.sourceToken0 != c.key.currency0 || r.sourceToken1 != c.key.currency1 || activePlan[id] != bytes32(0)) revert InvalidConfiguration();
        migrationId = keccak256(abi.encode(block.chainid, address(this), ++sequence, id, routeId));
        uint64 earliest = uint64(block.timestamp + MIGRATION_DELAY);
        plans[migrationId] = Plan(id, routeId, earliest, Status.Scheduled);
        activePlan[id] = migrationId;
        emit Scheduled(migrationId, id, routeId, earliest);
    }
    function cancel(bytes32 migrationId) external onlyGovernance {
        Plan storage plan = plans[migrationId];
        if (plan.status != Status.Scheduled) revert InvalidState();
        plan.status = Status.Cancelled;
        delete activePlan[plan.nftId];
        emit Cancelled(migrationId);
    }
    function execute(bytes32 migrationId, uint256 deadline) external payable onlyKeeper live nonReentrant {
        _deadline(deadline);
        Plan storage plan = plans[migrationId];
        if (plan.status != Status.Scheduled || block.timestamp < plan.earliest) revert InvalidState();
        (Route memory r, bool active) = IZZZRoutes(access.module(Ids.ROUTES)).get(plan.routeId);
        if (!active) revert InvalidConfiguration();
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.position(plan.nftId);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(p.poolId);
        if (c.key.currency0 != r.sourceToken0 || c.key.currency1 != r.sourceToken1) revert InvalidState();
        uint256 before0 = IERC20(r.sourceToken0).balanceOf(address(this));
        uint256 before1 = IERC20(r.sourceToken1).balanceOf(address(this));
        (uint256 amount0, uint256 amount1) = vault.releaseForMigration(plan.nftId, migrationId, deadline);
        if (IERC20(r.sourceToken0).balanceOf(address(this)) != before0 + amount0 ||
            IERC20(r.sourceToken1).balanceOf(address(this)) != before1 + amount1) revert InvalidState();
        plan.status = Status.Bridged;
        remotes[keccak256(abi.encode(plan.nftId, r.destinationChain, r.destinationVault))] = true;
        rewardPaths[keccak256(abi.encode(plan.nftId, r.destinationChain, r.destinationVault, r.destinationToken0, r.sourceToken0))] = true;
        rewardPaths[keccak256(abi.encode(plan.nftId, r.destinationChain, r.destinationVault, r.destinationToken1, r.sourceToken1))] = true;
        BridgeMessage memory m;
        m.version = 1;
        m.kind = MessageKind.Principal;
        m.routeId = plan.routeId;
        m.nftId = plan.nftId;
        m.migrationId = migrationId;
        m.homeChain = p.homeChain;
        m.homeVault = p.homeVault;
        m.homeReceiver = p.homeReceiver;
        m.depositUSD = p.depositUSD;
        m.amount0 = amount0;
        m.amount1 = amount1;
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
    function confirm(bytes32 migrationId, uint256 id, uint256 chainId, address vault) external onlyModule(Ids.RECEIVER) {
        Plan storage plan = plans[migrationId];
        (Route memory r,) = IZZZRoutes(access.module(Ids.ROUTES)).get(plan.routeId);
        if (plan.nftId != id || chainId != r.destinationChain || vault != r.destinationVault) revert InvalidState();
        if (plan.status == Status.Completed) return; // ACK retries are idempotent.
        if (plan.status != Status.Bridged) revert InvalidState();
        plan.status = Status.Completed;
        IZZZVault(access.module(Ids.VAULT)).confirmMigration(id, chainId, vault);
        emit Completed(migrationId, id);
    }
    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline) external onlyGovernance live {
        IZZZVault(access.module(Ids.VAULT)).movePool(id, newPool, minimumLiquidity, deadline);
    }
    // No timeout-based principal release. A timeout is NOT proof of bridge cancellation.
}
