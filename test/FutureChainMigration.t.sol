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
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZMigrationRegistry} from "../src/ZZZMigrationRegistry.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZMigrationReceiver} from "../src/ZZZMigrationReceiver.sol";
import {ZZZBridgeAdapter} from "../src/ZZZBridgeAdapter.sol";
import {ZZZBridgeRouter} from "../src/ZZZBridgeRouter.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {Ids, PoolKey, PoolConfig, Route, Position, PositionStatus, BridgeMessage, TransportPolicy, TransportEnvelope}
    from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed, BoundDummy} from "./mocks/Mocks.sol";
import {VaultPolicyMock, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

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
        address sourceRouter;
        address sourceProvider;
        uint256 destinationChain;
        address destinationRouter;
        address destinationProvider;
        address[] sourceTokens;
        address[] destinationTokens;
        uint256[] amounts;
        bytes payload;
        bool delivered;
    }
    mapping(bytes32 => Packet) private packets;
    uint256 public sequence;
    bytes32 public latest;

    function enqueue(bytes32 policyId, uint256 destinationChain, address destinationProvider, address destinationRouter,
        address[] calldata tokens, uint256[] calldata amounts, bytes calldata payload) external returns (bytes32 packetId) {
        TransportEnvelope memory envelope = abi.decode(payload, (TransportEnvelope));
        require(envelope.version == 1 && envelope.policyId == policyId, "wrong mock policy envelope");
        BridgeMessage memory message_ = abi.decode(envelope.payload, (BridgeMessage));
        address sourceRouter = FutureProviderWrapper(msg.sender).router();
        ZZZBridgeRouter router = ZZZBridgeRouter(sourceRouter);
        (Route memory route,) = ZZZMigrationRegistry(router.access().module(Ids.ROUTES)).get(message_.routeId);
        require(tokens.length == amounts.length && tokens.length <= 2, "invalid mock assets");
        packetId = bytes32(++sequence);
        latest = packetId;
        Packet storage packet = packets[packetId];
        packet.sourceChain = block.chainid;
        packet.sourceRouter = sourceRouter;
        packet.sourceProvider = msg.sender;
        packet.destinationChain = destinationChain;
        packet.destinationRouter = destinationRouter;
        packet.destinationProvider = destinationProvider;
        packet.payload = payload;
        for (uint256 i; i < tokens.length; ++i) {
            packet.sourceTokens.push(tokens[i]);
            packet.destinationTokens.push(i == 0 ? route.destinationToken0 : route.destinationToken1);
            packet.amounts.push(amounts[i]);
        }
    }
    function message(bytes32 packetId) external view returns (BridgeMessage memory) {
        TransportEnvelope memory envelope = abi.decode(packets[packetId].payload, (TransportEnvelope));
        return abi.decode(envelope.payload, (BridgeMessage));
    }
    function deliver(bytes32 packetId) external { _deliver(packetId, packets[packetId].payload); }
    function deliverAltered(bytes32 packetId, BridgeMessage calldata altered) external {
        TransportEnvelope memory envelope = abi.decode(packets[packetId].payload, (TransportEnvelope));
        envelope.payload = abi.encode(altered);
        _deliver(packetId, abi.encode(envelope));
    }
    function _deliver(bytes32 packetId, bytes memory payload) private {
        Packet storage packet = packets[packetId];
        require(!packet.delivered && packet.sourceProvider != address(0), "invalid mock packet");
        require(block.chainid == packet.destinationChain, "wrong mock destination");
        packet.delivered = true;
        for (uint256 i; i < packet.sourceTokens.length; ++i) {
            // Test representations are unbacked mock tokens. A production bridge
            // must separately establish backing, asset equivalence and finality.
            MockToken(packet.sourceTokens[i]).burn(packet.amounts[i]);
            MockToken(packet.destinationTokens[i]).mint(packet.destinationProvider, packet.amounts[i]);
        }
        FutureProviderWrapper(packet.destinationProvider).deliverToRouter(packet.sourceChain, packet.sourceRouter,
            packet.destinationRouter, packet.destinationTokens, packet.amounts, payload);
    }
    function replay(bytes32 packetId) external {
        Packet storage packet = packets[packetId];
        require(packet.delivered && block.chainid == packet.destinationChain, "invalid mock replay");
        FutureProviderWrapper(packet.destinationProvider).deliverToRouter(packet.sourceChain, packet.sourceRouter,
            packet.destinationRouter, packet.destinationTokens, packet.amounts, packet.payload);
    }
}

/// @notice TEST ONLY: per-chain provider wrapper over an unaudited burn/mint queue.
/// The fixture authenticates its local router/queue boundary; it does not model a
/// production bridge's consensus, finality, custody backing or configuration powers.
contract FutureProviderWrapper {
    address public immutable router;
    FutureQueuedTransport public immutable queue;
    bytes32 private immutable configuration;
    constructor(address router_, FutureQueuedTransport queue_, uint256 revision) {
        router = router_;
        queue = queue_;
        configuration = keccak256(abi.encode("TEST ONLY fake provider", block.chainid, revision));
    }
    function configurationHash(bytes32 channelId) external view returns (bytes32) {
        return keccak256(abi.encode(configuration, channelId));
    }
    function send(bytes32 policyId, uint256 destinationChain, address destinationProvider, address destinationRouter,
        address[] calldata tokens, uint256[] calldata amounts, bytes calldata envelope)
        external payable returns (bytes32) {
        require(msg.sender == router, "unbound mock router");
        require(tokens.length == amounts.length, "wrong mock assets");
        for (uint256 i; i < tokens.length; ++i) {
            require(IERC20(tokens[i]).transferFrom(router, address(queue), amounts[i]), "mock escrow failed");
        }
        return queue.enqueue(policyId, destinationChain, destinationProvider, destinationRouter, tokens, amounts, envelope);
    }
    function deliverToRouter(uint256 sourceChain, address sourceRouter, address destinationRouter,
        address[] calldata tokens, uint256[] calldata amounts, bytes calldata envelope) external {
        require(msg.sender == address(queue) && destinationRouter == router, "unbound mock delivery");
        for (uint256 i; i < tokens.length; ++i) IERC20(tokens[i]).approve(router, amounts[i]);
        ZZZBridgeRouter(router).onProviderMessage(sourceChain, sourceRouter, tokens, amounts, envelope);
        for (uint256 i; i < tokens.length; ++i) {
            IERC20(tokens[i]).approve(router, 0);
            require(IERC20(tokens[i]).balanceOf(address(this)) == 0, "unsettled mock delivery");
        }
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
        MockVRF vrf;
        ZZZMembership membership;
        ZZZRewards rewards;
        ZZZFeeController fees;
        ZZZMigration migration;
        ZZZMigrationReceiver receiver;
        ZZZBridgeAdapter bridge;
        ZZZBridgeRouter router;
        FutureProviderWrapper provider;
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
    uint256[] private canonicalNFTs;

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
        bundle.vrf = new MockVRF();
        bundle.nft.configureRandomness(address(bundle.vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        bundle.membership = new ZZZMembership(controller);
        bundle.rewards = new ZZZRewards(controller);
        bundle.fees = new ZZZFeeController(controller);
        bundle.migration = new ZZZMigration(controller);
        bundle.receiver = new ZZZMigrationReceiver(controller);
        bundle.router = new ZZZBridgeRouter(controller);
        bundle.provider = new FutureProviderWrapper(address(bundle.router), transport, 1);
        bundle.bridge = new ZZZBridgeAdapter(controller, address(bundle.router));
        bundle.routes = new ZZZMigrationRegistry(controller);
        bundle.venue = new FutureBoundVenue(controller, address(bundle.token0), address(bundle.token1));
        ZZZOracle oracle = new ZZZOracle(controller, address(0));
        ZZZPoolRegistry pools = new ZZZPoolRegistry(controller);
        bundle.access.bind(Ids.VAULT, address(bundle.vault));
        bundle.access.bind(Ids.NFT, address(bundle.nft));
        bundle.access.bind(Ids.MEMBERSHIP, address(bundle.membership));
        bundle.access.bind(Ids.REWARDS, address(bundle.rewards));
        bundle.access.bind(Ids.FEES, address(bundle.fees));
        bundle.access.bind(Ids.LIQUIDITY, address(bundle.venue));
        bundle.access.bind(Ids.STRATEGY, address(new FutureBoundPolicy(controller)));
        bundle.access.bind(Ids.COMPOUNDER, address(new ZZZCompounder(controller)));
        bundle.access.bind(Ids.BUYBACK, address(new BoundDummy(controller)));
        bundle.access.bind(Ids.MIGRATION, address(bundle.migration));
        bundle.access.bind(Ids.RECEIVER, address(bundle.receiver));
        bundle.access.bind(Ids.BRIDGE, address(bundle.bridge));
        bundle.access.bind(Ids.TRANSPORT, address(bundle.router));
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
    function _policy(Bundle storage source, Bundle storage destination) private view returns (TransportPolicy memory p) {
        p.providerId = keccak256("TEST ONLY queued burn/mint provider");
        p.sourceChain = source.chainId;
        p.sourceRouter = address(source.router);
        p.sourceProvider = address(source.provider);
        p.sourceCodeHash = address(source.provider).codehash;
        p.destinationChain = destination.chainId;
        p.destinationRouter = address(destination.router);
        p.destinationProvider = address(destination.provider);
        p.destinationCodeHash = address(destination.provider).codehash;
        p.channelId = keccak256(abi.encode(p.providerId, p.sourceChain, p.destinationChain,
            p.sourceProvider, p.destinationProvider));
        p.sourceConfigurationHash = source.provider.configurationHash(p.channelId);
        p.destinationConfigurationHash = destination.provider.configurationHash(p.channelId);
        p.reviewHash = keccak256("TEST ONLY fixture metadata, not a bridge review");
    }
    function _registerPolicy(Bundle storage bundle, TransportPolicy memory p) private returns (bytes32 policyId) {
        policyId = keccak256(abi.encode(p));
        if (bundle.router.policyExists(policyId)) return policyId;
        vm.chainId(bundle.chainId);
        assertTrue(bundle.access.isSealed());
        vm.expectRevert();
        bundle.router.registerPolicy(p);
        _govern(bundle, address(bundle.router), abi.encodeCall(ZZZBridgeRouter.registerPolicy, (p)));
        assertTrue(bundle.router.policyExists(policyId));
        assertFalse(bundle.router.outboundEnabled(policyId));
    }
    function _register(Bundle storage bundle, Route memory route, bytes32 policyId) private returns (bytes32 routeId) {
        routeId = keccak256(abi.encode(route, policyId));
        if (bundle.routes.exists(routeId)) return routeId;
        vm.chainId(bundle.chainId);
        assertTrue(bundle.access.isSealed());
        assertEq(bundle.access.bootstrap(), address(0));
        vm.expectRevert();
        bundle.routes.add(route, policyId);
        _govern(bundle, address(bundle.routes), abi.encodeCall(ZZZMigrationRegistry.add, (route, policyId)));
        assertTrue(bundle.routes.exists(routeId));
        assertTrue(bundle.routes.enabled(routeId));
        assertEq(bundle.routes.transportPolicyId(routeId), policyId);
    }
    function _onboard(Bundle storage source, Bundle storage destination, bool principal)
        private returns (bytes32 routeId) {
        return _onboardRoute(source, destination, _route(source, destination, principal));
    }
    function _onboardRoute(Bundle storage source, Bundle storage destination, Route memory route)
        private returns (bytes32 routeId) {
        if (route.sourceToken1 != address(0)) {
            uint256 bucket = a.vault.poolBucket(a.poolId);
            assertTrue(bucket != 0);
            if (destination.vault.poolBucket(route.destinationPool) == 0) {
                _govern(destination, address(destination.vault),
                    abi.encodeCall(ZZZVault.reservePool, (route.destinationPool, bucket)));
            }
            assertEq(destination.vault.poolBucket(route.destinationPool), bucket);
        }
        TransportPolicy memory p = _policy(source, destination);
        bytes32 policyId = _registerPolicy(source, p);
        routeId = _register(source, route, policyId);
        _registerPolicy(destination, p);
        _register(destination, route, policyId);
        // A learns future satellite-to-satellite edges through its own timelock.
        if (route.sourceToken1 != address(0) && source.chainId != HOME_CHAIN && destination.chainId != HOME_CHAIN) {
            _registerPolicy(a, p);
            _register(a, route, policyId);
        }
        if (!source.router.outboundEnabled(policyId)) {
            _govern(source, address(source.router), abi.encodeCall(ZZZBridgeRouter.setOutboundEnabled, (policyId, true)));
        }
        vm.chainId(source.chainId);
        assertTrue(source.router.canSend(routeId));
    }
    function _mintAndActivate(uint256 amount0, uint256 amount1) private returns (uint256 bucketId) {
        vm.chainId(HOME_CHAIN);
        vm.startPrank(ALICE);
        uint256 nftId = a.vault.mintDormant{value: 0.05 ether}();
        vm.stopPrank();
        _finalizeTraits(nftId);
        vm.startPrank(ALICE);
        canonicalNFTs.push(nftId);
        a.vault.activate(nftId, a.poolId, amount0, amount1, 1, block.timestamp + 100);
        bucketId = a.vault.nftBucket(nftId);
        vm.stopPrank();
        assertEq(TREASURY.balance, 0.05 ether * canonicalNFTs.length);
    }
    function _finalizeTraits(uint256 id) private {
        a.vrf.fulfill(a.nft.requestOf(id), 1, 1);
        a.nft.finalizeTraits(id);
    }
    function _logicalAmount(Bundle storage bundle, uint256 bucketId, bool assetZero) private view returns (uint256) {
        Position memory position = bundle.vault.group(bucketId);
        bool first = address(assetZero ? bundle.asset0 : bundle.asset1) == address(bundle.token0);
        return first ? position.idle0 + bundle.venue.a0(position.lpTokenId)
            : position.idle1 + bundle.venue.a1(position.lpTokenId);
    }
    function _totalLogical(uint256 bucketId, bool assetZero) private view returns (uint256) {
        return _logicalAmount(a, bucketId, assetZero) + _logicalAmount(b, bucketId, assetZero)
            + _logicalAmount(c, bucketId, assetZero)
            + (assetZero ? a.asset0 : a.asset1).balanceOf(address(transport))
            + (assetZero ? b.asset0 : b.asset1).balanceOf(address(transport))
            + (assetZero ? c.asset0 : c.asset1).balanceOf(address(transport));
    }
    function _assertIdentity(uint256 bucketId, uint256 contributedUSD) private view {
        uint256 shares;
        uint256 members;
        uint256 contributions;
        for (uint256 i; i < canonicalNFTs.length; ++i) {
            uint256 nftId = canonicalNFTs[i];
            assertEq(a.nft.ownerOf(nftId), ALICE);
            assertEq(a.vault.nftBucket(nftId), bucketId);
            shares += a.vault.sharesOf(nftId);
            if (a.membership.eligible(nftId)) ++members;
            contributions += a.vault.contributionUSD(nftId);
        }
        assertEq(shares, a.vault.bucketTotalShares(bucketId));
        assertEq(members, canonicalNFTs.length);
        assertEq(contributions, contributedUSD);
        assertEq(a.nft.balanceOf(ALICE), canonicalNFTs.length);
        assertEq(a.vault.sequence(), canonicalNFTs.length);
        assertEq(b.vault.sequence(), 0);
        assertEq(c.vault.sequence(), 0);
        assertEq(b.nft.balanceOf(ALICE), 0);
        assertEq(c.nft.balanceOf(ALICE), 0);
        assertEq(a.membership.totalEligible(), canonicalNFTs.length);
        assertEq(b.membership.totalEligible(), 0);
        assertEq(c.membership.totalEligible(), 0);
        assertEq(a.vault.group(bucketId).depositUSD, contributedUSD);
        assertEq(a.access.module(Ids.VAULT), address(a.vault));
        assertEq(b.access.module(Ids.VAULT), address(b.vault));
        assertEq(c.access.module(Ids.VAULT), address(c.vault));
        assertEq(a.access.module(Ids.TRANSPORT), address(a.router));
        assertEq(b.access.module(Ids.TRANSPORT), address(b.router));
        assertEq(c.access.module(Ids.TRANSPORT), address(c.router));
        assertEq(address(a.bridge.transport()), address(a.router));
        assertEq(address(b.bridge.transport()), address(b.router));
        assertEq(address(c.bridge.transport()), address(c.router));
    }
    function _hop(Bundle storage source, Bundle storage destination, uint256 bucketId,
        uint256 amount0, uint256 amount1, uint64 expectedEpoch, bool checkRollback) private {
        bytes32 principalRoute = _onboard(source, destination, true);
        bytes32 completionRoute = _onboard(destination, source, false);
        bytes32 homeRoute;
        if (source.chainId != HOME_CHAIN && destination.chainId != HOME_CHAIN) homeRoute = _onboard(destination, a, false);
        _govern(source, address(source.migration), abi.encodeCall(ZZZMigration.propose, (bucketId, principalRoute)));
        bytes32 migrationId = source.migration.activePlan(bucketId);
        assertTrue(migrationId != bytes32(0));
        vm.expectRevert();
        source.migration.execute(migrationId, block.timestamp + 100);
        vm.warp(block.timestamp + source.migration.MIGRATION_DELAY());
        feed.set(1e8, block.timestamp, block.timestamp);
        source.migration.execute(migrationId, block.timestamp + 100);
        bytes32 principalPacket = transport.latest();
        Position memory drained = source.vault.group(bucketId);
        assertEq(uint256(drained.status), uint256(PositionStatus.Outbound));
        assertEq(drained.lpTokenId, 0);
        assertEq(drained.idle0 + drained.idle1, 0);
        assertEq(source.vault.totalIdle(address(source.token0)), 0);
        assertEq(source.vault.totalIdle(address(source.token1)), 0);
        assertEq(_totalLogical(bucketId, true), amount0);
        assertEq(_totalLogical(bucketId, false), amount1);
        vm.chainId(destination.chainId);
        if (checkRollback) {
            BridgeMessage memory altered = transport.message(principalPacket);
            altered.previousVault = address(0xBAD);
            vm.expectRevert();
            transport.deliverAltered(principalPacket, altered);
            assertEq(uint256(destination.vault.group(bucketId).status), uint256(PositionStatus.None));
            assertEq(_totalLogical(bucketId, true), amount0);
            assertEq(_totalLogical(bucketId, false), amount1);
        }
        transport.deliver(principalPacket);
        assertEq(uint256(destination.vault.group(bucketId).status), uint256(PositionStatus.Inbound));
        assertEq(destination.migration.custodyEpoch(bucketId), expectedEpoch);
        vm.expectRevert();
        destination.receiver.acknowledge(migrationId, completionRoute);
        destination.receiver.finalize(migrationId, 1, block.timestamp + 100);
        assertEq(uint256(destination.vault.group(bucketId).status), uint256(PositionStatus.Active));
        assertEq(_logicalAmount(destination, bucketId, true), amount0);
        assertEq(_logicalAmount(destination, bucketId, false), amount1);
        assertEq(destination.vault.group(bucketId).depositUSD, a.vault.group(bucketId).depositUSD);
        Position memory active = destination.vault.group(bucketId);
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
        assertEq(source.migration.activePlan(bucketId), bytes32(0));
        assertEq(uint256(source.vault.group(bucketId).status), uint256(PositionStatus.Remote));
        assertEq(source.vault.group(bucketId).locationChain, destination.chainId);
        assertEq(source.vault.group(bucketId).locationVault, address(destination.vault));
        if (homeRoute != bytes32(0)) {
            vm.chainId(destination.chainId);
            bytes32 homePacket = destination.receiver.acknowledgeHome(migrationId, homeRoute);
            vm.chainId(HOME_CHAIN);
            transport.deliver(homePacket);
        }
        Position memory canonical = a.vault.group(bucketId);
        assertEq(canonical.locationChain, destination.chainId);
        assertEq(canonical.locationVault, address(destination.vault));
        assertEq(a.migration.custodyEpoch(bucketId), expectedEpoch);
        _assertIdentity(bucketId, a.vault.group(bucketId).depositUSD);
        assertEq(_totalLogical(bucketId, true), amount0);
        assertEq(_totalLogical(bucketId, false), amount1);
        vm.chainId(HOME_CHAIN);
    }

    function testEmptyRouterAllowsSealedDormantMintAndLocalPermanentActivation() public {
        bytes32 futurePolicy = keccak256(abi.encode(_policy(a, b)));
        bytes32 futureRoute = keccak256(abi.encode(_route(a, b, true), futurePolicy));
        assertTrue(a.access.isSealed());
        assertEq(a.access.bootstrap(), address(0));
        assertEq(a.access.module(Ids.TRANSPORT), address(a.router));
        assertFalse(a.router.policyExists(futurePolicy));
        assertFalse(a.routes.exists(futureRoute));
        assertFalse(a.router.canSend(futureRoute));
        vm.prank(ALICE);
        uint256 nftId = a.vault.mintDormant{value: 0.05 ether}();
        canonicalNFTs.push(nftId);
        uint256 bucketId = uint256(keccak256(abi.encode(HOME_CHAIN, address(a.vault), a.poolId)));
        assertEq(uint256(a.vault.nftStatus(nftId)), uint256(PositionStatus.Dormant));
        assertEq(a.vault.nftBucket(nftId), 0);
        assertEq(a.vault.sharesOf(nftId), 0);
        assertEq(a.vault.contributionUSD(nftId), 0);
        assertFalse(a.membership.eligible(nftId));
        assertEq(a.membership.totalEligible(), 0);
        assertEq(_totalLogical(bucketId, true), 0);
        assertEq(_totalLogical(bucketId, false), 0);
        assertEq(TREASURY.balance, 0.05 ether);

        _finalizeTraits(nftId);
        vm.prank(ALICE);
        // This mock venue leaves 1% idle; the deployed LP must still exceed $100.
        a.vault.activate(nftId, a.poolId, 300, 300, 1, block.timestamp + 100);
        Position memory active = a.vault.group(bucketId);
        assertEq(uint256(active.status), uint256(PositionStatus.Active));
        assertEq(a.venue.ownerOf(active.lpTokenId), address(a.vault));
        assertEq(_logicalAmount(a, bucketId, true), 300);
        assertEq(_logicalAmount(a, bucketId, false), 300);
        _assertIdentity(bucketId, 600e18);
        assertFalse(a.router.policyExists(futurePolicy));
        assertFalse(a.routes.exists(futureRoute));
        assertFalse(a.router.canSend(futureRoute));
    }

    function testPostSealRoutesSupportThreeChainsReturnHomeAndRevisitSatellite() public {
        uint256 bucketId = _mintAndActivate(1000, 1000);
        assertFalse(a.routes.exists(keccak256(abi.encode(_route(b, c, true), keccak256(abi.encode(_policy(b, c)))))));
        _hop(a, b, bucketId, 1000, 1000, 1, false);
        BridgeMessage memory firstAck = transport.message(transport.latest());
        vm.chainId(b.chainId);
        bytes32 completedRetry = b.receiver.acknowledge(firstAck.migrationId, firstAck.routeId);
        _hop(b, c, bucketId, 1000, 1000, 2, false);
        BridgeMessage memory onwardAck = transport.message(transport.latest());
        vm.chainId(c.chainId);
        bytes32 locationRetry = c.receiver.acknowledgeHome(onwardAck.migrationId, onwardAck.routeId);
        _hop(c, a, bucketId, 1000, 1000, 3, false);
        // New transport nonces may carry old valid ACKs. Both the old completed
        // source plan and the old canonical snapshot must remain harmless retries
        // after the NFT's principal has returned to an active home position.
        vm.chainId(HOME_CHAIN);
        transport.deliver(completedRetry);
        transport.deliver(locationRetry);
        assertEq(uint256(a.vault.group(bucketId).status), uint256(PositionStatus.Active));
        assertEq(a.vault.group(bucketId).locationChain, HOME_CHAIN);
        assertEq(a.vault.group(bucketId).locationVault, address(a.vault));
        assertEq(a.migration.custodyEpoch(bucketId), 3);
        assertEq(_logicalAmount(a, bucketId, true), 1000);
        assertEq(_logicalAmount(a, bucketId, false), 1000);
        _hop(a, b, bucketId, 1000, 1000, 4, false);
        assertEq(uint256(a.vault.group(bucketId).status), uint256(PositionStatus.Remote));
        assertEq(uint256(b.vault.group(bucketId).status), uint256(PositionStatus.Active));
        assertEq(uint256(c.vault.group(bucketId).status), uint256(PositionStatus.Remote));
    }
    function testReversedCurrenciesPreserveUnequalPrincipalAndRejectedDeliveryRollsBack() public {
        uint256 bucketId = _mintAndActivate(1000, 2000);
        assertEq(address(a.token0), address(a.asset0));
        assertEq(address(b.token0), address(b.asset1));
        _hop(a, b, bucketId, 1000, 2000, 1, true);
        assertEq(_logicalAmount(b, bucketId, true), 1000);
        assertEq(_logicalAmount(b, bucketId, false), 2000);
        assertTrue(a.membership.eligible(canonicalNFTs[0]));
        assertEq(a.vault.contributionUSD(canonicalNFTs[0]), 3000e18);
    }

    function testOneSidedPrincipalKeepsTwoLogicalMappingsThroughRealRouters() public {
        uint256 bucketId = _mintAndActivate(0, 1000);
        _hop(a, b, bucketId, 0, 1000, 1, false);
        assertEq(_logicalAmount(b, bucketId, true), 0);
        assertEq(_logicalAmount(b, bucketId, false), 1000);
        _assertIdentity(bucketId, 1000e18);
    }

    function _rotateProvider(Bundle storage bundle) private {
        vm.chainId(bundle.chainId);
        bundle.provider = new FutureProviderWrapper(address(bundle.router), transport, 2);
    }

    function testNewProviderPolicyCannotRedirectOrStrandAnOldPendingPrincipal() public {
        uint256 bucketId = _mintAndActivate(1000, 1000);
        bytes32 oldRoute = _onboard(a, b, true);
        bytes32 oldPolicy = a.routes.transportPolicyId(oldRoute);
        TransportPolicy memory frozen = a.router.policy(oldPolicy);
        _govern(a, address(a.migration), abi.encodeCall(ZZZMigration.propose, (bucketId, oldRoute)));
        bytes32 migrationId = a.migration.activePlan(bucketId);
        vm.warp(block.timestamp + a.migration.MIGRATION_DELAY());
        feed.set(1e8, block.timestamp, block.timestamp);
        a.migration.execute(migrationId, block.timestamp + 100);
        bytes32 pending = transport.latest();
        assertEq(_totalLogical(bucketId, true), 1000);
        assertEq(_totalLogical(bucketId, false), 1000);

        _rotateProvider(a);
        _rotateProvider(b);
        bytes32 newRoute = _onboard(a, b, true);
        bytes32 newPolicy = a.routes.transportPolicyId(newRoute);
        assertTrue(newRoute != oldRoute);
        assertTrue(newPolicy != oldPolicy);
        assertEq(keccak256(abi.encode(a.router.policy(oldPolicy))), keccak256(abi.encode(frozen)));
        _govern(a, address(a.router), abi.encodeCall(ZZZBridgeRouter.setOutboundEnabled, (oldPolicy, false)));
        _govern(a, address(a.routes), abi.encodeCall(ZZZMigrationRegistry.setEnabled, (oldRoute, false)));
        assertFalse(a.router.canSend(oldRoute));
        assertTrue(a.router.canSend(newRoute));
        // Disable the destination's route too: an accepted, funded old message
        // settles using its original wrapper/policy rather than the new provider.
        _govern(b, address(b.routes), abi.encodeCall(ZZZMigrationRegistry.setEnabled, (oldRoute, false)));
        transport.deliver(pending);
        b.receiver.finalize(migrationId, 1, block.timestamp + 100);
        assertEq(_logicalAmount(b, bucketId, true), 1000);
        assertEq(_logicalAmount(b, bucketId, false), 1000);
        bytes32 newAckRoute = _onboard(b, a, false);
        bytes32 ack = b.receiver.acknowledge(migrationId, newAckRoute);
        vm.chainId(HOME_CHAIN);
        transport.deliver(ack);
        assertEq(a.migration.activePlan(bucketId), bytes32(0));
        assertEq(a.vault.group(bucketId).locationVault, address(b.vault));
        _assertIdentity(bucketId, 2000e18);
        assertEq(_totalLogical(bucketId, true), 1000);
        assertEq(_totalLogical(bucketId, false), 1000);
    }

    function _governMustFail(Bundle storage bundle, address target, bytes memory data) private {
        vm.chainId(bundle.chainId);
        bytes32 salt = bytes32(++governanceSequence);
        uint256 delay = bundle.access.getMinDelay();
        bundle.access.schedule(target, 0, data, bytes32(0), salt, delay);
        vm.warp(block.timestamp + delay);
        feed.set(1e8, block.timestamp, block.timestamp);
        vm.expectRevert();
        bundle.access.execute(target, 0, data, bytes32(0), salt);
    }

    function testPolicyDisableBlocksProposalAndExecutionWithoutClosingTheLP() public {
        uint256 bucketId = _mintAndActivate(1000, 1000);
        bytes32 routeId = _onboard(a, b, true);
        bytes32 policyId = a.routes.transportPolicyId(routeId);
        _govern(a, address(a.router), abi.encodeCall(ZZZBridgeRouter.setOutboundEnabled, (policyId, false)));
        _governMustFail(a, address(a.migration), abi.encodeCall(ZZZMigration.propose, (bucketId, routeId)));
        assertEq(a.migration.activePlan(bucketId), bytes32(0));
        _govern(a, address(a.router), abi.encodeCall(ZZZBridgeRouter.setOutboundEnabled, (policyId, true)));
        _govern(a, address(a.migration), abi.encodeCall(ZZZMigration.propose, (bucketId, routeId)));
        bytes32 migrationId = a.migration.activePlan(bucketId);
        uint256 lp = a.vault.group(bucketId).lpTokenId;
        _govern(a, address(a.router), abi.encodeCall(ZZZBridgeRouter.setOutboundEnabled, (policyId, false)));
        vm.warp(block.timestamp + a.migration.MIGRATION_DELAY());
        feed.set(1e8, block.timestamp, block.timestamp);
        vm.expectRevert();
        a.migration.execute(migrationId, block.timestamp + 100);
        assertEq(uint256(a.vault.group(bucketId).status), uint256(PositionStatus.Active));
        assertEq(a.vault.group(bucketId).lpTokenId, lp);
        assertEq(a.venue.ownerOf(lp), address(a.vault));
        assertEq(_totalLogical(bucketId, true), 1000);
        assertEq(_totalLogical(bucketId, false), 1000);
        assertEq(a.migration.custodyEpoch(bucketId), 0);
        assertEq(a.migration.activePlan(bucketId), migrationId);
    }

    function testHistoricalRemoteRewardsCanUseANewProviderAfterPrincipalMovesOnward() public {
        uint256 bucketId = _mintAndActivate(1000, 1000);
        _hop(a, b, bucketId, 1000, 1000, 1, false);
        vm.chainId(b.chainId);
        b.venue.setFees(20, 40);
        b.vault.collectFees(bucketId, block.timestamp + 100);
        assertEq(b.fees.remoteIndividual(bucketId, address(b.asset0)), 32);
        assertEq(b.fees.remoteCollective(bucketId, address(b.asset0)), 4);
        // Five-percent compounding adds principal without changing equal membership.
        _hop(b, c, bucketId, 1002, 1001, 2, false);
        _rotateProvider(b);
        _rotateProvider(a);
        Route memory rewardRoute = _route(b, a, false);
        rewardRoute.sourceToken0 = address(b.asset0);
        rewardRoute.destinationToken0 = address(a.asset0);
        bytes32 rewardRouteId = _onboardRoute(b, a, rewardRoute);
        b.fees.bridgeRewards(bucketId, address(b.asset0), rewardRouteId);
        bytes32 rewardPacket = transport.latest();
        assertEq(b.fees.remoteIndividual(bucketId, address(b.asset0)), 0);
        assertEq(b.fees.remoteCollective(bucketId, address(b.asset0)), 0);
        vm.chainId(HOME_CHAIN);
        transport.deliver(rewardPacket);
        assertEq(a.rewards.claimable(canonicalNFTs[0], address(a.asset0)), 36);
        vm.prank(ALICE);
        assertEq(a.rewards.claim(canonicalNFTs[0], address(a.asset0)), 36);
        assertEq(_logicalAmount(c, bucketId, true), 1002);
        assertEq(_logicalAmount(c, bucketId, false), 1001);
        assertEq(_totalLogical(bucketId, true), 1002);
        assertEq(_totalLogical(bucketId, false), 1001);
        _assertIdentity(bucketId, 2000e18);
    }

    function testTwoNFTsShareOnePhysicalLPAndOneWholeBucketMigration() public {
        uint256 bucket = _mintAndActivate(1000, 1000);
        uint256 firstLP = a.vault.group(bucket).lpTokenId;
        assertEq(_mintAndActivate(1000, 1000), bucket);
        assertEq(a.vault.group(bucket).lpTokenId, firstLP);
        assertEq(a.venue.next(), 2);
        uint256 shares = a.vault.bucketTotalShares(bucket);
        _hop(a, b, bucket, 2000, 2000, 1, false);
        assertEq(b.venue.next(), 2);
        assertEq(b.vault.bucketTotalShares(bucket), shares);
        BridgeMessage memory accepted = b.receiver.acceptedMessage(
            transport.message(transport.latest()).migrationId);
        // Policy and governance operations never enqueue bridge messages. The
        // single principal packet represents both NFTs' immutable home shares.
        assertEq(accepted.bucketId, bucket);
        assertEq(accepted.totalShares, shares);
        assertEq(accepted.homePoolId, a.poolId);
        _assertIdentity(bucket, 4000e18);
    }

    function testReturnThenNewMembershipAndSatelliteRevisitUsesFreshFrozenShares() public {
        uint256 bucket = _mintAndActivate(1000, 1000);
        uint256 firstShares = a.vault.sharesOf(canonicalNFTs[0]);
        _hop(a, b, bucket, 1000, 1000, 1, false);
        _hop(b, a, bucket, 1000, 1000, 2, false);
        assertTrue(a.fees.remoteSettled(bucket));
        assertEq(_mintAndActivate(300, 300), bucket);
        assertEq(a.vault.sharesOf(canonicalNFTs[0]), firstShares);
        assertTrue(a.vault.bucketTotalShares(bucket) > firstShares);
        _hop(a, b, bucket, 1300, 1300, 3, false);
        assertEq(b.vault.bucketTotalShares(bucket), a.vault.bucketTotalShares(bucket));
        assertEq(b.vault.group(bucket).depositUSD, 2600e18);
        _assertIdentity(bucket, 2600e18);
    }

    function _deliverLegacyRewards(Bundle storage source, uint256 bucket, bool firstAsset) private {
        Route memory route = _route(source, a, false);
        address localToken = address(firstAsset ? source.asset0 : source.asset1);
        route.sourceToken0 = localToken;
        route.destinationToken0 = address(firstAsset ? a.asset0 : a.asset1);
        bytes32 routeId = _onboardRoute(source, a, route);
        source.fees.bridgeRewards(bucket, localToken, routeId);
        bytes32 packet = transport.latest();
        vm.chainId(HOME_CHAIN);
        transport.deliver(packet);
    }

    function testReturnedBucketWaitsForEveryFundedOldFeeBeforeAdmittingNewShares() public {
        uint256 bucket = _mintAndActivate(1000, 1000);
        uint256 firstNFT = canonicalNFTs[0];
        _hop(a, b, bucket, 1000, 1000, 1, false);
        vm.chainId(b.chainId);
        b.venue.setFees(20, 40);
        b.vault.collectFees(bucket, block.timestamp + 100);
        _hop(b, a, bucket, 1002, 1001, 2, false);
        assertFalse(a.fees.remoteSettled(bucket));
        vm.prank(ALICE);
        uint256 newcomer = a.vault.mintDormant{value: 0.05 ether}();
        _finalizeTraits(newcomer);
        canonicalNFTs.push(newcomer);
        vm.prank(ALICE);
        vm.expectRevert();
        a.vault.activate(newcomer, a.poolId, 300, 300, 1, block.timestamp + 100);
        vm.prank(ALICE);
        vm.expectRevert();
        a.vault.increase(firstNFT, 100, 100, 1, block.timestamp + 100);
        assertEq(a.vault.sharesOf(newcomer), 0);
        // Funded local fees remain claimable while late remote reserves keep
        // membership frozen. Principal is never an administrator's payout.
        a.venue.setFees(100, 100);
        a.vault.collectFees(bucket, block.timestamp + 100);
        vm.prank(ALICE);
        assertEq(a.rewards.claim(firstNFT, address(a.asset0)), 90);
        assertFalse(a.fees.remoteSettled(bucket));
        _deliverLegacyRewards(b, bucket, true);
        assertFalse(a.fees.remoteSettled(bucket));
        _deliverLegacyRewards(b, bucket, false);
        assertTrue(a.fees.remoteSettled(bucket));
        uint256 beforeClaimable = a.rewards.claimable(firstNFT, address(a.asset0));
        vm.prank(ALICE);
        a.vault.activate(newcomer, a.poolId, 300, 300, 1, block.timestamp + 100);
        assertEq(a.rewards.claimable(newcomer, address(a.asset0)), 0);
        assertEq(a.rewards.claimable(firstNFT, address(a.asset0)), beforeClaimable);
        assertTrue(a.vault.sharesOf(newcomer) != 0);
    }

    function testScheduledWholeBucketMoveFreezesContributionsUntilGovernanceCancels() public {
        uint256 bucket = _mintAndActivate(1000, 1000);
        uint256 firstNFT = canonicalNFTs[0];
        bytes32 routeId = _onboard(a, b, true);
        _govern(a, address(a.migration), abi.encodeCall(ZZZMigration.propose, (bucket, routeId)));
        bytes32 migrationId = a.migration.activePlan(bucket);
        vm.prank(ALICE);
        vm.expectRevert();
        a.vault.increase(firstNFT, 100, 100, 1, block.timestamp + 100);
        _govern(a, address(a.migration), abi.encodeCall(ZZZMigration.cancel, (migrationId)));
        vm.prank(ALICE);
        a.vault.increase(firstNFT, 100, 100, 1, block.timestamp + 100);
        assertEq(a.migration.activePlan(bucket), bytes32(0));
        assertEq(a.vault.group(bucket).depositUSD, 2200e18);
    }

    function testUnreservedDestinationRejectsThenRetriesTheSameFundedPacket() public {
        uint256 bucket = _mintAndActivate(1000, 1000);
        Route memory route = _route(a, b, true);
        TransportPolicy memory p = _policy(a, b);
        bytes32 policyId = _registerPolicy(a, p);
        bytes32 routeId = _register(a, route, policyId);
        _registerPolicy(b, p);
        _register(b, route, policyId);
        _govern(a, address(a.router), abi.encodeCall(ZZZBridgeRouter.setOutboundEnabled, (policyId, true)));
        _govern(a, address(a.migration), abi.encodeCall(ZZZMigration.propose, (bucket, routeId)));
        bytes32 migrationId = a.migration.activePlan(bucket);
        vm.warp(block.timestamp + a.migration.MIGRATION_DELAY());
        feed.set(1e8, block.timestamp, block.timestamp);
        a.migration.execute(migrationId, block.timestamp + 100);
        bytes32 packet = transport.latest();
        vm.chainId(b.chainId);
        vm.expectRevert();
        transport.deliver(packet);
        assertEq(uint256(b.vault.group(bucket).status), uint256(PositionStatus.None));
        assertEq(_totalLogical(bucket, true), 1000);
        assertEq(_totalLogical(bucket, false), 1000);
        _govern(b, address(b.vault), abi.encodeCall(ZZZVault.reservePool, (b.poolId, bucket)));
        transport.deliver(packet);
        b.receiver.finalize(migrationId, 1, block.timestamp + 100);
        assertEq(_logicalAmount(b, bucket, true), 1000);
        assertEq(_logicalAmount(b, bucket, false), 1000);
    }

}
