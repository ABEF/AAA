// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {Ids, Position, PositionStatus, PoolConfig, Route, BridgeMessage, MessageKind} from "../src/libraries/ZZZTypes.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockRoutes, MockReadyRouter, MockFeed, BoundDummy} from "./mocks/Mocks.sol";

/// @dev TEST ONLY: custody sink for a local migration-state-machine test. This
/// does not model bridge backing, finality or cross-chain authentication.
contract ParkingBridgeCapture {
    address immutable token0;
    address immutable token1;
    uint256 public received0;
    uint256 public received1;
    constructor(address a, address b) { token0 = a; token1 = b; }
    function send(BridgeMessage calldata m) external payable returns (bytes32) {
        received0 += m.amount0; received1 += m.amount1;
        require(IERC20(token0).transferFrom(msg.sender, address(this), m.amount0));
        require(IERC20(token1).transferFrom(msg.sender, address(this), m.amount1));
        return keccak256(abi.encode(m));
    }
}

/// @notice Real Vault/Migration/reward accounting, but a fake LP venue and mock
/// authority. The separate timelock test below covers actual governance delay.
contract CustodyParkingTest is PooledVaultFixture {
    function _migration() private returns (ZZZMigration migration) {
        migration = new ZZZMigration(address(ac)); ac.bind(Ids.MIGRATION, address(migration));
    }
    function _request(ZZZMigration migration, uint256 bucket) private view returns (ZZZMigration.ParkingRequest memory r) {
        Position memory p = vault.group(bucket);
        r.bucketId = bucket; r.poolId = p.poolId; r.lpTokenId = p.lpTokenId;
        r.totalShares = vault.bucketTotalShares(bucket); r.depositUSD = p.depositUSD;
        r.custodyEpoch = migration.custodyEpoch(bucket); r.nonce = migration.parkingNonce(bucket);
        r.token0 = address(t0); r.token1 = address(t1);
        r.minimum0 = uint128(venue.a0(p.lpTokenId)); r.minimum1 = uint128(venue.a1(p.lpTokenId));
        r.deadline = block.timestamp + 100; r.reviewHash = keccak256("reviewed-token-close-minima");
    }
    function _park(ZZZMigration migration) private {
        ac.setPaused(true); migration.park(_request(migration, _bucket()));
    }
    function _route() private returns (bytes32 routeId, ParkingBridgeCapture bridge) {
        MockRoutes routes = new MockRoutes(); ac.bind(Ids.ROUTES, address(routes));
        ac.bind(Ids.TRANSPORT, address(new MockReadyRouter()));
        bridge = new ParkingBridgeCapture(address(t0), address(t1)); ac.bind(Ids.BRIDGE, address(bridge));
        Route memory r; r.sourceChain = block.chainid; r.sourceVault = address(vault);
        r.sourceReceiver = ac.module(Ids.RECEIVER); r.sourceToken0 = address(t0); r.sourceToken1 = address(t1);
        r.destinationChain = block.chainid + 1; r.destinationVault = address(0xD357);
        r.destinationReceiver = address(0xD358); r.destinationToken0 = address(t0); r.destinationToken1 = address(t1);
        routeId = keccak256("parking-test-only-route"); routes.set(routeId, r);
    }
    function _refresh() private {
        MockFeed fresh = new MockFeed(8, 1e8);
        oracle.setFeed(address(t0), address(fresh), 3600); oracle.setFeed(address(t1), address(fresh), 3600);
    }
    function testParkingStaleOracleAndBrokenInboxKeepsPrincipalAndFundedClaimRights() public {
        uint256 id = activatedPosition(); ZZZMigration migration = _migration(); uint256 bucket = _bucket();
        Position memory beforePosition = vault.group(bucket); uint256 shares = vault.sharesOf(id);
        address inbox = fees.createRewardReceiver(bucket, address(0));
        t0.mint(inbox, 100); fees.syncExternal(bucket); uint256 funded = rewards.claimable(id, address(t0));
        t0.mint(inbox, 200); vm.mockCallRevert(inbox, abi.encodeWithSignature("sync()"), abi.encodePacked("inbox unavailable"));
        vm.warp(block.timestamp + 3601); vm.expectRevert(); oracle.price(address(t0));
        venue.setFees(100, 100); _park(migration);
        Position memory parked = vault.group(bucket);
        assertEq(uint8(parked.status), uint8(PositionStatus.Parked)); assertEq(parked.lpTokenId, 0);
        assertEq(parked.idle0, beforePosition.idle0 + 1000); assertEq(parked.idle1, beforePosition.idle1 + 1000);
        assertEq(vault.totalIdle(address(t0)), parked.idle0); assertEq(t0.balanceOf(inbox), 200);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 100);
        assertEq(fees.compoundBalance(bucket, address(t0)), 10); assertEq(fees.compoundBalance(bucket, address(t1)), 5);
        assertEq(vault.sharesOf(id), shares); assertTrue(membership.eligible(id)); assertEq(nft.ownerOf(id), alice);
        vm.prank(alice); assertEq(rewards.claim(id, address(t0)), funded + 90);
        assertEq(vault.group(bucket).idle0, parked.idle0); vm.expectRevert(); venue.ownerOf(beforePosition.lpTokenId);
    }
    function testParkingRequiresGovernancePausedSealedAndFixedMigrationModule() public {
        activatedPosition(); ZZZMigration migration = _migration(); ZZZMigration.ParkingRequest memory r = _request(migration, _bucket());
        vm.prank(alice); vm.expectRevert(); migration.park(r);
        vm.expectRevert(); migration.park(r); // Still live, so custody cannot be parked.
        ac.setPaused(true); vm.expectRevert(); vault.park(_bucket(), block.timestamp + 100);
        vm.mockCall(address(ac), abi.encodeWithSignature("isSealed()"), abi.encode(false));
        vm.expectRevert(); migration.park(r);
        vm.clearMockedCalls();
        migration.park(r); assertEq(migration.parkingNonce(_bucket()), 1);
    }
    function testParkingRejectsEveryStaleSnapshotAndInvalidAuthorizationField() public {
        activatedPosition(); ZZZMigration migration = _migration(); ac.setPaused(true);
        for (uint256 i; i < 13; ++i) {
            ZZZMigration.ParkingRequest memory r = _request(migration, _bucket());
            if (i == 0) ++r.bucketId;
            else if (i == 1) r.poolId = bytes32(uint256(123));
            else if (i == 2) ++r.lpTokenId;
            else if (i == 3) ++r.totalShares;
            else if (i == 4) ++r.depositUSD;
            else if (i == 5) ++r.custodyEpoch;
            else if (i == 6) ++r.nonce;
            else if (i == 7) r.token0 = address(t1);
            else if (i == 8) r.token1 = address(t0);
            else if (i == 9) r.reviewHash = bytes32(0);
            else if (i == 10) r.deadline = block.timestamp - 1;
            else if (i == 11) r.deadline = block.timestamp + 601;
            else { r.minimum0 = 0; r.minimum1 = 0; }
            vm.expectRevert(); migration.park(r);
            assertEq(migration.parkingNonce(_bucket()), 0);
            assertEq(uint8(vault.group(_bucket()).status), uint8(PositionStatus.Active));
        }
    }
    function testParkingRejectsNonlocalCustodyEvenWithMatchingLPAndShareSnapshot() public {
        activatedPosition(); ZZZMigration migration = _migration(); ac.setPaused(true);
        ZZZMigration.ParkingRequest memory r = _request(migration, _bucket());
        Position memory p = vault.group(_bucket()); p.locationChain = block.chainid + 1;
        vm.mockCall(address(vault), abi.encodeCall(vault.group, (_bucket())), abi.encode(p));
        vm.expectRevert(); migration.park(r); vm.clearMockedCalls();
        assertEq(migration.parkingNonce(_bucket()), 0);
    }
    function testParkingMinimaExcludeOldIdleCompoundAndDirectDonationsAndRollBack() public {
        venue.setSpendBps(9900); activatedPosition(); ZZZMigration migration = _migration(); uint256 bucket = _bucket();
        venue.setFees(100, 100); vault.collectFees(bucket, block.timestamp + 100);
        t0.mint(address(vault), 777); t1.mint(address(vault), 888);
        Position memory beforePosition = vault.group(bucket); uint256 balance0 = t0.balanceOf(address(vault));
        uint256 balance1 = t1.balanceOf(address(vault)); ac.setPaused(true);
        for (uint256 leg; leg < 2; ++leg) {
            ZZZMigration.ParkingRequest memory r = _request(migration, bucket);
            if (leg == 0) ++r.minimum0; else ++r.minimum1;
            vm.expectRevert(); migration.park(r);
            assertEq(migration.parkingNonce(bucket), 0); assertEq(vault.group(bucket).lpTokenId, beforePosition.lpTokenId);
            assertEq(vault.group(bucket).idle0, 10); assertEq(vault.group(bucket).idle1, 10);
            assertEq(t0.balanceOf(address(vault)), balance0); assertEq(t1.balanceOf(address(vault)), balance1);
            assertEq(fees.compoundBalance(bucket, address(t0)), 5); assertEq(venue.ownerOf(beforePosition.lpTokenId), address(vault));
        }
    }
    function testParkingVenueFeesCannotSubsidizePrincipalMinimums() public {
        activatedPosition(); ZZZMigration migration = _migration(); uint256 bucket = _bucket();
        venue.setFees(1000, 1000); ZZZMigration.ParkingRequest memory r = _request(migration, bucket); ++r.minimum0;
        ac.setPaused(true); vm.expectRevert(); migration.park(r);
        assertEq(venue.fee0(), 1000); assertEq(fees.compoundBalance(bucket, address(t0)), 0);
        assertEq(migration.parkingNonce(bucket), 0); assertEq(vault.group(bucket).idle0, 0);
    }
    function testParkingOneSidedPositionAllowsOneZeroMinimum() public {
        uint256 id = _mint(alice); _activate(alice, id, 1000, 0); ZZZMigration migration = _migration();
        ZZZMigration.ParkingRequest memory r = _request(migration, _bucket()); assertEq(r.minimum1, 0);
        ac.setPaused(true); migration.park(r); assertEq(vault.group(_bucket()).idle0, 1000);
        assertEq(vault.group(_bucket()).idle1, 0); assertTrue(membership.eligible(id));
    }
    function testParkingNonceInvalidationAndSuccessfulExecutionPreventReplay() public {
        activatedPosition(); ZZZMigration migration = _migration(); ZZZMigration.ParkingRequest memory stale = _request(migration, _bucket());
        ac.setPaused(true); migration.invalidateParking(_bucket()); vm.expectRevert(); migration.park(stale);
        ZZZMigration.ParkingRequest memory current = _request(migration, _bucket()); migration.park(current);
        assertEq(migration.parkingNonce(_bucket()), 2); vm.expectRevert(); migration.park(current);
    }
    function testParkingRebalanceInvalidatesScheduledLPTokenSnapshot() public {
        activatedPosition(); ZZZMigration migration = _migration(); ZZZMigration.ParkingRequest memory stale = _request(migration, _bucket());
        vault.rebalance(_bucket(), 1, block.timestamp + 100); assertTrue(vault.group(_bucket()).lpTokenId != stale.lpTokenId);
        ac.setPaused(true); vm.expectRevert(); migration.park(stale);
        migration.park(_request(migration, _bucket()));
    }
    function testParkingCannotRaceScheduledMigrationAndResumeCannotRaceParkedMigration() public {
        activatedPosition(); ZZZMigration migration = _migration(); (bytes32 routeId,) = _route();
        bytes32 plan = migration.propose(_bucket(), routeId); ac.setPaused(true);
        ZZZMigration.ParkingRequest memory r = _request(migration, _bucket());
        vm.expectRevert(); migration.park(r);
        migration.cancel(plan); migration.park(_request(migration, _bucket()));
        migration.propose(_bucket(), routeId); ac.setPaused(false);
        vm.expectRevert(); migration.resume(_bucket(), poolId, 1, block.timestamp + 100);
        assertEq(uint8(vault.group(_bucket()).status), uint8(PositionStatus.Parked));
    }
    function testParkedResumeRetainsStaleOracleAndVenueFailureRollbackThenPreservesShares() public {
        uint256 id = activatedPosition(); ZZZMigration migration = _migration(); uint256 shares = vault.sharesOf(id);
        _park(migration); ac.setPaused(false); vm.warp(block.timestamp + 3601);
        vm.expectRevert(); migration.resume(_bucket(), poolId, 1, block.timestamp + 100);
        assertEq(vault.group(_bucket()).idle0, 1000); assertEq(vault.group(_bucket()).lpTokenId, 0);
        _refresh(); venue.setFail(true); vm.expectRevert(); migration.resume(_bucket(), poolId, 1, block.timestamp + 100);
        assertEq(vault.group(_bucket()).idle0, 1000); assertEq(uint8(vault.group(_bucket()).status), uint8(PositionStatus.Parked));
        venue.setFail(false); migration.resume(_bucket(), poolId, 1, block.timestamp + 100);
        assertEq(uint8(vault.group(_bucket()).status), uint8(PositionStatus.Active)); assertGt(vault.group(_bucket()).lpTokenId, 0);
        assertEq(vault.sharesOf(id), shares); assertEq(vault.contributionUSD(id), 2000e18); assertTrue(membership.eligible(id));
    }
    function testParkedResumeRejectsChangedOrderedTokensAndDisabledDestination() public {
        activatedPosition(); ZZZMigration migration = _migration(); _park(migration); ac.setPaused(false);
        PoolConfig memory c = pools.get(poolId); bytes32 other = keccak256("parking-destination");
        c.key.currency0 = address(t1); c.key.currency1 = address(t0); pools.set(other, c);
        vm.expectRevert(); migration.resume(_bucket(), other, 1, block.timestamp + 100);
        c = pools.get(poolId); c.operationsEnabled = false; pools.set(other, c);
        vm.expectRevert(); migration.resume(_bucket(), other, 1, block.timestamp + 100);
        assertEq(vault.group(_bucket()).poolId, poolId); assertEq(vault.group(_bucket()).idle0, 1000);
    }
    function testParkedMigrationNeedsRemoteLiabilityFundingButNotRecoveredOracle() public {
        activatedPosition(); ZZZMigration migration = _migration(); uint256 bucket = _bucket();
        BridgeMessage memory imported; imported.version = 3; imported.kind = MessageKind.Principal;
        imported.bucketId = bucket; imported.homeChain = block.chainid; imported.homeVault = address(vault);
        imported.totalShares = vault.bucketTotalShares(bucket); imported.canonicalToken0 = address(t0); imported.canonicalToken1 = address(t1);
        imported.allocatedIndividual0 = 100; imported.allocatedCollective0 = 10;
        vm.prank(ac.module(Ids.RECEIVER)); fees.importAccounting(imported); assertFalse(fees.remoteSettled(bucket));
        _park(migration); (bytes32 routeId, ParkingBridgeCapture bridge) = _route();
        bytes32 plan = migration.propose(bucket, routeId); ac.setPaused(false); vm.warp(block.timestamp + 2 days);
        vm.expectRevert(); migration.execute(plan, block.timestamp + 100);
        assertEq(uint8(vault.group(bucket).status), uint8(PositionStatus.Parked)); assertEq(migration.custodyEpoch(bucket), 0);
        address receiver = ac.module(Ids.RECEIVER); t0.mint(receiver, 110);
        vm.startPrank(receiver); t0.approve(address(fees), 110); fees.creditRemote(bucket, address(t0), 100, 10); vm.stopPrank();
        assertTrue(fees.remoteSettled(bucket)); vm.expectRevert(); oracle.price(address(t0));
        migration.execute(plan, block.timestamp + 100);
        assertEq(uint8(vault.group(bucket).status), uint8(PositionStatus.Outbound)); assertEq(vault.group(bucket).idle0, 0);
        assertEq(bridge.received0(), 1000); assertEq(bridge.received1(), 1000); assertEq(migration.custodyEpoch(bucket), 1);
    }
}

/// @dev Role-only fixture: real sealed timelock and Migration, synthetic custody
/// record. Physical principal accounting is tested in CustodyParkingTest above.
contract ParkingRoleVault {
    ZZZAccessController public immutable access;
    Position private record;
    constructor(ZZZAccessController controller, address token0, address token1) {
        access = controller; record.poolId = bytes32(uint256(7)); record.lpTokenId = 99; record.depositUSD = 200e18;
        record.status = PositionStatus.Active; record.locationChain = block.chainid; record.locationVault = address(this);
        record.homeChain = block.chainid; record.homeVault = address(this); record.homeToken0 = token0; record.homeToken1 = token1;
    }
    function canonicalChainId() external view returns (uint256) { return block.chainid; }
    function group(uint256) external view returns (Position memory) { return record; }
    function bucketTotalShares(uint256) external pure returns (uint256) { return 200e18; }
    function park(uint256, uint256) external {
        require(msg.sender == access.module(Ids.MIGRATION) && access.paused());
        record.lpTokenId = 0; record.status = PositionStatus.Parked; record.idle0 += 100; record.idle1 += 100;
    }
}
contract ParkingRolePools {
    ZZZAccessController public immutable access;
    address immutable token0; address immutable token1;
    constructor(ZZZAccessController controller, address a, address b) { access = controller; token0 = a; token1 = b; }
    function accounting(bytes32) external view returns (PoolConfig memory c) { c.key.currency0 = token0; c.key.currency1 = token1; }
}
contract CustodyParkingGovernanceTest is Test {
    function testSealedPausedParkingRequiresExactImmediateGovernanceCall() public {
        vm.warp(1000000);
        address[] memory authorities = new address[](1); authorities[0] = address(this);
        ZZZAccessController controller = new ZZZAccessController(0, authorities, authorities, address(this), address(this));
        ParkingRoleVault vault = new ParkingRoleVault(controller, address(0x111), address(0x222));
        ZZZMigration migration = new ZZZMigration(address(controller));
        ParkingRolePools pools = new ParkingRolePools(controller, address(0x111), address(0x222));
        bytes32[16] memory ids = [Ids.VAULT, Ids.NFT, Ids.LIQUIDITY, Ids.REWARDS, Ids.MEMBERSHIP, Ids.FEES,
            Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION, Ids.BRIDGE, Ids.RECEIVER,
            Ids.ORACLE, Ids.POOLS, Ids.ROUTES, Ids.TRANSPORT];
        for (uint256 i; i < ids.length; ++i) {
            address implementation = ids[i] == Ids.VAULT ? address(vault) : ids[i] == Ids.MIGRATION ? address(migration) :
                ids[i] == Ids.POOLS ? address(pools) : address(new BoundDummy(address(controller)));
            controller.bind(ids[i], implementation);
        }
        CanonicalFixture.bind(address(controller));
        controller.seal(); controller.setPaused(true);
        ZZZMigration.ParkingRequest memory r; r.bucketId = 7; r.poolId = bytes32(uint256(7)); r.lpTokenId = 99;
        r.totalShares = 200e18; r.depositUSD = 200e18; r.token0 = address(0x111); r.token1 = address(0x222);
        r.minimum0 = 100; r.minimum1 = 100; r.deadline = block.timestamp + 100; r.reviewHash = keccak256("independent-close-review");
        bytes memory callData = abi.encodeCall(migration.park, (r)); bytes32 salt = keccak256("exact-paused-custody-authorization");
        vm.expectRevert(); migration.park(r);
        controller.schedule(address(migration), 0, callData, bytes32(0), salt, 0);
        controller.execute(address(migration), 0, callData, bytes32(0), salt);
        assertEq(uint8(vault.group(7).status), uint8(PositionStatus.Parked)); assertEq(migration.parkingNonce(7), 1);
    }
}
