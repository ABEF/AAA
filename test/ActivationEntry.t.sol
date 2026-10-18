// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {ZZZActivationEntry, IActivationV3Router} from "../src/ZZZActivationEntry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {Ids, PoolConfig, PoolKey} from "../src/libraries/ZZZTypes.sol";
import {ExactToken} from "../src/libraries/ExactToken.sol";
import {MockAccess, MockToken, TaxToken, BoundDummy} from "./mocks/Mocks.sol";

// TEST ONLY: conversion and marked LP values below are deterministic mocks.
// Actual Registry/Vault integration and mainnet-fork evidence are separate tests.
contract EntryNFTFixture is ERC721 {
    constructor() ERC721("Entry fixture", "EF") {}
    function mint(address owner, uint256 id) external { _mint(owner, id); }
}
contract EntryOracleFixture {
    bool public fail;
    function setFail(bool value_) external { fail = value_; }
    function tokenDecimals(address token) external view returns (uint8) { return IERC20Metadata(token).decimals(); }
    function price(address) external view returns (uint256) { require(!fail); return 1e18; }
    function value(address token, uint256 amount) external view returns (uint256) {
        require(!fail); return amount * 1e18 / 10 ** IERC20Metadata(token).decimals();
    }
}
contract EntryWrappedFixture is ERC20 {
    bool public broken;
    constructor() ERC20("Entry wrapped ETH", "EWETH") {}
    function mint(address owner, uint256 amount) external { _mint(owner, amount); }
    function setBroken(bool value_) external { broken = value_; }
    function deposit() external payable { if (!broken) _mint(msg.sender, msg.value); }
}
contract EntryCallbackToken is MockToken {
    address public callbackTarget;
    bytes public callbackData;
    address public triggerFrom;
    address public triggerTo;
    bool public requireFailure;
    bool public attempted;
    address public approvalProbe;
    address public approvalOwner;
    address public approvalSpender;
    address public resetProbe;
    address public resetOwner;
    address public resetSpender;
    address public resetTarget;
    bytes public resetData;
    bool public resetRequiresFailure;
    bool public resetAttempted;
    bytes4 public resetError;
    constructor() MockToken(18) {}
    function configure(address target, bytes calldata data, address from, address to, bool expectFailure) external {
        callbackTarget = target; callbackData = data; triggerFrom = from; triggerTo = to; requireFailure = expectFailure;
    }
    function configureApproval(address probe, address from, address spender) external {
        approvalProbe=probe;approvalOwner=from;approvalSpender=spender;
    }
    function configureReset(address probe, address from, address spender, address target, bytes calldata data, bool expectFailure) external {
        resetProbe=probe;resetOwner=from;resetSpender=spender;resetTarget=target;resetData=data;resetRequiresFailure=expectFailure;
    }
    function approve(address spender, uint256 amount) public override returns (bool) {
        bool result=super.approve(spender,amount);
        if(msg.sender==approvalOwner && spender==approvalSpender && amount!=0 && approvalProbe!=address(0)) {
            EntryVaultFixture(approvalProbe).inspectApprovalContext();
        }
        if(msg.sender==resetOwner && spender==resetSpender && amount==0 && resetProbe!=address(0)) {
            EntryVaultFixture(resetProbe).inspectResetContext();
            resetAttempted=true;
            (bool ok, bytes memory callbackResult)=resetTarget.call(resetData);
            require(ok != resetRequiresFailure,"unexpected reset callback result");
            if(callbackResult.length>=4)resetError=bytes4(callbackResult);
        }
        return result;
    }
    function _update(address from, address to, uint256 amount) internal override {
        super._update(from, to, amount);
        if (from == triggerFrom && to == triggerTo && callbackTarget != address(0)) {
            attempted = true;
            (bool ok,) = callbackTarget.call(callbackData);
            require(ok != requireFailure, "unexpected callback result");
        }
    }
}
contract EntryFactoryFixture {
    address public selected;
    function set(address value_) external { selected = value_; }
    function getPool(address, address, uint24) external view returns (address) { return selected; }
}
contract EntryPoolFixture {
    address public immutable factory;
    address public immutable token0;
    address public immutable token1;
    uint24 public constant fee = 500;
    constructor(address factory_, address a, address b) {
        factory = factory_; token0 = a < b ? a : b; token1 = a < b ? b : a;
    }
}
contract EntryRouterFixture is IActivationV3Router {
    address public immutable factory;
    uint256 public outputBps = 9950;
    bool public partialConsumption;
    bool public lie;
    constructor(address f) { factory = f; }
    function configure(uint256 bps, bool partial_, bool lie_) external { outputBps = bps; partialConsumption = partial_; lie = lie_; }
    function exactInputSingle(ExactInputSingleParams calldata p) external payable returns (uint256 amount) {
        require(msg.value == 0 && p.sqrtPriceLimitX96 == 0);
        IERC20(p.tokenIn).transferFrom(msg.sender, address(this), partialConsumption ? p.amountIn - 1 : p.amountIn);
        amount = p.amountIn * outputBps / 10000;
        require(amount >= p.amountOutMinimum);
        IERC20(p.tokenOut).transfer(p.recipient, amount);
        if (lie) amount++;
    }
}
contract EntryRegistryFixture {
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    PoolConfig private config;
    bool public native;
    constructor(address controller) {
        activationAssets = new ZZZActivationAssets(controller, address(this));
        activationEntry = new ZZZActivationEntry(controller, address(this), address(activationAssets));
    }
    function configure(address a, address b, bool native_) external {
        native = native_;
        config = PoolConfig(PoolKey(a,b,0,60,address(0)),true,true,1000,100,100,100,600,1e18,1e30);
    }
    function get(bytes32) external view returns (PoolConfig memory c) {
        c = config; if (native) c.key.currency0 = address(0);
    }
    function accounting(bytes32) external view returns (PoolConfig memory) { return config; }
    function admit(address token) external { activationAssets.admitPoolAsset(token); }
    function contributionValue(bytes32 pool, uint256 a0, uint256 a1) external view returns (uint256) {
        return activationEntry.sourceValue(pool, a0, a1);
    }
}
contract EntryVaultFixture {
    EntryRegistryFixture public immutable registry;
    ZZZActivationEntry public immutable entry;
    uint256 public gross;
    uint256 public deployed;
    uint256 public amount0;
    uint256 public amount1;
    uint256 public lastId;
    bool public increased;
    uint256 public lossBps = 40;
    bool public wrongHash;
    bool public wrongAmounts;
    bool public partialConsumption;
    uint256 public approvalObservedValue;
    bool public approvalObserved;
    bool public resetObserved;
    bytes32 public lastCallHash;
    constructor(EntryRegistryFixture pools) { registry = pools; entry = pools.activationEntry(); }
    function inspectApprovalContext() external {
        approvalObserved=true;
        approvalObservedValue=registry.contributionValue(bytes32(uint256(42)),0,100e18);
        require(approvalObservedValue==0,"source context leaked into approval callback");
    }
    function inspectResetContext() external {
        // The operation must already have completed. Use its exact arguments
        // and hash, so a stale armed context cannot pass through a mismatch.
        require(lastId!=0 && deployed!=0,"Vault has not completed");
        require(registry.contributionValue(bytes32(uint256(42)),amount0,amount1)==0,"context survived reset");
        (bool ok, bytes memory result)=address(entry).staticcall(abi.encodeCall(entry.validateOwner,(lastId,lastCallHash)));
        require(!ok && result.length>=4 && bytes4(result)==bytes4(keccak256("Unauthorized()")),"stale owner authorization");
        resetObserved=true;
    }
    function configure(uint256 loss, bool badHash, bool badAmounts, bool partial_) external {
        lossBps = loss; wrongHash = badHash; wrongAmounts = badAmounts; partialConsumption = partial_;
    }
    function activate(uint256 id, bytes32 pool, uint256 a0, uint256 a1, uint128, uint256) external {
        _join(id,pool,a0,a1,false);
    }
    function increase(uint256 id, uint256 a0, uint256 a1, uint128, uint256) external { _join(id,bytes32(uint256(42)),a0,a1,true); }
    function _join(uint256 id, bytes32 pool, uint256 a0, uint256 a1, bool add) private {
        require(msg.sender == address(entry));
        entry.validateOwner(id, wrongHash ? bytes32(uint256(1)) : keccak256(msg.data));
        gross = registry.contributionValue(pool, wrongAmounts ? a0 + 1 : a0, a1);
        require(gross != 0 && (add || gross >= 100e18));
        PoolConfig memory c = registry.accounting(pool);
        ExactToken.pull(c.key.currency0, msg.sender, partialConsumption && a0 > 0 ? a0 - 1 : a0);
        ExactToken.pull(c.key.currency1, msg.sender, partialConsumption && a1 > 0 ? a1 - 1 : a1);
        deployed = (a0 + a1) * (10000-lossBps) / 10000;
        require(deployed >= gross - gross/100, "end-to-end loss exceeds one percent");
        amount0 = a0; amount1 = a1; lastId = id; increased = add; lastCallHash = keccak256(msg.data);
    }
}

contract ActivationEntryTest is Test {
    MockAccess private access;
    EntryOracleFixture private oracle;
    EntryRegistryFixture private registry;
    EntryVaultFixture private vault;
    ZZZActivationAssets private assets;
    ZZZActivationEntry private entry;
    EntryNFTFixture private nft;
    EntryCallbackToken private source;
    EntryWrappedFixture private wrapped;
    EntryCallbackToken private second;
    EntryRouterFixture private router;
    EntryFactoryFixture private factory;
    EntryPoolFixture private pool;
    bytes32 private routeId;
    address private constant ALICE = address(0xA11CE);
    address private constant ATTACKER = address(0xBAD);
    bytes32 private constant POOL = bytes32(uint256(42));
    bytes32 private constant REVIEW = keccak256("internal entry route fixture, not independent audit");

    function setUp() public {
        vm.warp(1000000);
        access = new MockAccess(); oracle = new EntryOracleFixture();
        access.bind(Ids.ORACLE,address(oracle));
        source = new EntryCallbackToken(); wrapped = new EntryWrappedFixture(); second = new EntryCallbackToken();
        nft = new EntryNFTFixture(); nft.mint(ALICE,1); access.bind(Ids.NFT,address(nft));
        registry = new EntryRegistryFixture(address(access)); entry = registry.activationEntry(); assets = registry.activationAssets();
        registry.configure(address(wrapped),address(second),false); access.bind(Ids.POOLS,address(registry));
        vault = new EntryVaultFixture(registry); access.bind(Ids.VAULT,address(vault));
        registry.admit(address(source)); registry.admit(address(wrapped)); registry.admit(address(second));
        factory = new EntryFactoryFixture(); router = new EntryRouterFixture(address(factory));
        pool = new EntryPoolFixture(address(factory),address(source),address(wrapped)); factory.set(address(pool));
        routeId = entry.addRoute(_policy(address(source),address(wrapped)));
        source.mint(ALICE,10000e18); wrapped.mint(ALICE,10000e18); second.mint(ALICE,10000e18);
        wrapped.mint(address(router),10000e18); second.mint(address(router),10000e18);
        vm.startPrank(ALICE);
        source.approve(address(entry),10000e18); wrapped.approve(address(entry),10000e18); second.approve(address(entry),10000e18);
        vm.stopPrank(); vm.deal(ALICE,1000 ether); access.seal();
    }
    function _policy(address a,address b) private view returns (ZZZActivationEntry.RoutePolicy memory) {
        return ZZZActivationEntry.RoutePolicy(a,b,address(router),address(factory),address(pool),500,
            address(router).codehash,address(factory).codehash,address(pool).codehash,a.codehash,b.codehash,REVIEW);
    }
    function _request() private view returns (ZZZActivationEntry.Request memory r) {
        r = ZZZActivationEntry.Request(1,POOL,address(source),100e18,routeId,99e18,1,block.timestamp+100,false);
    }
    function _execute(ZZZActivationEntry.Request memory r) private { vm.prank(ALICE); entry.execute(r); }
    function _assertClean() private view {
        assertEq(source.balanceOf(address(entry)),0); assertEq(wrapped.balanceOf(address(entry)),0);
        assertEq(source.allowance(address(entry),address(router)),0); assertEq(wrapped.allowance(address(entry),address(vault)),0);
        assertEq(registry.contributionValue(POOL,0,0),0);
    }
    function testRoutedOriginalGrossBoundAndBothLegsUseOneBudget() public {
        _execute(_request()); assertEq(vault.gross(),100e18); assertEq(vault.amount0(),99.5e18);
        assertEq(vault.deployed(),99.102e18); assertEq(nft.ownerOf(1),ALICE); assertEq(nft.getApproved(1),address(0)); _assertClean();
    }
    function testTwoIndividuallySmallLossesCannotCompoundBeyondOnePercent() public {
        router.configure(9920,false,false); vault.configure(30,false,false,false);
        vm.expectRevert(); _execute(_request()); assertEq(source.balanceOf(ALICE),10000e18); assertEq(vault.lastId(),0); _assertClean();
    }
    function testDirectPairInputAndTopUpKeepOwnerAndSourceValue() public {
        ZZZActivationEntry.Request memory r = _request(); r.sourceAsset=address(second);r.routeId=0;r.minimumOut=0;
        _execute(r); assertEq(vault.amount1(),100e18); assertEq(vault.gross(),100e18);
        r.increase=true;r.amountIn=10e18;_execute(r);assertTrue(vault.increased());assertEq(vault.gross(),10e18);_assertClean();
    }
    function testNativeWrapUsesOnlyActualInputAndLeavesNoETHCustody() public {
        registry.configure(address(wrapped),address(second),true);
        ZZZActivationEntry.Request memory r=_request();r.sourceAsset=address(0);r.routeId=0;r.minimumOut=0;
        vm.prank(ALICE);entry.execute{value:100 ether}(r);assertEq(vault.gross(),100e18);assertEq(address(entry).balance,0);_assertClean();
    }
    function testPrefundsCannotBecomeContributionOrRouteOutput() public {
        source.mint(address(entry),17e18);wrapped.mint(address(entry),23e18);vm.deal(address(entry),5 ether);
        _execute(_request());assertEq(vault.gross(),100e18);assertEq(source.balanceOf(address(entry)),17e18);
        assertEq(wrapped.balanceOf(address(entry)),23e18);assertEq(address(entry).balance,5 ether);
    }
    function testAttackerOrNFTApprovalCannotActivateAnotherOwnersNFT() public {
        vm.prank(ALICE);nft.approve(ATTACKER,1);
        vm.prank(ATTACKER);vm.expectRevert();entry.execute(_request());assertEq(source.balanceOf(ALICE),10000e18);
    }
    function testContextCannotBeReadOrForgedByUntrustedCaller() public {
        vm.expectRevert();entry.validateOwner(1,0);vm.expectRevert();entry.sourceValue(POOL,1,0);
        vm.prank(address(vault));vm.expectRevert();entry.validateOwner(1,0);assertEq(registry.contributionValue(POOL,1,0),0);
    }
    function testActiveContextWrongVaultCallHashRevertsAtomically() public {
        vault.configure(0,true,false,false);vm.expectRevert();_execute(_request());assertEq(source.balanceOf(ALICE),10000e18);_assertClean();
    }
    function testActiveContextMismatchNeverFallsBackToPairValue() public {
        vault.configure(0,false,true,false);vm.expectRevert();_execute(_request());assertEq(source.balanceOf(ALICE),10000e18);_assertClean();
    }
    function testRoutePartialConsumptionCannotUsePrefunds() public {
        source.mint(address(entry),50e18);router.configure(9950,true,false);
        vm.expectRevert();_execute(_request());assertEq(source.balanceOf(address(entry)),50e18);assertEq(vault.lastId(),0);
    }
    function testFabricatedRouterOutputCannotBecomeGrossOrLP() public {
        router.configure(9950,false,true);vm.expectRevert();_execute(_request());assertEq(vault.lastId(),0);_assertClean();
    }
    function testVaultMustConsumeExactOutputAndApprovalIsNeverLeftLive() public {
        vault.configure(0,false,false,true);vm.expectRevert();_execute(_request());assertEq(vault.lastId(),0);_assertClean();
    }
    function testSourceCallbackCannotReenterAtomicEntry() public {
        ZZZActivationEntry.Request memory r=_request();
        source.configure(address(entry),abi.encodeCall(entry.execute,(r)),ALICE,address(entry),true);
        _execute(r);assertTrue(source.attempted());_assertClean();
    }
    function testSourceCallbackNFTTransferRollsBackEverything() public {
        vm.prank(ALICE);nft.approve(address(source),1);
        source.configure(address(nft),abi.encodeCall(nft.transferFrom,(ALICE,ATTACKER,1)),ALICE,address(entry),false);
        vm.expectRevert();_execute(_request());assertEq(nft.ownerOf(1),ALICE);assertEq(vault.lastId(),0);_assertClean();
    }
    function testFinalVaultPullCallbackNFTTransferRollsBackEverything() public {
        ZZZActivationEntry.Request memory r=_request();r.sourceAsset=address(second);r.routeId=0;r.minimumOut=0;
        vm.prank(ALICE);nft.approve(address(second),1);
        second.configure(address(nft),abi.encodeCall(nft.transferFrom,(ALICE,ATTACKER,1)),address(entry),address(vault),false);
        vm.expectRevert();_execute(r);assertEq(nft.ownerOf(1),ALICE);assertEq(vault.lastId(),0);assertEq(second.balanceOf(ALICE),10000e18);
    }
    function testApprovalCallbackSeesInactiveContextBeforeAnyVaultMutation() public {
        ZZZActivationEntry.Request memory r=_request();r.sourceAsset=address(second);r.routeId=0;r.minimumOut=0;
        second.configureApproval(address(vault),address(entry),address(vault));
        _execute(r);assertTrue(vault.approvalObserved());assertEq(vault.approvalObservedValue(),0);
        assertEq(vault.gross(),100e18);assertEq(second.allowance(address(entry),address(vault)),0);
    }
    function testFinalAllowanceResetClearsContextAndStillRejectsReentry() public {
        ZZZActivationEntry.Request memory r=_request();r.sourceAsset=address(second);r.routeId=0;r.minimumOut=0;
        second.configureReset(address(vault),address(entry),address(vault),address(entry),abi.encodeCall(entry.execute,(r)),true);
        _execute(r);
        assertTrue(vault.resetObserved());assertTrue(second.resetAttempted());
        assertEq(second.resetError(),bytes4(keccak256("ReentrancyGuardReentrantCall()")));
        assertEq(vault.lastId(),1);assertEq(vault.gross(),100e18);assertEq(vault.deployed(),99.6e18);
        assertEq(second.balanceOf(address(vault)),100e18);assertEq(second.balanceOf(address(entry)),0);
        assertEq(second.allowance(address(entry),address(vault)),0);assertEq(nft.ownerOf(1),ALICE);_assertClean();
    }
    function testFinalAllowanceResetOwnershipChangeRollsBackCompletedVaultOperation() public {
        ZZZActivationEntry.Request memory r=_request();r.sourceAsset=address(second);r.routeId=0;r.minimumOut=0;
        vm.prank(ALICE);nft.approve(address(second),1);
        bytes memory transfer=abi.encodeCall(nft.transferFrom,(ALICE,ATTACKER,1));
        second.configureReset(address(vault),address(entry),address(vault),address(nft),transfer,false);
        vm.expectCall(address(vault),abi.encodeCall(vault.inspectResetContext,()));
        vm.expectCall(address(nft),transfer);
        vm.expectRevert(bytes4(keccak256("InvalidState()")));_execute(r);
        assertEq(nft.ownerOf(1),ALICE);assertEq(nft.getApproved(1),address(second));
        assertEq(vault.lastId(),0);assertEq(vault.gross(),0);assertEq(vault.deployed(),0);assertFalse(vault.resetObserved());
        assertEq(second.balanceOf(ALICE),10000e18);assertEq(second.balanceOf(address(vault)),0);
        assertEq(second.balanceOf(address(entry)),0);assertEq(second.allowance(address(entry),address(vault)),0);
        assertEq(second.allowance(ALICE,address(entry)),10000e18);_assertClean();
    }
    function testTaxedOriginalInputCannotBeCreditedAsFullSource() public {
        TaxToken taxed=new TaxToken();taxed.mint(ALICE,1000e18);registry.admit(address(taxed));
        registry.configure(address(taxed),address(second),false);
        vm.prank(ALICE);taxed.approve(address(entry),100e18);
        ZZZActivationEntry.Request memory r=_request();r.sourceAsset=address(taxed);r.routeId=0;r.minimumOut=0;
        vm.expectRevert();_execute(r);assertEq(taxed.balanceOf(ALICE),1000e18);assertEq(taxed.balanceOf(address(entry)),0);
    }
    function testDisabledOriginalSourceDoesNotPullOrUseIntermediatePolicy() public {
        assets.setAsset(address(source),false,bytes32(0),REVIEW);vm.expectRevert();_execute(_request());_assertClean();
        assets.setAsset(address(source),true,address(source).codehash,REVIEW);
        assets.setAsset(address(wrapped),false,bytes32(0),REVIEW);_execute(_request());assertEq(vault.gross(),100e18);
    }
    function testStaleOrUnavailableOriginalPriceRollsBackCustody() public {
        oracle.setFail(true);vm.expectRevert();_execute(_request());assertEq(source.balanceOf(ALICE),10000e18);_assertClean();
    }
    function testBrokenWrapperOrWrongNativeAmountRollsBack() public {
        registry.configure(address(wrapped),address(second),true);ZZZActivationEntry.Request memory r=_request();r.sourceAsset=address(0);r.routeId=0;r.minimumOut=0;
        vm.prank(ALICE);vm.expectRevert();entry.execute{value:99 ether}(r);
        wrapped.setBroken(true);vm.prank(ALICE);vm.expectRevert();entry.execute{value:100 ether}(r);assertEq(ALICE.balance,1000 ether);_assertClean();
    }
    function testUnreviewedRouteMalformedRouteAndNonpairOutputRejected() public {
        ZZZActivationEntry.Request memory r=_request();r.routeId=bytes32(uint256(123));vm.expectRevert();_execute(r);
        ZZZActivationEntry.RoutePolicy memory p=_policy(address(source),address(wrapped));p.poolCodeHash=bytes32(uint256(1));vm.expectRevert();entry.addRoute(p);
        p=_policy(address(source),address(wrapped));p.reviewHash=0;vm.expectRevert();entry.addRoute(p);
        r=_request();r.routeId=0;r.minimumOut=0;vm.expectRevert();_execute(r);
    }
    function testRoutesAreImmutableAndDisableIgnoresBrokenDependency() public {
        ZZZActivationEntry.RoutePolicy memory p=entry.route(routeId);vm.expectRevert();entry.addRoute(p);
        vm.etch(address(router),hex"fe");entry.setRouteEnabled(routeId,false);assertFalse(entry.routeEnabled(routeId));
        assertEq(entry.route(routeId).reviewHash,REVIEW);vm.expectRevert();entry.setRouteEnabled(routeId,true);vm.expectRevert();_execute(_request());
    }
    function testOnlyGovernanceCanAdmitOrToggleRoutes() public {
        vm.startPrank(ATTACKER);vm.expectRevert();entry.addRoute(_policy(address(source),address(wrapped)));
        vm.expectRevert();entry.setRouteEnabled(routeId,false);vm.stopPrank();
    }
    function testPostSealRouteAdmissionExecutesImmediatelyThroughGovernance() public {
        address[] memory auth=new address[](1);auth[0]=address(this);
        ZZZAccessController governed=new ZZZAccessController(0,auth,auth,address(0xBEEF),address(0x600D));
        EntryRegistryFixture childFactory=new EntryRegistryFixture(address(governed));
        ZZZActivationEntry governedEntry=childFactory.activationEntry();
        bytes32[16] memory ids=[Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.FEES,
            Ids.STRATEGY,Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.BRIDGE,Ids.RECEIVER,Ids.ORACLE,Ids.POOLS,Ids.ROUTES,Ids.TRANSPORT];
        for(uint256 i;i<ids.length;++i)governed.bind(ids[i],address(new BoundDummy(address(governed))));
        CanonicalFixture.bind(address(governed));
        governed.seal();ZZZActivationEntry.RoutePolicy memory policy=_policy(address(source),address(wrapped));
        vm.expectRevert();governedEntry.addRoute(policy);
        bytes memory payload=abi.encodeCall(governedEntry.addRoute,(policy));bytes32 salt=keccak256("entry route governance");
        governed.schedule(address(governedEntry),0,payload,bytes32(0),salt,0);

        governed.execute(address(governedEntry),0,payload,bytes32(0),salt);
        assertTrue(governedEntry.routeEnabled(keccak256(abi.encode(policy))));
    }
    function testPauseUnsealedAndNoncanonicalRegistryFailClosed() public {
        MockAccess unsealed=new MockAccess();EntryRegistryFixture unsealedFactory=new EntryRegistryFixture(address(unsealed));
        ZZZActivationEntry unsealedEntry=unsealedFactory.activationEntry();
        ZZZActivationEntry.Request memory request=_request();vm.prank(ALICE);vm.expectRevert(bytes4(keccak256("NotReady()")));
        unsealedEntry.execute(request);
        access.setPaused(true);vm.expectRevert();_execute(_request());access.setPaused(false);
        access.bind(Ids.POOLS,ATTACKER);vm.expectRevert();_execute(_request());assertEq(source.balanceOf(ALICE),10000e18);
    }
    function testExpiredBoundsMinimumAndUnexpectedNativeRejected() public {
        ZZZActivationEntry.Request memory r=_request();r.deadline=block.timestamp-1;vm.expectRevert();_execute(r);
        r=_request();r.deadline=block.timestamp+601;vm.expectRevert();_execute(r);
        r=_request();r.amountIn=99e18;vm.expectRevert();_execute(r);
        r=_request();vm.prank(ALICE);vm.expectRevert();entry.execute{value:1}(r);_assertClean();
    }
    function testRejectsPlainETHArbitraryCallsAndThirdPartyConstructor() public {
        (bool ok,)=address(entry).call{value:1}("");assertFalse(ok);
        (ok,)=address(entry).call(abi.encodeWithSignature("execute(address,bytes)",ATTACKER,bytes("")));assertFalse(ok);
        vm.expectRevert();new ZZZActivationEntry(address(access),address(registry),address(assets));
    }
    function testFuzzSingleBudgetCannotBeResetAfterConversion(uint16 routeLoss,uint16 lpLoss) public {
        uint256 routeLossBps=bound(routeLoss,0,99);uint256 lpLossBps=bound(lpLoss,0,99);
        router.configure(10000-routeLossBps,false,false);vault.configure(lpLossBps,false,false,false);
        uint256 output=100e18*(10000-routeLossBps)/10000;uint256 deployed=output*(10000-lpLossBps)/10000;
        if(deployed<99e18)vm.expectRevert();_execute(_request());
        if(deployed>=99e18){assertEq(vault.gross(),100e18);assertEq(vault.deployed(),deployed);_assertClean();}
        else {assertEq(source.balanceOf(ALICE),10000e18);assertEq(vault.lastId(),0);}
    }
}
