// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZRewardConverter} from "./base/ZZZRewardConverter.sol";

/// @notice LP-only instance of the fixed-ledger converter. It shares reviewed
/// execution guards with royalty conversion, never custody, balances or ledger rights.
contract ZZZLPRewardConverter is ZZZRewardConverter {
    constructor(address controller, address rewards, address wrappedETH)
        ZZZRewardConverter(controller, rewards, wrappedETH) {}
}
