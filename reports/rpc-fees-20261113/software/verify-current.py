"""Offline current-source/data equivalence; reuses the completed baseline witness.

No RPC client, trace helper, test suite, EVM or compiler is invoked. The original
helper replay is immutable in BASELINE_TRACE_REPLAY.json and verify.py.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate evidence key')
            result[key] = value
        return result
    def reject(_value):
        raise ValueError('Nonfinite evidence value')
    return json.loads(path.read_text(encoding='utf8'), object_pairs_hook=pairs, parse_constant=reject)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network-index', type=Path, default=HERE.parent / 'network/RPC.json')
    parser.add_argument('--external-root', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    baseline = load(HERE / 'SOURCES.json')
    closure = load(HERE / 'TRACE_CLOSURE.json')
    witness = load(HERE / 'BASELINE_TRACE_REPLAY.json')
    require(witness['source_manifest_sha256'] == sha(HERE / 'SOURCES.json'), 'Baseline source manifest changed')
    require(witness['network_index_sha256'] == closure['initial_network_index_sha256'],
            'Original witness and capability snapshot differ')
    require(witness['verifier_sha256'] == sha(HERE / 'verify.py'), 'Original replay source changed')
    require(witness['approval_witness']['approval_event_verified'] is True, 'Baseline witness did not pass')
    for name, expected in closure['full_source_sha256'].items():
        require(sha(ROOT / name) == expected, 'Trace/RPC/ABI source changed')
    monitor_path = ROOT / 'keeper/monitor.py'
    monitor_source = monitor_path.read_text(encoding='utf8')
    tree = ast.parse(monitor_source)
    functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name, expected in closure['imported_monitor_function_AST_sha256'].items():
        require(name in functions, 'Imported monitor helper is missing')
        node = functions[name]
        require(hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest() == expected,
                'Imported monitor helper AST changed')
        require(hashlib.sha256(ast.get_source_segment(monitor_source, node).encode()).hexdigest() ==
                closure['monitor_selected_function_source_sha256'][name],
                'Imported monitor helper source changed')
    drift = []
    for name, old_hash in baseline['source_sha256'].items():
        current = sha(ROOT / name)
        if current != old_hash:
            require(name == 'keeper/monitor.py', 'Unreviewed production source drift')
            drift.append({'source': name, 'baseline_sha256': old_hash, 'current_sha256': current,
                          'scope': 'Separate explicit future-only keeper fee-profile work; no trace-helper change'})
    network = load(args.network_index)
    require(network['source_baseline'] == baseline['baseline'], 'Network capture baseline changed')
    rows = network['rows']
    capability = []
    for entry in closure['baseline_capability_rows']:
        matches = [r for r in rows if r.get('phase') == entry['phase'] and
                   r['request']['method'] == entry['method'] and r['request']['id'] == entry['id']]
        require(len(matches) == 1, 'Original capability row is missing or ambiguous')
        row = matches[0]
        require(semantic_sha(row['request']) == entry['request_semantic_sha256'] and
                row.get('response_sha256') == entry['response_sha256'] and
                semantic_sha(row.get('rpc_response')) == entry['parsed_response_semantic_sha256'],
                'Original capability request/response changed')
        if args.external_root:
            root = args.external_root.resolve()
            path = (root / row['raw_relative_path']).resolve()
            require(path.is_relative_to(root), 'Original capability path escapes root')
            raw = path.read_bytes()
            require(hashlib.sha256(raw).hexdigest() == entry['response_sha256'] and
                    len(raw) == row['response_bytes'] and json.loads(raw) == row['rpc_response'],
                    'Original capability response bytes differ')
        capability.append(entry)
    require(len(capability) == 16, 'Original capability row count differs')
    exact = []
    for entry in witness['offline_rpc_parser_replays']:
        found = [r for r in rows if r.get('provider_name') == witness['provider_label'] and
                 r['request']['method'] == entry['method'] and r['request']['id'] == entry['id'] and
                 r.get('response_sha256') == entry['response_sha256']]
        require(len(found) == 1, 'Original witness response is missing, ambiguous or changed')
        row = found[0]
        require(row.get('http_status') == 200 and row.get('body_truncated') is False,
                'Incomplete witness response')
        exact.append({'method': entry['method'], 'id': entry['id'], 'response_sha256': entry['response_sha256']})
    require(len(exact) == 10, 'Baseline replay count differs')
    receipt = load(HERE / 'BASELINE_RECEIPT.json')
    require(receipt['ethereum_fees_source_sha256'] == sha(ROOT / 'zzz_ops/ethereum_fees.py'),
            'Generic Ethereum fee source changed')
    require(receipt['helper_matches_reported_price'] is False and
            receipt['helper_execution_price_wei'] != receipt['reported_execution_price_wei'],
            'Original nonzero-tip discrepancy was relabeled')
    result = {'schema': 1, 'scope': 'Current static source/data equivalence; no unchanged witness or test rerun',
        'baseline': baseline['baseline'], 'baseline_trace_replay_sha256': sha(HERE / 'BASELINE_TRACE_REPLAY.json'),
        'baseline_nonzero_tip_receipt_sha256': sha(HERE / 'BASELINE_RECEIPT.json'),
        'source_snapshot_sha256': sha(HERE / 'SOURCES.json'), 'trace_closure_sha256': sha(HERE / 'TRACE_CLOSURE.json'),
        'source_drift_separately_scoped': drift,
        'full_trace_rpc_abi_source_hashes_match': True, 'imported_monitor_helpers_AST_and_source_match': True,
        'all_original_capability_rows_unchanged': capability,
        'original_witness_responses_unchanged': exact,
        'network_index_sha256': sha(args.network_index), 'network_index_rows': len(rows),
        'original_response_bytes_rechecked': bool(args.external_root),
        'baseline_nonzero_tip_fee_discrepancy_preserved': True,
        'actual_trace_replayed_in_baseline': True, 'new_trace_replays': 0,
        'new_rpc_parser_replays': 0, 'new_network_calls': 0, 'new_evm_tests_or_compiles': 0,
        'unchanged_tests_rerun': 0, 'full_activation_api_v1_profile_passed': False,
        'complete_fee_policy_approved': False, 'actual_public_popl_operation_qualified': False,
        'provider_adopted': False, 'production_approved': False, 'verifier_sha256': sha(Path(__file__))}
    with args.output.open('x', encoding='utf8', newline='\n') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'source_and_evidence_equivalence': True, 'new_trace_replays': 0,
                      'new_network_calls': 0, 'production_approved': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'source_and_evidence_equivalence': False, 'error_type': type(exc).__name__,
                          'new_network_calls': 0, 'production_approved': False}))
        raise SystemExit(1) from None
