"""Synthetic offline manifest tests; fixtures are never deployment configurations."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('production_gate',ROOT/'scripts/validate-production-config.py')
GATE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(GATE)
COMMIT='ab'*20;NOW=int(time.time());HASH='0x'+'11'*32
def addr(number):return '0x'+f'{number:040x}'
def proof():return {'status':'passed','commit':COMMIT,'sha256':'22'*32,'reference':'synthetic-test-evidence.json'}

def fixture():
    manifest={'schema_version':3,'accounting_model':'shared-pools-v1','release_commit':COMMIT,'canonical_chain_id':1,
        'migration':{'enabled':True,'future_onboarding_evidence':proof(),'disabled_scope_approval':proof()},
        'economics':{'reward_model':'conventional_lp_fees','mint_price_wei':'50000000000000000',
            'minimum_activation_usd18':str(500*10**18),'fee_split_bps':[5000,3000,1000,1000]},
        'evidence':{key:proof() for key in GATE.EVIDENCE},'chains':[],'routes':[],'transport_policies':[]}
    manifest['evidence']['multi_chain']=dict(proof(),kind='provider_staged_multichain')
    manifest['evidence']['independent_audit'].update(auditor='Synthetic external auditor fixture',
        independent=True,kind='external_security_audit',open_critical=0,open_high=0)
    for cid in (1,2):
        base=cid*1000;controller=addr(base+1)
        modules={name:{'address':addr(base+i+1),'runtime_hash':HASH,'controller':controller}
            for i,name in enumerate(GATE.MODULES)}
        del modules['access']['controller']
        dependencies={name:{'address':addr(base+i+100),'runtime_hash':HASH,'authority_review':proof()}
            for i,name in enumerate(('position_manager','state_view','pool_manager','permit2','zzz'))}
        dependencies['position_manager'].update(pool_manager=dependencies['pool_manager']['address'],permit2=dependencies['permit2']['address'])
        dependencies['state_view']['pool_manager']=dependencies['pool_manager']['address']
        dependencies['zzz'].update(address=addr(base+201),burn_model='burn(uint256):exact_local_supply_reduction',burn_evidence=proof())
        provider={'provider_id':HASH,'channel_id':'0x'+'33'*32,'address':addr(base+105),'runtime_hash':HASH,
            'router':modules['transport']['address'],'configuration_hash':'0x'+f'{cid:064x}',
            'upgradeable':False,'immutable_configuration':True,'authenticated_delivery':True,
            'funded_equivalent_assets':True,'nonce_domain_replay_protection':True,'finality_and_retries_reviewed':True,
            'authority_review':proof(),'integration_evidence':proof()}
        provider['integration_evidence'].update(kind='provider_staged_delivery',provider_id=HASH,channel_id=provider['channel_id'],chain_id=cid)
        tokens=[{'address':addr(base+200+i),'runtime_hash':HASH,'decimals':18,'canonical_asset':f'asset-{i}',
            'non_rebasing':True,'transfer_tax':False,'reward_asset':True,
            'feed':{'source':addr(base+300+i),'runtime_hash':HASH,'denomination':'USD','decimals':8,
                'maximum_age_seconds':3600,'answer':100_000_000,'updated_at':NOW-100,'round_id':7,
                'answered_in_round':7,'review':proof()}} for i in range(2)]
        pool={'currency0':tokens[0]['address'],'currency1':tokens[1]['address'],'fee':3000,'tickSpacing':60,
            'hooks':GATE.ZERO,'rangeBps':1000,'triggerBps':300,'maxSpotDeviationBps':100,'maxSlippageBps':100,
            'minRebalanceInterval':600,'minDepositUSD':str(500*10**18),'maxPositionUSD':str(100_000*10**18),
            'depositsEnabled':True,'operationsEnabled':True}
        pool['pool_id']=GATE.identity([(pool['currency0'],'address'),(pool['currency1'],'address'),
            (pool['fee'],'uint24'),(pool['tickSpacing'],'uint24'),(GATE.ZERO,'address')])
        manifest['chains'].append({'chain_id':cid,'observed_block':{'number':5000,'hash':HASH,'timestamp':NOW},
            'maximum_snapshot_age_seconds':3600,'modules':modules,
            'governance':{'multisig':addr(base+400),'proposers':[addr(base+400)],'executors':[GATE.ZERO],
                'signers':[addr(base+401),addr(base+402)],'threshold':2,'keeper':addr(base+403),'guardian':addr(base+404),
                'timelock_seconds':172800,'delay_fixed':True,'post_seal_routes_timelocked':True,
                'migration_delay_seconds':172800,'sealed':True,'bootstrap':GATE.ZERO,'roles_and_seal_evidence':proof()},
            'constructor':{'canonical_chain_id':1,'mint_proceeds_recipient':addr(base+405),'nft_base_uri':'ipfs://synthetic',
                'maximum_buyback_usd18':str(1000*10**18),'recipient_payment_evidence':proof(),'adapter_transport':modules['transport']['address']},
            'bridge_router':{'immutable_module':True,'upgradeable':False,'policy_count':2,'registered_policy_ids':[],'outbound_policy_count':1,'observation_evidence':proof()},
            'providers':[provider],'bucket_reservations':[],
            'dependencies':dependencies,'tokens':tokens,'sequencer':{'mode':'not_applicable','address':GATE.ZERO,'review':proof()},'pools':[pool]})
    origin=manifest['chains'][0]
    bucket=int(GATE.identity([(1,'uint256'),(origin['modules']['vault']['address'],'address'),
        (origin['pools'][0]['pool_id'],'bytes32')]),16)
    for chain in manifest['chains']:
        chain['bucket_reservations']=[{'pool_id':chain['pools'][0]['pool_id'],'bucket_id':str(bucket),
            'home_chain_id':1,'home_vault':origin['modules']['vault']['address'],'home_pool_id':origin['pools'][0]['pool_id'],
            'observed_chain_id':chain['chain_id'],'observed_vault':chain['modules']['vault']['address'],
            'observed_bucket_id':str(bucket),'observed_block_number':chain['observed_block']['number'],
            'observed_block_hash':chain['observed_block']['hash'],
            'review_evidence':dict(proof(),independent=True,reviewer='Synthetic independent reservation reviewer')}]
    for source,destination in ((1,2),(2,1)):
        a,b=manifest['chains'][source-1],manifest['chains'][destination-1];pa=a['providers'][0];pb=b['providers'][0]
        policy={'providerId':HASH,'sourceChain':source,'sourceRouter':pa['router'],'sourceProvider':pa['address'],
            'sourceCodeHash':pa['runtime_hash'],'sourceConfigurationHash':pa['configuration_hash'],
            'destinationChain':destination,'destinationRouter':pb['router'],'destinationProvider':pb['address'],
            'destinationCodeHash':pb['runtime_hash'],'destinationConfigurationHash':pb['configuration_hash'],
            'channelId':pa['channel_id'],'reviewHash':'0x'+'22'*32,'outbound_enabled':True,'review_evidence':proof()}
        policy['policy_id']=GATE.identity([(policy[key],typ) for key,typ in GATE.POLICY_FIELDS]);manifest['transport_policies'].append(policy)
    def route(source,destination,kind,slot=0):
        a,b=manifest['chains'][source-1],manifest['chains'][destination-1]
        item={'kind':kind,'enabled':True,'sourceChain':source,'destinationChain':destination,
            'sourceAdapter':a['modules']['bridge']['address'],'sourceVault':a['modules']['vault']['address'],
            'sourceReceiver':a['modules']['receiver']['address'],'destinationAdapter':b['modules']['bridge']['address'],
            'destinationVault':b['modules']['vault']['address'],'destinationReceiver':b['modules']['receiver']['address'],
            'destinationPool':b['pools'][0]['pool_id'] if kind=='principal' else '0x'+'00'*32,
            'sourceToken0':a['tokens'][slot]['address'] if kind!='ack' else GATE.ZERO,
            'destinationToken0':b['tokens'][slot]['address'] if kind!='ack' else GATE.ZERO,
            'sourceToken1':a['tokens'][1]['address'] if kind=='principal' else GATE.ZERO,
            'destinationToken1':b['tokens'][1]['address'] if kind=='principal' else GATE.ZERO,
            'token0Decimals':18 if kind!='ack' else 0,'token1Decimals':18 if kind=='principal' else 0,
            'asset_and_authority_evidence':proof()}
        if kind=='principal':item.update(bucket_id=str(bucket),source_pool_id=a['pools'][0]['pool_id'])
        item['policy_id']=next(p['policy_id'] for p in manifest['transport_policies'] if p['sourceChain']==source and p['destinationChain']==destination)
        item['route_id']=GATE.identity([(item[key],typ) for key,typ in GATE.ROUTE_FIELDS]+[(item['policy_id'],'bytes32')]);return item
    manifest['routes']=[route(1,2,'principal'),route(2,1,'ack'),route(2,1,'reward',0),route(2,1,'reward',1),
        route(2,1,'principal'),route(1,2,'ack')]
    for chain in manifest['chains']:chain['bridge_router']['registered_policy_ids']=[p['policy_id'] for p in manifest['transport_policies']]
    return manifest

def disabled_fixture():
    manifest=fixture();manifest['migration']['enabled']=False
    manifest['chains']=manifest['chains'][:1];manifest['routes']=[];manifest['transport_policies']=[]
    manifest['chains'][0]['providers']=[]
    manifest['chains'][0]['bucket_reservations']=[]
    manifest['chains'][0]['bridge_router'].update(policy_count=0,registered_policy_ids=[],outbound_policy_count=0)
    del manifest['evidence']['multi_chain']
    return manifest

def onward_fixture():
    manifest=fixture();third=copy.deepcopy(manifest['chains'][1]);third['chain_id']=3
    third['providers'][0]['integration_evidence']['chain_id']=3
    third['bucket_reservations'][0]['observed_chain_id']=3;manifest['chains'].append(third)
    for source,destination in ((2,3),(3,2),(3,1)):
        policy=copy.deepcopy(manifest['transport_policies'][0])
        for side,cid in (('source',source),('destination',destination)):
            wrapper=manifest['chains'][cid-1]['providers'][0]
            policy.update({side+'Chain':cid,side+'Router':wrapper['router'],side+'Provider':wrapper['address'],
                side+'CodeHash':wrapper['runtime_hash'],side+'ConfigurationHash':wrapper['configuration_hash']})
        policy['policy_id']=GATE.identity([(policy[key],typ) for key,typ in GATE.POLICY_FIELDS]);manifest['transport_policies'].append(policy)
    for source,destination,kind,slot in ((2,3,'principal',0),(3,2,'ack',0),(3,1,'ack',0),(3,1,'reward',0),(3,1,'reward',1)):
        route=copy.deepcopy(next(r for r in manifest['routes'] if r['kind']==kind))
        a,b=manifest['chains'][source-1],manifest['chains'][destination-1]
        for side,chain in (('source',a),('destination',b)):
            route[side+'Chain']=chain['chain_id']
            for suffix,module in (('Adapter','bridge'),('Vault','vault'),('Receiver','receiver')):route[side+suffix]=chain['modules'][module]['address']
            route[side+'Token0']=chain['tokens'][slot]['address'] if kind!='ack' else GATE.ZERO
            route[side+'Token1']=chain['tokens'][1]['address'] if kind=='principal' else GATE.ZERO
        route['destinationPool']=b['pools'][0]['pool_id'] if kind=='principal' else '0x'+'00'*32
        route['policy_id']=next(p['policy_id'] for p in manifest['transport_policies'] if p['sourceChain']==source and p['destinationChain']==destination)
        if kind=='principal':route.update(canonical_graph_evidence=proof(),source_pool_id=a['pools'][0]['pool_id'])
        route['route_id']=GATE.identity([(route[key],typ) for key,typ in GATE.ROUTE_FIELDS]+[(route['policy_id'],'bytes32')]);manifest['routes'].append(route)
    for chain in manifest['chains']:
        cid=chain['chain_id'];listed=[p['policy_id'] for p in manifest['transport_policies'] if cid in (p['sourceChain'],p['destinationChain'])]
        if cid==1:listed.append(next(p['policy_id'] for p in manifest['transport_policies'] if p['sourceChain']==2 and p['destinationChain']==3))
        chain['bridge_router'].update(registered_policy_ids=listed,policy_count=len(listed),
            outbound_policy_count=sum(p['sourceChain']==cid and p['outbound_enabled'] for p in manifest['transport_policies'] if p['policy_id'] in listed))
    return manifest

class ProductionConfigTests(unittest.TestCase):
    def setUp(self):self.config=fixture()
    def result(self):return GATE.validate(self.config,expected_commit=COMMIT,now=NOW)
    def blocked(self,code):
        result=self.result();self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
        self.assertIn(code,[issue['code'] for issue in result['issues']])
    def test_complete_synthetic_manifest_is_consistent_without_deployment_authorization(self):
        before=copy.deepcopy(self.config);result=self.result()
        self.assertEqual(result['issues'],[]);self.assertEqual(result['status'],'ready')
        self.assertFalse(result['deployment_authorized']);self.assertEqual(self.config,before)
    def test_canonical_only_sealed_launch_without_providers_is_consistent(self):
        self.config=disabled_fixture();result=self.result()
        self.assertEqual(result['issues'],[]);self.assertTrue(result['ready']);self.assertFalse(result['migration_enabled'])
        self.assertFalse(result['deployment_authorized'])
    def test_disabled_migration_does_not_waive_existing_release_gates(self):
        for key in GATE.EVIDENCE:
            with self.subTest(key=key):
                self.config=disabled_fixture();del self.config['evidence'][key];self.blocked('evidence.missing')
        self.config=disabled_fixture();self.config['economics']['reward_model']=None;self.blocked('reward.unsupported')
    def test_disabled_launch_requires_future_architecture_evidence_and_scope_approval(self):
        for key in ('future_onboarding_evidence','disabled_scope_approval'):
            with self.subTest(key=key):
                self.config=disabled_fixture();del self.config['migration'][key];self.blocked('evidence.missing')
    def test_disabled_launch_rejects_any_observed_or_declared_provider_policies(self):
        self.config=disabled_fixture();self.config['chains'][0]['bridge_router']['outbound_policy_count']=1;self.blocked('migration.not_disabled')
        self.config=disabled_fixture();self.config['transport_policies']=[fixture()['transport_policies'][0]];self.blocked('migration.not_disabled')
    def test_enabled_migration_requires_real_provider_delivery_evidence(self):
        del self.config['evidence']['multi_chain'];self.blocked('evidence.missing')
        self.config=fixture();del self.config['chains'][0]['providers'][0]['integration_evidence'];self.blocked('evidence.missing')
        self.config=fixture();self.config['evidence']['multi_chain']['kind']='mock_model';self.blocked('provider.evidence')
        self.config=fixture();self.config['chains'][0]['providers'][0]['integration_evidence']['channel_id']='0x'+'55'*32;self.blocked('provider.evidence')
    def test_adapter_must_bind_fixed_router_and_all_seventeen_modules(self):
        self.config['chains'][0]['constructor']['adapter_transport']=addr(999);self.blocked('router.binding')
        self.config=fixture();del self.config['chains'][0]['modules']['transport'];self.blocked('hex.invalid')
    def test_proxy_wrapper_configuration_drift_and_policy_rebinding_are_blocked(self):
        provider=self.config['chains'][0]['providers'][0];provider['upgradeable']=True;self.blocked('provider.mutable')
        provider.update(upgradeable=False,configuration_hash='0x'+'88'*32);self.blocked('policy.provider')
        self.config=fixture();self.config['transport_policies'][0]['sourceProvider']=addr(999);self.blocked('policy.identity');self.blocked('policy.provider')
    def test_policy_review_pin_and_observed_enabled_count_must_match(self):
        self.config['transport_policies'][0]['review_evidence']['sha256']='77'*32;self.blocked('policy.review')
        self.config=fixture();self.config['chains'][0]['bridge_router']['outbound_policy_count']=0;self.blocked('router.inventory')
    def test_unknown_registered_policy_cannot_hide_an_inbound_provider(self):
        router=self.config['chains'][0]['bridge_router'];router['registered_policy_ids'].append('0x'+'99'*32);router['policy_count']+=1
        self.blocked('router.unknown')
    def test_local_policy_missing_from_complete_registration_history_is_blocked(self):
        router=self.config['chains'][0]['bridge_router'];router['registered_policy_ids'].pop();router['policy_count']=1
        self.blocked('router.unlisted')
    def test_duplicate_registration_ids_and_count_mismatch_are_blocked(self):
        router=self.config['chains'][0]['bridge_router'];router['registered_policy_ids'].append(router['registered_policy_ids'][0])
        self.blocked('router.duplicate')
        self.config=fixture();self.config['chains'][0]['bridge_router']['policy_count']=3;self.blocked('router.inventory')
    def test_canonical_remote_policy_registration_requires_complete_reviewed_graph(self):
        self.config=onward_fixture();self.assertEqual(self.result()['issues'],[])
        graph=next(r for r in self.config['routes'] if r['sourceChain']==2 and r['destinationChain']==3 and r['kind']=='principal')
        del graph['canonical_graph_evidence'];self.blocked('evidence.missing')
    def test_noncanonical_chain_cannot_register_remote_only_policy(self):
        self.config=onward_fixture();router=self.config['chains'][2]['bridge_router']
        router['registered_policy_ids'].append(self.config['transport_policies'][0]['policy_id']);router['policy_count']+=1
        self.blocked('router.remote_registration')
    def test_disabled_policy_is_not_usable_for_new_outbound_route(self):
        self.config['transport_policies'][0]['outbound_enabled']=False
        self.config['chains'][0]['bridge_router']['outbound_policy_count']=0
        self.blocked('route.policy')
    def test_new_policy_creates_new_route_identity_without_mutating_old_route(self):
        old=copy.deepcopy(self.config['routes'][0]);policy=copy.deepcopy(self.config['transport_policies'][0])
        policy.update(reviewHash='0x'+'77'*32,review_evidence=dict(proof(),sha256='77'*32))
        policy['policy_id']=GATE.identity([(policy[key],typ) for key,typ in GATE.POLICY_FIELDS])
        new=copy.deepcopy(old);new['policy_id']=policy['policy_id']
        new['route_id']=GATE.identity([(new[key],typ) for key,typ in GATE.ROUTE_FIELDS]+[(new['policy_id'],'bytes32')])
        self.config['transport_policies'].append(policy);self.config['routes'].append(new)
        for chain in self.config['chains']:
            chain['bridge_router']['policy_count']=3;chain['bridge_router']['registered_policy_ids'].append(policy['policy_id'])
        self.config['chains'][0]['bridge_router']['outbound_policy_count']=2
        self.assertNotEqual(new['route_id'],old['route_id']);self.assertEqual(self.config['routes'][0],old)
        self.assertEqual(self.result()['issues'],[])
    def test_provider_rotation_retains_disabled_old_routes_and_complete_policy_history(self):
        old_policy=self.config['transport_policies'][0];old_policy['outbound_enabled']=False
        old_routes=[r for r in self.config['routes'] if r['policy_id']==old_policy['policy_id']]
        old_ids={r['route_id'] for r in old_routes}
        for route in old_routes:route['enabled']=False
        new_policy=copy.deepcopy(old_policy);new_policy.update(providerId='0x'+'aa'*32,channelId='0x'+'dd'*32,
            reviewHash='0x'+'ee'*32,review_evidence=dict(proof(),sha256='ee'*32),outbound_enabled=True)
        for side,index in (('source',0),('destination',1)):
            wrapper=copy.deepcopy(self.config['chains'][index]['providers'][0]);wrapper.update(provider_id=new_policy['providerId'],
                channel_id=new_policy['channelId'],address=addr(9000+index),runtime_hash='0x'+'bb'*32,configuration_hash='0x'+'cc'*32)
            wrapper['integration_evidence'].update(provider_id=wrapper['provider_id'],channel_id=wrapper['channel_id'])
            self.config['chains'][index]['providers'].append(wrapper)
            new_policy.update({side+'Provider':wrapper['address'],side+'CodeHash':wrapper['runtime_hash'],side+'ConfigurationHash':wrapper['configuration_hash']})
        new_policy['policy_id']=GATE.identity([(new_policy[key],typ) for key,typ in GATE.POLICY_FIELDS]);self.config['transport_policies'].append(new_policy)
        for old in old_routes:
            new=copy.deepcopy(old);new.update(policy_id=new_policy['policy_id'],enabled=True)
            new['route_id']=GATE.identity([(new[key],typ) for key,typ in GATE.ROUTE_FIELDS]+[(new['policy_id'],'bytes32')]);self.config['routes'].append(new)
        for chain in self.config['chains']:
            chain['bridge_router']['registered_policy_ids'].append(new_policy['policy_id']);chain['bridge_router']['policy_count']=3
        self.assertEqual(self.result()['issues'],[])
        self.assertTrue(old_ids<={r['route_id'] for r in self.config['routes']});self.assertTrue(all(r['enabled'] is False for r in old_routes))
        self.assertNotEqual(new_policy['sourceProvider'],old_policy['sourceProvider'])
    def test_enabled_migration_requires_active_principal_and_active_settlement_paths(self):
        for route in self.config['routes']:route['enabled']=False
        self.blocked('route.active_principal')
        self.config=fixture();next(r for r in self.config['routes'] if r['kind']=='ack' and r['sourceChain']==2)['enabled']=False
        self.blocked('route.ack_missing')
        self.config=fixture();next(r for r in self.config['routes'] if r['kind']=='reward')['enabled']=False
        self.blocked('route.rewards_missing')
    def test_missing_every_release_evidence_gate_blocks(self):
        for key in GATE.EVIDENCE:
            with self.subTest(key=key):
                evidence=self.config['evidence'].pop(key);self.blocked('evidence.missing');self.config['evidence'][key]=evidence
    def test_stale_evidence_or_wrong_commit_blocks(self):
        self.config['evidence']['uniswap_fork']['commit']='cd'*20;self.blocked('evidence.stale')
        self.config['release_commit']='cd'*20;self.blocked('commit.mismatch')
    def test_internal_audit_or_unresolved_high_findings_blocks(self):
        self.config['evidence']['independent_audit']['independent']=False;self.blocked('audit.internal')
        self.config['evidence']['independent_audit'].update(independent=True,open_high=1);self.blocked('audit.unresolved')
    def test_selected_robinhood_native_hooked_zero_fee_pool_blocks(self):
        pool=self.config['chains'][0]['pools'][0]
        pool.update(currency0=GATE.ZERO,fee=0,hooks='0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044',
            pool_id='0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f')
        self.blocked('pool.hook');self.blocked('pool.assets');self.blocked('integer.invalid')
    def test_deferred_or_unimplemented_reward_decision_blocks(self):
        self.config['economics']['reward_model']='pending';self.blocked('reward.unsupported')
    def test_wrong_price_activation_or_split_blocks(self):
        for key,value,code in [('mint_price_wei','1','mint.price'),('minimum_activation_usd18','499','activation.minimum'),
            ('fee_split_bps',[5000,3000,1000,999],'reward.split')]:
            with self.subTest(key=key):
                old=self.config['economics'][key];self.config['economics'][key]=value;self.blocked(code);self.config['economics'][key]=old
    def test_missing_module_hash_or_wrong_binding_blocks(self):
        module=self.config['chains'][0]['modules']['vault'];module['runtime_hash']=None;self.blocked('hex.invalid')
        module['controller']=addr(999);self.blocked('binding.controller')
    def test_duplicate_module_binding_blocks(self):
        chain=self.config['chains'][0];chain['modules']['nft']['address']=chain['modules']['vault']['address'];self.blocked('binding.duplicate')
    def test_governance_threshold_and_keeper_separation(self):
        governance=self.config['chains'][0]['governance'];governance['threshold']=3;self.blocked('integer.invalid')
        governance['threshold']=2;governance['keeper']=governance['multisig'];self.blocked('role.keeper')
    def test_guardian_governance_overlap_requires_review_and_is_allowed(self):
        governance=self.config['chains'][0]['governance'];governance['guardian']=governance['multisig'];self.blocked('decision.pending')
        governance['overlap_review']='Synthetic fixture explicitly reviewed combined pause/governance authority'
        self.assertTrue(self.result()['ready'])
    def test_short_timelock_mutable_delay_or_unsealed_bootstrap_blocks(self):
        governance=self.config['chains'][0]['governance'];governance['timelock_seconds']=86399;self.blocked('integer.invalid')
        governance.update(timelock_seconds=172800,delay_fixed=False);self.blocked('timelock.mutable')
        governance.update(delay_fixed=True,sealed=False,bootstrap=addr(99));self.blocked('seal.incomplete')
    def test_mint_recipient_cannot_be_protocol_custody(self):
        chain=self.config['chains'][0];chain['constructor']['mint_proceeds_recipient']=chain['modules']['vault']['address'];self.blocked('mint.custody')
    def test_float_boolean_integer_fields_are_not_truncated(self):
        self.config['schema_version']=3.0;self.blocked('schema.unsupported');self.config['schema_version']=3
        for field,value in [('chain_id',True),('chain_id',1.9),('maximum_snapshot_age_seconds',1.0)]:
            with self.subTest(field=field,value=value):
                previous=self.config['chains'][0][field];self.config['chains'][0][field]=value;self.blocked('integer.invalid');self.config['chains'][0][field]=previous
    def test_legacy_per_nft_manifest_is_rejected(self):
        self.config['schema_version']=2;self.blocked('schema.unsupported')
    def test_accounting_model_must_explicitly_match_shared_pools(self):
        for model in (None,'per-nft','pending'):
            with self.subTest(model=model):
                self.config['accounting_model']=model;self.blocked('accounting.unsupported')
    def test_principal_route_requires_both_exact_bucket_reservations(self):
        for chain_index in (0,1):
            with self.subTest(chain_index=chain_index):
                self.config=fixture();self.config['chains'][chain_index]['bucket_reservations']=[]
                self.blocked('route.reservation')
    def test_principal_route_requires_explicit_source_pool_and_bucket(self):
        for field in ('bucket_id','source_pool_id'):
            with self.subTest(field=field):
                self.config=fixture();del self.config['routes'][0][field]
                self.blocked('route.reservation')
    def test_principal_route_cannot_claim_another_cohort_or_source_pool(self):
        self.config['routes'][0]['bucket_id']='123';self.blocked('route.reservation')
        self.config=fixture();self.config['routes'][0]['source_pool_id']='0x'+'44'*32
        self.blocked('route.source_pool');self.blocked('route.reservation')
    def test_bucket_identity_must_hash_canonical_origin(self):
        record=self.config['chains'][1]['bucket_reservations'][0]
        record['bucket_id']='123';record['observed_bucket_id']='123'
        self.blocked('reservation.identity')
    def test_reservation_origin_must_be_the_actual_canonical_vault_and_pool(self):
        for field,value,code in (('home_chain_id',2,'reservation.origin'),('home_vault',addr(999),'reservation.origin'),
            ('home_pool_id','0x'+'44'*32,'reservation.pool')):
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][1]['bucket_reservations'][0][field]=value
                self.blocked(code)
    def test_observed_pool_reservation_must_match_exact_inventory_snapshot(self):
        for field,value in (('observed_chain_id',1),('observed_vault',addr(999)),('observed_bucket_id','123'),
            ('observed_block_number',4999),('observed_block_hash','0x'+'44'*32)):
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][1]['bucket_reservations'][0][field]=value
                self.blocked('reservation.observation')
    def test_zero_unreserved_pool_or_malformed_bucket_is_rejected(self):
        for value in (0,'0',True,'1.1',-1):
            with self.subTest(value=value):
                self.config=fixture();self.config['chains'][1]['bucket_reservations'][0]['observed_bucket_id']=value
                self.blocked('integer.invalid');self.blocked('reservation.observation')
    def test_reservation_evidence_must_be_independent_and_for_exact_release(self):
        review=self.config['chains'][1]['bucket_reservations'][0]['review_evidence']
        review['independent']=False;self.blocked('reservation.review')
        review.update(independent=True,commit='cd'*20);self.blocked('evidence.stale')
        review.update(commit=COMMIT,reviewer='pending');self.blocked('decision.pending')
    def test_duplicate_or_conflicting_pool_reservation_is_rejected(self):
        chain=self.config['chains'][1]
        chain['bucket_reservations'].append(copy.deepcopy(chain['bucket_reservations'][0]))
        self.blocked('reservation.duplicate')
    def test_disabled_initial_launch_can_have_no_pool_reservations(self):
        self.config=disabled_fixture();self.assertEqual(self.result()['issues'],[])
    def test_reservation_assets_cannot_change_canonical_group_identity(self):
        self.config['chains'][1]['tokens'][0]['canonical_asset']='unrelated-asset'
        self.blocked('reservation.assets')
    def test_malformed_reservation_inventory_fails_closed_without_exception(self):
        for value in (None,{},True,[None],[False],[[]]):
            with self.subTest(value=value):
                self.config=fixture();self.config['chains'][1]['bucket_reservations']=value
                self.assertFalse(self.result()['ready'])
    def test_reservation_gate_output_declares_shared_pool_schema_three(self):
        self.assertEqual(self.result()['schema_version'],3)
    def test_stale_snapshot_and_oracle_round_block(self):
        chain=self.config['chains'][0];chain['observed_block']['timestamp']=NOW-3601;self.blocked('snapshot.stale')
        chain['observed_block']['timestamp']=NOW;feed=chain['tokens'][0]['feed'];feed['updated_at']=NOW-3601;self.blocked('oracle.stale')
        feed.update(updated_at=NOW,answered_in_round=6);self.blocked('oracle.stale')
    def test_wrong_feed_denomination_or_sequencer_grace_blocks(self):
        chain=self.config['chains'][0];feed=chain['tokens'][0]['feed'];feed['denomination']='ETH';self.blocked('oracle.denomination');feed['denomination']='USD'
        chain['sequencer'].update(mode='feed',address=addr(999),runtime_hash=HASH,answer=0,started_at=NOW-3600);self.blocked('sequencer.down')
        chain['sequencer']['started_at']=NOW-3601;self.assertTrue(self.result()['ready'])
    def test_uniswap_dependency_mismatch_and_burn_semantics_block(self):
        dependencies=self.config['chains'][0]['dependencies'];dependencies['position_manager']['pool_manager']=addr(99);self.blocked('uniswap.binding')
        dependencies['zzz']['burn_model']='send_to_dead_address';self.blocked('burn.unsupported')
    def test_missing_transport_authentication_backing_or_replay_protection_blocks(self):
        transport=self.config['chains'][0]['providers'][0]
        for key in ('authenticated_delivery','funded_equivalent_assets','nonce_domain_replay_protection','finality_and_retries_reviewed'):
            with self.subTest(key=key):transport[key]=False;self.blocked('transport.incomplete');transport[key]=True
    def test_duplicate_route_and_mutated_identity_block(self):
        self.config['routes'].append(copy.deepcopy(self.config['routes'][0]));self.blocked('route.replay')
        self.config['routes'].pop();self.config['routes'][0]['destinationVault']=addr(99);self.blocked('route.identity');self.blocked('route.binding')
    def test_nonstring_route_kind_is_blocked_without_exception(self):
        for value in ([],{},["principal"]):
            with self.subTest(value=value):
                self.config['routes'][0]['kind']=value;self.blocked('route.kind')
    def test_unequal_asset_decimals_or_provenance_blocks(self):
        token=self.config['chains'][1]['tokens'][0];token['decimals']=6;self.blocked('route.equivalence')
        token.update(decimals=18,canonical_asset='different-asset');self.blocked('route.equivalence')
    def test_missing_ack_or_historical_reward_route_blocks(self):
        self.config['routes']=[r for r in self.config['routes'] if r['kind']!='ack'];self.blocked('route.ack_missing')
        self.config=fixture();self.config['routes']=[r for r in self.config['routes'] if r['kind']!='reward'];self.blocked('route.rewards_missing')
    def test_onward_satellite_requires_canonical_graph_and_home_location_ack(self):
        self.config=onward_fixture();self.config['routes']=[r for r in self.config['routes'] if not(r['sourceChain']==3 and r['destinationChain']==1 and r['kind']=='ack')]
        self.blocked('route.home_ack_missing')
    def test_malformed_nested_objects_fail_closed_without_exception(self):
        for field,value in [('modules',[]),('dependencies',False),('governance','invalid'),('tokens',True),('sequencer',None)]:
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][0][field]=value;self.assertFalse(self.result()['ready'])
    def test_template_is_explicitly_blocked(self):
        result=GATE.validate(json.loads((ROOT/'config/production.example.json').read_text(encoding='utf-8')),now=NOW)
        self.assertEqual(result['status'],'blocked');self.assertFalse(result['deployment_authorized'])
    def test_cli_emits_blocked_machine_readable_output_without_chain_access(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'gate.json'
            result=subprocess.run([sys.executable,str(ROOT/'scripts/validate-production-config.py'),
                '--config',str(ROOT/'config/production.example.json'),'--output',str(output)],capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,1,result.stderr);self.assertEqual(json.loads(result.stdout),json.loads(output.read_text(encoding='utf-8')))
    def test_cli_nonstring_route_kind_is_blocked_with_machine_readable_output(self):
        self.config['routes'][0]['kind']={"untrusted":"principal"}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'malformed.json';path.write_text(json.dumps(self.config),encoding='utf-8')
            result=subprocess.run([sys.executable,str(ROOT/'scripts/validate-production-config.py'),'--config',str(path)],
                capture_output=True,text=True,encoding='utf-8',check=False)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertIn('route.kind',[issue['code'] for issue in json.loads(result.stdout)['issues']])
    def test_cli_reads_utf8_inventory_and_writes_utf8_report(self):
        self.config['chains'][0]['constructor']['nft_base_uri']='ipfs://synthetic/caf\u00e9'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'inventory.json';output=Path(directory)/'gate.json'
            path.write_text(json.dumps(self.config,ensure_ascii=False),encoding='utf-8')
            result=subprocess.run([sys.executable,str(ROOT/'scripts/validate-production-config.py'),
                '--config',str(path),'--output',str(output)],capture_output=True,text=True,encoding='utf-8',check=False)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(json.loads(output.read_text(encoding='utf-8'))['ready'])
    def test_cli_invalid_json_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'invalid.json';path.write_text('{broken')
            result=subprocess.run([sys.executable,str(ROOT/'scripts/validate-production-config.py'),'--config',str(path)],capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,1);self.assertFalse(json.loads(result.stdout)['ready'])
