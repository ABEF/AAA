"""Bounded transport/config and transient upkeep faults; no signer or public RPC."""
import copy
import http.server
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, CONFIRMATION_RESETS
from keeper.rebalance_confirmation import PORTFOLIO_STATE_NAMESPACE
from tests_python import test_keeper as fixtures
from tests_python.test_keeper_policy_v6 import PolicyRPC
from tests_python.test_keeper_compound_range_policy import words
from zzz_ops.errors import WorkLimit
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.work_budget import Budget, BudgetedRPC, request_scope


class _Clock:
    def __init__(self): self.now=0.0
    def __call__(self): return self.now


class _ProgressResponse(io.BytesIO):
    """Old read waits for the whole body; read1 returns each timed fragment."""
    def __init__(self,clock,body,step=.25):
        super().__init__(body);self.clock=clock;self.body=body;self.step=step;self.delivered=0
    def read(self,size=-1):
        self.clock.now+=2
        data=super().read(size);self.delivered+=len(data);return data
    def read1(self,size=-1):
        self.clock.now+=self.step
        data=super().read(min(size,7));self.delivered+=len(data);return data


class RPCProgressDeadlineTests(unittest.TestCase):
    def test_slow_progress_cannot_reset_the_attempt_body_deadline(self):
        clock=_Clock();body=_ProgressResponse(clock,b'x'*200)
        rpc=Rpc(['https://rpc.invalid'],1,timeout=1,retries=1)
        with patch.object(rpc._opener,'open',return_value=body),patch('zzz_ops.rpc.time.monotonic',clock):
            with self.assertRaisesRegex(RpcError,'deadline'):rpc._read_http(rpc.active_url,b'{}')
        self.assertTrue(body.closed);self.assertLess(body.delivered,len(body.body))

    def test_request_budget_stops_stream_before_complete_payload(self):
        clock=_Clock();body=_ProgressResponse(clock,b'{"jsonrpc":"2.0","id":1,"result":"0x1"}')
        rpc=Rpc(['https://rpc.invalid'],1,timeout=10,retries=1)
        with patch.object(rpc._opener,'open',return_value=body),patch('zzz_ops.rpc.time.monotonic',clock):
            with self.assertRaises(WorkLimit):
                with request_scope(Budget(seconds=.5,clock=clock)):
                    rpc._post(rpc.active_url,'eth_chainId',[])
        self.assertTrue(body.closed);self.assertLess(body.delivered,len(body.body))

    def test_header_delay_consumes_body_attempt_budget(self):
        clock=_Clock();body=_ProgressResponse(clock,b'x'*100)
        rpc=Rpc(['https://rpc.invalid'],1,timeout=1,retries=1)
        def opened(*args,**kwargs):clock.now=1.1;return body
        with patch.object(rpc._opener,'open',side_effect=opened),patch('zzz_ops.rpc.time.monotonic',clock):
            with self.assertRaisesRegex(RpcError,'deadline'):rpc._read_http(rpc.active_url,b'{}')
        self.assertTrue(body.closed);self.assertEqual(body.delivered,0)

    def test_fast_fragmented_response_is_complete_and_identity_checked(self):
        clock=_Clock();body=_ProgressResponse(clock,b'{"jsonrpc":"2.0","id":1,"result":"0x9"}',step=.01)
        rpc=Rpc(['https://rpc.invalid'],1,timeout=1,retries=1)
        with patch.object(rpc._opener,'open',return_value=body),patch('zzz_ops.rpc.time.monotonic',clock):
            self.assertEqual(rpc._post(rpc.active_url,'eth_blockNumber',[]),'0x9')
        self.assertTrue(body.closed);self.assertEqual(body.delivered,len(body.body))

    def test_standard_http_content_length_and_chunked_readers_remain_compatible(self):
        for chunked in (False,True):
            class Handler(http.server.BaseHTTPRequestHandler):
                protocol_version='HTTP/1.1'
                def do_POST(self):
                    request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    body=json.dumps({'jsonrpc':'2.0','id':request['id'],
                        'result':'0x1' if request['method']=='eth_chainId' else '0x99'}).encode()
                    self.send_response(200);self.send_header('Content-Type','application/json')
                    self.send_header('Connection','close')
                    self.send_header('Transfer-Encoding','chunked') if chunked else self.send_header('Content-Length',str(len(body)))
                    self.end_headers()
                    for i in range(0,len(body),7):
                        part=body[i:i+7]
                        self.wfile.write((f'{len(part):x}\r\n'.encode()+part+b'\r\n') if chunked else part)
                        self.wfile.flush()
                    if chunked:self.wfile.write(b'0\r\n\r\n');self.wfile.flush()
                def log_message(self,*args):pass
            server=http.server.HTTPServer(('127.0.0.1',0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                # Test sockets are loopback only; do not consult host proxy config.
                with self.subTest(chunked=chunked),patch('urllib.request.getproxies',return_value={}):
                    rpc=Rpc([f'http://127.0.0.1:{server.server_port}'],1,timeout=2,retries=1)
                    self.assertEqual(rpc.call('eth_blockNumber'),'0x99')
            finally:server.shutdown();server.server_close();thread.join(2)
            self.assertFalse(thread.is_alive())


class MaintenanceConfigurationRecoveryTests(unittest.TestCase):
    def test_override_bucket_ids_fit_the_onchain_uint256_domain(self):
        f=fixtures.PoolKeeperTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        for bucket in (1<<256,10**78):
            cfg=copy.deepcopy(f.cfg);cfg['bucket_overrides']={str(bucket):{'harvest':False}}
            with self.subTest(bucket=bucket),patch('keeper.monitor.subprocess.run') as signer:
                with self.assertRaisesRegex(ValueError,'bucket'):
                    Keeper(cfg,rpc=f.rpc)
                signer.assert_not_called()
        cfg=copy.deepcopy(f.cfg);cfg['bucket_overrides']={str((1<<256)-1):{'harvest':False}}
        Keeper(cfg,rpc=f.rpc)

    def test_unknown_defaults_and_overrides_fail_before_signing(self):
        f=fixtures.PoolKeeperTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        f.k.save();before=f.k.path.read_bytes()
        for settings in ({'rebalance':False},{'harvest_interva_seconds':3600},{'secret_endpoint_do_not_echo':False}):
            for override in (False,True):
                cfg=copy.deepcopy(f.cfg)
                cfg['bucket_overrides']={'7':settings} if override else {}
                if not override:cfg['maintenance']=settings
                with self.subTest(settings=settings,override=override),patch('keeper.monitor.subprocess.run') as signer:
                    with self.assertRaisesRegex(ValueError,'Unknown maintenance') as observed:Keeper(cfg,rpc=f.rpc)
                    self.assertNotIn('secret_endpoint',str(observed.exception));signer.assert_not_called()
                    self.assertEqual(before,f.k.path.read_bytes())

    def test_pending_confirmation_precedes_invalid_new_maintenance_values(self):
        for settings in ({'harvest':'false'},{'sync_external_rewards':'false'},{'rebalance':False}):
            f=fixtures.KeeperTests('runTest');f.setUp();self.addCleanup(f.doCleanups);f.receipt()
            original=copy.deepcopy(f.k.state['pending']);f.k.save();f.cfg['maintenance']=settings
            with self.subTest(settings=settings),patch('keeper.monitor.subprocess.run') as signer:
                recovered=Keeper(f.cfg,rpc=f.rpc)
                self.assertEqual(recovered.state['pending'],original)
                with self.assertRaises(ValueError):recovered.cycle()
                self.assertIsNone(recovered.state['pending']);self.assertEqual(recovered.state['next_nonce'],original['nonce']+1)
                saved=json.loads(recovered.path.read_text());self.assertIsNone(saved['pending'])
                self.assertEqual(saved['next_nonce'],original['nonce']+1);signer.assert_not_called()
                # Correct config, preserve paid receipt/nonce; no replay/adoption.
                f.cfg['maintenance']={'harvest':False};again=Keeper(f.cfg,rpc=f.rpc)
                self.assertEqual(again.state,saved);signer.assert_not_called()


class PortfolioTransientFaultTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.rpc=PolicyRPC(Path(tmp.name)/'state.json');self.cfg=self.rpc.cfg;self.k=Keeper(self.cfg,rpc=self.rpc)
        self.k._confirmation_seen_buckets.add(7)
        self.rpc.position[6]=self.rpc.now-43200
        self.rpc.record=[1,self.rpc.now-600,self.rpc.now,2]

    def due(self):
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):
            return self.k._rebalance_due(7,words(*self.rpc.position),self.rpc.now,force=True)

    def test_one_minute_price_condition_fault_drops_jitter_and_survives_restart(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.assertFalse(self.due())
        self.assertGreater(self.k.state[PORTFOLIO_STATE_NAMESPACE]['7']['execute_after'],0)
        read=self.rpc.read
        def failed(target,method,*args,**kwargs):
            if method=='condition(uint256)':raise RpcError('inert price/condition unavailable')
            return read(target,method,*args,**kwargs)
        with patch.object(self.rpc,'read',side_effect=failed),self.assertRaises(RpcError):self.due()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7']);self.assertNotIn('7',self.k.state.get(PORTFOLIO_STATE_NAMESPACE,{}))
        self.rpc.now+=60;self.k=Keeper(self.cfg,rpc=self.rpc)
        with patch('keeper.monitor.subprocess.run') as signer:self.assertFalse(self.due());signer.assert_not_called()
        self.assertEqual(self.k._rebalance_reset_due,7);self.assertIsNone(self.k.state['pending'])

    def test_fast_market_reversal_invalidates_mature_evidence_before_submission(self):
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self.assertFalse(self.due())
        self.rpc.now+=60;self.rpc.physical_side=1 # independent reference remains2.
        with patch('keeper.monitor.subprocess.run') as signer:self.assertFalse(self.due());signer.assert_not_called()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7']);self.assertNotIn('7',self.k.state.get(PORTFOLIO_STATE_NAMESPACE,{}))
        self.rpc.reference=1 # Recovery cannot make old-side evidence valid again.
        self.assertFalse(self.due());self.assertEqual(self.k._rebalance_reset_due,7)


class ReviewedEndpointTests(unittest.TestCase):
    def test_mutating_the_source_config_does_not_replace_reviewed_endpoints(self):
        urls=['https://reviewed.invalid'];rpc=Rpc(urls,1,retries=1)
        urls[0]='http://unreviewed.invalid'
        self.assertEqual(rpc.active_url,'https://reviewed.invalid')

    def test_clearing_the_source_config_does_not_break_bounded_failover(self):
        urls=['https://a.invalid','https://b.invalid'];rpc=Rpc(urls,1,retries=1)
        urls.clear();seen=[]
        def respond(url,method,params):
            seen.append((url,method))
            if url=='https://a.invalid':raise OSError('inert failure')
            return '0x1' if method=='eth_chainId' else '0x9'
        with patch.object(rpc,'_post',side_effect=respond),patch('zzz_ops.rpc.time.sleep'):
            self.assertEqual(rpc.call('eth_blockNumber'),'0x9')
        self.assertEqual(seen,[('https://a.invalid','eth_chainId'),
            ('https://b.invalid','eth_chainId'),('https://b.invalid','eth_blockNumber')])

    def test_expanding_the_source_config_cannot_expand_the_retry_budget(self):
        urls=['https://reviewed.invalid'];rpc=Rpc(urls,1,retries=1)
        urls.extend(['https://unreviewed.invalid']*9)
        with patch.object(rpc,'_post',side_effect=OSError('inert failure')) as post,patch('zzz_ops.rpc.time.sleep'):
            with self.assertRaises(RpcError):rpc.call('eth_blockNumber')
        self.assertEqual(post.call_count,1)


class _BudgetTransport:
    def __init__(self,clock=None):self.calls=[];self.unmetered=[];self.clock=clock
    def call(self,method,params):
        self.calls.append((method,params))
        if self.clock:self.clock.now=2
        return '0x99'
    def eth_call(self,*args,**kwargs):
        self.unmetered.append((args,kwargs))
        return 'unmetered'


class ContractReadBudgetTests(unittest.TestCase):
    def test_contract_reads_share_call_budget_and_preserve_exact_sender_and_block(self):
        transport=_BudgetTransport();rpc=BudgetedRPC(transport)
        selector={'blockHash':'0x'+'7'*64,'requireCanonical':True}
        with request_scope(Budget(calls=1)):
            self.assertEqual(rpc.eth_call(fixtures.B,'0x12345678',sender=fixtures.A,block=selector),'0x99')
            with self.assertRaises(WorkLimit):rpc.eth_call(fixtures.B,'0x12345678')
        self.assertEqual(transport.unmetered,[])
        self.assertEqual(transport.calls,[('eth_call',[{'to':fixtures.B,'data':'0x12345678','from':fixtures.A},selector])])

    def test_contract_read_result_is_discarded_after_deadline(self):
        clock=_Clock();transport=_BudgetTransport(clock);rpc=BudgetedRPC(transport)
        with request_scope(Budget(seconds=1,clock=clock)):
            try:
                with self.assertRaises(WorkLimit):rpc.eth_call(fixtures.B,'0x12345678')
            finally:clock.now=0
        self.assertEqual(len(transport.calls),1);self.assertEqual(transport.unmetered,[])

    def test_expired_contract_read_cannot_start_the_injected_transport(self):
        clock=_Clock();transport=_BudgetTransport();rpc=BudgetedRPC(transport)
        with request_scope(Budget(seconds=1,clock=clock)):
            clock.now=2
            try:
                with self.assertRaises(WorkLimit):rpc.eth_call(fixtures.B,'0x12345678')
            finally:clock.now=0
        self.assertEqual(transport.calls,[]);self.assertEqual(transport.unmetered,[])


if __name__=='__main__':unittest.main()
