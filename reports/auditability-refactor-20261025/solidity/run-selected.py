"""Affected settlement, shared-converter, route-validation and join behaviors only."""
from pathlib import Path
import hashlib,importlib.util,sys
R=Path(__file__).resolve().parents[3]
driver=R/'reports/simplification-20261025/solidity/run-focused.py'
assert hashlib.sha256(driver.read_bytes()).hexdigest()=='d95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'
spec=importlib.util.spec_from_file_location('auditability_runner',driver)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.SELECTION={
 'NativeAssetFoundationTest':{
  'testNativeCollectDisarmsCreditAndReadsTokenRecipientAfterNativeCallback',
  'testNativeCloseDisarmsCreditAndReadsTokenRecipientAfterNativeCallback',
  'testNativeCollectAndDisabledClosePayETHWithFailedWrapper',
  'testNativeRejectedRecipientRollsBackAndReentryCannotCollectTwice'},
 'LiquidityEncodingTest':{'testCollectUsesZeroDecreaseAndVaultRecipient'},
 'V3VenueValidationTest':'*',
 'AtomicActivationIntegrationTest':{
  'testRealVaultActivationBindsHundredGrossToNinetyNineActualLPAndOwnerEvent',
  'testConversionOwnershipChangeRollsBackSourceTokensAndNFTTransfer'},
 'EntryReviewPolicyTest':{'testGrowthReviewRejectsWideningAndPreservesExistingSharesAndClaims'},
 'LPRewardConversionTest':{
  'testEarnedOnlyConservationAndNoNewcomerRedistribution',
  'testOnePercentBoundaryAndAtomicRollback',
  'testExactUnwrapWithoutPriceAndFailureRecovery',
  'testCallbacksCannotPauseOrExposePartialBalances'},
 'RoyaltyConversionTest':{
  'testBatchConvertsOnlyEarnedBalancesAndKeepsNativeEntitlement',
  'testLossOverOnePercentRollsBackEverythingAndRetryWorks',
  'testExactUnwrapNoSwapOrOracle',
  'testReadOnlyCallbacksCannotObserveIntermediateClaimableBalances'},
 'TypedV4RewardsTest':{
  'testActualV4RoyaltyConversionPreservesNFTWeightsAndEveryPrefund',
  'testActualV4LPConversionPreservesIndividualCollectiveAndExistingETH'},
 'VaultAccountingTest':{
  'testVenueFailureRollsBackActivationKeepsPaidDormantNFT',
  'testTopUpKeepsBothNFTsAndCheckpointsFees',
  'testActivationCannotCollectHistoricalSharedRewards'},
 'NativeVaultFlowsTest':{'testNativeFeesFollowOwnerThroughGrowthAndRepeatedRebalances'},
 'CanonicalHandoffTest':{'testFullHandoffCarriesConvertedNativeLPRewardsToCurrentOwner'},
}
B=m.EXTERNAL/'auditability-refactor-20261025/solidity'
sys.argv=[str(driver),'--evidence',str(B/'selected'),'--compiler-input',str(B/'all-source-typecheck-input.json'),
 '--compiler-output',str(B/'all-source-typecheck.json'),'--size-evidence',str(B/'source-size-gates.json'),*sys.argv[1:]]
raise SystemExit(m.main())
