# Function and operation coverage

Reviewed3November2026. [Review](REVIEW.md), [prompt](AUDIT_PROMPT.md), [evidence](VERIFICATION.md).

**795 implemented function/modifier bodies and342 declarations in52 project files** are enumerated in [functions.json](functions.json). Each record has source/line, AST identity, input/output names/types, modifiers, whole-definition hash and review group. These are not795 independently tested behaviors. Constructors/receivers/modifiers are included; automatic getters/inherited ABI duplicates are instead covered by the existing [callable reference](../../docs/CONTRACT_FUNCTIONS.md).

All implemented project bodies were read in their component/call-path context. The depth is manual code review plus targeted new execution and source-matched previous evidence, not exhaustive path exploration or formal verification. Pure declarations have no implementation to execute. Installed dependency review targeted core/periphery settlement/math and OpenZeppelin behavior actually used;1023 AST bodies in83 inputs is a compiler-analysis inventory, not1023 manually audited dependency functions.

## Review groups and expected behavior

The action/output/rollback table in [Review](REVIEW.md#lp-account-and-operation-review) crosses these groups. The Operator manual supplies exact callable inputs, authority, prerequisites, effects and reverse controls. Hidden/private helpers are mapped below and in the inventory; external output names alone do not establish economic meaning.

<a id="governance-policy"></a>
### Governance and admission

Caller/bootstrap/seal lifecycle, fixed identities, append-only reviewed policies, disable/re-enable asymmetry, scoped revision and future-only settings.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZAccessController.sol](../../src/ZZZAccessController.sol) |18|6|
| [ZZZActivationAssets.sol](../../src/ZZZActivationAssets.sol) |10|1|
| [ZZZActivationAssetsFactory.sol](../../src/ZZZActivationAssetsFactory.sol) |2|0|
| [ZZZPoolRegistry.sol](../../src/ZZZPoolRegistry.sol) |13|4|
| [ZZZProtocolPolicy.sol](../../src/ZZZProtocolPolicy.sol) |31|4|

<a id="entry-shares"></a>
### Contributions and shares

Original source/operation floors, entrant-only balancing, incumbent fee/compound checkpoints, actual marginal main LP, aggregate-NAV shares, captured price/policy and rollback.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZActivationEntry.sol](../../src/ZZZActivationEntry.sol) |20|2|
| [ZZZContributionPricing.sol](../../src/ZZZContributionPricing.sol) |31|9|
| [ZZZMigrationBudget.sol](../../src/ZZZMigrationBudget.sol) |51|17|
| [ZZZVault.sol](../../src/ZZZVault.sol) |59|2|

<a id="physical-execution"></a>
### Physical execution

Typed parent/callback/recipient/LP IDs, real core deltas and stored ticks, bounded actual quotes/search, exact debt/spend/refunds, one swap, main activity and residual placement.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZLPBalanceMath.sol](../../src/ZZZLPBalanceMath.sol) |9|0|
| [ZZZLPBalancer.sol](../../src/ZZZLPBalancer.sol) |26|2|
| [ZZZLPPositionExecutor.sol](../../src/ZZZLPPositionExecutor.sol) |30|7|
| [ZZZLiquidityManager.sol](../../src/ZZZLiquidityManager.sol) |41|9|
| [ZZZV4RouteExecutor.sol](../../src/ZZZV4RouteExecutor.sol) |14|0|
| [ZZZV3VenueValidation.sol](../../src/libraries/ZZZV3VenueValidation.sol) |1|0|

<a id="portfolio-timing"></a>
### Portfolio and timing

Desired/applied revisions, threshold/reference direction, range math, sampled evidence/cooldown/manual exceptions and actual service-versus-contract boundary.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZPortfolioPolicy.sol](../../src/ZZZPortfolioPolicy.sol) |22|2|
| [ZZZRebalanceConfirmation.sol](../../src/ZZZRebalanceConfirmation.sol) |18|13|
| [ZZZStrategy.sol](../../src/ZZZStrategy.sol) |33|2|
| [ZZZPriceMath.sol](../../src/libraries/ZZZPriceMath.sol) |1|0|

<a id="funded-revenue"></a>
### Funded revenue

Exact actual receipts/split/dust/fractions, old versus current ownership, per-NFT liabilities, reserve separation, compound/claim/conversion/burn and callback completion.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZBuyback.sol](../../src/ZZZBuyback.sol) |5|0|
| [ZZZClaimRouter.sol](../../src/ZZZClaimRouter.sol) |2|1|
| [ZZZCompounder.sol](../../src/ZZZCompounder.sol) |2|0|
| [ZZZFeeController.sol](../../src/ZZZFeeController.sol) |22|3|
| [ZZZLPRewardConverter.sol](../../src/ZZZLPRewardConverter.sol) |1|0|
| [ZZZMembership.sol](../../src/ZZZMembership.sol) |16|2|
| [ZZZRewards.sol](../../src/ZZZRewards.sol) |26|2|
| [ZZZRoyaltyConverter.sol](../../src/ZZZRoyaltyConverter.sol) |1|0|
| [ZZZRewardConverter.sol](../../src/base/ZZZRewardConverter.sol) |18|4|
| [ExactAsset.sol](../../src/libraries/ExactAsset.sol) |3|0|
| [ExactToken.sol](../../src/libraries/ExactToken.sol) |2|0|

<a id="prices-royalties"></a>
### Prices and royalties

Source bounds/rounds/freshness/codehash/decimals, declared independence, sequencer gates, optional currency cohort deferral/recovery and actual backing.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZOracle.sol](../../src/ZZZOracle.sol) |22|0|
| [ZZZPythPriceFeed.sol](../../src/ZZZPythPriceFeed.sol) |2|0|
| [ZZZRoyaltyFactory.sol](../../src/ZZZRoyaltyFactory.sol) |2|0|
| [ZZZRoyaltyRewards.sol](../../src/ZZZRoyaltyRewards.sol) |32|10|

<a id="custody-lifecycle"></a>
### Custody and lifecycle

Raw close/park/resume/move manifests, both-leg fingerprints/nonces, optional emergency budgets, terminal direct payouts and parked same-chain canonical rows/backing/abort.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZCanonicalHandoff.sol](../../src/ZZZCanonicalHandoff.sol) |25|8|
| [ZZZCustodyValidation.sol](../../src/ZZZCustodyValidation.sol) |5|5|
| [ZZZFeesCanonical.sol](../../src/ZZZFeesCanonical.sol) |18|0|
| [ZZZMigration.sol](../../src/ZZZMigration.sol) |28|8|
| [ZZZNFTCanonical.sol](../../src/ZZZNFTCanonical.sol) |11|2|
| [ZZZVaultCanonical.sol](../../src/ZZZVaultCanonical.sol) |29|13|
| [ZZZCanonicalLedger.sol](../../src/base/ZZZCanonicalLedger.sol) |15|1|
| [ZZZModule.sol](../../src/base/ZZZModule.sol) |19|0|

<a id="nft-metadata"></a>
### NFT and metadata

Finite quota/artwork draws, VRF original callbacks/drained rotation, transferability, metadata versus economic eligibility and value-unavailable semantics.

| Source | Bodies/modifiers | Declarations |
| --- | ---: | ---: |
| [ZZZNFT.sol](../../src/ZZZNFT.sol) |42|2|
| [ZZZNFTMetadata.sol](../../src/ZZZNFTMetadata.sol) |14|1|
| [ZZZArtwork.sol](../../src/libraries/ZZZArtwork.sol) |3|0|
| [ZZZTypes.sol](../../src/libraries/ZZZTypes.sol) |0|0|

<a id="interface-declarations"></a>
### Interface declarations

Interface-only sources define the typed cross-module, emergency, policy, NFT/canonical and optional v3 wire. Declarations embedded in implementing files remain listed in their source group. ABI/compiler consistency does not prove an external deployment satisfies those declarations.

## Fresh execution and reused evidence

Fresh two-method execution covers infeasible residual geometry rollback/recovery and one-minute USD outage with two-leg harvest, partial claims, raw residual close and later merge. Source-scoped existing lifecycle/long-horizon cases cover ordinary quote activity, downward stored-tick boundaries, main-only entrants, mixed/both-outside legs, mode reversal, ownership/claim ordering and terminal/canonical behavior under their original substitutes. See [verification](VERIFICATION.md) for exact limits rather than counting this table as additional tests.

Unresolved: actual feeds/venues/token/VRF/provider independence, maximum realistic gas/depth/market economics, sustained worker inclusion/outages, actual authority/marketplace/recovery and independent audit. No theoretical exhaustion, arbitrary future code, compromised host/compiler or complete absence of adversarial profit is proved.
