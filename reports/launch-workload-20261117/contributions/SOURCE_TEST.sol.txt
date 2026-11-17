// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {GasProfileQualificationTest} from "./GasProfileQualification.t.sol";
import {ZZZSeaDropMint} from "../src/ZZZSeaDropMint.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {IZZZSeaDrop,AllowListData} from "../src/interfaces/IZZZSeaDrop.sol";
import {VerifiedSeaDropV1} from "./fixtures/VerifiedSeaDropV1.sol";
import {MockToken} from "./mocks/Mocks.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";

/// @dev TEST ONLY: a conventional exact-transfer currency while healthy; the
/// deliberate balance-read fault consumes the isolated forwarded allowance.
contract LaunchCapacityCurrency is MockToken {
    address public failingReader;
    constructor() MockToken(6) {}
    function failFor(address reader) external { failingReader=reader; }
    function balanceOf(address owner) public view override returns(uint256) {
        if(msg.sender==failingReader) assembly("memory-safe"){invalid()}
        return super.balanceOf(owner);
    }
}

/// @notice New launch-workload measurements, not re-execution of parent tests.
/// Real PoPL Entry/Vault/royalty4/LP1 and v4 core/periphery; controlled access,
/// admission, dual prices, Permit2 and VRF. Actual pinned SeaDrop runtime mints.
/// Cold CALL deltas exclude intrinsic/calldata gas and transaction refunds.
contract LaunchContributionCapacity20261117Test is GasProfileQualificationTest {
    address internal constant INCUMBENT=address(0xA11CE);
    address internal constant NEWCOMER=address(0xB0B);
    address internal constant DROP_FEE=address(0xFEED);
    LaunchCapacityCurrency[16] internal currencies;
    ZZZRoyaltyRewards internal royalty;
    IZZZSeaDrop internal drop;
    ZZZSeaDropMint internal mintHelper;
    uint256 internal oldId;
    uint256 internal newId;
    bool internal openingPendingCase;
    bool internal launchFixtureReady;
    event LaunchGas(string action,uint256 faultCount,bool success20M,uint256 used20M,
        bool full20PercentFits,uint256 successfulDiagnosticGas,uint256 paddedDiagnosticGas);

    function _launchSetup(bool pending) internal {
        _installProductionEntryGraph();
        access.beginBootstrap();
        drop=IZZZSeaDrop(VerifiedSeaDropV1.install(vm));
        mintHelper=new ZZZSeaDropMint(address(access),address(nft),address(drop),address(drop).codehash);
        nft.setSeaDropMint(address(mintHelper));
        ZZZSeaDropMint.MintConfig memory c;
        c.publicWalletLimit=1000;c.maxBatch=10;c.feeBps=1000;c.feeRecipient=DROP_FEE;
        c.teamStart=uint48(block.timestamp);c.teamEnd=c.teamStart+1;
        c.allowlistStart=c.teamEnd+1;c.allowlistEnd=c.allowlistStart+1;
        c.publicStart=c.allowlistEnd+1;c.publicEnd=c.publicStart+1000;
        c.allowedPayersHash=keccak256(abi.encode(new address[](0)));
        mintHelper.configure(c,uint128(0.05 ether),REVIEW);
        nft.setMintEnd(c.publicEnd);
        nft.updatePublicDrop(address(drop),mintHelper.expectedPublicDrop());
        nft.updateAllowList(address(drop),AllowListData(bytes32(0),new string[](0),"ipfs://TEST-ONLY/"));
        nft.updateCreatorPayoutAddress(address(drop),ZZZProtocolPolicy(access.protocolPolicy()).salePolicy().recipient);
        nft.updateAllowedFeeRecipient(address(drop),DROP_FEE,true);
        royalty=nft.royaltyRewards();
        for(uint256 i;i<16;++i){currencies[i]=new LaunchCapacityCurrency();nft.addRoyaltyAsset(address(currencies[i]));}
        assertEq(royalty.assetCapacity(),16);assertEq(royalty.assetCount(),17);
        assertEq(ZZZProtocolPolicy(access.protocolPolicy()).royaltySyncGas(),1_000_000);
        access.seal();vm.warp(c.publicStart);
        ethFirst.set(1e8,block.timestamp,block.timestamp);ethSecond.set(1e8,block.timestamp,block.timestamp);
        vm.deal(INCUMBENT,10_000 ether);vm.deal(NEWCOMER,10_000 ether);
        token.mint(INCUMBENT,10_000 ether);token.mint(NEWCOMER,10_000 ether);
        _dropMint(INCUMBENT);oldId=nft.tokenAtOrdinal(1);
        _dropMint(NEWCOMER);newId=nft.tokenAtOrdinal(2);
        // Seed incumbent using the full real contribution path, before faults.
        _unboundedContribution(INCUMBENT,oldId,address(0),100 ether,false);
        vm.warp(uint256(c.publicEnd)+3600);
        ethFirst.set(1e8,block.timestamp,block.timestamp);ethSecond.set(1e8,block.timestamp,block.timestamp);
        if(!openingPendingCase)royalty.syncAll();assertTrue(royalty.royaltiesOpen());
        if(pending){
            for(uint256 i;i<16;++i)currencies[i].mint(address(royalty),1601);
            vm.deal(address(royalty),1601);
        }
        launchFixtureReady=true;
    }
    function _dropMint(address owner) internal {
        vm.prank(owner);drop.mintPublic{value:0.05 ether}(address(nft),DROP_FEE,address(0),1);
        uint256 id=nft.tokenAtOrdinal(nft.mintedCount());
        vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
        assertEq(mintHelper.originalMintRecipient(nft.mintedCount()),owner);
    }
    function _unboundedContribution(address owner,uint256 id,address asset,uint256 dollars,bool growth) internal {
        (uint256 lower,,)=oracle.priceBounds(asset);
        uint256 amount=Math.mulDiv(dollars,1e18,lower,Math.Rounding.Ceil);
        ZZZActivationEntry.Request memory r=ZZZActivationEntry.Request(id,target,asset,amount,1,block.timestamp+100,growth);
        bytes32 policy=ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint();
        if(asset!=address(0)){vm.prank(owner);token.approve(address(entry),amount);}
        vm.prank(owner);entry.executeReviewed{value:asset==address(0)?amount:0}(r,300,policy);
    }
    function _royaltyHash() internal view returns(bytes32 h){
        h=keccak256(abi.encode(royalty.activationCount(),royalty.totalWeight(),royalty.weightOf(newId),
            royalty.eligibleCount(address(0)),royalty.accounted(address(0)),royalty.liabilities(address(0))));
        for(uint256 i;i<16;++i){address a=address(currencies[i]);h=keccak256(abi.encode(h,
            royalty.eligibleCount(a),royalty.eligibleWeight(a),royalty.accounted(a),royalty.liabilities(a),royalty.allocationCursor(a)));}
    }
    function _coolLaunch() internal {
        _coolEntry();for(uint256 i;i<16;++i)vm.cool(address(currencies[i]));
        vm.cool(address(royalty));vm.cool(address(mintHelper));vm.cool(address(drop));
    }
    function _measure(bool growth,address asset,uint256 faults,bool pending) internal {
        if(!launchFixtureReady)_launchSetup(pending);
        for(uint256 i;i<faults;++i)currencies[i].failFor(address(royalty));
        address owner=growth?INCUMBENT:NEWCOMER;uint256 id=growth?oldId:newId;
        (uint256 lower,,)=oracle.priceBounds(asset);uint256 amount=Math.mulDiv(growth?5 ether:100 ether,1e18,lower,Math.Rounding.Ceil);
        if(asset!=address(0)){vm.prank(owner);token.approve(address(entry),amount);}
        bytes memory data=abi.encodeCall(ZZZActivationEntry.executeReviewed,
            (ZZZActivationEntry.Request(id,target,asset,amount,1,block.timestamp+100,growth),uint16(300),
            ZZZProtocolPolicy(access.protocolPolicy()).entryFingerprint()));
        ContributionCheck memory check;
        check.upperInput=Math.mulDiv(amount,_priceCapture(asset).upper,1e18,Math.Rounding.Ceil);
        (check.price0,,)=oracle.priceBounds(address(0));(check.price1,,)=oracle.priceBounds(address(token));
        uint256 existingBucket=vault.poolBucket(target);check.old=vault.group(existingBucket);
        check.beforeLP=_actualMainValue(existingBucket,check.price0,check.price1);
        check.beforeNAV=_attributedValue(existingBucket,check.price0,check.price1);
        check.beforeShares=vault.sharesOf(id);check.beforeSupply=vault.bucketTotalShares(existingBucket);
        bytes32 atomicBefore=_entryAtomicState(owner,id);bytes32 royaltyBefore=_royaltyHash();
        uint256 countBefore=royalty.activationCount();
        _exportLaunch(owner,id,asset,valueFor(asset,amount),data,faults,pending,atomicBefore);
        uint256 restore=vm.snapshotState();uint256 value=asset==address(0)?amount:0;
        _coolLaunch();vm.prank(owner);uint256 start=gasleft();
        (bool ok,)=address(entry).call{value:value,gas:20_000_000}(data);
        uint256 used=start-gasleft();
        if(!ok){assertEq(_entryAtomicState(owner,id),atomicBefore);assertEq(_royaltyHash(),royaltyBefore);}
        bool margin=ok && used+Math.ceilDiv(used,5)<=20_000_000;
        uint256 diagnostic=used;
        if(!margin){
            assertTrue(vm.revertToState(restore));assertEq(_entryAtomicState(owner,id),atomicBefore);assertEq(_royaltyHash(),royaltyBefore);
            // Measurement ceiling only: NEVER a candidate default or approval.
            // A failed20M attempt must not leave an enrollment/approval residue.
            _coolLaunch();vm.prank(owner);start=gasleft();
            (bool measured,bytes memory reason)=address(entry).call{value:value,gas:32_000_000}(data);
            diagnostic=start-gasleft();
            if(!measured)emit log_named_bytes("diagnostic32M.failure",reason);
            assertTrue(measured,"bounded diagnostic must reach the accounting assertions");
        }
        emit LaunchGas(growth?"growth":"activation",faults,ok,used,margin,diagnostic,diagnostic+Math.ceilDiv(diagnostic,5));
        emit log_named_uint("launch.faults",faults);emit log_named_uint("launch.is-growth",growth?1:0);
        emit log_named_uint("launch.call20M.success",ok?1:0);emit log_named_uint("launch.call20M.gas",used);
        emit log_named_uint("launch.full20percent.fits20M",margin?1:0);
        emit log_named_uint("launch.completed.call-gas",diagnostic);
        emit log_named_uint("launch.completed.full20percent",diagnostic+Math.ceilDiv(diagnostic,5));
        assertTrue(membership.eligible(id));assertGt(vault.sharesOf(id),0);assertFalse(_execution().executionActive());
        assertEq(nft.ownerOf(id),owner);assertEq(royalty.activationCount(),countBefore+(growth?0:1));
        _assertLaunchPlacement(id,existingBucket,check);
        if(pending){
            for(uint256 i;i<16;++i){address a=address(currencies[i]);
                if(i<faults)currencies[i].failFor(address(0));
                royalty.sync(a);
                assertEq(royalty.claimable(newId,a),0,"newcomer cannot take older royalties");
                assertEq(royalty.claimable(oldId,a),1601,"every old unit remains incumbent-owned");
            }
            royalty.sync(address(0));assertEq(royalty.claimable(oldId,address(0)),1601);assertEq(royalty.claimable(newId,address(0)),0);
        }
        assertEq(token.allowance(owner,address(entry)),0);assertEq(token.allowance(address(entry),address(vault)),0);
        assertEq(address(entry).balance,0);assertEq(token.balanceOf(address(entry)),0);
    }
    function _assertLaunchPlacement(uint256 id,uint256 bucket,ContributionCheck memory check) internal view {
        assertEq(vault.nftBucket(id),bucket);
        assertGe(_actualMainValue(bucket,check.price0,check.price1)-check.beforeLP,
            check.upperInput-Math.mulDiv(check.upperInput,300,10000),"actual added LP retains at least97percent");
        uint256 added=_attributedValue(bucket,check.price0,check.price1)-check.beforeNAV;
        assertEq(vault.sharesOf(id)-check.beforeShares,Math.mulDiv(check.beforeSupply,added,check.beforeNAV));
        assertEq(vault.group(bucket).lpTokenId,check.old.lpTokenId);
        assertEq(vault.group(bucket).centerX96,check.old.centerX96);
        assertEq(vault.group(bucket).lastRebalance,check.old.lastRebalance);
        assertEq(positions.ownerOf(check.old.lpTokenId),address(vault));
        assertEq(manager.secondaryId(check.old.lpTokenId),0);_assertPrefunds();
    }
    function valueFor(address asset,uint256 amount) internal pure returns(uint256){return asset==address(0)?amount:0;}
    function _exportLaunch(address owner,uint256 id,address asset,uint256 value,bytes memory data,uint256 faults,bool pending,bytes32 hash) internal {
        if(bytes(vm.envOr("POPL_GAS_PROFILE_EXPORT_ROOT",string(""))).length==0)return;
        string memory label=string.concat(id==oldId?"growth-":"activation-",asset==address(0)?"eth-":"zzz-",vm.toString(faults),pending?"-pending":"-empty",openingPendingCase?"-opening":"-steady");
        for(uint256 i;i<16;++i)_profileMaterialize(address(currencies[i]));
        _profileMaterialize(address(mintHelper));_profileMaterialize(address(drop));
        _profileExport(ProfileCall(label,owner,address(entry),value,data,20_000_000,2000,id,vault.nftBucket(id)),hash);
    }
    function testLaunch16ColdHealthyETHActivationAndGrowth() public {_measure(false,address(0),0,true);_measure(true,address(0),0,true);}
    function testLaunch16ColdHealthyZZZActivationAndGrowth() public {_measure(false,address(token),0,true);_measure(true,address(token),0,true);}
    function testLaunch16ColdEmptyETHActivation() public {_measure(false,address(0),0,false);}
    function testLaunch16FirstOpeningAllocationETHActivation() public {openingPendingCase=true;_measure(false,address(0),0,true);}
    function testLaunch16OneBurningFaultETHActivation() public {_measure(false,address(0),1,true);}
    function testLaunch16AllBurningFaultsETHActivation() public {_measure(false,address(0),16,true);}
    function testLaunch16AllBurningFaultsDoNotAffectGrowth() public {_measure(true,address(0),16,true);}
    function testLaunch16RPCStateHealthyPendingAndGrowth() public {_measure(false,address(0),0,true);_measure(true,address(0),0,true);}
}
