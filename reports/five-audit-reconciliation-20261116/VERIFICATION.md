# Five-audit follow-through: source-scoped verification

Reviewed16November2026, baseline `28431b3ac63d909c9c04246de1ee68cc16a3ed5e`.
This is internal source/tooling verification and archived evidence reconciliation,
not a full suite, target-chain rehearsal, external audit or deployment approval.

## New checks and retained failures

| Scope | Evidence |
| --- | --- |
| Deployment/build/evidence | 21distinct new methods pass across explicit source stages. Current100-source/39instance/48-size offline plan, old/current identity separation,112expected observations, constructor graph/values, closed RPC/send/impersonation and inert output, output preservation and malformed labels/quantities are covered. |
| Deployment invocation count | 30actual method invocations:23successful stage-specific invocations and7reproduced failing regressions. Three archived-capture positive invocations follow substantive checker changes and count as one unique method. |
| Historical test fixture | All22old method bodies/assertions are AST-identical; only the import is routed through a new explicit authenticated temporary historical checkout. A new fixture control exercises it. No22-method rerun is claimed. |
| Market evidence | 23distinct new methods pass:21at the initial focused source and2new input-container/deflate-corruption cases after the bounded parser correction. Earlier exact phase-schema failures and baseline false admission remain recorded. |
| Actual CLI | Current planner default emits a blocked metadata2 preview, exit2, with readiness/approval false; original local evidence checker replays44receipts/112observations, exit0. Market CLI passes39captured responses with all live-approval outputs false. Overlaps method workflows, not extra features. |
| Separate internal review | Read-only source inspection identified/followed up the constructor graph, RPC/send and inert-output issues. Final pinned review found no remaining concrete blocker in the changed paths. Reviewer ran0tests/builds/RPC; this is not independent external audit. |

The market initial valid-control attempts exposed differences between the actual
primary and discovery log schemas; the implementation was corrected to preserve
their exact phase formats. Malformed-container/deflate handling then received its
own new checks. Earlier21cases are not presented as a fresh full final-source run.

The deployment regressions first demonstrated stale build refusal, duplicate
observation admission, directory consumption, unused mutators, contradictory
constructor intent and unbound send/impersonation fields. Final source stages
add independent graph/value derivation, fixed method/envelope rules, exact
submission equality and bounded uint256 quantities. Inert data return bytes are
computed from trusted accepted ledger parts. Failures are retained; no assertion
was weakened or original capture rewritten.

## Reuse versus fresh execution

- All61Solidity sources are byte-identical to the accepted metadata baseline.
  No new compilation, normal build, static analysis, EVM or browser suite ran.
- Exact accepted metadata compiler inputs/output/48normal gates are reused by
  their trusted hashes. This is not fresh constructor or gas execution.
- All six manual-fix objects plus Vault have exact creation/runtime templates
  and ABIs across the prior manual and current metadata normal families. Scope
  comparison is mechanical, not another C/D transaction.
- Old complete manual/construction receipts retain their old caller/module graph
  and gas scope. Later metadata objects changed; current actual constructor/gas
  acceptance remains open.
- Original114selected historical report files, archives and checkers retain their
  exact hashes. The old market checker is used only in a new adversarial
  reproduction; current semantic validation lives in the new maintained tool.

## Publication and documentation

The [finding index](FINDINGS.json) contains57provenance-bearing assessments,
including10fixed/updated records,12earlier resolutions,1superseded inventory,
10bounded limitations,23external rows and1changed-runtime verification row.
Ten shared release gates avoid duplicating the same external work in a new Todo.

Generated Todo, callable and operator references, changed links/anchors and
new/legacy test inventory are mechanically checked. Exact staged and committed
Python imports are checked against Git blobs, excluding untracked drafts.
The current callable catalog remains40contracts/963functions/40constructors/
13receive hooks/1,016examples; no Solidity/API economic change is introduced.

Evidence bundles record original baseline hashes, before/final source, failure
and pass logs, CLI outputs, reviewer pins, object equivalence, test AST deltas and
preservation checks. They do not contain keys or credentialed endpoint data.

Four protected unrelated dirty files, website source/config/signer bytes,
existing Anvil state/journals/dist and paused heartbeat are preserved. No public
transaction, key use, deployment, seal, provider adoption or service/site rollout.
Live dependencies, actual current-source operation and independent approval stay open.
