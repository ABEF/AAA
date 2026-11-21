# Bounded Cast output capture

21 November 2026. Baseline main:
`7124b6cdeaaa697be02d4c91f91b46163051d673`.
Production remains undeployed and NOT APPROVED.

## Result

Both keeper Cast boundaries now use the small Unix
[`run_cast` helper](../../keeper/cast_process.py): encrypted wallet-address
validation and asynchronous transaction submission. **16 distinct NEW methods
pass**, eight composed integration/source-identity checks and eight actual
unprivileged Ubuntu subprocess checks. No unchanged test method was rerun.

| Property | Implemented behavior |
| --- | --- |
| Output |65,536 raw bytes total across stdout AND stderr; exact limit accepted, one extra byte refused before retaining it |
| Time | Existing30-second address and90-second send budgets; one monotonic deadline through reads, EOF, decoding and exit wait |
| Capture | Binary nonblocking pipes/selectors; bounded read chunks, strict UTF-8 and original universal-newline behavior; complete output only |
| Child | No shell, stdin is DEVNULL, descriptors close on exec, new owned process session/group |
| Failure | Kill the owned group before reaping its leader, close both pipes and wait at most2additional cleanup seconds; no unbounded drain or disk spool |
| Diagnostics | Fixed sanitized errors; timeout names only `Cast`, with no argv, environment or partial output attached |
| Scheduling | No retry, resubmit, background watchdog pulse or new financial allowance |

A valid-looking hash prefix followed by excess/bad stderr is not accepted.
Failed/nonzero commands and complete address/hash validation retain their prior
meaning. The byte cap bounds captured output, not Cast's own RSS/CPU or arbitrary
kernel process creation/kill latency. Existing host/cgroup supervision remains
necessary; deliberately escaped/same-UID hostile children are not contained by
this helper alone. [Python subprocess](https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen)
and [Unix pipe selector support](https://docs.python.org/3.12/library/selectors.html)
inform that boundary.

## Pending, recovery and financial safeguards

The existing intent is saved/fsynced BEFORE launching a send. Capture overflow,
invalid encoding or timeout preserves the exact hashless pending intent, nonce,
calldata/value, captured fee review, spend and receipt checkpoint. It cannot
establish whether the transaction was sent. No partial hash is parsed and no
automatic resend is introduced. Normal exact-hash/nonce/receipt reconciliation
remains required before any new action.

The final stop check, including stop observed during durable save, still
prevents launching a new signer. An underway submission is not transactionally
cancelled. A new child session means terminal Ctrl-C can stop future worker
actions while active Cast finishes within its timeout; it no longer incidentally
shares foreground SIGINT. Use the reviewed unit's whole-cgroup stop/fencing and
reconcile pending state before restart. Killing a child never proves that no
broadcast occurred. This preserves the documented
[underway-submission rule](../../docs/KEEPER_RECOVERY.md) and
[Q06 boundary](../q06-keeper-recovery-20261117/REVIEW.md).

All contract permissions, exact accounting, price/loss/slippage checks, gas/fee/
funding budgets,30/90timeouts and transaction/journal schemas remain unchanged.
No new config field, on-chain cap, signer authority or user transaction is added.

## Source identity and affected fixtures

`keeper.health.SOURCE_FILES` now includes `keeper/cast_process.py`. Both existing
execution and confirmation health readers reject absent/changed helper hashes.
Adopt matching keeper/checker source together; this is file identity, not loaded
code attestation. No health/journal/checkpoint schema is relabeled or rewritten.
Current checkpoint semantic source lists do not include these keeper modules.

Changing the Cast seam requires corresponding inert test mocks. The
[migration](FIXTURE_MIGRATION.json) changes157 patch-target string literals
across47 existing fixture files. Independent [AST checks](FIXTURE_AUDIT.json)
verify that only those literals change; method identities, assertions, command,
environment, timeout and exact-state checks remain. Actual optional Cast `--help`
and unrelated subprocess/CLI mocks are unchanged. None of those old bodies ran.

## Verification actually performed

| Stage | Actual result | Scope |
| --- | --- | --- |
| [Composed integration](integration/RESULT.json) |8NEW methods pass; source before/after identical | Fresh7 inert RPC/Cast seam: send overflow/encoding/timeout preserve reloadable intent/no resend; successful review/hash; shutdown; address validation; both health helper-source checks |
| [Ubuntu helper](UBUNTU_RESULT.json) |8NEW methods pass as UID65534 in1.610s | Exact aggregate cap, stdout/stderr/split overflow, partial hash/bad UTF-8, idle/active/closed-pipe deadlines, exited leader/inherited pipes, direct child reaping, descriptors and interruption |
| [Ubuntu process/transport](UBUNTU_EXECUTION.json) |No outer timeout; all children reaped, one already-terminated orphan collected, no unexpected live descendant; owned temp directory removed | Only reviewed helper/test files, no Cast/key/RPC/chain/service |

Helper tests use short controlled deadlines; integration checks assert the real
30/90 arguments. They are not a90-second live Cast campaign. No old suite,
browser, Solidity compiler/size build, population or fork was rerun. The broader
normal-daemon/encrypted-Cast Ubuntu qualification remains open.

The initial transport attempt failed locally with empty SSH output. The exact
same stripped environment also failed local `ssh -V`, while the existing strict
driver environment passed. Its [failure](UBUNTU_LOCAL_FAILURE.json) and
[diagnosis](UBUNTU_TRANSPORT_DIAGNOSIS.json) remain separate from test results.
The known-working strict transport performed the sole actual Ubuntu8 run.

Current named/anonymous inventories are refreshed separately. All61 project
Solidity/39dependencies/4build controls and1,021ABI rows retain their F6 pins.
The helper adds one production module; older inventories/reports retain their
own source scopes. New tests are registered in the maintained keeper selection.

## Operator and release boundaries

See the [operator procedure](../../docs/OPERATOR_MANUAL.md#bounded-cast-output-and-uncertain-transactions).
The code is implemented and checked, not deployed to an installed service.
Existing Anvil, NFTs/LP/balances, journals, websites, services, credentials and
paused heartbeat are untouched. No public signing, deployment, sealing or
financial/profile change is authorized by source publication.
