// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig, Route, BridgeMessage, MessageKind} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ZZZRewardReceiver} from "./ZZZRewardReceiver.sol";
import {IZZZRewards, IZZZVault, IZZZPools, IZZZRoutes, IZZZBridge} from "./interfaces/IZZZ.sol";

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
    event FeesAllocated(uint256 indexed bucketId, address indexed token, uint256 distributed, uint256 carriedDust);
    event RemoteRewardsSent(uint256 indexed bucketId, address indexed token, uint256 amount, bytes32 transportId);
    event RemoteAssetBound(uint256 indexed bucketId, address indexed token, address indexed canonicalToken);
    event RemoteAccountingImported(uint256 indexed bucketId, address indexed canonicalToken, uint256 individual, uint256 collective, bool canonical);
    event MembershipDustSettled(uint256 indexed bucketId, address indexed token, uint256 amount);
    event RewardReceiverCreated(uint256 indexed bucketId, address indexed receiver, address token0, address token1, address wrappedNative);
    event ExternalRewardsFunded(uint256 indexed bucketId, address indexed token, uint256 amount);
    constructor(address controller) ZZZModule(controller) {}
    function rewardReceiverCount() external view returns (uint256) { return rewardReceivers.length; }
    /// @notice Append-only funding destination. Governance cannot replace it or sweep payments.
    function createRewardReceiver(uint256 id, address wrapper) external onlyGovernance nonReentrant returns (address receiver) {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(id);
        IZZZRewards rewards = IZZZRewards(access.module(Ids.REWARDS));
        if (!access.isSealed() || rewardReceiver[id] != address(0) || rewardReceivers.length == MAX_REWARD_RECEIVERS ||
            p.status != PositionStatus.Active || p.homeChain != block.chainid || p.homeVault != address(vault) ||
            vault.bucketTotalShares(id) == 0 || !rewards.isAsset(p.homeToken0) || !rewards.isAsset(p.homeToken1)) {
            revert InvalidConfiguration();
        }
        receiver = address(new ZZZRewardReceiver(id, p.homeToken0, p.homeToken1, wrapper));
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
    /// @notice Bounded global settlement protects the 30% global Power index before entry.
    function syncAllExternal() external onlyModule(Ids.VAULT) {
        for (uint256 i; i < rewardReceivers.length; ++i) {
            ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(rewardReceivers[i]));
            receiver.sync();
            // Old sub-ten-unit dust must not cross a global Power membership change.
            _flushHomeDust(receiver.bucketId(), receiver.token0());
            _flushHomeDust(receiver.bucketId(), receiver.token1());
        }
    }
    /// @notice Final entry barrier also catches dust queued by nested callbacks.
    function hasPendingExternal() external view returns (bool) {
        for (uint256 i; i < rewardReceivers.length; ++i) {
            ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(rewardReceivers[i]));
            (uint256 a0, uint256 a1) = receiver.pending();
            uint256 id = receiver.bucketId();
            if (a0 != 0 || a1 != 0 || dust[id][receiver.token0()] != 0 || dust[id][receiver.token1()] != 0) return true;
        }
        return false;
    }
    function allocateExternal(uint256 id, address token, uint256 amount) external nonReentrant {
        if (rewardReceiver[id] == address(0) || msg.sender != rewardReceiver[id]) revert Unauthorized();
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(id);
        if (!access.isSealed() || amount == 0 || p.status == PositionStatus.None || p.status == PositionStatus.Dormant ||
            p.homeChain != block.chainid || p.homeVault != address(vault) || vault.bucketTotalShares(id) == 0 ||
            (token != p.homeToken0 && token != p.homeToken1)) revert InvalidState();
        ExactToken.pull(token, msg.sender, amount);
        totalExternalFunded[id][token] += amount;
        _distribute(id, token, amount, true);
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
    function bindRemoteAsset(uint256 id, address token, address canonicalToken) external onlyModule(Ids.RECEIVER) {
        _bindRemoteAsset(id, token, canonicalToken);
    }
    function _credit(uint256 id, address token, uint256 personal, uint256 shared) private {
        address rewards = access.module(Ids.REWARDS);
        IERC20(token).forceApprove(rewards, personal + shared);
        IZZZRewards(rewards).creditPool(id, token, personal, shared);
        IERC20(token).forceApprove(rewards, 0);
    }
    function _solvent(address token) private view {
        if (IERC20(token).balanceOf(address(this)) < accounted[token]) revert InvalidState();
    }
    function allocate(uint256 id, address token, uint256 amount) external onlyModule(Ids.VAULT) nonReentrant {
        if (amount == 0) revert InvalidAmount();
        Position memory p = IZZZVault(msg.sender).group(id);
        if (p.status != PositionStatus.Active) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(p.poolId);
        if (token != c.key.currency0 && token != c.key.currency1) revert InvalidConfiguration();
        bool canonical = p.homeChain == block.chainid && p.homeVault == msg.sender;
        if (!canonical) {
            _bindRemoteAsset(id, token, token == c.key.currency0 ? p.homeToken0 : p.homeToken1);
        }
        ExactToken.pull(token, msg.sender, amount);
        _distribute(id, token, amount, canonical);
    }
    function _distribute(uint256 id, address token, uint256 amount, bool canonical) private {
        accounted[token] += amount;
        uint256 total = dust[id][token] + amount;
        uint256 units = total / 10;
        dust[id][token] = total % 10;
        if (units != 0) {
            compoundBalance[id][token] += units;
            buybackBalance[token] += units;
            if (canonical) {
                accounted[token] -= units * 8;
                _credit(id, token, units * 5, units * 3);
            } else {
                remoteIndividual[id][token] += units * 5;
                remoteCollective[id][token] += units * 3;
                address canonicalToken = remoteCanonicalToken[id][token];
                allocatedPersonal[id][canonicalToken] += units * 5;
                allocatedShared[id][canonicalToken] += units * 3;
            }
        }
        _solvent(token);
        emit FeesAllocated(id, token, units * 10, dust[id][token]);
    }
    function flushDust(uint256 id, address token) external onlyModule(Ids.VAULT) nonReentrant {
        Position memory p = IZZZVault(msg.sender).group(id);
        if (p.status != PositionStatus.Outbound && p.status != PositionStatus.Active) revert InvalidState();
        uint256 remainder = dust[id][token];
        if (remainder == 0) return;
        if (p.homeChain == block.chainid && p.homeVault == msg.sender) {
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
        external onlyModule(Ids.VAULT) nonReentrant returns (uint256 amount) {
        amount = compoundBalance[id][token];
        compoundBalance[id][token] = 0;
        accounted[token] -= amount;
        ExactToken.push(token, msg.sender, amount);
        _solvent(token);
    }
    function releaseBuyback(address token, uint256 amount) external onlyModule(Ids.BUYBACK) nonReentrant {
        if (amount == 0 || amount > buybackBalance[token]) revert InvalidAmount();
        buybackBalance[token] -= amount;
        accounted[token] -= amount;
        ExactToken.push(token, msg.sender, amount);
        _solvent(token);
    }
    function bridgeRewards(uint256 id, address token, bytes32 routeId) external payable live nonReentrant {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(id);
        if (p.homeChain == block.chainid || (p.status != PositionStatus.Active && p.status != PositionStatus.Outbound &&
            p.status != PositionStatus.Remote && p.status != PositionStatus.Inbound)) revert InvalidState();
        address homeToken = remoteCanonicalToken[id][token];
        if (homeToken == address(0)) revert InvalidConfiguration();
        (Route memory r, bool enabled) = IZZZRoutes(access.module(Ids.ROUTES)).get(routeId);
        if (!enabled || r.sourceVault != access.module(Ids.VAULT) || r.sourceChain != block.chainid ||
            r.destinationChain != p.homeChain || r.destinationVault != p.homeVault || r.destinationReceiver != p.homeReceiver ||
            r.sourceToken0 != token || r.destinationToken0 != homeToken || r.sourceToken1 != address(0) ||
            r.destinationToken1 != address(0)) revert InvalidConfiguration();
        uint256 personal = remoteIndividual[id][token];
        uint256 shared = remoteCollective[id][token];
        uint256 amount = personal + shared;
        if (amount == 0) revert InvalidAmount();
        remoteIndividual[id][token] = 0;
        remoteCollective[id][token] = 0;
        accounted[token] -= amount;
        BridgeMessage memory m;
        m.version = 3;
        m.kind = MessageKind.Reward;
        m.routeId = routeId;
        m.bucketId = id;
        m.homeChain = p.homeChain;
        m.homeVault = p.homeVault;
        m.homeReceiver = p.homeReceiver;
        m.homePoolId = vault.homePoolId(id);
        m.totalShares = vault.bucketTotalShares(id);
        m.depositUSD = p.depositUSD;
        m.amount0 = amount;
        m.individual = personal;
        m.collective = shared;
        m.canonicalToken0 = homeToken;
        address adapter = access.module(Ids.BRIDGE);
        IERC20(token).forceApprove(adapter, amount);
        bytes32 receipt = IZZZBridge(adapter).send{value: msg.value}(m);
        IERC20(token).forceApprove(adapter, 0);
        _solvent(token);
        emit RemoteRewardsSent(id, token, amount, receipt);
    }
    function creditRemote(uint256 id, address token, uint256 personal, uint256 shared)
        external onlyModule(Ids.RECEIVER) nonReentrant {
        if (personal + shared == 0) revert InvalidAmount();
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(id);
        if (p.homeChain != block.chainid || p.homeVault != access.module(Ids.VAULT) ||
            (token != p.homeToken0 && token != p.homeToken1)) revert InvalidConfiguration();
        ExactToken.pull(token, msg.sender, personal + shared);
        receivedIndividual[id][token] += personal;
        receivedCollective[id][token] += shared;
        _credit(id, token, personal, shared);
        _solvent(token);
    }
    function allocated(uint256 id, address canonicalToken) external view returns (uint256 personal, uint256 shared) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(id);
        if (p.homeChain == block.chainid && p.homeVault == access.module(Ids.VAULT)) {
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
    function importAccounting(BridgeMessage calldata m) external onlyModule(Ids.RECEIVER) {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(m.bucketId);
        if (m.version != 3 || m.kind != MessageKind.Principal || m.homeChain != p.homeChain ||
            m.homeVault != p.homeVault || m.canonicalToken0 == m.canonicalToken1 ||
            m.totalShares != vault.bucketTotalShares(m.bucketId) || m.totalShares == 0) revert InvalidConfiguration();
        bool canonical = p.homeChain == block.chainid && p.homeVault == address(vault);
        if ((m.canonicalToken0 != p.homeToken0 || m.canonicalToken1 != p.homeToken1) &&
            (m.canonicalToken0 != p.homeToken1 || m.canonicalToken1 != p.homeToken0)) revert InvalidConfiguration();
        _importAccounting(m.bucketId, m.canonicalToken0, m.allocatedIndividual0, m.allocatedCollective0, canonical);
        _importAccounting(m.bucketId, m.canonicalToken1, m.allocatedIndividual1, m.allocatedCollective1, canonical);
    }
    function remoteSettled(uint256 id) external view returns (bool) {
        Position memory p = IZZZVault(access.module(Ids.VAULT)).group(id);
        if (p.status == PositionStatus.None || p.status == PositionStatus.Dormant) return false;
        if (p.homeChain != block.chainid || p.homeVault != access.module(Ids.VAULT)) return true;
        return receivedIndividual[id][p.homeToken0] >= expectedIndividual[id][p.homeToken0] &&
            receivedCollective[id][p.homeToken0] >= expectedCollective[id][p.homeToken0] &&
            receivedIndividual[id][p.homeToken1] >= expectedIndividual[id][p.homeToken1] &&
            receivedCollective[id][p.homeToken1] >= expectedCollective[id][p.homeToken1];
    }
    // Sub-10-unit fee dust settles to existing owners before membership changes
    // and departures, so no new share receives an old fee. This bounded raw-unit
    // rounding exception cannot be swept by an administrator.
    // No principal, reward liability or fee reserve can be swept by an administrator.
}
