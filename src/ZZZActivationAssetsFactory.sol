// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZActivationAssets} from "./ZZZActivationAssets.sol";

/// @notice Fixed, noncustodial deployment helper. Splits Registry initcode;
/// it cannot configure a child, replace one, execute calls or receive funds.
contract ZZZActivationAssetsFactory {
    address public immutable access;
    mapping(address => address) public assetsOf;
    error AlreadyCreated();
    constructor() { access=msg.sender; }
    function create() external returns(address child) {
        if (assetsOf[msg.sender]!=address(0)) revert AlreadyCreated();
        child=address(new ZZZActivationAssets(access,msg.sender));
        assetsOf[msg.sender]=child;
    }
}
