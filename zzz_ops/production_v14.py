"""Schema16/accounting7/exact LP1; historical15/6/V8 remains separate."""
from zzz_ops import production_v13 as H,production_v11 as LEGACY,production_v6 as BASE
from zzz_ops import factory_code_v3 as F

V,ZERO_HASH=H.V,H.ZERO_HASH
MODULES,HELPERS=H.MODULES,H.HELPERS+('rewards_canonical',)
SCHEMA_NAME='ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9'
SCHEMA_HASH='0x'+V.keccak256(SCHEMA_NAME.encode()).hex()
VERSIONS=dict(H.VERSIONS,schema_version=16,accounting_version=7,lp_allocation_version=1)
TOP_FIELDS=H.TOP_FIELDS|{'lp_allocation_version'}
CHAIN_FIELDS=H.CHAIN_FIELDS
MAX_TOKEN_RECORDS=66
SERVICE_PROFILES={k:v.replace('accounting6','accounting7_lp1').replace('holder_exit_v6','holder_exit_v9') for k,v in H.SERVICE_PROFILES.items()}
ROYALTY_CREATION_CODE_HASH=F.SPEC.creation_hash
raw_royalty_assets=H.raw_royalty_assets


def precheck_chain(chain):F.parse_section(chain)


def expected_bindings(chain):
    result=LEGACY.expected_bindings(chain)
    for group,role in H.REINVEST_ROLES:result[group][role]['RESIDUAL_REINVEST_VERSION']=1
    for group,role in H.RESIDUAL_EXIT_ROLES:result[group][role]['RESIDUAL_EXIT_VERSION']=1
    result['modules']['vault']['ACCOUNTING_VERSION']=7
    result['modules']['canonical']['SCHEMA']=SCHEMA_HASH
    result['modules']['rewards'].update(LP_ALLOCATION_VERSION=1,MAX_ASSETS=2)
    child=chain['helpers']['rewards_canonical']['address']
    result['modules']['rewards']['canonicalModule']=child
    result['modules']['canonical']['moduleAt3']=child
    result['helpers']['rewards_canonical']=dict(access=chain['modules']['access']['address'],rewards=chain['modules']['rewards']['address'])
    parts=F.parse_section(chain)['parts']
    result['helpers']['royalty_factory'].update(CODE_STORAGE_VERSION=2,royaltyCodeHash=F.SPEC.creation_hash,
        creationCodeLength=F.SPEC.creation_length,part0=parts[0]['address'],part1=parts[1]['address'],
        part0CodeHash=F.SPEC.parts[0].runtime_hash,part1CodeHash=F.SPEC.parts[1].runtime_hash)
    return result


def factory_code(g,chain,path,addresses):
    # Same immutable code-storage FORMAT2, new source-owned payload identity.
    section=F.parse_section(chain);base=path+'.factory_code';children=[]
    for row,spec in zip(section['parts'],F.SPEC.parts):
        rp=base+'.parts['+str(spec.index)+']';address=g.hex(row['address'],rp+'.address',20)
        if address is not None:children.append(address)
        for field,wanted in (('observed_data_length',spec.data_length),('observed_runtime_length',spec.runtime_length)):
            g.check(type(row[field]) is int and row[field]==wanted,rp+'.'+field,'factory.code.length','Verify independently source-bound child lengths.','bindings')
        g.check(row['observed_runtime_hash']==spec.runtime_hash and row['observed_prefix']=='0x5f5ffd',rp,
            'factory.code.runtime','Verify exact immutable data-child bytes.','bindings')
    g.check(len(children)==2 and len(set(addresses+children))==len(addresses)+2,base,'factory.code.alias','Keep both inert data children distinct.','bindings')
    g.check(type(section['observed_creation_code_length']) is int and section['observed_creation_code_length']==F.SPEC.creation_length and
        section['observed_creation_code_hash']==F.SPEC.creation_hash,base,'factory.code.payload','Reconstruct and match the whole source-owned payload.','bindings')
    V._bound_proof(g,section['review_evidence'],base+'.review_evidence',chain,kind='factory_code_storage_qualification',exact_block=True)
    assets=V._obj(chain.get('reward_assets'))
    rows=assets.get('assets')
    zzz=V._obj(V._obj(chain.get('helpers')).get('activation_assets')).get('bindings',{}).get('zzz')
    g.check(assets.get('asset_count')==2 and assets.get('observed_asset_count')==2 and isinstance(rows,list) and len(rows)==2 and
        [r.get('address') for r in rows if isinstance(r,dict)]==[BASE.ZERO,zzz],
        path+'.reward_assets','lp.assets.fixed','Exact LP funding admits native ETH and fixed ZZZ only.','bindings')
    return children


def validate_tokens(g,chain,path,now,addresses):
    return V._tokens(g,chain,path,now,addresses,raw_royalty_assets=raw_royalty_assets(chain),maximum_tokens=MAX_TOKEN_RECORDS)


def validate(config,*,expected_commit=None,now=None):
    return BASE._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,helpers=HELPERS,
        binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,route_validator=LEGACY.validate_routes,
        royalty_conversion=False,token_validator=validate_tokens,canonical_schema_name=SCHEMA_NAME,canonical_schema_hash=SCHEMA_HASH,
        royalty_max_assets=65,royalty_mint_revision=True,chain_fields=CHAIN_FIELDS,chain_validator=factory_code,top_fields=TOP_FIELDS)
