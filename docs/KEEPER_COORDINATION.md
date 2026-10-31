# Keeper coordination and operation review

This describes the fresh [accounting6 / maintenance3 / portfolio2](POSITION_V6.md)
source candidate. Normal gates, scoped offline checks and local actual-v4-core
integration pass within their [recorded scope](../reports/residual-operations-20261031/VERIFICATION.md);
actual operating/dependency qualification remains open. It does not upgrade installed services,
old deployments or journals. Read the
[operator manual](OPERATOR_MANUAL.md) before changing an operating service.

## Compounding and rebalancing have different jobs

Compounding adds the bucket's attributed idle and designated 5% compound reserve
to its existing main LP range. It does not replace the range, alter a residual or
reset the rebalance clock. It may need an ETH/ZZZ swap. Rebalancing closes the
old main and any residual, then atomically rebuilds the selected one/two-leg
portfolio. Both physical positions and attributed idle back the same NFT shares.
Compound swaps spend only the
idle/reserve budget, but a swap in the same pool can also reprice the incumbent
LP and change its NAV. Keeping its LP token does not eliminate market risk.

The ordinary keeper waits to compound whenever the main crosses the 85% physical
price-distance threshold, is outside its physical tick range, or an operator
width/mode/active residual-geometry change is pending. This applies during
the 12-hour rebalance cooldown too. It reads actual main/residual identity,
Vault custody, ticks, token amounts, desired/applied revisions, helper graph,
pool state and pending flag at one canonical block; an unknown or
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

When a live worker sees a return inside the trigger threshold, opposite-side or
required independent-reference disagreement, it checks any
tracked ordinary confirmation window at that same block hash. A proved nonempty
old window goes through the existing reset/acknowledgement path; it cannot be
reused if price returns before the next official sample. Empty/manual windows
do not cause repeated paid clears. Missing compound-reader configuration alone
must not invalidate a healthy rebalance window. The report only reads this state.

A deliberate configuration repair skips threshold interpolation, so an old
centre outside physical bounds cannot prevent that manual repair path. Its
threshold-side diagnostics are unavailable rather than guessed zero; healthy
on-chain price/tick and execution guards remain.

## Confirmation, cooldown and durable delay

The source evaluates the 85% actual centre-to-main-boundary ZZZ-in-ETH price
condition during cooldown too. Ordinary samples require physical/reference
thresholds on the same side. Initial policy is 600 seconds of sampled evidence,
240 second checks and a strict 300 second maximum confirmed gap. A known maturity
or cooldown boundary may schedule an earlier read. Eligibility still requires
the full initial 43,200 second hard execution interval.

The service keeps raw checks during cooldown but opens paid ordinary observations
only at `earliestCooldown - duration - maximumGap`: initially the final 15 minutes.
Already-due candidates enroll immediately. Foreign records, acknowledgements,
fault resets and pending intents retain their original priority. The service does
not silently delete an earlier record; its next confirmed observation naturally
restarts stale evidence. It does not keep waking on an intentionally dormant
early maturity deadline. Clock/configuration changes recompute enrollment.

Readiness starts one durable OS-random60–300 second delay, different from that
bucket's preceding chosen delay; routine renewal does not redraw it. Returns,
side/policy/physical identity changes and relevant faults clear the candidate and
its delay through canonical reset/recovery. Samples continue through the wait.
Known renewal/reset deadlines follow pending recovery and precede optional jobs.
One serial nonce lane and actual inclusion latency can still miss300 seconds;
there is no uninterrupted-price or timing guarantee.

The fresh journal namespace is `observed_adjustment_v3`; historical namespaces
retain their own profiles. No automatic journal migration or pending deletion is
provided. A fresh source/capability deployment requires separately reviewed
configuration and recovery identity, not relabeling an old Anvil or live service.

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

Standalone harvesting remains hourly by default for accounting6. Harvesting
collects actual LP fees from both live legs and applies the allocation/dust rules; it does
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

The report covers profile4/policy2 and fresh profile6/policy3 rebalance, compound
and standalone harvest. Fresh output shows actual physical legs, aggregate
amounts and desired/applied mode; secondary ID0 does not imply disabled mode. It separates
not-needed work, timing waits, known blockers, unavailable evidence and missing
configuration. Other operation families are explicitly unsupported. Read the
individual checks: `ok: true` and exit code zero mean the report was produced,
not that an operation is ready or authorized. A timing lower bound is not a
promised execution time, and a
missing local scheduling record is not a fabricated future jitter deadline.

Rows use `not_needed`, `not_due`, `blocked`, `unavailable`, `unconfigured`,
`observed_eligible`, `simulated` or `unsupported`. `observed_eligible` and `simulated`
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

- **Hybrid utilization:** after an ordinary hybrid replacement, does main value
  reach 60% and residual stay within 40% of retained principal at the same starting
  price vector? These are separate from the idle and loss ceilings and are not
  continuous market-allocation requirements.

These limits are ceilings, not targeted losses. Actual settings and stronger
caller/venue limits apply; network gas is separate. No financial check was removed
or widened by this keeper work. Missing actual prices or post-execution deltas
leave a margin unavailable, rather than calculated from a guessed price.

## Identity faults and confirmed telemetry

Missing/mismatched pool occupancy or contradictory active/parked LP identity now
requires a durable reset for that bucket's confirmation/jitter. Unrelated share
inventory faults do not become evidence of price-condition failure. Pending
recovery stays first; saved clear acknowledgements prevent repeated paid clears.
Do not delete schedules/journals to recover. Terminal stop creates no new
ordinary confirmation work for these identity faults.

Fresh snapshots bind the separately deployed Budget/Balancer/Policy/Confirmation
to the sealed controller's fixed parent modules, and the typed physical executor
and arithmetic child to exact parents/dependencies. `portfolioFingerprint`
excludes changing liquidity; `executionPortfolioFingerprint` includes it for
custody manifests. Source hashes are not remote attestation.

Execution telemetry additionally rechecks the final latest head, depth,
chronology, canonical anchor and freshness before publishing `last_confirmed`.
Failure retains old evidence as unavailable and cannot advance healthy time.
The successful observation adds one logical latest-header read; adapter chain
checks/retries and actual provider latency still need qualification. These
diagnostic changes do not add transaction authority or guarantee strict cadence.

## Rollout and recovery

Install matching reviewed source through the controlled service procedure, then
restart while preserving the existing journal, pending transaction and fee/nonce
history. A local source publication does not perform that rollout. Do not clear
state to make a report or health check pass. Verify real timing, logs and paid
receipts on the qualified deployment. Use the existing
[recovery runbook](KEEPER_RECOVERY.md) for contradictions and pending recovery.
