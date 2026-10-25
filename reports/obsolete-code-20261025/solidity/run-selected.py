"""Execute only cleanup-affected behavior using the existing exact AST harness.

No public RPC, signer, service or persistent local chain is accessed. The
referenced historical harness is pinned before import. Retired tests are not
counted as current passing coverage.
"""
from pathlib import Path
import hashlib, importlib.util, sys

R=Path(__file__).resolve().parents[3]
driver=R/'reports/simplification-20261025/solidity/run-focused.py'
EXPECTED_DRIVER='d95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'
if hashlib.sha256(driver.read_bytes()).hexdigest()!=EXPECTED_DRIVER:
    raise ValueError('Reviewed AST harness changed')
spec=importlib.util.spec_from_file_location('cleanup_scoped_runner',driver)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.SELECTION={
    'RegistryNativeFundsBoundaryTest':'*',
    'OperatorControlsTest':{
        'testPoolStopWorksWhenPriceTokenAndVenueCallsFail',
        'testPoolStopOnlyClearsSelectedFlagsAndIsIdempotent',
        'testOnlyApprovedGovernanceCanToggleControlsAfterSeal',
    },
    'EntryReviewPolicyTest':{
        'testReviewVersionsAreExplicit',
        'testReviewedMaximumRejectsRaisedGovernedCapBeforeSourcePullAndSwap',
    },
    'NativeCanonicalFundingTest':{
        'testCanonicalLedgerNativeTwoStageFundingPartialAbortAndPrefund',
        'testVaultCanonicalNativeForwardAndAbortUseZeroValueAcknowledgment',
    },
    'NFTMetadataTest':{
        'testBaseURICannotChangeAfterSealOrOverwriteConstructorCommitment',
        'testPendingAndRevealedTokenURIsAreValidJSONAndNonexistentIDsRevert',
    },
}
B=module.EXTERNAL/'obsolete-code-audit-20261025/solidity'
sys.argv=[str(driver),'--evidence',str(B/'selected'),
          '--compiler-input',str(B/'all-source-typecheck-input.json'),
          '--compiler-output',str(B/'all-source-typecheck.json'),
          '--size-evidence',str(B/'source-size-gates.json'),*sys.argv[1:]]
raise SystemExit(module.main())
