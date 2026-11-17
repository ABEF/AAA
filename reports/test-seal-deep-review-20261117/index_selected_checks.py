"""Index existing finite results without rerunning a check or counting reuse twice."""
import json
from pathlib import Path
import re

OWN = Path(__file__).resolve().parent
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-seal-deep-review-20261117')


def read(name):
    return json.loads((OWN / name).read_text(encoding='utf-8-sig'))


def forge_methods(raw):
    return [contract + '.' + name for contract, value in raw.items()
            for name, result in value['test_results'].items() if result['status'] == 'Success']


def main():
    latest = read('LATEST29_VERIFICATION.json')
    guard = read('SEAL_GUARD_VERIFICATION.json')
    guards = []
    for stage in guard['stages'].values():
        for row in stage.get('passed_methods', []):
            if isinstance(row, dict):
                guards.append(row['contract'] + '.' + row['method'])
            else:
                guards.append(row)
    corpus = []
    for stage in read('TEST_CORPUS_VERIFICATION.json')['stages'].values():
        corpus.extend(row['contract'] + '.' + row['method'] for row in stage['results'] if row['status'] == 'Success')
    planner = []
    for name in ('PLANNER_CHECKS.log', 'PLANNER_CHECKS-corrected.log', 'PLANNER_URI_CHECK.log'):
        planner.extend(re.findall(r'^test\w+ \(([^)]+)\) \.\.\. ok$', (EXTERNAL / name).read_text(), re.M))
    groups = {
        'earlier30_strengthened': read('earlier-changed-01.json')['selected'],
        'latest29_strengthened_and_new': latest['selected_solidity_methods'] + [
            'tests_python.test_keeper_standalone_harvest_review.StandaloneHarvestTimingTests.test_enabled_harvest_refreshes_due_clock_while_disabled_keeps_no_extra_head'],
        'irreversible_chain_root_guards': sorted(set(guards)),
        'reservation': read('RESERVATION_VERIFICATION.json')['methods'],
        'planner_and_build': sorted(set(planner)),
        'seadrop_artwork': forge_methods(read('OPENSEA_ARTWORK.json')),
        'normal_profile_permissions': read('profile-corpus-after.json')['selected'],
        'corpus_corrective_cases': corpus,
        'critical_reads_actual_abi': [read('PLANNER_ABI_READ_CHECK.json')['method']],
        'execution_fixtures': read('CURRENT_EXECUTION_RESULT.json')['method_ids'],
    }
    expected = [10, 9, 6, 16, 7, 1, 4, 8, 1, 18]
    assert [len(rows) for rows in groups.values()] == expected
    flat = [method for rows in groups.values() for method in rows]
    assert len(flat) == len(set(flat)) == 80
    value = {'schema': 1, 'unique_selected_methods_passed': len(flat), 'groups': groups,
             'source_scope': 'Finite successes at explicitly recorded original/corrected source stages; not all executed against one final tree',
             'counts_exclude': ['59 individually reviewed original methods unless actually selected',
                               'Repeated corrected executions', 'Four handoff methods already included in execution_fixtures',
                               'Inventory declarations, fuzz inputs, compiler gates, static records, skips and zero selections'],
             'unchanged_full_suites_rerun': False, 'production_approved': False}
    (OWN / 'SELECTED_CHECKS.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'unique_selected_passes': len(flat), 'groups': {key: len(rows) for key, rows in groups.items()}}))


if __name__ == '__main__':
    main()
