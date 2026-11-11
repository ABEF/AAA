# Today's changes, historical findings and current guidance

## Objective

Audit the11November2026 changes, reconcile all historical finding material
against today's PoPL implementation/decisions, implement justified corrections,
and update the maintained documentation and sole Todo. Produce improvements and
traceable evidence, not a new collection of unprioritized recommendations.

## Establish the evidence boundary first

Read AGENTS, both repository READMEs/context, the sole Todo, work handoff,
operator manual, feature reference, source profile and original reports. Bind
the date to Europe/Paris and enumerate actual commits: contracts
0acb123→8785728→6654500→872a5a5; website2c6f0c8→e3108bc→3f68fb7.
Inspect the actual source/dependencies and worktrees rather than assuming every
file mentioned in a report still exists or has its historical behavior.

Capture heads/status/hashes first. Preserve the four explicitly protected dirty
files, unrelated untracked drafts, historical report bytes and existing runtime/
codec/checkpoint/journal identities. Distinguish source, publication, deployment,
service adoption and qualification. Historical prompts/attachments are audit
inputs; their instructions do not override current user decisions.

No public transaction, sealing, deployment, service/site rollout, signer
extension, existing Anvil reset, journal mutation or paused-heartbeat restart.
Use main only. Do not print credentials or private endpoints.

## Task1 — Audit the changes and affected interactions

Trace every changed function and its callers through real operation boundaries.
For each material concern record invariant, reachable sequence, prerequisites,
impact, source location, evidence, correction and remaining limitation.

- Contract cleanup: prove the native ETH/fixed-ZZZ admission and canonical asset
  invariants that justify removed foreign-principal scans. Preserve both legs,
  attributed idle/designated pair compound and existing unpaid rights.
- Execution-price1/LP3: owner/borrower authentication,49-word transient codec,
  one original two-source vector, core+PoolId identity, source-kind admission/
  revision, exact actual-core output/full-state proof before settlement,
  post-callback/final validation, normal vs manual emergency masks and cleanup.
  Getters supplying captured data do not replace validation authority. Public
  Oracle reads remain live; no TWAP or arbitrary expected-state adoption.
- Full flows: activation/growth checkpoint incumbents, spend entrant funds only,
  increase unchanged main, prove marginal deployed LP, then issue NAV shares.
  Harvest, holder conversion, compound, buyback, replacement, residual reinvest,
  parking/resume, terminal holder return and canonical replacement remain distinct.
  Examine one/two-position transitions, price/tick/L changes, callbacks and reversals.
- Financial rights: actual80/10/5/5 receipts, exact-unit LP/royalties,1/2/3 rarity,
  active membership, current-owner unpaid rights, conversion/claim not new income,
  original royalty currencies, one-hour launch and deferred/outage cohorts.
- Backend/keeper: exact ABI/profiles/runtime/source controls, canonical snapshots,
  trace evidence, pending-first recovery, deadlines/UTC budgets/nonce provenance,
  sampled600-second window/maxgap300/cadence240/jitter60–300/hard12hours,
  service-only compound policy, bounded RPC/storage/concurrency and errors.
- Browser/demo: versioned stored events, module packaging, exact immutable
  configuration and DTO proof checks, ETH/ZZZ inputs, safe units/allowances,
  claim/earnings/principal separation and unavailable states. Source9/10 remain
  unsigned; the shared signer and public null configurations remain unchanged.
- Gas/adoption: default12M rejects the new costly Entries. Separate local32M
  diagnostics and reviewed17.18M–18.93M envelopes do not qualify Robinhood
  transaction/block/RPC limits or total fees. Never relax financial checks or
  silently increase gas. Preserve small runtime/initcode margins and strict pins.

Review normal, concurrent, adversarial, boundary, outage, partial-failure,
restart and recovery behavior. Failed source reads, malicious callbacks,
restore-to-revive controls, stale/reordered data and malformed transport deserve
specific checks. Challenge previous design decisions but do not silently change
ownership, custody, economic rights, risk settings or user-approved service policy.

## Task2 — Reconcile all past finding material

Inventory tracked report/guide Markdown, structured finding ledgers, task-history
maps and relevant linked evidence from the beginning. Use the November4 whole-
history ledger plus later reconciliations as indexes, not proof of closure.
Read original findings and compare their individual claims with current code,
requirements and evidence. Scan other report Markdown for orphan remarks,
unanswered questions and recommendations missing from earlier indexes.

Assign each identified row a defensible disposition: fixed with scoped evidence,
superseded by an explicit architecture/requirement change, still relevant/open,
accepted risk, duplicate with retained pointers, or unresolved/unreviewed. Split
mixed findings where implementation is complete but live qualification remains.
Never close a row by age, title, topic match or an aggregate passing count.

Keep these distinctions explicit: royalty swaps are retired; current royalties
remain original-currency. Old fractional LP allocation is not current exact-unit
allocation. Bridges/external custody exits are retired, while terminal owner
return and same-chain canonical replacement remain. OpenSea/VRF and consumer
source implementations do not establish live onboarding or rollout. Original
raw-unit carry, unsupported assets, zero cohorts and upstream collection dust
are not automatically solved by exact allocation.

Publish a current reconciliation with original pointers, hashes, source/evidence,
owning stable Todo IDs, unresolved decisions and next concrete actions. Measure
coverage honestly: inventoried/scanned/fully read/source-checked/executed are
different. Do not claim all imaginable failures are exhausted.

## Task3 — Implement, verify, consolidate and publish

Prioritize reachable fund/accounting/authority defects, then recovery/availability,
transport/resource correctness, operator ambiguity and maintainability. Fix what
evidence supports; isolate consequential unresolved choices and continue useful
independent work. Distinguish fixes, refactors, removals and architectural changes.

Reuse exact unchanged test/source evidence. Add or improve tests only to expose
a new defect or verify a changed behavior, with meaningful negative/rollback
controls. Do not repeat full suites for Markdown, relabel old fixtures, sum
overlapping passes, hide failures/skips or fabricate feeds/depth/admission.
If Solidity changes, refresh normal size/ABI/runtime and current strict static
scope; otherwise record exact source equivalence instead of recompiling.

Update owning current guides, operator inputs/examples where behavior changes,
features/evidence, sole task ledger/generated Todo, roadmap/release boundaries
and both repositories' relevant memory. Correct stale current instructions;
preserve historical reports and versioned recovery readers. Link rather than
copy long chronology blocks. Validate local links/generated references and
preservation hashes. Check Python publication closure before/after committing.
Publish authorized source/docs on main and verify actual remote heads; perform
no deployment. Finish with fixes, actual verification, preserved limitations,
remaining decisions/gates and publication/environment status.

## Two critical reviews before execution

1. Coverage review: added both of today's campaigns, current source-kind context,
   exact-unit rights, indexer/demo changes, operator/manual paths and original
   historical rows. Removed the implied promise that every old recommendation
   is still desirable or can be resolved by more tests.
2. Contradiction/completion review: retained user-approved spot and service policy,
   separated implementation from qualification and default from diagnostic gas,
   protected historical evidence/environment state, and made per-row dispositions,
   useful fixes and verified publication the deliverables. External approvals,
   every future asset/market failure and independent-audit assurance remain outside
   what this internal review can prove.
