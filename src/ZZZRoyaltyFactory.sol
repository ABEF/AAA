// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZRoyaltyRewards} from "./ZZZRoyaltyRewards.sol";

/// @notice Fixed factory keeps the royalty ledger initcode outside NFT initcode.
/// It creates a fresh ledger for the caller and binds the controller atomically.
contract ZZZRoyaltyFactory {
    address public immutable controller;
    constructor() { controller = msg.sender; }
    function create() external returns (ZZZRoyaltyRewards receiver) {
        receiver = new ZZZRoyaltyRewards(msg.sender);
        receiver.bindCanonicalController(controller);
    }
}
