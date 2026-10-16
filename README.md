# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

**[Project Todo: frontend, backend, contracts, testing and operations](TODO.md)**

Keeper: [recovery runbook](docs/KEEPER_RECOVERY.md) | [internal security review and open gates](reports/keeper-recovery/REVIEW.md).

Development candidate for transferable NFT rights to permanently attached LP and funded rewards. **Undeployed; not approved for real funds.** The website is a separate simulation at [popldemo.0xwave.com](https://popldemo.0xwave.com).

Start with the **[Implemented / Todo checklist](docs/IMPLEMENTATION_STATUS.md)** for current feature status, then the [component map](docs/COMPONENT_STATUS.md) for source boundaries and the separate [release checklist](docs/RELEASE_CHECKLIST.md) for production approval. The candidate includes the selected native/Pons adapter, atomic original-source activation, governed custody parking, bounded LP/royalty claims and read-only integration tools. Actual input routes, live services and independent production qualification remain open.

The [service decision record](docs/PRODUCTION_SERVICES.md) records randomness and pricing research plus the remaining provider choices. The [change and recovery matrix](docs/CHANGE_AND_RECOVERY.md) explains post-seal configuration and custody limits.

## Current product rules

- Exactly **1,000 NFTs maximum**, with **600 Commun, 300 Rare and 100 Legendary** when the full collection is minted and revealed.
- A dormant mint costs exactly **0.05 ETH**, forwarded to the immutable mint-proceeds recipient. Minting adds no LP or reward eligibility.
- The current owner activates the same NFT with at least **$100 in gross input value**, with **at least 99% actually deployed as new LP**. The same 1% execution/undeployed limit applies to additions. Network gas is separate; incumbent idle/compound funds cannot subsidize the minimum. The immutable Registry-created [activation entry](docs/ACTIVATION_ENTRY.md) binds the original source's measured USD value through a reviewed typed conversion into the Vault. Direct pair-token entry remains available; actual production routes and feeds need qualification.
- NFTs in each approved pool share one physical LP position. Keeper upkeep and whole-pool migration operate per bucket, without holder loops.
- The intended initial collection uses one shared pool. A vault can register at most 16 historical buckets, including imports, to bound global entry settlement; returns and future pool migrations of an existing bucket do not consume another slot.
- The owner allocation follows an NFT's LP shares. The collective allocation is **equal per activated NFT**, across pools. **Power has been removed**, replaced by one permanent membership per activated NFT. Top-ups never add collective memberships.
- LP principal cannot be redeemed. Transfers carry the shares, unclaimed funded balances and future economic rights to the NFT's current owner.
- Governance can add or disable contribution assets without disabling existing claims or LP exits. Reviewed wrapper policies and migration routes support controlled maintenance; sealed custody code is fixed. See [change and recovery boundaries](docs/CHANGE_AND_RECOVERY.md) for supported changes and external failure limits.
- While globally paused, timelocked governance can [park a shared LP position](docs/CUSTODY_PARKING.md) in the Vault using an exact custody snapshot and raw close-output minimums, without price feeds or creator-inbox synchronization. Principal stays attached and nonredeemable. Resume requires fresh normal deployment checks; reviewed migration retains route, custody and remote-liability barriers. Failed external assets or venues can still prevent movement.

## Separate reward pools

| Collected LP/creator revenue | Allocation |
| --- | --- |
| NFT owner | **80%**, proportional to shares in the earning LP bucket |
| Collective rewards | **10%**, equal per activated canonical NFT |
| LP compounding | **5%**, reserved for permanent reinvestment |
| ZZZ buyback and burn | **5%**, reserved for approved execution |

Actual funded receipts use batches of 20 raw token units: 16/2/1/1. Smaller receipts carry; membership/migration dust settles to incumbents under the documented bounded exception. Satellite owner/collective reserves return as already-allocated 90% rewards, without a second split. See [economic rules](docs/ECONOMICS.md).

NFT-sale royalties are **separate**: ERC-2981 requests **5% of sale value**, payable to an immutable `ZZZRoyaltyRewards` receiver. **100% of royalties actually received while members exist** are reserved for activated NFT holders: Commun ×1, Rare ×2, Legendary ×3. Dormant NFTs get no royalties. The royalty ledger accepts native ETH and reviewed exact-transfer ERC20 assets; it has no administrator withdrawal. Marketplace payment is not enforceable through ERC-2981. Rarity never changes LP or collective weights.

Both reward ledgers are funded by actual receipts, with no fixed per-minute accrual or periodic claim window. LP claims use already allocated funding; royalty claims also process pending admitted receipts. Direct ledger claims remain one NFT/asset per call; the immutable NFT-owned router batches up to 32 mixed LP/royalty claims. The website still simulates claims and needs live integration. See [reward timing and keeper schedules](docs/OPERATIONS.md#reward-timing-and-maintenance-schedule).

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
| `ZZZLiquidityManager` / `ZZZStrategy` | Hookless ERC20 and strictly pinned selected native/Pons v4 LP operations, normalization, price/range and swap bounds |
| `ZZZCompounder` / `ZZZBuyback` | Authorized reinvestment and bounded direct-route buyback/burn |
| `ZZZMigration`, bridge/router/receiver/registries | Repeated whole-bucket custody migrations and timelocked future-route onboarding |
| `ZZZAccessController`, oracle and pool registry | Fixed sealed modules, timelock/roles/pauses, valuation and reviewed pool admission |
| `ZZZActivationAssets` / `ZZZActivationEntry` | Immutable Registry-created helpers for source admission, typed conversion and one source-to-LP execution budget |

The fixed module inventory remains 17 contracts including the controller; Membership replaces Power. The per-bucket creator receiver and NFT royalty/metadata helpers are not additional sealed modules. Governance is the deployment-selected multisig, not automatic holder voting. New migration routes and provider policies require timelocked governance; sealing fixes core bindings without preventing reviewed future routes. The local template uses a two-day timelock and additional two-day migration delay.

The [keeper](keeper/monitor.py) operates once per shared bucket and defaults to dry run. Its ten-minute example polling interval does not force a rebalance: price movement, cooldown, oracle and execution bounds must pass. An optional watcher separately observes NFT evolution and sends bounded ERC-4906 notifications through the same budgeted transaction path. It defaults to disabled. The [indexer](indexer/monitor.py) stores confirmed events and handles bounded reorganizations; a hosted frontend API is not supplied. Linux/Unix and Python 3.11+ are required for full keeper/state-lock operation. See [architecture](docs/ARCHITECTURE.md) and [operations](docs/OPERATIONS.md).

## Development and release boundary

The selected Robinhood Chain ZZZ/native-ETH Pons-hooked pool now has a **development adapter with explicit real-key/WETH accounting separation**, exact native settlement and runtime-pinned admission. Other native/hooked markets remain rejected. This is not production approval: the offline production validator deliberately keeps its native-market gate closed pending full qualification. Its 0% conventional LP fee does not grant hook-revenue rights. The user reports a creator agreement to share according to PoPL liquidity; [measurement proposals](docs/REVENUE_SHARE.md), payment terms and actual funding still need qualification. The chain also needs an independently reviewed available VRF service; a compatible ABI or mock does not prove verifiable randomness.

The NFT-created [claim router](docs/CLAIM_ROUTER.md) batches up to 32 LP/royalty claim operations, paying the current owner directly. The unhosted [read API](docs/FRONTEND_API.md) exposes confirmed balances and optional creation-anchored wallet/lifetime-claims history; gross earned-fee and USD projections remain missing. [Activation route tools](docs/ACTIVATION_ROUTING.md) verify known stablecoin identities and quote a USDG/WETH conversion. The separate on-chain Entry now authenticates original-source value, owner intent and exact balances through activation/top-up; the unsigned quote alone does not establish an executable, qualified production route. An [artwork upload bundle](docs/ARTWORK_PUBLICATION.md) is prepared; publication and pinning remain pending.

Production still requires actual market integration, reviewed oracle/token/wrapper policies, governance addresses, staged operations, actual-venue gas qualification and an independent external audit with remediation. The user has not chosen production authority or mint-recipient addresses; those gates remain open. Earlier [release-hardening evidence](reports/release-hardening/README.md) records metadata notifications, keeper tests, normal size gates, source-specific internal [Slither review](reports/release-hardening/static-analysis/README.md) and a read-only [selected-market design review](reports/release-hardening/selected-market-review.md). Check Ubuntu CI for the exact published revision. Real bridge wrappers and multi-chain staging are required before migration is enabled; an independently approved initial launch may keep migration disabled. No public deployment, signatures or real transactions are part of this work. Earlier artwork, website-alignment and reward-funding reports retain their own source snapshots and evidence scope.

Current [gap-hardening receipts](reports/gap-hardening/README.md) record **488 Solidity passes**, **488 portable Python passes**, **20 selected native/Pons plus nine secondary fork passes**, all **23 normal module/helper size gates**, **29 production source bindings** and **220 internally reviewed Slither findings**. The earlier [integration/recovery evidence](reports/release-progress/README.md) retains its exact source snapshot; historical receipts do not validate subsequent changes. Actual route/service qualification, supported Ubuntu verification, staging and independent audit remain open.

The blocked [production inventory](config/production.example.json) uses schema 4 / `shared-pools-v2`. Its read-only validator requires the current economics, exact NFT quotas, helper bindings, randomness observations and actual staging evidence. A passing inventory is consistency evidence, never deployment approval.

```sh
python3 scripts/run_python_tests.py
python3 scripts/source_checks.py
bash scripts/install-deps.sh
bash scripts/verify.sh
```

See [development setup](docs/DEVELOPMENT.md), [roadmap](docs/ROADMAP.md), [security](SECURITY.md), and the [release checklist](docs/RELEASE_CHECKLIST.md). The compiler remains Solidity 0.8.26/Cancun, via IR with the existing optimizer profile. Dependencies and historical reviews remain pinned/preserved.
