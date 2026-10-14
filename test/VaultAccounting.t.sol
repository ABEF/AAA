// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
// Integration of real vault/rewards/NFT/Power contracts, with a FAKE liquidity venue.
import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZPower} from "../src/ZZZPower.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids,PoolKey,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockToken,MockPools,MockFeed} from "./mocks/Mocks.sol";
contract VaultPolicyMock {
    bool public need=true;
    function setNeed(bool v) external {need=v;}
    function needsRebalance(uint256) external view returns(bool){return need;}
    function target(bytes32) external pure returns(int24,int24,uint160){return(-600,600,uint160(1<<96));}
    function validatePrice(bytes32) external pure returns(uint160){return uint160(1<<96);}
    function compoundPlan(uint256,uint256,uint256) external pure returns(bool,uint256,uint256){return(false,0,0);}
    function swapPlan(bytes32,uint256,uint256) external pure returns(bool,uint256,uint256){return(false,0,0);}
}
contract VaultLiquidityMock is ERC721 {
    MockToken public t0;MockToken public t1;uint256 public next=1;bool public failMint;uint256 public spendBps=9900;
    uint256 public fee0;uint256 public fee1;
    mapping(uint256=>uint256) public a0;mapping(uint256=>uint256) public a1;
    constructor(address x,address y)ERC721("Mock venue","MV"){t0=MockToken(x);t1=MockToken(y);}
    function positionManager() external view returns(address){return address(this);}
    function setFees(uint256 x,uint256 y) external {fee0=x;fee1=y;}
    function setSpendBps(uint256 x) external {spendBps=x;}
    function amounts(uint256 id) external view returns(uint256,uint256){return(a0[id],a1[id]);}
    function setFail(bool x) external {failMint=x;}
    function mint(bytes32,int24,int24,uint256 x,uint256 y,uint128,uint256)external returns(uint256 id,uint256 s0,uint256 s1){
        require(!failMint);id=next++;_mint(msg.sender,id);(s0,s1)=_fund(id,x,y);
    }
    function increase(bytes32,uint256 id,uint256 x,uint256 y,uint128,uint256) external returns(uint256,uint256){return _fund(id,x,y);}
    function _fund(uint256 id,uint256 x,uint256 y) private returns(uint256 s0,uint256 s1){
        s0=x*spendBps/10000;s1=y*spendBps/10000;require(t0.transferFrom(msg.sender,address(this),s0));require(t1.transferFrom(msg.sender,address(this),s1));
        a0[id]+=s0;a1[id]+=s1;
    }
    function collect(bytes32,uint256,uint256) external {uint256 x=fee0;uint256 y=fee1;fee0=0;fee1=0;t0.mint(msg.sender,x);t1.mint(msg.sender,y);}
    function close(bytes32,uint256 id,uint256) external {uint256 x=a0[id];uint256 y=a1[id];delete a0[id];delete a1[id];_burn(id);require(t0.transfer(msg.sender,x));require(t1.transfer(msg.sender,y));}
}
contract VaultAccountingTest is Test {
    MockAccess ac;MockToken t0;MockToken t1;MockPools pools;VaultPolicyMock policy;VaultLiquidityMock venue;
    ZZZVault vault;ZZZNFT nft;ZZZPower power;ZZZRewards rewards;ZZZFeeController fees;ZZZCompounder compounder;ZZZOracle oracle;
    bytes32 poolId;address alice=address(0xA11CE);address bob=address(0xB0B);
    function setUp() public {
        vm.warp(1_000_000);ac=new MockAccess();t0=new MockToken(18);t1=new MockToken(18);pools=new MockPools();policy=new VaultPolicyMock();
        venue=new VaultLiquidityMock(address(t0),address(t1));vault=new ZZZVault(address(ac),block.chainid);nft=new ZZZNFT(address(ac),"");
        power=new ZZZPower(address(ac));rewards=new ZZZRewards(address(ac));fees=new ZZZFeeController(address(ac));
        compounder=new ZZZCompounder(address(ac));oracle=new ZZZOracle(address(ac),address(0));
        MockFeed feed=new MockFeed(8,1e8);oracle.setFeed(address(t0),address(feed),3600);oracle.setFeed(address(t1),address(feed),3600);
        ac.bind(Ids.VAULT,address(vault));ac.bind(Ids.NFT,address(nft));ac.bind(Ids.POWER,address(power));ac.bind(Ids.REWARDS,address(rewards));
        ac.bind(Ids.FEES,address(fees));ac.bind(Ids.COMPOUNDER,address(compounder));ac.bind(Ids.LIQUIDITY,address(venue));
        ac.bind(Ids.STRATEGY,address(policy));ac.bind(Ids.POOLS,address(pools));ac.bind(Ids.ORACLE,address(oracle));
        ac.bind(Ids.MIGRATION,address(this));ac.bind(Ids.RECEIVER,address(0x987));ac.setKeeper(address(this),true);
        rewards.addAsset(address(t0));rewards.addAsset(address(t1));
        PoolConfig memory c;c.key=PoolKey(address(t0),address(t1),3000,60,address(0));c.operationsEnabled=true;c.depositsEnabled=true;
        c.minDepositUSD=1;c.maxPositionUSD=1e30;c.maxSlippageBps=100;poolId=keccak256(abi.encode(c.key));pools.set(poolId,c);ac.seal();
        t0.mint(alice,100000);t1.mint(alice,100000);vm.startPrank(alice);t0.approve(address(vault),type(uint256).max);t1.approve(address(vault),type(uint256).max);vm.stopPrank();
    }
    function deposit() private returns(uint256 id){vm.prank(alice);id=vault.deposit(poolId,1000,1000,1,block.timestamp+100);}
    function testDepositLeavesExactAttributedIdle() public {
        uint256 id=deposit();Position memory p=vault.position(id);assertEq(nft.ownerOf(id),alice);assertEq(venue.ownerOf(p.lpTokenId),address(vault));
        assertEq(p.idle0,10);assertEq(vault.totalIdle(address(t0)),10);assertEq(venue.a0(p.lpTokenId)+p.idle0,1000);
        assertEq(power.powerOf(id),2000);
    }
    function testMostlyIdleDepositRejected() public {
        venue.setSpendBps(100);vm.prank(alice);vm.expectRevert();vault.deposit(poolId,1000,1000,1,block.timestamp+100);
        assertEq(t0.balanceOf(alice),100000);assertEq(vault.sequence(),0);
    }
    function testFailedMintRollsBackWholeDeposit() public {
        venue.setFail(true);vm.prank(alice);vm.expectRevert();vault.deposit(poolId,1000,1000,1,block.timestamp+100);
        assertEq(t0.balanceOf(alice),100000);assertEq(vault.sequence(),0);assertEq(vault.totalIdle(address(t0)),0);
    }
    function testDonationNeverBecomesAnotherNFTPrincipal() public {
        t0.mint(address(vault),777);uint256 id=deposit();assertEq(vault.position(id).idle0,10);assertEq(vault.totalIdle(address(t0)),10);
        assertEq(t0.balanceOf(address(vault)),787);
    }
    function testFeesNotPrincipal() public {
        uint256 id=deposit();venue.setFees(100,100);vault.collectFees(id,block.timestamp+100);
        assertEq(vault.position(id).idle0,10);assertEq(rewards.claimable(id,address(t0)),80);assertEq(fees.compoundBalance(id,address(t0)),10);
    }
    function testCompoundingAddsOnlyDesignatedShare() public {
        uint256 id=deposit();venue.setFees(100,100);compounder.compound(id,1,block.timestamp+100);
        Position memory p=vault.position(id);assertEq(p.idle0+venue.a0(p.lpTokenId),1010);
        assertEq(rewards.claimable(id,address(t0)),80);assertEq(fees.buybackBalance(address(t0)),10);assertEq(power.powerOf(id),2000);
    }
    function testRebalanceReplacesLPButPreservesEconomicNFT() public {
        uint256 id=deposit();uint256 old=vault.position(id).lpTokenId;vault.rebalance(id,1,block.timestamp+100);
        Position memory p=vault.position(id);assertTrue(p.lpTokenId!=old);assertEq(nft.ownerOf(id),alice);
        assertEq(p.idle0+venue.a0(p.lpTokenId),1000);vm.expectRevert();venue.ownerOf(old);
    }
    function testOnlyKeeperCanRebalance() public {uint256 id=deposit();vm.prank(alice);vm.expectRevert();vault.rebalance(id,1,block.timestamp+100);}
    function testNoOwnerWithdrawalEntrypoint() public {
        uint256 id=deposit();vm.prank(alice);(bool ok,)=address(vault).call(abi.encodeWithSignature("withdraw(uint256)",id));assertFalse(ok);
    }
    function testNFTUserCannotTransferUnderlyingLP() public {
        uint256 id=deposit();uint256 lp=vault.position(id).lpTokenId;
        vm.prank(alice);vm.expectRevert();venue.transferFrom(address(vault),alice,lp);
    }
    function testTopUpKeepsBothNFTsAndCheckpointsFees() public {
        uint256 id=deposit();uint256 lp=vault.position(id).lpTokenId;venue.setFees(100,100);
        vm.prank(alice);vault.increase(id,100,100,1,block.timestamp+100);
        assertEq(vault.position(id).lpTokenId,lp);assertEq(rewards.claimable(id,address(t0)),80);assertEq(power.powerOf(id),2200);
    }
    function testMigrationReleaseOnlyGoesToBoundModule() public {
        uint256 id=deposit();vm.prank(alice);vm.expectRevert();vault.releaseForMigration(id,bytes32(uint256(1)),block.timestamp+100);
        (uint256 a,uint256 b)=vault.releaseForMigration(id,bytes32(uint256(1)),block.timestamp+100);
        assertEq(a,1000);assertEq(b,1000);assertEq(uint256(vault.position(id).status),uint256(PositionStatus.Outbound));
        assertEq(vault.totalIdle(address(t0)),0);assertEq(nft.ownerOf(id),alice);
    }
    function testSatelliteCannotIssueAnotherCollection() public {
        vm.chainId(block.chainid+1);vm.prank(alice);vm.expectRevert();vault.deposit(poolId,1000,1000,1,block.timestamp+100);
        assertEq(vault.sequence(),0);
    }
    function testPauseBlocksDeposit() public {
        ac.setPaused(true);vm.prank(alice);vm.expectRevert();vault.deposit(poolId,1000,1000,1,block.timestamp+100);
    }
}
