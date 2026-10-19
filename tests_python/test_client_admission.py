"""Fair admission, proxy identity and actual loopback request recovery."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
from email.message import Message
import http.client
import io
import json
import socket
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from frontend_api.admission import ClientAdmission, AdmissionRejected, client_key, public_origin
from frontend_api.server import ReadServer, handler
from frontend_api.activation_server import handler as activation_handler

ORIGIN = 'https://popl.example.test'


class AdmissionTests(unittest.TestCase):
    def test_rates_are_separate_and_retry_after_tracks_refill(self):
        now = [0.]
        a = ClientAdmission(clock=lambda: now[0])
        for _ in range(2): a.acquire('one', preparation=True)()
        with self.assertRaises(AdmissionRejected) as caught: a.acquire('one', preparation=True)
        self.assertEqual((caught.exception.status, caught.exception.retry_after), (429, 10))
        for _ in range(12): a.acquire('one')()
        with self.assertRaises(AdmissionRejected): a.acquire('one')
        now[0] = 1
        a.acquire('one')()
        with self.assertRaises(AdmissionRejected) as caught: a.acquire('one', preparation=True)
        self.assertEqual(caught.exception.retry_after, 9)
        now[0] = 10
        a.acquire('one', preparation=True)()

    def test_concurrent_acquisition_is_atomic_and_release_idempotent(self):
        a = ClientAdmission()
        def acquire(_):
            try: return a.acquire('one')
            except AdmissionRejected: return None
        with ThreadPoolExecutor(16) as pool:
            leases = [v for v in pool.map(acquire, range(50)) if v]
        self.assertEqual(len(leases), 2)
        other = a.acquire('other'); other()
        for lease in leases: lease(); lease()
        self.assertEqual(a._clients['one'].active, 0)
        a.acquire('one')()

    def test_full_table_never_evicts_depleted_or_active_clients(self):
        now = [0.]
        a = ClientAdmission(capacity=2, clock=lambda: now[0])
        hold = a.acquire('active')
        for _ in range(2): a.acquire('depleted', preparation=True)()
        with self.assertRaises(AdmissionRejected) as caught: a.acquire('new')
        self.assertEqual(caught.exception.code, 'admission_capacity_unavailable')
        now[0] = 19.9
        with self.assertRaises(AdmissionRejected): a.acquire('new')
        now[0] = 20
        a.acquire('new')()
        self.assertIn('active', a._clients)
        self.assertNotIn('depleted', a._clients)
        self.assertEqual(len(a._clients), 2)
        hold()

    def test_bounds_and_origins_reject_unsafe_configuration(self):
        for value in (True, 0, 5, 1.5):
            with self.assertRaises(ValueError): ClientAdmission(max_active=value)
        for value in (True, 0, 16385, 1.5):
            with self.assertRaises(ValueError): ClientAdmission(capacity=value)
        for value in ('http://site.test', 'https://site.test/', 'https://*.test',
                      'https://user@site.test', 'https://site.test:0', 'https://site.test:65536',
                      'https://site..test', 'https://-site.test', 'https://SITE.test',
                      'https://site.test\r\nX: y', 'https://site.test/path'):
            with self.subTest(value=value), self.assertRaises(ValueError): public_origin(value)
        self.assertEqual(public_origin(ORIGIN), ORIGIN)
        self.assertEqual(public_origin(ORIGIN + ':8443'), ORIGIN + ':8443')
        self.assertIsNone(public_origin(None))

    def request(self, headers=(), method='GET', peer='127.0.0.1'):
        message = Message()
        for key, value in headers: message[key] = value
        return SimpleNamespace(headers=message, command=method, client_address=(peer, 12345))

    def test_untrusted_forwarding_cannot_select_capacity_key(self):
        self.assertEqual(client_key(self.request([('X-Forwarded-For','1.2.3.4'), ('Forwarded','for=5.6.7.8')]),None),'127.0.0.1')
        with self.assertRaises(AdmissionRejected):
            client_key(self.request([('X-PoPL-Client-IP','1.2.3.4')]),None)
        for identity in ('2001:db8:0:0::1', '2001:db8::1'):
            self.assertEqual(client_key(self.request([('X-PoPL-Client-IP', identity)]), ORIGIN), '2001:db8::1')
        self.assertEqual(client_key(self.request([('X-PoPL-Client-IP', '::ffff:192.0.2.1')]), ORIGIN), '192.0.2.1')

    def test_missing_duplicate_malformed_proxy_headers_and_remote_peer_fail_closed(self):
        cases = [[], [('X-PoPL-Client-IP','1.2.3.4')]*2]
        cases += [[('X-PoPL-Client-IP', v)] for v in ('1.2.3.4,5.6.7.8', '1.2.3.4:1', 'fe80::1%eth0', ' 1.2.3.4', 'unknown')]
        for headers in cases:
            with self.subTest(headers=headers), self.assertRaises(AdmissionRejected): client_key(self.request(headers), ORIGIN)
        with self.assertRaises(AdmissionRejected):
            client_key(self.request([('X-PoPL-Client-IP','1.2.3.4')], peer='192.0.2.1'), ORIGIN)

    def test_proxy_preparation_requires_exact_origin_and_rejects_cross_site(self):
        base = [('X-PoPL-Client-IP','192.0.2.1')]
        for extra in ([], [('Origin','null')], [('Origin','https://evil.test')], [('Origin',ORIGIN)]*2,
                      [('Origin',ORIGIN),('Sec-Fetch-Site','cross-site')]):
            with self.subTest(extra=extra), self.assertRaises(AdmissionRejected):
                client_key(self.request(base+extra, 'POST'), ORIGIN)
        self.assertEqual(client_key(self.request(base+[('Origin',ORIGIN)], 'POST'), ORIGIN), '192.0.2.1')


class HTTPAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.entered = threading.Event()
        self.gate = threading.Event()
        self.calls = []
        owner = self
        class Projection:
            def nft(self, token):
                owner.calls.append(token)
                if token == 1:
                    owner.entered.set()
                    if not owner.gate.wait(5): raise TimeoutError()
                if token == 13: raise RuntimeError('SECRET provider credentials')
                return {'token_id':token}
            def prepare(self, payload):
                owner.calls.append(payload)
                return {'unsigned':True}
        self.projection = Projection()
        self.admission = ClientAdmission(max_active=1)
        self.server = ReadServer(('127.0.0.1',0), handler(self.projection,self.projection),
                                 admission=self.admission, proxy_origin=ORIGIN)
        self.thread = threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        self.thread.start()
        self.log = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.log); self.capture.__enter__()

    def tearDown(self):
        self.gate.set()
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.capture.__exit__(None,None,None)

    def request(self, path='/v1/nfts/2', client='192.0.2.1', method='GET', extra=None):
        connection = http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        headers = {'X-PoPL-Client-IP':client}
        body = None
        if method == 'POST':
            body = '{}'; headers.update({'Content-Type':'application/json','Origin':ORIGIN})
        headers.update(extra or {})
        try:
            connection.request(method,path,body,headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally: connection.close()

    def test_busy_client_cannot_exhaust_another_clients_work_capacity(self):
        with ThreadPoolExecutor(1) as pool:
            pending = pool.submit(self.request,'/v1/nfts/1')
            self.assertTrue(self.entered.wait(1))
            try:
                status, headers, body = self.request(extra={'X-Forwarded-For':'192.0.2.99'})
                self.assertEqual((status,body),(429,{'error':'client_busy'}))
                self.assertEqual(headers['Retry-After'],'1')
                self.assertEqual(self.request(client='192.0.2.2')[0],200)
                self.assertEqual(self.calls,[1,2])
            finally: self.gate.set()
            self.assertEqual(pending.result()[0],200)
        self.assertEqual(self.request()[0],200)
        self.assertNotIn('192.0.2.',self.log.getvalue())

    def test_both_prepare_endpoints_limit_retries_without_consuming_read_budget(self):
        for route, factory in (('/v1/transactions/prepare',handler),('/v1/activation/prepare',activation_handler)):
            self.server.RequestHandlerClass = factory(self.projection,self.projection)
            self.server.admission = ClientAdmission()
            for _ in range(2): self.assertEqual(self.request(route,method='POST')[0],200)
            status, headers, body = self.request(route,method='POST')
            self.assertEqual((status,body),(429,{'error':'client_rate_limited'}))
            self.assertEqual(headers['Retry-After'],'10')
            self.assertEqual(self.request()[0],200)
        self.assertEqual(len([c for c in self.calls if isinstance(c,dict)]),4)

    def test_invalid_origin_no_work_and_failed_projection_releases_lease(self):
        self.assertEqual(self.request('/v1/transactions/prepare',method='POST',extra={'Origin':'https://evil.test'})[0],403)
        self.assertEqual(self.calls,[])
        self.assertEqual(self.request('/v1/nfts/13')[0],503)
        self.assertEqual(self.request()[0],200)
        self.assertNotIn('SECRET',self.log.getvalue())

    def test_read_burst_and_table_overflow_have_no_extra_upstream_calls(self):
        for _ in range(12): self.assertEqual(self.request()[0],200)
        self.assertEqual(self.request()[0],429)
        self.assertEqual(len(self.calls),12)
        self.server.admission = ClientAdmission(capacity=1)
        self.assertEqual(self.request()[0],200)
        status, headers, body = self.request(client='192.0.2.2')
        self.assertEqual((status,body),(503,{'error':'admission_capacity_unavailable'}))
        self.assertEqual(headers['Retry-After'],'1')
        self.assertEqual(len(self.calls),13)

    def test_disconnect_keeps_lease_until_started_work_finishes(self):
        connection=socket.create_connection(('127.0.0.1',self.server.server_port),timeout=2)
        connection.sendall((f'GET /v1/nfts/1 HTTP/1.0\r\nHost: 127.0.0.1:{self.server.server_port}\r\n'
                            'X-PoPL-Client-IP: 192.0.2.1\r\n\r\n').encode())
        self.assertTrue(self.entered.wait(1))
        connection.shutdown(socket.SHUT_RDWR);connection.close()
        self.assertEqual(self.request()[0],429)
        self.assertEqual(self.request(client='192.0.2.2')[0],200)
        self.gate.set()
        deadline=time.monotonic()+2
        while self.admission._clients['192.0.2.1'].active and time.monotonic()<deadline:time.sleep(.01)
        self.assertEqual(self.request()[0],200)
        self.assertEqual(self.calls.count(1),1)


class AdmissionCLITests(unittest.TestCase):
    def test_both_entrypoints_enable_admission_and_explicit_proxy_mode(self):
        from frontend_api import server, activation_server
        for module, extra in ((server,[]),(activation_server,['--activation-config','activation.json'])):
            context=MagicMock()
            context.__enter__.return_value.serve_forever.side_effect=KeyboardInterrupt
            pool=SimpleNamespace(chain=31337)
            argv=['service','--config','read.json','--proxy-origin',ORIGIN,'--per-client-active','1']+extra
            with patch('sys.argv',argv),patch.object(module.Path,'read_text',return_value='{}'), \
                    patch('frontend_api.worker.WorkerPool',return_value=pool), \
                    patch.object(module,'ReadServer',return_value=context) as constructor, \
                    contextlib.redirect_stdout(io.StringIO()) as log:
                module.main()
            self.assertEqual(constructor.call_args.args[0],('127.0.0.1',8787 if module is server else 8788))
            self.assertEqual(constructor.call_args.kwargs['proxy_origin'],ORIGIN)
            self.assertEqual(constructor.call_args.kwargs['admission'].max_active,1)
            self.assertTrue(json.loads(log.getvalue())['proxy_identity'])

    def test_invalid_proxy_origin_is_rejected_before_constructing_worker(self):
        from frontend_api import server
        with patch('sys.argv',['service','--config','read.json','--proxy-origin','https://*.example.test']), \
                patch('frontend_api.worker.WorkerPool') as constructor, \
                contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            server.main()
        constructor.assert_not_called()


if __name__ == '__main__': unittest.main()
