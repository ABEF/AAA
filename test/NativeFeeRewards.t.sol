// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZFeesCanonical} from "../src/ZZZFeesCanonical.sol";
import {MockAccess, MockToken, MockPools} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "../src/libraries/ZZZTypes.sol";

// TEST ONLY: isolated share/ownership fixture. Venue funding is exercised in the
// native custody suite; these tests exercise the real accounting modules.
contract NativeFeeAccess is MockAccess {
    function settle(bool value) external { canonicalSettling = value; }
}
contract NativeFeeVault {
    ZZZRewards public rewards;
    mapping(uint256 => uint256) public nftBucket;
    mapping(uint256 => uint256) public sharesOf;
    mapping(uint256 => uint256) public bucketTotalShares;
    mapping(uint256 => Position) private positions;
    uint64 public epoch;
    constructor(ZZZRewards r) { rewards = r; }
    receive() external payable {}
    function migrationBudget() external view returns (address) { return address(this); }
    function compositionEpoch(uint256) external view returns (uint64) { return epoch; }
    function setEpoch(uint64 e) external { epoch = e; }
    function bucketCount() external pure returns (uint256) { return 1; }
    function bucketAt(uint256 i) external pure returns (uint256) { require(i == 0); return 11; }
    function MAX_BUCKETS() external pure returns (uint256) { return 4; }
    function mintProceedsRecipient() external pure returns (address payable) { return payable(address(0x7EA5)); }
    function set(Position memory p) external { positions[11] = p; }
    function group(uint256 id) external view returns (Position memory) { return positions[id]; }
    function join(uint256 id, uint256 amount) external {
        nftBucket[id] = 11;
        rewards.checkpointOwner(id);
        sharesOf[id] += amount; bucketTotalShares[11] += amount;
    }
}
contract NativeConvertedCreditFixture is ZZZRewards {
    constructor(address controller) ZZZRewards(controller) {}
    // TEST ONLY: the converter's exact received ETH has already been attributed
    // to an NFT. It must not be replayed into the native fee indices.
    function convertedCredit(uint256 id, uint256 personal, uint256 shared) external payable {
        require(msg.value == personal + shared);
        individual[id][address(0)] += personal; collective[id][address(0)] += shared;
        liabilities[address(0)] += msg.value;
    }
}
contract RejectNativeClaim {
    receive() external payable { revert(); }
    function claim(ZZZRewards rewards, uint256 id) external { rewards.claim(id, address(0)); }
}

interface INativeFeeCaptureHook { function attemptCaptureDuringIntake() external; }
// TEST ONLY: hostile admitted token tries to freeze the whole system from its
// transfer callback; no unbounded reentrancy or public deployment is involved.
contract NativeFeeCaptureToken is MockToken {
    address private feeTarget;
    address private callback;
    constructor(address fees, address target) MockToken(18) { feeTarget = fees; callback = target; }
    function _update(address from, address to, uint256 amount) internal override {
        super._update(from, to, amount);
        if (from != address(0) && to == feeTarget) INativeFeeCaptureHook(callback).attemptCaptureDuringIntake();
    }
}

contract NativeFeeRewardsTest is Test {
    NativeFeeAccess ac;
    MockToken token;
    MockPools pools;
    NativeFeeVault vault;
    ZZZNFT nft;
    ZZZMembership membership;
    NativeConvertedCreditFixture rewards;
    ZZZFeeController fees;
    ZZZFeesCanonical canonical;
    NativeFeeCaptureToken captureToken;
    bool private captureBlocked;
    address constant ALICE = address(0xA11CE);
    address constant BOB = address(0xB0B);
    bytes32 constant POOL = keccak256("native-accounting");
    receive() external payable {}

    function setUp() public {
        ac = new NativeFeeAccess(); token = new MockToken(18); pools = new MockPools();
        rewards = new NativeConvertedCreditFixture(address(ac));
        vault = new NativeFeeVault(rewards); nft = new ZZZNFT(address(ac), "ipfs://");
        membership = new ZZZMembership(address(ac)); fees = new ZZZFeeController(address(ac));
        canonical = new ZZZFeesCanonical(address(ac), address(fees));
        ac.bind(Ids.VAULT, address(vault)); ac.bind(Ids.NFT, address(nft)); ac.bind(Ids.MEMBERSHIP, address(membership));
        ac.bind(Ids.REWARDS, address(rewards)); ac.bind(Ids.FEES, address(fees)); ac.bind(Ids.POOLS, address(pools));
        ac.bind(Ids.BUYBACK, address(this)); ac.bind(Ids.CANONICAL, address(this)); ac.bind(Ids.FEES_CANONICAL, address(canonical));
        rewards.addAsset(address(token));
        ProtocolPolicyFixture.randomness(address(nft.access()),address(new MockVRF()),bytes32(uint256(1)),1,3,500000,false);
        ac.seal();
        PoolConfig memory c; c.key.currency1 = address(token); pools.set(POOL, c);
        Position memory p; p.poolId = POOL; p.status = PositionStatus.Active;
        vault.set(p);
        vm.deal(address(vault), 100 ether); vm.deal(address(fees), 0); vm.deal(address(this), 100 ether);
    }
    function _seed(uint256 id, address owner, uint256 shares, bool active) private {
        vm.prank(address(vault)); nft.mint(owner, id); vault.join(id, shares);
        if (active) { vm.prank(address(vault)); membership.activate(id); }
    }
    function _allocate(uint256 amount) private {
        vm.prank(address(vault)); fees.allocate{value: amount}(11, address(0), amount);
    }
    function _credit(uint256 personal, uint256 shared) private {
        vm.deal(address(fees), address(fees).balance + personal + shared);
        vm.prank(address(fees)); rewards.creditPool{value: personal + shared}(11, address(0), personal, shared);
    }
    function testNativeFeeSplitIsIndexedAndSeparatelyBacked() public {
        _seed(1, ALICE, 100, true); _seed(2, BOB, 300, true); _allocate(1000);
        assertEq(rewards.claimable(1, address(0)), 250); assertEq(rewards.claimable(2, address(0)), 650);
        assertEq(rewards.liabilities(address(0)), 900); assertEq(address(rewards).balance, 900);
        assertEq(fees.compoundBalance(11, address(0)), 50); assertEq(fees.buybackBalance(address(0)), 50);
        assertEq(fees.accounted(address(0)), 100); assertEq(address(fees).balance, 100);
        assertGt(rewards.index(address(0)), 0); assertGt(rewards.ownerIndex(11, address(0)), 0);
    }
    function testNativeIngressRequiresExactValueAndRejectsTokenValueEvenWithPrefunds() public {
        _seed(1, ALICE, 100, true); vm.deal(address(fees), 1000); vm.deal(address(rewards), 1000);
        vm.prank(address(vault)); vm.expectRevert(); fees.allocate{value: 99}(11, address(0), 100);
        vm.prank(address(vault)); vm.expectRevert(); fees.allocate{value: 101}(11, address(0), 100);
        vm.prank(address(vault)); vm.expectRevert(); fees.allocate{value: 1}(11, address(token), 100);
        vm.prank(address(fees)); vm.expectRevert(); rewards.creditPool{value: 99}(11, address(0), 80, 20);
        vm.prank(address(fees)); vm.expectRevert(); rewards.creditPool{value: 101}(11, address(0), 80, 20);
        vm.prank(address(fees)); vm.expectRevert(); rewards.creditPool{value: 1}(11, address(token), 80, 20);
        assertEq(fees.accounted(address(0)), 0); assertEq(rewards.liabilities(address(0)), 0);
    }
    function testNativeTopUpAndLaterActivationExcludeHistoricalIncome() public {
        _seed(1, ALICE, 100, true); _allocate(1000); _seed(2, BOB, 100, true);
        assertEq(rewards.claimable(1, address(0)), 900); assertEq(rewards.claimable(2, address(0)), 0);
        _allocate(1000); vault.join(1, 200); _allocate(1000);
        assertEq(rewards.claimable(1, address(0)), 2000); assertEq(rewards.claimable(2, address(0)), 700);
        assertEq(membership.totalEligible(), 2);
    }
    function testNativeFractionsSurviveClaimsAndShareChanges() public {
        _seed(1, ALICE, 1, false); _seed(2, BOB, 3, false); _credit(1, 0);
        vm.prank(ALICE); assertEq(rewards.claim(1, address(0)), 0);
        assertEq(rewards.ownerFraction(1, address(0)), rewards.SCALE() / 4);
        vault.join(1, 3); _credit(7, 0);
        vm.prank(ALICE); assertEq(rewards.claim(1, address(0)), 4);
        vm.prank(BOB); assertEq(rewards.claim(2, address(0)), 3);
        assertEq(rewards.liabilities(address(0)), 1); assertEq(address(rewards).balance, 1);
    }
    function testNativeOrphansAndDonationsCannotRewardFutureMembership() public {
        _seed(1, ALICE, 100, false); vm.deal(address(rewards), 1000); _credit(50, 30);
        vm.prank(address(vault)); membership.activate(1);
        assertEq(rewards.claimable(1, address(0)), 50); assertEq(rewards.orphaned(address(0)), 30);
        assertEq(rewards.liabilities(address(0)), 50); assertEq(address(rewards).balance, 1080);
    }
    function testNativeTransferCarriesUnclaimedRightsAndClaimStillWorksPaused() public {
        _seed(1, ALICE, 100, true); _allocate(1000);
        vm.prank(ALICE); nft.transferFrom(ALICE, BOB, 1); ac.setPaused(true);
        vm.prank(ALICE); vm.expectRevert(); rewards.claim(1, address(0));
        vm.prank(BOB); assertEq(rewards.claim(1, address(0)), 900);
        vm.prank(BOB); assertEq(rewards.claim(1, address(0)), 0);
        assertEq(BOB.balance, 900); assertEq(rewards.liabilities(address(0)), 0);
    }
    function testRejectingNativeOwnerRevertsWholeClaim() public {
        _seed(1, ALICE, 100, true); _allocate(1000); RejectNativeClaim owner = new RejectNativeClaim();
        vm.prank(ALICE); nft.transferFrom(ALICE, address(owner), 1);
        vm.expectRevert(); owner.claim(rewards, 1);
        assertEq(rewards.claimable(1, address(0)), 900); assertEq(rewards.liabilities(address(0)), 900);
        assertEq(address(rewards).balance, 900);
    }
    function testConvertedNativeCreditsCoexistWithoutReindexing() public {
        _seed(1, ALICE, 100, true); rewards.convertedCredit{value: 300}(1, 200, 100); _allocate(1000);
        assertEq(rewards.claimable(1, address(0)), 1200); assertEq(rewards.liabilities(address(0)), 1200);
        vm.prank(ALICE); assertEq(rewards.claim(1, address(0)), 1200);
        assertEq(address(rewards).balance, 0);
    }
    function testHistoricalNativeDustIsFlushedWithAll33Currencies() public {
        _seed(1, ALICE, 100, true); _allocate(19);
        for (uint256 i; i < 31; ++i) rewards.addAsset(address(new MockToken(18)));
        assertEq(rewards.assetCount(), 33);
        PoolConfig memory c; c.key.currency0 = address(token); c.key.currency1 = rewards.assets(2); pools.set(POOL, c);
        vault.setEpoch(1);
        vm.prank(address(vault)); membership.settleDust();
        assertEq(rewards.claimable(1, address(0)), 19); assertEq(fees.dust(11, address(0)), 0);
        _seed(2, BOB, 100, true); assertEq(rewards.claimable(2, address(0)), 0);
    }
    function testNativeReservesReleaseOnlyTheirClassifiedBacking() public {
        _seed(1, ALICE, 100, true); _allocate(1000);
        uint256 beforeVault = address(vault).balance;
        vm.prank(address(vault)); assertEq(fees.releaseCompound(11, address(0)), 50);
        assertEq(address(vault).balance, beforeVault + 50);
        fees.releaseBuyback(address(0), 50);
        assertEq(address(fees).balance, 0); assertEq(address(rewards).balance, 900);
    }
    function testNativeRewardCanonicalCodecPreservesIndicesFractionsOrphansAndConvertedCredits() public {
        _seed(1, ALICE, 1, false); _seed(2, BOB, 3, false); _credit(1, 3);
        vm.prank(ALICE); assertEq(rewards.claim(1, address(0)), 0);
        vm.prank(address(vault)); membership.activate(1);
        vm.prank(address(vault)); membership.activate(2);
        _credit(1, 1); vm.prank(ALICE); rewards.claim(1, address(0));
        rewards.convertedCredit{value: 2}(1, 1, 1);
        assertEq(rewards.orphaned(address(0)), 3);
        assertGt(rewards.ownerFraction(1, address(0)), 0); assertGt(rewards.fraction(1, address(0)), 0);
        ac.setCanonicalState(1); rewards.canonicalCapture();

        NativeFeeAccess nextAccess = new NativeFeeAccess();
        NativeConvertedCreditFixture next = new NativeConvertedCreditFixture(address(nextAccess));
        NativeFeeVault nextVault = new NativeFeeVault(next);
        nextAccess.bind(Ids.VAULT, address(nextVault)); nextAccess.bind(Ids.NFT, address(nft));
        // Identity and membership reads are intentionally fixed fixtures here;
        // full controller/NFT handoff validation belongs to the canonical suite.
        nextAccess.bind(Ids.MEMBERSHIP, address(membership)); nextAccess.bind(Ids.CANONICAL, address(this));
        nextAccess.seal(); nextVault.join(1, 1); nextVault.join(2, 3);
        vm.deal(address(next), 13); nextAccess.setCanonicalState(2);
        for (uint256 row; row < rewards.canonicalCount(); ++row) next.canonicalImport(row, rewards.canonicalExport(row));
        for (uint256 i; i < rewards.canonicalAssetCount(); ++i) {
            rewards.canonicalRelease(i, address(next)); next.canonicalAccept(i, address(rewards));
        }
        next.canonicalValidate();
        assertEq(next.index(address(0)), rewards.index(address(0)));
        assertEq(next.ownerIndex(11, address(0)), rewards.ownerIndex(11, address(0)));
        assertEq(next.paidIndex(1, address(0)), rewards.paidIndex(1, address(0)));
        assertEq(next.paidOwnerIndex(1, address(0)), rewards.paidOwnerIndex(1, address(0)));
        assertEq(next.fraction(1, address(0)), rewards.fraction(1, address(0)));
        assertEq(next.ownerFraction(1, address(0)), rewards.ownerFraction(1, address(0)));
        assertEq(next.orphaned(address(0)), 3); assertEq(next.liabilities(address(0)), 5);
        nextAccess.setCanonicalState(0);
        assertEq(next.claimable(1, address(0)), 2); assertEq(next.claimable(2, address(0)), 1);
        vm.prank(ALICE); assertEq(next.claim(1, address(0)), 2);
        vm.prank(BOB); assertEq(next.claim(2, address(0)), 1);
        assertEq(address(next).balance, 18); // 13 prefund + 3 orphan + 2 reserved fractions/dust.
    }
    function testFuzzNativeFeeChunkingPreservesFundsAndAllocation(uint96 a, uint96 b) public {
        uint256 first = bound(uint256(a), 1, 10 ether); uint256 second = bound(uint256(b), 1, 10 ether);
        _seed(1, ALICE, 100, true); _allocate(first); _allocate(second);
        uint256 total = first + second; uint256 units = total / 20;
        assertEq(rewards.claimable(1, address(0)), units * 18);
        assertEq(fees.compoundBalance(11, address(0)), units); assertEq(fees.buybackBalance(address(0)), units);
        assertEq(fees.dust(11, address(0)), total % 20);
        assertEq(fees.accounted(address(0)), units * 2 + total % 20);
        vm.prank(ALICE); uint256 paid = rewards.claim(1, address(0));
        assertEq(address(fees).balance + address(rewards).balance + paid, total);
    }
    function testCanonicalLPOnlyReservesAndDonationQuarantineMigrateThenRestore() public {
        _seed(1, ALICE, 100, true); _allocate(1000);
        vm.deal(address(fees), address(fees).balance + 7);
        ac.setCanonicalState(1); ac.settle(true); rewards.canonicalCapture(); canonical.canonicalCapture(); canonical.canonicalSettle();
        assertEq(rewards.liabilities(address(0)), 900); assertEq(address(rewards).balance, 900);
        (address asset, uint256 amount) = canonical.canonicalBacking(0); assertEq(asset, address(0)); assertEq(amount, 107);
        assertEq(canonical.canonicalAssetCount(), 2);
        assertEq(canonical.canonicalExport(0).length, 64);
        assertEq(canonical.canonicalExport(3).length, 128);

        NativeFeeAccess destination = new NativeFeeAccess();
        ZZZFeeController nextFees = new ZZZFeeController(address(destination));
        ZZZFeesCanonical next = new ZZZFeesCanonical(address(destination), address(nextFees));
        destination.bind(Ids.VAULT, address(vault)); destination.bind(Ids.FEES, address(nextFees));
        destination.bind(Ids.FEES_CANONICAL, address(next)); destination.bind(Ids.CANONICAL, address(this));
        destination.setCanonicalState(2); vm.deal(address(next), 13);
        for (uint256 row; row < canonical.canonicalCount(); ++row) next.canonicalImport(row, canonical.canonicalExport(row));
        vm.expectRevert(); next.canonicalAccept(0, address(canonical));
        for (uint256 i; i < canonical.canonicalAssetCount(); ++i) {
            canonical.canonicalRelease(i, address(next)); next.canonicalAccept(i, address(canonical));
        }
        next.canonicalValidate(); assertEq(address(next).balance, 13); assertEq(address(nextFees).balance, 107);
        assertEq(nextFees.compoundBalance(11, address(0)), 50);
        assertEq(nextFees.buybackBalance(address(0)), 50); assertEq(nextFees.accounted(address(0)), 100);
        vm.expectRevert(); next.canonicalAccept(0, address(canonical));
        destination.setCanonicalState(4);
        for (uint256 i; i < canonical.canonicalAssetCount(); ++i) {
            next.canonicalRelease(i, address(canonical)); canonical.canonicalRestore(i, address(next));
        }
        canonical.canonicalValidate(); assertEq(address(fees).balance, 107);
        assertEq(fees.accounted(address(0)), 100); assertEq(fees.compoundBalance(11, address(0)), 50);
        assertEq(fees.buybackBalance(address(0)), 50);
        assertEq(address(rewards).balance, 900); assertEq(address(next).balance, 13);
    }
    function testLPOnlyFeesRejectInactiveBucketsAndRetiredIntakeSelectors() public {
        _seed(1, ALICE, 100, true);
        Position memory p = vault.group(11); p.status = PositionStatus.Outbound; vault.set(p);
        vm.prank(address(vault)); vm.expectRevert(); fees.allocate{value: 100}(11, address(0), 100);
        p.status = PositionStatus.Parked; vault.set(p);
        vm.prank(address(vault)); vm.expectRevert(); fees.allocate{value: 100}(11, address(0), 100);
        assertEq(fees.accounted(address(0)), 0); assertEq(rewards.liabilities(address(0)), 0);
        (bool creator,) = address(fees).call{value: 100}(abi.encodeWithSignature("allocateExternal(uint256,address,uint256)",11,address(0),100));
        (bool receiver,) = address(fees).call(abi.encodeWithSignature("createRewardReceiver(uint256,address)",11,address(0)));
        (bool remote,) = address(fees).call{value: 100}(abi.encodeWithSignature("creditRemote(uint256,address,uint256,uint256)",11,address(0),80,20));
        (bool bridge,) = address(fees).call(abi.encodeWithSignature("bridgeRewards(uint256,address,bytes32)",11,address(0),bytes32(0)));
        assertFalse(creator); assertFalse(receiver); assertFalse(remote); assertFalse(bridge);
        assertEq(fees.FEE_INTAKE_VERSION(), 1); assertEq(address(fees).balance, 0);
    }
    function attemptCaptureDuringIntake() external {
        require(msg.sender == address(captureToken));
        ac.setCanonicalState(1);
        (bool ok, bytes memory reason) = address(canonical).call(abi.encodeCall(canonical.canonicalCapture, ()));
        assertFalse(ok);
        assertEq(reason, abi.encodeWithSignature("ReentrancyGuardReentrantCall()"));
        captureBlocked = true;
        ac.setCanonicalState(0);
    }
    function testCanonicalCaptureBarrierRejectsMidReceiptCallbackWithoutBlockingTheFee() public {
        _seed(1, ALICE, 100, true);
        captureToken = new NativeFeeCaptureToken(address(fees), address(this));
        rewards.addAsset(address(captureToken));
        PoolConfig memory c; c.key.currency1 = address(captureToken); pools.set(POOL, c);
        captureToken.mint(address(vault), 1000);
        vm.startPrank(address(vault)); captureToken.approve(address(fees), 1000);
        fees.allocate(11, address(captureToken), 1000); vm.stopPrank();
        assertTrue(captureBlocked); assertEq(ac.canonicalState(), 0);
        assertEq(rewards.claimable(1, address(captureToken)), 900);
        assertEq(fees.accounted(address(captureToken)), 100);
        assertEq(captureToken.balanceOf(address(fees)), 100);
        assertEq(captureToken.balanceOf(address(rewards)), 900);
    }
    function testLPOnlyFeeCodecRejectsOlderHeadersAndExpandedBucketRows() public {
        ac.setCanonicalState(2);
        vm.expectRevert(); canonical.canonicalImport(0, abi.encode(uint256(2),uint256(1),uint256(0)));
        canonical.canonicalImport(0, abi.encode(uint256(2),uint256(1)));
        canonical.canonicalImport(1, abi.encode(address(0),uint256(0),uint256(0),uint256(0),uint256(0)));
        canonical.canonicalImport(2, abi.encode(address(token),uint256(0),uint256(0),uint256(0),uint256(0)));
        vm.expectRevert(); canonical.canonicalImport(3, abi.encode(uint256(11),address(0),uint256(0),uint256(0),uint256(0)));
        canonical.canonicalImport(3, abi.encode(uint256(11),address(0),uint256(0),uint256(0)));
        canonical.canonicalImport(4, abi.encode(uint256(11),address(token),uint256(0),uint256(0)));
        vm.expectRevert(); canonical.canonicalImport(5, abi.encode(uint256(11),address(token),uint256(0),uint256(0)));
        canonical.canonicalValidate();
    }
    function testCanonical33CurrencySourceCompanionPrefundsSurviveAbortAndRecapture() public {
        _seed(1, ALICE, 100, true); _allocate(1000);
        token.mint(address(vault), 1000);
        vm.startPrank(address(vault)); token.approve(address(fees), 1000); fees.allocate(11, address(token), 1000); vm.stopPrank();
        for (uint256 i; i < 31; ++i) rewards.addAsset(address(new MockToken(18)));
        assertEq(rewards.assetCount(), 33);
        vm.deal(address(canonical), 1);
        for (uint256 i = 1; i < 33; ++i) MockToken(rewards.assets(i)).mint(address(canonical), 1);
        ac.setCanonicalState(1); rewards.canonicalCapture(); canonical.canonicalCapture(); canonical.canonicalSettle();

        NativeFeeAccess destination = new NativeFeeAccess();
        ZZZFeeController nextFees = new ZZZFeeController(address(destination));
        ZZZFeesCanonical next = new ZZZFeesCanonical(address(destination), address(nextFees));
        destination.bind(Ids.VAULT, address(vault)); destination.bind(Ids.FEES, address(nextFees));
        destination.bind(Ids.FEES_CANONICAL, address(next)); destination.bind(Ids.CANONICAL, address(this));
        destination.setCanonicalState(2); vm.deal(address(next), 1);
        for (uint256 i = 1; i < 33; ++i) MockToken(rewards.assets(i)).mint(address(next), 1);
        for (uint256 row; row < canonical.canonicalCount(); ++row) next.canonicalImport(row, canonical.canonicalExport(row));
        for (uint256 i; i < 33; ++i) {
            canonical.canonicalRelease(i, address(next)); next.canonicalAccept(i, address(canonical));
        }
        next.canonicalValidate(); destination.setCanonicalState(4);
        for (uint256 i; i < 33; ++i) {
            (address asset, uint256 amount) = canonical.canonicalBacking(i);
            uint256 beforeBalance = asset == address(0) ? address(canonical).balance : MockToken(asset).balanceOf(address(canonical));
            next.canonicalRelease(i, address(canonical));
            uint256 receivedBalance = asset == address(0) ? address(canonical).balance : MockToken(asset).balanceOf(address(canonical));
            assertEq(receivedBalance, beforeBalance + amount); // Handoff.returnFunds authenticates this exact delta.
            canonical.canonicalRestore(i, address(next));
            assertEq(asset == address(0) ? address(canonical).balance : MockToken(asset).balanceOf(address(canonical)), 1);
            assertEq(asset == address(0) ? address(next).balance : MockToken(asset).balanceOf(address(next)), 1);
        }
        canonical.canonicalValidate(); canonical.canonicalCapture(); canonical.canonicalSettle();
        (, uint256 nativeBacking) = canonical.canonicalBacking(0); (, uint256 tokenBacking) = canonical.canonicalBacking(1);
        assertEq(nativeBacking, 100); assertEq(tokenBacking, 100);
        assertEq(address(canonical).balance, 1); assertEq(address(rewards).balance, 900);
    }

    /// Independent arithmetic example: 6,000 received units, unequal LP shares,
    /// equal collective membership and a dormant NFT. Claims cannot spend 5/5.
    function testThreeHolderClaimsPreserveExactSplitAndDormantExclusion() public {
        _seed(1, ALICE, 1, true); _seed(2, BOB, 2, true);
        _seed(3, address(0xCA401), 7, true); _seed(4, address(0xDA7E), 0, false);
        _allocate(6000);
        assertEq(rewards.claimable(1, address(0)), 680); // 480 personal + 200 equal.
        assertEq(rewards.claimable(2, address(0)), 1160); // 960 + 200.
        assertEq(rewards.claimable(3, address(0)), 3560); // 3,360 + 200.
        assertEq(rewards.claimable(4, address(0)), 0);
        assertEq(membership.totalEligible(), 3);
        _isolatedClaim(2, address(0));
        assertEq(rewards.liabilities(address(0)), 4240);
        _isolatedClaim(1, address(0));
        vm.prank(address(0xCA401)); nft.transferFrom(address(0xCA401), address(0xE7E), 3);
        vm.prank(address(0xCA401)); vm.expectRevert(); rewards.claim(3, address(0));
        _isolatedClaim(3, address(0));
        assertEq(address(rewards).balance, 0); assertEq(rewards.liabilities(address(0)), 0);
        assertEq(fees.compoundBalance(11, address(0)), 300);
        assertEq(fees.buybackBalance(address(0)), 300);
        assertEq(address(fees).balance, 600); assertEq(fees.accounted(address(0)), 600);
        assertEq(_isolatedClaim(3, address(0)), 0);
    }

    /// Same funded history, different claim schedules: claims must not change
    /// lifetime NFT entitlement, fractions, indices or the two purpose reserves.
    /// This isolates accounting; real venue/rebalance coverage lives elsewhere.
    function testFuzzClaimOrderAndFrequencyCannotRedistributeAnyNftRewards(uint8 order, uint8 early) public {
        _seed(1, ALICE, 1, true); _seed(2, BOB, 2, true);
        _seed(3, address(0xCA401), 7, true); _seed(4, address(0xDA7E), 0, false);
        uint256 checkpoint = vm.snapshotState();
        bytes32 frequent = _claimSchedule(order, early);
        assertTrue(vm.revertToState(checkpoint));
        bytes32 deferred = _claimSchedule(uint8(23 - order % 24), 0);
        assertEq(frequent, deferred);
    }

    function _allocateToken(uint256 amount) private {
        token.mint(address(vault), amount);
        vm.startPrank(address(vault)); token.approve(address(fees), amount);
        fees.allocate(11, address(token), amount); vm.stopPrank();
    }
    function _assetBalance(address asset, address holder) private view returns (uint256) {
        return asset == address(0) ? holder.balance : token.balanceOf(holder);
    }
    function _isolatedClaim(uint256 id, address asset) private returns (uint256 amount) {
        uint256[4] memory beforeClaims;
        for (uint256 i; i < 4; ++i) beforeClaims[i] = rewards.claimable(i + 1, asset);
        bytes32 reserved = keccak256(abi.encode(fees.compoundBalance(11, asset), fees.buybackBalance(asset),
            fees.accounted(asset), fees.dust(11, asset), _assetBalance(asset, address(fees)),
            rewards.index(asset), rewards.ownerIndex(11, asset), membership.totalEligible(), vault.bucketTotalShares(11)));
        address owner = nft.ownerOf(id);
        uint256 beforeWallet = _assetBalance(asset, owner);
        uint256 beforeBacking = _assetBalance(asset, address(rewards));
        uint256 beforeLiability = rewards.liabilities(asset);
        vm.prank(owner); amount = rewards.claim(id, asset);
        assertEq(amount, beforeClaims[id - 1]);
        assertEq(_assetBalance(asset, owner), beforeWallet + amount);
        assertEq(_assetBalance(asset, address(rewards)), beforeBacking - amount);
        assertEq(rewards.liabilities(asset), beforeLiability - amount);
        for (uint256 i; i < 4; ++i) {
            assertEq(rewards.claimable(i + 1, asset), i + 1 == id ? 0 : beforeClaims[i]);
        }
        assertEq(reserved, keccak256(abi.encode(fees.compoundBalance(11, asset), fees.buybackBalance(asset),
            fees.accounted(asset), fees.dust(11, asset), _assetBalance(asset, address(fees)),
            rewards.index(asset), rewards.ownerIndex(11, asset), membership.totalEligible(), vault.bucketTotalShares(11))));
    }
    function _claims(uint256[4][2] memory paid, uint8 order, uint8 mask) private {
        uint256 remaining = 15;
        uint256 permutation = order % 24;
        for (uint256 slot; slot < 4; ++slot) {
            uint256 rank = permutation % (4 - slot); permutation /= 4 - slot;
            uint256 id;
            for (uint256 candidate; candidate < 4; ++candidate) {
                if ((remaining & (1 << candidate)) == 0) continue;
                if (rank == 0) { id = candidate + 1; break; }
                --rank;
            }
            remaining &= ~(1 << (id - 1));
            if ((uint256(mask) & (1 << (id - 1))) == 0) continue;
            paid[0][id - 1] += _isolatedClaim(id, address(0));
            paid[1][id - 1] += _isolatedClaim(id, address(token));
        }
    }
    function _claimSchedule(uint8 order, uint8 early) private returns (bytes32 result) {
        uint256[4][2] memory paid;
        _allocate(1003); _allocate(2); _allocate(997);
        _allocateToken(2007); _allocateToken(13);
        _claims(paid, order, early & 15);
        // Mirror the real Vault's funded-dust barrier and old-share checkpoint.
        vm.prank(address(vault)); membership.settleDust();
        vault.join(1, 3);
        vm.prank(address(vault)); membership.settleDust();
        vault.join(4, 6);
        vm.prank(address(vault)); membership.activate(4);
        assertEq(rewards.claimable(4, address(0)), 0);
        assertEq(rewards.claimable(4, address(token)), 0);
        _allocate(1019); _allocate(381); _allocateToken(83); _allocateToken(58);
        _claims(paid, uint8(23 - order % 24), early >> 4);
        vm.prank(address(0xCA401)); nft.transferFrom(address(0xCA401), address(0xE7E), 3);
        _allocate(41); _allocate(3); _allocate(1999); _allocateToken(4001); _allocateToken(17);
        _claims(paid, order, 15);
        _claims(paid, order, 15); // A second claim pays zero, preserving fractions.
        result = keccak256(abi.encode(paid));
        for (uint256 k; k < 2; ++k) {
            address asset = k == 0 ? address(0) : address(token);
            uint256 totalPaid;
            for (uint256 i; i < 4; ++i) {
                totalPaid += paid[k][i];
                result = keccak256(abi.encode(result, rewards.claimable(i + 1, asset),
                    rewards.fraction(i + 1, asset), rewards.ownerFraction(i + 1, asset)));
            }
            assertEq(totalPaid + _assetBalance(asset, address(rewards)) + _assetBalance(asset, address(fees)),
                k == 0 ? 5445 : 6179);
            assertEq(_assetBalance(asset, address(rewards)), rewards.liabilities(asset));
            assertEq(_assetBalance(asset, address(fees)), fees.accounted(asset));
            result = keccak256(abi.encode(result, rewards.index(asset), rewards.ownerIndex(11, asset),
                rewards.liabilities(asset), fees.compoundBalance(11, asset), fees.buybackBalance(asset),
                fees.dust(11, asset), fees.accounted(asset)));
        }
        assertEq(membership.totalEligible(), 4);
    }
}
