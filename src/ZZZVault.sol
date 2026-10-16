// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZNFT, IZZZMembership, IZZZFees, IZZZPools, IZZZOracle, IZZZStrategy, IZZZLiquidity,
    IPositionManagerMinimal, IZZZRewards, IZZZMigration, IZZZActivationEntry} from "./interfaces/IZZZ.sol";

/// @notice Non-upgradeable custody. Principal has no owner/admin redemption path.
/// Deposits, idle assets, compound reserves and earned fees are separate ledgers.
contract ZZZVault is ZZZModule, ReentrancyGuard, IERC721Receiver {
    using SafeERC20 for IERC20;
    mapping(uint256 => Position) private positions; // Custody is keyed by stable bucket, never NFT.
    mapping(uint256 => bool) private minted;
    mapping(uint256 => uint256) public nftBucket;
    mapping(uint256 => uint256) public sharesOf;
    mapping(uint256 => uint256) public contributionUSD;
    mapping(uint256 => uint256) public bucketTotalShares;
    mapping(uint256 => bytes32) public homePoolId;
    mapping(bytes32 => uint256) public poolBucket;
    uint256[] private buckets;
    uint256 private constant MAX_SHARES = 1e36;
    // Bounds combined funded inbox/dust work, with all reward assets admitted.
    // Existing-bucket returns and pool migrations reuse their historical slot.
    uint256 public constant MAX_BUCKETS = 4;
    event PoolReserved(bytes32 indexed poolId, uint256 indexed bucketId);
    event SharesAdded(uint256 indexed nftId, uint256 indexed bucketId, uint256 shares, uint256 netUSD);
    mapping(address => uint256) public totalIdle;
    uint256 public sequence;
    uint256 public immutable canonicalChainId;
    address payable public immutable mintProceedsRecipient;
    uint256 public constant MINT_PRICE = 0.05 ether;
    uint256 private constant MIN_ACTIVATION_INPUT_USD = 100e18;
    uint256 private constant MAX_IDLE_BPS = 500; // At least 95% deployed by oracle value after LP updates.
    event DormantMinted(uint256 indexed nftId, address indexed owner, uint256 mintPrice);
    event Activated(uint256 indexed nftId, address indexed owner, bytes32 indexed poolId, uint256 amount0, uint256 amount1);
    event LiquidityAdded(uint256 indexed nftId, uint256 amount0, uint256 amount1);
    event FeesCollected(uint256 indexed bucketId, uint256 amount0, uint256 amount1);
    event Rebalanced(uint256 indexed bucketId, uint256 oldLpTokenId, uint256 newLpTokenId, uint160 centerX96);
    event Compounded(uint256 indexed bucketId, uint256 amount0, uint256 amount1);
    event PrincipalBridged(uint256 indexed bucketId, bytes32 indexed migrationId, uint256 amount0, uint256 amount1);
    event ImportPending(uint256 indexed bucketId, uint256 indexed homeChain, address indexed homeVault);
    event ImportFinalized(uint256 indexed bucketId, uint256 lpTokenId);
    event LocationConfirmed(uint256 indexed bucketId, uint256 chainId, address destinationVault);
    event PrincipalParked(uint256 indexed bucketId, uint256 oldLpTokenId);
    constructor(address controller, uint256 nftHomeChain, address payable mintRecipient) ZZZModule(controller) {
        if (nftHomeChain == 0 || mintRecipient == address(0) || mintRecipient == address(this)) revert InvalidConfiguration();
        canonicalChainId = nftHomeChain;
        mintProceedsRecipient = mintRecipient;
    }
    /// @notice NFT lifecycle is separate from shared physical LP custody.
    function nftStatus(uint256 id) external view returns (PositionStatus) {
        if (!minted[id]) return PositionStatus.None;
        uint256 bucket = nftBucket[id];
        return bucket == 0 ? PositionStatus.Dormant : positions[bucket].status;
    }
    function group(uint256 bucket) external view returns (Position memory) { return positions[bucket]; }
    function bucketCount() external view returns (uint256) { return buckets.length; }
    function bucketAt(uint256 index) external view returns (uint256) { return buckets[index]; }
    /// @dev Historical slots never free up. Returning custody reuses its bucket.
    function _registerBucket(uint256 bucket) private {
        if (buckets.length == MAX_BUCKETS) revert InvalidState();
        buckets.push(bucket);
    }
    /// @notice Reserve destinations before approving a route. Reservations cannot be reassigned.
    function reservePool(bytes32 pool, uint256 bucket) external onlyGovernance { _reserve(pool, bucket); }
    function _reserve(bytes32 pool, uint256 bucket) private {
        if (pool == bytes32(0) || bucket == 0) revert InvalidConfiguration();
        IZZZPools(_modulePools()).get(pool);
        uint256 old = poolBucket[pool];
        if (old != 0 && old != bucket) revert InvalidState();
        poolBucket[pool] = bucket;
        emit PoolReserved(pool, bucket);
    }
    function _pool(uint256 id) private view returns (PoolConfig memory) {
        return IZZZPools(_modulePools()).accounting(positions[id].poolId);
    }
    function _isHome(Position storage p) private view returns (bool) {
        return p.homeChain == block.chainid && p.homeVault == address(this);
    }
    function _nft() private view returns (IZZZNFT) { return IZZZNFT(access.module(Ids.NFT)); }
    function _requireOwner(uint256 id) private view {
        if (block.chainid != canonicalChainId || !minted[id]) revert Unauthorized();
        if (_nft().ownerOf(id) == msg.sender) return;
        address entry = IZZZPools(_modulePools()).activationEntry();
        if (entry == address(0) || msg.sender != entry) revert Unauthorized();
        IZZZActivationEntry(entry).validateOwner(id, keccak256(msg.data));
    }
    function _active(uint256 id) private view {
        if (positions[id].status != PositionStatus.Active) revert InvalidState();
    }
    function _tokenBalance(address token) private view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }
    function _idle(uint256 id, uint256 new0, uint256 new1) private {
        if (new0 > type(uint128).max || new1 > type(uint128).max) revert InvalidAmount();
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        totalIdle[c.key.currency0] = totalIdle[c.key.currency0] - p.idle0 + new0;
        totalIdle[c.key.currency1] = totalIdle[c.key.currency1] - p.idle1 + new1;
        p.idle0 = new0;
        p.idle1 = new1;
        if (_tokenBalance(c.key.currency0) < totalIdle[c.key.currency0] ||
            _tokenBalance(c.key.currency1) < totalIdle[c.key.currency1]) revert InvalidState();
    }
    function _valuePair(PoolConfig memory c, uint256 amount0, uint256 amount1) private view returns (uint256) {
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        return oracle.value(c.key.currency0, amount0) + oracle.value(c.key.currency1, amount1);
    }
    function _put(uint256 id, bool create, uint128 minimumLiquidity, uint256 deadline) private returns (uint256 deployedValue) {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        IZZZLiquidity manager = IZZZLiquidity(_moduleLiquidity());
        uint256 a0 = p.idle0;
        uint256 a1 = p.idle1;
        uint256 before0 = _tokenBalance(c.key.currency0);
        uint256 before1 = _tokenBalance(c.key.currency1);
        IERC20(c.key.currency0).forceApprove(address(manager), a0);
        IERC20(c.key.currency1).forceApprove(address(manager), a1);
        uint256 spent0;
        uint256 spent1;
        if (create) {
            (int24 lower, int24 upper, uint160 ref) = IZZZStrategy(_moduleStrategy()).target(p.poolId);
            (p.lpTokenId, spent0, spent1) = manager.mint(p.poolId, lower, upper, a0, a1, minimumLiquidity, deadline);
            IPositionManagerMinimal(manager.positionManager()).approve(address(manager), p.lpTokenId);
            p.centerX96 = ref;
            p.lastRebalance = uint64(block.timestamp);
        } else {
            (spent0, spent1) = manager.increase(p.poolId, p.lpTokenId, a0, a1, minimumLiquidity, deadline);
        }
        IERC20(c.key.currency0).forceApprove(address(manager), 0);
        IERC20(c.key.currency1).forceApprove(address(manager), 0);
        if (spent0 > a0 || spent1 > a1 ||
            _tokenBalance(c.key.currency0) + spent0 != before0 ||
            _tokenBalance(c.key.currency1) + spent1 != before1 ||
            IPositionManagerMinimal(manager.positionManager()).ownerOf(p.lpTokenId) != address(this)) revert InvalidState();
        _idle(id, a0 - spent0, a1 - spent1);
        (uint256 deployed0, uint256 deployed1) = manager.amounts(p.lpTokenId);
        deployedValue = _valuePair(c, deployed0, deployed1);
        uint256 idleValue = _valuePair(c, p.idle0, p.idle1);
        _checkIdle(deployedValue, idleValue);
    }
    function _checkIdle(uint256 deployed, uint256 idleValue) private pure {
        if (deployed == 0 || idleValue > Math.mulDiv(deployed + idleValue, MAX_IDLE_BPS, 10000)) revert Slippage();
    }
    /// @notice Paid issuance creates no LP, collective membership or fee entitlement. Proceeds are
    /// forwarded separately and never enter the permanently locked principal ledger.
    function mintDormant() external payable live nonReentrant returns (uint256 id) {
        // Satellite vaults can receive migrated positions, but never issue a second collection.
        if (block.chainid != canonicalChainId) revert InvalidState();
        if (msg.value != MINT_PRICE) revert InvalidAmount();
        id = uint256(keccak256(abi.encode(block.chainid, address(this), ++sequence)));
        if (minted[id]) revert InvalidState();
        minted[id] = true;
        _nft().mint(msg.sender, id);
        (bool paid,) = mintProceedsRecipient.call{value: msg.value}("");
        if (!paid) revert InvalidState();
        emit DormantMinted(id, msg.sender, msg.value);
    }
    /// @notice New NFTs join the sole shared position for this pool. No redeemable token is issued.
    function activate(uint256 id, bytes32 poolId, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline)
        external live nonReentrant {
        _requireOwner(id);
        if (nftBucket[id] != 0 || !_nft().traitsReady(id)) revert InvalidState();
        uint256 bucket = poolBucket[poolId];
        if (bucket == 0 || positions[bucket].status == PositionStatus.None) {
            uint256 canonicalBucket = uint256(keccak256(abi.encode(block.chainid, address(this), poolId)));
            if (bucket != 0 && bucket != canonicalBucket) revert InvalidState();
            bucket = canonicalBucket;
            _reserve(poolId, bucket);
            homePoolId[bucket] = poolId;
            _registerBucket(bucket);
            Position storage p = positions[bucket];
            PoolConfig memory c = IZZZPools(_modulePools()).accounting(poolId);
            p.poolId = poolId; p.status = PositionStatus.Active;
            p.homeChain = block.chainid; p.homeVault = address(this); p.homeReceiver = access.module(Ids.RECEIVER);
            p.homeToken0 = c.key.currency0; p.homeToken1 = c.key.currency1;
            p.locationChain = block.chainid; p.locationVault = address(this);
        }
        if (positions[bucket].poolId != poolId) revert InvalidState();
        nftBucket[id] = bucket; // Set the fee-index domain BEFORE checkpointing zero shares.
        _join(id, bucket, amount0, amount1, minimumLiquidity, deadline, true);
        emit Activated(id, _nft().ownerOf(id), poolId, amount0, amount1);
    }
    function increase(uint256 id, uint256 amount0, uint256 amount1, uint128 minimumLiquidity, uint256 deadline)
        external live nonReentrant {
        _requireOwner(id);
        uint256 bucket = nftBucket[id];
        if (bucket == 0) revert InvalidState();
        _join(id, bucket, amount0, amount1, minimumLiquidity, deadline, false);
        emit LiquidityAdded(id, amount0, amount1);
    }
    function _nav(uint256 bucket) private view returns (uint256 deployed, uint256 idleValue) {
        Position storage p = positions[bucket];
        PoolConfig memory c = _pool(bucket);
        if (p.lpTokenId != 0) {
            (uint256 a0, uint256 a1) = IZZZLiquidity(_moduleLiquidity()).amounts(p.lpTokenId);
            deployed = _valuePair(c, a0, a1);
        }
        idleValue = _valuePair(c, p.idle0, p.idle1);
    }
    function _join(uint256 id, uint256 bucket, uint256 amount0, uint256 amount1, uint128 minimumLiquidity,
        uint256 deadline, bool activation) private {
        _deadline(deadline); _active(bucket);
        Position storage p = positions[bucket];
        IZZZFees fees = IZZZFees(_moduleFees());
        if (!_isHome(p) || !fees.remoteSettled(bucket) ||
            IZZZMigration(access.module(Ids.MIGRATION)).activePlan(bucket) != bytes32(0)) revert InvalidState();
        PoolConfig memory c = _pool(bucket);
        if (!c.depositsEnabled || amount0 + amount1 == 0 || minimumLiquidity == 0) revert InvalidAmount();
        uint256 inputUSD = IZZZPools(_modulePools()).contributionValue(p.poolId, amount0, amount1);
        if (activation && inputUSD < MIN_ACTIVATION_INPUT_USD) revert InvalidAmount();
        if (inputUSD < c.minDepositUSD || contributionUSD[id] + inputUSD > c.maxPositionUSD) revert InvalidAmount();
        uint256 supply = bucketTotalShares[bucket];
        // Other inboxes also fund the global collective index. Settle ALL before entry.
        fees.syncAllExternal();
        if (supply != 0) {
            _harvest(bucket, deadline);
            fees.flushDust(bucket, c.key.currency0); fees.flushDust(bucket, c.key.currency1);
            _pullCompound(bucket);
        }
        (uint256 oldLP, uint256 oldIdle) = _nav(bucket);
        uint256 incumbentNAV = oldLP + oldIdle;
        if (supply != 0 && incumbentNAV == 0) revert InvalidState();
        ExactToken.pull(c.key.currency0, msg.sender, amount0);
        ExactToken.pull(c.key.currency1, msg.sender, amount1);
        _idle(bucket, p.idle0 + amount0, p.idle1 + amount1);
        _balanceUsing(bucket, deadline, supply != 0);
        uint256 freshCompound;
        // Settle any payments arriving during external entry calls before weights change.
        fees.syncAllExternal();
        if (supply != 0) {
            // Fees earned by the entry swap belong to pre-entry membership.
            _harvest(bucket, deadline);
            fees.flushDust(bucket, c.key.currency0); fees.flushDust(bucket, c.key.currency1);
            (uint256 f0, uint256 f1) = _pullCompound(bucket);
            freshCompound = _valuePair(c, f0, f1);
        }
        // Concentrated LP amounts reprice during the entry swap. Preserve that
        // gain/loss for incumbents; only net new assets buy the entrant's shares.
        (oldLP,) = _nav(bucket);
        incumbentNAV = oldLP + oldIdle + freshCompound;
        if (supply != 0 && incumbentNAV == 0) revert InvalidState();
        _put(bucket, supply == 0, minimumLiquidity, deadline);
        // LP mint/increase can call tokens. Settle late receipts under OLD weights.
        fees.syncAllExternal();
        (uint256 late0, uint256 late1) = _pullCompound(bucket);
        incumbentNAV += _valuePair(c, late0, late1);
        (uint256 newLP, uint256 newIdle) = _nav(bucket);
        _checkIdle(newLP, newIdle);
        // A transfer callback during the final pull may queue more receipts/dust.
        // All remaining dependency calls are static reads or fixed checkpoints.
        if (fees.hasPendingExternal()) revert InvalidState();
        IZZZRewards(access.module(Ids.REWARDS)).checkpointOwner(id);
        if (newLP + newIdle <= incumbentNAV) revert InvalidAmount();
        uint256 netUSD = newLP + newIdle - incumbentNAV;
        if (netUSD < Math.mulDiv(inputUSD, 10000 - c.maxSlippageBps, 10000)) revert Slippage();
        // A $100 gross contribution may deploy $99; network gas is separate.
        // Apply the same 1% execution/undeployed limit to later contributions.
        // Incumbent idle/compound assets cannot subsidize this contribution.
        uint256 minimumNet = inputUSD - inputUSD / 100; // ceil(99%); no multiplication overflow.
        if (netUSD < minimumNet || newLP < oldLP + oldIdle + freshCompound + minimumNet) revert Slippage();
        uint256 issued = supply == 0 ? netUSD : Math.mulDiv(supply, netUSD, incumbentNAV);
        if (issued == 0 || supply + issued > MAX_SHARES) revert InvalidAmount();
        sharesOf[id] += issued; bucketTotalShares[bucket] = supply + issued;
        contributionUSD[id] += inputUSD; p.depositUSD += inputUSD;
        if (activation) IZZZMembership(access.module(Ids.MEMBERSHIP)).activate(id);
        _nft().notifyContribution(id);
        emit SharesAdded(id, bucket, issued, netUSD);
    }
    function _allocate(uint256 id, address token, uint256 amount) private {
        if (amount == 0) return;
        address fees = _moduleFees();
        IERC20(token).forceApprove(fees, amount);
        IZZZFees(fees).allocate(id, token, amount);
        IERC20(token).forceApprove(fees, 0);
    }
    function _harvest(uint256 id, uint256 deadline) private {
        IZZZFees(_moduleFees()).syncExternal(id);
        _harvestVenue(id, deadline);
    }
    /// @dev Custody parking must not depend on an unrelated creator inbox.
    /// Venue fees are still separated and funded before closing principal.
    function _harvestVenue(uint256 id, uint256 deadline) private {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        uint256 before0 = _tokenBalance(c.key.currency0);
        uint256 before1 = _tokenBalance(c.key.currency1);
        IZZZLiquidity(_moduleLiquidity()).collect(p.poolId, p.lpTokenId, deadline);
        uint256 fee0 = _tokenBalance(c.key.currency0) - before0;
        uint256 fee1 = _tokenBalance(c.key.currency1) - before1;
        _allocate(id, c.key.currency0, fee0);
        _allocate(id, c.key.currency1, fee1);
        emit FeesCollected(id, fee0, fee1);
    }
    function collectFees(uint256 id, uint256 deadline) external live nonReentrant {
        _deadline(deadline);
        _active(id);
        _harvest(id, deadline);
    }
    function _pullCompound(uint256 id) private returns (uint256 amount0, uint256 amount1) {
        PoolConfig memory c = _pool(id);
        Position storage p = positions[id];
        IZZZFees fees = IZZZFees(_moduleFees());
        amount0 = fees.releaseCompound(id, c.key.currency0);
        amount1 = fees.releaseCompound(id, c.key.currency1);
        _idle(id, p.idle0 + amount0, p.idle1 + amount1);
    }
    function compound(uint256 id, uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.COMPOUNDER) live nonReentrant {
        _deadline(deadline);
        _active(id);
        _harvest(id, deadline);
        (uint256 amount0, uint256 amount1) = _pullCompound(id);
        if (amount0 + amount1 == 0 || minimumLiquidity == 0) revert InvalidAmount();
        uint256 beforeValue = _idleValue(id);
        _balanceUsing(id, deadline, true);
        // A same-pool swap can itself generate fees for this still-active LP.
        // Settle them separately before INCREASE so they cannot become principal.
        _harvest(id, deadline);
        if (_idleValue(id) < Math.mulDiv(beforeValue, 10000 - _pool(id).maxSlippageBps, 10000)) revert Slippage();
        _put(id, false, minimumLiquidity, deadline);
        emit Compounded(id, amount0, amount1);
    }
    function _close(uint256 id, uint256 deadline) private {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        uint256 before0 = _tokenBalance(c.key.currency0);
        uint256 before1 = _tokenBalance(c.key.currency1);
        IZZZLiquidity(_moduleLiquidity()).close(p.poolId, p.lpTokenId, deadline);
        p.lpTokenId = 0;
        _idle(id, p.idle0 + _tokenBalance(c.key.currency0) - before0,
            p.idle1 + _tokenBalance(c.key.currency1) - before1);
    }
    function _balance(uint256 id, uint256 deadline) private { _balanceUsing(id, deadline, false); }
    function _balanceUsing(uint256 id, uint256 deadline, bool existingRange) private {
        Position storage p = positions[id];
        PoolConfig memory c = _pool(id);
        IZZZStrategy strategy = IZZZStrategy(_moduleStrategy());
        bool zeroForOne;
        uint256 amountIn;
        uint256 minimumOut;
        if (existingRange) (zeroForOne, amountIn, minimumOut) = strategy.compoundPlan(id, p.idle0, p.idle1);
        else (zeroForOne, amountIn, minimumOut) = strategy.swapPlan(p.poolId, p.idle0, p.idle1);
        if (amountIn == 0) return;
        address input = zeroForOne ? c.key.currency0 : c.key.currency1;
        address manager = _moduleLiquidity();
        IERC20(input).forceApprove(manager, amountIn);
        uint256 amountOut = IZZZLiquidity(manager).swap(p.poolId, zeroForOne, amountIn, minimumOut, deadline);
        IERC20(input).forceApprove(manager, 0);
        if (zeroForOne) _idle(id, p.idle0 - amountIn, p.idle1 + amountOut);
        else _idle(id, p.idle0 + amountOut, p.idle1 - amountIn);
    }
    function _idleValue(uint256 id) private view returns (uint256) {
        PoolConfig memory c = _pool(id);
        Position storage p = positions[id];
        return _valuePair(c, p.idle0, p.idle1);
    }
    function _unwind(uint256 id, uint256 deadline) private {
        IZZZStrategy(_moduleStrategy()).validateExitPrice(positions[id].poolId);
        _harvest(id, deadline);
        _pullCompound(id);
        _close(id, deadline);
    }
    function _redeploy(uint256 id, uint128 minimumLiquidity, uint256 deadline) private {
        uint256 beforeValue = _idleValue(id);
        _balance(id, deadline);
        if (_idleValue(id) < Math.mulDiv(beforeValue, 10000 - _pool(id).maxSlippageBps, 10000)) revert Slippage();
        _put(id, true, minimumLiquidity, deadline);
    }
    function rebalance(uint256 id, uint128 minimumLiquidity, uint256 deadline) external onlyKeeper live nonReentrant {
        _deadline(deadline);
        _active(id);
        if (minimumLiquidity == 0 || !IZZZStrategy(_moduleStrategy()).needsRebalance(id)) revert InvalidState();
        Position storage p = positions[id];
        uint256 oldId = p.lpTokenId;
        _unwind(id, deadline);
        _redeploy(id, minimumLiquidity, deadline);
        emit Rebalanced(id, oldId, p.lpTokenId, p.centerX96);
    }
    function releaseForMigration(uint256 id, bytes32 migrationId, uint256 deadline)
        external onlyModule(Ids.MIGRATION) live nonReentrant returns (uint256 amount0, uint256 amount1) {
        _deadline(deadline);
        Position storage p = positions[id];
        if (!IZZZFees(_moduleFees()).remoteSettled(id)) revert InvalidState();
        if (p.status == PositionStatus.Parked) _pullCompound(id);
        else { _active(id); _unwind(id, deadline); }
        PoolConfig memory c = _pool(id);
        amount0 = p.idle0;
        amount1 = p.idle1;
        _idle(id, 0, 0);
        p.status = PositionStatus.Outbound;
        IZZZFees(_moduleFees()).flushDust(id, c.key.currency0);
        IZZZFees(_moduleFees()).flushDust(id, c.key.currency1);
        ExactToken.push(c.key.currency0, msg.sender, amount0);
        ExactToken.push(c.key.currency1, msg.sender, amount1);
        emit PrincipalBridged(id, migrationId, amount0, amount1);
    }
    function importPending(uint256 id, bytes32 poolId, Position calldata origin, uint256 shares, bytes32 homePool, uint256 amount0, uint256 amount1)
        external onlyModule(Ids.RECEIVER) nonReentrant {
        if (id != uint256(keccak256(abi.encode(origin.homeChain, origin.homeVault, homePool))) ||
            shares == 0 || shares > MAX_SHARES || poolBucket[poolId] != id) revert InvalidState();
        Position storage p = positions[id];
        bool returning = p.status == PositionStatus.Remote;
        if ((!returning && p.status != PositionStatus.None) || origin.homeChain != canonicalChainId ||
            origin.homeVault == address(0) || origin.homeReceiver == address(0)) revert InvalidState();
        if (returning && (p.lpTokenId != 0 || p.idle0 != 0 || p.idle1 != 0 || p.homeChain != origin.homeChain ||
            p.homeVault != origin.homeVault || p.homeReceiver != origin.homeReceiver || homePoolId[id] != homePool)) revert InvalidState();
        if (origin.homeChain == block.chainid && (!returning || origin.homeVault != address(this))) revert InvalidState();
        if (origin.homeChain == block.chainid &&
            (bucketTotalShares[id] != shares || p.depositUSD != origin.depositUSD)) revert InvalidState();
        if (!returning) _registerBucket(id);
        bucketTotalShares[id] = shares; homePoolId[id] = homePool;
        PoolConfig memory c = IZZZPools(_modulePools()).accounting(poolId);
        p.poolId = poolId;
        p.homeChain = origin.homeChain;
        p.homeVault = origin.homeVault;
        p.homeReceiver = origin.homeReceiver;
        p.homeToken0 = origin.homeToken0;
        p.homeToken1 = origin.homeToken1;
        p.depositUSD = origin.depositUSD;
        p.locationChain = block.chainid;
        p.locationVault = address(this);
        p.status = PositionStatus.Inbound;
        ExactToken.pull(c.key.currency0, msg.sender, amount0);
        ExactToken.pull(c.key.currency1, msg.sender, amount1);
        _idle(id, amount0, amount1);
        emit ImportPending(id, p.homeChain, p.homeVault);
    }
    function finalizeImport(uint256 id, uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.RECEIVER) live nonReentrant {
        _deadline(deadline);
        if (positions[id].status != PositionStatus.Inbound || minimumLiquidity == 0) revert InvalidState();
        _redeploy(id, minimumLiquidity, deadline);
        positions[id].status = PositionStatus.Active;
        emit ImportFinalized(id, positions[id].lpTokenId);
    }
    function confirmMigration(uint256 id, uint256 destinationChain, address destinationVault)
        external onlyModule(Ids.MIGRATION) {
        Position storage p = positions[id];
        if (p.status != PositionStatus.Outbound && p.status != PositionStatus.Remote) revert InvalidState();
        p.status = PositionStatus.Remote;
        p.locationChain = destinationChain;
        p.locationVault = destinationVault;
        emit LocationConfirmed(id, destinationChain, destinationVault);
    }

    /// @notice Only the fixed Migration module can park an LP. Its timelocked
    /// request binds exact custody and raw close minimums. No assets leave Vault.
    function park(uint256 id, uint256 deadline) external onlyModule(Ids.MIGRATION) nonReentrant {
        _deadline(deadline); _active(id);
        if (!access.paused() || positions[id].lpTokenId == 0) revert InvalidState();
        uint256 oldLp = positions[id].lpTokenId;
        _harvestVenue(id, deadline);
        _close(id, deadline);
        positions[id].status = PositionStatus.Parked;
        emit PrincipalParked(id, oldLp);
    }
    function resume(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.MIGRATION) live nonReentrant {
        _deadline(deadline);
        if (positions[id].status != PositionStatus.Parked) revert InvalidState();
        _movePool(id, newPool, minimumLiquidity, deadline);
        positions[id].status = PositionStatus.Active;
    }
    function movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline)
        external onlyModule(Ids.MIGRATION) live nonReentrant {
        _deadline(deadline);
        _active(id);
        if (positions[id].poolId == newPool) revert InvalidConfiguration();
        _movePool(id, newPool, minimumLiquidity, deadline);
    }
    function _movePool(uint256 id, bytes32 newPool, uint128 minimumLiquidity, uint256 deadline) private {
        Position storage p = positions[id];
        PoolConfig memory oldConfig = _pool(id);
        PoolConfig memory nextConfig = IZZZPools(_modulePools()).accounting(newPool);
        if (minimumLiquidity == 0 || oldConfig.key.currency0 != nextConfig.key.currency0 ||
            oldConfig.key.currency1 != nextConfig.key.currency1 || !nextConfig.operationsEnabled) revert InvalidConfiguration();
        _reserve(newPool, id);
        uint256 oldId = p.lpTokenId;
        if (p.status == PositionStatus.Parked) _pullCompound(id);
        else _unwind(id, deadline);
        p.poolId = newPool; // Both pool keys have the exact same ordered currencies.
        _redeploy(id, minimumLiquidity, deadline);
        emit Rebalanced(id, oldId, p.lpTokenId, p.centerX96);
    }
    function onERC721Received(address, address, uint256, bytes calldata) external view override returns (bytes4) {
        address manager = _moduleLiquidity();
        if (manager == address(0) || msg.sender != IZZZLiquidity(manager).positionManager()) revert Unauthorized();
        return IERC721Receiver.onERC721Received.selector;
    }
    // No withdraw, rescue-token, arbitrary execution, proxy upgrade or admin NFT transfer.
    function _modulePools() private view returns (address) { return access.module(Ids.POOLS); }
    function _moduleLiquidity() private view returns (address) { return access.module(Ids.LIQUIDITY); }
    function _moduleStrategy() private view returns (address) { return access.module(Ids.STRATEGY); }
    function _moduleFees() private view returns (address) { return access.module(Ids.FEES); }
}
