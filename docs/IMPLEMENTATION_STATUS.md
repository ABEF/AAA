# Feature and evidence reference

Reviewed 2026-10-26. This describes capabilities and evidence, not a second Todo.
Use [the single task list](../TODO.md) for status, [operator manual](OPERATOR_MANUAL.md)
for procedures, [component map](COMPONENT_STATUS.md) for code boundaries and
[release record](RELEASE_CHECKLIST.md) for approval. **Production NOT APPROVED.**

## Current profile

Fresh source uses accounting3/direct governance2/fee intake1/custody2/pricing2/
routing2/reviewed Entry1 and canonical `ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4`.
There is one fixed ZZZ identity and native ETH contribution input, not stablecoin
admission, WETH principal accounting, creator inboxes or integrated bridges.
Historical readers remain explicit; existing deployments/journals are unchanged.

## Smart contracts

| Capability | Implemented behavior and boundary | Reference |
| --- | --- | --- |
| NFT ownership and mint | ERC-721,1,000 supply, dormant mint creates no LP/membership. Direct mint currently pays0.05ETH to the fixed recipient; required OpenSea gross/net/recipient path remains unfinished. | [NFT](../src/ZZZNFT.sol), [mint qualification](MINT_INTEGRATION_QUALIFICATION.md) |
| Fair assignment and metadata | Fixed1,000-entry draw,600/300/100 rarity quotas,58palettes/four pattern slots and four LP-value evolution states. VRF callback stores original words; ordered finalization, no reroll/admin traits. Actual provider and permanent artwork hosting remain unqualified. | [Metadata/reveal](NFT_METADATA.md), [artwork publication](ARTWORK_PUBLICATION.md) |
| Activation and growth | ETH/fixedZZZ, conservative$100 activation/$5 growth, stronger pool minima; original-source pricing and actual marginal LP with captured budget/caller cap. Exact temporary venue approvals, no incumbent subsidy. | [Entry](ACTIVATION_ENTRY.md), [preparation](ACTIVATION_PREPARATION.md), [minimums](CONTRIBUTION_MINIMUMS.md) |
| Independent pricing | Two reviewed USD sources/asset,3% disagreement band; bounded freshness/precision/round checks and frozen price fingerprints. Actual independent sources/updaters remain open. | [Price security](PRICE_SECURITY.md), [optional Pyth reader](PYTH_PRICE_SOURCE.md) |
| Shared LP custody | Many NFT share accounts per physical LP; one contribution pool enabled at a time, four permanent historical custody buckets. Marked current LP+attributed idle/compound is separate from contributed USD/rewards. | [Architecture](ARCHITECTURE.md), [Position3](POSITION_V3.md), [dynamic liquidity](DYNAMIC_LIQUIDITY.md) |
| LP fee allocation | Physically received LP fees split80/10/5/5; individual LP shares/equal activated collective/compound/ZZZ buyback.20raw-unit batches and incumbent dust settlement; no configurable split or Power. | [Economics](ECONOMICS.md), [Fees](../src/ZZZFeeController.sol), [Rewards](../src/ZZZRewards.sol) |
| Royalties and claims | ERC-2981 requests5%;100%actual eligible royalties use rarity1/2/3, separate from LP. Outage isolation protects old cohorts. Current owner claims; unclaimed balances/fractions follow NFT. Bounded ClaimRouter and separate source-to-ETH converters preserve attribution. | [Settlement](ROYALTY_SETTLEMENT.md), [ClaimRouter](CLAIM_ROUTER.md), [LP settlement](LP_ETH_SETTLEMENT.md) |
| Maintenance | Shared-position rebalance/compound, bounded two-pass placement and attributed idle reinvestment. Reviewed optional keeper widths +/-25/50% in ZZZ price in ETH; cooldown/price/venue/captured aggregate guards. | [Ranges](RANGE_POLICY_UPDATES.md), [idle](IDLE_AND_DUST.md), [loss limits](EXECUTION_LOSS_POLICY.md) |
| Governance and containment | One human operator controls the direct governance wallet and services; no separate operator role or multi-person committee. Two-step wallet replacement, guardian pause and limited keeper capabilities remain; no timelock queue/executor. Sealing fixes module/token bindings. Mint-only pause and dependency-free pool disable are implemented. | [Governance](GOVERNANCE.md), [post-seal controls](POST_SEAL_POLICY.md) |
| Movement and external exit | Same-actual-pair local pool move, paused parking, approved normal fixed-ZZZ exit or explicit raw actual-asset exit. Trusted recipient, exact funded recovery/local completion; no generic sweep, remote proof or forced return. | [Custody handoff](GOVERNED_CUSTODY_HANDOFF.md), [recovery matrix](CHANGE_AND_RECOVERY.md) |
| Collection replacement | Same-chain localV4 handoff freezes/transfers complete NFT/ledger/backing state to one replacement with funded abort. Existing draws must finish. External custody alone does not relocate these rights; future-chain transport is excluded. | [Canonical handoff](CANONICAL_HANDOFF.md), [holder preflight](HOLDER_PREFLIGHT.md) |

Defaults remain2%contribution/1%conversion/3%maintenance, governance ceilings10%,
gas separate and stronger caller/venue minima retained. Raw exit has explicit raw
minima and no aggregate-loss guarantee. An unqualified route/feed cannot be made
safe by a documentation claim or simulated example.

## Backend and operations

| Capability | Implemented behavior and boundary | Reference |
| --- | --- | --- |
| Confirmed read API | Runtime/module/canonical/owner/physical LP/share checks at a confirmed block. Native ETH inventory and both claim ledgers required; impossible inactive rewards reject. Missing values stay unavailable. | [API](FRONTEND_API.md), [collection reads](COLLECTION_READS.md), [lifecycle](FRONTEND_LIFECYCLE.md) |
| Earnings and claims history | NFT/collection/current-holdings24h/all-time processed earnings, separate LP/collective/royalties and lifetime claims through verified same-chain epochs. Today's original-currency prices; claims/conversions/imports not new income. | [Earnings](EARNINGS_HISTORY.md), [lineage](FRONTEND_LINEAGE.md), [royalty reporting](ROYALTY_REPORTING.md) |
| Fee-integrity reconciliation | Current fee1 verifies actual module version, exact funded-credit/allocation pairs and pinned observed-key dust. Malformed summary data rejects; genuine outages null affected metrics. Authentic full logs/timestamps remain necessary. | [Latest fixes](../reports/backend-remediation-20261026/REVIEW.md) |
| Unsigned transaction preparation | Complete Entry simulation/newLP/caller cap checks, exact approval step, expiry and separate gas. Bounded claim preparation and opt-in direct-mint drafts exist. Current production qualification and website mint capability reject the unsupported OpenSea path; the preparer itself is not a universal public-mint block. No user signer in API. | [Activation preparation](ACTIVATION_PREPARATION.md), [transactions](FRONTEND_TRANSACTIONS.md) |
| Request and index resilience | Per-client admission, finite supervised workers/deadlines/RPC budgets; anchored SQLite replay/reorg handling and independent-provider history-window audit. Real hosting/capacity qualification remains open. | [Ingress](API_INGRESS.md), [concurrency](CONCURRENT_SERVICES.md), [index recovery](INDEXER_RECOVERY.md), [history audit](HISTORY_AUDIT.md) |
| Keeper | Discovers shared buckets, simulates eligible upkeep, persists intents/receipts/budgets, recovers nonce/fee state without automatic resend. Buyback priority/currency rotation prevents persistent maintenance or a first currency monopolizing all opportunities. Optional metadata notifications; dry-run default. | [Reward timing/fairness](OPERATIONS.md#reward-timing-and-maintenance-schedule), [recovery](KEEPER_RECOVERY.md), [rehearsals](KEEPER_REHEARSALS.md) |
| Release tooling | Current schema5 inventory/pinned observer, RPC/mint qualification gates, immutable artwork bundle and frozen review export. Tools do not deploy or replace approval. | [Preflight](PRODUCTION_PREFLIGHT.md), [review package](FROZEN_REVIEW_BUNDLE.md) |

## Frontend boundary

The separate public website simulates financial actions. Published native2 reads/
unsigned reviews and Anvil-only browser signing are historical supported profiles,
not current3 public acceptance. Current3 integration and ETH/fixedZZZ/cap copy
alignment remain open. Existing local test state, signer policy and public-null
deployment are preserved. See [website profile](NATIVE_WEBSITE_PROFILE.md),
[deployment integration](DEPLOYMENT_WEBSITE.md) and [browser wallet](BROWSER_WALLET.md).

## Current evidence and limits

[Reward allocation review](../reports/reward-allocation-20261026/REVIEW.md) checks
exact split, claim isolation and randomized order/frequency, and fixes buyback
starvation. [Verification](../reports/reward-allocation-20261026/VERIFICATION.md):
two new Solidity methods pass (one 1,000-run fuzz case);376 unique affected Python
methods yield370 passes/6 explicit skips, zero failures/errors. No production
Solidity/ABI/economic change or installed service rollout. Allocation at harvest,
claims and actual reinvestment/burn are distinct; sample jobs remain disabled.

[Keeper/LP audit](../reports/keeper-lp-audit-20261026/REVIEW.md) adds exact loaded-
config health identity and strict conversion Booleans, fixes the stale range test
domain and brings fresh rehearsal source to current3/fee1/native shape. Production
Solidity/economics/ABI are unchanged. Final affected Python:354passes/5Unix skips
from359methods;9range methods pass including1,000 fuzz runs. Standalone fixture/
reader checks are not the still-pending Linux crash/systemd or real-market campaign.


| Evidence | Actual verification scope |
| --- | --- |
| [Fee breakdown](../reports/backend-remediation-20261026/VERIFICATION.md) |167distinct affected Python methods (31new/136existing),54inputs pinned. Five backend modules; no Solidity/schema/economic change. Earlier focused runs overlap, not extra coverage. |
| [Full candidate audit](../reports/full-audit-20261025/VERIFICATION.md) | Actual399-finding Slither output manually triaged against47bindings; internal coverage PASS.11scoped Python methods, one composed gas case9,591,082<12M; successful solc output and37unchanged object lengths. Later Forge host-cache CLI failure preserved. Not full release regression. |
| [Deep cleanup](../reports/deep-cleanup-20261025/VERIFICATION.md) |32scoped Solidity/41Python/37normal object gates in its recorded scope; dependency/build bindings retained. Contract reference31contracts/608functions/13receive hooks. |
| [Earlier source-scoped reports](../reports/README.md) | Local/fork/UI/keeper/rights receipts apply only to their stated revisions, fixtures, chains and environments. Older counts, bridges, inboxes or WETH profiles are not current claims. |

Unchanged production 44 Solidity/31installed dependencies/four build inputs matched
the last backend publication. No new full test count, live provider approval,
published CI result, operating uptime or independent audit is inferred. Actual
OpenSea/VRF/prices/routes/authorities/artwork/services/gas/operations and audit
remediation remain release gates. Documentation/publication does not deploy.
