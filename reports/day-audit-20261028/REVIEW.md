# Paris28October change audit

Internal source/documentation review through implementation`b61aecb`.
**Production NOT APPROVED.** [Verification](VERIFICATION.md) explains reused
evidence and limits. This is not an independent audit or attack-profit campaign.

## Exact scope

Five reachable commits have committer dates28October2026 in Europe/Paris, after
base`422deaf7d942533a2e51772b6b1da0282e10147d` (27October23:58):

| Commit | Change reviewed |
| --- | --- |
| `2b9e069` | Manual rebalance authority, signer coordination and operator guidance |
| `1cabb85` | Bounded atomic LP routing, entrant-only budgets and exact settlement |
| `ae6dcc4` | Keeper safeguard inventory and remaining trust boundaries |
| `bf94b03` | Canonical receipt-based principal retry/fairness and guidance |
| `b61aecb` | Fee-adjusted extra-loss floor and versioned backend observations |

[Scope and current source hashes](scope.json) distinguish these changes from the
four pre-existing dirty files and unrelated untracked artifacts, all preserved.
The later user decision selects15minutes initially for a configurable rebalance
confirmation buffer, but its evidence method remains unanswered. No buffer code
was written, and40%trigger/passive-position discussion remains unimplemented.

## Findings and corrections

| ID / severity | Finding | Resolution / remaining boundary |
| --- | --- | --- |
| D28-01 / low, documentation | Current guides mixed the fresh accounting4/custody3/V5 candidate with historical schema5/accounting3 tooling, Position3 and external-custodian wording. | README navigation, preflight scope, feature link, security audit plan, current context and Todo now distinguish old tooling from the blocked fresh release. No schema relabel or ready-gate bypass. Removed stale current custodian/bridge instructions; original reports remain unchanged. |
| D28-02 / low, operating liveness | Blocked keeper example max_gas_limit2500000 is below earlier cold balance-only fixture measurements2590680(one venue)/5963090(four), before full operation and keeper25%padding. | Operator/operations/Todo explicitly mark it unqualified. No automatic gas-cap increase, service change or assertion that these old fixtures qualify current target-chain gas. Qualify exact catalog/depth/operations and budgets before rollout. |
| D28-03 / low, observability wording | Quality1 API reports owner/revision, but keeper only validates/stores observations in memory; current health/logs do not export them. | Corrected the owning guide/safeguards/operator instructions. Anchored external telemetry and paired writer/checker operating qualification remain open; no stale unanchored health field added. |
| D28-04 / low, decision tracking | Earlier current context grouped all persistence ideas with unselected brainstorming despite the later15-minute buffer request. | Dedicated stable Todo task plus policy/operator/roadmap/context records now mark the requirement requested and method unresolved, not implemented. No invented timer setter or continuous-history claim. |

No additional confirmed financial-accounting bug was identified in the scoped
source review. That is a bounded internal finding, not proof of absence of bugs,
profitable surrounding trades or future economic loss.

## Code and cross-layer review

Eight production source files changed during the day: Balancer, Manager,
Strategy, Vault, Budget, Registry, Pricing(comment only) and shared interface.
Reviewed actual installed v4 fee composition and net-input rounding, conservative
output floors, quote rollback/callback authentication, bounded route search,
quote-to-output/post-price matching, exact prefund/native accounting, entrant
isolation and physical-LP-only marginal deployment. Registry/quality monotonic
revisions detect those settings changed and restored during callbacks.
Existing gross/caller/aggregate controls remain binding; fee accounting does
not exempt known fees from total loss budgets.

Reviewed keeper retry receipt clocks/job rotation and the six changed current
Python modules against exact evidence pins: monitor/principal, activation/config/
trace and LP observer. Same-block capability/owner/runtime reads and historical0
branches remain explicit. Saved pending work retains priority; router failure
does not silently authorize a new action. Repeated full router observations per
bucket are a possible efficiency improvement; retaining fresh pre-signing checks
is necessary, and no caching behavior changed in this audit.

No custody destination,80/10/5/5 allocation, royalty weighting, claim/transfer
rights or ordinary outside-only/manual-width eligibility was changed by the
fee-quality work. This documentation audit changes no production code.

## Limits requiring further work

- Strategy layout is fresh-only. Historical immutable deployments/journals cannot
  acquire it from config edits. Manager initcode has54bytes headroom; future
  changes require fresh normal gates. Actual release URI/calldata/gas is open.
- Bounded solver search can skip a usable venue or miss a better size. Per-quote
  work caps and the blocked example do not establish economical/maximal operation.
- Entrant isolation leaves incumbent idle attributed. If the whole-bucket idle
  ceiling fails, guarded maintenance may be needed first; no sweep is available.
- Full Strategy target context adds direct-swap liveness dependencies near extreme
  TickMath bounds. Extra1% is oracle-relative and includes spread/rounding/source
  uncertainty. Separate converters retain their all-in controls; buybacks do not
  automatically use the LP best-venue solver.
- Keeper timing and ordinary external trading remain manipulable within permitted
  tolerances. No live independent price pair, protected ordering or profitability
  immunity is qualified. Jitter and averages are not uninterrupted-persistence
  proof. The requested15-minute buffer remains unimplemented pending method choice.
- Actual feeds/routes/VRF/authorities/OpenSea, current-profile preflight/poplint,
  service recovery/monitoring, metadata hosting and independent audit/remediation
  remain open. No public transaction, deployment, service/site or journal change.

Use [the operator manual](../../docs/OPERATOR_MANUAL.md),
[buffer decision](../../docs/LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer)
and [sole Todo](../../TODO.md), not historical test counts as launch approval.
