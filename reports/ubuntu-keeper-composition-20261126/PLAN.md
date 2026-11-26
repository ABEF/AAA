# Combined Ubuntu keeper, backups and observation — execution plan

Baseline: `7436933c153246f57eaa01cf42c5f3ec90363dad`.
This plan is not a pass or approval to adopt an existing environment.

The missing proof is composition: actual normal keeper/Cast execution has been
verified separately from timer-driven backup/alert work. Prior construction,
fee/recovery, timer, lock, outbox and exact-restore evidence retains its original
scope and will not be rerun as unchanged component tests.

## Scope

Use one fresh private Ubuntu lab and a copied, pinned F6 local-chain fixture.
Use current published Python files, unchanged financial/resource profiles,
one fresh disposable local keeper key and one local harvest transaction.
There is no public RPC, public transaction, new deployment or sealing.
No existing service, journal, chain, site or paused desktop monitor is adopted.

Run the normal daemon with the actual Cast binary, alongside native scheduled
backup and observer jobs. Original configuration and source identities must
match; unsigned jobs cannot read the signer files. Local timer timings must be
explicitly labeled and must not silently replace production configuration.

## Required new interactions

1. Pause a **lab-only** backup-reader wrapper after its first captured journal
   read. Let the actual keeper publish its intent, then release that read.
   Verify safe capture refusal and preservation of the prior selected backup.
   Distinguish this deterministic instrumentation from uninstrumented jobs.
2. Require successful ordinary timer-driven backup and observation against that
   same real daemon journal/configuration, including its known pending hash.
3. Briefly contend the shared scheduler lock while a pending clock and queued
   alert exist. Verify refusal preserves those exact records and does not hold
   the keeper's separate transaction lock; later delivery must retain event IDs.
4. Let the normal pending-first loop settle the original transaction. Check
   canonical receipt, nonce, journal and cost counters: exactly one submission,
   one fee booking, no resend and no guessed recovery state.
5. Retain the following ordinary wake: receipt-clearing intentionally skips
   fresh metadata and remains degraded. Require authentic later health and
   price/reference proofs before calling that phase healthy. Derive timings
   from preserved deadlines and distinguish wall time from chain time.
6. Capture final physical NFT/LP/rights/reserve/balance vectors and validate the
   producer's canonical/accounting assertions **before** completion/teardown.
   Independently reconcile the retained vectors before accepting or publishing
   the outcome. Preserve partial/failure evidence. This orders physical capture
   before shutdown without duplicating the later saved-evidence verification.

## Execution and review boundaries

Bound phase work to900 seconds and6,000 local RPC requests, with explicit
cleanup headroom and hard service limits. Keep240-second normal polling,
12 confirmations, hourly harvest and24M/full25% maintenance admission.
No forced early refresh, ordinary safeguard bypass, clock reset or financial
limit increase may be used to manufacture a pass.

Before execution, review complete static/dynamic source and command closure,
runtime permissions, loopback listener ownership, actual timer/service settings,
bounded captures and mandatory all-owned-group cleanup. Review source first;
fix only a confirmed defect, with necessary affected checks. Report-only saved
evidence verification does not count as another transaction or runtime test.

Take separate before/after snapshots of the existing host service states.
Original four unrelated tracked edits and all historical evidence remain exact.
Publish the outcome, Todo and operator procedure with explicit remaining limits.
This is not multi-day soak, actual market/provider qualification, off-host
possession/fencing, real notification delivery or independent release approval.
