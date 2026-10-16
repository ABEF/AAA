// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {Ids, Position, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZOracle, IZZZLiquidity} from "./interfaces/IZZZ.sol";

/// @notice Fixed execution budget for atomic, same-ordered-pair custody moves.
/// Created by its only caller, Vault. No token custody, configuration or executor.
contract ZZZMigrationBudget {
    address public immutable vault;
    IZZZAccess public immutable access;
    struct Snapshot {
        uint256 bucketId;
        uint256 value;
        uint256 price0;
        uint256 price1;
        uint256 scale0;
        uint256 scale1;
        uint256 idle0;
        uint256 idle1;
    }
    Snapshot private snapshot;
    bool private compoundIncluded;
    error Unauthorized();
    error InvalidState();
    error Slippage();
    event MigrationValueChecked(uint256 indexed bucketId, uint256 beforeUSD, uint256 deployedUSD, uint256 idleUSD);

    constructor(address controller) {
        vault = msg.sender;
        access = IZZZAccess(controller);
    }
    modifier onlyVault() {
        if (msg.sender != vault) revert Unauthorized();
        _;
    }
    /// @dev Called before fee settlement, token callbacks or closing the old LP.
    /// Only attributed assets enter the starting denominator.
    function checkpoint(uint256 id, uint8 phase) external onlyVault {
        if (phase == 0) _beforeMove(id);
        else if (phase == 1) _includeCompound(id);
        else if (phase == 2) _afterMove(id);
        else revert InvalidState();
    }
    function _beforeMove(uint256 id) private {
        if (snapshot.value != 0) revert InvalidState();
        Position memory p = IZZZVault(vault).group(id);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        Snapshot memory s;
        s.bucketId = id;
        // Price validates feed/sequencer freshness. Reuse this exact vector after
        // close, swap and mint; callbacks cannot reprice away execution loss.
        s.price0 = oracle.price(c.key.currency0);
        s.price1 = oracle.price(c.key.currency1);
        s.scale0 = 10 ** oracle.tokenDecimals(c.key.currency0);
        s.scale1 = 10 ** oracle.tokenDecimals(c.key.currency1);
        s.idle0 = p.idle0;
        s.idle1 = p.idle1;
        (uint256 deployed, uint256 idle) = _values(p, s);
        s.value = deployed + idle;
        if (s.value == 0) revert InvalidState();
        snapshot = s;
    }
    /// @dev Between checkpoints the guarded Vault only harvests and releases
    /// compound; harvest does not modify attributed idle. Its exact idle increase
    /// is therefore the designated compound, never donated/raw token balances.
    function _includeCompound(uint256 id) private {
        Snapshot memory s = snapshot;
        if (s.value == 0 || s.bucketId != id || compoundIncluded) revert InvalidState();
        Position memory p = IZZZVault(vault).group(id);
        snapshot.value = s.value + _value(p.idle0 - s.idle0, p.idle1 - s.idle1, s);
        compoundIncluded = true;
    }
    function _afterMove(uint256 id) private {
        Snapshot memory s = snapshot;
        if (s.value == 0 || s.bucketId != id || !compoundIncluded) revert InvalidState();
        (uint256 deployed, uint256 idle) = _values(IZZZVault(vault).group(id), s);
        uint256 retained = deployed + idle;
        // ceil(97%): rounding never permits more than 3% aggregate loss. Gas is
        // outside these custody ledgers. Keep the existing 5% idle ceiling under
        // this same vector, including when an admitted feed changes mid-call.
        if (retained < s.value - Math.mulDiv(s.value, 300, 10000) || deployed == 0 ||
            idle > Math.mulDiv(retained, 500, 10000)) revert Slippage();
        delete snapshot;
        delete compoundIncluded;
        emit MigrationValueChecked(id, s.value, deployed, idle);
    }
    function _values(Position memory p, Snapshot memory s) private view returns (uint256 deployed, uint256 idle) {
        if (p.lpTokenId != 0) {
            (uint256 amount0, uint256 amount1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(p.lpTokenId);
            deployed = _value(amount0, amount1, s);
        }
        idle = _value(p.idle0, p.idle1, s);
    }
    function _value(uint256 amount0, uint256 amount1, Snapshot memory s) private pure returns (uint256) {
        return Math.mulDiv(amount0, s.price0, s.scale0) + Math.mulDiv(amount1, s.price1, s.scale1);
    }
    /// @dev Shared current valuation keeps Vault within the standard code limit;
    /// migration checkpoints above deliberately use their cached price vector.
    function valuePair(address token0, address token1, uint256 amount0, uint256 amount1) external view returns (uint256) {
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        return oracle.value(token0, amount0) + oracle.value(token1, amount1);
    }
}
