"""Local launcher boundaries only; no unchanged contract regression."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('popl_local_stack',Path(__file__).resolve().parents[1]/'scripts/local-stack.py')
lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)

class LocalReadTests(unittest.TestCase):
    def test_optional_history_failure_is_unavailable_not_zero_or_a_portfolio_failure(self):
        p=object.__new__(lab.Lab)
        p.api=SimpleNamespace(earnings=Mock(side_effect=lab.RpcError('secret endpoint detail')))
        with patch('builtins.print') as log:
            self.assertEqual(p.optional_earnings('1'),{'available':False,'reason':'earnings_unavailable'})
            self.assertNotIn('secret',str(log.call_args))
        p.api.earnings.assert_called_once_with('1')
        p.api.earnings=Mock(side_effect=lab.WorkLimit('deadline'))
        with self.assertRaises(lab.WorkLimit):p.optional_earnings('1')
        p.api.earnings.assert_called_once_with('1')

    def test_optional_history_success_is_not_rewritten(self):
        p=object.__new__(lab.Lab);result={'available':True,'all_time_usd_at_current_price_18':{'royalties':None}}
        p.api=SimpleNamespace(earnings=Mock(return_value=result))
        self.assertIs(p.optional_earnings('2'),result)

    def test_state_skips_dormant_history_without_weakening_core_failure(self):
        p=object.__new__(lab.Lab);p.sync=Mock();p.read_rpc=SimpleNamespace(memo={},aggregation=False)
        p.ids=lambda:['1','2'];p.operations=SimpleNamespace(revision=0);p.uncertain=False
        p.accounts=['operator','alice','bob'];p.contracts={};p.pool='pool';p.tokens=[];p.receipts=[]
        positions=[{'token_id':'1','position':{'activated':True},'claimable':{'lp':['confirmed']}},
                   {'token_id':'2','position':{'activated':False}}]
        p.api=SimpleNamespace(nft=Mock(side_effect=positions),protocol=Mock(return_value={'confirmed':True}),
                             earnings=Mock(side_effect=[lab.RpcError('history only'),{'available':True}]))
        with patch('builtins.print'):result=p.state()
        self.assertEqual(result['nfts'][0]['claimable']['lp'],['confirmed'])
        self.assertFalse(result['nfts'][0]['earnings']['available'])
        self.assertEqual([call.args for call in p.api.earnings.call_args_list],[('1',),(None,)])
        self.assertFalse(p.read_rpc.aggregation);self.assertEqual(p.read_rpc.memo,{})
        p.api.nft=Mock(side_effect=lab.ProjectionError('core failure'))
        with self.assertRaises(lab.ProjectionError):p.state()
        self.assertFalse(p.read_rpc.aggregation)
    def test_only_exact_hash_bound_reads_are_deduplicated(self):
        rpc=lab.LocalReadRPC(['http://127.0.0.1:1234'],31337);rpc.aggregation=True;rpc.memo={}
        block={'blockHash':'0x'+'11'*32,'requireCanonical':True}
        with patch.object(lab.Rpc,'call',return_value='0xab') as upstream:
            for _ in range(2):rpc.call('eth_getCode',['0x'+'22'*20,block])
            self.assertEqual(upstream.call_count,1)
            rpc.call('eth_getCode',['0x'+'22'*20,dict(block,blockHash='0x'+'33'*32)])
            for _ in range(2):rpc.call('eth_getCode',['0x'+'22'*20,'latest'])
            for _ in range(2):rpc.call('eth_getBlockByNumber',['latest',False])
            self.assertEqual(upstream.call_count,6)
    def test_cache_is_disabled_between_aggregates(self):
        rpc=lab.LocalReadRPC(['http://127.0.0.1:1234'],31337);rpc.memo={}
        block={'blockHash':'0x'+'11'*32,'requireCanonical':True}
        with patch.object(lab.Rpc,'call',side_effect=['0xab','0xcd']) as upstream:
            self.assertNotEqual(rpc.call('eth_getCode',['addr',block]),rpc.call('eth_getCode',['addr',block]))
            self.assertEqual(upstream.call_count,2)
    def test_code_cache_does_not_cache_address_or_skip_reads(self):
        p=object.__new__(lab.LocalProjection)
        class RPC:
            code='0xab';calls=0
            def call(self,*args):self.calls+=1;return self.code
        p.rpc=RPC();expected=lab.runtime_hash('0xab')
        p._code('address',expected,{});p._code('address',expected,{})
        self.assertEqual(p.rpc.calls,2)
        p.rpc.code='0xcd'
        with self.assertRaises(lab.ProjectionError):p._code('address',expected,{})
    def test_missing_and_unbounded_runtime_rejected(self):
        p=object.__new__(lab.LocalProjection)
        for code in ['0x','0xx1','0x1','0x'+'11'*24577,None]:
            with self.subTest(code=str(code)[:12]):
                class RPC:
                    def call(self,*args):return code
                p.rpc=RPC()
                with self.assertRaises(lab.ProjectionError):p._code('address','anything',{})
    def test_local_identity_guard_checks_owned_process(self):
        p=object.__new__(lab.Lab);p.process=None
        with self.assertRaises(RuntimeError):p.guard()
    def test_external_account_rejected_before_simulation(self):
        p=object.__new__(lab.Lab);p.guard=lambda:None;p.accounts=['local']
        with self.assertRaises(ValueError):p.simulate({'from':'public-wallet'})
    def test_local_value_cap(self):
        p=object.__new__(lab.Lab);p.guard=lambda:None;p.accounts=['local']
        with self.assertRaises(ValueError):p.simulate({'from':'local','value':hex(lab.UNIT+1)})

if __name__=='__main__':unittest.main()
