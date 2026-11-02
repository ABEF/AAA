# Five-audit consolidation and remaining repairs

Reviewed November 2, 2026, Europe/Paris, starting at main `c6fb190`.
**Production remains NOT APPROVED.** This is a reconciliation of five technical
reviews against the current accounting6 source, not five new full audits or a
claim that all historical findings are closed. [Verification](VERIFICATION.md)
separates newly executed checks from reused source-bound evidence.

## Scope and disposition

The five latest substantive technical review families in the report index are:

| Review | What remains applicable now |
| --- | --- |
| [November 2 improvement audit](../improvement-audit-20261102/REVIEW.md) | Shared custody proofs, current buyback-cap admission, policy diagnostics and verification/publication corrections remain implemented. This consolidation finds a further health-profile downgrade gap and repairs it below. |
| [October 31 source/operating follow-up](../today-audit-20261031/REVIEW.md) | Published reader closure, same-role external dependency sharing in lineage, current fixtures, recovery labels and current static review remain applicable. Local hashes are not live-service attestation. |
| [October 31 adaptable-policy review](../adaptable-policy-20261031/REVIEW.md) | ProtocolPolicy1/Portfolio2, scoped callback-safe reviews, future-only controls, planned drained VRF rotation and canonicalV6 checks remain implemented. Provider, market and operating qualification remain open. |
| [October 31 manual-operation audit](../manual-operations-20261031/REVIEW.md) | The single Operator manual, authority corrections, ordered management inputs and offline review helper remain useful. Its source5 callable/size/static counts do not describe the current source6 candidate. |
| [October 31 source/change audit](../day-audit-20261031/REVIEW.md) | Price-outage ownership/raw-claim availability, activation executor binding and final physically active ordinary-main checks remain implemented. Its route-ranking limitation is still open. |

The intervening documentation-only synchronization is excluded from the five
technical campaigns. Original reports, failed attempts and artifact manifests are
preserved. [The disposition matrix](findings.json) maps grouped findings and
limitations to current mechanisms and existing central Todo tasks. Rows are
review groups, not independent vulnerability or test counts. It creates no second
task ledger. Status meanings are `resolved_in_source`,
`superseded_by_current_profile`, `accepted_boundary`, `open_implementation` and
`open_qualification`.

## Repairs made during consolidation

### Health-profile downgrade could hide required evidence — medium, repaired

The read-only health checker does not construct a Keeper. With accounting5/6
still selected, setting both confirmation and execution-quality versions to zero
could skip their evidence checks and accept a matching legacy-shaped healthy
file. The real Keeper already rejects that configuration; this was a diagnostic
false-green path, not a signing or custody bypass.

`keeper/health.py` now checks the supported accounting identity and mandatory
fresh profile before either evidence validator can take a legacy early return.
Accounting5 requires portfolio1/policy0; accounting6 requires portfolio2/policy1;
both require fee1/maintenance3/confirmation3/quality1/routing2 with exact integer
types. Explicit historical profiles retain their existing scope. The check makes
no RPC, constructs no application and changes no journal or transaction.

Three new regression methods reproduce the original defect, malformed and
missing profile tags, ambiguous types, and an actual health-command false-green
result. Relevant existing positive and historical health cases are also checked.
The recovery guide explains the refusal and controlled configuration procedure.
This does not authenticate a host, maliciously rewritten config or live provider.

### Two older tests did not reach their stated scenario — corrected

The telemetry policy-change race fixture failed at unrelated compound eligibility
before gas estimation. Its targeted test now isolates that independently tested
eligibility boundary and proves estimation actually occurred and changed the
policy before the signer was rejected. It does not claim whole-compound coverage.

The delayed-revert fixture moved its receipt timestamp earlier than its preceding
saved checkpoint. The production checkpoint guard correctly rejected it. The
fixture now models a coherent older checkpoint followed by the delayed receipt,
retaining the paid-revert/cooldown assertions. Both failures were reproduced with
the original health implementation; no production checks were weakened.

### Route failure triage is now explicit — implementation gap remains

The Operator manual now explains the conditional workaround for a selected
own-pool quote that would make the replacement main inactive: inspect the full
post-close simulation, review a qualified alternate venue and, if appropriate,
replace the complete automatic execution list. Preserve the active-main guard,
stronger financial floors, pending-first reconciliation and exact pool identity.
The LP destination and independent Entry/conversion/buyback routes do not change.

This is not automatic candidate filtering. A bounded planner may still rank an
unusable route over a viable alternate. A correct implementation must account for
the actual destination tick after withdrawal/swap, exact boundary behavior,
within-venue sizing and both ordinary modes without blocking allowed initial/grow
or explicit emergency semantics. A sqrt-price-only shortcut would not establish
those properties. No partial Solidity fix or unsafe fallback was introduced.
The existing [routing task](../../TODO.md#task-lp-execution-routing) stays open.

## Current findings that must not be called solved

| Area | Current disposition and owner |
| --- | --- |
| Candidate ranking and operating economics | The final active-main guard prevents the invalid ordinary replacement but can cause avoidable reverts. Qualify bounded search, actual post-withdrawal depth, fees, residual geometry and competing flows; implement ordinary candidate viability correctly. [Routing](../../TODO.md#task-lp-execution-routing). |
| Feed disagreement and deployment floors | Two agreeing sources within 3% do not guarantee a contribution passes the separate 2% deployed-LP budget. Conservative upper/lower marks, venue fees, idle and caller floors can legitimately block it. No automatic relaxation. [Pricing](../../docs/PRICE_SECURITY.md). |
| Randomness outage | Pending requests must drain before planned provider rotation or whole-collection handoff; no reroll/administrator-selected traits. This does not block ordinary LP pool movement or terminal holder return. Actual VRF remains unqualified. [Random assignment](../../TODO.md#task-fair-draw). |
| Maximum gas, timing and longevity | The current gas bounds, dynamic deployment arguments, payout/source/royalty batches, full populations, strict sampled cadence/jitter, actual Linux storage/recovery and host/load budgets need real qualification. Reused bytecode limits do not establish this. [Keeper](../../TODO.md#task-keeper-guardrails). |
| Service and website publication | Current source6 differs from served current3 poplint and popldemo simulation. New shared validation adds bounded reads whose real latency is unqualified. Public signing stays disabled and old profiles/journals remain separate. [Environment map](../../docs/SITE_ENVIRONMENTS.md). |
| External dependencies and approvals | Real independent feeds/routes/RPC/VRF, authority addresses, OpenSea primary mint, permanent metadata hosting, operating acceptance and independent audit/remediation remain open in the sole Todo. Coherent mocked reads and importability cannot close them. |

Accepted trust boundaries remain explicit: direct governance can alter reviewed
policies and approve replacements; paused exact emergency operations may bypass
financial guards and lose nearly all principal; runtime hashes do not freeze
upstream proxies or attest running code; strict observations are sampled rather
than continuous price evidence; rejecting receiver contracts and unavailable
external dependencies can delay recovery. These are not fixed by a report or by
labeling a local test successful.

Source5 counts and old fixed allocation prose are superseded by the maintained
source6 guides, not retroactively edited in historical reports. The obsolete WETH
example comment in `ZZZActivationAssets` is not an admitted input or runtime path;
native ETH/fixed ZZZ rules remain authoritative. No cosmetic Solidity edit was
made that would invalidate exact build/static evidence just to change that comment.

## Result and next priority

Implemented historical repairs remain present; the further monitoring defect and
two stale verification cases are corrected. Current guidance, feature reference,
Todo acceptance, roadmap and repository handoff point to this consolidation.
No economic rights, custody guarantees, defaults, roles, deployments, services,
sites, Anvil state, recovery journals, signing capabilities or heartbeat changed.

The next engineering priority from these five reviews is ordinary route-candidate
viability, alongside external service/market qualification. The independent
release audit and exact operating approval remain required. This reconciliation
provides evidence and a current disposition; it does not guarantee absence of
bugs or manipulation.
