import json
import time
import unittest
from keeper.probe import probe
from tests_python.test_keeper import A, H
from zzz_ops.rpc import RpcError


class ProbeRpc:
    def __init__(self,*args,**kwargs):self.now=int(time.time());self.bad_receipt=False;self.calls=[]
    def call(self,method,params):
        self.calls.append((method,params))
        if method=='eth_getBlockByNumber':
            number=100 if params[0] in ('latest','safe','finalized') else int(params[0],16)
            return {'number':hex(number),'hash':H,'timestamp':hex(self.now),'transactions':[H]}
        if method in ('eth_call','eth_getStorageAt'):
            if method=='eth_call' and params[-1].get('blockHash')=='0x'+'00'*32:raise RpcError('Unknown canonical block')
            return '0x'+'0'*64
        if method=='eth_getCode':return '0x6000'
        if method=='eth_gasPrice':return '0x1'
        if method=='eth_getTransactionByHash':return {'type':'0x2'}
        if method=='eth_getTransactionReceipt':
            data={'transactionHash':H,'blockHash':H,'gasUsed':'0x5208','effectiveGasPrice':'0x1','gasUsedForL1':'0x10','status':'0x1'}
            if self.bad_receipt:data.pop('effectiveGasPrice')
            return data
        raise AssertionError(method)


class ProbeTests(unittest.TestCase):
    def setUp(self):self.rpc=ProbeRpc();self.cfg={'chain_id':4663,'rpc_urls':['https://rpc.invalid/SECRET']}
    def run_probe(self):return probe(self.cfg,A,'0x18160ddd',factory=lambda *a,**k:self.rpc)
    def test_reads_only_and_report_contains_no_endpoint_secrets(self):
        report=self.run_probe()
        self.assertTrue(report['compatibility_checks_passed']);self.assertFalse(report['production_approved'])
        self.assertEqual(len(report['endpoints'][0]['receipts']),3)
        self.assertNotIn('SECRET',json.dumps(report));self.assertTrue(all('send' not in method for method,_ in self.rpc.calls))
    def test_stale_endpoint_cannot_pass(self):
        self.rpc.now-=1000;self.assertFalse(self.run_probe()['compatibility_checks_passed'])
    def test_incomplete_fee_receipt_cannot_pass(self):
        self.rpc.bad_receipt=True;self.assertFalse(self.run_probe()['compatibility_checks_passed'])
    def test_unsupported_hash_call_is_reported_not_substituted_with_latest(self):
        original=self.rpc.call
        def call(method,params):
            if method=='eth_call':raise ValueError('SECRET')
            return original(method,params)
        self.rpc.call=call;report=self.run_probe()
        self.assertFalse(report['compatibility_checks_passed']);self.assertNotIn('SECRET',json.dumps(report))
    def test_bounds_and_calldata_rejected_before_network(self):
        for kwargs in ({'receipt_blocks':33},{'confirmations':1001}):
            with self.assertRaises(ValueError):probe(self.cfg,A,'0x18160ddd',**kwargs)
        with self.assertRaises(ValueError):probe(self.cfg,A,'not calldata')
    def test_silent_latest_substitution_cannot_pass(self):
        original=self.rpc.call
        def call(method,params):
            if method=='eth_call':return '0x'+'0'*64
            return original(method,params)
        self.rpc.call=call;self.assertFalse(self.run_probe()['compatibility_checks_passed'])
