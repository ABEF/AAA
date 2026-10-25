# Day-change audit verification

This records actual fresh execution, controlled comparison and exact reuse
separately. It is not a fresh full regression, current Slither pass, independent
audit, real service qualification or authorization to deploy. Source scope is
initial main55011c0 / reference35007db, with the owned backend/tool/test changes
in the final publication manifest. Production Solidity remains byte-identical.

## Build, dependency and comparison scope

- [Ancestry inventory](SCOPE.json):24reachable commits, zero merges, baseline
  3551868; focal parent964e6b6/reference35007db/subsequent receipt55011c0.
  UTC boundaries represent the25-hour Europe/Paris day. Later audit commits
  belong to this task's publication, not the original24-commit count.
- Normal source75-input build:44project +31dependency units, all explicit.
  Exact source/build hashes match the previous successful normal capture.
  **37normal object gates are reused**, not a newly executed37-object build.
  Solidity0.8.26/Cancun/viaIR/optimizer runs1/Yul disabled, seven existing
  remappings. No compiler/dependency/config/limit upgrade or relaxation.
- [Controlled baseline compilation](solidity/controlled-size-comparison.json):
  one new compiler run,60.953s, using all current dependency bytes/settings and
  parent964e6b6 production source. Exactly three source files differ. This
  reproduces the role-event45runtime/175creation increase independently; it
  is not proof of unarchived historical dependency-byte identity.
- [Final AST](solidity/typecheck-summary.json):265closed source units,
  131project/test/script +134dependencies. Only NativeLiquidity.t.sol differs
  from the previous265-input capture. Initial new-test compile failed because
  pinned forge-std1.9.7 lacks fail(string); changing that test call to fail()
  repaired it. The failed input/output/diagnostic are preserved. Final typecheck
  passed in13.656s; no production source change or assertion was removed.
- [Callable evidence import](current-evidence-import.json): actual saved normal
  input/output/size artifacts regenerate snapshot3 with31contracts,
  608functions,31constructors and13receive hooks. No function/input explanation
  gaps;123outputs have no separate positional prose but retain exact types and
  function-purpose meaning. This is unchanged coverage, not608execution tests.

## Fresh EVM execution

| Selection | Actual result | Scope |
| --- | --- | --- |
| Native partial-fill and corrected uint128 bound tests | 2/2pass, no skips | [Native regressions](solidity/NATIVE_REGRESSIONS.md). Actual installed v4 dependencies with stated test seams. Specific intended errors, physical balances/LP/approval rollback. |
| Existing native royalty custody producer test, not in the previous32-case selection | 1/1pass | [Boundary case](solidity/NATIVE_CUSTODY_BOUNDARY.md). Actual RoyaltyRewards/Membership/Vault; mocked LP/price/authority seam, not an actual-v4 scenario. Defers new ETH eligibility, preserves earlier1.5ETH and returns full backing. |
| Isolated Access CREATE, guardian grant, repeat and revoke | 4/4pass | [Gas/event evidence](role-gas.md). Saved controlled old/new bytecodes, separate transaction contexts, exact role/event assertions. Raw gas deltas exclude intrinsic/calldata/L1/refund/target-network costs. |

These are **three project EVM methods plus four measurement checks**, not seven
new whole-protocol lifecycle scenarios. Prior32methods are not rerun or added to
the fresh count. The prior native fixture's19unchanged methods,44other body/helper
definitions and six fault helpers are AST/source-matched in
[reuse bindings](native-reuse-bindings.json). Actual old assertions are mapped in
[the matrix](native-assertion-matrix.md), not inferred from method names.

Gas: CREATE8,446,648→8,458,960(+12,312); grant26,598→28,240,
repeat6,698→8,340, revoke9,498→11,140(each+1,642). The earlier combined
grant/revoke measurement used dirty-slot pricing and is explicitly excluded.
Its passing controls/log-only repeat remain archived, not extra coverage.

## Backend and evidence tooling

- [Custody reporting/replay](native-royalty-custody-verification.json):52distinct
  methods,13new and39existing. Three positive controls fail on the original
  backend. Initial67invocations contained15duplicate imported passes and one
  new SQLite fixture error (missing second-NFT ordinal replies). Only that
  fixture's two API cases reran after repair;50unchanged passes are reused.
  Exact original/final source and fixture hashes, discovery and failures remain
  in the record. Final source is unchanged across those scopes.
- [Evidence checker](evidence-review.md):29distinct methods across two source
  scopes,20existing and nine new. First corrected source28pass; after bounded
  single-read hardening, one additional method plus two affected repeats pass.
  Initial15negative/control probes found11invalid acceptances. Repeated methods
  do not add coverage. CLI failure preserves existing outputs.
- [Strict-format follow-up](format-tests-final.json): two new regression methods
  fail16invalid subcases on the preceding implementation. Exact integer outer
  schemas and valid fixed/ufixed widths/precision now fail closed; valid current
  reference values remain unchanged. The two methods plus one affected existing
  canonical-type control pass. No broad suite repeats. Tool coverage is now
  **31distinct methods across three corrected source scopes**.
- Backend52 plus tool31 yield **83distinct Python methods across explicit source
  scopes**, not one fresh final-source83-test run. The last checker scope has
  three targeted passes. Earlier frozen results retain their exact source hashes.

Current code/signatures for source policies, ledgers, signing and deployed
profiles remain untouched. The fix adds only a bounded typed custodyNonce read
and custody-aware projection/replay. Raw logs are emitter/structure/order checked;
wrong IDs/amounts/spoofs/missing intervals remain failures. Return and conversion
are never new income. Full NFT earnings stays unavailable while backing is external.

## Final validation and unavailable gates

The publication manifest records final owned code/docs/report hashes and checks
reference freshness, generated sole Todo consistency, local Markdown targets,
source/dependency/build bindings and preservation of original dirty bytes. Source
consistency is emitted to this campaign only; the unrelated old report is preserved.
These checks are bookkeeping, not compilation or security proof.

Current stored static-review inventory43names differs from required47:
11additions, seven retired names and28changed retained contents. No fresh Slither
analysis was performed. **Current-source static-review release gate: FAIL.**
Normal compilation/size and selected passes do not override it. No published CI
green result or complete same-day final-source regression is asserted.

No actual provider/fork, feed independence/updater, selected route/market gas,
VRF, OpenSea, service rollout/recovery or independent audit qualification was
performed. All failure/skip/reuse boundaries remain explicit in
[readiness](READINESS.md). No signing key, public transaction, live database,
existing Anvil/NFT/LP/balance/journal, website build/server or monitor changed.
