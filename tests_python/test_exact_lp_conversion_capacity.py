"""Bounded accounting7 conversion sizing with injected RPC and a mocked signer.

Exercises the actual worker and submit() composition. Runtime/accounting and
signer-file admission are outside this fixture; no chain, service or key is used.
"""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.royalties import BATCH, RoyaltyAutomation, native_quote
from tests_python.test_royalty_keeper import HASH, PIN, addr
from tests_python.test_typed_v4_conversion_keeper import V4ConversionRPC
from zzz_ops.abi import calldata, decode_words, keccak256
from zzz_ops.rpc import RpcError
from zzz_ops.errors import RemoteRPCError, WorkLimit


def batch(data):
    words=[int(w,16) for w in decode_words('0x'+data[10:])]
    return {'ids':words[6:], 'minimum':words[3], 'deadline':words[4], 'count':words[5]}


class CapacityRPC(V4ConversionRPC):
    def __init__(self, contracts):
        super().__init__(contracts)
        self.gas_per_id=100000
        self.price=1
        self.simulations=[]
        self.estimates=[]
        self.balance_reads=[]
        self.quotes=[]
        self.fault_read=None
        self.fault_simulation=None
        self.fault_quote=False
        self.advance_quote=0
        self.stale_after_estimate=False
        self.anchor_now=100000
        self.advance_estimate=0
        self.probe_error=None
        self.probe_method='eth_call'
        self.probe_above=8
        self.simulation_output=None
        self.values[contracts['royalty_nft'],calldata('mintedCount()')]=32
        for ordinal in range(1,33):
            self.values[contracts['royalty_nft'],calldata('tokenAtOrdinal(uint256)',ordinal)]=ordinal
            self.values[contracts['royalties'],calldata('claimable(uint256,address)',ordinal,self.asset)]=100
        self.values[contracts['royalties'],calldata('access()')]=int(contracts['access'],16)
        self.values[contracts['access'],calldata('module(bytes32)','0x'+keccak256(b'ZZZRewards').hex())]=int(contracts['royalties'],16)

    def call(self, method, params):
        if method=='eth_getBlockByNumber':
            self.calls.append((method,params))
            return {'number':'0x64' if params[0]=='latest' else params[0],
                'timestamp':hex(self.now if params[0]=='latest' else self.anchor_now),'hash':HASH}
        if method=='eth_getTransactionCount': return '0x7'
        if method=='eth_getBalance': return hex(10**30)
        if method=='eth_gasPrice': return hex(self.price)
        if method=='eth_estimateGas':
            candidate=batch(params[0]['data']);self.estimates.append(candidate)
            if self.probe_error and self.probe_method==method and candidate['count']>self.probe_above:raise self.probe_error
            if self.stale_after_estimate:self.now+=301
            self.now+=self.advance_estimate
            return hex(candidate['count']*self.gas_per_id)
        if method=='eth_call':
            data=params[0]['data']
            if data.startswith(native_quote(self.asset,1)[:10]):
                if self.fault_quote:raise RpcError('quote unavailable')
                amount=int(data[-64:],16);self.quotes.append(amount)
                self.now+=self.advance_quote
                return '0x'+f'{amount*10**15:064x}'
            if data.startswith(calldata('claimable(uint256,address)',1,self.asset)[:10]):
                token=int(data[10:74],16);self.balance_reads.append(token)
                if token==self.fault_read:raise RpcError('claimable unavailable')
            if data.startswith('0x'+keccak256(BATCH.encode()).hex()[:8]):
                candidate=batch(data);self.simulations.append(candidate)
                if self.probe_error and self.probe_method==method and candidate['count']>self.probe_above:raise self.probe_error
                if self.fault_simulation in candidate['ids']:raise RpcError('simulation unavailable')
                if self.simulation_output is not None:return self.simulation_output
                return '0x'+f'{candidate["minimum"]:064x}'
        return super().call(method,params)


class ExactLPConversionCapacityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        names=['access','vault','strategy','fees','compounder','buyback','pools','royalties','royalty_converter',
            'royalty_nft','royalty_wrapper','oracle','royalty_v4_executor','principal_exit','liquidity','balancing_router',
            'pool_manager','state_view','portfolio_policy','lp_balance_math','lp_position_executor','protocol_policy',
            'rebalance_confirmation']
        contracts={name:addr(i+1) for i,name in enumerate(names)}
        self.rpc=CapacityRPC(contracts)
        for new,old in [('rewards','royalties'),('lp_converter','royalty_converter'),
                ('lp_nft','royalty_nft'),('lp_v4_executor','royalty_v4_executor')]:contracts[new]=contracts[old]
        self.cfg={'chain_id':1,'sender':addr(90),'contracts':contracts,'confirmations':2,
            'state_path':str(Path(self.tmp.name)/'state.json'),'code_hashes':{n:PIN for n in contracts},
            'accounting_version':7,'custody_version':5,'protocol_policy_version':1,'fee_intake_version':1,
            'portfolio_version':2,'maintenance_policy_version':3,'lp_routing_version':2,
            'rebalance_confirmation_version':3,'execution_quality_version':1,'interval_seconds':240,
            'idle_compounding_budget':addr(99),'maintenance':{'compound':False},
            'receipt_fee_policy':'included',
            'max_gas_limit':1000000,'max_gas_price_wei':100,'max_transaction_cost_wei':10**12,
            'max_daily_cost_wei':10**15,
            'lp_conversion':{'enabled':True,'profile':'v4_native','max_gas_to_output_bps':100,
                'assets':[{'asset':self.rpc.asset,'route_id':self.rpc.route,'minimum_source_units':1,'minimum_output_wei':1}]}}
        self.cfg['code_hashes']['idle_compounding_budget']=PIN
        self.k=Keeper(self.cfg,rpc=self.rpc)
        self.k.state['next_nonce']=7
        for name in ('_validate_accounting_version','_validate_code_hashes','_validate_checkpoint'):
            p=patch.object(self.k,name);p.start();self.addCleanup(p.stop)
        p=patch('keeper.monitor.time.time',side_effect=lambda:self.rpc.now);p.start();self.addCleanup(p.stop)
        p=patch('keeper.monitor.log');self.logs=p.start();self.addCleanup(p.stop)
        p=patch('keeper.monitor.subprocess.run');self.signer=p.start();self.addCleanup(p.stop)
        self.signer.return_value.returncode=0
        self.signer.return_value.stdout=json.dumps({'hash':'0x'+'12'*32})

    def enable_mocked_sender(self):
        # Admission was intentionally dry; only the actual serial send path below
        # is exercised with a mocked process and temporary pending journal.
        self.k.live=True;self.k.cast='mock-cast';self.k.keystore=Path(self.tmp.name)/'unused-key'
        self.k.password=Path(self.tmp.name)/'unused-password'

    def test_affordable_subset_preserves_every_cap_and_persists_remainder_before_one_send(self):
        self.enable_mocked_sender();before=copy.deepcopy(self.k.config)
        def send(*args,**kwargs):
            saved=json.loads(self.k.path.read_text())
            self.assertEqual(9,saved['lp_conversion']['ordinal'])
            self.assertEqual(list(range(1,9)),batch(saved['pending']['data'])['ids'])
            return type('Result',(),{'returncode':0,'stdout':json.dumps({'hash':'0x'+'12'*32})})()
        self.signer.side_effect=send
        self.assertTrue(self.k.lp_rewards.scan_once())
        self.assertEqual([32,16,8],[c['count'] for c in self.rpc.estimates])
        self.assertEqual([3200,1600,800],self.rpc.quotes)
        self.assertEqual(1000000,self.k.state['pending']['fee_review']['gas_limit'])
        self.assertEqual(7,self.k.state['pending']['nonce'])
        self.assertEqual(before,self.k.config);self.signer.assert_called_once()

    def test_continuation_visits_suffix_even_when_prefix_is_still_funded(self):
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual(9,self.k.state['lp_conversion']['ordinal'])
        self.rpc.estimates.clear()
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([24,12,6],[c['count'] for c in self.rpc.estimates])
        self.assertEqual(list(range(9,15)),self.rpc.estimates[-1]['ids'])
        self.assertEqual(15,self.k.state['lp_conversion']['ordinal'])
        self.signer.assert_not_called()

    def test_unaffordable_singleton_stops_at_six_attempts_and_does_not_hide_suffix(self):
        self.rpc.gas_per_id=10**7
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([32,16,8,4,2,1],[c['count'] for c in self.rpc.estimates])
        self.assertEqual(2,self.k.state['lp_conversion']['ordinal'])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_per_transaction_cost_can_shrink_but_daily_and_relative_limits_stay_fixed(self):
        self.k.config.update(max_gas_limit=10**8,max_transaction_cost_wei=1000000)
        self.rpc.price=2
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([32,16,8,4],[c['count'] for c in self.rpc.estimates])
        self.assertEqual(5,self.k.state['lp_conversion']['ordinal'])
        self.assertEqual({},self.k.state['spent'])

    def test_global_price_daily_economy_and_retry_blocks_never_trigger_sizing(self):
        day=dt.datetime.fromtimestamp(self.rpc.now,dt.timezone.utc).date().isoformat()
        for cause in ('price','daily','economy','retry'):
            with self.subTest(cause=cause):
                self.k.state['lp_conversion']['ordinal']=1;self.k.state['spent']={};self.k.state.pop('retry_after',None)
                self.rpc.estimates.clear();self.rpc.price=1
                self.k.config.update(max_daily_cost_wei=10**15)
                self.k.lp_rewards.gas_bps=100
                if cause=='price':self.rpc.price=101
                if cause=='daily':self.k.state['spent'][day]=10**15
                if cause=='economy':self.k.lp_rewards.gas_bps=1;self.rpc.price=100
                if cause=='retry':
                    key=f'lp_conversion:{self.rpc.asset}:1:32';self.k.state['retry_after']={key:self.rpc.now+100}
                # Make economy stricter without increasing any configured cap.
                maximum=1 if cause=='economy' else None
                original=self.k.submit
                def submit(*args,**kwargs):
                    if maximum is not None:kwargs['maximum_cost']=maximum
                    return original(*args,**kwargs)
                with patch.object(self.k,'submit',side_effect=submit):self.assertFalse(self.k.lp_rewards.scan_once())
                self.assertEqual(0 if cause=='retry' else 1,len(self.rpc.estimates))
                self.assertIsNone(self.k.state['pending'])
        self.signer.assert_not_called()

    def test_unknown_nft_read_and_simulation_faults_are_deferred_without_isolation(self):
        for read_failure in (True,False):
            with self.subTest(read_failure=read_failure):
                self.k.state['lp_conversion']['ordinal']=1;self.rpc.estimates.clear();self.rpc.simulations.clear()
                self.rpc.fault_read=11 if read_failure else None
                self.rpc.fault_simulation=None if read_failure else 11
                self.assertFalse(self.k._convert_rewards(self.k.lp_rewards))
                self.assertEqual([],self.rpc.estimates)
                self.assertEqual(0 if read_failure else 1,len(self.rpc.simulations))
                self.assertIsNone(self.k.state['pending'])
        self.signer.assert_not_called()

    def test_opaque_execution_rejections_allow_only_bounded_independently_validated_prefixes(self):
        for method in ('eth_call','eth_estimateGas'):
            for code in (3,-32000):
                with self.subTest(method=method,code=code):
                    self.k.state['lp_conversion']['ordinal']=1;self.rpc.simulations.clear();self.rpc.estimates.clear()
                    self.rpc.probe_method=method;self.rpc.probe_error=RemoteRPCError(method,code)
                    self.assertFalse(self.k.lp_rewards.scan_once())
                    self.assertEqual([32,16,8],[c['count'] for c in self.rpc.simulations])
                    self.assertEqual([3200,1600,800],self.rpc.quotes[-3:])
                    self.assertEqual(9,self.k.state['lp_conversion']['ordinal'])
                    self.assertIsNone(self.k.state['pending'])
        self.signer.assert_not_called()

    def test_opaque_singleton_failure_keeps_six_probe_ceiling_and_suffix_rotation(self):
        self.rpc.probe_error=RemoteRPCError('eth_call',3);self.rpc.probe_above=0
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([32,16,8,4,2,1],[c['count'] for c in self.rpc.simulations])
        self.assertEqual([],self.rpc.estimates)
        self.assertEqual(2,self.k.state['lp_conversion']['ordinal'])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_rate_transport_work_malformed_and_method_mismatches_never_allow_prefix_probes(self):
        errors=(RemoteRPCError('eth_call',-32005,'rate_limited'),RemoteRPCError('eth_call',-32603),
            RemoteRPCError('eth_call',-32000,'invalid_params'),RemoteRPCError('eth_estimateGas',3),
            RpcError('transport unavailable'),WorkLimit('rpc_budget'))
        for error in errors:
            with self.subTest(error=type(error).__name__,code=getattr(error,'code',None)):
                self.k.state['lp_conversion']['ordinal']=1;self.rpc.simulations.clear()
                self.rpc.probe_error=error;self.rpc.probe_method='eth_call'
                self.assertFalse(self.k._convert_rewards(self.k.lp_rewards))
                self.assertEqual([32],[c['count'] for c in self.rpc.simulations])
                self.assertIsNone(self.k.state['pending'])
        self.signer.assert_not_called()

    def test_saturated_daily_budget_prevents_opaque_prefix_probes(self):
        day=dt.datetime.fromtimestamp(self.rpc.now,dt.timezone.utc).date().isoformat()
        self.k.state['spent'][day]=self.k.config['max_daily_cost_wei']
        self.rpc.probe_error=RemoteRPCError('eth_call',3)
        self.assertFalse(self.k._convert_rewards(self.k.lp_rewards))
        self.assertEqual([32],[c['count'] for c in self.rpc.simulations])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_malformed_or_below_minimum_simulation_result_never_probes_or_signs(self):
        for output in ('0x','0x01','0x'+'0'*128,'0x'+'0'*64):
            with self.subTest(output=output):
                self.k.state['lp_conversion']['ordinal']=1;self.rpc.simulations.clear()
                self.rpc.simulation_output=output
                self.assertFalse(self.k._convert_rewards(self.k.lp_rewards))
                self.assertEqual([32],[c['count'] for c in self.rpc.simulations])
                self.assertEqual([],self.rpc.estimates)
                self.assertIsNone(self.k.state['pending'])
        self.signer.assert_not_called()

    def test_claim_or_pause_race_after_first_rejection_aborts_without_further_candidate(self):
        original=self.k.submit
        def submit(*args,**kwargs):
            result=original(*args,**kwargs)
            if len(self.rpc.estimates)==1:self.rpc.fault_simulation=1
            return result
        with patch.object(self.k,'submit',side_effect=submit):
            self.assertFalse(self.k._convert_rewards(self.k.lp_rewards))
        self.assertEqual([32,16],[c['count'] for c in self.rpc.simulations])
        self.assertEqual([32],[c['count'] for c in self.rpc.estimates])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_pending_blocks_scan_and_ambiguous_false_result_never_retries(self):
        pending={'key':'original','nonce':7,'hash':'0x'+'13'*32}
        self.k.state['pending']=pending;before=copy.deepcopy(self.k.state)
        self.assertFalse(self.k.lp_rewards.scan_once());self.assertEqual([],self.rpc.calls)
        self.assertEqual(before,self.k.state)
        self.k.state['pending']=None
        def ambiguous(*args,**kwargs):
            kwargs['capacity_review']['reason']='gas_limit_cap';self.k.state['pending']=pending
            return False
        with patch.object(self.k,'submit',side_effect=ambiguous) as submit:
            self.assertFalse(self.k.lp_rewards.scan_once());submit.assert_called_once()
        self.assertEqual(pending,self.k.state['pending']);self.signer.assert_not_called()

    def test_stale_snapshot_during_sizing_stops_before_second_simulation(self):
        self.rpc.stale_after_estimate=True
        self.assertFalse(self.k._convert_rewards(self.k.lp_rewards))
        self.assertEqual([32],[c['count'] for c in self.rpc.estimates])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_preparation_that_expires_after_estimate_never_saves_intent_or_signs(self):
        self.enable_mocked_sender();self.k.config['max_gas_limit']=10000000
        self.rpc.stale_after_estimate=True
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([32],[c['count'] for c in self.rpc.estimates])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_utc_rollover_uses_new_day_budget_without_rewriting_prepared_deadline(self):
        self.enable_mocked_sender();self.k.config['max_gas_limit']=10000000
        self.rpc.now=self.rpc.anchor_now=172799;self.rpc.advance_estimate=2
        day=dt.datetime.fromtimestamp(172801,dt.timezone.utc).date().isoformat()
        self.k.state['spent'][day]=self.k.config['max_daily_cost_wei']
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual(172979,self.rpc.simulations[0]['deadline'])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_subset_minimum_and_deadline_are_rebuilt_after_quote_time(self):
        self.rpc.advance_quote=3
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([100183,100186,100189],[c['deadline'] for c in self.rpc.simulations])
        self.assertEqual([n*100*10**15*99//100 for n in (32,16,8)],
            [c['minimum'] for c in self.rpc.simulations])
        self.assertEqual(32+32+16+8,len(self.rpc.balance_reads))

    def test_zero_source_and_economic_minimum_never_fabricate_a_conversion(self):
        for token in range(1,33):self.rpc.values[self.k.contracts['rewards'],calldata('claimable(uint256,address)',token,self.rpc.asset)]=0
        self.assertFalse(self.k.lp_rewards.scan_once());self.assertEqual([],self.rpc.estimates)
        self.assertEqual([],self.rpc.quotes)
        for token in range(1,33):self.rpc.values[self.k.contracts['rewards'],calldata('claimable(uint256,address)',token,self.rpc.asset)]=100
        self.k.lp_rewards.routes[0]['minimum_source_units']=1000
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([32,16],[c['count'] for c in self.rpc.estimates])
        self.assertEqual(17,self.k.state['lp_conversion']['ordinal'])
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_disabled_route_or_failed_oracle_never_reaches_estimation(self):
        converter=self.k.contracts['lp_converter']
        self.rpc.values[converter,calldata('routeEnabled(bytes32)',self.rpc.route)]=0
        self.assertFalse(self.k.lp_rewards.scan_once());self.assertEqual([],self.rpc.quotes)
        self.rpc.values[converter,calldata('routeEnabled(bytes32)',self.rpc.route)]=1;self.rpc.fault_quote=True
        self.assertFalse(self.k._convert_rewards(self.k.lp_rewards));self.assertEqual([],self.rpc.estimates)
        self.assertIsNone(self.k.state['pending']);self.signer.assert_not_called()

    def test_fresh_capacity_result_never_reuses_health_and_historical_profile_stays_single_attempt(self):
        self.k.gas_review_health={'last_review':{'reason':'gas_limit_cap'}}
        with patch.object(self.k,'submit',return_value=False) as submit:
            self.assertFalse(self.k.lp_rewards.scan_once());submit.assert_called_once()
        self.k.state['lp_conversion']['ordinal']=1;self.k.lp_rewards.exact_lp=False
        self.assertFalse(self.k.lp_rewards.scan_once())
        self.assertEqual([32],[c['count'] for c in self.rpc.estimates])
        self.assertEqual(1,self.k.state['lp_conversion']['ordinal'])

    def test_single_fixed_source_configuration_and_capacity_result_are_explicit(self):
        self.k.config['lp_conversion']['assets'].append(dict(self.k.config['lp_conversion']['assets'][0],asset=addr(401)))
        with self.assertRaisesRegex(ValueError,'exactly one'):RoyaltyAutomation(self.k,lp=True)
        with self.assertRaisesRegex(ValueError,'accounting7 LP conversion'):
            self.k.submit('royalties',BATCH,(self.rpc.asset,[1],self.rpc.route,1,100100),'bad',capacity_review={})

    def test_new_fixed_source_count_validation_does_not_block_saved_pending_recovery(self):
        self.k.config['lp_conversion']['assets'].append(dict(self.k.config['lp_conversion']['assets'][0],asset=addr(401)))
        self.k.state['pending']={'key':'saved','hash':'0x'+'15'*32,'nonce':7}
        before=copy.deepcopy(self.k.state)
        worker=RoyaltyAutomation(self.k,lp=True)
        self.assertEqual(before,self.k.state);self.assertFalse(worker.scan_once())
        self.k.state['pending']=None
        with self.assertRaisesRegex(ValueError,'exactly one'):worker.scan_once()
        self.signer.assert_not_called()


if __name__=='__main__':unittest.main()
