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
        if (!access.isSealed() || msg.sender != access.module(id)) revert Unauthorized();
        _;
    }
    modifier onlyGovernance() {
        if (!access.canConfigure(msg.sender)) revert Unauthorized();
        _;
    }
    modifier onlyKeeper() {
        if (!access.isSealed() || !access.keepers(msg.sender)) revert Unauthorized();
        _;
    }
    modifier live() {
        if (!access.isSealed()) revert NotReady();
        if (access.paused()) revert Paused();
        _;
    }
    function _deadline(uint256 deadline) internal view {
        if (deadline < block.timestamp || deadline > block.timestamp + 10 minutes) revert Expired();
    }
}
