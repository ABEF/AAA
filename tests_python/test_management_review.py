"""Whole unsigned management pipeline, including gas-sensitive batch outcomes.

The transport is injected. Projection, source catalog, adapters, ABI construction,
control comparison and simulations are the actual current implementations.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_python.test_frontend_api import words
from tests_python import test_management_custody as custody_fixtures
from tests_python import test_management_exit as exit_fixtures
from zzz_ops import management_custody as C, management_exit as E, management_review as M
from zzz_ops import operator_review as O
from zzz_ops.abi import keccak256
from zzz_ops.errors import RemoteRPCError, RpcError, WorkLimit
from zzz_ops.management_base import ManagementBlocked


class ManagementReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        custody_fixtures.CustodyManagementTests.setUpClass();exit_fixtures.ManagementExitTests.setUpClass()

    def setUp(self):
        self.h=custody_fixtures.CustodyManagementTests('runTest');self.h.setUp();self.addCleanup(self.h.doCleanups)
        self.rpc=self.h.rpc;self.policy=self.h.f.policy;self.config=self.h.f.config
        self.catalog=self.h.f.catalog;self.now=4000
        self.request={'schema':1,'action':'park','parameters':{'bucket':'7','minimum0':'0','minimum1':'0'},
            'expires_at':'4180','review_notes_sha256':'11'*32,'evidence_sha256':['22'*32]}
        self.add_selectors()

    def add_selectors(self):
        signatures=['park('+C.PARKING_TUPLE+')','closeResidual('+C.PARKING_TUPLE+')',
            'resume(uint256,bytes32,uint128,uint256)','beginCollectiveExit(bytes32)',
            'closeBucket(uint256,uint256,uint256,uint256)','allocatePrincipal(uint256)','distributePrincipal(uint256[])']
        self.rpc.void_selectors.update('0x'+keccak256(sig.encode()).hex()[:8]for sig in signatures)

    def prepare(self):
        return M.prepare(self.config,self.policy,self.request,rpc=self.rpc,clock=lambda:self.now,catalog=self.catalog)

    def use_exit(self,action):
        h=exit_fixtures.ManagementExitTests('runTest');h.setUp();self.addCleanup(h.doCleanups)
        self.x=h;self.rpc=h.rpc;self.config=h.f.config;self.catalog=h.catalog
        self.policy=copy.deepcopy(self.policy);self.policy.update(projection_sha256=h.p.identity,governance=h.gov,extra_contracts=h.extra)
        parameters=({'confirm_terminal_exit':True} if action=='collective_exit_begin' else
            {'bucket':'7','minimumETH':'0','minimumZZZ':'0'} if action=='close_bucket' else
            {'maximum':'2'} if action=='allocate_principal' else {'nft_ids':[str(h.ids[0]),str(h.ids[1])]})
        self.request.update(action=action,parameters=parameters);self.add_selectors()
        if action!='collective_exit_begin':h.terminal({'close_bucket':1,'allocate_principal':2,'distribute_principal':3}[action])
        if action=='distribute_principal':
            # Snapshot remains the complete selected set; return count does not
            # identify which receiver succeeded. The helper never infers a prefix.
            h.put('principal_exit','principalOf(uint256)',[10,20,1,0],h.ids[0])
            h.put('principal_exit','principalOf(uint256)',[30,40,1,0],h.ids[1])
            h.put('principal_exit','claimablePrincipal(uint256)',[10,20],h.ids[0])
            h.put('principal_exit','claimablePrincipal(uint256)',[30,40],h.ids[1])
            self.rpc.output=words(2)

    def test_all_seven_actions_use_real_catalog_exact_two_snapshot_pipeline(self):
        cases=('park','close_residual','resume',*M.EXIT_ACTIONS)
        artifacts={}
        for action in cases:
            with self.subTest(action=action):
                # Independent setup avoids adopting any prior prepared action.
                self.setUp()
                if action in M.EXIT_ACTIONS:self.use_exit(action)
                else:
                    self.request['action']=action
                    if action=='resume':
                        self.h.parked();self.request['parameters']={'bucket':'7','destination_pool':self.h.q.pool,'minimumLiquidity':'7'}
                out=self.prepare()
                artifacts[action]=out
                self.assertFalse(out['ready_for_submission']);self.assertFalse(out['production_approved'])
                self.assertEqual(self.request,out['original_selection']);self.assertEqual('0x0',out['transaction']['value'])
                self.assertIn('gas',out['transaction']);self.assertNotIn('nonce',out['transaction'])
                self.assertTrue(self.catalog.check(out['review'])['artifact_matches'])
                self.assertEqual(4,len(self.rpc.simulations));self.assertEqual(2,len(self.rpc.estimates))
                self.assertEqual(self.rpc.simulations[1][0],self.rpc.simulations[3][0])
                self.assertEqual(out['snapshot']['controls'],out['final_snapshot']['controls'])
                self.assertEqual(action in ('park','close_residual','resume','close_bucket'),out['contract_deadline_enforced'])
                self.assertFalse(any('send' in method.lower() or method=='eth_getTransactionCount' for method,_ in self.rpc.calls))
        self.review_artifacts=artifacts

    def test_healthy_market_change_preserves_exact_floor_deadline_hash_and_gas(self):
        self.request.update(action='close_residual',parameters={'bucket':'7','minimum0':'13','minimum1':'17'})
        self.rpc.after_estimate=lambda:setattr(self.h.q,'tick',50)
        out=self.prepare()
        self.assertNotEqual(out['snapshot']['market_observations'],out['final_snapshot']['market_observations'])
        self.assertEqual('13',out['arguments']['r']['minimum0']);self.assertEqual('17',out['arguments']['r']['minimum1'])
        self.assertEqual('4180',out['arguments']['r']['deadline'])

    def test_custody_change_stops_before_final_simulation(self):
        self.rpc.after_estimate=lambda:self.h.put('principal_exit','parkingNonce(uint256)',6,7)
        with self.assertRaisesRegex(ManagementBlocked,'changed'):self.prepare()
        self.assertEqual(2,len(self.rpc.simulations));self.assertEqual(1,len(self.rpc.estimates))

    def test_frozen_gas_never_increases_after_a_larger_final_estimate(self):
        self.rpc.after_second_estimate=lambda:setattr(self.rpc,'gas',110000)
        with self.assertRaisesRegex(ManagementBlocked,'unchanged transaction gas'):self.prepare()

    def test_distribution_uses_full_explicit_budget_despite_cheap_prefix_estimate(self):
        self.use_exit('distribute_principal');original=self.rpc.call;selector='0x'+keccak256(b'distributePrincipal(uint256[])').hex()[:8]
        def gas_sensitive(method,params):
            self.rpc.output=words(2 if method!='eth_call' or params[0]['data'][:10]!=selector or int(params[0]['gas'],16)>=300000 else 0)
            return original(method,params)
        self.rpc.call=gas_sensitive;out=self.prepare()
        self.assertEqual('1000000',out['network_gas']['transaction_gas'])
        self.assertEqual('explicit_batch_budget',out['network_gas']['gas_strategy'])
        self.assertEqual('0xf4240',out['transaction']['gas'])
        self.assertEqual(2,out['simulation']['final']['result']['paid_count'])
        self.assertFalse(out['simulation']['final']['result']['per_nft_success_proven'])
        self.assertEqual(self.request['parameters']['nft_ids'],out['original_selection']['parameters']['nft_ids'])

    def test_distribution_full_budget_fee_and_funding_not_cheap_estimate_cost(self):
        self.use_exit('distribute_principal');self.policy['fee_policy']['max_network_fee_wei']='300000'
        with self.assertRaisesRegex(ManagementBlocked,'Network fees'):self.prepare()
        self.policy['fee_policy']['max_network_fee_wei']='10000000';self.rpc.balance=300000
        with self.assertRaisesRegex(ManagementBlocked,'full reviewed gas'):self.prepare()

    def test_partial_count_is_not_a_paid_prefix_and_zero_or_malformed_counts_refuse(self):
        self.use_exit('distribute_principal');self.rpc.output=words(1)
        out=self.prepare();result=out['simulation']['final']['result']
        self.assertTrue(result['partial']);self.assertFalse(result['per_nft_success_proven'])
        self.assertNotIn('paid_ids',result);self.assertEqual(2,len(out['arguments']['ids']))
        for output in (words(0),words(3),'0x','0x'+'+'+'0'*62+'1',words(1)+('0'*64)):
            self.rpc.output=output
            with self.assertRaises(ManagementBlocked):self.prepare()

    def test_allocation_cursor_and_distribution_owner_drift_require_new_review(self):
        self.use_exit('allocate_principal')
        self.rpc.after_estimate=lambda:self.x.put('principal_exit','allocationCursor()',2)
        with self.assertRaises((ValueError,RpcError)):self.prepare()
        self.use_exit('distribute_principal')
        from tests_python.test_frontend_api import addr
        self.rpc.after_estimate=lambda:self.x.put('nft','ownerOf(uint256)',addr(88),self.x.ids[0])
        with self.assertRaisesRegex(ManagementBlocked,'changed'):self.prepare()

    def test_expiry_reorg_and_late_tip_are_not_retried(self):
        self.request['expires_at']='4010'
        def advance():
            self.h.f.f.rpc.head=111;self.rpc.extra_headers[111]=('0x'+'ef'*32,4011)
        self.rpc.after_second_estimate=advance
        with self.assertRaises((ManagementBlocked,RpcError)):self.prepare()
        self.assertEqual(2,len(self.rpc.estimates));self.assertEqual(4,len(self.rpc.simulations))

    def test_mutated_selection_and_work_limit_are_terminal(self):
        self.rpc.after_estimate=lambda:self.request['parameters'].update(minimum0='2')
        with self.assertRaisesRegex(ManagementBlocked,'Local source or reviewed inputs'):self.prepare()
        with patch.object(M,'MAX_CALLS',1),self.assertRaises(WorkLimit):self.prepare()

    def test_contract_governance_never_reaches_simulation_or_funding(self):
        self.rpc.governance_code='0x6000'
        with self.assertRaises(M.UnsupportedGovernanceEnvelope):self.prepare()
        self.assertEqual([],self.rpc.simulations)
        self.assertFalse(any(method=='eth_getBalance'for method,_ in self.rpc.calls))

    def test_strict_selection_and_cli_preserve_output_and_sanitize_provider_errors(self):
        for mutation in ({'arbitrary_target':'0x'+'1'*40},{'expires_at':'04180'},{'schema':True}):
            with self.assertRaises(ValueError):M.selection({**self.request,**mutation})
        with tempfile.TemporaryDirectory()as directory:
            paths={key:Path(directory)/(key+'.json')for key in ('read-config','policy','selection','output')}
            for key,value in [('read-config',self.config),('policy',self.policy),('selection',self.request)]:paths[key].write_bytes(O.render(value))
            args=[item for key,path in paths.items()for item in ('--'+key,str(path))]
            stream=io.StringIO()
            with patch.object(M,'prepare',side_effect=RemoteRPCError('private:credential@rpc.invalid',-32000)),contextlib.redirect_stderr(stream):
                self.assertEqual(1,M.main(args))
            self.assertNotIn('credential',stream.getvalue());self.assertIsNone(json.loads(stream.getvalue())['rpc_method'])
            paths['output'].write_bytes(b'preserved')
            existing=io.StringIO()
            with patch.object(M,'prepare')as prepared,contextlib.redirect_stderr(existing):
                self.assertEqual(1,M.main(args));prepared.assert_not_called()
            self.assertEqual('existing_output_preserved',json.loads(existing.getvalue())['reason'])
            self.assertTrue(json.loads(existing.getvalue())['output_may_exist'])
            self.assertEqual(b'preserved',paths['output'].read_bytes())

    def test_cli_writes_real_unsigned_artifact_and_preserves_uncertain_publication(self):
        with tempfile.TemporaryDirectory()as directory:
            paths={key:Path(directory)/(key+'.json')for key in ('read-config','policy','selection','output')}
            for key,value in [('read-config',self.config),('policy',self.policy),('selection',self.request)]:paths[key].write_bytes(O.render(value))
            args=[item for key,path in paths.items()for item in ('--'+key,str(path))]
            original=M.prepare
            def actual(config,policy,chosen):return original(config,policy,chosen,rpc=self.rpc,clock=lambda:self.now,catalog=self.catalog)
            with patch.object(M,'prepare',side_effect=actual),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0,M.main(args))
            artifact=O.load(paths['output'],O.MAX_ARTIFACT)
            self.assertEqual('park',artifact['action']);self.assertFalse(artifact['ready_for_submission'])
            self.assertEqual(4,len(self.rpc.simulations));self.assertNotIn('nonce',artifact['transaction'])
            paths['output'].unlink();saved=M.write_exclusive
            def fail_after_publication(path,raw):saved(path,raw);raise OSError('private:credential@storage.invalid')
            stream=io.StringIO()
            with patch.object(M,'prepare',return_value=artifact),patch.object(M,'write_exclusive',side_effect=fail_after_publication),contextlib.redirect_stderr(stream):
                self.assertEqual(1,M.main(args))
            error=json.loads(stream.getvalue());self.assertEqual('artifact_publication_uncertain',error['reason'])
            self.assertTrue(error['output_may_exist']);self.assertFalse(error['transaction_submitted'])
            self.assertNotIn('credential',stream.getvalue());self.assertEqual(artifact,O.load(paths['output'],O.MAX_ARTIFACT))


if __name__=='__main__':unittest.main()
