# PoPL current project context

Reviewed2026-10-31. [Instructions](AGENTS.md), [README](README.md),
[sole Todo](TODO.md) and [operator manual](docs/OPERATOR_MANUAL.md) are the starting
points. This is a current snapshot, not a timeline or global personal memory.

## Current local implementation

Fresh accounting6/portfolio2/maintenance3/confirmation3/compound4/custody4/
emergency2/LP-routing2; pricing2/Entry-routing2/governance2/fee1 retained.
ProtocolPolicy1 and reviewedEntry2 add new explicit policy interfaces.
Read [profile](docs/POSITION_V6.md), [plan](docs/OPTIONAL_PORTFOLIO_IMPLEMENTATION.md),
[current review](reports/adaptable-policy-20261031/REVIEW.md) and
[verification](reports/adaptable-policy-20261031/VERIFICATION.md).

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
object gates at normal-final-0a0cac9f06, unchanged compiler/settings. Source-scoped
runtime and backend checks are recorded in the new report; older50-source/42-gate/
463-static evidence is historical and does not verify these changes. No full-suite,
public CI, market/provider/host qualification or independent approval is implied.
The new callable reference/operator procedures must match source6, not old profiles.

## What remains

Production NOT APPROVED. Actual dual feeds/routes/VRF/authorities/OpenSea,
accounting6 website/services, target gas/market economics, operating recovery,
metadata hosting and independent audit/remediation remain open.60/40 is an
approved tradeoff, not an optimized/proven profitable strategy. Private submission
and manipulation immunity are not claimed. Exact deployment sizes are source-bound;
Current measured Vault635/Budget237/Migration20 runtime margins supersede old14/37/59-byte claims only at the new exact source closure.

## Boundaries and preservation

Main only. Determine source-publication status from exact local/remote Git heads; no deployment/service/site/Anvil/signer/journal/heartbeat change.
Public signing remains disabled, DEPLOYMENT null. Popldemo simulation and poplint
read/unsigned site are separate. Served current3 website and historical Anvil8902
must not be relabelled accounting6. New API reads/preparation support fresh6;
fresh inventory schema8 has21helpers; historical schema7/6 remain explicit inspection paths.

Four unrelated dirty tracked files remain untouched: reports/source-checks.json,
scripts/run-fork-checks.py, tests_python/test_fork_runner.py and
tests_python/test_frontend_history.py. Original hashes/guides and iteration logs
are external under the directories recorded in [handoff](docs/WORK_HANDOFF.md).
Historical reports retain their bytes, source identities, failures and limits.
