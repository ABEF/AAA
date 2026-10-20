"""Bounded connection reuse only during one serialized local state read."""
import io
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock, patch
from tests_python.test_local_stack import lab

class LocalConnectionTests(unittest.TestCase):
    def test_actual_http_connection_reused_but_chain_checked_each_call(self):
        connections=[];methods=[]
        class Handler(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def setup(self):
                super().setup();connections.append(self.client_address)
            def log_message(self,*args):pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                methods.append(body['method'])
                data=json.dumps({'jsonrpc':'2.0','id':body['id'],
                                 'result':'0x7a69' if body['method']=='eth_chainId' else '0x1'}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(data)))
                self.end_headers();self.wfile.write(data)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        rpc=lab.LocalReadRPC([f'http://127.0.0.1:{server.server_port}'],31337,retries=1)
        rpc.aggregation=True;rpc.memo={}
        try:
            rpc.call('eth_blockNumber');rpc.call('eth_blockNumber')
            self.assertEqual(len(connections),1)
            self.assertEqual(methods,['eth_chainId','eth_blockNumber']*2)
            rpc.close_aggregate();rpc.call('eth_blockNumber')
            self.assertEqual(len(connections),2)
        finally:
            rpc.close_aggregate();server.shutdown();server.server_close();thread.join()
    def rpc(self):
        rpc=lab.LocalReadRPC(['http://127.0.0.1:1234'],31337,retries=1)
        rpc.aggregation=True;rpc.memo={}
        return rpc
    def test_outside_aggregate_retains_default_transport(self):
        rpc=self.rpc();rpc.aggregation=False
        with patch.object(lab.Rpc,'_read_http',return_value=b'ok') as original:
            self.assertEqual(rpc._read_http(rpc.active_url,b'{}'),b'ok')
            original.assert_called_once()
    def test_reused_socket_receives_current_request_budget(self):
        rpc=self.rpc();connection=Mock();response=Mock(status=200);response.read.return_value=b'{}'
        connection.getresponse.return_value=response
        with patch.object(lab.http.client,'HTTPConnection',return_value=connection),patch.object(lab,'remaining_timeout',side_effect=[2.0,.25]):
            rpc._read_http(rpc.active_url,b'{}');rpc._read_http(rpc.active_url,b'{}')
        self.assertEqual(connection.timeout,.25)
        connection.sock.settimeout.assert_called_with(.25)
        response.read.assert_called_with(8*1024*1024+1)
        rpc.close_aggregate();connection.close.assert_called_once()
    def test_http_error_closes_connection_and_never_follows_redirect(self):
        rpc=self.rpc();connection=Mock();connection.getresponse.return_value=Mock(status=302)
        with patch.object(lab.http.client,'HTTPConnection',return_value=connection):
            with self.assertRaises(lab.RpcError):rpc._read_http(rpc.active_url,b'{}')
        connection.close.assert_called_once();self.assertIsNone(rpc._aggregate_http)
    def test_oversized_response_closes_connection(self):
        rpc=self.rpc();connection=Mock();response=Mock(status=200);response.read.return_value=b'x'*(8*1024*1024+1)
        connection.getresponse.return_value=response
        with patch.object(lab.http.client,'HTTPConnection',return_value=connection):
            with self.assertRaises(lab.RpcError):rpc._read_http(rpc.active_url,b'{}')
        connection.close.assert_called_once()
    def test_transport_failure_is_closed_before_existing_bounded_retry(self):
        rpc=self.rpc();connection=Mock();connection.request.side_effect=OSError('closed socket')
        with patch.object(lab.http.client,'HTTPConnection',return_value=connection):
            with self.assertRaises(OSError):rpc._read_http(rpc.active_url,b'{}')
        connection.close.assert_called_once();self.assertIsNone(rpc._aggregate_http)
    def test_only_literal_loopback_without_credentials_can_reuse(self):
        rpc=self.rpc()
        for url in ['https://rpc.example','http://localhost:1234','http://name:secret@127.0.0.1:1234']:
            with self.subTest(url=url),self.assertRaises(lab.RpcError):
                rpc._read_http(url,b'{}')
    def test_rpc_response_identity_and_write_allowlist_still_apply(self):
        rpc=self.rpc()
        with patch.object(rpc,'_read_http',return_value=b'{"id":999,"jsonrpc":"2.0","result":"0x7a69"}'):
            with self.assertRaises(lab.RpcError):rpc.call('eth_blockNumber')
        with patch.object(rpc,'_read_http') as transport:
            with self.assertRaises(lab.RpcError):rpc.call('eth_sendTransaction')
            transport.assert_not_called()
