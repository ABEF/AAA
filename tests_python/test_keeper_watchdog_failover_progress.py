"""Completed HTTP attempts must count as main-thread watchdog progress.

The real Rpc.call/_post/_read_http decoder and retry path run over bounded
synthetic HTTP responses. No network, service, signer or existing journal runs.
"""
import contextlib
import json
import os
import threading
import unittest
from unittest.mock import Mock, patch

from keeper import monitor
from keeper import watchdog as W
from zzz_ops import rpc as M
from zzz_ops.work_budget import Budget, request_scope
from zzz_ops.errors import WorkLimit


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class CompletedResponse:
    def __init__(self, case, request, delay):
        self.case = case
        self.request = request
        self.delay = delay
        self.sent = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read1(self, maximum):
        if self.sent:
            return b''
        self.sent = True
        # No heartbeat may come from inside a pending/blocked transport read.
        notifications = len(self.case.notifications)
        self.case.clock.now += self.delay
        self.case.assertEqual(notifications, len(self.case.notifications))
        self.request['completed_at'] = self.case.clock.now
        value = self.request['request']
        body = {'jsonrpc':'2.0', 'id':value['id']}
        if value['method'] == 'eth_chainId':
            body['result'] = '0x1237'  #4663, checked before each method attempt.
        elif self.request['endpoint'] < 7:
            body['error'] = {'code':-32000, 'message':'synthetic execution refusal'}
        else:
            body['result'] = '0x64'
        raw = json.dumps(body).encode()
        self.case.assertLessEqual(len(raw), maximum)
        return raw


class KeeperWatchdogFailoverProgressTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.notifications = []
        self.attempts = []
        self.delay = 9.0
        self.client = M.Rpc(['https://synthetic'+str(i)+'.invalid' for i in range(8)],4663)
        self.install_transport()
        for target, name, value in ((M.time,'monotonic',self.clock),
                                    (M.time,'sleep',self.clock.sleep)):
            item = patch.object(target,name,value)
            item.start(); self.addCleanup(item.stop)

    def install_transport(self):
        def open_response(request, timeout):
            body = json.loads(request.data)
            endpoint = self.client.urls.index(request.full_url)
            row = {'request':body, 'endpoint':endpoint, 'opened_at':self.clock.now,
                   'timeout':timeout}
            self.attempts.append(row)
            return CompletedResponse(self, row, self.delay)

        self.open = patch.object(self.client._opener,'open',side_effect=open_response)
        self.open.start(); self.addCleanup(self.open.stop)

    def watchdog(self):
        case = self

        class Channel:
            def __enter__(self): return self
            def __exit__(self,*_args): return False
            def setblocking(self, enabled): case.assertIs(enabled,False)
            def sendto(self, data, address):
                case.assertEqual(b'WATCHDOG=1',data)
                case.assertEqual(b'/private/synthetic-watchdog',address)
                case.notifications.append(case.clock.now)
                return len(data)

        family = patch.object(W.socket,'AF_UNIX',getattr(W.socket,'AF_UNIX',999),create=True)
        family.start(); self.addCleanup(family.stop)
        channel = patch.object(W.socket,'socket',return_value=Channel())
        channel.start(); self.addCleanup(channel.stop)
        watchdog = W.ProgressWatchdog(b'/private/synthetic-watchdog',120.0,
                                      owner=os.getpid(),clock=self.clock)
        self.assertTrue(watchdog.pulse(force=True))
        return watchdog

    def configure_progress(self, callback, *, urls=None, retries=None):
        """Match main's explicit construction; never mutate a client's hook."""
        previous = self.client
        self.open.stop()
        self.client = M.Rpc(list(previous.urls) if urls is None else urls,4663,
            timeout=previous.timeout,retries=previous.retries if retries is None else retries,
            transport_attempt_complete=callback)
        self.install_transport()

    def assert_legal_completed_attempts(self):
        self.assertEqual(16,len(self.attempts))
        self.assertEqual(['eth_chainId','eth_blockNumber']*8,
                         [row['request']['method'] for row in self.attempts])
        for row in self.attempts:
            self.assertLess(row['completed_at']-row['opened_at'],row['timeout'])
        self.assertAlmostEqual(151.4,self.clock.now)
        self.assertEqual(7,self.client.active)

    def test_completed_bounded_failover_does_not_falsely_expire_watchdog(self):
        watchdog = self.watchdog()
        self.configure_progress(watchdog.pulse)
        try:
            result = W.ProgressRPC(self.client,watchdog).call('eth_blockNumber')
        except W.WatchdogError as error:
            self.assert_legal_completed_attempts()
            self.fail('All16 HTTP responses completed within10s each and final '
                      'endpoint succeeded, but no intermediate progress was '
                      'reported before151.4s: '+str(error))
        self.assertEqual('0x64',result)
        self.assert_legal_completed_attempts()
        self.assertGreater(len(self.notifications),1)
        self.assertTrue(all(b-a<120 for a,b in zip(self.notifications,self.notifications[1:])))

    def test_plain_rpc_preserves_the_same_legal_failover_result(self):
        self.assertEqual('0x64',self.client.call('eth_blockNumber'))
        self.assert_legal_completed_attempts()
        self.assertEqual([],self.notifications)

    def test_one_overlong_read_cannot_publish_a_late_heartbeat(self):
        self.open.stop()
        self.client = M.Rpc(['https://synthetic0.invalid'],4663,retries=1)
        self.install_transport()
        self.delay = 121.0
        watchdog = self.watchdog()
        self.configure_progress(watchdog.pulse)
        with self.assertRaises(W.WatchdogError):
            W.ProgressRPC(self.client,watchdog).call('eth_blockNumber')
        self.assertEqual(1,len(self.attempts))
        self.assertEqual([0.0],self.notifications)
        self.assertEqual(0.0,watchdog.last)

    def test_completion_callback_stays_on_calling_thread_after_each_http_attempt(self):
        completed = []
        owner = threading.get_ident()
        self.configure_progress(lambda: completed.append((self.clock.now,threading.get_ident())))
        self.assertEqual('0x64',self.client.call('eth_blockNumber'))
        self.assert_legal_completed_attempts()
        self.assertEqual([(row['completed_at'],owner) for row in self.attempts],completed)

    def test_late_watchdog_callback_is_fatal_before_another_endpoint_or_backoff(self):
        watchdog = self.watchdog()
        self.configure_progress(watchdog.pulse)
        self.delay = 121.0
        with self.assertRaises(W.WatchdogError):
            W.ProgressRPC(self.client,watchdog).call('eth_blockNumber')
        self.assertEqual(1,len(self.attempts))
        self.assertEqual(0,self.client.active)
        self.assertEqual([],self.clock.sleeps)
        self.assertEqual([0.0],self.notifications)

    def test_post_budget_exhaustion_remains_fatal_without_a_new_callback_or_retry(self):
        completed = []
        self.configure_progress(lambda: completed.append(self.clock.now))
        with request_scope(Budget(seconds=60,calls=1,posts=1,clock=self.clock)):
            with self.assertRaises(WorkLimit) as observed:
                self.client.call('eth_blockNumber')
        self.assertEqual('rpc_budget',observed.exception.reason)
        self.assertEqual([9.0],completed)
        self.assertEqual(1,len(self.attempts))
        self.assertEqual([],self.clock.sleeps)
        self.assertEqual(0,self.client.active)

    def test_invalid_hooks_reject_and_none_preserves_an_inert_client(self):
        for callback in (False,True,0,'callback',{},[]):
            with self.subTest(kind=type(callback).__name__),self.assertRaises(ValueError):
                M.Rpc(['https://synthetic.invalid'],4663,transport_attempt_complete=callback)
        self.assertIsNone(M.Rpc(['https://synthetic.invalid'],4663).transport_attempt_complete)
        self.assertEqual([],self.attempts)

    def test_completed_remote_error_keeps_its_original_sanitized_retry_cause(self):
        watchdog = self.watchdog()
        self.configure_progress(watchdog.pulse,urls=['https://synthetic0.invalid'],retries=1)
        with self.assertRaises(M.RpcError) as observed:
            W.ProgressRPC(self.client,watchdog).call('eth_blockNumber')
        self.assertIsInstance(observed.exception.__cause__,M.RemoteRPCError)
        self.assertEqual(('eth_blockNumber',-32000,'unclassified'),
            (observed.exception.__cause__.method,observed.exception.__cause__.code,
             observed.exception.__cause__.reason))
        self.assertEqual(2,len(self.attempts)); self.assertEqual([],self.clock.sleeps)
        self.assertEqual([0.0,18.0],self.notifications)
        self.assertNotIn('synthetic0.invalid',str(observed.exception))


class KeeperWatchdogMainTransportWiringTests(unittest.TestCase):
    def test_actual_main_explicitly_connects_only_the_enabled_watchdog_transport(self):
        watchdog = Mock(); watchdog.enabled = True
        inner = Mock(); keeper = Mock(); keeper.run_cycle.return_value = True
        config = {'chain_id':4663,'rpc_urls':['https://synthetic.invalid']}
        with patch('sys.argv',['keeper.monitor','--config','unused-public-fixture','--once']), \
                patch.object(monitor,'read_json',return_value=config), \
                patch.object(monitor.ProgressWatchdog,'from_environment',return_value=watchdog), \
                patch.object(monitor,'Rpc',return_value=inner) as make_rpc, \
                patch.object(monitor,'Keeper',return_value=keeper) as make_keeper, \
                patch.object(monitor,'process_lock',return_value=contextlib.nullcontext()), \
                patch.object(monitor.signal,'signal'):
            monitor.main()
        make_rpc.assert_called_once_with(config['rpc_urls'],4663,
                                         transport_attempt_complete=watchdog.pulse)
        wrapped = make_keeper.call_args.kwargs['rpc']
        self.assertIsInstance(wrapped,W.ProgressRPC)
        self.assertIs(inner,wrapped.inner); self.assertIs(watchdog,wrapped.watchdog)
        keeper.run_cycle.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
