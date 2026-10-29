# Verification: confirmation2 and manual emergency1

Baseline `2feee92f6bc13b09bae1d43f36bfb7cf6c8faac9` on main. Fresh local candidate, undeployed and
**production NOT APPROVED**. [Review](REVIEW.md) and
[machine summary](verification-summary.json) define this scope. The wider
whole-project audit is unfinished; this is not a whole-suite or independent audit.

## Executed checks

The latest recorded result for **131 distinct Solidity methods** is
successful across scoped attempts7/8/9/10/11. This is the union by full suite/method
identity, not addition of repeat runs. Every included run used the identical final
production Solidity source hashes; no source drift occurred during a run. Four
test-only fingerprint fixtures changed between7 and8; the scale harness gained
its real Vault binding and migrationBudget getter between9 and11. Scope
details/hashes are retained in JSON.

| Solidity suite | Distinct methods |
| --- | --- |
| `test/CompoundInterval.t.sol:CompoundIntervalTest` | 6 |
| `test/HolderCollectiveExit.t.sol:HolderCollectiveExitTest` | 13 |
| `test/IntegratedEconomicConservation.t.sol:IntegratedEconomicConservationTest` | 3 |
| `test/KeeperRangePolicy.t.sol:KeeperRangePolicyTest` | 10 |
| `test/LPExecutionRouting.t.sol:LPExecutionRoutingTest` | 19 |
| `test/MigrationBudgetAdversarial.t.sol:MigrationBudgetAdversarialTest` | 13 |
| `test/MigrationExecutionBudget.t.sol:MigrationBudgetScaleTest` | 2 |
| `test/MigrationExecutionBudget.t.sol:MigrationExecutionBudgetTest` | 3 |
| `test/NativeVaultFlows.t.sol:NativeVaultFlowsTest` | 21 |
| `test/RebalanceBudget.t.sol:RebalanceBudgetTest` | 7 |
| `test/RebalanceConfirmation.t.sol:RebalanceConfirmationTest` | 34 |

The scope covers physical-only/reference-only/opposite-side rejection, actual
same-side execution-time checks, policy change/restore invalidation, width-policy
mutual exclusion/count integrity, normal cooldown/compound/loss behavior and
manual emergency authorization. Emergency cases exercise actual optional swap/
deployment, unavailable prices with explicit bypass, retained financial checks,
parked recovery, raw-minimum rollback, stale custody, bad mask/ticks/deadline,
canonical/terminal rejection, context cleanup and retained-policy fingerprints.
Real local v4 composition tests also cover callback-cleared evidence rolling back
the full rebalance (with positive control), failed idle compound cleanup and
funded fees/royalties/transfer rights through growth/compound/rebalance.

Backend/keeper/API/preflight: **162 defined, deduplicated methods
pass**, no skips or source drift. Tests include coherent disagreement versus
malformed reads, historical1 versus explicit2, durable clear even if market
recovers before inclusion, policy/runtime/health binding and physical tick
consistency. The callable-reference tooling has31 separate passes. These are
separate scopes, not a single added global assurance count. Offline/controlled
RPC fixtures do not qualify real providers or operating timing.

Normal Solidity0.8.26/Cancun/via-IR optimizer settings remain unchanged. Build11
compiles a closed78-source inventory with exact raw source/dependency/build/
compiler hashes and no during-build drift. **All39 normal runtime/initcode gates
pass**; no limit was raised. Fresh generated callable reference covers33 concrete
contracts and696 functions with no function-purpose/access/top-level-input gaps.
Its122 previously unannotated output positions remain reported rather than
invented; new functions have specific outputs/tuple explanations.

| Object | Runtime bytes | Runtime headroom | Initcode + argument floor | Initcode headroom |
| --- | --- | --- | --- | --- |
| ZZZLiquidityManager | 23111 | 1465 | 49115 | 37 |
| ZZZMigration | 24375 | 201 | 29298 | 19854 |
| ZZZMigrationBudget | 22238 | 2338 | 23345 | 25807 |
| ZZZStrategy | 24414 | 162 | 42024 | 7128 |
| ZZZVault | 24517 | 59 | 49047 | 105 |

Initcode uses actual static argument sizes or a conservative minimum for dynamic
arguments. Exact production dynamic constructor arguments still need approval;
the NFT metadata URI is not selected/qualified by a minimum-size check. The
Manager's37-byte initcode margin and Vault's59-byte runtime margin remain tight.
Existing scoped routing gas assertions pass, but neither size compliance nor
fixture gas proves complete cold/maximal or Robinhood execution cost. Added
helper calls incur overhead; no blanket gas-efficiency improvement is claimed.

## Failures retained and corrected

- Early compiler attempts exceeded normal limits. Exact v4/valuation/confirmation
  math was shared through already immutable helpers instead of raising gates.
  Build10 still exceeded Vault initcode; factoring raw evidence hashing into the
  fixed confirmation helper resolved it. Build11 is the final normal build.
- Early NativeLiquidity swaps failed before reaching the intended path because
  its Registry double lacked the already required configurationRevision getter.
  The explicit fixture revision fixed that; the3 failing swaps then passed with
  their actual swap calls. Their earlier source scope is preserved separately,
  not added to this final union.
- An early range-policy test placed expectRevert before a successful helper
  getter. Resolve the getter first so the expectation covers the real setter.
  The corrected mutual-exclusion test passes without weakening production code.
- First budget regressions after factoring evidence hashing failed on missing
  observationFingerprint in synthetic policies. Fixtures now hash exactly the
  same fixed controls and raw empty record, rather than bypassing the new read.
  All affected budget/compound/exit cases then passed.
- The mixed-decimal scale harness omitted its Vault module identity and the
  parent's migrationBudget getter. Binding its actual parent to Access and
  exposing that real parent getter, as required by Pricing, restores both
  the exact3% acceptance and one-base-unit-past-floor rejection. The production
  authorization was retained. A separate test-only manifest isolates the retained
  sample fingerprint; it is not represented as a real emergency deployment.

Raw traces, initial design/drafts, compiler failures and all attempts remain at
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/whole-project-completion-20261029`. Original unrelated dirty files remain byte-identical and
unpublished. Historical report bytes were not relabelled or replaced.

## Limits and operating status

No public transaction, deployment, sealing, signer extension, installed service,
existing Anvil state/journal, website build or server changed. Public signing
stays disabled; old deployments remain their old profiles. The website source
head remains e5bb2163e0af0019bd917f65711c1f669b2d6224 and tracked-clean.

Normal reference corroboration uses configured Oracle dual sources, not a newly
qualified deeper-market TWAP. Actual independence, source window/freshness,
post-withdraw depth/fees, attacker/protocol profit, public ordering, strict900/300/
240 timing, cold/maximal gas and independent audit/remediation remain open.
Observation during cooldown remains proposed. A paused governance emergency
with financial guards disabled can lose nearly all principal; exact accounting,
typed approved pools and manual invocation do not remove that accepted trust.
See [operator procedure](../../docs/EMERGENCY_REBALANCE.md) and
[sole Todo](../../TODO.md#task-manual-emergency-rebalance).
