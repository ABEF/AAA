// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PoolConfig, Route, BridgeMessage, MessageKind} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZRoutes, IZZZVault, IZZZPools, IZZZFees, IZZZMigration, IZZZBridge} from "./interfaces/IZZZ.sol";

contract ZZZMigrationReceiver is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    struct Receipt { uint256 nftId; bytes32 routeId; bool exists; bool finalized; }
    mapping(bytes32 => Receipt) public receipts;
    event PrincipalAccepted(bytes32 indexed migrationId, uint256 indexed nftId);
    event PrincipalActivated(bytes32 indexed migrationId, uint256 indexed nftId);
    event AcknowledgementSent(bytes32 indexed migrationId, bytes32 transportId);
    constructor(address controller) ZZZModule(controller) {}
    function receiveMessage(uint256 sourceChain, address sourceAdapter, BridgeMessage calldata m)
        external onlyModule(Ids.BRIDGE) nonReentrant {
        (Route memory r,) = IZZZRoutes(access.module(Ids.ROUTES)).get(m.routeId);
        if (r.sourceChain != sourceChain || r.sourceAdapter != sourceAdapter ||
            r.destinationChain != block.chainid || r.destinationVault != access.module(Ids.VAULT) ||
            r.destinationReceiver != address(this)) revert InvalidConfiguration();
        if (m.kind == MessageKind.Principal) _principal(r, m);
        else if (m.kind == MessageKind.Reward) _reward(r, m);
        else {
            if (m.homeChain != block.chainid || m.homeVault != access.module(Ids.VAULT) || m.homeReceiver != address(this)) revert InvalidState();
            IZZZMigration(access.module(Ids.MIGRATION)).confirm(m.migrationId, m.nftId, sourceChain, r.sourceVault);
        }
    }
    function _principal(Route memory r, BridgeMessage calldata m) private {
        if (receipts[m.migrationId].exists || m.homeChain != r.sourceChain || m.homeVault != r.sourceVault ||
            m.homeReceiver != r.sourceReceiver || m.depositUSD == 0) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(r.destinationPool);
        bool sameOrder = c.key.currency0 == r.destinationToken0 && c.key.currency1 == r.destinationToken1;
        if (!sameOrder && !(c.key.currency0 == r.destinationToken1 && c.key.currency1 == r.destinationToken0)) revert InvalidConfiguration();
        receipts[m.migrationId] = Receipt(m.nftId, m.routeId, true, false);
        ExactToken.pull(r.destinationToken0, msg.sender, m.amount0);
        ExactToken.pull(r.destinationToken1, msg.sender, m.amount1);
        address vault = access.module(Ids.VAULT);
        IERC20(r.destinationToken0).forceApprove(vault, m.amount0);
        IERC20(r.destinationToken1).forceApprove(vault, m.amount1);
        Position memory origin;
        origin.homeChain = m.homeChain;
        origin.homeVault = m.homeVault;
        origin.homeReceiver = m.homeReceiver;
        origin.homeToken0 = sameOrder ? r.sourceToken0 : r.sourceToken1;
        origin.homeToken1 = sameOrder ? r.sourceToken1 : r.sourceToken0;
        origin.depositUSD = m.depositUSD;
        IZZZVault(vault).importPending(m.nftId, r.destinationPool, origin,
            sameOrder ? m.amount0 : m.amount1, sameOrder ? m.amount1 : m.amount0);
        IERC20(r.destinationToken0).forceApprove(vault, 0);
        IERC20(r.destinationToken1).forceApprove(vault, 0);
        emit PrincipalAccepted(m.migrationId, m.nftId);
    }
    function _reward(Route memory r, BridgeMessage calldata m) private {
        if (m.homeChain != block.chainid || m.homeVault != access.module(Ids.VAULT) || m.homeReceiver != address(this) ||
            !IZZZMigration(access.module(Ids.MIGRATION)).authorizedReward(m.nftId, r.sourceChain, r.sourceVault,
                r.sourceToken0, r.destinationToken0)) revert Unauthorized();
        ExactToken.pull(r.destinationToken0, msg.sender, m.amount0);
        address fees = access.module(Ids.FEES);
        IERC20(r.destinationToken0).forceApprove(fees, m.amount0);
        IZZZFees(fees).creditRemote(m.nftId, r.destinationToken0, m.individual, m.collective);
        IERC20(r.destinationToken0).forceApprove(fees, 0);
    }
    function finalize(bytes32 migrationId, uint128 minimumLiquidity, uint256 deadline) external onlyKeeper live nonReentrant {
        Receipt storage receipt = receipts[migrationId];
        if (!receipt.exists || receipt.finalized) revert InvalidState();
        receipt.finalized = true;
        IZZZVault(access.module(Ids.VAULT)).finalizeImport(receipt.nftId, minimumLiquidity, deadline);
        emit PrincipalActivated(migrationId, receipt.nftId);
    }
    function acknowledge(bytes32 migrationId, bytes32 reverseRouteId) external payable live nonReentrant returns (bytes32) {
        Receipt memory receipt = receipts[migrationId];
        if (!receipt.exists || !receipt.finalized) revert InvalidState();
        (Route memory original,) = IZZZRoutes(access.module(Ids.ROUTES)).get(receipt.routeId);
        (Route memory reverse, bool enabled) = IZZZRoutes(access.module(Ids.ROUTES)).get(reverseRouteId);
        if (!enabled || reverse.sourceChain != block.chainid || reverse.sourceVault != access.module(Ids.VAULT) ||
            reverse.destinationChain != original.sourceChain || reverse.destinationVault != original.sourceVault ||
            reverse.destinationReceiver != original.sourceReceiver || reverse.sourceToken0 != address(0) ||
            reverse.sourceToken1 != address(0)) revert InvalidConfiguration();
        BridgeMessage memory m;
        m.version = 1;
        m.kind = MessageKind.Acknowledgement;
        m.routeId = reverseRouteId;
        m.nftId = receipt.nftId;
        m.migrationId = migrationId;
        m.homeChain = original.sourceChain;
        m.homeVault = original.sourceVault;
        m.homeReceiver = original.sourceReceiver;
        bytes32 transportId = IZZZBridge(access.module(Ids.BRIDGE)).send{value: msg.value}(m);
        emit AcknowledgementSent(migrationId, transportId);
        return transportId;
    }
}
