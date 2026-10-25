// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {BoundDummy, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";

using DualOracleFixture for ZZZOracle;

/// @notice Real Access/Registry/source identity/Migration/Buyback binding. Other
/// unused core roles, prices and tokens are explicit bootstrap test substitutes;
/// this does not deploy public contracts or qualify a token/venue/provider.
contract FixedZZZBindingTest is Test {
    ZZZAccessController private access;
    ZZZPoolRegistry private pools;
    ZZZOracle private oracle;
    ZZZRewards private rewards;
    ZZZMigration private migration;
    ZZZBuyback private buyback;
    MockToken private token;
    MockToken private other;
    bytes32 private constant REVIEW=keccak256("fixed ZZZ bootstrap fixture");

    function setUp() public {
        vm.warp(1_000_000);
        access=new ZZZAccessController(address(this), address(this), address(0x600D));
        token=new MockToken(18);other=new MockToken(18);
        pools=new ZZZPoolRegistry(address(access));oracle=new ZZZOracle(address(access),address(0));
        rewards=new ZZZRewards(address(access));migration=new ZZZMigration(address(access));
        access.bind(Ids.POOLS,address(pools));access.bind(Ids.ORACLE,address(oracle));
        access.bind(Ids.REWARDS,address(rewards));access.bind(Ids.MIGRATION,address(migration));
        MockFeed feed=new MockFeed(8,1e8);
        oracle.setTestFeed(address(token),address(feed),3600);
        oracle.setTestFeed(address(other),address(feed),3600);
        rewards.addAsset(address(token));rewards.addAsset(address(other));
        pools.activationAssets().configureZZZ(address(token),address(token).codehash,REVIEW);
    }

    function _bindBuyback(address target) private {
        buyback=new ZZZBuyback(address(access),target,1e30);
        access.bind(Ids.BUYBACK,address(buyback));
    }
    function _fillOtherModules() private {
        bytes32[7] memory ids=[Ids.VAULT,Ids.NFT,Ids.LIQUIDITY,Ids.MEMBERSHIP,
            Ids.FEES,Ids.STRATEGY,Ids.COMPOUNDER];
        for(uint256 i;i<ids.length;++i)access.bind(ids[i],address(new BoundDummy(address(access))));
        CanonicalFixture.bind(address(access));
    }
    function _configureExit() private {
        migration.configureZZZ(address(token),address(token).codehash,REVIEW);
    }

    function testUnboundBuybackCannotCommitExitIdentityAndMatchingBindingAllowsSeal() public {
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);_configureExit();
        assertEq(migration.currentZZZ(),address(0));assertEq(migration.zzzCodeHash(),bytes32(0));
        _fillOtherModules();
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);access.seal();
        assertFalse(access.isSealed());assertEq(access.bootstrap(),address(this));
        _bindBuyback(address(token));_configureExit();access.seal();
        assertTrue(access.isSealed());assertEq(access.bootstrap(),address(0));
        assertEq(pools.activationAssets().zzz(),address(token));
        assertEq(migration.currentZZZ(),address(token));assertEq(buyback.zzz(),address(token));
    }

    function testMismatchedImmutableBuybackCannotCommitExitIdentityOrSeal() public {
        _bindBuyback(address(other));
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);_configureExit();
        assertEq(migration.currentZZZ(),address(0));assertEq(migration.zzzCodeHash(),bytes32(0));
        assertEq(pools.activationAssets().zzz(),address(token));assertEq(buyback.zzz(),address(other));
        _fillOtherModules();
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);access.seal();
        assertFalse(access.isSealed());assertEq(access.bootstrap(),address(this));
    }

    function testRetiredBuybackSetterCannotRetargetBeforeOrAfterSeal() public {
        _bindBuyback(address(token));
        bytes memory payload=abi.encodeWithSignature("setZZZ(address,bytes32,bytes32)",
            address(other),address(other).codehash,REVIEW);
        // Both assets/feeds are admitted: the old bootstrap setter would pass.
        (bool bootstrapChanged,)=address(buyback).call(payload);
        assertFalse(bootstrapChanged);assertEq(buyback.zzz(),address(token));
        _configureExit();_fillOtherModules();access.seal();
        vm.prank(access.governance());(bool governanceChanged,)=address(buyback).call(payload);
        assertFalse(governanceChanged);assertEq(buyback.zzz(),address(token));
        assertEq(migration.currentZZZ(),address(token));assertEq(pools.activationAssets().zzz(),address(token));
        address replacement=address(new BoundDummy(address(access)));
        vm.prank(access.governance());vm.expectRevert();access.bind(Ids.BUYBACK,replacement);
    }
}
