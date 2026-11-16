"""Offline finite coverage inventory for this review; no compilation/RPC/tests."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = {
    'ZZZAccessController':'bootstrap-authority-lifecycle',
    'ZZZProtocolPolicy':'future-operating-policy',
    'ZZZActivationAssets':'fixed-source-admission',
    'ZZZActivationEntry':'holder-contribution-interference',
    'ZZZPoolRegistry':'pool-config-and-stop',
    'ZZZPortfolioPolicy':'main-residual-policy',
    'ZZZRebalanceConfirmation':'sampled-confirmation',
    'ZZZStrategy':'price-geometry-eligibility',
    'ZZZOracle':'price-policy-and-scoped-execution',
    'ZZZMigration':'manual-custody-and-terminal-holder-return',
    'ZZZCustodyValidation':'physical-review-and-postcondition-validation',
    'ZZZMigrationBudget':'captured-loss-and-attribution',
    'ZZZContributionPricing':'marginal-NAV-and-maintenance-valuation',
    'ZZZVault':'atomic-principal-custody-and-fee-intake',
    'ZZZVaultCanonical':'contribution-validation-and-canonical-custody',
    'ZZZLiquidityManager':'fixed-recipient-core-execution',
    'ZZZLPPositionExecutor':'physical-main-residual-execution',
    'ZZZLPBalancer':'bounded-post-withdrawal-routing',
    'ZZZLPBalanceMath':'typed-read-only-execution-arithmetic',
    'ZZZCompounder':'authorized-compound-coordination',
    'ZZZFeeController':'actual-fee-split-and-classified-reserves',
    'ZZZMembership':'equal-active-NFT-membership',
    'ZZZBuyback':'fixed-ZZZ-reserve-burn',
    'ZZZRewards':'whole-unit-current-owner-LP-rights',
    'ZZZLPRewardConverter':'same-ledger-LP-conversion-only',
    'ZZZV4RouteExecutor':'fixed-parent-conversion-settlement',
}

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def main() -> None:
    raw = (ROOT/'docs/function-reference.json').read_bytes()
    reference = json.loads(raw)
    examples = json.loads((ROOT/'docs/operator-call-examples.json').read_bytes())['rows']
    rows = []
    selected = [c for c in reference['contracts'] if c['name'] in FAMILIES]
    if {c['name'] for c in selected} != set(FAMILIES):
        raise SystemExit('Reviewed contract identity missing from ABI reference')
    for contract in selected:
        source = contract['source']
        pin = digest((ROOT/source).read_bytes())
        if reference['source_snapshot']['source_sha256'][source] != pin:
            raise SystemExit('Current reviewed source differs from function reference: '+source)
        for function in contract['functions']:
            identity = contract['name']+'.'+function['signature']
            example = examples[identity]
            row = {
                'identity': identity,
                'source': source,
                'source_sha256': pin,
                'kind': function['kind'],
                'mutability': function['state_mutability'],
                'caller_class': example['role'],
                'family': FAMILIES[contract['name']],
                'review_scope': 'source inspection; no new EVM execution',
                'purpose': function['purpose'],
                'authority': function['access'],
                'inputs': function['inputs'],
                'outputs': function['outputs'],
                'native_value': function['native_value'],
                'notes': function['notes'],
                'input_provenance_reference': 'CONTRACT_REVIEW.md#call-chain-and-inclusion-time-input-rules',
                'unit_reference': 'CONTRACT_REVIEW.md#inputstate-observations-checked-against-implementation',
                'source_review_outcome': 'no new confirmed defect in inspected implementation',
            }
            # Read-only endpoints and fixed module/callback entries are included,
            # not mislabeled as direct operator transaction instructions.
            if row['kind'] == 'constructor':
                row['freshness_obligation'] = 'Reviewed immutable construction graph; not a live deployment recipe.'
            elif row['kind'] in ('receive','fallback'):
                row['freshness_obligation'] = 'Verify authenticated sender/native credit scope; not an operator calldata function.'
            elif row['mutability'] in ('view','pure'):
                row['freshness_obligation'] = 'Read at one canonical block; only immutable identity/fixed existing bounds stay stable. Reads do not reserve execution.'
            elif example['role'] in ('M','C'):
                row['freshness_obligation'] = 'Only exact fixed parent/module/callback context; cannot use operator wallet as shortcut.'
            else:
                row['freshness_obligation'] = 'Review inclusion-time lifecycle/authority/policy/market state, exact units and operation-specific snapshot/floors; see action matrix.'
            rows.append(row)
    keys = [r['identity'] for r in rows]
    if len(keys) != len(set(keys)):
        raise SystemExit('Duplicate exact callable identity')
    result = {
        'schema': 1,
        'scope': 'Finite core operator/custody/execution/LP-reward source inspection; not full dynamic qualification.',
        'reference_sha256': digest(raw),
        'contract_count': len(selected),
        'callable_rows': len(rows),
        'direct_governance_bootstrap_keeper_rows': sum(r['caller_class'] in ('G','B','K') for r in rows),
        'new_tests_executed': 0,
        'new_solidity_changes': 0,
        'rows': rows,
    }
    destination = Path(__file__).with_name('contract-coverage.json')
    with destination.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__ == '__main__':
    main()
