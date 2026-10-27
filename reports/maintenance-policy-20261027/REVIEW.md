# Outside-only upkeep and independent compounding: internal review

Base main `295e2402e67a89a9c8058ff39ef42931d2b5bf68`. Fresh undeployed source;
production NOT APPROVED. [Verification](VERIFICATION.md) records the exact scope.

## Settled policy and implementation

The user selected a hard initial12-hour rebalance interval even after an earlier
range exit, deliberate operator width application inside after cooldown, and an
independent configurable compound interval. Hourly harvest remains independent.
The interval remains governed within existing supported bounds; twelve hours is
the intended initial configuration, not a new immutable minimum for every pool.

| Component | Delivered change | Boundary |
| --- | --- | --- |
| Strategy2 | Ordinary replacement requires actual stored tick outside physical LP ticks, or an operator desired-range mismatch, after the configured hard interval. Reference movement alone does not trigger it. | Independent fresh reference/spot checks remain; no same-pool oracle substitution. |
| Boundary observations | Validate sqrt/tick consistency, actual LP ticks, static LP fee and bounded directional protocol fees; preserve exact downward-crossing tick. | Consistent observation is not independent provider or market authenticity. |
| Budget3 | Per-pool compound interval, default3600seconds, governance600seconds-7days; existing clocks anchored at max(lastCompound,lastRebalance). | Due rebalance retains priority; compound never resets lastRebalance or changes NFT shares/backing. |
| Keeper policy2 | Bounded durable namespace, hourly ordinary inside checks, one OS-random60-600second jitter for outside or operator-directed work, fresh due-time/pre-signing checks. | Service-only schedule; a keeper key calling contracts directly bypasses jitter. No exact inclusion guarantee. |
| API preparation | Explicit accounting4 maintenance profile1 historical or2 current; policy2 verifies Strategy2/Budget3 once at pinned state and recomputes actual eligibility. | No fabricated keeper ETA, automatic profile fallback, website signer or deployment. |

## Security and recovery review

- New timers bind stable deployment/module/runtime, pool policy/orientation,
  physical LP ID and last replacement. Prices, balances, idle, deposit totals,
  top-ups and harvesting cannot redraw the delay. Restart preserves it; inactive
  scheduling records alone can be removed. Schema, count, uint256 bucket IDs,
  uint64 times and interval shapes are bounded.
- Durability precedes waiting/signing. A failed save restores memory and prevents
  submission. Pending/nonce/receipt/spend history and existing paid-revert backoff
  are preserved. No missed-cycle replay or automatic resend is introduced.
- A new manual width request can bypass the local hourly-inside wait, but never
  the on-chain cooldown or chosen jitter. Return inside cancels ordinary work;
  a still-pending operator range update retains its intended exception.
- Harvest and receipt work continue while a timer waits. Enabled fresh compound
  requires currency-specific thresholds and authenticated Budget3; historical
  fallback/readers are explicit. Malformed capabilities do not become legacy.
- The new compound setter requires governance, an admitted pool, allowed interval,
  operating canonical state, no preparation and no active captured snapshot.
  Ordinary pause permits reviewed configuration. It rewrites no clocks/backing.
- Existing Budget storage fields retain their recursive layout; one interval
  mapping is appended. Strategy/Vault/NFT storage stays unchanged. This is not
  authorization or a mechanism to upgrade an already sealed deployment.
- Existing contributions retain current LP ticks; reward allocation and claims,
  immutable token/custody boundaries, raw collective holder return and the
  default2%/1%/3% execution categories are unchanged.

Independent internal source partition reviews found no material defect in the
examined scheduler/API/contract composition. This is not an independent audit or
a proof of no profitable keeper/outside-actor strategy.

## Remaining exposure

An LP leaving range early can remain inactive until the hard interval elapses;
hourly checks, jitter, pending transactions and safety failures can delay upkeep
further. A wider range does not guarantee continuous fee earnings.

Current Vault still balances through its own LP pool. Best approved execution
venue selection, a full-depth normally-one-swap solver and optional timed partial
replacement remain outside this implementation. Jitter does not fix bad routes,
correlated/stale prices, sequencer/provider trust or repeated permitted losses.
No cumulative-loss breaker, new timelock, widened cap or protected provider was
added. Actual feeds/routes/gas/services/authority/OpenSea/VRF and independent
audit/remediation remain release gates.

Use the [operator guide](../../docs/OPERATOR_MANUAL.md#operator-selected-lp-policy),
[decision record](../../docs/LP_EXECUTION_POLICY.md) and
[single task ledger](../../TODO.md#task-lp-execution-routing).
