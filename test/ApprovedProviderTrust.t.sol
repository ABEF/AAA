// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZBridgeAdapter} from "../src/ZZZBridgeAdapter.sol";
import {ZZZBridgeRouter} from "../src/ZZZBridgeRouter.sol";
import {ZZZMigrationRegistry} from "../src/ZZZMigrationRegistry.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, Route, BridgeMessage, MessageKind, TransportPolicy} from "../src/libraries/ZZZTypes.sol";
import {MockToken, MockFeed, BoundDummy} from "./mocks/Mocks.sol";
import {RouterVaultStub} from "./mocks/RouterMocks.sol";

/// @dev DELIBERATELY MALICIOUS TEST PROVIDER. Its immutable code/getters match
/// every approved pin, but exact source consumption is theft, not settlement.
/// It has no destination call, escrow, backing, delivery or refund mechanism.
contract NondeliveringApprovedProvider {
    address public immutable router;
    address public immutable thief;
    bytes32 public immutable channelConfiguration;
    uint256 public sends;
    bytes32 public lastPolicy;
    uint256 public lastDestinationChain;
    address public lastDestinationProvider;
    address public lastDestinationRouter;
    bytes32 public lastEnvelopeHash;

    constructor(address approvedRouter, address recipient, bytes32 configuration) {
        router = approvedRouter;
        thief = recipient;
        channelConfiguration = configuration;
    }

    function configurationHash(bytes32) external view returns (bytes32) { return channelConfiguration; }

    function send(bytes32 policyId, uint256 destinationChain, address destinationProvider, address destinationRouter,
        address[] calldata tokens, uint256[] calldata amounts, bytes calldata envelope)
        external payable returns (bytes32 receipt) {
        require(msg.sender == router, "only approved router");
        for (uint256 i; i < tokens.length; ++i) {
            require(IERC20(tokens[i]).transferFrom(msg.sender, thief, amounts[i]), "exact theft failed");
        }
        lastPolicy = policyId;
        lastDestinationChain = destinationChain;
        lastDestinationProvider = destinationProvider;
        lastDestinationRouter = destinationRouter;
        lastEnvelopeHash = keccak256(envelope);
        return bytes32(++sends);
    }
}

/// @notice Trust-boundary demonstration, NOT a rejected unauthorized attack.
/// Real controller/timelock, adapter, router, registry and Oracle admit a pinned
/// malicious provider. Tokens, bound migration/Vault and remote identities are
/// fixtures; this does not exercise a production migration or live bridge SDK.
/// A successful source receipt is not proof of funded permanent destination custody.
contract ApprovedProviderTrustTest is Test {
    ZZZAccessController private controller;
    ZZZBridgeRouter private router;
    ZZZBridgeAdapter private bridge;
    ZZZMigrationRegistry private registry;
    NondeliveringApprovedProvider private provider;
    MockToken private token0;
    MockToken private token1;
    address private migration;
    address private vault;
    address private receiver;
    uint256 private governanceSequence;

    address private constant THIEF = address(0xBAD);
    uint256 private constant REMOTE_CHAIN = 77;
    address private constant REMOTE_ROUTER = address(0x7701);
    address private constant REMOTE_PROVIDER = address(0x7702);
    address private constant REMOTE_ADAPTER = address(0x7703);
    address private constant REMOTE_VAULT = address(0x7704);
    address private constant REMOTE_RECEIVER = address(0x7705);
    address private constant REMOTE_TOKEN0 = address(0x7706);
    address private constant REMOTE_TOKEN1 = address(0x7707);
    bytes32 private constant CONFIGURATION = keccak256("stable getters do not prove honest custody");
    bytes32 private constant CHANNEL = keccak256("test-only approved channel");
    bytes32 private constant POOL = keccak256("test-only economic pool");

    function setUp() public {
        if (block.timestamp < 2) vm.warp(1000000);
        vm.chainId(1);
        vm.warp(1_000_000);
        address[] memory governance = new address[](1);
        governance[0] = address(this);
        controller = new ZZZAccessController(0, governance, governance, address(this), address(this));
        router = new ZZZBridgeRouter(address(controller));
        bridge = new ZZZBridgeAdapter(address(controller), address(router));
        registry = new ZZZMigrationRegistry(address(controller));
        provider = new NondeliveringApprovedProvider(address(router), THIEF, CONFIGURATION);
        token0 = new MockToken(18);
        token1 = new MockToken(18);
        ZZZOracle oracle = new ZZZOracle(address(controller), address(0));
        MockFeed feed = new MockFeed(8, 1e8);
        oracle.setFeed(address(token0), address(feed), 3600);
        oracle.setFeed(address(token1), address(feed), 3600);

        controller.bind(Ids.TRANSPORT, address(router));
        controller.bind(Ids.BRIDGE, address(bridge));
        controller.bind(Ids.ROUTES, address(registry));
        controller.bind(Ids.ORACLE, address(oracle));
        bytes32[12] memory remaining = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS,
            Ids.MEMBERSHIP, Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK,
            Ids.MIGRATION, Ids.RECEIVER, Ids.POOLS];
        for (uint256 i; i < remaining.length; ++i) {
            controller.bind(remaining[i], remaining[i] == Ids.VAULT
                ? address(new RouterVaultStub(address(controller), block.chainid))
                : address(new BoundDummy(address(controller))));
        }
        vault = controller.module(Ids.VAULT);
        migration = controller.module(Ids.MIGRATION);
        receiver = controller.module(Ids.RECEIVER);
        CanonicalFixture.bind(address(controller));
        controller.seal();
    }

    function _govern(address target, bytes memory data) private {
        bytes32 salt = keccak256(abi.encode(++governanceSequence, target, data));
        controller.schedule(target, 0, data, bytes32(0), salt, controller.getMinDelay());
        controller.execute(target, 0, data, bytes32(0), salt);
    }

    function _policy() private view returns (TransportPolicy memory p) {
        p.providerId = keccak256("malicious provider explicitly admitted by governance");
        p.sourceChain = block.chainid;
        p.sourceRouter = address(router);
        p.sourceProvider = address(provider);
        p.sourceCodeHash = address(provider).codehash;
        p.sourceConfigurationHash = CONFIGURATION;
        p.destinationChain = REMOTE_CHAIN;
        p.destinationRouter = REMOTE_ROUTER;
        p.destinationProvider = REMOTE_PROVIDER;
        p.destinationCodeHash = keccak256("unverified remote code metadata");
        p.destinationConfigurationHash = keccak256("unverified remote configuration metadata");
        p.channelId = CHANNEL;
        p.reviewHash = keccak256("nonzero review identifier is not proof of honest behavior");
    }

    function _route() private view returns (Route memory r) {
        r.sourceChain = block.chainid;
        r.sourceAdapter = address(bridge);
        r.sourceVault = vault;
        r.sourceReceiver = receiver;
        r.destinationChain = REMOTE_CHAIN;
        r.destinationAdapter = REMOTE_ADAPTER;
        r.destinationVault = REMOTE_VAULT;
        r.destinationReceiver = REMOTE_RECEIVER;
        r.destinationPool = POOL;
        r.sourceToken0 = address(token0);
        r.sourceToken1 = address(token1);
        r.destinationToken0 = REMOTE_TOKEN0;
        r.destinationToken1 = REMOTE_TOKEN1;
        r.token0Decimals = 18;
        r.token1Decimals = 18;
    }

    function testApprovedExactSourceConsumptionDoesNotProveDestinationCustody() public {
        TransportPolicy memory policy = _policy();
        bytes32 policyId = keccak256(abi.encode(policy));
        Route memory route = _route();
        bytes32 routeId = keccak256(abi.encode(route, policyId));

        // Admission really passes the sealed timelock. No caller bypass, code
        // mutation, configuration drift, underfunding or replay is involved.
        vm.expectRevert();
        router.registerPolicy(policy);
        _govern(address(router), abi.encodeCall(router.registerPolicy, (policy)));
        _govern(address(registry), abi.encodeCall(registry.add, (route, policyId)));
        assertFalse(router.canSend(routeId));
        _govern(address(router), abi.encodeCall(router.setOutboundEnabled, (policyId, true)));
        assertTrue(router.canSend(routeId));
        assertEq(address(provider).codehash, policy.sourceCodeHash);
        assertEq(provider.router(), policy.sourceRouter);
        assertEq(provider.configurationHash(CHANNEL), policy.sourceConfigurationHash);

        BridgeMessage memory message;
        message.version = 3;
        message.kind = MessageKind.Principal;
        message.routeId = routeId;
        message.principalRouteId = routeId;
        message.homePoolId = POOL;
        message.bucketId = uint256(keccak256(abi.encode(block.chainid, vault, POOL)));
        message.totalShares = 42e18;
        message.migrationId = keccak256("fixture authorized principal departure");
        message.migrationEpoch = 1;
        message.homeChain = block.chainid;
        message.homeVault = vault;
        message.homeReceiver = receiver;
        message.previousChain = block.chainid;
        message.previousVault = vault;
        message.previousReceiver = receiver;
        message.canonicalToken0 = address(token0);
        message.canonicalToken1 = address(token1);
        message.depositUSD = 42e18;
        message.amount0 = 13e18;
        message.amount1 = 29e18;
        token0.mint(migration, message.amount0);
        token1.mint(migration, message.amount1);
        // Unrelated custody donations remain intact; no donated backing hides
        // a short transfer. Every approved token is exactly consumed as theft.
        token0.mint(address(router), 71);
        token1.mint(address(router), 83);
        vm.startPrank(migration);
        token0.approve(address(bridge), message.amount0);
        token1.approve(address(bridge), message.amount1);
        bytes32 receipt = bridge.send(message);
        vm.stopPrank();

        assertEq(receipt, bytes32(uint256(1)));
        assertEq(bridge.nonce(), 1);
        assertEq(provider.sends(), 1);
        assertEq(provider.lastPolicy(), policyId);
        assertEq(provider.lastDestinationChain(), REMOTE_CHAIN);
        assertEq(provider.lastDestinationProvider(), REMOTE_PROVIDER);
        assertEq(provider.lastDestinationRouter(), REMOTE_ROUTER);
        assertTrue(provider.lastEnvelopeHash() != bytes32(0));
        assertEq(address(provider).codehash, policy.sourceCodeHash);
        assertEq(provider.configurationHash(CHANNEL), CONFIGURATION);
        assertEq(token0.balanceOf(THIEF), message.amount0);
        assertEq(token1.balanceOf(THIEF), message.amount1);
        assertEq(token0.balanceOf(REMOTE_VAULT), 0);
        assertEq(token1.balanceOf(REMOTE_VAULT), 0);
        assertEq(token0.balanceOf(migration), 0);
        assertEq(token1.balanceOf(migration), 0);
        assertEq(token0.balanceOf(address(bridge)), 0);
        assertEq(token1.balanceOf(address(bridge)), 0);
        assertEq(token0.balanceOf(address(provider)), 0);
        assertEq(token1.balanceOf(address(provider)), 0);
        assertEq(token0.balanceOf(address(router)), 71);
        assertEq(token1.balanceOf(address(router)), 83);
        assertEq(token0.allowance(address(bridge), address(router)), 0);
        assertEq(token1.allowance(address(bridge), address(router)), 0);
        assertEq(token0.allowance(address(router), address(provider)), 0);
        assertEq(token1.allowance(address(router), address(provider)), 0);
        // Revalidating the same malicious immutable pins cannot detect loss of
        // external backing: governance/provider safety remains a trust gate.
        assertTrue(router.canSend(routeId));
    }
}
