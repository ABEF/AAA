// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZCustodyValidation} from "./ZZZCustodyValidation.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZVault, IZZZPools, IZZZOracle, IZZZLiquidity, IZZZRewards} from "./interfaces/IZZZ.sol";

interface ICustodyVault is IZZZVault {
    function migrationBudget() external view returns (address);
    function consolidateHandoff(uint256, address, uint256, uint256) external;
    function acceptHandoff(uint256, bytes32, uint256, uint256, uint128, uint256) external payable;
}

interface IMaintenanceLossPolicy {
    function maintenanceLossBps() external view returns (uint16);
}

interface ICustodySourceRegistry {
    function activationAssets() external view returns (address);
}

interface ICustodySourceIdentity {
    function zzz() external view returns (address);
}

interface ICustodyBuybackIdentity {
    function zzz() external view returns (address);
}

/// @notice Governed custody handoff; recipient custody/liveness are explicitly trusted.
/// Source-chain custody only; any bridge or issuer exchange happens outside PoPL.
/// No arbitrary call, delegatecall, sweep, timeout release or remote-completion proof.
contract ZZZMigration is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    uint8 public constant CUSTODY_VERSION = 2;
    enum Status {
        None,
        Approved,
        Sent,
        Completed,
        Recovered,
        Cancelled
    }

    struct ParkingRequest {
        uint256 bucketId;
        bytes32 poolId;
        uint256 lpTokenId;
        uint256 totalShares;
        uint256 depositUSD;
        uint64 custodyEpoch;
        uint64 nonce;
        address token0;
        address token1;
        uint128 minimum0;
        uint128 minimum1;
        uint256 deadline;
        bytes32 reviewHash;
    }

    struct Request {
        uint256 bucket;
        bytes32 sourceSnapshot;
        address recipient;
        bytes32 recipientCodeHash;
        address destinationCustody;
        bytes32 destinationPool;
        address output0;
        address output1;
        uint256 minimum0;
        uint256 minimum1;
        bool rawExit;
        uint256 exitMinimum0;
        uint256 exitMinimum1;
        uint256 minimumZZZ;
        uint256 deadline;
        bytes32 reviewHash;
    }

    struct Plan {
        Request request;
        bytes32 sourcePool;
        PositionStatus sourceStatus;
        Status status;
        uint256 shares;
        address token0;
        address token1;
        uint256 startingUSD;
        uint256 minimumRetainedUSD;
        uint256 sent0;
        uint256 sent1;
        uint256 outputPrice0;
        uint256 outputPrice1;
        uint256 outputScale0;
        uint256 outputScale1;
        uint256 departureBlock;
    }
    address public currentZZZ;
    bytes32 public zzzCodeHash;
    uint256 public sequence;
    uint256 public outstandingCount;
    mapping(bytes32 => Plan) private plans;
    mapping(uint256 => bytes32) public activePlan;
    mapping(uint256 => uint64) public custodyEpoch;
    mapping(uint256 => uint64) public parkingNonce;
    event ZZZConfigured(address indexed token, bytes32 codeHash, bytes32 reviewHash);
    event DestinationBound(bytes32 indexed id, bytes32 previousRequest, bytes32 newRequest, bytes32 destinationPool);
    event CustodyApproved(
        bytes32 indexed id, uint256 indexed bucket, address indexed recipient, address destinationCustody
    );
    event CustodySent(bytes32 indexed id, uint256 indexed bucket, address indexed recipient, uint256 zzzAmount);
    event CustodyCompleted(bytes32 indexed id, uint256 indexed bucket, uint256 lpTokenId);
    event CustodyAssetsSent(
        bytes32 indexed id, address token0, uint256 amount0, address token1, uint256 amount1, bool rawExit
    );
    event CustodyRecovered(bytes32 indexed id, uint256 indexed bucket, uint256 zzzAmount);
    event CustodyCancelled(bytes32 indexed id);
    event ParkingExecuted(
        bytes32 indexed requestHash, uint256 indexed bucketId, uint64 nonce, uint256 principal0, uint256 principal1
    );
    event ParkingInvalidated(uint256 indexed bucketId, uint64 nextNonce);
    ZZZCustodyValidation public immutable validation;

    constructor(address controller) ZZZModule(controller) {
        validation = new ZZZCustodyValidation(controller);
    }

    receive() external payable {
        if (msg.sender != access.module(Ids.VAULT)) revert Unauthorized();
    }

    function _balance(address asset) private view returns (uint256) {
        return ExactAsset.balance(asset, address(this));
    }

    function _vault() private view returns (ICustodyVault) {
        return ICustodyVault(access.module(Ids.VAULT));
    }

    function _pools() private view returns (IZZZPools) {
        return IZZZPools(access.module(Ids.POOLS));
    }

    function request(bytes32 id) external view returns (Request memory) {
        return plans[id].request;
    }

    function state(bytes32 id) external view returns (Status, uint256, uint256, uint256, uint256) {
        Plan storage plan = plans[id];
        return (plan.status, plan.sent0, plan.sent1, plan.startingUSD, plan.departureBlock);
    }

    function minimumRetainedUSD(bytes32 id) external view returns (uint256) {
        return plans[id].minimumRetainedUSD;
    }

    /// Bind the deployment's fixed ZZZ target once during bootstrap, before seal.
    /// Source admission and the immutable Buyback must already share this identity.
    /// Token-contract exchanges use external custody and a fresh reviewed deployment.
    function configureZZZ(address token, bytes32 codeHash, bytes32 reviewHash) external onlyGovernance nonReentrant {
        if (
            access.isSealed() || currentZZZ != address(0) || outstandingCount != 0 || token.code.length == 0
                || token.codehash != codeHash || reviewHash == bytes32(0)
                || !IZZZRewards(access.module(Ids.REWARDS)).isAsset(token)
        ) revert InvalidConfiguration();
        address buyback = access.module(Ids.BUYBACK);
        if (
            token != ICustodySourceIdentity(ICustodySourceRegistry(address(_pools())).activationAssets()).zzz()
                || buyback.code.length == 0 || ICustodyBuybackIdentity(buyback).zzz() != token
        ) revert InvalidConfiguration();
        IZZZOracle(access.module(Ids.ORACLE)).price(token);
        currentZZZ = token;
        zzzCodeHash = codeHash;
        emit ZZZConfigured(token, codeHash, reviewHash);
    }

    function sourceSnapshot(uint256 bucket) public view returns (bytes32) {
        ICustodyVault vault = _vault();
        Position memory position = vault.group(bucket);
        (uint256 a0, uint256 a1) = _amounts(position);
        return keccak256(
            abi.encode(
                block.chainid,
                address(this),
                address(vault),
                bucket,
                position,
                vault.bucketTotalShares(bucket),
                custodyEpoch[bucket],
                currentZZZ,
                zzzCodeHash,
                a0,
                a1
            )
        );
    }

    function approve(Request calldata r) external onlyGovernance operating nonReentrant returns (bytes32 id) {
        _deadline(r.deadline);
        ICustodyVault vault = _vault();
        Position memory position = vault.group(r.bucket);
        bool custodyOnly = r.destinationPool == bytes32(0) && r.destinationCustody == r.recipient;
        validation.validateRequest(abi.encode(r));
        PoolConfig memory source = _pools().accounting(position.poolId);
        if (!r.rawExit && source.key.currency0 != currentZZZ && source.key.currency1 != currentZZZ) {
            revert InvalidConfiguration();
        }
        id = keccak256(abi.encode("ZZZ_CUSTODY_V2", block.chainid, address(access), address(this), ++sequence, r));
        Plan storage plan = plans[id];
        plan.request = r;
        plan.sourcePool = position.poolId;
        plan.sourceStatus = position.status;
        plan.status = Status.Approved;
        plan.shares = vault.bucketTotalShares(r.bucket);
        plan.token0 = source.key.currency0;
        plan.token1 = source.key.currency1;
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        (uint256 a0, uint256 a1) = _amounts(position);
        if (!r.rawExit) {
            plan.startingUSD = oracle.value(plan.token0, a0 + position.idle0)
                + oracle.value(plan.token1, a1 + position.idle1);
            plan.minimumRetainedUSD = _currentFloor(plan.startingUSD);
            if (plan.startingUSD == 0 || oracle.value(currentZZZ, r.minimumZZZ) < plan.minimumRetainedUSD) {
                revert Slippage();
            }
        }
        if (custodyOnly) {
            if (r.output0 != plan.token0 || r.output1 != plan.token1) revert InvalidConfiguration();
        } else {
            _bindDestination(plan, r);
        }
        activePlan[r.bucket] = id;
        ++outstandingCount;
        emit CustodyApproved(id, r.bucket, r.recipient, r.destinationCustody);
    }

    /// @notice One-time local return destination for an already sent holding plan.
    /// Preserve source snapshot, actual departure, mode and original loss budget.
    function bindLocalDestination(bytes32 id, bytes32 pool, uint256 minimum0, uint256 minimum1, bytes32 reviewHash)
        external
        onlyGovernance
        operating
        nonReentrant
    {
        Plan storage plan = plans[id];
        Request memory requestData = plan.request;
        if (
            plan.status != Status.Sent || requestData.destinationPool != bytes32(0) || reviewHash == bytes32(0)
                || pool == bytes32(0) || (minimum0 == 0 && minimum1 == 0)
        ) revert InvalidState();
        bytes32 previous = keccak256(abi.encode(requestData));
        PoolConfig memory target = _pools().accounting(pool);
        requestData.destinationPool = pool;
        requestData.destinationCustody = address(_vault());
        requestData.output0 = target.key.currency0;
        requestData.output1 = target.key.currency1;
        requestData.minimum0 = minimum0;
        requestData.minimum1 = minimum1;
        requestData.reviewHash = reviewHash;
        _bindDestination(plan, requestData);
        plan.request = requestData;
        emit DestinationBound(id, previous, keccak256(abi.encode(requestData)), pool);
    }

    function _bindDestination(Plan storage plan, Request memory requestData) private {
        (plan.outputPrice0, plan.outputPrice1, plan.outputScale0, plan.outputScale1) =
            validation.validateDestination(abi.encode(requestData));
    }

    /// Migration Exit: close, convert ALL attributed principal to ZZZ, then send.
    /// Pause required; any close/swap/transfer failure rolls back this complete exit.
    function exit(bytes32 id) external onlyGovernance operating nonReentrant {
        Plan storage plan = plans[id];
        Request memory requestData = plan.request;
        _deadline(requestData.deadline);
        if (
            plan.status != Status.Approved || !access.paused()
                || requestData.sourceSnapshot != sourceSnapshot(requestData.bucket)
                || requestData.recipient.codehash != requestData.recipientCodeHash
                || (!requestData.rawExit && currentZZZ.codehash != zzzCodeHash)
        ) revert InvalidState();
        ICustodyVault vault = _vault();
        uint256 balance0Before = _balance(plan.token0);
        uint256 balance1Before = _balance(plan.token1);
        plan.status = Status.Sent;
        plan.departureBlock = block.number;
        ++custodyEpoch[requestData.bucket];
        if (plan.sourceStatus == PositionStatus.Active) vault.park(requestData.bucket, requestData.deadline);
        if (!requestData.rawExit) {
            vault.consolidateHandoff(requestData.bucket, currentZZZ, requestData.minimumZZZ, requestData.deadline);
        }
        (uint256 a0, uint256 a1) = vault.releaseForMigration(requestData.bucket, id, requestData.deadline);
        if (requestData.rawExit) {
            if (a0 < requestData.exitMinimum0 || a1 < requestData.exitMinimum1) revert Slippage();
        } else if (
            (currentZZZ == plan.token0 ? a1 : a0) != 0 || (currentZZZ == plan.token0 ? a0 : a1) < requestData.minimumZZZ
        ) {
            revert Slippage();
        }
        if (_balance(plan.token0) != balance0Before + a0 || _balance(plan.token1) != balance1Before + a1) {
            revert InvalidState();
        }
        plan.sent0 = a0;
        plan.sent1 = a1;
        ExactAsset.push(plan.token0, requestData.recipient, a0);
        ExactAsset.push(plan.token1, requestData.recipient, a1);
        if (
            _balance(plan.token0) != balance0Before || _balance(plan.token1) != balance1Before
                || vault.bucketTotalShares(requestData.bucket) != plan.shares
        ) revert InvalidState();
        emit CustodySent(id, requestData.bucket, requestData.recipient, _sentZZZ(plan));
        emit CustodyAssetsSent(id, plan.token0, a0, plan.token1, a1, requestData.rawExit);
    }

    function cancel(bytes32 id) external onlyDrainGovernance nonReentrant {
        Plan storage plan = plans[id];
        if (plan.status != Status.Approved) revert InvalidState();
        plan.status = Status.Cancelled;
        _close(plan, id);
        emit CustodyCancelled(id);
    }

    /// Actual funding + LP mint + original fixed-price approved budget in one transaction.
    function completeLocal(bytes32 id, uint256 a0, uint256 a1, uint128 minimumLiquidity, uint256 deadline)
        external
        payable
        live
        operating
        nonReentrant
    {
        _deadline(deadline);
        Plan storage plan = plans[id];
        Request memory requestData = plan.request;
        if (
            plan.status != Status.Sent || requestData.destinationPool == bytes32(0) || a0 < requestData.minimum0
                || a1 < requestData.minimum1 || minimumLiquidity == 0
        ) revert InvalidState();
        PoolConfig memory target = _pools().accounting(requestData.destinationPool);
        if (target.key.currency0 != requestData.output0 || target.key.currency1 != requestData.output1) {
            revert InvalidConfiguration();
        }
        _receive(
            plan,
            requestData.destinationPool,
            requestData.output0,
            requestData.output1,
            a0,
            a1,
            minimumLiquidity,
            deadline
        );
        Position memory position = _vault().group(requestData.bucket);
        (uint256 x, uint256 y) = _amounts(position);
        if (requestData.rawExit) {
            // Raw emergency approvals carry explicit destination token minima,
            // not a fabricated USD loss guarantee when pricing/markets fail.
            if (x + position.idle0 < requestData.minimum0 || y + position.idle1 < requestData.minimum1) revert Slippage();
        } else {
            uint256 retained = Math.mulDiv(x + position.idle0, plan.outputPrice0, plan.outputScale0)
                + Math.mulDiv(y + position.idle1, plan.outputPrice1, plan.outputScale1);
            if (retained < plan.minimumRetainedUSD) revert Slippage();
        }
        if (position.status != PositionStatus.Active || _vault().bucketTotalShares(requestData.bucket) != plan.shares) {
            revert InvalidState();
        }
        plan.status = Status.Completed;
        _close(plan, id);
        emit CustodyCompleted(id, requestData.bucket, position.lpTokenId);
    }

    /// Return every actually-sent source currency; no proof or invented remote balance.
    /// Anyone may fully fund recovery, including while ordinary operations are paused.
    function recover(bytes32 id, uint256 deadline) external payable operating nonReentrant {
        _deadline(deadline);
        Plan storage plan = plans[id];
        if (plan.status != Status.Sent) revert InvalidState();
        uint256 a0 = plan.sent0;
        uint256 a1 = plan.sent1;
        _receive(plan, plan.sourcePool, plan.token0, plan.token1, a0, a1, 0, deadline);
        if (_vault().bucketTotalShares(plan.request.bucket) != plan.shares) revert InvalidState();
        plan.status = Status.Recovered;
        _close(plan, id);
        emit CustodyRecovered(id, plan.request.bucket, _sentZZZ(plan));
    }

    function _receive(
        Plan storage plan,
        bytes32 pool,
        address token0,
        address token1,
        uint256 amount0,
        uint256 amount1,
        uint128 minimumLiquidity,
        uint256 deadline
    ) private {
        ICustodyVault vault = _vault();
        if (
            vault.group(plan.request.bucket).status != PositionStatus.Outbound
                || vault.bucketTotalShares(plan.request.bucket) != plan.shares
        ) revert InvalidState();
        uint256 nativeAmount = token0 == address(0) ? amount0 : (token1 == address(0) ? amount1 : 0);
        if (msg.value != nativeAmount || token0 == token1) revert InvalidAmount();
        // This is the funding ingress. Existing ETH cannot cover missing value;
        // only this operation's declared native budget is forwarded to Vault.
        uint256 balance0Before = _balance(token0) - (token0 == address(0) ? msg.value : 0);
        uint256 balance1Before = _balance(token1) - (token1 == address(0) ? msg.value : 0);
        if (token0 != address(0)) {
            ExactToken.pull(token0, msg.sender, amount0);
            IERC20(token0).forceApprove(address(vault), amount0);
        }
        if (token1 != address(0)) {
            ExactToken.pull(token1, msg.sender, amount1);
            IERC20(token1).forceApprove(address(vault), amount1);
        }
        vault.acceptHandoff{value: nativeAmount}(
            plan.request.bucket, pool, amount0, amount1, minimumLiquidity, deadline
        );
        if (token0 != address(0)) IERC20(token0).forceApprove(address(vault), 0);
        if (token1 != address(0)) IERC20(token1).forceApprove(address(vault), 0);
        if (_balance(token0) != balance0Before || _balance(token1) != balance1Before) revert InvalidState();
    }

    function _close(Plan storage plan, bytes32 planId) private {
        if (activePlan[plan.request.bucket] != planId) revert InvalidState();
        delete activePlan[plan.request.bucket];
        --outstandingCount;
    }

    /// @dev ZZZ is fixed once before seal. Report its original sent amount from
    /// the exact source-currency quantities; no duplicate per-plan token/balance.
    function _sentZZZ(Plan storage plan) private view returns (uint256) {
        address token = currentZZZ;
        return token == address(0) ? 0 : (token == plan.token0 ? plan.sent0 : (token == plan.token1 ? plan.sent1 : 0));
    }

    function _currentFloor(uint256 value) private view returns (uint256) {
        uint16 limit = IMaintenanceLossPolicy(_vault().migrationBudget()).maintenanceLossBps();
        if (limit > 1000) revert InvalidConfiguration();
        return value - Math.mulDiv(value, limit, 10000);
    }

    function _amounts(Position memory position) private view returns (uint256, uint256) {
        if (position.lpTokenId == 0) return (0, 0);
        return IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(position.lpTokenId);
    }

    /// @notice Atomic pool-to-pool move. Never transfers principal to an external custodian.
    /// Only identical actual currencies are accepted; native ETH and WETH are distinct.
    /// One captured governed loss budget, unchanged NFT shares, actual destination LP.
    function moveFunds(uint256 id, bytes32 pool, uint128 minimum, uint256 deadline)
        public
        onlyGovernance
        live
        nonReentrant
    {
        if (activePlan[id] != bytes32(0)) revert InvalidState();
        _vault().movePool(id, pool, minimum, deadline);
    }

    function resume(uint256 id, bytes32 pool, uint128 minimum, uint256 deadline)
        external
        onlyGovernance
        live
        nonReentrant
    {
        if (activePlan[id] != bytes32(0)) revert InvalidState();
        _vault().resume(id, pool, minimum, deadline);
    }

    function park(ParkingRequest calldata r) external onlyDrainGovernance nonReentrant {
        _deadline(r.deadline);
        ICustodyVault vault = _vault();
        Position memory position = vault.group(r.bucketId);
        validation.validateParking(abi.encode(r));
        ++parkingNonce[r.bucketId];
        vault.park(r.bucketId, r.deadline);
        Position memory afterPosition = vault.group(r.bucketId);
        uint256 a0 = afterPosition.idle0 - position.idle0;
        uint256 a1 = afterPosition.idle1 - position.idle1;
        if (
            afterPosition.status != PositionStatus.Parked || afterPosition.lpTokenId != 0 || a0 < r.minimum0
                || a1 < r.minimum1
        ) revert Slippage();
        emit ParkingExecuted(
            keccak256(abi.encode(block.chainid, address(this), address(vault), r)), r.bucketId, r.nonce, a0, a1
        );
    }

    function invalidateParking(uint256 id) external onlyDrainGovernance {
        ++parkingNonce[id];
        emit ParkingInvalidated(id, parkingNonce[id]);
    }
}
