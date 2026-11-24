"""NEW preflight composition checks; reuse fixture builders, never old test bodies.

Real Keeper admission, exact LP graph observer and preflight run with inert
canonical DTOs. No network, signer, service or existing journal is touched.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.ops import preflight
from tests_python.test_exact_lp_profile7 import Fresh7KeeperRPC
from tests_python import test_keeper_execution_price as execution_fixtures
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class KeeperPreflightRoutingTests(unittest.TestCase):
    def fixture(self, version=3):
        if version == 3:
            rpc, cfg, _ = execution_fixtures.KeeperExecutionPriceTests.fixture(self)
        else:
            directory = tempfile.TemporaryDirectory()
            self.addCleanup(directory.cleanup)
            rpc = Fresh7KeeperRPC(Path(directory.name) / 'state.json')
            cfg = rpc.cfg
        cfg.update(reviewed_for_live_use=True, receipt_fee_policy='included')
        calls = []
        original = rpc.call

        def call(method, params):
            calls.append((method, copy.deepcopy(params)))
            if method == 'eth_getTransactionCount':
                return '0x0'
            if method == 'eth_getCode' and params[1] == 'latest':
                return rpc.code(params[0])
            if method == 'eth_call' and params[0]['data'] == calldata('keepers(address)', cfg['sender']):
                return '0x' + f'{1:064x}'
            value = original(method, params)
            if method == 'eth_getBlockByNumber' and params[0] != 'latest':
                value = {**value, 'number': params[0]}
            return value

        rpc.call = call
        keeper = Keeper(cfg, rpc=rpc)
        keeper.state['next_nonce'] = 0
        keeper.save()
        calls.clear()
        return rpc, cfg, keeper, calls

    def reviewed(self, rpc, cfg, keeper):
        before = keeper.path.read_bytes()
        with patch('keeper.monitor.time.time', return_value=rpc.now), \
                patch('keeper.monitor.run_cast') as signer, \
                patch.object(Keeper, 'save', side_effect=AssertionError('Preflight must not save')), \
                patch.object(Keeper, 'submit', side_effect=AssertionError('Preflight must not submit')), \
                patch.object(Keeper, 'poll_pending', side_effect=AssertionError('Preflight must not recover')):
            result = preflight(cfg, rpc=rpc)
        signer.assert_not_called()
        self.assertEqual(before, keeper.path.read_bytes())
        return result

    def test_matching_runtime_with_wrong_router_parent_cannot_pass_preflight(self):
        rpc, cfg, keeper, calls = self.fixture()
        rpc.overrides[cfg['contracts']['balancing_router'], 'liquidityManager()'] = [f'{1:064x}']
        result = self.reviewed(rpc, cfg, keeper)
        self.assertFalse(result['ok'], result)
        self.assertIn('lp_routing_unavailable', result['reasons'])
        self.assertEqual('unavailable', result['lp_routing']['state'])
        self.assertTrue(any(method == 'eth_getCode' and isinstance(params[1], dict)
                            for method, params in calls))

    def test_fresh_lp2_and_lp3_validate_real_observer_without_execution(self):
        for version in (2, 3):
            with self.subTest(version=version):
                rpc, cfg, keeper, calls = self.fixture(version)
                result = self.reviewed(rpc, cfg, keeper)
                self.assertTrue(result['ok'], result)
                self.assertEqual({'version': version, 'state': 'validated',
                    'scope': 'fresh_canonical_latest_routing_not_inclusion_guarantee'}, result['lp_routing'])
                self.assertFalse(any(method.startswith('eth_send') or method == 'eth_estimateGas'
                                     for method, _ in calls))
                self.assertFalse(any(method == 'eth_call' and 'from' in params[0]
                                     for method, params in calls))

    def test_pending_intent_never_acquires_new_routing_dependency(self):
        rpc, cfg, keeper, calls = self.fixture()
        keeper.state['pending'] = {'nonce': 0, 'to': cfg['contracts']['vault'],
            'data': calldata('collectFees(uint256,uint256)', 7, rpc.now + 180),
            'value': 0, 'day': '2026-11-24', 'key': 'harvest:7', 'hash': None}
        keeper.save()
        with patch.object(Keeper, '_validate_lp_routing', side_effect=AssertionError('Pending recovery is independent')) as routing:
            result = self.reviewed(rpc, cfg, keeper)
        routing.assert_not_called()
        self.assertFalse(result['ok'])
        self.assertIn('pending_intent_requires_reconciliation', result['reasons'])
        self.assertEqual({'version': 3, 'state': 'pending_recovery',
            'scope': 'routing_not_observed_while_recovery_pending'}, result['lp_routing'])

    def test_routing_fault_is_sanitized_and_cannot_look_ready(self):
        rpc, cfg, keeper, calls = self.fixture()
        original = rpc.call

        def fault(method, params):
            if method == 'eth_call' and params[0]['to'] == cfg['contracts']['balancing_router']:
                raise RpcError('https://PRIVATE-RPC.invalid/DO-NOT-EXPORT')
            return original(method, params)

        rpc.call = fault
        result = self.reviewed(rpc, cfg, keeper)
        self.assertFalse(result['ok'])
        self.assertEqual('unavailable', result['lp_routing']['state'])
        self.assertNotIn('PRIVATE-RPC', json.dumps(result))
        self.assertNotIn('DO-NOT-EXPORT', json.dumps(result))
        self.assertIn('lp_routing_unavailable', result['reasons'])

