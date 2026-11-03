"""Read-only schema9/direct Entry3 observer; no signer, journal or pin adoption."""
from zzz_ops import production_observer_v6 as H
from zzz_ops import production_v7 as P


class Observer(H.Observer):
    def typed(self,target,getter,expected):
        if getter=='ENTRY_ROUTING_VERSION':
            return H.O._decode(self.read(target,'ENTRY_ROUTING_VERSION()')[0],0)
        return super().typed(target,getter,expected)


def observe(config,rpc):
    # Reject removed paths before RPC work; old schemas keep their own observer.
    if not isinstance(config,dict) or type(config.get('schema_version')) is not int or config['schema_version']!=9:
        raise ValueError('Use explicit schema9/direct Entry3')
    chains=config.get('chains')
    if not isinstance(chains,list) or len(chains)!=1 or not isinstance(chains[0],dict):
        raise ValueError('Use one bounded direct-Entry chain inventory')
    chain=chains[0]
    for key in ('conversion_routes','activation_sources'):
        if not isinstance(chain.get(key),list) or len(chain[key])>64:
            raise ValueError('Unbounded direct-Entry inventory')
    if any(not isinstance(row,dict) or row.get('role') not in ('lp','royalty') for row in chain['conversion_routes']):
        raise ValueError('Entry3 conversion routes are removed')
    if any(not isinstance(row,dict) or type(row.get('route_kind')) is not int or row.get('route_kind')!=0 or
            row.get('route_id')!=P.H.ZERO_HASH for row in chain['activation_sources']):
        raise ValueError('Entry3 source routing must be explicitly zero')
    return H._observe(config,rpc,profile=P,observer_class=Observer)
