// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZCanonicalHandoff} from "../../src/ZZZCanonicalHandoff.sol";
import {ZZZNFTCanonical} from "../../src/ZZZNFTCanonical.sol";
import {ZZZVaultCanonical} from "../../src/ZZZVaultCanonical.sol";
import {ZZZFeesCanonical} from "../../src/ZZZFeesCanonical.sol";
import {IZZZAccess, IZZZVault} from "../../src/interfaces/IZZZ.sol";
import {Ids} from "../../src/libraries/ZZZTypes.sol";

interface ICanonicalFixtureBinder {
    function bind(bytes32 id, address implementation) external;
}

/// @dev TEST ONLY: complete the same immutable companion bindings required by
/// production sealing. The caller remains the controller's existing bootstrap.
/// Deliberately partial unit fixtures using MockAccess do not use this helper.
library CanonicalFixture {
    function bind(address controller) internal {
        IZZZAccess access = IZZZAccess(controller);
        ICanonicalFixtureBinder binder = ICanonicalFixtureBinder(controller);
        if (access.module(Ids.CANONICAL) == address(0)) {
            binder.bind(Ids.CANONICAL, address(new ZZZCanonicalHandoff(controller)));
        }
        if (access.module(Ids.NFT_CANONICAL) == address(0)) {
            binder.bind(Ids.NFT_CANONICAL, address(new ZZZNFTCanonical(controller, access.module(Ids.NFT))));
        }
        if (access.module(Ids.VAULT_CANONICAL) == address(0)) {
            address vault = access.module(Ids.VAULT);
            binder.bind(Ids.VAULT_CANONICAL, address(new ZZZVaultCanonical(controller, vault,
                IZZZVault(vault).canonicalChainId())));
        }
        if (access.module(Ids.FEES_CANONICAL) == address(0)) {
            binder.bind(Ids.FEES_CANONICAL, address(new ZZZFeesCanonical(controller, access.module(Ids.FEES))));
        }
    }
}
