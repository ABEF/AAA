# API work limits and operator procedures - 2026-10-19

**Development evidence, not production approval.** Parent publication is
`19f63548c8e850a29be8a017cdd37d984b8c8959`. No Solidity, public signing,
deployment, website/server change or monitor restart is included. Unrelated
working drafts are excluded from the tested/published snapshot.

## Implemented remediation

The [daily audit](../daily-security-20261018/REVIEW.md) found safe final rejection
but excessive work after quote expiry (AUD18-03). Shared ContextVar budgets now
cover projection, predecessor/history and complete activation preparation:
25-second monotonic duration, 1,024 logical RPC calls, 2,048 actual RPC POSTs,
retry/backoff charging and snapshot/quote expiry shortening. WorkLimit is terminal,
not another transport retry. SQLite uses query progress and row checkpoints.

HTTP entry points run each read-only request in a spawned, serial worker with a
30-second parent deadline and terminate/kill cleanup waits of up to one second
each. Missing/partial/oversized/expired output is rejected. An uncertain live
worker poisons admission. Cleanup failures are sanitized and release the lock.
Logs exclude upstream error text, payloads and configured endpoints. Direct
library callers get cooperative budgets, not the HTTP process supervisor.

The new confirmed `GET /v1/mint-readiness` distinguishes unfulfilled original
requests from fulfilled draws awaiting ordered finalization. It checks inventory,
quotas and ordinal/request provenance at a canonical hash. Funding, liveness,
request age and other handoff requirements are not inferred. It cannot reveal,
select artwork, reroll or approve a replacement.

## Scoped checks

| Check | Result / evidence |
| --- | --- |
| Affected API, activation, HTTP, history, lineage, lifecycle, RPC and worker suites | [164 passes](targeted-164.json), [log](targeted-164.log); isolated HEAD plus intended edits |
| Final cleanup hardening and readiness HTTP observation | [24 passes](worker-readiness-24.json), [log](worker-readiness-24.log); includes two new cases; only these suites needed repeating |
| Combined current coverage | [166 distinct checks](coverage-reuse.json): 142 retained unchanged cases plus 24 final worker/readiness cases; not one newly executed full run |
| Original expiry reproduction | Now stops after the first expired code observation, before subsequent calls and before either trace |
| Windows process containment | Actual spawned child starts, blocks, is terminated/reaped, and a following request succeeds; bounded/partial results and cleanup failure are checked |
| Solidity/build reuse | [78 dependencies match](solidity-reuse.json), including all 39 production sources; unchanged Solidity/static suites and size builds were not rerun |

Tests use local/mock RPCs and loopback HTTP. No real provider funding, VRF
fulfillment, public RPC performance or Linux service qualification is claimed.
Earlier failing diagnostics are preserved: [140-case run](diagnostic-140.log)
found obsolete expiry-boundary expectations and one intermittent Windows socket
close; [158-case run](diagnostic-158.json) had 157 passes and one SQLite fixture
without the new progress-handler interface. Only fixture expectations/forwarding
were corrected; production fail-closed behavior was not weakened. An earlier
48-case diagnostic had one obsolete exception expectation failure and no retained
raw receipt; it is not counted as pass evidence.

## Operator decisions and documentation review

The [manual](../../docs/OPERATOR_MANUAL.md) was checked against current controller,
Registry/Entry/asset, Strategy, Oracle, Vault/budget, Migration, handoff, fee,
royalty, NFT and keeper interfaces. It documents rangeBps as per-side width,
full-config changes, immediate governance, coupled parameter limits, source
versus LP routes, finite historical capacity, disabled-dependency fallback,
parking/resume, exact funded abort and irreversible retirement. Deposit limits
are cumulative gross contributions per NFT, not live pool TVL ceilings.

Repository instructions and [Todo maintenance](../../docs/TODO_WORKFLOW.md)
require same-change manual updates or explicit no-operator-impact reasoning.
The manual is a procedural reference, not an additional task-status list or an
operating-rehearsal certificate.

User decisions retained: no governance delay; only the existing 3% per-operation
maintenance cap; qualify/fund/monitor the original VRF and drain reveals before
whole-collection replacement. No pending-request carry, reroll or administrator
trait choice. Ordinary LP migration is unrelated to reveal completion.

## Remaining boundaries

Actual Linux cleanup/ingress/rate/connection limits and maximum real history/trace
workloads need qualification; fixed budgets can deliberately reject large/slow
requests and are not throughput guarantees. The 30-second supervisor has bounded
cleanup overhead and still depends on a functioning OS. Memory/resource limits
and external monitoring belong to deployment. The unused local mint/claim adapter
remains unpublished; this change adds no signer or transaction broadcast.

Provider selection/funding/alerts are open. A permanently unanswered VRF request
still blocks whole-collection replacement. Escrow compatibility, malicious
immediate governance, accumulated permitted costs and unsupported future-chain
recovery remain risks; see the central Todo. This internal review is not an
independent audit or a guarantee against vulnerabilities.
