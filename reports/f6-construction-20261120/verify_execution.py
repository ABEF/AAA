"""Additional current-F6 wire/nonce/canonical proof, entirely offline.

The maintained constructor verifier is reused at an exact source pin for its
39-instance/112-observation scope. This report-owned supplement verifies the
preflight fields it explicitly leaves unproved. It never starts or contacts a
node, signs, submits, configures, seals or rewrites historical evidence.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PROFILE = 'activation-final-six-20261118'
CAP = 32_000_000
PADDING = 12_500
LIMIT = 128 * 1024 * 1024
CHECKER_SHA256 = 'fc3bb047ae882ce22639937acc9e589d5513b0e0db28941ac762081cddae439d'
TOOLS = {
    'scripts/rehearse-local-deployment.py': '7200f6f4cd03738d71a4024efa18be6490f60344553197ec8f9d4bdb6ceed206',
    'zzz_ops/deployment_plan.py': '1cc30fa06a8c509e2a7e56d9c5d8af4fab469aa2457e545a7366376c4ab93965',
    'zzz_ops/abi.py': '154d92685b6e473bd064880ec15a16a9b8aafa0b9104df671538cf1375a7250d',
}
BUILD_CONTROLS = frozenset(('package-lock.json', 'scripts/install-deps.sh', 'package.json', 'foundry.toml'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def loads(raw):
    require(len(raw) <= LIMIT, 'Evidence exceeds bound')
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False, 'Nonfinite JSON'))


def load(path):
    with Path(path).open('rb') as stream:
        return loads(stream.read(LIMIT + 1))


def quantity(value):
    require(type(value) is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})', value) is not None,
            'Noncanonical hexadecimal quantity')
    return int(value, 16)


def digest(value):
    require(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{64}', value) is not None,
            'Invalid block/transaction hash')
    return value.lower()


def check_build_controls(pins, root=ROOT):
    require(type(pins) is dict and set(pins) == BUILD_CONTROLS, 'Current build-control inventory differs')
    for name, expected in pins.items():
        path = Path(root) / name
        require(path.is_file() and path.stat().st_size <= LIMIT and sha(path.read_bytes()) == expected,
                'Current build-control bytes differ: ' + name)


def address(value):
    require(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{40}', value) is not None,
            'Invalid address')
    return value.lower()


def preflight_body(transaction, gas):
    result = {'from': address(transaction['from']), 'value': '0x0',
              'data': transaction['input'].lower(), 'gas': hex(gas)}
    if transaction.get('to') is not None:
        result['to'] = address(transaction['to'])
    return result


def check_nonce_read(record, account):
    request = record['request']
    require(request['method'] == 'eth_getTransactionCount' and
            request['params'] == [account, 'latest'], 'Nonce read identity/order differs')
    return record['response']['result']


def check_preflight(row, wire, send_index, previous_send_index, tracked_accounts):
    """Prove one exact three-stage preflight and its bracketing nonce reads."""
    tx = row['transaction']
    submitted = wire[send_index]
    require(submitted['request']['method'] == 'eth_sendTransaction', 'Missing exact submission')
    require(submitted['response']['result'] == tx['hash'], 'Submission hash differs')
    full = preflight_body(tx, CAP)
    padded = preflight_body(tx, row['padded_gas'])
    candidates = []
    for index in range(previous_send_index + 1, send_index):
        request = wire[index]['request']
        if request['method'] not in ('eth_call', 'eth_estimateGas'):
            continue
        params = request.get('params', [])
        if not params or type(params[0]) is not dict:
            continue
        body = params[0]
        if body.get('data', '').lower() == tx['input'].lower() and body.get('to') == full.get('to'):
            candidates.append(index)
    require(len(candidates) == 3 and candidates == list(range(candidates[0], candidates[0] + 3)),
            'Missing/duplicate/noncontiguous preflight stages')
    first, estimate, final = candidates
    require([wire[i]['request']['method'] for i in candidates] ==
            ['eth_call', 'eth_estimateGas', 'eth_call'], 'Preflight stage order differs')
    require(wire[first]['request']['params'] == [full, 'latest'], 'Full-cap preflight fields differ')
    require(wire[estimate]['request']['params'] == [full], 'Estimate preflight fields differ')
    require(wire[final]['request']['params'] == [padded, 'latest'], 'Padded preflight fields differ')
    require(wire[first]['response']['result'] == wire[final]['response']['result'] == row['simulation_return'],
            'Simulation returns differ')
    estimated = quantity(wire[estimate]['response']['result'])
    require(type(row['estimated_gas']) is int and row['estimated_gas'] == estimated,
            'Estimate differs from original wire')
    allowance = (estimated * PADDING + 9999) // 10000
    require(type(row['padded_gas']) is int and 21_000 <= allowance == row['padded_gas'] <= CAP and
            row['padding_bps'] == PADDING, 'Full25% gas padding differs')

    count = len(tracked_accounts)
    require(first - count > previous_send_index and final + count + 1 < send_index,
            'Missing bracketed nonce/gas-price reads')
    before = {}
    after = {}
    for offset, account in enumerate(tracked_accounts):
        before[account] = check_nonce_read(wire[first - count + offset], account)
        after[account] = check_nonce_read(wire[final + 1 + offset], account)
        quantity(before[account]); quantity(after[account])
    require(before == after == row['nonce_before'] and row['simulation_nonce_unchanged'] is True,
            'Sender/factory simulation nonce changed or snapshot detached')
    fee_read = wire[final + 1 + count]
    require(fee_read['request']['method'] == 'eth_gasPrice' and fee_read['request']['params'] == [],
            'Gas-price read missing or reordered')
    price = fee_read['response']['result']; quantity(price)
    frozen = dict(padded, nonce=before[address(tx['from'])], gasPrice=price)
    require(submitted['request']['params'] == [frozen], 'Submission fields differ from frozen padded review')
    require(quantity(tx['gas']) == allowance and quantity(tx['nonce']) == quantity(frozen['nonce']) and
            quantity(tx['gasPrice']) == quantity(price), 'Included transaction envelope differs')

    transaction_reads = [r['response']['result'] for r in wire[send_index + 1:]
                         if r['request']['method'] == 'eth_getTransactionByHash' and
                         r['request']['params'] == [tx['hash']]]
    require(tx in transaction_reads, 'Included transaction detached from original wire')
    receipt_reads = [r['response']['result'] for r in wire[send_index + 1:]
                    if r['request']['method'] == 'eth_getTransactionReceipt' and
                    r['request']['params'] == [tx['hash']]]
    require(row['receipt'] in receipt_reads, 'Included receipt detached from original wire')
    return {'label': row['label'], 'preflight_indices': candidates,
            'send_index': send_index, 'tracked_nonce_accounts': tracked_accounts,
            'estimated_gas': estimated, 'padded_gas': allowance,
            'exact_preflight_nonce_send_and_wire_receipt_verified': True}


def check_headers(rows, wire, captured, genesis_hash):
    """Bind every receipt to captured canonical numbered headers and final tip."""
    require(captured.get('schema') == 1 and type(captured.get('chain_id')) is int and
            captured['chain_id'] == 4663 and digest(captured.get('genesis_hash')) == digest(genesis_hash),
            'Canonical-header capture identity differs')
    headers = captured.get('headers')
    require(type(headers) is list and len(headers) == len(rows), 'Incomplete canonical receipt headers')
    latest_send = max(i for i, r in enumerate(wire) if r['request']['method'] == 'eth_sendTransaction')
    parent = digest(genesis_hash)
    last_header_index = latest_send
    for ordinal, (row, header) in enumerate(zip(rows, headers), 1):
        tx, receipt = row['transaction'], row['receipt']
        require(quantity(header['number']) == ordinal and digest(header['parentHash']) == parent,
                'Receipt header chain is missing/reordered/forked')
        current_hash = digest(header['hash'])
        require(quantity(receipt['blockNumber']) == quantity(tx['blockNumber']) == ordinal and
                digest(receipt['blockHash']) == digest(tx['blockHash']) == current_hash,
                'Receipt/transaction belongs to a different canonical block')
        require(header['transactions'] == [tx['hash']] and receipt['transactionHash'] == tx['hash'] and
                quantity(receipt['transactionIndex']) == quantity(tx['transactionIndex']) == 0,
                'Canonical block transaction inventory differs')
        require(quantity(header['gasUsed']) == quantity(receipt['gasUsed']), 'Canonical block gas differs')
        witnesses = [i for i, item in enumerate(wire) if i > latest_send and
                     item['request']['method'] == 'eth_getBlockByNumber' and
                     item['request']['params'] == [header['number'], False] and
                     item['response']['result'] == header]
        require(witnesses and witnesses[-1] > last_header_index,
                'Canonical numbered header absent/reordered in original wire')
        last_header_index = witnesses[-1]
        parent = current_hash
    closing = captured.get('closing_head')
    require(closing == headers[-1], 'Closing tip differs from final receipt block')
    require(any(i > last_header_index and item['request']['method'] == 'eth_getBlockByNumber' and
                item['request']['params'] == ['latest', False] and item['response']['result'] == closing
                for i, item in enumerate(wire)), 'Closing canonical tip missing from original wire')
    return {'receipt_blocks': len(headers), 'all_numbered_headers_and_closing_tip_wire_bound': True,
            'final_block_number': quantity(closing['number']), 'final_block_hash': closing['hash'],
            'scope': 'Coherent headers from the owned local node, not public-chain finality or provider honesty'}


def verify(folder):
    folder = Path(folder).resolve()
    require(folder.is_dir(), 'Only an existing fresh evidence directory is supported')
    for path, expected in TOOLS.items():
        require(sha((ROOT / path).read_bytes()) == expected, 'Pinned maintained tool changed')
    checker_path = ROOT / 'scripts/check-local-deployment-evidence.py'
    require(sha(checker_path.read_bytes()) == CHECKER_SHA256, 'Pinned maintained checker changed')
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location('f6_base_constructor_evidence', checker_path)
    checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
    from zzz_ops import deployment_plan
    stage = load(folder / 'source-stage.json')
    require(stage.get('accepted_build_profile') == PROFILE and
            stage.get('request_capture') == 'immutable_serialized_request_and_response_snapshot',
            'Only explicit current F6 immutable capture is supported')
    require(stage['tool_sources_sha256'] == TOOLS == load(folder / 'SOURCE_UNCHANGED.json'),
            'Captured tool identity differs')
    artifacts = deployment_plan.Artifacts(build_profile=PROFILE)
    start = load(artifacts.directory / 'START.json')
    require(start['candidate_build_id'] == PROFILE, 'Trusted build start identity differs')
    check_build_controls(start['build_input_sha256'])
    require(stage['source_sha256'] == artifacts.source_pins and
            stage['accepted_build_files_sha256'] == artifacts.file_pins,
            'Current closed source/build identity differs')
    base = checker.reconcile(folder)
    with gzip.open(folder / 'node/rpc-records.json.gz', 'rb') as stream:
        wire = loads(stream.read(LIMIT + 1))
    checker.check_wire(wire)
    instances = {x['role']: x['address'] for x in load(folder / 'instances.json')}
    sender = address(load(folder / 'actual-address-input.json')['inputs']['governance'])
    factories = [instances['royalty_factory'], instances['activation_assets_factory']]
    sends = [(i, r) for i, r in enumerate(wire) if r['request']['method'] == 'eth_sendTransaction']
    require(len(sends) == 44, 'Expected exactly44 closed submissions')
    rows, checked = [], []
    previous = -1
    for ordinal, (index, sent) in enumerate(sends, 1):
        paths = list(folder.glob(f'{ordinal:02d}-*.json'))
        require(len(paths) == 1, 'Missing/duplicate numbered transaction receipt')
        row = load(paths[0]); rows.append(row)
        require(row['transaction']['hash'] == sent['response']['result'], 'Receipt/submission order differs')
        accounts = [sender] + (factories if ordinal > 1 else [])
        checked.append(check_preflight(row, wire, index, previous, accounts))
        previous = index
    headers = check_headers(rows, wire, load(folder / 'MAIN_HEADERS.json'),
                            load(folder / 'node/process.json')['genesis_hash'])
    artifacts.check_sources()
    check_build_controls(start['build_input_sha256'])
    require(all(sha((ROOT / path).read_bytes()) == expected for path, expected in TOOLS.items()),
            'Maintained source changed during offline verification')
    return {'schema': 1, 'status': 'current_f6_additional_wire_proofs_passed', 'build_profile': PROFILE,
            'base_reconciliation': base, 'transactions': checked, 'canonical_headers': headers,
            'preflight_request_fields_verified_from_original_wire': True,
            'preflight_calls': 132, 'bracketing_nonce_reads': 260,
            'source_and_build_rechecked': True, 'current_compiler_sources': 100,
            'current_build_controls': 4, 'compiler_runs': 0, 'new_rpc_calls': 0,
            'signing_or_deployment_or_sealing': False, 'historical_records_relabelled': False,
            'production_approved': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    result = verify(args.evidence)
    raw = (json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode('ascii')
    with args.output.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({k: v for k, v in result.items() if k not in ('transactions', 'base_reconciliation')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
