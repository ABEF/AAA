"""Confirmed, versioned keeper diagnostics with inert RPC and no signer/network."""
import copy
import datetime as dt
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from keeper.health import HEALTH_SCHEMA, execution_reasons, source_hashes, summary
from keeper.monitor import Keeper
from keeper.ops import health_check
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError
from tests_python import test_execution_quality_profile as quality_fixtures
from tests_python import test_keeper as basic


class KeeperExecutionTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.fixture=quality_fixtures.ExecutionQualityKeeperTests('runTest')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.k,self.cfg,self.rpc=self.fixture.k,self.fixture.cfg,self.fixture.rpc
        self.values=self.fixture.fixture.values
        self.latest=self.fixture.fixture.block
        self.confirmed_hash='0x'+'55'*32
        self.confirmed={'blockHash':self.confirmed_hash,'requireCanonical':True}
        self.confirmed_header={'number':'0x63','hash':self.confirmed_hash,'timestamp':hex(self.rpc.now-2)}
        self.requests=[]
        original=self.rpc.call
        def call(method,params):
            self.requests.append((method,copy.deepcopy(params)))
            if method=='eth_getBlockByNumber' and params[0]=='0x64':
                return {'number':'0x64','hash':self.latest['blockHash'],'timestamp':hex(self.rpc.now)}
            if method=='eth_getBlockByNumber' and params[0]=='0x63':return dict(self.confirmed_header)
            if method=='eth_getCode' and params[1]==self.confirmed:return '0x6000'
            if method=='eth_call' and params[1]==self.confirmed:
                return self.values[params[0]['to'],params[0]['data']]
            return original(method,params)
        self.rpc.call=call
        self.k.canonical_lifecycle=0;self.k.preparing=False

    def _observe(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer:
            self.k._observe_execution_health()
            signer.assert_not_called()
        return copy.deepcopy(self.k.lp_execution_health)

    def _run(self,body=None):
        with patch.object(self.k,'cycle',side_effect=body or (lambda:None)), \
                patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer:
            result=self.k.run_cycle()
        signer.assert_not_called()
        return result,json.loads(self.k.health_path.read_text())

    def test_confirmed_observation_binds_exact_block_config_source_and_runtime(self):
        record=self._observe();self.assertEqual('observed_this_cycle',record['state'])
        observed=record['last_confirmed']
        self.assertEqual(99,observed['block_number']);self.assertEqual(100,observed['head_number'])
        self.assertEqual(self.confirmed_hash,observed['block_hash'])
        self.assertEqual(self.k.configuration_sha256,observed['configuration_sha256'])
        self.assertEqual(source_hashes(),observed['source_files_sha256'])
        self.assertEqual({name:self.cfg['code_hashes'][name] for name in observed['runtime_code_hashes']},
            observed['runtime_code_hashes'])
        self.assertEqual(100,observed['metadata']['execution_quality']['additional_loss_bps'])
        self.assertEqual(2,observed['metadata']['execution_quality']['quality_policy_revision'])
        calls=[p for m,p in self.requests if m in ('eth_call','eth_getCode')]
        self.assertTrue(calls);self.assertTrue(all(p[1]==self.confirmed for p in calls))
        self.assertEqual([],execution_reasons({'health_schema':HEALTH_SCHEMA,'lp_execution_health':record},
            self.cfg,now=self.rpc.now,max_age=1800))

    def test_failure_retains_last_confirmed_but_never_labels_it_fresh(self):
        previous=self._observe()['last_confirmed']
        original=self.rpc.call
        def call(method,params):
            if method=='eth_call':raise RpcError('https://secret.invalid/DO-NOT-EXPORT')
            return original(method,params)
        self.rpc.call=call;record=self._observe()
        self.assertEqual('unavailable',record['state']);self.assertEqual(previous,record['last_confirmed'])
        self.assertNotIn('DO-NOT-EXPORT',json.dumps(record))
        self.assertIn('execution_observation_not_current',execution_reasons(
            {'health_schema':HEALTH_SCHEMA,'lp_execution_health':record},self.cfg,now=self.rpc.now,max_age=1800))

    def test_reorg_future_and_unconfirmed_headers_cannot_produce_a_fresh_observation(self):
        for mutation in ('reorg','future','wrong_number','too_few_confirmations'):
            original=self.rpc.call
            count=0
            def call(method,params):
                nonlocal count
                result=original(method,params)
                if method=='eth_getBlockByNumber':
                    result=dict(result)
                    if params[0]=='0x63':
                        count+=1
                        if mutation=='reorg' and count>1:result['hash']='0x'+'77'*32
                        if mutation=='future':result['timestamp']=hex(self.rpc.now+1000)
                        if mutation=='wrong_number':result['number']='0x62'
                    if params[0]=='latest' and mutation=='too_few_confirmations':result['number']='0x0'
                return result
            self.rpc.call=call
            with self.subTest(mutation=mutation):self.assertEqual('unavailable',self._observe()['state'])
            self.rpc.call=original

    def test_pending_recovery_skips_metadata_and_does_not_rewrite_saved_state(self):
        self.k.state['pending']={'nonce':7,'to':self.cfg['contracts']['vault'],'data':'0x00',
            'value':0,'day':'2026-10-28','key':'harvest:7','hash':'0x'+'ab'*32}
        before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'_observe_execution_health',side_effect=AssertionError('Recovery must stay first')) as observed:
            _,health=self._run()
        observed.assert_not_called();self.assertEqual(before,self.k.state)
        self.assertEqual('pending_recovery',health['lp_execution_health']['state'])

    def test_latest_validation_failure_cannot_be_hidden_by_an_older_confirmed_read(self):
        self._observe()
        self.values[self.cfg['contracts']['balancing_router'],calldata('additionalLossBps()')]='0x'
        def body():
            try:self.k._validate_lp_routing()
            except RpcError:pass
        _,health=self._run(body)
        self.assertEqual('unavailable',health['lp_execution_health']['state'])
        self.assertEqual('degraded',health['status'])

    def test_same_block_discovery_reuses_metadata_but_fresh_validation_never_does(self):
        self.k._lp_metadata_cache={}
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            self.k._validate_lp_routing(use_cache=True)
            first=sum(m in ('eth_call','eth_getCode') for m,p in self.requests)
            self.k._validate_lp_routing(use_cache=True)
            second=sum(m in ('eth_call','eth_getCode') for m,p in self.requests)
            self.k._validate_lp_routing()
            third=sum(m in ('eth_call','eth_getCode') for m,p in self.requests)
        self.assertGreater(first,0);self.assertEqual(first,second);self.assertGreater(third,second)

    def test_new_hash_or_config_change_never_reuses_old_metadata(self):
        self.k._lp_metadata_cache={}
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            self.k._validate_lp_routing(use_cache=True)
            header=dict(self.confirmed_header)
            self.k._lp_routing_snapshot(header,use_cache=True)
            self.values[self.cfg['contracts']['balancing_router'],calldata('additionalLossBps()')]='0x'
            with self.assertRaises(RpcError):self.k._validate_lp_routing()
            self.cfg['code_hashes']['strategy']='0x'+'11'*32
            with self.assertRaisesRegex(RpcError,'configuration changed'):
                self.k._validate_lp_routing(use_cache=True)

    def test_submission_rechecks_policy_before_simulation_even_with_a_warm_discovery_cache(self):
        self.k._lp_metadata_cache={}
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            self.k._validate_lp_routing(use_cache=True)
            self.values[self.cfg['contracts']['strategy'],calldata('additionalLossBps()')]='0x'+f'{99:064x}'
            with patch('subprocess.run') as signer,patch.object(self.k,'_validate_accounting_version'), \
                    patch.object(self.k,'_defer_for_lifecycle',return_value=False),self.assertRaises(RpcError):
                self.k.submit('compounder','compound(uint256,uint128,uint256)',(7,1,self.rpc.now+180),'compound:7')
            signer.assert_not_called();self.assertIsNone(self.k.state['pending'])

    def test_submission_rechecks_changed_policy_after_estimation_before_any_signer(self):
        self.k._lp_metadata_cache={}
        self.k.live=True;self.k.cast='/inert/cast';self.k.keystore=Path('/inert/key');self.k.password=Path('/inert/pass')
        self.k.fee_policy='included';self.k.state['next_nonce']=7
        original=self.rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='eth_estimateGas':
                self.values[self.cfg['contracts']['strategy'],calldata('additionalLossBps()')]='0x'+f'{99:064x}'
            return result
        self.rpc.call=call
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            self.k._validate_lp_routing(use_cache=True)
            with patch('subprocess.run') as signer,patch.object(self.k,'_validate_accounting_version'), \
                    patch.object(self.k,'_validate_checkpoint'),patch.object(self.k,'_validate_code_hashes'), \
                    patch.object(self.k,'_defer_for_lifecycle',return_value=False),self.assertRaises(RpcError):
                self.k.submit('compounder','compound(uint256,uint128,uint256)',(7,1,self.rpc.now+180),'compound:7')
            signer.assert_not_called();self.assertIsNone(self.k.state['pending'])

    def test_cycles_do_not_reuse_metadata_or_change_transaction_journal(self):
        self.k.save();before=self.k.path.read_bytes()
        _,first=self._run()
        first_count=sum(m=='eth_call' for m,p in self.requests)
        _,second=self._run()
        self.assertGreater(sum(m=='eth_call' for m,p in self.requests),first_count)
        self.assertEqual(first['lp_execution_health']['last_confirmed'],second['lp_execution_health']['last_confirmed'])
        self.assertEqual(before,self.k.path.read_bytes());self.assertIsNone(self.k._lp_metadata_cache)

    def test_health_schema_and_profile_are_paired_without_relabeling_old_profiles(self):
        _,health=self._run()
        self.assertEqual(HEALTH_SCHEMA,health['health_schema'])
        self.assertEqual('dry_run_v2',health['status'])
        self.assertTrue(health_check(self.cfg,allow_dry_run=True,now=self.rpc.now)['ok'])
        del health['health_schema']
        self.assertIn('execution_health_schema_required',execution_reasons(health,self.cfg,now=self.rpc.now,max_age=1800))
        historical=copy.deepcopy(self.cfg);historical.pop('execution_quality_version')
        self.assertEqual([],execution_reasons(health,historical,now=self.rpc.now,max_age=1800))
        health['health_schema']=99
        self.assertEqual(['unsupported_health_schema'],execution_reasons(health,historical,now=self.rpc.now,max_age=1800))

    def test_checker_rejects_missing_tampered_or_stale_observation_fields(self):
        good={'health_schema':HEALTH_SCHEMA,'lp_execution_health':self._observe()}
        cases=[('configuration_sha256','0'*64),('block_timestamp',self.rpc.now-601),
            ('block_hash','0x0'),('block_number',100),('source_files_sha256',{}),
            ('runtime_code_hashes',{}),('observed_at_unix',self.rpc.now+60)]
        for field,value in cases:
            bad=copy.deepcopy(good);bad['lp_execution_health']['last_confirmed'][field]=value
            with self.subTest(field=field):self.assertTrue(execution_reasons(bad,self.cfg,now=self.rpc.now,max_age=1800))
        for path in ('schema','version','additional'):
            bad=copy.deepcopy(good)
            if path=='schema':bad['lp_execution_health']['schema']=True
            elif path=='version':bad['lp_execution_health']['last_confirmed']['metadata']['execution_quality']['version']=True
            else:bad['lp_execution_health']['last_confirmed']['metadata']['execution_quality']['additional_loss_bps']=True
            with self.subTest(path=path):self.assertTrue(execution_reasons(bad,self.cfg,now=self.rpc.now,max_age=1800))


class KeeperGasTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.fixture=basic.KeeperTests('runTest');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.k,self.rpc,self.cfg=self.fixture.k,self.fixture.rpc,self.fixture.cfg

    def _submit(self):
        with patch('subprocess.run') as signer:
            result=self.k.submit('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7')
            signer.assert_not_called()
        self.assertFalse(result);self.assertIsNone(self.k.state['pending'])
        return self.k.gas_review_health['last_review']

    def test_padded_gas_and_configured_cap_are_reported_without_widening(self):
        self.rpc.gas=100001;before=copy.deepcopy(self.cfg)
        record=self._submit()
        self.assertEqual(100001,record['estimated_gas']);self.assertEqual(125002,record['padded_gas_required'])
        self.assertEqual(100000,record['gas_limit_cap']);self.assertEqual('gas_limit_cap',record['reason'])
        self.assertEqual(before,self.cfg)

    def test_price_and_cost_caps_remain_distinct_from_gas_units(self):
        self.rpc.gas_price=101
        self.assertEqual('gas_price_cap',self._submit()['reason'])
        self.rpc.gas_price=2;self.cfg['max_transaction_cost_wei']=1
        self.assertEqual('cost_cap',self._submit()['reason'])

    def test_estimate_failure_retains_explicit_unavailable_diagnostics(self):
        original=self.rpc.call
        def call(method,params):
            if method=='eth_estimateGas':raise RpcError('DO-NOT-EXPORT')
            return original(method,params)
        self.rpc.call=call
        with patch('subprocess.run') as signer,self.assertRaises(RpcError):
            self.k.submit('vault','collectFees(uint256,uint256)',(7,self.rpc.now+180),'harvest:7')
        signer.assert_not_called();record=self.k.gas_review_health['last_review']
        self.assertEqual('unavailable',record['state']);self.assertIsNone(record['estimated_gas'])
        self.assertNotIn('DO-NOT-EXPORT',json.dumps(record))

    def test_health_summary_never_echoes_arbitrary_diagnostic_strings(self):
        result=summary({'lp_execution_health':{'state':'https://DO-NOT-EXPORT'},
            'gas_review':{'last_review':{'reason':'DO-NOT-EXPORT','action':'DO-NOT-EXPORT',
                'estimated_gas':True,'gas_limit_cap':100000}}})
        self.assertNotIn('DO-NOT-EXPORT',json.dumps(result));self.assertIsNone(result['gas_review']['estimated_gas'])
        self.assertEqual(100000,result['gas_review']['gas_limit_cap'])


if __name__=='__main__':unittest.main()
