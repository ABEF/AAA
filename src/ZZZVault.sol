// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZMigrationBudget} from "./ZZZMigrationBudget.sol";
import {ZZZVaultCanonical} from "./ZZZVaultCanonical.sol";
import {IZZZEmergencyLiquidity} from "./interfaces/IZZZEmergency.sol";
import {Ids, Position, PositionStatus} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {
    IZZZNFT,
    IZZZMembership,
    IZZZFees,
    IZZZPools,
    IZZZLiquidity,
    IPositionManagerMinimal,
    IZZZRewards,
    IZZZActivationEntry
} from "./interfaces/IZZZ.sol";
interface IVaultPositionOperator { function positionOperator() external view returns(address); }
interface IVaultResidualLiquidity { function closeSecondary(bytes32,uint256,uint256) external; }

/// @notice Non-upgradeable custody. No holder redemption during operation.
/// Governance may irreversibly settle actual principal to NFT holders.
/// Deposits, idle assets, compound reserves and earned fees are separate ledgers.
contract ZZZVault is ZZZModule, ReentrancyGuard, IERC721Receiver {
    mapping(uint256 => Position) private positions; // Custody is keyed by stable bucket, never NFT.
    mapping(uint256 => bool) private minted;
    mapping(uint256 => uint256) public nftBucket;
    mapping(uint256 => uint256) public sharesOf;
    mapping(uint256 => uint256) public contributionUSD;
    mapping(uint256 => uint256) public bucketTotalShares;
    mapping(uint256 => bytes32) public homePoolId;
    mapping(bytes32 => uint256) public poolBucket;
    uint256[] private buckets;
    mapping(uint256 => bool) private registeredBucket;
    // Bounds historical custody and collective fee-dust settlement work.
    // Existing-bucket returns and pool migrations reuse their historical slot.
    uint256 public constant MAX_BUCKETS = 4;
    event PoolReserved(bytes32 indexed poolId, uint256 indexed bucketId);
    event SharesAdded(uint256 indexed nftId, uint256 indexed bucketId, uint256 shares, uint256 netUSD);
    mapping(address => uint256) public totalIdle;
    uint256 private nativeReceived;
    uint256 public sequence;
    uint256 public immutable canonicalChainId;
    ZZZMigrationBudget public immutable migrationBudget;
    uint256 public constant ACCOUNTING_VERSION = 6;
    uint256 public constant RESIDUAL_EXIT_VERSION = 1;
    event DormantMinted(uint256 indexed nftId, address indexed owner, uint256 mintPrice);
    event Activated(
        uint256 indexed nftId, address indexed owner, bytes32 indexed poolId, uint256 amount0, uint256 amount1
    );
    event LiquidityAdded(uint256 indexed nftId, uint256 amount0, uint256 amount1);
    event FeesCollected(uint256 indexed bucketId, uint256 amount0, uint256 amount1);
    event Rebalanced(uint256 indexed bucketId, uint256 oldLpTokenId, uint256 newLpTokenId, uint160 centerX96);
    event Compounded(uint256 indexed bucketId, uint256 amount0, uint256 amount1);
    event PrincipalReturnedToHolders(uint256 indexed bucketId, uint256 amountETH, uint256 amountZZZ);
    event PrincipalParked(uint256 indexed bucketId, uint256 oldLpTokenId);

    constructor(address controller, uint256 nftHomeChain, address budget)
        ZZZModule(controller) {
        if (nftHomeChain == 0 || access.protocolPolicy().code.length == 0) {
            revert InvalidConfiguration();
        }
        if (budget.code.length == 0 || address(ZZZMigrationBudget(budget).access()) != controller ||
            ZZZMigrationBudget(budget).IDLE_COMPOUNDING_VERSION() != 4) revert InvalidConfiguration();
        canonicalChainId = nftHomeChain;
        migrationBudget = ZZZMigrationBudget(budget);
    }

    receive() external payable {
        if (migrationBudget.validateNativeSender(msg.sender)) nativeReceived += msg.value;
    }

    /// @notice NFT lifecycle is separate from shared physical LP custody.
    function nftStatus(uint256 id) external view returns (PositionStatus) {
        if (!minted[id]) return PositionStatus.None;
        uint256 bucket = nftBucket[id];
        return bucket == 0 ? PositionStatus.Dormant : positions[bucket].status;
    }

    function group(uint256 bucket) external view returns (Position memory) {
        return positions[bucket];
    }

    function bucketCount() external view returns (uint256) {
        return buckets.length;
    }

    function bucketAt(uint256 index) external view returns (uint256) {
        return buckets[index];
    }

    function canonicalModule() public view returns (ZZZVaultCanonical) {
        return ZZZVaultCanonical(payable(access.module(Ids.VAULT_CANONICAL)));
    }

    /// @dev Reservations and historical custody share permanent slots. Reusing a
    /// bucket (including through another pool alias) never consumes another slot.
    function _registerBucket(uint256 bucketId) private {
        if (registeredBucket[bucketId]) return;
        if (buckets.length == MAX_BUCKETS) revert InvalidState();
        registeredBucket[bucketId] = true;
        buckets.push(bucketId);
    }

    /// @notice Permanently reserve capacity before approving a route. Pool
    /// reservations cannot be reassigned or released on cancellation/timeout.
    function reservePool(bytes32 pool, uint256 bucket) external onlyGovernance principalOperating {
        _reserve(pool, bucket);
    }

    function _reserve(bytes32 pool, uint256 bucketId) private {
        migrationBudget.validateReservation(pool, bucketId);
        _registerBucket(bucketId);
        poolBucket[pool] = bucketId;
        canonicalModule().registerAlias(pool, bucketId);
        emit PoolReserved(pool, bucketId);
    }

    function _tokens(uint256 bucketId) private view returns (address token0, address token1) {
        return migrationBudget.poolTokens(positions[bucketId].poolId);
    }

    function _nft() private view returns (IZZZNFT) {
        return IZZZNFT(access.module(Ids.NFT));
    }

    function _requireOwner(uint256 nftId, bool activation) private view {
        address entry = migrationBudget.validateOwner(nftId, msg.sender, minted[nftId], activation);
        if (entry != address(0)) IZZZActivationEntry(entry).validateOwner(nftId, keccak256(msg.data));
    }

    function _active(uint256 bucketId) private view {
        if (positions[bucketId].status != PositionStatus.Active) revert InvalidState();
    }

    function _tokenBalance(address token) private view returns (uint256) {
        return ExactAsset.balance(token, address(this));
    }

    function _receiveAssets(address token0, address token1, uint256 amount0, uint256 amount1) internal virtual {
        // Every admitted current pool is native ETH/fixed ZZZ. Historical
        // wrapped/foreign-pair deployments retain their own source profile.
        if (token0 != address(0) || msg.value != amount0) revert InvalidAmount();
        ExactToken.pull(token1, msg.sender, amount1);
    }

    /// @dev Production always admits native ETH in slot zero. This typed
    /// internal seam permits isolated accounting fixtures to substitute transport;
    /// it creates no public extension, upgrade or configurable approval target.
    function _approvePrincipalAssets(address token0,address token1,address spender,uint256,uint256 amount1)
        internal virtual {
        if (token0 != address(0)) revert InvalidConfiguration();
        ExactAsset.approve(token1,spender,amount1);
    }

    function _idle(uint256 bucketId, uint256 new0, uint256 new1) private {
        Position storage p = positions[bucketId];
        (address token0, address token1) = _tokens(bucketId);
        totalIdle[token0] = totalIdle[token0] - p.idle0 + new0;
        totalIdle[token1] = totalIdle[token1] - p.idle1 + new1;
        p.idle0 = new0;
        p.idle1 = new1;
        migrationBudget.assertIdle(bucketId);
    }

    function _valueBucket(uint256 bucketId, uint256 amount0, uint256 amount1) private view returns (uint256) {
        return migrationBudget.valueBucket(bucketId, amount0, amount1);
    }
    function _approveLP(IPositionManagerMinimal positionManager,address manager,uint256 id) private {
        positionManager.approve(manager,id);
    }

    function _put(uint256 bucketId, bool create, uint128 minimumLiquidity, uint256 deadline,
        uint256 a0, uint256 a1) private {
        ZZZMigrationBudget budget = migrationBudget;
        Position storage p = positions[bucketId];
        (address token0, address token1) = _tokens(bucketId);
        IZZZLiquidity manager = IZZZLiquidity(_moduleLiquidity());
        address operator = IVaultPositionOperator(address(manager)).positionOperator();
        // A contribution can deploy only its own post-swap amounts. Incumbent
        // idle and released compound remain attributed for guarded maintenance.
        if (a0 > p.idle0 || a1 > p.idle1) revert InvalidAmount();
        uint256 before0 = _tokenBalance(token0);
        uint256 before1 = _tokenBalance(token1);
        _approvePrincipalAssets(token0,token1,operator,a0,a1);
        uint256 nativeValue = token0 == address(0) ? a0 : 0;
        uint256 spent0;
        uint256 spent1;
        if (create) {
            (int24 lower, int24 upper, uint160 ref) = budget.mintTarget(bucketId);
            (p.lpTokenId, spent0, spent1) =
                manager.mint{value: nativeValue}(p.poolId, lower, upper, a0, a1, minimumLiquidity, deadline);
            IPositionManagerMinimal positionManager = IPositionManagerMinimal(manager.positionManager());
            _approveLP(positionManager,operator,p.lpTokenId);
            uint256 secondary = manager.secondaryId(p.lpTokenId);
            if (secondary != 0) _approveLP(positionManager,operator,secondary);
            p.centerX96 = ref;
            p.lastRebalance = uint64(block.timestamp);
        } else {
            (spent0, spent1) =
                manager.increase{value: nativeValue}(p.poolId, p.lpTokenId, a0, a1, minimumLiquidity, deadline);
        }
        _approvePrincipalAssets(token0,token1,operator,0,0);
        budget.assertPut(bucketId, a0, a1, spent0, spent1, before0, before1);
        _idle(bucketId, p.idle0 - spent0, p.idle1 - spent1);
        budget.assertDeployed(bucketId);
    }

    /// @notice Paid issuance creates no LP, collective membership or fee entitlement. Proceeds are
    /// forwarded separately and never enter the permanently locked principal ledger.
    function mintPrice() external view returns(uint256) {
        return canonicalModule().mintPrice();
    }
    function mintProceedsRecipient() external view returns(address payable) {
        return payable(canonicalModule().mintProceedsRecipient());
    }
    function mintPolicyFingerprint() external view returns(bytes32) {
        return canonicalModule().mintPolicyFingerprint();
    }
    function mintDormant(bytes32 expectedMintPolicy) external payable live operating principalOperating nonReentrant returns (uint256 id) {
        address recipient;
        (id,recipient) = canonicalModule().validateMint(msg.value, ++sequence,expectedMintPolicy);
        if (minted[id]) revert InvalidState();
        minted[id] = true;
        _nft().mint(msg.sender, id);
        (bool paid,) = payable(recipient).call{value: msg.value}("");
        if (!paid || canonicalModule().mintPolicyFingerprint() != expectedMintPolicy) revert InvalidState();
        emit DormantMinted(id, msg.sender, msg.value);
    }

    /// @notice New NFTs join the sole shared position for this pool. No redeemable token is issued.
    function activate(
        uint256 id,
        bytes32 poolId,
        uint256 amount0,
        uint256 amount1,
        uint128 minimumLiquidity,
        uint256 deadline
    ) external payable live operating principalOperating nonReentrant {
        _requireOwner(id, true);
        uint256 bucket = poolBucket[poolId];
        if (bucket == 0 || positions[bucket].status == PositionStatus.None) {
            uint256 canonicalBucket = canonicalModule().bucketIdentity(poolId);
            if (bucket != 0 && bucket != canonicalBucket) revert InvalidState();
            bucket = canonicalBucket;
            _reserve(poolId, bucket);
            homePoolId[bucket] = poolId;
            Position storage p = positions[bucket];
            p.poolId = poolId;
            p.status = PositionStatus.Active;
        }
        if (positions[bucket].poolId != poolId) revert InvalidState();
        nftBucket[id] = bucket; // Set the fee-index domain BEFORE checkpointing zero shares.
        _join(id, bucket, amount0, amount1, minimumLiquidity, deadline, true);
        emit Activated(id, _nft().ownerOf(id), poolId, amount0, amount1);
    }

    function increase(uint256 id, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline)
        external
        payable
        live
        operating
        principalOperating
        nonReentrant
    {
        _requireOwner(id, false);
        uint256 bucket = nftBucket[id];
        if (bucket == 0) revert InvalidState();
        _join(id, bucket, amount0, amount1, minimumLiquidity, deadline, false);
        emit LiquidityAdded(id, amount0, amount1);
    }

    function _nav(uint256 bucketId) private returns (uint256 deployed, uint256 idleValue) {
        return migrationBudget.contributionNav(bucketId);
    }

    function _join(
        uint256 nftId,
        uint256 bucketId,
        uint256 amount0,
        uint256 amount1,
        uint128 minimumLiquidity,
        uint256 deadline,
        bool activation
    ) private {
        _deadline(deadline);
        Position storage p = positions[bucketId];
        IZZZFees fees = IZZZFees(_moduleFees());
        uint256 inputUSD = IZZZPools(_modulePools()).contributionValue(p.poolId, amount0, amount1);
        (address token0, address token1, uint32 limits) = migrationBudget.validateContribution(
            nftId, bucketId, inputUSD, amount0 | (amount1 << 128), minimumLiquidity, activation
        );
        uint256 supply = bucketTotalShares[bucketId];
        // Settle all already-funded collective dust before eligibility changes.
        // Only this nonreentrant Vault can allocate new LP fee receipts.
        IZZZMembership(access.module(Ids.MEMBERSHIP)).settleDust();
        if (supply != 0) {
            _harvest(bucketId, deadline);
            fees.flushDust(bucketId, token0);
            fees.flushDust(bucketId, token1);
            _pullCompound(bucketId);
        }
        (uint256 oldLP, uint256 oldIdle) = _nav(bucketId);
        uint256 incumbentNAV = oldLP + oldIdle;
        if (supply != 0 && incumbentNAV == 0) revert InvalidState();
        _receiveAssets(token0, token1, amount0, amount1);
        _idle(bucketId, p.idle0 + amount0, p.idle1 + amount1);
        (amount0, amount1) = _balanceUsing(bucketId, deadline, amount0, amount1);
        uint256 freshCompound;
        if (supply != 0) {
            // Fees earned by the entry swap belong to pre-entry membership.
            _harvest(bucketId, deadline);
            fees.flushDust(bucketId, token0);
            fees.flushDust(bucketId, token1);
            (uint256 f0, uint256 f1) = _pullCompound(bucketId);
            freshCompound = _valueBucket(bucketId, f0, f1);
        }
        // Concentrated LP amounts reprice during the entry swap. Preserve that
        // gain/loss for incumbents; only net new assets buy the entrant's shares.
        (oldLP,) = _nav(bucketId);
        incumbentNAV = oldLP + oldIdle + freshCompound;
        if (supply != 0 && incumbentNAV == 0) revert InvalidState();
        _put(bucketId, supply == 0, minimumLiquidity, deadline, amount0, amount1);
        (uint256 late0, uint256 late1) = _pullCompound(bucketId);
        incumbentNAV += _valueBucket(bucketId, late0, late1);
        (uint256 newLP, uint256 newIdle) = _nav(bucketId);
        // Unclassified donations during callbacks cannot become LP fee income.
        IZZZRewards(access.module(Ids.REWARDS)).checkpointOwner(nftId);
        // The captured governed contribution limit applies to activation and
        // growth. Network gas is separate; later callbacks cannot widen this budget.
        // Incumbent idle/compound assets cannot subsidize this contribution.
        (uint256 issued, uint256 netUSD) = migrationBudget.contributionResult(
            bucketId, inputUSD, supply, incumbentNAV, oldLP, newLP, newIdle, limits
        );
        sharesOf[nftId] += issued;
        bucketTotalShares[bucketId] = supply + issued;
        contributionUSD[nftId] += inputUSD;
        p.depositUSD += inputUSD;
        if (activation) IZZZMembership(access.module(Ids.MEMBERSHIP)).activate(nftId);
        _nft().notifyContribution(nftId);
        emit SharesAdded(nftId, bucketId, issued, netUSD);
    }

    function _allocate(uint256 bucketId, address token, uint256 amount) private {
        if (amount == 0) return;
        address fees = _moduleFees();
        ExactAsset.approve(token, fees, amount);
        IZZZFees(fees).allocate{value: token == address(0) ? amount : 0}(bucketId, token, amount);
        ExactAsset.approve(token, fees, 0);
    }

    /// @dev Separate and fund venue fees before closing principal.
    function _harvest(uint256 bucketId, uint256 deadline) private {
        _receiveVenue(bucketId, deadline, 0);
    }

    /// @dev Collection and closure share the same exact net-receipt proof.
    /// Manager performs the bounded portfolio operation atomically; neither
    /// raw prefunds nor forced ETH can become attributed receipts.
    /// @param operation Internal typed mode: collect=0, full close=1, residual close=2.
    function _receiveVenue(uint256 bucketId, uint256 deadline, uint8 operation) private {
        Position storage p = positions[bucketId];
        (address token0, address token1) = _tokens(bucketId);
        uint256 before0 = _tokenBalance(token0);
        uint256 before1 = _tokenBalance(token1);
        uint256 received = nativeReceived;
        IZZZLiquidity manager = IZZZLiquidity(_moduleLiquidity());
        if (operation == 0) manager.collect(p.poolId, p.lpTokenId, deadline);
        else if (operation == 1) manager.close(p.poolId, p.lpTokenId, deadline);
        else IVaultResidualLiquidity(address(manager)).closeSecondary(p.poolId, p.lpTokenId, deadline);
        uint256 amount0 = _tokenBalance(token0) - before0;
        uint256 amount1 = _tokenBalance(token1) - before1;
        if (token0 == address(0) && amount0 != nativeReceived - received) revert InvalidState();
        if (operation != 0) {
            if (operation == 1) p.lpTokenId = 0;
            _idle(bucketId, p.idle0 + amount0, p.idle1 + amount1);
        } else {
            _allocate(bucketId, token0, amount0);
            _allocate(bucketId, token1, amount1);
            emit FeesCollected(bucketId, amount0, amount1);
        }
    }

    function collectFees(uint256 id, uint256 deadline) external live nonReentrant canonicalAccounting principalOperating {
        _deadline(deadline);
        _active(id);
        _harvest(id, deadline);
    }

    function _pullCompound(uint256 bucketId) private returns (uint256 amount0, uint256 amount1) {
        (address token0, address token1) = _tokens(bucketId);
        Position storage p = positions[bucketId];
        IZZZFees fees = IZZZFees(_moduleFees());
        amount0 = fees.releaseCompound(bucketId, token0);
        amount1 = fees.releaseCompound(bucketId, token1);
        _idle(bucketId, p.idle0 + amount0, p.idle1 + amount1);
    }

    function compound(uint256 id, uint128 minimumLiquidity, uint256 deadline)
        external
        onlyModule(Ids.COMPOUNDER)
        live
        operating
        principalOperating
        nonReentrant
    {
        _deadline(deadline);
        _active(id);
        _migrationCheckpoint(id, 3);
        _harvest(id, deadline);
        (uint256 amount0, uint256 amount1) = _pullCompound(id);
        _migrationCheckpoint(id, 1);
        _redeploy(id, minimumLiquidity, deadline);
        _migrationCheckpoint(id, 2);
        emit Compounded(id, amount0, amount1);
    }

    function _close(uint256 bucketId, uint256 deadline) private {
        _receiveVenue(bucketId, deadline, 1);
    }

    /// @dev One atomic route/size decision consumes only this explicit budget.
    /// Whole-bucket attribution remains intact during external calls.
    function _balanceUsing(uint256 bucketId, uint256 deadline, uint256 amount0, uint256 amount1)
        private returns (uint256 balanced0, uint256 balanced1) {
        Position storage p = positions[bucketId];
        if (amount0 > p.idle0 || amount1 > p.idle1) revert InvalidAmount();
        (address token0, address token1) = _tokens(bucketId);
        address manager = _moduleLiquidity();
        uint256 before0 = _tokenBalance(token0);
        uint256 before1 = _tokenBalance(token1);
        bytes32 context = migrationBudget.balanceContext(bucketId);
        _approvePrincipalAssets(token0,token1,manager,amount0,amount1);
        (balanced0, balanced1) = IZZZLiquidity(manager).balance{value: token0 == address(0) ? amount0 : 0}(
            p.poolId, p.lpTokenId, amount0, amount1, deadline
        );
        _approvePrincipalAssets(token0,token1,manager,0,0);
        if (migrationBudget.balanceContext(bucketId) != context) revert InvalidState();
        // A typed return must match actual net receipts. Existing raw prefunds
        // or callback donations cannot fill a claimed balancing-output shortfall.
        if (_tokenBalance(token0) + amount0 != before0 + balanced0 ||
            _tokenBalance(token1) + amount1 != before1 + balanced1) revert InvalidState();
        _idle(bucketId, p.idle0 - amount0 + balanced0, p.idle1 - amount1 + balanced1);
    }

    function _idleValue(uint256 bucketId) private view returns (uint256) {
        return migrationBudget.idleValue(bucketId);
    }

    function _unwind(uint256 bucketId, uint256 deadline) private {
        migrationBudget.validateUnwind(bucketId);
        _harvest(bucketId, deadline);
        _pullCompound(bucketId);
        _migrationCheckpoint(bucketId, 1);
        _close(bucketId, deadline);
    }

    function _migrationCheckpoint(uint256 bucketId, uint8 phase) private {
        migrationBudget.checkpoint(bucketId, phase);
    }

    function _redeploy(uint256 bucketId, uint128 minimumLiquidity, uint256 deadline) private {
        bool create = positions[bucketId].lpTokenId == 0;
        uint256 beforeValue = _idleValue(bucketId);
        Position storage p = positions[bucketId];
        _balanceUsing(bucketId, deadline, p.idle0, p.idle1);
        // An existing LP can earn fees from its one balancing swap. Settle
        // them separately before INCREASE; they are never treated as principal.
        if (!create) _harvest(bucketId, deadline);
        migrationBudget.assertIdleLoss(bucketId, beforeValue);
        _put(bucketId, create, minimumLiquidity, deadline, p.idle0, p.idle1);
    }

    function rebalance(uint256 id, uint128 minimumLiquidity, uint256 deadline)
        external
        onlyKeeper
        live
        operating
        principalOperating
        nonReentrant
    {
        _rebalance(id,minimumLiquidity,deadline,false);
        if (!access.keeperAuthorized(msg.sender) || access.paused()) revert Unauthorized();
    }
    /// @notice Only the sealed Migration module can forward paused-governance
    /// emergency. No keeper, holder, arbitrary executor or recipient is admitted.
    function emergencyRebalance(uint256 id,uint128 minimumLiquidity,uint256 deadline)
        external onlyModule(Ids.MIGRATION) operating principalOperating nonReentrant {
        IZZZEmergencyLiquidity(_moduleLiquidity()).beginEmergency();
        _rebalance(id,minimumLiquidity,deadline,true);
        IZZZEmergencyLiquidity(_moduleLiquidity()).endEmergency();
    }
    function _rebalance(uint256 id,uint128 minimumLiquidity,uint256 deadline,bool emergency) private {
        _deadline(deadline);
        bool parked = emergency && positions[id].status == PositionStatus.Parked;
        if(!parked) _active(id);
        migrationBudget.validateRebalance(id, minimumLiquidity);
        Position storage p = positions[id];
        uint256 oldId = p.lpTokenId;
        _migrationCheckpoint(id, 0);
        if(parked) { _pullCompound(id); _migrationCheckpoint(id,1); }
        else _unwind(id, deadline);
        _redeploy(id, minimumLiquidity, deadline);
        _migrationCheckpoint(id, 2);
        if(parked) p.status = PositionStatus.Active;
        emit Rebalanced(id, oldId, p.lpTokenId, p.centerX96);
    }

    /// @notice Migration commits terminal LP retirement through this lock so it
    /// cannot start reentrantly inside contribution, harvest or maintenance.
    function beginLPExit() external onlyModule(Ids.MIGRATION) operating nonReentrant {
        access.startLPExit();
    }

    /// @notice Close one fixed ETH/ZZZ bucket into the holder settlement module.
    /// No swap or USD price dependency. Only attributed principal and its 5%
    /// compound reserve leave; earned fees, buyback reserves and donations do not.
    function exitBucketToHolders(uint256 id, uint256 minimumETH, uint256 minimumZZZ, uint256 deadline)
        external onlyModule(Ids.MIGRATION) operating nonReentrant
        returns (uint256 amountETH, uint256 amountZZZ)
    {
        _deadline(deadline);
        Position storage p = positions[id];
        (address token0, address token1) = migrationBudget.validateHolderExit(id,msg.sender);
        // Final harvest runs while Active, as required by funded fee allocation.
        if (p.status == PositionStatus.Active) _harvest(id, deadline);
        IZZZFees fees = IZZZFees(_moduleFees());
        fees.flushDust(id, token0);
        fees.flushDust(id, token1);
        _pullCompound(id);
        if (p.status == PositionStatus.Active) _close(id, deadline);
        if (p.lpTokenId != 0) revert InvalidState();
        amountETH = p.idle0;
        amountZZZ = p.idle1;
        if (amountETH < minimumETH || amountZZZ < minimumZZZ) revert Slippage();
        _idle(id, 0, 0);
        p.status = PositionStatus.Exited;
        migrationBudget.recordComposition(id);
        ExactAsset.push(token0, msg.sender, amountETH);
        ExactAsset.push(token1, msg.sender, amountZZZ);
        emit PrincipalReturnedToHolders(id, amountETH, amountZZZ);
    }

    /// @notice Paused governed residual-only close. Actual proceeds remain
    /// attributed to this bucket; no swap, holder payout or main replacement.
    /// A large retained idle balance is intentional recovery state, not entry
    /// permission to bypass the ordinary deployment/idle/loss checks.
    function closeResidual(uint256 id,uint256 deadline)
        external onlyModule(Ids.MIGRATION) operating principalOperating nonReentrant {
        _deadline(deadline);
        migrationBudget.validateResidualClose(id);
        _harvest(id,deadline);
        _receiveVenue(id,deadline,2);
        if(!access.paused()) revert InvalidState();
    }

    /// @notice Only the fixed Migration module can park an LP. Its governed
    /// request binds exact custody and raw close minimums. No assets leave Vault.
    function park(uint256 id, uint256 deadline) external onlyModule(Ids.MIGRATION) nonReentrant canonicalAccounting principalOperating {
        _deadline(deadline);
        _active(id);
        if (!access.paused() || positions[id].lpTokenId == 0) revert InvalidState();
        uint256 oldLp = positions[id].lpTokenId;
        _harvest(id, deadline);
        _close(id, deadline);
        positions[id].status = PositionStatus.Parked;
        emit PrincipalParked(id, oldLp);
    }

    function resume(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline)
        external
        onlyModule(Ids.MIGRATION)
        live
        operating
        principalOperating
        nonReentrant
    {
        _deadline(deadline);
        if (positions[id].status != PositionStatus.Parked) revert InvalidState();
        _movePool(id, newPool, minimumLiquidity, deadline);
        positions[id].status = PositionStatus.Active;
    }

    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline)
        external
        onlyModule(Ids.MIGRATION)
        live
        operating
        principalOperating
        nonReentrant
    {
        _deadline(deadline);
        _active(id);
        if (positions[id].poolId == newPool) revert InvalidConfiguration();
        _movePool(id, newPool, minimumLiquidity, deadline);
    }

    function _movePool(uint256 bucketId, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline) private {
        Position storage p = positions[bucketId];
        migrationBudget.validateMove(bucketId, newPool, minimumLiquidity);
        _reserve(newPool, bucketId);
        uint256 oldId = p.lpTokenId;
        _migrationCheckpoint(bucketId, 0);
        if (p.status == PositionStatus.Parked) {
            _pullCompound(bucketId);
            _migrationCheckpoint(bucketId, 1);
        } else {
            _unwind(bucketId, deadline);
        }
        p.poolId = newPool; // Ordinary local maintenance retains its ordered-pair guard.
        _redeploy(bucketId, minimumLiquidity, deadline);
        _migrationCheckpoint(bucketId, 2);
        emit Rebalanced(bucketId, oldId, p.lpTokenId, p.centerX96);
    }

    function onERC721Received(address, address, uint256, bytes calldata) external view override returns (bytes4) {
        migrationBudget.validateLPReceiver(msg.sender);
        return IERC721Receiver.onERC721Received.selector;
    }

    /// @dev Only the immutable canonical companion can write source-authenticated
    /// records while this deployment is inert. No raw storage slots are exposed.
    function canonicalWrite(uint8 kind, bytes calldata row) external {
        migrationBudget.validateCanonicalWriter(msg.sender);
        if (kind == 0) {
            sequence = abi.decode(row, (uint256));
        } else if (kind == 1) {
            (uint256 id, uint256 bucket, uint256 shares, uint256 contribution) =
                abi.decode(row, (uint256, uint256, uint256, uint256));
            if (minted[id]) revert InvalidState();
            minted[id] = true;
            nftBucket[id] = bucket;
            sharesOf[id] = shares;
            contributionUSD[id] = contribution;
        } else if (kind == 2) {
            (uint256 id, Position memory p, uint256 shares, bytes32 homePool) =
                abi.decode(row, (uint256, Position, uint256, bytes32));
            _registerBucket(id);
            positions[id] = p;
            bucketTotalShares[id] = shares;
            homePoolId[id] = homePool;
            if (p.status == PositionStatus.Parked) {
                (address a, address b) = migrationBudget.poolTokens(p.poolId);
                totalIdle[a] += p.idle0;
                totalIdle[b] += p.idle1;
            }
        } else if (kind == 3) {
            (bytes32 pool, uint256 id) = abi.decode(row, (bytes32, uint256));
            poolBucket[pool] = id;
        } else {
            revert InvalidConfiguration();
        }
    }

    /// @dev Recipient and amount come only from the fixed companion's captured
    /// manifest and the handoff's fixed module pairing. No public rescue path.
    function canonicalSend(address token, address destination, uint256 amount) external {
        _canonicalSender();
        ExactAsset.push(token, destination, amount);
    }

    function canonicalBarrier() external nonReentrant {
        _canonicalSender();
    }

    function _canonicalSender() private view {
        if (msg.sender != access.module(Ids.VAULT_CANONICAL)) revert Unauthorized();
    }

    // No individual early redemption, external custody recipient or generic sweep.
    function _modulePools() private view returns (address) {
        return access.module(Ids.POOLS);
    }

    function _moduleLiquidity() private view returns (address) {
        return access.module(Ids.LIQUIDITY);
    }

    function _moduleFees() private view returns (address) {
        return access.module(Ids.FEES);
    }
}

