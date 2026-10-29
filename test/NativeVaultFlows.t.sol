// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {Test} from "forge-std/Test.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {EmergencyRebalance} from "../src/interfaces/IZZZEmergency.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {BoundaryUnavailableOracle} from "./NativeLiquidity.t.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationAssetsFactory} from "../src/ZZZActivationAssetsFactory.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {FakePermit2, FakeState} from "./LiquidityEncoding.t.sol";
import {BoundaryWETH, BoundaryCore, BoundaryPositions, BoundaryForce} from "./NativeLiquidity.t.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

contract NativeFlowToken is MockToken {
    address public forceFrom;
    address payable public forceTarget;
    address public callbackFrom;
    address public callbackTo;
    address public callbackTarget;
    bytes private callbackData;
    constructor() MockToken(18) {}
    function forceOnTransfer(address from,address payable target) external { forceFrom=from; forceTarget=target; }
    function callbackOnTransfer(address from,address to,address target,bytes calldata data) external {
        callbackFrom=from; callbackTo=to; callbackTarget=target; callbackData=data;
    }
    function _update(address from,address to,uint256 amount) internal override {
        super._update(from,to,amount);
        if (from==forceFrom && amount!=0 && forceTarget!=address(0)) {
            new BoundaryForce{value:1}(forceTarget);
        }
        if (amount!=0 && from==callbackFrom && to==callbackTo && callbackTarget!=address(0)) {
            address target=callbackTarget; callbackTarget=address(0);
            (bool ok,)=target.call(callbackData); require(ok,"test-only policy callback failed");
        }
    }
}
/// Test-only stable manifest isolates Budget's retained-sample fingerprint.
/// A real Migration stores/clears its full request around the atomic Vault call.
contract EmergencyFingerprintManifest {
    function emergencyFingerprint() external pure returns(bytes32) { return keccak256("fixture manifest"); }
}

/// @dev Explicit fake admission. Real Vault, Entry, Strategy, manager and funded
/// ledgers execute below; this does not qualify Robinhood runtime pins/markets.
contract NativeFlowRegistry {
    uint64 public configurationRevision = 1;
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    ZZZOracle public immutable oracle;
    PoolConfig private config;
    constructor(address controller, ZZZOracle prices, address token) {
        oracle = prices;
        activationAssets = ZZZActivationAssets(ZZZActivationAssetsFactory(IZZZAccess(controller).activationAssetsFactory()).create());
        activationEntry = new ZZZActivationEntry(controller,address(this),address(activationAssets));
        config = PoolConfig(PoolKey(address(0),token,10020,60,address(0)),true,true,1000,100,100,200,600,1e18,1e30);
        activationAssets.admitPoolAsset(address(0)); activationAssets.admitPoolAsset(token);
    }
    function get(bytes32) external view returns (PoolConfig memory) { return config; }
    function accounting(bytes32) external view returns (PoolConfig memory) { return config; }
    function isNativePool(bytes32) external pure returns (bool) { return true; }
    function setRange(uint16 range) external { config.rangeBps = range; ++configurationRevision; }
    function setOperations(bool enabled) external { config.operationsEnabled=enabled; ++configurationRevision; }
    function contributionValue(bytes32 pool,uint256 a0,uint256 a1) external view returns (uint256) {
        uint256 original = activationEntry.sourceValue(pool,a0,a1);
        return original != 0 ? original : activationAssets.value(address(0),a0)+activationAssets.value(config.key.currency1,a1);
    }
}

contract NativeVaultFlowsTest is Test {
    MockAccess private access;
    NativeFlowToken private token;
    BoundaryWETH private wrapper;
    BoundaryCore private core;
    BoundaryPositions private positions;
    NativeFlowRegistry private pools;
    ZZZActivationEntry private entry;
    ZZZVault private vault;
    ZZZNFT private nft;
    ZZZMembership private membership;
    ZZZRewards private rewards;
    ZZZFeeController private fees;
    ZZZBuyback private buyback;
    MockVRF private vrf;
    bytes32 private poolId;
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address payable private constant TREASURY = payable(address(0x7EA5));
    receive() external payable {}
    function activePlan(uint256) external pure returns (bytes32) { return bytes32(0); }
    function currentZZZ() external view returns(address) { return address(token); }
    function setUp() public {
        vm.warp(1_000_000); access = new MockAccess(); token = new NativeFlowToken(); wrapper = new BoundaryWETH();
        wrapper.failures(true,true);
        ZZZOracle oracle = new ZZZOracle(address(access),address(0));
        MockFeed price = new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(price),1 hours); oracle.setTestFeed(address(token),address(price),1 hours);
        access.bind(Ids.ORACLE,address(oracle));
        pools = new NativeFlowRegistry(address(access),oracle,address(token));
        pools.activationAssets().configureZZZ(address(token),address(token).codehash,keccak256("reviewed native fixture ZZZ identity"));
        entry = pools.activationEntry();
        core = new BoundaryCore(); FakePermit2 permit = new FakePermit2();
        positions = new BoundaryPositions(address(core),address(permit),address(wrapper)); core.setPositions(address(positions));
        FakeState state = new FakeState(address(core));
        ZZZLiquidityManager manager = new ZZZLiquidityManager(address(access),address(positions),address(state),address(core),address(permit));
        vault = new ZZZVault(address(access),block.chainid,TREASURY); nft = new ZZZNFT(address(access),"ipfs://native/");
        membership = new ZZZMembership(address(access)); rewards = new ZZZRewards(address(access)); fees = new ZZZFeeController(address(access));
        buyback = new ZZZBuyback(address(access),address(token),1000e18);
        access.bind(Ids.VAULT,address(vault)); access.bind(Ids.NFT,address(nft)); access.bind(Ids.MEMBERSHIP,address(membership));
        access.bind(Ids.REWARDS,address(rewards)); access.bind(Ids.FEES,address(fees)); access.bind(Ids.POOLS,address(pools));
        access.bind(Ids.LIQUIDITY,address(manager)); access.bind(Ids.STRATEGY,address(new ZZZStrategy(address(access))));
        access.bind(Ids.MIGRATION,address(this)); access.bind(Ids.BUYBACK,address(buyback)); access.setKeeper(address(this),true);
        rewards.addAsset(address(token));
        vrf = new MockVRF(); nft.configureRandomness(address(vrf),bytes32(uint256(1)),1,3,500000,false);
        CanonicalFixture.bind(address(access)); access.seal();
        PoolConfig memory config = pools.get(bytes32(0)); poolId = keccak256(abi.encode(config.key));
        vm.mockCall(address(state),abi.encodeWithSignature("getSlot0(bytes32)",poolId),
            abi.encode(uint160(1 << 96),int24(0),uint24(0),uint24(10020)));
        bytes32[] memory catalog=new bytes32[](1);catalog[0]=poolId;
        manager.balancingRouter().configureExecutionPools(catalog,keccak256("TEST_ONLY_NATIVE_FLOW_CATALOG"));
        vm.deal(ALICE,1000 ether); vm.deal(BOB,1000 ether); vm.deal(address(this),1000 ether); vm.deal(address(core),10000 ether);
        token.mint(address(core),10000 ether); token.mint(ALICE,1000 ether); token.mint(BOB,1000 ether);
    }
    function _mint(address owner) private returns (uint256 id) {
        vm.prank(owner); id = vault.mintDormant{value:0.05 ether}();
        vrf.fulfill(nft.requestOf(id),0,0); nft.finalizeTraits(id);
    }
    function _entry(address owner,uint256 id,uint256 amount,bool grow) private {
        ZZZActivationEntry.Request memory r = ZZZActivationEntry.Request(id,poolId,address(0),amount,bytes32(0),0,1,block.timestamp+100,grow);
        vm.prank(owner); entry.executeReviewed{value:amount}(r,200);
    }
    function _emergency(uint256 bucket) private view returns(EmergencyRebalance memory r) {
        (r.lower,r.upper) = ZZZLiquidityManager(payable(access.module(Ids.LIQUIDITY))).ticks(vault.group(bucket).lpTokenId);
        r.bucket=bucket; r.minimumLiquidity=1; r.deadline=block.timestamp+100;
        r.custodyHash=keccak256(abi.encode(block.chainid,address(vault),bucket,vault.group(bucket),vault.bucketTotalShares(bucket)));
        r.reviewHash=keccak256("TEST ONLY explicit manual emergency risk review");
    }
    function _manualMigration() private returns(ZZZMigration migration) {
        migration=new ZZZMigration(address(access));
        // MockAccess permits this TEST ONLY dependency replacement. Real sealed
        // AccessController has no replacement or arbitrary module-write function.
        access.bind(Ids.MIGRATION,address(migration));
    }
    function testManualEmergencyReentersWithoutPricesPreservingSharesAndFundedRewards() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false);
        uint256 bucket=vault.nftBucket(id); uint256 shares=vault.sharesOf(id); uint256 oldLP=vault.group(bucket).lpTokenId;
        positions.fees(oldLP,1 ether,1 ether); vault.collectFees(bucket,block.timestamp+100);
        uint256 beforeClaim=rewards.claimable(id,address(0));
        uint256 beforeBuyback=fees.buybackBalance(address(0));
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        access.setPaused(true); access.bind(Ids.ORACLE,address(new BoundaryUnavailableOracle()));
        migration.emergencyRebalance(r);
        assertFalse(vault.migrationBudget().emergencyActive());
        assertEq(vault.sharesOf(id),shares); assertEq(vault.bucketTotalShares(bucket),shares);
        assertGt(vault.group(bucket).lpTokenId,oldLP); assertEq(vault.group(bucket).lastRebalance,block.timestamp);
        assertEq(rewards.claimable(id,address(0)),beforeClaim); assertEq(fees.buybackBalance(address(0)),beforeBuyback);
        assertTrue(access.paused()); assertEq(wrapper.totalSupply(),0);
        vm.prank(ALICE); rewards.claim(id,address(0));
    }
    function testManualEmergencyRequiresPausedGovernanceNotKeeperOrHolder() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false);
        EmergencyRebalance memory r=_emergency(vault.nftBucket(id)); ZZZMigration migration=_manualMigration();
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); migration.emergencyRebalance(r);
        access.setPaused(true); access.setKeeper(BOB,true);
        vm.prank(BOB); vm.expectRevert(ZZZModule.Unauthorized.selector); migration.emergencyRebalance(r);
        vm.prank(ALICE); vm.expectRevert(ZZZModule.Unauthorized.selector); migration.emergencyRebalance(r);
    }
    function testManualEmergencyRetainedPriceOrValueChecksFailAtomicallyWithoutPrices() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        uint256 lp=vault.group(bucket).lpTokenId; uint256 principal=positions.getPositionLiquidity(lp);
        access.setPaused(true); access.bind(Ids.ORACLE,address(new BoundaryUnavailableOracle()));
        r.checks=2; vm.expectRevert(); migration.emergencyRebalance(r);
        r.checks=4; vm.expectRevert(); migration.emergencyRebalance(r);
        assertFalse(vault.migrationBudget().emergencyActive());
        assertEq(vault.group(bucket).lpTokenId,lp); assertEq(positions.getPositionLiquidity(lp),principal);
    }
    function testManualEmergencyCanExplicitlyOverrideDisabledOperations() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        access.setPaused(true); pools.setOperations(false);
        r.checks=8; vm.expectRevert(); migration.emergencyRebalance(r);
        r.checks=0; migration.emergencyRebalance(r);
        assertFalse(pools.get(poolId).operationsEnabled); assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Active));
    }
    function testManualEmergencyRawSwapFloorFailureRestoresOriginalLPAndContext() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        uint256 lp=vault.group(bucket).lpTokenId; uint256 shares=vault.sharesOf(id);
        access.setPaused(true); r.swapPool=poolId; r.zeroForOne=true; r.amountIn=1 ether; r.minimumOut=2 ether;
        vm.expectCall(address(core),abi.encodeWithSelector(BoundaryCore.swap.selector));
        vm.expectRevert(); migration.emergencyRebalance(r);
        assertFalse(vault.migrationBudget().emergencyActive());
        assertEq(vault.group(bucket).lpTokenId,lp); assertEq(vault.sharesOf(id),shares);
    }
    function testManualEmergencyRejectsStaleCustodyAfterGrowthAndMalformedMasks() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); _entry(ALICE,id,5 ether,true);
        ZZZMigration migration=_manualMigration(); access.setPaused(true);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); migration.emergencyRebalance(r);
        r.custodyHash=migration.emergencyCustodyHash(bucket); r.checks=32;
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector); migration.emergencyRebalance(r);
        assertFalse(vault.migrationBudget().emergencyActive());
    }
    function testManualEmergencyActuallySwapsAndDeploysWithoutOracleWhenExplicitlyBypassed() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        uint256 oldLP=vault.group(bucket).lpTokenId; uint256 shares=vault.sharesOf(id);
        r.swapPool=poolId; r.zeroForOne=true; r.amountIn=1 ether; r.minimumOut=0.98 ether;
        access.setPaused(true); access.bind(Ids.ORACLE,address(new BoundaryUnavailableOracle()));
        vm.expectCall(address(core),abi.encodeWithSelector(BoundaryCore.swap.selector));
        migration.emergencyRebalance(r);
        assertEq(vault.sharesOf(id),shares); assertGt(vault.group(bucket).lpTokenId,oldLP);
        assertFalse(vault.migrationBudget().emergencyActive());
        assertEq(token.allowance(address(vault),access.module(Ids.LIQUIDITY)),0);
        assertEq(token.allowance(access.module(Ids.LIQUIDITY),address(core)),0);
    }
    function testManualEmergencyMayRetainCooldownOrFreshSampleRequirement() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        uint256 lp=vault.group(bucket).lpTokenId;access.setPaused(true);
        r.checks=1; vm.expectRevert(); migration.emergencyRebalance(r); // No elapsed hard cooldown.
        r.checks=16; vm.expectRevert(); migration.emergencyRebalance(r); // No sampled confirmation.
        assertEq(vault.group(bucket).lpTokenId,lp);assertFalse(vault.migrationBudget().emergencyActive());
    }
    function testManualEmergencyCannotReopenTerminalExitOrCanonicalPreparation() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        access.setPaused(true); access.setPreparation(true);
        vm.expectRevert(); migration.emergencyRebalance(r);
        access.setPreparation(false); access.setCanonicalState(2);
        vm.expectRevert(); migration.emergencyRebalance(r);
        access.setCanonicalState(0); vm.prank(address(migration)); vault.beginLPExit();
        vm.expectRevert(); migration.emergencyRebalance(r);
        assertFalse(vault.migrationBudget().emergencyActive());
    }
    function testManualEmergencyRejectsDirectForwardersExpiredReviewAndWrongTickSpacing() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        access.setPaused(true);
        ZZZMigrationBudget budget=vault.migrationBudget();
        vm.prank(ALICE); vm.expectRevert(); vault.emergencyRebalance(bucket,1,block.timestamp+100);
        vm.prank(ALICE); vm.expectRevert(); budget.beginEmergency(bucket,0);
        r.deadline=block.timestamp-1; vm.expectRevert(); migration.emergencyRebalance(r);
        r.deadline=block.timestamp+100; r.lower+=1;
        uint256 lp=vault.group(bucket).lpTokenId;
        vm.expectRevert(); migration.emergencyRebalance(r);
        assertEq(vault.group(bucket).lpTokenId,lp); assertFalse(vault.migrationBudget().emergencyActive());
    }
    function testManualEmergencyRecoversParkedCustodyWithFinancialChecksRetained() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        access.setPaused(true); vm.prank(address(migration)); vault.park(bucket,block.timestamp+100);
        assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Parked));
        r.custodyHash=migration.emergencyCustodyHash(bucket); r.checks=2+4+8;
        migration.emergencyRebalance(r);
        assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Active));
        assertGt(vault.group(bucket).lpTokenId,0); assertFalse(vault.migrationBudget().emergencyActive());
    }
    function testManualEmergencyRetainedSampleFingerprintIncludesPolicyWhenValueGuardIsOff() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        EmergencyFingerprintManifest manifest=new EmergencyFingerprintManifest();
        access.bind(Ids.MIGRATION,address(manifest)); access.setPaused(true);
        ZZZMigrationBudget budget=vault.migrationBudget();
        vm.prank(address(manifest)); budget.beginEmergency(bucket,16);
        bytes32 before=budget.emergencyFingerprint();
        ZZZStrategy(access.module(Ids.STRATEGY)).rebalanceConfirmation().configure(900,300,keccak256("changed reviewed policy"));
        assertNotEq(before,budget.emergencyFingerprint());
        vm.prank(address(manifest)); budget.endEmergency();
    }
    /// @dev One method covers 32 masks, not 32 independent test methods. Raw
    /// timing and retained samples still depend on healthy prices even when bit2
    /// is off; only explicit masks0/8 can execute without those dependencies.
    function testManualEmergencyMaskCompositionWithoutPricesHasExplicitPositiveControls() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        vm.warp(block.timestamp+601); pools.setRange(1100);
        EmergencyRebalance memory r=_emergency(bucket); ZZZMigration migration=_manualMigration();
        r.swapPool=poolId; r.zeroForOne=true; r.amountIn=1 ether; r.minimumOut=0.98 ether;
        uint256 oldLP=vault.group(bucket).lpTokenId; uint256 shares=vault.sharesOf(id);
        access.setPaused(true); access.bind(Ids.ORACLE,address(new BoundaryUnavailableOracle()));
        uint256 checkpoint=vm.snapshotState();
        for(uint8 mask;mask<32;++mask) {
            r.checks=mask;
            if((mask & 23)!=0) {
                vm.expectRevert(abi.encodeWithSignature("Error(string)","oracle unavailable"));
                migration.emergencyRebalance(r);
                assertEq(vault.group(bucket).lpTokenId,oldLP);
            } else {
                vm.expectCall(address(core),abi.encodeWithSelector(BoundaryCore.swap.selector));
                migration.emergencyRebalance(r);
                assertGt(vault.group(bucket).lpTokenId,oldLP);
                assertEq(vault.sharesOf(id),shares); assertEq(vault.bucketTotalShares(bucket),shares);
                EmergencyRebalance memory cleared=migration.emergencyRequest();
                assertEq(cleared.bucket,0); assertEq(cleared.reviewHash,bytes32(0));
            }
            assertFalse(vault.migrationBudget().emergencyActive());
            assertTrue(vm.revertToState(checkpoint));
        }
    }
    /// @dev Explicit governance callback fixture: a real controller would not
    /// let the token configure policy directly. A governed wallet can itself be
    /// called from a dependency callback, so pin the retained policy end-to-end.
    function changeEmergencyConfirmationPolicy() external {
        require(msg.sender==address(token),"test-only token callback");
        ZZZStrategy(access.module(Ids.STRATEGY)).rebalanceConfirmation().configure(
            900,300,keccak256("TEST ONLY governed callback changes retained policy"));
    }
    function testManualEmergencySamplePolicyCallbackRollsBackWhenValueGuardIsOff() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        uint256 oldLP=vault.group(bucket).lpTokenId; uint256 shares=vault.sharesOf(id);
        positions.fees(oldLP,1 ether,1 ether);
        vm.warp(block.timestamp+601); pools.setRange(1100); // Deliberate width exception after cooldown.
        EmergencyRebalance memory r=_emergency(bucket); r.checks=16;
        ZZZMigration migration=_manualMigration(); access.setPaused(true);
        ZZZStrategy policy=ZZZStrategy(access.module(Ids.STRATEGY));
        uint64 revision=policy.rebalanceConfirmation().policyRevision();
        uint256 claimable=rewards.claimable(id,address(0)); uint256 buybackReserve=fees.buybackBalance(address(0));
        bytes memory callback=abi.encodeCall(this.changeEmergencyConfirmationPolicy,());
        token.callbackOnTransfer(address(core),access.module(Ids.LIQUIDITY),address(this),callback);
        vm.expectCall(address(this),callback);
        vm.expectRevert(ZZZModule.InvalidState.selector); migration.emergencyRebalance(r);
        assertEq(policy.rebalanceConfirmation().policyRevision(),revision);
        assertEq(vault.group(bucket).lpTokenId,oldLP); assertEq(vault.sharesOf(id),shares);
        assertEq(vault.bucketTotalShares(bucket),shares); assertEq(positions.nativeFees(oldLP),1 ether);
        assertEq(positions.tokenFees(oldLP),1 ether); assertEq(rewards.claimable(id,address(0)),claimable);
        assertEq(fees.buybackBalance(address(0)),buybackReserve); assertFalse(vault.migrationBudget().emergencyActive());
        EmergencyRebalance memory cleared=migration.emergencyRequest(); assertEq(cleared.bucket,0);
        // The identical manifest succeeds when the callback is absent, proving
        // the negative path was the retained-policy mutation, not bad minima.
        token.callbackOnTransfer(address(0),address(0),address(0),bytes(""));
        migration.emergencyRebalance(r);
        assertGt(vault.group(bucket).lpTokenId,oldLP); assertEq(vault.sharesOf(id),shares);
        assertGt(rewards.claimable(id,address(0)),claimable); assertFalse(vault.migrationBudget().emergencyActive());
        assertEq(token.allowance(address(vault),access.module(Ids.LIQUIDITY)),0);
    }
    function testNativeActivationGrowthAndCurrentValueAreBackedWithoutWrapper() public {
        uint256 id = _mint(ALICE); _entry(ALICE,id,100 ether,false);
        uint256 shares = vault.sharesOf(id); uint256 bucket = vault.nftBucket(id);
        assertGt(shares,0); assertTrue(membership.eligible(id)); assertEq(vault.ACCOUNTING_VERSION(),4);
        assertEq(vault.contributionUSD(id),100 ether); assertEq(wrapper.totalSupply(),0);
        (bool available,uint256 beforeValue) = nft.currentLPValue(id); assertTrue(available); assertGe(beforeValue,99 ether);
        _entry(ALICE,id,5 ether,true);
        (available,beforeValue) = nft.currentLPValue(id); assertTrue(available); assertGe(beforeValue,103.95 ether);
        assertGt(vault.sharesOf(id),shares); assertEq(vault.bucketCount(),1); assertEq(vault.nftBucket(id),bucket);
        assertEq(vault.contributionUSD(id),105 ether); assertEq(wrapper.balanceOf(address(vault)),0);
        assertEq(address(pools.activationEntry()).balance,0);
    }
    function testNativeFeesFollowOwnerThroughGrowthAndRepeatedRebalances() public {
        uint256 id = _mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket = vault.nftBucket(id);
        positions.fees(vault.group(bucket).lpTokenId,1 ether,0); vault.collectFees(bucket,block.timestamp+100);
        assertApproxEqAbs(rewards.claimable(id,address(0)),0.9 ether,1);
        assertEq(fees.compoundBalance(bucket,address(0)),0.05 ether); assertEq(fees.buybackBalance(address(0)),0.05 ether);
        _entry(ALICE,id,5 ether,true); uint256 accrued = rewards.claimable(id,address(0));
        vm.warp(block.timestamp+601); pools.setRange(1100); vault.rebalance(bucket,1,block.timestamp+100);
        vm.warp(block.timestamp+601); pools.setRange(1200); vault.rebalance(bucket,1,block.timestamp+100);
        assertGe(rewards.claimable(id,address(0)),accrued);
        vm.prank(ALICE); nft.transferFrom(ALICE,BOB,id);
        vm.prank(ALICE); vm.expectRevert(); rewards.claim(id,address(0));
        uint256 beforeETH = BOB.balance; vm.prank(BOB); uint256 paid = rewards.claim(id,address(0));
        assertGe(paid,accrued); assertEq(BOB.balance,beforeETH+paid); assertEq(rewards.claimable(id,address(0)),0);
        assertGe(address(rewards).balance,rewards.liabilities(address(0)));
    }
    function testNativeFailedActivationAndIncreaseKeepFundsAndTraits() public {
        uint256 id = _mint(ALICE); uint256 beforeETH = ALICE.balance;
        positions.retain(true); vm.expectRevert(); _entry(ALICE,id,100 ether,false);
        assertEq(ALICE.balance,beforeETH); assertEq(vault.sharesOf(id),0); assertFalse(membership.eligible(id));
        assertEq(nft.ownerOf(id),ALICE); assertTrue(nft.traitsReady(id));
        positions.retain(false); _entry(ALICE,id,100 ether,false);
        uint256 shares = vault.sharesOf(id); beforeETH = ALICE.balance;
        positions.retain(true); vm.expectRevert(); _entry(ALICE,id,5 ether,true);
        assertEq(ALICE.balance,beforeETH); assertEq(vault.sharesOf(id),shares);
    }
    function testNativePrefundsCannotSatisfyMissingValueOrBecomeNFTPrincipal() public {
        uint256 id = _mint(ALICE); new BoundaryForce{value:7 ether}(payable(address(vault)));
        vm.prank(ALICE); vm.expectRevert(); vault.activate(id,poolId,100 ether,0,1,block.timestamp+100);
        assertEq(address(vault).balance,7 ether); assertEq(vault.nftBucket(id),0);
        _entry(ALICE,id,100 ether,false); uint256 bucket = vault.nftBucket(id);
        assertEq(address(vault).balance,7 ether+vault.totalIdle(address(0)));
        assertLt(vault.sharesOf(id),101 ether); assertEq(wrapper.totalSupply(),0);
        vm.prank(ALICE); vm.expectRevert(); vault.increase{value:5 ether+1}(id,5 ether,0,1,block.timestamp+100);
        assertEq(address(vault).balance,7 ether+vault.group(bucket).idle0);
    }
    function testNativeBuybackSpendsOnlyItsClassifiedReserve() public {
        uint256 id = _mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket = vault.nftBucket(id);
        positions.fees(vault.group(bucket).lpTokenId,1 ether,0); vault.collectFees(bucket,block.timestamp+100);
        uint256 claimable = rewards.claimable(id,address(0)); uint256 compound = fees.compoundBalance(bucket,address(0));
        uint256 supply = token.totalSupply(); buyback.execute(address(0),0.05 ether,poolId,block.timestamp+100);
        assertLt(token.totalSupply(),supply); assertEq(fees.buybackBalance(address(0)),0);
        assertEq(rewards.claimable(id,address(0)),claimable); assertEq(fees.compoundBalance(bucket,address(0)),compound);
        assertEq(address(buyback).balance,0); assertEq(wrapper.totalSupply(),0);
    }
    function testNativeForcedETHDuringHarvestCannotBecomeFeeIncome() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        uint256 lp=vault.group(bucket).lpTokenId;
        positions.fees(lp,1 ether,20); vm.deal(address(token),1 ether);
        token.forceOnTransfer(address(core),payable(address(vault)));
        uint256 beforeETH=address(vault).balance;
        vm.expectRevert(); vault.collectFees(bucket,block.timestamp+100);
        assertEq(address(vault).balance,beforeETH); assertEq(rewards.claimable(id,address(0)),0);
        assertEq(positions.nativeFees(lp),1 ether); assertEq(positions.tokenFees(lp),20);
    }
    function testNativeForcedETHDuringCloseCannotSubsidizePrincipal() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        uint256 lp=vault.group(bucket).lpTokenId; uint256 shares=vault.sharesOf(id);
        vm.deal(address(token),1 ether); token.forceOnTransfer(address(core),payable(address(vault)));
        access.setPaused(true); uint256 beforeETH=address(vault).balance;
        vm.expectRevert(); vault.park(bucket,block.timestamp+100);
        assertEq(address(vault).balance,beforeETH); assertEq(vault.sharesOf(id),shares);
        assertEq(vault.group(bucket).lpTokenId,lp); assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Active));
    }
    function testNativeHolderExitUsesActualManagerAndPreservesRewardsWithoutPrices() public {
        uint256 id = _mint(ALICE); _entry(ALICE,id,100 ether,false);
        uint256 bucket = vault.nftBucket(id); uint256 shares = vault.sharesOf(id);
        positions.fees(vault.group(bucket).lpTokenId,1 ether,0);
        access.setPaused(true); vault.beginLPExit();
        vm.warp(block.timestamp + 4000); // USD sources are now stale; raw close must still work.
        uint256 beforeETH = address(this).balance; uint256 beforeZZZ = token.balanceOf(address(this));
        (uint256 returnedETH,uint256 returnedZZZ) = vault.exitBucketToHolders(bucket,0,0,block.timestamp+100);
        assertGt(returnedETH,0); assertGt(returnedZZZ,0);
        assertEq(address(this).balance,beforeETH+returnedETH); assertEq(token.balanceOf(address(this)),beforeZZZ+returnedZZZ);
        assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Exited));
        assertEq(vault.sharesOf(id),shares); assertEq(vault.totalIdle(address(0)),0);
        assertEq(fees.compoundBalance(bucket,address(0)),0); assertGt(fees.buybackBalance(address(0)),0);
        uint256 earned = rewards.claimable(id,address(0)); assertGt(earned,0);
        (bool available,uint256 value) = nft.currentLPValue(id); assertTrue(available); assertEq(value,0);
        uint256 beforeOwner=ALICE.balance; vm.prank(ALICE); rewards.claim(id,address(0));
        assertEq(ALICE.balance,beforeOwner+earned); assertEq(wrapper.totalSupply(),0);
        access.setPaused(false); vm.expectRevert(); vault.resume(bucket,poolId,1,block.timestamp+100);
    }
    function testRetiredBridgeSelectorsRemainUncallable() public {
        (bool ok,)=address(vault).call(abi.encodeWithSignature("finalizeImport(uint256,uint128,uint256)",1,1,block.timestamp));
        assertFalse(ok);
        (ok,)=address(vault).call(abi.encodeWithSignature("confirmMigration(uint256,uint256,address)",1,block.chainid,BOB));
        assertFalse(ok);
    }
}
