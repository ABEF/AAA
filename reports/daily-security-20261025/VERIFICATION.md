# October25 verification: exact scope and limits

This internal audit covers the [recorded Paris-day commits](DAY_SCOPE.json) through
`1e00b49` and the source changes in this report. It does not certify every possible
execution, external dependency or production deployment. No public transaction,
existing Anvil state, service, website build/server, wallet policy or monitor was
changed. Production remains **NOT APPROVED**.

## What was executed

| Check | Result and evidence boundary |
| --- | --- |
| Solidity economic and authorization selection | **28 distinct behaviors pass**, across the three recorded fixture scopes below; not one fresh full-suite run. [Combined manifest](solidity/combined-selected-summary.json). |
| Affected indexer Python methods | **35/35 pass once**:8 new provenance methods and27 existing Indexer methods, isolated SQLite/mock chain. [Final record](indexer-log-poison-after.json); [before-fix failures](indexer-log-poison-before.json). No real service/database repair. |
| Final whole-repository Solidity typecheck | **124 src/test/script inputs**, ABI/AST only, zero compiler errors after both fixture repairs. [Final bindings](solidity/typecheck-summary.json); initial bindings are retained separately. |
| Normal production object limits | **36 gates pass** under unchanged0.8.26/Cancun/via-IR optimizer settings;41 production source hashes match final inputs. [Sizes/settings](solidity/production-size-gates.json). No optimizer, EVM or code-size waiver. |
| ABI/storage comparison |104 project object ABIs unchanged; only Buyback's old setter/event and an unused interface are removed. Buyback's token becomes immutable; its storage layout changes. Access/Registry/Membership/Migration label-slot-offset layouts match the preceding checkpoint. [Comparison](abi-storage-comparison.json). Fresh deployment only. |
| Necessity review |31 concrete contracts mapped to purpose/callers. Conservative AST screening:386 roots,650 reachable function/modifier nodes, no project private/internal candidate orphan. [Inventory](NECESSITY.md), [scan](internal-reachability.json). This is not proof of universal minimality or external-dispatch completeness. |

The eight new Python methods reproduced failures against the original indexer.
Subcase diagnostics are retained as failures/errors, not counted as extra tests.
Final checks preserve prior valid blocks/cursor on rejected new batches. A
separately proved bounded reorganization remains its own prior operation.

## Solidity selection and test-fixture repairs

The pinned [AST selector wrapper](solidity/run-selected.py) retains the exact
selected test bodies/helpers and compiles all production source files under an
isolated external profile. Unselected test methods are removed by declared AST
spans; production source is not transformed. The compiler/selection/source
manifest is [retained](solidity/focused-transformation.json). No real provider,
signer, service or persistent local blockchain is used by these Forge VM tests.

1. The initial execution passed **20** behaviors:5 native-source admission,
   3 fixed-ZZZ binding,4 Buyback operating-limit,3 Buyback execution,4 custody
   exit/return and1 captured custody-floor case. Foundry rejected a new dust
   method name beginning with reserved `testFail`, so the8 dust methods did not
   run. [Initial output](solidity/focused-results.json), [summary](solidity/focused-summary.json).
2. A single test-name replacement enabled the8 dust cases; **5 passed**. Three
   negative controls used `expectRevert` on a same-depth mocked call, which
   Foundry could not intercept. The trace confirms the injected venue error was
   returned. [Name repair](solidity/test-name-repair.json), [run](solidity/dust-repair-results.json),
   [trace](solidity/dust-negative-control-trace.log). A preceding anchored trace
   pattern matched no tests; that diagnostic is retained and not counted.
3. Only that negative-control assertion changed to a low-level `staticcall`
   checking exact failure bytes. Economic assertions and all41 production
   sources remained unchanged. **Only the3 failed methods were rerun**, all
   passing. [Control repair](solidity/control-repair.json), [run](solidity/control-repair-results.json).
   Previously passing methods were not repeated or added again.

The8 dust cases cover incumbent-only funded payout and zero-dust entry despite
an old venue outage, current-venue failure, nonpayable old dust rollback, failed
entry rollback, authorized settlement and exclusion of foreign-custody buckets.
The native admission tests prove the new identity guard precedes venue checks;
they **do not demonstrate successful admission against real Robinhood contracts**.
The fixed-ZZZ tests use real Access/Registry/Assets/Migration/Buyback with explicit
substitutes for unused roles, tokens and prices; matching bootstrap permits seal,
unbound/mismatched Buyback prevents it, and the removed setter rejects before/after
seal. Custody regressions verify actual financial balances and no automatic raw
fallback, not merely selector presence.

## Size and release implications

- Vault runtime23,889/24,576:687 bytes remain. Registry runtime10,131. Buyback
  runtime7,367. These are compiled current objects, not deployment gas estimates.
- Access creation48,835 plus minimal288-byte nonempty role arguments is49,123
  of49,152: **29-byte headroom**. One extra32-byte array item exceeds the limit
  by3 bytes. Actual release authority arrays are **not qualified**. A multisig
  can be one array address; its internal owner list is not duplicated there.
- Buyback's immutable token changes its fresh-deployment layout. No existing
  deployment/storage/journal is patched or reinterpreted. The catalog now covers
  **31 contracts/643 functions/31 constructors/14 receive hooks**, with exact
  compiled types/outputs and purpose/caller/input notes.

The full compiler input/output and disposable Forge profile remain in the
external local evidence directory; their hashes and raw source bindings are
recorded here. Reproduction uses the retained normal-build/selection scripts and
pinned dependencies/toolchain. The final typecheck binds the repaired test bytes;
the unchanged production build and earlier AST reachability scan are reused with
their exact original source/output hashes, not represented as new runs.

## Reused and unverified work

Prior dual-price, caller-policy, native accounting, canonical handoff, royalty
isolation, range/idle, metadata, gas and broader keeper/backend evidence keeps
its original report/source scope. No unchanged full regression, fork, static
analyzer, maximal collection gas campaign, frontend browser suite, operating
rehearsal or independent audit was rerun merely to increase counts.

Actual feeds/proxy independence, cheaper conversion routes, VRF, authorities,
OpenSea primary mint, current native wallet/services, strategy economics/maximal
gas, operating recovery and independent audit/remediation remain release gates.
No new unprivileged theft/dilution/double-claim path was confirmed in inspected
code; that is not an exploit-absence guarantee. Immediate governance and trusted
external custody remain explicitly accepted trust boundaries.

Documentation/Todo/function-reference checks and exact implementation/publication
hashes are recorded separately. A source commit, push and deployment are distinct
facts; consult the publication receipt before assuming publication occurred.
