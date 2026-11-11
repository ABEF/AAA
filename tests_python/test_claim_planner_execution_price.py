"""Pinned identity reuse for fresh claims; no mutable Oracle state is cached."""
import copy
import unittest

from frontend_api.claim_planner import _SnapshotReads
from frontend_api.service import Projection, ZERO
from frontend_api.transactions import Transactions
from tests_python.test_exact_lp_profile7 import Fresh7API
from tests_python.test_frontend_api import addr, words
from tests_python.test_frontend_transactions import transaction_config
from zzz_ops.abi import calldata


class ClaimPlannerExecutionPriceTests(unittest.TestCase):
    def test_current_claim_plan_reads_each_new_identity_once_without_oracle_dependency(self):
        f=Fresh7API(self);f.config['execution_price_version']=1
        for role in ('liquidity','balancing_router','strategy','lp_position_executor','lp_balance_math'):
            f.rpc.put(f.c[role],'EXECUTION_PRICE_VERSION()',values=(1,))
        f.rpc.put(f.c['liquidity'],'executionStrategy()',values=(f.c['lp_balance_math'],))
        for role in ('liquidity','balancing_router'):
            f.rpc.put(f.c[role],'LP_ROUTING_VERSION()',values=(3,))
        original=f.rpc.call
        def call(method,params):
            if method=='eth_call' and 'from' in params[0]:
                f.rpc.calls.append((method,copy.deepcopy(params)))
                count=int(params[0]['data'][74:138],16)
                return words(32,count,*([18]*count))
            if method=='eth_estimateGas':return hex(200000)
            if method=='eth_gasPrice':return hex(10**9)
            if method=='eth_getBalance':return hex(10**18)
            return original(method,params)
        f.rpc.call=call;p=Projection(f.config,f.rpc,clock=lambda:4000)
        result=Transactions(p,transaction_config(p)).plan_claims(dict(action='claim',wallet=addr(30),
            claims=[dict(token_id=str(f.rpc.nft_id),asset=ZERO,royalty=False)]))
        self.assertEqual(result['next_batch']['claim_operations'][0]['simulated_raw'],'18')
        self.assertEqual(result['planning']['trial_count'],1)
        counts={signature:sum(method=='eth_call' and params[0]['data']==calldata(signature)
            for method,params in f.rpc.calls) for signature in
            ('EXECUTION_PRICE_VERSION()','executionStrategy()','executionActive()','executionSourceRevision()')}
        self.assertEqual(counts,{'EXECUTION_PRICE_VERSION()':5,'executionStrategy()':1,
            'executionActive()':0,'executionSourceRevision()':0})
        self.assertNotIn('oracle',p.contracts)

    def test_identity_cache_requires_same_block_target_and_read_shape(self):
        class RPC:
            def __init__(self):self.count=0
            def call(self,method,params):
                self.count+=1
                return words(self.count)
        rpc=RPC();block={'blockHash':'0x'+'a'*64,'requireCanonical':True}
        reads=_SnapshotReads(rpc,block,{addr(1)})
        tx={'to':addr(1),'data':calldata('EXECUTION_PRICE_VERSION()')}
        first=reads.call('eth_call',[tx,block])
        self.assertEqual(reads.call('eth_call',[tx,block]),first)
        self.assertEqual(rpc.count,1)
        variants=([tx,{'blockHash':'0x'+'b'*64,'requireCanonical':True}],
            [tx,{'blockHash':block['blockHash'],'requireCanonical':False}],
            [tx,'latest'],[{**tx,'to':addr(2)},block],
            [{**tx,'from':addr(3)},block],[{**tx,'gas':'0x10000'},block])
        for params in variants:
            with self.subTest(params=params):
                a=reads.call('eth_call',params);b=reads.call('eth_call',params)
                self.assertNotEqual(a,b)
        other_request=_SnapshotReads(rpc,block,{addr(1)})
        self.assertNotEqual(other_request.call('eth_call',[tx,block]),first)

    def test_mutable_execution_prices_ownership_and_balances_are_never_cached(self):
        class RPC:
            def __init__(self):self.count=0
            def call(self,method,params):
                self.count+=1
                return words(self.count)
        rpc=RPC();block={'blockHash':'0x'+'a'*64,'requireCanonical':True}
        reads=_SnapshotReads(rpc,block,{addr(1)})
        for signature,args in (('executionActive()',()),('executionSourceRevision()',()),
                ('priceBounds(address)',(addr(2),)),('ownerOf(uint256)',(1,)),
                ('balanceOf(address)',(addr(3),))):
            with self.subTest(signature=signature):
                params=[{'to':addr(1),'data':calldata(signature,*args)},block]
                self.assertNotEqual(reads.call('eth_call',params),reads.call('eth_call',params))
