// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZContributionPricing} from "../src/ZZZContributionPricing.sol";
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
    ZZZContributionPricing public immutable contributionPricing;
    constructor(address controller) { contributionPricing = new ZZZContributionPricing(controller,address(this)); }
    function price(address) external pure returns(uint256){return 1e18;}
    function tokenDecimals(address) external pure returns(uint8){return 0;}
    function value(address,uint256 amount) external pure returns(uint256){return amount*1e18;}
}
contract NativeCanonicalVault {
    uint256 public constant ACCOUNTING_VERSION=7;
    uint256 public immutable canonicalChainId=block.chainid;
    uint256 public constant sequence=0;
    uint256 public constant bucketCount=0;
    function totalIdle(address) external pure returns(uint256){return 0;}
    function canonicalBarrier() external {}
    function canonicalWrite(uint8,bytes calldata) external {}
    function canonicalSend(address asset,address destination,uint256 amount) external {ExactAsset.push(asset,destination,amount);}
    receive() external payable {}
}
contract NativeClosedPortfolio {
    uint256 public constant PORTFOLIO_VERSION=2;
    function activeSecondaryCount() external pure returns(uint256){return 0;}
}
contract NativeLedgerHarness is ZZZCanonicalLedger {
    address private immutable controller;
    constructor(address a){controller=a;}
    receive() external payable {}
    function _canonicalAccess() internal view override returns(address){return controller;}
    function captureNative() external {_canonicalBeginCapture();_canonicalAdd(address(0),address(this).balance,0);}
    function importNative(uint256 amount) external {
        if (_state() != 2 || canonicalCursor != 0) revert CanonicalState();
        _canonicalAdd(address(0),amount,address(this).balance);
    }
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
contract OldNativeFeeSchema {
    bytes32 public constant SCHEMA=keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2");
}
contract RejectNativeCustody {receive() external payable {revert("recipient rejects");}}

contract NativeCanonicalFundingTest is Test {
    function _access() private returns(MockAccess a){
        a=new MockAccess(); ProtocolPolicyFixture.bind(address(a));a.bind(Ids.CANONICAL,address(this));
        a.bind(Ids.LIQUIDITY,address(new NativeClosedPortfolio()));
    }
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
        NativeVersionAccess targetAccess=new NativeVersionAccess(); ProtocolPolicyFixture.bind(address(targetAccess));targetAccess.bind(Ids.VAULT,address(new NativeCanonicalVault()));
        ZZZCanonicalHandoff target=new ZZZCanonicalHandoff(address(targetAccess));
        vm.expectRevert(ZZZCanonicalHandoff.UnsupportedTransport.selector);target.prepareImport(address(oldSource));
        assertEq(target.incomingSource(),address(0));assertEq(target.phase(),0);
    }
    function testCanonicalSchemaNamesNativeAccountingVersion() public {
        MockAccess a=_access();ZZZCanonicalHandoff handoff=new ZZZCanonicalHandoff(address(a));
        assertEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_ROYALTY_OPENING_V7"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2"));
        assertNotEq(handoff.SCHEMA(),keccak256("ZZZ_CANONICAL_SAME_CHAIN_V1"));
    }
    function testLPOnlyImporterRejectsTheOldNativeFeeCodec() public {
        MockAccess oldSource=_access();oldSource.bind(Ids.CANONICAL,address(new OldNativeFeeSchema()));oldSource.seal();
        NativeVersionAccess targetAccess=new NativeVersionAccess(); ProtocolPolicyFixture.bind(address(targetAccess));targetAccess.bind(Ids.VAULT,address(new NativeCanonicalVault()));
        ZZZCanonicalHandoff target=new ZZZCanonicalHandoff(address(targetAccess));
        vm.expectRevert(ZZZCanonicalHandoff.UnsupportedTransport.selector);target.prepareImport(address(oldSource));
        assertEq(target.incomingSource(),address(0));assertEq(target.phase(),0);
    }
}

/// TEST ONLY: fixed-pair component fixtures, not real market/feed qualification.
contract NativePairValueOracle {
    ZZZContributionPricing public immutable contributionPricing;
    constructor(address controller) { contributionPricing=new ZZZContributionPricing(controller,address(this)); }
    function price(address asset) external pure returns(uint256){return asset==address(0)?2000e18:1e18;}
    function tokenDecimals(address) external pure returns(uint8){return 18;}
    function value(address asset,uint256 amount) external pure returns(uint256){return amount*(asset==address(0)?2000:1);}
}
contract NativePairCompound {
    mapping(uint256=>mapping(address=>uint256))public compoundBalance;
    function set(address asset,uint256 amount)external{compoundBalance[1][asset]=amount;}
}
contract NativePairPrincipal {
    function portfolioAmounts(uint256)external pure returns(uint256,uint256){return(2 ether,3e18);}
}
contract NativeMigrationBudgetTest is Test {
    Position private p;
    ZZZMigrationBudget public migrationBudget;
    mapping(address=>uint256) public totalIdle;
    function group(uint256) external view returns(Position memory){return p;}
    function testFixedPairNAVKeepsActualIdleAndReleasedCompoundWithoutForeignAddOn() public {
        MockAccess ac=new MockAccess();ProtocolPolicyFixture.bind(address(ac));MockPools pools=new MockPools();
        MockToken zzz=new MockToken(18);NativePairCompound fees=new NativePairCompound();
        NativePairValueOracle oracle=new NativePairValueOracle(address(ac));
        ac.bind(Ids.POOLS,address(pools));ac.bind(Ids.FEES,address(fees));ac.bind(Ids.ORACLE,address(oracle));
        ac.bind(Ids.LIQUIDITY,address(new NativePairPrincipal()));
        PoolConfig memory c;c.key=PoolKey(address(0),address(zzz),3000,60,address(0));
        p.poolId=keccak256(abi.encode(c.key));p.lpTokenId=1;p.status=PositionStatus.Active;
        p.idle0=0.5 ether;p.idle1=7e18;pools.set(p.poolId,c);
        ZZZMigrationBudget budget=new ZZZMigrationBudget(address(ac));migrationBudget=budget;ac.bind(Ids.VAULT,address(this));
        (uint256 deployed,uint256 idle)=budget.nav(1);
        assertEq(deployed,4003e18);assertEq(idle,1007e18);
        fees.set(address(0),1 ether);fees.set(address(zzz),11e18);
        assertEq(budget.historicalCompoundValue(1),0);assertEq(oracle.contributionPricing().historicalValue(1),0);
        budget.recordComposition(1);
        assertEq(budget.historicalCompoundValue(1),0);assertEq(oracle.contributionPricing().historicalValue(1),0);
        // The ordinary Vault explicitly releases these existing pair reserves
        // into attributed idle. NAV then includes them exactly once.
        p.idle0+=fees.compoundBalance(1,address(0));p.idle1+=fees.compoundBalance(1,address(zzz));
        fees.set(address(0),0);fees.set(address(zzz),0);
        (uint256 afterLP,uint256 afterIdle)=budget.nav(1);
        assertEq(afterLP,deployed);assertEq(afterIdle,idle+2011e18);assertEq(afterLP+afterIdle,7021e18);
    }
    function testNativeIdleBackingReadsBalanceWithoutERC20Call() public {
        MockAccess ac=new MockAccess(); ProtocolPolicyFixture.bind(address(ac));MockPools pools=new MockPools();MockToken t=new MockToken(0);ac.bind(Ids.POOLS,address(pools));
        PoolConfig memory c;c.key=PoolKey(address(0),address(t),3000,60,address(0));p.poolId=keccak256(abi.encode(c.key));pools.set(p.poolId,c);
        ZZZMigrationBudget budget=new ZZZMigrationBudget(address(ac));migrationBudget=budget;ac.bind(Ids.VAULT,address(this));
        totalIdle[address(0)]=2;vm.deal(address(this),2);budget.assertIdle(1);
        vm.deal(address(this),1);vm.expectRevert();budget.assertIdle(1);
    }
}
