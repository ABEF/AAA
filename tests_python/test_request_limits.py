import contextlib
import io
import json
import multiprocessing
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from frontend_api.activation import ActivationTransactions
from frontend_api.service import Projection
from frontend_api.worker import WorkerClient
from tests_python.test_frontend_activation import ActivationRPC
from tests_python.test_frontend_api import configuration
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.rpc import Rpc
from zzz_ops.work_budget import Budget, BudgetedRPC, checkpoint, consume, expire_at, request_scope


def fast_child(output, config, activation, action, payload):
    Path(output).write_text(json.dumps({'ok': {'completed': True}}), encoding='utf-8')


def blocked_child(output, config, activation, action, payload):
    if payload:
        Path(payload).write_text(str(multiprocessing.current_process().pid), encoding='utf-8')
    time.sleep(10)
    Path(output).write_text(json.dumps({'ok': {'completed': True}}), encoding='utf-8')


def oversized_child(output, config, activation, action, payload):
    Path(output).write_bytes(b'x' * (1024 * 1024 + 1))


def partial_child(output, config, activation, action, payload):
    Path(output).write_bytes(b'{"ok":')


def expired_child(output, config, activation, action, payload):
    Path(output).write_text(json.dumps({'ok': {'expires_at': 1}}), encoding='utf-8')


class RequestBudgetTests(unittest.TestCase):
    def test_nested_scope_cannot_reset_budget_and_cleanup_restores_context(self):
        with request_scope(Budget(calls=1)):
            consume('calls')
            with self.assertRaises(WorkLimit), request_scope(Budget(calls=100)):
                consume('calls')
        with request_scope(Budget(calls=1)):
            consume('calls')

    def test_monotonic_limit_does_not_depend_on_wall_clock(self):
        mono = [1]; wall = [1000]
        with self.assertRaises(WorkLimit), request_scope(Budget(seconds=1, clock=lambda:mono[0])):
            expire_at(1002, lambda:wall[0])
            wall[0] = 100
            mono[0] = 2
            checkpoint()

    def test_wall_clock_jump_expires_before_monotonic_limit(self):
        wall = [1000]
        with self.assertRaisesRegex(WorkLimit, 'snapshot_expired'), request_scope(Budget(clock=lambda:1)):
            expire_at(1001, lambda:wall[0]);wall[0] = 1001;checkpoint()

    def test_limits_reject_nonfinite_boolean_and_unbounded_configuration(self):
        for kwargs in ({'seconds':float('nan')},{'seconds':float('inf')},{'seconds':True},
                       {'seconds':61},{'seconds':0},{'calls':True},{'calls':0},{'posts':4097}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):Budget(**kwargs)

    def test_expired_call_result_is_discarded_without_starting_another_call(self):
        rpc=ActivationRPC();wall=[1000];p=Projection(configuration(),rpc,clock=lambda:wall[0])
        svc=ActivationTransactions(p,rpc.config);original=rpc.call;calls_after=[]
        def call(method,params):
            if wall[0]>1000:calls_after.append(method)
            result=original(method,params)
            if method=='eth_getCode':wall[0]=2000
            return result
        rpc.call=call
        with self.assertRaises(WorkLimit):svc.prepare(rpc.request)
        self.assertEqual(calls_after,[])
        self.assertEqual(rpc.trace_count,0)

    def test_activation_call_budget_is_terminal_and_next_request_gets_fresh_budget(self):
        rpc=ActivationRPC();p=Projection(configuration(),rpc,clock=lambda:1000)
        svc=ActivationTransactions(p,rpc.config)
        with self.assertRaises(WorkLimit),request_scope(Budget(calls=10)):
            svc.prepare(rpc.request)
        result=svc.prepare(rpc.request)
        self.assertTrue(result['activation_ready'])

    def test_expiry_after_first_trace_prevents_second_trace(self):
        rpc=ActivationRPC();wall=[1000];p=Projection(configuration(),rpc,clock=lambda:wall[0])
        svc=ActivationTransactions(p,rpc.config);original=rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='debug_traceCall':wall[0]=1061
            return result
        rpc.call=call
        with self.assertRaises(WorkLimit):svc.prepare(rpc.request)
        self.assertEqual(rpc.trace_count,1)

    def test_post_budget_includes_chain_checks_and_retries(self):
        rpc=Rpc(['https://example.invalid'],1,retries=3)
        def response(req,timeout):
            request=json.loads(req.data)
            return io.BytesIO(json.dumps({'id':request['id'],'jsonrpc':'2.0','result':'0x1'}).encode())
        with patch('urllib.request.urlopen',side_effect=response) as opened:
            with self.assertRaises(WorkLimit), request_scope(Budget(posts=1)):
                rpc.call('eth_blockNumber')
        self.assertEqual(opened.call_count,1)

    def test_timeout_and_backoff_use_only_remaining_budget(self):
        rpc=Rpc(['https://example.invalid'],1,retries=3,timeout=5);mono=[1]
        observed=[]
        def fail(req,timeout):
            observed.append(timeout);raise OSError('SECRET')
        def sleep(seconds):mono[0]+=seconds
        with patch('urllib.request.urlopen',side_effect=fail),patch('zzz_ops.rpc.time.sleep',side_effect=sleep):
            with self.assertRaises(WorkLimit),request_scope(Budget(seconds=.1,clock=lambda:mono[0])):
                rpc.call('eth_blockNumber')
        self.assertEqual(len(observed),1)
        self.assertLessEqual(observed[0],.101)

    def test_terminal_work_limit_never_fails_over(self):
        rpc=Rpc(['https://a.invalid','https://b.invalid'],1)
        with patch.object(rpc,'_post',side_effect=WorkLimit('deadline')) as post:
            with self.assertRaises(WorkLimit):rpc.call('eth_blockNumber')
        self.assertEqual(post.call_count,1);self.assertEqual(rpc.active,0)

    def test_shared_rpc_does_not_double_wrap_for_predecessors(self):
        rpc=ActivationRPC();p=Projection(configuration(),rpc,clock=lambda:1000)
        other=Projection(configuration(),p.rpc,clock=lambda:1000)
        self.assertIs(other.rpc,p.rpc)


class WorkerTests(unittest.TestCase):
    def test_actual_spawn_returns_bounded_result_and_reaps(self):
        client=WorkerClient(configuration())
        with patch('frontend_api.worker._run',fast_child),contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(client.protocol()['completed'])
        self.assertIsNone(client._unreaped)

    def test_blocked_worker_is_terminated_and_next_request_can_succeed(self):
        client=WorkerClient(configuration());started=time.monotonic()
        with tempfile.TemporaryDirectory() as tmp:
            marker=Path(tmp)/'started'
            with patch('frontend_api.worker._run',blocked_child),patch('frontend_api.worker.HARD_SECONDS',1.5),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(WorkLimit):client.nft(str(marker))
            self.assertLess(time.monotonic()-started,5)
            self.assertTrue(marker.exists(),'Blocked child must actually run before the supervisor timeout')
        self.assertIsNone(client._unreaped)
        with patch('frontend_api.worker._run',fast_child),contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(client.protocol()['completed'])

    def test_partial_oversized_and_expired_results_fail_closed(self):
        for child,error in ((partial_child,RpcError),(oversized_child,RpcError),(expired_child,WorkLimit)):
            with self.subTest(child=child.__name__):
                client=WorkerClient(configuration())
                with patch('frontend_api.worker._run',child),contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(error):client.protocol()

    def test_busy_worker_rejects_instead_of_starting_parallel_upstream_work(self):
        client=WorkerClient(configuration());client._lock.acquire()
        try:
            with self.assertRaises(RpcError):client.protocol()
        finally:client._lock.release()
        admission = client._lock
        class QuarantinedAtAdmission:
            def acquire(self, **kwargs):
                acquired=admission.acquire(**kwargs)
                if acquired:client._unreaped=True
                return acquired
            def release(self):admission.release()
        client._lock=QuarantinedAtAdmission()
        with patch('frontend_api.worker.multiprocessing.get_context') as spawn:
            with self.assertRaises(RpcError):client.protocol()
            spawn.assert_not_called()
        self.assertFalse(admission.locked())

    def test_temp_creation_failure_releases_admission_lock(self):
        client=WorkerClient(configuration())
        with patch('frontend_api.worker.tempfile.TemporaryDirectory',side_effect=OSError('SECRET')),contextlib.redirect_stdout(io.StringIO()) as log:
            with self.assertRaises(RpcError):client.protocol()
        self.assertNotIn('SECRET',log.getvalue());self.assertFalse(client._lock.locked())

    def test_cleanup_failure_is_sanitized_and_releases_lock(self):
        client = WorkerClient(configuration())
        admission = client._lock
        case = self
        class CheckedAdmission:
            def acquire(self, **kwargs):return admission.acquire(**kwargs)
            def locked(self):return admission.locked()
            def release(self):
                case.assertIsNotNone(client._unreaped, 'Quarantine must precede reopening admission')
                admission.release()
        client._lock = CheckedAdmission()
        factory = tempfile.TemporaryDirectory
        def failing_cleanup(*args, **kwargs):
            directory = factory(*args, **kwargs)
            original = directory.cleanup
            def cleanup():
                original()
                raise OSError('SECRET cleanup detail')
            directory.cleanup = cleanup
            return directory
        with patch('frontend_api.worker.tempfile.TemporaryDirectory', side_effect=failing_cleanup), \
                patch('frontend_api.worker._run', fast_child), contextlib.redirect_stdout(io.StringIO()) as log:
            with self.assertRaisesRegex(RpcError, '^Request worker cleanup failed$'):
                client.protocol()
        self.assertNotIn('SECRET', log.getvalue())
        self.assertFalse(client._lock.locked())
        self.assertIn('worker_cleanup_failed', log.getvalue())
        self.assertIsNotNone(client._unreaped)
        with patch('frontend_api.worker.multiprocessing.get_context') as spawn:
            with self.assertRaises(RpcError):client.protocol()
            spawn.assert_not_called()


if __name__=='__main__':unittest.main()
