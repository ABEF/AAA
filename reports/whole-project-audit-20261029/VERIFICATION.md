# Verification and source preservation

Reviewed2026-10-29 Paris. Baseline contract main781fcc9, websitee5bb216.
[Machine summary](verification-summary.json), [raw artifact hashes](external-artifacts-sha256.json)
and [coverage](COVERAGE.md) distinguish actual execution from source tracing,
inventory, exact reuse and external qualification. Production **NOT APPROVED**.

## Fresh affected evidence

| Scope | Distinct result | Evidence / limits |
| --- | --- | --- |
| Stored history corruption |7new Python methods pass | Actual temporary SQLite, writer and reader with deterministic RPC. Duplicate cursor/raw keys, nonfinite JSON, malformed/unknown data, missing removed marker, parser failure and valid claims/owner recovery. No network/signing. |
| Ownership inventory currency isolation |7new Python methods pass | Accounting3/4, optional runtime/decimals/RPC outage, required core/allowlist/owner/depth/WorkLimit and verified empty ownership. Actual fixture/SQL path, not live token/provider qualification. |
| Keeper/runner/CI improvements |23new Python methods pass |13runner/CLI/static-CI,3metadata restart and7four-minute/journal/health methods. No prior full keeper bodies executed by inventory checks. |
| Directly affected existing operations |17Python methods pass | Confirmation/manual/cooldown/readiness/jitter, poll/health, pending, metadata/harvest/buyback fairness. Only changed schedule fixtures updated; no safeguard weakened. |
| Existing history/API/lineage/earnings |21Python methods pass | Payouts, current-owner transfers, valid raw history, anchored snapshots, complete totals, fractional/claim/conversion/epoch reconciliation. One method belongs to the original local-only dirty history draft and is not staged; fixture/common existing definitions are unchanged. |
| Current canonical composition |5EVM methods pass | Exact cutoff-before/after abort, multi-hop late receipts, native whole-state/backing transfer and native partial-funded abort. Real current economic/canonical modules, mocked venue/prices/VRF/admission. No market/gas/provider acceptance. |

**75distinct Python methods:75pass,0skip**, comprising37new and38affected existing.
Overlapping attempts/subcases are not added again. Final40method operations run
(23new+17existing) blocks network and subprocess. Stored-history7+21runs also
block both; frontend7 uses inert byte-RPC and real temporary SQLite. Metadata
process loss is injected and the worker reconstructed from saved state; it is
not an actual Unix watchdog/host-crash rehearsal.

Separate from method counts:12Node metadata-expression scenarios pass in a temp
copy, preserving other traits/paths. The website generator patch passes read-only
applicability check but remains unapplied; no rendering/generated assets/build/
browser/marketplace test ran. The AST-only applicability compile covers77exact
inputs; it executes no Solidity bytecode. New keeper inventory selects41modules/
623methods and reports **zero methods executed**. No623-pass claim is made.

## Exact EVM selection and nonvacuity

Forge1.4.4 commit05794498 and local solc0.8.26/Cancun/viaIR/runs1/Yul-off used
isolated external output/cache/home, offline/noFFI/noRPC/no wallet/broadcast.
Final current-source composition finished in258seconds including compilation.
An independent check requires exactly these five signatures, no extras/missing
or duplicate methods, every statusSuccess and zero source drift:

```text
CanonicalHandoffTest.testAbortBeforeSettlementPreservesLPAndPendingRoyaltyReceipts()
CanonicalHandoffTest.testAbortAfterRoyaltySettlementReopensWithoutDoubleCrediting()
CanonicalHandoffTest.testLegacyRoyaltyReceiptsQueuedWhileSuccessorFrozenRemainBackedAcrossNextHandoff()
NativeCanonicalIntegrationTest.testNativeWholeHandoffCarriesPrincipalIndicesRoyaltiesAndFeeDonationQuarantine()
NativeCanonicalIntegrationTest.testNativePartialFundingAbortRequiresAndRestoresExactBacking()
```

The first attempt exited0 but selected zero tests because its anchored filter
omitted signature parentheses. Exact-selection validation rejected it. Raw input/
stdout/stderr/check records remain under `contracts/attempt1`; only the corrected
same-five retry counts. No source/fixture/runtime/gas/size gate was relaxed.

Negative controls separately reproduce the optional-currency ownership failure,
permissive stored evidence, metadata restart starvation, omitted keeper selection,
historical fork wiring and old300 schedule failing the new240 requirement.
Initial corrected fixture attempts remain, including an unreliable hardcoded JSON
nesting-depth expectation replaced with an explicit parser-failure injection.
No failed or zero-selected attempt is reported as successful behavior evidence.

## Exact unchanged reuse

Revalidated all142pins for the prior217affected Solidity methods and all46source,
31dependency and4build-input pins for39normal object-size gates. No mismatch.
Those receipts remain in `practical-improvements-20261028`; they were not rerun.
The217methods do not contain either canonical suite above. Reuse is not a fresh
full-release test/build or coverage for later changed Python/website consumers.
Tool bytes match the captured executable; default gates and exact source profiles
are unchanged. Maximal target gas/initcode arguments/constructor URIs still need
real release qualification. See [compiler applicability limits](COMPILER_DEPENDENCIES.md).

## Preservation, synchronization and publication

The four original dirty tracked files are byte-identical to the archived baseline:
`reports/source-checks.json`, `scripts/run-fork-checks.py`,
`tests_python/test_fork_runner.py`, `tests_python/test_frontend_history.py`.
They remain excluded from publication. All tracked website hashes match baseline;
source/build/dist/signer and both public sites remain unchanged. Existing Anvil/
NFT/LP/balance/journals/services and paused monitoring were not operated.

The new final brief's hash is preserved; subsequent user-approved240cadence and
requested future cooldown-observation task are documented in prompt review and
current guides. Todo generation/check, source-bound callable reference, changed
Python/JSON syntax, document links/anchors/whitespace and preservation checks run
separately from test counts. Exact final source/publication hashes are recorded
in the manifest and publication evidence; verify actual GitHub head before saying
pushed. Published CI, actual providers/services and production approval are not
inferred from local checks or source publication.
