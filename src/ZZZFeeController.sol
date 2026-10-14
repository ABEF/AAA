// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Position, PositionStatus, PoolConfig, Route, BridgeMessage, MessageKind} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {IZZZRewards, IZZZVault, IZZZPools, IZZZRoutes, IZZZBridge} from "./interfaces/IZZZ.sol";

contract ZZZFeeController is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    mapping(uint256 => mapping(address => uint256)) public dust;
    mapping(uint256 => mapping(address => uint256)) public compoundBalance;
    mapping(address => uint256) public buybackBalance;
    mapping(uint256 => mapping(address => uint256)) public remoteIndividual;
    mapping(uint256 => mapping(address => uint256)) public remoteCollective;
    // Canonical destinations for old reserves must survive pool changes and
    // further custody hops. Once bound, a local asset cannot change identity.
    mapping(uint256 => mapping(address => address)) public remoteCanonicalToken;
    mapping(address => uint256) public accounted;
    event FeesAllocated(uint256 indexed nftId, address indexed token, uint256 distributed, uint256 carriedDust);
    event RemoteRewardsSent(uint256 indexed nftId, address indexed token, uint256 amount, bytes32 transportId);
    event RemoteAssetBound(uint256 indexed nftId, address indexed token, address indexed canonicalToken);
    constructor(address controller) ZZZModule(controller) {}
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
        IZZZRewards(rewards).credit(id, token, personal, shared);
        IERC20(token).forceApprove(rewards, 0);
    }
    function _solvent(address token) private view {
        if (IERC20(token).balanceOf(address(this)) < accounted[token]) revert InvalidState();
    }
    function allocate(uint256 id, address token, uint256 amount) external onlyModule(Ids.VAULT) nonReentrant {
        if (amount == 0) revert InvalidAmount();
        Position memory p = IZZZVault(msg.sender).position(id);
        if (p.status != PositionStatus.Active) revert InvalidState();
        PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).get(p.poolId);
        if (token != c.key.currency0 && token != c.key.currency1) revert InvalidConfiguration();
        bool canonical = p.homeChain == block.chainid && p.homeVault == msg.sender;
        if (!canonical) {
            _bindRemoteAsset(id, token, token == c.key.currency0 ? p.homeToken0 : p.homeToken1);
        }
        ExactToken.pull(token, msg.sender, amount);
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
            }
        }
        _solvent(token);
        emit FeesAllocated(id, token, units * 10, dust[id][token]);
    }
    function flushDust(uint256 id, address token) external onlyModule(Ids.VAULT) nonReentrant {
        Position memory p = IZZZVault(msg.sender).position(id);
        if (p.status != PositionStatus.Outbound) revert InvalidState();
        uint256 remainder = dust[id][token];
        if (remainder == 0) return;
        dust[id][token] = 0;
        if (p.homeChain == block.chainid && p.homeVault == msg.sender) {
            accounted[token] -= remainder;
            _credit(id, token, remainder, 0);
        } else {
            if (remoteCanonicalToken[id][token] == address(0)) revert InvalidConfiguration();
            // Keep the funded reserve here until it is delivered home; flushing
            // at a satellite does not turn dust into local canonical rewards.
            remoteIndividual[id][token] += remainder;
        }
        _solvent(token);
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
        Position memory p = IZZZVault(access.module(Ids.VAULT)).position(id);
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
        m.version = 2;
        m.kind = MessageKind.Reward;
        m.routeId = routeId;
        m.nftId = id;
        m.homeChain = p.homeChain;
        m.homeVault = p.homeVault;
        m.homeReceiver = p.homeReceiver;
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
        ExactToken.pull(token, msg.sender, personal + shared);
        _credit(id, token, personal, shared);
        _solvent(token);
    }
    // Final sub-10-unit fee dust is credited to the originating NFT on migration.
    // No principal, reward liability or fee reserve can be swept by an administrator.
}
