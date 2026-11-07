// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Vm} from "forge-std/Vm.sol";
import {MockToken} from "./mocks/Mocks.sol";
import {ZZZRoyaltyRewards} from "../src/ZZZRoyaltyRewards.sol";
import {ZZZClaimRouter} from "../src/ZZZClaimRouter.sol";
import {Ids, Position} from "../src/libraries/ZZZTypes.sol";
import {IZZZProtocolPolicy} from "../src/interfaces/IZZZProtocolPolicy.sol";

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
    uint256 public blockedContributions;
    uint256 public lockedRoyaltyChecks;
    uint256 public lockedMixedChecks;
    uint256 public positiveRoyaltyClaims;
    uint256 public positiveMixedClaims;
    uint256 public windowOpenings;
    uint256 public openingCountGhost;
    uint256 public openingWeightGhost;
    bool[8] private openingCohort;

    constructor() {
        setUp(); ac.bind(Ids.MIGRATION, address(new NFTRightsNoMigrationPlan()));
        royalties = nft.royaltyRewards(); router = nft.claimRouter();
        royaltyAsset = new MockToken(6); nft.addRoyaltyAsset(address(royaltyAsset));
        vm.deal(address(this), 1e30);
        for (uint256 i; i < ids.length; ++i) {
            address holder = address(uint160(0x10000 + i)); owner[i] = holder;
            _fundUser(holder);
            bytes32 reviewedPolicy1 = vault.mintPolicyFingerprint(); vm.prank(holder); uint256 id = vault.mintDormant{value: 0.05 ether}(reviewedPolicy1); ids[i] = id;
            uint256 draw = i % 3 == 0 ? 0 : uint256(nft.rarityRemaining(0));
            if (i % 3 == 2) draw += nft.rarityRemaining(1);
            vrf.fulfill(nft.requestOf(id), draw, i * 59); nft.finalizeTraits(id);
            rarity[i] = uint8(i % 3);
            assertEq(nft.rarityOf(id), rarity[i]);
            artwork[i] = keccak256(abi.encode(nft.paletteOf(id), nft.patternOf(id)));
        }
        // During minting these receipts are held for the eventual opening cohort.
        receiveRoyalty(13, false); receiveRoyalty(17, true);
        activate(0, 500); activate(1, 750); activate(2, 1000);
    }

    /// @dev All eight NFTs are already minted. Model the actual irreversible
    /// sale end and one-hour activation grace, recording its eligible cohort.
    function finishRoyaltyWindow() public {
        if(royalties.royaltiesOpen()) return;
        for(uint256 i;i<ids.length;++i) if(membership.eligible(ids[i])) {
            openingCohort[i]=true;++openingCountGhost;openingWeightGhost+=uint256(rarity[i])+1;
        }
        vm.recordLogs();_finishRoyaltyWindow();Vm.Log[] memory logs=vm.getRecordedLogs();
        uint256 found;
        for(uint256 i;i<logs.length;++i) if(logs[i].emitter==address(royalties) &&
            logs[i].topics.length!=0 && logs[i].topics[0]==keccak256("RoyaltyOpeningFinalized(uint256,uint256,uint256)")) {
            (uint256 cutoff,uint256 count,uint256 weight)=abi.decode(logs[i].data,(uint256,uint256,uint256));
            assertEq(cutoff,royalties.royaltiesOpenAt());assertEq(count,openingCountGhost);
            assertEq(weight,openingWeightGhost);++found;
        }
        assertEq(found,1,"one observed initial cutoff");++windowOpenings;
    }

    /// @dev Exact prediction for THIS fixture only: both raw assets are $1,
    /// no swap/repricing/placement dust exists, and the venue deploys all entry
    /// funds. Existing idle plus designated compound remains incumbent idle.
    function _entryIdleBlocked(uint256 amount) private view returns(bool) {
        Position memory p=vault.group(_bucket());
        uint256 idle=p.idle1+p.idle0+fees.compoundBalance(_bucket(),address(t1))+
            fees.compoundBalance(_bucket(),address(t0));
        uint256 retained=venue.a1(p.lpTokenId)+venue.a0(p.lpTokenId)+idle+amount*2;
        uint256 cap=IZZZProtocolPolicy(ac.protocolPolicy()).entryPolicy().maxIdleBps;
        return idle>retained*cap/10000;
    }
    function _rejectIdleEntry(uint256 n,uint256 amount,bool activation) private {
        uint256 id=ids[n];uint256 beforeShares=vault.sharesOf(id);
        uint256 beforeBucket=vault.nftBucket(id);uint256 beforeWeight=royalties.totalWeight();
        uint256 before0=t1.balanceOf(owner[n]);uint256 before1=address(owner[n]).balance;
        uint256 reserved0=fees.compoundBalance(_bucket(),address(t1));
        uint256 reserved1=fees.compoundBalance(_bucket(),address(t0));
        Position memory beforePosition=vault.group(_bucket());
        uint256 beforeSupply=vault.bucketTotalShares(_bucket());
        vm.prank(owner[n]);vm.expectRevert(bytes4(keccak256("Slippage()")));
        if(activation) vault.activate{value:amount}(id, poolId, amount, amount, 1, block.timestamp+100);
        else vault.increase{value:amount}(id, amount, amount, 1, block.timestamp+100);
        assertEq(t1.balanceOf(owner[n]),before0,"rejected entry t1 refund");
        assertEq(address(owner[n]).balance,before1,"rejected entry t0 refund");
        assertEq(vault.sharesOf(id),beforeShares);assertEq(vault.nftBucket(id),beforeBucket);
        assertEq(vault.bucketTotalShares(_bucket()),beforeSupply);assertEq(royalties.totalWeight(),beforeWeight);
        assertEq(keccak256(abi.encode(vault.group(_bucket()))),keccak256(abi.encode(beforePosition)));
        assertEq(fees.compoundBalance(_bucket(),address(t1)),reserved0);
        assertEq(fees.compoundBalance(_bucket(),address(t0)),reserved1);
        ++blockedContributions;
    }

    function activate(uint256 seed, uint256 raw) public {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        if (ac.paused() || membership.eligible(id)) return;
        uint256 amount = bound(raw, 100, 1000);
        t1.mint(owner[n], amount); _giftNative(owner[n], amount);
        if(_entryIdleBlocked(amount)) {_rejectIdleEntry(n,amount,true);return;}
        _activate(owner[n], id, amount, amount);
        lpDeposited[0] += amount; lpDeposited[1] += amount;
        assertEq(rewards.claimable(id, address(t1)), 0, "retroactive LP");
        assertEq(rewards.claimable(id, address(t0)), 0, "retroactive LP");
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
        venue.setFees(y,x); vault.collectFees(_bucket(), block.timestamp + 100);
        lpReceived[0] += x; lpReceived[1] += y;
    }

    function topUp(uint256 seed, uint256 raw) external {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        if (ac.paused() || !membership.eligible(id)) return;
        // Both normalized native/ZZZ raw fixture units are $1. Equal-sided growth
        // therefore needs at least 3+3 raw units to satisfy the real $5 floor.
        // Smaller generated values previously made fail_on_revert reject an
        // invalid action instead of exploring successful accounting changes.
        uint256 amount = bound(raw, 3, 100);
        t1.mint(owner[n], amount); _giftNative(owner[n], amount);
        uint256 old0 = rewards.claimable(id, address(t1));
        uint256 old1 = rewards.claimable(id, address(t0));
        uint256 royaltyBefore = royalties.claimable(id, address(royaltyAsset));
        uint256 sharesBefore = vault.sharesOf(id);
        if(_entryIdleBlocked(amount)) {
            _rejectIdleEntry(n,amount,false);
            assertEq(rewards.claimable(id,address(t1)),old0);assertEq(rewards.claimable(id,address(t0)),old1);
            assertEq(royalties.claimable(id,address(royaltyAsset)),royaltyBefore);return;
        }
        vm.prank(owner[n]); vault.increase{value:amount}(id, amount, amount, 1, block.timestamp + 100);
        lpDeposited[0] += amount; lpDeposited[1] += amount;
        ++topUps;
        assertGt(vault.sharesOf(id), sharesBefore);
        assertGe(rewards.claimable(id, address(t1)), old0);
        assertGe(rewards.claimable(id, address(t0)), old1);
        assertEq(royalties.claimable(id, address(royaltyAsset)), royaltyBefore);
    }

    function claimRoyalty(uint256 seed, bool token) public {
        uint256 n = seed % ids.length; uint256 id = ids[n]; address holder = owner[n];
        address asset = token ? address(royaltyAsset) : address(0); uint256 slot = token ? 1 : 0;
        uint256 expected = royalties.claimable(id, asset);
        uint256 beforeBalance = token ? royaltyAsset.balanceOf(holder) : holder.balance;
        if(!royalties.royaltiesOpen()) {
            vm.prank(holder);vm.expectRevert(ZZZRoyaltyRewards.InvalidState.selector);
            royalties.claim(id,asset);
            assertEq(token ? royaltyAsset.balanceOf(holder) : holder.balance,beforeBalance);
            ++lockedRoyaltyChecks;return;
        }
        vm.prank(holder); uint256 actual = royalties.claim(id, asset);
        assertEq(actual, expected);
        assertEq((token ? royaltyAsset.balanceOf(holder) : holder.balance) - beforeBalance, actual);
        royaltyPaid[slot] += actual; ++royaltiesClaimed;
        if(actual!=0) ++positiveRoyaltyClaims;
        vm.prank(holder); assertEq(royalties.claim(id, asset), 0, "duplicate royalty");
    }

    function claimLP(uint256 seed, bool second) public {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        MockToken asset = second ? t0 : t1; uint256 slot = second ? 1 : 0;
        uint256 expected = rewards.claimable(id, address(asset)); uint256 beforeBalance=address(asset)==address(0)?owner[n].balance:asset.balanceOf(owner[n]);
        vm.prank(owner[n]); uint256 actual = rewards.claim(id, address(asset));
        assertEq(actual, expected); assertEq((address(asset)==address(0)?owner[n].balance:asset.balanceOf(owner[n]))-beforeBalance,actual);
        lpPaid[slot] += actual;
        vm.prank(owner[n]); assertEq(rewards.claim(id, address(asset)), 0, "duplicate LP");
    }

    function claimMixed(uint256 seed) public {
        uint256 n = seed % ids.length; uint256 id = ids[n];
        ZZZClaimRouter.Claim[] memory list = new ZZZClaimRouter.Claim[](3);
        list[0] = ZZZClaimRouter.Claim(id, address(t1), false);
        list[1] = ZZZClaimRouter.Claim(id, address(royaltyAsset), true);
        list[2] = ZZZClaimRouter.Claim(id, address(0), true);
        uint256 lpBefore = t1.balanceOf(owner[n]); uint256 tokenBefore = royaltyAsset.balanceOf(owner[n]);
        uint256 nativeBefore = owner[n].balance;
        if(!royalties.royaltiesOpen()) {
            // A mixed batch must roll its earlier LP payment back when the
            // royalty item is locked. Separate LP claims remain available.
            vm.prank(owner[n]);vm.expectRevert(ZZZRoyaltyRewards.InvalidState.selector);
            router.claimBatch(list);
            assertEq(t1.balanceOf(owner[n]),lpBefore);assertEq(royaltyAsset.balanceOf(owner[n]),tokenBefore);
            assertEq(owner[n].balance,nativeBefore);++lockedMixedChecks;return;
        }
        vm.prank(owner[n]); uint256[] memory paid = router.claimBatch(list);
        assertEq(t1.balanceOf(owner[n]) - lpBefore, paid[0]);
        assertEq(royaltyAsset.balanceOf(owner[n]) - tokenBefore, paid[1]);
        assertEq(owner[n].balance - nativeBefore, paid[2]);
        lpPaid[0] += paid[0]; royaltyPaid[1] += paid[1]; royaltyPaid[0] += paid[2]; ++mixedClaims;
        if(paid[1]!=0 || paid[2]!=0) ++positiveMixedClaims;
    }

    function transfer(uint256 seed, uint256 recipient) public {
        uint256 n = seed % ids.length; uint256 id = ids[n]; address old = owner[n];
        address next = address(uint160(0x10000 + recipient % ids.length));
        uint256 shares = vault.sharesOf(id); uint256 lp = rewards.claimable(id, address(t1));
        uint256 nativeRoyalty = royalties.claimable(id, address(0));
        uint256 tokenRoyalty = royalties.claimable(id, address(royaltyAsset));
        vm.prank(old); nft.transferFrom(old, next, id); owner[n] = next; ++transfers;
        assertEq(vault.sharesOf(id), shares); assertEq(rewards.claimable(id, address(t1)), lp);
        assertEq(royalties.claimable(id, address(0)), nativeRoyalty);
        assertEq(royalties.claimable(id, address(royaltyAsset)), tokenRoyalty);
        if (old != next) {
            vm.prank(old); (bool lpSuccess,) = address(rewards).call(abi.encodeWithSignature("claim(uint256,address)", id, address(t1)));
            assertFalse(lpSuccess, "previous owner LP claim");
            vm.prank(old); (bool royaltySuccess,) = address(royalties).call(abi.encodeCall(ZZZRoyaltyRewards.claim, (id, address(0))));
            assertFalse(royaltySuccess, "previous owner royalty claim");
        }
    }

    function pause(bool value) external { ac.setPaused(value); }

    function maintain(bool rebalancePosition) external {
        if (ac.paused()) return;
        if (rebalancePosition) vault.rebalance(_bucket(), 1, block.timestamp + 100);
        else if (fees.compoundBalance(_bucket(), address(t1)) + fees.compoundBalance(_bucket(), address(t0)) != 0) {
            policy.setNeed(false);
            // The fake need flag is not a waiver of the real independent
            // compound interval. Invalid scheduling is not an economic action.
            if(vault.migrationBudget().compoundReady(_bucket()))
                compounder.compound(_bucket(), 1, block.timestamp + 100);
            policy.setNeed(true);
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
            lpClaims[0] += rewards.claimable(id, address(t1)); lpClaims[1] += rewards.claimable(id, address(t0));
            royaltyClaims[0] += royalties.claimable(id, address(0));
            royaltyClaims[1] += royalties.claimable(id, address(royaltyAsset));
        }
        assertEq(membership.totalEligible(), eligible); assertEq(royalties.totalWeight(), weight);
        bool open=royalties.royaltiesOpen();
        if(open) {
            assertEq(windowOpenings,1);
            for(uint256 i;i<ids.length;++i) {
                uint256 ordinal=royalties.activationOrdinal(ids[i]);
                if(openingCohort[i]) assertTrue(ordinal!=0 && ordinal<=openingCountGhost);
                else if(ordinal!=0) assertGt(ordinal,openingCountGhost);
            }
        } else assertEq(windowOpenings,0);
        assertEq(vault.bucketTotalShares(_bucket()), shares); assertEq(vault.bucketCount(), 1);
        Position memory p = vault.group(_bucket()); assertEq(venue.ownerOf(p.lpTokenId), address(vault));
        for (uint256 i; i < 2; ++i) {
            MockToken token = i == 0 ? t1 : t0; address asset = address(token);
            uint256 principal = i == 0 ? venue.a1(p.lpTokenId) + p.idle1 : venue.a0(p.lpTokenId) + p.idle0;
            uint256 feeBalance=asset==address(0)?address(fees).balance:token.balanceOf(address(fees));uint256 rewardBalance=asset==address(0)?address(rewards).balance:token.balanceOf(address(rewards));
            assertEq(feeBalance, fees.accounted(asset));
            assertEq(feeBalance, fees.dust(_bucket(), asset) + fees.compoundBalance(_bucket(), asset) + fees.buybackBalance(asset));
            assertEq(rewardBalance, rewards.liabilities(asset) + rewards.orphaned(asset));
            assertEq(lpClaims[i],rewards.liabilities(asset));
            assertEq(principal + feeBalance + rewardBalance + lpPaid[i], lpDeposited[i] + lpReceived[i], "LP conservation");
            address royaltyCurrency = i == 0 ? address(0) : address(royaltyAsset);
            uint256 balance = i == 0 ? address(royalties).balance : royaltyAsset.balanceOf(address(royalties));
            assertEq(royaltyPaid[i] + balance, royaltyReceived[i], "royalty conservation");
            uint256 held=royalties.openingPool(royaltyCurrency);
            uint256 unallocated=royalties.orphaned(royaltyCurrency);
            uint256 pending=royalties.pending(royaltyCurrency);
            assertEq(royalties.accounted(royaltyCurrency),royalties.liabilities(royaltyCurrency)+unallocated+held);
            assertEq(balance,royalties.accounted(royaltyCurrency)+pending);
            // These two healthy currencies were admitted with zero prefunds,
            // and the opening always has at least the three initial members.
            assertEq(unallocated,0,"unexpected unallocated royalty");
            if(open) {
                assertEq(held,0);
                // Exact royalty4 must not hide a whole-unit rounding residue.
                assertEq(royaltyPaid[i]+royaltyClaims[i]+unallocated,royaltyReceived[i],"exact opened royalty rights");
            } else {
                assertEq(royaltyClaims[i],0);assertEq(royaltyPaid[i],0);
                assertEq(royalties.liabilities(royaltyCurrency),0);
                assertEq(royaltyPaid[i]+royaltyClaims[i]+held+pending+unallocated,royaltyReceived[i],"held opening conservation");
            }
        }
        assertEq(address(router).balance, 0); assertEq(royaltyAsset.balanceOf(address(router)), 0);
        assertEq(address(vault).balance,p.idle0); assertEq(treasury.balance, 8 * 0.05 ether);
    }
    function assertRoyaltiesDrained() external view {
        assertTrue(royalties.royaltiesOpen());
        assertEq(royalties.liabilities(address(0)),0);assertEq(royalties.liabilities(address(royaltyAsset)),0);
        assertEq(address(royalties).balance,0);assertEq(royaltyAsset.balanceOf(address(royalties)),0);
        assertEq(royaltyPaid[0],royaltyReceived[0]);assertEq(royaltyPaid[1],royaltyReceived[1]);
    }
}

contract NFTRightsInvariantTest is Test {
    NFTRightsHandler private handler;
    function setUp() public {
        handler = new NFTRightsHandler(); bytes4[] memory selectors = new bytes4[](12);
        selectors[0] = handler.activate.selector; selectors[1] = handler.receiveRoyalty.selector;
        selectors[2] = handler.synchronizeRoyalty.selector; selectors[3] = handler.harvest.selector;
        selectors[4] = handler.topUp.selector; selectors[5] = handler.claimRoyalty.selector;
        selectors[6] = handler.claimLP.selector; selectors[7] = handler.claimMixed.selector;
        selectors[8] = handler.transfer.selector; selectors[9] = handler.pause.selector; selectors[10] = handler.maintain.selector;
        selectors[11] = handler.finishRoyaltyWindow.selector;
        targetContract(address(handler)); targetSelector(FuzzSelector(address(handler), selectors));
    }
    function invariant_rightsAndActualFundingConserved() public view { handler.assertEconomicRights(); }
    /// @dev Every bounded invariant run also executes positive, current-owner
    /// royalty claims after opening, including when the protocol is paused.
    /// This prevents successful handler selection from hiding vacuous reverts.
    function afterInvariant() public {
        handler.finishRoyaltyWindow();handler.receiveRoyalty(1024,false);handler.receiveRoyalty(2048,true);
        uint256 beforePositive=handler.positiveRoyaltyClaims();
        for(uint256 i;i<8;++i) {handler.claimRoyalty(i,false);handler.claimRoyalty(i,true);}
        assertGe(handler.positiveRoyaltyClaims(),beforePositive+6);
        handler.assertEconomicRights();handler.assertRoyaltiesDrained();
    }
    function testMinimumBoundTopUpActuallyExecutesAndConservesRights() public {
        uint256 beforeCount = handler.topUps();
        handler.topUp(1, 0);
        assertEq(handler.topUps(), beforeCount + 1, "valid top-up must not be skipped");
        // A harvest backlog can intentionally exceed the real 5% idle ceiling.
        // Prove rejected activation/growth returns both inputs and preserves
        // the incumbent position/reserves rather than silently skipping a bug.
        for(uint256 i;i<10;++i) handler.harvest(1000,1000);
        uint256 blocked=handler.blockedContributions();handler.activate(3,100);handler.topUp(1,0);
        assertEq(handler.blockedContributions(),blocked+2);
        assertEq(handler.topUps(),beforeCount+1);
        handler.assertEconomicRights();
    }
    function testReceiptActivationTransferPauseAndMixedClaimSequence() public {
        handler.receiveRoyalty(1001, false); handler.receiveRoyalty(2003, true);
        handler.harvest(109, 217); handler.activate(3, 900); handler.transfer(0, 3);
        handler.claimRoyalty(0,false);handler.claimMixed(0);
        assertEq(handler.lockedRoyaltyChecks(),1);assertEq(handler.lockedMixedChecks(),1);
        handler.finishRoyaltyWindow();handler.activate(4,600);
        assertEq(handler.openingCountGhost(),4);
        handler.claimMixed(0); handler.topUp(1, 33); handler.maintain(true);
        handler.receiveRoyalty(17, false); handler.synchronizeRoyalty(true);
        handler.transfer(2, 3); handler.pause(true); handler.claimRoyalty(2, false);
        handler.claimLP(3, true); handler.claimMixed(1); handler.assertEconomicRights();
        assertEq(handler.transfers(), 2); assertEq(handler.royaltiesClaimed(), 1); assertEq(handler.mixedClaims(), 2);
        assertGt(handler.positiveRoyaltyClaims(),0);assertGt(handler.positiveMixedClaims(),0);
    }
}
