"""Malformed provider data must not bypass identity or bounded failover.

The actual RPC decoder/retry path runs over inert HTTP bytes. The two recursion
cases explicitly inject a platform decoder-limit failure: Python JSON recursion
thresholds differ, so byte nesting alone would not prove that branch was reached.
No endpoint, signer, service or existing state is contacted or modified.
"""
import json
import unittest
from unittest.mock import patch

from zzz_ops.rpc import Rpc, RpcError


class RpcIntegrityTests(unittest.TestCase):
    @staticmethod
    def decoder_limit(bad):
        original = json.loads
        def decode(data, *args, **kwargs):
            if data == bad:
                raise RecursionError('Synthetic platform JSON decoder limit')
            return original(data, *args, **kwargs)
        return patch('zzz_ops.rpc.json.loads', side_effect=decode)

    @staticmethod
    def valid(raw, result=None):
        request = json.loads(raw)
        return json.dumps({'jsonrpc': '2.0', 'id': request['id'],
                           'result': ('0x1' if request['method'] == 'eth_chainId'
                                      else '0xabc') if result is None else result}).encode()

    def test_recursive_json_fails_over_to_a_reviewed_endpoint(self):
        rpc = Rpc(['https://a.invalid', 'https://b.invalid'], 1, retries=1)
        seen = []
        def transport(url, raw):
            seen.append((url, json.loads(raw)['method']))
            return b'[' * 2000 + b'0' + b']' * 2000 if url.endswith('a.invalid') else self.valid(raw)
        bad = b'[' * 2000 + b'0' + b']' * 2000
        with self.decoder_limit(bad), patch.object(rpc, '_read_http', side_effect=transport), patch('zzz_ops.rpc.time.sleep'):
            self.assertEqual(rpc.call('eth_blockNumber'), '0xabc')
        self.assertEqual(seen, [('https://a.invalid', 'eth_chainId'),
                                ('https://b.invalid', 'eth_chainId'),
                                ('https://b.invalid', 'eth_blockNumber')])

    def test_recursive_only_endpoint_returns_a_sanitized_rpc_error(self):
        rpc = Rpc(['https://a.invalid/SYNTHETIC_SECRET'], 1, retries=1)
        bad = b'[' * 2000 + b']' * 2000
        with self.decoder_limit(bad), patch.object(rpc, '_read_http', return_value=bad):
            with self.assertRaises(RpcError) as observed:
                rpc.call('eth_blockNumber')
        self.assertNotIn('SYNTHETIC_SECRET', str(observed.exception))

    def test_duplicate_response_fields_are_rejected_at_any_object_depth(self):
        payloads = (
            b'{"jsonrpc":"2.0","id":99,"id":1,"result":"0x1"}',
            b'{"jsonrpc":"1.0","jsonrpc":"2.0","id":1,"result":"0x1"}',
            b'{"jsonrpc":"2.0","id":1,"result":"0x2","result":"0x1"}',
            b'{"jsonrpc":"2.0","id":1,"result":{"slot":"old","slot":"new"}}',
        )
        for raw in payloads:
            with self.subTest(raw=raw):
                rpc = Rpc(['https://a.invalid'], 1, retries=1)
                with patch.object(rpc, '_read_http', return_value=raw), self.assertRaises(RpcError):
                    rpc._post(rpc.active_url, 'eth_call', [])

    def test_nonfinite_json_numbers_are_rejected_in_nested_results(self):
        for number in (b'NaN', b'Infinity', b'-Infinity', b'1e400', b'-1e400'):
            with self.subTest(number=number):
                rpc = Rpc(['https://a.invalid'], 1, retries=1)
                raw = b'{"jsonrpc":"2.0","id":1,"result":{"gasUsedRatio":[' + number + b']}}'
                with patch.object(rpc, '_read_http', return_value=raw), self.assertRaises(RpcError):
                    rpc._post(rpc.active_url, 'eth_feeHistory', [])

    def test_result_and_error_envelope_is_not_a_qualified_remote_rejection(self):
        rpc = Rpc(['https://a.invalid'], 1, retries=1)
        raw = b'{"jsonrpc":"2.0","id":1,"result":"0x1","error":{"code":-32001,"message":"block not found"}}'
        with patch.object(rpc, '_read_http', return_value=raw), self.assertRaises(RpcError) as observed:
            rpc._post(rpc.active_url, 'eth_call', [])
        self.assertIs(type(observed.exception), RpcError)

    def test_finite_fee_history_json_numbers_are_preserved(self):
        rpc = Rpc(['https://a.invalid'], 1, retries=1)
        result = {'gasUsedRatio': [0, 0.5, 1.0, 1e-9], 'oldestBlock': '0x1'}
        with patch.object(rpc, '_read_http', side_effect=lambda url, raw: self.valid(raw, result)):
            self.assertEqual(rpc._post(rpc.active_url, 'eth_feeHistory', []), result)

    def test_chain_id_requires_a_canonical_hex_quantity(self):
        for malformed in ('1', '0x01', '0X1', '+0x1', '0x0_1', ' 0x1', '0x1\n', b'0x1', True, 1):
            with self.subTest(malformed=malformed):
                rpc = Rpc(['https://a.invalid'], 1, retries=1)
                methods = []
                def respond(url, method, params):
                    methods.append(method)
                    return malformed if method == 'eth_chainId' else '0xabc'
                with patch.object(rpc, '_post', side_effect=respond), self.assertRaises(RpcError):
                    rpc.call('eth_blockNumber')
                self.assertEqual(methods, ['eth_chainId'])

    def test_invalid_chain_identity_fails_over_without_running_the_action_there(self):
        rpc = Rpc(['https://a.invalid', 'https://b.invalid'], 1, retries=1)
        seen = []
        def respond(url, method, params):
            seen.append((url, method))
            if method == 'eth_chainId':
                return '0x01' if url.endswith('a.invalid') else '0x1'
            return '0xabc'
        with patch.object(rpc, '_post', side_effect=respond), patch('zzz_ops.rpc.time.sleep'):
            self.assertEqual(rpc.call('eth_blockNumber'), '0xabc')
        self.assertEqual(seen, [('https://a.invalid', 'eth_chainId'),
                               ('https://b.invalid', 'eth_chainId'),
                               ('https://b.invalid', 'eth_blockNumber')])

    def test_canonical_chain_quantity_and_hex_letter_case_remain_supported(self):
        for chain in ('0x1', '0xa', '0xA', '0x7a69'):
            with self.subTest(chain=chain):
                rpc = Rpc(['https://a.invalid'], int(chain, 16), retries=1)
                with patch.object(rpc, '_post', return_value=chain):
                    self.assertEqual(rpc.call('eth_chainId'), int(chain, 16))


if __name__ == '__main__':
    unittest.main()
