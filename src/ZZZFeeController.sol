// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig, BridgeMessage, MessageKind} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ZZZRewardReceiver} from "./ZZZRewardReceiver.sol";
import {ZZZRewardReceiverFactory} from "./ZZZRewardReceiverFactory.sol";
import {IZZZAccess} from "./interfaces/IZZZ.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
import {IZZZRewards, IZZZVault, IZZZMembership, IZZZPools, IZZZBridge} from "./interfaces/IZZZ.sol";

interface ICanonicalFeeAssets { function assetCount() external view returns (uint256); function assets(uint256) external view returns (address); }
interface ICanonicalFeeCutoff {
    function creditCanonicalCutoff(uint256 id, address token, uint256 personal, uint256 shared) external;
}
interface ICanonicalFeeHandoff {
    function incomingSource() external view returns (address);
    function destinationController() external view returns (address);
}

contract ZZZFeeController is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    // Every id in this contract identifies a shared LP bucket, never one NFT.
    mapping(uint256 => mapping(address => uint256)) public dust;
    mapping(uint256 => mapping(address => uint256)) public compoundBalance;
    mapping(address => uint256) public buybackBalance;
    mapping(uint256 => mapping(address => uint256)) public remoteIndividual;
    mapping(uint256 => mapping(address => uint256)) public remoteCollective;
    // Canonical destinations for old reserves must survive pool changes and
    // further custody hops. Once bound, a local asset cannot change identity.
    mapping(uint256 => mapping(address => address)) public remoteCanonicalToken;
    mapping(address => uint256) public accounted;
    uint256 public constant MAX_REWARD_RECEIVERS = 16;
    mapping(uint256 => address) public rewardReceiver;
    address[] public rewardReceivers;
    mapping(uint256 => mapping(address => uint256)) public totalExternalFunded;
    // Lifetime counters use canonical token identities. They include allocated
    // but unsent remote reserves and are propagated through every custody hop.
    mapping(uint256 => mapping(address => uint256)) private allocatedPersonal;
    mapping(uint256 => mapping(address => uint256)) private allocatedShared;
    mapping(uint256 => mapping(address => uint256)) public receivedIndividual;
    mapping(uint256 => mapping(address => uint256)) public receivedCollective;
    mapping(uint256 => mapping(address => uint256)) public expectedIndividual;
    mapping(uint256 => mapping(address => uint256)) public expectedCollective;
    struct CanonicalBucket {
        uint256 id; address asset; uint256 dustAmount; uint256 compoundAmount;
        uint256 remotePersonal; uint256 remoteShared; address canonicalToken;
        uint256 externalFunded; uint256 allocatedPersonalAmount; uint256 allocatedSharedAmount;
        uint256 receivedPersonal; uint256 receivedShared; uint256 expectedPersonal; uint256 expectedShared;
    }
    mapping(uint256 => mapping(address => uint256)) public lateGross;
    mapping(address => uint256) private lateTotal;
    event FeesAllocated(uint256 indexed bucketId, address indexed token, uint256 distributed, uint256 carriedDust);
    event RemoteRewardsSent(uint256 indexed bucketId, address indexed token, uint256 amount, bytes32 transportId);
    event RemoteAssetBound(uint256 indexed bucketId, address indexed token, address indexed canonicalToken);
    event RemoteAccountingImported(uint256 indexed bucketId, address indexed canonicalToken, uint256 individual, uint256 collective, bool canonical);
    event MembershipDustSettled(uint256 indexed bucketId, address indexed token, uint256 amount);
    event RewardReceiverCreated(uint256 indexed bucketId, address indexed receiver, address token0, address token1, address wrappedNative);
    event ExternalRewardsFunded(uint256 indexed bucketId, address indexed token, uint256 amount);
    ZZZRewardReceiverFactory public immutable receiverFactory;
    constructor(address controller) ZZZModule(controller) { receiverFactory = new ZZZRewardReceiverFactory(controller); }
    receive() external payable {}
    function canonicalState() public view returns (uint8) { return IZZZCanonicalAccess(address(access)).canonicalState(); }
    function _vault() private view returns (IZZZVault) { return IZZZVault(access.module(Ids.VAULT)); }
    function _isHome(Position memory p, IZZZVault vault) private view returns (bool) {
        return p.homeChain == block.chainid && p.homeVault == address(vault);
    }
    function rewardReceiverCount() external view returns (uint256) { return rewardReceivers.length; }
    /// @notice Append-only funding destination. Governance cannot replace it or sweep payments.
    function createRewardReceiver(uint256 id, address wrapper) external onlyGovernance nonReentrant returns (address receiver) {
        IZZZVault vault = _vault();
        Position memory p = vault.group(id);
        IZZZRewards rewards = IZZZRewards(access.module(Ids.REWARDS));
        if (!access.isSealed() || rewardReceiver[id] != address(0) || rewardReceivers.length == MAX_REWARD_RECEIVERS ||
            (p.status != PositionStatus.Active && p.status != PositionStatus.Parked) || !_isHome(p, vault) ||
            vault.bucketTotalShares(id) == 0 || !rewards.isAsset(p.homeToken0) || !rewards.isAsset(p.homeToken1)) {
            revert InvalidConfiguration();
        }
        receiver = receiverFactory.create(id, p.homeToken0, p.homeToken1, wrapper);
        if (receiver == vault.mintProceedsRecipient()) revert InvalidConfiguration();
        rewardReceiver[id] = receiver;
        rewardReceivers.push(receiver);
        emit RewardReceiverCreated(id, receiver, p.homeToken0, p.homeToken1, wrapper);
    }
    /// @dev Dispatch has no guard: the immutable inbox calls the guarded allocator.
    function syncExternal(uint256 id) external {
        address receiver = rewardReceiver[id];
        if (receiver != address(0)) ZZZRewardReceiver(payable(receiver)).sync();
    }
    /// @notice Bounded global settlement protects collective membership before entry.
    function syncAllExternal() external onlyModule(Ids.VAULT) {
        IZZZMembership(access.module(Ids.MEMBERSHIP)).settleDust();
        for (uint256 i; i < rewardReceivers.length; ++i) {
            ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(rewardReceivers[i]));
            receiver.sync();
            // Old sub-twenty-unit dust must not cross a collective membership change.
            _flushHomeDust(receiver.bucketId(), receiver.token0());
            _flushHomeDust(receiver.bucketId(), receiver.token1());
        }
    }
    /// @notice Final entry barrier also catches dust queued by nested callbacks.
    function hasPendingExternal() external view returns (bool) { return receiverFactory.hasPendingExternal(); }
    function allocateExternal(uint256 id, address token, uint256 amount) external nonReentrant {
        if (rewardReceiver[id] == address(0) || msg.sender != rewardReceiver[id]) revert Unauthorized();
        IZZZVault vault = _vault();
        Position memory p = vault.group(id);
        if (!access.isSealed() || amount == 0 || p.status == PositionStatus.None || p.status == PositionStatus.Dormant ||
            !_isHome(p, vault) || vault.bucketTotalShares(id) == 0 ||
            (token != p.homeToken0 && token != p.homeToken1)) revert InvalidState();
        ExactToken.pull(token, msg.sender, amount);
        uint8 state = canonicalState();
        if (state == 3) { lateGross[id][token] += amount; lateTotal[token] += amount; return; }
        if (state != 0 && !(state == 1 && IZZZCanonicalAccess(address(access)).canonicalSettling())) revert InvalidState();
        totalExternalFunded[id][token] += amount;
        _distribute(id, token, amount, true);
        if (canonicalState() != state) revert InvalidState();
        emit ExternalRewardsFunded(id, token, amount);
    }
    function _bindRemoteAsset(uint256 id, address token, address canonicalToken) private {
        if (token == address(0) || canonicalToken == address(0)) revert InvalidConfiguration();
        address bound = remoteCanonicalToken[id][token];
        if (bound != address(0)) {
            if (bound != canonicalToken) revert InvalidConfiguration();
            return;
        }
        remoteCanonicalToken[id][token] = canonicalToken;
        emit RemoteAssetBound(id, token, canonicalToken);
    }
    function bindRemoteAsset(uint256 id, address token, address canonicalToken) external onlyModule(Ids.RECEIVER) canonicalAccounting {
        _bindRemoteAsset(id, token, canonicalToken);
    }
    function _credit(uint256 id, address token, uint256 personal, uint256 shared) private {
        address rewards = access.module(Ids.REWARDS);
        IERC20(token).forceApprove(rewards, personal + shared);
        if (canonicalState() == 1) {
            if (!IZZZCanonicalAccess(address(access)).canonicalSettling()) revert InvalidState();
            ICanonicalFeeCutoff(rewards).creditCanonicalCutoff(id, token, personal, shared);
        } else IZZZRewards(rewards).creditPool(id, token, personal, shared);
        IERC20(token).forceApprove(rewards, 0);
    }
    function _solvent(address token) private view {
        if (IERC20(token).balanceOf(address(this)) < accounted[token] + lateTotal[token]) revert InvalidState();
    }
    function allocate(uint256 id, address token, uint256 amount) external onlyModule(Ids.VAULT) nonReentrant canonicalAccounting {
        if (amount == 0) revert InvalidAmount();
        Position memory p = IZZZVault(msg.sender).group(id);
        if (p.status != PositionStatus.Active) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(p.poolId);
        if (token != c.key.currency0 && token != c.key.currency1) revert InvalidConfiguration();
        bool canonical = _isHome(p, IZZZVault(msg.sender));
        if (!canonical) {
            _bindRemoteAsset(id, token, token == c.key.currency0 ? p.homeToken0 : p.homeToken1);
        }
        ExactToken.pull(token, msg.sender, amount);
        _distribute(id, token, amount, canonical);
    }
    function _distribute(uint256 id, address token, uint256 amount, bool canonical) private {
        accounted[token] += amount;
        uint256 total = dust[id][token] + amount;
        // Twenty raw token units allocate exactly 80/10/5/5 without per-call
        // rounding changing the split. Carry smaller receipts until settlement.
        uint256 units = total / 20;
        dust[id][token] = total % 20;
        if (units != 0) {
            compoundBalance[id][token] += units;
            buybackBalance[token] += units;
            if (canonical) {
                accounted[token] -= units * 18;
                _credit(id, token, units * 16, units * 2);
            } else {
                remoteIndividual[id][token] += units * 16;
                remoteCollective[id][token] += units * 2;
                address canonicalToken = remoteCanonicalToken[id][token];
                allocatedPersonal[id][canonicalToken] += units * 16;
                allocatedShared[id][canonicalToken] += units * 2;
            }
        }
        _solvent(token);
        emit FeesAllocated(id, token, units * 20, dust[id][token]);
    }
    function flushDust(uint256 id, address token) external nonReentrant canonicalAccounting {
        IZZZVault vault = _vault();
        bool membership = msg.sender == access.module(Ids.MEMBERSHIP);
        if (!access.isSealed() || (msg.sender != address(vault) && !membership)) revert Unauthorized();
        Position memory p = vault.group(id);
        bool canonical = _isHome(p, vault);
        if (membership && !canonical) revert Unauthorized();
        if (p.status != PositionStatus.Outbound && p.status != PositionStatus.Active &&
            p.status != PositionStatus.Parked) revert InvalidState();
        uint256 remainder = dust[id][token];
        if (remainder == 0) return;
        if (canonical) {
            _flushHomeDust(id, token);
            return;
        } else {
            if (remoteCanonicalToken[id][token] == address(0)) revert InvalidConfiguration();
            dust[id][token] = 0;
            // Keep the funded reserve here until it is delivered home; flushing
            // at a satellite does not turn dust into local canonical rewards.
            remoteIndividual[id][token] += remainder;
            allocatedPersonal[id][remoteCanonicalToken[id][token]] += remainder;
        }
        _solvent(token);
        emit MembershipDustSettled(id, token, remainder);
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
        external onlyModule(Ids.VAULT) nonReentrant canonicalAccounting returns (uint256 amount) {
        amount = compoundBalance[id][token];
        compoundBalance[id][token] = 0;
        accounted[token] -= amount;
        ExactToken.push(token, msg.sender, amount);
        _solvent(token);
    }
    function releaseBuyback(address token, uint256 amount) external onlyModule(Ids.BUYBACK) nonReentrant canonicalAccounting {
        if (amount == 0 || amount > buybackBalance[token]) revert InvalidAmount();
        buybackBalance[token] -= amount;
        accounted[token] -= amount;
        ExactToken.push(token, msg.sender, amount);
        _solvent(token);
    }
    function bridgeRewards(uint256 id, address token, bytes32 routeId) external payable live nonReentrant canonicalAccounting {
        BridgeMessage memory m = receiverFactory.rewardMessage(id, token, routeId);
        uint256 amount = m.amount0;
        remoteIndividual[id][token] = 0;
        remoteCollective[id][token] = 0;
        accounted[token] -= amount;
        address adapter = access.module(Ids.BRIDGE);
        IERC20(token).forceApprove(adapter, amount);
        bytes32 receipt = IZZZBridge(adapter).send{value: msg.value}(m);
        IERC20(token).forceApprove(adapter, 0);
        _solvent(token);
        emit RemoteRewardsSent(id, token, amount, receipt);
    }
    function creditRemote(uint256 id, address token, uint256 personal, uint256 shared)
        external onlyModule(Ids.RECEIVER) nonReentrant canonicalAccounting {
        if (personal + shared == 0) revert InvalidAmount();
        IZZZVault vault = _vault();
        Position memory p = vault.group(id);
        if (!_isHome(p, vault) ||
            (token != p.homeToken0 && token != p.homeToken1)) revert InvalidConfiguration();
        ExactToken.pull(token, msg.sender, personal + shared);
        receivedIndividual[id][token] += personal;
        receivedCollective[id][token] += shared;
        _credit(id, token, personal, shared);
        _solvent(token);
    }
    function allocated(uint256 id, address canonicalToken) external view returns (uint256 personal, uint256 shared) {
        IZZZVault vault = _vault();
        Position memory p = vault.group(id);
        if (_isHome(p, vault)) {
            return (receivedIndividual[id][canonicalToken], receivedCollective[id][canonicalToken]);
        }
        return (allocatedPersonal[id][canonicalToken], allocatedShared[id][canonicalToken]);
    }
    function _importAccounting(uint256 id, address token, uint256 personal, uint256 shared, bool canonical) private {
        if (token == address(0)) revert InvalidConfiguration();
        if (canonical) {
            if (personal < expectedIndividual[id][token] || shared < expectedCollective[id][token]) revert InvalidState();
            expectedIndividual[id][token] = personal;
            expectedCollective[id][token] = shared;
        } else {
            if (personal < allocatedPersonal[id][token] || shared < allocatedShared[id][token]) revert InvalidState();
            allocatedPersonal[id][token] = personal;
            allocatedShared[id][token] = shared;
        }
        emit RemoteAccountingImported(id, token, personal, shared, canonical);
    }
    function importAccounting(BridgeMessage calldata m) external onlyModule(Ids.RECEIVER) canonicalAccounting {
        IZZZVault vault = _vault();
        Position memory p = vault.group(m.bucketId);
        if (m.version != 3 || m.kind != MessageKind.Principal || m.homeChain != p.homeChain ||
            m.homeVault != p.homeVault || m.canonicalToken0 == m.canonicalToken1 ||
            m.totalShares != vault.bucketTotalShares(m.bucketId) || m.totalShares == 0) revert InvalidConfiguration();
        bool canonical = _isHome(p, vault);
        if ((m.canonicalToken0 != p.homeToken0 || m.canonicalToken1 != p.homeToken1) &&
            (m.canonicalToken0 != p.homeToken1 || m.canonicalToken1 != p.homeToken0)) revert InvalidConfiguration();
        _importAccounting(m.bucketId, m.canonicalToken0, m.allocatedIndividual0, m.allocatedCollective0, canonical);
        _importAccounting(m.bucketId, m.canonicalToken1, m.allocatedIndividual1, m.allocatedCollective1, canonical);
    }
    function remoteSettled(uint256 id) external view returns (bool) {
        IZZZVault vault = _vault();
        Position memory p = vault.group(id);
        if (p.status == PositionStatus.None || p.status == PositionStatus.Dormant) return false;
        if (!_isHome(p, vault)) return true;
        return _remoteFunded(id, p.homeToken0) && _remoteFunded(id, p.homeToken1);
    }
    function _remoteFunded(uint256 id, address token) private view returns (bool) {
        return receivedIndividual[id][token] >= expectedIndividual[id][token] &&
            receivedCollective[id][token] >= expectedCollective[id][token];
    }

    /// @notice One-hop, exact, unsplit receipt forwarding. Later successors can
    /// queue and forward again without recursion or applying allocation twice.
    function forwardLate(uint256 id, address token) external nonReentrant {
        if (canonicalState() != 3) revert InvalidState();
        uint256 amount = lateGross[id][token];
        if (amount == 0) revert InvalidAmount();
        address nextController = ICanonicalFeeHandoff(IZZZCanonicalAccess(address(access)).canonicalHandoff()).destinationController();
        address nextFees = IZZZAccess(nextController).module(Ids.FEES);
        lateGross[id][token] = 0; lateTotal[token] -= amount;
        IERC20(token).forceApprove(nextFees, amount);
        ZZZFeeController(payable(nextFees)).acceptLegacyGross(id, token, amount);
        IERC20(token).forceApprove(nextFees, 0);
    }
    function acceptLegacyGross(uint256 id, address token, uint256 amount) external nonReentrant {
        uint8 state = canonicalState();
        address source = ICanonicalFeeHandoff(IZZZCanonicalAccess(address(access)).canonicalHandoff()).incomingSource();
        if (source == address(0) || msg.sender != IZZZAccess(source).module(Ids.FEES) || amount == 0) revert Unauthorized();
        Position memory p = _vault().group(id);
        if ((token != p.homeToken0 && token != p.homeToken1) || _vault().bucketTotalShares(id) == 0) revert InvalidConfiguration();
        ExactToken.pull(token, msg.sender, amount);
        if (canonicalState() != state) revert InvalidState();
        if (state == 0) {
            totalExternalFunded[id][token] += amount;
            _distribute(id, token, amount, true);
        } else { lateGross[id][token] += amount; lateTotal[token] += amount; }
        if (canonicalState() != state) revert InvalidState();
    }
    function processLate(uint256 id, address token) external nonReentrant canonicalAccounting {
        uint256 amount = lateGross[id][token];
        if (amount == 0) revert InvalidAmount();
        lateGross[id][token] = 0; lateTotal[token] -= amount;
        totalExternalFunded[id][token] += amount;
        _distribute(id, token, amount, true);
    }
    function canonicalModule() public view returns (address) { return access.module(Ids.FEES_CANONICAL); }
    modifier onlyCanonical() { if (msg.sender != canonicalModule()) revert Unauthorized(); _; }
    function canonicalCaptureReceivers() external onlyCanonical nonReentrant {
        for (uint256 i; i < rewardReceivers.length; ++i) ZZZRewardReceiver(payable(rewardReceivers[i])).canonicalCapture();
    }
    function canonicalSettleReceivers() external onlyCanonical {
        for (uint256 i; i < rewardReceivers.length; ++i) ZZZRewardReceiver(payable(rewardReceivers[i])).canonicalSettle();
    }
    function canonicalFlush(uint256 id, address asset) external onlyCanonical { _flushHomeDust(id, asset); }
    function canonicalLateTotal(address asset) external view returns (uint256) { return lateTotal[asset]; }
    function canonicalBucketRecord(uint256 id, address asset) external view returns (bytes memory) {
        return abi.encode(CanonicalBucket(id, asset, dust[id][asset], compoundBalance[id][asset], remoteIndividual[id][asset],
            remoteCollective[id][asset], remoteCanonicalToken[id][asset], totalExternalFunded[id][asset],
            allocatedPersonal[id][asset], allocatedShared[id][asset], receivedIndividual[id][asset],
            receivedCollective[id][asset], expectedIndividual[id][asset], expectedCollective[id][asset]));
    }
    function canonicalWrite(uint8 kind, bytes calldata record) external onlyCanonical {
        if (canonicalState() != 2) revert InvalidState();
        if (kind == 0) {
            (address asset, uint256 total, uint256 buyback,,) = abi.decode(record, (address,uint256,uint256,uint256,uint256));
            if (accounted[asset] != 0 || buybackBalance[asset] != 0) revert InvalidState();
            accounted[asset] = total; buybackBalance[asset] = buyback;
        } else if (kind == 1) {
            CanonicalBucket memory r = abi.decode(record, (CanonicalBucket));
            dust[r.id][r.asset] = r.dustAmount; compoundBalance[r.id][r.asset] = r.compoundAmount;
            remoteIndividual[r.id][r.asset] = r.remotePersonal; remoteCollective[r.id][r.asset] = r.remoteShared;
            remoteCanonicalToken[r.id][r.asset] = r.canonicalToken; totalExternalFunded[r.id][r.asset] = r.externalFunded;
            allocatedPersonal[r.id][r.asset] = r.allocatedPersonalAmount; allocatedShared[r.id][r.asset] = r.allocatedSharedAmount;
            receivedIndividual[r.id][r.asset] = r.receivedPersonal; receivedCollective[r.id][r.asset] = r.receivedShared;
            expectedIndividual[r.id][r.asset] = r.expectedPersonal; expectedCollective[r.id][r.asset] = r.expectedShared;
        } else if (kind == 2) {
            (uint256 id, address t0, address t1, address wrapper, uint256 p0, uint256 p1, uint256 pn) =
                abi.decode(record, (uint256,address,address,address,uint256,uint256,uint256));
            if (rewardReceiver[id] != address(0)) revert InvalidState();
            ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(receiverFactory.create(id, t0, t1, wrapper)));
            receiver.canonicalProtection(p0, p1, pn);
            rewardReceiver[id] = address(receiver); rewardReceivers.push(address(receiver));
        } else revert InvalidState();
    }
    function canonicalSend(address asset, uint256 receiver, uint8 slot, address destination, uint256 amount)
        external onlyCanonical nonReentrant {
        if (receiver == type(uint256).max) ExactToken.push(asset, destination, amount);
        else ZZZRewardReceiver(payable(rewardReceivers[receiver])).canonicalRelease(slot, destination, amount);
    }
    function canonicalFundReceiver(uint256 receiverIndex, uint8 slot, uint256 amount, bool restore)
        external payable onlyCanonical {
        ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(rewardReceivers[receiverIndex]));
        if (slot == 2) {
            if (msg.value != amount) revert InvalidAmount();
            receiver.canonicalNative{value: amount}();
        } else if (msg.value != 0) revert InvalidAmount();
        if (restore) receiver.canonicalProtection(slot == 0 ? amount : 0, slot == 1 ? amount : 0, slot == 2 ? amount : 0);
    }
    function canonicalQuarantineReceivers() external onlyCanonical {
        for (uint256 i; i < rewardReceivers.length; ++i) ZZZRewardReceiver(payable(rewardReceivers[i])).canonicalQuarantinePending();
    }
    // Sub-20-unit fee dust settles to existing owners before membership changes
    // and departures, so no new share receives an old fee. This bounded raw-unit
    // rounding exception cannot be swept by an administrator.
    // No principal, reward liability or fee reserve can be swept by an administrator.
}

