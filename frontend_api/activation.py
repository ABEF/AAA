"""Prepare exact owner-funded activation/top-up calls; never sign or broadcast."""
from __future__ import annotations

import re

from frontend_api.activation_config import ActivationConfig, ZERO_HASH
from frontend_api.activation_trace import measure, request_data
from frontend_api.liquidity_context import contribution_context
from frontend_api.service import ProjectionError, UnknownNFT, ZERO, _address_word, _bool, _hash, _keys, _quantity, token_id
from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.work_budget import bounded_request, expire_at

GAS_CAP = 12_000_000
SNAPSHOT_AGE = 120
DRAFT_SECONDS = 60


class ActivationInputError(ValueError):
    """Invalid typed owner request; raw request data is never echoed."""


def parse(payload):
    try:
        _keys(payload, {'action','wallet','token_id','pool_id','source_asset','amount_in','slippage_bps'}, 'activation request')
        if payload['action'] not in ('activate','increase'):
            raise ValueError('Unsupported activation action')
        if not isinstance(payload['token_id'],str) or not isinstance(payload['amount_in'],str):
            raise ValueError('IDs and raw amounts must be decimal strings')
        identifier = token_id(payload['token_id'])
        if not re.fullmatch(r'[1-9][0-9]{0,77}', payload['amount_in']) or int(payload['amount_in']) >= 2**128:
            raise ValueError('Contribution amount exceeds supported bounds')
        if type(payload['slippage_bps']) is not int or not 0 <= payload['slippage_bps'] <= 100:
            raise ValueError('Slippage must be 0..100 basis points')
        return {'id':identifier,'owner':address(payload['wallet']),'pool':_hash(payload['pool_id']),
                'source':ZERO if payload['source_asset']==ZERO else address(payload['source_asset']),
                'amount':int(payload['amount_in']),'increase':payload['action']=='increase',
                'slippage':payload['slippage_bps']}
    except (ValueError,TypeError,KeyError) as exc:
        raise ActivationInputError('Invalid typed activation request') from exc


class ActivationTransactions:
    def __init__(self, projection, config):
        self.p = projection
        self.config = ActivationConfig(config, projection)

    def _fresh(self, header):
        now = int(self.p.clock())
        if header['timestamp'] > now + 30 or now - header['timestamp'] > SNAPSHOT_AGE:
            raise ProjectionError('Activation snapshot is stale or in the future')
        return now

    def _gas(self, tx, block):
        # Only networks whose complete fee accounting was explicitly reviewed
        # may use this adapter. Trace gas alone is never a total network fee.
        estimate = _quantity(self.p.rpc.call('eth_estimateGas', [{**tx,'gas':hex(GAS_CAP)},block]))
        price = _quantity(self.p.rpc.call('eth_gasPrice', []))
        if not 21000 <= estimate <= GAS_CAP or not 0 < price <= self.config.max_gas_price:
            raise ProjectionError('Gas estimate or price exceeds the reviewed bound')
        limit = min(GAS_CAP, (estimate * 120 + 99)//100)
        balance = _quantity(self.p.rpc.call('eth_getBalance',[tx['from'],block]))
        if balance < int(tx['value'],16) + limit * price:
            raise ActivationInputError('Wallet lacks native currency for contribution and separate estimated gas')
        return {'estimated_units':str(estimate),'suggested_limit':str(limit),'price_wei':str(price),
                'estimated_fee_wei':str(estimate*price),'suggested_limit_cost_wei':str(limit*price),
                'currency':'native','included_in_execution_loss':False,'includes_all_network_components':True,
                'fee_policy_review_hash':self.config.fee_review,'price_source':'eth_gasPrice at preparation time',
                'wallet_must_refresh':True}

    def _route(self, req, source, pins, block):
        p=self.p; cfg=self.config
        route,policy_id=cfg.sources[(req['pool'],req['source'])]
        req['route']=route
        if '0x'+p._call(pins['activation_assets'],'activePolicy(address)',source,block=block)[0] != policy_id:
            raise ProjectionError('Active source policy differs from the reviewed policy')
        policy=p._call(pins['activation_assets'],'policies(bytes32)',policy_id,block=block,words=6)
        if (_address_word(policy[0])!=source or not _bool(policy[1]) or '0x'+policy[2]!=cfg.tokens[source]['code_hash'] or
                int(policy[3],16)==0 or int(policy[4],16)!=cfg.tokens[source]['decimals']):
            raise ProjectionError('Source asset is disabled or its admission changed')
        _bool(policy[5])
        if route==ZERO_HASH:
            if source not in (req['token0'],req['token1']):
                raise ActivationInputError('Source has no reviewed conversion route')
            return source
        entry=pins['entry']
        for getter in ('routeExists(bytes32)','routeEnabled(bytes32)'):
            if not _bool(p._call(entry,getter,route,block=block)[0]):
                raise ProjectionError('Reviewed route is absent or disabled')
        data=p._call(entry,'route(bytes32)',route,block=block,words=12)
        if '0x'+keccak256(bytes.fromhex(''.join(data))).hex()!=route:
            raise ProjectionError('Append-only route contents differ from their reviewed identity')
        src,out,router,factory,pool=map(_address_word,data[:5]);fee=int(data[5],16)
        if src!=source or out not in (req['token0'],req['token1']) or out==source or fee>=1_000_000 or int(data[11],16)==0:
            raise ProjectionError('Conversion route differs from the selected pair/source')
        for target,word in zip((router,factory,pool,source,out),data[6:11]):
            expected=cfg.tokens[target]['code_hash'] if target in cfg.tokens else cfg.dependencies.get(target)
            if expected is None or expected!='0x'+word:
                raise ProjectionError('Unreviewed conversion dependency')
            p._code(target,expected,block)
        expected_bindings=[(router,'factory()',(),factory),(factory,'getPool(address,address,uint24)',(source,out,fee),pool),
                           (pool,'factory()',(),factory),(pool,'token0()',(),min(source,out)),(pool,'token1()',(),max(source,out))]
        for target,method,args,want in expected_bindings:
            if _address_word(p._call(target,method,*args,block=block)[0])!=want:
                raise ProjectionError('Conversion venue identity changed')
        if int(p._call(pool,'fee()',block=block)[0],16)!=fee or int(p._call(pool,'liquidity()',block=block)[0],16)==0:
            raise ProjectionError('Conversion pool is mismatched or unfunded')
        return out

    def _trace(self, tx, pins, req, gross, max_slippage, block):
        raw=self.p.rpc.call('debug_traceCall',[{**tx,'gas':hex(GAS_CAP)},block,
            {'tracer':'callTracer','timeout':'5s','tracerConfig':{'withLog':True}}])
        return measure(raw,{**tx,'gas':hex(GAS_CAP)},pins,req,gross,max_slippage)

    @bounded_request
    def prepare(self, payload):
        req=parse(payload); p=self.p; cfg=self.config
        if (req['pool'],req['source']) not in cfg.sources:
            raise ActivationInputError('No explicitly reviewed route for this source and pool')
        header,head,block=p._snapshot(); now=self._fresh(header)
        expire_at(min(now+DRAFT_SECONDS,header['timestamp']+SNAPSHOT_AGE),p.clock)
        life=p._verify_deployment(block)
        if life['paused'] or life['preparation_active']:
            raise ActivationInputError('New contributions are paused or canonical preparation is active')
        ordinal=p._uint('nft','mintOrdinalOf(uint256)',req['id'],block=block)
        if ordinal==0: raise UnknownNFT('NFT has no canonical mint ordinal')
        if ordinal>1000 or p._uint('nft','tokenAtOrdinal(uint256)',ordinal,block=block)!=req['id']:
            raise ProjectionError('NFT identity does not match its canonical ordinal')
        if p._addr('nft','ownerOf(uint256)',req['id'],block=block)!=req['owner']:
            raise ActivationInputError('Only the current NFT owner can contribute')
        if not _bool(p._call(p.contracts['nft'].address,'traitsReady(uint256)',req['id'],block=block)[0]):
            raise ActivationInputError('NFT reveal must finish before activation')
        status=p._uint('vault','nftStatus(uint256)',req['id'],block=block)
        if status!=(1 if req['increase'] else 5):
            raise ActivationInputError('Selected action does not match the NFT custody state')
        registry=cfg.contracts['pools'];p._code(registry.address,registry.code_hash,block)
        actual=p._call(registry.address,'get(bytes32)',req['pool'],block=block,words=14)
        account=p._call(registry.address,'accounting(bytes32)',req['pool'],block=block,words=14)
        if ('0x'+keccak256(bytes.fromhex(''.join(actual[:5]))).hex()!=req['pool'] or actual[1:]!=account[1:] or
                not _bool(account[5]) or not _bool(account[6])):
            raise ProjectionError('Pool identity/configuration is invalid or contributions are disabled')
        req['token0'],req['token1']=map(_address_word,account[:2])
        if req['token0']==req['token1']: raise ProjectionError('Invalid accounting pair')
        source=req['token0'] if req['source']==ZERO else req['source']
        if req['source']==ZERO and (int(actual[0],16)!=0 or _address_word(p._call(registry.address,'nativeAsset(bytes32)',req['pool'],block=block)[0])!=source):
            raise ActivationInputError('Native input is unsupported for this pool')
        if req['source']!=ZERO and actual[0]!=account[0] and int(actual[0],16)!=0:
            raise ProjectionError('Unexpected accounting token substitution')
        pins,prices=cfg.verify(p,block,(source,req['token0'],req['token1']))
        req['output']=self._route(req,source,pins,block)
        gross=req['amount']*prices[source]//10**cfg.tokens[source]['decimals']
        measured=int(p._call(pins['activation_assets'],'value(address,uint256)',source,req['amount'],block=block)[0],16)
        if measured!=gross: raise ProjectionError('Original-source valuation mismatch')
        contributed=p._uint('vault','contributionUSD(uint256)',req['id'],block=block)
        if gross<int(account[12],16) or not req['increase'] and gross<100*10**18 or contributed+gross>int(account[13],16):
            raise ActivationInputError('Contribution is outside the original-source value limits')
        bucket=p._uint('vault','poolBucket(bytes32)',req['pool'],block=block)
        if req['increase'] and p._uint('vault','nftBucket(uint256)',req['id'],block=block)!=bucket:
            raise ActivationInputError('Top-up must use the NFT existing pool')
        req['old_lp_id']=0
        position=None
        if bucket:
            position=p._call(pins['vault'],'group(uint256)',bucket,block=block,words=15)
            if int(position[7],16) not in (0,1): raise ActivationInputError('Shared custody is unavailable for contributions')
            req['old_lp_id']=int(position[1],16)
            if int(position[7],16)==1 and '0x'+position[0]!=req['pool']:
                raise ActivationInputError('Pool alias is not the current custody pool')
        else:
            if req['increase']: raise ProjectionError('Active NFT has no shared bucket')
            bucket=int(p._call(pins['vault_canonical'],'bucketIdentity(bytes32)',req['pool'],block=block)[0],16)
        req['bucket']=bucket
        liquidity_context=contribution_context(p,pins,req['pool'],bucket,position,account,header,block)
        current=p._call(pins['nft'],'currentLPValue(uint256)',req['id'],block=block,words=2)
        available=_bool(current[0]);current_value=int(current[1],16)
        if not available and current_value: raise ProjectionError('Unavailable current NFT valuation contains a value')
        current_value={'available':available,'usd_18':str(current_value) if available else None,
                       'source':'NFT.currentLPValue','includes_attributed_idle_and_compound':True}
        req['deadline']=min(now+DRAFT_SECONDS,header['timestamp']+min(p.max_age,SNAPSHOT_AGE))
        if req['deadline']<=max(now,header['timestamp']): raise ProjectionError('Snapshot expires before preparation')
        approvals=[];gas=None;result=None;transaction=None;kind='activation_transaction'
        if req['source']!=ZERO:
            balance=int(p._call(source,'balanceOf(address)',req['owner'],block=block)[0],16)
            if balance<req['amount']: raise ActivationInputError('Source balance is insufficient')
            allowance=int(p._call(source,'allowance(address,address)',req['owner'],pins['entry'],block=block)[0],16)
            if allowance<req['amount']:
                # Reset a nonzero allowance first; never silently grant unlimited
                # approval or fake approval state to claim activation is ready.
                approval_amount=0 if allowance else req['amount']
                transaction={'from':req['owner'],'to':source,'value':'0x0',
                             'data':calldata('approve(address,uint256)',pins['entry'],approval_amount)}
                response=p.rpc.call('eth_call',[{**transaction,'gas':hex(GAS_CAP)},block])
                if response not in ('0x','0x'+f'{1:064x}'): raise ProjectionError('Approval simulation failed')
                kind='approval_required'
                approvals=[{'asset':source,'spender':pins['entry'],'amount_raw':str(approval_amount),
                            'reset_first':allowance!=0,'reprepare_after_confirmation':True}]
        if transaction is None:
            req['minimum_out']=0 if req['route']==ZERO_HASH else 1;req['minimum_lp']=1
            def tx():
                return {'from':req['owner'],'to':pins['entry'],'value':hex(req['amount'] if req['source']==ZERO else 0),
                        'data':request_data(req['id'],req['pool'],req['source'],req['amount'],req['route'],
                                            req['minimum_out'],req['minimum_lp'],req['deadline'],req['increase'])}
            # Probe is NEVER returned to the wallet. The actual contract's 99%
            # marginal-deployed floor applies even to this internal simulation.
            initial=self._trace(tx(),pins,req,gross,int(account[10],16),block)
            ceil_floor=lambda value:max(1,(value*(10000-req['slippage'])+9999)//10000)
            req['minimum_lp']=ceil_floor(initial['lp_liquidity_added_raw'])
            if req['route']!=ZERO_HASH: req['minimum_out']=ceil_floor(initial['converted_amount_raw'])
            transaction=tx()
            result=self._trace(transaction,pins,req,gross,int(account[10],16),block)
            # Tighter calldata changes intrinsic/execution gas; economic output
            # at the same state must remain identical.
            economics=lambda item:{k:v for k,v in item.items() if k!='simulation_gas_used'}
            if economics(result)!=economics(initial):
                raise ProjectionError('Same-snapshot activation simulations disagree')
        gas=self._gas(transaction,block)
        p._finish(header);prepared=self._fresh(header)
        if prepared>=req['deadline']: raise ProjectionError('Activation draft expired during preparation')
        return {'schema':1,'kind':kind,'activation_ready':kind=='activation_transaction',
                'action':payload['action'],'token_id':str(req['id']),'pool_id':req['pool'],
                'transaction':{**transaction,'chainId':hex(p.chain)},'approval_steps':approvals,
                'source':{'asset':req['source'],'amount_raw':str(req['amount']),'value_usd_18':str(gross)},
                'current_attached_value':current_value,
                'liquidity_context':liquidity_context,
                'contribution':None if result is None else {k:str(v) for k,v in result.items()},
                'execution_limit_bps':100,'minimum_deployed_usd_18':str(gross-gross//100),
                'minimum_liquidity_raw':str(req['minimum_lp']) if result else None,
                'minimum_conversion_output_raw':str(req['minimum_out']) if result else None,
                'network_gas':gas,'prepared_at':prepared,'expires_at':req['deadline'],
                'onchain_deadline':req['deadline'] if result else None,
                'provenance':{'block_number':header['number'],'block_hash':header['hash'],
                              'block_timestamp':header['timestamp'],'observed_head':head,'confirmations':p.confirmations,
                              'eip1898_require_canonical':True,'protocol_finalized':False,
                              'deployment_configuration_sha256':p.identity,'activation_configuration_sha256':cfg.identity},
                'wallet_revalidation_required':True,'state_overrides':False,
                'scope':'Confirmed-block unsigned preview. Wallet must recheck owner/network, exact calldata, '
                        'deadline, live simulation and gas. Approval is a separate transaction; reprepare after confirmation. '
                        'The on-chain 1% bound excludes gas. Future execution and production qualification are not guaranteed.'}


def main():
    import argparse,json
    from pathlib import Path
    from frontend_api.service import Projection
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,help='Reviewed schema-2 read API configuration')
    parser.add_argument('--activation-config',required=True,help='Reviewed activation bindings/routes and fee policy')
    parser.add_argument('--request',required=True,help='JSON typed request file; public wallet address only')
    args=parser.parse_args()
    try:
        p=Projection(json.loads(Path(args.config).read_text(encoding='utf-8')))
        service=ActivationTransactions(p,json.loads(Path(args.activation_config).read_text(encoding='utf-8')))
        result=service.prepare(json.loads(Path(args.request).read_text(encoding='utf-8')))
    except Exception:
        parser.exit(1,'Activation preparation unavailable; verify input, reviewed configuration and RPC capability.\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
