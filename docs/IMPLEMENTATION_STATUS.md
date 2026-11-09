# Feature and evidence reference

The [current double-check](../reports/today-change-review-20261109/REVIEW.md)
adds exact phase/time and count-type preflight validation plus focused funded
Entry trace regressions. This changes no Solidity, economics, service or site.
Source9/V9 remains distinct from mint2/V10; transport rotation is not a V10
handoff capability. Actual qualification remains open.

The [market qualification record](../reports/market-qualification-20261109/REVIEW.md)
adds dated official-feed/source/proxy and actual venue/quote/fork evidence. No
source pair or default1% conversion route is qualified. Underlying feed identity,
freshness, bidirectional range depth and exact operation guards remain release
requirements; no financial limit, runtime, live configuration or environment is
changed. Earlier synthetic-depth successes retain their original scope.

The [OpenSea source integration](OPENSEA_MINT.md) adds mint2/helper1,
canonicalV10 and schema17 with20 callable helpers plus2 inert data children.
Initial20free-team/500paid-allowlist/480public allocations are configurable;
AL is one NFT per distinct listed address, unused AL rolls public and
unused team stays reserved. Original-recipient lifetime mint counts,
dormancy and original two-word VRF requests are preserved. Normal size
limits remain unchanged; see the [source-scoped verification](../reports/opensea-integration-20261109/VERIFICATION.md).
Backend read/claim and lineage support is implemented with explicit mint2/V10
pins; default1 remains V9 and direct mint2 preparation returns Use OpenSea.
Actual OpenSea custom-drop onboarding, exact fee/payers, live VRF/gas, matching
website/installed-consumer and operating/independent acceptance remain open.
Earlier V9/schema16 evidence below retains its original scope; it does
not verify the mint extension or upgrade a served site/runtime.


[Fee-flow audit](../reports/fee-flow-audit-20261107/REVIEW.md) fixes
v3 final-native ETH pricing/wrapper18decimals, fresh7 affordable-prefix conversion
and late deadline/UTC-day checks, strict simulation output and zero-noop earnings
replay. Optional unsigned transaction policy2 adds reviewed operator gas limits
(21k–64M engineering cap, confirmed-block bound, full20%headroom); policy1 remains
12M/schema1. Policy2 requires explicitly matching consumers; no wallet signer,
running configuration, service/site/Anvil/journal or heartbeat is changed.
New normal87/46+2passes; strict532 has15current-context reviews/517unique exact
referenced-source reuse. Converter executable changes only; Rewards metadata
changes and all semantic storage/ABIs plus canonical object bytes are preserved.
F3payload/parts stay byte-identical; source pins are rebound, never old runtimes.
Actual11converter cases,338keeper passes+2explicit skips,28reader methods/fresh
one-method wire producer and56API methods have separate source-scoped evidence;
do not add overlapping stages. Actual routes/providers/gas/consumer rollout and
independent approval remain open. [Verification](../reports/fee-flow-audit-20261107/VERIFICATION.md).

Reviewed 2026-11-07. This records implemented source, not another task list.
[Todo](../TODO.md) owns work; [release approval](RELEASE_CHECKLIST.md) remains
**NOT APPROVED**. Existing contracts, services, websites and journals are unchanged.

## Current profile

Fresh **accounting7 / LP-allocation1 / portfolio2 / maintenance3 / confirmation3 / compound4 /
custody5 / emergency2 / LP routing2**, with pricing2, Entry routing3, reviewed
policy2, direct governance2 and fee intake1. The eight-word Position remains;
fresh royalty4/canonicalV10 carries sale end/capacity and exact-unit ticket rights,
and rejects older peers.
Tuple shape does not imply runtime compatibility.
[Profile](POSITION_V7.md), [portfolio controls](OPERATOR_MANUAL.md#portfolio-management-controls).
Production inventory is schema17/mint2 with explicit residual-reinvest1/raw-exit1 bindings; schema16 remains historical. It retains20 callable helper pins plus2 inert Factory code-data children; the exact-unit allocator is internal code. Factory storage2 preserves the exact RoyaltyRewards creation payload and accounting ABI. Historical schema9/custody4 retains direct Entry3 and20helpers; schema8 keeps
its routed Entry2 and21-helper profile; no conversion child remains on fresh Entry. Historical accounting5/4 and inventory7/6
profiles remain explicit and are never silently rewritten.

Use [consolidated findings](AUDIT_FINDINGS.md) for historical dispositions and
[the report map](../reports/README.md) for exact source-scoped evidence. A source
mechanism, test pass, configured service and approved production release are
separate milestones.

Current capabilities and exact evidence are in the tables below and the
[report map](../reports/README.md). Operator procedures have a source-bound
[complete short call catalog](OPERATOR_MANUAL.md#operator-call-tables), with
separate exact permission/output notes; it is documentation, not execution approval.

Fresh [exact-unit LP rewards](EXACT_LP_ALLOCATION.md) now integrate Vault post-write share synchronization, one-time equal Membership synchronization, whole current-owner claims, same-NFT/component conversion and lossless raw-phase canonicalV9. Profile7/schema16/source9 consumers explicitly authenticate LP-allocation1 and the fixed RewardsCanonical companion. Historical6/V8 and checkpoint1 are not reinterpreted. [Evidence](../reports/exact-lp-integration-20261106/VERIFICATION.md); target gas, actual rollout and checkpoint2 operating qualification remain separate work. Explicit checkpoint2 source support is described below.

## Smart contracts

| Capability | Implemented behavior | Reference |
| --- | --- | --- |
| NFT identity | ERC-721, fixed artwork draw, exact1,000 rarity quotas; actual VRF provider still unqualified. | [Metadata](NFT_METADATA.md) |
| Contributions | ETH or the fixed ZZZ; future-governed minima(default$100 activation/$5 growth); checkpoint incumbents, use entrant-only budgets, verify marginal main LP, then issue shares from aggregate NAV. Residuals and rebalance centre/clock remain unchanged. | [Entry](ACTIVATION_ENTRY.md), [pricing](PRICE_SECURITY.md) |
| Shared LP portfolio | Single main by default, optional one residual in the same pool; both NFTs remain Vault-owned. Aggregate raw principal/valuation includes both actual ranges, not a sum of their liquidity units. | [Portfolio profile](POSITION_V7.md) |
| Ordinary replacement | Both single/hybrid reject inactive stored-tick quotes before ranking and verify the new main is physically active before/after callbacks; hybrid requires its configured6000–9999bps main floor(default60%) and complementary residual ceiling(default40%) at captured post-cost valuation. Natural placement meeting that floor needs no swap. Otherwise bounded approved-route sizing targets a rounding-safe floor. Failed sizing/mint/close reverts atomically. | [Execution policy](LP_EXECUTION_POLICY.md) |
| Residual geometry | Default half of the corresponding main side, a governed positive tick-spacing gap(default1) beyond spot. Width governed1–10000bps of that side. At most one residual; mixed/filled inventory remains valued until whole adjustment. | [Range controls](RANGE_POLICY_UPDATES.md) |
| Same-main residual consolidation | Paused governance `Migration.consolidateResidual(request,forced)`: harvest/close only residual or recover prior attributed idle, balance and increase same main, atomically apply modeOFF. Shares/centre/rebalance clock preserved; compound clock updated; designated compound/rewards/buyback separate. Guarded routing now filters active candidates for preserved bounds, with financial guards and no keeper timing; force is explicit. | [Inputs/evidence](OPERATOR_MANUAL.md#same-main-residual-consolidation), [review](../reports/residual-main-consolidation-20261106/REVIEW.md) |
| Residual-only recovery | New paused governance-only Migration.closeResidual(ParkingRequest), explicit RESIDUAL_EXIT_VERSION1 across Migration/Vault/Manager/position child. Harvest both then burn only registered residual; exact raw proceeds to same bucket idle. Main/shares/clocks/configuration preserved; no swap/payout/compound release. | [Management controls](OPERATOR_MANUAL.md#portfolio-management-controls) |
| Enable/disable | Manual reviewed desired mode; enabling permits rather than forces a residual. Disabling retains both actual legs and NFT reward membership until a guarded single-position merge succeeds; no immediate deactivation or trade. | [Operator](OPERATOR_MANUAL.md) |
| Ordinary eligibility | 85% actual centre-to-edge human ZZZ-price distance; physical and independent reference on the same side.600-second sampled window/maxgap300, source240-second checks, fresh60–300-second service jitter, initial hard12hours. Manual geometry changes are a distinct cooldown-gated exception. | [Confirmation](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer) |
| Financial checks | Dual USD sources with3% agreement; captured default3% contribution/1% conversion/3% maintenance limits, governance ceilings10%, gas separate. Additional-loss default1% after known directional fees remains separate. | [Price security](PRICE_SECURITY.md), [execution quality](EXECUTION_QUALITY.md) |
| Exact-unit LP integration | Actual Rewards uses constant-work root credit, ten-level whole claims/views, both-book old-weight synchronization and raw pending/high/low V9. Current-owner claims and same-NFT conversion conserve every allocated unit. | [Rules/evidence](EXACT_LP_ALLOCATION.md) |
| LP revenue | Combined actual fees from both legs allocated once per asset at80/10/5/5. Individual shares/equal active collective; no dormant dilution. Independent claims, compound and buyback reserves. | [Economics](ECONOMICS.md) |
| Royalties | Settlement4 original-currency claims; ×1/×2/×3 weights with GCD-normalized exact-unit allocation and a saved rotating remainder cursor. Every allocated raw unit belongs to an NFT; no allocated rounding remainder remains after all eligible claims. Recovery2 assigns reviewed unallocated units at current active weights. Initial/prefund/zero-cohort and token-failure limits remain. No royalty converter; current owners inherit unpaid rights; ERC2981 requests5%, without universal payment enforcement. | [Exact allocation](EXACT_ROYALTY_ALLOCATION.md), [current audit](../reports/last24h-audit-20261105/REVIEW.md) |
| Compounding | Existing range, both-leg NAV and separate interval after last compound/rebalance; keeper waits for in-range main below the adjustment threshold/no pending geometry. Entrants cannot spend incumbent idle/compound. | [Coordination](KEEPER_COORDINATION.md) |
| Recovery | Governed same-pair move/resume can create a residual under destination mode ON, without ordinary keeper timing; financial/custody guards remain. Both-leg same-pair movement, raw paused parking and collective ETH+ZZZ holder return. Custody5 allocation/distribution is governance-only; holder LP/royalty/fallback claims remain. Pending compound follows shares; rewards/buyback backing remain separate. Pre-exit canonical export requires every residual closed. | [Parking](CUSTODY_PARKING.md), [holder return](HOLDER_COLLECTIVE_EXIT.md), [canonical](CANONICAL_HANDOFF.md) |
| Emergency | Paused governance-only reviewed manifest; both-leg liquidity-sensitive fingerprint. Financial bypass is explicit and can lose nearly all principal; structural rights/ownership/settlement remain. | [Emergency](EMERGENCY_REBALANCE.md) |

The [moving-market preparation supplement](../reports/consolidation-races-20261106/REVIEW.md) clarifies fixed bounds/live price, coherent snapshots and stale review handling. It changes tests/procedures only; normal/static production pins remain those of the same-main implementation.

Current [both-flow audit](../reports/moving-market-flows-20261106/REVIEW.md) changes only Manager guarded-manual quote filtering and keeper pre-sign checking. ABI/storage/profile shapes remain; exact Manager runtime pins change and require fresh adoption. Normal/static/reference and finite focused test evidence do not qualify running services.

## Backend and operations

Confirmed-read and preparation boundaries remain explicit. RPC endpoints are a
validated immutable snapshot, budgeted convenience calls use the metered path,
and strict new-work validation does not discard a valid pending recovery intent.

| Capability | Implemented source boundary |
| --- | --- |
| Confirmed reads | Fresh7 independently proves per-leg principal from captured sqrt/ticks/PosM L, containment, exact stable and L-sensitive fingerprints; no aggregate-only admission. Explicit accounting7 graph/runtime/version checks; both physical IDs/owners/keys/ticks/liquidity and aggregate principal authenticated at one confirmed block. Desired-disabled residuals remain included. Physical reads preserve owners/raw funded claims during price outages; valuations remain unavailable. No maintenance readiness inferred. Old profiles remain separate. |
| Claim planning | Opt-in /v1/claims/plan accepts up to32 exact selections, simulates bounded subsets under existing12M/fee/work limits and returns only one freshly verified draft. Every unresolved entry remains explicit; no signing, queue or automatic skip. [Procedure](CLAIM_PLANNING.md). |
| Factory deployment | Fixed creation payload moves from storage slots into exactly2 authenticated inert data children. Payload/royalty rules unchanged; source-bound schema16 and actual returned-runtime gates required. [Storage format](FACTORY_CODE_STORAGE.md). |
| Unsigned activation/growth | Fresh graph including actual typed-executor verification, control and portfolio review binding; exact Manager→typed child→PosM trace and entrant marginal main liquidity; no public signing added. |
| Keeper | Fresh3 threshold/window semantics, durable jitter/reset/pending-first recovery, in-range compound wait, authenticated harvest coalescing and operation diagnostics. Raw checks during cooldown; paid observation enrollment near hard eligibility avoids waste. Late gas-enveloped full LP simulation and final policy/nonce/funding/head/deadline/day-budget checks preserve original intent before signing. |
| Inventory | Schema17/mint2/custody5/reinvest1 validates20helpers plus2 immutable REVERT-prefixed Factory data children, both physical legs, primary mint books and exact-unit royalty4; reporting5/canonicalV10 are explicit. Schema10 converting royalties and schemas9/8/7/6 retain explicit historical inspection. Example is unqualified. |
| Manual operation preparation | [Typed preparation](MANUAL_LP_PREPARATION.md) now covers park/resume/residual-only close and begin/close/allocate/distribute collective exit, alongside separate Active B/C/D. Direct empty-code governance only; exact fetched inputs, explicit caller floors, confirmed/latest control review and frozen-gas simulations. Distribution preserves configured batch gas and reports partial counts without per-ID success guesses. No signing, queue, fallback or execution approval. Parked forced-D, contract-wallet envelopes and actual provider/operator qualification remain open. [Evidence](../reports/operator-management-20261109/REVIEW.md). |
| Earnings | Separate LP/collective/royalties, current-price USD and claimable versus earned/claimed. Fresh7 replays exact whole-unit trees from complete raw history. Checkpoint1 remains6-only; explicit checkpoint2 preserves raw exact trees/pending/phase/direct rights and a complete raw24-hour suffix. Lineage/archive/workload/operating qualification remain open. Claims/conversions/imports are not income; same-currency first allocation is counted once; exact-unit cursor/cohort state must match replay and checkpoints. Missing data stays unavailable. |

Explicit fresh read/keeper configs set custody_version5 and check actual runtime.
Keeper principal_distribution is disabled/rejected on5; governance pays/submits
terminal batches. Owner earned-reward claims remain available.
[Full permissions](ACCESS_PERMISSIONS.md).

See [API](FRONTEND_API.md), [unsigned preparation](ACTIVATION_PREPARATION.md),
[operation report](KEEPER_COORDINATION.md) and [preflight](PRODUCTION_PREFLIGHT.md).
Implementing source does not qualify a host, provider, maximum gas or operating latency.

## Frontend boundary

Popldemo remains simulation and the separately served current3 poplint is unchanged.
The [fresh source9 website consumer](SOURCE9_WEBSITE_PROFILE.md) implements explicit
schema4/accounting7/LP1/custody5/Entry3/royalty4/V9 reads and unsigned reviews,
including original-currency royalties, pending LP ZZZ, principal returns, governed
thresholds and fully classified gas-aware claim plans. Source9 never constructs
the signer, including on loopback; both build configurations stay null.
[Original source evidence](../reports/source9-website-20261109/REVIEW.md) retains
its synthetic Entry3 draft scope. The [actual follow-up](../reports/source9-actual-entry-20261109/REVIEW.md)
fixes fixed-ZZZ admission/epoch parsing and verifies real API/consumer reviews,
four confirmed ETH/ZZZ contributions, exact approvals, LP/share/metadata state and
atomic rollback. Optional activation policy2 has matched unsigned consumers.
Successes use explicit synthetic external depth/controlled feeds/VRF; actual
market/provider/wallet/hosting acceptance and independent review remain open.
[Environment map](SITE_ENVIRONMENTS.md); historical [current3 profile](CURRENT_WEBSITE_PROFILE.md).

## Collective exit scale and mixed-wallet evidence

[Focused assurance](../reports/holder-exit-assurance-20261103/REVIEW.md) adds corrected
1000-NFT enumeration, distinct-address and37-wallet mixed-holdings checks plus
real NFT rarity/tier/growth/prior-claim/transfer composition and local real-v4
both-leg exit.10distinct selected methods span explicit stages, including one
1000-case fuzz method. Production source/policy/profile are unchanged; normal
size/static evidence is reused at matching pins. Failed stale-fixture attempts
remain recorded. This is not target-chain gas, full-suite or independent approval.

## Latest audit consolidation

The [four-report reconciliation](../reports/four-report-consolidation-20261104/RECONCILIATION.md)
separates the indexer anchor/streaming, receipt-model, keeper-deadline and manual
recovery corrections from their remaining release limits. It preserves original
failure records, source scopes and distinct counts. Current contract evidence is
the manual-safeguard source scope, not older whole-project unchanged-source prose.

New startup safeguards in Indexer atomically admit schema/identity, close failed
connections, reject SQLite integer overflow before filesystem work and require
durable rollback/WAL. Valid restart retains history/cursor/ownership.93selected
Python methods pass, including9new regressions. Table/index names/columns/keys and
identity format are unchanged; no migration/rescan or operating rollout occurs.
Actual storage/recovery qualification remains open.



## Current evidence and limits

| Evidence | Source scope | What it does not establish |
| --- | --- | --- |
| [Exact-unit LP integration](../reports/exact-lp-integration-20261106/VERIFICATION.md) | Fresh7/LP1/V9/schema16: actual Rewards, share/membership hooks, whole claims/conversion and lossless canonical books. Normal87source gates46+2carrier; strict532records222current/310exact reuse. Source-scoped host/native/core/canonical methods and619affected backend methods; final315source type closure. | Broad45-class compilation ran out of memory before EVM results; selected corrected scopes are explicit. Cold32-entry claim exceeds12M, cold8 fits only its fixture. No full-suite/publicCI, target gas, checkpoint2, rollout or independent approval. |
| [Current 24-hour audit](../reports/last24h-audit-20261105/REVIEW.md) | Exact-unit royalty4 and affected cross-repository changes, with source-scoped verification recorded in the report. | No deployment, maximum-state target gas, supported OpenSea mint path, operating acceptance or independent approval. |
| [Four-report follow-up](../reports/four-report-consolidation-20261104/VERIFICATION.md) |93focused Python successes,9new startup cases; four input reports and current Solidity/dependency/build pins preserved. | No fresh contract execution, live storage/host acceptance or independent approval. |
| [Manual safeguard audit](../reports/manual-safeguard-audit-20261104/VERIFICATION.md) | Two view fixes;85distinct selected EVM successes across retained stages,47focused Python passes,43fresh normal gates and471fresh static records(13current-context review/458exact referenced reuse). ABI/storage unchanged; callable37/818/37/13 has0gaps. | Not a full suite, installed-runtime upgrade, target gas/operating rehearsal or independent approval. |
| [Authority change normal/static record](../reports/authority-audit-20261103/VERIFICATION.md) | Historical custody5 revision52production/31dependency sources;43normal gates/471static records,19current contexts reviewed and452unchanged reused.14distinct selected EVM passes across explicit corrected stages;25corrected Python methods. Reference37/818/37/13 has0gaps; Migration39/Vault635/Budget237/Balancer360runtime headroom. | No full suite/CI, independent review, deployment gas, service or production approval. |
| [Direct Entry3 normal/static record](../reports/direct-entry-v3-20261103/VERIFICATION.md) | Prior custody4 source52production/31dependency sources;43normal gates,471triaged static records; reference37contracts/818functions/37constructors/13receivers without note gaps. Entry runtime9863; Vault635/Budget237/Migration20/Balancer360headroom. | Full regression, published CI, independent audit, deployment gas, future edit capacity or production approval. |
| [Entry/native regressions](../reports/direct-entry-v3-20261103/test-stages.json) |28distinct selected successes across recorded scopes;19unchanged successful bodies reused after one assertion correction. Failures and empty selection retained. |28fresh final-source tests in one run, actual target-chain feeds/venues or browser/keeper operating acceptance. |
| [Backend/profile tooling](../reports/direct-entry-v3-20261103/python-verification.json) |314selected Python successes across two scopes; explicit direct/historical tuple, config/helper/observer and operator/reference/publication boundaries. |Actual tracing-provider or matching website acceptance. |
| [LP lifecycle](../reports/lp-lifecycle-audit-20261102/REVIEW.md), [multi-day journeys](../reports/portfolio-long-horizon-20261102/VERIFICATION.md) | Ordinary active-main candidate selection and composed main/residual/entry/reward/recovery behavior at recorded source/test pins. Relevant unchanged code can support reuse. | All market paths, profitable60/40 strategy, maximum populated gas or live uptime. Geometry getter coherence is not independent source proof. |
| [Backend/action consolidation](../reports/consolidation-20261103/VERIFICATION.md), [fault boundaries](../reports/action-resilience-audit-20261102/ACTION_MATRIX.md) | Scoped endpoint, budget, validation, receipt and availability corrections. | Honest providers, hard DNS/header timeouts, Linux host/storage/off-host recovery or source rollout. |
| [Documentation/findings consolidation](../reports/project-consolidation-20261103/REVIEW.md) | Current procedures/navigation/finding provenance and exact unchanged-source/evidence checks. | New contract execution, new independent security opinion or closure of external release gates. |

Older source/ABI/size/static/test counts remain in immutable reports and are not
combined into a current pass. Refresh applicability after code/settings/dependency
changes. The [compiler assessment](../reports/direct-entry-v3-20261103/compiler-assessment.json)
uses an explicitly captured official snapshot with source graph/layout limitations;
refresh advisories for the frozen release.

## Current selected-pool fork scope

[Prior fork evidence](../reports/current-pool-fork-20261026/VERIFICATION.md) is historical.
The [actual fresh7/Entry3 follow-up](../reports/source9-actual-entry-20261109/REVIEW.md)
executes ETH/ZZZ activation/growth through real API and unsigned website reviews.
The original-depth case fails safely; positive cases explicitly add synthetic
external depth and use controlled feed/VRF substitutes. They do not qualify
actual market depth, independent sources, burn ABI, target fees/gas, wallet
signing or operation. Never weaken policy or relabel fixtures to claim approval.

## Bounded post-seal flexibility

[ProtocolPolicy1](ADAPTABLE_POLICY.md) governs approved future terms within fixed
bounds; Entry3/review-policy2 binds scoped contribution terms before callbacks.
[Manual controls](OPERATOR_MANUAL.md#future-operating-settings) distinguish a chain
setter from a new runtime/worker/site rollout. Retired architecture and old
journals remain separate. Real providers/authorities/OpenSea, source9 services/
website, storage/operations, economics/gas and independent audit remain open.

Fresh royalty4 retains the [one-hour sale-close activation window](ROYALTY_LAUNCH_WINDOW.md)
and adds [exact-unit allocation](EXACT_ROYALTY_ALLOCATION.md): GCD-normalized rarity
weights, deterministic rotating indivisible units, and no allocated rounding
remainder after all eligible claims. Initial holding, prefunds, zero participants,
unsupported currencies and pathological-token failures remain distinct. CanonicalV9
rejects older peers. Actual OpenSea, gas/workloads and independent approval remain open.
