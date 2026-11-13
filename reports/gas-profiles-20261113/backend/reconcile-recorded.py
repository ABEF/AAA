"""Reconcile NEW owned-Anvil RPC captures with production gas/trace readers.

Offline only: this program has no RPC client, signer or broadcast path. It does
not perform complete ActivationConfig/Projection inventory or market admission.
The isolated fee settings describe the captured local execution demonstrator;
they do not attest Robinhood's complete fee accounting or approve live adoption.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from frontend_api.activation import ActivationTransactions
from frontend_api.activation_trace import measure
from frontend_api.transaction_gas import configured_limit

SOURCES = (
    'frontend_api/activation.py', 'frontend_api/activation_trace.py',
    'frontend_api/activation_config.py', 'frontend_api/transaction_gas.py',
    'frontend_api/activation_v4.py', 'frontend_api/liquidity_context.py',
    'frontend_api/service.py', 'zzz_ops/abi.py',
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()))


class RecordedOnly:
    def __init__(self, records):
        self.records = records
        self.used = []

    def call(self, method, params):
        matches = [r for r in self.records if r['method'] == method and r['params'] == params]
        if not matches:
            raise AssertionError('Production helper requested an uncaptured RPC call: ' + method)
        values = [r['response'] for r in matches]
        if any('error' in x or 'result' not in x for x in values):
            raise AssertionError('Recorded response is not successful: ' + method)
        if any(x['result'] != values[0]['result'] for x in values):
            raise AssertionError('Ambiguous captured response: ' + method)
        self.used.append({'method': method, 'params': copy.deepcopy(params)})
        return copy.deepcopy(values[0]['result'])


def reconcile(directory):
    fixture_path = directory / 'actual-profile-fixture.json.gz'
    records_path = directory / 'rpc-records.json.gz'
    fixture = read(fixture_path)
    records = read(records_path)
    profile = fixture['profile']
    assert profile['cap'] == 20_000_000 and profile['padding_bps'] == 2000
    assert fixture['request']['execution_price_version'] == 1
    assert fixture['request']['lp_routing_version'] == 3
    assert fixture['request']['accounting_version'] == 7
    assert all(sha(ROOT / p) == value for p, value in fixture['contract_source_sha256'].items())
    full_tx = fixture['transaction']
    assert int(full_tx['gas'], 16) == 20_000_000
    trace_call = fixture['actual_trace_call']
    assert trace_call['method'] == 'debug_traceCall' and trace_call['params'][0] == full_tx
    header = fixture['confirmed_block']
    block = {'blockHash': header['hash'], 'requireCanonical': True}
    assert trace_call['params'][1] == block
    exact_trace = [r for r in records if r['method'] == trace_call['method'] and
                   r['params'] == trace_call['params']]
    assert exact_trace and all(r['response'].get('result') == trace_call['result'] for r in exact_trace)
    measurement = measure(copy.deepcopy(trace_call['result']), copy.deepcopy(full_tx),
                          fixture['pins'], copy.deepcopy(fixture['request']),
                          fixture['gross_usd_18'], fixture['max_slippage_bps'])
    assert measurement == fixture['expected_measurement']

    rpc = RecordedOnly(records)
    service = object.__new__(ActivationTransactions)
    service.p = SimpleNamespace(rpc=rpc)
    # Isolated existing gas-helper inputs, NOT full deployment/service admission.
    # The execution-only fee cap is the original capture's explicit local value.
    service.config = SimpleNamespace(schema=2, max_gas_limit=configured_limit('20000000'),
        max_gas_price=fixture['gas_price_wei'], max_network_fee=fixture['reviewed_fee_wei'],
        fee_review='0x' + sha(fixture_path))
    normalized_header = {'hash': header['hash'], 'number': int(header['number'], 16),
                         'timestamp': int(header['timestamp'], 16)}
    gas_review = service._gas_review(normalized_header)
    unsigned_tx = {k: v for k, v in full_tx.items() if k != 'gas'}
    before = copy.deepcopy(unsigned_tx)
    gas = service._gas(unsigned_tx, block, gas_review)
    assert unsigned_tx == before and 'gas' not in unsigned_tx and 'nonce' not in unsigned_tx
    assert int(gas['estimated_units']) == fixture['estimate_gas']
    assert int(gas['suggested_limit']) == fixture['padded_gas']
    assert int(gas['suggested_limit_cost_wei']) == fixture['reviewed_fee_wei']
    assert gas['full_twenty_percent_headroom'] and gas_review.effective == 20_000_000
    assert len(rpc.used) == 4
    return {
        'case': profile['label'], 'fixture_sha256': sha(fixture_path),
        'rpc_records_sha256': sha(records_path), 'fixture_bytes': fixture_path.stat().st_size,
        'rpc_records_bytes': records_path.stat().st_size,
        'actual_owner': full_tx['from'], 'confirmed_block_hash': header['hash'],
        'confirmed_block_gas_limit': int(header['gasLimit'], 16),
        'selected_gas_limit': 20_000_000, 'estimate_gas': fixture['estimate_gas'],
        'padded_gas': fixture['padded_gas'], 'remaining_padded_margin': 20_000_000 - fixture['padded_gas'],
        'local_execution_price_wei': fixture['gas_price_wei'],
        'local_execution_fee_ceiling_wei': fixture['reviewed_fee_wei'],
        'exact_recorded_rpc_calls': rpc.used, 'measurement': measurement,
        'production_measurement_matches': True, 'production_gas_helper_matches': True,
        'full_service_config_inventory_admitted': False,
        'target_chain_fee_qualification': False, 'live_adoption': False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('captures', nargs='+', type=Path)
    args = parser.parse_args()
    before = {p: sha(ROOT / p) for p in SOURCES}
    results = [reconcile(p.resolve()) for p in args.captures]
    after = {p: sha(ROOT / p) for p in SOURCES}
    assert before == after
    output = {'schema': 1, 'scope': 'Offline production-helper replay of new owned-Anvil captures only',
              'cases': results, 'passed': len(results), 'evm_executions': 0, 'network_requests': 0,
              'source_sha256_before': before, 'source_sha256_after': after,
              'runner_sha256': sha(Path(__file__)), 'production_approved': False}
    with args.output.open('x', encoding='utf8', newline='\n') as handle:
        json.dump(output, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'passed': len(results), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
