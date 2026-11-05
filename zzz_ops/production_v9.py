"""Schema11: original-currency royalty2; old inventories remain inspection-only."""
from zzz_ops import production_v8 as H, production_v6 as BASE
V=H.V
ZERO_HASH=H.ZERO_HASH
SCHEMA_NAME,SCHEMA_HASH=H.SCHEMA_NAME,H.SCHEMA_HASH
MODULES=H.MODULES
HELPERS=tuple(x for x in H.HELPERS if x not in ('royalty_converter','royalty_v4_executor'))
VERSIONS=dict(H.VERSIONS,schema_version=11)
TOP_FIELDS,CHAIN_FIELDS=H.TOP_FIELDS,H.CHAIN_FIELDS
SERVICE_PROFILES=dict(H.SERVICE_PROFILES,
    api=H.SERVICE_PROFILES['api']+'_royalty2_original_currency',
    keeper=H.SERVICE_PROFILES['keeper']+'_no_royalty_swaps')

def expected_bindings(chain):
    result=H.expected_bindings(chain)
    for role in ('royalty_converter','royalty_v4_executor'):del result['helpers'][role]
    ledger=result['helpers']['royalty_rewards']
    del ledger['converter']
    ledger.update(ROYALTY_SETTLEMENT_VERSION=2,ROYALTY_RECOVERY_VERSION=2)
    return result

def validate_routes(g,chain,path,tokens,deps,pools,limits):
    for i,row in enumerate(g.items(chain.get('conversion_routes'),path+'.conversion_routes',64)):
        g.check(isinstance(row,dict) and row.get('role')=='lp',f'{path}.conversion_routes[{i}]',
                'route.royalty_removed','Only LP reward conversion remains; royalties keep their source currency.','routes')
    H.H.validate_routes(g,chain,path,tokens,deps,pools,limits)

def validate(config,*,expected_commit=None,now=None):
    return BASE._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,
        helpers=HELPERS,binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,
        route_validator=validate_routes,royalty_conversion=False,token_validator=validate_tokens)

def raw_royalty_assets(chain):
    """Only explicit royalty-only currencies may lack a USD valuation policy."""
    def rows(value):return value if isinstance(value,list) and len(value)<=256 else []
    nft=V._obj(chain.get('nft_inventory'))
    raw={x.get('address') for x in rows(V._obj(nft.get('royalty_assets')).get('assets'))
         if isinstance(x,dict) and x.get('strategy')=='claim_original' and isinstance(x.get('address'),str)}
    financial={V.ZERO,V.NATIVE_DEPENDENCIES['zzz'][0],V._obj(V._obj(chain.get('dependencies')).get('zzz')).get('address')}
    for x in rows(V._obj(chain.get('reward_assets')).get('assets')):
        if isinstance(x,dict):financial.add(x.get('address'))
    for key in ('activation_sources','conversion_routes'):
        for x in rows(chain.get(key)):
            if isinstance(x,dict):
                for field in ('asset','source_asset','valuation_asset'):financial.add(x.get(field))
    for x in rows(chain.get('pools')):
        if isinstance(x,dict):financial.update((x.get('currency0'),x.get('currency1')))
    return raw-financial

def validate_tokens(g,chain,path,now,addresses):
    return V._tokens(g,chain,path,now,addresses,raw_royalty_assets=raw_royalty_assets(chain))
