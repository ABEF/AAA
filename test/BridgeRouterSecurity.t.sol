// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZBridgeAdapter} from "../src/ZZZBridgeAdapter.sol";
import {ZZZBridgeRouter} from "../src/ZZZBridgeRouter.sol";
import {ZZZMigrationRegistry} from "../src/ZZZMigrationRegistry.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, PoolKey, PoolConfig, Route, BridgeMessage, MessageKind,
    TransportPolicy, TransportEnvelope} from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed, BoundDummy, TaxToken, ExtraTaxToken} from "./mocks/Mocks.sol";
import {RouterProviderMock, RouterVaultStub, RouterPoolsStub, RouterReceiverStub} from "./mocks/RouterMocks.sol";

/// @notice Real router/adapter/registry/timelock adversaries with explicitly fake
/// provider authentication, remote identities and receipt custody. No live SDK.
contract BridgeRouterSecurityTest is Test {
    ZZZAccessController private controller;
    ZZZBridgeRouter private router;
    ZZZBridgeAdapter private bridge;
    ZZZMigrationRegistry private registry;
    RouterVaultStub private vault;
    RouterReceiverStub private receiver;
    RouterProviderMock private provider;
    MockToken private token0;
    MockToken private token1;
    address private migration;
    bytes32 private outgoing;
    bytes32 private incoming;
    bytes32 private outgoingPolicy;
    bytes32 private incomingPolicy;
    uint256 private governanceSequence;
    uint256 private constant REMOTE = 77;
    address private constant REMOTE_ROUTER = address(0x7701);
    address private constant REMOTE_PROVIDER = address(0x7702);
    address private constant REMOTE_ADAPTER = address(0x7711);
    address private constant REMOTE_VAULT = address(0x7721);
    address private constant REMOTE_RECEIVER = address(0x7731);
    address private constant REMOTE_TOKEN0 = address(0x7741);
    address private constant REMOTE_TOKEN1 = address(0x7742);
    bytes32 private constant CONFIG = keccak256("reviewed mock channel configuration");
    bytes32 private constant REMOTE_CODE = keccak256("reviewed remote provider code");
    bytes32 private constant POOL = keccak256("local destination fixture pool");

    function setUp() public {
        vm.chainId(1);
        vm.warp(1_000_000);
        address[] memory actors = new address[](1); actors[0] = address(this);
        controller = new ZZZAccessController(1 days, actors, actors, address(this), address(this));
        token0 = new MockToken(18); token1 = new MockToken(18);
        vault = new RouterVaultStub(address(controller), block.chainid);
        receiver = new RouterReceiverStub(address(controller));
        router = new ZZZBridgeRouter(address(controller));
        bridge = new ZZZBridgeAdapter(address(controller), address(router));
        registry = new ZZZMigrationRegistry(address(controller));
        provider = new RouterProviderMock(address(router), CONFIG);
        migration = address(new BoundDummy(address(controller)));
        ZZZOracle oracle = new ZZZOracle(address(controller), address(0));
        MockFeed feed = new MockFeed(8, 1e8);
        oracle.setFeed(address(token0), address(feed), 3600);
        oracle.setFeed(address(token1), address(feed), 3600);
        PoolConfig memory config;
        config.key = PoolKey(address(token0), address(token1), 3000, 60, address(0));
        config.operationsEnabled = true;
        RouterPoolsStub pools = new RouterPoolsStub(address(controller), config);
        controller.bind(Ids.VAULT, address(vault));
        controller.bind(Ids.RECEIVER, address(receiver));
        controller.bind(Ids.TRANSPORT, address(router));
        controller.bind(Ids.BRIDGE, address(bridge));
        controller.bind(Ids.ROUTES, address(registry));
        controller.bind(Ids.MIGRATION, migration);
        controller.bind(Ids.ORACLE, address(oracle));
        controller.bind(Ids.POOLS, address(pools));
        bytes32[8] memory other = [Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP,
            Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK];
        for (uint256 i; i < other.length; ++i) controller.bind(other[i], address(new BoundDummy(address(controller))));
        receiver.setRegistry(address(registry));
        outgoingPolicy = router.registerPolicy(_policy(true, address(provider), keccak256("provider-v1")));
        incomingPolicy = router.registerPolicy(_policy(false, address(provider), keccak256("provider-v1")));
        outgoing = registry.add(_route(true), outgoingPolicy);
        incoming = registry.add(_route(false), incomingPolicy);
        CanonicalFixture.bind(address(controller));
        controller.seal();
    }

    function _policy(bool source, address localProvider, bytes32 providerId) private view returns (TransportPolicy memory p) {
        p.providerId = providerId;
        p.sourceChain = source ? block.chainid : REMOTE;
        p.sourceRouter = source ? address(router) : REMOTE_ROUTER;
        p.sourceProvider = source ? localProvider : REMOTE_PROVIDER;
        p.sourceCodeHash = source ? localProvider.codehash : REMOTE_CODE;
        p.sourceConfigurationHash = CONFIG;
        p.destinationChain = source ? REMOTE : block.chainid;
        p.destinationRouter = source ? REMOTE_ROUTER : address(router);
        p.destinationProvider = source ? REMOTE_PROVIDER : localProvider;
        p.destinationCodeHash = source ? REMOTE_CODE : localProvider.codehash;
        p.destinationConfigurationHash = CONFIG;
        p.channelId = keccak256("immutable mock channel");
        p.reviewHash = keccak256("explicit test-only review record");
    }

    function _route(bool source) private view returns (Route memory r) {
        r.sourceChain = source ? block.chainid : REMOTE;
        r.sourceAdapter = source ? address(bridge) : REMOTE_ADAPTER;
        r.sourceVault = source ? address(vault) : REMOTE_VAULT;
        r.sourceReceiver = source ? address(receiver) : REMOTE_RECEIVER;
        r.destinationChain = source ? REMOTE : block.chainid;
        r.destinationAdapter = source ? REMOTE_ADAPTER : address(bridge);
        r.destinationVault = source ? REMOTE_VAULT : address(vault);
        r.destinationReceiver = source ? REMOTE_RECEIVER : address(receiver);
        r.destinationPool = POOL;
        r.sourceToken0 = source ? address(token0) : REMOTE_TOKEN0;
        r.sourceToken1 = source ? address(token1) : REMOTE_TOKEN1;
        r.destinationToken0 = source ? REMOTE_TOKEN0 : address(token0);
        r.destinationToken1 = source ? REMOTE_TOKEN1 : address(token1);
        r.token0Decimals = 18; r.token1Decimals = 18;
    }

    function _govern(address target, bytes memory data) private {
        bytes32 salt = keccak256(abi.encode(++governanceSequence, target, data));
        controller.schedule(target, 0, data, bytes32(0), salt, controller.getMinDelay());
        vm.warp(block.timestamp + controller.getMinDelay());
        controller.execute(target, 0, data, bytes32(0), salt);
    }

    function _enable() private {
        _govern(address(router), abi.encodeCall(router.setOutboundEnabled, (outgoingPolicy, true)));
    }

    function _message(bytes32 routeId, uint256 nonce) private view returns (BridgeMessage memory m) {
        m.version = 3; m.kind = MessageKind.Principal; m.routeId = routeId; m.principalRouteId = routeId;
        m.nonce = nonce; m.bucketId = 42; m.migrationId = keccak256(abi.encode(routeId, nonce));
        m.homeChain = block.chainid; m.homeVault = address(vault); m.homeReceiver = address(receiver);
        m.depositUSD = 1000e18; m.migrationEpoch = 1;
        m.previousChain = routeId == outgoing ? block.chainid : REMOTE;
        m.previousVault = routeId == outgoing ? address(vault) : REMOTE_VAULT;
        m.previousReceiver = routeId == outgoing ? address(receiver) : REMOTE_RECEIVER;
        m.canonicalToken0 = address(token0); m.canonicalToken1 = address(token1);
        m.amount0 = 13; m.amount1 = 29;
    }

    function _fundSource(BridgeMessage memory m) private {
        token0.mint(migration, m.amount0); token1.mint(migration, m.amount1);
        vm.startPrank(migration);
        token0.approve(address(bridge), m.amount0); token1.approve(address(bridge), m.amount1);
        vm.stopPrank();
    }

    function _send(BridgeMessage memory m) private returns (bytes32) {
        _fundSource(m); vm.prank(migration); return bridge.send(m);
    }

    function _vectors(BridgeMessage memory m) private view returns (address[] memory tokens, uint256[] memory amounts) {
        tokens = new address[](2); amounts = new uint256[](2);
        tokens[0] = address(token0); tokens[1] = address(token1);
        amounts[0] = m.amount0; amounts[1] = m.amount1;
    }

    function _envelope(bytes32 policyId, BridgeMessage memory m) private pure returns (bytes memory) {
        return abi.encode(TransportEnvelope(1, policyId, abi.encode(m)));
    }

    function _fundProvider(RouterProviderMock target, BridgeMessage memory m) private {
        token0.mint(address(target), m.amount0); token1.mint(address(target), m.amount1);
    }

    function _deliver(RouterProviderMock target, bytes32 policyId, BridgeMessage memory m) private {
        (address[] memory tokens, uint256[] memory amounts) = _vectors(m);
        target.deliver(REMOTE, REMOTE_ROUTER, tokens, amounts, _envelope(policyId, m));
    }

    function testSealedRoutesStartOutboundDisabled() public {
        assertTrue(controller.isSealed()); assertFalse(router.outboundEnabled(outgoingPolicy));
        assertFalse(router.canSend(outgoing));
        BridgeMessage memory m = _message(outgoing, 0); _fundSource(m);
        vm.prank(migration); vm.expectRevert(); bridge.send(m);
        assertEq(bridge.nonce(), 0); assertEq(token0.balanceOf(migration), 13);
        assertEq(token0.balanceOf(address(provider)), 0);
    }

    function testSealRejectsBridgeWhoseFixedEndpointIsAnotherRouter() public {
        address[] memory actors = new address[](1); actors[0] = address(this);
        ZZZAccessController isolated = new ZZZAccessController(1 days, actors, actors, address(this), address(this));
        ZZZBridgeRouter expected = new ZZZBridgeRouter(address(isolated));
        ZZZBridgeRouter different = new ZZZBridgeRouter(address(isolated));
        ZZZBridgeAdapter mismatch = new ZZZBridgeAdapter(address(isolated), address(different));
        bytes32[16] memory ids = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP,
            Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION, Ids.BRIDGE,
            Ids.RECEIVER, Ids.ORACLE, Ids.POOLS, Ids.ROUTES, Ids.TRANSPORT];
        for (uint256 i; i < ids.length; ++i) {
            address implementation = ids[i] == Ids.BRIDGE ? address(mismatch) : ids[i] == Ids.TRANSPORT
                ? address(expected) : address(new BoundDummy(address(isolated)));
            isolated.bind(ids[i], implementation);
        }
        CanonicalFixture.bind(address(isolated));
        vm.expectRevert(); isolated.seal(); assertFalse(isolated.isSealed());
    }

    function testOnlyTimelockCanEnableAfterSeal() public {
        vm.expectRevert(); router.setOutboundEnabled(outgoingPolicy, true);
        bytes memory data = abi.encodeCall(router.setOutboundEnabled, (outgoingPolicy, true));
        bytes32 salt = keccak256("enable after notice");
        controller.schedule(address(router), 0, data, bytes32(0), salt, 1 days);
        vm.expectRevert(); controller.execute(address(router), 0, data, bytes32(0), salt);
        assertFalse(router.canSend(outgoing));
        vm.warp(block.timestamp + 1 days); controller.execute(address(router), 0, data, bytes32(0), salt);
        assertTrue(router.canSend(outgoing));
    }

    function testNewProviderPolicyNeedsTimelockAndNewRouteIdentity() public {
        RouterProviderMock second = new RouterProviderMock(address(router), CONFIG);
        TransportPolicy memory p = _policy(true, address(second), keccak256("provider-v2"));
        bytes32 id = keccak256(abi.encode(p));
        vm.expectRevert(); router.registerPolicy(p);
        _govern(address(router), abi.encodeCall(router.registerPolicy, (p)));
        assertTrue(router.policyExists(id)); assertFalse(router.outboundEnabled(id));
        Route memory r = _route(true);
        bytes32 newRoute = keccak256(abi.encode(r, id));
        _govern(address(registry), abi.encodeCall(registry.add, (r, id)));
        assertTrue(registry.exists(newRoute)); assertTrue(newRoute != outgoing);
        assertEq(registry.transportPolicyId(outgoing), outgoingPolicy);
        assertEq(registry.transportPolicyId(newRoute), id);
        _enable(); _send(_message(outgoing, 0));
        assertEq(provider.sends(), 1); assertEq(second.sends(), 0);
    }

    function testExistingPolicyCannotBeReRegistered() public {
        TransportPolicy memory p = _policy(true, address(provider), keccak256("provider-v1"));
        bytes memory data = abi.encodeCall(router.registerPolicy, (p)); bytes32 salt = keccak256("duplicate");
        controller.schedule(address(router), 0, data, bytes32(0), salt, 1 days);
        vm.warp(block.timestamp + 1 days);
        vm.expectRevert(); controller.execute(address(router), 0, data, bytes32(0), salt);
        assertEq(registry.transportPolicyId(outgoing), outgoingPolicy);
    }

    function _rejectedPolicy(TransportPolicy memory p) private {
        bytes memory data = abi.encodeCall(router.registerPolicy, (p));
        bytes32 salt = keccak256(abi.encode(++governanceSequence, data));
        controller.schedule(address(router), 0, data, bytes32(0), salt, 1 days);
        vm.warp(block.timestamp + 1 days);
        vm.expectRevert(); controller.execute(address(router), 0, data, bytes32(0), salt);
        assertFalse(router.policyExists(keccak256(abi.encode(p))));
    }

    function testWrongLocalProviderRouterAndCodeHashCannotBeApproved() public {
        RouterProviderMock wrong = new RouterProviderMock(address(0xBAD), CONFIG);
        _rejectedPolicy(_policy(true, address(wrong), keccak256("wrong bound router")));
        TransportPolicy memory p = _policy(true, address(provider), keccak256("wrong code"));
        p.sourceCodeHash = keccak256("unrelated reviewed runtime"); _rejectedPolicy(p);
    }

    function testZeroDomainAndMissingReviewCannotBeApproved() public {
        TransportPolicy memory p = _policy(true, address(provider), keccak256("zero domain"));
        p.sourceChain = 0; _rejectedPolicy(p);
        p = _policy(true, address(provider), keccak256("missing review"));
        p.reviewHash = bytes32(0); _rejectedPolicy(p);
    }

    function testOnlyBoundBridgeCanSendThroughRouter() public {
        _enable(); BridgeMessage memory m = _message(outgoing, 1);
        (address[] memory tokens, uint256[] memory amounts) = _vectors(m);
        vm.expectRevert(); router.send(REMOTE, REMOTE_ADAPTER, tokens, amounts, abi.encode(m));
    }

    function testOutgoingFundingEnvelopeAndAllowanceResets() public {
        _enable(); assertTrue(_send(_message(outgoing, 0)) != bytes32(0));
        TransportEnvelope memory e = abi.decode(provider.lastEnvelope(), (TransportEnvelope));
        BridgeMessage memory m = abi.decode(e.payload, (BridgeMessage));
        assertEq(e.version, 1); assertEq(e.policyId, outgoingPolicy); assertEq(m.version, 3); assertEq(m.nonce, 1);
        assertEq(provider.lastDestinationRouter(), REMOTE_ROUTER);
        assertEq(provider.lastDestinationProvider(), REMOTE_PROVIDER);
        assertEq(token0.balanceOf(address(provider)), 13); assertEq(token1.balanceOf(address(provider)), 29);
        assertEq(token0.balanceOf(address(router)), 0); assertEq(token0.balanceOf(address(bridge)), 0);
        assertEq(token0.allowance(address(router), address(provider)), 0);
        assertEq(token1.allowance(address(bridge), address(router)), 0);
    }

    function testTypedRewardAndAcknowledgementChannelsUseOnlyDeclaredFunding() public {
        _enable();
        Route memory reward = _route(true); reward.sourceToken1 = address(0); reward.destinationToken1 = address(0);
        bytes32 rewardId = keccak256(abi.encode(reward, outgoingPolicy));
        _govern(address(registry), abi.encodeCall(registry.add, (reward, outgoingPolicy)));
        BridgeMessage memory m = _message(rewardId, 0); m.kind = MessageKind.Reward;
        m.amount0 = 80; m.amount1 = 0; m.individual = 50; m.collective = 30;
        address feeModule = controller.module(Ids.FEES);
        token0.mint(feeModule, 80);
        vm.startPrank(feeModule); token0.approve(address(bridge), 80); bridge.send(m); vm.stopPrank();
        assertEq(token0.balanceOf(address(provider)), 80); assertEq(token1.balanceOf(address(provider)), 0);
        Route memory ack = reward; ack.sourceToken0 = address(0); ack.destinationToken0 = address(0);
        bytes32 ackId = keccak256(abi.encode(ack, outgoingPolicy));
        _govern(address(registry), abi.encodeCall(registry.add, (ack, outgoingPolicy)));
        m = _message(ackId, 0); m.kind = MessageKind.Acknowledgement; m.amount0 = 0; m.amount1 = 0;
        vm.prank(address(receiver)); bridge.send(m);
        assertEq(provider.sends(), 2); assertEq(token0.balanceOf(address(provider)), 80);
        assertEq(token1.balanceOf(address(provider)), 0);
    }

    function testPrincipalCanContainOneZeroValuedTokenLeg() public {
        _enable(); BridgeMessage memory m = _message(outgoing, 0); m.amount0 = 0; _send(m);
        assertEq(token0.balanceOf(address(provider)), 0); assertEq(token1.balanceOf(address(provider)), 29);
        assertEq(token0.allowance(address(router), address(provider)), 0);
    }

    function testProviderPartialConsumptionRollsBackAllSourceFundsAndNonce() public {
        _enable(); provider.setConsumeBps(5000);
        BridgeMessage memory m = _message(outgoing, 0); _fundSource(m);
        vm.prank(migration); vm.expectRevert(); bridge.send(m);
        assertEq(bridge.nonce(), 0); assertEq(provider.sends(), 0);
        assertEq(token0.balanceOf(migration), 13); assertEq(token1.balanceOf(migration), 29);
        assertEq(token0.allowance(address(router), address(provider)), 0);
    }

    function _preloadCustody() private {
        token0.mint(address(bridge), 71); token1.mint(address(bridge), 73);
        token0.mint(address(router), 101); token1.mint(address(router), 103);
    }

    function _assertCustodyDonationsUnchanged() private view {
        assertEq(token0.balanceOf(address(bridge)), 71); assertEq(token1.balanceOf(address(bridge)), 73);
        assertEq(token0.balanceOf(address(router)), 101); assertEq(token1.balanceOf(address(router)), 103);
        assertEq(token0.allowance(address(router), address(provider)), 0);
        assertEq(token1.allowance(address(bridge), address(router)), 0);
    }

    function testSourcePreexistingDonationsArePreservedAcrossSuccessfulDispatch() public {
        _enable(); _preloadCustody(); _send(_message(outgoing, 0));
        _assertCustodyDonationsUnchanged();
        assertEq(token0.balanceOf(address(provider)), 13); assertEq(token1.balanceOf(address(provider)), 29);
    }

    function testUnderfundedSourceCannotUseCustodyDonations() public {
        _enable(); _preloadCustody(); BridgeMessage memory m = _message(outgoing, 0);
        vm.startPrank(migration);
        token0.approve(address(bridge), m.amount0); token1.approve(address(bridge), m.amount1);
        vm.expectRevert(); bridge.send(m); vm.stopPrank();
        _assertCustodyDonationsUnchanged(); assertEq(bridge.nonce(), 0); assertEq(provider.sends(), 0);
    }

    function testProviderReceiptCannotCoverPartialConsumptionWithDonations() public {
        _enable(); _preloadCustody(); provider.setConsumeBps(5000);
        BridgeMessage memory m = _message(outgoing, 0); _fundSource(m);
        vm.prank(migration); vm.expectRevert(); bridge.send(m);
        _assertCustodyDonationsUnchanged(); assertEq(bridge.nonce(), 0); assertEq(provider.sends(), 0);
        assertEq(token0.balanceOf(migration), 13); assertEq(token1.balanceOf(migration), 29);
    }

    function _assertRouterRejectsTaxedPull(MockToken taxed) private {
        // Admit a separate test token through the real governance path, then call
        // the router as its sole fixed caller to isolate its own ExactToken check.
        ZZZOracle oracle = ZZZOracle(controller.module(Ids.ORACLE));
        MockFeed feed = new MockFeed(8, 1e8);
        _govern(address(oracle), abi.encodeCall(oracle.setFeed, (address(taxed), address(feed), uint32(3600))));
        Route memory r = _route(true); r.sourceToken0 = address(taxed);
        bytes32 routeId = keccak256(abi.encode(r, outgoingPolicy));
        _govern(address(registry), abi.encodeCall(registry.add, (r, outgoingPolicy)));
        _enable();
        BridgeMessage memory m = _message(routeId, 1); m.amount0 = 100;
        taxed.mint(address(bridge), 200); taxed.mint(address(router), 41);
        token1.mint(address(bridge), m.amount1);
        address[] memory tokens = new address[](2); uint256[] memory amounts = new uint256[](2);
        tokens[0] = address(taxed); tokens[1] = address(token1); amounts[0] = m.amount0; amounts[1] = m.amount1;
        vm.startPrank(address(bridge));
        taxed.approve(address(router), m.amount0); token1.approve(address(router), m.amount1);
        vm.expectRevert(); router.send(REMOTE, REMOTE_ADAPTER, tokens, amounts, abi.encode(m));
        vm.stopPrank();
        assertEq(taxed.balanceOf(address(bridge)), 200); assertEq(taxed.balanceOf(address(router)), 41);
        assertEq(taxed.balanceOf(address(provider)), 0); assertEq(provider.sends(), 0);
        assertEq(taxed.allowance(address(router), address(provider)), 0);
    }

    function testRouterRejectsRecipientTaxDespitePreexistingDonation() public {
        _assertRouterRejectsTaxedPull(new TaxToken());
    }

    function testRouterRejectsExtraSenderTaxDespitePreexistingDonation() public {
        _assertRouterRejectsTaxedPull(new ExtraTaxToken());
    }

    function testZeroReceiptRollsBackFunding() public {
        _enable(); provider.setZeroReceipt(true);
        BridgeMessage memory m = _message(outgoing, 0); _fundSource(m);
        vm.prank(migration); vm.expectRevert(); bridge.send(m);
        assertEq(bridge.nonce(), 0); assertEq(token0.balanceOf(migration), 13);
    }

    function testProviderReentryCannotReceiveDuringSend() public {
        _enable(); provider.setAttemptReentry(true); _send(_message(outgoing, 0));
        assertFalse(provider.reentrySucceeded()); assertEq(receiver.receipts(), 0);
    }

    function testProviderConfigurationMutationDuringSendRollsBackEntireDispatch() public {
        _enable(); provider.setMutateDuringSend(true);
        BridgeMessage memory m = _message(outgoing, 0); _fundSource(m);
        vm.prank(migration); vm.expectRevert(); bridge.send(m);
        assertEq(bridge.nonce(), 0); assertEq(provider.sends(), 0);
        assertEq(provider.configurationHash(bytes32(0)), CONFIG);
        assertEq(token0.balanceOf(migration), 13); assertEq(token1.balanceOf(migration), 29);
        assertEq(token0.allowance(address(router), address(provider)), 0);
    }

    function testChangedConfigurationBlocksSendingWithoutRebinding() public {
        _enable(); provider.setConfigurationHash(keccak256("changed channel"));
        assertFalse(router.canSend(outgoing));
        BridgeMessage memory m = _message(outgoing, 0); _fundSource(m);
        vm.prank(migration); vm.expectRevert(); bridge.send(m);
        assertEq(bridge.nonce(), 0); assertEq(token0.balanceOf(migration), 13);
    }

    function testChangedProviderCodeBlocksSending() public {
        _enable(); vm.etch(address(provider), hex"00"); assertFalse(router.canSend(outgoing));
        BridgeMessage memory m = _message(outgoing, 0); _fundSource(m);
        vm.prank(migration); vm.expectRevert(); bridge.send(m); assertEq(bridge.nonce(), 0);
    }

    function testChangedDestinationConfigurationRejectsIncomingWithoutConsumingNonce() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m);
        provider.setConfigurationHash(keccak256("changed destination configuration"));
        vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        assertEq(receiver.receipts(), 0); assertEq(token0.balanceOf(address(provider)), 13);
        provider.setConfigurationHash(CONFIG); _deliver(provider, incomingPolicy, m);
        assertEq(receiver.receipts(), 1);
    }

    function testChangedDestinationCodeRejectedEvenForBoundProviderAddress() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m);
        (address[] memory tokens, uint256[] memory amounts) = _vectors(m);
        vm.etch(address(provider), hex"00");
        vm.prank(address(provider)); vm.expectRevert();
        router.onProviderMessage(REMOTE, REMOTE_ROUTER, tokens, amounts, _envelope(incomingPolicy, m));
        assertEq(receiver.receipts(), 0); assertEq(token0.balanceOf(address(provider)), 13);
    }

    function testAuthenticatedIncomingRetainsFundingWhileOutboundDisabled() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m); _deliver(provider, incomingPolicy, m);
        assertEq(receiver.receipts(), 1); assertEq(token0.balanceOf(address(receiver)), 13);
        assertEq(token1.balanceOf(address(receiver)), 29); assertFalse(router.outboundEnabled(incomingPolicy));
        assertEq(token0.balanceOf(address(router)), 0); assertEq(token0.allowance(address(router), address(bridge)), 0);
        assertEq(token1.allowance(address(bridge), address(receiver)), 0);
    }

    function testIncomingSurvivesStrategyPauseAndRouteDisable() public {
        _govern(address(registry), abi.encodeCall(registry.setEnabled, (incoming, false)));
        controller.setPaused(true);
        BridgeMessage memory m = _message(incoming, 2); _fundProvider(provider, m); _deliver(provider, incomingPolicy, m);
        assertEq(receiver.receipts(), 1); assertEq(token0.balanceOf(address(receiver)), 13);
    }

    function testWrongProviderCallerRejected() public {
        BridgeMessage memory m = _message(incoming, 1); (address[] memory tokens, uint256[] memory amounts) = _vectors(m);
        vm.expectRevert(); router.onProviderMessage(REMOTE, REMOTE_ROUTER, tokens, amounts, _envelope(incomingPolicy, m));
        assertEq(receiver.receipts(), 0);
    }

    function testWrongAuthenticatedOriginChainOrRouterRejected() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m);
        (address[] memory tokens, uint256[] memory amounts) = _vectors(m);
        vm.expectRevert(); provider.deliver(REMOTE + 1, REMOTE_ROUTER, tokens, amounts, _envelope(incomingPolicy, m));
        vm.expectRevert(); provider.deliver(REMOTE, address(0xBAD), tokens, amounts, _envelope(incomingPolicy, m));
        assertEq(receiver.receipts(), 0); assertEq(token0.balanceOf(address(provider)), 13);
    }

    function testActualTokenOrderAndAmountsCannotDifferFromEconomicRoute() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m);
        (address[] memory tokens, uint256[] memory amounts) = _vectors(m);
        tokens[0] = address(token1); tokens[1] = address(token0);
        vm.expectRevert(); provider.deliver(REMOTE, REMOTE_ROUTER, tokens, amounts, _envelope(incomingPolicy, m));
        (tokens, amounts) = _vectors(m); amounts[0]--;
        vm.expectRevert(); provider.deliver(REMOTE, REMOTE_ROUTER, tokens, amounts, _envelope(incomingPolicy, m));
        assertEq(receiver.receipts(), 0);
    }

    function testUnfundedDestinationDeliveryCanRetryWithoutConsumedNonce() public {
        BridgeMessage memory m = _message(incoming, 1);
        vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        assertFalse(bridge.processed(keccak256(abi.encode(REMOTE, REMOTE_ADAPTER, uint256(1)))));
        _fundProvider(provider, m); _deliver(provider, incomingPolicy, m); assertEq(receiver.receipts(), 1);
    }

    function testDestinationPreexistingDonationsPreservedAcrossFundedReceipt() public {
        _preloadCustody(); BridgeMessage memory m = _message(incoming, 1);
        _fundProvider(provider, m); _deliver(provider, incomingPolicy, m);
        _assertCustodyDonationsUnchanged(); assertEq(receiver.receipts(), 1);
        assertEq(token0.balanceOf(address(receiver)), 13); assertEq(token1.balanceOf(address(receiver)), 29);
        assertEq(token0.allowance(address(router), address(bridge)), 0);
        assertEq(token1.allowance(address(bridge), address(receiver)), 0);
    }

    function testUnderfundedIncomingCannotUseCustodyDonationsAndCanRetry() public {
        _preloadCustody(); BridgeMessage memory m = _message(incoming, 1);
        vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        _assertCustodyDonationsUnchanged(); assertEq(receiver.receipts(), 0);
        bytes32 delivery = keccak256(abi.encode(REMOTE, REMOTE_ADAPTER, uint256(1)));
        assertFalse(router.processed(delivery)); assertFalse(bridge.processed(delivery));
        _fundProvider(provider, m); _deliver(provider, incomingPolicy, m);
        _assertCustodyDonationsUnchanged(); assertEq(receiver.receipts(), 1);
        assertTrue(router.processed(delivery)); assertTrue(bridge.processed(delivery));
    }

    function testReceiverFailurePreservesFundingAndAllowsExactRetry() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m); receiver.setReject(true);
        vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        assertEq(token0.balanceOf(address(provider)), 13); assertEq(token0.balanceOf(address(router)), 0);
        receiver.setReject(false); _deliver(provider, incomingPolicy, m); assertEq(receiver.receipts(), 1);
    }

    function testDestinationHandoffConfigurationMutationRollsBackFundingAndReplay() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m);
        receiver.setMutationProvider(address(provider));
        vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        bytes32 delivery = keccak256(abi.encode(REMOTE, REMOTE_ADAPTER, uint256(1)));
        assertFalse(bridge.processed(delivery)); assertFalse(router.processed(delivery));
        assertEq(receiver.receipts(), 0); assertEq(token0.balanceOf(address(provider)), 13);
        assertEq(token0.balanceOf(address(receiver)), 0); assertEq(provider.configurationHash(bytes32(0)), CONFIG);
        assertEq(token0.allowance(address(router), address(bridge)), 0);
        receiver.setMutationProvider(address(0)); _deliver(provider, incomingPolicy, m);
        assertTrue(bridge.processed(delivery)); assertTrue(router.processed(delivery)); assertEq(receiver.receipts(), 1);
    }

    function testEnvelopePolicyCannotReplaceTheRoutesImmutableBinding() public {
        TransportPolicy memory p = _policy(false, address(provider), keccak256("unbound new policy"));
        bytes32 otherPolicy = keccak256(abi.encode(p));
        _govern(address(router), abi.encodeCall(router.registerPolicy, (p)));
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m);
        vm.expectRevert(); _deliver(provider, otherPolicy, m);
        assertEq(registry.transportPolicyId(incoming), incomingPolicy);
        assertEq(receiver.receipts(), 0); assertEq(token0.balanceOf(address(provider)), 13);
    }

    function testOldPolicyReceiptWorksAfterNewProviderOnboardingAndReplayIsGlobal() public {
        RouterProviderMock second = new RouterProviderMock(address(router), CONFIG);
        TransportPolicy memory p = _policy(false, address(second), keccak256("provider-v2"));
        bytes32 policyId = keccak256(abi.encode(p));
        _govern(address(router), abi.encodeCall(router.registerPolicy, (p)));
        Route memory r = _route(false); bytes32 newRoute = keccak256(abi.encode(r, policyId));
        _govern(address(registry), abi.encodeCall(registry.add, (r, policyId)));
        _govern(address(registry), abi.encodeCall(registry.setEnabled, (incoming, false)));
        _govern(address(registry), abi.encodeCall(registry.setEnabled, (newRoute, false)));
        BridgeMessage memory old = _message(incoming, 9); _fundProvider(provider, old); _deliver(provider, incomingPolicy, old);
        BridgeMessage memory altered = _message(newRoute, 9); _fundProvider(second, altered);
        vm.expectRevert(); _deliver(second, policyId, altered);
        assertEq(receiver.receipts(), 1); assertEq(token0.balanceOf(address(second)), 13);
        altered.nonce = 10; altered.migrationId = keccak256("new authenticated origin nonce");
        _deliver(second, policyId, altered); assertEq(receiver.receipts(), 2);
    }

    function testInvalidEnvelopeAndPayloadVersionsAndZeroNonceRejected() public {
        BridgeMessage memory m = _message(incoming, 1); _fundProvider(provider, m);
        (address[] memory tokens, uint256[] memory amounts) = _vectors(m);
        bytes memory badEnvelope = abi.encode(TransportEnvelope(2, incomingPolicy, abi.encode(m)));
        vm.expectRevert(); provider.deliver(REMOTE, REMOTE_ROUTER, tokens, amounts, badEnvelope);
        m.version = 1; vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        m.version = 3; m.nonce = 0; vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        assertEq(receiver.receipts(), 0);
    }

    function testFuzzIncomingExactFundingAndReplay(uint96 amount0, uint96 amount1, uint64 nonce) public {
        amount0 = uint96(bound(amount0, 1, 1e24)); amount1 = uint96(bound(amount1, 1, 1e24));
        nonce = uint64(bound(nonce, 1, type(uint64).max));
        BridgeMessage memory m = _message(incoming, nonce); m.amount0 = amount0; m.amount1 = amount1;
        _fundProvider(provider, m); _deliver(provider, incomingPolicy, m);
        assertEq(token0.balanceOf(address(receiver)), amount0); assertEq(token1.balanceOf(address(receiver)), amount1);
        _fundProvider(provider, m); vm.expectRevert(); _deliver(provider, incomingPolicy, m);
        assertEq(receiver.receipts(), 1); assertEq(token0.balanceOf(address(provider)), amount0);
    }
}
