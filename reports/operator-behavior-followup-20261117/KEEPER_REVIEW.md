# Keeper coordination and interval-crossing behavior

Baseline: `6945eeeba24304b8ddf27ac4c08fe55dc553554e`.

This follow-up tests a behavior gap that the prior function/input inventory did
not establish. It does not repeat that inventory as new dynamic coverage.

## KEEPER-01 — slow reads could defer newly due maintenance

**Confirmed operational lag, fixed.** `Keeper.cycle()` captured `now` before
bucket discovery and strategy/routing/reserve reads. It later used that old
timestamp for the local compound interval and hourly harvest due comparison.
The separate final harvest-head refresh happened only after that old comparison
already said harvesting was due.

Example: the last harvest is3,590seconds old at the initial head. A strategy
read consumes20seconds. The current chain is then3,610seconds after the last
harvest, but the cycle still compares3,590against3,600 and produces no harvest
candidate. A transient price failure has the same effect, despite harvesting
being deliberately independent from price-based maintenance. Slow reserve reads
could similarly cross the local compound interval without producing a candidate.
This adds another polling delay; it is not proof of stolen fees or bad on-chain
allocation.

Three new cycle-level regressions reproduced the baseline failures before the
fix: successful-maintenance crossing, price-fault crossing, and compound-reserve
crossing. Each expected exactly one eligible operation and observed no candidate.

### Correction

- Refresh the authoritative chain head immediately before the local compound
  due decision, after reserve reads. Use that timestamp for the original local
  interval and freshly prepared deadline.
- Refresh the chain head **before** deciding whether an enabled harvest is due,
  including after failed price-based maintenance. Use the same timestamp for its
  due decision and deadline.
- Reject an observed timestamp retreat rather than use an older deadline.
- Do not add this harvest read when harvesting is disabled.

The ordinary submit path still performs its existing lifecycle, permission,
simulation, gas, nonce, budget and final-deadline checks. `compoundReady` and
the service's range/threshold policy remain required. No interval, observation
gap, jitter, permission, price/slippage limit, gas default or contract changes.

**Read-cost tradeoff:** an enabled but not-yet-due harvest now performs one
additional small head observation. Enabled compounding similarly refreshes its
due-decision head after reserve reads. The bounded bucket loop limits this work;
no additional transaction is authorized by the clock refresh itself.

## Focused behavior evidence

Nine new methods pass, covering:

1. Harvest becomes due during healthy maintenance reads.
2. Harvest becomes due during failed price-dependent maintenance.
3. Local compound interval becomes due during reserve reads.
4. Failed fresh harvest head never falls back to an earlier due head.
5. A retreated harvest timestamp rejects without using an old deadline.
6. A transient compound-head failure can yield to an independent healthy harvest
   head without submitting compounding.
7. Current clock readiness cannot override `compoundReady == false`.
8. Pending recovery precedes every new clock read and operation.
9. The actual accounting7/custody5/confirmation3 worker cycle, with real current
   profile validation and bounded discovery, produces the due harvest after an
   interval crossing.

The source7 case extends the existing pinned wire fixture only to expose worker
inventory methods. It uses the explicit LP2 profile, not execution1/LP3; no live
runtime or provider is inferred. All cases use injected RPC, temporary state and
a mocked submission boundary. They prove candidate selection/deadlines and
preservation of gating, not signatures, EVM execution or on-chain fees.

One affected existing call-count test was updated and passed: enabled harvest
refreshes its due clock in both not-due/due cases, while disabled harvest adds no
harvest-clock read. No unchanged methods or full suite were rerun.

The new module is registered in the maintained keeper runner. Its selection
inventory executes zero methods and does not stand in for behavior verification.
See [method/source evidence](KEEPER_EVIDENCE.json) and
[runner selection](KEEPER_INVENTORY.json).

## Additional inspected interactions

The following are source assessments, not additional dynamic passes:

| Flow | Assessment and remaining limit |
| --- | --- |
| Saved transaction recovery | Runs before new lifecycle, route and maintenance work. Ambiguous intent remains saved; no automatic resend or nonce adoption is introduced. |
| Receipt clocks | Successful internal harvesting advances the hourly clock only with authenticated receipt/log provenance. Submission or guessed NAV movement is not success. |
| Confirmation deadline priority | Existing sampled/reset deadlines precede optional nonce users after pending recovery. Several simultaneous windows or slow inclusion can still exceed the strict gap; priority is not a timing guarantee. |
| Local retry isolation | Paid-revert retry keys are action-specific. Unrelated due harvest is not automatically assigned a compound/rebalance retry delay. |
| Conversion and buyback scheduling | Existing durable rotating priorities retain independent opportunities. A pending serial transaction still blocks new signing until reconciled. |
| Read-only operation review | Its explicit scope reports selected chain prerequisites and local retry/reset evidence; it does not claim a worker jitter identity or guaranteed next execution time. That documented omission is not treated as a newly fixed worker defect. |
| Service-only compound policy | On17November the user explicitly chose to retain the extra wait in keeper software. Another authorized keeper implementation may ignore it where the contract allows; this accepted boundary is not a pending requirement to add an on-chain restriction. |
| Unknown errors | Unavailable data remains unavailable. No opaque RPC failure is relabelled as an exact slippage/oracle diagnosis, no automatic force path is added. |

## Preservation and remaining qualification

No Solidity, rights, safeguards, live service/site, actual signer, existing
Anvil/database/journal, public RPC or paused monitoring change occurs. Test state
is temporary and isolated. No compiler, static analyzer, fork campaign or chain
rehearsal was rerun. Original manual gas/output work is outside this change.

Actual chain/provider responsiveness, finality, complete fees, maximum-state
operation, independent markets, host recovery and independent approval remain
open. Finite injected-wire tests do not establish uninterrupted operation or
exhaustive adversarial coverage.
