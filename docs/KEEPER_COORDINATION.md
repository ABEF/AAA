# Keeper coordination and operation review

This describes the fresh accounting4 / maintenance-policy2 source. It does not
upgrade installed services, old deployments or journals. Read the
[operator manual](OPERATOR_MANUAL.md) before changing an operating service.

## Compounding and rebalancing have different jobs

Compounding adds the bucket's attributed idle and designated 5% compound reserve
to its existing LP range. It does not replace the range or reset the rebalance
clock. It may need an ETH/ZZZ swap. Rebalancing closes and replaces the shared LP.
Compound swaps spend only the
idle/reserve budget, but a swap in the same pool can also reprice the incumbent
LP and change its NAV. Keeping its LP token does not eliminate market risk.

The ordinary keeper waits to compound whenever the actual LP is outside its
physical tick range, or an operator width change is pending. This applies during
the 12-hour rebalance cooldown too. It reads the real LP identity, custody, ticks,
pool state and width-pending flag at one canonical block; an unknown or
contradictory result is unavailable, not an assumed in-range position.

This is a keeper scheduling policy. The contract's `compoundReady` decision,
separate compound interval, financial limits and full transaction simulation
still apply. The keeper cannot override the contract when it blocks compounding
after a raw rebalance need, including reference disagreement. An authorized key
running different code can ignore the additional Python wait rule; it cannot
ignore the existing contract checks. Price can move after the final service
check and before transaction inclusion. No new on-chain in-range guarantee is claimed.

Waiting, or an unavailable compound observation, must not stop an independently
due fee harvest. It also does not enable idle-only scheduling automatically.

When a live worker sees inside-range or opposite-side evidence, it checks any
tracked ordinary confirmation window at that same block hash. A proved nonempty
old window goes through the existing reset/acknowledgement path; it cannot be
reused if price returns before the next official sample. Empty/manual windows
do not cause repeated paid clears. Missing compound-reader configuration alone
must not invalidate a healthy rebalance window. The report only reads this state.

## What idle means

`Position.idle0/idle1` is ETH/ZZZ attributed to the shared bucket and its NFT
shares, but outside the Uniswap LP. It can include placement leftovers and
designated compound released during an activation/top-up checkpoint. For example,
a bucket with $9,900 of LP and $100 of attributed idle has $10,000 of attributed
value; the $100 outside the LP earns no swap fees. This is an illustration, not
a live price or balance.

Idle is not claimable fees, buyback money, royalty balances or accidental tokens.
It stays in NAV and is reinvested by guarded compounding/rebalancing, or included
in a terminal holder return. No operator sweep is authorized.

Waiting to compound can let idle accumulate. The separate 5% whole-bucket idle
ceiling may then block a contribution even if that entrant could add enough LP.
The remedy is to inspect/reinvest through an eligible operation or follow the
documented governance incident procedure; never use entrant funds to deploy old
idle or silently bypass the rebalance cooldown. See
[ownership, thresholds and recovery](IDLE_AND_DUST.md).

## Harvest clocks follow proved collection

Standalone harvesting remains hourly by default for accounting4. Harvesting
collects actual LP fees and applies the existing allocation/dust rules; it does
not itself convert rewards, compound, buy back, burn or pay a holder claim.

The worker can also collect fees inside a successful compound/rebalance. When
recovering its own saved transaction, it advances that bucket's harvest clock
only after the canonical successful receipt proves a matching `FeesCollected`
event from the actual Vault. The saved action, calldata bucket and event's
inclusion identity must agree. A valid zero-fee collection also counts as a
completed check. Use the receipt block time, never submission time or NAV changes.

This clock update shares the existing atomic nonce/spend/receipt journal save.
Reverts, pending or ambiguous transactions cannot advance it. Missing or malformed
optional event evidence leaves the harvest clock unchanged and produces a safe
diagnostic; it must not strand an otherwise verified paid transaction or cause
a resend. Manual transactions made outside the worker journal are not silently
adopted. A redundant later harvest is safer than guessing that one occurred.

## Read-only operation review

Use the actual reviewed keeper configuration and one to four explicit bucket IDs:

```bash
python3 -m keeper.ops --config /path/to/reviewed-keeper.json review --bucket 123
python3 -m keeper.ops --config /path/to/reviewed-keeper.json review --bucket 123 --simulate
```

Replace `123` with an observed bucket ID, not an NFT ID. The example configurations
remain unconfigured; filling a field or obtaining a report is not release approval.

The report covers rebalance, compound and standalone harvest. It separates
not-needed work, timing waits, known blockers, unavailable evidence and missing
configuration. Other operation families are explicitly unsupported. Read the
individual checks: `ok: true` and exit code zero mean the report was produced,
not that an operation is ready or authorized. A timing lower bound is not a
promised execution time, and a
missing local scheduling record is not a fabricated future jitter deadline.

Rows use `not_needed`, `not_due`, `blocked`, `unavailable`, `unconfigured`,
`observed_eligible`, `simulated` or `unsupported`. The last two positive states
cover evaluated views or a discarded simulation, not complete worker readiness.
Times are Unix seconds; loss settings are basis points. Reserve thresholds keep
each currency's raw units, and network costs use wei. Never add ETH and ZZZ raw
units or treat an unavailable margin as zero.

Optional simulation uses only the fixed typed calls for those operations at the
reported snapshot. It does not sign, submit, recover a transaction, create a
journal, draw jitter, reset a confirmation window or change a worker schedule.
Simulation success is not inclusion, paid gas, complete service readiness or
production approval. An opaque RPC revert remains unclassified; a report must
not invent an exact slippage inequality from a generic error.

## Understand the financial checks

- **Swap:** did ETH-to-ZZZ or ZZZ-to-ETH return enough output under the reviewed
  route, known fee, additional-loss and caller limits?
- **Before adding LP:** did the ETH+ZZZ amount retain enough value after balancing?
  This can overlap a swap check at unchanged prices, but not under every rounding,
  price-timing or emergency case.
- **Contribution:** did this entrant actually add enough new LP? At the default
  2% ceiling, a conservatively valued $100 input needs at least $98 of new LP.
  Existing LP/idle cannot satisfy that floor.
- **Maintenance:** did LP plus attributed idle retain enough starting value,
  including released compound? Its default ceiling is 3%; it is separate from
  the contribution check and the 5% idle ceiling.

These limits are ceilings, not targeted losses. Actual settings and stronger
caller/venue limits apply; network gas is separate. No financial check was removed
or widened by this keeper work. Missing actual prices or post-execution deltas
leave a margin unavailable, rather than calculated from a guessed price.

## Rollout and recovery

Install matching reviewed source through the controlled service procedure, then
restart while preserving the existing journal, pending transaction and fee/nonce
history. A local source publication does not perform that rollout. Do not clear
state to make a report or health check pass. Verify real timing, logs and paid
receipts on the qualified deployment. Use the existing
[recovery runbook](KEEPER_RECOVERY.md) for contradictions and pending recovery.
