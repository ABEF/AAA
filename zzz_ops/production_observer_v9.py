"""Schema11 readonly observer: no royalty converter, signer or pin adoption."""
from zzz_ops import production_observer_v6 as H,production_v9 as P

class Observer(H.Observer):
    converter_roles=('lp_converter',)
    def __init__(self,rpc,chain):
        super().__init__(rpc,chain)
        self.raw_royalty_assets=P.raw_royalty_assets(chain)
    def typed(self,target,getter,expected):
        if getter in ('ENTRY_ROUTING_VERSION','ROYALTY_SETTLEMENT_VERSION','ROYALTY_RECOVERY_VERSION'):
            return H.O._decode(self.read(target,getter+'()')[0],0)
        return super().typed(target,getter,expected)

def observe(config,rpc):
    if not isinstance(config,dict) or type(config.get('schema_version')) is not int or config['schema_version']!=11:
        raise ValueError('Use explicit schema11/original-currency royalty2')
    chains=config.get('chains')
    if not isinstance(chains,list) or len(chains)!=1 or not isinstance(chains[0],dict):
        raise ValueError('Use one bounded current chain inventory')
    c=chains[0]
    if any(x in c.get('helpers',{}) for x in ('royalty_converter','royalty_v4_executor')):
        raise ValueError('Original-currency royalty profile has no converter')
    for key in ('conversion_routes','activation_sources'):
        if not isinstance(c.get(key),list) or len(c[key])>64:raise ValueError('Unbounded current route inventory')
    if any(not isinstance(row,dict) or row.get('role')!='lp' for row in c['conversion_routes']):
        raise ValueError('Royalty conversion routes are removed')
    if any(not isinstance(row,dict) or type(row.get('route_kind')) is not int or row['route_kind']!=0 or
           row.get('route_id')!=P.ZERO_HASH for row in c['activation_sources']):
        raise ValueError('Direct Entry3 source routing must be zero')
    return H._observe(config,rpc,profile=P,observer_class=Observer)
