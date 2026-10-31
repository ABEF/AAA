// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IZZZAccess} from "../../src/interfaces/IZZZ.sol";
import {MockPools} from "../mocks/Mocks.sol";
import {VaultPolicyMock,VaultLiquidityMock} from "../VaultAccounting.t.sol";

// TEST ONLY: unchanged mock admission/venue policy shared by canonical suites.
contract PreparationPools is MockPools {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); activationAssets=address(this); }
    // TEST ONLY: admission is explicitly mocked; economic accounting is real.
    address public zzz;
    function setTestZZZIdentity(address token) external { zzz=token; }
}

contract PreparationPolicy is VaultPolicyMock {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}

contract PreparationVenue is VaultLiquidityMock {
    IZZZAccess public immutable access;
    constructor(address controller, address a, address b) VaultLiquidityMock(a, b) { access = IZZZAccess(controller); }
}
