// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Optional immutable AggregatorV3-shaped reader for a reviewed Pyth
/// Core feed. This does not publish updates, authenticate provider independence,
/// pin proxy implementations or qualify a production price service.
/// @dev Pyth publishTime is used as the synthetic round identity and as both
/// original observation timestamps. No freshness is manufactured by this reader.
contract ZZZPythPriceFeed {
    address public immutable core;
    bytes32 public immutable expectedCoreCodeHash;
    bytes32 public immutable feedId;
    bytes32 public immutable reviewHash;
    int32 public immutable expectedExponent;
    uint32 public immutable maxAge;
    uint16 public immutable maxConfidenceBps;
    uint8 public immutable decimals;
    uint256 public constant SOURCE_CALL_GAS = 300_000;
    uint16 public constant MAX_CONFIDENCE_BPS = 300;
    bytes4 private constant GET_PRICE_UNSAFE = bytes4(keccak256("getPriceUnsafe(bytes32)"));

    error InvalidConfiguration();
    error InvalidObservation();

    constructor(address source, bytes32 codeHash, bytes32 id, int32 exponent,
        uint32 age, uint16 confidenceBps, bytes32 review) {
        if (source.code.length == 0 || codeHash == bytes32(0) || source.codehash != codeHash ||
            id == bytes32(0) || review == bytes32(0) || exponent < -18 || exponent > 0 ||
            age == 0 || age > 1 days || confidenceBps > MAX_CONFIDENCE_BPS) {
            revert InvalidConfiguration();
        }
        core = source;
        expectedCoreCodeHash = codeHash;
        feedId = id;
        expectedExponent = exponent;
        maxAge = age;
        maxConfidenceBps = confidenceBps;
        decimals = uint8(uint32(-exponent));
        reviewHash = review;
    }

    function latestRoundData() external view returns
        (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound) {
        address source = core;
        if (source.codehash != expectedCoreCodeHash) revert InvalidObservation();
        bytes32 id = feedId;
        bytes4 selector = GET_PRICE_UNSAFE;
        bool success;
        uint256 returned;
        uint256 gasLimit = SOURCE_CALL_GAS;
        // Never allocate or copy an upstream's unbounded return/revert data.
        assembly ("memory-safe") {
            let input := mload(0x40)
            mstore(input, selector)
            mstore(add(input, 4), id)
            success := staticcall(gasLimit, source, input, 36, 0, 0)
            returned := returndatasize()
        }
        if (!success || returned != 128) revert InvalidObservation();
        bytes memory data = new bytes(128);
        assembly ("memory-safe") { returndatacopy(add(data, 32), 0, 128) }
        // Decode wide words first so malformed sign extension or high bits
        // produce a bounded domain error instead of being silently truncated.
        uint256 confidence;
        int256 exponent;
        (answer, confidence, exponent, updatedAt) = abi.decode(data, (int256, uint256, int256, uint256));
        if (answer <= 0 || answer > type(int64).max || confidence > type(uint64).max ||
            exponent != int256(expectedExponent) || updatedAt == 0 || updatedAt > type(uint80).max ||
            updatedAt > block.timestamp || block.timestamp - updatedAt > maxAge ||
            confidence * 10_000 > uint256(answer) * maxConfidenceBps) revert InvalidObservation();
        roundId = uint80(updatedAt);
        startedAt = updatedAt;
        answeredInRound = roundId;
    }
}
