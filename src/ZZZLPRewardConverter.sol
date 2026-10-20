// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZRoyaltyConverter} from "./ZZZRoyaltyConverter.sol";

/// @notice Dedicated LP-reward instance of the reviewed fixed-ledger converter.
/// Shares execution guards with royalty conversion, but never its custody or ledger.
contract ZZZLPRewardConverter is ZZZRoyaltyConverter {
    constructor(address controller, address rewards, address wrappedETH)
        ZZZRoyaltyConverter(controller, rewards, wrappedETH) {}
}
