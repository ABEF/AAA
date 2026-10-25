// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test, Vm} from "forge-std/Test.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {BalanceDelta, BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams, SwapParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {IPositionDescriptor} from "@uniswap/v4-periphery/src/interfaces/IPositionDescriptor.sol";
import {IWETH9} from "@uniswap/v4-periphery/src/interfaces/external/IWETH9.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationAssetsFactory} from "../src/ZZZActivationAssetsFactory.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {Ids, PoolKey, PoolConfig, Position} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {FactualPermit, FactualToken} from "./LiquidityFactualChecks.t.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

contract EconomicForcedETH { constructor(address payable to) payable { selfdestruct(to); } }

/// @dev TEST ONLY admission seam. Production pins Robinhood runtimes/addresses;
/// this accepts installed local v4 instead. No venue math/LP custody is mocked.
contract EconomicNativeRegistry {
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    ZZZOracle public immutable oracle;
    PoolConfig private config;
    bytes32 private immutable identity;
    constructor(address controller,ZZZOracle prices,address token) {
        oracle=prices;
        activationAssets=ZZZActivationAssets(ZZZActivationAssetsFactory(MockAccess(controller).activationAssetsFactory()).create());
        activationEntry=new ZZZActivationEntry(controller,address(this),address(activationAssets));
        config=PoolConfig(PoolKey(address(0),token,10020,200,address(0)),true,true,1000,100,100,200,600,1e18,1e30);
        identity=keccak256(abi.encode(config.key));
        activationAssets.admitPoolAsset(address(0)); activationAssets.admitPoolAsset(token);
    }
    function get(bytes32 id) external view returns(PoolConfig memory) { require(id==identity);return config; }
    function accounting(bytes32 id) external view returns(PoolConfig memory) { require(id==identity);return config; }
    function isNativePool(bytes32 id) external view returns(bool) { require(id==identity);return true; }
    function setRange(uint16 range) external { config.rangeBps=range; }
    function contributionValue(bytes32 id,uint256 a,uint256 b) external view returns(uint256) {
        require(id==identity);uint256 original=activationEntry.sourceValue(id,a,b);
        return original!=0?original:oracle.value(address(0),a)+oracle.value(config.key.currency1,b);
    }
}

/// @notice Four bounded composition scenarios, not a new full regression or live
/// qualification. Real installed PoolManager/PositionManager/StateView, actual
/// swaps/fees and production protocol accounting execute together. Governance,
/// feed independence/admission, VRF and Permit2 are explicit local substitutes.
/// The local venue uses the selected launch fee/spacing and observed directional
/// protocol fee (10020/200/1000); these constants are not a fresh on-chain read.
/// Ghost cash totals come from actual funding/claim events or known donations;
/// they do not recompute the production reward-index/share formulas.
contract IntegratedEconomicConservationTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    MockAccess private access;
    FactualToken private token;
    MockFeed private primary;
    MockFeed private secondary;
    ZZZOracle private oracle;
    EconomicNativeRegistry private registry;
    ZZZActivationEntry private entry;
    ZZZVault private vault;
    ZZZNFT private nft;
    ZZZMembership private membership;
    ZZZRewards private rewards;
    ZZZRoyaltyRewards private royalties;
    ZZZFeeController private fees;
    ZZZCompounder private compounder;
    MockVRF private vrf;
    PoolManager private core;
    StateView private state;
    PositionManager private positions;
    ZZZLiquidityManager private manager;
    CoreKey private key;
    bytes32 private pool;
    uint256[2] private credited;
    uint256[2] private claimed;
    uint256 private royaltyFunded;
    uint256 private royaltyClaimed;
    uint256[2] private grossHarvested;
    address private constant ALICE=address(0xA11CE);
    address private constant BOB=address(0xB0B);
    address private constant CAROL=address(0xCA201);
    uint256 private constant NATIVE_PREFUND=123;
    uint256 private constant TOKEN_PREFUND=456;
    bytes32 private constant CREDIT=keccak256("PoolRewardsCredited(uint256,address,uint256,uint256)");
    bytes32 private constant CLAIM=keccak256("Claimed(uint256,address,address,uint256)");
    bytes32 private constant HARVEST=keccak256("FeesCollected(uint256,uint256,uint256)");
    receive() external payable {}
    function activePlan(uint256) external pure returns(bytes32) { return bytes32(0); }

    function setUp() public {
        vm.warp(1_000_000);vm.deal(address(this),1_000_000 ether);
        vm.deal(ALICE,100_000 ether);vm.deal(BOB,100_000 ether);vm.deal(CAROL,100_000 ether);
        access=new MockAccess();token=new FactualToken();
        oracle=new ZZZOracle(address(access),address(0));access.bind(Ids.ORACLE,address(oracle));
        primary=new MockFeed(8,1e8);secondary=new MockFeed(8,1e8);
        _feeds(address(0));_feeds(address(token));
        registry=new EconomicNativeRegistry(address(access),oracle,address(token));entry=registry.activationEntry();
        core=new PoolManager(address(this));state=new StateView(IPoolManager(address(core)));
        FactualPermit permit=new FactualPermit();
        positions=new PositionManager(IPoolManager(address(core)),IAllowanceTransfer(address(permit)),100000,
            IPositionDescriptor(address(0)),IWETH9(address(0)));
        manager=new ZZZLiquidityManager(address(access),address(positions),address(state),address(core),address(permit));
        vault=new ZZZVault(address(access),block.chainid,payable(address(0x7EA5)));
        nft=new ZZZNFT(address(access),"ipfs://integrated-test/");
        membership=new ZZZMembership(address(access));rewards=new ZZZRewards(address(access));
        fees=new ZZZFeeController(address(access));compounder=new ZZZCompounder(address(access));
        access.bind(Ids.VAULT,address(vault));access.bind(Ids.NFT,address(nft));
        access.bind(Ids.MEMBERSHIP,address(membership));access.bind(Ids.REWARDS,address(rewards));
        access.bind(Ids.FEES,address(fees));access.bind(Ids.POOLS,address(registry));
        access.bind(Ids.LIQUIDITY,address(manager));access.bind(Ids.STRATEGY,address(new ZZZStrategy(address(access))));
        access.bind(Ids.MIGRATION,address(this));access.bind(Ids.COMPOUNDER,address(compounder));
        access.setKeeper(address(this),true);rewards.addAsset(address(token));
        vrf=new MockVRF();nft.configureRandomness(address(vrf),bytes32(uint256(1)),1,3,500000,false);
        royalties=nft.royaltyRewards();CanonicalFixture.bind(address(access));access.seal();
        PoolConfig memory c=registry.get(keccak256(abi.encode(PoolKey(address(0),address(token),10020,200,address(0)))));
        pool=keccak256(abi.encode(c.key));
        key=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),10020,200,IHooks(address(0)));
        core.initialize(key,uint160(1<<96));
        core.setProtocolFeeController(address(this));core.setProtocolFee(key,uint24(1000|(1000<<12)));
        token.mint(address(this),1_000_000 ether);token.mint(ALICE,100_000 ether);token.mint(BOB,100_000 ether);
        core.unlock(abi.encode(uint8(0),true,uint256(200_000 ether)));
        // Unsupported physical prefunds must survive every action, never buying
        // NFT shares or masquerading as fees. Force-send is deliberately tested.
        new EconomicForcedETH{value:NATIVE_PREFUND}(payable(address(vault)));
        new EconomicForcedETH{value:NATIVE_PREFUND}(payable(address(manager)));
        new EconomicForcedETH{value:NATIVE_PREFUND}(payable(address(entry)));
        new EconomicForcedETH{value:NATIVE_PREFUND}(payable(address(rewards)));
        token.mint(address(vault),TOKEN_PREFUND);token.mint(address(manager),TOKEN_PREFUND);
        token.mint(address(entry),TOKEN_PREFUND);token.mint(address(rewards),TOKEN_PREFUND);
        vm.recordLogs();
    }
    function _feeds(address asset) private {
        oracle.setDualFeed(asset,
            ZZZOracle.SourcePolicy(address(primary),address(primary).codehash,keccak256("mock-provider-a"),3600,8),
            ZZZOracle.SourcePolicy(address(secondary),address(secondary).codehash,keccak256("mock-provider-b"),3600,8),
            300,keccak256("test-only shared asset price; not independent provider qualification"));
    }
    function unlockCallback(bytes calldata data) external returns(bytes memory) {
        require(msg.sender==address(core));(uint8 mode,bool direction,uint256 amount)=abi.decode(data,(uint8,bool,uint256));
        BalanceDelta delta;
        if(mode==0 || mode==2) (delta,)=core.modifyLiquidity(key,ModifyLiquidityParams(-60000,60000,
            mode==0?int256(amount):-int256(amount),bytes32(0)),"");
        else delta=core.swap(key,SwapParams(direction,-int256(amount),direction?TickMath.MIN_SQRT_PRICE+1:TickMath.MAX_SQRT_PRICE-1),"");
        _settle(address(0),delta.amount0());_settle(address(token),delta.amount1());return "";
    }
    function _settle(address asset,int128 delta) private {
        if(delta==0)return;
        if(delta>0){core.take(Currency.wrap(asset),address(this),uint256(int256(delta)));return;}
        uint256 amount=uint256(-int256(delta));core.sync(Currency.wrap(asset));
        if(asset==address(0))assertEq(core.settle{value:amount}(),amount);
        else {token.transfer(address(core),amount);assertEq(core.settle(),amount);}
    }
    function _mint(address owner) private returns(uint256 id) {
        vm.prank(owner);id=vault.mintDormant{value:0.05 ether}();
        vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
    }
    function _contribute(address owner,uint256 id,uint256 amount,bool increase) private {
        ZZZActivationEntry.Request memory r=ZZZActivationEntry.Request(id,pool,address(0),amount,bytes32(0),0,1,block.timestamp+100,increase);
        vm.prank(owner);entry.executeReviewed{value:amount}(r, 200);
    }
    function _balanced(address owner,uint256 id,uint256 half,bool increase) private {
        vm.startPrank(owner);token.approve(address(vault),half);
        if(increase)vault.increase{value:half}(id,half,half,1,block.timestamp+100);
        else vault.activate{value:half}(id,pool,half,half,1,block.timestamp+100);
        vm.stopPrank();
    }
    function _targetPair(address owner,uint256 id,uint256 total,bool increase,bool reject) private {
        (int24 lower,int24 upper,)=ZZZStrategy(access.module(Ids.STRATEGY)).target(pool);
        uint160 q=manager.spot(pool);
        uint256 u0=SqrtPriceMath.getAmount0Delta(q,TickMath.getSqrtPriceAtTick(upper),1e18,false);
        uint256 u1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),q,1e18,false);
        uint256 a0=total*u0/(u0+u1);uint256 a1=total-a0;
        vm.startPrank(owner);token.approve(address(vault),a1);
        if(reject)vm.expectRevert(ZZZContributionPricing.Slippage.selector);
        if(increase)vault.increase{value:a0}(id,a0,a1,1,block.timestamp+100);
        else vault.activate{value:a0}(id,pool,a0,a1,1,block.timestamp+100);
        vm.stopPrank();
    }
    function _trade(bool nativeInput,uint256 amount) private {core.unlock(abi.encode(uint8(1),nativeInput,amount));}
    function _deepenExternalLiquidity() private {
        // Explicit success-fixture depth, not a claim about actual pool depth.
        // Direct external core liquidity is outside protocol principal/revenue.
        vm.deal(address(this),address(this).balance+2_000_000 ether);
        token.mint(address(this),2_000_000 ether);
        core.unlock(abi.encode(uint8(0),true,uint256(1_800_000 ether)));
    }
    function _royalty(uint256 amount) private {
        royaltyFunded+=amount;(bool ok,)=payable(address(royalties)).call{value:amount}("");assertTrue(ok);
    }
    function _observe() private {
        Vm.Log[] memory logs=vm.getRecordedLogs();
        for(uint256 i;i<logs.length;++i){
            Vm.Log memory e=logs[i];if(e.topics.length==0)continue;
            if(e.emitter==address(rewards)&&e.topics[0]==CREDIT){
                uint256 slot=address(uint160(uint256(e.topics[2])))==address(0)?0:1;
                (uint256 own,uint256 shared)=abi.decode(e.data,(uint256,uint256));credited[slot]+=own+shared;
            }else if(e.emitter==address(rewards)&&e.topics[0]==CLAIM){
                uint256 slot=address(uint160(uint256(e.topics[2])))==address(0)?0:1;
                claimed[slot]+=abi.decode(e.data,(uint256));
            }else if(e.emitter==address(royalties)&&e.topics[0]==CLAIM)royaltyClaimed+=abi.decode(e.data,(uint256));
            else if(e.emitter==address(vault)&&e.topics[0]==HARVEST){
                (uint256 a,uint256 b)=abi.decode(e.data,(uint256,uint256));grossHarvested[0]+=a;grossHarvested[1]+=b;
            }
        }
        vm.recordLogs();
    }
    function _assertBacking() private {
        _observe();
        assertEq(address(rewards).balance+claimed[0],credited[0]+NATIVE_PREFUND,"native LP cash conservation");
        assertEq(token.balanceOf(address(rewards))+claimed[1],credited[1]+TOKEN_PREFUND,"token LP cash conservation");
        assertEq(rewards.liabilities(address(0))+claimed[0],credited[0],"native LP liability conservation");
        assertEq(rewards.liabilities(address(token))+claimed[1],credited[1],"token LP liability conservation");
        assertEq(address(royalties).balance+royaltyClaimed,royaltyFunded,"royalties separate cash conservation");
        assertEq(royalties.accounted(address(0)),royalties.liabilities(address(0))+royalties.orphaned(address(0)));
        assertEq(address(vault).balance,vault.totalIdle(address(0))+NATIVE_PREFUND,"vault native prefund preserved");
        assertEq(token.balanceOf(address(vault)),vault.totalIdle(address(token))+TOKEN_PREFUND,"vault token prefund preserved");
        assertEq(address(manager).balance,NATIVE_PREFUND);assertEq(token.balanceOf(address(manager)),TOKEN_PREFUND);
        assertEq(address(entry).balance,NATIVE_PREFUND);assertEq(token.balanceOf(address(entry)),TOKEN_PREFUND);
        assertGe(address(fees).balance,fees.accounted(address(0)));assertGe(token.balanceOf(address(fees)),fees.accounted(address(token)));
        assertEq(token.allowance(address(entry),address(vault)),0);
    }
    function _claim(address owner,uint256 id) private {
        vm.startPrank(owner);rewards.claim(id,address(0));rewards.claim(id,address(token));royalties.claim(id,address(0));vm.stopPrank();
    }

    function testActualV4LifetimeFeesRoyaltiesGrowthCompoundRebalanceAndTransferRemainFunded() public {
        _deepenExternalLiquidity();
        uint256 a=_mint(ALICE);uint256 b=_mint(BOB);uint256 dormant=_mint(CAROL);
        _contribute(ALICE,a,100 ether,false);_royalty(31);royalties.sync(address(0));
        _contribute(BOB,b,100 ether,false);assertEq(royalties.claimable(b,address(0)),0,"no past royalties");
        uint256 bucket=vault.nftBucket(a);uint256 sharesA=vault.sharesOf(a);uint256 sharesB=vault.sharesOf(b);
        _trade(true,10 ether);_trade(false,10 ether);vault.collectFees(bucket,block.timestamp+100);
        _assertBacking();assertGt(credited[0],0);assertGt(credited[1],0);
        assertGt(grossHarvested[0],credited[0]);assertGt(grossHarvested[1],credited[1]);
        assertEq(rewards.claimable(dormant,address(0)),0);assertEq(royalties.claimable(dormant,address(0)),0);
        _contribute(ALICE,a,5 ether,true);assertGt(vault.sharesOf(a),sharesA);assertEq(vault.sharesOf(b),sharesB);
        _trade(true,10 ether);_trade(false,10 ether);compounder.compound(bucket,1,block.timestamp+100);
        uint256 afterGrowth=vault.sharesOf(a);uint256 previousLP=vault.group(bucket).lpTokenId;
        vm.warp(block.timestamp+601);registry.setRange(1100);vault.rebalance(bucket,1,block.timestamp+100);
        assertTrue(vault.group(bucket).lpTokenId!=previousLP);assertEq(vault.sharesOf(a),afterGrowth);
        assertEq(vault.sharesOf(b),sharesB);assertEq(membership.totalEligible(),2);
        _royalty(97);_assertBacking();
        uint256 beforeLP=rewards.claimable(a,address(0));uint256 beforeRoyalty=royalties.claimable(a,address(0));
        assertGt(beforeLP,0);assertGt(beforeRoyalty,0);
        vm.prank(ALICE);nft.transferFrom(ALICE,CAROL,a);
        vm.prank(ALICE);vm.expectRevert();rewards.claim(a,address(0));
        vm.prank(ALICE);vm.expectRevert();royalties.claim(a,address(0));
        uint256 beforeETH=CAROL.balance;_claim(CAROL,a);
        assertEq(CAROL.balance-beforeETH,beforeLP+beforeRoyalty);_claim(BOB,b);_assertBacking();
        assertEq(rewards.claimable(a,address(0)),0);assertEq(royalties.claimable(a,address(0)),0);
        assertEq(positions.ownerOf(vault.group(bucket).lpTokenId),address(vault));
    }

    function testActualV4BalancedJoinsCannotCaptureOldIncomeOrPrefundsAndPreserveShares() public {
        uint256 a=_mint(ALICE);uint256 b=_mint(BOB);_balanced(ALICE,a,50 ether,false);
        uint256 initial=vault.sharesOf(a);assertGe(initial,99 ether);assertLe(initial,100 ether);
        _royalty(1 ether);royalties.sync(address(0));_balanced(BOB,b,50 ether,false);
        // The asymmetric tick-rounded range needs a small real balancing swap,
        // even for equal-dollar input. Bound actual value instead of pretending
        // an exactly lossless synthetic 50/50 venue or equal share issuance.
        assertGe(vault.sharesOf(b),98 ether);assertLe(vault.sharesOf(b),101 ether);assertEq(vault.sharesOf(a),initial);
        assertEq(royalties.claimable(b,address(0)),0);assertEq(rewards.claimable(b,address(0)),0);
        uint256 bucket=vault.nftBucket(a);assertEq(vault.bucketTotalShares(bucket),vault.sharesOf(a)+vault.sharesOf(b));
        (bool availableA,uint256 valueA)=nft.currentLPValue(a);(bool availableB,uint256 valueB)=nft.currentLPValue(b);
        assertTrue(availableA&&availableB);assertGe(valueA,99 ether);assertLe(valueA,101 ether);
        assertGe(valueB,99 ether);assertLe(valueB,101 ether);
        _assertBacking();
    }

    function changePriceDuringFinalReset() external {
        require(msg.sender==address(token));primary.set(100_100_000,block.timestamp,block.timestamp);
        secondary.set(100_100_000,block.timestamp,block.timestamp);
    }
    function testActualV4LateSourceRoundCallbackRollsBackLPFundsEligibilityAndFees() public {
        // The intended final-check path must be reached; a thin-market execution
        // rejection would otherwise make a generic expectRevert vacuously pass.
        _deepenExternalLiquidity();
        uint256 id=_mint(ALICE);uint256 beforeETH=ALICE.balance;uint256 beforeToken=token.balanceOf(ALICE);
        vm.prank(ALICE);token.approve(address(entry),100 ether);
        token.arm(address(entry),2,address(this),abi.encodeCall(this.changePriceDuringFinalReset,()));
        ZZZActivationEntry.Request memory r=ZZZActivationEntry.Request(id,pool,address(token),100 ether,bytes32(0),0,1,block.timestamp+100,false);
        vm.expectCall(address(primary),abi.encodeCall(primary.set,(100_100_000,block.timestamp,block.timestamp)));
        vm.prank(ALICE);vm.expectRevert(ZZZContributionPricing.InvalidState.selector);entry.executeReviewed(r, 200);
        assertEq(ALICE.balance,beforeETH);assertEq(token.balanceOf(ALICE),beforeToken);
        assertEq(token.allowance(ALICE,address(entry)),100 ether);assertEq(vault.nftBucket(id),0);
        assertEq(vault.sharesOf(id),0);assertFalse(membership.eligible(id));assertEq(royalties.weightOf(id),0);
        assertEq(positions.nextTokenId(),1);assertEq(primary.answer(),1e8);assertTrue(nft.traitsReady(id));
        _assertBacking();
    }

    function testActualV4ThinMarketReconcilesActualPostSwapRatioWithinOriginalOnePercentFloor() public {
        uint256 id=_mint(ALICE);
        assertEq(vault.migrationBudget().contributionLossBps(),200,"approved two-percent default");
        vault.migrationBudget().setLossLimits(100,300);
        assertEq(vault.migrationBudget().contributionLossBps(),100,"explicit stricter one-percent proof");
        vm.expectCall(address(manager),abi.encodeWithSelector(ZZZLiquidityManager.swap.selector),uint64(2));
        uint256 startGas=gasleft();
        _contribute(ALICE,id,100 ether,false);
        emit log_named_uint("actual.v4.shallow.native.two-pass.activation.harness-gas",startGas-gasleft());
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        (uint256 deployed,uint256 idle)=vault.migrationBudget().nav(bucket);
        assertGe(deployed,99 ether,"actual deployed value, not idle-inclusive NAV");
        assertLt(idle,0.01 ether,"post-swap correction reduces recorded 0.5335 idle");
        emit log_named_uint("actual.v4.shallow.native.deployed.usd18",deployed);
        emit log_named_uint("actual.v4.shallow.native.idle.usd18",idle);
        assertTrue(membership.eligible(id));assertEq(positions.ownerOf(p.lpTokenId),address(vault));
        assertEq(vault.bucketTotalShares(bucket),vault.sharesOf(id));
        assertGt(vault.sharesOf(id),0);_assertBacking();
    }

    function testActualV4UnfeasibleDepthStillRollsBackEveryLedger() public {
        // Withdraw only external seed liquidity. Protocol custody is untouched;
        // this market is deliberately too thin for the same guarded $100 input.
        core.unlock(abi.encode(uint8(2),true,uint256(199_000 ether)));
        uint256 id=_mint(ALICE);uint256 userETH=ALICE.balance;uint256 userToken=token.balanceOf(ALICE);
        uint256 coreETH=address(core).balance;uint256 coreToken=token.balanceOf(address(core));
        (uint160 spotBefore,,uint24 protocol,uint24 lpFee)=state.getSlot0(PoolId.wrap(pool));
        assertEq(protocol,uint24(1000|(1000<<12)));assertEq(lpFee,10020);
        ZZZActivationEntry.Request memory r=ZZZActivationEntry.Request(id,pool,address(0),100 ether,bytes32(0),0,1,block.timestamp+100,false);
        vm.expectCall(address(manager),abi.encodeWithSelector(ZZZLiquidityManager.swap.selector));
        vm.prank(ALICE);vm.expectRevert(bytes4(keccak256("Slippage()")));entry.executeReviewed{value:100 ether}(r, 200);
        assertEq(ALICE.balance,userETH);assertEq(token.balanceOf(ALICE),userToken);
        assertEq(address(core).balance,coreETH);assertEq(token.balanceOf(address(core)),coreToken);
        (uint160 spotAfter,,,)=state.getSlot0(PoolId.wrap(pool));assertEq(spotAfter,spotBefore);
        assertEq(core.protocolFeesAccrued(Currency.wrap(address(0))),0);
        assertEq(core.protocolFeesAccrued(Currency.wrap(address(token))),0);
        assertEq(vault.nftBucket(id),0);assertEq(vault.sharesOf(id),0);assertEq(vault.contributionUSD(id),0);
        assertEq(vault.bucketCount(),0);assertFalse(membership.eligible(id));assertEq(membership.totalEligible(),0);
        assertEq(royalties.weightOf(id),0);assertEq(royalties.totalWeight(),0);
        assertEq(positions.nextTokenId(),1);assertEq(rewards.liabilities(address(0)),0);
        assertEq(rewards.liabilities(address(token)),0);assertEq(fees.accounted(address(0)),0);
        assertEq(fees.accounted(address(token)),0);assertTrue(nft.traitsReady(id));
        assertFalse(ZZZContributionPricing(oracle.contributionPricing()).active());_assertBacking();
    }

    function testActualV4SecondBalancingSwapFailureRollsBackTheFirstSwapAndAllEntitlements() public {
        uint256 id=_mint(ALICE);uint256 userETH=ALICE.balance;uint256 userToken=token.balanceOf(ALICE);
        uint256 coreETH=address(core).balance;uint256 coreToken=token.balanceOf(address(core));
        (uint160 spotBefore,,,)=state.getSlot0(PoolId.wrap(pool));
        // Native first balances 0 -> 1; its correction reverses 1 -> 0. Inject
        // only the second dependency failure, preserving the real first swap.
        bytes memory failure=abi.encodeWithSignature("CorrectionUnavailable()");
        vm.mockCallRevert(address(manager),abi.encodeWithSelector(ZZZLiquidityManager.swap.selector,pool,false),failure);
        vm.expectCall(address(manager),abi.encodeWithSelector(ZZZLiquidityManager.swap.selector),uint64(2));
        ZZZActivationEntry.Request memory r=ZZZActivationEntry.Request(id,pool,address(0),100 ether,bytes32(0),0,1,block.timestamp+100,false);
        vm.prank(ALICE);vm.expectRevert(failure);entry.executeReviewed{value:100 ether}(r, 200);
        vm.clearMockedCalls();vm.getRecordedLogs();vm.recordLogs();
        assertEq(ALICE.balance,userETH);assertEq(token.balanceOf(ALICE),userToken);
        assertEq(address(core).balance,coreETH);assertEq(token.balanceOf(address(core)),coreToken);
        (uint160 spotAfter,,,)=state.getSlot0(PoolId.wrap(pool));assertEq(spotAfter,spotBefore);
        assertEq(vault.nftBucket(id),0);assertEq(vault.sharesOf(id),0);assertEq(vault.bucketCount(),0);
        assertFalse(membership.eligible(id));assertEq(royalties.weightOf(id),0);
        assertEq(rewards.liabilities(address(0)),0);assertEq(rewards.liabilities(address(token)),0);
        assertEq(positions.nextTokenId(),1);_assertBacking();
    }

    function testActualV4ApprovedTwoPercentDefaultAndStricterOnePercentApplyToActivationAndGrowth() public {
        // Independent local source controls intentionally disagree by 1.5%.
        // Match the tick-rounded LP ratio so this tests the conservative USD
        // contribution floor rather than failing an unrelated swap minimum.
        secondary.set(101_500_000,block.timestamp,block.timestamp);
        uint256 id=_mint(ALICE);assertEq(vault.migrationBudget().contributionLossBps(),200);
        vault.migrationBudget().setLossLimits(100,300);
        _targetPair(ALICE,id,100 ether,false,true);
        assertEq(vault.nftBucket(id),0);assertFalse(membership.eligible(id));_assertBacking();
        vault.migrationBudget().setLossLimits(200,300);
        _targetPair(ALICE,id,100 ether,false,false);
        uint256 bucket=vault.nftBucket(id);uint256 shares=vault.sharesOf(id);
        assertTrue(membership.eligible(id));assertGt(shares,0);_assertBacking();
        vault.migrationBudget().setLossLimits(100,300);
        _targetPair(ALICE,id,5 ether,true,true);
        assertEq(vault.sharesOf(id),shares);assertEq(vault.contributionUSD(id),100 ether);_assertBacking();
        vault.migrationBudget().setLossLimits(200,300);
        _targetPair(ALICE,id,5 ether,true,false);
        assertGt(vault.sharesOf(id),shares);assertEq(vault.contributionUSD(id),105 ether);_assertBacking();
    }

    function testActualV4InverseZZZPriceRangeDeploysGrowsAndKeepsFeeAccounting() public {
        registry.setRange(2500);
        ZZZStrategy strategy=ZZZStrategy(access.module(Ids.STRATEGY));
        strategy.setRangeOrientation(pool,1);
        uint256 id=_mint(ALICE);_contribute(ALICE,id,100 ether,false);
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        (int24 lower,int24 upper)=manager.ticks(p.lpTokenId);
        uint256 lo=TickMath.getSqrtPriceAtTick(lower);uint256 hi=TickMath.getSqrtPriceAtTick(upper);
        uint256 center=uint256(p.centerX96)*p.centerX96;
        // ETH is currency0, so ZZZ's ETH price is the inverse raw pool ratio.
        // Actual installed-position ticks must bracket its requested +/-25%.
        assertLe(lo*lo*12500,center*10000);
        assertGe(hi*hi*7500,center*10000);
        assertFalse(strategy.rangeUpdatePending(bucket));
        uint256 shares=vault.sharesOf(id);uint128 liquidity=positions.getPositionLiquidity(p.lpTokenId);
        _trade(true,1 ether);_trade(false,1 ether);vault.collectFees(bucket,block.timestamp+100);
        _assertBacking();assertGt(credited[0]+credited[1],0,"real LP trading fees");
        uint256 nativeClaim=rewards.claimable(id,address(0));uint256 tokenClaim=rewards.claimable(id,address(token));
        _contribute(ALICE,id,5 ether,true);
        assertGt(positions.getPositionLiquidity(p.lpTokenId),liquidity);assertGt(vault.sharesOf(id),shares);
        assertGe(rewards.claimable(id,address(0)),nativeClaim);assertGe(rewards.claimable(id,address(token)),tokenClaim);
        assertEq(positions.ownerOf(p.lpTokenId),address(vault));_assertBacking();
    }

    function testActualV4IdleOnlyCompoundGrowsLPWithoutMovingSharesOrTakingPrefunds() public {
        uint256 id=_mint(ALICE);_contribute(ALICE,id,100 ether,false);
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        uint128 beforeLiquidity=positions.getPositionLiquidity(p.lpTokenId);
        uint256 shares=vault.sharesOf(id);
        assertEq(fees.compoundBalance(bucket,address(0)),0);assertEq(fees.compoundBalance(bucket,address(token)),0);
        assertGt(p.idle0+p.idle1,0,"non-vacuous idle-only input");
        _royalty(1 ether);royalties.sync(address(0));uint256 royalty=royalties.claimable(id,address(0));
        compounder.compound(bucket,1,block.timestamp+100);
        assertGt(positions.getPositionLiquidity(p.lpTokenId),beforeLiquidity,"actual LP increased");
        Position memory afterCompound=vault.group(bucket);
        assertLt(afterCompound.idle0+afterCompound.idle1,p.idle0+p.idle1,"less attributed idle");
        assertEq(vault.sharesOf(id),shares);assertEq(vault.bucketTotalShares(bucket),shares);
        assertEq(royalties.claimable(id,address(0)),royalty);
        assertEq(vault.migrationBudget().lastCompound(bucket),block.timestamp);
        assertEq(vault.migrationBudget().IDLE_COMPOUNDING_VERSION(),1);_assertBacking();
        vm.expectRevert();compounder.compound(bucket,1,block.timestamp+100);
        assertEq(vault.migrationBudget().lastCompound(bucket),block.timestamp);
    }

    function testActualV4FailedIdleCompoundDoesNotConsumeCooldownOrLeaveBudgetContext() public {
        uint256 id=_mint(ALICE);_contribute(ALICE,id,100 ether,false);
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        uint128 beforeLiquidity=positions.getPositionLiquidity(p.lpTokenId);uint256 shares=vault.sharesOf(id);
        _assertBacking();
        vm.expectRevert();compounder.compound(bucket,type(uint128).max,block.timestamp+100);
        // Foundry records logs from reverted calls as well. They are not chain
        // receipts and must not enter the independent committed-income ghost.
        vm.getRecordedLogs();vm.recordLogs();
        assertEq(vault.migrationBudget().lastCompound(bucket),0,"failed attempt cannot consume cooldown");
        assertEq(positions.getPositionLiquidity(p.lpTokenId),beforeLiquidity);assertEq(vault.sharesOf(id),shares);
        assertEq(vault.group(bucket).idle0,p.idle0);assertEq(vault.group(bucket).idle1,p.idle1);_assertBacking();
        compounder.compound(bucket,1,block.timestamp+100);
        assertGt(positions.getPositionLiquidity(p.lpTokenId),beforeLiquidity);_assertBacking();
    }

    function testActualV4SmallReceiptsAndRepeatedClaimsKeepFractionsAndLedgersSeparate() public {
        uint256 a=_mint(ALICE);uint256 b=_mint(BOB);_balanced(ALICE,a,50 ether,false);_balanced(BOB,b,50 ether,false);
        uint256 bucket=vault.nftBucket(a);
        for(uint256 i;i<9;++i){
            _royalty(1);royalties.sync(address(0));_trade(i%2==0,1e12);vault.collectFees(bucket,block.timestamp+100);
            _claim(ALICE,a);if(i%2==0)_claim(BOB,b);_assertBacking();
        }
        _claim(ALICE,a);_claim(BOB,b);_assertBacking();
        assertGt(credited[0]+credited[1],0,"real trades must generate protocol revenue");
        assertGt(royaltyClaimed,0,"royalty checks cannot be vacuous");assertLe(royaltyClaimed,9);
        assertLe(rewards.claimable(a,address(0))+rewards.claimable(b,address(0)),rewards.liabilities(address(0)));
        assertEq(vault.bucketTotalShares(bucket),vault.sharesOf(a)+vault.sharesOf(b));
    }
}
