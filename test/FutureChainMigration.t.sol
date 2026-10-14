// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

// Real custody, accounting, timelocks and message validation; FAKE LP venue and
// burn/mint transport. This demonstrates state-machine integration, not real
// Uniswap execution, bridge backing, finality or cross-chain authentication.
import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZPower} from "../src/ZZZPower.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZMigrationRegistry} from "../src/ZZZMigrationRegistry.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZMigrationReceiver} from "../src/ZZZMigrationReceiver.sol";
import {ZZZBridgeAdapter} from "../src/ZZZBridgeAdapter.sol";
import {IZZZAccess, IZZZTransportReceiver} from "../src/interfaces/IZZZ.sol";
import {Ids, PoolKey, PoolConfig, Route, Position, PositionStatus, BridgeMessage}
    from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed, BoundDummy} from "./mocks/Mocks.sol";
import {VaultPolicyMock, VaultLiquidityMock} from "./VaultAccounting.t.sol";

contract FutureBoundPolicy is VaultPolicyMock {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}
contract FutureBoundVenue is VaultLiquidityMock {
    IZZZAccess public immutable access;
    constructor(address controller, address token0, address token1) VaultLiquidityMock(token0, token1) {
        access = IZZZAccess(controller);
    }
}

contract FutureQueuedTransport {
    struct Packet {
        uint256 sourceChain;
        address sourceAdapter;
        uint256 destinationChain;
        address destinationAdapter;
        address[] sourceTokens;
        address[] destinationTokens;
        uint256[] amounts;
        bytes payload;
        bool delivered;
    }
    mapping(bytes32 => Packet) private packets;
    uint256 public sequence;
    bytes32 public latest;

    function send(uint256 destinationChain, address destinationAdapter, address[] calldata tokens,
        uint256[] calldata amounts, bytes calldata payload) external payable returns (bytes32 packetId) {
        BridgeMessage memory envelope = abi.decode(payload, (BridgeMessage));
        ZZZBridgeAdapter adapter = ZZZBridgeAdapter(msg.sender);
        (Route memory route,) = ZZZMigrationRegistry(adapter.access().module(Ids.ROUTES)).get(envelope.routeId);
        require(tokens.length == amounts.length && tokens.length <= 2, "invalid mock assets");
        packetId = bytes32(++sequence);
        latest = packetId;
        Packet storage packet = packets[packetId];
        packet.sourceChain = block.chainid;
        packet.sourceAdapter = msg.sender;
        packet.destinationChain = destinationChain;
        packet.destinationAdapter = destinationAdapter;
        packet.payload = payload;
        for (uint256 i; i < tokens.length; ++i) {
            require(IERC20(tokens[i]).transferFrom(msg.sender, address(this), amounts[i]), "escrow failed");
            packet.sourceTokens.push(tokens[i]);
            packet.destinationTokens.push(i == 0 ? route.destinationToken0 : route.destinationToken1);
            packet.amounts.push(amounts[i]);
        }
    }
    function message(bytes32 packetId) external view returns (BridgeMessage memory) {
        return abi.decode(packets[packetId].payload, (BridgeMessage));
    }
    function deliver(bytes32 packetId) external { _deliver(packetId, packets[packetId].payload); }
    function deliverAltered(bytes32 packetId, BridgeMessage calldata altered) external {
        _deliver(packetId, abi.encode(altered));
    }
    function _deliver(bytes32 packetId, bytes memory payload) private {
        Packet storage packet = packets[packetId];
        require(!packet.delivered && packet.sourceAdapter != address(0), "invalid mock packet");
        require(block.chainid == packet.destinationChain, "wrong mock destination");
        packet.delivered = true;
        for (uint256 i; i < packet.sourceTokens.length; ++i) {
            // Test representations are unbacked mock tokens. A production bridge
            // must separately establish backing, asset equivalence and finality.
            MockToken(packet.sourceTokens[i]).burn(packet.amounts[i]);
            MockToken(packet.destinationTokens[i]).mint(address(this), packet.amounts[i]);
            IERC20(packet.destinationTokens[i]).approve(packet.destinationAdapter, packet.amounts[i]);
        }
        IZZZTransportReceiver(packet.destinationAdapter).onMessage(packet.sourceChain, packet.sourceAdapter, payload);
        for (uint256 i; i < packet.destinationTokens.length; ++i) {
            IERC20(packet.destinationTokens[i]).approve(packet.destinationAdapter, 0);
        }
    }
    function replay(bytes32 packetId) external {
        Packet storage packet = packets[packetId];
        require(packet.delivered && block.chainid == packet.destinationChain, "invalid mock replay");
        IZZZTransportReceiver(packet.destinationAdapter).onMessage(
            packet.sourceChain, packet.sourceAdapter, packet.payload);
    }
}

contract FutureChainMigrationTest is Test {
    struct Bundle {
        uint256 chainId;
        MockToken asset0;
        MockToken asset1;
        MockToken token0;
        MockToken token1;
        ZZZAccessController access;
        ZZZVault vault;
        ZZZNFT nft;
        ZZZPower power;
        ZZZRewards rewards;
        ZZZFeeController fees;
        ZZZMigration migration;
        ZZZMigrationReceiver receiver;
        ZZZBridgeAdapter bridge;
        ZZZMigrationRegistry routes;
        FutureBoundVenue venue;
        bytes32 poolId;
    }
    uint256 private constant HOME_CHAIN = 4663;
    address private constant ALICE = address(0xA11CE);
    address payable private constant TREASURY = payable(address(0x7EA5));
    Bundle private a;
    Bundle private b;
    Bundle private c;
    FutureQueuedTransport private transport;
    MockFeed private feed;
    uint256 private governanceSequence;

    function setUp() public {
        vm.warp(1_000_000);
        transport = new FutureQueuedTransport();
        feed = new MockFeed(8, 1e8);
        a = _deploy(HOME_CHAIN, false);
        b = _deploy(57073, true);
        c = _deploy(1, false);
        vm.chainId(HOME_CHAIN);
        vm.deal(ALICE, 1 ether);
        a.asset0.mint(ALICE, 100_000);
        a.asset1.mint(ALICE, 100_000);
        vm.startPrank(ALICE);
        a.asset0.approve(address(a.vault), type(uint256).max);
        a.asset1.approve(address(a.vault), type(uint256).max);
        vm.stopPrank();
    }
    function _deploy(uint256 chainId, bool reverseAssets) private returns (Bundle memory bundle) {
        vm.chainId(chainId);
        bundle.chainId = chainId;
        MockToken first = new MockToken(0);
        MockToken second = new MockToken(0);
        bundle.token0 = address(first) < address(second) ? first : second;
        bundle.token1 = address(first) < address(second) ? second : first;
        bundle.asset0 = reverseAssets ? bundle.token1 : bundle.token0;
        bundle.asset1 = reverseAssets ? bundle.token0 : bundle.token1;
        address[] memory governors = new address[](1);
        governors[0] = address(this);
        bundle.access = new ZZZAccessController(1 days, governors, governors, address(this), address(this));
        address controller = address(bundle.access);
        bundle.vault = new ZZZVault(controller, HOME_CHAIN, TREASURY);
        bundle.nft = new ZZZNFT(controller, "");
        bundle.power = new ZZZPower(controller);
        bundle.rewards = new ZZZRewards(controller);
        bundle.fees = new ZZZFeeController(controller);
        bundle.migration = new ZZZMigration(controller);
        bundle.receiver = new ZZZMigrationReceiver(controller);
        bundle.bridge = new ZZZBridgeAdapter(controller, address(transport));
        bundle.routes = new ZZZMigrationRegistry(controller);
        bundle.venue = new FutureBoundVenue(controller, address(bundle.token0), address(bundle.token1));
        ZZZOracle oracle = new ZZZOracle(controller, address(0));
        ZZZPoolRegistry pools = new ZZZPoolRegistry(controller);
        bundle.access.bind(Ids.VAULT, address(bundle.vault));
        bundle.access.bind(Ids.NFT, address(bundle.nft));
        bundle.access.bind(Ids.POWER, address(bundle.power));
        bundle.access.bind(Ids.REWARDS, address(bundle.rewards));
        bundle.access.bind(Ids.FEES, address(bundle.fees));
        bundle.access.bind(Ids.LIQUIDITY, address(bundle.venue));
        bundle.access.bind(Ids.STRATEGY, address(new FutureBoundPolicy(controller)));
        bundle.access.bind(Ids.COMPOUNDER, address(new ZZZCompounder(controller)));
        bundle.access.bind(Ids.BUYBACK, address(new BoundDummy(controller)));
        bundle.access.bind(Ids.MIGRATION, address(bundle.migration));
        bundle.access.bind(Ids.RECEIVER, address(bundle.receiver));
        bundle.access.bind(Ids.BRIDGE, address(bundle.bridge));
        bundle.access.bind(Ids.ROUTES, address(bundle.routes));
        bundle.access.bind(Ids.ORACLE, address(oracle));
        bundle.access.bind(Ids.POOLS, address(pools));
        oracle.setFeed(address(bundle.token0), address(feed), 3600);
        oracle.setFeed(address(bundle.token1), address(feed), 3600);
        bundle.rewards.addAsset(address(bundle.token0));
        bundle.rewards.addAsset(address(bundle.token1));
        PoolConfig memory config;
        config.key = PoolKey(address(bundle.token0), address(bundle.token1), 3000, 60, address(0));
        config.depositsEnabled = true;
        config.operationsEnabled = true;
        config.rangeBps = 1000;
        config.triggerBps = 200;
        config.maxSpotDeviationBps = 100;
        config.maxSlippageBps = 100;
        config.minRebalanceInterval = 600;
        config.minDepositUSD = 1e18;
        config.maxPositionUSD = 1e30;
        bundle.poolId = pools.configure(config);
        bundle.access.seal();
    }
    function _govern(Bundle storage bundle, address target, bytes memory data) private {
        vm.chainId(bundle.chainId);
        bytes32 salt = bytes32(++governanceSequence);
        uint256 delay = bundle.access.getMinDelay();
        bundle.access.schedule(target, 0, data, bytes32(0), salt, delay);
        vm.expectRevert();
        bundle.access.execute(target, 0, data, bytes32(0), salt);
        vm.warp(block.timestamp + delay);
        feed.set(1e8, block.timestamp, block.timestamp);
        bundle.access.execute(target, 0, data, bytes32(0), salt);
    }
    function _route(Bundle storage source, Bundle storage destination, bool principal)
        private view returns (Route memory route) {
        route.sourceChain = source.chainId;
        route.sourceAdapter = address(source.bridge);
        route.sourceVault = address(source.vault);
        route.sourceReceiver = address(source.receiver);
        route.destinationChain = destination.chainId;
        route.destinationAdapter = address(destination.bridge);
        route.destinationVault = address(destination.vault);
        route.destinationReceiver = address(destination.receiver);
        if (principal) {
            route.destinationPool = destination.poolId;
            route.sourceToken0 = address(source.token0);
            route.sourceToken1 = address(source.token1);
            route.destinationToken0 = address(source.token0) == address(source.asset0)
                ? address(destination.asset0) : address(destination.asset1);
            route.destinationToken1 = address(source.token1) == address(source.asset1)
                ? address(destination.asset1) : address(destination.asset0);
        }
    }
    function _register(Bundle storage bundle, Route memory route) private returns (bytes32 routeId) {
        routeId = keccak256(abi.encode(route));
        if (bundle.routes.exists(routeId)) return routeId;
        vm.chainId(bundle.chainId);
        assertTrue(bundle.access.isSealed());
        assertEq(bundle.access.bootstrap(), address(0));
        vm.expectRevert();
        bundle.routes.add(route);
        _govern(bundle, address(bundle.routes), abi.encodeCall(ZZZMigrationRegistry.add, (route)));
        assertTrue(bundle.routes.exists(routeId));
        assertTrue(bundle.routes.enabled(routeId));
    }
    function _onboard(Bundle storage source, Bundle storage destination, bool principal)
        private returns (bytes32 routeId) {
        Route memory route = _route(source, destination, principal);
        routeId = _register(source, route);
        _register(destination, route);
        // A learns future satellite-to-satellite edges through its own timelock.
        if (principal && source.chainId != HOME_CHAIN && destination.chainId != HOME_CHAIN) _register(a, route);
    }
    function _mintAndActivate(uint256 amount0, uint256 amount1) private returns (uint256 nftId) {
        vm.chainId(HOME_CHAIN);
        vm.startPrank(ALICE);
        nftId = a.vault.mintDormant{value: 0.05 ether}();
        a.vault.activate(nftId, a.poolId, amount0, amount1, 1, block.timestamp + 100);
        vm.stopPrank();
        assertEq(TREASURY.balance, 0.05 ether);
    }
    function _logicalAmount(Bundle storage bundle, uint256 nftId, bool assetZero) private view returns (uint256) {
        Position memory position = bundle.vault.position(nftId);
        bool first = address(assetZero ? bundle.asset0 : bundle.asset1) == address(bundle.token0);
        return first ? position.idle0 + bundle.venue.a0(position.lpTokenId)
            : position.idle1 + bundle.venue.a1(position.lpTokenId);
    }
    function _totalLogical(uint256 nftId, bool assetZero) private view returns (uint256) {
        return _logicalAmount(a, nftId, assetZero) + _logicalAmount(b, nftId, assetZero)
            + _logicalAmount(c, nftId, assetZero)
            + (assetZero ? a.asset0 : a.asset1).balanceOf(address(transport))
            + (assetZero ? b.asset0 : b.asset1).balanceOf(address(transport))
            + (assetZero ? c.asset0 : c.asset1).balanceOf(address(transport));
    }
    function _assertIdentity(uint256 nftId, uint256 contributedUSD) private view {
        assertEq(a.nft.ownerOf(nftId), ALICE);
        assertEq(a.nft.balanceOf(ALICE), 1);
        assertEq(a.vault.sequence(), 1);
        assertEq(b.vault.sequence(), 0);
        assertEq(c.vault.sequence(), 0);
        assertEq(b.nft.balanceOf(ALICE), 0);
        assertEq(c.nft.balanceOf(ALICE), 0);
        assertEq(a.power.powerOf(nftId), contributedUSD);
        assertEq(a.power.totalPower(), contributedUSD);
        assertEq(b.power.totalPower(), 0);
        assertEq(c.power.totalPower(), 0);
        assertEq(a.vault.position(nftId).depositUSD, contributedUSD);
        assertEq(a.access.module(Ids.VAULT), address(a.vault));
        assertEq(b.access.module(Ids.VAULT), address(b.vault));
        assertEq(c.access.module(Ids.VAULT), address(c.vault));
    }
    function _hop(Bundle storage source, Bundle storage destination, uint256 nftId,
        uint256 amount0, uint256 amount1, uint64 expectedEpoch, bool checkRollback) private {
        bytes32 principalRoute = _onboard(source, destination, true);
        bytes32 completionRoute = _onboard(destination, source, false);
        bytes32 homeRoute;
        if (source.chainId != HOME_CHAIN && destination.chainId != HOME_CHAIN) homeRoute = _onboard(destination, a, false);
        _govern(source, address(source.migration), abi.encodeCall(ZZZMigration.propose, (nftId, principalRoute)));
        bytes32 migrationId = source.migration.activePlan(nftId);
        assertTrue(migrationId != bytes32(0));
        vm.expectRevert();
        source.migration.execute(migrationId, block.timestamp + 100);
        vm.warp(block.timestamp + source.migration.MIGRATION_DELAY());
        feed.set(1e8, block.timestamp, block.timestamp);
        source.migration.execute(migrationId, block.timestamp + 100);
        bytes32 principalPacket = transport.latest();
        Position memory drained = source.vault.position(nftId);
        assertEq(uint256(drained.status), uint256(PositionStatus.Outbound));
        assertEq(drained.lpTokenId, 0);
        assertEq(drained.idle0 + drained.idle1, 0);
        assertEq(source.vault.totalIdle(address(source.token0)), 0);
        assertEq(source.vault.totalIdle(address(source.token1)), 0);
        assertEq(_totalLogical(nftId, true), amount0);
        assertEq(_totalLogical(nftId, false), amount1);
        vm.chainId(destination.chainId);
        if (checkRollback) {
            BridgeMessage memory altered = transport.message(principalPacket);
            altered.previousVault = address(0xBAD);
            vm.expectRevert();
            transport.deliverAltered(principalPacket, altered);
            assertEq(uint256(destination.vault.position(nftId).status), uint256(PositionStatus.None));
            assertEq(_totalLogical(nftId, true), amount0);
            assertEq(_totalLogical(nftId, false), amount1);
        }
        transport.deliver(principalPacket);
        assertEq(uint256(destination.vault.position(nftId).status), uint256(PositionStatus.Inbound));
        assertEq(destination.migration.custodyEpoch(nftId), expectedEpoch);
        vm.expectRevert();
        destination.receiver.acknowledge(migrationId, completionRoute);
        destination.receiver.finalize(migrationId, 1, block.timestamp + 100);
        assertEq(uint256(destination.vault.position(nftId).status), uint256(PositionStatus.Active));
        assertEq(_logicalAmount(destination, nftId, true), amount0);
        assertEq(_logicalAmount(destination, nftId, false), amount1);
        assertEq(destination.vault.position(nftId).depositUSD, (amount0 + amount1) * 1e18);
        Position memory active = destination.vault.position(nftId);
        assertEq(active.homeChain, HOME_CHAIN);
        assertEq(active.homeVault, address(a.vault));
        assertEq(active.homeReceiver, address(a.receiver));
        assertEq(active.homeToken0, address(destination.token0) == address(destination.asset0)
            ? address(a.asset0) : address(a.asset1));
        assertEq(active.homeToken1, address(destination.token1) == address(destination.asset1)
            ? address(a.asset1) : address(a.asset0));
        vm.expectRevert();
        transport.replay(principalPacket);
        bytes32 completionPacket = destination.receiver.acknowledge(migrationId, completionRoute);
        vm.chainId(source.chainId);
        transport.deliver(completionPacket);
        assertEq(source.migration.activePlan(nftId), bytes32(0));
        assertEq(uint256(source.vault.position(nftId).status), uint256(PositionStatus.Remote));
        assertEq(source.vault.position(nftId).locationChain, destination.chainId);
        assertEq(source.vault.position(nftId).locationVault, address(destination.vault));
        if (homeRoute != bytes32(0)) {
            vm.chainId(destination.chainId);
            bytes32 homePacket = destination.receiver.acknowledgeHome(migrationId, homeRoute);
            vm.chainId(HOME_CHAIN);
            transport.deliver(homePacket);
        }
        Position memory canonical = a.vault.position(nftId);
        assertEq(canonical.locationChain, destination.chainId);
        assertEq(canonical.locationVault, address(destination.vault));
        assertEq(a.migration.custodyEpoch(nftId), expectedEpoch);
        _assertIdentity(nftId, (amount0 + amount1) * 1e18);
        assertEq(_totalLogical(nftId, true), amount0);
        assertEq(_totalLogical(nftId, false), amount1);
    }

    function testPostSealRoutesSupportThreeChainsReturnHomeAndRevisitSatellite() public {
        uint256 nftId = _mintAndActivate(1000, 1000);
        assertFalse(a.routes.exists(keccak256(abi.encode(_route(b, c, true)))));
        _hop(a, b, nftId, 1000, 1000, 1, false);
        BridgeMessage memory firstAck = transport.message(transport.latest());
        vm.chainId(b.chainId);
        bytes32 completedRetry = b.receiver.acknowledge(firstAck.migrationId, firstAck.routeId);
        _hop(b, c, nftId, 1000, 1000, 2, false);
        BridgeMessage memory onwardAck = transport.message(transport.latest());
        vm.chainId(c.chainId);
        bytes32 locationRetry = c.receiver.acknowledgeHome(onwardAck.migrationId, onwardAck.routeId);
        _hop(c, a, nftId, 1000, 1000, 3, false);
        // New transport nonces may carry old valid ACKs. Both the old completed
        // source plan and the old canonical snapshot must remain harmless retries
        // after the NFT's principal has returned to an active home position.
        vm.chainId(HOME_CHAIN);
        transport.deliver(completedRetry);
        transport.deliver(locationRetry);
        assertEq(uint256(a.vault.position(nftId).status), uint256(PositionStatus.Active));
        assertEq(a.vault.position(nftId).locationChain, HOME_CHAIN);
        assertEq(a.vault.position(nftId).locationVault, address(a.vault));
        assertEq(a.migration.custodyEpoch(nftId), 3);
        assertEq(_logicalAmount(a, nftId, true), 1000);
        assertEq(_logicalAmount(a, nftId, false), 1000);
        _hop(a, b, nftId, 1000, 1000, 4, false);
        assertEq(uint256(a.vault.position(nftId).status), uint256(PositionStatus.Remote));
        assertEq(uint256(b.vault.position(nftId).status), uint256(PositionStatus.Active));
        assertEq(uint256(c.vault.position(nftId).status), uint256(PositionStatus.Remote));
    }
    function testReversedCurrenciesPreserveUnequalPrincipalAndRejectedDeliveryRollsBack() public {
        uint256 nftId = _mintAndActivate(1000, 2000);
        assertEq(address(a.token0), address(a.asset0));
        assertEq(address(b.token0), address(b.asset1));
        _hop(a, b, nftId, 1000, 2000, 1, true);
        assertEq(_logicalAmount(b, nftId, true), 1000);
        assertEq(_logicalAmount(b, nftId, false), 2000);
        assertEq(a.power.powerOf(nftId), 3000e18);
    }
}
