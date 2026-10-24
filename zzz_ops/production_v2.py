"""Offline current native-V2 release inventory; never signs or contacts a chain.

Schema 5 is a new, explicit compatibility boundary. Observations never replace
approved pins. A consistent manifest cannot authenticate its own evidence and
never authorizes deployment, sealing, signing, or movement of funds.
"""
from __future__ import annotations

import copy
import hashlib
from itertools import combinations
import json
import re
import time
from typing import Any

from zzz_ops.abi import keccak256, word
from zzz_ops.state import integer

ZERO = '0x' + '00' * 20
ZERO_HASH = '0x' + '00' * 32
NATIVE_HASH = '0x' + keccak256(b'ZZZ_NATIVE_ETH_V1').hex()
V4_DOMAIN = '0x' + keccak256(b'ZZZ_TYPED_V4_ROUTE_V1').hex()
CANONICAL_SCHEMA = '0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2').hex()
MODULES = ('access', 'vault', 'nft', 'liquidity', 'rewards', 'membership', 'fees',
           'strategy', 'compounder', 'buyback', 'migration', 'oracle', 'pools',
           'canonical', 'nft_canonical', 'vault_canonical', 'fees_canonical')
RETIRED_MODULES = ('bridge', 'receiver', 'routes', 'transport')
HELPERS = ('activation_assets', 'activation_entry', 'migration_budget',
           'custody_validation', 'royalty_rewards', 'metadata_renderer',
           'claim_router', 'royalty_factory', 'reward_receiver_factory',
           'lp_converter', 'royalty_converter', 'entry_v4_executor',
           'lp_v4_executor', 'royalty_v4_executor')
MODULE_IDENTITIES = dict(zip(MODULES[1:], ('ZZZVault', 'ZZZNFT', 'ZZZLiquidityManager',
    'ZZZRewards', 'ZZZMembership', 'ZZZFeeController', 'ZZZStrategy', 'ZZZCompounder',
    'ZZZBuyback', 'ZZZMigration', 'ZZZOracle', 'ZZZPoolRegistry', 'ZZZCanonicalHandoff',
    'ZZZNFTCanonical', 'ZZZVaultCanonical', 'ZZZFeesCanonical')))
MODULE_IDENTITIES.update(dict(zip(RETIRED_MODULES, ('ZZZBridgeAdapter',
    'ZZZMigrationReceiver', 'ZZZMigrationRegistry', 'ZZZBridgeRouter'))))
EVIDENCE = ('toolchain', 'static_analysis', 'invariants', 'uniswap_fork', 'staging',
            'operations_recovery', 'gas_benchmarks', 'deployment_review',
            'economic_approval', 'independent_audit', 'remediation',
            'native_accounting', 'typed_v4_routes', 'custody_handoff')
SERVICES = ('rpc', 'pricing', 'randomness', 'keeper', 'api', 'metadata', 'opensea')
TOP_FIELDS = frozenset(('schema_version','accounting_version','routing_version',
    'accounting_model','custody_architecture','release_commit','canonical_chain_id',
    'economics','nft_policy','evidence','chains'))
CHAIN_FIELDS = frozenset(('chain_id','genesis_hash','observed_block',
    'maximum_snapshot_age_seconds','minimum_confirmations','observation',
    'modules','helpers','dependencies','tokens','constructor','operating_buyback_usd18',
    'native_accounting','execution_loss_policy','sequencer','pools','contribution_pool',
    'canonical_handoff','custody','inventory_history','activation_sources',
    'conversion_routes','services','governance','observed_modules','nft_inventory','reward_assets'))
NATIVE_DEPENDENCIES = {
    'pool_manager': ('0x8366a39cc670b4001a1121b8f6a443a643e40951',
        '0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626'),
    'position_manager': ('0x58daec3116aae6d93017baaea7749052e8a04fa7',
        '0xc873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2'),
    'state_view': ('0xf3334192d15450cdd385c8b70e03f9a6bd9e673b',
        '0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6'),
    'permit2': ('0x000000000022d473030f116ddee9f6b43ac78ba3',
        '0x5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca'),
    'zzz': ('0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a',
        '0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597')}
V4_FIELDS = (('source', 'address'), ('output', 'address'), ('currency0', 'address'),
    ('currency1', 'address'), ('fee', 'uint24'), ('tickSpacing', 'uint24'),
    ('hooks', 'address'), ('poolManager', 'address'), ('stateView', 'address'),
    ('sourceCodeHash', 'bytes32'), ('outputCodeHash', 'bytes32'),
    ('poolManagerCodeHash', 'bytes32'), ('stateViewCodeHash', 'bytes32'),
    ('reviewHash', 'bytes32'))
ENTRY_V3_FIELDS = (('source','address'),('output','address'),('router','address'),
    ('factory','address'),('pool','address'),('fee','uint24'),('routerCodeHash','bytes32'),
    ('factoryCodeHash','bytes32'),('poolCodeHash','bytes32'),('sourceCodeHash','bytes32'),
    ('outputCodeHash','bytes32'),('reviewHash','bytes32'))
CONVERTER_V3_FIELDS = (('source','address'),('router','address'),('factory','address'),
    ('pool','address'),('fee','uint24'),('sourceCodeHash','bytes32'),
    ('routerCodeHash','bytes32'),('factoryCodeHash','bytes32'),('poolCodeHash','bytes32'),
    ('reviewHash','bytes32'))
POOL_FIELDS = ('currency0','currency1','fee','tickSpacing','hooks','depositsEnabled',
    'operationsEnabled','rangeBps','triggerBps','maxSpotDeviationBps','maxSlippageBps',
    'minRebalanceInterval','minDepositUSD','maxPositionUSD')
COLORS = ('cyan','blue','violet','emerald','amber','crimson','ivory','onyx')
ANCHORS = frozenset(('amber','crimson','ivory','onyx'))
ADDITIONS = frozenset(('amber','crimson','onyx'))
PALETTES = tuple('-'.join(c) for n in (1,2,3) for c in combinations(COLORS,n)
    if n == 1 or n == 2 and ANCHORS.intersection(c) or n == 3 and any(
        v in ADDITIONS and ANCHORS.intersection(x for x in c if x != v) for v in c))
ARTWORK_FILES = tuple(f'{palette}-{pattern}-{rarity}-{stage}.svg' for palette in PALETTES
    for pattern in ('arcs','panels','orbits','ribs')
    for rarity in ('commun','rare','legendary')
    for stage in ('dormant','activated','enhanced','singularity'))


def identity(values: list[tuple[Any, str]]) -> str:
    encoded = ''.join(f'{int(value,16):064x}' if typ == 'address' else word(value,typ)
                      for value,typ in values)
    return '0x' + keccak256(bytes.fromhex(encoded)).hex()


def _obj(value):
    return value if isinstance(value, dict) else {}


def _numeric(value):
    try: return integer(value,'expected getter')
    except ValueError: return None


def configuration_hash(value: Any) -> str:
    """SHA-256 of code-owned configuration JSON; never contains credentials."""
    try:
        encoded = json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    except (ValueError,TypeError,OverflowError): return 'invalid-configuration'
    return hashlib.sha256(encoded.encode()).hexdigest()


def pool_configuration(chain, pool):
    values = {key:_obj(pool).get(key) for key in POOL_FIELDS}
    for key in ('minDepositUSD','maxPositionUSD'): values[key] = _numeric(values.get(key))
    return {'chain_id':_obj(chain).get('chain_id'),'pool_id':_obj(pool).get('pool_id'),
        'configuration':values,'principal_dependencies':{role:{key:_obj(_obj(_obj(chain).get('dependencies')).get(role)).get(key)
            for key in ('address','runtime_hash')} for role in NATIVE_DEPENDENCIES}}


def governance_configuration(chain):
    gov = _obj(_obj(chain).get('governance'))
    return {'chain_id':_obj(chain).get('chain_id'),
        'controller':_obj(_obj(_obj(chain).get('modules')).get('access')).get('address'),
        'policy':{key:gov.get(key) for key in ('multisig','signers','threshold','proposers',
            'executors','keeper','guardian','timelock_seconds','sealed','bootstrap')}}


def expected_bindings(chain: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """Finite reviewed zero-argument getter inventory, shared with the observer.

    Getter names are code-owned, never supplied as arbitrary RPC methods. Missing
    intended addresses stay None; the observer must not turn observations into
    approvals. Access.module(bytes32) is inventoried separately.
    """
    chain = _obj(chain)
    modules, helpers, deps = (_obj(chain.get(k)) for k in ('modules','helpers','dependencies'))
    def m(role): return _obj(modules.get(role)).get('address')
    def h(role): return _obj(helpers.get(role)).get('address')
    def d(role): return _obj(deps.get(role)).get('address')
    ctor, limits, canonical, nft, seq = (_obj(chain.get(k)) for k in
        ('constructor','execution_loss_policy','canonical_handoff','nft_inventory','sequencer'))
    vrf = _obj(nft.get('randomness'))
    result = {name: {'access': m('access')} for name in MODULES if name != 'access'}
    result['access'] = {'canonicalHandoff':m('canonical'), 'isSealed':True,
        'bootstrap':ZERO, 'getMinDelay':0, 'canonicalState':0,
        'canonicalSettling':False, 'preparationActive':False, 'paused':False,
        'royaltyFactory':h('royalty_factory')}
    result['vault'].update(ACCOUNTING_VERSION=2, migrationBudget=h('migration_budget'),
        canonicalChainId=chain.get('chain_id'),mintProceedsRecipient=ctor.get('mint_proceeds_recipient'))
    result['nft'].update(royaltyRewards=h('royalty_rewards'), claimRouter=h('claim_router'),
        metadataRenderer=h('metadata_renderer'), MAX_SUPPLY=1000, randomnessConfigured=True,mintPaused=False,
        artworkBaseURI=ctor.get('nft_base_uri'), randomnessCoordinator=vrf.get('coordinator'),
        keyHash=vrf.get('keyHash'),subscriptionId=_numeric(vrf.get('subscriptionId')),
        requestConfirmations=_numeric(vrf.get('requestConfirmations')),callbackGasLimit=_numeric(vrf.get('callbackGasLimit')),
        nativePayment=vrf.get('nativePayment'))
    result['liquidity'].update(positionManager=d('position_manager'),stateView=d('state_view'),
        poolManager=d('pool_manager'),permit2=d('permit2'))
    result['rewards']['converter'] = h('lp_converter')
    result['fees'].update(receiverFactory=h('reward_receiver_factory'),rewardReceiverCount=0)
    result['migration'].update(validation=h('custody_validation'),currentZZZ=d('zzz'),
        zzzCodeHash=_obj(deps.get('zzz')).get('runtime_hash'),outstandingCount=0)
    result['pools'].update(activationAssets=h('activation_assets'),activationEntry=h('activation_entry'),
        contributionPool=chain.get('contribution_pool'))
    result['oracle']['sequencerFeed'] = seq.get('address')
    result['buyback'].update(zzz=d('zzz'),maxTradeUSD=_numeric(ctor.get('maximum_buyback_usd18')),
        operatingTradeUSD=_numeric(chain.get('operating_buyback_usd18')))
    result['canonical'].update(SCHEMA=CANONICAL_SCHEMA,phase=canonical.get('phase'),
        incomingSource=canonical.get('incoming_source'))
    result['nft_canonical']['nft'] = m('nft')
    result['vault_canonical'].update(vault=m('vault'),originChain=canonical.get('origin_chain_id'),
        originVault=canonical.get('origin_vault'))
    result['fees_canonical']['fees'] = m('fees')
    helper = {
        'activation_assets': {'access':m('access'),'registry':m('pools')},
        'activation_entry': {'access':m('access'),'registry':m('pools'),
            'activationAssets':h('activation_assets'),'v4Executor':h('entry_v4_executor')},
        'migration_budget': {'access':m('access'),'vault':m('vault'),'MAX_LOSS_BPS':1000,
            'contributionLossBps':limits.get('contribution_bps'),
            'maintenanceLossBps':limits.get('maintenance_bps')},
        'custody_validation': {'access':m('access'),'migration':m('migration')},
        'royalty_rewards': {'nft':m('nft'),'canonicalController':m('access'),
            'converter':h('royalty_converter'),'custodyCount':0},
        'metadata_renderer': {'access':m('access')},
        'claim_router': {'access':m('access'),'nft':m('nft'),'royalties':h('royalty_rewards'),'MAX_CLAIMS':32},
        'royalty_factory': {'controller':m('access')},
        'reward_receiver_factory': {'access':m('access'),'fees':m('fees')},
        'entry_v4_executor': {'parent':h('activation_entry')},
        'lp_v4_executor': {'parent':h('lp_converter')},
        'royalty_v4_executor': {'parent':h('royalty_converter')}}
    for role, ledger in (('lp','rewards'),('royalty','royalty_rewards')):
        name = role + '_converter'
        bindings = _obj(_obj(helpers.get(name)).get('bindings'))
        helper[name] = {'access':m('access'),'ledger':m(ledger) if ledger == 'rewards' else h(ledger),
            'v4Executor':h(role+'_v4_executor'),'wrapper':bindings.get('wrapper'),
            'MAX_LOSS_BPS':1000,'conversionLossBps':limits.get(role+'_conversion_bps'),'enabled':True}
    return {'modules':result,'helpers':helper}


class Gate:
    def __init__(self, commit):
        self.commit = commit
        self.issues = []

    def check(self, condition, path, code, message, group='contracts'):
        if not condition:
            self.issues.append({'path':path,'code':code,'message':message,
                                'group':group,'remediation':message})
        return bool(condition)

    def obj(self, value, path):
        return value if self.check(isinstance(value,dict),path,'object.required',
            'Provide the required reviewed object.') else {}

    def items(self, value, path, maximum=1024, minimum=0):
        return value if self.check(isinstance(value,list) and minimum <= len(value) <= maximum,
            path,'list.invalid',f'Provide a list containing {minimum} through {maximum} entries.') else []

    def num(self, value, path, minimum=0, maximum=2**256-1):
        try: number = integer(value,path,minimum=minimum)
        except (ValueError,OverflowError): number = None
        return number if self.check(number is not None and number <= maximum,path,
            'integer.invalid',f'Provide an exact integer from {minimum} through {maximum}; booleans and floats are rejected.') else None

    def hex(self, value, path, size=32, zero=False, prefix=True):
        valid = isinstance(value,str) and re.fullmatch(('0x' if prefix else '') +
            f'[0-9a-fA-F]{{{size*2}}}',value) is not None
        valid = valid and (zero or int(value,16) != 0)
        return value.lower() if self.check(valid,path,'hex.invalid',
            'Provide the exact reviewed non-placeholder hexadecimal value.') else None

    def text(self, value, path):
        return self.check(isinstance(value,str) and bool(value.strip()) and not re.search(
            r'\b(?:pending|placeholder|tbd|todo|unknown|unset)\b|<[^>]+>',value,re.I),
            path,'decision.pending','Resolve and document this production decision.')

    def proof(self, value, path, *, independent=False, kind=None):
        proof = self.obj(value,path)
        self.check(proof.get('status') == 'passed',path+'.status','evidence.missing',
            'Retain passing evidence for this exact release and deployment scope.','security')
        self.check(proof.get('commit') == self.commit and self.commit is not None,path+'.commit',
            'evidence.stale','Bind the evidence to the exact release commit.','security')
        self.hex(proof.get('sha256'),path+'.sha256',prefix=False)
        self.text(proof.get('reference'),path+'.reference')
        if independent:
            self.check(proof.get('independent') is True,path+'.independent','evidence.independent',
                'Obtain the required independent review; internal tests do not substitute.','security')
        if kind is not None:
            self.check(proof.get('kind') == kind,path+'.kind','evidence.kind',
                'Supply evidence of the required actual integration or operating rehearsal.','security')
        return proof

    def keys(self, value, expected, path):
        self.check(isinstance(value,dict) and set(value) == set(expected),path,'schema.keys',
            'Use the exact current-version inventory fields; do not carry retired or ambiguous entries.')


def _equal(actual, expected):
    if isinstance(expected,bool): return type(actual) is bool and actual == expected
    if isinstance(expected,int): return type(actual) is int and actual == expected
    if isinstance(expected,str) and expected.startswith('0x'):
        return isinstance(actual,str) and actual.lower() == expected.lower()
    if isinstance(expected,list):
        return isinstance(actual,list) and len(actual) == len(expected) and all(
            _equal(a,b) for a,b in zip(actual,expected))
    if isinstance(expected,dict):
        return isinstance(actual,dict) and set(actual) == set(expected) and all(
            _equal(actual[k],v) for k,v in expected.items())
    return actual == expected


def _bindings(g, record, expected, path, *, helper=False):
    if helper:
        intended = g.obj(record.get('bindings'),path+'.bindings')
        g.check(all(v is not None for v in expected.values()) and set(intended) == set(expected) and all(_equal(intended.get(k),v) for k,v in expected.items()),
            path+'.bindings','binding.intended','Review the exact immutable parent/controller/ledger binding.','bindings')
    actual = g.obj(record.get('observed_bindings'),path+'.observed_bindings')
    g.check(all(v is not None for v in expected.values()) and set(actual) == set(expected) and all(_equal(actual.get(k),v) for k,v in expected.items()),
        path+'.observed_bindings','binding.observed',
        'Read every required getter at the pinned block and resolve the mismatched binding.','bindings')


def _runtime(g, record, path):
    address = g.hex(record.get('address'),path+'.address',20)
    pin = g.hex(record.get('runtime_hash'),path+'.runtime_hash')
    actual = g.hex(record.get('observed_runtime_hash'),path+'.observed_runtime_hash')
    g.check(pin is not None and actual == pin,path+'.observed_runtime_hash','runtime.mismatch',
        'Compare observed runtime against the independently approved constructor-specific pin.','bindings')
    return address, pin


def _bound_proof(g, value, path, chain, *, independent=True, kind=None, exact_block=False):
    proof = g.proof(value,path,independent=independent,kind=kind)
    block = _obj(chain.get('observed_block'))
    tested = g.num(proof.get('block_number'),path+'.block_number',1)
    tested_hash = g.hex(proof.get('block_hash'),path+'.block_hash')
    anchor = _numeric(block.get('number'))
    block_scope = type(proof.get('block_number')) is int and tested is not None and anchor is not None and tested <= anchor
    if exact_block or tested == anchor:
        block_scope = block_scope and tested == anchor and _equal(tested_hash,block.get('hash'))
    g.check(proof.get('chain_id') == chain.get('chain_id') and type(proof.get('chain_id')) is int and
        block_scope and tested_hash is not None and
        _equal(proof.get('deployment'),_obj(_obj(chain.get('modules')).get('access')).get('address')),
        path,'evidence.scope','Preserve the real tested block/hash, exact chain/deployment and current configuration; never relabel historical evidence as a fresh observation.','security')
    return proof


def _policies(g, config):
    economics = g.obj(config.get('economics'),'economics')
    for key, value in {'reward_model':'conventional_lp_fees','mint_price_wei':50_000_000_000_000_000,
        'minimum_activation_usd18':100*10**18,'minimum_top_up_usd18':5*10**18,
        'activation_minimum_basis':'gross_source_input','network_gas_separate':True,
        'fee_split_bps':[8000,1000,500,500],'collective_weights':'equal_activated_nfts',
        'maximum_membership_dust_raw':19}.items():
        actual = economics.get(key)
        if key in ('mint_price_wei','minimum_activation_usd18','minimum_top_up_usd18','maximum_membership_dust_raw'):
            actual = g.num(actual,'economics.'+key)
        g.check(_equal(actual,value),'economics.'+key,'economics.policy',
            'Preserve the current original-source contribution rules, funded 80/10/5/5 allocation and equal activated collective share.')
    nft = g.obj(config.get('nft_policy'),'nft_policy')
    expected = {'max_supply':1000,'rarity_counts':[600,300,100],'initial_rarity_bps':[6000,3000,1000],
        'rarity_distribution':'fixed_quotas_without_replacement',
        'rarity_randomization':'vrf_mint_order_without_replacement',
        'marketplace_royalty_bps':500,'received_royalty_distribution_bps':10000,
        'royalty_weights':[1,2,3],'royalty_eligibility':'activated_nfts_only',
        'royalty_entitlement':'received_funds_only','evolution_basis':'current_attributed_lp_value_usd18',
        'unavailable_valuation':'unavailable','randomness_policy':'verified_coordinator_two_words'}
    for key,value in expected.items():
        actual = nft.get(key)
        valid = _equal(actual,value)
        if isinstance(value,list): valid = isinstance(actual,list) and all(type(v) is int for v in actual) and actual == value
        g.check(valid,'nft_policy.'+key,'nft.policy','Use the implemented exact rarity quotas, received-only royalties and market-valued evolution policy.')
    thresholds = [g.num(v,f'nft_policy.evolution_thresholds_usd18[{i}]') for i,v in enumerate(
        g.items(nft.get('evolution_thresholds_usd18'),'nft_policy.evolution_thresholds_usd18',4,4))]
    g.check(thresholds == [0,100*10**18,1000*10**18,10000*10**18],
        'nft_policy.evolution_thresholds_usd18','nft.evolution','Preserve the $0/$100/$1,000/$10,000 evolution thresholds.')
    g.proof(nft.get('economic_review_evidence'),'nft_policy.economic_review_evidence')


def _chain(g, chain, path, home, now):
    g.check(set(chain)-{'_notes'} == set(CHAIN_FIELDS),path,'schema.keys',
        'Use the exact current chain inventory; remove retired transport, pair-migration and legacy-only fields.')
    cid = g.num(chain.get('chain_id'),path+'.chain_id',1)
    g.check(cid == home == 4663,path+'.chain_id','chain.unsupported',
        'This native deployment profile supports the current Robinhood canonical chain 4663 only.','native')
    genesis = g.hex(chain.get('genesis_hash'),path+'.genesis_hash')
    block = g.obj(chain.get('observed_block'),path+'.observed_block')
    number = g.num(block.get('number'),path+'.observed_block.number')
    block_hash = g.hex(block.get('hash'),path+'.observed_block.hash')
    stamp = g.num(block.get('timestamp'),path+'.observed_block.timestamp',1)
    maximum_age = g.num(chain.get('maximum_snapshot_age_seconds'),path+'.maximum_snapshot_age_seconds',1,86400)
    confirmations = g.num(chain.get('minimum_confirmations'),path+'.minimum_confirmations',1,256)
    g.check(stamp is not None and maximum_age is not None and 0 <= now-stamp <= maximum_age,
        path+'.observed_block','snapshot.stale','Collect a fresh pinned, sufficiently confirmed inventory snapshot.','services')
    obs = g.obj(chain.get('observation'),path+'.observation')
    head = g.num(obs.get('observed_head'),path+'.observation.observed_head')
    g.check(type(obs.get('chain_id')) is int and obs.get('chain_id') == cid and
        _equal(obs.get('genesis_hash'),genesis) and type(obs.get('block_number')) is int and
        obs.get('block_number') == number and _equal(obs.get('block_hash'),block_hash) and
        obs.get('complete') is True and obs.get('errors') == [] and
        head is not None and number is not None and confirmations is not None and head-number >= confirmations,
        path+'.observation','observation.incomplete',
        'Use one reviewed chain/genesis and confirmed canonical block; resolve every failed observation.','bindings')
    modules = g.obj(chain.get('modules'),path+'.modules')
    helpers = g.obj(chain.get('helpers'),path+'.helpers')
    g.keys(modules,MODULES,path+'.modules'); g.keys(helpers,HELPERS,path+'.helpers')
    addresses = []
    for category, roles in (('modules',MODULES),('helpers',HELPERS)):
        records = modules if category == 'modules' else helpers
        for role in roles:
            rp = path+'.'+category+'.'+role
            record = g.obj(records.get(role),rp)
            address,_ = _runtime(g,record,rp)
            if address is not None: addresses.append(address)
            if role != 'access' or category == 'helpers':
                g.check(record.get('immutable') is True,rp+'.immutable','module.upgradeable',
                    'Approve the exact non-upgradeable PoPL implementation and immutable bindings.','bindings')
            g.proof(record.get('review_evidence'),rp+'.review_evidence',independent=True)
    g.check(len(addresses) == len(set(addresses)),path+'.modules','binding.alias',
        'Use distinct module/helper deployments; no ledger, executor, controller or principal recipient may alias.','bindings')
    expected = expected_bindings(chain)
    for category in ('modules','helpers'):
        for role, values in expected[category].items():
            _bindings(g,_obj((modules if category == 'modules' else helpers).get(role)),values,
                path+'.'+category+'.'+role,helper=category == 'helpers')
    g.check(_obj(_obj(modules.get('fees')).get('observed_bindings')).get('rewardReceiverCount') == 0,
        path+'.modules.fees.observed_bindings.rewardReceiverCount','inbox.inventory_unsupported',
        'This release profile requires zero external-revenue inboxes; independently inventory receiver identities/protected balances before qualifying a deployment that has them.','bindings')
    observed_modules = g.obj(chain.get('observed_modules'),path+'.observed_modules')
    wanted = {name:_obj(modules.get(name)).get('address') for name in MODULES if name != 'access'}
    wanted.update({name:ZERO for name in RETIRED_MODULES})
    g.check(set(observed_modules) == set(wanted) and all(_equal(observed_modules.get(k),v) for k,v in wanted.items()),
        path+'.observed_modules','binding.registry','Read the current 16 module slots and confirm all four retired bridge slots are zero.','bindings')
    limits = g.obj(chain.get('execution_loss_policy'),path+'.execution_loss_policy')
    for name in ('contribution_bps','maintenance_bps','lp_conversion_bps','royalty_conversion_bps'):
        g.num(limits.get(name),path+'.execution_loss_policy.'+name,0,1000)
        g.check(type(limits.get(name)) is int,path+'.execution_loss_policy.'+name,'loss.type',
            'Record the actual governed basis-point getter as an integer, rather than assuming a default.')
    g.check(type(limits.get('hard_maximum_bps')) is int and limits.get('hard_maximum_bps') == 1000 and
        limits.get('gas_separate') is True,path+'.execution_loss_policy','loss.policy',
        'Read the immutable 1,000bps ceiling and keep gas separate; stronger transaction minima remain.','security')
    for role in ('lp_converter','royalty_converter'):
        g.hex(_obj(_obj(helpers.get(role)).get('bindings')).get('wrapper'),
            path+'.helpers.'+role+'.bindings.wrapper',20,zero=True)
    native = g.obj(chain.get('native_accounting'),path+'.native_accounting')
    g.check(_equal(native,{'version':2,'asset':ZERO,'decimals':18,'runtime_hash':None,
        'canonical_schema':CANONICAL_SCHEMA,'wrapper_independent':True,
        'eth_weth_principal_boundary':False,'legacy_v1_import':False}),path+'.native_accounting',
        'native.profile','Review actual ETH currency zero/native V2; do not substitute WETH, legacy ledgers or unsupported principal conversions.','native')
    ctor = g.obj(chain.get('constructor'),path+'.constructor')
    recipient = g.hex(ctor.get('mint_proceeds_recipient'),path+'.constructor.mint_proceeds_recipient',20)
    g.check(recipient is not None and recipient not in addresses,path+'.constructor.mint_proceeds_recipient',
        'mint.recipient','Keep mint proceeds outside all PoPL custody and helper contracts.','bindings')
    g.check(type(ctor.get('canonical_chain_id')) is int and ctor.get('canonical_chain_id') == home,
        path+'.constructor.canonical_chain_id','canonical.chain','Use the reviewed canonical chain in Vault construction.','native')
    hard = g.num(ctor.get('maximum_buyback_usd18'),path+'.constructor.maximum_buyback_usd18',1)
    operating = g.num(chain.get('operating_buyback_usd18'),path+'.operating_buyback_usd18')
    g.check(hard is not None and operating is not None and operating <= hard,path+'.operating_buyback_usd18',
        'buyback.ceiling','Read the operating per-trade ceiling and retain its immutable upper bound.')
    g.proof(ctor.get('recipient_payment_evidence'),path+'.constructor.recipient_payment_evidence')
    deps = _dependencies(g,chain,path,addresses)
    tokens = _tokens(g,chain,path,now,addresses)
    pools = _pools(g,chain,path,tokens,deps)
    _routes(g,chain,path,tokens,deps,pools,limits)
    _authority(g,chain,path)
    _canonical(g,chain,path,home)
    _nft(g,chain,path,tokens)
    history = g.obj(chain.get('inventory_history'),path+'.inventory_history')
    g.check(history.get('complete') is True,path+'.inventory_history.complete','history.incomplete',
        'Reconstruct complete admitted pools, source policies, all three parents\' route histories and both ledgers\' asset lists.','routes')
    _bound_proof(g,history.get('evidence'),path+'.inventory_history.evidence',chain,
        kind='complete_deployment_inventory',exact_block=True)
    _services(g,chain,path)


def _dependencies(g,chain,path,addresses):
    deps = g.obj(chain.get('dependencies'),path+'.dependencies')
    for role in NATIVE_DEPENDENCIES:
        record = g.obj(deps.get(role),path+'.dependencies.'+role)
        address,pin = _runtime(g,record,path+'.dependencies.'+role)
        intended, code = NATIVE_DEPENDENCIES[role]
        g.check(address == intended and pin == code,path+'.dependencies.'+role,'native.venue_pin',
            'Match the immutable native Registry venue/token pins; a manifest edit cannot change contract admission.','native')
    for role,record in deps.items():
        rp = path+'.dependencies.'+str(role)
        record = g.obj(record,rp)
        if role not in NATIVE_DEPENDENCIES: _runtime(g,record,rp)
        g.check(record.get('address') not in addresses,rp+'.address','dependency.alias',
            'External dependencies cannot alias a PoPL module or helper.','bindings')
        review = g.proof(record.get('authority_review'),rp+'.authority_review',independent=True)
        g.check(review.get('proxy_configuration_reviewed') is True and
            review.get('upgrade_authorities_reviewed') is True,rp+'.authority_review','dependency.authority',
            'Review proxy implementations, configuration and external upgrade authorities as well as runtime hashes.','security')
        expected = {}
        if role == 'position_manager': expected = {'poolManager':_obj(deps.get('pool_manager')).get('address'),
            'permit2':_obj(deps.get('permit2')).get('address')}
        if role == 'state_view': expected = {'poolManager':_obj(deps.get('pool_manager')).get('address')}
        _bindings(g,record,expected,rp,helper=True)
    zzz = _obj(deps.get('zzz'))
    g.check(zzz.get('burn_model') == 'burn(uint256):exact_local_supply_reduction',
        path+'.dependencies.zzz.burn_model','buyback.burn','Qualify an exact local-supply-reducing ZZZ burn.','security')
    g.proof(zzz.get('burn_evidence'),path+'.dependencies.zzz.burn_evidence')
    return deps


def _tokens(g,chain,path,now,addresses):
    result = {}
    stamp = _obj(chain.get('observed_block')).get('timestamp')
    for i,item in enumerate(g.items(chain.get('tokens'),path+'.tokens',33,2)):
        tp = f'{path}.tokens[{i}]'; token = g.obj(item,tp)
        address = g.hex(token.get('address'),tp+'.address',20,zero=True)
        decimals = g.num(token.get('decimals'),tp+'.decimals',0,18)
        g.check(address is not None and address not in result and address not in addresses,
            tp+'.address','token.duplicate','Inventory each currency exactly once, separately from protocol contracts.','pricing')
        if address == ZERO:
            g.check(token.get('kind') == 'native' and token.get('runtime_hash') is None and
                token.get('observed_runtime_hash') is None and decimals == 18,tp,'native.identity',
                'Native ETH uses address zero, 18 decimals and no ERC20 runtime pin.','native')
        else:
            g.check(token.get('kind') == 'erc20',tp+'.kind','token.kind','Use an explicit native/ERC20 currency kind.','native')
            _runtime(g,token,tp)
            g.check(token.get('non_rebasing') is True and token.get('transfer_tax') is False,
                tp,'token.semantics','Qualify exact non-rebasing, non-taxed transfer behavior and token authority risks.','security')
        g.check(type(token.get('observed_decimals')) is int and token.get('observed_decimals') == decimals,
            tp+'.observed_decimals','token.decimals','Read exact asset decimals at the inventory block.','pricing')
        feed = g.obj(token.get('feed'),tp+'.feed')
        source,_ = _runtime(g,dict(feed,address=feed.get('source')),tp+'.feed')
        fd = g.num(feed.get('decimals'),tp+'.feed.decimals',0,18)
        age = g.num(feed.get('maximum_age_seconds'),tp+'.feed.maximum_age_seconds',1,86400)
        answer = g.num(feed.get('answer'),tp+'.feed.answer',1,10**36)
        updated = g.num(feed.get('updated_at'),tp+'.feed.updated_at',1)
        round_id = g.num(feed.get('round_id'),tp+'.feed.round_id',1)
        answered = g.num(feed.get('answered_in_round'),tp+'.feed.answered_in_round',1)
        g.check(feed.get('denomination') == 'USD' and source not in addresses and
            type(stamp) is int and updated is not None and age is not None and 0 <= stamp-updated <= age and
            round_id is not None and answered is not None and answered >= round_id and answer is not None and
            fd is not None and answer * 10**(18-fd) <= 10**36,tp+'.feed','feed.invalid',
            'Qualify an independent USD feed with valid rounds, fresh positive values and exact decimals; do not hardcode stablecoin pegs.','pricing')
        g.check(_equal(feed.get('observed_oracle_feed'),{'source':source,'maxAge':age,
            'feedDecimals':fd,'assetDecimals':decimals}),tp+'.feed.observed_oracle_feed','feed.binding',
            'Match Oracle.feeds(asset) to the independently reviewed USD feed and freshness policy.','pricing')
        review = g.proof(feed.get('review_evidence'),tp+'.feed.review_evidence',independent=True)
        g.check(review.get('independent_price_source') is True and review.get('depeg_and_manipulation_reviewed') is True and
            type(review.get('chain_id')) is int and review.get('chain_id') == chain.get('chain_id') and
            _equal(review.get('asset'),address) and _equal(review.get('source'),source) and
            _equal(review.get('runtime_hash'),feed.get('runtime_hash')),
            tp+'.feed.review_evidence','feed.review','Review independence, depegs, market coverage and manipulation resistance.','pricing')
        if address is not None: result[address] = token
    g.check(ZERO in result and NATIVE_DEPENDENCIES['zzz'][0] in result,path+'.tokens','token.required',
        'Qualify both actual ETH and the currently selected ZZZ contract.','pricing')
    seq = g.obj(chain.get('sequencer'),path+'.sequencer')
    source = g.hex(seq.get('address'),path+'.sequencer.address',20,zero=True)
    mode = seq.get('mode')
    g.check(mode in ('not_applicable','uptime_feed') and (mode != 'not_applicable' or source == ZERO),
        path+'.sequencer','sequencer.mode','Review whether the chain requires a sequencer uptime feed.','pricing')
    if mode == 'uptime_feed':
        _runtime(g,seq,path+'.sequencer')
        started = g.num(seq.get('started_at'),path+'.sequencer.started_at',1)
        updated = g.num(seq.get('updated_at'),path+'.sequencer.updated_at',1)
        current_round = g.num(seq.get('round_id'),path+'.sequencer.round_id',1)
        answered = g.num(seq.get('answered_in_round'),path+'.sequencer.answered_in_round',1)
        g.check(source != ZERO and type(seq.get('answer')) is int and seq.get('answer') == 0 and
            type(seq.get('observed_decimals')) is int and seq.get('observed_decimals') == 0 and
            type(stamp) is int and started is not None and updated is not None and
            current_round is not None and answered is not None and answered >= current_round and
            started <= updated <= stamp and stamp-started > 3600,
            path+'.sequencer','sequencer.unavailable','Wait until the uptime feed is healthy beyond the mandatory one-hour grace period.','pricing')
        policy_id = g.hex(seq.get('active_policy_id'),path+'.sequencer.active_policy_id')
        policy = g.obj(seq.get('policy'),path+'.sequencer.policy')
        g.check(source == policy.get('source') and policy.get('expectedCodeHash') == seq.get('runtime_hash') and
            type(policy.get('bootstrapAdmission')) is bool and
            seq.get('observed_active_policy_id') == policy_id and _equal(seq.get('observed_policy'),policy),
            path+'.sequencer.policy','sequencer.policy',
            'Read the actual Oracle active sequencer policy, exact source/runtime pin and immutable descriptor.','pricing')
        g.hex(policy.get('reviewHash'),path+'.sequencer.policy.reviewHash')
    g.proof(seq.get('review_evidence'),path+'.sequencer.review_evidence',independent=True)
    return result


def _pools(g,chain,path,tokens,deps):
    result = {}
    for i,item in enumerate(g.items(chain.get('pools'),path+'.pools',16,1)):
        pp = f'{path}.pools[{i}]'; pool = g.obj(item,pp)
        c0 = g.hex(pool.get('currency0'),pp+'.currency0',20,zero=True)
        c1 = g.hex(pool.get('currency1'),pp+'.currency1',20)
        fee = g.num(pool.get('fee'),pp+'.fee',1,100000)
        spacing = g.num(pool.get('tickSpacing'),pp+'.tickSpacing',1,32767)
        hook = g.hex(pool.get('hooks'),pp+'.hooks',20,zero=True)
        pid = g.hex(pool.get('pool_id'),pp+'.pool_id')
        g.check(c0 in tokens and c1 in tokens and c0 is not None and c1 is not None and
            int(c0,16) < int(c1,16) and hook == ZERO,pp,'pool.assets',
            'Use sorted, reviewed currencies and a zero hook; native LP must be ETH/ZZZ.','native')
        if c0 == ZERO:
            g.check(c1 == NATIVE_DEPENDENCIES['zzz'][0],pp,'pool.native_pair',
                'Native principal admission currently supports only the pinned ETH/ZZZ pair.','native')
        if None not in (c0,c1,fee,spacing,hook):
            g.check(pid == identity([(c0,'address'),(c1,'address'),(fee,'uint24'),
                (spacing,'uint24'),(hook,'address')]),pp+'.pool_id','pool.identity',
                'Recompute the exact immutable PoolKey identity.','routes')
        g.check(pid is not None and pid not in result,pp+'.pool_id','pool.duplicate','Inventory every admitted principal pool exactly once.','routes')
        rb = g.num(pool.get('rangeBps'),pp+'.rangeBps',100,5000)
        trigger = g.num(pool.get('triggerBps'),pp+'.triggerBps',100,4999)
        deviation = g.num(pool.get('maxSpotDeviationBps'),pp+'.maxSpotDeviationBps',1,500)
        slip = g.num(pool.get('maxSlippageBps'),pp+'.maxSlippageBps',1,200)
        g.check(None not in (rb,trigger,deviation,slip,fee) and trigger < rb and deviation < rb and fee < slip*100,
            pp,'pool.guards','Use valid bounded range/trigger/deviation/slippage settings that admit the actual static fee.')
        g.num(pool.get('minRebalanceInterval'),pp+'.minRebalanceInterval',600,604800)
        minimum = g.num(pool.get('minDepositUSD'),pp+'.minDepositUSD',1)
        maximum = g.num(pool.get('maxPositionUSD'),pp+'.maxPositionUSD',1)
        g.check(minimum is not None and maximum is not None and minimum <= 5*10**18 <= 100*10**18 <= maximum,
            pp,'pool.activation_minimum','Keep principal-pool bounds compatible with $100 activation and $5 growth.')
        for flag in ('depositsEnabled','operationsEnabled'):
            g.check(type(pool.get(flag)) is bool,pp+'.'+flag,'pool.mode','Declare the actual contribution/maintenance flags explicitly.')
        wanted = {k:pool.get(k) for k in POOL_FIELDS}
        actual = _obj(pool.get('observed_config'))
        # ABI uint values may be decimal strings in the intended JSON manifest.
        for key in ('minDepositUSD','maxPositionUSD'):
            if key in wanted: wanted[key] = integer(wanted[key],key) if isinstance(wanted[key],(str,int)) and not isinstance(wanted[key],bool) and str(wanted[key]).isdigit() else None
        g.check(_equal(actual,wanted),pp+'.observed_config','pool.observation',
            'Read and compare the complete Registry PoolConfig at the pinned block.','bindings')
        g.check(_equal(pool.get('observed_accounting'),{'currency0':c0,'currency1':c1}),
            pp+'.observed_accounting','pool.accounting','Verify accounting() preserves actual ETH zero identity.','native')
        slot = g.obj(pool.get('slot0'),pp+'.slot0')
        g.num(slot.get('sqrt_price_x96'),pp+'.slot0.sqrt_price_x96',1,2**160-1)
        g.num(slot.get('protocol_fee'),pp+'.slot0.protocol_fee',0,2**24-1)
        g.check(type(slot.get('tick')) is int and -887272 <= slot.get('tick') <= 887272 and
            type(slot.get('lp_fee')) is int and slot.get('lp_fee') == fee,pp+'.slot0','pool.state',
            'Verify an initialized pool and its actual stored static LP fee; protocol fees are separate.','routes')
        g.num(pool.get('liquidity'),pp+'.liquidity',1,2**128-1)
        review = _bound_proof(g,pool.get('review_evidence'),pp+'.review_evidence',chain,kind='principal_pool_qualification')
        g.check(review.get('configuration_sha256') == configuration_hash(pool_configuration(chain,pool)),
            pp+'.review_evidence.configuration_sha256','pool.qualification_scope',
            'Bind pool qualification to the full current configuration and immutable principal venue pins.','routes')
        if pid is not None: result[pid] = pool
    selected = g.hex(chain.get('contribution_pool'),path+'.contribution_pool')
    active = [pid for pid,p in result.items() if p.get('depositsEnabled') is True]
    g.check(active == [selected] and _obj(result.get(selected)).get('operationsEnabled') is True,
        path+'.contribution_pool','pool.contribution','Enable exactly one selected contribution pool and qualify its LP operation.','routes')
    return result


def _routes(g,chain,path,tokens,deps,pools,limits):
    helpers = _obj(chain.get('helpers'))
    parent_roles = {'entry':'activation_entry','lp':'lp_converter','royalty':'royalty_converter'}
    executor_roles = {'entry':'entry_v4_executor','lp':'lp_v4_executor','royalty':'royalty_v4_executor'}
    external = {str(_obj(v).get('address','')).lower():_obj(v) for v in deps.values()}
    external.update(tokens)
    routes = {}
    for i,item in enumerate(g.items(chain.get('conversion_routes'),path+'.conversion_routes',256)):
        rp = f'{path}.conversion_routes[{i}]'; record = g.obj(item,rp)
        role = record.get('role'); kind = record.get('route_kind')
        if not isinstance(role,str): role = None
        valid_kind = type(kind) is int and kind in (1,2)
        g.check(role in parent_roles and valid_kind,rp,'route.kind',
            'Select an explicit Entry/LP/royalty parent and V3/V4 descriptor; direct routes have no invented descriptor.','routes')
        rid = g.hex(record.get('route_id'),rp+'.route_id')
        source = g.hex(record.get('source_asset'),rp+'.source_asset',20,zero=True)
        enabled = record.get('enabled')
        g.check(type(enabled) is bool and type(record.get('observed_enabled')) is bool and
            record.get('observed_enabled') is enabled and record.get('observed_exists') is True and
            type(record.get('observed_kind')) is int and record.get('observed_kind') == kind,rp+'.enabled','route.enabled',
            'Read route existence/kind/enablement from the exact parent and immutable child.','routes')
        key = (role,rid)
        g.check(key not in routes,rp+'.route_id','route.duplicate','Inventory each parent route identity exactly once.','routes')
        policy = g.obj(record.get('policy'),rp+'.policy')
        fields = V4_FIELDS if kind == 2 else ENTRY_V3_FIELDS if role == 'entry' else CONVERTER_V3_FIELDS
        g.keys(policy,[k for k,_ in fields],rp+'.policy')
        values = {}
        for name,typ in fields:
            if typ == 'address': values[name] = g.hex(policy.get(name),rp+'.policy.'+name,20,
                zero=kind == 2 and name in ('source','output','currency0','hooks'))
            elif typ == 'bytes32': values[name] = g.hex(policy.get(name),rp+'.policy.'+name)
            else: values[name] = g.num(policy.get(name),rp+'.policy.'+name,1 if name == 'tickSpacing' else 0,
                32767 if name == 'tickSpacing' else 999999)
        g.check(_equal(record.get('observed_policy'),values),rp+'.observed_policy','route.observation',
            'Read the correct typed route tuple from its parent; a v4 ID must not be decoded as V3.','bindings')
        parent = _obj(helpers.get(parent_roles.get(role))).get('address')
        executor = _obj(helpers.get(executor_roles.get(role))).get('address')
        if all(v is not None for v in values.values()) and role in parent_roles and parent is not None and executor is not None:
            prefix = [(V4_DOMAIN,'bytes32'),(chain.get('chain_id'),'uint256'),(executor,'address'),(parent,'address')] if kind == 2 else []
            g.check(rid == identity(prefix+[(values[k],typ) for k,typ in fields]),rp+'.route_id','route.identity',
                'Recompute the immutable policy/domain/chain/executor/parent route identity.','routes')
        g.check(source in tokens and source == values.get('source') and (role == 'entry' or source != ZERO),
            rp+'.source_asset','route.source','Use the exact admitted source currency and independently reviewed price.','routes')
        proof = g.proof(record.get('review_evidence'),rp+'.review_evidence',independent=True)
        g.check(values.get('reviewHash') == '0x'+str(proof.get('sha256')),
            rp+'.policy.reviewHash','route.review_hash','Pin the exact retained route review in the immutable descriptor.','routes')
        if kind == 2:
            c0,c1 = values.get('currency0'),values.get('currency1')
            output = values.get('output')
            g.check(c0 is not None and c1 is not None and int(c0,16) < int(c1,16) and
                source != output and {source,output} == {c0,c1} and values.get('hooks') == ZERO,
                rp+'.policy','route.v4_pair','Use a sorted static hookless PoolKey matching the directed source/output exactly.','routes')
            g.check(output in tokens and (role == 'entry' or output == ZERO),rp+'.policy.output',
                'route.output','Reward conversion must return actual native ETH to its fixed ledger.','routes')
            if enabled is True:
                for address_field,hash_field in (('source','sourceCodeHash'),('output','outputCodeHash'),
                    ('poolManager','poolManagerCodeHash'),('stateView','stateViewCodeHash')):
                    target = values.get(address_field)
                    wanted = NATIVE_HASH if target == ZERO and address_field in ('source','output') else _obj(external.get(target)).get('runtime_hash')
                    g.check(wanted is not None and values.get(hash_field) == wanted,rp+'.policy.'+hash_field,
                        'route.runtime_pin','Match current approved asset/core/StateView runtime pins; native uses its explicit sentinel.','routes')
                venue = g.obj(record.get('venue_observation'),rp+'.venue_observation')
                if None not in (c0,c1,values.get('fee'),values.get('tickSpacing'),values.get('hooks')):
                    pid = identity([(c0,'address'),(c1,'address'),(values['fee'],'uint24'),
                        (values['tickSpacing'],'uint24'),(values['hooks'],'address')])
                    g.check(venue.get('pool_id') == pid,rp+'.venue_observation.pool_id','route.pool_id',
                        'Read the exact conversion PoolKey identity, separately from principal-pool admission.','routes')
                g.check(venue.get('poolManager') == values.get('poolManager') and
                    venue.get('stateView') == values.get('stateView'),rp+'.venue_observation','route.state_binding',
                    'Confirm the conversion StateView actually binds this PoolManager.','bindings')
                slot = g.obj(venue.get('slot0'),rp+'.venue_observation.slot0')
                g.num(slot.get('sqrt_price_x96'),rp+'.venue_observation.slot0.sqrt_price_x96',1,2**160-1)
                g.num(slot.get('protocol_fee'),rp+'.venue_observation.slot0.protocol_fee',0,2**24-1)
                g.check(type(slot.get('lp_fee')) is int and slot.get('lp_fee') == values.get('fee') and
                    type(slot.get('tick')) is int and -887272 <= slot.get('tick') <= 887272,
                    rp+'.venue_observation.slot0','route.pool_state','Confirm initialized current static-fee conversion state.','routes')
                g.num(venue.get('liquidity'),rp+'.venue_observation.liquidity',1,2**128-1)
        elif kind == 1:
            output = values.get('output') if role == 'entry' else _obj(_obj(helpers.get(parent_roles.get(role))).get('bindings')).get('wrapper')
            g.check(source != ZERO and output not in (None,ZERO) and source != output,
                rp+'.policy','route.v3_native','V3 uses explicit nonzero ERC20 currencies; native input/output must use the separate v4 profile.','routes')
            if enabled is True:
                for address_field,hash_field in (('source','sourceCodeHash'),('router','routerCodeHash'),
                    ('factory','factoryCodeHash'),('pool','poolCodeHash')):
                    target = values.get(address_field)
                    g.check(target in external and values.get(hash_field) == _obj(external.get(target)).get('runtime_hash'),
                        rp+'.policy.'+hash_field,'route.runtime_pin','Review and pin every actual V3 token/router/factory/pool runtime.','routes')
                if role == 'entry':
                    g.check(values.get('outputCodeHash') == _obj(tokens.get(output)).get('runtime_hash'),
                        rp+'.policy.outputCodeHash','route.runtime_pin','Pin the exact V3 output currency.','routes')
                venue = g.obj(record.get('venue_observation'),rp+'.venue_observation')
                ordered = sorted((source,output)) if isinstance(source,str) and isinstance(output,str) else (None,None)
                g.check(venue.get('factory') == values.get('factory') and
                    venue.get('router_factory') == values.get('factory') and
                    venue.get('factory_pool') == values.get('pool') and venue.get('pool_address') == values.get('pool') and
                    [venue.get('token0'),venue.get('token1')] == list(ordered) and
                    type(venue.get('fee')) is int and venue.get('fee') == values.get('fee'),
                    rp+'.venue_observation','route.v3_binding','Verify router factory, factory pool, exact tokens and static V3 fee.','bindings')
                g.num(venue.get('liquidity'),rp+'.venue_observation.liquidity',1,2**128-1)
                if role != 'entry': _wrapper(g,chain,path,role,tokens,deps)
        if role in ('lp','royalty'):
            expected_profile = 'v4_native' if kind == 2 else 'v3_wrapper_configurable'
            g.check(record.get('profile') == expected_profile,rp+'.profile','route.profile',
                'Choose an explicit current converter worker profile with no legacy/fixed-limit fallback.','routes')
        if enabled is True:
            execution = _bound_proof(g,record.get('execution_evidence'),rp+'.execution_evidence',chain,
                kind='route_staged_execution')
            cap = limits.get('contribution_bps') if role == 'entry' else limits.get(str(role)+'_conversion_bps')
            observed_loss = g.num(execution.get('execution_loss_bps'),rp+'.execution_evidence.execution_loss_bps',0,10000)
            g.check(execution.get('network_gas_separate') is True and observed_loss is not None and
                type(cap) is int and observed_loss <= cap,rp+'.execution_evidence','route.loss_limit',
                'Qualify actual route execution under the current governed limit, including fees/slippage and separate gas.','routes')
            actual_output = values.get('output') if kind == 2 or role == 'entry' else ZERO
            g.check(execution.get('parent') == parent and execution.get('executor') == (executor if kind == 2 else parent) and
                execution.get('route_id') == rid and execution.get('source_asset') == source and
                execution.get('output_asset') == actual_output and type(execution.get('current_loss_bps')) is int and
                execution.get('current_loss_bps') == cap and execution.get('full_operation_simulated') is True,
                rp+'.execution_evidence','route.execution_scope',
                'Scope actual full-operation execution evidence to this parent/helper/route/assets and current governed cap.','routes')
            if kind == 2:
                fee_state = _obj(_obj(record.get('venue_observation')).get('slot0'))
                g.check(_equal(execution.get('fee_configuration'),{'lp_fee':fee_state.get('lp_fee'),
                    'protocol_fee':fee_state.get('protocol_fee')}),rp+'.execution_evidence.fee_configuration',
                    'route.fee_qualification','Requalify an enabled route after its actual LP/protocol fee configuration changes.','routes')
        routes[key] = record
    sources = set()
    selected_id = chain.get('contribution_pool')
    if not isinstance(selected_id,str): selected_id = None
    else: selected_id = selected_id.lower()
    selected = _obj(pools.get(selected_id))
    selected_pair = {selected.get('currency0'),selected.get('currency1')}
    for i,item in enumerate(g.items(chain.get('activation_sources'),path+'.activation_sources',64,2)):
        sp = f'{path}.activation_sources[{i}]'; source = g.obj(item,sp)
        asset = g.hex(source.get('source_asset'),sp+'.source_asset',20,zero=True)
        pid = g.hex(source.get('pool_id'),sp+'.pool_id')
        rid = g.hex(source.get('route_id'),sp+'.route_id',zero=True)
        policy_id = g.hex(source.get('asset_policy_id'),sp+'.asset_policy_id')
        ordinal = g.num(source.get('asset_policy_ordinal'),sp+'.asset_policy_ordinal')
        count = g.num(source.get('observed_asset_policy_count'),sp+'.observed_asset_policy_count',1)
        kind = source.get('route_kind'); enabled = source.get('enabled')
        g.check(type(enabled) is bool and type(kind) is int and kind in (0,1,2),sp,'source.mode',
            'Declare explicit enabled state and direct/V3/V4 source routing kind.','routes')
        g.check((pid,asset) not in sources and pid in pools and asset in tokens,sp,'source.duplicate',
            'Inventory unique admitted source/pool pairs with independently qualified prices.','routes')
        sources.add((pid,asset))
        ap = g.obj(source.get('asset_policy'),sp+'.asset_policy')
        fields = (('token','address'),('enabled','bool'),('expectedCodeHash','bytes32'),
            ('reviewHash','bytes32'),('decimals','uint8'),('poolAdmission','bool'))
        g.keys(ap,[k for k,_ in fields],sp+'.asset_policy')
        valid = (ap.get('token') == asset and type(ap.get('enabled')) is bool and ap.get('enabled') is enabled and
            type(ap.get('poolAdmission')) is bool and type(ap.get('decimals')) is int and
            ap.get('decimals') == _obj(tokens.get(asset)).get('decimals'))
        expected_hash = NATIVE_HASH if asset == ZERO else _obj(tokens.get(asset)).get('runtime_hash')
        valid = valid and ap.get('expectedCodeHash') == expected_hash
        g.hex(ap.get('reviewHash'),sp+'.asset_policy.reviewHash')
        g.check(valid and _equal(source.get('observed_asset_policy'),ap) and
            source.get('observed_asset_policy_id') == policy_id and
            source.get('observed_asset_policy_ordinal_id') == policy_id and ordinal is not None and
            count is not None and ordinal < count,sp+'.asset_policy','source.policy',
            'Read the active source-admission identity, code pin, decimals and exact policy; approval is separate from a wallet allowance.','routes')
        asset_helper = _obj(helpers.get('activation_assets')).get('address')
        if valid and ordinal is not None and isinstance(asset_helper,str) and re.fullmatch(r'0x[0-9a-fA-F]{40}',asset_helper) and all(isinstance(ap.get(k),str) and re.fullmatch(r'0x[0-9a-fA-F]{64}',ap[k]) for k in ('expectedCodeHash','reviewHash')):
            g.check(policy_id == identity([(asset_helper,'address'),(ordinal,'uint256')]+[(ap[k],typ) for k,typ in fields]),sp+'.asset_policy_id',
                'source.policy_id','Recompute the complete immutable source-admission policy ID.','routes')
        if kind == 0:
            g.check(rid == ZERO_HASH and asset in {pools.get(pid,{}).get('currency0'),pools.get(pid,{}).get('currency1')},
                sp+'.route_id','source.direct','Direct input requires route zero and an actual principal accounting currency.','routes')
        else:
            route = _obj(routes.get(('entry',rid)))
            output = _obj(route.get('policy')).get('output')
            g.check(bool(route) and route.get('route_kind') == kind and route.get('source_asset') == asset and
                (enabled is not True or route.get('enabled') is True) and output in selected_pair,
                sp+'.route_id','source.route','Bind this input to a qualified matching Entry route into the actual selected LP pair.','routes')
        if enabled is True:
            g.check(pid == chain.get('contribution_pool'),sp+'.pool_id','source.pool',
                'Only the selected contribution pool may accept enabled activation/top-up routes.','routes')
        source_review = _bound_proof(g,source.get('review_evidence'),sp+'.review_evidence',chain,kind='activation_source_qualification')
        g.check(source_review.get('source_asset') == asset and source_review.get('pool_id') == pid and
            source_review.get('asset_policy_id') == policy_id and type(source_review.get('route_kind')) is int and
            source_review.get('route_kind') == kind and source_review.get('route_id') == rid and
            source_review.get('activation_assets') == _obj(helpers.get('activation_assets')).get('address') and
            source_review.get('entry') == _obj(helpers.get('activation_entry')).get('address') and
            type(source_review.get('current_loss_bps')) is int and
            source_review.get('current_loss_bps') == limits.get('contribution_bps'),
            sp+'.review_evidence','source.qualification_scope',
            'Qualify this exact source, pool, admission policy, Entry/helper, typed route and current contribution cap.','routes')
    for asset in selected_pair:
        g.check(any(isinstance(s,dict) and s.get('source_asset') == asset and s.get('enabled') is True
            for s in _obj_list(chain.get('activation_sources'))),path+'.activation_sources','source.pair_required',
            'Qualify direct activation from both actual ETH/ZZZ pool currencies.','routes')
    zzz = NATIVE_DEPENDENCIES['zzz'][0]
    g.check(any(role == 'lp' and r.get('enabled') is True and r.get('source_asset') == zzz
        for (role,_),r in routes.items()),path+'.conversion_routes','route.lp_eth_required',
        'Qualify an enabled ZZZ LP-fee conversion route and worker into ETH; native fees require no conversion.','routes')
    chain['_validated_routes'] = routes


def _obj_list(value):
    return value if isinstance(value,list) else []


def _wrapper(g,chain,path,role,tokens,deps):
    helper = _obj(_obj(chain.get('helpers')).get(role+'_converter'))
    wrapper = _obj(helper.get('bindings')).get('wrapper')
    wp = g.obj(helper.get('wrapper_policy'),path+'.helpers.'+role+'_converter.wrapper_policy')
    g.check(wrapper not in (None,ZERO) and wrapper in tokens and
        wp.get('codeHash') == _obj(tokens.get(wrapper)).get('runtime_hash'),
        path+'.helpers.'+role+'_converter.wrapper_policy','wrapper.pin',
        'V3 conversion/unwrap requires the separately pinned and reviewed immutable wrapper.','routes')
    fields = ('codeHash','admin','implementation','adminOwner','adminCodeHash','implementationCodeHash','reviewHash')
    raw = {key:wp.get(key) for key in fields}
    g.check(set(wp)-{'review_evidence'} == set(fields) and _equal(helper.get('observed_wrapper_policy'),raw),
        path+'.helpers.'+role+'_converter.observed_wrapper_policy','wrapper.observation',
        'Read the converter wrapper policy and any proxy/admin configuration at the pinned block.','bindings')
    ap = path+'.helpers.'+role+'_converter.wrapper_policy'
    admin = g.hex(wp.get('admin'),ap+'.admin',20,zero=True)
    implementation = g.hex(wp.get('implementation'),ap+'.implementation',20,zero=True)
    owner = g.hex(wp.get('adminOwner'),ap+'.adminOwner',20,zero=True)
    admin_hash = g.hex(wp.get('adminCodeHash'),ap+'.adminCodeHash',zero=True)
    implementation_hash = g.hex(wp.get('implementationCodeHash'),ap+'.implementationCodeHash',zero=True)
    evidence = g.proof(wp.get('review_evidence'),ap+'.review_evidence',independent=True)
    g.check(wp.get('reviewHash') == '0x'+str(evidence.get('sha256')),ap+'.reviewHash','wrapper.review_hash',
        'Bind the configured wrapper policy to its exact independent review.','routes')
    if admin == ZERO:
        g.check(implementation == owner == ZERO and admin_hash == implementation_hash == ZERO_HASH,
            ap,'wrapper.nonproxy','A nonproxy wrapper policy must contain no fabricated implementation/admin state.','bindings')
    else:
        dependencies = {str(_obj(v).get('address','')).lower():_obj(v) for v in deps.values()}
        g.check(admin not in (None,ZERO) and implementation not in (None,ZERO) and owner not in (None,ZERO) and
            admin_hash == _obj(dependencies.get(admin)).get('runtime_hash') and
            implementation_hash == _obj(dependencies.get(implementation)).get('runtime_hash') and
            _equal(helper.get('wrapper_policy_observation'),{'admin':admin,'implementation':implementation,'adminOwner':owner}),
            ap,'wrapper.proxy','Read and match wrapper ProxyAdmin, implementation, owner and runtime pins; runtime code alone is insufficient.','bindings')


def _authority(g,chain,path):
    gov = g.obj(chain.get('governance'),path+'.governance')
    address = g.hex(gov.get('multisig'),path+'.governance.multisig',20)
    signers = [g.hex(v,path+'.governance.signers',20) for v in g.items(gov.get('signers'),path+'.governance.signers',64,1)]
    g.check(len(signers) == len(set(signers)),path+'.governance.signers','authority.duplicate',
        'Review unique multisig signers and threshold.','authorities')
    g.num(gov.get('threshold'),path+'.governance.threshold',1,len(signers))
    proposers = [g.hex(v,path+'.governance.proposers',20) for v in g.items(gov.get('proposers'),path+'.governance.proposers',64,1)]
    executors = [g.hex(v,path+'.governance.executors',20,zero=True) for v in g.items(gov.get('executors'),path+'.governance.executors',64,1)]
    keeper = g.hex(gov.get('keeper'),path+'.governance.keeper',20)
    guardian = g.hex(gov.get('guardian'),path+'.governance.guardian',20)
    g.check(address in proposers and address is not None and len(proposers) == len(set(proposers)) and
        len(executors) == len(set(executors)),path+'.governance','authority.roles',
        'Read governance proposer/executor membership and approve each operator role.','authorities')
    g.check(_equal(gov.get('observed_roles'),{'proposers':proposers,'executors':executors,'cancellers':proposers,
        'keeper':keeper,'keeper_enabled':True,'guardian':guardian,'guardian_enabled':True,'controller_admin':True}),
        path+'.governance.observed_roles','authority.observation',
        'Observe every declared role and full role-grant/revocation history at the pinned block.','authorities')
    if keeper in (address,guardian) or guardian == address:
        g.text(gov.get('overlap_review'),path+'.governance.overlap_review')
    g.check(type(gov.get('timelock_seconds')) is int and gov.get('timelock_seconds') == 0 and
        gov.get('sealed') is True and gov.get('bootstrap') == ZERO and gov.get('role_history_complete') is True,
        path+'.governance','authority.seal','Confirm immediate governance, revoked bootstrap, sealed modules and complete operator/role history.','authorities')
    review = _bound_proof(g,gov.get('review_evidence'),path+'.governance.review_evidence',chain,
        kind='immediate_governance_review')
    g.check(review.get('configuration_sha256') == configuration_hash(governance_configuration(chain)),
        path+'.governance.review_evidence.configuration_sha256','authority.qualification_scope',
        'Bind governance qualification to the actual controller, multisig/signers, role set and zero-delay/seal policy.','authorities')
    g.check(review.get('no_notice_risk_accepted') is True and review.get('loss_limit_authority_reviewed') is True and
        review.get('all_roles_inventoried') is True,
        path+'.governance.review_evidence','authority.trust','Accept immediate dependency/custody/loss-policy authority explicitly.','authorities')


def _canonical(g,chain,path,home):
    canonical = g.obj(chain.get('canonical_handoff'),path+'.canonical_handoff')
    g.check(canonical.get('transport') == 'same_chain_only' and canonical.get('remote_activation_enabled') is False and
        type(canonical.get('state')) is int and canonical.get('state') == 0 and canonical.get('settling') is False and
        canonical.get('preparation_active') is False and type(canonical.get('phase')) is int and
        canonical.get('phase') in (0,5),path+'.canonical_handoff','canonical.lifecycle',
        'Use exactly one active native-V2 canonical authority; importing, frozen or retired deployments cannot operate.','native')
    vault = _obj(_obj(chain.get('modules')).get('vault')).get('address')
    origin = g.hex(canonical.get('origin_vault'),path+'.canonical_handoff.origin_vault',20)
    g.check(type(canonical.get('origin_chain_id')) is int and canonical.get('origin_chain_id') == home,
        path+'.canonical_handoff.origin_chain_id','canonical.lineage','Preserve the actual original canonical chain/Vault lineage.','native')
    if canonical.get('phase') == 0:
        g.check(origin == vault and canonical.get('incoming_source') == ZERO,path+'.canonical_handoff',
            'canonical.origin','An original idle coordinator must have its own Vault origin and no source deployment.','native')
    elif canonical.get('phase') == 5:
        source = g.hex(canonical.get('incoming_source'),path+'.canonical_handoff.incoming_source',20)
        proof = _bound_proof(g,canonical.get('activation_evidence'),path+'.canonical_handoff.activation_evidence',chain,
            kind='atomic_same_chain_canonical_activation')
        g.check(source != _obj(_obj(chain.get('modules')).get('access')).get('address') and
            proof.get('source_controller') == source and proof.get('source_permanently_retired') is True and
            proof.get('all_backing_verified') is True and proof.get('origin_vault') == origin and
            proof.get('origin_chain_id') == home,path+'.canonical_handoff.activation_evidence','canonical.activation',
            'Retain actual funded atomic source-retirement/successor-activation and lineage evidence.','security')
    _bound_proof(g,canonical.get('review_evidence'),path+'.canonical_handoff.review_evidence',chain,
        kind='native_canonical_handoff_review')
    custody = g.obj(chain.get('custody'),path+'.custody')
    g.check(custody.get('cross_chain_enabled') is False and
        type(custody.get('pending_principal_count')) is int and custody.get('pending_principal_count') == 0 and
        type(custody.get('pending_royalty_custody_count')) is int and custody.get('pending_royalty_custody_count') == 0 and
        custody.get('recipient_trust_accepted') is True and custody.get('normal_floors_preserved') is True and
        custody.get('raw_exit_separately_approved') is True,path+'.custody','custody.release',
        'Resolve pending external custody and qualify normal-floor/raw-exit/return behavior; cross-chain custody remains unqualified.','security')
    _bound_proof(g,custody.get('review_evidence'),path+'.custody.review_evidence',chain,
        kind='governed_custody_qualification')


def _ledger_assets(g,chain,path,inventory,tokens,maximum,royalty=False):
    record = g.obj(inventory,path)
    entries = g.items(record.get('assets'),path+'.assets',maximum,1)
    count = g.num(record.get('asset_count'),path+'.asset_count',1,maximum)
    g.check(count == len(entries) and type(record.get('observed_asset_count')) is int and
        record.get('observed_asset_count') == count and record.get('complete_admission_history') is True,
        path,'ledger.assets_complete','Read assetCount/assets/isAsset and retain the complete admission history.','bindings')
    result = set(); custody_count = 0
    routes = chain.get('_validated_routes',{})
    for i,item in enumerate(entries):
        ap = f'{path}.assets[{i}]'; asset = g.obj(item,ap)
        address = g.hex(asset.get('address'),ap+'.address',20,zero=True)
        g.check(address not in result and address in tokens and (i != 0 or address == ZERO) and
            asset.get('observed_asset') == address and asset.get('observed_is_asset') is True,
            ap,'ledger.asset','Preserve native-first unique ledger assets with exact observed admission; do not hide historical currencies.','bindings')
        result.add(address)
        g.proof(asset.get('review_evidence'),ap+'.review_evidence',independent=True)
        if royalty:
            amount = g.num(asset.get('custody_amount'),ap+'.custody_amount')
            if amount: custody_count += 1
            strategy = asset.get('strategy')
            g.check(address == ZERO and strategy == 'native' or address != ZERO and strategy in
                ('convert_to_eth','governed_recovery'),ap+'.strategy','royalty.strategy',
                'Qualify ETH receipt or a deliberate conversion/outage-recovery policy for each optional royalty currency.','routes')
            if address != ZERO and strategy == 'convert_to_eth':
                g.check(any(role == 'royalty' and r.get('enabled') is True and r.get('source_asset') == address
                    for (role,_),r in routes.items()),ap,'royalty.route',
                    'Qualify an enabled actual royalty-to-ETH route and matching worker profile.','routes')
            review = _obj(asset.get('review_evidence'))
            g.check(review.get('outage_isolation_reviewed') is True and review.get('old_receipts_preserved') is True,
                ap+'.review_evidence','royalty.outage','Verify an optional currency failure cannot undo LP activation or grant newcomers older receipts.','security')
    if royalty:
        g.check(custody_count == _obj(chain.get('custody')).get('pending_royalty_custody_count') and custody_count == 0,
            path,'royalty.custody','Reconcile every admitted royalty currency\'s actual custody balance before release.','security')
    return result


def _nft(g,chain,path,tokens):
    np = path+'.nft_inventory'; nft = g.obj(chain.get('nft_inventory'),np)
    ctor = _obj(chain.get('constructor')); modules = _obj(chain.get('modules'))
    helpers = _obj(chain.get('helpers')); nft_address = _obj(modules.get('nft')).get('address')
    royalty = _obj(helpers.get('royalty_rewards')).get('address')
    observed = g.obj(nft.get('observed_bindings'),np+'.observed_bindings')
    g.check(observed.get('royaltyReceiver') == royalty and type(observed.get('royaltyBps')) is int and
        observed.get('royaltyBps') == 500,np+'.observed_bindings','nft.royalty_receiver',
        'Read ERC-2981 receiver/rate: royalties go to the NFT-bound ledger, not an operator wallet.','bindings')
    minted = g.num(observed.get('mintedCount'),np+'.observed_bindings.mintedCount',0,1000)
    cursor = g.num(observed.get('nextToFinalize'),np+'.observed_bindings.nextToFinalize',1,1001)
    remaining = g.num(observed.get('remainingToReveal'),np+'.observed_bindings.remainingToReveal',0,1000)
    quotas = [g.num(v,np+'.observed_bindings.rarityRemaining',0,maximum) for v,maximum in zip(
        g.items(observed.get('rarityRemaining'),np+'.observed_bindings.rarityRemaining',3,3),(600,300,100))]
    g.check(None not in (minted,cursor,remaining) and cursor <= minted+1 and remaining == 1001-cursor and
        len(quotas) == 3 and None not in quotas and sum(quotas) == remaining,
        np+'.observed_bindings','nft.draw_accounting','Observe minted/finalization order and remaining exact-quota artwork draws.','randomness')
    base = ctor.get('nft_base_uri')
    g.check(isinstance(base,str) and re.fullmatch(
        r'(?:ipfs://(?:Qm[1-9A-HJ-NP-Za-km-z]{44}|b[a-z2-7]{20,})|ar://[A-Za-z0-9_-]{43})/(?:[^\s"<>]*/)?',base) is not None,
        path+'.constructor.nft_base_uri','artwork.content_addressed','Publish the immutable artwork root on reviewed IPFS/Arweave storage.','services')
    artwork = g.obj(nft.get('artwork_publication'),np+'.artwork_publication')
    paths = g.items(artwork.get('asset_paths'),np+'.artwork_publication.asset_paths',len(ARTWORK_FILES),len(ARTWORK_FILES))
    manifest_hash = g.hex(artwork.get('manifest_sha256'),np+'.artwork_publication.manifest_sha256',prefix=False)
    g.check(artwork.get('base_uri') == base and type(artwork.get('asset_count')) is int and
        artwork.get('asset_count') == len(ARTWORK_FILES) and all(isinstance(v,str) for v in paths) and
        len(paths) == len(set(v for v in paths if isinstance(v,str))) == len(ARTWORK_FILES) and
        set(v for v in paths if isinstance(v,str)) == set(ARTWORK_FILES),np+'.artwork_publication',
        'artwork.inventory','Publish exactly the supported 2,784 palette/pattern/rarity/evolution assets.','services')
    proof = g.proof(artwork.get('review_evidence'),np+'.artwork_publication.review_evidence',
        independent=True,kind='content_addressed_artwork_review')
    g.check(proof.get('base_uri') == base and proof.get('asset_manifest_sha256') == manifest_hash,
        np+'.artwork_publication.review_evidence','artwork.review','Bind the independent artwork review to the actual content root and full asset manifest.','security')
    vrf = g.obj(nft.get('randomness'),np+'.randomness')
    coordinator,_ = _runtime(g,dict(vrf,address=vrf.get('coordinator')),np+'.randomness')
    key_hash = g.hex(vrf.get('keyHash'),np+'.randomness.keyHash')
    subscription = g.num(vrf.get('subscriptionId'),np+'.randomness.subscriptionId',1)
    confirmations = g.num(vrf.get('requestConfirmations'),np+'.randomness.requestConfirmations',3,200)
    gas = g.num(vrf.get('callbackGasLimit'),np+'.randomness.callbackGasLimit',200000,10000000)
    g.check(type(vrf.get('nativePayment')) is bool and vrf.get('immutable_provider_configuration') is True and
        vrf.get('mutable_request_parameters') == ['requestConfirmations','callbackGasLimit'] and
        vrf.get('no_admin_reroll') is True and 'immutable_configuration' not in vrf,np+'.randomness',
        'randomness.policy','Keep provider/lane/subscription/payment immutable while reviewing bounded future request settings and no reroll.','randomness')
    review = g.proof(vrf.get('review_evidence'),np+'.randomness.review_evidence',independent=True,
        kind='verified_randomness_coordinator_review')
    integration = _bound_proof(g,vrf.get('integration_evidence'),np+'.randomness.integration_evidence',chain,
        kind='coordinator_staged_randomness')
    for label,record in (('review_evidence',review),('integration_evidence',integration)):
        g.check(record.get('chain_id') == chain.get('chain_id') and record.get('coordinator') == coordinator and
            record.get('nft') == nft_address and record.get('keyHash') == key_hash and
            record.get('subscriptionId') == subscription and record.get('nativePayment') is vrf.get('nativePayment'),
            np+'.randomness.'+label,'randomness.scope','Qualify the actual coordinator, consumer, lane, subscription and payment mode.','randomness')
    g.check(confirmations is not None and gas is not None and
        integration.get('requestConfirmations') == confirmations and integration.get('callbackGasLimit') == gas and
        integration.get('original_request_recovery_tested') is True and
        g.num(integration.get('fulfilled_request_id'),np+'.randomness.integration_evidence.fulfilled_request_id',1) is not None and
        g.num(integration.get('finalized_token_id'),np+'.randomness.integration_evidence.finalized_token_id',1) is not None,
        np+'.randomness.integration_evidence','randomness.integration','Rehearse actual fulfillment/finalization, provider bounds/funding and original-request recovery.','randomness')
    _ledger_assets(g,chain,path+'.reward_assets',chain.get('reward_assets'),tokens,33)
    _ledger_assets(g,chain,np+'.royalty_assets',nft.get('royalty_assets'),tokens,17,True)


def _services(g,chain,path):
    services = g.obj(chain.get('services'),path+'.services')
    g.keys(services,SERVICES,path+'.services')
    profiles = {'rpc':'eip1898_hash_pinned_debug_trace','pricing':'independent_usd_native_v2',
        'randomness':'verified_coordinator_two_words','keeper':'native_v2_governed_limits',
        'api':'accounting_v2_routing_v2','metadata':'content_addressed_v2','opensea':'primary_mint_current_nft'}
    access = _obj(_obj(chain.get('modules')).get('access')).get('address')
    nft = _obj(_obj(chain.get('modules')).get('nft')).get('address')
    for role in SERVICES:
        sp = path+'.services.'+role; service = g.obj(services.get(role),sp)
        g.check(service.get('status') == 'qualified' and service.get('profile') == profiles[role] and
            type(service.get('chain_id')) is int and service.get('chain_id') == chain.get('chain_id') and
            service.get('controller') == access,sp,'service.'+role,
            f'Qualify the real {role} service against this exact native-V2 deployment and approved runtime/configuration.','randomness' if role == 'randomness' else 'pricing' if role == 'pricing' else 'services')
        pin = g.hex(service.get('configuration_sha256'),sp+'.configuration_sha256',prefix=False)
        proof = _bound_proof(g,service.get('evidence'),sp+'.evidence',chain,kind=role+'_production_qualification')
        g.check(proof.get('configuration_sha256') == pin and pin is not None and
            proof.get('profile') == profiles[role],sp+'.evidence','service.scope',
            'Bind actual operating evidence to the approved service configuration and compatibility profile.','services')
        if role == 'keeper':
            g.check(proof.get('crash_recovery_tested') is True and proof.get('off_host_backup_tested') is True and
                proof.get('nonce_and_pending_recovery_tested') is True,sp+'.evidence','service.keeper_recovery',
                'Rehearse outage/server replacement, off-host backups and saved-hash/nonce recovery on the actual configured service.','services')
        if role == 'opensea':
            g.check(proof.get('nft') == nft and proof.get('recipient_correct') is True and
                proof.get('mint_price_wei') == 50_000_000_000_000_000 and
                proof.get('vrf_and_royalty_receiver_tested') is True,sp+'.evidence','service.opensea',
                'Qualify OpenSea chain/product, actual caller/recipient, exact 0.05ETH mint and the NFT-bound VRF/royalty integration.','services')
            g.text(service.get('collection_url'),sp+'.collection_url')


def validate(config: Any, *, expected_commit: str | None = None, now: int | None = None) -> dict[str,Any]:
    """Validate explicit schema 5 only, preserving every legacy schema boundary."""
    config = copy.deepcopy(config) if isinstance(config,dict) else {}
    g = Gate(config.get('release_commit'))
    g.check(set(config)-{'_notes'} == set(TOP_FIELDS),'config','schema.keys',
        'Use only explicit schema-5 fields; obsolete bridge approvals cannot accompany this release inventory.')
    g.commit = g.hex(g.commit,'release_commit',20,prefix=False)
    now = int(time.time()) if now is None else now
    for key,value in {'schema_version':5,'accounting_version':2,'routing_version':2,
        'accounting_model':'shared-pools-native-v2','custody_architecture':'governed-v1'}.items():
        g.check(_equal(config.get(key),value),key,'schema.unsupported',
            'Use explicit current schema 5/native accounting 2/typed routing 2; legacy profiles cannot be reinterpreted.')
    if expected_commit is not None:
        g.check(g.commit == expected_commit,'release_commit','commit.mismatch','Use the exact reviewed release commit.')
    home = g.num(config.get('canonical_chain_id'),'canonical_chain_id',1)
    _policies(g,config)
    evidence = g.obj(config.get('evidence'),'evidence')
    for name in EVIDENCE: g.proof(evidence.get(name),'evidence.'+name)
    audit = g.obj(evidence.get('independent_audit'),'evidence.independent_audit')
    g.check(audit.get('independent') is True and audit.get('kind') == 'external_security_audit',
        'evidence.independent_audit','audit.independent','Commission an external audit of this exact release and remediate its findings.','security')
    g.text(audit.get('auditor'),'evidence.independent_audit.auditor')
    for severity in ('critical','high'):
        g.check(g.num(audit.get('open_'+severity),'evidence.independent_audit.open_'+severity) == 0,
            'evidence.independent_audit.open_'+severity,'audit.unresolved','Resolve every open critical/high audit finding.','security')
    gas = g.obj(evidence.get('gas_benchmarks'),'evidence.gas_benchmarks')
    used = g.num(gas.get('maximum_observed_transaction_gas'),'evidence.gas_benchmarks.maximum_observed_transaction_gas',1)
    limit = g.num(gas.get('reviewed_block_gas_limit'),'evidence.gas_benchmarks.reviewed_block_gas_limit',1)
    g.check(type(gas.get('chain_id')) is int and gas.get('chain_id') == home and used is not None and
        limit is not None and used < limit and gas.get('complete_operating_rehearsal') is True,
        'evidence.gas_benchmarks','gas.qualification',
        'Rehearse bounded production deployment/canonical/maintenance/contribution gas on the actual target chain and retain headroom.','security')
    compiler = g.obj(evidence.get('toolchain'),'evidence.toolchain')
    g.check(compiler.get('solidity_version') == '0.8.26' and compiler.get('evm_version') == 'cancun' and
        compiler.get('normal_size_limits') is True and compiler.get('constructor_arguments_included') is True and
        compiler.get('all_production_objects') is True,'evidence.toolchain','compiler.profile',
        'Verify the current pinned production compiler/profile and every normal runtime/initcode limit including constructor arguments.','security')
    chains = g.items(config.get('chains'),'chains',1,1)
    for index, value in enumerate(chains):
        chain = g.obj(value,f'chains[{index}]')
        _chain(g,chain,f'chains[{index}]',home,now)
    groups = {}
    for issue in g.issues:
        groups.setdefault(issue['group'],[]).append({'path':issue['path'],'code':issue['code'],
            'remediation':issue['remediation']})
    return {'schema_version':5,'status':'blocked' if g.issues else 'ready','ready':not g.issues,
        'release_commit':g.commit,'deployment_authorized':False,'issues':g.issues,
        'blockers':groups,'migration_enabled':False,
        'limitations':['Offline checks cannot authenticate supplied evidence or authorize deployment, sealing, signing, or spending.',
            'This profile covers one active canonical native-V2 deployment; cross-chain activation and ETH/WETH principal conversion are unsupported.',
            'Pinned observations establish consistency only; runtime pins alone do not prove dependency security or detect every proxy configuration change.']}
