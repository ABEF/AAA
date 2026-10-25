"""Affected direct-governance/Position/zero-custody financial behaviors only."""
from pathlib import Path
import hashlib,importlib.util,sys
R=Path(__file__).resolve().parents[3]
driver=R/'reports/simplification-20261025/solidity/run-focused.py'
assert hashlib.sha256(driver.read_bytes()).hexdigest()=='d95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'
spec=importlib.util.spec_from_file_location('pruning_runner',driver)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.SELECTION={
 'DirectGovernanceTest':'*','ZeroAssetCanonicalTest':'*','FixedZZZPoolTest':'*',
 'DualOracleSecurityTest':{
  'testDualBoundsUseLowerForThresholdAndUpperForConversionQuote','testSpreadExactBoundaryAndOneRawUnitAbove',
  'testStaleEitherSourceCannotFallBackToHealthySource','testPolicyHistoryAppendOnlyEvenWhenReturningToSameParameters',
  'testRetiredSingleFeedGetterCannotMasqueradeAsDualPricePolicy'},
 'EntryReviewPolicyTest':{
  'testReviewedMaximumRejectsRaisedGovernedCapBeforeSourcePullAndSwap',
  'testGrowthReviewRejectsWideningAndPreservesExistingSharesAndClaims',
  'testTenPercentMaximumCannotOverrideStrongerPhysicalVenueMinimum'},
 'CustodyHandoffTest':{
  'testExitAlwaysSendsOnlyZZZAndPreservesDonationsSharesAndRoyalties',
  'testEmergencyRawExitWorksWithFailedSwapAndStalePrices',
  'testRecoveredCustodyNeedsFullActualSentZZZAndCanRemainPaused',
  'testSwapFailureRevertsWholeExitWithoutAutomaticRawFallback',
  'testLocalEndToEndBudgetIncludesExitAndRedeployment'},
 'NativeCustodyTest':{
  'testRawNativeExitHasNoZZZOrWrapperDependencyAndPreservesPrefund',
  'testRecoveryRequiresExactNativeValueDespitePrefunds','testLocalCompletionForwardsExactNativeBudgetAndPreservesShares'},
 'CanonicalPreparationTest':'*',
 'CanonicalHandoffTest':{
  'testCompleteHandoffPreservesOwnersSharesTraitsAndBothRewardLedgers',
  'testFullHandoffCarriesConvertedNativeLPRewardsToCurrentOwner',
  'testAccountingV3UsesEightWordPositionAndRejectsLegacyOrTrailingGroupRows',
  'testPartialFundingCannotActivateAndFundingCannotReplay','testAbortAfterFundingRequiresExactReturnedBacking',
  'testRetiredSourceCannotAbortRecommitOrReopenThroughUnpause',
  'testFundingCallbackCannotAbortHalfwayThroughExactPrincipalTransfer'},
 'GlobalMembershipDustTest':{
  'testBrokenHistoricalVenueStillSettlesFundedDustOnlyToIncumbents',
  'testHistoricalDustPaymentFailureRejectsEntryWithoutLosingOldRights',
  'testMembershipSkipsInactiveBucketAndFeeControllerRejectsItsDustFlush'},
 'NativeCanonicalIntegrationTest':'*',
}
B=m.EXTERNAL/'architecture-pruning-20261025/solidity'
sys.argv=[str(driver),'--evidence',str(B/'selected'),'--compiler-input',str(B/'all-source-typecheck-input.json'),
 '--compiler-output',str(B/'all-source-typecheck.json'),'--size-evidence',str(B/'source-size-gates.json'),*sys.argv[1:]]
raise SystemExit(m.main())
