// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {Ids, Position} from "../src/libraries/ZZZTypes.sol";

contract NFTRightsNoMigrationPlan {
    function activePlan(uint256) external pure returns (bytes32) { return bytes32(0); }
}

/// @dev Bounded stateful integration using real economic contracts. Explicitly
/// mocked venue/VRF/authorities/prices; neither live payment terms nor yield model.
/// Ghost totals count actual test ingress and actual payouts in each asset's raw
/// units; native royalties and the six-decimal royalty asset are never added.
contract NFTRightsHandler is PooledVaultFixture {
    ZZZRoyaltyRewards private royalties;
    ZZZClaimRouter private router;
    MockToken private royaltyAsset;
    uint256[8] public ids;
    address[8] public owner;
    uint8[8] private rarity;
    bytes32[8] private artwork;
    uint256[2] private lpDeposited;
    uint256[2] private lpReceived;
    uint256[2] private lpPaid;
    uint256[2] private royaltyReceived;
    uint256[2] private royaltyPaid;
    uint256 public transfers;
    uint256 public royaltiesClaimed;
    uint256 public mixedClaims;
    uint256 public topUps;

    constructor() {
        setUp(); ac.bind(Ids.MIGRATION, address(new NFTRightsNoMigrationPlan()));
        royalties = nft.royaltyRewards(); router = nft.claimRouter();
        royaltyAsset = new MockToken(6); nft.addRoyaltyAsset(address(royaltyAsset));
        vm.deal(address(this), 1e30);
        for (uint256 i; i < ids.length; ++i) {
            address holder = address(uint160(0x10000 + i)); owner[i] = holder;
            _fundUser(holder);
            vm.prank(holder); uint256 id = vault.mintDormant{value: 0.05 ether}(); ids[i] = id;
            uint256 draw = i % 3 == 0 ? 0 : uint256(nft.rarityRemaining(0));
            if (i % 3 == 2) draw += nft.rarityRemaining(1);
            vrf.fulfill(nft.requestOf(id), draw, i * 59); nft.finalizeTraits(id);
            rarity[i] = uint8(i % 3);
            assertEq(nft.rarityOf(id), rarity[i]);
            artwork[i] = keccak256(abi.encode(nft.paletteOf(id), nft.patternOf(id)));
        }
        // Actual receipts before any eligibility must remain quarantined.
        receiveRoyalty(13, false); receiveRoyalty(17, true);
        activate(0, 500); activate(1, 750); activate(2, 1000);
    }

    function activate(uint256 seed, uint256 raw) public {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        if (ac.paused() || membership.eligible(id)) return;
        uint256 amount = bound(raw, 100, 1000);
        t0.mint(owner[n], amount); t1.mint(owner[n], amount);
        _activate(owner[n], id, amount, amount);
        lpDeposited[0] += amount; lpDeposited[1] += amount;
        assertEq(rewards.claimable(id, address(t0)), 0, "retroactive LP");
        assertEq(rewards.claimable(id, address(t1)), 0, "retroactive LP");
        assertEq(royalties.claimable(id, address(0)), 0, "retroactive native royalty");
        assertEq(royalties.claimable(id, address(royaltyAsset)), 0, "retroactive token royalty");
    }

    function receiveRoyalty(uint256 raw, bool token) public {
        uint256 amount = bound(raw, 0, 1e6); uint256 slot = token ? 1 : 0;
        if (token) royaltyAsset.mint(address(royalties), amount);
        else { (bool ok,) = address(royalties).call{value: amount}(""); require(ok); }
        royaltyReceived[slot] += amount;
    }

    function synchronizeRoyalty(bool token) external {
        royalties.sync(token ? address(royaltyAsset) : address(0));
    }

    function harvest(uint256 x, uint256 y) public {
        if (ac.paused()) return;
        x = bound(x, 0, 1000); y = bound(y, 0, 1000);
        venue.setFees(x, y); vault.collectFees(_bucket(), block.timestamp + 100);
        lpReceived[0] += x; lpReceived[1] += y;
    }

    function topUp(uint256 seed, uint256 raw) external {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        if (ac.paused() || !membership.eligible(id)) return;
        // Both zero-decimal fixture currencies are $1. Equal-sided growth
        // therefore needs at least 3+3 raw units to satisfy the real $5 floor.
        // Smaller generated values previously made fail_on_revert reject an
        // invalid action instead of exploring successful accounting changes.
        uint256 amount = bound(raw, 3, 100);
        t0.mint(owner[n], amount); t1.mint(owner[n], amount);
        uint256 old0 = rewards.claimable(id, address(t0));
        uint256 old1 = rewards.claimable(id, address(t1));
        uint256 royaltyBefore = royalties.claimable(id, address(royaltyAsset));
        uint256 sharesBefore = vault.sharesOf(id);
        vm.prank(owner[n]); vault.increase(id, amount, amount, 1, block.timestamp + 100);
        lpDeposited[0] += amount; lpDeposited[1] += amount;
        ++topUps;
        assertGt(vault.sharesOf(id), sharesBefore);
        assertGe(rewards.claimable(id, address(t0)), old0);
        assertGe(rewards.claimable(id, address(t1)), old1);
        assertEq(royalties.claimable(id, address(royaltyAsset)), royaltyBefore);
    }

    function claimRoyalty(uint256 seed, bool token) public {
        uint256 n = seed % ids.length; uint256 id = ids[n]; address holder = owner[n];
        address asset = token ? address(royaltyAsset) : address(0); uint256 slot = token ? 1 : 0;
        uint256 expected = royalties.claimable(id, asset);
        uint256 beforeBalance = token ? royaltyAsset.balanceOf(holder) : holder.balance;
        vm.prank(holder); uint256 actual = royalties.claim(id, asset);
        assertEq(actual, expected);
        assertEq((token ? royaltyAsset.balanceOf(holder) : holder.balance) - beforeBalance, actual);
        royaltyPaid[slot] += actual; ++royaltiesClaimed;
        vm.prank(holder); assertEq(royalties.claim(id, asset), 0, "duplicate royalty");
    }

    function claimLP(uint256 seed, bool second) public {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        MockToken asset = second ? t1 : t0; uint256 slot = second ? 1 : 0;
        uint256 expected = rewards.claimable(id, address(asset)); uint256 beforeBalance = asset.balanceOf(owner[n]);
        vm.prank(owner[n]); uint256 actual = rewards.claim(id, address(asset));
        assertEq(actual, expected); assertEq(asset.balanceOf(owner[n]) - beforeBalance, actual);
        lpPaid[slot] += actual;
        vm.prank(owner[n]); assertEq(rewards.claim(id, address(asset)), 0, "duplicate LP");
    }

    function claimMixed(uint256 seed) public {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](3);
        list[0] = ZZZClaimRouter.Claim(id, address(t0), false);
        list[1] = ZZZClaimRouter.Claim(id, address(royaltyAsset), true);
        list[2] = ZZZClaimRouter.Claim(id, address(0), true);
        uint256 lpBefore = t0.balanceOf(owner[n]); uint256 tokenBefore = royaltyAsset.balanceOf(owner[n]);
        uint256 nativeBefore = owner[n].balance;
        vm.prank(owner[n]); uint256[] memory paid = router.claimBatch(list);
        assertEq(t0.balanceOf(owner[n]) - lpBefore, paid[0]);
        assertEq(royaltyAsset.balanceOf(owner[n]) - tokenBefore, paid[1]);
        assertEq(owner[n].balance - nativeBefore, paid[2]);
        lpPaid[0] += paid[0]; royaltyPaid[1] += paid[1]; royaltyPaid[0] += paid[2]; ++mixedClaims;
    }

    function transfer(uint256 seed, uint256 recipient) public {
        uint256 n = seed % ids.length; uint256 id = ids[n]; address old = owner[n];
        address next = address(uint160(0x10000 + recipient % ids.length));
        uint256 shares = vault.sharesOf(id); uint256 lp = rewards.claimable(id, address(t0));
        uint256 nativeRoyalty = royalties.claimable(id, address(0));
        uint256 tokenRoyalty = royalties.claimable(id, address(royaltyAsset));
        vm.prank(old); nft.transferFrom(old, next, id); owner[n] = next; ++transfers;
        assertEq(vault.sharesOf(id), shares); assertEq(rewards.claimable(id, address(t0)), lp);
        assertEq(royalties.claimable(id, address(0)), nativeRoyalty);
        assertEq(royalties.claimable(id, address(royaltyAsset)), tokenRoyalty);
        if (old != next) {
            vm.prank(old); (bool lpSuccess,) = address(rewards).call(abi.encodeWithSignature("claim(uint256,address)", id, address(t0)));
            assertFalse(lpSuccess, "previous owner LP claim");
            vm.prank(old); (bool royaltySuccess,) = address(royalties).call(abi.encodeCall(ZZZRoyaltyRewards.claim, (id, address(0))));
            assertFalse(royaltySuccess, "previous owner royalty claim");
        }
    }

    function pause(bool value) external { ac.setPaused(value); }

    function maintain(bool rebalancePosition) external {
        if (ac.paused()) return;
        if (rebalancePosition) vault.rebalance(_bucket(), 1, block.timestamp + 100);
        else if (fees.compoundBalance(_bucket(), address(t0)) + fees.compoundBalance(_bucket(), address(t1)) != 0) {
            compounder.compound(_bucket(), 1, block.timestamp + 100);
        }
    }

    function assertEconomicRights() external view {
        uint256 weight; uint256 eligible; uint256 shares; uint256[2] memory lpClaims; uint256[2] memory royaltyClaims;
        for (uint256 i; i < ids.length; ++i) {
            uint256 id = ids[i]; assertEq(nft.ownerOf(id), owner[i]); assertEq(nft.rarityOf(id), rarity[i]);
            assertEq(keccak256(abi.encode(nft.paletteOf(id), nft.patternOf(id))), artwork[i]);
            assertEq(nft.tokenAtOrdinal(i + 1), id); assertEq(nft.mintOrdinalOf(id), i + 1);
            if (membership.eligible(id)) {
                ++eligible; weight += uint256(rarity[i]) + 1;
                assertEq(royalties.weightOf(id), uint256(rarity[i]) + 1);
                assertEq(vault.nftBucket(id), _bucket());
            } else { assertEq(royalties.weightOf(id), 0); assertEq(vault.sharesOf(id), 0); }
            shares += vault.sharesOf(id);
            lpClaims[0] += rewards.claimable(id, address(t0)); lpClaims[1] += rewards.claimable(id, address(t1));
            royaltyClaims[0] += royalties.claimable(id, address(0));
            royaltyClaims[1] += royalties.claimable(id, address(royaltyAsset));
        }
        assertEq(membership.totalEligible(), eligible); assertEq(royalties.totalWeight(), weight);
        assertEq(vault.bucketTotalShares(_bucket()), shares); assertEq(vault.bucketCount(), 1);
        Position memory p = vault.group(_bucket()); assertEq(venue.ownerOf(p.lpTokenId), address(vault));
        for (uint256 i; i < 2; ++i) {
            MockToken token = i == 0 ? t0 : t1; address asset = address(token);
            uint256 principal = i == 0 ? venue.a0(p.lpTokenId) + p.idle0 : venue.a1(p.lpTokenId) + p.idle1;
            uint256 feeBalance = token.balanceOf(address(fees)); uint256 rewardBalance = token.balanceOf(address(rewards));
            assertEq(feeBalance, fees.accounted(asset));
            assertEq(feeBalance, fees.dust(_bucket(), asset) + fees.compoundBalance(_bucket(), asset) + fees.buybackBalance(asset));
            assertEq(rewardBalance, rewards.liabilities(asset) + rewards.orphaned(asset));
            assertLe(lpClaims[i], rewards.liabilities(asset));
            assertEq(principal + feeBalance + rewardBalance + lpPaid[i], lpDeposited[i] + lpReceived[i], "LP conservation");
            address royaltyCurrency = i == 0 ? address(0) : address(royaltyAsset);
            uint256 balance = i == 0 ? address(royalties).balance : royaltyAsset.balanceOf(address(royalties));
            assertEq(royaltyPaid[i] + balance, royaltyReceived[i], "royalty conservation");
            assertEq(royalties.accounted(royaltyCurrency), royalties.liabilities(royaltyCurrency) + royalties.orphaned(royaltyCurrency));
            assertEq(balance, royalties.accounted(royaltyCurrency) + royalties.pending(royaltyCurrency));
            assertLe(royaltyClaims[i], balance - royalties.orphaned(royaltyCurrency), "unfunded royalty");
            assertEq(royalties.orphaned(royaltyCurrency), i == 0 ? 13 : 17, "quarantine reassigned");
        }
        assertEq(address(router).balance, 0); assertEq(royaltyAsset.balanceOf(address(router)), 0);
        assertEq(address(vault).balance, 0); assertEq(treasury.balance, 8 * 0.05 ether);
    }
}

contract NFTRightsInvariantTest is Test {
    NFTRightsHandler private handler;
    function setUp() public {
        handler = new NFTRightsHandler(); bytes4[] memory selectors = new bytes4[](11);
        selectors[0] = handler.activate.selector; selectors[1] = handler.receiveRoyalty.selector;
        selectors[2] = handler.synchronizeRoyalty.selector; selectors[3] = handler.harvest.selector;
        selectors[4] = handler.topUp.selector; selectors[5] = handler.claimRoyalty.selector;
        selectors[6] = handler.claimLP.selector; selectors[7] = handler.claimMixed.selector;
        selectors[8] = handler.transfer.selector; selectors[9] = handler.pause.selector; selectors[10] = handler.maintain.selector;
        targetContract(address(handler)); targetSelector(FuzzSelector(address(handler), selectors));
    }
    function invariant_rightsAndActualFundingConserved() public view { handler.assertEconomicRights(); }
    function testMinimumBoundTopUpActuallyExecutesAndConservesRights() public {
        uint256 beforeCount = handler.topUps();
        handler.topUp(1, 0);
        assertEq(handler.topUps(), beforeCount + 1, "valid top-up must not be skipped");
        handler.assertEconomicRights();
    }
    function testReceiptActivationTransferPauseAndMixedClaimSequence() public {
        handler.receiveRoyalty(1001, false); handler.receiveRoyalty(2003, true);
        handler.harvest(109, 217); handler.activate(3, 900); handler.transfer(0, 3);
        handler.claimMixed(0); handler.topUp(1, 33); handler.maintain(true);
        handler.receiveRoyalty(17, false); handler.synchronizeRoyalty(true);
        handler.transfer(2, 3); handler.pause(true); handler.claimRoyalty(2, false);
        handler.claimLP(3, true); handler.claimMixed(1); handler.assertEconomicRights();
        assertEq(handler.transfers(), 2); assertEq(handler.royaltiesClaimed(), 1); assertEq(handler.mixedClaims(), 2);
    }
}
