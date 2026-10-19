# Royalty reporting: scoped verification - 2026-10-19

Baseline: `e705a7aca43ff59af17ea4666f1a25c57cd5afc1` on `main`.
This delta changes backend reads/history and the generated event schema. It does
not change Solidity, deployment configuration, a website or a running service.
Release remains **NOT APPROVED**. Read the [integration/operator guide](../../docs/ROYALTY_REPORTING.md)
and [internal review](REVIEW.md).

## Executed checks

| Run | Result | Scope |
| --- | --- | --- |
| Initial focused run | **138 passed**, 0 failures/errors/skips | Royalty reporting, read API, ownership/claim history, predecessor lineage, lifecycle, indexer and generated event schema |
| Supplemental run | **20 passed**, 0 failures/errors/skips | Three added dormant/owner/historical-currency cases and 17 existing request-limit/worker cases |
| Existing compiler/source verification | **40 Solidity sources matched**, ten getter ABIs and 26 added event schemas verified | Reused normal royalty-conversion compiler artifacts; no rebuild or Solidity test rerun |

The [initial receipt](attempt1.json) and [log](attempt1.log),
[supplemental receipt](supplemental.json) and [log](supplemental.log) record separate
runs. Published log copies normalize line endings only; captured originals remain
in the external local evidence directory. The initial 17 new test bodies and production backend code did not change
before the supplemental run. Three edge cases were appended; these were run with
the request-limit tests rather than repeating the unchanged initial suite. This
is not a single fresh full regression or target-network rehearsal.

Both runs used an exported published baseline with only the six intended code,
schema and test files overlaid. Unrelated unpublished server/transaction/route and
history-test drafts were excluded. Receipts bind all input files before/after each
run; existing input bytes did not change during execution. The additional
`execution-result.json` is test output, not an input. The final
[source and ABI record](source-and-abi.json) binds the exact intended files and
records unchanged initial test bodies.

The generated schema now includes 101 events. All 75 previous entries are
unchanged; 26 previously missing current-source events were added, including
royalty conversion/eligibility and canonical/stop-control events. Each added
signature, topic hash and indexed layout matches an existing compiler ABI whose
source metadata matches current Solidity. The prior [royalty build and tests](../royalty-conversion/VERIFICATION.md)
keep their original evidence scope; they are not new runs for this backend delta.

## Covered behaviors

- Explicit current-ledger profile and strict configuration; legacy callers retain
  strict asset behavior and do not implicitly probe new eligibility getters.
- Eligible/deferred/inactive states, native and original-currency balances,
  converter disabled/unbound/missing-pin/runtime-drift states, no invented ETA.
- Failed balance or token metadata/runtime reads return sanitized unavailable/null
  amounts while healthy currencies remain visible. A shared failed token also
  affects its LP balance view. Invalid core bindings/eligibility still reject.
- Work-limit failures propagate through currency/converter reads. Existing serial
  request supervision checks include deadlines, busy workers, partial/oversized
  output and cleanup failure. Snapshot expiry/reorg rejects the complete response.
- Exact raw conversion logs are separated from actual claims and other NFTs;
  malformed topics/data, unknown source, unminted IDs and impossible zero-source
  credits reject. Decoded indexer labels cannot manufacture a claim.
- Only an actual later payout increases cumulative claimed amounts. NFT owner
  changes preserve the balance/reporting association in the read projection.
- Two verified same-chain handoffs preserve conversion totals without importing
  the current profile into old deployments. Missing lineage stays unavailable;
  historical source currencies remain represented when absent from current assets.

## Limits and remaining work

Fixtures exercise backend behavior, not live marketplace settlement or an actual
conversion transaction. The read profile cannot qualify router/feed/wrapper gas
economics, promise keeper timing or authorize a claim. Complete raw-log ingestion
and RPC archive responses remain operator/provider trust assumptions; source
checksums and internal tests are not consensus finality or log-completeness proofs.

The implementation exposes lifetime conversion credits and actual paid totals,
not gross earned 24-hour/all-time revenue or historical USD values. Website
integration, production hosting/client compatibility, actual token outages,
conversion recovery rehearsals and independent audit remain in the
[central Todo](../../TODO.md#task-royalty-reporting). No signer, public transaction,
contract deployment, server change or monitor restart occurred. Published commit
and exact-commit CI status must be established separately from these local receipts.
