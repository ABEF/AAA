# Adversarial reward and keeper review

This internal review covers current fee allocation, claims, royalty/conversion
boundaries, unsigned claim preparation and keeper scheduling. It follows the
[allocation review](../reward-allocation-20261026/REVIEW.md), reusing unchanged
source-bound checks rather than repeating passing suites. Production remains
**NOT APPROVED**. No public transaction, service rollout or deployed-state change
was performed, and no production Solidity/ABI/economic rule changed.

## Findings corrected

### Maintenance dependency failures could suppress independent harvesting

An oracle/strategy read or rebalance simulation failure escaped to the bucket's
outer error handler. The scheduled harvest was skipped too, although fee-only
collection does not require a USD price and does not reduce LP liquidity. A
persistent price outage could therefore postpone funded rewards unnecessarily.

After validating the bucket, position and configuration, the keeper now isolates
price-dependent maintenance RPC errors. An enabled, due harvest still passes its
own normal simulation, runtime, nonce, gas, lifecycle and sender checks. Slow
failures get a fresh deadline. Identity/configuration/ABI errors do not enter an
unsafe fallback: configuration/ABI `ValueError` remains fail-closed, and global
pause/canonical locks and disabled/not-due harvesting still stop the operation.
`maintenance_deferred` leaves degraded telemetry visible even if harvest succeeds.

The first wider regression caught an overbroad error catch in the candidate:
it also isolated invalid compound-threshold configuration. The original existing
assertion was retained, the catch narrowed to `RpcError`, and the final affected
scope rerun. The failed result and source pins are preserved under
[the first attempt](regression-attempt1/affected-suite.json).

### Contradictory dormant balances could reach an unsigned wallet review

The current NFT read projection already rejected positive rewards for a never-
activated NFT, but unsigned claim preparation lacked the same consistency check.
Contradictory core/RPC data could produce a review even while the NFT card failed.
This was not a demonstrated on-chain withdrawal exploit: honest contracts do not
create that entitlement, and the on-chain router still checks ownership/payouts.

Current accounting3 preparation now reads permanent activation weight once per
distinct NFT at the same canonical block. Malformed/unavailable weights or values
above3 reject; weight0 plus positive selected LP/royalty rewards rejects before
simulation/draft publication. This is an integrity marker, not a payout multiplier.
Parked/outbound active positions and deferred optional royalty currencies keep
valid rights; legacy profiles keep their existing getter/codec boundary. Amounts,
targets, sender, snapshot, batch limits and simulation rules are unchanged.

### Post-intent errors consistently stop scheduling

Caught RPC/value errors in conversion and per-bucket maintenance/harvest handling
now propagate if a pending intent exists. No later job is scanned or attempted
after an ambiguous submission. Existing serial submission and pending guards
already prevented duplicate signing; this hardening does not claim an earlier
double-spend exploit. It preserves the exact saved hash/review/nonce for recovery.

## Accounting and adversarial boundaries reviewed

- Actual venue receipts fund the fixed80/10/5/5 split once. Claims cannot spend
  compound/buyback reserves, redistribute other NFTs' balances or change membership.
- Owner checks, fractional checkpoints and current-owner transfer rights remain.
  Batch duplicates/oversize/unsupported assets reject; callback transfers of later
  batch NFTs cause atomic rollback. Selected payout failure does not erase rights.
- Conversion settles already-earned per-NFT balances, measures actual ETH and
  conserves output without redistributing it by current membership or counting it
  as new income. Optional royalty-currency recovery preserves older cohorts.
- Harvesting with stale prices can move only actual fees to classified ledgers;
  it does not authorize principal movement, a trade, wider slippage or a claim
  recipient. The new actual-v4 integration test verifies that distinction.
- Unsigned drafts remain bounded, read-only and owner/snapshot/runtime checked.
  The activation guard adds at most one mapping read per selected NFT, with no
  optional token reads or new shared mutable request state. Signing remains outside
  the API; public website signing is still disabled.

No new reachable unauthorized-claim or reward-redistribution defect was found in
the inspected contract paths. That is source-scoped review, not an assurance that
all attacks or external dependency failures are impossible.

## Remaining qualification

Keep receipt-time membership for unharvested historical buckets, bounded allocation
dust, reserved index dust and carried fractions explicit. Actual tokens, feed
independence/updater operation, routes/burn behavior, maximum-state gas/strategy
economics, provider/service concurrency, recovery and independent audit/remediation
remain release gates. Direct single-operator governance/external custody trust is
unchanged. Sample harvest/compound/buyback settings are not running production jobs.

See [verification and exact scope](VERIFICATION.md), the
[operator instructions](../../docs/OPERATOR_MANUAL.md#revenue-operations) and
[claim preparation](../../docs/FRONTEND_TRANSACTIONS.md).
