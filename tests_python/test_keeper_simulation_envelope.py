"""Read-only provider work is bounded before the keeper can create an intent."""
import copy
import json
import subprocess
import unittest
from unittest.mock import patch

from keeper.monitor import ROYALTY_BATCH
from tests_python import test_keeper as basic
from tests_python import test_keeper_late_job_budget as budget
from zzz_ops.errors import RemoteRPCError


class KeeperSimulationEnvelopeTests(unittest.TestCase):
    def fixture(self):
        return budget.KeeperLateJobBudgetTests.fixture(self)

    def submit(self, keeper, rpc):
        return keeper.submit('vault', 'collectFees(uint256,uint256)',
            (1, rpc.now+180), 'bounded:harvest')

    def test_initial_call_and_estimate_use_cap_but_intent_keeps_padded_estimate(self):
        keeper, rpc, config = self.fixture()
        before = copy.deepcopy(keeper.state['spent'])
        def sign(command, **_):
            pending = json.loads(keeper.path.read_text())['pending']
            self.assertEqual(pending['fee_review']['gas_limit'], 125)
            self.assertEqual(pending['fee_review']['maximum_cost_wei'], 250)
            return subprocess.CompletedProcess(command, 0, json.dumps({'hash': basic.H}), '')
        with patch('keeper.monitor.subprocess.run', side_effect=sign):
            self.assertTrue(self.submit(keeper, rpc))
        calls = [(method, params) for method, params in rpc.calls
            if method == 'eth_estimateGas' or
            method == 'eth_call' and 'from' in params[0]]
        self.assertEqual([method for method, _ in calls], ['eth_call', 'eth_estimateGas'])
        for _, params in calls:
            self.assertEqual(params[0]['gas'], hex(config['max_gas_limit']))
        self.assertEqual(before, keeper.state['spent'])

    def test_invalid_new_work_cap_is_rejected_before_provider_work(self):
        for value in (0, -1, True, 'invalid'):
            with self.subTest(value=value):
                keeper, rpc, config = self.fixture(); config['max_gas_limit'] = value
                before = copy.deepcopy(keeper.state); rpc.calls.clear()
                with patch('keeper.monitor.subprocess.run') as signer:
                    with self.assertRaises(ValueError): self.submit(keeper, rpc)
                    signer.assert_not_called()
                self.assertEqual(rpc.calls, [])
                self.assertEqual(before, keeper.state)
                self.assertFalse(keeper.path.exists())

    def test_provider_refusal_never_retries_with_a_wider_envelope_or_creates_intent(self):
        for failure_method in ('eth_call', 'eth_estimateGas'):
            with self.subTest(method=failure_method):
                keeper, rpc, config = self.fixture(); original = rpc.call
                def call(method, params):
                    if method == failure_method:
                        self.assertEqual(params[0]['gas'], hex(config['max_gas_limit']))
                        rpc.calls.append((method, params))
                        raise RemoteRPCError(method, -32000)
                    return original(method, params)
                rpc.call = call; before = copy.deepcopy(keeper.state)
                with patch('keeper.monitor.subprocess.run') as signer:
                    with self.assertRaises(RemoteRPCError): self.submit(keeper, rpc)
                    signer.assert_not_called()
                self.assertEqual(sum(method == failure_method for method, _ in rpc.calls), 1)
                self.assertEqual(before, keeper.state); self.assertFalse(keeper.path.exists())

    def test_fresh_conversion_capacity_refusal_keeps_prefix_planning_bounded(self):
        for failure_method in ('eth_call', 'eth_estimateGas'):
            with self.subTest(method=failure_method):
                keeper, rpc, config = self.fixture(); keeper.accounting_version = 7
                keeper.contracts['rewards'] = basic.B; original = rpc.call
                def call(method, params):
                    if method == failure_method:
                        self.assertEqual(params[0]['gas'], hex(config['max_gas_limit']))
                        rpc.calls.append((method, params))
                        raise RemoteRPCError(method, -32000)
                    if method == 'eth_call' and 'from' in params[0]:
                        rpc.calls.append((method, params)); return '0x'+f'{1:064x}'
                    return original(method, params)
                rpc.call = call; review = {}; before = copy.deepcopy(keeper.state)
                with patch('keeper.monitor.subprocess.run') as signer:
                    self.assertFalse(keeper.submit('rewards', ROYALTY_BATCH,
                        (basic.C, [1], basic.H, 1, rpc.now+180), 'bounded:convert', capacity_review=review))
                    signer.assert_not_called()
                self.assertEqual(review, {'reason': 'opaque_pre_send_rejection'})
                self.assertEqual(before, keeper.state); self.assertFalse(keeper.path.exists())

    def test_padding_remains_stronger_than_the_initial_execution_envelope(self):
        keeper, rpc, config = self.fixture(); rpc.gas = config['max_gas_limit']*4//5+1
        before = copy.deepcopy(keeper.state)
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit(keeper, rpc)); signer.assert_not_called()
        self.assertEqual(keeper.gas_review_health['last_review']['reason'], 'gas_limit_cap')
        self.assertEqual(before, keeper.state); self.assertFalse(keeper.path.exists())

    def test_pending_record_still_prevents_new_work_even_if_config_cap_is_invalid(self):
        keeper, rpc, config = self.fixture()
        keeper.state['pending'] = {'hash': basic.H, 'evidence': 'historical'}
        config['max_gas_limit'] = 0; before = copy.deepcopy(keeper.state); rpc.calls.clear()
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit(keeper, rpc)); signer.assert_not_called()
        self.assertEqual(rpc.calls, []); self.assertEqual(before, keeper.state)
