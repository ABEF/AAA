// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture, VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {Test} from "forge-std/Test.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ids, PoolConfig, Position, PositionStatus, BridgeMessage, MessageKind} from "../src/libraries/ZZZTypes.sol";

interface ExternalRewardInbox {
    function sync() external;
    function pending() external view returns (uint256, uint256);
    function protected0() external view returns (uint256);
    function protected1() external view returns (uint256);
    function protectedNative() external view returns (uint256);
}

/// @dev TEST ONLY. A conventional wrapper deposit mock, not a deployed WETH implementation.
contract ExternalRewardWETH is MockToken {
    constructor() MockToken(18) {}
    function deposit() external payable virtual { _mint(msg.sender, msg.value); }
}

contract BrokenExternalRewardWETH is ExternalRewardWETH {
    function deposit() external payable override { _mint(msg.sender, msg.value - 1); }
}

contract ReentrantExternalRewardWETH is ExternalRewardWETH {
    bool public attempted;
    bool public reentrySucceeded;
    function deposit() external payable override {
        attempted = true;
        (reentrySucceeded,) = msg.sender.call(abi.encodeCall(ExternalRewardInbox.sync, ()));
        _mint(msg.sender, msg.value);
    }
}

contract ExternalPendingMigration {
    function activePlan(uint256) external pure returns (bytes32) { return bytes32(uint256(1)); }
}

contract ExternalEmptyMigration {
    function activePlan(uint256) external pure returns (bytes32) { return bytes32(0); }
}

contract LowGasExternalPayment {
    function pay(address payable inbox) external payable { inbox.transfer(msg.value); }
}

/// @dev Exact-transfer venue with an adversarial payment callback after LP funds
/// move but before increase/mint returns. It deliberately models a dependency
/// beyond the currently fixed, hookless Uniswap implementation.
contract LateExternalPaymentVenue is ERC721 {
    MockToken public t0; MockToken public t1;
    uint256 public next = 1; uint256 public spendBps = 9900;
    uint256 public fee0; uint256 public fee1;
    mapping(uint256 => uint256) public a0; mapping(uint256 => uint256) public a1;
    address public paymentInbox; uint256 public paymentAmount; bool public syncPayment;
    constructor(address token0, address token1) ERC721("Late callback venue", "LCV") { t0 = MockToken(token0); t1 = MockToken(token1); }
    function positionManager() external view returns (address) { return address(this); }
    function setSpendBps(uint256 bps) external { spendBps = bps; }
    function setFees(uint256 x, uint256 y) external { fee0 = x; fee1 = y; }
    function configurePayment(address inbox, uint256 amount, bool process) external {
        require(paymentAmount == 0);
        paymentInbox = inbox; paymentAmount = amount; syncPayment = process;
        t0.mint(address(this), amount);
    }
    function amounts(uint256 id) external view returns (uint256, uint256) { return (a0[id], a1[id]); }
    function _fund(uint256 id, uint256 x, uint256 y) private returns (uint256 spent0, uint256 spent1) {
        spent0 = x * spendBps / 10000; spent1 = y * spendBps / 10000;
        require(t0.transferFrom(msg.sender, address(this), spent0)); require(t1.transferFrom(msg.sender, address(this), spent1));
        a0[id] += spent0; a1[id] += spent1;
        if (paymentAmount != 0) {
            address inbox = paymentInbox; uint256 amount = paymentAmount; bool process = syncPayment;
            paymentInbox = address(0); paymentAmount = 0;
            require(t0.transfer(inbox, amount));
            if (process) ExternalRewardInbox(inbox).sync();
        }
    }
    function mint(bytes32, int24, int24, uint256 x, uint256 y, uint128, uint256)
        external returns (uint256 id, uint256 spent0, uint256 spent1) {
        id = next++; _mint(msg.sender, id); (spent0, spent1) = _fund(id, x, y);
    }
    function increase(bytes32, uint256 id, uint256 x, uint256 y, uint128, uint256)
        external returns (uint256, uint256) { return _fund(id, x, y); }
    function collect(bytes32, uint256, uint256) external {
        uint256 x = fee0; uint256 y = fee1; fee0 = 0; fee1 = 0; t0.mint(msg.sender, x); t1.mint(msg.sender, y);
    }
    function close(bytes32, uint256 id, uint256) external {
        uint256 x = a0[id]; uint256 y = a1[id]; delete a0[id]; delete a1[id]; _burn(id);
        require(t0.transfer(msg.sender, x)); require(t1.transfer(msg.sender, y));
    }
}

/// @dev The main transfer is exact and untaxed. A second, independently funded
/// transfer queues a new payment during Fees -> Vault compound delivery.
contract RequeueExternalRewardToken is MockToken {
    address private triggerFrom; address private triggerTo; address private queuedInbox; uint256 private queuedAmount;
    constructor() MockToken(0) {}
    function configureRequeue(address from, address to, address inbox, uint256 amount) external {
        triggerFrom = from; triggerTo = to; queuedInbox = inbox; queuedAmount = amount;
        _mint(address(this), amount);
    }
    function _update(address from, address to, uint256 amount) internal override {
        super._update(from, to, amount);
        if (from == triggerFrom && to == triggerTo && queuedAmount != 0) {
            uint256 payment = queuedAmount; queuedAmount = 0;
            super._update(address(this), queuedInbox, payment);
        }
    }
}

contract ExternalTaxToken is MockToken {
    bool public taxed;
    constructor() MockToken(18) {}
    function enableTax() external { taxed = true; }
    function _update(address from, address to, uint256 amount) internal override {
        if (taxed && from != address(0) && to != address(0) && amount >= 10) {
            super._update(from, address(0), amount / 10);
            amount -= amount / 10;
        }
        super._update(from, to, amount);
    }
}

/// @dev Independently records user deposits and plain external payments, keeping
/// pending inbox balances separate from funded claims and permanently locked LP.
contract ExternalFundingHandler is PooledVaultFixture {
    uint256[] public ids;
    mapping(uint256 => address) public owners;
    address public inbox;
    uint256 private bucket;
    uint256[2] private deposited;
    uint256[2] private externalGross;
    uint256[2] private paid;
    uint256 private expectedEligible;
    address private constant CREATOR = address(0xC2EA70);

    constructor() {
        setUp(); ac.bind(Ids.MIGRATION, address(new ExternalEmptyMigration()));
        mint(false); activate(0); mint(true);
        bucket = vault.poolBucket(poolId);
        inbox = fees.createRewardReceiver(bucket, address(0));
    }

    function mint(bool second) public {
        if (ac.paused() || ids.length >= 8) return;
        address owner = second ? bob : alice; vm.deal(owner, 10 ether);
        uint256 id = _mint(owner); ids.push(id); owners[id] = owner;
        assertEq(vault.sharesOf(id), 0); assertFalse(membership.eligible(id));
    }

    function activate(uint256 seed) public {
        uint256 id = ids[seed % ids.length];
        if (ac.paused() || vault.nftBucket(id) != 0) return;
        vm.prank(owners[id]); vault.activate(id, poolId, 1000, 1000, 1, block.timestamp + 100);
        deposited[0] += 1000; deposited[1] += 1000; ++expectedEligible;
        assertTrue(membership.eligible(id));
        assertEq(rewards.claimable(id, address(t0)), 0, "new participant received old external revenue");
        assertEq(rewards.claimable(id, address(t1)), 0, "new participant received old external revenue");
    }

    function topUp(uint256 seed, uint256 amount) external {
        uint256 id = ids[seed % ids.length];
        if (ac.paused() || vault.nftBucket(id) == 0) return;
        amount = bound(amount, 1, 100);
        uint256 old0 = rewards.claimable(id, address(t0)); uint256 old1 = rewards.claimable(id, address(t1));
        vm.prank(owners[id]); vault.increase(id, amount, amount, 1, block.timestamp + 100);
        deposited[0] += amount; deposited[1] += amount;
        assertEq(membership.totalEligible(), expectedEligible, "top-up changed collective membership");
        assertGe(rewards.claimable(id, address(t0)), old0); assertGe(rewards.claimable(id, address(t1)), old1);
    }

    function fund(uint256 amount, bool second) public {
        amount = bound(amount, 1, 1000); MockToken token = second ? t1 : t0;
        token.mint(CREATOR, amount); vm.prank(CREATOR); assertTrue(token.transfer(inbox, amount));
        externalGross[second ? 1 : 0] += amount;
    }

    function sync() public { ExternalRewardInbox(inbox).sync(); }

    function claim(uint256 seed, bool second) public {
        uint256 id = ids[seed % ids.length]; address token = second ? address(t1) : address(t0);
        uint256 expected = rewards.claimable(id, token);
        vm.prank(owners[id]); uint256 amount = rewards.claim(id, token);
        assertEq(amount, expected); paid[second ? 1 : 0] += amount;
    }

    function transfer(uint256 seed) external {
        uint256 id = ids[seed % ids.length]; address old = owners[id]; address next = old == alice ? bob : alice;
        uint256 shares = vault.sharesOf(id); uint256 entitlement = rewards.claimable(id, address(t0));
        vm.prank(old); nft.transferFrom(old, next, id); owners[id] = next;
        assertEq(vault.sharesOf(id), shares); assertEq(rewards.claimable(id, address(t0)), entitlement);
    }

    function paused(bool state) external { ac.setPaused(state); }

    function compound() external {
        if (ac.paused()) return;
        sync();
        if (fees.compoundBalance(bucket, address(t0)) + fees.compoundBalance(bucket, address(t1)) == 0) return;
        compounder.compound(bucket, 1, block.timestamp + 100);
    }

    function rebalance() external {
        if (ac.paused()) return;
        uint256 shares = vault.bucketTotalShares(bucket);
        vault.rebalance(bucket, 1, block.timestamp + 100);
        assertEq(vault.bucketTotalShares(bucket), shares);
    }

    function assertConservation() external view {
        Position memory p = vault.group(bucket); uint256 shares; uint256 contribution; uint256[2] memory claims;
        for (uint256 i; i < ids.length; ++i) {
            uint256 id = ids[i]; assertEq(nft.ownerOf(id), owners[id]);
            shares += vault.sharesOf(id); contribution += vault.contributionUSD(id);
            assertEq(membership.eligible(id), vault.nftBucket(id) != 0);
            if (vault.nftBucket(id) == 0) assertEq(vault.sharesOf(id), 0);
            claims[0] += rewards.claimable(id, address(t0)); claims[1] += rewards.claimable(id, address(t1));
        }
        assertEq(shares, vault.bucketTotalShares(bucket)); assertEq(contribution, p.depositUSD);
        assertEq(membership.totalEligible(), expectedEligible);
        assertEq(contribution, (deposited[0] + deposited[1]) * 1e18);
        assertEq(vault.bucketCount(), 1); assertEq(venue.ownerOf(p.lpTokenId), address(vault));
        assertEq(t0.balanceOf(address(vault)), p.idle0); assertEq(t1.balanceOf(address(vault)), p.idle1);
        for (uint256 i; i < 2; ++i) {
            MockToken token = i == 0 ? t0 : t1;
            uint256 principal = i == 0 ? venue.a0(p.lpTokenId) + p.idle0 : venue.a1(p.lpTokenId) + p.idle1;
            uint256 liability = rewards.liabilities(address(token)); uint256 orphaned = rewards.orphaned(address(token));
            uint256 rewardBalance = token.balanceOf(address(rewards)); uint256 feeBalance = token.balanceOf(address(fees));
            uint256 pendingBalance = token.balanceOf(inbox);
            assertLe(claims[i], liability, "unfunded external claim"); assertEq(rewardBalance, liability + orphaned);
            assertEq(feeBalance, fees.accounted(address(token)));
            assertEq(feeBalance, fees.dust(bucket, address(token)) + fees.compoundBalance(bucket, address(token)) + fees.buybackBalance(address(token)));
            assertEq(principal + feeBalance + rewardBalance + pendingBalance + paid[i], deposited[i] + externalGross[i], "external/principal conservation");
            assertEq(fees.totalExternalFunded(bucket, address(token)) + pendingBalance, externalGross[i], "pending and funded must remain distinct");
        }
        assertEq(treasury.balance, ids.length * 0.05 ether); assertEq(address(vault).balance, 0);
    }
}

contract ExternalFundingInvariantTest is Test {
    ExternalFundingHandler private handler;
    function setUp() public {
        handler = new ExternalFundingHandler(); bytes4[] memory selectors = new bytes4[](10);
        selectors[0] = handler.mint.selector; selectors[1] = handler.activate.selector;
        selectors[2] = handler.topUp.selector; selectors[3] = handler.fund.selector;
        selectors[4] = handler.sync.selector; selectors[5] = handler.claim.selector;
        selectors[6] = handler.transfer.selector; selectors[7] = handler.paused.selector;
        selectors[8] = handler.compound.selector; selectors[9] = handler.rebalance.selector;
        targetContract(address(handler)); targetSelector(FuzzSelector(address(handler), selectors));
    }
    function invariant_pendingExternalFundsPrincipalAndClaimsAreConserved() public view { handler.assertConservation(); }
    function testPendingFundingActivationTopUpAndPausedClaims() public {
        handler.fund(109, false); handler.fund(217, true); handler.activate(1);
        handler.topUp(0, 40); handler.fund(211, false); handler.sync(); handler.compound();
        handler.fund(307, true); handler.rebalance(); handler.paused(true);
        handler.transfer(0); handler.claim(0, false); handler.claim(1, true); handler.assertConservation();
    }
}

/// @notice External ingress plus real Vault/Fees/Rewards/NFT/Membership accounting.
/// The LP venue, price feeds and optional native wrapper are deliberately local mocks.
contract ExternalRewardsTest is PooledVaultFixture {
    address private constant CREATOR = address(0xC2EA70);

    function _receiver(uint256 id) private returns (address inbox) {
        inbox = fees.createRewardReceiver(vault.nftBucket(id), address(0));
    }

    function _send(MockToken token, address inbox, uint256 amount) private {
        token.mint(CREATOR, amount);
        vm.prank(CREATOR);
        assertTrue(token.transfer(inbox, amount));
    }

    function _pending(address inbox) private view returns (uint256 a0, uint256 a1) {
        return ExternalRewardInbox(inbox).pending();
    }

    function _syncAll() private {
        vm.prank(address(vault)); fees.syncAllExternal();
    }

    function _assertNativeClaimBacking(uint256 id, address token, uint256 gross) private view returns (uint256 amount) {
        uint256 funded = gross / 20 * 18;
        amount = rewards.claimable(id, token);
        // Each separate single-owner index may retain less than one raw unit.
        // The two index floors remain funded liabilities rather than disappearing.
        assertLe(amount, funded); assertGe(amount, funded - 2);
        assertEq(rewards.liabilities(token), funded);
    }

    function _replaceFirstToken(MockToken replacement) private {
        PoolConfig memory c = pools.get(poolId);
        t0 = replacement;
        venue = new VaultLiquidityMock(address(t0), address(t1));
        ac.bind(Ids.LIQUIDITY, address(venue));
        oracle.setFeed(address(t0), address(new MockFeed(8, 1e8)), 3600);
        rewards.addAsset(address(t0));
        c.key.currency0 = address(t0);
        poolId = keccak256(abi.encode(c.key));
        pools.set(poolId, c);
        _fundUser(alice);
        _fundUser(bob);
    }

    function _anotherPool(uint24 fee) private returns (bytes32 id) {
        PoolConfig memory c = pools.get(poolId);
        c.key.fee = fee;
        id = keccak256(abi.encode(c.key));
        pools.set(id, c);
    }

    function _lateVenue() private returns (LateExternalPaymentVenue late) {
        late = new LateExternalPaymentVenue(address(t0), address(t1));
        // The helper field retains its original API; this deliberately adversarial
        // dependency supplies the matching selectors and exact token accounting.
        venue = VaultLiquidityMock(address(late)); ac.bind(Ids.LIQUIDITY, address(late));
    }

    function _activateOther(address owner, uint256 id, bytes32 other) private {
        vm.prank(owner);
        vault.activate(id, other, 1000, 1000, 1, block.timestamp + 100);
    }

    function testRawERC20PaymentIsFundedAndAllocatedExactlyOnce() public {
        uint256 id = activatedPosition();
        uint256 bucket = vault.nftBucket(id);
        address inbox = _receiver(id);
        _send(t0, inbox, 1000);
        (uint256 p0, uint256 p1) = _pending(inbox);
        assertEq(p0, 1000); assertEq(p1, 0);
        assertEq(rewards.claimable(id, address(t0)), 0);
        vm.prank(bob); ExternalRewardInbox(inbox).sync();
        assertEq(rewards.claimable(id, address(t0)), 900);
        assertEq(fees.compoundBalance(bucket, address(t0)), 50);
        assertEq(fees.buybackBalance(address(t0)), 50);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
        assertEq(t0.balanceOf(inbox), 0);
        assertEq(t0.allowance(inbox, address(fees)), 0);
        assertEq(t0.balanceOf(address(rewards)), rewards.liabilities(address(t0)));
        assertEq(t0.balanceOf(address(fees)), fees.accounted(address(t0)));
        ExternalRewardInbox(inbox).sync();
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
        assertEq(rewards.claimable(id, address(t0)), 900);
    }

    function testBothPairTokensUseIndependentFundedAllocations() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = _receiver(id);
        _send(t0, inbox, 1000); _send(t1, inbox, 2170);
        fees.syncExternal(bucket);
        assertEq(rewards.claimable(id, address(t0)), 900);
        assertEq(rewards.claimable(id, address(t1)), 1944);
        assertEq(fees.compoundBalance(bucket, address(t1)), 108);
        assertEq(fees.buybackBalance(address(t1)), 108);
        assertEq(fees.dust(bucket, address(t1)), 10);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
        assertEq(fees.totalExternalFunded(bucket, address(t1)), 2170);
    }

    function testExternalPaymentDoesNotChangePrincipalSharesMembershipOrMintProceeds() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = _receiver(id);
        Position memory p = vault.group(bucket); uint256 shares = vault.sharesOf(id); uint256 count = membership.totalEligible();
        uint256 proceeds = treasury.balance;
        _send(t0, inbox, 1000); _syncAll();
        Position memory next = vault.group(bucket);
        assertEq(next.lpTokenId, p.lpTokenId); assertEq(next.idle0, p.idle0); assertEq(next.idle1, p.idle1);
        assertEq(vault.sharesOf(id), shares); assertEq(vault.bucketTotalShares(bucket), shares);
        assertEq(membership.totalEligible(), count); assertEq(vault.contributionUSD(id), 2000e18);
        assertEq(treasury.balance, proceeds); assertEq(address(vault).balance, 0);
    }

    function testPendingPaymentSettlesBeforeSamePoolActivationAndPricesCompoundNAV() public {
        uint256 first = activatedPosition(); uint256 bucket = vault.nftBucket(first); address inbox = _receiver(first);
        uint256 second = _mint(bob); _send(t0, inbox, 1000);
        _activate(bob, second, 1000, 1000);
        assertEq(rewards.claimable(first, address(t0)), 900);
        assertEq(rewards.claimable(second, address(t0)), 0);
        assertEq(vault.sharesOf(second), uint256(2000e18) * 2000 / 2050);
        assertEq(fees.compoundBalance(bucket, address(t0)), 0);
        Position memory p = vault.group(bucket);
        assertEq(venue.a0(p.lpTokenId) + p.idle0, 2050);
        assertTrue(membership.eligible(first)); assertTrue(membership.eligible(second));
        assertEq(membership.totalEligible(), 2);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
    }

    function testPendingPaymentSettlesBeforeTopUpWithoutRewritingEitherNFTsFees() public {
        uint256 first = activatedPosition(); uint256 second = _mint(bob); _activate(bob, second, 1000, 1000);
        address inbox = _receiver(first);
        uint256 beforeShares = vault.sharesOf(first); _send(t0, inbox, 1000);
        vm.prank(alice); vault.increase(first, 100, 100, 1, block.timestamp + 100);
        assertEq(rewards.claimable(first, address(t0)), 450);
        assertEq(rewards.claimable(second, address(t0)), 450);
        assertEq(vault.sharesOf(first) - beforeShares, uint256(4000e18) * 200 / 4050);
        assertEq(vault.sharesOf(second), 2000e18);
        vm.prank(alice); assertEq(rewards.claim(first, address(t0)), 450);
        vm.prank(bob); assertEq(rewards.claim(second, address(t0)), 450);
    }

    function testFinalIncreaseCallbackCannotGiveNewNFTAnOldOwnerIndexIncrement() public {
        LateExternalPaymentVenue late = _lateVenue(); uint256 first = activatedPosition();
        uint256 bucket = vault.nftBucket(first); address inbox = _receiver(first); uint256 second = _mint(bob);
        late.configurePayment(inbox, 1000, true); _activate(bob, second, 1000, 1000);
        assertEq(rewards.claimable(first, address(t0)), 900);
        assertEq(rewards.claimable(second, address(t0)), 0);
        assertEq(rewards.paidOwnerIndex(second, address(t0)), rewards.ownerIndex(bucket, address(t0)));
        assertEq(rewards.liabilities(address(t0)), 900);
        assertEq(vault.sharesOf(second), uint256(2000e18) * 2000 / 2050);
        assertEq(fees.compoundBalance(bucket, address(t0)), 0);
        Position memory p = vault.group(bucket);
        assertEq(late.a0(p.lpTokenId) + p.idle0, 2050);
        assertEq(late.a1(p.lpTokenId) + p.idle1, 2000);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
        vm.prank(bob); assertEq(rewards.claim(second, address(t0)), 0);
        vm.prank(alice); assertEq(rewards.claim(first, address(t0)), 900);
        assertEq(rewards.liabilities(address(t0)), 0); assertEq(t0.balanceOf(address(rewards)), 0);
    }

    function testUnsyncedPaymentDuringFinalIncreaseSettlesBeforeSharesChange() public {
        LateExternalPaymentVenue late = _lateVenue(); uint256 first = activatedPosition();
        uint256 bucket = vault.nftBucket(first); address inbox = _receiver(first); uint256 second = _mint(bob);
        late.configurePayment(inbox, 1000, false); _activate(bob, second, 1000, 1000);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
        assertEq(rewards.claimable(first, address(t0)), 900); assertEq(rewards.claimable(second, address(t0)), 0);
        assertEq(vault.sharesOf(second), uint256(2000e18) * 2000 / 2050);
        (uint256 p0, uint256 p1) = _pending(inbox); assertEq(p0, 0); assertEq(p1, 0);
    }

    function testFinalIncreaseCallbackCheckpointsTopUpAtItsPreviousShareWeight() public {
        LateExternalPaymentVenue late = _lateVenue(); uint256 first = activatedPosition();
        uint256 second = _mint(bob); _activate(bob, second, 1000, 1000);
        uint256 bucket = vault.nftBucket(first); address inbox = _receiver(first); uint256 oldShares = vault.sharesOf(first);
        late.configurePayment(inbox, 1000, true);
        vm.prank(alice); vault.increase(first, 100, 100, 1, block.timestamp + 100);
        assertEq(rewards.claimable(first, address(t0)), 450); assertEq(rewards.claimable(second, address(t0)), 450);
        assertEq(vault.sharesOf(first) - oldShares, uint256(4000e18) * 200 / 4050);
        assertEq(vault.sharesOf(second), 2000e18); assertEq(rewards.liabilities(address(t0)), 900);
        Position memory p = vault.group(bucket);
        assertEq(late.a0(p.lpTokenId) + late.a1(p.lpTokenId) + p.idle0 + p.idle1, 4250);
        vm.prank(alice); assertEq(rewards.claim(first, address(t0)), 450);
        vm.prank(bob); assertEq(rewards.claim(second, address(t0)), 450);
        assertEq(rewards.liabilities(address(t0)), 0); assertEq(t0.balanceOf(address(rewards)), 0);
    }

    function testLateUndeployedCompoundDoesNotRaiseTheExactly100DeployedActivationMinimum() public {
        LateExternalPaymentVenue late = _lateVenue(); late.setSpendBps(10000);
        uint256 first = activatedPosition(); address inbox = _receiver(first); uint256 second = _mint(bob);
        late.configurePayment(inbox, 1000, true); _activate(bob, second, 50, 50);
        uint256 bucket = vault.nftBucket(first); Position memory p = vault.group(bucket);
        assertEq(late.a0(p.lpTokenId) + late.a1(p.lpTokenId), 2100);
        assertEq(p.idle0 + p.idle1, 50);
        assertEq(vault.sharesOf(second), uint256(2000e18) * 100 / 2050);
        assertEq(vault.contributionUSD(second), 100e18);
        assertEq(rewards.claimable(second, address(t0)), 0); assertEq(rewards.claimable(first, address(t0)), 900);
    }

    function testHugeLateCompoundCannotLeaveEntryAboveTheFivePercentIdleCap() public {
        LateExternalPaymentVenue late = _lateVenue(); uint256 first = activatedPosition();
        uint256 bucket = vault.nftBucket(first); address inbox = _receiver(first); uint256 second = _mint(bob);
        late.configurePayment(inbox, 25000, true);
        uint256 oldVenueBalance = t0.balanceOf(address(late)); Position memory old = vault.group(bucket);
        vm.prank(bob); vm.expectRevert(); vault.activate(second, poolId, 1000, 1000, 1, block.timestamp + 100);
        assertEq(vault.nftBucket(second), 0); assertEq(vault.sharesOf(second), 0);
        assertEq(uint256(vault.nftStatus(second)), uint256(PositionStatus.Dormant));
        assertEq(vault.sharesOf(first), 2000e18); assertEq(vault.bucketTotalShares(bucket), 2000e18);
        assertEq(t0.balanceOf(bob), 100000); assertEq(t0.balanceOf(address(late)), oldVenueBalance);
        assertEq(vault.group(bucket).idle0, old.idle0); assertEq(vault.group(bucket).lpTokenId, old.lpTokenId);
        assertEq(rewards.liabilities(address(t0)), 0); assertEq(fees.totalExternalFunded(bucket, address(t0)), 0);
        assertEq(fees.compoundBalance(bucket, address(t0)), 0); assertEq(t0.balanceOf(inbox), 0);
    }

    function testFinalCompoundDeliveryCannotQueueUnsettledFundsInAnotherInboxBeforeNewMember() public {
        RequeueExternalRewardToken token = new RequeueExternalRewardToken(); _replaceFirstToken(token);
        LateExternalPaymentVenue late = _lateVenue(); uint256 first = activatedPosition();
        uint256 firstBucket = vault.nftBucket(first); address firstInbox = _receiver(first);
        uint256 other = _mint(bob); _activateOther(bob, other, _anotherPool(500)); address otherInbox = _receiver(other);
        uint256 entrant = _mint(bob); token.configureRequeue(address(fees), address(vault), otherInbox, 7);
        late.configurePayment(firstInbox, 1000, true);
        uint256 oldSupply = vault.bucketTotalShares(firstBucket); uint256 oldCount = membership.totalEligible();
        vm.prank(bob); vm.expectRevert(); vault.activate(entrant, poolId, 1000, 1000, 1, block.timestamp + 100);
        assertEq(vault.nftBucket(entrant), 0); assertEq(vault.sharesOf(entrant), 0);
        assertEq(vault.bucketTotalShares(firstBucket), oldSupply); assertEq(membership.totalEligible(), oldCount);
        assertEq(rewards.liabilities(address(token)), 0); assertEq(fees.totalExternalFunded(firstBucket, address(token)), 0);
        assertEq(token.balanceOf(firstInbox), 0); assertEq(token.balanceOf(otherInbox), 0);
        assertEq(token.balanceOf(address(token)), 7);
        assertEq(rewards.claimable(first, address(token)), 0); assertEq(rewards.claimable(other, address(token)), 0);
    }

    function testLateMintCallbackDuringRebalancePreservesFundedOwnerEntitlements() public {
        LateExternalPaymentVenue late = _lateVenue(); uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        uint256 oldLP = vault.group(bucket).lpTokenId; address inbox = _receiver(id);
        late.configurePayment(inbox, 1000, true); vault.rebalance(bucket, 1, block.timestamp + 100);
        assertTrue(vault.group(bucket).lpTokenId != oldLP); assertEq(vault.sharesOf(id), 2000e18);
        assertEq(rewards.claimable(id, address(t0)), 900); assertEq(rewards.liabilities(address(t0)), 900);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
        Position memory p = vault.group(bucket);
        assertEq(late.a0(p.lpTokenId) + late.a1(p.lpTokenId) + p.idle0 + p.idle1
            + fees.accounted(address(t0)) + t0.balanceOf(address(rewards)), 3000);
    }

    function testPendingRewardFromOtherPoolSettlesBeforeNewCollectiveMember() public {
        uint256 first = activatedPosition(); address inbox = _receiver(first); _send(t0, inbox, 1000);
        uint256 second = _mint(bob); _activateOther(bob, second, _anotherPool(500));
        assertTrue(vault.nftBucket(first) != vault.nftBucket(second));
        assertEq(rewards.claimable(first, address(t0)), 900);
        assertEq(rewards.claimable(second, address(t0)), 0);
        assertEq(rewards.ownerIndex(vault.nftBucket(second), address(t0)), 0);
    }

    function testOwnerAllocationStaysInItsBucketAndCollectiveUsesGlobalMembership() public {
        uint256 first = activatedPosition(); uint256 second = _mint(bob); bytes32 other = _anotherPool(500);
        // Unequal LP contributions still receive one collective share each.
        vm.prank(bob); vault.activate(second, other, 2000, 2000, 1, block.timestamp + 100);
        uint256 bucket = vault.nftBucket(first); address inbox = _receiver(first); _send(t0, inbox, 1000);
        _syncAll();
        assertEq(rewards.claimable(first, address(t0)), 850);
        assertEq(rewards.claimable(second, address(t0)), 50);
        assertEq(membership.totalEligible(), 2);
        assertEq(vault.contributionUSD(first), 2000e18); assertEq(vault.contributionUSD(second), 4000e18);
        assertEq(rewards.ownerIndex(vault.nftBucket(second), address(t0)), 0);
        assertEq(fees.compoundBalance(vault.nftBucket(second), address(t0)), 0);
        assertEq(fees.totalExternalFunded(vault.nftBucket(second), address(t0)), 0);
        assertEq(fees.compoundBalance(bucket, address(t0)), 50);
    }

    function testDormantNFTCannotReceiveCurrentOrHistoricalExternalRewards() public {
        uint256 first = activatedPosition(); uint256 dormant = _mint(bob); address inbox = _receiver(first);
        _send(t0, inbox, 1000); _syncAll();
        assertEq(rewards.claimable(dormant, address(t0)), 0);
        vm.prank(bob); assertEq(rewards.claim(dormant, address(t0)), 0);
        _activate(bob, dormant, 1000, 1000);
        assertEq(rewards.claimable(dormant, address(t0)), 0);
        assertEq(rewards.claimable(first, address(t0)), 900);
    }

    function testNFTTransferCarriesExternalEntitlementAndOnlyCurrentOwnerCanClaim() public {
        uint256 id = activatedPosition(); address inbox = _receiver(id); _send(t0, inbox, 1000); _syncAll();
        vm.prank(alice); nft.transferFrom(alice, bob, id);
        vm.prank(alice); vm.expectRevert(); rewards.claim(id, address(t0));
        uint256 old = t0.balanceOf(bob);
        vm.prank(bob); assertEq(rewards.claim(id, address(t0)), 900);
        vm.prank(bob); assertEq(rewards.claim(id, address(t0)), 0);
        assertEq(t0.balanceOf(bob), old + 900);
    }

    function testPausedSystemCanPublishAlreadyFundedExternalRewardsAndClaim() public {
        uint256 id = activatedPosition(); address inbox = _receiver(id); ac.setPaused(true); _send(t0, inbox, 1000);
        ExternalRewardInbox(inbox).sync();
        vm.prank(alice); assertEq(rewards.claim(id, address(t0)), 900);
        assertEq(vault.sharesOf(id), 2000e18);
    }

    function testSubTwentyPendingDustBelongsToIncumbentBeforeActivation() public {
        uint256 first = activatedPosition(); address inbox = _receiver(first); uint256 second = _mint(bob);
        _send(t0, inbox, 19); _activate(bob, second, 1000, 1000);
        assertEq(rewards.claimable(first, address(t0)), 19);
        assertEq(rewards.claimable(second, address(t0)), 0);
        assertEq(fees.dust(vault.nftBucket(first), address(t0)), 0);
    }

    function testPairDonationToOtherCustodyContractsIsNotExternalRevenue() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); _receiver(id);
        _send(t0, address(vault), 1000); _send(t0, address(rewards), 2000); _send(t0, address(fees), 3000);
        _syncAll();
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 0);
        assertEq(rewards.claimable(id, address(t0)), 0);
        assertEq(rewards.liabilities(address(t0)), 0); assertEq(fees.accounted(address(t0)), 0);
    }

    function testUnknownTokenIsNotAllocatedOrRescued() public {
        uint256 id = activatedPosition(); address inbox = _receiver(id); MockToken unrelated = new MockToken(18);
        _send(unrelated, inbox, 1000); ExternalRewardInbox(inbox).sync();
        assertEq(unrelated.balanceOf(inbox), 1000);
        assertEq(rewards.claimable(id, address(unrelated)), 0);
        (bool ok,) = inbox.call(abi.encodeWithSignature("rescueToken(address,address,uint256)", address(unrelated), alice, 1000));
        assertFalse(ok); assertEq(unrelated.balanceOf(inbox), 1000);
    }

    function testConstructionPrefundingIsPermanentlyExcludedFromFutureRewards() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        address predicted = vm.computeCreateAddress(address(fees), vm.getNonce(address(fees)));
        t0.mint(predicted, 111); t1.mint(predicted, 222); vm.deal(predicted, 333);
        address inbox = _receiver(id); assertEq(inbox, predicted);
        assertEq(ExternalRewardInbox(inbox).protected0(), 111);
        assertEq(ExternalRewardInbox(inbox).protected1(), 222);
        assertEq(ExternalRewardInbox(inbox).protectedNative(), 333);
        (uint256 p0, uint256 p1) = _pending(inbox); assertEq(p0, 0); assertEq(p1, 0);
        ExternalRewardInbox(inbox).sync(); assertEq(rewards.claimable(id, address(t0)), 0);
        _send(t0, inbox, 1000); ExternalRewardInbox(inbox).sync();
        assertEq(rewards.claimable(id, address(t0)), 900);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
        assertEq(t0.balanceOf(inbox), 111); assertEq(t1.balanceOf(inbox), 222); assertEq(inbox.balance, 333);
    }

    function testReceiverCreationRequiresSealedCanonicalActiveBucketAndGovernance() public {
        uint256 dormant = _mint(alice); uint256 dormantBucket = vault.nftBucket(dormant);
        vm.expectRevert(); fees.createRewardReceiver(dormantBucket, address(0));
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        vm.prank(bob); vm.expectRevert(); fees.createRewardReceiver(bucket, address(0));
        ac.bind(Ids.VAULT, address(vault)); // The mock allows state fixtures; production bindings are immutable.
        vm.chainId(block.chainid + 1); vm.expectRevert(); fees.createRewardReceiver(bucket, address(0));
    }

    function testUnsealedControllerCannotCreateReceiverEvenForExistingShareLedger() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); MockAccess unsealed = new MockAccess();
        ZZZFeeController candidate = new ZZZFeeController(address(unsealed));
        unsealed.bind(Ids.VAULT, address(vault)); unsealed.bind(Ids.REWARDS, address(rewards));
        vm.expectRevert(); candidate.createRewardReceiver(bucket, address(0));
        assertEq(candidate.rewardReceiverCount(), 0);
    }

    function testFutureReceiverCannotBeTheImmutableMintProceedsRecipient() public {
        // _fixture deploys ten contracts before FeeController. This explicit
        // constructor-configuration scenario exercises an address which can be
        // predicted before the contract has code, rather than a module address.
        address predictedFees = vm.computeCreateAddress(address(this), vm.getNonce(address(this)) + 10);
        address predictedInbox = vm.computeCreateAddress(predictedFees, 1);
        _fixture(payable(predictedInbox)); assertEq(address(fees), predictedFees);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        assertEq(predictedInbox.balance, 0.05 ether);
        vm.expectRevert(); fees.createRewardReceiver(bucket, address(0));
        assertEq(fees.rewardReceiverCount(), 0); assertEq(fees.rewardReceiver(bucket), address(0));
        assertEq(predictedInbox.code.length, 0); assertEq(vm.getNonce(address(fees)), 1);
        assertEq(predictedInbox.balance, 0.05 ether);
    }

    function testOneImmutableReceiverPerBucketAndWrapperMustBePairAsset() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        MockToken unrelated = new MockToken(18);
        vm.expectRevert(); fees.createRewardReceiver(bucket, address(unrelated));
        address inbox = _receiver(id);
        assertEq(fees.rewardReceiver(bucket), inbox); assertEq(fees.rewardReceiverCount(), 1);
        vm.expectRevert(); fees.createRewardReceiver(bucket, address(0));
        assertEq(fees.rewardReceiver(bucket), inbox); assertEq(fees.rewardReceiverCount(), 1);
    }

    function testPairAssetWithWrongDecimalsCannotBeNativeWrapper() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        assertEq(t0.decimals(), 0);
        vm.expectRevert(); fees.createRewardReceiver(bucket, address(t0));
        assertEq(fees.rewardReceiver(bucket), address(0)); assertEq(fees.rewardReceiverCount(), 0);
    }

    function testUnregisteredCallerCannotAllocateExternalFundsOrChooseAnotherBucket() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); _receiver(id);
        t0.mint(address(this), 1000); t0.approve(address(fees), 1000);
        vm.expectRevert(); fees.allocateExternal(bucket, address(t0), 1000);
        vm.expectRevert(); fees.allocateExternal(bucket + 1, address(t0), 1000);
        assertEq(t0.balanceOf(address(this)), 1000); assertEq(fees.totalExternalFunded(bucket, address(t0)), 0);
    }

    function testGlobalMembershipBarrierCannotBeInvokedByOrdinaryCaller() public {
        uint256 id = activatedPosition(); _receiver(id);
        vm.prank(bob); vm.expectRevert(); fees.syncAllExternal();
        vm.expectRevert(); fees.syncAllExternal();
    }

    function testPendingMicroDustFromOtherPoolCannotRewardFutureCollectiveMember() public {
        uint256 first = activatedPosition(); uint256 firstBucket = vault.nftBucket(first); address inbox = _receiver(first);
        _send(t0, inbox, 19);
        uint256 second = _mint(bob); _activateOther(bob, second, _anotherPool(500));
        assertEq(rewards.claimable(first, address(t0)), 19);
        assertEq(rewards.claimable(second, address(t0)), 0);
        assertEq(fees.dust(firstBucket, address(t0)), 0);
        // The next full split may reward current collective participants, but
        // cannot pull old sub-twenty units into their membership index.
        _send(t0, inbox, 20); ExternalRewardInbox(inbox).sync();
        assertEq(rewards.claimable(second, address(t0)), 1);
        assertEq(rewards.claimable(first, address(t0)), 36);
    }

    function testSixteenExternalReceiversFitBucketCapAndSeventeenthActivationFails() public {
        for (uint256 i; i < 16; ++i) {
            _fundUser(alice); uint256 id = _mint(alice); bytes32 other = _anotherPool(uint24(500 + i));
            _activateOther(alice, id, other); address inbox = _receiver(id);
            assertGt(inbox.code.length, 0);
            assertEq(fees.rewardReceiver(vault.nftBucket(id)), inbox);
        }
        assertEq(fees.rewardReceiverCount(), 16); assertEq(vault.bucketCount(), 16);
        _fundUser(alice); uint256 seventeenth = _mint(alice); bytes32 newPool = _anotherPool(516);
        uint256 balance0 = t0.balanceOf(alice); uint256 balance1 = t1.balanceOf(alice);
        // The historical Vault limit now rejects a seventeenth distinct bucket
        // before it could reach the separate receiver factory's capacity guard.
        vm.expectRevert(bytes4(keccak256("InvalidState()")));
        _activateOther(alice, seventeenth, newPool);
        assertEq(vault.bucketCount(), 16); assertEq(vault.nftBucket(seventeenth), 0);
        assertEq(uint256(vault.nftStatus(seventeenth)), uint256(PositionStatus.Dormant));
        assertEq(t0.balanceOf(alice), balance0); assertEq(t1.balanceOf(alice), balance1);
        assertEq(fees.rewardReceiverCount(), 16);
    }

    function testReceiverCannotAcceptNativePaymentWithoutExplicitWrapper() public {
        uint256 id = activatedPosition(); address inbox = _receiver(id); vm.deal(CREATOR, 1 ether);
        vm.prank(CREATOR); (bool ok,) = payable(inbox).call{value: 1 ether}("");
        assertFalse(ok); assertEq(inbox.balance, 0); assertEq(CREATOR.balance, 1 ether);
    }

    function testNativePaymentWrapsOnlyActualNewFundsAndBecomesClaimableWETH() public {
        ExternalRewardWETH wrapper = new ExternalRewardWETH(); _replaceFirstToken(wrapper);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        address inbox = fees.createRewardReceiver(bucket, address(wrapper));
        vm.deal(CREATOR, 1 ether); vm.prank(CREATOR); (bool ok,) = payable(inbox).call{value: 1 ether}(""); assertTrue(ok);
        (uint256 p0, uint256 p1) = _pending(inbox); assertEq(p0, 1 ether); assertEq(p1, 0);
        assertEq(rewards.claimable(id, address(wrapper)), 0);
        ExternalRewardInbox(inbox).sync();
        assertEq(inbox.balance, 0); assertEq(address(wrapper).balance, 1 ether);
        assertEq(fees.totalExternalFunded(bucket, address(wrapper)), 1 ether);
        uint256 claimable = _assertNativeClaimBacking(id, address(wrapper), 1 ether);
        assertEq(fees.compoundBalance(bucket, address(wrapper)), 0.05 ether);
        assertEq(fees.buybackBalance(address(wrapper)), 0.05 ether);
        vm.prank(alice); assertEq(rewards.claim(id, address(wrapper)), claimable);
        assertEq(wrapper.balanceOf(address(rewards)), 0.9 ether - claimable);
        assertEq(rewards.liabilities(address(wrapper)), 0.9 ether - claimable);
    }

    function testNativeLowGasPaymentAlsoSupportsSecondPairAsset() public {
        ExternalRewardWETH wrapper = new ExternalRewardWETH(); PoolConfig memory c = pools.get(poolId);
        t1 = wrapper; venue = new VaultLiquidityMock(address(t0), address(t1)); ac.bind(Ids.LIQUIDITY, address(venue));
        oracle.setFeed(address(t1), address(new MockFeed(8, 1e8)), 3600); rewards.addAsset(address(t1));
        c.key.currency1 = address(t1); poolId = keccak256(abi.encode(c.key)); pools.set(poolId, c);
        _fundUser(alice); _fundUser(bob);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = fees.createRewardReceiver(bucket, address(wrapper));
        new LowGasExternalPayment().pay{value: 1 ether}(payable(inbox));
        (uint256 p0, uint256 p1) = _pending(inbox); assertEq(p0, 0); assertEq(p1, 1 ether);
        ExternalRewardInbox(inbox).sync();
        assertEq(fees.totalExternalFunded(bucket, address(wrapper)), 1 ether);
        _assertNativeClaimBacking(id, address(wrapper), 1 ether);
    }

    function testWrappedAndNativeConstructionPrefundingRemainsQuarantined() public {
        ExternalRewardWETH wrapper = new ExternalRewardWETH(); _replaceFirstToken(wrapper);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id);
        address predicted = vm.computeCreateAddress(address(fees), vm.getNonce(address(fees)));
        wrapper.mint(predicted, 3 ether); vm.deal(predicted, 7 ether);
        address inbox = fees.createRewardReceiver(bucket, address(wrapper)); assertEq(inbox, predicted);
        vm.deal(inbox, 8 ether); ExternalRewardInbox(inbox).sync();
        assertEq(inbox.balance, 7 ether); assertEq(wrapper.balanceOf(inbox), 3 ether);
        assertEq(address(wrapper).balance, 1 ether); assertEq(fees.totalExternalFunded(bucket, address(wrapper)), 1 ether);
        _assertNativeClaimBacking(id, address(wrapper), 1 ether);
    }

    function testNativeAndWrappedPaymentsCannotDoubleCount() public {
        ExternalRewardWETH wrapper = new ExternalRewardWETH(); _replaceFirstToken(wrapper);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = fees.createRewardReceiver(bucket, address(wrapper));
        _send(wrapper, inbox, 1 ether); vm.deal(inbox, 2 ether);
        ExternalRewardInbox(inbox).sync(); ExternalRewardInbox(inbox).sync();
        assertEq(fees.totalExternalFunded(bucket, address(wrapper)), 3 ether);
        _assertNativeClaimBacking(id, address(wrapper), 3 ether);
        assertEq(address(wrapper).balance, 2 ether); assertEq(inbox.balance, 0);
    }

    function testIncorrectWrapperOutputRollsBackAllFundingAndLeavesNativePending() public {
        BrokenExternalRewardWETH wrapper = new BrokenExternalRewardWETH(); _replaceFirstToken(wrapper);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = fees.createRewardReceiver(bucket, address(wrapper));
        vm.deal(inbox, 1 ether); vm.expectRevert(); ExternalRewardInbox(inbox).sync();
        assertEq(inbox.balance, 1 ether); assertEq(address(wrapper).balance, 0);
        assertEq(wrapper.balanceOf(inbox), 0); assertEq(fees.totalExternalFunded(bucket, address(wrapper)), 0);
        assertEq(rewards.claimable(id, address(wrapper)), 0);
    }

    function testWrapperCannotReenterSyncDuringWrapping() public {
        ReentrantExternalRewardWETH wrapper = new ReentrantExternalRewardWETH(); _replaceFirstToken(wrapper);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = fees.createRewardReceiver(bucket, address(wrapper));
        vm.deal(inbox, 1 ether); ExternalRewardInbox(inbox).sync();
        assertTrue(wrapper.attempted()); assertFalse(wrapper.reentrySucceeded());
        assertEq(fees.totalExternalFunded(bucket, address(wrapper)), 1 ether);
        _assertNativeClaimBacking(id, address(wrapper), 1 ether);
    }

    function testTaxedForwardTransferIsRejectedAtomically() public {
        ExternalTaxToken taxed = new ExternalTaxToken(); _replaceFirstToken(taxed);
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = _receiver(id);
        // A raw ERC20 transfer has no receiver callback, so only its actual
        // controlled balance is visible. The exact forwarding transfer still
        // rejects this deliberately malicious change in token behavior.
        taxed.enableTax(); _send(taxed, inbox, 1000);
        assertEq(taxed.balanceOf(inbox), 900);
        vm.expectRevert(); ExternalRewardInbox(inbox).sync();
        assertEq(taxed.balanceOf(inbox), 900);
        assertEq(taxed.balanceOf(address(fees)), 0); assertEq(taxed.allowance(inbox, address(fees)), 0);
        assertEq(fees.totalExternalFunded(bucket, address(taxed)), 0);
        assertEq(rewards.claimable(id, address(taxed)), 0);
    }

    function _outstandingRemote(uint256 bucket) private {
        BridgeMessage memory m; m.version = 3; m.kind = MessageKind.Principal; m.bucketId = bucket;
        m.homeChain = block.chainid; m.homeVault = address(vault); m.canonicalToken0 = address(t0); m.canonicalToken1 = address(t1);
        m.totalShares = vault.bucketTotalShares(bucket); m.allocatedIndividual0 = 80; m.allocatedCollective0 = 10;
        vm.prank(address(0x987)); fees.importAccounting(m);
    }

    function testExternalRewardsCannotMasqueradeAsOldRemoteSettlement() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = _receiver(id);
        _outstandingRemote(bucket); _send(t0, inbox, 1000); ExternalRewardInbox(inbox).sync();
        assertEq(rewards.claimable(id, address(t0)), 900);
        assertEq(fees.receivedIndividual(bucket, address(t0)), 0);
        assertEq(fees.receivedCollective(bucket, address(t0)), 0);
        assertEq(fees.expectedIndividual(bucket, address(t0)), 80);
        assertEq(fees.expectedCollective(bucket, address(t0)), 10);
        assertFalse(fees.remoteSettled(bucket));
        vm.prank(alice); assertEq(rewards.claim(id, address(t0)), 900);
        assertFalse(fees.remoteSettled(bucket));
        vm.prank(alice); vm.expectRevert(); vault.increase(id, 100, 100, 1, block.timestamp + 100);
    }

    function testScheduledMigrationFreezesMembershipButDoesNotPreventFundedClaims() public {
        uint256 id = activatedPosition(); address inbox = _receiver(id); ac.bind(Ids.MIGRATION, address(new ExternalPendingMigration()));
        _send(t0, inbox, 1000); ExternalRewardInbox(inbox).sync();
        vm.prank(alice); vm.expectRevert(); vault.increase(id, 100, 100, 1, block.timestamp + 100);
        vm.prank(alice); assertEq(rewards.claim(id, address(t0)), 900);
    }

    function testCanonicalRewardInboxContinuesAcrossOutboundRemoteAndInboundCustody() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = _receiver(id);
        vault.releaseForMigration(bucket, bytes32(uint256(1)), block.timestamp + 100);
        assertEq(uint256(vault.group(bucket).status), uint256(PositionStatus.Outbound));
        _send(t0, inbox, 1000); ExternalRewardInbox(inbox).sync(); assertEq(rewards.claimable(id, address(t0)), 900);
        vault.confirmMigration(bucket, block.chainid + 1, address(0xF001));
        assertEq(uint256(vault.group(bucket).status), uint256(PositionStatus.Remote));
        _send(t0, inbox, 1000); ExternalRewardInbox(inbox).sync(); assertEq(rewards.claimable(id, address(t0)), 1800);
        Position memory p = vault.group(bucket); address receiver = address(0x987);
        t0.mint(receiver, 1000); t1.mint(receiver, 1000);
        vm.startPrank(receiver); t0.approve(address(vault), 1000); t1.approve(address(vault), 1000);
        vault.importPending(bucket, poolId, p, vault.bucketTotalShares(bucket), vault.homePoolId(bucket), 1000, 1000); vm.stopPrank();
        assertEq(uint256(vault.group(bucket).status), uint256(PositionStatus.Inbound));
        _send(t0, inbox, 1000); ExternalRewardInbox(inbox).sync();
        assertEq(rewards.claimable(id, address(t0)), 2700);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 3000);
        assertEq(fees.receivedIndividual(bucket, address(t0)), 0);
        assertEq(fees.receivedCollective(bucket, address(t0)), 0);
        assertEq(vault.sharesOf(id), 2000e18);
        vm.prank(alice); assertEq(rewards.claim(id, address(t0)), 2700);
    }

    function testCollectingVenueFeesAlsoSynchronizesPendingExternalFunds() public {
        uint256 id = activatedPosition(); uint256 bucket = vault.nftBucket(id); address inbox = _receiver(id);
        _send(t0, inbox, 1000); venue.setFees(100, 0); vault.collectFees(bucket, block.timestamp + 100);
        assertEq(rewards.claimable(id, address(t0)), 990);
        assertEq(fees.compoundBalance(bucket, address(t0)), 55);
        assertEq(fees.buybackBalance(address(t0)), 55);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), 1000);
    }

    function testFuzzExternalFundedClaimsAndAllReservesConserveActualIngress(uint96 x, uint96 y) public {
        uint256 first = activatedPosition(); uint256 second = _mint(bob); _activate(bob, second, 2000, 2000);
        uint256 bucket = vault.nftBucket(first); address inbox = _receiver(first);
        uint256 a = bound(uint256(x), 1, 1e24); uint256 b = bound(uint256(y), 1, 1e24);
        _send(t0, inbox, a); ExternalRewardInbox(inbox).sync();
        vm.prank(alice); uint256 paid0 = rewards.claim(first, address(t0));
        _send(t0, inbox, b); _syncAll();
        vm.prank(alice); paid0 += rewards.claim(first, address(t0));
        vm.prank(bob); uint256 paid1 = rewards.claim(second, address(t0));
        uint256 liability = rewards.liabilities(address(t0)); uint256 orphaned = rewards.orphaned(address(t0));
        uint256 reserve = fees.accounted(address(t0));
        assertEq(paid0 + paid1 + liability + orphaned + reserve, a + b);
        assertEq(t0.balanceOf(address(rewards)), liability + orphaned);
        assertEq(t0.balanceOf(address(fees)), reserve);
        assertEq(reserve, fees.compoundBalance(bucket, address(t0)) + fees.buybackBalance(address(t0)) + fees.dust(bucket, address(t0)));
        assertEq(fees.totalExternalFunded(bucket, address(t0)), a + b);
        assertEq(t0.balanceOf(inbox), 0); assertEq(vault.bucketTotalShares(bucket), 6000e18);
    }
}
