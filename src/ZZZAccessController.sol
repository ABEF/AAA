// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {TimelockController} from "@openzeppelin/contracts/governance/TimelockController.sol";
import {IZZZBound, IZZZAccess} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";

/// @notice Timelocked configuration; module addresses become immutable at seal().
/// The timelock cannot replace the vault or execute calls as the vault.
contract ZZZAccessController is TimelockController {
    mapping(bytes32 => address) public module;
    mapping(address => bool) public keepers;
    mapping(address => bool) public guardians;
    address public bootstrap;
    bool public isSealed;
    bool public paused;
    event ModuleBound(bytes32 indexed id, address indexed implementation);
    event SystemSealed();
    event PauseChanged(bool paused);
    event KeeperChanged(address indexed account, bool enabled);
    error Unauthorized();
    error InvalidConfiguration();

    constructor(uint256 delay, address[] memory proposers, address[] memory executors, address initialKeeper,
        address initialGuardian) TimelockController(delay, proposers, executors, address(0)) {
        if (delay < 1 days || proposers.length == 0 || executors.length == 0 ||
            initialKeeper == address(0) || initialGuardian == address(0)) revert InvalidConfiguration();
        for (uint256 i; i < proposers.length; ++i) {
            if (proposers[i] == address(0)) revert InvalidConfiguration();
        }
        bootstrap = msg.sender;
        keepers[initialKeeper] = true;
        guardians[initialGuardian] = true;
    }
    function canConfigure(address account) public view returns (bool) {
        return account == address(this) || (!isSealed && account == bootstrap);
    }
    function bind(bytes32 id, address implementation) external {
        if (msg.sender != bootstrap || isSealed) revert Unauthorized();
        if (implementation.code.length == 0 || module[id] != address(0) ||
            address(IZZZBound(implementation).access()) != address(this)) revert InvalidConfiguration();
        module[id] = implementation;
        emit ModuleBound(id, implementation);
    }
    function seal() external {
        if (msg.sender != bootstrap || isSealed) revert Unauthorized();
        bytes32[15] memory required = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.POWER,
            Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION, Ids.BRIDGE,
            Ids.RECEIVER, Ids.ORACLE, Ids.POOLS, Ids.ROUTES];
        for (uint256 i; i < required.length; ++i) {
            if (module[required[i]].code.length == 0) revert InvalidConfiguration();
            for (uint256 j; j < i; ++j) {
                if (module[required[i]] == module[required[j]]) revert InvalidConfiguration();
            }
        }
        isSealed = true;
        bootstrap = address(0);
        emit SystemSealed();
    }
    function setKeeper(address who, bool enabled) external {
        if (!canConfigure(msg.sender) || who == address(0)) revert Unauthorized();
        keepers[who] = enabled;
        emit KeeperChanged(who, enabled);
    }
    function setGuardian(address who, bool enabled) external {
        if (!canConfigure(msg.sender) || who == address(0)) revert Unauthorized();
        guardians[who] = enabled;
    }
    function setPaused(bool state) external {
        if (!canConfigure(msg.sender) && !(state && guardians[msg.sender])) revert Unauthorized();
        paused = state;
        emit PauseChanged(state);
    }
    /// @notice The governance delay is fixed for the lifetime of this deployment.
    function updateDelay(uint256) external pure override {
        revert InvalidConfiguration();
    }
}
