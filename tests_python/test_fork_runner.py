import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('fork_runner',Path(__file__).resolve().parents[1]/'scripts/run-fork-checks.py')
RUNNER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(RUNNER)
UPSTREAM='https://archive.invalid/path'
def request(method='eth_getStorageAt',request_id=7):
    return json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':['0x'+'11'*20,'0x0','0x344ef1d']}).encode()
def response(request_id=7,**fields):return json.dumps({'jsonrpc':'2.0','id':request_id,**fields}).encode()
class Clock:
    def __init__(self):self.now=100.0;self.waits=[]
    def __call__(self):return self.now
    def sleep(self,seconds):self.waits.append(seconds);self.now+=seconds

class ForkRelayTests(unittest.TestCase):
    def setUp(self):self.clock=Clock();self.calls=[];self.replies=[(200,response(result='0x42'))]
    def post(self,body):
        self.calls.append((self.clock(),body))
        reply=self.replies.pop(0)
        if isinstance(reply,Exception):raise reply
        return reply
    def relay(self,upstream=UPSTREAM):return RUNNER.Relay(upstream,post=self.post,clock=self.clock,sleep=self.clock.sleep)
    def test_forwards_exact_request_block_tag_id_and_result_bytes(self):
        body=request();expected=self.replies[0][1]
        self.assertEqual(self.relay().handle(body),(200,expected));self.assertEqual(self.calls[0][1],body)
        self.assertEqual(json.loads(self.calls[0][1])['params'][-1],'0x344ef1d')
    def test_forwards_string_ids_and_jsonrpc_error_without_retry(self):
        upstream_error=response('abc',error={'code':-32000,'message':'historical state unavailable'})
        self.replies=[(200,upstream_error)]
        self.assertEqual(self.relay().handle(request(request_id='abc')),(200,upstream_error));self.assertEqual(len(self.calls),1)
    def test_confirmed_fork_environment_gas_price_read_is_forwarded(self):
        body=json.dumps({'jsonrpc':'2.0','id':7,'method':'eth_gasPrice','params':[]}).encode()
        self.assertEqual(self.relay().handle(body)[0],200);self.assertEqual(self.calls[0][1],body)
    def test_denies_write_sign_admin_wallet_and_unknown_methods(self):
        relay=self.relay()
        for method in ('eth_sendRawTransaction','eth_sendTransaction','eth_sign','personal_sign','wallet_sendCalls','admin_addPeer','unknown'):
            with self.subTest(method=method):
                status,body=relay.handle(request(method));self.assertEqual(status,403);self.assertEqual(json.loads(body)['id'],7)
                self.assertIn(method,json.loads(body)['error']['message'])
        self.assertFalse(self.calls)
    def test_invalid_method_identifiers_are_never_echoed(self):
        for method in ('https://user:secret@rpc.invalid/path','private value with spaces','x'*65):
            with self.subTest(method=method):
                status,body=self.relay().handle(request(method));self.assertEqual(status,403)
                self.assertNotIn(method.encode(),body);self.assertIn('invalid',json.loads(body)['error']['message'])
    def test_malformed_batch_or_oversized_requests_never_reach_upstream(self):
        for body in (b'broken',b'[]',b'{}',b'\xff',b'x'*(RUNNER.MAX_REQUEST+1),
            json.dumps({'jsonrpc':'2.0','id':True,'method':'eth_call','params':[]}).encode()):
            with self.subTest(length=len(body)):self.assertNotEqual(self.relay().handle(body)[0],200)
        self.assertFalse(self.calls)
    def test_serial_cadence_is_enforced_with_fake_clock(self):
        self.replies=[(200,response(result='0x42'))]*3;relay=self.relay()
        for _ in range(3):self.assertEqual(relay.handle(request())[0],200)
        self.assertEqual([stamp for stamp,_ in self.calls],[100.0,101.25,102.5])
        self.assertEqual(self.clock.waits,[1.25,1.25])
    def test_only_429_retries_are_bounded_and_keep_original_request(self):
        self.replies=[(429,b'limited'),(429,b'limited'),(200,response(result='0x42'))]
        body=request();self.assertEqual(self.relay().handle(body)[0],200)
        self.assertEqual(len(self.calls),3);self.assertTrue(all(sent==body for _,sent in self.calls))
        self.assertEqual(self.clock.waits,[6,12])
    def test_persistent_429_fails_after_three_attempts_without_fallback(self):
        self.replies=[(429,b'limited')]*3
        status,body=self.relay().handle(request());self.assertEqual(status,429);self.assertEqual(len(self.calls),3)
        self.assertIn('three attempts',json.loads(body)['error']['message'])
    def test_http_and_transport_failures_are_not_retried_or_leaked(self):
        for reply in ((500,UPSTREAM.encode()),OSError(UPSTREAM)):
            with self.subTest(reply=type(reply).__name__):
                self.replies=[reply];self.calls=[];status,body=self.relay().handle(request())
                self.assertGreaterEqual(status,400);self.assertNotIn(UPSTREAM.encode(),body);self.assertEqual(len(self.calls),1)
    def test_oversized_malformed_and_wrong_identity_responses_fail(self):
        for reply in (b'x'*(RUNNER.MAX_RESPONSE+1),b'not json',response(8,result='0x42'),response(result='0x42',error={} )):
            with self.subTest(length=len(reply)):
                self.replies=[(200,reply)];self.assertEqual(self.relay().handle(request())[0],502)
    def test_boolean_response_ids_do_not_alias_integer_request_ids(self):
        for request_id,reply_id in ((1,True),(0,False)):
            with self.subTest(request_id=request_id):
                self.replies=[(200,response(reply_id,result='0x42'))]
                self.assertEqual(self.relay().handle(request(request_id=request_id))[0],502)
    def test_rpc_error_containing_upstream_credentials_is_suppressed(self):
        upstream='https://user:privatevalue@archive.invalid/path?key=secret-query'
        self.replies=[(200,response(error={'code':-1,'message':'rejected secret-query'}))]
        status,body=self.relay(upstream).handle(request());self.assertEqual(status,502);self.assertNotIn(b'secret-query',body)
    def test_empty_insecure_invalid_upstream_and_invalid_cadence_are_rejected(self):
        for upstream in (None,'','http://remote.invalid','https://','file:///tmp/archive','https://archive.invalid:bad'):
            with self.subTest(upstream=upstream),self.assertRaises(ValueError):self.relay(upstream)
        for interval in (0,1.0,True,float('nan')):
            with self.subTest(interval=interval),self.assertRaises(ValueError):RUNNER.Relay(UPSTREAM,interval=interval)

class ForkProcessTests(unittest.TestCase):
    def setUp(self):self.servers=[];self.commands=[];self.fail=False
    def server(self,relay):
        outer=self
        class FakeServer:
            url='http://127.0.0.1:12345'
            started=False;closed=False
            def start(self):self.started=True
            def close(self):self.closed=True
        result=FakeServer();outer.servers.append(result);return result
    def spawn(self,command,**kwargs):
        self.commands.append((command,kwargs))
        if '--version' in command:
            return subprocess.CompletedProcess(command,0,'forge Version: 1.4.4-v1.4.4\nCommit SHA: '+RUNNER.FORGE_COMMIT+'\n','')
        if self.fail:raise OSError('upstream secret must not enter runner logs')
        return subprocess.CompletedProcess(command,9)
    def test_exit_code_and_loopback_fork_environment_are_forwarded_then_closed(self):
        code=RUNNER.run_fork(UPSTREAM,forge='/reviewed/forge',run=self.spawn,server_factory=self.server)
        self.assertEqual(code,9);self.assertTrue(self.servers[0].started);self.assertTrue(self.servers[0].closed)
        command,options=self.commands[-1]
        self.assertEqual(command,['/reviewed/forge','test','--match-contract','UniswapV4ForkTest','--threads','1','--no-storage-caching','-vvv'])
        self.assertEqual(options['env']['ROBINHOOD_RPC_URL'],self.servers[0].url)
        self.assertEqual(options['env']['RUN_ROBINHOOD_FORK_TESTS'],'true')
    def test_subprocess_failure_always_closes_relay(self):
        self.fail=True
        with self.assertRaises(OSError):RUNNER.run_fork(UPSTREAM,run=self.spawn,server_factory=self.server)
        self.assertTrue(self.servers[0].closed)
    def test_unpinned_forge_never_starts_relay(self):
        run=lambda command,**kwargs:subprocess.CompletedProcess(command,0,'forge Version: 1.5.0\n','')
        with self.assertRaises(ValueError):RUNNER.run_fork(UPSTREAM,run=run,server_factory=self.server)
        self.assertFalse(self.servers)
    def test_main_preserves_forge_failure_exit_status(self):
        with patch.object(sys,'argv',['run-fork-checks.py','--upstream',UPSTREAM]),patch.object(RUNNER,'run_fork',return_value=9):
            self.assertEqual(RUNNER.main(),9)

if __name__=='__main__':unittest.main()
