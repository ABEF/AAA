# Economic rights and allocation rules

Current accepted rules: $100 activation, 80/10/5/5 revenue, equal activated-NFT collective membership and separate rarity royalties. This is an undeployed candidate; publication is not approval to use real funds.

## Permanent capital

The 0.05 ETH mint charge is forwarded to the immutable mint recipient and never becomes LP or rewards. Initial activation requires $100 of marginal oracle-valued deployed LP, excluding idle and incumbent assets; losses/slippage may require more than $100 input. Pool limits still apply. Permanent additions remain attributed to the same NFT.

Shares are nonredeemable. They are priced against the pool's current principal NAV, including attributed idle and designated compounding reserves. Earlier owner fees are checkpointed before new shares. Swaps can reprice incumbent LP; this gain/loss belongs to incumbents, and execution losses are charged to the net new contribution. Compounding and market changes do not create collective memberships. Transfers preserve shares and unclaimed rewards for the current holder.

## Collected LP and creator funding

| Purpose | Share | Weight or destination |
| --- | --- | --- |
| NFT owner | 80% | Pool-specific nonredeemable shares |
| Collective | 10% | One equal share per activated canonical NFT, across pools |
| Permanent compounding | 5% | Isolated attributed reinvestment reserve |
| ZZZ buyback/burn | 5% | Isolated approved execution reserve |

Twenty raw units split 16/2/1/1; smaller receipts carry forward. Before membership/share changes or migration, remaining dust goes to existing owner shares. The maximum exception is now **19 raw units**, which must be valued for each admitted token. Low-decimal/high-unit-value tokens can make this economically material. Global index dust stays reserved; per-NFT fractions carry. No administrator can sweep reward or orphan reserves.

All registered creator inboxes are processed and their old dust settled before a new membership or shares can be issued. Late receipts during entry are settled under old weights with a final pending-funds barrier. New members get no earlier published/pending income. Payments delivered later use processing-time membership and shares; no historical creator entitlement is reconstructed.

The selected native/Pons pool has zero core LP fees. Creator payments, if actually received and processed, fund the above allocation. No creator percentage or TVL-derived hook entitlement is assumed. Native receipts may be wrapped by an admitted exact one-for-one pair wrapper; LP claims are ERC20, including WETH. The separate intake does not implement native/hooked LP custody.

Satellites reserve the already-allocated **90% owner+collective** portion for canonical delivery. It is never split again. Lifetime remote counters, historical token provenance and complete funding barriers remain in force across onward migration/return. Home external funding never discharges remote liabilities. New contributions remain blocked while custody is away, migration is scheduled, or earlier remote liabilities remain unfunded.

## Equal collective membership

`ZZZMembership.activate` is vault-only, one-time and checkpoints all admitted LP reward assets before eligibility changes. A dormant NFT has zero membership; each activated NFT has one share regardless of rarity, LP size or number of top-ups. Membership persists through transfer, market losses, pauses and migration. No contribution-USD Power module or score exists. Contribution USD remains a separate historical contribution record, not a reward weight or current valuation.

## NFT-sale royalties

ERC-2981 requests **5% of a marketplace sale** payable to the immutable NFT-owned royalty receiver. Payment cannot be forced by this interface. **100% of actual receipts** is reserved for already-activated NFTs in weights Commun1/Rare2/Legendary3, independently of LP revenue allocations. LP size and evolution do not change royalty weight. Current owners claim all their NFT's accrued balances.

Native ETH is supported; up to16 reviewed exact-transfer, non-rebasing ERC20 assets may be admitted. All raw pending royalties are synced to incumbents before a newly activated NFT gains weight. Constructor/admission prefunds and receipts with zero eligible weight are quarantined permanently, excluding future entrants. Fractions carry; index dust stays reserved. There is no rescue, administrator withdrawal, weight replacement or redirected payout. A broken admitted token can block activation's bounded global synchronization; admission must review that liveness risk.

## NFT supply and evolution

Mint supply is capped at1,000, with exact600/300/100 rarity quotas. Authenticated VRF words are bound to each NFT/request, and permissionless reveal proceeds strictly in mint order. Draws use remaining quotas; 60/30/10 describes initial odds only. Earlier unavailable randomness blocks later reveals; there is no reroll or administrator bypass.

Evolution follows current marked LP share NAV, including attributed idle and compounding reserves, excluding claimable rewards and donations. Enhanced starts at$1,000; Singularity at$10,000. A decline can lower evolution while activation, collective membership and rarity royalties remain. Stale/oracle/remote valuation is unavailable, not a zero-price observation. It does not block claims or migration.

## Strategy and migrations

Rebalancing uses configured range/deviation/cooldown, fresh valuation and bounded swaps. It does not eliminate impermanent loss or guarantee capital/returns. Buyback supports approved direct routes or direct ZZZ burn, not arbitrary multi-hop conversion. Equivalent-asset migrations preserve canonical NFT/share/membership and old funded fee paths; actual provider finality/backing, gas/MEV, payment timing and independent economic/security review remain release gates.
