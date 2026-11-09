from discover import *
if __name__=='__main__':
    discovered=json.loads((ROOT/'v4-discovered-pools.json').read_text(encoding='utf-8'))
    pools=[x for x in discovered if x['hookless'] and x['static'] and x['key'][2]<=100000]
    calls=[]
    for p in pools:calls.extend([call(S,'getSlot0(bytes32)',p['poolId']),call(S,'getLiquidity(bytes32)',p['poolId'])])
    state=[]
    for i in range(0,len(calls),32):state.extend(rpc('v4-state-02-'+str(i//32),calls[i:i+32]))
    for i,p in enumerate(pools):
        p['slot0_response']=state[2*i];p['liquidity_response']=state[2*i+1]
        p['liquidity']=int(state[2*i+1].get('result','0x0'),16)
        v=state[2*i].get('result','0x')[2:]
        if len(v)==256:
            vals=[int(v[j:j+64],16) for j in range(0,len(v),64)]
            p['slot0']={'sqrtPriceX96':vals[0],'tick':vals[1] if vals[1]<2**255 else vals[1]-2**256,'protocolFee':vals[2],'lpFee':vals[3]}
    put('v4-hookless-state.json',pools)
    v3=[x for x in json.loads((ROOT/'v3-known-fees-decoded.json').read_text(encoding='utf-8')) if int(x['pool_response'].get('result','0x0'),16)]
    labels=['token0()','token1()','fee()','tickSpacing()','liquidity()','slot0()','factory()']
    calls=[]
    for p in v3:
        addr='0x'+p['pool_response']['result'][-40:];p['address']=addr
        for sig in labels:calls.append(call(addr,sig))
        calls.append(('eth_getCode',[addr,PIN]))
    res=rpc('v3-state-01',calls)
    for i,p in enumerate(v3):
        p['reads']={s:r for s,r in zip(labels+['runtime'],res[i*8:i*8+8])}
        raw=bytes.fromhex(p['reads']['runtime']['result'][2:]);p['runtime_keccak256']='0x'+keccak256(raw).hex()
        p['reads']['runtime']={'bytes':len(raw),'raw_response_index':i*8+8}
        p['liquidity']=int(p['reads']['liquidity()'].get('result','0x0'),16)
    put('v3-state-decoded.json',v3)
    print(json.dumps({'v4_discovered':len(discovered),'compatible_fee_filtered':len(pools),'v4_nonzeroL':[{'poolId':p['poolId'],'key':p['key'],'slot0':p.get('slot0'),'liquidity':p['liquidity']} for p in pools if p['liquidity']],'v3':[{'address':p['address'],'fee':p['fee'],'L':p['liquidity'],'slot0':p['reads']['slot0()'],'hash':p['runtime_keccak256']} for p in v3]},indent=2))
