// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @dev TEST ONLY deterministic typed-v3 identity boundaries. Kept separate
/// from retired unreviewed-Entry/native-wrapper test scaffolding.
contract EntryFactoryFixture {
    address public selected;
    function set(address value_) external { selected = value_; }
    function getPool(address, address, uint24) external view returns (address) { return selected; }
}

contract EntryPoolFixture {
    address public immutable factory;
    address public immutable token0;
    address public immutable token1;
    uint24 public constant fee = 500;
    constructor(address factory_, address a, address b) {
        factory = factory_; token0 = a < b ? a : b; token1 = a < b ? b : a;
    }
}
