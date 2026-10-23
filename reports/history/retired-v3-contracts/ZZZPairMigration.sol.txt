// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig, BridgeMessage, Route} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZVault, IZZZFees, IZZZPools, IZZZOracle, IZZZLiquidity, IZZZMigration, IZZZRewards} from "./interfaces/IZZZ.sol";

interface IPairVault is IZZZVault { function migrationBudget() external view returns (IPairBudget); }
interface IPairBudget {
    function beginPair() external;
    function compositionEpoch(uint256) external view returns (uint64);
}
interface IPairMigration { function executePair(uint256 id, bytes32 pool, uint128 minimum, uint256 deadline) external; }
interface IPairParkingState {
    function parkingNonce(uint256) external view returns(uint64);
    function custodyEpoch(uint256) external view returns(uint64);
}
interface IPairAssets {
    function assetCount() external view returns (uint256);
    function assets(uint256) external view returns (address);
}

/// @notice Immutable, typed local conversion companion created by Migration.
/// No arbitrary router/calldata/recipient, rescue, delegatecall or standing approval.
/// Custody exists only inside the Vault's atomic close/convert/redeploy operation.
contract ZZZPairMigration is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    address public immutable migration;
    struct Step { bytes32 pool; bool zeroForOne; uint128 amountIn; uint128 minimumOut; }
    struct Parking {
        uint256 bucketId; bytes32 poolId; uint256 lpTokenId; uint256 totalShares; uint256 depositUSD;
        uint64 custodyEpoch; uint64 nonce; address token0; address token1;
        uint128 minimum0; uint128 minimum1; uint256 deadline; bytes32 reviewHash;
    }
    struct Request {
        uint256 bucket; bytes32 sourcePool; uint256 sourceLP; uint256 totalShares;
        uint64 epoch; bytes32 destinationPool; uint128 minimumLiquidity;
        uint256 deadline; bytes32 reviewHash; Step[] steps;
    }
    struct Asset { address token; uint256 price; uint256 scale; uint256 baseline; uint256 amount; }
    Asset[] private assets;
    Request private request;
    uint256 private startingValue;
    uint256 private oldIdle0;
    uint256 private oldIdle1;
    bool private compoundIncluded;
    bool private converted;
    bool public takingReserves;
    uint256 public activeBucket;
    bytes32 public activeRequest;
    event PairMigrated(bytes32 indexed requestHash, uint256 indexed bucket, uint64 epoch,
        bytes32 sourcePool, bytes32 destinationPool, uint256 beforeUSD, uint256 deployedUSD, uint256 idleUSD);

    constructor(address controller) ZZZModule(controller) { migration = msg.sender; }
    /// @dev Exact original parking checks, without consulting prices or inboxes.
    function validateParking(bytes calldata encoded) external view {
        Parking memory r = abi.decode(encoded,(Parking));
        IZZZVault v = IZZZVault(access.module(Ids.VAULT)); Position memory p = v.group(r.bucketId);
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(r.poolId);
        IPairParkingState state = IPairParkingState(migration);
        if (!access.isSealed() || !access.paused() || r.reviewHash == bytes32(0) ||
            (r.minimum0 == 0 && r.minimum1 == 0) || r.lpTokenId == 0 ||
            IZZZMigration(migration).activePlan(r.bucketId) != bytes32(0) || r.nonce != state.parkingNonce(r.bucketId) ||
            r.custodyEpoch != state.custodyEpoch(r.bucketId) || p.status != PositionStatus.Active || p.poolId != r.poolId ||
            p.lpTokenId != r.lpTokenId || p.depositUSD != r.depositUSD || p.locationChain != block.chainid ||
            p.locationVault != address(v) || r.totalShares == 0 || v.bucketTotalShares(r.bucketId) != r.totalShares ||
            c.key.currency0 != r.token0 || c.key.currency1 != r.token1) revert InvalidState();
    }
    /// @dev Pure V3 message validation extraction; no legacy identity semantics change.
    function validateBridgeIdentity(BridgeMessage calldata m, Route calldata r) external pure {
        if (m.version != 3 || m.totalShares == 0 || m.homePoolId == bytes32(0) ||
            m.bucketId != uint256(keccak256(abi.encode(m.homeChain,m.homeVault,m.homePoolId))) || m.migrationId == bytes32(0) ||
            m.migrationEpoch == 0 || m.depositUSD == 0 || m.homeChain == 0 || m.homeVault == address(0) ||
            m.homeReceiver == address(0) || m.canonicalToken0 == address(0) || m.canonicalToken1 == address(0) ||
            m.canonicalToken0 == m.canonicalToken1 || r.sourceToken0 == address(0) || r.sourceToken1 == address(0) ||
            m.previousChain != r.sourceChain || m.previousVault != r.sourceVault || m.previousReceiver != r.sourceReceiver) revert InvalidConfiguration();
    }
    modifier onlyBudget() {
        if (msg.sender != address(IPairVault(access.module(Ids.VAULT)).migrationBudget())) revert Unauthorized();
        _;
    }
    function execute(Request calldata r) external onlyGovernance live operating nonReentrant {
        _deadline(r.deadline);
        IPairVault v = IPairVault(access.module(Ids.VAULT));
        Position memory p = v.group(r.bucket);
        if (r.bucket == 0 || r.reviewHash == bytes32(0) || r.minimumLiquidity == 0 || r.steps.length > 8 ||
            r.sourcePool != p.poolId || r.sourceLP != p.lpTokenId ||
            r.totalShares == 0 || r.totalShares != v.bucketTotalShares(r.bucket) ||
            r.epoch != v.migrationBudget().compositionEpoch(r.bucket) ||
            p.homeChain != block.chainid || p.homeVault != address(v) ||
            p.locationChain != block.chainid || p.locationVault != address(v) ||
            (p.status != PositionStatus.Active && p.status != PositionStatus.Parked) ||
            IZZZMigration(migration).activePlan(r.bucket) != bytes32(0) ||
            !IZZZFees(access.module(Ids.FEES)).remoteSettled(r.bucket)) revert InvalidState();
        PoolConfig memory target = IZZZPools(access.module(Ids.POOLS)).accounting(r.destinationPool);
        if (!target.operationsEnabled) revert InvalidConfiguration();
        activeBucket = r.bucket;
        activeRequest = keccak256(abi.encode(block.chainid, address(this), address(v), r));
        request = r;
        v.migrationBudget().beginPair();
        IPairMigration(migration).executePair(r.bucket, r.destinationPool, r.minimumLiquidity, r.deadline);
        if (!converted || startingValue != 0) revert InvalidState();
        delete request; delete assets;
        delete activeBucket; delete activeRequest; delete converted; delete compoundIncluded;
    }
    function validateMove(uint256 id, bytes32 pool, uint128 minimum) external view onlyBudget {
        if (activeRequest == bytes32(0) || id != activeBucket || pool != request.destinationPool ||
            minimum != request.minimumLiquidity) revert InvalidState();
    }
    function checkpoint(uint256 id, uint8 phase) external onlyBudget {
        if (activeRequest == bytes32(0) || id != activeBucket) revert InvalidState();
        IPairVault v = IPairVault(access.module(Ids.VAULT));
        Position memory p = v.group(id);
        if (phase == 0) {
            if (assets.length != 0 || p.poolId != request.sourcePool || p.lpTokenId != request.sourceLP ||
                v.bucketTotalShares(id) != request.totalShares) revert InvalidState();
            _addPool(p.poolId); _addPool(request.destinationPool);
            IPairAssets admitted = IPairAssets(access.module(Ids.REWARDS));
            if (admitted.assetCount() > 32) revert InvalidState();
            // Unselected historical reserves stay in Fees, outside BOTH sides
            // of this move's budget. A failed unrelated token cannot trap LP.
            for (uint256 i; i < request.steps.length; ++i) {
                if (request.steps[i].amountIn == 0 || request.steps[i].minimumOut == 0) revert InvalidAmount();
                PoolConfig memory route = IZZZPools(access.module(Ids.POOLS)).accounting(request.steps[i].pool);
                if (!route.operationsEnabled) revert InvalidConfiguration();
                _add(route.key.currency0); _add(route.key.currency1);
            }
            (address t0, address t1) = _tokens(p.poolId);
            uint256 a0; uint256 a1;
            if (p.lpTokenId != 0) (a0,a1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(p.lpTokenId);
            startingValue = _value(t0, a0 + p.idle0) + _value(t1, a1 + p.idle1);
            if (startingValue == 0) revert InvalidState();
            oldIdle0 = p.idle0; oldIdle1 = p.idle1;
        } else if (phase == 1) {
            if (startingValue == 0 || compoundIncluded) revert InvalidState();
            (address t0, address t1) = _tokens(p.poolId);
            startingValue += _value(t0, p.idle0 - oldIdle0) + _value(t1, p.idle1 - oldIdle1);
            compoundIncluded = true;
        } else if (phase == 2) {
            if (!converted || !compoundIncluded || p.poolId != request.destinationPool || p.lpTokenId == 0 ||
                v.bucketTotalShares(id) != request.totalShares) revert InvalidState();
            (address t0, address t1) = _tokens(p.poolId);
            (uint256 a0,uint256 a1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(p.lpTokenId);
            uint256 deployed = _value(t0,a0) + _value(t1,a1);
            uint256 idle = _value(t0,p.idle0) + _value(t1,p.idle1);
            if (deployed == 0 || deployed + idle < startingValue - Math.mulDiv(startingValue,300,10000) ||
                idle > Math.mulDiv(deployed + idle,500,10000)) revert Slippage();
            for (uint256 i; i < assets.length; ++i) {
                if (IERC20(assets[i].token).balanceOf(address(this)) != assets[i].baseline) revert InvalidState();
            }
            emit PairMigrated(activeRequest,id,request.epoch + 1,request.sourcePool,p.poolId,startingValue,deployed,idle);
            delete startingValue;
        } else revert InvalidState();
    }
    /// @dev Only Vault calls this while its move is nonReentrant. Inputs have
    /// just been transferred with exact deltas, after removing their old idle classification.
    function convert(uint256 id, uint256 amount0, uint256 amount1) external returns (uint256 out0, uint256 out1) {
        if (msg.sender != access.module(Ids.VAULT_CANONICAL) || id != activeBucket || !compoundIncluded || converted) revert Unauthorized();
        (address old0, address old1) = _tokens(request.sourcePool);
        assets[_index(old0)].amount += amount0; assets[_index(old1)].amount += amount1;
        IPairAssets admitted = IPairAssets(access.module(Ids.REWARDS));
        takingReserves = true;
        for (uint256 i; i < admitted.assetCount(); ++i) {
            address token = admitted.assets(i);
            uint256 amount = IZZZFees(access.module(Ids.FEES)).compoundBalance(id, token);
            if (amount == 0) continue;
            uint256 slot = _find(token);
            if (slot == assets.length) continue; // Retain this currency's exact reserve in Fees.
            uint256 received = IZZZFees(access.module(Ids.FEES)).releaseCompound(id, token);
            if (received != amount) revert InvalidState();
            assets[slot].amount += amount;
            startingValue += _value(token,amount);
        }
        takingReserves = false;
        _solvent();
        address manager = access.module(Ids.LIQUIDITY);
        for (uint256 i; i < request.steps.length; ++i) {
            Step memory s = request.steps[i];
            (address t0,address t1) = _tokens(s.pool);
            uint256 input = _index(s.zeroForOne ? t0 : t1);
            uint256 output = _index(s.zeroForOne ? t1 : t0);
            if (s.amountIn > assets[input].amount) revert InvalidAmount();
            IERC20(assets[input].token).forceApprove(manager,s.amountIn);
            uint256 received = IZZZLiquidity(manager).swap(s.pool,s.zeroForOne,s.amountIn,s.minimumOut,request.deadline);
            IERC20(assets[input].token).forceApprove(manager,0);
            if (received < s.minimumOut) revert Slippage();
            assets[input].amount -= s.amountIn; assets[output].amount += received;
            _solvent();
        }
        (address new0,address new1) = _tokens(request.destinationPool);
        out0 = assets[_index(new0)].amount; out1 = assets[_index(new1)].amount;
        for (uint256 i; i < assets.length; ++i) {
            Asset storage a = assets[i];
            if (a.token != new0 && a.token != new1 && a.amount != 0) revert InvalidState();
        }
        address vault = access.module(Ids.VAULT);
        ExactToken.push(new0,vault,out0); ExactToken.push(new1,vault,out1);
        converted = true;
    }
    function _solvent() private view {
        for (uint256 i; i < assets.length; ++i) {
            if (IERC20(assets[i].token).balanceOf(address(this)) != assets[i].baseline + assets[i].amount) revert InvalidState();
        }
    }
    function _addPool(bytes32 pool) private { (address a,address b) = _tokens(pool); _add(a); _add(b); }
    function _tokens(bytes32 pool) private view returns (address,address) {
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(pool);
        return (c.key.currency0,c.key.currency1);
    }
    function _add(address token) private {
        for (uint256 i; i < assets.length; ++i) if (assets[i].token == token) return;
        if (token == address(0) || assets.length == 32 || !IZZZRewards(access.module(Ids.REWARDS)).isAsset(token)) revert InvalidConfiguration();
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        assets.push(Asset(token,oracle.price(token),10 ** oracle.tokenDecimals(token),IERC20(token).balanceOf(address(this)),0));
    }
    function _index(address token) private view returns (uint256) {
        uint256 slot = _find(token);
        if (slot != assets.length) return slot;
        revert InvalidConfiguration();
    }
    function _find(address token) private view returns (uint256) {
        for (uint256 i; i < assets.length; ++i) if (assets[i].token == token) return i;
        return assets.length;
    }
    function _value(address token,uint256 amount) private view returns (uint256) {
        Asset storage a = assets[_index(token)];
        return Math.mulDiv(amount,a.price,a.scale);
    }
}
