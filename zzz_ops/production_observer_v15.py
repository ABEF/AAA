"""Bounded schema17 read-only mint2/V10 observer; never adopts an old runtime.

All reads share the existing pinned canonical block and unchanged12000-read/
60-second whole-observation budget. Full1000-NFT operating capacity remains a
qualification item; exhaustion is an incomplete observation, never guessed data.
"""
from zzz_ops import production_observer_v14 as H,production_v15 as P
from zzz_ops import production_observer as O,production_observer_v6 as BASE


class Observer(H.Observer):
    def typed(self,target,getter,expected):
        if getter=='MINT_INTEGRATION_VERSION':return O._decode(self.read(target,getter+'()')[0],0)
        if getter in ('seaDropMint','seaDrop'):return O._decode(self.read(target,getter+'()')[0],O.ZERO)
        if getter=='seaDropCodeHash':return '0x'+self.read(target,getter+'()')[0]
        return super().typed(target,getter,expected)

    def _addresses(self,target,signature,*args,maximum=16):
        data='0x'+O.keccak256(signature.encode()).hex()[:8]+''.join(O._word(a) for a in args)
        values=O.decode_words(self.request('eth_call',[{'to':O._address(target),'data':data,
            'gas':hex(O.MAX_GETTER_GAS)},self.block]))
        if len(values)<2 or int(values[0],16)!=32 or int(values[1],16)>maximum or len(values)!=2+int(values[1],16):
            raise ValueError('Malformed or unbounded mint address list')
        result=[O._decode(w,O.ZERO) for w in values[2:]]
        if len(set(result))!=len(result) or O.ZERO in result:raise ValueError('Duplicate or zero mint address')
        return sorted(result)

    def primary_mint(self):
        section=self.chain['primary_mint']
        def capture():
            nft=self.chain['modules']['nft']['address'];vault=self.chain['modules']['vault']['address']
            helper=self.chain['helpers']['seadrop_mint']['address'];sd=O._address(section['sea_drop'])
            def uint(target,method,*args):return int(self.read(target,method,*args)[0],16)
            def addr(target,method,*args):return O._decode(self.read(target,method,*args)[0],O.ZERO)
            def digest(target,method):return '0x'+self.read(target,method)[0]
            raw=self.read(helper,'mintConfig()',count=15)
            widths=(16,16,16,16,8,48,48,48,48,48,48)
            values=[]
            for value,width in zip(raw,widths):
                number=int(value,16)
                if number>=1<<width:raise ValueError('Noncanonical mint configuration integer')
                values.append(number)
            values.extend((O._decode(raw[11],False),'0x'+raw[12],O._decode(raw[13],O.ZERO),'0x'+raw[14]))
            config=dict(zip(P.CONFIG_FIELDS,values))
            count=uint(helper,'totalMinted()')
            if not 0<=count<=1000:raise ValueError('Mint inventory exceeds1000')
            ordinals=[];recipients=set()
            for ordinal in range(1,count+1):
                identifier=uint(nft,'tokenAtOrdinal(uint256)',ordinal)
                recipient=addr(helper,'originalMintRecipient(uint256)',ordinal)
                ordinals.append(dict(ordinal=ordinal,reverse_ordinal=uint(nft,'mintOrdinalOf(uint256)',identifier),id=identifier,recipient=recipient,
                    stage=uint(helper,'mintStage(uint256)',ordinal),
                    nft_original_recipient=addr(nft,'originalMintRecipient(uint256)',identifier),
                    nft_stage=uint(nft,'mintStageOf(uint256)',identifier)))
                recipients.add(recipient)
            wallets=[]
            for recipient in sorted(recipients):
                stats=[int(w,16) for w in self.read(helper,'mintStats(address)',recipient,count=3)]
                if stats[1:]!=[count,1000]:raise ValueError('Lifetime mint stats disagree')
                wallets.append(dict(address=recipient,lifetime=stats[0],allowlist=uint(helper,'allowlistMinted(address)',recipient)))
            public=self.read(sd,'getPublicDrop(address)',nft,count=6)
            public_values=[]
            for value,width in zip(public,(80,48,48,16,16)):
                number=int(value,16)
                if number>=1<<width:raise ValueError('Noncanonical public drop integer')
                public_values.append(number)
            public_values.append(O._decode(public[5],False))
            public_drop=dict(zip(('mintPrice','startTime','endTime','maxTotalMintableByWallet','feeBps','restrictFeeRecipients'),public_values))
            royalties=self.chain['helpers']['royalty_rewards']['address']
            return dict(helper=helper,helper_version=uint(helper,'MINT_INTEGRATION_VERSION()'),sea_drop=addr(helper,'seaDrop()'),
                sea_drop_code_hash=digest(helper,'seaDropCodeHash()'),runtime_hash=self.code(sd),config=config,
                configured=O._decode(self.read(helper,'configured()')[0],False),minting=O._decode(self.read(helper,'minting()')[0],False),
                revision=uint(helper,'revision()'),configuration_hash=digest(helper,'configurationHash()'),
                configuration_values_hash=digest(helper,'configurationValuesHash()'),configuration_review_hash=digest(helper,'configurationReviewHash()'),
                reviewed_mint_price=uint(helper,'reviewedMintPrice()'),total_minted=count,nft_minted_count=uint(nft,'mintedCount()'),
                vault_sequence=uint(vault,'sequence()'),phase_minted=[uint(helper,'phaseMinted(uint8)',i) for i in (1,2,3)],
                current_phase=uint(helper,'currentPhase()'),ordinals=ordinals,wallets=wallets,public_drop=public_drop,
                creator_payout=addr(sd,'getCreatorPayoutAddress(address)',nft),allowlist_root='0x'+self.read(sd,'getAllowListMerkleRoot(address)',nft)[0],
                allowed_fee_recipients=self._addresses(sd,'getAllowedFeeRecipients(address)',nft),
                allowed_payers=self._addresses(sd,'getPayers(address)',nft),signer_count=len(self._addresses(sd,'getSigners(address)',nft)),
                token_gate_count=len(self._addresses(sd,'getTokenGatedAllowedTokens(address)',nft)),
                mint_end=uint(royalties,'mintEnd()'),mint_end_revision=uint(royalties,'mintEndRevision()'))
        section['observed']=self.attempt('primary_mint','mint.unavailable',capture)

    def confirmation(self):
        super().confirmation()
        self.primary_mint()


def observe(config,rpc):
    if not isinstance(config,dict) or any(type(config.get(k)) is not int or config[k]!=v for k,v in P.VERSIONS.items()):
        raise ValueError('Use explicit schema17/mint2/V10')
    chains=config.get('chains')
    if not isinstance(chains,list) or len(chains)!=1 or not isinstance(chains[0],dict):raise ValueError('Use one bounded current chain')
    chain=chains[0]
    if not isinstance(chain.get('primary_mint'),dict):raise ValueError('Missing explicit mint2 inventory')
    P.precheck_chain(chain)
    if any(x in chain.get('helpers',{}) for x in ('royalty_converter','royalty_v4_executor')):raise ValueError('Royalty conversion remains removed')
    for key in ('conversion_routes','activation_sources'):
        rows=chain.get(key)
        if not isinstance(rows,list) or len(rows)>64:raise ValueError('Unbounded current route inventory')
    if any(not isinstance(row,dict) or row.get('role')!='lp' for row in chain['conversion_routes']):raise ValueError('Only LP conversion routes remain')
    if any(not isinstance(row,dict) or type(row.get('route_kind')) is not int or row['route_kind']!=0 or row.get('route_id')!=P.ZERO_HASH for row in chain['activation_sources']):raise ValueError('Direct Entry3 source routing must be zero')
    return BASE._observe(config,rpc,profile=P,observer_class=Observer)
