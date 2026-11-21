"""NEW request-local canonical reuse checks; no old test methods/imports."""
import copy
from contextvars import Context
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api.canonical_cache import scope
from frontend_api.service import Projection, ProjectionError
from zzz_ops.abi import keccak256
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, BudgetedRPC, consume, request_scope


HASH = '0x' + '12' * 32
OTHER_HASH = '0x' + '34' * 32
TARGET = '0x' + '56' * 20
BLOCK = {'blockHash': HASH, 'requireCanonical': True}


def params(**fields):
    return [dict(to=TARGET, data='0x12345678', **fields), copy.deepcopy(BLOCK)]


class Transport:
    def __init__(self, reply='0x' + '00' * 31 + '01'):
        self.reply = reply
        self.calls = []
        self.failures = []
        self.active_url = 'redacted-local-fixture'

    def call(self, method, arguments=None):
        self.calls.append((method, copy.deepcopy(arguments)))
        # Model the ordinary per-attempt chain proof plus one read POST; cache
        # reuse must avoid new POSTs without changing the existing POST budget.
        consume('posts')
        if method != 'eth_chainId':
            consume('posts')
        if self.failures:
            raise self.failures.pop(0)
        return self.reply


class CanonicalCacheTests(unittest.TestCase):
    def projection(self, transport=None):
        transport = transport or Transport()
        return SimpleNamespace(rpc=BudgetedRPC(transport), lineage=None), transport

    def test_identical_canonical_calls_keep_original_call_and_post_budgets(self):
        p, transport = self.projection()
        budget = Budget()
        original = p.rpc
        with request_scope(budget), scope(p):
            first = p.rpc.call('eth_call', params())
            self.assertEqual(p.rpc.call('eth_call', params()), first)
            self.assertEqual((budget.calls, budget.posts), (1023, 2046))
        self.assertIs(p.rpc, original)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual((Budget().calls, Budget().posts), (1024, 2048))

    def test_canonical_code_reuse_keeps_each_expected_runtime_hash_check(self):
        p, transport = self.projection(Transport('0x6000'))
        digest = '0x' + keccak256(bytes.fromhex('6000')).hex()
        with request_scope(), scope(p):
            Projection._code(p, TARGET, digest, BLOCK)
            with self.assertRaisesRegex(ProjectionError, 'differs from deployment pin'):
                Projection._code(p, TARGET, '0x' + 'ff' * 32, BLOCK)
        self.assertEqual(len(transport.calls), 1)

    def test_abi_consumers_still_check_their_expected_word_count(self):
        p, transport = self.projection()
        p.accounting_version = 7
        with request_scope(), scope(p):
            self.assertEqual(len(Projection._call(p, TARGET, 'totalWeight()', block=BLOCK)), 1)
            with self.assertRaisesRegex(ProjectionError, 'Unexpected static ABI result length'):
                Projection._call(p, TARGET, 'totalWeight()', block=BLOCK, words=2)
        self.assertEqual(len(transport.calls), 1)

    def test_all_transaction_fields_and_method_belong_to_the_key(self):
        p, transport = self.projection()
        requests = [params(), params(**{'from': '0x' + '78' * 20}), params(gas='0x100'),
                    params(value='0x1'), [{'to': TARGET, 'data': '0x99999999'}, BLOCK],
                    [{'to': '0x' + '90' * 20, 'data': '0x12345678'}, BLOCK]]
        with request_scope(), scope(p):
            for request in requests:
                p.rpc.call('eth_call', request)
                p.rpc.call('eth_call', copy.deepcopy(request))
            p.rpc.call('eth_getCode', [TARGET, BLOCK])
            p.rpc.call('eth_getCode', [TARGET, BLOCK])
        self.assertEqual(len(transport.calls), len(requests) + 1)

    def test_distinct_canonical_blocks_never_share_a_reply(self):
        p, transport = self.projection()
        other = params()
        other[1]['blockHash'] = OTHER_HASH
        with request_scope(), scope(p):
            for request in (params(), other, params(), other):
                p.rpc.call('eth_call', request)
        self.assertEqual(len(transport.calls), 2)

    def test_nonexact_eip1898_shapes_and_extra_params_are_not_cached(self):
        p, transport = self.projection()
        blocks = ['latest', '0x63', {'blockNumber': '0x63'}, {'blockHash': HASH},
                  {'blockHash': HASH, 'requireCanonical': False},
                  {'blockHash': HASH, 'requireCanonical': 1},
                  {'blockHash': HASH, 'requireCanonical': True, 'extra': 0},
                  {'blockHash': '0x1234', 'requireCanonical': True}]
        requests = [[params()[0], block] for block in blocks]
        requests += [[params()[0], BLOCK, {}], tuple(params())]
        with request_scope(), scope(p):
            for request in requests:
                p.rpc.call('eth_call', request)
                p.rpc.call('eth_call', request)
        self.assertEqual(len(transport.calls), 2 * len(requests))

    def test_live_chain_head_headers_storage_and_receipts_remain_live(self):
        p, transport = self.projection()
        requests = [('eth_chainId', []), ('eth_blockNumber', []),
                    ('eth_getBlockByNumber', ['0x63', False]),
                    ('eth_getBlockByHash', [HASH, False]),
                    ('eth_getStorageAt', [TARGET, '0x0', BLOCK]),
                    ('eth_getTransactionReceipt', [HASH])]
        with request_scope(), scope(p):
            for method, request in requests:
                p.rpc.call(method, request)
                p.rpc.call(method, request)
        self.assertEqual(len(transport.calls), 2 * len(requests))

    def test_transport_identity_prevents_cross_provider_reply_reuse(self):
        p, first = self.projection(Transport('first'))
        peer, second = self.projection(Transport('second'))
        with request_scope(), scope([p, peer]):
            self.assertEqual(p.rpc.call('eth_call', params()), 'first')
            self.assertEqual(peer.rpc.call('eth_call', params()), 'second')
            self.assertEqual(p.rpc.call('eth_call', params()), 'first')
        self.assertEqual((len(first.calls), len(second.calls)), (1, 1))

    def test_saved_and_returned_nested_values_have_no_mutable_aliases(self):
        reply = {'nested': [{'amount': 7}]}
        p, transport = self.projection(Transport(reply))
        with request_scope(), scope(p):
            first = p.rpc.call('eth_call', params())
            first['nested'][0]['amount'] = 99
            reply['nested'][0]['amount'] = 88
            second = p.rpc.call('eth_call', params())
            self.assertEqual(second, {'nested': [{'amount': 7}]})
            second['nested'].append('changed')
            self.assertEqual(p.rpc.call('eth_call', params()), {'nested': [{'amount': 7}]})
        self.assertEqual(len(transport.calls), 1)

    def test_captured_params_and_equivalent_object_order_preserve_exact_query(self):
        p, transport = self.projection()
        request = params()
        with request_scope(), scope(p):
            p.rpc.call('eth_call', request)
            request[0]['data'] = '0x87654321'
            p.rpc.call('eth_call', request)
            reversed_order = [{'data': '0x12345678', 'to': TARGET},
                              {'requireCanonical': True, 'blockHash': HASH}]
            p.rpc.call('eth_call', reversed_order)
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(transport.calls[0][1][0]['data'], '0x12345678')

    def test_transport_failures_are_retried_and_only_later_success_is_cached(self):
        p, transport = self.projection()
        transport.failures = [RpcError('synthetic unavailable')]
        with request_scope(), scope(p):
            with self.assertRaises(RpcError):
                p.rpc.call('eth_call', params())
            expected = p.rpc.call('eth_call', params())
            self.assertEqual(p.rpc.call('eth_call', params()), expected)
        self.assertEqual(len(transport.calls), 2)

    def test_work_limit_exception_is_not_saved_as_a_response(self):
        p, transport = self.projection()
        transport.failures = [WorkLimit('rpc_budget')]
        with request_scope(), scope(p):
            with self.assertRaises(WorkLimit):
                p.rpc.call('eth_call', params())
            p.rpc.call('eth_call', params())
        self.assertEqual(len(transport.calls), 2)

    def test_cached_hit_cannot_cross_the_existing_work_deadline(self):
        now = [0.]
        budget = Budget(clock=lambda: now[0])
        p, transport = self.projection()
        with self.assertRaisesRegex(WorkLimit, 'deadline'):
            with request_scope(budget), scope(p):
                p.rpc.call('eth_call', params())
                now[0] = 25.
                p.rpc.call('eth_call', params())
        self.assertEqual(len(transport.calls), 1)

    def test_cached_hit_checks_snapshot_expiry_after_forward_wall_jump(self):
        wall = [100.]
        budget = Budget(clock=lambda: 0.)
        budget.expire_at(120., lambda: wall[0])
        p, transport = self.projection()
        with self.assertRaisesRegex(WorkLimit, 'snapshot_expired'):
            with request_scope(budget), scope(p):
                p.rpc.call('eth_getCode', [TARGET, BLOCK])
                wall[0] = 121.
                p.rpc.call('eth_getCode', [TARGET, BLOCK])
        self.assertEqual(len(transport.calls), 1)

    def test_nested_scopes_and_predecessors_share_one_budget_and_cache(self):
        p, transport = self.projection()
        peer = SimpleNamespace(rpc=p.rpc, lineage=None)
        p.lineage = SimpleNamespace(entries=[SimpleNamespace(projection=peer), SimpleNamespace(projection=peer)])
        originals = p.rpc, peer.rpc
        budget = Budget()
        with request_scope(budget), scope([p, p]):
            outer_proxy = p.rpc
            p.rpc.call('eth_call', params())
            with request_scope(Budget()), scope(peer):
                self.assertIs(p.rpc, outer_proxy)
                peer.rpc.call('eth_call', params())
                self.assertEqual(budget.calls, 1023)
            self.assertIs(p.rpc, outer_proxy)
            p.rpc.call('eth_call', params())
        self.assertIs(p.rpc, originals[0])
        self.assertIs(peer.rpc, originals[1])
        self.assertEqual(len(transport.calls), 1)

    def test_handled_nested_failure_keeps_the_outer_cache_alive(self):
        p, transport = self.projection()
        with request_scope(), scope(p):
            p.rpc.call('eth_call', params())
            try:
                with scope(p):
                    raise ValueError('synthetic nested refusal')
            except ValueError:
                pass
            p.rpc.call('eth_call', params())
        self.assertEqual(len(transport.calls), 1)

    def test_exception_restores_transports_and_next_request_reads_again(self):
        p, transport = self.projection()
        original = p.rpc
        with self.assertRaises(ValueError):
            with request_scope(), scope(p):
                p.rpc.call('eth_call', params())
                raise ValueError('synthetic refusal')
        self.assertIs(p.rpc, original)
        with request_scope(), scope(p):
            p.rpc.call('eth_call', params())
        self.assertEqual(len(transport.calls), 2)

    def test_leaked_proxy_cannot_reuse_a_completed_request(self):
        p, transport = self.projection()
        with request_scope(), scope(p):
            leaked = p.rpc
            leaked.call('eth_call', params())
        with request_scope():
            leaked.call('eth_call', params())
        self.assertEqual(len(transport.calls), 2)

    def test_separate_contexts_cannot_read_each_others_cached_replies(self):
        p, transport = self.projection(Transport('outer'))
        with request_scope(), scope(p):
            self.assertEqual(p.rpc.call('eth_call', params()), 'outer')
            def other_request():
                with request_scope(), scope(p):
                    self.assertEqual(p.rpc.call('eth_call', params()), 'other')
            transport.reply = 'other'
            Context().run(other_request)
            self.assertEqual(p.rpc.call('eth_call', params()), 'outer')
        self.assertEqual(len(transport.calls), 2)

    def test_scope_requires_existing_budget_and_validates_before_wrapping(self):
        p, _transport = self.projection()
        original = p.rpc
        with self.assertRaisesRegex(RuntimeError, 'active request budget'):
            with scope(p):
                self.fail('Scope without a budget was admitted')
        bad = SimpleNamespace(rpc=Transport(), lineage=None)
        with request_scope(), self.assertRaisesRegex(TypeError, 'existing budgeted RPC'):
            with scope([bad, p]):
                self.fail('Unbudgeted transport was admitted')
        self.assertIs(p.rpc, original)

    def test_convenience_eth_call_uses_the_same_cache_and_preserves_sender(self):
        p, transport = self.projection()
        with request_scope(), scope(p):
            self.assertEqual(p.rpc.active_url, 'redacted-local-fixture')
            p.rpc.eth_call(TARGET, '0x12345678', block=BLOCK)
            p.rpc.call('eth_call', params())
            p.rpc.eth_call(TARGET, '0x12345678', sender=TARGET, block=BLOCK)
            p.rpc.eth_call(TARGET, '0x12345678', sender=TARGET, block=BLOCK)
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(transport.calls[1][1][0]['from'], TARGET)

    def test_key_is_derived_from_captured_params_even_if_source_changes_during_capture(self):
        p, transport = self.projection()
        request = params()
        mutated = False
        original_copy = copy.deepcopy
        def capture(value):
            nonlocal mutated
            if value is request and not mutated:
                # Model an external owner changing a mutable input precisely at
                # the capture boundary, without threads or timing assumptions.
                mutated = True
                request[0]['data'] = '0x87654321'
            return original_copy(value)
        with request_scope(), scope(p), patch('frontend_api.canonical_cache.deepcopy', side_effect=capture):
            p.rpc.call('eth_call', request)
            request[0]['data'] = '0x12345678'
            p.rpc.call('eth_call', request)
        self.assertEqual([row[1][0]['data'] for row in transport.calls], ['0x87654321', '0x12345678'])


if __name__ == '__main__':
    unittest.main()
