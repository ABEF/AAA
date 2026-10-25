// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZV3VenueValidation} from "../src/libraries/ZZZV3VenueValidation.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";

error UnexpectedV3DependencyRead(uint8 stage);

// TEST ONLY: each later getter poisons the call if an earlier identity already
// mismatched. This distinguishes the established short-circuit order from an
// eager read/refactor that contacts all untrusted dependencies before rejecting.
contract V3IdentityPoolFixture {
    address private immutable expectedFactory;
    address private immutable first;
    address private immutable second;
    uint8 private failure = 6;
    constructor(address factory, address source, address output) {
        expectedFactory = factory;
        first = source < output ? source : output;
        second = source < output ? output : source;
    }
    function setFailure(uint8 stage) external { failure = stage; }
    function factory() external view returns (address) {
        if (failure < 2) revert UnexpectedV3DependencyRead(2);
        return failure == 2 ? address(0) : expectedFactory;
    }
    function token0() external view returns (address) {
        if (failure < 3) revert UnexpectedV3DependencyRead(3);
        return failure == 3 ? address(0) : first;
    }
    function token1() external view returns (address) {
        if (failure < 4) revert UnexpectedV3DependencyRead(4);
        return failure == 4 ? address(0) : second;
    }
    function fee() external view returns (uint24) {
        if (failure < 5) revert UnexpectedV3DependencyRead(5);
        return failure == 5 ? 501 : 500;
    }
}
contract V3IdentityFactoryFixture {
    address public pool;
    uint8 private failure = 6;
    function configure(address value, uint8 stage) external { pool = value; failure = stage; }
    function getPool(address, address, uint24) external view returns (address) {
        if (failure == 0) revert UnexpectedV3DependencyRead(1);
        return failure == 1 ? address(0) : pool;
    }
}
contract V3IdentityRouterFixture {
    address private immutable expectedFactory;
    uint8 private failure = 6;
    constructor(address factory) { expectedFactory = factory; }
    function setFailure(uint8 stage) external { failure = stage; }
    function factory() external view returns (address) {
        return failure == 0 ? address(0) : expectedFactory;
    }
}
contract V3IdentityValidationHarness {
    function validate(address router, address factory, address pool, address source, address output, uint24 fee)
        external view {
        ZZZV3VenueValidation.validate(router, factory, pool, source, output, fee);
    }
}

contract V3VenueValidationTest is Test {
    V3IdentityValidationHarness private validation;
    V3IdentityRouterFixture private router;
    V3IdentityFactoryFixture private factory;
    V3IdentityPoolFixture private pool;
    address private constant SOURCE = address(0x2000);
    address private constant OUTPUT = address(0x1000);
    function setUp() public {
        factory = new V3IdentityFactoryFixture();
        pool = new V3IdentityPoolFixture(address(factory), SOURCE, OUTPUT);
        factory.configure(address(pool), 6);
        router = new V3IdentityRouterFixture(address(factory));
        validation = new V3IdentityValidationHarness();
    }
    function testMatchingVenueAcceptsBothEndpointOrders() public view {
        validation.validate(address(router), address(factory), address(pool), SOURCE, OUTPUT, 500);
        validation.validate(address(router), address(factory), address(pool), OUTPUT, SOURCE, 500);
    }
    function testEachMismatchPreservesRevertSelectorAndSkipsLaterPoisonedReads() public {
        for (uint8 stage; stage < 6; ++stage) {
            router.setFailure(stage); factory.configure(address(pool), stage); pool.setFailure(stage);
            vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
            validation.validate(address(router), address(factory), address(pool), SOURCE, OUTPUT, 500);
        }
    }
}
