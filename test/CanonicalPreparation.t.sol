// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBridgeAdapter} from "../src/ZZZBridgeAdapter.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus, Route, BridgeMessage, MessageKind}
    from "../src/libraries/ZZZTypes.sol";
import {VaultPolicyMock, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {MockToken, MockPools, MockFeed, MockRoutes, MockTransport, MockMessageReceiver}
    from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

// TEST ONLY: real sealed controller and economic modules; venue, routes,
// remote message authentication, prices and VRF are explicit fixtures.
contract PreparationPools is MockPools {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}
contract PreparationPolicy is VaultPolicyMock {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}
contract PreparationVenue is VaultLiquidityMock {
    IZZZAccess public immutable access;
    constructor(address controller, address a, address b) VaultLiquidityMock(a, b) { access = IZZZAccess(controller); }
}
contract PreparationRoutes is MockRoutes {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}
contract PreparationTransport is MockTransport {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
    function canSend(bytes32) external pure returns (bool) { return true; }
}
contract PreparationReceiver is MockMessageReceiver {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}
contract PreparationMintCallback is IERC721Receiver {
    ZZZAccessController public immutable controller;
    ZZZVault public immutable vault;
    bytes private announcement;
    bytes32 private salt;
    constructor(ZZZAccessController c, ZZZVault v, bytes memory data, bytes32 operationSalt) {
        controller = c; vault = v; announcement = data; salt = operationSalt;
    }
    function mint() external payable { vault.mintDormant{value: msg.value}(); }
    function onERC721Received(address, address, uint256, bytes calldata) external returns (bytes4) {
        controller.execute(address(controller), 0, announcement, bytes32(0), salt);
        return IERC721Receiver.onERC721Received.selector;
    }
}
contract PreparationTreasuryCallback {
    ZZZAccessController private controller;
    bytes private announcement;
    bytes32 private salt;
    function arm(ZZZAccessController c, bytes memory data, bytes32 operationSalt) external {
        controller = c; announcement = data; salt = operationSalt;
    }
    receive() external payable {
        if (address(controller) != address(0)) controller.execute(address(controller), 0, announcement, bytes32(0), salt);
    }
}

contract CanonicalPreparationTest is Test {
    ZZZAccessController private ac;
    ZZZVault private vault;
    ZZZNFT private nft;
    ZZZRewards private rewards;
    ZZZMembership private membership;
    ZZZFeeController private fees;
    ZZZCompounder private compounder;
    ZZZBuyback private buyback;
    ZZZOracle private oracle;
    ZZZMigration private migration;
    ZZZBridgeAdapter private bridge;
    PreparationPools private pools;
    PreparationVenue private venue;
    PreparationRoutes private routes;
    PreparationTransport private transport;
    PreparationReceiver private receiver;
    MockToken private t0;
    MockToken private t1;
    MockFeed private feed;
    MockVRF private vrf;
    PreparationTreasuryCallback private treasury;
    bytes32 private poolId;
    uint256 private governanceNonce;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address private constant GUARDIAN = address(0x600D);

    function setUp() public {
        vm.warp(1_000_000);
        address[] memory proposers = new address[](1); proposers[0] = address(this);
        address[] memory executors = new address[](1); executors[0] = address(0);
        ac = new ZZZAccessController(1 days, proposers, executors, address(this), GUARDIAN);
        t0 = new MockToken(0); t1 = new MockToken(0);
        pools = new PreparationPools(address(ac));
        venue = new PreparationVenue(address(ac), address(t0), address(t1));
        treasury = new PreparationTreasuryCallback();
        vault = new ZZZVault(address(ac), block.chainid, payable(address(treasury)));
        nft = new ZZZNFT(address(ac), "");
        rewards = new ZZZRewards(address(ac)); membership = new ZZZMembership(address(ac));
        fees = new ZZZFeeController(address(ac)); compounder = new ZZZCompounder(address(ac));
        buyback = new ZZZBuyback(address(ac), address(t0), 1e30);
        oracle = new ZZZOracle(address(ac), address(0)); migration = new ZZZMigration(address(ac));
        routes = new PreparationRoutes(address(ac)); transport = new PreparationTransport(address(ac));
        receiver = new PreparationReceiver(address(ac)); receiver.configure(address(t0), false);
        bridge = new ZZZBridgeAdapter(address(ac), address(transport));
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.NFT, address(nft));
        ac.bind(Ids.LIQUIDITY, address(venue)); ac.bind(Ids.REWARDS, address(rewards));
        ac.bind(Ids.MEMBERSHIP, address(membership)); ac.bind(Ids.FEES, address(fees));
        ac.bind(Ids.STRATEGY, address(new PreparationPolicy(address(ac))));
        ac.bind(Ids.COMPOUNDER, address(compounder)); ac.bind(Ids.BUYBACK, address(buyback));
        ac.bind(Ids.MIGRATION, address(migration)); ac.bind(Ids.BRIDGE, address(bridge));
        ac.bind(Ids.RECEIVER, address(receiver)); ac.bind(Ids.ORACLE, address(oracle));
        ac.bind(Ids.POOLS, address(pools)); ac.bind(Ids.ROUTES, address(routes)); ac.bind(Ids.TRANSPORT, address(transport));
        feed = new MockFeed(8, 1e8);
        oracle.setFeed(address(t0), address(feed), 3600); oracle.setFeed(address(t1), address(feed), 3600);
        rewards.addAsset(address(t0)); rewards.addAsset(address(t1));
        vrf = new MockVRF(); nft.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        PoolConfig memory c; c.key = PoolKey(address(t0), address(t1), 3000, 60, address(0));
        c.operationsEnabled = true; c.depositsEnabled = true; c.minDepositUSD = 1e18;
        c.maxPositionUSD = 1e30; c.maxSlippageBps = 100; poolId = keccak256(abi.encode(c.key)); pools.set(poolId, c);
        CanonicalFixture.bind(address(ac));
        ac.seal();
        vm.deal(ALICE, 10 ether); vm.deal(address(this), 10 ether);
        t0.mint(ALICE, 100000); t1.mint(ALICE, 100000);
        vm.startPrank(ALICE); t0.approve(address(vault), type(uint256).max); t1.approve(address(vault), type(uint256).max); vm.stopPrank();
    }
    function _notice() private view returns (ZZZAccessController.PreparationNotice memory) {
        return ZZZAccessController.PreparationNotice(block.chainid + 1, address(0xCA11),
            keccak256("notice-only deployment commitment"), keccak256("review material"));
    }
    function _schedule(address target, bytes memory data) private returns (bytes32 salt) {
        salt = bytes32(++governanceNonce); ac.schedule(target, 0, data, bytes32(0), salt, 1 days);
    }
    function _govern(address target, bytes memory data) private {
        bytes32 salt = _schedule(target, data); vm.warp(block.timestamp + 1 days);
        ac.execute(target, 0, data, bytes32(0), salt);
    }
    function _prepare() private { _govern(address(ac), abi.encodeCall(ac.startPreparation, (_notice()))); }
    function _fresh() private { feed.set(1e8, block.timestamp, block.timestamp); }
    function _mint(bool reveal) private returns (uint256 id) {
        vm.prank(ALICE); id = vault.mintDormant{value: 0.05 ether}();
        if (reveal) { vrf.fulfill(nft.requestOf(id), 0, 0); nft.finalizeTraits(id); }
    }
    function _active() private returns (uint256 id) {
        id = _mint(true); vm.prank(ALICE); vault.activate(id, poolId, 1000, 1000, 1, block.timestamp + 100);
    }

    function testAnnouncementAndCancellationRequireActualTimelockAndExactNotice() public {
        vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.startPreparation(_notice());
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.startPreparation(_notice());
        bytes memory data = abi.encodeCall(ac.startPreparation, (_notice())); bytes32 salt = _schedule(address(ac), data);
        vm.expectRevert(); ac.execute(address(ac), 0, data, bytes32(0), salt);
        vm.warp(block.timestamp + 1 days); ac.execute(address(ac), 0, data, bytes32(0), salt);
        bytes32 first = ac.preparationHash(); assertTrue(ac.preparationActive()); assertEq(ac.preparationNonce(), 1);
        assertEq(first, keccak256(abi.encode("ZZZ_CANONICAL_PREPARATION_V1", block.chainid, address(ac),
            address(vault), address(nft), uint256(1), _notice())));
        assertFalse(ac.canConfigure(address(ac)));
        vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.cancelPreparation(first);
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.cancelPreparation(first);
        bytes memory wrong = abi.encodeCall(ac.cancelPreparation, (bytes32(uint256(1))));
        salt = _schedule(address(ac), wrong); vm.warp(block.timestamp + 1 days);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.execute(address(ac), 0, wrong, bytes32(0), salt);
        _govern(address(ac), abi.encodeCall(ac.cancelPreparation, (first)));
        assertFalse(ac.preparationActive()); assertTrue(ac.canConfigure(address(ac)));
        _prepare(); assertEq(ac.preparationNonce(), 2); assertNotEq(ac.preparationHash(), first);
    }
    function testPreparationIsCanonicalOnlyAndDoesNotAcceptAnEmptyNotice() public {
        ZZZAccessController.PreparationNotice memory notice = _notice(); notice.reviewHash = bytes32(0);
        bytes memory data = abi.encodeCall(ac.startPreparation, (notice)); bytes32 salt = _schedule(address(ac), data);
        vm.warp(block.timestamp + 1 days); vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        ac.execute(address(ac), 0, data, bytes32(0), salt);
        data = abi.encodeCall(ac.startPreparation, (_notice())); salt = _schedule(address(ac), data);
        vm.warp(block.timestamp + 1 days); vm.chainId(block.chainid + 1);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.execute(address(ac), 0, data, bytes32(0), salt);
    }
    function testNewEconomicWorkStopsAndCancellationRestoresIt() public {
        uint256 active = _active(); uint256 dormant = _mint(true); uint256 bucket = vault.nftBucket(active); _prepare();
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Preparing.selector); vault.mintDormant{value: 0.05 ether}();
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Preparing.selector); vault.activate(dormant, poolId, 1000, 1000, 1, block.timestamp + 100);
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Preparing.selector); vault.increase(active, 100, 100, 1, block.timestamp + 100);
        vm.expectRevert(ZZZModule.Preparing.selector); vault.rebalance(bucket, 1, block.timestamp + 100);
        vm.expectRevert(ZZZModule.Preparing.selector); compounder.compound(bucket, 1, block.timestamp + 100);
        vm.expectRevert(ZZZModule.Preparing.selector); buyback.execute(address(t0), 1, poolId, block.timestamp + 100);
        vm.expectRevert(ZZZModule.Preparing.selector); migration.execute(bytes32(uint256(1)), block.timestamp + 100);
        _govern(address(ac), abi.encodeCall(ac.cancelPreparation, (ac.preparationHash()))); _fresh();
        vm.prank(ALICE); vault.increase(active, 100, 100, 1, block.timestamp + 100);
        assertEq(vault.contributionUSD(active), 2200e18); assertEq(nft.mintedCount(), 2);
    }
    function testClaimsTransfersPendingRevealAndReceiptSettlementStayAvailable() public {
        uint256 active = _active(); uint256 pending = _mint(false); uint256 bucket = vault.nftBucket(active);
        _govern(address(fees), abi.encodeCall(fees.createRewardReceiver, (bucket, address(0))));
        address inbox = fees.rewardReceiver(bucket); _prepare();
        t0.mint(inbox, 100); fees.syncExternal(bucket);
        (bool funded,) = address(nft.royaltyRewards()).call{value: 1 ether}(""); assertTrue(funded);
        vrf.fulfill(nft.requestOf(pending), 0, 0); nft.finalizeTraits(pending); assertTrue(nft.traitsReady(pending));
        vm.prank(ALICE); nft.transferFrom(ALICE, BOB, active);
        vm.prank(BOB); assertEq(rewards.claim(active, address(t0)), 90);
        ZZZRoyaltyRewards royalties = nft.royaltyRewards();
        vm.prank(BOB); assertEq(royalties.claim(active, address(0)), 1 ether);
        t0.mint(inbox, 100); fees.syncExternal(bucket);
        (funded,) = address(royalties).call{value: 1 ether}(""); assertTrue(funded);
        ZZZClaimRouter router = nft.claimRouter(); ZZZClaimRouter.Claim[] memory claims = new ZZZClaimRouter.Claim[](2);
        claims[0] = ZZZClaimRouter.Claim(active, address(t0), false);
        claims[1] = ZZZClaimRouter.Claim(active, address(0), true);
        vm.prank(BOB); uint256[] memory amounts = router.claimBatch(claims);
        assertEq(amounts[0], 90); assertEq(amounts[1], 1 ether);
        assertEq(membership.totalEligible(), 1); assertEq(nft.ownerOf(active), BOB);
        assertEq(vault.sharesOf(active), 2000e18); assertTrue(ac.preparationActive());
    }
    function testQueuedConfigurationCannotBypassPreparationButPauseControlRemains() public {
        MockToken another = new MockToken(0); bytes memory add = abi.encodeCall(rewards.addAsset, (address(another)));
        bytes32 salt = _schedule(address(rewards), add); _prepare();
        vm.expectRevert(ZZZModule.Unauthorized.selector); ac.execute(address(rewards), 0, add, bytes32(0), salt);
        vm.prank(GUARDIAN); ac.setPaused(true); assertTrue(ac.paused());
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.setPaused(false);
        _govern(address(ac), abi.encodeCall(ac.setPaused, (false))); assertFalse(ac.paused()); assertTrue(ac.preparationActive());
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Preparing.selector); vault.mintDormant{value: 0.05 ether}();
    }
    function testMaturedAnnouncementInNFTCallbackRollsBackTheEntireMint() public {
        bytes memory data = abi.encodeCall(ac.startPreparation, (_notice())); bytes32 salt = _schedule(address(ac), data);
        PreparationMintCallback callback = new PreparationMintCallback(ac, vault, data, salt);
        vm.warp(block.timestamp + 1 days);
        vm.expectRevert(ZZZModule.Preparing.selector); callback.mint{value: 0.05 ether}();
        assertFalse(ac.preparationActive()); assertEq(ac.preparationNonce(), 0);
        assertEq(vault.sequence(), 0); assertEq(nft.mintedCount(), 0); assertEq(address(treasury).balance, 0);
        assertTrue(ac.isOperationReady(ac.hashOperation(address(ac), 0, data, bytes32(0), salt)));
        ac.execute(address(ac), 0, data, bytes32(0), salt); assertTrue(ac.preparationActive());
    }
    function testMaturedAnnouncementInFinalTreasuryCallbackCannotBypassVaultEndGuard() public {
        bytes memory data = abi.encodeCall(ac.startPreparation, (_notice())); bytes32 salt = _schedule(address(ac), data);
        treasury.arm(ac, data, salt); vm.warp(block.timestamp + 1 days);
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Preparing.selector); vault.mintDormant{value: 0.05 ether}();
        assertFalse(ac.preparationActive()); assertEq(ac.preparationNonce(), 0);
        assertEq(vault.sequence(), 0); assertEq(nft.mintedCount(), 0); assertEq(address(treasury).balance, 0);
        assertTrue(ac.isOperationReady(ac.hashOperation(address(ac), 0, data, bytes32(0), salt)));
    }
    function testScheduledPrincipalPlanCanBeCancelledThroughTimelockDuringPreparation() public {
        uint256 id = _active(); uint256 bucket = vault.nftBucket(id); bytes32 routeId = keccak256("planned departure");
        Route memory r; r.sourceChain = block.chainid; r.sourceVault = address(vault); r.sourceReceiver = address(receiver);
        r.sourceAdapter = address(bridge); r.sourceToken0 = address(t0); r.sourceToken1 = address(t1);
        r.destinationChain = block.chainid + 1; r.destinationVault = address(0x5151); r.destinationReceiver = address(0x5152);
        routes.set(routeId, r); _govern(address(migration), abi.encodeCall(migration.propose, (bucket, routeId)));
        bytes32 plan = migration.activePlan(bucket); assertNotEq(plan, bytes32(0)); _prepare();
        vm.prank(GUARDIAN); vm.expectRevert(ZZZModule.Unauthorized.selector); migration.cancel(plan);
        _govern(address(migration), abi.encodeCall(migration.cancel, (plan)));
        assertEq(migration.activePlan(bucket), bytes32(0)); assertEq(uint256(vault.group(bucket).status), uint256(PositionStatus.Active));
        assertTrue(ac.preparationActive());
    }
    function testHarvestAndTimelockedParkingRemainAvailableWithoutSourcePrice() public {
        uint256 id = _active(); uint256 bucket = vault.nftBucket(id); _prepare();
        venue.setFees(100, 100); vault.collectFees(bucket, block.timestamp + 100);
        assertEq(rewards.claimable(id, address(t0)), 90);
        vm.prank(GUARDIAN); ac.setPaused(true); Position memory p = vault.group(bucket);
        ZZZMigration.ParkingRequest memory request = ZZZMigration.ParkingRequest(bucket, poolId, p.lpTokenId,
            vault.bucketTotalShares(bucket), p.depositUSD, migration.custodyEpoch(bucket), migration.parkingNonce(bucket),
            address(t0), address(t1), 1000, 1000, block.timestamp + 1 days + 100, keccak256("parking review"));
        _govern(address(migration), abi.encodeCall(migration.park, (request)));
        p = vault.group(bucket); assertEq(uint256(p.status), uint256(PositionStatus.Parked));
        assertEq(p.idle0, 1000); assertEq(p.idle1, 1000); assertEq(vault.sharesOf(id), 2000e18);
        assertTrue(ac.preparationActive());
    }
    function testAdapterPreservesFundedInboundRewardDrainAndAcknowledgements() public {
        bytes32 incoming = keccak256("incoming"); Route memory r;
        r.sourceChain = block.chainid + 1; r.sourceAdapter = address(0x5150); r.sourceVault = address(0x5151);
        r.sourceReceiver = address(0x5152); r.destinationChain = block.chainid; r.destinationAdapter = address(bridge);
        r.destinationVault = address(vault); r.destinationReceiver = address(receiver);
        r.sourceToken0 = address(0x7711); r.destinationToken0 = address(t0); routes.set(incoming, r);
        bytes32 outgoing = keccak256("acknowledgement");
        r.sourceChain = block.chainid; r.sourceAdapter = address(bridge); r.sourceVault = address(vault);
        r.sourceReceiver = address(receiver); r.destinationChain = block.chainid + 1;
        r.destinationAdapter = address(0x5150); r.destinationVault = address(0x5151); r.destinationReceiver = address(0x5152);
        r.sourceToken0 = address(0); r.destinationToken0 = address(0); routes.set(outgoing, r);
        bytes32 rewardRoute = keccak256("reward drain");
        r.sourceToken0 = address(t0); r.destinationToken0 = address(0x7711); routes.set(rewardRoute, r); _prepare();
        BridgeMessage memory m; m.version = 3; m.kind = MessageKind.Reward; m.routeId = incoming;
        m.nonce = 1; m.bucketId = 42; m.amount0 = 80; m.individual = 50; m.collective = 30;
        t0.mint(address(transport), 80);
        transport.deliver(address(bridge), block.chainid + 1, address(0x5150), abi.encode(m), address(t0), 80);
        assertEq(t0.balanceOf(address(receiver)), 80); assertEq(receiver.received(), 1);
        t0.mint(address(fees), 80); vm.prank(address(fees)); t0.approve(address(bridge), 80);
        m.routeId = rewardRoute; m.nonce = 0;
        vm.prank(address(fees)); assertNotEq(bridge.send(m), bytes32(0));
        m.kind = MessageKind.Principal;
        vm.prank(address(migration)); vm.expectRevert(ZZZModule.Preparing.selector); bridge.send(m);
        m.kind = MessageKind.Acknowledgement; m.routeId = outgoing; m.nonce = 0; m.migrationId = keccak256("existing hop");
        m.amount0 = 0; m.individual = 0; m.collective = 0;
        vm.prank(address(receiver)); assertNotEq(bridge.send(m), bytes32(0)); assertEq(bridge.nonce(), 2);
    }
}
