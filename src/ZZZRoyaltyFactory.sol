// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZRoyaltyRewards} from "./ZZZRoyaltyRewards.sol";
import {ZZZRoyaltyCodeData} from "./ZZZRoyaltyCodeData.sol";

/// @notice Fixed, source-bound creation bytes live in two immutable data children.
/// Only typed NFT/controller binding can execute the reconstructed payload.
contract ZZZRoyaltyFactory {
    uint256 public constant CODE_STORAGE_VERSION = 2;
    uint256 private constant PART_DATA_LIMIT = 24573;
    uint256 private constant DATA_OFFSET = 3;
    address public immutable controller;
    bytes32 public immutable royaltyCodeHash;
    uint256 public immutable creationCodeLength;
    address public immutable part0;
    address public immutable part1;
    bytes32 public immutable part0CodeHash;
    bytes32 public immutable part1CodeHash;
    error InvalidCreationCode();

    constructor() {
        controller = msg.sender;
        bytes memory code = type(ZZZRoyaltyRewards).creationCode;
        uint256 length = code.length;
        if (length == 0 || length > 2 * PART_DATA_LIMIT) revert InvalidCreationCode();
        royaltyCodeHash = keccak256(code);
        creationCodeLength = length;
        uint256 first = length > PART_DATA_LIMIT ? PART_DATA_LIMIT : length;
        (part0,part0CodeHash) = _storePart(code,0,first);
        // Exactly two authenticated children, including a prefix-only second
        // child if a future source payload fits entirely in the first part.
        (part1,part1CodeHash) = _storePart(code,first,length-first);
    }

    function _storePart(bytes memory code,uint256 start,uint256 length)
        private returns(address pointer,bytes32 expectedHash) {
        bytes memory data = new bytes(length);
        assembly ("memory-safe") { mcopy(add(data,32),add(add(code,32),start),length) }
        expectedHash = keccak256(abi.encodePacked(hex"5f5ffd",data));
        pointer = address(new ZZZRoyaltyCodeData(data));
        _checkPart(pointer,length,expectedHash);
    }

    function _checkPart(address pointer,uint256 length,bytes32 expectedHash) private view {
        if (pointer.code.length != length + DATA_OFFSET || pointer.codehash != expectedHash)
            revert InvalidCreationCode();
    }

    function create() external returns (ZZZRoyaltyRewards receiver) {
        uint256 length = creationCodeLength;
        uint256 first = length > PART_DATA_LIMIT ? PART_DATA_LIMIT : length;
        address head = part0;
        address tail = part1;
        _checkPart(head,first,part0CodeHash);
        _checkPart(tail,length-first,part1CodeHash);
        bytes memory code = new bytes(length);
        assembly ("memory-safe") {
            extcodecopy(head,add(code,32),3,first)
            extcodecopy(tail,add(add(code,32),first),3,sub(length,first))
        }
        if (keccak256(code) != royaltyCodeHash) revert InvalidCreationCode();
        bytes memory init = abi.encodePacked(code,abi.encode(msg.sender));
        address deployed;
        assembly ("memory-safe") { deployed := create(0,add(init,32),mload(init)) }
        if (deployed == address(0)) revert InvalidCreationCode();
        receiver = ZZZRoyaltyRewards(payable(deployed));
        receiver.bindCanonicalController(controller);
    }
}
