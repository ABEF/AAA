"""Final gas-budget review for non-LP jobs; inert signer/RPC only."""
import copy
import datetime as dt
import json
import subprocess
import unittest
from unittest.mock import patch

from tests_python import test_keeper as basic
from zzz_ops.rpc import RpcError


class KeeperLateJobBudgetTests(unittest.TestCase):
    def fixture(self):
        fixture = basic.KeeperTests('runTest')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.enable_test_signer()
        keeper, rpc = fixture.k, fixture.rpc
        keeper._validate_accounting_version = lambda: None
        keeper._validate_checkpoint = lambda: None
        keeper._defer_for_lifecycle = lambda *_: False
        rpc.now = int(dt.datetime(2026, 11, 10, 23, 59, 59, tzinfo=dt.timezone.utc).timestamp())
        clock = patch('keeper.monitor.time.time', side_effect=lambda: rpc.now)
        clock.start(); self.addCleanup(clock.stop)
        return keeper, rpc, fixture.cfg

    @staticmethod
    def after_balance(rpc, effect):
        original = rpc.call
        def call(method, params):
            result = original(method, params)
            if method == 'eth_getBalance': effect()
            return result
        rpc.call = call

    @staticmethod
    def submit(keeper, rpc, buyback=False):
        if buyback:
            return keeper.submit('buyback', 'execute(address,uint256,bytes32,uint256)',
                (basic.C, 1, basic.H, rpc.now+180), 'buyback:test')
        return keeper.submit('vault', 'collectFees(uint256,uint256)',
            (1, rpc.now+180), 'harvest:1')

    def test_midnight_uses_new_days_remaining_budget_before_any_intent(self):
        for buyback in (False, True):
            with self.subTest(buyback=buyback):
                keeper, rpc, config = self.fixture()
                keeper.state['spent']['2026-11-11'] = config['max_daily_cost_wei']
                before = copy.deepcopy(keeper.state)
                self.after_balance(rpc, lambda: setattr(rpc, 'now', rpc.now+2))
                with patch('keeper.monitor.subprocess.run', return_value=
                        subprocess.CompletedProcess([], 0, json.dumps({'hash': basic.H}), '')) as signer:
                    self.assertFalse(self.submit(keeper, rpc, buyback))
                    signer.assert_not_called()
                self.assertEqual(before, keeper.state)
                self.assertFalse(keeper.path.exists())

    def test_success_journals_current_day_without_charging_submission(self):
        keeper, rpc, _ = self.fixture()
        self.after_balance(rpc, lambda: setattr(rpc, 'now', rpc.now+2))
        before = copy.deepcopy(keeper.state['spent'])
        def sign(command, **_):
            pending = json.loads(keeper.path.read_text())['pending']
            self.assertEqual(pending['day'], '2026-11-11')
            self.assertIsNone(pending['hash'])
            self.assertEqual(pending['fee_review']['maximum_cost_wei'], 250)
            return subprocess.CompletedProcess(command, 0, json.dumps({'hash': basic.H}), '')
        with patch('keeper.monitor.subprocess.run', side_effect=sign):
            self.assertTrue(self.submit(keeper, rpc))
        self.assertEqual(before, keeper.state['spent'])
        self.assertEqual(keeper.state['pending']['hash'], basic.H)

    def test_retreat_after_nonce_and_funding_reads_stops_before_intent(self):
        keeper, rpc, _ = self.fixture()
        before = copy.deepcopy(keeper.state)
        self.after_balance(rpc, lambda: setattr(rpc, 'now', rpc.now-1))
        with patch('keeper.monitor.subprocess.run', return_value=
                subprocess.CompletedProcess([], 0, json.dumps({'hash': basic.H}), '')) as signer:
            with self.assertRaises(RpcError): self.submit(keeper, rpc)
            signer.assert_not_called()
        self.assertEqual(before, keeper.state)
        self.assertFalse(keeper.path.exists())

    def test_final_head_failure_does_not_sign_using_earlier_budget(self):
        keeper, rpc, _ = self.fixture()
        before = copy.deepcopy(keeper.state); original = rpc.call; funded = False
        def call(method, params):
            nonlocal funded
            if method == 'eth_getBlockByNumber' and funded:
                raise RpcError('inert final head failure')
            result = original(method, params)
            if method == 'eth_getBalance': funded = True
            return result
        rpc.call = call
        with patch('keeper.monitor.subprocess.run', return_value=
                subprocess.CompletedProcess([], 0, json.dumps({'hash': basic.H}), '')) as signer:
            with self.assertRaises(RpcError): self.submit(keeper, rpc)
            signer.assert_not_called()
        self.assertEqual(before, keeper.state)
        self.assertFalse(keeper.path.exists())

    def test_expired_harvest_and_buyback_are_not_sent_after_slow_reads(self):
        for buyback in (False, True):
            with self.subTest(buyback=buyback):
                keeper, rpc, _ = self.fixture(); before = copy.deepcopy(keeper.state)
                self.after_balance(rpc, lambda: setattr(rpc, 'now', rpc.now+181))
                with patch('keeper.monitor.subprocess.run', return_value=
                        subprocess.CompletedProcess([], 0, json.dumps({'hash': basic.H}), '')) as signer:
                    self.assertFalse(self.submit(keeper, rpc, buyback))
                    signer.assert_not_called()
                self.assertEqual(before, keeper.state)
                self.assertFalse(keeper.path.exists())
