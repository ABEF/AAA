"""Interval crossings during a real cycle; inert RPC and temporary state only."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_python import test_hourly_harvest as harvest_fixture
from tests_python import test_keeper_compound_cadence as compound_fixture
from tests_python.test_exact_lp_profile7 import Fresh7KeeperRPC
from keeper.monitor import Keeper
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class CurrentCycleRPC(Fresh7KeeperRPC):
    """Extend the existing accounting7 pinned wire to actual worker discovery."""
    def __init__(self,path):
        super().__init__(path)
        self.physical_side=self.reference=0;self.cfg['maintenance'].update(compound=False,harvest=True)

    def call(self,method,params):
        if method=='eth_blockNumber':return '0x64'
        if method=='eth_getCode':return self.code(params[0])
        if method=='eth_call' and 'from' not in params[0]:
            additional={calldata('keepers(address)',self.cfg['sender']):self.authorized,
                calldata('bucketCount()'):1,calldata('bucketAt(uint256)',0):7}
            if params[0]['data'] in additional:return '0x'+f'{additional[params[0]["data"]]:064x}'
            if len(params)==1 or params[-1]=='latest':
                params=[params[0],{'blockHash':'0x'+'ab'*32,'requireCanonical':True}]
        return super().call(method,params)


class KeeperMaintenanceClockTests(unittest.TestCase):
    def fixture(self,compound=False):
        cls=compound_fixture.KeeperCompoundCadenceTests if compound else harvest_fixture.HourlyHarvestTests
        f=cls('runTest');f.setUp();self.addCleanup(f.doCleanups)
        return f

    def run_cycle(self,k,rpc):
        with patch('keeper.monitor.time.time',side_effect=lambda:rpc.now),\
                patch.object(k,'submit',return_value=True) as submit,\
                patch('keeper.monitor.subprocess.run',side_effect=AssertionError('signer')):
            k.cycle()
        return submit

    def test_hourly_harvest_becoming_due_during_healthy_maintenance_is_not_delayed(self):
        f=self.fixture();k,rpc=f.k,f.fixture.rpc
        k.state['last']['harvest:7']=rpc.now-3590
        old=copy.deepcopy(k.state['last']);original=k._rebalance_due
        def slow(*args,**kwargs):
            result=original(*args,**kwargs);rpc.now+=20;return result
        with patch.object(k,'_rebalance_due',side_effect=slow):submit=self.run_cycle(k,rpc)
        submit.assert_called_once_with('vault','collectFees(uint256,uint256)',
            (7,rpc.now+180),'harvest:7')
        self.assertEqual(old,k.state['last']);self.assertIsNone(k.state['pending'])
        self.assertEqual({},k.state['spent'])

    def test_hourly_harvest_becoming_due_during_price_fault_remains_independent(self):
        f=self.fixture();k,rpc=f.k,f.fixture.rpc
        k.state['last']['harvest:7']=rpc.now-3590
        def slow(*args,**kwargs):
            rpc.now+=20;raise RpcError('inert failed price-dependent maintenance')
        with patch.object(k,'_rebalance_due',side_effect=slow):submit=self.run_cycle(k,rpc)
        submit.assert_called_once_with('vault','collectFees(uint256,uint256)',
            (7,rpc.now+180),'harvest:7')
        self.assertEqual(1,k.blocked_actions);self.assertEqual(0,k.skipped_buckets)

    def test_compound_local_interval_crossed_during_reserve_read_uses_fresh_head(self):
        f=self.fixture(compound=True);k,rpc=f.k,f.rpc
        k.maintenance['compound_interval_seconds']=3600
        k.state['last']['compound:7']=rpc.now-3590
        original=k.view;delayed=False
        def read(name,signature,*args):
            nonlocal delayed
            value=original(name,signature,*args)
            if signature=='compoundBalance(uint256,address)' and not delayed:
                rpc.now+=20;delayed=True
            return value
        with patch.object(k,'view',side_effect=read):submit=self.run_cycle(k,rpc)
        submit.assert_called_once_with('compounder','compound(uint256,uint128,uint256)',
            (7,1,rpc.now+180),'compound:7')
        self.assertTrue(f.helper_calls('compoundReady(uint256)'))
        self.assertIsNone(k.state['pending']);self.assertEqual({},k.state['spent'])

    def test_new_harvest_clock_failure_never_falls_back_to_earlier_due_head(self):
        f=self.fixture();k,rpc=f.k,f.fixture.rpc
        k.state['last']['harvest:7']=rpc.now-3600
        original=k._rebalance_due
        def slow(*args,**kwargs):
            result=original(*args,**kwargs)
            k._head=lambda:(_ for _ in ()).throw(RpcError('inert clock unavailable'))
            return result
        with patch.object(k,'_rebalance_due',side_effect=slow):submit=self.run_cycle(k,rpc)
        submit.assert_not_called();self.assertEqual(1,k.skipped_buckets)
        self.assertIsNone(k.state['pending']);self.assertEqual({},k.state['spent'])

    def test_retreat_at_harvest_clock_refuses_without_using_old_deadline(self):
        f=self.fixture();k,rpc=f.k,f.fixture.rpc
        k.state['last']['harvest:7']=rpc.now-3600
        original=k._rebalance_due
        def retreat(*args,**kwargs):
            result=original(*args,**kwargs);rpc.now-=1;return result
        with patch.object(k,'_rebalance_due',side_effect=retreat):submit=self.run_cycle(k,rpc)
        submit.assert_not_called();self.assertEqual(1,k.skipped_buckets)
        self.assertIsNone(k.state['pending'])

    def test_compound_clock_failure_can_yield_to_later_healthy_harvest_clock(self):
        f=self.fixture(compound=True);k,rpc=f.k,f.rpc
        k.maintenance.update(harvest=True,compound_interval_seconds=3600)
        k.state['last'].update({'harvest:7':rpc.now-3590,'compound:7':rpc.now-3590})
        original_view,original_head=k.view,k._head;fail_next=False;delayed=False
        def read(name,signature,*args):
            nonlocal fail_next,delayed
            result=original_view(name,signature,*args)
            if signature=='compoundBalance(uint256,address)' and not delayed:
                rpc.now+=20;delayed=True;fail_next=True
            return result
        def head():
            nonlocal fail_next
            if fail_next:
                fail_next=False;raise RpcError('inert transient compound clock failure')
            return original_head()
        with patch.object(k,'view',side_effect=read),patch.object(k,'_head',side_effect=head):
            submit=self.run_cycle(k,rpc)
        submit.assert_called_once_with('vault','collectFees(uint256,uint256)',
            (7,rpc.now+180),'harvest:7')
        self.assertEqual(1,k.blocked_actions);self.assertEqual(0,k.skipped_buckets)

    def test_current_clock_does_not_override_onchain_compound_ineligibility(self):
        f=self.fixture(compound=True);k,rpc=f.k,f.rpc
        k.maintenance['compound_interval_seconds']=3600
        k.state['last']['compound:7']=rpc.now-3600;f.ready=0
        submit=self.run_cycle(k,rpc)
        submit.assert_not_called();self.assertTrue(f.helper_calls('compoundReady(uint256)'))
        self.assertIsNone(k.state['pending'])

    def test_pending_recovery_precedes_new_clock_reads_and_any_operation(self):
        f=self.fixture();k,rpc=f.k,f.fixture.rpc
        k.state['pending']={'key':'inert saved intent'}
        original=copy.deepcopy(k.state)
        with patch.object(k,'poll_pending',return_value=True),\
                patch.object(k,'_head',side_effect=AssertionError('new read before recovery')):
            submit=self.run_cycle(k,rpc)
        submit.assert_not_called();self.assertEqual(original,k.state)

    def test_current_accounting7_worker_harvests_after_interval_crosses(self):
        with tempfile.TemporaryDirectory() as directory:
            rpc=CurrentCycleRPC(Path(directory)/'current7.json');k=Keeper(rpc.cfg,rpc=rpc)
            k.state['last']['harvest:7']=rpc.now-3590
            original=k._rebalance_due
            def slow(*args,**kwargs):
                result=original(*args,**kwargs);rpc.now+=20;return result
            with patch.object(k,'_rebalance_due',side_effect=slow):submit=self.run_cycle(k,rpc)
            submit.assert_called_once_with('vault','collectFees(uint256,uint256)',
                (7,rpc.now+180),'harvest:7')
            self.assertEqual(7,k.accounting_version);self.assertEqual(5,k.custody_version)
            self.assertEqual(3,k.rebalance_confirmation.version)
            self.assertEqual(0,k.skipped_buckets);self.assertEqual(0,k.blocked_actions)


if __name__=='__main__':unittest.main()
