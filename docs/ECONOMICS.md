# Economic rights and allocation rules

This document records the shared-pool candidate's choices. These economic and migration policies still require product approval before a funded deployment; repository publication is not such approval.

## Permanent capital and transferable rights

Principal and reinvested capital are non-redeemable. Liquidity may be closed and recreated during authorized maintenance, temporarily idle, swapped, or moved through an approved bridge. The economic NFT persists across position replacement. Its current owner receives claim rights, including unclaimed rewards.

## Mint price and permanent LP contributions

`mintDormant()` charges exactly **0.05 ETH**, excluding transaction gas. The vault forwards it to the immutable mint-proceeds recipient chosen at construction. The payment is a mint charge, not deposited LP, contribution Power, funded rewards, or a compounding budget. A dormant mint therefore adds no collection locked LP and earns no LP fees.

Only the current NFT owner can activate it. `activate(...)` requires at least **$500 of actually deployed, oracle-valued LP** (`500e18` USD), excluding attributed idle assets, as well as the pool's contribution and position limits. Successful activation keeps the same NFT and does not charge another mint payment or issue another NFT. The minimum is enforced when activating, not guaranteed against subsequent price changes.

The owner of an active home-chain position can add further LP with `increase(...)`; satellite holder top-ups remain unsupported. Activation contributions, top-ups, attributed idle capital, and reinvested capital remain permanently non-redeemable. Mint income is isolated from those ledgers.

## Fee allocation

| Allocation | Share | Accounting |
|---|---|---|
| Individual NFT | 50% | Funded pool-specific index proportional to each NFT's shares |
| Collective pool | 30% | Funded reward index weighted by eligible Power |
| Permanent compounding | 10% | Reserved for reinvestment into attributed permanent liquidity |
| ZZZ buyback and burn | 10% | Reserved for approved direct-route execution or direct ZZZ burn |

Only measured, separately collected fees enter this allocation. Principal and LP-removal proceeds do not become reward income. For each asset, ten raw token units split into five, three, one, and one; smaller remainders carry forward. Before any membership increase or migration, sub-ten-unit dust settles to the existing pool owner index; a satellite retains it as funded remote-owner reserves. This bounded raw-unit rounding exception prevents later entrants receiving earlier dust.

This allocation describes the candidate's supported fee-collection path. It does not establish a revenue entitlement from the user-selected Robinhood ETH / ZZZ pool. That pool has a **0% core LP fee** and a separate **1% Pons hook fee** routed to its configured recipients, not to LP owners in proportion to their liquidity. The project's pool integration and reward funding model will be decided later; see [verified pool economics](ROBINHOOD_POOL.md). The previous website's 0.30% fee and 34% proportional fee-share calculation were hypothetical examples and must not be used as this pool's actual economics.

On satellite chains, the 80% NFT reward portion is reserved and delivered to the canonical chain without a second 50/30/10/10 split. Compounding and buyback budgets remain at the satellite.

Canonical asset provenance is bound permanently for each bucket/local-token pair. Old reward budgets retain that mapping after a pool change or further migration. They can be sent from an active, outbound, remote, or inbound old custody record; historical authorized reward paths remain available after principal leaves. A migration therefore does not require converting old reward liabilities into new principal or abandoning them at a former custodian.

## Power and reward timing

Power is lifetime user-contribution USD value recorded at activation and increases, using 18 decimals. A dormant NFT has zero Power, and the 0.05 ETH mint charge is excluded. Compounding and price gains do not increase it; market losses do not decrease it. Remote and in-flight positions remain eligible. Placement must deploy at least 95% of a position's oracle-valued assets, but that is an execution-time check rather than continuous productivity assurance.

Collective rewards use Power at settlement/collection or remote delivery time. Checkpoints preserve already-published indexes before Power changes; they do not reconstruct historical per-swap ownership or weights for uncollected fees. Harvest, deposit, and bridge timing therefore have economic consequences that need adversarial review.

The deployment supports at most 32 reward assets. Fractional entitlements carry forward, while index rounding dust and zero-Power orphan reserves are not administrator-withdrawable.

## Strategy and buybacks

Pool configuration can use `rangeBps = 1000` for an approximately ±10% price range, rounded outward to valid ticks. Rebalancing requires a trigger, cooldown, fresh oracle checks, bounded swaps, and execution limits. Costs, market impact, volatility, and MEV must be measured before production.

Buybacks support an approved direct token/ZZZ pair or burning fees already denominated in ZZZ. Multi-hop conversion is absent. A local supply reduction does not establish canonical/global supply reduction for arbitrary wrapped tokens.

## Migration scope

The development candidate supports repeated custody migration, satellite-to-satellite hops, and canonical return across approved equivalent-asset routes. Governance can onboard new append-only routes after sealing through the timelock, while module bindings and the transport endpoint stay fixed. Each principal move adds a separate two-day migration delay. Imports preserve the existing NFT and contribution value and do not add Power.

Version-3 whole-bucket messages preserve canonical identity, prior custodian, canonical token provenance, and custody epoch. Source-completion and canonical-location ACKs have separate roles. Canonical locations require ordered next-epoch updates; out-of-order updates wait for retry, and exact historical ACKs cannot roll location backward. Old funded rewards remain deliverable via historical paths after subsequent hops.

A provider-specific transport must define token equivalence, finality, retry, fee, and authenticated cancellation semantics. Failed destination activation retains attributed principal for retry rather than authorizing a principal refund.

Route onboarding is not general asset conversion, an NFT-chain move, or a proxy upgrade. Satellite user deposits and cross-chain holder top-ups remain absent. New destination code, token equivalence, proxy authorities, and bridge/provider behavior must be reviewed: timelock notice cannot establish perpetual custody safety for arbitrary future deployments. No production transport or native-ETH/hooked-pool reward integration is supplied. See [current implementation evidence](../reports/IMPLEMENTATION_UPDATE.md).

See [architecture](ARCHITECTURE.md), [security review](AUDIT.md), and [release checklist](RELEASE_CHECKLIST.md) for the associated invariants and unresolved gates.

## Shared-pool ownership

One stable bucket owns the physical LP for one pool/strategy. An NFT has one bucket association and nonredeemable internal shares; no external share token or principal-redemption function exists. Shares never change on NFT transfer, maintenance or migration. Entry mints shares against incumbent principal NAV, including attributed idle assets and the 10% compounding reserve. The incumbent LP is valued again after any entry swap so existing LP repricing belongs to incumbents. Execution losses are charged to net new contribution, bounded by the configured input-value slippage check. Initial shares use 18-decimal net USD; subsequent shares round down as `supply * netContribution / incumbentNAV`, with zero-NAV, zero-issuance and total-share caps. Pool limits remain per-NFT lifetime contributions.

Activation must add at least $500 of marginal deployed LP, conservatively subtracting all pre-existing idle and fresh compounding value from measured LP growth. A large existing pool cannot satisfy a small entrant's minimum. Owner rewards checkpoint before every share increase. Collective Power uses the original oracle-valued contribution; fee compounding and market repricing do not add Power.

Custody migrates an entire bucket. Shares cannot change while away, while a migration is scheduled, or after return until authenticated cumulative remote owner/collective allocations have all been funded home. These counters include unsent reserves and rounding dust. Maintenance, transfers and funded claims remain possible while settlement is pending. A failed reward transport can delay new contributions; there is no authority bypass. The 30% collective policy still uses Power at funding time, including contributions to other buckets; it is not historical swap-time weighting.

Token-admission review must value the maximum nine-raw-unit dust settlement in USD and consider holder-triggered top-up frequency. A raw-unit bound is not universally a small economic amount: low-decimal or high-value-per-unit tokens can materially skew the intended allocation. The current rounding policy is an explicit economic review gate for each future reward asset, rather than an assurance of exact 50/30/10/10 allocation for every sub-ten-unit collection.
