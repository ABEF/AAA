"""Offline capacity/history evidence integrity only; no network, tests or EVM."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pairs(items):
    value = {}
    for key, item in items:
        require(key not in value, 'Duplicate evidence key')
        value[key] = item
    return value


def decode(raw):
    def reject(_item):
        raise ValueError('Nonfinite JSON evidence')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


def load(path):
    return decode(path.read_bytes())


def result(row):
    return row['rpc_response']['result']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external-root', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    source, plan, rpc, summary = (load(HERE / name) for name in
                                 ('SOURCES.json', 'PLAN.json', 'RPC.json', 'RESULTS.json'))
    for name, expected in source['source_sha256'].items():
        require(sha(ROOT / name) == expected, 'Production source differs')
    require(rpc['source_baseline'] == source['baseline'] == summary['baseline'], 'Baseline differs')
    require(rpc['plan_sha256'] == sha(HERE / 'PLAN.json'), 'Executed plan differs')
    for name, expected in summary['evidence_sha256'].items():
        require(sha(HERE / name) == expected, 'Published evidence differs')
    rows = rpc['rows']
    require(len(rows) == 19 and summary['rpc_attempts'] == 19 and len(rpc['diagnostics']) == 3 and
            all(item['ok'] is True for item in rpc['diagnostics']), 'Scoped diagnostics/count differ')
    require(plan['wire_limits']['maximum_rpc_attempts'] == 19 and
            plan['wire_limits']['minimum_spacing_seconds'] == 2, 'Approved bounds differ')
    previous = None
    external_count = 0
    for index, row in enumerate(rows, 1):
        request, response = row['request'], row['rpc_response']
        require(request['id'] == index and response.get('jsonrpc') == '2.0' and
                type(response.get('id')) is int and response['id'] == index and
                'result' in response and 'error' not in response, 'RPC identity/result differs')
        require(row['http_status'] == 200 and row['body_truncated'] is False and
                0 < row['response_bytes'] <= 262144 and row['duration_ms'] <= 12000,
                'Transport bounds differ')
        stamp = dt.datetime.fromisoformat(row['observed_at_utc'])
        require(previous is None or (stamp-previous).total_seconds() >= 1.99, 'Recorded spacing differs')
        previous = stamp
        if args.external_root:
            base = args.external_root.resolve()
            raw_path = (base / 'rpc-permitted' / row['response_file']).resolve()
            require(raw_path.is_relative_to(base), 'External response path escapes root')
            raw = raw_path.read_bytes()
            require(len(raw) == row['response_bytes'] and hashlib.sha256(raw).hexdigest() == row['response_sha256'] and
                    decode(raw) == response, 'Original RPC response differs')
            external_count += 1
    tiny = rows[:11]
    require([r['request']['method'] for r in tiny] == ['eth_chainId', 'eth_getBlockByNumber',
        'eth_getCode', 'eth_getBalance', 'eth_getTransactionCount', 'eth_call', 'eth_call',
        'eth_estimateGas', 'debug_traceCall', 'eth_call', 'eth_getBlockByNumber'], 'Tiny call sequence differs')
    require(int(result(tiny[0]),16) == 4663, 'Wrong capability chain')
    head = result(tiny[1])
    selector = {'blockHash': head['hash'], 'requireCanonical': True}
    target = '0x' + keccak256(b'PoPL read-only RPC override capability 20261113 11e7488')[-20:].hex()
    require(target == plan['override']['target'] and plan['override']['runtime'] == '0x600160005260206000f3',
            'Tiny task target/code differs')
    require(result(tiny[2]) == '0x' and int(result(tiny[3]),16) == int(result(tiny[4]),16) == 0,
            'Task address was not empty')
    tx = {'to': target, 'data': '0x', 'gas': hex(50000)}
    override = {target: {'code': '0x600160005260206000f3'}}
    require(tiny[5]['request']['params'] == tiny[9]['request']['params'] == [tx, selector] and
            result(tiny[5]) == result(tiny[9]) == '0x', 'Nonpersistent negative controls differ')
    require(tiny[6]['request']['params'] == tiny[7]['request']['params'] == [tx, selector, override] and
            result(tiny[6]) == '0x'+f'{1:064x}' and 21000 <= int(result(tiny[7]),16) <= 50000,
            'Code-only call/estimate differs')
    require(tiny[8]['request']['params'] == [tx, selector, {'tracer':'callTracer', 'timeout':'5s',
            'tracerConfig':{'withLog':True}, 'stateOverrides':override}], 'Trace override/options differ')
    trace = result(tiny[8])
    require(trace['type'] == 'CALL' and trace['to'].lower() == target and trace['output'] == '0x'+f'{1:064x}' and
            0 < int(trace['gasUsed'],16) <= 50000 and not trace.get('error'), 'Tiny trace output differs')
    require(result(tiny[-1])['hash'] == head['hash'] and result(tiny[-1])['number'] == head['number'] and
            result(tiny[-1])['timestamp'] == head['timestamp'], 'Tiny canonical recheck differs')
    event = plan['logs']['expected_event']
    require(int(result(rows[11]),16) == 4663 and rows[13]['request'] == {
        'jsonrpc':'2.0', 'id':14, 'method':'eth_getLogs', 'params':[plan['logs']['filter']]}, 'Log filter differs')
    keys = ('address','topics','data','transactionHash','logIndex','blockHash','blockNumber','transactionIndex')
    matches = [x for x in result(rows[13]) if all(x.get(k) == event[k] for k in keys) and x.get('removed') is False]
    require(len(matches) == 1, 'Retained genuine event differs')
    old_rpc = load(ROOT / 'reports/rpc-fees-20261113/network/RPC.json')
    retained = next(x['rpc_response']['result'] for x in old_rpc['rows'] if
                    x.get('phase') == 'permitted/pinax-receipt' and x['request']['method'] == 'eth_getTransactionReceipt')
    require(event == retained['logs'][0], 'Event is not the retained actual receipt')
    for i in (12,14):
        require(result(rows[i])['hash'] == plan['logs']['block_hash'] and
                int(result(rows[i])['number'],16) == plan['logs']['block_number'], 'Log canonical header differs')
    archive = plan['archive']
    require(sha(ROOT / archive['retained_source']) == archive['retained_source_sha256'], 'Retained source differs')
    require(rows[16]['request']['params'] == archive['code_params'] and
            rows[17]['request']['params'] == archive['call_params'], 'Archive hash selector differs')
    code = bytes.fromhex(result(rows[16])[2:])
    require(len(code) == archive['expected_runtime_bytes'] and '0x'+keccak256(code).hex() == archive['expected_runtime_hash'] and
            result(rows[17]) == archive['expected_call_result'], 'Retained runtime/state differs')
    for i in (15,18):
        require(result(rows[i])['hash'] == archive['block_hash'] and
                int(result(rows[i])['number'],16) == archive['block_number'], 'Archive canonical header differs')
    primary = load(HERE / 'PRIMARY_SOURCES.json')
    require(len(primary['primary_documents']) == 8, 'Primary document count differs')
    if args.external_root:
        base = args.external_root.resolve()
        for doc in primary['primary_documents']:
            path = (base/doc['external_relative_path']).resolve()
            require(path.is_relative_to(base) and sha(path) == doc['sha256'] and
                    path.stat().st_size == doc['bytes'] and doc['status'] == 200, 'Primary source bytes differ')
            external_count += 1
        require(sha(base/'probe_capacity.py') == rpc['producer_sha256'], 'Campaign producer source differs')
        external_count += 1
    for row in load(HERE/'REUSED_TRACE_FOOTPRINTS.json')['cases']:
        require(sha(ROOT/row['source']) == row['sha256'], 'Reused trace source differs')
    require(all(x['public_execution_allowed'] is False for x in load(HERE/'OVERRIDE_SIZING.json')['cases']),
            'Unsent graph sizing was relabeled')
    approval = load(HERE/'PROVIDER_ACCEPTANCE.json')['approval']
    require(approval['live_adoption'] is False and approval['production_approved'] is False and
            approval['review_hash'] is None and approval['qualified_gas_limit'] is None,
            'Unapproved provider worksheet was relabeled')
    require(summary['full20m_24m_work_capacity_qualified'] is False and summary['heavy_graph_requests'] == 0 and
            rpc['public_transactions'] == 0 and rpc['heavy_graph_attempts'] == 0, 'Scope/approval differs')
    output = dict(schema=1, rpc_attempts=19, actual_diagnostics_verified=3, external_files_checked=external_count,
        public_rpc_sha256=sha(HERE/'RPC.json'), sources_unchanged=True,
        new_network_requests=0, new_tests_evm_or_compiles=0, numerical_capacity_qualified=False,
        production_approved=False, verifier_sha256=sha(Path(__file__)))
    if args.output:
        with args.output.open('x',encoding='utf8') as handle:
            json.dump(output,handle,indent=2);handle.write('\n')
    print(json.dumps(output))


if __name__ == '__main__':
    main()
