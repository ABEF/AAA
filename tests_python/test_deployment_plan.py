"""NEW offline deployment preparation checks; no compiler, RPC or signing."""
from __future__ import annotations
import contextlib,copy,io,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from zzz_ops import deployment_plan as D


def complete_input():
    value=D.template()
    value['planned_addresses']={role:'0x'+f'{0x110000+i:040x}' for i,(role,_,_) in enumerate(D.TOP)}
    value['inputs'].update(governance='0x'+'a1'*20,keeper='0x'+'a2'*20,guardian='0x'+'a1'*20,
        mint_recipient='0x'+'a1'*20,sequencer=D.ZERO,**D.NATIVE,seadrop=D.SEADROP,
        seadrop_codehash=D.SEADROP_HASH,base_uri='ipfs://TEST-ONLY/é',buyback_maximum_trade_usd=str(10**24))
    return value

class DeploymentPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview=D.prepare(D.template());cls.complete=D.prepare(complete_input())
    def row(self,result,role):return next(row for row in result['instances'] if row['role']==role)
    def test_template_is_blocked_but_complete_source_bound_graph(self):
        result=self.preview
        self.assertEqual(result['counts'],{'top_level':25,'internal_helpers':12,'inert_data_children':2,'total_instances':39})
        self.assertEqual(result['status'],'blocked_preview_missing_inputs');self.assertFalse(result['ready_for_submission'])
        self.assertFalse(result['rpc_performed']);self.assertFalse(result['simulation_performed']);self.assertFalse(result['address_predictions_performed'])
        self.assertEqual(result['accepted_build']['normal_size_gates'],48)
    def test_complete_inputs_still_never_approve_or_verify_runtime(self):
        result=self.complete
        self.assertTrue(result['top_level_constructor_payloads_complete']);self.assertTrue(result['input_assignments_complete'])
        self.assertFalse(result['all_instance_constructor_payloads_complete']);self.assertFalse(result['production_approved'])
        self.assertFalse(result['binding_addresses_verified'])
        self.assertTrue(all(not row['runtime_is_actual_deployment_pin'] for row in result['instances']))
        self.assertTrue(all(not item['verified'] for item in result['qualification_evidence'].values()))
    def test_exact_static_oracle_arguments_no_selector_and_79_margin(self):
        row=self.row(self.complete,'oracle');access=complete_input()['planned_addresses']['access']
        self.assertEqual(row['constructor_arguments_hex'],'0x'+access[2:].rjust(64,'0')+'0'*64)
        self.assertEqual(row['constructor_argument_bytes'],64);self.assertEqual(row['full_initcode_bytes'],49073);self.assertEqual(row['initcode_margin'],79)
        self.assertEqual(len(bytes.fromhex(row['full_initcode_hex'][2:])),row['full_initcode_bytes'])
    def test_dynamic_utf8_constructor_has_exact_offsets(self):
        row=self.row(self.complete,'nft');raw=bytes.fromhex(row['constructor_arguments_hex'][2:]);uri=complete_input()['inputs']['base_uri'].encode()
        self.assertEqual(int.from_bytes(raw[32:64],'big'),96);self.assertEqual(int.from_bytes(raw[96:128],'big'),len(uri))
        self.assertEqual(raw[128:128+len(uri)],uri);self.assertEqual(len(raw),128+32*((len(uri)+31)//32))
    def test_ascii_uri_initcode_boundary(self):
        value=complete_input();value['inputs']['base_uri']='ipfs://'+'x'*(18240-7)
        row=self.row(D.prepare(value),'nft');self.assertEqual(row['full_initcode_bytes'],49141)
        value['inputs']['base_uri']+='x'
        with self.assertRaisesRegex(D.PlanError,'initcode_size_limit'):D.prepare(value)
    def test_multibyte_uri_uses_bytes_not_character_count(self):
        value=complete_input();value['inputs']['base_uri']='ipfs://'+'é'*9116+'x'
        self.assertEqual(self.row(D.prepare(value),'nft')['full_initcode_bytes'],49141)
        value['inputs']['base_uri']='ipfs://'+'é'*9117
        with self.assertRaisesRegex(D.PlanError,'initcode_size_limit'):D.prepare(value)
    def test_empty_uri_is_constructor_valid_but_explicit_release_gap(self):
        value=complete_input();value['inputs']['base_uri']='';result=D.prepare(value)
        self.assertTrue(result['top_level_constructor_payloads_complete']);self.assertFalse(result['ready_for_submission'])
        self.assertTrue(any('Empty metadata URI' in text for text in result['release_prerequisites']))
        value['inputs']['base_uri']='https://not-source-valid.invalid/'
        with self.assertRaisesRegex(D.PlanError,'invalid_uri'):D.prepare(value)
    def test_unknowns_are_not_filled_with_zero_and_fixed_lengths_remain_known(self):
        row=self.row(self.preview,'oracle');self.assertIsNone(row['constructor_arguments_hex']);self.assertEqual(row['full_initcode_bytes'],49073)
        self.assertFalse(row['constructor_payload_complete']);self.assertIsNone(self.row(self.preview,'nft')['full_initcode_bytes'])
        value=complete_input();value['inputs']['sequencer']=None
        self.assertIsNone(self.row(D.prepare(value),'oracle')['arguments'][1]['value'])
    def test_external_factory_children_and_getter_dependencies(self):
        for role in ('royalty_rewards','activation_assets'):
            row=self.row(self.complete,role);self.assertTrue(row['constructor_payload_complete']);self.assertIsNone(row['planned_address'])
            self.assertEqual(row['address_status'],'discover_actual_getter_no_nonce_prediction')
        for role in ('activation_entry','claim_router'):
            row=self.row(self.complete,role);self.assertFalse(row['constructor_payload_complete']);self.assertEqual(row['constructor_argument_bytes'],96)
            self.assertIsNone(row['full_initcode_hex']);self.assertTrue(any(ref.startswith('g:') for ref in row['unresolved_bindings']))
    def test_exact_data_parts_reconstruct_ledger_creation(self):
        first=self.row(self.complete,'royalty_data_part0');second=self.row(self.complete,'royalty_data_part1')
        a=bytes.fromhex(first['returned_runtime_hex'][2:]);b=bytes.fromhex(second['returned_runtime_hex'][2:]);ledger=self.row(self.complete,'royalty_rewards')
        self.assertEqual(a[:3],b'\x5f\x5f\xfd');self.assertEqual(b[:3],a[:3]);self.assertEqual((len(a),len(b)),(24576,952))
        self.assertEqual(D.sha(a[3:]+b[3:]),ledger['creation_object_sha256']);self.assertEqual(ledger['full_initcode_bytes'],25554)
        self.assertEqual((first['full_initcode_bytes'],second['full_initcode_bytes']),(25095,1479))
    def test_binding_order_has_all_modules_policy_helpers_and_required_edges(self):
        steps=self.complete['construction_order'];seen=set()
        for step in steps:self.assertTrue(set(step['requires'])<=seen);seen.add(step['id'])
        module=[step for step in steps if step['kind']=='bootstrap_module_binding'];self.assertEqual(len(module),16)
        self.assertEqual({step['role'] for step in module},set(D.MODULES))
        for step in module:self.assertEqual(step['module_id'],'0x'+D.keccak256(next(name for role,name,_ in D.TOP if role==step['role']).encode()).hex())
        self.assertIn('bind:vault',next(s for s in steps if s['id']=='create:vault_canonical')['requires'])
        self.assertIn('bind:protocol_policy',next(s for s in steps if s['id']=='create:vault')['requires'])
        self.assertIn('configure:fixed_zzz',next(s for s in steps if s['id']=='configure:execution_sources')['requires'])
        self.assertIn('bind:lp_converter',seen);self.assertIn('bind:seadrop_mint',seen);self.assertFalse(any('seal' in s['id'] for s in steps))
    def test_nullable_unused_address_does_not_turn_preview_into_complete_input(self):
        value=complete_input();value['planned_addresses']['compounder']=None;result=D.prepare(value)
        self.assertTrue(result['top_level_constructor_payloads_complete']);self.assertFalse(result['input_assignments_complete'])
        self.assertEqual(result['status'],'blocked_preview_missing_inputs')
    def test_strict_schema_profile_native_and_numeric_inputs(self):
        variants=[]
        v=complete_input();v['rpc']='https://secret.invalid';variants.append(v)
        v=complete_input();v['chain_id']='31337';variants.append(v)
        v=complete_input();v['profile']='historical LP2';variants.append(v)
        v=complete_input();v['inputs']['pool_manager']='0x'+'23'*20;variants.append(v)
        v=complete_input();v['inputs']['buyback_maximum_trade_usd']=True;variants.append(v)
        v=complete_input();v['inputs']['buyback_maximum_trade_usd']=str(1<<128);variants.append(v)
        v=complete_input();v['inputs']['base_uri']='ipfs://\ud800';variants.append(v)
        for value in variants:
            with self.subTest(value=str(value)[:50]),self.assertRaises(D.PlanError):D.prepare(value)
    def test_duplicates_and_invalid_payees_rejected_authority_reuse_allowed(self):
        self.assertEqual(D.validate(complete_input())['inputs']['guardian'],complete_input()['inputs']['governance'])
        value=complete_input();value['planned_addresses']['nft']=value['planned_addresses']['vault']
        with self.assertRaisesRegex(D.PlanError,'duplicate_planned'):D.prepare(value)
        value=complete_input();value['inputs']['mint_recipient']=value['planned_addresses']['rewards']
        with self.assertRaisesRegex(D.PlanError,'excluded_mint_recipient'):D.prepare(value)
    def test_bounded_duplicate_json_and_unsupported_codec(self):
        for raw in (b'{"schema":1,"schema":1}',b'{"x":1.1}',b'{"x":NaN}',b' '* (D.MAX_INPUT+1)):
            with self.assertRaises(D.PlanError):D.decode(raw)
        with self.assertRaises(D.PlanError):D.encode_constructor(('address[]',),([],))
    def test_build_and_source_changes_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix='popl-deployment-test-') as folder:
            root=Path(folder).resolve();build=root/D.BUILD;build.mkdir(parents=True)
            for name in D.BUILD_PINS:shutil.copy2(D.ROOT/D.BUILD/name,build/name)
            manifest=json.loads((build/'source-manifest.json').read_bytes())
            for name in manifest['exact_source_sha256']:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D.ROOT/name,target)
            (root/'src/ZZZNFT.sol').write_bytes(b'changed')
            with self.assertRaisesRegex(D.PlanError,'source_changed'):D.prepare(complete_input(),root)
            path=build/'compiler-output.json.gz';path.write_bytes(path.read_bytes()+b'x')
            with self.assertRaisesRegex(D.PlanError,'accepted_build_changed'):D.prepare(complete_input(),root)
    def test_deterministic_complete_output_and_no_network(self):
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):again=D.prepare(complete_input())
        self.assertEqual(D.render(again),D.render(self.complete));self.assertEqual(again['manifest_sha256'],self.complete['manifest_sha256'])
    def cli(self,input_value,output,extra=()):
        source=output.parent/'input.json';source.write_bytes(D.canonical(input_value));stdout=io.StringIO();stderr=io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):code=D.main(['--input',str(source),'--output',str(output),*extra])
        return code,stdout.getvalue(),stderr.getvalue()
    def test_actual_cli_template_exit2_and_complete_exit0_are_never_ready(self):
        with tempfile.TemporaryDirectory(prefix='popl-deployment-cli-') as folder:
            root=Path(folder);code,out,err=self.cli(D.template(),root/'preview.json');self.assertEqual(code,2);self.assertEqual(err,'');self.assertFalse(json.loads(out)['ready_for_submission'])
            code,out,err=self.cli(complete_input(),root/'complete.json');self.assertEqual(code,0);self.assertEqual(err,'');self.assertFalse(json.loads((root/'complete.json').read_bytes())['ready_for_submission'])
    def test_cli_existing_path_preserved_before_loading_invalid_input(self):
        with tempfile.TemporaryDirectory(prefix='popl-deployment-preserve-') as folder:
            root=Path(folder);out=root/'existing.json';out.write_bytes(b'original');stderr=io.StringIO()
            with contextlib.redirect_stderr(stderr):code=D.main(['--input',str(root/'missing-secret.json'),'--output',str(out)])
            self.assertEqual(code,1);self.assertEqual(out.read_bytes(),b'original');error=json.loads(stderr.getvalue())
            self.assertEqual(error['reason'],'existing_output_preserved');self.assertTrue(error['output_may_exist']);self.assertNotIn('secret',stderr.getvalue())
    def test_publication_failure_is_uncertain_and_never_replaces_existing_file(self):
        with tempfile.TemporaryDirectory(prefix='popl-deployment-publish-') as folder:
            root=Path(folder);out=root/'result.json'
            def uncertain(path,raw):Path(path).write_bytes(raw);raise OSError('secret transport')
            with patch.object(D,'write_exclusive',side_effect=uncertain):code,_,err=self.cli(complete_input(),out)
            self.assertEqual(code,1);self.assertTrue(json.loads(err)['output_may_exist']);self.assertEqual(json.loads(err)['reason'],'publication_uncertain')
            self.assertNotIn('secret',err);self.assertTrue(out.is_file())
            with self.assertRaises(FileExistsError):D.write_exclusive(out,b'replacement')
    def test_dangling_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix='popl-deployment-link-') as folder:
            root=Path(folder);out=root/'dangling.json'
            try:os.symlink(root/'absent',out)
            except OSError as exc:self.skipTest('Local symlink creation unavailable: '+str(type(exc).__name__))
            stderr=io.StringIO()
            with contextlib.redirect_stderr(stderr):code=D.main(['--input',str(root/'absent-input'),'--output',str(out)])
            self.assertEqual(code,1);self.assertTrue(out.is_symlink());self.assertEqual(json.loads(stderr.getvalue())['reason'],'existing_output_preserved')

    def test_checked_in_sample_matches_exact_nullable_template(self):
        source=D.ROOT/'config/deployment-preparation.example.json'
        self.assertEqual(json.loads(source.read_bytes()),D.template())

if __name__=='__main__':unittest.main()
