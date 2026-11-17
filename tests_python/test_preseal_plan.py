"""New current-build pre-seal composition checks; no old test methods run."""
import copy
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops import deployment_plan as D, preseal_plan as P
from tests_python import preseal_fixture as F


class PresealPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory(prefix='popl-new-preseal-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.value=F.complete(Path(cls.temporary.name))
        cls.plan=P.prepare(copy.deepcopy(cls.value))
        cls.preview=P.prepare(P.example())

    def prepare(self,value=None): return P.prepare(copy.deepcopy(self.value if value is None else value))
    def row(self,plan,name): return next(r for r in plan['steps'] if r['id']=='configure:'+name)
    def rejected(self,value):
        with self.assertRaises(D.PlanError):P.prepare(value)

    def test_complete_current_build_produces_only_conditional_typed_bootstrap_calls(self):
        p=self.plan
        self.assertTrue(p['configuration_inputs_complete'])
        self.assertEqual('complete_unsigned_preseal_review_pending_live_verification',p['status'])
        self.assertEqual(12,len(p['steps']));self.assertEqual(24,sum(len(r['calls']) for r in p['steps']))
        self.assertTrue(all(not p[k] for k in P.FALSE_FLAGS));self.assertTrue(p['offline_only'])
        for step in p['steps']:
            self.assertTrue(step['inputs_prepared']);self.assertFalse(step['live_preconditions_verified'])
            for call in step['calls']:
                self.assertEqual(self.value['bootstrap'],call['from']);self.assertEqual('0',call['value'])
                self.assertFalse(call['authority_verified']);self.assertTrue(call['calldata'].startswith('0x'))
                self.assertNotIn('seal',call['function'].lower())

    def test_all_unknown_inputs_remain_blocked_and_unfilled(self):
        p=self.preview
        self.assertFalse(p['configuration_inputs_complete']);self.assertTrue(p['missing_inputs'])
        self.assertTrue(all(not r['inputs_prepared'] for r in p['steps']))
        self.assertIsNone(p['bootstrap'])
        self.assertTrue(all(c['calldata'] is None for r in p['steps'] for c in r['calls']))
        self.assertEqual(P.example(),P.validate(P.example()))

    def test_empty_constructor_root_requires_explicit_setup_in_both_unsigned_plans(self):
        v=copy.deepcopy(self.value)
        v['constructor_input']['inputs']['base_uri']=''
        construction=D.prepare(copy.deepcopy(v['constructor_input']))
        self.assertTrue(any('Access.seal rejects' in r and 'NFT.setBaseURI' in r
                            for r in construction['release_prerequisites']))
        plan=self.prepare(v)
        self.assertTrue(any('NFT.artworkBaseURI' in r and 'NFT.setBaseURI' in r
                            for r in plan['release_prerequisites']))
        self.assertFalse(plan['production_approved'])
        self.assertFalse(plan['onchain_snapshot_verified'])
        functions=[c['function'] for row in plan['steps'] for c in row['calls']]
        self.assertFalse(any('seal' in f.lower() or 'setbaseuri' in f.lower() for f in functions))

    def test_preparation_never_mutates_inputs_or_claims_factory_discovery(self):
        v=copy.deepcopy(self.value);before=copy.deepcopy(v);p=P.prepare(v)
        self.assertEqual(before,v);self.assertIn('no CREATE/factory prediction',p['address_scope'])
        self.assertTrue(all(not p[k] for k in ('binding_addresses_verified','target_runtime_verified','onchain_snapshot_verified')))

    def test_missing_fixed_token_blocks_dependants_without_blocking_unrelated_terms(self):
        v=copy.deepcopy(self.value);v['settings']['fixed_zzz']=None;p=self.prepare(v)
        self.assertTrue(self.row(p,'dual_usd')['inputs_prepared'])
        for name in ('fixed_zzz','lp_asset','migration_zzz','execution_sources','native_pools','routes'):
            self.assertFalse(self.row(p,name)['inputs_prepared'])
            self.assertTrue(all(c['calldata'] is None for c in self.row(p,name)['calls']))
        self.assertTrue(self.row(p,'seadrop_terms')['inputs_prepared'])

    def test_complete_upstream_with_unknown_terms_stays_blocked_instead_of_dereferencing_unknown(self):
        v=copy.deepcopy(self.value);v['settings']['seadrop_terms']=None;p=self.prepare(v)
        self.assertFalse(self.row(p,'seadrop_upstream')['inputs_prepared'])
        self.assertFalse(self.row(p,'mint_end')['inputs_prepared'])
        self.assertFalse(p['configuration_inputs_complete'])

    def test_unknown_nested_values_block_and_do_not_become_zero(self):
        for group,path in [('dual_usd',('zzz','primary','source')),('randomness',('subscriptionId',)),
                           ('native_pools',('pools',0,'config','rangeBps'))]:
            v=copy.deepcopy(self.value);node=v['settings'][group]
            for key in path[:-1]:node=node[key]
            node[path[-1]]=None;p=self.prepare(v)
            self.assertFalse(self.row(p,group)['inputs_prepared'])
            self.assertTrue(all(c['calldata'] is None for c in self.row(p,group)['calls']))

    def test_bootstrap_is_explicit_not_inferred_from_governance(self):
        v=copy.deepcopy(self.value);v['bootstrap']=None;p=self.prepare(v)
        self.assertTrue(all(not r['inputs_prepared'] for r in p['steps']))
        self.assertTrue(all(c['from'] is None and c['calldata'] is None for r in p['steps'] for c in r['calls']))

    def test_helper_targets_must_be_supplied_and_collisions_reject(self):
        v=copy.deepcopy(self.value);v['child_addresses']['activation_assets']=None;p=self.prepare(v)
        self.assertFalse(self.row(p,'fixed_zzz')['inputs_prepared'])
        for target in (v['constructor_input']['planned_addresses']['vault'],v['bootstrap'],D.NATIVE['zzz']):
            bad=copy.deepcopy(self.value);bad['child_addresses']['activation_assets']=target;self.rejected(bad)

    def test_fixed_zzz_code_pins_cannot_diverge_between_configurations(self):
        for name,field in [('migration_zzz','codeHash'),('fixed_zzz','expectedCodeHash')]:
            v=copy.deepcopy(self.value);v['settings'][name][field]=F.code(999);self.rejected(v)
        v=copy.deepcopy(self.value);v['settings']['routes']['conversion_routes'][0]['sourceCodeHash']=F.code(998);self.rejected(v)

    def test_two_source_identity_age_decimals_and_disagreement_bounds_are_retained(self):
        for mutate in ('same_source','same_independence','age0','age_over','decimals_over','spread_over','zero_review'):
            v=copy.deepcopy(self.value);p=v['settings']['dual_usd']['zzz']
            if mutate=='same_source':p['secondary']['source']=p['primary']['source']
            elif mutate=='same_independence':p['secondary']['independenceId']=p['primary']['independenceId']
            elif mutate=='age0':p['primary']['maxAge']='0'
            elif mutate=='age_over':p['primary']['maxAge']='86401'
            elif mutate=='decimals_over':p['primary']['feedDecimals']='19'
            elif mutate=='spread_over':p['maxDeviationBps']='501'
            else:p['reviewHash']='0x'+'0'*64
            with self.subTest(mutate=mutate):self.rejected(v)

    def test_execution_sources_must_match_exact_admitted_zzz_source_and_pin(self):
        for field,value in [('source',F.addr(88)),('expectedCodeHash',F.code(88))]:
            v=copy.deepcopy(self.value);v['settings']['execution_sources']['sources'][0][field]=value;self.rejected(v)
        v=copy.deepcopy(self.value);v['settings']['execution_sources']['sources']*=2;self.rejected(v)

    def test_known_execution_composite_source_requires_18_feed_decimals(self):
        v=copy.deepcopy(self.value);v['settings']['dual_usd']['zzz']['primary']['feedDecimals']='8'
        self.rejected(v)

    def test_known_native_code_pins_cannot_conflict_with_registry_constants(self):
        for field in ('zzz','poolManagerCodeHash','stateViewCodeHash'):
            v=copy.deepcopy(self.value)
            if field=='zzz':
                v['settings']['fixed_zzz']['expectedCodeHash']=F.code(11)
                v['settings']['migration_zzz']['codeHash']=F.code(11)
                v['settings']['routes']['conversion_routes'][0]['sourceCodeHash']=F.code(11)
            else:v['settings']['routes']['conversion_routes'][0][field]=F.code(15)
            with self.subTest(field=field):self.rejected(v)

    def test_declared_feed_and_coordinator_cannot_alias_known_protocol_implementations(self):
        for role in ('vault','activation_assets'):
            for field in ('feed','coordinator'):
                v=copy.deepcopy(self.value)
                known=v['constructor_input']['planned_addresses'].get(role,v['child_addresses'].get(role))
                if field=='feed':v['settings']['dual_usd']['eth']['primary']['source']=known
                else:v['settings']['randomness']['coordinator']=known
                with self.subTest(role=role,field=field):self.rejected(v)

    def test_pool_configuration_precedes_human_price_orientation_and_routes(self):
        calls=self.row(self.plan,'native_pools')['calls']
        self.assertEqual(['configureNative','setRangeOrientation']*2,[c['function'] for c in calls])
        self.assertEqual([F.pool_id(x['config']['key']) for x in self.value['settings']['native_pools']['pools']],self.plan['pool_ids'])
        self.assertTrue(all(c['arguments'][1]['value']=='1' for c in calls if c['function']=='setRangeOrientation'))
        self.assertIn('configure:native_pools',self.row(self.plan,'routes')['requires'])

    def test_pool_identity_hook_duplicate_and_one_contribution_destination_guards(self):
        for mutate in ('hook','pair','fee','spacing','wrong_launch','two_deposits','duplicate'):
            v=copy.deepcopy(self.value);rows=v['settings']['native_pools']['pools'];p=rows[0]['config']
            if mutate=='hook':p['key']['hooks']=F.addr(88)
            elif mutate=='pair':p['key']['currency1']=F.addr(88)
            elif mutate=='fee':p['key']['fee']='100001'
            elif mutate=='spacing':p['key']['tickSpacing']='-1'
            elif mutate=='wrong_launch':p['key']['fee']='3000'
            elif mutate=='two_deposits':rows[1]['config']['depositsEnabled']=True
            else:rows.append(copy.deepcopy(rows[0]))
            with self.subTest(mutate=mutate):self.rejected(v)

    def test_pool_geometry_cooldown_fee_budget_and_position_caps_are_checked(self):
        for field,value in [('rangeBps','99'),('triggerBps','5000'),('maxSpotDeviationBps','501'),
                            ('maxSlippageBps','1001'),('maxSlippageBps','100'),
                            ('minRebalanceInterval','599'),('minRebalanceInterval','604801'),
                            ('minDepositUSD','0'),('maxPositionUSD','1')]:
            v=copy.deepcopy(self.value);v['settings']['native_pools']['pools'][0]['config'][field]=value
            with self.subTest(field=field,value=value):self.rejected(v)

    def test_routes_remain_bounded_native_fixed_pair_and_admitted_execution_venues(self):
        for mutate in ('foreign_execution','duplicate_execution','foreign_source','weth_output','bad_nativehash','wrong_core','no_route_enabled'):
            v=copy.deepcopy(self.value);r=v['settings']['routes'];p=r['conversion_routes'][0]
            if mutate=='foreign_execution':r['execution_pool_ids']=[F.code(100)]
            elif mutate=='duplicate_execution':r['execution_pool_ids']*=2
            elif mutate=='foreign_source':p['source']=F.addr(100)
            elif mutate=='weth_output':p['output']=F.addr(101)
            elif mutate=='bad_nativehash':p['outputCodeHash']=F.code(102)
            elif mutate=='wrong_core':p['poolManager']=F.addr(103)
            else:r['conversion_routes']=[]
            with self.subTest(mutate=mutate):self.rejected(v)

    def test_explicit_empty_routes_and_disabled_conversion_are_not_unknown_or_fallback(self):
        v=copy.deepcopy(self.value);v['settings']['routes'].update(execution_pool_ids=[],conversion_routes=[],conversion_enabled=False)
        p=self.prepare(v);r=self.row(p,'routes');self.assertTrue(r['inputs_prepared'])
        self.assertEqual(['configureExecutionPools','setEnabled'],[c['function'] for c in r['calls']])
        self.assertEqual([],r['calls'][0]['arguments'][0]['value']);self.assertFalse(r['calls'][1]['arguments'][0]['value'])
        self.assertTrue(any('Empty execution lists disable swaps' in x for x in p['release_prerequisites']))

    def test_confirmation_keeps_reference_guard_and_distinguishes_stopped_gap(self):
        v=copy.deepcopy(self.value);v['settings']['confirmation']['requireReferenceExit']=False;self.rejected(v)
        v=copy.deepcopy(self.value);v['settings']['confirmation']['maximumGap']='301';self.rejected(v)
        v=copy.deepcopy(self.value);v['settings']['confirmation']['maximumGap']='0';p=self.prepare(v)
        self.assertTrue(self.row(p,'confirmation')['inputs_prepared'])
        self.assertTrue(any('gap0 stops confirmation' in x for x in p['release_prerequisites']))

    def test_vrf_bounds_are_initial_setup_not_rotation_or_pending_reroll(self):
        for field,value in [('subscriptionId','0'),('confirmations','2'),('confirmations','201'),
                            ('callbackGas','199999'),('callbackGas','10000001')]:
            v=copy.deepcopy(self.value);v['settings']['randomness'][field]=value;self.rejected(v)
        call=self.row(self.plan,'randomness')['calls'][0]
        self.assertEqual('configureRandomness',call['function']);self.assertEqual(8,len(call['arguments']))

    def test_drop_artifact_digest_source_identity_and_expected_price_are_checked(self):
        v=copy.deepcopy(self.value);v['settings']['seadrop_terms']['artifact_sha256']='a'*64;self.rejected(v)
        v=copy.deepcopy(self.value);v['constructor_input']['planned_addresses']['nft']=F.addr(999);self.rejected(v)
        info=self.plan['seadrop_manifest'];self.assertTrue(info['source_bindings_verified_offline'])
        self.assertFalse(info['onchain_settings_verified'])
        self.assertNotIn(str(Path(self.value['settings']['seadrop_terms']['artifact_path']).parent),json.dumps(self.plan))

    def test_upstream_setters_target_nft_with_fixed_seadrop_not_external_admin(self):
        p=self.row(self.plan,'seadrop_upstream')
        self.assertEqual(6,len(p['calls']))
        for c in p['calls']:
            self.assertEqual(self.value['constructor_input']['planned_addresses']['nft'],c['to'])
            self.assertEqual(D.SEADROP,c['arguments'][0]['value'])
        for field in ('existingFeeRecipients','existingPayers','existingSigners','existingTokenGated'):
            v=copy.deepcopy(self.value);v['settings']['seadrop_upstream'][field]=[F.addr(100)];self.rejected(v)

    def test_mint_end_aligns_with_proof_window_and_does_not_claim_live_future_timestamp(self):
        v=copy.deepcopy(self.value);v['settings']['mint_end']['end']='398';self.rejected(v)
        call=self.row(self.plan,'mint_end')['calls'][0];self.assertEqual('setMintEnd',call['function'])
        self.assertEqual('399',call['arguments'][0]['value'])
        self.assertFalse(self.plan['onchain_snapshot_verified'])

    def test_strict_object_types_integer_strings_and_array_limits_reject(self):
        for mutate in ('extra','schema_bool','chain_number','integer_number','leading_zero','boolean_number','too_many_pools'):
            v=copy.deepcopy(self.value)
            if mutate=='extra':v['arbitrary_calldata']='0x1234'
            elif mutate=='schema_bool':v['schema']=True
            elif mutate=='chain_number':v['chain_id']=4663
            elif mutate=='integer_number':v['settings']['randomness']['subscriptionId']=1
            elif mutate=='leading_zero':v['settings']['randomness']['subscriptionId']='01'
            elif mutate=='boolean_number':v['settings']['randomness']['nativePayment']=1
            else:v['settings']['native_pools']['pools']*=3
            with self.subTest(mutate=mutate):self.rejected(v)

    def test_historical_build_and_source_or_artifact_drift_do_not_fall_back(self):
        with self.assertRaises(D.PlanError):P.prepare(self.value,build_profile=D.LEGACY_BUILD_PROFILE)
        with patch.object(D.Artifacts,'check_sources',side_effect=D.PlanError('source_changed')):
            with self.assertRaisesRegex(D.PlanError,'source_changed'):self.prepare()
        with patch.object(D,'trusted_build',side_effect=D.PlanError('unknown_build_profile')):
            with self.assertRaises(D.PlanError):self.prepare()

    def test_no_network_call_or_false_release_approval_is_needed_for_complete_review(self):
        with patch.object(socket.socket,'connect',side_effect=AssertionError('Network forbidden')):
            p=self.prepare()
        self.assertTrue(p['configuration_inputs_complete']);self.assertTrue(all(p[k] is False for k in P.FALSE_FLAGS))
        calculated=copy.deepcopy(p);digest=calculated.pop('manifest_sha256')
        self.assertEqual(hashlib.sha256(D.canonical(calculated)).hexdigest(),digest)


if __name__=='__main__':unittest.main()
