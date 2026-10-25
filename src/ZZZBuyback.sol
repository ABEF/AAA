// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZFees, IZZZLiquidity, IZZZPools, IZZZOracle, IBurnable} from "./interfaces/IZZZ.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";

contract ZZZBuyback is ZZZModule, ReentrancyGuard {
    /// @notice Fixed deployment ZZZ identity; issuer migration requires exit/redeployment.
    address public immutable zzz;
    uint256 public immutable maxTradeUSD;
    /// @notice Immediate operating limit within the immutable deployment ceiling.
    /// Zero stops new buybacks without consulting an oracle or releasing reserves.
    uint256 public operatingTradeUSD;
    event BoughtAndBurned(address indexed input, uint256 inputAmount, uint256 zzzBurned);
    event OperatingTradeLimitChanged(uint256 previous, uint256 current);
    constructor(address controller, address zzzToken, uint256 maximumTradeUSD) ZZZModule(controller) {
        if (zzzToken.code.length == 0 || maximumTradeUSD == 0) revert InvalidConfiguration();
        zzz = zzzToken;
        maxTradeUSD = maximumTradeUSD;
        operatingTradeUSD = maximumTradeUSD;
    }
    receive() external payable {
        if (msg.sender != access.module(Ids.FEES)) revert Unauthorized();
    }
    /// @notice Changes execution policy only; cannot withdraw funds, change the
    /// revenue split or exceed the hard ceiling. Available during an ordinary
    /// pause, but not preparation or a canonical handoff lifecycle lock.
    function setOperatingTradeUSD(uint256 limit) external onlyGovernance operating nonReentrant {
        if (limit > maxTradeUSD) revert InvalidConfiguration();
        uint256 previous = operatingTradeUSD;
        operatingTradeUSD = limit;
        emit OperatingTradeLimitChanged(previous, limit);
    }
    function execute(address token, uint256 amount, bytes32 poolId, uint256 deadline) external onlyKeeper live operating nonReentrant {
        _deadline(deadline);
        if (amount == 0 || operatingTradeUSD == 0) revert InvalidAmount();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        // The maximum spend must hold at either admitted source price. Ordinary
        // Oracle.value is the lower mark for minimum contributions/display; it
        // can understate a trade budget. Round the upper input value upward.
        (, uint256 upper,) = oracle.priceBounds(token);
        if (Math.mulDiv(amount, upper, 10 ** oracle.tokenDecimals(token), Math.Rounding.Ceil) > operatingTradeUSD)
            revert InvalidAmount();
        uint256 beforeZZZ = IERC20(zzz).balanceOf(address(this));
        uint256 beforeInput = ExactAsset.balance(token,address(this));
        IZZZFees(access.module(Ids.FEES)).releaseBuyback(token, amount);
        if (ExactAsset.balance(token,address(this)) != beforeInput + amount) revert InvalidState();
        uint256 acquired = amount;
        if (token != zzz) {
            PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(poolId);
            bool zeroForOne = c.key.currency0 == token && c.key.currency1 == zzz;
            if (!zeroForOne && !(c.key.currency1 == token && c.key.currency0 == zzz)) revert InvalidConfiguration();
            uint256 minimum = Math.mulDiv(oracle.quote(token, zzz, amount), 10000 - c.maxSlippageBps, 10000);
            address manager = access.module(Ids.LIQUIDITY);
            ExactAsset.approve(token,manager, amount);
            acquired = IZZZLiquidity(manager).swap{value: token == address(0) ? amount : 0}(poolId, zeroForOne, amount, minimum, deadline);
            ExactAsset.approve(token,manager, 0);
            if (ExactAsset.balance(token,address(this)) != beforeInput) revert InvalidState();
        }
        if (IERC20(zzz).balanceOf(address(this)) != beforeZZZ + acquired) revert InvalidState();
        uint256 supplyBefore = IBurnable(zzz).totalSupply();
        IBurnable(zzz).burn(acquired);
        if (IBurnable(zzz).totalSupply() + acquired != supplyBefore ||
            IERC20(zzz).balanceOf(address(this)) != beforeZZZ) revert InvalidState();
        emit BoughtAndBurned(token, amount, acquired);
    }
}
