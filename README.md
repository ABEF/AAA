# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

PoPL connects transferable NFTs to vault-managed liquidity. Activation attaches
an LP allocation and unlocks funded LP fees plus a separate share of NFT-sale
royalties. Holders cannot redeem principal; governance can approve trusted
external custody for recovery or migration.

**Status: undeployed candidate; production NOT APPROVED.** The
[public website](https://popldemo.0xwave.com) simulates transactions. Existing
Anvil deployments retain their original code; public signing remains disabled.

| Current design | Implementation and remaining boundary |
| --- | --- |
| Market and custody | Robinhood v4 native ETH/ZZZ, selected pool `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`: static 1.002% LP fee, no hook; recorded combined fee about 1.101%. Protocol fees can change. Native V2 accounts for actual ETH. [Pool decision](docs/POOL_SELECTION.md), [native scope](docs/NATIVE_ETH_ARCHITECTURE.md). |
| Contributions and prices | Native ETH or one fixed ZZZ only. Source admission, the native pool, immutable buyback and normal exit use that same reviewed ZZZ identity. Minimum $100 activation / $5 growth, two reviewed USD sources per asset and 3% disagreement tolerance. Actual added LP must meet the captured 2% default loss budget; gas separate. Reviewed Entry V1 also binds a caller maximum before funds move. [Price security](docs/PRICE_SECURITY.md), [reviewed policy](docs/EXECUTION_LOSS_POLICY.md#review-time-policy-binding). |
| Maintenance and conversion | Conversion defaults to 1%, maintenance to 3%; governance may immediately set each category up to 10%. Bounded placement/idle reinvestment and opt-in reviewed +/-25/50% keeper widths preserve accounting. At 1%, ZZZ conversion needs a cheaper qualified route. [Idle](docs/IDLE_AND_DUST.md), [range policy](docs/RANGE_POLICY_UPDATES.md), [operating controls](docs/POST_SEAL_POLICY.md). |
| Movement and recovery | Same-actual-pair pool moves; separate approved paused all-ZZZ exit or explicit raw exit sending the actual assets (ETH/ZZZ for the selected pool), without swaps. External custodian is trusted. Same-chain whole-collection handoff remains; integrated bridge, remote-proof and creator-inbox paths are removed. No reset/sweep. [Operator procedure](docs/GOVERNED_CUSTODY_HANDOFF.md). |
| Release gates | Actual routes/independent feeds/VRF, authorities, native wallet/service acceptance and OpenSea integration, gas/strategy economics, operating rehearsals and independent audit/remediation remain open. [Sole Todo](TODO.md), [latest internal review](reports/daily-security-20261025/REVIEW.md). |

The native website read/unsigned profile is implemented in source. The
[latest review](reports/daily-security-20261025/REVIEW.md) covers the combined
financial, custody and service changes. The source-bound reference covers
31 contracts and 643 functions. Registry runtime is 10,131 bytes; Vault runtime
is 23,889 bytes with 687 bytes of headroom. Access construction is tight:
one proposer/one executor needs 49,123 total initcode bytes (29 bytes below the
limit); exact release role-array arguments require qualification. [Integration and operator boundaries](docs/NATIVE_WEBSITE_PROFILE.md).

Optional [Pyth source compatibility](docs/PYTH_PRICE_SOURCE.md), strict current
mint/VRF qualification and [frozen audit packaging](docs/FROZEN_REVIEW_BUNDLE.md)
are implemented. OpenSea still needs a compatible primary-mint path: buyer pays
0.05ETH gross, recipient receives net after the actual platform fee, gas separate.
No source pair, updater, provider or marketplace acceptance is approved.

Source-scoped local evidence establishes particular behavior, not production
qualification. Dated [price research](reports/price-reference-20261025/OBSERVATION.md)
does not select independent feeds or provide live prices.

## Project navigation

| Purpose | Start here |
| --- | --- |
| Progress and remaining work | **[Project Todo](TODO.md)** - the single task list, with expandable acceptance criteria |
| Questions for the token/pool creator | [Creator tasks / ZZZ team](TODO.md#creator-tasks--zzz-team) - independent ZZZ pricing, token controls and market continuity |
| What is built and tested | [Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) - capabilities, boundaries and verification |
| Manage the protocol | **[Operator manual](docs/OPERATOR_MANUAL.md)** - exact controls, range/assets/pools, emergency stops and restart procedures |
| System design | [Architecture](docs/ARCHITECTURE.md) for interactions; [evolution and trust boundaries](docs/ARCHITECTURE_EVOLUTION.md) for migration limits; [Component map](docs/COMPONENT_STATUS.md) for each module's responsibilities |
| Callable reads and writes | [Function reference](docs/CONTRACT_FUNCTIONS.md) - purpose, permissions, inputs, outputs and tuple fields, linked from the operator manual |
| Production inventory | [Native V2 preflight](docs/PRODUCTION_PREFLIGHT.md) - explicit pricing V2, 15 helper bindings, approved pins, actual observations and release blockers |
| Contribution and valuation security | [Two-source prices and actual LP](docs/PRICE_SECURITY.md) - fixed transaction basis, conservative loss checks and remaining provider trust |
| Security and release | [Latest internal review](reports/daily-security-20261025/REVIEW.md), with scoped fixes and remaining qualification; [Security audit plan](docs/SECURITY_AUDIT_PLAN.md) for review criteria; [Release approval record](docs/RELEASE_CHECKLIST.md) for the final go/no-go decision |

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
| **Activation and admission** | Reviewed Entry authenticates the owner, bounds the captured loss policy by the caller maximum, accepts only native ETH/reviewed ZZZ and checks routes and binds original contribution value to the exact Vault call. The registry admits venues and enforces one contribution pool at a time. | [Entry](src/ZZZActivationEntry.sol), [typed v4 helper](src/ZZZV4RouteExecutor.sol), [asset policies](src/ZZZActivationAssets.sol), [pool registry](src/ZZZPoolRegistry.sol) |
| **Custody and per-NFT shares** | Vault owns the physical LP and records each NFT's nonredeemable shares. LiquidityManager executes typed venue operations; the budget helper checks contribution and maintenance loss limits. | [Vault](src/ZZZVault.sol), [LiquidityManager](src/ZZZLiquidityManager.sol), [budget helper](src/ZZZMigrationBudget.sol) |
| **LP revenue accounting** | Actual local venue collections feed FeeController. It allocates receipts to holder/collective balances and separate compound/buyback reserves. Membership gives each activated NFT one collective share. | [FeeController](src/ZZZFeeController.sol), [Rewards](src/ZZZRewards.sol), [Membership](src/ZZZMembership.sol) |
| **Royalties and claims** | RoyaltyRewards preserves per-NFT entitlements, isolates optional currency outages and credits batch-converted ETH to the same NFTs. Current owners claim through either ledger or ClaimRouter. | [RoyaltyRewards](src/ZZZRoyaltyRewards.sol), [converter](src/ZZZRoyaltyConverter.sol), [ClaimRouter](src/ZZZClaimRouter.sol), [operator flow](docs/ROYALTY_SETTLEMENT.md) |
| **Valuation and maintenance** | Oracle requires two reviewed USD sources per asset. Its fixed pricing companion freezes contribution prices/limits and verifies marginal LP; Strategy defines guarded ranges and eligibility. Keeper maintenance stays within on-chain limits. | [Oracle](src/ZZZOracle.sol), [contribution pricing](src/ZZZContributionPricing.sol), [price security](docs/PRICE_SECURITY.md), [optional Pyth source](src/ZZZPythPriceFeed.sol), [Strategy](src/ZZZStrategy.sol), [Compounder](src/ZZZCompounder.sol), [Buyback](src/ZZZBuyback.sol) |
| **Governance and permissions** | AccessController binds modules and enforces immediate authorized configuration, guardian pause and keeper authorization. Sealing fixes module bindings; constrained configuration remains available. | [AccessController](src/ZZZAccessController.sol), [authority and change boundaries](docs/CHANGE_AND_RECOVERY.md) |
| **Recovery and migration** | Migration atomically moves LP between admitted pools with identical actual currencies and governs all-ZZZ or explicit raw custody exits. Native raw exit sends ETH/ZZZ without WETH. Actual funded local LP is required for completion; external custody is trusted. A separate versioned handoff carries ownership, ledgers and backing to one compatible replacement. Cross-version/future-chain handoff is outside this release. | [Migration](src/ZZZMigration.sol), [CanonicalHandoff](src/ZZZCanonicalHandoff.sol), [handoff scope](docs/CANONICAL_HANDOFF.md) |

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
| **Claim and local-mint preparation** | Builds up to 32 owner-authenticated LP/royalty claim operations with canonical simulation and separate gas estimates. Local/historical mint drafts remain test tools; the current release profile rejects unqualified OpenSea minting. Short-lived unsigned reviews only; no signer. | [Preparer](frontend_api/transactions.py), [configuration and wallet rules](docs/FRONTEND_TRANSACTIONS.md), [mint qualification](docs/MINT_INTEGRATION_QUALIFICATION.md) |
| **Activation preparation** | Checks asset/route/feed bindings, simulates the complete Entry call, measures new LP, and returns exact unsigned calldata and separate gas. Missing approval produces an approval step before re-quoting. | [Preparation](frontend_api/activation.py), [opt-in endpoint](frontend_api/activation_server.py), [integration sequence](docs/ACTIVATION_PREPARATION.md) |
| **Keeper** | Discovers shared buckets, checks eligibility, simulates and submits authorized upkeep. Persists intents, receipts and budgets for recovery; optional metadata watching uses the same bounded transaction path. | [Monitor](keeper/monitor.py), [execution](keeper/ops.py), [recovery runbook](docs/KEEPER_RECOVERY.md) |
| **Release preflight** | Explicit current native-V2 inventory validation and bounded read-only same-block observation. Actual service/evidence qualification stays separate; no signer or deployment authority. | [Gate](scripts/validate-production-config.py), [observer](scripts/observe-production-config.py), [operator sequence](docs/PRODUCTION_PREFLIGHT.md) |

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
| **Mint** | Buyer mint price is **0.05 ETH**, gas separate. Current direct mint pays it all to the immutable recipient; the required OpenSea integration pays the recipient net of its actual platform fee. Minting adds supply, not liquidity or reward eligibility. |
| **Activate** | After reveal, the conservative original input value must reach **$100**. Conversion and new LP deployment share the captured execution limit (2% by default, governance maximum 10%); the upper input / lower LP price bounds tighten its floor. Network gas is separate. |
| **Add liquidity** | Contributions from **$5 in conservative original input value** grow the same NFT under the captured contribution limit; gas is separate. Higher pool minima apply. Existing holders' assets cannot subsidize the new LP floor; a top-up adds no collective membership. |
| **Hold or transfer** | The current owner can claim its funded balances. Transfers carry the LP allocation, remaining unclaimed balances and future fee rights. A seller can claim before a transfer, so an earlier listing balance is not guaranteed to the buyer. |

**LP principal cannot be redeemed by holders.** It remains managed by the protocol for rebalancing, compounding and approved migration. A right to future funded fees has no expiry, but does not guarantee future revenue or capital value.

Activation and growth accept **native ETH or the fixed ZZZ token only**. USDG,
USDC and WETH are not user input options. Independent ETH/ZZZ feed pairs and
actual routes remain unqualified. The [atomic Entry](docs/ACTIVATION_ENTRY.md)
binds original contribution value through conversion into LP. Marketplace
royalty currencies and internal conversion assets have separate admission rules;
they do not expand these two contribution inputs.

## Revenue and claims

### LP trading revenue

The allocation is fixed in the current contracts:

| Use | Share | Basis |
| --- | --- | --- |
| Individual NFT holders | **80%** | Proportional to each NFT's shares in the earning LP bucket |
| Collective rewards | **10%** | Equal per activated NFT, across pools |
| LP compounding | **5%** | Reserved for reinvestment in the earning bucket |
| ZZZ buyback and burn | **5%** | Reserved for approved execution |

Rarity does not change LP or collective weights; there is no Power multiplier.
Only actual local venue collections enter this allocation. Creator-payment inboxes
and remote-fee intake are removed. Receipts allocate in batches of 20 raw token
units, with a documented sub-20-unit incumbent-dust exception at membership/move
boundaries. Already allocated rewards, conversions, claims and custody returns
are not new revenue and receive no second split. See [accounting and timing](docs/ECONOMICS.md).

The selected hookless native ETH/ZZZ pool has a static **1.002% LP fee**. PoPL allocates only actual fees earned by its own position; Uniswap's separate protocol fee is not PoPL revenue. The observed combined swap fee is approximately 1.101%. Native V2 accounts for ETH directly; already-native holder fees need no conversion. ZZZ reward conversion defaults to a **1% loss cap** (governed maximum 10%), gas separate, and needs a cheaper qualified route. See [pool selection](docs/POOL_SELECTION.md).

### NFT-sale royalties

ERC-2981 requests **5% of sale value** to the immutable royalty receiver. **100% of eligible receipts** are shared among activated NFTs at **Commun x1 / Rare x2 / Legendary x3**, independently of LP shares. Prefunds, pre-admission receipts and payments with no eligible members stay quarantined. ERC-2981 does not enforce marketplace payment. The optional keeper converts earned WETH/stablecoin royalties into ETH in guarded batches, preserving each NFT's share; the default 1% execution-loss cap excludes gas and is governed within a hard 10% maximum. Failed optional currencies defer only their new eligibility, with earlier royalties protected. See the [settlement runbook](docs/ROYALTY_SETTLEMENT.md) and [separate royalty ledger](docs/NFT_METADATA.md#separate-marketplace-royalties).

Claims follow funding events, not a per-minute clock. LP claims use allocated balances; royalty claims also synchronize pending admitted receipts. Direct claims take one NFT and asset; the [claim router](docs/CLAIM_ROUTER.md) supports up to **32 mixed LP/royalty operations**, paid to the current owner. [Timing and keeper schedules](docs/OPERATIONS.md) explain when processing occurs.

The candidate settles both LP rewards and royalties in **native ETH** through
separate guarded converters, preserving each NFT's entitlement. Already-native
fees need no conversion; earned non-ETH balances remain source-currency claims
until converted. An owner can explicitly claim the source asset if it works;
an ETH-only display must not report an unconverted balance as ETH. Conversion
defaults to 1% loss, gas separate, with governance bounded at 10%. Actual routes,
conversion latency and public operation remain unqualified. See
[LP settlement](docs/LP_ETH_SETTLEMENT.md) and [royalty settlement](docs/ROYALTY_SETTLEMENT.md).

## Collection and artwork

- **Supply:** at most **1,000 NFTs**, with exact eventual quotas of **600 Commun / 300 Rare / 100 Legendary**.
- **Assignment:** an authenticated random draw selects fixed inventory entries without replacement, finalized in mint order. There is no administrator trait selection or reroll. A stalled earlier request can block later reveals; live VRF qualification remains open.
- **Fixed traits:** rarity, palette and pattern never change. Eight colors form 58 palettes across monochrome, bicolor and tricolor styles; four patterns produce **2,784 rendered evolution states**. Palette and pattern do not change rewards; rarity affects only royalty weight.
- **Evolution:** Dormant until activation; afterward, current marked LP value selects Activated, **Enhanced from $1,000**, or **Singularity from $10,000**. Falling value can downgrade art without removing activation or fee rights. Unavailable prices or principal outside protocol custody produce an unavailable valuation, not a fabricated balance.

The [metadata specification](docs/NFT_METADATA.md) and [artwork catalogue](design/nft-metadata/palette-system-v1/README.md) detail inventory quotas, duplicate limits, palettes and patterns. The [IPFS bundle](docs/ARTWORK_PUBLICATION.md) is prepared; provider selection, publication and marketplace refresh testing remain open.

## Governance, custody and recovery

### Authority and configuration

| Role | Authority | Boundary |
| --- | --- | --- |
| **Governance multisig** | Approves configuration and supported recovery operations through the zero-delay governance controller. | Approved modules, destinations and replacement code require security review; governance remains a trust dependency. |
| **Guardian** | Pauses operations during an incident. | Cannot unpause or withdraw principal; unpause belongs to governance. |
| **Keeper** | Executes eligible maintenance within contract permissions and economic limits. | Cannot change governance policy or bypass execution guards. |

Production addresses are not selected. The [address inventory](docs/DEPLOYMENT_ADDRESSES.md) separates authority wallets, deployed contracts and network dependencies.

**Sealing fixes module implementations, local venue bindings and the ZZZ identity.**
Governance can enable/disable the fixed inputs and configure supported routes,
feeds, pools, royalty currencies and strategy parameters within existing controls.
It cannot retarget ZZZ burns or replace the contribution/normal-exit token. An
issuer migration uses custody exit and a fresh reviewed deployment. New algorithms
or unsupported venues also require separately reviewed code; they are not an
in-place upgrade. See the [change and recovery matrix](docs/CHANGE_AND_RECOVERY.md).

The [operator manual](docs/OPERATOR_MANUAL.md#stop-controls) includes a governed
mint-only pause and disable-only pool controls that work without healthy pool
dependencies. Re-enabling a pool still requires full validation; existing rights
retain their independent guards. See [scoped verification](reports/operator-controls/VERIFICATION.md).

### Recovery paths

| Situation | Supported path and limits | Reference |
| --- | --- | --- |
| **Pause and park LP** | Governance can close LP into Vault custody while globally paused, using an exact snapshot and raw output minimums. Parking omits source-price reads; resume requires fresh valuation and execution guards. Failed tokens or venues can still prevent movement. | [Custody parking](docs/CUSTODY_PARKING.md) |
| **Move LP between local pools** | Atomic moves require the same ordered actual currencies and the governed aggregate loss floor. Different-pair or ETH/WETH conversion uses explicit trusted external custody, followed by actual funded local completion or full original-asset recovery. Moving LP alone does not relocate NFT ownership or reward ledgers. | [Move/exit procedure](docs/GOVERNED_CUSTODY_HANDOFF.md), [migration safety](docs/MIGRATION_SAFETY.md) |
| **Review replacement NFT holders** | A confirmed owner/code inventory identifies contracts and delegated accounts requiring escrow release/claim review; rescan after freeze. Complete inventory is not migration approval. | [Holder preflight](docs/HOLDER_PREFLIGHT.md) |
| **Replace the whole deployment on the same chain** | The handoff candidate freezes and carries NFT ownership, both reward ledgers and exact classified backing to one replacement. Retirement/activation is atomic, with a restored funded abort path before retirement. Reviewed replacement code is an accepted governance trust boundary. | [Canonical handoff](docs/CANONICAL_HANDOFF.md) |
| **External migration or bridge** | Exit to the explicitly trusted source-chain custodian. The custodian performs external operations; this does not move NFT ownership or reward ledgers. Integrated cross-chain code is removed. | [Current release boundary](docs/SIMPLIFIED_RELEASE.md) |

**No integrated bridge is required or retained.** Local capacity reservation, guarded same-chain moves and explicit external custody remain. The [security audit plan](docs/SECURITY_AUDIT_PLAN.md) covers these cross-contract and external-dependency risks.

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
| **Local $1 test build** | [Rehearsal verification](reports/one-dollar-rehearsal/VERIFICATION.md) | Separate generated copy with mock services; not the production binary or qualification of the selected live pool. |
| **Published revision** | [GitHub Actions](https://github.com/ABEF/AAA/actions) | Check the exact commit and required jobs. Local results do not establish a green published workflow. |

<details>
<summary>Earlier verification and review history</summary>

- [NFT economic-rights verification](reports/nft-rights-audit/VERIFICATION.md): its historical 531 Solidity passes, two expected fork skips, 23 size gates and 65,536-call invariant run retain their original scope. The accompanying [internal review](reports/nft-rights-audit/REVIEW.md) records findings and risks.
- [Architecture evolution](reports/architecture-evolution/VERIFICATION.md) and [migration safety](reports/migration-safety/VERIFICATION.md): earlier source-specific evidence; neither verifies later handoff or maintenance changes.
- [Report index](reports/README.md): remaining historical receipts and their context.

</details>

### Production approval

Remaining work is tracked only in the [Project Todo](TODO.md). It includes:

- **Dependencies and configuration:** qualified market/input routes, tokens, feeds and VRF; authority addresses and reviewed operating configuration.
- **Integration and operations:** live frontend/backend flows, target-chain gas/strategy qualification and operating rehearsals.
- **Independent assurance:** external audit, remediation and final configuration/release review.

The [production inventory](config/production.example.json) records the exact deployment configuration and evidence. The [release approval record](docs/RELEASE_CHECKLIST.md) records the final go/no-go decision. Internal reviews and local passes do not replace either.

## Try the local browser test

The [local setup guide](docs/LOCAL_TEST_STACK.md) describes isolated, versioned
Anvil rehearsals with disposable wallets, confirmed API/indexer reads and a
browser panel. The [website rehearsal profile](docs/LOCAL_WEBSITE.md) uses `/app/`
on that local origin for explicit test transactions. Venue, prices and randomness
are substitutes. Existing local contracts and journals retain their original
profiles; they are not upgraded by these source changes. A fresh setup requires
a compatible build/profile and does not qualify current native production flows.
The public website remains simulated.

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

The [local $1 activation rehearsal](docs/ONE_DOLLAR_REHEARSAL.md) generates an isolated test build. It retains the source candidate's contribution policy (currently2% default) and **0.05 ETH mint price**; production activation remains **$100**. It does not enable live wallet transactions.

### Keep project records consistent

When implementation or evidence changes, follow the [Todo maintenance procedure](docs/TODO_WORKFLOW.md): update the [task ledger](docs/project-todo.json), reconcile the [feature/evidence reference](docs/IMPLEMENTATION_STATUS.md), then regenerate and check the task list:

```sh
python3 scripts/sync-project-todo.py
python3 scripts/sync-project-todo.py --check
```

Keep local work, GitHub publication, test evidence and deployment status explicit. The central Todo owns task status; feature references and release records have their separate purposes.

