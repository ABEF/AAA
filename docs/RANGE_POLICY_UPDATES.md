# Applying range settings after sealing

Governance can change the admitted pool's range through direct calls from the selected governance wallet.
The keeper can then apply it through the ordinary `Vault.rebalance` path even
while the old position is still within its physical range. A separate,
default-disabled policy lets it select **only** the reviewed 25%/50% presets under
governance-approved rules. Selecting a width and moving physical LP are distinct
transactions; neither gives the keeper general configuration or custody power.

The following is an undeployed candidate. [Earlier scoped evidence](../reports/liquidity-operations-20261025/VERIFICATION.md)
and [remaining release gates](../TODO.md) distinguish implemented controls from
actual provider, strategy/backtest and operating qualification.

## Selected operating policy and source versions

Fresh `MAINTENANCE_POLICY_VERSION()==2` requires the configured hard cooldown,
then actual physical range exit or an explicit desired-width/orientation change.
Initial intended cooldown is12hours. Manual +/-25/50% widths are selected; leave
optional automatic selection disabled. The matching keeper adds durable60-600s
jitter, hourly ordinary checks while eligible but inside, and fast receipt/health/
harvest observation. Source behavior does not install configuration or services.
Budget capability3 has a separate compound interval. [Operator procedure](OPERATOR_MANUAL.md#operator-selected-lp-policy),
[policy and limitations](LP_EXECUTION_POLICY.md), [verification](../reports/maintenance-policy-20261027/VERIFICATION.md).

## From approval to execution

1. Governance reviews the complete pool configuration and executes the exact
   selected-pool `PoolRegistry.configureNative` call. Bootstrap
   and keeper addresses cannot perform these complete configuration calls after
   sealing. The controller has no
   mandatory governance time delay; review and the maintenance cooldown are
   distinct controls.
2. After governance executes, `Strategy.rangeUpdatePending(bucket)` compares
   the current physical LP's ticks with the configured target calculated at
   the bucket's **recorded creation/rebalance center**. Using today's price for
   this comparison would cause needless repeated replacements as prices drift.
3. `needsRebalance` requires an active funded position, enabled operations,
   the configured cooldown and a fresh reference price. Either
   actual physical range exit or this range mismatch can then make it eligible.
4. The existing keeper discovers that shared bucket and submits the ordinary
   rebalance. Vault's keeper/lifecycle/pause, deadline, price/deviation,
   swap/close/mint minimums, the **captured governed maintenance-loss budget**
   (default 3%, maximum 10%) and **5% idle ceiling** remain in force. Network gas
   is separate. Later governance changes do not relax an already captured budget.
5. Successful replacement records the new physical LP, center and cooldown
   checkpoint. The mismatch clears. Any failed execution rolls back custody,
   accounting and the old position; the desired range remains pending.

## Explicit price direction

`Strategy.RANGE_POLICY_VERSION()==1` exposes `rangeOrientation(poolId)`:

- **Mode 0:** historical token1 per token0. Existing deployments/configurations
  remain in this mode unless governance explicitly opts in.
- **Mode 1:** token0 per token1. With the native ETH/ZZZ key, this is **ZZZ priced
  in ETH**, the usual token-price view requested for the new presets.

Governance calls `setRangeOrientation(poolId,1)` to opt in. This changes the
desired range and historical displacement orientation; it does not rewrite
existing physical ticks, historical LP values or NFT rights. Inspect
`rangeUpdatePending` and apply the normal rebalance when eligible. A direction
change disables an active automatic policy and requires a separate new review.
The versioned API/inventory profile must read and verify the intended direction;
old profiles make no new getter calls and retain their raw-price interpretation.

Supported examples around the independent oracle's reference price `P` in the
**selected direction**:

| Reference interval | `rangeBps` | Endpoints before outward tick rounding |
| --- | --- | --- |
| Minus/plus 25% | `2500` | `0.75P` to `1.25P` |
| Minus/plus 50% | `5000` | `0.50P` to `1.50P` |
| Minus/plus 10% | `1000` | `0.90P` to `1.10P` |

The center remains a fresh independent oracle reference, with the ordinary
spot/deviation checks. It is not an unchecked venue spot or a USD peg. In mode 1,
the desired 50% ETH-per-ZZZ interval is converted into the corresponding
asymmetric raw Uniswap interval before outward tick rounding. Lower denominators
round up and upper bounds round outwards so inversion cannot trim an endpoint.
It is not a promise to hold half the capital in each token. A config change that rounds
to the same ticks needs no replacement. Changing slippage or deposit limits
alone does not create a range-update trigger. Contributions use the current
physical ticks until replacement. Fresh capability3 standalone compounding also
uses those ticks but waits whenever rebalance or adaptive range selection is due.

## Scope and safeguards

The comparison always resolves the bucket's current pool and physical LP ID.
There is no stored update request that can accidentally refer to a retired LP,
be replayed, or require a cancellation nonce. Before execution, governance may
restore the configuration matching the deployed range; this clears the pending
mismatch. After replacement, another width change requires another governed
configuration and remains subject to the cooldown. Actual physical range exit
can still authorize policy2 rebalance; a separate movement trigger belongs only
to explicit historical policy1.

## Manual execution

Use [the manual rebalance procedure](OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time)
for exact caller, shared bucket, simulated raw LP minimum, short expiry and
separate gas. Direct `Vault.rebalance` skips service jitter/hourly checks, never
contract cooldown or range/operator-update eligibility. Governance must also be
keeper-authorized to call it. Reconcile service pending work and any same-key
out-of-band nonce before restarting; the physical LP/timer refresh alone cannot
repair a stale signer journal.

## Optional keeper selection: 25% or 50%

Governance first selects mode 1 and one of `rangeBps=2500`/`5000`, then reviews
and calls:

`Strategy.setKeeperRangePolicy(poolId,true,narrowTriggerBps,widenTriggerBps,minInterval,reviewHash)`

No automatic thresholds are chosen by the contract or example configuration.
The enabled policy requires `0 <= narrowTriggerBps < widenTriggerBps < 2500`,
a 600-604800-second interval at least as long as the pool's existing rebalance
cooldown, and a nonzero review hash. Existing `triggerBps` and spot-tolerance
settings must fit the narrower 25% width. Store the real reviewed parameters,
price direction, strategy tests and expected costs behind that review hash.

The rule measures **current reference-price displacement from the physical LP's
recorded center** in mode 1:

- A deployed 50% range may select 25% when displacement is at or below the
  approved narrow threshold.
- A deployed 25% range may select 50% when displacement is at or above the
  approved widen threshold.

This is a bounded price-displacement rule with hysteresis and cooldown. It is
not a continuously sampled volatility model, evidence of a quiet trading window
or a guarantee the LP stays in range. The policy also requires an active funded
bucket, fully applied current ticks, enabled operations, fresh prices and both
the policy and ordinary maintenance cooldowns. A pending range replacement must
finish before the policy can choose another width.

`keeperRangeTarget(poolId)` returns `0`, `2500` or `5000`. With explicit
`adaptive_range={"enabled":true,"policy_version":1}` and reviewed Strategy/Pool
Registry runtime pins, the keeper validates the policy and submits
`Strategy.applyKeeperRange(poolId)`. It supplies **no width argument**. Strategy
derives the allowed choice and calls the Registry's fixed-Strategy-only range
callback; all other parameters, assets and flags remain unchanged. The successful
Strategy event records old/new widths and the review hash. The next ordinary
rebalance applies the new ticks under all existing guards. Allow for this serial
two-step scheduling and separately fund both transactions' gas.

The policy fingerprint includes price direction and every PoolConfig field
except width. Changes to flags, venue identity, limits, trigger, slippage or
cooldown make it ineligible until governance reapproves the policy. Width-only
manual changes can remain compatible: disable the automatic policy first if
you intend a purely manual range. Governance disables it with
`setKeeperRangePolicy(poolId,false,0,0,0,bytes32(0))`; this needs no healthy price
or venue read. Audit fields persist. Global pause, preparation and canonical
locks stop keeper selection; stopping pool operations also stops it. Disabling
the policy does not undo a selected or physically deployed width.

The example keeps this option disabled. No current service or journal is
changed automatically. Neither narrow nor wide selection authorizes a different
pool, arbitrary width, new token, oracle update, bridge or external custody exit.

Execution uses the **current** approved configuration. The existing keeper
transaction contains bucket, minimum liquidity and deadline, not a configuration
hash or physical-LP-version lock. Operators must resimulate after configuration
or position changes. A signed transaction can still execute if the new current
state satisfies every guard. This is deliberate reuse of the existing governed
policy, not an exact historical-policy execution promise.

The range-mismatch comparison has no state-changing external calls.
Missing position data, malformed intervals and invalid target arithmetic fail
closed. A wider target near Uniswap's extreme tick limits can be unrepresentable;
governance must simulate the target and keeper transaction before approving it.
Cooldown and the per-operation loss cap do not prevent cumulative costs from
repeated governance-approved changes. Production parameter/backtest, MEV and
operating qualification remain required. This code must be included before
sealing a deployment; it cannot patch an already sealed strategy.

## Reinvesting attributed idle without dust churn

The current candidate's ordinary `compound` call can also reinvest the bucket's
own attributed idle. It preserves NFT share ownership, fee/royalty liabilities,
captured maintenance loss and deployment minima. This is not an administrative
sweep or a withdrawal: principal stays in the shared LP or its attributed idle
ledger. Raw donations, other buckets' cash and claim reserves are excluded.

Keeper idle scheduling is disabled by default. Fresh accounting4 due compounds,
including reserve-only jobs, require an exact `idle_compounding_budget` address
and `code_hashes.idle_compounding_budget`. The keeper verifies runtime, mutual
Vault binding and `IDLE_COMPOUNDING_VERSION()==3` for policy2, then reads `compoundReady`.
Explicit historical policy1 retains its helper2 reader.
To additionally use attributed idle, set `maintenance.compound_idle=true`,
`compound_thresholds` for **both actual pool currencies** and an explicit
`compound_interval_seconds` from600to604800. Currency zero is native ETH under
the explicit profile. Historical accounting1/2/3 retains its original helper1
reader and journal; changing a version field never upgrades an old deployment.

Thresholds are positive **raw units per currency**, such as independently chosen
ETH-wei and ZZZ-unit amounts. They are never summed across currencies or inferred
from a shared decimal count. An incomplete map stops that bucket's compound
attempt. The keeper combines only that currency's attributed idle and compound
reserve. It waits for both its confirmed local checkpoint/interval and the
on-chain Budget decision, including work by another keeper. Capability3 requires
`now >= max(lastCompound,lastRebalance) + compoundInterval(poolId)` for all
standalone compounds, including no-swap work and immediately after LP creation.
It yields to eligible `needsRebalance` or nonzero `keeperRangeTarget`. Rebalances
retain their existing eligibility and ignore `lastCompound`, so a compound cannot
delay needed range replacement. This read is not authorization or a guarantee
that the complete transaction will succeed. A threshold is a scheduling rule,
not a gas/value profitability guarantee: review simulated costs and turnover.

If the on-chain adaptive policy offers a selection but local `adaptive_range`
is disabled, standalone compounding remains deferred. Enable the reviewed job,
or deliberately review and disable/change the on-chain policy; do not bypass the
priority check. Independent harvesting, claims and guarded user contributions
continue under their own controls and do not reset this standalone wait.

The old `minimum_compound_units` remains a compatibility option for reserve-only
profiles; one raw value across different decimals is unsuitable as a production
economic policy. No threshold or idle option is activated in an existing service
by updating this documentation/example. Existing pending journals are preserved.
Retired `reward_routes` cannot schedule bridge transactions; remove a nonempty
legacy list from configuration after reconciling any saved transaction. Recovery
of an existing hash runs first and does not resend or delete it.

## Rewards, API and operations

NFT ownership, bucket share counts and LP/royalty ledgers are unchanged by this
feature. Ordinary rebalance still harvests before closing and keeps accrued
claims attached to their PoPL NFTs. New physical Uniswap IDs do not create new
PoPL NFTs or reset claims.

Confirmed activation/approval responses include `range_update_pending` and
`eligibility_reason` (`range_update`, `price_trigger`, `price_and_range`, or null).
The reason describes the observed trigger even while cooldown blocks execution.
Fresh policy2 uses reasons out_of_range/range_update/out_of_range_and_range_update,
with obsolete price trigger fields null; explicit historical policy1 retains
the listed movement reasons. The API checks eligibility against cooldown and
profile-specific actual observations at
the same pinned hash. Missing/malformed getters fail closed; manifests must bind
the matching Strategy runtime. Ordinary rebalance retains its call and role; optional selection uses the separately versioned call above.
`next_keeper_check_at` and `expected_execution_at` remain null without qualified
fresh telemetry. A polling interval is not a guaranteed rebalance schedule.

See the earlier [scoped verification](../reports/liquidity-operations-20261025/VERIFICATION.md)
and [review](../reports/liquidity-operations-20261025/REVIEW.md), plus
[manual-range evidence](../reports/range-policy/VERIFICATION.md) in its original
source scope, [idle/dust classification](IDLE_AND_DUST.md) and remaining
[strategy qualification](../TODO.md#task-security-strategy).

Those historical reports retain their original timing/capability scope; they do
not verify the later capability3 timing/outside policy. Use the new scoped
[maintenance verification](../reports/maintenance-policy-20261027/VERIFICATION.md).
