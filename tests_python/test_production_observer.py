"""Offline adversarial inventory-observer checks; no provider qualification."""
import copy
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops import production_observer as O
from zzz_ops import production_v2 as P
from tests_python import test_production_v2 as GATE_FIXTURE

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('production_observer_cli', ROOT/'scripts/observe-production-config.py')
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)
HASH = '0x'+'ab'*32
GENESIS = '0x'+'cd'*32
CODE = '0x6000'
RUNTIME = '0x'+O.keccak256(bytes.fromhex(CODE[2:])).hex()


def addr(number):
    return '0x'+format(number, '040x')


def encoded(*values):
    return '0x'+''.join(O._word(v) for v in values)


def selector(signature):
    return '0x'+O.keccak256(signature.encode()).hex()[:8]


def fixture():
    modules = {key: {'address': addr(i+1), 'runtime_hash': RUNTIME} for i, key in enumerate(('access','pools','oracle'))}
    modules['rewards'] = {'address':addr(4),'runtime_hash':RUNTIME}
    modules['nft'] = {'address':addr(5),'runtime_hash':RUNTIME}
    helpers = {key: {'address': addr(i+10), 'runtime_hash': RUNTIME} for i, key in enumerate(
        ('activation_assets','activation_entry','entry_v4_executor','royalty_rewards','lp_converter','royalty_converter'))}
    for role in ('lp_converter','royalty_converter'):
        helpers[role]['bindings'] = {'wrapper':O.ZERO}
    dependencies = {key: {'address': addr(i+20), 'runtime_hash': RUNTIME, 'bindings': {}} for i, key in enumerate(('pool_manager','state_view'))}
    expected = {'modules': {'access': {'isSealed': True, 'bootstrap': O.ZERO, 'canonicalState': 0},
        'pools': {'contributionPool': HASH}, 'oracle': {'access': addr(1)}},
        'helpers': {'activation_assets': {'registry': addr(2)},
        'activation_entry': {'registry': addr(2), 'v4Executor': addr(12)}, 'entry_v4_executor': {'parent': addr(11)}}}
    policy = {'source': addr(30), 'output': O.ZERO, 'currency0': O.ZERO, 'currency1': addr(30), 'fee': 500,
        'tickSpacing': 10, 'hooks': O.ZERO, 'poolManager': addr(20), 'stateView': addr(21),
        'sourceCodeHash': RUNTIME, 'outputCodeHash': '0x'+O.keccak256(b'ZZZ_NATIVE_ETH_V1').hex(),
        'poolManagerCodeHash': RUNTIME, 'stateViewCodeHash': RUNTIME, 'reviewHash': HASH}
    identity = O.keccak256(b'ZZZ_TYPED_V4_ROUTE_V1')+(4663).to_bytes(32,'big')+bytes.fromhex(O._word(addr(12)))+bytes.fromhex(O._word(addr(11)))
    identifier = '0x'+O.keccak256(identity+b''.join(bytes.fromhex(O._word(policy[k])) for k in O.V4_FIELDS)).hex()
    asset = dict(token=O.ZERO, enabled=True, expectedCodeHash=policy['outputCodeHash'], reviewHash=HASH, decimals=18, poolAdmission=False)
    pool = dict(zip(O.POOL_FIELDS, (O.ZERO,addr(30),10020,200,O.ZERO,True,True,2000,500,100,100,600,'100','99999')))
    pool['pool_id'] = HASH
    feed = dict(source=addr(31), runtime_hash=RUNTIME, decimals=8, maximum_age_seconds=3600,
        answer=None, updated_at=None, round_id=None, answered_in_round=None,
        review_evidence={'status':'pending','independent':False})
    chain = {'chain_id': 4663, 'genesis_hash': GENESIS, 'minimum_confirmations': 2,
        'observed_block': {'number':10,'hash':HASH,'timestamp':1000}, 'modules': modules, 'helpers': helpers,
        'dependencies': dependencies, 'tokens': [dict(address=O.ZERO,kind='native',runtime_hash=None,decimals=18,feed=feed)],
        'pools': [pool], 'activation_sources': [dict(pool_id=HASH,source_asset=O.ZERO,asset_policy_id=HASH,asset_policy_ordinal=0,
            asset_policy=asset,enabled=True,route_kind=0,route_id=O.ZERO_HASH)],
        'conversion_routes': [dict(role='entry',source_asset=addr(30),route_kind=2,route_id=identifier,enabled=True,
            policy=policy,review_evidence={'status':'pending','independent':False})],
        'inventory_history': {'complete':False,'evidence':None},
        'reward_assets':{'asset_count':1,'assets':[{'address':O.ZERO}]},
        'nft_inventory':{'royalty_assets':{'asset_count':1,'assets':[{'address':O.ZERO}]},
                         'randomness':{'coordinator':addr(32),'runtime_hash':RUNTIME}},
        'sequencer':{'mode':'not_applicable','address':O.ZERO},
        'governance':{'proposers':[addr(40)],'executors':[O.ZERO],'keeper':addr(41),'guardian':addr(42)}}
    return {'schema_version':5,'review_policy_version':1,'chains':[chain],'release_approved':False}, expected


class FakeRPC:
    def __init__(self, config, expected):
        self.chain = config['chains'][0]
        self.expected = expected
        self.calls = []
        self.fail = None
        self.mutate = None
        self.reorg = False
        self.anchor_reads = 0
        self.overrides = {}

    def call(self, method, params=None):
        self.calls.append((method,params))
        if self.fail is not None and self.fail(method,params):
            raise RuntimeError('https://private.provider/secret-token')
        if method == 'eth_chainId':
            return 4663
        if method == 'eth_getBlockByNumber':
            tag = params[0]
            if tag == 'latest': return dict(number='0xc',hash='0x'+'ef'*32,timestamp='0x3ea')
            if tag == '0x0': return dict(number=tag,hash=GENESIS,timestamp='0x0')
            self.anchor_reads += 1
            digest = '0x'+'ff'*32 if self.reorg and self.anchor_reads > 1 else HASH
            return dict(number=tag,hash=digest,timestamp='0x3e8')
        if method == 'eth_getCode':
            return CODE
        if method != 'eth_call':
            raise AssertionError('Unexpected non-read method')
        target, data = params[0]['to'], params[0]['data']
        if (target,data) in self.overrides:
            return self.overrides[target,data]
        for group in ('modules','helpers'):
            for role, record in self.chain[group].items():
                if target != record['address']: continue
                for getter, value in self.expected[group].get(role, {}).items():
                    if data == selector(getter+'()'):
                        result = encoded(int(value) if type(value) is bool else value)
                        return self.mutate(target,data,result) if self.mutate else result
        if target == addr(1) and data[:10] == selector('module(bytes32)'):
            for role, identifier in O.MODULE_IDS.items():
                if data[10:] == O.keccak256(identifier.encode()).hex():
                    return encoded(self.chain['modules'].get(role,{}).get('address',O.ZERO))
        if target == addr(1) and data[:10] in (selector('hasRole(bytes32,address)'),selector('keepers(address)'),selector('guardians(address)')):
            return encoded(1)
        if target == addr(31):
            if data == selector('decimals()'): return encoded(8)
            if data == selector('latestRoundData()'): return encoded(1,2000*10**8,999,999,1)
        if target == addr(3) and data[:10] == selector('feeds(address)'):
            return encoded(addr(31),3600,8,18)
        if target == addr(3) and data == selector('activeSequencerPolicy()'): return encoded(HASH)
        if target == addr(3) and data[:10] == selector('sequencerPolicies(bytes32)'):
            return encoded(addr(33),RUNTIME,HASH,0)
        if target == addr(33):
            if data == selector('decimals()'): return encoded(0)
            if data == selector('latestRoundData()'): return encoded(2,1,900,900,2)
        pool = self.chain['pools'][0]
        if target == addr(2) and data[:10] in (selector('get(bytes32)'),selector('accounting(bytes32)')):
            return encoded(*(int(pool[k]) if type(pool[k]) is bool else pool[k] for k in O.POOL_FIELDS))
        if target == addr(10):
            if data[:10] == selector('policies(bytes32)'):
                policy = self.chain['activation_sources'][0]['asset_policy']
                return encoded(*(int(policy[k]) if type(policy[k]) is bool else policy[k] for k in O.ASSET_FIELDS))
            if data[:10] == selector('activePolicy(address)'): return encoded(HASH)
            if data == selector('policyCount()'): return encoded(1)
            if data[:10] == selector('policyAt(uint256)'): return encoded(HASH)
        if target in (addr(4),addr(13)):
            if data == selector('assetCount()'): return encoded(1)
            if data[:10] == selector('assets(uint256)'): return encoded(O.ZERO)
            if data[:10] == selector('isAsset(address)'): return encoded(1)
            if data[:10] == selector('custodyAmount(address)'): return encoded(0)
        if target == addr(5):
            if data[:10] == selector('royaltyInfo(uint256,uint256)'): return encoded(addr(13),500)
            if data == selector('mintedCount()'): return encoded(0)
            if data == selector('nextToFinalize()'): return encoded(1)
            if data == selector('remainingToReveal()'): return encoded(1000)
            if data[:10] == selector('rarityRemaining(uint256)'):
                return encoded([600,300,100][int(data[10:],16)])
        route = self.chain['conversion_routes'][0]
        if target in (addr(11),addr(12)):
            if data[:10] == selector('routeEnabled(bytes32)'): return encoded(int(route['enabled']))
            if data[:10] == selector('routeKind(bytes32)'): return encoded(2)
            if data[:10] == selector('routeExists(bytes32)'): return encoded(1)
            if data[:10] in (selector('v4Route(bytes32)'),selector('route(bytes32)'),selector('validate(bytes32)')):
                return encoded(*(route['policy'][k] for k in O.V4_FIELDS))
        if target == addr(21):
            if data == selector('poolManager()'): return encoded(addr(20))
            if data[:10] == selector('getSlot0(bytes32)'):
                return encoded(1 << 96,0,0,10020 if data[10:] == HASH[2:] else 500)
            if data[:10] == selector('getLiquidity(bytes32)'): return encoded(123456)
        raise AssertionError('Unknown fixture call '+target+' '+data[:10])


class ProductionObserverTests(unittest.TestCase):
    def run_observer(self, config=None, expected=None, rpc=None):
        if config is None: config, expected = fixture()
        rpc = rpc or FakeRPC(config,expected)
        with patch('zzz_ops.production_v2.expected_bindings',return_value=expected):
            result = O.observe(config,rpc)
        return result,rpc

    def test_complete_pinned_native_v4_observation_preserves_reviews_and_input(self):
        config, expected = fixture()
        before = copy.deepcopy(config)
        result, rpc = self.run_observer(config,expected)
        chain = result['chains'][0]
        self.assertTrue(chain['observation']['complete'], chain['observation']['errors'])
        self.assertEqual(config,before)
        self.assertFalse(result['release_approved'])
        self.assertEqual(chain['conversion_routes'][0]['review_evidence'],before['chains'][0]['conversion_routes'][0]['review_evidence'])
        self.assertFalse(chain['inventory_history']['complete'])
        self.assertIsNone(chain['tokens'][0]['observed_runtime_hash'])
        self.assertEqual(chain['tokens'][0]['observed_decimals'],18)
        self.assertEqual(chain['tokens'][0]['feed']['answer'],'200000000000')
        for method, params in rpc.calls:
            self.assertIn(method,O.READ_METHODS)
            if method in ('eth_call','eth_getCode'):
                self.assertEqual(params[-1],{'blockHash':HASH,'requireCanonical':True})
            if method == 'eth_call':
                self.assertEqual(params[0]['gas'],hex(O.MAX_GETTER_GAS))

    def test_wrong_chain_genesis_hash_and_insufficient_depth_abort(self):
        for change in ('chain','genesis','hash','confirmations'):
            with self.subTest(change=change):
                config, expected = fixture()
                if change == 'chain': config['chains'][0]['chain_id'] = 1
                elif change == 'genesis': config['chains'][0]['genesis_hash'] = HASH
                elif change == 'hash': config['chains'][0]['observed_block']['hash'] = GENESIS
                else: config['chains'][0]['minimum_confirmations'] = 3
                with self.assertRaises(ValueError): self.run_observer(config,expected)

    def test_reorg_discards_whole_observation(self):
        config, expected = fixture(); rpc = FakeRPC(config,expected); rpc.reorg = True
        with self.assertRaisesRegex(ValueError,'anchor changed'):
            self.run_observer(config,expected,rpc)

    def test_failed_getter_is_unavailable_never_zero_and_failure_is_sanitized(self):
        config, expected = fixture(); rpc = FakeRPC(config,expected)
        rpc.fail = lambda method, params: method == 'eth_call' and params[0]['data'] == selector('isSealed()')
        result,_ = self.run_observer(config,expected,rpc)
        chain = result['chains'][0]
        self.assertIsNone(chain['modules']['access']['observed_bindings']['isSealed'])
        self.assertFalse(chain['observation']['complete'])
        self.assertNotIn('secret-token',json.dumps(result))

    def test_noncanonical_boolean_and_address_fail_closed(self):
        for getter, bad in [('isSealed',2),('bootstrap',1 << 160)]:
            config, expected = fixture(); rpc = FakeRPC(config,expected)
            rpc.mutate = lambda target,data,result: encoded(bad) if data == selector(getter+'()') else result
            result,_ = self.run_observer(config,expected,rpc)
            self.assertIsNone(result['chains'][0]['modules']['access']['observed_bindings'][getter])
            self.assertFalse(result['chains'][0]['observation']['complete'])

    def test_runtime_mismatch_does_not_replace_approved_pin(self):
        config, expected = fixture(); config['chains'][0]['modules']['access']['runtime_hash'] = HASH
        result,_ = self.run_observer(config,expected)
        record = result['chains'][0]['modules']['access']
        self.assertEqual(record['runtime_hash'],HASH)
        self.assertEqual(record['observed_runtime_hash'],RUNTIME)
        self.assertFalse(result['chains'][0]['observation']['complete'])

    def test_disabled_v4_route_is_read_without_calling_validate(self):
        config, expected = fixture(); config['chains'][0]['conversion_routes'][0]['enabled'] = False
        result,rpc = self.run_observer(config,expected)
        self.assertTrue(result['chains'][0]['observation']['complete'])
        self.assertFalse(any(method == 'eth_call' and p[0]['data'][:10] == selector('validate(bytes32)') for method,p in rpc.calls))

    def test_changed_route_identity_is_reported(self):
        config, expected = fixture(); config['chains'][0]['conversion_routes'][0]['route_id'] = HASH
        result,_ = self.run_observer(config,expected)
        self.assertIn('route.identity',[e['code'] for e in result['chains'][0]['observation']['errors']])

    def test_current_sequencer_values_replace_copied_healthy_status(self):
        config,expected=fixture()
        sequence={'mode':'uptime_feed','address':addr(33),'runtime_hash':RUNTIME,'decimals':0,
            'answer':0,'started_at':1,'updated_at':1,'round_id':'1','answered_in_round':'1',
            'active_policy_id':HASH,'policy':dict(source=addr(33),expectedCodeHash=RUNTIME,reviewHash=HASH,bootstrapAdmission=False)}
        config['chains'][0]['sequencer']=sequence
        result,_=self.run_observer(config,expected)
        actual=result['chains'][0]['sequencer']
        self.assertEqual(actual['answer'],1)
        self.assertEqual(actual['started_at'],900)
        self.assertEqual(actual['observed_policy'],sequence['policy'])
        rpc=FakeRPC(config,expected)
        rpc.fail=lambda method,params: method=='eth_call' and params[0]['to']==addr(33) and params[0]['data']==selector('latestRoundData()')
        failed,_=self.run_observer(config,expected,rpc)
        self.assertIsNone(failed['chains'][0]['sequencer']['answer'])
        self.assertFalse(failed['chains'][0]['observation']['complete'])

    def test_unreadable_governance_role_does_not_reuse_copied_grants(self):
        config,expected=fixture(); rpc=FakeRPC(config,expected)
        config['chains'][0]['governance']['observed_roles']={'proposers':[addr(40)],'controller_admin':True}
        rpc.fail=lambda method,p: method=='eth_call' and p[0]['data'][:10]==selector('hasRole(bytes32,address)')
        result,_=self.run_observer(config,expected,rpc)
        roles=result['chains'][0]['governance']['observed_roles']
        self.assertIsNone(roles['proposers'])
        self.assertIsNone(roles['controller_admin'])
        self.assertFalse(result['chains'][0]['observation']['complete'])

    def test_v3_policy_and_venue_are_observed_separately_from_v4(self):
        config,expected=fixture(); rpc=FakeRPC(config,expected)
        policy=dict(source=addr(30),output=addr(34),router=addr(40),factory=addr(41),pool=addr(42),fee=500,
            routerCodeHash=RUNTIME,factoryCodeHash=RUNTIME,poolCodeHash=RUNTIME,
            sourceCodeHash=RUNTIME,outputCodeHash=RUNTIME,reviewHash=HASH)
        identifier='0x'+O.keccak256(bytes.fromhex(encoded(*(policy[k] for k in O.V3_ENTRY_FIELDS))[2:])).hex()
        config['chains'][0]['conversion_routes']=[dict(role='entry',source_asset=addr(30),route_kind=1,
            route_id=identifier,enabled=True,policy=policy)]
        for sig, value in [('routeKind(bytes32)',encoded(1)),('route(bytes32)',encoded(*(policy[k] for k in O.V3_ENTRY_FIELDS)))]:
            rpc.overrides[addr(11),selector(sig)+identifier[2:]]=value
        for target,sig,value in [(addr(40),'factory()',addr(41)),(addr(42),'factory()',addr(41)),
                (addr(42),'token0()',addr(30)),(addr(42),'token1()',addr(34)),(addr(42),'fee()',500),
                (addr(42),'liquidity()',123)]:
            rpc.overrides[target,selector(sig)]=encoded(value)
        rpc.overrides[addr(41),selector('getPool(address,address,uint24)')+encoded(addr(30),addr(34),500)[2:]]=encoded(addr(42))
        result,_=self.run_observer(config,expected,rpc)
        route=result['chains'][0]['conversion_routes'][0]
        self.assertEqual(route['observed_kind'],1)
        self.assertEqual(route['observed_policy'],policy)
        self.assertEqual(route['venue_observation']['factory_pool'],addr(42))
        self.assertTrue(result['chains'][0]['observation']['complete'],result['chains'][0]['observation']['errors'])

    def test_wrapper_authority_observation_reads_actual_proxy_admin(self):
        config,expected=fixture(); rpc=FakeRPC(config,expected)
        helper=config['chains'][0]['helpers']['lp_converter']; helper['bindings']['wrapper']=addr(50)
        policy=dict(codeHash=RUNTIME,admin=addr(51),implementation=addr(52),adminOwner=addr(53),
            adminCodeHash=RUNTIME,implementationCodeHash=RUNTIME,reviewHash=HASH)
        helper['wrapper_policy']=dict(policy,review_evidence={'status':'pending'})
        rpc.overrides[addr(14),selector('wrapperPolicy()')]=encoded(*policy.values())
        rpc.overrides[addr(51),selector('getProxyAdmin(address)')+O._word(addr(50))]=encoded(addr(51))
        rpc.overrides[addr(51),selector('getProxyImplementation(address)')+O._word(addr(50))]=encoded(addr(52))
        rpc.overrides[addr(51),selector('owner()')]=encoded(addr(53))
        result,_=self.run_observer(config,expected,rpc)
        actual=result['chains'][0]['helpers']['lp_converter']
        self.assertEqual(actual['observed_wrapper_policy'],policy)
        self.assertEqual(actual['wrapper_policy_observation'],dict(admin=addr(51),implementation=addr(52),adminOwner=addr(53)))
        self.assertEqual(helper['wrapper_policy']['review_evidence'],{'status':'pending'})

    def test_rpc_method_allowlist_rejects_writes_before_transport(self):
        rpc = FakeRPC(*fixture())
        with self.assertRaises(ValueError): O.Observer(rpc,{}).request('eth_sendTransaction',[{}])
        self.assertEqual(rpc.calls,[])

    def test_numeric_and_dynamic_abi_boundaries(self):
        for value in ('0x00','0x',True,1.0,'-1'):
            with self.subTest(value=value),self.assertRaises(ValueError): O._quantity(value)
        for value in (True,1.0,'00','-1'):
            with self.subTest(value=value),self.assertRaises(ValueError): O._uint(value)
        text = b'ipfs://reviewed/'
        raw = encoded(32,len(text))+text.hex()+'00'*((32-len(text)%32)%32)
        self.assertEqual(O._string(raw),text.decode())
        for raw in ('0x',encoded(64,0),encoded(32,4097),encoded(32,0,1)):
            with self.subTest(raw=raw),self.assertRaises(ValueError): O._string(raw)

    def test_duplicate_json_and_file_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'input.json'; path.write_text('{"same":1,"same":2}')
            with self.assertRaises(ValueError): O.read_manifest(path)
            for text in ('{"number":NaN}','{"number":Infinity}','{"number":-Infinity}'):
                path.write_text(text)
                with self.assertRaises(ValueError): O.read_manifest(path)
            path.write_bytes(b' '*33)
            with patch.object(O,'MAX_INPUT_BYTES',32),self.assertRaises(ValueError): O.read_manifest(path)

    def test_failed_atomic_output_preserves_previous_and_removes_temporary(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'result.json'; path.write_text('old')
            with patch.object(O.os,'replace',side_effect=OSError('private-disk-detail')),self.assertRaises(OSError):
                O.write_observation(path,{'safe':True})
            self.assertEqual(path.read_text(),'old')
            self.assertEqual(list(Path(d).iterdir()),[path])

    def test_cli_failure_is_sanitized_and_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            config,expected=fixture(); source=Path(d)/'input.json'; source.write_text(json.dumps(config))
            output=Path(d)/'observed.json'; output.write_text('last successful evidence')
            stderr=io.StringIO()
            with patch.dict(CLI.os.environ,{'POPL_RELEASE_RPC_URL':'https://private.provider/secret-token'}), \
                    patch.object(CLI,'observe',side_effect=RuntimeError('private-secret')),contextlib.redirect_stderr(stderr):
                status=CLI.main(['--config',str(source),'--rpc-env','POPL_RELEASE_RPC_URL','--output',str(output)])
            self.assertEqual(status,1)
            self.assertNotIn('secret',stderr.getvalue())
            self.assertEqual(output.read_text(),'last successful evidence')

    def test_cli_rejects_same_output_secret_env_and_mismatched_anchor_before_rpc(self):
        with tempfile.TemporaryDirectory() as d:
            config,_=fixture(); source=Path(d)/'input.json'; source.write_text(json.dumps(config))
            for extra in (['--output',str(source)], ['--output',str(Path(d)/'out.json'),'--block-number','11','--expected-block-hash',HASH],
                          ['--output',str(Path(d)/'out.json'),'--block-number','10']):
                with patch.object(CLI,'Rpc') as rpc,contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(CLI.main(['--config',str(source),'--rpc-env','POPL_RELEASE_RPC_URL']+extra),1)
                    rpc.assert_not_called()
            with patch.object(CLI,'Rpc') as rpc,contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(CLI.main(['--config',str(source),'--rpc-env','POPL_TEST_PRIVATE_KEY','--output',str(Path(d)/'out.json')]),1)
                rpc.assert_not_called()


class CompositionRPC:
    """Static source-ABI mock for the complete gate fixture, not a live node."""
    def __init__(self, config):
        self.chain = config['chains'][0]
        self.expected = P.expected_bindings(self.chain,range_policy_version=config.get('range_policy_version',0))
        self.calls = []
        self.bad = None
        self.overrides = {}

    def call(self, method, params=None):
        self.calls.append((method,params))
        chain=self.chain; mods=chain['modules']; helpers=chain['helpers']; deps=chain['dependencies']
        if method=='eth_chainId': return 4663
        if method=='eth_getBlockByNumber':
            tag=params[0]
            number=chain['observed_block']['number']+2 if tag=='latest' else int(tag,16)
            return dict(number=hex(number),hash=chain['genesis_hash'] if number==0 else chain['observed_block']['hash'],
                timestamp=hex(0 if number==0 else chain['observed_block']['timestamp']))
        if method=='eth_getCode': return CODE
        if method!='eth_call': raise AssertionError('Non-read observation method')
        target,data=params[0]['to'],params[0]['data']
        if self.bad is not None and self.bad(target,data): raise ValueError('provider-secret')
        if (target,data) in self.overrides: return self.overrides[target,data]
        for group in ('modules','helpers'):
            for role,record in chain[group].items():
                if record['address']!=target: continue
                for getter,value in self.expected[group][role].items():
                    if data!=selector(getter+'()'): continue
                    if getter=='artworkBaseURI':
                        raw=value.encode(); return encoded(32,len(raw))+raw.hex()+'00'*((-len(raw))%32)
                    return encoded(int(value) if type(value) is bool else value)
        for record in deps.values():
            if record['address']==target:
                for getter,value in record['bindings'].items():
                    if data==selector(getter+'()'): return encoded(value)
        if target==mods['access']['address']:
            if data[:10]==selector('module(bytes32)'):
                for role,name in O.MODULE_IDS.items():
                    if data[10:]==O.keccak256(name.encode()).hex(): return encoded(mods.get(role,{}).get('address',O.ZERO))
            if data[:10] in (selector('hasRole(bytes32,address)'),selector('keepers(address)'),selector('guardians(address)')): return encoded(1)
        if target==mods['strategy']['address']:
            for pool in chain['pools']:
                if 'range_policy' not in pool:continue
                metadata=pool['observed_range_policy'];keeper=metadata['keeper']
                if data==selector('rangeOrientation(bytes32)')+O._word(pool['pool_id']):return encoded(metadata['orientation'])
                if data==selector('keeperRangeTarget(bytes32)')+O._word(pool['pool_id']):return encoded(metadata['target_half_width_bps'])
                if data==selector('keeperRangePolicy(bytes32)')+O._word(pool['pool_id']):return encoded(
                    int(keeper['enabled']),keeper['narrow_trigger_bps'],keeper['widen_trigger_bps'],
                    keeper['minimum_interval_seconds'],metadata['last_change_at'],keeper['configuration_hash'],keeper['review_hash'])
        if target==mods['oracle']['address']:
            if data==selector('PRICING_VERSION()'):return encoded(2)
            if data==selector('policyCount()'):return encoded(len(chain['tokens']))
            if data==selector('activeSequencerPolicy()'):return encoded(chain['sequencer'].get('active_policy_id',O.ZERO_HASH))
        for token in chain['tokens']:
            if 'price_policy' in token:
                from zzz_ops import price_policy as D
                record=token['price_policy'];policy=record['policy']
                if target==token['address'] and data==selector('decimals()'):return encoded(token['decimals'])
                for index,role in enumerate(('primary','secondary')):
                    if target==policy[role]['source']:
                        if data==selector('decimals()'):return encoded(policy[role]['feedDecimals'])
                        source=record['sources'][index]
                        if data==selector('latestRoundData()'):return encoded(*(source[key] for key in ('round_id','answer','started_at','updated_at','answered_in_round')))
                if target==mods['oracle']['address']:
                    if data==selector('activePolicy(address)')+O._word(token['address']):return encoded(record['policy_id'])
                    if data==selector('policyAt(uint256)')+O._word(record['ordinal']):return encoded(record['policy_id'])
                    if data==selector('policy(bytes32)')+O._word(record['policy_id']):return encoded(*D.flat(policy))
                    if data==selector('priceBounds(address)')+O._word(token['address']):return encoded(*(record['observed_bounds'][key] for key in ('lower','upper','fingerprint')))
                continue
            feed=token['feed']
            if target==token['address'] and data==selector('decimals()'): return encoded(token['decimals'])
            if target==feed['source']:
                if data==selector('decimals()'): return encoded(feed['decimals'])
                if data==selector('latestRoundData()'): return encoded(feed['round_id'],feed['answer'],feed['updated_at'],feed['updated_at'],feed['answered_in_round'])
            if target==mods['oracle']['address'] and data==selector('feeds(address)')+O._word(token['address']):
                return encoded(feed['source'],feed['maximum_age_seconds'],feed['decimals'],token['decimals'])
        for pool in chain['pools']:
            if target==mods['pools']['address'] and data[:10] in (selector('get(bytes32)'),selector('accounting(bytes32)')) and data[10:]==pool['pool_id'][2:]:
                return encoded(*(int(pool[k]) if type(pool[k]) is bool else pool[k] for k in O.POOL_FIELDS))
        if target==helpers['activation_assets']['address']:
            if data==selector('policyCount()'): return encoded(len(chain['activation_sources']))
            for source in chain['activation_sources']:
                if data==selector('policies(bytes32)')+O._word(source['asset_policy_id']):
                    return encoded(*(int(source['asset_policy'][k]) if type(source['asset_policy'][k]) is bool else source['asset_policy'][k] for k in O.ASSET_FIELDS))
                if data==selector('activePolicy(address)')+O._word(source['source_asset']) or data==selector('policyAt(uint256)')+O._word(source['asset_policy_ordinal']):
                    return encoded(source['asset_policy_id'])
        for key,ledger,inventory in (('reward',mods['rewards']['address'],chain['reward_assets']),
                ('royalty',helpers['royalty_rewards']['address'],chain['nft_inventory']['royalty_assets'])):
            if target!=ledger: continue
            if data==selector('assetCount()'): return encoded(inventory['asset_count'])
            if data[:10]==selector('assets(uint256)'): return encoded(inventory['assets'][int(data[10:],16)]['address'])
            if data[:10]==selector('isAsset(address)'): return encoded(1)
            if key=='royalty' and data[:10]==selector('custodyAmount(address)'): return encoded(0)
        if target==mods['nft']['address']:
            values=chain['nft_inventory']['observed_bindings']
            if data[:10]==selector('royaltyInfo(uint256,uint256)'): return encoded(values['royaltyReceiver'],values['royaltyBps'])
            for getter in ('mintedCount','nextToFinalize','remainingToReveal'):
                if data==selector(getter+'()'): return encoded(values[getter])
            if data[:10]==selector('rarityRemaining(uint256)'): return encoded(values['rarityRemaining'][int(data[10:],16)])
        for route in chain['conversion_routes']:
            parent=helpers[route['role']+'_converter']['address']; executor=helpers[route['role']+'_v4_executor']['address']; rid=route['route_id']
            if target in (parent,executor):
                if data==selector('routeKind(bytes32)')+O._word(rid): return encoded(2)
                if data[:10] in (selector('routeEnabled(bytes32)'),selector('routeExists(bytes32)')) and data[10:]==rid[2:]: return encoded(1)
                if data[:10] in (selector('v4Route(bytes32)'),selector('route(bytes32)'),selector('validate(bytes32)')) and data[10:]==rid[2:]:
                    return encoded(*(route['policy'][k] for k in O.V4_FIELDS))
        if target==deps['state_view']['address']:
            for venue in chain['pools']+[r['venue_observation'] for r in chain['conversion_routes']]:
                pid=venue.get('pool_id')
                if data==selector('getSlot0(bytes32)')+O._word(pid):
                    s=venue['slot0']; return encoded(s['sqrt_price_x96'],s['tick'],s['protocol_fee'],s['lp_fee'])
                if data==selector('getLiquidity(bytes32)')+O._word(pid): return encoded(venue['liquidity'])
        raise AssertionError('Unknown complete-fixture ABI '+target+' '+data[:10])


class ObserverGateCompositionTests(unittest.TestCase):
    def test_explicit_range_profile_reads_exact_metadata_and_malformed_abi_stays_unavailable(self):
        mock_deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',mock_deps),patch.object(GATE_FIXTURE,'HASH',RUNTIME):
            config=GATE_FIXTURE.range_fixture(True);chain=config['chains'][0]
            rpc=CompositionRPC(config); observed=O.observe(config,rpc)
            self.assertTrue(observed['chains'][0]['observation']['complete'])
            self.assertEqual(chain['pools'][0]['range_policy'],observed['chains'][0]['pools'][0]['range_policy'])
            self.assertTrue(P.validate(observed,expected_commit=GATE_FIXTURE.COMMIT,now=GATE_FIXTURE.NOW)['ready'])
            self.assertTrue(any(call[0]=='eth_call' and call[1][0]['data'].startswith(selector('keeperRangePolicy(bytes32)')) for call in rpc.calls))
            rpc=CompositionRPC(config)
            key=(chain['modules']['strategy']['address'],selector('keeperRangePolicy(bytes32)')+O._word(chain['pools'][0]['pool_id']))
            rpc.overrides[key]=encoded(2,100,1500,600,0,RUNTIME,RUNTIME)
            failed=O.observe(config,rpc)
            self.assertFalse(failed['chains'][0]['observation']['complete'])
            self.assertIsNone(failed['chains'][0]['pools'][0]['observed_range_policy'])
            self.assertFalse(P.validate(failed,expected_commit=GATE_FIXTURE.COMMIT,now=GATE_FIXTURE.NOW)['ready'])

    def test_legacy_range_profile_does_not_infer_orientation_or_query_new_getters(self):
        mock_deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',mock_deps),patch.object(GATE_FIXTURE,'HASH',RUNTIME):
            config=GATE_FIXTURE.fixture();rpc=CompositionRPC(config);O.observe(config,rpc)
            forbidden={selector(value) for value in ('RANGE_POLICY_VERSION()','rangeOrientation(bytes32)',
                'keeperRangePolicy(bytes32)','keeperRangeTarget(bytes32)')}
            self.assertFalse(any(method=='eth_call' and args[0]['data'][:10] in forbidden for method,args in rpc.calls))

    def test_complete_observer_output_passes_only_consistency_and_failures_remain_blocked(self):
        # Runtime preimages for real dependencies are not fabricated. This test
        # explicitly substitutes one known mock runtime in the gate's native
        # constants and fixture; actual-provider qualification remains absent.
        mock_deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',mock_deps),patch.object(GATE_FIXTURE,'HASH',RUNTIME):
            config=GATE_FIXTURE.fixture()
            # Exercise exact JSON decimal strings accepted by the gate across
            # ctor/VRF/PoolConfig/policy fields, not only tiny integer fixtures.
            chain=config['chains'][0]
            chain['nft_inventory']['randomness']['subscriptionId']='7'
            chain['pools'][0]['minDepositUSD']=str(chain['pools'][0]['minDepositUSD'])
            chain['pools'][0]['maxPositionUSD']=str(chain['pools'][0]['maxPositionUSD'])
            for route in chain['conversion_routes']:
                route['policy']['fee']=str(route['policy']['fee'])
                route['policy']['tickSpacing']=str(route['policy']['tickSpacing'])
            rpc=CompositionRPC(config)
            observed=O.observe(config,rpc)
            self.assertTrue(observed['chains'][0]['observation']['complete'],observed['chains'][0]['observation']['errors'])
            result=P.validate(observed,expected_commit=GATE_FIXTURE.COMMIT,now=GATE_FIXTURE.NOW)
            self.assertTrue(result['ready'],result['issues'])
            self.assertFalse(result['deployment_authorized'])
            rpc=CompositionRPC(config)
            rpc.bad=lambda target,data: target==chain['helpers']['migration_budget']['address'] and data==selector('contributionLossBps()')
            failed=O.observe(config,rpc)
            self.assertIsNone(failed['chains'][0]['helpers']['migration_budget']['observed_bindings']['contributionLossBps'])
            result=P.validate(failed,expected_commit=GATE_FIXTURE.COMMIT,now=GATE_FIXTURE.NOW)
            self.assertFalse(result['ready'])
            self.assertFalse(result['deployment_authorized'])
            rpc=CompositionRPC(config)
            rpc.overrides[chain['helpers']['migration_budget']['address'],selector('contributionLossBps()')]=encoded(200)
            changed=O.observe(config,rpc)
            self.assertEqual(changed['chains'][0]['helpers']['migration_budget']['observed_bindings']['contributionLossBps'],200)
            result=P.validate(changed,expected_commit=GATE_FIXTURE.COMMIT,now=GATE_FIXTURE.NOW)
            self.assertFalse(result['ready'])
            self.assertFalse(result['deployment_authorized'])


if __name__ == '__main__':
    unittest.main()
