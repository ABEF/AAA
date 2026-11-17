# Selected handoff fixture executions

Four distinct methods run successfully with the changed shared execution-math fixtures. Only the explicitly named selections run; no full suite, fork, browser, signing or public transaction occurs. Source files and limits are not edited by this driver.

| Contract | Method | Result | Whole test gas |
| --- | --- | --- | --- |
| SeaDropFullHandoffTest | `testBoundSeaDropWholeV10CommitCarriesActualLPAndRoyaltyClaimsToCurrentOwner` | Success | 7,916,734 |
| SeaDropFullHandoffTest | `testBoundSeaDropFundedV10AbortReturnsBackingAndPreservesOriginalMintBooks` | Success | 10,604,498 |
| CanonicalHandoffTest | `testCompleteHandoffPreservesOwnersSharesTraitsAndBothRewardLedgers` | Success | 820,887,326 |
| CanonicalHandoffTest | `testPartialFundingCannotActivateAndFundingCannotReplay` | Success | 816,988,562 |

These whole-harness gas numbers include setup and many simulated transaction/operation steps. They are not single-transaction gas-profile or deployment qualification. SeaDrop is the verified embedded runtime with explicitly initialized fixture state; venue, pricing, token and randomness dependencies remain controlled fixtures.

Each corrected run discovers exactly its two expected methods, uses pinned Forge1.4.4/solc0.8.26 with offline/default settings, and runs in separate owned output/cache directories. The first attempts used a name-only end anchor that selected zero methods. They are retained as nonpasses, even though Forge returned zero; the selector is corrected only in the external runner. No method executed in those empty attempts.

The raw corrected manifests also conservatively mark the whole test-tree snapshot unstable: four unrelated family files changed concurrently. No global-stability claim replaces those records. A separate exact compiled-target closure proves each selected host's114 metadata source dependencies: all64 selected repository src/test files retain their before/after hashes, all50 other dependency files match the actual compiler-recorded Keccak hashes (only explicit LF normalization allowed), and none of the four concurrently edited files belongs to either selected closure. Production source hashes continue to match the accepted final normal build. That establishes the narrower selected-execution pass without rerunning unaffected tests.

The four unrelated files are `GovernedExecutionLoss.t.sol`, `KeeperCompletion.t.sol`, `MigrationBudgetAdversarial.t.sol` and `MigrationExecutionBudget.t.sol`. Their edits and results belong to the other family's evidence.

- [Four-method summary](HANDOFF_EXECUTION_RESULT.json)
- [SeaDrop actual results](HANDOFF_SEADROP_FORGE.json) and [exact source closure](HANDOFF_SEADROP_SOURCE_CLOSURE.json)
- [Canonical actual results](HANDOFF_CANONICAL_V10_FORGE.json) and [exact source closure](HANDOFF_CANONICAL_V10_SOURCE_CLOSURE.json)

Raw attempts, global source drift, artifact/runtime hashes, dependency hashes, tool pins and initial empty selections remain separately preserved. This scoped controlled evidence does not approve production markets, providers, real OpenSea onboarding, fees, maximum state, operators, deployment or independent audit.
