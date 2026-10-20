# Mint confirmation and local read performance

Date: 2026-10-20. Internal, scoped follow-up; production NOT APPROVED.

## Observed behavior and changes

The user reported that a new NFT appears after Recover status. The inspected
local mint `0xf997b6d9dc1b776fa34b9fc00b02ff1fc27d3ccc168fadaac6be6a673a0baa42`
succeeded in block 234. Its exact original UI error was not captured, so the
15-second wallet-response deadline is a concrete weakness, not a proven cause
of that specific incident.

- Separate the human wallet response wait (90 seconds, bounded at 120) from
  RPC reads (15 seconds). Keep one send, durable intent and late-hash recovery.
- Retry receipt-read failures using the same hash, within the existing three
  attempts and 750ms interval. Persistent faults retain recovery; canonical,
  economic and reviewed gas checks are unchanged.
- During an ordinary same-account/session refresh, keep labeled last-confirmed
  cards and disable actions. Failed reads, context changes and pending NFT
  contributions retain their existing isolation rules. No optimistic LP update.
- Reuse one HTTP connection only during a serialized local portfolio read to
  literal 127.0.0.1. Close after completion/error, refresh socket timeouts against
  the work budget, reject redirects/oversize responses, and preserve per-call
  chain/JSON-RPC checks and exact-hash read memoization. Default production RPC
  transport remains unchanged; no public keepalive optimization is enabled.

## Verification

| Check | Result |
| --- | --- |
| `node --test tests/browser-wallet.test.mjs` | 48 passes, four new cases |
| `node --test tests/contribution-flow.test.mjs` | 8 passes, one new case |
| `python -m unittest tests_python.test_rpc tests_python.test_local_stack tests_python.test_local_rpc_connection -q` | 35 passes, including eight new transport cases |
| `node --check local-view.js`; `node build.mjs` | Passed; 5,593 build files |

New cases cover slow wallet responses, no duplicate sends, temporary/persistent
receipt faults, bounded wait configuration, refresh-context isolation, actual
HTTP connection reuse, per-call chain reads, request budgets, disconnects, HTTP
redirect rejection, response limits and retained identity/write restrictions.

An isolated local read profile identified hundreds of new TCP connections.
Actual eight-NFT `/state` timing was 6.057 seconds before; after the web-only
replacement, 3.723 seconds cold and 1.904 seconds warm. These are individual local
observations, not throughput or percentile guarantees. The read endpoint advances
empty confirmation blocks as before; no holder/operator test transaction was sent.

The authenticated fixed-fixture restart preserved the original Anvil process,
session, operation revision22, and all eight owner/position/claimable/trait records.
Only web process25784 was replaced by21472. The recovery helper and session
material remain external, outside Git. See [sanitized measurements](mint-speed-verification.json)
and [source bindings](mint-speed-source-sha256.json).

No new extension-signing acceptance is claimed from unit tests or the RPC-shaped
adapter. Actual extension recovery scenarios, production services/manifests,
independent audit and release approval remain open. The 10/25/100-user campaign
remains deferred. No Solidity change/rerun, public deployment or monitor restart.
