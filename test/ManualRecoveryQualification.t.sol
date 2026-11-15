// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey as CoreKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta, BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams, SwapParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {StateView} from "@uniswap/v4-periphery/src/lens/StateView.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {IPositionDescriptor} from "@uniswap/v4-periphery/src/interfaces/IPositionDescriptor.sol";
import {IWETH9} from "@uniswap/v4-periphery/src/interfaces/external/IWETH9.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {ZZZV4SpotPriceFeed} from "../src/ZZZV4SpotPriceFeed.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZSeaDropMint} from "../src/ZZZSeaDropMint.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZRoyaltyFactory} from "../src/ZZZRoyaltyFactory.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZSeaDrop} from "../src/interfaces/IZZZSeaDrop.sol";
import {EmergencyRebalance} from "../src/interfaces/IZZZEmergency.sol";
import {Position, PositionStatus, Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockFeed, MockToken} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {FactualPermit} from "./LiquidityFactualChecks.t.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {VerifiedSeaDropV1} from "./fixtures/VerifiedSeaDropV1.sol";

/// @dev TEST ONLY: preserve real Registry admission/accounting/policy code, but
/// replace Robinhood's fixed public-network pins with these exact owned local
/// dependencies and the one fixture ZZZ. This is not public venue qualification.
contract RecoveryNativeRegistry is ZZZPoolRegistry {
    address private immutable localCore;
    address private immutable localPositions;
    address private immutable localState;
    address private immutable localPermit;
    bytes32 private immutable coreHash;
    bytes32 private immutable positionsHash;
    bytes32 private immutable stateHash;
    bytes32 private immutable permitHash;
    constructor(address controller,address core,address positions,address state,address permit)
        ZZZPoolRegistry(controller) {
        localCore=core;localPositions=positions;localState=state;localPermit=permit;
        coreHash=core.codehash;positionsHash=positions.codehash;stateHash=state.codehash;permitHash=permit.codehash;
    }
    function configureFixture(PoolConfig calldata c) external onlyGovernance principalOperating returns(bytes32) {
        if(c.key.currency0!=address(0) || c.key.currency1!=activationAssets.zzz() ||
            c.key.currency1==address(0) || c.key.hooks!=address(0))revert InvalidConfiguration();
        _nativeBindings();
        return _configure(c,address(0),c.key.currency1);
    }
    function _nativeBindings() internal view override {
        if(block.chainid!=31337 || localCore.codehash!=coreHash || localPositions.codehash!=positionsHash ||
            localState.codehash!=stateHash || localPermit.codehash!=permitHash)revert InvalidConfiguration();
        ZZZLiquidityManager m=ZZZLiquidityManager(payable(access.module(Ids.LIQUIDITY)));
        if(address(m.poolManager())!=localCore || m.positionManager()!=localPositions ||
            address(m.stateView())!=localState || address(m.permit2())!=localPermit)revert InvalidConfiguration();
    }
}

/// @notice NEW controlled composition only. Real current Access/sealing,
/// mint2/V10, v4 core/periphery and LP accounting execute unchanged. Token,
/// publication/VRF/Permit2, depth and local-network admission are explicit seams.
/// No inherited historical test methods, public deployment or existing node.
contract ManualRecoveryQualificationTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    uint160 private constant Q96=2**96;
    uint256 private constant CAP=24_000_000;
    uint256 private constant PREFUND=12345;
    address private constant GOVERNANCE=address(0xA0A0);
    address private constant KEEPER=address(0xBEEF);
    address private constant OWNER=address(0xA11CE);
    address private constant SECOND_OWNER=address(0xB0B);
    bytes32 private constant REVIEW=keccak256("TEST ONLY manual recovery qualification");
    ZZZAccessController private access;
    RecoveryNativeRegistry private registry;
    MockToken private token;
    MockFeed private ethFirst;
    MockFeed private ethSecond;
    MockVRF private vrf;
    PoolManager private core;
    PoolManager private independentCore;
    StateView private state;
    StateView private independentState;
    PositionManager private posm;
    FactualPermit private permit;
    ZZZLPBalancer private router;
    ZZZLiquidityManager private manager;
    ZZZOracle private oracle;
    ZZZStrategy private strategy;
    ZZZV4SpotPriceFeed private referenceFeed;
    ZZZV4SpotPriceFeed private independentFeed;
    ZZZVault private vault;
    ZZZNFT private nft;
    ZZZRewards private rewards;
    ZZZMembership private members;
    ZZZFeeController private fees;
    ZZZMigration private migration;
    ZZZSeaDropMint private mintHelper;
    IZZZSeaDrop private seaDrop;
    CoreKey private targetKey;
    CoreKey private referenceKey;
    CoreKey private executionKey;
    bytes32 private target;
    bytes32 private referencePool;
    bytes32 private executionPool;
    uint256 private id;
    uint256 private secondId;
    uint256 private dormantId;
    uint256 private bucket;
    bytes32 private setupHash;
    string private setupPath;
    struct Before {
        Position position;uint256 residual;uint128 mainL;uint256 shares;uint256 secondShares;uint256 supply;
        uint256 compound0;uint256 compound1;uint256 liabilities0;uint256 liabilities1;
        uint256 buyback0;uint256 buyback1;uint64 lastCompound;uint64 nonce;uint64 epoch;
        uint256 royaltyWeight;uint256 secondRoyaltyWeight;uint256 royaltyTotal;
        uint256 firstClaim0;uint256 firstClaim1;uint256 secondClaim0;uint256 secondClaim1;
    }
    event RecoveryBindings(string[] roles,address[] components,bytes32[] hashes);
    event RecoveryAsset(address token,uint8 decimals);
    event RecoveryBaseline(string path,bytes32 hash);
    event RecoveryState(string label,string path,bytes32 deltaHash,uint256 blockNumber,uint256 timestamp,
        uint256 chainId,address governance,uint256 bucket,uint256[] nftIds,bytes32 setupHash);
    event RecoverySelected(string label,uint256 schema,string action,EmergencyRebalance request);
    event RecoveryUnsignedCall(string label,address sender,address destination,uint256 value,bytes data,
        uint256 cap,uint16 paddingBps,uint256 bucket,uint256[] nftIds);
    event RecoveryGas(string label,uint256 callGas,uint256 paddedGas);
    event RecoveryReferenceQuote(string label,uint256 output,uint128 liquidity,uint256 minimumOut,uint128 minimumLiquidity);

    receive() external payable {}
    function setUp() public {
        vm.chainId(31337);vm.warp(1_000_000);vm.deal(address(this),10_000_000 ether);
        vm.deal(GOVERNANCE,100 ether);vm.deal(KEEPER,100 ether);vm.deal(OWNER,10000 ether);
        vm.deal(SECOND_OWNER,10000 ether);
        access=new ZZZAccessController(GOVERNANCE,KEEPER,GOVERNANCE);
        ProtocolPolicyFixture.bind(address(access),address(0xCAFE));
        token=new MockToken(18);token.mint(address(this),10_000_000 ether);
        core=new PoolManager(address(this));independentCore=new PoolManager(address(this));
        state=new StateView(IPoolManager(address(core)));independentState=new StateView(IPoolManager(address(independentCore)));
        permit=new FactualPermit();
        posm=new PositionManager(IPoolManager(address(core)),IAllowanceTransfer(address(permit)),100000,
            IPositionDescriptor(address(0)),IWETH9(address(0)));
        router=new ZZZLPBalancer(address(access),address(core),address(state));
        manager=new ZZZLiquidityManager(address(access),address(posm),address(state),address(core),address(permit),address(router));
        oracle=new ZZZOracle(address(access),address(0));
        strategy=new ZZZStrategy(address(access),address(new ZZZPortfolioPolicy(address(access))),address(new ZZZRebalanceConfirmation(address(access))));
        registry=new RecoveryNativeRegistry(address(access),address(core),address(posm),address(state),address(permit));
        vault=new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        nft=new ZZZNFT(address(access),"ipfs://TEST-ONLY-MANUAL-RECOVERY/",address(new ZZZNFTMetadata(address(access))));
        rewards=new ZZZRewards(address(access));members=new ZZZMembership(address(access));
        fees=new ZZZFeeController(address(access));migration=new ZZZMigration(address(access));
        access.bind(Ids.VAULT,address(vault));access.bind(Ids.NFT,address(nft));access.bind(Ids.LIQUIDITY,address(manager));
        access.bind(Ids.REWARDS,address(rewards));access.bind(Ids.MEMBERSHIP,address(members));access.bind(Ids.FEES,address(fees));
        access.bind(Ids.STRATEGY,address(strategy));access.bind(Ids.COMPOUNDER,address(new ZZZCompounder(address(access))));
        access.bind(Ids.BUYBACK,address(new ZZZBuyback(address(access),address(token),1_000_000e18)));
        access.bind(Ids.MIGRATION,address(migration));access.bind(Ids.ORACLE,address(oracle));access.bind(Ids.POOLS,address(registry));
        ethFirst=new MockFeed(8,1e8);ethSecond=new MockFeed(8,1e8);
        targetKey=_key(10020,200);referenceKey=_key(500,10);executionKey=_key(1000,20);
        target=keccak256(abi.encode(targetKey));referencePool=keccak256(abi.encode(referenceKey));executionPool=keccak256(abi.encode(executionKey));
        core.initialize(targetKey,Q96);core.initialize(referenceKey,Q96);core.initialize(executionKey,Q96);independentCore.initialize(referenceKey,Q96);
        _external(core,targetKey,100_000 ether);_external(core,referenceKey,1_000_000 ether);
        _external(core,executionKey,1_000_000 ether);
        _external(independentCore,referenceKey,2_000_000 ether);
        referenceFeed=_feed(core,state,referenceKey,ethFirst);independentFeed=_feed(independentCore,independentState,referenceKey,ethSecond);
        oracle.setDualFeed(address(0),_source(address(ethFirst),8,"first ETH"),_source(address(ethSecond),8,"second ETH"),300,REVIEW);
        oracle.setDualFeed(address(token),_source(address(referenceFeed),18,"first independent ZZZ"),
            _source(address(independentFeed),18,"second independent ZZZ"),300,REVIEW);
        registry.activationAssets().configureZZZ(address(token),address(token).codehash,REVIEW);
        oracle.setExecutionSource(address(referenceFeed),true,address(referenceFeed).codehash,REVIEW);
        oracle.setExecutionSource(address(independentFeed),true,address(independentFeed).codehash,REVIEW);
        rewards.addAsset(address(token));migration.configureZZZ(address(token),address(token).codehash,REVIEW);
        _admit(targetKey,true);_admit(referenceKey,false);_admit(executionKey,false);
        vrf=new MockVRF();ProtocolPolicyFixture.randomness(address(access),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        seaDrop=IZZZSeaDrop(VerifiedSeaDropV1.install(vm));
        mintHelper=new ZZZSeaDropMint(address(access),address(nft),address(seaDrop),address(seaDrop).codehash);
        nft.setSeaDropMint(address(mintHelper));
        ZZZSeaDropMint.MintConfig memory c;
        c.publicWalletLimit=10;c.feeBps=1000;c.maxBatch=10;c.feeRecipient=address(0xFEE);
        c.teamStart=uint48(block.timestamp-4);c.teamEnd=uint48(block.timestamp-3);
        c.allowlistStart=uint48(block.timestamp-2);c.allowlistEnd=uint48(block.timestamp-1);
        c.publicStart=uint48(block.timestamp);c.publicEnd=uint48(block.timestamp+100);
        c.allowedPayersHash=keccak256(abi.encode(new address[](0)));
        mintHelper.configure(c,uint128(0.05 ether),REVIEW);nft.setMintEnd(c.publicEnd);
        nft.updatePublicDrop(address(seaDrop),mintHelper.expectedPublicDrop());
        nft.updateCreatorPayoutAddress(address(seaDrop),address(0xCAFE));
        nft.updateAllowedFeeRecipient(address(seaDrop),c.feeRecipient,true);
        CanonicalFixture.bind(address(access));access.seal();
        assertEq(access.bootstrap(),address(0));assertEq(GOVERNANCE.code.length,0);
        bytes32[] memory routes=new bytes32[](1);routes[0]=executionPool;
        vm.startPrank(GOVERNANCE);router.configureExecutionPools(routes,REVIEW);strategy.setRangeOrientation(target,1);
        strategy.portfolioPolicy().setMode(target,true,REVIEW);
        strategy.rebalanceConfirmation().configure(600,300,REVIEW);vm.stopPrank();
        vm.prank(OWNER);seaDrop.mintPublic{value:0.15 ether}(address(nft),c.feeRecipient,address(0),3);
        id=nft.tokenAtOrdinal(1);secondId=nft.tokenAtOrdinal(2);dormantId=nft.tokenAtOrdinal(3);
        vm.prank(OWNER);nft.transferFrom(OWNER,SECOND_OWNER,secondId);
        vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
        vrf.fulfill(nft.requestOf(secondId),0,0);nft.finalizeTraits(secondId);
        vrf.fulfill(nft.requestOf(dormantId),0,0);nft.finalizeTraits(dormantId);
        ZZZActivationEntry entry=registry.activationEntry();
        ZZZActivationEntry.Request memory activation=ZZZActivationEntry.Request(id,target,address(0),1000 ether,1,block.timestamp+100,false);
        bytes32 entryFingerprint=ProtocolPolicyFixture.bind(address(access)).entryFingerprint();
        vm.prank(OWNER);entry.executeReviewed{value:1000 ether,gas:20_000_000}(activation,300,entryFingerprint);
        activation.nftId=secondId;activation.amountIn=500 ether;
        vm.prank(SECOND_OWNER);entry.executeReviewed{value:500 ether,gas:20_000_000}(activation,300,entryFingerprint);
        bucket=vault.nftBucket(id);assertGt(bucket,0);assertEq(vault.sharesOf(dormantId),0);
        assertEq(vault.nftBucket(secondId),bucket);assertGt(vault.sharesOf(secondId),0);
        vm.deal(address(manager),PREFUND);token.mint(address(manager),PREFUND);
        vm.deal(manager.positionOperator(),PREFUND);token.mint(manager.positionOperator(),PREFUND);
        _exportSetup();
    }

    function _key(uint24 fee,int24 spacing) private view returns(CoreKey memory) {
        return CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),fee,spacing,IHooks(address(0)));
    }
    function _admit(CoreKey memory k,bool deposits) private {
        registry.configureFixture(PoolConfig(PoolKey(address(0),address(token),k.fee,k.tickSpacing,address(0)),
            deposits,true,5000,100,500,200,43200,1e18,1_000_000e18));
    }
    function _source(address feed,uint8 digits,string memory tag) private view returns(ZZZOracle.SourcePolicy memory) {
        return ZZZOracle.SourcePolicy(feed,feed.codehash,keccak256(bytes(tag)),3600,digits);
    }
    function _feed(PoolManager c,StateView s,CoreKey memory k,MockFeed eth) private returns(ZZZV4SpotPriceFeed) {
        ZZZV4SpotPriceFeed.Config memory x;
        x.core=address(c);x.expectedCoreCodeHash=address(c).codehash;x.stateView=address(s);x.expectedStateViewCodeHash=address(s).codehash;
        x.key=k;x.expectedPoolId=keccak256(abi.encode(k));x.zzz=address(token);x.expectedZZZCodeHash=address(token).codehash;
        x.ethUsdFeed=address(eth);x.expectedETHFeedCodeHash=address(eth).codehash;x.maxETHAge=3600;x.minimumLiquidity=1e18;x.reviewHash=REVIEW;
        return new ZZZV4SpotPriceFeed(x);
    }
    function _external(PoolManager c,CoreKey memory k,int256 l) private { c.unlock(abi.encode(uint8(0),k,l,uint160(0))); }
    function _to(PoolManager c,StateView s,CoreKey memory k,uint160 next) private {
        (uint160 current,,,)=s.getSlot0(PoolId.wrap(keccak256(abi.encode(k))));
        c.unlock(abi.encode(next<current?uint8(1):uint8(2),k,int256(2_000_000 ether),next));
    }
    function unlockCallback(bytes calldata data) external returns(bytes memory) {
        require(msg.sender==address(core)||msg.sender==address(independentCore));
        (uint8 action,CoreKey memory k,int256 amount,uint160 limit)=abi.decode(data,(uint8,CoreKey,int256,uint160));
        PoolManager c=PoolManager(msg.sender);BalanceDelta d;
        if(action==0)(d,)=c.modifyLiquidity(k,ModifyLiquidityParams(-60000,60000,amount,bytes32(0)),"");
        else d=c.swap(k,SwapParams(action==1,-amount,limit),"");
        _settle(c,k.currency0,d.amount0());_settle(c,k.currency1,d.amount1());return "";
    }
    function _settle(PoolManager c,Currency asset,int128 delta) private {
        if(delta>0)c.take(asset,address(this),uint256(int256(delta)));
        else if(delta<0){uint256 amount=uint256(-int256(delta));c.sync(asset);
            if(Currency.unwrap(asset)==address(0))assertEq(c.settle{value:amount}(),amount);
            else {token.transfer(address(c),amount);assertEq(c.settle(),amount);}}
    }
    function _fresh() private {ethFirst.set(1e8,block.timestamp,block.timestamp);ethSecond.set(1e8,block.timestamp,block.timestamp);}
    function _currentExportTime() private {
        uint256 timestamp=vm.envOr("POPL_MANUAL_RECOVERY_TIMESTAMP",block.timestamp);
        require(timestamp>=block.timestamp,"export time must not retreat");vm.warp(timestamp);_fresh();
    }
    function _hybrid() private {
        ZZZRebalanceConfirmation confirmation=strategy.rebalanceConfirmation();
        assertTrue(strategy.portfolioPolicy().enabled(target));assertFalse(strategy.portfolioPolicy().configurationPending(bucket));
        vm.warp(uint256(vault.group(bucket).lastRebalance)+43200);_fresh();
        uint160 next=uint160(uint256(Q96)*83/100);
        _to(core,state,targetKey,next);_to(core,state,referenceKey,next);_to(core,state,executionKey,next);_to(independentCore,independentState,referenceKey,next);
        vm.prank(KEEPER);assertFalse(confirmation.observe(bucket));
        for(uint256 i;i<3;++i){vm.warp(block.timestamp+240);_fresh();vm.prank(KEEPER);confirmation.observe(bucket);}
        assertTrue(strategy.rebalanceReady(bucket));
        vm.prank(KEEPER);vault.rebalance{gas:CAP}(bucket,1,block.timestamp+100);
        assertGt(manager.secondaryId(vault.group(bucket).lpTokenId),0);
        uint160 mixed=uint160(uint256(Q96)*86/100);
        _to(core,state,targetKey,mixed);_to(core,state,referenceKey,mixed);_to(core,state,executionKey,mixed);_to(independentCore,independentState,referenceKey,mixed);
        _to(core,state,targetKey,uint160(uint256(mixed)*1001/1000));_to(core,state,targetKey,mixed);
        // Fund actual venue receipts in both currencies before recovery.
        vm.prank(KEEPER);vault.collectFees(bucket,block.timestamp+100);
        assertGt(rewards.liabilities(address(0)),0);assertGt(rewards.liabilities(address(token)),0);
        assertGt(fees.compoundBalance(bucket,address(0)),0);assertGt(fees.compoundBalance(bucket,address(token)),0);
        assertGt(fees.buybackBalance(address(0)),0);assertGt(fees.buybackBalance(address(token)),0);
        vm.prank(GOVERNANCE);access.setPaused(true);
    }
    function _park() private {
        Before memory beforeState=_before();
        Position memory p=vault.group(bucket);
        ZZZMigration.ParkingRequest memory r=ZZZMigration.ParkingRequest(bucket,p.poolId,p.lpTokenId,vault.bucketTotalShares(bucket),p.depositUSD,
            migration.custodyEpoch(bucket),migration.parkingNonce(bucket),address(0),address(token),1,1,block.timestamp+500,REVIEW,
            manager.executionPortfolioFingerprint(p.lpTokenId));
        vm.prank(GOVERNANCE);migration.park(r);
        Position memory parked=vault.group(bucket);assertEq(uint8(parked.status),uint8(PositionStatus.Parked));assertEq(parked.lpTokenId,0);
        assertEq(posm.getPositionLiquidity(p.lpTokenId),0);assertEq(posm.getPositionLiquidity(beforeState.residual),0);
        assertEq(manager.secondaryId(p.lpTokenId),0);assertEq(manager.activeSecondaryCount(),0);
        assertEq(vault.sharesOf(id),beforeState.shares);assertEq(vault.sharesOf(secondId),beforeState.secondShares);
        assertEq(vault.bucketTotalShares(bucket),beforeState.supply);assertEq(parked.centerX96,p.centerX96);assertEq(parked.lastRebalance,p.lastRebalance);
        assertGe(fees.compoundBalance(bucket,address(0)),beforeState.compound0);assertGe(fees.compoundBalance(bucket,address(token)),beforeState.compound1);
        assertGe(rewards.liabilities(address(0)),beforeState.liabilities0);assertGe(rewards.liabilities(address(token)),beforeState.liabilities1);
        assertGe(fees.buybackBalance(address(0)),beforeState.buyback0);assertGe(fees.buybackBalance(address(token)),beforeState.buyback1);
        assertGe(address(vault).balance,parked.idle0);assertGe(token.balanceOf(address(vault)),parked.idle1);
    }
    function _request(bool consolidate,uint8 checks) private returns(EmergencyRebalance memory r) {
        Position memory p=vault.group(bucket);int24 low;int24 high;
        if(consolidate)(low,high)=manager.ticks(p.lpTokenId);else (low,high,)=strategy.target(target);
        (uint256 a0,uint256 a1)=_principal(consolidate);
        vm.prank(address(manager));ZZZLPBalancer.Plan memory plan=router.plan(target,low,high,a0,a1);
        require(plan.amountIn<=type(uint128).max && plan.minimumOut<=uint128(type(int128).max));
        if(plan.amountIn!=0){if(plan.zeroForOne){a0-=plan.amountIn;a1+=plan.amountOut;}else{a1-=plan.amountIn;a0+=plan.amountOut;}}
        (uint128 quotedL,)=router.deploymentAmounts(manager.spot(target),low,high,a0,a1);
        uint128 minimumL=uint128(uint256(quotedL)*95/100);require(minimumL>1,"meaningful actual quote floor");
        r=EmergencyRebalance(bucket,consolidate?migration.consolidationCustodyHash(bucket):migration.emergencyCustodyHash(bucket),
            checks,low,high,plan.poolId,plan.zeroForOne,uint128(plan.amountIn),uint128(plan.minimumOut),minimumL,block.timestamp+500,REVIEW);
        if(plan.amountIn==0){r.swapPool=bytes32(0);r.zeroForOne=false;r.minimumOut=0;}
    }
    function _principal(bool consolidate) private view returns(uint256 a0,uint256 a1) {
        Position memory p=vault.group(bucket);a0=p.idle0;a1=p.idle1;
        if(p.lpTokenId!=0){uint256 selected=consolidate?manager.secondaryId(p.lpTokenId):p.lpTokenId;
            if(selected!=0){(uint256 x,uint256 y)=consolidate?manager.amounts(selected):manager.portfolioAmounts(selected);a0+=x;a1+=y;}}
        if(!consolidate){a0+=fees.compoundBalance(bucket,address(0));a1+=fees.compoundBalance(bucket,address(token));}
    }
    function _before() private view returns(Before memory b) {
        b.position=vault.group(bucket);b.residual=manager.secondaryId(b.position.lpTokenId);
        if(b.position.lpTokenId!=0)b.mainL=posm.getPositionLiquidity(b.position.lpTokenId);
        b.shares=vault.sharesOf(id);b.secondShares=vault.sharesOf(secondId);b.supply=vault.bucketTotalShares(bucket);
        b.compound0=fees.compoundBalance(bucket,address(0));b.compound1=fees.compoundBalance(bucket,address(token));
        b.liabilities0=rewards.liabilities(address(0));b.liabilities1=rewards.liabilities(address(token));
        b.buyback0=fees.buybackBalance(address(0));b.buyback1=fees.buybackBalance(address(token));
        b.lastCompound=vault.migrationBudget().lastCompound(bucket);b.nonce=migration.parkingNonce(bucket);b.epoch=migration.custodyEpoch(bucket);
        b.royaltyWeight=nft.royaltyRewards().weightOf(id);b.secondRoyaltyWeight=nft.royaltyRewards().weightOf(secondId);b.royaltyTotal=nft.royaltyRewards().totalWeight();
        b.firstClaim0=rewards.claimable(id,address(0));b.firstClaim1=rewards.claimable(id,address(token));
        b.secondClaim0=rewards.claimable(secondId,address(0));b.secondClaim1=rewards.claimable(secondId,address(token));
    }
    function _atomic() private view returns(bytes32 hash) {
        Before memory b=_before();hash=keccak256(abi.encode(b,nft.ownerOf(id),nft.ownerOf(secondId),nft.ownerOf(dormantId),
            address(vault).balance,token.balanceOf(address(vault)),address(fees).balance,token.balanceOf(address(fees))));
        return keccak256(abi.encode(hash,address(rewards).balance,token.balanceOf(address(rewards)),posm.nextTokenId(),access.paused(),
            fees.accounted(address(0)),fees.accounted(address(token)),fees.dust(bucket,address(0)),fees.dust(bucket,address(token))));
    }
    function _call(EmergencyRebalance memory r,bool consolidate) private returns(bytes memory) {
        return consolidate?abi.encodeCall(ZZZMigration.consolidateResidual,(r,true)):abi.encodeCall(ZZZMigration.emergencyRebalance,(r));
    }
    function _fails(EmergencyRebalance memory r,bool consolidate,address caller) private returns(bytes memory reason) {
        bytes32 beforeState=_atomic();vm.prank(caller);bool ok;(ok,reason)=address(migration).call{gas:CAP}(_call(r,consolidate));
        assertFalse(ok);assertEq(_atomic(),beforeState,"failed manual operation must roll back rights/backing");
        assertFalse(vault.migrationBudget().emergencyActive());
    }
    function _mandatoryFailures(EmergencyRebalance memory r,bool consolidate) private {
        bytes32 requestHash=keccak256(abi.encode(r));
        _fails(r,consolidate,OWNER);_fails(r,consolidate,KEEPER);
        EmergencyRebalance memory bad=_copy(r);bad.custodyHash=bytes32(uint256(1));_fails(bad,consolidate,GOVERNANCE);
        bad=_copy(r);bad.deadline=block.timestamp-1;_fails(bad,consolidate,GOVERNANCE);
        bad=_copy(r);bad.minimumLiquidity=type(uint128).max;_fails(bad,consolidate,GOVERNANCE);
        vm.prank(GOVERNANCE);access.setPaused(false);_fails(r,consolidate,GOVERNANCE);vm.prank(GOVERNANCE);access.setPaused(true);
        assertEq(keccak256(abi.encode(r)),requestHash,"negative probes preserve original request");
    }
    function _copy(EmergencyRebalance memory r) private pure returns(EmergencyRebalance memory) {return abi.decode(abi.encode(r),(EmergencyRebalance));}
    function _referenceAccepted(string memory label,EmergencyRebalance memory r,bool consolidate) private returns(EmergencyRebalance memory) {
        assertEq(r.checks,14);assertGt(r.amountIn,0,"reference acceptance requires an actual swap");
        bytes32 original=keccak256(abi.encode(r));EmergencyRebalance memory bad=_copy(r);bad.swapPool=referencePool;
        assertTrue(registry.get(referencePool).operationsEnabled);assertTrue(registry.isNativePool(referencePool));
        strategy.validateExitPrice(target);strategy.validateExitPrice(referencePool);
        vm.prank(address(manager));(uint256 output,)=router.quoteSwap(referencePool,r.zeroForOne,r.amountIn);
        assertGe(output,r.minimumOut,"reference quote proves explicit swap floor");
        (uint256 a0,uint256 a1)=_principal(consolidate);
        if(r.zeroForOne){a0-=r.amountIn;a1+=output;}else{a1-=r.amountIn;a0+=output;}
        (uint128 quotedL,)=router.deploymentAmounts(manager.spot(target),r.lower,r.upper,a0,a1);
        assertGe(quotedL,r.minimumLiquidity,"reference quote proves explicit LP floor");
        emit RecoveryReferenceQuote(label,output,quotedL,r.minimumOut,r.minimumLiquidity);
        assertEq(keccak256(abi.encode(r)),original,"reference selection preserves the original reviewed floors");
        return bad;
    }
    function _post(Before memory b,bool consolidate) private view {
        Position memory p=vault.group(bucket);
        assertEq(uint8(p.status),uint8(PositionStatus.Active));assertEq(p.poolId,b.position.poolId);assertEq(p.depositUSD,b.position.depositUSD);
        assertEq(vault.sharesOf(id),b.shares);assertEq(vault.sharesOf(secondId),b.secondShares);assertEq(vault.bucketTotalShares(bucket),b.supply);
        assertEq(nft.ownerOf(id),OWNER);assertEq(nft.ownerOf(secondId),SECOND_OWNER);assertEq(nft.ownerOf(dormantId),OWNER);assertEq(vault.sharesOf(dormantId),0);
        assertTrue(members.eligible(id));assertTrue(members.eligible(secondId));assertFalse(members.eligible(dormantId));assertEq(members.totalEligible(),2);
        assertEq(nft.royaltyRewards().weightOf(id),b.royaltyWeight);assertEq(nft.royaltyRewards().weightOf(secondId),b.secondRoyaltyWeight);assertEq(nft.royaltyRewards().totalWeight(),b.royaltyTotal);
        assertGe(rewards.claimable(id,address(0)),b.firstClaim0);assertGe(rewards.claimable(id,address(token)),b.firstClaim1);
        assertGe(rewards.claimable(secondId,address(0)),b.secondClaim0);assertGe(rewards.claimable(secondId,address(token)),b.secondClaim1);
        assertEq(posm.ownerOf(p.lpTokenId),address(vault));assertEq(manager.secondaryId(p.lpTokenId),0);assertEq(manager.activeSecondaryCount(),0);
        assertGt(posm.getPositionLiquidity(p.lpTokenId),0);
        if(consolidate){assertEq(p.lpTokenId,b.position.lpTokenId);assertEq(p.centerX96,b.position.centerX96);assertEq(p.lastRebalance,b.position.lastRebalance);
            assertGe(posm.getPositionLiquidity(p.lpTokenId),uint256(b.mainL)+1);
            assertEq(vault.migrationBudget().lastCompound(bucket),block.timestamp);
            assertEq(migration.parkingNonce(bucket),b.nonce+1);assertEq(migration.custodyEpoch(bucket),b.epoch+1);
            assertFalse(strategy.portfolioPolicy().enabled(target));assertFalse(strategy.portfolioPolicy().configurationPending(bucket));
            assertGe(fees.compoundBalance(bucket,address(0)),b.compound0);
            assertGe(fees.compoundBalance(bucket,address(token)),b.compound1);
        }else{assertTrue(p.lpTokenId!=b.position.lpTokenId);assertEq(p.lastRebalance,block.timestamp);
            assertTrue(strategy.portfolioPolicy().enabled(target),"emergency single-main does not silently change desired mode");
            assertEq(vault.migrationBudget().lastCompound(bucket),b.lastCompound);assertEq(migration.parkingNonce(bucket),b.nonce);assertEq(migration.custodyEpoch(bucket),b.epoch);
            assertEq(fees.compoundBalance(bucket,address(0)),0);assertEq(fees.compoundBalance(bucket,address(token)),0);
            if(b.position.lpTokenId!=0)assertEq(posm.getPositionLiquidity(b.position.lpTokenId),0);}
        if(b.residual!=0){assertEq(posm.getPositionLiquidity(b.residual),0);assertEq(manager.secondaryId(b.position.lpTokenId),0);}
        assertGe(rewards.liabilities(address(0)),b.liabilities0);assertGe(rewards.liabilities(address(token)),b.liabilities1);
        assertGe(fees.buybackBalance(address(0)),b.buyback0);assertGe(fees.buybackBalance(address(token)),b.buyback1);
        assertGe(address(rewards).balance,rewards.liabilities(address(0)));assertGe(token.balanceOf(address(rewards)),rewards.liabilities(address(token)));
        assertGe(address(fees).balance,fees.accounted(address(0)));assertGe(token.balanceOf(address(fees)),fees.accounted(address(token)));
        assertEq(fees.accounted(address(0)),fees.compoundBalance(bucket,address(0))+fees.buybackBalance(address(0))+fees.dust(bucket,address(0)));
        assertEq(fees.accounted(address(token)),fees.compoundBalance(bucket,address(token))+fees.buybackBalance(address(token))+fees.dust(bucket,address(token)));
        assertGe(address(vault).balance,p.idle0);assertGe(token.balanceOf(address(vault)),p.idle1);
        assertEq(address(manager).balance,PREFUND);assertEq(token.balanceOf(address(manager)),PREFUND);
        assertEq(manager.positionOperator().balance,PREFUND);assertEq(token.balanceOf(manager.positionOperator()),PREFUND);
        assertEq(token.allowance(address(vault),address(manager)),0);assertEq(token.allowance(address(vault),manager.positionOperator()),0);
        assertFalse(oracle.executionActive());assertFalse(vault.migrationBudget().emergencyActive());assertFalse(migration.consolidationActive());
        assertTrue(access.paused());assertEq(access.canonicalState(),0);assertFalse(access.lpExitStarted());assertEq(GOVERNANCE.code.length,0);
    }

    function testActualManualC14ConsolidatesExistingMain() public {
        _hybrid();ZZZPortfolioPolicy portfolio=strategy.portfolioPolicy();
        vm.prank(GOVERNANCE);portfolio.setMode(target,false,REVIEW);
        _currentExportTime();EmergencyRebalance memory r=_request(true,14);_mandatoryFailures(r,true);
        r=_referenceAccepted("active-c14",r,true);_run("active-c14",r,true,1);
    }
    function testActualManualD14ReplacesBothLegs() public {
        _hybrid();_currentExportTime();EmergencyRebalance memory r=_request(false,14);_mandatoryFailures(r,false);
        r=_referenceAccepted("active-d14",r,false);_run("active-d14",r,false,1);
    }
    function testActualParkedD14RetainsFinancialGuards() public {
        _hybrid();_currentExportTime();_export("parked14-before-park");_park();EmergencyRebalance memory r=_request(false,14);
        _mandatoryFailures(r,false);EmergencyRebalance memory bad=_copy(r);bad.checks=15;_fails(bad,false,GOVERNANCE);
        bad=_copy(r);bad.checks=30;_fails(bad,false,GOVERNANCE);assertEq(r.checks,14);
        r=_referenceAccepted("parked-d14",r,false);_run("parked-d14",r,false,2);
    }
    function testActualParkedD0ExplicitOracleOutage() public {
        _hybrid();_currentExportTime();_park();EmergencyRebalance memory r=_request(false,0);
        // Explicitly selected emergency scenario, never an automated retry of14.
        ethFirst.set(0,block.timestamp-4000,block.timestamp-4000);ethSecond.set(0,block.timestamp-4000,block.timestamp-4000);
        vm.prank(GOVERNANCE);registry.disablePool(target,false,true);vm.prank(GOVERNANCE);registry.disablePool(referencePool,false,true);
        vm.prank(GOVERNANCE);registry.disablePool(executionPool,false,true);
        EmergencyRebalance memory guarded=_copy(r);guarded.checks=14;_fails(guarded,false,GOVERNANCE);assertEq(r.checks,0);
        _mandatoryFailures(r,false);_run("parked-d0",r,false,2);
    }
    function _run(string memory label,EmergencyRebalance memory r,bool consolidate,uint256 schema) private {
        Before memory b=_before();emit RecoverySelected(label,schema,consolidate?"C":"D",r);
        uint256[] memory ids=_ids();emit RecoveryUnsignedCall(label,GOVERNANCE,address(migration),0,_call(r,consolidate),CAP,2500,bucket,ids);
        _export(label);_cold();vm.prank(GOVERNANCE);uint256 start=gasleft();
        (bool ok,bytes memory reason)=address(migration).call{gas:CAP}(_call(r,consolidate));uint256 used=start-gasleft();
        if(!ok)emit log_named_bytes("manual-failure",reason);assertTrue(ok,"exact selected manual operation succeeds");
        uint256 padded=(used*125+99)/100;assertLe(padded,CAP);emit RecoveryGas(label,used,padded);_post(b,consolidate);
    }
    function _ids() private view returns(uint256[] memory ids){ids=new uint256[](3);ids[0]=id;ids[1]=secondId;ids[2]=dormantId;}
    function _bindings() private {
        string[31] memory names=[string("access"),"nft","vault","rewards","royalties","claim_router","handoff","vault_canonical",
            "principal_exit","rewards_canonical","seadrop_mint","seadrop","pools","liquidity","strategy","budget","portfolio_policy",
            "rebalance_confirmation","balancing_router","lp_balance_math","lp_position_executor","protocol_policy","pool_manager","state_view",
            "position_manager","permit2","activation_assets","contribution_pricing","custody_validation","fees","oracle"];
        address[31] memory addresses=[address(access),address(nft),address(vault),address(rewards),address(nft.royaltyRewards()),address(nft.claimRouter()),
            access.module(Ids.CANONICAL),access.module(Ids.VAULT_CANONICAL),address(migration),rewards.canonicalModule(),address(mintHelper),address(seaDrop),
            address(registry),address(manager),address(strategy),address(vault.migrationBudget()),address(strategy.portfolioPolicy()),address(strategy.rebalanceConfirmation()),
            address(router),address(router.balanceMath()),manager.positionOperator(),access.protocolPolicy(),address(core),address(state),address(posm),address(permit),
            address(registry.activationAssets()),address(oracle.contributionPricing()),address(migration.validation()),address(fees),address(oracle)];
        string[] memory roles=new string[](31);address[] memory components=new address[](31);bytes32[] memory hashes=new bytes32[](31);
        for(uint256 i;i<31;++i){roles[i]=names[i];components[i]=addresses[i];hashes[i]=addresses[i].codehash;_materialize(addresses[i]);}
        emit RecoveryBindings(roles,components,hashes);emit RecoveryAsset(address(token),18);
    }
    function _materialize(address a) private {bytes memory runtime=a.code;require(runtime.length!=0);vm.etch(a,runtime);}
    function _allCode() private {
        _bindings();_materialize(address(token));_materialize(address(vrf));_materialize(address(ethFirst));_materialize(address(ethSecond));
        _materialize(address(referenceFeed));_materialize(address(independentFeed));_materialize(address(independentCore));_materialize(address(independentState));
        _materialize(address(nft.metadataRenderer()));_materialize(access.module(Ids.NFT_CANONICAL));_materialize(access.module(Ids.FEES_CANONICAL));
        _materialize(access.module(Ids.COMPOUNDER));_materialize(access.module(Ids.BUYBACK));_materialize(access.royaltyFactory());_materialize(access.activationAssetsFactory());
        ZZZRoyaltyFactory factory=ZZZRoyaltyFactory(access.royaltyFactory());_materialize(factory.part0());_materialize(factory.part1());
    }
    function _exportSetup() private {
        string memory root=vm.envOr("POPL_MANUAL_RECOVERY_EXPORT_ROOT",string(""));if(bytes(root).length==0)return;
        _allCode();setupPath=string.concat(root,"/setup.json");vm.dumpState(setupPath);setupHash=keccak256(bytes(vm.readFile(setupPath)));
        emit RecoveryBaseline(setupPath,setupHash);
    }
    function _export(string memory label) private {
        string memory root=vm.envOr("POPL_MANUAL_RECOVERY_EXPORT_ROOT",string(""));if(bytes(root).length==0)return;
        assertEq(keccak256(bytes(vm.readFile(setupPath))),setupHash);_allCode();
        string memory path=string.concat(root,"/",label,".json");vm.dumpState(path);
        emit RecoveryState(label,path,keccak256(bytes(vm.readFile(path))),block.number,block.timestamp,block.chainid,GOVERNANCE,bucket,_ids(),setupHash);
    }
    function _cold() private {
        address[15] memory a=[address(access),address(migration),address(vault),address(vault.migrationBudget()),address(manager),manager.positionOperator(),
            address(router),address(router.balanceMath()),address(core),address(state),address(posm),address(permit),address(oracle),address(fees),address(rewards)];
        for(uint256 i;i<a.length;++i)vm.cool(a[i]);vm.cool(address(strategy));vm.cool(address(registry));vm.cool(address(token));
        vm.cool(address(ethFirst));vm.cool(address(ethSecond));vm.cool(address(referenceFeed));vm.cool(address(independentFeed));vm.cool(address(independentCore));
        vm.cool(address(independentState));vm.cool(address(strategy.portfolioPolicy()));vm.cool(address(strategy.rebalanceConfirmation()));
        vm.cool(address(nft));vm.cool(address(members));vm.cool(address(nft.royaltyRewards()));
        vm.cool(address(oracle.contributionPricing()));vm.cool(address(migration.validation()));vm.cool(access.protocolPolicy());
    }
}
