"""Synthetic schema-5 manifests: no record qualifies an actual deployment."""
import copy
import unittest

from zzz_ops import production_v2 as P

NOW = 1_800_000_000
COMMIT = 'ab' * 20
HASH = '0x' + '11' * 32
SHA = '22' * 32


def addr(n): return '0x' + f'{n:040x}'


def proof(**kwargs):
    return dict({'status':'passed','commit':COMMIT,'sha256':SHA,
        'reference':'synthetic-inventory-fixture.json','independent':True},**kwargs)


def fixture():
    """Fully consistent public-data fixture, explicitly not live evidence."""
    modules = {role:{'address':addr(i+100),'runtime_hash':HASH,'observed_runtime_hash':HASH,
        'immutable':True,'review_evidence':proof()} for i,role in enumerate(P.MODULES)}
    helpers = {role:{'address':addr(i+1000),'runtime_hash':HASH,'observed_runtime_hash':HASH,
        'immutable':True,'review_evidence':proof()} for i,role in enumerate(P.HELPERS)}
    for role in ('lp_converter','royalty_converter'): helpers[role]['bindings'] = {'wrapper':P.ZERO}
    access = modules['access']['address']; nft = modules['nft']['address']; vault = modules['vault']['address']
    def bound(**kwargs):
        return proof(chain_id=4663,block_number=100,block_hash=HASH,deployment=access,**kwargs)
    deps = {role:{'address':address,'runtime_hash':runtime,'observed_runtime_hash':runtime,
        'bindings':{},'observed_bindings':{},'authority_review':proof(
            proxy_configuration_reviewed=True,upgrade_authorities_reviewed=True)}
        for role,(address,runtime) in P.NATIVE_DEPENDENCIES.items()}
    for role,bindings in (('position_manager',{'poolManager':deps['pool_manager']['address'],
        'permit2':deps['permit2']['address']}),('state_view',{'poolManager':deps['pool_manager']['address']})):
        deps[role].update(bindings=bindings,observed_bindings=dict(bindings))
    deps['zzz'].update(burn_model='burn(uint256):exact_local_supply_reduction',burn_evidence=proof())
    tokens = []
    for i,(asset,runtime,answer) in enumerate(((P.ZERO,None,2000*10**8),
        (deps['zzz']['address'],deps['zzz']['runtime_hash'],10**8))):
        feed = {'source':addr(5000+i),'runtime_hash':HASH,'observed_runtime_hash':HASH,
            'denomination':'USD','decimals':8,'maximum_age_seconds':3600,'answer':answer,
            'updated_at':NOW-30,'round_id':2,'answered_in_round':2,
            'review_evidence':proof(independent_price_source=True,depeg_and_manipulation_reviewed=True,
                chain_id=4663,asset=asset,source=addr(5000+i),runtime_hash=HASH)}
        feed['observed_oracle_feed'] = {'source':feed['source'],'maxAge':3600,'feedDecimals':8,'assetDecimals':18}
        tokens.append({'address':asset,'kind':'native' if asset == P.ZERO else 'erc20',
            'runtime_hash':runtime,'observed_runtime_hash':runtime,'decimals':18,'observed_decimals':18,
            'non_rebasing':True,'transfer_tax':False,'feed':feed})
    pool = {'currency0':P.ZERO,'currency1':deps['zzz']['address'],'fee':10020,'tickSpacing':200,
        'hooks':P.ZERO,'depositsEnabled':True,'operationsEnabled':True,'rangeBps':5000,
        'triggerBps':1000,'maxSpotDeviationBps':100,'maxSlippageBps':200,'minRebalanceInterval':600,
        'minDepositUSD':10**18,'maxPositionUSD':1_000_000*10**18}
    pool['pool_id'] = P.identity([(pool[k],typ) for k,typ in
        (('currency0','address'),('currency1','address'),('fee','uint24'),('tickSpacing','uint24'),('hooks','address'))])
    pool['observed_config'] = {key:pool[key] for key in P.POOL_FIELDS}
    pool['observed_accounting'] = {'currency0':P.ZERO,'currency1':deps['zzz']['address']}
    pool.update(slot0={'sqrt_price_x96':2**96,'tick':0,'protocol_fee':0,'lp_fee':10020},
        liquidity=10**18,review_evidence=bound(kind='principal_pool_qualification'))
    chain = {'chain_id':4663,'genesis_hash':'0x'+'33'*32,
        'observed_block':{'number':100,'hash':HASH,'timestamp':NOW},
        'maximum_snapshot_age_seconds':600,'minimum_confirmations':1,
        'observation':{'chain_id':4663,'genesis_hash':'0x'+'33'*32,'block_number':100,
            'block_hash':HASH,'observed_head':102,'complete':True,'errors':[]},
        'modules':modules,'helpers':helpers,'dependencies':deps,'tokens':tokens,
        'constructor':{'canonical_chain_id':4663,'mint_proceeds_recipient':addr(7000),
            'maximum_buyback_usd18':str(1000*10**18),'nft_base_uri':'ipfs://bafy'+'a'*50+'/',
            'recipient_payment_evidence':proof()},'operating_buyback_usd18':str(500*10**18),
        'native_accounting':{'version':2,'asset':P.ZERO,'decimals':18,'runtime_hash':None,
            'canonical_schema':P.CANONICAL_SCHEMA,'wrapper_independent':True,
            'eth_weth_principal_boundary':False,'legacy_v1_import':False},
        'execution_loss_policy':{'contribution_bps':100,'maintenance_bps':300,'lp_conversion_bps':100,
            'royalty_conversion_bps':100,'hard_maximum_bps':1000,'gas_separate':True},
        'sequencer':{'mode':'not_applicable','address':P.ZERO,'review_evidence':proof()},
        'pools':[pool],'contribution_pool':pool['pool_id'],
        'canonical_handoff':{'transport':'same_chain_only','remote_activation_enabled':False,'state':0,
            'phase':0,'settling':False,'preparation_active':False,'incoming_source':P.ZERO,
            'origin_chain_id':4663,'origin_vault':vault,'review_evidence':bound(kind='native_canonical_handoff_review')},
        'custody':{'cross_chain_enabled':False,'pending_principal_count':0,'pending_royalty_custody_count':0,
            'recipient_trust_accepted':True,'normal_floors_preserved':True,'raw_exit_separately_approved':True,
            'review_evidence':bound(kind='governed_custody_qualification')},
        'inventory_history':{'complete':True,'evidence':bound(kind='complete_deployment_inventory')},
        'activation_sources':[],'conversion_routes':[],'services':{},
        'governance':{'multisig':addr(8000),'signers':[addr(8001),addr(8002)],'threshold':2,
            'proposers':[addr(8000)],'executors':[P.ZERO],'keeper':addr(8003),'guardian':addr(8004),
            'timelock_seconds':0,'sealed':True,'bootstrap':P.ZERO,'role_history_complete':True,
            'review_evidence':bound(kind='immediate_governance_review',no_notice_risk_accepted=True,
                loss_limit_authority_reviewed=True,all_roles_inventoried=True)}}
    chain['governance']['observed_roles'] = {'proposers':[addr(8000)],'executors':[P.ZERO],
        'cancellers':[addr(8000)],'keeper':addr(8003),'keeper_enabled':True,'guardian':addr(8004),
        'guardian_enabled':True,'controller_admin':True}
    chain['observed_modules'] = {role:modules[role]['address'] for role in P.MODULES if role != 'access'}
    chain['observed_modules'].update({role:P.ZERO for role in P.RETIRED_MODULES})
    for i,token in enumerate(tokens):
        asset = token['address']
        ap = {'token':asset,'enabled':True,'expectedCodeHash':P.NATIVE_HASH if asset == P.ZERO else token['runtime_hash'],
            'reviewHash':'0x'+SHA,'decimals':18,'poolAdmission':True}
        fields = (('token','address'),('enabled','bool'),('expectedCodeHash','bytes32'),
            ('reviewHash','bytes32'),('decimals','uint8'),('poolAdmission','bool'))
        pid = P.identity([(helpers['activation_assets']['address'],'address'),(i,'uint256')]+[(ap[k],t) for k,t in fields])
        chain['activation_sources'].append({'pool_id':pool['pool_id'],'source_asset':asset,
            'asset_policy_id':pid,'asset_policy_ordinal':i,'observed_asset_policy_count':2,
            'asset_policy':ap,'observed_asset_policy':dict(ap),'observed_asset_policy_id':pid,
            'observed_asset_policy_ordinal_id':pid,'enabled':True,'route_kind':0,'route_id':P.ZERO_HASH,
            'review_evidence':bound(kind='activation_source_qualification',source_asset=asset,pool_id=pool['pool_id'],
                asset_policy_id=pid,route_kind=0,route_id=P.ZERO_HASH,
                activation_assets=helpers['activation_assets']['address'],entry=helpers['activation_entry']['address'],
                current_loss_bps=100)})
    for role in ('lp','royalty'):
        policy = {'source':deps['zzz']['address'],'output':P.ZERO,'currency0':P.ZERO,
            'currency1':deps['zzz']['address'],'fee':500,'tickSpacing':10,'hooks':P.ZERO,
            'poolManager':deps['pool_manager']['address'],'stateView':deps['state_view']['address'],
            'sourceCodeHash':deps['zzz']['runtime_hash'],'outputCodeHash':P.NATIVE_HASH,
            'poolManagerCodeHash':deps['pool_manager']['runtime_hash'],
            'stateViewCodeHash':deps['state_view']['runtime_hash'],'reviewHash':'0x'+SHA}
        parent = helpers[role+'_converter']['address']; executor = helpers[role+'_v4_executor']['address']
        rid = P.identity([(P.V4_DOMAIN,'bytes32'),(4663,'uint256'),(executor,'address'),(parent,'address')]+
            [(policy[k],typ) for k,typ in P.V4_FIELDS])
        venue_pool = P.identity([(policy[k],typ) for k,typ in
            (('currency0','address'),('currency1','address'),('fee','uint24'),('tickSpacing','uint24'),('hooks','address'))])
        execution = bound(kind='route_staged_execution',execution_loss_bps=5,network_gas_separate=True,
            parent=parent,executor=executor,route_id=rid,source_asset=policy['source'],output_asset=P.ZERO,
            current_loss_bps=100,full_operation_simulated=True,fee_configuration={'lp_fee':500,'protocol_fee':0})
        chain['conversion_routes'].append({'role':role,'source_asset':policy['source'],'route_kind':2,
            'route_id':rid,'enabled':True,'observed_enabled':True,'observed_kind':2,'observed_exists':True,
            'policy':policy,'observed_policy':dict(policy),'profile':'v4_native',
            'review_evidence':proof(),'execution_evidence':execution,
            'venue_observation':{'pool_id':venue_pool,'poolManager':policy['poolManager'],
                'stateView':policy['stateView'],'slot0':{'sqrt_price_x96':2**96,'tick':0,'protocol_fee':0,'lp_fee':500},
                'liquidity':10**18}})
    vrf = {'coordinator':addr(9000),'runtime_hash':HASH,'observed_runtime_hash':HASH,'keyHash':'0x'+'44'*32,
        'subscriptionId':7,'requestConfirmations':3,'callbackGasLimit':300000,'nativePayment':False,
        'immutable_provider_configuration':True,'mutable_request_parameters':['requestConfirmations','callbackGasLimit'],
        'no_admin_reroll':True}
    vrf_scope = dict(chain_id=4663,coordinator=vrf['coordinator'],nft=nft,keyHash=vrf['keyHash'],
        subscriptionId=7,nativePayment=False)
    vrf['review_evidence'] = proof(kind='verified_randomness_coordinator_review',**vrf_scope)
    vrf['integration_evidence'] = bound(kind='coordinator_staged_randomness',coordinator=vrf['coordinator'],
        nft=nft,keyHash=vrf['keyHash'],subscriptionId=7,nativePayment=False,
        requestConfirmations=3,callbackGasLimit=300000,fulfilled_request_id=1,finalized_token_id=123,
        original_request_recovery_tested=True)
    royalty_asset = {'address':P.ZERO,'observed_asset':P.ZERO,'observed_is_asset':True,
        'custody_amount':'0','strategy':'native','review_evidence':proof(outage_isolation_reviewed=True,old_receipts_preserved=True)}
    chain['nft_inventory'] = {'randomness':vrf,
        'observed_bindings':{'royaltyReceiver':helpers['royalty_rewards']['address'],'royaltyBps':500,
            'mintedCount':0,'nextToFinalize':1,'remainingToReveal':1000,'rarityRemaining':[600,300,100]},
        'artwork_publication':{'base_uri':chain['constructor']['nft_base_uri'],'manifest_sha256':SHA,
            'asset_count':len(P.ARTWORK_FILES),'asset_paths':list(P.ARTWORK_FILES),
            'review_evidence':proof(kind='content_addressed_artwork_review',base_uri=chain['constructor']['nft_base_uri'],asset_manifest_sha256=SHA)},
        'royalty_assets':{'complete_admission_history':True,'asset_count':1,'observed_asset_count':1,'assets':[royalty_asset]}}
    chain['reward_assets'] = {'complete_admission_history':True,'asset_count':2,'observed_asset_count':2,
        'assets':[{'address':token['address'],'observed_asset':token['address'],'observed_is_asset':True,
            'review_evidence':proof()} for token in tokens]}
    profiles = {'rpc':'eip1898_hash_pinned_debug_trace','pricing':'independent_usd_native_v2',
        'randomness':'verified_coordinator_two_words','keeper':'native_v2_governed_limits',
        'api':'accounting_v2_routing_v2','metadata':'content_addressed_v2','opensea':'primary_mint_current_nft'}
    for role in P.SERVICES:
        ep = bound(kind=role+'_production_qualification',configuration_sha256=SHA,profile=profiles[role])
        if role == 'keeper': ep.update(crash_recovery_tested=True,off_host_backup_tested=True,nonce_and_pending_recovery_tested=True)
        if role == 'opensea': ep.update(nft=nft,recipient_correct=True,mint_price_wei=50_000_000_000_000_000,vrf_and_royalty_receiver_tested=True)
        chain['services'][role] = {'status':'qualified','profile':profiles[role],'chain_id':4663,
            'controller':access,'configuration_sha256':SHA,'evidence':ep}
        if role == 'opensea': chain['services'][role]['collection_url'] = 'https://opensea.io/collection/synthetic-fixture'
    bindings = P.expected_bindings(chain)
    for category in ('modules','helpers'):
        for role,values in bindings[category].items():
            chain[category][role]['observed_bindings'] = copy.deepcopy(values)
            if category == 'helpers': chain[category][role]['bindings'] = copy.deepcopy(values)
    result = {'schema_version':5,'accounting_version':2,'routing_version':2,'accounting_model':'shared-pools-native-v2',
        'custody_architecture':'governed-v1','release_commit':COMMIT,'canonical_chain_id':4663,
        'economics':{'reward_model':'conventional_lp_fees','mint_price_wei':'50000000000000000',
            'minimum_activation_usd18':str(100*10**18),'minimum_top_up_usd18':str(5*10**18),
            'activation_minimum_basis':'gross_source_input','network_gas_separate':True,
            'fee_split_bps':[8000,1000,500,500],'collective_weights':'equal_activated_nfts','maximum_membership_dust_raw':19},
        'nft_policy':{'max_supply':1000,'rarity_counts':[600,300,100],'initial_rarity_bps':[6000,3000,1000],
            'rarity_distribution':'fixed_quotas_without_replacement','rarity_randomization':'vrf_mint_order_without_replacement',
            'marketplace_royalty_bps':500,'received_royalty_distribution_bps':10000,'royalty_weights':[1,2,3],
            'royalty_eligibility':'activated_nfts_only','royalty_entitlement':'received_funds_only',
            'evolution_basis':'current_attributed_lp_value_usd18','unavailable_valuation':'unavailable',
            'randomness_policy':'verified_coordinator_two_words',
            'evolution_thresholds_usd18':[str(n*10**18) for n in (0,100,1000,10000)],'economic_review_evidence':proof()},
        'evidence':{role:dict(proof(),**({'kind':'external_security_audit','auditor':'Synthetic external reviewer',
            'open_critical':0,'open_high':0} if role == 'independent_audit' else {})) for role in P.EVIDENCE},'chains':[chain]}
    result['evidence']['gas_benchmarks'].update(chain_id=4663,maximum_observed_transaction_gas=12000000,
        reviewed_block_gas_limit=30000000,complete_operating_rehearsal=True)
    result['evidence']['toolchain'].update(solidity_version='0.8.26',evm_version='cancun',normal_size_limits=True,
        constructor_arguments_included=True,all_production_objects=True)
    pool['review_evidence']['configuration_sha256']=P.configuration_hash(P.pool_configuration(chain,pool))
    chain['governance']['review_evidence']['configuration_sha256']=P.configuration_hash(P.governance_configuration(chain))
    from tests_python.dual_price_fixtures import upgrade_inventory
    return upgrade_inventory(result,proof)


def v3_fixture():
    config = fixture(); chain = config['chains'][0]
    wrapper = addr(9100); converter = chain['helpers']['lp_converter']
    token = copy.deepcopy(chain['tokens'][0])
    token.update(address=wrapper,kind='erc20',runtime_hash=HASH,observed_runtime_hash=HASH)
    from tests_python.dual_price_fixtures import rebind_token
    token['price_policy']['ordinal']=len(chain['tokens'])
    rebind_token(chain,token,proof)
    chain['tokens'].append(token)
    for asset in chain['tokens']: asset['price_policy']['observed_policy_count']=len(chain['tokens'])
    for role,value in (('v3_router',addr(9101)),('v3_factory',addr(9102)),('v3_pool',addr(9103))):
        chain['dependencies'][role] = {'address':value,'runtime_hash':HASH,'observed_runtime_hash':HASH,
            'bindings':{},'observed_bindings':{},'authority_review':proof(
                proxy_configuration_reviewed=True,upgrade_authorities_reviewed=True)}
    converter['bindings']['wrapper']=wrapper;converter['observed_bindings']['wrapper']=wrapper
    wp = {'codeHash':HASH,'admin':P.ZERO,'implementation':P.ZERO,'adminOwner':P.ZERO,
        'adminCodeHash':P.ZERO_HASH,'implementationCodeHash':P.ZERO_HASH,'reviewHash':'0x'+SHA}
    converter['observed_wrapper_policy']=dict(wp);converter['wrapper_policy']=dict(wp,review_evidence=proof())
    source = P.NATIVE_DEPENDENCIES['zzz'][0]
    policy = {'source':source,'router':addr(9101),'factory':addr(9102),'pool':addr(9103),
        'fee':500,'sourceCodeHash':P.NATIVE_DEPENDENCIES['zzz'][1],'routerCodeHash':HASH,
        'factoryCodeHash':HASH,'poolCodeHash':HASH,'reviewHash':'0x'+SHA}
    route = chain['conversion_routes'][0]
    rid = P.identity([(policy[key],typ) for key,typ in P.CONVERTER_V3_FIELDS])
    route.update(route_kind=1,observed_kind=1,route_id=rid,policy=policy,observed_policy=dict(policy),
        profile='v3_wrapper_configurable',venue_observation={'factory':addr(9102),'router_factory':addr(9102),
            'factory_pool':addr(9103),'pool_address':addr(9103),'token0':wrapper,'token1':source,
            'fee':500,'liquidity':10**18})
    route['execution_evidence'].update(route_id=rid,executor=converter['address'])
    return config


def range_fixture(enabled=False):
    from zzz_ops.range_policy import fingerprint
    config=fixture(); config['range_policy_version']=1
    chain=config['chains'][0];pool=chain['pools'][0]
    keeper={'enabled':enabled,'narrow_trigger_bps':100 if enabled else 0,
        'widen_trigger_bps':1500 if enabled else 0,'minimum_interval_seconds':600 if enabled else 0,
        'configuration_hash':P.ZERO_HASH,'review_hash':HASH if enabled else P.ZERO_HASH}
    if enabled:
        pool['rangeBps']=5000;pool['observed_config']['rangeBps']=5000
        raw=[f'{int(pool[k],16) if isinstance(pool[k],str) and pool[k].startswith("0x") else int(pool[k]):064x}' for k in P.POOL_FIELDS]
        keeper['configuration_hash']=fingerprint(raw,1)
    pool['range_policy']={'orientation':1,'keeper':keeper}
    pool['observed_range_policy']={**copy.deepcopy(pool['range_policy']),
        'last_change_at':NOW-900 if enabled else 0,'target_half_width_bps':2500 if enabled else 0}
    strategy=chain['modules']['strategy']
    strategy['observed_bindings']['RANGE_POLICY_VERSION']=1
    pool['review_evidence']['configuration_sha256']=P.configuration_hash(P.pool_configuration(chain,pool))
    return config


class ProductionV2Tests(unittest.TestCase):
    def setUp(self): self.config = fixture()
    def result(self): return P.validate(self.config,expected_commit=COMMIT,now=NOW)
    def blocked(self,code):
        result = self.result(); self.assertFalse(result['ready']); self.assertFalse(result['deployment_authorized'])
        self.assertIn(code,{issue['code'] for issue in result['issues']},result['issues'])
    def chain(self): return self.config['chains'][0]

    def test_consistent_synthetic_inventory_is_not_deployment_authorization(self):
        result = self.result(); self.assertTrue(result['ready'],result['issues'])
        self.assertFalse(result['deployment_authorized']); self.assertEqual({},result['blockers'])

    def test_output_separates_local_custody_capability_from_protocol_bridging(self):
        for blocked in (False, True):
            with self.subTest(blocked=blocked):
                self.config = fixture()
                if blocked:
                    self.chain()['custody']['pending_principal_count'] = 1
                result = self.result()
                self.assertEqual(not blocked, result['ready'])
                self.assertIs(result['migration_enabled'], False)
                self.assertIs(result['protocol_bridge_enabled'], False)
                self.assertIs(result['local_pool_move_supported'], True)
                self.assertIs(result['source_chain_custody_handoff_supported'], True)
                self.assertIs(result['deployment_authorized'], False)
                boundary = ' '.join(result['limitations'])
                for phrase in ('legacy protocol-bridge flag', 'same ordered actual currencies',
                               'normal all-ZZZ', 'explicit raw exit', 'no forced return',
                               'remote NFT/reward ledger', 'not transaction authorization'):
                    self.assertIn(phrase, boundary)

    def test_current_schema_does_not_accept_legacy_or_implicit_profiles(self):
        for field,value in (('schema_version',4),('accounting_version',1),('routing_version',True),('custody_architecture','v3')):
            with self.subTest(field=field):
                self.config=fixture();self.config[field]=value;self.blocked('schema.unsupported')

    def test_explicit_range_profile_qualifies_default_disabled_and_bounded_enabled_policy(self):
        for enabled in (False,True):
            with self.subTest(enabled=enabled):
                self.config=range_fixture(enabled)
                self.assertTrue(self.result()['ready'],self.result()['issues'])

    def test_range_profile_blocks_observation_intent_and_policy_mismatch(self):
        for key,value in (('orientation',0),('orientation',True),('last_change_at',NOW+1),
                          ('last_change_at',True),('target_half_width_bps',4999)):
            with self.subTest(key=key,value=value):
                self.config=range_fixture();self.chain()['pools'][0]['observed_range_policy'][key]=value
                self.blocked('range.policy')
        self.config=range_fixture(True)
        pool=self.chain()['pools'][0]
        pool['range_policy']['keeper']['configuration_hash']=HASH
        pool['observed_range_policy']['keeper']['configuration_hash']=HASH
        self.blocked('range.policy')
        for field,value in (('last_change_at',NOW-1),('last_change_at',0),('target_half_width_bps',5000)):
            with self.subTest(field=field,value=value):
                self.config=range_fixture(True)
                self.chain()['pools'][0]['observed_range_policy'][field]=value
                self.blocked('range.policy')
        self.config=range_fixture();self.config['range_policy_version']=0;self.blocked('range.profile')
        self.config=fixture();self.config['range_policy_version']=True;self.blocked('range.profile')

    def test_uint256_string_getter_values_normalize_without_truncation(self):
        chain = self.chain(); values=P.expected_bindings(chain)['modules']['buyback']
        self.assertEqual(1000*10**18,values['maxTradeUSD'])
        chain['nft_inventory']['randomness']['subscriptionId']='7'
        self.assertEqual(7,P.expected_bindings(chain)['modules']['nft']['subscriptionId'])

    def test_approved_runtime_is_not_replaced_by_observation(self):
        self.chain()['modules']['vault']['observed_runtime_hash']='0x'+'99'*32
        self.blocked('runtime.mismatch')

    def test_helper_parent_ledger_and_hard_caps_are_exact(self):
        for role,field,value in (('entry_v4_executor','parent',addr(99)),
            ('lp_converter','ledger',addr(99)),('migration_budget','MAX_LOSS_BPS',1001)):
            with self.subTest(role=role):
                self.config=fixture();self.chain()['helpers'][role]['observed_bindings'][field]=value
                self.blocked('binding.observed')

    def test_all_governed_caps_accept_zero_through_ten_percent(self):
        for value in (0,1000):
            self.config=fixture();chain=self.chain()
            for key in ('contribution_bps','maintenance_bps','lp_conversion_bps','royalty_conversion_bps'):
                chain['execution_loss_policy'][key]=value
            bindings=P.expected_bindings(chain)
            for role,v in bindings['helpers'].items():
                chain['helpers'][role]['bindings']=copy.deepcopy(v);chain['helpers'][role]['observed_bindings']=copy.deepcopy(v)
            for route in chain['conversion_routes']:
                route['execution_evidence']['current_loss_bps']=value
                route['execution_evidence']['execution_loss_bps']=0
            for source in chain['activation_sources']: source['review_evidence']['current_loss_bps']=value
            self.assertTrue(self.result()['ready'],self.result()['issues'])
        self.chain()['execution_loss_policy']['contribution_bps']=1001;self.blocked('integer.invalid')

    def test_bool_cap_is_rejected(self):
        self.chain()['execution_loss_policy']['contribution_bps']=True;self.blocked('loss.type')

    def test_stale_wrong_genesis_or_incomplete_observation_blocks(self):
        for field,value in (('genesis_hash',HASH),('complete',False),('errors',['rpc_failed']),('observed_head',100)):
            with self.subTest(field=field):
                self.config=fixture();self.chain()['observation'][field]=value;self.blocked('observation.incomplete')
        self.config=fixture();self.chain()['observed_block']['timestamp']=NOW-1000;self.blocked('snapshot.stale')

    def test_retired_modules_cannot_be_reintroduced(self):
        self.chain()['observed_modules']['bridge']=addr(99);self.blocked('binding.registry')
        self.config=fixture();self.chain()['modules']['bridge']={};self.blocked('schema.keys')

    def test_native_eth_cannot_be_a_wrapper_or_fake_runtime(self):
        self.chain()['native_accounting']['asset']=addr(99);self.blocked('native.profile')
        self.config=fixture();self.chain()['tokens'][0]['runtime_hash']=HASH;self.blocked('native.identity')

    def test_required_zzz_feed_missing_stale_depegged_or_misbound_blocks(self):
        for field,value in (('answer',0),('updated_at',NOW-4000),('answered_in_round',0)):
            with self.subTest(field=field):
                self.config=fixture();self.chain()['tokens'][1]['price_policy']['sources'][0][field]=value
                self.blocked('pricing.round')
        self.config=fixture();self.chain()['tokens'][1]['price_policy']['observed_policy_id']=HASH
        self.blocked('pricing.binding')

    def test_pool_identity_accounting_flags_and_bounds_are_verified(self):
        for field,value,code in (('pool_id',HASH,'pool.identity'),('hooks',addr(2),'pool.assets'),
            ('maxSlippageBps',1,'pool.guards'),('depositsEnabled',False,'pool.contribution'),
            ('observed_accounting',{'currency0':addr(2),'currency1':addr(3)},'pool.accounting')):
            with self.subTest(field=field):
                self.config=fixture();self.chain()['pools'][0][field]=value;self.blocked(code)

    def test_v4_route_domain_parent_and_policy_cannot_be_swapped(self):
        route=self.chain()['conversion_routes'][0];route['policy']['fee']=501
        self.blocked('route.identity');self.blocked('route.observation')

    def test_native_route_sentinel_and_hook_are_enforced(self):
        self.chain()['conversion_routes'][0]['policy']['outputCodeHash']=HASH;self.blocked('route.runtime_pin')
        self.config=fixture();self.chain()['conversion_routes'][0]['policy']['hooks']=addr(3);self.blocked('route.v4_pair')

    def test_empty_or_disabled_zzz_conversion_does_not_satisfy_eth_product(self):
        self.chain()['conversion_routes']=[];self.blocked('route.lp_eth_required')
        self.config=fixture();r=self.chain()['conversion_routes'][0];r.update(enabled=False,observed_enabled=False)
        self.blocked('route.lp_eth_required')

    def test_route_current_execution_loss_and_scope_are_qualified(self):
        self.chain()['conversion_routes'][0]['execution_evidence']['execution_loss_bps']=101
        self.blocked('route.loss_limit')
        self.config=fixture();self.chain()['conversion_routes'][0]['execution_evidence']['block_hash']='0x'+'88'*32
        self.blocked('evidence.scope')

    def test_source_policy_hash_includes_helper_and_ordinal(self):
        self.chain()['activation_sources'][0]['asset_policy_ordinal']=1;self.blocked('source.policy_id')

    def test_source_must_be_current_policy_and_direct_pair_input(self):
        self.chain()['activation_sources'][0]['observed_asset_policy_id']=HASH;self.blocked('source.policy')
        self.config=fixture();self.chain()['activation_sources'][0]['route_id']=HASH;self.blocked('source.direct')

    def test_role_overlap_requires_acceptance_not_new_onchain_rule(self):
        chain=self.chain();gov=chain['governance'];gov['keeper']=gov['multisig'];gov['observed_roles']['keeper']=gov['keeper']
        self.blocked('decision.pending');gov['overlap_review']='Dedicated key controls reviewed for this shared operator role.'
        gov['review_evidence']['configuration_sha256']=P.configuration_hash(P.governance_configuration(chain))
        self.assertTrue(self.result()['ready'],self.result()['issues'])

    def test_canonical_successor_requires_retirement_and_backing_evidence(self):
        chain=self.chain();chain['canonical_handoff'].update(phase=5,incoming_source=addr(123),origin_vault=addr(124))
        self.blocked('canonical.activation')

    def test_pending_principal_and_royalty_custody_block_release(self):
        self.chain()['custody']['pending_principal_count']=1;self.blocked('custody.release')
        self.config=fixture();self.chain()['nft_inventory']['royalty_assets']['assets'][0]['custody_amount']='1'
        self.blocked('royalty.custody')

    def test_vrf_needs_actual_coordinator_consumer_and_original_recovery(self):
        for field,value in (('coordinator',addr(33)),('nft',addr(33)),('original_request_recovery_tested',False)):
            with self.subTest(field=field):
                self.config=fixture();self.chain()['nft_inventory']['randomness']['integration_evidence'][field]=value
                self.blocked('randomness.integration' if field=='original_request_recovery_tested' else 'randomness.scope')

    def test_artwork_and_royalty_receiver_are_exact(self):
        self.chain()['nft_inventory']['artwork_publication']['asset_paths'].pop();self.blocked('artwork.inventory')
        self.config=fixture();self.chain()['nft_inventory']['observed_bindings']['royaltyReceiver']=addr(99)
        self.blocked('nft.royalty_receiver')

    def test_history_cannot_be_claimed_complete_at_wrong_block(self):
        self.chain()['inventory_history']['evidence']['block_number']=99;self.blocked('evidence.scope')

    def test_missing_services_are_actionable_and_do_not_become_blanket_block(self):
        self.chain()['services']['pricing']['status']='pending';self.blocked('service.pricing')
        self.assertIn('pricing',self.result()['blockers'])

    def test_independent_audit_and_exact_release_evidence_required(self):
        self.config['evidence']['independent_audit']['independent']=False;self.blocked('audit.independent')
        self.config=fixture();self.config['evidence']['native_accounting']['commit']='cd'*20;self.blocked('evidence.stale')

    def test_unchanged_historical_qualification_does_not_need_relabeling(self):
        chain=self.chain()
        for record in (chain['pools'][0]['review_evidence'],chain['governance']['review_evidence'],
            chain['conversion_routes'][0]['execution_evidence'],chain['activation_sources'][0]['review_evidence'],
            chain['services']['keeper']['evidence']):
            record.update(block_number=95,block_hash='0x'+'55'*32)
        self.assertTrue(self.result()['ready'],self.result()['issues'])
        chain['conversion_routes'][0]['execution_evidence']['block_number']=101
        self.blocked('evidence.scope')

    def test_mutable_pool_and_governance_configuration_change_needs_review(self):
        chain=self.chain();pool=chain['pools'][0]
        pool['rangeBps']=4000;pool['observed_config']['rangeBps']=4000
        self.blocked('pool.qualification_scope')
        self.config=fixture();chain=self.chain();gov=chain['governance'];gov['threshold']=1
        self.blocked('authority.qualification_scope')

    def test_route_execution_proof_cannot_name_another_cap_or_helper(self):
        for field,value in (('parent',addr(34)),('executor',addr(34)),('route_id',HASH),
            ('source_asset',addr(34)),('current_loss_bps',101),('full_operation_simulated',False)):
            with self.subTest(field=field):
                self.config=fixture();self.chain()['conversion_routes'][0]['execution_evidence'][field]=value
                self.blocked('route.execution_scope')

    def test_source_qualification_is_exact_not_generic_passed_evidence(self):
        self.chain()['activation_sources'][0]['review_evidence']['asset_policy_id']=HASH
        self.blocked('source.qualification_scope')

    def test_v3_wrapper_profile_has_a_real_consistent_acceptance_path(self):
        self.config=v3_fixture();self.assertTrue(self.result()['ready'],self.result()['issues'])
        self.chain()['helpers']['lp_converter']['observed_wrapper_policy']['codeHash']='0x'+'77'*32
        self.blocked('wrapper.observation')

    def test_v3_wrapper_cannot_claim_unobserved_proxy_configuration(self):
        self.config=v3_fixture();helper=self.chain()['helpers']['lp_converter']
        helper['wrapper_policy']['admin']=addr(3);helper['observed_wrapper_policy']['admin']=addr(3)
        self.blocked('wrapper.proxy')

    def test_observed_route_existence_and_version_cannot_be_guessed(self):
        for field,value in (('observed_exists',False),('observed_kind',1),('observed_kind',True)):
            with self.subTest(field=field):
                self.config=fixture();self.chain()['conversion_routes'][0][field]=value;self.blocked('route.enabled')

    def test_paused_and_legacy_inbox_deployments_are_explicitly_blocked(self):
        self.chain()['modules']['access']['observed_bindings']['paused']=True;self.blocked('binding.observed')
        self.config=fixture();self.chain()['modules']['nft']['observed_bindings']['mintPaused']=True
        self.blocked('binding.observed')
        self.config=fixture();self.chain()['modules']['fees']['observed_bindings']['rewardReceiverCount']=1
        self.blocked('inbox.inventory_unsupported')

    def test_pool_settings_must_allow_five_dollar_growth(self):
        self.chain()['pools'][0]['minDepositUSD']=10*10**18
        self.blocked('pool.activation_minimum')

    def test_sequencer_policy_status_round_and_grace_are_current_observations(self):
        chain=self.chain();seq={'mode':'uptime_feed','address':addr(9300),'runtime_hash':HASH,
            'observed_runtime_hash':HASH,'answer':0,'started_at':NOW-7200,'updated_at':NOW-7000,
            'round_id':2,'answered_in_round':2,'observed_decimals':0,'active_policy_id':HASH,
            'observed_active_policy_id':HASH,'review_evidence':proof()}
        seq['policy']={'source':seq['address'],'expectedCodeHash':HASH,'reviewHash':'0x'+SHA,'bootstrapAdmission':False}
        seq['observed_policy']=dict(seq['policy']);chain['sequencer']=seq
        chain['modules']['oracle']['observed_bindings']['sequencerFeed']=seq['address']
        from tests_python.dual_price_fixtures import rebind_token
        for token in chain['tokens']: rebind_token(chain,token,proof)
        self.assertTrue(self.result()['ready'],self.result()['issues'])
        seq['answer']=1;self.blocked('sequencer.unavailable')
        seq['answer']=0;seq['observed_active_policy_id']=P.ZERO_HASH;self.blocked('sequencer.policy')

    def test_feed_review_cannot_be_reused_for_another_price_source(self):
        self.chain()['tokens'][1]['price_policy']['sources'][0]['review_evidence']['source']=addr(123)
        self.blocked('pricing.source_review')

    def test_changed_directional_protocol_fee_requires_route_requalification(self):
        route=self.chain()['conversion_routes'][0]
        route['venue_observation']['slot0']['protocol_fee']=1000
        self.blocked('route.fee_qualification')
        route['execution_evidence']['fee_configuration']['protocol_fee']=1000
        self.assertTrue(self.result()['ready'],self.result()['issues'])

    def test_production_gas_and_normal_creation_limits_need_scoped_evidence(self):
        self.config['evidence']['gas_benchmarks']['maximum_observed_transaction_gas']=30000000
        self.blocked('gas.qualification')
        self.config=fixture();self.config['evidence']['toolchain']['constructor_arguments_included']=False
        self.blocked('compiler.profile')

    def test_unknown_legacy_fields_cannot_be_ignored(self):
        self.config['migration']={'enabled':True};self.blocked('schema.keys')
        self.config=fixture();self.chain()['transport_policies']=[];self.blocked('schema.keys')

    def test_malformed_nested_inputs_fail_closed_without_exception(self):
        paths = [('chains',0,'contribution_pool'),('chains',0,'conversion_routes',0,'role'),
            ('chains',0,'conversion_routes',0,'route_kind'),('chains',0,'conversion_routes',0,'source_asset'),
            ('chains',0,'activation_sources',0,'source_asset'),('chains',0,'activation_sources',0,'route_id'),
            ('chains',0,'native_accounting'),('chains',0,'modules'),('chains',0,'helpers'),
            ('chains',0,'dependencies'),('chains',0,'tokens'),('chains',0,'pools'),
            ('chains',0,'governance'),('chains',0,'nft_inventory'),('chains',0,'observed_block'),
            ('chains',0,'observation'),('chains',0,'sequencer')]
        for path in paths:
            for bad in (None,[],{},True,-1,'garbage'):
                with self.subTest(path=path,value=bad):
                    self.config=fixture();item=self.config
                    for key in path[:-1]: item=item[key]
                    item[path[-1]]=bad
                    self.assertFalse(self.result()['ready'])


if __name__ == '__main__': unittest.main()
