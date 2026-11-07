// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Vm} from "forge-std/Vm.sol";
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
    // Compare two INCUMBENT paths, never first creation versus growth. The
    // allowance is a regression budget, not permission for an NFT-count loop.
    uint256 private constant SCALING_ALLOWANCE = 100_000;
    uint256[] private ids;
    address[] private holders;
    uint256[] private principal;
    uint256[] private weightOffsets;
    uint256[3] private openingRoyalties;
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
        // The same t1 asset enters separate LP and royalty ledgers, so their
        // backing cannot accidentally be conflated by a currency-only model.
        nft.addRoyaltyAsset(address(t1));
        nft.addRoyaltyAsset(address(stable));
    }

    function _mintScale(uint256 ordinal, bool varied) private returns (uint256 id) {
        address owner = _holder(ordinal);
        if (ordinal == 0 || ordinal >= 10) _fundUser(owner);
        bytes32 reviewedPolicy1 = vault.mintPolicyFingerprint(); vm.prank(owner);
        id = vault.mintDormant{value: 0.05 ether}(reviewedPolicy1);
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
        weightOffsets.push(totalWeight);
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
        t1.mint(address(royalties), totalWeight * 100);
        stable.mint(address(royalties), totalWeight * 1e6);
        _payNative(totalWeight * 1e12);
    }

    function _mixed(uint256 id) private view returns (ZZZClaimRouter.Claim[] memory requests) {
        requests = new ZZZClaimRouter.Claim[](5);
        requests[0] = ZZZClaimRouter.Claim(id, address(t1), false);
        requests[1] = ZZZClaimRouter.Claim(id, address(t0), false);
        requests[2] = ZZZClaimRouter.Claim(id, address(t1), true);
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
        assertEq(royalties.ticketStart(id),weightOffsets[ordinal]+1);
        assertEq(uint256(vault.nftStatus(id)), uint256(PositionStatus.Active));
    }

    // Independent whole-unit opening allocation: full weight rounds plus the
    // overlap with the initial cursor-zero remainder, without ledger previews.
    function _openingShare(uint256 ordinal,uint256 amount) private view returns(uint256) {
        uint256 weight = uint256(nft.rarityOf(ids[ordinal])) + 1;
        uint256 remainder = amount % totalWeight;
        uint256 first = weightOffsets[ordinal];
        uint256 extra = remainder > first ? remainder-first : 0;
        if(extra > weight) extra = weight;
        return (amount/totalWeight)*weight + extra;
    }

    function _closeWindowWithCohort(uint256 count,uint256 weight) private {
        vm.recordLogs();_finishRoyaltyWindow();Vm.Log[] memory logs=vm.getRecordedLogs();
        uint256 found;
        for(uint256 i;i<logs.length;++i) if(logs[i].emitter==address(royalties) &&
            logs[i].topics.length!=0 && logs[i].topics[0]==keccak256("RoyaltyOpeningFinalized(uint256,uint256,uint256)")) {
            (uint256 cutoff,uint256 actualCount,uint256 actualWeight)=abi.decode(logs[i].data,(uint256,uint256,uint256));
            assertEq(cutoff,royalties.royaltiesOpenAt());assertEq(actualCount,count);assertEq(actualWeight,weight);++found;
        }
        assertEq(found,1,"exactly one observed opening cutoff");
    }

    function _expected(uint256 ordinal) private view returns (uint256[5] memory amounts) {
        uint256 weight = uint256(nft.rarityOf(ids[ordinal])) + 1;
        // Funded LP fees are 40/60 times total original raw contribution.
        // Algebra is independent of on-chain index/checkpoint implementation.
        amounts[0] = principal[ordinal] * 32 + totalPrincipal * 4 / COUNT;
        amounts[1] = principal[ordinal] * 48 + totalPrincipal * 6 / COUNT;
        amounts[2] = weight * 100 + _openingShare(ordinal,openingRoyalties[0]);
        amounts[3] = weight * 1e6 + _openingShare(ordinal,openingRoyalties[1]);
        amounts[4] = weight * 1e12 + _openingShare(ordinal,openingRoyalties[2]);
    }

    function _assertEntitlement(uint256 ordinal) private view {
        uint256[5] memory expected = _expected(ordinal);
        uint256 id = ids[ordinal];
        assertEq(rewards.claimable(id, address(t1)), expected[0]);
        assertEq(rewards.claimable(id, address(t0)), expected[1]);
        assertEq(royalties.claimable(id, address(t1)), expected[2]);
        assertEq(royalties.claimable(id, address(stable)), expected[3]);
        assertEq(royalties.claimable(id, address(0)), expected[4]);
    }

    function _claimEveryNFT() private returns (uint256[5] memory paid) {
        for (uint256 i; i < COUNT; ++i) {
            uint256 id = ids[i]; address owner = holders[i];
            uint256[5] memory expected = _expected(i);
            uint256 before0 = t1.balanceOf(owner);
            uint256 before1 = address(owner).balance;
            uint256 beforeStable = stable.balanceOf(owner);
            uint256 beforeNative = owner.balance;
            vm.startPrank(owner);
            if (i % 2 == 0) {
                uint256[] memory received = router.claimBatch(_mixed(id));
                for (uint256 a; a < 5; ++a) assertEq(received[a], expected[a]);
            } else {
                assertEq(rewards.claim(id, address(t1)), expected[0]);
                assertEq(rewards.claim(id, address(t0)), expected[1]);
                assertEq(royalties.claim(id, address(t1)), expected[2]);
                assertEq(royalties.claim(id, address(stable)), expected[3]);
                assertEq(royalties.claim(id, address(0)), expected[4]);
            }
            // Repeated mixed claims cannot withdraw either ledger twice.
            uint256[] memory again = router.claimBatch(_mixed(id));
            vm.stopPrank();
            for (uint256 a; a < 5; ++a) { assertEq(again[a], 0); paid[a] += expected[a]; }
            assertEq(t1.balanceOf(owner) - before0, expected[0] + expected[2]);
            assertEq(owner.balance-before1,expected[1]+expected[4]);
            assertEq(stable.balanceOf(owner) - beforeStable, expected[3]);
            assertEq(owner.balance-beforeNative,expected[1]+expected[4]);
        }
    }

    function testAll1000NFTsPreserveIndependentRightsAndFundedConservation() public {
        // This models many separate users/transactions. Aggregate fixture and
        // payout-loop gas is not a claim that 1,000 claims fit one transaction.
        vm.pauseGasMetering();
        _prepareRoyaltyAssets();
        openingRoyalties = [uint256(23),uint256(41),uint256(17)];
        t1.mint(address(royalties), 23); stable.mint(address(royalties), 41); _payNative(17);
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
        // Receipts during minting belong to the eventual opening cohort, not
        // an orphan pool and not the first activation alone.
        assertEq(royalties.openingPool(address(t1)),23);
        assertEq(royalties.openingPool(address(stable)),41);
        assertEq(royalties.openingPool(address(0)),17);
        assertEq(royalties.orphaned(address(t1)),0);
        assertEq(royalties.orphaned(address(stable)),0);assertEq(royalties.orphaned(address(0)),0);
        assertEq(royalties.claimable(ids[0],address(t1)),0);
        vm.prank(holders[0]);vm.expectRevert(ZZZRoyaltyRewards.InvalidState.selector);
        royalties.claim(ids[0],address(t1));
        // Prove supply exhaustion while the sale is still open, rather than
        // accidentally passing because minting has already closed.
        bytes32 reviewedPolicy2 = vault.mintPolicyFingerprint(); vm.prank(_holder(0)); vm.expectRevert(); vault.mintDormant{value: 0.05 ether}(reviewedPolicy2);
        _closeWindowWithCohort(COUNT,totalWeight);
        assertEq(royalties.openingPool(address(t1)),0);assertEq(royalties.openingPool(address(stable)),0);
        assertEq(royalties.openingPool(address(0)),0);
        assertEq(royalties.liabilities(address(t1)),23);assertEq(royalties.liabilities(address(stable)),41);
        assertEq(royalties.liabilities(address(0)),17);

        // Actual venue receipts preserve the same 40/60 gross fee vector;
        // no optional creator-payment path is part of this candidate.
        venue.setFees(totalPrincipal * 60,totalPrincipal * 40);
        vault.collectFees(bucket, block.timestamp + 100);
        assertEq(fees.compoundBalance(bucket, address(t1)), totalPrincipal * 2);
        assertEq(fees.compoundBalance(bucket, address(t0)), totalPrincipal * 3);
        assertEq(fees.buybackBalance(address(t1)), totalPrincipal * 2);
        assertEq(fees.buybackBalance(address(t0)), totalPrincipal * 3);
        _fundRoyalties();
        for (uint256 i; i < COUNT; ++i) { _assertIdentity(i, bucket); _assertEntitlement(i); }

        uint256 oldLP = vault.group(bucket).lpTokenId;
        policy.setNeed(false);
        compounder.compound(bucket, 1, block.timestamp + 100);
        policy.setNeed(true);
        vault.rebalance(bucket, 1, block.timestamp + 100);
        assertTrue(vault.group(bucket).lpTokenId != oldLP);
        vm.expectRevert(); venue.ownerOf(oldLP);
        assertEq(venue.ownerOf(vault.group(bucket).lpTokenId), address(vault));
        assertEq(vault.bucketCount(), 1); assertEq(venue.next(), 3);
        assertEq(vault.bucketTotalShares(bucket), totalPrincipal * 1e18);
        assertEq(fees.compoundBalance(bucket, address(t1)), 0);
        assertEq(fees.compoundBalance(bucket, address(t0)), 0);

        // Direct approved ZZZ burn exercises the real burn supply check. The
        // other currency's reserve stays accounted; no swap price is invented.
        ZZZBuyback buyback = new ZZZBuyback(address(ac), address(t1), 1e30);
        ac.bind(Ids.BUYBACK, address(buyback));
        uint256 supplyBefore = t1.totalSupply();
        uint256 burned = totalPrincipal * 2;
        buyback.execute(address(t1), burned, poolId, block.timestamp + 100);
        assertEq(t1.totalSupply(), supplyBefore - burned);
        assertEq(t1.balanceOf(address(buyback)), 0);
        assertEq(fees.buybackBalance(address(t1)), 0);

        // Transfer several still-funded NFTs to an existing multi-NFT holder.
        // Exact historical entitlement and immutable traits remain token-bound.
        for (uint256 i = 99; i < COUNT; i += 100) {
            address previous = holders[i];
            vm.prank(previous); nft.transferFrom(previous, _holder(0), ids[i]);
            holders[i] = _holder(0);
            vm.prank(previous); vm.expectRevert(); rewards.claim(ids[i], address(t1));
            vm.prank(previous); vm.expectRevert(); royalties.claim(ids[i], address(0));
        }
        for (uint256 i; i < COUNT; ++i) { _assertIdentity(i, bucket); _assertEntitlement(i); }
        uint256[5] memory paid = _claimEveryNFT();
        assertEq(paid[0], totalPrincipal * 36); assertEq(paid[1], totalPrincipal * 54);
        assertEq(paid[2], totalWeight * 100 + 23); assertEq(paid[3], totalWeight * 1e6 + 41);
        assertEq(paid[4], totalWeight * 1e12 + 17);
        assertEq(rewards.liabilities(address(t1)), 0); assertEq(rewards.liabilities(address(t0)), 0);
        assertEq(t1.balanceOf(address(rewards)), 0); assertEq(address(address(rewards)).balance, 0);
        assertEq(royalties.liabilities(address(t1)), 0); assertEq(royalties.liabilities(address(stable)), 0);
        assertEq(royalties.liabilities(address(0)), 0);
        assertEq(t1.balanceOf(address(royalties)), 0); assertEq(stable.balanceOf(address(royalties)), 0);
        assertEq(address(royalties).balance, 0);
        assertEq(t1.balanceOf(address(fees)), fees.accounted(address(t1)));
        assertEq(address(address(fees)).balance, fees.accounted(address(t0)));
        assertEq(fees.accounted(address(t1)), 0); assertEq(fees.accounted(address(t0)), totalPrincipal * 3);

        Position memory p = vault.group(bucket);
        // Per-asset equality includes actual balances once, not liabilities plus
        // their backing. Principal, compounded revenue, paid fees, pending burn
        // reserve, burned supply and exact original-currency opening rights all reconcile.
        assertEq(venue.a1(p.lpTokenId) + p.idle1 + t1.balanceOf(address(fees)) +
            t1.balanceOf(address(rewards)) + t1.balanceOf(address(royalties)) + paid[0] + paid[2] + burned,
            totalPrincipal / 2 + totalPrincipal * 40 + totalWeight * 100 + 23);
        assertEq(venue.a0(p.lpTokenId) + p.idle0 + address(address(fees)).balance +
            address(address(rewards)).balance + paid[1], totalPrincipal / 2 + totalPrincipal * 60);
        assertEq(stable.balanceOf(address(royalties)) + paid[3], totalWeight * 1e6 + 41);
        assertEq(address(royalties).balance + paid[4], totalWeight * 1e12 + 17);
        assertEq(address(router).balance, 0); assertEq(t1.balanceOf(address(router)), 0);
        assertEq(address(address(router)).balance, 0); assertEq(stable.balanceOf(address(router)), 0);
        vm.resumeGasMetering();
    }


    function testZeroOpeningCohortKeepsUnallocatedSeparateFromFutureEarnings() public {
        _prepareRoyaltyAssets();_mintScale(0,false);
        t1.mint(address(royalties),23);stable.mint(address(royalties),41);_payNative(17);
        royalties.syncAll();
        assertEq(royalties.openingPool(address(t1)),23);assertEq(royalties.openingPool(address(stable)),41);
        assertEq(royalties.openingPool(address(0)),17);assertEq(royalties.orphaned(address(t1)),0);
        _closeWindowWithCohort(0,0);
        // Actual post-opening receipts with no eligible NFT also remain
        // unallocated; a later activation cannot silently capture either pool.
        t1.mint(address(royalties),7);stable.mint(address(royalties),11);_payNative(13);royalties.syncAll();
        assertEq(royalties.orphaned(address(t1)),30);assertEq(royalties.orphaned(address(stable)),52);
        assertEq(royalties.orphaned(address(0)),30);
        _activateScale(0);
        assertEq(royalties.claimable(ids[0],address(t1)),0);assertEq(royalties.claimable(ids[0],address(stable)),0);
        assertEq(royalties.claimable(ids[0],address(0)),0);
        _fundRoyalties();
        vm.startPrank(holders[0]);
        assertEq(royalties.claim(ids[0],address(t1)),totalWeight*100);
        assertEq(royalties.claim(ids[0],address(stable)),totalWeight*1e6);
        assertEq(royalties.claim(ids[0],address(0)),totalWeight*1e12);
        vm.stopPrank();
        assertEq(t1.balanceOf(address(royalties)),30);assertEq(stable.balanceOf(address(royalties)),52);
        assertEq(address(royalties).balance,30);
        assertEq(royalties.liabilities(address(t1)),0);assertEq(royalties.liabilities(address(stable)),0);
        assertEq(royalties.liabilities(address(0)),0);
    }

    function _cool(address owner) private {
        vm.cool(address(vault.migrationBudget()));
        address feed = oracle.policy(oracle.activePolicy(address(t1))).primary.source;
        vm.cool(address(ac)); vm.cool(address(vault)); vm.cool(address(membership));
        vm.cool(address(rewards)); vm.cool(address(fees)); vm.cool(address(compounder)); vm.cool(address(oracle));
        vm.cool(address(pools)); vm.cool(address(policy)); vm.cool(address(venue)); vm.cool(address(vrf));
        vm.cool(address(royalties)); vm.cool(address(router)); vm.cool(address(nft.metadataRenderer()));
        vm.cool(address(t1)); vm.cool(address(t0)); vm.cool(address(stable)); vm.cool(feed);
        vm.cool(owner); vm.cool(treasury);
        // Helper getters above touch the NFT; cool it after those reads.
        vm.cool(address(nft));
        vm.cool(ac.module(Ids.CANONICAL)); vm.cool(ac.module(Ids.NFT_CANONICAL));
        vm.cool(ac.module(Ids.VAULT_CANONICAL)); vm.cool(ac.module(Ids.FEES_CANONICAL));
        // policy above is the synthetic LP strategy; cool the ACTUAL shared
        // ProtocolPolicy too. Reading its binding warms Access, so cool it last.
        vm.cool(ac.protocolPolicy());vm.cool(address(ac));
    }

    function _measureAt(uint256 size) private returns (GasMeasurements memory result) {
        vm.pauseGasMetering();
        delete ids; delete holders; delete principal; delete traits;delete weightOffsets;delete openingRoyalties;
        totalPrincipal = 0; totalWeight = 0;
        _fixture(treasury); _prepareRoyaltyAssets();
        for (uint256 i; i < size; ++i) { _mintScale(i, false); if (i + 1 != size) _activateScale(i); }
        uint256 last = size - 1;
        _cool(holders[last]); vm.prank(holders[last]); vm.resumeGasMetering();
        uint256 start = gasleft();
        vault.activate{value:100}(ids[last], poolId, 100, 100, 1, block.timestamp + 100);
        result.activation = start - gasleft(); vm.pauseGasMetering();
        emit log_named_uint("collection.shape.nfts",size);
        emit log_named_uint("collection.shape.claimed-nft-royalty-weight",royalties.weightOf(ids[last]));
        emit log_named_uint("collection.shape.claimed-nft-first-ticket",royalties.ticketStart(ids[last]));
        emit log_named_uint("collection.shape.eligible-weight",royalties.totalWeight());
        // The measured activation remains a pre-opening entry. Open only
        // after every fixture mint/activation, and refresh its real mock feeds.
        _closeWindowWithCohort(size,totalWeight);
        uint256 bucket = vault.poolBucket(poolId);
        venue.setFees(totalPrincipal * 20,totalPrincipal * 20); vault.collectFees(bucket, block.timestamp + 100);
        _fundRoyalties();

        _cool(holders[last]); vm.prank(holders[last]); vm.resumeGasMetering();
        start = gasleft(); uint256 amount = rewards.claim(ids[last], address(t1));
        result.oneAssetClaim = start - gasleft(); vm.pauseGasMetering(); assertGt(amount, 0);
        ZZZClaimRouter.Claim[] memory requests = _mixed(ids[last]);
        _cool(holders[last]); vm.prank(holders[last]); vm.resumeGasMetering();
        start = gasleft(); uint256[] memory claimed = router.claimBatch(requests);
        result.mixedBatch = start - gasleft(); vm.pauseGasMetering();
        assertEq(claimed[0], 0); for (uint256 i = 1; i < 5; ++i) assertGt(claimed[i], 0);

        policy.setNeed(false);
        _cool(holders[last]); vm.resumeGasMetering(); start = gasleft();
        compounder.compound(bucket, 1, block.timestamp + 100);
        result.compound = start - gasleft(); vm.pauseGasMetering();
        policy.setNeed(true);
        _cool(holders[last]); vm.resumeGasMetering(); start = gasleft();
        vault.rebalance(bucket, 1, block.timestamp + 100);
        result.rebalance = start - gasleft(); vm.pauseGasMetering();
        assertEq(vault.bucketCount(), 1); assertEq(membership.totalEligible(), size);
        assertEq(venue.next(), 3); assertEq(vault.bucketTotalShares(bucket), totalPrincipal * 1e18);
        vm.resumeGasMetering();
    }

    function _absoluteBound(string memory operation,uint256 initial,uint256 incumbent,uint256 full) private {
        emit log_named_uint(string.concat("collection.1.",operation),initial);
        emit log_named_uint(string.concat("collection.2.",operation),incumbent);
        emit log_named_uint(string.concat("collection.1000.",operation),full);
        assertLt(initial,LOCAL_GAS_BUDGET);assertLt(incumbent,LOCAL_GAS_BUDGET);assertLt(full,LOCAL_GAS_BUDGET);
    }
    function _bounded(string memory operation,uint256 initial,uint256 incumbent,uint256 full) private {
        _absoluteBound(operation,initial,incumbent,full);
        assertLe(full,incumbent+SCALING_ALLOWANCE,"Same-path population regression exceeds allowance");
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
            requests[i * 2] = ZZZClaimRouter.Claim(ids[i], address(t1), false);
            requests[i * 2 + 1] = ZZZClaimRouter.Claim(ids[i], address(0), true);
            expectedLP += rewards.claimable(ids[i], address(t1));
            expectedNative += royalties.claimable(ids[i], address(0));
        }
        assertGt(expectedLP, 0); assertGt(expectedNative, 0);
        uint256 previousLP = t1.balanceOf(owner);
        uint256 previousNative = owner.balance;
        _cool(owner); vm.prank(owner); vm.resumeGasMetering();
        uint256 start = gasleft(); uint256[] memory paid = router.claimBatch(requests);
        uint256 used = start - gasleft(); vm.pauseGasMetering();
        emit log_named_uint("collection.1000.claim-32-mixed", used);
        assertLt(used, LOCAL_GAS_BUDGET);
        assertEq(paid.length, 32);
        assertEq(t1.balanceOf(owner) - previousLP, expectedLP);
        assertEq(owner.balance - previousNative, expectedNative);
        assertEq(address(router).balance, 0); assertEq(t1.balanceOf(address(router)), 0);
        vm.resumeGasMetering();
    }

    /// @notice Selected-account-and-slot-cooled local deltas exclude fixture
    /// setup, intrinsic/calldata gas and refunds. Unlisted helpers can remain
    /// warm; these are not target costs. Venue fees are synthetic.
    function testColdOperationsAtOneAnd1000NFTsStayBounded() public {
        GasMeasurements memory single = _measureAt(1);
        GasMeasurements memory incumbent = _measureAt(2);
        GasMeasurements memory full = _measureAt(COUNT);
        _bounded("activation",single.activation,incumbent.activation,full.activation);
        _bounded("claim-one-asset",single.oneAssetClaim,incumbent.oneAssetClaim,full.oneAssetClaim);
        // Royalty4 consumes bounded tree paths. These measured NFTs differ
        // in rarity and prefix/tag geometry, so an O(1) delta comparison would
        // conflate state shape with population. Keep the SAME absolute budget,
        // actual funded payouts and explicit shape logs; do not invent a larger
        // relative allowance or call these shapes a universal worst case.
        _absoluteBound("claim-five-mixed",single.mixedBatch,incumbent.mixedBatch,full.mixedBatch);
        _bounded("shared-rebalance",single.rebalance,incumbent.rebalance,full.rebalance);
        _bounded("shared-compound",single.compound,incumbent.compound,full.compound);
        _maximumMixedBatch();
    }
}
