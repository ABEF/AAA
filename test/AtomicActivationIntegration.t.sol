// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZProtocolPolicy} from "../src/interfaces/IZZZProtocolPolicy.sol";
import {SyntheticPoolRegistry as ZZZPoolRegistry} from "./helpers/SyntheticPoolRegistry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {Ids,PoolKey,PoolConfig,Position} from "../src/libraries/ZZZTypes.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {VaultLiquidityMock} from "./VaultAccounting.t.sol";
import {MockToken,MockFeed} from "./mocks/Mocks.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;

/// @dev Direct-input ledger fixture. This synthetic ERC20 pair isolates share,
/// price, policy and callback accounting; actual native/core execution remains
/// in NativeVaultFlows and OptionalPortfolioCore, not this mock LP manager.
abstract contract DirectEntryFixture is PooledVaultFixture {
    ZZZPoolRegistry registry;
    ZZZActivationAssets assets;
    ZZZActivationEntry entry;
    bytes32 constant REVIEW=keccak256("direct Entry3 test review, not provider qualification");
    modifier realIntegration() {_integrationFixture();_;}
    function _integrationFixture() internal {
        ac.beginBootstrap();vault.migrationBudget().setLossLimits(100,300);
        // The inherited accounting fixture deliberately has zero-decimal,
        // unsorted tokens. Use explicit sorted18-decimal test assets here.
        MockToken a=new MockToken(18);MockToken b=new MockToken(18);
        t0=address(a)<address(b)?a:b;t1=address(a)<address(b)?b:a;
        venue=new VaultLiquidityMock(address(t0),address(t1));ac.bind(Ids.LIQUIDITY,address(venue));
        MockFeed feed=new MockFeed(8,1e8);
        oracle.setTestFeed(address(t0),address(feed),3600);oracle.setTestFeed(address(t1),address(feed),3600);
        rewards.addAsset(address(t0));rewards.addAsset(address(t1));
        t0.mint(alice,10000e18);t0.mint(bob,10000e18);t1.mint(alice,10000e18);t1.mint(bob,10000e18);
        registry=new ZZZPoolRegistry(address(ac));ac.bind(Ids.POOLS,address(registry));
        assets=registry.activationAssets();entry=registry.activationEntry();
        assets.configureZZZ(address(t0),address(t0).codehash,REVIEW);
        PoolConfig memory config=PoolConfig(PoolKey(address(t0),address(t1),3000,60,address(0)),
            true,true,1000,300,100,100,600,1e18,1e30);
        poolId=registry.configure(config);ac.seal();
    }
    function _request(uint256 id,bool grow) internal view returns(ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id,poolId,address(t0),grow?5e18:100e18,1,block.timestamp+100,grow);
    }
    function _execute(address owner,ZZZActivationEntry.Request memory request) internal {
        bytes32 policy=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
        vm.startPrank(owner);t0.approve(address(entry),request.amountIn);
        entry.executeReviewed(request,100,policy);vm.stopPrank();
    }
    function _reject(address owner,ZZZActivationEntry.Request memory request) internal {
        bytes32 policy=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
        vm.startPrank(owner);t0.approve(address(entry),request.amountIn);
        vm.expectRevert();entry.executeReviewed(request,100,policy);vm.stopPrank();
    }
    function _clean() internal view {
        assertEq(t0.balanceOf(address(entry)),0);assertEq(t1.balanceOf(address(entry)),0);
        assertEq(t0.allowance(address(entry),address(vault)),0);
        assertFalse(oracle.contributionPricing().active());
    }
    function _unspent(uint256 id,uint256 balance) internal view {
        assertEq(t0.balanceOf(alice),balance);assertEq(vault.nftBucket(id),0);
        assertEq(vault.sharesOf(id),0);assertEq(vault.contributionUSD(id),0);
        assertFalse(membership.eligible(id));assertEq(nft.royaltyRewards().weightOf(id),0);
        assertEq(nft.ownerOf(id),alice);_clean();
    }
}

contract AtomicActivationIntegrationTest is DirectEntryFixture {
    function testDirectInputActivatesAndGrowsWithoutEntryConversion() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t0.balanceOf(alice);
        _execute(alice,_request(id,false));uint256 bucket=vault.nftBucket(id);
        Position memory p=vault.group(bucket);uint256 lp=p.lpTokenId;
        assertEq(venue.a0(lp),100e18);assertEq(venue.a1(lp),0);assertEq(vault.sharesOf(id),100e18);
        assertEq(before-t0.balanceOf(alice),100e18);assertEq(t0.allowance(alice,address(entry)),0);
        _execute(alice,_request(id,true));
        assertEq(vault.group(bucket).lpTokenId,lp);assertEq(venue.a0(lp),105e18);
        assertEq(vault.contributionUSD(id),105e18);assertEq(membership.totalEligible(),1);
        assertEq(vault.group(bucket).lastRebalance,p.lastRebalance);_clean();
    }
    function testDirectInputDeploymentFloorAndFailurePreservePrincipalAndShares() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t0.balanceOf(alice);
        venue.setSpendBps(9899);_reject(alice,_request(id,false));_unspent(id,before);
        venue.setSpendBps(9900);_execute(alice,_request(id,false));
        uint256 bucket=vault.nftBucket(id);uint256 lp=vault.group(bucket).lpTokenId;
        assertEq(venue.a0(lp),99e18);assertEq(vault.group(bucket).idle0,1e18);
        uint256 shares=vault.sharesOf(id);before=t0.balanceOf(alice);venue.setSpendBps(9899);
        _reject(alice,_request(id,true));
        assertEq(vault.sharesOf(id),shares);assertEq(t0.balanceOf(alice),before);
        assertEq(vault.group(bucket).lpTokenId,lp);_clean();
    }
    function testDirectInputActionMinimaAndStrongerPoolFloor() public realIntegration {
        uint256 id=_mint(alice);ZZZActivationEntry.Request memory r=_request(id,false);
        r.amountIn=100e18-1;_reject(alice,r);
        _execute(alice,_request(id,false));r=_request(id,true);r.amountIn=5e18-1;
        _reject(alice,r);
        PoolConfig memory c=registry.get(poolId);c.minDepositUSD=6e18;registry.configure(c);
        r.amountIn=5e18;_reject(alice,r);
        c.minDepositUSD=1;registry.configure(c);_execute(alice,r);
        assertEq(vault.contributionUSD(id),105e18);_clean();
    }
    function testDirectInputOwnershipAndOldUnclaimedRightsFollowTransfer() public realIntegration {
        uint256 id=_mint(alice);_execute(alice,_request(id,false));
        uint256 bucket=vault.nftBucket(id);venue.setFees(1000,1000);vault.collectFees(bucket,block.timestamp+100);
        uint256 earned=rewards.claimable(id,address(t0));assertGt(earned,0);
        vm.prank(alice);nft.transferFrom(alice,bob,id);
        _reject(alice,_request(id,true));
        _execute(bob,_request(id,true));vm.prank(alice);vm.expectRevert();rewards.claim(id,address(t0));
        uint256 before=t0.balanceOf(bob);vm.prank(bob);assertEq(rewards.claim(id,address(t0)),earned);
        assertEq(t0.balanceOf(bob)-before,earned);_clean();
    }
    function testNFTApprovalDoesNotAuthorizeFundingOrEntryContext() public realIntegration {
        uint256 id=_mint(alice);vm.prank(alice);nft.approve(bob,id);
        _reject(bob,_request(id,false));
        vm.prank(address(vault));vm.expectRevert();entry.validateOwner(id,bytes32(uint256(1)));
        vm.prank(address(registry));assertEq(entry.sourceValue(poolId,100e18,0),0);_clean();
    }
    function testDirectInputUnsupportedCurrencyAndMissingAllowanceStayAtomic() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t0.balanceOf(alice);
        ZZZActivationEntry.Request memory r=_request(id,false);r.sourceAsset=address(t1);
        _reject(alice,r);_unspent(id,before);
        r=_request(id,false);bytes32 policy=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
        vm.prank(alice);t0.approve(address(entry),0);
        vm.prank(alice);vm.expectRevert();entry.executeReviewed(r,100,policy);_unspent(id,before);
    }
    function testDirectInputDisabledPolicyAndPrefundsNeverSubsidizeActivation() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t0.balanceOf(alice);
        t0.mint(address(entry),17);vm.deal(address(entry),13);
        assets.setAsset(address(t0),false,address(t0).codehash,REVIEW);
        _reject(alice,_request(id,false));
        assertEq(t0.balanceOf(alice),before);assertEq(t0.balanceOf(address(entry)),17);
        assets.setAsset(address(t0),true,address(t0).codehash,REVIEW);
        _execute(alice,_request(id,false));assertEq(t0.balanceOf(address(entry)),17);
        assertEq(address(entry).balance,13);assertEq(vault.contributionUSD(id),100e18);
    }
    function testRetiredRouteAndNineWordRequestSelectorsCannotMoveFunds() public realIntegration {
        uint256 id=_mint(alice);uint256 before=t0.balanceOf(alice);
        bytes32 policy=IZZZProtocolPolicy(ac.protocolPolicy()).entryFingerprint();
        bytes memory old=abi.encodeWithSignature(
            "executeReviewed((uint256,bytes32,address,uint256,bytes32,uint256,uint128,uint256,bool),uint16,bytes32)",
            id,poolId,address(t0),100e18,bytes32(0),uint256(0),uint128(1),block.timestamp+100,false,uint16(100),policy);
        vm.prank(alice);(bool ok,)=address(entry).call(old);assertFalse(ok);_unspent(id,before);
        (ok,)=address(entry).call(abi.encodeWithSignature("setRouteEnabled(bytes32,bool)",bytes32(uint256(1)),true));assertFalse(ok);
        (ok,)=address(entry).call(abi.encodeWithSignature("v4Executor()"));assertFalse(ok);
        assertEq(entry.ENTRY_ROUTING_VERSION(),3);assertEq(entry.REVIEW_POLICY_VERSION(),2);
    }
}
