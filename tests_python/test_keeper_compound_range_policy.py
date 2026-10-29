"""Physical-range service gating: deterministic pinned reads, no actual worker."""
import copy
import hashlib
from pathlib import Path
import tempfile
import time
import subprocess
import unittest
from unittest.mock import patch

from keeper.compound_policy import classify_range, observe
from keeper.monitor import Keeper, NATIVE_ASSET, CONFIRMATION_STATE, CONFIRMATION_RESETS, CONFIRMATION_CLEARS
from tests_python import test_keeper_rebalance_confirmation as confirmation_fixtures
from tests_python import test_keeper_outside_schedule as schedule_fixtures
from tests_python import test_keeper as basic
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError
from zzz_ops.tick_math import sqrt_price_at_tick


def words(*values):
    return [f'{value % (1 << 256):064x}' for value in values]


class PhysicalTranscript:
    def __init__(self, path):
        self.now = int(time.time()); self.calls = []
        names = ('access', 'vault', 'strategy', 'fees', 'compounder', 'buyback', 'pools',
                 'principal_exit', 'liquidity', 'pool_manager', 'state_view')
        self.contracts = {name: '0x' + f'{i + 1:040x}' for i, name in enumerate(names)}
        self.posm = '0x' + 'd1' * 20; self.zzz = '0x' + 'd2' * 20
        self.pin = '0x' + keccak256(bytes.fromhex('6000')).hex()
        self.cfg = {'chain_id': 1, 'sender': basic.A, 'contracts': self.contracts,
                    'accounting_version': 4, 'fee_intake_version': 1, 'maintenance_policy_version': 2,
                    'maintenance': {'compound': False, 'harvest': True},
                    'code_hashes': {name: self.pin for name in names},
                    'state_path': str(path), 'confirmations': 2,
                    'receipt_fee_policy': 'included', 'max_gas_limit': 100000,
                    'max_gas_price_wei': 100, 'max_transaction_cost_wei': 1000000,
                    'max_daily_cost_wei': 10000000}
        self.config = [0, int(self.zzz, 16), 100, 10, 0, 1, 1, 2500, 0, 0, 0, 43200, 0, 0]
        self.pool = '0x' + keccak256(bytes.fromhex(''.join(words(*self.config[:5])))).hex()
        self.position = [int(self.pool, 16), 123, 0, 0, 10**18, 1 << 96, self.now - 1800, 1]
        self.lower, self.upper, self.tick, self.manual = -100, 100, 0, 0
        self.overrides = {}; self.code_overrides = {}; self.canonical_changed = False

    def code(self, target): return self.code_overrides.get(target, '0x6000')

    def read(self, target, signature, *args, count=1):
        self.calls.append((target, signature, args))
        if (target, signature) in self.overrides:
            value = self.overrides[target, signature]
            if isinstance(value, Exception): raise value
            return value
        c = self.contracts
        if signature == 'access()': return words(int(c['access'], 16))
        if target == c['access'] and signature == 'module(bytes32)':
            for role, label in (('vault', 'ZZZVault'), ('strategy', 'ZZZStrategy'),
                                ('pools', 'ZZZPoolRegistry'), ('liquidity', 'ZZZLiquidityManager')):
                if args == ('0x' + keccak256(label.encode()).hex(),): return words(int(c[role], 16))
        if signature == 'MAINTENANCE_POLICY_VERSION()': return words(2)
        if signature == 'stateView()': return words(int(c['state_view'], 16))
        if signature == 'poolManager()': return words(int(c['pool_manager'], 16))
        if signature == 'positionManager()': return words(int(self.posm, 16))
        if signature == 'group(uint256)': return words(*self.position)
        if signature in ('get(bytes32)', 'accounting(bytes32)'): return words(*self.config)
        if signature == 'poolBucket(bytes32)': return words(7)
        if signature == 'ticks(uint256)': return words(self.lower, self.upper)
        if signature == 'getPoolAndPositionInfo(uint256)':
            info = ((int(self.pool, 16) >> 56) << 56) | ((self.upper % (1 << 24)) << 32) | ((self.lower % (1 << 24)) << 8)
            return words(*self.config[:5], info)
        if signature == 'ownerOf(uint256)': return words(int(c['vault'], 16))
        if signature == 'getPositionLiquidity(uint256)': return words(500)
        if signature == 'getSlot0(bytes32)': return words(sqrt_price_at_tick(self.tick), self.tick, 0, 100)
        if signature == 'rangeUpdatePending(uint256)': return words(self.manual)
        raise AssertionError((target, signature, args, count))

    def call(self, method, params):
        if method == 'eth_getCode':
            if not isinstance(params[1], dict): raise AssertionError('Unpinned code read')
            return self.code(params[0])
        if method == 'eth_getBlockByNumber':
            changed = self.canonical_changed and params[0] != 'latest'
            return {'number': '0x64', 'hash': '0x' + ('cd' if changed else 'ab') * 32,
                    'timestamp': hex(self.now)}
        if method == 'eth_call':
            if not isinstance(params[1], dict) or params[1].get('requireCanonical') is not True:
                raise AssertionError('Unpinned physical call')
            target, data = params[0]['to'], params[0]['data']
            candidates = [('access()', ()), ('MAINTENANCE_POLICY_VERSION()', ()), ('stateView()', ()),
                          ('poolManager()', ()), ('positionManager()', ()), ('group(uint256)', (7,)),
                          ('get(bytes32)', (self.pool,)), ('accounting(bytes32)', (self.pool,)),
                          ('poolBucket(bytes32)', (self.pool,)), ('ticks(uint256)', (123,)),
                          ('getPoolAndPositionInfo(uint256)', (123,)), ('ownerOf(uint256)', (123,)),
                          ('getPositionLiquidity(uint256)', (123,)), ('getSlot0(bytes32)', (self.pool,)),
                          ('rangeUpdatePending(uint256)', (7,))]
            candidates += [('module(bytes32)', ('0x' + keccak256(label.encode()).hex(),))
                           for label in ('ZZZVault', 'ZZZStrategy', 'ZZZPoolRegistry', 'ZZZLiquidityManager')]
            for signature, args in candidates:
                if calldata(signature, *args) == data:
                    return '0x' + ''.join(self.read(target, signature, *args))
        raise AssertionError((method, params))


class KeeperCompoundRangePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.rpc = PhysicalTranscript(Path(self.tmp.name) / 'state.json')
        self.k = Keeper(self.rpc.cfg, rpc=self.rpc)
        self.item = {'compound_thresholds': {NATIVE_ASSET: 1, self.rpc.zzz: 1}}

    def physical(self):
        return observe(self.rpc.read, self.rpc.code, contracts=self.rpc.contracts,
                       code_hashes=self.rpc.cfg['code_hashes'], bucket=7)

    def due(self):
        with patch.object(self.k, '_compound_ready', return_value=True):
            return self.k._compound_due(7, [NATIVE_ASSET, self.rpc.zzz], [1, 0], self.item,
                                        self.rpc.now, words(*self.rpc.position))

    def test_outside_before_hard_rebalance_cooldown_waits_even_when_budget_ready(self):
        self.rpc.tick = self.rpc.upper
        self.assertFalse(self.due())

    def test_manual_width_pending_before_cooldown_waits_even_inside(self):
        self.rpc.manual = 1
        self.assertFalse(self.due())

    def test_inside_without_width_change_retains_independent_compound_eligibility(self):
        self.assertTrue(self.due())

    def test_budget_not_ready_short_circuits_expensive_physical_observation(self):
        with patch.object(self.k, '_compound_ready', return_value=False) as budget, \
                patch.object(self.k, '_compound_policy_status', return_value={'allowed': True}) as physical:
            self.assertFalse(self.k._compound_due(7, [NATIVE_ASSET, self.rpc.zzz], [1, 0], self.item,
                                                self.rpc.now, words(*self.rpc.position)))
        budget.assert_called_once_with(7); physical.assert_not_called()

    def test_range_classification_preserves_exact_inclusive_lower_exclusive_upper(self):
        for tick, expected in ((-101, False), (-100, True), (99, True), (100, False)):
            with self.subTest(tick=tick):
                value = classify_range(lower=-100, upper=100, tick=tick, range_update_pending=False)
                self.assertEqual(expected, value['allowed'])
        self.assertEqual('waiting_range_change', classify_range(
            lower=-100, upper=100, tick=0, range_update_pending=True)['status'])

    def test_physical_observation_has_no_cooldown_or_oracle_eligibility_read(self):
        proof = self.physical()
        self.assertTrue(proof['allowed']); self.assertEqual(123, proof['lp_token_id'])
        self.assertFalse(any(signature in ('needsRebalance(uint256)', 'referenceX96(address,address)',
                                          'rebalanceReady(uint256)') for _, signature, _ in self.rpc.calls))

    def test_valid_mixed_case_abi_words_have_identical_pool_identity(self):
        self.rpc.overrides[self.rpc.contracts['pools'], 'get(bytes32)'] = [word.upper() for word in words(*self.rpc.config)]
        self.assertTrue(self.physical()['allowed'])

    def test_downward_crossing_uses_stored_tick_instead_of_recomputed_price_tick(self):
        self.rpc.tick = -101
        self.rpc.overrides[self.rpc.contracts['state_view'], 'getSlot0(bytes32)'] = words(sqrt_price_at_tick(-100), -101, 0, 100)
        self.assertEqual('waiting_outside_range', self.physical()['status'])

    def test_runtime_binding_and_pool_identity_faults_are_unavailable(self):
        for role, signature, value in (('strategy', 'access()', words(99)),
                                       ('liquidity', 'stateView()', words(99)),
                                       ('vault', 'poolBucket(bytes32)', words(8)),
                                       ('strategy', 'rangeUpdatePending(uint256)', words(2))):
            with self.subTest(signature=signature):
                self.rpc.overrides[ self.rpc.contracts[role], signature] = value
                with self.assertRaises(ValueError): self.physical()
                self.rpc.overrides.clear()
        self.rpc.code_overrides[self.rpc.contracts['liquidity']] = '0x6001'
        with self.assertRaises(ValueError): self.physical()

    def test_inconsistent_slot0_packed_lp_or_custody_never_guesses_inside(self):
        changes = (('state_view', 'getSlot0(bytes32)', words(sqrt_price_at_tick(20), 0, 0, 100)),
                   ('liquidity', 'ticks(uint256)', words(-101, 100)),
                   (self.rpc.posm, 'ownerOf(uint256)', words(99)),
                   (self.rpc.posm, 'getPositionLiquidity(uint256)', words(0)))
        for role, signature, value in changes:
            with self.subTest(signature=signature):
                self.rpc.overrides[self.rpc.contracts.get(role, role), signature] = value
                with self.assertRaises(ValueError): self.physical()
                self.rpc.overrides.clear()

    def test_vault_owns_the_physical_lp_and_manager_ownership_is_rejected(self):
        self.assertTrue(self.physical()['allowed'])
        self.rpc.overrides[self.rpc.posm, 'ownerOf(uint256)'] = words(int(self.rpc.contracts['liquidity'], 16))
        with self.assertRaises(ValueError): self.physical()

    def test_changed_canonical_header_keeps_journal_and_schedules_untouched(self):
        self.k.save(); before = self.k.path.read_bytes(); state = copy.deepcopy(self.k.state)
        self.rpc.canonical_changed = True
        with self.assertRaises(RpcError): self.due()
        self.assertEqual(before, self.k.path.read_bytes()); self.assertEqual(state, self.k.state)

    def test_optional_header_field_variation_does_not_invent_a_reorg(self):
        original = self.rpc.call
        def call(method, params):
            result = original(method, params)
            if method == 'eth_getBlockByNumber' and params[0] == 'latest':
                return {**result, 'totalDifficulty': '0x123'}
            return result
        self.rpc.call = call
        self.assertTrue(self.due())

    def test_final_snapshot_must_still_be_fresh_after_physical_reads(self):
        self.k.save(); before = self.k.path.read_bytes()
        with patch('keeper.monitor.time.time', side_effect=[self.rpc.now, self.rpc.now + 601]), self.assertRaises(RpcError):
            self.due()
        self.assertEqual(before, self.k.path.read_bytes())

    def test_final_canonical_identity_fields_cannot_change_or_be_malformed(self):
        original = self.rpc.call
        for change in ({'number': '0x63'}, {'timestamp': hex(self.rpc.now + 1)},
                       {'hash': None}, {'number': '0x064'}, {'timestamp': True}):
            with self.subTest(change=change):
                def call(method, params):
                    result = original(method, params)
                    return {**result, **change} if method == 'eth_getBlockByNumber' and params[0] != 'latest' else result
                self.rpc.call = call
                with self.assertRaises(RpcError): self.due()
        self.rpc.call = original

    def test_wait_and_observation_failure_still_allow_independent_hourly_harvest(self):
        f = schedule_fixtures.KeeperOutsideScheduleTests('runTest')
        f.setUp(); self.addCleanup(f.doCleanups)
        f.base.group_words[6] = f.rpc.now - 100
        f.k.maintenance.update(compound=True, harvest=True,
            compound_thresholds={NATIVE_ASSET: 1, basic.C: 1})
        for outcome in ({'allowed': False, 'status': 'waiting_outside_range'}, RpcError('inert missing pool observation')):
            with self.subTest(outcome=type(outcome).__name__), \
                    patch.object(f.k, '_compound_ready', return_value=True), \
                    patch.object(f.k, '_compound_policy_status', create=True) as physical:
                if isinstance(outcome, Exception): physical.side_effect = outcome
                else: physical.return_value = outcome
                f.cycle().assert_called_once_with('vault', 'collectFees(uint256,uint256)',
                                                (7, f.rpc.now + 180), 'harvest:7')

    def test_historical_policy_does_not_call_the_new_physical_reader(self):
        self.k.maintenance_policy_version = 1
        self.rpc.tick = self.rpc.upper
        self.assertTrue(self.due())
        self.assertEqual([], self.rpc.calls)

    def test_policy2_lp0_without_reviewed_physical_readers_is_unavailable_without_rewriting(self):
        cfg = copy.deepcopy(self.rpc.cfg)
        cfg['state_path'] = str(Path(self.tmp.name) / 'historical-lp0.json')
        for role in ('liquidity', 'pool_manager', 'state_view'):
            cfg['contracts'].pop(role); cfg['code_hashes'].pop(role)
        self.k = Keeper(cfg, rpc=self.rpc)
        self.assertEqual(0, self.k.lp_routing_version)
        self.k.save(); before = self.k.path.read_bytes(); state = copy.deepcopy(self.k.state)
        with self.assertRaises(RpcError): self.due()
        self.assertEqual(before, self.k.path.read_bytes()); self.assertEqual(state, self.k.state)

    def test_pending_recovery_precedes_any_new_physical_observation(self):
        self.k.state['pending'] = {'hash': basic.H}
        with patch.object(self.k, 'poll_pending', return_value=True), \
                patch.object(self.k, '_compound_policy_status') as physical:
            self.k.cycle()
        physical.assert_not_called()

    def test_local_health_source_identity_includes_the_new_policy_helper(self):
        from keeper.health import source_hashes
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(hashlib.sha256((root / 'keeper/compound_policy.py').read_bytes()).hexdigest(),
                         source_hashes()['keeper/compound_policy.py'])

    def test_submit_rechecks_range_after_simulation_before_persisting_an_intent(self):
        self.k.rpc = basic.FakeRpc()
        self.k.state['next_nonce'] = 7
        self.k.save(); before = self.k.path.read_bytes(); state = copy.deepcopy(self.k.state)
        self.k.live = True
        proofs = [self.physical(), {**self.physical(), 'allowed': False, 'status': 'waiting_outside_range'}]
        with patch.object(self.k, '_validate_accounting_version'), \
                patch.object(self.k, '_defer_for_lifecycle', return_value=False), \
                patch.object(self.k, '_validate_checkpoint'), \
                patch.object(self.k, '_validate_code_hashes'), \
                patch.object(self.k, '_compound_policy_status', side_effect=proofs) as physical, \
                patch('subprocess.run') as signer:
            self.assertFalse(self.k.submit('compounder', 'compound(uint256,uint128,uint256)',
                (7, 1, self.rpc.now + 180), 'compound:7'))
        self.assertEqual(2, physical.call_count); signer.assert_not_called()
        self.assertEqual(before, self.k.path.read_bytes()); self.assertEqual(state, self.k.state)

    def test_submit_waits_before_simulation_for_outside_or_manual_range(self):
        self.k.save(); before = self.k.path.read_bytes()
        for status in ('waiting_outside_range', 'waiting_range_change'):
            with self.subTest(status=status), \
                    patch.object(self.k, '_validate_accounting_version'), \
                    patch.object(self.k, '_defer_for_lifecycle', return_value=False), \
                    patch.object(self.k, '_compound_policy_status', return_value={'allowed': False, 'status': status}), \
                    patch('subprocess.run') as signer:
                self.assertFalse(self.k.submit('compounder', 'compound(uint256,uint128,uint256)',
                    (7, 1, self.rpc.now + 180), 'compound:7'))
                signer.assert_not_called()
        self.assertEqual(before, self.k.path.read_bytes())

    def test_valid_inside_submission_retains_original_nonce_budget_and_signer_boundary(self):
        self.k.rpc = basic.FakeRpc()
        self.k.state['next_nonce'] = 7
        self.k.live = True
        self.k.cast = '/mock/cast'; self.k.keystore = Path('/mock/key'); self.k.password = Path('/mock/pass')
        proof = self.physical()
        def sign(command, **kwargs):
            self.assertIsNotNone(self.k.state['pending'])
            self.assertIsNone(self.k.state['pending']['hash'])
            self.assertEqual(7, self.k.state['pending']['nonce'])
            return subprocess.CompletedProcess(command, 0, basic.H, '')
        with patch.object(self.k, '_validate_accounting_version'), \
                patch.object(self.k, '_defer_for_lifecycle', return_value=False), \
                patch.object(self.k, '_validate_checkpoint'), \
                patch.object(self.k, '_validate_code_hashes'), \
                patch.object(self.k, '_compound_policy_status', return_value=proof) as physical, \
                patch('subprocess.run', side_effect=sign) as signer:
            self.assertTrue(self.k.submit('compounder', 'compound(uint256,uint128,uint256)',
                (7, 1, self.rpc.now + 180), 'compound:7'))
        self.assertEqual(2, physical.call_count); signer.assert_called_once()
        self.assertEqual(basic.H, self.k.state['pending']['hash'])
        self.assertEqual({}, self.k.state['spent'])


class KeeperCompoundConfirmationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.f = confirmation_fixtures.KeeperConfirmationTests('runTest')
        self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.k, self.rpc = self.f.k, self.f.rpc
        self.f.cycle()
        self.f.record = [self.f.identity, self.rpc.now - 480, self.rpc.now, 1]
        self.k._confirmation_seen_buckets.add(7)
        self.rpc.now += 60
        self.proof = {**classify_range(lower=-100, upper=100, tick=0, range_update_pending=False),
                      'bucket_id': 7, 'pool_id': self.f.base.pool, 'lp_token_id': 1,
                      'last_rebalance': self.rpc.now - 43200, 'block_number': 100,
                      'block_hash': basic.H, 'block_timestamp': self.rpc.now}
        self.physical_patch = patch.object(self.k, '_compound_policy_status', side_effect=lambda bucket: copy.deepcopy(self.proof))
        self.physical_patch.start(); self.addCleanup(self.physical_patch.stop)

    def allowed(self):
        with patch('keeper.monitor.time.time', side_effect=lambda: self.rpc.now):
            return self.k._compound_policy_allowed(7)

    def empty(self): self.f.record = [0, 0, 0, 0]

    def ack(self, *, awaiting=False):
        self.k.state.setdefault(CONFIRMATION_CLEARS, {})['7'] = {
            'number': 99, 'hash': basic.H, 'timestamp': self.rpc.now - 1,
            'nonce': 6, 'awaiting_healthy_read': awaiting}

    def enable_compound(self):
        self.k.maintenance.update(compound=True, harvest=False,
            compound_thresholds={NATIVE_ASSET: 1, basic.C: 1})

    def test_observed_inside_blocks_old_window_reuse_after_price_recovers(self):
        self.assertFalse(self.allowed())
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7', self.k.state.get(CONFIRMATION_STATE, {}))
        self.rpc.now += 60
        self.f.side = 1
        self.f.cycle().assert_called_once_with('rebalance_confirmation', 'resetObservation(uint256)', (7,), 'rebalance_reset:7')

    def test_opposite_side_evidence_also_invalidates_the_old_same_side_window(self):
        self.proof.update(classify_range(lower=-100, upper=100, tick=100, range_update_pending=False))
        self.assertFalse(self.allowed())
        self.assertTrue(self.k.state.get(CONFIRMATION_RESETS, {}).get('7', False))
        self.assertNotIn('7', self.k.state.get(CONFIRMATION_STATE, {}))

    def test_same_side_outside_or_empty_evidence_does_not_pay_or_mark_a_clear(self):
        self.proof.update(classify_range(lower=-100, upper=100, tick=-101, range_update_pending=False))
        for empty in (False, True):
            with self.subTest(empty=empty):
                if empty: self.empty()
                self.k.save(); disk = self.k.path.read_bytes()
                self.assertFalse(self.allowed())
                self.assertFalse(self.k.state.get(CONFIRMATION_RESETS, {}))
                self.assertEqual(disk, self.k.path.read_bytes())

    def test_late_inside_discovery_hands_nonce_to_the_existing_reset_path(self):
        self.enable_compound()
        with patch.object(self.k, '_compound_ready', return_value=True):
            self.f.cycle().assert_called_once_with('rebalance_confirmation', 'resetObservation(uint256)', (7,), 'rebalance_reset:7')
        self.assertIsNone(self.k.state['pending'])

    def test_empty_inside_schedule_keeps_compound_and_never_pays_a_clear(self):
        self.empty(); self.k.save(); disk = self.k.path.read_bytes()
        self.assertTrue(self.allowed()); self.assertTrue(self.allowed())
        self.assertFalse(self.k.state.get(CONFIRMATION_RESETS, {}))
        self.assertEqual(disk, self.k.path.read_bytes())
        helper_calls = [params for method, params in self.rpc.calls if method == 'eth_call' and
                        params[0]['to'] == self.f.helper]
        self.assertTrue(helper_calls)
        self.assertTrue(all(params[1] == {'blockHash': basic.H, 'requireCanonical': True} for params in helper_calls))

    def test_manual_width_wait_does_not_reset_an_ordinary_sample_as_a_side_effect(self):
        self.proof.update(allowed=False, range_update_pending=True, status='waiting_range_change')
        self.k.save(); disk = self.k.path.read_bytes(); self.rpc.calls.clear()
        self.assertFalse(self.allowed())
        self.assertEqual(disk, self.k.path.read_bytes())
        self.assertFalse(self.k.state.get(CONFIRMATION_RESETS, {}))
        self.assertFalse(any(method == 'eth_call' and params[0]['to'] == self.f.helper for method, params in self.rpc.calls))

    def test_empty_acknowledged_record_never_forces_or_repeats_paid_clears(self):
        self.empty()
        for awaiting in (False, True):
            with self.subTest(awaiting=awaiting):
                self.ack(awaiting=awaiting); self.k.save(); disk = self.k.path.read_bytes()
                self.assertTrue(self.allowed()); self.assertTrue(self.allowed())
                self.assertFalse(self.k.state.get(CONFIRMATION_RESETS, {}))
                self.assertEqual(disk, self.k.path.read_bytes())

    def test_nonempty_foreign_record_overrides_ack_once_and_marker_is_idempotent(self):
        self.ack(); self.k.save()
        self.assertFalse(self.allowed())
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        disk = self.k.path.read_bytes()
        self.assertFalse(self.allowed())
        self.assertEqual(disk, self.k.path.read_bytes())

    def test_same_side_foreign_record_after_ack_still_requires_a_clear(self):
        self.ack()
        self.proof.update(classify_range(lower=-100, upper=100, tick=-101, range_update_pending=False))
        self.assertFalse(self.allowed())
        self.assertTrue(self.k.state.get(CONFIRMATION_RESETS, {}).get('7', False))

    def test_record_fault_marks_only_this_window_and_keeps_independent_harvest(self):
        self.enable_compound(); self.k.maintenance['harvest'] = True
        self.k.state[CONFIRMATION_STATE]['8'] = copy.deepcopy(self.k.state[CONFIRMATION_STATE]['7'])
        other = copy.deepcopy(self.k.state[CONFIRMATION_STATE]['8'])
        self.f.bad[self.f.helper, calldata('observations(uint256)', 7)] = RpcError('inert missing raw evidence')
        with patch.object(self.k, '_compound_ready', return_value=True):
            self.f.cycle().assert_called_once_with('vault', 'collectFees(uint256,uint256)', (7, self.rpc.now + 180), 'harvest:7')
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertEqual(other, self.k.state[CONFIRMATION_STATE]['8'])

    def test_physical_snapshot_fault_invalidates_only_the_known_affected_window(self):
        self.k.state[CONFIRMATION_STATE]['8'] = copy.deepcopy(self.k.state[CONFIRMATION_STATE]['7'])
        other = copy.deepcopy(self.k.state[CONFIRMATION_STATE]['8'])
        with patch.object(self.k, '_compound_policy_status', side_effect=RpcError('inert physical read fault')), self.assertRaises(RpcError):
            self.allowed()
        self.assertTrue(self.k.state.get(CONFIRMATION_RESETS, {}).get('7', False))
        self.assertEqual(other, self.k.state[CONFIRMATION_STATE]['8'])

    def test_unconfigured_lp0_reader_does_not_invalidate_a_healthy_known_window(self):
        self.assertEqual(0, self.k.lp_routing_version)
        self.k.save(); before, disk = copy.deepcopy(self.k.state), self.k.path.read_bytes()
        self.rpc.calls.clear()
        with patch.object(self.k, '_compound_policy_status', side_effect=lambda bucket: Keeper._compound_policy_status(self.k, bucket)), self.assertRaises(RpcError):
            self.allowed()
        self.assertEqual(before, self.k.state); self.assertEqual(disk, self.k.path.read_bytes())
        self.assertEqual([], self.rpc.calls)

    def test_failed_late_reset_is_not_repeated_and_independent_harvest_still_runs(self):
        self.enable_compound(); self.k.maintenance['harvest'] = True
        with patch.object(self.k, '_compound_ready', return_value=True), \
                patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                patch.object(self.k, 'submit', return_value=False) as submit:
            self.k.cycle()
        self.assertEqual(['rebalance_reset:7', 'harvest:7'], [call.args[3] for call in submit.call_args_list])

    def test_same_hash_record_reader_rejects_changed_header_before_any_mutation(self):
        self.k.save(); before, disk = copy.deepcopy(self.k.state), self.k.path.read_bytes()
        original = self.rpc.call
        def call(method, params):
            result = original(method, params)
            return {**result, 'hash': '0x' + 'cd' * 32} if method == 'eth_getBlockByNumber' and params[0] == '0x64' else result
        with patch.object(self.rpc, 'call', side_effect=call), patch('keeper.monitor.time.time', return_value=self.rpc.now), self.assertRaises(RpcError):
            self.k._compound_confirmation_record(7, self.proof)
        self.assertEqual(before, self.k.state); self.assertEqual(disk, self.k.path.read_bytes())

    def test_helper_bindings_record_shape_and_clock_faults_require_scoped_recovery(self):
        changes = (('strategy()', confirmation_fixtures.words(99)),
                   ('REBALANCE_CONFIRMATION_VERSION()', confirmation_fixtures.words(2)),
                   ('observations(uint256)', confirmation_fixtures.words(self.f.identity, 0, self.rpc.now, 1)),
                   ('observations(uint256)', confirmation_fixtures.words(self.f.identity, 1, self.rpc.now, 0)))
        for signature, value in changes:
            with self.subTest(signature=signature):
                self.k.state.pop(CONFIRMATION_RESETS, None)
                self.k.state.setdefault(CONFIRMATION_STATE, {})['7'] = dict(identity=basic.H,
                    observed_at=self.rpc.now - 60, last_checked_at=self.rpc.now - 60,
                    next_check_at=self.rpc.now + 180, execute_after=0)
                args = (7,) if signature == 'observations(uint256)' else ()
                key = self.f.helper, calldata(signature, *args)
                self.f.bad[key] = value
                with self.assertRaises(RpcError): self.allowed()
                self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
                self.f.bad.pop(key)

    def test_proof_before_the_tracked_check_is_a_clock_fault(self):
        self.proof['block_timestamp'] = self.rpc.now - 61
        with self.assertRaises(RpcError): self.allowed()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])

    def test_failed_reset_marker_save_preserves_pending_nonce_and_spend_truth(self):
        self.k.save(); before, disk = copy.deepcopy(self.k.state), self.k.path.read_bytes()
        with patch.object(self.k, 'save', side_effect=OSError('inert failed atomic replace')), self.assertRaises(OSError):
            self.allowed()
        self.assertEqual(before, self.k.state); self.assertEqual(disk, self.k.path.read_bytes())


if __name__ == '__main__': unittest.main()
