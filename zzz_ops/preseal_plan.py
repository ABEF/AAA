"""Closed, unsigned fresh pre-seal configuration review; never live adoption.

Only the fixed source-defined setup families below can produce calldata. Public
addresses and predecessor construction are conditional assignments, not observed
contracts. Missing inputs block that family and its dependants. Live authority,
code, state, markets, fees and release approval remain unverified in every result.
"""
from __future__ import annotations
import copy
import re
from pathlib import Path
from urllib.parse import urlsplit
from zzz_ops import deployment_plan as D
from zzz_ops import opensea_drop as DROP
from zzz_ops.production_v2 import NATIVE_DEPENDENCIES

SCHEMA=1
PROFILE=D.PROFILE
STEPS=('dual_usd','fixed_zzz','lp_asset','migration_zzz','execution_sources',
       'native_pools','routes','confirmation','randomness','seadrop_terms','seadrop_upstream','mint_end')
CHILDREN=tuple(row[0] for row in D.INTERNAL)
PRODUCER_FILES=('zzz_ops/preseal_plan.py','scripts/prepare-preseal.py',
                'zzz_ops/deployment_plan.py','zzz_ops/abi.py','zzz_ops/opensea_drop.py',
                'zzz_ops/production_v2.py','zzz_ops/royalty_read_policy.py')
BALANCE_POLICY={'balanceGas':'uint32','reviewHash':'hash'}
NATIVE_HASH='0x'+D.keccak256(b'ZZZ_NATIVE_ETH_V1').hex()
SELECTED_POOL='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
INITIAL_MINT_PRICE='50000000000000000'
FALSE_FLAGS=('ready_for_submission','production_approved','transaction_submitted','rpc_performed',
             'simulation_performed','authority_verified','onchain_snapshot_verified','binding_addresses_verified',
             'target_runtime_verified','signing_performed','seal_prepared','nonce_reserved')
SOURCE={'source':'address','expectedCodeHash':'hash','independenceId':'hash','maxAge':'uint32','feedDecimals':'uint8'}
DUAL={'primary':SOURCE,'secondary':SOURCE,'maxDeviationBps':'uint16','reviewHash':'hash'}
KEY={'currency0':'address0','currency1':'address','fee':'uint24','tickSpacing':'int24','hooks':'address0'}
POOL={'key':KEY,'depositsEnabled':'bool','operationsEnabled':'bool','rangeBps':'uint16',
      'triggerBps':'uint16','maxSpotDeviationBps':'uint16','maxSlippageBps':'uint16',
      'minRebalanceInterval':'uint32','minDepositUSD':'uint256','maxPositionUSD':'uint256'}
ROUTE={'source':'address','output':'address0','key':KEY,'poolManager':'address','stateView':'address',
       'sourceCodeHash':'hash','outputCodeHash':'hash','poolManagerCodeHash':'hash',
       'stateViewCodeHash':'hash','reviewHash':'hash'}
SETTINGS={
 'dual_usd':{'eth':DUAL,'zzz':DUAL},
 'fixed_zzz':{'expectedCodeHash':'hash','reviewHash':'hash'},
 'lp_asset':{'add_fixed_zzz':'bool'},
 'migration_zzz':{'codeHash':'hash','reviewHash':'hash'},
 'execution_sources':{'sources':('list',{'source':'address','expectedCodeHash':'hash','reviewHash':'hash'},2)},
 'native_pools':{'pools':('list',{'config':POOL,'orientation':'uint8'},4)},
 'routes':{'execution_pool_ids':('list','hash',4),'execution_review_hash':'hash',
           'conversion_routes':('list',ROUTE,4),'conversion_enabled':'bool'},
 'confirmation':{'secondsRequired':'uint32','maximumGap':'uint32','reviewed':'hash',
                 'requireReferenceExit':'bool','referenceReview':'hash'},
 'randomness':{'coordinator':'address','expectedCodeHash':'hash','keyHash':'hash','subscriptionId':'uint256',
               'confirmations':'uint16','callbackGas':'uint32','nativePayment':'bool','reviewHash':'hash'},
 'seadrop_terms':{'artifact_path':'path','artifact_sha256':'sha'},
 'seadrop_upstream':{'publicKeyURIs':('list','uri',16),'allowListURI':'uri','dropURI':'uri',
                     'existingFeeRecipients':('list','address',16),'existingPayers':('list','address',16),
                     'existingSigners':('list','address',16),'existingTokenGated':('list','address',16)},
 'mint_end':{'end':'uint64'}}


def _blank(spec):
    return {k:_blank(v) for k,v in spec.items()} if isinstance(spec,dict) else None


def setting_templates():
    """Typed object skeletons; null never installs a policy/default."""
    return {k:_blank(v) for k,v in SETTINGS.items()}


def source_template():return _blank(SOURCE)
def pool_template():return _blank(POOL)
def route_template():return _blank(ROUTE)


def example():
    return {'schema':SCHEMA,'profile':PROFILE,'chain_id':'4663','constructor_input':D.template(),
            'bootstrap':None,'child_addresses':{name:None for name in CHILDREN},
            'settings':{name:None for name in STEPS}}


def producer_sources():
    return {name:D.sha((D.ROOT/name).read_bytes().replace(b'\r\n',b'\n')) for name in PRODUCER_FILES}


def _native_pins():
    # Reuse only this source-owned constant inventory, not its historical
    # profile/validator. The trusted current Registry source is checked below.
    if set(NATIVE_DEPENDENCIES)!=set(D.NATIVE):D.fail('preseal_native_constant_drift')
    result={}
    for role,address in D.NATIVE.items():
        pair=NATIVE_DEPENDENCIES.get(role)
        if type(pair)is not tuple or len(pair)!=2 or pair[0]!=address:D.fail('preseal_native_constant_drift')
        result[role]=D._hash(pair[1])
    return result


def _normal(value,spec):
    if value is None:return None
    if isinstance(spec,dict):
        D._keys(value,spec)
        return {k:_normal(value[k],v) for k,v in spec.items()}
    if isinstance(spec,tuple):
        if type(value)is not list or len(value)>spec[2]:D.fail('preseal_array_bound')
        return [_normal(v,spec[1]) for v in value]
    if spec.startswith('uint'):return D._uint(value,int(spec[4:]))
    if spec.startswith('int'):
        bits=int(spec[3:])
        if type(value)is not str or len(value)>79 or re.fullmatch(r'(0|-?[1-9][0-9]*)',value)is None:D.fail('invalid_signed_integer')
        if not -(1<<(bits-1))<=int(value)<(1<<(bits-1)):D.fail('integer_bounds')
        return value
    if spec in ('address','address0'):return D._address(value,spec=='address0')
    if spec in ('hash','sha'):return D._hash(value,spec=='hash')
    if spec=='bool':
        if type(value)is not bool:D.fail('preseal_boolean')
        return value
    if type(value)is not str or len(value)>4096:D.fail('preseal_string_bound')
    try:encoded=value.encode('utf-8')
    except UnicodeError:D.fail('preseal_string_encoding')
    if len(encoded)>4096 or any(ord(c)<32 or ord(c)==127 for c in value):D.fail('preseal_string_bound')
    if spec=='path':
        if not value:D.fail('preseal_artifact_path')
    elif spec=='uri':
        if value and not value.startswith(('ipfs://','ar://','https://')):D.fail('preseal_metadata_uri')
        try:parts=urlsplit(value)
        except ValueError:D.fail('preseal_metadata_uri')
        if parts.username is not None or parts.password is not None:D.fail('preseal_metadata_credentials')
    else:D.fail('preseal_spec')
    return value


def _known(value):
    if value is None:return False
    if isinstance(value,dict):return all(_known(v) for v in value.values())
    if isinstance(value,list):return all(_known(v) for v in value)
    return True


def _missing(value,path):
    if value is None:return [path]
    if isinstance(value,dict):return [p for k,v in value.items() for p in _missing(v,path+'.'+k)]
    if isinstance(value,list):return [p for n,v in enumerate(value) for p in _missing(v,path+'.'+str(n))]
    return []


def _equal(a,b,code):
    if a is not None and b is not None and a!=b:D.fail(code)


def _bounds(value,low,high,code):
    if value is not None and not low<=int(value)<=high:D.fail(code)


def _pool(key,zzz,*,principal):
    _equal(key['currency0'],D.ZERO,'preseal_pair_identity')
    _equal(key['currency1'],zzz,'preseal_pair_identity')
    _equal(key['hooks'],D.ZERO,'preseal_hook_forbidden')
    _bounds(key['fee'],0,100000 if principal else 999999,'preseal_pool_fee')
    _bounds(key['tickSpacing'],1,32767,'preseal_tick_spacing')


def validate(raw):
    keys=('schema','profile','chain_id','constructor_input','bootstrap','child_addresses','settings')
    D._keys(raw,keys+('royalty_balance_policy',) if isinstance(raw,dict) and 'royalty_balance_policy' in raw else keys)
    if type(raw['schema'])is not int or raw['schema']!=SCHEMA or raw['profile']!=PROFILE or raw['chain_id']!='4663':D.fail('preseal_profile')
    result=example();result['constructor_input']=D.validate(raw['constructor_input'])
    result['bootstrap']=None if raw['bootstrap'] is None else D._address(raw['bootstrap'])
    D._keys(raw['child_addresses'],CHILDREN);D._keys(raw['settings'],STEPS)
    for name,value in raw['child_addresses'].items():
        result['child_addresses'][name]=None if value is None else D._address(value)
    for name,spec in SETTINGS.items():result['settings'][name]=_normal(raw['settings'][name],spec)
    if 'royalty_balance_policy' in raw:
        result['royalty_balance_policy']=_normal(raw['royalty_balance_policy'],BALANCE_POLICY)
        if result['royalty_balance_policy'] is not None:
            _bounds(result['royalty_balance_policy']['balanceGas'],10000,1000000,'preseal_royalty_balance_gas')
    c=result['constructor_input'];s=result['settings'];zzz=c['inputs']['zzz'];native_pins=_native_pins()
    top=set(c['planned_addresses'].values())-{None};children=list(result['child_addresses'].values());used=[v for v in children if v is not None]
    if len(used)!=len(set(used)) or set(used)&(top|set(D.NATIVE.values())|{D.SEADROP}):D.fail('preseal_child_collision')
    if result['bootstrap'] in top|set(used)|set(D.NATIVE.values())|{D.SEADROP}:D.fail('preseal_bootstrap_collision')
    if c['inputs']['governance'] in set(used) or c['inputs']['mint_recipient'] in set(used):D.fail('preseal_authority_child_collision')
    dual=s['dual_usd']
    if dual is not None:
        for p in dual.values():
            if p is None:continue
            _bounds(p['maxDeviationBps'],0,500,'preseal_source_spread')
            for source in (p['primary'],p['secondary']):
                if source is not None:
                    _bounds(source['maxAge'],1,86400,'preseal_source_age');_bounds(source['feedDecimals'],0,18,'preseal_feed_decimals')
                    if source['source'] in top|set(used):D.fail('preseal_source_is_protocol_address')
            a,b=p['primary'],p['secondary']
            if a is not None and b is not None:
                for field in ('source','independenceId'):
                    if a[field] is not None and a[field]==b[field]:D.fail('preseal_source_independence')
    fixed=s['fixed_zzz'];migration=s['migration_zzz']
    if fixed is not None:_equal(fixed['expectedCodeHash'],native_pins['zzz'],'preseal_native_zzz_pin')
    if migration is not None:_equal(migration['codeHash'],native_pins['zzz'],'preseal_native_zzz_pin')
    if fixed is not None and migration is not None:_equal(fixed['expectedCodeHash'],migration['codeHash'],'preseal_zzz_codehash_mismatch')
    if s['lp_asset'] is not None and s['lp_asset']['add_fixed_zzz'] is False:D.fail('preseal_fixed_reward_required')
    ex=s['execution_sources']
    if ex is not None and ex['sources'] is not None:
        addresses=[v['source'] for v in ex['sources'] if v is not None and v['source'] is not None]
        if len(addresses)!=len(set(addresses)):D.fail('preseal_duplicate_execution_source')
        if dual is not None and _known(dual['zzz']):
            admitted={p['source']:p for p in (dual['zzz']['primary'],dual['zzz']['secondary'])}
            for item in ex['sources']:
                if _known(item):
                    policy=admitted.get(item['source'])
                    if policy is None or policy['expectedCodeHash']!=item['expectedCodeHash']:D.fail('preseal_execution_source_not_admitted')
                    if policy['feedDecimals']!='18':D.fail('preseal_execution_source_decimals')
    pools=s['native_pools'];configs=[]
    if pools is not None and pools['pools'] is not None:
        if not pools['pools']:D.fail('preseal_initial_pool_required')
        for row in pools['pools']:
            if row is None:continue
            _equal(row['orientation'],'1','preseal_price_orientation')
            p=row['config']
            if p is None:continue
            if p['key'] is not None:_pool(p['key'],zzz,principal=True)
            for name,lo,hi in (('rangeBps',100,9999),('triggerBps',100,9998),('maxSpotDeviationBps',1,500),
                               ('maxSlippageBps',1,1000),('minRebalanceInterval',600,604800),('minDepositUSD',1,(1<<256)-1),('maxPositionUSD',1,(1<<256)-1)):
                _bounds(p[name],lo,hi,'preseal_pool_'+name)
            for field in ('triggerBps','maxSpotDeviationBps'):
                if p[field] is not None and p['rangeBps'] is not None and int(p[field])>=int(p['rangeBps']):D.fail('preseal_pool_range_overlap')
            if p['key'] is not None and p['key']['fee'] is not None and p['maxSlippageBps'] is not None and int(p['key']['fee'])>=int(p['maxSlippageBps'])*100:D.fail('preseal_pool_fee_budget')
            if p['minDepositUSD'] is not None and p['maxPositionUSD'] is not None and int(p['maxPositionUSD'])<int(p['minDepositUSD']):D.fail('preseal_pool_position_cap')
            configs.append(p)
        if sum(p['depositsEnabled'] is True for p in configs)>1:D.fail('preseal_multiple_contribution_pools')
    routes=s['routes']
    if routes is not None:
        ids=routes['execution_pool_ids']
        if ids is not None and len([i for i in ids if i is not None])!=len(set(i for i in ids if i is not None)):D.fail('preseal_duplicate_execution_pool')
        policies=routes['conversion_routes']
        if policies is not None:
            for p in policies:
                if p is None:continue
                _equal(p['source'],zzz,'preseal_conversion_source');_equal(p['output'],D.ZERO,'preseal_conversion_output')
                _equal(p['outputCodeHash'],NATIVE_HASH,'preseal_native_hash')
                if p['key'] is not None:_pool(p['key'],zzz,principal=False)
                for k in ('poolManager','stateView'):_equal(p[k],c['inputs']['pool_manager' if k=='poolManager' else 'state_view'],'preseal_route_binding')
                _equal(p['poolManagerCodeHash'],native_pins['pool_manager'],'preseal_native_core_pin')
                _equal(p['stateViewCodeHash'],native_pins['state_view'],'preseal_native_state_pin')
                _equal(p['sourceCodeHash'],native_pins['zzz'],'preseal_native_zzz_pin')
                if fixed is not None:_equal(p['sourceCodeHash'],fixed['expectedCodeHash'],'preseal_zzz_codehash_mismatch')
            complete=[D.canonical(p) for p in policies if _known(p)]
            if len(complete)!=len(set(complete)):D.fail('preseal_duplicate_conversion_route')
        if routes['conversion_enabled'] is True and policies==[]:D.fail('preseal_enabled_converter_without_route')
    conf=s['confirmation']
    if conf is not None:
        _bounds(conf['secondsRequired'],60,604800,'preseal_confirmation_duration')
        _bounds(conf['maximumGap'],0,302400,'preseal_confirmation_gap')
        if conf['maximumGap'] is not None and conf['secondsRequired'] is not None and int(conf['maximumGap'])>int(conf['secondsRequired'])//2:D.fail('preseal_confirmation_gap')
        if conf['requireReferenceExit'] is False:D.fail('preseal_reference_guard_required')
    vrf=s['randomness']
    if vrf is not None:
        if vrf['coordinator'] in top|set(used):D.fail('preseal_vrf_is_protocol_address')
        _bounds(vrf['subscriptionId'],1,(1<<256)-1,'preseal_vrf_subscription')
        _bounds(vrf['confirmations'],3,200,'preseal_vrf_confirmations')
        _bounds(vrf['callbackGas'],200000,10000000,'preseal_vrf_callback')
    up=s['seadrop_upstream']
    if up is not None:
        for name in ('existingFeeRecipients','existingPayers','existingSigners','existingTokenGated'):
            if up[name] is not None and up[name]!=[]:D.fail('preseal_upstream_not_fresh')
    if s['mint_end'] is not None:_bounds(s['mint_end']['end'],1,(1<<64)-1,'preseal_mint_end')
    return result


def _canonical_type(item):
    typ=item['type']
    return '('+','.join(_canonical_type(x) for x in item['components'])+')'+typ[5:] if typ.startswith('tuple') else typ


def _dynamic(item):
    typ=item['type']
    return typ.endswith('[]') or typ in ('bytes','string') or typ=='tuple' and any(_dynamic(x) for x in item['components'])


def _size(item):
    if _dynamic(item):return 32
    return sum(_size(x) for x in item['components']) if item['type']=='tuple' else 32


def _tuple(items,values):
    if len(items)!=len(values):D.fail('preseal_abi_arguments')
    head=[];tail=b'';length=sum(_size(i) for i in items)
    for item,value in zip(items,values):
        encoded=_encode(item,value)
        if _dynamic(item):head.append((length+len(tail)).to_bytes(32,'big'));tail+=encoded
        else:head.append(encoded)
    return b''.join(head)+tail


def _encode(item,value):
    typ=item['type']
    if typ.endswith('[]'):
        if type(value)is not list or len(value)>16:D.fail('preseal_abi_array')
        child=dict(item,type=typ[:-2]);return len(value).to_bytes(32,'big')+_tuple([child]*len(value),value)
    if typ=='tuple':
        D._keys(value,[x['name'] for x in item['components']])
        return _tuple(item['components'],[value[x['name']] for x in item['components']])
    if typ=='string':
        if type(value)is not str:D.fail('preseal_abi_string')
        raw=value.encode('utf-8');return len(raw).to_bytes(32,'big')+raw+b'\0'*((-len(raw))%32)
    if typ=='address':return bytes.fromhex(D._address(value,True)[2:]).rjust(32,b'\0')
    if typ=='bytes32':
        if type(value)is not str or re.fullmatch(r'0x[0-9a-f]{64}',value)is None:D.fail('preseal_abi_hash')
        return bytes.fromhex(value[2:])
    if typ=='bool':
        if type(value)is not bool:D.fail('preseal_abi_boolean')
        return int(value).to_bytes(32,'big')
    if typ.startswith(('uint','int')):
        signed=typ.startswith('int');bits=int(typ[3:] if signed else typ[4:]);number=int(_normal(value,typ))
        return (number%(1<<256)).to_bytes(32,'big')
    D.fail('preseal_unsupported_abi_type')


class _ABI:
    def __init__(self,artifacts):self.artifacts=artifacts;self.used={}
    def function(self,contract,name):
        _,obj,_=self.artifacts.contract(contract)
        rows=[x for x in obj['abi'] if x['type']=='function' and x['name']==name]
        if len(rows)!=1 or rows[0]['stateMutability']!='nonpayable':D.fail('preseal_function_abi_changed')
        row=rows[0];sig=name+'('+','.join(_canonical_type(x) for x in row['inputs'])+')'
        self.used[contract+'.'+name]={'signature':sig,'sha256':D.sha(D.canonical(row))}
        return row,sig
    def encode(self,contract,name,values):
        row,sig=self.function(contract,name)
        raw=D.keccak256(sig.encode())[:4]+_tuple(row['inputs'],values)
        if len(raw)>64*1024:D.fail('preseal_calldata_bound')
        return sig,'0x'+raw.hex(),[{'name':i['name'],'type':_canonical_type(i),'value':v} for i,v in zip(row['inputs'],values)]
    def pool_id(self,key):
        row,_=self.function('ZZZPoolRegistry','configureNative');item=row['inputs'][0]['components'][0]
        return '0x'+D.keccak256(_encode(item,key)).hex()


def _drop(value,constructor,root):
    file=Path(value['artifact_path'])
    try:
        if not file.is_file() or file.stat().st_size>DROP.MAX_OUTPUT:D.fail('preseal_drop_unavailable_or_invalid')
        with file.open('rb') as stream:raw=stream.read(DROP.MAX_OUTPUT+1)
        if len(raw)>DROP.MAX_OUTPUT or D.sha(raw)!=value['artifact_sha256']:D.fail('preseal_drop_digest')
        artifact=DROP.decode(raw,DROP.MAX_OUTPUT);DROP.check(artifact,root)
    except D.PlanError:raise
    except Exception as exc:raise D.PlanError('preseal_drop_unavailable_or_invalid') from exc
    request=artifact['request'];a=constructor['planned_addresses'];i=constructor['inputs']
    for left,right in ((request['chain_id'],'4663'),(request['nft_contract'],a['nft']),
                       (request['seadrop'],i['seadrop']),(request['seadrop_runtime_keccak256'],i['seadrop_codehash']),
                       (request['creator_payout_address'],i['mint_recipient'])):
        _equal(left,right,'preseal_drop_identity_mismatch')
    if request['mint_price_wei']!=INITIAL_MINT_PRICE:D.fail('preseal_initial_sale_price')
    return artifact,raw


def _seal_boundary_review(construction,assigned,*,royalty_balance_supported=False):
    """Expose irreversible prerequisites; offline assignments never prove them."""
    constructors=[]
    for row in construction['instances']:
        arguments=copy.deepcopy(row['arguments'])
        if row['mode']=='inert_internal_create_only':
            for argument in arguments:
                raw=bytes.fromhex(argument['value'][2:])
                argument['value']={'kind':'accepted_inert_code_commitment','bytes':len(raw),'sha256':D.sha(raw)}
        constructors.append({'role':row['role'],'contract':row['contract'],'mode':row['mode'],
            'assigned_address':assigned.get(row['role']),'constructor_arguments':arguments,
            'actual_identity_verified':False,
            'recovery':'Wrong fixed identity requires reviewed reconstruction before use; source publication does not replace a deployed module.'})
    checks=[
        ('chain','vault',['canonicalChainId()'],'Must equal the actual deployment chain4663; an immutable wrong home is not repaired by unpause.'),
        ('module_graph','access',['bootstrap()','isSealed()','protocolPolicy()','module(bytes32)'],'Verify all16 unique modules, policy and reciprocal controller/companion identities from actual deployed code.'),
        ('artwork','nft',['artworkBaseURI()','metadataRenderer()'],'Nonempty reviewed immutable content root and matching renderer; constructor-empty setup needs the one-time setBaseURI before seal. Nonempty is not content proof.'),
        ('seadrop_binding','nft',['seaDropMint()'],'For this OpenSea release the exact collection-specific helper must already be bound. Zero-helper direct mint is only a separate explicit local profile; seal cannot be undone to add the helper.'),
        ('seadrop_identity','seadrop_mint',['nft()','seaDrop()','seaDropCodeHash()','configured()','mintConfig()'],'Verify NFT/controller and exact reviewed SeaDrop runtime, all sale/proof/payment/payer settings and actual platform acceptance. The immutable SeaDrop cannot be rotated in place.'),
        ('lp_converter_binding','rewards',['converter()'],'The exact reciprocal LP converter must be bound before seal; otherwise fixed-ZZZ LP fees cannot become ETH through this deployment.'),
        ('lp_converter_identity','lp_converter',['ledger()','access()'],'Verify the current Rewards/controller and reviewed native conversion capability; routes may be configured later, the converter binding may not.'),
        ('fixed_zzz','migration',['currentZZZ()'],'Contribution identity, Rewards asset, Buyback target and holder-return token must all be the single reviewed fixed ZZZ.'),
        ('native_venue','liquidity',['poolManager()','stateView()','permit2()','balancingRouter()'],'Verify the complete fixed core/periphery/child graph against the admitted native deployment; an internally coherent wrong graph may still be permanently unusable.'),
        ('randomness','nft',['randomnessConfigured()','randomnessCoordinator()','nextToFinalize()','mintedCount()'],'Configure and qualify the original provider/subscription/consumer/callback before minting. Future rotation requires all old draws finalized; pending results cannot be rerolled.'),
        ('launch_role','access',['canonicalState()','preparationActive()','lpExitStarted()'],'This planner is for a fresh standalone launch: operating state0, no preparation and no terminal exit. A replacement importer needs its own reviewed pre-seal prepareImport sequence.'),
        ('sale_end','royalty_rewards',['mintEnd()','mintEndRevision()','royaltiesOpenAt()','royaltiesOpen()'],'Before enabling sale, verify the final end is future at execution and matches OpenSea. Opening finalization is private: use authenticated RoyaltyOpeningFinalized event/state history; royaltiesOpen is a time predicate, not proof of finalization. An unset end may be initialized after seal; a previously configured nonzero end that expires during bootstrap cannot currently be reset, even before any mint.'),
        ('bucket_reservations','vault',['bucketCount()','bucketAt(uint256)','poolBucket(bytes32)'],'New bucket IDs must equal VaultCanonical.bucketIdentity(pool); existing registered aliases remain valid for pool moves. Inspect every retained slot before irreversible reservation; there is no unreserve and capacity stays four.'),
        ('reservation_validator','migration',['validation()'],'Before a first reservation, verify the fixed CustodyValidation parent/controller and reviewed runtime. Its public validReservationIdentity is only a read, not full pool admission or authority; an empty registered alias is not a new activation domain.'),
        ('royalty_workload','royalty_rewards',['assetCapacity()','MAX_ERC20_ASSETS()','MAX_ASSETS()','assetCount()','assets(uint256)'],'Enumerate the actual admitted currencies, with native ETH at index0. The initial capacity is16 ERC20 currencies plus native ETH, not17 already-admitted assets; reviewed capacity can expand to64 ERC20s plus ETH. Capacity alone is not aggregate gas qualification. Measure healthy, pending-receipt and gas-consuming fault workloads before currency admission or any capacity increase, preserving exact entitlements.'),
        ('gas_policy','protocol_policy',['gasPolicy()','payoutGas()','sourceCallGas()','royaltySyncGas()','gasFingerprint()'],'Verify actual per-call gas settings and their fingerprint. A per-currency sync budget is not a whole-transaction guarantee. Qualify aggregate work, exact calls and estimates, full20% activation-policy2 or25% maintenance headroom, selected service budgets, actual block bounds and complete fees. No gas limit, capacity, setting or operating approval is adopted by this checklist.'),
    ]
    if royalty_balance_supported:
        checks.append(('royalty_allocation_profile','royalty_rewards',
            ['ROYALTY_ALLOCATION_VERSION()','ROYALTY_SETTLEMENT_VERSION()'],
            'Verify exact fresh payload5/runtime identity and allocation version2; original-currency '
            'settlement remains4. Old tree-backed payload3/4 must not be relabelled as round counters. '
            'Neither the scalar version nor an internal review supplies release qualification.'))
        checks.append(('royalty_balance_read_policy','protocol_policy',
            ['royaltyBalanceGas()','gasPolicy()','gasFingerprint()'],
            'Read the separate activation-only ERC20 balance-call allowance in raw gas units (10000..1000000). '
            'The fresh source default50000 is not an observed or qualified setting. The legacy gas tuple '
            'and full royaltySyncGas allowance remain separate; ordinary sync/claim/canonical reads are not '
            'limited by this activation cap. A cap change increments its gas revision. '
            'Qualify exact selected currencies, delayed receipts and fault workloads within the unchanged '
            '20M contribution budget with full20% headroom. This check adopts no cap or readiness.'))
    bindings={'seadrop_binding':assigned.get('seadrop_mint'),'lp_converter_binding':assigned.get('lp_converter')}
    return {
        'schema':1,'scope':'Selected fresh OpenSea launch; not a generic seal validator or importer preparation.',
        'readiness':'blocked_pending_live_and_content_review','all_preconditions_verified':False,
        'rpc_performed':False,'seal_calldata':None,
        'constructor_boundaries':constructors,
        'inert_data_scope':'Immutable accepted-code parts are byte-length/hash commitments here; exact bytes remain in the separately authenticated construction plan.',
        'checks':[{'id':key,'target_role':role,'assigned_target':assigned.get(role),
            'required_reads':reads,'requirement':requirement,'expected_binding':bindings.get(key),
            **({'required_read_inputs':{'assets(uint256)':{'index':{'type':'uint256',
                'format':'canonical unsigned decimal string','range':'0 <= index < observed assetCount()',
                'first_index':'0','source':'Enumerate the observed current ledger; no count is assumed.'}}}}
                if key=='royalty_workload' else {}),
            'status':'unverified','verified':False} for key,role,reads,requirement in checks],
        'settings_are_offline_assignments':True,
    }


def prepare(raw,root=D.ROOT,build_profile=D.DEFAULT_BUILD_PROFILE):
    D.trusted_build(build_profile)
    if build_profile!=D.DEFAULT_BUILD_PROFILE:D.fail('preseal_current_build_required')
    value=validate(copy.deepcopy(raw));producer=producer_sources()
    construction=D.prepare(value['constructor_input'],root=root,build_profile=build_profile)
    artifacts=D.Artifacts(root,build_profile);abi=_ABI(artifacts)
    _,policy_object,_=artifacts.contract('ZZZProtocolPolicy')
    balance_supported=any(item.get('type')=='function' and item.get('name')=='setRoyaltyBalanceGas'
                          for item in policy_object['abi'])
    if 'royalty_balance_policy' in value and not balance_supported:D.fail('preseal_royalty_balance_profile_required')
    registry=artifacts.input['sources']['src/ZZZPoolRegistry.sol']['content'].lower()
    symbols={'pool_manager':'core','position_manager':'posm','state_view':'state','permit2':'permit2','zzz':'zzz'}
    for role,(address,pin) in NATIVE_DEPENDENCIES.items():
        if (address.lower() not in registry or re.search(r'\b'+symbols[role]+r'\.codehash\s*!=\s*'+re.escape(pin.lower())+r'\b',registry) is None):
            D.fail('preseal_native_registry_pin_drift')
    c=value['constructor_input'];a=c['planned_addresses'];i=c['inputs'];s=value['settings'];bootstrap=value['bootstrap']
    assigned={**a,**value['child_addresses']};rows=[];completed=set();all_missing=[];drop=None;drop_raw=None;pool_ids={}
    if _known(s['seadrop_terms']):drop,drop_raw=_drop(s['seadrop_terms'],c,root)
    # Validate known cross-family relations even when another family is unknown.
    if s['native_pools'] is not None and s['native_pools']['pools'] is not None:
        for item in s['native_pools']['pools']:
            if item is not None and _known(item['config']['key'] if item['config'] else None):
                pid=abi.pool_id(item['config']['key'])
                if pid in pool_ids:D.fail('preseal_duplicate_pool')
                pool_ids[pid]=item['config']
                if item['config']['depositsEnabled'] is True and pid!=SELECTED_POOL:D.fail('preseal_initial_contribution_pool')
    if s['routes'] is not None and s['routes']['execution_pool_ids'] is not None and s['native_pools'] is not None and _known(s['native_pools']):
        for pid in s['routes']['execution_pool_ids']:
            if pid is not None and (pid not in pool_ids or pool_ids[pid]['operationsEnabled'] is not True):D.fail('preseal_execution_pool_not_admitted')
    if drop is not None and s['mint_end'] is not None:_equal(s['mint_end']['end'],drop['mint_config']['publicEnd'],'preseal_mint_end_mismatch')
    specs={row['id'].split(':',1)[1]:row for row in D.construction_order() if row['kind']=='unverified_setup_checklist'}
    if tuple(specs)!=STEPS:D.fail('preseal_setup_graph_changed')
    dependencies={name:[d.split(':',1)[1] for d in specs[name]['requires'] if d.startswith('configure:')] for name in STEPS}
    dependencies['native_pools']=list(dict.fromkeys(dependencies['native_pools']+['migration_zzz']))
    dependencies['seadrop_upstream']=['seadrop_terms'];dependencies['mint_end']=['seadrop_terms','seadrop_upstream']
    def add(calls,role,contract,name,args):
        calls.append((role,contract,name,args))
    for step in STEPS:
        setting=s[step];missing=_missing(setting,'settings.'+step);calls=[]
        if bootstrap is None:missing.append('bootstrap')
        if not construction['input_assignments_complete']:missing+=['constructor_input.'+x for x in construction['missing_inputs']]
        for dep in dependencies[step]:
            if dep not in completed:missing.append('requires.configure:'+dep)
        needs_drop=step in ('seadrop_terms','seadrop_upstream','mint_end')
        if needs_drop and drop is None:missing.append('requires.reviewed_seadrop_manifest')
        if _known(setting) and (not needs_drop or drop is not None):
            if step=='dual_usd':
                for asset,token in (('eth',D.ZERO),('zzz',i['zzz'])):
                    p=setting[asset];add(calls,'oracle','ZZZOracle','setDualFeed',[token,p['primary'],p['secondary'],p['maxDeviationBps'],p['reviewHash']])
            elif step=='fixed_zzz':add(calls,'activation_assets','ZZZActivationAssets','configureZZZ',[i['zzz'],setting['expectedCodeHash'],setting['reviewHash']])
            elif step=='lp_asset':add(calls,'rewards','ZZZRewards','addAsset',[i['zzz']])
            elif step=='migration_zzz':add(calls,'migration','ZZZMigration','configureZZZ',[i['zzz'],setting['codeHash'],setting['reviewHash']])
            elif step=='execution_sources':
                for p in setting['sources']:add(calls,'oracle','ZZZOracle','setExecutionSource',[p['source'],True,p['expectedCodeHash'],p['reviewHash']])
            elif step=='native_pools':
                for p in setting['pools']:
                    pid=abi.pool_id(p['config']['key'])
                    add(calls,'pools','ZZZPoolRegistry','configureNative',[p['config']])
                    add(calls,'strategy','ZZZStrategy','setRangeOrientation',[pid,p['orientation']])
            elif step=='routes':
                add(calls,'balancing_router','ZZZLPBalancer','configureExecutionPools',[setting['execution_pool_ids'],setting['execution_review_hash']])
                for p in setting['conversion_routes']:add(calls,'lp_converter','ZZZLPRewardConverter','addV4Route',[p])
                add(calls,'lp_converter','ZZZLPRewardConverter','setEnabled',[setting['conversion_enabled']])
            elif step=='confirmation':
                add(calls,'rebalance_confirmation','ZZZRebalanceConfirmation','configure',[setting['secondsRequired'],setting['maximumGap'],setting['reviewed']])
                add(calls,'rebalance_confirmation','ZZZRebalanceConfirmation','setRequireReferenceExit',[setting['requireReferenceExit'],setting['referenceReview']])
            elif step=='randomness':add(calls,'protocol_policy','ZZZProtocolPolicy','configureRandomness',[setting[k] for k in SETTINGS[step]])
            elif step=='seadrop_terms':add(calls,'seadrop_mint','ZZZSeaDropMint','configure',[drop['mint_config'],drop['request']['mint_price_wei'],drop['review_hash']])
            elif step=='seadrop_upstream':
                add(calls,'nft','ZZZNFT','updatePublicDrop',[i['seadrop'],drop['public_drop']])
                add(calls,'nft','ZZZNFT','updateAllowList',[i['seadrop'],{'merkleRoot':drop['allowlist_root'],'publicKeyURIs':setting['publicKeyURIs'],'allowListURI':setting['allowListURI']}])
                add(calls,'nft','ZZZNFT','updateDropURI',[i['seadrop'],setting['dropURI']])
                add(calls,'nft','ZZZNFT','updateCreatorPayoutAddress',[i['seadrop'],i['mint_recipient']])
                add(calls,'nft','ZZZNFT','updateAllowedFeeRecipient',[i['seadrop'],drop['request']['fee_recipient'],True])
                for payer in drop['request']['allowed_payers']:add(calls,'nft','ZZZNFT','updatePayer',[i['seadrop'],payer,True])
            elif step=='mint_end':add(calls,'nft','ZZZNFT','setMintEnd',[setting['end']])
        # All fixed ABI selectors are checked even if the family is blocked.
        for role,contract,name,args in calls:
            abi.function(contract,name)
            if assigned.get(role) is None:missing.append('addresses.'+role)
            if not _known(args):missing.append('arguments.'+contract+'.'+name)
        missing=sorted(set(missing));prepared=not missing
        planned=[]
        for ordinal,(role,contract,name,args) in enumerate(calls):
            item={'ordinal':ordinal,'target_role':role,'to':assigned.get(role),'contract':contract,'function':name,
                  'from':bootstrap,'value':'0','calldata':None,'arguments':None,'authority_verified':False,
                  'conditional_caller':'actual Access.bootstrap() before sealing; no caller/control proof'}
            if prepared:
                item['signature'],item['calldata'],item['arguments']=abi.encode(contract,name,args)
            else:item['signature']=abi.function(contract,name)[1]
            planned.append(item)
        if prepared:completed.add(step)
        all_missing+=missing
        rows.append({'id':'configure:'+step,'status':'unsigned_inputs_complete_pending_live_verification' if prepared else 'blocked_missing_inputs',
            'inputs_prepared':prepared,'requires':['configure:'+d for d in dependencies[step]],'missing_inputs':missing,
            'calls':planned,'live_preconditions_verified':False,
            'construction_assumptions':specs[step]['requires']})
    complete=len(completed)==len(STEPS)
    optional_balance={'requested':False,'status':'not_requested','inputs_prepared':False,'calls':[],
        'live_preconditions_verified':False,'setting_adopted':False}
    if 'royalty_balance_policy' in value:
        setting=value['royalty_balance_policy'];missing=_missing(setting,'royalty_balance_policy')
        if bootstrap is None:missing.append('bootstrap')
        if not construction['input_assignments_complete']:
            missing+=['constructor_input.'+x for x in construction['missing_inputs']]
        if assigned.get('protocol_policy') is None:missing.append('addresses.protocol_policy')
        missing=sorted(set(missing));prepared=not missing
        function=abi.function('ZZZProtocolPolicy','setRoyaltyBalanceGas')[1]
        call={'target_role':'protocol_policy','contract':'ZZZProtocolPolicy','function':'setRoyaltyBalanceGas',
            'signature':function,'to':assigned.get('protocol_policy'),'from':bootstrap,'value':'0',
            'calldata':None,'arguments':None,'authority_verified':False,
            'conditional_caller':'actual Access.bootstrap() before sealing; no caller/control proof'}
        if prepared:
            call['signature'],call['calldata'],call['arguments']=abi.encode('ZZZProtocolPolicy',
                'setRoyaltyBalanceGas',[setting['balanceGas'],setting['reviewHash']])
        optional_balance.update(requested=True,status='unsigned_inputs_complete_pending_live_verification' if prepared else
            'blocked_missing_inputs',inputs_prepared=prepared,calls=[call],missing_inputs=missing)
        all_missing+=missing;complete=complete and prepared
    stopped=[]
    if s['routes'] is not None:
        if s['routes']['execution_pool_ids']==[]:stopped.append('Empty execution pool list disables ordinary balancing swaps.')
        if s['routes']['conversion_enabled'] is False:stopped.append('LP conversion is explicitly disabled; pending fixed-ZZZ is not claimable ETH.')
    if s['confirmation'] is not None and s['confirmation']['maximumGap']=='0':stopped.append('A zero observation gap stops ordinary confirmed rebalancing.')
    if _known(s['native_pools']):
        if not any(p['config']['depositsEnabled'] for p in s['native_pools']['pools']):
            stopped.append('All initial pools have contributions disabled.')
        for p in s['native_pools']['pools']:
            if not p['config']['operationsEnabled']:
                stopped.append('Pool '+abi.pool_id(p['config']['key'])+' has ordinary LP operations disabled; '
                    'contributions, compounding and ordinary rebalancing are stopped for that pool.')
    result={'schema':SCHEMA,'kind':'offline_preseal_configuration_review','profile':PROFILE,'chain_id':'4663',
        'build_profile':build_profile,'offline_only':True,**{name:False for name in FALSE_FLAGS},
        'configuration_inputs_complete':complete,
        'status':'complete_unsigned_preseal_review_pending_live_verification' if complete else 'blocked_preview_missing_inputs',
        'input_sha256':D.sha(D.canonical(value)),'producer_sources':producer,
        'constructor_review':{'manifest_sha256':construction['manifest_sha256'],'status':construction['status'],
            'accepted_build':construction['accepted_build'],'counts':construction['counts'],
            'input_assignments_complete':construction['input_assignments_complete']},
        'address_scope':'Unverified top-level assignments and actual-getter child assignments only; no CREATE/factory prediction.',
        'planner_limits':{'input_bytes':D.MAX_INPUT,'output_bytes':D.MAX_OUTPUT,'calldata_bytes_per_call':65536,
            'principal_pools_per_review':4,'conversion_routes_per_review':4,'execution_sources_per_review':2,
            'array_encoding_per_call':16,'bounds_scope':'Local review workload bounds, not lifetime on-chain pool/route capacity.'},
        'bootstrap':bootstrap,'settings_scope':'Fresh unsealed zero-mint graph only; no resume or adoption of existing configuration.',
        'seal_boundary_review':_seal_boundary_review(construction,assigned,royalty_balance_supported=balance_supported),
        'optional_royalty_balance_policy':optional_balance,
        'steps':rows,'missing_inputs':sorted(set(all_missing)),'abi_functions':abi.used,
        'explicit_operating_stops':stopped,
        'pool_ids':list(pool_ids),'seadrop_manifest':None if drop is None else {
            'artifact_sha256':D.sha(drop_raw),'review_hash':drop['review_hash'],'allowlist_root':drop['allowlist_root'],
            'proof_count':len(drop['proofs']),'source_bindings_verified_offline':True,'onchain_settings_verified':False},
        'unchanged_constructor_defaults':{'mint_price_wei':INITIAL_MINT_PRICE,'contribution_loss_bps':'300',
            'conversion_loss_bps':'100','maintenance_loss_bps':'300','additional_loss_bps':'100',
            'position_trigger_bps':'8500','hybrid_enabled':False,'adaptive_keeper_range_enabled':False,
            'live_defaults_verified':False},
        'release_prerequisites':[
            'Verify NFT.artworkBaseURI is nonempty and matches reviewed content before sealing. An empty constructor root requires the one-time bootstrap NFT.setBaseURI first; this configuration planner emits neither that call nor seal.',
            'Independently verify chain4663, all creation receipts/runtime immutables/getters and bindings, zero mintedCount, unsealed actual bootstrap/canConfigure and canonical operating/no preparation/exit state.',
            'Every emitted call is conditional unsigned calldata, not a transaction envelope or permission to send. Reconcile actual current state, simulate exact calls, estimate full fees and separately authorize execution.',
            'Qualify live token/source code, decimals, round freshness/age/agreement, genuine independent valuation paths and publication/liveness. Supplied source IDs/hashes are not proof of independence.',
            'Execution references must prove actual external markets, avoid duplicate reference cores/pools and principal-as-reference. Route admission is not best execution, useful depth or full-operation loss qualification.',
            'Validate initialized native pools, live protocol fees and all quote/deployment/output budgets. Empty execution lists disable swaps; gap0 stops confirmation; disabled conversion is not ETH-settlement readiness.',
            'Qualify supported VRF subscription funding/consumer/callback, exact pinned SeaDrop onboarding/code, actual upstream empty lists and sale/payer/fee/payment terms.',
            'Before each call, recheck current salePolicy mintPrice remains 0.05ETH, its recipient, helper/root/payer/upstream settings and sale windows. NFT.setMintEnd end must remain strictly later than its inclusion-block timestamp and match the reviewed final publicEnd; no local clock or offline plan proves that timing.',
            'Keep public signing disabled and existing chains/journals/sites/services/heartbeat unchanged. Metadata, providers, 20M/24M gas profiles, hosting/recovery and independent release approval remain separate.'],
        'excluded_capabilities':['No RPC/signing/submission, gas/nonce planning or authority adoption.',
            'No seal, public deployment, arbitrary selector/target, integrated bridge, principal movement, reward swap or contract upgrade.',
            'No source/default/limit changes, arbitrary prior configuration clearing, partial-deployment resume or production approval.']}
    artifacts.check_sources()
    if producer_sources()!=producer:D.fail('preseal_source_changed_during_preparation')
    if drop is not None:
        try:
            with Path(s['seadrop_terms']['artifact_path']).open('rb') as stream:now=stream.read(DROP.MAX_OUTPUT+1)
        except Exception as exc:raise D.PlanError('preseal_drop_changed') from exc
        if now!=drop_raw:D.fail('preseal_drop_changed')
    result['manifest_sha256']=D.sha(D.canonical(result))
    return result
