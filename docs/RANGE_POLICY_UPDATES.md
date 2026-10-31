# Applying range settings after sealing

Fresh [accounting6 / portfolio2](POSITION_V6.md) source candidate. Governance is
the user's operator wallet; the automated keeper has a separate limited grant.
Changing desired policy and replacing physical LP are different actions. Current
size/runtime gates, scoped offline checks and local actual-v4-core integration
pass within their [recorded scope](../reports/residual-operations-20261031/VERIFICATION.md).
Market, gas, host and independent qualification remain open.
No source or documentation update changes an installed service or deployment.

## Selected operating policy and source versions

Strategy maintenance3 and Confirmation3 use 85% of actual centre-to-main-boundary
ZZZ-in-ETH price distance. The selected sample window is 600 seconds, source
checks 240 seconds, maximum confirmed gap 300 seconds, then one durable random
60–300 second service delay. Samples may accumulate during the initial hard
12-hour cooldown; they never authorize early execution. Raw checks continue,
but paid ordinary samples enroll only from cooldown minus duration minus maximum
gap, initially the last 15 minutes. Earlier observations are not credited as
continuous evidence; required recovery/reset work remains first. Direct keeper calls skip
Python scheduling/jitter while preserving ordinary on-chain guards.

Governance manually selects width, normally +/-25% or +/-50%. Leave automatic
keeper width selection disabled. Mode and active residual-geometry changes also
create an explicit pending replacement after cooldown. [Full policy](LP_EXECUTION_POLICY.md)
and [operator steps](OPERATOR_MANUAL.md#operator-selected-lp-policy).

## From approval to execution

1. Read the complete `PoolRegistry.get(poolId)` and actual physical main/secondary
   IDs, bounds, custody and latest confirmed clocks. Governance changes only the
   reviewed fields through `configureNative(fullConfig)`; retain native ETH and
   the fixed ZZZ identity, static fee/key and every stronger limit.
2. `Strategy.rangeUpdatePending(bucket)` compares desired main ticks at the
   **recorded centre**, not today's drifting price, and includes Policy
   `configurationPending(bucket)`. It is not permission to trade immediately.
3. After the hard cooldown, a deliberate width/mode/active geometry mismatch can
   apply while the old main is in range. This manual exception skips the ordinary
   sample window, preserving healthy prices, exact custody and financial guards.
   It can repair an old centre outside the existing bounds without requiring
   threshold interpolation. Ordinary market candidates remain fail-closed.
4. The keeper runs the ordinary guarded `Vault.rebalance(bucket,minLP,deadline)`.
   It harvests and closes both actual old legs, balances within reviewed limits,
   and atomically creates the selected single or main/residual portfolio.
5. Verify confirmed new main/auxiliary IDs, owners, ticks, actual token amounts,
   applied geometry revision, new centre/clock, retained value and unchanged NFT
   shares/earned rights. Failure restores the old portfolio and leaves the
   desired configuration pending; it does not permit a raw fallback.

On-chain settings are read afresh and normally need no keeper restart or reseal.
Local source, version/runtime, RPC, schedule or threshold JSON changes require
controlled restart, with pending/nonce/spend evidence preserved. A configuration
change does not cancel a broadcast transaction. Reconcile it by its original hash.

## Explicit price direction

`Strategy.rangeOrientation(pool)` is 1 for ETH per ZZZ, the requested usual token
price view; 0 retains the historical raw inverse. Use governance
`setRangeOrientation(pool,1)` with reviewed full configuration. This changes
future target ticks, not existing custody or historical earnings. A direction
change disables an enabled automatic width policy.

| Desired interval around ZZZ price P in ETH | `rangeBps` | Endpoints before outward tick rounding |
| --- | --- | --- |
| +/-25% | `2500` | `0.75P` to `1.25P` |
| +/-50% | `5000` | `0.50P` to `1.50P` |
| +/-10% | `1000` | `0.90P` to `1.10P` |

The independently checked reference centres a replacement. Inversion produces an
asymmetric raw Uniswap range; outward rounding preserves the reviewed endpoints.
It does not promise half the assets in each token. Ordinary trigger math always
uses ZZZ-in-ETH price distance from actual main bounds, irrespective of this
range-orientation switch. With ideal +/-50% bounds the 85% trigger is +/-42.5%.
Side1/2 returned by `marketSides` remain raw-ratio directions: side1 means higher
ZZZ-in-ETH price, side2 lower. Main range membership still follows actual ticks.

## Scope and safeguards

A width restored to the old main's actual ticks can remove that width mismatch
**only if no portfolio geometry revision remains pending**. Portfolio mode and
active residual-width revisions are monotonic: enabling then disabling/restoring
values does not undo their pending reviewed replacement. Inspect
`configurationPending`, `geometryRevision(pool)` and `appliedRevision(main)`.
Trigger-only changes invalidate samples but do not create the manual exception.
Configuring an unused residual width while mode is off likewise does not force
single-mode replacement.

The old `triggerBps` PoolConfig field is retained for compatibility and bounds;
it does not control the new 85% threshold. Use Policy
`setTriggerBps(uint16 threshold,bytes32 reviewHash)`, where `8500` means 85% and
allowed values are 1–10000. This is separate from range width, source agreement,
spot deviation, execution loss and cooldown. A changed trigger needs fresh
review/samples; it is not an emergency bypass.

## Manual execution

A genuinely keeper-authorized wallet can call normal `Vault.rebalance`; governance
configuration permission alone is insufficient. Simulate from that exact caller
and preserve cooldown/ready, prices, minima and deadline. See [manual execution](OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time).
For a separately reviewed paused governance emergency, use [the emergency procedure](EMERGENCY_REBALANCE.md),
never an automatic workaround. An optional financial bypass may lose almost all
principal even while exact structural custody is preserved.

## Optional keeper selection: 25% or 50%

The retained automatic width capability is not the selected operating policy.
Keep `adaptive_range.enabled=false` and disable any on-chain policy through
`setKeeperRangePolicy(pool,false,0,0,0,bytes32(0))`. Enabled independent-reference
confirmation and automatic width policies are mutually exclusive. Do not relax
that protection merely to enable automation. Governance manual widths remain
available. [Detailed controls](OPERATOR_MANUAL.md#explicit-zzz-price-orientation-and-two-range-selection).

## Reinvesting attributed idle without dust churn

Attributed idle is the bucket's ETH/ZZZ outside physical LP, not available rewards,
royalties, buyback reserve or unclassified prefunds. It remains in NAV and can be
reinvested through eligible compounding/rebalancing or returned in collective exit.
No operator dust sweep or external recipient is introduced.

Fresh Budget compound capability4 retains a separate governed per-pool interval,
default 3600 seconds, supported 600 seconds–7 days. Every standalone compound
waits after `max(lastCompound,lastRebalance)` and yields to raw rebalance need.
The keeper also waits at the main's 85% physical threshold or pending geometry,
including during cooldown. It does not create/rebuild the residual independently.

Enabled compound jobs require positive `compound_thresholds` for both actual
currencies, in their own raw units. `compound_idle=true` is explicit opt-in; its
local interval remains an additional scheduling constraint. Use the reviewed
Budget, complete physical helper graph, runtime pins and [controlled service procedure](KEEPER_RECOVERY.md).
No policy read or threshold guarantees gas profitability. Hourly harvest and
funded claims keep separate controls. [Coordination](KEEPER_COORDINATION.md).

## Rewards, API and operations

Physical LP changes do not create new PoPL NFTs or reset earned rights. Both legs
feed the same 80/10/5/5 fee accounting; rarity affects received royalties only.
Consumers must select profile6, authenticate/sum both actual legs and distinguish
raw condition, cooldown, sampled readiness and service jitter. A manual repair
reports threshold-side evidence unavailable rather than fabricating a side.
Missing prices/ownership/partial inventory remain unavailable; guessed zero and
relabeled historical profiles are forbidden.

Future next-check/execute times require fresh matching worker telemetry; a poll
interval is not a promised deadline. Old profile4 outside-only timing and earlier
[range evidence](../reports/range-policy/VERIFICATION.md) retain their scope.
Source publication performs no deployment, service restart or website rollout.
