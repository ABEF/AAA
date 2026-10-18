// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZRewardReceiver} from "./ZZZRewardReceiver.sol";
import {IZZZAccess, IZZZVault, IZZZRoutes} from "./interfaces/IZZZ.sol";
import {Ids, Position, PositionStatus, Route, BridgeMessage, MessageKind} from "./libraries/ZZZTypes.sol";

interface IFactoryFeeState {
    function remoteCanonicalToken(uint256 id, address asset) external view returns (address);
    function remoteIndividual(uint256 id, address asset) external view returns (uint256);
    function remoteCollective(uint256 id, address asset) external view returns (uint256);
    function canonicalLateTotal(address asset) external view returns (uint256);
    function rewardReceiverCount() external view returns (uint256);
    function rewardReceivers(uint256 index) external view returns (address);
    function dust(uint256 id, address asset) external view returns (uint256);
}
interface IFactoryRewardAssets {
    function assetCount() external view returns (uint256);
    function assets(uint256 index) external view returns (address);
}

/// @notice Fixed factory created by one FeeController. It cannot hold payments,
/// choose a fee destination or replace an existing receiver.
contract ZZZRewardReceiverFactory {
    address public immutable fees;
    address public immutable access;
    error Unauthorized();
    error InvalidState();
    error InvalidConfiguration();
    error InvalidAmount();
    constructor(address controller) { fees = msg.sender; access = controller; }
    function create(uint256 bucket, address token0, address token1, address wrapper) external returns (address) {
        if (msg.sender != fees) revert Unauthorized();
        return address(new ZZZRewardReceiver(bucket, token0, token1, wrapper, fees));
    }
    /// @dev Read-only extraction; FeeController retains every ledger write,
    /// approval and send. No route, amount or destination can be supplied here.
    function rewardMessage(uint256 id, address token, bytes32 routeId) external view returns (BridgeMessage memory m) {
        IZZZAccess controller = IZZZAccess(access);
        IZZZVault vault = IZZZVault(controller.module(Ids.VAULT));
        IFactoryFeeState state = IFactoryFeeState(fees);
        Position memory p = vault.group(id);
        if (p.homeChain == block.chainid || (p.status != PositionStatus.Active && p.status != PositionStatus.Outbound &&
            p.status != PositionStatus.Remote && p.status != PositionStatus.Inbound &&
            p.status != PositionStatus.Parked)) revert InvalidState();
        address homeToken = state.remoteCanonicalToken(id, token);
        if (homeToken == address(0)) revert InvalidConfiguration();
        (Route memory r, bool enabled) = IZZZRoutes(controller.module(Ids.ROUTES)).get(routeId);
        if (!enabled || r.sourceVault != address(vault) || r.sourceChain != block.chainid ||
            r.destinationChain != p.homeChain || r.destinationVault != p.homeVault || r.destinationReceiver != p.homeReceiver ||
            r.sourceToken0 != token || r.destinationToken0 != homeToken || r.sourceToken1 != address(0) ||
            r.destinationToken1 != address(0)) revert InvalidConfiguration();
        uint256 personal = state.remoteIndividual(id, token);
        uint256 shared = state.remoteCollective(id, token);
        if (personal + shared == 0) revert InvalidAmount();
        m.version = 3; m.kind = MessageKind.Reward; m.routeId = routeId; m.bucketId = id;
        m.homeChain = p.homeChain; m.homeVault = p.homeVault; m.homeReceiver = p.homeReceiver;
        m.homePoolId = vault.homePoolId(id); m.totalShares = vault.bucketTotalShares(id); m.depositUSD = p.depositUSD;
        m.amount0 = personal + shared; m.individual = personal; m.collective = shared; m.canonicalToken0 = homeToken;
    }
    function hasPendingExternal() external view returns (bool) {
        IFactoryFeeState state = IFactoryFeeState(fees);
        IFactoryRewardAssets admitted = IFactoryRewardAssets(IZZZAccess(access).module(Ids.REWARDS));
        for (uint256 i; i < admitted.assetCount(); ++i) if (state.canonicalLateTotal(admitted.assets(i)) != 0) return true;
        for (uint256 i; i < state.rewardReceiverCount(); ++i) {
            ZZZRewardReceiver receiver = ZZZRewardReceiver(payable(state.rewardReceivers(i)));
            (uint256 a0, uint256 a1) = receiver.pending();
            uint256 id = receiver.bucketId();
            if (a0 != 0 || a1 != 0 || state.dust(id, receiver.token0()) != 0 || state.dust(id, receiver.token1()) != 0) return true;
        }
        return false;
    }
}
