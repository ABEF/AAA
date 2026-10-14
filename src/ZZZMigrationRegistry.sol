// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids, Route, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZOracle, IZZZVault, IZZZPools} from "./interfaces/IZZZ.sol";

/// @notice Append-only routes, including future chains, require timelocked governance
/// after seal. Remote-only graph edges let the canonical chain authenticate onward hops.
contract ZZZMigrationRegistry is ZZZModule {
    mapping(bytes32 => Route) private routes;
    mapping(bytes32 => bool) public exists;
    mapping(bytes32 => bool) public enabled;
    event RouteRegistered(bytes32 indexed routeId, uint256 sourceChain, uint256 destinationChain);
    event RouteEnabled(bytes32 indexed routeId, bool enabled);
    constructor(address controller) ZZZModule(controller) {}
    function add(Route calldata r) external onlyGovernance returns (bytes32 id) {
        if (r.sourceChain == 0 || r.destinationChain == 0 || r.sourceChain == r.destinationChain ||
            r.sourceAdapter == address(0) || r.destinationAdapter == address(0) || r.sourceVault == address(0) ||
            r.sourceReceiver == address(0) || r.destinationVault == address(0) || r.destinationReceiver == address(0) ||
            (r.sourceToken0 == address(0)) != (r.destinationToken0 == address(0)) ||
            (r.sourceToken1 == address(0)) != (r.destinationToken1 == address(0)) ||
            (r.sourceToken1 != address(0) && (r.sourceToken0 == address(0) || r.sourceToken0 == r.sourceToken1 ||
                r.destinationToken0 == r.destinationToken1)) || r.token0Decimals > 18 || r.token1Decimals > 18) revert InvalidConfiguration();
        bool localSource = r.sourceChain == block.chainid;
        bool localDestination = r.destinationChain == block.chainid;
        if (!localSource && !localDestination &&
            block.chainid != IZZZVault(access.module(Ids.VAULT)).canonicalChainId()) revert InvalidConfiguration();
        if (localSource && (r.sourceAdapter != access.module(Ids.BRIDGE) || r.sourceVault != access.module(Ids.VAULT) ||
            r.sourceReceiver != access.module(Ids.RECEIVER))) revert InvalidConfiguration();
        if (localDestination && (r.destinationAdapter != access.module(Ids.BRIDGE) || r.destinationVault != access.module(Ids.VAULT) ||
            r.destinationReceiver != access.module(Ids.RECEIVER))) revert InvalidConfiguration();
        if (localDestination && r.sourceToken1 != address(0)) {
            PoolConfig memory destination = IZZZPools(access.module(Ids.POOLS)).get(r.destinationPool);
            bool sameOrder = destination.key.currency0 == r.destinationToken0 && destination.key.currency1 == r.destinationToken1;
            bool reverseOrder = destination.key.currency0 == r.destinationToken1 && destination.key.currency1 == r.destinationToken0;
            if (!destination.operationsEnabled || (!sameOrder && !reverseOrder)) revert InvalidConfiguration();
        }
        if (localSource || localDestination) {
            address t0 = localSource ? r.sourceToken0 : r.destinationToken0;
            address t1 = localSource ? r.sourceToken1 : r.destinationToken1;
            IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
            if (t0 != address(0) && (t0.code.length == 0 || oracle.tokenDecimals(t0) != r.token0Decimals)) revert InvalidConfiguration();
            if (t1 != address(0) && (t1.code.length == 0 || oracle.tokenDecimals(t1) != r.token1Decimals)) revert InvalidConfiguration();
        }
        id = keccak256(abi.encode(r));
        if (exists[id]) revert InvalidConfiguration();
        routes[id] = r;
        exists[id] = true;
        enabled[id] = true;
        emit RouteRegistered(id, r.sourceChain, r.destinationChain);
    }
    function setEnabled(bytes32 id, bool state) external onlyGovernance {
        if (!exists[id]) revert InvalidConfiguration();
        enabled[id] = state;
        emit RouteEnabled(id, state);
    }
    function get(bytes32 id) external view returns (Route memory route, bool active) {
        if (!exists[id]) revert InvalidConfiguration();
        return (routes[id], enabled[id]);
    }
}
