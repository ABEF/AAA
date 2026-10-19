# Website and concurrent API: scoped verification

2026-10-19. Internal verification; production release remains NOT APPROVED.
Publication identity is established by Git HEAD/origin/main in each repository.
Website changes are published on main as `7396314456dc345326f345313bc415786e123036`.

## Source scope and findings addressed

- The previous HTTP server processed one request at a time. A slow earnings or
  preparation request blocked unrelated users. The entry points now lease bounded
  independent supervisors, each creating a fresh child Projection/RPC/history
  context, while HTTP connections have a separate pre-thread admission cap.
- An inactivity timeout alone allowed a continuously trickled body to hold a
  connection. Absolute ingress/connection timers and bounded header reads now
  complement the existing body and child-work limits. Expired ingress cannot
  dispatch work even if its timer callback is late. Ambiguous GET framing is
  rejected before upstream calls; disconnected clients do not trigger replay.
- A temporary-directory cleanup error could release a supervisor for reuse.
  Failed cleanup now quarantines that slot; healthy slots continue, and operator
  intervention is explicitly logged. No unbounded replacement loop is introduced.
- Main website preview reads replayed identical history repeatedly. One immutable
  exact-storage/epoch snapshot is now reused, with persistence checked every time.
  Changed data, reset, corrupt/failed storage and unsuccessful writes do not become
  stale successful balances. Legacy event meanings and economics are unchanged.
- Unsent preview actions now expire after 15 seconds and are cancelled on pagehide;
  changing tabs alone remains allowed. The local website's confirmation adapter
  rejects missing/nonfinite/unbounded expiry, wrong chain/revision and missing
  confirmed state. Preparation time consumes its deadline, with monotonic and wall
  time checks. Request extras cannot override the selected wallet or action.

## Executed checks

| Check | Result and limits |
| --- | --- |
| Python HTTP/worker scope | **47 passes**, zero failures/skips in the final current-source run, 8.483s. Sixteen concurrency cases, 14 mint/claim HTTP cases, six activation HTTP cases, four read HTTP cases, six worker supervision cases and one transaction-worker spawn case. |
| Website scope | **90 passes**, zero failures/skips, 566.6425ms. 21 UI-state, 33 local-client/view and 36 domain/wallet cases; ten new cases cover cache invalidation/immutability, expiry, context and duplicate-intent rejection. |
| Actual HTTP burst | Forty requests via twelve caller threads against two fake upstream slots/four HTTP connections. Every response is its own identifier or explicit 503 busy; independent user progress, recovery and no response crossover are asserted. This is an admission/isolation test, not a real RPC throughput measurement. |
| Process checks | Two actual parallel spawned children receive distinct payloads and are reaped. Existing blocked-child termination, partial/oversized/expired output, input rejection and cleanup tests passed on current source. Failed cleanup refuses a new child; fake pool tests verify other slots remain usable. |
| Hostile/disconnected clients | Duplicate/ambiguous framing, oversized line/aggregate headers, trickled bodies, stalled headers, disconnects and sanitized unexpected errors checked over real loopback sockets. Timers are shortened in these focused tests. |
| Main website browser | Reloaded the running 4179 site, retained selected demo wallet and the user's four current positions, opened/closed #444 Grow attached LP details. No browser console errors. Did not reset or change the user's example holdings or the separate running Anvil session. |
| Syntax/build | Changed JS syntax checks passed; static build completed with **5,588 files**. No new dependency. |

Commands run from their respective repository roots:

```sh
python -m unittest tests_python.test_http_concurrency tests_python.test_frontend_transaction_http tests_python.test_frontend_activation_http tests_python.test_frontend_api.FrontendHTTPTests tests_python.test_request_limits.WorkerTests tests_python.test_wallet_preparation.WalletWorkerTests -v
node --test tests/ui-state.test.mjs tests/local-client.test.mjs tests/domain.test.mjs
node --check app.js
node --check ui-state.js
node --check preview-store.js
node --check local-client.js
node build.mjs
```

The initial 15-case concurrency run had twelve passes, two fixture expectation
failures (HTTP converts token IDs to integer before the fake service) and a Windows
ConnectionAbortedError instead of EOF/reset during deliberate socket shutdown.
Corrected those expectations, added the late ingress callback guard/test and ran
the complete affected scope: 47 passes in 8.270s. Final review then moved cleanup
quarantine before lock release, including direct WorkerClient callers; the updated
cleanup regression asserts that ordering and refusal of another child.

The next 47-case rerun took 8.294s: 46 passes and one Windows socket-reset
error in the duplicate-header fixture. That fixture sent its body separately after
malformed headers could already have caused an early rejection/close. It now
requires header rejection before sending any body, within a one-second timeout,
and checks no RPC work occurred. The corrected single case passed in 0.119s.
Further review moved the quarantine check inside admission as well: a caller
preempted before acquiring the lock must observe the preceding request's failed
cleanup. An interleaving assertion now proves it cannot spawn another child.
That final worker change justified the final complete affected rerun: **47 passes,
8.483s**, recorded in [the log](python-tests.log). No failure was silently counted
as a pass; unrelated broad Solidity/artwork suites were not rerun.

[Source bindings](source-bindings.json) identify the implementation and affected
test files used by these checks. Previous source-bound receipts remain historical;
this report does not relabel them as a new full regression or independent audit.

## Review and remaining boundaries

Using threads around one shared Projection would not safely isolate RPC/snapshot
and mutable bookkeeping. Production entry points therefore use WorkerPool, never
a concurrently shared Projection. The pool has no waiting request queue and each
child is reaped before its healthy slot is returned. Connection limits apply even
before parsing, and the accept loop uses a bounded busy-response write. Errors
expose fixed codes, not upstream exception content. Existing hash/read-only,
request-budget and unsigned-transaction boundaries remain in place.

No Solidity, contract economic rule, activation loss limit, price source, public
signer or local launcher locking changed. These listeners still only prepare
unsigned transactions. The main site is a simulation; its browser locks cannot
coordinate real users on different devices. Local /app/ confirmation hardening
is website code, not a production wallet integration. Real shared-pool transaction
races, nonce/replacement/reorg recovery, Linux and provider load tests, ingress
fairness, complete historical workloads and independent review remain open.
Defaults multiply across processes and can still exceed provider capacity; use
the [operating procedure](../../docs/CONCURRENT_SERVICES.md) before hosting.
No public deployment, service restart or monitor restart occurred.
