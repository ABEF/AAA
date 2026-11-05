// Historical conversion fixture only; not fresh production code.
// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZRewardConverter} from "../../src/base/ZZZRewardConverter.sol";

/// @notice Royalty-only instance of the fixed-ledger converter. It shares reviewed
/// execution guards with LP conversion, never custody, balances or ledger rights.
contract ZZZRoyaltyConverter is ZZZRewardConverter {
    constructor(address controller, address receiver, address wrappedETH)
        ZZZRewardConverter(controller, receiver, wrappedETH) {}
}
