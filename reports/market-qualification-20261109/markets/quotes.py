from discover import *
from fractions import Fraction
QV4='0x8dc178efb8111bb0973dd9d722ebeff267c98f94'
QV3='0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7'
def v4call(key,zfo,amount):
    sig='quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))'
    # One dynamic tuple argument: offset32; five-key words +bool+amount+bytes-offset256; bytes length0.
    values=[32]+key+[int(zfo),amount,256,0]
    return ('eth_call',[{'to':QV4,'data':h(sig)[:10]+''.join(word(x) for x in values),'gas':hex(2000000)},PIN])
def v3call(fee,zfo,amount):
    return ('eth_call',[{'to':QV3,'data':data('quoteExactInputSingle((address,address,uint256,uint24,uint160))',W if zfo else Z,Z if zfo else W,amount,fee,0),'gas':hex(2000000)},PIN])
if __name__=='__main__':
    pools=json.loads((ROOT/'v4-hookless-state.json').read_text(encoding='utf-8'))
    v3=json.loads((ROOT/'v3-state-decoded.json').read_text(encoding='utf-8'))
    chosen=next(p for p in pools if p['poolId'].startswith('0x501122'))
    feed=rpc('sizing-eth-feed-01',[call('0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9','latestRoundData()'),call('0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9','decimals()')])
    words=[int(feed[0]['result'][i:i+64],16) for i in range(2,len(feed[0]['result']),64)]
    price=Fraction(words[1],10**int(feed[1]['result'],16));ratio=Fraction(chosen['slot0']['sqrtPriceX96']**2,2**192)
    sizing={'chainlink_eth_usd':str(price),'feed_answer':words[1],'feed_updatedAt':words[3],'anchor_timestamp':int(A['timestamp'],16),'warning':'One unqualified ETH/USD source and selected-pool instantaneous ZZZ/ETH ratio: sizing labels only, not independent PoPL valuation.'}
    usd_eth=[(label,int(Fraction(usd,1)*10**18/price)) for label,usd in [('nominal_100usd',100),('nominal_5usd',5)]]
    vectors=[('zzz1',False,10**18),('zzz1000',False,1000*10**18),('zzz10000',False,10000*10**18)]
    for label,amount in usd_eth:
        vectors.append((label+'_eth_half',True,amount//2))
        vectors.append((label+'_zzz_half_at_selected_spot',False,int(Fraction(amount)*ratio/2)))
    sizing['vectors']=[{'label':label,'zeroForOne':zfo,'amountIn':amount} for label,zfo,amount in vectors];put('quote-sizing.json',sizing)
    rows=[];calls=[]
    # All 15 low-fee hookless candidates: tiny input checks whether a gap can be crossed; active venues receive size vectors.
    for p in pools:
        vv=vectors if p['liquidity'] else [vectors[0],vectors[1]] if p['key'][2]<=10000 else []
        for label,zfo,amount in vv:
            rows.append({'version':4,'poolId':p['poolId'],'key':p['key'],'L':p['liquidity'],'label':label,'zeroForOne':zfo,'amountIn':amount,'sqrtPriceX96':p['slot0']['sqrtPriceX96'],'lpFee':p['slot0']['lpFee'],'protocolFee':p['slot0']['protocolFee']});calls.append(v4call(p['key'],zfo,amount))
    for p in v3:
        sqrt=int(p['reads']['slot0()']['result'][2:66],16)
        for label,zfo,amount in vectors:
            rows.append({'version':3,'pool':p['address'],'fee':p['fee'],'L':p['liquidity'],'label':label,'zeroForOne':zfo,'amountIn':amount,'sqrtPriceX96':sqrt});calls.append(v3call(p['fee'],zfo,amount))
    responses=[]
    for i in range(0,len(calls),16):responses.extend(rpc('quotes-01-'+str(i//16),calls[i:i+16]))
    for row,response in zip(rows,responses):
        row['response']=response
        raw=response.get('result','0x')[2:]
        if raw:
            values=[int(raw[j:j+64],16) for j in range(0,len(raw),64)]
            row['amountOut']=values[0];row['quoteGasEstimate']=values[-1]
            ownspot=Fraction(row['sqrtPriceX96']**2,2**192)
            expected=Fraction(row['amountIn'])*ownspot if row['zeroForOne'] else Fraction(row['amountIn'])/ownspot
            row['loss_bps_vs_own_spot']=float((1-Fraction(values[0])/expected)*10000)
            selectedexpected=Fraction(row['amountIn'])*ratio if row['zeroForOne'] else Fraction(row['amountIn'])/ratio
            row['loss_bps_vs_selected_spot']=float((1-Fraction(values[0])/selectedexpected)*10000)
    put('quotes-decoded.json',rows)
    recheck=rpc('anchor-recheck-01',[('eth_getBlockByNumber',[A['number'],False])])
    if recheck[0]['result']['hash']!=A['hash']:raise ValueError('anchor reorg')
    print(json.dumps({'queries':len(rows),'errors':sum('error'in r['response'] for r in rows),'zero_outputs':sum(r.get('amountOut')==0 for r in rows),'nonzero_pool_quote_examples':[r for r in rows if (r['version']==3 or r.get('poolId')==chosen['poolId']) and r['label'] in ('zzz1','zzz1000','nominal_100usd_eth_half','nominal_5usd_eth_half')]},indent=2))
