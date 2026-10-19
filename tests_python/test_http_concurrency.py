"""Concurrent loopback requests, isolated workers and bounded hostile clients."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
import http.client
import io
import json
from pathlib import Path
import socket
import threading
import time
import unittest
from unittest.mock import patch

from frontend_api.http_runtime import ServiceBusy, BoundedHandler
from frontend_api.server import ReadServer, handler
from frontend_api.activation_server import handler as activation_handler
from frontend_api.worker import WorkerPool
from tests_python.test_frontend_api import configuration


def echo_child(output, config, activation_config, action, payload, transaction_config=None):
    Path(output).write_text(json.dumps({'ok': {'action': action, 'payload': payload}}))


class FakeWorker:
    chain = 31337
    def __init__(self, *args, **kwargs):
        self._unreaped = None
        self.gate = None
        self.entered = threading.Event()
        self.active = False
    def nft(self, identifier):
        if self.active:
            raise AssertionError('Supervisor reused concurrently')
        self.active = True
        try:
            self.entered.set()
            if self.gate is not None:
                if not self.gate.wait(3):
                    raise TimeoutError('Test gate was not released')
            return {'token_id': identifier}
        finally:
            self.active = False
    def prepare(self, payload):
        self.entered.set()
        return {'wallet': payload['wallet'], 'signed': False}


class WorkerPoolTests(unittest.TestCase):
    def make_pool(self, count):
        clients = []
        def create(*args, **kwargs):
            c = FakeWorker();clients.append(c);return c
        with patch('frontend_api.worker.WorkerClient', side_effect=create):
            return WorkerPool({}, workers=count), clients

    def test_bounded_parallel_leases_isolate_results_and_recover_after_overload(self):
        p, clients = self.make_pool(4)
        gate = threading.Event()
        for c in clients:c.gate = gate
        with ThreadPoolExecutor(4) as threads:
            futures = [threads.submit(p.nft, str(i)) for i in range(4)]
            try:
                for c in clients:self.assertTrue(c.entered.wait(1))
                with self.assertRaises(ServiceBusy):p.nft('overflow')
            finally:gate.set()
            self.assertEqual([f.result()['token_id'] for f in futures], ['0','1','2','3'])
        for i in range(20):self.assertEqual(p.nft(str(i)), {'token_id':str(i)})

    def test_one_bad_supervisor_is_quarantined_but_healthy_capacity_continues(self):
        p, clients = self.make_pool(2)
        def broken(_):
            clients[0]._unreaped = True
            raise RuntimeError('simulated cleanup error')
        clients[0].nft = broken
        with contextlib.redirect_stdout(io.StringIO()) as log:
            with self.assertRaises(RuntimeError):p.nft('1')
        self.assertIn('api_worker_quarantined', log.getvalue())
        self.assertNotIn('simulated cleanup error', log.getvalue())
        for _ in range(4):self.assertEqual(p.nft('2'), {'token_id':'2'})
        self.assertEqual(p._available.qsize(),1)

    def test_rejection_and_failure_release_healthy_leases(self):
        p, clients = self.make_pool(1)
        original = clients[0].nft
        clients[0].nft = lambda _: (_ for _ in ()).throw(ValueError())
        with self.assertRaises(ValueError):p.nft('1')
        clients[0].nft = original
        self.assertEqual(p.nft('2'), {'token_id':'2'})

    def test_pool_and_http_bounds_reject_invalid_configuration(self):
        for n in (True,0,9,1.5):
            with self.assertRaises(ValueError):WorkerPool({},workers=n)
        for n in (True,0,33,1.5):
            with self.assertRaises(ValueError):ReadServer(('127.0.0.1',0),handler(None),max_connections=n)

    def test_actual_parallel_spawn_has_separate_payloads_and_reaps_children(self):
        p = WorkerPool(configuration(), workers=2)
        with patch('frontend_api.worker._run', echo_child),contextlib.redirect_stdout(io.StringIO()),ThreadPoolExecutor(2) as threads:
            futures = [threads.submit(p.nft, str(i)) for i in (11,22)]
            self.assertEqual([f.result(timeout=10)['payload'] for f in futures], ['11','22'])
        self.assertEqual(p._available.qsize(),2)
        self.assertTrue(all(c._unreaped is None for c in list(p._available.queue)))


class HTTPConcurrencyTests(unittest.TestCase):
    def test_expired_ingress_cannot_start_work_even_when_timer_callback_is_late(self):
        request=BoundedHandler.__new__(BoundedHandler)
        request._expired=threading.Event()
        request._ingress=threading.Timer(1,lambda:None)
        request._ingress_end=time.monotonic()-1
        with self.assertRaises(TimeoutError):request.begin_work()
        request._ingress_end=time.monotonic()+10;request._expired.set()
        with self.assertRaises(TimeoutError):request.begin_work()

    def setUp(self):
        self.clients=[]
        def create(*args, **kwargs):
            c=FakeWorker();self.clients.append(c);return c
        with patch('frontend_api.worker.WorkerClient',side_effect=create):
            self.pool=WorkerPool({},workers=2)
        self.server=ReadServer(('127.0.0.1',0),handler(self.pool,self.pool),max_connections=4)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        self.thread.start()

    def tearDown(self):
        for c in self.clients:
            if c.gate:c.gate.set()
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)

    def get(self, identifier='1'):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=4)
        try:
            c.request('GET','/v1/nfts/'+identifier)
            r=c.getresponse();return r.status,dict(r.getheaders()),json.loads(r.read())
        finally:c.close()

    def raw(self, data):
        with socket.create_connection(('127.0.0.1',self.server.server_port),timeout=2) as c:
            c.sendall(data);r=http.client.HTTPResponse(c);r.begin()
            return r.status,dict(r.getheaders()),json.loads(r.read())

    def header(self):return f'Host: 127.0.0.1:{self.server.server_port}\r\n'

    def test_slow_user_does_not_block_independent_user(self):
        self.clients[0].gate=threading.Event()
        with ThreadPoolExecutor(1) as threads:
            first=threads.submit(self.get,'10')
            self.assertTrue(self.clients[0].entered.wait(1))
            try:
                self.assertEqual(self.get('20')[2],{'token_id':20})
                self.assertFalse(first.done())
            finally:self.clients[0].gate.set()
            self.assertEqual(first.result()[2],{'token_id':10})

    def test_pool_overload_returns_retry_after_without_starting_extra_work(self):
        gate=threading.Event()
        for c in self.clients:c.gate=gate
        with ThreadPoolExecutor(2) as threads:
            first=[threads.submit(self.get,str(i)) for i in (1,2)]
            try:
                for c in self.clients:self.assertTrue(c.entered.wait(1))
                status,headers,body=self.get('3')
                self.assertEqual(status,503);self.assertEqual(body,{'error':'service_busy'});self.assertEqual(headers['Retry-After'],'1')
            finally:gate.set()
            self.assertTrue(all(f.result()[0]==200 for f in first))
        self.assertEqual(self.get('4')[0],200)

    def test_burst_has_no_cross_user_response_mix_or_unbounded_queue(self):
        with ThreadPoolExecutor(12) as threads:
            results=list(threads.map(self.get,map(str,range(1,41))))
        successes=0
        for identifier,(status,headers,body) in enumerate(results,1):
            if status==200:
                successes+=1;self.assertEqual(body,{'token_id':identifier})
            else:self.assertEqual((status,body),(503,{'error':'service_busy'}))
        self.assertGreater(successes,0);self.assertEqual(self.get('99')[0],200)

    def test_duplicate_get_framing_never_dispatches(self):
        extras=[self.header(),'Content-Length: 0\r\nContent-Length: 0\r\n','Transfer-Encoding:\r\n','Expect: 100-continue\r\n']
        for extra in extras:
            data=('GET /v1/nfts/1 HTTP/1.1\r\n'+self.header()+extra+'\r\n').encode()
            self.assertEqual(self.raw(data)[0],400)
        self.assertFalse(any(c.entered.is_set() for c in self.clients))

    def test_oversized_header_line_or_total_is_bounded(self):
        for extra in ['X-Large: '+'a'*9000+'\r\n', ''.join(f'X-{i}: '+('a'*7000)+'\r\n' for i in range(5))]:
            status,_,body=self.raw(('GET /v1/nfts/1 HTTP/1.1\r\n'+self.header()+extra+'\r\n').encode())
            self.assertEqual((status,body),(431,{'error':'request_headers_too_large'}))
        self.assertEqual(self.get('1')[0],200)

    def test_absolute_ingress_timeout_even_when_body_keeps_arriving(self):
        with patch('frontend_api.http_runtime.INGRESS_SECONDS',.2):
            with socket.create_connection(('127.0.0.1',self.server.server_port),timeout=1) as c:
                c.sendall(('POST /v1/transactions/prepare HTTP/1.1\r\n'+self.header()+'Content-Type: application/json\r\nContent-Length: 100\r\n\r\n').encode())
                started=time.monotonic()
                for _ in range(12):
                    try:c.sendall(b' ')
                    except OSError:break
                    time.sleep(.04)
                self.assertLess(time.monotonic()-started,.8)
                try:self.assertEqual(c.recv(100),b'')
                except (ConnectionResetError,ConnectionAbortedError):pass
        self.assertFalse(any(c.entered.is_set() for c in self.clients))
        self.assertEqual(self.get('1')[0],200)

    def test_slow_headers_use_bounded_connection_capacity_then_release(self):
        held=[]
        with patch('frontend_api.http_runtime.INGRESS_SECONDS',.25):
            try:
                for _ in range(4):
                    c=socket.create_connection(('127.0.0.1',self.server.server_port),timeout=2);held.append(c);c.sendall(b'GET /v1/nfts/1 HTTP/1.1\r\nX-Hold: ')
                time.sleep(.05)
                status,headers,body=self.get('1')
                self.assertEqual((status,body),(503,{'error':'service_busy'}));self.assertEqual(headers['Retry-After'],'1')
                for c in held:
                    try:self.assertEqual(c.recv(100),b'')
                    except (ConnectionResetError,ConnectionAbortedError):pass
            finally:
                for c in held:c.close()
        self.assertEqual(self.get('2')[0],200)

    def test_unexpected_read_error_is_sanitized_and_next_user_still_succeeds(self):
        self.clients[0].nft=lambda _: (_ for _ in ()).throw(OSError('SECRET provider credentials'))
        with contextlib.redirect_stdout(io.StringIO()) as log:
            status,_,body=self.get('1')
        self.assertEqual((status,body),(503,{'error':'confirmed_projection_unavailable'}))
        self.assertNotIn('SECRET',log.getvalue());self.assertEqual(self.get('2')[0],200)

    def test_disconnected_client_does_not_restart_work_or_leak_traceback(self):
        self.clients[0].gate=threading.Event()
        c=socket.create_connection(('127.0.0.1',self.server.server_port),timeout=2)
        c.sendall(('GET /v1/nfts/1 HTTP/1.1\r\n'+self.header()+'\r\n').encode())
        self.assertTrue(self.clients[0].entered.wait(1))
        c.shutdown(socket.SHUT_RDWR);c.close();self.clients[0].gate.set()
        self.assertEqual(self.get('2')[0],200)

    def test_both_preparation_routes_report_busy_without_echoing_body(self):
        class Busy:
            def prepare(self,_):raise ServiceBusy()
        for route,cls in [('/v1/transactions/prepare',handler(self.pool,Busy())),('/v1/activation/prepare',activation_handler(self.pool,Busy()))]:
            self.server.RequestHandlerClass=cls
            body=b'{"wallet":"SECRET"}'
            data=(f'POST {route} HTTP/1.1\r\n'+self.header()+f'Content-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n').encode()+body
            status,headers,result=self.raw(data)
            self.assertEqual((status,result),(503,{'error':'service_busy'}));self.assertEqual(headers['Retry-After'],'1')


if __name__=='__main__':unittest.main()
