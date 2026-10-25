import contextlib,copy,io,json,tempfile
from pathlib import Path
import time
import unittest
from keeper.probe import probe,main,PROBE_FROM,APPROVAL,TRACE_GAS
from unittest.mock import patch
from zzz_ops.abi import calldata,keccak256
from tests_python.test_keeper import A, H
from zzz_ops.rpc import RpcError
from zzz_ops.errors import RemoteRPCError


class ProbeRpc:
    def __init__(self,*args,**kwargs):self.now=int(time.time());self.bad_receipt=False;self.calls=[]
    def call(self,method,params):
        self.calls.append((method,params))
        if method=='eth_getBlockByNumber':
            number=100 if params[0] in ('latest','safe','finalized') else int(params[0],16)
            return {'number':hex(number),'hash':H,'timestamp':hex(self.now),'transactions':[H]}
        if method in ('eth_call','eth_getStorageAt'):
            if method=='eth_call' and params[-1].get('blockHash')=='0x'+'00'*32:raise RemoteRPCError(method,-32001,'unavailable_block')
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
    def test_unknown_hash_transport_or_ambiguous_error_is_not_successful_rejection(self):
        failures=[RpcError('timeout SECRET'),RemoteRPCError('eth_call',-32602,'invalid_params'),
                  RemoteRPCError('eth_call',-32005,'rate_limited'),RemoteRPCError('eth_call',-32000)]
        for failure in failures:
            with self.subTest(error=type(failure).__name__,reason=getattr(failure,'reason',None)):
                rpc=ProbeRpc();original=rpc.call
                def call(method,params):
                    if method=='eth_call' and params[-1].get('blockHash')=='0x'+'00'*32:raise failure
                    return original(method,params)
                rpc.call=call
                report=probe(self.cfg,A,'0x18160ddd',factory=lambda *a,**k:rpc)
                self.assertFalse(report['compatibility_checks_passed'])
                failed=next(item for item in report['endpoints'][0]['checks'] if item['name']=='unknown_hash_rejected')
                self.assertNotIn('transport_status',failed)
    def test_results_arriving_after_deadline_are_not_accepted_or_followed_by_more_work(self):
        clock=[0];original=self.rpc.call
        def call(method,params):
            value=original(method,params);clock[0]=91;return value
        self.rpc.call=call
        with patch('keeper.probe.time.monotonic',side_effect=lambda:clock[0]):report=self.run_probe()
        self.assertEqual(len(self.rpc.calls),1)
        self.assertFalse(report['endpoints'][0]['checks'][0]['ok'])
        self.assertFalse(report['compatibility_checks_passed'])
    def test_unsupported_receipt_window_cannot_exceed_the_logical_call_budget(self):
        original=self.rpc.call
        def call(method,params):
            value=original(method,params)
            if method=='eth_getBlockByNumber':value['transactions']=[H]*8
            if method=='eth_getTransactionByHash':value['type']='0x64'
            return value
        self.rpc.call=call
        report=probe(self.cfg,A,'0x18160ddd',receipt_blocks=32,factory=lambda *a,**k:self.rpc)
        self.assertEqual(len(self.rpc.calls),100)
        self.assertFalse(report['compatibility_checks_passed'])

GENESIS='0x'+'19'*32
RUNTIME='0x'+keccak256(bytes.fromhex('6000')).hex()
ONE='0x'+f'{1:064x}'

class PreparationRpc(ProbeRpc):
    def __init__(self):
        super().__init__()
        self.trace={'type':'CALL','from':PROBE_FROM,'to':A,'value':'0x0',
            'input':calldata('approve(address,uint256)',PROBE_FROM,0),'output':ONE,
            'gas':hex(TRACE_GAS),'gasUsed':'0x6000','logs':[{'address':A,
            'topics':[APPROVAL,'0x'+PROBE_FROM[2:].rjust(64,'0'),'0x'+PROBE_FROM[2:].rjust(64,'0')],
            'data':'0x'+'0'*64}]}
    def call(self,method,params):
        if method=='debug_traceCall':
            self.calls.append((method,params));return copy.deepcopy(self.trace)
        if method=='eth_call' and params[0].get('data')==self.trace['input']:
            self.calls.append((method,params));return ONE
        result=super().call(method,params)
        if method=='eth_getBlockByNumber' and params[0]=='0x0':result['hash']=GENESIS
        return result

class PreparationProbeTests(unittest.TestCase):
    def run_probe(self,rpc,**kwargs):
        return probe({'chain_id':4663,'rpc_urls':['https://rpc.invalid/SECRET']},A,'0x18160ddd',
            profile='activation_api_v1',expected_genesis=kwargs.get('genesis',GENESIS),
            expected_runtime=kwargs.get('runtime',RUNTIME),factory=lambda *a,**k:rpc)
    def test_actual_approval_log_and_same_hash_are_required_without_any_send_or_override(self):
        rpc=PreparationRpc();report=self.run_probe(rpc)
        self.assertTrue(report['compatibility_checks_passed']);self.assertFalse(report['production_approved'])
        self.assertEqual(len(report['endpoints'][0]['checks']),13)
        trace=[params for method,params in rpc.calls if method=='debug_traceCall'][0]
        self.assertEqual(trace[1],{'blockHash':H,'requireCanonical':True})
        self.assertEqual(trace[2],{'tracer':'callTracer','timeout':'5s','tracerConfig':{'withLog':True}})
        self.assertEqual(trace[0]['value'],'0x0')
        self.assertEqual(trace[0]['data'],calldata('approve(address,uint256)',PROBE_FROM,0))
        self.assertTrue(all(method in ('eth_getBlockByNumber','eth_call','eth_getCode','eth_getStorageAt',
            'eth_gasPrice','eth_getTransactionByHash','eth_getTransactionReceipt','debug_traceCall') for method,_ in rpc.calls))
        self.assertNotIn('SECRET',json.dumps(report))
    def test_missing_or_mismatched_reviewed_pins_cannot_qualify(self):
        for field,value in (('genesis',None),('runtime',None),('runtime','0x'+'0'*64)):
            with self.subTest(field=field,value=value),self.assertRaises((ValueError,RpcError)):
                self.run_probe(PreparationRpc(),**{field:value})
        for field in ('genesis','runtime'):
            with self.subTest(field=field):
                rpc=PreparationRpc()
                self.assertFalse(self.run_probe(rpc,**{field:'0x'+'71'*32})['compatibility_checks_passed'])
                self.assertFalse(any(method=='debug_traceCall' for method,_ in rpc.calls))
    def test_trace_wrong_identity_value_output_or_missing_real_event_cannot_pass(self):
        changes=[{'from':'0x'+'11'*20},{'to':'0x'+'22'*20},{'value':'0x1'},{'value':1},
            {'input':'0x18160ddd'},{'output':'0x'},{'gasUsed':'0x00'},{'gas':'0x1000000'},
            {'logs':[]},{'error':'SECRET'}]
        for change in changes:
            with self.subTest(change=change):
                rpc=PreparationRpc();rpc.trace.update(change)
                # A malformed trace must not alter the independent eth_call output.
                original=rpc.call
                def call(method,params):
                    if method=='eth_call' and params[0].get('data','').startswith('0x095ea7b3'):return ONE
                    return original(method,params)
                rpc.call=call
                report=self.run_probe(rpc)
                self.assertFalse(report['compatibility_checks_passed']);self.assertNotIn('SECRET',json.dumps(report))
        for field,value in (('address','0x'+'22'*20),('topics',[APPROVAL]),('data',ONE)):
            with self.subTest(log_field=field):
                rpc=PreparationRpc();rpc.trace['logs'][0][field]=value
                self.assertFalse(self.run_probe(rpc)['compatibility_checks_passed'])
    def test_proxy_child_event_is_accepted_but_excessive_trace_is_not(self):
        rpc=PreparationRpc();logs=rpc.trace.pop('logs');rpc.trace['calls']=[{'type':'DELEGATECALL','logs':logs}]
        self.assertTrue(self.run_probe(rpc)['compatibility_checks_passed'])
        rpc.trace['calls']=[{}]*257
        self.assertFalse(self.run_probe(rpc)['compatibility_checks_passed'])
    def test_first_endpoint_missing_reference_does_not_hide_next_endpoint(self):
        first=ProbeRpc();second=ProbeRpc();second.now=first.now;original=first.call
        def call(method,params):
            if method=='eth_getBlockByNumber' and params[0]=='0x58':return None
            return original(method,params)
        first.call=call;clients=iter((first,second))
        report=probe({'chain_id':4663,'rpc_urls':['https://first.invalid','https://second.invalid']},
            A,'0x18160ddd',factory=lambda *a,**k:next(clients))
        self.assertEqual(len(report['endpoints']),2);self.assertIn('reference_error',report['endpoints'][0])
        self.assertEqual(len(report['endpoints'][1]['checks']),11)
        self.assertFalse(report['compatibility_checks_passed'])
    def test_cli_rejects_ambiguous_json_input_overwrite_and_secret_arguments_before_probe(self):
        with tempfile.TemporaryDirectory() as folder:
            config=Path(folder)/'rpc.json';output=Path(folder)/'report.json';output.write_text('old evidence')
            base=['--config',str(config),'--address',A,'--calldata','0x18160ddd','--output',str(output)]
            for raw in ('{"chain_id":4663,"chain_id":1,"rpc_urls":[]}',
                        '{"chain_id":NaN,"rpc_urls":[]}','x'*65537):
                config.write_text(raw)
                with patch('keeper.probe.probe') as observed,contextlib.redirect_stdout(io.StringIO()) as captured:
                    self.assertEqual(main(base),1)
                observed.assert_not_called();self.assertEqual(output.read_text(),'old evidence')
            config.write_text('{"chain_id":4663,"rpc_urls":[]}')
            with patch('keeper.probe.probe') as observed,contextlib.redirect_stdout(io.StringIO()) as captured:
                self.assertEqual(main(base[:-1]+[str(config)]),1)
                self.assertEqual(main(base+['--SECRET-URL','https://SECRET.invalid']),1)
            observed.assert_not_called();self.assertNotIn('SECRET',captured.getvalue())
