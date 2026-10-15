// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Route, BridgeMessage, MessageKind} from "./ZZZTypes.sol";

/// @dev Both fixed bridge boundaries enforce the same logical token vectors.
library BridgeAssets {
    error InvalidConfiguration();
    error InvalidAmount();
    function assets(Route memory r, BridgeMessage memory m, bool inbound)
        internal pure returns (address[] memory tokens, uint256[] memory amounts) {
        if (m.version != 3) revert InvalidConfiguration();
        uint256 count;
        if (m.kind == MessageKind.Principal) {
            if (r.sourceToken0 == address(0) || r.sourceToken1 == address(0) || m.amount0 + m.amount1 == 0 ||
                m.individual != 0 || m.collective != 0 || m.migrationId == bytes32(0)) revert InvalidAmount();
            count = 2;
        } else if (m.kind == MessageKind.Reward) {
            if (r.sourceToken0 == address(0) || r.sourceToken1 != address(0) || m.amount0 == 0 || m.amount1 != 0 ||
                m.individual + m.collective != m.amount0) revert InvalidAmount();
            count = 1;
        } else {
            if (r.sourceToken0 != address(0) || r.sourceToken1 != address(0) || m.amount0 != 0 || m.amount1 != 0 ||
                m.individual != 0 || m.collective != 0 || m.migrationId == bytes32(0)) revert InvalidAmount();
        }
        tokens = new address[](count);
        amounts = new uint256[](count);
        if (count > 0) { tokens[0] = inbound ? r.destinationToken0 : r.sourceToken0; amounts[0] = m.amount0; }
        if (count > 1) { tokens[1] = inbound ? r.destinationToken1 : r.sourceToken1; amounts[1] = m.amount1; }
    }
}
