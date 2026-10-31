# Fee-aware execution quality

The current candidate retains an independent limit on oracle-relative execution
loss **after known trading fees**, alongside the existing all-in loss controls.
It does not discount those fees from contribution, maintenance, venue or caller
limits. [Review](../reports/fee-impact-policy-20261028/REVIEW.md) and
[verification](../reports/fee-impact-policy-20261028/VERIFICATION.md) record the
source scope and remaining qualification. Production is **NOT APPROVED**.

Fresh source uses accounting6, maintenance3, confirmation3 and optional portfolio2.
Ordinary samples require the physical pool and independent reference on the same
85%-of-centre-to-boundary threshold side in ZZZ-in-ETH price, using actual rounded
main bounds. This threshold can be reached while the main remains active. The
600-second sampled window may accumulate during the hard twelve-hour cooldown;
execution needs both, then one persisted 60–300-second keeper delay. Source checks
are 240 seconds; the configured maximum confirmed gap is 300 seconds. A gap-0 helper
is unconfigured and cannot authorize ordinary sampled execution. Earlier
maintenance2/confirmation2 deployments retain their outside-only policy and selected 900/300 settings; other historical profiles stay explicit.

A separate paused governance emergency capability2 may explicitly bypass chosen
financial/timing checks; exact custody/accounting remain, but near-total economic
loss is possible. It is not an automatic keeper fallback or API signing feature.
Live independent sources/routes remain unqualified. [Execution policy](LP_EXECUTION_POLICY.md),
[optional portfolio](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md), [emergency procedure](EMERGENCY_REBALANCE.md).

## Policy and scope

`ZZZStrategy` owns `additionalLossBps`, initially 100 bps (1%). Governance calls
`setAdditionalLossBps(uint16 limit,bytes32 reviewHash)` with a nonzero review hash.
The permitted range is 0–1000 bps (0–10%); zero is valid but can make execution
unavailable because source spread and rounding still consume headroom. Every
successful call increments `executionQualityRevision`, including changing a
setting back to its old value. There is no automatic widening after a failure.
See the [operator procedure](OPERATOR_MANUAL.md#set-additional-execution-loss).

The guard covers LPBalancer balancing and LiquidityManager direct swaps,
including buyback swaps. Balancing still selects among its bounded reviewed
venue list; this does not give buybacks the same automatic route selection.
Separate V3/V4 LP-reward and royalty converters retain their existing all-in
conversion policy (default 1%) and caller floors. They do not acquire this new
global additional-loss policy.

## Calculation

For the actual static, hookless v4 execution pool, read its current directional
protocol fee and verify its LP fee against the admitted PoolKey. Fees use
millionths; the additional-loss setting uses basis points. For raw input `a`:

```text
f        = protocolFee + lpFee - floor(protocolFee * lpFee / 1_000_000)
netInput = floor(a * (1_000_000 - f) / 1_000_000)
Q(x)     = floor(floor(x * inputUpperUSD / inputScale) * outputScale / outputLowerUSD)
extraMin = ceil(Q(netInput) * (10_000 - additionalLossBps) / 10_000)
grossMin = floor(Q(a) * (10_000 - grossVenueLossBps) / 10_000)
```

`Q` uses validated independent USD bounds: upper input value and lower output
value make the required output conservative. The fee-adjusted minimum rounds
up after the two quote divisions. The effective output requirement is the
maximum of `extraMin`, the existing gross venue floor and the positive submitted
minimum. Balancing retains the tighter target/selected-venue gross setting.
Actual-core quotes must pass the floor; settlement checks actual receipts and
revalidates price and captured policy. Full-operation retained/deployed-value
guards and stronger caller limits remain independent.

For example, a 1.101% combined pool fee followed by 1% additional loss permits
about 2.08999% total loss at an identical reference price before raw-unit
rounding. A 2% gross venue limit remains stronger in that example. Raising the
new setting therefore cannot bypass a tighter old guard or guarantee execution.

“Additional loss” is measured against the independent price bounds. It can
include market spread, source uncertainty, rounding and price impact; it is not
a pure measurement of AMM price impact. Known fees remain a real economic cost.
Network gas is separate.

## Explicit capability and observations

Manager, LPBalancer and Strategy advertise `EXECUTION_QUALITY_VERSION()==1`.
Fresh LP routing2 uses quality1 and a separately pinned, fixed BalanceMath child;
the typed PositionExecutor mints/updates the actual Vault-owned LPs. Historical
routing1/quality1 remains explicit, while absent/zero retains its older reads.
Neither an old deployment nor a saved journal acquires the fresh portfolio graph
through a version rename. Keeper/API configs explicitly set their full profile.

Quality1 observations use one pinned block, checked runtime/module bindings and
the real Strategy resolved through Access. They compare its policy with the
Balancer's forwarded value. The API reports `policy_owner`, `quality_policy_revision`,
the cap and maximum. Fresh health schema2 exports confirmed block/config/runtime
metadata and separates last success from current unavailable state. File hashes
are not running-code attestation. The helper's `executionRevision` remains its separate
catalog/solver revision. Strategy's monotonic quality revision is included in the
Balancer policy fingerprint, detecting changed-and-restored policy during an
operation. No journal or historical deployment is relabeled.

An unsigned wallet review reports the observed policy; it does not freeze that
policy until inclusion. The caller's signed maximum contribution loss remains
binding. Keeper validation likewise checks policy owner/revision without replacing
inclusion-time checks. Implemented source-anchored telemetry and block/config-local
read caching require matching writer/checker operating qualification; fresh
pre-signing checks are not cached. [Evidence](../reports/practical-improvements-20261028/VERIFICATION.md).

## Optional portfolio execution

Mode is disabled by default. When enabled, the residual uses half of the
corresponding main side (`5000`) with at least one full tick-spacing gap; governance
may review a fraction from 1 to 10000, including full 10000. It is not a forced 40% allocation. A whole
adjustment harvests/closes both old legs before quoting, so the route observes
liquidity actually remaining after our withdrawal. LP destination and swap venues
remain separate reviewed choices.

A naturally deployable main of at least 60% needs no balancing swap. Otherwise the
partial solver seeks a qualifying small swap, using a captured USD vector for
post-cost utilization and current validated bounds for financial execution floors.
Quoted sizing uses one basis point of headroom; the final actual main minimum
is the configured minimumMainBps(pool), default6000bps. The solver adds headroom; it does not change the actual floor. At most one swap and one residual are permitted. Search
is bounded rather than a proof of the globally smallest or best trade.

After actual mint, Budget values main/residual/attributed idle at the SAME captured
prices: main meets the configured floor(default60%), residual stays below its
complementary ceiling, idle meets the captured maintenance cap(default5%), plus the
unchanged aggregate maintenance loss floor. The ordinary hybrid main must have
an active actual physical tick before mint and after final mint/refund callbacks,
not merely enough NAV in an out-of-range position.
Financial floors and structural ownership/balance checks remain independent.
Later market movement may change activity, inventory and allocation. Entrant
contributions still fund only their marginal main increase, never repair old
residual/idle with a new user's budget. Standalone compounding keeps its separate
interval and does not acquire replacement/residual-mint permission.

## Fresh deployment and failure boundaries

Accounting6/ProtocolPolicy1/Portfolio2/maintenance3/confirmation3/compound4 and the new fixed companions are
fresh source/deployment boundaries, never an upgrade or relabel of preserved
Anvil contracts. Standalone children have explicit parent/controller bindings;
normal runtime/initcode gates still apply. Use the exact compiler/runtime graph.
Direct Manager swaps/buybacks now capture the complete policy/source/target
context before the input pull and recheck it after settlement. Consequently a
constructible configured target range is required; near extreme TickMath prices
that can reject a swap that spot validation alone would have allowed. This also
adds context reads. Do not bypass failed range/price/policy checks.
A positive weak caller minimum is raised to the protocol floor; zero still
rejects and a stronger caller minimum still binds.

## Limits of the protection

The guard constrains accepted execution; it does not prove feed independence,
provider authenticity, organic prices, globally optimal routing or resistance
to profitable surrounding trades. Qualified feeds, actual routes/depth/gas,
ordering and operating rehearsals remain open. The optional one-residual policy
reduces some immediate balancing demand; it does not remove IL, sandwiching or
adverse selection. No automatic volatility policy, staged TWAP execution or 40%
displacement strategy is introduced. Source/configuration changes do not update
installed services, sites, existing deployments or journals.

Sources: [Strategy](../src/ZZZStrategy.sol), [LPBalancer](../src/ZZZLPBalancer.sol),
[LiquidityManager](../src/ZZZLiquidityManager.sol),
[PositionExecutor](../src/ZZZLPPositionExecutor.sol), [BalanceMath](../src/ZZZLPBalanceMath.sol),
[reader](../zzz_ops/lp_execution.py), [loss policy](EXECUTION_LOSS_POLICY.md) and
[keeper safeguards](KEEPER_SAFEGUARDS.md).
