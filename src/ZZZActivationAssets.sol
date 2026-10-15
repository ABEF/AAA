// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZOracle} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";

/// @notice Governed source-contribution admission, separate from existing LP,
/// reward, valuation and unwind permissions. No assets are held or transferred.
contract ZZZActivationAssets is ZZZModule {
    address public immutable registry;
    struct Policy {
        address token;
        bool enabled;
        bytes32 expectedCodeHash;
        bytes32 reviewHash;
        uint8 decimals;
        bool poolAdmission;
    }
    mapping(bytes32 => Policy) public policies;
    mapping(address => bytes32) public activePolicy;
    bytes32[] private history;
    event AssetPolicyRecorded(bytes32 indexed id, address indexed token, bool enabled,
        bytes32 expectedCodeHash, bytes32 reviewHash, uint8 decimals, bool poolAdmission);
    event AssetPolicyActivated(address indexed token, bytes32 indexed previousPolicy, bytes32 indexed activePolicy);

    /// @dev Registry creates its immutable helper while under construction.
    constructor(address controller, address poolRegistry) ZZZModule(controller) {
        if (poolRegistry == address(0) || msg.sender != poolRegistry) revert InvalidConfiguration();
        registry = poolRegistry;
    }

    function policyCount() external view returns (uint256) { return history.length; }
    function policyAt(uint256 ordinal) external view returns (bytes32) { return history[ordinal]; }

    /// @notice Append a reviewed source policy. After seal only the controller's
    /// existing timelock can call governance configuration entrypoints.
    /// Disabling deliberately reads no token, price or implementation state.
    function setAsset(address token, bool enabled, bytes32 expectedCodeHash, bytes32 reviewHash)
        external onlyGovernance returns (bytes32 id) {
        if (token == address(0) || reviewHash == bytes32(0)) revert InvalidConfiguration();
        bytes32 previous = activePolicy[token];
        uint8 decimals = previous == bytes32(0) ? 0 : policies[previous].decimals;
        if (enabled) decimals = _validate(token, expectedCodeHash);
        return _record(Policy(token, enabled, expectedCodeHash, reviewHash, decimals, false));
    }

    /// @notice Only the immutable Registry can initially admit a pool currency.
    /// A known policy is NEVER overwritten: reconfiguring a pool cannot undo a
    /// disabled currency, replace an old pin or silently approve changed code.
    function admitPoolAsset(address token) external returns (bytes32 id) {
        if (msg.sender != registry) revert Unauthorized();
        if (token == address(0)) revert InvalidConfiguration();
        id = activePolicy[token];
        if (id != bytes32(0)) return id;
        bytes32 codeHash = token.codehash;
        uint8 decimals = _validate(token, codeHash);
        // This binds the authenticated pool-configuration admission, not an
        // independent audit. Explicit reviews use governance's supplied hash.
        bytes32 admissionReference = keccak256(abi.encode("ZZZ_POOL_ASSET_ADMISSION_V1", registry, token, codeHash, decimals));
        return _record(Policy(token, true, codeHash, admissionReference, decimals, true));
    }

    function _record(Policy memory policy) private returns (bytes32 id) {
        bytes32 previous = activePolicy[policy.token];
        // Ordinal is part of identity: previous records can never be overwritten
        // even when governance later returns to identical policy parameters.
        id = keccak256(abi.encode(address(this), history.length, policy));
        policies[id] = policy;
        history.push(id);
        activePolicy[policy.token] = id;
        emit AssetPolicyRecorded(id, policy.token, policy.enabled, policy.expectedCodeHash,
            policy.reviewHash, policy.decimals, policy.poolAdmission);
        emit AssetPolicyActivated(policy.token, previous, id);
    }

    function _validate(address token, bytes32 expectedCodeHash) private view returns (uint8 decimals) {
        if (expectedCodeHash == bytes32(0) || token.code.length == 0 || token.codehash != expectedCodeHash) {
            revert InvalidConfiguration();
        }
        decimals = IERC20Metadata(token).decimals();
        if (decimals > 18) revert InvalidConfiguration();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        if (oracle.tokenDecimals(token) != decimals || oracle.price(token) == 0) revert InvalidConfiguration();
    }

    /// @notice Price a newly supplied currency only. A zero side never consults
    /// its admission or dependency, preserving one-sided contributions.
    function value(address token, uint256 amount) external view returns (uint256) {
        if (amount == 0) return 0;
        Policy memory policy = policies[activePolicy[token]];
        if (!policy.enabled || policy.expectedCodeHash == bytes32(0) || token.code.length == 0 ||
            token.codehash != policy.expectedCodeHash) revert InvalidConfiguration();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        if (oracle.tokenDecimals(token) != policy.decimals) revert InvalidConfiguration();
        return oracle.value(token, amount);
    }
}
