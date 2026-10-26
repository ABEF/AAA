# Component implementation map

This describes the **undeployed current candidate**, not installed contracts or
services. Accounting V3 uses an 8-field local Position, governance V2 uses direct
wallet calls and canonical V4 carries the LP-only same-chain ledger. Historical
profiles and journals remain separately decoded. See [profile boundaries](POSITION_V3.md),
[pruning review](../reports/architecture-pruning-20261025/REVIEW.md) and the
[feature/evidence reference](IMPLEMENTATION_STATUS.md). Production NOT APPROVED.

Use the linked source for component boundaries, the [feature/evidence reference](IMPLEMENTATION_STATUS.md)
for source-scoped verification and the [sole Todo](../TODO.md) for remaining work.
This map does not repeat dated test totals or bytecode margins as current approval.

## On-chain identity, entry and custody

| Component | Current responsibility | Remaining qualification |
| --- | --- | --- |
| [AccessController](../src/ZZZAccessController.sol) | Direct selected governance wallet; separate keeper/guardian permissions; 16 fixed module bindings; 2-step governance handover. No timelock, generic executor or role-grant API. | Actual authority wallets/Safe configuration and signing/recovery rehearsal. Governance and external recipients remain trusted. |
| [Vault](../src/ZZZVault.sol) | Direct 0.05 ETH dormant mint; source-bound $100 activation / $5 growth; nonredeemable per-NFT shares; one physical LP per bucket; local custody and exact classified backing. | Actual venue/asset behavior, maximal target-chain gas and independent accounting review. |
| [ActivationAssets](../src/ZZZActivationAssets.sol) | One pre-seal fixed ZZZ plus native ETH as user inputs; reviewed source policies and dependency-independent disabling. | Actual token/proxy/code/decimal/feed policy and complete deployment inventory. Stablecoins are royalty options, not contribution inputs. |
| [PoolRegistry](../src/ZZZPoolRegistry.sol) | One contribution pool at a time; pinned hookless native ETH/ZZZ admission; generic ERC20 pools must contain the same fixed ZZZ. Supports reviewed future fee tiers or WETH/ZZZ; no arbitrary unrelated pair. | Actual pool/runtime/price/deposit/operation qualification. Pool admission does not qualify conversion routes or another user input. |
| [ActivationEntry](../src/ZZZActivationEntry.sol) | Authenticates owner and exact Vault call; captures source USD and caller loss maximum; direct/native or typed single-hop v3/v4 paths; exact approvals and callback-safe context. | Actual route funding/fees, whole-operation trace and browser-wallet/target-chain rehearsal. |
| [LiquidityManager](../src/ZZZLiquidityManager.sol) | Typed v4 mint/increase/collect/close/swap, exact native settlement and prefund isolation. Real LP key/ticks/liquidity remain authoritative. | Current selected-pool lifecycle fork, adverse dependencies, strategy economics and maximal real gas. Hooks/dynamic native fees are outside scope. |
| [ContributionPricing](../src/ZZZContributionPricing.sol) | Captures two-source bounds and caller policy before funds move; measures genuinely added LP and validates final fingerprints/spot. | Independent actual feeds, routes and real-market execution. |
| [MigrationBudget](../src/ZZZMigrationBudget.sol) | Captured contribution/maintenance budgets, physical LP evidence, loss floors and custody completion checks. | Maximal installed-venue composition and independent economic review. |

Position V3 stores poolId,lpTokenId,idle0,idle1,depositUSD,centerX96,lastRebalance,
status. `None=0`, `Active=1`, `Outbound=2`, `Dormant=3`, `Parked=4` are local states. Removed remote/
home copies are not silently synthesized. Original NFT/bucket identifiers and
history survive compatible same-chain handoff; old profiles retain old layouts.
The Vault permanently admits at most 4 historical/reserved buckets. Aliases and
returns reuse a slot; maintenance is per shared position, not per 1,000 NFTs.

## Funded income, claims and maintenance

| Component | Current responsibility | Remaining qualification |
| --- | --- | --- |
| [FeeController](../src/ZZZFeeController.sol) | Actual local LP receipts only; fixed 80/10/5/5 allocation, separate compound/buyback reserves and incumbent raw-unit dust. Creator inboxes and remote intake are removed. | Currency rounding economics, actual fee collection and independent accounting review. |
| [Rewards](../src/ZZZRewards.sol) | Individual bucket-share indices, equal activated collective indices, fractions and current-owner claims; native ETH credits without reallocation. | Actual token/native recipients, worst-case asset costs and complete indexed history. |
| [Membership](../src/ZZZMembership.sol) | One equal share per activated NFT; incumbent checkpoints/dust before entry; no top-up/rarity/age weighting. Canonical export is eligibility only, with no inherited asset custody. | Maximal 4-bucket entry gas and persistence across custody/whole-collection handoff. |
| [LPRewardConverter](../src/ZZZLPRewardConverter.sol) | Converts only earned holder/collective source balances into the same NFTs' ETH credits; retains backing/fractions. | Cheaper qualified ZZZ route at the default 1% limit, conversion latency, gas and operation. |
| [RoyaltyRewards](../src/ZZZRoyaltyRewards.sol) | Separate funded 1/2/3 royalty ledger; optional-currency outage cohorts; paused currency custody/full original-asset return. | Actual marketplace receipts, token/recipient behavior, conversion/late-receipt and custody rehearsal. |
| [RoyaltyConverter](../src/ZZZRoyaltyConverter.sol) | Guarded batch conversion into ETH without changing NFT entitlements; explicit wrapper dependency only for operations using one. | Reviewed conversion routes/feeds/wrapper where used and keeper execution/recovery. |
| [ClaimRouter](../src/ZZZClaimRouter.sol) | Up to 32 mixed NFT/asset/ledger claims; duplicates/current-owner checks, direct payout and atomic rollback. | Target-chain maximal gas, frontend chunking, simulated requests and actual recipient acceptance. |
| [Oracle](../src/ZZZOracle.sol) | Two-source reviewed USD policies, freshness/fingerprint/bounds and 3% disagreement rejection; governed reviewed sequencer replacement. | Actual independent sources, proxy/common-mode/uptime policies and real provider support. |
| [Optional Pyth reader](../src/ZZZPythPriceFeed.sol) | Immutable bounded Core observation reader; original time/confidence/precision checks; no funds or updater. | Actual Core/source review, updater service and independent source selection. |
| [Strategy](../src/ZZZStrategy.sol),[Compounder](../src/ZZZCompounder.sol) | Eligibility/range/cooldown and attributed LP/idle reinvestment. Optional reviewed keeper selection of +/-25% / +/-50% ZZZ-price-in-ETH widths. | Volatility/MEV/backtesting, thresholds, real gas and recovery rehearsals. |
| [Buyback](../src/ZZZBuyback.sol) | Bounded direct acquisition/burn with supply/balance checks; immutable ZZZ matches activation and normal exit; governed operating ceiling. | Actual routes/feed/burn behavior and operator funding/coordination. |

Contribution/conversion/maintenance defaults are 2%/1%/3%, each governed up to 10%,
gas separate. Reviewed caller limits and stronger venue minima remain. Already
approved normal custody floors do not weaken when governance changes policy.
Native pool ETH remains ETH throughout principal, reserves and indices. Source
currency claims remain source currency until actually converted; no ETH-only
presentation may relabel them.

## NFT identity, metadata and replacement

| Component | Current responsibility | Remaining qualification |
| --- | --- | --- |
| [NFT](../src/ZZZNFT.sol) | ERC-721/2981/4906; 1,000 cap; ordered quota/inventory draws; immutable traits and royalty/metadata/claim helpers. | Supported proof-verifying VRF, funded subscription and compatible OpenSea primary mint. |
| [NFTMetadata](../src/ZZZNFTMetadata.sol) | Current marked LP/idle/compound share NAV; four evolutions; downgrades and explicit unavailable valuation; 2,784 supported artwork states. | Permanent artwork root, real prices, cache refresh and watcher operation. |
| [RoyaltyFactory](../src/ZZZRoyaltyFactory.sol),[ActivationAssetsFactory](../src/ZZZActivationAssetsFactory.sol) | Fixed automatic helper creation and owner/parent bindings. | Exact release deployment/bindings and bytecode inventory. |
| [Migration](../src/ZZZMigration.sol),[CustodyValidation](../src/ZZZCustodyValidation.sol) | Same-actual-pair moveFunds; exact approved paused all-ZZZ or raw custody exit; funded local completion/full recovery; read-only validation companion. | External recipient custody is trusted. Actual routes/LP/return/recovery and operational acceptance remain open. No integrated bridge or remote-proof completion. |
| [CanonicalHandoff](../src/ZZZCanonicalHandoff.sol) | Six-domain capture/settlement, bounded export/import, classified funding, full abort and atomic source retirement/successor activation. | Current schema/implementation compatibility, complete financial/callback/interruption/gas review, contract-owner cutover and independent audit. |
| [NFTCanonical](../src/ZZZNFTCanonical.sol),[VaultCanonical](../src/ZZZVaultCanonical.sol),[FeesCanonical](../src/ZZZFeesCanonical.sol) | Sealed typed codecs for traits, shares, fractions, custody and backing. V4 group rows are 12 words / 384 bytes; legacy/trailing layouts rejected. | Exact source/successor manifest and operated relay/funding/recovery rehearsal. |

Rarity affects only separate royalties. Dormant traits still report 1/2/3 by
revealed rarity, while economic eligibility remains zero until activation.
Palette/pattern affect no rewards. Claims and transfers carry existing rights;
metadata cannot block them. Integrated future-chain transport, post-halt recovery
and old-schema import are outside this release. Issuer migration uses explicit
external custody and a fresh reviewed deployment of the new fixed token.

## Services and current evidence boundaries

The keeper discovers shared buckets, simulates guarded maintenance and persists
intents/receipts/budgets for recovery. Historical state remains versioned; no
pending journal is deleted or upgraded. Full locking/operations require Unix/Linux.
The indexer checks provenance/reorgs and the API verifies confirmed deployment,
local Position/lifecycle and complete pinned same-chain history. Missing history
or pricing is unavailable, not zero. Read/preparation APIs hold no user keys.

Current fee/royalty earnings, conversion and lifetime-claim replay are implemented
with separate entitlement/price semantics. Website read/unsigned source can inspect
reviewed data, but public DEPLOYMENT remains null and signing Anvil-only. Actual
current-profile providers, service hosting, wallet/OpenSea acceptance, keeper
operation and independent audit remain open. Existing local deployments are not
changed by source edits. The artwork bundle is prepared, not published/pinned.

Use the [sole Todo](../TODO.md) for tasks, the [feature/evidence reference](IMPLEMENTATION_STATUS.md)
for verification and the [operator manual](OPERATOR_MANUAL.md) for procedures.
Earlier [reports](../reports/README.md), including native V2, bridge/Pons and old
inbox scopes, keep their original source identities. They do not verify removed
or subsequently changed paths. The exact callable surface is generated in the
[function reference](CONTRACT_FUNCTIONS.md); maintain it for ABI/permission changes.
