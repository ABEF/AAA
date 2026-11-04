# Manual operations and safeguard composition

Source baseline main0b14aca; current change is limited to Confirmation and the
read-only custody validator. This is an internal control-flow review, not proof
that every combination of market/dependency behavior can execute.

## Operator intent and actual route

| Intent | Entry / authority | What can intentionally block it? | Recovery / reverse |
| --- | --- | --- | --- |
| Ordinary manual rebalance | `Vault.rebalance`, actual keeper grant, unpaused | On-chain cooldown, threshold/manual-geometry condition, confirmation, prices, execution/allocation/final LP guards. Python jitter/schedule is not a contract gate. | Use the separate paused governance emergency if optional policy must be bypassed. |
| Force replacement now | Paused governance `Migration.emergencyRebalance`, fresh exact request | Only selected retained policies plus mandatory structure/accounting; `checks=0` skips all five optional groups. | Always one new main in CURRENT pool; still paused. Repair ordinary policy then separately unpause. |
| Force LP again from parked | Same emergency entry, hash prepared from actual PARKED state | No optional trigger/window/cooldown/price/loss/idle/enabled-operation gate with mask0. Actual assets must form positive LP in supplied ticks. | Same fixed current pool. Shares/reward backing remain. |
| Close both temporarily | Paused governance `Migration.park` | Exact custody/nonce/epoch/hash/deadline and actual settlement. Both review-time token minima may explicitly be zero. | Guarded ordinary resume, or paused emergency for current-pool raw deployment. |
| Close residual only | Paused governance `Migration.closeResidual` | Same exact snapshot; actual registered residual, unchanged main and callbacks. Both raw floors may be zero. | Main stays; idle belongs to the same shares. Desired mode is unchanged. |
| Stop residual and consolidate | Governance desired modefalse, then guarded ordinary or paused emergency replacement | A setter alone never moves existing assets. Ordinary path still needs readiness. | Enable future mode separately; never silently create a third leg. |
| Select a different LP pool | Unpaused governance `moveFunds` or parked `resume` | Reviewed same-pair destination, fresh policy/prices, complete move loss/idle/LP proofs. | Park when ordinary movement cannot execute. Raw emergency is current-pool-only; it cannot admit a new destination. |
| Harvest only | Live `Vault.collectFees`; internal harvest inside recovery | Actual core/token/fee-ledger availability, deadline and custody. No USD, rebalance timer or swap. | Claims remain separately callable. Global pause blocks public harvest, not authenticated internal recovery harvest. |
| Compound | Authorized keeper/Compounder and Vault | Own interval after last compound/rebalance, raw rebalance priority, existing-range deployment and financial guards. Python also waits below threshold/in-range/no geometry change. | Wait/repair; governance may use whole emergency replacement. No new unsafe compound fallback. |
| Convert rewards / buyback | Authorized typed converter/buyback paths | Actual classified reserve, approved execution, prices/output floors and respective limits; not holder principal. | Hold funded raw balance until reviewed recovery. Emergency principal permission cannot sweep reserves. |
| Stop/restart operation | Pause, pool flags, desired policy and service controls are different | Pausing does not cancel an already broadcast transaction; unpause alone neither mints LP nor bypasses cooldown. | Reconcile same saved hashes/nonce/spend; repair runtime/config and separately resume service. |
| Return principal permanently | Paused governance collective exit, closure/allocation/distribution batches | Exact backing, ownership and isolated payouts. No swaps or USD required for raw close. | Terminal: no manual or emergency LP reopening. Failed recipients retain backing/fallback rights. |
| Canonical replacement | Reviewed pre-exit preparation/parked same-chain handoff | Ownership/reward lifecycle, exact backing and no live residual. | Cancel preparation where permitted; never use force to duplicate canonical rights. |

Normal standalone calls retain their established permissions. There is no generic
operator sweep, holder normal-principal withdrawal, external custodian, arbitrary
executor or automatic emergency fallback.

## Emergency groups: retaining one may need data used by another

| Retained bit | Actual dependency | Independent choice / scope |
| --- | --- | --- |
| 1 | Strategy raw threshold or pending deliberate geometry, hard cooldown and data needed by that Strategy read. | Disabled with mask16 alone; Budget enforces it separately when selected. |
| 2 | Fresh independent USD/reference data and spot agreement. | Bypassing it does not make valuation for retained bit4 possible without prices. |
| 4 | Captured whole-operation retention, swap-quality/venue floors and deployment idle budget. | Needs healthy USD valuation, actual directional fees and applicable venue state. Raw amounts/floors remain even when off. |
| 8 | Pool operations-enabled flags for deployment/swaps. | Typed already-admitted identity, fixed pair/core/recipients remain even when off. |
| 16 | Existing matching same-side sampled record or established manual-geometry exception; live condition/identity/control checks. | No implicit hard cooldown after this fix. Pause cannot extend samples; stale/absent/invalidated records reject. |
| 0 | No optional group retained. | Active and Parked recovery can execute without USD/ordinary router/confirmation policy when actual core/asset/math settlement works. |

The bits are not five independent sources of data. For example, a financial
limit cannot be evaluated without a price simply because spot-agreement bit2
was disabled. These dependencies are now explicit rather than weakened.

## Normal safeguards: overlap versus accidental coupling

| Guard / phase | Why it remains | Interaction and non-blocking boundary |
| --- | --- | --- |
| Raw85% trigger plus hard12h | Limits ordinary turnover; deliberate geometry is a separate exception after cooldown. | Readable during cooldown. It is not the sampled-window decision. Main contributions do not reset geometry identity/clock. |
| Physical/reference same side | A manipulated local pool alone cannot qualify ordinary adjustment. | Disagreement intentionally waits; it is unavailable/blocked rather than a forced trade. Operator may review emergency separately. |
| Sample600/maxgap300/source240 | Rejects transient sampled trigger and stale observations. | Can enroll near cooldown; service jitter60–300 renews samples. This is sampled evidence, not continuous history. Missing resets/receipts cannot be guessed. |
| Source agreement3% | Validates agreement of the two admitted USD sources. | Distinct from pool spot/reference deviation and swap loss. Higher TVL/two addresses do not prove independence. |
| Per-swap gross/fee-aware/caller floors | Bounds each actual swap, including known fees and an additional allowance. | Strongest floor wins; percentages are not summed or free budgets. More permissive aggregate policy cannot waive a stricter caller/venue floor. |
| Pre-mint buffer and final whole-operation retention | Protects different points around external swap/mint/refund calls. | Conditionally overlapping in fixed-price models, but valuation timing, rounding and callback scope differ. No blanket removal justified. |
| Final deployed LP / idle / main allocation | Proves actual productive liquidity and bounded retained leftovers. | A quote/config acceptance is not successful deployment. Infeasible optional geometry rolls back; modefalse or explicit emergency single recovery is available. |
| Contribution marginal-deployed floor | Entrant assets must actually increase main LP before shares/traits update. | Incumbent idle/residual/compound cannot subsidize an entrant. Separate whole-bucket idle ceiling can intentionally block entry; existing holder recovery remains available. |
| Compound timing and service wait | Stops routine compounding into a threshold/outside/pending-geometry condition. | Rebalance ignores lastCompound, so compound cannot postpone its hard clock. Hourly harvest remains independent. Different code on a keeper key can ignore Python-only restrictions, not contract guards. |
| Callback pre/post captures | Prevents governance/policy/price/context mutation during a single operation. | A repeated check after an external call protects a different moment. Restore-to-original configuration does not revive an old reviewed revision. |
| Exact balances/owners/shares/reserves | No prefund subsidy, recipient diversion, fee/principal confusion or duplicated entitlement. | Mandatory on normal and emergency paths. Never waive to get a trade through. |
| Lifecycle locks | Prevents principal reopening after terminal return or duplicating canonical ownership during handoff. | Mandatory. Closing for preparation is distinct from starting new LP work. |

## Two corrected conflicts

1. Emergency bit16 called `needsRebalance`, silently reintroducing bit1's hard
   cooldown. That gate is removed ONLY from emergency sampled evaluation;
   ordinary readiness and an explicitly retained bit1 still enforce it.
2. Shared parking validation rejected two zero reviewed output floors. A position
   can change asset composition before inclusion without changing IDs/ticks/L.
   Paused governance may now explicitly accept the actual composition. Supplied
   positive floors, the core-derived current principal proof, exact receipts,
   backing and all authority/lifecycle checks remain.

## Limits deliberately retained

Force cannot manufacture missing tokens, fix a frozen asset or broken core,
create liquidity from one asset inside arbitrary mixed ticks, accept invalid
tick spacing, ignore exact signed-delta/amount bounds, fund gas, or revive terminal
rights. An explicit positive output/LP floor can still fail. Public ordering and
malicious governance remain risks; mask0 may lose nearly all principal. A raw
mint need not be active or conform to configured future geometry. Verify it.

Future destination-force capability, richer diagnostics and real operating
rehearsals need their own review; this audit does not silently broaden them.
No remaining unintended deadlock was established in this reviewed scope; that
is not an exhaustive-state or exploit-absence guarantee.
