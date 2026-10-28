# Verification and reuse boundary

Base: `ae56de6d3b4c57e0ffb60f0a54cd3d74084d0b31`, main. Full method identities,
source hashes and selection references are in [the summary](verification-summary.json).
External diagnostic receipts are indexed by [SHA-256](external-artifacts-sha256.json).
This is source-scoped local evidence, not release approval.

## Fresh affected verification

**399 distinct Python methods:398 passes and one explicit missing-cast skip.**
53 new regression methods are included once. These are a union of the following
affected selections, not one frozen whole-suite run or a sum of overlapping runs:

| Selection | Result and scope |
| --- | --- |
| Keeper reset/raw-state recovery | 48 confirmation methods pass;181 raw/historical/native/canonical/preparation/harvest/compound methods yield180 passes/one missing-cast skip. Exact reset-scope pins precede the later parent heartbeat integration. |
| Final policy health and actual heartbeat writer | 21 distinct methods pass at final source:16 policy/admission cases and five heartbeat-path cases. A prior direct imported TestCase caused duplicate discovery; its37 results are not counted as37 distinct methods. |
| Final existing ops/telemetry compatibility | 29 methods pass at final health/monitor source, with no source drift. |
| Final physical schema6 inventory | 56 methods pass, including15 new physical consistency methods. Earlier52-method receipt overlaps and is not added. Installed v4-periphery1.0.3 PositionInfoLibrary/PositionManager and v4-core PoolId bytes are pinned. |
| Portfolio, collection and terminal-holder compatibility | First wider64-method run retained61 passes plus three explicit fixture/harness failures. Two corrected fixture cases and the final31-method portfolio selection pass; the HTTP case passes separately under a restricted loopback harness. Repeated IDs count once. |

Inert parent runners disable outbound sockets and subprocess execution. The one
HTTP dispatcher check permits only an ephemeral127.0.0.1 listener created by that
test and its own connections; it cannot contact other listeners or preserved
Anvil/services. Synthetic dependency adapters do not qualify real providers.

Negative controls retain the pre-fix keeper foreign-record/raw-read failures,
portfolio contradictions, opposite physical side/raw-false acceptance and a
foreign-pool LP accepted without a PosM PoolKey read. Intermediate failures are
not deleted or relabeled passes. The first portfolio work-bound expectation was
updated for the required extra custody read; a holder-exit test fixture now
declares explicit historical feature versions. The HTTP failure in the inert
runner was a harness restriction, resolved only by the restricted loopback run.

Agent exploratory ops runs without contemporaneous source pins are not claimed
as final-source receipts. The summary uses the final parent-pinned21/29 scopes.

## Unchanged contract evidence reused

No source Solidity or Solidity test changed. Exact142 execution-source/test pins,
46 normal production source pins, dependency pins and build-input pins match the
[previous implementation evidence](../practical-improvements-20261028/VERIFICATION.md).
Its **217 affected Solidity passes and39 normal object-size gates** are reused,
not rerun or added to the fresh Python count. ABI/storage/rights and existing
bytecode headroom are unchanged. Exact release arguments and full target gas
remain unqualified; the prepared cold-one-venue patch stays unexecuted.

## Preservation and limits

The four pre-existing dirty tracked files remain byte-identical to the saved
baseline;2,220 historical report files retain their bytes. The205 committed
source/doc baseline files and raw current receipts remain under the external
`confirmation-second-review-20261028` directory; physical-reader receipts are in
`second-review-readers`. Git publication is verified separately from local saves.

No source publication deploys code or changes installed services, websites,
preserved local-chain state, journals, browser signing or the paused monitor.
Real dependency/provider/fee/route qualification, current frontend acceptance,
cadence/gas/host rehearsals and independent audit/remediation remain open.
