"""Current7 custody adapters over the actual shared reader and physical codec.

Synthetic RPC transport only; no running process, public provider, transaction,
gas qualification or contract suite is represented by these cases.
"""
import unittest

from frontend_api.service import Projection, ZERO
from tests_python import test_manual_lp_review as fixtures
from tests_python.test_frontend_api import addr
from zzz_ops import management_custody as M
from zzz_ops.abi import calldata, decode_words, keccak256
from zzz_ops.errors import RpcError
from zzz_ops.management_base import ManagementBlocked, ManagementReader

H = '0x' + '12' * 32


class CustodyManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ManualLPReviewTests.setUpClass()

    def setUp(self):
        self.f = fixtures.ManualLPReviewTests('test_exact_b_c_d_calls_and_floor_meanings')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.rpc, self.q, self.c = self.f.rpc, self.f.q, self.f.c
        self.put('access', 'preparationNonce()', 3)
        self.put('access', 'preparationHash()', 0)
        self.put('vault', 'bucketCount()', 1)
        self.put('vault', 'MAX_BUCKETS()', 4)
        self.put('vault', 'bucketAt(uint256)', 7, 0)
        self.put('rebalance_confirmation', 'controlFingerprint(bytes32)', H, self.q.pool)
        self.put('portfolio_policy', 'revision()', 5)
        self.put('strategy', 'target(bytes32)', [self.q.lower % 2**256, self.q.upper, 2**96], self.q.pool)
        self.reader = ManagementReader(Projection(self.f.config, self.rpc, clock=lambda: 4000),
            self.f.extra, self.f.f.block())

    def put(self, role, method, value, *args):
        self.f.put(role, method, value, *args)

    def selected(self, action='park', **parameters):
        supplied = ({'bucket': '7', 'destination_pool': self.q.pool, 'minimumLiquidity': '1'}
            if action == 'resume' else {'bucket': '7', 'minimum0': '0', 'minimum1': '0'})
        supplied.update(parameters)
        return {'action': action, 'parameters': M.validate(action, supplied), 'expires_at': 4180}

    def observe(self, action='park', **parameters):
        selected = self.selected(action, **parameters)
        return selected, M.observe(self.reader, selected, self.f.gov)

    def parked(self):
        self.q.position[1] = 0;self.q.position[7] = 4
        self.q.secondary = 0;self.q.secondary_count = 0
        self.put('access', 'paused()', 0)

    def test_raw_park_exact_fourteen_word_native_tuple_and_explicit_zero_floors(self):
        selected, snapshot = self.observe()
        signature, arguments, data = M.call_spec(selected, snapshot, H)
        self.assertEqual('park(' + M.PARKING_TUPLE + ')', signature)
        values = [int(w, 16) for w in decode_words('0x' + data[10:])]
        self.assertEqual(14, len(values));self.assertEqual([7, int(self.q.pool, 16), 123], values[:3])
        self.assertEqual([0, int(addr(20), 16), 0, 0, 4180, int(H, 16)], values[7:13])
        self.assertEqual(int(snapshot['controls']['physical']['execution_portfolio_fingerprint'], 16), values[13])
        self.assertEqual(ZERO, arguments['r']['token0'])
        self.assertEqual('0', arguments['r']['minimum0']);self.assertEqual('0', arguments['r']['minimum1'])
        self.assertEqual(['123', '124'], [str(x['lp_token_id']) for x in snapshot['controls']['physical']['physical_legs']])

    def test_raw_close_price_outage_and_disabled_operations_need_no_financial_fallback(self):
        self.rpc.price_failure = True;self.q.config[6] = 0
        for action in ('park', 'close_residual'):
            selected, snapshot = self.observe(action, minimum0='9', minimum1='11')
            signature, arguments, data = M.call_spec(selected, snapshot, H)
            self.assertTrue(signature.startswith('park(' if action == 'park' else 'closeResidual('))
            self.assertEqual('9', arguments['r']['minimum0']);self.assertEqual('11', arguments['r']['minimum1'])
        excluded = {calldata('priceBounds(address)', addr(20))[:10], calldata('executionPoolCount()')[:10],
            calldata('target(bytes32)', self.q.pool)[:10], calldata('needsRebalance(uint256)', 7)[:10]}
        self.assertFalse(any(method == 'eth_call' and params[0]['data'][:10] in excluded for method, params in self.rpc.calls))

    def test_only_park_may_drain_during_preparation(self):
        self.put('access', 'preparationActive()', 1)
        self.put('access', 'canConfigure(address)', 0, self.f.gov)
        self.put('access', 'preparationHash()', H)
        _, snapshot = self.observe('park')
        self.assertTrue(snapshot['controls']['global_state']['preparation_active'])
        with self.assertRaisesRegex(ValueError, 'preparation'):
            self.observe('close_residual')

    def test_spot_changes_only_market_observations_and_never_fixed_manifest_fields(self):
        selected, before = self.observe('close_residual')
        self.q.tick = 50
        after = M.observe(self.reader, selected, self.f.gov)
        self.assertNotEqual(before['market_observations'], after['market_observations'])
        self.assertEqual(before['controls'], after['controls'])
        self.assertEqual(M.call_spec(selected, before, H), M.call_spec(selected, after, H))

    def test_nonce_epoch_shares_and_liquidity_changes_are_consent_changes(self):
        for method in ('parkingNonce(uint256)', 'custodyEpoch(uint256)'):
            with self.subTest(method=method):
                selected, before = self.observe()
                prior = self.reader.uint('principal_exit', method, 7)
                self.put('principal_exit', method, prior + 1, 7)
                self.assertNotEqual(before['controls'], M.observe(self.reader, selected, self.f.gov)['controls'])
                self.put('principal_exit', method, prior, 7)
        selected, before = self.observe()
        self.q.physical_liquidities[123] = self.reader.uint('position_manager', 'getPositionLiquidity(uint256)', 123) + 1
        self.assertNotEqual(before['controls'], M.observe(self.reader, selected, self.f.gov)['controls'])
        selected, before = self.observe()
        shares = self.reader.uint('vault', 'bucketTotalShares(uint256)', 7)
        self.put('vault', 'bucketTotalShares(uint256)', shares + 1, 7)
        self.assertNotEqual(before['controls'], M.observe(self.reader, selected, self.f.gov)['controls'])

    def test_residual_close_refuses_absent_residual_even_if_idle_is_available(self):
        self.q.secondary = 0;self.q.secondary_count = 0
        with self.assertRaisesRegex(ManagementBlocked, 'no registered residual') as failed:
            self.observe('close_residual')
        self.assertEqual('residual_absent', failed.exception.code)
        self.observe('park')

    def test_resume_preserves_exact_pool_floor_deadline_and_has_no_extra_hash_argument(self):
        self.parked();self.q.config[5] = 0
        selected, snapshot = self.observe('resume', minimumLiquidity='77')
        signature, arguments, data = M.call_spec(selected, snapshot, H)
        self.assertEqual('resume(uint256,bytes32,uint128,uint256)', signature)
        self.assertEqual({'id': '7', 'pool': self.q.pool, 'minimum': '77', 'deadline': '4180'}, arguments)
        self.assertEqual([7, int(self.q.pool, 16), 77, 4180], [int(w, 16) for w in decode_words('0x' + data[10:])])
        self.assertEqual(0, int(snapshot['controls']['destination_configuration'][5], 16))

    def test_resume_rejects_wrong_state_unpaused_requirement_disabled_operations_or_bad_alias(self):
        with self.assertRaises(ValueError):self.observe('resume')
        self.parked();self.put('access', 'paused()', 1)
        with self.assertRaises(ValueError):self.observe('resume')
        self.put('access', 'paused()', 0);self.q.config[6] = 0
        with self.assertRaisesRegex(ManagementBlocked, 'operations') as failed:self.observe('resume')
        self.assertEqual('destination_operations_disabled', failed.exception.code)
        self.q.config[6] = 1;self.q.overrides[self.c['vault'], 'poolBucket(bytes32)'] = [f'{8:064x}']
        with self.assertRaises((ValueError, RpcError)):self.observe('resume')

    def test_resume_outage_refuses_and_does_not_turn_into_forced_or_raw_close(self):
        self.parked();self.rpc.price_failure = True
        with self.assertRaises(RpcError):self.observe('resume')
        self.assertEqual([], self.rpc.simulations)
        self.assertFalse(any('send' in method.lower() for method, _ in self.rpc.calls))

    def test_resume_may_select_another_same_pair_pool_without_consuming_another_bucket_slot(self):
        self.parked()
        config = list(self.q.config);config[2] = 500;config[5] = 0
        destination = '0x' + keccak256(bytes.fromhex(''.join(f'{value:064x}' for value in config[:5]))).hex()
        for method in ('accounting(bytes32)', 'get(bytes32)'):
            self.put('pools', method, config, destination)
        self.put('vault', 'poolBucket(bytes32)', 0, destination)
        self.put('portfolio_policy', 'controlFingerprint(bytes32)', H, destination)
        self.put('state_view', 'getSlot0(bytes32)', [2**96, 0, 0, 500], destination)
        self.put('strategy', 'target(bytes32)', [self.q.lower % 2**256, self.q.upper, 2**96], destination)
        selected, snapshot = self.observe('resume', destination_pool=destination)
        self.assertEqual('0', snapshot['controls']['destination_reservation'])
        self.assertEqual(['7'], snapshot['controls']['registered_buckets'])
        signature, arguments, _ = M.call_spec(selected, snapshot, H)
        self.assertEqual(destination, arguments['pool'])
        self.put('vault', 'poolBucket(bytes32)', 8, destination)
        with self.assertRaisesRegex(ManagementBlocked, 'another bucket') as failed:
            self.observe('resume', destination_pool=destination)
        self.assertEqual('destination_reserved_elsewhere', failed.exception.code)

    def test_resume_no_principal_is_a_precise_blocker_without_inventing_funds(self):
        self.parked();self.q.position[2] = self.q.position[3] = 0
        with self.assertRaises(ManagementBlocked) as failed:
            self.observe('resume')
        self.assertEqual('no_resume_principal', failed.exception.code)
        self.assertFalse(self.rpc.simulations)

    def test_resume_rejects_noncanonical_target_or_out_of_width_custody_getters(self):
        self.parked()
        for target in ([2**255, 120, 2**96], [0, 0, 2**96],
                [self.q.lower % 2**256, self.q.upper, 0],
                [(self.q.lower + 1) % 2**256, self.q.upper, 2**96]):
            with self.subTest(target=target):
                self.put('strategy', 'target(bytes32)', target, self.q.pool)
                with self.assertRaisesRegex(RpcError, 'geometry'):
                    self.observe('resume')
        self.put('strategy', 'target(bytes32)', [self.q.lower % 2**256, self.q.upper, 2**96], self.q.pool)
        self.put('principal_exit', 'parkingNonce(uint256)', 2**64, 7)
        with self.assertRaisesRegex(RpcError, 'uint64'):
            self.observe('resume')

    def test_resume_price_rounds_are_market_but_policy_identity_and_routes_are_controls(self):
        self.parked();selected, before = self.observe('resume')
        self.put('oracle', 'priceBounds(address)', [10**18, 10**18, '0x' + '56' * 32], addr(20))
        after = M.observe(self.reader, selected, self.f.gov)
        self.assertNotEqual(before['market_observations'], after['market_observations'])
        self.assertEqual(before['controls'], after['controls'])
        self.put('oracle', 'activePolicy(address)', '0x' + '56' * 32, addr(20))
        self.assertNotEqual(before['controls'], M.observe(self.reader, selected, self.f.gov)['controls'])

    def test_malformed_parameters_and_uint_widths_fail_without_rpc(self):
        valid = {'bucket': '7', 'minimum0': '0', 'minimum1': '0'}
        for change in ({'minimum0': -1}, {'minimum1': '01'}, {'minimum0': str(2**128)},
                {'bucket': '0'}, {'bucket': 7}, {'recipient': addr(2)}):
            with self.subTest(change=change):
                supplied = dict(valid);supplied.update(change)
                with self.assertRaises(ValueError):M.validate('park', supplied)
        with self.assertRaises(ValueError):self.selected('resume', minimumLiquidity='0')
        with self.assertRaises(ValueError):self.selected('resume', destination_pool='0x' + '0' * 64)
        with self.assertRaises(ValueError):M.validate('move_funds', valid)

    def test_fixed_identity_and_governance_authority_are_checked_by_real_base(self):
        self.put('access', 'governance()', addr(41))
        with self.assertRaises(ValueError):self.observe()
        self.put('access', 'governance()', self.f.gov)
        self.put('principal_exit', 'currentZZZ()', addr(21))
        with self.assertRaises(ValueError):self.observe()
