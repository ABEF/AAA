import http.client
import json
import threading
import unittest

from frontend_api.activation import ActivationInputError, ActivationTransactions
from frontend_api.activation_server import handler
from frontend_api.server import ReadServer
from frontend_api.service import Projection, UnknownNFT
from tests_python.test_frontend_activation import ActivationRPC
from tests_python.test_frontend_api import configuration


class ActivationHTTPTests(unittest.TestCase):
    def setUp(self):
        self.rpc=ActivationRPC();p=Projection(configuration(),self.rpc,clock=lambda:1000)
        self.preparer=ActivationTransactions(p,self.rpc.config)
        self.server=ReadServer(('127.0.0.1',0),handler(p,self.preparer))
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2)

    def request(self,body=None,headers=None,path='/v1/activation/prepare',method='POST'):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
        raw=json.dumps(self.rpc.request) if body is None else body
        c.request(method,path,raw,headers or {'Content-Type':'application/json'})
        response=c.getresponse();result=response.status,json.loads(response.read()),dict(response.getheaders());c.close()
        return result

    def test_exact_unsigned_transaction_and_no_store(self):
        status,body,headers=self.request()
        self.assertEqual(status,200);self.assertTrue(body['activation_ready']);self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertNotIn('Access-Control-Allow-Origin',headers)

    def test_invalid_json_duplicate_keys_nested_objects_and_nonfinite(self):
        for body in ('{}{}','[]','{"wallet":"a","wallet":"b"}','{"x":NaN}','{"x":{}}'):
            with self.subTest(body=body):self.assertEqual(self.request(body)[0],400)

    def test_host_framing_media_and_size(self):
        for headers,status in [({'Host':'evil.example','Content-Type':'application/json'},400),
                               ({'Transfer-Encoding':'chunked','Content-Type':'application/json'},400),
                               ({'Expect':'100-continue','Content-Type':'application/json'},400),
                               ({'Content-Type':'text/plain'},415),
                               ({'Content-Type':'application/json','Content-Length':'20000'},413)]:
            with self.subTest(headers=headers):self.assertEqual(self.request('{}',headers)[0],status)

    def test_no_other_post_and_no_write_methods(self):
        self.assertEqual(self.request(path='/v1/transactions/prepare')[0],404)
        self.assertEqual(self.request(method='PUT')[0],405)

    def test_failure_messages_are_sanitized(self):
        for error,status,code in [(ActivationInputError('private request'),400,'invalid_activation_request'),
                                   (UnknownNFT('private NFT'),404,'nft_not_minted'),
                                   (RuntimeError('secret endpoint credentials'),503,'activation_preparation_unavailable')]:
            def fail(_):raise error
            self.preparer.prepare=fail
            actual,body,_=self.request()
            self.assertEqual(actual,status);self.assertEqual(body,{'error':code})

    def test_duplicate_host_and_length_rejected(self):
        for header,value in [('Host','localhost'),('Content-Length','2')]:
            c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
            c.putrequest('POST','/v1/activation/prepare')
            c.putheader('Content-Type','application/json');c.putheader('Content-Length','2');c.putheader(header,value)
            c.endheaders(b'{}');r=c.getresponse();self.assertEqual(r.status,400);r.read();c.close()


if __name__=='__main__':unittest.main()
