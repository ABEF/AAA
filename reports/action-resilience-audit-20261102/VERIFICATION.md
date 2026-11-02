# Action resilience verification

Reviewed2November2026. [Findings/fixes](REVIEW.md), [action outputs](ACTION_MATRIX.md),
[exact method/stage ledger](tests.json). Internal assessment, not release approval.

## Executed stages and preserved failures

| Stage | Result | Interpretation |
| --- | --- | --- |
| Initial negative controls |8 parent methods;10 subtest failures,2 subtest errors | Reproduces streaming and ignored-key gaps. Initial pending fixture also omitted saving its in-memory intent; this test-fixture mistake is retained, not counted as a source defect. |
| Corrected pending negative control |1 parent method,3 errors/subcases | With the intent saved, original code blocks startup on invalid boolean values, or ignores the unsupported setting and reaches unrelated fixture lifecycle gates. No paid-state reset is used. |
| Repaired regressions |8/8 pass | Timed fragments/request budget, header-time consumption, valid fragmented JSON, global/override keys, paid recovery/restart, source6 one-minute fault and rapid reversal. |
| Affected transport/request/HTTP selection |63 methods;59 passes,4 error occurrences | Process tests cannot spawn safely under the external evidence driver without a main guard. These errors are not attributed to application code. |
| Affected upkeep/recovery/API selection |106 methods;104 pass,1 failure,1 skip | The inventory test needs the new non-prefix module in its exact expected set. Unix permissions/ownership remains explicitly skipped on this Windows host. |
| First correction attempt |4 methods;1 inventory pass,3 worker errors | Inventory is corrected; an attempted shell edit failed to install the driver's guard. This unsuccessful retry remains recorded. |
| Dedicated guarded driver |3/3 process methods pass | Actual isolated process success, blocked child termination/recovery and parallel isolated payloads/reaping. Only failed methods are rerun. |
| Actual HTTP reader compatibility |1/1 new method passes | Real loopback urllib/HTTPResponse handles both Content-Length and chunked fragmented replies. Only this added method runs; the previous8 regression bodies are unchanged. |

There are **176 distinct successful selected Python methods across these stages**,
plus one Unix-only skipped method. This is not a new combined176-method run or
full suite. Subtest occurrences are not distinct parent methods. Failed attempts
and fixture/driver mistakes remain visible. Methods already passing unchanged
are not repeated to manufacture a clean broad transcript.

The focused keeper inventory now selects851 unique methods, including the new9;
the inventory command executes **zero** test bodies and is not added to176.
Its exact membership assertion remains strict. The [test ledger](tests.json)
binds source hashes, selections, individual outcomes and raw log/report hashes.

## What the checks verify

Fresh checks include chain/reply identity, malformed/parser/size rejection,
bounded retry, response/error socket cleanup, fragmented-body budgets,
request-local expiry, worker admission/termination, concurrent loopback HTTP,
maintenance input validation, exact pending receipt/nonce/spend recovery,
policy6 readiness/reset semantics, unrelated-job priority and API price-outage
ownership/raw-claim availability. No signing, public RPC, service rollout or
existing local-chain operation is performed.

Timed-stream and source6 price/market transcripts are deterministic substitutes.
Process tests exercise real local spawned workers; they do not qualify actual
providers, DNS, TLS, keepers, target chains or100-user production browser traffic.
An attempt/progress deadline does not forcibly preempt every blocking header,
chunk-metadata or OS call. API process supervision and keeper watchdog/provider
qualification are separate boundaries. Unix permissions and sustained off-host
operations remain open, not silently treated as passes.

## Reused contract evidence and preservation

All52 production Solidity sources and31 normal-build dependencies match
[43 normal gates](../lp-lifecycle-audit-20261102/production-size-gates.json)
at final-a8e7dc7cc5. Prior475-record internal static disposition and
[six-day actual-core evidence](../portfolio-long-horizon-20261102/VERIFICATION.md)
retain exact original scopes. No Solidity recompilation or unchanged contract
test repeat was necessary for these Python fixes. No ABI, bytecode, ownership,
economic, timing, financial or custody policy changed.

[Preservation](source-preservation.json) binds the base revision, four unrelated
dirty-file hashes,52 production hashes and2588 historical report artifacts.
Original guides/runtime modules, negative controls, partial runs and worker
drivers remain externally under
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/action-resilience-audit-20261102`.
No production service/site/Anvil/NFT/LP/balance/journal/signer/heartbeat changed.

[Final checks](FINAL_CHECKS.json) cover generated Todo/reference, current links,
exact-source static reuse and staged Python publication. Exact committed import
closure and remote main are verified separately in external publication evidence.
Source publication does not install this behavior on running systems.
