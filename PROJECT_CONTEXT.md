# PoPL current project context

Reviewed2026-11-03. [Instructions](AGENTS.md), [README](README.md),
[sole Todo](TODO.md) and [operator manual](docs/OPERATOR_MANUAL.md) are the starting
points. This is a current snapshot, not a timeline or global personal memory.

## Current source candidate

Fresh accounting6/portfolio2/maintenance3/confirmation3/compound4/custody4/
emergency2/LP-routing2; pricing2/Entry-routing3/governance2/fee1. Source7 uses schema9/20 helpers.
ProtocolPolicy1 and review-policy2 retain captured terms; direct Entry3 removes
whole-input pre-Vault conversion and its child/routes. The seven-field ABI is
distinct from historical Entry2; fixed accounting6/canonical V6 wires remain.
Read [profile](docs/POSITION_V6.md), [plan](docs/OPTIONAL_PORTFOLIO_IMPLEMENTATION.md),
[current Entry review](reports/direct-entry-v3-20261103/REVIEW.md) and
[verification](reports/direct-entry-v3-20261103/VERIFICATION.md).

Default single main; manual optional main>=60% and one residual<=40% of post-cost
principal at replacement. Both physical NFTs remain Vault-owned in the same
native ETH/fixed-ZZZ pool. Default residual width is HALF corresponding main
side(default5000bps), governed1–10000bps of that side; its gap is separately
configurable in positive full tick-spacings(default1).
Weights may drift; mixed/filled residuals remain included. Disabling desired mode
requires a guarded atomic merge, never dropping an existing leg from accounting.

Ordinary trigger85%actual centre-to-boundary distance in ZZZ-in-ETH price space,
physical and independent reference same side;600-second sampled window, source
checks240, strict maxgap300, then fresh durable60–300-second service jitter.
Hard initial12hours preserved. Raw checks can happen during cooldown; paid
enrollment starts near eligibility, avoiding hours of redundant observation writes.
Manual geometry changes are a distinct cooldown-gated exception. Sampled checks
are not uninterrupted evidence or MEV protection.

Fixed typed LP child and read-only math child separate execution for normal
bytecode limits. Vault approves individual LP IDs, not all NFTs. Main amounts are
physical; portfolio amounts aggregate both actual ranges. Stable confirmation
fingerprint excludes L; parking/emergency execution fingerprint includes L.
Every ordinary replacement verifies physically active main ticks before/after
mint callbacks; hybrid mode additionally proves the configured main floor(default60%,
governed6000–9999bps).
Initial activation/growth and explicit emergency retain their separate policies.

Contributions checkpoint incumbents, spend only entrant budgets, increase main
only, prove marginal LP and issue shares from aggregate NAV. They never recenter
or reset rebalance timing. Normal compound waits in keeper source for in-range
main/no pending geometry. Both legs harvest together, then apply80/10/5/5 once per
asset. Hourly harvest, claims, conversion, compound and burn remain separate.

Both legs close for parking/movement/holder return. CanonicalV6 is a new semantic admission boundary with the retained record
shape; parked export/import still requires no live residual. Source-pool controls are checked against
the captured source during same-pair movement. No bridge, external custody exit,
issuer token replacement or new input assets exist. Default contribution2%,
conversion1%, maintenance3%; governance ceiling10%, gas separate. USD agreement
3% and separate default1% additional execution loss retain distinct meanings.

## Manual portfolio controls

The [management follow-up](reports/residual-operations-20261031/REVIEW.md) adds
paused governance residual-only close with capability1 on Migration/Vault/Manager/
position child. Same Position/custody wire; both legs harvest first, only residual
burns to same-bucket attributed idle. Main/shares/clock/policy unchanged; no swap,
payout or reserve release. Raw minima, control/physical fingerprint and shared
nonce/epoch guard rollback. Modefalse prevents future residual; modetrue enables
next guarded adjustment. Existing emergency always creates one main using its
range's required ratio, not necessarily50/50. See [operator](docs/OPERATOR_MANUAL.md#portfolio-management-controls).

## Current implementation and verification boundary

[Adaptable policy](docs/ADAPTABLE_POLICY.md) adds bounded future mint/entry terms,
separate entry/maintenance idle, payout/read/sync gas, display thresholds and planned
VRF rotation after every old draw finalizes. Defaults remain unchanged. Main floor
can rise from60% to9999bps and gap can increase within actual geometry; lowering
below60% is not approved. Buyback maximum is separately adjustable with review.
New mint binds sale+VRF fingerprint, Entry2 captures entry terms, maintenance
captures its own policy. Restore operations advance revisions rather than revive
old reviews. Cosmetic/gas/mint changes do not invalidate unrelated LP samples.

Current compiler closure:52 production source files/31 dependencies,43 normal
object gates at normal-final-a8e7dc7cc5, unchanged compiler/settings. The
[LP lifecycle review](reports/lp-lifecycle-audit-20261102/REVIEW.md) repairs
single/hybrid ordinary quote ranking using actual stored post-swap ticks.
The no-swap baseline must be active; final pre/post-mint checks remain. Initial/
growth and explicit emergency policies remain separate. Only Balancer/Manager
production sources changed; exact runtimes/constructor pins must be refreshed
for a reviewed fresh deployment, never relabelled on existing services/journals.

The [verification](reports/lp-lifecycle-audit-20261102/VERIFICATION.md) records65
distinct successful selected EVM methods across stages,5 backend methods,43 normal
gates and475 detector records with407 exact unchanged-context reuse/68 current
reviews. Original failures, two corrected fixture expectations and their narrow
reruns are retained. This is not a fresh full suite, clean static run, public CI,
market/provider/host acceptance or independent approval. Callable reference:
37contracts/826functions/37constructors/14receivers, zero recorded gaps.

Harvest geometry diagnostics compare Manager/child getters to the same packed
PosM source, not independent stored ledgers. Report
geometry_sources_independent:false, preserve custody/shape/coherence checks and
price-outage availability. The new review corrects prior ten-report independence
claims without rewriting that historical evidence. Lifetime history scaling,
residual feasibility/bounded-search qualification and actual source6 rollout
remain open.

The [multi-day portfolio study](reports/portfolio-long-horizon-20261102/REVIEW.md)
adds four scoped journeys across recorded stages; three final methods pass after
an explicit fixture minimum correction, one unchanged successful method is reused.
Six virtual days exercise repeated mode cycles, main-only ETH/ZZZ Entry/growth,
harvest, compound, claims and both same-block orderings. Production52/dependency31
pins remain unchanged; reuse prior43 gates/static scope. Residual geometry is
nested inside main: an active residual implies active main; both outside means
the same asset side. This is not a live keeper/browser/load/profit qualification.

## What remains

Direct Entry3 verification records28 distinct selected EVM successes across
explicit stages and314 Python successes across two selected scopes, not a full
suite. Fresh52/31-source43normal gates and471static records are bound to the
new compiler output; callable reference37/818/37/13 has no note gaps. Entry
runtime18581→9863; Registry creation42736→22526. Vault635/Budget237/Migration20
headroom remains. Failure/empty-selection history and19unchanged-body reuse
are explicit in reports/direct-entry-v3-20261103/VERIFICATION.md. Source7
website/services and actual dependency/release qualification remain open.


[Direct Entry3](reports/direct-entry-v3-20261103/REVIEW.md) implements the user's
approved removal with explicit schema9/20-helper inventory and routing3 API
calldata/config/trace validation. Review-policy2/pricing2 and all financial/owner
guards remain; Vault balancing and separate LP/royalty conversion stay. Match
fresh runtime/configuration before any authorized rollout. Existing sites,
Anvil/journals, signing restrictions and historical schema8 are unchanged.

[Current contract/LP audit](reports/smart-contract-lp-audit-20261103/REVIEW.md)
reviews795 project bodies in component context and six current compiler
disclosures. Two new actual-core journeys verify infeasible residual-gap
rollback/recovery and USD-outage harvest/partial claims/raw close/later merge.
No production Solidity changed or new exploitable defect was established;
reuse exact52/31-source43-gate/475-static scope. The later direct Entry3 implementation resolves the removal decision; real qualification remains open.

[Current consolidation](reports/consolidation-20261103/REVIEW.md) reconciles the
three latest audits without changing contract policy. RPC clients snapshot their
reviewed endpoints; metered eth_call cannot delegate around count/expiry checks.
Strict maintenance validators no longer have a permissive mode; constructor-only
paid-intent deferral remains explicit. Oversized override IDs fail early. Prior
reports retain original source scopes; real service/market qualification is open.

[Action resilience](reports/action-resilience-audit-20261102/REVIEW.md)
fixes RPC body progress budgets and rejects unknown maintenance names before new
work. Validated saved pending intents recover before invalid new maintenance
values halt future work; receipt/nonce/spend/deployment identity stays intact.
176 distinct selected Python methods pass across recorded stages, with one Unix
permission skip and original negative/driver/fixture failures retained. No
Solidity/policy change: reuse prior52/31-source43-gate/static scope. Body progress
is not DNS/header preemption; API worker containment and keeper watchdog/provider
operating acceptance remain separate. The action matrix distinguishes confirmed
execution from API/price unavailability and event labels from actual post-state.

Production NOT APPROVED. Actual dual feeds/routes/VRF/authorities/OpenSea,
accounting6 website/services, target gas/market economics, operating recovery,
metadata hosting and independent audit/remediation remain open.60/40 is an
approved tradeoff, not an optimized/proven profitable strategy. Private submission
and manipulation immunity are not claimed. Exact deployment sizes are source-bound;
Current measured Balancer360/Vault635/Budget237/Migration20 runtime margins supersede old14/37/59-byte claims only at the new exact source closure.

## Boundaries and preservation

Main only. Determine source-publication status from exact local/remote Git heads; no deployment/service/site/Anvil/signer/journal/heartbeat change.
Public signing remains disabled, DEPLOYMENT null. Popldemo simulation and poplint
read/unsigned site are separate. Served current3 website and historical Anvil8902
must not be relabelled accounting6. New API reads/preparation support fresh6;
fresh inventory schema9 has20helpers; historical schema8/7/6 remain explicit inspection paths.

Four unrelated dirty tracked files remain untouched: reports/source-checks.json,
scripts/run-fork-checks.py, tests_python/test_fork_runner.py and
tests_python/test_frontend_history.py. Original hashes/guides and iteration logs
are external under the directories recorded in [handoff](docs/WORK_HANDOFF.md).
Historical reports retain their bytes, source identities, failures and limits.
