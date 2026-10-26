"""Scheduling liveness with funded reserves; inert RPC fixtures, never a signer."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, NATIVE_ASSET
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError
import tests_python.test_keeper as fixtures


class KeeperBuybackFairnessTests(unittest.TestCase):
    def setUp(self):
        f = fixtures.PoolKeeperTests('runTest')
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f, self.rpc, self.cfg = f, f.rpc, f.cfg
        self.cfg.update(accounting_version=3, fee_intake_version=1,
                        maintenance={'compound': False, 'harvest': False})
        runtime = '0x'+keccak256(bytes.fromhex('6000')).hex()
        self.cfg['code_hashes'] = {'vault': runtime, 'fees': runtime}
        f.config_words[0] = 0
        f.pool = '0x'+keccak256(bytes.fromhex(''.join(f'{n:064x}' for n in f.config_words[:5]))).hex()
        f.group_words = f.group_words[:8]
        f.group_words[0] = int(f.pool, 16)
        f.ids = [7]
        self.balances = {NATIVE_ASSET: 1000, fixtures.C: 1000}
        original = self.rpc.call
        def current_call(method, params):
            if method == 'eth_call' and 'from' not in params[0]:
                data = params[0]['data']
                versions = {calldata('ACCOUNTING_VERSION()'): 3, calldata('FEE_INTAKE_VERSION()'): 1}
                if data in versions: return '0x'+f'{versions[data]:064x}'
                if data[:10] == calldata('buybackBalance(address)', fixtures.B)[:10]:
                    asset = '0x'+f'{int(data[10:], 16):040x}'
                    value = self.balances.get(asset, 0)
                    if isinstance(value, Exception): raise value
                    return '0x'+f'{value:064x}'
            return original(method, params)
        self.rpc.call = current_call
        self.cfg['buybacks'] = [self.task(NATIVE_ASSET), self.task(fixtures.C)]
        self.k = f.k = Keeper(self.cfg, rpc=self.rpc)

    def task(self, asset):
        return {'token': asset, 'amount': '100', 'pool_id': self.f.pool}

    def cycles(self, count):
        actions = []
        for _ in range(count):
            self.rpc.now += 600
            def accepted_submission(*args, **kwargs):
                # Real submit() persists the scheduling cursor with the intent;
                # model only that persistence, without signing or pending funds.
                self.k.save()
                return True
            with patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                    patch.object(self.k, 'submit', side_effect=accepted_submission) as submit:
                self.k.cycle()
            self.assertLessEqual(submit.call_count, 1)
            if submit.called: actions.append(submit.call_args.args)
        return actions

    def test_funded_buyback_progresses_during_continuous_rebalancing(self):
        actions = self.cycles(6)
        self.assertIn('buyback', [action[0] for action in actions])
        self.assertIn('vault', [action[0] for action in actions])
        self.assertLessEqual(next(i for i, action in enumerate(actions) if action[0] == 'buyback'), 1)

    def test_perpetually_funded_first_currency_cannot_starve_second(self):
        self.f.rebalance = False
        actions = self.cycles(8)
        currencies = [action[2][0] for action in actions if action[0] == 'buyback']
        self.assertEqual(currencies[:4], [NATIVE_ASSET, fixtures.C, NATIVE_ASSET, fixtures.C])

    def test_busy_conversions_buyback_and_maintenance_all_progress(self):
        def worker(name):
            return SimpleNamespace(enabled=True, key=name,
                scan_once=lambda: self.k.submit(name, 'inert-fixture', (), name))
        self.k.lp_rewards, self.k.royalties = worker('rewards'), worker('royalties')
        actions = self.cycles(12)
        names = [action[0] for action in actions]
        for name in ('rewards', 'royalties', 'vault', 'buyback'):
            self.assertIn(name, names)
        self.assertEqual(names.count('rewards'), 4)
        self.assertEqual(names.count('royalties'), 4)
        self.assertEqual(names.count('vault'), 2)
        self.assertEqual(names.count('buyback'), 2)

    def test_busy_metadata_cannot_displace_every_lp_maintenance_opportunity(self):
        self.k.metadata_enabled = True
        self.k.state['metadata_refresh'] = {'next_first': True}
        with patch.object(self.k, '_refresh_metadata',
                side_effect=lambda: self.k.submit('nft', 'inert-fixture', (), 'metadata')):
            actions = self.cycles(8)
        names = [action[0] for action in actions]
        self.assertEqual(names.count('buyback'), 4)
        self.assertEqual(names.count('nft'), 2)
        self.assertEqual(names.count('vault'), 2)

    def test_empty_task_list_does_not_change_existing_maintenance_order(self):
        self.cfg['buybacks'] = []
        self.assertEqual([action[0] for action in self.cycles(4)], ['vault']*4)
        self.assertNotIn('buyback_cursor', self.k.state)
        self.assertNotIn('buyback_priority', self.k.state)

    def test_pending_receipt_blocks_all_new_actions_and_cursor_changes(self):
        before = copy.deepcopy(self.k.state)
        with patch.object(self.k, 'poll_pending', return_value=True), patch.object(self.k, 'submit') as submit:
            self.k.cycle()
        submit.assert_not_called()
        self.assertEqual(self.k.state, before)

    def test_pause_preparation_and_canonical_lock_never_buy_back(self):
        for paused, preparing, state in ((True, False, 0), (False, True, 0), (False, False, 1)):
            self.f.paused, self.f.preparing, self.f.canonical_state = paused, preparing, state
            self.k.state['buyback_priority'] = True
            with self.subTest(paused=paused, preparing=preparing, state=state):
                self.assertEqual(self.cycles(1), [])
                self.assertTrue(self.k.state['buyback_priority'])

    def test_broken_currency_does_not_block_healthy_reserve(self):
        self.k.state['buyback_priority'] = True
        self.balances[NATIVE_ASSET] = RpcError('fixture unavailable')
        action = self.cycles(1)[0]
        self.assertEqual((action[0], action[2][0]), ('buyback', fixtures.C))
        self.assertEqual(self.k.blocked_actions, 1)

    def test_failed_submission_guard_does_not_skip_other_currency(self):
        self.k.state['buyback_priority'] = True
        def submit(name, signature, args, key):
            return name == 'buyback' and args[0] == fixtures.C
        with patch.object(self.k, 'submit', side_effect=submit) as submitted:
            self.k.cycle()
        self.assertEqual([entry.args[2][0] for entry in submitted.call_args_list], [NATIVE_ASSET, fixtures.C])

    def test_unfunded_buybacks_leave_maintenance_available(self):
        self.k.state['buyback_priority'] = True
        self.balances = {}
        self.assertEqual(self.cycles(1)[0][0], 'vault')

    def test_zero_pool_id_is_allowed_for_direct_zzz_burn_task(self):
        # This is scheduling only. The real Buyback contract omits the route
        # when input is its fixed ZZZ; its actual burn still needs qualification.
        zero_pool = '0x'+'00'*32
        self.cfg['buybacks'] = [{**self.task(fixtures.C), 'pool_id': zero_pool}]
        self.k = self.f.k = Keeper(self.cfg, rpc=self.rpc)
        self.f.ids = []
        action = self.cycles(1)[0]
        self.assertEqual(action, ('buyback', 'execute(address,uint256,bytes32,uint256)',
            (fixtures.C, 100, zero_pool, self.rpc.now+180), 'buyback:'+fixtures.C))

    def test_submission_error_with_saved_intent_stops_all_other_actions(self):
        self.k.state['buyback_priority'] = True
        def unresolved(*args, **kwargs):
            self.k.state['pending'] = {'hash': fixtures.H}
            raise RpcError('fixture post-intent failure')
        with patch.object(self.k, 'submit', side_effect=unresolved) as submitted, self.assertRaises(RpcError):
            self.k.cycle()
        self.assertEqual(submitted.call_count, 1)
        self.assertEqual(self.k.state['pending'], {'hash': fixtures.H})

    def test_rotation_and_phase_survive_restart_without_resetting_journal(self):
        self.k.state['buyback_priority'] = True
        self.assertEqual(self.cycles(1)[0][2][0], NATIVE_ASSET)
        before = copy.deepcopy(self.k.state)
        restarted = Keeper(self.cfg, rpc=self.rpc)
        self.assertEqual(restarted.state, before)
        self.k = self.f.k = restarted
        following = self.cycles(2)
        self.assertEqual(next(a[2][0] for a in following if a[0] == 'buyback'), fixtures.C)

    def test_historical_state_without_optional_cursors_is_accepted(self):
        self.k.state.pop('buyback_priority', None)
        self.k.state.pop('buyback_cursor', None)
        self.k.save()
        self.k = self.f.k = Keeper(self.cfg, rpc=self.rpc)
        self.assertEqual(self.cycles(2)[1][0], 'buyback')

    def test_invalid_phase_and_cursor_state_are_rejected(self):
        baseline = copy.deepcopy(self.k.state)
        for field, values in (('buyback_priority', (1, 'true', None)),
                              ('buyback_cursor', (True, -1, 0.5, '0', 33))):
            for value in values:
                with self.subTest(field=field, value=value):
                    self.k.state = {**baseline, field: value}
                    self.k.save()
                    with self.assertRaises(ValueError): Keeper(self.cfg, rpc=self.rpc)

    def test_invalid_buyback_tasks_fail_before_any_new_submission(self):
        valid = self.task(NATIVE_ASSET)
        malformed = (None, {}, [None], [{**valid, 'amount': True}], [{**valid, 'amount': 0}],
                     [{**valid, 'amount': 1 << 256}],
                     [{**valid, 'pool_id': 'not-a-pool'}], [{**valid, 'token': 'not-a-token'}],
                     [valid, valid], [self.task('0x'+f'{i:040x}') for i in range(1, 34)])
        for value in malformed:
            with self.subTest(value=value):
                self.cfg['buybacks'] = value
                with patch.object(self.k, 'submit') as submit, self.assertRaises(ValueError):
                    self.k.cycle()
                submit.assert_not_called()

    def test_valid_pending_recovery_is_not_blocked_by_new_invalid_configuration(self):
        self.k.state['pending'] = {'key': 'buyback:'+NATIVE_ASSET, 'nonce': 7, 'value': 0,
            'to': fixtures.B, 'data': calldata('collectFees(uint256,uint256)', 7, 123),
            'day': '2026-10-26', 'hash': fixtures.H}
        self.k.save()
        pending = copy.deepcopy(self.k.state['pending'])
        self.cfg['buybacks'] = [None]
        restarted = Keeper(self.cfg, rpc=self.rpc)
        with patch.object(restarted, 'poll_pending', return_value=True), patch.object(restarted, 'submit') as submit:
            restarted.cycle()
        submit.assert_not_called()
        self.assertEqual(restarted.state['pending'], pending)


if __name__ == '__main__': unittest.main()
