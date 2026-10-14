# Economic rights and allocation rules

This document records the v0.2 candidate's choices. These economic and migration policies still require product approval before a funded deployment; repository publication is not such approval.

## Permanent capital and transferable rights

Principal and reinvested capital are non-redeemable. Liquidity may be closed and recreated during authorized maintenance, temporarily idle, swapped, or moved through an approved bridge. The economic NFT persists across position replacement. Its current owner receives claim rights, including unclaimed rewards.

## Fee allocation

| Allocation | Share | Accounting |
|---|---|---|
| Individual NFT | 50% | Attributed to the NFT whose LP earned the collected fees |
| Collective pool | 30% | Funded reward index weighted by eligible Power |
| Permanent compounding | 10% | Reserved for reinvestment into attributed permanent liquidity |
| ZZZ buyback and burn | 10% | Reserved for approved direct-route execution or direct ZZZ burn |

Only measured, separately collected fees enter this allocation. Principal and LP-removal proceeds do not become reward income. For each asset, ten raw token units split into five, three, one, and one; smaller remainders carry forward. Final source-migration dust is credited to the originating NFT.

On satellite chains, the 80% NFT reward portion is reserved and delivered to the canonical chain without a second 50/30/10/10 split. Compounding and buyback budgets remain at the satellite.

## Power and reward timing

Power is lifetime user-contribution USD value recorded at deposit, using 18 decimals. Compounding and price gains do not increase it; market losses do not decrease it. Remote and in-flight positions remain eligible. Placement must deploy at least 95% of a position's oracle-valued assets, but that is an execution-time check rather than continuous productivity assurance.

Collective rewards use Power at settlement/collection or remote delivery time. Checkpoints preserve already-published indexes before Power changes; they do not reconstruct historical per-swap ownership or weights for uncollected fees. Harvest, deposit, and bridge timing therefore have economic consequences that need adversarial review.

The deployment supports at most 32 reward assets. Fractional entitlements carry forward, while index rounding dust and zero-Power orphan reserves are not administrator-withdrawable.

## Strategy and buybacks

Pool configuration can use `rangeBps = 1000` for an approximately ±10% price range, rounded outward to valid ticks. Rebalancing requires a trigger, cooldown, fresh oracle checks, bounded swaps, and execution limits. Costs, market impact, volatility, and MEV must be measured before production.

Buybacks support an approved direct token/ZZZ pair or burning fees already denominated in ZZZ. Multi-hop conversion is absent. A local supply reduction does not establish canonical/global supply reduction for arbitrary wrapped tokens.

## Migration scope

Migration is one hop from the NFT's canonical chain to a preconfigured satellite. Return migration, onward migration, satellite user deposits, and cross-chain top-ups are absent. Module bindings and route identities are fixed after sealing; existing routes may be disabled or re-enabled, but arbitrary new chains cannot be appended.

A provider-specific transport must define token equivalence, finality, retry, fee, and authenticated cancellation semantics. Failed destination activation retains attributed principal for retry rather than authorizing a principal refund.

See [architecture](ARCHITECTURE.md), [security review](AUDIT.md), and [release checklist](RELEASE_CHECKLIST.md) for the associated invariants and unresolved gates.
