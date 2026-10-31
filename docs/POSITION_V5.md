# Accounting5: bounded main and residual LP

Historical source profile, started30October2026; the current candidate is [accounting6](POSITION_V6.md). This page retains its original version boundaries; **production NOT APPROVED**.
Normal size/runtime gates, focused offline reader/keeper checks and scoped local
actual-v4-core integration methods pass. The latter use real local PoolManager,
PositionManager and StateView with explicit mock feeds/access/VRF/Permit2 and
Registry admission/failure seams; they do not qualify live dependencies or host
operation. [Exact verification scope](../reports/residual-operations-20261031/VERIFICATION.md),
[implementation plan](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md) and [sole Todo](../TODO.md#task-passive-inventory)
retain operating qualification and independent audit as open work.
No existing deployment, service, website or journal is upgraded by this document.

## Exact profile

| Boundary | Fresh value |
| --- | --- |
| Vault accounting | `ACCOUNTING_VERSION()==5` |
| Residual-only management | Additional `RESIDUAL_EXIT_VERSION()==1` on Migration, Vault, Manager and position child; exact reviewed current runtimes required. No Position/custody wire change. |
| Migration custody / emergency | `CUSTODY_VERSION()==4`, `EMERGENCY_REBALANCE_VERSION()==2` |
| Strategy maintenance / confirmation / portfolio | `3 / 3 / 1` |
| Budget compound / confirmation / emergency | `4 / 3 / 2` |
| Manager / Balancer LP routing | `LP_ROUTING_VERSION()==2` |
| Manager portfolio / emergency | `1 / 2` |
| Fixed position executor / arithmetic child | `LP_POSITION_EXECUTOR_VERSION()==1`, `LP_BALANCE_MATH_VERSION()==1` |
| Execution quality / governance / fee intake | `1 / 2 / 1` |
| Entry routing / pricing / reviewed Entry | `2 / 2 / 1` |
| Production inventory | Schema7, 17 modules and 20 helpers |
| Canonical wire | `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5` |

The eight Position words remain `poolId, lpTokenId, idle0, idle1, depositUSD,
centerX96, lastRebalance, status`. `lpTokenId` is the actual main Uniswap NFT,
never a synthetic portfolio ID. Statuses remain None0, Active1, reserved
Outbound2, Dormant3, Parked4 and Exited5. Eight-word length does not select a
profile. [Profile 4](POSITION_V4.md) and older deployments retain their own codecs.

## Physical portfolio and value

Single-main mode is the default. Governance may enable one additional residual
position through the fixed [PortfolioPolicy](../src/ZZZPortfolioPolicy.sol).
`Manager.secondaryId(main)` is zero or one actual auxiliary ID; both NFTs belong
to Vault and use the bucket's same native ETH/fixed-ZZZ pool. There is no third
leg or unbounded list. A filled residual stays accounted until the next whole
adjustment; it is not independently replaced on every price reversal.

`amounts(actualId)` returns one physical leg's token amounts.
`portfolioAmounts(main)` sums both legs. Sum ETH/ZZZ amounts and their values,
**not raw Uniswap liquidity across different ranges**. NAV/share pricing,
contribution checkpoints, metadata, maintenance and readers must use both legs.
Contributions increase the existing main at its actual ticks using entrant funds;
they do not recenter it, rebuild the residual or reset its rebalance clock.

After an ordinary hybrid replacement, actual main value must be at least 60% of
retained principal and residual value at most 40%, using Budget's starting price
vector. Retained principal includes both physical legs and attributed idle.
In every ordinary replacement, single or hybrid, the actual stored pool tick
must leave the new main active before and after mint/refund callbacks; an inactive
main fails atomically even if its marked value passes. The executor-only
`executionOrdinaryReplacement()` context is false outside the captured normal
Budget operation. Initial activation/growth and explicit emergency stay separate.
The separate 5% idle ceiling and operation-loss floor still apply. This does not
force 40% into the residual, constrain every later market valuation, or impose a
60/40 split on an incoming contribution. These constants are not governance
setters. [Operator mode procedure](OPERATOR_MANUAL.md#optional-main-and-residual-mode).

## Trigger, observations and timing

Ordinary adjustment uses 85% of actual centre-to-main-boundary **ZZZ-in-ETH price
distance**, not an 85% change in token price, ticks or square-root price. With
ideal unrounded ±50%/±25% bounds, examples are±42.5%/±21.25%; actual rounded
bounds govern. Physical and independent-reference thresholds normally must cross
on the same side. The selected policy records 600 seconds of sampled confirmation,
checks every 240 seconds, and restarts after any confirmed gap greater than 300 seconds.
Raw checks continue during the hard 12-hour execution cooldown. Paid ordinary
observations enroll only from `earliestCooldown - duration - maximumGap`, initially
15 minutes before eligibility; an already-due candidate enrolls immediately.
Earlier checks do not count as a sampled confirmation window. Required foreign
record clears, fault resets and pending recovery remain higher priority.
The service draws
one durable 60–300 second delay only after readiness; it rechecks while waiting.

`rebalanceCondition`/`condition` can therefore show a candidate before
`needsRebalance` and `ready` allow execution. A deliberate width/mode/active
residual-geometry change retains its manual exception after cooldown. Threshold
interpolation is unavailable for that exception; healthy price/tick checks and
other ordinary execution guards remain. Side1/2 are raw pool-ratio sides: with
native ETH currency0, side1 means a **higher** ZZZ-in-ETH price, side2 a lower one.
[Complete timing policy](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer).

## Identity, custody and recovery

`portfolioFingerprint(main)` binds stable physical IDs, complete keys/bounds and
custody. Normal main liquidity increases do not reset samples. The separate
`executionPortfolioFingerprint(main)` also binds both current liquidity amounts;
parking and emergency custody reviews must use this stronger live manifest.
Mode/geometry/trigger revisions invalidate candidates and unsigned reviews,
without deleting submitted transaction truth.

Budget, Balancer, PortfolioPolicy and Confirmation are separately deployed fixed
controller companions. Their parent getters resolve the sealed Access module and
reciprocal binding; there is no mutable parent setter. Manager's fixed typed
`ZZZLPPositionExecutor` handles physical LP actions and owns the main/secondary
association. It is a contract, **not another human operator role**. Its immutable
Manager/core/state/PosM/Permit2/router wiring and the Balancer's arithmetic child
require exact runtime/version checks. No delegatecall or generic executor is added.

Harvest/close act on all live legs. Parking, pool movement, emergency recovery and
collective holder return cannot leave an auxiliary behind. Canonical V5 is retained
only with all physical LP closed into classified parked backing before export;
no live residual is imported through that wire. Terminal exit still preserves
NFT transfers, old funded rewards and future royalties. No bridge, external
custody address, new contribution asset, economic split or public signing is added.

Use [schema7 preflight](PRODUCTION_PREFLIGHT.md), the [operator manual](OPERATOR_MANUAL.md),
and exact source-bound verification before any separately authorized deployment
or rollout. Historical evidence does not qualify the new portfolio implementation.

## Manual residual-only recovery

The [Operator manual](OPERATOR_MANUAL.md#portfolio-management-controls) covers paused governance
Migration.closeResidual, reviewed raw minima and shared parking nonce/epoch.
Both legs harvest before only the residual burns. Actual ETH/ZZZ enters the same
bucket's attributed idle; main LP/shares/centre/clock and desired policy remain.
Subsequent entrant/deployment/loss checks are not relaxed. This capability does
not exist in earlier accounting5 binaries merely because their tuple matches.
