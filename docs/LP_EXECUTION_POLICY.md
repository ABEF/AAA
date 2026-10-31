# LP execution and operator-selected maintenance

Fresh [accounting6 / portfolio2](POSITION_V6.md) source candidate, started 30 October 2026.
**Undeployed; production NOT APPROVED.** Normal size/runtime gates, scoped offline
checks and local actual-v4-core integration pass within their
[recorded scope](../reports/residual-operations-20261031/VERIFICATION.md).
Live dependency, target-chain operations and independent review remain open.
[Implementation plan](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md)
and [sole Todo](../TODO.md#task-passive-inventory) own scope/status. Historical
[LP1 routing evidence](../reports/atomic-routing-20261028/VERIFICATION.md) and
[policy2 timing evidence](../reports/maintenance-policy-20261027/VERIFICATION.md)
retain their original source scope; they do not verify this fresh portfolio.

## Current behavior and requested direction

| Topic | Fresh source behavior |
| --- | --- |
| Contribution pool | One admitted native ETH/fixed-ZZZ destination at a time. Many PoPL NFTs own independent shares of the same bucket. |
| Physical positions | Default one main. Optional main plus at most one residual, both Vault-owned and in the same pool. No third leg or unbounded position accumulation. |
| Range | Governance selects the width, normally ±25%/±50% in ZZZ price in ETH. Leave automatic width selection disabled. |
| Ordinary trigger |85% of actual centre-to-main-boundary price distance on the same physical/reference side, with sampled confirmation and hard cooldown. |
| Operator changes | Deliberate width, mode or active residual-geometry changes apply at a guarded replacement after cooldown, including while the old main remains active. |
| Contributions | Balance/deploy only entrant funds into existing main ticks; preserve incumbent main/residual NAV, fee rights, centre and rebalance clock. |
| Harvest | Independent hourly service schedule; actual receipts allocate 80/10/5/5 without swaps. |
| Compound | Separate interval; reinvest attributed idle/designated reserve in the existing main. Service waits at the adjustment threshold or a pending configuration change. |
| Limits | Default contribution 2%, conversion 1%, maintenance 3%; each governed maximum 10%, separate gas and stronger caller/venue floors. |

## Requested rebalance confirmation buffer

Fresh `REBALANCE_CONFIRMATION_VERSION()==3` distinguishes the market condition,
elapsed execution cooldown and sampled readiness. The selected configuration is
**600 seconds confirmation, 240 second source checks, strict 300 second maximum
confirmed-observation gap, then durable 60–300 second service jitter**.
The initial pool cooldown remains 43,200 seconds (12 hours), a hard execution minimum.
Raw checks continue during cooldown. To avoid paying for samples throughout a
long wait, the fresh service enrolls ordinary on-chain observations only from
`earliestCooldown - duration - maximumGap` (initially the last 15 minutes).
An already-due candidate starts immediately. Pending recovery, foreign-record
clears and fault resets retain priority before that boundary. It does not erase
an existing record: the next observation naturally restarts a stale window.
Early readings are not credited as continuous confirmation. Construction still
starts with gap0: the sampled market-triggered path is stopped until reviewed
governance configuration. Deliberate mode/range geometry changes retain their
separate raw/cooldown-gated exception; use actual pause/permission/operation
controls to stop all ordinary execution.

The trigger is 85% of the actual price distance from the recorded centre to the
corresponding main boundary. It is not an 85% price change or a tick/square-root
fraction. Ideal unrounded ±50% bounds trigger at ±42.5%; ±25% at ±21.25%.
Actual outward-rounded physical bounds and conservative integer interpolation
are authoritative. The main can still be active at this threshold. A 1% movement
or imperfect centring is insufficient; legacy `triggerBps` is not this new setting.

`Strategy.rebalanceCondition(bucket)` and helper `condition(bucket)` can expose a
candidate during cooldown. `needsRebalance(bucket)` additionally requires the
hard interval; `rebalanceReady`/helper `ready` require both elapsed cooldown and
fresh mature samples. Manual width/mode/active residual-geometry changes have an
explicit exception to the sample window, never the ordinary hard cooldown or
price/execution guards. Manual repair does not require interpolating an old
centre that lies outside its physical bounds; its threshold-side diagnostics are
unavailable, not an invented ordinary candidate.

The keeper records authorized `observe(bucket)` transactions. Same-side identity,
physical main/residual IDs and bounds, price-policy identities and monotonic
control revisions must remain valid. Return inside the threshold, side reversal,
changed geometry/LP, stale gaps and observed relevant faults cancel evidence and
queued jitter. Off-chain faults require a durable clear-only reset and confirmed
`resetObservation` receipt; a failed transaction cannot persist a deletion.
Startup, observed pause and interrupted recovery keep their explicit reset rules.
Healthy feed rounds, harvesting and normal main contributions do not reset the
centre, hard clock or stable sample identity.

Checks normally occur at most 240 seconds apart in source. A known 600 second
maturity or cooldown boundary may schedule an earlier read. Pending recovery
comes first; known renewal/reset deadlines then precede optional nonce users.
Strict 300 seconds still depends on actual RPC, host and inclusion latency. Missing
that maximum restarts the window; there is no grace or promised execution time.

After readiness, the service draws and saves one OS-random delay of 60–300 seconds,
excluding the preceding chosen delay for that bucket. It does not promise every
delay will be unique forever. Routine checks/top-ups/harvest do not redraw it;
restart preserves it, while required recovery resets demand fresh evidence.
Continue samples through the wait and recheck at submission. Jitter is service
policy, not a contract restriction on a key running different code.

This is sampled evidence, not proof of every intervening price or MEV immunity.
Public observations reveal candidate activity. Independent prices, post-close
quotes, exact settlement and loss floors remain necessary. [Operator inputs](OPERATOR_MANUAL.md#configure-rebalance-confirmation).

<a id="independent-reference-in-confirmation2"></a>

### Independent reference in confirmation3

Ordinary samples normally require both the actual LP pool and
`Oracle.referenceX96` to cross the 85% threshold on the same side. Target-only,
reference-only and opposite-side conditions do not authorize replacement.
The reference uses the reviewed dual-source USD policies; this source change
neither installs a deeper-market feed nor qualifies source independence or a TWAP.

Side1/2 describe the raw native-first pool ratio. Side1 is a lower square-root
ratio and therefore a higher ZZZ-in-ETH price; side2 is the inverse. Do not label
side1 as a ZZZ-price fall in an operator display.

Governance can call `setRequireReferenceExit(required,reviewHash)` on the fixed
helper. Default true; every change invalidates samples through a monotonic
revision. Automatic keeper-width policies cannot coexist with enabled reference
protection; deliberate governance changes retain their manual exception.
[Emergency recovery](EMERGENCY_REBALANCE.md) remains separate, paused and
manually governed; optional financial bypass can lose almost all principal.

## Optional main and residual portfolio

Governance calls Policy `setMode(pool,bool enabled,reviewHash)`; default false.
Desired mode is independent of `secondaryId(main)`: enabled mode can have no useful
residual, and a disable request can coexist with an old live residual until the
next safe merge. `configurationPending(bucket)` and geometry/applied revisions
make that transition explicit. Changing a setting does not immediately trade.
Mode and active residual-geometry revisions are monotonic: switching mode and
then restoring its previous value still requires guarded replacement. Changing
the threshold resets observations without creating a manual replacement
exception. Configuring an unused residual width while mode is off likewise
does not force a single-mode replacement.

Ordinary `Vault.rebalance` closes the existing one/two legs and atomically rebuilds
the selected bounded portfolio. Hybrid sizing seeks the smallest qualifying swap
among bounded reviewed samples that meets minimumMainBps(pool), default60%, of retained principal in
the main. It does not maximize turnover or force a 40% residual. Actual final main
must meet the configured main floor6000–9999bps, with complementary residual ceiling, using Budget's captured starting price
vector; retained principal includes both legs and attributed idle. The separate
captured maintenance idle ceiling(default5%, governed0–40%) and maintenance-loss floor still apply. These are post-adjustment
requirements, not continuous portfolio ratios or new entrant allocation rules.
In both single and hybrid ordinary replacement, the actual stored pool tick
must place the new main in range before and after mint/refund callbacks. An
inactive main rejects and rolls back the whole replacement even if its USD value
passes. Initial activation/growth and explicit emergency have separate policies.
For very narrow bands, bounded route ranking may choose a candidate that the
final active-main guard rejects even when another reviewed venue could work.
This remaining liveness qualification is not permission to weaken the guard.
[Current audit](../reports/day-audit-20261031/REVIEW.md).

One excess asset may fund one residual range on the corresponding side of the
new main, leaving at least one tick-spacing beyond spot. Policy
`configureResidualSide(pool,bps,reviewHash)` chooses a fraction of that side's
ZZZ-in-ETH price distance; default 5000 uses half the corresponding side, while
10000 remains the governed full-side option. For main bounds50–150 around100,
the ideal residual spans75–100 or100–125 before spot-gap and tick rounding.
Actual rounded ticks, available inventory and deployment guards decide
whether a useful residual can exist. Tiny leftovers stay attributed idle; there
is no third position to absorb them. A filled/mixed residual remains accounted
until the next whole adjustment, including on reversals.

Disable with `setMode(pool,false,reviewHash)`. Continue valuing, harvesting and
closing both actual IDs until successful atomic merge into a single main. A
failed merge leaves the old portfolio and rights intact; never remove a live
residual from a reader/config to make single-mode status look applied.
[Exact procedure](OPERATOR_MANUAL.md#optional-main-and-residual-mode).

## Execution venue selection

The LP destination and balancing swap venue are separate. The bounded catalog
contains up to four admitted static hookless native ETH/fixed-ZZZ v4 pools. Quotes
run after withdrawing both old legs, so our removed liquidity cannot supply the
replacement swap. Direction/size, directional LP/protocol fees, traversed depth,
post-swap ratio and actual useful deployment are evaluated on-chain. Single-mode
comparison maximizes sampled useful deployment; hybrid comparison seeks a
qualifying main allocation with limited swap size. Neither is a global optimum.

Manager/Balancer `LP_ROUTING_VERSION()==2`, their fixed arithmetic/physical
executor children, reciprocal parents and exact core/state/PosM/Permit2/runtime
pins identify the fresh capability. The Balancer and Strategy helpers are
standalone fixed-controller companions: their parent resolves the sealed Access
module, without a mutable parent setter. `ZZZLPPositionExecutor` is a fixed typed
contract, not a new human operator, generic executor or external custodian.

Governance admits a compatible future pool through
`PoolRegistry.configureNative(fullConfig)`, normally with deposits disabled.
Then it supplies the complete catalog to Balancer
`configureExecutionPools(ids,reviewHash)`. Admission alone does not select a
swap route; changing the swap catalog does not move the LP destination.
An empty list disables swaps with no implicit target fallback and can be set
without healthy venue calls. Entry and reward converters keep separate routes.

Zero or one real balancing swap executes; quote effects revert. Exact input,
output, post-swap state, approved recipient, captured policy/price controls and
final value checks must pass. Governance can set bounded solver iterations4–12
and quote gas100,000–300,000; defaults8/200,000 are not gas qualification.
More venues/iterations can cost more; unavailable quotes cannot waive a floor.

## Deterministic execution and adjustable economics

Defaults remain 2% contribution,1% conversion and 3% maintenance, each governed up to
10%, separate gas. Venue slippage is governed1–1000bps; spot/reference deviation
is separate from the selected 3% two-source agreement. Stronger target/venue,
captured operation and caller floors all remain. Strategy's default 1% additional
oracle-relative loss excludes known directional trading fees, but those fees
still count under all-in limits. Source spread, rounding and price uncertainty
consume budget too. [Exact policies](EXECUTION_LOSS_POLICY.md), [fee-aware floor](EXECUTION_QUALITY.md).
No failure automatically widens a parameter or permits an arbitrary recovery swap.

<a id="implemented-outside-only-upkeep-policy2"></a>

## Historical outside-only policy2

Profile 4/policy2 used actual physical range exit,900 second confirmation after
cooldown and 60–600 second service jitter. Those deployments/readers/journals keep
their old behavior. Fresh profile6 uses the 85% threshold and 600/300/240 policy
above. Never change an old version field or journal namespace to acquire it.
[Historical profile](POSITION_V4.md).

## Direct manual execution

An actually keeper-authorized wallet may call
`Vault.rebalance(bucket,minimumLiquidity,deadline)` without Python jitter or its
poll schedule. Governance alone is not a keeper grant. All ordinary on-chain
cooldown, confirmation/explicit configuration exception, price, custody and
financial checks still apply. Coordinate the service and recover pending hashes;
a same-key transaction outside its journal requires nonce/receipt/spend
reconciliation before restart. [Manual procedure](OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time).

## Harvest, compound and contributions

Hourly harvest collects actual fees from both live legs and applies80/10/5/5.
The reserve allocations are accounting domains, not payments to new addresses.
Claims trigger neither compounding nor buybacks. Receipt-backed internal harvests
may coalesce the worker's local harvest clock; submission or a NAV change cannot.

Budget capability4 uses its separate compound interval after
`max(lastCompound,lastRebalance)` and yields to raw rebalance need. Source keeper
policy additionally waits when the main crosses the 85% physical threshold, is
outside its physical range, or width/mode/geometry is pending, including during
cooldown. Compound reinvests into the existing main; it cannot independently
mint a new residual. Positive raw-unit thresholds are required per actual currency;
idle scheduling remains explicit opt-in. [Coordination](KEEPER_COORDINATION.md).

Contributions swap/deploy entrant budgets into actual main ticks. Existing
main/residual amounts, attributed idle and eligible compound remain incumbent
NAV; they cannot mask an underdeployed entrant. Final marginal LP/caller/price
checks remain atomic. Wait for confirmed actual LP increase before updating
artwork/value. Approval alone does not activate or grow an NFT.

## Price authority and dependency upgrades

Pool state and configured oracle answers are read on-chain. Pool spot describes
actual execution; independently reviewed references constrain manipulation.
Higher TVL, two addresses or code hashes do not prove independent markets or
freeze upstream proxy/admin behavior. Review and monitor those dependencies;
no same-pool, single-source or presumed-peg fallback is selected.

## Timed 10% replacement versus a price TWAP

No staged 10% replacement or timed trade slicing is added. A TWAP averages prices;
several same-transaction slices do not average time or remove AMM impact.
The optional residual is a bounded portfolio, not permission to accumulate old
ranges or execute an unbounded passive strategy. Actual MEV/economic comparison
and a qualified independent reference remain release work.

## Operator configuration and verification

Use [range instructions](RANGE_POLICY_UPDATES.md), [mode instructions](OPERATOR_MANUAL.md#optional-main-and-residual-mode)
and [schema8 preflight](PRODUCTION_PREFLIGHT.md). On-chain setters normally need
no host restart; local JSON/source/runtime/endpoint changes require a controlled
matching rollout. Preserve submitted intents and original journals. Publication
performs no deployment, live restart, website rollout or public transaction.
