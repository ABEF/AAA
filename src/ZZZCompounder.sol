// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {IZZZVault} from "./interfaces/IZZZ.sol";

/// @notice Budget never passes through the keeper or this coordinator.
contract ZZZCompounder is ZZZModule {
    constructor(address controller) ZZZModule(controller) {}
    function compound(uint256 id, uint128 minimumLiquidity, uint256 deadline) external onlyKeeper live operating {
        _deadline(deadline);
        if (minimumLiquidity == 0) revert InvalidAmount();
        IZZZVault(access.module(Ids.VAULT)).compound(id, minimumLiquidity, deadline);
    }
}
