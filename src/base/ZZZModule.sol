// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZAccess} from "../interfaces/IZZZ.sol";

abstract contract ZZZModule {
    IZZZAccess public immutable access;
    error Unauthorized();
    error InvalidConfiguration();
    error NotReady();
    error Paused();
    error InvalidState();
    error InvalidAmount();
    error Slippage();
    error Expired();
    error Preparing();
    error CanonicalLocked();
    error LPExitLocked();
    constructor(address controller) {
        if (controller.code.length == 0) revert InvalidConfiguration();
        access = IZZZAccess(controller);
    }
    modifier onlyModule(bytes32 id) {
        _checkModule(id);
        _;
    }
    function _checkModule(bytes32 id) private view {
        if (!access.moduleAuthorized(id, msg.sender)) revert Unauthorized();
    }
    modifier onlyGovernance() {
        _checkGovernance();
        _;
        _checkGovernance();
    }
    function _checkGovernance() private view {
        if (!access.canConfigure(msg.sender)) revert Unauthorized();
    }
    /// @dev Only the selected governance wallet may drain during preparation. This does
    /// not grant a caller generic configuration or execution authority.
    modifier onlyDrainGovernance() {
        _checkDrainGovernance();
        _;
    }
    function _checkDrainGovernance() private view {
        _checkAccounting();
        if (msg.sender != access.governance() && !access.canConfigure(msg.sender)) revert Unauthorized();
    }
    /// @dev Check again after callbacks: a governance announcement cannot start
    /// inside new work and let that work finish after preparation.
    modifier operating() {
        _checkOperating();
        _;
        _checkOperating();
    }
    function _checkOperating() internal view {
        if (access.preparationActive()) revert Preparing();
        _checkAccounting();
    }
    /// @dev Collective principal exit is terminal, independently of pause and
    /// canonical ownership. Check after callbacks so retirement cannot begin
    /// inside an otherwise valid contribution or maintenance operation.
    modifier principalOperating() {
        _checkPrincipalOperating();
        _;
        _checkPrincipalOperating();
    }
    function _checkPrincipalOperating() private view {
        if (access.lpExitStarted()) revert LPExitLocked();
    }
    modifier onlyHandoff() {
        if (msg.sender != access.canonicalHandoff()) revert Unauthorized();
        _;
    }
    modifier canonicalAccounting() {
        _checkAccounting();
        _;
        _checkAccounting();
    }
    function _checkAccounting() internal view {
        if (access.canonicalState() != 0) revert CanonicalLocked();
    }
    modifier onlyKeeper() {
        _checkKeeper();
        _;
    }
    function _checkKeeper() private view {
        if (!access.keeperAuthorized(msg.sender)) revert Unauthorized();
    }
    modifier live() {
        _checkLive();
        _;
    }
    function _checkLive() private view {
        _checkAccounting();
        if (!access.isSealed()) revert NotReady();
        if (access.paused()) revert Paused();
    }
    function _deadline(uint256 deadline) internal view {
        if (deadline < block.timestamp || deadline > block.timestamp + 10 minutes) revert Expired();
    }
}
