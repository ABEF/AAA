// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZCanonicalHandoff} from "../src/ZZZCanonicalHandoff.sol";
import {ZZZCanonicalLedger} from "../src/base/ZZZCanonicalLedger.sol";
import {ExactAsset} from "../src/libraries/ExactAsset.sol";
import {Ids,PoolKey,PoolConfig,Position,PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockToken,MockPools} from "./mocks/Mocks.sol";

/// TEST ONLY: deterministic custody ingress stub. It does not qualify venue math,
/// liquidity backing or a price provider; tests below target Migration's boundary.
contract NativeCustodyAssets {
    function isAsset(address) external pure returns(bool){return true;}
    function assetCount() external pure returns(uint256){return 1;}
    function assets(uint256) external pure returns(address){return address(0);}
}
contract NativeCustodyOracle {
    function price(address) external pure returns(uint256){return 1e18;}
    function tokenDecimals(address) external pure returns(uint8){return 0;}
    function value(address,uint256 amount) external pure returns(uint256){return amount*1e18;}
}
contract NativeCustodyVault {
    Position private p;
    MockToken public immutable token;
    uint256 public immutable canonicalChainId=block.chainid;
    uint256 public acceptedNative;
    bool public reject;
    constructor(MockToken t){token=t;}
    receive() external payable {}
    function set(Position memory next) external {p=next;}
    function setReject(bool value) external {reject=value;}
    function group(uint256) external view returns(Position memory){return p;}
    function bucketTotalShares(uint256) external pure returns(uint256){return 7;}
    function poolBucket(bytes32) external pure returns(uint256){return 1;}
    function releaseForMigration(uint256,bytes32,uint256) external returns(uint256 x,uint256 y){
        x=p.idle0;y=p.idle1;p.idle0=0;p.idle1=0;p.status=PositionStatus.Outbound;
        ExactAsset.push(address(0),msg.sender,x);ExactAsset.push(address(token),msg.sender,y);
    }
    function acceptHandoff(uint256,bytes32 pool,uint256 a0,uint256 a1,uint128 minimum,uint256) external payable {
        require(!reject && msg.value==a0,"native budget");
        require(token.transferFrom(msg.sender,address(this),a1));acceptedNative=msg.value;
        p.poolId=pool;p.idle0=a0;p.idle1=a1;p.status=minimum==0?PositionStatus.Parked:PositionStatus.Active;
    }
}
contract NativeCanonicalVault {
    uint256 public immutable canonicalChainId=block.chainid;
    uint256 public constant sequence=0;
    uint256 public constant bucketCount=0;
    function totalIdle(address) external pure returns(uint256){return 0;}
    function canonicalBarrier() external {}
    function canonicalWrite(uint8,bytes calldata) external {}
    function canonicalSend(address asset,address destination,uint256 amount) external {ExactAsset.push(asset,destination,amount);}
    receive() external payable {}
}
contract NativeLedgerHarness is ZZZCanonicalLedger {
    address private immutable controller;
    constructor(address a){controller=a;}
    receive() external payable {}
    function _canonicalAccess() internal view override returns(address){return controller;}
    function captureNative() external {_canonicalBeginCapture();_canonicalAdd(address(0),address(this).balance,0);}
    function importNative(uint256 amount) external {_canonicalBeginImport();_canonicalAdd(address(0),amount,address(this).balance);}
    function validate() external view {_canonicalValidateBacking();}
    function duplicateNative() external {_canonicalAdd(address(0),0,0);}
}
contract NativeVersionAccess is MockAccess {
    address public immutable bootstrap=msg.sender;
    function canonicalTransition(uint8 next,bool settling,bool) external {canonicalState=next;canonicalSettling=settling;}
}
contract OldCanonicalSchema {
    bytes32 public constant SCHEMA=keccak256("ZZZ_CANONICAL_SAME_CHAIN_V1");
}
contract RejectNativeCustody {receive() external payable {revert("recipient rejects");}}

contract NativeCustodyTest is Test {
    MockAccess ac;MockToken token;MockPools pools;NativeCustodyVault vault;ZZZMigration migration;
    bytes32 pool;address custody=address(0xC057);bytes32 review=keccak256("native custody unit");
    function setUp() public {
        ac=new MockAccess();token=new MockToken(0);pools=new MockPools();vault=new NativeCustodyVault(token);
        migration=new ZZZMigration(address(ac));ac.bind(Ids.VAULT,address(vault));ac.bind(Ids.POOLS,address(pools));
        ac.bind(Ids.MIGRATION,address(migration));ac.bind(Ids.REWARDS,address(new NativeCustodyAssets()));
        ac.bind(Ids.ORACLE,address(new NativeCustodyOracle()));ac.seal();
        PoolConfig memory c;c.key=PoolKey(address(0),address(token),3000,60,address(0));c.operationsEnabled=true;
        pool=keccak256(abi.encode(c.key));pools.set(pool,c);
        Position memory p;p.poolId=pool;p.status=PositionStatus.Parked;p.homeChain=block.chainid;
        p.homeVault=address(vault);p.locationChain=block.chainid;p.locationVault=address(vault);p.idle0=100;p.idle1=100;vault.set(p);
        vm.deal(address(vault),100);token.mint(address(vault),100);vm.deal(address(this),1 ether);
    }
    function _request() private view returns(ZZZMigration.Request memory r){
        r.bucket=1;r.sourceSnapshot=migration.sourceSnapshot(1);r.recipient=custody;r.recipientCodeHash=custody.codehash;
        r.destinationChain=block.chainid;r.destinationCustody=custody;r.output0=address(0);r.output1=address(token);
        r.rawExit=true;r.exitMinimum0=100;r.exitMinimum1=100;r.deadline=block.timestamp+100;r.reviewHash=review;
    }
    function _exit() private returns(bytes32 id){id=migration.approve(_request());ac.setPaused(true);migration.exit(id);}
    function _tokens() private {token.mint(address(this),100);token.approve(address(migration),100);}
    function testRawNativeExitHasNoZZZOrWrapperDependencyAndPreservesPrefund() public {
        vm.deal(address(migration),13);bytes32 id=_exit();
        assertEq(custody.balance,100);assertEq(token.balanceOf(custody),100);assertEq(address(migration).balance,13);
        (ZZZMigration.Status status,uint256 a0,uint256 a1,,)=migration.state(id);
        assertEq(uint256(status),uint256(ZZZMigration.Status.Sent));assertEq(a0,100);assertEq(a1,100);
        assertEq(migration.currentZZZ(),address(0)); // Unset is not an ETH-as-ZZZ identity.
    }
    function testRecoveryRequiresExactNativeValueDespitePrefunds() public {
        bytes32 id=_exit();_tokens();vm.deal(address(migration),200);
        vm.expectRevert();migration.recover(id,block.timestamp+100,"");
        vm.expectRevert();migration.recover{value:101}(id,block.timestamp+100,"");
        migration.recover{value:100}(id,block.timestamp+100,"");
        assertEq(vault.acceptedNative(),100);assertEq(address(migration).balance,200);
        assertEq(vault.group(1).idle0,100);assertEq(token.allowance(address(migration),address(vault)),0);
    }
    function testLocalCompletionForwardsExactNativeBudgetAndPreservesShares() public {
        bytes32 id=_exit();migration.bindLocalDestination(id,pool,100,100,review);ac.setPaused(false);_tokens();
        vm.expectRevert();migration.completeLocal(id,100,100,1,block.timestamp+100);
        migration.completeLocal{value:100}(id,100,100,1,block.timestamp+100);
        assertEq(vault.acceptedNative(),100);assertEq(uint256(vault.group(1).status),uint256(PositionStatus.Active));
        assertEq(migration.outstandingCount(),0);
    }
    function testRecoveryFailureRollsBackETHAndTokens() public {
        bytes32 id=_exit();_tokens();vault.setReject(true);uint256 eth=address(this).balance;
        vm.expectRevert();migration.recover{value:100}(id,block.timestamp+100,"");
        assertEq(address(this).balance,eth);assertEq(token.balanceOf(address(this)),100);
        assertEq(uint256(vault.group(1).status),uint256(PositionStatus.Outbound));
    }
    function testRejectingRecipientRollsBackWholeNativeExit() public {
        custody=address(new RejectNativeCustody());bytes32 id=migration.approve(_request());ac.setPaused(true);
        vm.expectRevert();migration.exit(id);assertEq(address(vault).balance,100);assertEq(token.balanceOf(address(vault)),100);
        assertEq(uint256(vault.group(1).status),uint256(PositionStatus.Parked));
    }
    function testUnsolicitedNativeTransferToMigrationFails() public {
        (bool ok,)=address(migration).call{value:1}("");assertFalse(ok);
    }
}

contract NativeCanonicalFundingTest is Test {
    function _access() private returns(MockAccess a){a=new MockAccess();a.bind(Ids.CANONICAL,address(this));}
    function testCanonicalLedgerNativeTwoStageFundingPartialAbortAndPrefund() public {
        MockAccess a=_access();MockAccess b=_access();NativeLedgerHarness source=new NativeLedgerHarness(address(a));
        NativeLedgerHarness target=new NativeLedgerHarness(address(b));a.setCanonicalState(1);b.setCanonicalState(2);
        vm.deal(address(source),2 ether);vm.deal(address(target),7);source.captureNative();target.importNative(2 ether);
        vm.expectRevert();target.canonicalAccept(0,address(source)); // Existing prefunds cannot fund the row.
        source.canonicalRelease(0,address(target));target.canonicalAccept(0,address(source));target.validate();
        vm.expectRevert();target.canonicalAccept(0,address(source));
        b.setCanonicalState(4);target.canonicalRelease(0,address(source));source.canonicalRestore(0,address(target));source.validate();
        assertEq(address(source).balance,2 ether);assertEq(address(target).balance,7);
        vm.expectRevert();source.canonicalRestore(0,address(target));
    }
    function testDuplicateNativeBackingCannotCreateTwoLiabilityRows() public {
        MockAccess a=_access();a.setCanonicalState(1);NativeLedgerHarness source=new NativeLedgerHarness(address(a));
        source.captureNative();vm.expectRevert();source.duplicateNative();
    }
    function testVaultCanonicalNativeForwardAndAbortUseZeroValueAcknowledgment() public {
        MockAccess a=_access();MockAccess b=_access();NativeCanonicalVault sourceVault=new NativeCanonicalVault();
        NativeCanonicalVault targetVault=new NativeCanonicalVault();a.bind(Ids.VAULT,address(sourceVault));b.bind(Ids.VAULT,address(targetVault));
        a.bind(Ids.REWARDS,address(new NativeCustodyAssets()));b.bind(Ids.REWARDS,address(new NativeCustodyAssets()));
        ZZZVaultCanonical source=new ZZZVaultCanonical(address(a),address(sourceVault),block.chainid);
        ZZZVaultCanonical target=new ZZZVaultCanonical(address(b),address(targetVault),block.chainid);
        a.setCanonicalState(1);b.setCanonicalState(2);vm.deal(address(sourceVault),2 ether);vm.deal(address(target),11);
        vm.deal(address(source),17);
        source.canonicalCapture();source.canonicalSettle();assertEq(source.canonicalAssetCount(),1);
        target.canonicalImport(0,source.canonicalExport(0));target.canonicalImport(1,source.canonicalExport(1));
        vm.expectRevert();target.canonicalAccept(0,address(source));
        source.canonicalRelease(0,address(target));target.canonicalAccept(0,address(source));target.canonicalValidate();
        assertEq(address(targetVault).balance,2 ether);assertEq(address(target).balance,11);
        b.setCanonicalState(4);target.canonicalRelease(0,address(source));source.canonicalRestore(0,address(target));source.canonicalValidate();
        assertEq(address(sourceVault).balance,2 ether);assertEq(address(targetVault).balance,0);assertEq(address(target).balance,11);
        assertEq(address(source).balance,17);
    }
    function testImportedVaultCompanionCanBecomeSourceAndRestoreWithoutOldImporterBaseline() public {
        MockAccess a=_access();MockAccess b=_access();NativeCanonicalVault sourceVault=new NativeCanonicalVault();
        NativeCanonicalVault targetVault=new NativeCanonicalVault();NativeCanonicalVault holding=new NativeCanonicalVault();
        a.bind(Ids.VAULT,address(sourceVault));b.bind(Ids.VAULT,address(targetVault));
        a.bind(Ids.REWARDS,address(new NativeCustodyAssets()));b.bind(Ids.REWARDS,address(new NativeCustodyAssets()));
        ZZZVaultCanonical source=new ZZZVaultCanonical(address(a),address(sourceVault),block.chainid);
        ZZZVaultCanonical target=new ZZZVaultCanonical(address(b),address(targetVault),block.chainid);
        a.setCanonicalState(1);b.setCanonicalState(2);vm.deal(address(sourceVault),2 ether);vm.deal(address(target),11);
        source.canonicalCapture();target.canonicalImport(0,source.canonicalExport(0));target.canonicalImport(1,source.canonicalExport(1));
        source.canonicalRelease(0,address(target));target.canonicalAccept(0,address(source));target.canonicalActivate();
        // Model a later canonical freeze after replacement activation. Its
        // prior importer prefund is now unrelated to the new source manifest.
        b.setCanonicalState(1);target.canonicalCapture();target.canonicalSettle();target.canonicalRelease(0,address(holding));
        holding.canonicalSend(address(0),address(target),2 ether);target.canonicalRestore(0,address(holding));
        target.canonicalValidate();assertEq(address(targetVault).balance,2 ether);assertEq(address(target).balance,11);
    }
    function testNativeImporterRejectsAnOldAccountingSchema() public {
        MockAccess oldSource=_access();oldSource.bind(Ids.CANONICAL,address(new OldCanonicalSchema()));oldSource.seal();
        NativeVersionAccess targetAccess=new NativeVersionAccess();targetAccess.bind(Ids.VAULT,address(new NativeCanonicalVault()));
        ZZZCanonicalHandoff target=new ZZZCanonicalHandoff(address(targetAccess));
        vm.expectRevert(ZZZCanonicalHandoff.UnsupportedTransport.selector);target.prepareImport(address(oldSource));
        assertEq(target.incomingSource(),address(0));assertEq(target.phase(),0);
    }
    function testCanonicalSchemaNamesNativeAccountingVersion() public {
        MockAccess a=_access();ZZZCanonicalHandoff handoff=new ZZZCanonicalHandoff(address(a));
        assertEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_V1"));
    }
}

/// TEST ONLY: includes native as the last item to exercise the full 33-asset
/// finite bound, even though the ordinary deployed Rewards list adds ETH first.
contract NativeHistoricalAssets {
    uint256 public assetCount=33;
    function setCount(uint256 count) external {assetCount=count;}
    function assets(uint256 i) external pure returns(address){return i==32?address(0):address(uint160(i+1));}
    function compoundBalance(uint256,address asset) external pure returns(uint256){return asset==address(0)?3:0;}
}
contract NativeMigrationBudgetTest is Test {
    Position private p;
    mapping(address=>uint256) public totalIdle;
    function group(uint256) external view returns(Position memory){return p;}
    function testHistoricalNativeCompoundIncludesFullThirtyThreeAssetBound() public {
        MockAccess ac=new MockAccess();MockPools pools=new MockPools();NativeHistoricalAssets assets=new NativeHistoricalAssets();
        ac.bind(Ids.POOLS,address(pools));ac.bind(Ids.REWARDS,address(assets));ac.bind(Ids.FEES,address(assets));
        ac.bind(Ids.ORACLE,address(new NativeCustodyOracle()));
        PoolConfig memory c;c.key=PoolKey(address(100),address(200),3000,60,address(0));p.poolId=keccak256(abi.encode(c.key));pools.set(p.poolId,c);
        ZZZMigrationBudget budget=new ZZZMigrationBudget(address(ac));budget.recordComposition(1);
        assertEq(budget.historicalCompoundValue(1),3e18);
        assets.setCount(34);vm.expectRevert();budget.historicalCompoundValue(1);
    }
    function testNativeIdleBackingReadsBalanceWithoutERC20Call() public {
        MockAccess ac=new MockAccess();MockPools pools=new MockPools();MockToken t=new MockToken(0);ac.bind(Ids.POOLS,address(pools));
        PoolConfig memory c;c.key=PoolKey(address(0),address(t),3000,60,address(0));p.poolId=keccak256(abi.encode(c.key));pools.set(p.poolId,c);
        ZZZMigrationBudget budget=new ZZZMigrationBudget(address(ac));totalIdle[address(0)]=2;vm.deal(address(this),2);budget.assertIdle(1);
        vm.deal(address(this),1);vm.expectRevert();budget.assertIdle(1);
    }
}
