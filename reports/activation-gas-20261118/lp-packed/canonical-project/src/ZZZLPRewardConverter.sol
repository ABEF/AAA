// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZRewardConverter} from "./base/ZZZRewardConverter.sol";

/// @notice Fixed-ledger LP fee conversion to native ETH. NFT-sale royalties
/// remain separately accounted and claimed in their original currencies.
contract ZZZLPRewardConverter is ZZZRewardConverter {
    constructor(address controller, address rewards, address wrappedETH)
        ZZZRewardConverter(controller, rewards, wrappedETH) {}
}
