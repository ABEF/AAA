"""Inert keeper fixtures: collect fees independently from price-based maintenance.

No token movements, signer, existing journal or external RPC are used. These
checks exercise scheduling/error boundaries, not live harvest qualification.
"""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError
import tests_python.test_keeper as fixtures


class KeeperHarvestIsolationTests(unittest.TestCase):
    def setUp(self):
        f = fixtures.PoolKeeperTests('runTest')
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f, self.cfg, self.rpc = f, f.cfg, f.rpc
        self.cfg.update(accounting_version=3, fee_intake_version=1,
                        maintenance={'compound': False, 'harvest': True, 'harvest_interval_seconds': 1})
        runtime = '0x'+keccak256(bytes.fromhex('6000')).hex()
        self.cfg['code_hashes'] = {'vault': runtime, 'fees': runtime}
        f.config_words[0] = 0
        f.pool = '0x'+keccak256(bytes.fromhex(''.join(f'{n:064x}' for n in f.config_words[:5]))).hex()
        f.group_words = f.group_words[:8]
        f.group_words[0] = int(f.pool, 16)
        f.ids = [7]
        original = self.rpc.call
        def current_call(method, params):
            if method == 'eth_call' and 'from' not in params[0]:
                versions = {calldata('ACCOUNTING_VERSION()'): 3, calldata('FEE_INTAKE_VERSION()'): 1}
                if params[0]['data'] in versions: return '0x'+f'{versions[params[0]["data"]]:064x}'
            return original(method, params)
        self.rpc.call = current_call
        self.k = f.k = Keeper(self.cfg, rpc=self.rpc)

    def _view_fault(self, signature, *, delay=0):
        original = self.k.view
        def read(name, sig, *args):
            if sig == signature:
                self.rpc.now += delay
                raise RpcError('synthetic unavailable maintenance dependency')
            return original(name, sig, *args)
        return read

    def _cycle(self, **patches):
        with patch('keeper.monitor.time.time', side_effect=lambda: self.rpc.now), \
                patch.object(self.k, 'submit', return_value=True) as submit:
            if 'view' in patches:
                with patch.object(self.k, 'view', side_effect=patches['view']): self.k.cycle()
            else:
                self.k.cycle()
        return submit

    def _assert_harvest(self, submit):
        submit.assert_called_once_with('vault', 'collectFees(uint256,uint256)',
            (7, self.rpc.now+180), 'harvest:7')
        self.assertEqual(self.k.skipped_buckets, 0)

    def test_strategy_price_failure_does_not_block_due_fee_harvest(self):
        submit = self._cycle(view=self._view_fault('needsRebalance(uint256)'))
        self._assert_harvest(submit)
        self.assertEqual(self.k.blocked_actions, 1)

    def test_rebalance_simulation_failure_falls_back_to_independent_harvest(self):
        accepted = []
        def submit(name, signature, args, key):
            if signature.startswith('rebalance('): raise RpcError('synthetic maintenance slippage')
            accepted.append(signature)
            return True
        with patch.object(self.k, 'submit', side_effect=submit) as calls, \
                patch('keeper.monitor.time.time', side_effect=lambda: self.rpc.now):
            self.k.cycle()
        self.assertEqual([call.args[1] for call in calls.call_args_list],
            ['rebalance(uint256,uint128,uint256)', 'collectFees(uint256,uint256)'])
        self.assertEqual(accepted, ['collectFees(uint256,uint256)'])
        self.assertEqual(self.k.blocked_actions, 1)

    def test_compound_reserve_read_failure_does_not_block_due_harvest(self):
        self.f.rebalance = False
        self.k.maintenance['compound'] = True
        submit = self._cycle(view=self._view_fault('compoundBalance(uint256,address)'))
        self._assert_harvest(submit)

    def test_adaptive_range_failure_does_not_block_due_harvest(self):
        self.k.adaptive_range_enabled = True
        with patch.object(self.k, '_adaptive_range_target', side_effect=RpcError('synthetic range prices')):
            submit = self._cycle()
        self._assert_harvest(submit)

    def test_slow_failed_maintenance_uses_fresh_harvest_deadline(self):
        submit = self._cycle(view=self._view_fault('needsRebalance(uint256)', delay=240))
        self._assert_harvest(submit)

    def test_bucket_identity_failure_never_uses_harvest_fallback(self):
        with patch.object(self.k, '_bucket', side_effect=RpcError('synthetic bad pool identity')):
            submit = self._cycle()
        submit.assert_not_called()
        self.assertEqual(self.k.skipped_buckets, 1)

    def test_disabled_or_not_due_harvest_is_not_forced_after_price_failure(self):
        for enabled, interval in ((False, 1), (True, 14400)):
            with self.subTest(enabled=enabled, interval=interval):
                self.k.maintenance.update(harvest=enabled, harvest_interval_seconds=interval)
                self.k.state['last']['harvest:7'] = self.rpc.now
                submit = self._cycle(view=self._view_fault('needsRebalance(uint256)'))
                submit.assert_not_called()

    def test_global_pause_and_canonical_lock_still_block_harvest(self):
        for paused, canonical in ((True, 0), (False, 1), (False, 2), (False, 3), (False, 4)):
            self.f.paused, self.f.canonical_state = paused, canonical
            with self.subTest(paused=paused, canonical=canonical):
                self._cycle().assert_not_called()

    def test_preparation_retains_existing_harvest_only_behavior(self):
        self.f.preparing = True
        with patch.object(self.k, '_adaptive_range_target') as range_policy:
            self._assert_harvest(self._cycle())
        range_policy.assert_not_called()

    def test_pending_recovery_runs_before_maintenance_or_harvest(self):
        with patch.object(self.k, 'poll_pending', return_value=True), \
                patch.object(self.k, '_bucket') as bucket:
            self._cycle().assert_not_called()
        bucket.assert_not_called()

    def test_post_intent_maintenance_error_stops_every_new_action(self):
        pending = {'hash': fixtures.H}
        def submit(*args):
            self.k.state['pending'] = dict(pending)
            raise RpcError('synthetic post-intent failure')
        with patch.object(self.k, 'submit', side_effect=submit) as calls, \
                patch('keeper.monitor.time.time', side_effect=lambda: self.rpc.now), \
                self.assertRaises(RpcError):
            self.k.cycle()
        calls.assert_called_once()
        self.assertEqual(self.k.state['pending'], pending)

    def test_post_intent_harvest_error_is_not_swallowed_by_bucket_handler(self):
        self.f.rebalance = False
        pending = {'hash': fixtures.H}
        def submit(*args):
            self.k.state['pending'] = dict(pending)
            raise ValueError('synthetic pending write outcome')
        with patch.object(self.k, 'submit', side_effect=submit) as calls, \
                patch('keeper.monitor.time.time', side_effect=lambda: self.rpc.now), \
                self.assertRaises(ValueError):
            self.k.cycle()
        calls.assert_called_once()
        self.assertEqual(self.k.state['pending'], pending)

    def test_both_conversion_workers_rethrow_any_saved_pending_intent(self):
        for key in ('lp_conversion', 'royalty_conversion'):
            for error in (RpcError, ValueError):
                self.k.state['pending'] = None
                def failed_worker():
                    self.k.state['pending'] = {'hash': fixtures.H}
                    raise error('synthetic conversion post-intent failure')
                worker = SimpleNamespace(key=key, scan_once=failed_worker)
                with self.subTest(key=key, error=error.__name__), self.assertRaises(error):
                    self.k._convert_rewards(worker)
                self.assertEqual(self.k.state['pending'], {'hash': fixtures.H})

    def test_conversion_read_failure_before_intent_still_defers_only_that_job(self):
        def failed_worker(): raise RpcError('synthetic unavailable conversion source')
        worker = SimpleNamespace(key='lp_conversion', scan_once=failed_worker)
        self.assertFalse(self.k._convert_rewards(worker))
        self.assertIsNone(self.k.state['pending'])
        self.assertEqual(self.k.blocked_actions, 1)

    def test_fallback_retains_actual_simulation_and_gas_cap(self):
        self.cfg['max_gas_limit'] = 1
        with patch.object(self.k, 'view', side_effect=self._view_fault('needsRebalance(uint256)')), \
                patch('keeper.monitor.time.time', side_effect=lambda: self.rpc.now), \
                patch('keeper.monitor.subprocess.run') as signer:
            self.k.cycle()
        methods = [method for method, params in self.rpc.calls]
        self.assertIn('eth_estimateGas', methods)
        self.assertEqual(self.k.blocked_actions, 2)  # Price read plus gas cap.
        signer.assert_not_called()
        self.assertIsNone(self.k.state['pending'])

    def test_fallback_failed_harvest_simulation_never_releases_a_new_intent(self):
        original = self.rpc.call
        def call(method, params):
            if method == 'eth_call' and 'from' in params[0]:
                raise RpcError('synthetic failed fee collection')
            return original(method, params)
        with patch.object(self.k, 'view', side_effect=self._view_fault('needsRebalance(uint256)')), \
                patch.object(self.rpc, 'call', side_effect=call), \
                patch('keeper.monitor.time.time', side_effect=lambda: self.rpc.now), \
                patch('keeper.monitor.subprocess.run') as signer:
            self.k.cycle()
        self.assertEqual(self.k.skipped_buckets, 1)
        self.assertEqual(self.k.blocked_actions, 1)
        self.assertIsNone(self.k.state['pending'])
        signer.assert_not_called()


if __name__ == '__main__': unittest.main()
