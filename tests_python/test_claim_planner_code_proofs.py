"""New request-local runtime-proof checks; no EVM, network or old test methods."""
import copy
from collections import Counter
from functools import partial
import unittest

from frontend_api.claim_planner import MAX_METADATA, _SnapshotReads
from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.transactions import Transactions, TransactionInputError
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, BudgetedRPC, request_scope
from tests_python.test_exact_lp_profile7 import Fresh7API
from tests_python.test_frontend_api import addr, words
from tests_python.test_frontend_transactions import transaction_config


BLOCK = {'blockHash': '0x' + 'a' * 64, 'requireCanonical': True}
CODE = '0x60006000'
PIN = '0x' + keccak256(bytes.fromhex(CODE[2:])).hex()


class RuntimeRPC:
    def __init__(self):
        self.calls = []
        self.error = None

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if self.error is not None:
            raise self.error
        if method != 'eth_getCode':
            raise AssertionError('Unexpected test transport method')
        return CODE


class CountedProjection(Projection):
    def _code(self, target, expected, block):
        self.verifications.append((target, expected, copy.deepcopy(block)))
        return super()._code(target, expected, block)


def wrapped_projection(targets=(addr(1),), *, rpc=None, block=None):
    transport = rpc or RuntimeRPC()
    reads = _SnapshotReads(BudgetedRPC(transport), copy.deepcopy(block or BLOCK), set(targets))
    p = CountedProjection.__new__(CountedProjection)
    p.rpc, p.verifications = reads, []
    p._code = partial(reads.verify_code, p._code)
    return p, reads, transport


class ClaimPlannerCodeProofTests(unittest.TestCase):
    def test_real_runtime_verification_is_reused_only_inside_one_request(self):
        p, reads, rpc = wrapped_projection()
        p._code(addr(1), PIN, BLOCK)
        p._code(addr(1), PIN, copy.deepcopy(BLOCK))
        self.assertEqual(len(p.verifications), 1)
        self.assertEqual(len(rpc.calls), 1)
        self.assertEqual(len(reads.code_proofs), 1)
        second, _, _ = wrapped_projection(rpc=rpc)
        second._code(addr(1), PIN, BLOCK)
        self.assertEqual(len(second.verifications), 1)
        self.assertEqual(len(rpc.calls), 2)

    def test_a_different_expected_pin_still_runs_and_fails_the_real_hash_check(self):
        p, reads, rpc = wrapped_projection()
        p._code(addr(1), PIN, BLOCK)
        for _ in range(2):
            with self.assertRaises(ProjectionError):
                p._code(addr(1), '0x' + 'f' * 64, BLOCK)
        self.assertEqual(len(p.verifications), 3)
        self.assertEqual(len(reads.code_proofs), 1)
        # Bytes may already be cached, but the two wrong hashes are NOT proofs.
        self.assertEqual(len(rpc.calls), 1)

    def test_targets_and_canonical_block_shapes_cannot_inherit_another_proof(self):
        p, reads, _ = wrapped_projection((addr(1), addr(2)))
        p._code(addr(1), PIN, BLOCK)
        p._code(addr(2), PIN, BLOCK)
        p._code(addr(2), PIN, BLOCK)
        self.assertEqual(len(p.verifications), 2)
        for altered in ({'blockHash': '0x' + 'b' * 64, 'requireCanonical': True},
                        {'blockHash': BLOCK['blockHash'], 'requireCanonical': False},
                        {'blockHash': BLOCK['blockHash'], 'requireCanonical': 1},
                        {**BLOCK, 'extra': True}, 'latest'):
            for _ in range(2):
                p._code(addr(1), PIN, altered)
        for _ in range(2):
            p._code(addr(3), PIN, BLOCK)
        self.assertEqual(len(p.verifications), 14)
        self.assertEqual(len(reads.code_proofs), 2)

    def test_untyped_expected_hash_does_not_create_a_reusable_proof(self):
        _, reads, _ = wrapped_projection()
        calls = []
        # The production verifier rejects malformed pins. Even a custom
        # verifier's success cannot turn an untyped value into a cached proof.
        def succeeds(target, expected, block):
            calls.append((target, expected, block))
        for pin in (None, 1, b'x' * 32, '0x' + 'a' * 63):
            reads.verify_code(succeeds, addr(1), pin, BLOCK)
            reads.verify_code(succeeds, addr(1), pin, BLOCK)
        self.assertEqual(len(calls), 8)
        self.assertFalse(reads.code_proofs)

    def test_runtime_and_transport_failures_never_become_successful_proofs(self):
        p, reads, rpc = wrapped_projection()
        rpc.error = RpcError('Controlled transport failure')
        with self.assertRaises(RpcError):
            p._code(addr(1), PIN, BLOCK)
        self.assertFalse(reads.code_proofs)
        rpc.error = None
        with self.assertRaises(ProjectionError):
            p._code(addr(1), PIN, BLOCK)
        self.assertEqual(len(rpc.calls), 1)

    def test_cache_hits_preserve_global_failures_and_the_existing_deadline(self):
        p, reads, _ = wrapped_projection()
        p._code(addr(1), PIN, BLOCK)
        reads.global_error = RpcError('Later unrelated dependency failed')
        with self.assertRaises(ProjectionError):
            p._code(addr(1), PIN, BLOCK)
        self.assertEqual(len(p.verifications), 1)
        p, _, _ = wrapped_projection()
        now = [0.0]
        with self.assertRaises(WorkLimit):
            with request_scope(Budget(seconds=1, clock=lambda: now[0])):
                p._code(addr(1), PIN, BLOCK)
                now[0] = 1.0
                p._code(addr(1), PIN, BLOCK)
        self.assertEqual(len(p.verifications), 1)

    def test_successful_proofs_remain_bounded_by_the_existing_metadata_limit(self):
        targets = tuple(addr(i + 1) for i in range(MAX_METADATA + 1))
        p, reads, _ = wrapped_projection(targets)
        for target in targets:
            p._code(target, PIN, BLOCK)
        self.assertEqual(len(reads.code_proofs), MAX_METADATA)
        p._code(targets[0], PIN, BLOCK)
        p._code(targets[-1], PIN, BLOCK)
        self.assertEqual(len(p.verifications), MAX_METADATA + 2)

    def fresh_service(self, *, owner_changes=False):
        f = Fresh7API(self)
        original = f.rpc.call
        owner_reads = [0]
        sent = []
        def call(method, params):
            if method == 'eth_call' and 'from' in params[0]:
                sent.append(copy.deepcopy(params))
                count = int(params[0]['data'][74:138], 16)
                return words(32, count, *([18] * count))
            if method == 'eth_call' and params[0]['data'] == calldata('ownerOf(uint256)', f.rpc.nft_id):
                owner_reads[0] += 1
                if owner_changes and owner_reads[0] >= 3:
                    return words(addr(31))
            if method == 'eth_estimateGas':
                return hex(200000)
            if method == 'eth_gasPrice':
                return hex(10**9)
            if method == 'eth_getBalance':
                return hex(10**18)
            return original(method, params)
        f.rpc.call = call
        p = CountedProjection(f.config, f.rpc, clock=lambda: 4000)
        p.verifications = []
        request = {'action': 'claim', 'wallet': addr(30), 'claims': [
            {'token_id': str(f.rpc.nft_id), 'asset': ZERO, 'royalty': False}]}
        return p, Transactions(p, transaction_config(p)), request, owner_reads, sent

    def test_real_plan_copy_reuses_proofs_without_changing_original_or_later_requests(self):
        p, service, request, owners, sent = self.fresh_service()
        rpc, verifier = p.rpc, p._code
        first = service.plan_claims(request)
        counts = Counter((target, pin) for target, pin, _ in p.verifications)
        self.assertTrue(counts)
        self.assertTrue(all(count == 1 for count in counts.values()))
        self.assertEqual(owners[0], 3)
        self.assertEqual(len(sent), 2)
        self.assertEqual(first['next_batch']['claim_operations'][0]['simulated_raw'], '18')
        self.assertIs(p.rpc, rpc)
        self.assertEqual(p._code, verifier)
        service.plan_claims(request)
        self.assertTrue(all(count == 2 for count in Counter(
            (target, pin) for target, pin, _ in p.verifications).values()))

    def test_a_final_owner_change_still_rejects_the_earlier_successful_trial(self):
        p, service, request, owners, sent = self.fresh_service(owner_changes=True)
        with self.assertRaises(TransactionInputError):
            service.plan_claims(request)
        self.assertEqual(owners[0], 3)
        self.assertEqual(len(sent), 1)
        self.assertTrue(all(count == 1 for count in Counter(
            (target, pin) for target, pin, _ in p.verifications).values()))


if __name__ == '__main__':
    unittest.main()
