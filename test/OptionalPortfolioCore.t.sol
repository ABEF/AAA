// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
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
        nft=new ZZZNFT(address(access),"ipfs://TEST-ONLY/");membership=new ZZZMembership(address(access));
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
    function unlockCallback(bytes calldata data)external returns(bytes memory){
        require(msg.sender==address(core));(uint8 mode,uint160 q)=abi.decode(data,(uint8,uint160));BalanceDelta delta;
        if(mode==0 || mode==3)(delta,)=core.modifyLiquidity(mode==0?key:targetKey,ModifyLiquidityParams(-60000,60000,int256(1_000_000 ether),bytes32(0)),"");
        else if(mode==2)delta=core.donate(key,10 ether,10 ether,"");
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
        // A selector-prefix witness proves the actual mint is reached. Amounts
        // include real already-earned compound, so no guessed input is supplied.
        vm.expectCall(manager.positionOperator(),abi.encodePacked(ZZZLPPositionExecutor.mint.selector));
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
        vm.prank(address(manager));ZZZLPBalancer.Plan memory p=router.planPartial(pool,lower,upper,total-scarce,scarce,6001,marks);
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
        (uint256 id,uint256 bucket,uint256 main,uint256 aux)=_hybrid();access.setPaused(true);
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
        request=_residualReview(bucket);request.minimum0=0;request.minimum1=0;vm.expectRevert();migration.closeResidual(request);
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
        (uint256 id,uint256 bucket,,)=_hybrid();ZZZMigration.ParkingRequest memory request=_residualReview(bucket);
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
}
