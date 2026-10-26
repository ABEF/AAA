"""Current fork evidence must reject skipped, partial or legacy-green selections."""
import importlib.util
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('current_pool_fork_runner',ROOT/'scripts/run-current-pool-fork.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class CurrentPoolForkRunnerTest(unittest.TestCase):
    def results(self):
        return {runner.SUITE:{'test_results':{
            name+'()':{'status':'Success'} for name in runner.expected_tests()}}}

    def test_exact_complete_current_inventory_is_required(self):
        data=self.results()
        self.assertEqual(runner.verify_results(json.dumps(data)),len(runner.expected_tests()))
        key=next(iter(data[runner.SUITE]['test_results']))
        del data[runner.SUITE]['test_results'][key]
        with self.assertRaises(ValueError):runner.verify_results(json.dumps(data))

    def test_optout_skip_or_failed_setup_cannot_be_a_pass(self):
        for status in ('Skipped','Failure'):
            data=self.results(); first=next(iter(data[runner.SUITE]['test_results']))
            data[runner.SUITE]['test_results'][first]['status']=status
            with self.assertRaises(ValueError):runner.verify_results(json.dumps(data))
        with self.assertRaises(ValueError):runner.verify_results(json.dumps({runner.SUITE:{'test_results':{'setUp()':{'status':'Failure'}}}}))

    def test_old_or_extra_suite_is_not_current_qualification(self):
        data=self.results(); suite=data.pop(runner.SUITE)
        data['test/NativePoolFork.t.sol:NativePoolForkTest']=suite
        with self.assertRaises(ValueError):runner.verify_results(json.dumps(data))
        data=self.results();data['test/UniswapV4Fork.t.sol:UniswapV4ForkTest']=suite
        with self.assertRaises(ValueError):runner.verify_results(json.dumps(data))

    def test_empty_source_inventory_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'test').mkdir()
            (root/'test/CurrentNativePoolFork.t.sol').write_text('contract Example { /* function testFake() {} */ }')
            with self.assertRaises(ValueError):runner.expected_tests(root)

    def test_fork_relay_cannot_send_transactions_or_manage_wallets(self):
        observed=[]
        relay=runner.Relay('https://rpc.example.invalid',post=lambda body:observed.append(body))
        for method in ('eth_sendTransaction','eth_sendRawTransaction','personal_unlockAccount','anvil_setBalance','wallet_sendCalls'):
            status,raw=relay.handle(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':[]}).encode())
            self.assertEqual(status,403);self.assertIn('error',json.loads(raw))
        self.assertEqual(observed,[])

    def test_upstream_error_cannot_echo_path_credentials(self):
        secret='EXAMPLE_PATH_CREDENTIAL'
        upstream=json.dumps({'jsonrpc':'2.0','id':1,'error':{'code':-32000,
            'message':'provider rejected '+secret,'data':{'token':secret}}}).encode()
        relay=runner.Relay('https://rpc.example.invalid/v2/'+secret,post=lambda body:(200,upstream))
        status,raw=relay.handle(json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]}).encode())
        self.assertEqual(status,200);self.assertNotIn(secret.encode(),raw)
        self.assertEqual(json.loads(raw)['error'],{'code':-32000,'message':'Archive RPC rejected the read'})

    def test_strict_request_json_stops_before_archive_transport(self):
        invalid=[b'{"jsonrpc":"2.0","id":1,"method":"eth_chainId","method":"eth_call","params":[]}',
            b'{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[{"x":1,"x":2}]}',
            b'{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[NaN]}',
            b'{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[1e400]}']
        for body in invalid:
            calls=[];relay=runner.Relay('https://rpc.example.invalid',post=lambda data:calls.append(data))
            status,raw=relay.handle(body)
            self.assertEqual(status,400);self.assertEqual(calls,[])
            self.assertEqual(json.loads(raw)['error']['message'],'Malformed JSON-RPC request')

    def test_strict_archive_json_cannot_override_or_invent_values(self):
        invalid=[b'{"jsonrpc":"2.0","id":1,"result":"0x1","result":"0x1237"}',
            b'{"jsonrpc":"2.0","id":1,"result":{"value":1,"value":2}}',
            b'{"jsonrpc":"2.0","id":1,"result":Infinity}',
            b'{"jsonrpc":"2.0","id":1,"result":1e400}']
        body=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]}).encode()
        for response in invalid:
            relay=runner.Relay('https://rpc.example.invalid',post=lambda data:(200,response))
            status,raw=relay.handle(body);self.assertEqual(status,502)
            self.assertEqual(json.loads(raw)['error']['message'],'Archive RPC returned malformed JSON')

    def test_parser_limit_failures_are_sanitized_on_both_boundaries(self):
        body=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]}).encode()
        for exception in (ValueError,RecursionError):
            relay=runner.Relay('https://rpc.example.invalid',post=lambda data:(200,b'{}'))
            with patch.object(runner,'strict_json_loads',side_effect=exception('SECRET')):
                status,raw=relay.handle(body)
            self.assertEqual(status,400);self.assertNotIn(b'SECRET',raw)
            with patch.object(runner,'strict_json_loads',side_effect=[json.loads(body),exception('SECRET')]):
                status,raw=relay.handle(body)
            self.assertEqual(status,502);self.assertNotIn(b'SECRET',raw)

    def test_actual_redirect_is_not_followed_or_logged(self):
        requests=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                requests.append('post');self.rfile.read(int(self.headers.get('Content-Length','0')))
                self.send_response(302);self.send_header('Location','/leak');self.send_header('Content-Length','0');self.end_headers()
            def do_GET(self):
                requests.append('get');self.send_response(200);self.send_header('Content-Length','0');self.end_headers()
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            relay=runner.Relay('http://127.0.0.1:'+str(server.server_port)+'/v2/EXAMPLE_SECRET')
            body=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]}).encode()
            status,raw=relay.handle(body);self.assertEqual(status,502)
            self.assertEqual(requests,['post']);self.assertNotIn(b'EXAMPLE_SECRET',raw)
        finally:server.shutdown();server.server_close();thread.join(timeout=2)

    def test_compiler_environment_and_effective_config_are_pinned_before_rpc(self):
        original={'PATH':'runtime-bin','SystemRoot':'runtime-root','TMP':'runtime-tmp',
            'FOUNDRY_PROFILE':'audit','FOUNDRY_OPTIMIZER_RUNS':'999999','FOUNDRY_CODE_SIZE_LIMIT':'999999',
            'DAPP_REMAPPINGS':'evil=outside','foundry_evm_version':'paris',
            'POPL_TEST_PRIVATE_KEY':'EXAMPLE_SECRET','ROBINHOOD_RPC_URL':'EXAMPLE_ENDPOINT'}
        untouched=dict(original);environment=runner.controlled_environment(original)
        self.assertEqual(original,untouched)
        self.assertEqual(environment,{'PATH':'runtime-bin','SystemRoot':'runtime-root','TMP':'runtime-tmp','FOUNDRY_PROFILE':'default'})
        # Actual sanitized Forge output, with its executable path replaced by a
        # portable fixture. No Forge process or endpoint is started by this case.
        value=json.loads((ROOT/'reports/current-pool-fork-20261026/profile-effective-config.json').read_text())['configuration']
        value['solc']='/reviewed/solc';value['eth_rpc_url']='https://example.invalid/EXAMPLE_SECRET'
        reviewed=runner.reviewed_effective_config(value,'/reviewed/solc')
        self.assertEqual(reviewed['profile'],'default');self.assertNotIn('EXAMPLE_SECRET',json.dumps(reviewed))
        bad=[('src','../foreign'),('optimizer',False),('optimizer_runs',True),('optimizer_details',{'yul':0}),
            ('via_ir',False),('evm_version','paris'),('ffi',True),('code_size_limit',999999),
            ('libraries',['unreviewed=0x01']),('allow_paths',['../outside']),('solc','/foreign/solc'),
            ('remappings',value['remappings']+['@openzeppelin/contracts/=outside/'])]
        for key,changed in bad:
            config=copy.deepcopy(value);config[key]=changed
            with self.assertRaises(ValueError):runner.reviewed_effective_config(config,'/reviewed/solc')

if __name__=='__main__':unittest.main()
