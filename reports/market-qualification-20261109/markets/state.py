from discover import *
if __name__=='__main__':
    topic=h('Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)')
    calls=[]
    height=int(A['number'],16)
    for low in range(0,height+1,10000000):
        calls.append(('eth_getLogs',[{'address':C,'fromBlock':hex(low),'toBlock':hex(min(low+9999999,height)),'topics':[topic,None,'0x'+word(0),'0x'+word(Z)]}]))
    logs=rpc('v4-initialize-bounded-02',calls)
    decoded=[]
    for answer in logs:
        if 'error' in answer:continue
        for log in answer['result']:
            blob=log['data'][2:];values=[int(blob[i:i+64],16) for i in range(0,len(blob),64)]
            key=['0x'+'0'*40,Z,values[0],values[1] if values[1]<2**255 else values[1]-2**256,'0x'+format(values[2],'040x')]
            poolid='0x'+keccak256(bytes.fromhex(''.join(word(x if not isinstance(x,int) or x>=0 else x+2**256) for x in key))).hex()
            if poolid!=log['topics'][1]:raise ValueError('PoolKey mismatch')
            decoded.append({'poolId':poolid,'key':key,'blockNumber':int(log['blockNumber'],16),'transactionHash':log['transactionHash'],'hookless':values[2]==0,'static':values[0]&0x800000==0})
    put('v4-discovered-pools.json',decoded)
    print(json.dumps(decoded,indent=2))
    pools=[x for x in decoded if x['hookless'] and x['static']]
    calls=[]
    for p in pools:calls.extend([call(S,'getSlot0(bytes32)',p['poolId']),call(S,'getLiquidity(bytes32)',p['poolId'])])
    if calls:
        state=rpc('v4-state-01',calls)
        for i,p in enumerate(pools):p['slot0_response']=state[2*i];p['liquidity_response']=state[2*i+1]
    put('v4-hookless-state.json',pools)
    v3=[x for x in json.loads((ROOT/'v3-known-fees-decoded.json').read_text(encoding='utf-8')) if int(x['pool_response'].get('result','0x0'),16)]
    labels=['token0()','token1()','fee()','tickSpacing()','liquidity()','slot0()','factory()','observations(uint256)']
    calls=[]
    for p in v3:
        addr='0x'+p['pool_response']['result'][-40:];p['address']=addr
        for sig in labels[:-1]:calls.append(call(addr,sig))
        calls.append(('eth_getCode',[addr,PIN]))
    res=rpc('v3-state-01',calls)
    for i,p in enumerate(v3):
        p['reads']={s:r for s,r in zip(labels[:-1]+['runtime'],res[i*8:i*8+8])}
        raw=bytes.fromhex(p['reads']['runtime']['result'][2:]);p['runtime_keccak256']='0x'+keccak256(raw).hex()
        p['reads']['runtime']={'bytes':len(raw),'raw_response_index':i*8+8}
    put('v3-state-decoded.json',v3)
    print(json.dumps(v3,indent=2))
