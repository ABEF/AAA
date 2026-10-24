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
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
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
    constructor() MockToken(18) {}
    function forceOnTransfer(address from,address payable target) external { forceFrom=from; forceTarget=target; }
    function _update(address from,address to,uint256 amount) internal override {
        super._update(from,to,amount);
        if (from==forceFrom && amount!=0 && forceTarget!=address(0)) {
            new BoundaryForce{value:1}(forceTarget);
        }
    }
}

/// @dev Explicit fake admission. Real Vault, Entry, Strategy, manager and funded
/// ledgers execute below; this does not qualify Robinhood runtime pins/markets.
contract NativeFlowRegistry {
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    ZZZOracle public immutable oracle;
    PoolConfig private config;
    constructor(address controller, ZZZOracle prices, address token) {
        oracle = prices;
        activationAssets = new ZZZActivationAssets(controller,address(this));
        activationEntry = new ZZZActivationEntry(controller,address(this),address(activationAssets));
        config = PoolConfig(PoolKey(address(0),token,10020,60,address(0)),true,true,1000,100,100,200,600,1e18,1e30);
        activationAssets.admitPoolAsset(address(0)); activationAssets.admitPoolAsset(token);
    }
    function get(bytes32) external view returns (PoolConfig memory) { return config; }
    function accounting(bytes32) external view returns (PoolConfig memory) { return config; }
    function isNativePool(bytes32) external pure returns (bool) { return true; }
    function setRange(uint16 range) external { config.rangeBps = range; }
    function contributionValue(bytes32 pool,uint256 a0,uint256 a1) external view returns (uint256) {
        uint256 original = activationEntry.sourceValue(pool,a0,a1);
        return original != 0 ? original : oracle.value(address(0),a0)+oracle.value(config.key.currency1,a1);
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
    function setUp() public {
        vm.warp(1_000_000); access = new MockAccess(); token = new NativeFlowToken(); wrapper = new BoundaryWETH();
        wrapper.failures(true,true);
        ZZZOracle oracle = new ZZZOracle(address(access),address(0));
        MockFeed price = new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(price),1 hours); oracle.setTestFeed(address(token),address(price),1 hours);
        access.bind(Ids.ORACLE,address(oracle));
        pools = new NativeFlowRegistry(address(access),oracle,address(token));
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
        vm.deal(ALICE,1000 ether); vm.deal(BOB,1000 ether); vm.deal(address(this),1000 ether); vm.deal(address(core),10000 ether);
        token.mint(address(core),10000 ether); token.mint(ALICE,1000 ether); token.mint(BOB,1000 ether);
    }
    function _mint(address owner) private returns (uint256 id) {
        vm.prank(owner); id = vault.mintDormant{value:0.05 ether}();
        vrf.fulfill(nft.requestOf(id),0,0); nft.finalizeTraits(id);
    }
    function _entry(address owner,uint256 id,uint256 amount,bool grow) private {
        ZZZActivationEntry.Request memory r = ZZZActivationEntry.Request(id,poolId,address(0),amount,bytes32(0),0,1,block.timestamp+100,grow);
        vm.prank(owner); entry.execute{value:amount}(r);
    }
    function testNativeActivationGrowthAndCurrentValueAreBackedWithoutWrapper() public {
        uint256 id = _mint(ALICE); _entry(ALICE,id,100 ether,false);
        uint256 shares = vault.sharesOf(id); uint256 bucket = vault.nftBucket(id);
        assertGt(shares,0); assertTrue(membership.eligible(id)); assertEq(vault.ACCOUNTING_VERSION(),2);
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
    function testNativeRawPrincipalDepartureAndFullReturnIgnoreBrokenWrapper() public {
        uint256 id = _mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket = vault.nftBucket(id);
        positions.fees(vault.group(bucket).lpTokenId,1 ether,0);
        access.setPaused(true); vault.park(bucket,block.timestamp+100);
        uint256 holderFees = rewards.claimable(id,address(0)); uint256 shares = vault.sharesOf(id);
        uint256 beforeETH = address(this).balance;
        (uint256 a0,uint256 a1) = vault.releaseForMigration(bucket,keccak256("raw exit"),block.timestamp+100);
        assertEq(address(this).balance,beforeETH+a0); assertGt(a0,0); assertGt(a1,0);
        assertEq(rewards.claimable(id,address(0)),holderFees); assertEq(vault.sharesOf(id),shares);
        token.approve(address(vault),a1);
        vm.expectRevert(); vault.acceptHandoff(bucket,poolId,a0,a1,0,block.timestamp+100);
        vault.acceptHandoff{value:a0}(bucket,poolId,a0,a1,0,block.timestamp+100);
        assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Parked));
        assertEq(vault.totalIdle(address(0)),a0); assertEq(vault.sharesOf(id),shares);
        assertEq(rewards.claimable(id,address(0)),holderFees); assertEq(wrapper.totalSupply(),0);
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
    function testNativeNormalConsolidationKeepsStricterSwapFloorAndFeeBacking() public {
        uint256 id=_mint(ALICE); _entry(ALICE,id,100 ether,false); uint256 bucket=vault.nftBucket(id);
        positions.fees(vault.group(bucket).lpTokenId,1 ether,0); access.setPaused(true);
        vault.park(bucket,block.timestamp+100); Position memory p=vault.group(bucket);
        uint256 earned=rewards.claimable(id,address(0)); uint256 reserve=fees.compoundBalance(bucket,address(0));
        uint256 minimum=(p.idle0+p.idle1)*97/100;
        vault.consolidateHandoff(bucket,address(token),minimum,block.timestamp+100);
        assertEq(vault.group(bucket).idle0,0); assertGe(vault.group(bucket).idle1,minimum);
        assertEq(rewards.claimable(id,address(0)),earned); assertEq(fees.compoundBalance(bucket,address(0)),reserve);
        assertEq(wrapper.totalSupply(),0);
    }
    function testRetiredBridgeSelectorsRemainUncallable() public {
        (bool ok,)=address(vault).call(abi.encodeWithSignature("finalizeImport(uint256,uint128,uint256)",1,1,block.timestamp));
        assertFalse(ok);
        (ok,)=address(vault).call(abi.encodeWithSignature("confirmMigration(uint256,uint256,address)",1,block.chainid,BOB));
        assertFalse(ok);
    }
}
