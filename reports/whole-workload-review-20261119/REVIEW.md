# Whole-project workloads, functions and composed behavior

19 November 2026. Baseline main: `53ce73159004ec60031786b2c5c26af382dc1af7`.
Production remains undeployed and NOT APPROVED.

The scope is the complete project, rather than only the gas added by a residual
position. [The maintained plan](../../docs/WORKLOAD_PLAN.json) defines187 scenario
classes across17 contract/internal/shared families and7 service families, with
21 finer service subfamilies and85 additional partitions. Cross relevant cases
with role, lifecycle, market, population, currency, geometry, timing, input,
failure and interleaving dimensions. These counts are not executed tests.

A finite review cannot prove every possible numeric state, market or malicious
dependency. [The coverage guide](../../docs/WORKLOAD_COVERAGE.md) and
[scenario register](SCENARIO_REGISTER.json) make that distinction explicit.
Reachable state partitions, source-bound evidence and independent invariants
replace an unsupported claim of100% safety or dynamic coverage.

## Complete source/function inventory

The new [offline inventory tool](../../scripts/build-workload-inventory.py)
authenticates the trusted F6 build, function catalogue, compiler AST/settings and
all61 project/39 dependency/4 build-control source pins. It rejects a forged
positive manifest even when the caller supplies mutually matching fake inputs.
It compiles nothing, executes no application modules and has no RPC/signing path.

[FUNCTION_INVENTORY.json](FUNCTION_INVENTORY.json) records:

| Inventory | Count | Meaning |
| --- | ---: | --- |
| Callable contract objects |40| Every current catalogue object assigned to a reviewed family. |
| ABI rows |1,021|968 functions,40 constructors and13 receive hooks, with exact input/output/access descriptions. |
| Implemented project Solidity definitions |1,056| Public/internal/private source definitions from the authenticated AST. |
| Modifiers |29| Separately indexed; permission/callback guards are part of scope. |
| Bodyless declarations |511| Interfaces/declarations are separately counted, not claimed as exercised bodies. |
| Internal-only objects |8| Include the exact LP/royalty engines, asset/token/math/artwork/venue libraries beyond the public catalogue. |
| Production Python files |179| The unrelated dirty fork runner uses its published HEAD blob rather than adopting local work. |
| Python named lexical definitions |1,976|1,796 functions and180 classes; source inventory, not a test count. |

The [anonymous-code supplement](ANONYMOUS_CODE_INVENTORY.json) additionally records
276 Python lambdas and2 named project Yul helpers. Inline assembly/generator
bodies remain within their authenticated parent source and require semantic
review; enumerating them does not prove their correctness.

Eight new offline integrity-control groups pass: bad pins, duplicate contracts,
unmapped sources, a forged internally consistent graph, simulated source drift,
duplicate JSON, noncanonical paths and preservation of the protected HEAD blob.
The original control record and initial rejected draft remain explicit in
[INVENTORY_TOOL_CHECKS.json](INVENTORY_TOOL_CHECKS.json). The final plan changes
finding status duplication into evidence pointers; current generation/check is
verified separately without relabelling the earlier controls.

## Separate website source scope

The [published website scope](WEBSITE_SOURCE_SCOPE.json) binds website main
`f7dd399a4e5b5baaecd1d430a1b514f27e64b840`:29 production JavaScript modules and
1,178 function nodes, plus39 test/helper files and2,139 function nodes. Both HTML
documents have no inline script bodies/handlers;17 class nodes and nine logical
application components are included. Node24.13.1/bundled Acorn8.15.0 parses the
published blobs without executing application modules or installing dependencies.

This is AST/source scope, not fresh browser, wallet, renderer, shader or hosting
execution. Both null public configurations and Anvil-only signer are preserved.
The website's three project documents incorrectly presented the old Oracle3-byte
margin as current; their correction distinguishes historical evidence from F6
and notes that new backend pagination/checkpoint source has not been adopted.
No application JavaScript, served site, configuration or signer changes.

The [operational file map](OPERATIONS_SOURCE_SCOPE.json) also pins12 shell,
PowerShell and workflow entry files across the two repositories. They are
file-level obligations, not an assertion that every command executed. The
changed verifier passes a shell syntax check; no deployment/service workflow
or unchanged operational script ran. The website has no published automatic
GitHub workflow that would deploy these documentation-only commits.

## WG01: correct the obsolete independent market oracle

`OptionalPortfolioCore.t.sol` still modeled LP earnings as scaled1e36 individual
and collective fractions. Current Rewards uses whole-unit hierarchical
allocation. The selected existing mixed-residual journey failed by **one raw
unit** under that old model. This was a test-model defect, not an established
production accounting error. The baseline failure and an initial zero-test
selector attempt are retained separately.

The model now eagerly assigns every actual funded credit using an independent
rational carry formula. It replays actual share/membership events in order,
retains phase through weight changes and claims, and checks pre-operation
weights independently. It reads no production phase/pending/allocation book.
Individual and collective rights are checked separately; every allocated unit
must reconcile exactly with liabilities. Conversions are explicitly outside
this raw-unit oracle and cause an explicit refusal rather than guessed modeling.

**Nine methods pass:** seven affected market journeys and two new compositions:

- Bull/bear reversals and repeated one→two→one mode cycles.
- Mixed residual, pending merge, new activations/growth and current-owner transfers.
- Both positions outside, reference disagreement/recovery and observations whose
  clocks survive entrant actions.
- Royalty rights remaining separate through LP mode changes and terminal exit.
- Tiny raw fee tails, opposite claim orders, entrant dust barriers and complete
  claims with zero allocated rounding liability left behind.
- Raw residual close→attributed idle→same-main consolidation→Entry activation/
  growth→hybrid restart→whole merge→complete claims.

[Market evidence](MARKET_MODEL_VERIFICATION.json) binds exact methods, source,
tool/compiler and artifact hashes. The actual local v4 core/position manager
uses current production LP/reward/royalty source with explicit MockAccess,
registry, correlated feed/VRF/Permit2 and direct-mint seams. The eager model has
a bounded host-sized arithmetic domain, not arbitrary full-uint256 stress.

The test harness's1B allowance and45.9M–473.2M aggregate body gas cover many
serialized actions. They are **not per-transaction gas or cold32M qualification**.
No production Solidity, normal compiler settings, node or existing environment
changes. Only the affected test root and its195-source dependency closure were
compiled; nine selected methods ran, without an unchanged suite.

## WG02: bound complete ownership verification without dropping NFTs

The existing complete wallet endpoint performs one `ownerOf` check per indexed
NFT, in addition to canonical code/binding/history checks. A legitimate owner
of all1,000 NFTs therefore exceeds the unchanged1,024 logical-RPC-call budget.
The new focused reproduction confirms that exact limit failure.

The additive endpoint is:

```text
GET /v1/wallets/{address}/nfts/{block}/{offset}
```

It verifies at most16 returned IDs against one confirmed canonical block, exact
deployment/history and ERC721 count. It exposes the total count, verified page
count, offset/next offset, full-inventory digest and exact provenance. `complete`
is true only when offset0 actually verifies the entire wallet. A final page alone
never proves a multi-page wallet. Consumers must collect all contiguous pages
under the same wallet/chain/NFT/block/configuration/digest and validate the total.

The legacy schema2 complete endpoint remains complete-or-failed; no silent
partial response, indexer trust shortcut, batch-count trick or limit increase is
introduced. Explicit service/HTTP/worker dispatch carries the new page action.

**Thirteen distinct new methods pass.** They verify all63 pages/1,000 full-width
IDs exactly once, each within the asserted1,024-call and1MiB limits; final page
contains8 IDs and remains incomplete by itself. Other cases cover empty/small
wallets, forged count/ownership, missing history, currency faults, reorg/depth
loss, invalid cursors, changed digest, owned loopback HTTP and worker forwarding.
Four additional controlled first-page states use16/64 ERC20 currencies plus ETH,
with healthy or all metadata reads failing.

[Service evidence](service/VERIFICATION.json) retains the two original runs,
exact13 method IDs, source pins and limits. Its terminal summaries are explicitly
transcriptions, not independently retained raw logs. Numeric maxima were not
captured; only the passing upper-bound assertions are reported. Final source
format cleanup is normalized-byte equivalent to the tested source.

The injected page fixture explicitly uses accounting7/mint1/V9/reporting5 with
synthetic Fresh7 runtimes. It is not complete F6/mint2 deployed-graph acceptance.

Actual provider latency/history completeness, populated financial pages and
website adoption remain unqualified. `service.py` contributes to checkpoint
semantic source identity: retain existing checkpoint/review/database bytes and
explicitly rebuild/review/re-pin before a separately authorized consumer rollout.
No old checkpoint, journal or running configuration is rewritten.

## WG05: remove a stale operating-budget instruction

The current fresh pre-seal diagnostic still required an "unchanged20M"
contribution budget after the operator selected32M. The diagnostic now says
"reviewed configured contribution budget with full20% headroom." One affected
F6 preparation method fails before the correction and passes afterward;
[raw stages](service/preseal-diagnostic/final.json) retain both outcomes.
No actual limit, calldata, readiness flag, permission or economic behavior changes.
The13 wallet methods are not repeated for this independent diagnostic correction.

## Coverage still to qualify

The source/function inventory is complete for its declared pins. The187 scenario
classes are obligations; family membership and nearby test names do not make
each class dynamically passed. Newly composed financial and ownership evidence
is partial evidence for its exact assertions and states.

Remaining work includes cold maximum-populated32M contributions with both LPs,
every reviewed currency/activation-order/batch combination, complete latest-codec
canonical coordinator cutover, all manual emergency-state masks, actual release
constructors, authentic archive/history/provider performance and full normal-loop
key/host recovery. Real markets/feeds/routes, OpenSea/VRF/content, authority and
independent release approval remain original Q01-Q07 work.

Dedicated10/25/100-user capacity benchmarking stays user-deferred. Basic
concurrency/isolation/recovery remains in the scope; a bounded implementation
does not establish a production SLA. Unsupported bridges, replacement token
identities, custody-address exits or public signing are not silently revived.

The Todo, operator/API/coverage guides, findings, feature/roadmap/release records
and repository memory are updated. Financial rights, permissions, gas/fee/work
limits, existing Anvil state, sites/services, signer, checkpoints/journals and the
user-paused heartbeat remain unchanged. [Verification](VERIFICATION.json)
distinguishes the new checks, affected existing checks and retained evidence.
