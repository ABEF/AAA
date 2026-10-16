// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZActivationEntry} from "../src/ZZZActivationEntry.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {Ids, PoolKey, PoolConfig, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";
import {IPositionManagerMinimal, IStateViewMinimal} from "../src/interfaces/IZZZ.sol";
import {MockAccess, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";
import {IForkHeaderVm, IForkWETH, IForkPermit2Allowance, ForkRewardAssetAllowlist} from "./UniswapV4Fork.t.sol";

/// @notice Actual selected native/Pons custody tests; opt-in, no public transactions.
/// Mock authority and synthetic oracle calibration are test scaffolding only.
/// They do not establish production USD feeds, VRF, payout rights or audit approval.
contract NativePoolForkTest is Test, IERC721Receiver {
    uint256 private constant FORK_BLOCK = 88_544_093;
    bytes32 private constant FORK_HASH = 0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490;
    address private constant CORE = 0x8366a39CC670B4001A1121B8F6A443A643e40951;
    address private constant POSM = 0x58daec3116aae6D93017bAAea7749052E8a04fA7;
    address private constant STATE = 0xF3334192D15450CdD385c8B70e03f9A6bD9E673b;
    address private constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;
    address private constant WETH = 0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73;
    address private constant ZZZ = 0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    address private constant HOOK = 0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044;
    bytes32 private constant POOL = 0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f;
    MockAccess private access;
    ZZZPoolRegistry private pools;
    ZZZLiquidityManager private manager;
    ZZZOracle private oracle;
    ZZZStrategy private strategy;
    IPositionManagerMinimal private positions;
    ZZZNFT private canonicalNFT;
    MockVRF private vrf;

    function setUp() public {
        if (!vm.envOr("RUN_ROBINHOOD_FORK_TESTS", false)) {
            vm.skip(true, "Opt-in selected-market fork suite; excluded from offline unit verification"); return;
        }
        string memory rpc = vm.envOr("ROBINHOOD_RPC_URL", string("")); require(bytes(rpc).length != 0, "ROBINHOOD_RPC_URL required");
        vm.createSelectFork(rpc, FORK_BLOCK);
        assertEq(block.chainid, 4663); assertEq(block.number, FORK_BLOCK);
        assertEq(keccak256(IForkHeaderVm(address(vm)).getRawBlockHeader(FORK_BLOCK)), FORK_HASH);
        access = new MockAccess(); pools = new ZZZPoolRegistry(address(access));
        oracle = new ZZZOracle(address(access), address(0)); strategy = new ZZZStrategy(address(access));
        positions = IPositionManagerMinimal(POSM);
        manager = new ZZZLiquidityManager(address(access), POSM, STATE, CORE, PERMIT2);
        access.bind(Ids.VAULT, address(this)); access.bind(Ids.POOLS, address(pools)); access.bind(Ids.ORACLE, address(oracle));
        access.bind(Ids.REWARDS, address(new ForkRewardAssetAllowlist())); access.bind(Ids.STRATEGY, address(strategy));
        access.bind(Ids.LIQUIDITY, address(manager));
        (uint160 price,,,) = IStateViewMinimal(STATE).getSlot0(POOL);
        // Synthetic reference ratio matches the pinned spot; it is not an approved ZZZ/USD oracle.
        uint256 ratio = Math.mulDiv(uint256(price), price, uint256(1) << 192);
        oracle.setFeed(WETH, address(new MockFeed(8, int256(ratio * 1e8))), 1 days);
        oracle.setFeed(ZZZ, address(new MockFeed(8, 1e8)), 1 days);
        pools.configureNative(_config());
        canonicalNFT = new ZZZNFT(address(access), "ipfs://test-only/"); vrf = new MockVRF();
        canonicalNFT.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        access.seal();
        vm.deal(address(this), 100 ether); IForkWETH(WETH).deposit{value: 90 ether}(); deal(ZZZ, address(this), 10_000_000 ether);
        IERC20(WETH).approve(address(manager), type(uint256).max); IERC20(ZZZ).approve(address(manager), type(uint256).max);
    }
    function _config() private pure returns (PoolConfig memory c) {
        c.key = PoolKey(address(0), ZZZ, 0, 200, HOOK); c.depositsEnabled = true; c.operationsEnabled = true;
        c.rangeBps = 1000; c.triggerBps = 500; c.maxSpotDeviationBps = 100; c.maxSlippageBps = 200;
        c.minRebalanceInterval = 600; c.minDepositUSD = 100 ether; c.maxPositionUSD = 1_000_000 ether;
    }
    function _mint() private returns (uint256 id) {
        (int24 lower, int24 upper,) = strategy.target(POOL);
        (id,,) = manager.mint(POOL, lower, upper, 0.01 ether, 2000 ether, 1, block.timestamp + 100);
        positions.approve(address(manager), id);
    }
    function _assertApprovalsCleared() private view {
        assertEq(IERC20(WETH).allowance(address(manager), PERMIT2), 0);
        assertEq(IERC20(ZZZ).allowance(address(manager), PERMIT2), 0);
        (uint160 amount,,) = IForkPermit2Allowance(PERMIT2).allowance(address(manager), ZZZ, POSM); assertEq(amount, 0);
    }
    function testSelectedNativeAccountingKeepsRealPoolKey() public view {
        PoolConfig memory real = pools.get(POOL); PoolConfig memory ledger = pools.accounting(POOL);
        assertEq(real.key.currency0, address(0)); assertEq(real.key.hooks, HOOK); assertEq(keccak256(abi.encode(real.key)), POOL);
        assertEq(ledger.key.currency0, WETH); assertEq(ledger.key.currency1, ZZZ); assertEq(pools.nativeAsset(POOL), WETH);
        assertTrue(keccak256(abi.encode(ledger.key)) != POOL);
    }
    function testSelectedNativeMintIncreaseAndClose() public {
        uint256 beforePosmNative = POSM.balance; uint256 id = _mint();
        assertEq(positions.ownerOf(id), address(this)); (PoolKey memory key,) = positions.getPoolAndPositionInfo(id);
        assertEq(keccak256(abi.encode(key)), POOL); uint128 beforeLiquidity = positions.getPositionLiquidity(id);
        manager.collect(POOL, id, block.timestamp + 100);
        manager.increase(POOL, id, 0.001 ether, 200 ether, 1, block.timestamp + 100);
        assertGt(positions.getPositionLiquidity(id), beforeLiquidity); assertEq(POSM.balance, beforePosmNative);
        (uint256 a0, uint256 a1) = manager.amounts(id); uint256 w = IERC20(WETH).balanceOf(address(this));
        uint256 z = IERC20(ZZZ).balanceOf(address(this)); uint256 nativeBalance = address(this).balance;
        manager.collect(POOL, id, block.timestamp + 100); manager.close(POOL, id, block.timestamp + 100);
        assertEq(IERC20(WETH).balanceOf(address(this)), w + a0); assertEq(IERC20(ZZZ).balanceOf(address(this)), z + a1);
        assertEq(address(this).balance, nativeBalance); assertEq(address(manager).balance, 0); _assertApprovalsCleared();
        vm.expectRevert(); positions.ownerOf(id);
    }
    function testSelectedNativeBothSwapDirectionsUseNetOutput() public {
        uint256 beforeZZZ = IERC20(ZZZ).balanceOf(address(this));
        uint256 minZZZ = Math.mulDiv(oracle.quote(WETH, ZZZ, 0.0001 ether), 9800, 10000);
        uint256 outZZZ = manager.swap(POOL, true, 0.0001 ether, minZZZ, block.timestamp + 100);
        assertEq(IERC20(ZZZ).balanceOf(address(this)), beforeZZZ + outZZZ); assertGe(outZZZ, minZZZ);
        uint256 beforeWrapped = IERC20(WETH).balanceOf(address(this));
        uint256 minWrapped = Math.mulDiv(oracle.quote(ZZZ, WETH, 1 ether), 9800, 10000);
        uint256 outWrapped = manager.swap(POOL, false, 1 ether, minWrapped, block.timestamp + 100);
        assertEq(IERC20(WETH).balanceOf(address(this)), beforeWrapped + outWrapped); assertGe(outWrapped, minWrapped);
        assertEq(address(manager).balance, 0); _assertApprovalsCleared();
    }
    function testSelectedNativeCoreZeroFeeDoesNotConferPonsRevenue() public {
        uint256 id = _mint();
        uint256 minZZZ = Math.mulDiv(oracle.quote(WETH, ZZZ, 0.00001 ether), 9800, 10000);
        manager.swap(POOL, true, 0.00001 ether, minZZZ, block.timestamp + 100);
        uint256 w = IERC20(WETH).balanceOf(address(this)); uint256 z = IERC20(ZZZ).balanceOf(address(this));
        manager.collect(POOL, id, block.timestamp + 100);
        assertEq(IERC20(WETH).balanceOf(address(this)), w); assertEq(IERC20(ZZZ).balanceOf(address(this)), z);
    }
    function testSelectedNativePrefundsCannotBecomePrincipalOrFees() public {
        vm.deal(address(manager), 123); vm.deal(POSM, POSM.balance + 456);
        deal(WETH, address(manager), 789); deal(ZZZ, address(manager), 987);
        uint256 beforePosm = POSM.balance; uint256 id = _mint(); manager.collect(POOL, id, block.timestamp + 100);
        manager.close(POOL, id, block.timestamp + 100);
        assertEq(POSM.balance, beforePosm); assertEq(address(manager).balance, 123);
        assertEq(IERC20(WETH).balanceOf(address(manager)), 789); assertEq(IERC20(ZZZ).balanceOf(address(manager)), 987);
    }
    function testSelectedNativeReopenAtAnotherRangeKeepsPoolIdentity() public {
        uint256 id = _mint(); manager.collect(POOL, id, block.timestamp + 100); manager.close(POOL, id, block.timestamp + 100);
        (int24 lower, int24 upper,) = strategy.target(POOL);
        (uint256 nextId,,) = manager.mint(POOL, lower - 200, upper + 200, 0.01 ether, 2000 ether, 1, block.timestamp + 100);
        assertTrue(nextId != id); assertEq(positions.ownerOf(nextId), address(this));
        (PoolKey memory key,) = positions.getPoolAndPositionInfo(nextId); assertEq(keccak256(abi.encode(key)), POOL);
    }
    function testSelectedNativeChangedRuntimeDisablesAdmissionAndAccounting() public {
        vm.etch(HOOK, hex"00"); vm.expectRevert(); pools.accounting(POOL);
        vm.expectRevert(); manager.mint(POOL, 117000, 119000, 0.01 ether, 2000 ether, 1, block.timestamp + 100);
    }
    function testSelectedNativeMutablePayoutSettingsDoNotTrapCustody() public {
        // Simulate supported creator-recipient/buyback changes without altering frozen terms.
        vm.mockCall(HOOK, abi.encodeWithSignature("launches(bytes32)", POOL), abi.encode(
            true, false, ZZZ, address(0), address(0x123), address(0x456), address(0x789),
            uint16(0), uint16(3000), uint16(5000), uint16(100), uint16(300), true
        ));
        assertEq(pools.accounting(POOL).key.currency0, WETH); assertEq(pools.nativeAsset(POOL), WETH);
        uint256 id = _mint(); manager.collect(POOL, id, block.timestamp + 100); manager.close(POOL, id, block.timestamp + 100);
        assertEq(address(manager).balance, 0);
    }
    function testSelectedNativeProtocolFeeObservationDoesNotTrapCustody() public {
        uint256 id = _mint();
        (uint160 price, int24 tick,, uint24 lpFee) = IStateViewMinimal(STATE).getSlot0(POOL);
        vm.mockCall(STATE, abi.encodeWithSelector(IStateViewMinimal.getSlot0.selector, POOL),
            abi.encode(price, tick, uint24(1000), lpFee));
        assertEq(pools.accounting(POOL).key.currency0, WETH);
        manager.collect(POOL, id, block.timestamp + 100); manager.close(POOL, id, block.timestamp + 100);
        assertEq(address(manager).balance, 0);
    }
    function testSelectedNativeReportedWrapperImplementationChangeFailsClosed() public {
        address proxyAdmin = 0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF;
        vm.mockCall(proxyAdmin, abi.encodeWithSignature("getProxyImplementation(address)", WETH), abi.encode(address(0x123)));
        vm.expectRevert(); pools.accounting(POOL); vm.expectRevert(); pools.nativeAsset(POOL);
    }
    function testSelectedNativeWrapperAdminOwnershipChangeFailsClosed() public {
        address proxyAdmin = 0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF;
        vm.mockCall(proxyAdmin, abi.encodeWithSignature("owner()"), abi.encode(address(0x123)));
        vm.expectRevert(); pools.accounting(POOL); vm.expectRevert(); pools.nativeAsset(POOL);
    }
    function testSelectedNativeReviewedWrapperUpgradeRestoresSameAssetAndCustody() public {
        uint256 id = _mint(); bytes32 oldPolicy = pools.activeWrapperPolicy();
        address proxyAdmin = 0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF;
        address implementation = 0xC6B81b429797E0f555440b70cD99e032D7AE947e;
        address replacement = address(0xF001); vm.etch(replacement, implementation.code);
        // TEST ONLY: simulate an ordinary byte-identical implementation upgrade locally.
        vm.store(WETH, 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc,
            bytes32(uint256(uint160(replacement))));
        vm.expectRevert(); pools.accounting(POOL);
        ZZZPoolRegistry.WrapperPolicy memory policy = ZZZPoolRegistry.WrapperPolicy(proxyAdmin, replacement,
            0x2A153c6A1B66DBc930a8d7017230ab0253005C09, proxyAdmin.codehash, replacement.codehash);
        vm.prank(address(0xBAD)); vm.expectRevert(); pools.approveWrapperPolicy(policy);
        bytes32 next = pools.approveWrapperPolicy(policy); assertTrue(pools.wrapperPolicyExists(oldPolicy));
        vm.expectRevert(); pools.approveWrapperPolicy(policy); vm.expectRevert(); pools.accounting(POOL);
        pools.activateWrapperPolicy(next); assertEq(pools.accounting(POOL).key.currency0, WETH);
        assertEq(pools.nativeAsset(POOL), WETH); assertEq(pools.get(POOL).key.currency0, address(0));
        uint256 beforeWETH = IERC20(WETH).balanceOf(address(this)); (uint256 amount0,) = manager.amounts(id);
        manager.collect(POOL, id, block.timestamp + 100); manager.close(POOL, id, block.timestamp + 100);
        assertEq(IERC20(WETH).balanceOf(address(this)), beforeWETH + amount0);
        assertEq(address(manager).balance, 0); assertEq(pools.activeWrapperPolicy(), next);
    }
    function testSelectedNativeReviewedRenouncedWrapperAdminRestoresCustody() public {
        uint256 id = _mint(); bytes32 previous = pools.activeWrapperPolicy();
        address proxyAdmin = 0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF;
        // TEST ONLY: local Ownable owner-slot transition models a real renunciation.
        vm.store(proxyAdmin, bytes32(0), bytes32(0));
        vm.expectRevert(); pools.accounting(POOL);
        address implementation = 0xC6B81b429797E0f555440b70cD99e032D7AE947e;
        ZZZPoolRegistry.WrapperPolicy memory policy = ZZZPoolRegistry.WrapperPolicy(proxyAdmin, implementation,
            address(0), proxyAdmin.codehash, implementation.codehash);
        bytes32 next = pools.approveWrapperPolicy(policy); pools.activateWrapperPolicy(next);
        assertTrue(pools.wrapperPolicyExists(previous)); assertEq(pools.nativeAsset(POOL), WETH);
        uint256 beforeWETH = IERC20(WETH).balanceOf(address(this)); (uint256 amount0,) = manager.amounts(id);
        manager.collect(POOL, id, block.timestamp + 100); manager.close(POOL, id, block.timestamp + 100);
        assertEq(IERC20(WETH).balanceOf(address(this)), beforeWETH + amount0); assertEq(address(manager).balance, 0);
    }

    // TEST ONLY migration-readiness stub. Real bridge authentication has separate suites.
    function activePlan(uint256) external pure returns (bytes32) { return bytes32(0); }
    struct SharedSystem { ZZZVault vault; ZZZNFT nft; MockVRF vrf; ZZZRewards rewards; ZZZFeeController fees; ZZZMembership membership; }
    function _sharedSystem() private returns (SharedSystem memory s) {
        s.vault = new ZZZVault(address(access), block.chainid, payable(address(0x7EA5)));
        s.nft = canonicalNFT; s.vrf = vrf;
        s.rewards = new ZZZRewards(address(access)); s.fees = new ZZZFeeController(address(access));
        s.membership = new ZZZMembership(address(access));
        access.bind(Ids.VAULT, address(s.vault)); access.bind(Ids.NFT, address(s.nft));
        access.bind(Ids.REWARDS, address(s.rewards)); access.bind(Ids.FEES, address(s.fees));
        access.bind(Ids.MEMBERSHIP, address(s.membership)); access.bind(Ids.MIGRATION, address(this));
        access.bind(Ids.RECEIVER, address(this)); access.bind(Ids.COMPOUNDER, address(this)); access.bind(Ids.BUYBACK, address(this));
        access.setKeeper(address(this), true); s.rewards.addAsset(WETH); s.rewards.addAsset(ZZZ);
        IERC20(WETH).approve(address(s.vault), type(uint256).max); IERC20(ZZZ).approve(address(s.vault), type(uint256).max);
    }
    function _issue(SharedSystem memory s) private returns (uint256 id) {
        id = s.vault.mintDormant{value: 0.05 ether}();
        s.vrf.fulfill(s.nft.requestOf(id), 1, 1); s.nft.finalizeTraits(id);
    }
    event SourceContributed(address indexed owner, uint256 indexed nftId, bytes32 indexed poolId,
        address sourceAsset, uint256 sourceAmount, uint256 grossUSD, address output, uint256 outputAmount, bool increase);

    function _issueForEntry(SharedSystem memory s, address owner) private returns (uint256 id) {
        // TEST ONLY owner balances and VRF fulfillment. All Entry, wrapper,
        // balancing, hook and LP settlement calls execute their actual code.
        vm.deal(owner, 2 ether); deal(ZZZ, owner, 1000 ether);
        vm.prank(owner); id = s.vault.mintDormant{value: 0.05 ether}();
        s.vrf.fulfill(s.nft.requestOf(id), 1, 1); s.nft.finalizeTraits(id);
    }
    function _entryRequest(uint256 id, address source, uint256 amount, bool increase)
        private view returns (ZZZActivationEntry.Request memory) {
        return ZZZActivationEntry.Request(id, POOL, source, amount, bytes32(0), 0, 1, block.timestamp + 100, increase);
    }
    function _hundredUSDNative() private view returns (uint256) {
        uint256 price = oracle.price(WETH);
        return (100 ether * 1 ether + price - 1) / price;
    }
    function _entryExecute(address owner, ZZZActivationEntry entry, ZZZActivationEntry.Request memory request) private {
        if (request.sourceAsset != address(0)) {
            vm.prank(owner); IERC20(request.sourceAsset).approve(address(entry), request.amountIn);
        }
        vm.prank(owner); entry.execute{value: request.sourceAsset == address(0) ? request.amountIn : 0}(request);
    }
    function _entryClean(SharedSystem memory s, ZZZActivationEntry entry, uint256 id) private {
        assertEq(address(entry).balance, 0); assertEq(IERC20(WETH).balanceOf(address(entry)), 0);
        assertEq(IERC20(ZZZ).balanceOf(address(entry)), 0);
        assertEq(IERC20(WETH).allowance(address(entry), address(s.vault)), 0);
        assertEq(IERC20(ZZZ).allowance(address(entry), address(s.vault)), 0);
        assertEq(IERC20(WETH).allowance(address(s.vault), address(manager)), 0);
        assertEq(IERC20(ZZZ).allowance(address(s.vault), address(manager)), 0);
        vm.prank(address(pools)); assertEq(entry.sourceValue(POOL, 1, 2), 0);
        vm.prank(address(s.vault)); vm.expectRevert(); entry.validateOwner(id, bytes32(0));
        _assertApprovalsCleared();
    }
    function _markedLiquidityUSD(uint256 lp, uint128 liquidity) private view returns (uint256) {
        // Independently mark the added liquidity at the final real pool price.
        // Using the liquidity increment avoids counting incumbent repricing as
        // new contribution value; these remain synthetic USD feed observations.
        (int24 lower, int24 upper) = manager.ticks(lp);
        uint160 price = manager.spot(POOL);
        uint160 a = TickMath.getSqrtPriceAtTick(lower); uint160 b = TickMath.getSqrtPriceAtTick(upper);
        uint256 amount0; uint256 amount1;
        if (price <= a) amount0 = SqrtPriceMath.getAmount0Delta(a, b, liquidity, false);
        else if (price >= b) amount1 = SqrtPriceMath.getAmount1Delta(a, b, liquidity, false);
        else {
            amount0 = SqrtPriceMath.getAmount0Delta(price, b, liquidity, false);
            amount1 = SqrtPriceMath.getAmount1Delta(a, price, liquidity, false);
        }
        return oracle.value(WETH, amount0) + oracle.value(ZZZ, amount1);
    }
    function testSelectedNativeEntryETHActivationBindsOriginalOwnerAndGrossBudget() public {
        SharedSystem memory s = _sharedSystem(); address owner = address(0xA11CE); uint256 id = _issueForEntry(s, owner);
        ZZZActivationEntry entry = pools.activationEntry(); uint256 amount = _hundredUSDNative();
        uint256 gross = oracle.value(WETH, amount); uint256 nativeBefore = owner.balance;
        uint256 zzzBefore = IERC20(ZZZ).balanceOf(owner);
        assertGe(gross, 100 ether); assertEq(s.nft.royaltyRewards().weightOf(id), 0);
        vm.expectEmit(true, true, true, true, address(entry));
        emit SourceContributed(owner, id, POOL, address(0), amount, gross, WETH, amount, false);
        _entryExecute(owner, entry, _entryRequest(id, address(0), amount, false));
        uint256 bucket = s.vault.nftBucket(id); Position memory p = s.vault.group(bucket);
        assertEq(owner.balance, nativeBefore - amount); assertEq(IERC20(ZZZ).balanceOf(owner), zzzBefore);
        assertEq(IERC20(WETH).balanceOf(owner), 0); assertEq(s.nft.ownerOf(id), owner);
        assertEq(s.vault.contributionUSD(id), gross); assertEq(p.depositUSD, gross);
        assertGe(_markedLiquidityUSD(p.lpTokenId, positions.getPositionLiquidity(p.lpTokenId)), gross - gross / 100);
        assertEq(positions.ownerOf(p.lpTokenId), address(s.vault)); assertEq(s.vault.bucketCount(), 1);
        assertEq(s.membership.totalEligible(), 1); assertGt(s.nft.royaltyRewards().weightOf(id), 0);
        _entryClean(s, entry, id);
    }
    function testSelectedNativeEntryZZZActivationDeploysAtLeastNinetyNinePercent() public {
        SharedSystem memory s = _sharedSystem(); address owner = address(0xA11CE); uint256 id = _issueForEntry(s, owner);
        ZZZActivationEntry entry = pools.activationEntry(); uint256 amount = 100 ether;
        uint256 gross = oracle.value(ZZZ, amount); uint256 zzzBefore = IERC20(ZZZ).balanceOf(owner);
        uint256 nativeBefore = owner.balance;
        // ERC20 approval is a separate owner transaction, before expecting the
        // Entry operation's event; expectEmit checks the next external call.
        vm.prank(owner); IERC20(ZZZ).approve(address(entry), amount);
        vm.expectEmit(true, true, true, true, address(entry));
        emit SourceContributed(owner, id, POOL, ZZZ, amount, gross, ZZZ, amount, false);
        vm.prank(owner); entry.execute(_entryRequest(id, ZZZ, amount, false));
        uint256 bucket = s.vault.nftBucket(id); Position memory p = s.vault.group(bucket);
        assertEq(gross, 100 ether); assertEq(IERC20(ZZZ).balanceOf(owner), zzzBefore - amount);
        assertEq(owner.balance, nativeBefore); assertEq(IERC20(ZZZ).allowance(owner, address(entry)), 0);
        assertEq(s.nft.ownerOf(id), owner); assertEq(s.vault.contributionUSD(id), gross);
        assertEq(p.depositUSD, gross); assertEq(positions.ownerOf(p.lpTokenId), address(s.vault));
        assertGe(_markedLiquidityUSD(p.lpTokenId, positions.getPositionLiquidity(p.lpTokenId)), 99 ether);
        assertEq(s.membership.totalEligible(), 1); assertGt(s.nft.royaltyRewards().weightOf(id), 0);
        _entryClean(s, entry, id);
    }
    function testSelectedNativeEntryNativeAndZZZTopUpsPreserveOneLPAndMarginalBudget() public {
        SharedSystem memory s = _sharedSystem(); address owner = address(0xA11CE); uint256 id = _issueForEntry(s, owner);
        ZZZActivationEntry entry = pools.activationEntry(); uint256 nativeAmount = _hundredUSDNative();
        uint256 totalGross = oracle.value(WETH, nativeAmount);
        _entryExecute(owner, entry, _entryRequest(id, address(0), nativeAmount, false));
        uint256 bucket = s.vault.nftBucket(id); uint256 lp = s.vault.group(bucket).lpTokenId;
        uint256 next = positions.nextTokenId(); uint256 royaltyWeight = s.nft.royaltyRewards().weightOf(id);
        for (uint256 i; i < 2; ++i) {
            Position memory beforePosition = s.vault.group(bucket);
            uint128 beforeLiquidity = positions.getPositionLiquidity(lp); uint256 beforeShares = s.vault.sharesOf(id);
            address source = i == 0 ? ZZZ : address(0); uint256 amount = i == 0 ? 100 ether : nativeAmount;
            uint256 gross = oracle.value(i == 0 ? ZZZ : WETH, amount);
            uint256 oldIdle = oracle.value(WETH, beforePosition.idle0) + oracle.value(ZZZ, beforePosition.idle1);
            _entryExecute(owner, entry, _entryRequest(id, source, amount, true)); totalGross += gross;
            uint128 addedLiquidity = positions.getPositionLiquidity(lp) - beforeLiquidity;
            assertGe(_markedLiquidityUSD(lp, addedLiquidity), oldIdle + gross - gross / 100);
            assertEq(s.vault.group(bucket).lpTokenId, lp); assertEq(positions.nextTokenId(), next);
            assertGt(s.vault.sharesOf(id), beforeShares); assertEq(s.vault.contributionUSD(id), totalGross);
            assertEq(s.vault.group(bucket).depositUSD, totalGross); assertEq(s.vault.bucketCount(), 1);
            assertEq(s.membership.totalEligible(), 1); assertEq(s.nft.royaltyRewards().weightOf(id), royaltyWeight);
            assertEq(s.nft.ownerOf(id), owner); _entryClean(s, entry, id);
        }
    }
    function testSelectedNativeEntryFailedLiquidityGuardRollsBackOwnerFundsAndVenue() public {
        SharedSystem memory s = _sharedSystem(); address owner = address(0xA11CE); uint256 id = _issueForEntry(s, owner);
        ZZZActivationEntry entry = pools.activationEntry(); uint256 amount = _hundredUSDNative();
        ZZZActivationEntry.Request memory request = _entryRequest(id, address(0), amount, false);
        request.minimumLiquidity = type(uint128).max;
        uint256 nativeBefore = owner.balance; uint160 priceBefore = manager.spot(POOL); uint256 next = positions.nextTokenId();
        vm.prank(owner); vm.expectRevert(bytes4(keccak256("Slippage()"))); entry.execute{value: amount}(request);
        assertEq(owner.balance, nativeBefore); assertEq(manager.spot(POOL), priceBefore); assertEq(positions.nextTokenId(), next);
        assertEq(s.vault.nftBucket(id), 0); assertEq(s.vault.bucketCount(), 0); assertEq(s.vault.sharesOf(id), 0);
        assertEq(s.vault.contributionUSD(id), 0); assertEq(s.membership.totalEligible(), 0);
        assertEq(s.nft.royaltyRewards().weightOf(id), 0); assertEq(s.nft.ownerOf(id), owner); _entryClean(s, entry, id);

        request.minimumLiquidity = 1; _entryExecute(owner, entry, request);
        uint256 bucket = s.vault.nftBucket(id); Position memory p = s.vault.group(bucket);
        uint128 liquidityBefore = positions.getPositionLiquidity(p.lpTokenId); uint256 sharesBefore = s.vault.sharesOf(id);
        uint256 contributionBefore = s.vault.contributionUSD(id); uint256 zzzBefore = IERC20(ZZZ).balanceOf(owner);
        priceBefore = manager.spot(POOL); next = positions.nextTokenId();
        request = _entryRequest(id, ZZZ, 100 ether, true); request.minimumLiquidity = type(uint128).max;
        vm.prank(owner); IERC20(ZZZ).approve(address(entry), request.amountIn);
        vm.prank(owner); vm.expectRevert(bytes4(keccak256("Slippage()"))); entry.execute(request);
        assertEq(IERC20(ZZZ).balanceOf(owner), zzzBefore); assertEq(IERC20(ZZZ).allowance(owner, address(entry)), request.amountIn);
        assertEq(manager.spot(POOL), priceBefore); assertEq(positions.nextTokenId(), next);
        assertEq(positions.getPositionLiquidity(p.lpTokenId), liquidityBefore); assertEq(s.vault.sharesOf(id), sharesBefore);
        assertEq(s.vault.contributionUSD(id), contributionBefore); assertEq(keccak256(abi.encode(s.vault.group(bucket))), keccak256(abi.encode(p)));
        assertEq(s.membership.totalEligible(), 1); assertEq(s.nft.ownerOf(id), owner); _entryClean(s, entry, id);
    }
    function testSelectedNativeTwoNFTsShareOneLPAndFundedRewards() public {
        SharedSystem memory s = _sharedSystem(); uint256 first = _issue(s);
        // ZZZ-only entry is balanced into actual ETH/ZZZ; Vault enforces the net contribution budget.
        s.vault.activate(first, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 bucket = s.vault.nftBucket(first); uint256 lp = s.vault.group(bucket).lpTokenId;
        assertEq(s.vault.group(bucket).homeToken0, WETH); assertEq(s.vault.group(bucket).homeToken1, ZZZ);
        assertEq(positions.ownerOf(lp), address(s.vault));
        address inbox = s.fees.createRewardReceiver(bucket, WETH);
        (bool paid,) = inbox.call{value: 0.001 ether}(""); assertTrue(paid);
        uint256 second = _issue(s); uint256 next = positions.nextTokenId();
        s.vault.activate(second, POOL, 0, 200 ether, 1, block.timestamp + 100);
        assertEq(s.vault.nftBucket(second), bucket); assertEq(s.vault.group(bucket).lpTokenId, lp);
        assertEq(positions.nextTokenId(), next); assertEq(s.vault.bucketCount(), 1); assertEq(s.membership.totalEligible(), 2);
        assertEq(s.rewards.claimable(second, WETH), 0);
        uint256 owed = s.rewards.claimable(first, WETH); assertGe(owed, 0.0009 ether - 2); assertLe(owed, 0.0009 ether);
        uint256 sharesBefore = s.vault.sharesOf(first);
        s.vault.increase(first, 0, 200 ether, 1, block.timestamp + 100);
        assertGt(s.vault.sharesOf(first), sharesBefore); assertEq(s.membership.totalEligible(), 2);
        assertEq(s.vault.group(bucket).lpTokenId, lp); assertEq(positions.nextTokenId(), next);
        uint256 beforeWETH = IERC20(WETH).balanceOf(address(this)); assertEq(s.rewards.claim(first, WETH), owed);
        assertEq(IERC20(WETH).balanceOf(address(this)), beforeWETH + owed);
        assertEq(IERC20(WETH).allowance(address(s.vault), address(manager)), 0);
        assertEq(IERC20(ZZZ).allowance(address(s.vault), address(manager)), 0); _assertApprovalsCleared();
    }
    function testSelectedNativeOneBucketRebalancePreservesBothNFTShares() public {
        SharedSystem memory s = _sharedSystem(); uint256 first = _issue(s);
        s.vault.activate(first, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 second = _issue(s); s.vault.activate(second, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 bucket = s.vault.nftBucket(first); uint256 lp = s.vault.group(bucket).lpTokenId;
        uint256 shares0 = s.vault.sharesOf(first); uint256 shares1 = s.vault.sharesOf(second);
        // TEST ONLY force the policy decision: custody/accounting, not trigger economics, is under test.
        vm.mockCall(address(strategy), abi.encodeWithSignature("needsRebalance(uint256)", bucket), abi.encode(true));
        uint256 next = positions.nextTokenId(); s.vault.rebalance(bucket, 1, block.timestamp + 100);
        assertEq(s.vault.group(bucket).lpTokenId, next); assertEq(positions.nextTokenId(), next + 1);
        assertEq(positions.ownerOf(next), address(s.vault)); assertEq(s.vault.sharesOf(first), shares0);
        assertEq(s.vault.sharesOf(second), shares1); assertEq(s.vault.bucketTotalShares(bucket), shares0 + shares1);
        vm.expectRevert(); positions.ownerOf(lp); _assertApprovalsCleared();
    }
    function testSelectedNativeDisabledSourceVaultMigrationRetainsPriceGuard() public {
        SharedSystem memory s = _sharedSystem(); uint256 first = _issue(s);
        s.vault.activate(first, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 bucket = s.vault.nftBucket(first); uint256 lp = s.vault.group(bucket).lpTokenId;
        PoolConfig memory c = pools.get(POOL); c.operationsEnabled = false; c.depositsEnabled = false; pools.configureNative(c);
        vm.expectRevert(); strategy.validatePrice(POOL); assertGt(strategy.validateExitPrice(POOL), 0);
        // The authenticated migration module is represented by this test-only stub.
        (uint256 amount0, uint256 amount1) = s.vault.releaseForMigration(bucket, bytes32(uint256(1)), block.timestamp + 100);
        assertGt(amount0, 0); assertGt(amount1, 0); assertEq(uint8(s.vault.group(bucket).status), uint8(PositionStatus.Outbound));
        vm.expectRevert(); positions.ownerOf(lp); _assertApprovalsCleared();
    }
    function testSelectedNativeStaleOracleBlocksVaultExitUntilReviewedFeedReplacement() public {
        SharedSystem memory s = _sharedSystem(); uint256 first = _issue(s);
        s.vault.activate(first, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 bucket = s.vault.nftBucket(first); uint256 lp = s.vault.group(bucket).lpTokenId;
        uint256 ethPrice = oracle.price(WETH); uint256 zzzPrice = oracle.price(ZZZ);
        PoolConfig memory c = pools.get(POOL); c.operationsEnabled = false; c.depositsEnabled = false; pools.configureNative(c);
        vm.warp(block.timestamp + 1 days + 1);
        vm.expectRevert(); s.vault.releaseForMigration(bucket, bytes32(uint256(1)), block.timestamp + 100);
        assertEq(positions.ownerOf(lp), address(s.vault)); assertEq(uint8(s.vault.group(bucket).status), uint8(PositionStatus.Active));
        // Mock governance authorizes replacements here; real sealed governance is timelocked.
        oracle.setFeed(WETH, address(new MockFeed(8, int256(ethPrice / 1e10))), 1 days);
        oracle.setFeed(ZZZ, address(new MockFeed(8, int256(zzzPrice / 1e10))), 1 days);
        s.vault.releaseForMigration(bucket, bytes32(uint256(1)), block.timestamp + 100);
        assertEq(uint8(s.vault.group(bucket).status), uint8(PositionStatus.Outbound)); vm.expectRevert(); positions.ownerOf(lp);
    }
    function _parkingRequest(SharedSystem memory s, ZZZMigration migration, uint256 bucket)
        private view returns (ZZZMigration.ParkingRequest memory r) {
        Position memory p = s.vault.group(bucket);
        r.bucketId = bucket; r.poolId = p.poolId; r.lpTokenId = p.lpTokenId;
        r.totalShares = s.vault.bucketTotalShares(bucket); r.depositUSD = p.depositUSD;
        r.custodyEpoch = migration.custodyEpoch(bucket); r.nonce = migration.parkingNonce(bucket);
        r.token0 = WETH; r.token1 = ZZZ;
        (uint256 amount0, uint256 amount1) = manager.amounts(p.lpTokenId);
        r.minimum0 = uint128(amount0); r.minimum1 = uint128(amount1);
        r.deadline = block.timestamp + 100; r.reviewHash = keccak256("reviewed-actual-native-pool-close");
    }
    function testSelectedNativePausedParkingWorksWithStaleFeedsAndBrokenCreatorInbox() public {
        SharedSystem memory s = _sharedSystem(); uint256 id = _issue(s);
        s.vault.activate(id, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 bucket = s.vault.nftBucket(id); uint256 shares = s.vault.sharesOf(id);
        address inbox = s.fees.createRewardReceiver(bucket, WETH);
        (bool paid,) = inbox.call{value: 0.001 ether}(""); assertTrue(paid); s.fees.syncExternal(bucket);
        uint256 claimable = s.rewards.claimable(id, WETH); uint256 compound = s.fees.compoundBalance(bucket, WETH);
        (paid,) = inbox.call{value: 0.001 ether}(""); assertTrue(paid);
        vm.mockCallRevert(inbox, abi.encodeWithSignature("sync()"), abi.encodePacked("creator inbox unavailable"));
        ZZZMigration migration = new ZZZMigration(address(access)); access.bind(Ids.MIGRATION, address(migration));
        vm.warp(block.timestamp + 1 days + 1); vm.expectRevert(); oracle.price(WETH);
        ZZZMigration.ParkingRequest memory r = _parkingRequest(s, migration, bucket);
        Position memory beforePosition = s.vault.group(bucket);
        vm.deal(address(manager), 17); access.setPaused(true); migration.park(r);
        Position memory parked = s.vault.group(bucket);
        assertEq(uint8(parked.status), uint8(PositionStatus.Parked)); assertEq(parked.lpTokenId, 0);
        assertEq(parked.idle0 - beforePosition.idle0, r.minimum0); assertEq(parked.idle1 - beforePosition.idle1, r.minimum1);
        assertEq(s.fees.compoundBalance(bucket, WETH), compound); assertEq(inbox.balance, 0.001 ether);
        assertEq(s.fees.totalExternalFunded(bucket, WETH), 0.001 ether);
        assertEq(s.vault.sharesOf(id), shares); assertTrue(s.membership.eligible(id));
        assertEq(s.rewards.claim(id, WETH), claimable); assertEq(address(manager).balance, 17);
        assertEq(s.vault.group(bucket).idle0, parked.idle0); vm.expectRevert(); positions.ownerOf(r.lpTokenId);
        _assertApprovalsCleared();
    }
    function testSelectedNativeParkingMinimaExcludeCompoundAndUnattributedVaultDonations() public {
        SharedSystem memory s = _sharedSystem(); uint256 id = _issue(s);
        s.vault.activate(id, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 bucket = s.vault.nftBucket(id); address inbox = s.fees.createRewardReceiver(bucket, WETH);
        (bool paid,) = inbox.call{value: 0.001 ether}(""); assertTrue(paid); s.fees.syncExternal(bucket);
        uint256 compound = s.fees.compoundBalance(bucket, WETH); assertGt(compound, 0);
        assertTrue(IERC20(WETH).transfer(address(s.vault), 1 ether));
        ZZZMigration migration = new ZZZMigration(address(access)); access.bind(Ids.MIGRATION, address(migration));
        ZZZMigration.ParkingRequest memory r = _parkingRequest(s, migration, bucket); ++r.minimum0;
        uint256 beforeWETH = IERC20(WETH).balanceOf(address(s.vault)); access.setPaused(true);
        vm.expectRevert(); migration.park(r);
        assertEq(migration.parkingNonce(bucket), 0); assertEq(positions.ownerOf(r.lpTokenId), address(s.vault));
        assertEq(s.vault.group(bucket).lpTokenId, r.lpTokenId); assertEq(IERC20(WETH).balanceOf(address(s.vault)), beforeWETH);
        assertEq(s.fees.compoundBalance(bucket, WETH), compound); _assertApprovalsCleared();
    }
    function testSelectedNativeParkedResumeRequiresFreshFeedsAndPreservesAttachedShares() public {
        SharedSystem memory s = _sharedSystem(); uint256 id = _issue(s);
        s.vault.activate(id, POOL, 0, 200 ether, 1, block.timestamp + 100);
        uint256 bucket = s.vault.nftBucket(id); uint256 shares = s.vault.sharesOf(id);
        uint256 ethPrice = oracle.price(WETH); uint256 zzzPrice = oracle.price(ZZZ);
        ZZZMigration migration = new ZZZMigration(address(access)); access.bind(Ids.MIGRATION, address(migration));
        vm.warp(block.timestamp + 1 days + 1); ZZZMigration.ParkingRequest memory r = _parkingRequest(s, migration, bucket);
        access.setPaused(true); migration.park(r); Position memory parked = s.vault.group(bucket); access.setPaused(false);
        vm.expectRevert(); migration.resume(bucket, POOL, 1, block.timestamp + 100);
        assertEq(s.vault.group(bucket).lpTokenId, 0); assertEq(s.vault.group(bucket).idle0, parked.idle0);
        oracle.setFeed(WETH, address(new MockFeed(8, int256(ethPrice / 1e10))), 1 days);
        oracle.setFeed(ZZZ, address(new MockFeed(8, int256(zzzPrice / 1e10))), 1 days);
        migration.resume(bucket, POOL, 1, block.timestamp + 100);
        Position memory resumed = s.vault.group(bucket);
        assertEq(uint8(resumed.status), uint8(PositionStatus.Active)); assertGt(resumed.lpTokenId, 0);
        assertTrue(resumed.lpTokenId != r.lpTokenId); assertEq(positions.ownerOf(resumed.lpTokenId), address(s.vault));
        assertEq(s.vault.sharesOf(id), shares); assertTrue(s.membership.eligible(id)); _assertApprovalsCleared();
    }
    function onERC721Received(address, address, uint256, bytes calldata) external pure override returns (bytes4) {
        return IERC721Receiver.onERC721Received.selector;
    }
}
