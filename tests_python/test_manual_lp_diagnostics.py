"""Cause/stage diagnostics over real unsigned preparation and injected RPC.

No old test methods, public providers, signing, journals or gas qualification.
"""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_python import test_manual_lp_review as fixtures
from tests_python.test_frontend_api import addr
from zzz_ops import manual_lp_review as M
from zzz_ops.errors import RpcError, RemoteRPCError, WorkLimit


class ManualLPDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=M.offline.Catalog()

    def setUp(self):
        self.f=fixtures.ManualLPReviewTests('runTest');self.f.catalog=self.catalog
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.rpc=self.f.rpc;self.request=self.f.request

    def prepare(self):
        return M.prepare(self.f.config,self.f.policy,self.request,rpc=self.rpc,
            clock=lambda:self.f.now,catalog=self.catalog)

    def error(self,base,reason,stage):
        with self.assertRaises(base) as caught:self.prepare()
        self.assertEqual(reason,getattr(caught.exception,'manual_code',None))
        self.assertEqual(stage,getattr(caught.exception,'manual_stage',None))
        return caught.exception

    def cli(self,*,prepare=None,output=None,expected=1):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        root=Path(directory.name);args=[]
        for name,value in [('read-config',self.f.config),('policy',self.f.policy),('selection',self.request)]:
            path=root/(name+'.json');path.write_bytes(M.offline.render(value));args.extend(['--'+name,str(path)])
        output=output or root/'review.json';args.extend(['--output',str(output)])
        original=M.prepare
        def actual(config,policy,selection):
            return original(config,policy,selection,rpc=self.rpc,clock=lambda:self.f.now,catalog=self.catalog)
        stdout=io.StringIO();stderr=io.StringIO()
        with patch.object(M,'prepare',side_effect=prepare or actual),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(expected,M.main(args))
        response=json.loads(stdout.getvalue() if expected==0 else stderr.getvalue())
        return response,output

    def test_input_local_cause_preserves_valueerror_and_stops_before_rpc(self):
        self.request['checks']='32'
        self.error(ValueError,'invalid_request_bounds','input_validation')
        self.assertEqual([],self.rpc.calls)

    def test_configuration_binding_cause_preserves_valueerror(self):
        self.f.policy['projection_sha256']='0'*64
        self.error(ValueError,'read_configuration_mismatch','configuration_validation')
        self.assertEqual([],self.rpc.calls)

    def test_policy_source_and_fee_policy_codes_are_local_not_guessed(self):
        for variant,code in [('source','source_catalog_mismatch'),('fee','invalid_fee_policy')]:
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='source':self.f.policy['reference_sha256']='0'*64
                else:self.f.policy['fee_policy']['estimate_includes_all_fees']=False
                self.error(ValueError,code,'configuration_validation')
                self.assertEqual([],self.rpc.simulations)

    def test_initial_snapshot_lifecycle_and_geometry_codes_preserve_checks(self):
        for variant,code in [('paused','pause_required'),('ticks','same_main_ticks_changed')]:
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='paused':self.f.put('access','paused()',0)
                else:self.request['lower']=str(self.q_lower()+1)
                self.error(RpcError if variant=='paused' else ValueError,code,'initial_snapshot')
                self.assertEqual([],self.rpc.simulations)

    def q_lower(self):return self.f.q.lower

    def test_simulation_output_header_gas_fee_and_funding_have_grouped_local_codes(self):
        for variant,code in [('output','unexpected_simulation_output'),('gas','gas_headroom_exceeded'),
                ('fee','gas_price_exceeded'),('total_fee','network_fee_budget_exceeded'),('balance','insufficient_governance_gas')]:
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='output':self.rpc.output='0x'+'1'*64
                if variant=='gas':self.rpc.gas=900000
                if variant=='fee':self.rpc.price=11
                if variant=='total_fee':self.f.policy['fee_policy']['max_network_fee_wei']='1'
                if variant=='balance':self.rpc.balance=1
                self.error(RpcError,code,'initial_simulation')

    def test_unknown_rpc_revert_is_not_misreported_as_a_financial_guard(self):
        self.rpc.simulation_error=RpcError('https://private:secret@rpc.invalid guard Slippage minL 99')
        response,output=self.cli()
        self.assertEqual('initial_simulation',response['stage'])
        self.assertEqual('manual_preparation_unavailable_or_invalid',response['reason'])
        self.assertFalse(response['output_may_exist']);self.assertFalse(output.exists())
        self.assertNotIn('secret',json.dumps(response));self.assertNotIn('Slippage',json.dumps(response))

    def test_manifest_failure_has_its_own_stage_without_claiming_known_cause(self):
        with patch.object(self.catalog,'prepare',side_effect=ValueError('secret manifest detail')):
            response,_=self.cli()
        self.assertEqual('manifest_preparation',response['stage'])
        self.assertEqual('manual_preparation_unavailable_or_invalid',response['reason'])
        self.assertEqual([],self.rpc.simulations)

    def test_final_controls_failure_is_distinct_from_final_simulation(self):
        self.rpc.after_estimate=lambda:self.f.put('principal_exit','parkingNonce(uint256)',6,7)
        self.error(RpcError,'custody_or_controls_changed','final_snapshot')
        self.assertEqual(2,len(self.rpc.simulations))
        self.setUp();self.rpc.final_simulation_error=RpcError('opaque final rejection secret')
        response,_=self.cli()
        self.assertEqual('final_simulation',response['stage'])
        self.assertEqual('manual_preparation_unavailable_or_invalid',response['reason'])
        self.assertEqual(3,len(self.rpc.simulations))

    def test_final_canonicality_reorg_and_local_input_mutation_are_identified(self):
        for variant,code in [('reorg','final_anchor_changed'),('input','local_inputs_changed')]:
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='reorg':self.rpc.final_reorg=True
                else:self.rpc.after_second_estimate=lambda:self.request.update(minimumLiquidity='2')
                self.error(RpcError,code,'final_canonicality')
                self.assertEqual(4,len(self.rpc.simulations))

    def test_remote_rpc_and_work_limit_use_only_bounded_trusted_metadata(self):
        for error,reason in [(RemoteRPCError('eth_call',-32005,'rate_limited'),'rpc_rate_limited'),
                (WorkLimit('rpc_budget'),'work_limit_rpc_budget')]:
            with self.subTest(reason=reason):
                self.setUp();self.rpc.simulation_error=error
                response,_=self.cli()
                self.assertEqual(reason,response['reason']);self.assertEqual('initial_simulation',response['stage'])
                self.assertFalse(response['transaction_submitted'])
                if isinstance(error,RemoteRPCError):
                    self.assertEqual('eth_call',response['rpc_method']);self.assertEqual(-32005,response['rpc_code'])

    def test_remote_mutable_metadata_and_exception_class_cannot_leak(self):
        for variant in ('remote','unknown'):
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='remote':
                    error=RemoteRPCError('secret-method',2**100,'unclassified');error.reason='secret-reason'
                else:
                    error=type('secret_class_name',(Exception,),{})('secret provider password')
                    error.manual_stage='secret-stage';error.manual_code='secret-code'
                self.rpc.simulation_error=error
                response,_=self.cli()
                self.assertNotIn('secret',json.dumps(response))
                if variant=='remote':
                    self.assertIsNone(response['rpc_method']);self.assertIsNone(response['rpc_code'])
                    self.assertEqual('rpc_unclassified',response['reason'])
                else:self.assertEqual('Exception',response['error_type'])

    def test_existing_specific_wallet_and_parked_mask_reason_codes_stay(self):
        self.rpc.governance_code='0x6000'
        response,_=self.cli()
        self.assertEqual('unsupported_contract_wallet_envelope',response['reason'])
        self.assertEqual('initial_snapshot',response['stage'])
        self.setUp();self.request.update(schema=2,action='D',checks='1',expected_position_status='parked')
        response,_=self.cli()
        self.assertEqual('parked_active_trigger_or_confirmation_incompatible',response['reason'])
        self.assertEqual('input_validation',response['stage'])

    def test_success_cli_payload_and_transaction_boundary_stay_unchanged(self):
        response,path=self.cli(expected=0)
        self.assertEqual({'created':True,'kind':'unsigned_manual_lp_preparation','ready_for_submission':False},response)
        artifact=json.loads(path.read_bytes());self.assertFalse(artifact['ready_for_submission'])
        self.assertNotIn('manual_stage',artifact);self.assertNotIn('manual_code',artifact)
        self.assertFalse(any('send' in method.lower() or 'TransactionCount' in method for method,_ in self.rpc.calls))

    def test_preexisting_regular_output_is_preserved_without_prepare(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'existing.json';path.write_bytes(b'original')
            response,_=self.cli(output=path,prepare=AssertionError('must not prepare'))
            self.assertEqual('existing_output_preserved',response['reason'])
            self.assertTrue(response['output_may_exist']);self.assertEqual(b'original',path.read_bytes())
            self.assertEqual([],self.rpc.calls)

    def test_dangling_symlink_is_preserved_without_prepare(self):
        # The link need not exist on Windows; lexists admission is injected,
        # while POSIX can use an actual dangling link in the same assertion.
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'dangling.json'
            with patch.object(M.os.path,'lexists',return_value=True):
                response,_=self.cli(output=path,prepare=AssertionError('must not prepare'))
            self.assertEqual('existing_output_preserved',response['reason'])
            self.assertTrue(response['output_may_exist']);self.assertEqual([],self.rpc.calls)

    def test_render_failure_has_no_publication_attempt(self):
        original=M.offline.render
        def render(value):
            if isinstance(value,dict) and value.get('kind')=='unsigned_manual_lp_preparation':raise ValueError('secret render')
            return original(value)
        with patch.object(M.offline,'render',side_effect=render):response,path=self.cli()
        self.assertEqual('artifact_rendering',response['stage']);self.assertFalse(response['output_may_exist'])
        self.assertFalse(path.exists());self.assertNotIn('secret',json.dumps(response))

    def test_publication_failure_before_link_is_uncertain_without_retry(self):
        with patch.object(M.os,'link',side_effect=PermissionError('secret local path')) as linking:
            response,path=self.cli()
        self.assertEqual('artifact_publication',response['stage']);self.assertTrue(response['output_may_exist'])
        self.assertEqual(1,linking.call_count);self.assertFalse(path.exists())
        self.assertFalse(response['transaction_submitted'])

    def test_directory_fsync_failure_preserves_complete_published_artifact(self):
        original_open,original_close,original_fsync=M.os.open,M.os.close,M.os.fsync
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        path=Path(directory.name)/'review.json';sentinel=2147483600
        def opened(target,flags,*args,**kwargs):
            if Path(target)==path.parent:return sentinel
            return original_open(target,flags,*args,**kwargs)
        def synced(fd):
            if fd==sentinel:raise OSError('secret directory fsync')
            return original_fsync(fd)
        def closed(fd):
            if fd!=sentinel:return original_close(fd)
        with patch.object(M.os,'O_DIRECTORY',0,create=True),patch.object(M.os,'open',side_effect=opened),\
                patch.object(M.os,'close',side_effect=closed),patch.object(M.os,'fsync',side_effect=synced):
            response,_=self.cli(output=path)
        self.assertTrue(response['output_may_exist']);self.assertEqual('artifact_publication',response['stage'])
        self.assertEqual('unsigned_manual_lp_preparation',json.loads(path.read_bytes())['kind'])

    def test_post_publication_reporting_failure_keeps_complete_file(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        path=Path(directory.name)/'review.json'
        original_write=M.write_exclusive
        def uncertain(output,raw):
            original_write(output,raw);raise OSError('secret after publication')
        with patch.object(M,'write_exclusive',side_effect=uncertain):response,_=self.cli(output=path)
        self.assertTrue(response['output_may_exist']);self.assertEqual('artifact_publication',response['stage'])
        self.assertEqual('unsigned_manual_lp_preparation',json.loads(path.read_bytes())['kind'])

    def test_header_mismatch_and_estimate_failure_remain_distinct(self):
        from zzz_ops.abi import calldata
        original=self.rpc.call
        def call(method,params):
            value=original(method,params)
            if method=='eth_getBlockByNumber' and self.rpc.calls and params[0]!='latest':
                if any(m=='eth_call' and p[0]['data']==calldata('consolidationCustodyHash(uint256)',7) for m,p in self.rpc.calls):
                    return {**value,'hash':'0x'+'ab'*32}
            return value
        self.rpc.call=call
        self.error(RpcError,'simulation_header_changed','initial_simulation')
        self.assertEqual([],self.rpc.simulations)
        self.setUp();original=self.rpc.call
        def estimate_failure(method,params):
            if method=='eth_estimateGas':raise RpcError('secret opaque estimation failure')
            return original(method,params)
        self.rpc.call=estimate_failure;response,_=self.cli()
        self.assertEqual('initial_simulation',response['stage'])
        self.assertEqual('manual_preparation_unavailable_or_invalid',response['reason'])
        self.assertEqual(1,len(self.rpc.simulations))

    def test_final_head_retreat_and_opaque_finish_failure_are_not_guessed_expiry(self):
        def retreat():
            self.rpc.inner.head=111;self.rpc.extra_headers[111]=('0x'+'ab'*32,3999)
        self.rpc.after_second_estimate=retreat
        self.error(RpcError,'original_deadline_or_head_changed','final_canonicality')
        self.setUp()
        with patch.object(M.Projection,'_finish',side_effect=RpcError('secret unavailable final ancestry')):
            response,_=self.cli()
        self.assertEqual('final_canonicality',response['stage'])
        self.assertEqual('manual_preparation_unavailable_or_invalid',response['reason'])

    def test_mutable_unhashable_and_valid_foreign_metadata_cannot_invent_causes(self):
        for variant in ('unhashable','foreign_valid','hostile_getter'):
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='unhashable':
                    error=RemoteRPCError('eth_call',-32000);error.reason=[];error.method={};error.code=True
                elif variant=='foreign_valid':
                    error=RpcError('secret opaque error');error.manual_code='insufficient_governance_gas'
                else:
                    class Hostile(RpcError):
                        @property
                        def manual_stage(self):raise RpcError('secret metadata URL')
                    error=Hostile('secret payload')
                self.rpc.simulation_error=error;response,_=self.cli()
                self.assertNotIn('secret',json.dumps(response))
                self.assertNotEqual('insufficient_governance_gas',response['reason'])
                if variant=='unhashable':
                    self.assertIsNone(response['rpc_method']);self.assertIsNone(response['rpc_code'])
                    self.assertEqual('rpc_unclassified',response['reason'])

    def test_existing_output_is_preserved_even_with_missing_input_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);output=root/'existing.json';output.write_bytes(b'original')
            args=['--read-config',str(root/'missing.json'),'--policy',str(root/'missing2.json'),
                '--selection',str(root/'missing3.json'),'--output',str(output)]
            stream=io.StringIO()
            with contextlib.redirect_stderr(stream):self.assertEqual(1,M.main(args))
            response=json.loads(stream.getvalue())
            self.assertEqual('existing_output_preserved',response['reason'])
            self.assertTrue(response['output_may_exist']);self.assertEqual(b'original',output.read_bytes())
            self.assertEqual([],self.rpc.calls)

    def test_temporary_fsync_failure_is_uncertain_without_publishing_partial_bytes(self):
        with patch.object(M.os,'fsync',side_effect=OSError('secret temp fsync')):
            response,path=self.cli()
        self.assertEqual('artifact_publication_uncertain',response['reason'])
        self.assertTrue(response['output_may_exist']);self.assertFalse(path.exists())

    def test_temporary_cleanup_failure_preserves_complete_linked_bytes(self):
        original=Path.unlink
        def unlink(path,*args,**kwargs):
            if path.name.startswith('.manual-lp-'):raise OSError('secret temp cleanup')
            return original(path,*args,**kwargs)
        with patch.object(Path,'unlink',side_effect=unlink,autospec=True):response,path=self.cli()
        self.assertEqual('artifact_publication_uncertain',response['reason'])
        self.assertTrue(response['output_may_exist'])
        self.assertEqual('unsigned_manual_lp_preparation',json.loads(path.read_bytes())['kind'])

    def test_actual_success_reporting_failure_is_publication_uncertain(self):
        import builtins
        original=builtins.print
        def printed(*args,**kwargs):
            if args and isinstance(args[0],str) and args[0].startswith('{"created":'):
                raise OSError('secret stdout failure')
            return original(*args,**kwargs)
        with patch.object(builtins,'print',side_effect=printed):response,path=self.cli()
        self.assertEqual('artifact_publication_uncertain',response['reason'])
        self.assertTrue(response['output_may_exist'])
        self.assertEqual('unsigned_manual_lp_preparation',json.loads(path.read_bytes())['kind'])

    def test_static_human_messages_distinguish_known_gas_failures(self):
        messages=[]
        for variant,code in [('gas','gas_headroom_exceeded'),('price','gas_price_exceeded'),('fee','network_fee_budget_exceeded')]:
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='gas':self.rpc.gas=900000
                if variant=='price':self.rpc.price=11
                if variant=='fee':self.f.policy['fee_policy']['max_network_fee_wei']='1'
                response,_=self.cli();self.assertEqual(code,response['reason'])
                messages.append(response['message'])
        self.assertEqual(3,len(set(messages)))

    def test_nonannotatable_rpc_failure_uses_honest_preparation_stage_fallback(self):
        class NonAnnotatable(RpcError):
            def __setattr__(self,name,value):
                if name=='manual_stage':raise AttributeError('secret annotation failure')
                return super().__setattr__(name,value)
        self.rpc.simulation_error=NonAnnotatable('secret opaque simulation payload')
        response,path=self.cli()
        self.assertEqual('preparation',response['stage'])
        self.assertEqual('RpcError',response['error_type'])
        self.assertEqual('manual_preparation_unavailable_or_invalid',response['reason'])
        self.assertFalse(response['output_may_exist']);self.assertFalse(response['transaction_submitted'])
        self.assertFalse(path.exists());self.assertNotIn('secret',json.dumps(response))
        self.assertEqual(1,len(self.rpc.simulations));self.assertEqual([],self.rpc.estimates)
        invalid=M.diagnostic(RpcError('secret unavailable stage'),[])
        self.assertEqual('preparation',invalid['stage'])
        self.assertNotIn('secret',json.dumps(invalid))


if __name__=='__main__':unittest.main()
