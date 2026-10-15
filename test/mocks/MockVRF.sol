// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZVRFCoordinator} from "../../src/ZZZNFT.sol";

interface IMockVRFConsumer {
    function rawFulfillRandomWords(uint256 requestId, uint256[] calldata words) external;
}

/// @dev TEST ONLY. No proof verification, subscription backing or network
/// authentication. Mock fulfillment is never production VRF evidence.
contract MockVRF is IZZZVRFCoordinator {
    uint256 public sequence;
    mapping(uint256 => address) public consumer;
    bytes32 public lastKeyHash; uint256 public lastSubscriptionId;
    uint16 public lastConfirmations; uint32 public lastGasLimit; uint32 public lastNumWords;
    bytes public lastExtraArgs;
    bool public failRequests;
    function setFailRequests(bool fail) external { failRequests = fail; }
    function requestRandomWords(RandomWordsRequest calldata request) external returns (uint256 requestId) {
        require(!failRequests, "mock subscription unavailable");
        requestId = ++sequence; consumer[requestId] = msg.sender;
        lastKeyHash = request.keyHash; lastSubscriptionId = request.subId;
        lastConfirmations = request.requestConfirmations; lastGasLimit = request.callbackGasLimit;
        lastNumWords = request.numWords; lastExtraArgs = request.extraArgs;
    }
    function fulfill(uint256 requestId, uint256 word0, uint256 word1) external {
        uint256[] memory words = new uint256[](2); words[0] = word0; words[1] = word1;
        IMockVRFConsumer(consumer[requestId]).rawFulfillRandomWords(requestId, words);
    }
    function fulfillMalformed(uint256 requestId, uint256 length) external {
        IMockVRFConsumer(consumer[requestId]).rawFulfillRandomWords(requestId, new uint256[](length));
    }
}
