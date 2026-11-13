"""New probe transport regressions; no network, keys or old suite execution."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import keeper.probe as probe_module
from keeper.probe import APPROVAL, PROBE_FROM, TRACE_GAS, main, probe
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RemoteRPCError, RpcError
from zzz_ops.rpc import Rpc


TARGET = '0x'+'11'*20
HEADER = '0x'+'22'*32
GENESIS = '0x'+'33'*32
RUNTIME = '0x'+keccak256(bytes.fromhex('6000')).hex()
CONFIG = {'chain_id':4663, 'rpc_urls':['https://example.invalid/PRIVATE-URL']}
STAMP = 1800000000
ONE = '0x'+f'{1:064x}'


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration


class WireRpc(Rpc):
    """Exercise real chain checks, parser and error wrapping over inert bytes."""
    def __init__(self, urls, chain_id, *, clock, fail=None, advance=None, **kwargs):
        super().__init__(urls, chain_id, **kwargs)
        self.clock, self.fail, self.advance = clock, fail, advance
        self.posts = []

    def _read_http(self, url, raw):
        request = json.loads(raw)
        method, params = request['method'], request['params']
        self.posts.append({'method':method, 'at':self.clock.now, 'timeout':self.timeout})
        if self.advance:
            self.advance(self, request)
        failure = self.fail(self, request) if self.fail else None
        if isinstance(failure, int):
            raise HTTPError(url, failure, 'PRIVATE-ERROR', {}, None)
        if failure == 'rate':
            return json.dumps({'jsonrpc':'2.0','id':request['id'],
                'error':{'code':-32005,'message':'PRIVATE-ERROR'}}).encode()
        if method == 'eth_chainId':
            result = hex(self.chain_id)
        elif method == 'eth_getBlockByNumber':
            number = 100 if params[0] in ('latest','safe','finalized') else int(params[0],16)
            result = {'number':hex(number),'hash':GENESIS if number == 0 else HEADER,
                'timestamp':hex(STAMP),'transactions':[HEADER]}
        elif method == 'eth_call':
            if params[-1].get('blockHash') == '0x'+'0'*64:
                return json.dumps({'jsonrpc':'2.0','id':request['id'],
                    'error':{'code':-32001,'message':'header not found'}}).encode()
            result = ONE
        elif method == 'eth_getCode':
            result = '0x6000'
        elif method == 'eth_getStorageAt':
            result = '0x'+'0'*64
        elif method == 'eth_gasPrice':
            result = '0x1'
        elif method == 'eth_getTransactionByHash':
            result = {'type':'0x2'}
        elif method == 'eth_getTransactionReceipt':
            result = {'transactionHash':HEADER,'blockHash':HEADER,'gasUsed':'0x5208',
                'effectiveGasPrice':'0x1','status':'0x1'}
        elif method == 'debug_traceCall':
            result = {'type':'CALL','from':PROBE_FROM,'to':TARGET,'value':'0x0',
                'input':calldata('approve(address,uint256)',PROBE_FROM,0),'output':ONE,
                'gas':hex(TRACE_GAS),'gasUsed':'0x6000', 'logs':[{
                    'address':TARGET, 'topics':[APPROVAL,'0x'+PROBE_FROM[2:].rjust(64,'0'),
                        '0x'+PROBE_FROM[2:].rjust(64,'0')],'data':'0x'+'0'*64}]}
        else:
            raise AssertionError(method)
        return json.dumps({'jsonrpc':'2.0','id':request['id'],'result':result}).encode()


class ProbeTransportBudgetTests(unittest.TestCase):
    def run_probe(self, *, interval=None, fail=None, advance=None, urls=None, clock=None):
        clock = clock or Clock()
        clients = []
        def factory(*args, **kwargs):
            client = WireRpc(*args, **kwargs,clock=clock,fail=fail,advance=advance)
            clients.append(client)
            return client
        kwargs = {} if interval is None else {'request_interval_ms':interval}
        config = {**CONFIG,'rpc_urls':urls or CONFIG['rpc_urls']}
        with patch('keeper.probe.time.monotonic',side_effect=clock.monotonic), \
                patch('keeper.probe.time.sleep',side_effect=clock.sleep), \
                patch('keeper.probe.time.time',return_value=STAMP):
            report = probe(config,TARGET,'0x18160ddd',profile='activation_api_v1',
                expected_genesis=GENESIS,expected_runtime=RUNTIME,factory=factory,**kwargs)
        return report, clients, clock

    def test_opt_in_paces_every_actual_post_including_internal_chain_checks(self):
        report, clients, clock = self.run_probe(interval=1500)
        self.assertTrue(report['compatibility_checks_passed'])
        self.assertFalse(report['production_approved'])
        self.assertEqual(report['request_interval_ms'],1500)
        posts = clients[0].posts
        self.assertEqual(len(report['endpoints'][0]['checks']),13)
        self.assertGreater(len(posts),30)
        self.assertTrue(all(later['at']-earlier['at'] >= 1.5 for earlier,later in zip(posts,posts[1:])))
        self.assertEqual(posts[0]['method'],'eth_chainId')
        self.assertEqual(posts[1]['method'],'eth_getBlockByNumber')
        self.assertTrue(all(row['method'] in Rpc.READ_METHODS for row in posts))
        self.assertNotIn('PRIVATE',json.dumps(report))
        self.assertLess(clock.now,90)

    def test_default_does_not_sleep_or_add_pacing_metadata(self):
        report, clients, clock = self.run_probe()
        self.assertTrue(report['compatibility_checks_passed'])
        self.assertEqual(clock.sleeps,[])
        self.assertNotIn('request_interval_ms',report)
        self.assertTrue(all(row['timeout'] == 8 for row in clients[0].posts))

    def test_access_denial_stops_only_the_affected_endpoint(self):
        for status in (401,403,429):
            with self.subTest(status=status):
                def fail(client, request):
                    if client.active_url.startswith('https://first.') and request['method'] == 'eth_getCode':
                        return status
                report, clients, _clock = self.run_probe(fail=fail,
                    urls=['https://first.invalid/PRIVATE','https://second.invalid/PRIVATE'])
                methods = [row['method'] for row in clients[0].posts]
                self.assertEqual(methods[-1],'eth_getCode')
                self.assertEqual(methods.count('eth_getCode'),1)
                self.assertTrue(all(row['ok'] for row in report['endpoints'][1]['checks']))
                self.assertFalse(report['compatibility_checks_passed'])
                failure = next(row for row in report['endpoints'][0]['checks'] if row['name'] == 'canonical_hash_code')
                self.assertEqual(failure['transport_status'],status)
                self.assertNotIn('PRIVATE',json.dumps(report))

    def test_json_rpc_rate_limit_stops_further_transport_without_relabeling_unknown_hash(self):
        def fail(_client, request):
            if request['method'] == 'eth_getCode':return 'rate'
        report, clients, _clock = self.run_probe(fail=fail)
        self.assertEqual(clients[0].posts[-1]['method'],'eth_getCode')
        failure = next(row for row in report['endpoints'][0]['checks'] if row['name'] == 'canonical_hash_code')
        self.assertEqual(failure['remote_error'],{'code':-32005,'reason':'rate_limited'})
        self.assertFalse(report['compatibility_checks_passed'])

    def test_deadline_between_chain_check_and_method_prevents_second_post(self):
        def advance(client, request):
            if request['method'] == 'eth_chainId':client.clock.now=90
        report, clients, _clock = self.run_probe(advance=advance)
        self.assertEqual([row['method'] for row in clients[0].posts],['eth_chainId'])
        self.assertFalse(report['compatibility_checks_passed'])

    def test_pacing_cannot_start_a_post_at_or_after_the_endpoint_deadline(self):
        report, clients, clock = self.run_probe(interval=5000)
        self.assertEqual(clients[0].posts[-1]['at'],85)
        self.assertEqual(len(clients[0].posts),18)
        self.assertTrue(all(row['at']<90 for row in clients[0].posts))
        self.assertFalse(report['compatibility_checks_passed'])
        self.assertLessEqual(clock.now,90)

    def test_timeout_is_clamped_to_remaining_endpoint_budget_and_restored(self):
        def advance(client, request):
            if len(client.posts) == 1:client.clock.now=87
        report, clients, _clock = self.run_probe(advance=advance)
        self.assertTrue(report['compatibility_checks_passed'])
        self.assertEqual(clients[0].posts[0]['timeout'],8)
        self.assertEqual(clients[0].posts[1]['timeout'],3)
        self.assertEqual(clients[0].timeout,8)

    def test_clock_crossing_during_timeout_capture_does_not_start_transport(self):
        clock=Clock();client=WireRpc(CONFIG['rpc_urls'],4663,clock=clock,timeout=8,retries=1)
        raw=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]}).encode()
        # Constructor/check/check/final capture; no elapsed-time assumption can
        # authorize a zero or negative transport timeout at the final boundary.
        with patch('keeper.probe.time.monotonic',side_effect=[0,0,0,90]):
            budget=probe_module._EndpointBudget(client,0)
            with self.assertRaises(TimeoutError):budget.transport(CONFIG['rpc_urls'][0],raw)
        self.assertEqual(client.posts,[])
        self.assertEqual(client.timeout,8)

    def test_remote_error_cause_scan_remains_bounded_for_cycles_and_deep_chains(self):
        cycle=RpcError('PRIVATE');cycle.__cause__=cycle
        self.assertIsNone(probe_module._remote_error(cycle))
        remote=RemoteRPCError('eth_call',-32005,'rate_limited')
        root=remote
        for _ in range(4):
            wrapper=RpcError('PRIVATE');wrapper.__cause__=root;root=wrapper
        self.assertIsNone(probe_module._remote_error(root))
        short=RpcError('PRIVATE');short.__cause__=remote
        self.assertIs(probe_module._remote_error(short),remote)

    def test_invalid_interval_rejects_before_client_construction(self):
        for value in (-1,5001,True,1.5,'1500',None,float('nan'),float('inf')):
            with self.subTest(value=repr(value)), patch('keeper.probe.Rpc') as network:
                with self.assertRaises(ValueError):
                    probe(CONFIG,TARGET,'0x18160ddd',request_interval_ms=value,factory=network)
                network.assert_not_called()

    def test_injected_logical_only_client_cannot_claim_transport_pacing(self):
        class LogicalOnly:
            def call(self,*_args):raise AssertionError('Must reject before calls')
        with self.assertRaises(ValueError):
            probe(CONFIG,TARGET,'0x18160ddd',request_interval_ms=1500,factory=lambda *_a,**_k:LogicalOnly())

    def test_cli_passes_explicit_pacing_without_changing_other_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/'rpc.json'; output=Path(directory)/'result.json'
            config.write_text(json.dumps(CONFIG))
            result={'compatibility_checks_passed':True,'endpoints':[{}]}
            with patch('keeper.probe.probe',return_value=result) as observed, \
                    contextlib.redirect_stdout(io.StringIO()):
                status=main(['--config',str(config),'--address',TARGET,'--calldata','0x18160ddd',
                    '--output',str(output),'--request-interval-ms','1500'])
            self.assertEqual(status,0)
            self.assertEqual(observed.call_args.kwargs['request_interval_ms'],1500)
            self.assertEqual(observed.call_args.kwargs['confirmations'],12)
            self.assertEqual(observed.call_args.kwargs['receipt_blocks'],12)
            self.assertEqual(observed.call_args.kwargs['profile'],'keeper_v1')
            self.assertTrue(json.loads(output.read_text())['compatibility_checks_passed'])

    def test_cli_invalid_pacing_preserves_old_evidence_before_any_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/'rpc.json'; output=Path(directory)/'result.json'
            config.write_text(json.dumps(CONFIG));output.write_text('old evidence')
            for value in ('-1','5001','1.5','nan','SECRET'):
                with self.subTest(value=value), patch('keeper.probe.probe') as observed, \
                        contextlib.redirect_stdout(io.StringIO()) as captured:
                    status=main(['--config',str(config),'--address',TARGET,'--calldata','0x18160ddd',
                        '--output',str(output),'--request-interval-ms',value])
                    self.assertEqual(status,1)
                    observed.assert_not_called()
                    self.assertEqual(output.read_text(),'old evidence')
                    self.assertNotIn('SECRET',captured.getvalue())


if __name__ == '__main__':
    unittest.main()
