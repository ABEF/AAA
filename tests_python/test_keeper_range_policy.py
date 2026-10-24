"""Adaptive range selection uses reviewed source getters, never a local width."""
import copy
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper as fixtures
from zzz_ops.abi import calldata, keccak256
from zzz_ops.range_policy import fingerprint


class KeeperRangePolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PoolKeeperTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.cfg = self.fixture.cfg
        self.cfg['adaptive_range'] = {'enabled': True, 'policy_version': 1}
        self.cfg['code_hashes'] = {name: '0x'+keccak256(bytes.fromhex('6000')).hex() for name in ('strategy','pools')}
        self.cfg['maintenance'] = {'compound': False, 'harvest': False}
        self.k = self.fixture.k = Keeper(self.cfg,rpc=self.fixture.rpc)
        self.fixture.ids = [7]
        self.fixture.rebalance = False
        self.fixture.config_words[7] = 5000
        self.version = 1
        self.orientation = 1
        self.target = 2500
        words = [f'{value:064x}' for value in self.fixture.config_words]
        self.policy = [1,100,1000,600,self.fixture.rpc.now-600,
                       int(fingerprint(words,self.orientation),16),int(fixtures.H,16)]
        original = self.fixture.rpc.call
        def call(method,params):
            if method == 'eth_call' and 'from' not in params[0]:
                selector = params[0]['data'][:10]
                values = {calldata('RANGE_POLICY_VERSION()')[:10]: [self.version],
                          calldata('rangeOrientation(bytes32)',self.fixture.pool)[:10]: [self.orientation],
                          calldata('keeperRangeTarget(bytes32)',self.fixture.pool)[:10]: [self.target],
                          calldata('keeperRangePolicy(bytes32)',self.fixture.pool)[:10]: self.policy}
                if selector in values:
                    self.fixture.rpc.calls.append((method,params))
                    return '0x'+''.join(f'{value:064x}' for value in values[selector])
            return original(method,params)
        self.fixture.rpc.call = call

    def test_only_pool_is_submitted_not_arbitrary_width_or_other_configuration(self):
        self.fixture.invoke().assert_called_once_with('strategy','applyKeeperRange(bytes32)',
            (self.fixture.pool,), 'range_policy:7')
        self.assertIsNone(self.k.state['pending'])

    def test_disabled_historical_profile_never_calls_new_getters(self):
        self.k.adaptive_range_enabled = False
        self.fixture.invoke().assert_not_called()
        selector = calldata('RANGE_POLICY_VERSION()')[:10]
        self.assertFalse(any(method == 'eth_call' and params[0]['data'][:10] == selector
                             for method,params in self.fixture.rpc.calls))

    def test_zero_target_falls_through_to_normal_rebalance(self):
        self.target = 0
        self.fixture.rebalance = True
        self.fixture.invoke().assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
            (7,1,self.fixture.rpc.now+180),'rebalance:7')

    def test_policy_abi_and_bounds_failure_never_reaches_signing_or_other_work(self):
        cases = [('version',2),('orientation',2),('target',3000),('policy',[2,*self.policy[1:]]),
                 ('policy',[1,1000,1000,*self.policy[3:]]),('policy',[*self.policy[:4],1 << 64,*self.policy[5:]])]
        for name,value in cases:
            with self.subTest(name=name,value=value),patch('keeper.monitor.subprocess.run') as signer:
                before = getattr(self,name)
                setattr(self,name,value)
                self.fixture.invoke().assert_not_called()
                signer.assert_not_called()
                setattr(self,name,before)
        self.assertIsNone(self.k.state['pending'])

    def test_configuration_change_or_runtime_mismatch_defers_selection(self):
        self.fixture.config_words[13] += 1
        self.fixture.invoke().assert_not_called()
        self.fixture.config_words[13] -= 1
        self.cfg['code_hashes']['strategy'] = '0x'+'01'*32
        self.fixture.invoke().assert_not_called()

    def test_pause_and_preparation_keep_selection_off(self):
        for name in ('paused','preparing'):
            with self.subTest(name=name):
                self.fixture.rpc.calls.clear()
                setattr(self.fixture,name,True)
                self.fixture.invoke().assert_not_called()
                self.assertFalse(any(method == 'eth_call' and params[0]['data'][:10] == calldata('RANGE_POLICY_VERSION()')[:10]
                                     for method,params in self.fixture.rpc.calls))
                setattr(self.fixture,name,False)

    def test_explicit_version_and_boolean_cannot_be_guessed(self):
        for value in ({'enabled':'false'},{'enabled':1},{'enabled':True},
                      {'enabled':True,'policy_version':True},{'enabled':True,'policy_version':0}):
            with self.subTest(value=value):
                self.cfg['adaptive_range'] = value
                with self.assertRaises(ValueError): Keeper(self.cfg,rpc=self.fixture.rpc)

    def test_preparation_guard_covers_direct_range_submission_before_simulation(self):
        self.fixture.preparing = True
        before = copy.deepcopy(self.k.state)
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.submit('strategy','applyKeeperRange(bytes32)',(self.fixture.pool,),'range:7'))
            signer.assert_not_called()
        self.assertEqual(self.k.state,before)
        self.assertFalse(any(method == 'eth_estimateGas' for method,_ in self.fixture.rpc.calls))


if __name__ == '__main__': unittest.main()
