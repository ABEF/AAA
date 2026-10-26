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
| Unsigned transaction preparation | Complete Entry simulation/newLP/caller cap checks, exact approval step, expiry and separate gas. Bounded current3 claims reject contradictory inactive balances/malformed activation data before a wallet draft. Parked/outbound and optional-currency deferral rights remain. Opt-in direct-mint drafts exist; production/website mint gates reject unsupported OpenSea integration, while the preparer itself is not a universal public-mint block. No user signer in API. | [Activation preparation](ACTIVATION_PREPARATION.md), [transactions](FRONTEND_TRANSACTIONS.md) |
| Request and index resilience | Strict RPC chain quantities/unique finite JSON/exclusive envelopes and sanitized bounded parser-failure failover; per-client admission, finite supervised workers/deadlines/RPC budgets; anchored SQLite replay/reorg handling and independent-provider history-window audit. Real hosting/capacity qualification remains open. | [Ingress](API_INGRESS.md), [concurrency](CONCURRENT_SERVICES.md), [index recovery](INDEXER_RECOVERY.md), [history audit](HISTORY_AUDIT.md) |
| Keeper | Optional main-process systemd progress watchdog supervises stalled I/O in the reviewed120s example unit; standalone commands still lack this hard supervisor. Discovers shared buckets, simulates eligible upkeep, persists intents/receipts/budgets and recovers without automatic resend. Authenticated due harvesting can continue after maintenance RPC failure; malformed configuration/ABI still fails closed, and saved pending errors stop work. Buyback priority/currency rotation prevents starvation. Optional metadata notifications; dry-run default. | [Reward timing/fairness](OPERATIONS.md#reward-timing-and-maintenance-schedule), [recovery](KEEPER_RECOVERY.md), [rehearsals](KEEPER_REHEARSALS.md) |
| Release tooling | Bounded strict/sanitized holder inventory input and argument handling; exact integer slot0 consistency/fee validation in both observed and manually supplied states; current schema5 inventory/pinned observer, RPC/mint qualification gates, immutable artwork bundle and frozen review export. Tools do not deploy or replace approval. | [Preflight](PRODUCTION_PREFLIGHT.md), [review package](FROZEN_REVIEW_BUNDLE.md) |

## Frontend boundary

The separate public website simulates financial actions. Published native2 reads/
unsigned reviews and Anvil-only browser signing are historical supported profiles,
not current3 public acceptance. Current3 integration and ETH/fixedZZZ/cap copy
alignment remain open. Existing local test state, signer policy and public-null
deployment are preserved. See [website profile](NATIVE_WEBSITE_PROFILE.md),
[deployment integration](DEPLOYMENT_WEBSITE.md) and [browser wallet](BROWSER_WALLET.md).

## Current evidence and limits

[Systematic adversarial review](../reports/system-adversarial-20261026/REVIEW.md)
and [coverage](../reports/system-adversarial-20261026/COVERAGE.md) map every one
of608 functions/31 constructors/13 receive hooks to multiple applicable static cases.
All44 project Solidity units/helpers are identified/pinned;1,987 scenario instances
are not execution tests. RPC/holder input corrections and the source-only keeper
watchdog are covered by244 distinct affected methods:241 passes/3 explicit skips,
42 new methods included once, zero failures/errors/source drift. [Verification](../reports/system-adversarial-20261026/VERIFICATION.md)
preserves source-stage negative controls and reuses unchanged contract evidence.
The watchdog leaves financial/recovery method bodies and journals unchanged;
its real Linux/systemd kill/restart/signing-interruption rehearsal remains open.
No new on-chain exploit was confirmed in this internal scope; real qualification
and independent audit remain required. Solidity/ABI/rights and services unchanged.

[Adversarial market/input review](../reports/market-adversarial-20261026/REVIEW.md)
and [verification](../reports/market-adversarial-20261026/VERIFICATION.md):223affected
backend methods pass;15actual-v4 composed methods include both out-of-range
contribution directions, subsequent rebalance/claims and past-donation exclusion
for newcomers. Shared exact TickMath validation rejects inconsistent sqrt/tick/
fee state while preserving legitimate stored boundary ticks. A missing fixed-ZZZ
fixture binding was corrected and its first failures retained. Production Solidity,
ABI, economic rights and service configuration are unchanged; funded receipts do
not establish organic volume or sustainable returns.

[Adversarial reward review](../reports/reward-resilience-20261026/REVIEW.md): the
final affected scope has 443 unique methods, 437 passes/6 explicit skips, zero errors
or failures and stable source pins. One new actual-v4 test proves stale prices
block rebalancing while actual fee collection and backed claims preserve LP,
NFT shares and reserves. [Verification](../reports/reward-resilience-20261026/VERIFICATION.md)
preserves the first wider regression failure and its narrower exception-boundary
correction. No contract/rate/permission/API-schema change or service rollout.

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
| [Deep cleanup](../reports/deep-cleanup-20261025/VERIFICATION.md) |32scoped Solidity/41Python/37normal object gates in its recorded scope; dependency/build bindings retained. Contract reference31contracts/608 functions/13 receive hooks. |
| [Earlier source-scoped reports](../reports/README.md) | Local/fork/UI/keeper/rights receipts apply only to their stated revisions, fixtures, chains and environments. Older counts, bridges, inboxes or WETH profiles are not current claims. |

Unchanged production 44 Solidity/31installed dependencies/four build inputs matched
the last backend publication. No new full test count, live provider approval,
published CI result, operating uptime or independent audit is inferred. Actual
OpenSea/VRF/prices/routes/authorities/artwork/services/gas/operations and audit
remediation remain release gates. Documentation/publication does not deploy.
