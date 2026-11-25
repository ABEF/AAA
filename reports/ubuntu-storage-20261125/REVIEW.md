# Ubuntu keeper storage-failure recovery — 25 November 2026

The new isolated c808 partition passes **six genuine filesystem refusals and
two actual stock-Keeper/Cast transactions**, using2,265/6,000RPC requests in
38.3seconds. Exact journals, transaction recovery and captured NFT/LP rights
reconcile. The [independent saved-vector review](evidence/INDEPENDENT_REVIEW.json)
passes all eight checks. Production approval and broader Q06/P21 acceptance
remain open.

## Confirmed fixes

1. **Preserve the original failure diagnostic.** A failed journal write could
   trigger a second failure while writing health, before the original error was
   logged. `run_cycle` now logs the original sanitized `cycle_failed` and clears
   its ephemeral cache first. A failed health write still halts the keeper.
2. **Retain a reported recovery candidate.** When Cast returned a valid hash but
   saving that hash failed, the reconciliation event previously omitted the
   known candidate. It now includes `reported_transaction` only after strict
   nonzero-hash validation. This is a signer-reported candidate, **not proof of
   node acceptance**. Stock recovery must still verify its exact transaction
   identity. Invalid signer output is never logged.

Known genuine `OSError` values gain only a fixed `os_errno` name: ENOSPC,
EACCES, EPERM, EROFS, EIO or EDQUOT. Exception messages, exception-provided filenames, provider
URLs, signer output and credentials remain excluded. Other errors retain the
original two context fields. Neither fix changes persistence, accounting,
permissions, fee policy, signing authority, automatic resend behavior or limits.

## Actual Ubuntu sequence

The loaded unprivileged systemd job has a private network and mount namespace.
Its [filesystem record](evidence/c808/FILESYSTEM.json) verifies a separate
**1MiB tmpfs before filling it**. ENOSPC comes from actual bounded writes to
that volume; EACCES comes from removing write permission on its journal
directory. The host's physical disk is never filled. No mocked `OSError` is
used in these six [branches](evidence/c808/BRANCHES.json).

| Boundary | Actual failures | Verified result |
| --- | --- | --- |
| Publish intent before signing | EACCES and ENOSPC | Previous complete journal stays exact; no raw transaction is sent. |
| Persist hash after node acceptance | EACCES and ENOSPC | Exact durable hashless intent survives. Reconstructed stock Keeper blocks without resending; explicit `resolve_pending` adopts only the independently captured original hash. |
| Persist paid receipt accounting | ENOSPC and EACCES | Previous pending journal stays exact and in-memory receipt changes roll back. After repair and object reconstruction, canonical recovery books the original cost once. |

Each accepted hash is captured before inducing its write failure. Both actual
transactions are still unmined when the stock resolver adopts their hashes;
subsequent mining and twelve confirmations precede receipt recovery. A repeated
empty recovery changes neither settled journal bytes nor submission count.
The final [journal](evidence/c808/FINAL_JOURNAL.json) and
[pre-unmount capture](evidence/c808/JOURNAL_AT_STOP.json) have identical exact
bytes, parsed state and digest.

This is a **direct stock-object reconstruction** partition inside one isolated
job, not a new full-daemon/process-restart, watchdog, lock-release or off-host
proof. The earlier [supervisor checks](../ubuntu-supervisor-20261125/REVIEW.md)
retain those separate finite scopes and are not rerun.

## Accounting, limits and source scope

The [transaction vectors](evidence/c808/TRANSACTIONS.json) authenticate original
hashes, signed fields, receipt/header inclusion, confirmation depth, captured
fee bounds, inclusion-day spend and receipt anchors. Nonces advance0→1→2,
with exactly two original sends and zero resends. Canonical charges are
300,814,042,715,588wei and8,723,606wei; total300,814,051,439,194wei. These are
controlled Anvil fees, not Robinhood complete-fee qualification. Final on-chain
nonce getters execute as source assertions; separate getter vectors are not
supplied or invented.

Before/after projections match for the two NFT owners, shares, membership,
royalty weights, main-LP custody/identity/liquidity/ticks and selected reward,
compound and buyback balances. These zero-fee harvests do not requalify nonzero
80/10/5/5 allocation, claims, swaps or keeper-role enforcement.

The24M/full25% maintenance envelope,5gwei ceiling,0.01ETH transaction and0.05ETH
daily bounds, twelve confirmations and6,000RPC/900second lab limits remain.
Normal keeper polling/harvest policies are not changed by this directed check.

All190 packaged production members bind the published base
`352ebe0aa479a10f2220857edadbf049720616c5` plus exactly reviewed monitor-diagnostic
and verifier-inventory-pointer overrides. Final monitor SHA256 is
`5ab6bbb20eea21e301d81d2e829a827594079561e2f10770336ec8585b234631`.
Frozen F6 source/dependency/control maps remain61/39/4 with1,021ABI rows;
production Python inventory remains182files/2,003definitions/278lambdas.

Five NEW [diagnostic methods](evidence/DIAGNOSTIC_EVIDENCE.json) pass once at the
initial `5dda81c…` source. Two further NEW
[reported-hash methods](evidence/HASH_DIAGNOSTIC_EVIDENCE.json) pass once at the
final source. AST evidence preserves reuse of unchanged `error_context` and
`run_cycle` from the five-method stage; only `submit` changes in the second
stage. Against the published base, three function ASTs change and93 remain
unchanged. This is seven distinct new methods across explicit source stages,
not a seven-method rerun on the final source. No unchanged test bodies, passed
worker journeys, contract builds or financial suites rerun.

## Preparation, cleanup and remaining limits

The original c807 bundle is uploaded but never installed or started. Independent
pre-execution review caught its repeated use of an exclusive artifact writer.
The c808 correction is lab-only: a closed set of public outputs uses atomic
replacement, while frozen fixture helpers and production journal semantics stay
unchanged. Nested cleanup still stops the owned model if an evidence write fails.
Original unused artifacts retain their scope.

The [native stop](evidence/c808/control/STOP.json) verifies an inactive unit,
main PID0 and empty recursive cgroup. The separate
[host comparison](evidence/HOST_PRESERVATION.json) preserves five original
service states and seven previously stopped labs, with zero non-ambient
differences; one ambient observer invocation change remains explicit. Existing
chains, Anvil8902, NFTs/LP/balances, journals, websites, signer restrictions and
the user-paused heartbeat remain unchanged. Publication adopts no running
service, configuration or journal.

Tmpfs and directory-permission checks do **not** establish physical-power-loss,
ext4, directory-fsync-failure or arbitrary storage durability. Additional
transport/storage faults, restart storms, off-host fencing/restore, alert
delivery, sustained combined operation, actual providers/markets/complete fees
and independent release approval remain open. The
[evidence manifest](verification/EVIDENCE_MANIFEST.json) pins the exact public
outputs and reviewed helpers; original complete input archives remain private.
