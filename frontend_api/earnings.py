"""Bounded confirmed earnings endpoint with an explicit event-semantics profile."""
from frontend_api.earnings_replay import Replay, SCALE, require
from frontend_api.earnings_prices import Prices, value_report
from frontend_api.history import HistoryError, ZERO, conversion_report
from zzz_ops.abi import address, keccak256
from zzz_ops.work_budget import checkpoint


class Earnings:
    def __init__(self, config, projection):
        from frontend_api.service import _keys, _hash, Contract
        _keys(config, {'schema', 'deployments', 'prices'}, 'earnings_history')
        if type(config['schema']) is not int or config['schema'] != 1 or projection.history is None:
            raise ValueError('Earnings requires schema 1 and complete configured history')
        self.p = projection
        peers = ([e.projection for e in projection.lineage.entries] if projection.lineage else []) + [projection]
        if not isinstance(config['deployments'], list) or len(config['deployments']) != len(peers):
            raise ValueError('Earnings profiles must cover the complete configured lineage')
        self.profiles = {}
        reserved = {c.address for p in peers for c in p.contracts.values()} | {a for p in peers for a in p.assets}
        for item, peer in zip(config['deployments'], peers):
            _keys(item, {'controller', 'fees', 'membership'}, 'earnings deployment')
            controller = address(item['controller'])
            if controller != peer.contracts['access'].address or controller in self.profiles:
                raise ValueError('Earnings profiles differ from reviewed predecessor order')
            extra = {}
            for role in ('fees', 'membership'):
                _keys(item[role], {'address', 'code_hash'}, 'earnings '+role)
                contract = Contract(address(item[role]['address']), _hash(item[role]['code_hash']))
                if contract.address in reserved:
                    raise ValueError('Earnings role address collision')
                reserved.add(contract.address); extra[role] = contract
            emitters = {peer.contracts[r].address for r in ('nft','rewards','royalties','vault','handoff')} | {c.address for c in extra.values()}
            if peer.history is None or not emitters <= set(peer.history.contracts):
                raise ValueError('Indexer must cover all seven earnings emitters from creation')
            self.profiles[controller] = extra
        self.descriptors = projection.lineage.descriptors if projection.lineage else projection.assets
        self.prices = None if config['prices'] is None else Prices(config['prices'], projection, self.descriptors)

    def check_profile(self, p, block):
        extra = self.profiles[p.contracts['access'].address]
        for role, label in (('fees', 'ZZZFeeController'), ('membership', 'ZZZMembership')):
            contract = extra[role]
            p._code(contract.address, contract.code_hash, block)
            from frontend_api.service import _address_word
            require(_address_word(p._call(contract.address, 'access()', block=block)[0]) == p.contracts['access'].address,
                    'Earnings module controller mismatch')
            require(p._addr('access','module(bytes32)','0x'+keccak256(label.encode()).hex(),block=block) == contract.address,
                    'Earnings module is not the sealed binding')
        for role in ('rewards','royalties'):
            require(p._uint(role,'SCALE()',block=block) == SCALE, 'Unsupported earnings index scale')
        return {**{r:p.contracts[r].address for r in ('nft','rewards','royalties','vault','handoff')},
                **{r:c.address for r,c in extra.items()}}

    def reconcile(self, p, model, block, lp_assets, royalty_assets, count):
        """On-chain denominators/indexes must match replay at every epoch cutoff."""
        require(len(model.minted) == count, 'Earnings mint count differs from chain')
        member = self.profiles[p.contracts['access'].address]['membership'].address
        require(int(p._call(member,'totalEligible()',block=block)[0],16) == len(model.members), 'Collective member history differs')
        require(p._uint('royalties','totalWeight()',block=block) == sum(model.weights.values()), 'Royalty weight history differs')
        require(p._uint('royalties','activationCount()',block=block) == len(model.weights), 'Royalty activation history differs')
        for bucket, supply in model.supply.items():
            require(p._uint('vault','bucketTotalShares(uint256)',bucket,block=block) == supply, 'LP share history differs')
            for asset in lp_assets:
                require(p._uint('rewards','ownerIndex(uint256,address)',bucket,asset,block=block) == model.owner_index[bucket,asset],
                        'Individual reward index history differs')
        for asset in lp_assets:
            require(p._uint('rewards','index(address)',asset,block=block) == model.collective_index[asset], 'Collective index history differs')
        for asset in royalty_assets:
            require(p._uint('royalties','index(address)',asset,block=block) == model.royalty_index[asset], 'Royalty index history differs')
            cohort = model.cohorts[asset]
            require(p._uint('royalties','eligibleCount(address)',asset,block=block) == len(cohort), 'Royalty cohort count differs')
            require(p._uint('royalties','eligibleWeight(address)',asset,block=block) == sum(model.weights[i] for i in cohort), 'Royalty cohort weight differs')
        if model.nft_id is not None and model.nft_id in model.minted:
            identifier=model.nft_id;bucket,shares=model.shares.get(identifier,(0,0))
            require(p._uint('vault','sharesOf(uint256)',identifier,block=block)==shares and
                    p._uint('vault','nftBucket(uint256)',identifier,block=block)==bucket, 'NFT share history differs')
            require(p._uint('royalties','weightOf(uint256)',identifier,block=block)==model.weights.get(identifier,0), 'NFT royalty weight differs')

    def read(self, identifier):
        p=self.p
        header,head,block=p._snapshot()
        life=p._verify_deployment(block)
        lp,royalties=p._admitted(block)
        history=p._history_snapshot(header,block,lp,royalties)
        owner=ordinal=None
        if identifier is not None:
            from frontend_api.service import UnknownNFT
            if identifier not in history.owners:
                raise UnknownNFT('NFT absent from complete canonical history')
            owner=p._addr('nft','ownerOf(uint256)',identifier,block=block)
            ordinal=p._uint('nft','mintOrdinalOf(uint256)',identifier,block=block)
            require(owner==history.owners[identifier] and ordinal>0 and
                    p._uint('nft','tokenAtOrdinal(uint256)',ordinal,block=block)==identifier, 'Earnings NFT identity differs')
        epochs=[]
        if p.lineage:
            financial=p.lineage.financial(p,header,block,life,history,identifier,ordinal,verified_epochs=epochs)
        else:
            require(life['predecessor_controller'] is None, 'Earnings requires complete predecessor history')
            epochs=[(p,header,None)]
            financial={'previously_claimed':p._claimed(history,identifier),
                       'royalty_conversions':conversion_report(history.conversions,identifier,p.assets,dict(history.provenance))}
        model=Replay(header['timestamp'],identifier)
        provenance=[]
        for peer,cutoff,lower in epochs:
            checkpoint()
            at={'blockHash':cutoff['hash'],'requireCanonical':True}
            emitters=self.check_profile(peer,at)
            a,b=peer._admitted(at)
            model.begin(emitters,a,b,lower)
            replayed=peer._history_snapshot(cutoff,at,a,b,consumer=model,extra_emitters=tuple(emitters.values()))
            model.finish()
            self.reconcile(peer,model,at,a,b,replayed.provenance['minted_count'])
            provenance.append({'controller':peer.contracts['access'].address,'history':dict(replayed.provenance),
                               'activation_cutoff':None if lower is None else {'block':lower[0],'transaction':lower[1]}})
        result=model.report(self.descriptors)
        if identifier is not None:
            self.check_paid(p,model,financial,block,lp,royalties)
        prices=(self.prices.read(block) if self.prices else {a:{'available':False,'usd_per_token_18':None,'reason':'price_not_configured'} for a in self.descriptors})
        value_report(result,self.descriptors,prices)
        result.update(schema=1,chain_id=p.chain,token_id=None if identifier is None else str(identifier),owner=owner,
            lifecycle=life,provenance={'block_number':header['number'],'block_hash':header['hash'],
            'block_timestamp':header['timestamp'],'observed_head':head,'confirmations':p.confirmations,
            'configuration_sha256':p.identity,'epochs':provenance,'finality':'confirmation_depth_only',
            'completeness':'Operator-maintained complete ingestion and pinned RPC; not a cryptographic log-completeness proof.'})
        for peer,cutoff,_ in epochs:
            require(p._header(hex(cutoff['number']))==cutoff,'Earnings epoch anchor changed during replay')
        p._finish(header)
        return result

    @staticmethod
    def check_paid(p,model,financial,block,lp,royalties):
        """Reconcile earned original currencies to current entitlement plus payouts."""
        claimed={a['asset']:a for a in financial['previously_claimed']['assets']}
        conversions={a['asset']:a for a in financial['royalty_conversions']['assets']}
        for asset in lp:
            earned=model.totals['lp_individual',asset]+model.totals['lp_collective',asset]
            paid=int(claimed[asset]['lp_raw'])
            require(earned-paid==p._uint('rewards','claimable(uint256,address)',model.nft_id,asset,block=block),
                    'LP earnings do not reconcile with actual claims and entitlement')
        for asset in royalties:
            paid=int(claimed[asset]['royalties_raw'])
            converted=int(conversions.get(asset,{}).get('source_converted_raw','0'))
            credited=int(financial['royalty_conversions']['total_eth_credited_raw']) if asset==ZERO else 0
            pending=p._uint('royalties','pending(address)',asset,block=block)
            cohort=model.cohorts[asset];weight=sum(model.weights[i] for i in cohort)
            delta=pending*SCALE//weight if weight else 0
            scaled=model.scaled['royalties',asset]
            extra=(scaled%SCALE+delta*model.weights[model.nft_id])//SCALE if model.nft_id in cohort else 0
            expected=model.totals['royalties',asset]-paid-converted+credited+extra
            require(expected==p._uint('royalties','claimable(uint256,address)',model.nft_id,asset,block=block),
                    'Royalty earnings do not reconcile with actual claims/conversions and entitlement')
