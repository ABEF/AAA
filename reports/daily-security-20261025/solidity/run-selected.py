"""Only final audit-fix and directly affected economic regressions.

Uses a pinned existing AST selector, byte-preserving selected assertions/helpers.
No public provider, signer, service or existing local chain is accessed.
"""
from pathlib import Path
import hashlib,importlib.util,sys
R=Path(__file__).resolve().parents[3]
driver=R/'reports/simplification-20261025/solidity/run-focused.py'
EXPECTED_DRIVER='d95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'
if hashlib.sha256(driver.read_bytes()).hexdigest()!=EXPECTED_DRIVER:raise ValueError('Reviewed AST harness changed')
spec=importlib.util.spec_from_file_location('daily_audit_runner',driver)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.SELECTION={
    'NativeSourceIdentityTest':'*',
    'FixedZZZBindingTest':'*',
    'GlobalMembershipDustTest':'*',
    'BuybackOperatingLimitTest':{
        'testUpperBoundExactCeilingSucceedsAndOneRawUnitOverReverts',
        'testZeroStopsWithoutPriceOrReserveCallsAndCanBeReopened',
        'testAuthorizedGovernanceCallbackCannotChangePolicyDuringBurn',
        'testNativeExactLimitWorksAndOverLimitPreservesReservesAndDonations',
    },
    'BuybackExecutionTest':{
        'testDirectZZZBurnUsesOnlyBuybackReserveAndPreservesDonations',
        'testApprovedDirectSwapBurnPreservesRewardAndCompoundBalances',
        'testBurnReentryCannotSpendASecondBudgetEvenWithKeeperRole',
    },
    'CustodyHandoffTest':{
        'testExitAlwaysSendsOnlyZZZAndPreservesDonationsSharesAndRoyalties',
        'testCompleteRequiresActualLPAndPreservesNFTAndLedgers',
        'testSwapFailureRevertsWholeExitWithoutAutomaticRawFallback',
        'testEmergencyRawExitWorksWithFailedSwapAndStalePrices',
    },
    'GovernedExecutionLossTest':{
        'testNormalCustodyApprovalCannotBeWeakenedAfterPolicyIncrease',
    },
}
B=module.EXTERNAL/'daily-consistency-audit-20261025/solidity'
sys.argv=[str(driver),'--evidence',str(B/'selected'),
          '--compiler-input',str(B/'all-source-typecheck-control-final-input.json'),
          '--compiler-output',str(B/'all-source-typecheck-control-final.json'),
          '--size-evidence',str(B/'source-size-gates.json'),*sys.argv[1:]]
raise SystemExit(module.main())
