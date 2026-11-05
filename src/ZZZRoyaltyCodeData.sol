// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Construction-only fixed-payload carrier; deployed bytes are data.
/// @dev PUSH0/PUSH0/REVERT prevents ordinary calls and ETH payments. There is no
/// dispatcher, forwarding, selfdestruct, storage, authority or withdrawal path.
contract ZZZRoyaltyCodeData {
    error DataTooLong();
    constructor(bytes memory data) {
        if (data.length > 24573) revert DataTooLong();
        bytes memory runtime = abi.encodePacked(hex"5f5ffd",data);
        assembly ("memory-safe") { return(add(runtime,32),mload(runtime)) }
    }
}
