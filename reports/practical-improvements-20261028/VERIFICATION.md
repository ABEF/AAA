# Scoped verification - practical improvements

Reviewed2026-10-28. [Review](REVIEW.md) explains behavior, decisions and limits.
**Production NOT APPROVED.** Source publication is not deployment/rollout.

## Evidence boundaries

External raw evidence is preserved under
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/practical-improvements-20261028/`.
It includes the863-file baseline, compiler inputs/outputs, original failures,
test selections/results, source pins and delegated review records. Only sanitized
summaries/hashes belong in this report. No key, funded wallet, live provider or
operating-service transaction was used.

Current compiler evidence passes39normal object gates at pinned
Solidity0.8.26/Cancun/viaIR/optimizer-runs1/Yul-off. EIP-170/EIP-3860 limits were
not relaxed. Manager runtime23765/margin811 and creation48548+160arguments leave
444initcode bytes. Vault runtime24064/margin512, creation46245+96arguments;
Strategy runtime24004/margin572; NFT runtime24400/margin176 and dynamic URI
constructor arguments still need exact qualification. These are fresh-source
sizes, not upgrades to preserved deployments.

The generated callable reference covers33concrete contracts,665functions,
33constructors and13receivers, with zero purpose/caller/payable/input explanation
gaps. Existing122output positions without dedicated annotations retain their
prior documented semantics; this is not a claim of exhaustive nested-tuple prose.

## Affected checks

Final exact method/source summaries are recorded in the accompanying machine
evidence. Distinct methods are counted once across retries/overlapping selections.

- Keeper:160-method affected selection passed159, with one explicit missing-cast
  skip. The later active-Vault binding correction has two affected passes,
  including one new method and one repeated happy path. Together161distinct
  keeper methods,160pass/1skip. Both runs retain exact loaded-source pins.
- API:63distinct affected methods pass across the original selection and13-method
  fixture correction. The confirmed snapshot is timestamp990, not wallclock1000;
  correcting that fixture did not weaken production readiness validation.
- Schema6 preflight:36distinct new synthetic methods pass. Two overlapping
  scaffold/dispatch methods were rechecked after intended gap300/diagnostic update.
  Fifteen historical CLI methods retain earlier unchanged-code scope, excluded
  from this fresh count. The checked-in actual inventory remains blocked.
- Final Solidity campaign:217distinct affected methods pass, zero failures/skips
  or source drift. This includes28timer methods, actual-v4 callback rollback with
  a successful identical-state positive control, and affected contribution,
  rebalance/compound/move/parking/exit/accounting/cap fixtures. Old mock policies
  now explicitly provide test-only stable confirmation seams; they do not pretend
  to prove the real timer. Gates and production guards were not relaxed.
  The composed v4 cases install real PoolManager/PositionManager/StateView code
  inside Forge, with explicit test admission, sources, VRF and Permit2 substitutes.
  They are not live-market, real-provider or target-chain qualification.
- Deeper buffer audit:39keeper methods pass (18new included once),21reader/
  admission methods pass (7new included once), and31final reader/health methods
  pass as overlapping current-source verification. Three tests fail against
  archived pre-fix maintenance handlers in memory, proving they detect the
  unrelated-error reset regressions; those are negative controls, not extra passes.

Across source-scoped Python selections the distinct union is272methods:
271passes/one explicit missing-cast skip. This is not one whole-suite execution.
Exact method selections, current pins and original failure records are retained
in [machine evidence](verification-summary.json). Normal gate details are in
[size evidence](normal-size-gates.json), with
[external artifact hashes](external-artifacts-sha256.json).

Python tests disable real network/subprocess signing; all RPC observations are
synthetic. Thirteen API/keeper methods overlap and must not be counted twice.
These are source/fixture checks, not real services or target-chain capacity.

## Preserved failures and corrections

1. First helper build exceeded Yul stack capacity from a flat identity encoding.
   Nested physical/source/control hashes preserve the original fields. A later
   full-operation stable control fingerprint strengthens callback consistency.
2. Preflight attempts exposed omitted typed getter classification and decimal-text
   slot0 handling. Correct typed observation paths now reconcile before acceptance.
3. Keeper tests exposed an address-alias dispatch collision in an old synthetic
   fixture. Correct fixture dispatch retained all production binding checks.
4. API fixtures used wall-clock time where the service correctly used the confirmed
   block timestamp. Correct fixture expectations; contradictory readiness still fails.
5. Foundry rejected a new `testFailed...` method name as removed `testFail*` syntax.
   Rename only; original diagnostic retained. The timer fixture then exposed a
   missing `spot(bytes32)` implementation required by real Strategy price guards;
   add exact TickMath-derived fixture spot, without bypassing source validation.
6. A new clock-retreat regression initially failed: a retreated scheduling clock
   could hit the hard-cooldown shortcut before invalidation. Check the clock
   before that shortcut; retain the original34-method failure receipt.

The additional source audit fixes post-exit orientation invalidation, captures
raw evidence across maintenance, narrows unrelated reset boundaries, suppresses
repeated paid clears, binds jitter to the actual window, invalidates after exact
failed related receipts, rejects incompatible main polling and strengthens
lifecycle/typed reader consistency. Source ABI and economic rights remain as
described in the review. A cold-operation measurement patch was prepared externally
but not applied/executed; maximal full-operation/target-chain gas qualification
remains open and is not claimed by test-method gas totals.

No failed artifact is overwritten or relabelled a pass. Unchanged rewards,
membership, royalties, NFT and custody rights retain source identities; no broad
unrelated suite was rerun for a count increase. Four original dirty tracked files
and pre-existing report bytes are preserved.

## Open qualification

The selected900/300 policy is strict:300-second checks plus receipt latency can
repeatedly restart; configure/review actual timing and gas before operation.
Constructor gap0 remains stopped ordinary readiness until explicit governance
configuration. Samples can miss moves/faults/pause cycles between them and reveal
pending maintenance. No continuous-price, MEV or attacker-profit guarantee.
The trigger remains actual physical range exit with independent-price agreement
checks; an additional requirement that the independent reference itself lie
outside the LP is not silently introduced as a bug fix.

Actual sources/routes/provider identity,17helper addresses/runtimes, VRF,
authorities, unsupported OpenSea primary mint, frozen-release review, maximal
venue/depth/network costs, Linux service/monitoring recovery and independent
audit/remediation remain required. The keeper's2.5Mexample gas ceiling is unchanged,
not a qualified operating limit. No installed service, Anvil state/journal,
website, signer or public deployment changed.
