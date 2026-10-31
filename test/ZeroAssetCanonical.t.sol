// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess} from "./mocks/Mocks.sol";

/// @dev Controlled ownership/ordinal records, not a full NFT/reward ledger.
contract ZeroAssetNFTFixture {
    address public immutable access;
    uint256 public mintedCount;
    mapping(uint256 => uint256) public tokenAtOrdinal;
    mapping(uint256 => address) public ownerOf;
    constructor(address controller) { access = controller; }
    function seed(uint256 id, address owner) external {
        tokenAtOrdinal[++mintedCount] = id;
        ownerOf[id] = owner;
    }
}
contract ZeroAssetCheckpointFixture {
    ZZZMembership private immutable membership;
    mapping(uint256 => uint256) public checkpoints;
    mapping(uint256 => bool) public checkpointedBeforeEnrollment;
    constructor(ZZZMembership member) { membership = member; }
    function checkpointAll(uint256 id) external {
        ++checkpoints[id];
        checkpointedBeforeEnrollment[id] = !membership.eligible(id);
    }
}

/// @notice Actual Membership codec/authorization with controlled NFT/reward
/// dependencies. Funded asset ledgers and full NFT import keep separate tests.
contract ZeroAssetCanonicalTest is Test {
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address private constant CAROL = address(0xCA201);
    address private constant STRANGER = address(0xBAD);
    MockAccess private sourceAccess;
    ZZZMembership private source;
    ZeroAssetNFTFixture private sourceNFT;
    ZeroAssetCheckpointFixture private checkpoints;

    function setUp() public {
        (sourceAccess, source, sourceNFT, checkpoints) = _fresh();
    }
    function _fresh() private returns (MockAccess access, ZZZMembership member,
        ZeroAssetNFTFixture nft, ZeroAssetCheckpointFixture reward) {
        access = new MockAccess(); ProtocolPolicyFixture.bind(address(access)); member = new ZZZMembership(address(access));
        nft = new ZeroAssetNFTFixture(address(access)); reward = new ZeroAssetCheckpointFixture(member);
        nft.seed(101, ALICE); nft.seed(102, BOB); nft.seed(103, CAROL);
        access.bind(Ids.NFT, address(nft)); access.bind(Ids.MEMBERSHIP, address(member));
        access.bind(Ids.REWARDS, address(reward)); access.bind(Ids.VAULT, address(this));
        access.bind(Ids.CANONICAL, address(this)); access.seal();
    }
    function _retiredBackingHooks(address target) private {
        uint256 balance = address(this).balance;
        (bool ok, bytes memory result) = target.call(abi.encodeWithSignature("canonicalBacking(uint256)", 0));
        assertFalse(ok); assertEq(result.length, 0);
        (ok, result) = target.call(abi.encodeWithSignature("canonicalRelease(uint256,address)", 0, STRANGER));
        assertFalse(ok); assertEq(result.length, 0);
        (ok, result) = target.call{value: 1}(abi.encodeWithSignature("canonicalAccept(uint256,address)", 0, STRANGER));
        assertFalse(ok); assertEq(result.length, 0);
        (ok, result) = target.call{value: 1}(abi.encodeWithSignature("canonicalRestore(uint256,address)", 0, STRANGER));
        assertFalse(ok); assertEq(result.length, 0);
        assertEq(target.balance, 0); assertEq(address(this).balance, balance);
    }
    function testZeroAssetModulesRejectRemovedBackingHooksAndNativeFunding() public {
        ZZZNFTCanonical nftCodec = new ZZZNFTCanonical(address(sourceAccess), address(sourceNFT));
        assertEq(source.canonicalAssetCount(), 0); assertEq(nftCodec.canonicalAssetCount(), 0);
        vm.deal(address(this), 4);
        _retiredBackingHooks(address(source));
        _retiredBackingHooks(address(nftCodec));
    }
    function testMembershipKeepsVaultOnlySingleEqualEnrollmentAndFreezeChecks() public {
        vm.prank(STRANGER); vm.expectRevert(ZZZModule.Unauthorized.selector); source.activate(101);
        source.activate(101); source.activate(103);
        assertEq(source.totalEligible(), 2); assertTrue(source.eligible(101)); assertTrue(source.eligible(103));
        assertFalse(source.eligible(102)); assertEq(checkpoints.checkpoints(101), 1);
        assertTrue(checkpoints.checkpointedBeforeEnrollment(101));
        vm.expectRevert(ZZZModule.InvalidState.selector); source.activate(101);
        assertEq(source.totalEligible(), 2); assertEq(checkpoints.checkpoints(101), 1);
        sourceAccess.setCanonicalState(1);
        vm.expectRevert(ZZZModule.Unauthorized.selector); source.activate(102);
        assertEq(source.totalEligible(), 2); assertFalse(source.eligible(102));
        assertEq(checkpoints.checkpoints(102), 0);
    }
    function testMembershipRecordHandoffPreservesOrdinalsWeightsAndAuthorization() public {
        source.activate(101); source.activate(103);
        vm.expectRevert(ZZZMembership.CanonicalState.selector); source.canonicalCapture();
        sourceAccess.setCanonicalState(1);
        vm.prank(STRANGER); vm.expectRevert(ZZZMembership.CanonicalState.selector); source.canonicalCapture();
        source.canonicalCapture(); source.canonicalSettle();
        assertEq(source.canonicalCount(), 4); assertEq(source.canonicalAssetCount(), 0);
        (uint256 count, uint256 eligible) = abi.decode(source.canonicalExport(0), (uint256,uint256));
        assertEq(count, 3); assertEq(eligible, 2);
        bytes[4] memory rows;
        for (uint256 i; i < rows.length; ++i) rows[i] = source.canonicalExport(i);

        (MockAccess targetAccess, ZZZMembership target,,) = _fresh();
        targetAccess.setCanonicalState(2);
        vm.prank(STRANGER); vm.expectRevert(ZZZMembership.CanonicalState.selector);
        target.canonicalImport(0, rows[0]);
        target.canonicalImport(0, rows[0]);
        vm.expectRevert(ZZZMembership.CanonicalState.selector); target.canonicalImport(2, rows[2]);
        vm.expectRevert(ZZZMembership.CanonicalState.selector); target.canonicalImport(1, abi.encode(uint256(999), true));
        target.canonicalImport(1, rows[1]);
        vm.expectRevert(ZZZMembership.CanonicalState.selector); target.canonicalValidate();
        vm.expectRevert(ZZZMembership.CanonicalState.selector); target.canonicalImport(1, rows[1]);
        target.canonicalImport(2, rows[2]);
        target.canonicalImport(3, rows[3]);
        target.canonicalValidate();
        assertEq(target.totalEligible(), 2); assertTrue(target.eligible(101)); assertTrue(target.eligible(103));
        assertFalse(target.eligible(102)); assertEq(target.canonicalCount(), 4); assertEq(target.canonicalAssetCount(), 0);
        vm.prank(STRANGER); vm.expectRevert(ZZZMembership.CanonicalState.selector); target.canonicalActivate();
        target.canonicalActivate();
        // The coordinator, not this hook, performs the canonical authority transition.
        assertEq(targetAccess.canonicalState(), 2);
        targetAccess.setCanonicalState(0); target.activate(102);
        assertEq(target.totalEligible(), 3); assertTrue(target.eligible(102));
    }
}
