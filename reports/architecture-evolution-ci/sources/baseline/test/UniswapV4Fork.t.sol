// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZRewardReceiver} from "../src/ZZZRewardReceiver.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";
import {Ids, PoolKey, PoolConfig, Position} from "../src/libraries/ZZZTypes.sol";
import {IPositionManagerMinimal, IStateViewMinimal, IPriceFeed, IBurnable} from "../src/interfaces/IZZZ.sol";
import {MockAccess, MockFeed} from "./mocks/Mocks.sol";
import {MockVRF} from "./mocks/MockVRF.sol";

interface IForkPoolInitializer {
    function initialize(PoolKey calldata key, uint160 sqrtPriceX96) external returns (int24);
}

// Pinned Foundry v1.4.4 supports this cheatcode; the older pinned forge-std ABI omits it.
interface IForkHeaderVm {
    function getRawBlockHeader(uint256 blockNumber) external returns (bytes memory);
}

interface IForkWETH {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
}

interface IForkPermit2Allowance {
    function allowance(address owner, address token, address spender)
        external view returns (uint160 amount, uint48 expiration, uint48 nonce);
}

interface IForkPonsHook {
    function launches(bytes32 poolId) external view returns (
        bool registered, bool memecoinIsCurrency0, address memecoin, address quoteToken,
        address creator, address buybackCreatorRecipient, address protocolFeeRecipient,
        uint16 creatorTaxBps, uint16 protocolFeeShareBps, uint16 buybackBurnBps,
        uint16 hookFeeBps, uint16 maxInternalPriceImpactBps, bool buybackEnabled
    );
}

contract ForkRewardAssetAllowlist {
    function isAsset(address) external pure returns (bool) { return true; }
}

/// @notice Network integration tests, enabled explicitly with RUN_ROBINHOOD_FORK_TESTS=true.
/// The selected live native-ETH/Pons pool is verified and rejected by the current candidate.
/// Typed adapter flows use a DIFFERENT hookless pool initialized only on the local fork.
/// Real Uniswap settlement, WETH and ZZZ are used; access and the two $1 valuation feeds
/// are test scaffolding. This suite does not establish a safe production ZZZ price source,
/// approve an alternative market, execute real transactions or prove Pons fee entitlement.
contract UniswapV4ForkTest is Test, IERC721Receiver {
    uint256 private constant FORK_BLOCK = 88_544_093;
    bytes32 private constant FORK_HASH = 0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490;
    address private constant CORE = 0x8366a39CC670B4001A1121B8F6A443A643e40951;
    address private constant POSM = 0x58daec3116aae6D93017bAAea7749052E8a04fA7;
    address private constant STATE = 0xF3334192D15450CdD385c8B70e03f9A6bD9E673b;
    address private constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;
    address private constant WETH = 0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73;
    address private constant ZZZ = 0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    address private constant HOOK = 0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044;
    address private constant ETH_USD = 0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9;
    bytes32 private constant SELECTED_POOL = 0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f;

    MockAccess private access;
    ZZZLiquidityManager private manager;
    ZZZPoolRegistry private pools;
    IPositionManagerMinimal private positions;
    ZZZNFT private canonicalNFT;
    MockVRF private vrf;
    bytes32 private testPool;

    function setUp() public {
        if (!vm.envOr("RUN_ROBINHOOD_FORK_TESTS", false)) {
            vm.skip(true, "Opt-in real-network fork suite; excluded from offline unit verification");
            return;
        }
        string memory rpc = vm.envOr("ROBINHOOD_RPC_URL", string(""));
        require(bytes(rpc).length != 0, "ROBINHOOD_RPC_URL required for explicit fork verification");
        vm.createSelectFork(rpc, FORK_BLOCK);
        assertEq(block.chainid, 4663, "Incorrect fork chain");
        assertEq(block.number, FORK_BLOCK, "Incorrect fork block");
        bytes memory header = IForkHeaderVm(address(vm)).getRawBlockHeader(FORK_BLOCK);
        assertEq(keccak256(header), FORK_HASH, "Pinned block hash changed");
        // Runtime hashes were independently read at the pinned block (current-pool.json).
        assertEq(CORE.codehash, 0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626);
        assertEq(POSM.codehash, 0xc873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2);
        assertEq(STATE.codehash, 0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6);
        assertEq(PERMIT2.codehash, 0x5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca);
        assertEq(WETH.codehash, 0x5706be52f64875fee65a2cec0d80e47a23d8793cbe85d214b48445e2d05f5353);
        assertEq(ZZZ.codehash, 0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597);
        assertEq(HOOK.codehash, 0xc21b1e6c1b45403e81a581f22ed6d9c747997af1cfdac1b1dc9f4b1d346a10db);
        assertEq(ETH_USD.codehash, 0xbd6f524cdc4268b6bd1bb6f77a8821faeea9c52ee9e0afa0b6d948ce82c966c2);
        positions = IPositionManagerMinimal(POSM);
        assertEq(positions.poolManager(), CORE);
        assertEq(positions.permit2(), PERMIT2);
        assertEq(IStateViewMinimal(STATE).poolManager(), CORE);

        access = new MockAccess();
        canonicalNFT = new ZZZNFT(address(access), "ipfs://");
        vrf = new MockVRF();
        canonicalNFT.configureRandomness(address(vrf), bytes32(uint256(1)), 1, 3, 500000, false);
        pools = new ZZZPoolRegistry(address(access));
        ZZZOracle oracle = new ZZZOracle(address(access), address(0));
        ZZZStrategy strategy = new ZZZStrategy(address(access));
        // Synthetic feeds belong only to the separate local test pool's reference price.
        oracle.setFeed(WETH, address(new MockFeed(8, 1e8)), 1 days);
        oracle.setFeed(ZZZ, address(new MockFeed(8, 1e8)), 1 days);
        access.bind(Ids.VAULT, address(this));
        access.bind(Ids.POOLS, address(pools));
        access.bind(Ids.ORACLE, address(oracle));
        access.bind(Ids.REWARDS, address(new ForkRewardAssetAllowlist()));
        access.bind(Ids.STRATEGY, address(strategy));
        manager = new ZZZLiquidityManager(address(access), POSM, STATE, CORE, PERMIT2);
        access.bind(Ids.LIQUIDITY, address(manager));

        PoolConfig memory config = _testConfig();
        testPool = pools.configure(config);
        assertTrue(testPool != SELECTED_POOL, "Integration test must not replace the requested market");
        IForkPoolInitializer(CORE).initialize(config.key, uint160(1 << 96));
        access.seal();
        vm.deal(address(this), 100 ether);
        IForkWETH(WETH).deposit{value: 90 ether}();
        // Storage funding applies to the local fork only, without external mint authority.
        deal(ZZZ, address(this), 100 ether);
        IERC20(WETH).approve(address(manager), type(uint256).max);
        IERC20(ZZZ).approve(address(manager), type(uint256).max);
    }

    function _testConfig() private pure returns (PoolConfig memory c) {
        c.key = PoolKey(WETH, ZZZ, 3000, 60, address(0));
        c.depositsEnabled = true;
        c.operationsEnabled = true;
        c.rangeBps = 1000;
        c.triggerBps = 500;
        c.maxSpotDeviationBps = 100;
        c.maxSlippageBps = 100;
        c.minRebalanceInterval = 600;
        c.minDepositUSD = 100 ether;
        c.maxPositionUSD = 100_000 ether;
    }

    function _mint() private returns (uint256 id) {
        (id,,) = manager.mint(testPool, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        positions.approve(address(manager), id);
    }

    function _assertApprovalsCleared() private view {
        assertEq(IERC20(WETH).allowance(address(manager), PERMIT2), 0);
        assertEq(IERC20(ZZZ).allowance(address(manager), PERMIT2), 0);
        (uint160 amount0,,) = IForkPermit2Allowance(PERMIT2).allowance(address(manager), WETH, POSM);
        (uint160 amount1,,) = IForkPermit2Allowance(PERMIT2).allowance(address(manager), ZZZ, POSM);
        assertEq(amount0, 0);
        assertEq(amount1, 0);
    }

    function testPinnedSelectedPoolIdentityAndZeroCoreFees() public view {
        PoolKey memory selected = PoolKey(address(0), ZZZ, 0, 200, HOOK);
        assertEq(keccak256(abi.encode(selected)), SELECTED_POOL);
        (uint160 sqrtPrice, int24 tick, uint24 protocolFee, uint24 lpFee) = IStateViewMinimal(STATE).getSlot0(SELECTED_POOL);
        assertEq(sqrtPrice, 28_985_618_865_899_744_360_092_483_858_059);
        assertEq(tick, 118050);
        assertEq(protocolFee, 0);
        assertEq(lpFee, 0);
        (bool registered,, address meme, address quote, address creator,,, uint16 tax,
            uint16 protocolShare,, uint16 fee,, bool buyback) = IForkPonsHook(HOOK).launches(SELECTED_POOL);
        assertTrue(registered);
        assertEq(meme, ZZZ);
        assertEq(quote, address(0));
        assertEq(creator, 0x698084856F65Bf1B4740E3D0dBA0B57A5B1deBA9);
        assertEq(tax, 0);
        assertEq(protocolShare, 3000);
        assertEq(fee, 100);
        assertFalse(buyback);
    }

    function testCurrentRegistryRejectsSelectedNativeAndHookedPool() public {
        PoolConfig memory c = _testConfig();
        c.key = PoolKey(address(0), ZZZ, 0, 200, HOOK);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        pools.configure(c);
        c.key = PoolKey(WETH, ZZZ, 3000, 60, HOOK);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        pools.configure(c);
    }

    function testRealPositionMintIncreaseAndApprovalReset() public {
        uint256 before0 = IERC20(WETH).balanceOf(address(this));
        uint256 before1 = IERC20(ZZZ).balanceOf(address(this));
        (uint256 id, uint256 spent0, uint256 spent1) = manager.mint(testPool, -600, 600, 10 ether, 10 ether, 1, block.timestamp + 100);
        assertEq(positions.ownerOf(id), address(this));
        assertEq(before0 - IERC20(WETH).balanceOf(address(this)), spent0);
        assertEq(before1 - IERC20(ZZZ).balanceOf(address(this)), spent1);
        assertGt(spent0, 0);
        assertGt(spent1, 0);
        assertEq(IERC20(WETH).balanceOf(address(manager)), 0);
        assertEq(IERC20(ZZZ).balanceOf(address(manager)), 0);
        _assertApprovalsCleared();
        positions.approve(address(manager), id);
        uint128 beforeLiquidity = positions.getPositionLiquidity(id);
        uint256 next = positions.nextTokenId();
        manager.increase(testPool, id, 2 ether, 2 ether, 1, block.timestamp + 100);
        assertGt(positions.getPositionLiquidity(id), beforeLiquidity);
        assertEq(positions.nextTokenId(), next);
        _assertApprovalsCleared();
    }

    function testRealSwapFeeCollectionAndPositionBurn() public {
        uint256 id = _mint();
        uint128 beforeLiquidity = positions.getPositionLiquidity(id);
        uint256 beforeOut = IERC20(ZZZ).balanceOf(address(this));
        uint256 out = manager.swap(testPool, true, 0.01 ether, 0.0099 ether, block.timestamp + 100);
        assertEq(IERC20(ZZZ).balanceOf(address(this)), beforeOut + out);
        assertGe(out, 0.0099 ether);
        uint256 beforeFee = IERC20(WETH).balanceOf(address(this));
        manager.collect(testPool, id, block.timestamp + 100);
        assertGt(IERC20(WETH).balanceOf(address(this)), beforeFee, "Real static LP fee must reach the vault");
        assertEq(positions.getPositionLiquidity(id), beforeLiquidity);
        (uint256 expected0, uint256 expected1) = manager.amounts(id);
        uint256 before0 = IERC20(WETH).balanceOf(address(this));
        uint256 before1 = IERC20(ZZZ).balanceOf(address(this));
        manager.close(testPool, id, block.timestamp + 100);
        assertGe(IERC20(WETH).balanceOf(address(this)) - before0, expected0 * 99 / 100);
        assertGe(IERC20(ZZZ).balanceOf(address(this)) - before1, expected1 * 99 / 100);
        vm.expectRevert();
        positions.ownerOf(id);
        _assertApprovalsCleared();
    }

    function testActualTokenTransferBurnAndNativeWrapRoundTrip() public {
        address recipient = address(0xB0B);
        uint256 beforeRecipient = IERC20(ZZZ).balanceOf(recipient);
        uint256 beforeSupply = IBurnable(ZZZ).totalSupply();
        IERC20(ZZZ).transfer(recipient, 1 ether);
        assertEq(IERC20(ZZZ).balanceOf(recipient), beforeRecipient + 1 ether);
        assertEq(IBurnable(ZZZ).totalSupply(), beforeSupply);
        IBurnable(ZZZ).burn(1 ether);
        assertEq(IBurnable(ZZZ).totalSupply(), beforeSupply - 1 ether);
        uint256 nativeBefore = address(this).balance;
        uint256 wrappedBefore = IERC20(WETH).balanceOf(address(this));
        IForkWETH(WETH).withdraw(1 ether);
        assertEq(address(this).balance, nativeBefore + 1 ether);
        assertEq(IERC20(WETH).balanceOf(address(this)), wrappedBefore - 1 ether);
        IForkWETH(WETH).deposit{value: 1 ether}();
        assertEq(address(this).balance, nativeBefore);
        assertEq(IERC20(WETH).balanceOf(address(this)), wrappedBefore);
    }

    function testActualETHUSDFeedIsPositiveAndCurrentAtPinnedBlock() public view {
        (uint80 round, int256 answer,, uint256 updated, uint80 answeredRound) = IPriceFeed(ETH_USD).latestRoundData();
        assertEq(IPriceFeed(ETH_USD).decimals(), 8);
        assertGt(answer, 0);
        assertGt(round, 0);
        assertGe(answeredRound, round);
        assertGt(updated, 0);
        assertLe(updated, block.timestamp);
        assertLe(block.timestamp - updated, 1 days);
    }

    // TEST ONLY: an empty migration plan. Transport/migration authentication uses
    // real controller/router suites; these tests isolate deployed Uniswap custody.
    function activePlan(uint256) external pure returns (bytes32) { return bytes32(0); }

    struct SharedSystem { ZZZVault vault; ZZZRewards rewards; ZZZFeeController fees; ZZZMembership membership; }

    function _sharedSystem() private returns (SharedSystem memory s) {
        // Seed an independent LP so the first strategy-balancing swap has real
        // market liquidity. All balances and positions exist on the local fork.
        vm.deal(address(this), 200_000 ether);
        IForkWETH(WETH).deposit{value: 150_000 ether}();
        deal(ZZZ, address(this), 150_000 ether);
        manager.mint(testPool, -600, 600, 100_000 ether, 100_000 ether, 1, block.timestamp + 100);
        s.vault = new ZZZVault(address(access), block.chainid, payable(address(0x7EA5)));
        s.rewards = new ZZZRewards(address(access)); s.fees = new ZZZFeeController(address(access));
        s.membership = new ZZZMembership(address(access));
        access.bind(Ids.VAULT, address(s.vault)); access.bind(Ids.NFT, address(canonicalNFT));
        access.bind(Ids.MEMBERSHIP, address(s.membership)); access.bind(Ids.REWARDS, address(s.rewards));
        access.bind(Ids.FEES, address(s.fees)); access.bind(Ids.MIGRATION, address(this));
        access.bind(Ids.RECEIVER, address(this)); access.bind(Ids.BUYBACK, address(this));
        access.bind(Ids.COMPOUNDER, address(this)); access.setKeeper(address(this), true);
        s.rewards.addAsset(WETH); s.rewards.addAsset(ZZZ);
        PoolConfig memory config = _testConfig();
        config.triggerBps = 100; config.maxSpotDeviationBps = 200; config.maxSlippageBps = 200;
        assertEq(pools.configure(config), testPool);
        IERC20(WETH).approve(address(s.vault), type(uint256).max);
        IERC20(ZZZ).approve(address(s.vault), type(uint256).max);
    }

    function _sharedMint(SharedSystem memory s, uint256 amount0, uint256 amount1) private returns (uint256 id) {
        id = s.vault.mintDormant{value: 0.05 ether}();
        _finalizeTraits(id);
        s.vault.activate(id, testPool, amount0, amount1, 1, block.timestamp + 100);
    }

    function _finalizeTraits(uint256 id) private {
        // TEST ONLY local coordinator callback, not a real VRF service request.
        vrf.fulfill(canonicalNFT.requestOf(id), 1, 1);
        canonicalNFT.finalizeTraits(id);
    }

    function _assertSharedApprovalsCleared(SharedSystem memory s) private view {
        _assertApprovalsCleared();
        assertEq(IERC20(WETH).allowance(address(s.vault), address(manager)), 0);
        assertEq(IERC20(ZZZ).allowance(address(s.vault), address(manager)), 0);
        assertEq(IERC20(WETH).allowance(address(s.vault), address(s.fees)), 0);
        assertEq(IERC20(ZZZ).allowance(address(s.vault), address(s.fees)), 0);
        assertEq(IERC20(WETH).allowance(address(s.fees), address(s.rewards)), 0);
        assertEq(IERC20(ZZZ).allowance(address(s.fees), address(s.rewards)), 0);
    }

    function _liquidityValueAtCurrentSpot(uint256 tokenId, uint128 liquidity) private view returns (uint256 value) {
        (int24 lower, int24 upper) = manager.ticks(tokenId);
        uint160 spot = manager.spot(testPool); uint160 a = TickMath.getSqrtPriceAtTick(lower);
        uint160 b = TickMath.getSqrtPriceAtTick(upper);
        if (spot <= a) value = SqrtPriceMath.getAmount0Delta(a, b, liquidity, false);
        else if (spot >= b) value = SqrtPriceMath.getAmount1Delta(a, b, liquidity, false);
        else value = SqrtPriceMath.getAmount0Delta(spot, b, liquidity, false) +
            SqrtPriceMath.getAmount1Delta(a, spot, liquidity, false);
        // This helper is used only while both synthetic feeds remain exactly $1.
    }

    function testRealNativeAndZZZPaymentsFundNFTClaimsWithoutChangingLP() public {
        SharedSystem memory s = _sharedSystem();
        uint256 id = _sharedMint(s, 300 ether, 300 ether);
        uint256 bucket = s.vault.nftBucket(id);
        Position memory prior = s.vault.group(bucket);
        uint256 shares = s.vault.sharesOf(id);
        uint256 contribution = s.vault.contributionUSD(id);
        address inbox = s.fees.createRewardReceiver(bucket, WETH);
        assertEq(ZZZRewardReceiver(payable(inbox)).wrappedNative(), WETH);
        address creator = address(0xC2EA70);
        vm.deal(creator, 1 ether);
        vm.prank(creator);
        (bool paid,) = inbox.call{value: 1 ether}("");
        assertTrue(paid);
        assertTrue(IERC20(ZZZ).transfer(inbox, 100 ether));
        assertEq(s.rewards.claimable(id, WETH), 0);
        assertEq(address(inbox).balance, 1 ether);
        s.fees.syncExternal(bucket);
        assertEq(address(inbox).balance, 0);
        assertEq(IERC20(WETH).balanceOf(inbox), 0);
        assertEq(IERC20(ZZZ).balanceOf(inbox), 0);
        assertEq(s.fees.totalExternalFunded(bucket, WETH), 1 ether);
        assertEq(s.fees.totalExternalFunded(bucket, ZZZ), 100 ether);
        assertEq(s.fees.compoundBalance(bucket, WETH), 0.05 ether);
        assertEq(s.fees.buybackBalance(WETH), 0.05 ether);
        assertEq(s.vault.group(bucket).lpTokenId, prior.lpTokenId);
        assertEq(s.vault.group(bucket).idle0, prior.idle0);
        assertEq(s.vault.group(bucket).idle1, prior.idle1);
        assertEq(s.vault.sharesOf(id), shares);
        assertEq(s.vault.contributionUSD(id), contribution);
        uint256 owed = s.rewards.claimable(id, WETH);
        assertGe(owed, 0.9 ether - 2);
        assertLe(owed, 0.9 ether);
        uint256 before = IERC20(WETH).balanceOf(address(this));
        assertEq(s.rewards.claim(id, WETH), owed);
        assertEq(IERC20(WETH).balanceOf(address(this)), before + owed);
        assertEq(s.rewards.claim(id, WETH), 0);
        assertEq(IERC20(WETH).allowance(inbox, address(s.fees)), 0);
        assertEq(IERC20(ZZZ).allowance(inbox, address(s.fees)), 0);
        _assertSharedApprovalsCleared(s);
    }

    function testRealSharedPoolEntryUsesOneLPAndPostSwapSharePricing() public {
        SharedSystem memory s = _sharedSystem(); uint256 first = _sharedMint(s, 300 ether, 300 ether);
        uint256 bucket = s.vault.nftBucket(first); uint256 tokenId = s.vault.group(bucket).lpTokenId;
        manager.swap(testPool, true, 100 ether, 99 ether, block.timestamp + 100);
        s.vault.collectFees(bucket, block.timestamp + 100);
        uint256 oldClaim = s.rewards.claimable(first, WETH); assertGt(oldClaim, 0, "Actual LP fees must be funded");
        Position memory beforeEntry = s.vault.group(bucket);
        uint256 priorSupply = s.vault.bucketTotalShares(bucket);
        uint128 priorLiquidity = positions.getPositionLiquidity(tokenId);
        uint256 oldLPValue = _liquidityValueAtCurrentSpot(tokenId, priorLiquidity);
        uint256 incumbentIdle = beforeEntry.idle0 + beforeEntry.idle1 +
            s.fees.compoundBalance(bucket, WETH) + s.fees.compoundBalance(bucket, ZZZ);
        uint256 nextPosition = positions.nextTokenId();
        uint256 second = s.vault.mintDormant{value: 0.05 ether}();
        _finalizeTraits(second);
        vm.recordLogs(); s.vault.activate(second, testPool, 310 ether, 290 ether, 1, block.timestamp + 100);
        Vm.Log[] memory logs = vm.getRecordedLogs(); uint256 freshCompound;
        bytes32 allocation = keccak256("FeesAllocated(uint256,address,uint256,uint256)");
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].emitter == address(s.fees) && logs[i].topics[0] == allocation) {
                (uint256 distributed,) = abi.decode(logs[i].data, (uint256, uint256));
                freshCompound += distributed / 20;
            }
        }
        assertEq(s.vault.nftBucket(second), bucket); assertEq(s.vault.group(bucket).lpTokenId, tokenId);
        assertEq(s.vault.group(bucket).lpTokenId, tokenId); assertEq(positions.nextTokenId(), nextPosition);
        assertEq(positions.ownerOf(tokenId), address(s.vault));
        assertEq(s.rewards.claimable(second, WETH), 0); assertEq(s.rewards.claimable(second, ZZZ), 0);
        assertGe(s.rewards.claimable(first, WETH), oldClaim);
        uint256 repricedLP = _liquidityValueAtCurrentSpot(tokenId, priorLiquidity);
        assertTrue(repricedLP != oldLPValue, "Entry swap must exercise incumbent LP repricing");
        (uint256 amount0, uint256 amount1) = manager.amounts(tokenId); Position memory afterEntry = s.vault.group(bucket);
        uint256 incumbentNAV = repricedLP + incumbentIdle + freshCompound;
        uint256 net = amount0 + amount1 + afterEntry.idle0 + afterEntry.idle1 - incumbentNAV;
        assertEq(s.vault.sharesOf(second), Math.mulDiv(priorSupply, net, incumbentNAV));
        assertEq(s.vault.sharesOf(first) + s.vault.sharesOf(second), s.vault.bucketTotalShares(bucket));
        _assertSharedApprovalsCleared(s);
    }

    function testRealSharedPoolRebalanceChangesOneLPAndPreservesAllShares() public {
        SharedSystem memory s = _sharedSystem(); uint256 first = _sharedMint(s, 300 ether, 300 ether);
        uint256 second = _sharedMint(s, 310 ether, 290 ether); uint256 bucket = s.vault.nftBucket(first);
        uint256 firstShares = s.vault.sharesOf(first); uint256 secondShares = s.vault.sharesOf(second);
        uint256 supply = s.vault.bucketTotalShares(bucket); uint256 oldId = s.vault.group(bucket).lpTokenId;
        manager.swap(testPool, true, 100 ether, 99 ether, block.timestamp + 100);
        vm.warp(block.timestamp + 601);
        ZZZOracle(access.module(Ids.ORACLE)).setFeed(WETH, address(new MockFeed(8, 101_100_000)), 1 days);
        assertTrue(ZZZStrategy(access.module(Ids.STRATEGY)).needsRebalance(bucket));
        uint256 next = positions.nextTokenId(); s.vault.rebalance(bucket, 1, block.timestamp + 100);
        uint256 newId = s.vault.group(bucket).lpTokenId; assertEq(newId, next); assertTrue(newId != oldId);
        assertEq(positions.nextTokenId(), next + 1); assertEq(s.vault.group(bucket).lpTokenId, newId);
        assertEq(s.vault.group(bucket).lpTokenId, newId); assertEq(positions.ownerOf(newId), address(s.vault));
        assertEq(s.vault.sharesOf(first), firstShares); assertEq(s.vault.sharesOf(second), secondShares);
        assertEq(s.vault.bucketTotalShares(bucket), supply);
        assertGt(s.rewards.claimable(first, WETH), 0); assertGt(s.rewards.claimable(second, WETH), 0);
        vm.expectRevert(); positions.ownerOf(oldId); _assertSharedApprovalsCleared(s);
    }

    function onERC721Received(address, address, uint256, bytes calldata) external pure override returns (bytes4) {
        return IERC721Receiver.onERC721Received.selector;
    }

    receive() external payable {}
}
