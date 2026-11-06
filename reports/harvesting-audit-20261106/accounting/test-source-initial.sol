// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import "./OptionalPortfolioCore.t.sol";
import "./RewardsAndFees.t.sol";

contract HarvestAuditActualV4Test is Test {
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
    uint256 private auditDonation0; uint256 private auditDonation1;
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
        else if(mode==5)delta=core.donate(key,auditDonation0,auditDonation1,"");
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

    bytes32 private constant COLLECTED=keccak256("FeesCollected(uint256,uint256,uint256)");
    event AuditFragmentation(uint256 donationEach,uint256 repeats,uint256 mainL,uint256 auxL,uint256 sparseETH,uint256 sparseZZZ,uint256 fragmentedETH,uint256 fragmentedZZZ);
    function _donateRaw(uint256 x,uint256 y)private{auditDonation0=x;auditDonation1=y;core.unlock(abi.encode(uint8(5),Q96));}
    function _receipts(Vm.Log[] memory logs,uint256 bucket)private view returns(uint256 x,uint256 y){
        for(uint256 i;i<logs.length;++i)if(logs[i].emitter==address(vault)&&logs[i].topics[0]==COLLECTED){
            assertEq(uint256(logs[i].topics[1]),bucket);(uint256 a,uint256 b)=abi.decode(logs[i].data,(uint256,uint256));x+=a;y+=b;
        }
    }
    function _collect(uint256 bucket)private returns(uint256 x,uint256 y){
        vm.recordLogs();vm.prank(address(0xFEE));vault.collectFees(bucket,block.timestamp+100);
        return _receipts(vm.getRecordedLogs(),bucket);
    }
    function _backed(uint256 bucket)private view{
        assertEq(address(rewards).balance,rewards.liabilities(address(0))+rewards.orphaned(address(0)));
        assertEq(token.balanceOf(address(rewards)),rewards.liabilities(address(token))+rewards.orphaned(address(token)));
        assertEq(address(fees).balance,fees.accounted(address(0)));assertEq(token.balanceOf(address(fees)),fees.accounted(address(token)));
        assertEq(fees.accounted(address(0)),fees.compoundBalance(bucket,address(0))+fees.buybackBalance(address(0))+fees.dust(bucket,address(0)));
        assertEq(fees.accounted(address(token)),fees.compoundBalance(bucket,address(token))+fees.buybackBalance(address(token))+fees.dust(bucket,address(token)));
    }
    function _physicalHash(uint256 main,uint256 aux)private view returns(bytes32){
        (int24 l,int24 u)=manager.ticks(main);(int24 al,int24 au)=manager.ticks(aux);
        return keccak256(abi.encode(main,aux,l,u,al,au,positions.getPositionLiquidity(main),positions.getPositionLiquidity(aux)));
    }
    function _checkpointHash(uint256 main,uint256 aux)private view returns(bytes32){
        (int24 l,int24 u)=manager.ticks(main);(int24 al,int24 au)=manager.ticks(aux);
        (uint128 ml,uint256 m0,uint256 m1)=state.getPositionInfo(PoolId.wrap(pool),address(positions),l,u,bytes32(main));
        (uint128 ax,uint256 a0,uint256 a1)=state.getPositionInfo(PoolId.wrap(pool),address(positions),al,au,bytes32(aux));
        return keccak256(abi.encode(ml,m0,m1,ax,a0,a1,address(vault).balance,token.balanceOf(address(vault)),fees.accounted(address(0)),fees.accounted(address(token)),rewards.liabilities(address(0)),rewards.liabilities(address(token))));
    }
    function testHarvestAuditSparseVersusFragmentedActualBothLegReceipts()public{
        (,uint256 bucket,uint256 main,uint256 aux)=_hybrid();_move(uint160(uint256(Q96)*88/100));_collect(bucket);
        uint128 ml=positions.getPositionLiquidity(main);uint128 al=positions.getPositionLiquidity(aux);
        uint256 total=state.getLiquidity(PoolId.wrap(pool));
        // Select a donation giving the main approximately half a raw unit per
        // checkpoint. Donations fund actual core fee growth, not trading volume.
        uint256 each=total/(uint256(ml)*2);if(each==0)each=1;
        uint256 snap=vm.snapshotState();uint256 n=64;bytes32 physical=_physicalHash(main,aux);
        for(uint256 i;i<n;++i)_donateRaw(each,each);
        (uint256 sparse0,uint256 sparse1)=_collect(bucket);_backed(bucket);assertEq(_physicalHash(main,aux),physical);
        assertTrue(vm.revertToState(snap));uint256 fragmented0;uint256 fragmented1;
        for(uint256 i;i<n;++i){_donateRaw(each,each);(uint256 x,uint256 y)=_collect(bucket);fragmented0+=x;fragmented1+=y;}
        _backed(bucket);assertEq(_physicalHash(main,aux),physical);
        assertGt(sparse0,0);assertGt(sparse1,0);assertGt(sparse0,fragmented0);assertGt(sparse1,fragmented1);
        // Each of two real positions loses less than one raw unit per repeated
        // collection relative to the identical single-checkpoint fee growth.
        assertLt(sparse0-fragmented0,2*n);assertLt(sparse1-fragmented1,2*n);
        emit AuditFragmentation(each,n,ml,al,sparse0,sparse1,fragmented0,fragmented1);
    }
    function testHarvestAuditBothLegEntryCheckpointsAndSecondLegFailureRollback()public{
        (uint256 alice,uint256 bucket,uint256 main,uint256 aux)=_hybrid();_move(uint160(uint256(Q96)*88/100));_collect(bucket);
        uint256 bob=_mint(BOB);_donateRaw(20 ether+3,30 ether+7);
        // Revert the exact second position's genuine zero-liquidity decrease,
        // after the first leg would already have transferred real fee receipts.
        bytes[] memory p=new bytes[](2);p[0]=abi.encode(aux,uint256(0),uint128(0),uint128(0),bytes(""));
        p[1]=abi.encode(address(0),address(token),manager.positionOperator());
        bytes memory callData=abi.encodeWithSelector(positions.modifyLiquidities.selector,abi.encode(hex"0111",p),block.timestamp+100);
        bytes32 beforeFault=_checkpointHash(main,aux);uint256 liabBefore=rewards.liabilities(address(0));
        vm.mockCallRevert(address(positions),callData,abi.encodeWithSignature("Error(string)","TEST ONLY second-leg collection failure"));
        vm.expectRevert();vault.collectFees(bucket,block.timestamp+100);vm.clearMockedCalls();
        assertEq(_checkpointHash(main,aux),beforeFault);assertEq(rewards.liabilities(address(0)),liabBefore);
        uint256[2] memory liabilities=[rewards.liabilities(address(0)),rewards.liabilities(address(token))];
        uint256[2] memory dust=[fees.dust(bucket,address(0)),fees.dust(bucket,address(token))];
        uint256[2] memory burns=[fees.buybackBalance(address(0)),fees.buybackBalance(address(token))];
        uint128 residualL=positions.getPositionLiquidity(aux);vm.recordLogs();_contribute(BOB,bob,1000 ether,false);
        (uint256 x,uint256 y)=_receipts(vm.getRecordedLogs(),bucket);assertGt(x,0);assertGt(y,0);
        assertEq(rewards.claimable(bob,address(0)),0);assertEq(rewards.claimable(bob,address(token)),0);
        for(uint256 j;j<2;++j){address asset=j==0?address(0):address(token);uint256 received=j==0?x:y;uint256 units=received/20;
            assertEq(rewards.liabilities(asset)-liabilities[j],dust[j]+received-2*units);
            assertEq(fees.buybackBalance(asset)-burns[j],units);assertEq(fees.compoundBalance(bucket,asset),0);assertEq(fees.dust(bucket,asset),0);
        }
        assertEq(vault.group(bucket).lpTokenId,main);assertEq(manager.secondaryId(main),aux);assertEq(positions.getPositionLiquidity(aux),residualL);_backed(bucket);
        uint256 oldShares=vault.sharesOf(bob);uint256 oldTotal=vault.bucketTotalShares(bucket);
        uint256 aliceBefore=rewards.claimable(alice,address(0));uint256 bobBefore=rewards.claimable(bob,address(0));
        _donateRaw(25 ether,35 ether);vm.recordLogs();_contribute(BOB,bob,100 ether,true);
        (x,y)=_receipts(vm.getRecordedLogs(),bucket);assertGt(x,0);assertGt(y,0);uint256 units0=x/20;
        uint256 expectedBob=Math.mulDiv(units0*16+(x%20),oldShares,oldTotal)+units0;
        uint256 actualBob=rewards.claimable(bob,address(0))-bobBefore;
        assertGe(actualBob,expectedBob);assertLe(actualBob,expectedBob+2);
        assertGt(rewards.claimable(alice,address(0)),aliceBefore);assertGt(vault.sharesOf(bob),oldShares);
        assertEq(manager.secondaryId(main),aux);assertEq(positions.getPositionLiquidity(aux),residualL);_backed(bucket);
        uint256 owed=rewards.claimable(alice,address(0));uint256 bobBalance=BOB.balance;
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,alice);vm.prank(BOB);assertEq(rewards.claim(alice,address(0)),owed);
        assertEq(BOB.balance-bobBalance,owed);vm.prank(BOB);assertEq(rewards.claim(alice,address(0)),0);_backed(bucket);
    }
}

// Focused ledger isolation: actual Rewards/Fees contracts, explicit mock Vault
// share book. This proves the finite index limitation, not v4 or exit behavior.
contract HarvestAuditFinalIndexTest is RewardsAndFeesTest {
    event AuditFinalUnit(uint256 allocated,uint256 claimed,uint256 reserved,uint256 ownerFraction);
    function testHarvestAuditFiniteFinalIndexUnitRemainsBackedWithoutFutureReceipts()public{
        vault.join(1,BUCKET,1);assertEq(vault.bucketTotalShares(BUCKET),101);
        _allocate(20);assertEq(fees.compoundBalance(BUCKET,address(token)),1);assertEq(fees.buybackBalance(address(token)),1);
        assertEq(rewards.liabilities(address(token)),18);assertEq(rewards.claimable(1,address(token)),17);
        vm.prank(alice);assertEq(rewards.claim(1,address(token)),17);
        assertEq(token.balanceOf(address(rewards)),1);assertEq(rewards.liabilities(address(token)),1);
        assertEq(rewards.claimable(1,address(token)),0);assertGt(rewards.ownerFraction(1,address(token)),0);
        vm.prank(alice);assertEq(rewards.claim(1,address(token)),0);
        emit AuditFinalUnit(18,17,1,rewards.ownerFraction(1,address(token)));
    }
}
