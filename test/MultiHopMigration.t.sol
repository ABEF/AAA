// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
// Focused protocol tests use instrumented custody/transport mocks, not a live bridge.
import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZMigrationRegistry} from "../src/ZZZMigrationRegistry.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZBridgeRouter} from "../src/ZZZBridgeRouter.sol";
import {RouterProviderMock} from "./mocks/RouterMocks.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {Ids,Position,PositionStatus,PoolKey,PoolConfig,Route,BridgeMessage,MessageKind,AckPurpose,TransportPolicy} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockToken,MockPools,MockRoutes,MockFeed,BoundDummy,MockReadyRouter} from "./mocks/Mocks.sol";

contract HopVault {
    function migrationBudget() external view returns(address){return address(this);}
    function compositionEpoch(uint256) external pure returns(uint64){return 0;}
    IZZZAccess public immutable access;
    uint256 public immutable canonicalChainId;
    MockPools public immutable pools;
    mapping(uint256=>Position) private records;
    mapping(uint256=>uint256) private supplies;
    bytes32 private constant HOME_POOL = keccak256("canonical initial pool");
    uint256 public confirmations;
    constructor(address controller,uint256 home,MockPools registry){access=IZZZAccess(controller);canonicalChainId=home;pools=registry;}
    function set(uint256 id,Position memory p) external {records[id]=p;if(supplies[id]==0)supplies[id]=2000e18;}
    function setShares(uint256 id,uint256 amount) external {supplies[id]=amount;}
    function bucketTotalShares(uint256 id) external view returns(uint256){return supplies[id];}
    function homePoolId(uint256) external pure returns(bytes32){return HOME_POOL;}
    function group(uint256 id) external view returns(Position memory){return records[id];}
    function position(uint256 id) external view returns(Position memory){return records[id];}
    function releaseForMigration(uint256 id,bytes32,uint256) external returns(uint256,uint256){
        require(msg.sender==access.module(Ids.MIGRATION));Position storage p=records[id];require(p.status==PositionStatus.Active);
        PoolConfig memory c=pools.get(p.poolId);p.status=PositionStatus.Outbound;p.lpTokenId=0;
        require(IERC20(c.key.currency0).transfer(msg.sender,1000));require(IERC20(c.key.currency1).transfer(msg.sender,1000));
        return(1000,1000);
    }
    function confirmMigration(uint256 id,uint256 chain,address destination) external {
        require(msg.sender==access.module(Ids.MIGRATION));Position storage p=records[id];
        require(p.status==PositionStatus.Outbound||p.status==PositionStatus.Remote);
        p.status=PositionStatus.Remote;p.locationChain=chain;p.locationVault=destination;confirmations++;
    }
    function movePool(uint256 id,bytes32 pool,uint128,uint256) external {records[id].poolId=pool;}
}
contract HopNFT {
    mapping(uint256=>address) public owners;
    function set(uint256 id,address owner) external {owners[id]=owner;}
    function ownerOf(uint256 id) external view returns(address){require(owners[id]!=address(0),"missing canonical NFT");return owners[id];}
}
contract HopBoundPools is MockPools {
    IZZZAccess public immutable access;
    constructor(address controller){access=IZZZAccess(controller);}
}
contract HopBridge {
    MockRoutes public immutable routes;BridgeMessage private last;bool public fail;
    constructor(MockRoutes registry){routes=registry;}
    function setFail(bool value) external {fail=value;}
    function message() external view returns(BridgeMessage memory){return last;}
    function send(BridgeMessage calldata m) external payable returns(bytes32){
        require(!fail,"transport failed");(Route memory r,)=routes.get(m.routeId);
        require(IERC20(r.sourceToken0).transferFrom(msg.sender,address(this),m.amount0));
        require(IERC20(r.sourceToken1).transferFrom(msg.sender,address(this),m.amount1));
        last=m;return keccak256(abi.encode(m.migrationId,m.migrationEpoch));
    }
}
contract HopFees {
    function allocated(uint256,address) external pure returns(uint256,uint256){return(0,0);}
    function remoteSettled(uint256) external pure returns(bool){return true;}
}
contract MultiHopMigrationTest is Test {
    uint256 private constant HOME=1;uint256 private constant B=57073;uint256 private constant C=10;uint256 private ID;
    bytes32 private constant HOME_POOL=keccak256("canonical initial pool");
    address private constant BV=address(0xB001);address private constant BR=address(0xB002);
    address private constant CV=address(0xC001);address private constant CR=address(0xC002);
    address private constant BT0=address(0xB010);address private constant BT1=address(0xB011);
    address private constant CT0=address(0xC010);address private constant CT1=address(0xC011);
    address private receiver=address(0xF001);
    MockAccess private ac;MockToken private t0;MockToken private t1;MockPools private pools;MockRoutes private routes;
    HopVault private vault;HopNFT private nft;HopBridge private bridge;ZZZMigration private migration;bytes32 private poolId;
    function setUp() public {
        if (block.timestamp < 2) vm.warp(1000000);_fixture(HOME);}
    function _fixture(uint256 chain) private {
        vm.chainId(chain);vm.warp(1_000_000);ac=new MockAccess();t0=new MockToken(0);t1=new MockToken(0);
        pools=new MockPools();routes=new MockRoutes();vault=new HopVault(address(ac),HOME,pools);nft=new HopNFT();
        bridge=new HopBridge(routes);migration=new ZZZMigration(address(ac));
        ID=uint256(keccak256(abi.encode(HOME,chain==HOME?address(vault):address(0xA001),HOME_POOL)));
        ac.bind(Ids.VAULT,address(vault));ac.bind(Ids.NFT,address(nft));ac.bind(Ids.POOLS,address(pools));
        ac.bind(Ids.ROUTES,address(routes));ac.bind(Ids.BRIDGE,address(bridge));ac.bind(Ids.RECEIVER,receiver);
        ac.bind(Ids.MIGRATION,address(migration));ac.bind(Ids.FEES,address(new HopFees()));ac.bind(Ids.TRANSPORT,address(new MockReadyRouter()));ac.setKeeper(address(this),true);ac.seal();
        PoolConfig memory cfg;cfg.key=PoolKey(address(t0),address(t1),3000,60,address(0));poolId=keccak256(abi.encode(cfg.key));pools.set(poolId,cfg);
        t0.mint(address(vault),1000);t1.mint(address(vault),1000);nft.set(ID,address(0xA11CE));
        if(chain==HOME){Position memory p=_active(HOME,address(vault),receiver,address(t0),address(t1));vault.set(ID,p);}
    }
    function _active(uint256 home,address homeVault,address homeReceiver,address home0,address home1) private view returns(Position memory p){
        p.poolId=poolId;p.status=PositionStatus.Active;p.lpTokenId=1;p.depositUSD=2000e18;
        p.homeChain=home;p.homeVault=homeVault;p.homeReceiver=homeReceiver;p.homeToken0=home0;p.homeToken1=home1;
        p.locationChain=block.chainid;p.locationVault=address(vault);
    }
    function _route(uint256 from,address fromVault,address fromReceiver,address from0,address from1,
        uint256 to,address toVault,address toReceiver,address to0,address to1) private pure returns(Route memory r){
        r.sourceChain=from;r.sourceVault=fromVault;r.sourceReceiver=fromReceiver;r.sourceAdapter=address(0xAD01);
        r.destinationChain=to;r.destinationVault=toVault;r.destinationReceiver=toReceiver;r.destinationAdapter=address(0xAD02);
        r.sourceToken0=from0;r.sourceToken1=from1;r.destinationToken0=to0;r.destinationToken1=to1;
    }
    function _store(Route memory r) private returns(bytes32 id){id=keccak256(abi.encode(r));routes.set(id,r);}
    function _execute(bytes32 routeId) private returns(BridgeMessage memory m){
        bytes32 id=migration.propose(ID,routeId);
        assertEq(migration.MIGRATION_DELAY(),0);
        migration.execute(id,block.timestamp+100);return bridge.message();
    }
    function _first() private returns(BridgeMessage memory){
        return _execute(_store(_route(HOME,address(vault),receiver,address(t0),address(t1),B,BV,BR,BT0,BT1)));
    }
    function _ack(BridgeMessage memory m,AckPurpose purpose) private pure returns(BridgeMessage memory){
        m=abi.decode(abi.encode(m),(BridgeMessage));
        m.kind=MessageKind.Acknowledgement;m.routeId=keccak256("ACK delivery route");m.nonce=1;
        m.amount0=0;m.amount1=0;m.acknowledgement=purpose;return m;
    }
    function _confirm(BridgeMessage memory m,uint256 chain,address destination) private {
        vm.prank(receiver);migration.confirm(m,chain,destination);
    }
    function _second(BridgeMessage memory first) private returns(BridgeMessage memory m){
        m=_ack(first,AckPurpose.CanonicalLocation);m.migrationId=keccak256("second hop");m.migrationEpoch=2;
        m.previousChain=B;m.previousVault=BV;m.previousReceiver=BR;
        m.principalRouteId=_store(_route(B,BV,BR,BT0,BT1,C,CV,CR,CT0,CT1));
    }
    function _returning(BridgeMessage memory first) private returns(BridgeMessage memory m){
        m=abi.decode(abi.encode(first),(BridgeMessage));m.migrationEpoch=3;m.migrationId=keccak256("return home");
        m.previousChain=C;m.previousVault=CV;m.previousReceiver=CR;
        m.principalRouteId=_store(_route(C,CV,CR,CT0,CT1,HOME,address(vault),receiver,address(t0),address(t1)));
        m.routeId=m.principalRouteId;m.kind=MessageKind.Principal;
    }
    function _import(BridgeMessage memory m) private {vm.prank(receiver);migration.registerImport(m);}
    function _assertLocation(uint64 epoch,uint256 chain,address location) private view {
        (uint64 actualEpoch,uint256 actualChain,address actualVault)=migration.locations(ID);
        assertEq(actualEpoch,epoch);assertEq(actualChain,chain);assertEq(actualVault,location);
    }
    function testSourceCompletionRecordsCanonicalLocationAndClearsPlan() public {
        BridgeMessage memory m=_first();assertEq(m.version,3);assertEq(m.migrationEpoch,1);
        assertEq(m.previousVault,address(vault));assertEq(m.canonicalToken0,address(t0));
        _confirm(_ack(m,AckPurpose.SourceCompletion),B,BV);
        _assertLocation(1,B,BV);assertEq(migration.activePlan(ID),bytes32(0));
        assertEq(uint256(vault.position(ID).status),uint256(PositionStatus.Remote));
        assertTrue(migration.authorizedReward(ID,B,BV,BT0,address(t0)));assertTrue(migration.authorizedReward(ID,B,BV,BT1,address(t1)));
    }
    function testRemoteToRemoteAckAdvancesHomeAndKeepsHistoricalRewardPaths() public {
        BridgeMessage memory first=_first();_confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);
        _confirm(_second(first),C,CV);_assertLocation(2,C,CV);
        assertTrue(migration.authorizedReward(ID,B,BV,BT0,address(t0)));assertTrue(migration.authorizedReward(ID,C,CV,CT1,address(t1)));
        assertEq(nft.ownerOf(ID),address(0xA11CE));assertEq(vault.position(ID).depositUSD,2000e18);
    }
    function testReorderedLocationAckCanBeRetriedAfterEarlierAck() public {
        BridgeMessage memory first=_first();BridgeMessage memory second=_second(first);
        vm.expectRevert();_confirm(second,C,CV);assertEq(migration.locationSnapshots(ID,2),bytes32(0));
        _confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);_confirm(second,C,CV);_assertLocation(2,C,CV);
    }
    function testLateSourceCompletionCannotRegressNewerCanonicalLocation() public {
        BridgeMessage memory first=_first();_confirm(_ack(first,AckPurpose.CanonicalLocation),B,BV);
        _confirm(_second(first),C,CV);uint256 count=vault.confirmations();
        _confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);_assertLocation(2,C,CV);
        assertEq(vault.confirmations(),count);assertEq(migration.activePlan(ID),bytes32(0));
    }
    function testExactOldAckIsIdempotentAndAlteredOldAckRejected() public {
        BridgeMessage memory first=_first();BridgeMessage memory ack=_ack(first,AckPurpose.SourceCompletion);
        _confirm(ack,B,BV);_confirm(_second(first),C,CV);_confirm(ack,B,BV);_assertLocation(2,C,CV);
        ack.canonicalToken0=address(0xBAD);vm.expectRevert();_confirm(ack,B,BV);_assertLocation(2,C,CV);
    }
    function testForgedPreviousLocationAndCanonicalMappingRejected() public {
        BridgeMessage memory first=_first();_confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);
        BridgeMessage memory second=_second(first);second.previousVault=address(0xBAD);vm.expectRevert();_confirm(second,C,CV);
        second=_second(first);second.canonicalToken0=address(0xBAD);vm.expectRevert();_confirm(second,C,CV);_assertLocation(1,B,BV);
    }
    function testCanonicalReturnThenAnotherMigrationPreservesIdentity() public {
        BridgeMessage memory first=_first();_confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);_confirm(_second(first),C,CV);
        _import(_returning(first));_assertLocation(3,HOME,address(vault));assertEq(migration.custodyEpoch(ID),3);
        assertTrue(migration.authorizedReward(ID,B,BV,BT0,address(t0)));assertTrue(migration.authorizedReward(ID,C,CV,CT0,address(t0)));
        vault.set(ID,_active(HOME,address(vault),receiver,address(t0),address(t1)));t0.mint(address(vault),1000);t1.mint(address(vault),1000);
        BridgeMessage memory next=_first();assertEq(next.migrationEpoch,4);_confirm(_ack(next,AckPurpose.SourceCompletion),B,BV);
        _assertLocation(4,B,BV);assertEq(nft.ownerOf(ID),address(0xA11CE));assertEq(vault.position(ID).depositUSD,2000e18);
    }
    function testCanonicalReturnRequiresExistingSharesAndCorrectAssets() public {
        BridgeMessage memory first=_first();_confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);_confirm(_second(first),C,CV);
        BridgeMessage memory returning=_returning(first);returning.canonicalToken0=address(t1);vm.expectRevert();_import(returning);
        returning=_returning(first);vault.setShares(ID,0);vm.expectRevert();_import(returning);_assertLocation(2,C,CV);
    }
    function testSourceSnapshotChangedAfterScheduleCannotExecute() public {
        bytes32 routeId=_store(_route(HOME,address(vault),receiver,address(t0),address(t1),B,BV,BR,BT0,BT1));
        bytes32 id=migration.propose(ID,routeId);Position memory p=vault.position(ID);p.depositUSD++;vault.set(ID,p);
        vm.warp(block.timestamp+2 days);vm.expectRevert();migration.execute(id,block.timestamp+100);
        assertEq(migration.custodyEpoch(ID),0);assertEq(t0.balanceOf(address(vault)),1000);
    }
    function testTransportFailureRestoresPrincipalEpochAndScheduledPlan() public {
        bytes32 routeId=_store(_route(HOME,address(vault),receiver,address(t0),address(t1),B,BV,BR,BT0,BT1));
        bytes32 id=migration.propose(ID,routeId);
        assertEq(migration.MIGRATION_DELAY(),0);bridge.setFail(true);
        vm.expectRevert();migration.execute(id,block.timestamp+100);
        assertEq(migration.custodyEpoch(ID),0);assertEq(uint256(vault.position(ID).status),uint256(PositionStatus.Active));
        assertEq(t0.balanceOf(address(vault)),1000);assertEq(t0.balanceOf(address(migration)),0);
        bridge.setFail(false);migration.execute(id,block.timestamp+100);assertEq(migration.custodyEpoch(ID),1);
    }
    function testUnauthorizedReceiverCannotUpdateCustody() public {
        BridgeMessage memory first=_first();vm.expectRevert();migration.confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);
        vm.expectRevert();migration.registerImport(first);assertEq(migration.locationSnapshots(ID,1),bytes32(0));
    }
    function testSatelliteCanMigrateAndRevisitAfterSeveralAbsentEpochs() public {
        _fixture(B);address homeVault=address(0xA001);address homeReceiver=address(0xA002);address home0=address(0xA010);address home1=address(0xA011);
        BridgeMessage memory incoming;incoming.version=3;incoming.kind=MessageKind.Principal;incoming.bucketId=ID;
        incoming.homePoolId=HOME_POOL;incoming.totalShares=2000e18;
        incoming.homeChain=HOME;incoming.homeVault=homeVault;incoming.homeReceiver=homeReceiver;incoming.depositUSD=2000e18;
        incoming.previousChain=HOME;incoming.previousVault=homeVault;incoming.previousReceiver=homeReceiver;
        incoming.migrationEpoch=1;incoming.migrationId=keccak256("initial satellite import");incoming.canonicalToken0=home0;incoming.canonicalToken1=home1;
        incoming.principalRouteId=_store(_route(HOME,homeVault,homeReceiver,home0,home1,B,address(vault),receiver,address(t0),address(t1)));
        incoming.routeId=incoming.principalRouteId;_import(incoming);
        vault.set(ID,_active(HOME,homeVault,homeReceiver,home0,home1));
        BridgeMessage memory departure=_execute(_store(_route(B,address(vault),receiver,address(t0),address(t1),C,CV,CR,CT0,CT1)));
        assertEq(departure.migrationEpoch,2);_confirm(_ack(departure,AckPurpose.SourceCompletion),C,CV);
        incoming.previousChain=C;incoming.previousVault=CV;incoming.previousReceiver=CR;incoming.migrationEpoch=5;
        incoming.migrationId=keccak256("later satellite revisit");
        incoming.principalRouteId=_store(_route(C,CV,CR,CT0,CT1,B,address(vault),receiver,address(t0),address(t1)));
        incoming.routeId=incoming.principalRouteId;_import(incoming);assertEq(migration.custodyEpoch(ID),5);
        vm.expectRevert();_import(incoming);assertEq(migration.custodyEpoch(ID),5);
        _confirm(_ack(departure,AckPurpose.SourceCompletion),C,CV);assertEq(migration.custodyEpoch(ID),5);
    }
    function testFrozenShareSupplyCannotChangeBetweenProposalAndExecution() public {
        bytes32 routeId=_store(_route(HOME,address(vault),receiver,address(t0),address(t1),B,BV,BR,BT0,BT1));
        bytes32 plan=migration.propose(ID,routeId);
        vault.setShares(ID,2001e18);
        vm.warp(block.timestamp+2 days);
        vm.expectRevert();migration.execute(plan,block.timestamp+100);
        assertEq(migration.custodyEpoch(ID),0);
        assertEq(uint256(vault.position(ID).status),uint256(PositionStatus.Active));
        assertEq(t0.balanceOf(address(vault)),1000);
    }
    function testPooledMessageRejectsOldNFTVersionAndAlteredBucketIdentity() public {
        BridgeMessage memory first=_first();BridgeMessage memory ack=_ack(first,AckPurpose.SourceCompletion);
        ack.version=2;vm.expectRevert();_confirm(ack,B,BV);
        ack=_ack(first,AckPurpose.SourceCompletion);ack.bucketId++;
        vm.expectRevert();_confirm(ack,B,BV);
        ack=_ack(first,AckPurpose.SourceCompletion);ack.totalShares++;
        vm.expectRevert();_confirm(ack,B,BV);
        _assertLocation(0,0,address(0));
        _confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);_assertLocation(1,B,BV);
    }
    function testAcknowledgementCannotChangeFrozenRemoteFeeTotals() public {
        BridgeMessage memory first=_first();BridgeMessage memory ack=_ack(first,AckPurpose.SourceCompletion);
        ack.allocatedIndividual0=1;vm.expectRevert();_confirm(ack,B,BV);
        ack=_ack(first,AckPurpose.SourceCompletion);ack.allocatedCollective1=1;
        vm.expectRevert();_confirm(ack,B,BV);
        _confirm(_ack(first,AckPurpose.SourceCompletion),B,BV);_assertLocation(1,B,BV);
    }

}

contract MultiHopMigrationRegistryTest is Test {
    ZZZAccessController private ac;ZZZMigrationRegistry private registry;HopVault private vault;MockToken private token0;MockToken private token1;
    HopBoundPools private pools;bytes32 private localPool;
    ZZZBridgeRouter private router;RouterProviderMock private provider;bytes32 private lastPolicy;
    function setUp() public {
        if (block.timestamp < 2) vm.warp(1000000);
        vm.chainId(1);vm.warp(1_000_000);address[] memory actors=new address[](1);actors[0]=address(this);
        ac=new ZZZAccessController(0,actors,actors,address(this),address(this));pools=new HopBoundPools(address(ac));
        vault=new HopVault(address(ac),block.chainid,pools);registry=new ZZZMigrationRegistry(address(ac));
        router=new ZZZBridgeRouter(address(ac));provider=new RouterProviderMock(address(router),keccak256("test channel"));
        token0=new MockToken(6);token1=new MockToken(18);ZZZOracle oracle=new ZZZOracle(address(ac),address(0));
        PoolConfig memory c;c.key=PoolKey(address(token0),address(token1),3000,60,address(0));c.operationsEnabled=true;
        localPool=keccak256(abi.encode(c.key));pools.set(localPool,c);
        MockFeed feed=new MockFeed(8,1e8);oracle.setFeed(address(token0),address(feed),3600);oracle.setFeed(address(token1),address(feed),3600);
        bytes32[16] memory ids=[Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,Ids.STRATEGY,
            Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.BRIDGE,Ids.RECEIVER,Ids.ORACLE,Ids.POOLS,Ids.ROUTES,Ids.TRANSPORT];
        for(uint256 i;i<ids.length;i++){
            address implementation=ids[i]==Ids.VAULT?address(vault):ids[i]==Ids.ROUTES?address(registry):
                ids[i]==Ids.TRANSPORT?address(router):ids[i]==Ids.ORACLE?address(oracle):ids[i]==Ids.POOLS?address(pools):address(new BoundDummy(address(ac)));ac.bind(ids[i],implementation);
        }
        CanonicalFixture.bind(address(ac));
        ac.seal();
    }
    function _edge() private pure returns(Route memory r){
        r.sourceChain=2;r.destinationChain=3;r.sourceAdapter=address(0x101);r.sourceVault=address(0x102);r.sourceReceiver=address(0x103);
        r.destinationAdapter=address(0x201);r.destinationVault=address(0x202);r.destinationReceiver=address(0x203);
        r.sourceToken0=address(0x301);r.sourceToken1=address(0x302);r.destinationToken0=address(0x401);r.destinationToken1=address(0x402);
        r.token0Decimals=6;r.token1Decimals=18;
    }
    function _schedule(Route memory r,bytes32 salt) private returns(bytes memory data){
        TransportPolicy memory p;
        p.providerId=keccak256("test provider");p.channelId=keccak256("test channel");p.reviewHash=keccak256("test review");
        p.sourceChain=r.sourceChain;p.destinationChain=r.destinationChain;
        p.sourceRouter=r.sourceChain==block.chainid?address(router):address(0x501);
        p.destinationRouter=r.destinationChain==block.chainid?address(router):address(0x502);
        p.sourceProvider=r.sourceChain==block.chainid?address(provider):address(0x601);
        p.destinationProvider=r.destinationChain==block.chainid?address(provider):address(0x602);
        p.sourceCodeHash=r.sourceChain==block.chainid?address(provider).codehash:keccak256("remote code");
        p.destinationCodeHash=r.destinationChain==block.chainid?address(provider).codehash:keccak256("remote code");
        p.sourceConfigurationHash=keccak256("test channel");p.destinationConfigurationHash=keccak256("test channel");
        lastPolicy=keccak256(abi.encode(p));
        if(!router.policyExists(lastPolicy)){
            bytes memory policyData=abi.encodeCall(router.registerPolicy,(p));bytes32 policySalt=keccak256(abi.encode(salt,"policy"));
            ac.schedule(address(router),0,policyData,bytes32(0),policySalt,0);vm.warp(block.timestamp+1 days);
            ac.execute(address(router),0,policyData,bytes32(0),policySalt);
        }
        data=abi.encodeCall(ZZZMigrationRegistry.add,(r,lastPolicy));ac.schedule(address(registry),0,data,bytes32(0),salt,0);
    }
    function testFutureUnknownGraphEdgeRequiresImmediateGovernance() public {
        Route memory r=_edge();vm.expectRevert();registry.add(r,bytes32(0));
        bytes32 salt=keccak256("future edge");bytes memory data=_schedule(r,salt);
        ac.execute(address(registry),0,data,bytes32(0),salt);
        bytes32 id=keccak256(abi.encode(r,lastPolicy));assertTrue(registry.exists(id));assertTrue(registry.enabled(id));
        (Route memory stored,)=registry.get(id);assertEq(stored.destinationChain,3);assertEq(stored.destinationVault,r.destinationVault);
    }
    function testGraphEdgesRemainAppendOnlyAfterSeal() public {
        Route memory r=_edge();bytes32 salt=keccak256("first");bytes memory data=_schedule(r,salt);
        vm.warp(block.timestamp+1 days);ac.execute(address(registry),0,data,bytes32(0),salt);
        salt=keccak256("duplicate");data=_schedule(r,salt);vm.warp(block.timestamp+1 days);
        vm.expectRevert();ac.execute(address(registry),0,data,bytes32(0),salt);
        (Route memory stored,)=registry.get(keccak256(abi.encode(r,lastPolicy)));assertEq(stored.destinationVault,r.destinationVault);
    }
    function testLocalEndpointChecksStillApplyToPostSealRoutes() public {
        Route memory r=_edge();r.sourceChain=block.chainid;r.sourceVault=address(0xBAD);
        bytes32 salt=keccak256("bad local endpoint");bytes memory data=_schedule(r,salt);vm.warp(block.timestamp+1 days);
        vm.expectRevert();ac.execute(address(registry),0,data,bytes32(0),salt);assertFalse(registry.exists(keccak256(abi.encode(r,lastPolicy))));
    }
    function testLocalDecimalsChecksStillApplyToPostSealRoutes() public {
        Route memory r=_edge();r.sourceChain=block.chainid;r.sourceVault=address(vault);
        r.sourceAdapter=ac.module(Ids.BRIDGE);r.sourceReceiver=ac.module(Ids.RECEIVER);
        r.sourceToken0=address(token0);r.sourceToken1=address(token1);r.token0Decimals=18;
        bytes32 salt=keccak256("bad local decimals");bytes memory data=_schedule(r,salt);vm.warp(block.timestamp+1 days);
        vm.expectRevert();ac.execute(address(registry),0,data,bytes32(0),salt);assertFalse(registry.exists(keccak256(abi.encode(r,lastPolicy))));
    }
    function _incoming() private view returns(Route memory r){
        r=_edge();r.destinationChain=block.chainid;r.destinationVault=address(vault);
        r.destinationAdapter=ac.module(Ids.BRIDGE);r.destinationReceiver=ac.module(Ids.RECEIVER);
        r.destinationToken0=address(token0);r.destinationToken1=address(token1);r.destinationPool=localPool;
    }
    function testLocalDestinationRequiresExistingConfiguredPool() public {
        Route memory r=_incoming();r.destinationPool=keccak256("unknown local pool");
        bytes32 salt=keccak256("unknown pool");bytes memory data=_schedule(r,salt);vm.warp(block.timestamp+1 days);
        vm.expectRevert();ac.execute(address(registry),0,data,bytes32(0),salt);assertFalse(registry.exists(keccak256(abi.encode(r,lastPolicy))));
    }
    function testLocalDestinationRejectsWrongPoolAssetPair() public {
        Route memory r=_incoming();PoolConfig memory c=pools.get(localPool);c.key.currency1=address(0xBAD);pools.set(localPool,c);
        bytes32 salt=keccak256("wrong pool assets");bytes memory data=_schedule(r,salt);vm.warp(block.timestamp+1 days);
        vm.expectRevert();ac.execute(address(registry),0,data,bytes32(0),salt);assertFalse(registry.exists(keccak256(abi.encode(r,lastPolicy))));
    }
    function testLocalDestinationRequiresEnabledPoolOperations() public {
        Route memory r=_incoming();PoolConfig memory c=pools.get(localPool);c.operationsEnabled=false;pools.set(localPool,c);
        bytes32 salt=keccak256("disabled local pool");bytes memory data=_schedule(r,salt);vm.warp(block.timestamp+1 days);
        vm.expectRevert();ac.execute(address(registry),0,data,bytes32(0),salt);assertFalse(registry.exists(keccak256(abi.encode(r,lastPolicy))));
    }
    function testLocalDestinationAcceptsConfiguredPairInEitherOrder() public {
        Route memory r=_incoming();PoolConfig memory c=pools.get(localPool);
        c.key.currency0=address(token1);c.key.currency1=address(token0);pools.set(localPool,c);
        bytes32 salt=keccak256("configured reversed pool");bytes memory data=_schedule(r,salt);vm.warp(block.timestamp+1 days);
        ac.execute(address(registry),0,data,bytes32(0),salt);assertTrue(registry.exists(keccak256(abi.encode(r,lastPolicy))));
    }
}
