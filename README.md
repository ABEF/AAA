# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

PoPL connects transferable NFTs to vault-managed liquidity. Activation attaches
an LP allocation and unlocks funded LP fees plus a separate share of NFT-sale
royalties. Holders cannot redeem principal during normal operation. Governance can end LP
activity and return actual ETH+ZZZ proportionally to current NFT holders, while
NFTs keep transfers, future royalties and previously earned rewards.

**Status: undeployed candidate; production NOT APPROVED.** The
[public website](https://popldemo.0xwave.com) simulates transactions. Existing
Anvil deployments retain their original code; public signing remains disabled.
The separate [poplint integration site](https://www.poplint.0xwave.com/) targets
current-contract reads and unsigned reviews. [Environment boundaries](docs/SITE_ENVIRONMENTS.md)
keep its build, server root and configuration distinct from the unchanged demo;
no configured deployment means unavailable integration data, never examples.

| Current design | Implementation and remaining boundary |
| --- | --- |
| Market and custody | Robinhood v4 native ETH/fixed ZZZ, selected hookless/static pool 0x5011...afe1b. Accounting4 appends terminal Exited5; production LP admission is native ETH/ZZZ only. [Pool](docs/POOL_SELECTION.md), [profile](docs/POSITION_V4.md). |
| Contributions and prices | Native ETH or one fixed ZZZ only. Source admission, the native pool, immutable buyback and collective holder return use that same reviewed ZZZ identity. Minimum $100 activation / $5 growth, two reviewed USD sources per asset and 3% disagreement tolerance. Actual added LP must meet the captured 2% default loss budget; gas separate. Reviewed Entry V1 also binds a caller maximum before funds move. [Price security](docs/PRICE_SECURITY.md), [reviewed policy](docs/EXECUTION_LOSS_POLICY.md#review-time-policy-binding). |
| Maintenance and conversion | Keeper authorization/pause are rechecked after rebalance, compound and buyback callbacks. Paid-revert cooldowns remain visible in matching keeper health/checkers. [Scoped review](reports/manipulation-hardening-20261027/VERIFICATION.md). Maintenance policy2 permits ordinary replacement only outside the actual range, or for an operator width change, after the hard configured interval (initial12hours). Matching service adds durable1-10minute jitter; compound V3 has a separately governed interval after LP replacement/compound and yields to due rebalance. Hourly harvest stays independent. [Cadence procedure](docs/OPERATOR_MANUAL.md#coordinate-compounding-with-rebalancing). Conversion defaults to 1%, maintenance to 3%; governance may immediately set each category up to 10%. Bounded placement/idle reinvestment and opt-in reviewed +/-25/50% keeper widths preserve accounting. At 1%, ZZZ conversion needs a cheaper qualified route. [Idle](docs/IDLE_AND_DUST.md), [range policy](docs/RANGE_POLICY_UPDATES.md), [operating controls](docs/POST_SEAL_POLICY.md). |
| Movement and recovery | Same-native-pair moves and parking before exit. Governance may permanently close all LP and return actual ETH+ZZZ by NFT shares through bounded direct payouts; NFTs keep transfers/future royalties/old rewards. No external custody address or bridge. [Holder exit](docs/HOLDER_COLLECTIVE_EXIT.md). |
| Release gates | Actual routes/independent feeds/VRF, authorities, native wallet/service acceptance and OpenSea integration, gas/strategy economics, operating rehearsals and independent audit/remediation remain open. [Sole Todo](TODO.md), [current evidence](docs/IMPLEMENTATION_STATUS.md#current-evidence-and-limits). |

The [earlier whole-project source review](reports/whole-project-audit-20261029/REVIEW.md)
was built from contract/service/website understanding and a
[twice-challenged prompt](reports/whole-project-audit-20261029/PROMPT_REVIEW.md).
It fixes ownership-inventory outage isolation, malformed stored history and
metadata restart starvation, and corrects keeper regression/fork CI selection.
Five targeted current canonical composition methods pass; detailed individual
callable coverage and real qualification remain separate, explicit limits.

Current [confirmation policy](docs/LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer)
uses a15-minute sampled window, user-approved four-minute source checks and an
unchanged strict300-second maximum recorded gap after the hard cooldown.
The roughly60-second scheduling margin is not grace or guaranteed inclusion.
Observing during cooldown is a proposed Todo improvement, not implemented.
The [additional-loss guard](docs/EXECUTION_QUALITY.md) still separates actual
directional fees from additional deterioration; stronger operation/caller floors
remain. [Keeper safeguards](docs/KEEPER_SAFEGUARDS.md) distinguishes on-chain rules,
service controls and accepted market/governance risks.

That earlier review changed no Solidity. Current local confirmation2/emergency1
source changes below do not alter installed services, signer policy, sites or
existing Anvil deployments. The
[verification record](reports/whole-project-audit-20261029/VERIFICATION.md),
[feature reference](docs/IMPLEMENTATION_STATUS.md) and [documentation map](docs/README.md)
separate fresh evidence, exact reuse, legacy profiles and open release work.
Earlier [reports](reports/README.md) retain their original bytes/source scope;
neither inventories nor internal checks constitute independent approval.

Fresh [confirmation2](docs/LP_EXECUTION_POLICY.md#independent-reference-in-confirmation2)
requires our LP and the independent reference to exit on the same side. A separate
[manual emergency rebalance](docs/EMERGENCY_REBALANCE.md) is paused and governance-only,
with explicitly optional economic guards. It preserves custody/accounting but
expands governance trust: disabled financial floors can permit near-total loss.
[Review/evidence](reports/independent-rebalance-20261029/VERIFICATION.md) is local,
not production approval or a completed whole-project audit.

The [whole-project source pass](reports/whole-project-execution-20261029/REVIEW.md) and
[operational code follow-up](reports/operational-reliability-20261029/REVIEW.md) cover keeper
recovery, confirmed history, inventory/readiness consistency and verification
tooling. Current [keeper coordination](docs/KEEPER_COORDINATION.md) adds service-only
compound waits, proved harvest-clock coalescing and read-only LP operation reports,
and corrects the reservation observer's unsupported getter. [Current evidence](reports/keeper-coordination-20261029/VERIFICATION.md)
separates affected checks from unchanged Solidity/build reuse. Source publication
does not qualify real operation, deploy services/sites or enable public signing.

## Project navigation

| Purpose | Start here |
| --- | --- |
| Progress and remaining work | **[Project Todo](TODO.md)** - the single task list, with expandable acceptance criteria |
| Questions for the token/pool creator | [Creator tasks / ZZZ team](TODO.md#creator-tasks--zzz-team) - independent ZZZ pricing, token controls and market continuity |
| Current selected-pool fork | [Current native harness and evidence](reports/current-pool-fork-20261026/VERIFICATION.md) - exact real-pool snapshot, explicit substitutes and remaining qualification |
| What is built and tested | [Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) - capabilities, boundaries and verification |
| Keeper safeguards | [Implemented manipulation protections](docs/KEEPER_SAFEGUARDS.md) - architecture, on-chain guards, limits, service controls and remaining exposure |
| LP execution | [Manual range and reviewed-venue execution](docs/LP_EXECUTION_POLICY.md) - delivered upkeep2/compound3 and LP routing1; real depth/gas/operations qualification remains |
| Manage the protocol | **[Operator manual](docs/OPERATOR_MANUAL.md)** - exact controls, [manual rebalance](docs/OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time), emergency stops and restart procedures |
| Documentation map | [Current guides and historical references](docs/README.md) |
| System design | [Architecture](docs/ARCHITECTURE.md) for interactions; [evolution and trust boundaries](docs/ARCHITECTURE_EVOLUTION.md) for migration limits; [Component map](docs/COMPONENT_STATUS.md) for each module's responsibilities |
| Callable reads and writes | [Function reference](docs/CONTRACT_FUNCTIONS.md) - purpose, permissions, inputs, outputs and tuple fields, linked from the operator manual |
| Production inventory | [Preflight scope](docs/PRODUCTION_PREFLIGHT.md) - explicit schema6/accounting4 observer and validator; actual bindings/services remain unqualified, schema5 inspection is historical |
| Contribution and valuation security | [Two-source prices and actual LP](docs/PRICE_SECURITY.md) - fixed transaction basis, conservative loss checks and remaining provider trust |
| Security and release | [Latest systematic internal review](reports/system-adversarial-20261026/REVIEW.md), with scoped fixes and remaining qualification; [Security audit plan](docs/SECURITY_AUDIT_PLAN.md) for review criteria; [Release approval record](docs/RELEASE_CHECKLIST.md) for the final go/no-go decision |

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
    Manager --> Planner[Immutable LP Balancer: reviewed venues]
    Planner --> Quotes[Reverted actual-core quotes]
    Manager --> Pool[Uniswap v4: shared LP]
```

| Component group | Responsibility and relationship | Source / design |
| --- | --- | --- |
| **NFT identity and artwork** | Records the current owner and immutable revealed traits. Metadata reads the NFT's current attached LP value to select its evolution. | [NFT](src/ZZZNFT.sol), [metadata](src/ZZZNFTMetadata.sol), [trait/reveal design](docs/NFT_METADATA.md) |
| **Activation and admission** | Reviewed Entry accepts native ETH/fixed ZZZ, binds owner and captured execution policy. Registry admits only native ETH/fixedZZZ LP and one contribution pool at a time; reward conversion venues remain separate. Terminal exit blocks contributions. | [Entry](src/ZZZActivationEntry.sol), [Registry](src/ZZZPoolRegistry.sol) |
| **LP balancing** | Manager-created LP routing1 compares up to four reviewed ETH/ZZZ venues with bounded actual-core sizing, executes at most one swap and leaves LP custody in Vault. Contributions trade/deploy only their own budget. | [LP Balancer](src/ZZZLPBalancer.sol), [execution policy](docs/LP_EXECUTION_POLICY.md), [scoped evidence](reports/atomic-routing-20261028/VERIFICATION.md) |
| **Custody and per-NFT shares** | Vault owns the physical LP and records each NFT's nonredeemable shares. Its 8-field local Position replaces unused remote/home copies. LiquidityManager executes typed venue operations; the budget helper checks contribution and maintenance loss limits. | [Vault](src/ZZZVault.sol), [local profile](docs/POSITION_V4.md), [LiquidityManager](src/ZZZLiquidityManager.sol), [budget helper](src/ZZZMigrationBudget.sol) |
| **LP revenue accounting** | Actual local venue collections feed FeeController. It allocates receipts to holder/collective balances and separate compound/buyback reserves. Membership gives each activated NFT one collective share. | [FeeController](src/ZZZFeeController.sol), [Rewards](src/ZZZRewards.sol), [Membership](src/ZZZMembership.sol) |
| **Royalties and claims** | RoyaltyRewards preserves per-NFT entitlements, isolates optional currency outages and credits batch-converted ETH to the same NFTs. Current owners claim through either ledger or ClaimRouter. | [RoyaltyRewards](src/ZZZRoyaltyRewards.sol), [converter](src/ZZZRoyaltyConverter.sol), [ClaimRouter](src/ZZZClaimRouter.sol), [operator flow](docs/ROYALTY_SETTLEMENT.md) |
| **Valuation and maintenance** | Oracle requires two reviewed USD sources per asset. Its fixed pricing companion freezes contribution prices/limits and verifies marginal LP; Strategy defines guarded ranges and eligibility. Keeper maintenance stays within on-chain limits. | [Oracle](src/ZZZOracle.sol), [contribution pricing](src/ZZZContributionPricing.sol), [price security](docs/PRICE_SECURITY.md), [optional Pyth source](src/ZZZPythPriceFeed.sol), [Strategy](src/ZZZStrategy.sol), [Compounder](src/ZZZCompounder.sol), [Buyback](src/ZZZBuyback.sol) |
| **Governance and permissions** | The selected governance wallet calls modules directly; AccessController checks that authority, guardian pause and keeper permissions. Governance replacement requires proposal and acceptance. No timelock queue, executor or OpenZeppelin role grants remain. Sealing fixes module bindings. | [AccessController](src/ZZZAccessController.sol), [authority and change boundaries](docs/CHANGE_AND_RECOVERY.md) |
| **LP movement and holder return** | Migration keeps guarded same-pair moves/parking before exit. Collective exit closes all LP, includes pending compound, allocates actual ETH+ZZZ and pays current NFT owners in isolated batches. No external custodian. Whole-collection replacement is separate and blocked after exit. | [Migration](src/ZZZMigration.sol), [holder procedure](docs/HOLDER_COLLECTIVE_EXIT.md), [canonical handoff](docs/CANONICAL_HANDOFF.md) |

**Exit authority:** governance can irreversibly return principal to current NFT owners by their shares. It cannot choose a treasury/custody recipient. Failed automatic payouts stay backed for retry or a recipient chosen by the actual owner. Royalties and earned rewards are not swept.

Many NFTs share **one physical LP per pool/strategy**, with independent share accounts. Maintenance operates on the shared position. The registry permits **one deposits-enabled contribution pool at a time**, selected for the existing hookless ETH/ZZZ pool after qualification. Governance can disable it and enable a reviewed replacement without deleting historical pools; [switch procedure](docs/OPERATOR_MANUAL.md#one-contribution-pool-at-a-time). The Vault allows four permanently admitted/historical custody buckets, including reservations and imports. An existing bucket's migration or return reuses its slot. See the [detailed interactions](docs/ARCHITECTURE.md) and [complete module/helper map](docs/COMPONENT_STATUS.md).

<a id="backend-components"></a>

### 2. Backend and operations

Read services serve confirmed chain state. Transaction preparation returns an unsigned request for the user's wallet. The keeper uses a dedicated service signer controlled by the same project operator for authorized maintenance; it does not sign user activations.

| Service | Responsibility and relationship | Code / operating reference |
| --- | --- | --- |
| **Event indexer** | Reads confirmed contract logs into SQLite, detects bounded reorgs and supplies replay history for ownership and claims. | [Indexer](indexer/monitor.py), [event schema](indexer/event_schema.json), [history requirements](docs/FRONTEND_HISTORY.md) |
| **HTTP admission and isolation** | Bounded isolated workers, per-client concurrency/read/preparation budgets, finite connections and deadlines, explicit overload and cleanup quarantine. Guarded proxy identity/origin; no signer. | [Worker pool](frontend_api/worker.py), [client admission](frontend_api/admission.py), [HTTP bounds](frontend_api/http_runtime.py), [proxy and recovery](docs/API_INGRESS.md) |
| **Read API** | Verifies deployment/lifecycle at a confirmed block, then reads current owners, LP values and funded balances. Optional current-ledger reporting separates ETH/source balances and deferred royalty eligibility; complete pinned predecessor replay carries lifetime claims and conversion credits across same-chain handoffs. | [Service](frontend_api/service.py), [lifecycle](frontend_api/lifecycle.py), [lineage replay](frontend_api/lineage.py), [API contract](docs/FRONTEND_API.md), [royalty reporting](docs/ROYALTY_REPORTING.md) |
| **Earnings history** | Replays actual processed LP/royalty earnings per collection and NFT, preserving weights, fractions and complete same-chain lineage. Optional reviewed prices value original earned currencies at today's confirmed snapshot. Claims, conversions and current balances stay separate. | [Replay/API](frontend_api/earnings.py), [configuration and operations](docs/EARNINGS_HISTORY.md), [evidence](reports/earnings-history/VERIFICATION.md) |
| **Claim and local-mint preparation** | Builds up to 32 owner-authenticated LP/royalty claim operations with canonical simulation and separate gas estimates. Opt-in direct-mint drafts exist; the production qualification gate and website mint capability reject unsupported OpenSea primary minting. A draft alone does not approve public minting. Short-lived unsigned reviews only; no signer. | [Preparer](frontend_api/transactions.py), [configuration and wallet rules](docs/FRONTEND_TRANSACTIONS.md), [mint qualification](docs/MINT_INTEGRATION_QUALIFICATION.md) |
| **Activation preparation** | Checks asset/route/feed bindings, simulates the complete Entry call, measures new LP, and returns exact unsigned calldata and separate gas. Missing approval produces an approval step before re-quoting. | [Preparation](frontend_api/activation.py), [opt-in endpoint](frontend_api/activation_server.py), [integration sequence](docs/ACTIVATION_PREPARATION.md) |
| **Keeper** | Discovers shared buckets, checks eligibility, simulates and submits authorized upkeep. Persists intents, receipts and budgets for recovery; optional metadata watching uses the same bounded transaction path. | [Monitor](keeper/monitor.py), [execution](keeper/ops.py), [recovery runbook](docs/KEEPER_RECOVERY.md) |
| **Release preflight** | Historical accounting3 inventory/observer remains source-scoped. Fresh accounting4/custody3/V5 inventory qualification is required; old ready results do not approve this source. No deployment authority. | [Preflight](docs/PRODUCTION_PREFLIGHT.md), [profile](docs/POSITION_V4.md) |

These services require qualified RPC/archive providers, feeds, configuration and operating procedures. Hosting and live integration remain open. The API does not hold user keys; the contracts still enforce transaction permissions and accounting.

<a id="frontend-components"></a>

### 3. Frontend

The website is maintained in [AAA-website](https://github.com/ABEF/AAA-website). Its current components are:

| Component | Current responsibility | Website source |
| --- | --- | --- |
| **Pages and interactions** | Navigation, collection/portfolio cards, dialogs, contribution and claim interfaces. | [app.js](https://github.com/ABEF/AAA-website/blob/main/app.js) |
| **Demo data and accounting** | Example NFTs, balances, contribution events and simulated claims. This model must be replaced by confirmed API data for live use. | [domain.js](https://github.com/ABEF/AAA-website/blob/main/domain.js) |
| **Wallet connection** | Connects a browser wallet and handles account/chain changes. The separate reviewed Anvil-only profile handles signing/receipt recovery. Public signing remains disabled; current-profile deployment and actual wallet-provider qualification remain open. | [wallet.js](https://github.com/ABEF/AAA-website/blob/main/wallet.js) |
| **Artwork catalogue** | Resolves palette, pattern, rarity and evolution assets for display. On-chain metadata remains authoritative for a real NFT. | [artworks.js](https://github.com/ABEF/AAA-website/blob/main/artworks.js), [palette-system.js](https://github.com/ABEF/AAA-website/blob/main/palette-system.js) |

The target live flow is **website -> read/preparation API -> user wallet confirmation -> contracts -> confirmed receipt/indexer/API refresh**. The public/default website still simulates minting, LP contributions and claims; the separate [local contract mode](docs/LOCAL_WEBSITE.md) uses disposable Anvil contracts; see the [frontend integration tasks](TODO.md#frontend).

## NFT lifecycle

| Step | Rule |
| --- | --- |
| **Mint** | Buyer mint price is **0.05 ETH**, gas separate. Current direct mint pays it all to the immutable recipient; the required OpenSea integration pays the recipient net of its actual platform fee. Minting adds supply, not liquidity or reward eligibility. |
| **Activate** | After reveal, the conservative original input value must reach **$100**. Conversion and new LP deployment share the captured execution limit (2% by default, governance maximum 10%); the upper input / lower LP price bounds tighten its floor. Network gas is separate. |
| **Add liquidity** | Contributions from **$5 in conservative original input value** grow the same NFT under the captured contribution limit; gas is separate. Higher pool minima apply. Existing holders' assets cannot subsidize the new LP floor; a top-up adds no collective membership. |
| **Hold or transfer** | The current owner can claim its funded balances. Transfers carry the LP allocation, remaining unclaimed balances and future fee rights. A seller can claim before a transfer, so an earlier listing balance is not guaranteed to the buyer. |

**LP principal cannot be redeemed by holders during operation.** Governance may permanently end LP activity and return actual proportional ETH+ZZZ to them; existing rewards and future royalty rights survive. A right to future funded fees has no expiry, but does not guarantee future revenue or capital value.

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

The selected hookless native ETH/ZZZ pool has a static **1.002% LP fee**. PoPL allocates only actual fees earned by its own position; Uniswap's separate protocol fee is not PoPL revenue. The observed combined swap fee is approximately 1.101%. Current native accounting keeps ETH directly; already-native holder fees need no conversion. ZZZ reward conversion defaults to a **1% loss cap** (governed maximum 10%), gas separate, and needs a cheaper qualified route. See [pool selection](docs/POOL_SELECTION.md).

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
| **Governance wallet** | The single project operator controls this wallet and calls configuration/recovery functions directly, with no protocol waiting period. | Reviewed destinations and replacement code remain trusted. A new governance wallet must explicitly accept a proposal; keeper/guardian roles rotate separately. |
| **Guardian** | Pauses operations during an incident. | Cannot unpause or withdraw principal; unpause belongs to governance. |
| **Keeper** | Executes eligible maintenance within contract permissions and economic limits. | Cannot change governance policy or bypass execution guards. |

Production addresses are not selected. A Safe or another selected governance
wallet applies its own signature and nonce policy; PoPL adds no generic executor,
predecessor queue or role-grant API. The immutable mint recipient and bootstrap
setup role remain separate. The [address inventory](docs/DEPLOYMENT_ADDRESSES.md)
separates authority wallets, deployed contracts and network dependencies.

**Sealing fixes module implementations, local venue bindings and the ZZZ identity.**
Governance can enable/disable the fixed inputs and configure supported routes,
feeds, pools, royalty currencies and strategy parameters within existing controls.
It cannot retarget ZZZ burns or replace the contribution/normal-exit token. An
issuer migration has no external custody executor; collective exit returns actual ETH+ZZZ to holders. New algorithms
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
| **Move LP between local pools** | Atomic moves retain native ETH/fixed ZZZ, unchanged NFT shares and the captured maintenance floor. No different-pair or ETH/WETH custody conversion exists. | [Pool movement](docs/GOVERNED_CUSTODY_HANDOFF.md) |
| **Review replacement NFT holders** | A confirmed owner/code inventory identifies contracts and delegated accounts requiring escrow release/claim review; rescan after freeze. Complete inventory is not migration approval. | [Holder preflight](docs/HOLDER_PREFLIGHT.md) |
| **Replace the whole deployment on the same chain** | Canonical V5 carries ownership, reward ledgers and exact backing with atomic retirement/activation and funded abort. Available before LP exit only; terminal payout ledger is not imported. | [Canonical handoff](docs/CANONICAL_HANDOFF.md) |
| **End LP activity and return principal** | Governance-triggered permanent shutdown pays actual proportional ETH+ZZZ to current holders. Old rewards remain claimable; NFTs keep future royalties/transfers. No external custody/bridge executor. | [Holder exit](docs/HOLDER_COLLECTIVE_EXIT.md) |

**No integrated bridge is required or retained.** Local capacity reservation, guarded same-pair moves and collective holder return remain. The [security audit plan](docs/SECURITY_AUDIT_PLAN.md) covers these cross-contract and external-dependency risks.

## Keeper and operating services

The keeper **defaults to dry run**. Full keeper/state-lock operation requires **Linux/Unix and Python 3.11+**.

- **Polling:** fresh confirmation2 uses60-240second outer polling and240-second eligible checks; the historical default is ten minutes. These are not guaranteed execution times.
- **Rebalancing:** actual physical range exit or an approved range change must make the position eligible after cooldown. Ordinary exits also require sampled confirmation, fresh prices and execution guards. See [operating policy](docs/LP_EXECUTION_POLICY.md).
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
| **Current architecture pruning** | [Review](reports/architecture-pruning-20261025/REVIEW.md), [profile and codec](docs/POSITION_V3.md) | Accounting V3, direct governance V2 and same-chain canonical V4; source-scoped checks only. |
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

The [production inventory](config/production.holder-exit.example.json) records the exact deployment configuration and evidence. The [release approval record](docs/RELEASE_CHECKLIST.md) records the final go/no-go decision. Internal reviews and local passes do not replace either.

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
