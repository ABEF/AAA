"""Bounded schema14 observer: constructor data pins are not deployment approval."""
from zzz_ops import production_observer_v11 as H,production_v12 as P
from zzz_ops import production_observer as O,production_observer_v6 as BASE
from zzz_ops import factory_code_v2 as F


class Observer(H.Observer):
    def typed(self,target,getter,expected):
        if getter in ('CODE_STORAGE_VERSION','creationCodeLength'):
            return O._decode(self.read(target,getter+'()')[0],0)
        if getter in ('part0','part1'):
            return O._decode(self.read(target,getter+'()')[0],O.ZERO)
        if getter in ('part0CodeHash','part1CodeHash'):
            return O._decode(self.read(target,getter+'()')[0],O.ZERO_HASH)
        return super().typed(target,getter,expected)

    def observe_chain_extension(self):
        section=F.parse_section(self.chain)
        section['observed_creation_code_length']=None;section['observed_creation_code_hash']=None
        raw=[]
        for row in section['parts']:
            for key in ('observed_data_length','observed_runtime_length','observed_runtime_hash','observed_prefix'):row[key]=None
            path='factory_code.parts['+str(row['index'])+']'
            raw.append(self.attempt(path,'factory.code.unavailable',lambda r=row:
                self.request('eth_getCode',[O._address(r['address']),self.block])))
        result=self.attempt('factory_code','factory.code.mismatch',lambda:F.verify_runtime_parts(raw))
        if result is not None:
            parts,whole=result
            for row,observed in zip(section['parts'],parts):row.update(observed)
            section.update(whole)


def observe(config,rpc):
    if not isinstance(config,dict) or type(config.get('schema_version')) is not int or config['schema_version']!=14:
        raise ValueError('Use explicit schema14/factory code-data version2')
    # Retain the previous profile restrictions as well as the new extension.
    chains=config.get('chains')
    if not isinstance(chains,list) or len(chains)!=1 or not isinstance(chains[0],dict):raise ValueError('Use one bounded current chain')
    chain=chains[0];F.parse_section(chain)
    if any(x in chain.get('helpers',{}) for x in ('royalty_converter','royalty_v4_executor')):raise ValueError('Royalty conversion is removed')
    for key in ('conversion_routes','activation_sources'):
        rows=chain.get(key)
        if not isinstance(rows,list) or len(rows)>64:raise ValueError('Unbounded current route inventory')
    if any(not isinstance(row,dict) or row.get('role')!='lp' for row in chain['conversion_routes']):raise ValueError('Royalty conversion routes are removed')
    if any(not isinstance(row,dict) or type(row.get('route_kind')) is not int or row['route_kind']!=0 or
        row.get('route_id')!=P.ZERO_HASH for row in chain['activation_sources']):raise ValueError('Direct Entry3 source routing must be zero')
    return BASE._observe(config,rpc,profile=P,observer_class=Observer)
