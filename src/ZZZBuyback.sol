// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZFees, IZZZLiquidity, IZZZPools, IZZZOracle, IBurnable} from "./interfaces/IZZZ.sol";

contract ZZZBuyback is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    address public immutable zzz;
    uint256 public immutable maxTradeUSD;
    event BoughtAndBurned(address indexed input, uint256 inputAmount, uint256 zzzBurned);
    constructor(address controller, address zzzToken, uint256 maximumTradeUSD) ZZZModule(controller) {
        if (zzzToken.code.length == 0 || maximumTradeUSD == 0) revert InvalidConfiguration();
        zzz = zzzToken;
        maxTradeUSD = maximumTradeUSD;
    }
    function execute(address token, uint256 amount, bytes32 poolId, uint256 deadline) external onlyKeeper live nonReentrant {
        _deadline(deadline);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        if (amount == 0 || oracle.value(token, amount) > maxTradeUSD) revert InvalidAmount();
        uint256 beforeZZZ = IERC20(zzz).balanceOf(address(this));
        IZZZFees(access.module(Ids.FEES)).releaseBuyback(token, amount);
        uint256 acquired = amount;
        if (token != zzz) {
            PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(poolId);
            bool zeroForOne = c.key.currency0 == token && c.key.currency1 == zzz;
            if (!zeroForOne && !(c.key.currency1 == token && c.key.currency0 == zzz)) revert InvalidConfiguration();
            uint256 minimum = Math.mulDiv(oracle.quote(token, zzz, amount), 10000 - c.maxSlippageBps, 10000);
            address manager = access.module(Ids.LIQUIDITY);
            IERC20(token).forceApprove(manager, amount);
            acquired = IZZZLiquidity(manager).swap(poolId, zeroForOne, amount, minimum, deadline);
            IERC20(token).forceApprove(manager, 0);
        }
        if (IERC20(zzz).balanceOf(address(this)) != beforeZZZ + acquired) revert InvalidState();
        uint256 supplyBefore = IBurnable(zzz).totalSupply();
        IBurnable(zzz).burn(acquired);
        if (IBurnable(zzz).totalSupply() + acquired != supplyBefore ||
            IERC20(zzz).balanceOf(address(this)) != beforeZZZ) revert InvalidState();
        emit BoughtAndBurned(token, amount, acquired);
    }
}
