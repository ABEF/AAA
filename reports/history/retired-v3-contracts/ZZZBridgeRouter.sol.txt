// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Route, BridgeMessage, TransportPolicy, TransportEnvelope} from "./libraries/ZZZTypes.sol";
import {BridgeAssets} from "./libraries/BridgeAssets.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZRoutes, IZZZVault, IZZZTransportProvider, IZZZTransportReceiver} from "./interfaces/IZZZ.sol";

/// @notice Fixed custody router with timelocked, immutable provider policies.
/// No provider is selected by default. Disabling sends preserves pending inbound
/// settlement. Actual bridge wrappers, backing and finality need separate review.
contract ZZZBridgeRouter is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    mapping(bytes32 => TransportPolicy) private policies;
    mapping(bytes32 => bool) public policyExists;
    mapping(bytes32 => bool) public outboundEnabled;
    mapping(bytes32 => bool) public processed;
    event PolicyRegistered(bytes32 indexed policyId, bytes32 indexed providerId, uint256 sourceChain,
        uint256 destinationChain, address sourceRouter, address destinationRouter,
        address sourceProvider, address destinationProvider, bytes32 reviewHash);
    event OutboundEnabled(bytes32 indexed policyId, bool enabled);
    event TransportSent(bytes32 indexed policyId, bytes32 indexed routeId, uint256 indexed nonce, bytes32 receipt);
    event TransportReceived(bytes32 indexed policyId, bytes32 indexed routeId, uint256 indexed nonce, bytes32 deliveryId);
    constructor(address controller) ZZZModule(controller) {}

    function _providerValid(address provider, bytes32 codeHash, bytes32 configuration, bytes32 channel)
        private view returns (bool) {
        if (provider.code.length == 0 || provider.codehash != codeHash) return false;
        try IZZZTransportProvider(provider).router() returns (address bound) {
            if (bound != address(this)) return false;
        } catch { return false; }
        try IZZZTransportProvider(provider).configurationHash(channel) returns (bytes32 actual) {
            return actual == configuration;
        } catch { return false; }
    }
    function registerPolicy(TransportPolicy calldata p) external onlyGovernance returns (bytes32 id) {
        if (p.providerId == bytes32(0) || p.sourceChain == 0 || p.destinationChain == 0 || p.sourceChain == p.destinationChain ||
            p.sourceRouter == address(0) || p.destinationRouter == address(0) || p.sourceProvider == address(0) ||
            p.destinationProvider == address(0) || p.sourceCodeHash == bytes32(0) || p.destinationCodeHash == bytes32(0) ||
            p.sourceConfigurationHash == bytes32(0) || p.destinationConfigurationHash == bytes32(0) ||
            p.channelId == bytes32(0) || p.reviewHash == bytes32(0)) revert InvalidConfiguration();
        bool localSource = p.sourceChain == block.chainid;
        bool localDestination = p.destinationChain == block.chainid;
        if (!localSource && !localDestination && block.chainid !=
            IZZZVault(access.module(Ids.VAULT)).canonicalChainId()) revert InvalidConfiguration();
        if (localSource && (p.sourceRouter != address(this) ||
            !_providerValid(p.sourceProvider, p.sourceCodeHash, p.sourceConfigurationHash, p.channelId))) revert InvalidConfiguration();
        if (localDestination && (p.destinationRouter != address(this) ||
            !_providerValid(p.destinationProvider, p.destinationCodeHash, p.destinationConfigurationHash, p.channelId))) revert InvalidConfiguration();
        id = keccak256(abi.encode(p));
        if (policyExists[id]) revert InvalidConfiguration();
        policies[id] = p;
        policyExists[id] = true;
        emit PolicyRegistered(id, p.providerId, p.sourceChain, p.destinationChain, p.sourceRouter,
            p.destinationRouter, p.sourceProvider, p.destinationProvider, p.reviewHash);
    }
    function policy(bytes32 id) external view returns (TransportPolicy memory) {
        if (!policyExists[id]) revert InvalidConfiguration();
        return policies[id];
    }
    function setOutboundEnabled(bytes32 id, bool enabled) external onlyGovernance {
        TransportPolicy memory p = policies[id];
        if (!policyExists[id] || p.sourceChain != block.chainid || p.sourceRouter != address(this) ||
            (enabled && !_providerValid(p.sourceProvider, p.sourceCodeHash, p.sourceConfigurationHash, p.channelId))) revert InvalidConfiguration();
        outboundEnabled[id] = enabled;
        emit OutboundEnabled(id, enabled);
    }
    function matchesRoute(bytes32 id, Route memory r) public view returns (bool) {
        TransportPolicy memory p = policies[id];
        return policyExists[id] && p.sourceChain == r.sourceChain && p.destinationChain == r.destinationChain &&
            (r.sourceChain != block.chainid || (p.sourceRouter == address(this) && r.sourceAdapter == access.module(Ids.BRIDGE))) &&
            (r.destinationChain != block.chainid || (p.destinationRouter == address(this) && r.destinationAdapter == access.module(Ids.BRIDGE)));
    }
    function canSend(bytes32 routeId) public view returns (bool) {
        if (!access.isSealed() || access.paused()) return false;
        IZZZRoutes registry = IZZZRoutes(access.module(Ids.ROUTES));
        // Unknown routes fail closed, including a registry whose getter reverts.
        try registry.get(routeId) returns (Route memory r, bool enabled) {
            bytes32 id = registry.transportPolicyId(routeId);
            TransportPolicy memory p = policies[id];
            return enabled && outboundEnabled[id] && matchesRoute(id, r) &&
                r.sourceChain == block.chainid && p.sourceRouter == address(this) &&
                _providerValid(p.sourceProvider, p.sourceCodeHash, p.sourceConfigurationHash, p.channelId);
        } catch { return false; }
    }
    function _vector(address[] memory expectedTokens, uint256[] memory expectedAmounts,
        address[] calldata tokens, uint256[] calldata amounts) private pure {
        if (tokens.length != expectedTokens.length || amounts.length != expectedAmounts.length) revert InvalidAmount();
        for (uint256 i; i < tokens.length; ++i) {
            if (tokens[i] != expectedTokens[i] || amounts[i] != expectedAmounts[i]) revert InvalidAmount();
        }
    }
    function _fund(address[] memory tokens, uint256[] memory amounts, address from, address recipient)
        private returns (uint256[] memory beforeBalances) {
        beforeBalances = new uint256[](tokens.length);
        for (uint256 i; i < tokens.length; ++i) {
            beforeBalances[i] = IERC20(tokens[i]).balanceOf(address(this));
            ExactToken.pull(tokens[i], from, amounts[i]);
            IERC20(tokens[i]).forceApprove(recipient, amounts[i]);
        }
    }
    function _settled(address[] memory tokens, uint256[] memory beforeBalances, address recipient) private {
        for (uint256 i; i < tokens.length; ++i) {
            IERC20(tokens[i]).forceApprove(recipient, 0);
            if (IERC20(tokens[i]).balanceOf(address(this)) != beforeBalances[i]) revert InvalidState();
        }
    }
    function send(uint256 destinationChain, address destinationAdapter, address[] calldata tokens,
        uint256[] calldata amounts, bytes calldata payload) external payable onlyModule(Ids.BRIDGE) live nonReentrant returns (bytes32 receipt) {
        BridgeMessage memory m = abi.decode(payload, (BridgeMessage));
        IZZZRoutes registry = IZZZRoutes(access.module(Ids.ROUTES));
        (Route memory r,) = registry.get(m.routeId);
        bytes32 id = registry.transportPolicyId(m.routeId);
        if (!canSend(m.routeId) || m.nonce == 0 || r.destinationChain != destinationChain ||
            r.destinationAdapter != destinationAdapter) revert InvalidConfiguration();
        TransportPolicy memory p = policies[id];
        (address[] memory expectedTokens, uint256[] memory expectedAmounts) = BridgeAssets.assets(r, m, false);
        _vector(expectedTokens, expectedAmounts, tokens, amounts);
        uint256[] memory beforeBalances = _fund(expectedTokens, expectedAmounts, msg.sender, p.sourceProvider);
        receipt = IZZZTransportProvider(p.sourceProvider).send{value: msg.value}(id, destinationChain,
            p.destinationProvider, p.destinationRouter, tokens, amounts, abi.encode(TransportEnvelope(1, id, payload)));
        if (receipt == bytes32(0) || !_providerValid(p.sourceProvider, p.sourceCodeHash,
            p.sourceConfigurationHash, p.channelId)) revert InvalidState();
        _settled(expectedTokens, beforeBalances, p.sourceProvider);
        emit TransportSent(id, m.routeId, m.nonce, receipt);
    }
    function onProviderMessage(uint256 authenticatedSourceChain, address authenticatedSourceRouter,
        address[] calldata actualDestinationTokens, uint256[] calldata actualAmounts, bytes calldata envelope) external nonReentrant {
        if (!access.isSealed()) revert NotReady();
        TransportEnvelope memory e = abi.decode(envelope, (TransportEnvelope));
        if (e.version != 1 || !policyExists[e.policyId]) revert InvalidConfiguration();
        TransportPolicy memory p = policies[e.policyId];
        if (msg.sender != p.destinationProvider || p.destinationChain != block.chainid || p.destinationRouter != address(this) ||
            authenticatedSourceChain != p.sourceChain || authenticatedSourceRouter != p.sourceRouter ||
            !_providerValid(p.destinationProvider, p.destinationCodeHash, p.destinationConfigurationHash, p.channelId)) revert Unauthorized();
        BridgeMessage memory m = abi.decode(e.payload, (BridgeMessage));
        IZZZRoutes registry = IZZZRoutes(access.module(Ids.ROUTES));
        (Route memory r,) = registry.get(m.routeId);
        if (registry.transportPolicyId(m.routeId) != e.policyId || !matchesRoute(e.policyId, r) || m.nonce == 0) revert InvalidConfiguration();
        // The economic adapter's nonce domain spans providers and policy versions.
        bytes32 deliveryId = keccak256(abi.encode(authenticatedSourceChain, r.sourceAdapter, m.nonce));
        if (processed[deliveryId]) revert InvalidState();
        processed[deliveryId] = true;
        (address[] memory tokens, uint256[] memory amounts) = BridgeAssets.assets(r, m, true);
        _vector(tokens, amounts, actualDestinationTokens, actualAmounts);
        address bridge = access.module(Ids.BRIDGE);
        uint256[] memory beforeBalances = _fund(tokens, amounts, msg.sender, bridge);
        IZZZTransportReceiver(bridge).onMessage(authenticatedSourceChain, r.sourceAdapter, e.payload);
        if (!_providerValid(p.destinationProvider, p.destinationCodeHash,
            p.destinationConfigurationHash, p.channelId)) revert InvalidState();
        _settled(tokens, beforeBalances, bridge);
        emit TransportReceived(e.policyId, m.routeId, m.nonce, deliveryId);
    }
}
