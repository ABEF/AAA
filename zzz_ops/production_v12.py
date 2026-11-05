"""Schema14: exact-unit royalty4 with two source-bound inert code children."""
from zzz_ops import production_v11 as H,production_v6 as BASE
from zzz_ops import factory_code_v2 as F
V,ZERO_HASH=H.V,H.ZERO_HASH
MODULES,HELPERS=H.MODULES,H.HELPERS
SCHEMA_NAME,SCHEMA_HASH=H.SCHEMA_NAME,H.SCHEMA_HASH
VERSIONS=dict(H.VERSIONS,schema_version=14)
TOP_FIELDS=H.TOP_FIELDS
CHAIN_FIELDS=H.CHAIN_FIELDS|{'factory_code'}
SERVICE_PROFILES=H.SERVICE_PROFILES
MAX_TOKEN_RECORDS=H.MAX_TOKEN_RECORDS
ROYALTY_CREATION_CODE_HASH=F.SPEC.creation_hash
raw_royalty_assets=H.raw_royalty_assets


def precheck_chain(chain):F.parse_section(chain)


def expected_bindings(chain):
    result=H.expected_bindings(chain)
    parts=F.parse_section(chain)['parts']
    result['helpers']['royalty_factory'].update(CODE_STORAGE_VERSION=2,
        creationCodeLength=F.SPEC.creation_length,part0=parts[0]['address'],part1=parts[1]['address'],
        part0CodeHash=F.SPEC.parts[0].runtime_hash,part1CodeHash=F.SPEC.parts[1].runtime_hash)
    return result


def factory_code(g,chain,path,addresses):
    section=F.parse_section(chain);base=path+'.factory_code';children=[]
    for row,spec in zip(section['parts'],F.SPEC.parts):
        rp=base+'.parts['+str(spec.index)+']'
        address=g.hex(row['address'],rp+'.address',20)
        if address is not None:children.append(address)
        for field,wanted in [('observed_data_length',spec.data_length),('observed_runtime_length',spec.runtime_length)]:
            g.check(type(row[field]) is int and row[field]==wanted,rp+'.'+field,'factory.code.length',
                'Verify exact independently derived child length at the same pinned block.','bindings')
        g.check(row['observed_runtime_hash']==spec.runtime_hash and row['observed_prefix']=='0x5f5ffd',rp,
            'factory.code.runtime','Verify exact source-bound revert-prefixed inert bytes.','bindings')
    g.check(len(children)==2 and len(set(addresses+children))==len(addresses)+2,base,'factory.code.alias',
        'Use exactly two distinct inert children, separate from every protocol module/helper.','bindings')
    g.check(type(section['observed_creation_code_length']) is int and section['observed_creation_code_length']==F.SPEC.creation_length and
        section['observed_creation_code_hash']==F.SPEC.creation_hash,base,'factory.code.payload',
        'Reconstruct both ordered children and verify the source-owned complete creation payload.','bindings')
    V._bound_proof(g,section['review_evidence'],base+'.review_evidence',chain,kind='factory_code_storage_qualification',exact_block=True)
    return children


def validate(config,*,expected_commit=None,now=None):
    return BASE._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,
        helpers=HELPERS,binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,
        route_validator=H.validate_routes,royalty_conversion=False,token_validator=H.validate_tokens,
        canonical_schema_name=SCHEMA_NAME,canonical_schema_hash=SCHEMA_HASH,royalty_max_assets=65,
        royalty_mint_revision=True,chain_fields=CHAIN_FIELDS,chain_validator=factory_code)
