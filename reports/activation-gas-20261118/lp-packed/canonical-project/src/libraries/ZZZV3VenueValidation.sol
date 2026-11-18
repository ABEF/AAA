// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IV3RouteRouter, IV3RouteFactory, IV3RoutePool} from "../interfaces/IZZZV3Route.sol";
import {ZZZModule} from "../base/ZZZModule.sol";

/// @notice Read-only v3 venue identity checks shared by typed route policies.
/// Callers retain source/output admission and all runtime pins before this call.
/// No storage, approval, token movement or configurable execution target exists.
library ZZZV3VenueValidation {
    function validate(address router, address factory, address pool, address source, address output, uint24 fee)
        internal view {
        address a = source < output ? source : output;
        address b = source < output ? output : source;
        // Preserve the original short-circuit call order. A mismatch stops here;
        // it must not read a later untrusted dependency after earlier rejection.
        if (IV3RouteRouter(router).factory() != factory ||
            IV3RouteFactory(factory).getPool(source, output, fee) != pool ||
            IV3RoutePool(pool).factory() != factory || IV3RoutePool(pool).token0() != a ||
            IV3RoutePool(pool).token1() != b || IV3RoutePool(pool).fee() != fee) revert ZZZModule.InvalidConfiguration();
    }
}
