// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZRewards, IZZZNFT} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";

/// @notice Explicit v2 policy: Power = lifetime oracle-USD of user contributions.
/// Compounded fees and market appreciation do not increase Power. No manual setter.
/// Local weights are preserved while canonical liquidity is in flight/remote.
contract ZZZPower is ZZZModule {
    uint256 public constant MAX_TOTAL_POWER = 1e36;
    mapping(uint256 => uint256) public powerOf;
    uint256 public totalPower;
    event PowerIncreased(uint256 indexed nftId, uint256 increment, uint256 newPower);
    constructor(address controller) ZZZModule(controller) {}
    function add(uint256 id, uint256 amount) external onlyModule(Ids.VAULT) {
        if (amount == 0 || amount > MAX_TOTAL_POWER - totalPower) revert InvalidAmount();
        // This checkpoint MUST happen before either the local or total weight changes.
        IZZZRewards(access.module(Ids.REWARDS)).checkpointAll(id);
        powerOf[id] += amount;
        totalPower += amount;
        emit PowerIncreased(id, amount, powerOf[id]);
    }
}
