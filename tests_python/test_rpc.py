import io,json,threading,unittest,urllib.error
from http.server import BaseHTTPRequestHandler,HTTPServer
from unittest.mock import patch
from zzz_ops.rpc import Rpc,RpcError

class RpcTests(unittest.TestCase):
    def test_reject_insecure_remote(self):
        for url in ['http://example.com','file:///tmp/rpc','https://']:
            with self.assertRaises(ValueError):Rpc([url],1)
    def test_accept_loopback(self):
        self.assertEqual(Rpc(['http://127.0.0.1:8545'],1).chain_id,1)
    def test_reject_empty(self):
        with self.assertRaises(ValueError):Rpc([],1)
    def test_reject_broadcast(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        for method in ['eth_sendRawTransaction','eth_sendTransaction','personal_sendTransaction']:
            with self.assertRaises(RpcError):rpc.call(method,[])
    def test_unknown_and_bundler_methods_rejected(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        for method in ['eth_sendUserOperation','personal_unlockAccount','custom_write']:
            with self.assertRaises(RpcError):rpc.call(method,[])
    @patch('zzz_ops.rpc.time.sleep')
    def test_wrong_chain_never_executes_read(self,_):
        rpc=Rpc(['https://rpc.invalid'],1,retries=2)
        with patch.object(rpc,'_post',return_value='0x2') as post:
            with self.assertRaises(RpcError):rpc.call('eth_blockNumber')
            self.assertTrue(all(x.args[1]=='eth_chainId' for x in post.call_args_list))
    @patch('zzz_ops.rpc.time.sleep')
    def test_endpoint_failover(self,_):
        rpc=Rpc(['https://a.invalid','https://b.invalid'],1)
        def respond(url,method,params):
            if url.endswith('a.invalid'):raise OSError('unavailable')
            return '0x1' if method=='eth_chainId' else '0xabc'
        with patch.object(rpc,'_post',side_effect=respond):
            self.assertEqual(rpc.call('eth_blockNumber'),'0xabc')
            self.assertEqual(rpc.active_url,'https://b.invalid')
    def test_chain_rechecked_every_call(self):
        rpc=Rpc(['https://a.invalid'],1)
        with patch.object(rpc,'_post',side_effect=['0x1','0x8','0x1','0x9']) as post:
            rpc.call('eth_blockNumber');rpc.call('eth_blockNumber')
            self.assertEqual(sum(x.args[1]=='eth_chainId' for x in post.call_args_list),2)
    def test_request_and_response_identity(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        def open_response(req,timeout):
            body=json.loads(req.data)
            self.assertEqual(body['method'],'eth_blockNumber')
            return io.BytesIO(json.dumps({'id':body['id'],'jsonrpc':'2.0','result':'0x9'}).encode())
        with patch.object(rpc._opener,'open',side_effect=open_response):
            self.assertEqual(rpc._post(rpc.active_url,'eth_blockNumber',[]),'0x9')
    def test_response_id_mismatch(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        with patch.object(rpc._opener,'open',return_value=io.BytesIO(b'{"id":999,"jsonrpc":"2.0","result":1}')):
            with self.assertRaises(RpcError):rpc._post(rpc.active_url,'test',[])
    def test_error_message_sanitized(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        response=b'{"id":1,"jsonrpc":"2.0","error":{"code":-1,"message":"SECRET"}}'
        with patch.object(rpc._opener,'open',return_value=io.BytesIO(response)):
            with self.assertRaises(RpcError) as ctx:rpc._post(rpc.active_url,'test',[])
            self.assertNotIn('SECRET',str(ctx.exception))
    def test_response_size_limit(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        with patch.object(rpc._opener,'open',return_value=io.BytesIO(b'x'*(8*1024*1024+1))):
            with self.assertRaises(RpcError):rpc._post(rpc.active_url,'test',[])
    def test_bounds_reject_invalid_transport_configuration(self):
        for kwargs in ({'timeout':0},{'timeout':61},{'timeout':float('nan')},{'retries':True},{'retries':0},{'retries':11}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):Rpc(['https://rpc.invalid'],1,**kwargs)
        with self.assertRaises(ValueError):Rpc(['https://rpc.invalid']*9,1)
    @patch('zzz_ops.rpc.time.sleep')
    def test_incomplete_http_body_falls_back(self,_):
        import http.client
        rpc=Rpc(['https://a.invalid','https://b.invalid'],1)
        def respond(url,method,params):
            if url.endswith('a.invalid'):raise http.client.IncompleteRead(b'broken')
            return '0x1' if method=='eth_chainId' else '0xabc'
        with patch.object(rpc,'_post',side_effect=respond):self.assertEqual(rpc.call('eth_blockNumber'),'0xabc')
    def test_boolean_response_id_is_not_an_integer_id(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        with patch.object(rpc._opener,'open',return_value=io.BytesIO(b'{"id":true,"jsonrpc":"2.0","result":1}')):
            with self.assertRaises(RpcError):rpc._post(rpc.active_url,'test',[])
    def test_noninteger_error_code_is_not_reflected(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        with patch.object(rpc._opener,'open',return_value=io.BytesIO(b'{"id":1,"jsonrpc":"2.0","error":{"code":"SECRET"}}')):
            with self.assertRaises(RpcError) as ctx:rpc._post(rpc.active_url,'test',[])
            self.assertNotIn('SECRET',str(ctx.exception))
    def test_http_error_responses_close_before_preserved_error_and_configured_failover(self):
        for status in (429,500):
            with self.subTest(status=status):
                rpc=Rpc(['https://a.invalid','https://b.invalid'],1,retries=1)
                body=io.BytesIO(b'provider error')
                failure=urllib.error.HTTPError(rpc.active_url,status,'SECRET',{},body)
                with patch.object(rpc._opener,'open',side_effect=failure):
                    with self.assertRaises(urllib.error.HTTPError) as observed:
                        rpc._read_http(rpc.active_url,b'{}')
                self.assertIs(observed.exception,failure)
                self.assertTrue(body.closed,'Refused provider response must not retain its connection')
                attempts=[];retry_body=io.BytesIO(b'provider error')
                def reply(request,timeout):
                    attempts.append(request.full_url)
                    if request.full_url=='https://a.invalid':
                        raise urllib.error.HTTPError(request.full_url,status,'SECRET',{},retry_body)
                    message=json.loads(request.data)
                    return io.BytesIO(json.dumps({'jsonrpc':'2.0','id':message['id'],
                        'result':'0x1' if message['method']=='eth_chainId' else '0xabc'}).encode())
                with patch.object(rpc._opener,'open',side_effect=reply),patch('zzz_ops.rpc.time.sleep'):
                    self.assertEqual(rpc.call('eth_blockNumber'),'0xabc')
                self.assertTrue(retry_body.closed)
                self.assertEqual(attempts,['https://a.invalid','https://b.invalid','https://b.invalid'])

class RedirectTransportTests(unittest.TestCase):
    def server(self,respond):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):respond(self)
            def do_POST(self):respond(self)
        server=HTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        thread.start()
        def close():
            server.shutdown();server.server_close();thread.join(2)
            self.assertFalse(thread.is_alive())
        self.addCleanup(close)
        return 'http://127.0.0.1:'+str(server.server_port)
    @staticmethod
    def reply(handler,body):
        handler.send_response(200);handler.send_header('Content-Length',str(len(body)))
        handler.end_headers();handler.wfile.write(body)
    def test_redirect_destinations_never_receive_rpc_requests(self):
        trapped=[]
        def trap(handler):
            trapped.append(handler.command)
            self.reply(handler,b'{"jsonrpc":"2.0","id":1,"result":"0x1"}')
        target=self.server(trap)
        def redirect(handler):
            handler.send_response(int(handler.path[1:]));handler.send_header('Location',target+'/trap')
            handler.send_header('Content-Length','0');handler.end_headers()
        source=self.server(redirect)
        for status in (300,301,302,303,304,305,306,307,308,399):
            with self.subTest(status=status):
                before=len(trapped);rpc=Rpc([source+'/'+str(status)],1,retries=1)
                error=None
                try:rpc._read_http(rpc.active_url,b'{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}')
                except (RpcError,urllib.error.HTTPError) as exc:error=exc
                self.assertEqual(len(trapped),before,'A redirect must not reach the unreviewed target')
                self.assertIsNotNone(error)
    @patch('zzz_ops.rpc.time.sleep')
    def test_refused_redirect_fails_over_only_to_a_configured_chain_checked_endpoint(self,_):
        trapped=[];methods=[]
        def trap(handler):
            trapped.append(handler.command);self.reply(handler,b'forbidden')
        target=self.server(trap)
        def redirect(handler):
            handler.send_response(302);handler.send_header('Location',target+'/SECRET')
            handler.send_header('Content-Length','0');handler.end_headers()
        source=self.server(redirect)
        def valid(handler):
            request=json.loads(handler.rfile.read(int(handler.headers['Content-Length'])))
            methods.append(request['method'])
            self.reply(handler,json.dumps({'jsonrpc':'2.0','id':request['id'],
                'result':'0x1' if request['method']=='eth_chainId' else '0xabc'}).encode())
        approved=self.server(valid);rpc=Rpc([source,approved],1,retries=1)
        self.assertEqual(rpc.call('eth_blockNumber'),'0xabc')
        self.assertEqual(methods,['eth_chainId','eth_blockNumber']);self.assertEqual(trapped,[])
        self.assertEqual(rpc.active_url,approved)
    def test_opener_is_private_and_does_not_change_global_urlopen(self):
        import urllib.request
        original=urllib.request._opener
        first=Rpc(['https://a.invalid'],1);second=Rpc(['https://b.invalid'],1)
        self.assertIsNot(first._opener,second._opener)
        self.assertIs(urllib.request._opener,original)
