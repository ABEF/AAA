# Harvesting, allocation and keeper audit

6 November 2026; baseline main `11e0157`. **Production NOT APPROVED.**
[Executed scope](PROMPT.md), [lifecycle matrix](LIFECYCLE.md),
[verification](VERIFICATION.md), [accepted LP redesign](EXACT_LP_DESIGN.md).

## Result and implemented changes

Both actual physical positions feed one logical bucket. Public live
`Vault.collectFees(bucket,deadline)` performs a zero-liquidity decrease/take for
main and registered residual, measures actual ETH/ZZZ receipts and allocates
each once. It does not change LP liquidity, swap, compound, burn or pay all NFTs.
No new conventional-token custody or duplicate-allocation defect was established
in this scoped review. This is not proof over every dependency or market state.

Two demonstrated keeper defects are corrected; production Solidity is unchanged:

| Finding | Before | Correction |
| --- | --- | --- |
| H01: stale preparation deadline |240seconds of successful maintenance reads could produce a standalone harvest deadline60seconds in the past. A fresh deadline was obtained only after a failed maintenance read. | When collection is actually due, obtain a fresh head after the preceding work and prepare180seconds from it. Failed final reads defer safely; skipped jobs add no read. Inclusion can still be delayed. |
| H02: mismatched restored clock metadata | A verified `collectFees(1)` receipt plus saved key `harvest:2` could advance bucket2's clock. Exact typed/event proof previously applied only to internal compound/rebalance coalescing. | Accounting4/5/6 standalone clocks now require exact saved key/bucket, Vault target, zero value, typed calldata and matching canonical collection event. Missing proof leaves only this clock unchanged; paid receipt/nonce/spend recovery still completes atomically. |
| H03: silent early proof mismatch | Some key/target/calldata mismatches returned no optional clock proof before the existing event diagnostic. | A sanitized `harvest_clock_unverified` warning identifies unproved successful standalone telemetry after canonical checks, without exposing provider text or preventing paid recovery. |

These are source changes, not a service installation. No journal schema,
contract profile, signing permission or existing state is migrated. Historical
accounting1/2/3 recovery remains explicit. Unjournaled manual, contribution and
governance consolidation activity is not guessed into the worker's clock; an
extra later harvest is safer than falsely recording one.

## Measured accounting limits

### H04: upstream fee checkpoint rounding

An actual-local-v4 snapshot comparison uses64identical donations of448raw units
per currency to the entire pool. PoPL has a main and residual with unchanged
IDs/liquidity. A final single harvest receives116wei ETH and116raw ZZZ; collecting
after every donation receives64of each. The52unit difference per currency is
upstream per-position fee-growth flooring, before funds reach PoPL.

This fixture uses donations to create real fee growth; it is not a market-volume,
profitability or target-gas simulation. The measured difference is below the
two-leg64-checkpoint bound of128raw units per asset. It does not establish an
economically viable attack on18decimal assets or a universal loss bound for all
dependencies. A downstream exact-unit allocator cannot recover unreceived fees.
No new permission/cadence gate is justified solely by this measurement; ordinary
permissionless and internal harvest liveness is preserved.

### H05: finite LP reward units can remain unclaimable

The real FeeController/Rewards test allocates20raw units with one101-share NFT:
18holder liability,17claimed,1still backed. The owner fractional remainder is
`999999999999999999999999999999999984` under SCALE1e36. Repeating the claim does
not pay it without later revenue. The prior tests' solvency inequalities did not
prove final whole-unit claimability.

The user selected an exact-unit LP upgrade during this audit. The
[bounded allocation-tree design](EXACT_LP_DESIGN.md) and isolated model are
delivered; **the current Solidity LP ledger is not fixed by that prototype**.
The earlier exact-unit royalty4 work solved a different ledger. A separate fresh
accounting/canonical/consumer implementation is required; the central Todo keeps
that requirement open rather than describing backed LP fractions as solved.

### H06: intentional split and cohort policies

The split is exact per20raw distributable units:16/2/1/1. Carry<20remains until
another receipt or entitlement barrier. A barrier assigns up to19units entirely
to incumbent individual rewards. Thus combining two receipts before modelling
their intervening flush can produce a wrong expected split; this audit retained
and corrected that independent-model failure instead of weakening the source.

Collective membership is sampled at actual allocation. The current contribution
bucket harvests before admitting new rights; another historical bucket's
unharvested fees retain the documented receipt-time policy. It is not exact
swap-time attribution across all buckets. No split/weight/ownership policy is
silently changed here.

## Cross-component conclusions

- Entry settles funded dust, harvests incumbents, releases old compound to their
  attributed idle, balances entrant-only funds, harvests own-entry-swap fees and
  checkpoints before issuing shares. Growth changes no collective membership.
- Existing-main compound/consolidation also harvests its balancing-swap fees
  before increase. Full close/move/park/terminal paths harvest before classifying
  close proceeds as principal. Same-main phase4 does not release designated
  compound. Reserve release, idle and actual deployed compound are different.
- A failed second-leg collection rolls back the first collection, fee-growth
  checkpoints and every subsequent allocation. Both IDs/L, shares and backing
  remain. Out-of-range/mixed/filled positions are still registered custody.
- `PoolRewardsCredited` records holder income, `FeesAllocated` gross/reserves/
  carry and `MembershipDustSettled` the incumbent transfer. `FeesCollected` is
  operational telemetry, not another income credit. Negative replay allocation
  already fails closed; no speculative patch was made.
- Raw claim reads/preparation need no USD/NAV price. Fee-only collection keeps
  admitted key/core/periphery/token/custody checks without a spot/price-read
  requirement. Pause, canonical locks, broken tokens/core or bad bindings can
  still block appropriate operations.

The maintained economics guide had stale royalty index/fraction prose and the
operator manual mentioned royalty conversion. Both now reflect royalty4 exact
original-currency claims, separately from unchanged LP fractions/conversion.
Manual collection, clock proof, deadline, failure and restart instructions are
aligned with the implemented keeper behavior.

## Remaining risks and qualification

Implement and verify the approved exact-unit LP upgrade. Separately qualify actual
fixed-ZZZ/proxy/admin/callback behavior: a compromised dependency can create fees
between pre-close collection and burn, causing late fees to enter principal.
No ordinary outside transaction interleaving was established inside the atomic
hookless/exact-transfer flow; this known dependency boundary is not silently
redesigned or labelled a newly demonstrated outside exploit.

Actual providers, routes, token burn semantics, target gas, hourly operating
latency, source rollout, restart/restore and independent audit remain open.
Hourly is a scheduling target, not an uninterrupted-execution guarantee.
No deployment, public transaction, service/site change, existing Anvil/journal/
signer alteration or heartbeat restart occurred.
