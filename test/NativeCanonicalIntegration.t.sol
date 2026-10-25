// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {IZZZCanonicalModule} from "../src/interfaces/IZZZCanonical.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {ICanonicalHandoffTest} from "./CanonicalHandoff.t.sol";
import {PreparationPools, PreparationPolicy} from "./CanonicalPreparation.t.sol";
import {MockToken, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

/// @dev Deterministic settlement fixture only. All custody, NFT, fee/reward,
/// royalty, lifecycle and canonical transfer contracts in the test are real.
contract CanonicalNativeVenue is ERC721 {
    IZZZAccess public immutable access;
    MockToken private immutable token;
    uint256 private next = 1;
    uint256 private fee0;
    uint256 private fee1;
    mapping(uint256 => uint256) private a0;
    mapping(uint256 => uint256) private a1;
    constructor(address controller, address asset) ERC721("Native handoff fixture", "NHF") {
        access = IZZZAccess(controller); token = MockToken(asset);
    }
    receive() external payable {}
    function positionManager() external view returns (address) { return address(this); }
    function spot(bytes32) external pure returns (uint160) { return uint160(1 << 96); }
    function setFees(uint256 x, uint256 y) external { fee0 = x; fee1 = y; }
    function mint(bytes32, int24, int24, uint256 x, uint256 y, uint128, uint256)
        external payable returns (uint256 id, uint256 spent0, uint256 spent1) {
        id = next++; _mint(msg.sender, id); _fund(id, x, y); return (id, x, y);
    }
    function increase(bytes32, uint256 id, uint256 x, uint256 y, uint128, uint256)
        external payable returns (uint256, uint256) { _fund(id, x, y); return (x, y); }
    function _fund(uint256 id, uint256 x, uint256 y) private {
        require(msg.value == x); require(token.transferFrom(msg.sender, address(this), y)); a0[id] += x; a1[id] += y;
    }
    function amounts(uint256 id) external view returns (uint256, uint256) { return (a0[id], a1[id]); }
    function collect(bytes32, uint256, uint256) external {
        uint256 x = fee0; uint256 y = fee1; fee0 = 0; fee1 = 0;
        if (x != 0) { (bool ok,) = msg.sender.call{value: x}(""); require(ok); }
        token.mint(msg.sender, y);
    }
    function close(bytes32, uint256 id, uint256) external {
        uint256 x = a0[id]; uint256 y = a1[id]; delete a0[id]; delete a1[id]; _burn(id);
        (bool ok,) = msg.sender.call{value: x}(""); require(ok); require(token.transfer(msg.sender, y));
    }
}

contract NativeCanonicalIntegrationTest is Test {
    struct System {
        ZZZAccessController access;
        ZZZVault vault;
        ZZZNFT nft;
        ZZZRewards rewards;
        ZZZRoyaltyRewards royalties;
        ZZZFeeController fees;
        ZZZMigration migration;
        PreparationPools pools;
        CanonicalNativeVenue venue;
        MockVRF vrf;
        ICanonicalHandoffTest handoff;
    }
    System private source;
    System private destination;
    MockToken private token;
    MockFeed private feed;
    bytes32 private poolId;
    uint256 private nonce;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address private constant GUARDIAN = address(0x600D);
    address payable private constant TREASURY = payable(address(0x7EA5));

    function setUp() public {
        vm.warp(1_000_000); token = new MockToken(18); feed = new MockFeed(8, 1e8);
        poolId = keccak256(abi.encode(PoolKey(address(0), address(token), 3000, 60, address(0))));
        source = _deploy(true); destination = _deploy(false);
        destination.handoff.prepareImport(address(source.access)); destination.access.seal();
        vm.deal(ALICE, 10000 ether); vm.deal(BOB, 100 ether); vm.deal(address(this), 1000 ether);
        vm.deal(address(source.venue), 200 ether);
        token.mint(ALICE, 10000 ether);
        vm.startPrank(ALICE); token.approve(address(source.vault), type(uint256).max);
        token.approve(address(destination.vault), type(uint256).max); vm.stopPrank();
    }
    function _deploy(bool sealNow) private returns (System memory s) {
        address[] memory proposers = new address[](1); proposers[0] = address(this);
        address[] memory executors = new address[](1); executors[0] = address(0);
        s.access = new ZZZAccessController(0, proposers, executors, address(this), GUARDIAN);
        s.pools = new PreparationPools(address(s.access)); s.venue = new CanonicalNativeVenue(address(s.access), address(token));
        s.vault = new ZZZVault(address(s.access), block.chainid, TREASURY);
        s.nft = new ZZZNFT(address(s.access), "ipfs://native-canonical-fixture/"); s.royalties = s.nft.royaltyRewards();
        s.rewards = new ZZZRewards(address(s.access)); s.fees = new ZZZFeeController(address(s.access));
        s.migration = new ZZZMigration(address(s.access)); ZZZOracle oracle = new ZZZOracle(address(s.access), address(0));
        s.access.bind(Ids.VAULT, address(s.vault)); s.access.bind(Ids.NFT, address(s.nft));
        s.access.bind(Ids.LIQUIDITY, address(s.venue)); s.access.bind(Ids.REWARDS, address(s.rewards));
        s.access.bind(Ids.MEMBERSHIP, address(new ZZZMembership(address(s.access)))); s.access.bind(Ids.FEES, address(s.fees));
        s.access.bind(Ids.STRATEGY, address(new PreparationPolicy(address(s.access))));
        s.access.bind(Ids.COMPOUNDER, address(new ZZZCompounder(address(s.access))));
        s.access.bind(Ids.BUYBACK, address(new ZZZBuyback(address(s.access), address(token), 1e30)));
        s.access.bind(Ids.MIGRATION, address(s.migration)); s.access.bind(Ids.ORACLE, address(oracle)); s.access.bind(Ids.POOLS, address(s.pools));
        oracle.setTestFeed(address(0), address(feed), 3600); oracle.setTestFeed(address(token), address(feed), 3600);
        s.rewards.addAsset(address(token)); s.nft.addRoyaltyAsset(address(token));
        s.pools.setTestZZZIdentity(address(token));
        s.migration.configureZZZ(address(token),address(token).codehash,keccak256("native handoff fixed ZZZ"));
        s.vrf = new MockVRF(); s.nft.configureRandomness(address(s.vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        PoolConfig memory config; config.key = PoolKey(address(0), address(token), 3000, 60, address(0));
        config.operationsEnabled = true; config.depositsEnabled = true; config.minDepositUSD = 1e18;
        config.maxPositionUSD = 1e30; config.maxSlippageBps = 100; s.pools.set(poolId, config);
        CanonicalFixture.bind(address(s.access)); s.handoff = ICanonicalHandoffTest(address(s.access.canonicalHandoff()));
        if (sealNow) s.access.seal();
    }
    function _govern(System memory s, address target, bytes memory data) private {
        bytes32 salt = bytes32(++nonce); s.access.schedule(target, 0, data, bytes32(0), salt, 0);
        vm.warp(block.timestamp + 1 days); feed.set(1e8, block.timestamp, block.timestamp);
        s.access.execute(target, 0, data, bytes32(0), salt);
    }
    function _mint() private returns (uint256 id) {
        vm.prank(ALICE); id = source.vault.mintDormant{value: 0.05 ether}();
        source.vrf.fulfill(source.nft.requestOf(id), 0, 0); source.nft.finalizeTraits(id);
    }
    function _seed() private returns (uint256 id) {
        id = _mint(); _mint();
        vm.prank(ALICE); source.vault.activate{value: 1000 ether}(id, poolId, 1000 ether, 1000 ether, 1, block.timestamp + 100);
        uint256 bucket = source.vault.nftBucket(id);
        source.venue.setFees(103 ether + 7, 107 ether + 11); source.vault.collectFees(bucket, block.timestamp + 100);
        // Unsolicited native prefunds remain quarantined separately from fees.
        (bool ok,) = address(source.fees).call{value: 7}(""); assertTrue(ok);
        (ok,) = address(source.royalties).call{value: 1 ether + 3}(""); assertTrue(ok);
        token.mint(address(source.royalties), 13 ether + 2);
        vm.prank(ALICE); source.nft.transferFrom(ALICE, BOB, id);
    }
    function _freezeExportImport(uint256 id) private {
        ZZZAccessController.PreparationNotice memory notice = ZZZAccessController.PreparationNotice(
            block.chainid, address(destination.access), destination.handoff.deploymentCommitment(), keccak256("native handoff review"));
        _govern(source, address(source.access), abi.encodeCall(source.access.startPreparation, (notice)));
        vm.prank(GUARDIAN); source.access.setPaused(true);
        uint256 bucket = source.vault.nftBucket(id); Position memory p = source.vault.group(bucket);
        ZZZMigration.ParkingRequest memory request = ZZZMigration.ParkingRequest(bucket, p.poolId, p.lpTokenId,
            source.vault.bucketTotalShares(bucket), p.depositUSD, source.migration.custodyEpoch(bucket),
            source.migration.parkingNonce(bucket), address(0), address(token), 1, 1,
            block.timestamp + 1 days + 100, keccak256("native parked fixture"));
        _govern(source, address(source.migration), abi.encodeCall(source.migration.park, (request)));
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.freeze, ()));
        for (uint8 slot; slot < 6; ++slot) source.handoff.settle(slot);
        for (uint8 slot; slot < 6; ++slot) {
            uint256 count = source.handoff.recordCount(slot);
            for (uint256 offset; offset < count; offset += 8) source.handoff.exportRows(slot, count-offset > 8 ? 8 : count-offset);
        }
        for (uint8 slot; slot < 6; ++slot) {
            uint256 count = source.handoff.recordCount(slot);
            IZZZCanonicalModule module = IZZZCanonicalModule(source.handoff.moduleAt(slot));
            for (uint256 offset; offset < count; offset += 8) {
                uint256 length = count-offset > 8 ? 8 : count-offset; bytes[] memory records = new bytes[](length);
                for (uint256 i; i < length; ++i) records[i] = module.canonicalExport(offset+i);
                destination.handoff.importRows(slot, records);
            }
        }
        destination.handoff.completeImport();
    }
    function _fundAll() private {
        for (uint8 slot; slot < 6; ++slot) for (uint256 i; i < source.handoff.assetCount(slot); ++i) source.handoff.fund(slot, i);
    }
    function testNativeWholeHandoffCarriesPrincipalIndicesRoyaltiesAndFeeDonationQuarantine() public {
        uint256 id = _seed(); _freezeExportImport(id); uint256 bucket = source.vault.nftBucket(id);
        uint256 nativeLP = source.rewards.claimable(id, address(0)); uint256 nativeRoyalties = source.royalties.claimable(id, address(0));
        uint256 ownerIndex = source.rewards.ownerIndex(bucket, address(0)); uint256 collectiveIndex = source.rewards.index(address(0));
        uint256 principal = source.vault.totalIdle(address(0)); uint256 reserves = source.fees.accounted(address(0));
        _fundAll(); _govern(source, address(source.handoff), abi.encodeCall(source.handoff.commit, ()));
        assertEq(source.access.canonicalState(), 3); assertEq(destination.access.canonicalState(), 0);
        assertEq(destination.nft.ownerOf(id), BOB); assertEq(destination.nft.mintedCount(), 2);
        assertEq(destination.vault.sharesOf(id), source.vault.sharesOf(id));
        assertEq(destination.vault.totalIdle(address(0)), principal); assertEq(address(destination.vault).balance, principal);
        assertEq(destination.fees.accounted(address(0)), reserves); assertEq(address(destination.fees).balance, reserves + 7);
        assertEq(destination.rewards.ownerIndex(bucket, address(0)), ownerIndex); assertEq(destination.rewards.index(address(0)), collectiveIndex);
        assertEq(destination.rewards.claimable(id, address(0)), nativeLP); assertEq(destination.royalties.claimable(id, address(0)), nativeRoyalties);
        uint256 before = BOB.balance;
        vm.prank(BOB); assertEq(destination.rewards.claim(id, address(0)), nativeLP);
        vm.prank(BOB); assertEq(destination.royalties.claim(id, address(0)), nativeRoyalties);
        assertGt(nativeLP, 0); assertGt(nativeRoyalties, 0); assertEq(BOB.balance, before + nativeLP + nativeRoyalties);
        vm.prank(ALICE); vm.expectRevert(); destination.rewards.claim(id, address(0));
    }
    function testNativePartialFundingAbortRequiresAndRestoresExactBacking() public {
        uint256 id = _seed(); _freezeExportImport(id);
        uint256 principal = address(source.vault).balance; uint256 nativeLP = source.rewards.claimable(id, address(0));
        uint256 nativeRoyalties = source.royalties.claimable(id, address(0));
        source.handoff.fund(1, 0); // Native principal moves to destination companion, then Vault.
        source.handoff.fund(3, 0); // Independently classified native LP liability backing.
        assertEq(address(destination.vault).balance, principal); assertEq(address(source.vault).balance, 0);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.abort, ()));
        bytes32 salt = bytes32(++nonce); bytes memory finish = abi.encodeCall(source.handoff.finishAbort, ());
        source.access.schedule(address(source.handoff), 0, finish, bytes32(0), salt, 0);
        vm.expectRevert(); source.access.execute(address(source.handoff), 0, finish, bytes32(0), salt);
        source.handoff.returnFunds(1, 0); source.handoff.returnFunds(3, 0);
        _govern(source, address(source.handoff), abi.encodeCall(source.handoff.finishAbort, ()));
        assertEq(source.access.canonicalState(), 0); assertEq(destination.access.canonicalState(), 4);
        assertEq(address(source.vault).balance, principal); assertEq(address(destination.vault).balance, 0);
        assertEq(source.nft.ownerOf(id), BOB); assertEq(source.rewards.claimable(id, address(0)), nativeLP);
        assertEq(source.royalties.claimable(id, address(0)), nativeRoyalties);
        uint256 before = BOB.balance; vm.prank(BOB); source.rewards.claim(id, address(0));
        vm.prank(BOB); source.royalties.claim(id, address(0)); assertEq(BOB.balance, before + nativeLP + nativeRoyalties);
    }
}
