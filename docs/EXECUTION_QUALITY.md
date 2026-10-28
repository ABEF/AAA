# Fee-aware execution quality

The current candidate adds an independent limit on oracle-relative execution
loss **after known trading fees**, alongside the existing all-in loss controls.
It does not discount those fees from contribution, maintenance, venue or caller
limits. [Review](../reports/fee-impact-policy-20261028/REVIEW.md) and
[verification](../reports/fee-impact-policy-20261028/VERIFICATION.md) record the
source scope and remaining qualification. Production is **NOT APPROVED**.

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
This capability is separate from `LP_ROUTING_VERSION()==1`; existing LP-routing1
deployments do not gain it through a configuration rename. Fresh keeper/API
configs explicitly set `execution_quality_version:1`. Historical absent/zero
configurations retain their old reads and never probe these new getters.

Quality1 observations use one pinned block, checked runtime/module bindings and
the real Strategy resolved through Access. They compare its policy with the
Balancer's forwarded value and report `policy_owner`, `quality_policy_revision`,
the cap and maximum. The helper's `executionRevision` remains its separate
catalog/solver revision. Strategy's monotonic quality revision is included in the
Balancer policy fingerprint, detecting changed-and-restored policy during an
operation. No journal or historical deployment is relabeled.

An unsigned wallet review reports the observed policy; it does not freeze that
policy until inclusion. The caller's signed maximum contribution loss remains
binding. Keeper observations likewise report policy owner and revision, without
claiming that an old off-chain observation replaces inclusion-time checks.

## Fresh deployment and failure boundaries

Strategy's new policy fields shift the old mapping storage offsets. This is a
fresh undeployed contract layout, never an upgrade or relabel of preserved
Anvil deployments. Use exact new compiler/runtime and immutable bindings.
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
ordering and operating rehearsals remain open. No TWAP, passive inventory
strategy or new 40% displacement trigger is introduced. Source/configuration
changes do not update installed services, websites, existing deployments or
transaction journals.

Sources: [Strategy](../src/ZZZStrategy.sol), [LPBalancer](../src/ZZZLPBalancer.sol),
[LiquidityManager](../src/ZZZLiquidityManager.sol),
[reader](../zzz_ops/lp_execution.py), [loss policy](EXECUTION_LOSS_POLICY.md) and
[keeper safeguards](KEEPER_SAFEGUARDS.md).
