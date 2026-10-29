# Whole-project PoPL audit and improvement prompt

Historical date-limited brief: [exact prior Git text](https://github.com/ABEF/AAA/blob/2feee92f6bc13b09bae1d43f36bfb7cf6c8faac9/docs/THIRD_PASS_AUDIT_PROMPT.md).
Current understanding, two prompt challenges and execution evidence are retained
in [the audit record](../reports/whole-project-execution-20261029/REVIEW.md).

## Objective

Understand, critically review and improve the entire PoPL project: product rules,
contracts, economics, every user/operator operation, data services, keeper,
website and wallet boundaries, artwork/metadata, deployment/build/test pipeline,
dependencies, observability, recovery, documentation and release decisions.
Seek concrete improvements to correctness, security, availability, usability,
latency, efficiency and maintainability. Do not stop after a plan or report if
justified repairs can be implemented and verified within authorization.

This is the current canonical audit brief, replacing the former date-limited
third-pass prompt at this stable filename. Baseline: contract main
`2feee92f6bc13b09bae1d43f36bfb7cf6c8faac9` **plus the captured, intentional
uncommitted confirmation2/emergency1 candidate**, and website main
`e5bb2163e0af0019bd917f65711c1f669b2d6224`, reviewed2026-10-29 Paris.
These are the historical execution's baseline identities, not a version selection
for a future run. Before reuse, record the actual current heads, dirty state,
profiles and source hashes from both repositories; do not restore the old heads
or treat their then-uncommitted candidate as still unpublished.
Audit the entire current project, not only recent diffs. Baseline file hashes
distinguish unpublished work, original unrelated dirty files and historical
deployment compatibility. Save original dirty documents before replacement.
Historical reports and prior prompts retain their original source scope; neither
a current document link nor matching feature name upgrades their evidence.

## 1. Understand first, then challenge this prompt twice

Before drafting the final prompt, reconstruct the actual project from source,
requirements, ABI/dependency implementations, configuration, tests, operating
guides and previous decisions. Read each repository's instructions and record
heads/status. Save source-pinned understanding maps for contracts, services,
frontend and operations. Inventory every concrete module/helper, public read/
write/receiver/constructor, feature and management operation. Generated ABI rows
are navigation, not evidence every body has been independently reviewed.

For each feature/operation identify: purpose and economic owner; caller and
inputs/units; preconditions and lifecycle; state writes/external calls; outputs,
events and downstream consumers; backing/rounding; time/cost/resource bounds;
failure, stop/restart, recovery and irreversible effects; applicable versions;
current evidence and actual unknowns. Reconcile source versus prose conflicts.
Never fill an unknown with a plausible address, number, zero or prior assertion.

Choose needed knowledge/tools deliberately. Read relevant primary specifications
and installed version-pinned implementations; record how they apply, their
limitations and cost/regression tradeoffs. Apply an available skill only when
it improves the actual task, after reading its instructions. Do not install a
security plugin, create images, change toolchains or run UI automation by habit.
Refresh a current source-bound knowledge assessment. The earlier
[knowledge record](../reports/whole-project-audit-20261029/KNOWLEDGE.md) is a
starting point; check exact versions/settings and primary documentation again
where facts may have changed. No available generic skill or plugin is an audit
certificate.

After building draft1, perform two separate sequential challenges:

1. **Challenge1, coverage and meaning:** compare the prompt with every mapped
   feature/operation, financial class, role, lifecycle and environment. Find
   omissions, contradictions, retired features, generic prescriptions and
   unverifiable guarantees; revise with concrete reasons.
2. **Challenge2, independent adversarial feasibility:** review that revised
   prompt afresh against code/specs, counterexamples, authorization, evidence,
   implementation and recovery constraints. Verify each important factual claim
   or label its uncertainty. Check the plan cannot pass by weakening a gate,
   reusing stale evidence, changing policy silently or reporting a source edit
   as a deployed/qualified feature. Revise again, save both critiques and hashes.

Only then execute the final prompt. Retain blocked questions/accepted assumptions
explicitly and continue independently safe work. No test count or checklist can
prove no possible bug or replace independent release approval.

## 2. Established rules and authorization

- Fresh accounting4/governance2/fee1/custody3/pricing2/routing2/reviewedEntry1,
  LP-routing1/quality1/confirmation2/emergency1 and canonical same-chain holder-exitV5.
  Existing Anvil/legacy codecs/journals keep exact identities; no silent migration.
- One fixed deployment ZZZ and native ETH inputs, minimum100USD activation/5USD
  growth, stronger pool minima, governed cumulative `maxPositionUSD` cap, intended initially at1mUSD per NFT. One enabled
  contribution destination and at most four permanently registered custody
  buckets (including reservations); aliases/history can grow separately.
  No stablecoin input, replaceable ZZZ, creator inbox, integrated
  bridge, arbitrary executor/sweep or external-custody exit.
- At most1,000ERC721 NFTs, exact600/300/100 rarities and finite fixed artwork draw;
  reveal-bound palette/pattern/rarity immutable. Activation is permanent; current
  marked LP selects artwork, not eligibility. Metadata terminal stage4 differs
  from PositionStatus.Exited5. No new artwork texture or palette policy.
- Actual harvest80/10/5/5: share-weighted owner/equal activated collective/
  compound/fixed-ZZZ buyback-burn.20raw-unit split/remainders and fractions are
  explicit, including incumbent-owner settlement of sub20 boundary dust.
  Separate100% actual eligible royalties use rarity1/2/3; ERC2981
  requests5% but does not universally enforce payment. Current owner inherits
  all unclaimed rights. Earnings, claimable, claimed and principal differ.
- Two reviewed independent USD sources per asset, selected3% agreement, no
  spot/peg/missing-feed fallback. Captured contribution2%, conversion1% and
  maintenance3% default caps, governed at most10%; gas separate. Additional loss
  after actual directional trading fees defaults1%, governed0-10%. Stronger
  caller/venue/captured floors remain. These are different control categories.
- Hard initial12-hour ordinary rebalance interval; physical outside range or
  explicit governed width update, no centre chasing. Manual ZZZ-price-in-ETH
  +/-25/50%; separate compound interval and independent hourly harvest. No new
  passive/40%/volatility/TWAP strategy or cumulative loss breaker without decision.
- Sampled900sec confirmation, source checks240sec and strict maxgap300sec, greater delay
  restarts; constructor gap0 stops ordinary sampled readiness. Manual-width exception
  preserves cooldown. Service jitter60-600sec begins after readiness; continue
  sampling. Outer polling, sample clock, receipt time and execution are distinct.
- Confirmation2 defaults to physical **and configured independent-reference**
  exit on the same side of the actual LP bounds. Target-only/reference-only/
  opposite-side exits do not qualify ordinary replacement. Governed reviewed
  relaxation invalidates samples. Optional automatic keeper widths cannot
  coexist with enabled reference protection; manual governance widths retain
  their cooldown exception. Source/market independence is not established by
  this control. Observing during cooldown is still proposed, not authorized
  merely by this audit; changing it requires an explicit policy decision.
- Separate manual emergency1 is paused-governance-only, before terminal exit,
  no keeper scheduler/API fallback. Selected timing/price/value/operation/sample
  checks may be bypassed per reviewed manifest; exact assets, custody, budgets,
  shares/reserves, typed venues, raw minima and lifecycle remain structural.
  Financial bypass can permit near-total principal loss. Treat this as accepted
  governance trust, then audit accidental privilege leakage/context cleanup/
  retained-control pinning and rollback, not as a claim of trustless protection.
- Distinguish selected initial settings from governed legal bounds. Supported
  changes require compatible downstream cadence/configuration and requalification;
  do not make12hours or900/300 immutable by rewriting documentation.
- One human operator controls direct governance; limited automated keeper and
  separate guardian capabilities remain. No new committee, role or timelock.
  Reviewed replacement code/dependencies remain accepted governance trust.
- Normal holders cannot redeem principal. Paused governance may irrevocably end
  LP, close actual ETH/ZZZ buckets, include pending compound and allocate/pay
  current holders in bounded batches. Earned rewards/future royalties/transfers
  survive. No restart, custodian recipient or post-exit canonical replacement.
  Same-pair moves/parking and compatible pre-exit same-chain handoff remain.
- Production mint is intended for OpenSea; current direct0.05ETH mint lacks that
  primary-drop integration. Intended buyer gross0.05ETH, recipient net actual
  platform fee, gas separate. Supported VRF/marketplace/provider/authority facts
  must be evidenced, not inferred from mocks or generic chain support.
- Use main only. Preserve unrelated dirty files, old reports, Anvil8902/NFTs/LP/
  balances/journals/dist, public site roots and paused monitoring. Public signing
  remains disabled; browser signing remains Anvil-only; public
  DEPLOYMENT/INTEGRATION_DEPLOYMENT null. Popldemo remains
  simulation; served poplint is unconfigured current3, not fresh4 acceptance.
- This source audit authorizes no public transaction, funded-wallet use,
  deployment, seal, service/website rollout, server access or monitor restart.
  Do not print/log/commit secrets. Source publication is separate from deployment.
  The website checkout is outside the task's writable roots: inspect it and
  prepare/test any justified source patch in an isolated evidence copy. Apply a
  concrete, reviewed non-signing source correction only through the proper file
  approval boundary; preserve signer bytes, old profiles/journals, dist overlays
  and public configs. Do not build/install into a preserved serving directory. Continue all
  independently authorized contract/backend/CI/documentation repairs.
  Primary-source browsing is read-only research. No public RPC probe is required
  to complete local review; any optional probe needs its own authorized read scope.

## 3. Whole-project review matrix

Review every applicable row for normal, boundary, adversarial, delayed, concurrent,
callback, dependency-fault and recovery behavior. Trace complete journeys across
components; do not assume local correctness composes into system correctness.
Review unused/dead/obsolete behavior against current requirements, preserving
needed historical receipt decoders. Separate refactor from financial/policy change.

### A. Architecture, permissions and lifecycle

Audit all module/helper/factory ownership/bindings, setup/seal order, immutable
identities and permitted post-seal edits. Build call/role and state-transition
matrices: operating/pause/mint-only/pool-stop/preparation/frozen/importing/retired/
cancelled/parked/terminal. Inspect cross-function/read-only reentrancy, receiver/
token/oracle callbacks, control changes before/after external calls, privilege
revocation, admin compromise, lost keys, malicious successor and confused deputy.
Do not invent trustless safety against explicitly trusted governance.

### B. Financial conservation, contributions and valuation

Derive equations for actual assets versus classified principal/idle/compound,
LP owner/collective liabilities/fractions, buyback, royalties, dust/quarantine,
pending funding and returned principal. Check double counting and denomination.
Trace original budget, exact approvals/native value, conversion/placement,
marginal LP and incumbent NAV/share issuance. Include first/last/tiny/large/zero
shares, donations, forced ETH, fee-on-transfer/rebase/revert behavior, out-of-range
one-sided deposits, post-swap incumbents, price changes, refund/approval callbacks,
floor/ceiling rounding and all rollback paths. Cumulative contribution cap is not
market NAV. Evaluate costs and feasibility without silently loosening retention.

### C. Rewards, royalties, claims and reporting

Independently reconstruct20-unit80/10/5/5 receipts and carry, share/member indices,
fraction checkpoints, old-fee settlement before joins/top-ups, equal collective,
rarity cohorts/outage recovery, native receipts and source-to-ETH redistribution.
Exercise different claim/transfer/order/batch sequences,1000NFT population,
short supply, rejecting/contract owners, paused/terminal claims and late receipts.
Ensure compound/buyback only spend their own classification; verify actual ZZZ
burn, not an assumed dead-address transfer. LP claims do not harvest or rerun
80/10/5/5. Royalty claims may synchronize/index previously received pending funds
before paying; distinguish that funded recognition from the payout itself.
Do not require whole claimable sums to equal indexed liabilities: backed
fractions/division dust and boundary owner-dust settlement must remain explicit,
not be misclassified as theft or silently redistributed to enforce exact ratios.
Backing must cover classified obligations; forced prefunds/quarantine can make
backing greater. Boundary dust settlement does not imply exact lifetime split
ratios for every20-unit fragment.

Reconcile NFT/collection/current-wallet totals, individual+collective LP plus
royalties, current claimable versus lifetime generated/claimed,24h processing
time/fraction crossing, original currency at today's confirmed USD, conversions,
predecessor imports and post-exit principal. Missing or contradictory data stays
unavailable/error. Real owner callbacks may legitimately change later batch
claims; do not force false preview equality.

### D. LP execution, pricing, time and economics

Review actual core/periphery/Permit2/TickMath/liquidity/fee implementations at
installed pins. Verify native settle, fixed PoolKey/owner/range/liquidity, actual
post-withdrawal quote context, bounded candidate sizing/catalog, zero/one swap,
exact deltas/approval cleanup and no incumbent/prefund subsidy. A bounded solver
is not globally optimal. Validate source rounds/age/precision/negative/future/
sequencer states, common-mode/proxy/issuer risks and captured revisions/bounds.

Evaluate rebalance, width update, compound, independent harvest and buyback
guards together. Check sampled identity/reset/clear/pending behavior, exact
boundary ticks, clock retreat, changed same-value policies and strict cadence
liveness. Distinguish enforced caps from IL, repeated bounded erosion, keeper
personal trading, public MEV/price manipulation, inactivity and gas economics.
Measure only actual authorized environments; do not infer profitable attacks or
their absence from a spot consistency check.

### D1. Normal-operation safety versus availability

Audit controls as an interacting system, not as a count of checks. For every
gate identify threat, measurement/units, legal configuration, captured/rechecked
context, actual blocking outcome, authority able to repair and production cost.
Keep accounting/custody/authorization invariants distinct from economic caps
and service scheduling. Repeated pre/post callback checks may protect different
moments; do not delete them merely because their names look duplicated.

Reproduce busy serial job queues and strict observation deadlines: pending/nonce/
receipt recovery remains first, but optional conversion/buyback/metadata work or
unrelated retry backoff must not inadvertently consume all sample opportunities.
Prioritize a correctly due reset/observation without signing concurrently or
renewing evidence after an observed fault. Preserve initial12h,900/300 and240sec,
existing durable schedules, quotas, clear acknowledgements and fairness outside
time-critical windows. A scheduler repair is not a guaranteed target-chain SLA.

Examine raw-rebalance versus confirmed-candidate priority: reference disagreement
may block replacement while raw eligibility blocks compound. Do not change raw
priority to ready-only and reopen a path around the confirmation safeguards.
Record the economic choice if a different policy needs user approval.

Trace two-source3% uncertainty, conservative upper-input/lower-output quote,
gross/fee-adjusted1% swap floors, target pre-mint budget floor, overall3% captured
maintenance,5% idle and caller LP minimum together. Configuration validity is
not route executability. Distinguish known fees from price impact and accounted
idle from loss. Improve diagnostics/feasibility validation when justified;
never auto-widen thresholds or substitute a less conservative price to pass.

### E. Full canonical handoff and terminal recovery

Separately review local same-pair move, reversible parking, governance terminal
holder return and whole-collection pre-exit replacement. Reconstruct all six
canonical domains/row shapes, counters, root order, ownership, traits/random
provenance, shares/contributions, indices/paid/fractions, assets, backing and
quarantine. Test capture versus settlement versus late receipts, sequential
export/import/funding/acknowledgement, prefunds, fully funded abort, atomic
retirement/activation, replay and multi-hop forward/lineage. Calculate lifetime
workflow from actual admissible dimensions, not only per-call bounds: aliases/
history can grow despite four funded buckets. Report practicability limits;
do not silently cap aliases, delete history or introduce an import override.

For holder return, verify actual-close proceeds plus compound, shares/ordinal
cumulative floors, all raw units, current-owner lookup, paid flags, isolated
batch failure/retry and owner-only fallback. Inspect contract/marketplace escrow
beneficial ownership, partial global exit, dependency failure, no reopening and
continued royalties. No administrator shortcut may erase/backfill liabilities.
Record what key loss, broken token/venue or chain loss makes impossible.

### F. Keeper, storage, concurrency and operations

Audit every operation from discovery/simulation to durable intent, broadcast,
receipt/canonical proof, spend/nonce/checkpoint update and restart. Include failure
between each write/call, hashless ambiguity, pending-first, delayed/duplicate/
reorg receipts, nonce gaps/manual same-key transactions, midnight/L1/EIP1559 fee
accounting, signer environment, private files, locks and old-host fencing.

Check fairness across buckets/conversions/buybacks/metadata/principal payouts,
paid-revert/retry clocks, stale backup/disk full/atomic-write failure, wall-clock
versus monotonic time, watchdog main-progress/group cleanup, shutdown and paired
health writer/checker rollout. Invalid required config is not a license to adopt
unreviewed defaults. Source/config hashes are not running-code attestation.
Audit real operating instructions for authority, exact input/output, verification,
stop/restart, rollback and irreversible limitations; do not execute them on an
installed service merely to audit them.
Separate permissions from normal scheduling: Vault.collectFees is permissionless
under its lifecycle guards; governance starts/closes terminal exit, while bounded
allocation/current-owner delivery does not grant exit authority to its caller.

### G. Backend, indexer, ingress and unsigned preparation

Review ABI/JSON/RPC strict types and bounds, identity/canonical selectors, complete
snapshots and cache scope; coherent dishonest RPC remains a stated trust risk.
Review indexer one-writer transaction/reorg/backfill/log authenticity, bounded
lineage/events/queries, consistent backup/WAL and data corruption/rebuild.
Validate log/transaction indices, hash/index bijection and per-block transaction grouping/order
at ingestion and stored replay, preserving genuinely omitted optional legacy
fields. Reject malformed provided fields and contradictory receipt/event identity
before atomic cursor advancement; demonstrate both positive and negative paths.
Filtered eth_getLogs results legitimately have numeric index gaps. Contiguity
means a transaction cannot disappear and reappear after another transaction in
the same block, not a gapless numeric sequence. Preserve omitted optional legacy
transactionIndex values, reject malformed supplied values, and include valid
filtered-gap and partial-index positive controls.

Assess HTTP framing, origins/proxy identity/CORS/CSP, body/result limits, client
admission, independent process work/deadlines, overload, slow calls, cancellation,
resource cleanup/quarantine, disk/log exhaustion and request retry storms.

Review exact unsigned mint/activation/growth/claim requests, asset/route/feed/
module binding, full simulation and actual marginal LP, amount precision, exact
spender/approval/value, deadline/gas/caller caps and action/session isolation.
Unsupported OpenSea/fresh-profile services must stay blocked, not look live.
Public owner queries and unsigned preparation do not authenticate wallet control;
actual chain authorization/execution determines who can exercise the rights.

### H. Website, wallets, UX and metadata/assets

Audit actual source of both demo and integration with each local/versioned
profile kept separate. Review current-account/provider/network authorization,
event revisions, persistent per-account intents, partial approval, rejection,
hashless/pending/confirmed-but-API-lag recovery, refresh/tab/concurrent-user races
and explicit read/unsigned versus signing. Do not broaden the protected signer.
The extension's visibly selected account need not be the permitted account list
exposed to this dapp. Confirmed receipts must not be downgraded to failed/new
submissions because a later API/indexer observation is delayed or unavailable.
Fresh4requires a new explicit browser profile with holder-principal/terminal
semantics; current3support or backend4support cannot substitute for it.

Trace card-level versus aggregate/inventory block semantics, ownership changes,
loading/processing/error wording, finite retries/backoff, numeric units/BigInt,
unavailable values, data freshness, dormant/activated/exited rights, claim versus
growth dialogs and compound/fee distinctions. Review keyboard/focus/dialog/status
accessibility, mobile/reflow/color, motion/audio controls, HTML/SVG/URL injection,
provider-icon content, secure links/storage and static response headers.
Track provenance for every economic value: do not sum independent card snapshots
as an atomic wallet total. Inventory/owner disagreement requires bounded refresh
or explicit unavailability, never guessed zero or transaction failure. A claim
can succeed and then accrue more rewards; zero balance is not a success proof.

Verify immutable artwork traits/catalogue counts and duplicates, every evolution
path, preloading/memory/image fallback, confirmed LP-only transition/audio timing,
no unrelated-card updates, metadata root/URI construction, ERC4906 hashed IDs,
IPFS bundle/manifest/self-contained resources, immutable publication/retrieval
and marketplace cache limits. Preserve approved textures and known fixtures.
Static/synthetic tests are not visual/browser/marketplace acceptance.

### I. Complete journeys and measured latency

Trace these journeys across components before closing a function/module review:

1. Actual mint product versus direct demo mint; pending reveal, ordered draw,
   activation availability, marketplace transfer and inherited accrued rights.
2. ETH/ZZZ activation/growth: exact token units/USD basis, insufficient/sufficient
   allowance, exact approval, fresh review after approval/price or policy change,
   rejected second step, rollback and confirmed marginal-LP reconciliation.
3. Mixed LP/royalty claim: owner/units, source balances/deferred currencies,
   royalty synchronization, conversion, later new receipts, claim ordering and
   generated/claimed/remaining distinction through transfer.
4. Governance terminal exit: partial close, allocation, ready, automatic batches,
   unpaid versus paid ETH/ZZZ, transferred NFT, rejecting escrow/receiver,
   operator retry and owner fallback; continued royalties/old rewards.
5. Account/provider/chain change, soft refresh or competing tab during review,
   wallet prompt, approval, hashless intent, pending and confirmed reconciliation;
   old async responses must not mutate a newer session or lose recovery.
6. Concurrent users/NFTs: independent work within budgets, one contribution's
   artwork only after canonical LP proof, claim without artwork transition,
   no duplicate same-account submission or shared mutable user state.
7. Pre-exit whole-collection handoff/abort and multi-hop late funding/history;
   provider/token/host failure at each intermediate durable step.
8. Setup/configuration/incident response: source/pool/feed/range changes,
   pause/parking, role and host/key rotation, backup restoration and restart
   with old pending work and correctly versioned downstream consumers.

For each stage identify source trace, existing pinned evidence, new narrow test,
actual browser observation or external blocker. Do not rerun unchanged journeys
or submit public funds to fill a matrix. Establish critical-path calls, bounded
complexity and cancellation first; distinguish wallet delay, inclusion/finality,
API/indexer lag, data availability and image/audio readiness. Report measured
local timings as local only, with workload/config; do not invent production
percentiles or100-user capacity. Optional art/audio/earnings/price failures must
not erase healthy independent state; mandatory lifecycle/binding failure must
still fail closed. Never parallelize around quotas or weaken canonical checks.
Track snapshot/indexer/pending age, observation reset churn, reserve/delivery
backlog and gas economics symbolically before proposing load tests. Preserve
deliberate extra safety reads, including conversion's final post-quote head check.

### J. Delivery pipeline, supply chain and maintainability

Audit release-review packages as operator inputs: current templates must match
the frozen source/profile while immutable historical packages retain explicit
versioned verification. Existing intentional exclusions are not bugs by default.
Apply official current compiler advisories to actual settings and generated/
inherited code; AST predicate absence is not a lowering or vulnerability proof.

Audit all build/install/deployment/rehearsal/runner scripts and CI, normal
EIP170/EIP3860/constructor limits, compiler/dependency/action/lockfile pins,
generated ABI/reference/artifact provenance, secrets/FFI/broadcast boundaries,
actual selected test inventories, failure/skip/exit propagation, time/resource
bounds and artifact retention. Distinguish dedicated keeper selection from full
discovery and current fork harness from historical dependency fixtures; never
overwrite preserved dirty drafts. Do not run broad unchanged campaigns to fix
a selection/reporting defect that can be verified narrowly.

Remove demonstrably unused dangerous/contradictory current behavior only after
checking every consumer and historical need. Prefer small typed shared helpers
and clear invariants; do not split modules, rename public interfaces, widen
gas/size gates or add generic configuration just to make code look cleaner.

## 4. Execution, evidence and completion

Maintain a feature/operation/function/domain coverage ledger with source pins,
actual depth and one of: traced/reviewed, fresh targeted verification, exact
unchanged evidence, pending/unreviewed with reason, externally blocked, or
explicitly excluded with reason. Pending is not a completed audit disposition.
Refresh the current742 ABI entries (696functions,33constructors,13receivers)
from the existing exact-match compiler AST/reference, separating generated
getters, inherited bodies and distinct hand-written extents. This is navigation,
not742new tests or a verdict. For every manually reviewed body retain source
identity, review cases and reasoning; inherited/secondary-CLI review must not
remain hidden behind a module-level pass. Reconcile the historical494pending
individual-body gap explicitly rather than relabelling it complete.
Inventory private/internal helpers, modifiers, overrides and libraries separately
from external ABI entries; include reachable inherited dispatch and generated
getters' binding/storage semantics. Unreferenced installed package code is not
automatically part of executable project behavior. Reconcile122output positions
currently without dedicated notes and nested tuple semantics: inspect source/
existing purpose notes, add explanations only when established, otherwise record
the precise gap rather than guessing or treating a complete ABI as complete docs.
Every inventory entry must have a disposition; do not call an inventory itself
an audit or claim every function newly executed. Prioritize new high-impact
cross-component risks, then availability/reporting/efficiency and documentation.

For a finding record source/version, reproducible preconditions, expected versus
actual result, reachability/attacker power, financial/liveness impact, chosen fix
and regression/cost tradeoff. Use minimal negative-before/positive-after evidence
where useful; repair weak/vacuous fixtures first and retain failed attempts.
Separate confirmed bug, defense-in-depth, accepted trust, product gap, speculative
future consumer and external qualification. Never invent a finding to justify
work or turn a known unqualified feature into production-ready by documentation.

Implement justified source repairs autonomously within scope and review their
interactions again. Coordinate edits across agents. Consequential unresolved
policy/provider/authority choices need concrete alternatives; continue independent
work. A missing external service or operating permission does not justify
silently relaxing its acceptance condition or abandoning all other improvements.

Run useful new/affected checks only. Reuse prior Solidity/dependency/build or
unchanged backend evidence only at exact pins and recorded scope. Count distinct
methods only with their child/library/dependency/consumer scope intact. Count
methods once across overlap; distinguish cases/subtests/static rows, mocks,
actual dependency execution, skipped methods and failed CLI/build attempts.
Do not run actual funded, remote-host, marketplace or production operations.
Prepare reviewable patches where a filesystem or explicit scope boundary needs
approval; explain the precise blocker rather than bypassing it.

Update the sole task ledger/generated Todo, feature/evidence reference, roadmap,
release record, operator/specialist guides, callable reference when behavior/ABI
requires it, repository context and environment map where affected. Replace
stale current instructions, preserve historical reports and stable task IDs.
Website source/build/publication is separate from deployment; any permitted
frontend fix must retain signer/environment and preserved-data boundaries.

Finish with the twice-reviewed final prompt, understanding/knowledge/coverage
records, implemented repairs, fresh/reused verification, unverified/blocked
areas and prioritized next decisions. Publish only the reviewed allowlist on
main under the repository workflow and verify exact local/remote heads; no Git
publication implies a site/service/contract rollout. Keep production NOT APPROVED
until actual release gates and independent audit/remediation are evidenced.
