// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PoolConfig, Route, BridgeMessage, MessageKind, AckPurpose} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZRoutes, IZZZVault, IZZZPools, IZZZFees, IZZZMigration, IZZZBridge} from "./interfaces/IZZZ.sol";

contract ZZZMigrationReceiver is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    struct Receipt { uint256 bucketId; bytes32 routeId; bool exists; bool finalized; }
    mapping(bytes32 => Receipt) public receipts;
    // Every ACK describes the accepted hop, even if this bucket has since moved again.
    mapping(bytes32 => BridgeMessage) private acceptedMessages;
    event PrincipalAccepted(bytes32 indexed migrationId, uint256 indexed bucketId);
    event PrincipalActivated(bytes32 indexed migrationId, uint256 indexed bucketId);
    event AcknowledgementSent(bytes32 indexed migrationId, bytes32 transportId);
    constructor(address controller) ZZZModule(controller) {}
    function acceptedMessage(bytes32 migrationId) external view returns (BridgeMessage memory) {
        return acceptedMessages[migrationId];
    }
    function receiveMessage(uint256 sourceChain, address sourceAdapter, BridgeMessage calldata m)
        external onlyModule(Ids.BRIDGE) nonReentrant {
        (Route memory r,) = IZZZRoutes(access.module(Ids.ROUTES)).get(m.routeId);
        if (m.version != 3 || r.sourceChain != sourceChain || r.sourceAdapter != sourceAdapter ||
            r.destinationChain != block.chainid || r.destinationVault != access.module(Ids.VAULT) ||
            r.destinationReceiver != address(this)) revert InvalidConfiguration();
        if (m.kind == MessageKind.Principal) _principal(r, m);
        else if (m.kind == MessageKind.Reward) _reward(r, m);
        else {
            IZZZMigration(access.module(Ids.MIGRATION)).confirm(m, sourceChain, r.sourceVault);
        }
    }
    function _principal(Route memory r, BridgeMessage calldata m) private {
        address vault = access.module(Ids.VAULT);
        if (receipts[m.migrationId].exists || m.migrationId == bytes32(0) || m.principalRouteId != m.routeId ||
            m.previousChain != r.sourceChain || m.previousVault != r.sourceVault || m.previousReceiver != r.sourceReceiver ||
            m.homeChain != IZZZVault(vault).canonicalChainId() || m.homeVault == address(0) ||
            m.homeReceiver == address(0) || m.depositUSD == 0 || m.migrationEpoch == 0 ||
            m.totalShares == 0 || m.homePoolId == bytes32(0) ||
            m.bucketId != uint256(keccak256(abi.encode(m.homeChain, m.homeVault, m.homePoolId))) ||
            m.canonicalToken0 == address(0) || m.canonicalToken1 == address(0) ||
            m.canonicalToken0 == m.canonicalToken1) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(r.destinationPool);
        bool sameOrder = c.key.currency0 == r.destinationToken0 && c.key.currency1 == r.destinationToken1;
        if (!sameOrder && !(c.key.currency0 == r.destinationToken1 && c.key.currency1 == r.destinationToken0)) revert InvalidConfiguration();
        // Provenance and monotonically increasing custody epochs are recorded by
        // migration before accepting funds. Any later failure reverts this too.
        IZZZMigration(access.module(Ids.MIGRATION)).registerImport(m);
        receipts[m.migrationId] = Receipt(m.bucketId, m.routeId, true, false);
        acceptedMessages[m.migrationId] = m;
        ExactToken.pull(r.destinationToken0, msg.sender, m.amount0);
        ExactToken.pull(r.destinationToken1, msg.sender, m.amount1);
        IERC20(r.destinationToken0).forceApprove(vault, m.amount0);
        IERC20(r.destinationToken1).forceApprove(vault, m.amount1);
        Position memory origin;
        origin.homeChain = m.homeChain;
        origin.homeVault = m.homeVault;
        origin.homeReceiver = m.homeReceiver;
        origin.homeToken0 = sameOrder ? m.canonicalToken0 : m.canonicalToken1;
        origin.homeToken1 = sameOrder ? m.canonicalToken1 : m.canonicalToken0;
        origin.depositUSD = m.depositUSD;
        if (m.homeChain != block.chainid) {
            IZZZFees fees = IZZZFees(access.module(Ids.FEES));
            fees.bindRemoteAsset(m.bucketId, r.destinationToken0, m.canonicalToken0);
            fees.bindRemoteAsset(m.bucketId, r.destinationToken1, m.canonicalToken1);
        }
        IZZZVault(vault).importPending(m.bucketId, r.destinationPool, origin, m.totalShares, m.homePoolId,
            sameOrder ? m.amount0 : m.amount1, sameOrder ? m.amount1 : m.amount0);
        IZZZFees(access.module(Ids.FEES)).importAccounting(m);
        IERC20(r.destinationToken0).forceApprove(vault, 0);
        IERC20(r.destinationToken1).forceApprove(vault, 0);
        emit PrincipalAccepted(m.migrationId, m.bucketId);
    }
    function _reward(Route memory r, BridgeMessage calldata m) private {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(m.bucketId);
        if (m.totalShares == 0 || m.totalShares != vault.bucketTotalShares(m.bucketId) ||
            m.bucketId != uint256(keccak256(abi.encode(m.homeChain, m.homeVault, m.homePoolId))) ||
            m.homePoolId != vault.homePoolId(m.bucketId) || m.depositUSD != p.depositUSD ||
            m.canonicalToken0 != r.destinationToken0 || m.homeChain != block.chainid || m.homeVault != access.module(Ids.VAULT) || m.homeReceiver != address(this) ||
            !IZZZMigration(access.module(Ids.MIGRATION)).authorizedReward(m.bucketId, r.sourceChain, r.sourceVault,
                r.sourceToken0, r.destinationToken0)) revert Unauthorized();
        ExactToken.pull(r.destinationToken0, msg.sender, m.amount0);
        address fees = access.module(Ids.FEES);
        IERC20(r.destinationToken0).forceApprove(fees, m.amount0);
        IZZZFees(fees).creditRemote(m.bucketId, r.destinationToken0, m.individual, m.collective);
        IERC20(r.destinationToken0).forceApprove(fees, 0);
    }
    function finalize(bytes32 migrationId, uint128 minimumLiquidity, uint256 deadline) external onlyKeeper live nonReentrant {
        Receipt storage receipt = receipts[migrationId];
        if (!receipt.exists || receipt.finalized) revert InvalidState();
        receipt.finalized = true;
        IZZZVault(access.module(Ids.VAULT)).finalizeImport(receipt.bucketId, minimumLiquidity, deadline);
        emit PrincipalActivated(migrationId, receipt.bucketId);
    }
    function acknowledge(bytes32 migrationId, bytes32 reverseRouteId) external payable live nonReentrant returns (bytes32) {
        return _acknowledge(migrationId, reverseRouteId, AckPurpose.SourceCompletion);
    }
    function acknowledgeHome(bytes32 migrationId, bytes32 homeRouteId) external payable live nonReentrant returns (bytes32) {
        return _acknowledge(migrationId, homeRouteId, AckPurpose.CanonicalLocation);
    }
    function _acknowledge(bytes32 migrationId, bytes32 deliveryRouteId, AckPurpose purpose) private returns (bytes32) {
        Receipt memory receipt = receipts[migrationId];
        if (!receipt.exists || !receipt.finalized) revert InvalidState();
        BridgeMessage memory m = acceptedMessages[migrationId];
        bool sourceCompletion = purpose == AckPurpose.SourceCompletion;
        if (!sourceCompletion && m.homeChain == block.chainid) revert InvalidState();
        (Route memory reverse, bool enabled) = IZZZRoutes(access.module(Ids.ROUTES)).get(deliveryRouteId);
        if (!enabled || reverse.sourceChain != block.chainid || reverse.sourceVault != access.module(Ids.VAULT) ||
            reverse.sourceReceiver != address(this) ||
            reverse.destinationChain != (sourceCompletion ? m.previousChain : m.homeChain) ||
            reverse.destinationVault != (sourceCompletion ? m.previousVault : m.homeVault) ||
            reverse.destinationReceiver != (sourceCompletion ? m.previousReceiver : m.homeReceiver) ||
            reverse.sourceToken0 != address(0) || reverse.sourceToken1 != address(0) ||
            reverse.destinationToken0 != address(0) || reverse.destinationToken1 != address(0)) revert InvalidConfiguration();
        m.version = 3;
        m.kind = MessageKind.Acknowledgement;
        m.routeId = deliveryRouteId;
        m.nonce = 0;
        m.amount0 = 0;
        m.amount1 = 0;
        m.individual = 0;
        m.collective = 0;
        m.acknowledgement = purpose;
        bytes32 transportId = IZZZBridge(access.module(Ids.BRIDGE)).send{value: msg.value}(m);
        emit AcknowledgementSent(migrationId, transportId);
        return transportId;
    }
}
