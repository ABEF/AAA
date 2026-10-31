# Manual operation audit and operator improvements

Reviewed 2026-10-31, Europe/Paris. Local main candidate based on
`37577ebf610ed7182c3d5bc481d7bb32ec5438c1`; production NOT APPROVED. No deployment,
public transaction, service/site/Anvil change, signing extension or journal edit.

## Scope and actual changes

The review traced39 groups of manual/long-term operations and classified all231
state-changing ABI functions:90 direct management/manual-maintenance/public-relay
entries,127 fixed-module/self/provider endpoints,12 holder/payer flows and2
deployment factories. Constructors/receivers are inventoried separately. This
classification is not231 executed tests or proof of every possible state path.

The [single Operator manual](../../docs/OPERATOR_MANUAL.md) now contains task
sequences, exact input units/sources, caller/pause/lifecycle requirements,
postconditions, reversal/restart and failure handling, plus a90-entry ordered
[write-input catalog](../../docs/OPERATOR_MANUAL.md#manual-write-input-catalog).
Full nested ABI fields remain linked in the callable reference, avoiding a
second conflicting tuple specification. Management-guide compatibility links
and existing unrelated work are preserved.

| Finding or management hazard | Implemented correction |
| --- | --- |
| The main/residual were being described as two pools; global pause and position closure were easy to confuse. | Define two physical positions in one pool. Distinguish mode change, delayed normal merge, residual-only close, whole park, immediate emergency consolidation and irreversible holder return. Show exact unpause and separate resume calls. |
| Before-seal authority prose incorrectly implied an unrelated governance wallet could also configure. | Correct46 source-checked access explanations: canConfigure admits bootstrap only before seal, then current governance in canonical operating/no preparation. Preserve special propose/accept/pause rules. Regenerate both callable references without changing permissions. |
| Permanent reservation order can strand an intended pool move. | Admit target with deposits off, inspect its poolBucket, reserve the intended existing bucket before target deposits, stop source deposits, execute guarded movement, then enable target contributions. Explain non-reassignable aliases/four slots and first-activation canonical identity. |
| Unpausing after parking could reopen contributions sooner than intended because neither pause nor park clears deposit flags. | Explicit source-deposit stop before unpause/resume; inspect successful deployment before re-enabling. Treat successful prior steps as persistent when a later transaction fails. |
| gap0 wording could be read as stopping every rebalance; an empty automatic venue list could be mistaken for blocking the manual emergency swap. | Explain sampled-market stop versus deliberate geometry exception. Emergency uses its independently reviewed exact admitted swap manifest. Use actual permission/pause/operations controls for containment. |
| Operator hash/argument preparation was absent. | Add a bounded offline review helper with strict JSON and named nested ABI validation, exact decimal strings, deterministic provenance hash, ordered explorer inputs, source/catalog binding and tamper checking. Three intentionally incomplete examples show mode-off, residual-close and emergency requests. |
| Long-term limits and generic-only management names were difficult to discover. | Add exact preparation/export/import/conversion entry names and all management settings, with read sources and irreversible/unsupported boundaries. Correct fixed chain/pair and stale static-analysis wording. |

No new production Solidity defect was established by this manual-operation pass.
All50 production Solidity files remain byte-identical to final normal build
`normal-final-8511732986`. No pause requirement, financial limit, role, custody
right, economic allocation, profile or accepted emergency authority was changed.

## Most important operating sequences

- **Normal single-mode return:** setMode(false), then an eligible keeper-authorized
  unpaused ordinary rebalance merges both and proves an active new main. Failed
  execution preserves old positions; desired policy remains pending.
- **Residual only:** reconcile pending work, pause, choose desired mode, read a
  fresh ParkingRequest, closeResidual, verify unchanged main and attributed idle,
  then deliberately unpause. The main can keep accruing actual in-range Uniswap
  fees; large idle may require guarded deployment before new contributions work.
- **Immediate single recovery:** mode off if required, pause, fresh custody hash,
  complete reviewed emergency manifest/simulation, consolidate and inspect, then
  unpause. Explicit financial bypass can lose nearly all principal; never drop
  checks as an automatic retry.
- **Temporary full removal:** disable intended deposits and park both legs;
  repair dependencies, unpause, resume under normal guards, inspect, then reopen
  deposits. Terminal collective holder return has no corresponding restart.

PoPL cannot pause external Uniswap trading or independently freeze only one
deployed range. There is no close-main-only/keep-residual path, arbitrary sweep,
external custody recipient, live pair/token substitution, bucket reassignment,
integrated bridge or post-terminal canonical replacement. These are boundaries,
not hidden controls or newly proposed features.

## Verification and remaining work

[Verification](VERIFICATION.md) records16 final distinct offline helper methods
and one new composed actual-local-v4 journey: unpaused mode-off → guarded merge →
both old positions burned → active sole main → real core fee-growth collection →
exact native claim → second claim zero. Explicit token/feed/VRF/authority/Permit2
fixture substitutes remain; core donations test funded fee accounting, not real
trading volume, market profitability or production gas.

The helper performs no RPC, live custody lookup, operational simulation, signing,
calldata submission or authority/runtime/freshness verification. It always reports
not ready for submission. A successful hash check proves local consistency only;
an attacker able to rewrite both a record and checksum is not authenticated.
Actual input values, meaningful execution minima and full exact-call simulation
remain operator preparation requirements. The helper is not an automatic
ParkingRequest/EmergencyRebalance planner or Safe transaction file.

Actual dual feeds/routes/VRF/authorities/OpenSea, profile5 hosted services/UI,
target gas/depth/ordering economics, maximum populated batches/URI, Linux restart/
receipt/backup rehearsals and independent frozen-release audit/remediation remain
open. Strict sampled timing and narrow candidate ranking retain their known
liveness limits. The guide cannot promise recovery from irreparably broken tokens,
core dependencies, lost governance or rejecting/incompatible recipients.

README, sole Todo, features/evidence, roadmap, release/context/handoff and relevant
guides were synchronized. Source publication/deployment remains separate; this
request leaves the work local, uncommitted and unpushed.
