// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZRoyaltyRewards} from "./ZZZRoyaltyRewards.sol";

/// @notice Fixed factory stores one source-bound creation payload at deployment.
/// Runtime never embeds that large payload or accepts caller-supplied code.
/// Each typed create binds the caller NFT and fixed controller atomically.
contract ZZZRoyaltyFactory {
    address public immutable controller;
    bytes32 public immutable royaltyCodeHash;
    bytes private royaltyCreationCode;
    error InvalidCreationCode();

    constructor() {
        controller = msg.sender;
        bytes memory code = type(ZZZRoyaltyRewards).creationCode;
        royaltyCreationCode = code;
        royaltyCodeHash = keccak256(code);
    }

    function create() external returns (ZZZRoyaltyRewards receiver) {
        bytes memory code = royaltyCreationCode;
        if (keccak256(code) != royaltyCodeHash) revert InvalidCreationCode();
        bytes memory init = abi.encodePacked(code,abi.encode(msg.sender));
        address deployed;
        assembly ("memory-safe") { deployed := create(0,add(init,32),mload(init)) }
        if (deployed == address(0)) revert InvalidCreationCode();
        receiver = ZZZRoyaltyRewards(payable(deployed));
        receiver.bindCanonicalController(controller);
    }
}
