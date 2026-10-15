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
    constructor(address controller) {
        if (controller.code.length == 0) revert InvalidConfiguration();
        access = IZZZAccess(controller);
    }
    modifier onlyModule(bytes32 id) {
        _checkModule(id);
        _;
    }
    function _checkModule(bytes32 id) private view {
        if (!access.isSealed() || msg.sender != access.module(id)) revert Unauthorized();
    }
    modifier onlyGovernance() {
        _checkGovernance();
        _;
    }
    function _checkGovernance() private view {
        if (!access.canConfigure(msg.sender)) revert Unauthorized();
    }
    modifier onlyKeeper() {
        _checkKeeper();
        _;
    }
    function _checkKeeper() private view {
        if (!access.isSealed() || !access.keepers(msg.sender)) revert Unauthorized();
    }
    modifier live() {
        _checkLive();
        _;
    }
    function _checkLive() private view {
        if (!access.isSealed()) revert NotReady();
        if (access.paused()) revert Paused();
    }
    function _deadline(uint256 deadline) internal view {
        if (deadline < block.timestamp || deadline > block.timestamp + 10 minutes) revert Expired();
    }
}
