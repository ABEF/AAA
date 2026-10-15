// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZMigrationReceiver} from "../src/ZZZMigrationReceiver.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {Ids, Position, PositionStatus, PoolConfig, Route, BridgeMessage, MessageKind, AckPurpose} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockPools, MockRoutes} from "./mocks/Mocks.sol";

// TEST ONLY: isolate the receiver's ordering, immutable ACK data, and funded
// reserve ledgers. Production migration provenance is covered separately.
contract ReceiverVaultFixture {
    uint256 public canonicalChainId;
    MockPools private pools;
    mapping(uint256 => Position) private positions;
    mapping(uint256 => uint256) public bucketTotalShares;
    mapping(uint256 => bytes32) public homePoolId;
    bool public failImport;
    constructor(uint256 home, MockPools registry) { canonicalChainId = home; pools = registry; }
    function setHome(uint256 home) external { canonicalChainId = home; }
    function setFailImport(bool fail) external { failImport = fail; }
    function set(uint256 id, Position memory p) external {
        positions[id] = p;
        if(bucketTotalShares[id]==0)bucketTotalShares[id]=1000e18;
        if(homePoolId[id]==bytes32(0))homePoolId[id]=keccak256("canonical receiver pool");
    }
    function group(uint256 id) external view returns (Position memory) { return positions[id]; }
    function position(uint256 id) external view returns (Position memory) { return positions[id]; }
    function importPending(uint256 id, bytes32 pool, Position calldata origin, uint256 shares, bytes32 homePool, uint256 amount0, uint256 amount1) external {
        require(!failImport, "import failed");
        PoolConfig memory c = pools.get(pool);
        IERC20(c.key.currency0).transferFrom(msg.sender, address(this), amount0);
        IERC20(c.key.currency1).transferFrom(msg.sender, address(this), amount1);
        positions[id] = origin;
        bucketTotalShares[id] = shares;
        homePoolId[id] = homePool;
        positions[id].status = PositionStatus.Inbound;
        positions[id].poolId = pool;
        positions[id].idle0 = amount0;
        positions[id].idle1 = amount1;
    }
    function finalizeImport(uint256 id, uint128, uint256) external { positions[id].status = PositionStatus.Active; }
}

contract ReceiverMigrationFixture {
    mapping(uint256 => uint64) public custodyEpoch;
    BridgeMessage private confirmed;
    uint256 public confirmationCount;
    function registerImport(BridgeMessage calldata m) external {
        require(m.migrationEpoch > custodyEpoch[m.bucketId], "stale epoch");
        custodyEpoch[m.bucketId] = m.migrationEpoch;
    }
    function confirm(BridgeMessage calldata m, uint256, address) external {
        confirmed = m;
        confirmationCount++;
    }
    function confirmedMessage() external view returns (BridgeMessage memory) { return confirmed; }
    function authorizedReward(uint256, uint256, address, address, address) external pure returns (bool) { return true; }
}

contract CapturingBridgeFixture {
    MockRoutes private routes;
    BridgeMessage private lastMessage;
    uint256 public sends;
    bool public fail;
    constructor(MockRoutes registry) { routes = registry; }
    function setFail(bool value) external { fail = value; }
    function message() external view returns (BridgeMessage memory) { return lastMessage; }
    function send(BridgeMessage calldata m) external payable returns (bytes32) {
        require(!fail, "bridge failed");
        lastMessage = m;
        (Route memory r,) = routes.get(m.routeId);
        if (m.amount0 != 0) IERC20(r.sourceToken0).transferFrom(msg.sender, address(this), m.amount0);
        if (m.amount1 != 0) IERC20(r.sourceToken1).transferFrom(msg.sender, address(this), m.amount1);
        return bytes32(++sends);
    }
}

contract RemoteRewardsFixture {
    uint256 public credited;
    function creditPool(uint256, address token, uint256 personal, uint256 collective) external {
        IERC20(token).transferFrom(msg.sender, address(this), personal + collective);
        credited += personal + collective;
    }
}

contract MigrationReceiverSnapshotTest is Test {
    MockAccess ac;
    MockToken token0;
    MockToken token1;
    MockPools pools;
    MockRoutes routes;
    ReceiverVaultFixture vault;
    ReceiverMigrationFixture migration;
    CapturingBridgeFixture bridge;
    ZZZFeeController fees;
    ZZZMigrationReceiver receiver;
    bytes32 constant POOL = keccak256("receiver-pool");
    bytes32 constant PRINCIPAL = keccak256("principal-hop");
    bytes32 constant SOURCE_ACK = keccak256("source-ack");
    bytes32 constant HOME_ACK = keccak256("home-ack");
    uint256 constant HOME = 1;
    uint256 constant PREVIOUS = 100;
    address constant HOME_VAULT = address(0x1111);
    address constant HOME_RECEIVER = address(0x1112);
    address constant PREVIOUS_VAULT = address(0xAAA1);
    address constant PREVIOUS_RECEIVER = address(0xAAA2);
    address constant PREVIOUS_ADAPTER = address(0xAA11);
    address constant CANONICAL0 = address(0xB100);
    address constant CANONICAL1 = address(0xB101);

    function setUp() public {
        vm.chainId(31337);
        ac = new MockAccess(); token0 = new MockToken(18); token1 = new MockToken(18);
        pools = new MockPools(); routes = new MockRoutes(); vault = new ReceiverVaultFixture(HOME, pools);
        migration = new ReceiverMigrationFixture(); bridge = new CapturingBridgeFixture(routes);
        fees = new ZZZFeeController(address(ac)); receiver = new ZZZMigrationReceiver(address(ac));
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.POOLS, address(pools)); ac.bind(Ids.ROUTES, address(routes));
        ac.bind(Ids.MIGRATION, address(migration)); ac.bind(Ids.BRIDGE, address(bridge));
        ac.bind(Ids.FEES, address(fees)); ac.bind(Ids.RECEIVER, address(receiver)); ac.setKeeper(address(this), true); ac.seal();
        PoolConfig memory c; c.key.currency0 = address(token0); c.key.currency1 = address(token1); pools.set(POOL, c);
        Route memory r;
        r.sourceChain = PREVIOUS; r.sourceAdapter = PREVIOUS_ADAPTER; r.sourceVault = PREVIOUS_VAULT;
        r.sourceReceiver = PREVIOUS_RECEIVER; r.destinationChain = block.chainid;
        r.destinationAdapter = address(bridge); r.destinationVault = address(vault); r.destinationReceiver = address(receiver);
        r.destinationPool = POOL; r.sourceToken0 = address(0xA100); r.sourceToken1 = address(0xA101);
        // Deliberately reverse destination pool ordering to test canonical maps.
        r.destinationToken0 = address(token1); r.destinationToken1 = address(token0); routes.set(PRINCIPAL, r);
        _ackRoute(SOURCE_ACK, PREVIOUS, PREVIOUS_VAULT, PREVIOUS_RECEIVER);
        _ackRoute(HOME_ACK, HOME, HOME_VAULT, HOME_RECEIVER);
    }
    function _ackRoute(bytes32 id, uint256 destination, address destinationVault, address destinationReceiver) private {
        Route memory r; r.sourceChain = block.chainid; r.sourceVault = address(vault); r.sourceReceiver = address(receiver);
        r.sourceAdapter = address(bridge); r.destinationChain = destination;
        r.destinationVault = destinationVault; r.destinationReceiver = destinationReceiver; routes.set(id, r);
    }
    function _principal() private pure returns (BridgeMessage memory m) {
        m.version = 3; m.kind = MessageKind.Principal; m.routeId = PRINCIPAL; m.principalRouteId = PRINCIPAL;
        m.nonce = 8; m.homePoolId = keccak256("canonical receiver pool");
        m.totalShares=1000e18; m.bucketId = uint256(keccak256(abi.encode(HOME, HOME_VAULT, m.homePoolId))); m.migrationId = keccak256("accepted-hop"); m.migrationEpoch = 2;
        m.homeChain = HOME; m.homeVault = HOME_VAULT; m.homeReceiver = HOME_RECEIVER; m.depositUSD = 1000e18;
        m.previousChain = PREVIOUS; m.previousVault = PREVIOUS_VAULT; m.previousReceiver = PREVIOUS_RECEIVER;
        m.canonicalToken0 = CANONICAL0; m.canonicalToken1 = CANONICAL1; m.amount0 = 13; m.amount1 = 29;
    }
    function _deliver(BridgeMessage memory m) private {
        _deliver(m, false);
    }
    function _deliverRejected(BridgeMessage memory m) private {
        _deliver(m, true);
    }
    function _deliver(BridgeMessage memory m, bool expectFailure) private {
        token1.mint(address(bridge), m.amount0); token0.mint(address(bridge), m.amount1);
        vm.startPrank(address(bridge)); token1.approve(address(receiver), m.amount0); token0.approve(address(receiver), m.amount1);
        if (expectFailure) vm.expectRevert();
        receiver.receiveMessage(PREVIOUS, PREVIOUS_ADAPTER, m); vm.stopPrank();
    }
    function _finalize(BridgeMessage memory m) private { receiver.finalize(m.migrationId, 1, block.timestamp); }
    function _assertAck(BridgeMessage memory original, AckPurpose purpose, bytes32 deliveryRoute) private view {
        BridgeMessage memory ack = bridge.message();
        assertEq(ack.version, 3); assertEq(uint256(ack.kind), uint256(MessageKind.Acknowledgement));
        assertEq(ack.routeId, deliveryRoute); assertEq(ack.nonce, 0); assertEq(ack.migrationId, original.migrationId);
        assertEq(ack.migrationEpoch, original.migrationEpoch); assertEq(ack.principalRouteId, original.principalRouteId);
        assertEq(ack.homeChain, original.homeChain); assertEq(ack.homeVault, original.homeVault); assertEq(ack.homeReceiver, original.homeReceiver);
        assertEq(ack.previousChain, original.previousChain); assertEq(ack.previousVault, original.previousVault);
        assertEq(ack.previousReceiver, original.previousReceiver); assertEq(ack.canonicalToken0, original.canonicalToken0);
        assertEq(ack.canonicalToken1, original.canonicalToken1); assertEq(ack.depositUSD, original.depositUSD);
        assertEq(uint256(ack.acknowledgement), uint256(purpose)); assertEq(ack.amount0 + ack.amount1 + ack.individual + ack.collective, 0);
    }
    function testOnwardImportKeepsCanonicalIdentityAndReordersMappings() public {
        BridgeMessage memory m = _principal(); _deliver(m);
        Position memory p = vault.position(m.bucketId);
        assertEq(p.homeChain, HOME); assertEq(p.homeVault, HOME_VAULT); assertEq(p.homeReceiver, HOME_RECEIVER);
        assertEq(p.homeToken0, CANONICAL1); assertEq(p.homeToken1, CANONICAL0);
        assertEq(p.idle0, 29); assertEq(p.idle1, 13); assertEq(migration.custodyEpoch(m.bucketId), 2);
        assertEq(fees.remoteCanonicalToken(m.bucketId, address(token1)), CANONICAL0);
        assertEq(fees.remoteCanonicalToken(m.bucketId, address(token0)), CANONICAL1);
        BridgeMessage memory saved = receiver.acceptedMessage(m.migrationId);
        assertEq(keccak256(abi.encode(saved)), keccak256(abi.encode(m)));
    }
    function testWrongPreviousCustodyRejectedBeforeImport() public {
        BridgeMessage memory m = _principal(); m.previousVault = address(0xBAD);
        _deliverRejected(m); assertEq(migration.custodyEpoch(m.bucketId), 0);
    }
    function testWrongPrincipalRouteRejected() public {
        BridgeMessage memory m = _principal(); m.principalRouteId = HOME_ACK;
        _deliverRejected(m); assertEq(migration.custodyEpoch(m.bucketId), 0);
    }
    function testZeroEpochRejected() public {
        BridgeMessage memory m = _principal(); m.migrationEpoch = 0; _deliverRejected(m);
    }
    function testWrongCanonicalChainRejected() public {
        BridgeMessage memory m = _principal(); m.homeChain = PREVIOUS; _deliverRejected(m);
    }
    function testConflictingRemoteMappingRollsBackReceiptAndEpoch() public {
        BridgeMessage memory m = _principal();
        vm.prank(address(receiver)); fees.bindRemoteAsset(m.bucketId, address(token1), address(0xBAD));
        _deliverRejected(m);
        (, , bool exists,) = receiver.receipts(m.migrationId); assertFalse(exists);
        assertEq(migration.custodyEpoch(m.bucketId), 0); assertEq(token1.balanceOf(address(receiver)), 0);
        assertEq(receiver.acceptedMessage(m.migrationId).version, 0);
    }
    function testVaultImportFailureRollsBackCanonicalBindings() public {
        BridgeMessage memory m = _principal(); vault.setFailImport(true); _deliverRejected(m);
        (, , bool exists,) = receiver.receipts(m.migrationId); assertFalse(exists);
        assertEq(migration.custodyEpoch(m.bucketId), 0);
        assertEq(fees.remoteCanonicalToken(m.bucketId, address(token1)), address(0));
    }
    function testSourceAckUsesAcceptedSnapshotAfterAnotherPositionChange() public {
        BridgeMessage memory m = _principal(); _deliver(m); _finalize(m);
        Position memory changed; changed.homeChain = 999; changed.homeVault = address(0xBAD); vault.set(m.bucketId, changed);
        receiver.acknowledge(m.migrationId, SOURCE_ACK); _assertAck(m, AckPurpose.SourceCompletion, SOURCE_ACK);
    }
    function testHomeAckHasSeparatePurposeAndCanonicalDestination() public {
        BridgeMessage memory m = _principal(); _deliver(m); _finalize(m);
        receiver.acknowledgeHome(m.migrationId, HOME_ACK); _assertAck(m, AckPurpose.CanonicalLocation, HOME_ACK);
    }
    function testHomeAckCannotUsePreviousCustodyRoute() public {
        BridgeMessage memory m = _principal(); _deliver(m); _finalize(m);
        vm.expectRevert(); receiver.acknowledgeHome(m.migrationId, SOURCE_ACK);
    }
    function testUnfinalizedReceiptCannotAcknowledge() public {
        BridgeMessage memory m = _principal(); _deliver(m); vm.expectRevert(); receiver.acknowledge(m.migrationId, SOURCE_ACK);
    }
    function testReturningHomeDoesNotRequireSelfChainHomeAck() public {
        BridgeMessage memory m = _principal(); vault.setHome(block.chainid); m.homeChain = block.chainid;
        m.homeVault = address(vault); m.homeReceiver = address(receiver);
        m.bucketId=uint256(keccak256(abi.encode(m.homeChain,m.homeVault,m.homePoolId))); _deliver(m); _finalize(m);
        vm.expectRevert(); receiver.acknowledgeHome(m.migrationId, HOME_ACK);
    }
    function testForeignSourceCompletionAckDelegatesToMigrationValidation() public {
        Route memory incoming; incoming.sourceChain = PREVIOUS; incoming.sourceAdapter = PREVIOUS_ADAPTER;
        incoming.sourceVault = PREVIOUS_VAULT; incoming.destinationChain = block.chainid;
        incoming.destinationVault = address(vault); incoming.destinationReceiver = address(receiver); routes.set(SOURCE_ACK, incoming);
        BridgeMessage memory m = _principal(); m.kind = MessageKind.Acknowledgement; m.routeId = SOURCE_ACK;
        m.amount0 = 0; m.amount1 = 0;
        vm.prank(address(bridge)); receiver.receiveMessage(PREVIOUS, PREVIOUS_ADAPTER, m);
        assertEq(migration.confirmationCount(), 1); assertEq(migration.confirmedMessage().homeChain, HOME);
    }
    function testPooledPrincipalRejectsLegacyVersionAndZeroShares() public {
        BridgeMessage memory m=_principal();m.version=2;_deliverRejected(m);
        m=_principal();m.totalShares=0;_deliverRejected(m);
    }
    function testPooledPrincipalRejectsAlteredInitialPoolOrBucketHash() public {
        BridgeMessage memory m=_principal();m.homePoolId=keccak256("altered origin");_deliverRejected(m);
        m=_principal();m.bucketId++;_deliverRejected(m);
    }
    function testSourceAckRetainsFrozenSharesAndFeeCounters() public {
        BridgeMessage memory m=_principal();m.allocatedIndividual0=101;m.allocatedCollective0=61;
        m.allocatedIndividual1=203;m.allocatedCollective1=122;_deliver(m);_finalize(m);
        receiver.acknowledge(m.migrationId,SOURCE_ACK);BridgeMessage memory ack=bridge.message();
        assertEq(ack.homePoolId,m.homePoolId);assertEq(ack.totalShares,m.totalShares);
        assertEq(ack.allocatedIndividual0,101);assertEq(ack.allocatedCollective0,61);
        assertEq(ack.allocatedIndividual1,203);assertEq(ack.allocatedCollective1,122);
    }

    function _fundedReward() private returns (BridgeMessage memory m) {
        bytes32 rewardRoute=keccak256("authenticated bucket reward");
        Route memory r;r.sourceChain=PREVIOUS;r.sourceAdapter=PREVIOUS_ADAPTER;r.sourceVault=PREVIOUS_VAULT;
        r.destinationChain=block.chainid;r.destinationVault=address(vault);r.destinationReceiver=address(receiver);
        r.sourceToken0=address(0xAA01);r.destinationToken0=address(token1);routes.set(rewardRoute,r);
        m.version=3;m.kind=MessageKind.Reward;m.routeId=rewardRoute;
        m.homeChain=block.chainid;m.homeVault=address(vault);m.homeReceiver=address(receiver);
        m.homePoolId=keccak256("canonical receiver pool");m.totalShares=1000e18;m.depositUSD=1000e18;
        m.bucketId=uint256(keccak256(abi.encode(m.homeChain,m.homeVault,m.homePoolId)));
        m.canonicalToken0=address(token1);m.amount0=80;m.individual=50;m.collective=30;
        Position memory p;p.homeChain=m.homeChain;p.homeVault=m.homeVault;p.homeReceiver=m.homeReceiver;
        p.homeToken0=address(token0);p.homeToken1=address(token1);p.depositUSD=m.depositUSD;p.status=PositionStatus.Remote;
        vault.set(m.bucketId,p);ac.bind(Ids.REWARDS,address(new RemoteRewardsFixture()));
        token1.mint(address(bridge),80);vm.prank(address(bridge));token1.approve(address(receiver),80);
    }
    function testFundedRemoteRewardUsesFrozenCanonicalMembership() public {
        BridgeMessage memory m=_fundedReward();
        vm.prank(address(bridge));receiver.receiveMessage(PREVIOUS,PREVIOUS_ADAPTER,m);
        assertEq(fees.receivedIndividual(m.bucketId,address(token1)),50);
        assertEq(fees.receivedCollective(m.bucketId,address(token1)),30);
        assertEq(token1.balanceOf(address(receiver)),0);
    }
    function testRemoteRewardRejectsChangedSharesPoolContributionAndAsset() public {
        BridgeMessage memory m=_fundedReward();m.totalShares++;
        vm.prank(address(bridge));vm.expectRevert();receiver.receiveMessage(PREVIOUS,PREVIOUS_ADAPTER,m);
        m.totalShares--;m.homePoolId=keccak256("forged origin pool");
        vm.prank(address(bridge));vm.expectRevert();receiver.receiveMessage(PREVIOUS,PREVIOUS_ADAPTER,m);
        m.homePoolId=keccak256("canonical receiver pool");m.depositUSD++;
        vm.prank(address(bridge));vm.expectRevert();receiver.receiveMessage(PREVIOUS,PREVIOUS_ADAPTER,m);
        m.depositUSD--;m.canonicalToken0=address(token0);
        vm.prank(address(bridge));vm.expectRevert();receiver.receiveMessage(PREVIOUS,PREVIOUS_ADAPTER,m);
        assertEq(token1.balanceOf(address(bridge)),80);
        assertEq(fees.receivedIndividual(m.bucketId,address(token1)),0);
    }

}

contract RemoteFeeReserveTest is Test {
    MockAccess ac;
    MockToken token;
    MockToken other;
    MockPools pools;
    MockRoutes routes;
    ReceiverVaultFixture vault;
    CapturingBridgeFixture bridge;
    RemoteRewardsFixture rewards;
    ZZZFeeController fees;
    address constant CANONICAL = address(0x1001);
    address constant HOME_VAULT = address(0x1002);
    address constant HOME_RECEIVER = address(0x1003);
    bytes32 constant POOL = keccak256("fee-pool");
    bytes32 constant REWARD_ROUTE = keccak256("reward-home");
    function setUp() public {
        vm.chainId(31337); ac = new MockAccess(); token = new MockToken(18); other = new MockToken(18);
        pools = new MockPools(); routes = new MockRoutes(); vault = new ReceiverVaultFixture(1, pools);
        bridge = new CapturingBridgeFixture(routes); rewards = new RemoteRewardsFixture(); fees = new ZZZFeeController(address(ac));
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.POOLS, address(pools)); ac.bind(Ids.ROUTES, address(routes));
        ac.bind(Ids.BRIDGE, address(bridge)); ac.bind(Ids.REWARDS, address(rewards)); ac.bind(Ids.RECEIVER, address(this)); ac.seal();
        PoolConfig memory c; c.key.currency0 = address(token); c.key.currency1 = address(other); pools.set(POOL, c);
        Position memory p; p.poolId = POOL; p.status = PositionStatus.Active; p.homeChain = 1;
        p.homeVault = HOME_VAULT; p.homeReceiver = HOME_RECEIVER; p.homeToken0 = CANONICAL; p.homeToken1 = address(0x1004); vault.set(42, p);
        Route memory r; r.sourceChain = block.chainid; r.sourceVault = address(vault); r.sourceToken0 = address(token);
        r.destinationChain = 1; r.destinationVault = HOME_VAULT; r.destinationReceiver = HOME_RECEIVER;
        r.destinationToken0 = CANONICAL; routes.set(REWARD_ROUTE, r);
        vm.prank(address(vault)); token.approve(address(fees), type(uint256).max);
    }
    function _allocate(uint256 amount) private {
        token.mint(address(vault), amount); vm.prank(address(vault)); fees.allocate(42, address(token), amount);
    }
    function _status(PositionStatus status) private {
        Position memory p = vault.position(42); p.status = status; vault.set(42, p);
    }
    function testRemoteDustStaysFundedUntilDeliveredHome() public {
        _allocate(1009); _status(PositionStatus.Outbound); vm.prank(address(vault)); fees.flushDust(42, address(token));
        assertEq(fees.dust(42, address(token)), 0); assertEq(fees.remoteIndividual(42, address(token)), 809);
        assertEq(fees.remoteCollective(42, address(token)), 100); assertEq(fees.accounted(address(token)), 1009);
        assertEq(token.balanceOf(address(fees)), 1009); assertEq(rewards.credited(), 0);
        fees.bridgeRewards(42, address(token), REWARD_ROUTE);
        assertEq(bridge.message().individual, 809); assertEq(bridge.message().collective, 100);
        assertEq(fees.accounted(address(token)), 100); assertEq(token.balanceOf(address(fees)), 100);
    }
    function testLegacyBudgetUsesBoundCanonicalAssetAfterPoolReplacement() public {
        _allocate(100); Position memory p = vault.position(42); p.status = PositionStatus.Remote;
        p.poolId = keccak256("different-pool"); p.homeToken0 = address(0xBAD); p.homeToken1 = address(0xBEEF); vault.set(42, p);
        fees.bridgeRewards(42, address(token), REWARD_ROUTE);
        BridgeMessage memory m = bridge.message(); assertEq(m.version, 3); assertEq(m.canonicalToken0, CANONICAL);
        assertEq(m.amount0, 90); assertEq(fees.remoteCanonicalToken(42, address(token)), CANONICAL);
        assertEq(token.balanceOf(address(bridge)), 90);
    }
    function testLegacyBudgetsBridgeInAllCustodyStates() public {
        PositionStatus[4] memory states = [PositionStatus.Active, PositionStatus.Outbound, PositionStatus.Remote, PositionStatus.Inbound];
        for (uint256 i; i < states.length; i++) {
            _status(PositionStatus.Active); _allocate(100); _status(states[i]); fees.bridgeRewards(42, address(token), REWARD_ROUTE);
        }
        assertEq(bridge.sends(), 4); assertEq(token.balanceOf(address(bridge)), 360);
        assertEq(fees.accounted(address(token)), 40);
    }
    function testDormantAndNoneCannotSendLegacyBudgets() public {
        _allocate(100); _status(PositionStatus.Dormant); vm.expectRevert(); fees.bridgeRewards(42, address(token), REWARD_ROUTE);
        _status(PositionStatus.None); vm.expectRevert(); fees.bridgeRewards(42, address(token), REWARD_ROUTE);
        assertEq(fees.remoteIndividual(42, address(token)), 80);
    }
    function testBoundAssetCannotBeChangedByReceiver() public {
        fees.bindRemoteAsset(42, address(token), CANONICAL); fees.bindRemoteAsset(42, address(token), CANONICAL);
        vm.expectRevert(); fees.bindRemoteAsset(42, address(token), address(0xBAD));
        assertEq(fees.remoteCanonicalToken(42, address(token)), CANONICAL);
    }
    function testAllocationRejectsConflictingCanonicalMappingBeforeTakingFunds() public {
        _allocate(10); Position memory p = vault.position(42); p.homeToken0 = address(0xBAD); vault.set(42, p);
        token.mint(address(vault), 100); vm.prank(address(vault)); vm.expectRevert(); fees.allocate(42, address(token), 100);
        assertEq(token.balanceOf(address(vault)), 100); assertEq(fees.accounted(address(token)), 10);
    }
    function testMappingRequiresAuthenticatedReceiver() public {
        vm.prank(address(0xBAD)); vm.expectRevert(); fees.bindRemoteAsset(42, address(token), CANONICAL);
    }
    function testRewardSendFailureRestoresBudgetsAndFunding() public {
        _allocate(100); bridge.setFail(true); vm.expectRevert(); fees.bridgeRewards(42, address(token), REWARD_ROUTE);
        assertEq(fees.remoteIndividual(42, address(token)), 80); assertEq(fees.remoteCollective(42, address(token)), 10);
        assertEq(fees.accounted(address(token)), 100); assertEq(token.balanceOf(address(fees)), 100);
    }
}
