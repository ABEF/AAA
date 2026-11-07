"""Bounded source-only accounting7/schema16 observer; no old journal adoption."""
from zzz_ops import production_observer_v13 as H,production_v14 as P
from zzz_ops import production_observer as O,production_observer_v6 as BASE


class Observer(H.Observer):
    def __init__(self,rpc,chain):
        super().__init__(rpc,chain);self.accounting_version=7

    def typed(self,target,getter,expected):
        if getter in ('LP_ALLOCATION_VERSION','MAX_ASSETS'):return O._decode(self.read(target,getter+'()')[0],0)
        if getter in ('canonicalModule','rewards'):return O._decode(self.read(target,getter+'()')[0],O.ZERO)
        if getter=='moduleAt3':return O._decode(self.read(target,'moduleAt(uint8)',3)[0],O.ZERO)
        return super().typed(target,getter,expected)

    def ledgers(self):
        for name,inventory,ledger,maximum in (
                ('reward_assets',self.chain['reward_assets'],self.chain['modules']['rewards']['address'],2),
                ('royalty_assets',self.chain['nft_inventory']['royalty_assets'],self.chain['helpers']['royalty_rewards']['address'],65)):
            entries=inventory.get('assets')
            if not isinstance(entries,list) or len(entries)>maximum:raise ValueError('Unbounded fresh ledger inventory')
            count=self.attempt(name,'ledger_assets.unavailable',lambda:int(self.read(ledger,'assetCount()')[0],16))
            inventory['observed_asset_count']=count
            if count!=len(entries) or count!=inventory.get('asset_count'):
                self.errors.append(dict(path=name,code='ledger_assets.mismatch'))
            for index,record in enumerate(entries):
                path=name+'.'+str(index)
                record['observed_asset']=self.attempt(path,'ledger_asset.unavailable',lambda i=index,l=ledger:
                    O._decode(self.read(l,'assets(uint256)',i)[0],O.ZERO))
                record['observed_is_asset']=self.attempt(path,'ledger_asset.unavailable',lambda r=record,l=ledger:
                    O._decode(self.read(l,'isAsset(address)',r['address'])[0],False))
                if record['observed_asset']!=record.get('address') or record['observed_is_asset'] is not True:
                    self.errors.append(dict(path=path,code='ledger_asset.mismatch'))
        ledger=self.chain['helpers']['royalty_rewards']['address']
        raw=self.attempt('royalty_assets.capacity','royalty.capacity.unavailable',lambda:self.read(ledger,'assetCapacity()'))
        self.chain['nft_inventory']['royalty_assets']['observed_capacity']=None if raw is None else int(raw[0],16)

    def observe_chain_extension(self):
        section=P.F.parse_section(self.chain);raw=[]
        section['observed_creation_code_length']=section['observed_creation_code_hash']=None
        for row in section['parts']:
            for field in ('observed_data_length','observed_runtime_length','observed_runtime_hash','observed_prefix'):row[field]=None
            raw.append(self.attempt('factory_code.parts.'+str(row['index']),'factory.code.unavailable',lambda r=row:
                self.request('eth_getCode',[O._address(r['address']),self.block])))
        observed=self.attempt('factory_code','factory.code.mismatch',lambda:P.F.verify_runtime_parts(raw))
        if observed is not None:
            parts,whole=observed
            for row,part in zip(section['parts'],parts):row.update(part)
            section.update(whole)


def observe(config,rpc):
    if not isinstance(config,dict) or any(type(config.get(k)) is not int or config[k]!=v for k,v in P.VERSIONS.items()):
        raise ValueError('Use explicit schema16/accounting7/exact LP1')
    chains=config.get('chains')
    if not isinstance(chains,list) or len(chains)!=1 or not isinstance(chains[0],dict):raise ValueError('Use one bounded current chain')
    chain=chains[0];P.precheck_chain(chain)
    if any(x in chain.get('helpers',{}) for x in ('royalty_converter','royalty_v4_executor')):raise ValueError('Royalty conversion remains removed')
    for key in ('conversion_routes','activation_sources'):
        rows=chain.get(key)
        if not isinstance(rows,list) or len(rows)>64:raise ValueError('Unbounded current route inventory')
    if any(not isinstance(row,dict) or row.get('role')!='lp' for row in chain['conversion_routes']):raise ValueError('Only LP conversion routes remain')
    if any(not isinstance(row,dict) or type(row.get('route_kind')) is not int or row.get('route_kind')!=0 or row.get('route_id')!=P.ZERO_HASH for row in chain['activation_sources']):raise ValueError('Direct Entry3 source routing must be zero')
    return BASE._observe(config,rpc,profile=P,observer_class=Observer)
