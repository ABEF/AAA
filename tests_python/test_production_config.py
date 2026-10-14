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
    manifest={'schema_version':1,'release_commit':COMMIT,'canonical_chain_id':1,
        'economics':{'reward_model':'conventional_lp_fees','mint_price_wei':'50000000000000000',
            'minimum_activation_usd18':str(500*10**18),'fee_split_bps':[5000,3000,1000,1000]},
        'evidence':{key:proof() for key in GATE.EVIDENCE},'chains':[],'routes':[]}
    manifest['evidence']['independent_audit'].update(auditor='Synthetic external auditor fixture',
        independent=True,kind='external_security_audit',open_critical=0,open_high=0)
    for cid in (1,2):
        base=cid*1000;controller=addr(base+1)
        modules={name:{'address':addr(base+i+1),'runtime_hash':HASH,'controller':controller}
            for i,name in enumerate(GATE.MODULES)}
        del modules['access']['controller']
        dependencies={name:{'address':addr(base+i+100),'runtime_hash':HASH,'authority_review':proof()}
            for i,name in enumerate(('position_manager','state_view','pool_manager','permit2','zzz','transport'))}
        dependencies['position_manager'].update(pool_manager=dependencies['pool_manager']['address'],permit2=dependencies['permit2']['address'])
        dependencies['state_view']['pool_manager']=dependencies['pool_manager']['address']
        dependencies['zzz'].update(address=addr(base+201),burn_model='burn(uint256):exact_local_supply_reduction',burn_evidence=proof())
        dependencies['transport'].update(provider='Synthetic provider fixture',immutable_endpoint=True,authenticated_delivery=True,
            funded_equivalent_assets=True,nonce_domain_replay_protection=True,finality_and_retries_reviewed=True,integration_evidence=proof())
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
                'maximum_buyback_usd18':str(1000*10**18),'recipient_payment_evidence':proof()},
            'dependencies':dependencies,'tokens':tokens,'sequencer':{'mode':'not_applicable','address':GATE.ZERO,'review':proof()},'pools':[pool]})
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
        item['route_id']=GATE.identity([(item[key],typ) for key,typ in GATE.ROUTE_FIELDS]);return item
    manifest['routes']=[route(1,2,'principal'),route(2,1,'ack'),route(2,1,'reward',0),route(2,1,'reward',1),
        route(2,1,'principal'),route(1,2,'ack')]
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
        self.config['schema_version']=1.0;self.blocked('schema.unsupported');self.config['schema_version']=1
        for field,value in [('chain_id',True),('chain_id',1.9),('maximum_snapshot_age_seconds',1.0)]:
            with self.subTest(field=field,value=value):
                previous=self.config['chains'][0][field];self.config['chains'][0][field]=value;self.blocked('integer.invalid');self.config['chains'][0][field]=previous
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
        transport=self.config['chains'][0]['dependencies']['transport']
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
        third=copy.deepcopy(self.config['chains'][1]);third['chain_id']=3;self.config['chains'].append(third)
        route=copy.deepcopy(self.config['routes'][4]);route.update(sourceChain=2,destinationChain=3,
            destinationAdapter=third['modules']['bridge']['address'],destinationVault=third['modules']['vault']['address'],
            destinationReceiver=third['modules']['receiver']['address'],destinationPool=third['pools'][0]['pool_id'])
        route['route_id']=GATE.identity([(route[key],typ) for key,typ in GATE.ROUTE_FIELDS]);self.config['routes'].append(route)
        self.blocked('evidence.missing');self.blocked('route.home_ack_missing')
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
