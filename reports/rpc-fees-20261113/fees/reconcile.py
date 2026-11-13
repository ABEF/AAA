"""Offline fee interpretation of frozen RPC bytes; no network or execution."""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256  # noqa: E402
from zzz_ops.ethereum_fees import execution_price  # noqa: E402


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def words(data, count):
    require(isinstance(data, str) and re.fullmatch('0x[0-9a-fA-F]{' + str(64*count) + '}', data), 'Exact ABI result size required')
    return [int(data[2+64*i:2+64*(i+1)], 16) for i in range(count)]


def components(data, total):
    values = words(data, 4 if total else 3)
    units = values[:2] if total else values[:1]
    require(all(value < 1 << 64 for value in units), 'Noncanonical uint64 component')
    base = values[2] if total else values[1]
    require(base > 0, 'Zero base fee cannot price a component')
    if total:
        require(values[0] >= values[1] and values[0] > 0, 'Poster gas exceeds total')
    return values


def wrap(signature, target, data):
    payload = bytes.fromhex(data[2:])
    return '0x' + (keccak256(signature.encode())[:4] + int(target, 16).to_bytes(32, 'big') + bytes(32) +
                  (96).to_bytes(32, 'big') + len(payload).to_bytes(32, 'big') + payload + bytes((-len(payload)) % 32)).hex()


def decode_rlp(data, offset=0):
    require(offset < len(data), 'Truncated RLP')
    prefix = data[offset]
    if prefix < 128:
        return data[offset:offset+1], offset+1
    is_list = prefix >= 192
    short = 192 if is_list else 128
    long = 247 if is_list else 183
    if prefix <= long:
        size = prefix-short
        start = offset+1
    else:
        length_size = prefix-long
        length_end = offset+1+length_size
        require(length_end <= len(data) and data[offset+1] != 0, 'Invalid RLP length')
        size = int.from_bytes(data[offset+1:length_end], 'big')
        require(size > 55, 'Noncanonical long RLP')
        start = length_end
    end = start+size
    require(end <= len(data), 'RLP extends past input')
    if not is_list:
        require(not (size == 1 and data[start] < 128), 'Noncanonical RLP string')
        return data[start:end], end
    values = []
    while start < end:
        value, start = decode_rlp(data, start)
        require(start <= end, 'RLP child exceeds list')
        values.append(value)
    return values, end


def compute():
    rpc_file = HERE.parent/'network/RPC.json'
    rpc = read(rpc_file)
    rows = rpc['rows']
    require(sha(rpc_file.read_bytes()) == '8f612d2b88d03cf05be171dbb5fcfc66cc2b3d0e547b3c899cd7184691a8d453', 'Frozen RPC transcript changed')
    fee_rows = [r for r in rows if r.get('phase') == 'permitted/pinax-fees']
    receipt_rows = [r for r in rows if r.get('phase') == 'permitted/pinax-receipt']
    zero_rows = [r for r in rows if r.get('phase') == 'permitted/pinax-zero-tip']
    require((len(fee_rows), len(receipt_rows), len(zero_rows)) == (22, 11, 4), 'Fee phase inventory differs')

    def response(phase, method, params=None):
        found = [row for row in phase if row['request']['method'] == method and (params is None or row['request']['params'] == params)]
        require(len(found) > 0, 'Missing recorded RPC response')
        row = found[0]
        for candidate in found:
            require(candidate['http_status'] == 200 and not candidate['body_truncated'] and 'error' not in candidate['rpc_response'], 'Recorded fee read failed')
            require(candidate['rpc_response']['result'] == row['rpc_response']['result'], 'Repeated identical requests disagree')
        return row['rpc_response']['result']

    network = read(HERE.parent/'network/RESULTS.json')
    anchor = network['fee_anchor']
    block = {'blockHash': anchor['hash'], 'requireCanonical': True}
    header = response(receipt_rows, 'eth_getBlockByNumber', [hex(anchor['number']), False])
    require(header['hash'] == anchor['hash'], 'Receipt header differs from fee anchor')
    require(int(response(fee_rows, 'eth_chainId', []), 16) == 4663, 'Wrong fee chain')
    tip_call = next(row for row in fee_rows if row['request']['method'] == 'eth_call' and
                    row['request']['params'][0].get('to') == '0x000000000000000000000000000000000000006b')
    require(tip_call['request']['params'][1] == block, 'Tip policy not canonical-hash pinned')
    collect = words(tip_call['rpc_response']['result'], 1)[0]
    require(collect in (0, 1), 'Noncanonical policy boolean')
    version_call = next(row for row in fee_rows if row['request']['method'] == 'eth_call' and
                        row['request']['params'][0].get('to') == '0x0000000000000000000000000000000000000064')
    require(version_call['request']['params'][1] == block, 'Version not canonical-hash pinned')
    raw_version = words(version_call['rpc_response']['result'], 1)[0]
    require(raw_version == 116, 'Observed version changed')
    cases = []
    plan = read(HERE/'REQUEST_PLAN.json')
    for item in plan['requests']:
        # The original plan contains absolute local paths. Bind only the exact
        # public fixture basename/profile; do not require that workstation path.
        source_path = ROOT/'reports/gas-profiles-20261113/evm/cases'/item['label']/'actual-profile-fixture.json.gz'
        require(sha(source_path.read_bytes()) == item['source_fixture_sha256'], 'Original operation fixture changed')
        source = read(source_path)
        tx = source['transaction']
        require(tx == item['source_transaction'], 'Original transaction fields changed')
        request = item['transaction']
        require(request == {**tx, 'to': '0x00000000000000000000000000000000000000c8',
            'data': wrap('gasEstimateL1Component(address,bool,bytes)', tx['to'], tx['data'])}, 'Virtual request does not preserve exact sender/value/gas/payload')
        output = response(fee_rows, 'eth_call', [request, block])
        poster, base, l1base = components(output, False)
        cases.append(dict(case=item['label'], source_fixture_sha256=item['source_fixture_sha256'],
            source_calldata_sha256=sha(bytes.fromhex(tx['data'][2:])), source_calldata_bytes=len(bytes.fromhex(tx['data'][2:])),
            original_from=tx['from'], original_value_wei=str(int(tx['value'], 16)), supplied_gas_cap=int(tx['gas'], 16),
            response_abi=output, poster_gas_units=poster, component_base_fee_wei=base,
            parent_base_fee_estimate_wei=l1base, poster_component_wei=str(poster*base),
            full_operation_target_chain_estimate=False, caller_authority_or_funding_qualified=False))
    witness_call = next(row for row in fee_rows if row['request']['method'] == 'eth_call' and
                        row['request']['params'][0].get('data', '').startswith('0xc94e6eeb'))
    require(witness_call['request']['params'][1] == block, 'Component witness not hash pinned')
    output = witness_call['rpc_response']['result']
    total, poster, base, l1base = components(output, True)
    direct_estimate = int(response(receipt_rows, 'eth_estimateGas'), 16)
    witness = dict(response_abi=output, total_gas_units=total, poster_gas_units=poster,
        compute_gas_units=total-poster, component_base_fee_wei=base, parent_base_fee_estimate_wei=l1base,
        full_witness_estimated_fee_wei=str(total*base), poster_component_wei=str(poster*base),
        separately_captured_direct_estimate=direct_estimate, observed_estimates_equal=direct_estimate == total,
        scope='Actual approve(0) witness only, never a PoPL complete-operation estimate')
    receipts = []
    for phase, label in ((receipt_rows, 'positive_tip'), (zero_rows, 'zero_tip')):
        ordinary = [row['rpc_response']['result'] for row in phase if row['request']['method'] == 'eth_getTransactionByHash'
                    and row['rpc_response'].get('result', {}).get('type') == '0x2']
        require(len(ordinary) == 1, 'Ambiguous ordinary type2 receipt sample')
        tx = ordinary[0]
        receipt = response(phase, 'eth_getTransactionReceipt')
        true_header = response(phase, 'eth_getBlockByNumber', [tx['blockNumber'], False])
        require(tx['blockHash'] == receipt['blockHash'] == true_header['hash'] == anchor['hash'], 'Ordinary sample is not in the exact fee anchor')
        require(tx['hash'] == receipt['transactionHash'] and tx['transactionIndex'] == receipt['transactionIndex'], 'Ordinary inclusion identity differs')
        require(tx['type'] == '0x2' and int(tx['chainId'], 16) == 4663, 'Wrong ordinary transaction profile')
        gas, observed, inclusion_base = int(receipt['gasUsed'], 16), int(receipt['effectiveGasPrice'], 16), int(true_header['baseFeePerGas'], 16)
        derived = execution_price(tx, true_header, receipt)
        require(collect == 0 and observed == inclusion_base, 'Actual sample does not show base-only charging')
        receipts.append(dict(sample=label, transaction_hash=tx['hash'], signed_priority_wei=int(tx['maxPriorityFeePerGas'], 16),
            signed_maximum_fee_wei=int(tx['maxFeePerGas'], 16), inclusion_base_fee_wei=inclusion_base,
            reported_effective_price_wei=observed, existing_ethereum_helper_price_wei=derived,
            gas_used=gas, included_poster_gas_units=int(receipt['gasUsedForL1'], 16),
            receipt_accounted_fee_wei=str(gas*observed), existing_helper_accounted_fee_wei=str(gas*derived),
            existing_helper_overstatement_wei=str(gas*(derived-observed)), existing_helper_matches_receipt=derived == observed,
            scope='Actual public non-PoPL receipt; original fields unchanged; no native balance-debit or full PoPL-operation proof'))
    require(receipts[0]['signed_priority_wei'] > 0 and not receipts[0]['existing_helper_matches_receipt'], 'Missing genuine baseline discrepancy')
    require(receipts[1]['signed_priority_wei'] == 0 and receipts[1]['existing_helper_matches_receipt'], 'Missing genuine zero-tip witness')
    cast = read(HERE/'CAST_UNSIGNED.json')
    require(cast['exit_code'] == 0 and not cast['stderr'], 'Unsigned builder failed')
    raw = bytes.fromhex(cast['stdout'].removeprefix('0x'))
    require(raw[0] == 2, 'Builder did not choose type2')
    fields, end = decode_rlp(raw, 1)
    require(end == len(raw) and len(fields) == 9 and fields[8] == [], 'Not an unsigned type2 envelope')
    numeric = [int.from_bytes(fields[i], 'big') for i in (0, 1, 2, 3, 4, 6)]
    require(numeric == [4663, 7, 0, 20106000, 24000000, 0], 'Unsigned envelope fee/chain fields differ')
    source = read(ROOT/cast['source_fixture'])['transaction']
    require(fields[5].hex() == source['to'][2:] and fields[7].hex() == source['data'][2:], 'Unsigned payload changed')
    price = int(response(fee_rows, 'eth_gasPrice', []), 16)
    return dict(schema=1, baseline='0330a98a0be91c979fcba291258eb6019e528b1f',
        scope='Frozen read-only primary-source/fee interpretation; no chain, signer, service or policy adoption',
        network_transcript_sha256=sha(rpc_file.read_bytes()), anchor=anchor,
        client_version=response(receipt_rows, 'web3_clientVersion', []), arb_sys_version_raw=raw_version,
        internal_arbos_version=raw_version-55, version_normalization='ArbSys getter adds55 in upstream Nitro', collect_tips=bool(collect),
        header_inclusion_base_fee_wei=int(header['baseFeePerGas'], 16), gas_price_unpinned_wei=price,
        suggested_priority_unpinned_wei=int(response(fee_rows, 'eth_maxPriorityFeePerGas', []), 16),
        poster_component_cases=cases, approval_component_witness=witness,
        ordinary_receipt_reconciliation=receipts,
        unsigned_cast=dict(type=2, chain_id=numeric[0], nonce=numeric[1], priority_wei=numeric[2], max_fee_per_gas_wei=numeric[3],
            gas_limit=numeric[4], value_wei=numeric[5], unsigned_bytes_sha256=sha(raw), signature_fields=0,
            public_network=False, signing_or_wallet_use=False, scope='Installed keyless builder only; not send/sign/nonce/provider approval'),
        conditional_budget_examples=[dict(gas_cap=cap, sampled_price_wei=price, product_wei=str(cap*price),
            scope='Arithmetic at a dated unpinned quote, not a full-operation estimate or approved ceiling') for cap in (20000000, 24000000)],
        complete_popl_target_fee_quote=False, operator_fee_ceilings_approved=False, defaults_or_profile_adoption=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit', action='store_true', help='Create this report-local deterministic result')
    args = parser.parse_args()
    if not args.emit:
        for entry in read(HERE/'ARTIFACTS.json')['files']:
            require(sha((HERE/entry['path']).read_bytes()) == entry['sha256'], 'Fee evidence artifact changed')
        focused = read(HERE/'KEEPER_FOCUSED.json')
        require(focused['successful'] and focused['tests_run'] == 14 and focused['old_methods_executed'] == 0, 'Focused verification did not pass')
        require(focused['source_sha256_before'] == focused['source_sha256_after'], 'Focused sources changed during execution')
        require(len(set(focused['executed_methods'])) == 14 and focused['executed_methods'] == focused['selected_methods'], 'Unexpected test execution scope')
        for name, digest in focused['source_sha256_after'].items():
            require(sha((ROOT/name).read_bytes()) == digest, 'Current source differs from focused verification')
    result = compute()
    if args.emit:
        (HERE/'RESULTS.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    else:
        require(result == read(HERE/'RESULTS.json'), 'Published fee interpretation differs from recorded bytes')
    print(json.dumps(dict(successful=True, poster_cases=len(result['poster_component_cases']),
        actual_receipts=len(result['ordinary_receipt_reconciliation']), unsigned_type=result['unsigned_cast']['type'],
        new_network_calls=0, new_evm_calls=0, full_operation_qualification=False)))


if __name__ == '__main__':
    main()
