# Independent saved Entry fee baseline review

The new offline [eager replay](verify_baseline_eager.py) independently processes
all six `PoolRewardsCredited` events and share/membership weight changes from the
original [Entry archive](../../pool-integration-20261120/entry/EVIDENCE_MANIFEST.json).
Its exact SHA256 is `e56b8d78aba465c673aa0379e6a4214860189e935c133dafc7da8c46aa99d2ff`.
All four captured contribution after-states match individual plus collective
claimables, share totals and eligible count. [Result](BASELINE_EAGER.json) and
[source/output identity](EXECUTION.json) preserve this finite check.

The oracle allocates every whole unit immediately using a rational numerator over
`totalWeight * 2**128`, rather than the production lazy pending tree, packed carry
or two-fold split implementation. Genuine weight changes preserve high phase and
rebase the low remainder; no-op changes preserve both. It reads no production
pending, phase or accrued getter and does not initialize expected claims from
observed claimables. Final independent nonzero phases are retained for comparison.
The old Python design helper that resets a stream on weight changes is unsuitable
for this F6 restored history; it was inspected, not executed or silently adopted.

This establishes the restored two-NFT baseline only. It does not re-execute old
Entry calls, run an unchanged suite, prove physical TickMath valuation, qualify
new harvest/payout transactions or validate a real ETH conversion route. New
fee-flow evidence must independently reconcile actual Vault receipts,20-unit
80/10/5/5 splitting and dust barriers, reserve backing and current-owner payouts.

## New saved extension review

The [separate saved-extension verifier](verify_extension_saved.py) and
[result](EXTENSION_REVIEW.json) add17 exact transaction identities and full
padded gas limits,1,333 immutable request identities/hashes,25 state checkpoints,
three actual-fee receipts and seven direct source-currency LP payouts. It seeds
expected rights and phase only from the independently derived baseline above,
then replays new credits and claims. Unchanged main L/ticks/shares and current
payout recipients, exact native gas adjustments, typed simulation-only former-owner
and Oracle refusals, and no Oracle/feed calls in harvest or claim traces pass.
Both allocated Rewards liabilities/cash drain; classified fee dust and compound/
buyback reserves remain backed and separate.

[Execution identities](EXTENSION_EXECUTION.json) retain exact source/output hashes.
Two initial offline-verifier failures concerned absent constructor `to` keys;
their source copies and failure records remain. Correcting those filters did not
change or rerun EVM evidence. This review does not imply provider/fees/daemon,
multiple-leg, arbitrary cohort, ETH conversion or production approval.

## Archive and source readback

The [offline archive verifier](verify_archive.py) and [result](ARCHIVE_REVIEW.json)
check all114 unique member lengths/hashes, current runner/helper equality to the
successful execution source, the new oracle-control source pin, both stopped owned
nodes and exact35 public HTTP200 reads,176 cache hits and3 local rejections.
No public/EVM request is made by this check. The failed restore stage stays in
the original archive; report prose corrections do not rewrite its bytes.
