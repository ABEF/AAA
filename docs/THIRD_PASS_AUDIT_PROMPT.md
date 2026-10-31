# Whole-project PoPL audit and improvement prompt

This is the canonical whole-project brief at its stable filename. The
[current campaign](../reports/comprehensive-popl-20261029/REVIEW.md) records
understanding, two sequential prompt critiques, implementation and evidence.
Earlier briefs/reports retain their exact Git/source scope. Do not restore old
heads or reinterpret old deployments to match this prompt.

## Objective

Understand, critically review and improve the entire PoPL project: product rules,
contracts, economics, every user/operator operation, data services, keeper,
website and wallet boundaries, artwork/metadata, deployment/build/test pipeline,
dependencies, observability, recovery, documentation and release decisions.
Seek concrete improvements to correctness, security, availability, usability,
latency, efficiency and maintainability. Do not stop after a plan or report if
justified repairs can be implemented and verified within authorization.

Execution baseline: contract `main` at
`93ceee1b78ad1e8532932961b934177b558f13c3`, website `main` at
`997f8c3524ea75d613dbb752f67b33a69fe7992f`, with explicitly preserved unrelated
dirty files and local-only drafts. Before any future reuse, discover the actual
heads, dirty state, dependency/toolchain identities, source hashes and deployed
profiles. These are source baselines, not installed-service identities.

The [completed historical reconciliation](../reports/historical-reconciliation-completion-20261029/REVIEW.md)
already accounts for352original report narratives/91guides in235overlapping
material groups. Use its exact dispositions and pins as input, not as235new
bugs/tests or evidence all risks are resolved. Do not reread/retest unchanged
reports just to reproduce that count. Revisit relevant evidence when a current
trace, changed implementation or unsupported claim makes it necessary.

Audit the entire current project, not only recent diffs. Save original dirty
documentation before replacement. Preserve historical report bytes, original
failures and old deployment/journal compatibility. Prior implementation facts
must be rechecked at actual source pins; changed consumers can invalidate reuse
even when one producer file did not change.

## Execution amendment: approved terminal reserve recovery

The user approved restoring a fully validated ETH/fixed-ZZZ swap venue after
collective exit. Implement only at Migration Ready(3), with deposits disabled;
Ready means all principal allocated, not necessarily all payouts delivered.
Keep terminal principal locks, exact holder backing, native dependency checks,
ordinary keeper/buyback authority and all financial controls. Admission neither
moves funds nor enables new LP. Qualify the new source with focused positive and
negative tests and normal production compilation; distinguish synthetic native
runtime test seams from actual mainnet venue admission.

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

Re-establish these against actual source and current repo instructions before
execution. [Accounting6](POSITION_V6.md), [policy](ADAPTABLE_POLICY.md), the sole
Todo and operator manual take precedence over old campaign assumptions.

- Fresh accounting6/ProtocolPolicy1/Portfolio2/governance2/fee1/custody4/pricing2/
  routing2/reviewedEntry2, LP-routing2/quality1/maintenance3/confirmation3/
  compound4/emergency2 and same-chain ADAPTABLE_POLICY_V6. Preserve historical
  codecs/Anvil/journals rather than silently migrating or relabelling them.
- One fixed ZZZ and native ETH are contribution/LP inputs. Future action minima
  default100USD activation/5USD growth, governed>=1USD with growth<=activation;
  stronger pool minima remain. Intended cumulative per-NFT maxPositionUSD is1mUSD.
  One contribution destination and at most four permanent historical/reserved
  custody buckets; no third input, replaceable ZZZ, creator inbox, bridge,
  arbitrary executor/sweep or external custody exit.
- One default main plus at most one optional residual in the same pool, both
  Vault-owned. Sum actual amounts/NAV, not liquidity across different ticks.
  Per-pool main floor6000–9999bps(default6000), complementary residual maximum,
  governed side fraction(default5000bps) and positive tick-spacing gap(default1).
  Ratios apply at guarded replacement, not continuously. Disabling records a
  desired merge; a live residual remains valued/harvested until safely closed.
- Contributions checkpoint incumbents, spend only entrant funds, increase the
  existing main, prove marginal deployed LP, then issue shares from net added
  NAV. No recenter/rebalance-clock reset or incumbent idle/residual subsidy.
- At most1000ERC721 NFTs; exact600/300/100 rarity quotas and fixed prepared
  artwork draw. Revealed rarity/palette/pattern and art root are immutable.
  Activated eligibility is independent of falling NAV. Governed positive
  enhanced/singularity thresholds change display only(default1000/10000USD).
  Terminal visual stage4 differs from PositionStatus.Exited5.
- Actual harvested fees allocate80/10/5/5: individual/equal activated collective/
  compound/fixed-ZZZ burn. Dust/fractions and incumbent checkpoints remain.
  Separate100% received eligible royalties use rarity1/2/3; ERC2981 requests5%
  without universal enforcement. Current owners inherit unclaimed rights.
  Earnings, claimable, paid and returned principal are distinct.
- Two independent reviewed USD sources, selected3% agreement, no spot/peg/missing
  fallback. Contribution2%/conversion1%/maintenance3% defaults, ceilings10%, gas
  separate. Additional loss after known directional fees defaults1%, governed
 0–10%. Caller/venue/raw-output floors and dual-source agreement are separate.
- Separate captured entry/maintenance idle caps default5%, governed0–40%.
  Changing idle never waives marginal deployed-LP or retained-value floors.
  Source/payout/optional-currency budgets are bounded100k–1m, not provider/gas
  qualification. Pyth's optional adapter has its own immutable300k inner cap.
- Ordinary trigger85% of actual centre-to-boundary ZZZ-in-ETH price distance;
  physical pool and independent reference must corroborate the same side.
 600second sampled window,240second source checks, strict300second max gap,
  then durable fresh60–300second service jitter; initial hard12hours remains.
  Raw cooldown checks and near-eligibility paid enrollment are implemented.
  Reset on observed return/side/fault/identity/relevant-policy change. This is
  sampled evidence, not uninterrupted history or MEV immunity.
- Deliberate governed geometry changes retain their cooldown exception. Manual
  ranges may extend below100% within Registry/tick constraints; optional automatic
  two-width selection remains distinct and disabled under selected protection.
  Separate compound cadence; worker waits for in-range main below adjustment
  threshold/no pending geometry. Independent hourly harvest and pending-first
  nonce/receipt recovery must not be blocked by optional jobs.
- Paused governance emergency2 is a separate exact manifest, never ordinary
  keeper fallback. Optional financial/timing checks may be bypassed deliberately,
  but exact assets/custody/settlement/shares/reserves/lifecycle stay structural.
  Accepted governance trust can permit near-total economic loss.
- ProtocolPolicy is fixed noncustodial code with bounded future settings.
  Mint binds sale+VRF fingerprint; Entry2 binds exact entry policy; maintenance
  captures its own values. Revisions prevent change-and-restore stale review
  revival. Cosmetic/gas/sale changes must not reset unrelated LP samples.
- Planned VRF provider/subscription/lane/payment rotation requires every old draw
  finalized; no pending retarget/reroll/admin traits. New requests pin runtime;
  original-address callbacks can drain pending work. Provider upgrade/proof/
  funding recovery remains a real qualification requirement.
- One human operator controls direct governance, without timelock/committee;
  automated keeper and guardian capabilities remain distinct. Reviewed successor
  and dependency code remain governance trust. Future mint recipient proposes/
  accepts without moving old payments or granting management powers.
- Normal holders cannot redeem principal. Paused governance can permanently stop
  LP, close both legs, allocate principal+compound by shares and pay current
  owners in isolated bounded batches. Old rewards/future royalties/transfers
  survive; no restart or post-exit canonical replacement. Before exit, compatible
  same-pair moves/parking and complete same-chain handoff remain.
- Production mint is intended for OpenSea; reviewed direct mint is not compatible
  primary-drop integration. Default gross0.05ETH is future-governed; actual
  platform fee comes from gross buyer price, with recipient net and gas separate.
  No live provider/authority/product support may be inferred from mocks.
- Main only; preserve unrelated dirty files, original reports, Anvil8902/NFTs/LP/
  balances/journals/dist and paused monitoring. Popldemo stays simulation; served
  poplint remains current3, not qualified source6. Public DEPLOYMENT stays null,
  signing Anvil-only. Source publication is separate from deployment/rollout.
- This audit authorizes no public/funded transaction, deployment, seal, server or
  service/site change, signing extension or monitor restart. Never print/log/
  commit secrets. Respect website checkout write boundaries; a reviewed isolated
  patch is not permission to modify shared signers or serving directories.
  Continue independently authorized source/backend/docs improvements; optional
  public RPC probes need their own authorized read scope.

## 3. Whole-project review matrix

Review every applicable row for normal, boundary, adversarial, delayed, concurrent,
callback, dependency-fault and recovery behavior. Trace complete journeys across
components; do not assume local correctness composes into system correctness.
Review unused/dead/obsolete behavior against current requirements, preserving
needed historical receipt decoders. Separate refactor from financial/policy change.

### Review depth and knowledge boundaries

For every feature reason globally about its purpose/owner/lifetime and locally
about each input, branch, dependency, side effect and recovery boundary. Include
the feature's interactions with unchanged components and operator actions.
Use the attached35-point checklist as a coverage taxonomy; mark each applicable,
adapted or not applicable with reasons. Do not add AI inference, consensus-node,
generic account/password recovery, integrated bridges or mandatory committee
workflows that this project does not implement. Public wallet addresses are not
private authenticated tenants, and an unsigned review is not transaction authority.

Apply current primary guidance to the pinned technology rather than upgrading
the toolchain to match an article. Read installed Solidity0.8.26/Cancun/via-IR,
OpenZeppelin5.4.0, v4-core1.0.2/periphery1.0.3/Permit2 and Python3.11+ behavior.
Map relevant web boundaries contextually to OWASP ASVS5.0.0; use SSDF1.1 for
source/artifact protection and release response, not as a claimed certification.
Distinguish documented behavior, inspected code, executed results, inference,
accepted trust and unavailable external facts. Never promise exhaustive absence
of bugs, uninterrupted execution or production capacity from finite local work.

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

Audit evidence admission as part of the execution trust boundary: fresh exclusive
output before analyzer/journey effects, strict unambiguous report/review parsing,
no overwritten old evidence, retained failed/interrupted results and exact source/
tool/dependency identity. An analyzer finding exit differs from an execution
failure; source-mismatched historical triage must not become a current pass.

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

### K. Management, longevity and loss of dependencies

Trace who pays/funds gas, randomness, RPC/indexing/storage, hosting, archival
history and metadata availability over time; contract reserves cannot be assumed
to fund operating costs. Review operator/key loss, key rotation, unavailable
guardian/governance, immutable dead dependencies, lost original VRF results,
long inactivity, supply below1000, dead/rejecting holders, escrow/beneficial owner
ambiguity, stablecoin royalty depeg/freeze and permanent venue/token failure.
State what remains possible, what requires governance, what needs compatible
pre-exit replacement and what no current mechanism can recover. Preserve raw
liability and paid truth; do not propose a sweep to make apparent dust disappear.

Evaluate lifetime aliases, lineage/events, quarantine/fractions, retries, disk and
logs—not only a single bounded call. Assess observability for backing/freshness,
pending age, sample churn, backlog and missing operating funding. Give the sole
operator exact diagnosis/stop/repair/resume procedures and irreversible limits.
Avoid new roles, infrastructure or automatic policy changes without a concrete
failure/benefit. Proposed business/governance changes remain visible decisions.

## 4. Execution, evidence and completion

Maintain a feature/operation/function/domain coverage ledger with source pins,
actual depth and one of: traced/reviewed, fresh targeted verification, exact
unchanged evidence, pending/unreviewed with reason, externally blocked, or
explicitly excluded with reason. Pending is not a completed audit disposition.
Refresh actual ABI/function/helper/receiver inventories from the source-bound
reference and exact compiler/dependency artifacts. The baseline reference has
696functions,33constructors and13receivers; verify these rather than assuming
they remain current. Separate generated getters, inherited dispatch and distinct
handwritten functions/internal helpers/modifiers. Reuse the existing complete
handwritten-body review only at matching source pins and preserved scope; it is
not new execution. The earlier494body gap and122output-note gap were addressed
by later source work: do not reopen them merely because an old prompt called them
pending. Inspect current annotations/tuple meanings and report any actual new
gap. Include reachable dependency bodies and generated storage semantics without
claiming that every installed package is executable application scope.
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

Completion requires a disposition for every feature/operation in the current
inventory, not a universal pass. Record fresh versus exact reused versus inspected
versus externally blocked evidence; justify every exclusion. Implement verified
repairs, preserve unresolved consequential decisions and show the next safe
operator/engineering action. Reconcile the whole system after changes and retain
negative/partial evidence without double-counting repeated verification methods.
