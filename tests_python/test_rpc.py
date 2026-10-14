import io,json,unittest
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
        with patch('urllib.request.urlopen',side_effect=open_response):
            self.assertEqual(rpc._post(rpc.active_url,'eth_blockNumber',[]),'0x9')
    def test_response_id_mismatch(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"id":999,"jsonrpc":"2.0","result":1}')):
            with self.assertRaises(RpcError):rpc._post(rpc.active_url,'test',[])
    def test_error_message_sanitized(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        response=b'{"id":1,"jsonrpc":"2.0","error":{"code":-1,"message":"SECRET"}}'
        with patch('urllib.request.urlopen',return_value=io.BytesIO(response)):
            with self.assertRaises(RpcError) as ctx:rpc._post(rpc.active_url,'test',[])
            self.assertNotIn('SECRET',str(ctx.exception))
    def test_response_size_limit(self):
        rpc=Rpc(['https://rpc.invalid'],1)
        with patch('urllib.request.urlopen',return_value=io.BytesIO(b'x'*(8*1024*1024+1))):
            with self.assertRaises(RpcError):rpc._post(rpc.active_url,'test',[])
