# Execution and evidence record

November4,2026; baseline main `44f5fa7db5d8472e4cd8f3e1af13a4b9dc27fa09`.
[Review](REVIEW.md), [coverage](COVERAGE.md), [method/stage ledger](campaigns.json),
[exact unchanged production/dependency/build pins](preservation.json),
[challenged execution plan](PLAN.md). Production **NOT APPROVED**.

## Actual local-v4 execution

| Retained stage | Selected methods | Actual result |
| --- | --- | --- |
| campaign-initial |6new methods |1pass,5failures. The independent NAV model rounded separately priced LP/idle/compound subtotals; actual NFT marking correctly prices summed token inventory. Each observed discrepancy was one raw USD unit. Correct the model, not production. |
| campaign-inventory-corrected |7new methods |5pass,2failures in the repeated-cohort paths. The model pooled individual/collective fractional entitlements before rounding, inventing one raw spendable unit. Production correctly keeps those fractions separate. |
| campaign-ledgers-corrected |7new methods plus one affected existing six-day control |All8pass,0failures,0skips; exact source pins unchanged during execution. The two cohort paths now also execute the real typed Compounder. |

There are **8distinct selected successful methods**, including7new scenario
methods and1existing control, not21tests from adding overlapping attempts.
The control is justified by the shared harvest helper's test-only return of its
captured logs; its receipt and allocation assertions remain intact. All7new
methods ran again at the final model source. No unchanged broad suite rerun.

Final new methods in [OptionalPortfolioCore](../../test/OptionalPortfolioCore.t.sol):

- `testMarketCampaignBullBearCohortsThroughRepeatedOneTwoOneModes`
- `testMarketCampaignBearBullCohortsThroughRepeatedOneTwoOneModes`
- `testMarketCampaignMixedResidualPendingMergeTransferAndNewEntries`
- `testMarketCampaignBothOutsideInputsStayInMainWithoutRecentering`
- `testMarketCampaignOrdinarySamplesSurviveEntryAndGrowWithoutClockReset`
- `testMarketCampaignFeedDisagreementRejectsEntryThenRecoversWithoutLostRights`
- `testMarketCampaignRoyaltyEntitlementsStaySeparateThroughLPModeChangesAndExit`

The existing control is
`testLongHorizonSixDayModesEntryGrowthHarvestCompoundAndClaims`.
Method names are canonical in the stage ledger, including their suite IDs.

Forge1.4.4, Solidity0.8.26/Cancun, existing viaIR/optimizer1/Yulfalse profile.
Each stage uses exclusive external compiler output/cache paths and records
command, source hashes, raw JSON output, stderr, exit status and elapsed time.
The explicit1000000-byte fixture allowance applies only to test deployment;
normal production EIP170/EIP3860 gates are separately preserved.

Reproduce the selected final methods with the existing toolchain, repository
root and separate output/cache directories:

```text
forge test --match-contract OptionalPortfolioCoreTest --match-test "^(testMarketCampaign|testLongHorizonSixDay)" --json
```

Do not run that command against or reset an existing Anvil deployment. Forge
uses its isolated test EVM. Keep the normal build profile unchanged; the exact
external command and fixture-only environment are recorded in the archive.

### Scope of the model

Real local PoolManager/PositionManager/StateView and production PoPL contracts
execute controlled swaps, fee-generating donations, entry, harvest, compound,
replacement, transfers, claims and terminal payout. Access/bootstrap/registry
admission, correlated USD feeds, VRF, Permit2 and mintable test ZZZ remain explicit
substitutes. The test controller can bind Compounder before user state; production
has no unseal/rebind operation. Alice/Bob use initial disposable fixture funding;
new mints do not refill their wallets during the journeys.

The model reconstructs reward entitlement from actual funded-credit events and
pre-operation shares/membership; it does not use production reward indices or
fractions. Contribution checks also reconcile the measured marginal-LP event and
actual post-operation inventory/share supply. This is not an independently
implemented Uniswap AMM, live oracle qualification, organic-volume proof, market
profit/IL forecast, MEV/profitability test or formal proof.

## Backend and worker execution

| Retained stage | Actual result |
| --- | --- |
| projection-initial |4new Projection methods pass. |
| backend-corrected |7methods run;5pass,2fail because the strict synthetic RPC fixture rejected the companion reader's preliminary `eth_getCode(...,"latest")`. No production safety defect was inferred from this fixture omission. |
| backend-runtime-corrected |All7new methods pass,0failures/errors/skips; source unchanged during execution. The fixture now handles only that exact budget-runtime preliminary read; later physical reads remain hash-pinned. |

**7distinct new Python methods**, not18from adding repeated stages. They execute
the actual Projection/worker/read-review code with synthetic canonical responses,
temporary journals, restart and explicit no-signer assertions. No real service,
database, wallet, credentials, public RPC or network transaction is used.
[Projection cases](../../tests_python/test_market_lifecycle_projection.py),
[worker cases](../../tests_python/test_market_lifecycle_keeper.py).

## Production evidence reused and preservation

All52production Solidity sources,31dependencies and4build inputs match the
current [authority normal-gate record](../authority-audit-20261103/production-size-gates.json)
byte-for-byte. Its43normal gates remain valid at those pins. Current runtime
margins remain Migration39/Vault635/Budget237/Balancer360bytes. No optimization,
ABI/profile/storage/economic/authority change, fresh analyzer, full suite or
published-CI result is claimed. Existing static/callback/maximum-holder/canonical
records retain their original source and test scopes; see coverage rather than
adding historical counts to this campaign.

The four unrelated dirty files match the starting raw hashes and remain excluded.
Original maintained documents were archived before edits. External originals,
full compiler outputs, raw failed/successful logs and exact test-source stages
remain under the local evidence root's `market-lifecycle-20261104/`. Public stage
records contain their hashes; no private credential was accessed or included.

The source-bound function reference, sole Todo, document links, staged/committed
Python publication closure and preservation are checked separately in final
consistency/publication evidence. Source publication is not deployment, sealing,
service/site/Anvil/journal rollout, public signing or production approval.

## Reference material used

The [Uniswap v4 PositionManager guide](https://developers.uniswap.org/docs/protocols/v4/guides/position-manager)
was checked against the installed core/periphery implementation for liquidity
actions and settlement. [Solidity0.8.26 security considerations](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
informed cross-contract callback and bounded-work review. An attempted Foundry
invariant-document fetch failed because of its Markdown content type; it is not
claimed as consulted guidance. These references do not independently audit PoPL
or qualify deployed dependencies.
