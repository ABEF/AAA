"""Offline CPU profile of a NEW captured claim plan, with unchanged work limits.

No node, endpoint, network, compiler or EVM execution. Only exact responses at
the captured fixture hash are replayed; unseen requests fail rather than being
invented. cProfile overhead is explicit, so this is bottleneck evidence rather
than a service-latency qualification. The owned-chain campaign remains separate.
"""
import argparse
import collections
import cProfile
import gzip
import hashlib
import json
from pathlib import Path
import pstats
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]
from claims_planner_qualification import qualify_plan
from zzz_ops.errors import RemoteRPCError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifest_path = args.campaign / 'planner/mixed-next-0-MANIFEST.json'
    rpc_path = args.campaign / 'fixture/RPC.json.gz'
    manifest = json.loads(manifest_path.read_text())
    compressed = rpc_path.read_bytes()
    if len(compressed) > 64*1024*1024:
        raise ValueError('Compressed replay bound exceeded')
    raw = gzip.decompress(compressed)
    if len(raw) > 256*1024*1024:
        raise ValueError('Expanded replay bound exceeded')
    records = json.loads(raw)
    key = lambda method, params: (method, json.dumps(params, sort_keys=True, separators=(',', ':')))
    lookup, execution, head = {}, None, None
    for row in records:
        responses = row['response']
        responses = responses if isinstance(responses, list) else [responses]
        by_id = {response['id']: response for response in responses}
        for request in row['requests']:
            response, params, method = by_id[request['id']], request['params'], request['method']
            value = response.get('result')
            if method in ('eth_getBlockByHash', 'eth_getBlockByNumber') and isinstance(value, dict):
                if value.get('hash') == manifest['deployment_block_hash']:
                    head = value
                    lookup[key(method, params)] = response
            elif any(isinstance(p, dict) and p.get('blockHash') == manifest['deployment_block_hash'] for p in params):
                lookup[key(method, params)] = response
                if (execution is None and method == 'eth_call' and
                        params[0].get('to') == manifest['contracts']['claim_router']['address'] and
                        len(params[0].get('data', '')) > 138):
                    execution = params[0]
            elif method == 'eth_gasPrice':
                lookup.setdefault(key(method, params), response)
    if head is None or execution is None:
        raise ValueError('No captured exact-block plan and header')
    body, selection = execution['data'][10:], []
    for index in range(int(body[64:128], 16)):
        item = body[128+192*index:128+192*(index+1)]
        selection.append({'token_id': str(int(item[:64], 16)), 'asset': '0x'+item[88:128],
                          'royalty': bool(int(item[128:192], 16))})
    calls = []
    def replay(method, params):
        calls.append(method)
        if method == 'eth_chainId':
            return hex(manifest['chain_id'])
        if method == 'eth_blockNumber':
            return hex(manifest['deployment_block'])
        if method == 'eth_getBlockByNumber' and params[0] == hex(manifest['deployment_block']):
            return head
        response = lookup.get(key(method, params))
        if response is None:
            raise RuntimeError('Uncaptured replay method/parameters: ' + method)
        if 'error' in response:
            raise RemoteRPCError(method, response['error']['code'])
        return response['result']
    profile, error, result = cProfile.Profile(), None, None
    started = time.monotonic()
    try:
        profile.enable()
        result = qualify_plan(replay, manifest, selection, wallet=execution['from'])
    except Exception as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        profile.disable()
    elapsed = time.monotonic()-started
    profile.dump_stats(str(out / 'profile.pstats'))
    functions = []
    for (file, line, name), (_, count, own, cumulative, _) in pstats.Stats(profile).stats.items():
        if any(part in file for part in ('zzz_ops', 'frontend_api', 'claims_planner')):
            functions.append({'file': file, 'line': line, 'name': name, 'calls': count,
                              'cpu_self': own, 'cpu_cumulative': cumulative})
    functions.sort(key=lambda row: row['cpu_cumulative'], reverse=True)
    summary = {'scope': 'Offline exact captured-RPC replay; cProfile overhead; no EVM/network',
        'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'rpc_compressed_sha256': hashlib.sha256(compressed).hexdigest(),
        'default_seconds': 25, 'default_logical_calls': 1024, 'claim_gas_cap': 12000000,
        'selection_count': len(selection), 'elapsed_seconds': elapsed, 'error': error,
        'rpc_counts': dict(collections.Counter(calls)), 'cpu_functions': functions,
        'published_draft': bool(result and result['plan']['next_batch'])}
    (out / 'PROFILE.json').write_text(json.dumps(summary, indent=2)+'\n')
    if result is not None:
        (out / 'REPLAYED_PLAN.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': str(out), 'elapsed': elapsed, 'error': error,
                      'rpc_calls': len(calls), 'top': functions[:8]}, indent=2))
    return int(error is not None)


if __name__ == '__main__':
    raise SystemExit(main())
