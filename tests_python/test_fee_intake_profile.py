"""Offline profile/codec isolation, not live deployment qualification."""
import copy
import unittest
from unittest.mock import patch

from zzz_ops import production_v2 as P
from zzz_ops import production_observer as O
from tests_python.fee_intake_fixtures import lp_only_fixture
from tests_python import test_production_v2 as F
from tests_python.test_production_observer import CompositionRPC, RUNTIME, encoded, selector


class FeeIntakeProfileTests(unittest.TestCase):
    def report(self, config):
        return P.validate(config,now=F.NOW)

    def test_lp_only_profile_requires_exact_helper_and_controller_inventory(self):
        config=lp_only_fixture(F.fixture())
        result=self.report(config)
        self.assertTrue(result['ready'],result['issues'])
        self.assertEqual(1,result['fee_intake_version'])
        self.assertFalse(result['production_qualification_supported'])
        self.assertFalse(result['deployment_authorized'])
        expected=P.expected_bindings(config['chains'][0],fee_intake_version=1)
        self.assertEqual(15,len(expected['helpers']))
        self.assertIn('activation_assets_factory',expected['helpers'])
        self.assertNotIn('reward_receiver_factory',expected['helpers'])
        self.assertEqual({'access','FEE_INTAKE_VERSION'},set(expected['modules']['fees']))
        self.assertEqual(1,expected['modules']['fees']['FEE_INTAKE_VERSION'])
        self.assertEqual(2,expected['modules']['migration']['CUSTODY_VERSION'])

    def test_legacy_absent_and_zero_keep_original_helpers_and_codec(self):
        for explicit in (False,True):
            config=F.fixture()
            if explicit:config['fee_intake_version']=0
            result=self.report(config)
            self.assertTrue(result['ready'],result['issues'])
            self.assertFalse(result['production_qualification_supported'])
            expected=P.expected_bindings(config['chains'][0])
            self.assertEqual(15,len(expected['helpers']))
            self.assertIn('receiverFactory',expected['modules']['fees'])
            self.assertNotIn('FEE_INTAKE_VERSION',expected['modules']['fees'])
            self.assertEqual(P.CANONICAL_SCHEMA,expected['modules']['canonical']['SCHEMA'])

    def test_old_and_new_snapshots_are_not_reinterpreted_in_either_direction(self):
        for base,new_version in ((F.fixture(),1),(lp_only_fixture(F.fixture()),0)):
            config=copy.deepcopy(base);config['fee_intake_version']=new_version
            result=self.report(config)
            self.assertFalse(result['ready'])
            codes={i['code'] for i in result['issues']}
            self.assertIn('native.profile',codes)
            self.assertIn('binding.observed',codes)
            self.assertIn('schema.keys',codes)
        self.assertNotEqual(P.CANONICAL_SCHEMA,P.LP_ONLY_CANONICAL_SCHEMA)

    def test_lp_only_profile_rejects_extra_factory_and_legacy_getter_claims(self):
        for mutation in ('factory','getters'):
            config=lp_only_fixture(F.fixture());chain=config['chains'][0]
            old=F.fixture()['chains'][0]
            if mutation=='factory':
                chain['helpers']['reward_receiver_factory']=old['helpers']['reward_receiver_factory']
            else:
                chain['modules']['fees']['observed_bindings'].update(receiverFactory=F.addr(9900),rewardReceiverCount=0)
            self.assertFalse(self.report(config)['ready'])

    def test_controller_version_missing_wrong_or_boolean_never_qualifies(self):
        for value in (None,0,True,'1',2):
            config=lp_only_fixture(F.fixture())
            values=config['chains'][0]['modules']['fees']['observed_bindings']
            if value is None:values.pop('FEE_INTAKE_VERSION')
            else:values['FEE_INTAKE_VERSION']=value
            self.assertFalse(self.report(config)['ready'])

    def test_unsupported_profile_is_rejected_without_inference(self):
        for value in (True,False,'1',None,2,-1):
            config=lp_only_fixture(F.fixture());config['fee_intake_version']=value
            result=self.report(config)
            self.assertIn('fees.profile',{i['code'] for i in result['issues']})
            self.assertFalse(result['production_qualification_supported'])
            rpc=CompositionRPC(F.fixture())
            with self.assertRaisesRegex(ValueError,'fee-intake'):
                O.observe(config,rpc)
            self.assertEqual([],rpc.calls)
            with self.assertRaises(ValueError):P.expected_bindings(config['chains'][0],fee_intake_version=value)

    def test_lp_only_manifest_requires_actual_local_only_custody_version(self):
        for value in (None,1,True,'2',3):
            config=lp_only_fixture(F.fixture())
            values=config['chains'][0]['modules']['migration']['observed_bindings']
            if value is None:values.pop('CUSTODY_VERSION')
            else:values['CUSTODY_VERSION']=value
            result=self.report(config)
            self.assertFalse(result['ready'])
            self.assertIn('binding.observed',{i['code'] for i in result['issues']})

    def test_source_policy_version_and_reviewed_zzz_identity_are_required(self):
        for field,value in (('SOURCE_POLICY_VERSION',0),('SOURCE_POLICY_VERSION',True),('zzz',F.addr(99999))):
            config=lp_only_fixture(F.fixture())
            config['chains'][0]['helpers']['activation_assets']['observed_bindings'][field]=value
            self.assertFalse(self.report(config)['ready'])

    def test_fixed_zzz_identity_requires_matching_exit_target_and_code_pin(self):
        for field,value in (('currentZZZ',P.ZERO),('currentZZZ',F.addr(99999)),
                ('zzzCodeHash',P.ZERO_HASH),('zzzCodeHash','0x'+'77'*32)):
            config=lp_only_fixture(F.fixture());chain=config['chains'][0]
            chain['modules']['migration']['observed_bindings'][field]=value
            result=self.report(config)
            self.assertFalse(result['ready'])
            self.assertIn('binding.observed',{i['code'] for i in result['issues']})
        config=lp_only_fixture(F.fixture());chain=config['chains'][0]
        self.assertEqual(chain['modules']['migration']['observed_bindings']['currentZZZ'],
            chain['helpers']['activation_assets']['observed_bindings']['zzz'])

    def test_valid_third_source_remains_historical_but_cannot_extend_current_contributions(self):
        chain=lp_only_fixture(F.fixture())['chains'][0]
        third=F.addr(99999);tokens={t['address']:t for t in chain['tokens']}
        tokens[third]={'runtime_hash':F.HASH,'decimals':18}
        route=copy.deepcopy(chain['conversion_routes'][0]);route['role']='entry';route['source_asset']=third
        policy=route['policy'];policy.update(source=third,currency1=third,sourceCodeHash=F.HASH)
        parent=chain['helpers']['activation_entry']['address'];executor=chain['helpers']['entry_v4_executor']['address']
        rid=P.identity([(P.V4_DOMAIN,'bytes32'),(4663,'uint256'),(executor,'address'),(parent,'address')]+
            [(policy[k],typ) for k,typ in P.V4_FIELDS])
        route.update(route_id=rid,observed_policy=dict(policy))
        route['venue_observation']['pool_id']=P.identity([(policy[k],typ) for k,typ in
            (('currency0','address'),('currency1','address'),('fee','uint24'),('tickSpacing','uint24'),('hooks','address'))])
        route['execution_evidence'].update(parent=parent,executor=executor,route_id=rid,source_asset=third)
        chain['conversion_routes'].append(route)
        source=copy.deepcopy(chain['activation_sources'][1]);ap=source['asset_policy']
        ap.update(token=third,expectedCodeHash=F.HASH)
        fields=(('token','address'),('enabled','bool'),('expectedCodeHash','bytes32'),
            ('reviewHash','bytes32'),('decimals','uint8'),('poolAdmission','bool'))
        pid=P.identity([(chain['helpers']['activation_assets']['address'],'address'),(2,'uint256')]+[(ap[k],typ) for k,typ in fields])
        source.update(source_asset=third,route_kind=2,route_id=rid,asset_policy_ordinal=2,
            asset_policy_id=pid,observed_asset_policy=dict(ap),observed_asset_policy_id=pid,
            observed_asset_policy_ordinal_id=pid,observed_asset_policy_count=3)
        source['review_evidence'].update(source_asset=third,asset_policy_id=pid,route_kind=2,route_id=rid)
        chain['activation_sources'].append(source)
        pools={p['pool_id']:p for p in chain['pools']}
        for version in (0,1):
            gate=P.Gate(F.COMMIT)
            P._routes(gate,copy.deepcopy(chain),'chain',tokens,chain['dependencies'],pools,chain['execution_loss_policy'],version)
            self.assertEqual(set() if version==0 else {'source.contribution_assets'},
                {i['code'] for i in gate.issues},gate.issues)

    def test_mint_profile_one_does_not_promote_historical_fee_layout(self):
        from tests_python.test_mint_integration_qualification import current_fixture
        config=current_fixture()
        old=F.fixture()['chains'][0]
        config.pop('fee_intake_version')
        chain=config['chains'][0]
        chain['helpers'].pop('activation_assets_factory')
        chain['helpers']['reward_receiver_factory']=old['helpers']['reward_receiver_factory']
        chain['native_accounting']['canonical_schema']=P.CANONICAL_SCHEMA
        expected=P.expected_bindings(chain)
        for category,records in expected.items():
            for role,bindings in records.items():
                chain[category][role]['observed_bindings']=copy.deepcopy(bindings)
                if category=='helpers':chain[category][role]['bindings']=copy.deepcopy(bindings)
        result=self.report(config)
        self.assertEqual({'mint.opensea_unsupported'},{i['code'] for i in result['issues']})
        self.assertFalse(result['production_qualification_supported'])
        self.assertEqual('legacy_manifest_consistency_only',result['approval_scope'])

    def test_observer_queries_current_version_and_never_removed_factory_getters(self):
        deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(F,'HASH',RUNTIME):
            config=lp_only_fixture(F.fixture());rpc=CompositionRPC(config)
            observed=O.observe(config,rpc)
            self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
            self.assertTrue(self.report(observed)['ready'])
            calls={args[0]['data'] for method,args in rpc.calls if method=='eth_call'}
            self.assertIn(selector('FEE_INTAKE_VERSION()'),calls)
            self.assertIn(selector('CUSTODY_VERSION()'),calls)
            self.assertIn(selector('SOURCE_POLICY_VERSION()'),calls)
            self.assertIn(selector('activationAssetsFactory()'),calls)
            self.assertIn(selector('assetsOf(address)')+O._word(config['chains'][0]['modules']['pools']['address']),calls)
            self.assertNotIn(selector('assetsOfRegistry()'),calls)
            self.assertNotIn(selector('receiverFactory()'),calls)
            self.assertNotIn(selector('rewardReceiverCount()'),calls)

    def test_current_observer_rejects_missing_or_retired_helpers_before_rpc(self):
        for change in ('missing','retired'):
            config=lp_only_fixture(F.fixture())
            if change=='missing':config['chains'][0]['helpers'].pop('lp_converter')
            else:config['chains'][0]['helpers']['reward_receiver_factory']=F.fixture()['chains'][0]['helpers']['reward_receiver_factory']
            rpc=CompositionRPC(config)
            with self.assertRaisesRegex(ValueError,'15-helper'):
                O.observe(config,rpc)
            self.assertEqual([],rpc.calls)

    def test_activation_factory_mapping_uses_exact_registry_and_fails_closed(self):
        deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(F,'HASH',RUNTIME):
            for failure in ('missing','wrong','malformed'):
                config=lp_only_fixture(F.fixture());chain=config['chains'][0];rpc=CompositionRPC(config)
                target=chain['helpers']['activation_assets_factory']['address']
                data=selector('assetsOf(address)')+O._word(chain['modules']['pools']['address'])
                if failure=='missing':rpc.bad=lambda address,payload:address==target and payload==data
                else:rpc.overrides[target,data]=encoded(F.addr(99999)) if failure=='wrong' else '0x'
                observed=O.observe(config,rpc)
                self.assertFalse(observed['chains'][0]['observation']['complete'])
                self.assertFalse(self.report(observed)['ready'])

    def test_observer_missing_or_wrong_version_is_unavailable_without_legacy_fallback(self):
        deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(F,'HASH',RUNTIME):
            for role,signature in (('fees','FEE_INTAKE_VERSION()'),('migration','CUSTODY_VERSION()')):
                for failure in ('missing','wrong','malformed'):
                    config=lp_only_fixture(F.fixture());rpc=CompositionRPC(config)
                    target=config['chains'][0]['modules'][role]['address']
                    getter=selector(signature)
                    if failure=='missing':rpc.bad=lambda address,data:address==target and data==getter
                    else:rpc.overrides[target,getter]=encoded(0) if failure=='wrong' else '0x'
                    observed=O.observe(config,rpc)
                    self.assertFalse(observed['chains'][0]['observation']['complete'])
                    self.assertFalse(self.report(observed)['ready'])
                    calls={args[0]['data'] for method,args in rpc.calls if method=='eth_call'}
                    self.assertNotIn(selector('receiverFactory()'),calls)
                    self.assertNotIn(selector('rewardReceiverCount()'),calls)


if __name__=='__main__':unittest.main()
