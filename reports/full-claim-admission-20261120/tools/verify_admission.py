"""Independent offline verification of current full normal claim admission.

This reader never starts or contacts a node and has no signing/submission path.
Positive plan transcripts are replayed in their original order through the exact
normal Projection and Transactions classes. An uncaptured read is an error;
neither admission results nor EVM execution results are synthesized.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
import copy
import codecs
import gzip
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import lzma
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from frontend_api.service import Projection, ZERO
from frontend_api.transactions import Transactions, claim_calldata, _parse
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RemoteRPCError, RpcError, WorkLimit

LIMIT = 128 * 1024 * 1024
CAP = 12_000_000
SOURCE_PINS = {
    'frontend_api/service.py': 'af0e9f494721d11be4c027fdc15dc4bb6c40583eaa87e06cc704b035c6c2a1b9',
    'frontend_api/portfolio_v6.py': '4f44737dcffeb7630bf52d6079c69519f0e7981dd72420b7fa41ee6803410c59',
    'frontend_api/portfolio_v7.py': '28ae93df6983be4fc37267cdfadcb276d28486689840c84dd9efcf74f75b6e99',
    'frontend_api/lifecycle.py': '1ac10191bbc0002e81fd00108512ee4844af9db2e96cef7dc462a1484b7c2235',
    'frontend_api/transactions.py': '6fa618e58186b9bbcb7bbd2549733d973e52e733e312eefc2abfe45c4cacab8e',
    'frontend_api/transaction_gas.py': '35f5c2221726e8987bb1ad28a9e62034ee65a51e2696dd382d66a800c2a13d9b',
    'frontend_api/claim_planner.py': '6d5241d61e5d48a6b2d77f10d09114426ad8a33fc7dddf47d2ec804b48136d5f',
    'frontend_api/royalty_reporting.py': '94985af003bd51ebd5435ea3fa43b99464483b2357e410e6b3cabaa266e4f1c3',
    'zzz_ops/work_budget.py': 'd60de944ee02fc8be02cdbdde0210c84fff02dea8bb63b386cc73688061a535b',
    'zzz_ops/abi.py': '154d92685b6e473bd064880ec15a16a9b8aafa0b9104df671538cf1375a7250d',
    'zzz_ops/rpc.py': '6b76610b1bc042196198657e069b30ef1009aff3237d71979e8d21495fb6380f',
    'zzz_ops/errors.py': '1dcc2855b45af8f806835f70f7f75200aa5b93ef84ddcf862e1e0f067aba5305',
}
READ_METHODS = frozenset(('eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber',
    'eth_getBlockByHash', 'eth_getCode', 'eth_getBalance', 'eth_call',
    'eth_estimateGas', 'eth_gasPrice'))
CLAIMED = '0x' + keccak256(b'Claimed(uint256,address,address,uint256)').hex()
CONSTRUCTOR_CHECKER_SHA = 'fc3bb047ae882ce22639937acc9e589d5513b0e0db28941ac762081cddae439d'
DEPLOYMENT_PLAN_SHA = '1cc30fa06a8c509e2a7e56d9c5d8af4fab469aa2457e545a7366376c4ab93965'
BUILD_PROFILE = 'activation-final-six-20261118'
ORIGINAL_WIRE_GZIP_SHA = 'c5839ee2301e6107b7e5ab2a964919c385ea89566db47cd89ddc7db19a150001'
ORIGINAL_WIRE_EXPANDED_SHA = 'c80a0ab40130adeead4668d3909e87febb4d529ff6b58f856a76a53d3e7595ff'
ALIASES = {'royalties': 'royalty_rewards', 'handoff': 'canonical',
           'principal_exit': 'migration', 'budget': 'migration_budget'}
NATIVE_PINS = {
    'pool_manager': '0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626',
    'position_manager': '0xc873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2',
    'state_view': '0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6',
    'permit2': '0x5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca',
    'zzz': '0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597',
}
OLD_PLANNER_SHA = SOURCE_PINS['frontend_api/claim_planner.py']
NEW_PLANNER_SHA = '7a3e720b97acf38e2ebfc7f4dde7a5912852a3eabd0a39629546aa1097cab810'
_planner_source = ContextVar('full_admission_reviewed_planner_source', default=None)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def loads(raw):
    require(len(raw) <= LIMIT, 'Evidence exceeds expanded bound')
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False, 'Nonfinite JSON'))


def load(path):
    path = Path(path)
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT, 'Evidence exceeds compressed bound')
    if path.suffix == '.gz':
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            raw = stream.read(LIMIT + 1)
    return loads(raw)


def file_sha(path, maximum):
    value, size = hashlib.sha256(), 0
    with Path(path).open('rb') as stream:
        while raw := stream.read(1024 * 1024):
            size += len(raw)
            require(size <= maximum, 'Streaming original compressed bound exceeded')
            value.update(raw)
    return value.hexdigest(), size


def stream_wire(path, records, construction_wire):
    """Read the large immutable original without enlarging the JSON-object bound.

    The owned transport caps each response at64MiB and the campaign at100000
    records. Repeated guard bytecode is checked/skipped in the stream, never
    loaded as one multi-gigabyte JSON object. Every normal plan range is kept.
    Construction's separate bounded prefix must equal the original prefix.
    """
    path = Path(path)
    stat = path.stat()
    require(stat.st_size <= 512 * 1024 * 1024, 'Original wire compressed bound exceeded')
    compressed_sha, compressed_bytes = file_sha(path, 512 * 1024 * 1024)
    ranges = [(record['fixture_wire_start'], record['fixture_wire_end']) for record in records]
    require(all(type(a) is int and type(b) is int and 0 <= a < b <= 100000 for a, b in ranges),
            'Invalid requested original-wire range')
    keep_methods = READ_METHODS - {'eth_getCode'} | frozenset((
        'eth_sendTransaction', 'eth_getTransactionReceipt', 'eth_getTransactionByHash', 'debug_traceTransaction'))
    decoder = json.JSONDecoder(object_pairs_hook=pairs,
        parse_constant=lambda _: require(False, 'Nonfinite original wire JSON'))
    utf8 = codecs.getincrementaldecoder('utf-8')()
    selected, expanded_sha, expanded_bytes, index, kept_bytes = [], hashlib.sha256(), 0, 0, 0
    buffer, eof, first, started, ended = '', False, True, False, False
    opener = lzma.open if path.suffix == '.xz' else gzip.open
    with opener(path, 'rb') as stream:
        def more():
            nonlocal buffer, eof, expanded_bytes
            raw = stream.read(256 * 1024)
            if not raw:
                eof = True
                buffer += utf8.decode(b'', final=True)
                return
            expanded_bytes += len(raw)
            require(expanded_bytes <= 16 * 1024 * 1024 * 1024, 'Streaming original expanded bound exceeded')
            expanded_sha.update(raw)
            buffer += utf8.decode(raw)
        while not ended:
            buffer = buffer.lstrip()
            if not buffer:
                require(not eof, 'Truncated original wire array')
                more()
                continue
            if not started:
                require(buffer[0] == '[', 'Original wire is not an array')
                buffer, started = buffer[1:], True
                continue
            if buffer[0] == ']':
                require(not first and index > 0, 'Empty/trailing-comma original wire inventory')
                buffer, ended = buffer[1:], True
                break
            if not first:
                require(buffer[0] == ',', 'Missing original wire array separator')
                buffer = buffer[1:].lstrip()
                first = True
                if not buffer:
                    require(not eof, 'Truncated original wire record')
                    more()
                    continue
            try:
                row, finish = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                require(not eof and len(buffer) <= 65 * 1024 * 1024, 'Malformed/oversized original wire record')
                more()
                continue
            require(finish <= 65 * 1024 * 1024 and type(row) is dict and index < 100000,
                    'Original wire row/count bound exceeded')
            if index < len(construction_wire):
                require(row == construction_wire[index], 'Separate construction prefix differs from original wire')
            request = row.get('request')
            require(type(request) is dict and request.get('id') == index + 1 and
                    row.get('response', {}).get('id') == index + 1, 'Original wire request IDs are not ordered')
            if request.get('method') in keep_methods or any(a <= index < b for a, b in ranges):
                kept_bytes += len(canonical(row).encode())
                require(kept_bytes <= LIMIT, 'Selected original wire exceeds bounded JSON inventory')
                selected.append({**row, 'original_index': index})
            buffer = buffer[finish:]
            first, index = False, index + 1
        while not eof:
            more()
        require(not buffer.strip(), 'Unexpected data after original wire array')
    require(index >= len(construction_wire) and all(b <= index for _, b in ranges),
            'Original wire is shorter than a bound capture range')
    after = path.stat()
    require((stat.st_size, stat.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Original wire changed during streaming')
    return flatten_wire(selected), {'compressed_sha256': compressed_sha, 'compressed_bytes': compressed_bytes,
        'compression': 'xz' if path.suffix == '.xz' else 'gzip',
        'expanded_sha256': expanded_sha.hexdigest(), 'expanded_bytes': expanded_bytes,
        'original_records': index, 'selected_records': len(selected), 'selected_json_bytes': kept_bytes,
        'construction_prefix_exact': True, 'all_normal_request_ranges_retained': True,
        'scope': 'Original fully streamed; omitted repeated nonrequest guard-code responses only from selected in-memory view'}


def quantity(value):
    require(type(value) is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})', value),
            'Noncanonical hexadecimal quantity')
    return int(value, 16)


def address(value):
    require(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{40}', value), 'Invalid address')
    return value.lower()


def digest(value):
    require(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{64}', value), 'Invalid hash')
    return value.lower()


def words(raw):
    require(type(raw) is str and re.fullmatch(r'0x(?:[0-9a-fA-F]{64})*', raw), 'Invalid ABI words')
    return [int(raw[i:i + 64], 16) for i in range(2, len(raw), 64)]


def check_sources(record=None):
    pins = dict(SOURCE_PINS)
    stage = _planner_source.get()
    if stage is not None:
        pins['frontend_api/claim_planner.py'] = stage[1]
    for name, expected in pins.items():
        path = stage[0] if stage is not None and name == 'frontend_api/claim_planner.py' else ROOT / name
        with path.open('rb') as stream:
            raw = stream.read(LIMIT + 1)
        require(len(raw) <= LIMIT and sha(raw) == expected, 'Unreviewed current source: ' + name)
        if record is not None:
            require(record.get(name) == expected, 'Captured source differs: ' + name)
    return pins


@contextmanager
def planner_stage(path, expected_sha):
    """Load only one of the two explicitly reviewed exact planner source stages.

    A retained old capture executes its authenticated old planner bytes. The
    unchanged normal service/transaction/profile code stays imported normally.
    This never overwrites production source or relabels an old result as new.
    """
    path = Path(path).resolve()
    require(expected_sha in (OLD_PLANNER_SHA, NEW_PLANNER_SHA) and
            sha(path.read_bytes()) == expected_sha, 'Unreviewed planner stage bytes')
    import frontend_api
    name = 'frontend_api.claim_planner'
    previous_module = sys.modules.get(name)
    previous_bytecode = sys.dont_write_bytecode
    had_attribute = hasattr(frontend_api, 'claim_planner')
    previous_attribute = getattr(frontend_api, 'claim_planner', None)
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    frontend_api.claim_planner = module
    token = _planner_source.set((path, expected_sha))
    try:
        sys.dont_write_bytecode = True
        loader.exec_module(module)
        check_sources()
        yield module
        check_sources()
    finally:
        sys.dont_write_bytecode = previous_bytecode
        _planner_source.reset(token)
        if previous_module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous_module
        if had_attribute:
            frontend_api.claim_planner = previous_attribute
        else:
            del frontend_api.claim_planner


def flatten_wire(rows):
    """Accept the two existing capture envelopes, preserving every observation."""
    require(type(rows) is list and len(rows) <= 100_000, 'Unbounded wire inventory')
    result = []
    for row in rows:
        require(type(row) is dict, 'Invalid wire row')
        requests = row.get('requests', [row.get('request')])
        responses = row.get('response')
        responses = responses if type(responses) is list else [responses]
        require(type(requests) is list and 1 <= len(requests) <= 1024 and
                len(responses) == len(requests), 'Mismatched wire batch')
        response_by_id = {}
        for response in responses:
            require(type(response) is dict and type(response.get('id')) is int and
                    response.get('jsonrpc') == '2.0' and
                    ('result' in response) != ('error' in response), 'Invalid RPC response')
            require(response['id'] not in response_by_id, 'Duplicate response ID')
            response_by_id[response['id']] = response
        request_ids = set()
        for request in requests:
            require(type(request) is dict and type(request.get('id')) is int and
                    request.get('jsonrpc') == '2.0' and type(request.get('params')) is list and
                    type(request.get('method')) is str, 'Invalid RPC request')
            require(request['id'] not in request_ids and request['id'] in response_by_id,
                    'Duplicate or unmatched request ID')
            request_ids.add(request['id'])
            result.append({'request': request, 'response': response_by_id[request['id']],
                **{key: value for key, value in row.items() if key not in ('request', 'requests', 'response')}})
    return result


class ExactReplay:
    """Replay an ordered positive transcript; no network or result fallback."""
    def __init__(self, rows, *, negative=False):
        self.rows = flatten_wire(rows)
        self.cursor = 0
        require(0 < len(self.rows) <= 1024, 'Positive request exceeds logical RPC bound')
        for row in self.rows:
            require(row['request']['method'] in READ_METHODS, 'Unsigned API used a nonread method')
            if not negative:
                require(not row.get('interception') and not row.get('interception_label') and
                        not row.get('explicit_negative_interception') and
                        'upstream_response' not in row, 'Positive evidence contains an injected response')

    def call(self, method, params=None):
        require(self.cursor < len(self.rows), 'Normal API requested an uncaptured RPC')
        row = self.rows[self.cursor]
        request, response = row['request'], row['response']
        require(request['method'] == method and request['params'] == (params or []),
                'Normal API RPC order/parameters differ at ' + str(self.cursor))
        self.cursor += 1
        if 'error' in response:
            error = response['error']
            require(type(error) is dict and type(error.get('code')) is int, 'Invalid raw RPC error')
            code = error['code']
            reason = {-32602: 'invalid_params', -32005: 'rate_limited'}.get(code, 'unclassified')
            raise RemoteRPCError(method, code, reason)
        value = response['result']
        if method == 'eth_chainId':
            value = quantity(value) if type(value) is str else value
            require(type(value) is int and value > 0, 'Invalid delivered chain identity')
        if 'delivered_result' in row:
            require(method == 'eth_chainId' and row['delivered_result'] == value,
                    'Unexpected response normalization')
        return copy.deepcopy(value)

    def finish(self):
        require(self.cursor == len(self.rows), 'Captured positive RPC reads were omitted by replay')


def check_configuration(config, transaction_config, fixture=None):
    require(config.get('schema') == 2 and config.get('accounting_version') == 7 and
            config.get('custody_version') == 5 and config.get('mint_integration_version') == 2 and
            config.get('execution_price_version') == 1 and config.get('fee_intake_version') == 1 and
            config.get('protocol_policy_version') == 1 and
            config.get('royalty_reporting') == {'schema': 5, 'converter': None},
            'Read configuration is not the explicit current normal profile')
    require(type(config.get('contracts')) is dict and len(config['contracts']) == 26,
            'Current normal API requires exactly26 contract pins')
    require(transaction_config.get('schema') == 2 and
            transaction_config.get('chain_id') == config.get('chain_id') and
            transaction_config.get('fee_policy', {}).get('max_gas_limit') == str(CAP) and
            transaction_config['fee_policy'].get('estimate_includes_all_fees') is True,
            'Transaction policy lacks the unchanged12M/full20% reviewed boundary')
    if fixture is not None:
        require(config['chain_id'] == fixture['chain_id'] and
                config['deployment_block'] == fixture['deployment_block'] and
                config['deployment_block_hash'] == fixture['deployment_block_hash'],
                'Projection anchor differs from actual fixture')
        pins = fixture['expected_runtime_pins']
        for role, item in config['contracts'].items():
            require(pins.get(role) == item['code_hash'], 'Projection runtime differs from constructor proof: ' + role)
            require(fixture['contracts'].get(role) == item['address'], 'Projection address differs from actual fixture: ' + role)


def check_plan_result(payload, plan):
    require(plan.get('kind') == 'unsigned_claim_plan' and plan.get('schema') == 2 and
            plan.get('automatic_submission') is False and plan.get('production_approved') is False,
            'Result is not an unsigned policy2 plan')
    original = payload['claims']
    entries = plan['entries']
    require(len(original) == len(entries) <= 32 and all(
        entry['selection_index'] == index and all(entry[key] == selected[key]
            for key in ('token_id', 'asset', 'royalty'))
        for index, (selected, entry) in enumerate(zip(original, entries))),
        'Planner lost/reordered/changed an explicit selection')
    require(plan['wallet'] == payload['wallet'], 'Plan caller differs')
    planning = plan['planning']
    require(planning['maximum_selection'] == 32 and planning['maximum_trials'] == 10 and
            0 <= planning['trial_count'] <= 10 and
            planning['trial_count'] == len(planning['attempts']) and
            planning['simulation_gas_cap'] == str(CAP), 'Planner changed work/gas bounds')
    unresolved = [row for row in entries if row['status'] not in ('zero', 'in_next_batch')]
    require([row['selection_index'] for row in unresolved] ==
            [row['selection_index'] for row in plan['remaining_claims']], 'An unresolved selection disappeared')
    draft = plan['next_batch']
    require(planning['final_batch_revalidated'] is (draft is not None), 'Final preparation flag differs')
    if draft is None:
        require(not any(row['status'] == 'in_next_batch' for row in entries), 'Selected rows lack a draft')
        return {'entries': len(entries), 'published': 0, 'trials': planning['trial_count']}
    selected = [row for row in entries if row['status'] == 'in_next_batch']
    operations = draft['claim_operations']
    require(len(selected) == len(operations) > 0 and all(all(a[key] == b[key]
            for key in ('token_id', 'asset', 'royalty')) for a, b in zip(selected, operations)),
            'Published claim operations differ from classified entries')
    gas = draft['network_gas']
    estimate, padded = int(gas['estimated_units']), int(gas['suggested_limit'])
    require(padded == (estimate * 120 + 99) // 100 <= CAP and
            gas['configured_gas_limit'] == gas['effective_gas_limit'] == str(CAP) and
            gas['full_twenty_percent_headroom'] is True, 'Claim estimate lacks full20% headroom')
    tx = draft['transaction']
    require(set(tx) == {'from', 'to', 'data', 'value', 'chainId'} and
            tx['from'] == payload['wallet'] and tx['value'] == '0x0', 'Unsigned transaction envelope differs')
    _, _, claims = _parse({'action': 'claim', 'wallet': payload['wallet'],
        'claims': [{key: row[key] for key in ('token_id', 'asset', 'royalty')} for row in operations]})
    require(tx['data'] == claim_calldata(claims), 'Draft calldata differs from exact typed selection')
    return {'entries': len(entries), 'published': len(operations), 'trials': planning['trial_count'],
            'estimate': estimate, 'padded': padded}


def check_plan(record, config, transaction_config, wire):
    require(type(record.get('elapsed_seconds')) in (int, float) and
            0 <= record['elapsed_seconds'] < 25, 'Positive actual request exceeded25seconds')
    check_sources(record['production_source_sha256'])
    check_sources(record['production_source_sha256_after'])
    require(record.get('normal_deployment_admission_replaced') is False and
            record.get('projection_class') == 'frontend_api.service.Projection' and
            record.get('deployment_verifier') == 'frontend_api.service.Projection._verify_deployment' and
            record.get('explicit_negative_control') is None and record.get('interception_matches') == 0,
            'Positive admission used a replacement or negative interception')
    require(all(record.get(key) == value for key, value in
            {'logical_rpc_limit': 1024, 'request_seconds_limit': 25, 'http_post_limit': 2048,
             'maximum_selection': 32, 'maximum_trials': 10, 'claim_gas_limit': CAP,
             'claim_padding_percent': 20}.items()), 'Captured API limits changed')
    replay = ExactReplay(wire)
    counts = dict(Counter(row['request']['method'] for row in replay.rows))
    require(record['rpc_count'] == len(replay.rows) <= 1024 and record['rpc_counts'] == counts,
            'Captured logical RPC count differs')
    stamp = record['projection_clock_timestamp']
    require(type(stamp) is int and stamp > 0, 'Missing captured fixture clock')
    p = Projection(copy.deepcopy(config), rpc=replay, clock=lambda: stamp)
    require(type(p) is Projection and p._verify_deployment.__func__ is Projection._verify_deployment,
            'Normal deployment admission was replaced')
    prepared = Transactions(p, copy.deepcopy(transaction_config))
    started = time.monotonic()
    actual = prepared.plan_claims(copy.deepcopy(record['payload']))
    elapsed = time.monotonic() - started
    replay.finish()
    require(actual == record['result'], 'Independent normal API replay result differs')
    result = check_plan_result(record['payload'], actual)
    result.update(label=record['label'], rpc_reads=len(replay.rows),
                  captured_seconds=record['elapsed_seconds'], replay_seconds=elapsed)
    return result


def check_refusal(record, config, transaction_config, wire):
    """Keep injected faults separate; only replayable refusal claims are closed."""
    check_sources(record['production_source_sha256'])
    check_sources(record['production_source_sha256_after'])
    require('result' not in record and type(record.get('error')) is dict,
            'Negative record published a result')
    require(record.get('normal_deployment_admission_replaced') is False and
            record.get('projection_class') == 'frontend_api.service.Projection' and
            record.get('deployment_verifier') == 'frontend_api.service.Projection._verify_deployment',
            'Negative admission used a replacement Projection')
    replay = ExactReplay(wire, negative=True)
    require(record['rpc_count'] == len(replay.rows) and record['rpc_counts'] ==
            dict(Counter(row['request']['method'] for row in replay.rows)), 'Refusal RPC count differs')
    intercepted = [row for row in replay.rows if row.get('explicit_negative_interception')]
    require(len(intercepted) == record.get('interception_matches'), 'Refusal interception count differs')
    if intercepted:
        description = record.get('explicit_negative_control')
        require(type(description) is dict and description.get('kind') == 'explicit_intercepted_scalar_negative'
                and description.get('upstream_real_response_retained') is True,
                'Intercepted fault lacks explicit original-response scope')
        wanted = {'to': description['target'], 'data': calldata(description['signature'])}
        matching = [row for row in replay.rows if row['request']['method'] == 'eth_call'
                    and row['request']['params'][0] == wanted]
        occurrence = description['occurrence']
        require(type(occurrence) is int and 1 <= occurrence <= len(matching) and
                len(intercepted) == 1 and matching[occurrence - 1] is intercepted[0],
                'Injected fault changed the wrong normal read occurrence')
        require(intercepted[0]['response']['result'] == description['replacement'] and
                type(intercepted[0].get('upstream_response')) is dict and
                'result' in intercepted[0]['upstream_response'], 'Injected response differs from declared fault')
    expected = record['error']
    # A captured deadline is retained honestly; a quicker offline replay cannot
    # independently reproduce network elapsed time, and is never called a pass.
    if expected == {'type': 'WorkLimit', 'reason': 'deadline'}:
        require(record['elapsed_seconds'] >= 25, 'Deadline record lacks elapsed deadline')
        return {'label': record['label'], 'error': expected, 'replayed': False,
                'scope': 'Retained actual elapsed refusal; no successful admission claimed'}
    stamp = record['projection_clock_timestamp']
    p = Projection(copy.deepcopy(config), rpc=replay, clock=lambda: stamp)
    try:
        Transactions(p, copy.deepcopy(transaction_config)).plan_claims(copy.deepcopy(record['payload']))
    except (RpcError, ValueError) as error:
        actual = {'type': type(error).__name__}
        if isinstance(error, WorkLimit):
            actual['reason'] = error.reason
        elif isinstance(error, RemoteRPCError):
            actual.update(method=error.method, code=error.code, reason=error.reason)
        require(actual == expected, 'Independent normal refusal type/reason differs')
    else:
        raise ValueError('Negative normal admission unexpectedly published a plan')
    replay.finish()
    return {'label': record['label'], 'error': expected, 'replayed': True,
            'rpc_reads': len(replay.rows), 'explicit_interceptions': len(intercepted)}


def wire_result(wire, method, params, expected):
    require(any(row['request']['method'] == method and row['request']['params'] == params and
                row['response'].get('result') == expected for row in wire),
            'Observation has no exact original wire response: ' + method)


def bind_plan_to_original(rows, original, start=0):
    """Cross-bind adapter captures to the separately recorded actual node wire."""
    for observed in flatten_wire(rows):
        delivered = observed['response']
        response = observed.get('upstream_response', delivered)
        request = observed['request']
        def matches(row):
            other, reply = row['request'], row['response']
            if other['method'] != request['method'] or other['params'] != request['params']:
                return False
            if 'result' in response:
                return reply.get('result') == response['result'] and 'error' not in reply
            return ('error' in reply and reply['error'].get('code') == response['error'].get('code'))
        while start < len(original) and not matches(original[start]):
            start += 1
        require(start < len(original), 'Adapter observation absent/out of order in original node capture')
        start += 1
    return start


def constructor_reader():
    path = ROOT / 'scripts/check-local-deployment-evidence.py'
    require(sha(path.read_bytes()) == CONSTRUCTOR_CHECKER_SHA and
            sha((ROOT / 'zzz_ops/deployment_plan.py').read_bytes()) == DEPLOYMENT_PLAN_SHA,
            'Unreviewed constructor-check helper source')
    spec = importlib.util.spec_from_file_location('full_admission_constructor_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_construction(folder, manifest):
    """Reuse exact constructor arithmetic, without pretending the launcher is old.

    The campaign has a new native-genesis transport. The historical whole-run
    checker requires its original launcher layout, so only its reviewed pure
    encoding/binding helpers are used here; actual traces and wire are reread.
    """
    folder = Path(folder)
    helper = constructor_reader()
    from zzz_ops.deployment_plan import Artifacts
    artifacts = Artifacts(build_profile=BUILD_PROFILE)
    build = helper.trusted_build(BUILD_PROFILE)
    build_dir = ROOT / build['directory']
    for name, expected in build['files'].items():
        require(sha((build_dir / name).read_bytes()) == expected, 'Trusted normal build artifact changed')
    compiler = artifacts.output
    ledger = bytes.fromhex(compiler['contracts']['src/ZZZRoyaltyRewards.sol']
        ['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
    actual_input = load(folder / 'actual-address-input.json')
    require(helper.validate(actual_input) == actual_input, 'Construction inputs are invalid')
    instances = load(folder / 'instances.json')
    require(type(instances) is list and len(instances) == 39, 'Wrong actual constructor inventory')
    by_role = {row['role']: row for row in instances}
    addresses = {role: row['address'] for role, row in by_role.items()}
    specs = helper.constructor_specifications()
    require(set(by_role) == set(specs) and len(set(addresses.values())) == 39,
            'Constructed graph differs from exact39 roles')
    wire = flatten_wire(load(folder / 'construction-rpc-records.json.gz'))
    receipts = {row['response']['result']['transactionHash']: row['response']['result']
        for row in wire if row['request']['method'] == 'eth_getTransactionReceipt'
        and row['response'].get('result')}
    sent = {row['response']['result']: row['request']['params'][0]
        for row in wire if row['request']['method'] == 'eth_sendTransaction'
        and 'result' in row['response']}
    require(len(sent) == 44, 'Construction prefix does not contain exactly44 sends')
    frames, transactions = {}, []
    for number in range(1, 45):
        files = list(folder.glob(f'{number:02d}-*.json'))
        require(len(files) == 1, 'Missing/ambiguous construction transaction record')
        row = load(files[0])
        tx, receipt = row['transaction'], row['receipt']
        require(receipt == receipts.get(tx['hash']) and receipt['transactionHash'] == tx['hash']
                and quantity(receipt['status']) == 1, 'Construction receipt absent/different on original wire')
        require(tx['hash'] in sent, 'Construction transaction absent from original send')
        helper.check_submission(sent[tx['hash']], tx,
            None if row['label'].startswith('create:') else address(tx['to']))
        wire_result(wire, 'eth_getTransactionByHash', [tx['hash']], tx)
        estimate, padded = row['estimated_gas'], row['padded_gas']
        require(type(estimate) is int and padded == (estimate * 12500 + 9999) // 10000
                == quantity(tx['gas']) <= 32_000_000 and quantity(receipt['gasUsed']) <= padded,
                'Construction lost full25% estimate headroom')
        transactions.append(row)
        if not row['label'].startswith('create:'):
            continue
        trace_path = files[0].with_name(files[0].stem + '-trace.json.gz')
        trace_raw = trace_path.read_bytes()
        with gzip.GzipFile(fileobj=io.BytesIO(trace_raw)) as stream:
            raw = stream.read(LIMIT + 1)
        trace = loads(raw)
        trace_sha = sha(raw)
        wire_result(wire, 'debug_traceTransaction', [tx['hash'], {'tracer': 'callTracer'}], trace)
        def walk(frame):
            require(not frame.get('error'), 'Construction CREATE trace reverted')
            if frame.get('type') == 'CREATE':
                target = address(frame['to'])
                require(target not in frames, 'Duplicate actual CREATE target')
                frames[target] = (frame, trace_sha)
            for child in frame.get('calls', []):
                walk(child)
        walk(trace)
    require(set(frames) == set(addresses.values()), 'Actual CREATE trace graph differs from39instances')
    for role, instance in by_role.items():
        name, mode, parent, refs = specs[role]
        require(instance['contract'] == name, 'Constructor role contract differs')
        contract = compiler['contracts']['src/' + name + '.sol'][name]
        abi = next((row['inputs'] for row in contract['abi'] if row['type'] == 'constructor'), [])
        types = tuple(item['type'] for item in abi)
        require(types == helper.TYPES[name], 'Trusted constructor ABI differs')
        values = helper.constructor_values(refs, actual_input, addresses, ledger, True)
        expected = '0x' + contract['evm']['bytecode']['object'] + helper.encoded(types, values).hex()
        frame, trace_sha = frames[instance['address']]
        proof = instance['create_proof']
        creator = actual_input['inputs']['governance'] if mode == 'top_level' else addresses[parent]
        require(frame['input'].lower() == expected.lower() == instance['full_initcode_hex'].lower()
                == proof['input'].lower() and frame['from'].lower() == creator == proof['creator']
                and trace_sha == proof['trace_sha256'], 'Normal creation input/parent/source proof differs')
        runtime = bytes.fromhex(frame['output'][2:])
        runtime_pin = '0x' + keccak256(runtime).hex()
        require(frame['output'].lower() == proof['output'] and len(runtime) == instance['runtime_bytes'] <= 24576
                and len(bytes.fromhex(expected[2:])) <= 49152 and sha(runtime) == instance['runtime_sha256']
                and runtime_pin == instance['runtime_keccak256'], 'Actual normal runtime proof differs')
        require(any(row['request']['method'] == 'eth_getCode' and
                    address(row['request']['params'][0]) == instance['address'] and
                    row['response'].get('result') == frame['output'] for row in wire),
                    'Constructed runtime not observed on original wire')
        if name == 'ZZZRoyaltyCodeData':
            helper.check_carrier_runtime(role, ledger, frame['output'], frame['output'])
    bindings = load(folder / 'bindings.json')
    helper.check_bindings(bindings, wire, addresses, actual_input['inputs'], ledger)
    for role, target in manifest['contracts'].items():
        actual_role = ALIASES.get(role, role)
        if actual_role in by_role:
            require(target == addresses[actual_role] and
                    manifest['expected_runtime_pins'].get(role) == by_role[actual_role]['runtime_keccak256'],
                    'Admitted API manifest is not tied to actual normal construction: ' + role)
    return {'instances': 39, 'transactions': 44, 'binding_observations': len(bindings),
            'unchanged_compiler_source_pins': len(artifacts.source_pins),
            'build_profile': BUILD_PROFILE, 'runtime_pins':
                {role: row['runtime_keccak256'] for role, row in by_role.items()}}


def amount(value):
    if type(value) is int:
        require(0 <= value < 1 << 256, 'Amount outside uint256')
        return value
    require(type(value) is str and re.fullmatch(r'0|[1-9][0-9]{0,77}', value),
            'Amount is not a canonical decimal integer')
    value = int(value)
    require(value < 1 << 256, 'Amount outside uint256')
    return value


def check_header(header, wire):
    require(type(header) is dict, 'Missing captured canonical header')
    digest(header['hash'])
    quantity(header['number'])
    quantity(header['timestamp'])
    require(any(row['request']['method'] in ('eth_getBlockByNumber', 'eth_getBlockByHash') and
                row['response'].get('result') == header for row in wire),
                'Canonical header absent/different on original wire')
    return {'blockHash': header['hash'], 'requireCanonical': True}


def claim_read(config, owner, row, block, wire):
    token, asset, royalty = row['token_id'], row['asset'], row['royalty']
    target = config['contracts']['royalties' if royalty else 'rewards']['address']
    # Native zero is encoded explicitly; the generic ABI address helper rejects
    # zero targets, so it is not used to invent a native ERC20 address.
    data = '0x' + keccak256(b'claimable(uint256,address)').hex()[:8]
    data += f'{int(token):064x}{int(asset, 16):064x}'
    for key, value in (('read_target', target), ('read_data', data), ('read_block', block)):
        if key in row:
            require(row[key] == value, 'Claim read metadata differs from its exact derived identity')
    expected = '0x' + f'{amount(row["raw"]):064x}'
    wire_result(wire, 'eth_call', [{'to': target, 'data': data}, block], expected)
    return amount(row['raw'])


def snapshot_balances(snapshot, owner, assets, block, wire):
    balances = dict(snapshot.get('recipient_balances', {}))
    if ZERO not in balances and 'owner_native_balance' in snapshot:
        balances[ZERO] = snapshot['owner_native_balance']
    if 'owner_native_balance' in snapshot:
        require(amount(balances[ZERO]) == amount(snapshot['owner_native_balance']), 'Snapshot native-balance metadata disagrees')
    require(set(assets) <= set(balances), 'Snapshot omits a selected recipient currency')
    result = {}
    for asset in assets:
        value = amount(balances[asset])
        if asset == ZERO:
            wire_result(wire, 'eth_getBalance', [owner, block], hex(value))
        else:
            wire_result(wire, 'eth_call', [{'to': asset, 'data': calldata('balanceOf(address)', owner)}, block],
                        '0x' + f'{value:064x}')
        result[asset] = value
    return result


def check_execution(record, plans, wire):
    require(record['plan_label'] in plans, 'Claim execution lacks a verified positive plan')
    planned = plans[record['plan_label']]
    config, result = planned['projection_config'], planned['result']
    draft = result['next_batch']
    require(draft is not None, 'Actual claim execution refers to an empty plan')
    operation = record['transaction']
    submitted, tx, receipt = operation['submitted'], operation['transaction'], operation['receipt']
    unsigned = draft['transaction']
    require(all(submitted[key] == unsigned[key] for key in ('from', 'to', 'data', 'value')),
            'Actual submitted caller/target/calldata/value differs from unsigned plan')
    helper = constructor_reader()
    helper.check_submission(submitted, tx, unsigned['to'])
    wire_result(wire, 'eth_sendTransaction', [submitted], tx['hash'])
    wire_result(wire, 'eth_getTransactionByHash', [tx['hash']], tx)
    wire_result(wire, 'eth_getTransactionReceipt', [tx['hash']], receipt)
    require(receipt['transactionHash'] == tx['hash'] and quantity(receipt['status']) == 1,
            'Claim receipt is not an actual successful included transaction')
    estimate, padded = operation['estimate'], operation['padded_gas']
    require(operation['cap'] == CAP and operation['padding_bps'] == 2000 and
            padded == (estimate * 120 + 99) // 100 <= CAP and
            quantity(submitted['gas']) == quantity(tx['gas']) == padded and
            quantity(receipt['gasUsed']) <= padded,
            'Actual claim envelope lost12M/full20% admission')
    require(estimate == int(draft['network_gas']['estimated_units']) and
            padded == int(draft['network_gas']['suggested_limit']),
            'Actual claim revalidation estimate differs from published exact plan')
    # The report's sender revalidates locally with a fresh ordinary estimate;
    # this is distinct from the unsigned API's confirmed-block estimate.
    full = {key: submitted[key] for key in ('from', 'to', 'data', 'value')}
    full['gas'] = hex(CAP)
    wire_result(wire, 'eth_call', [full, 'latest'], operation['simulation_return'])
    wire_result(wire, 'eth_estimateGas', [full], hex(estimate))
    before, after = record['before'], record['after']
    before_block = check_header(before['header'], wire)
    after_block = check_header(after['header'], wire)
    require(receipt['blockHash'] == after['header']['hash'] and
            receipt['blockNumber'] == after['header']['number'] and
            quantity(after['header']['number']) == quantity(before['header']['number']) + 1 and
            after['header']['parentHash'] == before['header']['hash'],
            'Payout observations are not adjacent canonical receipt blocks')
    identity = lambda row: (str(row['token_id']), row['asset'], row['royalty'])
    entries = draft['claim_operations']
    require([identity(row) for row in before['claims']] == [identity(row) for row in entries] ==
            [identity(row) for row in after['claims']], 'Claim observation identities differ')
    owner = unsigned['from']
    require(before['owner'] == after['owner'] == owner, 'Payout snapshot names a different recipient')
    expected = [claim_read(config, owner, row, before_block, wire) for row in before['claims']]
    require(expected == [amount(row['simulated_raw']) for row in entries],
            'Actual preclaim units differ from final confirmed simulation')
    require(all(claim_read(config, owner, row, after_block, wire) == 0 for row in after['claims']),
            'Selected rights remain after a reported full claim')
    logs = [row for row in receipt['logs'] if row.get('topics', [])[:1] == [CLAIMED]]
    require(len(logs) == len(entries), 'Receipt lacks the exact count of claim events')
    paid = {}
    for entry, value, log in zip(entries, expected, logs):
        ledger = config['contracts']['royalties' if entry['royalty'] else 'rewards']['address']
        topics = log['topics']
        require(value > 0 and address(log['address']) == ledger and len(topics) == 4 and
                int(topics[1], 16) == int(entry['token_id']) and
                int(topics[2], 16) == int(entry['asset'], 16) and
                int(topics[3], 16) == int(owner, 16) and words(log['data']) == [value],
                'Actual claim event ledger/ID/currency/current-owner/amount differs')
        paid[entry['asset']] = paid.get(entry['asset'], 0) + value
    assets = set(paid) | {ZERO}
    b = snapshot_balances(before, owner, assets, before_block, wire)
    a = snapshot_balances(after, owner, assets, after_block, wire)
    price = receipt.get('effectiveGasPrice', tx['gasPrice'])
    fee = quantity(receipt['gasUsed']) * quantity(price)
    require(all(a[asset] - b[asset] + (fee if asset == ZERO else 0) == paid.get(asset, 0)
                for asset in assets), 'Actual recipient balance delta differs from exact receipt payouts')
    return {'label': record['label'], 'plan_label': record['plan_label'],
            'transaction_hash': tx['hash'], 'entries_paid': len(entries), 'paid_by_asset': paid,
            'estimate': estimate, 'padded': padded, 'gas_fee': fee}


def check_faults(qualification, plans, wire):
    cases = qualification.get('fault_cases', [])
    require(len(cases) == 1, 'Expected one explicitly scoped taxed-currency refusal case')
    record = cases[0]
    require(record['label'] == 'taxed-last-atomic-simulation-refusal' and record['plan_label'] in plans and
            record['before'] == record['after'], 'Opaque simulation refusal changed its captured selected snapshot')
    planned = plans[record['plan_label']]
    config, plan = planned['projection_config'], planned['result']
    owner = planned['payload']['wallet']
    before = record['before']
    block = check_header(before['header'], wire)
    require(before['owner'] == owner and len(before['claims']) == 2, 'Fault snapshot caller/selection differs')
    expected = [claim_read(config, owner, row, block, wire) for row in before['claims']]
    require(all(value > 0 for value in expected), 'Fault selection did not retain two funded rights')
    snapshot_balances(before, owner, {row['asset'] for row in before['claims']} | {ZERO}, block, wire)
    attempts = plan['planning']['attempts']
    require(len(attempts) == 2 and attempts[0] == {'outcome': 'unresolved',
        'reason': 'execution_refused_unclassified', 'selection_indices': [0, 1]} and
        attempts[1] == {'outcome': 'simulated', 'selection_indices': [0]},
        'Fault evidence relabeled the opaque mixed refusal or omitted fresh prefix preparation')
    entries = plan['entries']
    require(len(entries) == 2 and entries[0]['status'] == 'in_next_batch' and
            len(plan['remaining_claims']) == 1 and plan['remaining_claims'][0]['selection_index'] == 1 and
            plan['next_batch']['claim_operations'][0]['asset'] == before['claims'][0]['asset'],
            'Faulty last entry disappeared or was reported as paid')
    singles = [row for row in plans.values() if row['label'] == 'tax-only-remains-unavailable']
    require(len(singles) == 1, 'Missing fresh unavailable taxed-currency continuation')
    single = singles[0]['result']
    require(single['next_batch'] is None and len(single['entries']) == len(single['remaining_claims']) == 1 and
            single['entries'][0]['status'] == 'unavailable' and
            single['entries'][0]['reason'] == 'execution_refused_unclassified' and
            amount(single['entries'][0]['view_raw']) == expected[1],
            'Untransferable right was converted to zero or an executable draft')
    closing = qualification['closing_claims']
    closing_block = check_header(closing['header'], wire)
    require(closing['owner'] == owner and len(closing['claims']) == 2 and
            all(all(a[key] == b[key] for key in ('token_id', 'asset', 'royalty'))
                for a, b in zip(before['claims'], closing['claims'])), 'Closing right identities differ')
    require([claim_read(config, owner, row, closing_block, wire) for row in closing['claims']] == [0, expected[1]],
            'Healthy prefix did not drain exactly or unresolved taxed right changed')
    snapshot_balances(closing, owner, {row['asset'] for row in closing['claims']} | {ZERO}, closing_block, wire)
    return {'cases': 1, 'healthy_prefix_paid_once': True, 'unavailable_original_units_retained': expected[1],
        'scope': 'Exact selected-right/recipient snapshots and opaque read-only execution refusal; not a full global rollback snapshot'}


def check_fixture(folder, manifest, construction):
    require(manifest.get('schema') == 1 and manifest.get('normal_build') == BUILD_PROFILE and
            manifest.get('chain_id') == 4663 and manifest.get('production_approved') is False and
            manifest.get('public_requests') == 0 and manifest.get('compiler_run') is False,
            'Fixture changed its reviewed local-only source boundary')
    require(manifest.get('active_nfts') == manifest.get('actual_entry_activations') == 32 and
            manifest.get('royalty_currencies') == 65 and manifest.get('actual_normal_access_sealed') is True and
            manifest.get('no_protocol_storage_seeded') is True and manifest.get('no_prior_population_rerun') is True,
            'Fixture population/source claims differ')
    cleanup = load(folder / 'node/cleanup.json')
    process = load(folder / 'node/process.json')
    genesis = load(folder / 'node/genesis.json')
    require(cleanup.get('owned_node_stopped') is True and cleanup.get('pending_submission') is None and
            cleanup.get('failure_type') is None and cleanup.get('existing_nodes_contacted') is False,
            'Owned fixture did not stop cleanly')
    require(process.get('chain_id') == 4663 and process.get('minimal_environment') is True and
            process.get('size_limit_override') is False and process.get('public_rpc') is False and
            process.get('port') not in (8902, 57306), 'Fixture process boundary differs')
    command = process['command']
    require(command[command.index('--host') + 1] == '127.0.0.1' and
            command[command.index('--accounts') + 1] == '0' and
            command[command.index('--hardfork') + 1] == 'cancun' and
            command[command.index('--gas-limit') + 1] == '32000000', 'Fixture node flags differ')
    alloc = {address(key if key.startswith('0x') else '0x' + key): value
             for key, value in genesis['alloc'].items()}
    for role in construction['runtime_pins']:
        target = manifest['contracts'][role]
        before = alloc.get(target, {})
        require(not before.get('storage') and before.get('code', '0x') == '0x',
                'A PoPL construction target was seeded in genesis')
    native = load(folder / 'native-source.json')
    require(native.get('cache_sha256') == 'f6995f207531ee3b22ea6b76f2605075b889226fe0267e7549ca1f3fc9f069da' and
            native.get('no_cached_storage_inherited') is True and
            {row['role'] for row in native['native']} == set(NATIVE_PINS),
            'External native source provenance differs')
    for row in native['native']:
        role, target = row['role'], row['address']
        raw = bytes.fromhex(row['runtime_hex'][2:])
        require(row.get('inherited_storage_rows') == 0 and len(raw) == row['original_len'] and
                sha(raw) == row['runtime_sha256'] and
                '0x' + keccak256(raw).hex() == row['runtime_keccak256'] == NATIVE_PINS[role] and
                alloc[target]['code'] == row['runtime_hex'] and
                manifest['contracts'][role] == target and
                manifest['expected_runtime_pins'][role] == NATIVE_PINS[role],
                'Native genesis code differs from exact archived runtime')
    # These are explicit external fixture defaults, never a PoPL slot import.
    sender = manifest['owner']
    w = lambda n: '0x' + f'{n:064x}'
    short = lambda value: '0x' + (value.encode() + bytes(31 - len(value)) + bytes([len(value) * 2])).hex()
    expected_storage = {
        'pool_manager': {w(0): w(int(sender, 16))},
        'position_manager': {w(0): short('Uniswap v4 Positions NFT'), w(1): short('UNI-V4-POSM'), w(8): w(1)},
        'state_view': {}, 'permit2': {},
        'zzz': {'0x' + keccak256(bytes.fromhex(f'{int(sender, 16):064x}' + '0' * 64)).hex(): w(100_000_000 * 10**18)},
    }
    for role, expected in expected_storage.items():
        require(alloc[manifest['contracts'][role]].get('storage', {}) == expected,
                'Native genesis contains an unreviewed external storage row')
    constructor_reader()
    from zzz_ops.deployment_plan import SEADROP, SEADROP_HASH
    sea = alloc[SEADROP]
    sea_raw = bytes.fromhex(sea['code'][2:])
    require('0x' + keccak256(sea_raw).hex() == SEADROP_HASH ==
            manifest['expected_runtime_pins']['seadrop'] and sea.get('storage') == {w(0): w(1)},
            'Archived SeaDrop fixture code/default differs')
    return {'owned_node_stopped': True, 'fresh_protocol_construction': True,
            'exact_native_runtimes': 5, 'explicit_external_genesis_defaults_verified': True,
            'real_market_or_supply_qualified': False}


def corruption_controls(qualification, plans, original):
    """New finite rejection controls using copies of the actual captured record."""
    baseline = plans['baseline-full32']
    config, policy = baseline['projection_config'], baseline['transaction_config']
    checks = []
    def rejects(name, action):
        try:
            action()
        except (ValueError, RpcError) as error:
            checks.append({'name': name, 'rejected': True, 'error_type': type(error).__name__})
        else:
            raise ValueError('Corruption control was accepted: ' + name)
    target = config['contracts']['lp_balance_math']['address']
    def runtime_changed():
        changed = copy.deepcopy(baseline)
        row = next(row for row in changed['rpc_wire'] if
            row['requests'][0]['method'] == 'eth_getCode' and row['requests'][0]['params'][0] == target)
        row['response']['result'] = '0x6000'
        check_plan(changed, config, policy, changed['rpc_wire'])
    rejects('altered_normal_only_helper_runtime', runtime_changed)
    def normal_read_omitted():
        changed = copy.deepcopy(baseline)
        index = next(index for index, row in enumerate(changed['rpc_wire']) if
            row['requests'][0]['method'] == 'eth_getCode' and row['requests'][0]['params'][0] == target)
        changed['rpc_wire'].pop(index)
        changed['rpc_count'] -= 1
        changed['rpc_counts']['eth_getCode'] -= 1
        check_plan(changed, config, policy, changed['rpc_wire'])
    rejects('omitted_normal_only_helper_read', normal_read_omitted)
    def header_changed():
        changed = copy.deepcopy(baseline)
        row = next(row for row in changed['rpc_wire'] if row['requests'][0]['method'] == 'eth_getBlockByNumber')
        row['response']['result']['hash'] = '0x' + 'f' * 64
        check_plan(changed, config, policy, changed['rpc_wire'])
    rejects('altered_canonical_anchor_response', header_changed)
    def caller_changed():
        changed = copy.deepcopy(baseline)
        changed['payload']['wallet'] = '0x' + '42' * 20
        check_plan(changed, config, policy, changed['rpc_wire'])
    rejects('altered_claim_caller', caller_changed)
    def padding_reduced():
        changed = copy.deepcopy(baseline['result'])
        gas = changed['next_batch']['network_gas']
        gas['suggested_limit'] = str(int(gas['suggested_limit']) - 1)
        check_plan_result(baseline['payload'], changed)
    rejects('reduced_full_twenty_percent_padding', padding_reduced)
    def recipient_changed():
        changed = copy.deepcopy(qualification['executions'][-1])
        selected_asset = plans[changed['plan_label']]['result']['next_batch']['claim_operations'][0]['asset']
        balances = changed['after']['recipient_balances']
        balances[selected_asset] = str(amount(balances[selected_asset]) + 1)
        check_execution(changed, plans, original)
    rejects('altered_actual_recipient_balance', recipient_changed)
    def source_forged():
        changed = copy.deepcopy(baseline['production_source_sha256'])
        changed['frontend_api/service.py'] = 'f' * 64
        check_sources(changed)
    rejects('forged_normal_admission_source_identity', source_forged)
    def entitlement_erased():
        changed = copy.deepcopy(qualification)
        changed['closing_claims']['claims'][1]['raw'] = '0'
        check_faults(changed, plans, original)
    rejects('erased_unavailable_original_currency_right', entitlement_erased)
    require(len(checks) == 8, 'Wrong new corruption-control inventory')
    return {'schema': 1, 'passed': True, 'controls': checks,
            'evm_transactions': 0, 'rpc_calls': 0, 'unchanged_test_methods_rerun': 0,
            'scope': 'New offline corruptions of copies of this actual captured evidence only'}


def verify(folder, wire_path=None, *, run_controls=False):
    """Read a newly owned campaign directory; outputs are created by main only."""
    folder = Path(folder).resolve()
    qualification_path = folder / 'qualification.json'
    if not qualification_path.exists():
        qualification_path = folder / 'qualification/qualification.json'
    qualification = load(qualification_path)
    require(qualification.get('schema') == 1, 'Unsupported admission evidence schema')
    manifest_path = folder / 'FIXTURE_MANIFEST.json'
    manifest = load(manifest_path)
    require(qualification.get('fixture_manifest_sha256') == sha(canonical(manifest).encode()),
            'Qualification is not bound to the exact fixture manifest')
    construction = check_construction(folder / 'construction', manifest)
    fixture = check_fixture(folder, manifest, construction)
    records = qualification.get('plans', [qualification]) + qualification.get('controls', [])
    require(type(records) is list and 1 <= len(records) <= 64, 'Unbounded plan record inventory')
    wire = load(folder / 'RPC.json.gz') if (folder / 'RPC.json.gz').exists() else None
    original_path = Path(wire_path) if wire_path is not None else folder / 'node/rpc-records.json.xz'
    if wire_path is None and not original_path.exists():
        original_path = folder / 'node/rpc-records.json.gz'
    require(original_path.exists(), 'Independent original fixture wire is required')
    construction_wire = load(folder / 'construction/construction-rpc-records.json.gz')
    original, wire_proof = stream_wire(original_path, records, construction_wire)
    require(wire_proof['expanded_sha256'] == ORIGINAL_WIRE_EXPANDED_SHA and
            wire_proof['expanded_bytes'] == 1_568_472_867 and wire_proof['original_records'] == 94335,
            'Full original wire differs from independently reviewed current campaign')
    if original_path.suffix == '.gz':
        require(wire_proof['compressed_sha256'] == ORIGINAL_WIRE_GZIP_SHA,
                'Original gzip bytes differ from retained source capture')
    original_by_index = {row['original_index']: row for row in original}
    results, refusals, positive_records = [], [], {}
    labels = set()
    cursor = 0
    records.sort(key=lambda record: record.get('fixture_wire_start', 0))
    for record in records:
        require(record['label'] not in labels, 'Duplicate plan label')
        labels.add(record['label'])
        config = record['projection_config']
        transaction_config = record['transaction_config']
        check_configuration(config, transaction_config, manifest if 'result' in record else None)
        rows = record.get('rpc_wire')
        if rows is None:
            require(wire is not None and type(record.get('wire_start')) is int and
                    type(record.get('wire_end')) is int and
                    0 <= record['wire_start'] < record['wire_end'] <= len(wire), 'Missing exact plan wire slice')
            rows = wire[record['wire_start']:record['wire_end']]
        if 'fixture_wire_start' in record:
            first, last = record['fixture_wire_start'], record['fixture_wire_end']
            require(type(first) is int and type(last) is int and cursor <= first < last <= wire_proof['original_records'],
                    'Plan original-wire range overlaps or escapes capture')
            require(last - first == len(flatten_wire(rows)), 'Plan original-wire range contains missing/extra reads')
            captured_range = [original_by_index[index] for index in range(first, last)]
            used = bind_plan_to_original(rows, captured_range)
            require(used == last - first, 'Plan did not consume its entire actual wire range')
            cursor = last
        else:
            cursor = bind_plan_to_original(rows, original, cursor)
        if 'result' in record:
            results.append(check_plan(record, config, transaction_config, rows))
            positive_records[record['label']] = record
        else:
            refusals.append(check_refusal(record, config, transaction_config, rows))
    require(results and any(row['published'] for row in results), 'No successful full normal claim plan')
    executions = [check_execution(record, positive_records, original)
                  for record in qualification.get('executions', [])]
    require(executions, 'No actual current-owner payout linked to normal admission')
    faults = check_faults(qualification, positive_records, original)
    original_selection = positive_records.get('baseline-full32')
    require(original_selection is not None and len(original_selection['payload']['claims']) == 32,
            'Missing original finite32 selection')
    identities = lambda rows: [(row['token_id'], row['asset'], row['royalty']) for row in rows]
    paid_selection = [entry for record in qualification['executions']
                     if record['plan_label'] in ('baseline-full32', 'fresh-original32-after-prefix')
                     for entry in positive_records[record['plan_label']]['result']['next_batch']['claim_operations']]
    require(len(paid_selection) == len(set(identities(paid_selection))) == 32 and
            set(identities(paid_selection)) == set(identities(original_selection['payload']['claims'])),
            'Original32 selection was omitted or paid twice')
    zero_plans = [record for label, record in positive_records.items() if label.startswith('fresh-original32-after-')
                  and record['result']['next_batch'] is None]
    require(len(zero_plans) == 1 and identities(zero_plans[0]['payload']['claims']) ==
            identities(original_selection['payload']['claims']) and
            all(row['status'] == 'zero' for row in zero_plans[0]['result']['entries']) and
            zero_plans[0]['result']['planning']['trial_count'] == 0,
            'Fresh original selection did not confirm exact zero without extra simulations')
    check_sources()
    result = {'schema': 1, 'complete': True, 'production_approved': False,
        'normal_projection_replayed': True, 'configured_contract_pins': len(config['contracts']),
        'positive_plans': results, 'refusals': refusals, 'executions': executions,
        'faults': faults, 'original32_paid_exactly_once_and_confirmed_zero': True,
        'construction': construction, 'fixture': fixture, 'original_wire': wire_proof,
        'source_sha256': dict(SOURCE_PINS),
        'scope': 'Independent offline exact-wire normal API replay; not additional EVM/network/provider acceptance'}
    if run_controls:
        result['new_corruption_controls'] = corruption_controls(qualification, positive_records, original)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wire', type=Path, help='Exact lossless XZ transcode or retained original gzip')
    parser.add_argument('--controls-output', type=Path, help='Run and exclusively save the eight new offline corruption controls')
    parser.add_argument('--planner-source', type=Path,
        default=ROOT / 'reports/lp-claims-maximum-20261120/campaign04/tool-sources/frontend_api_claim_planner.py',
        help='Exact retained6d5 planner bytes for this original attempt02 source stage')
    args = parser.parse_args(argv)
    source_before = sha(Path(__file__).read_bytes())
    with planner_stage(args.planner_source, OLD_PLANNER_SHA):
        result = verify(args.campaign, args.wire, run_controls=args.controls_output is not None)
    result['planner_source_scope'] = 'Exact archived6d5 source stage; no relabeling as later first-success planner'
    require(sha(Path(__file__).read_bytes()) == source_before, 'Checker source changed during verification')
    result['checker_source_sha256'] = source_before
    if args.controls_output is not None:
        controls = result.pop('new_corruption_controls')
        controls['checker_source_sha256'] = source_before
        with args.controls_output.open('x', encoding='utf-8') as stream:
            json.dump(controls, stream, indent=2, allow_nan=False)
            stream.write('\n')
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'complete': result['complete'], 'positive_plans': len(result['positive_plans']),
                      'production_approved': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
