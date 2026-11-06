# Automatic and manual LP execution in moving markets

6 November 2026; baseline main e1a85a2. Production NOT APPROVED.
[Executed scope](PROMPT.md), [all-input matrix](INPUT_MATRIX.md),
[blockers/recovery](BLOCKERS.md), [verification](VERIFICATION.md).

## Implemented improvements

| Finding | Change / effect |
| --- | --- |
| Guarded manual same-main routing could select an inactive candidate although the final contract requires activity | Manager now uses the existing active-aware solver only for paused, fixed-Migration authenticated guarded consolidation. Actual local core comparison reproduces legacy inactive self quote and successful active alternate. No feasible active route still reverts atomically. |
| Initial keeper economics simulation preceded several final validation RPCs | One late exact whole-call simulation uses the original reviewed gas/gasPrice envelope. Exact void0x is required. No calldata, caller floor, deadline or cost cap is changed. |
| Those final policy reads could themselves expire the deadline or change the UTC budget day | Two additional failing probes exposed this before publication. Final service/lifecycle/readiness, nonce and funding now precede the LAST head/deadline/day/retry check; only local intent/signing work follows. |
| Fixed LP bounds, live tick, custody hash and financial preview were easily confused operationally | Full input/phase and blocker/recovery matrices now distinguish all four paths, parameters, current owner/fee/idle rights, callbacks, pending recovery and long-lived cycles. Manual instructions include exact diagnostic names and original-deadline behavior. |

These are operability and pre-sign policy improvements. Prior on-chain guards
already reverted unsuitable ordinary trades; the route gap did not authorize a
lossy inactive normal main. A discarded simulation is not a public transaction.
Old acceptance probes concern unnecessary/locally invalid signing, not proof
that an on-chain attacker could bypass principal accounting.

## What stays distinct

Automatic Vault.rebalance takes bucket/minL/deadline, not old ticks. At inclusion
it reads current shares/NAV/policy, harvests both, includes compound, closes both,
calculates a new approved reference-based range and actual-core route, then checks
active placement. Desired OFF produces one main. Another transaction cannot
interleave inside this atomic call; our own swap and callbacks are checked.

Guarded manual consolidation preserves main ID/bounds/centre/lastRebalance and
shares, reinvests actual residual/idle and leaves designated compound separate.
It does not recenter an already unsuitable main. Contributions before pause
invalidate its custody snapshot; after confirmed pause ordinary entry is blocked.
Price and fees can change without a custody identity mutation.

Forced same-main and full emergency remain explicit governance choices, never
automatic retries. Their financial masks are optional; even full-emergency
checks14 does not promise active geometry. Fixed identities, exact receipt/
classification/custody, positive caller floors, deadline and lifecycle remain.
No funds are sent to a new recipient, no economic split/claim right changes and
no holder or keeper gains a governance operation.

## Verification and limits

10 distinct selected actual-local-v4 successes (3new/7affected),67 focused Python
methods (21new/46affected),93 reference/default methods, fresh44normal objects
plus2actual data-child gates and497strict static records are separately scoped.
Earlier failing fixtures/assertions/timing probes are retained; overlapping
stages are not summed. No full suite or independent audit is claimed.

Only Manager changes production Solidity. ABI/storage/capability/profile shapes
stay unchanged; exact runtime/creation pins change. Manager runtime is22411bytes
(2165headroom); Vault remains24469(107headroom). All other production runtime
templates and the full normal RoyaltyRewards creation payload remain identical.
Compiled templates are not deployed immutable-bound code hashes.

The live manual read/unsigned preparation tool remains unimplemented: the
offline review helper only hashes/validates supplied evidence and orders inputs.
Actual operator/provider/gas rehearsals remain required. Bounded routing cannot
guarantee a globally optimal or always-feasible execution. A local pause does not
stop external trading. Local fsync/signing/network latency and later blocks can
invalidate a final review; do not extend a deadline, clear ambiguous intent or
weaken financial guards to manufacture success.

Real independent feeds/routes/VRF, authorities/OpenSea, target maximum gas and
economics, provider/host/backup recovery, matching fresh services/site and
independent audit/remediation remain release gates. Source publication is not
deployment, sealing or rollout. Existing Anvil/NFTs/LP/balances/journals, websites,
signer restrictions and the user-paused heartbeat remain unchanged.
