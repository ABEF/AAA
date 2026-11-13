// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReferenceExecutionContextTest} from "./ReferenceExecutionContext.t.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZRoyaltyFactory} from "../src/ZZZRoyaltyFactory.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Position,Ids} from "../src/libraries/ZZZTypes.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";

/// @notice TEST ONLY: new launch-amount and explicit gas-profile qualification.
/// Production contracts/defaults, prior test bodies and old evidence are untouched.
/// Local feeds price ETH at $1; real venues have controlled synthetic depth.
contract GasProfileQualificationTest is ReferenceExecutionContextTest {
    uint256 internal constant CONTRIBUTION_PROFILE_GAS = 20_000_000;
    uint256 internal constant MAINTENANCE_PROFILE_GAS = 24_000_000;
    address internal constant PROFILE_KEEPER = address(0xBEEF);

    struct ProfileCall {
        string label;
        address sender;
        address destination;
        uint256 value;
        bytes data;
        uint256 cap;
        uint16 paddingBps;
        uint256 nftId;
        uint256 bucket;
    }
    struct ContributionCheck {
        uint256 upperInput;
        uint256 price0;
        uint256 price1;
        uint256 beforeLP;
        uint256 beforeNAV;
        uint256 beforeShares;
        uint256 beforeSupply;
        Position old;
    }
    event ProfileUnsignedCall(string label,address sender,address destination,uint256 value,bytes data,
        uint256 gasCap,uint16 paddingBps,uint256 nftId,uint256 bucket,bytes32 preState);
    event ProfileStateExport(string label,string path,bytes32 deltaHash);
    event ProfileAmount(string label,address asset,uint256 amount,uint256 lowerUSD,uint256 upperUSD);
    event ProfileGas(string label,uint256 rawCallGas,uint256 paddedCallGas,uint256 gasCap);

    function _profileExport(ProfileCall memory c,bytes32 beforeState) internal {
        emit ProfileUnsignedCall(c.label,c.sender,c.destination,c.value,c.data,c.cap,c.paddingBps,c.nftId,c.bucket,beforeState);
        string memory root=vm.envOr("POPL_GAS_PROFILE_EXPORT_ROOT",string(""));
        if(bytes(root).length==0)return;
        string memory original=vm.envString("POPL_REFERENCE_EXPORT_PATH");
        string memory setup=string.concat(original,".setup.json");
        assertTrue(exportSetupHash!=bytes32(0));
        assertEq(keccak256(bytes(vm.readFile(setup))),exportSetupHash,"authenticate actual setup state before exporting delta");
        emit ReferenceExportBaseline(setup,exportSetupHash);
        emit ReferenceExportBlock(block.number,block.timestamp,block.chainid);
        _materializeExportGraph();
        if(address(maintenanceCompounder)!=address(0))_profileMaterialize(address(maintenanceCompounder));
        _profileMaterialize(address(nft.royaltyRewards()));_profileMaterialize(address(nft.claimRouter()));
        _profileMaterialize(address(nft.metadataRenderer()));_profileMaterialize(rewards.canonicalModule());
        _profileMaterialize(access.module(Ids.CANONICAL));_profileMaterialize(access.module(Ids.NFT_CANONICAL));
        _profileMaterialize(access.module(Ids.VAULT_CANONICAL));_profileMaterialize(access.module(Ids.FEES_CANONICAL));
        _profileMaterialize(access.module(Ids.BUYBACK));
        ZZZRoyaltyFactory factory=ZZZRoyaltyFactory(access.royaltyFactory());
        _profileMaterialize(factory.part0());_profileMaterialize(factory.part1());
        string memory path=string.concat(root,"/",c.label,".json");
        vm.dumpState(path);
        emit ProfileStateExport(c.label,path,keccak256(bytes(vm.readFile(path))));
    }
    function _profileMaterialize(address target_) internal {
        bytes memory runtime=target_.code;bytes32 hash=target_.codehash;
        assertGt(runtime.length,0);vm.etch(target_,runtime);assertEq(target_.codehash,hash);
        emit ReferenceExportCodeMaterialized(target_,hash,runtime.length);
    }

    function _profileCall(ProfileCall memory c) internal returns(uint256 used) {
        bytes32 beforeState=_entryAtomicState(nft.ownerOf(c.nftId),c.nftId);
        _profileExport(c,beforeState);
        vm.startPrank(c.sender);
        if(c.cap==CONTRIBUTION_PROFILE_GAS)_coolEntry();else _coldMaintenance();
        uint256 beforeGas=gasleft();
        (bool ok,bytes memory reason)=c.destination.call{value:c.value,gas:c.cap}(c.data);
        used=beforeGas-gasleft();vm.stopPrank();
        if(!ok)emit log_named_bytes(string.concat(c.label,".failure"),reason);
        assertTrue(ok,"requested explicit profile must execute the complete guarded operation");
        uint256 padded=used+Math.mulDiv(used,c.paddingBps,10000,Math.Rounding.Ceil);
        assertLe(padded,c.cap,"full requested margin fits the same explicit profile");
        emit ProfileGas(c.label,used,padded,c.cap);
        assertFalse(_execution().executionActive());_assertPrefunds();
    }

    function _attributedValue(uint256 bucket,uint256 p0,uint256 p1) internal view returns(uint256) {
        Position memory p=vault.group(bucket);
        return _actualMainValue(bucket,p0,p1)+Math.mulDiv(p.idle0,p0,1e18)+Math.mulDiv(p.idle1,p1,1e18);
    }
    function _contributionAtDollarFloor(address owner,uint256 id,address asset,uint256 dollars,bool grow,string memory label)
        internal returns(uint256 input) {
        (uint256 lower,uint256 upper,)=oracle.priceBounds(asset);
        input=Math.mulDiv(dollars,1e18,lower,Math.Rounding.Ceil);
        assertGe(Math.mulDiv(input,lower,1e18),dollars);
        assertLt(Math.mulDiv(input-1,lower,1e18),dollars,"immediately smaller raw amount is below the requested USD floor");
        ContributionCheck memory check;
        check.upperInput=Math.mulDiv(input,upper,1e18,Math.Rounding.Ceil);
        emit ProfileAmount(label,asset,input,Math.mulDiv(input,lower,1e18),check.upperInput);
        (check.price0,,)=oracle.priceBounds(address(0));(check.price1,,)=oracle.priceBounds(address(token));
        uint256 oldBucket=vault.nftBucket(id);check.old=vault.group(oldBucket);
        assertEq(fees.compoundBalance(oldBucket,address(0)),0,"launch NAV comparison has no pre-existing native compound");
        assertEq(fees.compoundBalance(oldBucket,address(token)),0,"launch NAV comparison has no pre-existing ZZZ compound");
        check.beforeLP=check.old.lpTokenId==0?0:_actualMainValue(oldBucket,check.price0,check.price1);
        check.beforeNAV=check.old.lpTokenId==0?0:_attributedValue(oldBucket,check.price0,check.price1);
        check.beforeShares=vault.sharesOf(id);check.beforeSupply=vault.bucketTotalShares(oldBucket);
        ZZZActivationEntry.Request memory req=ZZZActivationEntry.Request(id,target,asset,input,1,block.timestamp+100,grow);
        bytes32 fingerprint=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();
        if(asset!=address(0)){vm.prank(owner);token.approve(address(entry),input);}
        _profileBelowFloor(owner,req,fingerprint);
        ProfileCall memory call_;
        call_.label=label;call_.sender=owner;call_.destination=address(entry);call_.value=asset==address(0)?input:0;
        call_.data=abi.encodeCall(ZZZActivationEntry.executeReviewed,(req,uint16(300),fingerprint));
        call_.cap=CONTRIBUTION_PROFILE_GAS;call_.paddingBps=2000;call_.nftId=id;call_.bucket=oldBucket;
        _profileCall(call_);
        _assertProfileContribution(owner,id,grow,check);
    }
    function _profileBelowFloor(address owner,ZZZActivationEntry.Request memory req,bytes32 fingerprint) internal {
        // A larger gas cap must not let a one-unit-short contribution bypass
        // the actual $100 activation/$5 growth minimum or consume approvals.
        bytes32 atomicBefore=_entryAtomicState(owner,req.nftId);
        uint256 input=req.amountIn;req.amountIn=input-1;
        vm.prank(owner);
        (bool bad,bytes memory reason)=address(entry).call{value:req.sourceAsset==address(0)?input-1:0,gas:CONTRIBUTION_PROFILE_GAS}(
            abi.encodeCall(ZZZActivationEntry.executeReviewed,(req,uint16(300),fingerprint)));
        assertFalse(bad);assertEq(reason,abi.encodeWithSelector(ZZZModule.InvalidAmount.selector));
        assertEq(_entryAtomicState(owner,req.nftId),atomicBefore);
        req.amountIn=input;
    }
    function _assertProfileContribution(address owner,uint256 id,bool grow,ContributionCheck memory check) internal view {
        uint256 bucket=vault.nftBucket(id);Position memory afterPosition=vault.group(bucket);
        uint256 floor=check.upperInput-Math.mulDiv(check.upperInput,300,10000);
        assertGe(_actualMainValue(bucket,check.price0,check.price1)-check.beforeLP,floor,"actual marginal deployed LP still meets97%");
        assertEq(nft.ownerOf(id),owner);assertTrue(membership.eligible(id));
        assertEq(positions.ownerOf(afterPosition.lpTokenId),address(vault));
        assertEq(manager.secondaryId(afterPosition.lpTokenId),0);
        if(grow){
            assertEq(afterPosition.lpTokenId,check.old.lpTokenId);assertEq(afterPosition.centerX96,check.old.centerX96);
            assertEq(afterPosition.lastRebalance,check.old.lastRebalance);
            uint256 added=_attributedValue(bucket,check.price0,check.price1)-check.beforeNAV;
            assertEq(vault.sharesOf(id)-check.beforeShares,Math.mulDiv(check.beforeSupply,added,check.beforeNAV));
        }
        assertEq(vault.bucketTotalShares(bucket),vault.sharesOf(id));
        (uint256 treeWeight,,)=rewards.allocationTree(bucket);assertEq(treeWeight,vault.sharesOf(id));
        assertEq(token.allowance(owner,address(entry)),0);assertEq(token.allowance(address(entry),address(vault)),0);
        assertEq(address(entry).balance,0);assertEq(token.balanceOf(address(entry)),0);
    }
    function _launchProfile(address asset,string memory prefix) internal {
        _installProductionEntryGraph();address owner=address(0xA11CE);
        vm.deal(owner,10000 ether);token.mint(owner,10000 ether);uint256 id=_mint(owner);
        _contributionAtDollarFloor(owner,id,asset,100 ether,false,string.concat(prefix,"-activate100"));
        uint256 bucket=vault.nftBucket(id);uint256 main=vault.group(bucket).lpTokenId;
        (int24 low,int24 high)=manager.ticks(main);uint128 beforeL=positions.getPositionLiquidity(main);
        vm.warp(block.timestamp+17);
        _contributionAtDollarFloor(owner,id,asset,5 ether,true,string.concat(prefix,"-grow5"));
        assertGt(positions.getPositionLiquidity(main),beforeL);
        (int24 nextLow,int24 nextHigh)=manager.ticks(main);assertEq(nextLow,low);assertEq(nextHigh,high);
    }
    function testProfile20ETHExact100ActivationAnd5Growth() public { _launchProfile(address(0),"eth"); }
    function testProfile20ZZZExact100ActivationAnd5Growth() public { _launchProfile(address(token),"zzz"); }

    function _keeperProfileSetup(bool hybrid) internal returns(address owner,uint256 id,uint256 bucket) {
        (owner,id,bucket)=_installMaintenanceGraph(hybrid);
        access.setKeeper(PROFILE_KEEPER,true);vm.deal(PROFILE_KEEPER,1 ether);
    }
    function _keeperProfileCall(string memory label,uint256 id,uint256 bucket,address target_,bytes memory data)
        internal returns(uint256 used) {
        return _profileCall(ProfileCall(label,PROFILE_KEEPER,target_,0,data,MAINTENANCE_PROFILE_GAS,2500,id,bucket));
    }
    function testProfile24MainHarvestAndCompoundPreservePrincipalAndRewards() public {
        (address owner,uint256 id,uint256 bucket)=_keeperProfileSetup(false);
        _trade(core,targetKey,true,100 ether);
        Position memory beforePosition=vault.group(bucket);uint256 shares=vault.sharesOf(id);
        _keeperProfileCall("main-harvest",id,bucket,address(vault),abi.encodeCall(ZZZVault.collectFees,(bucket,block.timestamp+100)));
        assertEq(keccak256(abi.encode(vault.group(bucket))),keccak256(abi.encode(beforePosition)));
        uint256 reserve=fees.compoundBalance(bucket,address(0));assertGt(reserve,0);
        uint256 liabilities=rewards.liabilities(address(0));uint256 buyback=fees.buybackBalance(address(0));
        uint128 beforeL=positions.getPositionLiquidity(beforePosition.lpTokenId);
        vm.warp(uint256(beforePosition.lastRebalance)+3601);_freshMaintenanceFeeds();
        assertTrue(vault.migrationBudget().compoundReady(bucket));
        _keeperProfileCall("compound",id,bucket,address(maintenanceCompounder),
            abi.encodeCall(ZZZCompounder.compound,(bucket,uint128(1),block.timestamp+100)));
        Position memory afterPosition=vault.group(bucket);
        assertEq(afterPosition.lpTokenId,beforePosition.lpTokenId);assertEq(afterPosition.centerX96,beforePosition.centerX96);
        assertEq(afterPosition.lastRebalance,beforePosition.lastRebalance);assertEq(vault.sharesOf(id),shares);
        assertEq(vault.bucketTotalShares(bucket),shares);assertEq(nft.ownerOf(id),owner);
        assertGt(positions.getPositionLiquidity(afterPosition.lpTokenId),beforeL);
        assertGe(rewards.liabilities(address(0)),liabilities);assertGe(fees.buybackBalance(address(0)),buyback);
        assertLt(fees.compoundBalance(bucket,address(0)),reserve);
    }
    function testProfile24OrdinarySingleReplacementKeepsTimingAndShareRights() public {
        (address owner,uint256 id,uint256 bucket)=_keeperProfileSetup(false);
        Position memory beforePosition=vault.group(bucket);uint256 shares=vault.sharesOf(id);
        _prepareOrdinaryRebalance(bucket);
        _keeperProfileCall("single-rebalance",id,bucket,address(vault),
            abi.encodeCall(ZZZVault.rebalance,(bucket,uint128(1),block.timestamp+100)));
        Position memory afterPosition=vault.group(bucket);assertTrue(afterPosition.lpTokenId!=beforePosition.lpTokenId);
        assertEq(positions.getPositionLiquidity(beforePosition.lpTokenId),0);
        assertEq(positions.ownerOf(afterPosition.lpTokenId),address(vault));assertGt(positions.getPositionLiquidity(afterPosition.lpTokenId),0);
        assertEq(afterPosition.lastRebalance,block.timestamp);assertEq(manager.secondaryId(afterPosition.lpTokenId),0);
        assertEq(vault.sharesOf(id),shares);assertEq(vault.bucketTotalShares(bucket),shares);assertEq(nft.ownerOf(id),owner);
    }
    function testProfile24HybridOpenHarvestAndTwoLegReplacementKeepsBothLegs() public {
        (address owner,uint256 id,uint256 bucket)=_keeperProfileSetup(true);uint256 shares=vault.sharesOf(id);
        _prepareOrdinaryRebalance(bucket);
        _keeperProfileCall("hybrid-open",id,bucket,address(vault),
            abi.encodeCall(ZZZVault.rebalance,(bucket,uint128(1),block.timestamp+100)));
        uint256 main=vault.group(bucket).lpTokenId;uint256 residual=manager.secondaryId(main);
        assertGt(residual,0);assertEq(manager.activeSecondaryCount(),1);assertEq(positions.ownerOf(residual),address(vault));
        uint160 mixed=uint160(uint256(Q96)*86/100);
        _tradeToMaintenancePrice(core,targetKey,mixed);_tradeToMaintenancePrice(core,referenceKey,mixed);
        _tradeToMaintenancePrice(independentCore,independentKey,mixed);
        uint128 mainL=positions.getPositionLiquidity(main);uint128 residualL=positions.getPositionLiquidity(residual);
        _keeperProfileCall("hybrid-harvest",id,bucket,address(vault),
            abi.encodeCall(ZZZVault.collectFees,(bucket,block.timestamp+100)));
        assertEq(positions.getPositionLiquidity(main),mainL);assertEq(positions.getPositionLiquidity(residual),residualL);
        _prepareOrdinaryRebalanceAt(bucket,uint160(uint256(Q96)*69/100));
        _keeperProfileCall("hybrid-replace",id,bucket,address(vault),
            abi.encodeCall(ZZZVault.rebalance,(bucket,uint128(1),block.timestamp+100)));
        uint256 nextMain=vault.group(bucket).lpTokenId;uint256 nextResidual=manager.secondaryId(nextMain);
        assertTrue(nextMain!=main);assertTrue(nextResidual!=residual);assertGt(nextResidual,0);
        assertEq(positions.getPositionLiquidity(main),0);assertEq(positions.getPositionLiquidity(residual),0);
        assertEq(manager.secondaryId(main),0);assertEq(manager.activeSecondaryCount(),1);
        assertEq(positions.ownerOf(nextMain),address(vault));assertEq(positions.ownerOf(nextResidual),address(vault));
        assertGt(positions.getPositionLiquidity(nextMain),0);assertGt(positions.getPositionLiquidity(nextResidual),0);
        assertEq(vault.sharesOf(id),shares);assertEq(vault.bucketTotalShares(bucket),shares);assertEq(nft.ownerOf(id),owner);
    }
}
