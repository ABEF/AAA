"""Schema12: original-currency royalty3 with a sale-close activation window."""
from zzz_ops import production_v9 as H, production_v6 as BASE
V, ZERO_HASH = H.V, H.ZERO_HASH
from zzz_ops.abi import keccak256
SCHEMA_NAME = 'ZZZ_CANONICAL_SAME_CHAIN_ROYALTY_OPENING_V7'
SCHEMA_HASH = '0x'+keccak256(SCHEMA_NAME.encode()).hex()
MODULES, HELPERS = H.MODULES, H.HELPERS
raw_royalty_assets = H.raw_royalty_assets
VERSIONS = dict(H.VERSIONS, schema_version=12)
TOP_FIELDS, CHAIN_FIELDS = H.TOP_FIELDS, H.CHAIN_FIELDS
SERVICE_PROFILES = dict(H.SERVICE_PROFILES, api=H.SERVICE_PROFILES['api'].replace('royalty2_original_currency','royalty3_launch_window'))
def expected_bindings(chain):
    result=H.expected_bindings(chain)
    result['helpers']['royalty_rewards']['ROYALTY_SETTLEMENT_VERSION']=3
    result['helpers']['royalty_rewards']['ACTIVATION_WINDOW']=3600
    result['modules']['canonical']['SCHEMA']=SCHEMA_HASH
    nft=chain.get('nft_inventory',{})
    result['helpers']['royalty_rewards']['assetCapacity']=nft.get('royalty_assets',{}).get('capacity')
    result['helpers']['royalty_rewards']['mintEnd']=nft.get('royalty_window',{}).get('mint_end')
    return result
def validate(config,*,expected_commit=None,now=None):
    return BASE._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,
        helpers=HELPERS,binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,
        route_validator=H.validate_routes,royalty_conversion=False,token_validator=validate_tokens,
        canonical_schema_name=SCHEMA_NAME,canonical_schema_hash=SCHEMA_HASH,royalty_max_assets=65)

def validate_tokens(g,chain,path,now,addresses):
    return V._tokens(g,chain,path,now,addresses,raw_royalty_assets=H.raw_royalty_assets(chain),maximum_tokens=97)
