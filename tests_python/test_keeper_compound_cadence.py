"""Fresh maintenance eligibility is contract-authoritative; inert RPC transcripts only."""
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, NATIVE_ASSET
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError
from tests_python import test_holder_exit_profile as H
from tests_python import test_keeper as K
from tests_python import test_keeper_native as N
from tests_python import test_local_position_services as L


class KeeperCompoundCadenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = H.HolderExitKeeperTests('runTest')
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.k, self.cfg, self.rpc = self.fixture.k, self.fixture.cfg, self.fixture.rpc
        self.base = self.fixture.f.base
        self.base.ids = [7]; self.base.rebalance = False
        self.k.maintenance = {'compound': True, 'harvest': False}
        self.budget = '0x'+'92'*20
        self.cfg['idle_compounding_budget'] = self.budget
        self.cfg['code_hashes']['idle_compounding_budget'] = '0x'+keccak256(bytes.fromhex('6000')).hex()
        self.version, self.ready = 2, 1
        self.bound_budget = int(self.budget,16)
        self.bound_vault = int(self.k.contracts['vault'],16)
        self.runtime, self.ready_response = '0x6000', None
        original = self.rpc.call
        def call(method, params):
            if method == 'eth_getCode' and params[0] == self.budget:
                self.rpc.calls.append((method,params)); return self.runtime
            if method == 'eth_call' and 'from' not in params[0]:
                target, data = params[0]['to'], params[0]['data']
                values = {}
                if target == self.k.contracts['vault']:
                    values[calldata('migrationBudget()')] = self.bound_budget
                if target == self.budget:
                    values.update({calldata('vault()'): self.bound_vault,
                        calldata('IDLE_COMPOUNDING_VERSION()'): self.version,
                        calldata('compoundReady(uint256)',7): self.ready})
                if data in values:
                    self.rpc.calls.append((method,params))
                    if data == calldata('compoundReady(uint256)',7) and self.ready_response is not None:
                        if isinstance(self.ready_response,Exception): raise self.ready_response
                        return self.ready_response
                    return '0x'+f'{values[data]:064x}'
            return original(method,params)
        self.rpc.call = call

    def cycle(self):
        with patch('keeper.monitor.time.time',side_effect=lambda:self.rpc.now), \
                patch.object(self.k,'submit',return_value=True) as submit:
            self.k.cycle()
        return submit

    def helper_calls(self, signature):
        return [params for method,params in self.rpc.calls if method == 'eth_call' and
            params[0]['to'] == self.budget and params[0]['data'] == calldata(signature,*((7,) if 'uint256' in signature else ()))]

    def assert_compound(self, submit):
        submit.assert_called_once_with('compounder','compound(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'compound:7')

    def test_due_compound_authenticates_exact_version_binding_pin_and_boolean_once(self):
        self.assert_compound(self.cycle())
        self.assertEqual(1,len([1 for method,args in self.rpc.calls if method == 'eth_getCode' and args == [self.budget,'latest']]))
        for signature in ('vault()','IDLE_COMPOUNDING_VERSION()','compoundReady(uint256)'):
            self.assertEqual(1,len(self.helper_calls(signature)),signature)
        self.assertFalse(self.helper_calls('lastCompound(uint256)'))

    def test_recent_rebalance_and_other_keeper_compound_are_authoritatively_deferred(self):
        for journal_key in ('rebalance:7','compound:7'):
            with self.subTest(journal_key=journal_key):
                self.k.state['last'][journal_key] = self.rpc.now-10000
                self.ready = 0  # The pinned contract observes the newer shared checkpoint.
                self.cycle().assert_not_called()
        self.ready = 1
        self.assert_compound(self.cycle())

    def test_local_optional_interval_is_an_additional_exact_boundary_not_a_rebalance_lock(self):
        self.k.maintenance['compound_interval_seconds'] = 3600
        self.k.state['last']['compound:7'] = self.rpc.now-3599
        self.cycle().assert_not_called()
        self.assertFalse(self.helper_calls('compoundReady(uint256)'))
        self.k.state['last']['compound:7'] -= 1
        self.assert_compound(self.cycle())
        self.base.rebalance = True
        self.k.state['last']['compound:7'] = self.rpc.now
        self.cycle().assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'rebalance:7')

    def test_contract_eligibility_covers_idle_and_reserve_compounding(self):
        self.k.maintenance.update(compound_idle=True,compound_interval_seconds=600,
            compound_thresholds={NATIVE_ASSET:'100',K.C:'100'})
        self.base.reserves[NATIVE_ASSET] = 0
        self.base.group_words[2] = 100
        self.ready = 0; self.cycle().assert_not_called()
        self.ready = 1; self.assert_compound(self.cycle())
        self.assertFalse(self.helper_calls('lastCompound(uint256)'))

    def test_not_due_threshold_does_not_read_optional_budget(self):
        self.k.maintenance['minimum_compound_units'] = 1000
        self.cycle().assert_not_called()
        self.assertFalse(self.helper_calls('compoundReady(uint256)'))
        self.assertFalse(self.helper_calls('IDLE_COMPOUNDING_VERSION()'))

    def test_ineligible_or_failed_maintenance_preserves_independently_due_hourly_harvest(self):
        self.k.maintenance['harvest'] = True
        for response in (0,RpcError('synthetic unavailable eligibility')):
            with self.subTest(response=type(response).__name__):
                self.ready = 0 if response == 0 else 1
                self.ready_response = response if isinstance(response,Exception) else None
                self.cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',
                    (7,self.rpc.now+180),'harvest:7')

    def test_bad_runtime_binding_version_or_boolean_never_submits_compound(self):
        cases = (('runtime','0x6001'),('bound_budget',int(K.A,16)),
            ('bound_vault',int(K.A,16)),('version',1),('version',3),('ready',2))
        for name,value in cases:
            with self.subTest(name=name,value=value):
                old = getattr(self,name); setattr(self,name,value)
                self.cycle().assert_not_called(); setattr(self,name,old)
        self.assertIsNone(self.k.state['pending'])

    def test_missing_reviewed_configuration_defers_compound_without_breaking_due_harvest(self):
        self.k.maintenance['harvest'] = True
        for parent,key in ((self.cfg,'idle_compounding_budget'),(self.cfg['code_hashes'],'idle_compounding_budget')):
            with self.subTest(key=key):
                old = parent.pop(key)
                self.cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',
                    (7,self.rpc.now+180),'harvest:7')
                parent[key] = old

    def test_malformed_abi_is_not_coerced_into_eligibility_or_fallback_work(self):
        self.k.maintenance['harvest'] = True
        self.ready_response = '0x'
        self.cycle().assert_not_called()
        self.assertEqual(1,self.k.skipped_buckets)

    def test_pending_recovery_precedes_every_new_eligibility_read(self):
        self.k.state['pending'] = {'key':'saved'}
        with patch.object(self.k,'poll_pending',return_value=True):
            self.cycle().assert_not_called()
        self.assertFalse(self.helper_calls('compoundReady(uint256)'))

    def test_historical_ordinary_compound_never_reads_new_capability(self):
        for factory in (K.PoolKeeperTests,N.NativeKeeperTests,L.LocalPositionKeeperTests):
            with self.subTest(profile=factory.__name__):
                f = factory('runTest'); f.setUp(); self.addCleanup(f.doCleanups)
                base = f if factory is K.PoolKeeperTests else f.f if factory is N.NativeKeeperTests else f.base
                base.ids = [7]; base.rebalance = False
                base.reserves[K.C] = 100
                f.k.maintenance = {'compound':True,'harvest':False}
                base.invoke().assert_called_once()
                selectors = {calldata('compoundReady(uint256)',7)[:10],calldata('IDLE_COMPOUNDING_VERSION()')[:10]}
                self.assertFalse(any(method == 'eth_call' and args[0]['data'][:10] in selectors for method,args in f.rpc.calls))


if __name__ == '__main__': unittest.main()
