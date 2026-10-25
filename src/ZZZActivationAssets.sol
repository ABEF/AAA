// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZOracle} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";

interface IActivationAssetsFactoryIdentity { function access() external view returns (address); }

/// @notice Governed source-contribution admission, separate from existing LP,
/// reward, valuation and unwind permissions. No assets are held or transferred.
contract ZZZActivationAssets is ZZZModule {
    address public immutable registry;
    uint256 public constant SOURCE_POLICY_VERSION = 1;
    /// @notice The reviewed current ZZZ contract, not an arbitrary input list.
    /// Native ETH remains address zero; a new token requires a new deployment.
    address public zzz;
    // Native currency has no deployed runtime. This explicit identity pin must
    // never be interpreted as a runtime code hash or as a missing policy.
    bytes32 public constant NATIVE_ASSET_CODE_HASH = keccak256("ZZZ_NATIVE_ETH_V1");
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
    event ZZZIdentityConfigured(address indexed token, bytes32 codeHash, bytes32 reviewHash);

    /// @dev The controller's fixed factory creates the Registry's unique child.
    constructor(address controller, address poolRegistry) ZZZModule(controller) {
        if (poolRegistry == address(0) || msg.sender != access.activationAssetsFactory() ||
            IActivationAssetsFactoryIdentity(msg.sender).access() != controller) revert InvalidConfiguration();
        registry = poolRegistry;
    }

    function policyCount() external view returns (uint256) { return history.length; }
    function policyAt(uint256 ordinal) external view returns (bytes32) { return history[ordinal]; }

    /// @notice Only native ETH and the reviewed current ZZZ are user inputs.
    /// Target-pair currencies and marketplace royalty currencies are separate.
    function isContributionAsset(address token) public view returns (bool) {
        return token == address(0) || (zzz != address(0) && token == zzz);
    }

    /// @notice Bind the ZZZ identity once, before sealing, after validating its
    /// code, precision and dual-price policy. It cannot be replaced or relabelled.
    function configureZZZ(address token, bytes32 expectedCodeHash, bytes32 reviewHash)
        external onlyGovernance returns (bytes32 id) {
        if (zzz != address(0) || access.isSealed() || token == address(0) || reviewHash == bytes32(0)) revert InvalidConfiguration();
        uint8 decimals = _validate(token, expectedCodeHash);
        zzz = token;
        id = _record(Policy(token, true, expectedCodeHash, reviewHash, decimals, false));
        emit ZZZIdentityConfigured(token, expectedCodeHash, reviewHash);
    }

    /// @notice Append a reviewed source policy. After seal only the controller's
    /// immediate governance can call configuration entrypoints. It cannot add a
    /// third input currency or change the fixed ZZZ identity.
    /// Disabling deliberately reads no token, price or implementation state.
    function setAsset(address token, bool enabled, bytes32 expectedCodeHash, bytes32 reviewHash)
        external onlyGovernance returns (bytes32 id) {
        if (reviewHash == bytes32(0)) revert InvalidConfiguration();
        bytes32 previous = activePolicy[token];
        uint8 decimals = previous == bytes32(0) ? 0 : policies[previous].decimals;
        if (enabled) {
            if (!isContributionAsset(token)) revert InvalidConfiguration();
            decimals = _validate(token, expectedCodeHash);
        }
        return _record(Policy(token, enabled, expectedCodeHash, reviewHash, decimals, false));
    }

    /// @notice Only the immutable Registry can initially admit a pool currency.
    /// A known policy is NEVER overwritten: reconfiguring a pool cannot undo a
    /// disabled currency, replace an old pin or silently approve changed code.
    function admitPoolAsset(address token) external returns (bytes32 id) {
        if (msg.sender != registry) revert Unauthorized();
        id = activePolicy[token];
        if (id != bytes32(0)) return id;
        bytes32 codeHash = token == address(0) ? NATIVE_ASSET_CODE_HASH : token.codehash;
        uint8 decimals = _validate(token, codeHash);
        // This binds the authenticated pool-configuration admission, not an
        // independent audit. Explicit reviews use governance's supplied hash.
        bytes32 admissionReference = keccak256(abi.encode("ZZZ_POOL_ASSET_ADMISSION_V1", registry, token, codeHash, decimals));
        // A target pair may use another accounting currency (for example WETH).
        // Pool admission must not make that currency an externally supplied asset.
        return _record(Policy(token, isContributionAsset(token), codeHash, admissionReference, decimals, true));
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
        if (token == address(0)) {
            if (expectedCodeHash != NATIVE_ASSET_CODE_HASH) revert InvalidConfiguration();
            decimals = 18;
        } else {
            if (expectedCodeHash == bytes32(0) || token.code.length == 0 || token.codehash != expectedCodeHash) {
                revert InvalidConfiguration();
            }
            decimals = IERC20Metadata(token).decimals();
        }
        if (decimals > 18) revert InvalidConfiguration();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        if (oracle.tokenDecimals(token) != decimals || oracle.price(token) == 0) revert InvalidConfiguration();
    }

    /// @notice Price a newly supplied currency only. A zero side never consults
    /// its admission or dependency, preserving one-sided contributions.
    function value(address token, uint256 amount) external view returns (uint256) {
        if (amount == 0) return 0;
        if (!isContributionAsset(token)) revert InvalidConfiguration();
        Policy memory policy = policies[activePolicy[token]];
        if (!policy.enabled || (token == address(0) ?
            policy.expectedCodeHash != NATIVE_ASSET_CODE_HASH || policy.decimals != 18 :
            policy.expectedCodeHash == bytes32(0) || token.code.length == 0 || token.codehash != policy.expectedCodeHash)) {
            revert InvalidConfiguration();
        }
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        if (oracle.tokenDecimals(token) != policy.decimals) revert InvalidConfiguration();
        return oracle.value(token, amount);
    }
}
