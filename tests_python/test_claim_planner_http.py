"""Opt-in claim-planning HTTP/worker dispatch; no listener or signer rollout."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api.server import handler, MAX_PREPARATION_BODY
from frontend_api.service import Projection, ProjectionError
from frontend_api.transactions import Transactions, TransactionInputError
from frontend_api.worker import WorkerClient, WorkerPool, _run
from tests_python import test_frontend_transaction_http as http_fixtures
from tests_python.test_frontend_api import addr, configuration
from tests_python.test_frontend_transactions import transaction_config
from tests_python.test_claim_planner import PlannerRPC
from zzz_ops.errors import RpcError


class ClaimPlannerHTTPTests(unittest.TestCase):
    def setUp(self):
        self.base=http_fixtures.TransactionHTTPTests('runTest');self.base.setUp()
        self.addCleanup(self.base.tearDown)
        self.body=json.dumps(dict(action='claim',wallet=addr(30),claims=[
            dict(token_id=str(self.base.rpc.nft_id),asset=addr(21),royalty=False)])).encode()
        self.plans=[]
        self.base.preparer.plan_claims=lambda payload:self.plans.append(payload) or dict(schema=1,next_batch=None)

    def request(self,**kwargs):
        return self.base.request(path=kwargs.pop('path','/v1/claims/plan'),body=kwargs.pop('body',self.body),**kwargs)

    def test_new_endpoint_dispatches_distinct_method_without_changing_prepare(self):
        status,headers,result=self.request()
        self.assertEqual(status,200);self.assertEqual(result,dict(schema=1,next_batch=None))
        self.assertEqual(len(self.plans),1);self.assertEqual(self.base.preparer.calls,[])
        self.assertEqual(headers['Cache-Control'],'no-store');self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertEqual(self.base.request()[0],200)
        self.assertEqual(len(self.plans),1);self.assertEqual(len(self.base.preparer.calls),1)

    def test_default_get_only_and_exact_endpoint_boundaries_remain(self):
        self.base.server.RequestHandlerClass=handler(self.base.projection)
        self.assertEqual(self.request()[0],405)
        self.base.server.RequestHandlerClass=handler(self.base.projection,self.base.preparer)
        for method,path in [('GET','/v1/claims/plan'),('POST','/v1/claims/plan/'),
                            ('POST','/v1/claims/plan?rpc=SECRET'),('POST','/v1/claims/send')]:
            with self.subTest(method=method,path=path):
                self.assertEqual(self.request(method=method,path=path,body=b'' if method=='GET' else self.body)[0],404)
        self.assertEqual(self.plans,[])

    def test_new_route_keeps_body_limits_duplicate_rejection_and_sanitized_failures(self):
        self.assertEqual(self.request(body=b'x'*(MAX_PREPARATION_BODY+1))[0],413)
        self.assertEqual(self.request(body=b'{"action":"claim","action":"mint"}')[0],400)
        self.assertEqual(self.plans,[])
        for exception,status,code in [(ProjectionError('SECRET provider'),503,'claim_planning_unavailable'),
                (TransactionInputError('SECRET payload'),400,'invalid_transaction_request')]:
            def fail(_):raise exception
            self.base.preparer.plan_claims=fail
            with contextlib.redirect_stderr(io.StringIO()) as log:
                actual,_headers,result=self.request()
            self.assertEqual((actual,result),(status,{'error':code}));self.assertEqual(log.getvalue(),'')

    def test_actual_planner_crosses_http_with_only_one_next_unsigned_batch(self):
        rpc=PlannerRPC();rpc.maximum_batch=1
        p=Projection(configuration(),rpc,clock=lambda:1000)
        self.base.server.RequestHandlerClass=handler(p,Transactions(p,transaction_config(p)))
        body=json.dumps(dict(action='claim',wallet=addr(30),claims=[
            dict(token_id=str(rpc.nft_id),asset=addr(21),royalty=False),
            dict(token_id=str(rpc.nft_id),asset=addr(20),royalty=False)])).encode()
        status,_headers,result=self.request(body=body)
        self.assertEqual(status,200)
        self.assertEqual(len(result['next_batch']['claim_operations']),1)
        self.assertEqual(len(result['remaining_claims']),1)
        self.assertFalse(result['automatic_submission']);self.assertTrue(result['replan_after_confirmation'])
        self.assertNotIn('transaction',result['remaining_claims'][0])


class ClaimPlannerWorkerTests(unittest.TestCase):
    def test_client_pool_and_child_dispatch_use_a_dedicated_enabled_action(self):
        config=configuration();rpc=PlannerRPC();p=Projection(config,rpc,clock=lambda:1000)
        policy=transaction_config(p);payload=dict(action='claim',wallet=addr(30),claims=[
            dict(token_id=str(rpc.nft_id),asset=addr(21),royalty=False)])
        client=WorkerClient(config,transaction_config=policy)
        with patch.object(client,'_request',return_value={'routed':True}) as request:
            self.assertEqual(client.plan_claims(payload),{'routed':True})
            request.assert_called_once_with('claim_plan',payload)
        disabled=WorkerClient(config)
        with patch.object(disabled,'_request') as request,self.assertRaises(RpcError):
            disabled.plan_claims(payload)
        request.assert_not_called()
        pool=object.__new__(WorkerPool)
        with patch.object(pool,'_dispatch',return_value={'pooled':True}) as dispatch:
            self.assertEqual(pool.plan_claims(payload),{'pooled':True})
            dispatch.assert_called_once_with('plan_claims',payload)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'response.json'
            with patch('frontend_api.worker.Projection',return_value=p):
                _run(output,config,None,'claim_plan',payload,policy)
            result=json.loads(output.read_bytes())
        self.assertIn('ok',result)
        self.assertEqual(result['ok']['kind'],'unsigned_claim_plan')
        self.assertEqual(result['ok']['next_batch']['action'],'claim')

    def test_child_does_not_enable_planning_without_a_reviewed_policy(self):
        p=Projection(configuration(),PlannerRPC(),clock=lambda:1000)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'response.json'
            with patch('frontend_api.worker.Projection',return_value=p):
                _run(output,configuration(),None,'claim_plan',{},None)
            result=json.loads(output.read_bytes())
        self.assertEqual(result,{'error':'unavailable'})


if __name__=='__main__':unittest.main()
