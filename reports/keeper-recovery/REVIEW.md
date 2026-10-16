# Keeper recovery: internal security review

Reviewed 2026-10-16. **Not an independent audit or production approval.** No real signing, asset movement or smart-contract deployment was performed. This review concerns the keeper, RPC transport, durable state boundaries, relevant tests and operating instructions; it is not a fresh audit of every contract or a guarantee against every failure.

## Result

The candidate now stops unsafe recovery/signing paths and exposes blocked operations explicitly. A supported live keeper remains **not approved** until the external operating gates below are closed. Liquidity custody remains on chain. A server restart does not recreate missed fees or guarantee that an out-of-range position earned revenue during downtime.

## Findings addressed

| ID | Priority | Finding and remedy | Regression evidence |
| --- | --- | --- | --- |
| K01 | High | Missing state could initialize empty budget/history. Live mode now refuses missing/corrupt/legacy-uncheckpointed state. Explicit bootstrap accepts only an unused signer after chain/code checks. | Missing state, malformed counters, used-signer rejection, bootstrap/no-overwrite and legacy rejection tests. |
| K02 | High | Restored state could be stale relative to an externally used nonce. New submissions require exact saved/confirmed/pending nonce continuity. Unknown outstanding transactions block signing. | Nonce drift and restoration tests; durable intent remains authoritative. |
| K03 | High | A previously confirmed receipt could later be reorganized after local pending state was cleared. A persisted receipt anchor is rechecked before reconciliation/submission; changed identity/depth stops progress. | Reorged prior checkpoint, missing checkpoint and pending preservation tests. |
| K04 | Medium | Receipt evidence must not silently invent zero costs or accept a mismatched transaction. Strict hash/sender/nonce/target/calldata/value/inclusion checks and atomic cost updates are retained and exercised. Live mode additionally requires reviewed inclusive/separate-L1 accounting. | Malformed/missing receipt fields, changed inclusion, midnight spend, save failure, fee-policy and exactly-once cost tests. |
| K05 | Medium | Malformed estimates and inadequate funds could reach the signer. Estimates/prices/balances now use strict RPC quantities; bounded costs and available native balance are checked. | Malformed gas, low balance, gas/price/transaction/daily limits tests. |
| K06 | Medium | Reverted operations could be repeatedly retried while burning keeper funds. Actual costs remain charged and the same action receives a durable cooldown, default one hour. | Revert accounting and no-immediate-resubmission tests. |
| K07 | Medium | A running loop could look healthy while skipping work. Separate atomic health output records pending/recovery/degraded/error states, blocked actions and last success. Storage/unexpected failures halt; errors have sanitized source locations. | RPC failure/recovery, blocked gas, skipped bucket, ambiguous receipt, health-write failure and secret-redaction tests. |
| K08 | Medium | Weak runtime paths could overwrite sensitive files or permit unsafe recovery state. Live mode requires Unix private owned files/directories, rejects leaf symlinks and path collisions. | Collision tests and dedicated Unix permissions/symlink regression. |
| K09 | Medium | Malformed transport replies/incomplete HTTP reads could bypass intended fallback. Endpoint count, retries, timeout, response IDs and error codes are bounded/validated; safe read fallback handles malformed transport. | Wrong-chain, bounded retry, incomplete-body failover, response ID, size and redaction tests. |
| K10 | Medium | Stop/restart behavior needed clearer boundaries. Stop requests before durable intent prevent submission. The dry-run systemd unit stops signer children, limits restart storms and narrows OS privileges. | Shutdown-during-preflight and durability tests; Ubuntu unit verification. |

Prior receipt-hardening work was included in this scoped publication rather than discarded. `zzz_ops/state.py` retains its existing exclusive temporary file, fsync, atomic replace and process-lock implementation. On-chain keeper role/seal/pause checks, strategy cooldown/trigger, deadlines, prices and swap bounds were inspected as safety boundaries; no Solidity implementation was changed by this keeper-only review.

## Validation scope

- The current local workspace passed **602 Python tests**, with zero failures, errors or runtime skips; **five Unix-only cases** were explicitly reserved for Ubuntu. That full workspace contains other unpublished work, so it is not a claim about every file in this Git commit.
- `focused-tests.json` and `source-binding.json` record the keeper/RPC/state test inventory and exact source hashes for this review. The dedicated **Keeper safety regression** workflow executes these cases, including Unix permissions/locking and the actual pinned `cast` CLI parser, on Ubuntu. Check its exact commit result separately.
- No Solidity, live venue, mainnet/testnet signing, real server-loss or multi-day outage rehearsal was executed as part of this scoped review. Earlier contract/fork receipts retain their original source scope.
- An earlier local full-suite attempt had one CLI-parser skip because the bundled Python launcher did not retain the shell PATH change. That result was not counted as final evidence. The final run set the pinned Foundry path inside Python and had no runtime skips.

## Production gates still open

1. **Real service configuration:** approved deployment/runtime pins, supported RPC behavior and confirmation policy, actual Robinhood L1/L2 receipt accounting, appropriate gas allowances and funded least-privilege keeper address. Provider failover is not Byzantine quorum verification; compromised providers remain a trust boundary.
2. **Restore/reorg operations:** recover stale backups, ambiguous broadcasts without a discoverable hash, deep reorgs, crashed disks and complete server loss. No arbitrary transaction deletion, automatic same-nonce replacement or universal lost-state reconstruction is supplied. Some incidents require reviewed reconciliation and/or timelocked signer rotation.
3. **Single active signer:** prevent two hosts or another tool from using the same key. Local locks do not provide distributed fencing. Revocation and replacement must be rehearsed if a host/key is lost or compromised.
4. **Off-host monitoring and backups:** configure encrypted credential custody, state backup frequency/retention, restore verification, log retention and alert delivery from a separate host. A local health file is not an alerting service.
5. **Operating rehearsal:** actual Linux service lifecycle, shutdown during signing, multi-day downtime, low balance, RPC outages, reverts and ongoing receipt/metadata maintenance. Unit tests and systemd syntax verification do not substitute for this.
6. **Independent review and strategy economics:** independently review these changes and the complete contract/deployment configuration; qualify slippage, oracle/hook behavior, gas use and rebalance parameters. Rebalancing does not eliminate impermanent loss. A configured L1 allowance is not an on-chain cap on external gas charges.

The [central Todo](../../TODO.md) and [recovery runbook](../../docs/KEEPER_RECOVERY.md) retain these requirements. Do not remove a gate merely because tests pass.
