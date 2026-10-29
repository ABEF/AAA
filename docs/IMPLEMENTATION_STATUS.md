# Feature and evidence reference

[Complete-project audit and improvements](../reports/comprehensive-popl-20261029/REVIEW.md)
implements terminal reserve-venue recovery, relevant keeper identity resets,
final telemetry depth/chronology, stored-history chronology and exclusive,
source-pinned evidence production. Verification is scoped:16 Solidity methods,
82 distinct Python methods across recorded stages (80pass/two platform skips),
and39 fresh normal production gates. This is not a full regression or release
approval. ABI/storage remain unchanged; only Registry bytecode changes. Manager
initcode37-byte and Vault runtime59-byte margins remain. Matching services,
actual providers/marketplaces/gas and independent review stay open.

[Completed historical reconciliation](../reports/historical-reconciliation-completion-20261029/REVIEW.md)
accounts for352 original report narratives/91current guides and235 overlapping
finding groups. Strict frontend/indexer CLI JSON object admission now precedes
workers/RPC/listeners/signals/locks/DB;15 affected methods pass. Earlier13 local
verifier methods are not rerun. Exact82 build pins reuse39normal gates. The
October25static review has19of47changed pins and needs refresh. No Solidity,
financial/timing policy or installed service/site change.
[Verification](../reports/historical-reconciliation-completion-20261029/VERIFICATION.md).

[Keeper coordination](KEEPER_COORDINATION.md) implements service-only compound
waiting, proved internal-harvest clock coalescing and a bounded read-only LP
operation report. The current observer also corrects a previous private-getter
mistake using complete actual bucket inventory. [Evidence](../reports/keeper-coordination-20261029/VERIFICATION.md)
records 261 distinct affected methods: 185 final keeper/report, 12 final
reservation and 64 before the explicitly proved diagnostic-only change. The
scopes are not summed with earlier overlapping campaigns. Matching worker/checker
rollout, real dependencies/timing/gas and independent qualification remain open.
No Solidity or installed service change is implied.

The [operational code follow-up](../reports/operational-reliability-20261029/REVIEW.md) repairs confirmed
history commit/chronology, keeper receipt/management parsing, sold-out readiness,
permanent reservation observation and verification/evidence tooling. 221 distinct
affected methods pass across pinned scopes; no whole Solidity/CI rerun or live
rollout is implied. Existing economic/timing policies remain unchanged.

Current [whole-project execution](../reports/whole-project-execution-20261029/REVIEW.md) completes the internal
source/body review and implements keeper deadline priority, strict durable/log
provenance, final-depth/fee/pool observation and artifact-tooling repairs.
All122previously missing callable outputs are explained. Static review is not
exhaustive execution or independent release approval. Website reference metadata
was published separately at cae44a1d without changing images/signing/configs
or deploying sites.
Actual providers, economics, gas/host/marketplace qualification and audit remain open.

Current fresh source: **accounting4 / custody3 / canonical holder-exit V5**.
[Collective holder return](HOLDER_COLLECTIVE_EXIT.md) replaces external principal
and royalty custody exits. Governance permanently ends LP and pays actual
ETH+ZZZ by shares; NFTs retain transfers, future royalties and earned rewards.
No external recipient/bridge/return ingress remains. Whole-collection handoff
is available only before exit. Earlier source-scoped evidence and accounting3
service/inventory/website qualification remain historical to their original pins.
See [profile4](POSITION_V4.md); new release qualification remains open.


Reviewed 2026-10-29. This describes capabilities and evidence, not a second Todo.
Use [the single task list](../TODO.md) for status, [operator manual](OPERATOR_MANUAL.md)
for procedures, [component map](COMPONENT_STATUS.md) for code boundaries and
[release record](RELEASE_CHECKLIST.md) for approval. **Production NOT APPROVED.**

## Current profile

Fresh source uses accounting4/direct governance2/fee intake1/custody3/pricing2/
Entry routing2/LP execution1/reviewed Entry1 and canonical
`ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`. Eight Position words remain; Exited5
is a terminal local status. Historical1/2/3 deployments/readers/journals retain
original identities. [Profile](POSITION_V4.md), [holder procedure](HOLDER_COLLECTIVE_EXIT.md).

Fresh Strategy maintenance policy2 checks actual physical range exit or an operator range update after the hard governed interval (initial12hours). Historical keeper mode2 uses hourly inside checks; fresh confirmation2 checks
eligible conditions every240seconds and persists1-10minute post-ready jitter without blocking harvest/receipt recovery. Budget capability3 uses its separately governed compound interval after max(lastCompound,lastRebalance), yielding to due rebalance; it never resets that clock. Explicit API profiles verify Strategy2/Budget3 and preserve historical readers. [Operator procedure](OPERATOR_MANUAL.md#coordinate-compounding-with-rebalancing), [new scoped verification](../reports/maintenance-policy-20261027/VERIFICATION.md). No live service/site changes.

Current [manipulation-related hardening](../reports/manipulation-hardening-20261027/VERIFICATION.md) adds keeper/pause completion checks for rebalance/compound/buyback and corrects paid-revert health visibility across restart/unrelated success. It introduces no new economic caps, roles or custody path. Actual profitability, real market/feed/ordering and service qualification remain open; defensive checks are not attack-profit evidence.

The [two-day change audit](../reports/two-day-audit-20261028/VERIFICATION.md) fixes post-exit payout-retry starvation in source keeper scheduling. Canonical receipt clocks throttle repeated batches, durable priority alternates delivery with other jobs, and pending recovery stays first. Source comment corrections preserve ABI/storage/instructions; exact new compiler pins are recorded. No economic rule, signing path or running service changed. [Keeper safeguards](KEEPER_SAFEGUARDS.md) distinguishes contract guards from service policy.

Fresh execution-quality1 adds a Strategy-owned1% default additional-loss floor
after actual directional LP/protocol fees to balancing and Manager swaps/buybacks.
It preserves stronger gross/caller/operation limits and separate converter policy.
Exact same-block reader capabilities and revisions are explicit; historical
profiles remain separate. [Feature scope](EXECUTION_QUALITY.md), [verification](../reports/fee-impact-policy-20261028/VERIFICATION.md).
No passive position or40% rebalance policy is implemented. Fresh confirmation2
adds a15-minute sampled on-chain window, four-minute checks after cooldown,
strict300-second maximum receipt gap and journaled reset recovery. Greater gaps
restart; actual latency can prevent progress. The constructor gap0 requires
reviewed governance configuration. Stable controls are rechecked across full
maintenance. Matching API exposes raw due versus buffered readiness without an
execution promise. [Policy](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer)
and [new evidence](../reports/practical-improvements-20261028/VERIFICATION.md).

The same improvement slice adds current schema6 preflight, healthschema2 metadata,
exact-block/config discovery caching (fresh pre-signing checks retained), explicit
gas refusal diagnostics and native-only Manager cleanup. Actual bindings, runtime
writer/checker rollout, target gas and independent release qualification stay open.

[The day audit](../reports/day-audit-20261028/VERIFICATION.md) revalidates the current
55distinct Solidity/53backend/38normal-gate evidence at exact pins without new
test runs. It corrects documentation and operating qualification gaps; it does
not establish live readiness, manipulation immunity or a new implementation.

The deeper buffer audit also fixes unrelated-job resets, repeated paid clears,
old-window jitter reuse, failed-related-receipt recovery, incompatible outer
polling, clock retreat and contradictory lifecycle/ABI observations. Budget now
captures raw observation state across maintenance; callback invalidation reverts
the complete LP operation. Post-exit governance orientation remains available
without reopening principal. Final evidence:217affected Solidity passes,
272distinct source-scoped Python methods (271pass/1missing-cast skip),39normal
object gates. Counts are scoped, not a global security or production approval.

[Review and evidence](../reports/practical-improvements-20261028/VERIFICATION.md).

The [independent follow-up](../reports/confirmation-followup-20261028/REVIEW.md)
fixes foreign clear-window adoption and initial raw-read reset gaps; validates
actual policy helper/Budget bindings during cooldown; exports separately anchored
latest policy health without false healthy timestamps; binds physical PosM
PoolKey/ticks to the Vault; and aligns wallet custody totals with NFT views.
[Verification](../reports/confirmation-followup-20261028/VERIFICATION.md) records
399distinct methods (398pass/1explicit skip,53new), plus exact reused Solidity/build
pins. Source Solidity/ABI/storage/economics and installed services are unchanged.
Old schema6 inventories require fresh observation of new required physical fields.

The [third-pass review](../reports/third-pass-20261028/REVIEW.md) adds focused
keeper checkpoint and indexer/conversion snapshot repairs after tracing35main
commits from October26-28. Solidity/economics remain unchanged; operator recovery,
strict provider-input validation and source-scoped evidence are updated together.
Prior reports remain scoped history, not additive full-release test counts.

Current source additionally implements [confirmation2 and manual emergency1](EMERGENCY_REBALANCE.md).
Ordinary samples require physical/reference same-side exit; automatic width
policies cannot bypass that guard. Governance can review policy relaxation or
manually perform a paused emergency with optional financial checks. Exact
accounting/custody/lifecycle remain; nearly all principal may be lost if financial
guards are disabled. [Source-scoped review/evidence](../reports/independent-rebalance-20261029/VERIFICATION.md)
does not qualify feeds, economic profitability, actual gas/services or an
independent audit. No installed service/site/Anvil/deployment changed. The wider
current handwritten-body review is recorded in the [whole-project execution](../reports/whole-project-execution-20261029/COVERAGE.md); historical reports retain their pins.

## Smart contracts

| Capability | Implemented behavior and boundary | Reference |
| --- | --- | --- |
| NFT ownership and mint | ERC-721,1,000 supply, dormant mint creates no LP/membership. Direct mint currently pays0.05ETH to the fixed recipient; required OpenSea gross/net/recipient path remains unfinished. | [NFT](../src/ZZZNFT.sol), [mint qualification](MINT_INTEGRATION_QUALIFICATION.md) |
| Fair assignment and metadata | Fixed1,000-entry draw,600/300/100 rarity quotas,58palettes/four pattern slots and four LP-value evolution states. VRF callback stores original words; ordered finalization, no reroll/admin traits. Actual provider and permanent artwork hosting remain unqualified. | [Metadata/reveal](NFT_METADATA.md), [artwork publication](ARTWORK_PUBLICATION.md) |
| Activation and growth | ETH/fixedZZZ, conservative$100 activation/$5 growth, stronger pool minima; original-source pricing and actual marginal LP with captured budget/caller cap. Exact temporary venue approvals, no incumbent subsidy. | [Entry](ACTIVATION_ENTRY.md), [preparation](ACTIVATION_PREPARATION.md), [minimums](CONTRIBUTION_MINIMUMS.md) |
| Independent pricing | Two reviewed USD sources/asset,3% disagreement band; bounded freshness/precision/round checks and frozen price fingerprints. Actual independent sources/updaters remain open. | [Price security](PRICE_SECURITY.md), [optional Pyth reader](PYTH_PRICE_SOURCE.md) |
| Shared LP custody | Many NFT share accounts per physical LP; one contribution pool enabled at a time, four permanent historical custody buckets. Marked current LP+attributed idle/compound is separate from contributed USD/rewards. | [Architecture](ARCHITECTURE.md), [Position4](POSITION_V4.md), [dynamic liquidity](DYNAMIC_LIQUIDITY.md) |
| LP fee allocation | Physically received LP fees split80/10/5/5; individual LP shares/equal activated collective/compound/ZZZ buyback.20raw-unit batches and incumbent dust settlement; no configurable split or Power. | [Economics](ECONOMICS.md), [Fees](../src/ZZZFeeController.sol), [Rewards](../src/ZZZRewards.sol) |
| Royalties and claims | ERC-2981 requests5%;100%actual eligible royalties use rarity1/2/3, separate from LP. Outage isolation protects old cohorts. Current owner claims; unclaimed balances/fractions follow NFT. Bounded ClaimRouter and separate source-to-ETH converters preserve attribution. | [Settlement](ROYALTY_SETTLEMENT.md), [ClaimRouter](CLAIM_ROUTER.md), [LP settlement](LP_ETH_SETTLEMENT.md) |
| Maintenance | Shared-position rebalance/compound, LP routing1 bounded reviewed-venue comparison/actual-core sizing, zero/one swap and attributed idle reinvestment. Contributions trade/deploy only entrant funds. Reviewed optional keeper widths +/-25/50% in ZZZ price in ETH; cooldown/price/venue/captured aggregate guards. | [Ranges](RANGE_POLICY_UPDATES.md), [idle](IDLE_AND_DUST.md), [loss limits](EXECUTION_LOSS_POLICY.md) |
| Governance and containment | One human operator controls the direct governance wallet and services; no separate operator role or multi-person committee. Two-step wallet replacement, guardian pause and limited keeper capabilities remain; no timelock queue/executor. Sealing fixes module/token bindings. Mint-only pause and dependency-free pool disable are implemented. | [Governance](GOVERNANCE.md), [post-seal controls](POST_SEAL_POLICY.md) |
| Movement and collective return | Native ETH/fixedZZZ same-pair moves/parking before exit; governance may irreversibly close all LP and allocate actual ETH+ZZZ by shares. Isolated direct batches pay current owners; owner fallback handles rejected transfers. No external custody recipient or royalty drain. Pending compound joins principal; rewards/buyback remain separate. | [Holder exit](HOLDER_COLLECTIVE_EXIT.md), [scoped review](../reports/holder-collective-exit-20261027/REVIEW.md) |
| Collection replacement | Same-chain canonical V5 carries ownership/ledgers/backing with funded abort only before collective exit. Terminal payout ledger is not imported; post-exit preparation/replacement stays blocked even after all principal is paid. | [Canonical handoff](CANONICAL_HANDOFF.md) |

Defaults remain2%contribution/1%conversion/3%maintenance, governance ceilings10%,
gas separate and stronger caller/venue minima retained. Raw exit has explicit raw
minima and no aggregate-loss guarantee. An unqualified route/feed cannot be made
safe by a documentation claim or simulated example.

[Operator-selected LP execution](LP_EXECUTION_POLICY.md) now includes immutable
LP routing1: at most four explicitly reviewed ETH/ZZZ execution pools, bounded
actual-core quotes, best sampled deployed value and zero/one swap independently
of the LP destination. Contributions swap/deploy only their own budget; old
idle/compound cannot mask the marginal LP floor. Empty catalog disables swaps
without fallback. Governance can configure catalog/solver and venue slippage
up to10%, preserving operating/caller/captured limits. See [atomic LP routing review](../reports/atomic-routing-20261028/REVIEW.md)
and [verification](../reports/atomic-routing-20261028/VERIFICATION.md). Manual
widths, hard initial 12 hours and durable service jitter remain. Fresh
confirmation2 evaluates eligible conditions every 240 seconds; hourly inside
checks belong to historical policy2. Independent hourly harvest and the separate
compound interval remain. Actual rollout, depth,
gas, economic qualification and independent audit remain open. The $1m per-NFT
cap is existing configuration, not a capacity proof.

Manual `Vault.rebalance` already exists for keeper-authorized wallets; governance
alone does not grant that capability. The [documented procedure](OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time)
skips local jitter/evaluation scheduling only, retains on-chain eligibility and
separately handles same-key journal reconciliation. This documentation update
adds no contract behavior, ABI, test pass, service rollout or production approval.

## Backend and operations

| Capability | Implemented behavior and boundary | Reference |
| --- | --- | --- |
| Confirmed read API | Explicit accounting4/custody3/V5 pins, irreversible flag and phase, known-zero Exited LP and retained royalty eligibility. Principal return is a separate exact ETH/ZZZ allocation/paid view; it is not earnings. Historical1/2/3 remain separate. | [API](FRONTEND_API.md), [principal reader](../frontend_api/principal_return.py) |
| Earnings and claims history | NFT/collection/current-holdings24h/all-time processed earnings, separate LP/collective/royalties and lifetime claims through verified same-chain epochs. Today's original-currency prices; claims/conversions/imports not new income. | [Earnings](EARNINGS_HISTORY.md), [lineage](FRONTEND_LINEAGE.md), [royalty reporting](ROYALTY_REPORTING.md) |
| Fee-integrity reconciliation | Current fee1 verifies actual module version, exact funded-credit/allocation pairs and pinned observed-key dust. Malformed summary data rejects; genuine outages null affected metrics. Authentic full logs/timestamps remain necessary. | [Latest fixes](../reports/backend-remediation-20261026/REVIEW.md) |
| Unsigned transaction preparation | Complete Entry simulation/newLP/caller cap checks, exact approval step, expiry and separate gas. Bounded current3 claims reject contradictory inactive balances/malformed activation data before a wallet draft. Parked/outbound and optional-currency deferral rights remain. Opt-in direct-mint drafts exist; production/website mint gates reject unsupported OpenSea integration, while the preparer itself is not a universal public-mint block. No user signer in API. | [Activation preparation](ACTIVATION_PREPARATION.md), [transactions](FRONTEND_TRANSACTIONS.md) |
| Request and index resilience | Strict RPC chain quantities/unique finite JSON/exclusive envelopes and sanitized bounded parser-failure failover; per-client admission, finite supervised workers/deadlines/RPC budgets; anchored SQLite replay/reorg handling and independent-provider history-window audit. Real hosting/capacity qualification remains open. | [Ingress](API_INGRESS.md), [concurrency](CONCURRENT_SERVICES.md), [index recovery](INDEXER_RECOVERY.md), [history audit](HISTORY_AUDIT.md) |
| Keeper | Optional main-process systemd progress watchdog supervises stalled I/O in the reviewed120s example unit; standalone commands still lack this hard supervisor. Discovers shared buckets, simulates eligible upkeep, persists intents/receipts/budgets and recovers without automatic resend. Accounting4 defaults to hourly independent collectFees; historical defaults and explicit overrides are preserved. Authenticated due harvesting can continue after maintenance RPC failure; malformed configuration/ABI still fails closed, and saved pending errors stop work. Buyback priority/currency rotation prevents starvation. Optional metadata notifications; dry-run default. | [Reward timing/fairness](OPERATIONS.md#reward-timing-and-maintenance-schedule), [recovery](KEEPER_RECOVERY.md), [rehearsals](KEEPER_REHEARSALS.md) |
| Release tooling | Explicit schema6/accounting4/custody3/V5 observer and offline gate verify17helpers, holder-share/terminal payout/backing and policy bindings. Incomplete actual dependencies remain blocked; historical schema5 is inspection-only. Strict JSON/file/read bounds remain. No deployment authority. | [Preflight](PRODUCTION_PREFLIGHT.md), [blocked fresh scaffold](../config/production.holder-exit.example.json) |

## Frontend boundary

Popldemo keeps its existing public simulation. The separate poplint build now
implements an explicit schema3/accounting3 reader and unsigned-review profile,
including ETH/fixedZZZ admission, current module/canonical/runtime checks and
correct captured contribution limits. [Scoped verification](../reports/current3-website-20261026/VERIFICATION.md)
records451affected JS passes, including46new methods and six real Python API DTO
fixtures with synthetic dependencies; no actual providers or public transactions
are qualified. Missing integration configuration shows unconfigured, never demo
balances. Native2/historical local profiles, signer policy and journals remain.
[Environment procedures](SITE_ENVIRONMENTS.md) keep the two public targets separate.
Actual current3 contracts/API/feeds/routes/marketplace/service acceptance remain open. See [website profile](NATIVE_WEBSITE_PROFILE.md),
[deployment integration](DEPLOYMENT_WEBSITE.md) and [browser wallet](BROWSER_WALLET.md).

## Current evidence and limits

[Whole-project review](../reports/whole-project-audit-20261029/REVIEW.md) adds
ownership-only optional-currency outage isolation, strict stored-history decoding,
durable metadata priority and corrected keeper/current-fork CI selection. User
approved240-second service checks with unchanged900/300on-chain confirmation;
old300schedules/pending/reset/jitter remain preserved. Five current canonical
composition methods and75affected Python methods pass in their exact scopes;
unchanged217EVM/39normal gates are reused, not rerun. Per-function pending depth,
separately published website metadata (not deployed), real operating/provider/compiler-lowering and
independent-audit gates stay explicit. [Verification](../reports/whole-project-audit-20261029/VERIFICATION.md).
Observing during cooldown is proposed in the sole Todo, not implemented.

[Holder-return verification](../reports/holder-collective-exit-20261027/VERIFICATION.md) records133distinct affected Solidity passes,37normal object gates,16new profile4 methods and11new automatic-delivery methods. Separate historical/common scopes and platform skip are explicit; no combined full-regression or live approval is implied. Optional keeper delivery is implemented/disabled, and actual source4 website/services remain open.


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

At that historical backend checkpoint,44production Solidity/31installed dependencies/
four build inputs matched its publication. Fresh fee-quality source instead has
45production/31dependency inputs and its own [exact evidence](../reports/fee-impact-policy-20261028/VERIFICATION.md). No new full test count, live provider approval,
published CI result, operating uptime or independent audit is inferred. Actual
OpenSea/VRF/prices/routes/authorities/artwork/services/gas/operations and audit
remediation remain release gates. Documentation/publication does not deploy.


## Current selected-pool fork scope

[Current native harness verification](../reports/current-pool-fork-20261026/VERIFICATION.md)
records11distinct successful EVM methods across affected source-bound runs and
11focused transport/runner methods. The whole final11-method suite was not rerun.
The actual pinned native ETH/ZZZ venue, runtime parents, fees, swaps, shared
native/ZZZ contributions, small growth, transfer-following fees and atomic
unsafe-growth rollback are exercised. Explicit mock governance/randomness/USD
sources and fork-only funding do not qualify live services, prices, gas,
rebalancing or sustainable revenue. The maintained whole runner still rejects
missing/skipped/failed cases. Production Solidity and economic rules are unchanged.
