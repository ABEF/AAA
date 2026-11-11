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
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {ZZZV4SpotPriceFeed} from "../src/ZZZV4SpotPriceFeed.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationAssetsFactory} from "../src/ZZZActivationAssetsFactory.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {IZZZExecutionOracle, IZZZExecutionSpotSource, MarketState} from "../src/interfaces/IZZZExecutionOracle.sol";
import {PoolKey, PoolConfig, Position, Ids} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockFeed} from "./mocks/Mocks.sol";
import {FactualPermit, FactualToken} from "./LiquidityFactualChecks.t.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";

/// @dev TEST ONLY registry seam: real core, StateViews, spot readers and PosM are
/// used below. Distinct local states do not qualify real market independence.
contract ContextExecutionPools {
    uint64 public configurationRevision;
    address public access;
    address public activationAssets;
    address public activationEntry;
    mapping(bytes32=>PoolConfig) private configurations;
    function configure(bytes32 id, PoolConfig memory config) external {
        configurations[id]=config;
        ++configurationRevision;
    }
    function get(bytes32 id) external view returns(PoolConfig memory) {return configurations[id];}
    function accounting(bytes32 id) external view returns(PoolConfig memory) {return configurations[id];}
    function isNativePool(bytes32 id) external view returns(bool) {
        return configurations[id].key.currency0==address(0) && configurations[id].key.currency1!=address(0);
    }
    function initializeEntry(address controller,address token) external {
        require(access==address(0));access=controller;
        ZZZActivationAssets assets=ZZZActivationAssets(ZZZActivationAssetsFactory(MockAccess(controller).activationAssetsFactory()).create());
        activationAssets=address(assets);
        activationEntry=address(new ZZZActivationEntry(controller,address(this),address(assets)));
        assets.admitPoolAsset(address(0));assets.admitPoolAsset(token);
    }
    function contributionValue(bytes32 id,uint256 amount0,uint256 amount1) external view returns(uint256) {
        if(activationEntry!=address(0)) {
            uint256 original=ZZZActivationEntry(activationEntry).sourceValue(id,amount0,amount1);
            if(original!=0)return original;
        }
        ZZZOracle oracle=ZZZOracle(MockAccess(access).module(Ids.ORACLE));
        PoolConfig memory config=configurations[id];
        return oracle.value(config.key.currency0,amount0)+oracle.value(config.key.currency1,amount1);
    }
}

/// @dev Separately funded outsider: its trade must not alter the contributor's
/// balances and get rejected merely by ExactToken's recipient-delta proof.
contract ContextExternalTrader {
    using BalanceDeltaLibrary for BalanceDelta;
    PoolManager private immutable core;
    CoreKey private key;
    constructor(PoolManager manager,CoreKey memory poolKey){core=manager;key=poolKey;}
    receive() external payable {}
    function swapTokenForETH(uint256 amount) external {core.unlock(abi.encode(amount));}
    function unlockCallback(bytes calldata data) external returns(bytes memory){
        require(msg.sender==address(core));uint256 amount=abi.decode(data,(uint256));
        BalanceDelta delta=core.swap(key,SwapParams(false,-int256(amount),TickMath.MAX_SQRT_PRICE-1),"");
        uint256 debt=uint256(-int256(delta.amount1()));
        core.sync(key.currency1);require(FactualToken(Currency.unwrap(key.currency1)).transfer(address(core),debt));
        require(core.settle()==debt);
        core.take(key.currency0,address(this),uint256(int256(delta.amount0())));
        return "";
    }
}

/// @notice Actual installed v4 execution against a spot-reference swap venue.
/// ETH publication, admission and Permit2 are explicit local test seams; these
/// tests do not deploy publicly, use a wallet, or qualify prices/market depth.
contract ReferenceExecutionContextTest is Test {
    using BalanceDeltaLibrary for BalanceDelta;
    uint160 internal constant Q96 = uint160(1 << 96);
    uint256 internal constant PREFUND = 17;
    uint256 internal constant DEFAULT_ENTRY_GAS_BUDGET = 12_000_000;
    uint256 internal constant POLICY2_DIAGNOSTIC_GAS_BUDGET = 32_000_000;
    bytes32 internal constant REVIEW = keccak256("local actual-v4 reference context test only");
    MockAccess internal access;
    FactualToken internal token;
    MockFeed internal ethFirst;
    MockFeed internal ethSecond;
    PoolManager internal core;
    PoolManager internal independentCore;
    StateView internal state;
    StateView internal independentState;
    PositionManager internal positions;
    FactualPermit internal permit;
    ZZZLiquidityManager internal manager;
    ZZZLPBalancer internal router;
    ZZZOracle internal oracle;
    ZZZStrategy internal strategy;
    ContextExecutionPools internal registry;
    ZZZV4SpotPriceFeed internal referenceFeed;
    ZZZV4SpotPriceFeed internal independentReference;
    CoreKey internal targetKey;
    CoreKey internal referenceKey;
    CoreKey internal independentKey;
    bytes32 internal target;
    bytes32 internal referencePool;
    bytes32 internal independentPool;
    uint256 internal callbackCount;
    bytes32 internal callbackLiveFingerprint;
    bytes32 internal callbackETHFingerprint;
    uint256 internal callbackLiveLower;
    uint256 internal callbackLiveUpper;
    bytes32 internal callbackExecutionFingerprint;
    uint256 internal callbackExecutionLower;
    uint256 internal callbackExecutionUpper;
    bool internal callbackSeen;
    ZZZVault internal vault;
    ZZZNFT internal nft;
    ZZZRewards internal rewards;
    ZZZMembership internal membership;
    ZZZFeeController internal fees;
    ZZZMigration internal migration;
    ZZZActivationEntry internal entry;
    MockVRF internal vrf;
    ContextExternalTrader internal callbackTrader;
    bytes32 private exportSetupHash;
    struct PriceCapture { uint256 lower; uint256 upper; bytes32 fingerprint; }
    PriceCapture internal callbackExpectedPrice;
    struct EntryScenario {
        address owner;
        ZZZActivationEntry.Request request;
        uint16 maximumLossBps;
        bytes32 expectedContributionPolicy;
        uint256 oldBucket;
        uint256 oldLpId;
        uint256 oldShares;
        uint8 sourceDecimals;
        PriceCapture sourceUSD;
        PriceCapture ethUSD;
        PriceCapture zzzUSD;
    }
    struct EntryOutcome {
        uint256 nftId;uint256 bucket;uint256 lpId;uint256 shares;uint256 totalShares;
        uint128 liquidity;uint256 principal0;uint256 principal1;uint256 idle0;uint256 idle1;
        bool executionActive;uint256 callGas;
    }
    event ReferenceEntryScenario(EntryScenario scenario);
    event ReferenceEntryOutcome(EntryOutcome outcome);
    event ReferenceDefaultBudgetRejected(uint256 indexed nftId,bool growth,uint256 gasBudget,bytes32 returnDataHash);
    event ReferenceExportBlock(uint256 number,uint256 timestamp,uint256 chainId);
    event ReferenceExportBaseline(string path,bytes32 contentHash);
    event ReferenceExportCodeMaterialized(address indexed component,bytes32 runtimeHash,uint256 length);
    /// @dev Ordered Entry,Vault,Budget,Pricing,Oracle,Manager,Executor,PosM,Fees,
    /// Policy,Registry,NFT,Rewards,Membership,Migration,core,StateView,Router,
    /// reference,independentReference,independentCore,independentState,Assets,VRF.
    event ReferenceExecutionBindings(address[] components,bytes32[] runtimeHashes);
    receive() external payable {}

    // TEST ONLY fixed Budget read capability for the ordinary entry path.
    function migrationBudget() external view returns (address) { return address(this); }
    function maintenanceBucket() external pure returns (uint256) { return 0; }
    function maintenancePrices() external pure returns (uint256,uint256,uint256,uint256) {
        return (1e18,1e18,1e18,1e18);
    }

    function setUp() public {
        vm.warp(1_000_000);
        vm.deal(address(this),10_000_000 ether);
        access = new MockAccess();
        ProtocolPolicyFixture.bind(address(access));
        token = new FactualToken();
        token.mint(address(this),10_000_000 ether);
        core = new PoolManager(address(this));
        independentCore = new PoolManager(address(this));
        state = new StateView(IPoolManager(address(core)));
        independentState = new StateView(IPoolManager(address(independentCore)));
        permit = new FactualPermit();
        positions = new PositionManager(IPoolManager(address(core)),IAllowanceTransfer(address(permit)),100000,
            IPositionDescriptor(address(0)),IWETH9(address(0)));
        router = new ZZZLPBalancer(address(access),address(core),address(state));
        manager = new ZZZLiquidityManager(address(access),address(positions),address(state),address(core),
            address(permit),address(router));
        oracle = new ZZZOracle(address(access),address(0));
        strategy = new ZZZStrategy(address(access),address(new ZZZPortfolioPolicy(address(access))),
            address(new ZZZRebalanceConfirmation(address(access))));
        registry = new ContextExecutionPools();
        ethFirst = new MockFeed(8,1e8);
        ethSecond = new MockFeed(8,1e8);
        access.bind(Ids.VAULT,address(this));
        access.bind(Ids.LIQUIDITY,address(manager));
        access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.STRATEGY,address(strategy));
        access.bind(Ids.POOLS,address(registry));
        targetKey = _key(10020,200);
        referenceKey = _key(500,10);
        // Pool IDs hash the key, not the deployment of PoolManager. Identical
        // keys on independently funded cores MUST remain distinct markets.
        independentKey = _key(500,10);
        target = _admit(targetKey,true);
        referencePool = _admit(referenceKey,false);
        independentPool = keccak256(abi.encode(independentKey));
        core.initialize(targetKey,Q96);
        core.initialize(referenceKey,Q96);
        independentCore.initialize(independentKey,Q96);
        core.setProtocolFeeController(address(this));
        core.setProtocolFee(referenceKey,uint24(1000 | (1000 << 12)));
        _external(core,targetKey,100_000 ether);
        _external(core,referenceKey,1_000_000 ether);
        _external(independentCore,independentKey,2_000_000 ether);
        referenceFeed = _reader(core,state,referenceKey,ethFirst);
        independentReference = _reader(independentCore,independentState,independentKey,ethSecond);
        oracle.setDualFeed(address(0),_source(address(ethFirst),8,"ETH first"),
            _source(address(ethSecond),8,"ETH second"),300,REVIEW);
        oracle.setDualFeed(address(token),_source(address(referenceFeed),18,"external pool first"),
            _source(address(independentReference),18,"separate core pool second"),300,REVIEW);
        registry.initializeEntry(address(access),address(token));
        ZZZActivationAssets(registry.activationAssets()).configureZZZ(address(token),address(token).codehash,REVIEW);
        oracle.setExecutionSource(address(referenceFeed),true,address(referenceFeed).codehash,REVIEW);
        oracle.setExecutionSource(address(independentReference),true,address(independentReference).codehash,REVIEW);
        access.seal();
        bytes32[] memory venues = new bytes32[](1); venues[0]=referencePool;
        router.configureExecutionPools(venues,REVIEW);
        vm.deal(address(manager),PREFUND); token.mint(address(manager),PREFUND);
        token.approve(address(manager),type(uint128).max);
        token.approve(manager.positionOperator(),type(uint128).max);
        _exportSetupIfRequested();
    }

    /// @dev Forge's later dump may omit setup-only storage which the test only
    /// reads. Preserve actual initialized state, then merge the later dump over
    /// it per account and storage slot, including explicit zero writes. This
    /// optional I/O is inactive for every default verification workflow.
    function _exportSetupIfRequested() internal {
        string memory path=vm.envOr("POPL_REFERENCE_EXPORT_PATH",string(""));
        if(bytes(path).length==0)return;
        path=string.concat(path,".setup.json");
        vm.dumpState(path);
        exportSetupHash=keccak256(bytes(vm.readFile(path)));
    }

    function _key(uint24 fee,int24 spacing) internal view returns (CoreKey memory) {
        return CoreKey(Currency.wrap(address(0)),Currency.wrap(address(token)),fee,spacing,IHooks(address(0)));
    }
    function _admit(CoreKey memory key,bool deposits) internal returns (bytes32 id) {
        PoolKey memory k=PoolKey(Currency.unwrap(key.currency0),Currency.unwrap(key.currency1),key.fee,
            key.tickSpacing,address(key.hooks));
        id=keccak256(abi.encode(k));
        registry.configure(id,PoolConfig(k,deposits,true,5000,100,500,200,43200,1e18,1_000_000e18));
    }
    function _source(address feed,uint8 digits,string memory identity) internal view returns (ZZZOracle.SourcePolicy memory) {
        return ZZZOracle.SourcePolicy(feed,feed.codehash,keccak256(bytes(identity)),3600,digits);
    }
    function _reader(PoolManager sourceCore,StateView sourceState,CoreKey memory key,MockFeed eth)
        internal returns (ZZZV4SpotPriceFeed) {
        ZZZV4SpotPriceFeed.Config memory c;
        c.core=address(sourceCore);c.expectedCoreCodeHash=address(sourceCore).codehash;
        c.stateView=address(sourceState);c.expectedStateViewCodeHash=address(sourceState).codehash;
        c.key=key;c.expectedPoolId=keccak256(abi.encode(key));
        c.zzz=address(token);c.expectedZZZCodeHash=address(token).codehash;
        c.ethUsdFeed=address(eth);c.expectedETHFeedCodeHash=address(eth).codehash;
        c.maxETHAge=3600;c.minimumLiquidity=1e18;c.reviewHash=REVIEW;
        return new ZZZV4SpotPriceFeed(c);
    }
    function _external(PoolManager sourceCore,CoreKey memory key,int256 liquidity) internal {
        sourceCore.unlock(abi.encode(uint8(0),key,liquidity,uint160(0)));
    }
    function _trade(PoolManager sourceCore,CoreKey memory key,bool zeroForOne,uint256 amount) internal {
        require(amount<=uint256(type(int256).max));
        sourceCore.unlock(abi.encode(zeroForOne?uint8(1):uint8(2),key,int256(amount),uint160(0)));
    }
    function _referenceNarrowLiquidity() internal {
        uint160 geometry=uint160(uint24(int24(-10))) | (uint160(uint24(int24(10)))<<24);
        core.unlock(abi.encode(uint8(3),referenceKey,int256(1_000_000 ether),geometry));
    }
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender==address(core) || msg.sender==address(independentCore));
        PoolManager sourceCore=PoolManager(msg.sender);
        (uint8 action,CoreKey memory key,int256 amount,uint160 geometry)=abi.decode(data,(uint8,CoreKey,int256,uint160));
        BalanceDelta delta;
        if(action==0) {
            (delta,)=sourceCore.modifyLiquidity(key,ModifyLiquidityParams(-60000,60000,amount,bytes32(0)),"");
        } else if(action==3) {
            (delta,)=sourceCore.modifyLiquidity(key,ModifyLiquidityParams(int24(uint24(geometry)),
                int24(uint24(geometry>>24)),amount,bytes32(uint256(1))),"");
        } else {
            bool zeroForOne=action==1 || action==4;
            uint160 limit=(action==4 || action==5)?geometry:(zeroForOne?TickMath.MIN_SQRT_PRICE+1:TickMath.MAX_SQRT_PRICE-1);
            delta=sourceCore.swap(key,SwapParams(zeroForOne,-amount,limit),"");
        }
        _settle(sourceCore,key.currency0,delta.amount0());
        _settle(sourceCore,key.currency1,delta.amount1());
        return "";
    }
    function _settle(PoolManager sourceCore,Currency asset,int128 delta) internal {
        if(delta==0)return;
        if(delta>0) {sourceCore.take(asset,address(this),uint256(int256(delta)));return;}
        uint256 amount=uint256(-int256(delta));sourceCore.sync(asset);
        if(Currency.unwrap(asset)==address(0)) assertEq(sourceCore.settle{value:amount}(),amount);
        else {token.transfer(address(sourceCore),amount);assertEq(sourceCore.settle(),amount);}
    }
    function _snapshot(StateView sourceState,bytes32 pool) internal view returns (bytes32) {
        (uint160 sqrt,int24 tick,uint24 protocol,uint24 fee)=sourceState.getSlot0(PoolId.wrap(pool));
        (uint256 growth0,uint256 growth1)=sourceState.getFeeGrowthGlobals(PoolId.wrap(pool));
        return keccak256(abi.encode(sqrt,tick,protocol,fee,growth0,growth1,sourceState.getLiquidity(PoolId.wrap(pool))));
    }
    function _assertPrefunds() internal view {
        assertEq(address(manager).balance,PREFUND);
        assertEq(token.balanceOf(address(manager)),PREFUND);
    }
    function _plan(uint256 amount0,uint256 amount1) internal returns (ZZZLPBalancer.Plan memory) {
        (int24 lower,int24 upper,)=strategy.target(target);
        vm.prank(address(manager));
        return router.plan(target,lower,upper,amount0,amount1);
    }
    function observeRefund() external {
        require(msg.sender==address(token));
        ++callbackCount;callbackSeen=true;
        (callbackLiveLower,callbackLiveUpper,callbackLiveFingerprint)=oracle.priceBounds(address(token));
        (callbackExecutionLower,callbackExecutionUpper,callbackExecutionFingerprint)=_execution().executionBounds(address(token));
        (,,callbackETHFingerprint)=oracle.priceBounds(address(0));
    }

    function testActualIndependentReadersUseSeparateFundedCoreStatesAndPublicReadsStayLive() public {
        assertTrue(address(core)!=address(independentCore));
        assertTrue(target!=referencePool);
        assertEq(referencePool,independentPool,"same key is not same market across distinct cores");
        assertGt(state.getLiquidity(PoolId.wrap(referencePool)),state.getLiquidity(PoolId.wrap(target)));
        (uint256 lower,uint256 upper,bytes32 before)=oracle.priceBounds(address(token));
        (,,bytes32 ethBefore)=oracle.priceBounds(address(0));
        bytes32 independentBefore=_snapshot(independentState,independentPool);
        assertEq(lower,1e18);assertEq(upper,1e18);
        _trade(core,referenceKey,true,1 ether);
        (uint256 changedLower,uint256 changedUpper,bytes32 afterFingerprint)=oracle.priceBounds(address(token));
        assertTrue(before!=afterFingerprint);assertTrue(changedLower!=lower || changedUpper!=upper);
        (uint256 outsideLower,uint256 outsideUpper,bytes32 outsideFingerprint)=_execution().executionBounds(address(token));
        assertEq(outsideLower,changedLower);assertEq(outsideUpper,changedUpper);assertEq(outsideFingerprint,afterFingerprint);
        (,,bytes32 ethAfter)=oracle.priceBounds(address(0));assertEq(ethAfter,ethBefore);
        assertEq(_snapshot(independentState,independentPool),independentBefore);
    }
    function testActualReaderCapturedStateProofMatchesLiveAndHypotheticalReadDoesNotMoveThePool() public {
        IZZZExecutionSpotSource source=IZZZExecutionSpotSource(address(referenceFeed));
        (address observedCore,address observedState,bytes32 pool,MarketState memory initial)=source.executionMarket();
        assertEq(observedCore,address(core));assertEq(observedState,address(state));assertEq(pool,referencePool);
        assertEq(keccak256(abi.encode(initial)),keccak256(abi.encode(_market(state,referencePool))));
        (uint80 round,int256 answer,uint256 started,uint256 updated,uint80 answered)=referenceFeed.latestRoundData();
        (uint80 proofRound,int256 proofAnswer,uint256 proofStarted,uint256 proofUpdated,uint80 proofAnswered)=source.roundAt(initial);
        assertEq(proofRound,round);assertEq(proofAnswer,answer);assertEq(proofStarted,started);
        assertEq(proofUpdated,updated);assertEq(proofAnswered,answered);
        (,MarketState memory expected)=_quoteActualTrade(true,1 ether);
        bytes32 beforePool=_snapshot(state,referencePool);
        (uint80 hypotheticalRound,,,,)=source.roundAt(expected);
        assertTrue(hypotheticalRound!=round);
        assertEq(_snapshot(state,referencePool),beforePool,"hypothetical observation is read only");
        (uint80 stillLive,,,,)=referenceFeed.latestRoundData();assertEq(stillLive,round);
    }
    function _execution() internal view returns (IZZZExecutionOracle) {
        return IZZZExecutionOracle(address(oracle));
    }
    function _market(StateView sourceState,bytes32 pool) internal view returns (MarketState memory result) {
        (result.sqrtPriceX96,result.tick,result.protocolFee,result.lpFee)=sourceState.getSlot0(PoolId.wrap(pool));
        result.liquidity=sourceState.getLiquidity(PoolId.wrap(pool));
    }
    function _quoteActualTrade(bool direction,uint256 amount) internal returns (uint256 output,MarketState memory afterState) {
        uint256 snapshot=vm.snapshotState();
        uint256 beforeOutput=direction?token.balanceOf(address(this)):address(this).balance;
        _trade(core,referenceKey,direction,amount);
        output=(direction?token.balanceOf(address(this)):address(this).balance)-beforeOutput;
        afterState=_market(state,referencePool);
        assertTrue(vm.revertToState(snapshot));
    }
    function _beginStandalone() internal returns (bool owned) {
        vm.prank(address(manager));
        owned=_execution().beginManagerExecution(address(token),target,false);
        assertTrue(owned);assertTrue(_execution().executionActive());
    }
    function _endStandalone(bool owned) internal {
        vm.prank(address(manager));_execution().endManagerExecution(owned);
        assertFalse(_execution().executionActive());
    }
    function _registerTransition(MarketState memory expected) internal {
        vm.prank(address(manager));_execution().beforeSwap(address(core),address(state),referencePool,expected);
    }
    function _finishTransition() internal {
        vm.prank(address(manager));_execution().afterSwap();
    }
    function _transitionProof(bool direction) internal {
        bytes32 targetBefore=_snapshot(state,target);
        bytes32 independentBefore=_snapshot(independentState,independentPool);
        (uint256 lower,uint256 upper,bytes32 captured)=oracle.priceBounds(address(token));
        (,,bytes32 ethBefore)=oracle.priceBounds(address(0));
        (,MarketState memory expected)=_quoteActualTrade(direction,1 ether);
        bool owned=_beginStandalone();
        (uint256 a,uint256 b,bytes32 fingerprint)=_execution().executionBounds(address(token));
        assertEq(a,lower);assertEq(b,upper);assertEq(fingerprint,captured);
        _registerTransition(expected);
        vm.expectRevert(ZZZModule.InvalidState.selector);_execution().executionBounds(address(token));
        vm.expectRevert(ZZZModule.InvalidState.selector);_execution().executionReferenceX96(address(0),address(token));
        _trade(core,referenceKey,direction,1 ether);
        _finishTransition();
        (a,b,fingerprint)=_execution().executionBounds(address(token));
        assertEq(a,lower);assertEq(b,upper);assertEq(fingerprint,captured);
        (,,bytes32 live)=oracle.priceBounds(address(token));assertTrue(live!=captured);
        (,,bytes32 ethAfter)=oracle.priceBounds(address(0));assertEq(ethBefore,ethAfter);
        assertEq(_snapshot(state,target),targetBefore);
        assertEq(_snapshot(independentState,independentPool),independentBefore);
        _endStandalone(owned);
    }
    function testCapturedExecutionBoundsPermitExactQuotedETHToZZZReferenceTransition() public { _transitionProof(true); }
    function testCapturedExecutionBoundsPermitExactQuotedZZZToETHReferenceTransition() public { _transitionProof(false); }
    function _tickCrossingTransition(bool direction) internal {
        _referenceNarrowLiquidity();
        uint128 initialLiquidity=state.getLiquidity(PoolId.wrap(referencePool));
        (,MarketState memory expected)=_quoteActualTrade(direction,2000 ether);
        assertLt(expected.liquidity,initialLiquidity,"the real swap must cross initialized liquidity");
        assertTrue(direction?expected.tick< -10:expected.tick>=10);
        (uint256 lower,uint256 upper,bytes32 fingerprint)=oracle.priceBounds(address(token));
        bytes32 independentBefore=_snapshot(independentState,independentPool);
        bool owned=_beginStandalone();_registerTransition(expected);
        _trade(core,referenceKey,direction,2000 ether);_finishTransition();
        (uint256 a,uint256 b,bytes32 captured)=_execution().executionBounds(address(token));
        assertEq(a,lower);assertEq(b,upper);assertEq(captured,fingerprint);
        assertEq(state.getLiquidity(PoolId.wrap(referencePool)),expected.liquidity);
        assertEq(_snapshot(independentState,independentPool),independentBefore);
        _endStandalone(owned);
    }
    function testQuotedReferenceTransitionAllowsRealDownwardTickCrossingAndLiquidityChange() public { _tickCrossingTransition(true); }
    function testQuotedReferenceTransitionAllowsRealUpwardTickCrossingAndLiquidityChange() public { _tickCrossingTransition(false); }

    function _managerBalance(bool direction) internal {
        uint256 amount0=direction?100 ether:1 ether;
        uint256 amount1=direction?1 ether:100 ether;
        (uint256 lower,uint256 upper,bytes32 fingerprint)=oracle.priceBounds(address(token));
        (,,bytes32 ethFingerprint)=oracle.priceBounds(address(0));
        bytes32 destinationBefore=_snapshot(state,target);
        bytes32 referenceBefore=_snapshot(state,referencePool);
        bytes32 independentBefore=_snapshot(independentState,independentPool);
        uint256 nativeProtocolFees=core.protocolFeesAccrued(Currency.wrap(address(0)));
        uint256 zzzProtocolFees=core.protocolFeesAccrued(Currency.wrap(address(token)));
        ZZZLPBalancer.Plan memory plan=_plan(amount0,amount1);
        assertEq(plan.poolId,referencePool);assertEq(plan.zeroForOne,direction);assertGt(plan.amountIn,0);
        assertEq(_snapshot(state,referencePool),referenceBefore,"quote leaves the reference unchanged");
        assertEq(core.protocolFeesAccrued(Currency.wrap(address(0))),nativeProtocolFees);
        assertEq(core.protocolFeesAccrued(Currency.wrap(address(token))),zzzProtocolFees);
        (uint256 exactOutput,MarketState memory exactAfter)=_quoteActualTrade(direction,plan.amountIn);
        assertEq(plan.amountOut,exactOutput);assertEq(keccak256(abi.encode(plan.afterState)),keccak256(abi.encode(exactAfter)));
        token.arm(address(manager),3,address(this),abi.encodeCall(this.observeRefund,()));
        uint256 ethBefore=address(this).balance;uint256 zzzBefore=token.balanceOf(address(this));
        (uint256 out0,uint256 out1)=manager.balance{value:amount0}(target,0,amount0,amount1,block.timestamp+100);
        assertEq(callbackCount,1);assertTrue(callbackSeen);
        assertEq(callbackExecutionLower,lower);assertEq(callbackExecutionUpper,upper);
        assertEq(callbackExecutionFingerprint,fingerprint);
        assertTrue(callbackLiveFingerprint!=fingerprint,"public reference is live even inside refund callback");
        assertEq(callbackETHFingerprint,ethFingerprint);
        assertEq(_snapshot(state,target),destinationBefore);assertEq(_snapshot(independentState,independentPool),independentBefore);
        assertEq(keccak256(abi.encode(_market(state,referencePool))),keccak256(abi.encode(plan.afterState)));
        if(direction) {
            assertEq(out0,amount0-plan.amountIn);assertEq(out1,amount1+plan.amountOut);
            assertEq(ethBefore-address(this).balance,plan.amountIn);assertEq(token.balanceOf(address(this))-zzzBefore,plan.amountOut);
        } else {
            assertEq(out0,amount0+plan.amountOut);assertEq(out1,amount1-plan.amountIn);
            assertEq(address(this).balance-ethBefore,plan.amountOut);assertEq(zzzBefore-token.balanceOf(address(this)),plan.amountIn);
        }
        _assertPrefunds();
    }
    function testManagerActualReferenceVenueSwapETHToZZZUsesCapturedPricesBeforeRefund() public { _managerBalance(true); }
    function testManagerActualReferenceVenueSwapZZZToETHUsesCapturedPricesBeforeRefund() public { _managerBalance(false); }

    function testStandaloneContextsCannotBeBorrowedAndTwoSequentialOperationsRecaptureLivePrices() public {
        bool owned=_beginStandalone();
        vm.prank(address(manager));vm.expectRevert();_execution().beginManagerExecution(address(token),target,true);
        vm.prank(address(manager));vm.expectRevert();_execution().beginManagerExecution(address(token),target,false);
        vm.prank(address(oracle.contributionPricing()));vm.expectRevert();_execution().beginExecution(address(token));
        _endStandalone(owned);
        _trade(core,referenceKey,true,1 ether);
        (uint256 lower,uint256 upper,bytes32 fingerprint)=oracle.priceBounds(address(token));
        owned=_beginStandalone();
        (uint256 a,uint256 b,bytes32 captured)=_execution().executionBounds(address(token));
        assertEq(a,lower);assertEq(b,upper);assertEq(captured,fingerprint);
        _endStandalone(owned);
        vm.prank(address(manager));vm.expectRevert();_execution().endManagerExecution(owned);
    }
    function testCheapCapturedReadsRejectEveryAssetOtherThanNativeETHAndTheFixedZZZ() public {
        bool owned=_beginStandalone();address other=address(0xBAD);
        vm.expectRevert(abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,other));_execution().executionBounds(other);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);_execution().executionReferenceX96(address(0),other);
        _endStandalone(owned);
    }
    /// @dev Independent pre-coalescing call graph retained from stage2. It
    /// intentionally rereads executionTarget instead of reusing local bounds.
    function _originalPolicyFingerprint(bytes32 venue) internal view returns(bytes32) {
        PoolConfig memory config=registry.accounting(target);
        (,,bytes32 first)=_execution().executionBounds(address(0));
        (,,bytes32 second)=_execution().executionBounds(config.key.currency1);
        bytes32 route=venue==bytes32(0)?bytes32(0):keccak256(abi.encode(registry.accounting(venue)));
        // Original executionTarget path rereads the target and oracle graph.
        PoolConfig memory targetAgain=registry.accounting(target);
        if(!targetAgain.operationsEnabled)revert ZZZModule.InvalidState();
        uint160 referencePrice=_execution().executionReferenceX96(targetAgain.key.currency0,targetAgain.key.currency1);
        ZZZPortfolioPolicy portfolio=strategy.portfolioPolicy();
        (int24 lower,int24 upper)=portfolio.range(targetAgain,referencePrice,strategy.rangeOrientation(target));
        return keccak256(abi.encode(address(registry),registry.configurationRevision(),config,route,
            address(oracle),address(strategy),strategy.executionQualityRevision(),portfolio.controlFingerprint(target),
            lower,upper,referencePrice,first,second));
    }
    function _assertPolicyFingerprintEquivalent() internal view returns(bytes32 actual) {
        assertEq(router.policyFingerprint(target,bytes32(0)),_originalPolicyFingerprint(bytes32(0)));
        assertEq(router.policyFingerprint(target,target),_originalPolicyFingerprint(target));
        actual=router.policyFingerprint(target,referencePool);
        assertEq(actual,_originalPolicyFingerprint(referencePool));
    }
    function originalPolicyFingerprint(bytes32 venue) external view returns(bytes32) {return _originalPolicyFingerprint(venue);}
    function testCoalescedPolicyFingerprintIsByteExactInactiveAndAcrossBothOwnReferenceSwapDirections() public {
        uint256 snapshot=vm.snapshotState();
        for(uint256 i;i<4;++i){
            if(i!=0)assertTrue(vm.revertToState(snapshot));
            if(i>=2)strategy.setRangeOrientation(target,1);
            _assertPolicyFingerprintEquivalent();
            bool direction=i%2==0;
            (,MarketState memory expected)=_quoteActualTrade(direction,1 ether);
            bool owned=_beginStandalone();bytes32 beforeFingerprint=_assertPolicyFingerprintEquivalent();
            _registerTransition(expected);_trade(core,referenceKey,direction,1 ether);_finishTransition();
            assertEq(_assertPolicyFingerprintEquivalent(),beforeFingerprint,"own swap cannot change the captured policy bytes");
            _endStandalone(owned);_assertPolicyFingerprintEquivalent();
        }
        PoolConfig memory disabled=registry.get(target);disabled.operationsEnabled=false;registry.configure(target,disabled);
        vm.expectRevert(ZZZModule.InvalidState.selector);router.policyFingerprint(target,referencePool);
        vm.expectRevert(ZZZModule.InvalidState.selector);this.originalPolicyFingerprint(referencePool);
        disabled.operationsEnabled=true;disabled.rangeBps=10000;registry.configure(target,disabled);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);router.policyFingerprint(target,referencePool);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);this.originalPolicyFingerprint(referencePool);
    }
    function testOnlyPricingOwnsWholeEntryContextAndOnlyTheAuthenticatedVaultManagerCanBorrowIt() public {
        vm.expectRevert();_execution().beginExecution(address(token));
        vm.prank(address(oracle.contributionPricing()));_execution().beginExecution(address(token));
        assertTrue(_execution().executionActive());
        vm.prank(address(manager));vm.expectRevert();_execution().beginManagerExecution(address(token),target,false);
        vm.prank(address(manager));bool owned=_execution().beginManagerExecution(address(token),target,true);
        assertFalse(owned);
        vm.prank(address(manager));_execution().endManagerExecution(owned);
        assertTrue(_execution().executionActive(),"Manager cannot close its lender's captured operation");
        vm.prank(address(oracle.contributionPricing()));_execution().endExecution();
        assertFalse(_execution().executionActive());
    }
    function testTheReferencePoolCannotAlsoBeTheOwnedLPDestination() public {
        bytes32 beforePool=_snapshot(state,referencePool);
        vm.expectRevert();manager.balance{value:100 ether}(referencePool,0,100 ether,0,block.timestamp+100);
        assertEq(_snapshot(state,referencePool),beforePool);_assertPrefunds();
        assertFalse(_execution().executionActive());
    }
    function testAnIndependentCoreMayUseTheDestinationKeyWithoutBecomingOurOwnedLPMarket() public {
        independentKey=targetKey;independentPool=target;
        independentCore.initialize(independentKey,Q96);
        _external(independentCore,independentKey,2_000_000 ether);
        independentReference=_reader(independentCore,independentState,independentKey,ethSecond);
        oracle.setDualFeed(address(token),_source(address(referenceFeed),18,"external pool first"),
            _source(address(independentReference),18,"separate core destination key"),300,REVIEW);
        oracle.setExecutionSource(address(independentReference),true,address(independentReference).codehash,REVIEW);
        assertEq(independentPool,target);assertTrue(address(independentCore)!=address(core));
        _managerBalance(true);
    }
    function testAReaderABIAloneDoesNotAuthorizeNormalizationWithoutReviewedSourceKind() public {
        oracle.setExecutionSource(address(referenceFeed),false,address(referenceFeed).codehash,REVIEW);
        bytes32 beforePool=_snapshot(state,referencePool);uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        vm.expectRevert();manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        assertEq(_snapshot(state,referencePool),beforePool);
        assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);_assertPrefunds();
        assertFalse(_execution().executionActive());
    }
    function unregisteredReferenceScope(bool ownerEnd) external {
        require(msg.sender==address(this));
        (uint256 lower,uint256 upper,bytes32 fingerprint)=oracle.priceBounds(address(token));
        bool owned=_beginStandalone();
        _trade(core,referenceKey,true,1 ether);
        // Captured getters are cheap observations, never write authorization.
        (uint256 a,uint256 b,bytes32 captured)=_execution().executionBounds(address(token));
        assertEq(a,lower);assertEq(b,upper);assertEq(captured,fingerprint);
        if(ownerEnd){vm.prank(address(manager));_execution().endManagerExecution(owned);}
        else _execution().validateExecution();
    }
    function testUnregisteredReferenceMovementCannotHideAtFullValidationOrOwnerEnd() public {
        bytes32 original=_snapshot(state,referencePool);
        uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        for(uint256 i;i<2;++i){
            vm.expectRevert(ZZZModule.InvalidState.selector);this.unregisteredReferenceScope(i!=0);
            assertEq(_snapshot(state,referencePool),original);
            assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);
            assertFalse(_execution().executionActive());
        }
    }
    function wrongTransition(uint8 field) external {
        require(msg.sender==address(this));
        (,MarketState memory expected)=_quoteActualTrade(true,1 ether);
        if(field==0)++expected.tick;
        else if(field==1)++expected.liquidity;
        else if(field==2)++expected.protocolFee;
        else if(field==3)++expected.lpFee;
        else ++expected.sqrtPriceX96;
        _beginStandalone();_registerTransition(expected);_trade(core,referenceKey,true,1 ether);
        _finishTransition();
    }
    function testWrongExpectedTickLiquidityFeesOrSqrtRejectsAndRollsBackTheWholeContext() public {
        bytes32 original=_snapshot(state,referencePool);
        uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        for(uint8 i;i<5;++i) {
            vm.expectRevert();this.wrongTransition(i);
            assertEq(_snapshot(state,referencePool),original);
            assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);
            bool owned=_beginStandalone();_endStandalone(owned);
        }
    }
    function testETHObservationCannotChangeEvenWhenTheReferenceTransitionMatches() public {
        (,MarketState memory expected)=_quoteActualTrade(true,1 ether);
        _beginStandalone();_registerTransition(expected);_trade(core,referenceKey,true,1 ether);
        ethFirst.rounds(2,2);
        vm.prank(address(manager));vm.expectRevert();_execution().afterSwap();
    }
    function testInitialSourceDisagreementRejectsBeforeTakingAnyContribution() public {
        _trade(independentCore,independentKey,false,100_000 ether);
        bytes32 targetBefore=_snapshot(state,target);bytes32 venueBefore=_snapshot(state,referencePool);
        uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        vm.expectRevert();manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        assertEq(_snapshot(state,target),targetBefore);assertEq(_snapshot(state,referencePool),venueBefore);
        assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);_assertPrefunds();
    }
    function distortIndependentReferenceDuringRefund() external {
        require(msg.sender==address(token));
        callbackTrader.swapTokenForETH(100_000 ether);
        (bool ok,bytes memory reason)=address(oracle).staticcall(abi.encodeCall(ZZZOracle.priceBounds,(address(token))));
        assertFalse(ok,"the large outsider trade must violate live source agreement");
        assertEq(reason,abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,address(token)));
    }
    function testPostSwapSourceDisagreementRollsBackSwapFundingAndForeignCallbackTrade() public {
        callbackTrader=new ContextExternalTrader(independentCore,independentKey);token.mint(address(callbackTrader),200_000 ether);
        bytes32 targetBefore=_snapshot(state,target);bytes32 venueBefore=_snapshot(state,referencePool);
        bytes32 independentBefore=_snapshot(independentState,independentPool);
        uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        token.arm(address(manager),3,address(this),abi.encodeCall(this.distortIndependentReferenceDuringRefund,()));
        vm.expectCall(address(this),abi.encodeCall(this.distortIndependentReferenceDuringRefund,()));
        // Exact unapproved market state is rejected even before the separate
        // live-price disagreement check could authorize anything.
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.balance{value:100 ether}(target,0,100 ether,1 ether,block.timestamp+100);
        assertEq(_snapshot(state,target),targetBefore);assertEq(_snapshot(state,referencePool),venueBefore);
        assertEq(_snapshot(independentState,independentPool),independentBefore);
        assertEq(token.balanceOf(address(callbackTrader)),200_000 ether);assertEq(address(callbackTrader).balance,0);
        assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);_assertPrefunds();
        bool owned=_beginStandalone();_endStandalone(owned);
    }
    function changeSmallIndependentMarketAndReadCapturedPrices() external {
        require(msg.sender==address(token));
        bytes32 beforePool=_snapshot(independentState,independentPool);
        callbackTrader.swapTokenForETH(1 ether);
        assertTrue(_snapshot(independentState,independentPool)!=beforePool);
        // The tiny trade remains inside the dual-source spread. Full boundary
        // validation must nevertheless reject its unapproved exact state.
        oracle.priceBounds(address(token));
        (uint256 a,uint256 b,bytes32 fingerprint)=_execution().executionBounds(address(token));
        assertEq(a,callbackExpectedPrice.lower);assertEq(b,callbackExpectedPrice.upper);
        assertEq(fingerprint,callbackExpectedPrice.fingerprint);
    }
    function testMutatingCallbackCannotCommitByReadingTheOldCapturedPriceVector() public {
        callbackTrader=new ContextExternalTrader(independentCore,independentKey);token.mint(address(callbackTrader),10 ether);
        callbackExpectedPrice=_priceCapture(address(token));
        bytes32 beforeVenue=_snapshot(state,referencePool);bytes32 beforeIndependent=_snapshot(independentState,independentPool);
        uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        token.arm(address(manager),3,address(this),abi.encodeCall(this.changeSmallIndependentMarketAndReadCapturedPrices,()));
        vm.expectCall(address(this),abi.encodeCall(this.changeSmallIndependentMarketAndReadCapturedPrices,()));
        vm.expectRevert(ZZZModule.InvalidState.selector);
        manager.balance{value:100 ether}(target,0,100 ether,1 ether,block.timestamp+100);
        assertEq(_snapshot(state,referencePool),beforeVenue);assertEq(_snapshot(independentState,independentPool),beforeIndependent);
        assertEq(token.balanceOf(address(callbackTrader)),10 ether);assertEq(address(callbackTrader).balance,0);
        assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);_assertPrefunds();
        assertFalse(_execution().executionActive());
    }
    function restoreSourceKindDuringRefund() external {
        require(msg.sender==address(token));
        oracle.setExecutionSource(address(referenceFeed),false,address(referenceFeed).codehash,REVIEW);
        oracle.setExecutionSource(address(referenceFeed),true,address(referenceFeed).codehash,REVIEW);
    }
    function testSourceKindDisableAndRestoreCannotReviveTheOldExecutionReview() public {
        uint64 revision=oracle.executionSourceRevision();bytes32 beforePool=_snapshot(state,referencePool);
        uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        token.arm(address(manager),3,address(this),abi.encodeCall(this.restoreSourceKindDuringRefund,()));
        vm.expectRevert();manager.balance{value:100 ether}(target,0,100 ether,1 ether,block.timestamp+100);
        assertEq(oracle.executionSourceRevision(),revision);assertEq(_snapshot(state,referencePool),beforePool);
        assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);_assertPrefunds();
        assertFalse(_execution().executionActive());
    }
    function testWrongQuotedOutputCannotPassEvenWithAValidReferenceTransition() public {
        (int24 lower,int24 upper,)=strategy.target(target);
        ZZZLPBalancer.Plan memory plan=_plan(100 ether,0);assertGt(plan.amountIn,0);
        ++plan.amountOut;
        vm.mockCall(address(router),abi.encodeCall(ZZZLPBalancer.plan,(target,lower,upper,uint256(100 ether),uint256(0))),abi.encode(plan));
        bytes32 targetBefore=_snapshot(state,target);bytes32 venueBefore=_snapshot(state,referencePool);
        uint256 e=address(this).balance;uint256 z=token.balanceOf(address(this));
        vm.expectRevert();manager.balance{value:100 ether}(target,0,100 ether,0,block.timestamp+100);
        vm.clearMockedCalls();
        assertEq(_snapshot(state,target),targetBefore);assertEq(_snapshot(state,referencePool),venueBefore);
        assertEq(address(this).balance,e);assertEq(token.balanceOf(address(this)),z);_assertPrefunds();
        bool owned=_beginStandalone();_endStandalone(owned);
    }
    function _standaloneSwap(bool direction) internal {
        address buyer=address(0xB0BBAC);
        access.bind(Ids.BUYBACK,buyer);vm.deal(buyer,10 ether);token.mint(buyer,10 ether);
        if(!direction) {vm.prank(buyer);token.approve(address(manager),1 ether);}
        (uint256 expected,MarketState memory afterState)=_quoteActualTrade(direction,1 ether);
        bytes32 destinationBefore=_snapshot(state,target);
        uint256 e=buyer.balance;uint256 z=token.balanceOf(buyer);
        vm.prank(buyer);
        uint256 output=manager.swap{value:direction?1 ether:0}(referencePool,direction,1 ether,1,block.timestamp+100);
        assertEq(output,expected);
        assertEq(keccak256(abi.encode(_market(state,referencePool))),keccak256(abi.encode(afterState)));
        assertEq(_snapshot(state,target),destinationBefore);
        if(direction){assertEq(e-buyer.balance,1 ether);assertEq(token.balanceOf(buyer)-z,output);}
        else {assertEq(buyer.balance-e,output);assertEq(z-token.balanceOf(buyer),1 ether);}
        _assertPrefunds();
        bool owned=_beginStandalone();_endStandalone(owned);
    }
    function testStandaloneBuybackManagerSwapETHToZZZCanUseItsReferenceVenue() public { _standaloneSwap(true); }
    function testStandaloneAuthorizedManagerSwapZZZToETHCanUseItsReferenceVenue() public { _standaloneSwap(false); }

    function _installProductionEntryGraph() internal {
        // TEST ONLY MockAccess bootstrap. No real sealed deployment is mutated.
        access.beginBootstrap();
        vault=new ZZZVault(address(access),block.chainid,address(new ZZZMigrationBudget(address(access))));
        nft=new ZZZNFT(address(access),"ipfs://REFERENCE-CONTEXT-TEST/",address(new ZZZNFTMetadata(address(access))));
        nft.setMintEnd(uint64(block.timestamp+365 days));
        membership=new ZZZMembership(address(access));rewards=new ZZZRewards(address(access));
        fees=new ZZZFeeController(address(access));migration=new ZZZMigration(address(access));
        access.bind(Ids.VAULT,address(vault));access.bind(Ids.NFT,address(nft));
        access.bind(Ids.MEMBERSHIP,address(membership));access.bind(Ids.REWARDS,address(rewards));
        access.bind(Ids.FEES,address(fees));access.bind(Ids.MIGRATION,address(migration));
        access.bind(Ids.BUYBACK,address(new ZZZBuyback(address(access),address(token),10000e18)));
        access.setKeeper(address(this),true);rewards.addAsset(address(token));
        migration.configureZZZ(address(token),address(token).codehash,REVIEW);
        vrf=new MockVRF();ProtocolPolicyFixture.randomness(address(access),address(vrf),bytes32(uint256(1)),1,3,500000,false);
        CanonicalFixture.bind(address(access));access.seal();
        entry=ZZZActivationEntry(payable(registry.activationEntry()));
        strategy.setRangeOrientation(target,1);
        _emitEntryBindings();
    }
    function _emitEntryBindings() internal {
        address[24] memory values=[address(entry),address(vault),address(vault.migrationBudget()),
            address(oracle.contributionPricing()),address(oracle),address(manager),manager.positionOperator(),
            address(positions),address(fees),access.protocolPolicy(),address(registry),address(nft),address(rewards),
            address(membership),address(migration),address(core),address(state),address(router),address(referenceFeed),
            address(independentReference),address(independentCore),address(independentState),registry.activationAssets(),address(vrf)];
        address[] memory components=new address[](values.length);bytes32[] memory hashes=new bytes32[](values.length);
        for(uint256 i;i<values.length;++i){components[i]=values[i];hashes[i]=values[i].codehash;}
        emit ReferenceExecutionBindings(components,hashes);
    }
    function _mint(address owner) internal returns(uint256 id) {
        bytes32 reviewed=vault.mintPolicyFingerprint();
        vm.prank(owner);id=vault.mintDormant{value:0.05 ether}(reviewed);
        vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
    }
    /// @dev Candidate-only local gas comparison; measure changed default outcome
    /// without changing any production/default budget or financial assertions.
    function _policy2DiagnosticContribution(address owner,uint256 id,address source,uint256 amount,bool grow) internal {
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(id,target,source,amount,1,block.timestamp+100,grow);
        bytes32 fingerprint=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();
        uint256 oldBucket=vault.nftBucket(id);
        emit ReferenceEntryScenario(EntryScenario(owner,request,300,fingerprint,oldBucket,vault.group(oldBucket).lpTokenId,
            vault.sharesOf(id),oracle.tokenDecimals(source),_priceCapture(source),_priceCapture(address(0)),_priceCapture(address(token))));
        vm.startPrank(owner);
        if(source!=address(0))token.approve(address(entry),amount);
        _candidateDefaultGasProbe(owner,request,fingerprint);
        _coolEntry();uint256 beforeGas=gasleft();
        entry.executeReviewed{value:source==address(0)?amount:0,gas:POLICY2_DIAGNOSTIC_GAS_BUDGET}(request,300,fingerprint);
        uint256 used=beforeGas-gasleft();
        vm.stopPrank();
        emit log_named_uint(grow?"execution-reference.policy2-diagnostic.cold.grow.call-gas":"execution-reference.policy2-diagnostic.cold.activate.call-gas",used);
        assertLe(used+Math.ceilDiv(used,5),POLICY2_DIAGNOSTIC_GAS_BUDGET,"explicit local policy2 diagnostic still needs full20% headroom");
        emit log_named_uint("gas-feasibility.candidate.call-with-full20pct",used+Math.ceilDiv(used,5));
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        (uint256 principal0,uint256 principal1)=manager.amounts(p.lpTokenId);
        emit ReferenceEntryOutcome(EntryOutcome(id,bucket,p.lpTokenId,vault.sharesOf(id),vault.bucketTotalShares(bucket),
            positions.getPositionLiquidity(p.lpTokenId),principal0,principal1,p.idle0,p.idle1,_execution().executionActive(),used));
    }
    /// @dev TEST ONLY: isolate a bounded probe so changed gas success never
    /// duplicates activation or consumes approvals before the measured call.
    function _candidateDefaultGasProbe(address owner,ZZZActivationEntry.Request memory request,bytes32 fingerprint) internal {
        bytes32 beforeState=_entryAtomicState(owner,request.nftId);
        uint256 probe=vm.snapshotState();
        _coolEntry();
        (bool ok,bytes memory reason)=address(entry).call{
            value:request.sourceAsset==address(0)?request.amountIn:0,gas:DEFAULT_ENTRY_GAS_BUDGET
        }(abi.encodeCall(ZZZActivationEntry.executeReviewed,(request,uint16(300),fingerprint)));
        if(!ok)assertEq(_entryAtomicState(owner,request.nftId),beforeState,"failed default probe must preserve all economic state");
        assertFalse(_execution().executionActive());
        assertTrue(vm.revertToState(probe),"restore exact state after candidate default probe");
        assertEq(_entryAtomicState(owner,request.nftId),beforeState,"candidate probe must not alter the measured starting state");
        emit log_named_uint("gas-feasibility.candidate.default12M.call-succeeded",ok?1:0);
        if(!ok)emit ReferenceDefaultBudgetRejected(request.nftId,request.increase,DEFAULT_ENTRY_GAS_BUDGET,keccak256(reason));
    }
    function _entryAtomicState(address owner,uint256 id) internal view returns(bytes32 hash) {
        uint256 bucket=vault.nftBucket(id);Position memory p=vault.group(bucket);
        hash=keccak256(abi.encode(owner,nft.ownerOf(id),bucket,p,vault.sharesOf(id),vault.bucketTotalShares(bucket),
            vault.bucketCount(),vault.poolBucket(target)));
        hash=keccak256(abi.encode(hash,membership.eligible(id),membership.totalEligible(),
            nft.royaltyRewards().weightOf(id),nft.royaltyRewards().totalWeight(),positions.nextTokenId(),manager.activeSecondaryCount(),
            vault.migrationBudget().compositionEpoch(bucket),vault.migrationBudget().lastCompound(bucket)));
        if(p.lpTokenId!=0){
            uint256 residual=manager.secondaryId(p.lpTokenId);
            hash=keccak256(abi.encode(hash,positions.ownerOf(p.lpTokenId),positions.getApproved(p.lpTokenId),
                positions.getPositionLiquidity(p.lpTokenId),residual,manager.executionPortfolioFingerprint(p.lpTokenId)));
            if(residual!=0)hash=keccak256(abi.encode(hash,positions.ownerOf(residual),positions.getPositionLiquidity(residual)));
        }
        address[9] memory accounts=[owner,address(this),address(entry),address(vault),address(manager),manager.positionOperator(),
            address(positions),address(fees),address(rewards)];
        for(uint256 i;i<accounts.length;++i)hash=keccak256(abi.encode(hash,accounts[i],accounts[i].balance,token.balanceOf(accounts[i])));
        hash=keccak256(abi.encode(hash,token.allowance(owner,address(entry)),token.allowance(address(entry),address(vault)),
            token.allowance(address(vault),address(manager)),token.allowance(address(vault),manager.positionOperator()),
            token.allowance(address(manager),address(permit)),token.allowance(manager.positionOperator(),address(permit))));
        hash=keccak256(abi.encode(hash,_snapshot(state,target),_snapshot(state,referencePool),_snapshot(independentState,independentPool),
            core.protocolFeesAccrued(Currency.wrap(address(0))),core.protocolFeesAccrued(Currency.wrap(address(token)))));
        address[2] memory assets=[address(0),address(token)];
        for(uint256 i;i<assets.length;++i)hash=keccak256(abi.encode(hash,fees.dust(bucket,assets[i]),fees.compoundBalance(bucket,assets[i]),
            fees.buybackBalance(assets[i]),fees.accounted(assets[i]),rewards.liabilities(assets[i]),rewards.claimable(id,assets[i])));
        uint256[6] memory books;
        (books[0],books[1],books[2])=rewards.allocationTree(0);
        (books[3],books[4],books[5])=rewards.allocationTree(bucket);
        return keccak256(abi.encode(hash,books,_execution().executionActive()));
    }
    function _coolEntry() internal {
        // Foundry cool marks an account AND all its accessed storage slots cold.
        // This is local EVM engineering evidence, not Robinhood gas approval.
        address pricing=address(oracle.contributionPricing());address executor=manager.positionOperator();
        address budget=address(vault.migrationBudget());address policy=access.protocolPolicy();
        address portfolio=address(strategy.portfolioPolicy());address confirmation=address(strategy.rebalanceConfirmation());
        address math=address(router.balanceMath());address royalty=address(nft.royaltyRewards());
        address assets=registry.activationAssets();
        vm.cool(address(entry));vm.cool(address(vault));vm.cool(budget);vm.cool(pricing);vm.cool(address(oracle));
        vm.cool(address(manager));vm.cool(executor);vm.cool(address(router));vm.cool(math);vm.cool(address(positions));vm.cool(address(permit));
        vm.cool(address(core));vm.cool(address(state));vm.cool(address(independentCore));vm.cool(address(independentState));
        vm.cool(address(referenceFeed));vm.cool(address(independentReference));vm.cool(address(ethFirst));vm.cool(address(ethSecond));
        vm.cool(address(registry));vm.cool(assets);vm.cool(address(access));vm.cool(policy);
        vm.cool(address(nft));vm.cool(royalty);vm.cool(address(membership));vm.cool(address(rewards));vm.cool(address(fees));
        vm.cool(address(migration));vm.cool(address(strategy));vm.cool(portfolio);vm.cool(confirmation);vm.cool(address(token));
    }
    function _priceCapture(address asset) internal view returns(PriceCapture memory captured) {
        (captured.lower,captured.upper,captured.fingerprint)=oracle.priceBounds(asset);
    }
    function _actualMainValue(uint256 bucket,uint256 price0,uint256 price1) internal view returns(uint256) {
        Position memory p=vault.group(bucket);
        (uint256 a0,uint256 a1)=manager.amounts(p.lpTokenId);
        return Math.mulDiv(a0,price0,1e18)+Math.mulDiv(a1,price1,1e18);
    }
    function _checkEntryAsset(address source) internal {
        _installProductionEntryGraph();
        address owner=address(0xA11CE);vm.deal(owner,10000 ether);token.mint(owner,10000 ether);
        uint256 id=_mint(owner);
        (uint256 price0,,)=oracle.priceBounds(address(0));
        (uint256 price1,,)=oracle.priceBounds(address(token));
        uint256 sourceUpper; (,sourceUpper,)=oracle.priceBounds(source);
        uint256 input=1000 ether;uint256 upperInput=Math.mulDiv(input,sourceUpper,1e18,Math.Rounding.Ceil);
        uint256 minimumAdded=upperInput-Math.mulDiv(upperInput,300,10000);
        bytes32 referenceBefore=_snapshot(state,referencePool);
        _policy2DiagnosticContribution(owner,id,source,input,false);
        uint256 bucket=vault.nftBucket(id);Position memory first=vault.group(bucket);
        uint256 initialShares=vault.sharesOf(id);
        assertGt(initialShares,0);assertEq(vault.bucketTotalShares(bucket),initialShares);
        assertEq(nft.ownerOf(id),owner);assertTrue(membership.eligible(id));
        assertGe(_actualMainValue(bucket,price0,price1),minimumAdded,"activation proves actual marginal deployed principal");
        assertEq(positions.ownerOf(first.lpTokenId),address(vault));assertEq(manager.secondaryId(first.lpTokenId),0);
        assertTrue(_snapshot(state,referencePool)!=referenceBefore);
        (int24 lower,int24 upper)=manager.ticks(first.lpTokenId);
        uint128 mainL=positions.getPositionLiquidity(first.lpTokenId);
        vm.warp(block.timestamp+17);
        // Capture the NEXT operation's live independent valuation. It is not
        // the previous operation's frozen basis or the target pool's spot.
        (price0,,)=oracle.priceBounds(address(0));(price1,,)=oracle.priceBounds(address(token));
        uint256 beforeLP=_actualMainValue(bucket,price0,price1);
        (,sourceUpper,)=oracle.priceBounds(source);input=100 ether;
        upperInput=Math.mulDiv(input,sourceUpper,1e18,Math.Rounding.Ceil);
        minimumAdded=upperInput-Math.mulDiv(upperInput,300,10000);
        _policy2DiagnosticContribution(owner,id,source,input,true);
        Position memory last=vault.group(bucket);
        assertEq(last.lpTokenId,first.lpTokenId);assertEq(last.centerX96,first.centerX96);
        assertEq(last.lastRebalance,first.lastRebalance,"growth never resets the shared rebalance clock");
        (int24 finalLower,int24 finalUpper)=manager.ticks(last.lpTokenId);assertEq(finalLower,lower);assertEq(finalUpper,upper);
        assertGt(positions.getPositionLiquidity(last.lpTokenId),mainL);assertGt(vault.sharesOf(id),initialShares);
        assertEq(vault.bucketTotalShares(bucket),vault.sharesOf(id));
        (uint256 treeWeight,,)=rewards.allocationTree(bucket);assertEq(treeWeight,vault.sharesOf(id));
        assertGe(_actualMainValue(bucket,price0,price1)-beforeLP,minimumAdded,"growth uses only newly funded marginal LP");
        assertEq(token.allowance(owner,address(entry)),0);assertEq(token.allowance(address(entry),address(vault)),0);
        assertEq(address(entry).balance,0);assertEq(token.balanceOf(address(entry)),0);_assertPrefunds();
        assertFalse(_execution().executionActive());
        bool owned=_beginStandalone();_endStandalone(owned);
    }
    function testPolicy2DiagnosticActualEntryETHActivationAndGrowthUseTheReferencedSwapVenueAndExactLPShares() public { _checkEntryAsset(address(0)); }
    function testPolicy2DiagnosticActualEntryZZZActivationAndGrowthUseTheReferencedSwapVenueAndExactLPShares() public { _checkEntryAsset(address(token)); }
    function testPolicy2DiagnosticSecondActualEntrantIssuesOnlyNetNewNAVSharesAndPreservesTheIncumbentPosition() public {
        _installProductionEntryGraph();
        address alice=address(0xA11CE);address bob=address(0xB0B);
        vm.deal(alice,10000 ether);vm.deal(bob,10000 ether);token.mint(alice,10000 ether);token.mint(bob,10000 ether);
        uint256 firstId=_mint(alice);uint256 secondId=_mint(bob);
        _policy2DiagnosticContribution(alice,firstId,address(0),1000 ether,false);
        uint256 bucket=vault.nftBucket(firstId);Position memory beforePosition=vault.group(bucket);
        vm.warp(block.timestamp+23);
        uint256 shares=vault.sharesOf(firstId);uint256 supply=vault.bucketTotalShares(bucket);
        (uint256 price0,,)=oracle.priceBounds(address(0));(uint256 price1,,)=oracle.priceBounds(address(token));
        uint256 beforeNAV=_actualMainValue(bucket,price0,price1)+Math.mulDiv(beforePosition.idle0,price0,1e18)+
            Math.mulDiv(beforePosition.idle1,price1,1e18);
        _policy2DiagnosticContribution(bob,secondId,address(token),1000 ether,false);
        Position memory afterPosition=vault.group(bucket);
        uint256 afterNAV=_actualMainValue(bucket,price0,price1)+Math.mulDiv(afterPosition.idle0,price0,1e18)+
            Math.mulDiv(afterPosition.idle1,price1,1e18);
        uint256 expectedShares=Math.mulDiv(supply,afterNAV-beforeNAV,beforeNAV);
        assertEq(vault.sharesOf(firstId),shares);assertEq(vault.sharesOf(secondId),expectedShares);
        assertEq(vault.bucketTotalShares(bucket),supply+expectedShares);assertEq(vault.nftBucket(secondId),bucket);
        assertEq(afterPosition.lpTokenId,beforePosition.lpTokenId);assertEq(afterPosition.centerX96,beforePosition.centerX96);
        assertEq(afterPosition.lastRebalance,beforePosition.lastRebalance);assertEq(manager.secondaryId(afterPosition.lpTokenId),0);
        assertEq(nft.ownerOf(firstId),alice);assertEq(nft.ownerOf(secondId),bob);
        assertTrue(membership.eligible(firstId));assertTrue(membership.eligible(secondId));assertEq(membership.totalEligible(),2);
        (uint256 treeWeight,,)=rewards.allocationTree(bucket);assertEq(treeWeight,supply+expectedShares);
        assertFalse(_execution().executionActive());_assertPrefunds();
    }
    function testActualEntryFinalLPFloorFailureRollsBackSwapSharesMembershipAndApproval() public {
        _installProductionEntryGraph();
        address owner=address(0xA11CE);vm.deal(owner,10000 ether);token.mint(owner,10000 ether);
        uint256 id=_mint(owner);
        bytes32 targetBefore=_snapshot(state,target);bytes32 venueBefore=_snapshot(state,referencePool);
        uint256 e=owner.balance;uint256 z=token.balanceOf(owner);
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(id,target,address(0),1000 ether,
            type(uint128).max,block.timestamp+100,false);
        bytes32 fingerprint=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();
        vm.prank(owner);vm.expectRevert();entry.executeReviewed{value:request.amountIn}(request,300,fingerprint);
        assertEq(_snapshot(state,target),targetBefore);assertEq(_snapshot(state,referencePool),venueBefore);
        assertEq(owner.balance,e);assertEq(token.balanceOf(owner),z);assertEq(nft.ownerOf(id),owner);
        assertEq(vault.nftBucket(id),0);assertEq(vault.sharesOf(id),0);assertFalse(membership.eligible(id));
        assertEq(address(entry).balance,0);assertEq(token.balanceOf(address(entry)),0);
        assertEq(token.allowance(address(entry),address(vault)),0);assertFalse(_execution().executionActive());_assertPrefunds();
    }
    /// @dev Optional local producer utility, not a default security assertion.
    /// Its copied test profile alone grants writes to the owned export folder.
    function testExportReferenceEntryFixtureForOwnedAnvil() public {
        string memory path=vm.envOr("POPL_REFERENCE_EXPORT_PATH",string(""));
        if(bytes(path).length==0){vm.skip(true,"optional owned-state export not requested");return;}
        string memory baselinePath=string.concat(path,".setup.json");
        assertTrue(exportSetupHash!=bytes32(0));
        assertEq(keccak256(bytes(vm.readFile(baselinePath))),exportSetupHash);
        emit ReferenceExportBaseline(baselinePath,exportSetupHash);
        bool zzzInput=vm.envOr("POPL_REFERENCE_EXPORT_ZZZ",false);
        bool growth=vm.envOr("POPL_REFERENCE_EXPORT_GROW",false);
        _installProductionEntryGraph();
        address owner=address(0xA11CE);vm.deal(owner,10000 ether);token.mint(owner,10000 ether);
        uint256 id=_mint(owner);address source=zzzInput?address(token):address(0);
        if(growth){
            // Establish real active state for the later RPC growth call. This
            // export utility is not the separate unchanged 12M gas admission.
            ZZZActivationEntry.Request memory activate=ZZZActivationEntry.Request(id,target,source,1000 ether,1,block.timestamp+100,false);
            bytes32 activationPolicy=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();
            vm.startPrank(owner);if(zzzInput)token.approve(address(entry),activate.amountIn);
            entry.executeReviewed{value:zzzInput?0:activate.amountIn}(activate,300,activationPolicy);
            vm.stopPrank();vm.warp(block.timestamp+17);
        }
        uint256 amount=growth?100 ether:1000 ether;
        if(zzzInput){vm.prank(owner);token.approve(address(entry),amount);}
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(id,target,source,amount,1,block.timestamp+100,growth);
        bytes32 fingerprint=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();uint256 bucket=vault.nftBucket(id);
        emit ReferenceEntryScenario(EntryScenario(owner,request,300,fingerprint,bucket,vault.group(bucket).lpTokenId,
            vault.sharesOf(id),oracle.tokenDecimals(source),_priceCapture(source),_priceCapture(address(0)),_priceCapture(address(token))));
        assertFalse(_execution().executionActive());
        emit ReferenceExportBlock(block.number,block.timestamp,block.chainid);
        _materializeExportGraph();
        vm.dumpState(path);
    }
    function _materializeExportGraph() internal {
        // dumpState can omit setup-only stateless accounts. Write back exactly
        // their existing runtime in this isolated test VM, preserving storage,
        // balances, identities and every configured code hash. No production
        // source, live chain or public transaction uses this fixture utility.
        address[36] memory components=[address(entry),address(vault),address(vault.migrationBudget()),
            address(oracle.contributionPricing()),address(oracle),address(manager),manager.positionOperator(),
            address(positions),address(fees),access.protocolPolicy(),address(registry),address(nft),address(rewards),
            address(membership),address(migration),address(core),address(state),address(router),address(referenceFeed),
            address(independentReference),address(independentCore),address(independentState),registry.activationAssets(),address(vrf),
            address(this),address(access),address(permit),address(router.balanceMath()),address(strategy),
            address(strategy.portfolioPolicy()),address(strategy.rebalanceConfirmation()),address(ethFirst),address(ethSecond),
            access.activationAssetsFactory(),access.royaltyFactory(),address(token)];
        for(uint256 i;i<components.length;++i){
            address targetAddress=components[i];bytes memory runtime=targetAddress.code;bytes32 beforeHash=targetAddress.codehash;
            assertGt(runtime.length,0);vm.etch(targetAddress,runtime);assertEq(targetAddress.codehash,beforeHash);
            emit ReferenceExportCodeMaterialized(targetAddress,beforeHash,runtime.length);
        }
    }
    // New maintenance cohort only: its extra real coordinator is never added
    // to the unchanged Entry comparison graph or its deployment nonce stream.
    ZZZCompounder internal maintenanceCompounder;
    function _installMaintenanceGraph() internal returns(address owner,uint256 id,uint256 bucket) {
        return _installMaintenanceGraph(false);
    }
    function _installMaintenanceGraph(bool hybrid) internal returns(address owner,uint256 id,uint256 bucket) {
        access.beginBootstrap();
        maintenanceCompounder=new ZZZCompounder(address(access));
        access.bind(Ids.COMPOUNDER,address(maintenanceCompounder));
        _installProductionEntryGraph();
        if(hybrid)strategy.portfolioPolicy().setMode(target,true,REVIEW);
        owner=address(0xA11CE);vm.deal(owner,10000 ether);token.mint(owner,10000 ether);
        id=_mint(owner);
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(id,target,address(0),1000 ether,1,block.timestamp+100,false);
        bytes32 fingerprint=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();
        (uint256 price0,,)=oracle.priceBounds(address(0));(uint256 price1,,)=oracle.priceBounds(address(token));
        vm.prank(owner);
        entry.executeReviewed{value:request.amountIn,gas:POLICY2_DIAGNOSTIC_GAS_BUDGET}(request,300,fingerprint);
        bucket=vault.nftBucket(id);
        assertGe(_actualMainValue(bucket,price0,price1),970 ether,"maintenance bootstrap still proves97% deployed LP");
        assertEq(vault.bucketTotalShares(bucket),vault.sharesOf(id));
        assertFalse(_execution().executionActive());
    }
    function _freshMaintenanceFeeds() internal {
        ethFirst.set(1e8,block.timestamp,block.timestamp);
        ethSecond.set(1e8,block.timestamp,block.timestamp);
    }
    function _coldMaintenance() internal {
        _coolEntry();vm.cool(address(maintenanceCompounder));
    }
    function _measureMaintenance(address owner,uint256 id,address destination,bytes memory input,string memory label)
        internal returns(uint256 used) {
        bytes32 beforeState=_entryAtomicState(owner,id);
        uint256 probe=vm.snapshotState();
        _coldMaintenance();
        (bool defaultSucceeded,)=destination.call{gas:DEFAULT_ENTRY_GAS_BUDGET}(input);
        if(!defaultSucceeded)assertEq(_entryAtomicState(owner,id),beforeState,"failed maintenance default probe is atomic");
        assertFalse(_execution().executionActive());
        assertTrue(vm.revertToState(probe));
        assertEq(_entryAtomicState(owner,id),beforeState,"probe never consumes principal or reserve funds");
        emit log_named_uint(string.concat(label,".default12M.call-succeeded"),defaultSucceeded?1:0);
        _coldMaintenance();uint256 beforeGas=gasleft();
        (bool ok,bytes memory reason)=destination.call{gas:POLICY2_DIAGNOSTIC_GAS_BUDGET}(input);
        used=beforeGas-gasleft();
        if(!ok)emit log_named_bytes("gas-feasibility.maintenance.failure",reason);
        assertTrue(ok,"full production maintenance operation must succeed under explicit local diagnostic budget");
        emit log_named_uint(string.concat(label,".cold.call-gas"),used);
        emit log_named_uint(string.concat(label,".call-with-full20pct"),used+Math.ceilDiv(used,5));
        assertLe(used+Math.ceilDiv(used,5),POLICY2_DIAGNOSTIC_GAS_BUDGET);
        assertFalse(_execution().executionActive());_assertPrefunds();
    }
    function _tradeToMaintenancePrice(PoolManager sourceCore,CoreKey memory key,uint160 next) internal {
        // Actions4/5 are test-only real-core swaps with an explicit sqrt limit;
        // it does not overwrite pool storage or bypass any production guard.
        StateView sourceState=address(sourceCore)==address(core)?state:independentState;
        (uint160 current,,,)=sourceState.getSlot0(PoolId.wrap(keccak256(abi.encode(key))));
        sourceCore.unlock(abi.encode(next<current?uint8(4):uint8(5),key,int256(2_000_000 ether),next));
    }
    function _prepareOrdinaryRebalance(uint256 bucket) internal {
        _prepareOrdinaryRebalanceAt(bucket,uint160(uint256(Q96)*83/100));
    }
    function _prepareOrdinaryRebalanceAt(uint256 bucket,uint160 next) internal {
        Position memory p=vault.group(bucket);
        vm.warp(uint256(p.lastRebalance)+43200);_freshMaintenanceFeeds();
        _tradeToMaintenancePrice(core,targetKey,next);
        _tradeToMaintenancePrice(core,referenceKey,next);
        _tradeToMaintenancePrice(independentCore,independentKey,next);
        ZZZRebalanceConfirmation confirmation=strategy.rebalanceConfirmation();
        confirmation.configure(600,300,REVIEW);
        (uint8 physical,uint8 independent)=confirmation.marketSides(bucket);
        assertGt(physical,0);assertEq(physical,independent);
        (,,bool manual)=confirmation.condition(bucket);assertFalse(manual);
        assertTrue(strategy.needsRebalance(bucket));assertFalse(strategy.rebalanceReady(bucket));
        assertFalse(confirmation.observe(bucket));
        for(uint256 i;i<3;++i){
            vm.warp(block.timestamp+240);_freshMaintenanceFeeds();
            assertEq(confirmation.observe(bucket),i==2,"ordinary sampled evidence keeps600s duration and300s maximum gap");
        }
        assertTrue(strategy.rebalanceReady(bucket));
    }
    function testGasFeasibilityFullHarvestAllocatesActualFeesWithoutMovingPrincipal() public {
        (address owner,uint256 id,uint256 bucket)=_installMaintenanceGraph();
        _trade(core,targetKey,true,100 ether);
        Position memory beforePosition=vault.group(bucket);
        uint128 beforeL=positions.getPositionLiquidity(beforePosition.lpTokenId);
        uint256 beforeShares=vault.sharesOf(id);
        uint256[6] memory beforeBooks=[address(fees).balance,address(rewards).balance,fees.dust(bucket,address(0)),
            fees.compoundBalance(bucket,address(0)),fees.buybackBalance(address(0)),rewards.liabilities(address(0))];
        _measureMaintenance(owner,id,address(vault),abi.encodeCall(ZZZVault.collectFees,(bucket,block.timestamp+100)),
            "gas-feasibility.harvest");
        uint256 receipt=address(fees).balance-beforeBooks[0]+address(rewards).balance-beforeBooks[1];
        assertGt(receipt,0,"harvest must receive actual funded fees");uint256 units=(beforeBooks[2]+receipt)/20;
        assertEq(fees.compoundBalance(bucket,address(0))-beforeBooks[3],units);
        assertEq(fees.buybackBalance(address(0))-beforeBooks[4],units);
        assertEq(rewards.liabilities(address(0))-beforeBooks[5],units*18);
        assertEq(fees.dust(bucket,address(0)),(beforeBooks[2]+receipt)%20);
        Position memory afterPosition=vault.group(bucket);
        assertEq(keccak256(abi.encode(afterPosition)),keccak256(abi.encode(beforePosition)));
        assertEq(positions.getPositionLiquidity(afterPosition.lpTokenId),beforeL);assertEq(vault.sharesOf(id),beforeShares);
    }
    function testGasFeasibilityFullCompoundUsesCapturedPricesAndPreservesOwnerSharesAndMainGeometry() public {
        (address owner,uint256 id,uint256 bucket)=_installMaintenanceGraph();
        _trade(core,targetKey,true,100 ether);vault.collectFees(bucket,block.timestamp+100);
        Position memory beforePosition=vault.group(bucket);
        uint128 beforeL=positions.getPositionLiquidity(beforePosition.lpTokenId);
        uint256 beforeShares=vault.sharesOf(id);uint256 beforeSupply=vault.bucketTotalShares(bucket);
        uint256 reserve=fees.compoundBalance(bucket,address(0));assertGt(reserve,0);
        uint256 rewardLiability=rewards.liabilities(address(0));uint256 buyback=fees.buybackBalance(address(0));
        vm.warp(uint256(beforePosition.lastRebalance)+3601);_freshMaintenanceFeeds();
        assertTrue(vault.migrationBudget().compoundReady(bucket));
        _measureMaintenance(owner,id,address(maintenanceCompounder),
            abi.encodeCall(ZZZCompounder.compound,(bucket,uint128(1),block.timestamp+100)),"gas-feasibility.compound");
        Position memory afterPosition=vault.group(bucket);
        assertEq(afterPosition.lpTokenId,beforePosition.lpTokenId);assertEq(afterPosition.centerX96,beforePosition.centerX96);
        assertEq(afterPosition.lastRebalance,beforePosition.lastRebalance);assertGt(positions.getPositionLiquidity(afterPosition.lpTokenId),beforeL);
        assertEq(vault.sharesOf(id),beforeShares);assertEq(vault.bucketTotalShares(bucket),beforeSupply);
        assertEq(nft.ownerOf(id),owner);assertTrue(membership.eligible(id));assertEq(manager.secondaryId(afterPosition.lpTokenId),0);
        assertEq(vault.migrationBudget().lastCompound(bucket),block.timestamp);
        assertGe(rewards.liabilities(address(0)),rewardLiability);assertGe(fees.buybackBalance(address(0)),buyback);
        assertLt(fees.compoundBalance(bucket,address(0)),reserve,"designated compound was reinvested, never claimed or burned");
        assertEq(token.allowance(address(vault),address(manager)),0);assertEq(token.allowance(address(vault),manager.positionOperator()),0);
    }
    function testGasFeasibilityOrdinaryVaultRebalanceRetainsCooldownSamplesAndFullPriceGuards() public {
        (address owner,uint256 id,uint256 bucket)=_installMaintenanceGraph();
        Position memory beforePosition=vault.group(bucket);
        uint256 beforeShares=vault.sharesOf(id);uint256 beforeSupply=vault.bucketTotalShares(bucket);
        _prepareOrdinaryRebalance(bucket);
        _measureMaintenance(owner,id,address(vault),abi.encodeCall(ZZZVault.rebalance,
            (bucket,uint128(1),block.timestamp+100)),"gas-feasibility.rebalance");
        Position memory afterPosition=vault.group(bucket);
        assertTrue(afterPosition.lpTokenId!=beforePosition.lpTokenId);assertTrue(afterPosition.centerX96!=beforePosition.centerX96);
        assertEq(afterPosition.lastRebalance,block.timestamp);assertEq(vault.sharesOf(id),beforeShares);
        assertEq(vault.bucketTotalShares(bucket),beforeSupply);assertEq(nft.ownerOf(id),owner);assertTrue(membership.eligible(id));
        assertEq(positions.ownerOf(afterPosition.lpTokenId),address(vault));assertGt(positions.getPositionLiquidity(afterPosition.lpTokenId),0);
        assertEq(manager.secondaryId(afterPosition.lpTokenId),0);(int24 lower,int24 upper)=manager.ticks(afterPosition.lpTokenId);
        (,int24 tick,,)=state.getSlot0(PoolId.wrap(target));assertGe(tick,lower);assertLt(tick,upper);
        assertEq(token.allowance(address(vault),address(manager)),0);assertEq(token.allowance(address(vault),manager.positionOperator()),0);
    }
    function testGasFeasibilityMaintenanceSourceFaultsPreservePrincipalAndEarnedReserveBooks() public {
        (address owner,uint256 id,uint256 bucket)=_installMaintenanceGraph();
        _trade(core,targetKey,true,100 ether);vault.collectFees(bucket,block.timestamp+100);
        vm.warp(block.timestamp+3601);_freshMaintenanceFeeds();
        ethSecond.set(1e8,block.timestamp-3601,block.timestamp-3601);
        bytes32 beforeState=_entryAtomicState(owner,id);
        (bool ok,bytes memory reason)=address(maintenanceCompounder).call{gas:POLICY2_DIAGNOSTIC_GAS_BUDGET}(
            abi.encodeCall(ZZZCompounder.compound,(bucket,uint128(1),block.timestamp+100)));
        assertFalse(ok,"stale independent ETH publication must stop compound");
        assertEq(reason,abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,address(0)));
        assertEq(_entryAtomicState(owner,id),beforeState);assertFalse(_execution().executionActive());
        _freshMaintenanceFeeds();_prepareOrdinaryRebalance(bucket);
        _tradeToMaintenancePrice(independentCore,independentKey,uint160(uint256(Q96)*80/100));
        beforeState=_entryAtomicState(owner,id);
        (ok,reason)=address(vault).call{gas:POLICY2_DIAGNOSTIC_GAS_BUDGET}(
            abi.encodeCall(ZZZVault.rebalance,(bucket,uint128(1),block.timestamp+100)));
        assertFalse(ok,"independent ZZZ disagreement must stop ordinary rebalancing");
        assertEq(reason,abi.encodeWithSelector(ZZZOracle.InvalidPrice.selector,address(token)));
        assertEq(_entryAtomicState(owner,id),beforeState);assertFalse(_execution().executionActive());_assertPrefunds();
    }
    function testGasFeasibilityHybridOpeningThenTwoLegHarvestAndOrdinaryReplacementKeepAllBacking() public {
        (address owner,uint256 id,uint256 bucket)=_installMaintenanceGraph(true);
        uint256 shares=vault.sharesOf(id);_prepareOrdinaryRebalance(bucket);
        _measureMaintenance(owner,id,address(vault),abi.encodeCall(ZZZVault.rebalance,
            (bucket,uint128(1),block.timestamp+100)),"gas-feasibility.hybrid.open");
        uint256 firstMain=vault.group(bucket).lpTokenId;uint256 firstResidual=manager.secondaryId(firstMain);
        assertGt(firstResidual,0);assertEq(positions.ownerOf(firstResidual),address(vault));
        assertGt(positions.getPositionLiquidity(firstResidual),0);assertEq(manager.activeSecondaryCount(),1);
        uint160 mixedPrice=uint160(uint256(Q96)*86/100);
        _tradeToMaintenancePrice(core,targetKey,mixedPrice);
        _tradeToMaintenancePrice(core,referenceKey,mixedPrice);
        _tradeToMaintenancePrice(independentCore,independentKey,mixedPrice);
        uint256 liability=rewards.liabilities(address(0));uint256 mainL=positions.getPositionLiquidity(firstMain);
        uint256 residualL=positions.getPositionLiquidity(firstResidual);
        _measureMaintenance(owner,id,address(vault),abi.encodeCall(ZZZVault.collectFees,
            (bucket,block.timestamp+100)),"gas-feasibility.hybrid.harvest-two-legs");
        assertEq(positions.getPositionLiquidity(firstMain),mainL);
        assertEq(positions.getPositionLiquidity(firstResidual),residualL);assertGe(rewards.liabilities(address(0)),liability);
        _prepareOrdinaryRebalanceAt(bucket,uint160(uint256(Q96)*69/100));
        _measureMaintenance(owner,id,address(vault),abi.encodeCall(ZZZVault.rebalance,
            (bucket,uint128(1),block.timestamp+100)),"gas-feasibility.hybrid.replace-two-legs");
        uint256 nextMain=vault.group(bucket).lpTokenId;uint256 nextResidual=manager.secondaryId(nextMain);
        assertTrue(nextMain!=firstMain);assertTrue(nextResidual!=firstResidual);assertGt(nextResidual,0);
        assertEq(manager.activeSecondaryCount(),1);assertEq(positions.ownerOf(nextMain),address(vault));
        assertEq(positions.ownerOf(nextResidual),address(vault));assertGt(positions.getPositionLiquidity(nextMain),0);
        assertGt(positions.getPositionLiquidity(nextResidual),0);
        assertEq(positions.getPositionLiquidity(firstMain),0);assertEq(positions.getPositionLiquidity(firstResidual),0);
        assertEq(manager.secondaryId(firstMain),0);assertEq(vault.sharesOf(id),shares);
        assertEq(vault.bucketTotalShares(bucket),shares);assertEq(nft.ownerOf(id),owner);assertFalse(_execution().executionActive());
    }
}
