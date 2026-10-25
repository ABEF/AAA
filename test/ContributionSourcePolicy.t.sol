// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZActivationAssetsFactory} from "../src/ZZZActivationAssetsFactory.sol";
import {IZZZAccess} from "../src/interfaces/IZZZ.sol";
import {MockAccess,MockToken,MockFeed,BoundDummy} from "./mocks/Mocks.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {Ids,PoolKey,PoolConfig} from "../src/libraries/ZZZTypes.sol";

contract ContributionPolicyRegistryFixture {
    ZZZActivationAssets public immutable activationAssets;
    ZZZActivationEntry public immutable activationEntry;
    address private immutable token;
    constructor(address controller,address pairToken) {
        token=pairToken;
        activationAssets=ZZZActivationAssets(ZZZActivationAssetsFactory(IZZZAccess(controller).activationAssetsFactory()).create());
        activationEntry=new ZZZActivationEntry(controller,address(this),address(activationAssets));
    }
    function admit(address asset) external returns(bytes32) { return activationAssets.admitPoolAsset(asset); }
    function accounting(bytes32) external view returns(PoolConfig memory config) {
        config.key=PoolKey(address(0),token,500,60,address(0));
        config.depositsEnabled=true;config.operationsEnabled=true;
    }
}
contract ContributionPolicyNFTFixture {
    address private immutable owner;
    constructor(address account) { owner=account; }
    function ownerOf(uint256) external view returns(address) { return owner; }
}
contract ContributionPolicyRewardsFixture {
    function isAsset(address) external pure returns(bool) { return true; }
}

/// @notice Tests source policy and actual Registry direct-value boundary with
/// controlled dual-feed fixtures; no token/feed/venue is production-qualified.
contract ContributionSourcePolicyTest is Test {
    using DualOracleFixture for ZZZOracle;
    MockAccess private access;
    ZZZOracle private oracle;
    ContributionPolicyRegistryFixture private registry;
    ZZZActivationAssets private assets;
    MockToken private zzz;
    MockToken private stable;
    MockToken private replacement;
    MockFeed private feed;
    bytes32 private constant REVIEW=keccak256("explicit source identity fixture, not live approval");

    function setUp() public {
        vm.warp(1_000_000);
        access=new MockAccess();oracle=new ZZZOracle(address(access),address(0));
        access.bind(Ids.ORACLE,address(oracle));
        zzz=new MockToken(18);stable=new MockToken(6);replacement=new MockToken(18);
        feed=new MockFeed(8,1e8);
        oracle.setTestFeed(address(0),address(feed),3600);
        oracle.setTestFeed(address(zzz),address(feed),3600);
        oracle.setTestFeed(address(stable),address(feed),3600);
        oracle.setTestFeed(address(replacement),address(feed),3600);
        registry=new ContributionPolicyRegistryFixture(address(access),address(zzz));assets=registry.activationAssets();
        access.bind(Ids.POOLS,address(registry));
        access.bind(Ids.NFT,address(new ContributionPolicyNFTFixture(address(this))));
        access.bind(Ids.VAULT,address(new BoundDummy(address(access))));
    }
    function _configure() private { assets.configureZZZ(address(zzz),address(zzz).codehash,REVIEW); }

    function testFixedFactoryAuthenticatesConstructionAndNeverReplacesRegistryChild() public {
        ZZZActivationAssetsFactory factory=ZZZActivationAssetsFactory(access.activationAssetsFactory());
        assertEq(factory.access(),address(access));
        assertEq(factory.assetsOf(address(registry)),address(assets));
        assertEq(assets.registry(),address(registry));
        vm.prank(address(registry));vm.expectRevert();factory.create();
        vm.expectRevert();new ZZZActivationAssets(address(access),address(this));
        address other=factory.create();
        assertEq(factory.assetsOf(address(this)),other);
        assertEq(ZZZActivationAssets(other).registry(),address(this));
        assertEq(factory.assetsOf(address(registry)),address(assets));
        vm.expectRevert();factory.create();
    }
    function testOnlyNativeETHAndExplicitReviewedZZZCanBeSupplied() public {
        assertEq(assets.SOURCE_POLICY_VERSION(),1);
        assertTrue(assets.isContributionAsset(address(0)));
        assertFalse(assets.isContributionAsset(address(zzz)));
        _configure();registry.admit(address(0));
        assertTrue(assets.isContributionAsset(address(zzz)));
        assertFalse(assets.isContributionAsset(address(stable)));
        assertEq(assets.value(address(zzz),100e18),100e18);
        assertEq(assets.value(address(0),100 ether),100e18);
    }
    function testPairAdmissionCannotEnableAThirdContributionCurrency() public {
        _configure();bytes32 id=registry.admit(address(stable));
        (,bool enabled,,,,bool poolAdmission)=assets.policies(id);
        assertFalse(enabled);assertTrue(poolAdmission);
        vm.expectRevert();assets.setAsset(address(stable),true,address(stable).codehash,REVIEW);
        vm.expectRevert();assets.value(address(stable),1e6);
        assertEq(assets.value(address(stable),0),0);
        assertEq(assets.activePolicy(address(stable)),id);
    }
    function testZZZIdentityCannotBeReplacedEvenBeforeSeal() public {
        _configure();bytes32 old=assets.activePolicy(address(zzz));
        zzz.mint(address(this),17e18);replacement.mint(address(this),23e18);
        vm.expectRevert();assets.configureZZZ(address(replacement),address(replacement).codehash,REVIEW);
        vm.expectRevert();assets.configureZZZ(address(zzz),address(zzz).codehash,REVIEW);
        assertEq(assets.zzz(),address(zzz));assertTrue(assets.isContributionAsset(address(zzz)));
        assertFalse(assets.isContributionAsset(address(replacement)));
        assertEq(assets.activePolicy(address(zzz)),old);assertEq(assets.policyCount(),1);
        assertEq(assets.value(address(zzz),1e18),1e18);
        assertEq(zzz.balanceOf(address(this)),17e18);assertEq(replacement.balanceOf(address(this)),23e18);
    }
    function testSealedIdentityCannotInitializeOrChangeButSameTokenCanBeDisabledAndEnabled() public {
        ContributionPolicyRegistryFixture empty=new ContributionPolicyRegistryFixture(address(access),address(zzz));
        ZZZActivationAssets unconfigured=empty.activationAssets();
        _configure();uint256 count=assets.policyCount();bytes32 old=assets.activePolicy(address(zzz));
        access.seal();
        vm.expectRevert();unconfigured.configureZZZ(address(zzz),address(zzz).codehash,REVIEW);
        vm.expectRevert();assets.configureZZZ(address(replacement),address(replacement).codehash,REVIEW);
        assertEq(assets.zzz(),address(zzz));assertEq(assets.policyCount(),count);
        assertEq(unconfigured.zzz(),address(0));assertEq(assets.activePolicy(address(zzz)),old);
        assets.setAsset(address(zzz),false,address(zzz).codehash,REVIEW);
        vm.expectRevert();assets.value(address(zzz),1e18);
        assets.setAsset(address(zzz),true,address(zzz).codehash,REVIEW);
        assertEq(assets.value(address(zzz),1e18),1e18);assertEq(assets.zzz(),address(zzz));
    }
    function testInvalidIdentityReviewRuntimePriceAndAuthorityDoNotChangePolicy() public {
        uint256 count=assets.policyCount();bytes32 nativeHash=assets.NATIVE_ASSET_CODE_HASH();
        vm.prank(address(0xBAD));vm.expectRevert();
        assets.configureZZZ(address(replacement),address(replacement).codehash,REVIEW);
        vm.expectRevert();assets.configureZZZ(address(0),nativeHash,REVIEW);
        vm.expectRevert();assets.configureZZZ(address(replacement),address(replacement).codehash,bytes32(0));
        vm.expectRevert();assets.configureZZZ(address(replacement),bytes32(uint256(7)),REVIEW);
        feed.set(0,block.timestamp,block.timestamp);
        vm.expectRevert();assets.configureZZZ(address(replacement),address(replacement).codehash,REVIEW);
        assertEq(assets.zzz(),address(0));assertEq(assets.policyCount(),count);
        feed.set(1e8,block.timestamp,block.timestamp);_configure();assertEq(assets.zzz(),address(zzz));
    }
    function testDisabledZZZStillRejectsValueAndPoolReconfigurationCannotReenableIt() public {
        _configure();assets.setAsset(address(zzz),false,address(zzz).codehash,REVIEW);
        bytes32 disabled=assets.activePolicy(address(zzz));registry.admit(address(zzz));
        assertEq(assets.activePolicy(address(zzz)),disabled);
        vm.expectRevert();assets.value(address(zzz),1e18);
        assets.setAsset(address(zzz),true,address(zzz).codehash,REVIEW);
        assertEq(assets.value(address(zzz),1e18),1e18);
    }
    function testEntryRejectsUnsupportedOriginalInputBeforePullOrConversion() public {
        ZZZActivationEntry entry=registry.activationEntry();
        _configure();stable.mint(address(this),100e6);
        stable.approve(address(entry),100e6);access.seal();
        ZZZActivationEntry.Request memory request=ZZZActivationEntry.Request(
            1,bytes32(uint256(42)),address(stable),100e6,bytes32(0),0,1,block.timestamp+100,false);
        vm.expectRevert();entry.executeReviewed(request,200);
        assertEq(stable.balanceOf(address(this)),100e6);
        assertEq(stable.balanceOf(address(registry.activationEntry())),0);
        assertEq(stable.allowance(address(this),address(registry.activationEntry())),100e6);
        assertFalse(oracle.contributionPricing().active());
    }
    function testRealRegistryDirectVaultValueCannotBypassSourceRestriction() public {
        ZZZPoolRegistry real=new ZZZPoolRegistry(address(access));
        real.activationAssets().configureZZZ(address(zzz),address(zzz).codehash,REVIEW);
        access.bind(Ids.REWARDS,address(new ContributionPolicyRewardsFixture()));
        bool first=address(zzz)<address(stable);
        PoolConfig memory config;
        config.key=PoolKey(first?address(zzz):address(stable),first?address(stable):address(zzz),500,60,address(0));
        config.operationsEnabled=true;config.depositsEnabled=true;config.rangeBps=2500;config.triggerBps=100;
        config.maxSpotDeviationBps=100;config.maxSlippageBps=100;config.minRebalanceInterval=600;
        config.minDepositUSD=100e18;config.maxPositionUSD=1e30;
        bytes32 pool=real.configure(config);
        address caller=access.module(Ids.VAULT);
        vm.prank(caller);assertEq(real.contributionValue(pool,first?1e18:0,first?0:1e18),1e18);
        vm.prank(caller);vm.expectRevert();real.contributionValue(pool,first?0:1e6,first?1e6:0);
        vm.prank(caller);vm.expectRevert();real.contributionValue(pool,first?1e18:1e6,first?1e6:1e18);
    }
}
