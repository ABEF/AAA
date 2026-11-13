"""New20M/24M budget wiring checks, with injected RPC and inert signer only.

These qualify existing software gates for the proposed ceilings. They are not
new market execution, fee/provider qualification, authority or release approval.
Only this module's new tests run; imported old fixture methods are not rerun.
"""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api.activation import ActivationTransactions, ActivationGasHeadroomError, ActivationInputError
from frontend_api.activation_config import ActivationConfig
from frontend_api.service import ProjectionError
from frontend_api.transaction_gas import DEFAULT_GAS_LIMIT
from tests_python.test_execution_price_profile import verifier
from tests_python.test_frontend_api import addr
from tests_python import test_keeper as basic
from tests_python import test_keeper_late_lp_review as late
from zzz_ops import manual_lp_review as manual
from zzz_ops.errors import RemoteRPCError
from zzz_ops.rpc import RpcError


class Activation20MProfileTests(unittest.TestCase):
    def fixture(self):
        rpc, projection, config = verifier()
        config = copy.deepcopy(config)
        config.update(schema=2)
        config['fee_policy'].update(max_gas_limit='20000000',
            max_network_fee_wei='40000000', max_gas_price_wei='2')
        rpc.estimate=16_000_000;rpc.gas_price=2;rpc.balance=10**18
        header={'number':99,'hash':rpc.hash,'timestamp':990}
        self.block_limit=32_000_000;original=rpc.call
        def call(method,params):
            if method=='eth_getBlockByHash':
                rpc.calls.append((method,copy.deepcopy(params)))
                return {'number':'0x63','hash':rpc.hash,'timestamp':hex(990),
                        'gasLimit':hex(self.block_limit)}
            return original(method,params)
        rpc.call=call
        service=ActivationTransactions(projection,config)
        self.assertEqual((7,1,3),(projection.accounting_version,
            service.config.execution_price_version,service.config.lp_routing_version))
        tx={'from':addr(30),'to':rpc.pins['entry'],'data':'0x12345678','value':'0x0'}
        return rpc,projection,config,service,header,tx

    def test_explicit20m_and_historical_default_have_distinct_review_identity(self):
        rpc,p,cfg,service,_h,_tx=self.fixture()
        old=copy.deepcopy(cfg);old['schema']=1
        old['fee_policy'].pop('max_gas_limit');old['fee_policy'].pop('max_network_fee_wei')
        historical=ActivationConfig(old,p)
        self.assertEqual(DEFAULT_GAS_LIMIT,12_000_000)
        self.assertEqual(historical.max_gas_limit,12_000_000)
        self.assertEqual(service.config.max_gas_limit,20_000_000)
        self.assertNotEqual(historical.identity,service.config.identity)
        self.assertEqual(rpc.calls,[])

    def test20m_cap_and_full20pct_boundary_are_never_clipped(self):
        for estimate,accepted in ((16_666_666,True),(16_666_667,False)):
            rpc,_p,_cfg,service,h,tx=self.fixture();rpc.estimate=estimate
            review=service._gas_review(h)
            if accepted:
                result=service._gas(tx,{'blockHash':rpc.hash,'requireCanonical':True},review)
                self.assertEqual(result['suggested_limit'],'20000000')
                self.assertEqual(result['effective_gas_limit'],'20000000')
                self.assertTrue(result['full_twenty_percent_headroom'])
            else:
                with self.assertRaises(ActivationGasHeadroomError):
                    service._gas(tx,{'blockHash':rpc.hash,'requireCanonical':True},review)
            estimate_calls=[x for m,x in rpc.calls if m=='eth_estimateGas']
            self.assertEqual(len(estimate_calls),1)
            self.assertEqual(estimate_calls[0][0]['gas'],hex(20_000_000))

    def test_synthetic_header_does_not_raise20m_and_lower_block_stays_binding(self):
        for block,estimate,padded in ((1<<50,16_000_000,19_200_000),
                                      (18_000_000,15_000_000,18_000_000)):
            rpc,_p,_cfg,service,h,tx=self.fixture();self.block_limit=block;rpc.estimate=estimate
            review=service._gas_review(h)
            result=service._gas(tx,{'blockHash':rpc.hash,'requireCanonical':True},review)
            self.assertEqual(review.effective,min(20_000_000,block))
            self.assertEqual(result['suggested_limit'],str(padded))
            self.assertEqual(result['configured_gas_limit'],'20000000')

    def test_price_fee_and_native_funding_remain_separate_failures(self):
        for fault in ('price','fee','balance'):
            rpc,_p,_cfg,service,h,tx=self.fixture()
            if fault=='price':rpc.gas_price=3
            elif fault=='fee':service.config.max_network_fee=38_399_999
            else:tx['value']=hex(rpc.balance-38_400_000+1)
            before=copy.deepcopy(tx)
            with self.subTest(fault=fault),self.assertRaises((ProjectionError,ActivationInputError)):
                service._gas(tx,{'blockHash':rpc.hash,'requireCanonical':True},service._gas_review(h))
            self.assertEqual(tx,before)
            self.assertEqual(service.config.max_gas_limit,20_000_000)

    def test_confirmed_hash_failure_does_not_fall_back_or_widen(self):
        rpc,_p,_cfg,service,h,_tx=self.fixture();original=rpc.call
        def call(method,params):
            if method=='eth_getBlockByHash':
                rpc.calls.append((method,copy.deepcopy(params)))
                raise RpcError('Unavailable confirmed header')
            return original(method,params)
        rpc.call=call
        with self.assertRaises(RpcError):service._gas_review(h)
        self.assertEqual([m for m,_ in rpc.calls],['eth_getBlockByHash'])

    def test_incomplete_real_fee_review_is_not_made_valid_by20m(self):
        _rpc,p,cfg,_service,_h,_tx=self.fixture()
        for field,value in (('estimate_includes_all_fees',False),('review_hash',None),
                            ('max_network_fee_wei',None),('max_gas_price_wei',None)):
            bad=copy.deepcopy(cfg);bad['fee_policy'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):ActivationConfig(bad,p)


class Manual24MProfileTests(unittest.TestCase):
    def fixture(self):
        h={'number':100,'timestamp':1000,'hash':basic.H};block={'blockHash':basic.H,'requireCanonical':True}
        fee={'max_gas_limit':'24000000','max_gas_price_wei':'2','max_network_fee_wei':'48000000'}
        state=SimpleNamespace(estimate=19_200_000,price=2,balance=48_000_000,block=32_000_000,calls=[])
        def call(method,params):
            state.calls.append((method,copy.deepcopy(params)))
            if method=='eth_getBlockByNumber':return {'number':'0x64','timestamp':hex(1000),'hash':basic.H,'gasLimit':hex(state.block)}
            if method=='eth_call':return '0x'
            if method=='eth_estimateGas':return hex(state.estimate)
            if method=='eth_gasPrice':return hex(state.price)
            if method=='eth_getBalance':return hex(state.balance)
            raise AssertionError(method)
        p=SimpleNamespace(rpc=SimpleNamespace(call=call))
        tx={'from':basic.A,'to':basic.B,'data':'0x12345678','value':'0x0'}
        return p,state,h,block,tx,fee

    def test24m_manual_cap_retains_full25pct_and_exact_frozen_call(self):
        p,s,h,b,tx,fee=self.fixture();original=copy.deepcopy(tx)
        result=manual.simulation(p,h,b,tx,fee,confirmed=True)
        self.assertEqual(result['padded_gas'],'24000000')
        self.assertEqual(result['gas_limit_cap'],'24000000')
        calls=[args for method,args in s.calls if method in ('eth_call','eth_estimateGas')]
        self.assertEqual(calls,[[{**tx,'gas':hex(24_000_000)},b]]*2)
        self.assertEqual(tx,original);self.assertNotIn('gas',tx)

    def test_one_unit_above_full25pct_boundary_fails_without_larger_probe(self):
        p,s,h,b,tx,fee=self.fixture();s.estimate+=1
        with self.assertRaisesRegex(RpcError,'gas/fee limits'):manual.simulation(p,h,b,tx,fee,confirmed=True)
        self.assertEqual(sum(m=='eth_estimateGas' for m,_ in s.calls),1)
        self.assertTrue(all(args[0]['gas']==hex(24_000_000) for m,args in s.calls if m in ('eth_call','eth_estimateGas')))

    def test_lower_block_price_fee_and_governance_funding_still_bind(self):
        for fault in ('block','price','fee','balance'):
            p,s,h,b,tx,fee=self.fixture()
            if fault=='block':s.block=23_999_999
            elif fault=='price':s.price=3
            elif fault=='fee':fee['max_network_fee_wei']='47999999'
            else:s.balance-=1
            with self.subTest(fault=fault),self.assertRaises(RpcError):
                manual.simulation(p,h,b,tx,fee,confirmed=False)
            self.assertEqual(fee['max_gas_limit'],'24000000')


class Keeper24MProfileTests(unittest.TestCase):
    def fixture(self):
        f=late.KeeperLateLPReviewTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        f.cfg.update(max_gas_limit=24_000_000,max_gas_price_wei=2,
                     max_transaction_cost_wei=48_000_000,max_daily_cost_wei=96_000_000)
        return f

    def test24m_bound_and_padded_only_mock_signing_for_both_lp_actions(self):
        for action in late.LP_ACTIONS:
            f=self.fixture();f.rpc.gas=16_631_798;before=copy.deepcopy(f.k.state['spent'])
            with self.subTest(action=action[0]),patch('keeper.monitor.subprocess.run',
                    return_value=SimpleNamespace(stdout=basic.H,returncode=0)) as signer:
                self.assertTrue(f.submit(action))
            command=signer.call_args.args[0]
            self.assertEqual(command[command.index('--gas-limit')+1],'20789748')
            initial=[params for method,params in f.rpc.calls if method in ('eth_call','eth_estimateGas') and 'from'in params[0]][:2]
            self.assertEqual(len(initial),2)
            self.assertTrue(all(x[0]['gas']==hex(24_000_000) for x in initial))
            self.assertEqual(f.k.state['pending']['fee_review']['gas_limit'],20_789_748)
            self.assertEqual(f.k.state['spent'],before)

    def test24m_limit_does_not_bypass_padding_price_transaction_or_daily_caps(self):
        for fault in ('padding','price','transaction','daily'):
            f=self.fixture();f.rpc.gas=16_631_798
            if fault=='padding':f.rpc.gas=19_200_001
            elif fault=='price':f.rpc.gas_price=3
            elif fault=='transaction':f.cfg['max_transaction_cost_wei']=41_579_495
            else:f.cfg['max_daily_cost_wei']=41_579_495
            before=copy.deepcopy(f.k.state)
            with self.subTest(fault=fault),patch('keeper.monitor.subprocess.run') as signer:
                self.assertFalse(f.submit());signer.assert_not_called()
            f.assert_no_intent(before);self.assertEqual(f.cfg['max_gas_limit'],24_000_000)

    def test_provider_refusal_never_widens24m_or_creates_intent(self):
        f=self.fixture();original=f.rpc.call
        def call(method,params):
            if method=='eth_estimateGas':
                f.rpc.calls.append((method,copy.deepcopy(params)))
                raise RemoteRPCError(method,-32000)
            return original(method,params)
        f.rpc.call=call;before=copy.deepcopy(f.k.state)
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(RemoteRPCError):f.submit()
            signer.assert_not_called()
        f.assert_no_intent(before)
        self.assertEqual(sum(m=='eth_estimateGas' for m,_ in f.rpc.calls),1)

    def test_older_pending_operation_blocks_new24m_work_without_relabeling(self):
        f=self.fixture();f.k.state['pending']={'hash':basic.H,'fee_review':{'gas_limit':12_000_000}}
        before=copy.deepcopy(f.k.state);f.rpc.calls.clear()
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(f.submit());signer.assert_not_called()
        self.assertEqual(before,f.k.state);self.assertEqual(f.rpc.calls,[])
