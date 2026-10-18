// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {Ids, Position, PositionStatus} from "../src/libraries/ZZZTypes.sol";

/// @notice Integrated maximum-supply rights/accounting exercise. Real Vault,
/// NFT, Membership, Rewards, FeeController, Compounder, Buyback, royalty ledger
/// and claim router; TEST-ONLY access, feed, VRF, ERC20s and liquidity venue.
/// Receipts below are deliberately funded fixtures, never evidence of Pons or
/// marketplace payment. No bridge, real price, live randomness or MEV claim.
contract CollectionScaleTest is PooledVaultFixture {
    uint256 private constant COUNT = 1000;
    uint256 private constant LOCAL_GAS_BUDGET = 12_000_000;
    // Fixed regression allowance for constant-size paths, not permission for
    // an NFT-count loop. Cold access and zero/nonzero storage cases can differ.
    uint256 private constant SCALING_ALLOWANCE = 100_000;
    uint256[] private ids;
    address[] private holders;
    uint256[] private principal;
    bytes32[] private traits;
    MockToken private stable;
    ZZZRoyaltyRewards private royalties;
    ZZZClaimRouter private router;
    uint256 private totalPrincipal;
    uint256 private totalWeight;

    struct GasMeasurements {
        uint256 activation;
        uint256 oneAssetClaim;
        uint256 mixedBatch;
        uint256 rebalance;
        uint256 compound;
    }

    function _holder(uint256 ordinal) private pure returns (address) {
        // Ten NFTs share a wallet; the other 990 start with distinct owners.
        return address(uint160(0x100000 + (ordinal < 10 ? 0 : ordinal)));
    }

    function _traits(uint256 id) private view returns (bytes32) {
        return keccak256(abi.encode(nft.rarityOf(id), nft.paletteOf(id), nft.patternOf(id), nft.colorOf(id)));
    }

    function _prepareRoyaltyAssets() private {
        royalties = nft.royaltyRewards();
        router = nft.claimRouter();
        stable = new MockToken(6);
        // The same t0 asset enters separate LP and royalty ledgers, so their
        // backing cannot accidentally be conflated by a currency-only model.
        nft.addRoyaltyAsset(address(t0));
        nft.addRoyaltyAsset(address(stable));
    }

    function _mintScale(uint256 ordinal, bool varied) private returns (uint256 id) {
        address owner = _holder(ordinal);
        if (ordinal == 0 || ordinal >= 10) _fundUser(owner);
        vm.prank(owner);
        id = vault.mintDormant{value: 0.05 ether}();
        assertEq(id, uint256(keccak256(abi.encode(block.chainid, address(vault), ordinal + 1))));
        assertEq(nft.tokenAtOrdinal(ordinal + 1), id);
        assertEq(nft.mintOrdinalOf(id), ordinal + 1);
        vrf.fulfill(nft.requestOf(id), uint256(keccak256(abi.encode("rarity", ordinal))),
            uint256(keccak256(abi.encode("artwork", ordinal))));
        nft.finalizeTraits(id);
        ids.push(id); holders.push(owner); traits.push(_traits(id));
        uint256 amount = varied ? 50 + (ordinal % 10) * 50 : 100;
        principal.push(amount * 2);
        totalPrincipal += amount * 2;
        totalWeight += uint256(nft.rarityOf(id)) + 1;
        assertEq(vault.nftBucket(id), 0);
        assertEq(vault.sharesOf(id), 0);
        assertFalse(membership.eligible(id));
    }

    function _activateScale(uint256 ordinal) private {
        _activate(holders[ordinal], ids[ordinal], principal[ordinal] / 2, principal[ordinal] / 2);
    }

    function _payNative(uint256 amount) private {
        (bool ok,) = address(royalties).call{value: amount}("");
        assertTrue(ok);
    }

    function _fundRoyalties() private {
        t0.mint(address(royalties), totalWeight * 100);
        stable.mint(address(royalties), totalWeight * 1e6);
        _payNative(totalWeight * 1e12);
    }

    function _mixed(uint256 id) private view returns (ZZZClaimRouter.Claim[] memory requests) {
        requests = new ZZZClaimRouter.Claim[](5);
        requests[0] = ZZZClaimRouter.Claim(id, address(t0), false);
        requests[1] = ZZZClaimRouter.Claim(id, address(t1), false);
        requests[2] = ZZZClaimRouter.Claim(id, address(t0), true);
        requests[3] = ZZZClaimRouter.Claim(id, address(stable), true);
        requests[4] = ZZZClaimRouter.Claim(id, address(0), true);
    }

    function _assertIdentity(uint256 ordinal, uint256 bucket) private view {
        uint256 id = ids[ordinal];
        assertEq(nft.ownerOf(id), holders[ordinal]);
        assertEq(vault.nftBucket(id), bucket);
        assertEq(vault.sharesOf(id), principal[ordinal] * 1e18);
        assertEq(vault.contributionUSD(id), principal[ordinal] * 1e18);
        assertEq(_traits(id), traits[ordinal]);
        assertTrue(membership.eligible(id));
        assertEq(royalties.weightOf(id), uint256(nft.rarityOf(id)) + 1);
        assertEq(uint256(vault.nftStatus(id)), uint256(PositionStatus.Active));
    }

    function _expected(uint256 ordinal) private view returns (uint256[5] memory amounts) {
        uint256 weight = uint256(nft.rarityOf(ids[ordinal])) + 1;
        // Funded LP fees are 40/60 times total original raw contribution.
        // Algebra is independent of on-chain index/checkpoint implementation.
        amounts[0] = principal[ordinal] * 32 + totalPrincipal * 4 / COUNT;
        amounts[1] = principal[ordinal] * 48 + totalPrincipal * 6 / COUNT;
        amounts[2] = weight * 100;
        amounts[3] = weight * 1e6;
        amounts[4] = weight * 1e12;
    }

    function _assertEntitlement(uint256 ordinal) private view {
        uint256[5] memory expected = _expected(ordinal);
        uint256 id = ids[ordinal];
        assertEq(rewards.claimable(id, address(t0)), expected[0]);
        assertEq(rewards.claimable(id, address(t1)), expected[1]);
        assertEq(royalties.claimable(id, address(t0)), expected[2]);
        assertEq(royalties.claimable(id, address(stable)), expected[3]);
        assertEq(royalties.claimable(id, address(0)), expected[4]);
    }

    function _claimEveryNFT() private returns (uint256[5] memory paid) {
        for (uint256 i; i < COUNT; ++i) {
            uint256 id = ids[i]; address owner = holders[i];
            uint256[5] memory expected = _expected(i);
            uint256 before0 = t0.balanceOf(owner);
            uint256 before1 = t1.balanceOf(owner);
            uint256 beforeStable = stable.balanceOf(owner);
            uint256 beforeNative = owner.balance;
            vm.startPrank(owner);
            if (i % 2 == 0) {
                uint256[] memory received = router.claimBatch(_mixed(id));
                for (uint256 a; a < 5; ++a) assertEq(received[a], expected[a]);
            } else {
                assertEq(rewards.claim(id, address(t0)), expected[0]);
                assertEq(rewards.claim(id, address(t1)), expected[1]);
                assertEq(royalties.claim(id, address(t0)), expected[2]);
                assertEq(royalties.claim(id, address(stable)), expected[3]);
                assertEq(royalties.claim(id, address(0)), expected[4]);
            }
            // Repeated mixed claims cannot withdraw either ledger twice.
            uint256[] memory again = router.claimBatch(_mixed(id));
            vm.stopPrank();
            for (uint256 a; a < 5; ++a) { assertEq(again[a], 0); paid[a] += expected[a]; }
            assertEq(t0.balanceOf(owner) - before0, expected[0] + expected[2]);
            assertEq(t1.balanceOf(owner) - before1, expected[1]);
            assertEq(stable.balanceOf(owner) - beforeStable, expected[3]);
            assertEq(owner.balance - beforeNative, expected[4]);
        }
    }

    function testAll1000NFTsPreserveIndependentRightsAndFundedConservation() public {
        // This models many separate users/transactions. Aggregate fixture and
        // payout-loop gas is not a claim that 1,000 claims fit one transaction.
        vm.pauseGasMetering();
        _prepareRoyaltyAssets();
        t0.mint(address(royalties), 23); stable.mint(address(royalties), 41); _payNative(17);
        uint256[3] memory rarityCounts;
        for (uint256 i; i < COUNT; ++i) {
            uint256 id = _mintScale(i, true);
            ++rarityCounts[nft.rarityOf(id)];
            _activateScale(i);
        }
        uint256 bucket = vault.poolBucket(poolId);
        assertEq(nft.mintedCount(), COUNT); assertEq(nft.remainingToReveal(), 0);
        assertEq(rarityCounts[0], 600); assertEq(rarityCounts[1], 300); assertEq(rarityCounts[2], 100);
        assertEq(totalWeight, 1500); assertEq(royalties.totalWeight(), totalWeight);
        assertEq(membership.totalEligible(), COUNT); assertEq(vault.bucketCount(), 1);
        assertEq(nft.balanceOf(_holder(0)), 10);
        assertEq(vault.bucketTotalShares(bucket), totalPrincipal * 1e18);
        assertEq(vault.group(bucket).depositUSD, totalPrincipal * 1e18);
        assertEq(venue.next(), 2); assertEq(treasury.balance, COUNT * 0.05 ether);
        assertEq(royalties.orphaned(address(t0)), 23); assertEq(royalties.orphaned(address(stable)), 41);
        assertEq(royalties.orphaned(address(0)), 17);
        vm.prank(_holder(0)); vm.expectRevert(); vault.mintDormant{value: 0.05 ether}();

        // Exercise actual receipt-backed creator-inbox allocation and the
        // distinct conventional harvest path without pretending either is live.
        address inbox = fees.createRewardReceiver(bucket, address(0));
        t0.mint(inbox, totalPrincipal * 20); t1.mint(inbox, totalPrincipal * 40);
        fees.syncExternal(bucket);
        venue.setFees(totalPrincipal * 20, totalPrincipal * 20);
        vault.collectFees(bucket, block.timestamp + 100);
        assertEq(fees.totalExternalFunded(bucket, address(t0)), totalPrincipal * 20);
        assertEq(fees.totalExternalFunded(bucket, address(t1)), totalPrincipal * 40);
        assertEq(fees.compoundBalance(bucket, address(t0)), totalPrincipal * 2);
        assertEq(fees.compoundBalance(bucket, address(t1)), totalPrincipal * 3);
        assertEq(fees.buybackBalance(address(t0)), totalPrincipal * 2);
        assertEq(fees.buybackBalance(address(t1)), totalPrincipal * 3);
        _fundRoyalties();
        for (uint256 i; i < COUNT; ++i) { _assertIdentity(i, bucket); _assertEntitlement(i); }

        uint256 oldLP = vault.group(bucket).lpTokenId;
        compounder.compound(bucket, 1, block.timestamp + 100);
        vault.rebalance(bucket, 1, block.timestamp + 100);
        assertTrue(vault.group(bucket).lpTokenId != oldLP);
        vm.expectRevert(); venue.ownerOf(oldLP);
        assertEq(venue.ownerOf(vault.group(bucket).lpTokenId), address(vault));
        assertEq(vault.bucketCount(), 1); assertEq(venue.next(), 3);
        assertEq(vault.bucketTotalShares(bucket), totalPrincipal * 1e18);
        assertEq(fees.compoundBalance(bucket, address(t0)), 0);
        assertEq(fees.compoundBalance(bucket, address(t1)), 0);

        // Direct approved ZZZ burn exercises the real burn supply check. The
        // other currency's reserve stays accounted; no swap price is invented.
        ZZZBuyback buyback = new ZZZBuyback(address(ac), address(t0), 1e30);
        ac.bind(Ids.BUYBACK, address(buyback));
        uint256 supplyBefore = t0.totalSupply();
        uint256 burned = totalPrincipal * 2;
        buyback.execute(address(t0), burned, poolId, block.timestamp + 100);
        assertEq(t0.totalSupply(), supplyBefore - burned);
        assertEq(t0.balanceOf(address(buyback)), 0);
        assertEq(fees.buybackBalance(address(t0)), 0);

        // Transfer several still-funded NFTs to an existing multi-NFT holder.
        // Exact historical entitlement and immutable traits remain token-bound.
        for (uint256 i = 99; i < COUNT; i += 100) {
            address previous = holders[i];
            vm.prank(previous); nft.transferFrom(previous, _holder(0), ids[i]);
            holders[i] = _holder(0);
            vm.prank(previous); vm.expectRevert(); rewards.claim(ids[i], address(t0));
            vm.prank(previous); vm.expectRevert(); royalties.claim(ids[i], address(0));
        }
        for (uint256 i; i < COUNT; ++i) { _assertIdentity(i, bucket); _assertEntitlement(i); }
        uint256[5] memory paid = _claimEveryNFT();
        assertEq(paid[0], totalPrincipal * 36); assertEq(paid[1], totalPrincipal * 54);
        assertEq(paid[2], totalWeight * 100); assertEq(paid[3], totalWeight * 1e6);
        assertEq(paid[4], totalWeight * 1e12);
        assertEq(rewards.liabilities(address(t0)), 0); assertEq(rewards.liabilities(address(t1)), 0);
        assertEq(t0.balanceOf(address(rewards)), 0); assertEq(t1.balanceOf(address(rewards)), 0);
        assertEq(royalties.liabilities(address(t0)), 0); assertEq(royalties.liabilities(address(stable)), 0);
        assertEq(royalties.liabilities(address(0)), 0);
        assertEq(t0.balanceOf(address(royalties)), 23); assertEq(stable.balanceOf(address(royalties)), 41);
        assertEq(address(royalties).balance, 17);
        assertEq(t0.balanceOf(address(fees)), fees.accounted(address(t0)));
        assertEq(t1.balanceOf(address(fees)), fees.accounted(address(t1)));
        assertEq(fees.accounted(address(t0)), 0); assertEq(fees.accounted(address(t1)), totalPrincipal * 3);

        Position memory p = vault.group(bucket);
        // Per-asset equality includes actual balances once, not liabilities plus
        // their backing. Principal, compounded revenue, paid fees, pending burn
        // reserve, burned supply and separate royalty quarantine all reconcile.
        assertEq(venue.a0(p.lpTokenId) + p.idle0 + t0.balanceOf(address(fees)) +
            t0.balanceOf(address(rewards)) + t0.balanceOf(address(royalties)) + paid[0] + paid[2] + burned,
            totalPrincipal / 2 + totalPrincipal * 40 + totalWeight * 100 + 23);
        assertEq(venue.a1(p.lpTokenId) + p.idle1 + t1.balanceOf(address(fees)) +
            t1.balanceOf(address(rewards)) + paid[1], totalPrincipal / 2 + totalPrincipal * 60);
        assertEq(stable.balanceOf(address(royalties)) + paid[3], totalWeight * 1e6 + 41);
        assertEq(address(royalties).balance + paid[4], totalWeight * 1e12 + 17);
        assertEq(address(router).balance, 0); assertEq(t0.balanceOf(address(router)), 0);
        assertEq(t1.balanceOf(address(router)), 0); assertEq(stable.balanceOf(address(router)), 0);
        vm.resumeGasMetering();
    }

    function _cool(address owner) private {
        vm.cool(address(vault.migrationBudget())); vm.cool(address(fees.receiverFactory()));
        (address feed,,,) = oracle.feeds(address(t0));
        vm.cool(address(ac)); vm.cool(address(vault)); vm.cool(address(membership));
        vm.cool(address(rewards)); vm.cool(address(fees)); vm.cool(address(compounder)); vm.cool(address(oracle));
        vm.cool(address(pools)); vm.cool(address(policy)); vm.cool(address(venue)); vm.cool(address(vrf));
        vm.cool(address(royalties)); vm.cool(address(router)); vm.cool(address(nft.metadataRenderer()));
        vm.cool(address(t0)); vm.cool(address(t1)); vm.cool(address(stable)); vm.cool(feed);
        vm.cool(owner); vm.cool(treasury);
        // Helper getters above touch the NFT; cool it after those reads.
        vm.cool(address(nft));
        vm.cool(ac.module(Ids.CANONICAL)); vm.cool(ac.module(Ids.NFT_CANONICAL));
        vm.cool(ac.module(Ids.VAULT_CANONICAL)); vm.cool(ac.module(Ids.FEES_CANONICAL));
        // Reading companion bindings warms the controller; cool it last.
        vm.cool(address(ac));
    }

    function _measureAt(uint256 size) private returns (GasMeasurements memory result) {
        vm.pauseGasMetering();
        delete ids; delete holders; delete principal; delete traits;
        totalPrincipal = 0; totalWeight = 0;
        _fixture(treasury); _prepareRoyaltyAssets();
        for (uint256 i; i < size; ++i) { _mintScale(i, false); if (i + 1 != size) _activateScale(i); }
        uint256 last = size - 1;
        _cool(holders[last]); vm.prank(holders[last]); vm.resumeGasMetering();
        uint256 start = gasleft();
        vault.activate(ids[last], poolId, 100, 100, 1, block.timestamp + 100);
        result.activation = start - gasleft(); vm.pauseGasMetering();
        uint256 bucket = vault.poolBucket(poolId);
        venue.setFees(totalPrincipal * 20, totalPrincipal * 20); vault.collectFees(bucket, block.timestamp + 100);
        _fundRoyalties();

        _cool(holders[last]); vm.prank(holders[last]); vm.resumeGasMetering();
        start = gasleft(); uint256 amount = rewards.claim(ids[last], address(t0));
        result.oneAssetClaim = start - gasleft(); vm.pauseGasMetering(); assertGt(amount, 0);
        ZZZClaimRouter.Claim[] memory requests = _mixed(ids[last]);
        _cool(holders[last]); vm.prank(holders[last]); vm.resumeGasMetering();
        start = gasleft(); uint256[] memory claimed = router.claimBatch(requests);
        result.mixedBatch = start - gasleft(); vm.pauseGasMetering();
        assertEq(claimed[0], 0); for (uint256 i = 1; i < 5; ++i) assertGt(claimed[i], 0);

        _cool(holders[last]); vm.resumeGasMetering(); start = gasleft();
        compounder.compound(bucket, 1, block.timestamp + 100);
        result.compound = start - gasleft(); vm.pauseGasMetering();
        _cool(holders[last]); vm.resumeGasMetering(); start = gasleft();
        vault.rebalance(bucket, 1, block.timestamp + 100);
        result.rebalance = start - gasleft(); vm.pauseGasMetering();
        assertEq(vault.bucketCount(), 1); assertEq(membership.totalEligible(), size);
        assertEq(venue.next(), 3); assertEq(vault.bucketTotalShares(bucket), totalPrincipal * 1e18);
        vm.resumeGasMetering();
    }

    function _bounded(string memory operation, uint256 single, uint256 full) private {
        emit log_named_uint(string.concat("collection.1.", operation), single);
        emit log_named_uint(string.concat("collection.1000.", operation), full);
        assertLt(single, LOCAL_GAS_BUDGET); assertLt(full, LOCAL_GAS_BUDGET);
        assertLe(full, single + SCALING_ALLOWANCE, "NFT population unexpectedly increases bounded path gas");
    }

    function _maximumMixedBatch() private {
        vm.pauseGasMetering();
        address owner = _holder(0);
        ZZZClaimRouter.Claim[] memory requests = new ZZZClaimRouter.Claim[](32);
        uint256 expectedLP;
        uint256 expectedNative;
        for (uint256 i; i < 16; ++i) {
            if (holders[i] != owner) {
                vm.prank(holders[i]); nft.transferFrom(holders[i], owner, ids[i]);
                holders[i] = owner;
            }
            requests[i * 2] = ZZZClaimRouter.Claim(ids[i], address(t0), false);
            requests[i * 2 + 1] = ZZZClaimRouter.Claim(ids[i], address(0), true);
            expectedLP += rewards.claimable(ids[i], address(t0));
            expectedNative += royalties.claimable(ids[i], address(0));
        }
        assertGt(expectedLP, 0); assertGt(expectedNative, 0);
        uint256 previousLP = t0.balanceOf(owner);
        uint256 previousNative = owner.balance;
        _cool(owner); vm.prank(owner); vm.resumeGasMetering();
        uint256 start = gasleft(); uint256[] memory paid = router.claimBatch(requests);
        uint256 used = start - gasleft(); vm.pauseGasMetering();
        emit log_named_uint("collection.1000.claim-32-mixed", used);
        assertLt(used, LOCAL_GAS_BUDGET);
        assertEq(paid.length, 32);
        assertEq(t0.balanceOf(owner) - previousLP, expectedLP);
        assertEq(owner.balance - previousNative, expectedNative);
        assertEq(address(router).balance, 0); assertEq(t0.balanceOf(address(router)), 0);
        vm.resumeGasMetering();
    }

    /// @notice Cold execution-gas deltas exclude fixture/loop setup, intrinsic
    /// and calldata gas and refunds. Fake venue fees are not real Uniswap costs.
    function testColdOperationsAtOneAnd1000NFTsStayBounded() public {
        GasMeasurements memory single = _measureAt(1);
        GasMeasurements memory full = _measureAt(COUNT);
        _bounded("activation", single.activation, full.activation);
        _bounded("claim-one-asset", single.oneAssetClaim, full.oneAssetClaim);
        _bounded("claim-five-mixed", single.mixedBatch, full.mixedBatch);
        _bounded("shared-rebalance", single.rebalance, full.rebalance);
        _bounded("shared-compound", single.compound, full.compound);
        _maximumMixedBatch();
    }
}
