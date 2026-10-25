// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZRewards, IZZZVault, IZZZPools} from "./interfaces/IZZZ.sol";

interface ICanonicalFeeAssets { function assetCount() external view returns (uint256); function assets(uint256) external view returns (address); }
interface ICanonicalFeeCutoff {
    function creditCanonicalCutoff(uint256 id, address token, uint256 personal, uint256 shared) external payable;
}

/// @notice Allocates actual local LP fees once into 80/10/5/5 classified reserves.
/// No creator-payment inbox, bridge receiver, arbitrary funding or reserve sweep.
contract ZZZFeeController is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    uint256 public constant FEE_INTAKE_VERSION = 1;
    // Every id identifies a shared LP bucket, never an individual NFT.
    mapping(uint256 => mapping(address => uint256)) public dust;
    mapping(uint256 => mapping(address => uint256)) public compoundBalance;
    mapping(address => uint256) public buybackBalance;
    mapping(address => uint256) public accounted;
    struct CanonicalBucket {
        uint256 id; address asset; uint256 dustAmount; uint256 compoundAmount;
    }
    event FeesAllocated(uint256 indexed bucketId, address indexed token, uint256 distributed, uint256 carriedDust);
    event MembershipDustSettled(uint256 indexed bucketId, address indexed token, uint256 amount);

    constructor(address controller) ZZZModule(controller) {}
    // Unsolicited ETH remains unallocated and is separately quarantined at handoff.
    receive() external payable {}
    function _balance(address token) private view returns (uint256) {
        return token == address(0) ? address(this).balance : IERC20(token).balanceOf(address(this));
    }
    /// @dev Existing donations cannot substitute for the declared fee receipt.
    function _pull(address token, uint256 amount) private {
        if (msg.value != (token == address(0) ? amount : 0)) revert InvalidAmount();
        if (token != address(0)) ExactToken.pull(token, msg.sender, amount);
    }
    function _push(address token, address destination, uint256 amount) private {
        if (token != address(0)) { ExactToken.push(token, destination, amount); return; }
        if (amount == 0) return;
        uint256 beforeBalance = address(this).balance;
        (bool ok,) = payable(destination).call{value: amount}("");
        if (!ok || address(this).balance != beforeBalance - amount) revert InvalidState();
    }
    function _approve(address token, address spender, uint256 amount) private {
        if (token != address(0)) IERC20(token).forceApprove(spender, amount);
    }
    function canonicalState() public view returns (uint8) { return access.canonicalState(); }
    function _vault() private view returns (IZZZVault) { return IZZZVault(access.module(Ids.VAULT)); }
    function _credit(uint256 id, address token, uint256 personal, uint256 shared) private {
        address rewards = access.module(Ids.REWARDS);
        _approve(token, rewards, personal + shared);
        if (canonicalState() == 1) {
            if (!access.canonicalSettling()) revert InvalidState();
            ICanonicalFeeCutoff(rewards).creditCanonicalCutoff{value: token == address(0) ? personal + shared : 0}(id, token, personal, shared);
        } else IZZZRewards(rewards).creditPool{value: token == address(0) ? personal + shared : 0}(id, token, personal, shared);
        _approve(token, rewards, 0);
    }
    function _solvent(address token) private view {
        if (_balance(token) < accounted[token]) revert InvalidState();
    }
    /// @notice Only the bound Vault can allocate a physically received local fee.
    function allocate(uint256 id, address token, uint256 amount) external payable onlyModule(Ids.VAULT) nonReentrant canonicalAccounting {
        if (amount == 0) revert InvalidAmount();
        Position memory p = IZZZVault(msg.sender).group(id);
        if (p.status != PositionStatus.Active) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if (token != c.key.currency0 && token != c.key.currency1) revert InvalidConfiguration();
        _pull(token, amount);
        accounted[token] += amount;
        uint256 total = dust[id][token] + amount;
        // Twenty raw units allocate exactly 80/10/5/5. Smaller receipts carry
        // until another receipt or the incumbent-owner dust settlement barrier.
        uint256 units = total / 20;
        dust[id][token] = total % 20;
        if (units != 0) {
            compoundBalance[id][token] += units;
            buybackBalance[token] += units;
            accounted[token] -= units * 18;
            _credit(id, token, units * 16, units * 2);
        }
        _solvent(token);
        emit FeesAllocated(id, token, units * 20, dust[id][token]);
    }
    /// @notice Existing-owner dust settlement before entry or local pool moves.
    function flushDust(uint256 id, address token) external nonReentrant canonicalAccounting {
        IZZZVault vault = _vault();
        if (!access.isSealed() || (msg.sender != address(vault) && msg.sender != access.module(Ids.MEMBERSHIP))) revert Unauthorized();
        Position memory p = vault.group(id);
        if (p.status != PositionStatus.Outbound && p.status != PositionStatus.Active && p.status != PositionStatus.Parked) revert InvalidState();
        _flushHomeDust(id, token);
    }
    function _flushHomeDust(uint256 id, address token) private {
        uint256 remainder = dust[id][token];
        if (remainder == 0) return;
        dust[id][token] = 0;
        accounted[token] -= remainder;
        _credit(id, token, remainder, 0);
        _solvent(token);
        emit MembershipDustSettled(id, token, remainder);
    }
    function releaseCompound(uint256 id, address token)
        external nonReentrant canonicalAccounting returns (uint256 amount) {
        if (!access.moduleAuthorized(Ids.VAULT, msg.sender)) revert Unauthorized();
        amount = compoundBalance[id][token];
        compoundBalance[id][token] = 0;
        accounted[token] -= amount;
        _push(token, msg.sender, amount);
        _solvent(token);
    }
    function releaseBuyback(address token, uint256 amount) external onlyModule(Ids.BUYBACK) nonReentrant canonicalAccounting {
        if (amount == 0 || amount > buybackBalance[token]) revert InvalidAmount();
        buybackBalance[token] -= amount;
        accounted[token] -= amount;
        _push(token, msg.sender, amount);
        _solvent(token);
    }
    function canonicalModule() public view returns (address) { return access.module(Ids.FEES_CANONICAL); }
    modifier onlyCanonical() { if (msg.sender != canonicalModule()) revert Unauthorized(); _; }
    /// @notice Capture must fail inside any allocation/reserve-send callback.
    /// This barrier performs no token calls and grants no withdrawal permission.
    function canonicalBarrier() external onlyCanonical nonReentrant {
        if (canonicalState() != 1) revert InvalidState();
    }
    function canonicalFlush(uint256 id, address asset) external onlyCanonical { _flushHomeDust(id, asset); }
    function canonicalBucketRecord(uint256 id, address asset) external view returns (bytes memory) {
        return abi.encode(CanonicalBucket(id, asset, dust[id][asset], compoundBalance[id][asset]));
    }
    function canonicalWrite(uint8 kind, bytes calldata record) external onlyCanonical {
        if (canonicalState() != 2) revert InvalidState();
        if (kind == 0) {
            if (record.length != 160) revert InvalidState();
            (address asset, uint256 total, uint256 buyback,,) = abi.decode(record, (address,uint256,uint256,uint256,uint256));
            if (accounted[asset] != 0 || buybackBalance[asset] != 0 || buyback > total) revert InvalidState();
            accounted[asset] = total; buybackBalance[asset] = buyback;
        } else if (kind == 1) {
            if (record.length != 128) revert InvalidState();
            CanonicalBucket memory r = abi.decode(record, (CanonicalBucket));
            dust[r.id][r.asset] = r.dustAmount; compoundBalance[r.id][r.asset] = r.compoundAmount;
        } else revert InvalidState();
    }
    function canonicalSend(address asset, address destination, uint256 amount) external onlyCanonical nonReentrant {
        _push(asset, destination, amount);
    }
    // No principal, reward liability or fee reserve can be swept by an administrator.
}
