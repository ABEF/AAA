// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta,BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams,SwapParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionInfo} from "@uniswap/v4-periphery/src/libraries/PositionInfoLibrary.sol";
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
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationAssetsFactory} from "../src/ZZZActivationAssetsFactory.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZLPPositionExecutor} from "../src/ZZZLPPositionExecutor.sol";
import {Ids,PoolKey,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {EmergencyRebalance} from "../src/interfaces/IZZZEmergency.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
interface IOptionalResidualBurnCallback { function residualBurnCallback(uint8) external; }

contract OptionalToken is ERC20 {
    constructor()ERC20("TEST ONLY ZZZ","TZZZ"){}
    function mint(address to,uint256 amount)external{_mint(to,amount);}
}
/// @dev Explicit local Permit2 substitute; no provider/approval qualification.
contract OptionalPermit {
    struct Approval{uint160 amount;uint48 expiry;}
    mapping(address=>mapping(address=>mapping(address=>Approval)))public allowances;
    function approve(address token,address spender,uint160 amount,uint48 expiry)external{
        allowances[msg.sender][token][spender]=Approval(amount,expiry);
    }
    function transferFrom(address from,address to,uint160 amount,address token)external{
        Approval storage a=allowances[from][token][msg.sender];require(a.expiry>=block.timestamp && a.amount>=amount);
        a.amount-=amount;require(IERC20(token).transferFrom(from,to,amount));
    }
}
/// @dev Real PositionManager execution with a deliberate failure seam at one
/// MINT/BURN action. All other core/periphery execution remains unmodified.
contract OptionalPositions is PositionManager {
    uint256 public failMintId;uint256 public failBurnId;
    address public callbackTarget;uint256 public callbackBurnId;uint8 public callbackKind;
    error IntentionalMintFailure();error IntentionalBurnFailure();
    constructor(IPoolManager core,IAllowanceTransfer permit)
        PositionManager(core,permit,100000,IPositionDescriptor(address(0)),IWETH9(address(0))){}
    function failAt(uint256 mintId,uint256 burnId)external{failMintId=mintId;failBurnId=burnId;}
    function configureBurnCallback(address target,uint256 aux,uint8 kind)external{callbackTarget=target;callbackBurnId=aux;callbackKind=kind;}
    function _handleAction(uint256 action,bytes calldata params)internal override{
        if(action==0x02 && nextTokenId==failMintId)revert IntentionalMintFailure();
        if(action==0x03 && abi.decode(params,(uint256))==failBurnId)revert IntentionalBurnFailure();
        super._handleAction(action,params);
        // TEST ONLY: emulate a dependency callback after the selected burn.
        // It is not behavior asserted of the deployed hookless PositionManager.
        if(action==0x03 && abi.decode(params,(uint256))==callbackBurnId && callbackTarget!=address(0))
            IOptionalResidualBurnCallback(callbackTarget).residualBurnCallback(callbackKind);
    }
}
/// @dev TEST ONLY native admission seam. Production Registry runtime/network
/// admission is not bypassed in production or claimed qualified by this suite.
contract OptionalRegistry {
    uint64 public configurationRevision=1;
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    ZZZOracle public immutable oracle;
    PoolConfig private c;PoolConfig private target;bytes32 private immutable pool;bytes32 private targetId;
    constructor(address controller,ZZZOracle pricing,address token){
        oracle=pricing;
        activationAssets=ZZZActivationAssets(ZZZActivationAssetsFactory(MockAccess(controller).activationAssetsFactory()).create());
        activationEntry=new ZZZActivationEntry(controller,address(this),address(activationAssets));
        c=PoolConfig(PoolKey(address(0),token,10020,200,address(0)),true,true,5000,100,300,500,43200,100e18,1_000_000e18);
        pool=keccak256(abi.encode(c.key));activationAssets.admitPoolAsset(address(0));activationAssets.admitPoolAsset(token);
    }
    function get(bytes32 id)external view returns(PoolConfig memory){if(id==targetId && id!=0)return target;require(id==pool);return c;}
    function accounting(bytes32 id)external view returns(PoolConfig memory){if(id==targetId && id!=0)return target;require(id==pool);return c;}
    function isNativePool(bytes32 id)external view returns(bool){return id==pool || (targetId!=0 && id==targetId);}
    function admitTarget()external returns(bytes32){target=c;target.key.fee=3000;targetId=keccak256(abi.encode(target.key));++configurationRevision;return targetId;}
    function setRange(uint16 width)external{c.rangeBps=width;++configurationRevision;}
    function setSpotDeviation(uint16 deviation)external{c.maxSpotDeviationBps=deviation;++configurationRevision;}
    function setOperations(bool enabled)external{c.operationsEnabled=enabled;++configurationRevision;}
    function setMinimum(uint256 amount)external{c.minDepositUSD=amount;++configurationRevision;}
    function contributionValue(bytes32 id,uint256 a0,uint256 a1)external view returns(uint256){
        require(id==pool);uint256 original=activationEntry.sourceValue(id,a0,a1);
        return original!=0?original:oracle.value(address(0),a0)+oracle.value(c.key.currency1,a1);
    }
}

/// @notice Actual local v4 PoolManager/PositionManager/StateView and production
/// PoPL custody/accounting execute together. Mock controller, correlated USD
/// feeds, VRF, Permit2 and native admission are explicit local substitutes.
contract OptionalPortfolioCoreTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    MockAccess private access;OptionalToken private token;MockFeed private ethA;MockFeed private ethB;
    MockFeed private zzzA;MockFeed private zzzB;ZZZOracle private oracle;
    OptionalRegistry private registry;ZZZVault private vault;ZZZNFT private nft;MockVRF private vrf;
    ZZZMembership private membership;ZZZRewards private rewards;ZZZFeeController private fees;
    ZZZMigration private migration;ZZZStrategy private strategy;ZZZPortfolioPolicy private policy;
    PoolManager private core;StateView private state;OptionalPositions private positions;
    ZZZLiquidityManager private manager;CoreKey private key;CoreKey private targetKey;bytes32 private pool;
    address private constant ALICE=address(0xA11CE);address private constant BOB=address(0xB0B);
    uint160 private constant Q96=uint160(1<<96);
    uint256 private residualCallbackBucket;
    struct ResidualSnapshot {
        Position position;uint128 mainL;uint128 auxL;uint256 shares;uint256 total;
        uint256[2] claims;uint256[2] compound;uint256[2] buyback;uint256[2] principal;
        uint256 operatorETH;uint256 operatorZZZ;bytes32 fingerprint;
    }
    receive()external payable{}

    function setUp()public{
        vm.warp(1_000_000);vm.deal(address(this),10_000_000 ether);vm.deal(ALICE,100_000 ether);vm.deal(BOB,100_000 ether);
        access=new MockAccess(); ProtocolPolicyFixture.bind(address(access));token=new OptionalToken();oracle=new ZZZOracle(address(access),address(0));
        access.bind(Ids.ORACLE,address(oracle));ethA=new MockFeed(18,1e18);ethB=new MockFeed(18,1e18);
        zzzA=new MockFeed(18,1e18);zzzB=new MockFeed(18,1e18);
        _feed(address(0),ethA,ethB);_feed(address(token),zzzA,zzzB);
        registry=new OptionalRegistry(address(access),oracle,address(token));
        registry.activationAssets().configureZZZ(address(token),address(token).codehash,keccak256("TEST ONLY IDENTITY"));
        core=new PoolManager(address(this));state=new StateView(IPoolManager(address(core)));
        OptionalPermit permit=new OptionalPermit();positions=new OptionalPositions(IPoolManager(address(core)),IAllowanceTransfer(address(permit)));
        manager=new ZZZLiquidityManager(address(access),address(positions),address(state),address(core),address(permit),
            address(new ZZZLPBalancer(address(access),address(core),address(state))));
        vault=new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        nft=new ZZZNFT(address(access),"ipfs://TEST-ONLY/"); nft.setMintEnd(uint64(block.timestamp + 3650 days));membership=new ZZZMembership(address(access));
        rewards=new ZZZRewards(address(access));fees=new ZZZFeeController(address(access));migration=new ZZZMigration(address(access));
        policy=new ZZZPortfolioPolicy(address(access));
        strategy=new ZZZStrategy(address(access),address(policy),address(new ZZZRebalanceConfirmation(address(access))));
        access.bind(Ids.VAULT,address(vault));access.bind(Ids.NFT,address(nft));access.bind(Ids.MEMBERSHIP,address(membership));
        access.bind(Ids.REWARDS,address(rewards));access.bind(Ids.FEES,address(fees));access.bind(Ids.POOLS,address(registry));
        access.bind(Ids.LIQUIDITY,address(manager));access.bind(Ids.STRATEGY,address(strategy));access.bind(Ids.MIGRATION,address(migration));
        access.bind(Ids.BUYBACK,address(new ZZZBuyback(address(access),address(token),10000e18)));
        access.setKeeper(address(this),true);rewards.addAsset(address(token));
        migration.configureZZZ(address(token),address(token).codehash,keccak256("TEST ONLY EXIT IDENTITY"));
        vrf=new MockVRF();ProtocolPolicyFixture.randomness(address(nft.access()),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        CanonicalFixture.bind(address(access));access.seal();
        key=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),10020,200,IHooks(address(0)));
        pool=keccak256(abi.encode(PoolKey(address(0),address(token),10020,200,address(0))));
        core.initialize(key,Q96);core.setProtocolFeeController(address(this));core.setProtocolFee(key,uint24(1000|(1000<<12)));
        strategy.setRangeOrientation(pool,1);strategy.rebalanceConfirmation().configure(600,300,keccak256("TEST ONLY CADENCE"));
        bytes32[] memory venues=new bytes32[](1);venues[0]=pool;
        manager.balancingRouter().configureExecutionPools(venues,keccak256("TEST ONLY EXECUTION DEPTH"));
        token.mint(address(this),10_000_000 ether);token.mint(ALICE,100_000 ether);token.mint(BOB,100_000 ether);
        core.unlock(abi.encode(uint8(0),Q96));
    }
    function _feed(address asset,MockFeed a,MockFeed b)private{
        oracle.setDualFeed(asset,
            ZZZOracle.SourcePolicy(address(a),address(a).codehash,keccak256(abi.encode(asset,uint256(1))),1 days,18),
            ZZZOracle.SourcePolicy(address(b),address(b).codehash,keccak256(abi.encode(asset,uint256(2))),1 days,18),
            300,keccak256("TEST ONLY CORRELATED PRICES"));
    }
    function _prices()private{
        (uint160 q,,,)=state.getSlot0(PoolId.wrap(pool));
        uint256 usd=(uint256(1e18)*Q96/q)*Q96/q;
        ethA.set(1e18,block.timestamp,block.timestamp);ethB.set(1e18,block.timestamp,block.timestamp);
        zzzA.set(int256(usd),block.timestamp,block.timestamp);zzzB.set(int256(usd),block.timestamp,block.timestamp);
    }
    function _finishRoyaltyWindow()private{
        ZZZRoyaltyRewards ledger=nft.royaltyRewards();
        if(!ledger.royaltiesOpen()){
            nft.setMintEnd(uint64(block.timestamp+1));vm.warp(block.timestamp+3601);
            _prices();ledger.syncAll();
        }
        assertTrue(ledger.royaltiesOpen(),"royalty window must actually open");
    }
    function unlockCallback(bytes calldata data)external returns(bytes memory){
        require(msg.sender==address(core));(uint8 mode,uint160 q)=abi.decode(data,(uint8,uint160));BalanceDelta delta;
        if(mode==0 || mode==3)(delta,)=core.modifyLiquidity(mode==0?key:targetKey,ModifyLiquidityParams(-60000,60000,int256(1_000_000 ether),bytes32(0)),"");
        else if(mode==2)delta=core.donate(key,10 ether,10 ether,"");
        // TEST ONLY: the external seed provider removes its OWN position. The
        // Vault's physical main, idle and permissions are not modified here.
        else if(mode==4)(delta,)=core.modifyLiquidity(key,ModifyLiquidityParams(-60000,60000,-int256(999_999 ether),bytes32(0)),"");
        else { (uint160 current,,,)=state.getSlot0(PoolId.wrap(pool));delta=core.swap(key,SwapParams(q<current,-int256(1_000_000 ether),q),""); }
        _settle(address(0),delta.amount0());_settle(address(token),delta.amount1());return "";
    }
    function _settle(address asset,int128 delta)private{
        if(delta>0){core.take(Currency.wrap(asset),address(this),uint256(int256(delta)));return;}
        if(delta==0)return;uint256 amount=uint256(-int256(delta));core.sync(Currency.wrap(asset));
        if(asset==address(0))assertEq(core.settle{value:amount}(),amount);
        else{token.transfer(address(core),amount);assertEq(core.settle(),amount);}
    }
    function _move(uint160 q)private{core.unlock(abi.encode(uint8(1),q));_prices();}
    function _mint(address owner)private returns(uint256 id){
        bytes32 reviewed=vault.mintPolicyFingerprint();
        vm.prank(owner);id=vault.mintDormant{value:0.05 ether}(reviewed);vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
    }
    function _contribute(address owner,uint256 id,uint256 value,bool grow)private{
        int24 lower;int24 upper;uint256 bucket=vault.nftBucket(id);
        if(grow)(lower,upper)=manager.ticks(vault.group(bucket).lpTokenId);else(lower,upper,)=strategy.target(pool);
        uint160 q=manager.spot(pool);
        uint256 u0=SqrtPriceMath.getAmount0Delta(q,TickMath.getSqrtPriceAtTick(upper),1e18,false);
        uint256 u1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),q,1e18,false);
        uint256 e=value*u0/(u0+u1);uint256 z=value-e;
        vm.startPrank(owner);token.approve(address(vault),z);
        if(grow)vault.increase{value:e}(id,e,z,1,block.timestamp+100);
        else vault.activate{value:e}(id,pool,e,z,1,block.timestamp+100);vm.stopPrank();
    }
    function _hybrid()private returns(uint256 id,uint256 bucket,uint256 main,uint256 aux){
        policy.setMode(pool,true,keccak256("TEST ONLY HYBRID MODE"));id=_mint(ALICE);_contribute(ALICE,id,1000 ether,false);
        bucket=vault.nftBucket(id);uint64 last=vault.group(bucket).lastRebalance;
        // Raw sqrt falls when ZZZ-in-ETH rises. Main remains active at this price.
        _move(uint160(uint256(Q96)*83/100));vm.warp(last+43200-600);_prices();
        for(uint256 i;i<3;++i){strategy.rebalanceConfirmation().observe(bucket);vm.warp(block.timestamp+(i==2?120:240));_prices();}
        // First600seconds were observed during cooldown; final sample has <=300gap.
        assertTrue(strategy.rebalanceConfirmation().observe(bucket));
        vault.rebalance(bucket,1,block.timestamp+100);main=vault.group(bucket).lpTokenId;aux=manager.secondaryId(main);
        assertGt(aux,0);
    }
    function testSingleModeActivationUsesOneVaultOwnedLPAndExactOperatorApproval()public{
        uint256 id=_mint(ALICE);_contribute(ALICE,id,1000 ether,false);uint256 main=vault.group(vault.nftBucket(id)).lpTokenId;
        assertEq(manager.secondaryId(main),0);assertEq(positions.ownerOf(main),address(vault));
        assertEq(positions.getApproved(main),manager.positionOperator());assertEq(token.allowance(address(vault),manager.positionOperator()),0);
        assertEq(address(manager).balance,0);assertEq(manager.positionOperator().balance,0);
    }
    function testOrdinarySingleNarrowReplacementRejectsInactiveTargetAndKeepsOldLP()public{
        // Both before/after policies satisfy production parameter bounds. The
        // wider allowed raw spot deviation still exceeds the rounded inverse
        // price lower edge: validatePrice alone cannot prove active placement.
        registry.setRange(200);registry.setSpotDeviation(99);
        uint256 id=_mint(ALICE);_contribute(ALICE,id,1000 ether,false);
        uint256 bucket=vault.nftBucket(id);Position memory beforePosition=vault.group(bucket);
        uint128 originalL=positions.getPositionLiquidity(beforePosition.lpTokenId);
        _move(TickMath.getSqrtPriceAtTick(-407));
        vm.warp(uint256(beforePosition.lastRebalance)+43200);
        ethA.set(1e18,block.timestamp,block.timestamp);ethB.set(1e18,block.timestamp,block.timestamp);
        zzzA.set(1e18,block.timestamp,block.timestamp);zzzB.set(1e18,block.timestamp,block.timestamp);
        registry.setRange(400);registry.setSpotDeviation(399);
        {
            (int24 lower,int24 upper,)=strategy.target(pool);assertEq(lower,-400);assertEq(upper,600);
            assertEq(strategy.validatePrice(pool),TickMath.getSqrtPriceAtTick(-407));
            assertTrue(strategy.rangeUpdatePending(bucket));assertTrue(strategy.rebalanceReady(bucket));
            (uint256 principal0,uint256 principal1)=manager.amounts(beforePosition.lpTokenId);
            assertGt(principal0,0);assertEq(principal1,0);assertFalse(policy.enabled(pool));
            ZZZLPBalancer router=manager.balancingRouter();
            vm.prank(address(manager));ZZZLPBalancer.Plan memory plan=router.plan(pool,lower,upper,principal0,0);
            assertEq(plan.amountIn,0);assertLt(plan.targetSqrtAfter,TickMath.getSqrtPriceAtTick(lower));
        }
        uint256 next=positions.nextTokenId();uint256 beforeShares=vault.sharesOf(id);
        // Ordinary planning now rejects the inactive destination before mint.
        // The actual call still unwinds atomically and must restore old backing.
        vm.expectCall(address(manager.balancingRouter()),abi.encodePacked(ZZZLPBalancer.planReplacement.selector));
        vm.expectRevert(ZZZModule.Slippage.selector);vault.rebalance(bucket,1,block.timestamp+100);
        assertEq(vault.group(bucket).lpTokenId,beforePosition.lpTokenId);
        assertEq(positions.getPositionLiquidity(beforePosition.lpTokenId),originalL);
        assertEq(vault.sharesOf(id),beforeShares);assertEq(positions.nextTokenId(),next);
        assertEq(manager.activeSecondaryCount(),0);
    }
    function testInitialAndGrowthOutsideRangeRemainAllowedAndDoNotRecenter()public{
        registry.setRange(400);registry.setSpotDeviation(399);
        _move(TickMath.getSqrtPriceAtTick(-407));
        ethA.set(1e18,block.timestamp,block.timestamp);ethB.set(1e18,block.timestamp,block.timestamp);
        zzzA.set(1e18,block.timestamp,block.timestamp);zzzB.set(1e18,block.timestamp,block.timestamp);
        policy.setMode(pool,true,keccak256("TEST ONLY ENABLED BUT INITIAL NOT HYBRID"));
        uint256 id=_mint(ALICE);
        vm.prank(ALICE);vault.activate{value:1000 ether}(id,pool,1000 ether,0,1,block.timestamp+100);
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        (int24 lower,int24 upper)=manager.ticks(p.lpTokenId);assertEq(lower,-400);assertEq(upper,600);
        assertLt(manager.spot(pool),TickMath.getSqrtPriceAtTick(lower));assertEq(manager.secondaryId(p.lpTokenId),0);
        uint128 oldL=positions.getPositionLiquidity(p.lpTokenId);uint256 oldShares=vault.sharesOf(id);
        // This fixture pool has a stronger $100 pool minimum in addition to
        // the protocol's $5 growth minimum. Keep both production guards.
        vm.prank(ALICE);vault.increase{value:100 ether}(id,100 ether,0,1,block.timestamp+100);
        assertGt(positions.getPositionLiquidity(p.lpTokenId),oldL);assertGt(vault.sharesOf(id),oldShares);
        assertEq(vault.group(bucket).lpTokenId,p.lpTokenId);assertEq(vault.group(bucket).centerX96,p.centerX96);
        assertEq(vault.group(bucket).lastRebalance,p.lastRebalance);assertEq(manager.secondaryId(p.lpTokenId),0);
    }
    function testAlreadySufficientSixtyPercentMainDoesNotRequireAnySwapVenue()public{
        bytes32[] memory empty=new bytes32[](0);manager.balancingRouter().configureExecutionPools(empty,keccak256("TEST NO VENUES"));
        (int24 lower,int24 upper,)=strategy.target(pool);uint160 q=manager.spot(pool);
        uint256 u0=SqrtPriceMath.getAmount0Delta(q,TickMath.getSqrtPriceAtTick(upper),1e18,false);
        uint256 u1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),q,1e18,false);
        uint256 total=1000 ether;uint256 scarce=total*60005*u1/(100000*(u0+u1));
        uint256[4] memory marks=[uint256(1 ether),1 ether,1 ether,1 ether];
        ZZZLPBalancer router=manager.balancingRouter();
        vm.prank(address(manager));ZZZLPBalancer.Plan memory p=router.planReplacement(pool,lower,upper,total-scarce,scarce,6000,marks);
        assertEq(p.amountIn,0);assertEq(p.poolId,bytes32(0));
    }
    function testActualCoreHybridAtInsideRangeTriggerProvesBothLegsAndSixtyPercentFloor()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        assertEq(positions.ownerOf(main),address(vault));assertEq(positions.ownerOf(aux),address(vault));
        assertEq(positions.getApproved(aux),manager.positionOperator());assertEq(manager.activeSecondaryCount(),1);
        (uint256 e,uint256 z)=manager.portfolioAmounts(main);(uint256 me,uint256 mz)=manager.amounts(main);
        (uint256 ae,uint256 az)=manager.amounts(aux);assertEq(e,me+ae);assertEq(z,mz+az);
        Position memory p=vault.group(bucket);uint256 total=oracle.value(address(0),e+p.idle0)+oracle.value(address(token),z+p.idle1);
        assertGe(oracle.value(address(0),me)+oracle.value(address(token),mz),total*6000/10000);
        assertLe(oracle.value(address(0),ae)+oracle.value(address(token),az),total*4000/10000);
        assertTrue(ae==0 || az==0);assertEq(address(manager).balance,0);assertEq(manager.positionOperator().balance,0);
    }
    function testGovernedEightyPercentMainAndLargerGapExecuteThenGrowthPreservesResidual()public{
        policy.configureMainAllocation(pool,8000,keccak256("TEST ONLY GOVERNED80/20"));
        policy.configureResidualGap(pool,3,keccak256("TEST ONLY THREE SPACINGS"));
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        Position memory p=vault.group(bucket);
        {
        (uint256 me,uint256 mz)=manager.amounts(main);(uint256 ae,uint256 az)=manager.amounts(aux);
        uint256 mainValue=oracle.value(address(0),me)+oracle.value(address(token),mz);
        uint256 residualValue=oracle.value(address(0),ae)+oracle.value(address(token),az);
        uint256 retained=mainValue+residualValue+oracle.value(address(0),p.idle0)+oracle.value(address(token),p.idle1);
        assertGe(mainValue*10000,retained*8000);assertLe(residualValue*10000,retained*2000);
        (int24 lower,int24 upper)=manager.ticks(main);(int24 auxLower,int24 auxUpper)=manager.ticks(aux);
        int24 current=TickMath.getTickAtSqrtPrice(manager.spot(pool));
        assertGe(current,lower);assertLt(current,upper);assertGe(auxLower,lower);assertLe(auxUpper,upper);
        if(ae!=0){assertEq(az,0);assertGe(auxLower-current,600);}
        else{assertGt(az,0);assertGe(current-auxUpper,600);}
        }
        uint128 mainL=positions.getPositionLiquidity(main);uint128 auxiliaryL=positions.getPositionLiquidity(aux);
        uint256 shares=vault.sharesOf(id);uint64 geometry=policy.geometryRevision(pool);
        _contribute(ALICE,id,100 ether,true);
        assertGt(positions.getPositionLiquidity(main),mainL);assertEq(positions.getPositionLiquidity(aux),auxiliaryL);
        assertGt(vault.sharesOf(id),shares);assertEq(manager.secondaryId(main),aux);
        assertEq(vault.group(bucket).lastRebalance,p.lastRebalance);assertEq(vault.group(bucket).centerX96,p.centerX96);
        assertEq(policy.minimumMainBps(pool),8000);assertEq(policy.geometryRevision(pool),geometry);
        assertEq(manager.activeSecondaryCount(),1);assertEq(positions.ownerOf(aux),address(vault));
    }
    function testSecondMintFailureRollsBackOldPrincipalFeesAndCustody()public{
        policy.setMode(pool,true,keccak256("TEST HYBRID"));uint256 id=_mint(ALICE);_contribute(ALICE,id,1000 ether,false);
        uint256 bucket=vault.nftBucket(id);uint256 old=vault.group(bucket).lpTokenId;uint128 oldL=positions.getPositionLiquidity(old);
        uint256 shares=vault.sharesOf(id);_move(uint160(uint256(Q96)*83/100));vm.warp(block.timestamp+43200);_prices();
        for(uint256 i;i<3;++i){strategy.rebalanceConfirmation().observe(bucket);vm.warp(block.timestamp+240);_prices();}
        strategy.rebalanceConfirmation().observe(bucket);uint256 next=positions.nextTokenId();positions.failAt(next+1,0);
        vm.expectRevert();vault.rebalance(bucket,1,block.timestamp+100);
        assertEq(vault.group(bucket).lpTokenId,old);assertEq(positions.getPositionLiquidity(old),oldL);
        assertEq(vault.sharesOf(id),shares);assertEq(manager.activeSecondaryCount(),0);assertEq(positions.nextTokenId(),next);
    }
    function testGrowingMainPreservesAuxiliaryAndClocks()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        uint128 beforeMain=positions.getPositionLiquidity(main);uint128 beforeAux=positions.getPositionLiquidity(aux);
        Position memory beforePosition=vault.group(bucket);bytes32 identity=manager.portfolioFingerprint(main);
        _contribute(ALICE,id,100 ether,true);
        assertGt(positions.getPositionLiquidity(main),beforeMain);assertEq(positions.getPositionLiquidity(aux),beforeAux);
        assertEq(manager.portfolioFingerprint(main),identity);assertEq(vault.group(bucket).lastRebalance,beforePosition.lastRebalance);
        assertEq(vault.group(bucket).centerX96,beforePosition.centerX96);
    }
    function testNewEntrantBuysAggregateNAVWithoutOldRewardsOrResidualMutation()public{
        (uint256 aliceId,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        uint256 oldClaim=rewards.claimable(aliceId,address(0));assertGt(oldClaim,0);
        uint128 oldAux=positions.getPositionLiquidity(aux);uint64 clock=vault.group(bucket).lastRebalance;
        uint256 bobId=_mint(BOB);_contribute(BOB,bobId,1000 ether,false);
        assertEq(vault.nftBucket(bobId),bucket);assertEq(vault.group(bucket).lpTokenId,main);
        assertEq(manager.secondaryId(main),aux);assertEq(positions.getPositionLiquidity(aux),oldAux);
        assertEq(vault.group(bucket).lastRebalance,clock);assertGt(vault.sharesOf(bobId),0);
        assertEq(rewards.claimable(bobId,address(0)),0);assertEq(rewards.claimable(bobId,address(token)),0);
        assertGe(rewards.claimable(aliceId,address(0)),oldClaim);
    }
    function testPreviouslyEarnedHybridRightsFollowNFTTransfer()public{
        (uint256 id,uint256 bucket,,)=_hybrid();vault.collectFees(bucket,block.timestamp+100);
        uint256 expected=rewards.claimable(id,address(0));assertGt(expected,0);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,id);
        vm.prank(ALICE);vm.expectRevert();rewards.claim(id,address(0));
        uint256 beforeETH=BOB.balance;vm.prank(BOB);rewards.claim(id,address(0));assertEq(BOB.balance-beforeETH,expected);
    }
    function testDisabledModePreservesBothUntilGuardedAtomicMerge()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();policy.setMode(pool,false,keccak256("TEST DESIRED SINGLE"));
        assertEq(manager.secondaryId(main),aux);assertTrue(policy.configurationPending(bucket));
        vm.expectRevert();vault.rebalance(bucket,1,block.timestamp+100);
        vm.warp(block.timestamp+43200);_prices();vault.rebalance(bucket,1,block.timestamp+100);
        uint256 replacement=vault.group(bucket).lpTokenId;assertTrue(replacement!=main);
        assertEq(manager.activeSecondaryCount(),0);assertEq(manager.secondaryId(replacement),0);
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
    }
    function testManualSingleModeJourneyMergesUnpausedThenHarvestsAndClaimsNewFees()public{
        (uint256 id,uint256 bucket,uint256 oldMain,uint256 oldAux)=_hybrid();
        uint256 shares=vault.sharesOf(id);uint256 total=vault.bucketTotalShares(bucket);
        policy.setMode(pool,false,keccak256("TEST ONLY NORMAL UNPAUSED MANUAL JOURNEY"));
        assertFalse(access.paused());assertEq(manager.secondaryId(oldMain),oldAux);
        vm.warp(block.timestamp+43200);_prices();
        assertTrue(strategy.rebalanceReady(bucket));vault.rebalance(bucket,1,block.timestamp+100);
        uint256 main=vault.group(bucket).lpTokenId;
        assertFalse(access.paused());assertFalse(policy.enabled(pool));
        assertFalse(policy.configurationPending(bucket));assertEq(manager.secondaryId(main),0);
        assertEq(manager.activeSecondaryCount(),0);assertEq(vault.sharesOf(id),shares);
        assertEq(vault.bucketTotalShares(bucket),total);assertEq(nft.ownerOf(id),ALICE);
        vm.expectRevert();positions.ownerOf(oldMain);vm.expectRevert();positions.ownerOf(oldAux);
        {
            (int24 lower,int24 upper)=manager.ticks(main);
            (,int24 tick,,)=state.getSlot0(PoolId.wrap(pool));
            assertGe(tick,lower);assertLt(tick,upper);assertEq(positions.ownerOf(main),address(vault));
        }
        uint128 liquidity=positions.getPositionLiquidity(main);
        uint256 previous=rewards.claimable(id,address(0));
        // Actual local v4 fee-growth donation, not a direct PoPL ledger credit.
        // This exercises post-merge collection/accounting, not market volume.
        core.unlock(abi.encode(uint8(2),Q96));vault.collectFees(bucket,block.timestamp+100);
        uint256 expected=rewards.claimable(id,address(0));assertGt(expected,previous);
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(positions.getPositionLiquidity(main),liquidity);
        uint256 balanceBefore=ALICE.balance;vm.prank(ALICE);
        assertEq(rewards.claim(id,address(0)),expected);assertEq(ALICE.balance-balanceBefore,expected);
        vm.prank(ALICE);assertEq(rewards.claim(id,address(0)),0);
        assertEq(rewards.claimable(id,address(0)),0);assertEq(vault.sharesOf(id),shares);
    }
    function testAuxiliaryBurnFailureRollsBackWholeMerge()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();uint128 beforeMain=positions.getPositionLiquidity(main);
        uint128 beforeAux=positions.getPositionLiquidity(aux);policy.setMode(pool,false,keccak256("TEST SINGLE"));
        vm.warp(block.timestamp+43200);_prices();positions.failAt(0,aux);
        vm.expectRevert();vault.rebalance(bucket,1,block.timestamp+100);
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(manager.secondaryId(main),aux);
        assertEq(positions.getPositionLiquidity(main),beforeMain);assertEq(positions.getPositionLiquidity(aux),beforeAux);
        assertEq(manager.activeSecondaryCount(),1);
    }
    function testBothLegsHarvestWithoutReplacingEitherPosition()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        // Reverse enough to enter the ETH residual without crossing the main boundary.
        _move(uint160(uint256(Q96)*88/100));core.unlock(abi.encode(uint8(2),Q96));
        uint128 lm=positions.getPositionLiquidity(main);uint128 la=positions.getPositionLiquidity(aux);
        vault.collectFees(bucket,block.timestamp+100);
        for(uint256 j;j<2;++j){
            uint256 lp=j==0?main:aux;(int24 l,int24 u)=manager.ticks(lp);
            (,uint256 f0,uint256 f1)=state.getPositionInfo(PoolId.wrap(pool),address(positions),l,u,bytes32(lp));
            (uint256 current0,uint256 current1)=state.getFeeGrowthInside(PoolId.wrap(pool),l,u);
            assertEq(f0,current0);assertEq(f1,current1);
        }
        assertEq(positions.getPositionLiquidity(main),lm);assertEq(positions.getPositionLiquidity(aux),la);
        uint256 beforeETH=ALICE.balance;vm.prank(ALICE);rewards.claim(id,address(0));assertGt(ALICE.balance,beforeETH);
        uint256 paid=ALICE.balance;vm.prank(ALICE);rewards.claim(id,address(0));assertEq(ALICE.balance,paid);
    }
    function testCollectiveExitClosesBothAndDirectlyPaysHolderKeepingRoyalties()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();_finishRoyaltyWindow();access.setPaused(true);
        migration.beginCollectiveExit(keccak256("TEST ONLY HOLDER RETURN"));migration.closeBucket(bucket,0,0,block.timestamp+100);
        assertEq(manager.activeSecondaryCount(),0);vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
        migration.allocatePrincipal(32);uint256 beforeETH=ALICE.balance;uint256 beforeZZZ=token.balanceOf(ALICE);
        uint256[] memory ids=new uint256[](1);ids[0]=id;migration.distributePrincipal(ids);
        assertGt(ALICE.balance,beforeETH);assertGt(token.balanceOf(ALICE),beforeZZZ);
        assertEq(nft.ownerOf(id),ALICE);assertEq(uint256(vault.nftStatus(id)),uint256(PositionStatus.Exited));
        ZZZRoyaltyRewards royalty=nft.royaltyRewards();(bool ok,)=payable(address(royalty)).call{value:1 ether}("");assertTrue(ok);
        beforeETH=ALICE.balance;vm.prank(ALICE);royalty.claim(id,address(0));assertGt(ALICE.balance,beforeETH);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,id);assertEq(nft.ownerOf(id),BOB);
    }
    function testSamePairMoveClosesBothAndKeepsNFTSharesAtNewPool()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        uint256 shares=vault.sharesOf(id);uint256 total=vault.bucketTotalShares(bucket);
        bytes32 destination=registry.admitTarget();
        targetKey=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),3000,200,IHooks(address(0)));
        core.initialize(targetKey,manager.spot(pool));core.unlock(abi.encode(uint8(3),Q96));
        migration.moveFunds(bucket,destination,1,block.timestamp+100);
        assertEq(vault.group(bucket).poolId,destination);assertEq(vault.sharesOf(id),shares);
        assertEq(vault.bucketTotalShares(bucket),total);assertEq(vault.nftBucket(id),bucket);
        assertEq(manager.activeSecondaryCount(),0);vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
        assertEq(positions.ownerOf(vault.group(bucket).lpTokenId),address(vault));
    }
    function testPausedParkingClosesBothWithoutOracleAndPreservesAttributedAssets()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();Position memory p=vault.group(bucket);
        ZZZMigration.ParkingRequest memory request=ZZZMigration.ParkingRequest(bucket,p.poolId,main,
            vault.bucketTotalShares(bucket),p.depositUSD,migration.custodyEpoch(bucket),migration.parkingNonce(bucket),
            address(0),address(token),1,1,block.timestamp+100,keccak256("TEST RAW PARK"),manager.executionPortfolioFingerprint(main));
        zzzA.set(0,block.timestamp,block.timestamp);zzzB.set(0,block.timestamp,block.timestamp);access.setPaused(true);
        migration.park(request);p=vault.group(bucket);assertEq(uint256(p.status),uint256(PositionStatus.Parked));
        assertEq(p.lpTokenId,0);assertGt(p.idle0,0);assertGt(p.idle1,0);assertEq(manager.activeSecondaryCount(),0);
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
    }
    function testNewExecutorDoesNotAddHolderOrGovernanceWithdrawalAuthority()public{
        uint256 id=_mint(ALICE);_contribute(ALICE,id,1000 ether,false);uint256 main=vault.group(vault.nftBucket(id)).lpTokenId;
        ZZZLPPositionExecutor executor=ZZZLPPositionExecutor(payable(manager.positionOperator()));
        vm.prank(ALICE);vm.expectRevert();executor.close(pool,main,block.timestamp+100);
        vm.prank(address(vault));vm.expectRevert();executor.close(pool,main,block.timestamp+100);
        vm.expectRevert();manager.close(pool,main,block.timestamp+100);
        vm.expectRevert();policy.recordApplied(main,pool);
        assertEq(positions.ownerOf(main),address(vault));assertGt(positions.getPositionLiquidity(main),0);
    }

    function _residualReview(uint256 bucket)private view returns(ZZZMigration.ParkingRequest memory r){
        Position memory p=vault.group(bucket);uint256 aux=manager.secondaryId(p.lpTokenId);
        uint256 a0;uint256 a1;if(aux!=0)(a0,a1)=manager.amounts(aux);
        r.bucketId=bucket;r.poolId=p.poolId;r.lpTokenId=p.lpTokenId;r.totalShares=vault.bucketTotalShares(bucket);
        r.depositUSD=p.depositUSD;r.custodyEpoch=migration.custodyEpoch(bucket);r.nonce=migration.parkingNonce(bucket);
        r.token0=address(0);r.token1=address(token);r.minimum0=uint128(a0!=0||a1==0?1:0);r.minimum1=uint128(a1!=0?1:0);
        r.deadline=block.timestamp+100;r.reviewHash=keccak256("TEST ONLY RAW RESIDUAL CLOSE");
        r.portfolioHash=manager.executionPortfolioFingerprint(p.lpTokenId);
    }
    function _residualSnapshot(uint256 id,uint256 bucket,uint256 main,uint256 aux)private view returns(ResidualSnapshot memory s){
        s.position=vault.group(bucket);s.mainL=positions.getPositionLiquidity(main);s.auxL=positions.getPositionLiquidity(aux);
        s.shares=vault.sharesOf(id);s.total=vault.bucketTotalShares(bucket);s.fingerprint=manager.portfolioFingerprint(main);
        s.claims=[rewards.claimable(id,address(0)),rewards.claimable(id,address(token))];
        s.compound=[fees.compoundBalance(bucket,address(0)),fees.compoundBalance(bucket,address(token))];
        s.buyback=[fees.buybackBalance(address(0)),fees.buybackBalance(address(token))];
        (s.principal[0],s.principal[1])=manager.amounts(aux);
        s.operatorETH=address(this).balance;s.operatorZZZ=token.balanceOf(address(this));
    }
    function _assertSameMain(Position memory beforePosition,uint256 bucket,uint128 liquidity)private view{
        Position memory afterPosition=vault.group(bucket);
        assertEq(afterPosition.poolId,beforePosition.poolId);assertEq(afterPosition.lpTokenId,beforePosition.lpTokenId);
        assertEq(afterPosition.depositUSD,beforePosition.depositUSD);assertEq(afterPosition.centerX96,beforePosition.centerX96);
        assertEq(afterPosition.lastRebalance,beforePosition.lastRebalance);assertEq(uint256(afterPosition.status),uint256(beforePosition.status));
        assertEq(positions.ownerOf(afterPosition.lpTokenId),address(vault));assertEq(positions.getPositionLiquidity(afterPosition.lpTokenId),liquidity);
    }
    function testResidualCloseReturnsExactPrincipalToSameBucketWithoutChangingMainOrRights()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();core.unlock(abi.encode(uint8(2),Q96));
        ResidualSnapshot memory s=_residualSnapshot(id,bucket,main,aux);ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);migration.closeResidual(request);
        _assertSameMain(s.position,bucket,s.mainL);Position memory afterPosition=vault.group(bucket);
        assertEq(afterPosition.idle0-s.position.idle0,s.principal[0]);assertEq(afterPosition.idle1-s.position.idle1,s.principal[1]);
        assertEq(vault.totalIdle(address(0)),afterPosition.idle0);assertEq(vault.totalIdle(address(token)),afterPosition.idle1);
        assertEq(manager.secondaryId(main),0);assertEq(manager.activeSecondaryCount(),0);
        assertTrue(manager.portfolioFingerprint(main)!=s.fingerprint);vm.expectRevert();positions.ownerOf(aux);
        assertEq(vault.sharesOf(id),s.shares);assertEq(vault.bucketTotalShares(bucket),s.total);
        assertGe(rewards.claimable(id,address(0)),s.claims[0]);assertGe(rewards.claimable(id,address(token)),s.claims[1]);
        assertGe(fees.compoundBalance(bucket,address(0)),s.compound[0]);assertGe(fees.compoundBalance(bucket,address(token)),s.compound[1]);
        assertGe(fees.buybackBalance(address(0)),s.buyback[0]);assertGe(fees.buybackBalance(address(token)),s.buyback[1]);assertTrue(policy.enabled(pool));
        assertEq(address(this).balance,s.operatorETH);assertEq(token.balanceOf(address(this)),s.operatorZZZ);
        assertEq(migration.parkingNonce(bucket),request.nonce+1);assertEq(migration.custodyEpoch(bucket),request.custodyEpoch+1);
    }
    function testResidualCloseAcceptsMixedInventoryWithBrokenUSDAndDisabledOperations()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        (int24 lower,int24 upper)=manager.ticks(aux);_move(TickMath.getSqrtPriceAtTick((lower+upper)/2));
        (uint256 a0,uint256 a1)=manager.amounts(aux);assertGt(a0,0);assertGt(a1,0);
        Position memory beforePosition=vault.group(bucket);uint128 beforeL=positions.getPositionLiquidity(main);
        ZZZMigration.ParkingRequest memory request=_residualReview(bucket);registry.setOperations(false);
        ethA.set(0,block.timestamp,block.timestamp);ethB.set(0,block.timestamp,block.timestamp);
        zzzA.set(0,block.timestamp,block.timestamp);zzzB.set(0,block.timestamp,block.timestamp);access.setPaused(true);
        migration.closeResidual(request);_assertSameMain(beforePosition,bucket,beforeL);
        assertEq(vault.group(bucket).idle0-beforePosition.idle0,a0);assertEq(vault.group(bucket).idle1-beforePosition.idle1,a1);
        assertEq(manager.secondaryId(main),0);
    }
    function testResidualCloseMinimumFailureRollsBackBurnAndFeeCheckpoint()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();core.unlock(abi.encode(uint8(2),Q96));
        ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        (uint256 a0,)=manager.amounts(aux);if(a0!=0)request.minimum0=type(uint128).max;else request.minimum1=type(uint128).max;
        ResidualSnapshot memory s=_residualSnapshot(id,bucket,main,aux);
        access.setPaused(true);vm.expectRevert();migration.closeResidual(request);
        _assertSameMain(s.position,bucket,s.mainL);assertEq(vault.group(bucket).idle0,s.position.idle0);assertEq(vault.group(bucket).idle1,s.position.idle1);
        assertEq(manager.secondaryId(main),aux);assertEq(positions.getPositionLiquidity(aux),s.auxL);
        assertEq(rewards.claimable(id,address(0)),s.claims[0]);assertEq(fees.compoundBalance(bucket,address(0)),s.compound[0]);
        assertEq(migration.parkingNonce(bucket),request.nonce);assertEq(migration.custodyEpoch(bucket),request.custodyEpoch);
    }
    function testResidualCloseBurnFailureRollsBackAssociationBalancesAndNonce()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        Position memory p=vault.group(bucket);uint128 mainL=positions.getPositionLiquidity(main);uint128 auxL=positions.getPositionLiquidity(aux);
        positions.failAt(0,aux);access.setPaused(true);vm.expectRevert();migration.closeResidual(request);
        _assertSameMain(p,bucket,mainL);assertEq(manager.secondaryId(main),aux);assertEq(manager.activeSecondaryCount(),1);
        assertEq(positions.getPositionLiquidity(aux),auxL);assertEq(vault.group(bucket).idle0,p.idle0);
        assertEq(migration.parkingNonce(bucket),request.nonce);
    }
    function testResidualCloseRejectsReplayAndNoLongerExistingResidual()public{
        (,uint256 bucket,uint256 main,)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);migration.closeResidual(request);vm.expectRevert();migration.closeResidual(request);
        request=_residualReview(bucket);vm.expectRevert();migration.closeResidual(request);assertEq(manager.secondaryId(main),0);
    }
    function testResidualCloseRejectsWrongCustodyReviewAndRawMinima()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);request.portfolioHash=bytes32(uint256(123));vm.expectRevert();migration.closeResidual(request);
        request=_residualReview(bucket);request.nonce+=1;vm.expectRevert();migration.closeResidual(request);
        request=_residualReview(bucket);request.portfolioHash=bytes32(0);vm.expectRevert();migration.closeResidual(request);
        request=_residualReview(bucket);request.reviewHash=bytes32(0);vm.expectRevert();migration.closeResidual(request);
        request=_residualReview(bucket);request.deadline=block.timestamp-1;vm.expectRevert();migration.closeResidual(request);
        assertEq(manager.secondaryId(main),aux);
    }
    function testResidualCloseRequiresGovernanceAndNoDirectModuleBypass()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);vm.prank(ALICE);vm.expectRevert();migration.closeResidual(request);
        vm.expectRevert();vault.closeResidual(bucket,request.deadline);
        vm.expectRevert();manager.closeSecondary(pool,main,request.deadline);
        ZZZLPPositionExecutor child=ZZZLPPositionExecutor(payable(manager.positionOperator()));
        vm.expectRevert();child.closeSecondary(pool,main,request.deadline);assertEq(manager.secondaryId(main),aux);
    }
    function testResidualCloseRequiresPauseAndSealedOperatingCanonicalLifecycle()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        vm.expectRevert();migration.closeResidual(request);access.setPaused(true);
        access.setPreparation(true);vm.expectRevert();migration.closeResidual(request);access.setPreparation(false);
        access.setCanonicalState(1);vm.expectRevert();migration.closeResidual(request);access.setCanonicalState(0);
        access.beginBootstrap();vm.expectRevert();migration.closeResidual(request);access.seal();
        assertEq(manager.secondaryId(main),aux);
    }
    function testResidualCloseCannotRunAfterTerminalHolderExitStarts()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);migration.beginCollectiveExit(keccak256("TEST TERMINAL EXIT"));
        vm.expectRevert();migration.closeResidual(request);assertEq(manager.secondaryId(main),aux);
    }
    function testResidualCloseKeepsDisabledModeAndPendingConfiguration()public{
        (,uint256 bucket,uint256 main,)=_hybrid();policy.setMode(pool,false,keccak256("TEST STAY SINGLE"));
        ZZZMigration.ParkingRequest memory request=_residualReview(bucket);access.setPaused(true);migration.closeResidual(request);
        assertFalse(policy.enabled(pool));assertTrue(policy.configurationPending(bucket));assertEq(manager.secondaryId(main),0);
    }
    function testResidualClosePreservesClaimAndTransferRightsWhilePaused()public{
        (uint256 id,uint256 bucket,,)=_hybrid();_finishRoyaltyWindow();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        uint256 expected=rewards.claimable(id,address(0));assertGt(expected,0);access.setPaused(true);migration.closeResidual(request);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,id);uint256 paid=BOB.balance;
        vm.prank(BOB);rewards.claim(id,address(0));assertGe(BOB.balance-paid,expected);
        vm.prank(ALICE);vm.expectRevert();rewards.claim(id,address(0));
        ZZZRoyaltyRewards royalty=nft.royaltyRewards();(bool ok,)=payable(address(royalty)).call{value:2 ether}("");assertTrue(ok);
        paid=BOB.balance;vm.prank(BOB);royalty.claim(id,address(0));assertEq(BOB.balance-paid,2 ether);
    }
    function testResidualCloseDoesNotExemptNewGrowthFromUndeployedPrincipalGuard()public{
        (uint256 id,uint256 bucket,uint256 main,)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);migration.closeResidual(request);access.setPaused(false);
        Position memory p=vault.group(bucket);uint128 mainL=positions.getPositionLiquidity(main);uint256 shares=vault.sharesOf(id);
        uint256[2] memory amounts=_reviewGrowth(main,100 ether);
        ZZZMigrationBudget budget=vault.migrationBudget();
        vm.startPrank(ALICE);token.approve(address(vault),amounts[1]);
        vm.expectCall(address(budget),abi.encodeCall(ZZZMigrationBudget.assertDeployed,(bucket)));
        vm.expectRevert(ZZZModule.Slippage.selector);
        vault.increase{value:amounts[0]}(id,amounts[0],amounts[1],1,block.timestamp+100);vm.stopPrank();
        _assertSameMain(p,bucket,mainL);assertEq(vault.sharesOf(id),shares);assertEq(vault.group(bucket).idle0,p.idle0);
    }
    function testReviewedEntryIdleHeadroomRecoversGrowthWithoutSpendingOldIdle()public{
        (uint256 id,uint256 bucket,uint256 main,)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);migration.closeResidual(request);access.setPaused(false);
        Position memory beforePosition=vault.group(bucket);uint128 beforeL=positions.getPositionLiquidity(main);
        uint256 shares=vault.sharesOf(id);uint256 oldClaim=rewards.claimable(id,address(0));
        assertGt(oracle.value(address(0),beforePosition.idle0)+oracle.value(address(token),beforePosition.idle1),0);
        ProtocolPolicyFixture.bind(address(access)).setEntryPolicy(100e18,5e18,4000,keccak256("TEST ONLY RECOVERY IDLE REVIEW"));
        _contribute(ALICE,id,100 ether,true);
        Position memory afterPosition=vault.group(bucket);
        assertGt(positions.getPositionLiquidity(main),beforeL);assertGt(vault.sharesOf(id),shares);
        assertGe(afterPosition.idle0,beforePosition.idle0);assertGe(afterPosition.idle1,beforePosition.idle1);
        assertEq(afterPosition.lpTokenId,main);assertEq(afterPosition.centerX96,beforePosition.centerX96);
        assertEq(afterPosition.lastRebalance,beforePosition.lastRebalance);assertEq(manager.secondaryId(main),0);
        assertGe(rewards.claimable(id,address(0)),oldClaim);
    }
    function _reviewGrowth(uint256 main,uint256 value)private view returns(uint256[2] memory amounts){
        (int24 lower,int24 upper)=manager.ticks(main);uint160 q=manager.spot(pool);
        uint256 u0=SqrtPriceMath.getAmount0Delta(q,TickMath.getSqrtPriceAtTick(upper),1e18,false);
        uint256 u1=SqrtPriceMath.getAmount1Delta(TickMath.getSqrtPriceAtTick(lower),q,1e18,false);
        amounts[0]=value*u0/(u0+u1);amounts[1]=value-amounts[0];
    }
    function testResidualCloseThenCollectiveExitStillReturnsAttributedPrincipal()public{
        (uint256 id,uint256 bucket,uint256 main,)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);migration.closeResidual(request);uint256 idle0=vault.group(bucket).idle0;
        migration.beginCollectiveExit(keccak256("TEST CLOSE THEN HOLDER EXIT"));migration.closeBucket(bucket,0,0,block.timestamp+100);
        migration.allocatePrincipal(32);uint256 before=ALICE.balance;uint256[] memory ids=new uint256[](1);ids[0]=id;
        migration.distributePrincipal(ids);assertGe(ALICE.balance-before,idle0);assertEq(manager.activeSecondaryCount(),0);
        vm.expectRevert();positions.ownerOf(main);assertEq(uint256(vault.nftStatus(id)),uint256(PositionStatus.Exited));
    }
    function _reviewForcedSingle(uint256 bucket)private returns(EmergencyRebalance memory request){
        vault.collectFees(bucket,block.timestamp+100);Position memory p=vault.group(bucket);
        (uint256 a0,uint256 a1)=manager.portfolioAmounts(p.lpTokenId);
        a0+=p.idle0+fees.compoundBalance(bucket,address(0));a1+=p.idle1+fees.compoundBalance(bucket,address(token));
        (int24 lower,int24 upper,)=strategy.target(pool);ZZZLPBalancer router=manager.balancingRouter();
        vm.prank(address(manager));ZZZLPBalancer.Plan memory plan=router.plan(pool,lower,upper,a0,a1);
        request.bucket=bucket;request.custodyHash=migration.emergencyCustodyHash(bucket);request.checks=14;
        request.lower=lower;request.upper=upper;request.swapPool=plan.poolId;request.zeroForOne=plan.zeroForOne;
        request.amountIn=uint128(plan.amountIn);request.minimumOut=uint128(plan.minimumOut);request.minimumLiquidity=1;
        request.deadline=block.timestamp+100;request.reviewHash=keccak256("TEST ONLY GUARDED FORCE SINGLE");
    }
    function testResidualControlForcedSingleBypassesTimingButKeepsFinancialGuardsAndModeOff()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();uint256 shares=vault.sharesOf(id);
        policy.setMode(pool,false,keccak256("TEST PERSISTENT SINGLE"));EmergencyRebalance memory request=_reviewForcedSingle(bucket);
        access.setPaused(true);migration.emergencyRebalance(request);Position memory p=vault.group(bucket);
        assertTrue(p.lpTokenId!=main);assertEq(manager.secondaryId(p.lpTokenId),0);assertEq(manager.activeSecondaryCount(),0);
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
        assertEq(vault.sharesOf(id),shares);assertFalse(policy.enabled(pool));
        (uint160 q,int24 tick,,)=state.getSlot0(PoolId.wrap(pool));(int24 lower,int24 upper)=manager.ticks(p.lpTokenId);
        assertGe(tick,lower);assertLt(tick,upper);assertGt(q,0);assertFalse(ZZZMigrationBudget(address(vault.migrationBudget())).emergencyActive());
    }
    function testResidualControlForcedSingleDoesNotSilentlyDisableFutureHybridMode()public{
        (,uint256 bucket,uint256 main,)=_hybrid();EmergencyRebalance memory request=_reviewForcedSingle(bucket);
        access.setPaused(true);migration.emergencyRebalance(request);uint256 replacement=vault.group(bucket).lpTokenId;
        assertTrue(replacement!=main);assertEq(manager.secondaryId(replacement),0);assertTrue(policy.enabled(pool));
    }
    function testResidualControlEnableIsDesiredStateThenNextGuardedAdjustmentCreatesOneResidual()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();policy.setMode(pool,false,keccak256("TEST DISABLE"));
        ZZZMigration.ParkingRequest memory request=_residualReview(bucket);access.setPaused(true);migration.closeResidual(request);
        policy.setMode(pool,true,keccak256("TEST REENABLE"));assertEq(manager.secondaryId(main),0);
        access.setPaused(false);vm.expectRevert();vault.rebalance(bucket,1,block.timestamp+100);
        vm.warp(block.timestamp+43200);_prices();vault.rebalance(bucket,1,block.timestamp+100);
        uint256 replacement=vault.group(bucket).lpTokenId;uint256 nextAux=manager.secondaryId(replacement);
        assertGt(nextAux,0);assertTrue(nextAux!=aux);assertEq(manager.activeSecondaryCount(),1);
    }
    /// @dev TEST ONLY governance callback target. The injected dependency can
    /// invoke only this fixture; each branch calls a real permitted admin action.
    function residualBurnCallback(uint8 kind)external{
        require(msg.sender==address(positions));
        if(kind==1)policy.setMode(pool,false,keccak256("TEST CALLBACK MODE CHANGE"));
        else if(kind==2)migration.invalidateParking(residualCallbackBucket);
        else if(kind==3)access.setPaused(false);
        else if(kind==4)ProtocolPolicyFixture.bind(address(access)).setMaintenancePolicy(1000,keccak256("TEST CALLBACK IDLE WIDENING"));
        else revert();
    }
    function testMidReplacementMaintenancePolicyChangeRevertsBothLegsAndAllBacking()public{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        policy.configureResidualGap(pool,2,keccak256("TEST ONLY EXPLICIT NEXT GEOMETRY"));
        vm.warp(uint256(vault.group(bucket).lastRebalance)+43200);_prices();
        ResidualSnapshot memory s=_residualSnapshot(id,bucket,main,aux);
        bytes32 beforePolicy=ProtocolPolicyFixture.bind(address(access)).maintenanceFingerprint();
        positions.configureBurnCallback(address(this),aux,4);
        vm.expectCall(address(this),abi.encodeCall(this.residualBurnCallback,(uint8(4))));
        vm.expectRevert();vault.rebalance(bucket,1,block.timestamp+100);
        assertEq(ProtocolPolicyFixture.bind(address(access)).maintenanceFingerprint(),beforePolicy);
        _assertSameMain(s.position,bucket,s.mainL);assertEq(manager.secondaryId(main),aux);
        assertEq(positions.ownerOf(aux),address(vault));assertEq(positions.getPositionLiquidity(aux),s.auxL);
        assertEq(vault.sharesOf(id),s.shares);assertEq(vault.bucketTotalShares(bucket),s.total);
        assertEq(vault.group(bucket).idle0,s.position.idle0);assertEq(vault.group(bucket).idle1,s.position.idle1);
        assertEq(fees.compoundBalance(bucket,address(0)),s.compound[0]);assertEq(fees.compoundBalance(bucket,address(token)),s.compound[1]);
        assertEq(fees.buybackBalance(address(0)),s.buyback[0]);assertEq(fees.buybackBalance(address(token)),s.buyback[1]);
        assertEq(rewards.claimable(id,address(0)),s.claims[0]);assertEq(rewards.claimable(id,address(token)),s.claims[1]);
    }
    function _assertResidualCallbackRollback(uint8 kind)private{
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();core.unlock(abi.encode(uint8(2),Q96));
        ResidualSnapshot memory s=_residualSnapshot(id,bucket,main,aux);ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        uint64 geometry=policy.geometryRevision(pool);uint64 revision=policy.revision();
        residualCallbackBucket=bucket;positions.configureBurnCallback(address(this),aux,kind);access.setPaused(true);
        vm.expectCall(address(this),abi.encodeCall(this.residualBurnCallback,(kind)));
        // Policy/nonce changes fail Migration's final frozen-context check;
        // unpause fails the typed executor's completion pause check first.
        vm.expectRevert(kind==3?ZZZModule.InvalidState.selector:ZZZModule.Slippage.selector);
        migration.closeResidual(request);
        _assertSameMain(s.position,bucket,s.mainL);assertEq(positions.ownerOf(aux),address(vault));
        assertEq(positions.getPositionLiquidity(aux),s.auxL);assertEq(manager.secondaryId(main),aux);
        assertEq(manager.activeSecondaryCount(),1);assertEq(vault.group(bucket).idle0,s.position.idle0);
        assertEq(vault.group(bucket).idle1,s.position.idle1);assertEq(vault.sharesOf(id),s.shares);
        assertEq(vault.bucketTotalShares(bucket),s.total);assertEq(migration.parkingNonce(bucket),request.nonce);
        assertEq(migration.custodyEpoch(bucket),request.custodyEpoch);assertEq(policy.geometryRevision(pool),geometry);
        assertEq(policy.revision(),revision);assertTrue(policy.enabled(pool));assertTrue(access.paused());
        assertEq(rewards.claimable(id,address(0)),s.claims[0]);assertEq(rewards.claimable(id,address(token)),s.claims[1]);
        assertEq(fees.compoundBalance(bucket,address(0)),s.compound[0]);assertEq(fees.compoundBalance(bucket,address(token)),s.compound[1]);
        assertEq(fees.buybackBalance(address(0)),s.buyback[0]);assertEq(fees.buybackBalance(address(token)),s.buyback[1]);
    }
    function testResidualCallbackModeChangeRollsBackBurnFeesAndPrincipal()public{_assertResidualCallbackRollback(1);}
    function testResidualCallbackNonceChangeRollsBackBurnFeesAndPrincipal()public{_assertResidualCallbackRollback(2);}
    function testResidualCallbackUnpauseRollsBackBurnFeesAndPrincipal()public{_assertResidualCallbackRollback(3);}

    function _allocationBefore(uint256 bucket,address asset) private view returns(uint256[4] memory b){
        return [fees.dust(bucket,asset),fees.compoundBalance(bucket,asset),fees.buybackBalance(asset),rewards.liabilities(asset)];
    }
    function _assertAllocation(uint256 bucket,address asset,uint256 receipt,uint256[4] memory b) private view {
        uint256 units=(b[0]+receipt)/20;
        assertEq(fees.dust(bucket,asset),(b[0]+receipt)%20,"carried raw fee dust");
        assertEq(fees.compoundBalance(bucket,asset),b[1]+units,"5 percent compound reserve");
        assertEq(fees.buybackBalance(asset),b[2]+units,"5 percent buyback reserve");
        assertEq(rewards.liabilities(asset),b[3]+18*units,"funded80 plus10 holder liabilities");
    }
    function _auditHarvestAllocation(uint256 bucket) private returns(Vm.Log[] memory logs) {
        uint256[4] memory beforeETH=_allocationBefore(bucket,address(0));
        uint256[4] memory beforeZZZ=_allocationBefore(bucket,address(token));
        vm.recordLogs();vault.collectFees(bucket,block.timestamp+100);logs=vm.getRecordedLogs();
        uint256 count;uint256 receivedETH;uint256 receivedZZZ;
        for(uint256 i;i<logs.length;++i){
            if(logs[i].emitter==address(vault) && logs[i].topics.length==2 &&
                logs[i].topics[0]==keccak256("FeesCollected(uint256,uint256,uint256)") && uint256(logs[i].topics[1])==bucket){
                ++count;(receivedETH,receivedZZZ)=abi.decode(logs[i].data,(uint256,uint256));
            }
        }
        assertEq(count,1,"one logical-bucket receipt for both physical legs");
        assertGt(receivedETH+receivedZZZ,0,"actual funded core fees were reached");
        _assertAllocation(bucket,address(0),receivedETH,beforeETH);
        _assertAllocation(bucket,address(token),receivedZZZ,beforeZZZ);
    }
    function _claimExactly(uint256 id,address owner,address asset) private returns(uint256 amount){
        amount=rewards.claimable(id,asset);uint256 liability=rewards.liabilities(asset);
        uint256 beforeBalance=asset==address(0)?owner.balance:token.balanceOf(owner);
        vm.prank(owner);assertEq(rewards.claim(id,asset),amount);
        assertEq((asset==address(0)?owner.balance:token.balanceOf(owner))-beforeBalance,amount);
        assertEq(rewards.liabilities(asset),liability-amount);assertEq(rewards.claimable(id,asset),0);
    }
    function testLifecycleModeOffPreservesBothLegFeesAndOtherHolderAfterPartialClaims() public {
        (uint256 alice,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        uint256 bob=_mint(BOB);_contribute(BOB,bob,1000 ether,false);
        uint128 mainL=positions.getPositionLiquidity(main);uint128 auxL=positions.getPositionLiquidity(aux);
        policy.setMode(pool,false,keccak256("TEST ONLY DESIRED SINGLE"));
        assertTrue(policy.configurationPending(bucket));assertEq(manager.secondaryId(main),aux);
        assertTrue(membership.eligible(alice));assertTrue(membership.eligible(bob));assertEq(membership.totalEligible(),2);
        core.unlock(abi.encode(uint8(2),Q96));_auditHarvestAllocation(bucket);
        uint256 bobETH=rewards.claimable(bob,address(0));uint256 bobZZZ=rewards.claimable(bob,address(token));
        assertGt(bobETH+bobZZZ,0);_claimExactly(alice,ALICE,address(0));_claimExactly(alice,ALICE,address(token));
        assertEq(rewards.claimable(bob,address(0)),bobETH);assertEq(rewards.claimable(bob,address(token)),bobZZZ);
        assertEq(_claimExactly(alice,ALICE,address(0)),0);assertEq(positions.getPositionLiquidity(main),mainL);
        assertEq(positions.getPositionLiquidity(aux),auxL);
        core.unlock(abi.encode(uint8(2),Q96));_auditHarvestAllocation(bucket);
        assertGt(rewards.claimable(bob,address(0)),bobETH);
        vm.warp(block.timestamp+43200);_prices();vault.rebalance(bucket,1,block.timestamp+100);
        uint256 replacement=vault.group(bucket).lpTokenId;
        assertFalse(policy.enabled(pool));assertFalse(policy.configurationPending(bucket));
        assertEq(manager.secondaryId(replacement),0);assertEq(manager.activeSecondaryCount(),0);
        assertGe(rewards.claimable(bob,address(0)),bobETH);assertGe(rewards.claimable(bob,address(token)),bobZZZ);
        _claimExactly(bob,BOB,address(0));_claimExactly(bob,BOB,address(token));
        assertEq(membership.totalEligible(),2);assertTrue(membership.eligible(alice));assertTrue(membership.eligible(bob));
    }
    function testLifecycleEnableDisableEnableAcknowledgesGeometryWithoutForcingFortyPercent() public {
        uint256 id=_mint(ALICE);_contribute(ALICE,id,1000 ether,false);uint256 bucket=vault.nftBucket(id);
        uint256 previous=vault.group(bucket).lpTokenId;uint256 shares=vault.sharesOf(id);
        policy.setMode(pool,true,keccak256("TEST ENABLE"));policy.setMode(pool,false,keccak256("TEST DISABLE"));
        policy.setMode(pool,true,keccak256("TEST ENABLE AGAIN"));
        assertEq(vault.group(bucket).lpTokenId,previous);assertEq(manager.secondaryId(previous),0);
        assertTrue(policy.configurationPending(bucket));vm.warp(block.timestamp+43200);_prices();
        vault.rebalance(bucket,1,block.timestamp+100);uint256 current=vault.group(bucket).lpTokenId;
        assertTrue(current!=previous);assertTrue(policy.enabled(pool));assertFalse(policy.configurationPending(bucket));
        assertEq(manager.secondaryId(current),0,"balanced main needs no manufactured residual");
        assertEq(manager.activeSecondaryCount(),0);assertEq(vault.sharesOf(id),shares);assertTrue(membership.eligible(id));
    }

    event LongHorizonCheckpoint(uint256 step,uint256 main,uint256 residual,uint256 deployed,uint256 idle,uint256 shares);
    /// @dev Test-only USD feeds deliberately follow the real core spot. This
    /// proves lifecycle accounting, not oracle independence or market profits.
    function _longEntry(address owner,uint256 id,address source,uint256 usd,bool grow) private {
        ZZZActivationEntry entry=registry.activationEntry();
        uint256 price=oracle.price(source);uint256 amount=(usd*1e18+price-1)/price;
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(id,pool,source,amount,1,block.timestamp+100,grow);
        bytes32 reviewed=ProtocolPolicyFixture.bind(address(access)).entryFingerprint();
        vm.startPrank(owner);
        if(source!=address(0))token.approve(address(entry),amount);
        entry.executeReviewed{value:source==address(0)?amount:0}(request,200,reviewed);
        vm.stopPrank();
        if(source!=address(0))assertEq(token.allowance(owner,address(entry)),0,"exact source approval consumed");
        assertEq(address(entry).balance,0);assertEq(token.balanceOf(address(entry)),0);
        assertEq(token.allowance(address(entry),address(vault)),0);
    }
    function _longReady(uint256 bucket) private {
        uint256 earliest=uint256(vault.group(bucket).lastRebalance)+43200;
        if(block.timestamp<earliest)vm.warp(earliest);
        _prices();(,bool manual)=strategy.rebalanceCondition(bucket);
        if(!manual){
            strategy.rebalanceConfirmation().observe(bucket);
            for(uint256 i;i<3;++i){vm.warp(block.timestamp+240);_prices();strategy.rebalanceConfirmation().observe(bucket);}
        }
        assertTrue(strategy.rebalanceConfirmation().ready(bucket));
    }
    function _longPortfolio(uint256 bucket,uint256 alice,uint256 bob,uint256 step) private {
        Position memory p=vault.group(bucket);uint256 aux=manager.secondaryId(p.lpTokenId);
        assertEq(positions.ownerOf(p.lpTokenId),address(vault));assertGt(positions.getPositionLiquidity(p.lpTokenId),0);
        (uint256 a0,uint256 a1)=manager.amounts(p.lpTokenId);
        if(aux!=0){
            assertTrue(aux!=p.lpTokenId);assertEq(positions.ownerOf(aux),address(vault));
            assertGt(positions.getPositionLiquidity(aux),0);
            (uint256 b0,uint256 b1)=manager.amounts(aux);a0+=b0;a1+=b1;
        }
        (uint256 all0,uint256 all1)=manager.portfolioAmounts(p.lpTokenId);assertEq(all0,a0);assertEq(all1,a1);
        assertEq(manager.activeSecondaryCount(),aux==0?0:1);
        assertEq(vault.sharesOf(alice)+vault.sharesOf(bob),vault.bucketTotalShares(bucket));
        assertEq(membership.totalEligible(),bob==0?1:2);assertTrue(membership.eligible(alice));
        if(bob!=0)assertTrue(membership.eligible(bob));
        (uint256 deployed,uint256 idle)=vault.migrationBudget().nav(bucket);
        assertEq(deployed,oracle.value(address(0),a0)+oracle.value(address(token),a1));
        assertEq(idle,oracle.value(address(0),p.idle0)+oracle.value(address(token),p.idle1));
        assertGe(address(vault).balance,vault.totalIdle(address(0)));assertGe(token.balanceOf(address(vault)),vault.totalIdle(address(token)));
        assertGe(address(rewards).balance,rewards.liabilities(address(0)));assertGe(token.balanceOf(address(rewards)),rewards.liabilities(address(token)));
        assertGe(address(fees).balance,fees.accounted(address(0)));assertGe(token.balanceOf(address(fees)),fees.accounted(address(token)));
        emit LongHorizonCheckpoint(step,p.lpTokenId,aux,deployed,idle,vault.bucketTotalShares(bucket));
    }
    function _longMainOnlyEntry(address owner,uint256 id,address source,uint256 usd,bool grow) private {
        uint256 bucket=grow?vault.nftBucket(id):vault.poolBucket(pool);Position memory beforePosition=vault.group(bucket);
        uint256 main=beforePosition.lpTokenId;uint256 aux=manager.secondaryId(main);
        uint128 mainL=positions.getPositionLiquidity(main);uint128 auxL=aux==0?0:positions.getPositionLiquidity(aux);
        bytes32 geometry=manager.portfolioFingerprint(main);uint256 supply=vault.bucketTotalShares(bucket);
        uint256 shares=vault.sharesOf(id);_longEntry(owner,id,source,usd,grow);
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(manager.secondaryId(main),aux);
        assertGt(positions.getPositionLiquidity(main),mainL);
        if(aux!=0)assertEq(positions.getPositionLiquidity(aux),auxL);
        assertEq(manager.portfolioFingerprint(main),geometry);assertEq(vault.group(bucket).lastRebalance,beforePosition.lastRebalance);
        assertEq(vault.group(bucket).centerX96,beforePosition.centerX96);
        assertGt(vault.sharesOf(id),shares);assertEq(vault.bucketTotalShares(bucket)-supply,vault.sharesOf(id)-shares);
    }
    function testLongHorizonSixDayModesEntryGrowthHarvestCompoundAndClaims() public {
        // Explicit test-only bootstrap of the real typed Compounder before any
        // user state. Production has no unseal/rebind function.
        access.beginBootstrap();ZZZCompounder compounder=new ZZZCompounder(address(access));
        access.bind(Ids.COMPOUNDER,address(compounder));access.seal();
        // Match the fresh example's admitted5USD floor. The older fixture's
        // 100USD pool floor correctly rejects smaller growth independently of
        // ProtocolPolicy's5USD default; no production guard is bypassed.
        registry.setMinimum(5e18);
        (uint256 alice,uint256 bucket,,)=_hybrid();uint256 bob=_mint(BOB);uint256 start=block.timestamp;
        _longMainOnlyEntry(BOB,bob,address(0),150e18,false);
        assertEq(rewards.claimable(bob,address(0)),0);assertEq(rewards.claimable(bob,address(token)),0);
        for(uint256 day;day<6;++day){
            vm.warp(block.timestamp+1 days);_prices();
            if(day==1 || day==4)policy.setMode(pool,false,keccak256(abi.encode("TEST MERGE",day)));
            if(day==2 || day==5)policy.setMode(pool,true,keccak256(abi.encode("TEST ENABLE",day)));
            uint160 center=vault.group(bucket).centerX96;
            _move(uint160(uint256(center)*(day%2==0?83:135)/100));_longReady(bucket);
            uint256 oldMain=vault.group(bucket).lpTokenId;uint256 oldAux=manager.secondaryId(oldMain);
            vault.rebalance(bucket,1,block.timestamp+100);_prices();
            vm.expectRevert();positions.ownerOf(oldMain);
            if(oldAux!=0){vm.expectRevert();positions.ownerOf(oldAux);}
            assertEq(manager.secondaryId(oldMain),0);assertFalse(policy.configurationPending(bucket));
            if(!policy.enabled(pool))assertEq(manager.secondaryId(vault.group(bucket).lpTokenId),0);
            if(day==2 || day==5)assertGt(manager.secondaryId(vault.group(bucket).lpTokenId),0);
            for(uint256 hour;hour<3;++hour){
                vm.warp(block.timestamp+1 hours);_prices();core.unlock(abi.encode(uint8(2),Q96));_auditHarvestAllocation(bucket);
            }
            uint256 bobETH=rewards.claimable(bob,address(0));uint256 bobZZZ=rewards.claimable(bob,address(token));
            _longMainOnlyEntry(ALICE,alice,day%2==0?address(0):address(token),5e18,true);
            assertGe(rewards.claimable(bob,address(0)),bobETH);assertGe(rewards.claimable(bob,address(token)),bobZZZ);
            uint256 main=vault.group(bucket).lpTokenId;uint256 aux=manager.secondaryId(main);
            uint128 auxL=aux==0?0:positions.getPositionLiquidity(aux);uint256 supply=vault.bucketTotalShares(bucket);
            assertTrue(vault.migrationBudget().compoundReady(bucket));compounder.compound(bucket,1,block.timestamp+100);
            assertEq(vault.group(bucket).lpTokenId,main);assertEq(manager.secondaryId(main),aux);
            if(aux!=0)assertEq(positions.getPositionLiquidity(aux),auxL);
            assertEq(vault.bucketTotalShares(bucket),supply);assertEq(vault.migrationBudget().lastCompound(bucket),block.timestamp);
            _claimExactly(day%2==0?alice:bob,day%2==0?ALICE:BOB,address(0));
            _claimExactly(day%2==0?bob:alice,day%2==0?BOB:ALICE,address(token));
            _longPortfolio(bucket,alice,bob,day);
        }
        assertGe(block.timestamp-start,6 days);
    }
    function _longOrdering(bool usersFirst) private {
        (uint256 alice,uint256 bucket,,)=_hybrid();uint256 bob=_mint(BOB);
        _longRejectedGrowthAtPoolFloor(alice,bucket);registry.setMinimum(5e18);
        vm.warp(block.timestamp+1 days);_prices();_move(uint160(uint256(vault.group(bucket).centerX96)*83/100));
        _longReady(bucket);bytes32 observationBefore;uint64 firstBefore;uint64 lastBefore;uint8 sideBefore;
        (observationBefore,firstBefore,lastBefore,sideBefore)=strategy.rebalanceConfirmation().observations(bucket);
        uint256 oldMain=vault.group(bucket).lpTokenId;
        if(!usersFirst){vault.rebalance(bucket,1,block.timestamp+100);_prices();}
        // Both orders execute at one timestamp/block: EVM transactions are
        // serialized, never simultaneous writes to the shared bucket.
        _longMainOnlyEntry(BOB,bob,address(token),150e18,false);
        assertEq(rewards.claimable(bob,address(0)),0);assertEq(rewards.claimable(bob,address(token)),0);
        _longMainOnlyEntry(ALICE,alice,address(0),5e18,true);
        if(usersFirst){
            (bytes32 identity,uint64 first,uint64 last,uint8 side)=strategy.rebalanceConfirmation().observations(bucket);
            assertEq(identity,observationBefore);assertEq(first,firstBefore);assertEq(last,lastBefore);assertEq(side,sideBefore);
            assertTrue(strategy.rebalanceConfirmation().ready(bucket));vault.rebalance(bucket,1,block.timestamp+100);_prices();
        }
        assertTrue(vault.group(bucket).lpTokenId!=oldMain);_longPortfolio(bucket,alice,bob,usersFirst?100:101);
        core.unlock(abi.encode(uint8(2),Q96));_auditHarvestAllocation(bucket);
        _claimExactly(alice,ALICE,address(0));_claimExactly(bob,BOB,address(token));
        _longPortfolio(bucket,alice,bob,102);
    }
    function testLongHorizonSameBlockUsersBeforeRebalance() public {_longOrdering(true);}
    function testLongHorizonSameBlockRebalanceBeforeUsers() public {_longOrdering(false);}
    function _longRejectedGrowthAtPoolFloor(uint256 id,uint256 bucket) private {
        ZZZActivationEntry entry=registry.activationEntry();
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(id,pool,address(0),25 ether,1,block.timestamp+100,true);
        bytes32 reviewed=ProtocolPolicyFixture.bind(address(access)).entryFingerprint();
        Position memory p=vault.group(bucket);uint256 aux=manager.secondaryId(p.lpTokenId);
        uint256 shares=vault.bucketTotalShares(bucket);uint256 balance=ALICE.balance;
        assertEq(registry.get(pool).minDepositUSD,100e18);
        vm.prank(ALICE);vm.expectRevert(ZZZModule.InvalidAmount.selector);
        entry.executeReviewed{value:25 ether}(request,200,reviewed);
        assertEq(vault.bucketTotalShares(bucket),shares);assertEq(ALICE.balance,balance);
        assertEq(vault.group(bucket).lpTokenId,p.lpTokenId);assertEq(manager.secondaryId(p.lpTokenId),aux);
        assertEq(address(entry).balance,0);assertEq(token.balanceOf(address(entry)),0);
    }
    function testAuditInfeasibleResidualGapRollsBackThenSingleModeRecovers() public {
        (uint256 alice,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        policy.configureResidualGap(pool,4000,keccak256("TEST ADMITTED BUT UNPLACEABLE GAP"));
        _longReady(bucket);
        (int24 lower,int24 upper,)=strategy.target(pool);uint160 q=manager.spot(pool);
        vm.expectRevert(ZZZModule.InvalidState.selector);policy.residualRange(pool,q,lower,upper,true);
        vm.expectRevert(ZZZModule.InvalidState.selector);policy.residualRange(pool,q,lower,upper,false);
        ResidualSnapshot memory beforeState=_residualSnapshot(alice,bucket,main,aux);
        uint256 feeETH=rewards.liabilities(address(0));uint256 feeZZZ=rewards.liabilities(address(token));
        vm.expectRevert(ZZZModule.InvalidState.selector);vault.rebalance(bucket,1,block.timestamp+100);
        _assertSameMain(beforeState.position,bucket,beforeState.mainL);
        assertEq(manager.portfolioFingerprint(main),beforeState.fingerprint);
        assertEq(positions.getPositionLiquidity(aux),beforeState.auxL);
        assertEq(vault.sharesOf(alice),beforeState.shares);assertEq(vault.bucketTotalShares(bucket),beforeState.total);
        assertEq(rewards.liabilities(address(0)),feeETH);assertEq(rewards.liabilities(address(token)),feeZZZ);
        assertEq(vault.group(bucket).idle0,beforeState.position.idle0);assertEq(vault.group(bucket).idle1,beforeState.position.idle1);
        // An impossible optional geometry cannot prevent the independently
        // governed single-position recovery; no limit or financial guard changes.
        policy.setMode(pool,false,keccak256("TEST RECOVER SINGLE WITHOUT LOOSENING LOSS"));
        assertTrue(strategy.rebalanceConfirmation().ready(bucket));
        vault.rebalance(bucket,1,block.timestamp+100);
        uint256 replacement=vault.group(bucket).lpTokenId;
        assertTrue(replacement!=main);assertEq(manager.secondaryId(replacement),0);assertEq(manager.activeSecondaryCount(),0);
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
        assertEq(vault.sharesOf(alice),beforeState.shares);assertEq(membership.totalEligible(),1);
    }

    function testAuditMinutePriceOutagePreservesHarvestClaimsAndResidualMergeRecovery() public {
        (uint256 alice,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        uint256 bob=_mint(BOB);_contribute(BOB,bob,1000 ether,false);
        uint256 shares=vault.bucketTotalShares(bucket);Position memory beforePosition=vault.group(bucket);
        ZZZMigrationBudget budget=vault.migrationBudget();
        uint128 mainL=positions.getPositionLiquidity(main);
        core.unlock(abi.encode(uint8(2),Q96));
        ethA.set(0,block.timestamp,block.timestamp);ethB.set(0,block.timestamp,block.timestamp);
        zzzA.set(0,block.timestamp,block.timestamp);zzzB.set(0,block.timestamp,block.timestamp);
        vm.expectRevert();budget.nav(bucket);
        _auditHarvestAllocation(bucket);
        assertGt(rewards.claimable(alice,address(0)),0);assertGt(rewards.claimable(bob,address(token)),0);
        _claimExactly(alice,ALICE,address(0));uint256 bobETH=rewards.claimable(bob,address(0));
        uint256 bobZZZ=rewards.claimable(bob,address(token));
        policy.setMode(pool,false,keccak256("TEST OUTAGE STOP RESIDUAL"));
        ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
        access.setPaused(true);migration.closeResidual(request);
        _assertSameMain(beforePosition,bucket,mainL);assertEq(manager.secondaryId(main),0);
        assertEq(vault.bucketTotalShares(bucket),shares);assertEq(membership.totalEligible(),2);
        assertEq(_claimExactly(bob,BOB,address(0)),bobETH);assertEq(_claimExactly(bob,BOB,address(token)),bobZZZ);
        // Price-dependent valuation recovers after one minute. Replacing the
        // LP still waits for the originally approved hard cooldown.
        vm.warp(block.timestamp+60);_prices();access.setPaused(false);
        (uint256 deployed,uint256 idle)=vault.migrationBudget().nav(bucket);assertGt(deployed,0);assertGt(idle,0);
        assertFalse(strategy.rebalanceConfirmation().ready(bucket));
        _longReady(bucket);vault.rebalance(bucket,1,block.timestamp+100);
        uint256 replacement=vault.group(bucket).lpTokenId;assertTrue(replacement!=main);
        assertEq(manager.activeSecondaryCount(),0);assertEq(vault.bucketTotalShares(bucket),shares);
        assertEq(nft.ownerOf(alice),ALICE);assertEq(nft.ownerOf(bob),BOB);
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
    }

    function testLongHorizonResidualMixedAndBothLegsOutsideStayBackedThenMerge() public {
        (uint256 alice,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        (int24 ml,int24 mu)=manager.ticks(main);(int24 al,int24 au)=manager.ticks(aux);
        _move(TickMath.getSqrtPriceAtTick((al+au)/2));
        (uint256 r0,uint256 r1)=manager.amounts(aux);assertGt(r0,0);assertGt(r1,0);
        _longPortfolio(bucket,alice,0,200);
        _move(TickMath.getSqrtPriceAtTick((mu>au?mu:au)+200));
        (uint256 a0,)=manager.amounts(main);(r0,)=manager.amounts(aux);assertEq(a0+r0,0);
        assertEq(manager.secondaryId(main),aux);_longPortfolio(bucket,alice,0,201);
        _move(TickMath.getSqrtPriceAtTick((ml<al?ml:al)-200));
        (,uint256 a1)=manager.amounts(main);(,r1)=manager.amounts(aux);assertEq(a1+r1,0);
        uint256 claimBefore=rewards.claimable(alice,address(0));
        uint256 bob=_mint(BOB);uint256 bobFunds=BOB.balance;uint256 supply=vault.bucketTotalShares(bucket);
        // Missing required pricing rejects entrant atomically, without forgetting
        // either physical leg. Raw funded claims do not require that price.
        ethA.set(0,block.timestamp,block.timestamp);ethB.set(0,block.timestamp,block.timestamp);
        vm.prank(BOB);vm.expectRevert();vault.activate{value:100 ether}(bob,pool,100 ether,0,1,block.timestamp+100);
        assertEq(BOB.balance,bobFunds);assertEq(vault.nftBucket(bob),0);assertEq(vault.bucketTotalShares(bucket),supply);
        assertEq(manager.secondaryId(main),aux);assertEq(_claimExactly(alice,ALICE,address(0)),claimBefore);
        _prices();_longPortfolio(bucket,alice,0,202);
        policy.setMode(pool,false,keccak256("TEST MERGE AFTER BOTH OUTSIDE"));vm.warp(block.timestamp+2 days);_prices();
        vault.rebalance(bucket,1,block.timestamp+100);_prices();assertEq(manager.activeSecondaryCount(),0);
        _longMainOnlyEntry(BOB,bob,address(0),150e18,false);_longPortfolio(bucket,alice,bob,203);
    }

    // Independent test ledger: replay actual funded-credit events against the
    // PRE-operation ownership of shares and collective membership. No production
    // reward index, paid index, fraction or accrued getter supplies this model.
    mapping(uint256=>uint256[2]) private marketScaled;
    mapping(uint256=>uint256[2]) private marketCollectiveScaled;
    mapping(uint256=>uint256[2]) private marketClaimed;
    struct MarketMembers { uint256[] shares; bool[] eligible; uint256 supply; uint256 count; }
    function _marketMembers() private view returns(MarketMembers memory m) {
        uint256 count=nft.mintedCount();m.shares=new uint256[](count);m.eligible=new bool[](count);
        for(uint256 i;i<count;++i){uint256 id=nft.tokenAtOrdinal(i+1);
            m.shares[i]=vault.sharesOf(id);m.eligible[i]=membership.eligible(id);
            m.supply+=m.shares[i];if(m.eligible[i])++m.count;
        }
    }
    function _marketReplay(Vm.Log[] memory logs,MarketMembers memory m) private {
        bytes32 signature=keccak256("PoolRewardsCredited(uint256,address,uint256,uint256)");
        for(uint256 j;j<logs.length;++j){Vm.Log memory log=logs[j];
            if(log.emitter!=address(rewards) || log.topics.length!=3 || log.topics[0]!=signature)continue;
            assertEq(uint256(log.topics[1]),vault.poolBucket(pool));
            address asset=address(uint160(uint256(log.topics[2])));assertTrue(asset==address(0)||asset==address(token));
            (uint256 personal,uint256 shared)=abi.decode(log.data,(uint256,uint256));
            assertGt(m.supply,0);assertGt(m.count,0);
            uint256 ownerDelta=Math.mulDiv(personal,1e36,m.supply);
            uint256 equalDelta=Math.mulDiv(shared,1e36,m.count);uint256 k=asset==address(0)?0:1;
            for(uint256 i;i<m.shares.length;++i){uint256 id=nft.tokenAtOrdinal(i+1);
                marketScaled[id][k]+=m.shares[i]*ownerDelta;
                marketCollectiveScaled[id][k]+=m.eligible[i]?equalDelta:0;
            }
        }
    }
    function _marketAssert(uint256 bucket) private {
        Position memory p=vault.group(bucket);MarketMembers memory m=_marketMembers();
        assertEq(m.supply,vault.bucketTotalShares(bucket));assertEq(m.count,membership.totalEligible());
        uint256 main=p.lpTokenId;uint256 aux=manager.secondaryId(main);
        assertEq(positions.ownerOf(main),address(vault));assertGt(positions.getPositionLiquidity(main),0);
        (uint256 a0,uint256 a1)=manager.amounts(main);
        if(aux!=0){assertEq(positions.ownerOf(aux),address(vault));assertGt(positions.getPositionLiquidity(aux),0);
            assertEq(manager.secondaryId(aux),0,"no residual tree");
            (uint256 b0,uint256 b1)=manager.amounts(aux);a0+=b0;a1+=b1;
            (int24 ml,int24 mu)=manager.ticks(main);(int24 al,int24 au)=manager.ticks(aux);
            assertGe(al,ml);assertLe(au,mu);
        }
        assertEq(manager.activeSecondaryCount(),aux==0?0:1);
        (uint256 all0,uint256 all1)=manager.portfolioAmounts(main);assertEq(a0,all0);assertEq(a1,all1);
        (uint256 deployed,uint256 idle)=vault.migrationBudget().nav(bucket);
        assertEq(deployed,oracle.value(address(0),a0)+oracle.value(address(token),a1));
        assertEq(idle,oracle.value(address(0),p.idle0)+oracle.value(address(token),p.idle1));
        // Combine each asset BEFORE USD rounding, as an independent inventory
        // mark; separately rounded classifications can differ by one raw unit.
        uint256 nav=oracle.value(address(0),a0+p.idle0+fees.compoundBalance(bucket,address(0)))
            +oracle.value(address(token),a1+p.idle1+fees.compoundBalance(bucket,address(token)));
        uint256 marked;uint256 royaltyWeights;uint256[2] memory claims;
        for(uint256 i;i<m.shares.length;++i){uint256 id=nft.tokenAtOrdinal(i+1);
            (bool available,uint256 value)=nft.currentLPValue(id);assertTrue(available);
            uint256 expected=m.supply==0?0:Math.mulDiv(nav,m.shares[i],m.supply);
            assertEq(value,expected,"per-NFT aggregate principal mark");marked+=value;
            uint256 weight=nft.royaltyRewards().weightOf(id);
            assertEq(weight,m.eligible[i]?uint256(nft.rarityOf(id))+1:0);royaltyWeights+=weight;
            for(uint256 k;k<2;++k){address asset=k==0?address(0):address(token);
                uint256 claim=_marketExpectedClaim(id,k);
                assertEq(rewards.claimable(id,asset),claim,"independent receipt model");claims[k]+=claim;
            }
        }
        assertLe(marked,nav);assertLt(nav-marked,nft.mintedCount());
        assertEq(nft.royaltyRewards().totalWeight(),royaltyWeights);
        for(uint256 k;k<2;++k){address asset=k==0?address(0):address(token);
            assertLe(claims[k],rewards.liabilities(asset));
            uint256 rewardBalance=k==0?address(rewards).balance:token.balanceOf(address(rewards));
            uint256 feeBalance=k==0?address(fees).balance:token.balanceOf(address(fees));
            uint256 vaultBalance=k==0?address(vault).balance:token.balanceOf(address(vault));
            assertGe(rewardBalance,rewards.liabilities(asset));assertGe(feeBalance,fees.accounted(asset));
            assertGe(vaultBalance,vault.totalIdle(asset));
        }
    }
    function _marketMint(address owner,uint8 rarity) private returns(uint256 id){
        uint256 word=rarity==0?0:uint256(nft.rarityRemaining(0))+(rarity==2?nft.rarityRemaining(1):0);
        bytes32 review=vault.mintPolicyFingerprint();vm.prank(owner);id=vault.mintDormant{value:0.05 ether}(review);
        vrf.fulfill(nft.requestOf(id),word,nft.mintedCount());nft.finalizeTraits(id);assertEq(nft.rarityOf(id),rarity);
    }
    function _marketEntry(address owner,uint256 id,address asset,uint256 usd,bool grow) private {
        uint256 bucket=vault.poolBucket(pool);Position memory p=vault.group(bucket);
        uint256 aux=p.lpTokenId==0?0:manager.secondaryId(p.lpTokenId);
        uint128 oldL=p.lpTokenId==0?0:positions.getPositionLiquidity(p.lpTokenId);
        uint128 auxL=aux==0?0:positions.getPositionLiquidity(aux);
        bytes32 geometry=p.lpTokenId==0?bytes32(0):manager.portfolioFingerprint(p.lpTokenId);
        uint256 oldShares=vault.sharesOf(id);MarketMembers memory members=_marketMembers();
        vm.recordLogs();_longEntry(owner,id,asset,usd,grow);Vm.Log[] memory logs=vm.getRecordedLogs();
        _marketReplay(logs,members);bucket=vault.nftBucket(id);
        uint256 net;uint256 marginal;uint256 upper;uint256 verified;
        bytes32 signature=keccak256("ContributionVerified(uint256,uint256,uint256,uint256,uint256,uint256,uint160,bytes32)");
        for(uint256 i;i<logs.length;++i)if(logs[i].emitter==address(oracle.contributionPricing()) &&
            logs[i].topics.length==3 && logs[i].topics[0]==signature){
            assertEq(uint256(logs[i].topics[1]),id);assertEq(uint256(logs[i].topics[2]),bucket);
            (,upper,marginal,net,,)=abi.decode(logs[i].data,(uint256,uint256,uint256,uint256,uint160,bytes32));++verified;
        }
        assertEq(verified,1,"one independently measured contribution");
        assertGe(marginal,upper-Math.mulDiv(upper,200,10000));
        (uint256 deployed,uint256 idle)=vault.migrationBudget().nav(bucket);
        uint256 issued=members.supply==0?net:Math.mulDiv(members.supply,net,deployed+idle-net);
        assertEq(vault.sharesOf(id)-oldShares,issued,"fair shares at post-swap incumbent NAV");
        assertEq(vault.bucketTotalShares(bucket),members.supply+issued);
        if(p.lpTokenId!=0){Position memory afterPosition=vault.group(bucket);
            assertEq(afterPosition.lpTokenId,p.lpTokenId);assertEq(manager.secondaryId(p.lpTokenId),aux);
            assertGt(positions.getPositionLiquidity(p.lpTokenId),oldL);
            if(aux!=0)assertEq(positions.getPositionLiquidity(aux),auxL);
            assertEq(manager.portfolioFingerprint(p.lpTokenId),geometry);
            assertEq(afterPosition.lastRebalance,p.lastRebalance);assertEq(afterPosition.centerX96,p.centerX96);
        }
        _marketAssert(bucket);
    }
    function _marketHarvest(uint256 bucket) private {
        MarketMembers memory m=_marketMembers();_marketReplay(_auditHarvestAllocation(bucket),m);_marketAssert(bucket);
    }
    function _marketRebalance(uint256 bucket) private {
        _longReady(bucket);MarketMembers memory m=_marketMembers();
        uint256 oldMain=vault.group(bucket).lpTokenId;uint256 oldAux=manager.secondaryId(oldMain);
        vm.recordLogs();vault.rebalance(bucket,1,block.timestamp+100);_marketReplay(vm.getRecordedLogs(),m);
        vm.expectRevert();positions.ownerOf(oldMain);
        if(oldAux!=0){vm.expectRevert();positions.ownerOf(oldAux);}
        assertEq(manager.secondaryId(oldMain),0);assertFalse(policy.configurationPending(bucket));_marketAssert(bucket);
    }
    function _marketClaim(uint256 id,uint256 k) private {
        uint256 expected=_marketExpectedClaim(id,k);
        assertEq(_claimExactly(id,nft.ownerOf(id),k==0?address(0):address(token)),expected);
        marketClaimed[id][k]+=expected;
    }
    function _marketExpectedClaim(uint256 id,uint256 k) private view returns(uint256){
        // Individual and equal-collective fractions are distinct entitlements;
        // joining their sub-unit remainders would invent a spendable raw unit.
        return marketScaled[id][k]/1e36+marketCollectiveScaled[id][k]/1e36-marketClaimed[id][k];
    }
    function _marketJourney(bool rising) private {
        access.beginBootstrap();ZZZCompounder compounder=new ZZZCompounder(address(access));
        access.bind(Ids.COMPOUNDER,address(compounder));access.seal(); // test-only before all user state
        registry.setMinimum(5e18);uint256 alice=_marketMint(ALICE,0);_marketMint(ALICE,2); // remains dormant
        _marketEntry(ALICE,alice,address(0),1000e18,false);uint256 bucket=vault.nftBucket(alice);
        for(uint256 phase;phase<4;++phase){
            bool hybrid=phase%2==0;policy.setMode(pool,hybrid,keccak256(abi.encode("CAMPAIGN MODE",phase)));
            uint160 center=vault.group(bucket).centerX96;
            _move(uint160(uint256(center)*(rising?83:135)/100));_marketAssert(bucket);
            // Two new NFTs may have the same owner; each joins independently.
            address owner=phase%2==0?BOB:ALICE;uint256 entrant=_marketMint(owner,uint8(phase%3));
            _marketEntry(owner,entrant,address(token),150e18,false);
            _marketEntry(ALICE,alice,address(0),5e18,true);
            _marketRebalance(bucket);uint256 main=vault.group(bucket).lpTokenId;
            if(!hybrid)assertEq(manager.secondaryId(main),0);
            else assertGt(manager.secondaryId(main),0,"trend supplies useful residual");
            _marketEntry(owner,entrant,address(0),8e18,true);
            uint256 afterId=_marketMint(owner,uint8((phase+1)%3));
            _marketEntry(owner,afterId,address(token),100e18,false);
            for(uint256 hour;hour<2;++hour){vm.warp(block.timestamp+1 hours);_prices();
                core.unlock(abi.encode(uint8(2),Q96));_marketHarvest(bucket);
            }
            MarketMembers memory members=_marketMembers();uint256 aux=manager.secondaryId(main);
            uint128 auxL=aux==0?0:positions.getPositionLiquidity(aux);
            assertTrue(vault.migrationBudget().compoundReady(bucket));vm.recordLogs();
            compounder.compound(bucket,1,block.timestamp+100);_marketReplay(vm.getRecordedLogs(),members);
            assertEq(vault.bucketTotalShares(bucket),members.supply);assertEq(vault.group(bucket).lpTokenId,main);
            assertEq(manager.secondaryId(main),aux);if(aux!=0)assertEq(positions.getPositionLiquidity(aux),auxL);
            _marketClaim(alice,phase%2);_marketClaim(entrant,(phase+1)%2);_marketAssert(bucket);
            rising=!rising;
        }
        assertEq(nft.mintedCount(),10);assertEq(membership.totalEligible(),9);
        for(uint256 i=1;i<=nft.mintedCount();++i){uint256 id=nft.tokenAtOrdinal(i);_marketClaim(id,0);_marketClaim(id,1);}
        _marketAssert(bucket);
    }
    function testMarketCampaignBullBearCohortsThroughRepeatedOneTwoOneModes() public {_marketJourney(true);}
    function testMarketCampaignBearBullCohortsThroughRepeatedOneTwoOneModes() public {_marketJourney(false);}

    function testMarketCampaignOrdinarySamplesSurviveEntryAndGrowWithoutClockReset() public {
        registry.setMinimum(5e18);uint256 alice=_marketMint(ALICE,0);_marketEntry(ALICE,alice,address(0),1000e18,false);
        uint256 bucket=vault.nftBucket(alice);uint256 main=vault.group(bucket).lpTokenId;
        uint256 earliest=uint256(vault.group(bucket).lastRebalance)+43200;
        _move(uint160(uint256(vault.group(bucket).centerX96)*83/100));
        vm.warp(earliest-600);_prices();assertFalse(strategy.rebalanceConfirmation().observe(bucket));
        (bytes32 identity,uint64 first,,uint8 side)=strategy.rebalanceConfirmation().observations(bucket);
        uint256 bob=_marketMint(BOB,1);_marketEntry(BOB,bob,address(token),100e18,false);
        _marketEntry(ALICE,alice,address(0),5e18,true);
        for(uint256 i;i<3;++i){vm.warp(block.timestamp+(i==2?120:240));_prices();strategy.rebalanceConfirmation().observe(bucket);}
        (bytes32 afterIdentity,uint64 afterFirst,,uint8 afterSide)=strategy.rebalanceConfirmation().observations(bucket);
        assertEq(afterIdentity,identity);assertEq(afterFirst,first);assertEq(afterSide,side);
        assertTrue(strategy.rebalanceConfirmation().ready(bucket));
        MarketMembers memory members=_marketMembers();vm.recordLogs();vault.rebalance(bucket,1,block.timestamp+100);
        _marketReplay(vm.getRecordedLogs(),members);assertTrue(vault.group(bucket).lpTokenId!=main);
        _marketAssert(bucket);
    }

    function testMarketCampaignMixedResidualPendingMergeTransferAndNewEntries() public {
        registry.setMinimum(5e18);uint256 alice=_marketMint(ALICE,1);_marketEntry(ALICE,alice,address(token),1000e18,false);
        uint256 bucket=vault.nftBucket(alice);policy.setMode(pool,true,keccak256("CAMPAIGN ON"));
        _move(uint160(uint256(vault.group(bucket).centerX96)*83/100));_marketRebalance(bucket);
        uint256 aux=manager.secondaryId(vault.group(bucket).lpTokenId);assertGt(aux,0);
        (int24 lower,int24 upper)=manager.ticks(aux);_move(TickMath.getSqrtPriceAtTick((lower+upper)/2));
        (uint256 r0,uint256 r1)=manager.amounts(aux);assertGt(r0,0);assertGt(r1,0);
        policy.setMode(pool,false,keccak256("CAMPAIGN PENDING MERGE"));
        uint256 bob=_marketMint(BOB,2);_marketEntry(BOB,bob,address(0),100e18,false);
        _marketEntry(ALICE,alice,address(token),5e18,true);assertEq(manager.secondaryId(vault.group(bucket).lpTokenId),aux);
        core.unlock(abi.encode(uint8(2),Q96));_marketHarvest(bucket);
        uint256 oldClaim=rewards.claimable(alice,address(0));assertGt(oldClaim,0);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,alice);
        vm.prank(ALICE);vm.expectRevert(ZZZModule.Unauthorized.selector);rewards.claim(alice,address(0));
        _marketClaim(alice,0);_marketRebalance(bucket);assertEq(manager.activeSecondaryCount(),0);
        _marketEntry(BOB,alice,address(0),5e18,true);_marketAssert(bucket);
    }

    function testMarketCampaignBothOutsideInputsStayInMainWithoutRecentering() public {
        registry.setMinimum(5e18);uint256 alice=_marketMint(ALICE,0);_marketEntry(ALICE,alice,address(0),1000e18,false);
        uint256 bucket=vault.nftBucket(alice);policy.setMode(pool,true,keccak256("CAMPAIGN OUTSIDE ON"));
        _move(uint160(uint256(vault.group(bucket).centerX96)*83/100));_marketRebalance(bucket);
        uint256 main=vault.group(bucket).lpTokenId;uint256 aux=manager.secondaryId(main);assertGt(aux,0);
        (int24 lower,int24 upper)=manager.ticks(main);
        _move(TickMath.getSqrtPriceAtTick(upper+200));_marketAssert(bucket);
        uint256 bob=_marketMint(BOB,1);_marketEntry(BOB,bob,address(token),100e18,false);
        _marketEntry(ALICE,alice,address(token),5e18,true);
        _move(TickMath.getSqrtPriceAtTick(lower-200));_marketAssert(bucket);
        uint256 next=_marketMint(ALICE,2);_marketEntry(ALICE,next,address(0),100e18,false);
        _marketEntry(BOB,bob,address(0),5e18,true);
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(manager.secondaryId(main),aux);
        policy.setMode(pool,false,keccak256("CAMPAIGN RECOVER BOTH OUTSIDE"));_marketRebalance(bucket);
    }

    function testMarketCampaignFeedDisagreementRejectsEntryThenRecoversWithoutLostRights() public {
        registry.setMinimum(5e18);uint256 alice=_marketMint(ALICE,0);_marketEntry(ALICE,alice,address(0),1000e18,false);
        uint256 bucket=vault.nftBucket(alice);policy.setMode(pool,true,keccak256("CAMPAIGN FAULT ON"));
        _move(uint160(uint256(vault.group(bucket).centerX96)*83/100));_marketRebalance(bucket);
        uint256 bob=_marketMint(BOB,2);ZZZActivationEntry entry=registry.activationEntry();
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(bob,pool,address(0),100 ether,1,block.timestamp+100,false);
        bytes32 reviewed=ProtocolPolicyFixture.bind(address(access)).entryFingerprint();
        bytes32 physical=manager.executionPortfolioFingerprint(vault.group(bucket).lpTokenId);
        uint256 supply=vault.bucketTotalShares(bucket);uint256 balance=BOB.balance;
        ethB.set(2e18,block.timestamp,block.timestamp);
        vm.prank(BOB);vm.expectRevert();entry.executeReviewed{value:100 ether}(request,200,reviewed);
        assertEq(BOB.balance,balance);assertEq(vault.sharesOf(bob),0);assertEq(vault.bucketTotalShares(bucket),supply);
        assertEq(manager.executionPortfolioFingerprint(vault.group(bucket).lpTokenId),physical);
        (bool available,)=nft.currentLPValue(alice);assertFalse(available);
        core.unlock(abi.encode(uint8(2),Q96));_marketHarvestWithoutPrice(bucket);_marketClaim(alice,0);
        vm.warp(block.timestamp+60);_prices();_marketEntry(BOB,bob,address(0),100e18,false);_marketAssert(bucket);
    }
    function _marketHarvestWithoutPrice(uint256 bucket) private {
        MarketMembers memory m=_marketMembers();_marketReplay(_auditHarvestAllocation(bucket),m);
        for(uint256 i=1;i<=nft.mintedCount();++i){uint256 id=nft.tokenAtOrdinal(i);
            for(uint256 k;k<2;++k)assertEq(rewards.claimable(id,k==0?address(0):address(token)),_marketExpectedClaim(id,k));
        }
    }

    function testMarketCampaignRoyaltyEntitlementsStaySeparateThroughLPModeChangesAndExit() public {
        registry.setMinimum(5e18);uint256 alice=_marketMint(ALICE,0);uint256 bob=_marketMint(BOB,2);
        _marketEntry(ALICE,alice,address(0),1000e18,false);uint256 bucket=vault.nftBucket(alice);
        _finishRoyaltyWindow();ZZZRoyaltyRewards royalties=nft.royaltyRewards();
        (bool funded,)=address(royalties).call{value:4 ether}("");assertTrue(funded);royalties.sync(address(0));
        assertEq(royalties.claimable(alice,address(0)),4 ether);assertEq(royalties.claimable(bob,address(0)),0);
        _marketEntry(BOB,bob,address(token),100e18,false);
        policy.setMode(pool,true,keccak256("CAMPAIGN ROYALTY ON"));
        _move(uint160(uint256(vault.group(bucket).centerX96)*83/100));_marketRebalance(bucket);
        (funded,)=address(royalties).call{value:4 ether}("");assertTrue(funded);royalties.sync(address(0));
        assertEq(royalties.claimable(alice,address(0)),5 ether);assertEq(royalties.claimable(bob,address(0)),3 ether);
        core.unlock(abi.encode(uint8(2),Q96));_marketHarvest(bucket);
        uint256 claimETH=rewards.claimable(alice,address(0));uint256 burnETH=fees.buybackBalance(address(0));
        MarketMembers memory m=_marketMembers();access.setPaused(true);
        vm.recordLogs();migration.beginCollectiveExit(keccak256("CAMPAIGN TERMINAL"));migration.closeBucket(bucket,0,0,block.timestamp+100);
        _marketReplay(vm.getRecordedLogs(),m);assertEq(manager.activeSecondaryCount(),0);
        assertGe(rewards.claimable(alice,address(0)),claimETH);assertGe(fees.buybackBalance(address(0)),burnETH);
        migration.allocatePrincipal(32);uint256[] memory ids=new uint256[](2);ids[0]=alice;ids[1]=bob;
        uint256[2] memory e;uint256[2] memory z;uint256 beforeETH=ALICE.balance;uint256 beforeZZZ=token.balanceOf(ALICE);
        (e[0],z[0])=migration.claimablePrincipal(alice);(e[1],z[1])=migration.claimablePrincipal(bob);
        assertGt(e[0]+z[0],0);assertEq(migration.distributePrincipal(ids),2);
        assertEq(ALICE.balance-beforeETH,e[0]);assertEq(token.balanceOf(ALICE)-beforeZZZ,z[0]);
        assertEq(migration.remainingETH(),0);assertEq(migration.remainingZZZ(),0);
        _marketClaim(alice,0);_marketClaim(bob,1);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,alice);
        (funded,)=address(royalties).call{value:4 ether}("");assertTrue(funded);royalties.sync(address(0));
        assertEq(royalties.claimable(alice,address(0)),6 ether);assertEq(royalties.claimable(bob,address(0)),6 ether);
        uint256 recipientBefore=BOB.balance;vm.prank(BOB);royalties.claim(alice,address(0));assertEq(BOB.balance-recipientBefore,6 ether);
        assertEq(membership.totalEligible(),2);assertEq(royalties.totalWeight(),4);
        (bool available,uint256 value)=nft.currentLPValue(alice);assertTrue(available);assertEq(value,0);
    }
    function _manualAuditRawRequest(uint256 bucket) private view returns(EmergencyRebalance memory r){
        int24 tick=TickMath.getTickAtSqrtPrice(manager.spot(pool));int24 aligned=tick/200*200;
        r.bucket=bucket;r.custodyHash=migration.emergencyCustodyHash(bucket);r.checks=0;
        r.lower=aligned-4000;r.upper=aligned+4000;r.minimumLiquidity=1;
        r.deadline=block.timestamp+100;r.reviewHash=keccak256("TEST ONLY EXPLICIT RAW RECOVERY");
    }
    function _manualAuditDisableFinancialDependencies() private {
        registry.setOperations(false);bytes32[] memory empty=new bytes32[](0);
        manager.balancingRouter().configureExecutionPools(empty,keccak256("TEST DISABLED AUTOMATIC SWAPS"));
        strategy.rebalanceConfirmation().configure(600,0,keccak256("TEST STOPPED ORDINARY WINDOW"));
        vault.migrationBudget().setLossLimits(0,0);
        ethA.set(0,block.timestamp,block.timestamp);ethB.set(0,block.timestamp,block.timestamp);
        zzzA.set(0,block.timestamp,block.timestamp);zzzB.set(0,block.timestamp,block.timestamp);
    }
    function testManualAuditRawParkAndReenterIgnorePolicyOutagesWithoutLosingRights() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        policy.setMode(pool,false,keccak256("TEST RAW RECOVERY STAY SINGLE"));
        core.unlock(abi.encode(uint8(2),Q96));uint256 shares=vault.sharesOf(id);
        ZZZMigration.ParkingRequest memory parking=_residualReview(bucket);parking.minimum0=0;parking.minimum1=0;
        access.setPaused(true);_manualAuditDisableFinancialDependencies();
        uint256 operatorETH=address(this).balance;uint256 operatorZZZ=token.balanceOf(address(this));
        migration.park(parking);assertEq(uint256(vault.group(bucket).status),uint256(PositionStatus.Parked));
        assertEq(manager.activeSecondaryCount(),0);assertEq(vault.sharesOf(id),shares);
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
        uint256 oldClaim=rewards.claimable(id,address(0));uint256 burn=fees.buybackBalance(address(0));
        assertGt(oldClaim,0);assertGt(burn,0);
        vm.expectRevert();migration.resume(bucket,pool,1,block.timestamp+100);
        access.setPaused(false);vm.expectRevert();migration.resume(bucket,pool,1,block.timestamp+100);
        access.setPaused(true);EmergencyRebalance memory r=_manualAuditRawRequest(bucket);
        migration.emergencyRebalance(r);Position memory p=vault.group(bucket);
        assertEq(uint256(p.status),uint256(PositionStatus.Active));assertGt(p.lpTokenId,0);
        assertEq(positions.ownerOf(p.lpTokenId),address(vault));assertEq(manager.secondaryId(p.lpTokenId),0);
        assertEq(vault.sharesOf(id),shares);assertEq(vault.bucketTotalShares(bucket),shares);
        assertEq(rewards.claimable(id,address(0)),oldClaim);assertEq(fees.buybackBalance(address(0)),burn);
        assertEq(address(this).balance,operatorETH);assertEq(token.balanceOf(address(this)),operatorZZZ);
        assertTrue(membership.eligible(id));assertFalse(vault.migrationBudget().emergencyActive());
        assertTrue(access.paused());_claimExactly(id,ALICE,address(0));
        registry.setOperations(true);_prices();access.setPaused(false);
        vm.expectRevert();vault.rebalance(bucket,1,block.timestamp+100);
    }
    function testManualAuditRawResidualCloseSurvivesInventoryReversalAndUnavailablePrices() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();
        ZZZMigration.ParkingRequest memory r=_residualReview(bucket);r.minimum0=0;r.minimum1=0;
        (int24 lower,int24 upper)=manager.ticks(aux);_move(TickMath.getSqrtPriceAtTick(upper+200));
        (uint256 expected0,uint256 expected1)=manager.amounts(aux);assertGt(expected0+expected1,0);
        uint128 mainL=positions.getPositionLiquidity(main);Position memory p=vault.group(bucket);
        uint256 shares=vault.sharesOf(id);access.setPaused(true);_manualAuditDisableFinancialDependencies();
        migration.closeResidual(r);_assertSameMain(p,bucket,mainL);assertEq(manager.secondaryId(main),0);
        assertEq(vault.sharesOf(id),shares);assertEq(manager.activeSecondaryCount(),0);
        assertEq(vault.group(bucket).idle0-p.idle0,expected0);assertEq(vault.group(bucket).idle1-p.idle1,expected1);
        vm.expectRevert();positions.ownerOf(aux);assertTrue(access.paused());assertTrue(policy.enabled(pool));
        assertLt(lower,upper);
    }
    function testManualAuditRawActiveRebalanceDoesNotNeedPendingGeometryOrConfiguredRouter() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();uint256 shares=vault.sharesOf(id);
        policy.configureResidualGap(pool,4000,keccak256("TEST INFEASIBLE OPTIONAL GEOMETRY"));
        access.setPaused(true);_manualAuditDisableFinancialDependencies();
        EmergencyRebalance memory r=_manualAuditRawRequest(bucket);migration.emergencyRebalance(r);
        uint256 replacement=vault.group(bucket).lpTokenId;assertTrue(replacement!=main);
        assertEq(manager.secondaryId(replacement),0);assertEq(manager.activeSecondaryCount(),0);
        assertEq(vault.sharesOf(id),shares);assertTrue(policy.enabled(pool));assertTrue(access.paused());
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
    }

    // Destination-mode creation is a replacement context too: movement/resume
    // must not silently revert to a main-only accounting view.
    function _residualAuditPrincipalValue(uint256 bucket) private view returns(uint256) {
        Position memory p=vault.group(bucket);uint256 a0;uint256 a1;
        if(p.lpTokenId!=0)(a0,a1)=manager.portfolioAmounts(p.lpTokenId);
        return oracle.value(address(0),a0+p.idle0+fees.compoundBalance(bucket,address(0)))+
            oracle.value(address(token),a1+p.idle1+fees.compoundBalance(bucket,address(token)));
    }
    function _residualAuditPhysical(uint256 bucket,bool wantResidual) private view returns(uint256 main,uint256 aux) {
        Position memory p=vault.group(bucket);main=p.lpTokenId;aux=manager.secondaryId(main);
        assertEq(positions.ownerOf(main),address(vault));assertGt(positions.getPositionLiquidity(main),0);
        (CoreKey memory actual,)=positions.getPoolAndPositionInfo(main);assertEq(keccak256(abi.encode(actual)),p.poolId);
        (uint256 a0,uint256 a1)=manager.amounts(main);
        if(wantResidual){
            assertGt(aux,0);assertTrue(aux!=main);assertEq(positions.ownerOf(aux),address(vault));
            assertGt(positions.getPositionLiquidity(aux),0);assertEq(manager.secondaryId(aux),0);
            // The reverse association is private; the authenticated full
            // portfolio read below checks it without inventing a public getter.
            assertTrue(manager.portfolioFingerprint(main)!=bytes32(0));
            (actual,)=positions.getPoolAndPositionInfo(aux);assertEq(keccak256(abi.encode(actual)),p.poolId);
            (uint256 b0,uint256 b1)=manager.amounts(aux);a0+=b0;a1+=b1;
            (int24 ml,int24 mu)=manager.ticks(main);(int24 al,int24 au)=manager.ticks(aux);
            assertGe(al,ml);assertLe(au,mu);
        }else assertEq(aux,0);
        assertEq(manager.activeSecondaryCount(),wantResidual?1:0);
        (uint256 total0,uint256 total1)=manager.portfolioAmounts(main);assertEq(total0,a0);assertEq(total1,a1);
        assertGe(address(vault).balance,vault.totalIdle(address(0)));assertGe(token.balanceOf(address(vault)),vault.totalIdle(address(token)));
        assertGe(address(fees).balance,fees.accounted(address(0)));assertGe(token.balanceOf(address(fees)),fees.accounted(address(token)));
        assertGe(address(rewards).balance,rewards.liabilities(address(0))+rewards.orphaned(address(0)));
        assertGe(token.balanceOf(address(rewards)),rewards.liabilities(address(token))+rewards.orphaned(address(token)));
    }
    function testResidualAuditEnabledDestinationMoveCreatesTrackedPortfolioAndPreservesEarnedRights() public {
        (uint256 id,uint256 bucket,uint256 oldMain,uint256 oldAux)=_hybrid();
        core.unlock(abi.encode(uint8(2),Q96));_auditHarvestAllocation(bucket);
        uint256[2] memory claims=[rewards.claimable(id,address(0)),rewards.claimable(id,address(token))];
        uint256 shares=vault.sharesOf(id);uint256 value=_residualAuditPrincipalValue(bucket);
        bytes32 destination=registry.admitTarget();
        targetKey=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),3000,200,IHooks(address(0)));
        core.initialize(targetKey,manager.spot(pool));core.unlock(abi.encode(uint8(3),Q96));
        strategy.setRangeOrientation(destination,1);policy.setMode(destination,true,keccak256("TEST DESTINATION HYBRID"));
        migration.moveFunds(bucket,destination,1,block.timestamp+100);
        (uint256 main,)=_residualAuditPhysical(bucket,true);assertTrue(main!=oldMain);
        assertEq(vault.group(bucket).poolId,destination);assertEq(vault.poolBucket(destination),bucket);
        assertEq(vault.sharesOf(id),shares);assertEq(vault.bucketTotalShares(bucket),shares);
        assertEq(rewards.claimable(id,address(0)),claims[0]);assertEq(rewards.claimable(id,address(token)),claims[1]);
        assertGe(_residualAuditPrincipalValue(bucket),Math.mulDiv(value,9700,10000));
        vm.expectRevert();positions.ownerOf(oldMain);vm.expectRevert();positions.ownerOf(oldAux);
        assertEq(manager.secondaryId(oldMain),0);assertFalse(policy.configurationPending(bucket));
    }
    function testResidualAuditEnabledResumeThenGrowthThenSingleMergeKeepsAllBacking() public {
        (uint256 alice,uint256 bucket,uint256 oldMain,uint256 oldAux)=_hybrid();
        core.unlock(abi.encode(uint8(2),Q96));_auditHarvestAllocation(bucket);
        uint256 shares=vault.sharesOf(alice);uint256 value=_residualAuditPrincipalValue(bucket);
        ZZZMigration.ParkingRequest memory r=_residualReview(bucket);r.minimum0=0;r.minimum1=0;
        access.setPaused(true);migration.park(r);assertEq(manager.activeSecondaryCount(),0);
        vm.expectRevert();positions.ownerOf(oldMain);vm.expectRevert();positions.ownerOf(oldAux);
        access.setPaused(false);migration.resume(bucket,pool,1,block.timestamp+100);
        (uint256 main,uint256 aux)=_residualAuditPhysical(bucket,true);
        assertEq(vault.sharesOf(alice),shares);assertGe(_residualAuditPrincipalValue(bucket),Math.mulDiv(value,9700,10000));
        uint64 clock=vault.group(bucket).lastRebalance;uint128 auxL=positions.getPositionLiquidity(aux);
        uint256 bob=_mint(BOB);_contribute(BOB,bob,1000 ether,false);_contribute(ALICE,alice,250 ether,true);
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(manager.secondaryId(main),aux);
        assertEq(positions.getPositionLiquidity(aux),auxL);assertEq(vault.group(bucket).lastRebalance,clock);
        assertEq(membership.totalEligible(),2);assertGt(vault.sharesOf(alice),shares);
        uint256 aliceShares=vault.sharesOf(alice);uint256 bobShares=vault.sharesOf(bob);
        policy.setMode(pool,false,keccak256("TEST POST RESUME SINGLE"));assertTrue(policy.configurationPending(bucket));
        vm.warp(uint256(clock)+43200);_prices();vault.rebalance(bucket,1,block.timestamp+100);
        _residualAuditPhysical(bucket,false);assertEq(manager.secondaryId(main),0);
        assertEq(vault.sharesOf(alice),aliceShares);assertEq(vault.sharesOf(bob),bobShares);
        assertEq(vault.bucketTotalShares(bucket),aliceShares+bobShares);
        core.unlock(abi.encode(uint8(2),Q96));_auditHarvestAllocation(bucket);
        assertGt(rewards.claimable(alice,address(0)),0);assertGt(rewards.claimable(bob,address(0)),0);
        _claimExactly(alice,ALICE,address(0));_claimExactly(bob,BOB,address(0));
    }
    function testResidualAuditInfeasibleDestinationRollsBackBothSourceLegsAndReservation() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();core.unlock(abi.encode(uint8(2),Q96));
        bytes32 destination=registry.admitTarget();
        targetKey=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),3000,200,IHooks(address(0)));
        core.initialize(targetKey,manager.spot(pool));core.unlock(abi.encode(uint8(3),Q96));
        strategy.setRangeOrientation(destination,1);policy.setMode(destination,true,keccak256("TEST DESTINATION MODE"));
        policy.configureResidualGap(destination,4000,keccak256("TEST IMPOSSIBLE DESTINATION GEOMETRY"));
        bytes32 beforeState=keccak256(abi.encode(_residualSnapshot(id,bucket,main,aux)));
        uint256[6] memory reserves=[fees.accounted(address(0)),fees.accounted(address(token)),
            rewards.liabilities(address(0)),rewards.liabilities(address(token)),fees.dust(bucket,address(0)),fees.dust(bucket,address(token))];
        assertEq(vault.poolBucket(destination),0);assertEq(vault.canonicalModule().aliasBucket(destination),0);
        vm.expectRevert();migration.moveFunds(bucket,destination,1,block.timestamp+100);
        assertEq(keccak256(abi.encode(_residualSnapshot(id,bucket,main,aux))),beforeState);
        assertEq(vault.poolBucket(destination),0);assertEq(vault.canonicalModule().aliasBucket(destination),0);
        assertEq(fees.accounted(address(0)),reserves[0]);assertEq(fees.accounted(address(token)),reserves[1]);
        assertEq(rewards.liabilities(address(0)),reserves[2]);assertEq(rewards.liabilities(address(token)),reserves[3]);
        assertEq(fees.dust(bucket,address(0)),reserves[4]);assertEq(fees.dust(bucket,address(token)),reserves[5]);
        _residualAuditPhysical(bucket,true);assertTrue(policy.enabled(destination));assertTrue(policy.configurationPending(bucket)==false);
    }

    struct ResidualAuditProducerVector {
        uint256 schema;address executor;address positionManager;address vaultAddress;bytes32 poolId;
        uint256 mainId;uint256 secondaryId;uint256 mainInfo;uint256 secondaryInfo;uint128 mainLiquidity;uint128 secondaryLiquidity;
        uint160 sqrtPriceX96;int24 storedTick;uint160 centreX96;
        uint256 mainAmount0;uint256 mainAmount1;uint256 secondaryAmount0;uint256 secondaryAmount1;
        bytes32 stableHash;bytes32 executionHash;
        address currency0;address currency1;uint24 fee;int24 tickSpacing;address hooks;
    }
    event ResidualAuditVectorProduced(uint8 indexed phase,bytes encoded);
    function _residualAuditProduce(uint256 bucket) private view returns(ResidualAuditProducerVector memory v) {
        Position memory p=vault.group(bucket);v.schema=1;
        v.executor=manager.positionOperator();v.positionManager=address(positions);v.vaultAddress=address(vault);v.poolId=p.poolId;
        v.mainId=p.lpTokenId;v.secondaryId=manager.secondaryId(p.lpTokenId);assertGt(v.secondaryId,0);
        (CoreKey memory actual,PositionInfo mainInfo)=positions.getPoolAndPositionInfo(v.mainId);
        (CoreKey memory auxiliary,PositionInfo secondaryInfo)=positions.getPoolAndPositionInfo(v.secondaryId);
        v.mainInfo=PositionInfo.unwrap(mainInfo);v.secondaryInfo=PositionInfo.unwrap(secondaryInfo);
        assertEq(keccak256(abi.encode(actual)),keccak256(abi.encode(auxiliary)));
        v.currency0=Currency.unwrap(actual.currency0);v.currency1=Currency.unwrap(actual.currency1);
        v.fee=actual.fee;v.tickSpacing=actual.tickSpacing;v.hooks=address(actual.hooks);
        v.mainLiquidity=positions.getPositionLiquidity(v.mainId);v.secondaryLiquidity=positions.getPositionLiquidity(v.secondaryId);
        (v.sqrtPriceX96,v.storedTick,,)=state.getSlot0(PoolId.wrap(p.poolId));v.centreX96=p.centerX96;
        (v.mainAmount0,v.mainAmount1)=manager.amounts(v.mainId);(v.secondaryAmount0,v.secondaryAmount1)=manager.amounts(v.secondaryId);
        v.stableHash=manager.portfolioFingerprint(v.mainId);v.executionHash=manager.executionPortfolioFingerprint(v.mainId);
    }
    function testResidualAuditProducerVectorsFromActualUnfilledAndMixedPortfolio() public {
        (,uint256 bucket,uint256 main,uint256 auxiliary)=_hybrid();
        ResidualAuditProducerVector memory unfilled=_residualAuditProduce(bucket);
        assertTrue((unfilled.secondaryAmount0==0)!=(unfilled.secondaryAmount1==0));
        emit ResidualAuditVectorProduced(0,abi.encode(unfilled));
        (int24 lower,int24 upper)=manager.ticks(auxiliary);
        _move(TickMath.getSqrtPriceAtTick(int24((int256(lower)+int256(upper))/2)));
        ResidualAuditProducerVector memory mixed=_residualAuditProduce(bucket);
        assertGt(mixed.secondaryAmount0,0);assertGt(mixed.secondaryAmount1,0);
        assertEq(mixed.mainId,main);assertEq(mixed.secondaryId,auxiliary);
        assertEq(mixed.mainLiquidity,unfilled.mainLiquidity);assertEq(mixed.secondaryLiquidity,unfilled.secondaryLiquidity);
        assertEq(mixed.stableHash,unfilled.stableHash);assertEq(mixed.executionHash,unfilled.executionHash);
        emit ResidualAuditVectorProduced(1,abi.encode(mixed));
    }

    struct ConsolidationSnapshot {
        Position position;bytes32 mainStructure;bytes32 control;uint128 mainL;uint256 shares;uint256 supply;
        uint64 nonce;uint64 epoch;uint64 lastCompound;uint256[4] ethAllocation;uint256[4] zzzAllocation;
        uint256 operatorETH;uint256 operatorZZZ;
    }
    /// @dev The main may gain L and attributed idle may change, but none of its
    /// geometry, ownership, clock or accounting identity is replaced.
    function _consolidationMainStructure(uint256 bucket) private view returns(bytes32) {
        Position memory p=vault.group(bucket);p.idle0=0;p.idle1=0;
        (CoreKey memory actual,PositionInfo info)=positions.getPoolAndPositionInfo(p.lpTokenId);
        return keccak256(abi.encode(p,positions.ownerOf(p.lpTokenId),actual,PositionInfo.unwrap(info)));
    }
    function _consolidationSnapshot(uint256 id,uint256 bucket) private view returns(ConsolidationSnapshot memory s) {
        s.position=vault.group(bucket);s.mainStructure=_consolidationMainStructure(bucket);s.control=policy.controlFingerprint(pool);
        s.mainL=positions.getPositionLiquidity(s.position.lpTokenId);s.shares=vault.sharesOf(id);s.supply=vault.bucketTotalShares(bucket);
        s.nonce=migration.parkingNonce(bucket);s.epoch=migration.custodyEpoch(bucket);s.lastCompound=vault.migrationBudget().lastCompound(bucket);
        s.ethAllocation=_allocationBefore(bucket,address(0));s.zzzAllocation=_allocationBefore(bucket,address(token));
        s.operatorETH=address(this).balance;s.operatorZZZ=token.balanceOf(address(this));
    }
    function _consolidationReview(uint256 bucket,bool forced) private view returns(EmergencyRebalance memory r) {
        r.bucket=bucket;r.custodyHash=migration.consolidationCustodyHash(bucket);r.checks=forced?0:14;
        (r.lower,r.upper)=manager.ticks(vault.group(bucket).lpTokenId);r.minimumLiquidity=1;
        r.deadline=block.timestamp+100;r.reviewHash=keccak256("TEST ONLY UNCHANGED MAIN CONSOLIDATION");
    }
    function _consolidationExplicitReview(uint256 bucket,uint8 checks) private returns(EmergencyRebalance memory r) {
        r=_consolidationReview(bucket,true);r.checks=checks;Position memory p=vault.group(bucket);
        uint256 aux=manager.secondaryId(p.lpTokenId);uint256 a0;uint256 a1;if(aux!=0)(a0,a1)=manager.amounts(aux);
        ZZZLPBalancer router=manager.balancingRouter();vm.prank(address(manager));
        ZZZLPBalancer.Plan memory plan=router.plan(pool,r.lower,r.upper,a0+p.idle0,a1+p.idle1);
        r.swapPool=plan.poolId;r.zeroForOne=plan.zeroForOne;r.amountIn=uint128(plan.amountIn);r.minimumOut=uint128(plan.minimumOut);
    }
    function _consolidationStateHash(uint256 id,uint256 bucket) private view returns(bytes32) {
        uint256 main=vault.group(bucket).lpTokenId;
        return keccak256(abi.encode(_consolidationSnapshot(id,bucket),manager.executionPortfolioFingerprint(main),
            manager.activeSecondaryCount(),policy.controlFingerprint(pool),policy.appliedRevision(main),
            fees.accounted(address(0)),fees.accounted(address(token)),rewards.orphaned(address(0)),rewards.orphaned(address(token))));
    }
    function _consolidateAndAssert(uint256 id,uint256 bucket,EmergencyRebalance memory r,bool forced) private {
        ConsolidationSnapshot memory s=_consolidationSnapshot(id,bucket);uint256 aux=manager.secondaryId(s.position.lpTokenId);
        vm.recordLogs();migration.consolidateResidual(r,forced);Vm.Log[] memory logs=vm.getRecordedLogs();
        uint256 receipts;uint256 received0;uint256 received1;
        for(uint256 i;i<logs.length;++i)if(logs[i].emitter==address(vault) && logs[i].topics.length==2 &&
            logs[i].topics[0]==keccak256("FeesCollected(uint256,uint256,uint256)") && uint256(logs[i].topics[1])==bucket){
            ++receipts;(uint256 a0,uint256 a1)=abi.decode(logs[i].data,(uint256,uint256));received0+=a0;received1+=a1;
        }
        assertEq(receipts,2,"harvest before close and after balancing existing main");
        _assertAllocation(bucket,address(0),received0,s.ethAllocation);_assertAllocation(bucket,address(token),received1,s.zzzAllocation);
        assertEq(_consolidationMainStructure(bucket),s.mainStructure,"unchanged main identity/geometry/clock");
        assertGt(positions.getPositionLiquidity(s.position.lpTokenId),s.mainL,"positive main L delta");
        assertEq(vault.sharesOf(id),s.shares);assertEq(vault.bucketTotalShares(bucket),s.supply);
        assertEq(manager.secondaryId(s.position.lpTokenId),0);assertEq(manager.activeSecondaryCount(),0);
        if(aux!=0){vm.expectRevert();positions.ownerOf(aux);}
        assertFalse(policy.enabled(pool));assertFalse(policy.configurationPending(bucket));
        assertTrue(policy.controlFingerprint(pool)!=s.control,"manual reinvest invalidates prior sampled evidence even already OFF");
        assertEq(policy.appliedRevision(s.position.lpTokenId),policy.geometryRevision(pool));
        assertEq(vault.migrationBudget().lastCompound(bucket),block.timestamp,"coordinate later compound");
        assertEq(migration.parkingNonce(bucket),s.nonce+1);assertEq(migration.custodyEpoch(bucket),s.epoch+1);
        assertTrue(access.paused());assertFalse(vault.migrationBudget().emergencyActive());assertFalse(migration.consolidationActive());
        assertEq(address(this).balance,s.operatorETH);assertEq(token.balanceOf(address(this)),s.operatorZZZ);
        assertEq(token.allowance(address(vault),address(manager)),0);assertEq(token.allowance(address(vault),manager.positionOperator()),0);
        _residualAuditPhysical(bucket,false);
    }
    function testResidualConsolidationNormalMergesModeOnBeforeCooldownAndKeepsFundedClaims() public {
        (uint256 alice,uint256 bucket,uint256 main,)=_hybrid();uint256 bob=_mint(BOB);_contribute(BOB,bob,500 ether,false);
        uint256 bobShares=vault.sharesOf(bob);core.unlock(abi.encode(uint8(2),Q96));
        uint256 principal=_residualAuditPrincipalValue(bucket);EmergencyRebalance memory r=_consolidationReview(bucket,false);
        assertLt(block.timestamp,uint256(vault.group(bucket).lastRebalance)+43200);assertTrue(policy.enabled(pool));
        assertFalse(vault.migrationBudget().compoundReady(bucket));assertFalse(strategy.rebalanceReady(bucket));
        access.setPaused(true);_consolidateAndAssert(alice,bucket,r,false);
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(vault.sharesOf(bob),bobShares);
        assertGe(_residualAuditPrincipalValue(bucket),Math.mulDiv(principal,9700,10000));
        assertGt(rewards.claimable(alice,address(0)),0);assertGt(rewards.claimable(bob,address(0)),0);
        _claimExactly(alice,ALICE,address(0));_claimExactly(bob,BOB,address(0));
    }
    function testResidualConsolidationAcknowledgesOffButPreservesIndependentPendingMainWidth() public {
        (uint256 id,uint256 bucket,,)=_hybrid();policy.setMode(pool,false,keccak256("TEST PRE-DISABLED MODE"));
        registry.setRange(2500);assertTrue(policy.configurationPending(bucket));assertTrue(strategy.rangeUpdatePending(bucket));
        EmergencyRebalance memory r=_consolidationReview(bucket,false);access.setPaused(true);_consolidateAndAssert(id,bucket,r,false);
        assertTrue(strategy.rangeUpdatePending(bucket),"unchanged main cannot apply different desired width");
    }
    function _consolidateInventory(bool converted) private {
        (uint256 id,uint256 bucket,,uint256 aux)=_hybrid();(int24 lower,int24 upper)=manager.ticks(aux);
        _move(TickMath.getSqrtPriceAtTick(converted?upper+200:int24((int256(lower)+int256(upper))/2)));
        (uint256 a0,uint256 a1)=manager.amounts(aux);if(converted){assertEq(a0,0);assertGt(a1,0);}else{assertGt(a0,0);assertGt(a1,0);}
        EmergencyRebalance memory r=_consolidationReview(bucket,false);access.setPaused(true);_consolidateAndAssert(id,bucket,r,false);
    }
    function testResidualConsolidationHandlesMixedResidualInventory() public {_consolidateInventory(false);}
    function testResidualConsolidationHandlesFullyConvertedResidualInventory() public {_consolidateInventory(true);}
    function testResidualConsolidationRepairsIdleFromEarlierRawCloseWithoutCompoundRelease() public {
        (uint256 id,uint256 bucket,uint256 main,)=_hybrid();core.unlock(abi.encode(uint8(2),Q96));
        ZZZMigration.ParkingRequest memory raw=_residualReview(bucket);
        access.setPaused(true);migration.closeResidual(raw);assertEq(manager.secondaryId(main),0);
        assertGt(fees.compoundBalance(bucket,address(0))+fees.compoundBalance(bucket,address(token)),0,"nonvacuous retained compound reserve");
        Position memory p=vault.group(bucket);assertGt(p.idle0+p.idle1,0);uint128 oldL=positions.getPositionLiquidity(main);
        EmergencyRebalance memory r=_consolidationReview(bucket,false);_consolidateAndAssert(id,bucket,r,false);
        assertGt(positions.getPositionLiquidity(main),oldL);assertLt(vault.group(bucket).idle0+vault.group(bucket).idle1,p.idle0+p.idle1);
    }
    function testResidualConsolidationForcedExplicitlyAcceptsInactiveMainWithUnavailableFeedsAndDisabledOperations() public {
        (uint256 id,uint256 bucket,uint256 main,)=_hybrid();access.setPaused(true);
        ethA.set(0,block.timestamp,block.timestamp);ethB.set(0,block.timestamp,block.timestamp);
        EmergencyRebalance memory r=_consolidationReview(bucket,false);bytes32 beforeState=_consolidationStateHash(id,bucket);
        vm.expectCall(address(oracle),abi.encodeCall(ZZZOracle.price,(address(0))));vm.expectRevert();migration.consolidateResidual(r,false);
        assertEq(_consolidationStateHash(id,bucket),beforeState);_prices();registry.setOperations(false);
        r=_consolidationReview(bucket,false);beforeState=_consolidationStateHash(id,bucket);
        vm.expectCall(address(strategy),abi.encodeCall(ZZZStrategy.target,(pool)));vm.expectRevert();migration.consolidateResidual(r,false);
        assertEq(_consolidationStateHash(id,bucket),beforeState);
        (,int24 upper)=manager.ticks(main);_move(TickMath.getSqrtPriceAtTick(upper+200));
        ethA.set(0,block.timestamp,block.timestamp);ethB.set(0,block.timestamp,block.timestamp);
        zzzA.set(0,block.timestamp,block.timestamp);zzzB.set(0,block.timestamp,block.timestamp);
        r=_consolidationReview(bucket,true);_consolidateAndAssert(id,bucket,r,true);
        (,int24 tick,,)=state.getSlot0(PoolId.wrap(pool));assertGe(tick,upper,"force does not pretend to recenter the unchanged main");
    }
    function testResidualConsolidationForcedExplicitSwapRetainsChosenFinancialChecks() public {
        (uint256 id,uint256 bucket,,)=_hybrid();EmergencyRebalance memory r=_consolidationExplicitReview(bucket,14);
        assertGt(r.amountIn,0);
        access.setPaused(true);_consolidateAndAssert(id,bucket,r,true);
    }
    function testResidualConsolidationRetainedSampleWorksAndIdleOnlyOffCompletionInvalidatesOldEvidence() public {
        (uint256 id,uint256 bucket,,uint256 aux)=_hybrid();(int24 lower,int24 upper)=manager.ticks(aux);
        _move(TickMath.getSqrtPriceAtTick(int24((int256(lower)+int256(upper))/2)));
        EmergencyRebalance memory r=_consolidationReview(bucket,true);access.setPaused(true);_consolidateAndAssert(id,bucket,r,true);
        assertGt(vault.group(bucket).idle0+vault.group(bucket).idle1,0,"forced no-swap leaves meaningful same-bucket idle");
        access.setPaused(false);_move(uint160(uint256(vault.group(bucket).centerX96)*83/100));_longReady(bucket);
        (uint8 side,bytes32 oldIdentity,bool manual)=strategy.rebalanceConfirmation().condition(bucket);
        assertGt(side,0);assertFalse(manual);assertTrue(strategy.rebalanceConfirmation().ready(bucket));
        r=_consolidationExplicitReview(bucket,16);access.setPaused(true);_consolidateAndAssert(id,bucket,r,true);access.setPaused(false);
        bytes32 nextIdentity;(side,nextIdentity,manual)=strategy.rebalanceConfirmation().condition(bucket);
        assertGt(side,0);assertFalse(manual);assertTrue(nextIdentity!=oldIdentity);
        assertFalse(strategy.rebalanceConfirmation().ready(bucket),"old sample cannot survive manual idle reinvest");
    }
    function testResidualConsolidationControlFullEmergencyRetainsPositiveSampleThroughBudgetCaller() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();uint256 shares=vault.sharesOf(id);
        _move(uint160(uint256(vault.group(bucket).centerX96)*83/100));_longReady(bucket);
        assertTrue(strategy.rebalanceConfirmation().ready(bucket));EmergencyRebalance memory r=_reviewForcedSingle(bucket);r.checks=30;
        uint256 earned=rewards.claimable(id,address(0));access.setPaused(true);migration.emergencyRebalance(r);
        uint256 replacement=vault.group(bucket).lpTokenId;assertTrue(replacement!=main);assertEq(manager.secondaryId(replacement),0);
        assertEq(manager.activeSecondaryCount(),0);assertEq(vault.sharesOf(id),shares);assertGe(rewards.claimable(id,address(0)),earned);
        vm.expectRevert();positions.ownerOf(main);vm.expectRevert();positions.ownerOf(aux);
        assertFalse(vault.migrationBudget().emergencyActive());assertTrue(access.paused());
    }
    function testResidualConsolidationRejectsAuthorityMalformedReviewAndReplay() public {
        (uint256 id,uint256 bucket,,)=_hybrid();EmergencyRebalance memory r=_consolidationReview(bucket,false);
        vm.expectRevert();migration.consolidateResidual(r,false);access.setPaused(true);bytes32 expected=_consolidationStateHash(id,bucket);
        vm.prank(ALICE);vm.expectRevert();migration.consolidateResidual(r,false);assertEq(_consolidationStateHash(id,bucket),expected);
        vm.expectRevert();vault.emergencyRebalance(bucket,1,r.deadline);
        vm.expectRevert();policy.completeConsolidation();
        r.checks=0;vm.expectRevert();migration.consolidateResidual(r,false);r=_consolidationReview(bucket,false);
        r.lower+=200;vm.expectRevert();migration.consolidateResidual(r,false);r=_consolidationReview(bucket,false);
        r.custodyHash=bytes32(uint256(123));vm.expectRevert();migration.consolidateResidual(r,false);r=_consolidationReview(bucket,false);
        r.amountIn=1;vm.expectRevert();migration.consolidateResidual(r,false);r=_consolidationReview(bucket,false);
        r.minimumLiquidity=0;vm.expectRevert();migration.consolidateResidual(r,false);r=_consolidationReview(bucket,false);
        r.reviewHash=bytes32(0);vm.expectRevert();migration.consolidateResidual(r,false);r=_consolidationReview(bucket,false);
        r.deadline=block.timestamp-1;vm.expectRevert();migration.consolidateResidual(r,false);r=_consolidationReview(bucket,false);
        access.setPreparation(true);vm.expectRevert();migration.consolidateResidual(r,false);access.setPreparation(false);
        access.setCanonicalState(1);vm.expectRevert();migration.consolidateResidual(r,false);access.setCanonicalState(0);
        assertEq(_consolidationStateHash(id,bucket),expected);_consolidateAndAssert(id,bucket,r,false);
        vm.expectRevert();migration.consolidateResidual(r,false);
    }
    function testResidualConsolidationFloorOrCallbackFailureRollsBackBurnModeFeesAndNonce() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();core.unlock(abi.encode(uint8(2),Q96));
        access.setPaused(true);EmergencyRebalance memory r=_consolidationReview(bucket,false);bytes32 expected=_consolidationStateHash(id,bucket);
        r.minimumLiquidity=type(uint128).max;vm.expectRevert();migration.consolidateResidual(r,false);
        assertEq(_consolidationStateHash(id,bucket),expected);assertEq(positions.ownerOf(aux),address(vault));
        r=_consolidationReview(bucket,false);residualCallbackBucket=bucket;uint8[3] memory kinds=[uint8(1),uint8(2),uint8(4)];
        bytes32 maintenance=ProtocolPolicyFixture.bind(address(access)).maintenanceFingerprint();
        for(uint256 i;i<kinds.length;++i){positions.configureBurnCallback(address(this),aux,kinds[i]);
            vm.expectCall(address(this),abi.encodeCall(this.residualBurnCallback,(kinds[i])));vm.expectRevert();migration.consolidateResidual(r,false);
            assertEq(_consolidationStateHash(id,bucket),expected);assertEq(manager.secondaryId(main),aux);
            assertEq(ProtocolPolicyFixture.bind(address(access)).maintenanceFingerprint(),maintenance);
        }
    }
    function testResidualConsolidationCanReenableThenCreateAndConsolidateOnlyOneNewResidual() public {
        (uint256 id,uint256 bucket,uint256 originalMain,)=_hybrid();EmergencyRebalance memory r=_consolidationReview(bucket,false);
        access.setPaused(true);_consolidateAndAssert(id,bucket,r,false);access.setPaused(false);
        _contribute(ALICE,id,100 ether,true);policy.setMode(pool,true,keccak256("TEST REENABLE AFTER CONSOLIDATION"));
        _move(uint160(uint256(vault.group(bucket).centerX96)*83/100));_longReady(bucket);vault.rebalance(bucket,1,block.timestamp+100);
        (uint256 main,uint256 aux)=_residualAuditPhysical(bucket,true);assertTrue(main!=originalMain);assertGt(aux,0);
        r=_consolidationReview(bucket,false);access.setPaused(true);_consolidateAndAssert(id,bucket,r,false);
    }

    function testConsolidationRacePausedReviewUsesLiveInventoryAfterExternalSwap() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();access.setPaused(true);
        EmergencyRebalance memory reviewed=_consolidationReview(bucket,false);
        uint128 mainL=positions.getPositionLiquidity(main);uint128 auxL=positions.getPositionLiquidity(aux);
        (uint256 old0,uint256 old1)=manager.amounts(aux);assertEq(old1,0);assertGt(old0,0);
        bytes32 physical=manager.executionPortfolioFingerprint(main);(int24 lower,int24 upper)=manager.ticks(aux);
        vm.warp(block.timestamp+30);_move(TickMath.getSqrtPriceAtTick(int24((int256(lower)+int256(upper))/2)));
        (uint256 live0,uint256 live1)=manager.amounts(aux);assertGt(live0,0);assertGt(live1,0);
        assertTrue(live0!=old0 || live1!=old1);assertEq(positions.getPositionLiquidity(main),mainL);assertEq(positions.getPositionLiquidity(aux),auxL);
        assertEq(manager.executionPortfolioFingerprint(main),physical);
        assertEq(migration.consolidationCustodyHash(bucket),reviewed.custodyHash,"market inventory drift is not custody mutation");
        uint256 liveValue=_residualAuditPrincipalValue(bucket);_consolidateAndAssert(id,bucket,reviewed,false);
        assertGe(_residualAuditPrincipalValue(bucket),Math.mulDiv(liveValue,9700,10000),"retention starts at execution inventory, not old preview");
        (lower,upper)=manager.ticks(aux);assertEq(lower,0);assertEq(upper,0,"raw burned-ID metadata is not current-main authentication");
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(positions.ownerOf(main),address(vault));
    }
    function testConsolidationRaceCapturedReviewRejectsBothExternalBoundaryCrossingsAtomically() public {
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();access.setPaused(true);
        EmergencyRebalance memory reviewed=_consolidationReview(bucket,false);(int24 lower,int24 upper)=manager.ticks(main);
        uint256 snapshot=vm.snapshotState();
        for(uint256 i;i<2;++i){
            if(i!=0)assertTrue(vm.revertToState(snapshot));
            vm.warp(block.timestamp+20);uint160 boundary=TickMath.getSqrtPriceAtTick(i==0?lower:upper);_move(boundary);
            (uint160 actual,int24 tick,,)=state.getSlot0(PoolId.wrap(pool));assertEq(actual,boundary);
            assertEq(tick,i==0?lower-1:upper,"actual v4 downward/upward exact-boundary stored tick");
            assertEq(migration.consolidationCustodyHash(bucket),reviewed.custodyHash);
            bytes32 beforeState=_consolidationStateHash(id,bucket);uint128 mainL=positions.getPositionLiquidity(main);uint128 auxL=positions.getPositionLiquidity(aux);
            vm.expectRevert(ZZZModule.InvalidState.selector);migration.consolidateResidual(reviewed,false);
            assertEq(_consolidationStateHash(id,bucket),beforeState);assertEq(positions.getPositionLiquidity(main),mainL);assertEq(positions.getPositionLiquidity(aux),auxL);
            assertEq(positions.ownerOf(main),address(vault));assertEq(positions.ownerOf(aux),address(vault));assertEq(manager.secondaryId(main),aux);
            (actual,tick,,)=state.getSlot0(PoolId.wrap(pool));assertEq(actual,boundary);assertEq(tick,i==0?lower-1:upper);
        }
    }
    function testConsolidationRaceGrowthActivationTransferClaimAndExpiryRequireCorrectFreshness() public {
        (uint256 alice,uint256 bucket,uint256 main,uint256 aux)=_hybrid();uint256 bob=_mint(BOB);
        core.unlock(abi.encode(uint8(2),Q96));EmergencyRebalance memory staleGrowth=_consolidationReview(bucket,false);
        uint128 auxL=positions.getPositionLiquidity(aux);_contribute(ALICE,alice,100 ether,true);
        assertTrue(migration.consolidationCustodyHash(bucket)!=staleGrowth.custodyHash);assertEq(positions.getPositionLiquidity(aux),auxL);
        access.setPaused(true);bytes32 expected=_consolidationStateHash(alice,bucket);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);migration.consolidateResidual(staleGrowth,false);assertEq(_consolidationStateHash(alice,bucket),expected);
        access.setPaused(false);EmergencyRebalance memory staleActivation=_consolidationReview(bucket,false);_contribute(BOB,bob,500 ether,false);
        assertTrue(migration.consolidationCustodyHash(bucket)!=staleActivation.custodyHash);assertEq(positions.getPositionLiquidity(aux),auxL);
        assertEq(rewards.claimable(bob,address(0)),0,"new activation cannot claim earlier native fees");
        assertEq(rewards.claimable(bob,address(token)),0,"new activation cannot claim earlier ZZZ fees");
        assertGt(rewards.claimable(alice,address(0)),0);access.setPaused(true);expected=_consolidationStateHash(alice,bucket);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);migration.consolidateResidual(staleActivation,false);assertEq(_consolidationStateHash(alice,bucket),expected);
        EmergencyRebalance memory reviewed=_consolidationReview(bucket,false);uint256 aliceShares=vault.sharesOf(alice);uint256 bobShares=vault.sharesOf(bob);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,alice);assertEq(migration.consolidationCustodyHash(bucket),reviewed.custodyHash);
        vm.prank(ALICE);vm.expectRevert(ZZZModule.Unauthorized.selector);rewards.claim(alice,address(0));
        assertGt(_claimExactly(alice,BOB,address(0)),0);assertEq(rewards.claimable(bob,address(0)),0);
        assertEq(migration.consolidationCustodyHash(bucket),reviewed.custodyHash,"current-owner claims are separate from principal review");
        uint256[2] memory input=_reviewGrowth(main,100 ether);uint256 ownerETH=BOB.balance;uint256 ownerZZZ=token.balanceOf(BOB);
        vm.startPrank(BOB);token.approve(address(vault),input[1]);vm.expectRevert(ZZZModule.Paused.selector);
        vault.increase{value:input[0]}(bob,input[0],input[1],1,block.timestamp+100);vm.stopPrank();
        assertEq(BOB.balance,ownerETH);assertEq(token.balanceOf(BOB),ownerZZZ);
        vm.warp(reviewed.deadline+1);expected=_consolidationStateHash(alice,bucket);
        vm.expectRevert(ZZZModule.Expired.selector);migration.consolidateResidual(reviewed,false);assertEq(_consolidationStateHash(alice,bucket),expected);
        reviewed=_consolidationReview(bucket,false);_consolidateAndAssert(alice,bucket,reviewed,false);
        assertEq(vault.sharesOf(alice),aliceShares);assertEq(vault.sharesOf(bob),bobShares);assertEq(vault.group(bucket).lpTokenId,main);
        assertGt(rewards.claimable(bob,address(0)),0,"later harvested swap fees belong to current active cohort");
        _claimExactly(alice,BOB,address(0));_claimExactly(bob,BOB,address(0));
    }

    event MovingMarketRouteProof(bytes encoded);
    /// @dev A reachable, deliberately guarded-bypass recovery setup. Existing
    /// full emergency creates a SMALL active main and LARGE attributed idle;
    /// it does not forge balances or relax the later normal operation's guards.
    function _movingRecoveryMain() private returns(uint256 id,uint256 bucket,uint256 main) {
        (id,bucket,main,)=_hybrid();(int24 oldLower,)=manager.ticks(main);
        _move(TickMath.getSqrtPriceAtTick(oldLower-200));(,int24 tick,,)=state.getSlot0(PoolId.wrap(pool));
        int24 aligned=(tick/200)*200;EmergencyRebalance memory r;
        r.bucket=bucket;r.custodyHash=migration.emergencyCustodyHash(bucket);r.lower=aligned-200;r.upper=aligned+200;
        r.swapPool=pool;r.zeroForOne=true;r.amountIn=1 ether;r.minimumOut=1;r.minimumLiquidity=1;
        r.deadline=block.timestamp+100;r.reviewHash=keccak256("TEST ONLY DELIBERATE PARTIAL RECOVERY BEFORE NORMAL REINVEST");
        access.setPaused(true);migration.emergencyRebalance(r);main=vault.group(bucket).lpTokenId;
        assertEq(manager.secondaryId(main),0);assertGt(vault.group(bucket).idle0,100 ether);
        uint128 mainL=positions.getPositionLiquidity(main);core.unlock(abi.encode(uint8(4),Q96));assertEq(positions.getPositionLiquidity(main),mainL);
        (int24 lower,)=manager.ticks(main);uint160 epsilon=uint160(uint256(Q96)*201/(2*1e18));
        _move(TickMath.getSqrtPriceAtTick(lower)+epsilon);(,tick,,)=state.getSlot0(PoolId.wrap(pool));assertEq(tick,lower);
    }
    function _movingAlternate() private returns(bytes32 destination) {
        destination=registry.admitTarget();targetKey=CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),3000,200,IHooks(address(0)));
        core.initialize(targetKey,manager.spot(pool));core.unlock(abi.encode(uint8(3),Q96));strategy.setRangeOrientation(destination,1);
        bytes32[] memory venues=new bytes32[](2);venues[0]=pool;venues[1]=destination;
        manager.balancingRouter().configureExecutionPools(venues,keccak256("TEST ONLY TWO ACTUAL REVIEWED VENUES"));
    }
    function _movingRebuildFees(uint256 bucket,Vm.Log[] memory logs,uint256[4] memory e,uint256[4] memory z)
        private view returns(uint256 released0,uint256 released1) {
        uint256 count;uint256 a0;uint256 a1;
        for(uint256 i;i<logs.length;++i)if(logs[i].emitter==address(vault) && logs[i].topics.length==2 &&
            logs[i].topics[0]==keccak256("FeesCollected(uint256,uint256,uint256)") && uint256(logs[i].topics[1])==bucket){
            ++count;(uint256 f0,uint256 f1)=abi.decode(logs[i].data,(uint256,uint256));a0+=f0;a1+=f1;
        }
        assertEq(count,1);uint256 u0=(e[0]+a0)/20;uint256 u1=(z[0]+a1)/20;
        assertEq(fees.dust(bucket,address(0)),(e[0]+a0)%20);assertEq(fees.dust(bucket,address(token)),(z[0]+a1)%20);
        assertEq(fees.buybackBalance(address(0)),e[2]+u0);assertEq(fees.buybackBalance(address(token)),z[2]+u1);
        assertEq(rewards.liabilities(address(0)),e[3]+18*u0);assertEq(rewards.liabilities(address(token)),z[3]+18*u1);
        assertEq(fees.compoundBalance(bucket,address(0)),0);assertEq(fees.compoundBalance(bucket,address(token)),0);
        return(e[1]+u0,z[1]+u1);
    }
    function testMovingMarketOffRebuildUsesExecutionStateAfterPriceAndContributionChanges() public {
        (uint256 alice,uint256 bucket,uint256 oldMain,uint256 oldAux)=_hybrid();uint256 bob=_mint(BOB);
        policy.setMode(pool,false,keccak256("TEST ONLY PENDING WHOLE SINGLE MERGE"));
        vm.warp(uint256(vault.group(bucket).lastRebalance)+43200);_prices();assertTrue(strategy.rebalanceReady(bucket));
        bytes memory prepared=abi.encodeCall(ZZZVault.rebalance,(bucket,uint128(1),block.timestamp+300));
        uint64 oldClock=vault.group(bucket).lastRebalance;uint128 auxL=positions.getPositionLiquidity(oldAux);
        vm.warp(block.timestamp+30);_move(uint160(uint256(manager.spot(pool))*101/100));
        uint256[2] memory amount=_reviewGrowth(oldMain,500 ether);vm.startPrank(BOB);token.approve(address(vault),amount[1]);
        vault.activate{value:amount[0]}(bob,pool,amount[0],amount[1],1,block.timestamp+100);vm.stopPrank();
        _contribute(ALICE,alice,100 ether,true);assertEq(vault.group(bucket).lastRebalance,oldClock);assertEq(positions.getPositionLiquidity(oldAux),auxL);
        uint256 aliceShares=vault.sharesOf(alice);uint256 bobShares=vault.sharesOf(bob);assertGt(bobShares,0);
        core.unlock(abi.encode(uint8(2),Q96));
        uint256[4] memory e=_allocationBefore(bucket,address(0));uint256[4] memory z=_allocationBefore(bucket,address(token));
        (uint256 deployed,uint256 idle)=vault.migrationBudget().nav(bucket);vm.recordLogs();
        (bool ok,bytes memory reason)=address(vault).call(prepared);if(!ok)assembly("memory-safe"){revert(add(reason,32),mload(reason))}
        (uint256 c0,uint256 c1)=_movingRebuildFees(bucket,vm.getRecordedLogs(),e,z);
        assertGt(c0+c1,0,"funded compounding actually enters the rebuilt principal");
        uint256 starting=deployed+idle+oracle.value(address(0),c0)+oracle.value(address(token),c1);
        (uint256 afterLP,uint256 afterIdle)=vault.migrationBudget().nav(bucket);assertGe(afterLP+afterIdle,Math.mulDiv(starting,9700,10000,Math.Rounding.Ceil));
        (uint256 main,)=_residualAuditPhysical(bucket,false);assertTrue(main!=oldMain);assertEq(manager.secondaryId(oldMain),0);
        (int24 lower,int24 upper)=manager.ticks(main);(,int24 tick,,)=state.getSlot0(PoolId.wrap(pool));assertGe(tick,lower);assertLt(tick,upper);
        assertEq(vault.sharesOf(alice),aliceShares);assertEq(vault.sharesOf(bob),bobShares);assertEq(vault.bucketTotalShares(bucket),aliceShares+bobShares);
        assertEq(vault.group(bucket).lastRebalance,block.timestamp);assertFalse(policy.configurationPending(bucket));
        vm.expectRevert();positions.ownerOf(oldMain);vm.expectRevert();positions.ownerOf(oldAux);
    }
    function testMovingMarketManualSelectsActiveAlternateInsteadOfInactiveLegacyCandidate() public {
        (uint256 id,uint256 bucket,uint256 main)=_movingRecoveryMain();bytes32 alternative=_movingAlternate();
        Position memory p=vault.group(bucket);(int24 lower,int24 upper)=manager.ticks(main);ZZZLPBalancer router=manager.balancingRouter();
        vm.prank(address(manager));ZZZLPBalancer.Plan memory legacy=router.plan(pool,lower,upper,p.idle0,p.idle1);
        uint256[4] memory marks;vm.prank(address(manager));ZZZLPBalancer.Plan memory active=router.planReplacement(pool,lower,upper,p.idle0,p.idle1,10000,marks);
        emit MovingMarketRouteProof(abi.encode(manager.spot(pool),lower,upper,p.idle0,p.idle1,legacy,active,alternative));
        assertEq(legacy.poolId,pool);assertLt(legacy.targetSqrtAfter,TickMath.getSqrtPriceAtTick(lower));
        assertEq(active.poolId,alternative);assertEq(active.targetSqrtAfter,manager.spot(pool));
        EmergencyRebalance memory r=_consolidationReview(bucket,false);
        vm.expectCall(address(router),abi.encodePacked(ZZZLPBalancer.planReplacement.selector));_consolidateAndAssert(id,bucket,r,false);
        (,int24 tick,,)=state.getSlot0(PoolId.wrap(pool));assertGe(tick,lower);assertLt(tick,upper);
    }
    function testMovingMarketNoActiveFeasibleRouteRestoresPrincipalFeesAndReview() public {
        (uint256 id,uint256 bucket,uint256 main)=_movingRecoveryMain();Position memory p=vault.group(bucket);
        (int24 lower,int24 upper)=manager.ticks(main);ZZZLPBalancer router=manager.balancingRouter();
        vm.prank(address(manager));ZZZLPBalancer.Plan memory legacy=router.plan(pool,lower,upper,p.idle0,p.idle1);
        emit MovingMarketRouteProof(abi.encode(manager.spot(pool),lower,upper,p.idle0,p.idle1,legacy));
        assertEq(legacy.poolId,pool);assertLt(legacy.targetSqrtAfter,TickMath.getSqrtPriceAtTick(lower));
        EmergencyRebalance memory r=_consolidationReview(bucket,false);bytes32 beforeState=_consolidationStateHash(id,bucket);
        vm.expectCall(address(router),abi.encodePacked(ZZZLPBalancer.planReplacement.selector));vm.expectRevert();migration.consolidateResidual(r,false);
        assertEq(_consolidationStateHash(id,bucket),beforeState);assertEq(migration.consolidationCustodyHash(bucket),r.custodyHash);
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(manager.secondaryId(main),0);assertTrue(access.paused());
    }
}
