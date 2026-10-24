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
ARTWORK_BASE='ipfs://bafy'+'a'*55+'/'
def addr(number):return '0x'+f'{number:040x}'
def proof():return {'status':'passed','commit':COMMIT,'sha256':'22'*32,'reference':'synthetic-test-evidence.json'}

def nft_inventory(chain):
    """Synthetic coordinator/helper observations, never claims about live availability."""
    nft=chain['modules']['nft']['address'];controller=chain['modules']['access']['address'];cid=chain['chain_id']
    royalty=addr(cid*1000+700);renderer=addr(cid*1000+701);coordinator=addr(cid*1000+702);router=addr(cid*1000+703)
    key_hash='0x'+'77'*32
    artwork_base=chain['constructor']['nft_base_uri'];asset_manifest='55'*32
    bindings={'nft':nft,'royaltyRewards':royalty,'metadataRenderer':renderer,'royaltyReceiver':royalty,'royaltyBps':500,
        'claimRouter':router,'claimRouterNft':nft,'claimRouterController':controller,'claimRouterRoyalties':royalty,'MAX_CLAIMS':32,
        'artworkBaseURI':artwork_base,
        'MAX_SUPPLY':1000,'mintedCount':2,'nextToFinalize':2,'remainingToReveal':999,'rarityRemaining':[599,300,100],
        'randomnessConfigured':True,'randomnessCoordinator':coordinator,'keyHash':key_hash,'subscriptionId':7,
        'requestConfirmations':3,'callbackGasLimit':300000,'nativePayment':False}
    return {'royalty_rewards':{'address':royalty,'runtime_hash':HASH,'immutable':True,'nft':nft,
            'review_evidence':dict(proof(),independent=True)},
        'metadata_renderer':{'address':renderer,'runtime_hash':HASH,'immutable':True,'controller':controller,
            'review_evidence':dict(proof(),independent=True)},
        'claim_router':{'address':router,'runtime_hash':HASH,'immutable':True,'nft':nft,'controller':controller,
            'royalties':royalty,'max_claims':32,'review_evidence':dict(proof(),independent=True)},
        'observed_chain_id':cid,'observed_block_number':chain['observed_block']['number'],
        'observed_block_hash':chain['observed_block']['hash'],'observed_bindings':bindings,
        'artwork_publication':{'base_uri':artwork_base,'manifest_sha256':asset_manifest,'asset_count':len(GATE.ARTWORK_FILES),'asset_paths':list(GATE.ARTWORK_FILES),
            'review_evidence':dict(proof(),independent=True,kind='content_addressed_artwork_review',base_uri=artwork_base,
                asset_manifest_sha256=asset_manifest)},
        'royalty_assets':{'asset_count':1,'complete_admission_history':True,'observation_evidence':proof(),
            'assets':[{'address':GATE.ZERO,'observed_asset':GATE.ZERO,'observed_is_asset':True,'kind':'native','decimals':18,
                'runtime_hash':None,'admission_evidence':dict(proof(),independent=True,kind='royalty_asset_admission',asset=GATE.ZERO,
                    chain_id=cid,exact_transfers_reviewed=True,authority_risks_reviewed=True,activation_griefing_reviewed=True)}]},
        'randomness':{'coordinator':coordinator,'runtime_hash':HASH,'keyHash':key_hash,'subscriptionId':7,
            'requestConfirmations':3,'callbackGasLimit':300000,'nativePayment':False,
            'immutable_provider_configuration':True,
            'mutable_request_parameters':['requestConfirmations','callbackGasLimit'],'no_admin_reroll':True,
            'review_evidence':dict(proof(),independent=True,kind='verified_randomness_coordinator_review',chain_id=cid,coordinator=coordinator),
            'integration_evidence':dict(proof(),kind='coordinator_staged_randomness',chain_id=cid,coordinator=coordinator,
                nft=nft,fulfilled_request_id=91,finalized_token_id=123)},'observation_evidence':proof()}

def fixture():
    manifest={'schema_version':4,'accounting_model':'shared-pools-v2','release_commit':COMMIT,'canonical_chain_id':1,
        'migration':{'enabled':True,'future_onboarding_evidence':proof(),'disabled_scope_approval':proof()},
        'economics':{'reward_model':'conventional_lp_fees','mint_price_wei':'50000000000000000',
            'minimum_activation_usd18':str(100*10**18),'activation_minimum_basis':'gross_source_input',
            'maximum_entry_loss_bps':100,'network_gas_separate':True,'fee_split_bps':[8000,1000,500,500],
            'collective_weights':'equal_activated_nfts','maximum_membership_dust_raw':19},
        'nft_policy':{'max_supply':1000,'rarity_distribution':'fixed_quotas_without_replacement',
            'rarity_randomization':'vrf_mint_order_without_replacement','rarity_counts':[600,300,100],
            'initial_rarity_bps':[6000,3000,1000],
            'marketplace_royalty_bps':500,'received_royalty_distribution_bps':10000,'royalty_weights':[1,2,3],
            'royalty_eligibility':'activated_nfts_only','royalty_entitlement':'received_funds_only',
            'evolution_basis':'current_attributed_lp_value_usd18','unavailable_valuation':'unavailable',
            'evolution_thresholds_usd18':[str(n*10**18) for n in (0,100,1000,10000)],
            'randomness_policy':'verified_coordinator_two_words','economic_review_evidence':proof()},
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
            'minRebalanceInterval':600,'minDepositUSD':str(10**16),'maxPositionUSD':str(100_000*10**18),
            'depositsEnabled':True,'operationsEnabled':True}
        pool['pool_id']=GATE.identity([(pool['currency0'],'address'),(pool['currency1'],'address'),
            (pool['fee'],'uint24'),(pool['tickSpacing'],'uint24'),(GATE.ZERO,'address')])
        manifest['chains'].append({'chain_id':cid,'observed_block':{'number':5000,'hash':HASH,'timestamp':NOW},
            'maximum_snapshot_age_seconds':3600,'modules':modules,
            'governance':{'multisig':addr(base+400),'proposers':[addr(base+400)],'executors':[GATE.ZERO],
                'signers':[addr(base+401),addr(base+402)],'threshold':2,'keeper':addr(base+403),'guardian':addr(base+404),
                'timelock_seconds':0,'delay_fixed':True,'post_seal_routes_timelocked':False,
                'migration_delay_seconds':0,'sealed':True,'bootstrap':GATE.ZERO,'roles_and_seal_evidence':dict(proof(),zero_delay_governance_tested=True,immediate_migration_tested=True,no_notice_risk_accepted=True),
                'parking_rehearsal':dict(proof(),independent=True,oracle_independent_close_tested=True,
                    close_only_minimums_tested=True,governance_pause_nonce_tested=True,
                    oracle_guarded_resume_tested=True,parked_rewards_and_migration_tested=True)},
            'constructor':{'canonical_chain_id':1,'mint_proceeds_recipient':addr(base+405),'nft_base_uri':ARTWORK_BASE,
                'maximum_buyback_usd18':str(1000*10**18),'recipient_payment_evidence':proof(),'adapter_transport':modules['transport']['address']},
            'bridge_router':{'immutable_module':True,'upgradeable':False,'policy_count':2,'registered_policy_ids':[],'outbound_policy_count':1,'observation_evidence':proof()},
            'providers':[provider],'bucket_reservations':[],
            'dependencies':dependencies,'tokens':tokens,'sequencer':{'mode':'not_applicable','address':GATE.ZERO,
                'observed_oracle_feed':GATE.ZERO,'active_policy_id':'0x'+'00'*32,'policy_count':0,'review':proof()},'pools':[pool]})
        activation_address=addr(base+704)
        manifest['chains'][-1]['activation_assets']={'address':activation_address,'runtime_hash':HASH,'immutable':True,
            'registry':modules['pools']['address'],'controller':controller,'observed_registry_helper':activation_address,
            'observed_chain_id':cid,'observed_block_number':5000,'observed_block_hash':HASH,
            'review_evidence':dict(proof(),independent=True,add_disable_reenable_tested=True,
                active_policies_reviewed=True,no_claim_or_exit_dependency=True)}
        entry_address=addr(base+705)
        manifest['chains'][-1]['activation_entry']={'address':entry_address,'runtime_hash':HASH,'immutable':True,
            'registry':modules['pools']['address'],'controller':controller,'activation_assets':activation_address,
            'observed_registry_entry':entry_address,'observed_chain_id':cid,'observed_block_number':5000,'observed_block_hash':HASH,
            'review_evidence':dict(proof(),independent=True,original_source_value_tested=True,
                aggregate_loss_budget_tested=True,callback_owner_context_reviewed=True,
                typed_routes_reviewed=True,complete_route_history_reviewed=True)}
        budget_address=addr(base+706)
        manifest['chains'][-1]['migration_budget']={'address':budget_address,'runtime_hash':HASH,'immutable':True,
            'vault':modules['vault']['address'],'controller':controller,'observed_vault_helper':budget_address,
            'observed_chain_id':cid,'observed_block_number':5000,'observed_block_hash':HASH,
            'review_evidence':dict(proof(),independent=True,aggregate_loss_tested=True,
                compound_not_subsidy_tested=True,callback_price_snapshot_tested=True,local_scope_reviewed=True)}
        bindings={name:modules[name]['address'] for name in ('canonical','nft_canonical','vault_canonical','fees_canonical')}
        pair_address=addr(base+799)
        manifest['chains'][-1]['pair_migration']={'address':pair_address,'runtime_hash':HASH,'immutable':True,
            'migration':modules['migration']['address'],'controller':controller,'vault':modules['vault']['address'],
            'budget':budget_address,'vault_canonical':modules['vault_canonical']['address'],
            'observed_migration_helper':pair_address,'observed_chain_id':cid,'observed_block_number':5000,
            'observed_block_hash':HASH,'active_bucket':0,'active_request':'0x'+'00'*32,'taking_reserves':False,
            'budget_pair_executor':GATE.ZERO,'review_evidence':dict(proof(),independent=True,
                fixed_price_aggregate_loss_tested=True,historical_compound_tested=True,
                unchanged_reward_currencies_tested=True,exact_transient_custody_tested=True,
                composition_epoch_import_tested=True,v3_boundary_reviewed=True,bounded_gas_qualified=True)}
        bindings.update({name+'_owner':modules[owner]['address'] for name,owner in
            (('nft_canonical','nft'),('vault_canonical','vault'),('fees_canonical','fees'))})
        bindings.update(origin_chain_id=1,origin_vault=modules['vault']['address'])
        canonical={'transport':'same_chain_only','remote_activation_enabled':False,'state':0,'settling':False,
            'preparation_active':False,'phase':0,'incoming_source':GATE.ZERO,'observed_chain_id':cid,
            'origin_chain_id':1,'origin_vault':modules['vault']['address'],
            'observed_block_number':5000,'observed_block_hash':HASH,'observed_bindings':bindings,
            'review_evidence':dict(proof(),independent=True,complete_accounting_tested=True,exact_backing_tested=True,
                abort_restoration_tested=True,single_successor_tested=True,late_receipts_tested=True,onward_migration_tested=True)}
        for offset,(name,owner) in enumerate((('royalty_factory','access'),('reward_receiver_factory','fees'))):
            factory_address=addr(base+707+offset);bindings[name]=factory_address
            canonical[name]={'address':factory_address,'runtime_hash':HASH,'immutable':True,
                'owner':modules[owner]['address'],'controller':controller}
        manifest['chains'][-1]['canonical_handoff']=canonical
        if cid==1:manifest['chains'][-1]['nft_inventory']=nft_inventory(manifest['chains'][-1])
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

def external_fixture():
    """Synthetic creator-payment inventory, never actual deployed contracts."""
    manifest=disabled_fixture();chain=manifest['chains'][0];pool=chain['pools'][0]
    bucket=int(GATE.identity([(1,'uint256'),(chain['modules']['vault']['address'],'address'),
        (pool['pool_id'],'bytes32')]),16)
    manifest['economics'].update(reward_model='external_funded_revenue',external_reward_policy={
        'payment_method':'plain_transfers','allocation_timing':'processing_time','owner_weights':'bucket_shares',
        'collective_weights':'equal_activated_nfts','revenue_entitlement':'received_funds_only',
        'source_description':'Discretionary creator payments without a guaranteed share','terms_evidence':proof()})
    receiver={'address':addr(7777),'runtime_hash':HASH,'bucket_id':str(bucket),'home_pool_id':pool['pool_id'],
        'fees':chain['modules']['fees']['address'],'token0':pool['currency0'],'token1':pool['currency1'],
        'wrapped_native':pool['currency0'],'immutable_configuration':True,'upgradeable':False,
        'observed_chain_id':1,'observed_receiver':addr(7777),'observed_fee_receiver':addr(7777),
        'observed_block_number':chain['observed_block']['number'],'observed_block_hash':HASH,
        'observed_total_shares':'1000000000000000000000',
        'review_evidence':dict(proof(),independent=True,reviewer='Synthetic independent receiver reviewer'),
        'wrapper_review':{'address':pool['currency0'],'runtime_hash':HASH,'upgradeable':False,
            'conversion':'deposit:exact_1_to_1','evidence':proof()}}
    receiver['observed_bindings']={key:receiver[key] for key in ('fees','bucket_id','token0','token1','wrapped_native')}
    chain['external_rewards']={'receiver_count':1,'observation_evidence':proof(),'receivers':[receiver]}
    return manifest

def onward_fixture():
    manifest=fixture();third=copy.deepcopy(manifest['chains'][1]);third['chain_id']=3
    third['providers'][0]['integration_evidence']['chain_id']=3
    third['activation_assets']['observed_chain_id']=3
    third['activation_entry']['observed_chain_id']=3
    third['migration_budget']['observed_chain_id']=3
    third['pair_migration']['observed_chain_id']=3
    third['canonical_handoff']['observed_chain_id']=3
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

class CanonicalHandoffConfigTests(unittest.TestCase):
    def setUp(self):self.config=disabled_fixture()
    def blocked(self,code):
        result=GATE.validate(self.config,expected_commit=COMMIT,now=NOW)
        self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
        self.assertIn(code,[issue['code'] for issue in result['issues']])
    def test_missing_canonical_inventory_is_rejected(self):
        del self.config['chains'][0]['canonical_handoff'];self.blocked('canonical.transport')
    def test_frozen_importing_retired_cancelled_and_boolean_states_are_rejected(self):
        for state in (1,2,3,4,False):
            with self.subTest(state=state):
                self.config=disabled_fixture();self.config['chains'][0]['canonical_handoff']['state']=state
                self.blocked('canonical.lifecycle')
    def test_remote_override_is_rejected(self):
        self.config['chains'][0]['canonical_handoff']['remote_activation_enabled']=True
        self.blocked('canonical.transport')
    def test_wrong_owner_or_bound_helper_is_rejected(self):
        for field in ('canonical','nft_canonical','nft_canonical_owner','vault_canonical_owner','fees_canonical_owner'):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.config['chains'][0]['canonical_handoff']['observed_bindings'][field]=addr(99999)
                self.blocked('canonical.binding')
    def test_stale_canonical_observation_is_rejected(self):
        self.config['chains'][0]['canonical_handoff']['observed_block_number']=4999
        self.blocked('canonical.observation')
    def test_internal_review_cannot_replace_independent_review(self):
        self.config['chains'][0]['canonical_handoff']['review_evidence']['independent']=False
        self.blocked('canonical.review')
    def test_missing_onward_and_abort_evidence_are_rejected(self):
        for key in ('abort_restoration_tested','onward_migration_tested','exact_backing_tested'):
            with self.subTest(key=key):
                self.config=disabled_fixture();del self.config['chains'][0]['canonical_handoff']['review_evidence'][key]
                self.blocked('canonical.review')
    def test_factory_cannot_alias_module_or_mint_recipient(self):
        chain=self.config['chains'][0];factory=chain['canonical_handoff']['royalty_factory']
        chain['constructor']['mint_proceeds_recipient']=factory['address'];self.blocked('canonical.factory')
        self.config=disabled_fixture();chain=self.config['chains'][0]
        chain['canonical_handoff']['royalty_factory']['address']=chain['modules']['vault']['address']
        self.blocked('canonical.factory')
    def test_genesis_cannot_have_previous_source(self):
        self.config['chains'][0]['canonical_handoff']['incoming_source']=addr(99999);self.blocked('canonical.origin')
    def test_successor_requires_retired_source_and_backing_evidence(self):
        canonical=self.config['chains'][0]['canonical_handoff'];canonical.update(phase=5,incoming_source=addr(99999))
        self.blocked('canonical.activation')
        canonical['activation_evidence']=dict(proof(),kind='atomic_same_chain_canonical_activation',
            source_permanently_retired=True,all_backing_verified=True,
            origin_chain_id=canonical['origin_chain_id'],origin_vault=canonical['origin_vault'])
        result=GATE.validate(self.config,expected_commit=COMMIT,now=NOW)
        self.assertEqual(result['issues'],[]);self.assertFalse(result['deployment_authorized'])
    def test_successor_creator_bucket_uses_preserved_origin_vault(self):
        self.config=external_fixture();chain=self.config['chains'][0];canonical=chain['canonical_handoff']
        canonical.update(phase=5,incoming_source=addr(99999),origin_vault=addr(88888))
        canonical['observed_bindings']['origin_vault']=canonical['origin_vault']
        canonical['activation_evidence']=dict(proof(),kind='atomic_same_chain_canonical_activation',
            source_permanently_retired=True,all_backing_verified=True,origin_chain_id=1,origin_vault=addr(88888))
        receiver=chain['external_rewards']['receivers'][0]
        bucket=int(GATE.identity([(1,'uint256'),(addr(88888),'address'),(receiver['home_pool_id'],'bytes32')]),16)
        receiver['bucket_id']=str(bucket);receiver['observed_bindings']['bucket_id']=str(bucket)
        self.assertEqual(GATE.validate(self.config,expected_commit=COMMIT,now=NOW)['issues'],[])
        canonical['observed_bindings']['origin_vault']=chain['modules']['vault']['address']
        self.blocked('canonical.lineage')
    def test_malformed_lineage_and_missing_inventory_fail_without_exception(self):
        for value in (None,[],{'origin_chain_id':-1,'origin_vault':'bad'}):
            with self.subTest(value=value):
                self.config=external_fixture();self.config['chains'][0]['canonical_handoff']=value
                self.blocked('canonical.transport')
    def test_boolean_observed_origin_chain_is_rejected(self):
        self.config['chains'][0]['canonical_handoff']['observed_bindings']['origin_chain_id']=True
        self.blocked('canonical.lineage')
    def test_factory_cannot_alias_creator_receiver_even_with_mixed_case(self):
        self.config=external_fixture();chain=self.config['chains'][0]
        address=chain['external_rewards']['receivers'][0]['address']
        chain['canonical_handoff']['royalty_factory']['address']='0x'+address[2:].upper()
        chain['canonical_handoff']['observed_bindings']['royalty_factory']=address.lower()
        self.blocked('reward.custody')

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
    def test_activation_helper_inventory_requires_fixed_registry_binding_and_observation(self):
        for field,value,code in (('registry',addr(999),'activation.binding'),
                ('controller',addr(999),'activation.binding'),('immutable',False,'activation.binding'),
                ('observed_registry_helper',addr(999),'activation.observation'),
                ('observed_block_hash','0x'+'99'*32,'activation.observation')):
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][0]['activation_assets'][field]=value;self.blocked(code)
    def test_activation_helper_policy_and_recovery_review_is_required(self):
        for field in ('independent','add_disable_reenable_tested','active_policies_reviewed','no_claim_or_exit_dependency'):
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][0]['activation_assets']['review_evidence'][field]=False
                self.blocked('activation.review')
    def test_activation_helper_cannot_receive_mint_proceeds_or_alias_nft_helper(self):
        chain=self.config['chains'][0];chain['constructor']['mint_proceeds_recipient']=chain['activation_assets']['address']
        self.blocked('mint.custody')
        self.config=fixture();chain=self.config['chains'][0]
        chain['nft_inventory']['claim_router']['address']=chain['activation_assets']['address'];self.blocked('nft.helper')
    def test_atomic_entry_requires_exact_immutable_registry_source_and_context_review(self):
        for field,value,code in (('registry',addr(999),'entry.binding'),('controller',addr(999),'entry.binding'),
                ('activation_assets',addr(999),'entry.binding'),('immutable',False,'entry.binding'),
                ('observed_registry_entry',addr(999),'entry.observation'),
                ('observed_block_hash','0x'+'99'*32,'entry.observation')):
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][0]['activation_entry'][field]=value;self.blocked(code)
        for field in ('independent','original_source_value_tested','aggregate_loss_budget_tested',
                'callback_owner_context_reviewed','typed_routes_reviewed','complete_route_history_reviewed'):
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][0]['activation_entry']['review_evidence'][field]=False
                self.blocked('entry.review')
    def test_recovery_requires_complete_independent_parking_resume_and_claim_rehearsal(self):
        for field in ('independent','oracle_independent_close_tested','close_only_minimums_tested',
                'governance_pause_nonce_tested','oracle_guarded_resume_tested','parked_rewards_and_migration_tested'):
            with self.subTest(field=field):
                self.config=fixture();self.config['chains'][0]['governance']['parking_rehearsal'][field]=False
                self.blocked('recovery.review')
    def test_atomic_entry_cannot_alias_other_helpers_or_mint_proceeds(self):
        chain=self.config['chains'][0];chain['activation_entry']['address']=chain['activation_assets']['address'];self.blocked('entry.binding')
        self.config=fixture();chain=self.config['chains'][0];chain['constructor']['mint_proceeds_recipient']=chain['activation_entry']['address']
        self.blocked('mint.custody')
        self.config=fixture();chain=self.config['chains'][0];chain['nft_inventory']['claim_router']['address']=chain['activation_entry']['address']
        self.blocked('nft.helper')
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
            ('minimum_activation_usd18',str(500*10**18),'activation.minimum'),
            ('fee_split_bps',[5000,3000,1000,1000],'reward.split'),('fee_split_bps',[8000,1000,500,499],'reward.split')]:
            with self.subTest(key=key):
                old=self.config['economics'][key];self.config['economics'][key]=value;self.blocked(code);self.config['economics'][key]=old
    def test_collective_allocation_must_use_equal_activated_membership(self):
        for value in ('lifetime_power','bucket_shares','rarity_weights',None):
            with self.subTest(value=value):
                self.config['economics']['collective_weights']=value;self.blocked('reward.collective')
    def test_twenty_unit_basket_dust_limit_is_explicit(self):
        for value in (9,20,True,19.0,None):
            with self.subTest(value=value):
                self.config['economics']['maximum_membership_dust_raw']=value;self.blocked('reward.dust')
    def test_legacy_power_module_is_rejected_even_alongside_membership(self):
        self.config['chains'][0]['modules']['power']={'address':addr(9999),'runtime_hash':HASH}
        self.blocked('binding.legacy')
    def test_pool_bounds_must_allow_hundred_dollar_activation(self):
        self.config['chains'][0]['pools'][0]['minDepositUSD']=str(500*10**18);self.blocked('pool.activation_minimum')
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
    def test_nonzero_delay_mutable_delay_or_unsealed_bootstrap_blocks(self):
        governance=self.config['chains'][0]['governance'];governance['timelock_seconds']=86399;self.blocked('integer.invalid')
        governance.update(timelock_seconds=0,delay_fixed=False);self.blocked('timelock.mutable')
        governance.update(delay_fixed=True,sealed=False,bootstrap=addr(99));self.blocked('seal.incomplete')
    def test_zero_delay_manifest_requires_strict_values_and_current_review(self):
        governance=self.config['chains'][0]['governance']
        for key,bad,code in [('timelock_seconds',True,'integer.invalid'),('timelock_seconds',0.0,'integer.invalid'),
                ('post_seal_routes_timelocked',True,'timelock.routes'),('migration_delay_seconds',False,'migration.delay'),
                ('migration_delay_seconds',172800,'migration.delay')]:
            with self.subTest(key=key,bad=bad):
                old=governance[key];governance[key]=bad;self.blocked(code);governance[key]=old
        for key in ('zero_delay_governance_tested','immediate_migration_tested','no_notice_risk_accepted'):
            review=governance['roles_and_seal_evidence'];review[key]=False
            self.blocked('governance.immediate_review');review[key]=True
        self.assertTrue(self.result()['ready'])
    def test_mint_recipient_cannot_be_protocol_custody(self):
        chain=self.config['chains'][0];chain['constructor']['mint_proceeds_recipient']=chain['modules']['vault']['address'];self.blocked('mint.custody')
    def test_float_boolean_integer_fields_are_not_truncated(self):
        self.config['schema_version']=4.0;self.blocked('schema.unsupported');self.config['schema_version']=4
        for field,value in [('chain_id',True),('chain_id',1.9),('maximum_snapshot_age_seconds',1.0)]:
            with self.subTest(field=field,value=value):
                previous=self.config['chains'][0][field];self.config['chains'][0][field]=value;self.blocked('integer.invalid');self.config['chains'][0][field]=previous
    def test_legacy_per_nft_manifest_is_rejected(self):
        self.config['schema_version']=2;self.blocked('schema.unsupported')
    def test_previous_power_weighted_schema_is_rejected(self):
        self.config['schema_version']=3;self.config['accounting_model']='shared-pools-v1'
        self.blocked('schema.unsupported');self.blocked('accounting.unsupported')
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
    def test_gate_output_declares_current_schema_four(self):
        self.assertEqual(self.result()['schema_version'],4)
    def test_stale_snapshot_and_oracle_round_block(self):
        chain=self.config['chains'][0];chain['observed_block']['timestamp']=NOW-3601;self.blocked('snapshot.stale')
        chain['observed_block']['timestamp']=NOW;feed=chain['tokens'][0]['feed'];feed['updated_at']=NOW-3601;self.blocked('oracle.stale')
        feed.update(updated_at=NOW,answered_in_round=6);self.blocked('oracle.stale')
    def test_wrong_feed_denomination_or_sequencer_grace_blocks(self):
        chain=self.config['chains'][0];feed=chain['tokens'][0]['feed'];feed['denomination']='ETH';self.blocked('oracle.denomination');feed['denomination']='USD'
        chain['sequencer'].update(mode='feed',address=addr(999),runtime_hash=HASH,answer=0,started_at=NOW-3600,
            observed_oracle_feed=addr(999),active_policy_id=HASH,policy_count=1,
            observed_policy={'source':addr(999),'expected_code_hash':HASH,'review_hash':HASH,'bootstrap_admission':True},
            replacement_review=dict(proof(),independent=True,failed_source_replacement_tested=True,zero_bypass_disabled=True))
        self.blocked('sequencer.down')
        chain['sequencer']['started_at']=NOW-3601;self.assertTrue(self.result()['ready'])
        chain['sequencer']['replacement_review']['zero_bypass_disabled']=False;self.blocked('sequencer.recovery')
        chain['sequencer']['replacement_review']['zero_bypass_disabled']=True
        chain['sequencer']['observed_policy']['expected_code_hash']='0x'+'99'*32;self.blocked('sequencer.binding')
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
        uri=ARTWORK_BASE+'caf\u00e9/'
        chain=self.config['chains'][0];chain['constructor']['nft_base_uri']=uri
        chain['nft_inventory']['observed_bindings']['artworkBaseURI']=uri
        publication=chain['nft_inventory']['artwork_publication'];publication['base_uri']=uri
        publication['review_evidence']['base_uri']=uri
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
            self.assertEqual(result.returncode,1);report=json.loads(result.stdout)
            self.assertFalse(report['ready']);self.assertEqual(report['schema_version'],4)

class NFTProductionConfigTests(unittest.TestCase):
    def setUp(self):self.config=disabled_fixture()
    result=ProductionConfigTests.result
    blocked=ProductionConfigTests.blocked
    def inventory(self):return self.config['chains'][0]['nft_inventory']
    def royalty_token(self,number=8800):
        token=addr(number);asset=copy.deepcopy(self.inventory()['royalty_assets']['assets'][0])
        asset.update(address=token,observed_asset=token,kind='erc20',runtime_hash=HASH,non_rebasing=True,transfer_tax=False)
        asset['admission_evidence']['asset']=token
        return asset
    def test_nft_policy_requires_exact_supply_quotas_and_received_royalties(self):
        mutations=(('max_supply',1001),('rarity_counts',[600,299,101]),('initial_rarity_bps',[6000,2999,1001]),
            ('rarity_distribution','independent_per_nft_odds'),('rarity_randomization','fulfillment_order'),
            ('marketplace_royalty_bps',1000),('received_royalty_distribution_bps',8000),('royalty_weights',[1,2,4]),
            ('royalty_weights',[True,2,3]),('royalty_eligibility','all_minted_nfts'),('royalty_entitlement','guaranteed_marketplace_payment'))
        for field,value in mutations:
            with self.subTest(field=field,value=value):
                self.config=disabled_fixture();self.config['nft_policy'][field]=value;self.blocked('nft.policy')
    def test_live_lp_evolution_cannot_use_historical_contributions_or_stale_fallback(self):
        for field,value in (('evolution_basis','lifetime_contribution_usd18'),('unavailable_valuation','dormant')):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.config['nft_policy'][field]=value;self.blocked('nft.policy')
        self.config=disabled_fixture();self.config['nft_policy']['evolution_thresholds_usd18'][-1]=str(100000*10**18)
        self.blocked('nft.evolution')
    def test_helper_bindings_code_and_independent_reviews_are_required(self):
        self.inventory()['royalty_rewards']['nft']=addr(99);self.blocked('nft.binding')
        self.config=disabled_fixture();self.inventory()['metadata_renderer']['controller']=addr(99);self.blocked('nft.binding')
        self.config=disabled_fixture();self.inventory()['royalty_rewards']['address']=self.config['chains'][0]['modules']['vault']['address']
        self.blocked('nft.helper')
        self.config=disabled_fixture();self.inventory()['metadata_renderer']['runtime_hash']=None;self.blocked('hex.invalid')
        self.config=disabled_fixture();self.inventory()['royalty_rewards']['review_evidence']['independent']=False;self.blocked('nft.review')
    def test_mint_recipient_cannot_be_the_royalty_receiver(self):
        self.config['chains'][0]['constructor']['mint_proceeds_recipient']=self.inventory()['royalty_rewards']['address']
        self.blocked('nft.helper')
    def test_claim_router_binding_limit_and_independent_review_are_required(self):
        for field,value in (('nft',addr(99)),('controller',addr(99)),('royalties',addr(99)),('max_claims',33)):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()['claim_router'][field]=value;self.blocked('nft.binding')
        self.config=disabled_fixture();self.inventory()['observed_bindings']['claimRouter']=addr(99);self.blocked('nft.binding')
        self.config=disabled_fixture();self.inventory()['claim_router']['review_evidence']['independent']=False;self.blocked('nft.review')
    def test_royalty_tokens_need_not_be_lp_assets_but_require_their_own_admission(self):
        inventory=self.inventory()['royalty_assets'];inventory['asset_count']=2;inventory['assets'].append(self.royalty_token())
        self.assertNotIn(inventory['assets'][1]['address'],[token['address'] for token in self.config['chains'][0]['tokens']])
        self.assertTrue(self.result()['ready'])
    def test_native_plus_sixteen_erc20_asset_bound_is_enforced(self):
        inventory=self.inventory()['royalty_assets'];inventory['asset_count']=17
        inventory['assets'].extend(self.royalty_token(8800+i) for i in range(16));self.assertTrue(self.result()['ready'])
        inventory['asset_count']=18;inventory['assets'].append(self.royalty_token(9900));self.blocked('nft.royalty_assets')
    def test_royalty_admission_count_history_order_and_getters_must_match(self):
        for field,value in (('asset_count',2),('complete_admission_history',False)):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()['royalty_assets'][field]=value;self.blocked('nft.royalty_assets')
        self.config=disabled_fixture();self.inventory()['royalty_assets']['assets'][0]=self.royalty_token();self.blocked('nft.royalty_assets')
        self.config=disabled_fixture();inventory=self.inventory()['royalty_assets'];inventory['asset_count']=2
        inventory['assets'].append(copy.deepcopy(inventory['assets'][0]));self.blocked('nft.royalty_assets')
        self.config=disabled_fixture();self.inventory()['royalty_assets']['assets'][0]['observed_is_asset']=False;self.blocked('nft.royalty_assets')
    def test_royalty_assets_require_exact_transfer_semantics_and_runtime_code(self):
        for field,value,code in (('non_rebasing',False,'nft.royalty_asset_semantics'),('transfer_tax',True,'nft.royalty_asset_semantics'),
            ('runtime_hash',None,'hex.invalid')):
            with self.subTest(field=field):
                self.config=disabled_fixture();inventory=self.inventory()['royalty_assets'];inventory['asset_count']=2
                token=self.royalty_token();token[field]=value;inventory['assets'].append(token);self.blocked(code)
    def test_royalty_asset_review_covers_actual_chain_authority_and_activation_griefing(self):
        for field,value in (('chain_id',2),('asset',addr(99)),('independent',False),('exact_transfers_reviewed',False),
            ('authority_risks_reviewed',False),('activation_griefing_reviewed',False)):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()['royalty_assets']['assets'][0]['admission_evidence'][field]=value
                self.blocked('nft.royalty_asset_review')
    def test_artwork_base_and_all_seventy_two_content_paths_are_reviewed(self):
        self.inventory()['artwork_publication']['asset_paths'].pop();self.blocked('nft.artwork')
        self.config=disabled_fixture();self.inventory()['artwork_publication']['asset_paths'][0]='missing.png';self.blocked('nft.artwork')
        self.config=disabled_fixture();self.inventory()['artwork_publication']['review_evidence']['independent']=False;self.blocked('nft.artwork_review')
        self.config=disabled_fixture();self.inventory()['artwork_publication']['manifest_sha256']='66'*32;self.blocked('nft.artwork_review')
    def test_artwork_rejects_mutable_http_malformed_content_root_and_missing_slash(self):
        for uri in ('https://example.com/art/','ipfs://synthetic/',ARTWORK_BASE.rstrip('/')):
            with self.subTest(uri=uri):
                self.config=disabled_fixture();self.config['chains'][0]['constructor']['nft_base_uri']=uri;self.blocked('nft.artwork')
    def test_artwork_getter_must_match_reviewed_frozen_content_root(self):
        self.inventory()['observed_bindings']['artworkBaseURI']=ARTWORK_BASE+'other/';self.blocked('nft.binding')
    def test_royalty_receiver_and_rate_getters_must_match(self):
        for field,value in (('royaltyReceiver',addr(99)),('royaltyBps',499),('royaltyBps',True),('metadataRenderer',addr(99))):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()['observed_bindings'][field]=value;self.blocked('nft.binding')
    def test_nft_snapshot_must_match_confirmed_chain_inventory(self):
        for field,value in (('observed_chain_id',2),('observed_block_number',5001),('observed_block_hash','0x'+'33'*32)):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()[field]=value;self.blocked('nft.observation')
    def test_remaining_quotas_and_mint_order_are_conserved(self):
        for field,value in (('MAX_SUPPLY',999),('mintedCount',0),('nextToFinalize',3),
            ('remainingToReveal',1000),('rarityRemaining',[599,299,100]),('rarityRemaining',[601,298,100]),
            ('rarityRemaining',[599,300]),('rarityRemaining',[True,300,100])):
            with self.subTest(field=field,value=value):
                self.config=disabled_fixture();self.inventory()['observed_bindings'][field]=value;self.blocked('nft.quotas')
    def test_complete_reveal_can_exhaust_all_exact_quotas(self):
        self.inventory()['observed_bindings'].update(mintedCount=1000,nextToFinalize=1001,remainingToReveal=0,rarityRemaining=[0,0,0])
        self.assertTrue(self.result()['ready'])
    def test_verified_randomness_cannot_be_replaced_with_admin_entropy(self):
        self.config['nft_policy']['randomness_policy']='admin_seed';self.blocked('nft.policy')
        self.config=disabled_fixture();self.inventory()['randomness']['no_admin_reroll']=False;self.blocked('nft.randomness')
        self.config=disabled_fixture();self.inventory()['randomness']['immutable_provider_configuration']=False;self.blocked('nft.randomness')
    def test_future_request_policy_cannot_claim_provider_rotation_or_full_immutability(self):
        for fields in ({'immutable_configuration':True},
            {'mutable_request_parameters':['requestConfirmations','callbackGasLimit','coordinator']},
            {'mutable_request_parameters':['requestConfirmations','callbackGasLimit','subscriptionId']},
            {'mutable_request_parameters':['callbackGasLimit']},
            {'mutable_request_parameters':True}, {'immutable_provider_configuration':1}):
            with self.subTest(fields=fields):
                self.config=disabled_fixture();self.inventory()['randomness'].update(fields);self.blocked('nft.randomness')
    def test_current_future_request_settings_may_change_with_matching_observation(self):
        self.inventory()['randomness'].update(requestConfirmations=200,callbackGasLimit=10000000)
        self.inventory()['observed_bindings'].update(requestConfirmations=200,callbackGasLimit=10000000)
        self.assertTrue(self.result()['ready'])
    def test_randomness_configuration_and_observed_getters_must_match(self):
        for field,value in (('randomnessConfigured',False),('randomnessCoordinator',addr(99)),('keyHash','0x'+'33'*32),
            ('subscriptionId',8),('requestConfirmations',4),('callbackGasLimit',300001),('nativePayment',True)):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()['observed_bindings'][field]=value;self.blocked('nft.randomness')
    def test_randomness_configuration_must_satisfy_immutable_nft_bounds(self):
        for field,value in (('requestConfirmations',2),('requestConfirmations',201),('callbackGasLimit',199999),('callbackGasLimit',10000001)):
            with self.subTest(field=field,value=value):
                self.config=disabled_fixture();self.inventory()['randomness'][field]=value
                self.inventory()['observed_bindings'][field]=value;self.blocked('integer.invalid')
    def test_randomness_review_must_name_actual_chain_coordinator_and_independent_reviewer(self):
        for field,value in (('independent',False),('kind','internal_review'),('chain_id',4663),('coordinator',addr(99))):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()['randomness']['review_evidence'][field]=value;self.blocked('nft.randomness_review')
    def test_mock_or_wrong_chain_randomness_evidence_cannot_pass_staging(self):
        for field,value in (('kind','mock_model'),('chain_id',4663),('coordinator',addr(99)),('nft',addr(99))):
            with self.subTest(field=field):
                self.config=disabled_fixture();self.inventory()['randomness']['integration_evidence'][field]=value;self.blocked('nft.randomness_staging')
    def test_missing_or_stale_randomness_evidence_is_blocked(self):
        self.inventory()['randomness']['review_evidence']=None;self.blocked('evidence.missing')
        self.config=disabled_fixture();self.inventory()['randomness']['integration_evidence']['commit']='cd'*20;self.blocked('evidence.stale')
        self.config=disabled_fixture();self.inventory()['randomness']['integration_evidence']['fulfilled_request_id']=0;self.blocked('integer.invalid')
    def test_malformed_nft_records_fail_closed_without_exception(self):
        for key,value in (('nft_policy',[]),('nft_policy',None)):
            with self.subTest(key=key,value=value):
                self.config=disabled_fixture();self.config[key]=value;self.assertFalse(self.result()['ready'])
        for value in (None,[],False):
            with self.subTest(inventory=value):
                self.config=disabled_fixture();self.config['chains'][0]['nft_inventory']=value;self.assertFalse(self.result()['ready'])

class ExternalRewardConfigTests(unittest.TestCase):
    def setUp(self):self.config=external_fixture()
    result=ProductionConfigTests.result
    blocked=ProductionConfigTests.blocked
    def inbox(self):return self.config['chains'][0]['external_rewards']['receivers'][0]
    def test_complete_external_inventory_is_consistent_but_never_authorizes_deployment(self):
        before=copy.deepcopy(self.config);result=self.result()
        self.assertEqual(result['issues'],[]);self.assertTrue(result['ready'])
        self.assertFalse(result['deployment_authorized']);self.assertEqual(self.config,before)
    def test_discretionary_funding_does_not_require_an_invented_creator_percentage(self):
        self.assertNotIn('creator_share_bps',self.config['economics']['external_reward_policy'])
        self.assertTrue(self.result()['ready'])
    def test_external_policy_cannot_claim_historical_swap_time_or_guaranteed_revenue(self):
        for key,value in (('allocation_timing','swap_time'),('owner_weights','wallet_balance'),
            ('collective_weights','pool_shares'),('collective_weights','lifetime_power'),('revenue_entitlement','guaranteed_34_percent')):
            with self.subTest(key=key):
                self.config=external_fixture();self.config['economics']['external_reward_policy'][key]=value
                self.blocked('reward.policy')
    def test_external_terms_must_be_exact_release_reviewed(self):
        self.config['economics']['external_reward_policy']['terms_evidence']['commit']='cd'*20
        self.blocked('evidence.stale')
    def test_external_mode_requires_nonempty_canonical_inventory(self):
        for inventory in (None,{'receiver_count':0,'observation_evidence':proof(),'receivers':[]}):
            with self.subTest(inventory=inventory):
                self.config=external_fixture();self.config['chains'][0]['external_rewards']=inventory
                self.blocked('reward.inventory')
    def test_receiver_inventory_count_and_bound_must_match(self):
        for count in (0,2,5,17,True):
            with self.subTest(count=count):
                self.config=external_fixture();self.config['chains'][0]['external_rewards']['receiver_count']=count
                self.assertFalse(self.result()['ready'])
    def test_receiver_count_cannot_exceed_four_bucket_capacity_even_with_matching_length(self):
        external=self.config['chains'][0]['external_rewards']
        external['receiver_count']=5
        external['receivers']=[copy.deepcopy(self.inbox()) for _ in range(5)]
        self.blocked('integer.invalid')
    def test_external_mode_preserves_selected_native_pons_pool_rejection(self):
        self.config['chains'][0]['pools'][0].update(currency0=GATE.ZERO,fee=0,hooks=addr(77))
        self.blocked('pool.hook');self.blocked('pool.assets')
    def test_external_mode_accepts_zero_fee_hookless_erc20_pool_with_funded_receivers(self):
        chain=self.config['chains'][0];pool=chain['pools'][0];pool['fee']=0
        pool['pool_id']=GATE.identity([(pool['currency0'],'address'),(pool['currency1'],'address'),
            (0,'uint24'),(pool['tickSpacing'],'uint24'),(GATE.ZERO,'address')])
        receiver=self.inbox();receiver['home_pool_id']=pool['pool_id']
        receiver['bucket_id']=str(int(GATE.identity([(1,'uint256'),(chain['modules']['vault']['address'],'address'),
            (pool['pool_id'],'bytes32')]),16));receiver['observed_bindings']['bucket_id']=receiver['bucket_id']
        self.assertTrue(self.result()['ready'])
    def test_conventional_fee_model_rejects_zero_core_fee_pool(self):
        self.config=disabled_fixture();self.config['chains'][0]['pools'][0]['fee']=0
        self.blocked('integer.invalid')
    def test_receiver_cannot_point_at_wrong_fee_controller_or_bucket(self):
        self.inbox()['fees']=addr(4444);self.blocked('reward.binding')
        self.config=external_fixture();self.inbox()['bucket_id']='5';self.blocked('reward.bucket')
    def test_receiver_pair_must_match_original_home_pool(self):
        self.inbox()['token1']=addr(5555);self.blocked('reward.assets')
    def test_receiver_duplicate_bucket_or_address_is_rejected(self):
        external=self.config['chains'][0]['external_rewards'];external['receiver_count']=2
        external['receivers'].append(copy.deepcopy(self.inbox()));self.blocked('reward.duplicate')
    def test_receiver_is_separate_from_mint_and_protocol_custody(self):
        self.inbox()['address']=self.config['chains'][0]['constructor']['mint_proceeds_recipient']
        self.blocked('reward.custody')
        self.config=external_fixture();self.inbox()['address']=self.config['chains'][0]['nft_inventory']['royalty_rewards']['address']
        self.blocked('reward.custody')
        self.config=external_fixture();self.inbox()['address']=self.config['chains'][0]['activation_assets']['address']
        self.blocked('reward.custody')
        self.config=external_fixture();self.inbox()['address']=self.config['chains'][0]['activation_entry']['address']
        self.blocked('reward.custody')
    def test_mutable_receiver_or_unreviewed_getters_rejected(self):
        self.inbox()['upgradeable']=True;self.blocked('reward.mutable')
        self.config=external_fixture();self.inbox()['observed_bindings']['fees']=addr(4444)
        self.blocked('reward.observation')
    def test_snapshot_must_match_receiver_and_factory_getters(self):
        for field,value in (('observed_block_number',5001),('observed_block_hash','0x'+'33'*32),
            ('observed_receiver',addr(5555)),('observed_fee_receiver',addr(5555)),('observed_chain_id',2)):
            with self.subTest(field=field):
                self.config=external_fixture();self.inbox()[field]=value;self.blocked('reward.observation')
    def test_receiver_review_cannot_be_internal_or_stale(self):
        self.inbox()['review_evidence']['independent']=False;self.blocked('reward.review')
        self.config=external_fixture();self.inbox()['review_evidence']['commit']='cd'*20
        self.blocked('evidence.stale')
    def test_receiver_requires_positive_observed_share_supply(self):
        self.inbox()['observed_total_shares']=0;self.blocked('integer.invalid')
    def test_wrapper_must_be_one_original_admitted_18_decimal_asset(self):
        self.inbox()['wrapped_native']=addr(5555);self.blocked('reward.wrapper')
        self.config=external_fixture();self.config['chains'][0]['tokens'][0]['decimals']=6
        self.blocked('reward.wrapper')
    def test_wrapper_runtime_or_conversion_or_authority_drift_rejected(self):
        for field,value in (('runtime_hash','0x'+'44'*32),('conversion','deposit:variable_rate'),('upgradeable',True)):
            with self.subTest(field=field):
                self.config=external_fixture();self.inbox()['wrapper_review'][field]=value
                self.blocked('reward.wrapper')
    def test_erc20_only_receiver_has_no_native_wrapper_review(self):
        self.inbox()['wrapped_native']=GATE.ZERO;self.inbox()['observed_bindings']['wrapped_native']=GATE.ZERO
        self.inbox()['wrapper_review']=None;self.assertTrue(self.result()['ready'])
    def test_conventional_only_mode_cannot_hide_receivers(self):
        self.config['economics']['reward_model']='conventional_lp_fees';self.blocked('reward.model')
    def test_satellite_cannot_register_external_receiver(self):
        satellite=copy.deepcopy(fixture()['chains'][1])
        satellite['external_rewards']=copy.deepcopy(self.config['chains'][0]['external_rewards'])
        self.config['chains'].append(satellite);self.blocked('reward.canonical')

class MigrationBudgetConfigTests(unittest.TestCase):
    def setUp(self): self.config=disabled_fixture()
    def check_blocked(self, code):
        result=GATE.validate(self.config, expected_commit=COMMIT, now=NOW)
        self.assertFalse(result['ready'])
        self.assertFalse(result['deployment_authorized'])
        self.assertIn(code, [issue['code'] for issue in result['issues']])
    def test_budget_required_even_when_bridging_disabled(self):
        del self.config['chains'][0]['migration_budget']
        self.check_blocked('migration_budget.binding')
    def test_wrong_vault_controller_or_mutability_rejected(self):
        for field,value in (('vault',addr(990)),('controller',addr(991)),('immutable',False)):
            with self.subTest(field=field):
                self.config=disabled_fixture()
                self.config['chains'][0]['migration_budget'][field]=value
                self.check_blocked('migration_budget.binding')
    def test_helper_observation_must_match_exact_inventory(self):
        for field,value in (('observed_vault_helper',addr(990)),('observed_chain_id',2),
            ('observed_block_number',4999),('observed_block_hash','0x'+'ab'*32)):
            with self.subTest(field=field):
                self.config=disabled_fixture()
                self.config['chains'][0]['migration_budget'][field]=value
                self.check_blocked('migration_budget.observation')
    def test_omitted_independent_budget_review_is_rejected(self):
        for field in ('independent','aggregate_loss_tested','compound_not_subsidy_tested',
            'callback_price_snapshot_tested','local_scope_reviewed'):
            with self.subTest(field=field):
                self.config=disabled_fixture()
                self.config['chains'][0]['migration_budget']['review_evidence'][field]=False
                self.check_blocked('migration_budget.review')
    def test_budget_cannot_alias_modules_entry_or_assets_helper(self):
        for category in ('modules','activation_entry','activation_assets'):
            with self.subTest(category=category):
                self.config=disabled_fixture();chain=self.config['chains'][0]
                other=chain['modules']['vault']['address'] if category=='modules' else chain[category]['address']
                chain['migration_budget']['address']=other
                self.check_blocked('migration_budget.binding')
    def test_budget_cannot_receive_mint_proceeds(self):
        chain=self.config['chains'][0]
        chain['constructor']['mint_proceeds_recipient']=chain['migration_budget']['address']
        self.check_blocked('mint.custody')
    def test_budget_cannot_alias_nft_helper_or_creator_inbox(self):
        chain=self.config['chains'][0]
        chain['nft_inventory']['claim_router']['address']=chain['migration_budget']['address']
        self.check_blocked('nft.helper')
        self.config=external_fixture();chain=self.config['chains'][0]
        chain['external_rewards']['receivers'][0]['address']=chain['migration_budget']['address']
        self.check_blocked('reward.custody')
    def test_budget_mixed_case_cannot_alias_creator_inbox(self):
        self.config=external_fixture();chain=self.config['chains'][0]
        receiver=chain['external_rewards']['receivers'][0]['address']
        chain['migration_budget']['address']='0x'+receiver[2:].upper()
        chain['migration_budget']['observed_vault_helper']=receiver.lower()
        self.check_blocked('reward.custody')

class PairMigrationInventoryTest(unittest.TestCase):
    def setUp(self): self.config=disabled_fixture()
    def blocked(self,code):
        result=GATE.validate(self.config,expected_commit=COMMIT,now=NOW)
        self.assertFalse(result['ready']);self.assertIn(code,[x['code'] for x in result['issues']])
    def test_required_when_bridging_is_disabled(self):
        del self.config['chains'][0]['pair_migration'];self.blocked('pair_migration.binding')
    def test_bindings_and_mutability(self):
        for key,value in (('migration',addr(990)),('controller',addr(991)),('vault',addr(992)),
            ('budget',addr(993)),('vault_canonical',addr(994)),('immutable',False)):
            with self.subTest(key=key):
                self.config=disabled_fixture();self.config['chains'][0]['pair_migration'][key]=value
                self.blocked('pair_migration.binding')
    def test_stale_or_nonempty_atomic_context(self):
        for key,value in (('observed_chain_id',2),('observed_block_number',4999),
            ('observed_migration_helper',addr(995)),('active_bucket',True),('active_bucket',1),
            ('active_request',HASH),('taking_reserves',True),('budget_pair_executor',addr(996))):
            with self.subTest(key=key,value=value):
                self.config=disabled_fixture();self.config['chains'][0]['pair_migration'][key]=value
                self.blocked('pair_migration.observation')
    def test_independent_review_and_gas_are_required(self):
        for key in ('independent','fixed_price_aggregate_loss_tested','historical_compound_tested',
            'unchanged_reward_currencies_tested','exact_transient_custody_tested',
            'composition_epoch_import_tested','v3_boundary_reviewed','bounded_gas_qualified'):
            with self.subTest(key=key):
                self.config=disabled_fixture();self.config['chains'][0]['pair_migration']['review_evidence'][key]=False
                self.blocked('pair_migration.review')
    def test_helper_cannot_alias_other_custody_or_mint_recipient(self):
        for key in ('activation_entry','activation_assets','migration_budget'):
            with self.subTest(key=key):
                self.config=disabled_fixture();chain=self.config['chains'][0]
                chain['pair_migration']['address']=chain[key]['address'];self.blocked('pair_migration.binding')
        self.config=disabled_fixture();chain=self.config['chains'][0]
        chain['constructor']['mint_proceeds_recipient']=chain['pair_migration']['address'];self.blocked('mint.custody')
        self.config=external_fixture();chain=self.config['chains'][0]
        chain['pair_migration']['address']='0x'+chain['external_rewards']['receivers'][0]['address'][2:].upper()
        self.blocked('reward.custody')
