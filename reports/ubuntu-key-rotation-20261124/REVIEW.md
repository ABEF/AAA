# Ubuntu keeper key replacement and pending recovery — 24 November 2026

## Result and scope

The new c803 isolated check passes **revocation before an old pending call,
recovery of its reverted receipt, and a successful protected call from a separate
replacement key**. It uses2,077/6,000 requests, seven setup transactions and two
actual stock-keeper/Cast submissions: one intended revert and one success.
No production contract, Python implementation, financial policy, fee profile,
signer behavior, gas limit or existing environment changes.

The exact old and new operation is `RebalanceConfirmation.resetObservation(bucket)`,
which is genuinely keeper-only. Permissionless harvesting or metadata would not
prove revocation. This is a direct stock `submit`/restart/recovery partition,
not another normal-daemon or LP-market qualification. Existing financial-worker
and one→two→one evidence is reused without repeating those journeys.

All190 copied production members match published
`55e90d7d665bd3a310db163d95f2dba51083ae0b`. Unrelated dirty work is excluded;
F6 sources/dependencies/build controls remain61/39/4 with1,021ABI rows.
See [runtime result](evidence/c803/RESULT.json), [state](STATE.json),
[raw vectors](evidence/c803/rotation-ROTATION_VECTORS.json) and
[artifact manifest](verification/EVIDENCE_MANIFEST.json).

## Executed sequence

| Step | Actual evidence |
| --- | --- |
| Prepare | Two new encrypted disposable keys, separate sender/configuration/state/health/lock paths;39 normal runtimes and91 sealed static bindings match |
| Publish old work | Stock simulation, nonce/funding/runtime checks, full25% gas review and real Cast produce a saved, genuinely unmined reset hash at old nonce0 |
| Fence the old actor | Driver requests stop, closes its submission gate and releases its lock without changing the pending journal; this is not a full supervisor/off-host fencing proof |
| Revoke and grant | Genuine governance revocation executes at transaction index0; the old reset executes at index1 in that same canonical block and reverts. A separate successful governance transaction admits the replacement |
| Recover | After twelve genuine descendants, a new stock Keeper instance uses the exact old config/journal and authenticates the original hash, receipt, signed fields, canonical header and reverted gas cost; no resend |
| Reject old authority | The reset read from the old sender returns exact `Unauthorized()`; mapping/authorization checks preserve the intended role boundary |
| Reject identity reuse | Loading the old journal with the new sender refuses before RPC or submission, without changing its bytes |
| Start replacement | Explicit dry initialization requires the unused new wallet's latest/pending nonce0 and missing state. No old pending record, nonce, receipt anchor or spending is copied |
| Execute replacement | One genuine protected reset succeeds at new nonce0; canonical recovery advances its own journal to nonce1. Old recovered journal bytes remain unchanged throughout |

The old recovery cycle correctly returns false after recovery: its later role
check refuses new work by the revoked address. Saved state and logs distinguish
that expected authorization failure from a failure to recover the receipt.
Both actors are distinct from governance and are not guardians. Existing unrelated
keeper grants are left unchanged; this does not claim the replacement is the only
authorized keeper globally.

Before/after NFT owners, shares, membership, royalty weights, current LP claim
components/liabilities, compound/buyback reserves and main LP identity, liquidity,
ticks and clock match. No LP swap, contribution, harvesting, payout or reward
allocation is executed in this reset-only case. It does not requalify those engines.

## Independent receipt, cost and journal verification

The separate [saved-vector review](evidence/INDEPENDENT_REVIEW.json) passes using
only retained public transactions, receipts, headers, intents, states and exact
events. It independently checks governance calldata/events and ordering, both
reset identities/statuses, twelve-confirmation depth, original fee reviews,
canonical execution charges, precise nonce/anchor/spending updates and final
oldfalse/newtrue role getters. The before-grant newfalse read is an executed-source
assertion; it is not invented as an extra stored getter vector.

| Old reverted reset | New successful reset |
| --- | --- |
| Gas33,196; signed allowance69,364 | Gas52,691; signed allowance69,364 |
| Canonical1,000,000,142wei/gas | Canonical26wei/gas |
| Cost33,196,004,713,832wei | Cost1,369,966wei |

Combined actual charge is33,196,006,083,798wei; combined captured maximum is
138,728,011,583,788wei, below the unchanged shared0.05ETH lab ceiling. Each
transaction stays below24M/full25%,5gwei and0.01ETH. The governance ordering input
is2gwei legacy gas price, also bounded before submission. Actual ordering is
verified after inclusion; this is not a promise about public mempool ordering.

Production spending counters are **per sender journal**, not an automatic global
cross-key ledger. New state correctly starts with empty spending. The private
driver separately enforces the shared old-plus-new budget; operators must review
remaining project-wide spending and unresolved commitments when rotating keys.

No raw signature, key, password or keystore contents are exported. New disposable
journal snapshots contain public operational fields only; their exact original
bytes/hashes are retained. Original real environments/journals are never adopted.

## Original failures and coherent test-node inputs

The c801 aggregate remains [failed](evidence/c801/RESULT.json):1,031 requests,
five setup transactions and one raw forwarding attempt, with no accepted hash
recorded. Cast returned nonzero; its original node answer was not captured.
Forwarding alone is not proof of node acceptance or of a particular rejection.
The exact original hashless journal is [preserved](evidence/c801/ORIGINAL_HASHLESS_JOURNAL.json),
SHA256`94a8462aae3ced330a02d44552d72842059f38124161eee5f9acb65877943924`.
It is not cleared, relabelled, retried or retrospectively declared recovered.

A separate c802 diagnostic changes only response capture and the fresh lab path.
Its [actual answer](evidence/c802/rotation-RAW_SUBMISSION_RESPONSE.json) is
error-32003: priority fee exceeds maximum fee, with captured maxFee142wei and
no accepted hash. Its false aggregate remains. This authenticates c802's cause,
not a reconstructed c801 response. Request payloads/signatures are not recorded;
the actual answer is returned unchanged to Cast.

The inconsistent isolated input came from disabling normal Anvil minimum-priority
enforcement while the signer still used its priority-fee recommendations. c803
restores normal enforcement, starts the local gas-price input at1gwei, captures
[actual gas/priority/history responses](evidence/c803/rotation-FEE_INPUTS.json),
and uses a bounded2gwei governance ordering input. No keeper maximum, financial
guard, signing argument or production/default fee configuration is relaxed.
Schema1 remains selected; Nitro fee-profile2 is not adopted. These model prices
are not Robinhood fee or provider qualification.

Only these failed/previously uncompleted branches run in fresh clones; no old
passed test body, build, constructor/population suite or LP journey reruns.
Original c801/c802 sources, journals and failures remain separate.

## Operator impact and remaining qualification

The [operator guide](../../docs/OPERATOR_MANUAL.md#pending-transactions-during-keeper-key-replacement)
and [recovery runbook](../../docs/KEEPER_RECOVERY.md#different-keeper-key-recovery-boundary)
now explain execution ordering, legitimate recovery updates, the post-recovery
authorization error, fresh-key identities, hashless uncertainty, permissionless
exceptions and cross-key spending review. Revocation does not undo a mined result,
cancel an EOA's other transactions or secure its compromised credentials.

All three new labs have empty process-group/stopped readbacks. The separate
[host comparison](evidence/HOST_PRESERVATION.json) preserves five original service
states and seven previously stopped labs, with zero non-ambient differences;
one pre-existing observer invocation change is separately identified. Existing
sites, Anvil8902, balances/NFTs/LP, journals, checkpoints, public-null configuration
and the user-paused heartbeat remain unchanged.

Keep Q06/P20/P21 open. This does not qualify a successful old call mined before
revocation, arbitrary nonce/backlog/hashless resolution, real compromise,
cross-host fencing/restore, full supervisor shutdown, sustained scheduling,
all lifecycle states, actual provider fees or independent release approval.
The old encrypted signing files remain available privately for constructor
validation; recovery without signing material is not newly demonstrated.
