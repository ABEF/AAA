// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
// These are ABI/action/custody unit tests with fake settlement, NOT real Uniswap integration tests.
import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {Ids,PoolKey,PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockToken,MockPools} from "./mocks/Mocks.sol";
contract FakePermit2 {
    mapping(address=>mapping(address=>mapping(address=>uint160))) public amount;
    function approve(address token,address spender,uint160 value,uint48) external {amount[msg.sender][token][spender]=value;}
    function pay(address owner,address token,uint256 n) external {
        require(amount[owner][token][msg.sender]>=n);amount[owner][token][msg.sender]-=uint160(n);
        require(IERC20(token).transferFrom(owner,msg.sender,n));
    }
}
contract FakePoolManager {}
contract FakeState {
    address public immutable poolManager;
    constructor(address p){poolManager=p;}
    function getSlot0(bytes32) external pure returns(uint160,int24,uint24,uint24){return(uint160(1<<96),0,0,3000);}
}
contract FakePolicy {
    function validatePrice(bytes32) external pure returns(uint160){return uint160(1<<96);}
}
contract FakePositionManager is ERC721 {
    address public immutable poolManager;FakePermit2 public immutable permit2;
    uint256 public nextTokenId=1;uint256 public calls;uint256 public collects;
    mapping(uint256=>uint128) public getPositionLiquidity;
    mapping(uint256=>PoolKey) private keys;mapping(uint256=>uint256) private info;
    mapping(uint256=>uint256) public principal0;mapping(uint256=>uint256) public principal1;
    constructor(address p,address a) ERC721("Fake LP","FLP"){poolManager=p;permit2=FakePermit2(a);}
    function getPoolAndPositionInfo(uint256 id) external view returns(PoolKey memory,uint256){return(keys[id],info[id]);}
    function modifyLiquidities(bytes calldata encoded,uint256 deadline) external payable {
        require(block.timestamp<=deadline);calls++;
        (bytes memory actions,bytes[] memory args)=abi.decode(encoded,(bytes,bytes[]));require(actions.length==2&&args.length==2);
        uint256 id;uint256 liq;uint128 a0;uint128 a1;PoolKey memory k;
        if(uint8(actions[0])==2){
            int24 lower;int24 upper;address recipient;bytes memory hd;
            (k,lower,upper,liq,a0,a1,recipient,hd)=abi.decode(args[0],(PoolKey,int24,int24,uint256,uint128,uint128,address,bytes));
            require(hd.length==0);id=nextTokenId++;_mint(recipient,id);keys[id]=k;
            info[id]=(uint256(uint24(lower))<<8)|(uint256(uint24(upper))<<32);
        }else if(uint8(actions[0])==0){
            bytes memory hd;(id,liq,a0,a1,hd)=abi.decode(args[0],(uint256,uint256,uint128,uint128,bytes));
            require(getApproved(id)==msg.sender);k=keys[id];
        }else if(uint8(actions[0])==1){
            bytes memory hd;(id,liq,a0,a1,hd)=abi.decode(args[0],(uint256,uint256,uint128,uint128,bytes));
            require(getApproved(id)==msg.sender&&liq==0&&uint8(actions[1])==0x11);collects++;
            (address t0,address t1,address recipient)=abi.decode(args[1],(address,address,address));
            require(t0==keys[id].currency0&&t1==keys[id].currency1);
            MockToken(t0).mint(recipient,50);MockToken(t1).mint(recipient,30);return;
        }else revert("unsupported fake action");
        require(uint8(actions[1])==0x0d);(address s0,address s1)=abi.decode(args[1],(address,address));
        require(s0==k.currency0&&s1==k.currency1);
        // Deliberately spend half to test attribution of unused deposits.
        permit2.pay(msg.sender,s0,uint256(a0)/2);permit2.pay(msg.sender,s1,uint256(a1)/2);
        principal0[id]+=uint256(a0)/2;principal1[id]+=uint256(a1)/2;getPositionLiquidity[id]+=uint128(liq);
    }
}
contract LiquidityEncodingTest is Test {
    MockAccess ac;MockToken t0;MockToken t1;MockPools pools;FakePermit2 permit;
    FakePositionManager posm;ZZZLiquidityManager manager;bytes32 poolId;
    function setUp() public {
        ac=new MockAccess(); ProtocolPolicyFixture.bind(address(ac));t0=new MockToken(18);t1=new MockToken(18);pools=new MockPools();permit=new FakePermit2();
        FakePoolManager core=new FakePoolManager();FakeState state=new FakeState(address(core));FakePolicy policy=new FakePolicy();
        posm=new FakePositionManager(address(core),address(permit));
        manager=new ZZZLiquidityManager(address(ac),address(posm),address(state),address(core),address(permit), address(new ZZZLPBalancer(address(ac), address(core), address(state))));
        PoolConfig memory c;c.key=PoolKey(address(t0),address(t1),3000,60,address(0));c.operationsEnabled=true;c.maxSlippageBps=100;
        poolId=keccak256(abi.encode(c.key));pools.set(poolId,c);
        ac.bind(Ids.VAULT,address(this));ac.bind(Ids.POOLS,address(pools));ac.bind(Ids.STRATEGY,address(policy));ac.seal();
        t0.mint(address(this),100e18);t1.mint(address(this),100e18);t0.approve(address(manager),type(uint256).max); t0.approve(manager.positionOperator(), type(uint256).max);t1.approve(address(manager),type(uint256).max); t1.approve(manager.positionOperator(), type(uint256).max);
    }
    function mint() private returns(uint256 id){(id,,)=manager.mint(poolId,-600,600,10e18,10e18,1,block.timestamp+100);posm.approve(manager.positionOperator(),id);}
    function testMintKeepsNFTInVaultAndRefundsExactUnused() public {
        (uint256 id,uint256 s0,uint256 s1)=manager.mint(poolId,-600,600,10e18,10e18,1,block.timestamp+100);
        assertEq(posm.ownerOf(id),address(this));assertEq(s0,5e18);assertEq(s1,5e18);
        assertEq(t0.balanceOf(address(this)),95e18);assertEq(t0.balanceOf(address(manager)),0);
    }
    function testApprovalsCleared() public {
        mint();assertEq(t0.allowance(address(manager),address(permit)),0);
        assertEq(permit.amount(address(manager),address(t0),address(posm)),0);
    }
    function testIncreasePreservesPositionID() public {
        uint256 id=mint();uint128 beforeLiquidity=posm.getPositionLiquidity(id);
        manager.increase(poolId,id,10e18,10e18,1,block.timestamp+100);
        assertEq(posm.nextTokenId(),2);assertGt(posm.getPositionLiquidity(id),beforeLiquidity);
    }
    function testCollectUsesZeroDecreaseAndVaultRecipient() public {
        uint256 id=mint();uint128 beforeLiquidity=posm.getPositionLiquidity(id);uint256 b=t0.balanceOf(address(this));
        manager.collect(poolId,id,block.timestamp+100);assertEq(posm.collects(),1);assertEq(t0.balanceOf(address(this)),b+50);
        assertEq(posm.getPositionLiquidity(id),beforeLiquidity);
    }
    function testUnauthorizedMintRejected() public {
        vm.prank(address(0xB0B));vm.expectRevert();manager.mint(poolId,-600,600,1e18,1e18,1,block.timestamp+100);
    }
    function testInvalidTickSpacingRejected() public {vm.expectRevert();manager.mint(poolId,-601,600,1e18,1e18,1,block.timestamp+100);}
    function testExpiredDeadlineRejected() public {vm.warp(1000);vm.expectRevert();manager.mint(poolId,-600,600,1e18,1e18,1,999);}
    function testMinimumLiquidityEnforced() public {vm.expectRevert();manager.mint(poolId,-600,600,1e18,1e18,type(uint128).max,block.timestamp+100);}
    function testUnsolicitedCallbackRejected() public {vm.expectRevert();manager.unlockCallback(bytes(""));}
    function testDonationsNotSweptToNextDepositor() public {
        t0.mint(address(manager),123);mint();assertEq(t0.balanceOf(address(manager)),123);
    }
}
