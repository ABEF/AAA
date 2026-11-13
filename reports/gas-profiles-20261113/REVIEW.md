# 20M contribution / 24M maintenance qualification

13 November 2026; source baseline `fbe47c330a11ab3370417ae999b31c8ab61fc66d`.
**Controlled execution and software qualification passed. Production adoption
remains blocked by provider, fee and deployment/market qualification.** No global
default, financial guard, production implementation or running configuration changed.

## What is now concrete

The [candidate package](backend/profiles.template.json) specifies20M for explicit
activation policy2 and24M for keeper/manual maintenance policies. The backend
and website configured activation ceilings match exactly. Full20% contribution
and25% keeper/manual padding remain; estimates above their budgets reject rather
than being clipped. Legacy policy1/claim12M behavior stays separate.

New local execution proves $100 activation and $5 growth in both native ETH and
fixed ZZZ. Six complete keeper operations also execute within24M. Each actual
RPC case succeeds both at its selected ceiling and its exact padded estimate,
at a rechecked canonical hash on a new owned32M-block Anvil node. No signed or
submitted transaction is needed. These are actual contract calls and estimates,
not arithmetic applied to the old $1,000 trace.

The [software checks](backend/README.md) cover configuration, consumer equality,
headroom boundaries, fee/balance/day rejection, provider failure and unchanged
pending-record priority. The [operator procedure](../../docs/OPERATOR_MANUAL.md#gas-profiles-20m-24m)
explains distinct files, field types, listener setup, restart, rollback and approvals.

## Actual local RPC results

Every row below uses the actual current owner or an explicitly granted disposable
keeper EOA. The prestate, runtime graph, original setup and later per-slot delta
are authenticated. Gas limits, payloads and actor addresses are not normalized
to make a failing call pass. The exact padded calls also succeed.

| Operation | Profile ceiling | Actual estimate | Required padded gas | Remaining margin |
| --- | ---: | ---: | ---: | ---: |
| ETH activation, $100 |20,000,000|14,748,028|17,697,634 (20%)|2,302,366|
| ETH growth, $5 |20,000,000|13,616,039|16,339,247 (20%)|3,660,753|
| ZZZ activation, $100 |20,000,000|15,082,371|18,098,846 (20%)|1,901,154|
| ZZZ growth, $5 |20,000,000|13,929,079|16,714,895 (20%)|3,285,105|
| Main harvest |24,000,000|728,312|910,390 (25%)|23,089,610|
| Compound |24,000,000|10,987,750|13,734,688 (25%)|10,265,312|
| Ordinary single replacement |24,000,000|13,535,113|16,918,892 (25%)|7,081,108|
| Open optional main + residual |24,000,000|16,473,330|20,591,663 (25%)|3,408,337|
| Harvest both legs |24,000,000|1,083,316|1,354,145 (25%)|22,645,855|
| Next two-leg replacement |24,000,000|16,836,989|21,046,237 (25%)|2,953,763|

[EVM/RPC evidence](evm/REVIEW.md), [exact gas records](evm/GAS.json).
These estimates differ from the earlier Foundry cold-call measurements; do not
label that difference a source regression or a maintenance optimization.

The $100/$5 amounts use controlled USD publications, including $1/ETH, synthetic
external depth and explicit registry/authority/Permit2/VRF seams. They are dollar
unit tests, not real ETH/ZZZ market quotes. The new maintenance cohort starts
from separately funded $1,000 principal. It contains one activated NFT and is
not the maximum collection/royalty/history workload.

## Safeguards and rights retained

All61 production Solidity files are byte-identical to the baseline. Contribution
default3%, conversion1%, maintenance3%, additional execution1%, source agreement3%,
actual marginal deployed-LP proof, entrant-only funding, custody, owner rights,
callback checks and atomic rollback are unchanged. One raw unit below each
requested activation/growth floor rejects with the exact minimum-amount error
and unchanged state. Growth preserves main ID, geometry, rebalance clock and
net-NAV share issuance. No residual funds subsidize it.

Keeper replacement retains the12-hour minimum, independent/physical corroboration,
600-second sampled window and strict300-second gap. Both LP legs remain valued,
harvested and closed/accounted through replacement. Compounding preserves shares
and existing main geometry. Harvesting stays independent. No forced path is used.

The overall gas ceiling is not the on-chain source/solver/payout/royalty-sync
subcall budget and grants no new authority. The keeper's24M setting applies to
all enabled jobs in its configuration; unmeasured jobs still require their exact
simulation and affordability checks. Actual governance Migration/manual C/D
workloads are **not** represented by these keeper calls. Manual24M budget gates
are covered separately with injected inputs, not claimed as live manual admission.

## Actual consumer reconciliation

The four new contribution captures also pass production `activation_trace.measure`
and schema2 gas helpers offline against the exact recorded responses. This adds
current-runtime accounting/gas-reader integration without repeating EVM execution.
[Receipt](backend/ACTUAL_CONTRIBUTIONS.json).

That does not establish complete Projection/configuration inventory admission,
the final hosted preparation endpoint, or actual provider fee semantics. The
browser checks use typed fixtures through actual source9/source10 code; they do
not turn the source9/mint1 EVM cohort into a mint2/OpenSea/V10 deployment.

## Public provider outcome

The [bounded network campaign](network/REVIEW.md) refreshes actual32M execution
parameters at two corroborated recent anchors. It does **not** find a provider
qualified for complete preparation:

- Daybreak accepts canonical-hash calls/estimates with20M/24M fields, rejects an
  unknown hash and corroborates selected-core code; `callTracer` with logs is
  unavailable (`Method not found`).
- BlockVectra rejects fresh canonical-hash state calls/estimates and disallows
  tracing. Numbered-block successes are isolated diagnostics, never a fallback.
- OrdoFi's first chain handshake fails in transport; no valid chain data is inferred.

Cheap precompile calls prove interface/field acceptance, not the amount of work
a provider will execute. Numerical full-operation gas caps, trace/response/time
bounds, archive retention and sustained service still need qualification. No
provider is installed or adopted. Missing traces remain an explicit refusal,
never an invented success or weaker financial check.

## Adoption and remaining gates

The package intentionally leaves complete-fee approval false, review hashes and
fee ceilings null, and keeper receipt accounting unverified. It is **not** a full
runnable service configuration. A calculated local padded cost is not an approved
operator spending ceiling. No current Robinhood total-operation fee quote is
established by the local Anvil estimates.

Before adoption: qualify a complete canonical-hash trace/estimate provider,
real independent feeds and useful routes/depth, exact deployment/consumer
identities, complete fees and operator transaction/day budgets. Cover the actual
NFT/currency/bucket/state workload and unchanged request/worker/trace limits;
these cases are not a universal20M/24M guarantee. Existing consumer/work budgets
and both public null configurations remain. Review pending hashes/spend, then
use a separately authorized restart/rollout with original journals preserved.

The [sole Todo](../../TODO.md) retains those external gates. The normal/static
and earlier market reports keep their source scopes. This campaign deploys
nothing, resets no existing Anvil or saved operation, enables no signer and
does not restart the user-paused heartbeat.
