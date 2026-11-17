"""Offline fresh-deployment constructor review; never RPC, signing or deployment.

Addresses are unverified operator assignments, not CREATE predictions. Source
constructor bytes and size checks cannot establish live code, caller or release
readiness. Factory-created addresses are deliberately discovered by getters.
"""
from __future__ import annotations
import argparse,gzip,hashlib,io,json,os,re,sys,tempfile
from pathlib import Path
from zzz_ops.abi import keccak256
ROOT=Path(__file__).resolve().parents[1]
BUILD='reports/manual-reference-swap-fix-20261115/build'
PROFILE='schema17/mint2/V10/execution1/LP3'
ZERO='0x'+'0'*40
MAX_INPUT=64*1024;MAX_BUILD=64*1024*1024;MAX_OUTPUT=16*1024*1024
LIMITS={'runtime_bytes':24576,'full_initcode_bytes':49152}
BUILD_PINS={
 'compiler-input.json.gz':'da046010ffef2efe32870d58478f11ed52a25a7932b4726768bc9fe1ef1abfd3',
 'compiler-output.json.gz':'d18a51c0f5d19c6abec3fbad7f50d9997c9e5b65c10ad80c7299c942234a19b4',
 'source-manifest.json':'c1fbb683be3735d4558f553acb1af0153ffaf74b808e113a760fcde30bd8af4b',
 'production-size-gates.json':'43b3bdbe58c31893b9e648f3cc2e565e096a730f089abef4745f8fe3a7f78633',
 'START.json':'02d9a986e74cf2b6f2dd4f36bcb58db65af21de0ab43f6acf440b62da36e9d90',
 'ARTIFACTS.json':'8adb7a01a5e159b04348baebfcb8022ed633e1cc3df55d32ad9b7367323a67b1'}
# Historical constants stay exact for the original construction capture. A
# profile label alone cannot adopt newer objects or reinterpret old evidence.
LEGACY_BUILD_PROFILE='manual-reference-20261115'
PREVIOUS_BUILD_PROFILE='metadata2-20261116'
DEFAULT_BUILD_PROFILE='operator-seal-20261117'
TRUSTED_BUILDS={
 LEGACY_BUILD_PROFILE:{'directory':BUILD,'files':BUILD_PINS,
  'source_inventory':'source-manifest.json','source_key':'exact_source_sha256','gates':'production-size-gates.json'},
 PREVIOUS_BUILD_PROFILE:{'directory':'reports/metadata-lifecycle-fixes-20261116/build','files':{
  'compiler-input.json.gz':'596dbb7967cc51f0b854c8be20644facaadc15ceabe8ee2acfadf4bd8d20df41',
  'compiler-output.json.gz':'4acc319da1a5b4e8a4c112fb9a6c0832d3943d2722d2d17f30dd288c125f3a0f',
  'normal-size-evidence.json':'b67e4d9cdf645e1433bca7569c7ad5be6d46237cce944f100cff6fc8d054b07e',
  'RESULT.json':'74ee74839b689bbc08ba17bfc94bdb468e16dbd75931caddb251e1485bb92c22',
  'START.json':'966add935532fccffbbb2518fe094aabb50e456462e5e5dd3dab62c71d76b5d8'},
  'source_inventory':'START.json','source_key':'source_sha256','gates':'normal-size-evidence.json'},
 DEFAULT_BUILD_PROFILE:{'directory':'reports/operator-behavior-followup-20261117/build','files':{'compiler-input.json.gz': '574c37b4b29c24e8666ee08d6fba6d0019e587854526fc02584e4cd23cb2c434', 'compiler-output.json.gz': '14c1ce5044ea6d5e2d74aea2ff0e5a32e782bce37e1fe83c88e8b458c8f53806', 'normal-size-evidence.json': '6fcdfc4368a3c6efe77540140ca38da029e6c29987f5a39cd849a3e483934927', 'START.json': 'ea15822d8831e5705c4ac527f8fc18d712a00662b71e8a4010b250baa08c301a'},
  'source_inventory':'START.json','source_key':'source_sha256','gates':'normal-size-evidence.json'}}
NATIVE={
 'pool_manager':'0x8366a39cc670b4001a1121b8f6a443a643e40951',
 'position_manager':'0x58daec3116aae6d93017baaea7749052e8a04fa7',
 'state_view':'0xf3334192d15450cdd385c8b70e03f9a6bd9e673b',
 'permit2':'0x000000000022d473030f116ddee9f6b43ac78ba3',
 'zzz':'0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'}
SEADROP='0x00005ea00ac477b1030ce78506496e8c2de24bf5'
SEADROP_HASH='0x53e4b9339cf624803c9a7d0195576cca5b917920813508d86b3eb93dcbabeb5c'
INPUT_KEYS=('governance','keeper','guardian','mint_recipient','sequencer','pool_manager','position_manager','state_view','permit2','zzz','seadrop','seadrop_codehash','base_uri','buyback_maximum_trade_usd')
QUALIFICATIONS=('authorities','metadata','feeds','routes','vrf','opensea','fees_and_provider','operating_rehearsals','independent_audit')
# role, concrete constructor, argument sources. This closed graph is not a
# general-purpose compiler-object or arbitrary ABI transaction interface.
TOP=(
 ('access','ZZZAccessController',('i:governance','i:keeper','i:guardian')),
 ('protocol_policy','ZZZProtocolPolicy',('p:access','i:mint_recipient')),
 ('migration_budget','ZZZMigrationBudget',('p:access',)),
 ('metadata_renderer','ZZZNFTMetadata',('p:access',)),
 ('portfolio_policy','ZZZPortfolioPolicy',('p:access',)),
 ('rebalance_confirmation','ZZZRebalanceConfirmation',('p:access',)),
 ('balancing_router','ZZZLPBalancer',('p:access','i:pool_manager','i:state_view')),
 ('oracle','ZZZOracle',('p:access','i:sequencer')),
 ('liquidity','ZZZLiquidityManager',('p:access','i:position_manager','i:state_view','i:pool_manager','i:permit2','p:balancing_router')),
 ('pools','ZZZPoolRegistry',('p:access',)),
 ('strategy','ZZZStrategy',('p:access','p:portfolio_policy','p:rebalance_confirmation')),
 ('vault','ZZZVault',('p:access','chain','p:migration_budget')),
 ('rewards','ZZZRewards',('p:access',)),('fees','ZZZFeeController',('p:access',)),
 ('membership','ZZZMembership',('p:access',)),('migration','ZZZMigration',('p:access',)),
 ('compounder','ZZZCompounder',('p:access',)),
 ('buyback','ZZZBuyback',('p:access','i:zzz','i:buyback_maximum_trade_usd')),
 ('nft','ZZZNFT',('p:access','i:base_uri','p:metadata_renderer')),
 ('nft_canonical','ZZZNFTCanonical',('p:access','p:nft')),
 ('vault_canonical','ZZZVaultCanonical',('p:access','p:vault','chain')),
 ('fees_canonical','ZZZFeesCanonical',('p:access','p:fees')),
 ('canonical','ZZZCanonicalHandoff',('p:access',)),
 ('lp_converter','ZZZLPRewardConverter',('p:access','p:rewards','zero')),
 ('seadrop_mint','ZZZSeaDropMint',('p:access','p:nft','i:seadrop','i:seadrop_codehash')))
INTERNAL=(
 ('royalty_factory','ZZZRoyaltyFactory','access',(), 'Access.royaltyFactory()'),
 ('activation_assets_factory','ZZZActivationAssetsFactory','access',(), 'Access.activationAssetsFactory()'),
 ('lp_balance_math','ZZZLPBalanceMath','balancing_router',(), 'Balancer.balanceMath()'),
 ('lp_position_executor','ZZZLPPositionExecutor','liquidity',('p:access','i:position_manager','i:state_view','i:pool_manager','i:permit2','p:balancing_router'),'Manager.positionOperator()'),
 ('contribution_pricing','ZZZContributionPricing','oracle',('p:access','p:oracle'),'Oracle.contributionPricing()'),
 ('activation_assets','ZZZActivationAssets','activation_assets_factory',('p:access','p:pools'),'Registry.activationAssets(); AssetsFactory.assetsOf(Registry)'),
 ('activation_entry','ZZZActivationEntry','pools',('p:access','p:pools','g:Registry.activationAssets()'),'Registry.activationEntry()'),
 ('royalty_rewards','ZZZRoyaltyRewards','royalty_factory',('p:nft',),'NFT.royaltyRewards()'),
 ('claim_router','ZZZClaimRouter','nft',('p:access','p:nft','g:NFT.royaltyRewards()'),'NFT.claimRouter()'),
 ('rewards_canonical','ZZZRewardsCanonical','rewards',('p:access',),'Rewards.canonicalModule()'),
 ('custody_validation','ZZZCustodyValidation','migration',('p:access',),'Migration.validation()'),
 ('lp_v4_executor','ZZZV4RouteExecutor','lp_converter',(),'LPConverter.v4Executor()'))
TYPES={
 'ZZZAccessController':('address','address','address'),'ZZZProtocolPolicy':('address','address'),
 'ZZZLiquidityManager':('address',)*6,'ZZZLPPositionExecutor':('address',)*6,
 'ZZZLPBalancer':('address',)*3,'ZZZOracle':('address','address'),'ZZZStrategy':('address',)*3,
 'ZZZVault':('address','uint256','address'),'ZZZBuyback':('address','address','uint256'),
 'ZZZNFT':('address','string','address'),'ZZZVaultCanonical':('address','address','uint256'),
 'ZZZNFTCanonical':('address','address'),'ZZZFeesCanonical':('address','address'),
 'ZZZLPRewardConverter':('address',)*3,'ZZZSeaDropMint':('address','address','address','bytes32'),
 'ZZZActivationAssets':('address','address'),'ZZZActivationEntry':('address',)*3,
 'ZZZClaimRouter':('address',)*3,'ZZZContributionPricing':('address','address'),
 'ZZZRoyaltyFactory':(),'ZZZActivationAssetsFactory':(),'ZZZLPBalanceMath':(),'ZZZV4RouteExecutor':(),
 'ZZZRoyaltyCodeData':('bytes',)}
for _role,_name,_args in TOP:TYPES.setdefault(_name,('address',))
for _role,_name,_parent,_args,_getter in INTERNAL:TYPES.setdefault(_name,('address',))
MODULES=('vault','nft','liquidity','rewards','membership','fees','strategy','compounder','buyback','migration','oracle','pools','canonical','nft_canonical','vault_canonical','fees_canonical')

class PlanError(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)
def fail(code):raise PlanError(code)

def trusted_build(profile):
    # Admit a closed identifier before resolving or reading any build path.
    if type(profile)is not str or profile not in TRUSTED_BUILDS:fail('unsupported_build_profile')
    return TRUSTED_BUILDS[profile]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def _pairs(items):
    result={}
    for key,value in items:
        if key in result:fail('duplicate_json_key')
        result[key]=value
    return result
def decode(raw,maximum=MAX_INPUT):
    if type(raw) is not bytes or len(raw)>maximum:fail('input_size')
    try:return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=_pairs,parse_float=lambda _:fail('noninteger_json'),parse_constant=lambda _:fail('nonfinite_json'))
    except (UnicodeError,RecursionError,json.JSONDecodeError):fail('invalid_json')
def _keys(value,keys):
    if type(value) is not dict or set(value)!=set(keys):fail('input_shape')
def _address(value,zero=False):
    if type(value) is not str or re.fullmatch(r'0x[0-9a-fA-F]{40}',value) is None:fail('invalid_address')
    value=value.lower()
    if not zero and value==ZERO:fail('zero_address')
    return value
def _hash(value,prefix=True):
    if type(value) is not str or re.fullmatch(('0x' if prefix else '')+r'[0-9a-fA-F]{64}',value) is None or int(value,16)==0:fail('invalid_hash')
    return value.lower()
def _uint(value,bits=256,positive=False):
    if type(value) is not str or len(value)>78 or re.fullmatch(r'(0|[1-9][0-9]*)',value) is None:fail('invalid_integer')
    if int(value)>=1<<bits or positive and int(value)==0:fail('integer_bounds')
    return value

def template():
    return {'schema':1,'profile':PROFILE,'chain_id':'4663','planned_addresses':{role:None for role,_,_ in TOP},
        'inputs':{key:None for key in INPUT_KEYS},'qualification_evidence':{key:None for key in QUALIFICATIONS}}

def validate(raw):
    _keys(raw,('schema','profile','chain_id','planned_addresses','inputs','qualification_evidence'))
    if type(raw['schema']) is not int or raw['schema']!=1 or raw['profile']!=PROFILE:fail('unsupported_profile')
    if _uint(raw['chain_id'],positive=True)!='4663':fail('wrong_chain_profile')
    _keys(raw['planned_addresses'],(role for role,_,_ in TOP));_keys(raw['inputs'],INPUT_KEYS);_keys(raw['qualification_evidence'],QUALIFICATIONS)
    result=template();seen=set()
    for role,value in raw['planned_addresses'].items():
        if value is not None:
            value=_address(value)
            if value in seen:fail('duplicate_planned_address')
            seen.add(value)
        result['planned_addresses'][role]=value
    for key,value in raw['inputs'].items():
        if value is None:continue
        if key=='base_uri':
            if type(value) is not str:fail('invalid_uri')
            if len(value)>MAX_INPUT:fail('input_size')
            try:value.encode('utf-8')
            except UnicodeError:fail('invalid_uri')
            if value and not value.startswith(('ipfs://','ar://')):fail('invalid_uri')
        elif key=='buyback_maximum_trade_usd':value=_uint(value,128,True)
        elif key=='seadrop_codehash':value=_hash(value)
        else:value=_address(value,zero=key=='sequencer')
        result['inputs'][key]=value
    for key,value in raw['qualification_evidence'].items():
        if value is not None:result['qualification_evidence'][key]=_hash(value,False)
    for key,expected in NATIVE.items():
        if result['inputs'][key] not in (None,expected):fail('native_profile_mismatch')
    if result['inputs']['seadrop'] not in (None,SEADROP) or result['inputs']['seadrop_codehash'] not in (None,SEADROP_HASH):fail('seadrop_profile_mismatch')
    addresses=result['planned_addresses'];inputs=result['inputs']
    if inputs['governance'] is not None and inputs['governance']==addresses['access']:fail('governance_is_controller')
    # These fixed protocol/dependency implementations are not governance wallet
    # executors. A known collision cannot become a usable operator after seal.
    # Unknown wallet addresses still require the separate live authority review.
    if inputs['governance'] is not None and inputs['governance'] in seen:fail('governance_is_protocol_address')
    if inputs['governance'] in set(NATIVE.values())|{SEADROP}:fail('governance_is_external_dependency')
    if inputs['mint_recipient'] is not None and inputs['mint_recipient'] in {addresses[k] for k in ('access','protocol_policy','vault','nft','fees','rewards','migration')} - {None}:fail('excluded_mint_recipient')
    if seen.intersection(NATIVE.values()) or SEADROP in seen:fail('planned_address_is_external_dependency')
    return result

def encode_constructor(types,values):
    if len(types)!=len(values) or any(t not in ('address','uint256','bytes32','string','bytes') for t in types):fail('constructor_abi_shape')
    if any(value is None for value in values):return None
    head=[];tail=b'';head_size=32*len(types)
    for typ,value in zip(types,values):
        if typ in ('string','bytes'):
            data=value.encode('utf-8') if typ=='string' else value
            if type(data) is not bytes:fail('constructor_value')
            head.append((head_size+len(tail)).to_bytes(32,'big'));tail+=len(data).to_bytes(32,'big')+data+b'\0'*((-len(data))%32)
        elif typ=='address':head.append(bytes.fromhex(_address(value,True)[2:]).rjust(32,b'\0'))
        elif typ=='uint256':head.append(int(_uint(value)).to_bytes(32,'big'))
        else:head.append(bytes.fromhex(_hash(value)[2:]))
    return b''.join(head)+tail

def argument_length(types,values):
    total=32*len(types)
    for typ,value in zip(types,values):
        if typ in ('string','bytes'):
            if value is None:return None
            size=len(value.encode('utf-8')) if typ=='string' else len(value)
            total+=32+((size+31)//32)*32
    return total

class Artifacts:
    def __init__(self,root=ROOT,build_profile=DEFAULT_BUILD_PROFILE):
        spec=trusted_build(build_profile)
        self.profile=build_profile;self.root=Path(root).resolve();self.directory=self.root/spec['directory'];self.file_pins={};raws={}
        for name,pin in spec['files'].items():
            path=self.directory/name
            with path.open('rb') as stream:raw=stream.read(MAX_BUILD+1)
            if len(raw)>MAX_BUILD or sha(raw)!=pin:fail('accepted_build_changed')
            self.file_pins[name]=sha(raw);raws[name]=raw
        def unpack(name):
            with gzip.GzipFile(fileobj=io.BytesIO(raws[name])) as stream:raw=stream.read(MAX_BUILD+1)
            return decode(raw,MAX_BUILD)
        self.input=unpack('compiler-input.json.gz');self.output=unpack('compiler-output.json.gz')
        manifest=decode(raws[spec['source_inventory']],MAX_BUILD);self.source_pins=manifest[spec['source_key']]
        if len(self.input['sources'])!=100 or len(self.source_pins)!=100 or set(self.input['sources'])!=set(self.source_pins):fail('source_closure')
        settings=self.input['settings']
        if settings.get('evmVersion')!='cancun' or settings.get('viaIR') is not True or settings.get('optimizer')!={'enabled':True,'runs':1,'details':{'yul':False}}:fail('compiler_settings')
        if any(error.get('severity')=='error' for error in self.output.get('errors',[])):fail('compiler_errors')
        # The hash-pinned compiler report includes a fractional elapsed-time
        # measurement; constructor/user numbers still use strict integer JSON.
        gates=json.loads(raws[spec['gates']],object_pairs_hook=_pairs,parse_constant=lambda _:fail('nonfinite_json'))['gates']
        if len(gates)!=48 or not all(g['runtime_ok'] and g['creation_ok'] for g in gates):fail('normal_size_gates')
        self.check_sources()
    def check_sources(self):
        for name,pin in self.source_pins.items():
            path=(self.root/name).resolve()
            if not path.is_relative_to(self.root) or not path.is_file():fail('source_path')
            expected=len(self.input['sources'][name]['content'].encode('utf-8'))
            if path.stat().st_size!=expected:fail('source_changed')
            with path.open('rb') as stream:raw=stream.read(expected+1)
            if len(raw)!=expected or sha(raw)!=pin or raw.decode('utf-8')!=self.input['sources'][name]['content']:fail('source_changed')
    def contract(self,name):
        source='src/'+name+'.sol'
        try:obj=self.output['contracts'][source][name]
        except KeyError:fail('missing_contract')
        for field in ('bytecode','deployedBytecode'):
            code=obj['evm'][field]['object']
            if type(code) is not str or re.fullmatch(r'(?:[a-fA-F0-9]{2})+',code) is None:fail('unlinked_or_invalid_object')
        abi=next((row for row in obj['abi'] if row['type']=='constructor'),{'inputs':[]})['inputs']
        if tuple(item['type'] for item in abi)!=TYPES[name]:fail('constructor_abi_changed')
        return source,obj,abi

def _resolve(ref,value,parts):
    if ref=='zero':return ZERO
    if ref=='chain':return value['chain_id']
    prefix,name=ref.split(':',1)
    if prefix=='i':return value['inputs'][name]
    if prefix=='p':return value['planned_addresses'][name]
    if prefix=='d':return parts[int(name)]
    return None # Named getter discoveries stay unknown, never zero-filled.

def construction_order():
    steps=[]
    for role,name,_ in TOP:
        dependencies=[]
        if role!='access':dependencies.append('create:access')
        if role not in ('access','protocol_policy'):dependencies.append('bind:protocol_policy')
        dependencies+={'liquidity':['create:balancing_router'],'strategy':['create:portfolio_policy','create:rebalance_confirmation'],
            'vault':['create:migration_budget'],'nft':['create:metadata_renderer'],'nft_canonical':['create:nft'],
            'vault_canonical':['bind:vault'],'fees_canonical':['create:fees'],'lp_converter':['create:rewards'],'seadrop_mint':['create:nft']}.get(role,[])
        steps.append({'id':'create:'+role,'kind':'conditional_constructor','role':role,'requires':dependencies,'future_live_verification_required':True})
        if role=='protocol_policy':steps.append({'id':'bind:protocol_policy','kind':'bootstrap_binding','call':'Access.bindProtocolPolicy(policy)','requires':['create:access','create:protocol_policy'],'caller':'actual Access.bootstrap(), constructor CREATE sender; unresolved offline'})
        if role in MODULES:steps.append({'id':'bind:'+role,'kind':'bootstrap_module_binding','role':role,
            'module_id':'0x'+keccak256(name.encode()).hex(),'call':'Access.bind(moduleId,address)',
            'requires':['create:'+role],'caller':'actual Access.bootstrap(), constructor CREATE sender; unresolved offline'})
    steps.extend([
        {'id':'bind:lp_converter','kind':'bootstrap_helper_binding','call':'Rewards.bindConverter(converter)',
         'requires':['bind:rewards','create:lp_converter'],'caller':'actual Access.bootstrap(); unresolved offline'},
        {'id':'bind:seadrop_mint','kind':'bootstrap_helper_binding','call':'NFT.setSeaDropMint(helper)',
         'requires':['bind:nft','create:seadrop_mint'],'caller':'actual Access.bootstrap(); unresolved offline'}])
    setup=(
        ('dual_usd','Oracle.setDualFeed(ETH); Oracle.setDualFeed(fixedZZZ)',('bind:oracle','bind:protocol_policy')),
        ('fixed_zzz','ActivationAssets.configureZZZ(token,codeHash,reviewHash)',('bind:pools','configure:dual_usd')),
        ('lp_asset','Rewards.addAsset(fixedZZZ)',('bind:rewards','configure:fixed_zzz')),
        ('migration_zzz','Migration.configureZZZ(token,codeHash,reviewHash)',('bind:migration','bind:buyback','configure:lp_asset')),
        ('execution_sources','Oracle.setExecutionSource(reviewedReader,true,codeHash,reviewHash)',('bind:liquidity','configure:fixed_zzz','configure:dual_usd')),
        ('native_pools','PoolRegistry.configureNative(reviewedPoolConfig)',('bind:pools','bind:liquidity','configure:lp_asset','configure:dual_usd')),
        ('routes','Balancer.configureExecutionPools(reviewedPools,reviewHash); LPConverter route/enable review',('configure:execution_sources','configure:native_pools','bind:lp_converter')),
        ('confirmation','RebalanceConfirmation.configure(reviewedDuration,reviewedMaxGap,reviewHash)',('bind:strategy','create:rebalance_confirmation')),
        ('randomness','ProtocolPolicy.configureRandomness(reviewedProvider,settings)',('bind:protocol_policy','bind:nft')),
        ('seadrop_terms','SeaDropMint.configure(reviewedTerms,price,reviewHash)',('bind:seadrop_mint',)),
        ('seadrop_upstream','NFT-keyed upstream SeaDrop payout/drop/root/payer synchronization',('configure:seadrop_terms',)),
        ('mint_end','NFT.setMintEnd(final publicEnd)',('configure:seadrop_terms','configure:seadrop_upstream')))
    steps.extend({'id':'configure:'+key,'kind':'unverified_setup_checklist','call':call,'requires':list(deps),
        'caller':'actual authorized bootstrap before sealing; resolve after creation','inputs_prepared':False} for key,call,deps in setup)
    seen=set()
    for step in steps:
        if not set(step['requires'])<=seen:fail('graph_order')
        seen.add(step['id'])
    if len([step for step in steps if step['kind']=='bootstrap_module_binding'])!=16:fail('graph_module_bindings')
    return steps

def prepare(raw,root=ROOT,build_profile=DEFAULT_BUILD_PROFILE):
    value=validate(raw);artifacts=Artifacts(root,build_profile);rows=[];ledger=bytes.fromhex(artifacts.contract('ZZZRoyaltyRewards')[1]['evm']['bytecode']['object']);parts=(ledger[:24573],ledger[24573:])
    if not ledger or len(ledger)>49146:fail('royalty_code_parts')
    specs=[(role,name,'top_level',None,args,None) for role,name,args in TOP]+[(role,name,'internal_create_only',parent,args,getter) for role,name,parent,args,getter in INTERNAL]+[(f'royalty_data_part{i}','ZZZRoyaltyCodeData','inert_internal_create_only','royalty_factory',(f'd:{i}',),f'RoyaltyFactory.part{i}()') for i in range(2)]
    for role,name,mode,parent,refs,getter in specs:
        source,obj,abi=artifacts.contract(name);types=tuple(item['type'] for item in abi);values=[_resolve(ref,value,parts) for ref in refs]
        if len(refs)!=len(abi):fail('graph_constructor_arguments')
        encoded=encode_constructor(types,values);length=argument_length(types,values);creation=bytes.fromhex(obj['evm']['bytecode']['object']);template_runtime=bytes.fromhex(obj['evm']['deployedBytecode']['object']);runtime=(b'\x5f\x5f\xfd'+values[0]) if name=='ZZZRoyaltyCodeData' else template_runtime
        total=None if length is None else len(creation)+length
        if len(runtime)>LIMITS['runtime_bytes']:fail('runtime_size_limit')
        if total is not None and total>LIMITS['full_initcode_bytes']:fail('initcode_size_limit')
        args=[{'name':item['name'],'type':item['type'],'source':ref,'value':('0x'+v.hex()) if type(v) is bytes else v} for item,ref,v in zip(abi,refs,values)]
        row={'role':role,'contract':name,'source':source,'mode':mode,'creator_role':parent,'planned_address':value['planned_addresses'].get(role),
            'address_status':'unverified_operator_assignment' if mode=='top_level' else 'discover_actual_getter_no_nonce_prediction',
            'discovery':getter,'constructor_types':list(types),'arguments':args,'constructor_payload_complete':encoded is not None,
            'constructor_arguments_hex':None if encoded is None else '0x'+encoded.hex(),
            'full_initcode_hex':None if encoded is None else '0x'+(creation+encoded).hex(),'creation_bytes':len(creation),'creation_object_sha256':sha(creation),
            'constructor_argument_bytes':length,'full_initcode_bytes':total,'initcode_size_verified':total is not None,'initcode_margin':None if total is None else 49152-total,
            'runtime_bytes':len(runtime),'runtime_margin':24576-len(runtime),'runtime_hash_scope':'exact_returned_inert_data' if name=='ZZZRoyaltyCodeData' else 'unpatched_compiler_template_not_deployed_runtime',
            'runtime_sha256':sha(runtime),'runtime_is_actual_deployment_pin':False,'unresolved_bindings':[ref for ref,v in zip(refs,values) if v is None]}
        if name=='ZZZRoyaltyCodeData':row.update(returned_runtime_hex='0x'+runtime.hex(),returned_runtime_keccak256='0x'+keccak256(runtime).hex())
        rows.append(row)
    missing=[f'inputs.{key}' for key,v in value['inputs'].items() if v is None]+[f'planned_addresses.{key}' for key,v in value['planned_addresses'].items() if v is None]
    top_complete=all(row['constructor_payload_complete'] for row in rows if row['mode']=='top_level')
    result={'schema':1,'kind':'offline_deployment_preparation','profile':PROFILE,'build_profile':artifacts.profile,'offline_only':True,'ready_for_submission':False,'production_approved':False,
        'transaction_submitted':False,'rpc_performed':False,'simulation_performed':False,'address_predictions_performed':False,
        'status':'offline_inputs_and_top_level_payloads_complete_pending_live_verification' if top_complete and not missing else 'blocked_preview_missing_inputs',
        'input_sha256':sha(canonical(value)),'inputs':value,'accepted_build':{'profile':artifacts.profile,'directory':str(artifacts.directory.relative_to(artifacts.root)).replace('\\','/'),'files_sha256':artifacts.file_pins,'source_count':100,'production_sources':61,'normal_size_gates':48,'compiler_settings':artifacts.input['settings']},
        'limits':LIMITS,'counts':{'top_level':25,'internal_helpers':12,'inert_data_children':2,'total_instances':39},'instances':rows,
        'top_level_constructor_payloads_complete':top_complete,'all_instance_constructor_payloads_complete':all(row['constructor_payload_complete'] for row in rows),
        'input_assignments_complete':not missing,'binding_order_defined':True,'binding_addresses_verified':False,'construction_order':construction_order(),'missing_inputs':missing,
        'bootstrap_identity':'Actual Access constructor CREATE sender; not assumed to equal governance/keeper/guardian. Read actual bootstrap and canConfigure before binding.',
        'native_profile':{'chain_id':'4663','required_addresses':NATIVE,'live_runtime_and_getter_checks':'not_performed'},
        'factory_interleaving':'RoyaltyFactory.create and AssetsFactory.create are permissionless. No fixed factory nonce or child address is predicted. Read actual NFT/Registry/factory getters.',
        'qualification_evidence':{key:{'sha256':evidence,'status':'missing' if evidence is None else 'supplied_unverified','verified':False} for key,evidence in value['qualification_evidence'].items()},
        'release_prerequisites':['Reconcile actual deployed addresses, constructor returns, immutable values and actual runtime hashes.','Bind all16 module IDs with actual bootstrap; policy binding is separate.','Bind LP converter and SeaDrop helper before sealing; sealing alone does not validate either readiness.','Qualify ETH/fixedZZZ dual feeds, source independence and liveness, then configure fixedZZZ before execution sources/pools.','Add fixedZZZ to Rewards; bind identical ZZZ in Migration and Buyback; validate exact initialized native pools/routes.','Configure VRF funding/provider and SeaDrop upstream NFT-keyed settings; match NFT mintEnd to publicEnd.','RebalanceConfirmation starts with maxObservationGap0 (stopped); separately review configure(600,300,reviewHash), range/timing/keeper policy. No setting is adopted by this plan.','Qualify metadata content, operating services, full gas/fees and independent audit.'],
        'excluded_capabilities':['No deployer/nonce planning or CREATE predictions','No RPC, code discovery, provider qualification or signer','No seal calldata or administrative transaction payloads','No price-adapter creation or market/VRF/sale configuration manifests']}
    if value['inputs']['base_uri']=='':result['release_prerequisites'].append('Empty metadata URI is constructor-valid, but Access.seal rejects until bootstrap sets a nonempty NFT.setBaseURI root. Verify NFT.artworkBaseURI and reviewed content before sealing; this plan emits neither that setup call nor seal.')
    artifacts.check_sources();result['manifest_sha256']=sha(canonical(result));return result

def render(value):
    raw=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
    if len(raw)>MAX_OUTPUT:fail('output_size')
    return raw

def write_exclusive(path,raw):
    path=Path(path);temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.deployment-plan-',delete=False) as stream:
            temporary=Path(stream.name);stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.link(temporary,path)
        if hasattr(os,'O_DIRECTORY'):
            fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)

def main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self,message):fail('invalid_cli_arguments')
    parser=Parser(description=__doc__);parser.add_argument('--input',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--build-profile',default=DEFAULT_BUILD_PROFILE,help='Exact trusted build identifier; no automatic fallback.')
    stage='input';publishing=False
    try:
        args=parser.parse_args(argv)
        trusted_build(args.build_profile)
        if os.path.lexists(args.output):fail('existing_output_preserved')
        with args.input.open('rb') as stream:value=decode(stream.read(MAX_INPUT+1))
        stage='offline_preparation';result=prepare(value,build_profile=args.build_profile);stage='rendering';raw=render(result);stage='publication';publishing=True;write_exclusive(args.output,raw)
        print(json.dumps({'created':True,'status':result['status'],'build_profile':result['build_profile'],'ready_for_submission':False,'top_level_constructor_payloads_complete':result['top_level_constructor_payloads_complete']}))
        return 0 if result['top_level_constructor_payloads_complete'] and result['input_assignments_complete'] else 2
    except Exception as exc:
        reason=exc.code if type(exc) is PlanError else 'offline_preparation_unavailable'
        if publishing:reason='publication_uncertain'
        print(json.dumps({'created':False,'offline_only':True,'ready_for_submission':False,'transaction_submitted':False,'stage':stage,'reason':reason,'output_may_exist':publishing or reason=='existing_output_preserved'}),file=sys.stderr);return 1
