# Independent native-fixture assertion review

The archived 24-method fixture contains 73 direct assertions/expectations/helper calls (77 expectations when its two approval-helper calls are expanded). Each is extracted verbatim with a source line and reviewed correspondence in [the assertion matrix](native-assertion-matrix.json).

The first replacement had 20 methods. Current native tests add one actual-Core exact-input sensitivity case and strengthen the existing uint128-bound case. Production guards are unchanged. Test counts alone do not establish preserved coverage.

| Previous test | Current correspondence | Verdict |
| --- | --- | --- |
| `testNativeMintSpendsOnlyExactDebtAndPreservesPrefunds` | `testNativeMintSpendsOnlyExactDebtAndPreservesPrefunds` | Preserved |
| `testNativeIncreaseReusesPositionAndClearsApprovals` | `testNativeIncreaseReusesPositionAndClearsApprovals` | Preserved |
| `testNativeCollectWrapsOnlyActualCreditsIncludingDonationFees` | `testNativeCollectReturnsOnlyActualCoreFeesIncludingDonations`, `testNativeCollectAndDisabledClosePayETHWithFailedWrapper` | Intentionally changed denomination |
| `testNativeCloseReturnsWrappedPrincipalWithoutExposingNativeToVault` | `testNativeCloseReturnsActualPrincipalInETHWithoutWrapping` | Intentionally changed denomination |
| `testNativeInputSwapResetsDirtySyncAndUsesNetDelta` | `testNativeInputSwapResetsActualCoreDirtySyncAndUsesNetDelta` | Preserved with actual venue pricing |
| `testNativeOutputSwapWrapsNetDeltaAndPreservesForcedETH` | `testNativeOutputSwapPaysETHAndPreservesForcedPrefunds` | Intentionally changed denomination |
| `testNativePartialInputRejectedAtomically` | `testNativeUnfillableInputRevertsAllCoreAndWalletState`, `testNativePartialSettlementAndUnexpectedETHRevertAtomically`, `testNativeExactInputGuardRejectsPartialFillEvenWhenOutputPassesOracleFloor` | Verification gap identified and strengthened |
| `testNativeMinOutIncludesExecutionFees` | `testNativeMinimumOutputIncludesActualLPAndProtocolFees` | Preserved |
| `testNativeUnexpectedSenderAndCallbackRejected` | `testNativeUnexpectedSenderAndCallbackRejected` | Preserved |
| `testNativeIncorrectWrapperRejectedBeforePull` | `testNativeIdentityMustBeAdmittedBeforePullOrMint`, `testNativeETHOracleAndSourceAdmissionAreDistinctFromWETH` | Obsolete wrapper rule replaced |
| `testNativeAmountsRemainUint128BoundedWithoutPermitApproval` | `testNativeAmountsStayUint128BoundedWithoutPermitApproval` | Pre-existing verification gap strengthened |
| `testNativeLiquidityCallbackHookMaskRejected` | `testNativeHookAndDynamicFeePoliciesRejectBeforeVenueExecution` | Preserved |
| `testNativeDynamicFeeRejected` | `testNativeHookAndDynamicFeePoliciesRejectBeforeVenueExecution` | Preserved |
| `testNativeBrokenWithdrawRollsBack` | `testNativeLifecycleDoesNotCallAnUnusedBrokenWrapper`, `testNativeMintAndIncreaseReturnUnusedETHWithoutCallingBrokenWrapper` | Obsolete wrapper dependency retired |
| `testNativeBrokenDepositRollsBackCredits` | `testNativeLifecycleDoesNotCallAnUnusedBrokenWrapper`, `testNativeRejectedRecipientRollsBackAndReentryCannotCollectTwice` | Obsolete wrapper dependency retired |
| `testNativeUnconsumedPosmValueRollsBackInsteadOfSweeping` | `testNativeRetainedPositionValueRevertsInsteadOfSubsidizingLaterLP`, `testNativePendingFeesMustBeCollectedBeforeIncreasingPrincipal` | Preserved through explicit fault seam |
| `testNativeForcedETHDuringTakeCannotBeClaimed` | `testNativePartialSettlementAndUnexpectedETHRevertAtomically`, `testForcedETHDuringNativeForwardCannotBecomeIncome` | Preserved at both boundaries |
| `testNativeWrapperReentryFailsWhileCreditStillSucceeds` | `testNativeRejectedRecipientRollsBackAndReentryCannotCollectTwice` | Obsolete wrapper callback retired; active callback protected |
| `testNativeRegistryAdmissionRejectsUnreviewedDependencies` | `testNativeAdmissionRetainsItsSeparateFixedIdentityGuard`, `testMatchingSourceStillCannotBypassNativeRuntimePins` | Negative admission preserved; real qualification open |
| `testNativePlanBalancesNetAmountsWithinOnePercentBudget` | `testNativePlannerReadsActualDirectionalProtocolFee`, `testActualV4ThinMarketReconcilesActualPostSwapRatioWithinOriginalOnePercentFloor` | Behavior preserved with corrected evidence reference |
| `testNativePlanUsesDirectionalProtocolFeesAndRejectsChangedLPFee` | `testNativePlannerReadsActualDirectionalProtocolFee` | Preserved |
| `testNativeDisabledPoolStillCollectsAndClosesButCannotEnterOrSwap` | `testNativeDisabledPoolCollectsAndClosesButCannotEnterOrSwap`, `testNativeCollectAndDisabledClosePayETHWithFailedWrapper` | Preserved; ETH denomination |
| `testNativeDisabledPoolExitDoesNotReadUnavailableOracle` | `testNativeDisabledPoolCollectsAndClosesButCannotEnterOrSwap` | Preserved by merged case |
| `testNativeExitPolicyIgnoresDisabledFlagButRequiresValidOracle` | `testNativeExitPriceIgnoresStopFlagButStillRequiresValidOracle` | Preserved |

## Material conclusions

1. Native-to-WETH custody expectations are legitimately retired: current ETH remains ETH, fixed ZZZ is the other principal token, and raw custody exit sends actual pair assets without requiring WETH. Exact balances, refunds, permissions and liabilities remain required.
2. The broad 1000-ETH unfillable swap test did not isolate the exact-input guard: its output floor also rejects. An unchanged foundation test retained the one-wei short-fill check. The new actual-Core narrow-range probe proves a partial fill whose output clears the floor, then requires the Manager’s exact Slippage error and full rollback.
3. Both old and initial replacement uint128 tests accepted any revert with missing native value. The repaired method supplies matching value for both oversized amount slots, poisons later reads, requires exact InvalidAmount and checks unchanged funds/position/approval state. This is a pre-existing verification weakness, not a production bound regression.
4. The prior planner mapping pointed to a direct paired-input cap test. The correct planner evidence is `testActualV4ThinMarketReconcilesActualPostSwapRatioWithinOriginalOnePercentFloor`, which actually executes single-sided two-pass planning and checks deployed LP rather than idle-inclusive NAV. The artificial >99.25% fixture outcome is not a universal guarantee.
5. Some exact assertions moved to unchanged foundation/typed-executor tests. The matrix distinguishes these from assertions directly present in the 20 replacement methods. Real native admission/runtime qualification remains open; old any-revert admission tests did not prove each dependency independently.

## Verification boundary

The earlier 32-method pass retains its exact source/body scope. The new exact-input and repaired bound methods now passed in [the separate two-case execution](solidity/NATIVE_REGRESSIONS.md); unchanged peers were not rerun. Referenced peer-test presence is not a fresh pass. No live RPC, existing Anvil, service, wallet journal, deployment or public transaction is used. Actual feeds/routes/VRF/OpenSea/authorities/operations, maximal gas/economics and independent review remain release gates.
