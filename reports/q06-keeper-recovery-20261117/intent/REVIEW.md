# Shutdown after durable intent publication

## Confirmed defect and correction

The submission path checked the shutdown flag before writing its pending intent,
then started the signer without checking again. A stop received while that write
was completing could therefore be followed by a new signer launch.

`Keeper.submit` now checks the existing flag immediately before invoking the
signer. If set, it emits the fixed `shutdown_after_intent_before_signer` event and
returns false. It retains the exact already-published hashless intent and fee
review. No journal field, fee cap, nonce, permission, schema or economic rule
changes; no automatic deletion, cancellation or resend is introduced.

The retained hashless intent deliberately blocks new work. Even though this
process did not launch its signer, this patch does not invent broader evidence
about the nonce or other software. Existing reviewed recovery remains necessary.
A signal arriving after the final check, or a previously broadcast transaction,
cannot be retrospectively cancelled by this check.

## Verification

Only three new test methods execute. The baseline runs just the new regression:
one selected method fails with **one signer invocation**, a true submission
result and a journal changed from hashless intent to returned hash. This is a
demonstrated source defect, not a generic expected revert.

After the correction, all three new methods pass, with no skips or errors:

| New method | Evidence |
| --- | --- |
| `test_stop_during_durable_save_retains_hashless_intent_and_restart_never_resends` | Stop flag set after the real atomic writer returns; no signer call, false result, byte-identical retained hashless journal, unchanged nonce/spend/clock/receipt anchor; reconstructing Keeper and running recovery/new submission sends nothing. |
| `test_uninterrupted_submission_keeps_durable_intent_exact_review_and_hash` | Healthy control reaches the inert signer once with the exact durable calldata, nonce, gas review and timeout; returned hash is persisted without charging spend before receipt. |
| `test_failed_save_after_atomic_publication_never_signs_or_discards_recovery` | A post-publication storage failure prevents signing; reconstructing the unchanged journal preserves and blocks the hashless intent. |

The new fixture uses typed fresh accounting7/custody5/execution-price1/LP3 replies.
Actual Keeper accounting, runtime, lifecycle, checkpoint, nonce, funding,
simulation, gas/fee and deadline validators run; none are replaced by no-op
functions. RPC responses and the external signer are inert controlled seams.
The journal is a new disposable temporary file and uses `atomic_json` normally.
The shutdown flag models receipt of a stop during the save; this is not an actual
Linux signal or systemd proof. Unix permission/lock/startup and real encrypted
signer validation are outside this focused check and require the separate host
rehearsal.

`baseline01-START.json` and `baseline01-RESULT.json` retain the failed source
stage, exact selection and observed signer call. `final01-START.json` and
`final01-RESULT.json` retain all three exact IDs, compiler-independent Python
runtime, source hashes and stable before/after import closure. Corresponding
`unittest.log` copies are included. The runner explicitly constructs the one new
test class, so imported fixture classes do not execute their old test methods.

No existing suite, Forge/compiler/static gate, service, live journal, database,
chain, website, heartbeat or signing operation was run or changed by this work.
