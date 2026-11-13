"""Offline reconciliation of NEW public RPC observations; never makes RPC calls.

Reuses the unchanged production Approval-log witness and JSON-RPC envelope
parser. Public parsed responses permit semantic replay; --external-root also
checks/replays original response bytes. Neither mode approves a provider or fees.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from keeper.probe import _approval_trace, PROBE_FROM, TRACE_GAS
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RemoteRPCError
from zzz_ops.rpc import Rpc

HERE = Path(__file__).resolve().parent
ZERO_HASH = '0x' + '00' * 32
GAS_INFO = '0x' + '00' * 19 + '6c'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


class RecordedRPC:
    def __init__(self, rows, external_root):
        self.rows, self.external_root, self.used = rows, external_root, []

    def result(self, row):
        request = row['request']
        require(request['method'] in Rpc.READ_METHODS, 'Non-read evidence method')
        response = row['rpc_response']
        if self.external_root is not None:
            relative = row.get('raw_relative_path') or row.get('response_file')
            require(isinstance(relative, str) and relative, 'Original response path is unavailable')
            path = (self.external_root / relative).resolve()
            require(path.is_relative_to(self.external_root), 'External evidence path escapes root')
            require(path.is_file(), 'Original response file is unavailable')
            raw = path.read_bytes()
            require(len(raw) == row['response_bytes'], 'Original response size differs')
            require(hashlib.sha256(raw).hexdigest() == row['response_sha256'], 'Original response hash differs')
            require(json.loads(raw) == response, 'Original response semantic values differ')
        else:
            # Preserve the recorded fields/values and id, without claiming the
            # serialization has the original response's byte-level properties.
            raw = json.dumps(response, separators=(',', ':'), allow_nan=False).encode()
        require(row.get('http_status') == 200 and row.get('body_truncated') is False,
                'Incomplete or unsuccessful evidence transport')
        client = Rpc(['https://offline.invalid'], 4663, timeout=1, retries=1)
        client._ids = iter([request['id']])
        def read_http(_url, sent):
            require(json.loads(sent) == request, 'Production parser request differs')
            return raw
        client._read_http = read_http  # Exact recorded bytes; no socket path.
        self.used.append({'method': request['method'], 'id': request['id'],
                          'response_sha256': row['response_sha256']})
        return client._post('https://offline.invalid', request['method'], copy.deepcopy(request['params']))

    def call(self, method, params):
        matches = [r for r in self.rows if r['request']['method'] == method and r['request']['params'] == params]
        require(len(matches) == 1, 'Captured helper call is missing or ambiguous')
        return self.result(matches[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network-index', type=Path, default=HERE.parent / 'network/RPC.json')
    parser.add_argument('--external-root', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = load(HERE / 'SOURCES.json')
    for name, expected in source['source_sha256'].items():
        require(sha(ROOT / name) == expected, 'Production source changed')
    evidence = load(args.network_index)
    require(evidence['source_baseline'] == source['baseline'], 'Capture baseline differs')
    all_rows = evidence['rows']
    target_pin_path = ROOT / 'reports/market-followup-20261109/routes/runtime-pins.json'
    reviewed = [r for r in load(target_pin_path) if r['name'] == 'WETH']
    require(len(reviewed) == 1, 'Independent probe runtime pin is ambiguous')
    target, runtime_pin = reviewed[0]['address'], reviewed[0]['runtime_keccak256']
    data = calldata('approve(address,uint256)', PROBE_FROM, 0)
    traces = [r for r in all_rows if r['request']['method'] == 'debug_traceCall' and
              isinstance(r.get('rpc_response', {}).get('result'), dict) and
              r['request']['params'][0].get('to') == target and
              r['request']['params'][0].get('data') == data and
              r['request']['params'][0].get('gas') == hex(TRACE_GAS)]
    require(len(traces) == 1, 'New actual Approval trace is missing or ambiguous')
    trace_row = traces[0]
    selector = trace_row['request']['params'][1]
    require(selector.get('requireCanonical') is True and set(selector) == {'blockHash', 'requireCanonical'},
            'Witness lacks an exact canonical hash')
    provider = trace_row['provider_name']
    rows = [r for r in all_rows if r['provider_name'] == provider]
    client = RecordedRPC(rows, args.external_root.resolve() if args.external_root else None)
    witness = _approval_trace(client, target, selector)
    require(witness['approval_event_verified'] is True, 'Actual Approval witness failed')
    header_rows = [r for r in rows if r['request']['method'] == 'eth_getBlockByNumber' and
                   r['request']['params'][0] not in ('latest', 'safe', 'finalized') and
                   r.get('rpc_response', {}).get('result', {}).get('hash') == selector['blockHash']]
    require(len(header_rows) >= 2, 'Canonical numbered-header recheck is missing')
    headers = [r['rpc_response']['result'] for r in header_rows]
    require(all(h == headers[0] for h in headers), 'Canonical header changed')
    require(any(r['observed_at_utc'] < trace_row['observed_at_utc'] for r in header_rows) and
            any(r['observed_at_utc'] > trace_row['observed_at_utc'] for r in header_rows),
            'Witness is not bracketed by numbered headers')
    header = headers[0]
    code = client.call('eth_getCode', [target, selector])
    code_bytes = bytes.fromhex(code[2:])
    require(len(code_bytes) == reviewed[0]['runtime_bytes'] and
            '0x' + keccak256(code_bytes).hex() == runtime_pin, 'Reviewed runtime differs')
    cap_rows = []
    for cap in (20_000_000, 24_000_000):
        tx = {'to': GAS_INFO, 'data': calldata('getMaxTxGasLimit()'), 'gas': hex(cap)}
        current = client.call('eth_call', [tx, selector])
        estimate = client.call('eth_estimateGas', [tx, selector])
        require(isinstance(current, str) and len(current) == 66 and int(current, 16) == 32_000_000,
                'Current transaction parameter differs from captured32M')
        require(21_000 <= int(estimate, 16) <= cap, 'Cheap estimate exceeds selected cap')
        cap_rows.append({'gas_field': cap, 'cheap_estimate': int(estimate, 16),
                         'observed_execution_parameter': int(current, 16),
                         'numerical_provider_work_capacity_qualified': False})
    negative = []
    for method in ('eth_call', 'eth_estimateGas', 'debug_traceCall'):
        found = [r for r in rows if r['request']['method'] == method and
                 len(r['request']['params']) >= 2 and
                 r['request']['params'][1] == {'blockHash': ZERO_HASH, 'requireCanonical': True}]
        require(len(found) == 1, 'Missing or ambiguous negative hash control')
        try:
            client.result(found[0])
        except RemoteRPCError as exc:
            require(exc.code in (-32000, -32001), 'Unexpected negative hash error')
            if method != 'debug_traceCall':
                require(exc.reason == 'unavailable_block', 'Missing-block control is not recognized')
            else:
                # Retain the production classifier result. Independently review
                # only this exact explicit missing-hash wording; do not broaden
                # the production classifier or relabel an ambiguous error.
                message = found[0]['rpc_response']['error']['message']
                require(message == 'block ' + ZERO_HASH + ' not found', 'Unreviewed trace-error wording')
            negative.append({'method': method, 'explicit_error_code': exc.code,
                'rejected': True, 'production_error_reason': exc.reason,
                'production_recognized_unavailable_block': exc.reason == 'unavailable_block'})
        else:
            raise ValueError('Provider accepted an unavailable block')
    require(all(sha(ROOT / name) == value for name, value in source['source_sha256'].items()),
            'Source changed during offline replay')
    result = {'schema': 1, 'baseline': source['baseline'],
        'scope': 'Offline unchanged-helper replay of new actual interface observations only',
        'provider_label': provider, 'anchor': {'number': int(header['number'], 16),
            'hash': header['hash'], 'timestamp': int(header['timestamp'], 16)},
        'probe_address': target, 'independently_retained_runtime_pin': runtime_pin,
        'approval_witness': witness, 'gas_field_admission': cap_rows,
        'method_specific_unknown_hash_controls': negative,
        'original_response_bytes_checked': args.external_root is not None,
        'network_index_sha256': sha(args.network_index), 'source_manifest_sha256': sha(HERE / 'SOURCES.json'),
        'independent_runtime_manifest_sha256': sha(target_pin_path),
        'offline_rpc_parser_replays': client.used, 'new_network_calls': 0,
        'new_evm_test_executions': 0, 'unchanged_tests_rerun': 0,
        'independent_genesis_reviewed': False, 'full_activation_api_v1_profile_passed': False,
        'actual_popl_public_operation_qualified': False, 'complete_fee_policy_approved': False,
        'provider_adopted': False, 'production_approved': False,
        'verifier_sha256': sha(Path(__file__))}
    with args.output.open('x', encoding='utf8', newline='\n') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'offline_witness_passed': True, 'new_network_calls': 0,
                      'complete_fee_policy_approved': False, 'production_approved': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'offline_witness_passed': False, 'error_type': type(exc).__name__,
                          'new_network_calls': 0, 'production_approved': False}))
        raise SystemExit(1) from None
