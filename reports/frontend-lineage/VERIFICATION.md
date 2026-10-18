# Same-chain lifetime claim verification - 2026-10-18

**Development evidence, not production approval.** This extends the read API;
production Solidity, the website and existing staging are unchanged. No contracts
were deployed, transactions submitted or paused monitor restarted.

| Check | Result | Scope |
| --- | --- | --- |
| [Exact publication snapshot](publication-tests.json), [case log](publication-tests.log) | 91 passed; zero failures, errors or skips | 17 new lineage cases plus 74 existing API, lifecycle and history cases; real local Indexer/SQLite replay with synthetic RPC deployments |
| [Reused compiler ABI](abi-check.json) | Two getters and two event layouts match; four source identities bound | Normal coordinator artifact for `handoffId`, `stateRoot`, `Retired` and `Activated`; no new compile or Solidity run |

The baseline is `d27c20197b7aacfab240559c2fe2dfe33526d115`. The final
publication snapshot overlays only `frontend_api/lineage.py`, the integration in
`frontend_api/service.py` and `tests_python/test_frontend_lineage.py`. It excludes
unrelated saved wallet POST, quote/process-runner and artwork drafts. Hashes before
and after execution match in the receipt. This is one 91-case run; earlier scoped
15-case and two-case development checks are not added to that total.

The successful fixture spans three deployments and two handoffs. It uses actual
raw-log ingestion and replay, includes previous owners' LP/royalty claims, and
allows predecessor indexes to stop at retirement. Additional checks cover a new
NFT minted after replacement and a historical claim asset no longer admitted by
the current deployment. Current claimable funds do not increase through replay.

Failure cases exercise missing/reordered/duplicate predecessors, missing original
identity, wrong lifecycle/runtime/ordinal, conflicting asset decimals, oversized
configuration, missing or reverted receipts, orphaned blocks, wrong roots/peers,
malformed log provenance/order, duplicated retirement events, unavailable archive
state, incomplete ingestion and historical-anchor changes during the request.
Without predecessor configuration, successor lifetime totals remain unavailable;
invalid configured lineage does not return a partial sum.

The internal review specifically checked that an intermediate successor can
later retire with a different outgoing root, that chronological ordering uses
block/transaction/log position, that only the queried NFT's amounts are summed,
and that historical creation/retirement headers are checked again after replay.

These tests do not establish RPC honesty, cryptographic log completeness,
consensus finality, independent replacement-code safety or production latency at
the configured bounds. The service relies on reviewed deployment pins and
operator-maintained complete indexer coverage. Live archive service qualification,
retention/backups, consumer integration and independent review remain under
[hosted services](../../TODO.md#task-host-services) and
[live history UI](../../TODO.md#task-live-history-ui). Cross-chain history and
proof-based retirement remain in the
[canonical migration requirement](../../TODO.md#task-security-chain-recovery).

No unchanged Solidity, gas, static-analysis or broad unrelated Python checks were
repeated. See [the implementation reference](../../docs/FRONTEND_LINEAGE.md) for
configuration, bounds and trust assumptions; release remains **NOT APPROVED**.
