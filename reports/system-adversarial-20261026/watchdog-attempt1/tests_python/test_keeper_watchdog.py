"""Main-thread progress and watchdog composition; no live service or signer.

Fake clocks/sockets verify blocking/no-progress semantics without slow tests.
The one real Unix datagram test is explicitly skipped on unsupported platforms.
"""
import contextlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch

from keeper import monitor
from keeper.watchdog import ProgressWatchdog, ProgressRPC, WatchdogError
from zzz_ops.rpc import RpcError


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.clock = Mock(return_value=0.0)
        self.env = {'WATCHDOG_USEC': '120000000', 'WATCHDOG_PID': str(os.getpid()),
                    'NOTIFY_SOCKET': '/run/synthetic-notify'}
        self.channel = Mock()
        self.channel.__enter__ = Mock(return_value=self.channel)
        self.channel.__exit__ = Mock(return_value=False)
        self.channel.sendto.return_value = len(b'WATCHDOG=1')
        self.socket = patch('keeper.watchdog.socket.socket', return_value=self.channel)
        self.make_socket = self.socket.start()
        self.addCleanup(self.socket.stop)

    def watchdog(self, env=None):
        return ProgressWatchdog.from_environment(self.env if env is None else env,
                                                 clock=self.clock)

    def test_unconfigured_watchdog_is_noop_without_clock_or_socket(self):
        watchdog = self.watchdog({})
        self.assertFalse(watchdog.enabled)
        self.assertFalse(watchdog.pulse(force=True))
        self.make_socket.assert_not_called()
        self.clock.assert_not_called()

    def test_ancestor_pid_does_not_authorize_descendant_progress(self):
        watchdog = self.watchdog({**self.env, 'WATCHDOG_PID': str(os.getpid()+1)})
        self.assertFalse(watchdog.enabled)
        self.assertFalse(watchdog.pulse(force=True))
        self.make_socket.assert_not_called()

    def test_malformed_configuration_is_rejected_without_echoing_values(self):
        values = (('WATCHDOG_USEC','0'), ('WATCHDOG_USEC','-1'),
                  ('WATCHDOG_USEC','1.0'), ('WATCHDOG_USEC','001'),
                  ('WATCHDOG_USEC',str(2**64)), ('WATCHDOG_USEC',True),
                  ('WATCHDOG_PID','0'), ('WATCHDOG_PID','+1'),
                  ('WATCHDOG_PID',str(2**31)), ('WATCHDOG_PID',1),
                  ('NOTIFY_SOCKET',''), ('NOTIFY_SOCKET','relative/SYNTHETIC_SECRET'),
                  ('NOTIFY_SOCKET','@'), ('NOTIFY_SOCKET','/bad\nSYNTHETIC_SECRET'),
                  ('NOTIFY_SOCKET','/bad\0SYNTHETIC_SECRET'),
                  ('NOTIFY_SOCKET','/'+'x'*107))
        for field, value in values:
            with self.subTest(field=field,value=value), self.assertRaises(WatchdogError) as observed:
                self.watchdog({**self.env, field:value})
            self.assertNotIn('SYNTHETIC_SECRET', str(observed.exception))
        missing = dict(self.env);del missing['NOTIFY_SOCKET']
        with self.assertRaises(WatchdogError): self.watchdog(missing)
        self.make_socket.assert_not_called()

    def test_main_progress_sends_only_fixed_nonblocking_datagram(self):
        watchdog = self.watchdog()
        self.assertTrue(watchdog.pulse())
        self.make_socket.assert_called_once_with(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.channel.setblocking.assert_called_once_with(False)
        self.channel.sendto.assert_called_once_with(b'WATCHDOG=1',b'/run/synthetic-notify')
        self.channel.__exit__.assert_called_once()

    def test_abstract_notification_socket_is_encoded_without_path_leak(self):
        watchdog = self.watchdog({**self.env,'NOTIFY_SOCKET':'@synthetic'})
        watchdog.pulse()
        self.channel.sendto.assert_called_once_with(b'WATCHDOG=1',b'\0synthetic')

    def test_cadence_preserves_margin_for_bounded_ninety_second_signer(self):
        watchdog = self.watchdog();watchdog.pulse()
        self.clock.return_value = 9.0
        self.assertFalse(watchdog.pulse())
        self.clock.return_value = 10.0
        self.assertTrue(watchdog.pulse())
        # A completed90s step after at most9s since the last pulse is not late.
        self.clock.return_value = 109.0
        self.assertTrue(watchdog.pulse())
        self.assertEqual(self.channel.sendto.call_count,3)

    def test_short_reviewed_intervals_use_one_third_cadence_and_force_is_explicit(self):
        watchdog = self.watchdog({**self.env,'WATCHDOG_USEC':'6000000'})
        watchdog.pulse();self.clock.return_value = 1.0
        self.assertFalse(watchdog.pulse())
        self.assertTrue(watchdog.pulse(force=True))
        self.clock.return_value = 2.9
        self.assertFalse(watchdog.pulse())
        self.clock.return_value = 3.0
        self.assertTrue(watchdog.pulse())

    def test_late_or_backward_progress_cannot_revive_a_missed_watchdog(self):
        for now in (120.0,121.0,-1.0,float('nan'),float('inf')):
            with self.subTest(now=now):
                self.clock.return_value = 0.0
                watchdog = self.watchdog();watchdog.pulse()
                before = self.channel.sendto.call_count
                self.clock.return_value = now
                with self.assertRaises(WatchdogError):watchdog.pulse(force=True)
                self.assertEqual(self.channel.sendto.call_count,before)

    def test_forked_process_cannot_use_captured_main_identity(self):
        watchdog = self.watchdog()
        with patch('keeper.watchdog.os.getpid',return_value=os.getpid()+1), self.assertRaises(WatchdogError):
            watchdog.pulse(force=True)
        self.make_socket.assert_not_called()

    def test_failed_or_short_notification_is_sanitized_and_not_credited(self):
        for outcome in (OSError('SYNTHETIC_SECRET'),0):
            watchdog = self.watchdog()
            self.channel.sendto.side_effect = outcome if isinstance(outcome,Exception) else None
            self.channel.sendto.return_value = outcome if not isinstance(outcome,Exception) else 0
            with self.subTest(outcome=type(outcome).__name__), self.assertRaises(WatchdogError) as observed:
                watchdog.pulse(force=True)
            self.assertNotIn('SYNTHETIC_SECRET',str(observed.exception))
            self.assertIsNone(watchdog.last)
        self.assertEqual(self.channel.__exit__.call_count,2)

    def test_systemd_environment_is_consumed_before_children_are_constructed(self):
        with patch.dict(os.environ,{**self.env,'KEPT_SETTING':'still-present'},clear=True):
            watchdog = ProgressWatchdog.from_environment(clock=self.clock)
            self.assertTrue(watchdog.enabled)
            self.assertEqual(dict(os.environ),{'KEPT_SETTING':'still-present'})
            self.assertFalse(ProgressWatchdog.from_environment(clock=self.clock).enabled)


class ProgressRPCTests(unittest.TestCase):
    def test_only_completed_read_calls_pulse_and_all_other_identity_is_delegated(self):
        watchdog = Mock();events=[]
        watchdog.pulse.side_effect=lambda:events.append('progress')
        inner = Mock();inner.active_url='https://synthetic.invalid'
        def read(method,params):
            self.assertEqual(events,[])
            events.append(('read',method,params))
            return 4663
        inner.call.side_effect=read
        rpc=ProgressRPC(inner,watchdog)
        self.assertEqual(rpc.active_url,inner.active_url)
        self.assertEqual(rpc.call('eth_chainId'),4663)
        self.assertEqual(events,[('read','eth_chainId',None),'progress'])
        inner.call.assert_called_once_with('eth_chainId',None)

    def test_bounded_read_error_is_progress_but_original_error_is_preserved(self):
        watchdog=Mock();inner=Mock();failure=RpcError('Synthetic read failure')
        inner.call.side_effect=failure
        with self.assertRaises(RpcError) as observed:ProgressRPC(inner,watchdog).call('eth_call',['fixture'])
        self.assertIs(observed.exception,failure)
        watchdog.pulse.assert_called_once_with()


class WatchdogMainTests(unittest.TestCase):
    def run_main(self,extra,*,enabled=True,repeat=False):
        events=[];saved={};watchdog=Mock();watchdog.enabled=enabled
        watchdog.pulse.side_effect=lambda **kw:events.append(('pulse',kw))
        rpc=Mock();rpc.call.side_effect=lambda method,params=None:events.append(('rpc',method)) or 1
        class FakeKeeper:
            def __init__(self,config,*,live=False,**kwargs):
                events.append(('construct',live,sorted(kwargs)))
                saved['keeper']=self
                self.rpc=kwargs.get('rpc')
                self.cycle_failures=0
                if self.rpc is not None:self.rpc.call('eth_chainId')
            def run_cycle(self):events.append(('cycle',));return True
            def initialize_state(self):events.append(('initialize',))
            def resolve_pending(self,value):events.append(('resolve',value))
        @contextlib.contextmanager
        def lock(path):events.append(('lock',));yield
        def on_signal(number,handler):saved[number]=handler
        def sleep(seconds):
            events.append(('sleep',seconds))
            saved[monitor.signal.SIGTERM]()
        with tempfile.TemporaryDirectory() as temporary:
            config=Path(temporary)/'config.json'
            config.write_text(json.dumps({'chain_id':1,'rpc_urls':['https://synthetic.invalid'],
                                           'interval_seconds':60}),encoding='utf-8')
            args=['keeper.monitor','--config',str(config),*extra]
            with patch('sys.argv',args), patch.object(monitor.ProgressWatchdog,'from_environment',return_value=watchdog), \
                    patch.object(monitor,'Rpc',return_value=rpc) as make_rpc, \
                    patch.object(monitor,'Keeper',FakeKeeper),patch.object(monitor,'process_lock',lock), \
                    patch.object(monitor.signal,'signal',side_effect=on_signal), \
                    patch.object(monitor.time,'sleep',side_effect=sleep):
                monitor.main()
            saved['rpc_constructed']=make_rpc.call_count
        return events,saved

    def test_once_mode_pulses_before_constructor_and_wraps_its_real_read_path(self):
        events,saved=self.run_main(['--once','--live'])
        self.assertEqual(events[0],('pulse',{'force':True}))
        construction=next(i for i,x in enumerate(events) if x[0]=='construct')
        self.assertEqual(events[construction],('construct',True,['rpc']))
        self.assertEqual(events[construction+1:construction+3],[('rpc','eth_chainId'),('pulse',{})])
        self.assertEqual(sum(x[0]=='cycle' for x in events),1)
        self.assertFalse(any(x[0]=='sleep' for x in events))
        self.assertEqual(saved['rpc_constructed'],1)

    def test_without_watchdog_preserves_old_constructor_and_once_dispatch(self):
        events,saved=self.run_main(['--once'],enabled=False)
        self.assertIn(('construct',False,[]),events)
        self.assertEqual(saved['rpc_constructed'],0)
        self.assertEqual(sum(x[0]=='cycle' for x in events),1)

    def test_initialize_and_explicit_resolution_do_not_start_a_cycle(self):
        for extra,expected in ((['--initialize-state'],('initialize',)),
                               (['--resolve-pending','fixture-hash'],('resolve','fixture-hash'))):
            with self.subTest(action=extra):
                events,_saved=self.run_main(extra)
                self.assertIn(expected,events)
                self.assertFalse(any(x[0] in ('cycle','sleep') for x in events))

    def test_intentional_idle_pulses_main_thread_and_honors_existing_stop_request(self):
        events,saved=self.run_main([])
        sleep_at=events.index(('sleep',1))
        self.assertEqual(events[sleep_at-1],('pulse',{}))
        self.assertTrue(saved['keeper'].stop_requested())
        self.assertEqual(sum(x[0]=='cycle' for x in events),1)


class WatchdogServiceTests(unittest.TestCase):
    def test_shipped_service_has_matching_main_watchdog_group_kill_and_no_core_policy(self):
        unit=(Path(__file__).resolve().parents[1]/'keeper/zzz-keeper.service').read_text()
        values=dict(line.split('=',1) for line in unit.splitlines() if '=' in line and not line.startswith('#'))
        for key,value in {'Type':'simple','NotifyAccess':'main','WatchdogSec':'120s',
                          'WatchdogSignal':'SIGKILL','KillMode':'control-group',
                          'SendSIGKILL':'yes','FinalKillSignal':'SIGKILL',
                          'TimeoutStopSec':'120','Restart':'on-failure','LimitCORE':'0'}.items():
            self.assertEqual(values[key],value)
        self.assertIn('systemd>=240',unit)

    @unittest.skipUnless(os.name=='posix' and hasattr(socket,'AF_UNIX'),
                         'Actual Unix datagram semantics require Unix; no systemd service is started.')
    def test_actual_private_unix_datagram_receives_only_fixed_watchdog_payload(self):
        with tempfile.TemporaryDirectory(prefix='popl-wd-') as temporary:
            path=str(Path(temporary)/'notify')
            with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as receiver:
                receiver.bind(path);receiver.settimeout(0.2)
                watchdog=ProgressWatchdog.from_environment({'WATCHDOG_USEC':'120000000',
                                                            'NOTIFY_SOCKET':path})
                self.assertTrue(watchdog.pulse(force=True))
                self.assertEqual(receiver.recv(64),b'WATCHDOG=1')


if __name__=='__main__':unittest.main()
