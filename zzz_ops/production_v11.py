"""Schema13: exact-unit royalty4 with an explicit canonical V8 boundary."""
from zzz_ops import production_v10 as H, production_v6 as BASE
from zzz_ops.production_v9 import validate_routes
from zzz_ops.mint_policy_v2 import fingerprint as mint_fingerprint
V, ZERO_HASH = H.V, H.ZERO_HASH
from zzz_ops.abi import keccak256
SCHEMA_NAME = 'ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8'
SCHEMA_HASH = '0x'+keccak256(SCHEMA_NAME.encode()).hex()
# Exact normal compiler creation payload; update only with its source-bound build.
ROYALTY_CREATION_CODE_HASH = '0x4a520b4af1c8ded6fe2539ec7f3ec4f6d9a1c7fbdd710a53ccffd3412bfce831'
MODULES, HELPERS = H.MODULES, H.HELPERS
MAX_TOKEN_RECORDS = 97
raw_royalty_assets = H.raw_royalty_assets
VERSIONS = dict(H.VERSIONS, schema_version=13)
TOP_FIELDS, CHAIN_FIELDS = H.TOP_FIELDS, H.CHAIN_FIELDS
SERVICE_PROFILES = dict(H.SERVICE_PROFILES, api=H.SERVICE_PROFILES['api'].replace('royalty3_launch_window','royalty4_exact_units'))
def expected_bindings(chain):
    result=H.expected_bindings(chain)
    result['helpers']['royalty_rewards']['ROYALTY_SETTLEMENT_VERSION']=4
    result['helpers']['royalty_rewards']['ACTIVATION_WINDOW']=3600
    result['modules']['canonical']['SCHEMA']=SCHEMA_HASH
    result['helpers']['royalty_factory']['royaltyCodeHash']=ROYALTY_CREATION_CODE_HASH
    nft=chain.get('nft_inventory',{})
    result['helpers']['royalty_rewards']['assetCapacity']=nft.get('royalty_assets',{}).get('capacity')
    result['helpers']['royalty_rewards']['mintEnd']=nft.get('royalty_window',{}).get('mint_end')
    revision=nft.get('royalty_window',{}).get('mint_end_revision')
    result['helpers']['royalty_rewards']['mintEndRevision']=revision
    try:
        core=chain['protocol_policy']['mint']['fingerprint']
        combined=mint_fingerprint(core,chain['modules']['nft']['address'],
            chain['helpers']['royalty_rewards']['address'],
            nft.get('royalty_window',{}).get('mint_end'),revision)
    except (ValueError,TypeError,KeyError):
        combined=None
    result['modules']['vault']['mintPolicyFingerprint']=combined
    return result
def validate(config,*,expected_commit=None,now=None):
    return BASE._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,
        helpers=HELPERS,binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,
        route_validator=validate_routes,royalty_conversion=False,token_validator=validate_tokens,
        canonical_schema_name=SCHEMA_NAME,canonical_schema_hash=SCHEMA_HASH,royalty_max_assets=65,
        royalty_mint_revision=True)

def validate_tokens(g,chain,path,now,addresses):
    return V._tokens(g,chain,path,now,addresses,raw_royalty_assets=H.raw_royalty_assets(chain),maximum_tokens=MAX_TOKEN_RECORDS)
