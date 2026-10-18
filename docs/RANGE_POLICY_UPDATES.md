# Applying range settings after sealing

Governance can change the admitted pool's range through the existing timelock.
The keeper can then apply it through the ordinary `Vault.rebalance` path even
if the price has not moved far enough to satisfy the price trigger. No new
force-rebalance authority or separately queued keeper request is introduced.

## From approval to execution

1. Governance reviews the complete pool configuration and schedules the exact
   `PoolRegistry.configure` or selected-pool `configureNative` call. Bootstrap
   and keeper addresses cannot change it after sealing.
2. After the timelock executes, `Strategy.rangeUpdatePending(bucket)` compares
   the current physical LP's ticks with the configured target calculated at
   the bucket's **recorded creation/rebalance center**. Using today's price for
   this comparison would cause needless repeated replacements as prices drift.
3. `needsRebalance` requires an active funded position, enabled operations,
   the configured cooldown and a fresh reference price. Either the existing
   price trigger or this range mismatch can then make it eligible.
4. The existing keeper discovers that shared bucket and submits the ordinary
   rebalance. Vault's keeper/lifecycle/pause, deadline, price/deviation,
   swap/close/mint minimums, **3% aggregate execution budget** and **5% idle
   ceiling** all remain in force. Network gas is separate.
5. Successful replacement records the new physical LP, center and cooldown
   checkpoint. The mismatch clears. Any failed execution rolls back custody,
   accounting and the old position; the desired range remains pending.

`rangeBps = 1000` means approximately **minus 10% / plus 10%** around the
reference token1/token0 price, before outward tick rounding. It does not mean
that half the capital is always held in each token. A config change that rounds
to the same ticks needs no replacement. Changing slippage or deposit limits
alone does not create a range-update trigger. Contributions and compounding
continue using the current physical position's ticks until replacement.

## Scope and safeguards

The comparison always resolves the bucket's current pool and physical LP ID.
There is no stored update request that can accidentally refer to a retired LP,
be replayed, or require a cancellation nonce. Before execution, governance may
restore the configuration matching the deployed range; this clears the pending
mismatch. After replacement, another width change requires another governed
configuration and remains subject to the cooldown. A separate price trigger may
still authorize a normal rebalance.

Execution uses the **current** approved configuration. The existing keeper
transaction contains bucket, minimum liquidity and deadline, not a configuration
hash or physical-LP-version lock. Operators must resimulate after configuration
or position changes. A signed transaction can still execute if the new current
state satisfies every guard. This is deliberate reuse of the existing governed
policy, not an exact historical-policy execution promise.

The fixed strategy has no state-changing external calls in the new comparison.
Missing position data, malformed intervals and invalid target arithmetic fail
closed. A wider target near Uniswap's extreme tick limits can be unrepresentable;
governance must simulate the target and keeper transaction before approving it.
Cooldown and the per-operation loss cap do not prevent cumulative costs from
repeated governance-approved changes. Production parameter/backtest, MEV and
operating qualification remain required. This code must be included before
sealing a deployment; it cannot patch an already sealed strategy.

## Rewards, API and operations

NFT ownership, bucket share counts and LP/royalty ledgers are unchanged by this
feature. Ordinary rebalance still harvests before closing and keeps accrued
claims attached to their PoPL NFTs. New physical Uniswap IDs do not create new
PoPL NFTs or reset claims.

Confirmed activation/approval responses include `range_update_pending` and
`eligibility_reason` (`range_update`, `price_trigger`, `price_and_range`, or null).
The reason describes the observed trigger even while cooldown blocks execution.
The API checks eligibility against cooldown and both trigger observations at
the same pinned hash. Missing/malformed getters fail closed; manifests must bind
the matching Strategy runtime. Keeper submission needs no new command or role.
`next_keeper_check_at` and `expected_execution_at` remain null without qualified
fresh telemetry. A polling interval is not a guaranteed rebalance schedule.

See [scoped verification](../reports/range-policy/VERIFICATION.md),
[internal review](../reports/range-policy/REVIEW.md) and the remaining
[strategy qualification](../TODO.md#task-security-strategy).
