# History export/reload diagnosis — 24 November 2026

The targeted replay identifies a **response-size refusal**: Anvil declares a 25,625,277-byte HTTP response, and the unchanged reader stops at 16,777,217 bytes (16 MiB plus its overflow sentinel). Export and reload remain unsuccessful. No cap or safeguard was raised.

The confirmed correction is diagnostic retention: the old fixture kept only `ValueError`, losing the failing guard. The new isolated driver retains the stage, fixed guard, request ID, status, observed byte count, deadline state and bounded traceback before refusing. Unknown exception text is hashed rather than published. Its [report-only diagnostic function](tooling/export_failure.py) has the same AST as the executed function; this is not an adopted backend module or production rollout. [Source boundary](verification/SOURCE_BOUNDARY.json).

## What actually ran

| Partition | Result and limits |
| --- | --- |
| Empty-chain codec | Original Node/capture code exports and reloads both omitted parameters and `[true]`; zero transactions. True includes the history field, but this proves no populated history. [Receipt](verification/EMPTY_CODEC.json) |
| Affected state preparation | Replay of exactly 44 captured, zero-value local setup envelopes reconstructs 39 instances. The reviewed driver checks original nonce/gas-price/value/calldata, successful receipts and matching gas used, actual CREATE returns/runtime code, genuine NFT-contract creation history, an authenticated exact genesis bytecopy and final nonce150. No compiler, estimates, old constructor runner or unchanged test bodies run |
| Populated export | Request1817 fails at original `Node.wire` line130: HTTP200, declared25,625,277 bytes, observed16,777,217. Neither the response nor whole-node deadline expired. Before it,1,816 records/7,985,646 encoded bytes remain below6,000/64MiB. [Refusal receipt](verification/REPLAY_REFUSAL.json) |
| Reload | **Not reached.** No complete dump is retained. Compressed/decompressed size, reloaded bindings, all historical account slots and full roundtrip are not measured or claimed |
| Preservation | Original ten pinned evidence files,113 fixed source/helper members and genesis bytes remain unchanged according to the executed driver. All seven owned labs stop; five existing service states match the new pre-diagnostic snapshot. One ambient observer invocation ID is explicitly excluded. [Comparison](verification/ENVIRONMENT_PRESERVATION.json) |

The replay uses the same complete controlled genesis and captured setup inputs, with no pruning, batched mining, fabricated history or artificial clock changes. Later block timestamps can differ; equality to the old final state root is not claimed. Constructor dependencies remain declared doubles, and the graph remains unsealed/unpopulated. These are local setup transactions, not public deployment or financial/API acceptance.

The original c7e6 refusal still has **no recoverable exact guard**. The new run proves its own size failure; it does not retroactively prove which guard failed previously. The available result is authenticated aggregate execution/diagnostic evidence plus reviewed code, not a new independent per-receipt wire audit. See the [original static boundary analysis](verification/STATIC_DIAGNOSIS.json). Earlier failures and their original bytes remain preserved.

## Format and safeguards

Primary [Anvil v1.4.4 source](https://github.com/foundry-rs/foundry/blob/v1.4.4/crates/anvil/src/eth/backend/mem/mod.rs) confirms that `[true]` returns hex-encoded gzip JSON with retained history. CLI reload accepts the decompressed JSON. The existing format is correct; blindly changing encoding or adding flags is not a fix. The [CLI source](https://github.com/foundry-rs/foundry/blob/v1.4.4/crates/anvil/src/cmd.rs) also makes `--init` conflict with the CLI dump/preserve/load options.

The layers remain separate:16MiB total HTTP response,16MiB compressed file,16MiB decompressed state,64MiB encoded capture,6,000 requests,30 seconds per response and900 seconds per node. Hex framing consumes response budget before decoding. No larger response, hidden chunk aggregation, latest-only dump or shortened history is admitted. Full-body/decompressed size is unknown after this refusal.

## Remaining recovery requirement

A faithful complete snapshot cannot pass this measured HTTP path under the current response bound. Keep portable full-state recovery and actual F6/V10 consumer qualification open. The next design must preserve required historical reads within the existing budgets; if no faithful bounded representation fits, an explicit isolated-snapshot budget decision is required. A checkpoint, saved code proof, replayed logical graph or latest-state dump must never be relabeled as full historical recovery.

Todo and the operator procedure now name this exact blocker and the staged diagnostic requirements. Production source/F6/build identities, financial rights, default budgets, public signer/null configurations, original DB/checkpoint/journal bytes, sites, Anvil8902 and the user-paused heartbeat remain unchanged. No public transaction, sealing or live rollout occurred. Current23-package/83-task statuses are retained.

Only the new codec and affected recovery partitions ran. An early pre-freeze local pin refusal and a local new-folder access failure occurred before upload; their records stay private. The final reviewed bundle ran once. No unchanged wallet, browser, Solidity, gas or prior backend test suite was rerun. Detailed host records and runtime archives stay outside Git.
