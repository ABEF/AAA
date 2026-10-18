// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Route, BridgeMessage, MessageKind} from "./libraries/ZZZTypes.sol";
import {BridgeAssets} from "./libraries/BridgeAssets.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZRoutes, IZZZTransport, IZZZReceiver} from "./interfaces/IZZZ.sol";

interface IBridgeCanonicalVault { function canonicalModule() external view returns (address); }
interface IBridgeCanonicalOrigin { function originVault() external view returns (address); }

/// @notice Fully specified transport boundary, NOT a universal live bridge.
/// The sealed deployment pins this endpoint to the fixed ZZZBridgeRouter.
contract ZZZBridgeAdapter is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    IZZZTransport public immutable transport;
    uint256 public nonce;
    uint256 public receivedCount;
    mapping(bytes32 => bool) public processed;
    event Sent(bytes32 indexed transportId, bytes32 indexed routeId, uint256 indexed nonce, uint8 kind);
    event Received(bytes32 indexed deliveryId, bytes32 indexed routeId, uint256 indexed bucketId, uint8 kind);
    constructor(address controller, address endpoint) ZZZModule(controller) {
        if (endpoint.code.length == 0) revert InvalidConfiguration();
        transport = IZZZTransport(endpoint);
    }
    function send(BridgeMessage calldata message) external payable live canonicalAccounting nonReentrant returns (bytes32 transportId) {
        if (message.kind == MessageKind.Principal) {
            _checkOperating();
            address vault = access.module(Ids.VAULT);
            // v3 binds genesis lineage and current home routing into one field.
            // An imported canonical deployment must not send ambiguous v3
            // principal packets. A separately qualified epoch-aware transport
            // is required; retaining these guards prevents silent relabelling.
            if (IBridgeCanonicalOrigin(IBridgeCanonicalVault(vault).canonicalModule()).originVault() != vault)
                revert InvalidConfiguration();
        }
        bytes32 required = message.kind == MessageKind.Principal ? Ids.MIGRATION :
            message.kind == MessageKind.Reward ? Ids.FEES : Ids.RECEIVER;
        if (msg.sender != access.module(required) || message.nonce != 0) revert Unauthorized();
        (Route memory r, bool active) = IZZZRoutes(access.module(Ids.ROUTES)).get(message.routeId);
        if (!active || r.sourceChain != block.chainid || r.sourceAdapter != address(this) ||
            r.sourceVault != access.module(Ids.VAULT)) revert InvalidConfiguration();
        BridgeMessage memory m = message;
        m.nonce = ++nonce;
        (address[] memory tokens, uint256[] memory amounts) = BridgeAssets.assets(r, m, false);
        uint256[] memory beforeBalances = new uint256[](tokens.length);
        for (uint256 i; i < tokens.length; ++i) {
            beforeBalances[i] = IERC20(tokens[i]).balanceOf(address(this));
            ExactToken.pull(tokens[i], msg.sender, amounts[i]);
            IERC20(tokens[i]).forceApprove(address(transport), amounts[i]);
        }
        transportId = transport.send{value: msg.value}(r.destinationChain, r.destinationAdapter, tokens, amounts, abi.encode(m));
        if (transportId == bytes32(0)) revert InvalidState();
        for (uint256 i; i < tokens.length; ++i) {
            IERC20(tokens[i]).forceApprove(address(transport), 0);
            if (IERC20(tokens[i]).balanceOf(address(this)) != beforeBalances[i]) revert InvalidState();
        }
        emit Sent(transportId, m.routeId, m.nonce, uint8(m.kind));
        if (message.kind == MessageKind.Principal) _checkOperating();
    }
    function onMessage(uint256 sourceChain, address sourceAdapter, bytes calldata payload) external canonicalAccounting nonReentrant {
        // Inbound settlement remains available during a local strategy pause.
        if (!access.isSealed() || msg.sender != address(transport)) revert Unauthorized();
        BridgeMessage memory m = abi.decode(payload, (BridgeMessage));
        (Route memory r,) = IZZZRoutes(access.module(Ids.ROUTES)).get(m.routeId);
        if (r.sourceChain != sourceChain || r.sourceAdapter != sourceAdapter ||
            r.destinationChain != block.chainid || r.destinationAdapter != address(this) ||
            r.destinationReceiver != access.module(Ids.RECEIVER) || m.nonce == 0) revert InvalidConfiguration();
        bytes32 deliveryId = keccak256(abi.encode(sourceChain, sourceAdapter, m.nonce));
        if (processed[deliveryId]) revert InvalidState();
        processed[deliveryId] = true;
        ++receivedCount;
        (address[] memory tokens, uint256[] memory amounts) = BridgeAssets.assets(r, m, true);
        address receiver = access.module(Ids.RECEIVER);
        uint256[] memory beforeBalances = new uint256[](tokens.length);
        for (uint256 i; i < tokens.length; ++i) {
            beforeBalances[i] = IERC20(tokens[i]).balanceOf(address(this));
            ExactToken.pull(tokens[i], msg.sender, amounts[i]);
            IERC20(tokens[i]).forceApprove(receiver, amounts[i]);
        }
        IZZZReceiver(receiver).receiveMessage(sourceChain, sourceAdapter, m);
        for (uint256 i; i < tokens.length; ++i) {
            IERC20(tokens[i]).forceApprove(receiver, 0);
            if (IERC20(tokens[i]).balanceOf(address(this)) != beforeBalances[i]) revert InvalidState();
        }
        emit Received(deliveryId, m.routeId, m.bucketId, uint8(m.kind));
    }
}
