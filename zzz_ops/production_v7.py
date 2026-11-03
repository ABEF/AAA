"""Fresh schema9: direct Entry3 over accounting6; never deployment approval.

Schema8 keeps its routed Entry2 profile. No incoming manifest is rewritten to an
older schema to pass. Reward and royalty conversion retain their own children.
"""
from zzz_ops import production_v6 as H

V=H.V
SCHEMA_NAME,SCHEMA_HASH=H.SCHEMA_NAME,H.SCHEMA_HASH
MODULES=H.MODULES
HELPERS=tuple(role for role in H.HELPERS if role!='entry_v4_executor')
VERSIONS=dict(H.VERSIONS,schema_version=9,routing_version=3)
TOP_FIELDS,CHAIN_FIELDS=H.TOP_FIELDS,H.CHAIN_FIELDS
SERVICE_PROFILES=dict(H.SERVICE_PROFILES,api=H.SERVICE_PROFILES['api']+'_entry3')


def expected_bindings(chain):
    result=H.expected_bindings(chain)
    del result['helpers']['entry_v4_executor']
    entry=result['helpers']['activation_entry']
    del entry['v4Executor']
    entry['ENTRY_ROUTING_VERSION']=3
    return result


def validate_routes(g,chain,path,tokens,deps,pools,limits):
    for i,row in enumerate(g.items(chain.get('conversion_routes'),path+'.conversion_routes',64)):
        g.check(isinstance(row,dict) and row.get('role') in ('lp','royalty'),
            f'{path}.conversion_routes[{i}]','route.entry_removed',
            'Entry3 has no conversion routes. Only separate LP/royalty converters remain.','routes')
    for i,row in enumerate(g.items(chain.get('activation_sources'),path+'.activation_sources',64,2)):
        g.check(isinstance(row,dict) and type(row.get('route_kind')) is int and
            row.get('route_kind')==0 and row.get('route_id')==H.ZERO_HASH,
            f'{path}.activation_sources[{i}]','source.direct_only',
            'Direct Entry3 sources have explicit zero routing; no pre-Vault conversion.','routes')
    V._routes(g,chain,path,tokens,deps,pools,limits,1)


def validate(config,*,expected_commit=None,now=None):
    return H._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,
        helpers=HELPERS,binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,
        route_validator=validate_routes)
