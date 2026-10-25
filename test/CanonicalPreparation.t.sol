// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

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
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus}
    from "../src/libraries/ZZZTypes.sol";
import {VaultPolicyMock, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {MockToken, MockPools, MockFeed}
    from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

// TEST ONLY: real sealed controller and economic modules; venue, prices and VRF are explicit fixtures.
contract PreparationPools is MockPools {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); activationAssets=address(this); }
    // TEST ONLY: admission is explicitly mocked; economic accounting is real.
    address public zzz;
    function setTestZZZIdentity(address token) external { zzz=token; }
}
contract PreparationPolicy is VaultPolicyMock {
    IZZZAccess public immutable access;
    constructor(address controller) { access = IZZZAccess(controller); }
}
contract PreparationVenue is VaultLiquidityMock {
    IZZZAccess public immutable access;
    constructor(address controller, address a, address b) VaultLiquidityMock(a, b) { access = IZZZAccess(controller); }
}
contract PreparationMintCallback is IERC721Receiver {
    ZZZAccessController public immutable controller;
    ZZZVault public immutable vault;
    bytes private announcement;
    constructor(ZZZAccessController c, ZZZVault v, bytes memory data) {
        controller = c; vault = v; announcement = data;
    }
    function acceptGovernance() external { controller.acceptGovernance(); }
    function mint() external payable { vault.mintDormant{value: msg.value}(); }
    function onERC721Received(address, address, uint256, bytes calldata) external returns (bytes4) {
        (bool ok, bytes memory result) = address(controller).call(announcement);
        if (!ok) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
        return IERC721Receiver.onERC721Received.selector;
    }
}
contract PreparationTreasuryCallback {
    ZZZAccessController private controller;
    bytes private announcement;
    function acceptGovernance(ZZZAccessController c) external { c.acceptGovernance(); }
    function arm(ZZZAccessController c, bytes memory data) external {
        controller = c; announcement = data;
    }
    receive() external payable {
        if (address(controller) != address(0)) {
            (bool ok, bytes memory result) = address(controller).call(announcement);
            if (!ok) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
        }
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
    PreparationPools private pools;
    PreparationVenue private venue;
    MockToken private t0;
    MockToken private t1;
    MockFeed private feed;
    MockVRF private vrf;
    PreparationTreasuryCallback private treasury;
    bytes32 private poolId;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address private constant GUARDIAN = address(0x600D);

    function setUp() public {
        vm.warp(1_000_000);
        ac = new ZZZAccessController(address(this), address(this), GUARDIAN);
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
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.NFT, address(nft));
        ac.bind(Ids.LIQUIDITY, address(venue)); ac.bind(Ids.REWARDS, address(rewards));
        ac.bind(Ids.MEMBERSHIP, address(membership)); ac.bind(Ids.FEES, address(fees));
        ac.bind(Ids.STRATEGY, address(new PreparationPolicy(address(ac))));
        ac.bind(Ids.COMPOUNDER, address(compounder)); ac.bind(Ids.BUYBACK, address(buyback));
        ac.bind(Ids.MIGRATION, address(migration)); ac.bind(Ids.ORACLE, address(oracle));
        ac.bind(Ids.POOLS, address(pools));
        feed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(t0), address(feed), 3600); oracle.setTestFeed(address(t1), address(feed), 3600);
        rewards.addAsset(address(t0)); rewards.addAsset(address(t1));
        pools.setTestZZZIdentity(address(t0)); migration.configureZZZ(address(t0),address(t0).codehash,keccak256("preparation fixed ZZZ"));
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
        return ZZZAccessController.PreparationNotice(block.chainid, address(0xCA11),
            keccak256("notice-only deployment commitment"), keccak256("review material"));
    }
    function _govern(address target, bytes memory data) private {
        address governor = ac.governance();
        vm.prank(governor);
        (bool ok, bytes memory result) = target.call(data);
        if (!ok) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
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

    function testImmediatePreparationAndCancellationRequireGovernanceAndExactNotice() public {
        vm.prank(ALICE); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.startPreparation(_notice());
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.startPreparation(_notice());
        _prepare();
        bytes32 first = ac.preparationHash(); assertTrue(ac.preparationActive()); assertEq(ac.preparationNonce(), 1);
        assertEq(first, keccak256(abi.encode("ZZZ_CANONICAL_PREPARATION_V1", block.chainid, address(ac),
            address(vault), address(nft), uint256(1), _notice())));
        assertFalse(ac.canConfigure(address(this)));
        vm.prank(ALICE); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.cancelPreparation(first);
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.cancelPreparation(first);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.cancelPreparation(bytes32(uint256(1)));
        _govern(address(ac), abi.encodeCall(ac.cancelPreparation, (first)));
        assertFalse(ac.preparationActive()); assertTrue(ac.canConfigure(address(this)));
        _prepare(); assertEq(ac.preparationNonce(), 2); assertNotEq(ac.preparationHash(), first);
    }
    function testPreparationIsCanonicalOnlyAndDoesNotAcceptAnEmptyNotice() public {
        ZZZAccessController.PreparationNotice memory notice = _notice(); notice.reviewHash = bytes32(0);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.startPreparation(notice);
        notice = _notice(); vm.chainId(block.chainid + 1);
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector); ac.startPreparation(notice);
    }

    function testClaimsTransfersPendingRevealAndLPFeeCollectionStayAvailable() public {
        uint256 active = _active(); uint256 pending = _mint(false); uint256 bucket = vault.nftBucket(active);
        _prepare(); venue.setFees(100, 0); vault.collectFees(bucket, block.timestamp + 100);
        (bool funded,) = address(nft.royaltyRewards()).call{value: 1 ether}(""); assertTrue(funded);
        vrf.fulfill(nft.requestOf(pending), 0, 0); nft.finalizeTraits(pending); assertTrue(nft.traitsReady(pending));
        vm.prank(ALICE); nft.transferFrom(ALICE, BOB, active);
        vm.prank(BOB); assertEq(rewards.claim(active, address(t0)), 90);
        ZZZRoyaltyRewards royalties = nft.royaltyRewards();
        vm.prank(BOB); assertEq(royalties.claim(active, address(0)), 1 ether);
        venue.setFees(100, 0); vault.collectFees(bucket, block.timestamp + 100);
        (funded,) = address(royalties).call{value: 1 ether}(""); assertTrue(funded);
        ZZZClaimRouter router = nft.claimRouter(); ZZZClaimRouter.Claim[] memory claims = new ZZZClaimRouter.Claim[](2);
        claims[0] = ZZZClaimRouter.Claim(active, address(t0), false);
        claims[1] = ZZZClaimRouter.Claim(active, address(0), true);
        vm.prank(BOB); uint256[] memory amounts = router.claimBatch(claims);
        assertEq(amounts[0], 90); assertEq(amounts[1], 1 ether);
        assertEq(membership.totalEligible(), 1); assertEq(nft.ownerOf(active), BOB);
        assertEq(vault.sharesOf(active), 2000e18); assertTrue(ac.preparationActive());
    }
    function testDirectConfigurationCannotBypassPreparationButPauseControlRemains() public {
        MockToken another = new MockToken(0);
        _prepare();
        vm.expectRevert(ZZZModule.Unauthorized.selector); rewards.addAsset(address(another));
        vm.prank(GUARDIAN); ac.setPaused(true); assertTrue(ac.paused());
        vm.prank(GUARDIAN); vm.expectRevert(ZZZAccessController.Unauthorized.selector); ac.setPaused(false);
        _govern(address(ac), abi.encodeCall(ac.setPaused, (false))); assertFalse(ac.paused()); assertTrue(ac.preparationActive());
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Preparing.selector); vault.mintDormant{value: 0.05 ether}();
    }
    function testGovernanceAnnouncementInNFTCallbackRollsBackTheEntireMint() public {
        bytes memory data = abi.encodeCall(ac.startPreparation, (_notice()));
        PreparationMintCallback callback = new PreparationMintCallback(ac, vault, data);
        ac.proposeGovernance(address(callback)); callback.acceptGovernance();
        vm.expectRevert(ZZZModule.Preparing.selector); callback.mint{value: 0.05 ether}();
        assertFalse(ac.preparationActive()); assertEq(ac.preparationNonce(), 0);
        assertEq(vault.sequence(), 0); assertEq(nft.mintedCount(), 0); assertEq(address(treasury).balance, 0);
        assertEq(ac.governance(), address(callback));
        _prepare(); assertTrue(ac.preparationActive());
    }
    function testGovernanceAnnouncementInFinalTreasuryCallbackCannotBypassVaultEndGuard() public {
        bytes memory data = abi.encodeCall(ac.startPreparation, (_notice()));
        ac.proposeGovernance(address(treasury)); treasury.acceptGovernance(ac);
        treasury.arm(ac, data);
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Preparing.selector); vault.mintDormant{value: 0.05 ether}();
        assertFalse(ac.preparationActive()); assertEq(ac.preparationNonce(), 0);
        assertEq(vault.sequence(), 0); assertEq(nft.mintedCount(), 0); assertEq(address(treasury).balance, 0);
        assertEq(ac.governance(), address(treasury));
        _prepare(); assertTrue(ac.preparationActive());
    }

    function testHarvestAndGovernanceParkingRemainAvailableWithoutSourcePrice() public {
        uint256 id = _active(); uint256 bucket = vault.nftBucket(id); _prepare();
        vm.warp(block.timestamp + 3601); // Explicitly stale both fixture feeds.
        venue.setFees(100, 100); vault.collectFees(bucket, block.timestamp + 100);
        assertEq(rewards.claimable(id, address(t0)), 90);
        vm.prank(GUARDIAN); ac.setPaused(true); Position memory p = vault.group(bucket);
        ZZZMigration.ParkingRequest memory request = ZZZMigration.ParkingRequest(bucket, poolId, p.lpTokenId,
            vault.bucketTotalShares(bucket), p.depositUSD, migration.custodyEpoch(bucket), migration.parkingNonce(bucket),
            address(t0), address(t1), 1000, 1000, block.timestamp + 100, keccak256("parking review"));
        _govern(address(migration), abi.encodeCall(migration.park, (request)));
        p = vault.group(bucket); assertEq(uint256(p.status), uint256(PositionStatus.Parked));
        assertEq(p.idle0, 1000); assertEq(p.idle1, 1000); assertEq(vault.sharesOf(id), 2000e18);
        assertTrue(ac.preparationActive());
    }

}
