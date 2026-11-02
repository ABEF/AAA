"""Stored Policy1 evidence and transient report faults; no RPC, signer or service."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.health import confirmation_reasons, execution_reasons, observe_confirmation_health
from keeper.monitor import Keeper
from keeper.operation_review import review
from tests_python.test_keeper_policy_v6 import PolicyRPC
from tests_python.test_keeper_portfolio_policy import PortfolioRPC
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class KeeperPolicyIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.rpc=PolicyRPC(Path(self.tmp.name)/'source6.json')
        self.rpc.physical_side=self.rpc.reference=0
        self.k=Keeper(self.rpc.cfg,rpc=self.rpc);self.k.save()

    def health(self, keeper=None, rpc=None):
        keeper,rpc=keeper or self.k,rpc or self.rpc
        with patch('keeper.monitor.time.time',return_value=rpc.now):
            policy=observe_confirmation_health(keeper)
        self.assertEqual('observed_this_cycle',policy['state'])
        return {'health_schema':2,'rebalance_confirmation_health':{
            'version':3,'check_interval_seconds':240,'policy':policy}}

    def reasons(self,data,config=None):
        return confirmation_reasons(data,config or self.rpc.cfg,now=self.rpc.now,max_age=600)

    def test_corrupt_missing_or_misbound_idle_policy_cannot_report_healthy(self):
        data=self.health();self.assertEqual([],self.reasons(data))
        current=data['rebalance_confirmation_health']['policy']['last_observed']['maintenance_policy']
        faults=[None,{}, {**current,'version':True},{**current,'domain':'entry'},
            {**current,'maximum_idle_bps':True},{**current,'maximum_idle_bps':4001},
            {**current,'maximum_idle_bps':-1},{**current,'revision':0},
            {**current,'revision':2**64},{**current,'revision':True},
            {**current,'fingerprint':'0x'+'f'*64},{**current,'policy':self.rpc.contracts['vault']},
            {**current,'revision':current['revision']+1},{**current,'unknown':1}]
        for fault in faults:
            bad=copy.deepcopy(data)
            bad['rebalance_confirmation_health']['policy']['last_observed']['maintenance_policy']=fault
            with self.subTest(fault=fault):
                self.assertIn('confirmation_observation_maintenance_policy_invalid',self.reasons(bad))
        bad=copy.deepcopy(data)
        del bad['rebalance_confirmation_health']['policy']['last_observed']['maintenance_policy']
        self.assertIn('confirmation_observation_maintenance_policy_invalid',self.reasons(bad))

    def test_valid_governed_bounds_and_historical_profile_remain_supported(self):
        for idle in (0,4000):
            self.rpc.policy.set('maintenance',(idle,2**64-1))
            with self.subTest(idle=idle):self.assertEqual([],self.reasons(self.health()))
        old=PortfolioRPC(Path(self.tmp.name)/'source5.json');keeper=Keeper(old.cfg,rpc=old)
        data=self.health(keeper,old)
        self.assertNotIn('maintenance_policy',data['rebalance_confirmation_health']['policy']['last_observed'])
        self.assertEqual([],self.reasons(data,old.cfg))

    def test_malformed_nested_health_config_is_rejected_without_attribute_errors(self):
        data=self.health()
        for field in ('contracts','code_hashes'):
            for value in (None,[],False,'invalid'):
                config=copy.deepcopy(self.rpc.cfg);config[field]=value
                with self.subTest(field=field,value=value):
                    self.assertEqual(['confirmation_health_profile_invalid'],self.reasons(data,config))
                    self.assertEqual(['execution_health_profile_invalid'],
                        execution_reasons(data,config,now=self.rpc.now,max_age=600))

    def test_unknown_financial_idle_policy_prevents_principal_simulation_but_not_harvest(self):
        original=self.rpc.call;reads=0;simulations=[]
        def fail_second_read(method,params):
            nonlocal reads
            if method=='eth_call' and 'from' in params[0]:simulations.append(params[0]['data'])
            if (method=='eth_call' and params[0]['to']==self.rpc.policy.target and
                    params[0]['data']==calldata('maintenancePolicy()')):
                reads+=1
                if reads==2:raise RpcError('PRIVATE-POLICY-FAILURE')
            return original(method,params)
        self.rpc.call=fail_second_read;before=self.k.path.read_bytes()
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            result=review(self.rpc.cfg,[7],rpc=self.rpc,simulate=True,now=lambda:self.rpc.now)
        rows={row['operation']:row for row in result['operations']}
        self.assertEqual('unavailable',rows['compound']['state'])
        self.assertEqual(['maintenance_idle_policy_unavailable'],rows['compound']['reasons'])
        self.assertEqual('not_requested',rows['compound']['simulation']['state'])
        self.assertEqual('simulated',rows['harvest']['state'])
        self.assertEqual([calldata('collectFees(uint256,uint256)',7,self.rpc.now+180)],simulations)
        self.assertEqual(before,self.k.path.read_bytes());self.assertNotIn('PRIVATE-POLICY-FAILURE',json.dumps(result))

    def test_healthy_financial_policy_keeps_principal_report_available_without_writes(self):
        before=self.k.path.read_bytes()
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            result=review(self.rpc.cfg,[7],rpc=self.rpc,now=lambda:self.rpc.now)
        row=next(row for row in result['operations'] if row['operation']=='compound')
        self.assertEqual('observed_eligible',row['state'])
        self.assertEqual(1700,row['checks']['financial_limits']['value']['post_deployment_idle_ceiling']['bps'])
        self.assertEqual(before,self.k.path.read_bytes())


if __name__=='__main__':unittest.main()
