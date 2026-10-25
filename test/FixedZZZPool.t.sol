// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZActivationAssets} from "../src/ZZZActivationAssets.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess, MockToken} from "./mocks/Mocks.sol";

/// @dev Token/feed/module observations are explicit test substitutes. A poison
/// flag proves rejected identities never reach price/reward admission reads.
contract FixedPoolOracleFixture {
    bool private poisoned;
    error UnexpectedOracleRead();
    function poison() external {poisoned=true;}
    function tokenDecimals(address) external view returns(uint8) {
        if(poisoned)revert UnexpectedOracleRead();return 18;
    }
    function price(address) external view returns(uint256) {
        if(poisoned)revert UnexpectedOracleRead();return 1e18;
    }
}
contract FixedPoolRewardsFixture {
    bool private poisoned;
    error UnexpectedRewardRead();
    function poison() external {poisoned=true;}
    function isAsset(address) external view returns(bool) {
        if(poisoned)revert UnexpectedRewardRead();return true;
    }
}

/// @notice Actual Registry/Assets identity checks with explicit local authority,
/// tokens and pricing/admission substitutes; no live route/venue qualification.
contract FixedZZZPoolTest is Test {
    MockAccess private access;
    ZZZPoolRegistry private registry;
    ZZZActivationAssets private assets;
    FixedPoolOracleFixture private oracle;
    FixedPoolRewardsFixture private rewards;
    MockToken private zzz;
    MockToken private other;
    MockToken private third;
    bytes32 private constant REVIEW=keccak256("fixed ZZZ pair fixture, not token approval");
    address private constant NATIVE_ZZZ=0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;

    function setUp() public {
        access=new MockAccess();registry=new ZZZPoolRegistry(address(access));assets=registry.activationAssets();
        oracle=new FixedPoolOracleFixture();rewards=new FixedPoolRewardsFixture();
        access.bind(Ids.POOLS,address(registry));access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.REWARDS,address(rewards));
        zzz=new MockToken(18);other=new MockToken(18);third=new MockToken(18);
    }
    function _config(address first,address second) private pure returns(PoolConfig memory c) {
        (address a,address b)=first<second?(first,second):(second,first);
        c.key=PoolKey(a,b,3000,60,address(0));c.depositsEnabled=true;c.operationsEnabled=true;
        c.rangeBps=5000;c.triggerBps=500;c.maxSpotDeviationBps=100;c.maxSlippageBps=100;
        c.minRebalanceInterval=600;c.minDepositUSD=100e18;c.maxPositionUSD=1e30;
    }
    function _identity() private {
        assets.configureZZZ(address(zzz),address(zzz).codehash,REVIEW);
    }
    function _unchanged(PoolConfig memory c,uint256 policies) private view {
        assertFalse(registry.exists(keccak256(abi.encode(c.key))));
        assertEq(registry.contributionPool(),bytes32(0));assertEq(assets.policyCount(),policies);
    }

    function testMissingFixedZZZRejectsGenericPoolBeforeDependencyAdmission() public {
        PoolConfig memory c=_config(address(zzz),address(other));oracle.poison();rewards.poison();
        vm.expectCall(address(assets),abi.encodeWithSignature("zzz()"),uint64(2));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);registry.configure(c);
        _unchanged(c,0);assertEq(assets.zzz(),address(0));
    }
    function testPairWithoutFixedZZZRejectsBeforeDependencyAdmission() public {
        _identity();PoolConfig memory c=_config(address(other),address(third));oracle.poison();rewards.poison();
        vm.expectCall(address(assets),abi.encodeWithSignature("zzz()"),uint64(2));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);registry.configure(c);
        _unchanged(c,1);assertEq(assets.zzz(),address(zzz));
    }
    function testFixedZZZPairAndLaterFeeTierRemainAdmissibleWithoutThirdSource() public {
        _identity();PoolConfig memory c=_config(address(zzz),address(other));
        bytes32 initial=registry.configure(c);assertTrue(registry.exists(initial));
        assertEq(registry.contributionPool(),initial);assertEq(assets.zzz(),address(zzz));
        assertTrue(assets.isContributionAsset(address(0)));assertTrue(assets.isContributionAsset(address(zzz)));
        assertFalse(assets.isContributionAsset(address(other)));assertEq(assets.policyCount(),2);
        // Same-token fee-tier changes remain governed after sealing. The old
        // bucket's admitted identity is retained while new contributions switch.
        access.seal();registry.disablePool(initial,true,false);c.key.fee=500;
        bytes32 replacement=registry.configure(c);assertTrue(registry.exists(replacement));
        assertEq(registry.contributionPool(),replacement);assertFalse(registry.get(initial).depositsEnabled);
        assertEq(assets.zzz(),address(zzz));assertFalse(assets.isContributionAsset(address(other)));
    }
    function testNativeAdmissionRetainsItsSeparateFixedIdentityGuard() public {
        _identity();PoolConfig memory c=_config(address(zzz),address(other));
        c.key=PoolKey(address(0),NATIVE_ZZZ,10020,200,address(0));c.maxSlippageBps=200;
        // The distinct native source getter must run even on this unsupported
        // local chain; a chain-only rejection would hide a removed identity check.
        vm.expectCall(address(assets),abi.encodeWithSignature("zzz()"),uint64(2));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);registry.configureNative(c);
        _unchanged(c,1);assertEq(assets.zzz(),address(zzz));
    }
}
