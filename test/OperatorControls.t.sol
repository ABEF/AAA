// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {DualOracleFixture} from "./helpers/DualOracleFixture.sol";
import {ZZZOracle as FixtureOracleType} from "../src/ZZZOracle.sol";
using DualOracleFixture for FixtureOracleType;


import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {Ids, PoolConfig, PoolKey} from "../src/libraries/ZZZTypes.sol";
import {BoundDummy, MockToken, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {CanonicalFixture} from "./helpers/CanonicalFixture.sol";
import {RangeRewardAdmission} from "./RangePolicy.t.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";

/// Test-only dependencies; real controller/registry/NFT, no actual venue or VRF.
contract OperatorControlsTest is Test, IERC721Receiver {
    ZZZAccessController ac;
    ZZZPoolRegistry registry;
    ZZZNFT nft;
    ZZZOracle oracle;
    MockVRF vrf;
    MockToken t0; MockToken t1; MockFeed feed;
    PoolConfig config; bytes32 pool;
    bool pauseOnReceive;
    address constant GUARDIAN = address(0x600D);
    address constant KEEPER = address(0xBEEF);

    function setUp() public {
        vm.warp(1000000);
        ac = new ZZZAccessController(address(this), KEEPER, GUARDIAN);
        registry = new ZZZPoolRegistry(address(ac)); nft = new ZZZNFT(address(ac), "");
        oracle = new ZZZOracle(address(ac), address(0)); vrf = new MockVRF();
        nft.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        t0 = new MockToken(0); t1 = new MockToken(0);
        if (address(t0) > address(t1)) (t0, t1) = (t1, t0);
        feed = new MockFeed(8, 1e8);
        oracle.setTestFeed(address(t0), address(feed), 3600); oracle.setTestFeed(address(t1), address(feed), 3600);
        ac.bind(Ids.NFT,address(nft)); ac.bind(Ids.POOLS,address(registry)); ac.bind(Ids.ORACLE,address(oracle));
        ac.bind(Ids.REWARDS,address(new RangeRewardAdmission(address(ac))));
        bytes32[8] memory ids = [Ids.VAULT, Ids.LIQUIDITY, Ids.MEMBERSHIP, Ids.FEES, Ids.STRATEGY, Ids.COMPOUNDER, Ids.BUYBACK, Ids.MIGRATION];
        for(uint256 i; i<ids.length; ++i) {
            ac.bind(ids[i],address(new BoundDummy(address(ac))));
        }
        config.key=PoolKey(address(t0),address(t1),3000,60,address(0));
        config.depositsEnabled=true;config.operationsEnabled=true;config.rangeBps=2000;
        config.triggerBps=500;config.maxSpotDeviationBps=100;config.maxSlippageBps=100;
        config.minRebalanceInterval=600;config.minDepositUSD=1e18;config.maxPositionUSD=1e30;
        registry.activationAssets().configureZZZ(address(t1),address(t1).codehash,keccak256("operator fixture ZZZ"));
        pool=registry.configure(config);
        CanonicalFixture.bind(address(ac)); ac.seal();
    }
    function _gov(address target, bytes memory data) private {
        (bool ok, bytes memory result) = target.call(data);
        if (!ok) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
    }
    function testPoolStopWorksWhenPriceTokenAndVenueCallsFail() public {
        vm.mockCallRevert(address(oracle),bytes(""),bytes("price unavailable"));
        vm.mockCallRevert(address(t0),bytes(""),bytes("token unavailable"));
        vm.mockCallRevert(ac.module(Ids.LIQUIDITY),bytes(""),bytes("venue unavailable"));
        _gov(address(registry),abi.encodeCall(registry.disablePool,(pool,true,true)));
        PoolConfig memory c=registry.get(pool);assertFalse(c.depositsEnabled);assertFalse(c.operationsEnabled);
        c.depositsEnabled=true;c.operationsEnabled=true;
        vm.expectRevert();registry.configure(c);
        assertFalse(registry.get(pool).depositsEnabled);
        vm.clearMockedCalls();registry.configure(c);
        assertTrue(registry.get(pool).depositsEnabled);assertTrue(registry.get(pool).operationsEnabled);
    }
    function testPoolStopOnlyClearsSelectedFlagsAndIsIdempotent() public {
        _gov(address(registry),abi.encodeCall(registry.disablePool,(pool,true,false)));
        PoolConfig memory expected=config;expected.depositsEnabled=false;
        assertEq(abi.encode(registry.get(pool)),abi.encode(expected));
        _gov(address(registry),abi.encodeCall(registry.disablePool,(pool,true,false)));
        _gov(address(registry),abi.encodeCall(registry.disablePool,(pool,false,true)));
        expected.operationsEnabled=false;assertEq(abi.encode(registry.get(pool)),abi.encode(expected));
    }
    function testUnknownPoolAndEmptyStopRejectedWithoutAdmission() public {
        vm.prank(ac.governance());vm.expectRevert();registry.disablePool(bytes32(uint256(55)),true,true);
        vm.prank(ac.governance());vm.expectRevert();registry.disablePool(pool,false,false);
        assertFalse(registry.exists(bytes32(uint256(55))));assertTrue(registry.get(pool).depositsEnabled);
    }
    function testOnlyApprovedGovernanceCanToggleControlsAfterSeal() public {
        address[4] memory callers=[address(0xA0A0),GUARDIAN,KEEPER,address(0xBAD)];
        for(uint256 i;i<callers.length;++i){
            vm.prank(callers[i]);vm.expectRevert();registry.disablePool(pool,true,true);
            vm.prank(callers[i]);vm.expectRevert();nft.setMintPaused(true);
        }
        _gov(address(nft),abi.encodeCall(nft.setMintPaused,(true)));assertTrue(nft.mintPaused());
        _gov(address(nft),abi.encodeCall(nft.setMintPaused,(false)));assertFalse(nft.mintPaused());
    }
    function testGlobalPauseDoesNotPreventGovernanceStopsOrGetCleared() public {
        vm.prank(GUARDIAN);ac.setPaused(true);
        _gov(address(registry),abi.encodeCall(registry.disablePool,(pool,true,true)));
        _gov(address(nft),abi.encodeCall(nft.setMintPaused,(true)));
        _gov(address(nft),abi.encodeCall(nft.setMintPaused,(false)));assertTrue(ac.paused());
    }
    function testCanonicalLockCannotBeBypassedThroughNewControls() public {
        vm.prank(ac.canonicalHandoff());ac.canonicalTransition(1,false,false);
        vm.prank(ac.governance());vm.expectRevert();registry.disablePool(pool,true,true);
        vm.prank(ac.governance());vm.expectRevert();nft.setMintPaused(false);
    }
    function testMintCallbackPauseRollsBackOriginalRequestAndOwnership() public {
        // The NFT recipient is the configured governance contract. Its direct
        // callback mutation must roll back with the failed in-progress mint.
        // The bound test vault's getter is supplied explicitly for this boundary.
        address vault=ac.module(Ids.VAULT);
        vm.mockCall(vault,abi.encodeWithSignature("mintProceedsRecipient()"),abi.encode(address(0x1234)));
        pauseOnReceive=true;
        vm.prank(vault);vm.expectRevert(bytes4(keccak256("Paused()")));nft.mint(address(this),44);
        assertEq(nft.mintedCount(),0);assertEq(vrf.sequence(),0);assertEq(nft.requestOf(44),0);
        assertFalse(nft.mintPaused());
    }
    function onERC721Received(address,address,uint256,bytes calldata) external returns(bytes4) {
        if(pauseOnReceive) nft.setMintPaused(true);
        return IERC721Receiver.onERC721Received.selector;
    }
}

/// Real economic modules with explicitly mocked authority, prices and venue.
contract MintControlIntegrationTest is PooledVaultFixture {
    function testPausedMintCannotSpendPaymentOrCreateRequestAndResumeWorks() public {
        nft.setMintPaused(true);uint256 beforeBalance=alice.balance;uint256 beforeTreasury=treasury.balance;
        vm.prank(alice);vm.expectRevert(bytes4(keccak256("Paused()")));vault.mintDormant{value:0.05 ether}();
        assertEq(alice.balance,beforeBalance);assertEq(treasury.balance,beforeTreasury);
        assertEq(vault.sequence(),0);assertEq(nft.mintedCount(),0);assertEq(vrf.sequence(),0);
        nft.setMintPaused(false);assertEq(nft.ownerOf(_mint(alice)),alice);
    }
    function testPendingFulfillmentAndRevealContinueWhileMintPaused() public {
        vm.prank(alice);uint256 id=vault.mintDormant{value:0.05 ether}();uint256 request=nft.requestOf(id);
        nft.setMintPaused(true);vrf.fulfill(request,0,0);nft.finalizeTraits(id);
        assertTrue(nft.traitsReady(id));assertEq(nft.requestOf(id),request);assertEq(nft.nextToFinalize(),2);
    }
    function testExistingActivationTopUpMaintenanceTransfersAndBothClaimsContinue() public {
        uint256 id=_mint(alice);nft.setMintPaused(true);_activate(alice,id,1000,1000);
        uint256 bucket=vault.nftBucket(id);venue.setFees(100,100);vault.collectFees(bucket,block.timestamp+100);
        vm.prank(alice);vault.increase(id,100,100,1,block.timestamp+100);
        vault.rebalance(bucket,1,block.timestamp+100);
        (bool funded,)=address(nft.royaltyRewards()).call{value:1 ether}("");assertTrue(funded);
        vm.prank(alice);nft.transferFrom(alice,bob,id);
        // Keep the owner impersonation across the royalty-ledger getter as well.
        vm.startPrank(bob);assertEq(rewards.claim(id,address(t0)),90);
        assertEq(nft.royaltyRewards().claim(id,address(0)),1 ether);vm.stopPrank();
        assertTrue(membership.eligible(id));assertGt(vault.sharesOf(id),2000e18);assertTrue(nft.mintPaused());
    }
    function testUnpausingMintCannotBypassGlobalPauseOrPreparation() public {
        nft.setMintPaused(true);ac.setPaused(true);nft.setMintPaused(false);
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}();
        ac.setPaused(false);ac.setPreparation(true);
        vm.expectRevert();nft.setMintPaused(false);
        vm.prank(alice);vm.expectRevert();vault.mintDormant{value:0.05 ether}();
        assertEq(nft.mintedCount(),0);
    }
}

contract PoolStopEconomicIntegrationTest is PooledVaultFixture {
    function testDepositStopBlocksActivationAndTopUpWithoutTouchingExistingRights() public {
        ZZZPoolRegistry actual = new ZZZPoolRegistry(address(ac));
        PoolConfig memory c=pools.get(poolId);
        if(c.key.currency0>c.key.currency1) (c.key.currency0,c.key.currency1)=(c.key.currency1,c.key.currency0);
        c.rangeBps=2000;c.triggerBps=500;c.maxSpotDeviationBps=100;c.minRebalanceInterval=600;
        ac.bind(Ids.POOLS,address(actual));
        actual.activationAssets().configureZZZ(address(t1),address(t1).codehash,keccak256("economic stop fixed ZZZ"));
        poolId=actual.configure(c);
        uint256 id=activatedPosition();uint256 other=_mint(bob);uint256 bucket=vault.nftBucket(id);
        uint256 shares=vault.sharesOf(id);uint256 lp=vault.group(bucket).lpTokenId;
        venue.setFees(100,100);vault.collectFees(bucket,block.timestamp+100);
        actual.disablePool(poolId,true,false);
        vm.prank(bob);vm.expectRevert();vault.activate(other,poolId,1000,1000,1,block.timestamp+100);
        vm.prank(alice);vm.expectRevert();vault.increase(id,100,100,1,block.timestamp+100);
        assertEq(vault.sharesOf(id),shares);assertEq(vault.group(bucket).lpTokenId,lp);
        assertEq(vault.sharesOf(other),0);vm.prank(alice);nft.transferFrom(alice,bob,id);
        vm.prank(bob);assertEq(rewards.claim(id,address(t0)),90);
        actual.configure(c);vm.prank(bob);vault.increase(id,100,100,1,block.timestamp+100);
        assertGt(vault.sharesOf(id),shares);
    }
}
