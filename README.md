# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

**Selected pool (2026-10-24):** Robinhood Uniswap v4 native ETH/ZZZ `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`, static 1.002% LP fee, no hook. The observed protocol fee makes the combined fee about 1.101%. Hookless native admission and atomic `moveFunds` are the current candidate; external `exit` remains separately approved and paused. [Selection and limits](docs/POOL_SELECTION.md). Production remains NOT APPROVED.

**Latest development candidate:** [governed custody handoff](docs/GOVERNED_CUSTODY_HANDOFF.md) replaces the old LP bridge/pair stack. Normal exits consolidate principal into ZZZ; an explicit raw emergency exit avoids swaps. Royalty currencies use separate custody accounting. Whole-collection handoff is retained. [Current verification and limits](reports/custody-handoff/VERIFICATION.md). Undeployed; production approval and updated inventory/provider qualification remain open.

PoPL connects transferable NFTs to vault-managed liquidity. Activating an NFT attaches an LP allocation and unlocks two income streams: funded LP revenue and a separate share of NFT-sale royalties.

**Status: undeployed contract candidate; not approved for real funds.** The [website demo](https://popldemo.0xwave.com) uses simulated balances and transactions.

**Current development work (2026-10-24):** the [native accounting V2 candidate](reports/native-eth-port/VERIFICATION.md) carries actual ETH through Entry, Vault, LP settlement, fee reserves, indexed rewards and raw custody exits. Same-actual-pair fee-tier moves default to a 3% loss cap, now governance-adjustable up to 10%. ETH and WETH are distinct: atomic moves between them await an explicit conversion boundary. The separate custody `exit` supports reviewed external migration. Existing Anvil deployments remain on their original code.

**Before sealing:** qualify the [native V2 implementation and remaining boundaries](docs/NATIVE_ETH_ARCHITECTURE.md), qualify the [typed v4 conversion candidate](docs/TYPED_V4_ROUTES.md), native profiles and real services, then complete independent security review. [Bounded operating controls](docs/POST_SEAL_POLICY.md) now allow future VRF gas/confirmation tuning and a buyback execution ceiling below its immutable maximum. [Execution-loss policy](docs/EXECUTION_LOSS_POLICY.md) retains 1% / 1% / 3% defaults; governance may change each category up to a hard 10%, with gas separate and original pending-custody minima preserved. At the default 1%, ZZZ conversion still needs a cheaper qualified route. Mainnet rehearsal must use a separate deployment; there is no collection reset.

**Price security (2026-10-24):** [Two-source pricing and factual LP checks](docs/PRICE_SECURITY.md) are implemented in the undeployed candidate. Every priced asset requires two independently qualified USD sources. Entry freezes source/pair prices and operating limits before transfers/conversion; actual LP increments, raw spending and unchanged deployment spot are verified separately. Missing or stale prices, or disagreement above the selected **3%**, stop the contribution. The separate default **1% execution-loss cap** still applies; disagreement within 3% does not guarantee acceptance. No live feed pair is selected or qualified; production remains NOT APPROVED.

The [on-chain safety and cost review](reports/onchain-safety/REVIEW.md) adds bounded sequencer reads and reduces repeated strategy, contribution-storage and reward-checkpoint work. Final execution checks and economic limits remain; [scoped measurements](reports/onchain-safety/VERIFICATION.md) are local evidence, not live-provider qualification or independent audit.

**Pricing follow-up (2026-10-25):** [Dated reference readings and costs](reports/price-reference-20261025/OBSERVATION.md) are research only. Production source pairs remain unset; a pool-derived ZZZ estimate is not an independent oracle.

## Project navigation

| Purpose | Start here |
| --- | --- |
| Progress and remaining work | **[Project Todo](TODO.md)** - the single task list, with expandable acceptance criteria |
| Questions for the token/pool creator | [Creator tasks / ZZZ team](TODO.md#creator-tasks--zzz-team) - fee sharing, pricing, payments and market continuity |
| What is built and tested | [Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) - capabilities, boundaries and verification |
| Manage the protocol | **[Operator manual](docs/OPERATOR_MANUAL.md)** - exact controls, range/assets/pools, emergency stops and restart procedures |
| System design | [Architecture](docs/ARCHITECTURE.md) for interactions; [evolution and trust boundaries](docs/ARCHITECTURE_EVOLUTION.md) for migration limits; [Component map](docs/COMPONENT_STATUS.md) for each module's responsibilities |
| Production inventory | [Native V2 preflight](docs/PRODUCTION_PREFLIGHT.md) - explicit pricing V2, 15 helper bindings, approved pins, actual observations and release blockers |
| Contribution and valuation security | [Two-source prices and actual LP](docs/PRICE_SECURITY.md) - fixed transaction basis, conservative loss checks and remaining provider trust |
| Security and release | [Latest internal audit](reports/preproduction-audit-20261025/REVIEW.md), including open activation feasibility/review-cap gaps; [Security audit plan](docs/SECURITY_AUDIT_PLAN.md) for review criteria; [Release approval record](docs/RELEASE_CHECKLIST.md) for the final go/no-go decision |

## Architecture overview

| Layer | Owns this responsibility | Explore |
| --- | --- | --- |
| **1. Smart contracts** | Enforce ownership, LP custody, accounting and permissions on-chain. | [Contract components](#contract-components) |
| **2. Backend and operations** | Read confirmed state, prepare unsigned user transactions and operate authorized maintenance. | [Services and data flow](#backend-components) |
| **3. Frontend** | Explain the product and present NFT positions and wallet actions. Public simulation; separate local contract/browser-wallet profile. | [Website components](#frontend-components) |

<a id="contract-components"></a>

### 1. Smart contracts

The main activation path separates contribution routing, share accounting and venue execution:

```mermaid
flowchart LR
    Entry[Activation Entry] --> Vault[Vault: NFT share accounts]
    Vault --> Manager[Liquidity Manager]
    Manager --> Pool[Uniswap v4: shared LP]
```

| Component group | Responsibility and relationship | Source / design |
| --- | --- | --- |
| **NFT identity and artwork** | Records the current owner and immutable revealed traits. Metadata reads the NFT's current attached LP value to select its evolution. | [NFT](src/ZZZNFT.sol), [metadata](src/ZZZNFTMetadata.sol), [trait/reveal design](docs/NFT_METADATA.md) |
| **Activation and admission** | Entry authenticates the owner, checks admitted assets/routes, converts the contribution and binds its original value to the exact Vault call. The registry admits venues and enforces one contribution pool at a time. | [Entry](src/ZZZActivationEntry.sol), [typed v4 helper](src/ZZZV4RouteExecutor.sol), [asset policies](src/ZZZActivationAssets.sol), [pool registry](src/ZZZPoolRegistry.sol) |
| **Custody and per-NFT shares** | Vault owns the physical LP and records each NFT's nonredeemable shares. LiquidityManager executes typed venue operations; the budget helper checks contribution and maintenance loss limits. | [Vault](src/ZZZVault.sol), [LiquidityManager](src/ZZZLiquidityManager.sol), [budget helper](src/ZZZMigrationBudget.sol) |
| **LP revenue accounting** | Creator inboxes and venue collections feed FeeController. It allocates receipts to holder/collective balances and separate compound/buyback reserves. Membership gives each activated NFT one collective share. | [FeeController](src/ZZZFeeController.sol), [Rewards](src/ZZZRewards.sol), [Membership](src/ZZZMembership.sol), [creator intake](docs/EXTERNAL_REWARDS.md) |
| **Royalties and claims** | RoyaltyRewards preserves per-NFT entitlements, isolates optional currency outages and credits batch-converted ETH to the same NFTs. Current owners claim through either ledger or ClaimRouter. | [RoyaltyRewards](src/ZZZRoyaltyRewards.sol), [converter](src/ZZZRoyaltyConverter.sol), [ClaimRouter](src/ZZZClaimRouter.sol), [operator flow](docs/ROYALTY_SETTLEMENT.md) |
| **Valuation and maintenance** | Oracle requires two reviewed USD sources per asset. Its fixed pricing companion freezes contribution prices/limits and verifies marginal LP; Strategy defines guarded ranges and eligibility. Keeper maintenance stays within on-chain limits. | [Oracle](src/ZZZOracle.sol), [contribution pricing](src/ZZZContributionPricing.sol), [price security](docs/PRICE_SECURITY.md), [Strategy](src/ZZZStrategy.sol), [Compounder](src/ZZZCompounder.sol), [Buyback](src/ZZZBuyback.sol) |
| **Governance and permissions** | AccessController binds modules and enforces immediate authorized configuration, guardian pause and keeper authorization. Sealing fixes module bindings; constrained configuration remains available. | [AccessController](src/ZZZAccessController.sol), [authority and change boundaries](docs/CHANGE_AND_RECOVERY.md) |
| **Recovery and migration** | Migration atomically moves LP between admitted pools with identical actual currencies and governs all-ZZZ or explicit raw custody exits. Native raw exit sends ETH/ZZZ without WETH. Actual funded local LP is required for completion; external custody is trusted. A separate versioned handoff carries ownership, ledgers and backing to one compatible replacement. Cross-version and future-chain completion remain open. | [Migration](src/ZZZMigration.sol), [CanonicalHandoff](src/ZZZCanonicalHandoff.sol), [handoff scope](docs/CANONICAL_HANDOFF.md) |

**Custody authority:** holders cannot redeem principal. Governance can send it to an approved external EOA/contract, which is explicitly trusted to preserve/return it. Royalty custody separately suspends the exited currency until full backing returns. The source cannot force an external custodian to return funds.

Many NFTs share **one physical LP per pool/strategy**, with independent share accounts. Maintenance operates on the shared position. The registry permits **one deposits-enabled contribution pool at a time**, selected for the existing hookless ETH/ZZZ pool after qualification. Governance can disable it and enable a reviewed replacement without deleting historical pools; [switch procedure](docs/OPERATOR_MANUAL.md#one-contribution-pool-at-a-time). The Vault allows four permanently admitted/historical custody buckets, including reservations and imports. An existing bucket's migration or return reuses its slot. See the [detailed interactions](docs/ARCHITECTURE.md) and [complete module/helper map](docs/COMPONENT_STATUS.md).

<a id="backend-components"></a>

### 2. Backend and operations

Read services serve confirmed chain state. Transaction preparation returns an unsigned request for the user's wallet. The keeper uses a separate operator signer for authorized maintenance; it does not sign user activations.

| Service | Responsibility and relationship | Code / operating reference |
| --- | --- | --- |
| **Event indexer** | Reads confirmed contract logs into SQLite, detects bounded reorgs and supplies replay history for ownership and claims. | [Indexer](indexer/monitor.py), [event schema](indexer/event_schema.json), [history requirements](docs/FRONTEND_HISTORY.md) |
| **HTTP admission and isolation** | Bounded isolated workers, per-client concurrency/read/preparation budgets, finite connections and deadlines, explicit overload and cleanup quarantine. Guarded proxy identity/origin; no signer. | [Worker pool](frontend_api/worker.py), [client admission](frontend_api/admission.py), [HTTP bounds](frontend_api/http_runtime.py), [proxy and recovery](docs/API_INGRESS.md) |
| **Read API** | Verifies deployment/lifecycle at a confirmed block, then reads current owners, LP values and funded balances. Optional current-ledger reporting separates ETH/source balances and deferred royalty eligibility; complete pinned predecessor replay carries lifetime claims and conversion credits across same-chain handoffs. | [Service](frontend_api/service.py), [lifecycle](frontend_api/lifecycle.py), [lineage replay](frontend_api/lineage.py), [API contract](docs/FRONTEND_API.md), [royalty reporting](docs/ROYALTY_REPORTING.md) |
| **Earnings history** | Replays actual processed LP/royalty earnings per collection and NFT, preserving weights, fractions and complete same-chain lineage. Optional reviewed prices value original earned currencies at today's confirmed snapshot. Claims, conversions and current balances stay separate. | [Replay/API](frontend_api/earnings.py), [configuration and operations](docs/EARNINGS_HISTORY.md), [evidence](reports/earnings-history/VERIFICATION.md) |
| **Mint/claim preparation** | Builds exact 0.05 ETH mints or up to 32 owner-authenticated LP/royalty claim operations; verifies lifecycle, simulates at a canonical hash and returns a short-lived unsigned draft with separate bounded gas estimates. Opt-in policy; no signer. | [Preparer](frontend_api/transactions.py), [configuration and wallet rules](docs/FRONTEND_TRANSACTIONS.md), [evidence](reports/wallet-preparation/VERIFICATION.md) |
| **Activation preparation** | Checks asset/route/feed bindings, simulates the complete Entry call, measures new LP, and returns exact unsigned calldata and separate gas. Missing approval produces an approval step before re-quoting. | [Preparation](frontend_api/activation.py), [opt-in endpoint](frontend_api/activation_server.py), [integration sequence](docs/ACTIVATION_PREPARATION.md) |
| **Keeper** | Discovers shared buckets, checks eligibility, simulates and submits authorized upkeep. Persists intents, receipts and budgets for recovery; optional metadata watching uses the same bounded transaction path. | [Monitor](keeper/monitor.py), [execution](keeper/ops.py), [recovery runbook](docs/KEEPER_RECOVERY.md) |
| **Release preflight** | Explicit current native-V2 inventory validation and bounded read-only same-block observation. Actual service/evidence qualification stays separate; no signer or deployment authority. | [Gate](scripts/validate-production-config.py), [observer](scripts/observe-production-config.py), [operator sequence](docs/PRODUCTION_PREFLIGHT.md) |
| **Revenue measurement** | Calculates proposed active-liquidity shares for creator-payment reconciliation. Measurements do not collect money or create claimable rewards. | [Measurement tool](zzz_ops/revenue_share.py), [agreement and calculation model](docs/REVENUE_SHARE.md) |

These services require qualified RPC/archive providers, feeds, configuration and operating procedures. Hosting and live integration remain open. The API does not hold user keys; the contracts still enforce transaction permissions and accounting.

<a id="frontend-components"></a>

### 3. Frontend

The website is maintained in [AAA-website](https://github.com/ABEF/AAA-website). Its current components are:

| Component | Current responsibility | Website source |
| --- | --- | --- |
| **Pages and interactions** | Navigation, collection/portfolio cards, dialogs, contribution and claim interfaces. | [app.js](https://github.com/ABEF/AAA-website/blob/main/app.js) |
| **Demo data and accounting** | Example NFTs, balances, contribution events and simulated claims. This model must be replaced by confirmed API data for live use. | [domain.js](https://github.com/ABEF/AAA-website/blob/main/domain.js) |
| **Wallet connection** | Connects a browser wallet and handles account/chain changes. The separate reviewed Anvil-only profile handles signing/receipt recovery. Public signing remains disabled; native-V2 deployment and actual wallet-provider qualification remain open. | [wallet.js](https://github.com/ABEF/AAA-website/blob/main/wallet.js) |
| **Artwork catalogue** | Resolves palette, pattern, rarity and evolution assets for display. On-chain metadata remains authoritative for a real NFT. | [artworks.js](https://github.com/ABEF/AAA-website/blob/main/artworks.js), [palette-system.js](https://github.com/ABEF/AAA-website/blob/main/palette-system.js) |

The target live flow is **website -> read/preparation API -> user wallet confirmation -> contracts -> confirmed receipt/indexer/API refresh**. The public/default website still simulates minting, LP contributions and claims; the separate [local contract mode](docs/LOCAL_WEBSITE.md) uses disposable Anvil contracts; see the [frontend integration tasks](TODO.md#frontend).

## NFT lifecycle

| Step | Rule |
| --- | --- |
| **Mint** | Pay exactly **0.05 ETH** to the immutable mint recipient for a dormant NFT. Minting adds supply, not liquidity or reward eligibility. |
| **Activate** | After reveal, the conservative original input value must reach **$100**. Conversion and new LP deployment share the captured execution limit (1% by default, governance maximum 10%); the upper input / lower LP price bounds tighten its floor. Network gas is separate. |
| **Add liquidity** | Contributions from **$5 in conservative original input value** grow the same NFT under the captured contribution limit; gas is separate. Higher pool minima apply. Existing holders' assets cannot subsidize the new LP floor; a top-up adds no collective membership. |
| **Hold or transfer** | The current owner can claim its funded balances. Transfers carry the LP allocation, remaining unclaimed balances and future fee rights. A seller can claim before a transfer, so an earlier listing balance is not guaranteed to the buyer. |

**LP principal cannot be redeemed by holders.** It remains managed by the protocol for rebalancing, compounding and approved migration. A right to future funded fees has no expiry, but does not guarantee future revenue or capital value.

Target activation assets are **ETH, ZZZ, USDG and USDC**, admitted by reviewed address and route. Each economic asset needs two independently qualified USD sources, including depeg-aware USDG/USDC prices. Actual routes and feed pairs remain unqualified; USDC has no qualified funded route. The [atomic Entry](docs/ACTIVATION_ENTRY.md) binds the original contribution value through conversion into LP; [route qualification](docs/ACTIVATION_ROUTING.md) covers the remaining integration work.

## Revenue and claims

### LP revenue and optional funding

The allocation is fixed in the current contracts:

| Use | Share | Basis |
| --- | --- | --- |
| Individual NFT holders | **80%** | Proportional to each NFT's shares in the earning LP bucket |
| Collective rewards | **10%** | Equal per activated NFT, across pools |
| LP compounding | **5%** | Reserved for reinvestment in the earning bucket |
| ZZZ buyback and burn | **5%** | Reserved for approved execution |

Rarity does not change LP or collective weights; there is no Power multiplier. Actual receipts allocate in batches of 20 raw token units, with a documented sub-20-unit incumbent-dust exception at membership/migration boundaries. Returned remote holder rewards are already allocated and are not split again. See [accounting and timing](docs/ECONOMICS.md).

The selected hookless native ETH/ZZZ pool has a static **1.002% LP fee**. PoPL allocates only actual fees earned by its own position; Uniswap's separate protocol fee is not PoPL revenue. The observed combined swap fee is approximately 1.101%. Historical Pons creator payments are optional external funding. Native V2 accounts for ETH directly; already-native holder fees need no conversion. ZZZ reward conversion defaults to a **1% loss cap** (governed maximum 10%), gas separate, and needs a cheaper qualified route. See [pool selection](docs/POOL_SELECTION.md).

### NFT-sale royalties

ERC-2981 requests **5% of sale value** to the immutable royalty receiver. **100% of eligible receipts** are shared among activated NFTs at **Commun x1 / Rare x2 / Legendary x3**, independently of LP shares. Prefunds, pre-admission receipts and payments with no eligible members stay quarantined. ERC-2981 does not enforce marketplace payment. The optional keeper converts earned WETH/stablecoin royalties into ETH in guarded batches, preserving each NFT's share; the default 1% execution-loss cap excludes gas and is governed within a hard 10% maximum. Failed optional currencies defer only their new eligibility, with earlier royalties protected. See the [settlement runbook](docs/ROYALTY_SETTLEMENT.md) and [separate royalty ledger](docs/NFT_METADATA.md#separate-marketplace-royalties).

Claims follow funding events, not a per-minute clock. LP claims use allocated balances; royalty claims also synchronize pending admitted receipts. Direct claims take one NFT and asset; the [claim router](docs/CLAIM_ROUTER.md) supports up to **32 mixed LP/royalty operations**, paid to the current owner. [Timing and keeper schedules](docs/OPERATIONS.md#reward-timing-and-maintenance-schedule) explain when processing occurs.

## Collection and artwork

- **Supply:** at most **1,000 NFTs**, with exact eventual quotas of **600 Commun / 300 Rare / 100 Legendary**.
- **Assignment:** an authenticated random draw selects fixed inventory entries without replacement, finalized in mint order. There is no administrator trait selection or reroll. A stalled earlier request can block later reveals; live VRF qualification remains open.
- **Fixed traits:** rarity, palette and pattern never change. Eight colors form 58 palettes across monochrome, bicolor and tricolor styles; four patterns produce **2,784 rendered evolution states**. Palette and pattern do not change rewards; rarity affects only royalty weight.
- **Evolution:** Dormant until activation; afterward, current marked LP value selects Activated, **Enhanced from $1,000**, or **Singularity from $10,000**. Falling value can downgrade art without removing activation or fee rights. Remote or stale valuation is explicitly unavailable.

The [metadata specification](docs/NFT_METADATA.md) and [artwork catalogue](design/nft-metadata/palette-system-v1/README.md) detail inventory quotas, duplicate limits, palettes and patterns. The [IPFS bundle](docs/ARTWORK_PUBLICATION.md) is prepared; provider selection, publication and marketplace refresh testing remain open.

## Governance, custody and recovery

### Authority and configuration

| Role | Authority | Boundary |
| --- | --- | --- |
| **Governance multisig** | Approves configuration and supported recovery operations through the zero-delay governance controller. | Approved modules, destinations and replacement code require security review; governance remains a trust dependency. |
| **Guardian** | Pauses operations during an incident. | Cannot unpause or withdraw principal; unpause belongs to governance. |
| **Keeper** | Executes eligible maintenance within contract permissions and economic limits. | Cannot change governance policy or bypass execution guards. |

Production addresses are not selected. The [address inventory](docs/DEPLOYMENT_ADDRESSES.md) separates authority wallets, deployed contracts and network dependencies.

**Sealing fixes module implementations and local venue bindings.** Governance can still configure supported assets, routes, feeds, destinations and strategy parameters within existing controls. New algorithms or unsupported venues need separately reviewed compatible deployments, rather than an in-place code update. The [change and recovery matrix](docs/CHANGE_AND_RECOVERY.md) details these boundaries.

The [operator manual](docs/OPERATOR_MANUAL.md#stop-controls) includes a governed
mint-only pause and disable-only pool controls that work without healthy pool
dependencies. Re-enabling a pool still requires full validation; existing rights
retain their independent guards. See [scoped verification](reports/operator-controls/VERIFICATION.md).

### Recovery paths

| Situation | Supported path and limits | Reference |
| --- | --- | --- |
| **Pause and park LP** | Governance can close LP into Vault custody while globally paused, using an exact snapshot and raw output minimums. Parking omits source-price reads and creator-inbox synchronization; resume requires fresh valuation and execution guards. Failed tokens or venues can still prevent movement. | [Custody parking](docs/CUSTODY_PARKING.md) |
| **Move LP between local pools** | Ordinary moves retain same-ordered-pair guards and the governed aggregate loss floor. Different-pair and ETH/WETH conversion need a reviewed compatible implementation; governed external custody is a separate workflow. Moving LP alone does not relocate NFT ownership or reward ledgers. | [Move/exit procedure](docs/GOVERNED_CUSTODY_HANDOFF.md), [migration safety](docs/MIGRATION_SAFETY.md) |
| **Review replacement NFT holders** | A confirmed owner/code inventory identifies contracts and delegated accounts requiring escrow release/claim review; rescan after freeze. Complete inventory is not migration approval. | [Holder preflight](docs/HOLDER_PREFLIGHT.md) |
| **Replace the whole deployment on the same chain** | The handoff candidate freezes and carries NFT ownership, both reward ledgers and exact classified backing to one replacement. Retirement/activation is atomic, with a restored funded abort path before retirement. Reviewed replacement code is an accepted governance trust boundary. | [Canonical handoff](docs/CANONICAL_HANDOFF.md) |
| **Relocate the collection to another chain** | Verified source finality, authenticated channel closure, new lineage/message semantics and reviewed transport remain pre-seal work. There is no multisig-only activation override. Recovery after a permanent source-chain halt is deferred. | [Canonical migration design](docs/CANONICAL_MIGRATION_DESIGN.md) |

**Real bridging remains disabled** pending independent destination-admission review, provider/backing review and multi-chain rehearsals. Local permanent capacity reservation is implemented; the source does not authenticate remote admission proof. The [security audit plan](docs/SECURITY_AUDIT_PLAN.md) covers these cross-contract and external-dependency risks.

## Keeper and operating services

The keeper **defaults to dry run**. Full keeper/state-lock operation requires **Linux/Unix and Python 3.11+**.

- **Polling:** the example checks every ten minutes; this is not a guaranteed execution schedule.
- **Rebalancing:** price movement or an approved range change must make the position eligible. Cooldown, fresh prices and execution guards still apply. See [range-policy behavior](docs/RANGE_POLICY_UPDATES.md).
- **Metadata:** the optional watcher is disabled by default and uses the same bounded transaction path.

| Operating task | Start here |
| --- | --- |
| Select RPC, pricing, randomness and other dependencies | [Production service decisions](docs/PRODUCTION_SERVICES.md) |
| Configure and run maintenance | [Operations guide](docs/OPERATIONS.md) |
| Recover after an outage, lost state or server loss | [Recovery runbook](docs/KEEPER_RECOVERY.md) |
| Rehearse failures and assess operating evidence | [Keeper rehearsals](docs/KEEPER_REHEARSALS.md) |
| Assess remaining security and availability risks | [Internal keeper review](reports/keeper-recovery/REVIEW.md) |

## Verification and release status

**Release decision: NOT APPROVED.** Local verification, published CI and independent release approval are separate requirements. Each report applies only to its recorded source, configuration and test scope; no full current-source regression is claimed by combining historical counts.

### Find the relevant evidence

| Area | Evidence | Scope |
| --- | --- | --- |
| **LP accounting and maintenance** | [Dynamic liquidity](reports/dynamic-liquidity/VERIFICATION.md), [range-policy updates](reports/range-policy/VERIFICATION.md) | Contribution/valuation guards, aggregate rebalance budget, range-change eligibility and targeted venue/backend checks. |
| **Backend integration** | [Activation preparation](reports/activation-preparation/VERIFICATION.md), [API lifecycle](reports/frontend-lifecycle/VERIFICATION.md), [claim-history lineage](reports/frontend-lineage/VERIFICATION.md) | Scoped transaction preparation and confirmed reads; not hosted-service or live website qualification. |
| **Same-chain replacement** | [Canonical handoff](reports/canonical-handoff/VERIFICATION.md) | Handoff accounting and regression evidence for its recorded snapshot. Later changed paths use the separate reports above. |
| **Local $1 test build** | [Rehearsal verification](reports/one-dollar-rehearsal/VERIFICATION.md) | Separate generated copy with mock services; not the production binary or live Pons execution. |
| **Published revision** | [GitHub Actions](https://github.com/ABEF/AAA/actions) | Check the exact commit and required jobs. Local results do not establish a green published workflow. |

<details>
<summary>Earlier verification and review history</summary>

- [NFT economic-rights verification](reports/nft-rights-audit/VERIFICATION.md): its historical 531 Solidity passes, two expected fork skips, 23 size gates and 65,536-call invariant run retain their original scope. The accompanying [internal review](reports/nft-rights-audit/REVIEW.md) records findings and risks.
- [Architecture evolution](reports/architecture-evolution/VERIFICATION.md) and [migration safety](reports/migration-safety/VERIFICATION.md): earlier source-specific evidence; neither verifies later handoff or maintenance changes.
- [Report index](reports/README.md): remaining historical receipts and their context.

</details>

### Production approval

Remaining work is tracked only in the [Project Todo](TODO.md). It includes:

- **Dependencies and configuration:** qualified market/input routes, tokens, feeds and VRF; authority addresses and creator-payment terms.
- **Integration and operations:** live frontend/backend flows, target-chain gas/strategy qualification and operating rehearsals.
- **Independent assurance:** external audit, remediation and final configuration/release review.

The [production inventory](config/production.example.json) records the exact deployment configuration and evidence. The [release approval record](docs/RELEASE_CHECKLIST.md) records the final go/no-go decision. Internal reviews and local passes do not replace either.

## Try the local browser test

The [local setup guide](docs/LOCAL_TEST_STACK.md) starts an isolated Anvil deployment,
confirmed API/indexer and browser panel with disposable test wallets. The
[existing website integration](docs/LOCAL_WEBSITE.md) is available at `/app/`
on the same local origin, with actual holdings, history and explicit transaction
confirmations. Mint, activate,
add LP, fund fees/royalties, rebalance, transfer and claim without public funds.
The venue, prices and randomness are test substitutes; the public website is unchanged.

## Development

### Setup and verification

Use the [supported development environment](docs/DEVELOPMENT.md), including Linux/Unix or WSL for complete off-chain verification. From the repository root:

```sh
# Install pinned dependencies when setting up the checkout.
bash scripts/install-deps.sh

# Run full verification when the change or release requires it.
bash scripts/verify.sh
```

The verifier runs Python/source checks, normal build/size checks and offline Solidity tests. The toolchain uses **Solidity 0.8.26, Cancun and the configured via-IR optimizer profile**. During iteration, run checks for the affected behavior and reuse unchanged source-bound evidence. The development guide provides explicit fork and static-analysis commands. These commands do not deploy public contracts.

### Small-value experiments

The [local $1 activation rehearsal](docs/ONE_DOLLAR_REHEARSAL.md) generates an isolated test build. It retains the **1% execution-loss limit** and **0.05 ETH mint price**; production activation remains **$100**. It does not enable live wallet transactions.

### Keep project records consistent

When implementation or evidence changes, follow the [Todo maintenance procedure](docs/TODO_WORKFLOW.md): update the [task ledger](docs/project-todo.json), reconcile the [feature/evidence reference](docs/IMPLEMENTATION_STATUS.md), then regenerate and check the task list:

```sh
python3 scripts/sync-project-todo.py
python3 scripts/sync-project-todo.py --check
```

Keep local work, GitHub publication, test evidence and deployment status explicit. The central Todo owns task status; feature references and release records have their separate purposes.

### Holder payout currency

The product requires rewards claimable in ETH. The current candidate still pays
LP rewards in their source ERC20 currency; the implemented ETH converter handles
marketplace royalties only. This is an open pre-seal requirement, documented in
the [payout audit](reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md) and
[central Todo](TODO.md#task-lp-eth-settlement).

Historical contribution UI rehearsal: four visible input choices (ZZZ/USDG/USDC/ETH), a dedicated contribution dialog and confirmed per-NFT evolution refresh. The [named local rehearsal](docs/LOCAL_TEST_STACK.md#named-input-local-rehearsal) retains its original WETH-accounted fixtures. Native V2 uses actual ETH; its website profile and public route/payout qualification remain open.

## LP reward settlement

The development candidate converts allocated holder LP rewards to native ETH with a **1% execution-loss cap and separate gas**. Credits stay with the same NFT; failed conversion preserves its source balances. [Conversion, claims and operator procedure](docs/LP_ETH_SETTLEMENT.md) | [Scoped verification](reports/lp-eth-settlement/VERIFICATION.md). Public routes and production approval remain open.
