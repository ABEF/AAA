// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZVault} from "../../src/ZZZVault.sol";
import {ExactToken} from "../../src/libraries/ExactToken.sol";
import {ExactAsset} from "../../src/libraries/ExactAsset.sol";
import {ProtocolPolicyFixture} from "./ProtocolPolicyFixture.sol";

/// @notice TEST ONLY. Preserves the historical two-ERC20 unit transport for
/// isolated share/reward/callback/rounding models. It is never the deployable
/// native-only Vault and does not qualify ETH ingress, real LP or providers.
/// All share, fee, custody, checkpoint and lifecycle bodies remain inherited.
contract AccountingVaultHarness is ZZZVault {
    constructor(address controller,uint256 chain,address payable recipient,address budget)
        ZZZVault(controller,chain,budget) { ProtocolPolicyFixture.recipient(controller,recipient); }

    function _receiveAssets(address token0,address token1,uint256 amount0,uint256 amount1)
        internal override {
        if (msg.value != 0) revert InvalidAmount();
        ExactToken.pull(token0,msg.sender,amount0);
        ExactToken.pull(token1,msg.sender,amount1);
    }

    function _approvePrincipalAssets(address token0,address token1,address spender,uint256 amount0,uint256 amount1)
        internal override {
        ExactAsset.approve(token0,spender,amount0);
        ExactAsset.approve(token1,spender,amount1);
    }
}
