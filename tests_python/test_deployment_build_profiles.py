"""Focused trusted-build regression checks; offline only, no constructor run."""
import copy,gzip,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from zzz_ops import deployment_plan as D

_spec=importlib.util.spec_from_file_location('deployment_build_evidence',D.ROOT/'scripts/check-local-deployment-evidence.py')
M=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(M)


class DeploymentBuildProfileTests(unittest.TestCase):
    def complete(self):
        value=D.template();value['planned_addresses']={role:'0x'+f'{0x220000+i:040x}'for i,(role,_,_)in enumerate(D.TOP)}
        value['inputs'].update(governance='0x'+'a1'*20,keeper='0x'+'a2'*20,guardian='0x'+'a3'*20,
            mint_recipient='0x'+'a4'*20,sequencer=D.ZERO,**D.NATIVE,seadrop=D.SEADROP,
            seadrop_codehash=D.SEADROP_HASH,base_uri='ipfs://fresh-metadata2/é',buyback_maximum_trade_usd=str(100*10**18))
        return value
    @classmethod
    def bindings_fixture(cls):
        if not hasattr(cls,'_bindings'):
            evidence=M.Evidence(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')
            try:
                rows=evidence.obj('attempt1/bindings.json');instances=evidence.obj('attempt1/instances.json')
                inputs=evidence.obj('attempt1/actual-address-input.json')['inputs']
                wire,_=evidence.zipped_json('attempt1/node/rpc-records.json.gz')
            finally:evidence.zip.close()
            compiler=json.loads(gzip.decompress((D.ROOT/D.BUILD/'compiler-output.json.gz').read_bytes()))
            ledger=bytes.fromhex(compiler['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
            cls._bindings=(rows,wire,{x['role']:x['address']for x in instances},inputs,ledger)
        return copy.deepcopy(cls._bindings)
    def test_default_planner_accepts_current_metadata_build_and_tags_identity(self):
        result=D.prepare(D.template())
        self.assertEqual(result['accepted_build']['profile'],'seal-boundaries-20261117')
        self.assertEqual(result['accepted_build']['source_count'],100)
        self.assertEqual(result['accepted_build']['normal_size_gates'],48)
        self.assertEqual(len(result['instances']),39)
        self.assertFalse(result['ready_for_submission'])
        self.assertFalse(result['production_approved'])

    def test_scheme_only_artwork_is_rejected_before_artifacts_or_calldata(self):
        for root in ('ipfs://','ar://'):
            value=self.complete();value['inputs']['base_uri']=root
            with self.subTest(root=root),patch.object(D,'Artifacts',side_effect=AssertionError('invalid input must fail first')):
                with self.assertRaisesRegex(D.PlanError,'invalid_uri'):
                    D.prepare(value)
        # Draft setup and real suffixes retain their previous meanings; no CID
        # availability or content validity is inferred by the offline planner.
        for root in ('','ipfs://fresh/é','ar://reviewed-root'):
            value=self.complete();value['inputs']['base_uri']=root
            self.assertEqual(root,D.validate(value)['inputs']['base_uri'])

    def test_seal_fix_keeps_previous_objects_historical_without_automatic_fallback(self):
        self.assertEqual(D.PREVIOUS_BUILD_PROFILE, 'operator-seal-20261117')
        self.assertEqual(D.METADATA_BUILD_PROFILE, 'metadata2-20261116')
        self.assertIn(D.METADATA_BUILD_PROFILE,D.TRUSTED_BUILDS)
        previous = D.TRUSTED_BUILDS[D.PREVIOUS_BUILD_PROFILE]
        for name, expected in previous['files'].items():
            self.assertEqual(D.sha((D.ROOT / previous['directory'] / name).read_bytes()), expected)
        old = json.loads(gzip.decompress((D.ROOT / previous['directory'] / 'compiler-output.json.gz').read_bytes()))
        old_vault = old['contracts']['src/ZZZVault.sol']['ZZZVault']
        current_vault = D.Artifacts().contract('ZZZVault')[1]
        self.assertNotEqual(old_vault['evm']['bytecode']['object'], current_vault['evm']['bytecode']['object'])
        self.assertEqual(old_vault['abi'], current_vault['abi'])
        with self.assertRaisesRegex(D.PlanError, 'source_changed'):
            D.prepare(D.template(), build_profile=D.PREVIOUS_BUILD_PROFILE)
        self.assertEqual(D.prepare(D.template())['accepted_build']['profile'], 'seal-boundaries-20261117')

    def test_checker_rejects_duplicated_binding_observation_coverage(self):
        original=M.Evidence
        class RepeatedBindings(original):
            def obj(self,name):
                value=super().obj(name)
                if name.endswith('/bindings.json'):return [value[0]]*112
                return value
        with patch.object(M,'Evidence',RepeatedBindings):
            with self.assertRaisesRegex(ValueError,'binding observation'):
                M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip',D.ROOT/D.BUILD)

    def test_current_complete_graph_has_exact_objects_and_original_size_limits(self):
        result=D.prepare(self.complete());build=D.Artifacts()
        self.assertEqual(result['build_profile'],D.DEFAULT_BUILD_PROFILE)
        self.assertTrue(result['top_level_constructor_payloads_complete'])
        self.assertFalse(result['all_instance_constructor_payloads_complete'])
        for row in result['instances']:
            obj=build.contract(row['contract'])[1]
            self.assertEqual(row['creation_object_sha256'],D.sha(bytes.fromhex(obj['evm']['bytecode']['object'])))
            self.assertLessEqual(row['runtime_bytes'],24576)
            self.assertLessEqual(row['full_initcode_bytes'],49152)
            if row['full_initcode_hex']:self.assertEqual(len(bytes.fromhex(row['full_initcode_hex'][2:])),row['full_initcode_bytes'])
        by_role={row['role']:row for row in result['instances']}
        self.assertEqual(by_role['metadata_renderer']['runtime_bytes'],24119)
        self.assertEqual(by_role['nft_canonical']['runtime_bytes'],23130)
        self.assertEqual(by_role['access']['full_initcode_bytes'],48377)
        self.assertEqual(by_role['oracle']['runtime_margin'],3)
        self.assertEqual(result['accepted_build']['source_count'],100)
        self.assertEqual(result['accepted_build']['normal_size_gates'],48)

    def test_unknown_build_rejected_before_build_filesystem_reads(self):
        value=D.template()
        for profile in ('unknown','../arbitrary',None,True):
            with self.subTest(profile=profile),patch.object(Path,'open',side_effect=AssertionError('No build read')):
                with self.assertRaisesRegex(D.PlanError,'unsupported_build_profile'):D.prepare(value,build_profile=profile)

    def test_explicit_historical_fixture_retains_old_objects_and_source_identity(self):
        from tests_python.deployment_legacy_fixture import deployment_plan as legacy
        result=legacy.prepare(legacy.template())
        self.assertEqual(result['build_profile'],D.LEGACY_BUILD_PROFILE)
        self.assertEqual(result['accepted_build']['files_sha256'],D.BUILD_PINS)
        self.assertEqual(next(r for r in result['instances']if r['role']=='metadata_renderer')['runtime_bytes'],19499)
        with self.assertRaisesRegex(D.PlanError,'source_changed'):
            D.prepare(D.template(),build_profile=D.LEGACY_BUILD_PROFILE)

    def test_original_capture_reconciles_as_legacy_without_current_relabelling(self):
        result=M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')
        self.assertEqual(result['build_profile'],D.LEGACY_BUILD_PROFILE)
        self.assertEqual((result['receipts'],result['instances'],result['binding_observations']),(44,39,112))
        self.assertTrue(result['legacy_mutable_transaction_request_capture'])
        self.assertFalse(result['preflight_request_fields_verified_from_original_wire'])
        self.assertEqual(result['rpc_calls'],0)

    def test_deleted_binding_observation_cannot_pass(self):
        rows,wire,a,inputs,ledger=self.bindings_fixture()
        with self.assertRaisesRegex(ValueError,'binding observation'):M.check_bindings(rows[:-1],wire,a,inputs,ledger)

    def test_missing_expected_field_cannot_disable_derived_binding_check(self):
        rows,wire,a,inputs,ledger=self.bindings_fixture();del rows[0]['expected']
        with self.assertRaisesRegex(ValueError,'binding observation'):M.check_bindings(rows,wire,a,inputs,ledger)

    def test_self_consistent_wrong_expected_and_wire_value_is_rejected(self):
        rows,wire,a,inputs,ledger=self.bindings_fixture();row=rows[0];wrong='0x'+'0'*64
        row['actual']=row['expected']=wrong
        signature=row['signature'];payload=M.call(signature,('bytes32',),row['arguments'])
        for item in wire:
            if item['request']['method']=='eth_call'and item['request']['params'][0].get('data')==payload:
                item['response']['result']=wrong
        with self.assertRaisesRegex(ValueError,'Independent binding observation'):M.check_bindings(rows,wire,a,inputs,ledger)

    def test_unknown_or_mismatched_evidence_build_rejected_before_build_read(self):
        class Captured:
            def __init__(self,path):self.zip=None
            def obj(self,name):return records[name]
        tools={'scripts/rehearse-local-deployment.py':M.LEGACY_RUNNER}
        records={'RESULT.json':{'status':'controlled_local_constructor_and_binding_rehearsal_passed','chain_id':4663,'sealed':False,'release_ready':False,'production_approved':False},
          'source-stage.json':{'tool_sources_sha256':tools,'accepted_build_files_sha256':D.BUILD_PINS},
          'node/cleanup.json':{'owned_node_stopped':True,'pending_submission':None,'failure_type':None},
          'node/process.json':{'chain_id':4663,'port':61000,'pid':123,'minimal_environment':True,'size_limit_override':False,'command':['anvil.exe','--host','127.0.0.1','--accounts','0','--silent','--hardfork','cancun','--gas-limit','32000000']},
          'node/socket-ownership.json':[],'SOURCE_UNCHANGED.json':tools}
        for profile in ('unknown',D.DEFAULT_BUILD_PROFILE):
            records['source-stage.json']['accepted_build_profile']=profile
            with self.subTest(profile=profile),patch.object(M,'Evidence',Captured),patch.object(Path,'open',side_effect=AssertionError('No build read')):
                with self.assertRaises(ValueError):M.reconcile(Path('.'))

    def test_mislabelled_result_chain_rejected_before_build_read(self):
        original=M.Evidence
        class WrongChain(original):
            def obj(self,name):
                value=super().obj(name)
                if name.endswith('/RESULT.json'):value['chain_id']=1
                return value
        with patch.object(M,'Evidence',WrongChain):
            with self.assertRaisesRegex(ValueError,'chain scope'):
                M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')

    def test_legacy_capture_cannot_smuggle_current_result_build_label(self):
        original=M.Evidence
        class WrongLabel(original):
            def obj(self,name):
                value=super().obj(name)
                if name.endswith('/RESULT.json'):value['build_profile']=D.DEFAULT_BUILD_PROFILE
                return value
        with patch.object(M,'Evidence',WrongLabel):
            with self.assertRaisesRegex(ValueError,'mismatched result build profile'):
                M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')

    def test_unavailable_build_does_not_consume_rehearsal_output_folder(self):
        spec=importlib.util.spec_from_file_location('new_rehearsal_profile',D.ROOT/'scripts/rehearse-local-deployment.py')
        local=importlib.util.module_from_spec(spec);spec.loader.exec_module(local)
        with tempfile.TemporaryDirectory()as folder:
            output=Path(folder)/'new-owned-run'
            with patch.object(local.P,'Artifacts',side_effect=D.PlanError('source_changed')):
                with self.assertRaisesRegex(D.PlanError,'source_changed'):
                    local.main(['--anvil','unused-anvil.exe','--output',str(output)])
            self.assertFalse(output.exists())

    def test_rogue_rpc_mutation_cannot_hide_outside_counted_sends(self):
        original=M.Evidence
        class RogueMutation(original):
            def zipped_json(self,name):
                value,digest=super().zipped_json(name)
                if name.endswith('/rpc-records.json.gz'):
                    ordinal=len(value)+1
                    value.append({'request':{'jsonrpc':'2.0','id':ordinal,'method':'anvil_setCode','params':[]},
                                  'response':{'jsonrpc':'2.0','id':ordinal,'result':True}})
                return value,digest
        with patch.object(M,'Evidence',RogueMutation):
            with self.assertRaisesRegex(ValueError,'RPC method'):
                M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')

    def test_constructor_arguments_derive_from_validated_inputs_not_plan_rows(self):
        original=M.Evidence;sequencer='0x'+'99'*20
        class WrongArgument(original):
            def obj(self,name):
                value=super().obj(name)
                if name.endswith('/actual-address-input.json'):value['inputs']['sequencer']=sequencer
                if name.endswith('/offline-plan.json'):
                    value['inputs']['inputs']['sequencer']=sequencer
                    value['input_sha256']=M.sha(M.canonical(value['inputs']))
                    value.pop('manifest_sha256');value['manifest_sha256']=M.sha(M.canonical(value))
                return value
        with patch.object(M,'Evidence',WrongArgument):
            with self.assertRaisesRegex(ValueError,'Constructor argument'):
                M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')

    def test_wire_envelopes_and_additional_mutation_kinds_are_rejected(self):
        valid={'request':{'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]},
               'response':{'jsonrpc':'2.0','id':1,'result':'0x1237'}}
        M.check_wire([copy.deepcopy(valid)])
        for method in ('anvil_reset','anvil_setStorageAt','eth_sendRawTransaction','anvil_mine'):
            row=copy.deepcopy(valid);row['request']['method']=method
            with self.subTest(method=method),self.assertRaisesRegex(ValueError,'RPC method'):M.check_wire([row])
        for field,value in (('id',True),('id',1.0),('id','1'),('jsonrpc','1.0'),('params',{})):
            row=copy.deepcopy(valid);row['request'][field]=value
            with self.subTest(field=field,value=value),self.assertRaisesRegex(ValueError,'RPC envelope'):M.check_wire([row])
        for mutate in (lambda row:row['response'].update(id=2),lambda row:row['response'].update(error=None),lambda row:row['response'].pop('result')):
            row=copy.deepcopy(valid);mutate(row)
            with self.assertRaisesRegex(ValueError,'RPC envelope'):M.check_wire([row])
        with self.assertRaisesRegex(ValueError,'RPC envelope'):M.check_wire([copy.deepcopy(valid),copy.deepcopy(valid)])

    def test_send_request_cannot_disagree_with_captured_transaction_sender(self):
        original=M.Evidence
        class WrongSender(original):
            def zipped_json(self,name):
                value,digest=super().zipped_json(name)
                if name.endswith('/rpc-records.json.gz'):
                    next(row for row in value if row['request']['method']=='eth_sendTransaction')['request']['params'][0]['from']='0x'+'88'*20
                return value,digest
        with patch.object(M,'Evidence',WrongSender):
            with self.assertRaisesRegex(ValueError,'submission'):
                M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')

    def test_impersonation_must_name_exact_reviewed_constructor_sender(self):
        original=M.Evidence
        class WrongImpersonation(original):
            def zipped_json(self,name):
                value,digest=super().zipped_json(name)
                if name.endswith('/rpc-records.json.gz'):
                    next(row for row in value if row['request']['method']=='anvil_impersonateAccount')['request']['params']=['0x'+'88'*20]
                return value,digest
        with patch.object(M,'Evidence',WrongImpersonation):
            with self.assertRaisesRegex(ValueError,'impersonation'):
                M.reconcile(D.ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip')

    def test_submission_fields_quantities_and_creation_target_are_bound(self):
        _,wire,_,_,_=self.bindings_fixture()
        sends={row['response']['result']:row['request']['params'][0]for row in wire if row['request']['method']=='eth_sendTransaction'}
        transactions=[row['response']['result']for row in wire if row['request']['method']=='eth_getTransactionByHash']
        actual=next(tx for tx in transactions if tx['to']is None);request=sends[actual['hash']]
        M.check_submission(request,actual,None)
        changes=(('from','0x'+'88'*20),('to','0x'+'88'*20),('value','0x1'),('nonce','0x1'),('data','0x00'),
                 ('gas','0x1'),('gasPrice','0x1'),('nonce','0x00'),('nonce',0),('chainId','0x1237'))
        for field,value in changes:
            altered=copy.deepcopy(request);altered[field]=value
            with self.subTest(field=field,value=value),self.assertRaisesRegex(ValueError,'submission'):M.check_submission(altered,actual,None)
        actual=next(tx for tx in transactions if tx['to']is not None);request=sends[actual['hash']]
        M.check_submission(request,actual,actual['to'].lower())
        altered=copy.deepcopy(request);altered['to']='0x'+'88'*20
        with self.assertRaisesRegex(ValueError,'submission'):M.check_submission(altered,actual,actual['to'].lower())

    def test_inert_carrier_output_is_derived_from_trusted_ledger_bytes(self):
        ledger=b'\x60\x01'*12300
        for index,piece in enumerate((ledger[:24573],ledger[24573:])):
            role='royalty_data_part'+str(index);expected='0x'+(b'\x5f\x5f\xfd'+piece).hex()
            M.check_carrier_runtime(role,ledger,expected,expected)
            wrong='0x00'+expected[4:]
            with self.assertRaisesRegex(ValueError,'trusted ledger slice'):M.check_carrier_runtime(role,ledger,wrong,wrong)
            with self.assertRaisesRegex(ValueError,'trusted ledger slice'):M.check_carrier_runtime(role,ledger,expected,wrong)

    def test_submission_quantity_is_bounded_uint256_and_preserves_actual_wire(self):
        self.assertEqual(M.quantity('0x0'),0)
        self.assertEqual(M.quantity('0x'+'f'*64),(1<<256)-1)
        with self.assertRaisesRegex(ValueError,'quantity'):M.quantity('0x1'+'0'*64)
        _,wire,_,_,_=self.bindings_fixture();count=0
        for row in wire:
            if row['request']['method']=='eth_sendTransaction':
                for field in ('gas','value','nonce','gasPrice'):
                    self.assertEqual(M.quantity(row['request']['params'][0][field]),int(row['request']['params'][0][field],16));count+=1
        self.assertEqual(count,176)


if __name__=='__main__':unittest.main()
