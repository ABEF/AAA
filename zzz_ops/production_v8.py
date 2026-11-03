"""Fresh schema10/custody5: only governance allocates/distributes terminal principal.
Historical schema9/custody4 remains explicitly separate, with permissionless batches.
Accounting6/Entry3/canonicalV6 and all entitlement/backing wires stay unchanged.
"""
from zzz_ops import production_v7 as H,production_v6 as BASE
V=H.V
ZERO_HASH=BASE.ZERO_HASH
SCHEMA_NAME,SCHEMA_HASH=H.SCHEMA_NAME,H.SCHEMA_HASH
MODULES,HELPERS=H.MODULES,H.HELPERS
TOP_FIELDS,CHAIN_FIELDS=H.TOP_FIELDS,H.CHAIN_FIELDS
VERSIONS=dict(H.VERSIONS,schema_version=10,custody_version=5)
SERVICE_PROFILES=dict(H.SERVICE_PROFILES,
    api=H.SERVICE_PROFILES['api'].replace('custody4','custody5'),
    keeper=H.SERVICE_PROFILES['keeper']+'_custody5_governance_principal')

def expected_bindings(chain):
    result=H.expected_bindings(chain)
    result['modules']['migration']['CUSTODY_VERSION']=5
    return result

def validate(config,*,expected_commit=None,now=None):
    return BASE._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,
        helpers=HELPERS,binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,
        route_validator=H.validate_routes)
