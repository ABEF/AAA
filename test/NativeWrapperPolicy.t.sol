// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {MockAccess} from "./mocks/Mocks.sol";

/// @dev Registry admission receives no native funds. The former optional WETH
/// policy suite is archived; actual native settlement and converter safety tests
/// remain in NativeAssetFoundation/NativeCustody and the conversion suites.
contract RegistryNativeFundsBoundaryTest is Test {
    function testRegistryDoesNotAcceptNativeFunds() public {
        MockAccess access = new MockAccess();
        ZZZPoolRegistry registry = new ZZZPoolRegistry(address(access));
        vm.deal(address(this), 1);
        (bool ok,) = address(registry).call{value: 1}("");
        assertFalse(ok);
        assertEq(address(registry).balance, 0);
        assertEq(address(this).balance, 1);
    }
}
