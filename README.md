# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

Development candidate for transferable NFT rights to permanently attached LP and funded rewards. **Undeployed; not approved for real funds.** The website is a separate simulation at [popldemo.0xwave.com](https://popldemo.0xwave.com).

Start with the **[Implemented / Todo checklist](docs/IMPLEMENTATION_STATUS.md)** for current feature status, then the [component map](docs/COMPONENT_STATUS.md) for source boundaries and the separate [release checklist](docs/RELEASE_CHECKLIST.md) for production approval. The accepted website economics and artwork rules are implemented in the candidate; selected-pool custody, arbitrary USDC routing, live services and production qualification remain open.

## Current product rules

- Exactly **1,000 NFTs maximum**, with **600 Commun, 300 Rare and 100 Legendary** when the full collection is minted and revealed.
- A dormant mint costs exactly **0.05 ETH**, forwarded to the immutable mint-proceeds recipient. Minting adds no LP or reward eligibility.
- The current owner activates the same NFT with at least **$100 of marginal, actually deployed LP** after execution; idle assets and incumbents' compound funds cannot meet its minimum. Later contributions grow its nonredeemable allocation.
- NFTs in each approved pool share one physical LP position. Keeper upkeep and whole-pool migration operate per bucket, without holder loops.
- The intended initial collection uses one shared pool. A vault can register at most 16 historical buckets, including imports, to bound global entry settlement; returns and future pool migrations of an existing bucket do not consume another slot.
- The owner allocation follows an NFT's LP shares. The collective allocation is **equal per activated NFT**, across pools. **Power has been removed**, replaced by one permanent membership per activated NFT. Top-ups never add collective memberships.
- LP principal cannot be redeemed. Transfers carry the shares, unclaimed funded balances and future economic rights to the NFT's current owner.

## Separate reward pools

| Collected LP/creator revenue | Allocation |
| --- | --- |
| NFT owner | **80%**, proportional to shares in the earning LP bucket |
| Collective rewards | **10%**, equal per activated canonical NFT |
| LP compounding | **5%**, reserved for permanent reinvestment |
| ZZZ buyback and burn | **5%**, reserved for approved execution |

Actual funded receipts use batches of 20 raw token units: 16/2/1/1. Smaller receipts carry; membership/migration dust settles to incumbents under the documented bounded exception. Satellite owner/collective reserves return as already-allocated 90% rewards, without a second split. See [economic rules](docs/ECONOMICS.md).

NFT-sale royalties are **separate**: ERC-2981 requests **5% of sale value**, payable to an immutable `ZZZRoyaltyRewards` receiver. **100% of royalties actually received while members exist** are reserved for activated NFT holders: Commun ×1, Rare ×2, Legendary ×3. Dormant NFTs get no royalties. The royalty ledger accepts native ETH and reviewed exact-transfer ERC20 assets; it has no administrator withdrawal. Marketplace payment is not enforceable through ERC-2981. Rarity never changes LP or collective weights.

Both reward ledgers are funded by actual receipts, with no fixed per-minute accrual or periodic claim window. LP claims use already allocated funding; royalty claims also process pending admitted receipts. The current holder claims one NFT and one asset per call. The website still simulates LP claims and needs live royalty integration. See [reward timing and keeper schedules](docs/OPERATIONS.md#reward-timing-and-maintenance-schedule).

## Random traits and current-value artwork

Each dormant mint requests verifiable randomness from a once-configured, fixed VRF-v2.5-compatible coordinator. The callback stores words; anyone can finalize traits strictly in mint order. A draw without replacement enforces exact rarity quotas. Initial odds are 60/30/10; later odds equal the remaining quota divided by remaining reveals. There is no cancellation, reroll or administrator trait selection. Delayed earlier fulfillment blocks later reveals, and activation requires revealed traits.

Rarity, palette and circuit pattern are permanent. Eight base colors (Cyan, Blue, Violet, Emerald, Amber, Crimson, Ivory and Onyx) form **58 palettes: eight monochrome, 22 bicolor and 28 tricolor**. A bicolor pair contains Ivory, Amber, Crimson or Onyx; a tricolor adds a distinct Amber, Crimson or Onyx to an allowed pair. Every palette is available across all rarities, and these visual traits never change rewards.

The finite visual inventory contains **200 monochrome / 500 bicolor / 300 tricolor** entries, each style independently maintaining the 60/30/10 rarity composition. Four circuit patterns provide variety: Flowing arcs, Segmented panels, Orbital rings and Vertical ribs. The second VRF word draws without replacement from the selected rarity's remaining inventory, limiting identical complete palette/pattern/rarity artwork to four copies; Legendary artwork has no identical copies. The renderer supports **2,784 SVG states** (58 palettes × four patterns × three rarities × four evolutions), separate from the **1,000-NFT cap**. The former 72-PNG library is historical. The deterministic preview inventory order is not production mint randomness.

Evolution follows current oracle-marked attached principal, attributed idle and compounding NAV, proportionally to shares: Dormant before activation; Activated after activation; Enhanced from **$1,000**; Singularity from **$10,000**. Market declines can lower evolution without removing activation or royalty eligibility. Remote/in-flight custody and stale/unavailable valuation return an explicit unavailable state, with labelled Activated fallback art; they do not fabricate a current value. Claims and migration do not depend on metadata valuation. See [NFT metadata and royalties](docs/NFT_METADATA.md).

## Contracts and operations

| Component | Responsibility |
| --- | --- |
| `ZZZVault` | Paid dormant mint, $100 activation, shared LP custody, nonredeemable shares and permanent additions |
| `ZZZNFT` | ERC-721 ownership, capped mint, VRF requests, fixed traits, ERC-2981 and ERC-4906 |
| `ZZZMembership` | One equal collective membership per activated NFT; no contribution weights |
| `ZZZRewards` | Funded LP owner and equal collective indexes, checkpoints and current-owner claims |
| `ZZZFeeController` / `ZZZRewardReceiver` | 80/10/5/5 allocation, compound/buyback reserves and immutable creator-payment intake |
| `ZZZRoyaltyRewards` / `ZZZNFTMetadata` | Immutable NFT-owned royalty helper and read-only dynamic renderer |
| `ZZZLiquidityManager` / `ZZZStrategy` | Supported hookless ERC20 Uniswap v4 LP operations, price/range and swap bounds |
| `ZZZCompounder` / `ZZZBuyback` | Authorized reinvestment and bounded direct-route buyback/burn |
| `ZZZMigration`, bridge/router/receiver/registries | Repeated whole-bucket custody migrations and timelocked future-route onboarding |
| `ZZZAccessController`, oracle and pool registry | Fixed sealed modules, timelock/roles/pauses, valuation and reviewed pool admission |

The fixed module inventory remains 17 contracts including the controller; Membership replaces Power. The per-bucket creator receiver and NFT royalty/metadata helpers are not additional sealed modules. Governance is the deployment-selected multisig, not automatic holder voting. New migration routes and provider policies require timelocked governance; sealing fixes core bindings without preventing reviewed future routes. The local template uses a two-day timelock and additional two-day migration delay.

The [keeper](keeper/monitor.py) operates once per shared bucket and defaults to dry run. Its ten-minute example polling interval does not force a rebalance: price movement, cooldown, oracle and execution bounds must pass. An optional watcher separately observes NFT evolution and sends bounded ERC-4906 notifications through the same budgeted transaction path. It defaults to disabled. The [indexer](indexer/monitor.py) stores confirmed events and handles bounded reorganizations; a hosted frontend API is not supplied. Linux/Unix and Python 3.11+ are required for full keeper/state-lock operation. See [architecture](docs/ARCHITECTURE.md) and [operations](docs/OPERATIONS.md).

## Development and release boundary

The selected Robinhood Chain ZZZ/native-ETH Pons-hooked pool remains **unsupported by the LP adapter**. Its 0% conventional LP fee does not create proportional hook-revenue rights. Plain creator payments can fund the separate bucket receiver, but intake does not add native/hook custody support or promise payments. The selected chain also needs an independently reviewed available VRF coordinator and funded subscription; a compatible ABI or mock does not prove verifiable randomness.

Production still requires actual market integration, reviewed oracle/token/wrapper policies, governance addresses, staged operations, actual-venue gas qualification and an independent external audit with remediation. The user has not chosen production authority or mint-recipient addresses; those gates remain open. Current [release-hardening evidence](reports/release-hardening/README.md) records metadata notifications, keeper tests, normal size gates, fresh internal [Slither review](reports/release-hardening/static-analysis/README.md) and a read-only [selected-market design review](reports/release-hardening/selected-market-review.md). Check Ubuntu CI for the exact published revision. Real bridge wrappers and multi-chain staging are required before migration is enabled; an independently approved initial launch may keep migration disabled. No public deployment, signatures or real transactions are part of this work. Earlier artwork, website-alignment and reward-funding reports retain their own source snapshots and evidence scope.

The blocked [production inventory](config/production.example.json) uses schema 4 / `shared-pools-v2`. Its read-only validator requires the current economics, exact NFT quotas, helper bindings, randomness observations and actual staging evidence. A passing inventory is consistency evidence, never deployment approval.

```sh
python3 scripts/run_python_tests.py
python3 scripts/source_checks.py
bash scripts/install-deps.sh
bash scripts/verify.sh
```

See [development setup](docs/DEVELOPMENT.md), [roadmap](docs/ROADMAP.md), [security](SECURITY.md), and the [release checklist](docs/RELEASE_CHECKLIST.md). The compiler remains Solidity 0.8.26/Cancun, via IR with the existing optimizer profile. Dependencies and historical reviews remain pinned/preserved.
