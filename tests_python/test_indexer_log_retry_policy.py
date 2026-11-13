"""Log range reduction must not amplify terminal/global provider failures."""
import http.client
import unittest
import urllib.error
from unittest.mock import patch

from tests_python import test_indexer as fixtures
from zzz_ops.errors import RemoteRPCError, RpcError, WorkLimit
from zzz_ops.rpc import WrongChain


def wrapped(error):
    outer = RpcError('Bounded transport failed')
    outer.__cause__ = error
    return outer


class IndexerLogRetryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.IndexerTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.index, self.chain = self.f.idx, self.f.chain

    def rejected_once(self, error):
        before = self.f.database_snapshot(self.index)
        original, ranges = self.chain.call, []

        def call(method, params):
            if method == 'eth_getLogs':
                ranges.append((params[0]['fromBlock'], params[0]['toBlock']))
                raise error
            return original(method, params)

        with patch.object(self.chain, 'call', side_effect=call):
            with self.assertRaises(type(error)) as caught:
                self.index.step()
        self.assertIs(caught.exception, error)
        self.assertEqual(ranges, [('0x1', '0x5')])
        self.assertEqual(self.f.database_snapshot(self.index), before)
        self.assertEqual(self.index.next_block, 1)

    def test_terminal_work_limits_do_not_start_smaller_log_requests(self):
        for reason in ('deadline', 'rpc_budget', 'snapshot_expired'):
            for factory in (lambda e: e, wrapped):
                with self.subTest(reason=reason, wrapped=factory is wrapped):
                    self.rejected_once(factory(WorkLimit(reason)))

    def test_typed_provider_refusals_do_not_start_smaller_log_requests(self):
        faults = [RemoteRPCError('eth_getLogs', -32005, 'rate_limited'),
                  RemoteRPCError('eth_getLogs', -32602, 'invalid_params'),
                  RemoteRPCError('eth_getLogs', -32000, 'unavailable_block'),
                  RemoteRPCError('eth_getLogs', None),
                  RemoteRPCError('eth_getLogs', -32700),
                  RemoteRPCError('eth_getLogs', -32600),
                  RemoteRPCError('eth_getLogs', -32601),
                  RemoteRPCError('eth_getLogs', -32602),
                  RemoteRPCError('eth_getLogs', -32603)]
        for error in faults:
            for factory in (lambda e: e, wrapped):
                with self.subTest(code=error.code, reason=error.reason,
                                  wrapped=factory is wrapped):
                    self.rejected_once(factory(error))

    def test_transport_authentication_and_wrong_chain_faults_are_terminal(self):
        errors = [WrongChain('Wrong chain'), OSError('Transport unavailable'),
                  TimeoutError('Transport expired'), http.client.HTTPException('Transport closed')]
        # These exact diagnostics are emitted by our shared transport, never
        # copied from a provider's error message or credentialed endpoint.
        errors.extend(RpcError(message) for message in (
            'Malformed RPC chain identity',
            'RPC redirects are not permitted; configure the reviewed endpoint explicitly',
            'RPC stream cannot provide bounded reads',
            'RPC response deadline exceeded',
            'Malformed RPC transport payload',
            'Malformed JSON-RPC payload',
            'Malformed JSON-RPC response',
            'Malformed JSON-RPC response envelope',
            'Missing JSON-RPC result',
            'RPC method is not on the read-only allowlist',
        ))
        for code in (401, 403, 404, 429, 500, 503):
            errors.append(urllib.error.HTTPError('https://invalid.test/', code,
                                                'Unavailable', {}, None))
        for error in errors:
            with self.subTest(kind=type(error).__name__, code=getattr(error, 'code', None)):
                self.rejected_once(wrapped(error))

    def test_cyclic_and_excessively_nested_failure_causes_fail_closed(self):
        cycle = RpcError('Cycle')
        cycle.__cause__ = cycle
        deep = RpcError('Original')
        for _ in range(9):
            deep = wrapped(deep)
        for error in (cycle, deep):
            with self.subTest(cycle=error is cycle):
                self.rejected_once(error)

    def test_existing_opaque_range_limit_reduction_preserves_exact_chunk(self):
        self.chain.max_range = 2
        self.chain.transfer(2, fixtures.B)
        self.chain.transfer(3, fixtures.C)
        original, ranges = self.chain.call, []

        def call(method, params):
            if method == 'eth_getLogs':
                ranges.append((params[0]['fromBlock'], params[0]['toBlock']))
            return original(method, params)

        with patch.object(self.chain, 'call', side_effect=call):
            self.assertEqual(self.index.step(), 2)
        self.assertEqual(ranges, [('0x1', '0x5'), ('0x1', '0x3'), ('0x1', '0x2')])
        self.assertEqual(self.index.next_block, 3)
        self.assertEqual(self.index.nft_owners(fixtures.A), {'7': fixtures.B})
        self.assertEqual(self.index.db.execute('SELECT number FROM blocks ORDER BY number').fetchall(),
                         [(1,), (2,)])

    def test_payload_too_large_can_reduce_without_retrying_other_http_errors(self):
        for kind in ('http413', 'response_size'):
            with self.subTest(kind=kind):
                fixture = fixtures.IndexerTests('runTest')
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                index, chain = fixture.idx, fixture.chain
                chain.transfer(2, fixtures.B)
                original, ranges = chain.call, []

                def call(method, params):
                    if method == 'eth_getLogs':
                        ranges.append((params[0]['fromBlock'], params[0]['toBlock']))
                        if int(params[0]['toBlock'], 16) - int(params[0]['fromBlock'], 16) + 1 > 2:
                            error = (urllib.error.HTTPError('https://invalid.test/', 413,
                                                           'Too large', {}, None) if kind == 'http413'
                                     else RpcError('RPC response exceeded size limit'))
                            raise wrapped(error)
                    return original(method, params)

                with patch.object(chain, 'call', side_effect=call):
                    self.assertEqual(index.step(), 2)
                self.assertEqual(len(ranges), 3)
                self.assertEqual(index.next_block, 3)
                self.assertEqual(index.nft_owners(fixtures.A), {'7': fixtures.B})

    def test_one_block_opaque_rejection_does_not_loop_or_commit(self):
        self.index.chunk = 1
        before = self.f.database_snapshot(self.index)
        original, ranges = self.chain.call, []

        def call(method, params):
            if method == 'eth_getLogs':
                ranges.append((params[0]['fromBlock'], params[0]['toBlock']))
                raise RpcError('Opaque provider refusal')
            return original(method, params)

        with patch.object(self.chain, 'call', side_effect=call), self.assertRaises(RpcError):
            self.index.step()
        self.assertEqual(ranges, [('0x1', '0x1')])
        self.assertEqual(before, self.f.database_snapshot(self.index))


if __name__ == '__main__':
    unittest.main()
