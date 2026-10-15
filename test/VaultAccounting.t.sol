// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
// Integration of real vault/rewards/NFT/Membership contracts, with a FAKE liquidity venue.
import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids,PoolKey,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {MockAccess,MockToken,MockPools,MockFeed} from "./mocks/Mocks.sol";
contract VaultPolicyMock {
    bool public need=true;
    uint256 public swapAmount;
    function setSwapAmount(uint256 amount) external {swapAmount=amount;}
    function setNeed(bool v) external {need=v;}
    function needsRebalance(uint256) external view returns(bool){return need;}
    function target(bytes32) external pure returns(int24,int24,uint160){return(-600,600,uint160(1<<96));}
    function validatePrice(bytes32) external pure returns(uint160){return uint160(1<<96);}
    function validateExitPrice(bytes32) external pure returns(uint160){return uint160(1<<96);}
    function compoundPlan(uint256,uint256,uint256) external view returns(bool,uint256,uint256){return(true,swapAmount,swapAmount);}
    function swapPlan(bytes32,uint256,uint256) external pure returns(bool,uint256,uint256){return(false,0,0);}
}
contract VaultLiquidityMock is ERC721 {
    // Default positive fixture deploys every supplied unit. Tests that exercise
    // idle/rounding losses select 9900 explicitly instead of taxing all entries.
    MockToken public t0;MockToken public t1;uint256 public next=1;bool public failMint;uint256 public spendBps=10000;
    uint256 public fee0;uint256 public fee1;
    uint256 public repricingLP;uint256 public repricingGain;
    mapping(uint256=>uint256) public a0;mapping(uint256=>uint256) public a1;
    constructor(address x,address y)ERC721("Mock venue","MV"){t0=MockToken(x);t1=MockToken(y);}
    function positionManager() external view returns(address){return address(this);}
    function setFees(uint256 x,uint256 y) external {fee0=x;fee1=y;}
    function setSpendBps(uint256 x) external {spendBps=x;}
    function setRepricing(uint256 id,uint256 gain) external {repricingLP=id;repricingGain=gain;}
    // Explicitly artificial quantity repricing to catch share-issuance snapshots
    // taken before an entry swap; this is not a model of Uniswap profitability.
    function swap(bytes32,bool zeroForOne,uint256 amount,uint256,uint256) external returns(uint256) {
        if(zeroForOne){require(t0.transferFrom(msg.sender,address(this),amount));t1.mint(msg.sender,amount);}
        else{require(t1.transferFrom(msg.sender,address(this),amount));t0.mint(msg.sender,amount);}
        if(repricingLP!=0){a0[repricingLP]+=repricingGain;t0.mint(address(this),repricingGain);}
        return amount;
    }
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
contract RejectingMintReceiver {
    function mint(ZZZVault target) external payable returns(uint256) {return target.mintDormant{value:msg.value}();}
}
contract RejectingMintTreasury { receive() external payable {revert("reject proceeds");} }
contract ReentrantMintReceiver is IERC721Receiver {
    ZZZVault public immutable vault;bool public attempted;bool public reentrySucceeded;bytes4 public reentryError;
    constructor(ZZZVault target){vault=target;}
    function mint() external payable returns(uint256){return vault.mintDormant{value:msg.value}();}
    function onERC721Received(address,address,uint256,bytes calldata) external returns(bytes4) {
        if (!attempted) {
            attempted=true;
            (bool ok,bytes memory result)=address(vault).call{value:0.05 ether}(abi.encodeCall(ZZZVault.mintDormant,()));
            reentrySucceeded=ok;if(result.length>=4)reentryError=bytes4(result);
        }
        return IERC721Receiver.onERC721Received.selector;
    }
}
contract ReentrantMintTreasury is IERC721Receiver {
    ZZZVault public vault;bool public attempted;bool public reentrySucceeded;bytes4 public reentryError;
    function configure(ZZZVault target) external {vault=target;}
    receive() external payable {
        if (!attempted) {
            attempted=true;
            (bool ok,bytes memory result)=address(vault).call{value:0.05 ether}(abi.encodeCall(ZZZVault.mintDormant,()));
            reentrySucceeded=ok;if(result.length>=4)reentryError=bytes4(result);
        }
    }
    function onERC721Received(address,address,uint256,bytes calldata) external pure returns(bytes4) {
        return IERC721Receiver.onERC721Received.selector;
    }
}
abstract contract PooledVaultFixture is Test {
    MockAccess ac;MockToken t0;MockToken t1;MockPools pools;VaultPolicyMock policy;VaultLiquidityMock venue;
    ZZZVault vault;ZZZNFT nft;ZZZMembership membership;MockVRF vrf;ZZZRewards rewards;ZZZFeeController fees;ZZZCompounder compounder;ZZZOracle oracle;
    bytes32 poolId;address alice=address(0xA11CE);address bob=address(0xB0B);address payable treasury=payable(address(0x7EA5));
    function _record(uint256 id) internal view returns(Position memory p) {
        uint256 bucket=vault.nftBucket(id);
        if(bucket!=0)p=vault.group(bucket);
        p.status=vault.nftStatus(id);p.depositUSD=vault.contributionUSD(id);

    }
    function _bucket() internal view returns(uint256) {return uint256(keccak256(abi.encode(block.chainid,address(vault),poolId)));}
    function activePlan(uint256) external pure returns(bytes32) {return bytes32(0);}
    function setUp() public { _fixture(treasury); }
    function _fixture(address payable recipient) internal {
        vm.warp(1_000_000);ac=new MockAccess();t0=new MockToken(0);t1=new MockToken(0);pools=new MockPools();policy=new VaultPolicyMock();
        venue=new VaultLiquidityMock(address(t0),address(t1));vault=new ZZZVault(address(ac),block.chainid,recipient);nft=new ZZZNFT(address(ac),"");
        membership=new ZZZMembership(address(ac));rewards=new ZZZRewards(address(ac));fees=new ZZZFeeController(address(ac));
        compounder=new ZZZCompounder(address(ac));oracle=new ZZZOracle(address(ac),address(0));
        MockFeed feed=new MockFeed(8,1e8);oracle.setFeed(address(t0),address(feed),3600);oracle.setFeed(address(t1),address(feed),3600);
        ac.bind(Ids.VAULT,address(vault));ac.bind(Ids.NFT,address(nft));ac.bind(Ids.MEMBERSHIP,address(membership));ac.bind(Ids.REWARDS,address(rewards));
        ac.bind(Ids.FEES,address(fees));ac.bind(Ids.COMPOUNDER,address(compounder));ac.bind(Ids.LIQUIDITY,address(venue));
        ac.bind(Ids.STRATEGY,address(policy));ac.bind(Ids.POOLS,address(pools));ac.bind(Ids.ORACLE,address(oracle));
        ac.bind(Ids.MIGRATION,address(this));ac.bind(Ids.RECEIVER,address(0x987));ac.setKeeper(address(this),true);
        vrf=new MockVRF();nft.configureRandomness(address(vrf),bytes32(uint256(1)),1,3,500000,false);
        rewards.addAsset(address(t0));rewards.addAsset(address(t1));
        PoolConfig memory c;c.key=PoolKey(address(t0),address(t1),3000,60,address(0));c.operationsEnabled=true;c.depositsEnabled=true;
        c.minDepositUSD=1e18;c.maxPositionUSD=1e30;c.maxSlippageBps=100;poolId=keccak256(abi.encode(c.key));pools.set(poolId,c);ac.seal();
        _fundUser(alice);_fundUser(bob);vm.deal(address(this),10 ether);
    }
    function _fundUser(address owner) internal {
        vm.deal(owner,1 ether);t0.mint(owner,100000);t1.mint(owner,100000);
        vm.startPrank(owner);t0.approve(address(vault),type(uint256).max);t1.approve(address(vault),type(uint256).max);vm.stopPrank();
    }
    function _mint(address owner) internal returns(uint256 id){vm.prank(owner);id=vault.mintDormant{value:0.05 ether}();vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);}
    function _activate(address owner,uint256 id,uint256 amount0,uint256 amount1) internal {
        vm.prank(owner);vault.activate(id,poolId,amount0,amount1,1,block.timestamp+100);
    }
    function activatedPosition() internal returns(uint256 id){id=_mint(alice);_activate(alice,id,1000,1000);}
}
contract VaultAccountingTest is PooledVaultFixture {
    function testActivationLeavesExactAttributedIdle() public {
        venue.setSpendBps(9900);
        uint256 id=activatedPosition();Position memory p=_record(id);assertEq(nft.ownerOf(id),alice);assertEq(venue.ownerOf(p.lpTokenId),address(vault));
        assertEq(p.idle0,10);assertEq(vault.totalIdle(address(t0)),10);assertEq(venue.a0(p.lpTokenId)+p.idle0,1000);
        assertTrue(membership.eligible(id));assertEq(vault.contributionUSD(id),2000e18);
    }
    function testMostlyIdleActivationRejected() public {
        uint256 id=_mint(alice);venue.setSpendBps(100);vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        assertEq(t0.balanceOf(alice),100000);assertEq(vault.sequence(),1);assertEq(uint256(_record(id).status),uint256(PositionStatus.Dormant));
    }
    function testVenueFailureRollsBackActivationKeepsPaidDormantNFT() public {
        uint256 id=_mint(alice);uint256 paid=treasury.balance;venue.setFail(true);vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        assertEq(t0.balanceOf(alice),100000);assertEq(vault.sequence(),1);assertEq(vault.totalIdle(address(t0)),0);
        assertEq(nft.ownerOf(id),alice);assertEq(treasury.balance,paid);assertEq(uint256(_record(id).status),uint256(PositionStatus.Dormant));
        assertEq(_record(id).poolId,bytes32(0));assertEq(_record(id).depositUSD,0);assertFalse(membership.eligible(id));
    }
    function testDonationNeverBecomesAnotherNFTPrincipal() public {
        venue.setSpendBps(9900);
        t0.mint(address(vault),777);uint256 id=activatedPosition();assertEq(_record(id).idle0,10);assertEq(vault.totalIdle(address(t0)),10);
        assertEq(t0.balanceOf(address(vault)),787);
    }
    function testFeesNotPrincipal() public {
        venue.setSpendBps(9900);
        uint256 id=activatedPosition();venue.setFees(100,100);vault.collectFees(_bucket(),block.timestamp+100);
        assertEq(_record(id).idle0,10);assertEq(rewards.claimable(id,address(t0)),90);assertEq(fees.compoundBalance(_bucket(),address(t0)),5);
    }
    function testCompoundingAddsOnlyDesignatedShare() public {
        uint256 id=activatedPosition();venue.setFees(100,100);compounder.compound(_bucket(),1,block.timestamp+100);
        Position memory p=_record(id);assertEq(p.idle0+venue.a0(p.lpTokenId),1005);
        assertEq(rewards.claimable(id,address(t0)),90);assertEq(fees.buybackBalance(address(t0)),5);assertTrue(membership.eligible(id));assertEq(vault.contributionUSD(id),2000e18);
    }
    function testRebalanceReplacesLPButPreservesEconomicNFT() public {
        uint256 id=activatedPosition();uint256 old=_record(id).lpTokenId;vault.rebalance(_bucket(),1,block.timestamp+100);
        Position memory p=_record(id);assertTrue(p.lpTokenId!=old);assertEq(nft.ownerOf(id),alice);
        assertEq(p.idle0+venue.a0(p.lpTokenId),1000);vm.expectRevert();venue.ownerOf(old);
    }
    function testOnlyKeeperCanRebalance() public {uint256 id=activatedPosition();vm.prank(alice);vm.expectRevert();vault.rebalance(_bucket(),1,block.timestamp+100);}
    function testNoOwnerWithdrawalEntrypoint() public {
        uint256 id=activatedPosition();vm.prank(alice);(bool ok,)=address(vault).call(abi.encodeWithSignature("withdraw(uint256)",id));assertFalse(ok);
    }
    function testNFTUserCannotTransferUnderlyingLP() public {
        uint256 id=activatedPosition();uint256 lp=_record(id).lpTokenId;
        vm.prank(alice);vm.expectRevert();venue.transferFrom(address(vault),alice,lp);
    }
    function testTopUpKeepsBothNFTsAndCheckpointsFees() public {
        uint256 id=activatedPosition();uint256 lp=_record(id).lpTokenId;venue.setFees(100,100);
        vm.prank(alice);vault.increase(id,100,100,1,block.timestamp+100);
        assertEq(_record(id).lpTokenId,lp);assertEq(rewards.claimable(id,address(t0)),90);assertTrue(membership.eligible(id));assertEq(vault.contributionUSD(id),2200e18);
    }
    function testMigrationReleaseOnlyGoesToBoundModule() public {
        uint256 id=activatedPosition();vm.prank(alice);vm.expectRevert();vault.releaseForMigration(_bucket(),bytes32(uint256(1)),block.timestamp+100);
        (uint256 a,uint256 b)=vault.releaseForMigration(_bucket(),bytes32(uint256(1)),block.timestamp+100);
        assertEq(a,1000);assertEq(b,1000);assertEq(uint256(_record(id).status),uint256(PositionStatus.Outbound));
        assertEq(vault.totalIdle(address(t0)),0);assertEq(nft.ownerOf(id),alice);
    }
    function testSatelliteCannotIssueAnotherCollection() public {
        vm.chainId(block.chainid+1);vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}();
        assertEq(vault.sequence(),0);
    }
    function testPauseBlocksMint() public {
        ac.setPaused(true);vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}();
        assertEq(vault.sequence(),0);
    }
    function testDormantMintForwardsPriceWithoutLiquidityOrRewards() public {
        uint256 beforeTreasury=treasury.balance;uint256 beforeOwner=alice.balance;uint256 id=_mint(alice);Position memory p=_record(id);
        assertEq(vault.MINT_PRICE(),0.05 ether); // Gross minimum is exercised by the 99/100 input tests.
        assertEq(vault.mintProceedsRecipient(),treasury);assertEq(treasury.balance,beforeTreasury+0.05 ether);
        assertEq(alice.balance,beforeOwner-0.05 ether);assertEq(address(vault).balance,0);assertEq(nft.ownerOf(id),alice);
        assertEq(uint256(p.status),uint256(PositionStatus.Dormant));assertEq(p.poolId,bytes32(0));assertEq(p.lpTokenId,0);
        assertEq(p.depositUSD,0);assertEq(p.idle0,0);assertEq(p.idle1,0);assertFalse(membership.eligible(id));assertEq(membership.totalEligible(),0);
        assertEq(vault.totalIdle(address(t0)),0);assertEq(vault.totalIdle(address(t1)),0);assertEq(venue.next(),1);
        assertEq(rewards.claimable(id,address(t0)),0);assertEq(rewards.claimable(id,address(t1)),0);
        assertEq(fees.compoundBalance(_bucket(),address(t0)),0);assertEq(fees.buybackBalance(address(t0)),0);
        assertEq(vault.canonicalChainId(),block.chainid);assertEq(vault.nftBucket(id),0);assertEq(vault.sharesOf(id),0);assertEq(vault.contributionUSD(id),0);
    }
    function testFuzzMintRejectsAnyUnderpayment(uint256 payment) public {
        payment=bound(payment,0,0.05 ether-1);uint256 beforeTreasury=treasury.balance;uint256 beforeOwner=alice.balance;
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:payment}();
        assertEq(vault.sequence(),0);assertEq(treasury.balance,beforeTreasury);assertEq(alice.balance,beforeOwner);
    }
    function testFuzzMintRejectsAnyOverpayment(uint256 payment) public {
        payment=bound(payment,0.05 ether+1,1 ether);uint256 beforeTreasury=treasury.balance;uint256 beforeOwner=alice.balance;
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:payment}();
        assertEq(vault.sequence(),0);assertEq(treasury.balance,beforeTreasury);assertEq(alice.balance,beforeOwner);
    }
    function testRejectingNFTReceiverRollsBackMintAndPayment() public {
        RejectingMintReceiver receiver=new RejectingMintReceiver();uint256 beforeTreasury=treasury.balance;
        vm.expectRevert();receiver.mint{value:0.05 ether}(vault);
        assertEq(vault.sequence(),0);assertEq(treasury.balance,beforeTreasury);assertEq(address(vault).balance,0);
        uint256 rejectedId=uint256(keccak256(abi.encode(block.chainid,address(vault),uint256(1))));
        assertEq(uint256(_record(rejectedId).status),uint256(PositionStatus.None));vm.expectRevert();nft.ownerOf(rejectedId);
    }
    function testRejectingTreasuryRollsBackNFTAndPayment() public {
        RejectingMintTreasury receiver=new RejectingMintTreasury();_fixture(payable(address(receiver)));uint256 beforeOwner=alice.balance;
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}();
        assertEq(vault.sequence(),0);assertEq(alice.balance,beforeOwner);assertEq(address(receiver).balance,0);assertEq(address(vault).balance,0);
        uint256 rejectedId=uint256(keccak256(abi.encode(block.chainid,address(vault),uint256(1))));
        assertEq(uint256(_record(rejectedId).status),uint256(PositionStatus.None));vm.expectRevert();nft.ownerOf(rejectedId);
    }
    function testReceiverReentrancyCannotMintSecondNFT() public {
        ReentrantMintReceiver receiver=new ReentrantMintReceiver(vault);vm.deal(address(receiver),1 ether);
        uint256 id=receiver.mint{value:0.05 ether}();assertEq(nft.ownerOf(id),address(receiver));assertTrue(receiver.attempted());
        assertFalse(receiver.reentrySucceeded());assertEq(receiver.reentryError(),bytes4(keccak256("ReentrancyGuardReentrantCall()")));
        assertEq(vault.sequence(),1);assertEq(address(receiver).balance,1 ether);
    }
    function testTreasuryReentrancyCannotMintSecondNFT() public {
        ReentrantMintTreasury receiver=new ReentrantMintTreasury();_fixture(payable(address(receiver)));receiver.configure(vault);
        uint256 id=_mint(alice);assertEq(nft.ownerOf(id),alice);assertTrue(receiver.attempted());assertFalse(receiver.reentrySucceeded());
        assertEq(receiver.reentryError(),bytes4(keccak256("ReentrancyGuardReentrantCall()")));assertEq(vault.sequence(),1);
        assertEq(address(receiver).balance,0.05 ether);assertEq(address(vault).balance,0);
    }
    function testZeroProceedsRecipientRejected() public {
        vm.expectRevert();new ZZZVault(address(ac),block.chainid,payable(address(0)));
    }
    function testSelfProceedsRecipientRejected() public {
        address predicted=vm.computeCreateAddress(address(this),vm.getNonce(address(this)));
        vm.expectRevert();new ZZZVault(address(ac),block.chainid,payable(predicted));
    }
    function testUnsealedSystemCannotMint() public {
        MockAccess unsealed=new MockAccess();ZZZVault candidate=new ZZZVault(address(unsealed),block.chainid,treasury);
        vm.prank(alice);vm.expectRevert();candidate.mintDormant{value:0.05 ether}();assertEq(candidate.sequence(),0);
    }
    function testDormantTransferOnlyNewOwnerCanActivate() public {
        uint256 id=_mint(alice);vm.prank(alice);nft.transferFrom(alice,bob,id);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        _activate(bob,id,1000,1000);assertEq(nft.ownerOf(id),bob);assertEq(vault.sequence(),1);
        assertEq(uint256(_record(id).status),uint256(PositionStatus.Active));assertTrue(membership.eligible(id));assertEq(vault.contributionUSD(id),2000e18);
    }
    function testActivationCannotIssueSecondNFTOrChargeAnotherMintFee() public {
        uint256 id=_mint(alice);uint256 paid=treasury.balance;uint256 etherBalance=alice.balance;_activate(alice,id,1000,1000);
        assertEq(vault.sequence(),1);assertEq(nft.balanceOf(alice),1);assertEq(treasury.balance,paid);assertEq(alice.balance,etherBalance);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        assertEq(vault.sequence(),1);assertEq(nft.balanceOf(alice),1);assertEq(t0.balanceOf(alice),99000);
    }
    function testDormantCannotTopUpCollectCompoundRebalanceOrMigrate() public {
        uint256 id=_mint(alice);
        vm.prank(alice);vm.expectRevert();vault.increase(id,1000,1000,1,block.timestamp+100);
        vm.expectRevert();vault.collectFees(_bucket(),block.timestamp+100);
        vm.expectRevert();compounder.compound(_bucket(),1,block.timestamp+100);
        vm.expectRevert();vault.rebalance(_bucket(),1,block.timestamp+100);
        vm.expectRevert();vault.releaseForMigration(_bucket(),bytes32(uint256(1)),block.timestamp+100);
        assertEq(membership.totalEligible(),0);assertEq(_record(id).lpTokenId,0);
    }
    function testActivationRequiresAtLeast100USDInput() public {
        uint256 id=_mint(alice);venue.setSpendBps(10000);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,49,50,1,block.timestamp+100);
        assertEq(uint256(_record(id).status),uint256(PositionStatus.Dormant));assertEq(t0.balanceOf(alice),100000);
    }
    function testActivationRejects100InputWhenActualLPIsBelow99() public {
        venue.setSpendBps(9900);
        uint256 id=_mint(alice);
        // Integer rounding deploys only $98; the $100 input requires at least $99 LP.
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,50,50,1,block.timestamp+100);
        assertEq(uint256(_record(id).status),uint256(PositionStatus.Dormant));assertFalse(membership.eligible(id));
        assertEq(vault.totalIdle(address(t0)),0);assertEq(t0.balanceOf(alice),100000);assertEq(venue.next(),1);
    }
    function testExactly100ActualLPActivates() public {
        uint256 id=_mint(alice);venue.setSpendBps(10000);_activate(alice,id,50,50);
        Position memory p=_record(id);assertEq(venue.a0(p.lpTokenId)+venue.a1(p.lpTokenId),100);
        assertEq(p.idle0+p.idle1,0);assertEq(p.depositUSD,100e18);assertTrue(membership.eligible(id));assertEq(vault.contributionUSD(id),100e18);
    }
    function testActivationHonorsStricterPoolMinimum() public {
        uint256 id=_mint(alice);PoolConfig memory c=pools.get(poolId);c.minDepositUSD=1000e18;pools.set(poolId,c);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,450,450,1,block.timestamp+100);
        assertEq(uint256(_record(id).status),uint256(PositionStatus.Dormant));
    }
    function testPauseBlocksActivationKeepsDormantNFT() public {
        uint256 id=_mint(alice);ac.setPaused(true);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        assertEq(nft.ownerOf(id),alice);assertEq(uint256(_record(id).status),uint256(PositionStatus.Dormant));
    }
    function testWrongChainCannotActivateCanonicalDormantNFT() public {
        uint256 id=_mint(alice);vm.chainId(block.chainid+1);
        vm.prank(alice);vm.expectRevert();vault.activate(id,poolId,1000,1000,1,block.timestamp+100);
        assertEq(uint256(_record(id).status),uint256(PositionStatus.Dormant));assertFalse(membership.eligible(id));
    }
    function testOldDepositSelectorCannotBypassPaidMint() public {
        vm.prank(alice);(bool ok,)=address(vault).call(abi.encodeWithSignature("deposit(bytes32,uint256,uint256,uint128,uint256)",poolId,1000,1000,uint128(1),block.timestamp+100));
        assertFalse(ok);assertEq(vault.sequence(),0);assertEq(nft.balanceOf(alice),0);assertEq(t0.balanceOf(alice),100000);
    }
    function testActivationCannotCollectHistoricalSharedRewards() public {
        uint256 activeId=activatedPosition();uint256 dormantId=_mint(bob);venue.setFees(100,100);vault.collectFees(_bucket(),block.timestamp+100);
        assertEq(rewards.claimable(activeId,address(t0)),90);assertEq(rewards.claimable(dormantId,address(t0)),0);
        _activate(bob,dormantId,1000,1000);assertEq(rewards.claimable(dormantId,address(t0)),0);
        assertEq(rewards.paidIndex(dormantId,address(t0)),rewards.index(address(t0)));
        venue.setFees(100,100);vault.collectFees(_bucket(),block.timestamp+100);
        assertEq(rewards.claimable(dormantId,address(t0)),44);assertEq(rewards.claimable(activeId,address(t0)),135);
        vm.prank(bob);assertEq(rewards.claim(dormantId,address(t0)),44);assertEq(_record(dormantId).depositUSD,2000e18);
    }
}
