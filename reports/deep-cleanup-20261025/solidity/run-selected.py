"""Execute only affected native-venue, role-log and royalty-ledger behaviors.

The shared AST-selection driver is hash pinned and unchanged.  This wrapper
additionally checks every production, test and installed dependency input before
and after execution; it never connects to an RPC or a running Anvil instance.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BUILD = EXTERNAL / 'deep-cleanup-20261025/solidity'
EVIDENCE = BUILD / 'selected'
DRIVER = ROOT / 'reports/simplification-20261025/solidity/run-focused.py'
DRIVER_SHA = 'd95a638be139624cb109c34612230043f9f40a50a68672c17aaba3cca5c9c1ee'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def bindings(stage):
    assert digest(DRIVER) == DRIVER_SHA, 'Pinned selection driver changed'
    summary = load(BUILD / 'typecheck-summary.json')
    sizes = load(BUILD / 'source-size-gates.json')
    compiler_input = BUILD / 'all-source-typecheck-input.json'
    compiler_output = BUILD / 'all-source-typecheck.json'
    assert summary['all_pass'] and sizes['all_pass']
    assert digest(compiler_input) == summary['compiler_input_sha256']
    assert digest(compiler_output) == summary['compiler_output_sha256']
    supplied = load(compiler_input)['sources']
    expected = dict(summary['source_sha256'])
    expected.update(summary['dependency_source_sha256'])
    assert len(expected) == len(supplied) == 265
    actual = {name: digest(ROOT / name) for name in expected}
    assert actual == expected, 'Project or installed dependency changed since AST'
    for name, item in supplied.items():
        assert (ROOT / name).read_bytes().decode('utf-8-sig') == item['content'], name
    production = dict(sizes['source_sha256'])
    production.update(sizes['dependency_source_sha256'])
    assert len(production) == 75
    assert all(actual[name] == value for name, value in production.items())
    return {'stage': stage, 'driver_sha256': DRIVER_SHA,
            'compiler_input_sha256': digest(compiler_input),
            'compiler_output_sha256': digest(compiler_output),
            'size_evidence_sha256': digest(BUILD / 'source-size-gates.json'),
            'project_inputs': len(summary['source_sha256']),
            'dependency_inputs': len(summary['dependency_source_sha256']),
            'normal_build_inputs': len(production), 'all_match': True,
            'source_sha256': actual}


EVIDENCE.mkdir(parents=True, exist_ok=True)
save(EVIDENCE / 'bindings-before.json', bindings('before'))
spec = importlib.util.spec_from_file_location('deep_cleanup_runner', DRIVER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.SELECTION = {
    'NativeLiquidityTest': '*',
    'DirectGovernanceTest': {
        'testInitialRoleLogsReconstructBothConstructorGrants',
        'testBootstrapRoleGrantAndRevocationLogsMatchStoredEntitlements',
        'testSealedGovernanceRoleLogsCoverGrantAndRevocationWithoutBootstrapAuthority',
        'testUnauthorizedOrInvalidRoleUpdatesEmitNothingAndPreserveMappings',
    },
    'V3VenueValidationTest': '*',
    'NFTOwnershipRightsTest': {
        'testUnavailableRoyaltyCurrencyDefersOnlyItsEligibilityWhileActualLPActivates',
    },
    'RoyaltyCustodyTest': {
        'testFullReturnIsNotNewIncomeAndRightsFollowTransfer',
        'testNativeExitAndExactReturn',
    },
    'RoyaltyConversionTest': {
        'testBatchConvertsOnlyEarnedBalancesAndKeepsNativeEntitlement',
        'testLossOverOnePercentRollsBackEverythingAndRetryWorks',
    },
    'CanonicalHandoffTest': {
        'testFullHandoffCarriesConvertedNativeLPRewardsToCurrentOwner',
    },
}
sys.argv = [str(DRIVER), '--evidence', str(EVIDENCE),
            '--compiler-input', str(BUILD / 'all-source-typecheck-input.json'),
            '--compiler-output', str(BUILD / 'all-source-typecheck.json'),
            '--size-evidence', str(BUILD / 'source-size-gates.json'), *sys.argv[1:]]
try:
    code = module.main()
finally:
    save(EVIDENCE / 'bindings-after.json', bindings('after'))
    before = load(EVIDENCE / 'bindings-before.json')
    after = load(EVIDENCE / 'bindings-after.json')
    assert before['source_sha256'] == after['source_sha256']
raise SystemExit(code)
