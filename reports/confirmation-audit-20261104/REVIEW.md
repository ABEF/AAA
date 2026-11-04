# Rebalance confirmation: timing and recovery audit

November4,2026. Baseline main `cf39b1402915c438b8278cf9c8b51c321922b98f`.
[Verification](VERIFICATION.md), [audit matrix](COVERAGE.md),
[stage evidence](evidence.json). Production **NOT APPROVED**.

## Result

Two keeper liveness defects are corrected. No contract, authority, financial
guard, configured duration, journal schema or deployed service changes.
The final selected100Python methods pass, including14new regressions. Failed
negative controls remain retained; counts from overlapping attempts are not added.

### C1: saved deadlines did not control the daemon sleep

The keeper already recorded an early next check for600-second maturity/cooldown
and a saved60–300-second jitter. The outer `poll_delay()` nevertheless returned
the complete configured interval. A120-second maturity or60-second jitter could
therefore wait240seconds. Work after the last scheduling head added still more
delay; a slow cycle could contribute to exceeding the strict300-second gap.
On-chain checks fail closed, so the demonstrated consequence is delayed work or
repeated window restarts, not an authorized stale rebalance or stolen principal.

The keeper now caps healthy, non-pending sleep by the earliest saved candidate
deadline, including maturity, cooldown and jitter. A recent validated head plus
elapsed monotonic time supplies an ephemeral scheduling estimate. It is never an
eligibility proof, persisted clock, replacement RPC, observation or signature.
Every submission still rechecks actual chain state. Time spent after the read
reduces remaining sleep. The daemon sleeps toward a monotonic deadline instead
of accumulating watchdog/work overhead once for every one-second iteration.

Missing, backward, nonfinite or older-than600-second local timing anchors fall
back to normal polling. An already-overdue blocked candidate uses at most a
60-second retry wait, avoiding a one-second busy loop. Pending receipt polling
and global RPC/nonce-error backoff retain their existing behavior. Restart does
not import this local clock; it obtains fresh state. No saved jitter is redrawn.

### C2: a queued clear depended on unrelated router metadata

Priority work validated LP routing before checking an already-recorded incident
reset. A router metadata outage could therefore prevent `resetObservation` from
being attempted, even though clearing evidence performs no swap. The durable
reset flag still blocked this keeper's rebalance: this was a recovery delay,
not a bypass of the sampled window.

Known clear-only work now precedes that routing metadata read. Its own submission retains
helper/runtime/authority/lifecycle/simulation, nonce, gas and spending checks.
Global reviewed-code checks remain; unavailable or changed dependency bytecode
can still prevent signing. This removes the specific metadata prerequisite,
not every dependency needed for safe submission.
If it cannot submit, it remains queued and cannot turn into a renewal or a
rebalance in the same cycle. Normal observations and LP routing behavior otherwise
remain unchanged; unrelated routing faults still do not erase healthy price
evidence by themselves.

## Contract and timing conclusions

- Current confirmation3 defaults to600seconds, not the earlier900-second design.
  Construction max-gap0 deliberately stops ordinary sampled readiness until
  reviewed governance configures it. The selected maximum gap is300seconds.
- A same-side physical and independent-reference85%threshold is required at
  recorded samples and execution. Return inside, reversal, LP/control identity
  change or a caught observed fault clears/restarts evidence as appropriate.
- 300seconds is inclusive;301is stale. Repeating samples in one block does not
  manufacture elapsed time. An old first sample plus a late endpoint is insufficient.
- The hard initial12hours is separately enforced. Ordinary samples may mature
  during cooldown; service jitter starts only when both sampled readiness and
  execution cooldown pass. Near-eligibility paid enrollment starts600+300seconds
  early: that15-minute lead is not a15-minute confirmation requirement.
- Deliberate operator geometry changes retain the explicit cooldown-gated sample
  exception. Paused-governance emergency retains its separate accepted bypass
  trust. A normal keeper cannot configure these policies.
- Successful entry/growth changes shares/main L but not stable geometry identity
  or the rebalance clock. Raw evidence/control fingerprints remain checked across
  external execution callbacks; post-replacement readiness is intentionally not
  substituted for the original evidence snapshot.

These conclusions combine source inspection, selected worker tests and the prior
source-bound actual-v4 campaign. No unchanged Solidity suite or analyzer was rerun.

## Operator action and remaining risk

This is published source, not a service update. For a matching reviewed keeper
release, use the existing stop/reconcile/install/restart procedure, preserve the
same deployment/profile/configuration and pending/nonce/spend journal, and verify
new source-bound health. There is no journal migration, contract redeployment,
reseal or duration setter required by these fixes. Do not relabel the older
served site/Anvil/staging runtime, expose governance keys, or restart the paused
heartbeat. No running environment was changed by this campaign.

Sampling cannot detect a return inside between observations. A serial pending
transaction, RPC/inclusion delay, host outage, stalled chain, spending limits or
unqualified feeds can still prevent timely samples and legitimately restart the
window. Jitter is service policy, visible observation transactions are not MEV
immunity, and these tests do not establish attacker unprofitability. Actual
independent price sources, current-profile hosting, target-chain receipt timing,
gas/economics and independent review remain open in the sole Todo.
