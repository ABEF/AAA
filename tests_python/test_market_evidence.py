"""New offline market-evidence semantic checks. No network or archived code."""
from pathlib import Path
import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from zzz_ops.market_evidence import Archive, MAX_MEMBER, verify

R=Path(__file__).resolve().parents[1]
ORIGINAL=R/'reports/real-market-refresh-20261116/evidence.zip'


class MarketEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ORIGINAL) as archive:
            cls.original={name:archive.read(name) for name in archive.namelist()}

    @staticmethod
    def edit(files,name,path,value):
        obj=json.loads(files[name]);target=obj
        for key in path[:-1]:
            target=target[key]
        target[path[-1]]=value
        files[name]=json.dumps(obj,sort_keys=True,indent=2).encode()

    def bundle(self,directory,mutate=lambda files:None, *, add=None, rehash=True):
        files=dict(self.original);mutate(files)
        if rehash:
            manifest=json.loads(files['manifest.json'])
            for row in manifest['files']:
                raw=files[row['path']]
                row['bytes']=len(raw);row['sha256']=hashlib.sha256(raw).hexdigest()
            files['manifest.json']=json.dumps(manifest).encode()
        path=Path(directory)/'capture.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
            for name,raw in files.items():
                archive.writestr(name,raw)
            if add:
                for name,raw in add:
                    archive.writestr(name,raw)
        return path

    def rejected(self,mutate, *, add=None, rehash=True):
        with tempfile.TemporaryDirectory() as directory:
            path=self.bundle(directory,mutate,add=add,rehash=rehash)
            with self.assertRaises(ValueError):
                verify(path)

    def rejects_fields(self,name,cases):
        for path,value in cases:
            with self.subTest(path=path):
                self.rejected(lambda files:self.edit(files,name,path,value))

    def test_valid_frozen_capture_is_not_live_qualification(self):
        result=verify(ORIGINAL)
        self.assertEqual(result['status'],'PASS')
        self.assertFalse(result['production_approved'])
        self.assertFalse(result['deployable_configuration'])
        self.assertEqual(result['actual_read_responses'],39)
        self.assertEqual(result['known_pool_states'],95)
        self.assertEqual(result['quote_diagnostics'],6)
        self.assertEqual(result['network_calls'],0)

    def test_false_source_qualification_is_rejected_even_with_consistent_manifest(self):
        self.rejects_fields('RESULTS.json',[
            (['sources_qualified','independent_ZZZ_pair'],True),
            (['sources_qualified','independent_ETH_pair'],True),
            (['feeds','pyth','qualified'],True)])

    def test_pyth_age_agreement_confidence_and_qualification_are_derived(self):
        self.rejects_fields('RESULTS.json',[
            (['feeds','pyth','hard_86400_seconds_pass'],True),
            (['feeds','pyth','agreement_300bps_pass'],True),
            (['feeds','pyth','confidence_usd','decimal'],'0'),
            (['feeds','pyth','publish_time'],1794826624)])

    def test_chainlink_summary_cannot_invent_freshness_or_independence(self):
        self.rejects_fields('RESULTS.json',[
            (['feeds','chainlink','age_seconds'],0),
            (['feeds','chainlink','two_proxies_same_aggregator'],False),
            (['feeds','chainlink','usd','decimal'],'2000'),
            (['feeds','chainlink','max_age_policy_unapproved'],False)])

    def test_all_market_rows_counts_order_and_fee_screens_are_rebuilt(self):
        self.rejects_fields('RESULTS.json',[
            (['markets','active_reference_fee_only_count'],99),
            (['markets','all_bands',0,'strict_principal_fee_only_candidate'],True),
            (['markets','all_bands'],[]),
            (['markets','global_highest_or_ownership_or_depth_qualified'],True)])
        def reverse(files):
            obj=json.loads(files['RESULTS.json'])
            obj['markets']['active_by_rawL_not_TVL'].reverse()
            files['RESULTS.json']=json.dumps(obj).encode()
        self.rejected(reverse)

    def test_market_price_orientation_and_reference_overlap_are_derived(self):
        self.rejects_fields('RESULTS.json',[
            (['markets','active_by_rawL_not_TVL',0,'common_500bps_continuous_reference_possible'],True),
            (['markets','active_by_rawL_not_TVL',0,'price_ratio_to_selected','decimal'],'5.8119259565'),
            (['markets','all_bands',0,'combined_fee_pips_ZZZ_to_ETH'],0)])

    def test_each_successful_quote_floor_boolean_is_recomputed(self):
        self.rejects_fields('RESULTS.json',[
            (['quotes',0,'passes_analytic_3pct_swap_value_floor'],True),
            (['quotes',0,'passes_analytic_1pct_conversion_gross_floor'],True),
            (['quotes',0,'passes_analytic_1pct_additional_after_fee_floor'],True)])

    def test_quote_gas_amount_display_and_qualification_are_not_free_fields(self):
        self.rejects_fields('RESULTS.json',[
            (['quotes',0,'quoter_reported_gas'],1),
            (['quotes',0,'conditional_own_spot_gross_loss_bps','decimal'],'0'),
            (['quotes',0,'whole_operation_qualified'],True)])

    def test_candidate_cannot_invent_reviewed_feeds_routes_or_policy(self):
        self.rejects_fields('CANDIDATE_CONFIG.json',[
            (['eth_secondary'],'0x'+'11'*20),
            (['eth_primary_candidate','maxAge'],86400),
            (['reviewed_reference'],'0x'+'12'*32),
            (['reviewed_swap_routes'],[{'approved':True}])])

    def test_captured_policy_and_nominal_input_bounds_are_exact(self):
        self.rejects_fields('capture/CAPTURE.json',[
            (['safeguards_unchanged','source_agreement_bps'],500),
            (['quotes',0,'input_raw'],'1'),
            (['quotes',0,'gas_ceiling'],200000),
            (['quotes',4,'nominal_USD_from_single_ETH_round_only'],100)])

    def test_old_quote_and_source_detachment_regressions_stay_rejected(self):
        self.rejects_fields('capture/CAPTURE.json',[
            (['quotes'],[]),
            (['feeds','api3','observation'],'0x'+'0'*64),
            (['anchor','hash'],'0x'+'ab'*32)])

    def test_wrong_request_target_is_rejected_without_trusting_label(self):
        obj=json.loads(self.original['capture/RPC.json'])
        index=next(i for i,row in enumerate(obj['rows']) if row['label']=='chainlink.primary.round')
        self.rejects_fields('capture/RPC.json',[
            (['rows',index,'request','params',0,'to'],'0x'+'22'*20)])

    def test_bool_and_float_aliases_do_not_satisfy_exact_integer_or_false_fields(self):
        self.rejects_fields('RESULTS.json',[
            (['feeds','pyth','qualified'],0),
            (['markets','known_pool_count'],95.0),
            (['quotes',0,'passes_analytic_3pct_swap_value_floor'],1)])

    def test_duplicate_nonfinite_or_oversized_json_values_reject_before_semantics(self):
        for raw in (b'{"files":[],"files":[]}',b'{"files":NaN}',
            b'{"files":1e999}',b'{"schema":'+b'1'*79+b'}'):
            with self.subTest(raw=raw[:30]):
                def mutate(files):files['manifest.json']=raw
                self.rejected(mutate,rehash=False)

    def test_unsafe_zip_paths_symlinks_and_duplicates_are_rejected(self):
        for path in ('../outside','C:/outside','/outside','a\\outside','a//b'):
            with self.subTest(path=path):
                self.rejected(lambda files:None,add=[(path,b'x')])
        self.rejected(lambda files:None,add=[('RESULTS.json',b'{}')])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'symlink.zip'
            info=zipfile.ZipInfo('link');info.create_system=3
            info.external_attr=(0o120777<<16)
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr(info,b'/outside')
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                Archive(path)

    def test_manifest_must_cover_every_member_once_and_bind_bytes(self):
        self.rejected(lambda files:None,add=[('unlisted.json',b'{}')])
        def duplicate(files):
            obj=json.loads(files['manifest.json']);obj['files'].append(copy.deepcopy(obj['files'][0]))
            files['manifest.json']=json.dumps(obj).encode()
        self.rejected(duplicate)
        self.rejected(lambda files:self.edit(files,'RESULTS.json',['production_approved'],True),rehash=False)

    def test_archive_member_size_and_member_count_are_bounded(self):
        self.rejected(lambda files:None,add=[('large',b'x'*(MAX_MEMBER+1))])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'many.zip'
            with zipfile.ZipFile(path,'w') as archive:
                for index in range(513):archive.writestr(str(index),b'')
            with self.assertRaisesRegex(ValueError,'Unbounded'):
                Archive(path)

    def test_readable_sidecar_must_match_archive_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            path=self.bundle(directory)
            (Path(directory)/'RESULTS.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'sidecar'):
                verify(path)

    def test_discovery_scope_does_not_become_global_completeness(self):
        self.rejects_fields('discovery/RESULT.json',[
            (['global_inventory_complete'],True),
            (['range_start'],113296579),
            (['new_pool_keys'],['0x'+'22'*32])])

    def test_prior_provenance_cannot_be_rewritten_as_a_new_approval(self):
        self.rejects_fields('provenance/known95-Nov9.json',[
            ([0,'key',2],1)])

    def test_malformed_object_containers_fail_with_a_controlled_error(self):
        for name in ('capture/CAPTURE.json','RESULTS.json','CANDIDATE_CONFIG.json','capture/RPC.json'):
            with self.subTest(name=name):
                self.rejected(lambda files:files.__setitem__(name,b'[]'))
        self.rejects_fields('capture/CAPTURE.json',[(['runtimes'],[])])

    def test_corrupt_compressed_archive_fails_with_a_controlled_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'corrupt.zip'
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('manifest.json',b'x'*128)
            raw=bytearray(path.read_bytes())
            # Local header: 30 fixed bytes followed by name, then compressed data.
            raw[30+len('manifest.json')]=255
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'Invalid evidence ZIP'):
                verify(path)

    def test_cli_is_offline_and_never_relabels_failure_as_live_approval(self):
        import contextlib,importlib.util,io
        spec=importlib.util.spec_from_file_location('check_market_evidence',R/'scripts/check-market-evidence.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with (patch.object(cli,'verify',return_value={'status':'PASS','production_approved':False,
                'deployable_configuration':False,'network_calls':0}) as check,
                contextlib.redirect_stdout(io.StringIO()) as output):
            status=cli.main(['--evidence',str(ORIGINAL)])
        self.assertEqual(status,0);check.assert_called_once_with(ORIGINAL)
        self.assertFalse(json.loads(output.getvalue())['production_approved'])
        with (patch.object(cli,'verify',side_effect=ValueError('Detached summary')),
                contextlib.redirect_stdout(io.StringIO()) as output):
            status=cli.main(['--evidence',str(ORIGINAL)])
        self.assertEqual(status,1)
        self.assertFalse(json.loads(output.getvalue())['production_approved'])


if __name__=='__main__':
    unittest.main()
