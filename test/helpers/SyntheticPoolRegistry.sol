// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZPoolRegistry} from "../../src/ZZZPoolRegistry.sol";
import {PoolKey, PoolConfig} from "../../src/libraries/ZZZTypes.sol";

/// @dev TEST ONLY. Keeps synthetic ERC20 math/route/accounting fixtures usable
/// while the production Registry admits only pinned native ETH/fixed ZZZ LP.
/// Generic ERC20 admission is deliberately absent from production. These tests
/// cannot qualify native venue admission, holder exits or Robinhood dependencies.
contract SyntheticPoolRegistry is ZZZPoolRegistry {
    constructor(address controller) ZZZPoolRegistry(controller) {}
    function configure(PoolConfig calldata config) external onlyGovernance principalOperating returns (bytes32 poolId) {
        PoolKey memory k = config.key;
        address fixedZZZ = activationAssets.zzz();
        if (fixedZZZ == address(0) || (k.currency0 != fixedZZZ && k.currency1 != fixedZZZ) ||
            k.currency0 >= k.currency1 || k.currency0.code.length == 0 || k.currency1.code.length == 0 ||
            k.hooks != address(0)) revert InvalidConfiguration();
        return _configure(config, k.currency0, k.currency1);
    }
}
