# Current code necessity and boundaries

This is a caller/purpose review of the current architecture, not a proof that
every function is minimal or that an independent auditor cannot find more dead
code. Public getters and user/operator entrypoints can have legitimate external
callers even if no Solidity function in this repository invokes them.

## Concrete contracts

| Contract | Retained purpose / actual consumer |
| --- | --- |
| `ZZZAccessController` | Role-authorized exact operations, module binding/sealing, guardian/keeper authorization and canonical lifecycle; queried by all fixed modules. Zero delay does not remove replay/role/predecessor checks. |
| `ZZZActivationAssets` | Fixed ETH/ZZZ source identity and enable/disable policies; Entry, Registry and custody setup consume them. |
| `ZZZActivationAssetsFactory` | Unique caller-bound Registry child creation; splits embedded initcode without custody/configuration authority. |
| `ZZZActivationEntry` | Atomic owner-funded contribution, typed conversion, caller loss maximum and original-source context; called by holders through reviewed transactions. |
| `ZZZBuyback` | Spend only the classified 5% reserve and prove actual burn of the one fixed ZZZ; called by authorized keepers. Its retargeting setter is removed in this audit. |
| `ZZZCanonicalHandoff` | Complete same-chain capture/import/funding/abort and exactly one successor activation; principal exit alone cannot replace these ownership/reward duties. |
| `ZZZClaimRouter` | Bounded current-owner multi-ledger claims; user preparation and portfolio claim flows consume it. |
| `ZZZCompounder` | Authorized guarded reinvestment of classified compound and attributed idle; keeper maintenance consumes it. |
| `ZZZContributionPricing` | Frozen dual-price/policy basis, conservative marginal-LP verification and historical incumbent backing; Entry and Vault Budget call it. |
| `ZZZCustodyValidation` | Read-only typed request/parking/destination validation for the fixed Migration; it is not another custodian. |
| `ZZZFeeController` | Actual local venue receipts, 80/10/5/5 reserves and incumbent dust; Vault, Membership, Buyback and canonical companion consume it. |
| `ZZZFeesCanonical` | Exact classified fee backing and versioned export/import/abort; the handoff coordinator calls it. |
| `ZZZLPRewardConverter` | Convert already-earned LP holder/collective source balances to the same NFTs' ETH credits; separate from royalties and principal. |
| `ZZZLiquidityManager` | Typed physical LP mint/increase/collect/close/swap with exact budgets and guarded callbacks; Vault and authorized execution modules use it. |
| `ZZZMembership` | One equal collective share per activated NFT, incumbent dust barriers and canonical membership; Vault and Rewards use it. |
| `ZZZMigration` | Same-pair pool movement, exact parking, approved normal/raw custody exit, full recovery and funded local completion. No integrated bridge. |
| `ZZZMigrationBudget` | Actual LP/share/capacity, captured contribution and maintenance limits, composition and authenticated receiver checks; fixed Vault calls it. |
| `ZZZNFT` | ERC-721 ownership, ordered exact-quota/inventory reveal, royalty identity and metadata; holders, marketplace, Vault and ledgers consume it. |
| `ZZZNFTCanonical` | Exact ownership/trait/request/ordinal state transfer and inert importer writes; same-chain handoff consumes it. |
| `ZZZNFTMetadata` | Read-only marked-value evolution and immutable revealed traits/artwork paths; NFT tokenURI calls it. It cannot award rewards. |
| `ZZZOracle` | Reviewed two-source USD bounds, precision/freshness/sequencer policies and fingerprints; pricing/strategy/conversion/maintenance consume it. |
| `ZZZPoolRegistry` | Admitted immutable pool identities, one contribution pool and bounded operating settings; custody, execution, pricing and reads consume it. Unused Registry wrapper bookkeeping is already removed. |
| `ZZZPythPriceFeed` | Optional immutable compatible price-source reader, only when independently selected/configured. It is not a qualified ZZZ feed or update service; optional does not mean abandoned. |
| `ZZZRewards` | Funded NFT-indexed LP/collective balances, fractions, converted credits and current-owner claims; Fees, Membership and holders consume it. |
| `ZZZRoyaltyConverter` | Bounded actual receipt conversion preserving each NFT's source entitlement and ETH credit; royalty settlement workers/holders consume it. |
| `ZZZRoyaltyFactory` | Fixed NFT-owned helper creation and parent bindings; NFT construction uses it. No creator-payment inbox factory remains. |
| `ZZZRoyaltyRewards` | Actual marketplace receipts, activated rarity weights, outage cohorts, custody/recovery and unclaimed rights; NFT, converter and holders consume it. |
| `ZZZStrategy` | Actual price/range validation, bounded balancing, rebalance eligibility and reviewed +/-25/50 width selection; manager/Vault/keeper consume it. |
| `ZZZV4RouteExecutor` | Parent-bound typed hookless v4 conversion; Entry and the two earned-reward converters instantiate/use it. It accepts no arbitrary target/calldata/recipient. |
| `ZZZVault` | Permanent shared LP and per-NFT shares, actual mint/contribution/maintenance/harvest/custody; economic authority lives here, not in the API. |
| `ZZZVaultCanonical` | Owner-bound exact Vault state/backing export/import and delegated read validation; fixed Budget and canonical coordinator consume it. |

The concrete class count is not the deployment instance count: several parent-bound
executors/converters/helpers share an implementation class. Libraries and abstract
bases provide exact transfer, price/range, artwork and authenticated backing
mechanics; they are not separately configurable authorities.

## Compatibility and off-chain code

- Historical fee/accounting/routing profiles, event descriptors, stable Position
  fields/status numbers and saved transactions preserve the meaning of old
  deployments. They are not active creator/bridge paths in the current profile.
- The `nativeAsset` getter and `movePool` alias have documented consumers. Removing
  them requires an explicit compatibility decision, not a text search alone.
- Converter wrapper validation protects actual v3 or WETH settlement. Native
  custody does not call it. It must not be confused with removed Registry metadata.
- Keeper discovery/recovery, strict RPC/fees, HTTP admission, indexer, read and
  unsigned preparation, earnings/lineage replay and release observers each have
  distinct trust and failure boundaries. Off-chain projections never authorize
  claims or principal movement. Examples and legacy rehearsals are explicitly
  gated; existing Anvil-only signing is not public signing support.
- Frozen-source packaging and source-bound function documentation serve review and
  reproducibility; they do not execute tests or approve deployment by themselves.
- Preparation notices are cancellable planning/draining state. Actual freezing
  still requires a sealed committed same-chain importer. They do not provide a
  cross-chain bridge or post-halt recovery.

A conservative [AST-reference scan](internal-reachability.json) starts from386
public/external/constructor/override roots and reaches650 function/modifier nodes,
with no remaining project private/internal candidate orphan. This is a screening
result, not a proof of runtime necessity, external-dispatch completeness or safety.

## Limits of this conclusion

The code retains immediate governance and trusted external custody. Source/runtime
pins do not establish honest oracles, tokens, proxies, venues, VRF or recipients.
No claim of universal necessity, gas optimality or absence of vulnerabilities is
made. See [findings](REVIEW.md) and [verification scope](VERIFICATION.md).
