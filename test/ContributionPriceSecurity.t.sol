// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {PooledVaultFixture, VaultPolicyMock} from "./VaultAccounting.t.sol";
import {MockToken, MockFeed} from "./mocks/Mocks.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";
import {Ids, PositionStatus} from "../src/libraries/ZZZTypes.sol";

interface IPriceCallback { function changePrice() external; function changeSpot() external; function arriveHistorical() external; }

/// @dev TEST ONLY hostile runtime substitution, retaining ERC20 storage layout.
/// It models an admitted callback-capable asset, not current public ZZZ code.
contract ContributionCallbackToken is MockToken {
    address private target;
    address private watched;
    uint8 private mode;
    bool private entered;
    constructor() MockToken(0) {}
    function configure(address callback,address account,uint8 behavior) external { target=callback;watched=account;mode=behavior; }
    function _update(address from,address to,uint256 amount) internal override {
        super._update(from,to,amount);
        if (!entered && target!=address(0) && mode==1 && to==watched && amount!=0) {
            entered=true;IPriceCallback(target).changePrice();entered=false;
        }
        if (!entered && target!=address(0) && mode==3 && to==watched && amount!=0) {
            entered=true;IPriceCallback(target).arriveHistorical();entered=false;
        }
    }
    function approve(address spender,uint256 amount) public override returns(bool) {
        bool ok=super.approve(spender,amount);
        if (!entered && target!=address(0) && mode==2 && msg.sender==watched && amount==0) {
            entered=true;IPriceCallback(target).changeSpot();entered=false;
        }
        return ok;
    }
}

/// @notice Real Vault/Oracle/ledgers, explicitly substituted LP venue and feeds.
/// Actual installed v4 position/settlement checks have separate scoped evidence.
contract ContributionPriceSecurityTest is PooledVaultFixture {
    MockFeed private primary;
    MockFeed private secondary;
    uint160 private changedSpot;
    MockToken private historical;
    MockFeed private historicalPrimary;
    bool private breakHistorical;
    function setUp() public override {
        super.setUp();
        primary=new MockFeed(8,1e8);secondary=new MockFeed(8,1e8);
        _policy(0);
    }
    function _policy(uint16 tolerance) private {
        oracle.setDualFeed(address(t0),
            ZZZOracle.SourcePolicy(address(primary),address(primary).codehash,keccak256("provider-one"),3600,8),
            ZZZOracle.SourcePolicy(address(secondary),address(secondary).codehash,keccak256("provider-two"),3600,8),
            tolerance,keccak256("local-independent-control-fixture-not-production"));
    }
    function _callback(uint8 mode) private {
        ContributionCallbackToken implementation=new ContributionCallbackToken();
        vm.etch(address(t0),address(implementation).code);
        ContributionCallbackToken(address(t0)).configure(address(this),address(vault),mode);
    }
    function changePrice() external {
        require(msg.sender==address(t0));
        primary.set(101e6,block.timestamp,block.timestamp);
        secondary.set(101e6,block.timestamp,block.timestamp);
    }
    function changeSpot() external {
        require(msg.sender==address(t0));
        vm.mockCall(address(policy),abi.encodeWithSignature("validatePrice(bytes32)",poolId),abi.encode(changedSpot));
    }
    // TEST ONLY historical-ledger observation seam: other suites exercise
    // actual old inbox receipts. Here physical backing is minted explicitly,
    // while compound classification and prior composition are substituted.
    function _historicalFixture() private {
        historical=new MockToken(0); historicalPrimary=new MockFeed(8,1e8);
        MockFeed second=new MockFeed(8,1e8);
        oracle.setDualFeed(address(historical),
            ZZZOracle.SourcePolicy(address(historicalPrimary),address(historicalPrimary).codehash,keccak256("history-one"),3600,8),
            ZZZOracle.SourcePolicy(address(second),address(second).codehash,keccak256("history-two"),3600,8),
            0,keccak256("history observation substitute, not live qualification"));
        rewards.addAsset(address(historical));
        vm.mockCall(address(vault.migrationBudget()),abi.encodeWithSignature("compositionEpoch(uint256)",_bucket()),abi.encode(uint64(1)));
        vm.mockCall(address(fees),abi.encodeWithSignature("compoundBalance(uint256,address)",_bucket(),address(historical)),abi.encode(uint256(0)));
    }
    function arriveHistorical() external {
        require(msg.sender==address(t0));
        historical.mint(address(fees),100);
        vm.mockCall(address(fees),abi.encodeWithSignature("compoundBalance(uint256,address)",_bucket(),address(historical)),abi.encode(uint256(100)));
        if (breakHistorical) historicalPrimary.set(0,block.timestamp,block.timestamp);
    }
    function testLateHistoricalBackingIsPricedOnlyForIncumbents() public {
        uint256 incumbent=activatedPosition();_historicalFixture();uint256 before=vault.sharesOf(incumbent);
        uint256 entrant=_mint(bob);_callback(3);_activate(bob,entrant,100,0);
        assertEq(vault.sharesOf(incumbent),before);
        assertEq(vault.sharesOf(entrant),before*100e18/2100e18);
        assertEq(historical.balanceOf(address(fees)),100);
        assertEq(rewards.claimable(entrant,address(historical)),0);
        assertFalse(oracle.contributionPricing().active());
    }
    function testHistoricalBackingCannotSubsidizeInsufficientMarginalLP() public {
        uint256 incumbent=activatedPosition();_historicalFixture();uint256 before=vault.sharesOf(incumbent);
        uint256 entrant=_mint(bob);_callback(3);venue.setSpendBps(9800);
        vm.prank(bob);vm.expectRevert();vault.activate(entrant,poolId,100,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(incumbent),before);assertEq(vault.sharesOf(entrant),0);
        assertEq(t0.balanceOf(bob),100000);assertEq(historical.balanceOf(address(fees)),0);
        assertFalse(oracle.contributionPricing().active());
    }
    function testUnreadableNewHistoricalBackingRevertsWithoutLosingContribution() public {
        activatedPosition();_historicalFixture();uint256 entrant=_mint(bob);_callback(3);breakHistorical=true;
        vm.prank(bob);vm.expectRevert();vault.activate(entrant,poolId,100,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(entrant),0);assertEq(t0.balanceOf(bob),100000);
        assertEq(historical.balanceOf(address(fees)),0);assertFalse(oracle.contributionPricing().active());
    }
    function testDirectActivationAndGrowthClearFrozenBasisAndKeepRights() public {
        uint256 id=activatedPosition();uint256 before=vault.sharesOf(id);
        assertFalse(oracle.contributionPricing().active());
        vm.prank(alice);vault.increase(id,5,0,1,block.timestamp+100);
        assertGt(vault.sharesOf(id),before);assertFalse(oracle.contributionPricing().active());
        assertTrue(membership.eligible(id));
    }
    function testPriceRoundChangeDuringPullRevertsAllAssetsAndMembership() public {
        uint256 id=_mint(alice);_callback(1);
        uint256 before=t0.balanceOf(alice);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,100,0,1,block.timestamp+100);
        assertEq(t0.balanceOf(alice),before);assertEq(vault.sharesOf(id),0);
        assertEq(uint256(vault.nftStatus(id)),uint256(PositionStatus.Dormant));
        assertFalse(membership.eligible(id));assertFalse(oracle.contributionPricing().active());
        assertEq(primary.answer(),1e8);assertEq(secondary.answer(),1e8);
    }
    function testGrowingExistingLPRejectsChangedRoundWithoutDilutingIncumbent() public {
        uint256 incumbent=activatedPosition();uint256 original=vault.sharesOf(incumbent);
        uint256 id=_mint(bob);_callback(1);uint256 before=t0.balanceOf(bob);
        vm.prank(bob);vm.expectRevert();vault.activate(id,poolId,100,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(incumbent),original);assertEq(vault.sharesOf(id),0);
        assertEq(t0.balanceOf(bob),before);assertEq(membership.totalEligible(),1);
        assertFalse(oracle.contributionPricing().active());
    }
    function testVaultApprovalResetCannotRepriceLPAfterManagerReturns() public {
        uint256 id=activatedPosition();uint256 before=vault.sharesOf(id);
        _callback(2);changedSpot=uint160((uint256(1)<<96)+1);
        vm.prank(alice);vm.expectRevert();vault.increase(id,5,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(id),before);assertFalse(oracle.contributionPricing().active());
        vm.clearMockedCalls();
    }
    function testUpperInputLowerLPRejectsHiddenPriceUncertaintyAtLossBoundary() public {
        vault.migrationBudget().setLossLimits(100,300);
        secondary.set(100_400_000,block.timestamp,block.timestamp);_policy(50);
        venue.setSpendBps(9900);uint256 id=_mint(alice);
        // $100 lower input/$100.40 upper input requires $99.396 lower LP.
        // Deploying $99 does not prove the agreed 1% all-in bound.
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,100,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(id),0);assertFalse(oracle.contributionPricing().active());
    }
    function testThreePercentAgreementDoesNotOverrideExecutionLossFloor() public {
        vault.migrationBudget().setLossLimits(100,300);
        secondary.set(103_000_000,block.timestamp,block.timestamp);_policy(300);
        (uint256 lower,uint256 upper,)=oracle.priceBounds(address(t0));
        assertEq(lower,1e18);assertEq(upper,103e16);
        uint256 id=_mint(alice);
        // Agreement is allowed, but $100 of lower-bound LP cannot prove the
        // separate 99% floor against $103 of upper-bound source value.
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,100,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(id),0);assertEq(t0.balanceOf(alice),100000);
        secondary.set(103_000_001,block.timestamp,block.timestamp);
        vm.expectRevert();oracle.priceBounds(address(t0));
    }
    function testTightAgreementAllowsHonestFullLPAndConservativeThreshold() public {
        secondary.set(100_400_000,block.timestamp,block.timestamp);_policy(50);
        uint256 id=_mint(alice);_activate(alice,id,100,0);
        assertTrue(membership.eligible(id));assertEq(vault.contributionUSD(id),100e18);
        assertFalse(oracle.contributionPricing().active());
    }
    function testDepegCannotBeAssumedOneDollarForMinimumGrowth() public {
        primary.set(99_000_000,block.timestamp,block.timestamp);
        secondary.set(99_000_000,block.timestamp,block.timestamp);
        uint256 id=_mint(alice);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,100,0,1,block.timestamp+100);
        assertEq(vault.sharesOf(id),0);assertFalse(oracle.contributionPricing().active());
    }
    function testFundedClaimsRemainAvailableWhenPricingFails() public {
        uint256 id=activatedPosition();venue.setFees(100,0);vault.collectFees(vault.nftBucket(id),block.timestamp+100);
        primary.set(0,block.timestamp,block.timestamp);
        vm.expectRevert();oracle.price(address(t0));
        uint256 before=t0.balanceOf(alice);vm.prank(alice);uint256 paid=rewards.claim(id,address(t0));
        assertGt(paid,0);assertEq(t0.balanceOf(alice),before+paid);
    }
    function testUnrelatedCallerCannotOpenOrAdoptPriceSnapshot() public {
        ZZZContributionPricing guard=oracle.contributionPricing();
        (bool legacy,)=address(guard).call(abi.encodeWithSignature("beginEntry(uint256,bytes32,address,uint256)",1,poolId,address(t0),100));
        assertFalse(legacy);
        vm.expectRevert();guard.beginEntryReviewed(1,poolId,address(t0),100,200);
        vm.expectRevert();guard.begin(1,1,100,100e18,0);
        vm.expectRevert();guard.contributionNav(1);
        vm.expectRevert();guard.endEntry();assertFalse(guard.active());
    }
}
